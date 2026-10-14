"""Scoped family extension APIs; local accounts do not represent Cognito."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request, Response

from pawtwin.api import CsrfSessionDep, SessionDep, _client_ip, _cookie_secure
from pawtwin.auth import SESSION_COOKIE
from pawtwin.care_access import CreateCareAccess, grant_view
from pawtwin.family_models import (
    AccountLogin,
    AccountRegister,
    ChatInput,
    ConfirmProposal,
    DiaryRevision,
    HouseholdInput,
    InvitationAccept,
    InvitationInput,
    MeasurementInput,
    MemberPermission,
    MemoryInput,
    MemoryUpdate,
    NoteRevision,
    PetLifecycleInput,
    ProfileInput,
    ProposalInput,
    ReportInput,
)
from pawtwin.family_store import SEED_USER, FamilyStore
from pawtwin.family_views import (
    CareAccessCreatedView,
    CareAccessGrantView,
    CareAccessListView,
    FamilySessionView,
    HouseholdView,
    MeasurementListView,
    MeasurementView,
    MemoryListView,
    MemoryView,
    PetContextView,
    ProposalView,
    ReplyView,
    ReportListView,
    ReportView,
    VisitSummaryView,
)
from pawtwin.home_api import authenticated_actor, check_photo, find, log, trusted_actor
from pawtwin.home_store import new_id, now_iso
from pawtwin.pet_context import snapshot
from pawtwin.visit_summary import build_summary

router = APIRouter(prefix="/api/family", tags=["Local family extension"])


def store(request: Request) -> FamilyStore:
    result = request.app.state.family_store
    if result is None:
        raise HTTPException(503, "Cloud family identity/storage has not been connected")
    return result


def identity(request: Request, session):
    repo = store(request)
    if not session.user_id:
        repo.import_legacy(request.app.state.legacy_source_store)
        session.user_id = SEED_USER
    return repo


def member(request, session, admin=False):
    repo = identity(request, session)
    result = repo.membership(session.owner_id, session.user_id)
    if admin and result["role"] != "admin":
        raise HTTPException(403, "Household administrator required")
    return result


def me_view(repo, session):
    hid = session.owner_id if not session.owner_id.startswith("unassigned:") else None
    return {
        "user": repo.user(session.user_id),
        "household": repo.household(hid) if hid else None,
        "membership": repo.membership(hid, session.user_id) if hid else None,
        "members": repo.members(hid) if hid else [],
        "csrf_token": session.csrf_token,
        "identity_backend": "local_account",
        "cloud_authenticated": False,
    }


def open_session(request, response, user):
    repo = store(request)
    auth = request.app.state.auth
    auth.logout(request.cookies.get(SESSION_COOKIE))
    session = auth.account_session(user["user_id"], repo.current_household(user["user_id"]))
    response.set_cookie(
        SESSION_COOKIE,
        session.session_id,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
        max_age=request.app.state.settings.session_ttl_seconds,
    )
    response.headers["Cache-Control"] = "no-store"
    return me_view(repo, session)


@router.post("/register", response_model=FamilySessionView)
def register(body: AccountRegister, request: Request, response: Response) -> dict:
    repo = store(request)
    limiter = request.app.state.registration_limiter
    ip = _client_ip(request)
    if wait := limiter.check(ip):
        raise HTTPException(429, "RATE_LIMITED", headers={"Retry-After": str(wait)})
    # Registration is local-development only; deployed AWS mode fails closed in store().
    limiter.register_failure(ip)
    return open_session(
        request, response, repo.register(body.username, body.password, body.display_name)
    )


@router.post("/login", response_model=FamilySessionView)
def login(body: AccountLogin, request: Request, response: Response) -> dict:
    repo = store(request)
    limiter, ip = request.app.state.login_limiter, _client_ip(request)
    if wait := limiter.check(ip):
        raise HTTPException(429, "RATE_LIMITED", headers={"Retry-After": str(wait)})
    user = repo.authenticate(body.username, body.password)
    if not user:
        limiter.register_failure(ip)
        raise HTTPException(401, "Invalid account or password")
    limiter.register_success(ip)
    return open_session(request, response, user)


@router.get("/me", response_model=FamilySessionView)
def me(request: Request, session: SessionDep) -> dict:
    return me_view(identity(request, session), session)


@router.get("/services")
def services(request: Request, session: SessionDep) -> dict:
    member(request, session)
    settings = request.app.state.settings
    return {
        "assistant": {
            "backend": settings.family_model_backend,
            "connection": (
                "configured_not_verified" if settings.family_model_backend == "bedrock" else "local"
            ),
        },
        "photo_recognition": {
            "enabled": settings.photo_recognition_enabled,
            "backend": "bedrock" if settings.photo_recognition_enabled else "disabled",
        },
        "model_budget": request.app.state.family_model_ledger.summary(),
        "identity": "local_account", "family_storage": "sqlite",
        "photos": "private_backend_database", "reports": "backend_worker",
        "memory": "owner_confirmed_database",
        "legacy_memory": settings.effective_memory_backend,
        "alexa_platform": "not_connected_partner_access_unavailable",
        "device": "simulated", "cloud_end_to_end_verified": False,
    }


@router.patch("/me", response_model=FamilySessionView)
def update_me(body: ProfileInput, request: Request, session: CsrfSessionDep) -> dict:
    repo = identity(request, session)
    hid = session.owner_id if not session.owner_id.startswith("unassigned:") else None
    repo.update_profile(session.user_id, hid, body.model_dump())
    return me_view(repo, session)


@router.post("/households", response_model=HouseholdView)
def household(body: HouseholdInput, request: Request, session: CsrfSessionDep) -> dict:
    repo = identity(request, session)
    home = repo.create_household(session.user_id, body.name, body.timezone)
    session.owner_id = home["household_id"]
    return home


@router.patch("/household", response_model=HouseholdView)
def update_household(body: HouseholdInput, request: Request, session: CsrfSessionDep) -> dict:
    member(request, session, admin=True)
    repo = store(request)

    def change(home):
        repo.conn.execute(
            "UPDATE family_households SET name=?,timezone=? WHERE id=?",
            (body.name, body.timezone, session.owner_id),
        )
        home["timezone"] = body.timezone

    repo.mutate(session.owner_id, change)
    return repo.household(session.owner_id)


@router.post("/invitations")
def invite(body: InvitationInput, request: Request, session: CsrfSessionDep) -> dict:
    member(request, session, admin=True)
    return store(request).invite(session.owner_id, session.user_id, body.model_dump())


@router.get("/invitations")
def invitations(request: Request, session: SessionDep) -> dict:
    member(request, session, admin=True)
    repo = store(request)
    with repo.lock:
        rows = repo.conn.execute(
            "SELECT id,role,expires_at,max_uses,use_count,revoked "
            "FROM family_invitations WHERE household=?",
            (session.owner_id,),
        ).fetchall()
    return {
        "invitations": [
            dict(
                zip(
                    ("invitation_id", "role", "expires_at", "max_uses", "use_count", "revoked"),
                    row,
                    strict=True,
                )
            )
            for row in rows
        ]
    }


@router.post("/invitations/accept", response_model=FamilySessionView)
def accept(body: InvitationAccept, request: Request, session: CsrfSessionDep) -> dict:
    repo = identity(request, session)
    session.owner_id = repo.accept(session.user_id, body.token)
    return me_view(repo, session)


@router.delete("/invitations/{invitation_id}")
def revoke(invitation_id: str, request: Request, session: CsrfSessionDep) -> dict:
    member(request, session, admin=True)
    repo = store(request)
    with repo.lock, repo.conn:
        cursor = repo.conn.execute(
            "UPDATE family_invitations SET revoked=1 WHERE id=? AND household=?",
            (invitation_id, session.owner_id),
        )
        if not cursor.rowcount:
            raise HTTPException(404, "Invitation not found")
    return {"revoked": True}


@router.patch("/members/{user_id}", response_model=FamilySessionView)
def permissions(
    user_id: str, body: MemberPermission, request: Request, session: CsrfSessionDep
) -> dict:
    member(request, session, admin=True)
    repo = store(request)
    repo.change_member(session.owner_id, user_id, role=body.role, feeding=body.feeding_pet_ids)
    repo.audit(session.owner_id, session.user_id, "permission_changed", user_id)
    return me_view(repo, session)


@router.delete("/members/{user_id}")
def remove(user_id: str, request: Request, session: CsrfSessionDep) -> dict:
    target = session.user_id if user_id == "me" else user_id
    member(request, session, admin=target != session.user_id)
    repo = store(request)
    repo.change_member(session.owner_id, target, remove=True)
    repo.audit(session.owner_id, session.user_id, "member_removed", target)
    if target == session.user_id:
        session.owner_id = f"unassigned:{session.user_id}"
    return {"removed": True}


def scoped_home(request, session, pet_id):
    member(request, session)
    home = store(request).read(session.owner_id)
    find(home, "pets", pet_id)
    return home


@router.get("/pets/archived")
def archived_pets(request: Request, session: SessionDep) -> dict:
    member(request, session, admin=True)
    home = store(request).read(session.owner_id)
    return {"pets": [p for p in home["pets"] if p.get("archived_at")]}


@router.patch("/pets/{pet_id}/lifecycle")
def pet_lifecycle(
    pet_id: str, body: PetLifecycleInput, request: Request, session: CsrfSessionDep
) -> dict:
    member(request, session, admin=True)
    if pet_id == "mochi" and body.archived:
        raise HTTPException(409, "Mochi is the stable device profile and cannot be archived")

    def change(home):
        pet = next((p for p in home["pets"] if p["id"] == pet_id), None)
        if pet is None:
            raise HTTPException(404, "Pet not found")
        if bool(pet.get("archived_at")) == body.archived:
            return
        pet["archived_at"] = now_iso() if body.archived else None
        if body.archived:
            store(request).conn.execute(
                "UPDATE family_care_access SET revoked_at=? "
                "WHERE household=? AND pet=? AND revoked_at IS NULL",
                (pet["archived_at"], session.owner_id, pet_id),
            )
        log(
            home,
            pet_id,
            "归档宠物资料" if body.archived else "恢复宠物资料",
            authenticated_actor(request, session),
        )

    store(request).mutate(session.owner_id, change)
    return {"pet_id": pet_id, "archived": body.archived}


@router.get("/pets/{pet_id}/measurements", response_model=MeasurementListView)
def measurements(pet_id: str, request: Request, session: SessionDep) -> dict:
    home = scoped_home(request, session, pet_id)
    return {
        "records": [
            m for m in home["measurements"] if m["pet_id"] == pet_id and not m.get("deleted")
        ]
    }


def measurement_record(body, session):
    return {
        **body.model_dump(mode="json", exclude={"version"}),
        "id": new_id(),
        "household_id": session.owner_id,
        "author_user_id": session.user_id,
        "value_g": round(body.value * (1000 if body.unit == "kg" else 1), 6),
        "recorded_at": now_iso(),
        "version": 1,
        "deleted": False,
        "corrections": [],
    }


@router.post("/pets/{pet_id}/measurements", response_model=MeasurementView)
def add_measurement(
    pet_id: str, body: MeasurementInput, request: Request, session: CsrfSessionDep
) -> dict:
    scoped_home(request, session, pet_id)
    if body.measured_at > datetime.now(UTC):
        raise HTTPException(422, "Measurement cannot be in the future")
    record = {**measurement_record(body, session), "pet_id": pet_id}
    store(request).mutate(session.owner_id, lambda home: home["measurements"].append(record))
    return record


def editable(record, session, membership, version):
    if record.get("deleted"):
        raise HTTPException(409, "Record already deleted")
    if version != record.get("version", 1):
        raise HTTPException(409, "Record changed; refresh before continuing")
    if (
        membership["role"] != "admin"
        and record.get("author_user_id", record.get("actor_id")) != session.user_id
    ):
        raise HTTPException(403, "Only the author or administrator can revise this record")


@router.put("/pets/{pet_id}/measurements/{record_id}", response_model=MeasurementView)
def edit_measurement(
    pet_id: str, record_id: str, body: MeasurementInput, request: Request, session: CsrfSessionDep
) -> dict:
    scope = member(request, session)
    result = {}

    def change(home):
        find(home, "pets", pet_id)
        record = find(home, "measurements", record_id)
        if record["pet_id"] != pet_id:
            raise HTTPException(404, "Record not found")
        editable(record, session, scope, body.version)
        if body.measured_at > datetime.now(UTC):
            raise HTTPException(422, "Measurement cannot be in the future")
        record["corrections"].append({k: v for k, v in record.items() if k != "corrections"})
        record.update(body.model_dump(mode="json", exclude={"version"}))
        record.update(
            value_g=round(body.value * (1000 if body.unit == "kg" else 1), 6),
            version=record["version"] + 1,
            corrected_at=now_iso(),
            corrected_by=session.user_id,
        )
        result.update(record)

    store(request).mutate(session.owner_id, change)
    return result


@router.delete("/pets/{pet_id}/measurements/{record_id}")
def delete_measurement(
    pet_id: str, record_id: str, version: int, request: Request, session: CsrfSessionDep
) -> dict:
    return delete_record(request, session, pet_id, "measurements", record_id, version)


def delete_record(request, session, pet_id, group, record_id, version):
    scope = member(request, session)

    def change(home):
        find(home, "pets", pet_id)
        record = find(home, group, record_id)
        if record["pet_id"] != pet_id:
            raise HTTPException(404, "Record not found")
        editable(record, session, scope, version)
        record.update(
            deleted=True,
            version=record.get("version", 1) + 1,
            deleted_at=now_iso(),
            deleted_by=session.user_id,
        )

    store(request).mutate(session.owner_id, change)
    return {"deleted": True}


@router.get("/pets/{pet_id}/reports", response_model=ReportListView)
def reports(pet_id: str, request: Request, session: SessionDep) -> dict:
    scoped_home(request, session, pet_id)
    store(request).refresh_reports(session.owner_id)
    home = scoped_home(request, session, pet_id)
    return {"reports": [r for r in home["reports"] if r["pet_id"] == pet_id]}


@router.post("/pets/{pet_id}/reports/generate", response_model=ReportView)
def generate_report(
    pet_id: str, body: ReportInput, request: Request, session: CsrfSessionDep
) -> dict:
    scoped_home(request, session, pet_id)
    return store(request).generate(session.owner_id, pet_id, body.date, body.period)


@router.get("/pets/{pet_id}/context", response_model=PetContextView)
def context(pet_id: str, request: Request, session: SessionDep) -> dict:
    return snapshot(
        scoped_home(request, session, pet_id), pet_id, store(request).household(session.owner_id)
    )


@router.get("/pets/{pet_id}/memories", response_model=MemoryListView)
def memories(pet_id: str, request: Request, session: SessionDep) -> dict:
    home = scoped_home(request, session, pet_id)
    return {
        "memories": [m for m in home["memories"] if m["pet_id"] == pet_id and not m.get("deleted")]
    }


@router.post("/pets/{pet_id}/memories", response_model=MemoryView)
def add_memory(pet_id: str, body: MemoryInput, request: Request, session: CsrfSessionDep) -> dict:
    scoped_home(request, session, pet_id)
    record = {
        **body.model_dump(mode="json"),
        "id": new_id(),
        "pet_id": pet_id,
        "household_id": session.owner_id,
        "author_user_id": session.user_id,
        "author_name": store(request).user(session.user_id)["display_name"],
        "created_at": now_iso(),
        "version": 1,
        "deleted": False,
        "memory_backend": "owner_confirmed_database",
    }
    store(request).mutate(session.owner_id, lambda home: home["memories"].append(record))
    return record


@router.patch("/pets/{pet_id}/memories/{record_id}", response_model=MemoryView)
def edit_memory(
    pet_id: str, record_id: str, body: MemoryUpdate, request: Request, session: CsrfSessionDep
) -> dict:
    scope, result = member(request, session), {}

    def change(home):
        find(home, "pets", pet_id)
        record = find(home, "memories", record_id)
        if record["pet_id"] != pet_id:
            raise HTTPException(404, "Record not found")
        editable(record, session, scope, body.version)
        record.update(body.model_dump(mode="json", exclude={"version"}, exclude_unset=True))
        record["version"] += 1
        record["corrected_at"] = now_iso()
        result.update(record)

    store(request).mutate(session.owner_id, change)
    return result


@router.delete("/pets/{pet_id}/memories/{record_id}")
def delete_memory(
    pet_id: str, record_id: str, version: int, request: Request, session: CsrfSessionDep
) -> dict:
    return delete_record(request, session, pet_id, "memories", record_id, version)


@router.delete("/pets/{pet_id}/notes/{record_id}")
def delete_note(
    pet_id: str, record_id: str, version: int, request: Request, session: CsrfSessionDep
) -> dict:
    return delete_record(request, session, pet_id, "notes", record_id, version)


@router.delete("/pets/{pet_id}/diary/{record_id}")
def delete_diary(
    pet_id: str, record_id: str, version: int, request: Request, session: CsrfSessionDep
) -> dict:
    return delete_record(request, session, pet_id, "diary", record_id, version)


def revise_record(request, session, pet_id, group, record_id, body):
    scope = member(request, session)
    body = trusted_actor(body, session)
    if group == "diary":
        check_photo(store(request), session.owner_id, body.photo_id)
    result = {}

    def change(home):
        find(home, "pets", pet_id)
        record = find(home, group, record_id)
        if record["pet_id"] != pet_id:
            raise HTTPException(404, "Record not found")
        editable(record, session, scope, body.version)
        record.setdefault("corrections", []).append(
            {k: v for k, v in record.items() if k != "corrections"}
        )
        record.update(body.model_dump(mode="json", exclude={"actor_id", "version"}))
        record.update(
            version=record.get("version", 1) + 1,
            corrected_at=now_iso(),
            corrected_by=session.user_id,
        )
        result.update(record)

    store(request).mutate(session.owner_id, change)
    return result


@router.patch("/pets/{pet_id}/notes/{record_id}")
def revise_note(
    pet_id: str, record_id: str, body: NoteRevision, request: Request, session: CsrfSessionDep
) -> dict:
    return revise_record(request, session, pet_id, "notes", record_id, body)


@router.patch("/pets/{pet_id}/diary/{record_id}")
def revise_diary(
    pet_id: str, record_id: str, body: DiaryRevision, request: Request, session: CsrfSessionDep
) -> dict:
    return revise_record(request, session, pet_id, "diary", record_id, body)


@router.post("/pets/{pet_id}/chat", response_model=ReplyView)
def chat(pet_id: str, body: ChatInput, request: Request, session: CsrfSessionDep) -> dict:
    original_owner = session.owner_id
    home = scoped_home(request, session, pet_id)
    ctx = snapshot(home, pet_id, store(request).household(session.owner_id))
    other_names = [
        p["name"] for p in home["pets"] if p["id"] != pet_id and not p.get("archived_at")
    ]
    result = request.app.state.family_assistant.respond(
        ctx, body.text, body.entry, other_names, session
    )
    if request.app.state.auth.get_session(session.session_id) is None:
        raise HTTPException(401, "Session expired during inference")
    if session.owner_id != original_owner:
        raise HTTPException(409, "Household changed during inference")
    latest = scoped_home(request, session, pet_id)  # Rechecks live membership/archive.
    if (
        latest["revision"] != ctx["context_version"]
        or datetime.fromisoformat(ctx["valid_until"]) <= datetime.now(UTC)
    ):
        raise HTTPException(409, "Context changed or expired during inference; ask again")
    return result


@router.get("/pets/{pet_id}/visit-summary", response_model=VisitSummaryView)
def visit_summary(
    pet_id: str, request: Request, session: SessionDep,
    days: int = Query(7, json_schema_extra={"enum": [7, 30, 90]}), include_demo: bool = False,
) -> dict:
    if days not in (7, 30, 90):
        raise HTTPException(422, "Choose a 7, 30 or 90 day window")
    return build_summary(
        scoped_home(request, session, pet_id), pet_id,
        store(request).household(session.owner_id)["timezone"], days, include_demo,
    )


@router.post("/pets/{pet_id}/care-access", response_model=CareAccessCreatedView)
def create_access(
    pet_id: str, body: CreateCareAccess, request: Request, session: CsrfSessionDep,
) -> dict:
    member(request, session, admin=True)
    repo = store(request)
    token, grant = repo.create_care_access(
        session.owner_id, pet_id, session.user_id, body.expires_in_hours,
    )
    return {"token": token, "grant": grant_view(repo, grant)}


@router.get("/pets/{pet_id}/care-access", response_model=CareAccessListView)
def list_access(pet_id: str, request: Request, session: SessionDep) -> dict:
    member(request, session, admin=True)
    home = scoped_home(request, session, pet_id)
    repo = store(request)
    return {"grants": [
        grant_view(repo, g, home) for g in repo.care_access_list(session.owner_id, pet_id)
    ]}


@router.post("/pets/{pet_id}/care-access/{access_id}/revoke", response_model=CareAccessGrantView)
def revoke_access(pet_id: str, access_id: str, request: Request, session: CsrfSessionDep) -> dict:
    member(request, session, admin=True)
    repo = store(request)
    return grant_view(repo, repo.revoke_care_access(
        session.owner_id, pet_id, access_id, session.user_id,
    ))


@router.post("/pets/{pet_id}/proposals", response_model=ProposalView)
def propose(pet_id: str, body: ProposalInput, request: Request, session: CsrfSessionDep) -> dict:
    member(request, session)
    record = {}

    def change(home):
        find(home, "pets", pet_id)
        if body.context_version is not None and body.context_version != home["revision"]:
            raise HTTPException(409, "Facts changed; review a fresh proposal")
        if body.context_valid_until is not None and body.context_valid_until <= datetime.now(UTC):
            raise HTTPException(409, "Context expired; review a fresh proposal")
        ctx = snapshot(home, pet_id, store(request).household(session.owner_id))
        record.update(
            **body.model_dump(mode="json", exclude={"context_version", "context_valid_until"}),
            id=new_id(),
            pet_id=pet_id,
            household_id=session.owner_id,
            author_user_id=session.user_id,
            version=1,
            context_version=home["revision"] + 1,
            status="awaiting_confirmation",
            created_at=now_iso(),
            device_action=False,
            context_valid_until=ctx["valid_until"],
        )
        home["proposals"].append(record)

    store(request).mutate(session.owner_id, change)
    return record


@router.post("/pets/{pet_id}/proposals/{proposal_id}/confirm", response_model=ProposalView)
def confirm(
    pet_id: str, proposal_id: str, body: ConfirmProposal, request: Request, session: CsrfSessionDep
) -> dict:
    member(request, session)
    result = {}

    def change(home):
        find(home, "pets", pet_id)
        proposal = find(home, "proposals", proposal_id)
        if proposal["pet_id"] != pet_id:
            raise HTTPException(404, "Proposal not found")
        if proposal["status"] == "confirmed":
            result.update(proposal)
            return
        if (
            body.version != proposal["version"]
            or body.context_version != proposal["context_version"]
            or proposal["context_version"] != home["revision"]
            or (
                proposal.get("context_valid_until")
                and datetime.fromisoformat(proposal["context_valid_until"]) <= datetime.now(UTC)
            )
        ):
            raise HTTPException(409, "Facts changed; review a fresh proposal")
        task = {
            "id": new_id(),
            "pet_id": pet_id,
            "kind": proposal["kind"],
            "title": proposal["title"],
            "due_at": proposal["due_at"],
            "interval_days": None,
            "assigned_to": session.user_id,
            "completed": False,
            "last_completed_at": None,
            "claimed_by": None,
            "status": "pending",
            "version": 1,
            "occurrence_id": new_id(),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "revisions": [],
            "author_user_id": session.user_id,
        }
        home["tasks"].append(task)
        proposal.update(
            status="confirmed", confirmed_by=session.user_id, task_id=task["id"], version=2
        )
        result.update(proposal)

    store(request).mutate(session.owner_id, change)
    return result
