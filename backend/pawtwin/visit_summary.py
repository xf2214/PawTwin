"""Source-based export projections; historical records are not AI retrieval context."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pawtwin.family_views import (
    VisitCareView,
    VisitDiaryView,
    VisitMeasurementView,
    VisitObservationView,
    VisitPetView,
    VisitPreferenceView,
)
from pawtwin.growth import parse


def profile(pet: dict) -> dict:
    return VisitPetView.model_validate(pet).model_dump()


def measurement(record: dict) -> dict:
    return VisitMeasurementView.model_validate(record).model_dump()


def historical_title(home: dict, occurrence: dict) -> str:
    task = next((t for t in home["tasks"] if t["id"] == occurrence["task_id"]), None)
    if task is None:
        return "人工照护（历史名称未记录）"
    matching = [
        v for v in [*task.get("revisions", []), task] if v.get("occurrence_id") == occurrence["id"]
    ]
    dated = [
        (index, v)
        for index, v in enumerate(matching)
        if v.get("updated_at") and parse(v["updated_at"]) <= parse(occurrence["completed_at"])
    ]
    if dated:
        return max(dated, key=lambda pair: (parse(pair[1]["updated_at"]), pair[0]))[1]["title"]
    undated = [v for v in task.get("revisions", []) if v in matching and not v.get("updated_at")]
    return undated[-1]["title"] if undated else "人工照护（历史名称未记录）"


def care_record(home: dict, occurrence: dict) -> dict:
    task = next((t for t in home["tasks"] if t["id"] == occurrence["task_id"]), {})
    return VisitCareView.model_validate(
        {
            **occurrence,
            "title": historical_title(home, occurrence),
            "kind": task.get("kind"),
        }
    ).model_dump()


def preferences(home: dict, pet_id: str, now: datetime) -> list[dict]:
    result = []
    for record in home.get("memories", []):
        if (
            record["pet_id"] != pet_id
            or record.get("deleted")
            or record["status"] != "confirmed"
            or parse(record["created_at"]) > now
        ):
            continue
        result.append(
            VisitPreferenceView.model_validate(
                {
                    **record,
                    "source": "owner_confirmed",
                    "active": not record.get("valid_until") or parse(record["valid_until"]) > now,
                }
            ).model_dump()
        )
    for record in home["notes"]:
        if (
            record["pet_id"] == pet_id
            and not record.get("deleted")
            and record["scope"] == "preference"
            and parse(record["created_at"]) <= now
        ):
            result.append(
                VisitPreferenceView.model_validate(
                    {
                        **record,
                        "topic": record.get("activity", "general"),
                        "active": True,
                        "source": "owner_confirmed",
                    }
                ).model_dump()
            )
    return sorted(result, key=lambda r: (parse(r["created_at"]), r["id"]), reverse=True)


def age_at(pet: dict, now: datetime, timezone: str) -> dict:
    if pet.get("birthday"):
        birthday = date.fromisoformat(pet["birthday"])
        days = (now.astimezone(ZoneInfo(timezone)).date() - birthday).days
        if days >= 0:
            return {
                "years": round(days / 365.2425, 2),
                "days": days,
                "basis": "birthday",
                "estimated": pet.get("birthday_estimated", False),
            }
    if pet.get("age_years") is not None:
        return {
            "years": pet["age_years"],
            "days": None,
            "basis": "owner_entered",
            "estimated": True,
        }
    return {"years": None, "days": None, "basis": "unknown", "estimated": False}


def build_summary(home: dict, pet_id: str, timezone: str, days=7, include_demo=False, now=None):
    now = now or datetime.now(UTC)
    zone = ZoneInfo(timezone)
    today = now.astimezone(zone).date()
    first_day = today - timedelta(days=days - 1)
    start = datetime.combine(first_day, time(), zone).astimezone(UTC)
    pet = next(p for p in home["pets"] if p["id"] == pet_id)
    valid = [
        r
        for r in home.get("measurements", [])
        if r["pet_id"] == pet_id and not r.get("deleted") and parse(r["measured_at"]) <= now
    ]
    excluded = (
        sum(r["source"] == "demo_sample" and parse(r["measured_at"]) >= start for r in valid)
        if not include_demo
        else 0
    )
    accepted = [r for r in valid if include_demo or r["source"] != "demo_sample"]
    measurements = [measurement(r) for r in accepted if parse(r["measured_at"]) >= start]
    measurements.sort(key=lambda r: (parse(r["measured_at"]), r["id"]), reverse=True)
    weights = [r for r in accepted if r["kind"] == "weight"]
    latest = (
        measurement(max(weights, key=lambda r: (parse(r["measured_at"]), r["id"])))
        if weights
        else None
    )
    observations = [
        VisitObservationView.model_validate({**r, "source": "owner_record"}).model_dump()
        for r in home["notes"]
        if r["pet_id"] == pet_id
        and not r.get("deleted")
        and r["scope"] != "preference"
        and start <= parse(r["created_at"]) <= now
    ]
    care = [
        care_record(home, r)
        for r in home.get("occurrences", [])
        if r["pet_id"] == pet_id
        and not r.get("deleted")
        and r["source"] == "manual_care"
        and r["status"] == "completed"
        and start <= parse(r["completed_at"]) <= now
    ]
    diary = [
        VisitDiaryView.model_validate({**r, "source": "owner_record"}).model_dump()
        for r in home["diary"]
        if r["pet_id"] == pet_id
        and not r.get("deleted")
        and first_day <= date.fromisoformat(r["happened_on"]) <= today
        and (not r.get("created_at") or parse(r["created_at"]) <= now)
    ]
    confirmed = preferences(home, pet_id, now)
    records = measurements + observations + care + diary + confirmed + ([latest] if latest else [])
    missing = [
        "食物说明未结构化记录（请查看原始饮食备注）",
        "过敏资料需核对补充",
        "用药资料需核对补充",
        "疫苗资料需核对补充",
    ]
    if not latest:
        missing.append("实测体重未记录")
    age = age_at(pet, now, timezone)
    if age["basis"] == "unknown":
        missing.append("生日或年龄未记录")
    return {
        "pet": profile(pet),
        "measurements": measurements,
        "latest_weight": latest,
        "observations": observations,
        "care": care,
        "diary": diary,
        "preferences": confirmed,
        "age": age,
        "source_versions": {r["id"]: r["version"] for r in records},
        "context_version": home.get("revision", 1),
        "as_of": now.isoformat(),
        "timezone": timezone,
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "days": days,
        "include_demo": include_demo,
        "missing_fields": missing,
        "demo_excluded_count": excluded,
        "label": "已保存记录的就诊资料摘要，非诊断；观察时间为录入时间",
    }
