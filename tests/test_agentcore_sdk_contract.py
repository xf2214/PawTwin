"""Offline real-response fixtures; no AWS client, credentials or cloud requests."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pawtwin.agentcore_client import AgentCoreMemoryClient
from pawtwin.memory import MemoryUnavailable


def test_create_event_metadata_satisfies_locked_sdk_request_shape(monkeypatch):
    pytest.importorskip("botocore", reason="optional memory SDK is not installed")
    from botocore.session import Session
    from botocore.validate import validate_parameters

    request_shape = Session().get_service_model("bedrock-agentcore").operation_model(
        "CreateEvent"
    ).input_shape

    def create(**request):
        # Validate the actual boundary payload with the installed AWS service model.
        validate_parameters(request, request_shape)
        return {
            "event": {
                "memoryId": request["memoryId"],
                "actorId": request["actorId"],
                "sessionId": request["sessionId"],
                "eventId": "123#abc",
                "eventTimestamp": request["eventTimestamp"],
                "payload": request["payload"],
                "metadata": request["metadata"],
            }
        }

    client = AgentCoreMemoryClient(memory_id="PawTwinMemory-abcdefghij")
    monkeypatch.setattr(client, "_client", lambda: SimpleNamespace(create_event=create))
    assert client.create_event(
        memory_id="PawTwinMemory-abcdefghij",
        actor_id="demo-owner",
        session_id="session-1",
        text="likes play",
        namespace_variables={"owner": "demo-owner", "pet": "mochi"},
        metadata={"scope": "observation", "feedback_id": "feedback-1"},
    ) == "123#abc"


def test_retrieval_surfaces_sdk_memory_record_summaries_and_content_text(monkeypatch):
    # AWS RetrieveMemoryRecords returns memoryRecordSummaries, not memoryRecords.
    response = {
        "memoryRecordSummaries": [
            {
                "memoryRecordId": "record-1",
                "content": {"text": "Mochi prefers play after meals"},
                "memoryStrategyId": "strategy-1",
                "namespaces": ["/owner/demo-owner/pet/mochi"],
                "createdAt": datetime(2026, 10, 3, tzinfo=UTC),
                "score": 0.9,
                "metadata": {},
            }
        ]
    }

    def retrieve(**request):
        assert request == {
            "memoryId": "memory-1",
            "namespacePath": "/owner/demo-owner/pet/mochi",
            "searchCriteria": {"searchQuery": "play", "topK": 5},
        }
        return response

    client = AgentCoreMemoryClient(memory_id="memory-1")
    monkeypatch.setattr(
        client, "_client", lambda: SimpleNamespace(retrieve_memory_records=retrieve)
    )
    assert client.retrieve(
        memory_id="memory-1", namespace_path="/owner/demo-owner/pet/mochi", query="play"
    ) == [{"record_id": "record-1", "summary": "Mochi prefers play after meals"}]


def test_raw_event_without_extraction_status_fails_explicitly(monkeypatch):
    # GetEvent proves a raw event exists. Its official response has no extraction status.
    event = {
        "memoryId": "memory-1",
        "actorId": "demo-owner",
        "sessionId": "session-1",
        "eventId": "123#abc",
        "eventTimestamp": datetime(2026, 10, 3, tzinfo=UTC),
        "payload": [{"conversational": {"content": {"text": "likes play"}, "role": "USER"}}],
        "metadata": {},
    }
    client = AgentCoreMemoryClient(memory_id="memory-1")
    monkeypatch.setattr(
        client, "_client", lambda: SimpleNamespace(get_event=lambda **_: {"event": event})
    )
    with pytest.raises(MemoryUnavailable, match="EVENT_EXTRACTION_STATUS_UNSUPPORTED"):
        client.event_status(
            memory_id="memory-1", event_id="123#abc", session_id="session-1", actor_id="demo-owner"
        )
