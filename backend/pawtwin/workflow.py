"""Run state machine: intake -> analysis -> proposal -> approval -> execution.

Day-2 replaces the Day-1 inline stub with a real analyzer seam while keeping
:class:`InlineProposer` as an explicitly-selected TEST backend. Analysis is
bounded (wall-clock deadline plus a durable model-call budget) and fails closed:
an analyzer error, an unknown evidence id or an exceeded ceiling becomes FAILED
with a bounded reason code, never a canned proposal.

Two invariants protect the food and the money:

* a run is only (re)analyzed from a CLAIMABLE state, so ``EXECUTING`` can never be
  re-analyzed into a new ``command_id`` -- which would account the quota twice;
* approval goes through a compare-and-set transition, so concurrent approvals
  execute at most once (A04);
* every verdict written from the approval path -- expiry, decline, the A03
  re-evaluation and a policy block -- claims the state through a compare-and-set
  first, so a stale reader can never overwrite a run another caller has already
  settled (and can never blank its receipt).

Hard limits stay in :mod:`pawtwin.policy` and cannot be overridden by approval or
model wording.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import (
    ANALYSIS_TIMEOUT,
    ANALYZER_ERROR,
    ATTEMPTS_EXHAUSTED,
    Action,
    AnalysisOutcome,
    AnalysisTelemetry,
    ApprovalIn,
    EventIn,
    Proposal,
    RunState,
    compute_action_digest,
    failure_code_from,
    make_command_id,
    validate_proposal_evidence,
)
from pawtwin.policy import MISSING_FACTS, Facts, evaluate_policy
from pawtwin.repository import CLAIMABLE_STATES, FactsSnapshot, Repository, RunRecord

APPROVAL_WINDOW = timedelta(minutes=10)


def _now() -> datetime:
    return datetime.now(UTC)


def _elapsed_ms(started: datetime, finished: datetime) -> int:
    return max(0, int((finished - started).total_seconds() * 1000))


class Proposer(Protocol):
    """Analyzer seam (Day-2 ruling 1).

    Deliberately narrow: the workflow hands over the event, the PINNED facts
    snapshot, the owner id and the already-consumed model-call budget. It never
    hands over the ``RunRecord``, whose internal bookkeeping fields must not reach
    the model layer.
    """

    def analyze_event(
        self,
        event: EventIn,
        snapshot: FactsSnapshot,
        owner_id: str,
        *,
        model_calls_used: int = 0,
    ) -> AnalysisOutcome: ...


class ApprovalRejected(Exception):
    """An approval could not be applied. ``status_code`` maps to the HTTP reply."""

    def __init__(self, reason: str, *, status_code: int = 409) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


class AnalysisGuard:
    """Wall-clock deadline around one analysis call (rulings 16 and 17).

    The pool is created lazily and shut down by the application lifespan, so
    ``create_app`` stays side-effect free and the offline contract export never
    spawns a thread. Shutdown must NOT wait: a runaway model call may never block
    process exit, and an abandoned call cannot corrupt the run because every write
    is guarded by ``_persist_if_still_owner``.
    """

    def __init__(self, timeout_seconds: float, *, max_workers: int = 4) -> None:
        self._timeout = timeout_seconds
        self._max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None

    def _pool(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="pawtwin-analysis",
            )
        return self._executor

    def run(self, call: Callable[[], AnalysisOutcome]) -> AnalysisOutcome:
        future = self._pool().submit(call)
        try:
            return future.result(timeout=self._timeout)
        except FutureTimeout as exc:
            # The thread keeps running; the lease/ownership guard below is what
            # stops its late result from overwriting the FAILED verdict.
            future.cancel()
            raise TimeoutError(ANALYSIS_TIMEOUT) from exc

    def shutdown(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None


class InlineProposer:
    """Deterministic TEST backend (``PAWTWIN_MODEL_BACKEND=inline``).

    Uses only structured facts and the event kind -- never the free-text note and
    never a scenario label -- so a judge changing facts changes the proposal. It
    makes no model call and cites no evidence id, which keeps the Day-1 ruling
    "the decline loop does not depend on the AI stand-in" true.
    """

    backend = "inline"

    def analyze_event(
        self,
        event: EventIn,
        snapshot: FactsSnapshot,
        owner_id: str,
        *,
        model_calls_used: int = 0,
    ) -> AnalysisOutcome:
        started = _now()
        proposal = _inline_proposal(event, to_policy_facts(snapshot))
        finished = _now()
        return AnalysisOutcome(
            proposal=proposal,
            evidence=[],
            telemetry=AnalysisTelemetry(
                backend="inline",
                model_calls=0,
                output_tokens=0,
                duration_ms=_elapsed_ms(started, finished),
                started_at=started,
                finished_at=finished,
            ),
        )


class Workflow:
    def __init__(
        self,
        repo: Repository,
        device: DeviceSimulator,
        *,
        proposer: Proposer | None = None,
        guard: AnalysisGuard | None = None,
        lease_seconds: int = 60,
        max_attempts: int = 2,
    ) -> None:
        self._repo = repo
        self._device = device
        self._proposer = proposer
        self._guard = guard
        self._lease_seconds = lease_seconds
        self._max_attempts = max_attempts

    # -- intake -------------------------------------------------------------

    def handle_event(self, owner_id: str, event: EventIn) -> RunRecord:
        """Intake plus analysis in the calling thread (``worker_mode=inline``).

        It goes through exactly the same claim/deadline/budget path as the
        background worker, so the tested code path is the shipped one.
        """

        record = self._repo.create_or_get_run(owner_id, event)
        if record.state != RunState.QUEUED:
            # De-duplicated redelivery: return the existing run untouched, and
            # never spend another model call on it (A05).
            return record
        analyzed = self.analyze_run(record.run_id, "inline")
        return analyzed if analyzed is not None else record

    def enqueue_event(self, owner_id: str, event: EventIn) -> RunRecord:
        """Persist only; a background worker picks it up (returns QUEUED)."""

        return self._repo.create_or_get_run(owner_id, event)

    # -- analysis -----------------------------------------------------------

    def analyze_run(self, run_id: UUID, worker_id: str) -> RunRecord | None:
        """Claim a run, analyze it under the deadline and budget, then persist."""

        record = self._repo.get_run(run_id)
        if record is None or record.state not in CLAIMABLE_STATES:
            return record

        lease_until = _now() + timedelta(seconds=self._lease_seconds)
        claimed = self._repo.claim_run(
            run_id, worker_id, lease_until, max_attempts=self._max_attempts
        )
        if not claimed:
            fresh = self._repo.get_run(run_id)
            if fresh is None:
                return None
            lease_free = fresh.lease_until is None or fresh.lease_until < _now()
            if (
                fresh.state in CLAIMABLE_STATES
                and lease_free
                and fresh.attempt_count >= self._max_attempts
            ):
                # Durable ceiling: two attempts and no more, then a visible
                # failure. Only when no live lease is held, and only through a
                # compare-and-set, so a worker that IS analyzing is never
                # overruled by a bystander.
                return self._fail_unclaimed(fresh, ATTEMPTS_EXHAUSTED)
            return fresh

        try:
            return self._analyze_claimed(record, worker_id)
        finally:
            self._repo.release_run(run_id, worker_id)

    def _analyze_claimed(self, record: RunRecord, worker_id: str) -> RunRecord:
        snapshot = self._repo.get_facts(record.owner_id)
        # The lease itself is already set by claim_run; save_run never writes it.
        record.state = RunState.ANALYZING
        self._repo.save_run(record)
        try:
            outcome = self._propose_guarded(record, snapshot)
            return self._apply_outcome(record, snapshot, outcome, worker_id)
        except Exception as exc:  # noqa: BLE001 - every analyzer failure fails closed
            return self._fail(record, failure_code_from(exc), worker_id)

    def _propose_guarded(self, record: RunRecord, snapshot: FactsSnapshot) -> AnalysisOutcome:
        if record.event is None:
            raise ValueError(f"{ANALYZER_ERROR}: run has no event payload")
        proposer = self._proposer or InlineProposer()
        event = record.event
        owner_id = record.owner_id
        budget = record.model_calls_used

        def call() -> AnalysisOutcome:
            return proposer.analyze_event(
                event, snapshot, owner_id, model_calls_used=budget
            )

        if self._guard is not None:
            return self._guard.run(call)
        return call()

    def _apply_outcome(
        self,
        record: RunRecord,
        snapshot: FactsSnapshot,
        outcome: AnalysisOutcome,
        worker_id: str,
    ) -> RunRecord:
        # Unconditional evidence enforcement (ruling 3 / gate G1): a proposal may
        # only cite evidence THIS analysis really retrieved.
        validate_proposal_evidence(
            outcome.proposal,
            {item.evidence_id for item in outcome.evidence},
        )
        proposal = outcome.proposal
        result = evaluate_policy(proposal.action, to_policy_facts(snapshot))

        record.proposal = proposal
        record.proposal_version += 1
        record.action_digest = compute_action_digest(proposal.action)
        record.facts_version = snapshot.facts_version
        record.policy_reason = result.reason
        record.failure_reason = None
        record.receipt = None
        record.evidence = list(outcome.evidence)
        record.telemetry = outcome.telemetry
        record.model_calls_used += outcome.telemetry.model_calls

        if result.reason == MISSING_FACTS or proposal.missing_fields:
            # A09: "not enough information" is the verdict whenever a required fact
            # is unknown -- even when the analyzer fell back to proposing
            # ``observe``, which the feeding policy always allows. Showing "awaiting
            # approval" there would hide the gap from the owner. This is the
            # fail-safe direction: an over-declared gap costs a re-run, never food.
            record.state = RunState.NEEDS_INFO
            # Report the REAL reason: the observe fallback would otherwise be
            # labelled NON_FEEDING right next to a "information missing" verdict.
            record.policy_reason = MISSING_FACTS
            record.expires_at = None
        elif result.allowed:
            record.state = RunState.AWAITING_APPROVAL
            record.expires_at = _now() + APPROVAL_WINDOW
        else:
            record.state = RunState.BLOCKED
            record.expires_at = None

        self._persist_if_still_owner(record, worker_id)
        return record

    def _fail(self, record: RunRecord, reason: str, worker_id: str) -> RunRecord:
        """Visible failure. Never a fallback to the inline stub or a canned answer."""

        record.state = RunState.FAILED
        record.failure_reason = reason
        record.expires_at = None
        self._persist_if_still_owner(record, worker_id)
        return record

    def _fail_unclaimed(self, record: RunRecord, reason: str) -> RunRecord:
        """Fail a run this worker does not hold a lease for (attempts exhausted)."""

        if not self._repo.transition_run(record.run_id, record.state, RunState.FAILED):
            current = self._repo.get_run(record.run_id)
            return current if current is not None else record
        record.state = RunState.FAILED
        record.failure_reason = reason
        record.expires_at = None
        self._repo.save_run(record)
        return record

    def _persist_if_still_owner(self, record: RunRecord, worker_id: str) -> bool:
        """Drop the write if this attempt was abandoned (deadline) or re-claimed.

        ``future.result(timeout=...)`` cannot terminate the running thread, so a
        late result would otherwise overwrite the FAILED verdict.
        """

        fresh = self._repo.get_run(record.run_id)
        if fresh is None or fresh.lease_owner != worker_id:
            return False
        self._repo.save_run(record)
        return True

    # -- approval -----------------------------------------------------------

    def handle_approval(self, owner_id: str, run_id: UUID, approval: ApprovalIn) -> RunRecord:
        record = self._repo.get_run(run_id)
        if record is None or record.owner_id != owner_id:
            raise ApprovalRejected("RUN_NOT_FOUND", status_code=404)

        self._expire_if_due(record)

        if record.state != RunState.AWAITING_APPROVAL:
            raise ApprovalRejected("NOT_AWAITING_APPROVAL")

        if (
            approval.proposal_version != record.proposal_version
            or approval.action_digest != record.action_digest
        ):
            raise ApprovalRejected("APPROVAL_MISMATCH")

        if approval.decision == "decline":
            # Compare-and-set: a second concurrent decline cannot flip anything.
            if not self._settle(record, RunState.DECLINED):
                raise ApprovalRejected("NOT_AWAITING_APPROVAL")
            return record

        # Approve path: facts may have moved since the proposal was produced.
        snapshot = self._repo.get_facts(owner_id)
        if snapshot.facts_version != record.facts_version:
            # A03 (ruling 11): re-evaluate the policy WITHOUT calling the model.
            self._reevaluate_under_new_facts(record, snapshot)
            raise ApprovalRejected("STALE_APPROVAL_FACTS_CHANGED")

        assert record.proposal is not None  # noqa: S101 - awaiting approval implies a proposal
        result = evaluate_policy(record.proposal.action, to_policy_facts(snapshot))
        if not result.allowed:
            record.policy_reason = result.reason
            if not self._settle(record, RunState.BLOCKED):
                raise ApprovalRejected("NOT_AWAITING_APPROVAL")
            raise ApprovalRejected("POLICY_BLOCKED_ON_EXECUTE")

        # A04: this compare-and-set is what makes "execute at most once" real. Two
        # concurrent approvals cannot both reach the simulated actuator.
        if not self._repo.transition_run(run_id, RunState.AWAITING_APPROVAL, RunState.EXECUTING):
            raise ApprovalRejected("NOT_AWAITING_APPROVAL")
        record.state = RunState.EXECUTING
        return self._execute(record)

    def _expire_if_due(self, record: RunRecord) -> bool:
        """Close an approval window that has run out, or write nothing at all.

        Expiry has to LOSE to a concurrent approval that already moved the run out
        of ``AWAITING_APPROVAL``. The plain read-modify-write used here before
        overwrote the winner's terminal state and -- because ``save_run`` also
        writes ``receipt_json`` -- blanked the receipt of a run whose food had
        already been dispensed and accounted for.
        """

        if (
            record.state != RunState.AWAITING_APPROVAL
            or record.expires_at is None
            or _now() < record.expires_at
        ):
            return False
        return self._settle(record, RunState.EXPIRED)

    def _settle(self, record: RunRecord, new: RunState) -> bool:
        """Claim ``new`` through a CAS and only then persist the rest of the record.

        The single write primitive of the approval path: a stale reader whose run
        was settled by a concurrent caller gets ``False`` and must abandon its
        write, which is what keeps a terminal state and its receipt intact.

        ``record.expires_at`` is whatever the caller decided: a fresh window when
        the verdict stays ``AWAITING_APPROVAL`` (the A03 re-evaluation), ``None``
        for every settled verdict. It is never overwritten here.
        """

        if record.state == new:
            # Nothing to claim; persist the caller's verdict on its own row.
            self._repo.save_run(record)
            return True
        if not self._repo.transition_run(record.run_id, RunState.AWAITING_APPROVAL, new):
            return False
        record.state = new
        record.expires_at = None
        self._repo.save_run(record)
        return True

    def _reevaluate_under_new_facts(
        self, record: RunRecord, snapshot: FactsSnapshot
    ) -> RunRecord:
        """A03 with ZERO model calls: same bound action, new policy verdict.

        Keeping the action means ``action_digest`` is unchanged (it is derived
        deterministically) while ``proposal_version`` still bumps, so the stale
        approval is rejected and the owner must confirm the new verdict. Evidence
        keeps its ORIGINAL ``retrieved_at``: nothing was re-fetched, and pretending
        otherwise would misrepresent the record.
        """

        assert record.proposal is not None  # noqa: S101
        result = evaluate_policy(record.proposal.action, to_policy_facts(snapshot))
        record.facts_version = snapshot.facts_version
        record.proposal_version += 1
        record.action_digest = compute_action_digest(record.proposal.action)
        record.policy_reason = result.reason
        record.failure_reason = None

        if result.reason == MISSING_FACTS or record.proposal.missing_fields:
            verdict = RunState.NEEDS_INFO
            record.policy_reason = MISSING_FACTS
            record.expires_at = None
        elif result.allowed:
            verdict = RunState.AWAITING_APPROVAL
            record.expires_at = _now() + APPROVAL_WINDOW
        else:
            verdict = RunState.BLOCKED
            record.expires_at = None

        if not self._settle(record, verdict):
            # Someone else settled the run while this caller was re-reading the
            # facts: drop the re-evaluation instead of overwriting their verdict.
            fresh = self._repo.get_run(record.run_id)
            return fresh if fresh is not None else record
        return record

    def _execute(self, record: RunRecord) -> RunRecord:
        assert record.proposal is not None  # noqa: S101
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
    """Deterministic stand-in for the AI analyzer (TEST backend only).

    Uses only structured facts/event kind, never the free-text note or a scenario
    label, so a judge changing facts changes the proposal. It cites no evidence id
    because it performs no retrieval; an empty list passes evidence validation,
    while an invented id such as ``pet_facts`` would (correctly) not.

    It declares ``missing_fields`` for every required fact that is NULL, exactly
    like the ``local_fake`` stand-in: ``evaluate_policy`` always allows the
    ``observe`` fallback, so without this the workflow could not tell "unknown
    fact" apart from "nothing to feed" (A09 would degrade to AWAITING_APPROVAL).
    """

    if event is not None and event.kind == "attention_request":
        return Proposal(
            action=Action(kind="create_play_task", grams=0),
            explanation=(
                "互动请求：建议创建一个陪玩任务，不涉及喂食。"
                "是否执行仍由硬性策略与主人审批决定。"
            ),
            evidence_ids=[],
        )

    missing = [
        name
        for name in ("last_fed_minutes_ago", "daily_dispensed_grams")
        if getattr(facts, name) is None
    ]
    if missing:
        labels = {
            "last_fed_minutes_ago": "上次喂食时间",
            "daily_dispensed_grams": "当日已出粮量",
        }
        listed = "、".join(labels[name] for name in missing)
        return Proposal(
            action=Action(kind="observe", grams=0),
            explanation=(
                f"缺少必要事实（{listed}），无法给出喂食建议，仅建议观察；"
                "补全事实后重新发送请求即可。"
            ),
            evidence_ids=[],
            missing_fields=missing,
        )

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
    return Proposal(action=action, explanation=explanation, evidence_ids=[])
