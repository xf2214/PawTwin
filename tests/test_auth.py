from datetime import UTC, datetime, timedelta
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

    # Without the trusted-proxy switch (the shipped default), a spoofed
    # X-Forwarded-Proto changes NOTHING: plain HTTP keeps omitting Secure.
    spoof_app = create_app(
        Settings(_env_file=None, worker_mode="inline", trust_proxy_headers=False)
    )
    with TestClient(spoof_app, base_url="http://testserver") as spoof_client:
        spoofed = spoof_client.post(
            "/api/login", json=payload, headers={"X-Forwarded-Proto": "https"}
        )
    assert "secure" not in spoofed.headers["set-cookie"].lower()

    # An operator who has confirmed a TLS-terminating proxy opts in explicitly;
    # only then is the header's FIRST chain value honoured (it can only ADD
    # Secure, never remove it).
    proxy_app = create_app(
        Settings(_env_file=None, worker_mode="inline", trust_proxy_headers=True)
    )
    with TestClient(proxy_app, base_url="http://testserver") as proxied_client:
        proxied = proxied_client.post(
            "/api/login", json=payload, headers={"X-Forwarded-Proto": "https, http"}
        )
    assert "secure" in proxied.headers["set-cookie"].lower()

    with TestClient(proxy_app, base_url="http://testserver") as plain_proxy_client:
        unproxied = plain_proxy_client.post("/api/login", json=payload)
    assert "secure" not in unproxied.headers["set-cookie"].lower()


# --- Day-5 ruling 4b/4c: session lifetime and login throttling -----------------
#
# These are PROCESS-LOCAL gates (replicas fixed at 1x1, ruling 15). They prove the
# single-task behaviour only; a multi-replica session store or distributed throttle
# is explicitly out of scope and NOT verified here.


def _login_client(**overrides: object) -> tuple[TestClient, object]:
    settings = Settings(_env_file=None, worker_mode="inline", **overrides)  # type: ignore[arg-type]
    return TestClient(create_app(settings)), settings


def test_session_expires_after_the_idle_window() -> None:
    client, settings = _login_client(session_idle_seconds=30)
    with client:
        client.post("/api/login", json={"passphrase": settings.demo_passphrase})
        assert client.get("/api/state").status_code == 200
        # Age only the idle clock (created_at stays recent) to isolate idle expiry
        # from the absolute TTL.
        session = next(iter(client.app.state.auth._sessions.values()))
        session.last_seen_at = datetime.now(UTC) - timedelta(seconds=31)
        # Expired -> the session is dropped and reads as unauthenticated.
        assert client.get("/api/state").status_code == 401


def test_session_expires_after_the_absolute_ttl_even_when_recently_seen() -> None:
    client, settings = _login_client(session_ttl_seconds=60)
    with client:
        client.post("/api/login", json={"passphrase": settings.demo_passphrase})
        session = next(iter(client.app.state.auth._sessions.values()))
        # Created long ago but just seen: the ABSOLUTE lifetime still expires it.
        session.created_at = datetime.now(UTC) - timedelta(seconds=61)
        session.last_seen_at = datetime.now(UTC)
        assert client.get("/api/state").status_code == 401


def test_login_is_rate_limited_after_repeated_failures() -> None:
    client, settings = _login_client(login_max_failures=3, login_backoff_seconds=60)
    with client:
        # Below the threshold: ordinary 401s.
        for _ in range(2):
            assert client.post("/api/login", json={"passphrase": "wrong"}).status_code == 401
        # The attempt that crosses the threshold is 429 with a Retry-After.
        blocked = client.post("/api/login", json={"passphrase": "wrong"})
        assert blocked.status_code == 429
        assert blocked.json()["detail"] == "RATE_LIMITED"
        assert int(blocked.headers["Retry-After"]) > 0
        # While blocked, even the CORRECT passphrase is refused (checked before
        # verification), so the throttle cannot be used to probe.
        correct_while_blocked = client.post(
            "/api/login", json={"passphrase": settings.demo_passphrase}
        )
        assert correct_while_blocked.status_code == 429


def test_a_successful_login_resets_the_failure_counter() -> None:
    client, settings = _login_client(login_max_failures=3)
    with client:
        client.post("/api/login", json={"passphrase": "wrong"})
        client.post("/api/login", json={"passphrase": "wrong"})
        ok = client.post("/api/login", json={"passphrase": settings.demo_passphrase})
        assert ok.status_code == 200
        # After a success the counter is cleared, so two more failures are again
        # below the threshold (401, not 429).
        assert client.post("/api/login", json={"passphrase": "wrong"}).status_code == 401
        assert client.post("/api/login", json={"passphrase": "wrong"}).status_code == 401
