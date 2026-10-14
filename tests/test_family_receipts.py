from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app
from test_family_extension import write


def test_successful_simulator_receipt_is_reported_separately_from_intake(tmp_path):
    app = create_app(Settings(_env_file=None, database_path=str(tmp_path / "receipts.db")))
    client = TestClient(app)
    csrf = client.post("/api/login", json={"passphrase": "local-demo-passphrase"}).json()[
        "csrf_token"
    ]
    client.headers["x-csrf-token"] = csrf
    client.get("/api/family/me")
    client.post("/api/demo/facts", json={"reset": True})
    accepted = client.post(
        "/api/events", json={"event_id": str(uuid4()), "kind": "food_request", "room": "kitchen"}
    ).json()
    run = client.get(f"/api/runs/{accepted['run_id']}").json()
    assert run["state"] == "awaiting_approval"
    approved = client.post(
        f"/api/runs/{run['run_id']}/approval",
        json={
            "decision": "approve",
            "proposal_version": run["proposal_version"],
            "action_digest": run["action_digest"],
        },
    )
    assert approved.status_code == 200 and approved.json()["state"] == "succeeded"
    report = write(
        client,
        "/api/family/pets/mochi/reports/generate",
        period="daily",
        date=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
    )
    assert report["care"]["device_success"] == 1
    assert report["diet"]["simulated_device_dispensed_g"] == run["proposal"]["action"]["grams"]
    assert report["diet"]["actual_intake_g"] is None
