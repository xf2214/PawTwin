"""Care totals use durable completion facts, with legacy-log compatibility."""

from datetime import UTC, date, datetime
from uuid import uuid4

from pawtwin.config import Settings
from pawtwin.family_store import FamilyStore
from pawtwin.growth import build_report
from pawtwin.home_api import log
from pawtwin.home_store import initial_home
from pawtwin.main import create_app
from test_family_extension import account, household, write

HOUSEHOLD = {"household_id": "demo-owner", "timezone": "UTC"}
NOW = datetime(2026, 10, 12, tzinfo=UTC)


def home_document():
    home = initial_home()
    home.update(
        household_id="demo-owner", measurements=[], reports=[], occurrences=[], revision=1,
        device_receipts=[], simulated_device_connected=False,
    )
    return home


def occurrence(record_id, completed_at, member="member-a", **overrides):
    return {
        "id": record_id, "task_id": "task-1", "pet_id": "mochi",
        "due_at": completed_at, "completed_at": completed_at, "completed_by": member,
        "status": "completed", "source": "manual_care", **overrides,
    }


def completion_log(record_id, created_at, member="member-a", **overrides):
    return {
        "id": record_id, "pet_id": "mochi", "text": "完成：换水", "actor": member,
        "actor_id": member, "created_at": created_at, "source": "owner_record", **overrides,
    }


def task_record(title="换水", **overrides):
    return {
        "id": "task-1", "pet_id": "mochi", "title": title, "completed": False,
        "due_at": "2026-10-13T12:00:00+00:00", "created_at": "2026-09-01T00:00:00+00:00",
        "updated_at": "2026-10-01T12:00:00+00:00", "status": "pending",
        "occurrence_id": "completion-1", "revisions": [], **overrides,
    }


def report_for(home, day="2026-10-01", now=NOW):
    return build_report(home, "mochi", date.fromisoformat(day), "daily", HOUSEHOLD, now)


def test_old_report_keeps_completion_after_more_than_1000_unrelated_actions(tmp_path):
    repo = FamilyStore(str(tmp_path / "care.db"))
    try:
        def add_completion(home):
            home["tasks"].append(task_record())
            home["occurrences"].append(occurrence("completion-1", "2026-10-01T12:00:00+00:00"))
            home["history"].append(completion_log("history-1", "2026-10-01T12:00:00+00:00"))

        repo.mutate("demo-owner", add_completion)
        original = repo.generate("demo-owner", "mochi", date(2026, 10, 1), "daily", NOW)
        assert original["care"]["manual_completed"] == 1

        def unrelated_actions(home):
            for number in range(1001):
                log(home, "mochi", f"更新物品位置 {number}")

        repo.mutate("demo-owner", unrelated_actions)
        stored = repo.read("demo-owner")
        current = next(r for r in stored["reports"] if r["status"] == "current")
        assert current["care"]["manual_completed"] == 1
        assert current["care"]["by_member"] == {"member-a": 1}
        assert "completion-1" in current["source_record_ids"]
        assert current["source_versions"]["completion-1"] == 1
    finally:
        repo.close()


def test_mixed_durable_and_legacy_completions_do_not_double_count():
    home = home_document()
    home["tasks"] = [task_record()]
    home["occurrences"] = [
        occurrence("completion-1", "2026-10-01T12:00:00+00:00", version=3),
        occurrence("completion-2", "2026-10-01T16:00:00+00:00"),
    ]
    home["history"] = [
        completion_log("legacy-1", "2026-10-01T08:00:00+00:00", "member-b", version=2),
        completion_log("history-1", "2026-10-01T12:00:00.000100+00:00"),
    ]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 3
    assert result["care"]["by_member"] == {"member-a": 2, "member-b": 1}
    assert {"completion-1", "completion-2", "legacy-1", "history-1"} <= set(
        result["source_record_ids"]
    )
    assert result["source_versions"]["completion-1"] == 3
    assert result["source_versions"]["legacy-1"] == 2


def test_old_same_title_near_simultaneous_completions_match_logs_one_to_one():
    home = home_document()
    home["tasks"] = [task_record(
        occurrence_id="completion-2", updated_at="2026-10-01T12:00:00.000010+00:00",
        revisions=[task_record()],
    )]
    home["occurrences"] = [
        occurrence("completion-1", "2026-10-01T12:00:00+00:00"),
        occurrence("completion-2", "2026-10-01T12:00:00.000010+00:00"),
    ]
    home["history"] = [
        completion_log("history-1", "2026-10-01T12:00:00.000100+00:00"),
        completion_log("history-2", "2026-10-01T12:00:00.000200+00:00"),
        completion_log("legacy-other-member", "2026-10-01T12:00:00.000300+00:00", "member-b"),
        completion_log("legacy-later", "2026-10-01T12:00:10+00:00"),
    ]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 4
    assert result["care"]["by_member"] == {"member-a": 3, "member-b": 1}
    assert {"completion-1", "completion-2"} <= set(result["source_record_ids"])


def test_first_completion_of_migrated_repeating_task_uses_its_undated_revision_title():
    home = home_document()
    original = task_record("旧换水任务")
    original.pop("updated_at")
    original.pop("created_at")
    home["tasks"] = [task_record(
        "后来修改的新标题", occurrence_id="next-occurrence",
        updated_at="2026-10-02T12:00:00+00:00", revisions=[original],
    )]
    home["occurrences"] = [occurrence("completion-1", "2026-10-01T12:00:00+00:00")]
    home["history"] = [completion_log(
        "old-completion-log", "2026-10-01T12:00:00.000100+00:00", text="完成：旧换水任务",
    )]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 1
    assert result["care"]["by_member"] == {"member-a": 1}
    assert {"completion-1", "old-completion-log"} <= set(result["source_record_ids"])


def test_completion_timestamp_governs_windows_even_when_linked_log_is_later():
    home = home_document()
    home["occurrences"] = [
        occurrence("before-midnight", "2026-10-01T23:59:59.999900+00:00"),
        occurrence("after-midnight", "2026-10-02T00:00:00.000100+00:00", "member-b"),
    ]
    home["history"] = [
        completion_log(
            "late-log-1", "2026-10-02T00:00:00.000300+00:00",
            occurrence_id="before-midnight", task_id="task-1",
        ),
        completion_log(
            "late-log-2", "2026-10-02T00:00:00.000400+00:00", "member-b",
            occurrence_id="after-midnight", task_id="task-1",
        ),
    ]
    previous = report_for(home)
    assert previous["care"]["manual_completed"] == 1
    assert previous["care"]["by_member"] == {"member-a": 1}
    current = report_for(home, "2026-10-02", datetime(2026, 10, 2, 0, 0, 0, 200, tzinfo=UTC))
    assert current["care"]["manual_completed"] == 1
    assert current["care"]["by_member"] == {"member-b": 1}
    assert report_for(home, "2026-10-02")["care"]["manual_completed"] == 1


def test_old_unlinked_log_across_midnight_does_not_create_a_second_completion():
    home = home_document()
    home["tasks"] = [task_record(updated_at="2026-10-01T23:59:59.999900+00:00")]
    home["occurrences"] = [occurrence("completion-1", "2026-10-01T23:59:59.999900+00:00")]
    home["history"] = [completion_log("history-1", "2026-10-02T00:00:00.000100+00:00")]
    assert report_for(home)["care"]["manual_completed"] == 1
    assert report_for(home, "2026-10-02")["care"]["manual_completed"] == 0
    assert "history-1" in report_for(home, "2026-10-02")["source_record_ids"]


def test_explicitly_linked_occurrence_does_not_consume_an_independent_legacy_completion():
    home = home_document()
    home["tasks"] = [task_record()]
    home["occurrences"] = [occurrence("completion-1", "2026-10-01T12:00:00+00:00")]
    home["history"] = [
        completion_log("linked", "2026-10-01T12:00:00.000100+00:00", occurrence_id="completion-1"),
        completion_log("independent-legacy", "2026-10-01T12:00:00.000200+00:00"),
    ]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 2
    assert result["care"]["by_member"] == {"member-a": 2}


def test_only_valid_manual_completions_in_this_household_pet_and_cutoff_are_counted():
    home = home_document()
    home["occurrences"] = [
        occurrence("included", "2026-10-01T00:00:00+00:00", version=7),
        occurrence("other-pet", "2026-10-01T01:00:00+00:00", pet_id="other-pet"),
        occurrence("other-household", "2026-10-01T01:00:00+00:00", household_id="elsewhere"),
        occurrence("deleted", "2026-10-01T01:00:00+00:00", deleted=True),
        occurrence("cancelled", "2026-10-01T01:00:00+00:00", status="cancelled"),
        occurrence("device", "2026-10-01T01:00:00+00:00", source="simulated_device"),
        occurrence("at-cutoff", "2026-10-01T12:00:00+00:00"),
        occurrence("strictly-future", "2026-10-01T12:00:00.000001+00:00"),
        occurrence("before-window", "2026-09-30T23:59:59+00:00"),
    ]
    home["history"] = [
        completion_log("foreign-log", "2026-10-01T01:00:00+00:00", household_id="elsewhere"),
        completion_log("cancel-log", "2026-10-01T01:00:00+00:00", action="cancel"),
        completion_log("deleted-log", "2026-10-01T01:00:00+00:00", deleted=True),
    ]
    result = report_for(home, now=datetime(2026, 10, 1, 12, tzinfo=UTC))
    assert result["care"]["manual_completed"] == 2
    assert result["care"]["by_member"] == {"member-a": 2}
    assert set(result["source_record_ids"]) == {"included", "at-cutoff", "cancel-log"}
    assert result["source_versions"] == {"included": 7, "at-cutoff": 1, "cancel-log": 1}


def test_legacy_only_history_remains_reported_with_original_member_and_record_id():
    home = home_document()
    home["history"] = [
        completion_log("legacy-prefix", "2026-10-01T09:00:00+00:00"),
        completion_log("legacy-action", "2026-10-01T10:00:00+00:00", "member-b", action="complete"),
    ]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 2
    assert result["care"]["by_member"] == {"member-a": 1, "member-b": 1}
    assert result["source_record_ids"] == ["legacy-prefix", "legacy-action"]


def test_legacy_records_without_actor_id_keep_consistent_unknown_or_author_attribution():
    home = home_document()
    home["history"] = [
        {
            "id": "original-unattributed", "pet_id": "mochi", "text": "完成：换水",
            "actor": "爸爸", "created_at": "2026-10-01T09:00:00+00:00", "source": "owner_record",
        },
        {
            "id": "migrated-unattributed", "pet_id": "mochi", "text": "完成：换水",
            "actor": "爸爸", "actor_id": None, "author_user_id": "legacy-unknown",
            "author_name": "爸爸", "created_at": "2026-10-01T10:00:00+00:00",
            "source": "owner_record",
        },
        {
            "id": "author-attributed", "pet_id": "mochi", "text": "完成：换水",
            "actor": "爸爸", "author_user_id": "member-b",
            "created_at": "2026-10-01T11:00:00+00:00", "source": "owner_record",
        },
    ]
    result = report_for(home)
    assert result["care"]["manual_completed"] == 3
    assert result["care"]["by_member"] == {"legacy-unknown": 2, "member-b": 1}
    assert result["source_record_ids"] == [
        "original-unattributed", "migrated-unattributed", "author-attributed",
    ]


def test_current_report_includes_receipt_committed_on_the_same_clock_tick():
    home = home_document()
    home["simulated_device_connected"] = True
    home["device_receipts"] = [{
        "id": "same-tick-receipt", "pet_id": "mochi", "status": "succeeded",
        "created_at": "2026-10-01T12:00:00+00:00", "kind": "dispense_food",
        "grams": 15, "simulated": True, "version": 7,
    }]
    result = report_for(home, now=datetime(2026, 10, 1, 12, tzinfo=UTC))
    assert result["care"]["device_success"] == 1
    assert result["diet"]["simulated_device_dispensed_g"] == 15
    assert result["diet"]["actual_intake_g"] is None
    assert result["source_record_ids"] == ["same-tick-receipt"]
    assert result["source_versions"] == {"same-tick-receipt": 7}


def test_current_report_includes_manual_care_completed_on_the_same_clock_tick():
    home = home_document()
    home["occurrences"] = [occurrence("same-tick-care", "2026-10-01T12:00:00+00:00")]
    result = report_for(home, now=datetime(2026, 10, 1, 12, tzinfo=UTC))
    assert result["care"]["manual_completed"] == 1
    assert result["care"]["by_member"] == {"member-a": 1}
    assert result["source_record_ids"] == ["same-tick-care"]


def test_current_report_includes_weight_and_diet_saved_on_the_same_clock_tick():
    home = home_document()
    home["measurements"] = [
        {
            "id": "same-tick-weight", "pet_id": "mochi", "kind": "weight",
            "value_g": 1500, "measured_at": "2026-10-01T12:00:00+00:00", "version": 3,
        },
        {
            "id": "same-tick-diet", "pet_id": "mochi", "kind": "diet",
            "diet_type": "actual_intake", "value_g": 50,
            "measured_at": "2026-10-01T12:00:00+00:00", "version": 2,
        },
    ]
    result = report_for(home, now=datetime(2026, 10, 1, 12, tzinfo=UTC))
    assert result["weight"]["latest_g"] == 1500
    assert result["coverage"]["weight_measurements"] == 1
    assert result["diet"]["actual_intake_g"] == 50
    assert result["coverage"]["diet_records"] == 1
    assert set(result["source_record_ids"]) == {"same-tick-weight", "same-tick-diet"}
    assert result["source_versions"] == {"same-tick-weight": 3, "same-tick-diet": 2}


def test_closed_report_excludes_receipt_at_next_window_start():
    home = home_document()
    home["simulated_device_connected"] = True
    home["device_receipts"] = [{
        "id": "next-day-receipt", "pet_id": "mochi", "status": "succeeded",
        "created_at": "2026-10-02T00:00:00+00:00", "kind": "dispense_food",
        "grams": 15, "simulated": True,
    }]
    home["occurrences"] = [occurrence("next-day-care", "2026-10-02T00:00:00+00:00")]
    home["measurements"] = [{
        "id": "next-day-weight", "pet_id": "mochi", "kind": "weight", "value_g": 1500,
        "measured_at": "2026-10-02T00:00:00+00:00",
    }]
    result = report_for(home)
    assert result["care"]["device_success"] == 0
    assert result["care"]["manual_completed"] == 0
    assert result["diet"]["simulated_device_dispensed_g"] is None
    assert result["weight"]["latest_g"] is None
    assert result["source_record_ids"] == []


def test_api_single_and_repeating_care_links_each_completion_and_preserves_historical_titles(
    tmp_path, monkeypatch,
):
    import pawtwin.home_api as api

    current = datetime(2026, 10, 1, 12, tzinfo=UTC)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current.astimezone(tz) if tz else current.replace(tzinfo=None)

    monkeypatch.setattr(api, "datetime", Clock)
    monkeypatch.setattr(api, "now_iso", lambda: current.isoformat())
    app = create_app(Settings(database_path=str(tmp_path / "actual-care.db"), _env_file=None))
    with account(app, "statistics-owner") as client:
        hid = household(client)["household_id"]
        repeating = write(
            client, "/api/home/pets/mochi/tasks", kind="water", title="换水",
            due_at="2026-10-01T10:00:00+00:00", interval_days=1,
        )["tasks"][-1]
        single = write(
            client, "/api/home/pets/mochi/tasks", kind="bath", title="洗澡",
            due_at="2026-10-01T10:00:00+00:00",
        )["tasks"][-1]
        for task in (repeating, single):
            write(
                client, f"/api/home/tasks/{task['id']}/action", action="complete",
                event_id=str(uuid4()), version=1,
            )
        current = datetime(2026, 10, 2, 12, tzinfo=UTC)
        edited = write(
            client, f"/api/home/tasks/{repeating['id']}/action", action="edit", title="清洗水碗",
            event_id=str(uuid4()), version=2,
        )["tasks"][0]
        completed = write(
            client, f"/api/home/tasks/{edited['id']}/action", action="complete",
            event_id=str(uuid4()), version=3,
        )["tasks"][0]
        write(
            client, f"/api/home/tasks/{completed['id']}/action", action="cancel",
            event_id=str(uuid4()), version=4,
        )
        home = client.get("/api/home/state").json()
        logs = [h for h in home["history"] if h["text"].startswith("完成：")]
        assert len(home["occurrences"]) == 3
        assert len(logs) == 3
        assert {h.get("occurrence_id") for h in logs} == {o["id"] for o in home["occurrences"]}
        assert {h.get("task_id") for h in logs} == {repeating["id"], single["id"]}
        # Exercise legacy correlation too, after the repeating task was renamed.
        for history in logs:
            history.pop("occurrence_id")
            history.pop("task_id")
        first = build_report(home, "mochi", date(2026, 10, 1), "daily", {
            "household_id": hid, "timezone": "UTC",
        }, NOW)
        second = build_report(home, "mochi", date(2026, 10, 2), "daily", {
            "household_id": hid, "timezone": "UTC",
        }, NOW)
        assert first["care"]["manual_completed"] == 2
        assert second["care"]["manual_completed"] == 1
        uid = client.get("/api/family/me").json()["user"]["user_id"]
        assert first["care"]["by_member"] == {uid: 2}
