"""Alexa web simulation uses real scoped local records, never real Alexa or AI."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pawtwin.config import Settings
from pawtwin.main import create_app
from test_family_extension import account, household, join, write


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(_env_file=None, database_path=str(tmp_path / "alexa.db")))


def test_explicit_care_request_returns_draft_without_any_side_effect(app):
    client = account(app, "alexa-owner")
    household(client)
    before = client.get("/api/home/state").json()
    for entry in ("app", "alexa_simulator"):
        reply = write(client, "/api/family/pets/mochi/chat", text="安排陪玩", entry=entry)
        assert reply["care_draft"]["kind"] == "play"
        assert reply["care_draft"]["title"] == "陪 Mochi 玩耍"
        assert reply["action_executed"] is False
        assert reply["request_id"] is None
        assert reply["backend"] == "local_rules"
    after = client.get("/api/home/state").json()
    assert after["tasks"] == before["tasks"]
    assert after["proposals"] == before["proposals"]
    assert after["revision"] == before["revision"]


@pytest.mark.parametrize("text", ["不要安排陪玩", "取消换水提醒", "安排自动喂食", "安排陪玩和换水"])
def test_negation_automation_and_ambiguous_care_never_offer_action(app, text):
    client = account(app, "alexa-safe")
    household(client)
    reply = write(client, "/api/family/pets/mochi/chat", text=text, entry="alexa_simulator")
    assert reply["care_draft"] is None
    assert reply["action_executed"] is False


def test_draft_creation_checks_original_context_atomically(app):
    client = account(app, "alexa-stale")
    household(client)
    reply = write(client, "/api/family/pets/mochi/chat", text="安排换水")
    write(client, "/api/home/pets/mochi/notes", text="刚刚换了水")
    result = client.post(
        "/api/family/pets/mochi/proposals",
        json={
            "kind": "water",
            "title": "换水",
            "due_at": "2026-10-11T09:00:00Z",
            "context_version": reply["context_version"],
        },
    )
    assert result.status_code == 409
    assert client.get("/api/home/state").json()["proposals"] == []


def test_guest_can_read_context_but_cannot_use_chat_or_create_or_confirm_care(app):
    owner, guest = account(app, "alexa-admin"), account(app, "alexa-guest")
    household(owner)
    join(owner, guest, "guest")
    assert guest.get("/api/family/pets/mochi/context").status_code == 200
    assert guest.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"}).status_code == 403
    proposal = write(
        owner,
        "/api/family/pets/mochi/proposals",
        kind="play",
        title="陪玩",
        due_at="2026-10-11T09:00:00Z",
    )
    assert (
        guest.post(
            "/api/family/pets/mochi/proposals",
            json={
                "kind": "play",
                "title": "陪玩",
                "due_at": "2026-10-11T09:00:00Z",
            },
        ).status_code
        == 403
    )
    assert (
        guest.post(
            f"/api/family/pets/mochi/proposals/{proposal['id']}/confirm",
            json={
                "version": proposal["version"],
                "context_version": proposal["context_version"],
            },
        ).status_code
        == 403
    )


def test_observations_and_completion_use_actual_scoped_source_records(app):
    client = account(app, "alexa-outcomes")
    household(client)
    home = write(client, "/api/home/pets/mochi/notes", text="今天换过水", scope="today")
    note = home["notes"][-1]
    reply = write(client, "/api/family/pets/mochi/chat", text="今天有什么观察")
    assert "今天换过水" in reply["answer"]
    assert note["id"] in reply["source_record_ids"]
    home = write(
        client,
        "/api/home/pets/mochi/tasks",
        kind="play",
        title="陪玩已完成",
        due_at="2026-10-11T09:00:00Z",
    )
    task = home["tasks"][-1]
    home = write(
        client,
        f"/api/home/tasks/{task['id']}/action",
        action="complete",
        version=1,
        event_id=str(uuid4()),
    )
    reply = write(client, "/api/family/pets/mochi/chat", text="最近完成了什么")
    assert "人工完成记录" in reply["answer"]
    assert "陪玩已完成" in reply["answer"]
    assert home["occurrences"][-1]["id"] in reply["source_record_ids"]


def test_context_expiry_blocks_pending_confirmation_even_without_revision_change(app, monkeypatch):
    client = account(app, "alexa-expiry")
    household(client)
    path = "/api/family/pets/mochi/proposals"
    proposal = write(client, path, kind="play", title="陪玩", due_at="2026-10-11T09:00:00Z")
    assert proposal["context_valid_until"]

    class FutureDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz or UTC) + timedelta(days=2)

    monkeypatch.setattr("pawtwin.family_api.datetime", FutureDateTime)
    result = client.post(
        f"{path}/{proposal['id']}/confirm",
        json={
            "version": proposal["version"],
            "context_version": proposal["context_version"],
        },
    )
    assert result.status_code == 409
    assert client.get("/api/home/state").json()["tasks"] == []


@pytest.mark.parametrize("text", ["帮我安排 Luna 陪玩", "帮我安排Luna陪玩", "安排Luna换水"])
def test_explicit_other_pet_name_requires_switch_instead_of_wrong_pet_draft(app, text):
    client = account(app, "alexa-names")
    household(client)
    write(client, "/api/home/pets", name="Luna")
    reply = write(client, "/api/family/pets/mochi/chat", text=text)
    assert reply["care_draft"] is None
    assert "切换" in reply["answer"]


def test_completed_recurring_care_keeps_its_original_title_after_rename(app):
    client = account(app, "alexa-history")
    household(client)
    home = write(
        client,
        "/api/home/pets/mochi/tasks",
        kind="play",
        title="原来的陪玩",
        due_at="2026-10-11T09:00:00Z",
        interval_days=1,
    )
    task = home["tasks"][-1]
    path = f"/api/home/tasks/{task['id']}/action"
    write(client, path, action="complete", version=1, event_id=str(uuid4()))
    write(client, path, action="edit", version=2, event_id=str(uuid4()), title="明天的新活动")
    reply = write(client, "/api/family/pets/mochi/chat", text="最近完成了什么")
    assert "原来的陪玩" in reply["answer"]
    assert "明天的新活动" not in reply["answer"]
