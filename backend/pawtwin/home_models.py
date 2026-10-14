"""Owner-confirmed pet-home data, separate from actuator authority."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CareKind = Literal["feeding", "water", "play", "brush", "bath", "nails", "clean", "walk"]


class HomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PetInput(HomeInput):
    name: str = Field(min_length=1, max_length=40)
    species: Literal["cat", "dog"] = "cat"
    breed: str = Field(default="", max_length=80)
    gender: Literal["unknown", "female", "male"] = "unknown"
    birthday: date | None = None
    birthday_estimated: bool = False
    neutered: bool | None = None
    expected_adult_weight_kg: float | None = Field(default=None, gt=0, le=200, allow_inf_nan=False)
    age_years: float | None = Field(default=None, ge=0, le=50)
    coat: Literal["gold", "gray", "cream", "black", "white"] = "gold"
    pattern: Literal["solid", "stripes", "spots"] = "solid"
    size: Literal["small", "medium", "large"] = "medium"
    likes: str = Field(default="", max_length=300)
    dislikes: str = Field(default="", max_length=300)
    photo_id: UUID | None = None

    @field_validator("birthday")
    @classmethod
    def past_birthday(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value


class MemberInput(HomeInput):
    name: str = Field(min_length=1, max_length=40)


class ObjectInput(HomeInput):
    kind: Literal["nest", "toy", "water", "feeder"]
    name: str = Field(min_length=1, max_length=80)
    x: int = Field(default=40, ge=8, le=88)
    y: int = Field(default=60, ge=18, le=82)
    note: str = Field(default="", max_length=300)


class TaskInput(HomeInput):
    kind: CareKind
    title: str = Field(min_length=1, max_length=80)
    due_at: datetime
    interval_days: int | None = Field(default=None, ge=1, le=365)
    assigned_to: UUID | None = None

    @field_validator("due_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class TaskAction(HomeInput):
    event_id: UUID
    actor_id: UUID | None = None
    action: Literal["complete", "postpone", "claim", "transfer", "edit", "cancel"]
    version: int | None = Field(default=None, ge=1)
    assigned_to: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=80)
    interval_days: int | None = Field(default=None, ge=1, le=365)
    next_due: datetime | None = None
    note: str = Field(default="", max_length=300)


class NoteInput(HomeInput):
    text: str = Field(min_length=1, max_length=500)
    scope: Literal["today", "preference", "observation"] = "observation"
    activity: CareKind | Literal["general"] = "general"
    actor_id: UUID | None = None


class DiaryInput(HomeInput):
    title: str = Field(min_length=1, max_length=80)
    text: str = Field(default="", max_length=2000)
    happened_on: date
    actor_id: UUID | None = None
    photo_id: UUID | None = None


class PhotoInput(HomeInput):
    data_url: str = Field(max_length=4_200_000)


class PhotoDraft(HomeInput):
    species: Literal["cat", "dog"] | None = None
    breed: str = Field(default="", max_length=80)
    coat: Literal["gold", "gray", "cream", "black", "white"] | None = None
    pattern: Literal["solid", "stripes", "spots"] | None = None
    uncertainty: str = Field(default="", max_length=300)
