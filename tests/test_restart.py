"""Restart recovery on a FILE database (Day-3 gate G7 / A13, ruling 9a).

``:memory:`` dies with the process, so none of this is observable there. Each test
opens a SECOND ``SqliteRepository`` on the same file after closing the first -- the
logical equivalent of a new OS process. The NEW coverage versus Day-2 is the
"in-progress" (``ANALYZING``) case: a run another worker was mid-analysis on when it
died must NOT be re-analysed while its lease is live (re-analysis would mint a new
command_id and could double-account), and becomes reclaimable only after expiry.

Honest boundary: this is a two-connection logical restart. A real subprocess
kill/relaunch is a best-effort item (marker ``restart``); it is never claimed here
as "real OS process restart verified" unless that test actually ran.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import ApprovalIn, EventIn, RunState
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.repository import CLAIMABLE_STATES
from pawtwin.workflow import Workflow


def _now() -> datetime:
    return datetime.now(UTC)


def _food_event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="food_request", room="kitchen")


def test_an_in_progress_run_with_a_live_lease_is_not_re_analyzed_after_a_restart(
    tmp_path,
) -> None:
    db = str(tmp_path / "pawtwin.db")
    event = _food_event()

    # Process 1 claims the run, moves it to ANALYZING with a LIVE lease, then dies.
    first = SqliteRepository(db)
    record = first.create_or_get_run(DEMO_OWNER_ID, event)
    live = _now() + timedelta(seconds=60)
    assert first.claim_run(record.run_id, "worker-crashed", live) is True
    assert first.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is True
    run_id = record.run_id
    version_before = record.proposal_version
    first.close()

    # Process 2 starts after the crash while the lease is still live.
    second = SqliteRepository(db)
    try:
        # Not offered for claim: the live lease hides it from a new worker.
        assert run_id not in {item.run_id for item in second.list_claimable_runs()}
        assert second.claim_run(run_id, "worker-2", _now() + timedelta(seconds=60)) is False
        # And a full analyse attempt leaves it untouched -- no second proposal.
        result = Workflow(second, DeviceSimulator()).analyze_run(run_id, "worker-2")
        assert result is not None
        after = second.get_run(run_id)
        assert after is not None
        assert after.state == RunState.ANALYZING
        assert after.proposal_version == version_before  # NOT re-analyzed
    finally:
        second.close()


def test_an_in_progress_run_becomes_reclaimable_once_its_lease_expires(tmp_path) -> None:
    db = str(tmp_path / "pawtwin.db")
    event = _food_event()

    first = SqliteRepository(db)
    record = first.create_or_get_run(DEMO_OWNER_ID, event)
    expired = _now() - timedelta(seconds=1)  # the crashed worker's lease lapsed
    assert first.claim_run(record.run_id, "worker-crashed", expired) is True
    assert first.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is True
    run_id = record.run_id
    first.close()

    second = SqliteRepository(db)
    try:
        # Once the lease has expired the survivor may take the run over.
        assert run_id in {item.run_id for item in second.list_claimable_runs()}
        assert second.claim_run(run_id, "worker-2", _now() + timedelta(seconds=60)) is True
        assert second.get_run(run_id).lease_owner == "worker-2"
    finally:
        second.close()


def test_a_queued_run_survives_a_restart_and_is_processed_by_the_new_process(
    tmp_path,
) -> None:
    db = str(tmp_path / "pawtwin.db")
    event = _food_event()

    # Process 1 only persists the intake (background mode) and then dies.
    first = SqliteRepository(db)
    queued = Workflow(first, DeviceSimulator()).enqueue_event(DEMO_OWNER_ID, event)
    assert queued.state == RunState.QUEUED
    run_id = queued.run_id
    first.close()

    # Process 2 picks the still-queued run up and reaches a verdict.
    second = SqliteRepository(db)
    try:
        assert run_id in {item.run_id for item in second.list_claimable_runs()}
        result = Workflow(second, DeviceSimulator()).analyze_run(run_id, "worker-restart")
        assert result is not None
        assert result.state == RunState.AWAITING_APPROVAL
        assert result.state not in CLAIMABLE_STATES
    finally:
        second.close()


def test_a_terminal_run_is_never_re_processed_after_a_restart(tmp_path) -> None:
    db = str(tmp_path / "pawtwin.db")
    event = _food_event()

    first = SqliteRepository(db)
    record = Workflow(first, DeviceSimulator()).handle_event(DEMO_OWNER_ID, event)
    run_id = record.run_id
    first.close()

    second = SqliteRepository(db)
    try:
        # Approve+execute in the new process, then confirm it stays terminal.
        approved = Workflow(second, DeviceSimulator()).handle_approval(
            DEMO_OWNER_ID,
            run_id,
            ApprovalIn(
                decision="approve",
                proposal_version=record.proposal_version,
                action_digest=record.action_digest or "",
            ),
        )
        assert approved.state == RunState.SUCCEEDED
        assert second.count_receipts(run_id) == 1
        # A third "process" must not re-run a settled run.
        third = SqliteRepository(db)
        try:
            assert run_id not in {item.run_id for item in third.list_claimable_runs()}
            assert third.claim_run(run_id, "worker-3", _now() + timedelta(seconds=60)) is False
            assert third.count_receipts(run_id) == 1
        finally:
            third.close()
    finally:
        second.close()
