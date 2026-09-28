// Typed API client. Types are hand-written from the FROZEN contract
// (contracts/openapi.json + domain.schema.json) — the single source of truth.
// Still zero runtime dependencies on Day-2: nothing here needs a code generator
// or a request library.

export type RunState =
  | 'queued'
  | 'analyzing'
  | 'needs_info'
  | 'blocked'
  | 'awaiting_approval'
  | 'declined'
  | 'expired'
  | 'executing'
  | 'succeeded'
  | 'failed'
  | 'unknown'

export type AnalyzerBackend = 'inline' | 'local_fake' | 'bedrock'
export type DeviceMode = 'succeeded' | 'failed' | 'unknown'
export type ToolName =
  | 'get_pet_facts'
  | 'get_recent_events'
  | 'search_owner_memory'
  | 'get_policy_summary'

export interface Action {
  kind: 'dispense_food' | 'create_play_task' | 'observe'
  grams: number
}

export interface Proposal {
  action: Action
  explanation: string
  evidence_ids: string[]
  missing_fields: string[]
}

export interface Receipt {
  command_id: string
  status: 'succeeded' | 'failed' | 'unknown'
  simulated: true
}

// One read-only tool call that really happened. Bounded summary only: never the
// raw event note and never hidden reasoning.
export interface EvidenceItem {
  evidence_id: string
  tool: ToolName
  source: 'repository' | 'policy' | 'memory'
  retrieved_at: string
  summary: string
}

// Auditable model-call record. request_id stays null until a REAL Bedrock call
// happens, so a local run can never be mistaken for a cloud one.
export interface AnalysisTelemetry {
  backend: AnalyzerBackend
  model_id: string | null
  model_calls: number
  output_tokens: number
  duration_ms: number
  started_at: string
  finished_at: string
  request_id: string | null
  limit_exceeded: string | null
}

export interface FactsView {
  // null means UNKNOWN. It is never rendered as 0: the policy judges
  // MISSING_FACTS on null, and showing "0 minutes ago" would contradict it.
  last_fed_minutes_ago: number | null
  daily_dispensed_grams: number | null
  daily_limit_grams: number
  single_serving_grams: number
  minimum_interval_minutes: number
  facts_version: number
}

export interface RunView {
  run_id: string
  state: RunState
  facts_version: number
  proposal: Proposal | null
  receipt: Receipt | null
  expires_at: string | null
  created_at: string
  proposal_version: number
  action_digest: string | null
  policy_reason: string | null
  failure_reason: string | null
  evidence: EvidenceItem[]
  telemetry: AnalysisTelemetry | null
}

export interface StateView {
  pet_id: 'mochi'
  mode: 'local' | 'aws'
  aws_connected: boolean
  analyzer: AnalyzerBackend
  storage: 'sqlite' | 'dynamodb'
  memory: MemoryBackend
  device_mode: DeviceMode
  // Rotated by POST /api/demo/new-session; pet memory and facts survive it.
  conversation_id: string | null
  facts: FactsView
  runs: RunView[]
  feedback: FeedbackView[]
}

export interface EventAccepted {
  run_id: string
  state: RunState
}

export interface EventIn {
  event_id: string
  pet_id?: 'mochi'
  kind: 'food_request' | 'attention_request'
  room: 'kitchen' | 'living_room' | 'unknown'
  note?: string
  source?: 'simulator'
}

export interface ApprovalIn {
  decision: 'approve' | 'decline'
  proposal_version: number
  action_digest: string
}

// Only the two injectable facts. The hard limits are not expressible here, which
// is the point: no request from this page can raise the daily quota.
export interface DemoFactsIn {
  last_fed_minutes_ago?: number
  daily_dispensed_grams?: number
  clear?: ('last_fed_minutes_ago' | 'daily_dispensed_grams')[]
  reset?: boolean
}

export interface DemoAck {
  facts: FactsView
  device_mode: DeviceMode | null
}

// Long-term memory (Day-3). ``memory_status='saved'`` means the RAW owner text is
// stored in the business database -- it NEVER means it was extracted into AgentCore
// memory. ``memory_backend`` is carried alongside so a local 'saved' can never be
// read as 'retrieved memory'. 'available' only ever appears with real retrieval.
export type MemoryStatus = 'saved' | 'processing' | 'available' | 'failed'
export type MemoryBackend = 'not_implemented' | 'agentcore'
export type FeedbackScope = 'observation' | 'today_only'

export interface FeedbackView {
  feedback_id: string
  scope: FeedbackScope
  text: string
  memory_status: MemoryStatus
  memory_backend: MemoryBackend
  created_at: string
  conversation_id: string | null
}

export interface FeedbackIn {
  text: string
  scope: FeedbackScope
}

export interface NewSessionView {
  conversation_id: string
}

// States after which nothing changes by itself. NOTE: this is NOT the backend's
// terminal set (declined/expired/succeeded/failed/unknown) -- blocked/needs_info
// are settled for the UI but are deliberately excluded from the backend's
// claimable/terminal logic. Renamed on Day-2 to stop the two being confused.
const SETTLED: RunState[] = [
  'awaiting_approval',
  'declined',
  'succeeded',
  'failed',
  'expired',
  'blocked',
  'needs_info',
  'unknown',
]

export function isSettled(state: RunState): boolean {
  return SETTLED.includes(state)
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// The CSRF token lives in memory only (never localStorage) and is refreshed on
// login; the session cookie is HttpOnly and managed by the browser.
let csrfToken: string | null = null

export function hasCsrf(): boolean {
  return csrfToken !== null
}

function newEventId(): string {
  return crypto.randomUUID()
}

async function readError(res: Response): Promise<string> {
  try {
    const text = await res.text()
    return text.slice(0, 200) || res.statusText
  } catch {
    return res.statusText
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  const method = init.method ?? 'GET'
  if (method !== 'GET' && csrfToken) headers.set('X-CSRF-Token', csrfToken)
  const res = await fetch(path, { ...init, method, headers, credentials: 'same-origin' })
  if (!res.ok) throw new ApiError(res.status, await readError(res))
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export async function login(passphrase: string): Promise<void> {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passphrase }),
    credentials: 'same-origin',
  })
  if (!res.ok) throw new ApiError(res.status, await readError(res))
  const data = (await res.json()) as { csrf_token: string }
  csrfToken = data.csrf_token
}

export async function logout(): Promise<void> {
  try {
    await request('/api/logout', { method: 'POST' })
  } catch {
    // Best-effort server logout; local state is always cleared below so a user
    // can never be locked into a session (e.g. after a reload drops the token).
  } finally {
    csrfToken = null
  }
}

export const getState = (): Promise<StateView> => request<StateView>('/api/state')

export const getRun = (runId: string): Promise<RunView> => request<RunView>(`/api/runs/${runId}`)

export function postEvent(kind: EventIn['kind'], room: EventIn['room'], note = ''): Promise<EventAccepted> {
  const event: EventIn = { event_id: newEventId(), kind, room, note }
  return request<EventAccepted>('/api/events', { method: 'POST', body: JSON.stringify(event) })
}

export const postApproval = (runId: string, approval: ApprovalIn): Promise<RunView> =>
  request<RunView>(`/api/runs/${runId}/approval`, {
    method: 'POST',
    body: JSON.stringify(approval),
  })

export const postDemoFacts = (body: DemoFactsIn): Promise<DemoAck> =>
  request<DemoAck>('/api/demo/facts', { method: 'POST', body: JSON.stringify(body) })

export const postDeviceMode = (mode: DeviceMode): Promise<DemoAck> =>
  request<DemoAck>('/api/demo/device-mode', { method: 'POST', body: JSON.stringify({ mode }) })

export const postFeedback = (body: FeedbackIn): Promise<FeedbackView> =>
  request<FeedbackView>('/api/feedback', { method: 'POST', body: JSON.stringify(body) })

export const getFeedback = (feedbackId: string): Promise<FeedbackView> =>
  request<FeedbackView>(`/api/feedback/${feedbackId}`)

// Rotates the AgentCore conversation id; login, facts and pet memory stay intact.
export const postNewSession = (): Promise<NewSessionView> =>
  request<NewSessionView>('/api/demo/new-session', { method: 'POST' })

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// The backend analysis deadline is 45s. The client budget must be strictly
// larger, otherwise the page gives up in the same instant the server writes
// FAILED and the owner is left staring at "analyzing" forever.
export const POLL_TIMEOUT_MS = 75_000

// Poll a run until it settles or the deadline passes. The final observed run is
// always returned so the caller can show an explicit "still working" notice
// instead of an endless spinner. The client never declares a failure itself.
export async function pollRun(
  runId: string,
  onUpdate: (run: RunView) => void,
  opts: { intervalMs?: number; timeoutMs?: number } = {},
): Promise<RunView> {
  const intervalMs = opts.intervalMs ?? 2000
  const timeoutMs = opts.timeoutMs ?? POLL_TIMEOUT_MS
  const deadline = Date.now() + timeoutMs
  let last: RunView = await getRun(runId)
  onUpdate(last)
  let waited = 0
  while (!isSettled(last.state) && Date.now() < deadline) {
    // Back off after 15s: nothing new is learned by hammering a 45s analysis.
    const delay = waited < 15_000 ? intervalMs : Math.max(intervalMs, 5000)
    await sleep(delay)
    waited += delay
    last = await getRun(runId)
    onUpdate(last)
  }
  return last
}
