"""Memory updates reject corrupting null text while retaining PATCH semantics."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app


@pytest.fixture
def family():
    app = create_app(
        Settings(
            _env_file=None,
            mode="local",
            database_path=":memory:",
            worker_mode="inline",
            family_model_backend="local_rules",
        )
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        account = client.post(
            "/api/family/register",
            json={
                "username": "memory-validation",
                "password": "test-password-123",
                "display_name": "Memory owner",
            },
        )
        assert account.status_code == 200, account.text
        client.headers["x-csrf-token"] = account.json()["csrf_token"]
        household = client.post("/api/family/households", json={"name": "Memory household"})
        assert household.status_code == 200, household.text
        yield app.state.family_store, client, household.json()["household_id"]


def test_null_memory_text_is_rejected_without_corrupting_stored_records_or_readers(family):
    repo, client, hid = family
    path = "/api/family/pets/mochi/memories"
    created = client.post(
        path, json={"text": "Likes feathers", "topic": "play", "status": "confirmed"}
    )
    assert created.status_code == 200, created.text
    record = created.json()

    response = client.patch(
        f"{path}/{record['id']}", json={"version": 1, "status": "confirmed", "text": None}
    )

    assert response.status_code == 422, response.text
    assert repo.read(hid)["memories"][0] == record
    listed = client.get(path)
    assert listed.status_code == 200, listed.text
    assert listed.json()["memories"][0]["text"] == "Likes feathers"
    assert listed.json()["memories"][0]["version"] == 1
    context = client.get("/api/family/pets/mochi/context")
    assert context.status_code == 200, context.text
    assert context.json()["layers"]["memory"][0]["text"] == "Likes feathers"
    chat = client.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert chat.status_code == 200, chat.text
    assert record["id"] in chat.json()["source_record_ids"]
    assert "Likes feathers" in chat.json()["answer"]
    summary = client.get("/api/family/pets/mochi/visit-summary")
    assert summary.status_code == 200, summary.text
    assert summary.json()["preferences"][0]["text"] == "Likes feathers"


def test_memory_update_can_omit_text_and_explicitly_clear_expiry(family):
    repo, client, hid = family
    path = "/api/family/pets/mochi/memories"
    expiry = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    created = client.post(
        path,
        json={"text": "Likes feathers", "topic": "play", "valid_until": expiry},
    )
    assert created.status_code == 200, created.text
    record = created.json()

    confirmed = client.patch(
        f"{path}/{record['id']}", json={"version": 1, "status": "confirmed"}
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["text"] == "Likes feathers"
    assert confirmed.json()["version"] == 2
    assert datetime.fromisoformat(confirmed.json()["valid_until"]) == datetime.fromisoformat(expiry)

    cleared = client.patch(
        f"{path}/{record['id']}",
        json={"version": 2, "status": "confirmed", "valid_until": None},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["text"] == "Likes feathers"
    assert cleared.json()["version"] == 3
    assert cleared.json()["valid_until"] is None
    assert repo.read(hid)["memories"][0]["valid_until"] is None
