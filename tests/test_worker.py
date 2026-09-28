"""Worker, lease and concurrency tests (Day-2 gates G2/G3/G5).

Everything here is LOCAL and uses a programmable test double instead of a model,
so these tests prove the deadline, the durable call budget, the claim whitelist
and the compare-and-set guards. They are NOT cloud evidence.
"""

import threading
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pawtwin.agent import AnalyzerProposer
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import (
    ANALYSIS_TIMEOUT,
    ANALYZER_ERROR,
    ATTEMPTS_EXHAUSTED,
    MODEL_CALL_LIMIT,
    UNKNOWN_EVIDENCE,
    Action,
    AnalysisOutcome,
    AnalysisTelemetry,
    ApprovalIn,
    EventIn,
    Proposal,
    RunState,
)
from pawtwin.policy import MISSING_FACTS
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.repository import CLAIMABLE_STATES
from pawtwin.worker import AdmissionControl, AnalysisWorker
from pawtwin.workflow import AnalysisGuard, ApprovalRejected, Workflow


def _now() -> datetime:
    return datetime.now(UTC)


def _food_event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="food_request", room="kitchen")


def _outcome(model_calls: int = 1, output_tokens: int = 100) -> AnalysisOutcome:
    started = _now()
    return AnalysisOutcome(
        proposal=Proposal(
            action=Action(kind="dispense_food", grams=15),
            explanation="programmable test proposal",
            evidence_ids=[],
        ),
        evidence=[],
        telemetry=AnalysisTelemetry(
            backend="inline",
            model_calls=model_calls,
            output_tokens=output_tokens,
            duration_ms=1,
            started_at=started,
            finished_at=_now(),
        ),
    )


class ProgrammableProposer:
    """Test double with a real call counter; can sleep, fail or over-report."""

    backend = "inline"

    def __init__(
        self,
        *,
        delay: float = 0.0,
        error: BaseException | None = None,
        model_calls: int = 1,
        output_tokens: int = 100,
        evidence_ids: list[str] | None = None,
    ) -> None:
        self.calls = 0
        self._delay = delay
        self._error = error
        self._model_calls = model_calls
        self._output_tokens = output_tokens
        self._evidence_ids = evidence_ids or []

    def analyze_event(
        self,
        event: EventIn,
        snapshot: object,
        owner_id: str,
        *,
        model_calls_used: int = 0,
    ) -> AnalysisOutcome:
        self.calls += 1
        if self._delay:
            time.sleep(self._delay)
        if self._error is not None:
            raise self._error
        outcome = _outcome(self._model_calls, self._output_tokens)
        if self._evidence_ids:
            outcome.proposal.evidence_ids = list(self._evidence_ids)
        return outcome


class ProgrammableAnalyzer:
    """EventAnalyzer-shaped double: takes an AgentContext, reports call counts."""

    label = "local_fake"

    def __init__(self, *, model_calls: int = 1, output_tokens: int = 100) -> None:
        self.calls = 0
        self._model_calls = model_calls
        self._output_tokens = output_tokens

    def analyze_event(self, event: EventIn, context: object) -> AnalysisOutcome:
        self.calls += 1
        return _outcome(self._model_calls, self._output_tokens)


class CountingDevice(DeviceSimulator):
    """Counts actuator invocations: the evidence for "execute at most once"."""

    def __init__(self, mode: str = "succeeded") -> None:
        super().__init__(mode)  # type: ignore[arg-type]
        self.execute_calls = 0
        self._counter_lock = threading.Lock()

    def execute(self, command_id, action):  # type: ignore[no-untyped-def]
        with self._counter_lock:
            self.execute_calls += 1
        return super().execute(command_id, action)


def _wait_for(predicate, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("condition was not met in time")


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, worker_mode="inline", **overrides)  # type: ignore[arg-type]


# --- claim whitelist (ruling 7) ---------------------------------------------


def test_claimable_states_are_exactly_queued_and_analyzing() -> None:
    assert set(CLAIMABLE_STATES) == {RunState.QUEUED, RunState.ANALYZING}


def test_no_state_waiting_on_a_human_or_on_the_device_can_be_claimed(
    repo: SqliteRepository,
) -> None:
    """The defect this guards: re-claiming EXECUTING would re-analyze it, bump
    proposal_version, mint a NEW command_id and account the quota a second time.
    Re-claiming AWAITING_APPROVAL would invalidate an approval already on screen.
    """

    future = _now() + timedelta(seconds=60)
    for state in RunState:
        record = repo.create_or_get_run(DEMO_OWNER_ID, _food_event())
        if state is not RunState.QUEUED:
            assert repo.transition_run(record.run_id, RunState.QUEUED, state) is True

        claimed = repo.claim_run(record.run_id, "worker-1", future)

        assert claimed is (state in CLAIMABLE_STATES), state


def test_executing_run_keeps_its_receipt_and_command_identity(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    repo.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING)
    workflow = Workflow(repo, CountingDevice(), proposer=ProgrammableProposer())
    analyzed = workflow.analyze_run(record.run_id, "worker-1")
    assert analyzed is not None
    version_before = analyzed.proposal_version

    # Nobody may re-analyze it out of a settled state.
    assert repo.claim_run(record.run_id, "worker-2", _now() + timedelta(seconds=60)) is False
    assert workflow.analyze_run(record.run_id, "worker-2") is not None
    after = repo.get_run(record.run_id)
    assert after is not None
    assert after.proposal_version == version_before


# --- leases (ruling 8) -------------------------------------------------------


def test_claim_bumps_attempts_atomically_and_enforces_the_ceiling(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    past = _now() - timedelta(seconds=1)

    assert repo.claim_run(record.run_id, "w1", past) is True
    assert repo.get_run(record.run_id).attempt_count == 1  # type: ignore[union-attr]
    # An expired lease is re-claimable, and the counter is durable.
    assert repo.claim_run(record.run_id, "w2", past) is True
    assert repo.get_run(record.run_id).attempt_count == 2  # type: ignore[union-attr]
    assert repo.claim_run(record.run_id, "w3", past, max_attempts=2) is False


def test_live_lease_cannot_be_stolen_but_can_be_renewed_by_its_owner(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    future = _now() + timedelta(seconds=60)
    assert repo.claim_run(record.run_id, "w1", future) is True

    assert repo.claim_run(record.run_id, "w2", future) is False
    # claim_run can never renew (its predicate rejects a live lease for everyone),
    # which is exactly why renew_lease exists.
    assert repo.renew_lease(record.run_id, "w2", future) is False
    assert repo.renew_lease(record.run_id, "w1", _now() + timedelta(seconds=120)) is True


def test_release_run_only_clears_the_owners_lease(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    assert repo.claim_run(record.run_id, "w1", _now() + timedelta(seconds=60)) is True

    repo.release_run(record.run_id, "someone-else")
    assert repo.get_run(record.run_id).lease_owner == "w1"  # type: ignore[union-attr]
    repo.release_run(record.run_id, "w1")
    assert repo.get_run(record.run_id).lease_owner is None  # type: ignore[union-attr]


def test_save_run_never_clears_the_lease(repo: SqliteRepository, food_event: EventIn) -> None:
    """Regression for the Day-1 defect: the analyzer used to null its own lease."""

    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    future = _now() + timedelta(seconds=60)
    assert repo.claim_run(record.run_id, "w1", future) is True

    fresh = repo.get_run(record.run_id)
    assert fresh is not None
    fresh.lease_owner = None
    fresh.lease_until = None
    fresh.attempt_count = 99
    repo.save_run(fresh)

    after = repo.get_run(record.run_id)
    assert after is not None
    assert after.lease_owner == "w1"
    assert after.lease_until is not None
    assert after.attempt_count == 1
    assert repo.claim_run(record.run_id, "w2", future) is False


def test_transition_run_is_compare_and_set(repo: SqliteRepository, food_event: EventIn) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    assert repo.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is True
    assert repo.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is False


# --- deadline and budgets (gate G2) ------------------------------------------


def test_analysis_timeout_fails_closed_with_a_bounded_reason(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    guard = AnalysisGuard(0.05)
    proposer = ProgrammableProposer(delay=1.0)
    workflow = Workflow(repo, DeviceSimulator(), proposer=proposer, guard=guard)
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    try:
        result = workflow.analyze_run(record.run_id, "w1")
    finally:
        guard.shutdown()

    assert result is not None
    assert result.state == RunState.FAILED
    assert result.failure_reason == ANALYSIS_TIMEOUT
    # Never a canned answer, and never the inline stub stepping in.
    assert result.proposal is None
    assert result.receipt is None
    assert repo.count_receipts(record.run_id) == 0


def test_analyzer_error_fails_closed_and_never_falls_back(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    proposer = ProgrammableProposer(error=RuntimeError("model exploded"))
    workflow = Workflow(repo, DeviceSimulator(), proposer=proposer)
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    result = workflow.analyze_run(record.run_id, "w1")

    assert result is not None
    assert result.state == RunState.FAILED
    assert result.failure_reason == ANALYZER_ERROR
    assert result.proposal is None


def test_unknown_evidence_from_the_analyzer_fails_the_run(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    proposer = ProgrammableProposer(evidence_ids=["invented-id"])
    workflow = Workflow(repo, DeviceSimulator(), proposer=proposer)
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    result = workflow.analyze_run(record.run_id, "w1")

    assert result is not None
    assert result.state == RunState.FAILED
    assert result.failure_reason == UNKNOWN_EVIDENCE
    # FAILED is terminal, so the worker can never loop and burn calls on it.
    assert repo.claim_run(record.run_id, "w2", _now() + timedelta(seconds=60)) is False


def test_durable_budget_refuses_a_fifth_model_call(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    inner = ProgrammableAnalyzer(model_calls=4)
    proposer = AnalyzerProposer(inner, repo, max_model_calls=4)
    workflow = Workflow(repo, DeviceSimulator(), proposer=proposer, max_attempts=2)
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    first = workflow.analyze_run(record.run_id, "w1")
    assert first is not None
    assert first.model_calls_used == 4

    # Re-queue as a crashed attempt would be; the budget is durable, so no restart
    # and no re-claim can lift the ceiling.
    assert repo.transition_run(record.run_id, RunState.AWAITING_APPROVAL, RunState.QUEUED) is True
    second = workflow.analyze_run(record.run_id, "w2")

    assert second is not None
    assert second.state == RunState.FAILED
    assert second.failure_reason == MODEL_CALL_LIMIT
    assert inner.calls == 1


def test_attempts_ceiling_produces_a_visible_failure(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    workflow = Workflow(repo, DeviceSimulator(), proposer=ProgrammableProposer(), max_attempts=2)
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    past = _now() - timedelta(seconds=1)
    assert repo.claim_run(record.run_id, "w1", past) is True
    assert repo.claim_run(record.run_id, "w2", past) is True
    repo.release_run(record.run_id, "w2")

    result = workflow.analyze_run(record.run_id, "w3")

    assert result is not None
    assert result.state == RunState.FAILED
    assert result.failure_reason == ATTEMPTS_EXHAUSTED
    assert result.attempt_count == 2


# --- worker loop and admission (gate G3) -------------------------------------


def test_worker_drains_a_queued_run_then_leaves_it_alone(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    workflow = Workflow(repo, DeviceSimulator(), proposer=ProgrammableProposer())
    worker = AnalysisWorker(repo, workflow, _settings(lease_renew_seconds=1), poll_interval=0.05)
    queued = workflow.enqueue_event(DEMO_OWNER_ID, food_event)
    assert queued.state == RunState.QUEUED

    worker.start()
    try:
        _wait_for(
            lambda: (repo.get_run(queued.run_id) or queued).state == RunState.AWAITING_APPROVAL
        )
        version = (repo.get_run(queued.run_id) or queued).proposal_version
        _wait_for(lambda: worker.processed >= 1)
        # A settled run is never picked up again.
        assert repo.list_claimable_runs() == []
        assert worker.drain_once() == 0
        assert (repo.get_run(queued.run_id) or queued).proposal_version == version
    finally:
        worker.stop()

    assert worker.running is False


def test_worker_stop_is_idempotent_and_fast(repo: SqliteRepository) -> None:
    workflow = Workflow(repo, DeviceSimulator(), proposer=ProgrammableProposer())
    worker = AnalysisWorker(repo, workflow, _settings(), poll_interval=0.05)

    worker.stop()  # never started
    worker.start()
    started = time.monotonic()
    worker.stop(timeout=2.0)

    assert worker.running is False
    assert time.monotonic() - started < 3.0


def test_admission_control_enforces_both_ceilings() -> None:
    admission = AdmissionControl(per_session=1, global_limit=2)

    assert admission.try_acquire("owner-a") is True
    assert admission.try_acquire("owner-a") is False  # per-session ceiling
    assert admission.try_acquire("owner-b") is True
    assert admission.try_acquire("owner-c") is False  # site-wide ceiling
    assert admission.active == 2

    admission.release("owner-a")
    assert admission.try_acquire("owner-c") is True
    assert admission.active == 2


# --- concurrent approval (gate G5 / A04) -------------------------------------


def test_concurrent_approvals_execute_the_device_exactly_once(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    device = CountingDevice()
    workflow = Workflow(repo, device, proposer=ProgrammableProposer())
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    assert record.proposal is not None
    approval = ApprovalIn(
        decision="approve",
        proposal_version=record.proposal_version,
        action_digest=record.action_digest or "",
    )

    barrier = threading.Barrier(2, timeout=10)
    outcomes: list[object] = []
    lock = threading.Lock()

    def approve() -> None:
        barrier.wait()
        try:
            result = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)
            with lock:
                outcomes.append(result.state)
        except Exception as exc:  # noqa: BLE001 - recorded, asserted below
            with lock:
                outcomes.append(exc)

    threads = [threading.Thread(target=approve) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    assert device.execute_calls == 1
    assert repo.count_receipts(record.run_id) == 1
    assert outcomes.count(RunState.SUCCEEDED) == 1
    rejections = [item for item in outcomes if isinstance(item, Exception)]
    assert len(rejections) == 1
    # WHICH rejection the loser gets depends on the interleaving, and both are
    # correct: ``NOT_AWAITING_APPROVAL`` when it loses the state CAS, or
    # ``STALE_APPROVAL_FACTS_CHANGED`` when the winner had already accounted the
    # quota (bumping facts_version) before this thread read the record. Asserting
    # a single reason made this test flaky without any product defect behind it;
    # the invariant that matters is the two counts above.
    assert getattr(rejections[0], "reason", None) in {
        "NOT_AWAITING_APPROVAL",
        "STALE_APPROVAL_FACTS_CHANGED",
    }
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == record.proposal.action.grams


# --- expiry never overwrites a settled run (gate G5 / A04) --------------------


def test_late_expiry_write_cannot_blank_an_already_executed_receipt(
    repo: SqliteRepository, food_event: EventIn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale reader must not turn an executed run into EXPIRED with no receipt.

    The interleaving is reproduced at the only place it can happen: the stale
    caller reads the record while it is still awaiting approval with a window
    that has just closed, and a concurrent approval completes the execution
    inside that read-before-write gap. The old read-modify-write then erased both
    the terminal state and ``receipt_json`` of a run whose food had already been
    dispensed and accounted for.
    """

    device = CountingDevice()
    workflow = Workflow(repo, device, proposer=ProgrammableProposer())
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    approval = ApprovalIn(
        decision="approve",
        proposal_version=record.proposal_version,
        action_digest=record.action_digest or "",
    )

    real_get_run = repo.get_run
    fired: list[bool] = []

    def racy_get_run(run_id):  # type: ignore[no-untyped-def]
        fresh = real_get_run(run_id)
        # Hand the caller the stale copy first, then let the rival approval win
        # the race before this caller gets to write.
        if fresh is not None and fresh.state == RunState.AWAITING_APPROVAL and not fired:
            fired.append(True)
            fresh.expires_at = _now() - timedelta(seconds=1)  # the window closed
            winner = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)
            assert winner.state == RunState.SUCCEEDED
        return fresh

    monkeypatch.setattr(repo, "get_run", racy_get_run)

    with pytest.raises(ApprovalRejected) as excinfo:
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)

    assert fired == [True]
    # Either rejection is honest; what matters is that NOTHING was written. (With
    # the fix the expiry CAS loses, so control reaches the A03 facts check, whose
    # version moved when the winner accounted the quota.)
    assert excinfo.value.reason in {
        "NOT_AWAITING_APPROVAL",
        "STALE_APPROVAL_FACTS_CHANGED",
    }
    settled = real_get_run(record.run_id)
    assert settled is not None
    assert settled.state == RunState.SUCCEEDED  # NOT expired
    assert settled.receipt is not None and settled.receipt.status == "succeeded"
    assert device.execute_calls == 1
    assert repo.count_receipts(record.run_id) == 1  # accounted exactly once
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 15


def test_stale_facts_reevaluation_cannot_overwrite_an_executed_run(
    repo: SqliteRepository, food_event: EventIn, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The A03 re-evaluation must lose to the approval that already executed.

    Same stale-reader race as above, but the rival wins while this caller is
    re-reading the facts: the re-evaluation used to write its verdict with a plain
    ``save_run``, turning a SUCCEEDED run into BLOCKED and clearing its window.
    """

    device = CountingDevice()
    workflow = Workflow(repo, device, proposer=ProgrammableProposer())
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    approval = ApprovalIn(
        decision="approve",
        proposal_version=record.proposal_version,
        action_digest=record.action_digest or "",
    )

    real_get_run = repo.get_run
    fired: list[bool] = []

    def racy_get_run(run_id):  # type: ignore[no-untyped-def]
        fresh = real_get_run(run_id)
        if fresh is not None and fresh.state == RunState.AWAITING_APPROVAL and not fired:
            fired.append(True)
            winner = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)
            assert winner.state == RunState.SUCCEEDED
            # Quota is now spent, so the stale caller's re-evaluation says BLOCKED.
            repo.update_facts(DEMO_OWNER_ID, daily_dispensed_grams=30)
        return fresh

    monkeypatch.setattr(repo, "get_run", racy_get_run)

    with pytest.raises(ApprovalRejected) as excinfo:
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)

    assert fired == [True]
    assert excinfo.value.reason == "STALE_APPROVAL_FACTS_CHANGED"
    settled = real_get_run(record.run_id)
    assert settled is not None
    assert settled.state == RunState.SUCCEEDED  # NOT blocked, NOT expired
    assert settled.receipt is not None and settled.receipt.status == "succeeded"
    assert settled.policy_reason != MISSING_FACTS
    assert device.execute_calls == 1
    assert repo.count_receipts(record.run_id) == 1
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 30  # untouched


def test_redelivery_never_spends_another_model_call(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    proposer = ProgrammableProposer()
    workflow = Workflow(repo, DeviceSimulator(), proposer=proposer)

    first = workflow.handle_event(DEMO_OWNER_ID, food_event)
    second = workflow.handle_event(DEMO_OWNER_ID, food_event)

    assert first.run_id == second.run_id
    assert proposer.calls == 1
    assert repo.count_runs(DEMO_OWNER_ID) == 1


def test_background_intake_returns_queued_and_inline_returns_the_verdict(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    proposer = ProgrammableProposer()

    background = Workflow(repo, DeviceSimulator(), proposer=proposer)
    queued = background.enqueue_event(DEMO_OWNER_ID, food_event)
    assert queued.state == RunState.QUEUED
    assert proposer.calls == 0

    analyzed = background.handle_event(DEMO_OWNER_ID, food_event)
    assert analyzed.state == RunState.AWAITING_APPROVAL
    assert proposer.calls == 1


@pytest.mark.parametrize("mode", ["inline", "background"])
def test_worker_mode_defaults_and_env_alias(mode: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAWTWIN_WORKER_MODE", mode)
    monkeypatch.setenv("PAWTWIN_MODEL_BACKEND", "inline")

    assert Settings(_env_file=None).worker_mode == mode


# --- the inline backend must not hide an unknown fact (A09) -------------------


@pytest.mark.parametrize("cleared", ["daily_dispensed_grams", "last_fed_minutes_ago"])
def test_inline_backend_reports_an_unknown_fact_as_needs_info(
    workflow: Workflow,
    repo: SqliteRepository,
    food_event: EventIn,
    cleared: str,
) -> None:
    """``evaluate_policy`` always allows the ``observe`` fallback, so NEEDS_INFO
    can only come from ``missing_fields``: without it the verdict would read
    "awaiting approval" right next to a fact the UI shows as unknown.
    """

    repo.update_facts(DEMO_OWNER_ID, **{cleared: None})

    record = workflow.handle_event(DEMO_OWNER_ID, food_event)

    assert record.state == RunState.NEEDS_INFO
    assert record.policy_reason == "MISSING_FACTS"
    assert record.proposal is not None
    assert record.proposal.action == Action(kind="observe", grams=0)
    assert record.proposal.missing_fields == [cleared]
    assert "None" not in record.proposal.explanation


# --- real concurrency (gate G5 / Day-2 nit#6 closure) -------------------------


def test_worker_analyzes_two_owners_in_parallel_up_to_the_global_ceiling(
    repo: SqliteRepository,
) -> None:
    """Day-3 ruling 7: the pool really overlaps analyses, and the site-wide ceiling
    (two) is a LIVE constraint. This is the production trigger path the Day-2
    sequential drain never exercised (nit#6): a third owner waits for a free slot.
    """

    slow = ProgrammableProposer(delay=0.3)
    workflow = Workflow(repo, DeviceSimulator(), proposer=slow)
    worker = AnalysisWorker(
        repo,
        workflow,
        _settings(max_concurrent_global=2, max_concurrent_per_session=1, lease_renew_seconds=1),
        poll_interval=0.05,
    )
    ids = [
        repo.create_or_get_run(owner, _food_event()).run_id
        for owner in ("owner-a", "owner-b", "owner-c")
    ]

    def all_settled() -> bool:
        for run_id in ids:
            rec = repo.get_run(run_id)
            if rec is None or rec.state in CLAIMABLE_STATES:
                return False
        return True

    worker.start()
    try:
        _wait_for(lambda: worker.peak_concurrency >= 2, timeout=5.0)
        _wait_for(all_settled, timeout=15.0)
    finally:
        worker.stop()

    assert worker.peak_concurrency == 2  # never exceeded the global ceiling
    assert slow.calls == 3  # the third ran once a slot freed


def test_worker_serializes_one_owner_at_the_per_session_ceiling(
    repo: SqliteRepository,
) -> None:
    """per-session ceiling = 1: one owner's two queued runs never overlap even
    though the site-wide ceiling is two. This is the real production path for the
    single-demo-owner household, and the second run is left QUEUED (not dropped).
    """

    slow = ProgrammableProposer(delay=0.2)
    workflow = Workflow(repo, DeviceSimulator(), proposer=slow)
    worker = AnalysisWorker(
        repo,
        workflow,
        _settings(max_concurrent_global=2, max_concurrent_per_session=1, lease_renew_seconds=1),
        poll_interval=0.05,
    )
    for _ in range(2):
        repo.create_or_get_run("owner-a", _food_event())

    worker.start()
    try:
        _wait_for(lambda: worker.processed >= 2, timeout=10.0)
    finally:
        worker.stop()

    assert worker.peak_concurrency == 1
    assert slow.calls == 2
