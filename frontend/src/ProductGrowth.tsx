import { t } from './i18n'
import { useId } from 'react'
import { PET_PROFILES, type PetKind } from './PetPortrait'
import './product-growth.css'

// Static marketing fixtures only. These never enter the household record store.
export const DEMO_GROWTH = {
  mochi: [4.10, 4.16, 4.14, 4.22],
  miso: [9.20, 9.32, 9.28, 9.40],
  luna: [3.60, 3.64, 3.62, 3.68],
  coco: [5.20, 5.26, 5.24, 5.30],
} as const satisfies Record<PetKind, readonly number[]>

const DEMO_DATES = ['2026-09-22', '2026-09-29', '2026-10-06', '2026-10-13'] as const
export const DEMO_SOURCE = '电子秤 · 主人录入（模拟）'

export function demoGrowthRecords(pet: PetKind) {
  return DEMO_DATES.map((date, index) => ({ date, weight: DEMO_GROWTH[pet][index], source: DEMO_SOURCE }))
}

export function demoGrowthSummary(pet: PetKind) {
  const records = demoGrowthRecords(pet)
  const first = records[0]
  const latest = records[records.length - 1]
  const change = Math.round((latest.weight - first.weight) * 100) / 100
  return { first, latest, change, count: records.length }
}

export function formatDemoWeight(weight: number) {
  return `${weight.toFixed(2)} kg`
}

export function formatDemoChange(change: number) {
  return `${change > 0 ? '+' : ''}${change.toFixed(2)} kg`
}

export function GrowthTrend({ pet, compact = false }: { pet: PetKind; compact?: boolean }) {
  const gradientId = useId()
  const records = demoGrowthRecords(pet)
  const lower = Math.floor(Math.min(...DEMO_GROWTH[pet]) * 10 - 1) / 10
  const upper = Math.ceil(Math.max(...DEMO_GROWTH[pet]) * 10 + 1) / 10
  const yFor = (value: number) => 116 - (value - lower) / (upper - lower) * 88
  const points = records.map((record, index) => ({ ...record, x: 44 + index * 94, y: yFor(record.weight) }))
  const line = points.map(point => `${point.x},${point.y}`).join(' ')
  const ticks = [lower, (lower + upper) / 2, upper]
  return <figure className={`pg-trend${compact ? ' pg-trend-compact' : ''}`} aria-label={t(`${PET_PROFILES[pet].name} 的模拟体重曲线`, `${PET_PROFILES[pet].name} simulated weight trend`)}>
    <div className="pg-chart-caption"><strong>{t("体重趋势")}</strong><span>{t("kg · 模拟数据")}</span></div>
    <svg viewBox="0 0 360 152" role="img" aria-label={records.map(record => t(`${record.date}：${formatDemoWeight(record.weight)}`, `${record.date}: ${formatDemoWeight(record.weight)}`)).join(t('，', ', '))}>
      <defs><linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8d9e79" stopOpacity=".24" /><stop offset="100%" stopColor="#8d9e79" stopOpacity=".02" /></linearGradient></defs>
      {ticks.map(tick => <g key={tick}><path d={`M44 ${yFor(tick)}H326`} fill="none" stroke="#e2e4d9" strokeDasharray="3 5" /><text x="32" y={yFor(tick) + 3} textAnchor="end" className="pg-axis-label">{tick.toFixed(2)}</text></g>)}
      <path d={`M44 116 L${line.replaceAll(' ', ' L')} L326 116 Z`} fill={`url(#${gradientId})`} />
      <polyline className="pg-chart-line" points={line} fill="none" stroke="#718666" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      {points.map((point, index) => <g key={point.date}>
        <circle className="pg-chart-point" cx={point.x} cy={point.y} r="3.5" fill="#fffdf8" stroke="#718666" strokeWidth="2" />
        <text className="pg-weight-label" x={point.x} y={point.y - 11} textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'}>{point.weight.toFixed(2)}</text>
        <text className="pg-axis-label" x={point.x} y="140" textAnchor="middle">{point.date.slice(5).replace('-', '/')}</text>
      </g>)}
    </svg>
    <figcaption>{t("2026/09/22 — 10/13 · 四次模拟测量")}</figcaption>
  </figure>
}

export function ProductGrowth({ pet }: { pet: PetKind }) {
  const records = demoGrowthRecords(pet)
  const { latest, change, count } = demoGrowthSummary(pet)
  return <div className="pg-demo">
    <div className="pg-heading"><h4>{t("点滴记录，连成成长。")}</h4><span className="pg-demo-badge">{t("模拟数据")}</span></div>
    <p className="pg-subtitle">{t(`${PET_PROFILES[pet].name} 的成长手记 · 09/22 — 10/13`, `${PET_PROFILES[pet].name} growth journal · 09/22 — 10/13`)}</p>
    <div className="pg-metrics">
      <div><span>{t("最新体重")}</span><strong className="pg-latest">{formatDemoWeight(latest.weight)}</strong><small>{t("10/13 · 模拟测量")}</small></div>
      <div><span>{t("阶段变化")}</span><strong className="pg-change">{formatDemoChange(change)}</strong><small>{t(`相较 09/22 · ${count} 次记录`, `Since 09/22 · ${count} records`)}</small></div>
    </div>
    <GrowthTrend pet={pet} />
    <div className="pg-record-heading"><strong>{t("测量记录")}</strong><span>{t(`${count} 条示例`, `${count} examples`)}</span></div>
    <ol className="pg-records" aria-label={t("模拟测量记录")}>{records.map(record => <li key={record.date}>
      <time dateTime={record.date}>{record.date.slice(5).replace('-', '/')}<small>{t(record.source)}</small></time>
      <strong>{formatDemoWeight(record.weight)}</strong>
    </li>)}</ol>
    <div className="pg-diary"><span aria-hidden="true">✎</span><div><strong>{t("10/13 · 窗边的小日常")}</strong><p>{t("今天在窗边晒了会儿太阳，也陪它玩了一会儿。")}</p><small>{t("主人手记 · 模拟内容")}</small></div></div>
    <div className="pt-preview-foot">{t("模拟数据 · 仅用于产品展示，不写入真实成长记录。")}</div>
  </div>
}
