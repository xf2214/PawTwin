import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from pawtwin import api, care_access, family_api, home_api
from pawtwin.agent import AnalyzerProposer, build_analyzer
from pawtwin.auth import AuthService, LoginRateLimiter
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.family_assistant import BedrockConverseService, FamilyAssistant, ModelLedger
from pawtwin.family_store import FamilyStore, LegacyHomeView
from pawtwin.family_worker import FamilyReportWorker
from pawtwin.home_store import HomeStore
from pawtwin.memory import MemoryService, build_memory
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.repository import Repository
from pawtwin.worker import AnalysisWorker, MemoryPoller
from pawtwin.workflow import AnalysisGuard, InlineProposer, Proposer, Workflow


def _default_frontend_dist() -> Path:
    configured = os.getenv("PAWTWIN_FRONTEND_DIST")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _build_proposer(
    settings: Settings, repository: Repository, memory: MemoryService
) -> Proposer:
    """Select the analyzer backend. Never a silent fallback between them.

    ``inline`` is the deterministic test backend; ``local_fake`` is the labelled
    stand-in; ``bedrock`` is the real model and fails visibly when unavailable. The
    memory service is threaded into the analyzer adapters so ``search_owner_memory``
    reads the SAME injected backend (ruling 1); the inline test backend retrieves
    nothing and cites no evidence.
    """

    backend = settings.effective_model_backend
    if backend == "inline":
        return InlineProposer()
    return AnalyzerProposer(
        build_analyzer(settings, repository),
        repository,
        memory=memory,
        max_model_calls=settings.max_model_calls_per_run,
        max_output_tokens=settings.max_output_tokens,
        timeout_seconds=settings.analysis_timeout_seconds,
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    reporter = getattr(app.state, "family_reporter", None)
    if reporter is not None:
        reporter.start()
    worker: AnalysisWorker | None = getattr(app.state, "worker", None)
    if worker is not None:
        worker.start()
    poller: MemoryPoller | None = getattr(app.state, "memory_poller", None)
    if poller is not None:
        poller.start()
    try:
        yield
    finally:
        if reporter is not None:
            reporter.stop()
        # Order matters: stop the background threads BEFORE closing the repository,
        # otherwise a final pass would touch a closed database. Then release the
        # deadline pool without waiting, so a runaway model call can never block exit.
        if poller is not None:
            poller.stop()
        if worker is not None:
            worker.stop()
        guard: AnalysisGuard | None = getattr(app.state, "guard", None)
        if guard is not None:
            guard.shutdown()
        repository = getattr(app.state, "repository", None)
        if repository is not None:
            repository.close()
        home_store = getattr(app.state, "home_store", None)
        if home_store is not None:
            home_store.close()
        family_store = getattr(app.state, "family_store", None)
        if family_store is not None:
            family_store.close()
        source = getattr(app.state, "legacy_source_store", None)
        if source is not None:
            source.close()


def create_app(
    settings: Settings | None = None,
    *,
    frontend_dist: Path | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()

    app = FastAPI(title="PawTwin", version="0.1.0", lifespan=_lifespan)

    # Storage and memory are assembled per mode. Day-5 ruling 7 REMOVES the old
    # unconditional ``mode=aws`` rejection: aws now builds the real adapters and does
    # a read-only, zero-cost startup probe. State is built synchronously so it is
    # available even to TestClient instances that never enter the lifespan, and
    # nothing here starts a thread (worker/poller threads start only inside the
    # lifespan), which keeps the offline contract export deterministic/side-effect
    # free (the export always pins mode=local, so boto3 is never imported there).
    if resolved_settings.mode == "aws":
        from pawtwin.repo_dynamo import DynamoRepository  # lazy: boto3 stays out of local/CI

        repository: Repository = DynamoRepository(
            resolved_settings.dynamodb_table_name or "",
            region=resolved_settings.aws_region,
            owner_id=DEMO_OWNER_ID,
        )
        storage_label = "dynamodb"
        memory = build_memory(resolved_settings)  # AgentCoreMemory in aws mode
        # Read-only, ZERO-COST probe (ruling 7): DynamoDB GetItem + AgentCore
        # GetMemory. Bedrock is NOT probed (Converse is billable); its connectivity is
        # proven later by a real request_id. A probe failure raises, so create_app
        # refuses to start and surfaces the real reason -- it NEVER falls back to a
        # stand-in (AGENTS.md L22).
        repository.probe()  # type: ignore[attr-defined]  # DynamoRepository in aws mode
        memory.probe()  # type: ignore[attr-defined]  # AgentCoreMemory in aws mode
        # GetItem/GetMemory prove component access only. There is no Bedrock
        # inference proof, correlated memory-extraction completion, or family cloud
        # store yet. Do not upgrade the whole product based on configuration.
        aws_connected = False
    else:
        repository = SqliteRepository(
            resolved_settings.database_path or ":memory:",
            owner_id=DEMO_OWNER_ID,
        )
        storage_label = "sqlite"
        memory = build_memory(resolved_settings)
        # The Settings layer does no IO, so local mode can never assert a cloud
        # connection (ruling 8): the real flag lives on app.state, computed above.
        aws_connected = False
    device = DeviceSimulator()
    guard = AnalysisGuard(resolved_settings.analysis_timeout_seconds)
    workflow = Workflow(
        repository,
        device,
        proposer=_build_proposer(resolved_settings, repository, memory),
        guard=guard,
        lease_seconds=resolved_settings.lease_seconds,
        max_attempts=resolved_settings.max_attempts,
    )
    app.state.settings = resolved_settings
    app.state.repository = repository
    app.state.home_store = (
        HomeStore(resolved_settings.database_path or ":memory:")
        if resolved_settings.mode == "local" else None
    )
    path = resolved_settings.database_path
    app.state.family_store = (
        FamilyStore(path + ".family.db" if path and path != ":memory:" else ":memory:")
        if resolved_settings.mode == "local" else None
    )
    app.state.family_reporter = (
        FamilyReportWorker(app.state.family_store) if app.state.family_store else None
    )
    app.state.bedrock_client = None  # SDK client is lazy; local mode never imports it.
    app.state.family_model_ledger = ModelLedger(app.state.family_store, resolved_settings)
    app.state.family_model_service = BedrockConverseService(app, app.state.family_model_ledger)
    app.state.family_assistant = FamilyAssistant(resolved_settings, app.state.family_model_service)
    app.state.care_access_limiter = care_access.CareAccessLimiter()
    app.state.legacy_source_store = app.state.home_store
    if app.state.family_store is not None:
        app.state.family_store.device_source = app.state.legacy_source_store
        app.state.home_store = LegacyHomeView(app.state.family_store, app.state.legacy_source_store)
    app.state.aws_connected = aws_connected
    app.state.storage_label = storage_label
    app.state.device = device
    app.state.memory = memory
    app.state.auth = AuthService(
        demo_passphrase=resolved_settings.demo_passphrase,
        owner_id=DEMO_OWNER_ID,
        ttl_seconds=resolved_settings.session_ttl_seconds,
        idle_seconds=resolved_settings.session_idle_seconds,
    )
    # Day-5 ruling 4c: the login throttle is process-local state, built here (no
    # thread, no side effect) so create_app stays deterministic for the offline
    # contract export.
    app.state.login_limiter = LoginRateLimiter(
        max_failures=resolved_settings.login_max_failures,
        backoff_seconds=resolved_settings.login_backoff_seconds,
    )
    app.state.registration_limiter = LoginRateLimiter(max_failures=30, backoff_seconds=60)
    app.state.workflow = workflow
    app.state.guard = guard
    app.state.worker = (
        AnalysisWorker(repository, workflow, resolved_settings)
        if resolved_settings.worker_mode == "background"
        else None
    )
    # Day-5 ruling 11: the extraction poller runs ONLY for the real AgentCore backend
    # and only in background mode, so create_app stays thread-free for the offline
    # contract export. In local mode memory is not_implemented -> this is None and
    # nothing polls, so a locally-saved feedback never advances to available.
    app.state.memory_poller = (
        MemoryPoller(repository, memory)
        if resolved_settings.worker_mode == "background"
        and resolved_settings.effective_memory_backend == "agentcore"
        else None
    )

    @app.middleware("http")
    async def private_care_responses(request, call_next):
        path = request.url.path
        private = path.startswith("/api/care-access/") or (
            path.startswith("/api/family/pets/")
            and ("/care-access" in path or path.endswith("/visit-summary"))
        )
        try:
            response = await call_next(request)
        except Exception:
            if not private:
                raise
            response = JSONResponse(status_code=500, content={"detail": "Care data unavailable"})
        if private:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/readyz", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    def readyz(response: Response) -> dict[str, Any]:
        # Container liveness uses /healthz. Product readiness requires verified
        # inference, extraction and family storage, beyond read-only startup probes.
        if app.state.aws_connected:
            response.status_code = status.HTTP_200_OK
            return {
                "status": "ready",
                "reason": "cloud_adapters_verified",
                "business": "ready",
                "model": resolved_settings.effective_model_backend,
                "storage": f"{app.state.storage_label}_connected",
                "memory": resolved_settings.effective_memory_backend,
                "cloud": "verified",
            }
        if resolved_settings.mode == "aws":
            return {
                "status": "degraded",
                "reason": "cloud_end_to_end_not_verified",
                "business": "cloud_components_only",
                "model": resolved_settings.effective_model_backend,
                "storage": f"{app.state.storage_label}_connected",
                "memory": resolved_settings.effective_memory_backend,
                "cloud": "not_verified",
                "verification": {
                    "model_inference": "not_verified",
                    "memory_extraction": "unsupported",
                    "family": "not_connected",
                },
            }
        # Local / unverified: component-honest degraded. The local business loop IS
        # ready; what is missing is any verified cloud adapter.
        return {
            "status": "degraded",
            "reason": "cloud_adapters_not_verified",
            "business": "ready_local",
            "model": resolved_settings.effective_model_backend,
            "storage": "sqlite_local",
            "memory": resolved_settings.effective_memory_backend,
            "cloud": "not_verified",
        }

    @app.get("/api/bootstrap")
    def bootstrap() -> dict[str, Any]:
        return {
            "project": "PawTwin",
            "stage": (
                "aws_business" if app.state.aws_connected
                else "aws_components" if resolved_settings.mode == "aws"
                else "local_business"
            ),
            "mode": resolved_settings.mode,
            "aws_connected": app.state.aws_connected,
            "analyzer": resolved_settings.effective_model_backend,
            "capabilities": {
                "event_intake": "implemented_local",
                "owner_approval": "implemented_local",
                "simulated_device": "implemented_simulated",
                # Day-3: raw owner feedback is really saved locally, but LONG-TERM
                # extraction/retrieval is AgentCore and stays unimplemented without
                # an account -- kept separate so "saved" is never read as "extracted".
                "owner_feedback": "implemented_local",
                "long_term_memory": resolved_settings.effective_memory_backend,
            },
        }

    # Business API router is registered BEFORE the catch-all static mount so any
    # unknown /api/* path still returns a JSON 404 instead of the SPA HTML.
    app.include_router(api.router)
    app.include_router(home_api.router)
    app.include_router(family_api.router)
    app.include_router(care_access.router)

    static_root = (frontend_dist or _default_frontend_dist()).resolve()
    if (static_root / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")

    return app
