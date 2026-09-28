import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles

from pawtwin import api
from pawtwin.agent import AnalyzerProposer, build_analyzer
from pawtwin.auth import AuthService
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.memory import MemoryService, build_memory
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.repository import Repository
from pawtwin.worker import AnalysisWorker
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
    worker: AnalysisWorker | None = getattr(app.state, "worker", None)
    if worker is not None:
        worker.start()
    try:
        yield
    finally:
        # Order matters: stop the worker BEFORE closing the repository, otherwise a
        # final pass would touch a closed database. Then release the deadline pool
        # without waiting, so a runaway model call can never block process exit.
        if worker is not None:
            worker.stop()
        guard: AnalysisGuard | None = getattr(app.state, "guard", None)
        if guard is not None:
            guard.shutdown()
        repository = getattr(app.state, "repository", None)
        if repository is not None:
            repository.close()


def create_app(
    settings: Settings | None = None,
    *,
    frontend_dist: Path | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    if resolved_settings.mode == "aws":
        raise NotImplementedError("AWS adapters are not implemented; use PAWTWIN_MODE=local")

    app = FastAPI(title="PawTwin", version="0.1.0", lifespan=_lifespan)

    # Local application state is built synchronously so it is available even to
    # TestClient instances that never enter the lifespan context. Nothing here
    # starts a thread: the worker thread only starts inside the lifespan, which
    # keeps the offline contract export deterministic and side-effect free.
    repository = SqliteRepository(
        resolved_settings.database_path or ":memory:",
        owner_id=DEMO_OWNER_ID,
    )
    device = DeviceSimulator()
    guard = AnalysisGuard(resolved_settings.analysis_timeout_seconds)
    memory = build_memory(resolved_settings)
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
    app.state.device = device
    app.state.memory = memory
    app.state.auth = AuthService(
        demo_passphrase=resolved_settings.demo_passphrase,
        owner_id=DEMO_OWNER_ID,
    )
    app.state.workflow = workflow
    app.state.guard = guard
    app.state.worker = (
        AnalysisWorker(repository, workflow, resolved_settings)
        if resolved_settings.worker_mode == "background"
        else None
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/readyz", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    def readyz() -> dict[str, Any]:
        # Still degraded, but component-honest: the local business loop IS ready,
        # what is missing is any verified cloud adapter. Reporting "business not
        # ready" now would understate the truth just as much as overstating it.
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
            "stage": "local_business",
            "mode": resolved_settings.mode,
            "aws_connected": resolved_settings.aws_connected,
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

    static_root = (frontend_dist or _default_frontend_dist()).resolve()
    if (static_root / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")

    return app
