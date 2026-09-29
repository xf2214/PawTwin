from uuid import uuid4

from fastapi.testclient import TestClient
from pawtwin.config import Settings
from pawtwin.main import create_app


def _event() -> dict[str, object]:
    return {"event_id": str(uuid4()), "kind": "food_request", "room": "kitchen"}


def test_business_api_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/state").status_code == 401
    assert client.post("/api/events", json=_event()).status_code == 401
    assert client.get(f"/api/runs/{uuid4()}").status_code == 401


def test_login_rejects_wrong_passphrase(client: TestClient) -> None:
    response = client.post("/api/login", json={"passphrase": "definitely-wrong"})

    assert response.status_code == 401
    assert client.get("/api/state").status_code == 401


def test_login_sets_httponly_samesite_session_and_returns_csrf(client: TestClient) -> None:
    response = client.post("/api/login", json={"passphrase": Settings().demo_passphrase})

    assert response.status_code == 200
    assert response.json()["csrf_token"]
    cookie = response.headers.get("set-cookie", "")
    assert "pawtwin_session" in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()
    # Local HTTP omits ONLY the Secure flag; it is never sent over plain HTTP.
    # Secure is bound to the CONNECTION, not to PAWTWIN_MODE: see the paired test
    # below (Day-4 ruling 5).
    assert "secure" not in cookie.lower()


def test_writes_require_a_matching_csrf_token(client: TestClient, login) -> None:
    csrf = login()

    # Authenticated but no CSRF header -> 403.
    assert client.post("/api/events", json=_event()).status_code == 403
    # Wrong CSRF token -> 403.
    wrong = client.post("/api/events", json=_event(), headers={"X-CSRF-Token": "not-the-token"})
    assert wrong.status_code == 403
    # Correct CSRF token -> accepted.
    ok = client.post("/api/events", json=_event(), headers={"X-CSRF-Token": csrf})
    assert ok.status_code == 202


def test_logout_revokes_the_session(client: TestClient, login) -> None:
    login()
    assert client.get("/api/state").status_code == 200

    assert client.post("/api/logout").status_code == 204
    assert client.get("/api/state").status_code == 401


def test_approval_is_gated_by_session_then_csrf(client: TestClient, login) -> None:
    """A12: the only write that can dispense food must be unreachable unauthenticated.

    Day-4 found this route had NO 401 and NO 403 assertion at all, while every other
    write route had both. The gate order is asserted too: an unknown run must yield
    401 (not 404) before login, so an unauthenticated caller cannot probe which runs
    exist.
    """

    run = f"/api/runs/{uuid4()}/approval"
    body = {"decision": "approve", "proposal_version": 1, "action_digest": "0" * 64}

    # No session -> 401, before the run is looked up (no existence leak).
    assert client.post(run, json=body).status_code == 401

    csrf = login()
    # Authenticated, no CSRF header -> 403.
    assert client.post(run, json=body).status_code == 403
    # Authenticated, wrong token -> 403.
    wrong = client.post(run, json=body, headers={"X-CSRF-Token": "not-the-token"})
    assert wrong.status_code == 403
    # The issued token opens the CSRF gate; the run is unknown, so 404 proves the
    # gate passed WITHOUT executing anything.
    opened = client.post(run, json=body, headers={"X-CSRF-Token": csrf})
    assert opened.status_code == 404


def test_logout_requires_a_session(client: TestClient) -> None:
    """A12: logout is session-scoped, so an anonymous caller gets 401, not 204."""

    assert client.post("/api/logout").status_code == 401


def test_secure_cookie_follows_the_connection_not_the_mode() -> None:
    """Day-4 ruling 5: a deployed image runs ``mode=local`` behind TLS.

    The old predicate (``secure = mode == "aws"``) would therefore ship a PUBLIC
    session cookie without ``Secure`` -- and ``create_app`` refuses ``mode=aws``
    anyway, so the flag could never turn on. Secure now follows the request scheme.
    This is a TestClient scheme assertion only: no real TLS terminator, certificate
    or proxy chain was exercised (see docs/evidence/day4-cloud-blocked.md).
    """

    app = create_app(Settings(_env_file=None, worker_mode="inline"))
    passphrase = Settings(_env_file=None).demo_passphrase
    payload = {"passphrase": passphrase}

    with TestClient(app, base_url="https://testserver") as tls_client:
        tls_cookie = tls_client.post("/api/login", json=payload).headers["set-cookie"]
    assert "secure" in tls_cookie.lower()

    with TestClient(app, base_url="http://testserver") as plain_client:
        plain_cookie = plain_client.post("/api/login", json=payload).headers["set-cookie"]
    assert "secure" not in plain_cookie.lower()

    # A TLS-terminating proxy reports the outer scheme; honouring the header can
    # only ADD Secure, never remove it.
    with TestClient(app, base_url="http://testserver") as proxied_client:
        proxied = proxied_client.post(
            "/api/login", json=payload, headers={"X-Forwarded-Proto": "https"}
        )
    assert "secure" in proxied.headers["set-cookie"].lower()
