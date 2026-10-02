"""AI adapter tests.

Everything here runs OFFLINE: no AWS account, no network, no credentials. Passing
tests in this file prove request construction, evidence discipline and fail-closed
behaviour. They are NOT cloud evidence -- see docs/evidence/day2-cloud-blocked.md.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pawtwin.agent import (
    AgentContext,
    AnalyzerProposer,
    BedrockAgent,
    ModelBudgetExceeded,
    build_analyzer,
    validate_proposal_evidence,
)
from pawtwin.config import Settings
from pawtwin.local_fakes import LOCAL_FAKE_LABEL, LocalFakeAgent
from pawtwin.models import (
    MODEL_CALL_LIMIT,
    UNKNOWN_EVIDENCE,
    Action,
    AnalysisOutcome,
    AnalysisTelemetry,
    EventIn,
    Proposal,
)
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository
from pydantic import ValidationError


def _food_event() -> EventIn:
    return EventIn(event_id=uuid4(), kind="food_request", room="kitchen")


def _now() -> datetime:
    return datetime.now(UTC)


def test_unknown_evidence_id_is_rejected() -> None:
    proposal = Proposal(
        action=Action(kind="observe"), explanation="观察", evidence_ids=["invented-id"]
    )
    with pytest.raises(ValueError, match=UNKNOWN_EVIDENCE):
        validate_proposal_evidence(proposal, available_ids={"fact-1"})


def test_known_evidence_id_passes() -> None:
    proposal = Proposal(action=Action(kind="observe"), explanation="ok", evidence_ids=["fact-1"])
    validate_proposal_evidence(proposal, available_ids={"fact-1"})


def test_empty_evidence_ids_passes() -> None:
    """The inline backend cites nothing because it retrieves nothing."""

    proposal = Proposal(action=Action(kind="observe"), explanation="ok", evidence_ids=[])
    validate_proposal_evidence(proposal, available_ids=set())


def test_context_tools_are_owner_scoped_and_labelled(repo: SqliteRepository) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID)

    facts = context.get_pet_facts(context.pet_id)
    assert facts["source"] == "repository"
    assert facts["evidence_id"].startswith("facts:v")
    # Long-term memory is Day-3; the tool returns an explicitly empty result and
    # records NO evidence, so a memory can never be fabricated into a proposal.
    assert context.search_owner_memory(context.pet_id, "anything") == []
    assert context.get_policy_summary(context.pet_id)["evidence_id"] == "policy:summary"
    assert context.retrieved_evidence_ids() == {"facts:v0", "policy:summary"}


def test_recent_events_expose_state_but_never_the_free_text_note(
    repo: SqliteRepository, food_event: EventIn
) -> None:
    """A11: a past event's note must not become an injection channel."""

    repo.create_or_get_run(DEMO_OWNER_ID, food_event)
    context = AgentContext(repo, DEMO_OWNER_ID)

    recent = context.get_recent_events(context.pet_id)

    assert recent
    joined = repr(recent)
    assert food_event.note not in joined
    assert all(set(item) == {"evidence_id", "pet_id", "state", "source"} for item in recent)


def test_local_fake_cites_only_real_evidence_and_is_labelled(repo: SqliteRepository) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID)
    agent = LocalFakeAgent()

    outcome = agent.analyze_event(_food_event(), context)

    assert agent.label == "local_fake"
    assert LOCAL_FAKE_LABEL in outcome.proposal.explanation
    assert outcome.proposal.evidence_ids
    # Validation uses the RETRIEVED ledger, never a re-query (ruling 3).
    assert set(outcome.proposal.evidence_ids) <= context.retrieved_evidence_ids()
    assert {item.evidence_id for item in outcome.evidence} == context.retrieved_evidence_ids()
    assert all(item.summary for item in outcome.evidence)


def test_local_fake_reports_zero_model_calls_and_no_request_id(repo: SqliteRepository) -> None:
    """Honest telemetry: the stand-in performs no model call and has no request id."""

    context = AgentContext(repo, DEMO_OWNER_ID)

    telemetry = LocalFakeAgent().analyze_event(_food_event(), context).telemetry

    assert telemetry.backend == "local_fake"
    assert telemetry.model_calls == 0
    assert telemetry.output_tokens == 0
    assert telemetry.request_id is None
    assert telemetry.model_id is None


def test_pinned_snapshot_keeps_evidence_valid_when_facts_change_mid_analysis(
    repo: SqliteRepository,
) -> None:
    """Ruling 3: a facts_version bump during analysis must not fake UNKNOWN_EVIDENCE.

    A re-queried id set would reject the proposal, and the policy would end up
    judging older facts than the proposal used (a fail-open).
    """

    snapshot = repo.get_facts(DEMO_OWNER_ID)
    context = AgentContext(repo, DEMO_OWNER_ID, snapshot=snapshot)
    outcome = LocalFakeAgent().analyze_event(_food_event(), context)

    repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=10)

    assert repo.get_facts(DEMO_OWNER_ID).facts_version != snapshot.facts_version
    assert context.snapshot is snapshot
    validate_proposal_evidence(outcome.proposal, context.retrieved_evidence_ids())


def test_local_fake_never_invents_a_quantity_from_an_unknown_fact(
    repo: SqliteRepository,
) -> None:
    """Regression: NULL means UNKNOWN, never 0.

    Coercing it made the stand-in propose 15 g while the policy was judging
    MISSING_FACTS, so the page showed "not enough information" right next to
    "dispense 15 grams, fed None minutes ago".
    """

    repo.update_facts(DEMO_OWNER_ID, last_fed_minutes_ago=None)
    context = AgentContext(repo, DEMO_OWNER_ID)

    outcome = LocalFakeAgent().analyze_event(_food_event(), context)

    assert outcome.proposal.action == Action(kind="observe", grams=0)
    assert outcome.proposal.missing_fields == ["last_fed_minutes_ago"]
    assert "None" not in outcome.proposal.explanation
    assert "缺少必要事实" in outcome.proposal.explanation


def test_local_mode_builds_the_labelled_fake(repo: SqliteRepository) -> None:
    analyzer = build_analyzer(Settings(_env_file=None, mode="local"), repo)
    assert isinstance(analyzer, LocalFakeAgent)


def test_aws_mode_never_silently_uses_fake(repo: SqliteRepository) -> None:
    settings = Settings(
        _env_file=None,
        mode="aws",
        bedrock_model_id="example-model",
        aws_region="us-west-2",
        dynamodb_table_name="pawtwin-example",
        agentcore_memory_id="memory-example",
        # Day-5 ruling 4a: aws mode also requires a strong passphrase; supply one so
        # this analyzer-selection test reaches build_analyzer instead of the gate.
        demo_passphrase="a-strong-passphrase-123",
    )

    analyzer = build_analyzer(settings, repo)

    assert isinstance(analyzer, BedrockAgent)
    assert not isinstance(analyzer, LocalFakeAgent)
    assert analyzer.label == "bedrock"


def test_inline_backend_has_no_analyzer(repo: SqliteRepository) -> None:
    """``inline`` is a workflow-level deterministic backend, not an analyzer."""

    with pytest.raises(ValueError, match="inline"):
        build_analyzer(Settings(_env_file=None, model_backend="inline"), repo)


def test_bedrock_backend_requires_a_model_id_and_region() -> None:
    with pytest.raises(ValidationError, match="BEDROCK_MODEL_ID"):
        Settings(_env_file=None, model_backend="bedrock")


def test_aws_mode_rejects_a_stand_in_analyzer() -> None:
    with pytest.raises(ValidationError, match="PAWTWIN_MODEL_BACKEND=bedrock"):
        Settings(
            _env_file=None,
            mode="aws",
            model_backend="local_fake",
            bedrock_model_id="example-model",
            aws_region="us-west-2",
            dynamodb_table_name="pawtwin-example",
            agentcore_memory_id="memory-example",
        )


# The Bedrock fail-closed and offline-stub cases live in
# tests/test_bedrock_adapter_offline.py; the blocked real-call cases live in
# tests/test_bedrock_live.py (named-skipped, never silently absent).


def test_strands_is_never_imported_without_a_real_call() -> None:
    """Local mode, CI and the contract export must work with the extra absent.

    ``strands`` is imported only inside a real analysis call, so merely importing
    the application -- or the lazily-imported client module -- must not pull it in.
    """

    import sys

    import pawtwin.main  # noqa: F401 - importing the app must not pull in strands

    assert "strands" not in sys.modules


def test_proposer_refuses_a_fifth_model_call(repo: SqliteRepository) -> None:
    """The durable budget is checked BEFORE spending another call."""

    proposer = AnalyzerProposer(LocalFakeAgent(), repo, max_model_calls=4)
    snapshot = repo.get_facts(DEMO_OWNER_ID)

    with pytest.raises(ModelBudgetExceeded) as excinfo:
        proposer.analyze_event(_food_event(), snapshot, DEMO_OWNER_ID, model_calls_used=4)

    assert excinfo.value.reason == MODEL_CALL_LIMIT


def test_proposer_rejects_a_proposal_citing_unretrieved_evidence(
    repo: SqliteRepository,
) -> None:
    class _Liar:
        """Cites an id it never retrieved: the adapter must refuse the proposal."""

        label = "local_fake"

        def analyze_event(self, event: EventIn, context: AgentContext) -> AnalysisOutcome:
            context.get_pet_facts(context.pet_id)
            return AnalysisOutcome(
                proposal=Proposal(
                    action=Action(kind="observe"),
                    explanation="编造依据",
                    evidence_ids=["invented-id"],
                ),
                evidence=context.evidence_ledger(),
                telemetry=AnalysisTelemetry(
                    backend="local_fake",
                    started_at=_now(),
                    finished_at=_now(),
                ),
            )

    proposer = AnalyzerProposer(_Liar(), repo)
    snapshot = repo.get_facts(DEMO_OWNER_ID)

    with pytest.raises(ValueError, match=UNKNOWN_EVIDENCE):
        proposer.analyze_event(_food_event(), snapshot, DEMO_OWNER_ID)
