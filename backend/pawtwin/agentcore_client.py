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

Day-5 REWRITE (ruling 10; real shapes from the Day-5 plan §2, obtained by
introspecting botocore's ``bedrock-agentcore`` service model): the Day-3 calls were
WRONG for the real data plane -- ``create_event`` has NO ``namespace`` parameter,
``list_events(memoryId=...)`` cannot locate one event, and there is NO
``search_memory`` operation. They are replaced by ``CreateEvent`` (payload =
``[{conversational:{content:{text}, role}}]``, routed by
``extractionConfig.namespaceVariables``), ``GetEvent`` (which REQUIRES ``sessionId``
and ``actorId``, fact G-G), and ``RetrieveMemoryRecords`` (``namespacePath`` +
``searchCriteria.searchQuery``). Still **never exercised against a real account**
(no credential available). The locked SDK and official API response shapes were
checked offline: retrieval returns ``memoryRecordSummaries`` with ``content.text``.
``GetEvent`` has NO extraction-status field, so extraction polling explicitly fails
with ``EVENT_EXTRACTION_STATUS_UNSUPPORTED`` until a correlated completion signal
is implemented; existence of a raw event never proves long-term extraction.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
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
        actor_id: str,
        session_id: str | None,
        text: str,
        namespace_variables: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Submit one owner observation for asynchronous extraction (``CreateEvent``).

        Real shape (plan §2): ``memoryId``/``actorId``/``eventTimestamp``/``payload``
        are required; the payload is a list of structures and a conversational item
        is ``{conversational:{content:{text}, role}}``. There is NO ``namespace``
        parameter -- routing into ``/owner/<o>/pet/<p>`` happens through the
        strategy's ``namespaceTemplates`` fed by ``extractionConfig.
        namespaceVariables``. Returns the AgentCore ``eventId`` so a retry can reuse
        the local feedback id and never submit twice (T5); ``sessionId`` is a
        conversation, never the pet identity, and is persisted because ``GetEvent``
        requires it (fact G-G).
        """

        client = self._client()
        request: dict[str, Any] = {
            "memoryId": memory_id,
            "actorId": actor_id,
            "eventTimestamp": datetime.now(UTC),
            "payload": [{"conversational": {"content": {"text": text}, "role": "USER"}}],
        }
        if session_id is not None:
            request["sessionId"] = session_id
        if namespace_variables:
            request["extractionConfig"] = {"namespaceVariables": namespace_variables}
        if metadata:
            # The locked SDK models MetadataValue as a stringValue union, rather
            # than a bare string. Preserve stable UUID/int metadata as text.
            request["metadata"] = {
                str(key): {"stringValue": str(value)} for key, value in metadata.items()
            }
        try:
            response = client.create_event(**request)
        except Exception as exc:  # noqa: BLE001 - fail closed, never a fake event id
            raise _unavailable(f"CREATE_EVENT_FAILED {exc.__class__.__name__}") from exc
        event = _field(response, "event") or response
        event_id = _field(event, "eventId", "id")
        return str(event_id) if event_id is not None else None

    def event_status(
        self,
        *,
        memory_id: str,
        event_id: str,
        session_id: str | None = None,
        actor_id: str | None = None,
    ) -> str:
        """Fail explicitly: ``GetEvent`` does not expose extraction completion.

        The official response proves only that a raw event exists. A correlated
        extraction job or memory-record signal must be implemented before this
        adapter can report a terminal extraction state. Returning ``processing``
        here would make the caller poll forever for a field the API never returns.
        """

        if session_id is None or actor_id is None:
            raise _unavailable("GET_EVENT_CONTEXT_MISSING")
        client = self._client()
        try:
            client.get_event(
                memoryId=memory_id, sessionId=session_id, actorId=actor_id, eventId=event_id
            )
        except Exception as exc:  # noqa: BLE001 - a poll failure is never "processed"
            raise _unavailable(f"STATUS_FAILED {exc.__class__.__name__}") from exc
        raise _unavailable("EVENT_EXTRACTION_STATUS_UNSUPPORTED")

    def retrieve(
        self,
        *,
        memory_id: str,
        namespace_path: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve really-extracted records for one owner/pet namespacePath.

        Real shape (plan §2): ``RetrieveMemoryRecords(memoryId, namespacePath,
        searchCriteria={searchQuery, topK})``. There is no ``search_memory``
        operation. Only records with a real id are surfaced -- an id-less blob is
        never a citable memory.
        """

        client = self._client()
        try:
            response = client.retrieve_memory_records(
                memoryId=memory_id,
                namespacePath=namespace_path,
                searchCriteria={"searchQuery": query, "topK": top_k},
            )
        except Exception as exc:  # noqa: BLE001 - retrieval failure is never a fake memory
            raise _unavailable(f"RETRIEVE_FAILED {exc.__class__.__name__}") from exc
        records: list[dict[str, Any]] = []
        items = _field(response, "memoryRecordSummaries", "memoryRecords", "records", "results")
        for item in items or []:
            record_id = _field(item, "recordId", "id", "memoryRecordId")
            if record_id is None:
                continue  # never surface an id-less blob as a citable memory
            content = _field(item, "content", "summary", "text") or ""
            summary = _field(content, "text") if not isinstance(content, str) else content
            summary = summary or ""
            records.append({"record_id": str(record_id), "summary": str(summary)[:300]})
        return records

    def memory_exists(self) -> bool:
        """Read-only control-plane probe (``GetMemory``), zero model cost (ruling 7).

        Used by ``create_app`` to confirm the AgentCore memory really exists before
        the app claims a cloud connection. Any failure raises
        :class:`~pawtwin.memory.MemoryUnavailable` so startup is refused rather than
        silently degrading. Uses ``bedrock-agentcore-control`` (GetMemory lives on the
        control plane, not the data plane used above).
        """

        require_credentials()
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise _unavailable("SDK_NOT_INSTALLED") from exc
        kwargs: dict[str, Any] = {"region_name": self._region} if self._region else {}
        try:
            control = boto3.client("bedrock-agentcore-control", **kwargs)
            control.get_memory(memoryId=self._memory_id)
        except Exception as exc:  # noqa: BLE001 - report the real reason, never fall back
            raise _unavailable(f"PROBE_FAILED {exc.__class__.__name__}") from exc
        return True
