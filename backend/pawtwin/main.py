import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles

from pawtwin import api
from pawtwin.auth import AuthService
from pawtwin.config import Settings
from pawtwin.device_sim import DeviceSimulator
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pawtwin.workflow import Workflow


def _default_frontend_dist() -> Path:
    configured = os.getenv("PAWTWIN_FRONTEND_DIST")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
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
    # TestClient instances that never enter the lifespan context.
    repository = SqliteRepository(
        resolved_settings.database_path or ":memory:",
        owner_id=DEMO_OWNER_ID,
    )
    device = DeviceSimulator()
    app.state.settings = resolved_settings
    app.state.repository = repository
    app.state.device = device
    app.state.auth = AuthService(
        demo_passphrase=resolved_settings.demo_passphrase,
        owner_id=DEMO_OWNER_ID,
    )
    app.state.workflow = Workflow(repository, device)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/readyz", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    def readyz() -> dict[str, str]:
        return {
            "status": "degraded",
            "reason": "scaffold_business_not_ready",
        }

    @app.get("/api/bootstrap")
    def bootstrap() -> dict[str, Any]:
        return {
            "project": "PawTwin",
            "stage": "scaffold",
            "mode": resolved_settings.mode,
            "aws_connected": resolved_settings.aws_connected,
            "capabilities": {
                "event_intake": "planned",
                "owner_approval": "planned",
                "simulated_device": "planned",
                "long_term_memory": "planned",
            },
        }

    # Business API router is registered BEFORE the catch-all static mount so any
    # unknown /api/* path still returns a JSON 404 instead of the SPA HTML.
    app.include_router(api.router)

    static_root = (frontend_dist or _default_frontend_dist()).resolve()
    if (static_root / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")

    return app
