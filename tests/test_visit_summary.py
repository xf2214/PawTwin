from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pawtwin.config import Settings
from pawtwin.main import create_app
from test_family_extension import account, household


@pytest.fixture
def family(tmp_path):
    app = create_app(Settings(database_path=str(tmp_path / "visit.db"), _env_file=None))
    with account(app, "visit-owner") as client:
        hid = household(client)["household_id"]
        yield app, client, hid


def measurement(record_id, at, source="owner_measured", **extra):
    return {
        "id": record_id,
        "pet_id": "mochi",
        "kind": "weight",
        "value": 2,
        "unit": "kg",
        "value_g": 2000,
        "measured_at": at,
        "recorded_at": at,
        "source": source,
        "diet_type": None,
        "note": "真实原始备注",
        "version": 1,
        "deleted": False,
        "author_user_id": "PRIVATE_ACCOUNT",
        "household_id": "PRIVATE_FAMILY",
        "corrections": [{"note": "PRIVATE_CORRECTION"}],
        **extra,
    }


def test_visit_window_preserves_historical_today_observations_and_completion_titles(family):
    app, client, hid = family
    now = datetime.now(UTC)
    yesterday = (now - timedelta(days=1)).isoformat()
    local_day = (now - timedelta(days=1)).astimezone(ZoneInfo("Asia/Shanghai")).date().isoformat()

    def seed(home):
        home["notes"].append(
            {
                "id": "past-observation",
                "pet_id": "mochi",
                "text": "昨天的实际观察",
                "scope": "today",
                "activity": "general",
                "created_at": yesterday,
                "author_user_id": "PRIVATE_ACCOUNT",
                "version": 2,
            }
        )
        home["diary"].append(
            {
                "id": "diary-1",
                "pet_id": "mochi",
                "title": "原始日记",
                "text": "真实文字",
                "happened_on": local_day,
                "photo_id": "PRIVATE_PHOTO",
                "created_at": yesterday,
            }
        )
        home["tasks"].append(
            {
                "id": "task-1",
                "pet_id": "mochi",
                "title": "后来的任务名称",
                "kind": "water",
                "due_at": yesterday,
                "completed": True,
                "occurrence_id": "care-1",
                "updated_at": now.isoformat(),
                "revisions": [
                    {
                        "occurrence_id": "care-1",
                        "title": "历史换水名称",
                        "updated_at": yesterday,
                    }
                ],
            }
        )
        home["occurrences"].append(
            {
                "id": "care-1",
                "task_id": "task-1",
                "pet_id": "mochi",
                "due_at": yesterday,
                "completed_at": yesterday,
                "completed_by": "PRIVATE_ACCOUNT",
                "status": "completed",
                "source": "manual_care",
            }
        )

    app.state.family_store.mutate(hid, seed)
    response = client.get("/api/family/pets/mochi/visit-summary?days=7")
    assert response.status_code == 200
    body = response.json()
    assert body.get("days") == 7
    assert body["observations"][0]["text"] == "昨天的实际观察"
    assert body["care"][0]["title"] == "历史换水名称"
    assert body["diary"][0]["happened_on"] == local_day
    assert body["source_versions"]["past-observation"] == 2
    assert "PRIVATE_" not in response.text
    assert datetime.fromisoformat(body["window_end"]) <= datetime.fromisoformat(body["as_of"])


def test_visit_latest_weight_outside_window_demo_filter_and_unknown_food(family):
    app, client, hid = family
    now = datetime.now(UTC)

    def seed(home):
        home["measurements"] += [
            measurement("older-real", (now - timedelta(days=31)).isoformat()),
            measurement("new-demo", (now - timedelta(hours=1)).isoformat(), "demo_sample"),
            measurement("deleted-real", now.isoformat(), deleted=True),
            measurement("future-real", (now + timedelta(days=1)).isoformat()),
        ]

    app.state.family_store.mutate(hid, seed)
    body = client.get("/api/family/pets/mochi/visit-summary?days=30").json()
    assert body.get("measurements") == []
    assert body["latest_weight"]["id"] == "older-real"
    assert body["source_versions"] == {"older-real": 1}
    assert body["demo_excluded_count"] == 1
    assert any("食物" in field for field in body["missing_fields"])
    included = client.get("/api/family/pets/mochi/visit-summary?days=30&include_demo=true").json()
    assert included["latest_weight"]["id"] == "new-demo"
    assert included["measurements"][0]["source"] == "demo_sample"
    assert client.get("/api/family/pets/mochi/visit-summary?days=14").status_code == 422
    app.state.family_store.mutate(
        hid,
        lambda h: h["measurements"][0].update(deleted=True, version=2),
    )
    assert client.get("/api/family/pets/mochi/visit-summary").json()["latest_weight"] is None


def test_visit_age_basis_timezone_scope_and_revoked_account(family):
    app, client, hid = family
    birthday = (datetime.now(ZoneInfo("Asia/Shanghai")).date() - timedelta(days=400)).isoformat()
    app.state.family_store.mutate(hid, lambda h: h["pets"][0].update(birthday=birthday))
    body = client.get("/api/family/pets/mochi/visit-summary?days=7").json()
    assert body.get("age", {}).get("basis") == "birthday"
    assert body["age"]["days"] == 400
    assert body["timezone"] == "Asia/Shanghai"
    app.state.family_store.mutate(hid, lambda h: h["pets"][0].update(birthday=None, age_years=1.2))
    assert client.get("/api/family/pets/mochi/visit-summary").json()["age"] == {
        "years": 1.2,
        "days": None,
        "basis": "owner_entered",
        "estimated": True,
    }
    other = account(app, "other-visit-owner")
    try:
        household(other)
        assert other.get("/api/family/pets/not-owned/visit-summary").status_code == 404
    finally:
        other.close()


def test_visit_calendar_window_dst_boundaries_and_future_birthday():
    from pawtwin.home_store import initial_home
    from pawtwin.visit_summary import build_summary

    home = initial_home()
    home.update(measurements=[], memories=[], occurrences=[], revision=1)
    home["pets"][0]["birthday"] = "2027-01-01"
    home["measurements"] = [
        measurement("at-start", "2026-03-02T05:00:00+00:00"),
        measurement("before-start", "2026-03-02T04:59:59+00:00"),
        measurement("at-cutoff", "2026-03-09T01:00:00+00:00"),
        measurement("after-cutoff", "2026-03-09T01:00:00.000001+00:00"),
    ]
    result = build_summary(
        home, "mochi", "America/New_York", 7, now=datetime(2026, 3, 9, 1, tzinfo=UTC)
    )
    assert result["window_start"] == "2026-03-02T05:00:00+00:00"
    assert {r["id"] for r in result["measurements"]} == {"at-start", "at-cutoff"}
    assert result["age"]["basis"] == "unknown" and result["age"]["years"] is None


def test_visit_diet_retains_raw_food_note_without_inferred_fields(family):
    app, client, hid = family
    record = measurement(
        "diet-note", datetime.now(UTC).isoformat(), kind="diet", diet_type="actual_intake"
    )
    app.state.family_store.mutate(hid, lambda h: h["measurements"].append(record))
    result = client.get("/api/family/pets/mochi/visit-summary").json()
    assert result["measurements"][0]["note"] == "真实原始备注"
    assert "food_name" not in result["measurements"][0]
    assert result["source_versions"]["diet-note"] == 1
