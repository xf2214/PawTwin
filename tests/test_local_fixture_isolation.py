"""Local test fixtures must ignore a developer's billable dotenv configuration."""

import importlib

import pytest
from fastapi.testclient import TestClient
from pawtwin.family_assistant import BedrockConverseService


@pytest.fixture
def developer_dotenv(tmp_path, monkeypatch):
    # Use an actual dotenv in a temporary cwd; never touch the checkout's settings
    # or initialize an AWS client, even while reproducing the unsafe old fixtures.
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "PAWTWIN_MODE=local\n"
        "PAWTWIN_FAMILY_MODEL_BACKEND=bedrock\n"
        "AWS_REGION=us-east-1\n"
        "BEDROCK_MODEL_ID=amazon.nova-lite-v1:0\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def reject_cloud_client(self):
        raise AssertionError("Local fixture tried to initialize a billable SDK client")

    monkeypatch.setattr(BedrockConverseService, "client", reject_cloud_client)
    return dotenv


@pytest.mark.parametrize(
    "module_name",
    ["test_family_extension", "test_family_completeness", "test_alexa_simulator"],
)
def test_family_fixture_chat_stays_local_with_developer_dotenv(
    developer_dotenv, tmp_path, module_name
):
    module = importlib.import_module(module_name)
    app = module.app.__wrapped__(tmp_path)
    with TestClient(app) as client:
        login = client.post("/api/login", json={"passphrase": "local-demo-passphrase"})
        assert login.status_code == 200, login.text
        client.headers["x-csrf-token"] = login.json()["csrf_token"]
        assert client.get("/api/family/me").status_code == 200
        response = client.post(
            "/api/family/pets/mochi/chat",
            json={"text": "今天有什么观察", "entry": "app"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["backend"] == "local_rules"
        assert response.json()["request_id"] is None


def test_receipt_scenario_uses_local_gate_with_developer_dotenv(developer_dotenv, tmp_path):
    with developer_dotenv.open("a", encoding="utf-8") as handle:
        handle.write("PAWTWIN_DEMO_PASSPHRASE=developer-only-passphrase\n")
    module = importlib.import_module("test_family_receipts")
    module.test_successful_simulator_receipt_is_reported_separately_from_intake(tmp_path)


def test_auth_scenario_uses_fixture_gate_with_developer_dotenv(developer_dotenv, client):
    with developer_dotenv.open("a", encoding="utf-8") as handle:
        handle.write("PAWTWIN_DEMO_PASSPHRASE=developer-only-passphrase\n")
    module = importlib.import_module("test_auth")
    module.test_login_sets_httponly_samesite_session_and_returns_csrf(client)


@pytest.mark.parametrize(
    ("scenario", "uses_monkeypatch"),
    [
        ("test_local_mode_is_the_safe_default", False),
        ("test_invalid_mode_is_rejected", True),
        ("test_aws_mode_lists_every_missing_requirement", True),
        ("test_aws_mode_refuses_to_start_when_the_cloud_probe_fails", True),
        ("test_aws_mode_rejects_the_default_or_a_short_passphrase", True),
    ],
)
def test_settings_scenarios_keep_explicit_environment_semantics(
    developer_dotenv, monkeypatch, scenario, uses_monkeypatch
):
    module = importlib.import_module("test_settings")
    check = getattr(module, scenario)
    if uses_monkeypatch:
        check(monkeypatch)
    else:
        check()
