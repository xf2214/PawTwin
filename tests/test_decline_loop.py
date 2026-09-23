"""Day-1 必过 integration evidence: the decline loop over the real HTTP API.

This is the plan's guaranteed fallback evidence (httpx/TestClient) for the
decline loop, independent of the browser e2e. It exercises login -> event ->
awaiting_approval -> decline -> durable DECLINED with zero execution, plus the
best-effort approve loop and event de-duplication.
"""

from uuid import uuid4

from fastapi.testclient import TestClient


def _food_event() -> dict[str, object]:
    return {
        "event_id": str(uuid4()),
        "kind": "food_request",
        "room": "kitchen",
        "note": "Mochi is waiting near the bowl.",
    }


def test_decline_loop_is_durable_and_executes_nothing(client: TestClient, login) -> None:
    headers = {"X-CSRF-Token": login()}
    grams_before = client.get("/api/state").json()["facts"]["daily_dispensed_grams"]

    accepted = client.post("/api/events", json=_food_event(), headers=headers)
    assert accepted.status_code == 202
    body = accepted.json()
    assert body["state"] == "awaiting_approval"
    run_id = body["run_id"]

    run = client.get(f"/api/runs/{run_id}").json()
    assert run["state"] == "awaiting_approval"
    assert run["proposal"]["action"]["kind"] == "dispense_food"

    decline = {
        "decision": "decline",
        "proposal_version": run["proposal_version"],
        "action_digest": run["action_digest"],
    }
    declined = client.post(f"/api/runs/{run_id}/approval", json=decline, headers=headers)
    assert declined.status_code == 200
    assert declined.json()["state"] == "declined"

    # "Reload": a fresh read still shows declined, with no receipt and no quota use.
    again = client.get(f"/api/runs/{run_id}").json()
    assert again["state"] == "declined"
    assert again["receipt"] is None

    state = client.get("/api/state").json()
    assert state["facts"]["daily_dispensed_grams"] == grams_before
    assert any(r["run_id"] == run_id and r["state"] == "declined" for r in state["runs"])

    # A repeated decline is refused (no longer awaiting) but the state stays declined.
    repeat = client.post(f"/api/runs/{run_id}/approval", json=decline, headers=headers)
    assert repeat.status_code == 409
    assert client.get(f"/api/runs/{run_id}").json()["state"] == "declined"


def test_approve_loop_executes_once_with_a_simulated_receipt(client: TestClient, login) -> None:
    headers = {"X-CSRF-Token": login()}

    run_id = client.post("/api/events", json=_food_event(), headers=headers).json()["run_id"]
    run = client.get(f"/api/runs/{run_id}").json()
    grams = run["proposal"]["action"]["grams"]

    approve = {
        "decision": "approve",
        "proposal_version": run["proposal_version"],
        "action_digest": run["action_digest"],
    }
    result = client.post(f"/api/runs/{run_id}/approval", json=approve, headers=headers)
    assert result.status_code == 200
    payload = result.json()
    assert payload["state"] == "succeeded"
    assert payload["receipt"]["status"] == "succeeded"
    assert payload["receipt"]["simulated"] is True

    facts = client.get("/api/state").json()["facts"]
    assert facts["daily_dispensed_grams"] == grams
    assert facts["last_fed_minutes_ago"] == 0

    # A second approval is refused and never double-accounts (single logical receipt).
    replay = client.post(f"/api/runs/{run_id}/approval", json=approve, headers=headers)
    assert replay.status_code == 409
    assert client.get("/api/state").json()["facts"]["daily_dispensed_grams"] == grams


def test_event_redelivery_returns_the_same_run(client: TestClient, login) -> None:
    headers = {"X-CSRF-Token": login()}
    event = _food_event()

    first = client.post("/api/events", json=event, headers=headers).json()
    second = client.post("/api/events", json=event, headers=headers).json()

    assert first["run_id"] == second["run_id"]
    runs = client.get("/api/state").json()["runs"]
    assert sum(1 for run in runs if run["run_id"] == first["run_id"]) == 1
