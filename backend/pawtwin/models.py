import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunState(StrEnum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    NEEDS_INFO = "needs_info"
    BLOCKED = "blocked"
    AWAITING_APPROVAL = "awaiting_approval"
    DECLINED = "declined"
    EXPIRED = "expired"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class EventIn(ContractModel):
    event_id: UUID
    pet_id: Literal["mochi"] = "mochi"
    kind: Literal["food_request", "attention_request"]
    room: Literal["kitchen", "living_room", "unknown"]
    note: str = Field(default="", max_length=500)
    source: Literal["simulator"] = "simulator"


class Action(ContractModel):
    kind: Literal["dispense_food", "create_play_task", "observe"]
    grams: StrictInt = Field(default=0, ge=0, le=15)

    @model_validator(mode="after")
    def validate_amount_for_action(self) -> "Action":
        if self.kind == "dispense_food" and not 1 <= self.grams <= 15:
            raise ValueError("dispense_food requires grams between 1 and 15")
        if self.kind != "dispense_food" and self.grams != 0:
            raise ValueError("non-food actions require grams to be exactly 0")
        return self


class Proposal(ContractModel):
    action: Action
    explanation: str = Field(max_length=1200)
    evidence_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class ApprovalIn(ContractModel):
    decision: Literal["approve", "decline"]
    proposal_version: StrictInt = Field(gt=0)
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


FeedbackText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class FeedbackIn(ContractModel):
    text: FeedbackText
    scope: Literal["observation", "today_only"]


class Receipt(ContractModel):
    command_id: UUID
    status: Literal["succeeded", "failed", "unknown"]
    simulated: Literal[True] = True


# --- Shared contract helpers -------------------------------------------------
# Frozen surface used by both the backend workflow and the AI agent so the
# approval digest and the idempotency command id can never drift apart.

COMMAND_NAMESPACE = UUID("9e6a3a9a-2b7c-5d41-8f6a-1c2e5b7a9d03")


def canonical_json(model: BaseModel) -> str:
    """Deterministic JSON serialization; stable across processes and versions."""
    return json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def compute_action_digest(action: Action) -> str:
    """sha256 hex digest of the canonical action; matches ApprovalIn.action_digest."""
    return hashlib.sha256(canonical_json(action).encode("utf-8")).hexdigest()


def make_command_id(run_id: UUID, proposal_version: int) -> UUID:
    """Deterministic command id from run+version; retries never mint a new id."""
    return uuid5(COMMAND_NAMESPACE, f"{run_id}:{proposal_version}")


UNKNOWN_EVIDENCE = "UNKNOWN_EVIDENCE"
MODEL_INVALID_OUTPUT = "MODEL_INVALID_OUTPUT"
MODEL_CALL_LIMIT = "MODEL_CALL_LIMIT"
TOKEN_LIMIT = "TOKEN_LIMIT"
ANALYSIS_TIMEOUT = "ANALYSIS_TIMEOUT"
ATTEMPTS_EXHAUSTED = "ATTEMPTS_EXHAUSTED"
BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
ANALYZER_ERROR = "ANALYZER_ERROR"

# Bounded reason codes surfaced through RunView.policy_reason / failure_reason.
# They live in the contract layer so Backend and AI share one vocabulary without
# a Backend -> AI import, and so the UI never has to parse free-form model text.
FAILURE_CODES = frozenset(
    {
        UNKNOWN_EVIDENCE,
        MODEL_INVALID_OUTPUT,
        MODEL_CALL_LIMIT,
        TOKEN_LIMIT,
        ANALYSIS_TIMEOUT,
        ATTEMPTS_EXHAUSTED,
        BACKEND_UNAVAILABLE,
        ANALYZER_ERROR,
    }
)


def failure_code_from(exc: BaseException) -> str:
    """Map any analyzer exception onto a bounded reason code (fail closed)."""

    text = str(exc)
    for code in FAILURE_CODES:
        if text.startswith(code):
            return code
    return ANALYZER_ERROR


def validate_proposal_evidence(proposal: "Proposal", available_ids: set[str]) -> None:
    """Reject any proposal citing an evidence id that was not really retrieved.

    Lives in the contract layer so BOTH the workflow (Backend) and the analyzer
    adapters (AI) enforce it without a Backend -> AI import. An empty
    ``evidence_ids`` passes: only *unknown* ids are rejected.
    """

    unknown = [eid for eid in proposal.evidence_ids if eid not in available_ids]
    if unknown:
        raise ValueError(f"{UNKNOWN_EVIDENCE}: {', '.join(sorted(unknown))}")


# --- Public response DTOs ----------------------------------------------------
# These appear in OpenAPI only. They are intentionally NOT part of DOMAIN_MODELS
# (domain.schema.json keeps validating the six input models only).

AnalyzerBackend = Literal["inline", "local_fake", "bedrock"]
DeviceModeLabel = Literal["succeeded", "failed", "unknown"]
ToolName = Literal[
    "get_pet_facts",
    "get_recent_events",
    "search_owner_memory",
    "get_policy_summary",
]
ClearableFact = Literal["last_fed_minutes_ago", "daily_dispensed_grams"]
# Day-3 (T5): the long-term-memory surface. ``MemoryStatus`` is the owner-facing
# lifecycle of ONE feedback item: ``saved`` means the RAW text is stored in the
# business database, NOT that it was extracted into AgentCore memory. Without a
# real AgentCore retrieval a local run can only ever be ``saved`` -- claiming
# ``available`` would present stored feedback as extracted memory (AGENTS.md L18).
MemoryStatus = Literal["saved", "processing", "available", "failed"]
MemoryBackend = Literal["not_implemented", "agentcore"]
FeedbackScope = Literal["observation", "today_only"]


class ErrorResponse(ContractModel):
    """Shared error body, declared in OpenAPI ``responses`` (401/403/404/409)."""

    detail: str


class LoginRequest(ContractModel):
    passphrase: str = Field(min_length=1, max_length=200)


class LoginResponse(ContractModel):
    csrf_token: str


class EventAccepted(ContractModel):
    run_id: UUID
    state: RunState


class FactsView(ContractModel):
    # Day-2 ruling 12: nullable on purpose. An UNKNOWN fact must never be
    # rendered as ``0`` while the policy judges MISSING_FACTS -- that would tell
    # the owner "fed 0 minutes ago" and "not enough information" at once.
    last_fed_minutes_ago: int | None
    daily_dispensed_grams: int | None
    daily_limit_grams: int
    single_serving_grams: int
    minimum_interval_minutes: int
    facts_version: int


class EvidenceItem(ContractModel):
    """One read-only tool call that really happened.

    Tool name, source, timestamp and a bounded summary only: never hidden
    reasoning, never the raw event note, never the full model request.
    """

    evidence_id: str
    tool: ToolName
    source: Literal["repository", "policy", "memory"]
    retrieved_at: datetime
    summary: str = Field(default="", max_length=300)


class AnalysisTelemetry(ContractModel):
    """Auditable model-call record (Day-2 acceptance: call records are checkable).

    ``request_id`` stays ``None`` until a real Bedrock call happens, so a local
    run can never be mistaken for a cloud one. Counts/durations/identifiers only.
    """

    backend: AnalyzerBackend
    model_id: str | None = None
    model_calls: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    started_at: datetime
    finished_at: datetime
    request_id: str | None = None
    limit_exceeded: str | None = None


class AnalysisOutcome(ContractModel):
    """Frozen analyzer seam result (Day-2 rulings 1 and 2).

    Shared by Backend (workflow) and AI (agent) so a proposal, its evidence
    ledger and its call telemetry can never drift apart. INTERNAL ONLY: it is
    not a route response model and not part of DOMAIN_MODELS.
    """

    proposal: Proposal
    evidence: list[EvidenceItem] = Field(default_factory=list)
    telemetry: AnalysisTelemetry


class RunView(ContractModel):
    run_id: UUID
    state: RunState
    facts_version: int
    proposal: Proposal | None = None
    receipt: Receipt | None = None
    expires_at: datetime | None = None
    created_at: datetime
    # Coordinator ruling (Day-1, restated Day-2): the anti-tamper approval binding
    # must be echoed by the client to satisfy ApprovalIn, so these two NON-secret
    # fields are exposed. owner_id / attempt_count / lease_owner / lease_until
    # stay internal to the repository record and never appear in any response --
    # including inside ``evidence`` and ``telemetry``.
    proposal_version: int = 0
    action_digest: str | None = None
    # Day-2: the owner must be able to see WHY a run is blocked or failed
    # (A09/A10). Bounded reason codes only, never free-form model text.
    policy_reason: str | None = None
    failure_reason: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    telemetry: AnalysisTelemetry | None = None


class DemoFactsIn(ContractModel):
    """Demo-only fact injection (Day-2 ruling 13).

    ``extra='forbid'`` IS the hard-quota guard: the limits themselves
    (``daily_limit_grams`` / ``single_serving_grams`` / ``minimum_interval_minutes``)
    can never be edited through this endpoint, so a demo request cannot raise the
    daily budget. ``clear`` distinguishes "leave unchanged" from "set to unknown";
    naming a field in both places is a conflict and is rejected.
    """

    last_fed_minutes_ago: StrictInt | None = Field(default=None, ge=0, le=1440)
    daily_dispensed_grams: StrictInt | None = Field(default=None, ge=0, le=10_000)
    clear: list[ClearableFact] = Field(default_factory=list)
    reset: bool = False

    @model_validator(mode="after")
    def validate_clear_does_not_conflict(self) -> "DemoFactsIn":
        for name in self.clear:
            if getattr(self, name) is not None:
                raise ValueError(f"{name} cannot be set and cleared at the same time")
        return self


class DemoDeviceModeIn(ContractModel):
    """Injects the SIMULATED actuator outcome for NEW commands only."""

    mode: DeviceModeLabel


class DemoAck(ContractModel):
    """Echoes what changed so the UI never has to guess the new facts_version."""

    facts: FactsView
    device_mode: DeviceModeLabel | None = None


class FeedbackView(ContractModel):
    """Owner feedback plus its HONEST long-term-memory lifecycle.

    ``memory_status='saved'`` means the raw text is stored in the business
    database; it never implies extraction. ``memory_backend`` is carried alongside
    so a judge can never read ``saved`` as "AgentCore memory available"
    (AGENTS.md L18). ``available`` only ever appears with real retrieval evidence.
    """

    feedback_id: UUID
    scope: FeedbackScope
    text: str
    memory_status: MemoryStatus
    memory_backend: MemoryBackend
    created_at: datetime
    conversation_id: str | None = None


class NewSessionView(ContractModel):
    """Result of ``POST /api/demo/new-session``: a fresh conversation id.

    Pet memory, facts and the login session are preserved; only the conversation
    (the AgentCore session id) rotates, which is what makes cross-session
    retrieval demonstrable. The conversation id is never a pet identity.
    """

    conversation_id: str


class StateView(ContractModel):
    pet_id: Literal["mochi"] = "mochi"
    mode: Literal["local", "aws"]
    aws_connected: bool
    # Day-2 ruling 15: component-level labels. ``aws_connected`` stays False until
    # storage AND model AND memory are all really connected, so
    # analyzer='bedrock' with aws_connected=False is honest, not contradictory.
    analyzer: AnalyzerBackend
    storage: Literal["sqlite", "dynamodb"] = "sqlite"
    memory: MemoryBackend = "not_implemented"
    device_mode: DeviceModeLabel = "succeeded"
    # Day-3 (ruling 5): the current AgentCore conversation/session id. Rotated by
    # POST /api/demo/new-session; pet memory and facts SURVIVE the rotation
    # (retrieval is namespaced by owner/pet, never by session). Process-local and
    # reset on restart while sessions stay in memory (ruling 6).
    conversation_id: str | None = None
    facts: FactsView
    runs: list[RunView]
    # Day-3: recent owner feedback with its HONEST memory lifecycle, so the memory
    # area survives a reload and never needs a fabricated "retrieved memory".
    feedback: list[FeedbackView] = Field(default_factory=list)

