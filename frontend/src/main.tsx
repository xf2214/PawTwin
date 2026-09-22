import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

import './styles.css'

type BootstrapInfo = {
  project: string
  stage: 'scaffold'
  mode: 'local' | 'aws'
  aws_connected: boolean
}

const plannedAreas = [
  { title: '事件台', button: '进入事件台', description: '接收模拟传感器事件，形成可追溯的照护请求。' },
  { title: '审批台', button: '进入审批台', description: '主人确认具体动作参数后，才允许执行。' },
  { title: '长期记忆', button: '查看长期记忆', description: '未来接入个体历史，让证据真正改变建议。' },
]

function App() {
  const [bootstrap, setBootstrap] = useState<BootstrapInfo | null>(null)
  const [connectionError, setConnectionError] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/bootstrap', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Bootstrap request failed: ${response.status}`)
        return response.json() as Promise<BootstrapInfo>
      })
      .then(setBootstrap)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setConnectionError(true)
      })

    return () => controller.abort()
  }, [])

  const connectionLabel = connectionError
    ? '本地骨架连接失败'
    : bootstrap
      ? '本地骨架已连接'
      : '正在连接本地骨架'

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">PET CARE AGENT · INITIALIZATION</p>
          <h1>PawTwin</h1>
          <p className="lede">一个以个体历史和主人审批为核心的宠物照护 Agent。</p>
        </div>
        <div className={`connection ${connectionError ? 'connection--error' : ''}`}>
          <span aria-hidden="true" />
          <div>
            <strong>{connectionLabel}</strong>
            <small>
              {bootstrap
                ? `${bootstrap.mode.toUpperCase()} · ${bootstrap.stage}`
                : 'API /api/bootstrap'}
            </small>
          </div>
        </div>
      </header>

      <section className="truth-strip" aria-label="实现边界">
        <div><strong>模拟传感器事件</strong><span>持续保留明确标签</span></div>
        <div><strong>模拟执行器</strong><span>不会伪装为真实硬件</span></div>
        <div><strong>项圈为概念设计</strong><span>当前没有设备连接</span></div>
        <div><strong>AWS 未连接</strong><span>{bootstrap?.aws_connected ? '连接状态异常' : '等待后续适配器'}</span></div>
      </section>

      <section className="intro">
        <p className="section-label">开发基线</p>
        <h2>真实连接，克制承诺。</h2>
        <p>这里仅验证前后端骨架和公共契约。照护流程、主人审批与长期记忆由后续 Agent 分阶段实现。</p>
      </section>

      <section className="areas" aria-label="计划开发区域">
        {plannedAreas.map((area) => (
          <article key={area.title}>
            <span className="planned">尚未开发</span>
            <h3>{area.title}</h3>
            <p>{area.description}</p>
            <button type="button" disabled>{area.button}</button>
          </article>
        ))}
      </section>

      <footer>Scaffold only · 无业务数据 · 无云端资源</footer>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
