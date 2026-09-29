import { useCallback, useEffect, useRef, useState } from 'react'

import {
  ApiError,
  type AnalyzerBackend,
  type DemoFactsIn,
  type DeviceMode,
  type FeedbackScope,
  type MemoryStatus,
  type RunState,
  type RunView,
  type StateView,
  getRun,
  getState,
  hasCsrf,
  isSettled,
  login,
  logout,
  pollRun,
  postApproval,
  postDemoFacts,
  postDeviceMode,
  postEvent,
  postFeedback,
  postNewSession,
} from './api'

const STATE_LABELS: Record<RunState, string> = {
  queued: '排队中',
  analyzing: '分析中',
  needs_info: '信息不足',
  blocked: '已阻止',
  awaiting_approval: '等待主人确认',
  declined: '已拒绝',
  expired: '已过期',
  executing: '执行中',
  succeeded: '已完成',
  failed: '执行失败',
  unknown: '状态未知',
}

const ACTION_LABELS: Record<string, string> = {
  dispense_food: '出粮',
  create_play_task: '创建陪玩任务',
  observe: '仅观察',
}

// Day-4 ruling 13: labels are EVIDENCE-driven, never configuration-driven. The
// wording with the 「真实」 marker may only appear once a real cloud artifact is
// observable in the payloads (a non-null request_id / a real available memory
// status); config alone (analyzer==='bedrock') only ever earns 「已配置」.
const ANALYZER_CONFIG_LABELS: Record<AnalyzerBackend, string> = {
  inline: '确定性测试后端',
  local_fake: '本地替身（非真实模型）',
  bedrock: 'AWS Bedrock（已配置，未经真实调用验证）',
}

const MEMORY_BACKEND_LABELS: Record<'not_implemented' | 'agentcore', string> = {
  not_implemented: '未实现（无 AWS 账号）',
  agentcore: 'AgentCore（已配置，未经真实检索证据验证）',
}

const TOOL_LABELS: Record<string, string> = {
  get_pet_facts: '查询宠物当前事实',
  get_recent_events: '查询近期事件',
  search_owner_memory: '检索主人长期记忆',
  get_policy_summary: '读取策略摘要',
}

const SOURCE_LABELS: Record<string, string> = {
  repository: '业务数据库',
  policy: '硬性策略',
  memory: '长期记忆',
}

const DEVICE_LABELS: Record<DeviceMode, string> = {
  succeeded: 'succeeded（成功回执）',
  failed: 'failed（失败回执）',
  unknown: 'unknown（未知回执）',
}

// ``saved`` is the ONLY status a local (no-account) run can reach: it means the raw
// owner text is stored, never that a memory was extracted or retrieved.
// Day-4 ruling 13: even ``available``/``processing`` are phrased as lifecycle
// states plus the backend name — never 「真实记忆」, which would let a stub or a
// future wiring change assert cloud truth without evidence.
const MEMORY_STATUS_LABELS: Record<MemoryStatus, string> = {
  saved: '已保存原文（未提炼）',
  processing: '提炼中（尚未可检索）',
  available: '可检索（AgentCore 生命周期状态，以服务端记录为准）',
  failed: '提炼失败',
}

const SCOPE_LABELS: Record<FeedbackScope, string> = {
  observation: '观察（可长期提炼）',
  today_only: '仅今天（不成为永久偏好）',
}

const POLICY_LABELS: Record<string, string> = {
  ALLOWED: '策略允许',
  NON_FEEDING: '非喂食动作，不占配额',
  MISSING_FACTS: '缺少必要事实，已停止喂食建议',
  RECENT_FEED: '距上次喂食过近',
  SINGLE_SERVING_EXCEEDED: '超过单次上限',
  DAILY_LIMIT_EXCEEDED: '超过当日配额',
}

const FAILURE_LABELS: Record<string, string> = {
  UNKNOWN_EVIDENCE: '建议引用了未真实检索到的依据，已拒绝',
  MODEL_INVALID_OUTPUT: '模型输出不符合契约，已拒绝',
  MODEL_CALL_LIMIT: '超过每任务模型调用上限',
  TOKEN_LIMIT: '超过单次输出 token 上限',
  ANALYSIS_TIMEOUT: '分析超时（45 秒），未产生建议',
  ATTEMPTS_EXHAUSTED: '处理尝试次数已用尽',
  BACKEND_UNAVAILABLE: '真实模型后端不可用（未回退到替身）',
  ANALYZER_ERROR: '分析器异常，已失败关闭',
}

// A 409 is not a bug: it is the state machine refusing something. Say which.
const CONFLICT_HINTS: Array<[string, string]> = [
  ['STALE_APPROVAL_FACTS_CHANGED', '事实已变化，旧批准失效。系统已按新事实重评策略（未调用模型），请重新确认。'],
  ['APPROVAL_MISMATCH', '批准参数与当前建议不匹配，已拒绝执行。'],
  ['POLICY_BLOCKED_ON_EXECUTE', '执行前复查策略未通过，本次动作已被阻止。'],
  ['NOT_AWAITING_APPROVAL', '该任务已不在等待确认状态（可能已处理、过期或被另一处批准）。'],
  ['RUN_NOT_FOUND', '找不到该任务。'],
]

function describeAction(run: RunView | null): string {
  if (!run?.proposal) return '暂无建议'
  const { kind, grams } = run.proposal.action
  return kind === 'dispense_food' ? `${ACTION_LABELS[kind]} ${grams} 克` : ACTION_LABELS[kind]
}

function stateLabel(run: RunView): string {
  // "failed" covers two different things; tell them apart instead of misleading.
  if (run.state === 'failed') return run.receipt ? '执行失败' : '分析失败'
  return STATE_LABELS[run.state]
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString()
}

function conflictHint(detail: string): string | null {
  const found = CONFLICT_HINTS.find(([code]) => detail.includes(code))
  return found ? found[1] : null
}

function factMinutes(value: number | null | undefined): string {
  return value == null ? '未知' : `${value} 分钟`
}

function factGrams(value: number | null | undefined, limit: number | undefined): string {
  return value == null ? `未知 / ${limit ?? '—'} 克` : `${value} / ${limit ?? '—'} 克`
}

export default function App() {
  const [state, setState] = useState<StateView | null>(null)
  const [authed, setAuthed] = useState(false)
  const [activeRun, setActiveRun] = useState<RunView | null>(null)
  const [busy, setBusy] = useState(false)
  const [polling, setPolling] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [pollDeadline, setPollDeadline] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [passphrase, setPassphrase] = useState('')
  const [canAct, setCanAct] = useState(hasCsrf())
  const [demoOpen, setDemoOpen] = useState(false)
  const [note, setNote] = useState('')
  const [room, setRoom] = useState<'kitchen' | 'living_room' | 'unknown'>('kitchen')
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackScope, setFeedbackScope] = useState<FeedbackScope>('observation')
  const [factLastFed, setFactLastFed] = useState('')
  const [factDispensed, setFactDispensed] = useState('')
  const [clearLastFed, setClearLastFed] = useState(false)
  const [clearDispensed, setClearDispensed] = useState(false)
  const pollingRef = useRef(false)

  const handleError = useCallback((err: unknown) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        setAuthed(false)
        setCanAct(false)
        setError('会话已失效，请重新登录。')
        return
      }
      if (err.status === 403) {
        setCanAct(false)
        setError('操作令牌缺失或失效，请重新登录后再试。')
        return
      }
      setError(`请求失败（${err.status}）：${err.message}`)
      return
    }
    setError('无法连接本地后端，请确认服务已启动。')
  }, [])

  const refresh = useCallback(async (): Promise<StateView | null> => {
    try {
      const snapshot = await getState()
      setState(snapshot)
      setAuthed(true)
      setError(null)
      return snapshot
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthed(false)
        setState(null)
      } else {
        handleError(err)
      }
      return null
    }
  }, [handleError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  // Follow a run until the backend settles it. The client never decides the
  // verdict itself: on deadline it says "still working", not "failed".
  const trackRun = useCallback(
    async (runId: string) => {
      if (pollingRef.current) return
      pollingRef.current = true
      setPolling(true)
      setPollDeadline(false)
      setElapsed(0)
      const startedAt = Date.now()
      const timer = window.setInterval(
        () => setElapsed(Math.round((Date.now() - startedAt) / 1000)),
        500,
      )
      try {
        const run = await pollRun(runId, setActiveRun)
        if (!isSettled(run.state)) setPollDeadline(true)
        await refresh()
      } catch (err) {
        handleError(err)
      } finally {
        window.clearInterval(timer)
        setPolling(false)
        pollingRef.current = false
        setCanAct(hasCsrf())
      }
    },
    [handleError, refresh],
  )

  // After a (re)load, surface the most recent run and keep following it if the
  // backend has not settled it yet.
  useEffect(() => {
    if (activeRun === null && state && state.runs.length > 0) {
      const latest = state.runs[0]
      setActiveRun(latest)
      if (!isSettled(latest.state)) void trackRun(latest.run_id)
    }
  }, [state, activeRun, trackRun])

  async function onLogin(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(passphrase)
      setPassphrase('')
      setCanAct(true)
      await refresh()
    } catch (err) {
      setCanAct(false)
      setError(err instanceof ApiError && err.status === 401 ? '演示口令不正确。' : '登录失败。')
    } finally {
      setBusy(false)
    }
  }

  async function onLogout() {
    await logout()
    setAuthed(false)
    setState(null)
    setActiveRun(null)
    setCanAct(false)
  }

  async function sendEvent(kind: 'food_request' | 'attention_request', customNote = '') {
    setBusy(true)
    setError(null)
    setNotice(null)
    setPollDeadline(false)
    try {
      const accepted = await postEvent(kind, room, customNote)
      // Release the buttons at once: analysis may take seconds and the demo
      // controls must stay usable while it runs.
      setBusy(false)
      setCanAct(hasCsrf())
      await trackRun(accepted.run_id)
    } catch (err) {
      handleError(err)
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function decide(decision: 'approve' | 'decline') {
    if (!activeRun || activeRun.action_digest === null) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const run = await postApproval(activeRun.run_id, {
        decision,
        proposal_version: activeRun.proposal_version,
        action_digest: activeRun.action_digest,
      })
      setActiveRun(run)
      await refresh()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setNotice(conflictHint(err.message) ?? `操作被拒绝（409）：${err.message}`)
        // The backend has usually already moved the run (A03 re-evaluates it), so
        // re-read it instead of leaving a stale "awaiting approval" on screen.
        try {
          setActiveRun(await getRun(activeRun.run_id))
        } catch {
          // The refresh below is the fallback.
        }
      } else {
        handleError(err)
      }
      await refresh()
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function applyFacts(body: DemoFactsIn) {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await postDemoFacts(body)
      setNotice(
        body.reset
          ? '已恢复演示事实默认值。'
          : '事实已更新，facts_version 递增；此前待批准的建议将失效并要求重新确认。',
      )
      setFactLastFed('')
      setFactDispensed('')
      setClearLastFed(false)
      setClearDispensed(false)
      await refresh()
    } catch (err) {
      handleError(err)
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function applyDeviceMode(mode: DeviceMode) {
    setBusy(true)
    setError(null)
    try {
      await postDeviceMode(mode)
      setNotice(`模拟执行器模式已设为 ${mode}，仅影响之后的新命令；本进程内有效，重启后复位。`)
      await refresh()
    } catch (err) {
      handleError(err)
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function submitFeedback(event: React.FormEvent) {
    event.preventDefault()
    const text = feedbackText.trim()
    if (text.length === 0) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await postFeedback({ text, scope: feedbackScope })
      setFeedbackText('')
      setNotice(
        feedbackScope === 'today_only'
          ? '已保存为「仅今天」的业务记录，不会成为永久偏好；未接入 AgentCore，不提炼为长期记忆。'
          : '已保存主人观察原文（归因为主人，非模型推断）；未接入 AgentCore，不提炼为长期记忆。',
      )
      await refresh()
    } catch (err) {
      handleError(err)
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function startNewSession() {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const result = await postNewSession()
      setNotice(
        `已开启新会话（conversation ${result.conversation_id.slice(0, 8)}…）；宠物记忆、事实与登录均保留。`,
      )
      await refresh()
    } catch (err) {
      handleError(err)
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  if (!authed) {
    return (
      <main>
        <header className="hero">
          <div>
            <p className="eyebrow">PET CARE AGENT · 演示登录</p>
            <h1>PawTwin</h1>
            <p className="lede">照护请求需经主人审批。登录后查看 Mochi 的实时状态与建议。</p>
          </div>
        </header>
        <section className="panel login">
          <form onSubmit={onLogin}>
            <label htmlFor="passphrase">演示口令</label>
            <input
              id="passphrase"
              type="password"
              value={passphrase}
              autoComplete="current-password"
              onChange={(e) => setPassphrase(e.target.value)}
            />
            <button type="submit" disabled={busy || passphrase.length === 0}>
              登录演示
            </button>
          </form>
          {error ? <p className="error" role="alert">{error}</p> : null}
          <p className="hint">未授权时不会读取业务数据、触发模型或批准任务。</p>
        </section>
      </main>
    )
  }

  const facts = state?.facts
  const awaiting = activeRun?.state === 'awaiting_approval'

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">PET CARE AGENT</p>
          <h1>PawTwin</h1>
          <p className="lede">
            以个体事实与主人审批为核心的宠物照护 Agent。本页为软件测试演示，非喂养建议。
          </p>
        </div>
        <div className="connection">
          <span aria-hidden="true" />
          <div>
            <strong data-testid="mode-badge">
              {state ? `${state.mode.toUpperCase()} · ${state.aws_connected ? 'AWS 已连接' : 'AWS 未连接'}` : '加载中'}
            </strong>
            <small>状态来源 /api/state</small>
          </div>
          <button type="button" className="ghost" onClick={onLogout} disabled={busy}>
            退出
          </button>
        </div>
      </header>

      <section className="truth-strip" aria-label="实现边界">
        <div><strong>模拟传感器事件</strong><span>事件来源固定为 simulator</span></div>
        <div><strong>模拟执行器</strong><span>回执 simulated，不驱动真实硬件</span></div>
        <div><strong>项圈为概念设计</strong><span>当前没有设备连接</span></div>
        <div><strong>{state?.aws_connected ? 'AWS 已连接' : 'AWS 未连接'}</strong><span>本地替身与云端状态分别标注</span></div>
      </section>

      {state ? (
        <p className="impl-labels" data-testid="impl-labels">
          <span>分析器：{activeRun?.telemetry?.request_id ? 'AWS Bedrock（真实模型，本 run 已有 request id）' : ANALYZER_CONFIG_LABELS[state.analyzer]}</span>
          <span>存储：{state.storage === 'sqlite' ? 'SQLite（本地实现；repo_dynamo 未实现，未经云端验证）' : 'DynamoDB（未经云端验证）'}</span>
          <span>长期记忆：{(state.feedback ?? []).some((f) => f.memory_status === 'available') ? 'AgentCore（生命周期显示可检索）' : MEMORY_BACKEND_LABELS[state.memory]}</span>
        </p>
      ) : null}

      {error ? <p className="error" role="alert">{error}</p> : null}
      {notice ? <p className="notice" data-testid="notice" role="status">{notice}</p> : null}
      {pollDeadline ? (
        <p className="warn" data-testid="poll-deadline">
          已超过客户端等待上限（75 秒），任务仍在后端处理。页面不会自行判定失败，请刷新查看最新状态。
        </p>
      ) : null}
      {!canAct ? (
        <p className="warn" data-testid="reauth-hint">
          会话可查看，但执行批准/拒绝需要操作令牌。请重新登录以继续操作。
        </p>
      ) : null}

      <div className="columns">
        <section className="panel" aria-label="宠物与请求">
          <p className="section-label">宠物与请求</p>
          <h2>🐱 Mochi</h2>
          <dl className="facts" data-testid="facts">
            <div><dt>上次喂食距今</dt><dd>{factMinutes(facts?.last_fed_minutes_ago)}</dd></div>
            <div>
              <dt>当日已出粮</dt>
              <dd>{factGrams(facts?.daily_dispensed_grams, facts?.daily_limit_grams)}</dd>
            </div>
            <div><dt>单次上限</dt><dd>{facts?.single_serving_grams ?? '—'} 克</dd></div>
            <div><dt>最短间隔</dt><dd>{facts?.minimum_interval_minutes ?? '—'} 分钟</dd></div>
          </dl>
          <div className="actions">
            <button type="button" onClick={() => sendEvent('food_request')} disabled={busy || !canAct}>
              发送吃饭请求
            </button>
            <button type="button" onClick={() => sendEvent('attention_request')} disabled={busy || !canAct}>
              发送互动请求
            </button>
          </div>
        </section>

        <section className="panel" aria-label="建议与确认">
          <p className="section-label">建议与确认</p>
          {activeRun ? (
            <>
              <p className="state" data-testid="run-status">
                {stateLabel(activeRun)}
              </p>
              {polling ? (
                <p className="muted" data-testid="run-elapsed">正在等待后端结论，已等待 {elapsed} 秒…</p>
              ) : null}
              {activeRun.policy_reason && activeRun.policy_reason !== 'ALLOWED' ? (
                <p className="reason" data-testid="policy-reason">
                  策略结论：{POLICY_LABELS[activeRun.policy_reason] ?? activeRun.policy_reason}
                </p>
              ) : null}
              {activeRun.failure_reason ? (
                <p className="reason error" data-testid="failure-reason">
                  失败原因：{FAILURE_LABELS[activeRun.failure_reason] ?? activeRun.failure_reason}
                </p>
              ) : null}
              {activeRun.proposal ? (
                <div className="proposal">
                  <p className="action" data-testid="proposal-action">{describeAction(activeRun)}</p>
                  <p className="explanation">{activeRun.proposal.explanation}</p>
                </div>
              ) : (
                <p className="muted">当前任务没有可执行的建议。</p>
              )}
              {activeRun.evidence.length > 0 ? (
                <div className="evidence">
                  <p className="section-label">真实查询证据</p>
                  <ul className="evidence-list" data-testid="evidence-list">
                    {activeRun.evidence.map((item) => (
                      <li key={item.evidence_id} data-testid="evidence-item">
                        <strong>{TOOL_LABELS[item.tool] ?? item.tool}</strong>
                        <span className="tag">{SOURCE_LABELS[item.source] ?? item.source}</span>
                        <time dateTime={item.retrieved_at}>{formatTime(item.retrieved_at)}</time>
                        <code>{item.evidence_id}</code>
                        <p>{item.summary}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="muted" data-testid="evidence-empty">
                  本次分析没有检索记录（确定性测试后端不产生证据）。
                </p>
              )}
              {activeRun.telemetry ? (
                <dl className="telemetry" data-testid="telemetry">
                  <div><dt>分析后端</dt><dd>{activeRun.telemetry.request_id ? `${ANALYZER_CONFIG_LABELS[activeRun.telemetry.backend].replace('（已配置，未经真实调用验证）', '')}（本 run 已有 request id）` : ANALYZER_CONFIG_LABELS[activeRun.telemetry.backend]}</dd></div>
                  <div><dt>模型调用</dt><dd>{activeRun.telemetry.model_calls} 次（上限 4）</dd></div>
                  <div><dt>输出 tokens</dt><dd>{activeRun.telemetry.output_tokens}（上限 800）</dd></div>
                  <div><dt>耗时</dt><dd>{activeRun.telemetry.duration_ms} ms</dd></div>
                  <div>
                    <dt>云端 request id</dt>
                    <dd>{activeRun.telemetry.request_id ?? '无（未发生真实云调用）'}</dd>
                  </div>
                </dl>
              ) : null}
              {activeRun.receipt ? (
                <p className="receipt" data-testid="receipt">
                  {activeRun.receipt.status === 'succeeded'
                    ? '模拟执行成功'
                    : activeRun.receipt.status === 'failed'
                      ? '模拟执行失败'
                      : '执行状态未知'}
                  （simulated={String(activeRun.receipt.simulated)}）
                </p>
              ) : null}
              <div className="actions">
                <button
                  type="button"
                  className="primary"
                  data-testid="approve"
                  onClick={() => decide('approve')}
                  disabled={busy || !awaiting || !canAct}
                >
                  批准本次动作
                </button>
                <button
                  type="button"
                  className="danger"
                  data-testid="decline"
                  onClick={() => decide('decline')}
                  disabled={busy || !awaiting || !canAct}
                >
                  拒绝本次动作
                </button>
              </div>
            </>
          ) : (
            <p className="muted">发送一个请求以查看建议与审批。</p>
          )}
        </section>

        <section className="panel" aria-label="任务与记忆">
          <p className="section-label">任务与记忆</p>
          <ul className="runs" data-testid="runs">
            {(state?.runs ?? []).map((run) => (
              <li key={run.run_id}>
                <button type="button" className="runlink" onClick={() => setActiveRun(run)}>
                  <span>{stateLabel(run)}</span>
                  <small>{describeAction(run)}</small>
                </button>
              </li>
            ))}
            {(state?.runs ?? []).length === 0 ? <li className="muted">尚无任务。</li> : null}
          </ul>
          <div className="memory" data-testid="memory-area">
            <p className="section-label">主人反馈与长期记忆</p>
            <p className="memory-backend" data-testid="memory-backend">
              长期记忆：
              {(state?.feedback ?? []).some((f) => f.memory_status === 'available')
                ? 'AgentCore（生命周期显示可检索）'
                : state?.memory === 'agentcore'
                  ? MEMORY_BACKEND_LABELS.agentcore
                  : '未实现（无 AWS 账号）'}
              {state?.conversation_id ? ` · 当前会话 ${state.conversation_id.slice(0, 8)}…` : ''}
            </p>
            <form className="feedback-form" onSubmit={submitFeedback}>
              <label htmlFor="feedback-text">记录一条主人观察（归因为主人，非模型推断）</label>
              <textarea
                id="feedback-text"
                data-testid="feedback-text"
                value={feedbackText}
                maxLength={500}
                rows={2}
                disabled={busy || !canAct}
                onChange={(e) => setFeedbackText(e.target.value)}
              />
              <label htmlFor="feedback-scope">范围</label>
              <select
                id="feedback-scope"
                data-testid="feedback-scope"
                value={feedbackScope}
                disabled={busy || !canAct}
                onChange={(e) => setFeedbackScope(e.target.value as FeedbackScope)}
              >
                <option value="observation">观察（可长期提炼）</option>
                <option value="today_only">仅今天（不成为永久偏好）</option>
              </select>
              <div className="actions">
                <button
                  type="submit"
                  data-testid="submit-feedback"
                  disabled={busy || !canAct || feedbackText.trim().length === 0}
                >
                  保存反馈
                </button>
                <button
                  type="button"
                  data-testid="new-session"
                  onClick={() => void startNewSession()}
                  disabled={busy || !canAct}
                >
                  开启新会话
                </button>
              </div>
            </form>
            <ul className="feedback-list" data-testid="feedback-list">
              {(state?.feedback ?? []).map((item) => (
                <li key={item.feedback_id} data-testid="feedback-item">
                  <span className="tag" data-testid="feedback-status">
                    {MEMORY_STATUS_LABELS[item.memory_status] ?? item.memory_status}
                  </span>
                  <span className="tag">{SCOPE_LABELS[item.scope] ?? item.scope}</span>
                  <p>{item.text}</p>
                </li>
              ))}
              {(state?.feedback ?? []).length === 0 ? (
                <li className="muted" data-testid="feedback-empty">尚无主人反馈。</li>
              ) : null}
            </ul>
            <p className="hint">
              本地「已保存原文」仅表示反馈已存入业务库；未接入 AgentCore 时不会提炼为长期记忆，
              页面也不会谎称记忆检索成功。反馈归因为主人观察，不等同于模型推断的宠物意图。
            </p>
          </div>
        </section>
      </div>

      <section className="demo">
        <button type="button" className="ghost" onClick={() => setDemoOpen((v) => !v)} aria-expanded={demoOpen}>
          {demoOpen ? '收起演示控制区' : '展开演示控制区'}
        </button>
        {demoOpen ? (
          <div className="demo-body">
            <fieldset disabled={busy || !canAct}>
              <legend>注入事件</legend>
              <label htmlFor="room">事件房间</label>
              <select id="room" value={room} onChange={(e) => setRoom(e.target.value as typeof room)}>
                <option value="kitchen">kitchen</option>
                <option value="living_room">living_room</option>
                <option value="unknown">unknown</option>
              </select>
              <label htmlFor="note">事件备注（视为资料，不作为策略输入）</label>
              <input id="note" value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
              <button type="button" onClick={() => sendEvent('food_request', note)}>
                注入自定义吃饭事件
              </button>
            </fieldset>

            <fieldset disabled={busy || !canAct}>
              <legend>修改演示事实</legend>
              <label htmlFor="fact-last-fed">上次喂食距今（分钟，0–1440）</label>
              <input
                id="fact-last-fed"
                type="number"
                min={0}
                max={1440}
                value={factLastFed}
                disabled={clearLastFed}
                onChange={(e) => setFactLastFed(e.target.value)}
              />
              <label htmlFor="clear-last-fed">
                <input
                  id="clear-last-fed"
                  type="checkbox"
                  checked={clearLastFed}
                  onChange={(e) => setClearLastFed(e.target.checked)}
                />
                设为未知（触发信息不足）
              </label>
              <label htmlFor="fact-dispensed">当日已出粮（克）</label>
              <input
                id="fact-dispensed"
                data-testid="fact-dispensed"
                type="number"
                min={0}
                value={factDispensed}
                disabled={clearDispensed}
                onChange={(e) => setFactDispensed(e.target.value)}
              />
              <label htmlFor="clear-dispensed">
                <input
                  id="clear-dispensed"
                  type="checkbox"
                  checked={clearDispensed}
                  onChange={(e) => setClearDispensed(e.target.checked)}
                />
                设为未知（触发信息不足）
              </label>
              <div className="actions">
                <button
                  type="button"
                  data-testid="apply-facts"
                  onClick={() => {
                    const body: DemoFactsIn = {}
                    const clear: DemoFactsIn['clear'] = []
                    if (clearLastFed) clear.push('last_fed_minutes_ago')
                    else if (factLastFed !== '') body.last_fed_minutes_ago = Number(factLastFed)
                    if (clearDispensed) clear.push('daily_dispensed_grams')
                    else if (factDispensed !== '') body.daily_dispensed_grams = Number(factDispensed)
                    if (clear.length > 0) body.clear = clear
                    void applyFacts(body)
                  }}
                >
                  应用事实变更
                </button>
                <button type="button" data-testid="reset-facts" onClick={() => void applyFacts({ reset: true })}>
                  恢复默认事实
                </button>
              </div>
              <p className="hint">
                只能修改这两项事实；日配额、单次上限与最短间隔是硬性限制，不可经演示端点修改。
                变更会递增 facts_version，此前待批准的建议将失效（返回 409）并要求重新确认。
              </p>
            </fieldset>

            <fieldset disabled={busy || !canAct}>
              <legend>注入模拟回执</legend>
              <label htmlFor="device-mode">模拟执行器模式</label>
              <select
                id="device-mode"
                data-testid="device-mode"
                value={state?.device_mode ?? 'succeeded'}
                onChange={(e) => void applyDeviceMode(e.target.value as DeviceMode)}
              >
                <option value="succeeded">succeeded（成功）</option>
                <option value="failed">failed（失败）</option>
                <option value="unknown">unknown（未知）</option>
              </select>
              <p className="hint">
                仅影响之后的新命令，不追溯已记录的回执；保存在进程内，重启后复位为 succeeded。
                执行器始终是模拟对象，不驱动真实硬件。
              </p>
            </fieldset>
          </div>
        ) : null}
      </section>

      <footer>Local prototype · 传感器与执行器均为模拟 · 无云端资源 · 无 AWS 凭据下发</footer>
    </main>
  )
}
