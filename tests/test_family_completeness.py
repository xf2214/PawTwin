from datetime import UTC, datetime

import pytest
from pawtwin.config import Settings
from pawtwin.contracts import build_openapi_schema
from pawtwin.main import create_app
from test_family_extension import account, household, join, write


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(_env_file=None, database_path=str(tmp_path / "complete.db")))


def test_note_and_diary_corrections_change_context_and_report_with_version_conflicts(app):
    client = account(app, "record-corrections")
    household(client)
    note = write(client, "/api/home/pets/mochi/notes", text="old preference", scope="preference")[
        "notes"
    ][-1]
    path = f"/api/family/pets/mochi/notes/{note['id']}"
    assert (
        client.patch(
            path, json={"version": 1, "text": "corrected preference", "scope": "preference"}
        ).status_code
        == 200
    )
    assert client.patch(path, json={"version": 1, "text": "stale"}).status_code == 409
    assert "old preference" not in client.get("/api/family/pets/mochi/context").text
    diary = write(
        client, "/api/home/pets/mochi/diary", title="date correction", happened_on="2026-09-30"
    )["diary"][-1]
    write(client, "/api/family/pets/mochi/reports/generate", period="daily", date="2026-09-30")
    assert (
        client.patch(
            f"/api/family/pets/mochi/diary/{diary['id']}",
            json={"version": 1, "title": "date correction", "happened_on": "2026-10-01"},
        ).status_code
        == 200
    )
    reports = client.get("/api/family/pets/mochi/reports").json()["reports"]
    assert next(r for r in reports if r["status"] == "current")["growth"]["diary_count"] == 0


def test_family_contract_declares_scoped_session_and_record_response_shapes():
    schema = build_openapi_schema()
    session = schema["paths"]["/api/family/me"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert session.get("$ref", "").endswith("/FamilySessionView")
    measurement = schema["components"]["schemas"]["MeasurementView"]
    assert {"household_id", "pet_id", "author_user_id", "version", "value_g", "measured_at"} <= set(
        measurement["required"]
    )


def test_timezone_change_supersedes_old_window_and_recomputes_source_records(app):
    client = account(app, "timezone-change")
    household(client)
    write(
        client,
        "/api/family/pets/mochi/measurements",
        kind="diet",
        diet_type="actual_intake",
        value=30,
        unit="g",
        measured_at="2026-10-01T20:00:00Z",
    )
    old = write(
        client, "/api/family/pets/mochi/reports/generate", period="daily", date="2026-10-02"
    )
    assert old["diet"]["actual_intake_g"] == 30
    assert (
        client.patch("/api/family/household", json={"name": "Home", "timezone": "UTC"}).status_code
        == 200
    )
    reports = client.get("/api/family/pets/mochi/reports").json()["reports"]
    current = [r for r in reports if r["status"] == "current" and r["date"] == "2026-10-02"]
    assert len(current) == 1
    assert current[0]["diet"]["actual_intake_g"] is None
    assert next(r for r in reports if r["report_id"] == old["report_id"])["status"] == "superseded"


def test_confirmed_profile_supplies_growth_reference_inputs_without_reasking(app):
    client = account(app, "profile-complete")
    household(client)
    response = client.put(
        "/api/home/pets/mochi",
        json={
            "name": "Mochi",
            "species": "dog",
            "gender": "female",
            "birthday": "2026-07-01",
            "birthday_estimated": True,
            "neutered": False,
            "expected_adult_weight_kg": 8,
        },
    )
    assert response.status_code == 200, response.text
    pet = response.json()["pets"][0]
    assert pet["birthday_estimated"] and pet["neutered"] is False
    answer = write(client, "/api/family/pets/mochi/chat", text="三个月通常多重", entry="app")
    assert "适用成长参考仍缺" not in answer["answer"]
    assert "不能给出标准体重" in answer["answer"]


def test_profile_archive_is_admin_only_reversible_and_keeps_original_records(app):
    admin, carer = account(app, "archive-admin"), account(app, "archive-carer")
    household(admin)
    join(admin, carer)
    home = write(admin, "/api/home/pets", name="Luna")
    pet = home["pets"][-1]["id"]
    fact = write(
        admin,
        f"/api/family/pets/{pet}/measurements",
        kind="weight",
        value=2,
        unit="kg",
        measured_at="2026-10-01T00:00:00Z",
    )
    path = f"/api/family/pets/{pet}/lifecycle"
    assert carer.patch(path, json={"archived": True}).status_code == 403
    assert admin.patch(path, json={"archived": True}).status_code == 200
    assert pet not in {p["id"] for p in admin.get("/api/home/state").json()["pets"]}
    assert admin.get(f"/api/family/pets/{pet}/context").status_code == 404
    assert admin.post(f"/api/home/pets/{pet}/notes", json={"text": "denied"}).status_code == 404
    assert carer.get("/api/family/pets/archived").status_code == 403
    assert admin.get("/api/family/pets/archived").json()["pets"][0]["id"] == pet
    assert admin.patch(path, json={"archived": False}).status_code == 200
    assert (
        admin.get(f"/api/family/pets/{pet}/measurements").json()["records"][0]["id"] == fact["id"]
    )
    assert (
        admin.patch("/api/family/pets/mochi/lifecycle", json={"archived": True}).status_code == 409
    )


def test_reference_question_uses_known_age_and_declares_missing_breed_evidence(app):
    client = account(app, "known-age")
    household(client)
    assert (
        client.put(
            "/api/home/pets/mochi",
            json={
                "name": "Mochi",
                "species": "dog",
                "age_years": 0.25,
                "gender": "male",
                "breed": "Poodle",
                "expected_adult_weight_kg": 8,
            },
        ).status_code
        == 200
    )
    response = write(client, "/api/family/pets/mochi/chat", text="三个月通常多重", entry="app")
    assert "适用成长参考仍缺" not in response["answer"]
    response = write(
        client, "/api/family/pets/mochi/chat", text="这个品种通常什么习性", entry="app"
    )
    assert "Poodle" in response["answer"]
    assert "缺少适用" in response["answer"]


def test_report_worker_imports_original_before_advancing_seed_report_cursor(app):
    source = app.state.legacy_source_store
    source.mutate(
        "demo-owner",
        lambda home: home["diary"].append(
            {
                "id": "legacy-yesterday",
                "pet_id": "mochi",
                "title": "before first login",
                "happened_on": "2026-10-02",
                "created_at": "2026-10-02T00:00:00Z",
            }
        ),
    )
    before = source.read("demo-owner")
    repo = app.state.family_store
    assert repo.run_due_reports(datetime(2026, 10, 3, 3, tzinfo=UTC)) > 0
    report = next(r for r in repo.read("demo-owner")["reports"] if r["status"] == "current")
    assert report["growth"]["diary_count"] == 1
    assert repo.import_legacy(source)["already_imported"]
    assert source.read("demo-owner") == before


def test_outside_window_latest_weight_sources_follow_correction_and_deletion(app):
    client = account(app, "weight-provenance")
    household(client)
    path = "/api/family/pets/mochi/measurements"
    fact = write(
        client, path, kind="weight", value=1.2, unit="kg", measured_at="2026-09-25T00:00:00Z"
    )
    report = write(
        client, "/api/family/pets/mochi/reports/generate", period="weekly", date="2026-10-02"
    )
    assert report["weight"]["latest_g"] == 1200
    assert report["weight"]["change_g"] is None
    assert report["weight"]["span_days"] is None
    assert report["weight"]["source_record_ids"] == [fact["id"]]
    assert report["source_versions"][fact["id"]] == 1
    assert fact["id"] in report["source_record_ids"]

    corrected = client.put(
        f"{path}/{fact['id']}",
        json={
            "version": 1,
            "kind": "weight",
            "value": 1250,
            "unit": "g",
            "measured_at": "2026-09-25T00:00:00Z",
        },
    )
    assert corrected.status_code == 200, corrected.text
    current = next(
        r for r in client.get("/api/family/pets/mochi/reports").json()["reports"]
        if r["status"] == "current"
    )
    assert current["weight"]["latest_g"] == 1250
    assert current["source_versions"][fact["id"]] == 2
    assert current["weight"]["source_record_ids"] == [fact["id"]]

    assert client.delete(f"{path}/{fact['id']}?version=2").status_code == 200
    current = next(
        r for r in client.get("/api/family/pets/mochi/reports").json()["reports"]
        if r["status"] == "current"
    )
    assert current["weight"]["latest_g"] is None
    assert current["weight"]["source_record_ids"] == []
    assert fact["id"] not in current["source_record_ids"]
    assert fact["id"] not in current["source_versions"]
