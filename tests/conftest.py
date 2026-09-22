from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def clear_pawtwin_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in (
        "PAWTWIN_MODE",
        "BEDROCK_MODEL_ID",
        "AWS_REGION",
        "DYNAMODB_TABLE_NAME",
        "AGENTCORE_MEMORY_ID",
        "PAWTWIN_FRONTEND_DIST",
    ):
        monkeypatch.delenv(name, raising=False)
    yield
