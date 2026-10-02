"""Offline validation of the Day-5 24-case evaluation set (T6, ruling 18).

``scripts/evaluate.py`` runs these cases against an ALREADY-DEPLOYED HTTPS URL; that
run is a CONDITION item (it needs a deployment + credentials + a real model). Here we
validate the case SET offline: exactly 24 uniquely-named cases, full A01-A14
coverage, the required categories present, and -- critically -- NO pre-filled
accuracy / latency / success-rate assertion anywhere in a case (five-day spec L138).

This does NOT prove any case passes; only a real run against the deployed service
does, and its report is written to docs/evidence/evaluation-<stamp>.md.
"""

from __future__ import annotations

import json
from pathlib import Path

SCENARIOS = Path(__file__).resolve().parents[1] / "tests" / "cases" / "scenarios.json"


def _cases() -> list[dict]:
    return json.loads(SCENARIOS.read_text("utf-8"))["cases"]


def test_there_are_exactly_24_uniquely_named_cases() -> None:
    cases = _cases()
    assert len(cases) == 24
    ids = [case["id"] for case in cases]
    assert len(set(ids)) == 24, "case ids must be unique"


def test_every_case_has_the_required_shape() -> None:
    for case in _cases():
        assert case["id"] and case["category"] and case["acceptance"]
        assert isinstance(case["steps"], list) and case["steps"]
        for step in case["steps"]:
            assert "op" in step


def test_the_full_a01_to_a14_matrix_is_covered() -> None:
    covered = {tag for case in _cases() for tag in case["acceptance"]}
    expected = {f"A{n:02d}" for n in range(1, 15)}
    assert expected <= covered, f"missing acceptance coverage: {sorted(expected - covered)}"


def test_injection_insufficient_info_and_failure_categories_are_present() -> None:
    categories = {case["category"] for case in _cases()}
    assert {"injection", "insufficient-info", "failure-receipt"} <= categories


def test_no_case_asserts_a_prefilled_metric_or_verdict() -> None:
    """Ruling 18 / spec L138: the set must not bake in any expected accuracy, latency,
    success rate or pre-declared verdict -- those are MEASURED by a real run, never
    asserted up front. Only the machine-actionable step/case keys are scanned (prose
    in _comment explaining what this is NOT is allowed)."""

    forbidden_step_keys = {
        "accuracy",
        "expected_accuracy",
        "success_rate",
        "pass_rate",
        "precision",
        "recall",
        "expected_latency_ms",
    }
    for case in _cases():
        assert "expected_verdict" not in case, f"{case['id']} pre-declares its verdict"
        for step in case["steps"]:
            overlap = forbidden_step_keys & step.keys()
            assert not overlap, f"{case['id']} pre-fills a metric: {sorted(overlap)}"
