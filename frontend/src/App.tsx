import { t, tf, locale, serverText } from './i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import PetHome from './PetHome'
import WorkspaceIcon from './WorkspaceIcon'
import WorkbenchConcierge from './WorkbenchConcierge'
import './workbench.css'

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
  POLL_TIMEOUT_MS,
  request,
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
// observable in the payloads (a non-null request_id PAIRED with a bedrock
// backend / a real available memory status); config alone (analyzer==='bedrock')
// only ever earns 「已配置」. G8 review: the evidence suffix is a separate
// constant, never a string.replace off the config label, so rewording one site
// cannot silently break the other.
const ANALYZER_CONFIG_LABELS: Record<AnalyzerBackend, string> = {
  inline: '确定性测试后端',
  local_fake: '本地替身（非真实模型）',
  bedrock: 'AWS Bedrock（已配置，未经真实调用验证）',
}

const REAL_CALL_EVIDENCE = '本 run 已有 request id，真实调用已发生'

// G8 review: every label here must avoid the substrings the e2e specs forbid
// (「可检索」/「已检索到记忆」/「真实记忆」/「真实检索」), otherwise an honest
// lifecycle state would either trip those assertions or read as proven retrieval.
const MEMORY_BACKEND_LABELS: Record<'not_implemented' | 'agentcore', string> = {
  not_implemented: '未接入 AgentCore（仅保存本地记录）',
  agentcore: 'AgentCore（已配置，未经真实证据验证）',
}

// Day-5 §4.3: the "extracted" wording is a dedicated constant so the label guard can
// pin it. It deliberately avoids the e2e forbidden substrings and is rendered ONLY
// paired with a real, non-zero AgentCore record count (memory_record_count) -- never
// from configuration or a bare status. The count is appended in dynamic text.
const MEMORY_EXTRACTED_LABEL = 'AgentCore · 已提炼（真实 AgentCore 记录'

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
  processing: '提炼中（尚未完成）',
  available: '服务端上报提炼完成（AgentCore 生命周期；本地未做检索验证）',
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
  return kind === 'dispense_food' ? tf("{0} {1} 克", t(ACTION_LABELS[kind]), grams) : ACTION_LABELS[kind]
}

function stateLabel(run: RunView): string {
  // "failed" covers two different things; tell them apart instead of misleading.
  if (run.state === 'failed') return run.receipt ? '执行失败' : '分析失败'
  return STATE_LABELS[run.state]
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString(locale())
}

function conflictHint(detail: string): string | null {
  const found = CONFLICT_HINTS.find(([code]) => detail.includes(code))
  return found ? found[1] : null
}

function factMinutes(value: number | null | undefined): string {
  return value == null ? '未知' : tf("{0} 分钟", value)
}

function factGrams(value: number | null | undefined, limit: number | undefined): string {
  return value == null ? tf("未知 / {0} 克", limit ?? '—') : tf("{0} / {1} 克", value, limit ?? '—')
}

function workbenchPage() {
  return window.location.hash === '#workbench/history' ? 'history'
    : window.location.hash === '#workbench/settings' ? 'settings'
      : window.location.hash === '#workbench/concierge' ? 'concierge' : 'requests'
}

function waitForPoll(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise(resolve => {
    const finish = () => { window.clearTimeout(timer); signal.removeEventListener('abort', finish); resolve() }
    const timer = window.setTimeout(finish, ms)
    signal.addEventListener('abort', finish, { once: true })
    if (signal.aborted) finish()
  })
}

export default function App() {
  const [homePage, setHomePage] = useState(window.location.hash === '#home')
  const [page, setPage] = useState(workbenchPage)
  useEffect(() => {
    const changed = () => { setHomePage(window.location.hash === '#home'); setPage(workbenchPage()) }
    window.addEventListener('hashchange', changed)
    return () => window.removeEventListener('hashchange', changed)
  }, [])
  const [state, setState] = useState<StateView | null>(null)
  const [authed, setAuthed] = useState(false)
  const [activeRun, setActiveRun] = useState<RunView | null>(null)
  const [busy, setBusy] = useState(false)
  const [polling, setPolling] = useState(false)
  const [acceptedRunId, setAcceptedRunId] = useState<string | null>(null)
  const [awaitingFirstRead, setAwaitingFirstRead] = useState(false)
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
  const requestPendingRef = useRef(false)
  const acceptedRunIdRef = useRef<string | null>(null)
  const firstReadPendingRef = useRef(false)
  const pollGeneration = useRef(0)
  const sessionGeneration = useRef(0)
  const pollController = useRef<AbortController | null>(null)
  const mounted = useRef(true)
  const [runFilter, setRunFilter] = useState('all')
  const [runOrder, setRunOrder] = useState('newest')

  const cancelTracking = useCallback(() => {
    pollGeneration.current++
    pollController.current?.abort()
    pollController.current = null
    pollingRef.current = false
    firstReadPendingRef.current = false
    setPolling(false)
    setAwaitingFirstRead(false)
    setPollDeadline(false)
  }, [])

  const handleError = useCallback((err: unknown) => {
    if (!mounted.current) return
    if (err instanceof ApiError) {
      if (err.status === 401) {
        cancelTracking()
        sessionGeneration.current++
        requestPendingRef.current = false
        acceptedRunIdRef.current = null
        setAcceptedRunId(null)
        setAuthed(false)
        setState(null)
        setActiveRun(null)
        setCanAct(false)
        setError('会话已失效，请重新登录。')
        return
      }
      if (err.status === 403) {
        setCanAct(false)
        setError('操作令牌缺失或失效，请重新登录后再试。')
        return
      }
      setError(tf("请求失败（{0}）：{1}", err.status, err.message))
      return
    }
    setError('无法连接本地后端，请确认服务已启动。')
  }, [cancelTracking])

  const refresh = useCallback(async (): Promise<StateView | null> => {
    const session = sessionGeneration.current
    try {
      const snapshot = await getState()
      if (!mounted.current || session !== sessionGeneration.current) return null
      if (snapshot.runs.some(run => run.run_id === acceptedRunIdRef.current && isSettled(run.state))) {
        acceptedRunIdRef.current = null
        setAcceptedRunId(null)
      }
      setState(snapshot)
      setAuthed(true)
      setError(null)
      return snapshot
    } catch (err) {
      if (!mounted.current || session !== sessionGeneration.current) return null
      handleError(err)
      return null
    }
  }, [handleError])

  useEffect(() => {
    mounted.current = true
    void refresh()
    return () => {
      mounted.current = false
      sessionGeneration.current++
      pollGeneration.current++
      pollController.current?.abort()
      pollingRef.current = false
      firstReadPendingRef.current = false
      acceptedRunIdRef.current = null
    }
  }, [refresh])

  // Follow a run until the backend settles it. The client never decides the
  // verdict itself: on deadline it says "still working", not "failed".
  const trackRun = useCallback(
    async (runId: string) => {
      if (!mounted.current) return
      cancelTracking()
      const generation = pollGeneration.current
      const session = sessionGeneration.current
      const controller = new AbortController()
      pollController.current = controller
      const current = () => mounted.current && !controller.signal.aborted && generation === pollGeneration.current && session === sessionGeneration.current
      pollingRef.current = true
      firstReadPendingRef.current = true
      setPolling(true)
      setAwaitingFirstRead(true)
      setPollDeadline(false)
      setElapsed(0)
      const startedAt = Date.now()
      const timer = window.setInterval(
        () => { if (current()) setElapsed(Math.round((Date.now() - startedAt) / 1000)) },
        500,
      )
      // This deadline must also fire while fetch itself is stuck. Aborting a
      // read says nothing about the backend verdict or its accepted request.
      const deadline = window.setTimeout(() => {
        if (!current()) return
        setPollDeadline(true)
        controller.abort()
      }, POLL_TIMEOUT_MS)
      try {
        while (current()) {
          const run = await request<RunView>(`/api/runs/${encodeURIComponent(runId)}`, { signal: controller.signal })
          if (!current()) return
          firstReadPendingRef.current = false
          setAwaitingFirstRead(false)
          setActiveRun(run)
          setState(previous => previous ? { ...previous, runs: [run, ...previous.runs.filter(item => item.run_id !== runId)].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)) } : previous)
          if (isSettled(run.state)) {
            if (acceptedRunIdRef.current === runId) {
              acceptedRunIdRef.current = null
              setAcceptedRunId(null)
            }
            break
          }
          await waitForPoll(Date.now() - startedAt < 15_000 ? 2000 : 5000, controller.signal)
        }
        // The stored RunView has settled. A separate facts refresh must not
        // extend ownership of the run tracker or block the next request.
        if (current()) void refresh()
      } catch (err) {
        if (current()) handleError(err)
      } finally {
        window.clearInterval(timer)
        window.clearTimeout(deadline)
        if (generation === pollGeneration.current && session === sessionGeneration.current && mounted.current) {
          setPolling(false)
          pollingRef.current = false
          firstReadPendingRef.current = false
          setAwaitingFirstRead(false)
          pollController.current = null
          setCanAct(hasCsrf())
        }
      }
    },
    [cancelTracking, handleError, refresh],
  )

  // After a (re)load, surface the most recent run and keep following it if the
  // backend has not settled it yet.
  useEffect(() => {
    if (activeRun === null && !acceptedRunIdRef.current && !pollingRef.current && !requestPendingRef.current && state && state.runs.length > 0) {
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
    cancelTracking()
    sessionGeneration.current++
    requestPendingRef.current = false
    acceptedRunIdRef.current = null
    setAcceptedRunId(null)
    setBusy(true)
    setAuthed(false)
    setState(null)
    setActiveRun(null)
    setCanAct(false)
    setError(null)
    setNotice(null)
    await logout()
    if (mounted.current) setBusy(false)
  }

  async function sendEvent(kind: 'food_request' | 'attention_request', customNote = '') {
    // One request owns the tracker at a time. Simulation settings stay usable;
    // a second event must not be created and silently lose its UI tracking.
    if (requestPendingRef.current || acceptedRunIdRef.current || pollingRef.current || busy || !canAct || state?.runs.some(run => !isSettled(run.state))) return
    requestPendingRef.current = true
    const session = sessionGeneration.current
    window.location.hash = '#workbench'
    setBusy(true)
    setActiveRun(null)
    setError(null)
    setNotice(null)
    setPollDeadline(false)
    try {
      const accepted = await postEvent(kind, room, customNote)
      if (!mounted.current || session !== sessionGeneration.current) return
      // Acknowledgement establishes request ownership before the first GET;
      // do not manufacture a RunView or infer that cancelling a read finishes it.
      acceptedRunIdRef.current = accepted.run_id
      setAcceptedRunId(accepted.run_id)
      // Release the buttons at once: analysis may take seconds and the demo
      // controls must stay usable while it runs.
      setBusy(false)
      setCanAct(hasCsrf())
      await trackRun(accepted.run_id)
    } catch (err) {
      if (mounted.current && session === sessionGeneration.current) {
        handleError(err)
        setBusy(false)
        setCanAct(hasCsrf())
      }
    } finally {
      if (session === sessionGeneration.current) requestPendingRef.current = false
    }
  }

  function selectRun(run: RunView) {
    if (busy || firstReadPendingRef.current) return
    cancelTracking()
    setActiveRun(run)
    setError(null)
    setNotice(null)
    void trackRun(run.run_id)
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
        setNotice(conflictHint(err.message) ?? tf("操作被拒绝（409）：{0}", err.message))
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
      setNotice(tf("模拟执行器模式已设为 {0}，仅影响之后的新命令；本进程内有效，重启后复位。", mode))
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
        tf("已开启新会话（conversation {0}…）；宠物记忆、事实与登录均保留。", result.conversation_id.slice(0, 8)),
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
      <main className="wb-login">
        <header className="hero">
          <div>
            <p className="eyebrow">{t("PET CARE AGENT · 演示登录")}</p>
            <h1>PawTwin</h1>
            <p className="lede">{t("照护请求需经主人审批。登录后查看 Mochi 的实时状态与建议。")}</p>
          </div>
        </header>
        <section className="panel login">
          <form onSubmit={onLogin}>
            <label htmlFor="passphrase">{t("演示口令")}</label>
            <input
              id="passphrase"
              type="password"
              aria-describedby="demo-passphrase-hint"
              value={passphrase}
              autoComplete="current-password"
              onChange={(e) => setPassphrase(e.target.value)}
            />
            <p id="demo-passphrase-hint" className="wb-login-hint">
              {t('本地默认演示口令：', 'Default local demo passphrase: ')}<code>local-demo-passphrase</code>
              <span>{t('若已设置自定义演示口令，请使用配置后的口令。', 'If a custom demo passphrase is configured, use that value instead.')}</span>
            </p>
            <button type="submit" disabled={busy || passphrase.length === 0}>{t("登录演示")}</button>
          </form>
          {t(error ? <p className="error" role="alert">{t(error)}</p> : null)}
          <p className="hint">{t("未授权时不会读取业务数据、触发模型或批准任务。")}</p>
          <a href="#app">{t("进入家庭 App · 独立账号")}</a>
        </section>
      </main>
    )
  }

  if (homePage) return <PetHome onLogout={() => void onLogout()} />

  const facts = state?.facts
  const awaiting = activeRun?.state === 'awaiting_approval'
  // §4.3: the extracted-memory label is evidence-driven -- it renders ONLY when the
  // backend reports a non-zero count of real AgentCore records (which the repository
  // invariant ties to an 'available' status). Locally the count is always 0, so the
  // honest '未接入 AgentCore（仅保存本地记录）' label shows instead.
  const extractedRecordCount = (state?.feedback ?? []).reduce(
    (total, item) =>
      item.memory_status === 'available' ? total + item.memory_record_count : total,
    0,
  )

  const requestDisabled = busy || polling || !!acceptedRunId || !canAct || !!state?.runs.some(run => !isSettled(run.state))
  const pageTitle = page === 'history' ? '运行记录' : page === 'settings' ? '演示设置' : page === 'concierge' ? '宠物管家' : '请求与审批'
  const visibleRuns = (state?.runs ?? []).filter(run => page !== 'history' || runFilter === 'all' || run.state === runFilter)
    .slice().sort((a, b) => runOrder === 'oldest' ? Date.parse(a.created_at) - Date.parse(b.created_at) : Date.parse(b.created_at) - Date.parse(a.created_at))
  const runDetails = (
        <section className="panel wb-run-detail" aria-label={t("建议与确认")}>
          <div className="wb-card-heading"><div><p className="section-label">{t("建议与确认")}</p><h2>{t("本次请求")}</h2></div><span className="wb-soft-badge">{t("需主人明确审批")}</span></div>
          {t(activeRun ? (
            <>
              <div className="wb-run-meta"><code data-testid="active-run-id">{t(activeRun.run_id)}</code><time dateTime={activeRun.created_at}>{t(formatTime(activeRun.created_at))}</time></div>
              <p className="state" data-testid="run-status">
                {t(stateLabel(activeRun))}
              </p>
              {t(polling ? (
                <p className="muted" data-testid="run-elapsed">{t("正在等待后端结论，已等待 ")}{t(elapsed)}{t(" 秒…")}</p>
              ) : null)}
              {t(activeRun.policy_reason && activeRun.policy_reason !== 'ALLOWED' ? (
                <p className="reason" data-testid="policy-reason">{t("策略结论：")}{t(POLICY_LABELS[activeRun.policy_reason] ?? activeRun.policy_reason)}
                </p>
              ) : null)}
              {t(activeRun.failure_reason ? (
                <p className="reason error" data-testid="failure-reason">{t("失败原因：")}{t(FAILURE_LABELS[activeRun.failure_reason] ?? activeRun.failure_reason)}
                </p>
              ) : null)}
              {t(activeRun.proposal ? (
                <div className="proposal">
                  <p className="action" data-testid="proposal-action">{t(describeAction(activeRun))}</p>
                  <p className="explanation">{serverText(activeRun.proposal.explanation)}</p>
                </div>
              ) : (
                <p className="muted">{t("当前任务没有可执行的建议。")}</p>
              ))}
              <details className="wb-evidence-details"><summary>{t("查询证据与调用记录")}</summary>
              {t(activeRun.evidence.length > 0 ? (
                <div className="evidence">
                  <p className="section-label">{t("真实查询证据")}</p>
                  <ul className="evidence-list" data-testid="evidence-list">
                    {t(activeRun.evidence.map((item) => (
                      <li key={item.evidence_id} data-testid="evidence-item">
                        <strong>{t(TOOL_LABELS[item.tool] ?? item.tool)}</strong>
                        <span className="tag">{t(SOURCE_LABELS[item.source] ?? item.source)}</span>
                        <time dateTime={item.retrieved_at}>{t(formatTime(item.retrieved_at))}</time>
                        <code>{t(item.evidence_id)}</code>
                        <p>{t(item.summary)}</p>
                      </li>
                    )))}
                  </ul>
                </div>
              ) : (
                <p className="muted" data-testid="evidence-empty">{t("本次分析没有检索记录（确定性测试后端不产生证据）。")}</p>
              ))}
              {t(activeRun.telemetry ? (
                <dl className="telemetry" data-testid="telemetry">
                  <div><dt>{t("分析后端")}</dt><dd>{t(activeRun.telemetry.request_id && activeRun.telemetry.backend === 'bedrock' ? tf("AWS Bedrock（真实模型，{0}）", t(REAL_CALL_EVIDENCE)) : ANALYZER_CONFIG_LABELS[activeRun.telemetry.backend])}</dd></div>
                  <div><dt>{t("模型调用")}</dt><dd>{t(activeRun.telemetry.model_calls)}{t(" 次（上限 4）")}</dd></div>
                  <div><dt>{t("输出 tokens")}</dt><dd>{t(activeRun.telemetry.output_tokens)}{t("（上限 800）")}</dd></div>
                  <div><dt>{t("耗时")}</dt><dd>{t(activeRun.telemetry.duration_ms)} ms</dd></div>
                  <div>
                    <dt>{t("云端 request id")}</dt>
                    <dd>{t(activeRun.telemetry.request_id ?? '无（未发生真实云调用）')}</dd>
                  </div>
                </dl>
              ) : null)}
              <dl className="wb-version"><div><dt>{t("事实版本")}</dt><dd>{t(activeRun.facts_version)}</dd></div><div><dt>{t("建议版本")}</dt><dd>{t(activeRun.proposal_version)}</dd></div><div><dt>{t("动作校验摘要")}</dt><dd><code>{t(activeRun.action_digest ?? "无可批准动作")}</code></dd></div></dl>
              </details>
              {t(awaiting && <p className="wb-approval-note">{t("请核对本次动作与上方额度。")}{t(activeRun.expires_at ? tf("建议有效至 {0}；", formatTime(activeRun.expires_at)) : "")}{t("批准仅适用于本次建议，事实变化后必须重新确认。")}</p>)}
              {t(activeRun.receipt ? (
                <p className="receipt" data-testid="receipt">
                  {t(activeRun.receipt.status === 'succeeded'
                    ? '模拟执行成功'
                    : activeRun.receipt.status === 'failed'
                      ? '模拟执行失败'
                      : '执行状态未知')}
                  （simulated={t(String(activeRun.receipt.simulated))}）
                </p>
              ) : null)}
              <div className="actions">
                <button
                  type="button"
                  className="primary"
                  data-testid="approve"
                  onClick={() => decide('approve')}
                  disabled={busy || polling || !awaiting || !canAct}
                >{t("批准本次动作")}</button>
                <button
                  type="button"
                  className="danger"
                  data-testid="decline"
                  onClick={() => decide('decline')}
                  disabled={busy || polling || !awaiting || !canAct}
                >{t("拒绝本次动作")}</button>
              </div>
            </>
          ) : (
            <div className="wb-empty"><WorkspaceIcon name="care" /><h3>{t(acceptedRunId ? '请求已接收' : '先发起一项请求')}</h3><p>{t(acceptedRunId ? '正在读取这项请求的后端状态；当前还没有可供审批的建议。可刷新状态重新查询。' : '后台分析与硬性策略检查之后，有可执行建议才进入主人审批。当前没有动作被执行。')}</p></div>
          ))}
        </section>
  )
  const memoryPanel = <section className="panel wb-memory" aria-label={t("主人反馈与会话")}><h2>{t("主人反馈与会话")}</h2><p className="muted">{t("保存观察原文或开始新会话；这不会改变喂食额度与审批权限。")}</p>
          <div className="memory" data-testid="memory-area">
            <p className="section-label">{t("主人反馈与长期记忆")}</p>
            <p className="memory-backend" data-testid="memory-backend">{t("长期记忆：")}{t(extractedRecordCount > 0
                ? tf("{0} {1} 条）", t(MEMORY_EXTRACTED_LABEL), extractedRecordCount)
                : state?.memory === 'agentcore'
                  ? MEMORY_BACKEND_LABELS.agentcore
                  : '未接入 AgentCore（仅保存本地记录）')}
              {t(state?.conversation_id ? tf(" · 当前会话 {0}…", state.conversation_id.slice(0, 8)) : '')}
            </p>
            <form className="feedback-form" onSubmit={submitFeedback}>
              <label htmlFor="feedback-text">{t("记录一条主人观察（归因为主人，非模型推断）")}</label>
              <textarea
                id="feedback-text"
                data-testid="feedback-text"
                value={feedbackText}
                maxLength={500}
                rows={2}
                disabled={busy || !canAct}
                onChange={(e) => setFeedbackText(e.target.value)}
              />
              <label htmlFor="feedback-scope">{t("范围")}</label>
              <select
                id="feedback-scope"
                data-testid="feedback-scope"
                value={feedbackScope}
                disabled={busy || !canAct}
                onChange={(e) => setFeedbackScope(e.target.value as FeedbackScope)}
              >
                <option value="observation">{t("观察（可长期提炼）")}</option>
                <option value="today_only">{t("仅今天（不成为永久偏好）")}</option>
              </select>
              <div className="actions">
                <button
                  type="submit"
                  data-testid="submit-feedback"
                  disabled={busy || !canAct || feedbackText.trim().length === 0}
                >{t("保存反馈")}</button>
                <button
                  type="button"
                  data-testid="new-session"
                  onClick={() => void startNewSession()}
                  disabled={busy || !canAct}
                >{t("开启新会话")}</button>
              </div>
            </form>
            <ul className="feedback-list" data-testid="feedback-list">
              {t((state?.feedback ?? []).map((item) => (
                <li key={item.feedback_id} data-testid="feedback-item">
                  <span className="tag" data-testid="feedback-status">
                    {t(MEMORY_STATUS_LABELS[item.memory_status] ?? item.memory_status)}
                  </span>
                  <span className="tag">{t(SCOPE_LABELS[item.scope] ?? item.scope)}</span>
                  <p>{item.text}</p>
                </li>
              )))}
              {t((state?.feedback ?? []).length === 0 ? (
                <li className="muted" data-testid="feedback-empty">{t("尚无主人反馈。")}</li>
              ) : null)}
            </ul>
            <p className="hint">{t("本地「已保存原文」仅表示反馈已存入业务库；未接入 AgentCore 时不会提炼为长期记忆， 页面也不会谎称记忆检索成功。反馈归因为主人观察，不等同于模型推断的宠物意图。")}</p>
          </div>
  </section>
  const demoControls = (
      <section className="demo panel wb-demo">
        {t(page !== "settings" && <button type="button" className="ghost" onClick={() => setDemoOpen((v) => !v)} aria-expanded={demoOpen}>
          {t(demoOpen ? '收起演示控制区' : '展开演示控制区')}
        </button>)}
        {t(page === "settings" && <div className="wb-card-heading"><div><p className="section-label">SIMULATION SETTINGS</p><h2>{t("模拟事实与设备")}</h2></div><span className="wb-soft-badge">{t("演示控制")}</span></div>)}
        {t((demoOpen || page === "settings") ? (
          <div className="demo-body">
            <fieldset disabled={busy || !canAct}>
              <legend>{t("注入事件")}</legend>
              <label htmlFor="room">{t("事件房间")}</label>
              <select id="room" value={room} onChange={(e) => setRoom(e.target.value as typeof room)}>
                <option value="kitchen">kitchen</option>
                <option value="living_room">living_room</option>
                <option value="unknown">unknown</option>
              </select>
              <label htmlFor="note">{t("事件备注（视为资料，不作为策略输入）")}</label>
              <input id="note" value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
              <button type="button" disabled={requestDisabled} onClick={() => sendEvent('food_request', note)}>{t("注入自定义吃饭事件")}</button>
            </fieldset>

            <fieldset disabled={busy || !canAct}>
              <legend>{t("修改演示事实")}</legend>
              <label htmlFor="fact-last-fed">{t("上次喂食距今（分钟，0–1440）")}</label>
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
                />{t("设为未知（触发信息不足）")}</label>
              <label htmlFor="fact-dispensed">{t("当日已出粮（克）")}</label>
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
                />{t("设为未知（触发信息不足）")}</label>
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
                >{t("应用事实变更")}</button>
                <button type="button" data-testid="reset-facts" onClick={() => void applyFacts({ reset: true })}>{t("恢复默认事实")}</button>
              </div>
              <p className="hint">{t("只能修改这两项事实；日配额、单次上限与最短间隔是硬性限制，不可经演示端点修改。 变更会递增 facts_version，此前待批准的建议将失效（返回 409）并要求重新确认。")}</p>
            </fieldset>

            <fieldset disabled={busy || !canAct}>
              <legend>{t("注入模拟回执")}</legend>
              <label htmlFor="device-mode">{t("模拟执行器模式")}</label>
              <select
                id="device-mode"
                data-testid="device-mode"
                value={state?.device_mode ?? 'succeeded'}
                onChange={(e) => void applyDeviceMode(e.target.value as DeviceMode)}
              >
                <option value="succeeded">{t("succeeded（成功）")}</option>
                <option value="failed">{t("failed（失败）")}</option>
                <option value="unknown">{t("unknown（未知）")}</option>
              </select>
              <p className="hint">{t("仅影响之后的新命令，不追溯已记录的回执；保存在进程内，重启后复位为 succeeded。 执行器始终是模拟对象，不驱动真实硬件。")}</p>
            </fieldset>
          </div>
        ) : null)}
      </section>
  )
  const runList = <section className="panel wb-records" aria-label={t("运行记录列表")}>
    <div className="wb-card-heading"><div><p className="section-label">RUN HISTORY</p><h2>{t(page === 'history' ? '全部运行' : '最近运行')}</h2></div>{t(page !== 'history' && <a href="#workbench/history">{t("查看全部 ")}<WorkspaceIcon name="arrow" /></a>)}</div>
    {t(page === 'history' && <div className="wb-history-filters"><label>{t("运行状态筛选")}<select value={runFilter} onChange={event => setRunFilter(event.target.value)}><option value="all">{t("全部状态")}</option>{t(Object.entries(STATE_LABELS).map(([value, label]) => <option key={value} value={value}>{t(label)}</option>))}</select></label><label>{t("时间排序")}<select value={runOrder} onChange={event => setRunOrder(event.target.value)}><option value="newest">{t("最新优先")}</option><option value="oldest">{t("最早优先")}</option></select></label></div>)}
    <ul className="runs" data-testid="runs">
      {t((page === 'history' ? visibleRuns : visibleRuns.slice(0, 3)).map(run => <li key={run.run_id}><button type="button" className="runlink" data-run-id={run.run_id} aria-pressed={activeRun?.run_id === run.run_id} disabled={busy || awaitingFirstRead} onClick={() => selectRun(run)}><span><strong>{t(stateLabel(run))}</strong><small>{t(describeAction(run))}</small></span><time dateTime={run.created_at}>{t(formatTime(run.created_at))}</time></button></li>))}
      {t(visibleRuns.length === 0 && <li className="wb-empty"><strong>{t(runFilter === 'all' ? '还没有运行记录' : '没有匹配的运行')}</strong><p>{t("运行状态与时间来自后端记录；可切换筛选或发起新的模拟请求。")}</p></li>)}
    </ul>
    {t(page === 'history' && <p className="hint">{t(awaitingFirstRead ? '正在读取本次请求的首个状态，读取结束后可切换记录。' : '点选一条记录重新核对后端状态。选择记录不会触发新动作。')}</p>)}
  </section>

  return (
    <main className="wb-workbench" data-page={page}>
      <aside className="wb-sidebar"><p className="wb-sidebar-label">{t("模拟照护空间")}</p><nav aria-label={t("工作台导航")}>{t(([
        ['requests', '#workbench', '请求与审批', 'care'],
        ['history', '#workbench/history', '运行记录', 'history'],
        ['settings', '#workbench/settings', '演示设置', 'settings'],
        ['concierge', '#workbench/concierge', '宠物管家', 'twin'],
      ] as const).map(([key, href, label, icon]) => <a key={key} href={href} aria-current={page === key ? 'page' : undefined}><WorkspaceIcon name={icon} /><span>{t(label)}</span></a>))}</nav><div className="wb-sidebar-foot"><span className="wb-pet-avatar" aria-hidden="true">🐱</span><strong>Mochi</strong><p>{t("虚构宠物 · 单一模拟执行器")}</p><a href="#home">{t("打开原宠物小屋 ")}<WorkspaceIcon name="arrow" /></a></div></aside>
      <div className="wb-content">
      <header className="wb-heading">
        <div><p className="eyebrow">{t("PAWTWIN · 照护工作台")}</p><h1>{t(pageTitle)}</h1><p className="lede">{page === 'concierge' ? t('从一句自然的提问，看见宠物资料如何帮助照护。', 'See how pet context supports care, starting with a natural question.') : t(page === 'history' ? '回看每次请求的状态、依据与模拟回执。' : page === 'settings' ? '按场景核对事实，调整模拟条件与主人观察。' : '从当前事实出发，逐次确认可执行的照护建议。')}</p></div>
        <div className="connection"><span aria-hidden="true" /><div><strong data-testid="mode-badge">{t(state ? tf("{0} · {1}", state.mode.toUpperCase(), t(state.aws_connected ? 'AWS 已连接' : 'AWS 未连接')) : '加载中')}</strong><small>{t("状态来源 /api/state")}</small></div><button type="button" className="ghost" onClick={() => void onLogout()} disabled={busy}>{t("退出")}</button></div>
      </header>
      <section className="truth-strip" aria-label={t("实现边界")}><div><strong>{t("模拟传感器事件")}</strong><span>{t("事件来源固定为 simulator")}</span></div><div><strong>{t("模拟执行器")}</strong><span>{t("回执 simulated，不驱动真实硬件")}</span></div><div><strong>{t("项圈为概念设计")}</strong><span>{t("当前没有设备连接")}</span></div><div><strong>{t(state?.aws_connected ? 'AWS 已连接' : 'AWS 未连接')}</strong><span>{t("本地替身与云端状态分别标注")}</span></div></section>
      {t(state ? (
        <p className="impl-labels" data-testid="impl-labels">
          <span>{t("分析器：")}{t(activeRun?.telemetry?.request_id && activeRun.telemetry.backend === 'bedrock' ? tf("AWS Bedrock（真实模型，{0}）", t(REAL_CALL_EVIDENCE)) : ANALYZER_CONFIG_LABELS[state.analyzer])}</span>
          <span>{t("存储：")}{t(state.storage === 'dynamodb' ? (state.aws_connected ? 'DynamoDB（真实表，启动探活通过）' : 'DynamoDB（已配置，未经云端验证）') : 'SQLite（本地实现，未经云端验证）')}</span>
          <span>{t("长期记忆：")}{t(extractedRecordCount > 0 ? tf("{0} {1} 条）", t(MEMORY_EXTRACTED_LABEL), extractedRecordCount) : MEMORY_BACKEND_LABELS[state.memory])}</span>
        </p>
      ) : null)}


      {t(error ? <p className="error" role="alert">{t(error)}</p> : null)}
      {t(notice ? <p className="notice" data-testid="notice" role="status">{t(notice)}</p> : null)}
      {t(pollDeadline ? (
        <p className="warn" data-testid="poll-deadline">{t("已超过客户端等待上限（75 秒），任务仍在后端处理。页面不会自行判定失败，请刷新查看最新状态。")}</p>
      ) : null)}
      {t(!canAct ? (
        <p className="warn" data-testid="reauth-hint">{t("会话可查看，但执行批准/拒绝需要操作令牌。请重新登录以继续操作。")}</p>
      ) : null)}

      {page !== 'concierge' && <section className="panel wb-facts" aria-label={t("当前宠物事实")}>
        <div className="wb-card-heading"><div><p className="section-label">CURRENT FACTS</p><h2>{t("Mochi 的当前事实")}</h2></div><button type="button" className="ghost" disabled={busy} onClick={() => { const runId = acceptedRunIdRef.current ?? activeRun?.run_id; void refresh(); if (runId && !pollingRef.current) void trackRun(runId) }}>{t("刷新状态")}</button></div>
        <dl className="facts" data-testid="facts"><div><dt>{t("上次喂食距今")}</dt><dd>{t(factMinutes(facts?.last_fed_minutes_ago))}</dd></div><div><dt>{t("当日已出粮")}</dt><dd>{t(factGrams(facts?.daily_dispensed_grams, facts?.daily_limit_grams))}</dd></div><div><dt>{t("单次上限")}</dt><dd>{t(facts?.single_serving_grams ?? '—')}{t(" 克")}</dd></div><div><dt>{t("最短间隔")}</dt><dd>{t(facts?.minimum_interval_minutes ?? '—')}{t(" 分钟")}</dd></div></dl>
        <p className="hint">{t("来源：应用存储 · 未知事实保持未知 · 出粮不代表实际摄入 · 硬性限额不能由批准或演示设置提高")}</p>
      </section>}
      {t(page === 'requests' && <section className="panel wb-request" aria-label={t("宠物与请求")}><div className="wb-card-heading"><div><p className="section-label">ONE REQUEST AT A TIME</p><h2>{t("发起一次模拟请求")}</h2></div><span className="wb-soft-badge">{t("仅 Mochi")}</span></div><p>{t("请求进入分析和策略检查。有可执行建议时，你仍需明确批准；本页为软件测试演示，非喂养建议。")}</p><div className="wb-flow" aria-label={t("请求流程")}><span>{t("01 请求与分析")}</span><WorkspaceIcon name="arrow" /><span>{t("02 主人确认")}</span><WorkspaceIcon name="arrow" /><span>{t("03 模拟回执")}</span></div><div className="actions"><button type="button" onClick={() => void sendEvent('food_request')} disabled={requestDisabled}>{t("发送吃饭请求")}</button><button type="button" className="ghost" onClick={() => void sendEvent('attention_request')} disabled={requestDisabled}>{t("发送互动请求")}</button></div>{t((polling || acceptedRunId || state?.runs.some(run => !isSettled(run.state))) && <p className="hint">{t("还有请求正在处理，结束后可发起下一次；演示事实与回执设置仍可修改。")}<a href="#workbench/history">{t("查看运行记录")}</a></p>)}</section>)}
      {page === 'concierge' ? <WorkbenchConcierge /> : t(page !== 'settings' ? <><div className={`wb-run-layout wb-run-layout--${page}`}>{t(page === 'history' ? <>{t(runList)}{t(runDetails)}</> : <>{t(runDetails)}{t(runList)}</>)}</div>{t(page === 'requests' && demoControls)}</> : <div className="wb-settings-layout">{t(demoControls)}{t(memoryPanel)}</div>)}
      <footer>{t("Local prototype · 传感器与执行器均为模拟 · 本地演示身份 · 非家庭账号 · 真实云端能力以证据为准")}</footer>
      </div>
    </main>
  )
}
