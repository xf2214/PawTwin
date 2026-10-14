#!/usr/bin/env python
"""Read-only, ZERO-COST AWS readiness probe for PawTwin (Day-5 G0 / ruling 3).

Confirms the account is reachable and reports exactly what a real deployment needs,
without creating anything or invoking any billable model:

* ``sts.get_caller_identity``  -- the account/identity actually in use (the account
  id is NOT a secret and may appear in evidence; credentials NEVER do).
* ``bedrock-agentcore-control.list_memories`` -- AgentCore control-plane reachability
  in the target region.
* ``bedrock.list_foundation_models`` -- the models the account can see, so the user
  picks a model id from a REAL candidate list (ruling 3: region/model are never
  pre-filled; they go only into ``.env``, never into the repo).

It deliberately does NOT call ``bedrock-runtime.Converse``/``InvokeModel`` (those are
billable) -- Bedrock connectivity is proven later by the first real analysis's
``request_id``, not here. Run:

    uv run --frozen --extra bedrock --extra memory python scripts/aws_probe.py

Output is Markdown so it can be pasted into docs/evidence/day5-cloud-probe.md.
"""

from __future__ import annotations

import os
import sys


def _section(title: str) -> None:
    print(f"\n## {title}\n")


def main() -> int:
    failed = False
    region = os.environ.get("AWS_REGION")
    if not region:
        print("NOT EXECUTED: AWS_REGION is not set. No AWS call was made.", file=sys.stderr)
        return 2
    try:
        import boto3
    except ImportError:
        print(
            "NOT EXECUTED: boto3 is not installed. Run with "
            "`uv run --frozen --extra bedrock --extra memory`.",
            file=sys.stderr,
        )
        return 2

    print("# PawTwin Day-5 cloud readiness probe (read-only, zero cost)")
    print(f"\nTarget region: `{region}`. No resource was created; no model was invoked.")

    _section("Caller identity")
    try:
        identity = boto3.client("sts", region_name=region).get_caller_identity()
        # Account id and ARN are not secrets; credentials/session tokens never are
        # printed here (they are not part of this response).
        print(f"- Account: `{identity.get('Account')}`")
        print(f"- Arn: `{identity.get('Arn')}`")
        print(f"- UserId: `{identity.get('UserId')}`")
    except Exception as exc:  # noqa: BLE001 - report the real reason, never guess
        print(f"- FAILED: `{exc.__class__.__name__}: {exc}`")
        print("\nProbe could not confirm identity; do not proceed to apply.", file=sys.stderr)
        return 1

    _section("AgentCore control plane (list_memories)")
    try:
        control = boto3.client("bedrock-agentcore-control", region_name=region)
        memories = control.list_memories()
        listed = memories.get("memorySummaries", memories.get("memories", []))
        print(f"- Reachable. Existing memories: {len(listed)}")
        for memory in listed:
            print(f"  - `{memory.get('id', memory.get('memoryId'))}` {memory.get('name', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"- FAILED: `{exc.__class__.__name__}: {exc}`")
        failed = True

    _section("Bedrock foundation models visible to this account")
    try:
        bedrock = boto3.client("bedrock", region_name=region)
        models = bedrock.list_foundation_models(byOutputModality="TEXT")
        summaries = models.get("modelSummaries", [])
        print(f"- {len(summaries)} textual models listed.")
        print(
            "- Selection criteria (ruling 3): tool calling + structured output + "
            "account-authorized + lowest unit price. The user confirms the model id; "
            "it is NEVER hardcoded here."
        )
        for model in summaries[:40]:
            print(f"  - `{model.get('modelId')}` -- {model.get('providerName', '')}")
    except Exception as exc:  # noqa: BLE001
        print(f"- FAILED: `{exc.__class__.__name__}: {exc}`")
        failed = True

    print(
        "\n---\nNo billable call was made (no Converse/InvokeModel). Bedrock "
        "connectivity is proven later by a real analysis `request_id`, not here."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
