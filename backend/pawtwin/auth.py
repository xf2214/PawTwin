"""Demo authentication: server-side passphrase hash, session, and CSRF.

The ``Secure`` cookie flag follows the request scheme (``https``, or
``X-Forwarded-Proto: https`` behind a TLS terminator), NOT ``PAWTWIN_MODE``: the
shipped image runs ``mode=local`` even when deployed (Day-4 ruling 5). Plain local
HTTP therefore omits only ``Secure``; CSRF validation is never omitted (see Day-1
technical ruling). The demo passphrase is a NON-SECRET local
gate: the real judge passphrase is injected via ``PAWTWIN_DEMO_PASSPHRASE`` and
delivered through private test instructions, never committed to source.

Known gaps CLOSED in Day-5 (ruling 4): session TTL + idle expiry now consume
``Session.created_at``/``last_seen_at``, and login is throttled per client IP with a
capped exponential backoff (429 ``RATE_LIMITED``). Both remain PROCESS-LOCAL: the
replicas are fixed at 1x1 (ruling 15), so one process is the whole site. Under
multiple replicas each keeps its own counters and sessions, so this is an honest
single-task gate, NOT a distributed session store or throttle.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

SESSION_COOKIE = "pawtwin_session"
CSRF_HEADER = "x-csrf-token"


def _now() -> datetime:
    return datetime.now(UTC)


def hash_passphrase(passphrase: str) -> str:
    return hashlib.sha256(passphrase.encode("utf-8")).hexdigest()


@dataclass
class Session:
    session_id: str
    owner_id: str
    csrf_token: str
    # Day-3 (ruling 5): the current AgentCore conversation/session id. Rotated by
    # POST /api/demo/new-session WITHOUT re-authenticating; pet memory and facts
    # survive the rotation. In-memory, so it resets on restart (ruling 6).
    conversation_id: str = field(default_factory=lambda: secrets.token_hex(8))
    created_at: datetime = field(default_factory=_now)
    # Day-5 (ruling 4b): last activity, refreshed on every authenticated request so
    # an idle session expires. ``created_at`` is the absolute lifetime anchor.
    last_seen_at: datetime = field(default_factory=_now)


class AuthService:
    """Single-owner demo auth. Sessions live in process memory.

    Day-5 (ruling 4b): a session expires after an absolute lifetime
    (``ttl_seconds`` from ``created_at``) OR an idle window (``idle_seconds`` from
    ``last_seen_at``); an expired session is dropped and reads as unauthenticated
    (401). ``get_session`` refreshes ``last_seen_at`` so any authenticated activity
    keeps the session alive within its absolute lifetime.
    """

    def __init__(
        self,
        *,
        demo_passphrase: str,
        owner_id: str = "demo-owner",
        ttl_seconds: int = 28800,
        idle_seconds: int = 1800,
    ) -> None:
        self._passphrase_hash = hash_passphrase(demo_passphrase)
        self._owner_id = owner_id
        self._sessions: dict[str, Session] = {}
        self._ttl_seconds = max(1, ttl_seconds)
        self._idle_seconds = max(1, idle_seconds)

    @property
    def owner_id(self) -> str:
        return self._owner_id

    def verify_passphrase(self, passphrase: str) -> bool:
        return secrets.compare_digest(hash_passphrase(passphrase), self._passphrase_hash)

    def login(self, passphrase: str) -> Session | None:
        if not self.verify_passphrase(passphrase):
            return None
        session = Session(
            session_id=secrets.token_urlsafe(32),
            owner_id=self._owner_id,
            csrf_token=secrets.token_urlsafe(32),
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str | None) -> Session | None:
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        now = _now()
        # Absolute lifetime, then idle window. Expired -> drop and read as 401.
        if (now - session.created_at).total_seconds() > self._ttl_seconds:
            self._sessions.pop(session_id, None)
            return None
        if (now - session.last_seen_at).total_seconds() > self._idle_seconds:
            self._sessions.pop(session_id, None)
            return None
        session.last_seen_at = now
        return session

    def logout(self, session_id: str | None) -> None:
        if session_id:
            self._sessions.pop(session_id, None)

    def new_conversation(self, session_id: str | None) -> str | None:
        """Rotate the conversation id for a live session (``demo/new-session``).

        The login, the pet facts and any stored feedback are untouched; only the
        AgentCore conversation rotates, which is what makes a cross-session
        retrieval demonstrable. Returns ``None`` when the session is gone.
        """

        session = self.get_session(session_id)
        if session is None:
            return None
        session.conversation_id = secrets.token_hex(8)
        return session.conversation_id

    def check_csrf(self, session: Session, token: str | None) -> bool:
        if not token:
            return False
        return secrets.compare_digest(session.csrf_token, token)


class LoginRateLimiter:
    """In-process login throttle (Day-5 ruling 4c): per-client-IP failure count.

    After ``max_failures`` consecutive failures from one IP the caller is blocked
    for a backoff window; each further failure past the threshold DOUBLES the window
    (capped at ``2**_MAX_DOUBLINGS``), and a successful login clears the counter.
    ``check`` returns the remaining ``Retry-After`` seconds (0 when not blocked).

    HONEST BOUNDARY: the counter is process-local. With the replicas fixed at 1x1
    (ruling 15) one process is the whole site, so this is effective; under multiple
    replicas the real site-wide threshold becomes ``replicas x max_failures`` and a
    distributed store would be required. It is documented as a single-task gate,
    never as a site-wide guarantee.
    """

    _MAX_DOUBLINGS = 4  # cap the multiplier at 2**4 = 16x the base backoff

    def __init__(self, *, max_failures: int, backoff_seconds: int) -> None:
        self._max_failures = max(1, max_failures)
        self._backoff_seconds = max(1, backoff_seconds)
        self._lock = threading.Lock()
        self._failures: dict[str, int] = {}
        self._blocked_until: dict[str, datetime] = {}

    def check(self, client_ip: str) -> int:
        """Remaining ``Retry-After`` seconds for this IP, or 0 when not blocked."""

        with self._lock:
            until = self._blocked_until.get(client_ip)
            if until is None:
                return 0
            remaining = (until - _now()).total_seconds()
            if remaining <= 0:
                return 0
            # Round up so a sub-second remainder still asks the client to wait 1s.
            return int(remaining) + (1 if remaining % 1 else 0)

    def register_failure(self, client_ip: str) -> int:
        """Record a failed attempt; return the ``Retry-After`` if now blocked, else 0."""

        with self._lock:
            count = self._failures.get(client_ip, 0) + 1
            self._failures[client_ip] = count
            if count < self._max_failures:
                return 0
            doublings = min(count - self._max_failures, self._MAX_DOUBLINGS)
            backoff = self._backoff_seconds * (2**doublings)
            self._blocked_until[client_ip] = _now() + timedelta(seconds=backoff)
            return backoff

    def register_success(self, client_ip: str) -> None:
        with self._lock:
            self._failures.pop(client_ip, None)
            self._blocked_until.pop(client_ip, None)
