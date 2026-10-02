"""Offline tests for the deployment orchestrator's PURE plan logic (Day-5 ruling 17).

``deploy_aws.py`` is written so that everything except ``--apply`` is a pure
function that sends NO AWS request -- the ``plan`` mode is the aws-cli v1
``--cli-dry-run`` equivalent this environment lacks (fact G-C). These tests exercise
that logic with no boto3 client and no credentials; they prove ordering and
placeholder handling ONLY, never that a resource can be created.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deploy_aws.py"


def _load_orchestrator():
    spec = importlib.util.spec_from_file_location("deploy_aws_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deploy_aws = _load_orchestrator()


def test_resolve_value_substitutes_known_and_tracks_missing_placeholders() -> None:
    missing: set[str] = set()
    out = deploy_aws.resolve_value(
        {"a": "<FOO>", "b": ["<BAR>", "plain"], "n": 7}, {"FOO": "x"}, missing
    )
    assert out == {"a": "x", "b": ["<BAR>", "plain"], "n": 7}
    assert missing == {"BAR"}


def test_build_context_reads_only_the_known_runtime_keys() -> None:
    context = deploy_aws.build_context(
        {"AWS_REGION": "us-west-2", "SOME_UNRELATED_VAR": "z", "ECR_IMAGE_URI": "uri"}
    )
    assert context == {"AWS_REGION": "us-west-2", "ECR_IMAGE_URI": "uri"}


def test_topological_order_creates_dependencies_first() -> None:
    plan = deploy_aws.load_plan()
    order = [r["logical_id"] for r in deploy_aws.topological_order(plan)]
    position = {name: index for index, name in enumerate(order)}
    for resource in plan["resources"]:
        for dependency in resource["depends_on"]:
            assert position[dependency] < position[resource["logical_id"]]
    # The Express service depends on the table, memory, roles and image, so it is last.
    assert order[-1] == "ecs_express_service"


def test_plan_report_names_every_missing_value_without_touching_aws() -> None:
    plan = deploy_aws.load_plan()
    report = deploy_aws.build_plan_report(plan, {})
    assert len(report["steps"]) == len(plan["resources"])
    # With an empty context, the runtime-only placeholders are reported missing so
    # ``plan`` can name them; no boto3 client is constructed anywhere in this path.
    assert "PAWTWIN_DYNAMODB_TABLE_NAME" in report["missing"]
    assert "ECR_IMAGE_URI" in report["missing"]


def test_plan_report_resolves_when_the_context_is_complete() -> None:
    plan = deploy_aws.load_plan()
    context = {key: f"value-{key}" for key in deploy_aws._CONTEXT_ENV_KEYS}
    report = deploy_aws.build_plan_report(plan, context)
    assert report["missing"] == []
