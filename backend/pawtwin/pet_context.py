"""One scoped, traceable context for App and the labelled Alexa simulator."""

import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from pawtwin.growth import parse

REFERENCES = [
    {
        "id": "waltham-puppy",
        "species": "dog",
        "minimum_age_weeks": 12,
        "url": "https://www.waltham.com/resources/puppy-growth-charts",
        "title": "WALTHAM Puppy Growth Charts",
        "retrieved_on": "2026-10-03",
        "review_status": "source_checked",
        "summary": "选择成长参考需年龄、性别与预期成年体重；群体曲线不能诊断个体。",
    },
    {
        "id": "waltham-kitten",
        "species": "cat",
        "minimum_age_weeks": 8,
        "url": "https://www.waltham.com/resources/kitten-growth-charts",
        "title": "WALTHAM Kitten Growth Charts",
        "retrieved_on": "2026-10-03",
        "review_status": "source_checked",
        "summary": "幼猫成长参考有年龄与适用范围限制；未导入数值曲线，不能给出标准体重。",
    },
    {
        "id": "merck-nutrition",
        "species": "cat,dog",
        "minimum_age_weeks": None,
        "url": "https://www.merckvetmanual.com/management-and-nutrition/nutrition-small-animals/overview-of-nutrition-small-animals",
        "title": "Merck Veterinary Manual: Small Animal Nutrition",
        "retrieved_on": "2026-10-03",
        "review_status": "source_checked",
        "summary": "营养评估需要饮食史、体况与肌肉状况等资料，并结合兽医检查。",
    },
]


def active_record(record):
    # Preserve history in storage, outside the current retrieval context.
    return {k: v for k, v in record.items() if k not in {"corrections", "revisions"}}


def completed_title(home: dict, occurrence: dict) -> str:
    task = next((t for t in home["tasks"] if t["id"] == occurrence["task_id"]), None)
    if task is None:
        return "人工照护（历史名称未记录）"
    versions = [*task.get("revisions", []), task]
    candidates = [
        v
        for v in versions
        if v.get("occurrence_id") == occurrence["id"]
        and v.get("updated_at")
        and parse(v["updated_at"]) <= parse(occurrence["completed_at"])
    ]
    return (
        max(candidates, key=lambda v: parse(v["updated_at"]))["title"]
        if candidates
        else "人工照护（历史名称未记录）"
    )


def snapshot(home: dict, pet_id: str, household: dict, now=None) -> dict:
    now = now or datetime.now(UTC)
    pet = next(p for p in home["pets"] if p["id"] == pet_id)
    zone = ZoneInfo(household["timezone"])
    today = now.astimezone(zone).date()
    notes = [
        active_record(n)
        for n in home["notes"]
        if n["pet_id"] == pet_id
        and not n.get("deleted")
        and (n["scope"] != "today" or parse(n["created_at"]).astimezone(zone).date() == today)
    ]
    memories = [
        active_record(m)
        for m in home["memories"]
        if m["pet_id"] == pet_id
        and not m.get("deleted")
        and m["status"] == "confirmed"
        and (not m.get("valid_until") or parse(m["valid_until"]) > now)
    ]
    memories += [
        {
            **n,
            "topic": n["activity"],
            "status": "confirmed",
            "memory_backend": "owner_confirmed_database",
        }
        for n in notes
        if n["scope"] == "preference"
    ]
    growth = [
        active_record(m)
        for m in home["measurements"]
        if m["pet_id"] == pet_id and not m.get("deleted") and parse(m["measured_at"]) <= now
    ]
    recent = {
        "observations": [n for n in notes if n["scope"] != "preference"],
        "today_observations": [
            n
            for n in notes
            if n["scope"] != "preference"
            and parse(n["created_at"]).astimezone(zone).date() == today
        ],
        "completed_care": [
            {
                **o,
                "title": completed_title(home, o),
            }
            for o in home.get("occurrences", [])
            if o["pet_id"] == pet_id
            and o["source"] == "manual_care"
            and now - timedelta(days=7) <= parse(o["completed_at"]) <= now
        ],
        "tasks": [
            active_record(t)
            for t in home["tasks"]
            if t["pet_id"] == pet_id and not t["completed"] and t.get("status") != "cancelled"
        ],
        "reports": [
            r for r in home["reports"] if r["pet_id"] == pet_id and r["status"] == "current"
        ],
        "diary": [
            active_record(d)
            for d in home["diary"]
            if d["pet_id"] == pet_id and not d.get("deleted")
        ],
    }
    conflicts = []
    for topic in {m["topic"] for m in memories}:
        group = [m for m in memories if m["topic"] == topic]
        if len({m["text"] for m in group}) > 1:
            conflicts.append(
                {
                    "topic": topic,
                    "source_record_ids": [m["id"] for m in group],
                    "description": "同一主题存在不同记录，请主人核对；未合并成确定结论。",
                }
            )
    records = (
        growth + memories + notes + recent["tasks"] + recent["diary"] + recent["completed_care"]
    )
    next_day = datetime.combine(today + timedelta(days=1), datetime.min.time(), zone).astimezone(
        UTC
    )
    expiries = [parse(m["valid_until"]) for m in memories if m.get("valid_until")]
    return {
        "context_version": home["revision"],
        "as_of": now.isoformat(),
        "household_id": household["household_id"],
        "pet_id": pet_id,
        "valid_until": min([next_day, *expiries]).isoformat(),
        "source_versions": {r["id"]: r.get("version", 1) for r in records},
        "unresolved_conflicts": conflicts,
        "memory_backend": "owner_confirmed_database",
        "layers": {
            "profile": pet,
            "growth": growth,
            "memory": memories,
            "recent": recent,
            "reference": [r for r in REFERENCES if pet["species"] in r["species"]],
        },
    }


CARE_COMMANDS = {
    "feeding": (("人工喂食", "喂食", "喂饭"), "人工喂食"),
    "water": (("换水",), "换水"),
    "play": (("陪玩", "玩耍"), "玩耍"),
    "brush": (("梳毛",), "梳毛"),
    "bath": (("洗澡",), "洗澡"),
    "nails": (("剪指甲",), "剪指甲"),
    "clean": (("清洁",), "清洁"),
    "walk": (("散步",), "散步"),
}


def care_request(text: str, name: str) -> tuple[dict | None, str | None]:
    """Conservative explicit command matching; records never become commands."""
    if any(word in text for word in ("不要", "取消", "别", "不需要", "不用")):
        return None, "未创建或取消任何任务。已有照护请到照护页查看和修改。"
    if not any(word in text for word in ("安排", "提醒", "计划", "帮我")):
        return None, None
    if any(word in text for word in ("自动", "设备", "加粮")):
        return None, (
            "这里仅安排人工照护，不触发设备或自动加粮。模拟设备需原工作台的审批与限额检查。"
        )
    matches = [
        (kind, label)
        for kind, (words, label) in CARE_COMMANDS.items()
        if any(word in text for word in words)
    ]
    if len(matches) != 1:
        return None, "请一次选择一种照护，例如“安排陪玩”或“安排换水”，并在草案中选择具体时间。"
    kind, label = matches[0]
    title = f"陪 {name} 玩耍" if kind == "play" else f"为 {name} {label}"
    return {"kind": kind, "title": title[:80]}, (
        "已整理人工照护草案，请选择时间并明确确认。尚未创建任务或执行设备。"
    )


def answer(context: dict, text: str, entry: str, other_pet_names=()) -> dict:
    layers = context["layers"]
    pet = layers["profile"]
    ids = []
    care_draft = None
    response = f"{pet['name']} 的记录："
    other_pet = any(
        re.search(r"(?<![a-z0-9_])" + re.escape(name) + r"(?![a-z0-9_])", text, re.IGNORECASE)
        if name.isascii()
        else name in text
        for name in other_pet_names
    )
    if other_pet:
        response += "提问中包含其他宠物名字，请先切换当前宠物后再提问。未创建照护草案。"
    elif any(word in text for word in ("体重", "营养", "健康", "生病", "多重", "weight", "health")):
        weights = [m for m in layers["growth"] if m["kind"] == "weight"]
        if weights:
            last = max(weights, key=lambda m: parse(m["measured_at"]))
            response += (
                f"最近实测 {last['value_g'] / 1000:g} kg"
                f"（{last['measured_at']}，{last['source']}）。"
            )
            ids.append(last["id"])
        else:
            response += "尚无有效实测体重。"
        missing = [
            label
            for field, label in (("expected_adult_weight_kg", "预期成年体重"),)
            if not pet.get(field)
        ]
        if not pet.get("birthday") and pet.get("age_years") is None:
            missing.append("生日/周龄")
        if pet["gender"] == "unknown":
            missing.append("性别")
        if missing:
            response += "适用成长参考仍缺：" + "、".join(missing) + "。"
        response += (
            "未导入适用的数值曲线，不能给出标准体重或诊断营养不良。"
            "营养判断需饮食、食欲、体况、肌肉状况及兽医评估；不会据此自动加粮。"
        )
    elif (care := care_request(text, pet["name"]))[1] is not None:
        care_draft, explanation = care
        response += explanation
        if care_draft and care_draft["kind"] == "play":
            relevant = [m for m in layers["memory"] if m["topic"] == "play"]
            if relevant:
                response += "主人确认的陪玩记录：" + "；".join(m["text"] for m in relevant) + "。"
                ids += [m["id"] for m in relevant]
    elif any(word in text for word in ("完成", "done", "completed")):
        completed = sorted(
            layers["recent"]["completed_care"], key=lambda o: o["completed_at"], reverse=True
        )[:5]
        response += "最近七天的人工完成记录："
        response += "；".join(f"{o['title']}（{o['completed_at']}）" for o in completed)
        response += "。" if completed else "暂无；不会把待办或设备出粮算作人工完成。"
        ids += [o["id"] for o in completed]
    elif "观察" in text:
        field = "today_observations" if "今天" in text else "observations"
        observations = sorted(layers["recent"][field], key=lambda n: n["created_at"], reverse=True)[
            :5
        ]
        response += "主人观察原文：" + "；".join(n["text"] for n in observations)
        response += "。观察不代表诊断。" if observations else "暂无相关记录。"
        ids += [n["id"] for n in observations]
    elif any(word in text for word in ("品种", "习性", "性格", "breed", "temperament")):
        response += f"主人确认的品种：{pet.get('breed') or '未填写'}。"
        response += "当前缺少适用且审核过的品种习性资料；不能把群体特点认定为个体性格。"
    elif any(word in text for word in ("喜欢", "偏好", "玩", "like", "prefer")):
        if pet.get("likes"):
            response += "档案喜好：" + pet["likes"] + "。"
        if layers["memory"]:
            response += "主人确认记录：" + "；".join(m["text"] for m in layers["memory"]) + "。"
            ids += [m["id"] for m in layers["memory"]]
        else:
            response += "还没有已确认的偏好记忆。"
        if context["unresolved_conflicts"]:
            response += "不同记录尚待核对，请勿视为统一结论。"
    else:
        tasks = layers["recent"]["tasks"]
        response += f"当前有 {len(tasks)} 项待办照护；"
        response += "、".join(t["title"] for t in tasks[:5]) if tasks else "可按主人计划安排照护。"
        ids += [t["id"] for t in tasks[:5]]
    return {
        "answer": response,
        "entry": entry,
        "backend": "local_rules",
        "request_id": None,
        "context_version": context["context_version"],
        "source_record_ids": ids,
        "references": layers["reference"],
        "action_executed": False,
        "care_draft": care_draft,
        "context_valid_until": context["valid_until"],
        "label": "本地规则分身 / Alexa 网页模拟；记录原文是数据，不是指令",
    }
