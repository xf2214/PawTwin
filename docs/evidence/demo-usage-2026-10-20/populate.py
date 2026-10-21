"""Same-day, explicitly fictional usage samples for the named local preview.

Uses normal authenticated APIs only. No credentials, cookies or CSRF tokens are
saved. Replays preserve existing records and skip already completed scenarios.
Run from the repository: uv run --frozen python <this file> --date 2026-10-20
The two databases must be backed up before the first execution.
"""

import argparse
import hashlib
import http.cookiejar
import json
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
ZONE = ZoneInfo("Asia/Shanghai")
DAY = "2026-10-20"
MARK = f"[DEMO {DAY}]"
FIELDS = (
    "name",
    "species",
    "breed",
    "gender",
    "birthday",
    "birthday_estimated",
    "neutered",
    "expected_adult_weight_kg",
    "age_years",
    "coat",
    "pattern",
    "size",
    "likes",
    "dislikes",
    "photo_id",
)


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = None
        status = self.call("/api/bootstrap")
        if status["mode"] != "local" or status["aws_connected"]:
            raise RuntimeError("This fixture only supports the local, disconnected preview")
        self.csrf = self.call("/api/login", {"passphrase": "local-demo-passphrase"})["csrf_token"]
        self.me = self.call("/api/family/me")
        if (
            self.me["user"]["username"],
            self.me["household"]["household_id"],
            self.me["membership"]["role"],
        ) != ("legacy-demo", "demo-owner", "admin"):
            raise RuntimeError("Unexpected household: refusing writes")
        state = self.call("/api/state")
        services = self.call("/api/family/services")
        if (
            state["analyzer"] != "local_fake"
            or state["storage"] != "sqlite"
            or state["memory"] != "not_implemented"
            or services["assistant"]["backend"] != "local_rules"
            or services["device"] != "simulated"
        ):
            raise RuntimeError("Local rules, SQLite and simulated devices are required")

    def call(self, path, body=None, method=None):
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        req = urllib.request.Request(
            "http://127.0.0.1:8000" + path,
            None if body is None else json.dumps(body).encode(),
            headers,
            method=method or ("GET" if body is None else "POST"),
        )
        with self.opener.open(req, timeout=30) as response:
            return json.load(response)

    def home(self):
        return self.call("/api/home/state")


def at(offset, hour=9):
    now = datetime.now(ZONE)
    value = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=offset)
    return min(value, now - timedelta(minutes=10)).isoformat()


def family(client):
    home = client.home()
    if not (ROOT / "before.json").exists():
        save("before.json", {"home": home, "workbench": client.call("/api/state")})
    mochi = next(p for p in home["pets"] if p["id"] == "mochi")
    # Fill only an untouched starter profile. Preserve any authored profile.
    if mochi.get("source") == "demo" and not mochi.get("breed") and not mochi.get("likes"):
        profile = {k: mochi.get(k) for k in FIELDS if k in mochi}
        profile.update(
            breed="Domestic shorthair (fictional demo)",
            gender="male",
            birthday="2026-05-21",
            birthday_estimated=False,
            neutered=False,
            pattern="stripes",
            likes="Feather wand, sunny window seat. Fictional demo profile.",
            dislikes="Sudden noises and being picked up. Fictional demo profile.",
        )
        client.call("/api/home/pets/mochi", profile, "PUT")
    home = client.home()
    miso = next(
        (
            p
            for p in home["pets"]
            if p["name"] == "Miso" and "Fictional demo profile" in p.get("likes", "")
        ),
        None,
    )
    if miso is None:
        home = client.call(
            "/api/home/pets",
            {
                "name": "Miso",
                "species": "dog",
                "breed": "Pembroke Welsh Corgi (fictional demo)",
                "gender": "female",
                "birthday": "2024-08-12",
                "neutered": True,
                "coat": "cream",
                "pattern": "spots",
                "size": "medium",
                "likes": (
                    "Short sniff walks and a chicken-flavoured lick mat. Fictional demo profile."
                ),
                "dislikes": "Busy roads and long brushing sessions. Fictional demo profile.",
            },
        )
        miso = next(
            p
            for p in home["pets"]
            if p["name"] == "Miso" and "Fictional demo profile" in p.get("likes", "")
        )
    pets = ["mochi", miso["id"]]
    for kind, name, x, y in [
        ("nest", "Miso's soft bed", 19, 74),
        ("toy", "Soft puzzle ball", 38, 70),
        ("water", "Miso's water bowl", 81, 72),
    ]:
        if not any(
            o["pet_id"] == miso["id"] and o["name"] == name for o in client.home()["objects"]
        ):
            client.call(
                f"/api/home/pets/{miso['id']}/objects",
                {
                    "kind": kind,
                    "name": name,
                    "x": x,
                    "y": y,
                    "note": f"{MARK} Fictional household item; no connected device.",
                },
            )
    for pet_id, weights, offered, intake in [
        ("mochi", [1.96, 1.99, 2.02, 2.06, 2.08, 2.09, 2.10], 18, 16),
        (miso["id"], [11.90, 11.88, 11.85, 11.86, 11.82, 11.81, 11.80], 140, 132),
    ]:
        records = client.call(f"/api/family/pets/{pet_id}/measurements")["records"]
        samples = [
            ("weight", value, "kg", None, offset, 9)
            for offset, value in zip([-14, -11, -8, -5, -2, -1, 0], weights, strict=True)
        ] + [
            ("diet", value, "g", kind, 0, 10)
            for kind, value in [
                ("food_offered", offered),
                ("actual_intake", intake),
                ("remaining", offered - intake),
            ]
        ]
        for kind, value, unit, diet_type, offset, hour in samples:
            note = f"{MARK} Fictional {kind} sample; {diet_type or 'weight'}; day {offset:+d}."
            if any(r.get("note") == note for r in records):
                continue
            body = {
                "kind": kind,
                "value": value,
                "unit": unit,
                "measured_at": at(offset, hour),
                "source": "demo_sample",
                "note": note,
            }
            if diet_type:
                body["diet_type"] = diet_type
            client.call(f"/api/family/pets/{pet_id}/measurements", body)
    now = datetime.now(ZONE)
    plans = {
        "mochi": [
            ("water", "Refresh water bowl", -120, None, "complete"),
            ("play", "Feather-wand playtime", -90, None, "complete"),
            ("brush", "Gentle back brushing", -60, 3, "complete"),
            ("feeding", "Review the next manual meal", 120, None, "claim"),
            ("water", "Evening fresh water", 180, 1, None),
            ("clean", "Wash the window-bed cover", 1440, 7, None),
            ("nails", "Check claws before trimming", 2880, 14, None),
        ],
        miso["id"]: [
            ("walk", "Short neighbourhood sniff walk", -90, None, "complete"),
            ("water", "Refill water after the walk", -60, None, "complete"),
            ("feeding", "Record dinner leftovers", 150, None, "claim"),
            ("walk", "Quiet evening walk", 210, 1, None),
            ("brush", "Short coat-brushing session", 1440, 3, None),
            ("bath", "Prepare towels for bath day", 4320, 30, None),
        ],
    }
    for pet_id, entries in plans.items():
        for kind, label, minutes, interval, action in entries:
            title = label + " - Demo"
            # Keep today's pending and overdue examples visible even in an evening demo.
            evening = {
                "Review the next manual meal": "22:40",
                "Evening fresh water": "22:00",
                "Record dinner leftovers": "22:45",
                "Quiet evening walk": "22:10",
            }
            due = (
                datetime.fromisoformat(f"{DAY}T{evening[label]}:00+08:00")
                if label in evening
                else now + timedelta(minutes=minutes)
            )
            home = client.home()
            task = next(
                (t for t in home["tasks"] if t["pet_id"] == pet_id and t["title"] == title), None
            )
            if task is None:
                home = client.call(
                    f"/api/home/pets/{pet_id}/tasks",
                    {
                        "kind": kind,
                        "title": title,
                        "due_at": due.isoformat(),
                        "interval_days": interval,
                        "assigned_to": client.me["user"]["user_id"],
                    },
                )
                task = next(
                    t for t in home["tasks"] if t["pet_id"] == pet_id and t["title"] == title
                )
            if label in evening and datetime.fromisoformat(task["due_at"]) != due:
                home = client.call(
                    f"/api/home/tasks/{task['id']}/action",
                    {
                        "event_id": str(uuid4()),
                        "version": task["version"],
                        "action": "edit",
                        "next_due": due.isoformat(),
                    },
                )
                task = next(t for t in home["tasks"] if t["id"] == task["id"])
            if (action == "complete" and not task.get("last_completed_at")) or (
                action == "claim" and not task.get("claimed_by") and not task["completed"]
            ):
                client.call(
                    f"/api/home/tasks/{task['id']}/action",
                    {
                        "event_id": str(uuid4()),
                        "version": task["version"],
                        "action": action,
                        "note": (
                            f"{MARK} Fictional manual-care replay; "
                            "completion time is recorded by the server."
                        ),
                    },
                )
    preferences = {
        "mochi": [
            ("play", "Prefers short feather-wand sessions near the window.", "confirmed"),
            ("brush", "Start brushing on the back; avoid the belly.", "confirmed"),
            ("handling", "Approach quietly and let Mochi initiate contact.", "confirmed"),
            (
                "food_review",
                "May prefer a shallow food bowl; needs owner confirmation.",
                "candidate",
            ),
        ],
        miso["id"]: [
            ("walk", "Enjoys short sniff walks on quiet paths.", "confirmed"),
            ("reward", "Likes chicken-flavoured treats in a lick mat.", "confirmed"),
            ("brush", "Prefers brief brushing with a soft brush.", "confirmed"),
            ("toy_review", "May enjoy a soft puzzle ball; needs owner confirmation.", "candidate"),
        ],
    }
    for pet_id, entries in preferences.items():
        for topic, label, status in entries:
            text = f"{label} {MARK} Fictional preference."
            memories = client.call(f"/api/family/pets/{pet_id}/memories")["memories"]
            record = next((m for m in memories if m["text"] == text), None)
            if record is None:
                record = client.call(
                    f"/api/family/pets/{pet_id}/memories",
                    {
                        "text": text,
                        "topic": topic,
                        "status": "candidate",
                    },
                )
            if status == "confirmed" and record["status"] == "candidate":
                client.call(
                    f"/api/family/pets/{pet_id}/memories/{record['id']}",
                    {
                        "version": record["version"],
                        "status": "confirmed",
                    },
                    "PATCH",
                )
        for offset, label, text in [
            (
                -5,
                "A little routine begins",
                "Saved a first weight sample and prepared a quiet rest area.",
            ),
            (
                -1,
                "Yesterday's small moments",
                "Spent time together and noted which play routine was preferred.",
            ),
            (
                0,
                "Today's care handoff",
                "Reviewed water, play or walking, and the next care tasks together.",
            ),
        ]:
            title = label + " - Demo"
            if not any(
                d["pet_id"] == pet_id and d["title"] == title for d in client.home()["diary"]
            ):
                client.call(
                    f"/api/home/pets/{pet_id}/diary",
                    {
                        "title": title,
                        "text": f"{text} {MARK} Fictional household diary.",
                        "happened_on": (now.date() + timedelta(days=offset)).isoformat(),
                    },
                )
        for scope, activity, label in [
            (
                "observation",
                "general",
                "Profile, weights, meals and care records are fictional demonstration samples.",
            ),
            (
                "observation",
                "play" if pet_id == "mochi" else "walk",
                "Use the confirmed preference cards to prepare the next shared care session.",
            ),
        ]:
            text = f"{MARK} {label}"
            prior = next(
                (n for n in client.home()["notes"] if n["pet_id"] == pet_id and n["text"] == text),
                None,
            )
            if prior and prior["scope"] == "preference":
                client.call(
                    f"/api/family/pets/{pet_id}/notes/{prior['id']}",
                    {
                        "version": prior["version"],
                        "text": text,
                        "scope": scope,
                        "activity": activity,
                    },
                    "PATCH",
                )
            if not any(n["pet_id"] == pet_id and n["text"] == text for n in client.home()["notes"]):
                client.call(
                    f"/api/home/pets/{pet_id}/notes",
                    {
                        "text": text,
                        "scope": scope,
                        "activity": activity,
                    },
                )
    return pets


def workbench(client):
    journal_path = ROOT / "workbench.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8")) if journal_path.exists() else {}
    state = client.call("/api/state")
    known = {item["run_id"] for item in journal.values()}
    if any(r["run_id"] not in known for r in state["runs"]):
        raise RuntimeError("Unrelated workbench runs exist; refusing to change their facts")
    scenarios = [
        (
            "approved-meal",
            "food_request",
            {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 0},
            "succeeded",
            "approve",
            "succeeded",
            "Owner reviewed and approved a simulated 15 g meal.",
        ),
        (
            "recent-meal-block",
            "food_request",
            {"last_fed_minutes_ago": 10, "daily_dispensed_grams": 15},
            "succeeded",
            None,
            "blocked",
            "A second request soon after feeding is stopped by the interval rule.",
        ),
        (
            "missing-feed-time",
            "food_request",
            {"clear": ["last_fed_minutes_ago"]},
            "succeeded",
            None,
            "needs_info",
            "The last feeding time is missing, so the system asks for more information.",
        ),
        (
            "owner-declined",
            "food_request",
            {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
            "succeeded",
            "decline",
            "declined",
            "Owner chooses to review the manual meal plan instead.",
        ),
        (
            "device-failure",
            "food_request",
            {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
            "failed",
            "approve",
            "failed",
            "Simulated feeder failure produces a failed receipt without adding food.",
        ),
        (
            "approved-play",
            "attention_request",
            {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
            "succeeded",
            "approve",
            "succeeded",
            "An attention request becomes an owner-approved simulated play task.",
        ),
    ]
    for slug, kind, facts, device, decision, expected, label in scenarios:
        old = journal.get(slug)
        if old:
            run = client.call(f"/api/runs/{old['run_id']}")
            if run["state"] == expected:
                continue
            if run["state"] not in ("queued", "analyzing", "awaiting_approval", "executing"):
                raise RuntimeError(f"{slug}: saved scenario requires manual review")
            # Keep the existing proposal's facts version intact when resuming.
            event = old
        else:
            client.call("/api/demo/facts", facts)
            event = client.call(
                "/api/events",
                {
                    "event_id": str(uuid5(NAMESPACE_URL, f"pawtwin:usage:{DAY}:{slug}")),
                    "pet_id": "mochi",
                    "kind": kind,
                    "room": "living_room" if kind == "attention_request" else "kitchen",
                    "source": "simulator",
                    "note": f"{MARK} {label}",
                },
            )
            journal[slug] = {"run_id": event["run_id"], "expected": expected, "scenario": label}
            save("workbench.json", journal)
        deadline = time.monotonic() + 30
        while True:
            run = client.call(f"/api/runs/{event['run_id']}")
            if run["state"] not in ("queued", "analyzing", "executing"):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Timed out waiting for {slug}")
            time.sleep(0.2)
        if decision:
            if run["state"] != "awaiting_approval":
                raise RuntimeError(f"{slug}: expected reviewable proposal, got {run['state']}")
            client.call("/api/demo/device-mode", {"mode": device})
            run = client.call(
                f"/api/runs/{run['run_id']}/approval",
                {
                    "decision": decision,
                    "proposal_version": run["proposal_version"],
                    "action_digest": run["action_digest"],
                },
            )
        if run["state"] != expected:
            raise RuntimeError(f"{slug}: expected {expected}, got {run['state']}")
    # Leave a usable simulator. No unknown food receipt/reservation is generated.
    if client.call("/api/state")["device_mode"] != "succeeded":
        client.call("/api/demo/device-mode", {"mode": "succeeded"})
    existing = client.call("/api/state")["feedback"]
    for label in [
        (
            "Meal approval: review the amount and evidence before confirming; "
            "all device receipts here are simulated."
        ),
        (
            "Safety review: recent feeding is blocked; "
            "a missing feeding time requires more information."
        ),
        (
            "Care handoff: Mochi likes a feather wand. "
            "Saved feedback is a database record, not cloud-extracted memory."
        ),
    ]:
        text = f"{MARK} {label}"
        if not any(f["text"] == text for f in existing):
            client.call("/api/feedback", {"text": text, "scope": "observation"})


def reports(client, pets):
    home = client.home()
    for pet_id in pets:
        for offset, period in [(0, "daily"), (0, "weekly"), (-1, "daily"), (-7, "weekly")]:
            date = (datetime.now(ZONE).date() + timedelta(days=offset)).isoformat()
            if not any(
                r["pet_id"] == pet_id
                and r["date"] == date
                and r["period"] == period
                and r["status"] == "current"
                for r in home["reports"]
            ):
                client.call(
                    f"/api/family/pets/{pet_id}/reports/generate", {"period": period, "date": date}
                )


def verify(client, pets):
    home = client.home()
    state = client.call("/api/state")
    before = json.loads((ROOT / "before.json").read_text(encoding="utf-8"))["home"]
    for key in (
        "pets",
        "objects",
        "tasks",
        "notes",
        "diary",
        "measurements",
        "memories",
        "occurrences",
    ):
        assert {r["id"] for r in before.get(key, [])} <= {r["id"] for r in home.get(key, [])}, key
    for pet_id in pets:
        weights = [
            r
            for r in home["measurements"]
            if r["pet_id"] == pet_id and MARK in r["note"] and r["kind"] == "weight"
        ]
        assert len(weights) == 7 and all(r["source"] == "demo_sample" for r in weights)
        confirmed = [
            m
            for m in home["memories"]
            if m["pet_id"] == pet_id and MARK in m["text"] and m["status"] == "confirmed"
        ]
        assert len(confirmed) == 3
        ctx = client.call(f"/api/family/pets/{pet_id}/context")
        assert not ctx["unresolved_conflicts"]
        save(f"context-{pet_id}.json", ctx)
    journal = json.loads((ROOT / "workbench.json").read_text(encoding="utf-8"))
    assert len(journal) == 6
    for item in journal.values():
        run = next(r for r in state["runs"] if r["run_id"] == item["run_id"])
        assert run["state"] == item["expected"]
        if run.get("receipt"):
            assert run["receipt"]["simulated"] is True
    seeded = [t for t in home["tasks"] if t["title"].endswith(" - Demo")]
    assert len(seeded) == 13
    assert len([o for o in home["occurrences"] if o["task_id"] in {t["id"] for t in seeded}]) == 5
    assert state["facts"]["daily_limit_grams"] == 30
    assert state["facts"]["single_serving_grams"] == 15
    assert state["facts"]["minimum_interval_minutes"] == 120
    assert state["facts"]["daily_dispensed_grams"] == 15
    assert state["device_mode"] == "succeeded"
    summary = {
        "date": DAY,
        "fictional": True,
        "household": "demo-owner",
        "pets": len(pets),
        "measurements": len(home["measurements"]),
        "care_plans": len(seeded),
        "manual_demo_completions": 5,
        "diary": len(home["diary"]),
        "notes": len(home["notes"]),
        "confirmed_preferences": sum(m["status"] == "confirmed" for m in home["memories"]),
        "candidate_preferences": sum(m["status"] == "candidate" for m in home["memories"]),
        "current_reports": sum(r["status"] == "current" for r in home["reports"]),
        "retained_report_versions": len(home["reports"]),
        "workbench_runs": len(state["runs"]),
        "workbench_feedback": len(state["feedback"]),
        "original_record_ids_preserved": True,
    }
    save("after.json", {"home": home, "workbench": state})
    save("verification.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, choices=[DAY])
    args = parser.parse_args()
    if datetime.now(ZONE).date().isoformat() != args.date:
        raise SystemExit("This fixture is restricted to its named client day")
    backup = ROOT.parents[3] / "PawTwin-before-usage-demo-2026-10-20" / "manifest.json"
    if not backup.is_file():
        raise SystemExit("Create the named two-database backup before populating")
    for item in json.loads(backup.read_text(encoding="utf-8")):
        if hashlib.sha256(Path(item["backup"]).read_bytes()).hexdigest() != item["sha256"]:
            raise SystemExit("Backup integrity check failed")
    client = Client()
    pets = family(client)
    workbench(client)
    reports(client, pets)
    verify(client, pets)
