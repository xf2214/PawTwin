"""Care chat snapshots distinguish system fallbacks from identical owner titles."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.family_assistant import FamilyAssistant, GroundedAnswer
from pawtwin.main import create_app
from pawtwin.pet_context import snapshot

OWNER_TITLE = "人工照护（历史名称未记录）"


@pytest.fixture
def care_client(tmp_path):
    app = create_app(
        Settings(
            _env_file=None, worker_mode="inline", database_path=str(tmp_path / "care-reply.db")
        )
    )
    with TestClient(app) as client:
        login = client.post("/api/login", json={"passphrase": "local-demo-passphrase"})
        assert login.status_code == 200
        client.headers["x-csrf-token"] = login.json()["csrf_token"]
        assert client.get("/api/family/me").status_code == 200
        yield app, client


def task(client):
    result = client.post(
        "/api/home/pets/mochi/tasks",
        json={
            "kind": "water",
            "title": OWNER_TITLE,
            "due_at": (datetime.now(UTC) - timedelta(minutes=2)).isoformat(),
        },
    )
    assert result.status_code == 200, result.text
    return result.json()["tasks"][-1]


def complete(client, record):
    response = client.post(
        f"/api/home/tasks/{record['id']}/action",
        json={
            "event_id": str(uuid4()),
            "version": record["version"],
            "action": "complete",
        },
    )
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("entry", ["app", "alexa_simulator"])
def test_pending_care_reply_preserves_owner_title_snapshot(care_client, entry):
    _, client = care_client
    record = task(client)
    reply = client.post(
        "/api/family/pets/mochi/chat",
        json={
            "text": "今天有哪些待办",
            "entry": entry,
        },
    )
    assert reply.status_code == 200
    summary = reply.json().get("care_summary")
    assert summary == {
        "kind": "pending",
        "pet_name": "Mochi",
        "total_count": 1,
        "records": [
            {
                "id": record["id"],
                "title": OWNER_TITLE,
                "title_is_fallback": False,
                "completed_at": None,
            }
        ],
    }
    complete(client, record)
    assert summary["records"][0]["title"] == OWNER_TITLE


@pytest.mark.parametrize("entry", ["app", "alexa_simulator"])
@pytest.mark.parametrize("missing_history", [False, True])
def test_completed_reply_carries_actual_title_provenance(care_client, entry, missing_history):
    app, client = care_client
    record = task(client)
    complete(client, record)
    if missing_history:
        app.state.family_store.mutate("demo-owner", lambda home: home["tasks"].clear())
    reply = client.post(
        "/api/family/pets/mochi/chat",
        json={
            "text": "最近完成了什么",
            "entry": entry,
        },
    )
    assert reply.status_code == 200
    summary = reply.json().get("care_summary")
    assert summary and summary["kind"] == "completed"
    assert summary["pet_name"] == "Mochi" and summary["total_count"] == 1
    assert summary["records"][0]["title"] == OWNER_TITLE
    assert summary["records"][0]["title_is_fallback"] is missing_history
    assert summary["records"][0]["completed_at"]
    assert summary["records"][0]["id"] in reply.json()["source_record_ids"]


@pytest.mark.parametrize("missing_history", [False, True])
def test_read_only_care_reply_has_scoped_title_provenance(care_client, missing_history):
    app, client = care_client
    record = task(client)
    complete(client, record)
    if missing_history:
        app.state.family_store.mutate("demo-owner", lambda home: home["tasks"].clear())
    grant = client.post("/api/family/pets/mochi/care-access", json={"expires_in_hours": 1})
    assert grant.status_code == 200
    visitor = TestClient(app)
    response = visitor.post(
        "/api/care-access/chat",
        json={"text": "做过哪些照护"},
        headers={"Authorization": f"Bearer {grant.json()['token']}"},
    )
    assert response.status_code == 200
    summary = response.json().get("care_summary")
    assert summary and summary["pet_name"] is None and summary["kind"] == "completed"
    assert summary["records"][0]["title"] == OWNER_TITLE
    assert summary["records"][0]["title_is_fallback"] is missing_history
    assert set(summary["records"][0]) == {"id", "title", "title_is_fallback", "completed_at"}
    assert response.json()["action_executed"] is False


def test_model_answer_does_not_reuse_unrelated_local_care_summary(care_client):
    app, client = care_client
    task(client)
    ctx = snapshot(
        app.state.family_store.read("demo-owner"),
        "mochi",
        app.state.family_store.household("demo-owner"),
    )
    gateway = SimpleNamespace(
        invoke=lambda **_: (
            GroundedAnswer(answer="A general note from the model.", source_record_ids=[]),
            {},
        )
    )
    assistant = FamilyAssistant(SimpleNamespace(family_model_backend="bedrock"), gateway)
    reply = assistant.respond(ctx, "Hello", "app", [], SimpleNamespace())
    assert reply["answer_origin"] == "model"
    assert "care_summary" in reply and reply["care_summary"] is None
