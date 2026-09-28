"""Cross-connection (== cross-process) concurrency on a shared FILE database.

Day-2 proved double-approval safety with two threads on ONE connection. Day-3
(ruling 8) proves it across TWO separate connections to one file, which is the real
contention surface of two OS processes / two rolling-deploy replicas. The simulated
actuator is a per-process object, so the invariants are asserted on the SHARED
database (one receipt, one SUCCEEDED, quota accounted once), not on a shared counter.

Honest boundary: two SQLite connections are NOT DynamoDB multi-replica conditional
writes; that stays a Day-4/T7 condition item and is never claimed here.
"""

import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import ApprovalIn, EventIn, RunState
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.workflow import Workflow


def _now() -> datetime:
    return datetime.now(UTC)


def _food_event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="food_request", room="kitchen")


def test_two_connections_cannot_both_execute_the_same_approval(tmp_path) -> None:
    db = str(tmp_path / "pawtwin.db")
    event = _food_event()

    # A first process analyses the run to awaiting_approval, then goes away.
    setup = SqliteRepository(db)
    record = Workflow(setup, DeviceSimulator()).handle_event(DEMO_OWNER_ID, event)
    assert record.state == RunState.AWAITING_APPROVAL
    run_id = record.run_id
    grams = record.proposal.action.grams if record.proposal else 0
    approval = ApprovalIn(
        decision="approve",
        proposal_version=record.proposal_version,
        action_digest=record.action_digest or "",
    )
    setup.close()

    # Two SEPARATE connections (== two processes/replicas) approve concurrently.
    repo_1 = SqliteRepository(db)
    repo_2 = SqliteRepository(db)
    workflow_1 = Workflow(repo_1, DeviceSimulator())
    workflow_2 = Workflow(repo_2, DeviceSimulator())
    outcomes: list[object] = []
    lock = threading.Lock()
    barrier = threading.Barrier(2, timeout=10)

    def approve(workflow: Workflow) -> None:
        barrier.wait()
        try:
            result = workflow.handle_approval(DEMO_OWNER_ID, run_id, approval)
            with lock:
                outcomes.append(result.state)
        except Exception as exc:  # noqa: BLE001 - recorded and asserted below
            with lock:
                outcomes.append(exc)

    threads = [
        threading.Thread(target=approve, args=(workflow_1,)),
        threading.Thread(target=approve, args=(workflow_2,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    try:
        # The compare-and-set is a single atomic UPDATE, so exactly one connection
        # reaches EXECUTING and the simulated actuator -- one logical receipt.
        assert repo_1.count_receipts(run_id) == 1
        assert repo_2.count_receipts(run_id) == 1  # same file, same single receipt
        assert outcomes.count(RunState.SUCCEEDED) == 1
        rejections = [item for item in outcomes if isinstance(item, Exception)]
        assert len(rejections) == 1
        assert getattr(rejections[0], "reason", None) in {
            "NOT_AWAITING_APPROVAL",
            "STALE_APPROVAL_FACTS_CHANGED",
        }
        final = repo_1.get_run(run_id)
        assert final is not None
        assert final.state == RunState.SUCCEEDED
        assert final.receipt is not None and final.receipt.status == "succeeded"
        # Quota accounted exactly once, never 2x.
        assert repo_1.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == grams
    finally:
        repo_1.close()
        repo_2.close()


def test_a_live_lease_on_one_connection_blocks_a_second_connection(tmp_path) -> None:
    """The lease is enforced by the database, not by an in-process lock."""

    db = str(tmp_path / "pawtwin.db")
    repo_1 = SqliteRepository(db)
    repo_2 = SqliteRepository(db)
    try:
        record = repo_1.create_or_get_run(DEMO_OWNER_ID, _food_event())
        future = _now() + timedelta(seconds=60)
        assert repo_1.claim_run(record.run_id, "process-1", future) is True
        # A second connection cannot steal a lease that is still live.
        assert repo_2.claim_run(record.run_id, "process-2", future) is False
        # ...but can renew its own only, and the holder still can.
        assert repo_2.renew_lease(record.run_id, "process-2", future) is False
        renewed = repo_1.renew_lease(
            record.run_id, "process-1", _now() + timedelta(seconds=90)
        )
        assert renewed is True
    finally:
        repo_1.close()
        repo_2.close()


def test_an_expired_lease_is_reclaimable_from_a_second_connection(tmp_path) -> None:
    db = str(tmp_path / "pawtwin.db")
    repo_1 = SqliteRepository(db)
    repo_2 = SqliteRepository(db)
    try:
        record = repo_1.create_or_get_run(DEMO_OWNER_ID, _food_event())
        past = _now() - timedelta(seconds=1)
        assert repo_1.claim_run(record.run_id, "crashed-process", past) is True
        # The crashed holder's lease has expired, so a survivor may take over.
        assert repo_2.claim_run(record.run_id, "process-2", _now() + timedelta(seconds=60)) is True
        assert repo_2.get_run(record.run_id).lease_owner == "process-2"
    finally:
        repo_1.close()
        repo_2.close()
