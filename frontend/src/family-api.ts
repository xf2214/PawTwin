import { ApiError, request, restoreCsrf } from "./api";

export type Member = {
  user_id: string;
  display_name: string;
  family_label: string;
  role: "admin" | "carer" | "guest";
  feeding_pet_ids: string[];
  avatar_ref: string;
};
export type Me = {
  user: {
    user_id: string;
    display_name: string;
    username: string;
    avatar_ref: string;
  };
  household: { household_id: string; name: string; timezone: string } | null;
  membership: Member | null;
  members: Member[];
  csrf_token: string;
};
export type Pet = { id: string; name: string; species: string; likes: string };
export type Task = {
  id: string;
  pet_id: string;
  title: string;
  kind: string;
  due_at: string;
  status: string;
  completed: boolean;
  version: number;
  assigned_to: string | null;
  interval_days: number | null;
  last_completed_at: string | null;
  claimed_by: string | null;
};
export type Home = {
  pets: Pet[];
  tasks: Task[];
  revision: number;
  notes: Note[];
  diary: Diary[];
  occurrences?: {
    id: string;
    task_id: string;
    pet_id: string;
    due_at: string;
    completed_at: string;
    completed_by: string;
    status: string;
    source: string;
  }[];
  history: {
    id: string;
    pet_id: string;
    text: string;
    actor: string;
    created_at: string;
  }[];
};
export type Note = {
  id: string;
  pet_id: string;
  text: string;
  scope: string;
  activity: string;
  author_user_id: string;
  author_name: string;
  version: number;
  created_at: string;
};
export type Diary = {
  id: string;
  pet_id: string;
  title: string;
  text: string;
  happened_on: string;
  photo_id: string | null;
  author_user_id: string;
  author_name: string;
  version: number;
};
export type Invitation = {
  invitation_id: string;
  role: string;
  expires_at: string;
  max_uses: number;
  use_count: number;
  revoked: boolean;
};
export type Measurement = {
  id: string;
  kind: "weight" | "diet";
  value: number;
  unit: string;
  value_g: number;
  measured_at: string;
  source: string;
  version: number;
  note: string;
  diet_type: string | null;
};
export type Report = {
  report_id: string;
  period: string;
  date: string;
  generated_at: string;
  source_versions: Record<string, number>;
  status: string;
  window_start: string;
  window_end: string;
  cutoff: string;
  stat_version: number;
  source_record_ids: string[];
  weight: {
    change_g: number | null;
    change_percent: number | null;
    span_days: number | null;
  };
  care: {
    manual_completed: number;
    pending: number;
    overdue: number;
    device_success: number | null;
    device_failed: number;
    device_unknown: number;
  };
  diet: {
    actual_intake_g: number | null;
    dispensed_g: number | null;
    simulated_device_dispensed_g: number | null;
  };
  notification: string;
};
export type Memory = {
  id: string;
  text: string;
  topic: string;
  status: string;
  version: number;
  author_name: string;
  valid_until: string | null;
};
export type Reply = {
  answer: string;
  backend: string;
  context_version: number;
  source_record_ids: string[];
  references: { id: string; url: string; title: string }[];
  entry: "app" | "alexa_simulator";
  request_id: string | null;
  model_id: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_ms: number | null;
  inference_status: "completed" | null;
  answer_origin: "local_rules" | "server_guard" | "model";
  action_executed: false;
  label: string;
  care_draft: { kind: string; title: string } | null;
  context_valid_until: string;
};
export type Proposal = {
  id: string;
  title: string;
  version: number;
  context_version: number;
  status: string;
  kind: string;
  due_at: string;
  task_id: string | null;
  device_action: false;
  context_valid_until: string | null;
};

export async function getMe(): Promise<Me> {
  const me = await request<Me>("/api/family/me");
  restoreCsrf(me.csrf_token);
  return me;
}

export const SOURCE: Record<string, string> = {
  owner_measured: "主人实测",
  vet: "兽医资料",
  demo_sample: "演示样本",
};

// Whitelisted export / temporary-access views omit account and household data.
export type VisitPet = {
  name: string; species: string; breed: string; gender: string;
  birthday: string | null; birthday_estimated: boolean; neutered: boolean | null;
  expected_adult_weight_kg: number | null; age_years: number | null;
  coat: string; pattern: string; size: string; likes: string; dislikes: string;
};
export type VisitMeasurement = Measurement & { recorded_at: string | null; unit: "g" | "kg" };
export type VisitObservation = { id: string; text: string; scope: string; activity: string; created_at: string; version: number; source: "owner_record" };
export type VisitPreference = { id: string; text: string; topic: string; created_at: string; valid_until: string | null; active: boolean; version: number; source: "owner_confirmed" };
export type VisitCare = { id: string; title: string; kind: string | null; due_at: string | null; completed_at: string; version: number; source: "manual_care" };
export type VisitDiary = { id: string; title: string; text: string; happened_on: string; created_at: string | null; version: number; source: "owner_record" };
export type VisitSummary = {
  pet: VisitPet; measurements: VisitMeasurement[]; latest_weight: VisitMeasurement | null;
  age: { years: number | null; days: number | null; basis: "birthday" | "owner_entered" | "unknown"; estimated: boolean };
  observations: VisitObservation[]; preferences: VisitPreference[]; care: VisitCare[]; diary: VisitDiary[];
  source_versions: Record<string, number>; as_of: string; timezone: string;
  window_start: string; window_end: string; days: number; include_demo: boolean;
  demo_excluded_count: number; missing_fields: string[]; context_version: number; label: string;
};
export type CareAccessGrant = {
  id: string; pet_name: string; created_at: string; expires_at: string; revoked_at: string | null;
  status: "active" | "expired" | "revoked" | "pet_archived";
};
export type AccessTask = { id: string; title: string; kind: string; due_at: string; interval_days: number | null; last_completed_at: string | null; status: "pending" | "claimed"; version: number; source: "owner_plan" };
export type CareAccessContext = {
  grant: CareAccessGrant; pet: VisitPet; as_of: string; timezone: string; context_version: number;
  read_only: true; preferences: VisitPreference[]; observations: VisitObservation[];
  completed_care: VisitCare[]; tasks: AccessTask[]; measurements: VisitMeasurement[]; label: string;
};
export type CareAccessReply = { answer: string; backend: "local_rules"; read_only: true; action_executed: false; as_of: string; context_version: number; source_record_ids: string[]; label: string };

export async function accessRequest<T>(token: string, path: "context" | "chat", init: RequestInit = {}): Promise<T> {
  // Separate transport: a signed-in owner's cookie must never authorize a visitor.
  const response = await fetch(`/api/care-access/${path}`, {
    ...init, credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, "临时访问请求失败");
  return response.json() as Promise<T>;
}
