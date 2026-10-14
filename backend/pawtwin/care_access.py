"""Temporary, pet-scoped read-only capability access. Never calls a cloud model."""

import re
import threading
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from datetime import time as day_time
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from pawtwin.api import _client_ip
from pawtwin.family_views import (
    CareAccessContextView,
    CareAccessReplyView,
    CareTaskView,
    VisitObservationView,
)
from pawtwin.growth import parse
from pawtwin.pet_context import answer, care_request, snapshot
from pawtwin.visit_summary import care_record, measurement, preferences, profile

router = APIRouter(prefix="/api/care-access", tags=["Temporary read-only care access"])
bearer = HTTPBearer(auto_error=False)


class CreateCareAccess(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expires_in_hours: Literal[1, 4, 24, 72] = 24


class CareAccessChat(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=2000)


class CareAccessLimiter:
    """Single-process 60-request/minute IP limit, including invalid keys."""

    def __init__(self):
        self.lock = threading.Lock()
        self.requests: dict[str, deque] = {}

    def check(self, key):
        now = time.monotonic()
        with self.lock:
            recent = self.requests.setdefault(key, deque())
            while recent and recent[0] <= now - 60:
                recent.popleft()
            if len(recent) >= 60:
                raise HTTPException(429, "Care access rate limited", headers={"Retry-After": "60"})
            recent.append(now)


def grant_view(repo, grant, home=None):
    with repo.lock:
        home = home if home is not None else repo._load(grant["household"])
        pet = next((p for p in home["pets"] if p["id"] == grant["pet"]), {})
        return {
            "id": grant["id"],
            "pet_name": pet.get("name", "宠物"),
            "created_at": grant["created_at"],
            "expires_at": grant["expires_at"],
            "revoked_at": grant["revoked_at"],
            "status": repo.care_access_status(grant, home),
        }


def access_key(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    request.app.state.care_access_limiter.check(_client_ip(request))
    if request.query_params:
        raise HTTPException(400, "Use the Authorization header for care access")
    if credentials is None or not re.fullmatch(r"[A-Za-z0-9_-]{43}", credentials.credentials):
        raise HTTPException(401, "Care access key is required")
    return credentials.credentials


AccessKey = Annotated[str, Depends(access_key)]


def resolve(request, token):
    repo = request.app.state.family_store
    if repo is None:
        raise HTTPException(503, "Care access storage is not connected")
    grant, home = repo.resolve_care_access(token)
    return repo, grant, home


def public_context(repo, grant, home):
    now = datetime.now(UTC)
    household = repo.household(grant["household"])
    zone = ZoneInfo(household["timezone"])
    first_day = now.astimezone(zone).date() - timedelta(days=6)
    start = datetime.combine(first_day, day_time(), zone).astimezone(UTC)
    pet = next(p for p in home["pets"] if p["id"] == grant["pet"])
    current = snapshot(home, grant["pet"], household, now)
    allowed_preferences = [r for r in preferences(home, grant["pet"], now) if r["active"]]
    observations = [
        VisitObservationView.model_validate({**r, "source": "owner_record"}).model_dump()
        for r in current["layers"]["recent"]["observations"]
        if start <= parse(r["created_at"]) <= now
    ]
    completed = [
        care_record(home, r)
        for r in home.get("occurrences", [])
        if r["pet_id"] == grant["pet"]
        and not r.get("deleted")
        and r["source"] == "manual_care"
        and r["status"] == "completed"
        and start <= parse(r["completed_at"]) <= now
    ]
    tasks = [
        CareTaskView.model_validate({**r, "source": "owner_plan"}).model_dump()
        for r in current["layers"]["recent"]["tasks"]
        if start <= parse(r["due_at"]) <= now + timedelta(days=7)
    ]
    measurements = [
        measurement(r)
        for r in current["layers"]["growth"]
        if r["source"] != "demo_sample" and start <= parse(r["measured_at"]) <= now
    ]
    public = {
        "grant": grant_view(repo, grant, home),
        "pet": profile(pet),
        "as_of": now.isoformat(),
        "timezone": household["timezone"],
        "context_version": home.get("revision", 1),
        "read_only": True,
        "preferences": allowed_preferences,
        "observations": observations,
        "completed_care": completed,
        "tasks": tasks,
        "measurements": measurements,
        "label": "仅该宠物的临时只读照护资料；本地规则分身，无设备或修改权限",
    }
    # The rule answer receives the same scoped facts that the visitor can see.
    current["layers"] = {
        "profile": public["pet"],
        "growth": measurements,
        "memory": allowed_preferences,
        "recent": {
            "observations": observations,
            "today_observations": [
                r
                for r in observations
                if r["id"] in {n["id"] for n in current["layers"]["recent"]["today_observations"]}
            ],
            "completed_care": completed,
            "tasks": tasks,
        },
        "reference": [],
    }
    current["valid_until"] = grant["expires_at"]
    return public, current


@router.get("/context", response_model=CareAccessContextView)
def context(request: Request, token: AccessKey):
    repo, grant, home = resolve(request, token)
    result, _ = public_context(repo, grant, home)
    repo.resolve_care_access(token)  # Recheck expiry/revocation/archive/issuer before responding.
    return result


@router.post("/chat", response_model=CareAccessReplyView)
def chat(body: CareAccessChat, request: Request, token: AccessKey):
    repo, grant, home = resolve(request, token)
    public, current = public_context(repo, grant, home)
    if care_request(body.text, public["pet"]["name"])[1] is not None:
        text = "此入口仅能查看照护记录；安排、完成、修改或设备操作需主人在家庭应用中进行。"
        ids = []
    elif any(word in body.text for word in ("吃了什么", "饮食", "摄入", "出粮", "剩余")):
        records = sorted(
            (r for r in public["measurements"] if r["kind"] == "diet"),
            key=lambda r: parse(r["measured_at"]),
            reverse=True,
        )[:5]
        meanings = {
            "actual_intake": "主人记录实际摄入",
            "food_offered": "提供食物",
            "dispensed": "记录出粮",
            "remaining": "剩余食物",
        }
        text = "近期饮食记录：" + (
            "；".join(
                f"{meanings.get(r['diet_type'], '含义未说明')} {r['value_g']:g} g"
                f"（{r['measured_at']}；原备注：{r['note'] or '未填写'}）"
                for r in records
            )
            if records
            else "暂无已记录的饮食事实。"
        )
        text += "。提供食物、出粮与剩余不等于实际摄入；食物说明只来自原始备注。"
        ids = [r["id"] for r in records]
    elif any(word in body.text for word in ("做了哪些照护", "做过哪些照护", "照护记录")):
        records = sorted(
            public["completed_care"],
            key=lambda r: parse(r["completed_at"]),
            reverse=True,
        )[:5]
        text = "近七天实际人工完成记录：" + (
            "；".join(f"{r['title']}（{r['completed_at']}）" for r in records)
            if records
            else "暂无人工完成记录；待办与设备出粮不计为人工完成。"
        )
        ids = [r["id"] for r in records]
    else:
        result = answer(current, body.text, "app")
        text, ids = result["answer"], result["source_record_ids"]
    repo.resolve_care_access(token)
    return {
        "answer": text,
        "backend": "local_rules",
        "read_only": True,
        "action_executed": False,
        "as_of": public["as_of"],
        "context_version": public["context_version"],
        "source_record_ids": ids,
        "label": public["label"],
    }
