from datetime import UTC, datetime, timedelta

from pawtwin.models import EventIn, Receipt, RunState, make_command_id
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository


def test_valid_lease_blocks_a_second_worker(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    future = datetime.now(UTC) + timedelta(seconds=60)

    assert repo.claim_run(record.run_id, "worker-1", future) is True
    # A live lease cannot be stolen by another worker.
    assert repo.claim_run(record.run_id, "worker-2", future) is False


def test_expired_lease_can_be_reclaimed(repo: SqliteRepository, food_event: EventIn) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    past = datetime.now(UTC) - timedelta(seconds=1)
    future = datetime.now(UTC) + timedelta(seconds=60)

    # Simulate a worker that died holding a lease that has since expired.
    assert repo.claim_run(record.run_id, "dead-worker", past) is True
    assert repo.claim_run(record.run_id, "worker-2", future) is True


def test_terminal_run_is_never_reclaimed(repo: SqliteRepository, food_event: EventIn) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    record.state = RunState.SUCCEEDED
    repo.save_run(record)
    future = datetime.now(UTC) + timedelta(seconds=60)

    assert repo.claim_run(record.run_id, "worker-1", future) is False


def test_unknown_receipt_never_double_accounts(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    command_id = make_command_id(record.run_id, 1)
    unknown = Receipt(command_id=command_id, status="unknown")
    before = repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams

    first = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=unknown, dispense_grams=15
    )
    # A late/duplicate receipt for the same command id must not re-dispense.
    second = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=unknown, dispense_grams=15
    )

    assert first is True
    assert second is False
    assert repo.count_receipts(record.run_id) == 1
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == before
