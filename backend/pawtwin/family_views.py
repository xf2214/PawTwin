"""Public extension response DTOs exported through OpenAPI, never device domain schema."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class UserView(BaseModel):
    user_id: str
    username: str
    display_name: str
    avatar_ref: str
    created_at: str


class HouseholdView(BaseModel):
    household_id: str
    name: str
    timezone: str
    created_by: str
    created_at: str


class MembershipView(BaseModel):
    user_id: str
    role: Literal["admin", "carer", "guest"]
    family_label: str
    status: Literal["active"]
    feeding_pet_ids: list[str]
    joined_at: str


class MemberView(UserView, MembershipView):
    pass


class FamilySessionView(BaseModel):
    user: UserView
    household: HouseholdView | None
    membership: MembershipView | None
    members: list[MemberView]
    csrf_token: str
    identity_backend: Literal["local_account"]
    cloud_authenticated: Literal[False]


class MeasurementView(BaseModel):
    id: str
    household_id: str
    pet_id: str
    author_user_id: str
    kind: Literal["weight", "diet"]
    value: float
    unit: Literal["kg", "g"]
    value_g: float
    measured_at: str
    recorded_at: str
    source: Literal["owner_measured", "vet", "demo_sample"]
    diet_type: str | None
    note: str
    version: int
    deleted: bool
    corrections: list[dict[str, Any]]


class MeasurementListView(BaseModel):
    records: list[MeasurementView]


class ReportView(BaseModel):
    report_id: str
    household_id: str
    pet_id: str
    period: Literal["daily", "weekly"]
    date: str
    window_start: str
    window_end: str
    cutoff: str
    generated_at: str
    stat_version: int
    status: Literal["current", "superseded", "failed"]
    notification: Literal["not_sent"]
    source_record_ids: list[str]
    source_versions: dict[str, int] = Field(default_factory=dict)
    coverage: dict[str, Any]
    weight: dict[str, Any]
    diet: dict[str, float | None]
    care: dict[str, Any]
    growth: dict[str, Any]


class ReportListView(BaseModel):
    reports: list[ReportView]


class MemoryView(BaseModel):
    id: str
    household_id: str
    pet_id: str
    author_user_id: str
    author_name: str
    text: str
    topic: str
    status: Literal["candidate", "confirmed", "rejected"]
    valid_until: str | None
    created_at: str
    version: int
    deleted: bool
    memory_backend: Literal["owner_confirmed_database"]


class MemoryListView(BaseModel):
    memories: list[MemoryView]


class PetContextView(BaseModel):
    context_version: int
    as_of: str
    household_id: str
    pet_id: str
    valid_until: str
    source_versions: dict[str, int]
    unresolved_conflicts: list[dict[str, Any]]
    memory_backend: Literal["owner_confirmed_database"]
    layers: dict[str, Any]


class CareDraftView(BaseModel):
    kind: Literal["feeding", "water", "play", "brush", "bath", "nails", "clean", "walk"]
    title: str


class ReplyView(BaseModel):
    answer: str
    entry: Literal["app", "alexa_simulator"]
    backend: Literal["local_rules", "bedrock"]
    request_id: str | None
    model_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    inference_status: Literal["completed"] | None = None
    answer_origin: Literal["local_rules", "server_guard", "model"] = "local_rules"
    context_version: int
    source_record_ids: list[str]
    references: list[dict[str, Any]]
    action_executed: Literal[False]
    label: str
    care_draft: CareDraftView | None = None
    context_valid_until: str


class ProposalView(BaseModel):
    id: str
    household_id: str
    pet_id: str
    author_user_id: str
    kind: str
    title: str
    due_at: str
    version: int
    context_version: int
    status: Literal["awaiting_confirmation", "confirmed"]
    created_at: str
    device_action: Literal[False]
    task_id: str | None = None
    confirmed_by: str | None = None
    context_valid_until: str | None = None


class VisitPetView(BaseModel):
    name: str
    species: str
    breed: str = ""
    gender: str = "unknown"
    birthday: str | None = None
    birthday_estimated: bool = False
    neutered: bool | None = None
    expected_adult_weight_kg: float | None = None
    age_years: float | None = None
    coat: str = "gold"
    pattern: str = "solid"
    size: str = "medium"
    likes: str = ""
    dislikes: str = ""


class VisitMeasurementView(BaseModel):
    id: str
    kind: Literal["weight", "diet"]
    value: float
    unit: Literal["g", "kg"]
    value_g: float
    measured_at: str
    recorded_at: str | None = None
    source: str
    diet_type: str | None = None
    note: str = ""
    version: int = 1


class VisitObservationView(BaseModel):
    id: str
    text: str
    scope: str
    activity: str = "general"
    created_at: str
    version: int = 1
    source: Literal["owner_record"] = "owner_record"


class VisitPreferenceView(BaseModel):
    id: str
    text: str
    topic: str = "general"
    created_at: str
    valid_until: str | None = None
    active: bool
    version: int = 1
    source: Literal["owner_confirmed"] = "owner_confirmed"


class VisitCareView(BaseModel):
    id: str
    title: str
    kind: str | None = None
    due_at: str | None = None
    completed_at: str
    version: int = 1
    source: Literal["manual_care"] = "manual_care"


class VisitDiaryView(BaseModel):
    id: str
    title: str
    text: str = ""
    happened_on: str
    created_at: str | None = None
    version: int = 1
    source: Literal["owner_record"] = "owner_record"


class CareTaskView(BaseModel):
    id: str
    title: str
    kind: str
    due_at: str
    interval_days: int | None = None
    last_completed_at: str | None = None
    status: Literal["pending", "claimed"]
    version: int = 1
    source: Literal["owner_plan"] = "owner_plan"


class VisitAgeView(BaseModel):
    years: float | None
    days: int | None
    basis: Literal["birthday", "owner_entered", "unknown"]
    estimated: bool


class VisitSummaryView(BaseModel):
    pet: VisitPetView
    measurements: list[VisitMeasurementView]
    latest_weight: VisitMeasurementView | None
    observations: list[VisitObservationView]
    care: list[VisitCareView]
    diary: list[VisitDiaryView]
    preferences: list[VisitPreferenceView]
    age: VisitAgeView
    source_versions: dict[str, int]
    context_version: int
    as_of: str
    timezone: str
    window_start: str
    window_end: str
    days: Literal[7, 30, 90]
    include_demo: bool
    missing_fields: list[str]
    demo_excluded_count: int
    label: str


class CareAccessGrantView(BaseModel):
    id: str
    pet_name: str
    created_at: str
    expires_at: str
    revoked_at: str | None
    status: Literal["active", "expired", "revoked", "pet_archived"]


class CareAccessCreatedView(BaseModel):
    token: str
    grant: CareAccessGrantView


class CareAccessListView(BaseModel):
    grants: list[CareAccessGrantView]


class CareAccessContextView(BaseModel):
    grant: CareAccessGrantView
    pet: VisitPetView
    as_of: str
    timezone: str
    context_version: int
    read_only: Literal[True] = True
    preferences: list[VisitPreferenceView]
    observations: list[VisitObservationView]
    completed_care: list[VisitCareView]
    tasks: list[CareTaskView]
    measurements: list[VisitMeasurementView]
    label: str


class CareAccessReplyView(BaseModel):
    answer: str
    backend: Literal["local_rules"] = "local_rules"
    read_only: Literal[True] = True
    action_executed: Literal[False] = False
    as_of: str
    context_version: int
    source_record_ids: list[str]
    label: str
