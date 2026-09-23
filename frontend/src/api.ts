// Typed API client. Types are hand-written from the FROZEN contract
// (contracts/openapi.json + domain.schema.json) — the single source of truth.
// No new dependencies are added on Day-1 (see plan §3.3).

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

export interface FactsView {
  last_fed_minutes_ago: number
  daily_dispensed_grams: number
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
}

export interface StateView {
  pet_id: 'mochi'
  mode: 'local' | 'aws'
  aws_connected: boolean
  facts: FactsView
  runs: RunView[]
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

// Polling stops once a run settles. awaiting_approval is settled (it waits for a
// human) but not terminal; the rest are terminal (no further automatic change).
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

export const TERMINAL: RunState[] = [
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

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Poll a run every intervalMs until it settles or the deadline passes. The final
// observed run is always returned so the caller can show an explicit
// failure/unknown state instead of an endless spinner.
export async function pollRun(
  runId: string,
  onUpdate: (run: RunView) => void,
  opts: { intervalMs?: number; timeoutMs?: number } = {},
): Promise<RunView> {
  const intervalMs = opts.intervalMs ?? 2000
  const timeoutMs = opts.timeoutMs ?? 45_000
  const deadline = Date.now() + timeoutMs
  let last: RunView = await getRun(runId)
  onUpdate(last)
  while (!isSettled(last.state) && Date.now() < deadline) {
    await sleep(intervalMs)
    last = await getRun(runId)
    onUpdate(last)
  }
  return last
}
