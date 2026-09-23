from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pawtwin.models import Action, EventIn, Proposal, Receipt, RunState, make_command_id
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository


def test_event_redelivery_does_not_create_second_run(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    first = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    second = repo.create_or_get_run(DEMO_OWNER_ID, food_event)

    assert first.run_id == second.run_id
    assert repo.count_runs(DEMO_OWNER_ID) == 1


def test_distinct_events_create_independent_runs(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    other = EventIn(event_id=uuid4(), kind="attention_request", room="living_room")

    first = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    second = repo.create_or_get_run(DEMO_OWNER_ID, other)

    assert first.run_id != second.run_id
    assert repo.count_runs(DEMO_OWNER_ID) == 2


def test_new_run_starts_queued_and_persists_transitions(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    assert record.state == RunState.QUEUED

    record.state = RunState.AWAITING_APPROVAL
    record.proposal = Proposal(
        action=Action(kind="dispense_food", grams=15),
        explanation="Deterministic local proposal.",
        evidence_ids=["pet_facts"],
    )
    record.proposal_version = 1
    record.action_digest = "a" * 64
    record.expires_at = datetime.now(UTC) + timedelta(minutes=10)
    repo.save_run(record)

    reloaded = repo.get_run(record.run_id)
    assert reloaded is not None
    assert reloaded.state == RunState.AWAITING_APPROVAL
    assert reloaded.proposal is not None
    assert reloaded.proposal.action.grams == 15
    assert reloaded.proposal_version == 1
    assert reloaded.action_digest == "a" * 64
    assert reloaded.expires_at is not None


def test_record_receipt_once_is_idempotent_and_accounts_once(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    command_id = make_command_id(record.run_id, 1)
    receipt = Receipt(command_id=command_id, status="succeeded")
    before = repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams

    first = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=receipt, dispense_grams=15
    )
    second = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=receipt, dispense_grams=15
    )

    assert first is True
    assert second is False
    assert repo.count_receipts(record.run_id) == 1
    facts = repo.get_facts(DEMO_OWNER_ID)
    assert facts.daily_dispensed_grams == (before or 0) + 15
    assert facts.last_fed_minutes_ago == 0


def test_failed_receipt_is_recorded_without_accounting(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    record = repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    command_id = make_command_id(record.run_id, 1)
    before = repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams

    recorded = repo.record_receipt_once(
        command_id=command_id,
        run_id=record.run_id,
        receipt=Receipt(command_id=command_id, status="failed"),
        dispense_grams=15,
    )

    assert recorded is True
    assert repo.count_receipts(record.run_id) == 1
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == before


def test_update_facts_bumps_version(repo: SqliteRepository) -> None:
    version_before = repo.get_facts(DEMO_OWNER_ID).facts_version

    updated = repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=20)

    assert updated.last_fed_minutes_ago == 20
    assert updated.facts_version == version_before + 1
