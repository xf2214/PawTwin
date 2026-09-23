"""Local-only stand-in analyzer (PAWTWIN_MODE=local).

Clearly labelled, reads real repository facts through the injected read-only
tools, cites only evidence ids that were actually returned, and never bypasses
policy (hard limits are applied by the workflow, not here). AWS mode must never
select this stand-in (see :func:`pawtwin.agent.build_analyzer`).
"""

from __future__ import annotations

from pawtwin.agent import AgentContext, validate_proposal_evidence
from pawtwin.models import Action, EventIn, Proposal

LOCAL_FAKE_LABEL = "本地替身"


class LocalFakeAgent:
    label = "local_fake"

    def analyze_event(self, event: EventIn, context: AgentContext) -> Proposal:
        facts = context.get_pet_facts(context.pet_id)
        policy = context.get_policy_summary(context.pet_id)
        available = {facts["evidence_id"], policy["evidence_id"]}

        if event.kind == "attention_request":
            action = Action(kind="create_play_task", grams=0)
            explanation = f"[{LOCAL_FAKE_LABEL}] 互动请求：建议创建陪玩任务，不涉及喂食。"
        else:
            dispensed = facts["daily_dispensed_grams"] or 0
            remaining = max(0, facts["daily_limit_grams"] - dispensed)
            grams = min(facts["single_serving_grams"], remaining)
            action = (
                Action(kind="dispense_food", grams=grams)
                if grams >= 1
                else Action(kind="observe", grams=0)
            )
            last_fed = facts["last_fed_minutes_ago"]
            limit = facts["daily_limit_grams"]
            explanation = (
                f"[{LOCAL_FAKE_LABEL}] 依据当前事实（上次喂食距今 {last_fed} 分钟、"
                f"当日已出粮 {dispensed} 克、日配额 {limit} 克）生成建议；"
                "最终是否执行由硬性策略与主人审批决定。"
            )

        proposal = Proposal(
            action=action,
            explanation=explanation,
            evidence_ids=sorted(available),
        )
        # The stand-in may only cite evidence it really retrieved.
        validate_proposal_evidence(proposal, available_ids=available)
        return proposal
