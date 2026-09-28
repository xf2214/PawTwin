"""Real AWS Bedrock AgentCore Memory round trip -- Day-3 CONDITION ITEM, BLOCKED.

Skipped by default through the ``agentcore_live`` marker (see ``addopts`` in
pyproject.toml). Run explicitly, and only inside the budget and scope the user
authorised:

    uv sync --frozen --extra memory
    $env:AGENTCORE_MEMORY_ID = '<memory id>'; $env:AWS_REGION = '<region>'
    ./scripts/agentcore-smoke.ps1          # writes docs/evidence/agentcore-*.md
    uv run --frozen pytest -m agentcore_live

The skip reason is deliberately explicit: AGENTS.md requires a blocked check to be
NAMED, not silently absent. Nothing in this file is cloud-verified today, and no
offline stub or locally-``saved`` feedback may ever be reported as an extracted or
retrieved AgentCore memory.
"""

import pytest

pytestmark = pytest.mark.agentcore_live

SKIP_REASON = (
    "BLOCKED: no AWS account is authorised, so no real AgentCore Memory call is "
    "made. See docs/evidence/day3-cloud-blocked.md. Nothing here is cloud-verified, "
    "and locally-saved feedback is never presented as retrieved memory."
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_memory_strategy_is_active_before_sending_an_observation() -> None:
    """T5: an observation is only sent for long-term extraction once the AgentCore
    memory strategy is ACTIVE, scoped by an owner/pet namespace (the session id is
    never the pet identity). Record the strategy state and namespace in evidence.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_saved_feedback_becomes_available_only_after_real_retrieval() -> None:
    """T5/A06: submit an observation, poll every 10s up to 3 minutes, and only mark
    it ``available`` when a real memory record id, namespace and source association
    can be listed. Until then it stays ``processing`` and is never claimed as
    generated. No pre-filled latency or success rate.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_a_new_session_really_retrieves_the_owners_prior_observation() -> None:
    """Scenario C / A06: after ``demo/new-session`` (a fresh conversation), a related
    event makes the agent cite the owner's earlier observation from a REAL AgentCore
    retrieval, keeping uncertainty, and the evidence panel shows it as
    ``source=memory`` with a real record id -- never a hard-coded new answer.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_a_current_fact_or_hard_quota_overrides_a_conflicting_old_memory() -> None:
    """A08: when a retrieved memory conflicts with the current facts or a hard quota,
    the facts and the program policy win. Memory text never grants approval or lifts
    a quota. Assert the OUTCOME, not the model's wording.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_today_only_feedback_is_not_extracted_into_a_permanent_preference() -> None:
    """A07: a ``today_only`` note stays a time-bounded business record and is never
    turned into a lasting trait by extraction; only ``observation`` may be sent for
    long-term extraction.
    """
