"""Business API surface (frozen contract).

Routes are declared here so the OpenAPI contract is complete; ownership of this
module sits with Backend. Auth is enforced by dependencies: business endpoints
require a session (401 otherwise), and the state-changing business writes (event
intake, approval) additionally require a matching ``X-CSRF-Token`` (403
otherwise). ``logout`` is intentionally session-scoped and idempotent: the
``SameSite=Lax`` cookie already prevents a cross-site request from carrying the
session, so no CSRF token is needed to sign out -- and a lost in-memory token
(e.g. after a page reload) must never lock a user in. Responses project internal
records onto the public DTOs; internal bookkeeping never crosses the boundary.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from pawtwin.auth import CSRF_HEADER, SESSION_COOKIE, AuthService, Session
from pawtwin.config import Settings
from pawtwin.models import (
    ApprovalIn,
    EventAccepted,
    EventIn,
    FactsView,
    LoginRequest,
    LoginResponse,
    RunView,
    StateView,
)
from pawtwin.repository import FactsSnapshot, Repository, RunRecord
from pawtwin.workflow import ApprovalRejected, Workflow

router = APIRouter()


# --- dependencies -----------------------------------------------------------


def _auth(request: Request) -> AuthService:
    return request.app.state.auth


def _workflow(request: Request) -> Workflow:
    return request.app.state.workflow


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _repository(request: Request) -> Repository:
    return request.app.state.repository


def current_session(request: Request) -> Session:
    session = _auth(request).get_session(request.cookies.get(SESSION_COOKIE))
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHENTICATED")
    return session


def require_csrf(
    request: Request, session: Annotated[Session, Depends(current_session)]
) -> Session:
    token = request.headers.get(CSRF_HEADER)
    if not _auth(request).check_csrf(session, token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF_FAILED")
    return session


SessionDep = Annotated[Session, Depends(current_session)]
CsrfSessionDep = Annotated[Session, Depends(require_csrf)]


# --- projections ------------------------------------------------------------


def _facts_view(facts: FactsSnapshot) -> FactsView:
    return FactsView(
        last_fed_minutes_ago=facts.last_fed_minutes_ago or 0,
        daily_dispensed_grams=facts.daily_dispensed_grams or 0,
        daily_limit_grams=facts.daily_limit_grams,
        single_serving_grams=facts.single_serving_grams,
        minimum_interval_minutes=facts.minimum_interval_minutes,
        facts_version=facts.facts_version,
    )


def _run_view(record: RunRecord) -> RunView:
    return RunView(
        run_id=record.run_id,
        state=record.state,
        facts_version=record.facts_version,
        proposal=record.proposal,
        receipt=record.receipt,
        expires_at=record.expires_at,
        created_at=record.created_at,
        proposal_version=record.proposal_version,
        action_digest=record.action_digest,
    )


# --- routes -----------------------------------------------------------------


@router.post("/api/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, request: Request) -> LoginResponse:
    auth = _auth(request)
    session = auth.login(body.passphrase)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session.session_id,
        httponly=True,
        samesite="lax",
        # Local HTTP omits ONLY Secure; CSRF is still enforced on writes.
        secure=_settings(request).mode == "aws",
        path="/",
    )
    return LoginResponse(csrf_token=session.csrf_token)


@router.post("/api/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, session: SessionDep) -> Response:
    _auth(request).logout(session.session_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/api/state", response_model=StateView)
def get_state(request: Request, session: SessionDep) -> StateView:
    repo = _repository(request)
    settings = _settings(request)
    facts = repo.get_facts(session.owner_id)
    runs = repo.list_runs(session.owner_id)
    return StateView(
        mode=settings.mode,
        aws_connected=settings.aws_connected,
        facts=_facts_view(facts),
        runs=[_run_view(run) for run in runs],
    )


@router.post(
    "/api/events",
    response_model=EventAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_event(event: EventIn, request: Request, session: CsrfSessionDep) -> EventAccepted:
    record = _workflow(request).handle_event(session.owner_id, event)
    return EventAccepted(run_id=record.run_id, state=record.state)


@router.get("/api/runs/{run_id}", response_model=RunView)
def get_run(run_id: UUID, request: Request, session: SessionDep) -> RunView:
    record = _repository(request).get_run(run_id)
    if record is None or record.owner_id != session.owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RUN_NOT_FOUND")
    return _run_view(record)


@router.post("/api/runs/{run_id}/approval", response_model=RunView)
def post_approval(
    run_id: UUID,
    approval: ApprovalIn,
    request: Request,
    session: CsrfSessionDep,
) -> RunView:
    try:
        record = _workflow(request).handle_approval(session.owner_id, run_id, approval)
    except ApprovalRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return _run_view(record)
