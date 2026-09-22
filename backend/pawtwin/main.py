import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles

from pawtwin.config import Settings


def _default_frontend_dist() -> Path:
    configured = os.getenv("PAWTWIN_FRONTEND_DIST")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app(
    settings: Settings | None = None,
    *,
    frontend_dist: Path | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    if resolved_settings.mode == "aws":
        raise NotImplementedError("AWS adapters are not implemented; use PAWTWIN_MODE=local")

    app = FastAPI(title="PawTwin", version="0.1.0")

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

    static_root = (frontend_dist or _default_frontend_dist()).resolve()
    if (static_root / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_root, html=True), name="frontend")

    return app
