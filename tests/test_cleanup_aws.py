"""Offline cleanup evidence: SDK-validated requests, no account or network calls."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

boto3 = pytest.importorskip("boto3")
from botocore.exceptions import ClientError, EndpointConnectionError  # noqa: E402
from botocore.stub import Stubber  # noqa: E402

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cleanup_aws.py"
_SPEC = importlib.util.spec_from_file_location("cleanup_aws_under_test", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
cleanup = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cleanup)

_NOW = datetime(2026, 10, 3, tzinfo=UTC)
_SERVICE_ARN = "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-service"
_ROLE_ARN = "arn:aws:iam::123456789012:role/test-role"
_OIDC_ARN = "arn:aws:iam::123456789012:oidc-provider/test.example"
_MEMORY_ID = "test-memory-1234567890"

# Literal expectations come from the installed service models and AWS API docs.
_RESOURCES = [
    (
        "ecs_express_service",
        "ecs",
        {"service_arn": _SERVICE_ARN, "service_name": "test-service"},
        "delete_express_gateway_service",
        {"serviceArn": _SERVICE_ARN},
        "describe_express_gateway_service",
        {"serviceArn": _SERVICE_ARN},
        {"service": {"serviceArn": _SERVICE_ARN, "status": {"statusCode": "DRAINING"}}},
        "ResourceNotFoundException",
    ),
    (
        "iam_role",
        "iam",
        {"role_arn": _ROLE_ARN},
        "delete_role",
        {"RoleName": "test-role"},
        "get_role",
        {"RoleName": "test-role"},
        {
            "Role": {
                "Path": "/",
                "RoleName": "test-role",
                "RoleId": "TESTROLEIDENTIFIER",
                "Arn": _ROLE_ARN,
                "CreateDate": _NOW,
            }
        },
        "NoSuchEntity",
    ),
    (
        "iam_oidc_provider",
        "iam",
        {"oidc_provider_arn": _OIDC_ARN},
        "delete_open_id_connect_provider",
        {"OpenIDConnectProviderArn": _OIDC_ARN},
        "get_open_id_connect_provider",
        {"OpenIDConnectProviderArn": _OIDC_ARN},
        {
            "Url": "test.example",
            "ClientIDList": ["sts.amazonaws.com"],
            "ThumbprintList": ["a" * 40],
            "CreateDate": _NOW,
        },
        "NoSuchEntity",
    ),
    (
        "cloudwatch_log_group",
        "logs",
        {"log_group_name": "/test/app"},
        "delete_log_group",
        {"logGroupName": "/test/app"},
        "describe_log_groups",
        {"logGroupNamePrefix": "/test/app"},
        {"logGroups": [{"logGroupName": "/test/app"}]},
        None,
    ),
    (
        "agentcore_memory",
        "bedrock-agentcore-control",
        {"memory_id": _MEMORY_ID},
        "delete_memory",
        {"memoryId": _MEMORY_ID},
        "get_memory",
        {"memoryId": _MEMORY_ID},
        {
            "memory": {
                "arn": f"arn:aws:bedrock-agentcore:us-east-1:123456789012:memory/{_MEMORY_ID}",
                "id": _MEMORY_ID,
                "name": "test-memory",
                "eventExpiryDuration": 3,
                "status": "DELETING",
                "createdAt": _NOW,
                "updatedAt": _NOW,
            }
        },
        "ResourceNotFoundException",
    ),
    (
        "dynamodb_table",
        "dynamodb",
        {"table_name": "test-table"},
        "delete_table",
        {"TableName": "test-table"},
        "describe_table",
        {"TableName": "test-table"},
        {"Table": {"TableName": "test-table", "TableStatus": "DELETING"}},
        "ResourceNotFoundException",
    ),
    (
        "ecr_repository",
        "ecr",
        {"repository_uri": "example/test-repository"},
        "delete_repository",
        {"repositoryName": "test-repository", "force": True},
        "describe_repositories",
        {"repositoryNames": ["test-repository"]},
        {"repositories": [{"repositoryName": "test-repository"}]},
        "RepositoryNotFoundException",
    ),
]


@pytest.fixture(autouse=True)
def no_network_or_sleep(monkeypatch):
    def reject_network(*args, **kwargs):
        raise AssertionError("cleanup tests must never send a network request")

    monkeypatch.setattr("botocore.httpsession.URLLib3Session.send", reject_network)
    monkeypatch.setattr("time.sleep", lambda _: None)


def _stub_client(monkeypatch, service):
    client = boto3.client(
        service,
        region_name="us-east-1",
        aws_access_key_id="offline-test",
        aws_secret_access_key="offline-test",
    )
    monkeypatch.setattr(cleanup, "_client", lambda _service, _region: client)
    return Stubber(client)


def _queue_delete(stubber, kind, operation, params):
    if kind == "iam_role":
        stubber.add_response(
            "list_attached_role_policies", {"AttachedPolicies": []}, {"RoleName": "test-role"}
        )
    response = {"memoryId": _MEMORY_ID} if kind == "agentcore_memory" else {}
    stubber.add_response(operation, response, params)


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "AccessDenied", "Message": "denied"}}, "Read"),
        EndpointConnectionError(endpoint_url="https://offline.invalid"),
        RuntimeError("malformed read-back"),
    ],
)
def test_waiter_never_treats_access_network_or_local_errors_as_absence(error):
    def describe():
        raise error

    with pytest.raises(type(error)):
        cleanup._await_gone(describe, attempts=1, delay=0)


@pytest.mark.parametrize("resource", _RESOURCES, ids=lambda row: row[0])
def test_each_delete_confirms_read_back_before_reporting_success(resource, monkeypatch, capsys):
    kind, service, ids, delete_op, delete_params, read_op, read_params, present, missing = resource
    with _stub_client(monkeypatch, service) as stubber:
        _queue_delete(stubber, kind, delete_op, delete_params)
        stubber.add_response(read_op, present, read_params)
        if missing:
            stubber.add_client_error(
                read_op, service_error_code=missing, expected_params=read_params
            )
        else:
            stubber.add_response(read_op, {"logGroups": []}, read_params)
        cleanup._delete(kind, "recorded-resource", ids, "us-east-1")
        stubber.assert_no_pending_responses()
    assert "confirmed" in capsys.readouterr().out


@pytest.mark.parametrize("resource", _RESOURCES, ids=lambda row: row[0])
def test_each_delete_fails_on_denied_read_back(resource, monkeypatch, capsys):
    kind, service, ids, delete_op, delete_params, read_op, read_params, _, _ = resource
    with _stub_client(monkeypatch, service) as stubber:
        _queue_delete(stubber, kind, delete_op, delete_params)
        stubber.add_client_error(
            read_op, service_error_code="AccessDeniedException", expected_params=read_params
        )
        with pytest.raises(ClientError):
            cleanup._delete(kind, "recorded-resource", ids, "us-east-1")
        stubber.assert_no_pending_responses()
    assert "confirmed" not in capsys.readouterr().out


def test_log_group_prefix_requires_exact_match_across_pages(monkeypatch):
    with _stub_client(monkeypatch, "logs") as stubber:
        stubber.add_response("delete_log_group", {}, {"logGroupName": "/test/app"})
        stubber.add_response(
            "describe_log_groups",
            {
                "logGroups": [{"logGroupName": "/test/app-other"}],
                "nextToken": "next-page",
            },
            {"logGroupNamePrefix": "/test/app"},
        )
        stubber.add_response(
            "describe_log_groups",
            {
                "logGroups": [{"logGroupName": "/test/app"}],
            },
            {"logGroupNamePrefix": "/test/app", "nextToken": "next-page"},
        )
        stubber.add_response(
            "describe_log_groups",
            {
                "logGroups": [{"logGroupName": "/test/app-other"}],
            },
            {"logGroupNamePrefix": "/test/app"},
        )
        cleanup._delete(
            "cloudwatch_log_group", "logs", {"log_group_name": "/test/app"}, "us-east-1"
        )
        stubber.assert_no_pending_responses()


def test_ecs_never_constructs_service_arn_from_a_name(monkeypatch):
    def reject_client(*args):
        raise AssertionError("missing recorded ARN must fail before constructing a client")

    monkeypatch.setattr(cleanup, "_client", reject_client)
    with pytest.raises(ValueError, match="service_arn"):
        cleanup._delete("ecs_express_service", "ecs", {"service_name": "test-service"}, "us-east-1")


def _state_paths(tmp_path, monkeypatch):
    state_path = tmp_path / "deploy_state.json"
    plan_path = tmp_path / "deploy_plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "resources": [{"logical_id": "memory", "type": "agentcore_memory"}],
                "delete_order": ["memory"],
            }
        ),
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(
            {
                "region": "us-east-1",
                "resources": {"memory": {"memory_id": _MEMORY_ID}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cleanup, "PLAN_PATH", plan_path)
    monkeypatch.setattr(cleanup, "STATE_PATH", state_path)
    return state_path


def test_failed_confirmation_preserves_state(tmp_path, monkeypatch, capsys):
    state_path = _state_paths(tmp_path, monkeypatch)
    original_state = state_path.read_bytes()
    with _stub_client(monkeypatch, "bedrock-agentcore-control") as stubber:
        stubber.add_response("delete_memory", {"memoryId": _MEMORY_ID}, {"memoryId": _MEMORY_ID})
        stubber.add_client_error(
            "get_memory",
            service_error_code="AccessDeniedException",
            expected_params={"memoryId": _MEMORY_ID},
        )
        with pytest.raises(ClientError):
            cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION])
        stubber.assert_no_pending_responses()
    assert state_path.read_bytes() == original_state
    assert "state file removed" not in capsys.readouterr().out


def test_only_confirmed_cleanup_removes_state(tmp_path, monkeypatch):
    state_path = _state_paths(tmp_path, monkeypatch)
    with _stub_client(monkeypatch, "bedrock-agentcore-control") as stubber:
        stubber.add_response("delete_memory", {"memoryId": _MEMORY_ID}, {"memoryId": _MEMORY_ID})
        stubber.add_client_error(
            "get_memory",
            service_error_code="ResourceNotFoundException",
            expected_params={"memoryId": _MEMORY_ID},
        )
        assert cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION]) == 0
        stubber.assert_no_pending_responses()
    assert not state_path.exists()


def test_waiter_has_a_finite_read_limit():
    calls = []

    def describe():
        calls.append("read")
        return {"still": "present"}

    with pytest.raises(TimeoutError):
        cleanup._await_gone(describe, attempts=3, delay=0)
    assert calls == ["read", "read", "read"]


def test_waiter_rejects_a_different_services_not_found_code():
    def describe():
        raise ClientError({"Error": {"Code": "ResourceNotFoundException"}}, "GetRole")

    with pytest.raises(ClientError):
        cleanup._await_gone(describe, not_found_codes={"NoSuchEntity"}, attempts=1, delay=0)


def test_log_group_nonadvancing_pagination_does_not_confirm_absence(monkeypatch, capsys):
    with _stub_client(monkeypatch, "logs") as stubber:
        stubber.add_response("delete_log_group", {}, {"logGroupName": "/test/app"})
        stubber.add_response(
            "describe_log_groups",
            {"logGroups": [], "nextToken": "same"},
            {"logGroupNamePrefix": "/test/app"},
        )
        stubber.add_response(
            "describe_log_groups",
            {"logGroups": [], "nextToken": "same"},
            {"logGroupNamePrefix": "/test/app", "nextToken": "same"},
        )
        with pytest.raises(RuntimeError, match="pagination"):
            cleanup._delete(
                "cloudwatch_log_group", "logs", {"log_group_name": "/test/app"}, "us-east-1"
            )
        stubber.assert_no_pending_responses()
    assert "confirmed" not in capsys.readouterr().out


@pytest.mark.parametrize("resource", _RESOURCES, ids=lambda row: row[0])
def test_already_deleted_resource_still_requires_read_confirmation(resource, monkeypatch, capsys):
    kind, service, ids, delete_op, delete_params, read_op, read_params, _, read_missing = resource
    delete_missing = {
        "ecs_express_service": "ServiceNotFoundException",
        "iam_role": "NoSuchEntity",
        "iam_oidc_provider": "NoSuchEntity",
        "cloudwatch_log_group": "ResourceNotFoundException",
        "agentcore_memory": "ResourceNotFoundException",
        "dynamodb_table": "ResourceNotFoundException",
        "ecr_repository": "RepositoryNotFoundException",
    }[kind]
    with _stub_client(monkeypatch, service) as stubber:
        if kind == "iam_role":
            stubber.add_response(
                "list_attached_role_policies", {"AttachedPolicies": []}, {"RoleName": "test-role"}
            )
        stubber.add_client_error(
            delete_op, service_error_code=delete_missing, expected_params=delete_params
        )
        if read_missing:
            stubber.add_client_error(
                read_op, service_error_code=read_missing, expected_params=read_params
            )
        else:
            stubber.add_response(read_op, {"logGroups": []}, read_params)
        cleanup._delete(kind, "already-deleted", ids, "us-east-1")
        stubber.assert_no_pending_responses()
    assert "confirmed" in capsys.readouterr().out


def test_missing_role_during_policy_listing_requires_read_confirmation(monkeypatch):
    with _stub_client(monkeypatch, "iam") as stubber:
        stubber.add_client_error(
            "list_attached_role_policies",
            service_error_code="NoSuchEntity",
            expected_params={"RoleName": "test-role"},
        )
        stubber.add_client_error(
            "get_role", service_error_code="NoSuchEntity", expected_params={"RoleName": "test-role"}
        )
        cleanup._delete("iam_role", "role", {"role_arn": _ROLE_ARN}, "us-east-1")
        stubber.assert_no_pending_responses()


def test_partial_cleanup_failure_can_be_retried_without_discarding_state(tmp_path, monkeypatch):
    state_path = _state_paths(tmp_path, monkeypatch)
    second_id = "test-second-1234567890"
    cleanup.PLAN_PATH.write_text(
        json.dumps(
            {
                "resources": [
                    {"logical_id": "first", "type": "agentcore_memory"},
                    {"logical_id": "second", "type": "agentcore_memory"},
                ],
                "delete_order": ["first", "second"],
            }
        ),
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(
            {
                "region": "us-east-1",
                "resources": {
                    "first": {"memory_id": _MEMORY_ID},
                    "second": {"memory_id": second_id},
                },
            }
        ),
        encoding="utf-8",
    )
    original_state = state_path.read_bytes()
    with _stub_client(monkeypatch, "bedrock-agentcore-control") as stubber:
        stubber.add_response("delete_memory", {"memoryId": _MEMORY_ID}, {"memoryId": _MEMORY_ID})
        stubber.add_client_error(
            "get_memory",
            service_error_code="ResourceNotFoundException",
            expected_params={"memoryId": _MEMORY_ID},
        )
        stubber.add_response("delete_memory", {"memoryId": second_id}, {"memoryId": second_id})
        stubber.add_client_error(
            "get_memory",
            service_error_code="AccessDeniedException",
            expected_params={"memoryId": second_id},
        )
        with pytest.raises(ClientError):
            cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION])
        assert state_path.read_bytes() == original_state
        stubber.add_client_error(
            "delete_memory",
            service_error_code="ResourceNotFoundException",
            expected_params={"memoryId": _MEMORY_ID},
        )
        stubber.add_client_error(
            "get_memory",
            service_error_code="ResourceNotFoundException",
            expected_params={"memoryId": _MEMORY_ID},
        )
        stubber.add_response("delete_memory", {"memoryId": second_id}, {"memoryId": second_id})
        stubber.add_client_error(
            "get_memory",
            service_error_code="ResourceNotFoundException",
            expected_params={"memoryId": second_id},
        )
        assert cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION]) == 0
        stubber.assert_no_pending_responses()
    assert not state_path.exists()


@pytest.mark.parametrize("case", ["unknown", "omitted_from_order", "missing_type"])
def test_plan_must_cover_every_recorded_resource_before_any_aws_operation(
    case, tmp_path, monkeypatch, capsys
):
    state_path = _state_paths(tmp_path, monkeypatch)
    state_path.write_text(
        json.dumps(
            {
                "region": "us-east-1",
                "resources": {
                    "memory": {"memory_id": _MEMORY_ID},
                    "old_memory": {"memory_id": "old-memory-1234567890"},
                },
            }
        ),
        encoding="utf-8",
    )
    original_state = state_path.read_bytes()
    plan = {
        "resources": [{"logical_id": "memory", "type": "agentcore_memory"}],
        "delete_order": ["memory"],
    }
    if case == "omitted_from_order":
        plan["resources"].append({"logical_id": "old_memory", "type": "agentcore_memory"})
    if case == "missing_type":
        plan["delete_order"].append("old_memory")
    cleanup.PLAN_PATH.write_text(json.dumps(plan), encoding="utf-8")

    def reject_client(*args):
        raise AssertionError("invalid plan must fail before any AWS client is constructed")

    monkeypatch.setattr(cleanup, "_client", reject_client)
    with pytest.raises(ValueError, match="old_memory"):
        cleanup.main(["--destroy", "--cost-authorization", cleanup.COST_AUTHORIZATION])
    assert state_path.read_bytes() == original_state
    assert "confirmed" not in capsys.readouterr().out
