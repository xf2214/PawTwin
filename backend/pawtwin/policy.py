"""Hard feeding policy.

Program-decided limits only. Neither model wording nor stored memory may grant
authority here (see AGENTS.md product boundaries). Field names ``Facts`` and
``PolicyResult`` are part of the frozen contract and must not be renamed.
"""

from __future__ import annotations

from dataclasses import dataclass

from pawtwin.models import Action

# Reason codes returned by :func:`evaluate_policy`.
ALLOWED = "ALLOWED"
NON_FEEDING = "NON_FEEDING"
MISSING_FACTS = "MISSING_FACTS"
RECENT_FEED = "RECENT_FEED"
SINGLE_SERVING_EXCEEDED = "SINGLE_SERVING_EXCEEDED"
DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"


@dataclass(frozen=True)
class Facts:
    """Current, application-owned facts used for the feeding decision.

    ``last_fed_minutes_ago`` / ``daily_dispensed_grams`` may be ``None`` when the
    fact is unknown; unknown facts fail closed (feeding is refused).
    """

    last_fed_minutes_ago: int | None
    daily_dispensed_grams: int | None
    daily_limit_grams: int
    minimum_interval_minutes: int
    single_serving_grams: int = 15


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    reason: str


def evaluate_policy(action: Action, facts: Facts) -> PolicyResult:
    """Return whether ``action`` is allowed under ``facts`` and why.

    Non-feeding actions (observe / create_play_task) never touch the quota and
    are always allowed. Feeding is refused on any missing fact, a too-recent
    feed, an over-large single serving, or exceeding the daily budget.
    """

    if action.kind != "dispense_food":
        return PolicyResult(True, NON_FEEDING)

    if facts.last_fed_minutes_ago is None or facts.daily_dispensed_grams is None:
        return PolicyResult(False, MISSING_FACTS)

    if facts.last_fed_minutes_ago < facts.minimum_interval_minutes:
        return PolicyResult(False, RECENT_FEED)

    if action.grams > facts.single_serving_grams:
        return PolicyResult(False, SINGLE_SERVING_EXCEEDED)

    if facts.daily_dispensed_grams + action.grams > facts.daily_limit_grams:
        return PolicyResult(False, DAILY_LIMIT_EXCEEDED)

    return PolicyResult(True, ALLOWED)
