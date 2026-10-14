"""Offline service wiring evidence; these tests never contact AWS."""

import pytest
from pawtwin.config import Settings
from pawtwin.main import create_app
from test_family_extension import account, household, write


class ConverseClient:
    def __init__(self, payload=None, failure=False, during=None):
        self.payload = payload or {
            "answer": "Mochi 还没有主人确认的偏好记录。",
            "source_record_ids": [],
        }
        self.failure = failure
        self.during = during
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.during:
            self.during()
        if self.failure:
            raise RuntimeError("a secret SDK error must never reach the browser")
        tool = kwargs["toolConfig"]["toolChoice"]["tool"]["name"]
        return {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"toolUse": {"toolUseId": "tool-1", "name": tool, "input": self.payload}}
                    ],
                }
            },
            "stopReason": "tool_use",
            "usage": {"inputTokens": 900, "outputTokens": 70, "totalTokens": 970},
            "metrics": {"latencyMs": 200},
            "ResponseMetadata": {
                "RequestId": "aws-response-123",
                "HTTPStatusCode": 200,
                "RetryAttempts": 0,
            },
        }


def configured_app(tmp_path, sdk, **overrides):
    settings = Settings(
        _env_file=None,
        database_path=str(tmp_path / "services.db"),
        family_model_backend="bedrock",
        aws_region="us-east-1",
        bedrock_model_id="amazon.nova-lite-v1:0",
        **overrides,
    )
    app = create_app(settings)
    app.state.bedrock_client = sdk
    owner = account(app, "bedrock-owner")
    household(owner)
    return app, owner


@pytest.mark.parametrize("entry", ["app", "alexa_simulator"])
def test_family_entries_use_real_model_response_evidence_without_mutating_home(tmp_path, entry):
    sdk = ConverseClient()
    app, owner = configured_app(tmp_path, sdk)
    before = owner.get("/api/home/state").json()
    reply = write(owner, "/api/family/pets/mochi/chat", text="喜欢什么", entry=entry)
    assert reply["backend"] == "bedrock"
    assert reply["request_id"] == "aws-response-123"
    assert reply["model_id"] == "amazon.nova-lite-v1:0"
    assert (reply["input_tokens"], reply["output_tokens"]) == (900, 70)
    assert reply["action_executed"] is False
    assert reply["care_draft"] is None
    assert owner.get("/api/home/state").json()["revision"] == before["revision"]
    assert len(sdk.calls) == 1
    assert app.state.settings.effective_model_backend == "local_fake"


def test_bedrock_failure_never_returns_local_success_or_raw_sdk_error(tmp_path):
    sdk = ConverseClient(failure=True)
    _, owner = configured_app(tmp_path, sdk)
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert response.status_code == 503
    assert "secret" not in response.text
    assert len(sdk.calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"answer": "来源不存在", "source_record_ids": ["other-household-record"]},
        {"answer": "执行了", "source_record_ids": [], "action_executed": True},
        {"answer": "伪造草案", "source_record_ids": [], "care_draft": {"kind": "feeding"}},
    ],
)
def test_unknown_evidence_and_model_authority_are_rejected(tmp_path, payload):
    _, owner = configured_app(tmp_path, ConverseClient(payload))
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert response.status_code == 503
    assert owner.get("/api/home/state").json()["tasks"] == []


@pytest.mark.parametrize(
    "answer",
    [
        "自动喂食已经完成，已经批准并执行了设备。",
        "The automatic feeder was activated successfully.",
    ],
)
def test_model_cannot_claim_device_execution_in_answer_text(tmp_path, answer):
    _, owner = configured_app(
        tmp_path,
        ConverseClient(
            {
                "answer": answer,
                "source_record_ids": [],
            }
        ),
    )
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "介绍一下Mochi"})
    assert response.status_code == 503


def test_model_may_explain_its_clinical_limit(tmp_path):
    _, owner = configured_app(
        tmp_path,
        ConverseClient(
            {
                "answer": "无法确诊或提供用药剂量，请咨询兽医。",
                "source_record_ids": [],
            }
        ),
    )
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "介绍一下Mochi"})
    assert response.status_code == 200


def test_current_report_is_valid_model_evidence(tmp_path):
    sdk = ConverseClient()
    _, owner = configured_app(tmp_path, sdk)
    report = write(
        owner, "/api/family/pets/mochi/reports/generate", period="daily", date="2026-10-10"
    )
    sdk.payload = {"answer": "当天没有有效体重记录。", "source_record_ids": [report["report_id"]]}
    reply = write(owner, "/api/family/pets/mochi/chat", text="解释日报")
    assert reply["source_record_ids"] == [report["report_id"]]


def test_changed_context_during_inference_rejects_stale_reply(tmp_path):
    sdk = ConverseClient()
    app, owner = configured_app(tmp_path, sdk)
    sdk.during = lambda: app.state.family_store.mutate(
        owner.get("/api/family/me").json()["household"]["household_id"],
        lambda home: home["pets"][0].update(likes="刚刚修正"),
    )
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert response.status_code == 409


def test_persisted_call_limit_survives_app_restart(tmp_path):
    sdk = ConverseClient()
    app, owner = configured_app(tmp_path, sdk, family_model_max_calls=1)
    write(owner, "/api/family/pets/mochi/chat", text="喜欢什么")
    restarted = create_app(app.state.settings)
    restarted.state.bedrock_client = sdk
    from fastapi.testclient import TestClient

    client = TestClient(restarted)
    login = client.post(
        "/api/family/login",
        json={
            "username": "bedrock-owner",
            "password": "test-password-123",
        },
    )
    assert login.status_code == 200
    client.headers["X-CSRF-Token"] = login.json()["csrf_token"]
    denied = client.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert denied.status_code == 429
    assert len(sdk.calls) == 1


def test_requested_automatic_action_is_never_provided_by_model(tmp_path):
    sdk = ConverseClient()
    _, owner = configured_app(tmp_path, sdk)
    reply = write(owner, "/api/family/pets/mochi/chat", text="安排自动喂食")
    assert reply["care_draft"] is None
    assert reply["action_executed"] is False
    assert reply["answer_origin"] == "server_guard"
    assert reply["request_id"] is None
    assert not sdk.calls


def test_photo_recognition_and_chat_share_budget_and_return_candidate(tmp_path):
    PNG = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
        "AAAAC0lEQVR42mP8/x8AAwMCAO+aL1sAAAAASUVORK5CYII="
    )
    sdk = ConverseClient(
        {
            "species": "cat",
            "breed": "",
            "coat": "gold",
            "pattern": "solid",
            "uncertainty": "仅是照片候选，等待主人确认",
        }
    )
    _, owner = configured_app(
        tmp_path, sdk, photo_recognition_enabled=True, family_model_max_calls=1
    )
    photo = write(owner, "/api/home/photos", data_url=PNG)
    candidate = write(owner, f"/api/home/photos/{photo['id']}/recognize")
    assert candidate["confirmed"] is False
    assert candidate["model_id"] == "amazon.nova-lite-v1:0"
    assert candidate["request_id"] == "aws-response-123"
    assert owner.get("/api/home/state").json()["pets"][0]["breed"] == ""
    denied = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert denied.status_code == 429
    assert len(sdk.calls) == 1


def test_missing_bedrock_target_rejects_config_instead_of_staying_local():
    with pytest.raises(ValueError):
        Settings(_env_file=None, family_model_backend="bedrock")


@pytest.mark.parametrize("database_path", [None, ":memory:"])
@pytest.mark.parametrize("entry", ["chat", "photo"])
def test_billable_family_services_require_persistent_budget(database_path, entry):
    with pytest.raises(ValueError, match="persistent"):
        Settings(
            _env_file=None,
            database_path=database_path,
            family_model_backend="bedrock" if entry == "chat" else "local_rules",
            photo_recognition_enabled=entry == "photo",
            aws_region="us-east-1",
            bedrock_model_id="amazon.nova-lite-v1:0",
        )


def test_unknown_usage_retains_reservation_and_blocks_further_spend(tmp_path):
    from decimal import Decimal

    from pawtwin.family_assistant import CONTEXT_TOKENS, INPUT_PRICE, OUTPUT_PRICE

    class MissingUsage(ConverseClient):
        def converse(self, **kwargs):
            response = super().converse(**kwargs)
            response.pop("usage")
            return response

    sdk = MissingUsage()
    app, owner = configured_app(tmp_path, sdk, family_model_budget_usd=Decimal("0.02"))
    assert owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"}).status_code == 503
    ledger = app.state.family_model_ledger.summary()
    assert ledger["calls_reserved"] == 1 and ledger["responses_received"] == 0
    assert Decimal(ledger["accounted_usd"]) == CONTEXT_TOKENS * INPUT_PRICE + 800 * OUTPUT_PRICE
    assert owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"}).status_code == 429
    assert len(sdk.calls) == 1


def test_sdk_failure_keeps_session_slot_until_attempt_really_finishes(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    started, release = Event(), Event()
    sdk = ConverseClient(failure=True)

    def block():
        started.set()
        assert release.wait(5)

    sdk.during = block
    app, owner = configured_app(tmp_path, sdk, max_concurrent_global=1)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(owner.post, "/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
        try:
            assert started.wait(3)
            denied = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
            assert denied.status_code == 429 and denied.json()["detail"] == "MODEL_BUSY"
            assert app.state.family_model_ledger.summary()["calls_reserved"] == 1
        finally:
            release.set()
        assert pending.result(timeout=5).status_code == 503
    assert not app.state.family_model_service.active


def test_session_revoked_during_model_call_cannot_receive_result(tmp_path):
    sdk = ConverseClient()
    app, owner = configured_app(tmp_path, sdk)
    sdk.during = lambda: owner.post("/api/logout")
    response = owner.post("/api/family/pets/mochi/chat", json={"text": "喜欢什么"})
    assert response.status_code == 401
    assert "aws-response-123" not in response.text
