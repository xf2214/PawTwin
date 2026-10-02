"""Real AWS DynamoDB table round trip -- Day-5 LIVE item (rule: never moto/mock).

Skipped by default through the ``dynamodb_live`` marker (see ``addopts`` in
pyproject.toml). Run explicitly, and only inside the budget/scope the user
authorised, against a REAL provisioned table:

    uv sync --frozen --extra memory
    $env:AWS_REGION = '<region>'
    $env:PAWTWIN_DYNAMODB_TABLE_NAME = '<real table>'   # created by infra/deploy_plan.json
    uv run --frozen pytest -m dynamodb_live

The skip reason is deliberately explicit: AGENTS.md requires a blocked check to be
NAMED, not silently absent. A SQLite PASS NEVER stands in for these (five-day spec
L106) -- the DynamoDB conditional-write / TransactWriteItems semantics differ from a
held SQLite lock and only a real table can prove the equivalence asserted here.
Nothing in this file is cloud-verified until it really runs against a table.

Each test uses a unique owner id so cases never collide on a shared table, and
resets the facts it touches (ruling 6: "cases self-reset facts").
"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pawtwin.models import Action, EventIn, Proposal, Receipt, RunState
from pawtwin.repository import CLAIMABLE_STATES, TERMINAL_STATES

pytestmark = pytest.mark.dynamodb_live

LIVE_SKIP = (
    "BLOCKED: no AWS credential source or no real DynamoDB table name is configured, "
    "so no live DynamoDB call is made. Set AWS credentials and "
    "PAWTWIN_DYNAMODB_TABLE_NAME (a table created by infra/deploy_plan.json, with the "
    "entity-index GSI) to run this against a REAL table. Nothing here is "
    "cloud-verified; a SQLite PASS never stands in for it. See "
    "docs/evidence/day5-cloud-blocked.md."
)

_CREDENTIAL_ENV_NAMES = ("AWS_ACCESS_KEY_ID", "AWS_PROFILE", "AWS_SESSION_TOKEN")


def _configured() -> bool:
    has_creds = any(os.getenv(name) for name in _CREDENTIAL_ENV_NAMES) or os.path.isfile(
        os.environ.get("AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials"))
    )
    return bool(has_creds and os.getenv("PAWTWIN_DYNAMODB_TABLE_NAME"))


def _unique_owner() -> str:
    return f"live-{uuid4().hex[:12]}"


def _event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="food_request", room="kitchen", note="live probe")


def _proposal(grams: int = 15) -> Proposal:
    return Proposal(
        action=Action(kind="dispense_food", grams=grams),
        explanation="live probe proposal",
    )


@pytest.fixture
def repo():
    if not _configured():
        pytest.skip(LIVE_SKIP)
    from pawtwin.repo_dynamo import DynamoRepository

    repository = DynamoRepository(
        os.environ["PAWTWIN_DYNAMODB_TABLE_NAME"], region=os.getenv("AWS_REGION")
    )
    try:
        yield repository
    finally:
        repository.close()


def test_create_or_get_run_dedups_a_redelivered_event(repo) -> None:
    owner = _unique_owner()
    event = _event()
    first = repo.create_or_get_run(owner, event)
    again = repo.create_or_get_run(owner, event)
    assert again.run_id == first.run_id
    assert repo.count_runs(owner) == 1


def test_only_whitelisted_states_are_claimable_exhaustively(repo) -> None:
    """Every one of the 11 states is forced, then a claim is attempted: it succeeds
    ONLY for QUEUED/ANALYZING. This is the DynamoDB guard against the Day-2 defect
    where 'not terminal' let EXECUTING be re-analyzed and account twice.
    """

    now = datetime.now(UTC)
    for state in RunState:
        owner = _unique_owner()
        record = repo.create_or_get_run(owner, _event())
        record.state = state
        repo.save_run(record)
        claimed = repo.claim_run(record.run_id, "worker-a", now + timedelta(seconds=60))
        assert claimed is (state in CLAIMABLE_STATES), state


def test_concurrent_double_approval_executes_and_accounts_exactly_once(repo) -> None:
    owner = _unique_owner()
    record = repo.create_or_get_run(owner, _event())
    record.state = RunState.AWAITING_APPROVAL
    record.proposal = _proposal(grams=15)
    record.proposal_version = 1
    repo.save_run(record)

    results: list[bool] = []
    barrier = threading.Barrier(2)

    def approve() -> None:
        barrier.wait()
        results.append(
            repo.transition_run(record.run_id, RunState.AWAITING_APPROVAL, RunState.EXECUTING)
        )

    threads = [threading.Thread(target=approve) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # CAS: exactly one approval wins the AWAITING_APPROVAL -> EXECUTING transition.
    assert sorted(results) == [False, True]

    command_id = UUID(int=record.run_id.int)  # deterministic per run for the probe
    receipt = Receipt(command_id=command_id, status="succeeded")
    before = repo.get_facts(owner).daily_dispensed_grams or 0
    first = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=receipt, dispense_grams=15
    )
    second = repo.record_receipt_once(
        command_id=command_id, run_id=record.run_id, receipt=receipt, dispense_grams=15
    )
    # Idempotent accounting: the retry inserts nothing and adds no quota.
    assert first is True
    assert second is False
    assert repo.count_receipts(record.run_id) == 1
    after = repo.get_facts(owner).daily_dispensed_grams
    assert after == before + 15


def test_an_expired_lease_can_be_reclaimed_but_a_live_one_cannot(repo) -> None:
    owner = _unique_owner()
    record = repo.create_or_get_run(owner, _event())
    now = datetime.now(UTC)
    # Worker A takes a lease that is ALREADY expired.
    assert repo.claim_run(record.run_id, "worker-a", now - timedelta(seconds=1)) is True
    # Worker B can reclaim because A's lease is in the past.
    assert repo.claim_run(record.run_id, "worker-b", now + timedelta(seconds=60)) is True
    assert repo.get_run(record.run_id).lease_owner == "worker-b"
    # A third worker cannot steal B's LIVE lease.
    assert repo.claim_run(record.run_id, "worker-c", now + timedelta(seconds=60)) is False


def test_renew_lease_only_succeeds_for_the_current_holder(repo) -> None:
    owner = _unique_owner()
    record = repo.create_or_get_run(owner, _event())
    now = datetime.now(UTC)
    assert repo.claim_run(record.run_id, "worker-a", now + timedelta(seconds=30)) is True
    assert repo.renew_lease(record.run_id, "worker-a", now + timedelta(seconds=90)) is True
    assert repo.renew_lease(record.run_id, "worker-b", now + timedelta(seconds=90)) is False


def test_release_run_is_silent_for_a_non_holder(repo) -> None:
    owner = _unique_owner()
    record = repo.create_or_get_run(owner, _event())
    now = datetime.now(UTC)
    assert repo.claim_run(record.run_id, "worker-a", now + timedelta(seconds=30)) is True
    repo.release_run(record.run_id, "worker-b")  # not the holder: no error, no change
    assert repo.get_run(record.run_id).lease_owner == "worker-a"
    repo.release_run(record.run_id, "worker-a")
    assert repo.get_run(record.run_id).lease_owner is None


def test_unset_leaves_a_column_and_none_writes_null(repo) -> None:
    owner = _unique_owner()
    seeded = repo.get_facts(owner)
    assert seeded.last_fed_minutes_ago == 360
    # None writes a DynamoDB NULL (UNKNOWN, A09); the other column is untouched.
    cleared = repo.update_facts(owner, last_fed_minutes_ago=None)
    assert cleared.last_fed_minutes_ago is None
    assert cleared.daily_dispensed_grams == seeded.daily_dispensed_grams
    # UNSET (the default) leaves last_fed as-is while daily is set.
    bumped = repo.update_facts(owner, daily_dispensed_grams=7)
    assert bumped.last_fed_minutes_ago is None
    assert bumped.daily_dispensed_grams == 7


def test_facts_version_increments_once_per_update(repo) -> None:
    owner = _unique_owner()
    start = repo.get_facts(owner).facts_version
    repo.update_facts(owner, last_fed_minutes_ago=10)
    repo.update_facts(owner, last_fed_minutes_ago=20)
    assert repo.get_facts(owner).facts_version == start + 2


def test_reset_facts_restores_the_documented_defaults(repo) -> None:
    owner = _unique_owner()
    repo.update_facts(owner, last_fed_minutes_ago=None, daily_dispensed_grams=25)
    reset = repo.reset_facts(owner)
    assert reset.last_fed_minutes_ago == 360
    assert reset.daily_dispensed_grams == 0


def test_transition_run_is_a_compare_and_set(repo) -> None:
    owner = _unique_owner()
    record = repo.create_or_get_run(owner, _event())
    assert repo.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is True
    # A stale expectation no longer matches, so the CAS fails.
    assert repo.transition_run(record.run_id, RunState.QUEUED, RunState.ANALYZING) is False
    assert repo.get_run(record.run_id).state is RunState.ANALYZING


def test_terminal_runs_are_never_claimable(repo) -> None:
    owner = _unique_owner()
    for state in TERMINAL_STATES:
        record = repo.create_or_get_run(owner, _event())
        record.state = state
        repo.save_run(record)
        assert record.run_id not in {r.run_id for r in repo.list_claimable_runs(limit=200)}


def test_feedback_roundtrip_persists_session_id_and_record_ids(repo) -> None:
    owner = _unique_owner()
    saved = repo.save_feedback(
        owner_id=owner,
        pet_id="mochi",
        text="Mochi loves the new kibble",
        scope="observation",
        memory_status="saved",
        memory_backend="agentcore",
        conversation_id="conv-1",
        idempotency_key="key-1",
    )
    # Idempotent on (owner, idempotency_key): a retry returns the SAME record.
    retry = repo.save_feedback(
        owner_id=owner,
        pet_id="mochi",
        text="Mochi loves the new kibble",
        scope="observation",
        memory_status="saved",
        memory_backend="agentcore",
        conversation_id="conv-1",
        idempotency_key="key-1",
    )
    assert retry.feedback_id == saved.feedback_id

    processing = repo.set_feedback_status(
        saved.feedback_id,
        memory_status="processing",
        agentcore_event_id="evt-1",
        agentcore_session_id="conv-1",
    )
    assert processing is not None
    assert processing.memory_status == "processing"
    assert processing.agentcore_session_id == "conv-1"

    available = repo.set_feedback_status(
        saved.feedback_id, memory_status="available", memory_record_ids=["rec-1", "rec-2"]
    )
    assert available is not None
    assert available.memory_status == "available"
    assert available.memory_record_ids == ["rec-1", "rec-2"]
    assert len(repo.list_feedback(owner)) == 1
