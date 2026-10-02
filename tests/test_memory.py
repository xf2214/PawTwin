"""Memory seam tests (Day-3 gate G2/G3, acceptance A06/A07/A08 structure).

Everything here is LOCAL. The ``StubMemoryService`` is a construction-injected test
double -- it proves the ``source='memory'`` evidence wiring WITHOUT any cloud call,
so a stubbed retrieval is never mistaken for a real AgentCore memory. The real
round trip lives in ``tests/test_agentcore_live.py`` (conditional, named-skipped).
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pawtwin.agent import AgentContext, AnalyzerProposer
from pawtwin.config import Settings
from pawtwin.memory import (
    AgentCoreMemory,
    LocalFakeMemory,
    MemoryRecord,
    MemoryUnavailable,
    StubMemoryService,
    build_memory,
)
from pawtwin.models import (
    UNKNOWN_EVIDENCE,
    Action,
    AnalysisOutcome,
    AnalysisTelemetry,
    EventIn,
    Proposal,
    validate_proposal_evidence,
)
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _attention_event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="attention_request", room="living_room")


class MemoryCitingAnalyzer:
    """A local analyzer that really calls the memory tool and cites what it got.

    ``label`` stays ``local_fake``: it makes no model call. It exists only to prove
    that a retrieved memory becomes citable ``source='memory'`` evidence.
    """

    label = "local_fake"

    def __init__(self, *, cite: str | None = None) -> None:
        self._cite = cite  # when set, cite this id instead of what was retrieved

    def analyze_event(self, event: EventIn, context: AgentContext) -> AnalysisOutcome:
        started = _now()
        facts = context.get_pet_facts(context.pet_id)
        memories = context.search_owner_memory(context.pet_id, "play after meals")
        evidence_ids = [facts["evidence_id"]]
        if self._cite is not None:
            evidence_ids.append(self._cite)
        else:
            evidence_ids.extend(m["evidence_id"] for m in memories)
        action = (
            Action(kind="create_play_task", grams=0)
            if memories
            else Action(kind="observe", grams=0)
        )
        proposal = Proposal(
            action=action,
            explanation="owner-observation-informed play suggestion (test analyzer)",
            evidence_ids=evidence_ids,
        )
        finished = _now()
        return AnalysisOutcome(
            proposal=proposal,
            evidence=context.evidence_ledger(),
            telemetry=AnalysisTelemetry(
                backend="local_fake",
                model_calls=0,
                output_tokens=0,
                duration_ms=max(0, int((finished - started).total_seconds() * 1000)),
                started_at=started,
                finished_at=finished,
            ),
        )


# --- the honest local backend (G2) ------------------------------------------


def test_local_memory_saves_raw_but_never_claims_extraction() -> None:
    memory = LocalFakeMemory()
    result = memory.submit_feedback(
        feedback_id=uuid4(),
        owner_id=DEMO_OWNER_ID,
        pet_id="mochi",
        text="I notice she looks for play after meals.",
        scope="observation",
        conversation_id="conv-1",
    )
    # ``saved`` = the raw text is stored. It is NEVER ``available``/``processing``:
    # no extraction job runs locally, and claiming one would be a distortion.
    assert result.memory_status == "saved"
    assert result.memory_backend == "not_implemented"
    assert result.memory_record_ids == []
    assert result.agentcore_event_id is None


def test_local_memory_get_status_stays_saved() -> None:
    memory = LocalFakeMemory()
    result = memory.get_status(uuid4())
    assert result.memory_status == "saved"
    assert result.memory_record_ids == []


def test_local_memory_search_returns_nothing_rather_than_a_fabricated_memory() -> None:
    memory = LocalFakeMemory()
    assert memory.search(owner_id=DEMO_OWNER_ID, pet_id="mochi", query="anything") == []


@pytest.mark.parametrize("scope", ["observation", "today_only"])
def test_both_scopes_are_saved_locally_without_becoming_a_preference(scope: str) -> None:
    """A07 (structure): neither scope is extracted into a permanent preference
    locally; ``today_only`` in particular must never be turned into a lasting trait.
    """

    memory = LocalFakeMemory()
    result = memory.submit_feedback(
        feedback_id=uuid4(),
        owner_id=DEMO_OWNER_ID,
        pet_id="mochi",
        text="she seemed restless tonight",
        scope=scope,  # type: ignore[arg-type]
        conversation_id=None,
    )
    assert result.memory_status == "saved"
    assert result.memory_record_ids == []


# --- the memory tool wiring (G3) --------------------------------------------


def test_no_memory_service_returns_empty_and_records_no_evidence(
    repo: SqliteRepository,
) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID)  # memory=None
    assert context.search_owner_memory("mochi", "q") == []
    assert context.evidence_ledger() == []
    assert context.tool_calls == 1  # the attempt is counted, but nothing is cited


def test_local_memory_records_no_evidence_in_the_agent_context(
    repo: SqliteRepository, memory_service: LocalFakeMemory
) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID, memory=memory_service)
    assert context.search_owner_memory("mochi", "q") == []
    assert [item for item in context.evidence_ledger() if item.source == "memory"] == []


def test_a_retrieved_record_becomes_citable_memory_evidence(
    repo: SqliteRepository,
) -> None:
    stub = StubMemoryService(
        records=[
            MemoryRecord(
                record_id="mem-42",
                namespace=f"{DEMO_OWNER_ID}/mochi",
                summary="owner observed post-meal play seeking",
            )
        ]
    )
    context = AgentContext(repo, DEMO_OWNER_ID, memory=stub)

    results = context.search_owner_memory("mochi", "play after meals")

    assert [r["evidence_id"] for r in results] == ["memory:mem-42"]
    assert results[0]["source"] == "memory"
    memory_evidence = [i for i in context.evidence_ledger() if i.source == "memory"]
    assert len(memory_evidence) == 1
    assert memory_evidence[0].tool == "search_owner_memory"
    assert memory_evidence[0].evidence_id == "memory:mem-42"
    # A proposal may cite exactly what was retrieved.
    proposal = Proposal(
        action=Action(kind="create_play_task", grams=0),
        explanation="informed by the owner observation",
        evidence_ids=["memory:mem-42"],
    )
    validate_proposal_evidence(proposal, context.retrieved_evidence_ids())
    assert stub.queries == ["play after meals"]


def test_an_invented_memory_id_is_still_rejected(repo: SqliteRepository) -> None:
    stub = StubMemoryService(records=[])  # nothing retrieved
    context = AgentContext(repo, DEMO_OWNER_ID, memory=stub)
    context.search_owner_memory("mochi", "q")
    proposal = Proposal(
        action=Action(kind="observe", grams=0),
        explanation="cites a memory that was never returned",
        evidence_ids=["memory:not-real"],
    )
    with pytest.raises(ValueError, match=UNKNOWN_EVIDENCE):
        validate_proposal_evidence(proposal, context.retrieved_evidence_ids())


def test_a_stub_memory_record_flows_through_the_analyzer_seam(
    repo: SqliteRepository,
) -> None:
    """End-to-end through AnalyzerProposer: a retrieved memory influences the cited
    evidence and the proposed action, and evidence validation still passes.

    This is the LOCAL wiring for scenario C. The real "memory changes the advice"
    demo needs a genuine AgentCore retrieval and stays a CONDITION item.
    """

    stub = StubMemoryService(
        records=[
            MemoryRecord(
                record_id="mem-7",
                namespace=f"{DEMO_OWNER_ID}/mochi",
                summary="owner says she sometimes wants company after eating",
            )
        ]
    )
    proposer = AnalyzerProposer(MemoryCitingAnalyzer(), repo, memory=stub)

    snapshot = repo.get_facts(DEMO_OWNER_ID)
    outcome = proposer.analyze_event(_attention_event(), snapshot, DEMO_OWNER_ID)

    assert "memory:mem-7" in outcome.proposal.evidence_ids
    assert outcome.proposal.action.kind == "create_play_task"
    memory_evidence = [e for e in outcome.evidence if e.source == "memory"]
    assert [e.evidence_id for e in memory_evidence] == ["memory:mem-7"]


def test_analyzer_citing_an_unretrieved_memory_fails_closed(
    repo: SqliteRepository,
) -> None:
    stub = StubMemoryService(records=[])  # retrieves nothing
    proposer = AnalyzerProposer(MemoryCitingAnalyzer(cite="memory:hallucinated"), repo, memory=stub)
    with pytest.raises(ValueError, match=UNKNOWN_EVIDENCE):
        proposer.analyze_event(_attention_event(), repo.get_facts(DEMO_OWNER_ID), DEMO_OWNER_ID)


# --- the real adapter fails closed, never fabricates (尽力项) ----------------


def test_agentcore_without_a_client_fails_closed_on_retrieve() -> None:
    memory = AgentCoreMemory("mem-id", region="us-west-2")  # no client injected
    with pytest.raises(MemoryUnavailable):
        memory.search(owner_id=DEMO_OWNER_ID, pet_id="mochi", query="q")


def test_agentcore_with_a_missing_memory_id_fails_closed() -> None:
    # The id is validated when the real client is built (lazily), exactly like
    # BedrockAgent: construction is cheap, but any USE fails closed.
    memory = AgentCoreMemory("", region="us-west-2")
    with pytest.raises(MemoryUnavailable):
        memory.search(owner_id=DEMO_OWNER_ID, pet_id="mochi", query="q")


# --- factory + config wiring ------------------------------------------------


def test_build_memory_selects_the_honest_local_backend_by_default() -> None:
    memory = build_memory(Settings(_env_file=None))
    assert isinstance(memory, LocalFakeMemory)
    assert memory.label == "not_implemented"


def test_build_memory_selects_agentcore_only_when_configured() -> None:
    settings = Settings(
        _env_file=None,
        memory_backend="agentcore",
        agentcore_memory_id="mem-id",
        aws_region="us-west-2",
    )
    memory = build_memory(settings)
    assert isinstance(memory, AgentCoreMemory)
    assert memory.label == "agentcore"


def test_agentcore_backend_requires_a_memory_id_and_region() -> None:
    with pytest.raises(ValueError, match="AGENTCORE_MEMORY_ID"):
        Settings(_env_file=None, memory_backend="agentcore")


def test_aws_mode_rejects_unimplemented_memory() -> None:
    with pytest.raises(ValueError, match="PAWTWIN_MEMORY_BACKEND=agentcore"):
        Settings(
            _env_file=None,
            mode="aws",
            memory_backend="not_implemented",
            bedrock_model_id="m",
            aws_region="us-west-2",
            dynamodb_table_name="t",
            agentcore_memory_id="mem",
        )


# --- Day-5: the real AgentCore data plane and the two-stage poll (offline) -----
#
# A stub CLIENT is injected into AgentCoreMemory so the request SHAPE and the
# two-stage poll logic are exercised with zero network and zero credentials. This
# proves wiring and mapping ONLY -- it is explicitly NOT cloud evidence (a real
# round trip lives in tests/test_agentcore_live.py, named-skipped without account).


class _StubAgentCoreClient:
    def __init__(self, *, event_state: str = "processed", records: list | None = None) -> None:
        self._event_state = event_state
        self._records = records or []
        self.create_calls: list[dict] = []
        self.status_calls: list[dict] = []
        self.retrieve_calls: list[dict] = []

    def create_event(self, **kwargs: object) -> str:
        self.create_calls.append(kwargs)
        return "evt-1"

    def event_status(self, **kwargs: object) -> str:
        self.status_calls.append(kwargs)
        return self._event_state

    def retrieve(self, **kwargs: object) -> list:
        self.retrieve_calls.append(kwargs)
        return list(self._records)


def test_namespace_is_the_leading_slash_owner_pet_path() -> None:
    # Ruling 10: paired with the CreateMemory namespaceTemplates in deploy_plan.json.
    assert AgentCoreMemory._namespace("owner-a", "mochi") == "/owner/owner-a/pet/mochi"


def test_agentcore_submit_builds_the_real_create_event_shape() -> None:
    client = _StubAgentCoreClient()
    memory = AgentCoreMemory("mem-id", region="us-west-2", client=client)
    result = memory.submit_feedback(
        feedback_id=uuid4(),
        owner_id="owner-a",
        pet_id="mochi",
        text="she looks for play after meals",
        scope="observation",
        conversation_id="conv-9",
    )
    assert result.memory_status == "processing"
    assert result.agentcore_event_id == "evt-1"
    call = client.create_calls[0]
    # actorId=owner, sessionId=conversation (persisted for GetEvent), text carried,
    # and routing via namespaceVariables (there is NO namespace param on CreateEvent).
    assert call["actor_id"] == "owner-a"
    assert call["session_id"] == "conv-9"
    assert call["text"] == "she looks for play after meals"
    assert call["namespace_variables"] == {"owner": "owner-a", "pet": "mochi"}


def test_two_stage_poll_returns_available_only_with_real_record_ids() -> None:
    client = _StubAgentCoreClient(
        event_state="processed", records=[{"record_id": "rec-1", "summary": "s"}]
    )
    memory = AgentCoreMemory("mem-id", client=client)
    result = memory.get_status(
        uuid4(),
        owner_id="owner-a",
        pet_id="mochi",
        agentcore_event_id="evt-1",
        agentcore_session_id="conv-1",
        query="play",
    )
    assert result.memory_status == "available"
    assert result.memory_record_ids == ["rec-1"]
    # Stage 1 passed the sessionId/actorId GetEvent needs; stage 2 retrieved by path.
    assert client.status_calls[0]["session_id"] == "conv-1"
    assert client.status_calls[0]["actor_id"] == "owner-a"
    assert client.retrieve_calls[0]["namespace_path"] == "/owner/owner-a/pet/mochi"


def test_processed_event_with_empty_retrieval_stays_processing() -> None:
    # Ruling 11: event succeeded but nothing retrievable yet -> never guess available.
    client = _StubAgentCoreClient(event_state="processed", records=[])
    memory = AgentCoreMemory("mem-id", client=client)
    result = memory.get_status(
        uuid4(), owner_id="o", pet_id="mochi", agentcore_event_id="e",
        agentcore_session_id="s", query="q",
    )
    assert result.memory_status == "processing"
    assert result.memory_record_ids == []


def test_non_terminal_event_never_retrieves_or_claims_available() -> None:
    client = _StubAgentCoreClient(event_state="processing", records=[{"record_id": "rec-1"}])
    memory = AgentCoreMemory("mem-id", client=client)
    result = memory.get_status(
        uuid4(), owner_id="o", pet_id="mochi", agentcore_event_id="e",
        agentcore_session_id="s", query="q",
    )
    assert result.memory_status == "processing"
    assert client.retrieve_calls == []  # stage 2 is not reached before terminal


def test_failed_event_reports_failed() -> None:
    client = _StubAgentCoreClient(event_state="failed")
    memory = AgentCoreMemory("mem-id", client=client)
    result = memory.get_status(
        uuid4(), owner_id="o", pet_id="mochi", agentcore_event_id="e",
        agentcore_session_id="s", query="q",
    )
    assert result.memory_status == "failed"


def test_get_status_without_an_event_id_stays_saved() -> None:
    memory = AgentCoreMemory("mem-id", client=_StubAgentCoreClient())
    assert memory.get_status(uuid4()).memory_status == "saved"


# --- Day-5: the worker extraction poller wiring (offline, stub service) --------


def _seed_processing_feedback(repo: SqliteRepository) -> object:
    saved = repo.save_feedback(
        owner_id=DEMO_OWNER_ID,
        pet_id="mochi",
        text="play after meals",
        scope="observation",
        memory_status="saved",
        memory_backend="agentcore",
        conversation_id="conv-1",
    )
    return repo.set_feedback_status(
        saved.feedback_id,
        memory_status="processing",
        agentcore_event_id="evt-1",
        agentcore_session_id="conv-1",
    )


def test_memory_poller_advances_processing_to_available_with_real_ids() -> None:
    from pawtwin.worker import MemoryPoller

    repo = SqliteRepository(":memory:")
    try:
        seeded = _seed_processing_feedback(repo)
        stub = StubMemoryService(
            status="available",
            records=[
                MemoryRecord(
                    record_id="rec-1",
                    namespace="/owner/demo-owner/pet/mochi",
                    summary="owner observed post-meal play",
                )
            ],
        )
        poller = MemoryPoller(repo, stub)
        assert poller.poll_once() == 1
        updated = repo.get_feedback(seeded.feedback_id)
        assert updated.memory_status == "available"
        assert updated.memory_record_ids == ["rec-1"]
        # No longer pending, so a second pass advances nothing.
        assert poller.poll_once() == 0
    finally:
        repo.close()


def test_memory_poller_leaves_feedback_processing_when_the_backend_is_unavailable() -> None:
    from pawtwin.worker import MemoryPoller

    class _Raising:
        label = "agentcore"

        def get_status(self, feedback_id: object, **kwargs: object) -> object:
            raise MemoryUnavailable("MEMORY_UNAVAILABLE: STATUS_FAILED Probe")

    repo = SqliteRepository(":memory:")
    try:
        seeded = _seed_processing_feedback(repo)
        poller = MemoryPoller(repo, _Raising())
        # A poll failure is never a fake success: nothing advances, nothing is forged.
        assert poller.poll_once() == 0
        assert repo.get_feedback(seeded.feedback_id).memory_status == "processing"
    finally:
        repo.close()
