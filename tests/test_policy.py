from pawtwin.models import Action
from pawtwin.policy import (
    ALLOWED,
    DAILY_LIMIT_EXCEEDED,
    MISSING_FACTS,
    NON_FEEDING,
    RECENT_FEED,
    SINGLE_SERVING_EXCEEDED,
    Facts,
    evaluate_policy,
)


def facts(**overrides: object) -> Facts:
    base: dict[str, object] = {
        "last_fed_minutes_ago": 360,
        "daily_dispensed_grams": 0,
        "daily_limit_grams": 30,
        "minimum_interval_minutes": 120,
        "single_serving_grams": 15,
    }
    base.update(overrides)
    return Facts(**base)  # type: ignore[arg-type]


def test_recent_feed_blocks_even_if_model_suggests_food() -> None:
    result = evaluate_policy(Action(kind="dispense_food", grams=15), facts(last_fed_minutes_ago=20))
    assert result.allowed is False
    assert result.reason == RECENT_FEED


def test_normal_feeding_within_every_limit_is_allowed() -> None:
    result = evaluate_policy(Action(kind="dispense_food", grams=15), facts())
    assert result.allowed is True
    assert result.reason == ALLOWED


def test_missing_facts_fail_closed() -> None:
    for override in ({"last_fed_minutes_ago": None}, {"daily_dispensed_grams": None}):
        result = evaluate_policy(Action(kind="dispense_food", grams=10), facts(**override))
        assert result.allowed is False
        assert result.reason == MISSING_FACTS


def test_daily_budget_cannot_be_exceeded() -> None:
    result = evaluate_policy(
        Action(kind="dispense_food", grams=15),
        facts(daily_dispensed_grams=20, daily_limit_grams=30),
    )
    assert result.allowed is False
    assert result.reason == DAILY_LIMIT_EXCEEDED


def test_single_serving_ceiling_is_enforced() -> None:
    result = evaluate_policy(
        Action(kind="dispense_food", grams=10),
        facts(single_serving_grams=5),
    )
    assert result.allowed is False
    assert result.reason == SINGLE_SERVING_EXCEEDED


def test_non_feeding_actions_never_touch_the_quota() -> None:
    for kind in ("observe", "create_play_task"):
        result = evaluate_policy(Action(kind=kind, grams=0), facts(last_fed_minutes_ago=1))
        assert result.allowed is True
        assert result.reason == NON_FEEDING
