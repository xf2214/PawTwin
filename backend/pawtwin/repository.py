"""Persistence protocol and internal records.

The internal ``RunRecord`` carries bookkeeping fields (``owner_id``,
``proposal_version``, ``action_digest``, ``attempt_count``, ``lease_owner``,
``lease_until``, ``model_calls_used``) that are deliberately NOT part of any
public response DTO. Adapters (SQLite now, DynamoDB later) implement the same
``Repository`` protocol so the workflow never depends on a specific backend.

Day-2 adds the concurrency primitives the worker needs: an explicit claimable
whitelist, lease renewal/release, a compare-and-set state transition, and an
idempotent schema migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from pawtwin.models import (
    AnalysisTelemetry,
    EventIn,
    EvidenceItem,
    FeedbackScope,
    MemoryBackend,
    MemoryStatus,
    Proposal,
    Receipt,
    RunState,
)

# Terminal states must never be re-processed or re-dispensed.
TERMINAL_STATES: frozenset[RunState] = frozenset(
    {
        RunState.DECLINED,
        RunState.EXPIRED,
        RunState.SUCCEEDED,
        RunState.FAILED,
        RunState.UNKNOWN,
    }
)

# Day-2 ruling 7: claimable states are an explicit WHITELIST. "not terminal" is
# NOT the same as "safe to re-analyze" -- ``awaiting_approval``/``needs_info``/
# ``blocked`` have finished analysis and are waiting on a human, and
# ``EXECUTING`` must be reconciled (never re-analyzed): re-analysis would mint a
# new ``command_id`` from the bumped ``proposal_version`` and account the quota a
# second time.
CLAIMABLE_STATES: frozenset[RunState] = frozenset({RunState.QUEUED, RunState.ANALYZING})


class _Unset:
    """Sentinel separating "leave this column alone" from "write NULL"."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "UNSET"


UNSET = _Unset()


@dataclass
class RunRecord:
    run_id: UUID
    owner_id: str
    event_id: UUID
    state: RunState
    created_at: datetime
    facts_version: int = 0
    proposal: Proposal | None = None
    proposal_version: int = 0
    action_digest: str | None = None
    receipt: Receipt | None = None
    expires_at: datetime | None = None
    lease_owner: str | None = None
    lease_until: datetime | None = None
    attempt_count: int = 0
    policy_reason: str | None = None
    # Day-2: durable failure reason, evidence ledger, call telemetry and the
    # cross-attempt model-call budget (an in-process counter alone could be reset
    # by a restart, which would silently lift the <=4 calls ceiling).
    failure_reason: str | None = None
    evidence: list[EvidenceItem] = field(default_factory=list)
    telemetry: AnalysisTelemetry | None = None
    model_calls_used: int = 0
    event: EventIn | None = field(default=None, repr=False)


@dataclass
class FactsSnapshot:
    owner_id: str
    pet_id: str
    last_fed_minutes_ago: int | None
    daily_dispensed_grams: int | None
    daily_limit_grams: int
    single_serving_grams: int
    minimum_interval_minutes: int
    facts_version: int


@dataclass
class FeedbackRecord:
    """Internal owner-feedback record (NOT a public response DTO).

    Holds the raw owner text, its HONEST memory lifecycle and the AgentCore
    bookkeeping (event id, extracted record ids). ``memory_status='saved'`` means
    the RAW text is stored in the business database; it never implies extraction
    (see :mod:`pawtwin.memory`). ``owner_id``/``idempotency_key`` stay internal,
    exactly like ``RunRecord``'s bookkeeping fields.
    """

    feedback_id: UUID
    owner_id: str
    pet_id: str
    text: str
    scope: FeedbackScope
    memory_status: MemoryStatus
    memory_backend: MemoryBackend
    created_at: datetime
    conversation_id: str | None = None
    agentcore_event_id: str | None = None
    # Day-5 (ruling 10 / fact G-G): ``GetEvent`` needs the AgentCore ``sessionId``
    # to poll one event's extraction status, but the event id alone cannot locate
    # it. The conversation id used at submission is persisted here so the poller can
    # call ``get_event(memoryId, sessionId, actorId, eventId)``. Internal only.
    agentcore_session_id: str | None = None
    memory_record_ids: list[str] = field(default_factory=list)
    idempotency_key: str | None = field(default=None, repr=False)


class Repository(Protocol):
    """Storage semantics shared by the SQLite and (future) DynamoDB adapters."""

    def create_or_get_run(self, owner_id: str, event: EventIn) -> RunRecord:
        """Return the run for ``(owner_id, event.event_id)``; dedup on redelivery."""
        ...

    def get_run(self, run_id: UUID) -> RunRecord | None: ...

    def list_runs(self, owner_id: str) -> list[RunRecord]: ...

    def list_claimable_runs(self, limit: int = 10) -> list[RunRecord]:
        """Runs a worker may try to claim: whitelisted state and no live lease."""
        ...

    def count_runs(self, owner_id: str) -> int:
        """Test/adapter helper: number of runs owned by ``owner_id``."""
        ...

    def save_run(self, record: RunRecord, *, expected_approval_version: int | None = None) -> bool:
        """Persist analysis/approval fields atomically.

        An expected approval version makes the whole update conditional on that
        pending version and state. This prevents late re-evaluation from erasing
        an execution/receipt. Lease fields and ``attempt_count`` are NOT written
        here: they are owned by
        :meth:`claim_run` / :meth:`renew_lease` / :meth:`release_run` so a worker
        can never clear its own lease by saving a record.
        """
        ...

    def claim_run(
        self,
        run_id: UUID,
        worker_id: str,
        lease_until: datetime,
        *,
        max_attempts: int | None = None,
    ) -> bool:
        """Acquire a lease and atomically bump ``attempt_count``.

        Only :data:`CLAIMABLE_STATES` with an absent or expired lease can be
        claimed. A live lease cannot be stolen -- and cannot be "renewed" through
        this method either; use :meth:`renew_lease`.
        """
        ...

    def renew_lease(self, run_id: UUID, worker_id: str, lease_until: datetime) -> bool:
        """Extend the lease; succeeds only for the current owner."""
        ...

    def release_run(self, run_id: UUID, worker_id: str) -> None:
        """Drop the lease once processing finished (only if still owned)."""
        ...

    def transition_run(self, run_id: UUID, expected: RunState, new: RunState) -> bool:
        """Compare-and-set a state transition; the guard behind "execute once"."""
        ...

    def reserve_feeding(self, record: RunRecord) -> bool:
        """Atomically bind current facts, one owner's feeding gate and run CAS.

        No actuator may run before this commits. Unknown results or interruption
        retain the durable gate; only a known receipt can settle it. A reservation
        never counts as actually dispensed food.
        """
        ...

    def get_facts(self, owner_id: str) -> FactsSnapshot: ...

    def update_facts(
        self,
        owner_id: str,
        *,
        last_fed_minutes_ago: int | None | _Unset = UNSET,
        daily_dispensed_grams: int | None | _Unset = UNSET,
    ) -> FactsSnapshot:
        """Update mutable demo facts and bump ``facts_version``.

        ``UNSET`` leaves a column untouched; ``None`` writes SQL NULL so the fact
        becomes UNKNOWN and feeding fails closed (A09). The hard limits are not
        parameters here and cannot be edited at all.
        """
        ...

    def reset_facts(self, owner_id: str) -> FactsSnapshot:
        """Restore the documented demo defaults (also bumps ``facts_version``)."""
        ...

    def record_receipt_once(
        self,
        *,
        command_id: UUID,
        run_id: UUID,
        receipt: Receipt,
        dispense_grams: int,
    ) -> bool:
        """Idempotently store a receipt; account quota only on first success.

        Returns ``True`` when this call newly recorded the receipt, ``False``
        when the ``command_id`` was already present (no double accounting).
        """
        ...

    def count_receipts(self, run_id: UUID) -> int:
        """Test/adapter helper: number of logical receipts for a run."""
        ...

    # -- owner feedback (Day-3 / T5) ----------------------------------------

    def save_feedback(
        self,
        *,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        memory_status: MemoryStatus,
        memory_backend: MemoryBackend,
        conversation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> FeedbackRecord:
        """Persist the raw owner feedback.

        Idempotent on ``(owner_id, idempotency_key)``: a retry with the same key
        returns the EXISTING record instead of storing a duplicate, so one feedback
        item is never submitted to AgentCore twice (T5).
        """
        ...

    def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None: ...

    def list_feedback(self, owner_id: str) -> list[FeedbackRecord]:
        """Owner feedback, newest first."""
        ...

    def list_feedback_pending_extraction(self) -> list[FeedbackRecord]:
        """Feedback still in the processing lifecycle AND carrying an AgentCore event
        id: the work list for the Day-5 extraction poller (ruling 11). The status is
        compared against ``models.MEMORY_PROCESSING`` so no repository module writes
        the bare literal (ruling 12 keeps the anti-forgery whitelist unchanged).
        """
        ...

    def set_feedback_status(
        self,
        feedback_id: UUID,
        *,
        memory_status: MemoryStatus,
        agentcore_event_id: str | None = None,
        agentcore_session_id: str | None = None,
        memory_record_ids: list[str] | None = None,
    ) -> FeedbackRecord | None:
        """Update the honest memory lifecycle after an extraction attempt.

        Never writes ``available`` unless the caller really holds AgentCore record
        ids; the local backend leaves the status at ``saved``.

        Day-5 (ruling 11) makes that a hard repository invariant, not a convention:
        calling with the available status and an empty/absent ``memory_record_ids``
        raises :class:`ValueError` (fail closed) so a future wiring bug can never
        mark stored feedback as extracted memory without real AgentCore record ids
        behind it (AGENTS.md L18).
        """
        ...
