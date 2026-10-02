import json
import threading
from pathlib import Path

from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app


def test_status_endpoints_report_component_honest_readiness() -> None:
    client = TestClient(create_app(Settings(_env_file=None)))

    assert client.get("/healthz").json() == {"status": "live"}
    readiness = client.get("/readyz")
    # Still degraded (no cloud adapter is verified), but no longer claiming the
    # business loop is missing: understating readiness is a distortion too.
    assert readiness.status_code == 503
    assert readiness.json() == {
        "status": "degraded",
        "reason": "cloud_adapters_not_verified",
        "business": "ready_local",
        "model": "local_fake",
        "storage": "sqlite_local",
        "memory": "not_implemented",
        "cloud": "not_verified",
    }


def test_readyz_maps_a_verified_probe_to_200_not_a_perpetual_503() -> None:
    """Day-5 ruling 9 MAPPING test: when create_app's startup probe marked the cloud
    connected, /readyz returns 200 ``{status: ready}`` instead of understating with a
    perpetual 503 (a low-report is a distortion too). This injects the probe RESULT
    directly onto app.state -- it is a mapping-logic test, NOT cloud evidence: no real
    probe ran, and the LB/HEALTHCHECK still use /healthz (never /readyz). The local
    503 assertion above is unchanged.
    """

    app = create_app(Settings(_env_file=None))
    try:
        # Simulate a verified aws assembly; the real values come from create_app's probe.
        app.state.aws_connected = True
        app.state.storage_label = "dynamodb"
        ready = TestClient(app).get("/readyz")
        assert ready.status_code == 200
        body = ready.json()
        assert body["status"] == "ready"
        assert body["cloud"] == "verified"
        assert body["storage"] == "dynamodb_connected"
    finally:
        app.state.repository.close()


def test_bootstrap_is_public_and_contains_only_non_sensitive_state() -> None:
    settings = Settings(
        _env_file=None,
        BEDROCK_MODEL_ID="must-not-leak",
        AWS_REGION="us-east-1",
        DYNAMODB_TABLE_NAME="must-not-leak",
        AGENTCORE_MEMORY_ID="must-not-leak",
    )
    response = TestClient(create_app(settings)).get("/api/bootstrap")

    assert response.status_code == 200
    assert response.json() == {
        "project": "PawTwin",
        "stage": "local_business",
        "mode": "local",
        "aws_connected": False,
        "analyzer": "local_fake",
        "capabilities": {
            "event_intake": "implemented_local",
            "owner_approval": "implemented_local",
            "simulated_device": "implemented_simulated",
            "owner_feedback": "implemented_local",
            "long_term_memory": "not_implemented",
        },
    }
    body = response.text
    assert "must-not-leak" not in body
    assert "us-east-1" not in body


def test_static_frontend_serves_root_without_turning_api_404s_into_html(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<main>PawTwin shell</main>", encoding="utf-8")
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")
    client = TestClient(create_app(Settings(_env_file=None), frontend_dist=tmp_path))

    assert client.get("/").text == "<main>PawTwin shell</main>"
    assert client.get("/asset.txt").text == "asset"
    unknown_api = client.get("/api/runs")
    assert unknown_api.status_code == 404
    assert unknown_api.headers["content-type"].startswith("application/json")
    assert json.loads(unknown_api.text) == {"detail": "Not Found"}
    assert client.get("/future-page").status_code == 404


def test_business_routes_keep_unknown_api_json_and_require_auth(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<main>PawTwin</main>", encoding="utf-8")
    client = TestClient(create_app(Settings(_env_file=None), frontend_dist=tmp_path))

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


def test_create_app_is_side_effect_free_and_starts_no_worker_thread() -> None:
    """The offline contract export calls create_app directly, outside any lifespan.

    A thread started here would make the export non-deterministic and could hang
    CI, so the worker only starts inside the lifespan.
    """

    before = threading.active_count()
    app = create_app(Settings(_env_file=None, worker_mode="background"))
    try:
        assert threading.active_count() == before
        assert app.state.worker is not None
        assert app.state.worker.running is False
    finally:
        app.state.repository.close()
