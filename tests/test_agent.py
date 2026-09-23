from uuid import uuid4

import pytest
from pawtwin.agent import (
    UNKNOWN_EVIDENCE,
    AgentContext,
    BedrockAgent,
    build_analyzer,
    validate_proposal_evidence,
)
from pawtwin.config import Settings
from pawtwin.local_fakes import LOCAL_FAKE_LABEL, LocalFakeAgent
from pawtwin.models import Action, EventIn, Proposal
from pawtwin.repo_sqlite import DEMO_OWNER_ID, SqliteRepository


def test_unknown_evidence_id_is_rejected() -> None:
    proposal = Proposal(
        action=Action(kind="observe"), explanation="观察", evidence_ids=["invented-id"]
    )
    with pytest.raises(ValueError, match=UNKNOWN_EVIDENCE):
        validate_proposal_evidence(proposal, available_ids={"fact-1"})


def test_known_evidence_id_passes() -> None:
    proposal = Proposal(action=Action(kind="observe"), explanation="ok", evidence_ids=["fact-1"])
    validate_proposal_evidence(proposal, available_ids={"fact-1"})


def test_context_tools_are_owner_scoped_and_labelled(repo: SqliteRepository) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID)

    facts = context.get_pet_facts(context.pet_id)
    assert facts["source"] == "repository"
    assert facts["evidence_id"].startswith("facts:v")
    # Long-term memory is Day-3; the tool returns an explicitly empty result.
    assert context.search_owner_memory(context.pet_id, "anything") == []
    assert context.get_policy_summary(context.pet_id)["evidence_id"] == "policy:summary"


def test_local_fake_cites_only_real_evidence_and_is_labelled(repo: SqliteRepository) -> None:
    context = AgentContext(repo, DEMO_OWNER_ID)
    agent = LocalFakeAgent()
    event = EventIn(event_id=uuid4(), kind="food_request", room="kitchen")

    proposal = agent.analyze_event(event, context)

    assert agent.label == "local_fake"
    assert LOCAL_FAKE_LABEL in proposal.explanation
    assert proposal.evidence_ids
    assert set(proposal.evidence_ids) <= context.available_evidence_ids()


def test_local_mode_builds_the_labelled_fake(repo: SqliteRepository) -> None:
    analyzer = build_analyzer(Settings(mode="local"), repo)
    assert isinstance(analyzer, LocalFakeAgent)


def test_aws_mode_never_silently_uses_fake(repo: SqliteRepository) -> None:
    settings = Settings(
        mode="aws",
        bedrock_model_id="example-model",
        aws_region="us-west-2",
        dynamodb_table_name="pawtwin-example",
        agentcore_memory_id="memory-example",
    )

    analyzer = build_analyzer(settings, repo)

    assert isinstance(analyzer, BedrockAgent)
    assert not isinstance(analyzer, LocalFakeAgent)
    event = EventIn(event_id=uuid4(), kind="food_request", room="kitchen")
    with pytest.raises(NotImplementedError):
        analyzer.analyze_event(event, AgentContext(repo, DEMO_OWNER_ID))
