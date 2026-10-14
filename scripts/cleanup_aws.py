#!/usr/bin/env python
"""boto3 teardown orchestrator for PawTwin (Day-5 ruling 1; companion to deploy_aws).

Reads the real resource ids from ``infra/deploy_state.json`` (written by
``deploy_aws.py --apply``) and deletes them in the ``delete_order`` declared in
``infra/deploy_plan.json`` -- reverse dependency order -- then READS EACH BACK to
prove it is gone (DoD: "dry-run -> delete -> read back zero residue").

* ``--dry-run`` (default) -- OFFLINE. Lists exactly what would be deleted, using the
  recorded ids. Sends NO AWS request. If there is no state file (nothing was ever
  deployed) it says so and exits non-zero rather than pretending.
* ``--destroy`` -- REAL. Requires ``--cost-authorization I-AUTHORIZE-BILLABLE-READ``
  (listing/deleting billable resources is an account operation). Deletion failures
  are reported as real failures; nothing is claimed as cleaned up unless the read
  back confirms absence.

HONESTY: the delete/read-back request shapes were written from botocore
introspection and have NEVER run against a real account. Resource ids are NEVER
guessed or invented -- they come only from the recorded state file.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Collection
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "infra" / "deploy_plan.json"
STATE_PATH = REPO_ROOT / "infra" / "deploy_state.json"
COST_AUTHORIZATION = "I-AUTHORIZE-BILLABLE-READ"


def _client(service: str, region: str) -> Any:
    import boto3  # lazy: --dry-run must work with no boto3 and no credentials

    return boto3.client(service, region_name=region)


def _delete(resource_type: str, logical_id: str, ids: dict[str, Any], region: str) -> None:
    """Delete one resource and read it back to confirm absence."""

    if resource_type == "ecs_express_service":
        service_arn = ids.get("service_arn")
        if not isinstance(service_arn, str) or not service_arn:
            raise ValueError("ECS cleanup requires recorded service_arn; ARN is never guessed")
        client = _client("ecs", region)
        _request_delete(
            lambda: client.delete_express_gateway_service(serviceArn=service_arn),
            not_found_codes=("ServiceNotFoundException",),
        )
        _await_gone(
            lambda: client.describe_express_gateway_service(serviceArn=service_arn),
            not_found_codes=("ResourceNotFoundException",),
        )
    elif resource_type == "iam_role":
        client = _client("iam", region)
        role_name = _role_name(ids)
        _request_delete(lambda: _delete_role(client, role_name), not_found_codes=("NoSuchEntity",))
        _await_gone(lambda: client.get_role(RoleName=role_name), not_found_codes=("NoSuchEntity",))
    elif resource_type == "iam_oidc_provider":
        client = _client("iam", region)
        provider_arn = ids["oidc_provider_arn"]
        _request_delete(
            lambda: client.delete_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn),
            not_found_codes=("NoSuchEntity",),
        )
        _await_gone(
            lambda: client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn),
            not_found_codes=("NoSuchEntity",),
        )
    elif resource_type == "cloudwatch_log_group":
        client = _client("logs", region)
        log_group_name = ids["log_group_name"]
        _request_delete(
            lambda: client.delete_log_group(logGroupName=log_group_name),
            not_found_codes=("ResourceNotFoundException",),
        )
        _await_gone(
            lambda: _log_group_present(client, log_group_name),
            is_absent=lambda present: present is False,
        )
    elif resource_type == "agentcore_memory":
        client = _client("bedrock-agentcore-control", region)
        memory_id = ids["memory_id"]
        _request_delete(
            lambda: client.delete_memory(memoryId=memory_id),
            not_found_codes=("ResourceNotFoundException",),
        )
        _await_gone(
            lambda: client.get_memory(memoryId=memory_id),
            not_found_codes=("ResourceNotFoundException",),
        )
    elif resource_type == "dynamodb_table":
        client = _client("dynamodb", region)
        table_name = ids["table_name"]
        _request_delete(
            lambda: client.delete_table(TableName=table_name),
            not_found_codes=("ResourceNotFoundException",),
        )
        _await_gone(
            lambda: client.describe_table(TableName=table_name),
            not_found_codes=("ResourceNotFoundException",),
        )
    elif resource_type == "ecr_repository":
        client = _client("ecr", region)
        repo_name = _repo_name(ids)
        # force=True removes any images so the repository can actually be deleted.
        _request_delete(
            lambda: client.delete_repository(repositoryName=repo_name, force=True),
            not_found_codes=("RepositoryNotFoundException",),
        )
        _await_gone(
            lambda: client.describe_repositories(repositoryNames=[repo_name]),
            not_found_codes=("RepositoryNotFoundException",),
        )
    else:
        raise ValueError(f"unknown resource type: {resource_type}")
    print(f"[destroy] confirmed absent {logical_id} ({resource_type})", flush=True)


def _role_name(ids: dict[str, Any]) -> str:
    # The role name is recoverable from the ARN's trailing ``role/<name>``.
    return ids.get("role_name") or ids["role_arn"].split("role/")[-1]


def _repo_name(ids: dict[str, Any]) -> str:
    return ids.get("repository_name") or ids["repository_uri"].split("/")[-1]


def _delete_role(client: Any, role_name: str) -> None:
    attached = client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
    for policy in attached:
        client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
    client.delete_role(RoleName=role_name)


def _request_delete(delete: Callable[[], Any], *, not_found_codes: Collection[str]) -> None:
    """Allow a retry of an already deleted resource; read-back is still mandatory."""
    from botocore.exceptions import ClientError

    try:
        delete()
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in not_found_codes:
            raise


def _log_group_present(client: Any, name: str, *, max_pages: int = 30) -> bool:
    """Prefix matches are not absence evidence until every page is checked."""
    token: str | None = None
    seen_tokens: set[str] = set()
    for _ in range(max_pages):
        params = {"logGroupNamePrefix": name}
        if token is not None:
            params["nextToken"] = token
        response = client.describe_log_groups(**params)
        if any(group["logGroupName"] == name for group in response["logGroups"]):
            return True
        token = response.get("nextToken")
        if not token:
            return False
        if token in seen_tokens:
            raise RuntimeError("log group pagination did not advance; absence unconfirmed")
        seen_tokens.add(token)
    raise TimeoutError("log group pagination limit reached; absence unconfirmed")


def _await_gone(
    describe: Callable[[], Any],
    *,
    not_found_codes: Collection[str] = (),
    is_absent: Callable[[Any], bool] | None = None,
    attempts: int = 30,
    delay: float = 5.0,
) -> None:
    import time

    from botocore.exceptions import ClientError  # lazy: dry-run needs no boto3

    for attempt in range(attempts):
        try:
            response = describe()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in not_found_codes:
                return
            raise
        if is_absent is not None and is_absent(response):
            return
        if attempt + 1 < attempts:
            time.sleep(delay)
    raise TimeoutError("resource still present after delete; read-back did not confirm absence")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="offline listing; no AWS call")
    group.add_argument("--destroy", action="store_true", help="REAL deletion")
    parser.add_argument("--cost-authorization", default="")
    args = parser.parse_args(argv)
    destroy = args.destroy  # default (neither flag) behaves as dry-run listing

    if not STATE_PATH.is_file():
        print(
            "NOT EXECUTED: no infra/deploy_state.json. Nothing has been deployed from "
            "this checkout, so there is nothing to list or destroy (ids are never guessed).",
            file=sys.stderr,
        )
        return 2

    plan = json.loads(PLAN_PATH.read_text("utf-8"))
    state = json.loads(STATE_PATH.read_text("utf-8"))
    region = state.get("region", "")
    by_type = {r["logical_id"]: r["type"] for r in plan["resources"]}

    if not destroy:
        print("dry-run: the following would be deleted, in order (no AWS call made):")
        for logical_id in plan["delete_order"]:
            ids = state["resources"].get(logical_id, {})
            print(f"  - {logical_id} ({by_type.get(logical_id)}): {json.dumps(ids, default=str)}")
        print("No AWS API was called. Nothing was deleted.", file=sys.stderr)
        return 0

    if args.cost_authorization != COST_AUTHORIZATION:
        print(
            f"NOT EXECUTED: --destroy requires --cost-authorization {COST_AUTHORIZATION}. "
            "No AWS call was made.",
            file=sys.stderr,
        )
        return 2

    recorded = {logical_id for logical_id, ids in state["resources"].items() if ids}
    unknown = {
        logical_id
        for logical_id, attempt in state.get("attempts", {}).items()
        if attempt.get("status") != "created" and logical_id not in recorded
    }
    if unknown:
        raise ValueError(
            "unknown creation results require account reconciliation: "
            f"{', '.join(sorted(unknown))}; state retained, no AWS operation performed"
        )
    uncovered = recorded - (set(plan["delete_order"]) & by_type.keys())
    if uncovered:
        raise ValueError(
            "state resources not covered by current deletion plan: "
            f"{', '.join(sorted(uncovered))}; state retained, no AWS operation performed"
        )

    for logical_id in plan["delete_order"]:
        ids = state["resources"].get(logical_id)
        if not ids:
            print(f"[destroy] skip {logical_id}: not present in state", flush=True)
            continue
        _delete(by_type[logical_id], logical_id, ids, region)

    STATE_PATH.unlink(missing_ok=True)
    print("destroy: all recorded resources deleted and read back absent; state file removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
