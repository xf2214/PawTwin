import json
from pathlib import Path

from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app


def test_status_endpoints_report_scaffold_truthfully() -> None:
    client = TestClient(create_app(Settings()))

    assert client.get("/healthz").json() == {"status": "live"}
    readiness = client.get("/readyz")
    assert readiness.status_code == 503
    assert readiness.json() == {
        "status": "degraded",
        "reason": "scaffold_business_not_ready",
    }


def test_bootstrap_is_public_and_contains_only_non_sensitive_scaffold_state() -> None:
    settings = Settings(
        BEDROCK_MODEL_ID="must-not-leak",
        AWS_REGION="us-east-1",
        DYNAMODB_TABLE_NAME="must-not-leak",
        AGENTCORE_MEMORY_ID="must-not-leak",
    )
    response = TestClient(create_app(settings)).get("/api/bootstrap")

    assert response.status_code == 200
    assert response.json() == {
        "project": "PawTwin",
        "stage": "scaffold",
        "mode": "local",
        "aws_connected": False,
        "capabilities": {
            "event_intake": "planned",
            "owner_approval": "planned",
            "simulated_device": "planned",
            "long_term_memory": "planned",
        },
    }
    body = response.text
    assert "must-not-leak" not in body
    assert "us-east-1" not in body


def test_static_frontend_serves_root_without_turning_api_404s_into_html(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<main>PawTwin shell</main>", encoding="utf-8")
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")
    client = TestClient(create_app(Settings(), frontend_dist=tmp_path))

    assert client.get("/").text == "<main>PawTwin shell</main>"
    assert client.get("/asset.txt").text == "asset"
    unknown_api = client.get("/api/runs")
    assert unknown_api.status_code == 404
    assert unknown_api.headers["content-type"].startswith("application/json")
    assert json.loads(unknown_api.text) == {"detail": "Not Found"}
    assert client.get("/future-page").status_code == 404


def test_business_routes_keep_unknown_api_json_and_require_auth(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<main>PawTwin</main>", encoding="utf-8")
    client = TestClient(create_app(Settings(), frontend_dist=tmp_path))

    # /api/runs/{run_id} now exists, but the bare collection path must still be a
    # JSON 404 (router registered before the catch-all static mount).
    bare = client.get("/api/runs")
    assert bare.status_code == 404
    assert bare.headers["content-type"].startswith("application/json")
    assert json.loads(bare.text) == {"detail": "Not Found"}

    # A well-formed run id is protected: unauthenticated access is 401, not 404,
    # so existence is never leaked without a session.
    guarded = client.get("/api/runs/00000000-0000-0000-0000-000000000000")
    assert guarded.status_code == 401
