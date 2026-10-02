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


def test_aws_mode_refuses_to_start_when_the_cloud_probe_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Day-5 ruling 7 replaces the old ``NotImplementedError``: aws mode now assembles
    the REAL adapters and runs a read-only, zero-cost startup probe. With no
    credentials the DynamoDB probe fails closed and ``create_app`` REFUSES to start
    with the real reason -- it never falls back to SQLite or a stand-in (AGENTS.md
    L22). This is the offline half of the gate; a real probe needs an account.
    """

    # Deterministically ensure the probe sees no credential source at all.
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", "/nonexistent/credentials")
    monkeypatch.setenv("AWS_CONFIG_FILE", "/nonexistent/config")
    monkeypatch.setenv("PAWTWIN_MODE", "aws")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "example-model")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "pawtwin-example")
    monkeypatch.setenv("AGENTCORE_MEMORY_ID", "memory-example")
    monkeypatch.setenv("PAWTWIN_DEMO_PASSPHRASE", "a-strong-passphrase-123")

    from pawtwin.repo_dynamo import DynamoUnavailable

    settings = Settings()
    with pytest.raises(DynamoUnavailable):
        create_app(settings)


def test_aws_mode_rejects_the_default_or_a_short_passphrase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Day-5 ruling 4a: a public (``mode=aws``) demo must never ship the built-in
    local passphrase or a trivially short one -- the gate refuses to START. This is
    a hard startup gate, not a runtime check, so the demo cannot come up exposed.
    """

    for key, value in {
        "PAWTWIN_MODE": "aws",
        "BEDROCK_MODEL_ID": "example-model",
        "AWS_REGION": "us-east-1",
        "DYNAMODB_TABLE_NAME": "pawtwin-example",
        "AGENTCORE_MEMORY_ID": "memory-example",
    }.items():
        monkeypatch.setenv(key, value)

    # Built-in default -> rejected.
    with pytest.raises(ValidationError, match="strong PAWTWIN_DEMO_PASSPHRASE"):
        Settings()

    # Too short (< 12 characters) -> rejected.
    monkeypatch.setenv("PAWTWIN_DEMO_PASSPHRASE", "short-pass")
    with pytest.raises(ValidationError, match="strong PAWTWIN_DEMO_PASSPHRASE"):
        Settings()

    # Strong and not the default -> constructs.
    monkeypatch.setenv("PAWTWIN_DEMO_PASSPHRASE", "a-strong-passphrase-123")
    assert Settings().demo_passphrase == "a-strong-passphrase-123"


def test_local_mode_still_allows_the_non_secret_default_passphrase() -> None:
    # Ruling 4a tightens ONLY the aws-mode gate; the local non-secret default and
    # its value are unchanged, so local development and the frozen tests keep working.
    assert Settings(_env_file=None).demo_passphrase == "local-demo-passphrase"
