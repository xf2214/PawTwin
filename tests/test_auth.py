from uuid import uuid4

from fastapi.testclient import TestClient
from pawtwin.config import Settings


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
