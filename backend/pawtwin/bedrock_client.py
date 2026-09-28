"""Real Bedrock client behind the optional ``bedrock`` extra.

Imported LAZILY by :class:`pawtwin.agent.BedrockAgent`, so local mode, CI and the
offline contract export never need this dependency installed. Nothing here falls
back to a stand-in: a missing SDK, a missing model id or missing credentials raise
``BedrockUnavailable`` and the run fails visibly.

VERIFICATION STATUS (Day-2): written against ``strands-agents==1.57.0`` whose
``BedrockModel`` / ``Agent`` / ``Limits`` signatures were introspected locally, but
**never exercised against a real AWS account** -- no account is available. This
module is therefore condition-blocked evidence, not a claim that Bedrock works.

Design note: the four read-only tools are wrapped closures over the server-built
:class:`~pawtwin.agent.AgentContext`. The model never receives an ``owner_id`` and
cannot widen its own scope; every tool call is appended to the context ledger, so
a proposal can only cite evidence that was really retrieved.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Safe at import time: this module is only ever imported from inside
# ``BedrockAgent._build_client``, i.e. after pawtwin.agent is fully loaded.
from pawtwin.agent import BedrockUnavailable
from pawtwin.models import BACKEND_UNAVAILABLE

# SDK-level budget. ``read_timeout`` must stay clearly below the 45s analysis
# deadline so the workflow's own guard is the last line of defence, not the first.
_CONNECT_TIMEOUT_SECONDS = 10
_MAX_SDK_ATTEMPTS = 2
_CREDENTIAL_ENV_NAMES = (
    "AWS_ACCESS_KEY_ID",
    "AWS_PROFILE",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
)


def _unavailable(detail: str) -> BedrockUnavailable:
    return BedrockUnavailable(f"{BACKEND_UNAVAILABLE}: {detail}")


def require_credentials() -> None:
    """Fail closed when no credential source is configured at all.

    This only decides whether to ATTEMPT a call; it never implies connectivity and
    never sets ``aws_connected`` (which stays False until storage, model and memory
    are all verified). Long-lived keys are never read from or written to the repo.
    """

    if any(os.getenv(name) for name in _CREDENTIAL_ENV_NAMES):
        return
    candidates = [
        os.environ.get("AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials")),
        os.environ.get("AWS_CONFIG_FILE", os.path.expanduser("~/.aws/config")),
    ]
    if any(path and os.path.isfile(path) for path in candidates):
        return
    raise _unavailable("BEDROCK_NOT_CONFIGURED")


def _field(container: Any, *names: str) -> Any:
    """Read a field from a dict OR an object, tolerating SDK shape differences."""

    for name in names:
        if isinstance(container, dict):
            if name in container:
                return container[name]
        else:
            value = getattr(container, name, None)
            if value is not None:
                return value
    return None


def _extract_json(text: Any) -> Any:
    """Best-effort JSON recovery from a message; returns None rather than guessing."""

    if not isinstance(text, str):
        return None
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


class StrandsBedrockClient:
    """Thin adapter over Strands + Bedrock with the project's budgets applied."""

    def __init__(
        self,
        *,
        model_id: str,
        region: str | None = None,
        max_output_tokens: int = 800,
        timeout_seconds: float = 45.0,
        max_model_calls: int = 4,
        temperature: float = 0.2,
    ) -> None:
        if not model_id:
            raise _unavailable("BEDROCK_MODEL_ID_MISSING")
        self._model_id = model_id
        self._region = region
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds
        self._max_model_calls = max_model_calls
        self._temperature = temperature

    # -- public surface used by BedrockAgent ---------------------------------

    def analyze(
        self,
        *,
        prompt: str,
        system_prompt: str,
        context: Any,
        output_schema: type,
        model_id: str | None = None,
        max_output_tokens: int | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """One bounded analysis turn. Returns a plain dict for the caller to parse."""

        require_credentials()
        try:
            from strands import Agent
            from strands.models import BedrockModel
            from strands.types.agent import Limits
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise _unavailable("STRANDS_NOT_INSTALLED") from exc

        resolved_model = model_id or self._model_id
        resolved_tokens = max_output_tokens or self._max_output_tokens
        resolved_timeout = timeout_seconds or self._timeout_seconds

        try:
            model = self._build_model(
                BedrockModel, resolved_model, resolved_tokens, resolved_timeout
            )
            agent = Agent(
                model=model,
                tools=_build_tools(context),
                system_prompt=system_prompt,
            )
            # ``Limits`` is the SDK-level enforcement of the project ceilings:
            # turns bound the tool/model round trips, output_tokens bound the reply.
            result = agent(
                prompt,
                structured_output_model=output_schema,
                limits=Limits(turns=self._max_model_calls, output_tokens=resolved_tokens),
            )
        except Exception as exc:  # noqa: BLE001 - any cloud failure must fail closed
            raise _unavailable(f"BEDROCK_CALL_FAILED {exc.__class__.__name__}") from exc

        return self._summarise(result)

    def _build_model(
        self, bedrock_model: type, model_id: str, max_tokens: int, timeout_seconds: float
    ) -> Any:
        boto_config = self._boto_config(timeout_seconds)
        kwargs: dict[str, Any] = {
            "model_id": model_id,
            "max_tokens": max_tokens,
            "temperature": self._temperature,
            "streaming": False,
        }
        if self._region:
            kwargs["region_name"] = self._region
        if boto_config is not None:
            kwargs["boto_client_config"] = boto_config
        return bedrock_model(**kwargs)

    @staticmethod
    def _boto_config(timeout_seconds: float) -> Any | None:
        """SDK timeouts/retries so a hung call cannot outlive the analysis budget."""

        try:
            from botocore.config import Config
        except ImportError:  # pragma: no cover - botocore ships with the extra
            return None
        read_timeout = max(_CONNECT_TIMEOUT_SECONDS, int(timeout_seconds) - 5)
        return Config(
            connect_timeout=_CONNECT_TIMEOUT_SECONDS,
            read_timeout=read_timeout,
            retries={"max_attempts": _MAX_SDK_ATTEMPTS, "mode": "standard"},
        )

    def _summarise(self, result: Any) -> dict[str, Any]:
        proposal = getattr(result, "structured_output", None)
        if proposal is None:
            # Only a payload that really parses is accepted; otherwise the caller
            # fails closed instead of inventing a proposal.
            proposal = _extract_json(_field(_field(result, "message"), "content"))
        metrics = getattr(result, "metrics", None) or {}
        usage = getattr(result, "usage", None) or {}
        return {
            "proposal": proposal,
            "model_calls": int(_field(metrics, "modelInvocationCount") or 1),
            "output_tokens": int(_field(usage, "outputTokens", "output_tokens") or 0),
            "request_id": _field(metrics, "modelRequestId", "requestId"),
        }


def _build_tools(context: Any) -> list[Any]:
    """Wrap the four read-only tools; ``owner_id`` is captured, never a parameter."""

    from strands import tool

    @tool
    def get_pet_facts(pet_id: str) -> dict[str, Any]:
        """Read the current feeding facts and quota for this pet from the app database."""
        return context.get_pet_facts(pet_id)

    @tool
    def get_recent_events(pet_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """List recent care requests and their outcomes (state only, no free text)."""
        return context.get_recent_events(pet_id, limit)

    @tool
    def search_owner_memory(pet_id: str, query: str) -> list[dict[str, Any]]:
        """Search the owner's long-term observations. Empty until memory is enabled."""
        return context.search_owner_memory(pet_id, query)

    @tool
    def get_policy_summary(pet_id: str) -> dict[str, Any]:
        """Read the non-negotiable feeding policy summary."""
        return context.get_policy_summary(pet_id)

    return [get_pet_facts, get_recent_events, search_owner_memory, get_policy_summary]
