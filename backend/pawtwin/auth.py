"""Demo authentication: server-side passphrase hash, session, and CSRF.

Local HTTP omits only the ``Secure`` cookie flag; CSRF validation is never
omitted (see Day-1 technical ruling). The demo passphrase is a NON-SECRET local
gate: the real judge passphrase is injected via ``PAWTWIN_DEMO_PASSPHRASE`` and
delivered through private test instructions, never committed to source.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime

SESSION_COOKIE = "pawtwin_session"
CSRF_HEADER = "x-csrf-token"


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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuthService:
    """Single-owner demo auth. Sessions live in process memory for Day-1."""

    def __init__(self, *, demo_passphrase: str, owner_id: str = "demo-owner") -> None:
        self._passphrase_hash = hash_passphrase(demo_passphrase)
        self._owner_id = owner_id
        self._sessions: dict[str, Session] = {}

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
        return self._sessions.get(session_id)

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
