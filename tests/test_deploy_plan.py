"""Offline guards for infra/deploy_plan.json (Day-5 rulings 1/5/9/10/15).

These run with NO credentials and NO AWS call: they validate the declarative
manifest's structure and, critically, pin the AgentCore ``namespaceTemplates`` to
:func:`pawtwin.memory.AgentCoreMemory._namespace` so the two sources cannot drift
(ruling 10's cross-source consistency guard). Nothing here proves a resource was
created -- that only happens in ``scripts/deploy_aws.py -Apply``, gated on the cost
authorization and the user's written budget approval (AGENTS.md L69).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pawtwin.memory import AgentCoreMemory

PLAN_PATH = Path(__file__).resolve().parents[1] / "infra" / "deploy_plan.json"


def _plan() -> dict:
    return json.loads(PLAN_PATH.read_text("utf-8"))


def _resource(plan: dict, logical_id: str) -> dict:
    for resource in plan["resources"]:
        if resource["logical_id"] == logical_id:
            return resource
    raise AssertionError(f"resource {logical_id} not declared in deploy_plan.json")


def test_plan_declares_the_single_table_key_schema_and_entity_index() -> None:
    """Ruling 5: one table, pk(HASH)+sk(RANGE), one entity-index GSI on gpk/gsk,
    PAY_PER_REQUEST, and NO PITR (demo-period data is disposable)."""

    params = _resource(_plan(), "dynamodb_table")["params"]
    assert params["billing_mode"] == "PAY_PER_REQUEST"
    assert {a["attribute_name"] for a in params["attribute_definitions"]} == {
        "pk",
        "sk",
        "gpk",
        "gsk",
    }
    assert {k["key_name"]: k["key_type"] for k in params["key_schema"]} == {
        "pk": "HASH",
        "sk": "RANGE",
    }
    gsi = params["global_secondary_indexes"][0]
    assert gsi["index_name"] == "entity-index"
    assert {k["key_name"]: k["key_type"] for k in gsi["key_schema"]} == {
        "gpk": "HASH",
        "gsk": "RANGE",
    }
    assert gsi["projection"]["projection_type"] == "ALL"
    assert params["point_in_time_recovery"] is False


def test_namespace_templates_pair_exactly_with_the_memory_adapter() -> None:
    """Ruling 10 cross-source guard: the CreateMemory ``namespaceTemplates`` in the
    plan and ``AgentCoreMemory._namespace`` MUST yield the same path for the same
    owner/pet, or an event would be routed to a namespace the retriever never reads
    (and ``available`` could then never be reached honestly).
    """

    params = _resource(_plan(), "agentcore_memory")["params"]
    templates = params["namespace_templates"]
    assert len(templates) == 1
    template = templates[0]
    assert set(params["_namespace_template_keys"]) == {"owner", "pet"}
    for owner, pet in (("owner-a", "mochi"), ("demo-owner", "mochi")):
        assert template.format(owner=owner, pet=pet) == AgentCoreMemory._namespace(owner, pet)


def test_express_service_uses_healthz_and_a_single_replica() -> None:
    params = _resource(_plan(), "ecs_express_service")["params"]
    # Ruling 9: LB/target-group and container health check use /healthz, never /readyz.
    assert params["health_check_path"] == "/healthz"
    # Ruling 15: replicas fixed 1x1 (session, login throttle and concurrency
    # ceilings are process-local; >1 replica would multiply the site-wide ceiling).
    assert params["scaling_target"] == {"min_task_count": 1, "max_task_count": 1}
    assert params["primary_container"]["container_port"] == 8080


def test_delete_order_covers_every_resource_and_reverses_dependencies() -> None:
    plan = _plan()
    ids = {r["logical_id"] for r in plan["resources"]}
    delete_order = plan["delete_order"]
    assert set(delete_order) == ids
    assert len(delete_order) == len(ids)  # no duplicates
    position = {logical_id: index for index, logical_id in enumerate(delete_order)}
    for resource in plan["resources"]:
        for dependency in resource["depends_on"]:
            # A resource must be deleted BEFORE anything it depends on.
            assert position[resource["logical_id"]] < position[dependency], (
                f"{resource['logical_id']} depends on {dependency}, so it must "
                "appear earlier in delete_order"
            )


def test_no_region_or_account_id_is_hardcoded() -> None:
    """Runtime-resolved values appear only as ``<PLACEHOLDERS>``; AWS-managed policy
    ARNs are account-agnostic (``arn:aws:iam::aws:policy/...``) and allowed."""

    text = PLAN_PATH.read_text("utf-8")
    assert "us-east-1" not in text
    assert "us-west-2" not in text
    # No 12-digit AWS account id is baked into the manifest.
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", text)
