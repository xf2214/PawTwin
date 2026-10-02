"""SQLite adapter for the local (PAWTWIN_MODE=local) persistence layer.

A single held connection keeps an in-memory database alive for the process
lifetime; a file path gives durability across restarts. All semantics required
by T1 live here: unique-constraint de-duplication, one logical receipt per
command id, quota accounted only on first success, and re-claimable leases that
never re-process a terminal run.

Day-2 adds an idempotent schema migration (``PRAGMA user_version``), an explicit
claimable-state whitelist, lease renewal/release and a compare-and-set state
transition, so a run can never be re-analyzed out of ``EXECUTING`` and a
concurrent approval can never execute twice.

Cloud note: a SQLite PASS here does NOT stand in for the DynamoDB conditional
write / transaction tests, which are tracked separately and remain un-run.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from uuid import UUID, uuid4, uuid5

from pawtwin.models import (
    MEMORY_AVAILABLE,
    MEMORY_PROCESSING,
    AnalysisTelemetry,
    EventIn,
    EvidenceItem,
    FeedbackScope,
    MemoryBackend,
    MemoryStatus,
    Proposal,
    Receipt,
    RunState,
)
from pawtwin.repository import (
    CLAIMABLE_STATES,
    UNSET,
    FactsSnapshot,
    FeedbackRecord,
    RunRecord,
    _Unset,
)

RUN_NAMESPACE = UUID("3f2b8c1e-77a4-5b09-9d21-6c8f0a4e1b57")
FEEDBACK_NAMESPACE = UUID("6c1d9f42-3a7e-5b8d-9c41-2f7a8e5b0d63")

DEMO_OWNER_ID = "demo-owner"
DEMO_PET_ID = "mochi"
DEFAULT_FACTS = {
    "last_fed_minutes_ago": 360,
    "daily_dispensed_grams": 0,
    "daily_limit_grams": 30,
    "single_serving_grams": 15,
    "minimum_interval_minutes": 120,
}

# Bump when a migration is added; ``_migrate`` is idempotent and column-existence
# checked, so it is safe on both fresh and pre-Day-2 database files.
# v2 = Day-2 run columns; v3 = Day-3 ``feedback`` table (created by _SCHEMA's
# CREATE TABLE IF NOT EXISTS, so no ALTER was needed -- only the version gate);
# v4 = Day-5 ``feedback.agentcore_session_id`` (the AgentCore ``sessionId`` that
# ``GetEvent`` requires to poll one event, fact G-G) -- a real ALTER on a v3 file.
SCHEMA_VERSION = 4
_V2_RUN_COLUMNS = (
    "failure_reason TEXT",
    "evidence_json TEXT",
    "telemetry_json TEXT",
    "model_calls_used INTEGER NOT NULL DEFAULT 0",
)
_V4_FEEDBACK_COLUMNS = (
    "agentcore_session_id TEXT",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    facts_version INTEGER NOT NULL DEFAULT 0,
    proposal_json TEXT,
    proposal_version INTEGER NOT NULL DEFAULT 0,
    action_digest TEXT,
    receipt_json TEXT,
    expires_at TEXT,
    lease_owner TEXT,
    lease_until TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    policy_reason TEXT,
    event_json TEXT,
    failure_reason TEXT,
    evidence_json TEXT,
    telemetry_json TEXT,
    model_calls_used INTEGER NOT NULL DEFAULT 0,
    UNIQUE(owner_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_runs_owner ON runs(owner_id);
CREATE INDEX IF NOT EXISTS idx_runs_state ON runs(state);
CREATE TABLE IF NOT EXISTS facts (
    owner_id TEXT PRIMARY KEY,
    pet_id TEXT NOT NULL,
    last_fed_minutes_ago INTEGER,
    daily_dispensed_grams INTEGER,
    daily_limit_grams INTEGER NOT NULL,
    single_serving_grams INTEGER NOT NULL,
    minimum_interval_minutes INTEGER NOT NULL,
    facts_version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS receipts (
    command_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_receipts_run ON receipts(run_id);
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    pet_id TEXT NOT NULL,
    text TEXT NOT NULL,
    scope TEXT NOT NULL,
    memory_status TEXT NOT NULL,
    memory_backend TEXT NOT NULL,
    conversation_id TEXT,
    agentcore_event_id TEXT,
    agentcore_session_id TEXT,
    memory_record_ids_json TEXT,
    idempotency_key TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(owner_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_feedback_owner ON feedback(owner_id);
"""


def _now() -> datetime:
    return datetime.now(UTC)


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _state_values(states: frozenset[RunState]) -> tuple[str, ...]:
    return tuple(state.value for state in states)


def _dump_evidence(evidence: list[EvidenceItem]) -> str | None:
    if not evidence:
        return None
    return "[" + ",".join(item.model_dump_json() for item in evidence) + "]"


def _load_evidence(raw: str | None) -> list[EvidenceItem]:
    if not raw:
        return []
    return [EvidenceItem.model_validate(item) for item in json.loads(raw)]


class SqliteRepository:
    """Implements :class:`pawtwin.repository.Repository` on SQLite."""

    def __init__(self, path: str = ":memory:", *, owner_id: str = DEMO_OWNER_ID) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        # Day-3 (ruling 8): a FILE database may be opened by two connections at
        # once -- the cross-process double-approval test, and a rolling deploy's
        # two replicas. WAL lets a reader and a writer proceed concurrently, and
        # busy_timeout makes a contended write WAIT instead of failing instantly
        # with "database is locked". Neither is meaningful for ":memory:".
        if path != ":memory:":
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA busy_timeout = 5000")
        # Re-entrant: Day-2 methods call each other while holding the lock, and a
        # plain Lock would deadlock (there is no pytest-timeout to rescue a hang).
        self._lock = threading.RLock()
        self._owner_id = owner_id
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._migrate()
            self._seed_facts(owner_id)
            self._conn.commit()

    def _migrate(self) -> None:
        """Add Day-2 columns to a pre-existing database file, exactly once.

        ``CREATE TABLE IF NOT EXISTS`` never alters an existing table, so without
        this a persisted ``PAWTWIN_DB_PATH`` database would fail on the first
        save/read -- a defect the ``:memory:`` test suite cannot surface.
        """

        row = self._conn.execute("PRAGMA user_version").fetchone()
        version = int(row[0]) if row is not None else 0
        if version < SCHEMA_VERSION:
            existing = {r["name"] for r in self._conn.execute("PRAGMA table_info(runs)")}
            for declaration in _V2_RUN_COLUMNS:
                column = declaration.split()[0]
                if column not in existing:
                    self._conn.execute(f"ALTER TABLE runs ADD COLUMN {declaration}")
            # v4 (Day-5): a pre-existing (v3) ``feedback`` table has no
            # ``agentcore_session_id``; CREATE TABLE IF NOT EXISTS never alters it,
            # so add the column here. _SCHEMA runs before _migrate, so the table
            # always exists by this point.
            existing_feedback = {
                r["name"] for r in self._conn.execute("PRAGMA table_info(feedback)")
            }
            for declaration in _V4_FEEDBACK_COLUMNS:
                column = declaration.split()[0]
                if column not in existing_feedback:
                    self._conn.execute(f"ALTER TABLE feedback ADD COLUMN {declaration}")
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- seeding ------------------------------------------------------------

    def _seed_facts(self, owner_id: str) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO facts (
                owner_id, pet_id, last_fed_minutes_ago, daily_dispensed_grams,
                daily_limit_grams, single_serving_grams, minimum_interval_minutes,
                facts_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                owner_id,
                DEMO_PET_ID,
                DEFAULT_FACTS["last_fed_minutes_ago"],
                DEFAULT_FACTS["daily_dispensed_grams"],
                DEFAULT_FACTS["daily_limit_grams"],
                DEFAULT_FACTS["single_serving_grams"],
                DEFAULT_FACTS["minimum_interval_minutes"],
            ),
        )

    # -- runs ---------------------------------------------------------------

    def create_or_get_run(self, owner_id: str, event: EventIn) -> RunRecord:
        run_id = _run_uuid(owner_id, event.event_id)
        now = _now()
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO runs (
                    run_id, owner_id, event_id, state, created_at,
                    facts_version, proposal_version, attempt_count, event_json
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)
                """,
                (
                    str(run_id),
                    owner_id,
                    str(event.event_id),
                    RunState.QUEUED.value,
                    _dt(now),
                    self._facts_version(owner_id),
                    event.model_dump_json(),
                ),
            )
        record = self.get_run(run_id)
        assert record is not None  # noqa: S101 - just inserted/selected
        return record

    def _facts_version(self, owner_id: str) -> int:
        row = self._conn.execute(
            "SELECT facts_version FROM facts WHERE owner_id = ?", (owner_id,)
        ).fetchone()
        return int(row["facts_version"]) if row else 0

    def get_run(self, run_id: UUID) -> RunRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (str(run_id),)
            ).fetchone()
        return _row_to_record(row) if row else None

    def list_runs(self, owner_id: str) -> list[RunRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM runs WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def list_claimable_runs(self, limit: int = 10) -> list[RunRecord]:
        """Candidates for :meth:`claim_run`; the claim itself stays atomic."""

        claimable = _state_values(CLAIMABLE_STATES)
        placeholders = ",".join("?" for _ in claimable)
        with self._lock:
            rows = self._conn.execute(
                f"""
                SELECT * FROM runs
                WHERE state IN ({placeholders})
                  AND (lease_until IS NULL OR lease_until < ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (*claimable, _dt(_now()), max(1, limit)),
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def count_runs(self, owner_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM runs WHERE owner_id = ?", (owner_id,)
            ).fetchone()
        return int(row["n"])

    def save_run(self, record: RunRecord) -> None:
        # Lease fields and attempt_count are deliberately NOT written here: they
        # belong to claim_run/renew_lease/release_run, so saving an analyzed
        # record can never clear the lease this worker just acquired.
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE runs SET
                    state = ?, facts_version = ?, proposal_json = ?,
                    proposal_version = ?, action_digest = ?, receipt_json = ?,
                    expires_at = ?, policy_reason = ?, failure_reason = ?,
                    evidence_json = ?, telemetry_json = ?, model_calls_used = ?
                WHERE run_id = ?
                """,
                (
                    record.state.value,
                    record.facts_version,
                    record.proposal.model_dump_json() if record.proposal else None,
                    record.proposal_version,
                    record.action_digest,
                    record.receipt.model_dump_json() if record.receipt else None,
                    _dt(record.expires_at),
                    record.policy_reason,
                    record.failure_reason,
                    _dump_evidence(record.evidence),
                    record.telemetry.model_dump_json() if record.telemetry else None,
                    record.model_calls_used,
                    str(record.run_id),
                ),
            )

    def claim_run(
        self,
        run_id: UUID,
        worker_id: str,
        lease_until: datetime,
        *,
        max_attempts: int | None = None,
    ) -> bool:
        claimable = _state_values(CLAIMABLE_STATES)
        placeholders = ",".join("?" for _ in claimable)
        now = _dt(_now())
        sql = f"""
            UPDATE runs SET lease_owner = ?, lease_until = ?,
                            attempt_count = attempt_count + 1
            WHERE run_id = ?
              AND state IN ({placeholders})
              AND (lease_until IS NULL OR lease_until < ?)
        """
        params: list[object] = [worker_id, _dt(lease_until), str(run_id), *claimable, now]
        if max_attempts is not None:
            # Atomic ceiling: read-increment-write from the worker would race.
            sql += " AND attempt_count < ?"
            params.append(max_attempts)
        with self._lock, self._conn:
            cursor = self._conn.execute(sql, tuple(params))
        return cursor.rowcount == 1

    def renew_lease(self, run_id: UUID, worker_id: str, lease_until: datetime) -> bool:
        claimable = _state_values(CLAIMABLE_STATES)
        placeholders = ",".join("?" for _ in claimable)
        with self._lock, self._conn:
            cursor = self._conn.execute(
                f"""
                UPDATE runs SET lease_until = ?
                WHERE run_id = ? AND lease_owner = ?
                  AND state IN ({placeholders})
                """,
                (_dt(lease_until), str(run_id), worker_id, *claimable),
            )
        return cursor.rowcount == 1

    def release_run(self, run_id: UUID, worker_id: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE runs SET lease_owner = NULL, lease_until = NULL
                WHERE run_id = ? AND lease_owner = ?
                """,
                (str(run_id), worker_id),
            )

    def transition_run(self, run_id: UUID, expected: RunState, new: RunState) -> bool:
        """Compare-and-set. The guard that makes "execute at most once" real."""

        with self._lock, self._conn:
            cursor = self._conn.execute(
                "UPDATE runs SET state = ? WHERE run_id = ? AND state = ?",
                (new.value, str(run_id), expected.value),
            )
        return cursor.rowcount == 1

    # -- facts --------------------------------------------------------------

    def get_facts(self, owner_id: str) -> FactsSnapshot:
        # Seeding is lazy: the FIRST read for an owner inserts the default row
        # (inside the lock, idempotent); every later read is a pure read. That keeps
        # the agent's tools read-only in steady state while the worker thread and
        # request threads read concurrently.
        with self._lock:
            row = self._fetch_facts_row(owner_id)
            if row is None:
                self._seed_facts(owner_id)
                self._conn.commit()
                row = self._fetch_facts_row(owner_id)
        return FactsSnapshot(
            owner_id=row["owner_id"],
            pet_id=row["pet_id"],
            last_fed_minutes_ago=row["last_fed_minutes_ago"],
            daily_dispensed_grams=row["daily_dispensed_grams"],
            daily_limit_grams=row["daily_limit_grams"],
            single_serving_grams=row["single_serving_grams"],
            minimum_interval_minutes=row["minimum_interval_minutes"],
            facts_version=row["facts_version"],
        )

    def _fetch_facts_row(self, owner_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM facts WHERE owner_id = ?", (owner_id,)
        ).fetchone()

    def update_facts(
        self,
        owner_id: str,
        *,
        last_fed_minutes_ago: int | None | _Unset = UNSET,
        daily_dispensed_grams: int | None | _Unset = UNSET,
    ) -> FactsSnapshot:
        sets: list[str] = []
        params: list[object] = []
        for column, value in (
            ("last_fed_minutes_ago", last_fed_minutes_ago),
            ("daily_dispensed_grams", daily_dispensed_grams),
        ):
            if isinstance(value, _Unset):
                continue  # leave the column untouched
            sets.append(f"{column} = ?")
            # ``None`` writes SQL NULL: the fact becomes UNKNOWN and feeding fails
            # closed (A09). This is why the sentinel exists.
            params.append(value)
        sets.append("facts_version = facts_version + 1")
        params.append(owner_id)
        with self._lock, self._conn:
            self._seed_facts(owner_id)
            self._conn.execute(
                f"UPDATE facts SET {', '.join(sets)} WHERE owner_id = ?", tuple(params)
            )
        return self.get_facts(owner_id)

    def reset_facts(self, owner_id: str) -> FactsSnapshot:
        return self.update_facts(
            owner_id,
            last_fed_minutes_ago=DEFAULT_FACTS["last_fed_minutes_ago"],
            daily_dispensed_grams=DEFAULT_FACTS["daily_dispensed_grams"],
        )

    # -- receipts -----------------------------------------------------------

    def record_receipt_once(
        self,
        *,
        command_id: UUID,
        run_id: UUID,
        receipt: Receipt,
        dispense_grams: int,
    ) -> bool:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """
                INSERT OR IGNORE INTO receipts (command_id, run_id, receipt_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (str(command_id), str(run_id), receipt.model_dump_json(), _dt(_now())),
            )
            inserted = cursor.rowcount == 1
            if inserted and receipt.status == "succeeded" and dispense_grams > 0:
                owner_row = self._conn.execute(
                    "SELECT owner_id FROM runs WHERE run_id = ?", (str(run_id),)
                ).fetchone()
                if owner_row is not None:
                    self._conn.execute(
                        """
                        UPDATE facts SET
                            daily_dispensed_grams = COALESCE(daily_dispensed_grams, 0) + ?,
                            last_fed_minutes_ago = 0,
                            facts_version = facts_version + 1
                        WHERE owner_id = ?
                        """,
                        (dispense_grams, owner_row["owner_id"]),
                    )
        return inserted

    def count_receipts(self, run_id: UUID) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM receipts WHERE run_id = ?", (str(run_id),)
            ).fetchone()
        return int(row["n"])

    # -- owner feedback (Day-3 / T5) ----------------------------------------

    def save_feedback(
        self,
        *,
        owner_id: str,
        pet_id: str,
        text: str,
        scope: FeedbackScope,
        memory_status: MemoryStatus,
        memory_backend: MemoryBackend,
        conversation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> FeedbackRecord:
        # With an idempotency key the id is DETERMINISTIC, so INSERT OR IGNORE
        # makes a retry return the existing row instead of storing a duplicate
        # (one feedback item is never submitted to AgentCore twice). Without a key
        # a fresh uuid4 always inserts.
        feedback_id = (
            _feedback_uuid(owner_id, idempotency_key) if idempotency_key is not None else uuid4()
        )
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO feedback (
                    feedback_id, owner_id, pet_id, text, scope, memory_status,
                    memory_backend, conversation_id, agentcore_event_id,
                    agentcore_session_id, memory_record_ids_json, idempotency_key,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(feedback_id),
                    owner_id,
                    pet_id,
                    text,
                    scope,
                    memory_status,
                    memory_backend,
                    conversation_id,
                    None,
                    None,
                    None,
                    idempotency_key,
                    _dt(_now()),
                ),
            )
        record = self.get_feedback(feedback_id)
        assert record is not None  # noqa: S101 - just inserted/selected
        return record

    def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM feedback WHERE feedback_id = ?", (str(feedback_id),)
            ).fetchone()
        return _row_to_feedback(row) if row else None

    def list_feedback(self, owner_id: str) -> list[FeedbackRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM feedback WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,)
            ).fetchall()
        return [_row_to_feedback(row) for row in rows]

    def list_feedback_pending_extraction(self) -> list[FeedbackRecord]:
        # Compared against MEMORY_PROCESSING (imported from the vocabulary module),
        # never a bare literal, so this module stays off the anti-forgery guard's
        # offender list (Day-5 ruling 12: the whitelist is not extended).
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM feedback WHERE memory_status = ? "
                "AND agentcore_event_id IS NOT NULL ORDER BY created_at ASC",
                (MEMORY_PROCESSING,),
            ).fetchall()
        return [_row_to_feedback(row) for row in rows]

    def set_feedback_status(
        self,
        feedback_id: UUID,
        *,
        memory_status: MemoryStatus,
        agentcore_event_id: str | None = None,
        agentcore_session_id: str | None = None,
        memory_record_ids: list[str] | None = None,
    ) -> FeedbackRecord | None:
        # Day-5 (ruling 11): a hard fail-closed invariant. The available status
        # means real AgentCore records were retrieved, so it can NEVER be written
        # without the record ids to prove it -- a future wiring bug raises instead
        # of silently dressing stored feedback up as extracted memory (AGENTS.md
        # L18). The literal lives in models.py (MEMORY_AVAILABLE), not here, so the
        # anti-forgery static guard's whitelist stays unchanged (ruling 12).
        if memory_status == MEMORY_AVAILABLE and not memory_record_ids:
            raise ValueError(
                "set_feedback_status(available) requires memory_record_ids"
            )
        ids_json = json.dumps(memory_record_ids) if memory_record_ids is not None else None
        with self._lock, self._conn:
            cursor = self._conn.execute(
                """
                UPDATE feedback SET
                    memory_status = ?,
                    agentcore_event_id = COALESCE(?, agentcore_event_id),
                    agentcore_session_id = COALESCE(?, agentcore_session_id),
                    memory_record_ids_json = COALESCE(?, memory_record_ids_json)
                WHERE feedback_id = ?
                """,
                (
                    memory_status,
                    agentcore_event_id,
                    agentcore_session_id,
                    ids_json,
                    str(feedback_id),
                ),
            )
        if cursor.rowcount != 1:
            return None
        return self.get_feedback(feedback_id)


def _run_uuid(owner_id: str, event_id: UUID) -> UUID:
    return uuid5(RUN_NAMESPACE, f"{owner_id}:{event_id}")


def _feedback_uuid(owner_id: str, idempotency_key: str) -> UUID:
    return uuid5(FEEDBACK_NAMESPACE, f"{owner_id}:{idempotency_key}")


def _row_to_record(row: sqlite3.Row) -> RunRecord:
    return RunRecord(
        run_id=UUID(row["run_id"]),
        owner_id=row["owner_id"],
        event_id=UUID(row["event_id"]),
        state=RunState(row["state"]),
        created_at=_parse_dt(row["created_at"]),  # type: ignore[arg-type]  # always set on insert
        facts_version=row["facts_version"],
        proposal=(
            Proposal.model_validate_json(row["proposal_json"]) if row["proposal_json"] else None
        ),
        proposal_version=row["proposal_version"],
        action_digest=row["action_digest"],
        receipt=Receipt.model_validate_json(row["receipt_json"]) if row["receipt_json"] else None,
        expires_at=_parse_dt(row["expires_at"]),
        lease_owner=row["lease_owner"],
        lease_until=_parse_dt(row["lease_until"]),
        attempt_count=row["attempt_count"],
        policy_reason=row["policy_reason"],
        failure_reason=row["failure_reason"],
        evidence=_load_evidence(row["evidence_json"]),
        telemetry=(
            AnalysisTelemetry.model_validate_json(row["telemetry_json"])
            if row["telemetry_json"]
            else None
        ),
        model_calls_used=row["model_calls_used"],
        event=EventIn.model_validate_json(row["event_json"]) if row["event_json"] else None,
    )


def _row_to_feedback(row: sqlite3.Row) -> FeedbackRecord:
    raw_ids = row["memory_record_ids_json"]
    return FeedbackRecord(
        feedback_id=UUID(row["feedback_id"]),
        owner_id=row["owner_id"],
        pet_id=row["pet_id"],
        text=row["text"],
        scope=row["scope"],
        memory_status=row["memory_status"],
        memory_backend=row["memory_backend"],
        created_at=_parse_dt(row["created_at"]),  # type: ignore[arg-type]  # always set on insert
        conversation_id=row["conversation_id"],
        agentcore_event_id=row["agentcore_event_id"],
        agentcore_session_id=row["agentcore_session_id"],
        memory_record_ids=json.loads(raw_ids) if raw_ids else [],
        idempotency_key=row["idempotency_key"],
    )
