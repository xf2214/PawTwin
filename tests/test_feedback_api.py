"""Owner-feedback and new-session API tests (Day-3 gates G1/G2/G4).

These run against the real HTTP API in local mode with the honest
``not_implemented`` memory backend. They prove the LOCAL contract only: raw
feedback is saved, its status never claims extraction, and a new session rotates
the conversation without touching login/facts/memory. Real AgentCore extraction and
cross-session retrieval are CONDITION items (see day3-cloud-blocked.md).
"""

from uuid import uuid4

from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app
from pawtwin.memory import MemoryUnavailable


def _headers(login) -> dict[str, str]:
    return {"X-CSRF-Token": login()}


def _feedback(
    text: str = "I notice she looks for play after meals.", scope: str = "observation"
) -> dict[str, str]:
    return {"text": text, "scope": scope}


# --- auth boundaries (A12) ---------------------------------------------------


def test_feedback_and_new_session_require_a_session(client: TestClient) -> None:
    assert client.post("/api/feedback", json=_feedback()).status_code == 401
    assert client.get(f"/api/feedback/{uuid4()}").status_code == 401
    assert client.post("/api/demo/new-session").status_code == 401


def test_feedback_and_new_session_require_csrf(client: TestClient, login) -> None:
    login()
    assert client.post("/api/feedback", json=_feedback()).status_code == 403
    assert client.post("/api/demo/new-session").status_code == 403


# --- honest lifecycle (G2, A06/A07 structure) --------------------------------


def test_submitting_an_observation_saves_the_raw_text_without_claiming_extraction(
    client: TestClient, login
) -> None:
    headers = _headers(login)

    response = client.post("/api/feedback", json=_feedback(), headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "observation"
    assert body["text"] == "I notice she looks for play after meals."
    # ``saved`` = raw stored. NEVER ``available``/``processing`` locally, and the
    # backend label makes that unambiguous (AGENTS.md L18).
    assert body["memory_status"] == "saved"
    assert body["memory_backend"] == "not_implemented"
    assert body["feedback_id"]
    # owner_id / idempotency_key stay internal, like RunRecord's bookkeeping.
    assert "owner_id" not in body
    assert "idempotency_key" not in body


def test_today_only_feedback_is_saved_but_never_a_permanent_preference(
    client: TestClient, login
) -> None:
    headers = _headers(login)

    body = client.post(
        "/api/feedback", json=_feedback(text="she seems restless tonight", scope="today_only"),
        headers=headers,
    ).json()

    assert body["scope"] == "today_only"
    assert body["memory_status"] == "saved"
    assert body["memory_backend"] == "not_implemented"


def test_feedback_is_readable_by_id(client: TestClient, login) -> None:
    headers = _headers(login)
    created = client.post("/api/feedback", json=_feedback(), headers=headers).json()

    fetched = client.get(f"/api/feedback/{created['feedback_id']}")

    assert fetched.status_code == 200
    assert fetched.json()["feedback_id"] == created["feedback_id"]
    assert fetched.json()["memory_status"] == "saved"


def test_unknown_feedback_id_is_a_404(client: TestClient, login) -> None:
    _headers(login)
    assert client.get(f"/api/feedback/{uuid4()}").status_code == 404


def test_feedback_rejects_an_invalid_body(client: TestClient, login) -> None:
    headers = _headers(login)
    # Empty text (after strip) violates min_length=1.
    blank = client.post("/api/feedback", json=_feedback(text="   "), headers=headers)
    assert blank.status_code == 422
    # An unknown scope is forbidden by the frozen contract.
    bad_scope = client.post(
        "/api/feedback", json={"text": "hi", "scope": "forever"}, headers=headers
    )
    assert bad_scope.status_code == 422
    # extra='forbid': an unexpected field is rejected.
    extra = client.post(
        "/api/feedback",
        json={"text": "hi", "scope": "observation", "owner_id": "someone-else"},
        headers=headers,
    )
    assert extra.status_code == 422


def test_an_idempotency_key_reuses_the_same_feedback_and_never_duplicates(
    client: TestClient, login
) -> None:
    """T5: a retry reuses the local feedback id, so one observation is never stored
    (or later submitted to AgentCore) twice."""

    headers = _headers(login)
    headers["Idempotency-Key"] = "key-1"

    first = client.post("/api/feedback", json=_feedback(), headers=headers).json()
    retry = client.post("/api/feedback", json=_feedback(), headers=headers).json()

    assert first["feedback_id"] == retry["feedback_id"]

    headers["Idempotency-Key"] = "key-2"
    other = client.post("/api/feedback", json=_feedback(), headers=headers).json()
    assert other["feedback_id"] != first["feedback_id"]


# --- new session (G4, A06 cross-session plumbing) ----------------------------


def test_new_session_rotates_the_conversation_and_preserves_state(
    client: TestClient, login
) -> None:
    headers = _headers(login)
    before = client.get("/api/state").json()
    client.post("/api/demo/facts", json={"last_fed_minutes_ago": 42}, headers=headers)
    facts_before = client.get("/api/state").json()["facts"]

    response = client.post("/api/demo/new-session", headers=headers)

    assert response.status_code == 200
    new_conversation = response.json()["conversation_id"]
    assert new_conversation and new_conversation != before["conversation_id"]
    after = client.get("/api/state").json()
    # The conversation rotated, but login, facts and the memory label are intact.
    assert after["conversation_id"] == new_conversation
    assert after["facts"] == facts_before
    assert after["memory"] == "not_implemented"
    assert after["aws_connected"] is False

    client.post("/api/demo/facts", json={"reset": True}, headers=headers)


def test_state_exposes_a_conversation_id_and_the_memory_label(
    client: TestClient, login
) -> None:
    _headers(login)

    state = client.get("/api/state").json()

    assert state["memory"] == "not_implemented"
    assert isinstance(state["conversation_id"], str) and state["conversation_id"]


def test_feedback_records_the_conversation_it_was_submitted_in(
    client: TestClient, login
) -> None:
    headers = _headers(login)
    conversation = client.get("/api/state").json()["conversation_id"]

    body = client.post("/api/feedback", json=_feedback(), headers=headers).json()

    assert body["conversation_id"] == conversation


def test_a_memory_submission_failure_is_reported_as_failed_not_a_500() -> None:
    """If a real memory backend cannot be reached, the raw feedback is still saved
    and the lifecycle honestly reads ``failed`` -- never a 500, and never a fake
    memory. Only reachable when an operator selects ``agentcore`` without creds."""

    class _RaisingMemory:
        label = "agentcore"

        def submit_feedback(self, **kwargs: object) -> object:
            raise MemoryUnavailable("MEMORY_UNAVAILABLE: SUBMIT_FAILED Probe")

        def get_status(self, feedback_id: object, *, agentcore_event_id: object = None) -> str:
            return "failed"

        def search(self, *, owner_id: str, pet_id: str, query: str) -> list:
            return []

    app = create_app(Settings(_env_file=None))
    with TestClient(app) as raising_client:
        app.state.memory = _RaisingMemory()
        passphrase = Settings(_env_file=None).demo_passphrase
        token = raising_client.post(
            "/api/login", json={"passphrase": passphrase}
        ).json()["csrf_token"]

        response = raising_client.post(
            "/api/feedback",
            json=_feedback(text="probe observation"),
            headers={"X-CSRF-Token": token},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["memory_status"] == "failed"
        assert body["text"] == "probe observation"  # the raw text is still saved
        fetched = raising_client.get(f"/api/feedback/{body['feedback_id']}").json()
        assert fetched["memory_status"] == "failed"
