from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.main import create_app
from pawtwin.models import EventIn
from pawtwin.repo_sqlite import SqliteRepository
from pawtwin.workflow import Workflow


@pytest.fixture(autouse=True)
def clear_pawtwin_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Every settings alias must be listed: a value left in a developer shell would
    # otherwise leak into tests and make failures unreproducible.
    for name in (
        "PAWTWIN_MODE",
        "BEDROCK_MODEL_ID",
        "AWS_REGION",
        "DYNAMODB_TABLE_NAME",
        "AGENTCORE_MEMORY_ID",
        "PAWTWIN_FRONTEND_DIST",
        "PAWTWIN_DB_PATH",
        "PAWTWIN_DEMO_PASSPHRASE",
        "PAWTWIN_MODEL_BACKEND",
        "PAWTWIN_MEMORY_BACKEND",
        "PAWTWIN_WORKER_MODE",
        "PAWTWIN_ANALYSIS_TIMEOUT_SECONDS",
        "PAWTWIN_MAX_MODEL_CALLS",
        "PAWTWIN_MAX_OUTPUT_TOKENS",
        "PAWTWIN_LEASE_SECONDS",
        "PAWTWIN_LEASE_RENEW_SECONDS",
        "PAWTWIN_MAX_ATTEMPTS",
        "PAWTWIN_MAX_CONCURRENT_PER_SESSION",
        "PAWTWIN_MAX_CONCURRENT_GLOBAL",
        "PAWTWIN_TRUST_PROXY_HEADERS",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


def _local_settings(**overrides: object) -> Settings:
    """Settings that ignore any ``.env`` file and stay on the inline worker.

    ``_env_file=None`` matters: the autouse fixture can only clear process
    environment variables, not a ``.env`` on disk.
    """

    values: dict[str, object] = {"worker_mode": "inline", **overrides}
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture
def repo() -> Iterator[SqliteRepository]:
    repository = SqliteRepository(":memory:")
    try:
        yield repository
    finally:
        repository.close()


@pytest.fixture
def device() -> DeviceSimulator:
    return DeviceSimulator()


@pytest.fixture
def memory_service():
    """The honest LOCAL memory backend: saves raw feedback, retrieves nothing.

    It never reports ``available`` and ``search`` returns an empty list, so a test
    built on it can never mistake a stand-in for a real AgentCore retrieval.
    """

    from pawtwin.memory import LocalFakeMemory

    return LocalFakeMemory()


@pytest.fixture
def file_repo(tmp_path):
    """A FILE-backed repository so durability/restart can actually be exercised.

    ``:memory:`` dies with the process, so any restart or cross-connection claim
    needs a real file. Two instances on one path model two processes/replicas.
    """

    repository = SqliteRepository(str(tmp_path / "pawtwin.db"))
    try:
        yield repository
    finally:
        repository.close()


@pytest.fixture
def workflow(repo: SqliteRepository, device: DeviceSimulator) -> Workflow:
    # No proposer injected: the workflow falls back to InlineProposer, so the
    # approval/decline suite keeps the Day-1 guarantee that it does not depend on
    # the AI layer or any stand-in.
    return Workflow(repo, device)


@pytest.fixture
def food_event() -> EventIn:
    return EventIn(
        event_id=uuid4(),
        kind="food_request",
        room="kitchen",
        note="Mochi is waiting near the bowl.",
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(_local_settings())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def background_client() -> Iterator[TestClient]:
    """The shipped asynchronous path: intake returns QUEUED, a worker analyzes it."""

    app = create_app(_local_settings(worker_mode="background"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(client: TestClient):
    """Return a callable that logs in and yields the CSRF token.

    The passphrase is read from Settings so no secret is hardcoded in tests.
    """

    def _login(passphrase: str | None = None) -> str:
        password = passphrase if passphrase is not None else _local_settings().demo_passphrase
        response = client.post("/api/login", json={"passphrase": password})
        assert response.status_code == 200, response.text
        return response.json()["csrf_token"]

    return _login


@pytest.fixture
def background_login(background_client: TestClient):
    def _login() -> str:
        password = _local_settings().demo_passphrase
        response = background_client.post("/api/login", json={"passphrase": password})
        assert response.status_code == 200, response.text
        return response.json()["csrf_token"]

    return _login
