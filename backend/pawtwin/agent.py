"""Product Agent adapters: read-only tools, evidence validation, analyzer seam.

Day-1 delivers the interfaces plus a labelled local stand-in. The real
Bedrock/Strands analyzer is Day-2, and AWS mode never silently falls back to the
stand-in. Authorization scope (``owner_id``) is injected by the server; a model
can never pass an arbitrary owner id. Tools return data bearing real
``evidence_id`` values so a proposal can only cite what was actually retrieved.
"""

from __future__ import annotations

from typing import Any, Protocol

from pawtwin.config import Settings
from pawtwin.models import EventIn, Proposal
from pawtwin.repository import Repository

UNKNOWN_EVIDENCE = "UNKNOWN_EVIDENCE"
DEFAULT_PET_ID = "mochi"


class AgentContext:
    """Read-only tools bound to a single server-authorized owner/pet scope."""

    def __init__(self, repo: Repository, owner_id: str, pet_id: str = DEFAULT_PET_ID) -> None:
        self._repo = repo
        self.owner_id = owner_id
        self.pet_id = pet_id

    def get_pet_facts(self, pet_id: str) -> dict[str, Any]:
        facts = self._repo.get_facts(self.owner_id)
        return {
            "evidence_id": f"facts:v{facts.facts_version}",
            "pet_id": pet_id,
            "last_fed_minutes_ago": facts.last_fed_minutes_ago,
            "daily_dispensed_grams": facts.daily_dispensed_grams,
            "daily_limit_grams": facts.daily_limit_grams,
            "single_serving_grams": facts.single_serving_grams,
            "minimum_interval_minutes": facts.minimum_interval_minutes,
            "facts_version": facts.facts_version,
            "source": "repository",
        }

    def get_recent_events(self, pet_id: str, limit: int = 5) -> list[dict[str, Any]]:
        runs = self._repo.list_runs(self.owner_id)[: max(0, limit)]
        return [
            {
                "evidence_id": f"event:{run.event_id}",
                "pet_id": pet_id,
                "state": run.state.value,
                "source": "repository",
            }
            for run in runs
        ]

    def search_owner_memory(self, pet_id: str, query: str) -> list[dict[str, Any]]:
        # Long-term memory retrieval is Day-3 (AgentCore). Return an explicitly
        # empty result rather than fabricating memories.
        return []

    def get_policy_summary(self, pet_id: str) -> dict[str, Any]:
        return {
            "evidence_id": "policy:summary",
            "pet_id": pet_id,
            "rules": [
                "all_feeding_requires_owner_approval",
                "hard_quota_cannot_be_overridden_by_approval",
                "missing_facts_fail_closed",
            ],
            "source": "policy",
        }

    def available_evidence_ids(self) -> set[str]:
        ids = {
            self.get_pet_facts(self.pet_id)["evidence_id"],
            self.get_policy_summary(self.pet_id)["evidence_id"],
        }
        ids.update(item["evidence_id"] for item in self.get_recent_events(self.pet_id))
        return ids


class EventAnalyzer(Protocol):
    """Analyzer seam. ``label`` keeps the local/aws boundary visible."""

    label: str

    def analyze_event(self, event: EventIn, context: AgentContext) -> Proposal: ...


def validate_proposal_evidence(proposal: Proposal, available_ids: set[str]) -> None:
    """Reject any proposal citing an evidence id that was not really retrieved."""

    unknown = [eid for eid in proposal.evidence_ids if eid not in available_ids]
    if unknown:
        raise ValueError(f"{UNKNOWN_EVIDENCE}: {', '.join(sorted(unknown))}")


class BedrockAgent:
    """Real Bedrock/Strands analyzer (Day-2). Never a silent local stand-in."""

    label = "bedrock"

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id

    def analyze_event(self, event: EventIn, context: AgentContext) -> Proposal:
        raise NotImplementedError(
            "Bedrock analyzer lands on Day-2; AWS mode must never use a local fake"
        )


def build_analyzer(settings: Settings, repo: Repository) -> EventAnalyzer:
    """Fail-closed analyzer factory: aws -> real Bedrock, local -> labelled fake."""

    if settings.mode == "aws":
        return BedrockAgent(settings.bedrock_model_id or "")
    from pawtwin.local_fakes import LocalFakeAgent  # deferred: local_fakes imports agent

    return LocalFakeAgent()
