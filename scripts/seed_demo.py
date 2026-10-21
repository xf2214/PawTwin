"""Populate an untouched local demo through authenticated APIs.

Start a separate service and fresh database first (see README). Example:
  uv run --frozen python scripts/seed_demo.py --base-url http://127.0.0.1:8861 \
      --state-dir data/portable-demo-state

No service is started, existing records are never cleared, and no database is
uploaded. Keep the state directory to resume/replay this particular instance.
Only the public default local demo passphrase is supported.
"""

import argparse
import hashlib
import http.cookiejar
import ipaddress
import json
import os
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

from pawtwin.repo_sqlite import _run_uuid

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
USER_ID = "00000000-0000-4000-8000-000000000001"
HOME_KEYS = (
    "pets",
    "members",
    "objects",
    "tasks",
    "notes",
    "diary",
    "history",
    "processed_actions",
    "legacy_members",
    "measurements",
    "memories",
    "proposals",
    "occurrences",
)
STARTER_PET = {
    "id": "mochi",
    "name": "Mochi",
    "species": "cat",
    "breed": "",
    "gender": "unknown",
    "birthday": None,
    "age_years": None,
    "coat": "gold",
    "pattern": "solid",
    "size": "medium",
    "likes": "",
    "dislikes": "",
    "photo_id": None,
    "source": "demo",
}
STARTER_OBJECTS = [
    ("nest", "窗边小窝", 19, 74, "初始展示物品，可修改"),
    ("toy", "羽毛棒", 38, 70, "初始展示物品，可修改"),
    ("feeder", "模拟喂食器", 82, 48, "模拟设备，不连接真实硬件"),
    ("water", "水碗", 81, 72, "初始展示物品，可修改"),
]
SCENARIOS = [
    (
        "approved-meal",
        "food_request",
        {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 0},
        "succeeded",
        "approve",
        "succeeded",
        "Owner approved a simulated 15 g meal.",
    ),
    (
        "recent-meal-block",
        "food_request",
        {"last_fed_minutes_ago": 10, "daily_dispensed_grams": 15},
        "succeeded",
        None,
        "blocked",
        "Recent feeding is blocked by the interval rule.",
    ),
    (
        "missing-feed-time",
        "food_request",
        {"clear": ["last_fed_minutes_ago"]},
        "succeeded",
        None,
        "needs_info",
        "A missing feeding time requires more information.",
    ),
    (
        "owner-declined",
        "food_request",
        {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
        "succeeded",
        "decline",
        "declined",
        "Owner declined the proposed meal.",
    ),
    (
        "device-failure",
        "food_request",
        {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
        "failed",
        "approve",
        "failed",
        "Simulated feeder failure adds no food.",
    ),
    (
        "approved-play",
        "attention_request",
        {"last_fed_minutes_ago": 360, "daily_dispensed_grams": 15},
        "succeeded",
        "approve",
        "succeeded",
        "Owner approved a simulated play session.",
    ),
]


class SeedError(RuntimeError):
    """An unsafe or incompatible target; no attempt is made to repair it."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SeedError("The local API must not redirect requests")


class Client:
    def __init__(self, base_url, *, opener=None):
        try:
            parsed = urlsplit(base_url)
            local = ipaddress.ip_address(parsed.hostname or "").is_loopback
            port = parsed.port
        except ValueError as exc:
            raise SeedError("Use an explicit HTTP loopback URL with a port") from exc
        if (
            parsed.scheme != "http"
            or not local
            or not port
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise SeedError(
                "Use an explicit HTTP loopback URL with a port and no path or credentials"
            )
        self.base_url = base_url.rstrip("/")
        self.opener = opener or urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            NoRedirect(),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )
        self.csrf = None
        self.after_write = None

    def call(self, path, body=None, method=None):
        method = method or ("GET" if body is None else "POST")
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        request = urllib.request.Request(
            self.base_url + path,
            None if body is None else json.dumps(body).encode(),
            headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SeedError(f"Local API rejected {method} {path} (HTTP {exc.code})") from None
        if method != "GET" and path != "/api/login" and self.after_write:
            self.after_write()
        return result

    def authenticate(self):
        status = self.call("/api/bootstrap")
        if status["mode"] != "local" or status["aws_connected"]:
            raise SeedError("Only a disconnected local service is supported")
        if not self.csrf:
            self.csrf = self.call("/api/login", {"passphrase": "local-demo-passphrase"})[
                "csrf_token"
            ]
        self.me = self.call("/api/family/me")

    def home(self):
        return self.call("/api/home/state")


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def business_home(home):
    # Reports are worker-managed projections; receipts follow workbench progress.
    return {key: home.get(key, []) for key in HOME_KEYS}


def check_local(client, state):
    me, services = client.me, client.call("/api/family/services")
    if (
        me["user"]["user_id"] != USER_ID
        or me["user"]["username"] != "legacy-demo"
        or (me.get("household") or {}).get("household_id") != "demo-owner"
        or (me.get("membership") or {}).get("role") != "admin"
        or me.get("cloud_authenticated")
    ):
        raise SeedError("Only the legacy-demo administrator in demo-owner is supported")
    if (
        state["mode"] != "local"
        or state["aws_connected"]
        or state["analyzer"] != "local_fake"
        or state["storage"] != "sqlite"
        or state["memory"] != "not_implemented"
        or services["assistant"]["backend"] != "local_rules"
        or services["device"] != "simulated"
        or services["photo_recognition"]["enabled"]
    ):
        raise SeedError("Local rules, disconnected SQLite and simulated devices are required")


def check_starter(client, home, state):
    if (
        home["pets"] != [STARTER_PET]
        or len(home["members"]) != 1
        or client.me["user"]["display_name"] != "主人"
        or client.me["household"]["name"] != "演示家庭"
        or client.me["membership"]["family_label"] != "主人"
        or home["members"][0]["user_id"] != USER_ID
    ):
        raise SeedError("An untouched starter demo household is required")
    objects = [
        (o["kind"], o["name"], o["x"], o["y"], o["note"])
        for o in home["objects"]
        if o["pet_id"] == "mochi"
    ]
    if len(home["objects"]) != 4 or sorted(objects) != sorted(STARTER_OBJECTS):
        raise SeedError("Only untouched starter objects are accepted")
    if (
        any(
            home.get(key)
            for key in HOME_KEYS
            if key not in ("pets", "members", "objects", "legacy_members")
        )
        or home.get("device_receipts")
        or state["runs"]
        or state["feedback"]
    ):
        raise SeedError(
            "An empty demo household and workbench are required; unrelated records exist"
        )
    facts = state["facts"]
    if (
        facts["facts_version"] != 0
        or facts["daily_dispensed_grams"] != 0
        or facts["last_fed_minutes_ago"] != 360
        or state["device_mode"] != "succeeded"
        or (
            facts["daily_limit_grams"],
            facts["single_serving_grams"],
            facts["minimum_interval_minutes"],
        )
        != (30, 15, 120)
    ):
        raise SeedError("An untouched workbench with default facts and limits is required")


class Seeder:
    def __init__(self, client, directory, now):
        self.client, self.directory = client, directory
        self.path = directory / "journal.json"
        client.authenticate()
        state, home = client.call("/api/state"), client.home()
        check_local(client, state)
        identity = {
            "url": client.base_url,
            "household": client.me["household"],
            "starter_objects": sorted(o["id"] for o in home["objects"] if o["pet_id"] == "mochi"),
        }
        instance = digest(identity)
        if self.path.exists():
            self.journal = json.loads(self.path.read_text(encoding="utf-8"))
            if self.journal.get("schema") != 1 or self.journal.get("instance") != instance:
                raise SeedError("Journal belongs to another instance or unsupported schema")
            if self.journal["home_digest"] != digest(business_home(home)):
                raise SeedError("Household changed outside this journal; refusing unrelated edits")
            known = {r["run_id"] for r in self.journal["runs"].values()}
            actual = {r["run_id"] for r in state["runs"]}
            unsubmitted = {
                r["run_id"]
                for r in self.journal["runs"].values()
                if r.get("event") and r.get("submitted") is False
            }
            if actual - known or known - actual - unsubmitted:
                raise SeedError("Unrelated or missing workbench runs; refusing to change facts")
            if (
                state["facts"] != self.journal["facts"]
                or state["feedback"] != self.journal["feedback"]
                or state["device_mode"] != self.journal["device_mode"]
            ):
                raise SeedError("Workbench changed outside this journal; manual review is required")
        else:
            if any(p.name != ".lock" for p in directory.iterdir()):
                raise SeedError("Use an empty state directory or its original journal")
            check_starter(client, home, state)
            zone = client.me["household"]["timezone"]
            started = (now or datetime.now(UTC)).astimezone(ZoneInfo(zone))
            self.journal = {
                "schema": 1,
                "instance": instance,
                "seed_id": str(uuid4()),
                "started_at": started.isoformat(),
                "day": started.date().isoformat(),
                "timezone": zone,
                "runs": {},
                "summary": None,
            }
            self.checkpoint()
        self.now = datetime.fromisoformat(self.journal["started_at"]).astimezone(
            ZoneInfo(self.journal["timezone"])
        )
        self.day = self.journal["day"]
        self.mark = f"[DEMO {self.day}]"
        client.after_write = self.checkpoint

    def save(self):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self.journal, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # Windows can briefly deny replacement while another process holds the
        # file. Keep atomic replacement and the previous journal on persistent errors.
        for attempt in range(6):
            try:
                temporary.replace(self.path)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.05 * 2**attempt)

    def checkpoint(self):
        self.journal["home_digest"] = digest(business_home(self.client.home()))
        state = self.client.call("/api/state")
        self.journal["facts"] = state["facts"]
        self.journal["feedback"] = state["feedback"]
        self.journal["device_mode"] = state["device_mode"]
        self.save()

    def event_id(self, key):
        return str(uuid5(NAMESPACE_URL, f"pawtwin:portable:{self.journal['seed_id']}:{key}"))

    def at(self, days, hour=9):
        sample = self.now.replace(hour=hour, minute=0, second=0, microsecond=0)
        return min(sample + timedelta(days=days), self.now - timedelta(minutes=10)).isoformat()

    def family(self):
        c = self.client
        mochi = c.home()["pets"][0]
        if not mochi.get("breed"):
            c.call(
                "/api/home/pets/mochi",
                {
                    **{k: v for k, v in mochi.items() if k not in ("id", "source")},
                    "breed": "Domestic shorthair (fictional demo)",
                    "gender": "male",
                    "birthday": (self.now.date() - timedelta(days=152)).isoformat(),
                    "birthday_estimated": False,
                    "neutered": False,
                    "pattern": "stripes",
                    "likes": "Feather wand and sunny window seat. Fictional demo profile.",
                    "dislikes": "Sudden noises. Fictional demo profile.",
                },
                "PUT",
            )
        miso = next((p for p in c.home()["pets"] if p["name"] == "Miso"), None)
        if miso is None:
            result = c.call(
                "/api/home/pets",
                {
                    "name": "Miso",
                    "species": "dog",
                    "breed": "Pembroke Welsh Corgi (fictional demo)",
                    "gender": "female",
                    "birthday": (self.now.date() - timedelta(days=799)).isoformat(),
                    "neutered": True,
                    "coat": "cream",
                    "pattern": "spots",
                    "size": "medium",
                    "likes": (
                        "Short sniff walks and chicken-flavoured lick mats. Fictional demo profile."
                    ),
                    "dislikes": "Busy roads. Fictional demo profile.",
                },
            )
            miso = next(p for p in result["pets"] if p["name"] == "Miso")
        pets = ["mochi", miso["id"]]
        for kind, name, x, y in [
            ("nest", "Miso's soft bed", 19, 74),
            ("toy", "Soft puzzle ball", 38, 70),
            ("water", "Miso's water bowl", 81, 72),
        ]:
            if not any(o["pet_id"] == pets[1] and o["name"] == name for o in c.home()["objects"]):
                c.call(
                    f"/api/home/pets/{pets[1]}/objects",
                    {
                        "kind": kind,
                        "name": name,
                        "x": x,
                        "y": y,
                        "note": f"{self.mark} Fictional item; no connected device.",
                    },
                )
        for pet, weights, offered, intake in [
            (pets[0], [1.96, 1.99, 2.02, 2.06, 2.08, 2.09, 2.10], 18, 16),
            (pets[1], [11.90, 11.88, 11.85, 11.86, 11.82, 11.81, 11.80], 140, 132),
        ]:
            samples = [
                ("weight", weight, "kg", None, offset)
                for offset, weight in zip([-14, -11, -8, -5, -2, -1, 0], weights, strict=True)
            ] + [
                ("diet", n, "g", kind, 0)
                for kind, n in (
                    ("food_offered", offered),
                    ("actual_intake", intake),
                    ("remaining", offered - intake),
                )
            ]
            for kind, value, unit, diet, offset in samples:
                note = f"{self.mark} Fictional {kind} sample; {diet or 'weight'}; day {offset:+d}."
                if any(r["pet_id"] == pet and r["note"] == note for r in c.home()["measurements"]):
                    continue
                body = {
                    "kind": kind,
                    "value": value,
                    "unit": unit,
                    "source": "demo_sample",
                    "measured_at": self.at(offset),
                    "note": note,
                }
                if diet:
                    body["diet_type"] = diet
                c.call(f"/api/family/pets/{pet}/measurements", body)
        self.care(pets)
        self.records(pets)
        return pets

    def care(self, pets):
        plans = [
            [
                ("water", "Refresh water bowl", -120, None, "complete"),
                ("play", "Feather-wand playtime", -90, None, "complete"),
                ("brush", "Gentle back brushing", -60, 3, "complete"),
                ("feeding", "Review the next manual meal", 120, None, "claim"),
                ("water", "Evening fresh water", 180, 1, None),
                ("clean", "Wash the window-bed cover", 1440, 7, None),
                ("nails", "Check claws before trimming", 2880, 14, None),
            ],
            [
                ("walk", "Short neighbourhood sniff walk", -90, None, "complete"),
                ("water", "Refill water after the walk", -60, None, "complete"),
                ("feeding", "Record dinner leftovers", 150, None, "claim"),
                ("walk", "Quiet evening walk", 210, 1, None),
                ("brush", "Short coat-brushing session", 1440, 3, None),
                ("bath", "Prepare towels for bath day", 4320, 30, None),
            ],
        ]
        c = self.client
        for pet, entries in zip(pets, plans, strict=True):
            for kind, label, minutes, interval, action in entries:
                title = label + " - Demo"
                day_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
                last_due = day_start + timedelta(days=1, seconds=-1)
                due = self.now + timedelta(minutes=minutes)
                if label in ("Evening fresh water", "Quiet evening walk"):
                    overdue_minutes = 15 if pet == "mochi" else 10
                    due = max(day_start, self.now - timedelta(minutes=overdue_minutes))
                elif label in ("Review the next manual meal", "Record dinner leftovers"):
                    pending_minutes = 30 if pet == "mochi" else 45
                    due = min(self.now + timedelta(minutes=pending_minutes), last_due)
                task = next(
                    (t for t in c.home()["tasks"] if t["pet_id"] == pet and t["title"] == title),
                    None,
                )
                if task is None:
                    result = c.call(
                        f"/api/home/pets/{pet}/tasks",
                        {
                            "kind": kind,
                            "title": title,
                            "due_at": due.isoformat(),
                            "interval_days": interval,
                            "assigned_to": USER_ID,
                        },
                    )
                    task = next(
                        t for t in result["tasks"] if t["pet_id"] == pet and t["title"] == title
                    )
                if (action == "complete" and not task.get("last_completed_at")) or (
                    action == "claim" and not task.get("claimed_by") and not task["completed"]
                ):
                    c.call(
                        f"/api/home/tasks/{task['id']}/action",
                        {
                            "event_id": self.event_id(f"{pet}:{title}:{action}"),
                            "version": task["version"],
                            "action": action,
                            "note": (
                                f"{self.mark} Fictional care; server records completion time."
                            ),
                        },
                    )

    def records(self, pets):
        preferences = [
            [
                ("play", "Prefers short feather-wand sessions near the window."),
                ("brush", "Start brushing on the back; avoid the belly."),
                ("handling", "Approach quietly and let Mochi initiate contact."),
                ("food_review", "May prefer a shallow bowl; needs owner confirmation."),
            ],
            [
                ("walk", "Enjoys short sniff walks on quiet paths."),
                ("reward", "Likes chicken-flavoured treats in a lick mat."),
                ("brush", "Prefers brief brushing with a soft brush."),
                ("toy_review", "May enjoy a puzzle ball; needs owner confirmation."),
            ],
        ]
        c = self.client
        for pet, entries in zip(pets, preferences, strict=True):
            for index, (topic, label) in enumerate(entries):
                text = f"{label} {self.mark} Fictional preference."
                record = next(
                    (m for m in c.home()["memories"] if m["pet_id"] == pet and m["text"] == text),
                    None,
                )
                if record is None:
                    record = c.call(
                        f"/api/family/pets/{pet}/memories",
                        {
                            "text": text,
                            "topic": topic,
                            "status": "candidate",
                        },
                    )
                if index < 3 and record["status"] == "candidate":
                    c.call(
                        f"/api/family/pets/{pet}/memories/{record['id']}",
                        {
                            "version": record["version"],
                            "status": "confirmed",
                        },
                        "PATCH",
                    )
            for days, title, text in [
                (-5, "A little routine begins", "Saved a first weight sample and quiet rest area."),
                (-1, "Yesterday's small moments", "Noted which play routine was preferred."),
                (0, "Today's care handoff", "Reviewed water and the next care tasks together."),
            ]:
                title += " - Demo"
                if not any(d["pet_id"] == pet and d["title"] == title for d in c.home()["diary"]):
                    c.call(
                        f"/api/home/pets/{pet}/diary",
                        {
                            "title": title,
                            "text": f"{text} {self.mark} Fictional household diary.",
                            "happened_on": (self.now.date() + timedelta(days=days)).isoformat(),
                        },
                    )
            for activity, label in [
                (
                    "general",
                    "Profile, weights, meals and care are fictional demonstration samples.",
                ),
                ("play" if pet == "mochi" else "walk", "Review confirmed preferences before care."),
            ]:
                text = f"{self.mark} {label}"
                if not any(n["pet_id"] == pet and n["text"] == text for n in c.home()["notes"]):
                    c.call(
                        f"/api/home/pets/{pet}/notes",
                        {
                            "text": text,
                            "scope": "observation",
                            "activity": activity,
                        },
                    )

    def workbench(self):
        c = self.client
        for slug, kind, facts, device, decision, expected, label in SCENARIOS:
            old = self.journal["runs"].get(slug)
            if old:
                present = any(r["run_id"] == old["run_id"] for r in c.call("/api/state")["runs"])
                if present:
                    run = c.call(f"/api/runs/{old['run_id']}")
                    if run["state"] == expected:
                        continue
                    if run["state"] not in (
                        "queued",
                        "analyzing",
                        "awaiting_approval",
                        "executing",
                    ):
                        raise SeedError(f"{slug}: saved run needs manual review")
                else:
                    # Only a journaled, never-acknowledged intent may be submitted.
                    # Its facts were captured before the first attempt; keep that version.
                    if not old.get("event") or old.get("submitted") is not False:
                        raise SeedError(f"{slug}: missing saved run requires manual review")
                    accepted = c.call("/api/events", old["event"])
                    if accepted["run_id"] != old["run_id"]:
                        raise SeedError("The local service uses an incompatible event identity")
                    old["submitted"] = True
                    self.save()
                    run = c.call(f"/api/runs/{old['run_id']}")
            else:
                c.call("/api/demo/facts", facts)
                event = {
                    "event_id": self.event_id(slug),
                    "pet_id": "mochi",
                    "kind": kind,
                    "room": "living_room" if kind == "attention_request" else "kitchen",
                    "source": "simulator",
                    "note": f"{self.mark} Fictional scenario: {label}",
                }
                # The repository's existing identity function lets the journal own
                # exactly this event even if its HTTP acknowledgement is lost.
                run_id = str(_run_uuid("demo-owner", UUID(event["event_id"])))
                self.journal["runs"][slug] = {
                    "run_id": run_id,
                    "expected": expected,
                    "event": event,
                    "submitted": False,
                }
                self.save()
                accepted = c.call("/api/events", event)
                if accepted["run_id"] != run_id:
                    raise SeedError("The local service uses an incompatible event identity")
                self.journal["runs"][slug]["submitted"] = True
                self.save()
                run = c.call(f"/api/runs/{run_id}")
            deadline = time.monotonic() + 30
            while run["state"] in ("queued", "analyzing", "executing"):
                if time.monotonic() >= deadline:
                    raise SeedError(f"{slug}: worker timed out; resume using the same journal")
                time.sleep(0.1)
                run = c.call(f"/api/runs/{run['run_id']}")
            if decision and run["state"] == "awaiting_approval":
                if c.call("/api/state")["device_mode"] != device:
                    c.call("/api/demo/device-mode", {"mode": device})
                # Reuse the saved proposal/facts version; never reinject facts on resume.
                run = c.call(
                    f"/api/runs/{run['run_id']}/approval",
                    {
                        "decision": decision,
                        "proposal_version": run["proposal_version"],
                        "action_digest": run["action_digest"],
                    },
                )
            if run["state"] != expected:
                raise SeedError(
                    f"{slug}: expected {expected}, got {run['state']}; manual review needed"
                )
            self.checkpoint()
        if c.call("/api/state")["device_mode"] != "succeeded":
            c.call("/api/demo/device-mode", {"mode": "succeeded"})
        for label in [
            "Review the amount and evidence before approving; all device receipts are simulated.",
            "Recent feeding is blocked; a missing feeding time requires more information.",
            "Mochi likes a feather wand. Saved feedback is a database record, not cloud memory.",
        ]:
            text = f"{self.mark} Fictional demo: {label}"
            if not any(f["text"] == text for f in c.call("/api/state")["feedback"]):
                c.call("/api/feedback", {"text": text, "scope": "observation"})

    def reports(self, pets):
        for pet in pets:
            for days, period in [(0, "daily"), (0, "weekly"), (-1, "daily"), (-7, "weekly")]:
                day = (self.now.date() + timedelta(days=days)).isoformat()
                if not any(
                    r["pet_id"] == pet
                    and r["date"] == day
                    and r["period"] == period
                    and r["status"] == "current"
                    for r in self.client.home()["reports"]
                ):
                    self.client.call(
                        f"/api/family/pets/{pet}/reports/generate",
                        {
                            "date": day,
                            "period": period,
                        },
                    )


def populate(client, state_dir, *, now=None):
    directory = Path(state_dir).resolve()
    if not directory.is_relative_to(DATA_ROOT.resolve()) or directory == DATA_ROOT.resolve():
        raise SeedError("State directory must be a subdirectory of this repository's ignored data/")
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SeedError(
            "State directory is locked; check that no other importer is running"
        ) from exc
    try:
        os.close(descriptor)
        seeder = Seeder(client, directory, now)
        if seeder.journal["summary"] is not None:
            return seeder.journal["summary"]
        pets = seeder.family()
        seeder.workbench()
        seeder.reports(pets)
        home, state = client.home(), client.call("/api/state")
        summary = {
            "fictional": True,
            "day": seeder.day,
            "household": "demo-owner",
            "pets": len(pets),
            "measurements": len(home["measurements"]),
            "care_plans": len(home["tasks"]),
            "manual_demo_completions": len(home["occurrences"]),
            "current_reports": sum(r["status"] == "current" for r in home["reports"]),
            "workbench_runs": len(state["runs"]),
        }
        seeder.journal["summary"] = summary
        seeder.checkpoint()
        return summary
    finally:
        client.after_write = None
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Separate local HTTP service, with port")
    parser.add_argument(
        "--state-dir", required=True, type=Path, help="New subdirectory beneath data/"
    )
    args = parser.parse_args()
    try:
        summary = populate(Client(args.base_url), args.state_dir)
    except (SeedError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Demo import stopped: {exc}\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
