import { useSyncExternalStore } from 'react'
import { baseMessages } from './base-messages'
import { showcaseMessages } from './showcase-messages'
import { familyMessages } from './family-messages'
import { supportMessages } from './support-messages'
import { serverMessages } from './server-messages'
import type { CareSummary } from './family-api'
import './i18n.css'

export type Language = 'en' | 'zh'
const key = 'pawtwin-language'
function readLanguage(): Language {
  try { return localStorage.getItem(key) === 'zh' ? 'zh' : 'en' } catch { return 'en' }
}
let language = readLanguage()
const listeners = new Set<() => void>()
const messages: Record<string, string> = { ...baseMessages, ...showcaseMessages, ...familyMessages, ...supportMessages, ...serverMessages }
const originals = new Map(Object.entries(messages).map(([zh, en]) => [en, zh]))
function register(zh: string, en: string) { messages[zh] = en; originals.set(en, zh) }

// Call at UI boundaries; user-authored content is rendered without this helper.
export function t<T>(value: T, english?: string): T {
  if (typeof value !== 'string') return value
  if (english !== undefined) register(value, english)
  const original = originals.get(value) ?? value
  return (language === 'zh' ? original : messages[original] ?? value) as T
}
export function tf(template: string, ...values: unknown[]): string {
  const render = (text: string) => text.replace(/\{(\d+)\}/g, (_, index: string) => String(values[Number(index)] ?? ''))
  const zh = render(template), en = render(messages[template] ?? template)
  register(zh, en)
  return language === 'zh' ? zh : en
}
export function locale() { return language === 'zh' ? 'zh-CN' : 'en-US' }
// Match only the English prompts offered by the UI. Unknown freeform text and
// user names stay untouched; server permissions and confirmation still apply.
export function chatInput(text: string): string {
  const normalize = (value: string) => value.trim().toLowerCase().replace(/[?.!]+$/, '').replace(/\s+/g, ' ')
  const input = normalize(text)
  const aliases: Record<string, string> = { 'plan playtime': '安排陪玩', 'plan a walk': '安排散步', 'do not plan playtime': '不要安排陪玩', "don't plan playtime": '不要安排陪玩', 'cancel playtime': '取消陪玩' }
  if (aliases[input]) return aliases[input]
  const prompts = ['它喜欢什么', '最近体重是多少', '今天有哪些待办', '今天有什么观察', '最近完成了什么', '安排陪玩', '安排换水', '最近吃了什么', '做过哪些照护', '做了哪些照护', '照护记录', '现在有哪些待办', '最近饮食记录']
  return prompts.find(prompt => messages[prompt] && normalize(messages[prompt]) === input) ?? text
}
function careSummaryText(summary: CareSummary): string {
  const english = language === 'en'
  const prefix = summary.pet_name === null ? '' : `${summary.pet_name}${english ? '’s records: ' : ' 的记录：'}`
  const records = summary.records.map(record => {
    // Titles and pet names are the reply's original source snapshot. Only an
    // explicit server fallback flag authorizes translating a record title.
    const title = record.title_is_fallback
      ? t('人工照护（历史名称未记录）', 'Manual care (historical title not recorded)') : record.title
    return summary.kind === 'completed' && record.completed_at
      ? `${title}${english ? ` (${record.completed_at})` : `（${record.completed_at}）`}` : title
  }).join(english ? '; ' : '；')
  if (summary.kind === 'pending') {
    return prefix + (english ? `There are ${summary.total_count} pending care tasks; ` : `当前有 ${summary.total_count} 项待办照护；`)
      + (records || t('可按主人计划安排照护。'))
  }
  const heading = summary.pet_name === null
    ? (english ? 'Completed manual care in the last 7 days: ' : '近七天实际人工完成记录：')
    : (english ? 'Manual care completed in the last 7 days: ' : '最近七天的人工完成记录：')
  const empty = summary.pet_name === null
    ? t('暂无人工完成记录；待办与设备出粮不计为人工完成。')
    : t('暂无；不会把待办或设备出粮算作人工完成。')
  return prefix + heading + (records ? records + (english ? '.' : '。') : empty)
}
export function serverText(value: string, items: { name: string; displayName: string }[] = [], facts?: { breed?: string; care_summary?: CareSummary | null }): string {
  if (facts?.care_summary) return careSummaryText(facts.care_summary)
  if (language === 'zh') return originals.get(value) ?? value
  if (messages[value]) return messages[value]
  const todayObservation = ' 今天有相关主人观察，请先参考下方原文。'
  if (value.endsWith(todayObservation)) return serverText(value.slice(0, -todayObservation.length), items, facts) + t(todayObservation)
  if (value.startsWith('近期饮食记录：')) {
    return 'Recent diet records: ' + value.slice('近期饮食记录：'.length)
      .replace(/(主人记录实际摄入|提供食物|记录出粮|剩余食物|含义未说明) ([\d.]+) g（([^；]+)；原备注：([\s\S]*?)）(?=；|。提供食物)/g, (_, kind: string, grams: string, time: string, note: string) => `${({ 主人记录实际摄入: 'Owner-recorded actual intake', 提供食物: 'Food offered', 记录出粮: 'Recorded dispensing', 剩余食物: 'Food remaining', 含义未说明: 'Meaning not specified' } as Record<string,string>)[kind]} ${grams} g (${time}; original note: ${note === '未填写' ? t('未填写') : note})`)
      .replace('暂无已记录的饮食事实。', serverMessages['暂无已记录的饮食事实。'])
      .replace('。提供食物、出粮与剩余不等于实际摄入；食物说明只来自原始备注。', serverMessages['。提供食物、出粮与剩余不等于实际摄入；食物说明只来自原始备注。'])
  }
  if (value.startsWith('近七天实际人工完成记录：')) return 'Completed manual care in the last 7 days: ' + serverText(value.slice('近七天实际人工完成记录：'.length))
  const insightStart = '按主人设置的计划安排照护，先查看近期完成记录。'
  if (value.startsWith(insightStart)) return serverMessages[insightStart] + serverText(value.slice(insightStart.length), items, facts)
  // System templates use captured data verbatim, including names and notes.
  const patterns: [RegExp, (...parts: string[]) => string][] = [
    [/^过去 7 天有 (\d+) 条主人完成记录、(\d+) 篇成长日记。$/, (care, diary) => `Over the last 7 days: ${care} owner-completed care records and ${diary} diary entries.`],
    [/^\[本地替身\] 依据当前事实（上次喂食距今 (\d+) 分钟、当日已出粮 (\d+) 克、日配额 (\d+) 克）生成建议；最终是否执行由硬性策略与主人审批决定。$/, (minutes, dispensed, limit) => `[Local stand-in] Suggested from current facts: ${minutes} minutes since feeding, ${dispensed} g dispensed today, daily quota ${limit} g. Execution depends on hard policy checks and owner approval.`],
    [/^\[本地替身\] 缺少必要事实（(.+)），无法给出喂食建议，仅建议观察。补全事实后重新发送请求即可。$/, fields => `[Local stand-in] Required facts missing (${fields.replace('上次喂食时间', 'last feeding time').replace('当日已出粮量', 'food dispensed today').replaceAll('、', ', ')}). Observe only; complete the facts and send another request.`],
    [/^可选择(.+)安排陪玩。(.*)$/, (toys, rest) => `Plan playtime with ${toys === '添加一个喜欢的玩具' ? 'a favorite toy you add' : items.length && toys === items.map(item => item.name).join('、') ? items.map(item => item.displayName).join(', ') : toys}.${serverText(rest, items, facts)}`],
    [/^ 主人记录的喜好：([\s\S]*)。$/, likes => ` Owner-recorded preferences: ${likes}.`],
    [/^陪 (.+) 玩耍$/, name => `Play with ${name}`],
    [/^为 (.+) (人工喂食|换水|玩耍|梳毛|洗澡|剪指甲|清洁|散步)$/, (name, care) => `${t(care === '玩耍' ? '陪玩' : care)} for ${name}`],
    [/^(建立宠物档案|添加生活物品|调整物品|安排照护|领取|转交|编辑|取消|延期|完成|记录主人观察|添加成长日记)：([\s\S]*)$/, (action, content) => `${({ 建立宠物档案: 'Created pet profile', 添加生活物品: 'Added item', 调整物品: 'Adjusted item', 安排照护: 'Planned care', 领取: 'Claimed', 转交: 'Handed off', 编辑: 'Edited', 取消: 'Cancelled', 延期: 'Postponed', 完成: 'Completed', 记录主人观察: 'Recorded owner observation', 添加成长日记: 'Added diary entry' } as Record<string, string>)[action]}: ${content}`],
  ]
  for (const [pattern, render] of patterns) {
    const match = value.match(pattern)
    if (match) return render(...match.slice(1))
  }
  const answer = value.match(/^([\s\S]+?) 的记录：([\s\S]*)$/)
  if (!answer) return value
  let body = answer[2]
  if (body === '主人观察原文：暂无相关记录。') return `${answer[1]}’s records: Original owner observations: No related records yet.`
  if (facts?.breed === '') body = body.replace(/^主人确认的品种：未填写。/, 'Owner-confirmed breed: Not provided. ')
  const protectedValues: string[] = []
  // The local assistant inserts owner content after these explicit labels.
  const labels: Record<string, string> = { '档案喜好：': 'Profile preferences: ', '主人确认记录：': 'Owner-confirmed records: ', '主人确认的陪玩记录：': 'Owner-confirmed play records: ', '主人观察原文：': 'Original owner observations: ', '主人确认的品种：': 'Owner-confirmed breed: ' }
  body = body.replace(/(档案喜好：|主人确认记录：|主人确认的陪玩记录：|主人观察原文：|主人确认的品种：)([\s\S]*?)(?=。(?:主人确认记录：|观察不代表诊断。|当前缺少|不同记录|还没有已确认的偏好记忆。|$))/g, (_, label: string, content: string) => {
    protectedValues.push(content)
    return `${labels[label]}\u0001${protectedValues.length - 1}\u0001`
  })
  body = body.replace(/当前有 (\d+) 项待办照护；([\s\S]*)$/, (_, count: string, titles: string) => `There are ${count} pending care tasks; ${titles === '可按主人计划安排照护。' ? serverMessages[titles] : titles}`)
    .replace(/最近实测 (\S+) kg（([^，]+)，([^）]+)）。/g, 'Latest measured weight: $1 kg ($2, $3). ')
    .replace(/适用成长参考仍缺：([^。]+)。/g, (_, fields: string) => `Growth reference still needs: ${fields.split('、').map(field => t(field)).join(', ')}. `)
    .replace('最近七天的人工完成记录：', 'Manual care completed in the last 7 days: ')
  for (const [zh, en] of Object.entries(serverMessages).sort((a, b) => b[0].length - a[0].length)) {
    if (zh.length > 8) body = body.split(zh).join(en)
  }
  body = body.replace(/\u0001(\d+)\u0001/g, (_, index: string) => protectedValues[Number(index)])
  return `${answer[1]}’s records: ${body}`
}
export function setLanguage(next: Language) {
  if (next === language) return
  language = next
  try { localStorage.setItem(key, next) } catch { /* Switching still works when storage is unavailable. */ }
  listeners.forEach(listener => listener())
}
window.addEventListener('storage', event => {
  if (event.key === key || event.key === null) {
    const next = readLanguage()
    if (next !== language) { language = next; listeners.forEach(listener => listener()) }
  }
})
export function useLanguage() {
  return useSyncExternalStore(listener => { listeners.add(listener); return () => listeners.delete(listener) }, () => language)
}
export function LanguageSwitch() {
  const selected = useLanguage()
  return <div className="language-switch" role="group" aria-label={selected === 'en' ? 'Language' : '语言'}>
    <button type="button" lang="en" aria-pressed={selected === 'en'} onClick={() => setLanguage('en')}>English</button>
    <button type="button" lang={selected === 'zh' ? 'zh-CN' : 'en'} aria-pressed={selected === 'zh'} onClick={() => setLanguage('zh')}>{selected === 'zh' ? '中文' : 'Chinese'}</button>
  </div>
}
