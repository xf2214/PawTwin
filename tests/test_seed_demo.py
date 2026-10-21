"""Portable samples use real authenticated APIs against isolated SQLite storage."""

import importlib.util
import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed_demo.py"


@pytest.fixture
def seed(tmp_path, monkeypatch):
    assert SCRIPT.is_file(), "The portable demo importer is missing"
    spec = importlib.util.spec_from_file_location("seed_demo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "DATA_ROOT", tmp_path / "data")
    return module


class ApiOpener:
    """An urllib-shaped transport; every request still enters the real ASGI API."""

    def __init__(self, client):
        self.client = client
        self.writes = []
        self.interrupt_approval = False
        self.interrupt_event = None
        self.fail_event_checkpoint = False

    def open(self, request, timeout):
        path = urlsplit(request.full_url).path
        method = request.get_method()
        if self.fail_event_checkpoint and path == "/api/home/state":
            self.fail_event_checkpoint = False
            raise OSError("Interrupted event checkpoint")
        if self.interrupt_event == "before" and path == "/api/events":
            self.interrupt_event = None
            raise OSError("Interrupted before event submission")
        if self.interrupt_approval and path.endswith("/approval"):
            self.interrupt_approval = False
            raise OSError("Interrupted before approval")
        if method != "GET" and path != "/api/login":
            self.writes.append(path)
        response = self.client.request(
            method, path, content=request.data, headers=dict(request.header_items())
        )
        if response.status_code >= 400:
            raise HTTPError(request.full_url, response.status_code, "API rejected", {}, None)
        if path == "/api/events" and self.interrupt_event:
            interruption, self.interrupt_event = self.interrupt_event, None
            if interruption == "response":
                raise OSError("Interrupted after server accepted event")
            self.fail_event_checkpoint = True
        return io.BytesIO(response.content)


@pytest.fixture
def api(tmp_path, request):
    app = create_app(
        Settings(
            _env_file=None,
            database_path=str(tmp_path / "isolated.db"),
            model_backend="local_fake",
            family_model_backend="local_rules",
            memory_backend="not_implemented",
            worker_mode=getattr(request, "param", "inline"),
        )
    )
    with TestClient(app) as client:
        yield ApiOpener(client)


def run_seed(seed, api, state_dir, **kwargs):
    return seed.populate(seed.Client("http://127.0.0.1:8861", opener=api), state_dir, **kwargs)


def home(api):
    return api.client.get("/api/home/state").json()


def state(api):
    return api.client.get("/api/state").json()


@pytest.mark.parametrize("api", ["inline", "background"], indirect=True)
def test_fresh_sqlite_samples_and_completed_replay(seed, api):
    directory = seed.DATA_ROOT / "portable"
    result = run_seed(seed, api, directory)
    saved = home(api)
    workbench = state(api)
    assert result["fictional"] is True
    assert (
        result["day"]
        == datetime.now(UTC).astimezone(seed.ZoneInfo("Asia/Shanghai")).date().isoformat()
    )
    assert len(saved["pets"]) == 2
    assert len(saved["measurements"]) == 20
    assert {r["source"] for r in saved["measurements"]} == {"demo_sample"}
    assert all("Fictional" in r["note"] for r in saved["measurements"])
    assert len(saved["tasks"]) == 13
    assert len(saved["occurrences"]) == 5
    assert len(saved["diary"]) == 6
    assert len(saved["notes"]) == 4
    assert sum(m["status"] == "confirmed" for m in saved["memories"]) == 6
    assert sum(m["status"] == "candidate" for m in saved["memories"]) == 2
    assert sum(r["status"] == "current" for r in saved["reports"]) == 8
    assert sorted(r["state"] for r in workbench["runs"]) == [
        "blocked",
        "declined",
        "failed",
        "needs_info",
        "succeeded",
        "succeeded",
    ]
    assert all(r["receipt"]["simulated"] for r in workbench["runs"] if r.get("receipt"))
    assert workbench["facts"]["daily_dispensed_grams"] == 15
    assert len(workbench["feedback"]) == 3
    api.writes.clear()
    assert run_seed(seed, api, directory) == result
    assert api.writes == []
    assert home(api) == saved
    assert state(api)["facts"] == workbench["facts"]
    journal = (directory / "journal.json").read_text(encoding="utf-8")
    assert "csrf_token" not in journal and "passphrase" not in journal


@pytest.mark.parametrize("interruption", ["before", "response", "checkpoint"])
def test_saved_event_intent_recovers_without_duplicate_runs_or_changed_facts(
    seed, api, interruption
):
    directory = seed.DATA_ROOT / f"event-{interruption}"
    api.interrupt_event = interruption
    with pytest.raises(OSError, match="Interrupted"):
        run_seed(seed, api, directory)
    before = state(api)
    journal = json.loads((directory / "journal.json").read_text(encoding="utf-8"))
    intent = journal["runs"].get("approved-meal")
    assert intent and intent["event"]["event_id"]
    assert len(before["runs"]) == (0 if interruption == "before" else 1)
    api.writes.clear()
    result = run_seed(seed, api, directory)
    assert result["workbench_runs"] == 6
    expected_first = (
        "/api/events" if interruption == "before" else (f"/api/runs/{intent['run_id']}/approval")
    )
    assert api.writes[0] == expected_first
    after = state(api)
    recovered = next(r for r in after["runs"] if r["run_id"] == intent["run_id"])
    assert recovered["state"] == "succeeded"
    assert recovered["facts_version"] == before["facts"]["facts_version"]
    assert sum(r.get("receipt") is not None for r in after["runs"]) == 3
    assert after["facts"]["daily_dispensed_grams"] == 15


def test_interrupted_pending_approval_resumes_without_rewriting_its_facts(seed, api):
    directory = seed.DATA_ROOT / "interrupted"
    api.interrupt_approval = True
    with pytest.raises(OSError, match="Interrupted"):
        run_seed(seed, api, directory)
    before = state(api)
    assert [r["state"] for r in before["runs"]] == ["awaiting_approval"]
    facts_version = before["facts"]["facts_version"]
    api.writes.clear()
    run_seed(seed, api, directory)
    assert api.writes[0] == f"/api/runs/{before['runs'][0]['run_id']}/approval"
    run = next(r for r in state(api)["runs"] if r["run_id"] == before["runs"][0]["run_id"])
    assert run["state"] == "succeeded"
    assert run["facts_version"] == facts_version


@pytest.mark.parametrize("existing", ["note", "profile", "object", "workbench"])
def test_nonempty_or_edited_starter_is_rejected_before_business_writes(seed, api, existing):
    client = seed.Client("http://127.0.0.1:8861", opener=api)
    client.authenticate()
    if existing == "note":
        client.call(
            "/api/home/pets/mochi/notes", {"text": "Owner's real note", "scope": "observation"}
        )
    elif existing == "profile":
        profile = home(api)["pets"][0]
        client.call(
            "/api/home/pets/mochi",
            {
                **{k: v for k, v in profile.items() if k not in ("id", "source")},
                "name": "Owner's cat",
            },
            "PUT",
        )
    elif existing == "object":
        item = home(api)["objects"][0]
        client.call(
            f"/api/home/objects/{item['id']}",
            {
                **{k: v for k, v in item.items() if k not in ("id", "pet_id")},
                "name": "Owner's bed",
            },
            "PUT",
        )
    else:
        client.call(
            "/api/events",
            {
                "event_id": "461b7938-c975-4bc1-a7f4-68e5d2db93ab",
                "pet_id": "mochi",
                "kind": "food_request",
                "room": "kitchen",
                "source": "simulator",
            },
        )
    before, facts = home(api), state(api)["facts"]
    api.writes.clear()
    with pytest.raises(seed.SeedError, match="untouched|unrelated|empty"):
        run_seed(seed, api, seed.DATA_ROOT / "refused")
    assert api.writes == []
    assert home(api) == before and state(api)["facts"] == facts


def test_foreign_journal_is_rejected(seed, api):
    directory = seed.DATA_ROOT / "one"
    run_seed(seed, api, directory)
    journal_path = directory / "journal.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    journal["instance"] = "foreign-instance"
    journal_path.write_text(json.dumps(journal), encoding="utf-8")
    api.writes.clear()
    with pytest.raises(seed.SeedError, match="instance"):
        run_seed(seed, api, directory)
    assert api.writes == []


@pytest.mark.parametrize("edit", ["family", "run", "facts", "device"])
def test_post_seed_unrelated_changes_are_rejected_without_more_writes(seed, api, edit):
    directory = seed.DATA_ROOT / "changed"
    run_seed(seed, api, directory)
    client = seed.Client("http://127.0.0.1:8861", opener=api)
    client.authenticate()
    if edit == "family":
        client.call(
            "/api/home/pets/mochi/notes", {"text": "Owner-authored note", "scope": "observation"}
        )
    elif edit == "run":
        client.call(
            "/api/events",
            {
                "event_id": "a98bac76-6092-4c39-83e1-22348a144013",
                "pet_id": "mochi",
                "kind": "attention_request",
                "room": "living_room",
                "source": "simulator",
            },
        )
    elif edit == "facts":
        client.call("/api/demo/facts", {"last_fed_minutes_ago": 42})
    else:
        client.call("/api/demo/device-mode", {"mode": "failed"})
    before, facts = home(api), state(api)["facts"]
    api.writes.clear()
    with pytest.raises(seed.SeedError, match="unrelated|Unrelated|outside"):
        run_seed(seed, api, directory)
    assert api.writes == []
    assert home(api) == before and state(api)["facts"] == facts


def test_journal_cannot_be_reused_for_another_sqlite_instance(seed, api, tmp_path):
    directory = seed.DATA_ROOT / "bound"
    run_seed(seed, api, directory)
    app = create_app(Settings(_env_file=None, database_path=str(tmp_path / "another.db")))
    with TestClient(app) as client:
        other = ApiOpener(client)
        with pytest.raises(seed.SeedError, match="instance"):
            run_seed(seed, other, directory)
        assert other.writes == []
        assert len(home(other)["pets"]) == 1 and home(other)["tasks"] == []


def test_another_household_identity_is_rejected_before_business_writes(seed, api):
    response = api.client.post(
        "/api/family/register",
        json={
            "username": "portable-test-owner",
            "password": "portable-test-password",
            "display_name": "Actual owner",
        },
    )
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    response = api.client.post(
        "/api/family/households",
        json={
            "name": "Owner's household",
            "timezone": "Asia/Shanghai",
        },
        headers={"x-csrf-token": token},
    )
    assert response.status_code == 200
    client = seed.Client("http://127.0.0.1:8861", opener=api)
    client.csrf = token
    before = home(api)
    api.writes.clear()
    with pytest.raises(seed.SeedError, match="legacy-demo|HTTP 403"):
        seed.populate(client, seed.DATA_ROOT / "foreign-owner")
    assert api.writes == [] and home(api) == before


def test_incompatible_analyzer_is_rejected_without_mutation(seed, tmp_path):
    app = create_app(
        Settings(
            _env_file=None,
            database_path=str(tmp_path / "incompatible.db"),
            model_backend="inline",
        )
    )
    with TestClient(app) as test_client:
        incompatible = ApiOpener(test_client)
        with pytest.raises(seed.SeedError, match="Local rules"):
            run_seed(seed, incompatible, seed.DATA_ROOT / "incompatible")
        assert incompatible.writes == []


def test_saved_day_does_not_roll_forward_when_resuming(seed, api):
    directory = seed.DATA_ROOT / "day"
    now = datetime.now(UTC) - timedelta(days=1)
    server_before = datetime.now(UTC)
    result = run_seed(seed, api, directory, now=now)
    before = home(api)
    assert result["day"] == now.astimezone(seed.ZoneInfo("Asia/Shanghai")).date().isoformat()
    assert all(
        datetime.fromisoformat(row["completed_at"]) >= server_before
        for row in before["occurrences"]
    )
    api.writes.clear()
    assert run_seed(seed, api, directory, now=now + timedelta(days=1)) == result
    assert api.writes == [] and home(api) == before


def test_evening_pending_examples_stay_in_the_original_household_day(seed, api):
    now = (datetime.now(seed.ZoneInfo("Asia/Shanghai")) - timedelta(days=1)).replace(
        hour=22, minute=0, second=0, microsecond=0
    )
    directory = seed.DATA_ROOT / "evening"
    run_seed(seed, api, directory, now=now)
    saved = home(api)
    for pet in saved["pets"]:
        today = [
            task
            for task in saved["tasks"]
            if task["pet_id"] == pet["id"]
            and not task["completed"]
            and datetime.fromisoformat(task["due_at"]).date() == now.date()
        ]
        assert len(today) == 2
        assert sum(datetime.fromisoformat(task["due_at"]) < now for task in today) == 1
    api.writes.clear()
    run_seed(seed, api, directory, now=now + timedelta(days=1))
    assert api.writes == [] and home(api) == saved


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8861",
        "http://example.com:8861",
        "http://127.0.0.1:8861/api",
        "http://owner:password@127.0.0.1:8861",
        "http://127.0.0.1:8861/?query=1",
    ],
)
def test_nonlocal_or_ambiguous_url_is_rejected_without_contact(seed, url):
    with pytest.raises(seed.SeedError, match="loopback|URL"):
        seed.Client(url)


def test_state_directory_must_stay_under_ignored_data(seed, api, tmp_path):
    with pytest.raises(seed.SeedError, match="data"):
        run_seed(seed, api, tmp_path / "outside")
    assert api.writes == []


def test_atomic_journal_retries_transient_windows_file_lock(seed, tmp_path, monkeypatch):
    seeder = seed.Seeder.__new__(seed.Seeder)
    seeder.path = tmp_path / "journal.json"
    seeder.path.write_text('{"old": true}', encoding="utf-8")
    seeder.journal = {"new": True}
    original = Path.replace
    calls = []

    def temporarily_locked(path, target):
        calls.append(path)
        if len(calls) == 1:
            raise PermissionError("Temporary scanner lock")
        return original(path, target)

    monkeypatch.setattr(Path, "replace", temporarily_locked)
    seeder.save()
    assert len(calls) == 2
    assert json.loads(seeder.path.read_text(encoding="utf-8")) == {"new": True}


def test_atomic_journal_keeps_previous_file_when_lock_persists(seed, tmp_path, monkeypatch):
    seeder = seed.Seeder.__new__(seed.Seeder)
    seeder.path = tmp_path / "journal.json"
    previous = '{"old": true}'
    seeder.path.write_text(previous, encoding="utf-8")
    seeder.journal = {"new": True}

    def locked(path, target):
        raise PermissionError("Persistent lock")

    monkeypatch.setattr(Path, "replace", locked)
    with pytest.raises(PermissionError, match="Persistent lock"):
        seeder.save()
    assert seeder.path.read_text(encoding="utf-8") == previous
