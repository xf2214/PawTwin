"""Readiness exit codes and SDK request boundary; no network or credentials."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location(
    "aws_probe_under_test", Path(__file__).resolve().parents[1] / "scripts" / "aws_probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.parametrize("failed_service", [None, "sts", "bedrock-agentcore-control", "bedrock"])
def test_probe_exits_nonzero_when_any_required_plane_fails(monkeypatch, failed_service):
    calls = []

    def client(service, **kwargs):
        assert kwargs == {"region_name": "us-east-1"}

        def invoke(**params):
            calls.append(service)
            if service == failed_service:
                raise RuntimeError("offline probe failure")
            if service == "sts":
                return {"Account": "offline-test", "Arn": "offline-arn", "UserId": "test"}
            if service == "bedrock-agentcore-control":
                return {"memories": []}
            assert params == {"byOutputModality": "TEXT"}
            return {"modelSummaries": []}

        return SimpleNamespace(
            get_caller_identity=invoke, list_memories=invoke, list_foundation_models=invoke
        )

    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=client))
    assert probe.main() == (1 if failed_service else 0)
    if failed_service == "sts":
        assert calls == ["sts"]
    else:
        assert calls == ["sts", "bedrock-agentcore-control", "bedrock"]
