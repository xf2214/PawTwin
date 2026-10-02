#!/usr/bin/env python
"""boto3 declarative deployment orchestrator for PawTwin (Day-5 ruling 1/17).

This REPLACES the CDK/CloudFormation path: the development machine has no ``cdk``
and no local Docker (fact G-B), and the Express/AgentCore operations are already in
the locked boto3 (fact G-D). It reads ``infra/deploy_plan.json`` and:

* ``plan``  -- OFFLINE. Sends NO AWS request. Loads the manifest, resolves the
  ``<PLACEHOLDER>`` values from the environment, topologically orders the resources
  and prints exactly what WOULD be created (with any still-missing value named).
  This is the aws-cli v1 ``--cli-dry-run`` equivalent the environment lacks
  (fact G-C), and its pure logic is unit-tested in ``tests/test_deploy_aws.py``.
* ``apply`` -- REAL and BILLABLE. Requires ``--cost-authorization
  I-AUTHORIZE-BILLABLE-DEPLOYMENT`` (the user's written budget approval, AGENTS.md
  L69) AND every placeholder resolved. Creates each resource in dependency order,
  writes the real ARNs/ids to ``infra/deploy_state.json`` (git-ignored), and polls
  the AgentCore memory strategy to ACTIVE before finishing (ruling 13).

HONESTY: the ``apply`` request shapes were written from botocore introspection
(plan §2 / facts G-D..G-I) but have NEVER run against a real account. A failure is
reported as a real failure and never falls back to a stand-in. Region/account are
resolved at runtime only; nothing is hardcoded.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "infra" / "deploy_plan.json"
STATE_PATH = REPO_ROOT / "infra" / "deploy_state.json"
COST_AUTHORIZATION = "I-AUTHORIZE-BILLABLE-DEPLOYMENT"

_PLACEHOLDER = re.compile(r"<([A-Z0-9_]+)>")

# Environment variables that fill ``<PLACEHOLDER>`` values at apply time. They are
# never hardcoded in the manifest and never committed (deploy_state.json is ignored).
_CONTEXT_ENV_KEYS = (
    "PAWTWIN_DYNAMODB_TABLE_NAME",
    "PAWTWIN_AGENTCORE_MEMORY_NAME",
    "ECR_IMAGE_URI",
    "GITHUB_OWNER",
    "GITHUB_REPO",
    "OIDC_THUMBPRINT",
    "GITHUB_OIDC_PROVIDER_ARN",
    "AWS_REGION",
)


# --- pure, offline plan logic (unit-tested; touches NO AWS) --------------------


def load_plan(path: Path = PLAN_PATH) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def build_context(environ: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if environ is None else environ
    return {key: env[key] for key in _CONTEXT_ENV_KEYS if env.get(key)}


def resolve_value(value: Any, context: dict[str, str], missing: set[str]) -> Any:
    """Recursively substitute ``<KEY>`` placeholders from ``context``.

    A placeholder with no context value is recorded in ``missing`` and left as-is so
    ``plan`` can name it. Only fully-resolved strings are returned verbatim.
    """

    if isinstance(value, str):
        def _sub(match: re.Match[str]) -> str:
            key = match.group(1)
            if key in context:
                return context[key]
            missing.add(key)
            return match.group(0)

        return _PLACEHOLDER.sub(_sub, value)
    if isinstance(value, list):
        return [resolve_value(item, context, missing) for item in value]
    if isinstance(value, dict):
        return {k: resolve_value(v, context, missing) for k, v in value.items()}
    return value


def topological_order(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Resources in dependency order (a resource comes after everything it needs)."""

    by_id = {r["logical_id"]: r for r in plan["resources"]}
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()

    def visit(logical_id: str, stack: list[str]) -> None:
        if logical_id in seen:
            return
        if logical_id in stack:
            raise ValueError(f"dependency cycle at {logical_id}: {' -> '.join(stack)}")
        resource = by_id[logical_id]
        for dependency in resource["depends_on"]:
            visit(dependency, [*stack, logical_id])
        seen.add(logical_id)
        ordered.append(resource)

    for logical_id in by_id:
        visit(logical_id, [])
    return ordered


def build_plan_report(plan: dict[str, Any], context: dict[str, str]) -> dict[str, Any]:
    """The offline plan: ordered resources with resolved params and missing values.

    Sends NO AWS request. This is what ``plan`` prints and what the unit test checks.
    """

    missing: set[str] = set()
    steps: list[dict[str, Any]] = []
    for resource in topological_order(plan):
        resolved = resolve_value(resource["params"], context, missing)
        steps.append(
            {
                "logical_id": resource["logical_id"],
                "type": resource["type"],
                "depends_on": resource["depends_on"],
                "params": resolved,
            }
        )
    return {"project": plan["project"], "steps": steps, "missing": sorted(missing)}


# --- real, billable apply path (boto3; NEVER exercised without an account) -----


def _client(service: str, region: str) -> Any:
    import boto3  # lazy: ``plan`` must work with no boto3 and no credentials

    return boto3.client(service, region_name=region)


def _apply(plan: dict[str, Any], context: dict[str, str], region: str) -> dict[str, Any]:
    """Create every resource in dependency order; return the real state mapping.

    Written from botocore-introspected shapes; UNVERIFIED against a real account.
    Any exception propagates as a real failure (no stand-in, no silent success).
    """

    state: dict[str, Any] = {"project": plan["project"], "region": region, "resources": {}}
    tags_map: dict[str, str] = plan.get("tags", {})
    for resource in topological_order(plan):
        params = resolve_value(resource["params"], context, set())
        logical_id = resource["logical_id"]
        print(f"[apply] creating {logical_id} ({resource['type']}) ...", flush=True)
        created = _create_resource(resource["type"], params, context, region, state, tags_map)
        state["resources"][logical_id] = created
    return state


def _create_resource(
    resource_type: str,
    params: dict[str, Any],
    context: dict[str, str],
    region: str,
    state: dict[str, Any],
    tags_map: dict[str, str],
) -> dict[str, Any]:
    tags = [{"Key": k, "Value": v} for k, v in tags_map.items()]
    if resource_type == "ecr_repository":
        client = _client("ecr", region)
        response = client.create_repository(
            repositoryName=params["repository_name"],
            imageTagMutability=params["image_tag_mutability"],
            imageScanningConfiguration={"scanOnPush": params["scan_on_push"]},
            tags=tags,
        )
        repo = response["repository"]
        return {
            "repository_name": params["repository_name"],
            "repository_uri": repo["repositoryUri"],
            "registry_id": repo["registryId"],
        }
    if resource_type == "dynamodb_table":
        client = _client("dynamodb", region)
        response = client.create_table(
            TableName=params["table_name"],
            BillingMode=params["billing_mode"],
            AttributeDefinitions=[
                {"AttributeName": a["attribute_name"], "AttributeType": a["attribute_type"]}
                for a in params["attribute_definitions"]
            ],
            KeySchema=[
                {"AttributeName": k["key_name"], "KeyType": k["key_type"]}
                for k in params["key_schema"]
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": gsi["index_name"],
                    "KeySchema": [
                        {"AttributeName": k["key_name"], "KeyType": k["key_type"]}
                        for k in gsi["key_schema"]
                    ],
                    "Projection": {"ProjectionType": gsi["projection"]["projection_type"]},
                }
                for gsi in params["global_secondary_indexes"]
            ],
            Tags=tags,
        )
        return {
            "table_name": params["table_name"],
            "table_arn": response["TableDescription"]["TableArn"],
        }
    if resource_type == "cloudwatch_log_group":
        client = _client("logs", region)
        client.create_log_group(logGroupName=params["log_group_name"], tags=tags_map)
        client.put_retention_policy(
            logGroupName=params["log_group_name"],
            retentionInDays=params["retention_in_days"],
        )
        return {"log_group_name": params["log_group_name"]}
    if resource_type == "iam_role":
        client = _client("iam", region)
        response = client.create_role(
            RoleName=params["role_name"],
            AssumeRolePolicyDocument=json.dumps(params["assume_role_policy"]),
            Tags=tags,
        )
        for arn in params.get("managed_policy_arns", []):
            client.attach_role_policy(RoleName=params["role_name"], PolicyArn=arn)
        return {"role_name": params["role_name"], "role_arn": response["Role"]["Arn"]}
    if resource_type == "iam_oidc_provider":
        client = _client("iam", region)
        response = client.create_open_id_connect_provider(
            Url=params["url"],
            ClientIDList=params["client_id_list"],
            ThumbprintList=params["thumbprint_list"],
        )
        return {"oidc_provider_arn": response["OpenIDConnectProviderArn"]}
    if resource_type == "agentcore_memory":
        return _create_agentcore_memory(params, region, tags)
    if resource_type == "ecs_express_service":
        return _create_express_service(params, region, state)
    raise ValueError(f"unknown resource type: {resource_type}")


def _create_agentcore_memory(
    params: dict[str, Any], region: str, tags: list[dict[str, str]]
) -> dict[str, Any]:
    client = _client("bedrock-agentcore-control", region)
    response = client.create_memory(
        name=params["name"],
        eventExpiryDuration=params["event_expiry_duration"],
        memoryStrategies=params["memory_strategies"],
        tags=tags,
    )
    memory_id = response["memoryId"]
    # Ruling 13: an event stored before the strategy is ACTIVE is NEVER extracted,
    # so block here until GetMemory reports the strategy ACTIVE (or fail honestly).
    _wait_memory_active(client, memory_id)
    return {"memory_id": memory_id, "memory_arn": response.get("memoryArn")}


def _wait_memory_active(client: Any, memory_id: str, *, attempts: int = 30, delay: float = 10.0):
    for _ in range(attempts):
        described = client.get_memory(memoryId=memory_id)
        statuses = [
            strategy.get("status")
            for strategy in described.get("memoryStrategies", [])
        ]
        if statuses and all(status == "ACTIVE" for status in statuses):
            return
        time.sleep(delay)
    raise TimeoutError(f"AgentCore memory {memory_id} strategy did not reach ACTIVE")


def _create_express_service(
    params: dict[str, Any], region: str, state: dict[str, Any]
) -> dict[str, Any]:
    client = _client("ecs", region)
    resources = state["resources"]
    container = params["primary_container"]
    environment = _container_environment(params, resources)
    response = client.create_express_gateway_service(
        serviceName=params["service_name"],
        cpu=params["cpu"],
        memory=params["memory"],
        cpuArchitecture=params["cpu_architecture"],
        healthCheckPath=params["health_check_path"],
        infrastructureRoleArn=resources["ecs_infrastructure_role"]["role_arn"],
        executionRoleArn=resources["ecs_task_execution_role"]["role_arn"],
        primaryContainer={
            "image": container["image"],
            "containerPort": container["container_port"],
            "environment": environment,
        },
        scalingTarget=params["scaling_target"],
    )
    # There is NO Monitor operation (fact G-D): poll Describe until ACTIVE.
    service_name = response.get("serviceName", params["service_name"])
    url = _wait_service_active(client, service_name)
    return {
        "service_arn": response.get("serviceArn"),
        "service_name": service_name,
        "url": url,
        "cpu": response.get("cpu"),
        "memory": response.get("memory"),
        "scaling_target": response.get("scalingTarget"),
    }


def _container_environment(
    params: dict[str, Any], resources: dict[str, Any]
) -> list[dict[str, str]]:
    """Non-secret env for the container. The passphrase is a SECRET and is injected
    separately at apply time (ruling 14) -- never read from this manifest, never
    written to deploy_state.json, never logged here."""

    container = params["primary_container"]
    values: dict[str, str] = {
        "PAWTWIN_MODE": "aws",
        "PAWTWIN_WORKER_MODE": "background",
        "AWS_REGION": os.environ.get("AWS_REGION", ""),
        "DYNAMODB_TABLE_NAME": os.environ.get("PAWTWIN_DYNAMODB_TABLE_NAME", ""),
        "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID", ""),
        "AGENTCORE_MEMORY_ID": resources.get("agentcore_memory", {}).get("memory_id", ""),
        "PAWTWIN_TRUST_PROXY_HEADERS": "true",
    }
    for key in container.get("environment_public_keys", []):
        if key in os.environ and key not in values:
            values[key] = os.environ[key]
    return [{"name": k, "value": v} for k, v in values.items() if v != ""]


def _wait_service_active(
    client: Any, service_name: str, *, attempts: int = 60, delay: float = 10.0
) -> str:
    url = ""
    for _ in range(attempts):
        described = client.describe_express_gateway_service(serviceName=service_name)
        url = described.get("serviceUrl") or described.get("url") or url
        if str(described.get("statusCode", "")).upper() == "ACTIVE":
            return url
        time.sleep(delay)
    raise TimeoutError(f"Express service {service_name} did not reach ACTIVE")


# --- CLI -----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="offline; sends no AWS request")
    group.add_argument("--apply", action="store_true", help="REAL and BILLABLE")
    parser.add_argument("--cost-authorization", default="")
    args = parser.parse_args(argv)

    plan = load_plan()
    context = build_context()

    if args.plan:
        report = build_plan_report(plan, context)
        print(json.dumps(report, indent=2, default=str))
        if report["missing"]:
            print(
                f"\nplan: {len(report['steps'])} resources would be created; "
                f"MISSING values: {', '.join(report['missing'])}",
                file=sys.stderr,
            )
        else:
            print(f"\nplan: {len(report['steps'])} resources ready to create.", file=sys.stderr)
        print("No AWS API was called. Nothing was created. No cost was incurred.", file=sys.stderr)
        return 0

    # --- apply: hard gates before any billable call ---
    if args.cost_authorization != COST_AUTHORIZATION:
        print(
            f"NOT EXECUTED: --apply requires --cost-authorization {COST_AUTHORIZATION} "
            "(the user's written budget approval). No AWS call was made.",
            file=sys.stderr,
        )
        return 2
    region = context.get("AWS_REGION")
    if not region:
        print("NOT EXECUTED: AWS_REGION is not set. No AWS call was made.", file=sys.stderr)
        return 2
    report = build_plan_report(plan, context)
    if report["missing"]:
        print(
            f"NOT EXECUTED: unresolved placeholders: {', '.join(report['missing'])}. "
            "Supply them in the environment. No AWS call was made.",
            file=sys.stderr,
        )
        return 2

    state = _apply(plan, context, region)
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    print(f"apply: wrote real resource state to {STATE_PATH} (git-ignored).")
    service = state["resources"].get("ecs_express_service", {})
    if service.get("url"):
        print(f"apply: Express service URL = {service['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
