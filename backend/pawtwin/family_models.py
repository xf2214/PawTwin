"""Extension inputs; actor and household scope come exclusively from the session."""

from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from pawtwin.home_models import CareKind, DiaryInput, HomeInput, NoteInput

Role = Literal["admin", "carer", "guest"]


class NoteRevision(NoteInput):
    version: int = Field(ge=1)


class DiaryRevision(DiaryInput):
    version: int = Field(ge=1)


class AccountLogin(HomeInput):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=128)


class AccountRegister(AccountLogin):
    display_name: str = Field(min_length=1, max_length=40)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if len(value) < 12:
            raise ValueError("Use at least 12 characters")
        return value


class HouseholdInput(HomeInput):
    name: str = Field(min_length=1, max_length=80)
    timezone: str = "Asia/Shanghai"

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class ProfileInput(HomeInput):
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    family_label: str | None = Field(default=None, max_length=40)
    avatar_ref: str | None = Field(default=None, max_length=200)


class PetLifecycleInput(HomeInput):
    archived: bool


class InvitationInput(HomeInput):
    role: Role = "carer"
    expires_in_hours: int = Field(default=48, ge=1, le=168)
    max_uses: int = Field(default=1, ge=1, le=20)


class InvitationAccept(HomeInput):
    token: str = Field(min_length=20, max_length=200)


class MemberPermission(HomeInput):
    role: Role
    feeding_pet_ids: list[Literal["mochi"]] = Field(default_factory=list)


class MeasurementInput(HomeInput):
    kind: Literal["weight", "diet"]
    value: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    unit: Literal["kg", "g"]
    measured_at: datetime
    source: Literal["owner_measured", "vet", "verified_device", "demo_sample"] = "owner_measured"
    diet_type: Literal["actual_intake", "food_offered", "dispensed", "remaining"] | None = None
    note: str = Field(default="", max_length=1000)
    version: int | None = Field(default=None, ge=1)

    @field_validator("measured_at")
    @classmethod
    def measurement_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Timezone required")
        return value

    @model_validator(mode="after")
    def semantics(self):
        if round(self.value * (1000 if self.unit == "kg" else 1), 6) <= 0:
            raise ValueError("Normalized measurement must remain positive")
        if self.kind == "diet" and self.diet_type is None:
            raise ValueError("Diet facts require their meaning")
        if self.kind == "weight" and self.diet_type is not None:
            raise ValueError("Weight has no diet type")
        if self.source == "verified_device":
            raise ValueError("No verified measurement device is connected")
        return self


class ReportInput(HomeInput):
    period: Literal["daily", "weekly"]
    date: date


class MemoryInput(HomeInput):
    text: str = Field(min_length=1, max_length=1000)
    topic: str = Field(default="general", max_length=80)
    status: Literal["candidate", "confirmed"] = "candidate"
    valid_until: datetime | None = None

    @field_validator("valid_until")
    @classmethod
    def aware_expiry(cls, value: datetime | None) -> datetime | None:
        if value and value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class MemoryUpdate(HomeInput):
    version: int = Field(ge=1)
    status: Literal["candidate", "confirmed", "rejected"]
    text: str | None = Field(default=None, min_length=1, max_length=1000)
    valid_until: datetime | None = None

    @field_validator("text")
    @classmethod
    def non_null_text(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Memory text cannot be null; omit it to keep the current text")
        return value

    @field_validator("valid_until")
    @classmethod
    def aware_expiry(cls, value: datetime | None) -> datetime | None:
        return MemoryInput.aware_expiry(value)


class ChatInput(HomeInput):
    text: str = Field(min_length=1, max_length=2000)
    entry: Literal["app", "alexa_simulator"] = "app"


class ProposalInput(HomeInput):
    kind: CareKind
    title: str = Field(min_length=1, max_length=80)
    due_at: datetime
    context_version: int | None = Field(default=None, ge=1)
    context_valid_until: datetime | None = None

    @field_validator("context_valid_until")
    @classmethod
    def aware_context_expiry(cls, value: datetime | None) -> datetime | None:
        return MemoryInput.aware_expiry(value)

    @field_validator("due_at")
    @classmethod
    def aware_due(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class ConfirmProposal(HomeInput):
    version: int = Field(ge=1)
    context_version: int = Field(ge=1)
