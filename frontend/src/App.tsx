import { useCallback, useEffect, useState } from 'react'

import {
  ApiError,
  type RunState,
  type RunView,
  type StateView,
  getState,
  hasCsrf,
  login,
  logout,
  pollRun,
  postApproval,
  postEvent,
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

function describeAction(run: RunView | null): string {
  if (!run?.proposal) return '暂无建议'
  const { kind, grams } = run.proposal.action
  return kind === 'dispense_food' ? `${ACTION_LABELS[kind]} ${grams} 克` : ACTION_LABELS[kind]
}

export default function App() {
  const [state, setState] = useState<StateView | null>(null)
  const [authed, setAuthed] = useState(false)
  const [activeRun, setActiveRun] = useState<RunView | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [passphrase, setPassphrase] = useState('')
  const [canAct, setCanAct] = useState(hasCsrf())
  const [demoOpen, setDemoOpen] = useState(false)
  const [note, setNote] = useState('')
  const [room, setRoom] = useState<'kitchen' | 'living_room' | 'unknown'>('kitchen')

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

  // After a (re)load, surface the most recent run so its durable state is visible.
  useEffect(() => {
    if (activeRun === null && state && state.runs.length > 0) setActiveRun(state.runs[0])
  }, [state, activeRun])

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
    try {
      const accepted = await postEvent(kind, room, customNote)
      const run = await pollRun(accepted.run_id, setActiveRun)
      setActiveRun(run)
      await refresh()
    } catch (err) {
      handleError(err)
    } finally {
      setBusy(false)
      setCanAct(hasCsrf())
    }
  }

  async function decide(decision: 'approve' | 'decline') {
    if (!activeRun || activeRun.action_digest === null) return
    setBusy(true)
    setError(null)
    try {
      const run = await postApproval(activeRun.run_id, {
        decision,
        proposal_version: activeRun.proposal_version,
        action_digest: activeRun.action_digest,
      })
      setActiveRun(run)
      await refresh()
    } catch (err) {
      handleError(err)
      await refresh()
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

      {error ? <p className="error" role="alert">{error}</p> : null}
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
            <div><dt>上次喂食距今</dt><dd>{facts?.last_fed_minutes_ago ?? '—'} 分钟</dd></div>
            <div><dt>当日已出粮</dt><dd>{facts?.daily_dispensed_grams ?? '—'} / {facts?.daily_limit_grams ?? '—'} 克</dd></div>
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
                {STATE_LABELS[activeRun.state]}
              </p>
              {activeRun.proposal ? (
                <div className="proposal">
                  <p className="action" data-testid="proposal-action">{describeAction(activeRun)}</p>
                  <p className="explanation">{activeRun.proposal.explanation}</p>
                  <p className="evidence">
                    依据：{activeRun.proposal.evidence_ids.join('、') || '无'}
                  </p>
                </div>
              ) : (
                <p className="muted">当前任务没有可执行的建议。</p>
              )}
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
                  <span>{STATE_LABELS[run.state]}</span>
                  <small>{describeAction(run)}</small>
                </button>
              </li>
            ))}
            {(state?.runs ?? []).length === 0 ? <li className="muted">尚无任务。</li> : null}
          </ul>
          <p className="placeholder" data-testid="memory-placeholder">
            长期记忆与主人反馈检索将于 Day-3 接入（AgentCore）。当前不展示任何伪造记忆。
          </p>
        </section>
      </div>

      <section className="demo">
        <button type="button" className="ghost" onClick={() => setDemoOpen((v) => !v)} aria-expanded={demoOpen}>
          {demoOpen ? '收起演示控制区' : '展开演示控制区'}
        </button>
        {demoOpen ? (
          <div className="demo-body">
            <label htmlFor="room">事件房间</label>
            <select id="room" value={room} onChange={(e) => setRoom(e.target.value as typeof room)}>
              <option value="kitchen">kitchen</option>
              <option value="living_room">living_room</option>
              <option value="unknown">unknown</option>
            </select>
            <label htmlFor="note">事件备注（视为资料，不作为策略输入）</label>
            <input id="note" value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
            <button type="button" onClick={() => sendEvent('food_request', note)} disabled={busy || !canAct}>
              注入自定义吃饭事件
            </button>
            <p className="hint">现场修改喂食事实与注入设备回执（成功/失败/未知）将于 Day-2 接入。</p>
          </div>
        ) : null}
      </section>

      <footer>Local prototype · 传感器与执行器均为模拟 · 无云端资源 · 无 AWS 凭据下发</footer>
    </main>
  )
}
