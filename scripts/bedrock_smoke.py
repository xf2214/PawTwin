"""One REAL Bedrock round trip, recorded as evidence.

This is the Day-2 CONDITION item: it only runs when a credential source,
BEDROCK_MODEL_ID and AWS_REGION are all present. It never fabricates a result --
if configuration is missing it reports "NOT EXECUTED" (exit 2), and if the call
fails it reports the failure (exit 1). In neither case is a stand-in substituted.

The printed report is secret-free: request id, model id, region, call count,
tokens, latency and the evidence ids that were really retrieved. No credential,
no full model request and no hidden reasoning is printed.

Storage for this smoke run is in-memory SQLite on purpose: DynamoDB, AgentCore
memory, deployment and access control are verified separately (Day-3/Day-4).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import uuid4

from pawtwin.agent import AgentContext, BedrockAgent
from pawtwin.config import Settings
from pawtwin.models import EventIn
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository

NOT_EXECUTED = 2
CALL_FAILED = 1


def main() -> int:
    try:
        settings = Settings(_env_file=None, model_backend="bedrock")
    except Exception as exc:  # noqa: BLE001 - configuration is incomplete
        print(f"NOT EXECUTED: configuration incomplete ({exc.__class__.__name__}).")
        print("Set BEDROCK_MODEL_ID and AWS_REGION, and authorise a credential source.")
        print("Nothing is claimed as cloud-verified.")
        return NOT_EXECUTED

    repository = SqliteRepository(":memory:")
    agent = BedrockAgent(
        settings.bedrock_model_id or "",
        region=settings.aws_region,
        max_output_tokens=settings.max_output_tokens,
        timeout_seconds=settings.analysis_timeout_seconds,
        max_model_calls=settings.max_model_calls_per_run,
    )
    event = EventIn(
        event_id=uuid4(),
        kind="food_request",
        room="kitchen",
        note="Smoke-test event. This note is untrusted data, not an instruction.",
    )
    context = AgentContext(repository, DEMO_OWNER_ID)

    started = time.monotonic()
    try:
        outcome = agent.analyze_event(event, context)
    except Exception as exc:  # noqa: BLE001 - report the real failure verbatim
        elapsed = int((time.monotonic() - started) * 1000)
        print(f"FAILED after {elapsed} ms: the real call did not succeed ({exc}).")
        print("No stand-in result was substituted; nothing here is cloud-verified.")
        return CALL_FAILED
    finally:
        repository.close()

    elapsed_ms = int((time.monotonic() - started) * 1000)
    telemetry = outcome.telemetry
    deadline_ms = int(settings.analysis_timeout_seconds * 1000)
    evidence = ", ".join(sorted(context.retrieved_evidence_ids())) or "NONE"

    print("# Real Bedrock round trip")
    print()
    print(f"- Timestamp (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}")
    print(f"- Model id: {telemetry.model_id}")
    print(f"- Region: {settings.aws_region}")
    print(f"- Request id: {telemetry.request_id or 'NOT RETURNED BY SDK'}")
    print(
        f"- Model calls: {telemetry.model_calls} "
        f"(ceiling {settings.max_model_calls_per_run})"
    )
    print(
        f"- Output tokens: {telemetry.output_tokens} "
        f"(ceiling {settings.max_output_tokens})"
    )
    print(f"- Wall clock: {elapsed_ms} ms (analysis deadline {deadline_ms} ms)")
    print(
        f"- Proposed action: {outcome.proposal.action.kind} "
        f"grams={outcome.proposal.action.grams}"
    )
    print(f"- Evidence really retrieved: {evidence}")
    print()
    print(
        "Scope: one model round trip only. Storage was in-memory SQLite, so this "
        "does NOT verify DynamoDB, AgentCore memory, deployment or access control."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
