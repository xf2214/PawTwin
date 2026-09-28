"""Real AWS Bedrock round trip -- Day-2 CONDITION ITEM, currently BLOCKED.

Skipped by default through the ``bedrock_live`` marker (see ``addopts`` in
pyproject.toml). Run explicitly, and only inside the budget and scope the user
authorised:

    uv sync --frozen --extra bedrock
    $env:BEDROCK_MODEL_ID = '<model id>'; $env:AWS_REGION = '<region>'
    ./scripts/bedrock-smoke.ps1          # writes docs/evidence/bedrock-call-*.md
    uv run --frozen pytest -m bedrock_live

The skip reason is deliberately explicit: AGENTS.md requires a blocked check to be
NAMED, not silently absent. Nothing in this file is cloud-verified today, and no
offline stub result may be reported as if it were.
"""

import pytest

pytestmark = pytest.mark.bedrock_live

SKIP_REASON = (
    "BLOCKED: no AWS account is authorised, so no real Bedrock call is made. "
    "See docs/evidence/day2-cloud-blocked.md. Nothing here is cloud-verified."
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_real_bedrock_round_trip_records_a_request_id() -> None:
    """One real call must yield a request id, model id, region, call count,
    output tokens and latency -- recorded verbatim in docs/evidence/, with no
    credential and no hidden reasoning, and no estimated number presented as a
    measured one.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_real_model_participates_in_the_normal_and_repeat_feeding_scenarios() -> None:
    """The five-day spec's Day-2 acceptance: a cloud model takes part in scenario A
    (normal care) and scenario B (already fed). Scenario B must stop feeding based
    on the newly read fact, and a re-delivered event id must not create a second run.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_real_model_proposal_varies_with_the_facts() -> None:
    """A14 with a real model: the same event under different facts must produce a
    different, evidence-backed proposal -- never a scenario-name lookup.
    """


@pytest.mark.skip(reason=SKIP_REASON)
def test_model_in_the_loop_injection_cannot_exceed_the_hard_quota() -> None:
    """A11 with a real model: an injected instruction in the event note must not
    raise grams above the contractual/policy ceiling, must not skip approval, and
    must not widen the tool set. The enforced gate is the application, not the
    prompt -- so the assertion is about the outcome, not about model behaviour.
    """
