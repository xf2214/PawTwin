"""SQLite adapter for the local (PAWTWIN_MODE=local) persistence layer.

A single held connection keeps an in-memory database alive for the process
lifetime; a file path gives durability across restarts. All semantics required
by T1 live here: unique-constraint de-duplication, one logical receipt per
command id, quota accounted only on first success, and re-claimable leases that
never re-process a terminal run.

Cloud note: a SQLite PASS here does NOT stand in for the DynamoDB conditional
write / transaction tests, which are tracked separately and remain un-run.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from uuid import UUID, uuid5

from pawtwin.models import EventIn, Proposal, Receipt, RunState
from pawtwin.repository import TERMINAL_STATES, FactsSnapshot, RunRecord

RUN_NAMESPACE = UUID("3f2b8c1e-77a4-5b09-9d21-6c8f0a4e1b57")

DEMO_OWNER_ID = "demo-owner"
DEMO_PET_ID = "mochi"
DEFAULT_FACTS = {
    "last_fed_minutes_ago": 360,
    "daily_dispensed_grams": 0,
    "daily_limit_grams": 30,
    "single_serving_grams": 15,
    "minimum_interval_minutes": 120,
}

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
    UNIQUE(owner_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_runs_owner ON runs(owner_id);
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
"""


def _now() -> datetime:
    return datetime.now(UTC)


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SqliteRepository:
    """Implements :class:`pawtwin.repository.Repository` on SQLite."""

    def __init__(self, path: str = ":memory:", *, owner_id: str = DEMO_OWNER_ID) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.Lock()
        self._owner_id = owner_id
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._seed_facts(owner_id)
            self._conn.commit()

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

    def count_runs(self, owner_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM runs WHERE owner_id = ?", (owner_id,)
            ).fetchone()
        return int(row["n"])

    def save_run(self, record: RunRecord) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE runs SET
                    state = ?, facts_version = ?, proposal_json = ?,
                    proposal_version = ?, action_digest = ?, receipt_json = ?,
                    expires_at = ?, lease_owner = ?, lease_until = ?,
                    attempt_count = ?, policy_reason = ?
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
                    record.lease_owner,
                    _dt(record.lease_until),
                    record.attempt_count,
                    record.policy_reason,
                    str(record.run_id),
                ),
            )

    def claim_run(self, run_id: UUID, worker_id: str, lease_until: datetime) -> bool:
        terminal = tuple(state.value for state in TERMINAL_STATES)
        placeholders = ",".join("?" for _ in terminal)
        now = _dt(_now())
        with self._lock, self._conn:
            cursor = self._conn.execute(
                f"""
                UPDATE runs SET lease_owner = ?, lease_until = ?
                WHERE run_id = ?
                  AND state NOT IN ({placeholders})
                  AND (lease_until IS NULL OR lease_until < ?)
                """,
                (worker_id, _dt(lease_until), str(run_id), *terminal, now),
            )
        return cursor.rowcount == 1

    # -- facts --------------------------------------------------------------

    def get_facts(self, owner_id: str) -> FactsSnapshot:
        with self._lock:
            self._seed_facts(owner_id)
            self._conn.commit()
            row = self._conn.execute(
                "SELECT * FROM facts WHERE owner_id = ?", (owner_id,)
            ).fetchone()
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

    def update_facts(
        self,
        owner_id: str,
        *,
        last_fed_minutes_ago: int | None = None,
        daily_dispensed_grams: int | None = None,
    ) -> FactsSnapshot:
        sets: list[str] = []
        params: list[object] = []
        if last_fed_minutes_ago is not None:
            sets.append("last_fed_minutes_ago = ?")
            params.append(last_fed_minutes_ago)
        if daily_dispensed_grams is not None:
            sets.append("daily_dispensed_grams = ?")
            params.append(daily_dispensed_grams)
        sets.append("facts_version = facts_version + 1")
        params.append(owner_id)
        with self._lock, self._conn:
            self._seed_facts(owner_id)
            self._conn.execute(
                f"UPDATE facts SET {', '.join(sets)} WHERE owner_id = ?", tuple(params)
            )
        return self.get_facts(owner_id)

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


def _run_uuid(owner_id: str, event_id: UUID) -> UUID:
    return uuid5(RUN_NAMESPACE, f"{owner_id}:{event_id}")


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
        event=EventIn.model_validate_json(row["event_json"]) if row["event_json"] else None,
    )
