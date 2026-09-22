import pytest
from pawtwin.config import Settings
from pawtwin.main import create_app
from pydantic import ValidationError


def test_local_mode_is_the_safe_default() -> None:
    settings = Settings()

    assert settings.mode == "local"
    assert settings.aws_connected is False


def test_invalid_mode_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAWTWIN_MODE", "preview")

    with pytest.raises(ValidationError):
        Settings()


def test_aws_mode_lists_every_missing_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAWTWIN_MODE", "aws")

    with pytest.raises(ValidationError) as error:
        Settings()

    message = str(error.value)
    assert "BEDROCK_MODEL_ID" in message
    assert "AWS_REGION" in message
    assert "DYNAMODB_TABLE_NAME" in message
    assert "AGENTCORE_MEMORY_ID" in message


def test_fully_configured_aws_mode_fails_until_adapters_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAWTWIN_MODE", "aws")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "example-model")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "pawtwin-example")
    monkeypatch.setenv("AGENTCORE_MEMORY_ID", "memory-example")

    settings = Settings()
    with pytest.raises(NotImplementedError, match="AWS adapters are not implemented"):
        create_app(settings)
