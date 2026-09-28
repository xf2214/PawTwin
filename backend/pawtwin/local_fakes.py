"""Local-only stand-in analyzer (PAWTWIN_MODE=local, model_backend=local_fake).

Clearly labelled, reads real repository facts through the injected read-only
tools, cites only evidence ids that were actually retrieved in THIS analysis,
and never bypasses policy (hard limits are applied by the workflow, not here).
AWS mode must never select this stand-in (see :func:`pawtwin.agent.build_analyzer`).

It performs **zero** model calls: the telemetry says so explicitly, which is why
the per-run call ceiling cannot be validated through this stand-in.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pawtwin.agent import AgentContext, validate_proposal_evidence
from pawtwin.models import (
    Action,
    AnalysisOutcome,
    AnalysisTelemetry,
    AnalyzerBackend,
    EventIn,
    Proposal,
)

LOCAL_FAKE_LABEL = "本地替身"


def _now() -> datetime:
    return datetime.now(UTC)


class LocalFakeAgent:
    label: AnalyzerBackend = "local_fake"

    def analyze_event(self, event: EventIn, context: AgentContext) -> AnalysisOutcome:
        started = _now()
        facts = context.get_pet_facts(context.pet_id)
        policy = context.get_policy_summary(context.pet_id)

        if event.kind == "attention_request":
            action = Action(kind="create_play_task", grams=0)
            explanation = f"[{LOCAL_FAKE_LABEL}] 互动请求：建议创建陪玩任务，不涉及喂食。"
            missing: list[str] = []
        else:
            action, explanation, missing = self._feeding_proposal(facts)

        proposal = Proposal(
            action=action,
            explanation=explanation,
            evidence_ids=[facts["evidence_id"], policy["evidence_id"]],
            missing_fields=missing,
        )
        # The stand-in may only cite evidence it really retrieved.
        validate_proposal_evidence(proposal, context.retrieved_evidence_ids())

        finished = _now()
        return AnalysisOutcome(
            proposal=proposal,
            evidence=context.evidence_ledger(),
            telemetry=AnalysisTelemetry(
                backend="local_fake",
                model_id=None,
                model_calls=0,
                output_tokens=0,
                duration_ms=max(0, int((finished - started).total_seconds() * 1000)),
                started_at=started,
                finished_at=finished,
                request_id=None,
            ),
        )

    @staticmethod
    def _feeding_proposal(facts: dict[str, object]) -> tuple[Action, str, list[str]]:
        """Propose feeding ONLY from facts that are actually known.

        A NULL fact is UNKNOWN, never 0. Coercing it would make the stand-in
        propose 15 g while the policy is judging MISSING_FACTS, and the owner would
        see "not enough information" next to "dispense 15 grams, fed 0 minutes ago"
        -- the same distortion that was removed from the API projection.
        """

        unknown = [
            name
            for name in ("last_fed_minutes_ago", "daily_dispensed_grams")
            if facts[name] is None
        ]
        if unknown:
            labels = {
                "last_fed_minutes_ago": "上次喂食时间",
                "daily_dispensed_grams": "当日已出粮量",
            }
            listed = "、".join(labels[name] for name in unknown)
            return (
                Action(kind="observe", grams=0),
                f"[{LOCAL_FAKE_LABEL}] 缺少必要事实（{listed}），无法给出喂食建议，"
                "仅建议观察。补全事实后重新发送请求即可。",
                unknown,
            )

        dispensed = int(facts["daily_dispensed_grams"] or 0)
        limit = int(facts["daily_limit_grams"] or 0)
        serving = int(facts["single_serving_grams"] or 0)
        remaining = max(0, limit - dispensed)
        grams = min(serving, remaining)
        action = (
            Action(kind="dispense_food", grams=grams)
            if grams >= 1
            else Action(kind="observe", grams=0)
        )
        last_fed = facts["last_fed_minutes_ago"]
        explanation = (
            f"[{LOCAL_FAKE_LABEL}] 依据当前事实（上次喂食距今 {last_fed} 分钟、"
            f"当日已出粮 {dispensed} 克、日配额 {limit} 克）生成建议；"
            "最终是否执行由硬性策略与主人审批决定。"
        )
        return action, explanation, []
