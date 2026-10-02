"""DynamoDB adapter for the real-cloud (``PAWTWIN_MODE=aws``) persistence layer.

Day-5 ruling 5: a SINGLE table keyed by ``pk`` (HASH) + ``sk`` (RANGE) with one
``entity-index`` GSI (``gpk`` HASH + ``gsk`` RANGE) carries every item type::

    run       pk="run#<run_id>"          sk="R"   gpk="owner#<owner>"  gsk=created_at
    facts     pk="facts#<owner>"         sk="F"
    receipt   pk="receipt#<command_id>"  sk="C"   gpk="run#<run_id>"   gsk=created_at
    feedback  pk="feedback#<id>"         sk="B"

Only runs and receipts are projected into ``entity-index`` (feedback/facts carry no
``gpk``), so a ``gpk="owner#<o>"`` query returns runs alone and ``gpk="run#<r>"``
returns that run's receipts. ``list_claimable_runs`` and ``list_feedback`` are
cross-partition and therefore use a bounded ``Scan`` (demo scale, PAY_PER_REQUEST);
the atomic claim/receipt guards -- not the candidate listing -- are what keep
concurrency safe, exactly as in SQLite.

:mod:`pawtwin.repo_sqlite` is the SEMANTIC baseline. The deterministic run/feedback
ids, the ISO-8601 UTC timestamp format, the evidence (de)serialization and the
claimable-state vocabulary are IMPORTED from it on purpose so the two adapters can
never drift: a condition expression compares those timestamp strings
lexicographically, which equals time order ONLY because both write the identical
``datetime.isoformat()`` form. Numbers are DynamoDB numbers (read back as
``Decimal``); ``None`` is written as a DynamoDB ``NULL`` (so A09's UNKNOWN fact and
``COALESCE``-style status updates behave as in SQL).

VERIFICATION STATUS (Day-5): IMPLEMENTED but NOT cloud-verified. No AWS
account/credential was available when this was written, so it has never run against
a real table. The offline suite asserts ONLY that the public method set covers the
:class:`~pawtwin.repository.Repository` protocol (a missing-method guard, explicitly
NOT cloud evidence). Every behavioural test lives behind the ``dynamodb_live``
marker and is skipped until a real table is reachable; a SQLite PASS never stands in
for it (AGENTS.md; five-day spec L106).
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pawtwin.models import (
    MEMORY_AVAILABLE,
    MEMORY_PROCESSING,
    AnalysisTelemetry,
    EventIn,
    FeedbackScope,
    MemoryBackend,
    MemoryStatus,
    Proposal,
    Receipt,
    RunState,
)
from pawtwin.repo_sqlite import (
    DEFAULT_FACTS,
    DEMO_OWNER_ID,
    DEMO_PET_ID,
    _dt,
    _dump_evidence,
    _feedback_uuid,
    _load_evidence,
    _now,
    _parse_dt,
    _run_uuid,
    _state_values,
)
from pawtwin.repository import (
    CLAIMABLE_STATES,
    UNSET,
    FactsSnapshot,
    FeedbackRecord,
    RunRecord,
    _Unset,
)

DYNAMO_UNAVAILABLE = "DYNAMO_UNAVAILABLE"
_CREDENTIAL_ENV_NAMES = ("AWS_ACCESS_KEY_ID", "AWS_PROFILE", "AWS_SESSION_TOKEN")

# Table/GSI names are fixed by infra/deploy_plan.json; the GSI carries runs-by-owner
# and receipts-by-run so list_runs/count_receipts are indexed queries.
ENTITY_INDEX = "entity-index"


class DynamoUnavailable(RuntimeError):
    """Real DynamoDB could not be used. NEVER substituted by SQLite or a stand-in.

    The message always starts with ``DYNAMO_UNAVAILABLE`` so ``create_app`` can
    refuse to start and print the real reason (AGENTS.md L22) instead of silently
    falling back to local storage and overstating readiness.
    """


def _unavailable(detail: str) -> DynamoUnavailable:
    return DynamoUnavailable(f"{DYNAMO_UNAVAILABLE}: {detail}")


def require_credentials() -> None:
    """Fail closed when no credential source is configured at all.

    Decides only whether to ATTEMPT a call; never implies connectivity and never
    sets ``aws_connected``. Long-lived keys are never read from or written to the
    repository, logs or evidence.
    """

    if any(os.getenv(name) for name in _CREDENTIAL_ENV_NAMES):
        return
    candidates = [
        os.environ.get("AWS_SHARED_CREDENTIALS_FILE", os.path.expanduser("~/.aws/credentials")),
        os.environ.get("AWS_CONFIG_FILE", os.path.expanduser("~/.aws/config")),
    ]
    if any(path and os.path.isfile(path) for path in candidates):
        return
    raise _unavailable("DYNAMODB_NOT_CONFIGURED")


def _int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _run_key(run_id: UUID) -> dict[str, str]:
    return {"pk": f"run#{run_id}", "sk": "R"}


def _facts_key(owner_id: str) -> dict[str, str]:
    return {"pk": f"facts#{owner_id}", "sk": "F"}


def _receipt_key(command_id: UUID) -> dict[str, str]:
    return {"pk": f"receipt#{command_id}", "sk": "C"}


def _feedback_key(feedback_id: UUID) -> dict[str, str]:
    return {"pk": f"feedback#{feedback_id}", "sk": "B"}


class DynamoRepository:
    """Implements :class:`pawtwin.repository.Repository` on a single DynamoDB table.

    ``client`` is an injection seam for the ``dynamodb_live`` tests (a real boto3
    client); it is NEVER a mock in the offline suite. boto3 is imported lazily so
    local mode, CI and the offline contract export never need the ``memory`` extra.
    """

    def __init__(
        self,
        table_name: str,
        *,
        region: str | None = None,
        client: Any | None = None,
        owner_id: str = DEMO_OWNER_ID,
    ) -> None:
        if not table_name:
            raise _unavailable("DYNAMODB_TABLE_NAME_MISSING")
        self._table_name = table_name
        self._region = region
        self._client = client
        self._owner_id = owner_id
        self._ser: Any | None = None
        self._deser: Any | None = None

    # -- low-level plumbing -------------------------------------------------

    def _types(self) -> tuple[Any, Any]:
        if self._ser is None or self._deser is None:
            try:
                from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
            except ImportError as exc:  # pragma: no cover - depends on optional extra
                raise _unavailable("SDK_NOT_INSTALLED") from exc
            self._ser = TypeSerializer()
            self._deser = TypeDeserializer()
        return self._ser, self._deser

    def _ddb(self) -> Any:
        if self._client is not None:
            return self._client
        require_credentials()
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise _unavailable("SDK_NOT_INSTALLED") from exc
        kwargs: dict[str, Any] = {}
        if self._region:
            kwargs["region_name"] = self._region
        try:
            self._client = boto3.client("dynamodb", **kwargs)
        except Exception as exc:  # noqa: BLE001 - any client failure must fail closed
            raise _unavailable(f"CLIENT_INIT_FAILED {exc.__class__.__name__}") from exc
        return self._client

    def _ser_item(self, item: dict[str, Any]) -> dict[str, Any]:
        ser, _ = self._types()
        return {key: ser.serialize(value) for key, value in item.items()}

    def _av(self, values: dict[str, Any]) -> dict[str, Any]:
        ser, _ = self._types()
        return {name: ser.serialize(value) for name, value in values.items()}

    def _deser_item(self, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if item is None:
            return None
        _, deser = self._types()
        return {key: deser.deserialize(value) for key, value in item.items()}

    def _get(self, key: dict[str, str]) -> dict[str, Any] | None:
        client = self._ddb()
        response = client.get_item(TableName=self._table_name, Key=self._ser_item(key))
        return self._deser_item(response.get("Item"))

    def _put_if_absent(self, item: dict[str, Any]) -> bool:
        """Idempotent insert guarded by ``attribute_not_exists(pk)``.

        Returns ``True`` when this call inserted the item, ``False`` when it already
        existed -- the DynamoDB equivalent of SQLite ``INSERT OR IGNORE`` + rowcount.
        """

        client = self._ddb()
        try:
            client.put_item(
                TableName=self._table_name,
                Item=self._ser_item(item),
                ConditionExpression="attribute_not_exists(pk)",
            )
        except client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    def _conditional_update(
        self,
        key: dict[str, str],
        update_expression: str,
        condition_expression: str,
        values: dict[str, Any],
        *,
        names: dict[str, str] | None = None,
    ) -> bool:
        client = self._ddb()
        kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "Key": self._ser_item(key),
            "UpdateExpression": update_expression,
            "ConditionExpression": condition_expression,
            "ExpressionAttributeValues": self._av(values),
        }
        if names:
            kwargs["ExpressionAttributeNames"] = names
        try:
            client.update_item(**kwargs)
        except client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    def _scan(
        self,
        filter_expression: str,
        values: dict[str, Any],
        *,
        names: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        client = self._ddb()
        kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "FilterExpression": filter_expression,
            "ExpressionAttributeValues": self._av(values),
        }
        if names:
            # ``state`` (and other DynamoDB reserved words) MUST be aliased, or a real
            # table rejects the expression with ValidationException.
            kwargs["ExpressionAttributeNames"] = names
        items: list[dict[str, Any]] = []
        while True:
            response = client.scan(**kwargs)
            for raw in response.get("Items", []):
                item = self._deser_item(raw)
                if item is not None:
                    items.append(item)
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key

    def _query_items(self, gpk: str, *, forward: bool = True) -> list[dict[str, Any]]:
        """Paginated entity-index query. DynamoDB caps one page at 1 MB, so follow
        ``LastEvaluatedKey`` to match SQLite's "return every row" semantics."""

        client = self._ddb()
        kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "IndexName": ENTITY_INDEX,
            "KeyConditionExpression": "gpk = :g",
            "ExpressionAttributeValues": self._av({":g": gpk}),
            "ScanIndexForward": forward,
        }
        items: list[dict[str, Any]] = []
        while True:
            response = client.query(**kwargs)
            for raw in response.get("Items", []):
                item = self._deser_item(raw)
                if item is not None:
                    items.append(item)
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key

    def _query_count(self, gpk: str) -> int:
        client = self._ddb()
        kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "IndexName": ENTITY_INDEX,
            "KeyConditionExpression": "gpk = :g",
            "ExpressionAttributeValues": self._av({":g": gpk}),
            "Select": "COUNT",
        }
        total = 0
        while True:
            response = client.query(**kwargs)
            total += int(response.get("Count", 0))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return total
            kwargs["ExclusiveStartKey"] = last_key

    def close(self) -> None:
        """Interface parity with :class:`SqliteRepository`; a boto3 client needs no
        explicit close, and an injected client is owned by the caller."""

        self._client = None

    def probe(self) -> None:
        """Read-only, zero-cost reachability probe (Day-5 ruling 7).

        A ``GetItem`` on a fixed meta key: a missing key is fine (it still proves the
        table is reachable), while missing credentials, a missing table or any client
        error raises :class:`DynamoUnavailable` so ``create_app`` REFUSES to start
        rather than silently falling back to SQLite (AGENTS.md L22). This is not a
        billable model call.
        """

        client = self._ddb()  # require_credentials + client init, both fail closed
        try:
            client.get_item(
                TableName=self._table_name,
                Key=self._ser_item({"pk": "meta#pawtwin", "sk": "M"}),
            )
        except Exception as exc:  # noqa: BLE001 - report the real reason, never fall back
            raise _unavailable(f"PROBE_FAILED {exc.__class__.__name__}") from exc

    # -- seeding ------------------------------------------------------------

    def _seed_facts(self, owner_id: str) -> None:
        self._put_if_absent(
            {
                **_facts_key(owner_id),
                "owner_id": owner_id,
                "pet_id": DEMO_PET_ID,
                "last_fed_minutes_ago": DEFAULT_FACTS["last_fed_minutes_ago"],
                "daily_dispensed_grams": DEFAULT_FACTS["daily_dispensed_grams"],
                "daily_limit_grams": DEFAULT_FACTS["daily_limit_grams"],
                "single_serving_grams": DEFAULT_FACTS["single_serving_grams"],
                "minimum_interval_minutes": DEFAULT_FACTS["minimum_interval_minutes"],
                "facts_version": 0,
            }
        )

    def _read_facts_version(self, owner_id: str) -> int:
        item = self._get(_facts_key(owner_id))
        return _int(item.get("facts_version")) if item else 0

    # -- runs ---------------------------------------------------------------

    def create_or_get_run(self, owner_id: str, event: EventIn) -> RunRecord:
        # De-dup is carried by the conditional Put on the deterministic run id
        # (uuid5(owner, event_id)), which is the part that MUST be atomic. The
        # facts_version snapshot is a separate read: TransactWriteItems cannot
        # contain a Get, and a slightly stale baseline version here is harmless --
        # the workflow re-reads facts before proposing, and double-dispense is
        # guarded by record_receipt_once, not by this stamp.
        run_id = _run_uuid(owner_id, event.event_id)
        now = _now()
        facts_version = self._read_facts_version(owner_id)
        self._put_if_absent(
            {
                **_run_key(run_id),
                "gpk": f"owner#{owner_id}",
                "gsk": _dt(now),
                "run_id": str(run_id),
                "owner_id": owner_id,
                "event_id": str(event.event_id),
                "state": RunState.QUEUED.value,
                "created_at": _dt(now),
                "facts_version": facts_version,
                "proposal_version": 0,
                "attempt_count": 0,
                "model_calls_used": 0,
                "event_json": event.model_dump_json(),
            }
        )
        record = self.get_run(run_id)
        if record is None:  # pragma: no cover - just put/selected
            raise _unavailable("RUN_MISSING_AFTER_CREATE")
        return record

    def get_run(self, run_id: UUID) -> RunRecord | None:
        item = self._get(_run_key(run_id))
        return _item_to_run(item) if item else None

    def list_runs(self, owner_id: str) -> list[RunRecord]:
        items = self._query_items(f"owner#{owner_id}", forward=False)
        return [_item_to_run(item) for item in items]

    def list_claimable_runs(self, limit: int = 10) -> list[RunRecord]:
        claimable = _state_values(CLAIMABLE_STATES)
        placeholders = ", ".join(f":c{i}" for i in range(len(claimable)))
        expression = (
            f"sk = :rsk AND #state IN ({placeholders}) AND "
            "(attribute_not_exists(lease_until) OR lease_until < :now)"
        )
        values: dict[str, Any] = {
            ":rsk": "R",
            ":now": _dt(_now()),
            **{f":c{i}": state for i, state in enumerate(claimable)},
        }
        # ``state`` is a DynamoDB reserved word: it MUST be aliased as ``#state``.
        items = self._scan(expression, values, names={"#state": "state"})
        items.sort(key=lambda item: item.get("created_at") or "")
        return [_item_to_run(item) for item in items[: max(1, limit)]]

    def count_runs(self, owner_id: str) -> int:
        return self._query_count(f"owner#{owner_id}")

    def save_run(self, record: RunRecord) -> None:
        # Lease fields and attempt_count are deliberately NOT written (owned by
        # claim/renew/release), so saving an analyzed record can never clear the
        # lease this worker holds -- identical to SqliteRepository.save_run.
        client = self._ddb()
        client.update_item(
            TableName=self._table_name,
            Key=self._ser_item(_run_key(record.run_id)),
            UpdateExpression=(
                "SET #state = :state, facts_version = :fv, proposal_version = :pv, "
                "action_digest = :ad, expires_at = :ea, policy_reason = :pr, "
                "failure_reason = :fr, model_calls_used = :mcu, proposal_json = :pj, "
                "receipt_json = :rj, evidence_json = :ej, telemetry_json = :tj"
            ),
            # ``state`` is a reserved word in DynamoDB, so it is aliased.
            ExpressionAttributeNames={"#state": "state"},
            ExpressionAttributeValues=self._av(
                {
                    ":state": record.state.value,
                    ":fv": record.facts_version,
                    ":pv": record.proposal_version,
                    ":ad": record.action_digest,
                    ":ea": _dt(record.expires_at),
                    ":pr": record.policy_reason,
                    ":fr": record.failure_reason,
                    ":mcu": record.model_calls_used,
                    ":pj": record.proposal.model_dump_json() if record.proposal else None,
                    ":rj": record.receipt.model_dump_json() if record.receipt else None,
                    ":ej": _dump_evidence(record.evidence),
                    ":tj": record.telemetry.model_dump_json() if record.telemetry else None,
                }
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
        placeholders = ", ".join(f":c{i}" for i in range(len(claimable)))
        condition = (
            f"sk = :rsk AND #state IN ({placeholders}) AND "
            "(attribute_not_exists(lease_until) OR lease_until < :now)"
        )
        values: dict[str, Any] = {
            ":rsk": "R",
            ":now": _dt(_now()),
            ":w": worker_id,
            ":lu": _dt(lease_until),
            ":one": 1,
            **{f":c{i}": state for i, state in enumerate(claimable)},
        }
        if max_attempts is not None:
            # Atomic ceiling: a read-increment-write from the worker would race.
            condition += " AND attempt_count < :max"
            values[":max"] = max_attempts
        return self._conditional_update(
            _run_key(run_id),
            "SET lease_owner = :w, lease_until = :lu, attempt_count = attempt_count + :one",
            condition,
            values,
            names={"#state": "state"},
        )

    def renew_lease(self, run_id: UUID, worker_id: str, lease_until: datetime) -> bool:
        claimable = _state_values(CLAIMABLE_STATES)
        placeholders = ", ".join(f":c{i}" for i in range(len(claimable)))
        condition = f"lease_owner = :w AND #state IN ({placeholders})"
        values: dict[str, Any] = {
            ":w": worker_id,
            ":lu": _dt(lease_until),
            **{f":c{i}": state for i, state in enumerate(claimable)},
        }
        return self._conditional_update(
            _run_key(run_id),
            "SET lease_until = :lu",
            condition,
            values,
            names={"#state": "state"},
        )

    def release_run(self, run_id: UUID, worker_id: str) -> None:
        client = self._ddb()
        # Not the owner anymore -> silent, matching SQLite ``rowcount != 1``.
        with contextlib.suppress(client.exceptions.ConditionalCheckFailedException):
            client.update_item(
                TableName=self._table_name,
                Key=self._ser_item(_run_key(run_id)),
                UpdateExpression="REMOVE lease_owner, lease_until",
                ConditionExpression="lease_owner = :w",
                ExpressionAttributeValues=self._av({":w": worker_id}),
            )

    def transition_run(self, run_id: UUID, expected: RunState, new: RunState) -> bool:
        """Compare-and-set. The guard that makes "execute at most once" real."""

        return self._conditional_update(
            _run_key(run_id),
            "SET #state = :new",
            "#state = :expected",
            {":new": new.value, ":expected": expected.value},
            names={"#state": "state"},
        )

    # -- facts --------------------------------------------------------------

    def get_facts(self, owner_id: str) -> FactsSnapshot:
        item = self._get(_facts_key(owner_id))
        if item is None:
            self._seed_facts(owner_id)
            item = self._get(_facts_key(owner_id))
        if item is None:  # pragma: no cover - just seeded/selected
            raise _unavailable("FACTS_MISSING_AFTER_SEED")
        return _item_to_facts(item)

    def update_facts(
        self,
        owner_id: str,
        *,
        last_fed_minutes_ago: int | None | _Unset = UNSET,
        daily_dispensed_grams: int | None | _Unset = UNSET,
    ) -> FactsSnapshot:
        # Mirror SQLite: seed first (idempotent), then a single conditional-free
        # update that bumps facts_version. ``UNSET`` leaves a column out of the
        # expression entirely; ``None`` writes a DynamoDB NULL so the fact becomes
        # UNKNOWN and feeding fails closed (A09).
        self._seed_facts(owner_id)
        sets: list[str] = []
        values: dict[str, Any] = {}
        for column, value in (
            ("last_fed_minutes_ago", last_fed_minutes_ago),
            ("daily_dispensed_grams", daily_dispensed_grams),
        ):
            if isinstance(value, _Unset):
                continue
            sets.append(f"{column} = :{column}")
            values[f":{column}"] = value
        sets.append("facts_version = facts_version + :one")
        values[":one"] = 1
        client = self._ddb()
        client.update_item(
            TableName=self._table_name,
            Key=self._ser_item(_facts_key(owner_id)),
            UpdateExpression="SET " + ", ".join(sets),
            ExpressionAttributeValues=self._av(values),
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
        client = self._ddb()
        run_item = self._get(_run_key(run_id))
        if run_item is None:
            # No run to account against; SQLite no-ops when the owner row is absent.
            return False
        owner_id = run_item.get("owner_id")
        now = _dt(_now())
        receipt_item = {
            **_receipt_key(command_id),
            "gpk": f"run#{run_id}",
            "gsk": now,
            "command_id": str(command_id),
            "run_id": str(run_id),
            "receipt_json": receipt.model_dump_json(),
            "created_at": now,
        }
        account = receipt.status == "succeeded" and dispense_grams > 0 and owner_id is not None
        if not account:
            # A failed/unknown or zero-gram receipt is still stored idempotently but
            # never accounts quota (identical to the SQLite branch).
            return self._put_if_absent(receipt_item)

        # Accounting path: one TransactWriteItems so the receipt insert and the
        # quota bump commit together or not at all. If the receipt already exists
        # the Put condition fails, the WHOLE transaction cancels, and the quota is
        # NOT touched -- the DynamoDB equivalent of INSERT OR IGNORE + rowcount.
        self._seed_facts(owner_id)
        try:
            client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": self._ser_item(receipt_item),
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                    {
                        "Update": {
                            "TableName": self._table_name,
                            "Key": self._ser_item(_facts_key(owner_id)),
                            "UpdateExpression": (
                                "SET last_fed_minutes_ago = :zero, "
                                "facts_version = facts_version + :one "
                                "ADD daily_dispensed_grams :g"
                            ),
                            "ExpressionAttributeValues": self._av(
                                {":zero": 0, ":one": 1, ":g": dispense_grams}
                            ),
                        }
                    },
                ]
            )
        except client.exceptions.TransactionCanceledException as exc:
            reasons = exc.response.get("CancellationReasons", [])
            if reasons and reasons[0].get("Code") == "ConditionalCheckFailed":
                return False  # already recorded -> no double accounting
            raise
        return True

    def count_receipts(self, run_id: UUID) -> int:
        return self._query_count(f"run#{run_id}")

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
        # With an idempotency key the id is DETERMINISTIC, so attribute_not_exists
        # makes a retry return the existing item instead of storing a duplicate (one
        # feedback item is never submitted to AgentCore twice). Without a key a
        # fresh uuid4 always inserts.
        feedback_id = (
            _feedback_uuid(owner_id, idempotency_key) if idempotency_key is not None else uuid4()
        )
        self._put_if_absent(
            {
                **_feedback_key(feedback_id),
                "feedback_id": str(feedback_id),
                "owner_id": owner_id,
                "pet_id": pet_id,
                "text": text,
                "scope": scope,
                "memory_status": memory_status,
                "memory_backend": memory_backend,
                "conversation_id": conversation_id,
                "idempotency_key": idempotency_key,
                "created_at": _dt(_now()),
            }
        )
        record = self.get_feedback(feedback_id)
        if record is None:  # pragma: no cover - just inserted/selected
            raise _unavailable("FEEDBACK_MISSING_AFTER_SAVE")
        return record

    def get_feedback(self, feedback_id: UUID) -> FeedbackRecord | None:
        item = self._get(_feedback_key(feedback_id))
        return _item_to_feedback(item) if item else None

    def list_feedback(self, owner_id: str) -> list[FeedbackRecord]:
        items = self._scan("sk = :bsk AND owner_id = :o", {":bsk": "B", ":o": owner_id})
        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return [_item_to_feedback(item) for item in items]

    def list_feedback_pending_extraction(self) -> list[FeedbackRecord]:
        # Compared against MEMORY_PROCESSING (imported from the vocabulary module),
        # never a bare literal (Day-5 ruling 12: the whitelist is not extended).
        items = self._scan(
            "sk = :bsk AND memory_status = :ms AND attribute_exists(agentcore_event_id)",
            {":bsk": "B", ":ms": MEMORY_PROCESSING},
        )
        items.sort(key=lambda item: item.get("created_at") or "")
        return [_item_to_feedback(item) for item in items]

    def set_feedback_status(
        self,
        feedback_id: UUID,
        *,
        memory_status: MemoryStatus,
        agentcore_event_id: str | None = None,
        agentcore_session_id: str | None = None,
        memory_record_ids: list[str] | None = None,
    ) -> FeedbackRecord | None:
        # Day-5 (ruling 11) hard invariant, identical to SqliteRepository: never
        # mark the available status without the real AgentCore record ids that
        # prove it. The literal lives in models.py (MEMORY_AVAILABLE), so the
        # anti-forgery static guard's whitelist stays unchanged (ruling 12).
        if memory_status == MEMORY_AVAILABLE and not memory_record_ids:
            raise ValueError(
                "set_feedback_status(available) requires memory_record_ids"
            )
        sets = ["memory_status = :ms"]
        values: dict[str, Any] = {":ms": memory_status}
        # A ``None`` parameter is OMITTED from the expression, which is the
        # DynamoDB equivalent of SQLite ``COALESCE(?, column)``: keep the stored
        # value. Only an explicitly provided value overwrites.
        if agentcore_event_id is not None:
            sets.append("agentcore_event_id = :aei")
            values[":aei"] = agentcore_event_id
        if agentcore_session_id is not None:
            sets.append("agentcore_session_id = :asi")
            values[":asi"] = agentcore_session_id
        if memory_record_ids is not None:
            sets.append("memory_record_ids_json = :mri")
            values[":mri"] = json.dumps(memory_record_ids)
        updated = self._conditional_update(
            _feedback_key(feedback_id),
            "SET " + ", ".join(sets),
            "attribute_exists(pk)",
            values,
        )
        if not updated:
            return None
        return self.get_feedback(feedback_id)


def _item_to_run(item: dict[str, Any]) -> RunRecord:
    return RunRecord(
        run_id=UUID(item["run_id"]),
        owner_id=item["owner_id"],
        event_id=UUID(item["event_id"]),
        state=RunState(item["state"]),
        created_at=_parse_dt(item["created_at"]),  # type: ignore[arg-type]  # always set on insert
        facts_version=_int(item.get("facts_version")),
        proposal=(
            Proposal.model_validate_json(item["proposal_json"])
            if item.get("proposal_json")
            else None
        ),
        proposal_version=_int(item.get("proposal_version")),
        action_digest=item.get("action_digest"),
        receipt=(
            Receipt.model_validate_json(item["receipt_json"]) if item.get("receipt_json") else None
        ),
        expires_at=_parse_dt(item.get("expires_at")),
        lease_owner=item.get("lease_owner"),
        lease_until=_parse_dt(item.get("lease_until")),
        attempt_count=_int(item.get("attempt_count")),
        policy_reason=item.get("policy_reason"),
        failure_reason=item.get("failure_reason"),
        evidence=_load_evidence(item.get("evidence_json")),
        telemetry=(
            AnalysisTelemetry.model_validate_json(item["telemetry_json"])
            if item.get("telemetry_json")
            else None
        ),
        model_calls_used=_int(item.get("model_calls_used")),
        event=EventIn.model_validate_json(item["event_json"]) if item.get("event_json") else None,
    )


def _item_to_facts(item: dict[str, Any]) -> FactsSnapshot:
    return FactsSnapshot(
        owner_id=item["owner_id"],
        pet_id=item["pet_id"],
        last_fed_minutes_ago=_opt_int(item.get("last_fed_minutes_ago")),
        daily_dispensed_grams=_opt_int(item.get("daily_dispensed_grams")),
        daily_limit_grams=_int(item.get("daily_limit_grams")),
        single_serving_grams=_int(item.get("single_serving_grams")),
        minimum_interval_minutes=_int(item.get("minimum_interval_minutes")),
        facts_version=_int(item.get("facts_version")),
    )


def _item_to_feedback(item: dict[str, Any]) -> FeedbackRecord:
    raw_ids = item.get("memory_record_ids_json")
    return FeedbackRecord(
        feedback_id=UUID(item["feedback_id"]),
        owner_id=item["owner_id"],
        pet_id=item["pet_id"],
        text=item["text"],
        scope=item["scope"],
        memory_status=item["memory_status"],
        memory_backend=item["memory_backend"],
        created_at=_parse_dt(item["created_at"]),  # type: ignore[arg-type]  # always set on insert
        conversation_id=item.get("conversation_id"),
        agentcore_event_id=item.get("agentcore_event_id"),
        agentcore_session_id=item.get("agentcore_session_id"),
        memory_record_ids=json.loads(raw_ids) if raw_ids else [],
        idempotency_key=item.get("idempotency_key"),
    )
