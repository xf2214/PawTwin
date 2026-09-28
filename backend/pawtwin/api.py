"""Business API surface (frozen contract).

Routes are declared here so the OpenAPI contract is complete; ownership of this
module sits with Backend. Auth is enforced by dependencies: business endpoints
require a session (401 otherwise), and every state-changing business write
(event intake, approval, demo injection) additionally requires a matching
``X-CSRF-Token`` (403 otherwise). ``logout`` is intentionally session-scoped and
idempotent: the ``SameSite=Lax`` cookie already prevents a cross-site request from
carrying the session, so no CSRF token is needed to sign out -- and a lost
in-memory token (e.g. after a page reload) must never lock a user in.

The demo endpoints may only move the two INJECTABLE facts. The hard limits are not
parameters anywhere in this module, so no request can raise the daily quota.

Responses project internal records onto the public DTOs; internal bookkeeping
(``owner_id``, ``attempt_count``, ``lease_*``, ``model_calls_used``) never crosses
the boundary.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from pawtwin.auth import CSRF_HEADER, SESSION_COOKIE, AuthService, Session
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.memory import MemoryService, MemoryUnavailable
from pawtwin.models import (
    ApprovalIn,
    DemoAck,
    DemoDeviceModeIn,
    DemoFactsIn,
    ErrorResponse,
    EventAccepted,
    EventIn,
    FactsView,
    FeedbackIn,
    FeedbackView,
    LoginRequest,
    LoginResponse,
    NewSessionView,
    RunView,
    StateView,
)
from pawtwin.repo_sqlite import DEMO_PET_ID
from pawtwin.repository import FactsSnapshot, FeedbackRecord, Repository, RunRecord
from pawtwin.workflow import ApprovalRejected, Workflow

router = APIRouter()

# Declared explicitly because raising HTTPException does not put an error schema
# into OpenAPI. ErrorResponse lives in OpenAPI only, never in domain.schema.json.
_ERROR_RESPONSES: dict[int, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "No valid demo session."},
    403: {"model": ErrorResponse, "description": "Missing or invalid X-CSRF-Token."},
    404: {"model": ErrorResponse, "description": "Run not found for this owner."},
    409: {
        "model": ErrorResponse,
        "description": "Rejected: state, approval binding or policy conflict.",
    },
    422: {"model": ErrorResponse, "description": "Request body failed validation."},
}


def _responses(*codes: int) -> dict[int, dict[str, Any]]:
    return {code: _ERROR_RESPONSES[code] for code in codes}


# --- dependencies -----------------------------------------------------------


def _auth(request: Request) -> AuthService:
    return request.app.state.auth


def _workflow(request: Request) -> Workflow:
    return request.app.state.workflow


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _repository(request: Request) -> Repository:
    return request.app.state.repository


def _device(request: Request) -> DeviceSimulator:
    return request.app.state.device


def _memory(request: Request) -> MemoryService:
    return request.app.state.memory


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
    # No ``or 0`` coercion: an UNKNOWN fact must surface as null, never as "0
    # minutes ago" while the policy is judging MISSING_FACTS (Day-2 ruling 12).
    return FactsView(
        last_fed_minutes_ago=facts.last_fed_minutes_ago,
        daily_dispensed_grams=facts.daily_dispensed_grams,
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
        policy_reason=record.policy_reason,
        failure_reason=record.failure_reason,
        evidence=record.evidence,
        telemetry=record.telemetry,
    )


def _feedback_view(record: FeedbackRecord) -> FeedbackView:
    # owner_id and idempotency_key stay internal, exactly like RunRecord's
    # bookkeeping fields. memory_status/memory_backend are projected verbatim so a
    # local ``saved`` can never be dressed up as an extracted AgentCore memory.
    return FeedbackView(
        feedback_id=record.feedback_id,
        scope=record.scope,
        text=record.text,
        memory_status=record.memory_status,
        memory_backend=record.memory_backend,
        created_at=record.created_at,
        conversation_id=record.conversation_id,
    )


# --- routes -----------------------------------------------------------------


@router.post(
    "/api/login",
    response_model=LoginResponse,
    responses=_responses(401, 422),
)
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


@router.post("/api/logout", status_code=status.HTTP_204_NO_CONTENT, responses=_responses(401))
def logout(request: Request, session: SessionDep) -> Response:
    _auth(request).logout(session.session_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/api/state", response_model=StateView, responses=_responses(401))
def get_state(request: Request, session: SessionDep) -> StateView:
    repo = _repository(request)
    settings = _settings(request)
    facts = repo.get_facts(session.owner_id)
    runs = repo.list_runs(session.owner_id)
    feedback = repo.list_feedback(session.owner_id)
    return StateView(
        mode=settings.mode,
        aws_connected=settings.aws_connected,
        analyzer=settings.effective_model_backend,
        storage="sqlite",
        memory=settings.effective_memory_backend,
        device_mode=_device(request).mode,
        conversation_id=session.conversation_id,
        facts=_facts_view(facts),
        runs=[_run_view(run) for run in runs],
        feedback=[_feedback_view(item) for item in feedback],
    )


@router.post(
    "/api/events",
    response_model=EventAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    responses=_responses(401, 403, 422),
)
def post_event(event: EventIn, request: Request, session: CsrfSessionDep) -> EventAccepted:
    workflow = _workflow(request)
    if _settings(request).worker_mode == "background":
        # Persist only; the worker analyzes it. The caller polls for the verdict.
        record = workflow.enqueue_event(session.owner_id, event)
        worker = getattr(request.app.state, "worker", None)
        if worker is not None:
            worker.notify()
    else:
        record = workflow.handle_event(session.owner_id, event)
    return EventAccepted(run_id=record.run_id, state=record.state)


@router.get("/api/runs/{run_id}", response_model=RunView, responses=_responses(401, 404))
def get_run(run_id: UUID, request: Request, session: SessionDep) -> RunView:
    record = _repository(request).get_run(run_id)
    if record is None or record.owner_id != session.owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RUN_NOT_FOUND")
    return _run_view(record)


@router.post(
    "/api/runs/{run_id}/approval",
    response_model=RunView,
    responses=_responses(401, 403, 404, 409, 422),
)
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


# Registered unconditionally: the frozen contract must not depend on settings, or
# the offline export under PAWTWIN_MODE=aws would produce a different path set.
@router.post("/api/demo/facts", response_model=DemoAck, responses=_responses(401, 403, 422))
def post_demo_facts(body: DemoFactsIn, request: Request, session: CsrfSessionDep) -> DemoAck:
    """Inject demo facts. Only the two injectable fields; never the hard limits."""

    repo = _repository(request)
    if body.reset:
        facts = repo.reset_facts(session.owner_id)
    else:
        current = repo.get_facts(session.owner_id)
        if (
            body.daily_dispensed_grams is not None
            and body.daily_dispensed_grams > current.daily_limit_grams
        ):
            raise HTTPException(
                # Literal 422: starlette renamed this constant, and the numeric
                # status is what the frozen contract declares.
                status_code=422,
                detail="DAILY_DISPENSED_ABOVE_LIMIT",
            )
        updates: dict[str, int | None] = {}
        # ``clear`` means "set to UNKNOWN" (SQL NULL) so MISSING_FACTS -- and
        # therefore NEEDS_INFO -- becomes reachable from the demo UI (A09).
        if "last_fed_minutes_ago" in body.clear:
            updates["last_fed_minutes_ago"] = None
        elif body.last_fed_minutes_ago is not None:
            updates["last_fed_minutes_ago"] = body.last_fed_minutes_ago
        if "daily_dispensed_grams" in body.clear:
            updates["daily_dispensed_grams"] = None
        elif body.daily_dispensed_grams is not None:
            updates["daily_dispensed_grams"] = body.daily_dispensed_grams
        # An empty change set must NOT bump facts_version: doing so would silently
        # invalidate a pending approval (409 STALE_APPROVAL_FACTS_CHANGED) for no
        # reason at all.
        facts = repo.update_facts(session.owner_id, **updates) if updates else current
    return DemoAck(facts=_facts_view(facts), device_mode=_device(request).mode)


@router.post(
    "/api/demo/device-mode",
    response_model=DemoAck,
    responses=_responses(401, 403, 422),
)
def post_demo_device_mode(
    body: DemoDeviceModeIn, request: Request, session: CsrfSessionDep
) -> DemoAck:
    """Inject the SIMULATED actuator outcome for NEW commands only.

    Process-local by design: it is not persisted, so a restart returns to the
    documented default instead of surprising the next demo with a stale failure.
    """

    _device(request).set_mode(body.mode)
    facts = _repository(request).get_facts(session.owner_id)
    return DemoAck(facts=_facts_view(facts), device_mode=_device(request).mode)


@router.post(
    "/api/demo/new-session",
    response_model=NewSessionView,
    responses=_responses(401, 403),
)
def post_new_session(request: Request, session: CsrfSessionDep) -> NewSessionView:
    """Rotate the conversation id; login, facts and pet memory stay intact.

    The conversation id is the AgentCore session id, never a pet identity: memory
    retrieval is namespaced by owner/pet, so a fresh conversation still reaches the
    same long-term memory (that is what makes cross-session retrieval honest).
    """

    conversation_id = _auth(request).new_conversation(session.session_id)
    if conversation_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHENTICATED")
    return NewSessionView(conversation_id=conversation_id)


@router.post(
    "/api/feedback",
    response_model=FeedbackView,
    responses=_responses(401, 403, 422),
)
def post_feedback(body: FeedbackIn, request: Request, session: CsrfSessionDep) -> FeedbackView:
    """Store raw owner feedback, then ask the memory backend to process it.

    The raw text is persisted FIRST (T5) so a retry carrying the same
    ``Idempotency-Key`` header reuses the stored feedback id and never submits
    twice. The honest lifecycle is decided by the memory backend: locally it stays
    ``saved`` (nothing is extracted), so it is never reported as ``available``.
    """

    repo = _repository(request)
    settings = _settings(request)
    memory = _memory(request)
    conversation_id = session.conversation_id
    record = repo.save_feedback(
        owner_id=session.owner_id,
        pet_id=DEMO_PET_ID,
        text=body.text,
        scope=body.scope,
        memory_status="saved",
        memory_backend=settings.effective_memory_backend,
        conversation_id=conversation_id,
        idempotency_key=request.headers.get("Idempotency-Key"),
    )
    # Only a never-submitted record is offered to the backend, so an idempotent
    # retry cannot re-send the same feedback to AgentCore.
    if record.agentcore_event_id is None:
        try:
            result = memory.submit_feedback(
                feedback_id=record.feedback_id,
                owner_id=session.owner_id,
                pet_id=DEMO_PET_ID,
                text=body.text,
                scope=body.scope,
                conversation_id=conversation_id,
            )
        except MemoryUnavailable:
            # The raw feedback is already saved; only the extraction submission
            # failed. Report the honest 'failed' lifecycle instead of a 500, and
            # never fall back to claiming a memory was created (AGENTS.md L18/L22).
            failed = repo.set_feedback_status(record.feedback_id, memory_status="failed")
            return _feedback_view(failed if failed is not None else record)
        if (
            result.memory_status != record.memory_status
            or result.agentcore_event_id is not None
            or result.memory_record_ids
        ):
            updated = repo.set_feedback_status(
                record.feedback_id,
                memory_status=result.memory_status,
                agentcore_event_id=result.agentcore_event_id,
                memory_record_ids=result.memory_record_ids or None,
            )
            if updated is not None:
                record = updated
    return _feedback_view(record)


@router.get(
    "/api/feedback/{feedback_id}",
    response_model=FeedbackView,
    responses=_responses(401, 404),
)
def get_feedback(feedback_id: UUID, request: Request, session: SessionDep) -> FeedbackView:
    record = _repository(request).get_feedback(feedback_id)
    if record is None or record.owner_id != session.owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FEEDBACK_NOT_FOUND")
    return _feedback_view(record)
