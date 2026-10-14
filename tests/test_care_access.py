import hashlib
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app
from test_family_extension import account, household, join, write


@pytest.fixture
def family(tmp_path):
    settings = Settings(database_path=str(tmp_path / "access.db"), _env_file=None)
    app = create_app(settings)
    with account(app, "access-owner") as admin:
        hid = household(admin)["household_id"]
        pet = write(admin, "/api/home/pets", name="豆豆")["pets"][-1]["id"]
        yield app, admin, hid, pet, settings


def create(admin, pet, hours=24):
    response = admin.post(f"/api/family/pets/{pet}/care-access", json={"expires_in_hours": hours})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def bearer(token):
    return {"authorization": f"Bearer {token}"}


def test_access_created_once_hashed_persistent_and_safe_read_only_chat(family, monkeypatch):
    app, admin, hid, pet, settings = family
    record = create(admin, pet)
    token, grant = record["token"], record["grant"]
    listed = admin.get(f"/api/family/pets/{pet}/care-access")
    assert listed.json()["grants"][0]["id"] == grant["id"]
    assert token not in listed.text and "digest" not in listed.text
    row = app.state.family_store.conn.execute("SELECT digest FROM family_care_access").fetchone()
    assert row[0] == hashlib.sha256(token.encode()).hexdigest()

    def seed(home):
        stamp = grant["created_at"]
        home["memories"] += [
            {
                "id": "confirmed-1",
                "pet_id": pet,
                "text": "喜欢羽毛棒",
                "topic": "play",
                "status": "confirmed",
                "created_at": stamp,
                "valid_until": None,
                "version": 1,
                "author_user_id": "PRIVATE_ACCOUNT",
                "author_name": "PRIVATE_AUTHOR",
            }
        ]
        home["diary"].append(
            {
                "id": "private-diary",
                "pet_id": pet,
                "text": "PRIVATE_DIARY",
                "title": "私人日记",
                "happened_on": stamp[:10],
            }
        )
        home["pets"][0]["likes"] = "OTHER_PET_SECRET"
        home["pets"][-1]["photo_id"] = "PRIVATE_PHOTO"
        home["measurements"].append(
            {
                "id": "demo-weight",
                "pet_id": pet,
                "kind": "weight",
                "value_g": 99999,
                "value": 99.999,
                "unit": "kg",
                "source": "demo_sample",
                "measured_at": stamp,
            }
        )

    app.state.family_store.mutate(hid, seed)
    monkeypatch.setattr(app.state.family_assistant, "respond", lambda *a: pytest.fail("cloud seam"))
    before = json.dumps(app.state.family_store.read(hid), sort_keys=True)
    visitor = TestClient(app)
    context = visitor.get("/api/care-access/context", headers=bearer(token))
    assert context.status_code == 200
    assert context.json()["pet"]["name"] == "豆豆"
    assert context.json()["read_only"] is True
    assert context.json()["measurements"] == []
    for forbidden in (
        "PRIVATE_",
        "OTHER_PET_SECRET",
        "household_id",
        "user_id",
        "photo_id",
        "diary",
    ):
        assert forbidden not in context.text
    answer = visitor.post("/api/care-access/chat", headers=bearer(token), json={"text": "喜欢什么"})
    assert answer.status_code == 200 and "羽毛棒" in answer.json()["answer"]
    assert answer.json()["backend"] == "local_rules"
    command = visitor.post(
        "/api/care-access/chat", headers=bearer(token), json={"text": "安排陪玩"}
    )
    assert command.json()["action_executed"] is False
    assert "care_draft" not in command.json() and "proposal" not in command.text
    assert json.dumps(app.state.family_store.read(hid), sort_keys=True) == before
    assert (
        visitor.post(
            "/api/home/pets", headers=bearer(token), json={"name": "forbidden"}
        ).status_code
        == 401
    )
    restarted = create_app(settings)
    with TestClient(restarted) as after_restart:
        assert (
            after_restart.get("/api/care-access/context", headers=bearer(token)).status_code == 200
        )


@pytest.mark.parametrize("hours", [1, 4, 24, 72])
def test_admin_duration_validation_and_member_denial(family, hours):
    app, admin, _, pet, _ = family
    created = create(admin, pet, hours)
    grant = created["grant"]
    assert datetime.fromisoformat(grant["expires_at"]) - datetime.fromisoformat(
        grant["created_at"]
    ) == timedelta(hours=hours)
    assert (
        admin.post(f"/api/family/pets/{pet}/care-access", json={"expires_in_hours": 2}).status_code
        == 422
    )
    carer = account(app, "access-carer")
    try:
        join(admin, carer)
        assert carer.post(f"/api/family/pets/{pet}/care-access", json={}).status_code == 403
        assert carer.get(f"/api/family/pets/{pet}/care-access").status_code == 403
    finally:
        carer.close()
    admin.headers.pop("x-csrf-token")
    assert admin.post(f"/api/family/pets/{pet}/care-access", json={}).status_code == 403


def test_revoke_expiry_archive_bad_token_and_error_cache_policy(family):
    app, admin, _, pet, _ = family
    visitor = TestClient(app)
    created = create(admin, pet)
    path = f"/api/family/pets/{pet}/care-access/{created['grant']['id']}/revoke"
    assert admin.post(path).json()["status"] == "revoked"
    revoked = visitor.get("/api/care-access/context", headers=bearer(created["token"]))
    assert revoked.status_code == 410 and revoked.headers["cache-control"] == "no-store"
    expired = create(admin, pet)
    with app.state.family_store.conn:
        app.state.family_store.conn.execute(
            "UPDATE family_care_access SET expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",
            (expired["grant"]["id"],),
        )
    assert (
        visitor.get("/api/care-access/context", headers=bearer(expired["token"])).status_code == 410
    )
    archived = create(admin, pet)
    assert (
        admin.patch(f"/api/family/pets/{pet}/lifecycle", json={"archived": True}).status_code == 200
    )
    assert (
        visitor.get("/api/care-access/context", headers=bearer(archived["token"])).status_code
        == 410
    )
    assert (
        admin.patch(f"/api/family/pets/{pet}/lifecycle", json={"archived": False}).status_code
        == 200
    )
    assert (
        visitor.get("/api/care-access/context", headers=bearer(archived["token"])).status_code
        == 410
    )
    for response in (
        visitor.get("/api/care-access/context"),
        visitor.get("/api/care-access/context", headers=bearer("invalid")),
    ):
        assert response.status_code == 401 and response.headers["cache-control"] == "no-store"
    query = visitor.get("/api/care-access/context?token=invalid")
    assert query.status_code == 400


@pytest.mark.parametrize("action", ["demote", "remove"])
def test_creator_loss_of_admin_immediately_invalidates_existing_access(family, action):
    app, admin, _, pet, _ = family
    created = create(admin, pet)
    owner_id = admin.get("/api/family/me").json()["user"]["user_id"]
    other = account(app, "second-admin")
    try:
        join(admin, other)
        other_id = other.get("/api/family/me").json()["user"]["user_id"]
        assert (
            admin.patch(f"/api/family/members/{other_id}", json={"role": "admin"}).status_code
            == 200
        )
        if action == "demote":
            assert (
                other.patch(f"/api/family/members/{owner_id}", json={"role": "carer"}).status_code
                == 200
            )
        else:
            assert other.delete(f"/api/family/members/{owner_id}").status_code == 200
        response = TestClient(app).get("/api/care-access/context", headers=bearer(created["token"]))
        assert response.status_code == 410
        if action == "remove":
            join(other, admin)
        assert (
            other.patch(f"/api/family/members/{owner_id}", json={"role": "admin"}).status_code
            == 200
        )
        assert (
            TestClient(app)
            .get("/api/care-access/context", headers=bearer(created["token"]))
            .status_code
            == 410
        )
    finally:
        other.close()


def test_invalid_tokens_are_rate_limited_without_secret_echo(family):
    app, _, _, _, _ = family
    visitor = TestClient(app)
    responses = [
        visitor.get("/api/care-access/context", headers=bearer("invalid")) for _ in range(65)
    ]
    assert responses[-1].status_code == 429
    assert responses[-1].headers["cache-control"] == "no-store"
    assert "invalid" not in responses[-1].text


def test_care_quick_questions_cite_distinct_diet_and_actual_manual_completion(family):
    app, admin, hid, pet, _ = family
    created = create(admin, pet)
    stamp = created["grant"]["created_at"]

    def seed(home):
        for meaning, grams in (("actual_intake", 10), ("food_offered", 30), ("dispensed", 20)):
            home["measurements"].append(
                {
                    "id": meaning,
                    "pet_id": pet,
                    "kind": "diet",
                    "value": grams,
                    "unit": "g",
                    "value_g": grams,
                    "measured_at": stamp,
                    "source": "owner_measured",
                    "diet_type": meaning,
                    "note": "主人填写的猫粮备注",
                }
            )
        home["tasks"].append(
            {
                "id": "done-task",
                "pet_id": pet,
                "kind": "water",
                "title": "真实换水",
                "due_at": stamp,
                "completed": True,
                "occurrence_id": "done-care",
                "updated_at": stamp,
            }
        )
        home["occurrences"].append(
            {
                "id": "done-care",
                "pet_id": pet,
                "task_id": "done-task",
                "due_at": stamp,
                "completed_at": stamp,
                "completed_by": "PRIVATE_ACTOR",
                "status": "completed",
                "source": "manual_care",
            }
        )

    app.state.family_store.mutate(hid, seed)
    visitor = TestClient(app)
    headers = bearer(created["token"])
    diet = visitor.post(
        "/api/care-access/chat", headers=headers, json={"text": "最近吃了什么"}
    ).json()
    assert "实际摄入 10 g" in diet["answer"]
    assert "提供食物 30 g" in diet["answer"]
    assert "记录出粮 20 g" in diet["answer"]
    assert "主人填写的猫粮备注" in diet["answer"]
    assert set(diet["source_record_ids"]) == {"actual_intake", "food_offered", "dispensed"}
    care = visitor.post(
        "/api/care-access/chat", headers=headers, json={"text": "最近做了哪些照护"}
    ).json()
    assert "真实换水" in care["answer"]
    assert care["source_record_ids"] == ["done-care"]


def test_scoped_management_and_recheck_before_context_or_chat_response(family, monkeypatch):
    import pawtwin.care_access as access

    app, admin, _, pet, _ = family
    created = create(admin, pet)
    other = account(app, "unrelated-owner")
    try:
        household(other)
        assert other.get(f"/api/family/pets/{pet}/care-access").status_code == 404
        path = f"/api/family/pets/{pet}/care-access/{created['grant']['id']}/revoke"
        assert other.post(path).status_code == 404
    finally:
        other.close()
    original = access.public_context

    def revoke_during_projection(repo, grant, home):
        projected = original(repo, grant, home)
        repo.revoke_care_access(grant["household"], grant["pet"], grant["id"], grant["creator"])
        return projected

    monkeypatch.setattr(access, "public_context", revoke_during_projection)
    visitor = TestClient(app)
    assert (
        visitor.get("/api/care-access/context", headers=bearer(created["token"])).status_code == 410
    )
    second = create(admin, pet)
    response = visitor.post(
        "/api/care-access/chat", headers=bearer(second["token"]), json={"text": "喜欢什么"}
    )
    assert response.status_code == 410 and "豆豆" not in response.text


def test_unexpected_projection_failure_is_opaque_and_never_cached(family, monkeypatch):
    import pawtwin.care_access as access

    app, admin, _, pet, _ = family
    created = create(admin, pet)

    def unavailable(*args):
        raise RuntimeError("PRIVATE_EXCEPTION_CONTENT")

    monkeypatch.setattr(access, "public_context", unavailable)
    response = TestClient(app, raise_server_exceptions=False).get(
        "/api/care-access/context",
        headers=bearer(created["token"]),
    )
    assert response.status_code == 500
    assert response.headers.get("cache-control") == "no-store"
    assert "PRIVATE_EXCEPTION" not in response.text
