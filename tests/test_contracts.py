from pawtwin.contracts import build_domain_schema, build_openapi_schema


def test_openapi_contains_only_active_scaffold_routes() -> None:
    schema = build_openapi_schema()

    assert set(schema["paths"]) == {"/healthz", "/readyz", "/api/bootstrap"}
    assert not any("run" in path or "approval" in path for path in schema["paths"])


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
