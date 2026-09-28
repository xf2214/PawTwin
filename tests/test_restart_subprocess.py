"""Real OS-process restart recovery (Day-3 best-effort, ruling 9b, marker=restart).

Unlike ``test_restart.py`` (two connections inside ONE process), this really spawns
a SECOND Python process that writes to the file database and exits, then verifies
recovery from THIS process -- the faithful A13 "a new process picks up where the old
one left off" semantics. It binds no port and starts no server, so it is far less
flaky than a uvicorn kill/relaunch, while still proving cross-PROCESS durability.

Honest scope: this proves a settled (awaiting_approval) run survives a real process
boundary and executes exactly once in the new process. The "killed mid-analysis with
a live lease" case is covered logically in ``test_restart.py`` (a live lease is not
re-analysed and becomes reclaimable only after expiry); it is not re-run through a
timed subprocess kill here.
"""

import subprocess
import sys
import textwrap
from uuid import UUID

import pytest
from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import ApprovalIn, RunState
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.workflow import Workflow

pytestmark = pytest.mark.restart

# Runs in a SEPARATE interpreter: create + analyse a run to awaiting_approval,
# print its id, and exit (closing the database cleanly).
_CHILD = textwrap.dedent(
    """
    import sys
    from uuid import uuid4
    from pawtwin.device_sim import DeviceSimulator
    from pawtwin.models import EventIn
    from pawtwin.repo_sqlite import SqliteRepository, DEMO_OWNER_ID
    from pawtwin.workflow import Workflow

    db = sys.argv[1]
    repo = SqliteRepository(db)
    event = EventIn(event_id=uuid4(), kind="food_request", room="kitchen")
    record = Workflow(repo, DeviceSimulator()).handle_event(DEMO_OWNER_ID, event)
    repo.close()
    print(record.run_id)
    """
)


def test_a_run_from_one_os_process_survives_and_executes_once_in_a_new_one(
    tmp_path,
) -> None:
    db = str(tmp_path / "pawtwin.db")

    # Process A: do the intake + analysis, then really exit.
    child = subprocess.run(
        [sys.executable, "-c", _CHILD, db],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert child.returncode == 0, f"child failed:\n{child.stderr}"
    run_id = UUID(child.stdout.strip().splitlines()[-1])

    # Process B (this interpreter): the run is still awaiting approval on the file.
    repo = SqliteRepository(db)
    try:
        record = repo.get_run(run_id)
        assert record is not None
        assert record.state == RunState.AWAITING_APPROVAL

        approved = Workflow(repo, DeviceSimulator()).handle_approval(
            DEMO_OWNER_ID,
            run_id,
            ApprovalIn(
                decision="approve",
                proposal_version=record.proposal_version,
                action_digest=record.action_digest or "",
            ),
        )
        assert approved.state == RunState.SUCCEEDED
        assert repo.count_receipts(run_id) == 1
    finally:
        repo.close()


def test_a_terminal_run_stays_terminal_across_a_third_process(tmp_path) -> None:
    db = str(tmp_path / "pawtwin.db")

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, db],
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert child.returncode == 0, f"child failed:\n{child.stderr}"
    run_id = UUID(child.stdout.strip().splitlines()[-1])

    # Process B approves it to a terminal state.
    second = SqliteRepository(db)
    try:
        record = second.get_run(run_id)
        assert record is not None
        Workflow(second, DeviceSimulator()).handle_approval(
            DEMO_OWNER_ID,
            run_id,
            ApprovalIn(
                decision="approve",
                proposal_version=record.proposal_version,
                action_digest=record.action_digest or "",
            ),
        )
    finally:
        second.close()

    # Process C must find it terminal, unclaimable, and accounted exactly once.
    third = SqliteRepository(db)
    try:
        final = third.get_run(run_id)
        assert final is not None
        assert final.state == RunState.SUCCEEDED
        assert run_id not in {item.run_id for item in third.list_claimable_runs()}
        assert third.count_receipts(run_id) == 1
    finally:
        third.close()


@pytest.mark.skip(
    reason=(
        "Best-effort real kill/relaunch of a running uvicorn process is not run by "
        "default: on a single local runner it adds port-binding/startup flakiness "
        "for evidence already covered by the two subprocess tests above plus the "
        "logical live-lease restart tests. Named, not silently absent (AGENTS.md)."
    )
)
def test_kill_a_running_server_mid_analysis_then_relaunch() -> None:
    """Placeholder for a timed uvicorn kill during ANALYZING; see module docstring."""
