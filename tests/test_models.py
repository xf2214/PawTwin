from uuid import uuid4

import pytest
from pawtwin.models import Action, ApprovalIn, EventIn, FeedbackIn, Proposal, Receipt, RunState
from pydantic import ValidationError


def event_payload() -> dict[str, object]:
    return {
        "event_id": str(uuid4()),
        "kind": "food_request",
        "room": "kitchen",
        "note": "Mochi is waiting near the bowl.",
    }


def test_event_accepts_uuid_text_and_rejects_invalid_id_or_surplus_fields() -> None:
    event = EventIn.model_validate(event_payload())
    assert event.pet_id == "mochi"
    assert event.source == "simulator"

    invalid_id = event_payload() | {"event_id": "not-a-uuid"}
    with pytest.raises(ValidationError):
        EventIn.model_validate(invalid_id)

    with pytest.raises(ValidationError):
        EventIn.model_validate(event_payload() | {"owner": "hidden-extra"})


def test_event_rejects_drifted_field_names() -> None:
    with pytest.raises(ValidationError):
        EventIn.model_validate(
            {
                "event_id": str(uuid4()),
                "pet": "mochi",
                "event_type": "food_request",
                "location": "kitchen",
            }
        )


@pytest.mark.parametrize("grams", [1, 15])
def test_food_action_accepts_only_the_inclusive_safe_range(grams: int) -> None:
    assert Action(kind="dispense_food", grams=grams).grams == grams


@pytest.mark.parametrize("grams", [0, 16, -1])
def test_food_action_rejects_amounts_outside_the_safe_range(grams: int) -> None:
    with pytest.raises(ValidationError):
        Action(kind="dispense_food", grams=grams)


@pytest.mark.parametrize("kind", ["create_play_task", "observe"])
def test_non_food_actions_require_zero_grams(kind: str) -> None:
    assert Action(kind=kind, grams=0).grams == 0
    with pytest.raises(ValidationError):
        Action(kind=kind, grams=1)


def test_action_grams_rejects_boolean_and_float_coercion() -> None:
    for grams in (True, 1.0):
        with pytest.raises(ValidationError):
            Action(kind="dispense_food", grams=grams)


def test_proposal_list_defaults_are_independent() -> None:
    first = Proposal(action=Action(kind="observe"), explanation="Need more context")
    second = Proposal(action=Action(kind="observe"), explanation="Still observing")
    first.evidence_ids.append("event-1")

    assert second.evidence_ids == []
    assert second.missing_fields == []


def test_approval_requires_positive_strict_version_and_sha256_digest() -> None:
    valid = ApprovalIn(
        decision="approve",
        proposal_version=1,
        action_digest="a" * 64,
    )
    assert valid.proposal_version == 1

    for version in (0, -1, True, 1.0):
        with pytest.raises(ValidationError):
            ApprovalIn(
                decision="approve",
                proposal_version=version,
                action_digest="a" * 64,
            )

    for digest in ("a" * 63, "G" * 64, "not-hex"):
        with pytest.raises(ValidationError):
            ApprovalIn(decision="decline", proposal_version=1, action_digest=digest)


def test_feedback_trims_text_and_rejects_blank_or_oversized_text() -> None:
    assert FeedbackIn(text="  Mochi settled down.  ", scope="observation").text == (
        "Mochi settled down."
    )

    for text in ("   ", "x" * 501):
        with pytest.raises(ValidationError):
            FeedbackIn(text=text, scope="today_only")


def test_receipt_requires_simulated_true_and_uuid_command() -> None:
    receipt = Receipt(command_id=str(uuid4()), status="unknown")
    assert receipt.simulated is True

    with pytest.raises(ValidationError):
        Receipt(command_id=str(uuid4()), status="succeeded", simulated=False)
    with pytest.raises(ValidationError):
        Receipt(command_id="not-a-uuid", status="failed")


def test_run_state_vocabulary_matches_the_shared_contract() -> None:
    assert {state.value for state in RunState} == {
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
