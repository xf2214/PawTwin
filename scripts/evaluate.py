#!/usr/bin/env python
"""Day-5 24-case evaluation driver (T6, ruling 18).

Runs tests/cases/scenarios.json against an ALREADY-DEPLOYED HTTPS base URL and
reports, per case: the input, the expected workflow conclusion, the actual result,
the real Bedrock ``request_id``, latency and a verdict -- plus a total pass rate.

HONESTY GUARANTEES:
* The demo passphrase is read ONLY from the environment (PAWTWIN_DEMO_PASSPHRASE);
  it is never a CLI arg, never written to the report, the repo or a log.
* NOTHING is pre-filled: no accuracy, latency or success rate is asserted before the
  run. A case that cannot be exercised is recorded ERROR/TIMEOUT, never re-labelled
  as a local pass.
* The report quantifies WORKFLOW / advice consistency ONLY. It is NOT a pet-intent
  accuracy benchmark and must not be read as one (five-day spec L138).
* Memory cases are bound by AgentCore's asynchronous extraction (fact G-I): they poll
  up to ``poll_budget_seconds`` (default 180) and record TIMEOUT honestly.

Usage (against the deployed service):
    $env:PAWTWIN_DEMO_PASSPHRASE = '<injected, never stored>'
    uv run --frozen python scripts/evaluate.py --base-url https://<svc>.ecs.<region>.on.aws
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = REPO_ROOT / "tests" / "cases" / "scenarios.json"
DEFAULT_POLL_BUDGET = 180
VERDICTS = ("PASS", "FAIL", "TIMEOUT", "ERROR")


class Client:
    """Minimal JSON HTTP client with a cookie jar (the session cookie is HttpOnly)."""

    def __init__(self, base_url: str, passphrase: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._passphrase = passphrase
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar)
        )
        self.csrf: str | None = None

    def request(
        self, method: str, path: str, body: dict | None = None, headers: dict | None = None
    ) -> tuple[int, dict | None, dict]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        all_headers = {"Content-Type": "application/json", **(headers or {})}
        if self.csrf and method != "GET":
            all_headers["X-CSRF-Token"] = self.csrf
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        for key, value in all_headers.items():
            req.add_header(key, value)
        try:
            with self._opener.open(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
                status = response.status
                resp_headers = dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            status = exc.code
            resp_headers = dict(exc.headers.items()) if exc.headers else {}
        parsed: dict | None = None
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
        return status, parsed, resp_headers

    def login(self) -> None:
        status, body, _ = self.request("POST", "/api/login", {"passphrase": self._passphrase})
        if status != 200 or not body:
            raise RuntimeError(f"login failed with status {status}")
        self.csrf = body.get("csrf_token")

    def logout(self) -> None:
        self.request("POST", "/api/logout")
        self.csrf = None


class CaseRunner:
    def __init__(self, client: Client) -> None:
        self.client = client
        self.run_id: str | None = None
        self.event_id: str | None = None
        self.feedback_id: str | None = None
        self.captured: dict[str, Any] = {}
        self.request_id: str | None = None

    # -- helpers -------------------------------------------------------------

    def _state(self) -> dict:
        _, body, _ = self.client.request("GET", "/api/state")
        return body or {}

    def _run(self) -> dict | None:
        if not self.run_id:
            return None
        _, body, _ = self.client.request("GET", f"/api/runs/{self.run_id}")
        return body

    def _poll_run_state(self, target: str, budget: float) -> str | None:
        deadline = time.time() + budget
        state = None
        while time.time() < deadline:
            run = self._run()
            if run:
                state = run.get("state")
                self.request_id = (run.get("telemetry") or {}).get("request_id") or self.request_id
                if state == target:
                    return state
            time.sleep(2)
        return state

    # -- ops -----------------------------------------------------------------

    def run_step(self, step: dict, budget: float) -> tuple[bool, str, bool]:
        op = step["op"]
        handler = getattr(self, f"_op_{op}", None)
        if handler is None:
            # An advisory/unsupported expectation is RECORDED as a note and is NOT
            # counted as a machine-checked assertion -- so it can never, on its own,
            # make a case pass (a case with only advisory steps is downgraded below).
            return True, f"note: op '{op}' not machine-checked by this driver", False
        ok, detail = handler(step, budget)
        return ok, detail, True

    def _op_login(self, step: dict, budget: float) -> tuple[bool, str]:
        self.client.login()
        return True, "logged in"

    def _op_logout(self, step: dict, budget: float) -> tuple[bool, str]:
        self.client.logout()
        return True, "logged out"

    def _op_set_facts(self, step: dict, budget: float) -> tuple[bool, str]:
        body: dict[str, Any] = {}
        for key in ("last_fed_minutes_ago", "daily_dispensed_grams", "clear", "reset"):
            if key in step:
                body[key] = step[key]
        status, _, _ = self.client.request("POST", "/api/demo/facts", body)
        return status == 200, f"set_facts -> {status}"

    def _op_set_device_mode(self, step: dict, budget: float) -> tuple[bool, str]:
        status, _, _ = self.client.request(
            "POST", "/api/demo/device-mode", {"mode": step["mode"]}
        )
        return status == 200, f"device_mode={step['mode']} -> {status}"

    def _op_post_event(self, step: dict, budget: float) -> tuple[bool, str]:
        import uuid

        self.event_id = str(uuid.uuid4())
        event = {
            "event_id": self.event_id,
            "kind": step["kind"],
            "room": step["room"],
            "note": step.get("note", ""),
        }
        status, body, _ = self.client.request("POST", "/api/events", event)
        if status == 202 and body:
            self.run_id = body["run_id"]
            return True, f"event accepted run={self.run_id}"
        return False, f"post_event -> {status}"

    def _op_post_event_same_id(self, step: dict, budget: float) -> tuple[bool, str]:
        event = {"event_id": self.event_id, "kind": "food_request", "room": "kitchen"}
        status, body, _ = self.client.request("POST", "/api/events", event)
        if status == 202 and body:
            same = body["run_id"] == self.run_id
            return same, f"redelivery reused run={same}"
        return False, f"post_event_same_id -> {status}"

    def _op_expect_state(self, step: dict, budget: float) -> tuple[bool, str]:
        state = self._poll_run_state(step["state"], budget)
        return state == step["state"], f"state={state} expected={step['state']}"

    def _op_expect_state_in(self, step: dict, budget: float) -> tuple[bool, str]:
        deadline = time.time() + budget
        state = None
        while time.time() < deadline:
            run = self._run()
            state = run.get("state") if run else None
            if state in step["states"]:
                return True, f"state={state} in {step['states']}"
            time.sleep(2)
        return False, f"state={state} not in {step['states']}"

    def _op_expect_policy(self, step: dict, budget: float) -> tuple[bool, str]:
        run = self._run() or {}
        reason = run.get("policy_reason")
        if "reason" in step:
            return reason == step["reason"], f"policy_reason={reason} expected={step['reason']}"
        return reason in step["reason_in"], f"policy_reason={reason} in {step['reason_in']}"

    def _op_expect_request_id(self, step: dict, budget: float) -> tuple[bool, str]:
        run = self._run() or {}
        rid = (run.get("telemetry") or {}).get("request_id")
        self.request_id = rid or self.request_id
        return bool(rid), f"request_id={'present' if rid else 'NULL'}"

    def _op_approve(self, step: dict, budget: float) -> tuple[bool, str]:
        run = self._run() or {}
        body = {
            "decision": step["decision"],
            "proposal_version": run.get("proposal_version", 1),
            "action_digest": run.get("action_digest") or "0" * 64,
        }
        status, _, _ = self.client.request(
            "POST", f"/api/runs/{self.run_id}/approval", body
        )
        if "expect_conflict" in step:
            return status == 409, f"approve -> {status} (expected 409 conflict)"
        return status in (200, 409), f"approve -> {status}"

    def _op_expect_receipts(self, step: dict, budget: float) -> tuple[bool, str]:
        run = self._run() or {}
        count = 1 if run.get("receipt") else 0
        return count == step["count"], f"receipts={count} expected={step['count']}"

    def _op_expect_receipt_status(self, step: dict, budget: float) -> tuple[bool, str]:
        run = self._run() or {}
        status = (run.get("receipt") or {}).get("status")
        return status == step["status"], f"receipt.status={status} expected={step['status']}"

    def _op_expect_accounting(self, step: dict, budget: float) -> tuple[bool, str]:
        facts = self._state().get("facts", {})
        actual = facts.get("daily_dispensed_grams")
        expected = step["daily_dispensed_grams"]
        return actual == expected, f"daily_dispensed_grams={actual} expected={expected}"

    def _op_post_feedback(self, step: dict, budget: float) -> tuple[bool, str]:
        status, body, _ = self.client.request(
            "POST", "/api/feedback", {"text": step["text"], "scope": step["scope"]}
        )
        if status == 200 and body:
            self.feedback_id = body["feedback_id"]
            return True, f"feedback saved {self.feedback_id}"
        return False, f"post_feedback -> {status}"

    def _op_expect_memory_status(self, step: dict, budget: float) -> tuple[bool, str]:
        target = step["status"]
        if not step.get("poll"):
            _, body, _ = self.client.request("GET", f"/api/feedback/{self.feedback_id}")
            actual = (body or {}).get("memory_status")
            return actual == target, f"memory_status={actual} expected={target}"
        deadline = time.time() + budget
        actual = None
        while time.time() < deadline:
            _, body, _ = self.client.request("GET", f"/api/feedback/{self.feedback_id}")
            actual = (body or {}).get("memory_status")
            if actual == target:
                return True, f"memory_status reached {target}"
            time.sleep(10)
        # Extraction is asynchronous (fact G-I): a non-match after the budget is a
        # real TIMEOUT, never a pass.
        raise TimeoutError(f"memory_status={actual} did not reach {target} within {budget}s")

    def _op_new_session(self, step: dict, budget: float) -> tuple[bool, str]:
        status, _, _ = self.client.request("POST", "/api/demo/new-session")
        return status == 200, f"new_session -> {status}"

    def _op_expect_http(self, step: dict, budget: float) -> tuple[bool, str]:
        status, _, headers = self.client.request(
            step.get("method", "POST"), step["path"], step.get("body")
        )
        ok = status == step["status"]
        if step.get("has_retry_after"):
            ok = ok and "Retry-After" in headers
        return ok, f"{step['path']} -> {status} expected={step['status']}"

    def _op_expect_unauthenticated(self, step: dict, budget: float) -> tuple[bool, str]:
        status, _, _ = self.client.request(step.get("method", "GET"), step["path"])
        return status == step["status"], f"{step['path']} -> {status} expected={step['status']}"

    def _op_failed_logins(self, step: dict, budget: float) -> tuple[bool, str]:
        for _ in range(step["count"]):
            self.client.request("POST", "/api/login", {"passphrase": "definitely-wrong"})
        return True, f"{step['count']} failed logins attempted"


def run_case(client: Client, case: dict, default_budget: float) -> dict:
    runner = CaseRunner(client)
    budget = float(case.get("poll_budget_seconds", default_budget))
    details: list[str] = []
    verdict = "PASS"
    checked = 0
    started = time.time()
    try:
        client.login()
        for step in case["steps"]:
            ok, detail, was_checked = runner.run_step(step, budget)
            details.append(detail)
            checked += int(was_checked)
            if not ok:
                verdict = "FAIL"
                break
    except TimeoutError as exc:
        verdict, details = "TIMEOUT", [*details, str(exc)]
    except Exception as exc:  # noqa: BLE001 - record the real failure, never a fake pass
        verdict, details = "ERROR", [*details, f"{exc.__class__.__name__}: {exc}"]
    if case.get("expect_request_id") and verdict == "PASS" and not runner.request_id:
        # A case that requires a real model call must show a real request_id.
        verdict, details = "FAIL", [*details, "expected a real request_id, got NULL"]
    if verdict == "PASS" and checked == 0:
        # Every step was advisory: nothing was actually verified, so this is NOT a pass.
        verdict, details = "ERROR", [*details, "no step was machine-checked (all advisory)"]
    return {
        "id": case["id"],
        "acceptance": case.get("acceptance", []),
        "verdict": verdict,
        "request_id": runner.request_id,
        "latency_ms": int((time.time() - started) * 1000),
        "details": details,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="deployed HTTPS base URL")
    parser.add_argument("--poll-budget", type=float, default=DEFAULT_POLL_BUDGET)
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    passphrase = os.environ.get("PAWTWIN_DEMO_PASSPHRASE")
    if not passphrase:
        print(
            "NOT EXECUTED: PAWTWIN_DEMO_PASSPHRASE is not set. The passphrase is read "
            "from the environment ONLY -- never a CLI arg, file, log or the repo.",
            file=sys.stderr,
        )
        return 2

    plan = json.loads(SCENARIOS.read_text("utf-8"))
    client = Client(args.base_url, passphrase)
    results = [run_case(client, case, args.poll_budget) for case in plan["cases"]]

    total = len(results)
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        f"# PawTwin evaluation {stamp}",
        "",
        f"Base URL: `{args.base_url}`. Cases: {total}. Passed: {passed}. "
        f"Pass rate: {passed / total:.1%} (measured, not pre-filled).",
        "",
        "This quantifies WORKFLOW / advice consistency ONLY. It is NOT a pet-intent",
        "accuracy benchmark (five-day spec L138). TIMEOUT/ERROR are recorded honestly.",
        "",
        "| case | acceptance | verdict | request_id | latency_ms |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result['id']} | {','.join(result['acceptance'])} | {result['verdict']} "
            f"| {result['request_id'] or '-'} | {result['latency_ms']} |"
        )
    lines.append("")
    for result in results:
        lines.append(f"## {result['id']} -- {result['verdict']}")
        lines.extend(f"- {d}" for d in result["details"])
        lines.append("")
    report = "\n".join(lines)
    print(report)

    out = Path(args.out) if args.out else REPO_ROOT / "docs" / "evidence" / f"evaluation-{stamp}.md"
    out.write_text(report, encoding="utf-8")
    print(f"\nReport written to {out}", file=sys.stderr)
    # A non-green run is a real result, not a script error: exit 0 so CI/evidence
    # keeps the report; the verdicts themselves carry the truth.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
