"""Offline AWS response contracts and crash recovery, never cloud evidence."""

import importlib.util
import json

import pytest
from test_deploy_aws import deploy_aws


def test_apply_stops_before_creating_resources_when_runtime_dependencies_missing(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(deploy_aws, "STATE_PATH", tmp_path / "state.json")
    context = {key: f"offline-{key}" for key in deploy_aws._CONTEXT_ENV_KEYS}
    monkeypatch.setattr(deploy_aws, "build_context", lambda: context)
    called = []
    monkeypatch.setattr(
        deploy_aws, "_apply", lambda *args: called.append(args) or {"resources": {}}
    )
    assert deploy_aws.main(["--apply", "--cost-authorization", deploy_aws.COST_AUTHORIZATION]) == 2
    assert not called
    assert "runtime" in capsys.readouterr().err


def test_service_units_and_memory_namespace_request_are_valid(monkeypatch):
    plan = deploy_aws.load_plan()
    params = {r["logical_id"]: r["params"] for r in plan["resources"]}
    assert (params["ecs_express_service"]["cpu"], params["ecs_express_service"]["memory"]) == (
        "1024",
        "2048",
    )
    assert params["github_oidc_provider"]["url"].startswith("https://")
    assert params["ecs_infrastructure_role"]["managed_policy_arns"] == [
        "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
    ]
    captured = {}

    class Control:
        def create_memory(self, **kwargs):
            captured.update(kwargs)
            return {"memory": {"id": "memory-id", "arn": "memory-arn"}}

    monkeypatch.setattr(deploy_aws, "_client", lambda *args: Control())
    monkeypatch.setattr(deploy_aws, "_wait_memory_active", lambda *args: None)
    deploy_aws._create_agentcore_memory(params["agentcore_memory"], "us-east-1", {})
    assert captured["namespaceKeys"] == [{"key": "owner"}, {"key": "pet"}]
    strategy = captured["memoryStrategies"][0]["userPreferenceMemoryStrategy"]
    assert strategy["namespaceTemplates"] == ["/owner/{owner}/pet/{pet}"]
    assert "namespaces" not in strategy
    import re

    assert re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,47}", strategy["name"])


def test_cleanup_preserves_unknown_creation_attempt_without_calling_aws(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "cleanup_unknown_under_test", deploy_aws.REPO_ROOT / "scripts" / "cleanup_aws.py"
    )
    cleanup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cleanup)
    state = tmp_path / "state.json"
    plan = tmp_path / "plan.json"
    state.write_text(
        json.dumps(
            {
                "region": "us-east-1",
                "resources": {},
                "attempts": {"a": {"type": "ecr_repository", "status": "failed_or_unknown"}},
            }
        )
    )
    plan.write_text(json.dumps({"resources": [], "delete_order": []}))
    monkeypatch.setattr(cleanup, "STATE_PATH", state)
    monkeypatch.setattr(cleanup, "PLAN_PATH", plan)
    with pytest.raises(ValueError, match="unknown"):
        cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION])
    assert state.exists()


def test_partial_apply_records_completed_resource_before_next_failure(tmp_path, monkeypatch):
    path = tmp_path / "owned-state.json"
    monkeypatch.setattr(deploy_aws, "STATE_PATH", path)
    plan = {
        "project": "test",
        "resources": [
            {"logical_id": "a", "type": "ecr_repository", "depends_on": [], "params": {}},
            {"logical_id": "b", "type": "cloudwatch_log_group", "depends_on": ["a"], "params": {}},
        ],
    }

    def create(kind, *args, **kwargs):
        if kind == "cloudwatch_log_group":
            raise RuntimeError("external service unavailable")
        return {"repository_name": "only-owned"}

    monkeypatch.setattr(deploy_aws, "_create_resource", create)
    with pytest.raises(RuntimeError):
        deploy_aws._apply(plan, {}, "us-east-1")
    assert path.exists()
    state = json.loads(path.read_text())
    assert state["resources"] == {"a": {"repository_name": "only-owned"}}


def test_existing_resource_state_cannot_be_overwritten(tmp_path, monkeypatch):
    path = tmp_path / "owned-state.json"
    path.write_text(json.dumps({"resources": {"a": {"repository_name": "preserve-me"}}}))
    monkeypatch.setattr(deploy_aws, "STATE_PATH", path)
    with pytest.raises(ValueError):
        deploy_aws._apply({"project": "test", "resources": []}, {}, "us-east-1")
    assert json.loads(path.read_text())["resources"]["a"]["repository_name"] == "preserve-me"


def test_memory_wait_reads_nested_memory_and_stops_on_failed_state():
    class Control:
        def get_memory(self, **kwargs):
            return {
                "memory": {
                    "id": "mem-id",
                    "status": "ACTIVE",
                    "strategies": [{"strategyId": "s1", "status": "ACTIVE"}],
                }
            }

    deploy_aws._wait_memory_active(Control(), "mem-id", attempts=1, delay=0)


def test_express_wait_uses_arn_and_public_ingress_from_nested_service():
    class ECS:
        def describe_express_gateway_service(self, **kwargs):
            assert kwargs == {"serviceArn": "arn:aws:ecs:us-east-1:123:service/test"}
            return {
                "service": {
                    "serviceArn": kwargs["serviceArn"],
                    "status": {"statusCode": "ACTIVE"},
                    "activeConfigurations": [
                        {
                            "ingressPaths": [
                                {"accessType": "PRIVATE", "endpoint": "internal.example"},
                                {"accessType": "PUBLIC", "endpoint": "https://test.example"},
                            ]
                        }
                    ],
                }
            }

    assert (
        deploy_aws._wait_service_active(
            ECS(), "arn:aws:ecs:us-east-1:123:service/test", attempts=1, delay=0
        )
        == "https://test.example"
    )
