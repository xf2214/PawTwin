"""Different runs must share a durable feeding gate before actuator side effects."""

import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pawtwin.auth import LoginRateLimiter
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.main import create_app
from pawtwin.models import ApprovalIn, EventIn, RunState
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.workflow import ApprovalRejected, Workflow


def pending(workflow):
    record = workflow.handle_event(
        DEMO_OWNER_ID, EventIn(event_id=uuid4(), kind="food_request", room="kitchen")
    )
    assert record.state == RunState.AWAITING_APPROVAL
    return record


def approve(workflow, record):
    return workflow.handle_approval(
        DEMO_OWNER_ID,
        record.run_id,
        ApprovalIn(
            decision="approve",
            proposal_version=record.proposal_version,
            action_digest=record.action_digest,
        ),
    )


def test_two_different_runs_cannot_dispense_concurrently_across_connections(tmp_path):
    path = str(tmp_path / "feeding.db")
    first, second = SqliteRepository(path), SqliteRepository(path)
    entered, release = threading.Event(), threading.Event()
    device = DeviceSimulator()
    original = device.execute
    calls = []

    def paused_execute(command_id, action):
        calls.append(command_id)
        if len(calls) == 1:
            entered.set()
            assert release.wait(10)
        return original(command_id, action)

    device.execute = paused_execute
    one, two = Workflow(first, device), Workflow(second, device)
    try:
        first.update_facts(DEMO_OWNER_ID, daily_dispensed_grams=15)
        a, b = pending(one), pending(two)
        with ThreadPoolExecutor(max_workers=2) as pool:
            execution = pool.submit(approve, one, a)
            assert entered.wait(5)
            try:
                with pytest.raises(ApprovalRejected):
                    approve(two, b)
            finally:
                release.set()
            assert execution.result(timeout=10).state == RunState.SUCCEEDED
        assert len(calls) == 1
        assert first.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 30
    finally:
        release.set()
        first.close()
        second.close()


def test_unknown_receipt_keeps_the_feeding_gate_after_restart_and_fact_reset(tmp_path):
    path = str(tmp_path / "unknown.db")
    repo = SqliteRepository(path)
    device = DeviceSimulator()
    device.set_mode("unknown")
    flow = Workflow(repo, device)
    try:
        assert approve(flow, pending(flow)).state == RunState.UNKNOWN
        assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 0
    finally:
        repo.close()
    reopened = SqliteRepository(path)
    try:
        reopened.reset_facts(DEMO_OWNER_ID)
        flow = Workflow(reopened, DeviceSimulator())
        with pytest.raises(ApprovalRejected):
            approve(flow, pending(flow))
        assert reopened.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 0
    finally:
        reopened.close()


def test_known_failed_receipt_releases_the_gate_without_accounting(repo):
    device = DeviceSimulator()
    device.set_mode("failed")
    flow = Workflow(repo, device)
    assert approve(flow, pending(flow)).state == RunState.FAILED
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 0
    device.set_mode("succeeded")
    assert approve(flow, pending(flow)).state == RunState.SUCCEEDED
    assert repo.get_facts(DEMO_OWNER_ID).daily_dispensed_grams == 15


def test_interruption_before_a_receipt_keeps_the_gate_after_restart(tmp_path):
    path = str(tmp_path / "interrupted.db")
    repo = SqliteRepository(path)
    device = DeviceSimulator()

    def interrupted_execute(command, action):
        raise RuntimeError("device outcome unavailable")

    device.execute = interrupted_execute
    try:
        flow = Workflow(repo, device)
        with pytest.raises(RuntimeError, match="outcome unavailable"):
            approve(flow, pending(flow))
    finally:
        repo.close()
    reopened = SqliteRepository(path)
    try:
        reopened.reset_facts(DEMO_OWNER_ID)
        flow = Workflow(reopened, DeviceSimulator())
        with pytest.raises(ApprovalRejected):
            approve(flow, pending(flow))
    finally:
        reopened.close()


def test_legacy_unknown_execution_without_a_reservation_still_blocks(repo):
    flow = Workflow(repo, DeviceSimulator("unknown"))
    assert approve(flow, pending(flow)).state == RunState.UNKNOWN
    with repo._conn:
        repo._conn.execute("DELETE FROM feeding_reservations")
    repo.reset_facts(DEMO_OWNER_ID)
    with pytest.raises(ApprovalRejected):
        approve(Workflow(repo, DeviceSimulator()), pending(flow))


def test_local_server_stack_ignores_raw_forwarded_headers():
    import uvicorn

    settings = Settings(_env_file=None, worker_mode="inline", login_max_failures=1)
    server = uvicorn.Config(create_app(settings), proxy_headers=False, log_config=None)
    server.load()
    with TestClient(server.loaded_app, client=("127.0.0.1", 50000)) as client:
        assert (
            client.post(
                "/api/login",
                json={"passphrase": "wrong"},
                headers={"x-forwarded-for": "198.51.100.10"},
            ).status_code
            == 429
        )
        assert (
            client.post(
                "/api/login",
                json={"passphrase": settings.demo_passphrase},
                headers={"x-forwarded-for": "198.51.100.11"},
            ).status_code
            == 429
        )


def test_late_allowed_reevaluation_cannot_overwrite_a_completed_run(repo, monkeypatch):
    flow = Workflow(repo, DeviceSimulator())
    record = pending(flow)
    original = repo.save_run
    entered, release = threading.Event(), threading.Event()
    first_thread = []

    def delayed_save(value, **kwargs):
        if value.proposal_version == record.proposal_version + 1 and not first_thread:
            first_thread.append(threading.get_ident())
            entered.set()
            assert release.wait(10)
        return original(value, **kwargs)

    monkeypatch.setattr(repo, "save_run", delayed_save)
    repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=200)
    with ThreadPoolExecutor(max_workers=1) as pool:
        stale = pool.submit(approve, flow, record)
        assert entered.wait(5)
        try:
            with pytest.raises(ApprovalRejected):
                approve(flow, record)
            newer = repo.get_run(record.run_id)
            assert approve(flow, newer).state == RunState.SUCCEEDED
        finally:
            release.set()
        with pytest.raises(ApprovalRejected):
            stale.result(timeout=10)
    final = repo.get_run(record.run_id)
    assert final.state == RunState.SUCCEEDED
    assert final.receipt.status == "succeeded"
    assert repo.count_receipts(record.run_id) == 1


def test_receipt_commits_terminal_run_before_later_save_can_fail(repo, monkeypatch):
    device = DeviceSimulator("failed")
    flow = Workflow(repo, device)
    record = pending(flow)
    original = repo.save_run

    def interrupted_save(value, **kwargs):
        if value.receipt is not None:
            raise RuntimeError("interruption after receipt commit")
        return original(value, **kwargs)

    monkeypatch.setattr(repo, "save_run", interrupted_save)
    with pytest.raises(RuntimeError, match="interruption"):
        approve(flow, record)
    persisted = repo.get_run(record.run_id)
    assert persisted.state == RunState.FAILED
    assert persisted.receipt.status == "failed"
    monkeypatch.setattr(repo, "save_run", original)
    device.set_mode("succeeded")
    assert approve(flow, pending(flow)).state == RunState.SUCCEEDED


@pytest.mark.parametrize("endpoint", ["/api/login", "/api/family/login", "/api/family/register"])
def test_raw_forwarded_header_does_not_change_the_authentication_limit_key(endpoint):
    settings = Settings(
        _env_file=None,
        worker_mode="inline",
        trust_proxy_headers=True,
        login_max_failures=1,
        login_backoff_seconds=60,
    )
    with TestClient(create_app(settings)) as client:
        client.app.state.registration_limiter = LoginRateLimiter(max_failures=1, backoff_seconds=60)
        first = {"x-forwarded-for": "198.51.100.10, 192.0.2.99"}
        second = {"x-forwarded-for": "198.51.100.11, 192.0.2.99"}
        if endpoint == "/api/login":
            bad, following = {"passphrase": "wrong"}, {"passphrase": settings.demo_passphrase}
        elif endpoint == "/api/family/login":
            bad = following = {"username": "nobody", "password": "wrong-password-123"}
        else:
            bad = {
                "username": "first-user",
                "password": "registration-pass-123",
                "display_name": "First",
            }
            following = {
                "username": "second-user",
                "password": "registration-pass-123",
                "display_name": "Second",
            }
        client.post(endpoint, json=bad, headers=first)
        assert client.post(endpoint, json=following, headers=second).status_code == 429
