"""Run state machine: intake -> proposal -> approval -> simulated execution.

Day-1 ships a deterministic inline proposer so the decline loop does not depend
on the AI adapter or any local fake. The proposer reads only ``Facts``; it never
branches on a scenario name or the free-text ``note``. Hard limits stay in
:mod:`pawtwin.policy` and cannot be overridden by approval or model wording.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import (
    Action,
    ApprovalIn,
    EventIn,
    Proposal,
    RunState,
    compute_action_digest,
    make_command_id,
)
from pawtwin.policy import MISSING_FACTS, Facts, evaluate_policy
from pawtwin.repository import FactsSnapshot, Repository, RunRecord

APPROVAL_WINDOW = timedelta(minutes=10)


def _now() -> datetime:
    return datetime.now(UTC)


class Proposer(Protocol):
    """Analyzer seam. Day-2 swaps the inline stub for the AI agent adapter."""

    def analyze_event(self, event: EventIn, facts: Facts) -> Proposal: ...


class ApprovalRejected(Exception):
    """An approval could not be applied. ``status_code`` maps to the HTTP reply."""

    def __init__(self, reason: str, *, status_code: int = 409) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


class Workflow:
    def __init__(
        self,
        repo: Repository,
        device: DeviceSimulator,
        *,
        proposer: Proposer | None = None,
    ) -> None:
        self._repo = repo
        self._device = device
        self._proposer = proposer

    # -- intake -------------------------------------------------------------

    def handle_event(self, owner_id: str, event: EventIn) -> RunRecord:
        record = self._repo.create_or_get_run(owner_id, event)
        if record.state != RunState.QUEUED:
            # De-duplicated redelivery: return the existing run untouched.
            return record
        return self._analyze(record)

    def _analyze(self, record: RunRecord) -> RunRecord:
        snapshot = self._repo.get_facts(record.owner_id)
        return self._analyze_with_facts(record, snapshot)

    def _analyze_with_facts(self, record: RunRecord, snapshot: FactsSnapshot) -> RunRecord:
        facts = to_policy_facts(snapshot)
        proposal = self._propose(record, facts)
        result = evaluate_policy(proposal.action, facts)

        record.proposal = proposal
        record.proposal_version += 1
        record.action_digest = compute_action_digest(proposal.action)
        record.facts_version = snapshot.facts_version
        record.policy_reason = result.reason
        record.receipt = None
        record.lease_owner = None
        record.lease_until = None

        if result.reason == MISSING_FACTS:
            record.state = RunState.NEEDS_INFO
            record.expires_at = None
        elif result.allowed:
            record.state = RunState.AWAITING_APPROVAL
            record.expires_at = _now() + APPROVAL_WINDOW
        else:
            record.state = RunState.BLOCKED
            record.expires_at = None

        self._repo.save_run(record)
        return record

    def _propose(self, record: RunRecord, facts: Facts) -> Proposal:
        if self._proposer is not None and record.event is not None:
            return self._proposer.analyze_event(record.event, facts)
        return _inline_proposal(record.event, facts)

    # -- approval -----------------------------------------------------------

    def handle_approval(self, owner_id: str, run_id: UUID, approval: ApprovalIn) -> RunRecord:
        record = self._repo.get_run(run_id)
        if record is None or record.owner_id != owner_id:
            raise ApprovalRejected("RUN_NOT_FOUND", status_code=404)

        if (
            record.state == RunState.AWAITING_APPROVAL
            and record.expires_at is not None
            and _now() >= record.expires_at
        ):
            record.state = RunState.EXPIRED
            record.expires_at = None
            self._repo.save_run(record)

        if record.state != RunState.AWAITING_APPROVAL:
            raise ApprovalRejected("NOT_AWAITING_APPROVAL")

        if (
            approval.proposal_version != record.proposal_version
            or approval.action_digest != record.action_digest
        ):
            raise ApprovalRejected("APPROVAL_MISMATCH")

        if approval.decision == "decline":
            record.state = RunState.DECLINED
            record.expires_at = None
            self._repo.save_run(record)
            return record

        # Approve path: facts may have moved since the proposal was produced.
        snapshot = self._repo.get_facts(owner_id)
        if snapshot.facts_version != record.facts_version:
            # A03: an old approval can never drive a new action; re-analyze and
            # require a fresh approval under the new facts.
            self._analyze_with_facts(record, snapshot)
            raise ApprovalRejected("STALE_APPROVAL_FACTS_CHANGED")

        assert record.proposal is not None  # noqa: S101 - awaiting approval implies a proposal
        result = evaluate_policy(record.proposal.action, to_policy_facts(snapshot))
        if not result.allowed:
            record.state = RunState.BLOCKED
            record.policy_reason = result.reason
            record.expires_at = None
            self._repo.save_run(record)
            raise ApprovalRejected("POLICY_BLOCKED_ON_EXECUTE")

        return self._execute(record)

    def _execute(self, record: RunRecord) -> RunRecord:
        assert record.proposal is not None  # noqa: S101
        record.state = RunState.EXECUTING
        self._repo.save_run(record)

        command_id = make_command_id(record.run_id, record.proposal_version)
        receipt = self._device.execute(command_id, record.proposal.action)
        dispense = (
            record.proposal.action.grams
            if record.proposal.action.kind == "dispense_food"
            else 0
        )
        # Idempotent: a repeated command_id never double-accounts the quota.
        self._repo.record_receipt_once(
            command_id=command_id,
            run_id=record.run_id,
            receipt=receipt,
            dispense_grams=dispense,
        )

        record.receipt = receipt
        record.expires_at = None
        if receipt.status == "succeeded":
            record.state = RunState.SUCCEEDED
        elif receipt.status == "failed":
            record.state = RunState.FAILED
        else:
            record.state = RunState.UNKNOWN
        self._repo.save_run(record)
        return record


def to_policy_facts(snapshot: FactsSnapshot) -> Facts:
    return Facts(
        last_fed_minutes_ago=snapshot.last_fed_minutes_ago,
        daily_dispensed_grams=snapshot.daily_dispensed_grams,
        daily_limit_grams=snapshot.daily_limit_grams,
        minimum_interval_minutes=snapshot.minimum_interval_minutes,
        single_serving_grams=snapshot.single_serving_grams,
    )


def _inline_proposal(event: EventIn | None, facts: Facts) -> Proposal:
    """Deterministic stand-in for the AI analyzer (replaced on Day-2).

    Uses only structured facts/event kind, never the free-text note or a
    scenario label, so a judge changing facts changes the proposal.
    """

    if event is not None and event.kind == "attention_request":
        return Proposal(
            action=Action(kind="create_play_task", grams=0),
            explanation=(
                "互动请求：建议创建一个陪玩任务，不涉及喂食。"
                "是否执行仍由硬性策略与主人审批决定。"
            ),
            evidence_ids=["pet_facts"],
        )

    remaining = 0
    if facts.daily_dispensed_grams is not None:
        remaining = max(0, facts.daily_limit_grams - facts.daily_dispensed_grams)
    grams = min(facts.single_serving_grams, remaining)
    if grams >= 1:
        action = Action(kind="dispense_food", grams=grams)
    else:
        action = Action(kind="observe", grams=0)

    explanation = (
        f"依据当前事实生成建议：上次喂食距今 {facts.last_fed_minutes_ago} 分钟、"
        f"当日已出粮 {facts.daily_dispensed_grams} 克、日配额 {facts.daily_limit_grams} 克、"
        f"单次上限 {facts.single_serving_grams} 克。展示文案为推测，最终以硬性策略与主人审批为准。"
    )
    return Proposal(action=action, explanation=explanation, evidence_ids=["pet_facts"])
