import pytest
from pawtwin.visit_summary import care_record, historical_title


def occurrence():
    return {
        "id": "completion-1",
        "task_id": "task-1",
        "pet_id": "mochi",
        "due_at": "2026-10-01T10:00:00+00:00",
        "completed_at": "2026-10-01T12:00:00+00:00",
        "status": "completed",
        "source": "manual_care",
    }


@pytest.mark.parametrize("missing_task", [True, False])
def test_missing_historical_title_is_marked_as_system_fallback(missing_task):
    home = {
        "tasks": []
        if missing_task
        else [
            {
                "id": "task-1",
                "kind": "water",
                "title": "Later owner title",
                "occurrence_id": "another-completion",
            }
        ],
    }

    result = care_record(home, occurrence())

    assert result["title"] == "人工照护（历史名称未记录）"
    assert result.get("title_is_fallback") is True
    assert historical_title(home, occurrence()) == "人工照护（历史名称未记录）"


@pytest.mark.parametrize("snapshot_source", ["current", "dated_revision", "undated_revision"])
def test_owner_title_equal_to_fallback_is_preserved_as_owner_content(snapshot_source):
    snapshot = {
        "occurrence_id": "completion-1",
        "title": "人工照护（历史名称未记录）",
    }
    if snapshot_source != "undated_revision":
        snapshot["updated_at"] = "2026-10-01T11:00:00+00:00"
    task = {"id": "task-1", "kind": "water"}
    if snapshot_source == "current":
        task.update(snapshot)
    else:
        task.update(
            title="Later owner title",
            occurrence_id="another-completion",
            revisions=[snapshot],
        )
    home = {"tasks": [task]}

    result = care_record(home, occurrence())

    assert result["title"] == "人工照护（历史名称未记录）"
    assert result.get("title_is_fallback") is False
    assert historical_title(home, occurrence()) == "人工照护（历史名称未记录）"
