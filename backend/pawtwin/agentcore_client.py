"""Real AgentCore Memory client behind the optional ``memory`` extra.

Imported LAZILY by :class:`pawtwin.memory.AgentCoreMemory`, so local mode, CI and
the offline contract export never need this dependency installed. Nothing here falls
back to a stand-in: a missing SDK, a missing memory id or missing credentials raise
:class:`~pawtwin.memory.MemoryUnavailable`, and the caller keeps the honest
``not_implemented``/``failed`` label instead of inventing a memory.

VERIFICATION STATUS (Day-3): written against the boto3 ``bedrock-agentcore``
data-plane shape (create_event / search_memory / event status), but **never
exercised against a real AWS account** -- no account is available. This module is
therefore condition-blocked evidence, NOT a claim that AgentCore Memory works. The
full asynchronous extraction lifecycle (strategy ACTIVE, submit, poll until really
retrievable, then ``available`` with real record ids) is verified only against a
real account, and until then the honest local status stays ``saved``.
"""

from __future__ import annotations

import os
from typing import Any

# Safe at import time: this module is only ever imported from inside
# ``AgentCoreMemory._build_client``, i.e. after pawtwin.memory is fully loaded.
from pawtwin.memory import MEMORY_UNAVAILABLE, MemoryUnavailable

_CREDENTIAL_ENV_NAMES = (
    "AWS_ACCESS_KEY_ID",
    "AWS_PROFILE",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
)


def _unavailable(detail: str) -> MemoryUnavailable:
    return MemoryUnavailable(f"{MEMORY_UNAVAILABLE}: {detail}")


def require_credentials() -> None:
    """Fail closed when no credential source is configured at all.

    This only decides whether to ATTEMPT a call; it never implies connectivity and
    never sets ``aws_connected``. Long-lived keys are never read from or written to
    the repository, logs or evidence.
    """

    if any(os.getenv(name) for name in _CREDENTIAL_ENV_NAMES):
        return
    candidates = [
        os.environ.get("AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials")),
        os.environ.get("AWS_CONFIG_FILE", os.path.expanduser("~/.aws/config")),
    ]
    if any(path and os.path.isfile(path) for path in candidates):
        return
    raise _unavailable("AGENTCORE_NOT_CONFIGURED")


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


class AgentCoreMemoryClient:
    """Thin adapter over the boto3 ``bedrock-agentcore`` data plane.

    Every method fails closed: any SDK/credential/network error becomes
    :class:`MemoryUnavailable` rather than an empty result that could be mistaken
    for "no memory yet" or, worse, a fabricated one.
    """

    def __init__(self, *, memory_id: str, region: str | None = None) -> None:
        if not memory_id:
            raise _unavailable("AGENTCORE_MEMORY_ID_MISSING")
        self._memory_id = memory_id
        self._region = region

    def _client(self) -> Any:
        require_credentials()
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise _unavailable("SDK_NOT_INSTALLED") from exc
        kwargs: dict[str, Any] = {}
        if self._region:
            kwargs["region_name"] = self._region
        try:
            return boto3.client("bedrock-agentcore", **kwargs)
        except Exception as exc:  # noqa: BLE001 - any client failure must fail closed
            raise _unavailable(f"CLIENT_INIT_FAILED {exc.__class__.__name__}") from exc

    def create_event(
        self,
        *,
        memory_id: str,
        namespace: str,
        session_id: str | None,
        payload: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Submit one owner observation for asynchronous extraction.

        Returns the AgentCore event id so a retry can reuse the local feedback id
        and never submit the same observation twice (T5). The session id is a
        conversation, never the pet identity; the namespace carries owner/pet.
        """

        client = self._client()
        request: dict[str, Any] = {
            "memoryId": memory_id,
            # AgentCore requires a session id; fall back to the namespace so a
            # missing conversation still scopes the event to the owner/pet.
            "sessionId": session_id or namespace,
            "payload": payload,
            "namespace": namespace,
        }
        if metadata:
            request["metadata"] = metadata
        try:
            response = client.create_event(**request)
        except Exception as exc:  # noqa: BLE001 - fail closed, never a fake event id
            raise _unavailable(f"CREATE_EVENT_FAILED {exc.__class__.__name__}") from exc
        event_id = _field(response, "eventId", "id")
        return str(event_id) if event_id is not None else None

    def event_status(self, *, memory_id: str, event_id: str) -> str:
        """Map the extraction lifecycle onto the honest MemoryStatus vocabulary.

        Anything not clearly retrievable stays ``processing``; an error is
        ``failed``. This NEVER returns ``available`` unless the service says the
        event was really processed (AGENTS.md L18).
        """

        client = self._client()
        try:
            response = client.list_events(memoryId=memory_id)
        except Exception as exc:  # noqa: BLE001 - a poll failure is never "available"
            raise _unavailable(f"STATUS_FAILED {exc.__class__.__name__}") from exc
        for event in _field(response, "events", "items") or []:
            if str(_field(event, "eventId", "id") or "") != event_id:
                continue
            status = str(_field(event, "status", "state") or "").upper()
            if status in {"PROCESSED", "COMPLETED", "SUCCEEDED", "AVAILABLE"}:
                return "available"
            if status in {"FAILED", "ERROR"}:
                return "failed"
            return "processing"
        # Unknown/absent event: still being ingested, never claim it is retrievable.
        return "processing"

    def retrieve(self, *, memory_id: str, namespace: str, query: str) -> list[dict[str, Any]]:
        """Retrieve really-extracted memory records for one owner/pet namespace."""

        client = self._client()
        try:
            response = client.search_memory(
                memoryId=memory_id, searchQuery=query, namespace=namespace
            )
        except Exception as exc:  # noqa: BLE001 - retrieval failure is never a fake memory
            raise _unavailable(f"RETRIEVE_FAILED {exc.__class__.__name__}") from exc
        records: list[dict[str, Any]] = []
        for item in _field(response, "memoryRecords", "records", "results") or []:
            record_id = _field(item, "recordId", "id", "memoryRecordId")
            if record_id is None:
                continue  # never surface an id-less blob as a citable memory
            summary = _field(item, "content", "summary", "text") or ""
            records.append({"record_id": str(record_id), "summary": str(summary)[:300]})
        return records
