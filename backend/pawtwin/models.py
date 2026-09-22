from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

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
