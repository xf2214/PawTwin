"""One REAL AgentCore Memory round trip, recorded as evidence.

This is the Day-3 CONDITION item: it only runs when a credential source,
AGENTCORE_MEMORY_ID and AWS_REGION are all present (and the optional ``memory``
extra is installed). It never fabricates a result -- missing configuration reports
"NOT EXECUTED" (exit 2), and a failed call reports the failure (exit 1). A locally
``saved`` feedback item is NEVER presented as an extracted or retrieved memory.

The printed report is secret-free: memory id, region, namespace, the AgentCore event
id, the record ids really retrieved and their status. No credential and no hidden
reasoning is printed. Storage for this smoke run is in-memory SQLite on purpose:
DynamoDB, deployment and access control are verified separately (Day-4).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import uuid4

from pawtwin.config import Settings
from pawtwin.memory import AgentCoreMemory
from pawtwin.repo_sqlite import DEMO_OWNER_ID, DEMO_PET_ID

NOT_EXECUTED = 2
CALL_FAILED = 1


def main() -> int:
    try:
        settings = Settings(_env_file=None, memory_backend="agentcore")
    except Exception as exc:  # noqa: BLE001 - configuration is incomplete
        print(f"NOT EXECUTED: configuration incomplete ({exc.__class__.__name__}).")
        print("Set AGENTCORE_MEMORY_ID and AWS_REGION, and authorise a credential source.")
        print("Nothing is claimed as retrieved or cloud-verified.")
        return NOT_EXECUTED

    memory = AgentCoreMemory(settings.agentcore_memory_id or "", region=settings.aws_region)
    feedback_id = uuid4()
    namespace = f"{DEMO_OWNER_ID}/{DEMO_PET_ID}"
    started = time.monotonic()
    try:
        submitted = memory.submit_feedback(
            feedback_id=feedback_id,
            owner_id=DEMO_OWNER_ID,
            pet_id=DEMO_PET_ID,
            text="Smoke-test observation: she sometimes looks for company after meals.",
            scope="observation",
            conversation_id=f"smoke-{feedback_id.hex[:8]}",
        )
        records = memory.search(
            owner_id=DEMO_OWNER_ID, pet_id=DEMO_PET_ID, query="company after meals"
        )
    except Exception as exc:  # noqa: BLE001 - report the real failure verbatim
        elapsed = int((time.monotonic() - started) * 1000)
        print(f"FAILED after {elapsed} ms: the real AgentCore call did not succeed ({exc}).")
        print("No stand-in memory was substituted; nothing here is cloud-verified.")
        return CALL_FAILED

    elapsed_ms = int((time.monotonic() - started) * 1000)
    print("# Real AgentCore Memory round trip")
    print()
    print(f"- Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}")
    print(f"- Memory id: {settings.agentcore_memory_id}")
    print(f"- Region: {settings.aws_region}")
    print(f"- Namespace (owner/pet, never a session id): {namespace}")
    print(f"- Submit status: {submitted.memory_status}")
    print(f"- AgentCore event id: {submitted.agentcore_event_id or 'NOT RETURNED BY SDK'}")
    print(f"- Records retrieved: {len(records)}")
    for record in records:
        print(f"  - record_id={record.record_id} namespace={record.namespace}")
    print(f"- Wall clock: {elapsed_ms} ms")
    print()
    print(
        "Scope: submit + one immediate search only. Extraction is ASYNCHRONOUS, so an "
        "empty result here does NOT mean failure; a real 'available' status needs the "
        "polling lifecycle (strategy ACTIVE, poll until retrievable) verified separately. "
        "Storage was in-memory SQLite, so this does NOT verify DynamoDB, deployment or "
        "access control."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
