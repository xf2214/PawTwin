"""Persistence protocol and internal records.

The internal ``RunRecord`` carries bookkeeping fields (``owner_id``,
``proposal_version``, ``action_digest``, ``attempt_count``, ``lease_owner``,
``lease_until``) that are deliberately NOT part of any public response DTO.
Adapters (SQLite now, DynamoDB later) implement the same ``Repository``
protocol so the workflow never depends on a specific backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from pawtwin.models import EventIn, Proposal, Receipt, RunState

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


class Repository(Protocol):
    """Storage semantics shared by the SQLite and (future) DynamoDB adapters."""

    def create_or_get_run(self, owner_id: str, event: EventIn) -> RunRecord:
        """Return the run for ``(owner_id, event.event_id)``; dedup on redelivery."""
        ...

    def get_run(self, run_id: UUID) -> RunRecord | None:
        ...

    def list_runs(self, owner_id: str) -> list[RunRecord]:
        ...

    def count_runs(self, owner_id: str) -> int:
        """Test/adapter helper: number of runs owned by ``owner_id``."""
        ...

    def save_run(self, record: RunRecord) -> None:
        """Persist a state transition atomically."""
        ...

    def claim_run(self, run_id: UUID, worker_id: str, lease_until: datetime) -> bool:
        """Acquire a lease; expired leases are re-claimable, terminal states are not."""
        ...

    def get_facts(self, owner_id: str) -> FactsSnapshot:
        ...

    def update_facts(
        self,
        owner_id: str,
        *,
        last_fed_minutes_ago: int | None = None,
        daily_dispensed_grams: int | None = None,
    ) -> FactsSnapshot:
        """Update mutable demo facts and bump ``facts_version``."""
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
