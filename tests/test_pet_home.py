import base64
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.home_store import HomeStore
from pawtwin.main import create_app

PNG = "data:image/png;base64," + (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aYxkAAAAASUVORK5CYII="
)


@pytest.fixture
def household(tmp_path):
    app = create_app(Settings(_env_file=None, database_path=str(tmp_path / "home.db")))
    with TestClient(app) as client:
        token = client.post("/api/login", json={"passphrase": "local-demo-passphrase"}).json()
        client.headers["X-CSRF-Token"] = token["csrf_token"]
        yield client


def state(client):
    response = client.get("/api/home/state")
    assert response.status_code == 200
    return response.json()


def create_pet(client, name="豆豆"):
    response = client.post("/api/home/pets", json={"name": name, "species": "dog"})
    assert response.status_code == 200
    return response.json()["pets"][-1]["id"]


def create_task(client, pet="mochi", kind="bath", interval=None):
    response = client.post(
        f"/api/home/pets/{pet}/tasks",
        json={
            "title": "洗澡" if kind == "bath" else "剪指甲",
            "kind": kind,
            "due_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "interval_days": interval,
        },
    )
    assert response.status_code == 200
    return response.json()["tasks"][-1]["id"]


def test_profile_and_photo_survive_app_restart(tmp_path):
    settings = Settings(_env_file=None, database_path=str(tmp_path / "persist.db"))
    with TestClient(create_app(settings)) as client:
        login = client.post("/api/login", json={"passphrase": "local-demo-passphrase"}).json()
        client.headers["X-CSRF-Token"] = login["csrf_token"]
        photo = client.post("/api/home/photos", json={"data_url": PNG}).json()["id"]
        result = client.post("/api/home/pets", json={"name": "团团", "photo_id": photo})
        pet = result.json()["pets"][-1]
    with TestClient(create_app(settings)) as client:
        client.post("/api/login", json={"passphrase": "local-demo-passphrase"})
        assert state(client)["pets"][-1] == pet
        image = client.get(f"/api/home/photos/{photo}")
        assert image.status_code == 200
        assert image.content == base64.b64decode(PNG.split(",")[1])


def test_all_home_data_requires_login_and_writes_require_csrf(household):
    household.headers.pop("X-CSRF-Token")
    assert household.post("/api/home/pets", json={"name": "X"}).status_code == 403
    household.cookies.clear()
    assert household.get("/api/home/state").status_code == 401
    assert household.get(f"/api/home/photos/{uuid4()}").status_code == 401
    assert household.post("/api/home/pets", json={"name": "X"}).status_code == 401


def test_profiles_objects_and_notes_are_isolated_by_pet(household):
    pet = create_pet(household)
    member = state(household)["members"][0]["id"]
    household.post(f"/api/home/pets/{pet}/objects", json={"name": "小球", "kind": "toy"})
    household.post(
        f"/api/home/pets/{pet}/notes",
        json={
            "text": "喜欢小球",
            "scope": "preference",
            "activity": "play",
            "actor_id": member,
        },
    )
    own = household.get(f"/api/home/pets/{pet}/insights").json()
    assert "小球" in own["suggestion"]
    assert len(own["evidence"]) == 1
    mochi = household.get("/api/home/pets/mochi/insights").json()
    assert "小球" not in mochi["suggestion"] and not mochi["evidence"]
    assert (
        household.post(
            "/api/home/pets/nonexistent/tasks",
            json={
                "title": "换水",
                "kind": "water",
                "due_at": datetime.now(UTC).isoformat(),
            },
        ).status_code
        == 404
    )


@pytest.mark.parametrize("kind", ["bath", "nails", "brush", "water", "feeding", "walk"])
def test_care_completion_is_recorded_with_actor_and_idempotent(household, kind):
    member = household.post("/api/home/members", json={"name": "姐姐"}).json()["members"][-1]
    task = create_task(household, kind=kind)
    payload = {"event_id": str(uuid4()), "actor_id": member["id"], "action": "complete"}
    first = household.post(f"/api/home/tasks/{task}/action", json=payload)
    assert first.status_code == 200
    assert first.json()["history"][-1]["actor"] == "姐姐"
    replay = household.post(f"/api/home/tasks/{task}/action", json=payload)
    assert replay.json()["history"] == first.json()["history"]
    assert (
        household.post(
            f"/api/home/tasks/{task}/action",
            json={
                **payload,
                "event_id": str(uuid4()),
            },
        ).status_code
        == 409
    )
    assert household.get("/api/home/pets/mochi/insights").json()["weekly"]["completed_count"] == 1


def test_postpone_then_complete_and_recurring_next_occurrence(household):
    task = create_task(household, interval=3)
    actor = state(household)["members"][0]["id"]
    path = f"/api/home/tasks/{task}/action"
    action = {
        "event_id": str(uuid4()),
        "actor_id": actor,
        "action": "postpone",
        "next_due": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    assert household.post(path, json=action).status_code == 200
    bad = {**action, "event_id": str(uuid4()), "next_due": datetime.now(UTC).isoformat()}
    assert household.post(path, json=bad).status_code == 422
    complete = {"event_id": str(uuid4()), "actor_id": actor, "action": "complete"}
    done = household.post(path, json=complete).json()["tasks"][-1]
    assert not done["completed"] and done["last_completed_at"]
    assert datetime.fromisoformat(done["due_at"]) > datetime.now(UTC) + timedelta(days=2)
    assert household.post(path, json={**complete, "event_id": str(uuid4())}).status_code == 409


def test_scope_expiry_and_activity_filter(household):
    actor = state(household)["members"][0]["id"]
    for scope, activity, text in [
        ("today", "play", "今天不玩"),
        ("preference", "play", "喜欢羽毛棒"),
        ("preference", "bath", "怕吹风机"),
    ]:
        household.post(
            "/api/home/pets/mochi/notes",
            json={
                "text": text,
                "scope": scope,
                "activity": activity,
                "actor_id": actor,
            },
        )
    home_store = household.app.state.home_store
    from pawtwin.repo_sqlite import DEMO_OWNER_ID

    home_store.mutate(
        DEMO_OWNER_ID,
        lambda h: h["notes"][0].update(
            {
                "created_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
            }
        ),
    )
    play = household.get("/api/home/pets/mochi/insights?activity=play").json()
    assert [n["text"] for n in play["evidence"]] == ["喜欢羽毛棒"]
    bath = household.get("/api/home/pets/mochi/insights?activity=bath").json()
    assert [n["text"] for n in bath["evidence"]] == ["怕吹风机"]


def test_diary_photo_reference_is_validated_and_weekly_is_grounded(household):
    actor = state(household)["members"][0]["id"]
    body = {
        "title": "第一次剪指甲",
        "text": "主人记录",
        "happened_on": "2026-09-30",
        "actor_id": actor,
        "photo_id": str(uuid4()),
    }
    assert household.post("/api/home/pets/mochi/diary", json=body).status_code == 404
    photo = household.post("/api/home/photos", json={"data_url": PNG}).json()["id"]
    assert (
        household.post("/api/home/pets/mochi/diary", json={**body, "photo_id": photo}).status_code
        == 200
    )
    summary = household.get("/api/home/pets/mochi/insights").json()["weekly"]
    assert summary["completed_count"] == 0
    assert "1 篇" in summary["text"]


@pytest.mark.parametrize(
    "image",
    [
        "data:text/html;base64,PHNjcmlwdD4=",
        "data:image/png;base64,AAAA",
        "data:image/jpeg;base64,!!!",
    ],
)
def test_invalid_photos_are_rejected(household, image):
    assert household.post("/api/home/photos", json={"data_url": image}).status_code == 422


def test_disabled_recognition_never_fakes_a_draft(household):
    photo = household.post("/api/home/photos", json={"data_url": PNG}).json()["id"]
    response = household.post(f"/api/home/photos/{photo}/recognize")
    assert response.status_code == 503 and "draft" not in response.json()


def test_real_adapter_request_shape_and_draft_validation_offline(household, monkeypatch):
    # Injected SDK response proves mapping only, not model accuracy or a live cloud call.
    import sys
    from types import SimpleNamespace

    captured = {}

    def converse(**kwargs):
        captured.update(kwargs)
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "species": "cat",
                                    "coat": "gray",
                                    "pattern": "stripes",
                                    "breed": "",
                                    "uncertainty": "品种不确定",
                                }
                            )
                        }
                    ]
                }
            },
            "ResponseMetadata": {"RequestId": "offline-test-only"},
        }

    monkeypatch.setitem(
        sys.modules,
        "boto3",
        SimpleNamespace(client=lambda *a, **k: SimpleNamespace(converse=converse)),
    )
    monkeypatch.setitem(sys.modules, "botocore.config", SimpleNamespace(Config=lambda **k: k))
    household.app.state.settings.photo_recognition_enabled = True
    household.app.state.settings.bedrock_model_id = "offline-test"
    household.app.state.settings.aws_region = "us-east-1"
    photo = household.post("/api/home/photos", json={"data_url": PNG}).json()["id"]
    result = household.post(f"/api/home/photos/{photo}/recognize")
    assert result.status_code == 200 and not result.json()["confirmed"]
    assert result.json()["draft"]["coat"] == "gray"
    assert captured["messages"][0]["content"][0]["image"]["source"]["bytes"]
    assert "age" not in result.json()["draft"]
    assert state(household)["pets"][0]["coat"] == "gold"


def test_households_cannot_access_each_others_photos_or_profiles(tmp_path):
    repo = HomeStore(str(tmp_path / "owners.db"))
    try:
        photo = repo.save_photo("owner-a", "image/png", b"test")
        assert repo.photo("owner-b", photo) is None
        repo.mutate("owner-a", lambda h: h["pets"].append({"id": "private"}))
        assert len(repo.read("owner-b")["pets"]) == 1
    finally:
        repo.close()


def test_two_connections_do_not_lose_simultaneous_updates(tmp_path):
    path = str(tmp_path / "concurrent.db")
    stores = [HomeStore(path), HomeStore(path)]
    try:

        def write(i):
            stores[i % 2].mutate("owner", lambda h: h["history"].append({"i": i}))

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(write, range(20)))
        assert len(stores[0].read("owner")["history"]) == 20
    finally:
        for repo in stores:
            repo.close()


def test_missing_cloud_home_storage_fails_explicitly(household):
    original = household.app.state.home_store
    household.app.state.home_store = None
    assert household.get("/api/home/state").status_code == 503
    household.app.state.home_store = original
