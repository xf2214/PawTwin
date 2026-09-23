from pathlib import Path

import pytest
from pawtwin.contracts import build_domain_schema, build_openapi_schema

# Frozen Day-1 contract: the scaffold health routes plus the business API needed
# for the login -> event -> approval (decline) loop. Demo/feedback routes are
# intentionally deferred (Day-2/Day-3) and are NOT part of this set yet.
ACTIVE_PATHS = {
    "/healthz",
    "/readyz",
    "/api/bootstrap",
    "/api/login",
    "/api/logout",
    "/api/state",
    "/api/events",
    "/api/runs/{run_id}",
    "/api/runs/{run_id}/approval",
}


def test_openapi_contains_the_frozen_business_routes() -> None:
    schema = build_openapi_schema()

    assert set(schema["paths"]) == ACTIVE_PATHS
    # The decline-loop routes are now part of the frozen contract.
    assert "/api/events" in schema["paths"]
    assert "/api/runs/{run_id}/approval" in schema["paths"]


def test_openapi_export_is_offline_local_even_when_runtime_requests_aws(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PAWTWIN_MODE", "aws")
    (tmp_path / ".env").write_text("PAWTWIN_MODE=aws\n", encoding="utf-8")

    schema = build_openapi_schema()

    assert set(schema["paths"]) == ACTIVE_PATHS


def test_domain_schema_exports_each_shared_model_with_forbidden_extras() -> None:
    schema = build_domain_schema()

    models = {"EventIn", "Action", "Proposal", "ApprovalIn", "FeedbackIn", "Receipt"}
    assert models | {"RunState"} <= set(schema["$defs"])
    for name in models:
        assert schema["$defs"][name]["additionalProperties"] is False


def test_domain_schema_exposes_consumer_safe_event_and_action_constraints() -> None:
    definitions = build_domain_schema()["$defs"]

    event = definitions["EventIn"]
    assert set(event["properties"]) == {
        "event_id",
        "pet_id",
        "kind",
        "room",
        "note",
        "source",
    }
    assert event["properties"]["pet_id"]["default"] == "mochi"
    assert event["properties"]["source"]["default"] == "simulator"

    grams = definitions["Action"]["properties"]["grams"]
    assert grams["minimum"] == 0
    assert grams["maximum"] == 15

    assert set(definitions["RunState"]["enum"]) == {
        "queued",
        "analyzing",
        "needs_info",
        "blocked",
        "awaiting_approval",
        "declined",
        "expired",
        "executing",
        "succeeded",
        "failed",
        "unknown",
    }
