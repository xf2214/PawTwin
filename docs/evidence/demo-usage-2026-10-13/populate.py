"""Populate only the explicitly named local demo identities through existing APIs.

This is a same-day 2026-10-13 fixture, not an app startup hook. Existing records stay
in place. Dates, measurements, care completion and preferences are fictional.
Session cookies and CSRF tokens remain in memory and are never written to disk.
"""

import argparse
import http.cookiejar
import json
import os
import urllib.request
from datetime import datetime, time, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parent
TARGETS = {
    "legacy-8807": (8807, "legacy-demo", "demo-owner"),
    "legacy-8834": (8834, "legacy-demo", "demo-owner"),
    "family-8834": (8834, "workspace-preview-20261013", "066657a2-ea49-46c5-b621-9fbf6509ad66"),
}
PROFILE_FIELDS = (
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


class Client:
    def __init__(self, target):
        port, username, household = TARGETS[target]
        self.base = f"http://127.0.0.1:{port}"
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.csrf = None
        bootstrap = self.call("/api/bootstrap")
        if bootstrap["mode"] != "local" or bootstrap["aws_connected"]:
            raise RuntimeError("Only the named local demo is supported")
        if username == "legacy-demo":
            self.call(
                "/api/login",
                {"passphrase": os.getenv("PAWTWIN_DEMO_PASSPHRASE", "local-demo-passphrase")},
            )
        else:
            self.call(
                "/api/family/login",
                {
                    "username": username,
                    "password": os.getenv("PAWTWIN_PREVIEW_PASSWORD", "local-preview-password"),
                },
            )
        self.me = self.call("/api/family/me")
        if (
            self.me["user"]["username"] != username
            or self.me["household"]["household_id"] != household
        ):
            raise RuntimeError("Refusing to modify a different account or household")
        if self.me["membership"]["role"] != "admin":
            raise RuntimeError("Expected the demo household administrator")
        self.csrf = self.me["csrf_token"]
        # The older :8807 preview predates this status route. This fixture only
        # calls storage/report APIs and never calls chat, models or devices.
        routes = self.call("/openapi.json")["paths"]
        if "/api/family/services" in routes:
            services = self.call("/api/family/services")
            if services["assistant"]["backend"] != "local_rules":
                raise RuntimeError("Expected the local-rule preview configuration")

    def call(self, route, body=None, method=None):
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        request = urllib.request.Request(
            self.base + route,
            None if body is None else json.dumps(body, ensure_ascii=False).encode(),
            headers,
            method=method or ("GET" if body is None else "POST"),
        )
        with self.opener.open(request, timeout=30) as response:
            return json.load(response)

    def home(self):
        return self.call("/api/home/state")


def populate(target, day):
    client = Client(target)
    marker = f"[演示使用记录 {day.isoformat()}]"
    home = client.home()
    # Versioned snapshots contain only this demo household, without auth data.
    before = ROOT / f"{target}-before.json"
    if not before.exists():
        before.write_text(json.dumps(home, ensure_ascii=False, indent=2), encoding="utf-8")
    completed = any(
        note["text"] == marker + " 档案、成长、照护与偏好均为虚构样例。" for note in home["notes"]
    )
    if not completed:
        pet = next(pet for pet in home["pets"] if pet["id"] == "mochi")
        profile = {key: pet.get(key) for key in PROFILE_FIELDS}
        profile.update(
            {
                "name": "Mochi",
                "species": "cat",
                "breed": "中华田园猫（虚构演示）",
                "gender": "male",
                "birthday": "2026-05-21",
                "birthday_estimated": False,
                "neutered": False,
                "expected_adult_weight_kg": None,
                "age_years": None,
                "coat": "gold",
                "pattern": "stripes",
                "size": "medium",
                "likes": "羽毛棒、安静的窗边陪玩（演示设定）",
                "dislikes": "突然的响声、强行抱起（演示设定）",
            }
        )
        client.call("/api/home/pets/mochi", profile, "PUT")
        if client.me["household"]["household_id"] == "demo-owner":
            client.call(
                "/api/family/household",
                {"name": "Mochi 的虚构演示家庭", "timezone": "Asia/Shanghai"},
                "PATCH",
            )

        def at(offset, hour=9, minute=0):
            return datetime.combine(
                day + timedelta(days=offset), time(hour, minute), ZONE
            ).isoformat()

        existing = client.call("/api/family/pets/mochi/measurements")["records"]
        for offset, weight in [
            (-14, 1.96),
            (-11, 1.99),
            (-8, 2.02),
            (-5, 2.06),
            (-2, 2.08),
            (-1, 2.09),
            (0, 2.10),
        ]:
            note = f"{marker} 体重样本 {offset:+d}天；虚构数据，不代表真实宠物测量。"
            if not any(record.get("note") == note for record in existing):
                client.call(
                    "/api/family/pets/mochi/measurements",
                    {
                        "kind": "weight",
                        "value": weight,
                        "unit": "kg",
                        "measured_at": at(offset),
                        "source": "demo_sample",
                        "note": note,
                    },
                )
        for kind, amount in [("food_offered", 48), ("actual_intake", 44), ("remaining", 4)]:
            note = f"{marker} 饮食样本 {kind}；虚构干粮记录，仅用于展示不同记录含义。"
            if not any(record.get("note") == note for record in existing):
                client.call(
                    "/api/family/pets/mochi/measurements",
                    {
                        "kind": "diet",
                        "value": amount,
                        "unit": "g",
                        "measured_at": at(0, 12),
                        "source": "demo_sample",
                        "diet_type": kind,
                        "note": note,
                    },
                )

        now = datetime.now(ZONE)
        later = datetime.combine(day, time(23, 30), ZONE)
        if later <= now:
            later += timedelta(days=1)
        routines = [
            ("water", "晨间换水 · 演示", at(0, 9), None, "complete"),
            ("play", "羽毛棒陪玩 · 演示", at(0, 10), None, "complete"),
            ("brush", "本次梳毛 · 演示", at(0, 11), 3, "complete"),
            ("feeding", "下一次人工喂食 · 演示", later.isoformat(), None, "claim"),
            ("water", "睡前换水 · 演示", (later + timedelta(minutes=20)).isoformat(), 1, None),
            ("clean", "周末整理猫窝 · 演示", at((5 - day.weekday()) % 7 or 7, 10), 7, None),
        ]
        for kind, title, due_at, interval_days, action in routines:
            home = client.home()
            task = next(
                (
                    task
                    for task in home["tasks"]
                    if task["pet_id"] == "mochi" and task["title"] == title
                ),
                None,
            )
            if task is None:
                home = client.call(
                    "/api/home/pets/mochi/tasks",
                    {
                        "kind": kind,
                        "title": title,
                        "due_at": due_at,
                        "interval_days": interval_days,
                        "assigned_to": client.me["user"]["user_id"],
                    },
                )
                task = next(task for task in home["tasks"] if task["title"] == title)
            if action == "complete" and not task.get("last_completed_at"):
                client.call(
                    f"/api/home/tasks/{task['id']}/action",
                    {
                        "event_id": str(uuid4()),
                        "version": task["version"],
                        "action": action,
                        "note": "虚构使用记录；仅记录演示人工完成，不触发设备。",
                    },
                )
            elif action == "claim" and not task.get("claimed_by") and not task["completed"]:
                client.call(
                    f"/api/home/tasks/{task['id']}/action",
                    {"event_id": str(uuid4()), "version": task["version"], "action": action},
                )

        memories = client.call("/api/family/pets/mochi/memories")["memories"]
        for topic, text in [
            ("play", "更喜欢羽毛棒，适合短时间分段陪玩。（虚构演示偏好）"),
            ("brush", "梳毛时先从背部开始，不喜欢碰腹部。（虚构演示偏好）"),
            ("general", "不喜欢突然的大声响，互动时保持安静。（虚构演示偏好）"),
        ]:
            record = next((record for record in memories if record["text"] == text), None)
            if record is None:
                record = client.call(
                    "/api/family/pets/mochi/memories",
                    {"text": text, "topic": topic, "status": "candidate"},
                )
            if record["status"] != "confirmed":
                client.call(
                    f"/api/family/pets/mochi/memories/{record['id']}",
                    {"version": record["version"], "status": "confirmed"},
                    "PATCH",
                )
        home = client.home()
        preference = "羽毛棒是常用陪玩玩具；饭后先休息再互动。（虚构演示设定）"
        if not any(note["text"] == preference for note in home["notes"]):
            client.call(
                "/api/home/pets/mochi/notes",
                {"text": preference, "scope": "preference", "activity": "play"},
            )
        for offset, title, text in [
            (-1, "窗边的午后 · 演示", "一起待在窗边，记录今天的陪伴。此条为虚构日记示例。"),
            (
                0,
                "换水与羽毛棒 · 演示",
                "整理水碗后陪玩一会儿，把完成照护和日常观察一起记下来。此条为虚构日记示例。",
            ),
        ]:
            if not any(entry["title"] == title for entry in home["diary"]):
                client.call(
                    "/api/home/pets/mochi/diary",
                    {
                        "title": title,
                        "text": text,
                        "happened_on": (day + timedelta(days=offset)).isoformat(),
                    },
                )
        client.call(
            "/api/home/pets/mochi/notes",
            {
                "text": marker + " 档案、成长、照护与偏好均为虚构样例。",
                "scope": "observation",
                "activity": "general",
            },
        )

    # Reports are calculated by the shipped backend; no prepared report text.
    reports = []
    for offset, period in [(0, "daily"), (0, "weekly"), (-1, "daily"), (-2, "weekly")]:
        reports.append(
            client.call(
                "/api/family/pets/mochi/reports/generate",
                {"period": period, "date": (day + timedelta(days=offset)).isoformat()},
            )
        )
    home = client.home()
    measures = client.call("/api/family/pets/mochi/measurements")["records"]
    memories = client.call("/api/family/pets/mochi/memories")["memories"]
    context = client.call("/api/family/pets/mochi/context")
    weights = [
        record
        for record in measures
        if record["kind"] == "weight" and marker in record.get("note", "")
    ]
    if len(weights) != 7 or any(record["source"] != "demo_sample" for record in weights):
        raise RuntimeError("Seven explicitly labelled weight samples are required")
    seeded_tasks = [task for task in home["tasks"] if task["title"].endswith(" · 演示")]
    if (
        len(seeded_tasks) != 6
        or len(
            [
                record
                for record in home["occurrences"]
                if record["task_id"] in {task["id"] for task in seeded_tasks}
            ]
        )
        != 3
    ):
        raise RuntimeError("Expected six plans and three server-recorded demo completions")
    confirmed = [
        memory
        for memory in memories
        if memory["status"] == "confirmed" and "虚构演示偏好" in memory["text"]
    ]
    if len(confirmed) != 3 or any(
        memory["memory_backend"] != "owner_confirmed_database" for memory in confirmed
    ):
        raise RuntimeError("Expected three genuinely saved and confirmed demo preferences")
    today_report = reports[0]
    if today_report["care"]["manual_completed"] < 3 or not today_report["source_record_ids"]:
        raise RuntimeError("The calculated report must cite saved demo care facts")
    available_ids = {
        record["id"]
        for key in ("measurements", "tasks", "occurrences", "diary", "history", "device_receipts")
        for record in home.get(key, [])
    }
    if any(set(report["source_record_ids"]) - available_ids for report in reports):
        raise RuntimeError("A report cited a missing source")
    after = {"home": home, "reports": reports, "context": context}
    (ROOT / f"{target}-after.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {
        "target": target,
        "household_id": client.me["household"]["household_id"],
        "already_populated": completed,
        "weight_samples": len(weights),
        "all_weight_records": len([record for record in measures if record["kind"] == "weight"]),
        "demo_plans": len(seeded_tasks),
        "demo_completions": 3,
        "confirmed_preferences": len(confirmed),
        "generated_reports": len(reports),
        "today_report_manual_completed": today_report["care"]["manual_completed"],
        "today_report_sources": len(today_report["source_record_ids"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date", required=True, type=lambda value: datetime.strptime(value, "%Y-%m-%d").date()
    )
    parser.add_argument("--target", choices=TARGETS, action="append")
    args = parser.parse_args()
    if args.date.isoformat() != "2026-10-13" or args.date != datetime.now(ZONE).date():
        raise SystemExit("This fixture supports only its original client day: 2026-10-13")
    result = [populate(target, args.date) for target in args.target or TARGETS]
    (ROOT / "verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False))
