"""Long-term memory adapters: owner feedback, extraction status, retrieval.

Day-3 wires the fourth read-only tool (``search_owner_memory``) to a
:class:`MemoryService` and gives owner feedback an HONEST lifecycle. The real AWS
Bedrock AgentCore Memory adapter is optional and NEVER a silent stand-in:

* the local backend (``not_implemented``) saves the raw feedback to the business
  database and reports ``saved``. It never reports ``available`` -- that would
  present stored feedback as extracted memory without real retrieval evidence
  (AGENTS.md L18) -- and ``search`` returns nothing rather than a fabricated
  memory;
* the AgentCore backend (``agentcore``) is the real adapter. A missing dependency
  or missing credential raises :class:`MemoryUnavailable` so the caller keeps the
  honest ``not_implemented``/``failed`` label instead of inventing a memory.

Ownership: this module is the AI/memory seam. ``workflow.py`` (Backend) never
imports it; ``main.py`` (Coordinator) assembles a service and injects it into
:class:`pawtwin.agent.AgentContext`. Persistence of the raw feedback stays in the
repository (Backend): this module is a pure AgentCore abstraction and does not
import the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import UUID

from pawtwin.config import Settings
from pawtwin.models import FeedbackScope, MemoryBackend, MemoryStatus

__all__ = [
    "AgentCoreMemory",
    "FeedbackResult",
    "LocalFakeMemory",
    "MemoryRecord",
    "MemoryService",
    "MemoryUnavailable",
    "StubMemoryService",
    "build_memory",
]

MEMORY_UNAVAILABLE = "MEMORY_UNAVAILABLE"
DEFAULT_PET_ID = "mochi"


class MemoryUnavailable(RuntimeError):
    """Real AgentCore memory could not be used. Never substituted by a stand-in.

    The message always starts with ``MEMORY_UNAVAILABLE`` so a caller can map it
    onto a bounded reason and keep the honest label instead of fabricating a
    retrieved memory.
    """


@dataclass
class MemoryRecord:
    """One long-term memory that was REALLY retrieved.

    ``record_id`` is the AgentCore record id and ``namespace`` the owner/pet scope
    it came from -- never a session id (T5: session_id does not act as pet
    identity). ``summary`` is bounded text safe to surface as evidence; it is not
    hidden reasoning and never carries an AWS credential.
    """

    record_id: str
    namespace: str
    summary: str
    source: Literal["agentcore"] = "agentcore"


@dataclass
class FeedbackResult:
    """Outcome of asking a memory backend to process one owner feedback item.

    ``memory_status`` is the honest lifecycle and ``memory_record_ids`` stays empty
    until a real AgentCore extraction is retrievable, so a local ``saved`` result
    can never be mistaken for an extracted memory.
    """

    feedback_id: UUID
    memory_status: MemoryStatus
    memory_backend: MemoryBackend
    memory_record_ids: list[str] = field(default_factory=list)
    agentcore_event_id: str | None = None


class MemoryService(Protocol):
    """Frozen Day-3 memory seam (ruling 1).

    ``submit_feedback`` decides the honest status for one ALREADY-persisted
    feedback id (the raw text is stored by the repository first, T5); ``get_status``
    re-reads that lifecycle; ``search`` retrieves long-term memory for one
    owner/pet scope and returns an empty list when nothing was really extracted.
    """

    label: MemoryBackend

    def submit_feedback(
        self,
        *,
        feedback_id: UUID,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        conversation_id: str | None,
    ) -> FeedbackResult: ...

    def get_status(
        self, feedback_id: UUID, *, agentcore_event_id: str | None = None
    ) -> MemoryStatus: ...

    def search(self, *, owner_id: str, pet_id: str, query: str) -> list[MemoryRecord]: ...


class LocalFakeMemory:
    """The honest ``not_implemented`` backend used in local mode.

    Feedback is really saved to the business database by the repository; this
    backend performs NO extraction and NO retrieval. ``submit_feedback`` therefore
    reports ``saved`` (raw stored), never ``processing``/``available`` -- there is
    no extraction job running locally, and claiming one would be a distortion.
    ``search`` returns an empty list rather than a fabricated memory.
    """

    label: MemoryBackend = "not_implemented"

    def submit_feedback(
        self,
        *,
        feedback_id: UUID,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        conversation_id: str | None,
    ) -> FeedbackResult:
        _ = (owner_id, pet_id, text, scope, conversation_id)  # raw already persisted by Backend
        return FeedbackResult(
            feedback_id=feedback_id,
            memory_status="saved",
            memory_backend="not_implemented",
        )

    def get_status(
        self, feedback_id: UUID, *, agentcore_event_id: str | None = None
    ) -> MemoryStatus:
        _ = (feedback_id, agentcore_event_id)
        # Nothing is ever extracted locally, so the raw-saved status is the truth.
        return "saved"

    def search(self, *, owner_id: str, pet_id: str, query: str) -> list[MemoryRecord]:
        _ = (owner_id, pet_id, query)
        # Never fabricate a memory: no real AgentCore retrieval happened.
        return []


class AgentCoreMemory:
    """Real AWS Bedrock AgentCore Memory adapter. Never a silent local stand-in.

    ``client`` is an injection seam for OFFLINE tests only: it lets us assert how a
    submission/retrieval request is constructed and parsed without any cloud call.
    Passing a stub here is explicitly NOT cloud evidence. Without a client the SDK
    is imported lazily and a missing dependency or credential raises
    :class:`MemoryUnavailable` so the run keeps the honest label.

    NOTE: the full asynchronous extraction lifecycle (strategy ACTIVE check, submit
    observation, poll every 10s up to 3 minutes, then ``available`` with real record
    ids) is a CONDITIONAL item -- it can only be exercised against a real account
    and is verified there, not here.
    """

    label: MemoryBackend = "agentcore"

    def __init__(
        self,
        memory_id: str,
        *,
        region: str | None = None,
        client: Any | None = None,
    ) -> None:
        self._memory_id = memory_id
        self._region = region
        self._client = client

    def submit_feedback(
        self,
        *,
        feedback_id: UUID,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        conversation_id: str | None,
    ) -> FeedbackResult:
        client = self._client if self._client is not None else self._build_client()
        try:
            event_id = client.create_event(
                memory_id=self._memory_id,
                namespace=self._namespace(owner_id, pet_id),
                session_id=conversation_id,
                payload=text,
                # ``today_only`` must never become a permanent preference (A07):
                # it is tagged so the strategy does not extract a lasting trait.
                metadata={"scope": scope, "feedback_id": str(feedback_id)},
            )
        except MemoryUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 - any cloud failure fails closed
            raise MemoryUnavailable(
                f"{MEMORY_UNAVAILABLE}: SUBMIT_FAILED {exc.__class__.__name__}"
            ) from exc
        return FeedbackResult(
            feedback_id=feedback_id,
            memory_status="processing",
            memory_backend="agentcore",
            agentcore_event_id=str(event_id) if event_id is not None else None,
        )

    def get_status(
        self, feedback_id: UUID, *, agentcore_event_id: str | None = None
    ) -> MemoryStatus:
        _ = feedback_id
        if agentcore_event_id is None:
            # No submission was ever recorded, so nothing is being extracted.
            return "saved"
        client = self._client if self._client is not None else self._build_client()
        try:
            return client.event_status(memory_id=self._memory_id, event_id=agentcore_event_id)
        except MemoryUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 - a poll failure is never "available"
            raise MemoryUnavailable(
                f"{MEMORY_UNAVAILABLE}: STATUS_FAILED {exc.__class__.__name__}"
            ) from exc

    def search(self, *, owner_id: str, pet_id: str, query: str) -> list[MemoryRecord]:
        client = self._client if self._client is not None else self._build_client()
        namespace = self._namespace(owner_id, pet_id)
        try:
            raw = client.retrieve(memory_id=self._memory_id, namespace=namespace, query=query)
        except MemoryUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 - retrieval failure is never a fake memory
            raise MemoryUnavailable(
                f"{MEMORY_UNAVAILABLE}: RETRIEVE_FAILED {exc.__class__.__name__}"
            ) from exc
        records: list[MemoryRecord] = []
        for item in raw or []:
            records.append(
                MemoryRecord(
                    record_id=str(item.get("record_id", "")),
                    namespace=namespace,
                    summary=str(item.get("summary", ""))[:300],
                )
            )
        return records

    @staticmethod
    def _namespace(owner_id: str, pet_id: str) -> str:
        """Owner/pet scope. Deliberately NOT the session id (T5)."""

        return f"{owner_id}/{pet_id}"

    def _build_client(self) -> Any:
        """Deferred import: a missing extra must never break local mode or CI."""

        try:
            from pawtwin.agentcore_client import AgentCoreMemoryClient
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise MemoryUnavailable(f"{MEMORY_UNAVAILABLE}: SDK_NOT_INSTALLED") from exc
        return AgentCoreMemoryClient(memory_id=self._memory_id, region=self._region)


class StubMemoryService:
    """Construction-injected test double. Proves wiring, NOT cloud evidence.

    Mirrors the Day-2 ``StubBedrockClient`` pattern: an offline test can hand the
    agent a memory service that returns canned records, so the ``source='memory'``
    evidence chain and proposal citation can be asserted with zero network and zero
    credentials. A stubbed retrieval is explicitly NOT a real AgentCore memory.
    """

    def __init__(
        self,
        *,
        label: MemoryBackend = "agentcore",
        records: list[MemoryRecord] | None = None,
        status: MemoryStatus = "processing",
    ) -> None:
        self.label = label
        self._records = list(records or [])
        self._status = status
        self.submitted: list[dict[str, Any]] = []
        self.queries: list[str] = []

    def submit_feedback(
        self,
        *,
        feedback_id: UUID,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        conversation_id: str | None,
    ) -> FeedbackResult:
        self.submitted.append(
            {
                "feedback_id": feedback_id,
                "owner_id": owner_id,
                "pet_id": pet_id,
                "text": text,
                "scope": scope,
                "conversation_id": conversation_id,
            }
        )
        return FeedbackResult(
            feedback_id=feedback_id,
            memory_status=self._status,
            memory_backend=self.label,
        )

    def get_status(
        self, feedback_id: UUID, *, agentcore_event_id: str | None = None
    ) -> MemoryStatus:
        _ = (feedback_id, agentcore_event_id)
        return self._status

    def search(self, *, owner_id: str, pet_id: str, query: str) -> list[MemoryRecord]:
        _ = (owner_id, pet_id)
        self.queries.append(query)
        return list(self._records)


def build_memory(settings: Settings) -> MemoryService:
    """Fail-closed memory factory: agentcore -> real adapter, else honest local.

    ``not_implemented`` saves raw feedback and retrieves nothing; it never
    fabricates a memory. ``agentcore`` requires AGENTCORE_MEMORY_ID (enforced by
    :class:`pawtwin.config.Settings`) and fails visibly when unavailable.
    """

    backend = settings.effective_memory_backend
    if backend == "agentcore":
        return AgentCoreMemory(settings.agentcore_memory_id or "", region=settings.aws_region)
    return LocalFakeMemory()
