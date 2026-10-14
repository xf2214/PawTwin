"""Deterministic statistics with original record IDs and explicit missing values."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pawtwin.home_store import new_id


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def window(day: date, period: str, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    start_day = day - timedelta(days=day.weekday()) if period == "weekly" else day
    end_day = start_day + timedelta(days=7 if period == "weekly" else 1)
    return (
        datetime.combine(start_day, time(), zone).astimezone(UTC),
        datetime.combine(end_day, time(), zone).astimezone(UTC),
    )


def through_cutoff(value: str, cutoff: datetime, end: datetime) -> bool:
    """Current as-of time is inclusive; a closed calendar window's end is not."""
    instant = parse(value)
    return instant < cutoff or (cutoff < end and instant == cutoff)


def manual_completions(
    home: dict, pet_id: str, household_id: str,
    start: datetime, cutoff: datetime, end: datetime,
) -> list[dict]:
    """Durable facts own completion time; unlinked old logs remain a fallback."""

    def scoped(record):
        return (
            record["pet_id"] == pet_id
            and not record.get("deleted")
            and record.get("household_id") in (None, household_id)
        )

    occurrences = sorted(
        (
            o for o in home.get("occurrences", [])
            if scoped(o) and o["source"] == "manual_care" and o["status"] == "completed"
        ),
        key=lambda o: (parse(o["completed_at"]), o["id"]),
    )
    legacy = {
        h["id"]: h
        for h in sorted(home["history"], key=lambda h: (parse(h["created_at"]), h["id"]))
        if scoped(h) and not h.get("occurrence_id") and (
            h.get("action") == "complete"
            or (h.get("action") is None and h["text"].startswith("完成："))
        )
    }
    linked = {
        h["occurrence_id"] for h in home["history"] if scoped(h) and h.get("occurrence_id")
    }
    tasks_by_id = {t["id"]: t for t in home["tasks"]}
    # Older builds did not link a completion's log to its occurrence. Correlate
    # only an immediately following log from the same member and historical title,
    # consuming at most one per fact. Keep unmatched legacy records and source IDs.
    # Match across window boundaries, so a later log never moves a completion.
    for occurrence in occurrences:
        if occurrence["id"] in linked:
            continue
        completed_at = parse(occurrence["completed_at"])
        task = tasks_by_id.get(occurrence["task_id"])
        if task is None:
            continue
        candidates = [
            v for v in [*task.get("revisions", []), task]
            if v.get("occurrence_id") == occurrence["id"] and v.get("updated_at")
            and parse(v["updated_at"]) <= completed_at
        ]
        if candidates:
            title = max(candidates, key=lambda v: parse(v["updated_at"]))["title"]
        else:
            # A migrated task's first pre-completion revision has an occurrence
            # ID but no update timestamp. Its exact ID still identifies the title;
            # do not substitute today's title or invent a historical timestamp.
            undated = [
                v for v in task.get("revisions", [])
                if v.get("occurrence_id") == occurrence["id"] and not v.get("updated_at")
            ]
            if not undated:
                continue
            title = undated[-1]["title"]
        prefix = "完成：" + title
        match = next(
            (
                h for h in legacy.values()
                if h.get("actor_id") == occurrence["completed_by"]
                and h.get("task_id", occurrence["task_id"]) == occurrence["task_id"]
                and (h["text"] == prefix or h["text"].startswith(prefix + "；"))
                and 0 <= (parse(h["created_at"]) - completed_at).total_seconds() <= 1
            ),
            None,
        )
        if match is not None:
            del legacy[match["id"]]
    return [
        {**o, "actor_id": o["completed_by"]}
        for o in occurrences
        if start <= parse(o["completed_at"]) and through_cutoff(o["completed_at"], cutoff, end)
    ] + [
        {**h, "actor_id": h.get("actor_id") or h.get("author_user_id") or "legacy-unknown"}
        for h in legacy.values()
        if start <= parse(h["created_at"]) and through_cutoff(h["created_at"], cutoff, end)
    ]


def build_report(
    home: dict, pet_id: str, day: date, period: str, household: dict, now: datetime | None = None
) -> dict:
    now = now or datetime.now(UTC)
    start, end = window(day, period, household["timezone"])
    cutoff = min(end, now)
    measurements = [
        m
        for m in home.get("measurements", [])
        if m["pet_id"] == pet_id and not m.get("deleted")
        and through_cutoff(m["measured_at"], cutoff, end)
    ]
    weights = sorted(
        (m for m in measurements if m["kind"] == "weight"),
        key=lambda m: (parse(m["measured_at"]), m["id"]),
    )
    ids = [m["id"] for m in measurements if start <= parse(m["measured_at"])]
    delta = percent = span = None
    # latest_g remains a displayed fact even when its measurement predates the window.
    weight_sources = [weights[-1]["id"]] if weights else []
    # A baseline before the window is allowed, but its real span is always exposed.
    if weights and parse(weights[-1]["measured_at"]) >= start:
        last = weights[-1]
        earlier = [m for m in weights[:-1] if parse(m["measured_at"]) < parse(last["measured_at"])]
        if earlier:
            first = (
                earlier[0]
                if parse(earlier[0]["measured_at"]) >= start
                else (
                    next(
                        (m for m in reversed(earlier) if parse(m["measured_at"]) < start),
                        earlier[0],
                    )
                )
            )
            delta = round(last["value_g"] - first["value_g"], 6)
            percent = round(delta / first["value_g"] * 100, 6) if first["value_g"] > 0 else None
            span = round(
                (parse(last["measured_at"]) - parse(first["measured_at"])).total_seconds() / 86400,
                6,
            )
            weight_sources = [first["id"], last["id"]]
    ids += weight_sources
    diet = {}
    for kind in ("actual_intake", "food_offered", "dispensed", "remaining"):
        values = [
            m["value_g"]
            for m in measurements
            if m.get("diet_type") == kind and start <= parse(m["measured_at"])
        ]
        diet[kind + "_g"] = round(sum(values), 6) if values else None
    history = [
        h
        for h in home["history"]
        if h["pet_id"] == pet_id
        and not h.get("deleted")
        and h.get("household_id") in (None, household["household_id"])
        and start <= parse(h["created_at"])
        and through_cutoff(h["created_at"], cutoff, end)
    ]
    completed = manual_completions(home, pet_id, household["household_id"], start, cutoff, end)
    diaries = [
        d
        for d in home["diary"]
        if d["pet_id"] == pet_id
        and not d.get("deleted")
        and start.astimezone(ZoneInfo(household["timezone"])).date()
        <= date.fromisoformat(d["happened_on"])
        < (end.astimezone(ZoneInfo(household["timezone"])).date())
    ]
    tasks = []
    unknown_tasks = 0
    for task in home["tasks"]:
        if task["pet_id"] != pet_id:
            continue
        if not task.get("created_at"):
            unknown_tasks += 1
            continue
        versions = [*task.get("revisions", []), task]
        effective = [
            v for v in versions if v.get("updated_at") and parse(v["updated_at"]) <= cutoff
        ]
        if not effective:
            continue
        state = max(effective, key=lambda v: parse(v["updated_at"]))
        if (
            not state["completed"]
            and state.get("status") != "cancelled"
            and parse(state["due_at"]) < end
        ):
            tasks.append(state)
    receipts = [
        r
        for r in home.get("device_receipts", [])
        if r["pet_id"] == pet_id and start <= parse(r["created_at"])
        and through_cutoff(r["created_at"], cutoff, end)
    ]
    successes = [r for r in receipts if r["status"] == "succeeded"]
    food = [r for r in successes if r["kind"] == "dispense_food"]
    diet["simulated_device_dispensed_g"] = sum(r["grams"] for r in food) if food else None
    ids += [h["id"] for h in history] + [d["id"] for d in diaries]
    ids += [c["id"] for c in completed]
    ids += [t["id"] for t in tasks] + [r["id"] for r in receipts]
    return {
        "report_id": new_id(),
        "household_id": household["household_id"],
        "pet_id": pet_id,
        "period": period,
        "date": day.isoformat(),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "cutoff": cutoff.isoformat(),
        "generated_at": now.isoformat(),
        "stat_version": home.get("revision", 1),
        "status": "current",
        "notification": "not_sent",
        "source_record_ids": list(dict.fromkeys(ids)),
        "source_versions": {
            r["id"]: r.get("version", 1)
            for r in measurements + history + diaries + tasks + receipts + completed
            if r["id"] in ids
        },
        "coverage": {
            "weight_measurements": sum(
                m["kind"] == "weight" and start <= parse(m["measured_at"]) for m in measurements
            ),
            "diet_records": sum(
                m["kind"] == "diet" and start <= parse(m["measured_at"]) for m in measurements
            ),
            "incomplete_window": cutoff < end,
            "tasks_without_creation_time": unknown_tasks,
        },
        "weight": {
            "change_g": delta,
            "change_percent": percent,
            "span_days": span,
            "source_record_ids": weight_sources,
            "latest_g": weights[-1]["value_g"] if weights else None,
            "description": "实际测量跨度；群体参考不能用于诊断",
        },
        "diet": diet,
        "care": {
            "manual_completed": len(completed),
            "device_success": len(successes) if home.get("simulated_device_connected") else None,
            "device_failed": sum(r["status"] == "failed" for r in receipts),
            "device_unknown": sum(r["status"] == "unknown" for r in receipts),
            "device_results_simulated": True,
            "pending": len(tasks),
            "pending_definition": "截止时仍待照护且应在窗口结束前完成；缺创建时间不补算",
            "overdue": sum(parse(t["due_at"]) < cutoff for t in tasks),
            "by_member": {
                uid: sum(h.get("actor_id") == uid for h in completed)
                for uid in {h.get("actor_id", "legacy") for h in completed}
            },
        },
        "growth": {"diary_count": len(diaries)},
    }


def put_report(home: dict, report: dict) -> dict:
    for old in home["reports"]:
        if (old["pet_id"], old["period"], old["window_start"]) == (
            report["pet_id"],
            report["period"],
            report["window_start"],
        ) and old["status"] == "current":
            if (
                old["stat_version"] == report["stat_version"]
                and old["coverage"]["incomplete_window"] == report["coverage"]["incomplete_window"]
                and old["source_record_ids"] == report["source_record_ids"]
                and old["care"] == report["care"]
                and old["diet"] == report["diet"]
                and old["weight"] == report["weight"]
            ):
                return old
            old["status"] = "superseded"
    home["reports"].append(report)
    return report
