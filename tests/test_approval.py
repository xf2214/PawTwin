from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import ApprovalIn, EventIn, RunState, compute_action_digest
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.repository import RunRecord
from pawtwin.workflow import ApprovalRejected, Workflow


def _approval(record: RunRecord, decision: str) -> ApprovalIn:
    return ApprovalIn(
        decision=decision,  # type: ignore[arg-type]
        proposal_version=record.proposal_version,
        action_digest=record.action_digest or "",
    )


def test_new_food_event_awaits_approval_with_bound_digest(
    workflow: Workflow, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)

    assert record.state == RunState.AWAITING_APPROVAL
    assert record.proposal is not None
    assert record.proposal.action.kind == "dispense_food"
    assert record.proposal_version == 1
    assert record.action_digest == compute_action_digest(record.proposal.action)
    assert record.expires_at is not None


def test_event_redelivery_returns_same_run_without_reanalysis(
    workflow: Workflow, food_event: EventIn
) -> None:
    first = workflow.handle_event(DEMO_OWNER_ID, food_event)
    second = workflow.handle_event(DEMO_OWNER_ID, food_event)

    assert first.run_id == second.run_id
    assert second.proposal_version == 1


def test_decline_is_durable_and_executes_nothing(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    grams_before = repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams

    declined = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, _approval(record, "decline"))

    assert declined.state == RunState.DECLINED
    assert declined.receipt is None
    assert repo.count_receipts(record.run_id) == 0
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == grams_before
    # A reload of the run keeps the terminal decision.
    reloaded = repo.get_run(record.run_id)
    assert reloaded is not None
    assert reloaded.state == RunState.DECLINED


def test_approve_executes_once_and_accounts(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    assert record.proposal is not None
    grams = record.proposal.action.grams

    approved = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, _approval(record, "approve"))

    assert approved.state == RunState.SUCCEEDED
    assert approved.receipt is not None
    assert approved.receipt.status == "succeeded"
    assert approved.receipt.simulated is True
    assert repo.count_receipts(record.run_id) == 1
    facts = repo.get_facts(DEMO_OWNER_ID)
    assert facts.daily_dispensed_grams == grams
    assert facts.last_fed_minutes_ago == 0


def test_approval_rejects_tampered_digest(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    tampered = ApprovalIn(
        decision="approve", proposal_version=record.proposal_version, action_digest="b" * 64
    )

    with pytest.raises(ApprovalRejected) as exc:
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, tampered)

    assert exc.value.reason == "APPROVAL_MISMATCH"
    still = repo.get_run(record.run_id)
    assert still is not None
    assert still.state == RunState.AWAITING_APPROVAL
    assert repo.count_receipts(record.run_id) == 0


def test_expired_approval_marks_run_expired(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    repo.save_run(record)

    with pytest.raises(ApprovalRejected):
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, _approval(record, "approve"))

    expired = repo.get_run(record.run_id)
    assert expired is not None
    assert expired.state == RunState.EXPIRED
    assert repo.count_receipts(record.run_id) == 0


def test_facts_change_invalidates_old_approval_and_reanalyzes(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    stale = _approval(record, "approve")

    # Owner injects a recent feed: facts_version bumps and feeding is now blocked.
    repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=10)

    with pytest.raises(ApprovalRejected) as exc:
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, stale)

    assert exc.value.reason == "STALE_APPROVAL_FACTS_CHANGED"
    refreshed = repo.get_run(record.run_id)
    assert refreshed is not None
    assert refreshed.proposal_version == record.proposal_version + 1
    assert refreshed.state == RunState.BLOCKED
    assert repo.count_receipts(record.run_id) == 0


def test_double_approval_executes_once(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)
    assert record.proposal is not None
    approval = _approval(record, "approve")

    first = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)
    assert first.state == RunState.SUCCEEDED

    with pytest.raises(ApprovalRejected) as exc:
        workflow.handle_approval(DEMO_OWNER_ID, record.run_id, approval)

    assert exc.value.reason == "NOT_AWAITING_APPROVAL"
    assert repo.count_receipts(record.run_id) == 1
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == record.proposal.action.grams


def test_device_failure_marks_failed_without_accounting(
    workflow: Workflow, repo: SqliteRepository, device: DeviceSimulator, food_event: EventIn
) -> None:
    device.set_mode("failed")
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)

    result = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, _approval(record, "approve"))

    assert result.state == RunState.FAILED
    assert result.receipt is not None
    assert result.receipt.status == "failed"
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 0


def test_device_unknown_marks_unknown_without_accounting(
    workflow: Workflow, repo: SqliteRepository, device: DeviceSimulator, food_event: EventIn
) -> None:
    device.set_mode("unknown")
    record = workflow.handle_event(DEMO_OWNER_ID, food_event)

    result = workflow.handle_approval(DEMO_OWNER_ID, record.run_id, _approval(record, "approve"))

    assert result.state == RunState.UNKNOWN
    assert result.receipt is not None
    assert result.receipt.status == "unknown"
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 0


def test_recent_feed_event_is_blocked_at_intake(
    workflow: Workflow, repo: SqliteRepository, food_event: EventIn
) -> None:
    repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=15)

    record = workflow.handle_event(DEMO_OWNER_ID, food_event)

    assert record.state == RunState.BLOCKED
    assert record.policy_reason == "RECENT_FEED"


def test_attention_event_proposes_non_feeding_and_awaits_approval(workflow: Workflow) -> None:
    event = EventIn(event_id=uuid4(), kind="attention_request", room="living_room")

    record = workflow.handle_event(DEMO_OWNER_ID, event)

    assert record.state == RunState.AWAITING_APPROVAL
    assert record.proposal is not None
    assert record.proposal.action.kind == "create_play_task"
    assert record.proposal.action.grams == 0
