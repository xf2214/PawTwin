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


# --- Public response DTOs ----------------------------------------------------
# These appear in OpenAPI only. They are intentionally NOT part of DOMAIN_MODELS
# (domain.schema.json keeps validating the six input models only).

class LoginRequest(ContractModel):
    passphrase: str = Field(min_length=1, max_length=200)


class LoginResponse(ContractModel):
    csrf_token: str


class EventAccepted(ContractModel):
    run_id: UUID
    state: RunState


class FactsView(ContractModel):
    last_fed_minutes_ago: int
    daily_dispensed_grams: int
    daily_limit_grams: int
    single_serving_grams: int
    minimum_interval_minutes: int
    facts_version: int


class RunView(ContractModel):
    run_id: UUID
    state: RunState
    facts_version: int
    proposal: Proposal | None = None
    receipt: Receipt | None = None
    expires_at: datetime | None = None
    created_at: datetime
    # Coordinator ruling (Day-1): the anti-tamper approval binding must be echoed
    # by the client to satisfy ApprovalIn, so these two NON-secret fields are
    # exposed here. owner_id / attempt_count / lease_owner / lease_until stay
    # internal to the repository record and never appear in any response.
    proposal_version: int = 0
    action_digest: str | None = None


class StateView(ContractModel):
    pet_id: Literal["mochi"] = "mochi"
    mode: Literal["local", "aws"]
    aws_connected: bool
    facts: FactsView
    runs: list[RunView]
