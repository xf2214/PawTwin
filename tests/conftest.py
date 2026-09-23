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
    for name in (
        "PAWTWIN_MODE",
        "BEDROCK_MODEL_ID",
        "AWS_REGION",
        "DYNAMODB_TABLE_NAME",
        "AGENTCORE_MEMORY_ID",
        "PAWTWIN_FRONTEND_DIST",
        "PAWTWIN_DB_PATH",
        "PAWTWIN_DEMO_PASSPHRASE",
    ):
        monkeypatch.delenv(name, raising=False)
    yield


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
def workflow(repo: SqliteRepository, device: DeviceSimulator) -> Workflow:
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
    app = create_app(Settings())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(client: TestClient):
    """Return a callable that logs in and yields the CSRF token.

    The passphrase is read from Settings so no secret is hardcoded in tests.
    """

    def _login(passphrase: str | None = None) -> str:
        password = passphrase if passphrase is not None else Settings().demo_passphrase
        response = client.post("/api/login", json={"passphrase": password})
        assert response.status_code == 200, response.text
        return response.json()["csrf_token"]

    return _login
