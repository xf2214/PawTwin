import { t, tf, locale, serverText } from './i18n'
import { actorName, itemText } from './system-defaults'
import { LocalizedInput, storedInputValue } from './LocalizedInput'
import { familyTime } from "./family-time";
import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, getRun, getState, hasCsrf, postApproval, postEvent, request, type FactsView, type RunView } from './api'
import PetAvatar from './PetAvatar'
import './pet-home.css'

type Species = 'cat' | 'dog'
type Coat = 'gold' | 'gray' | 'cream' | 'black' | 'white'
type Care = 'feeding' | 'water' | 'play' | 'brush' | 'bath' | 'nails' | 'clean' | 'walk'
type Pet = { id: string; name: string; species: Species; breed: string; gender: string;
  birthday: string | null; birthday_estimated: boolean; neutered: boolean | null; expected_adult_weight_kg: number | null; age_years: number | null; coat: Coat; pattern: string; size: string;
  likes: string; dislikes: string; photo_id: string | null; source: string }
type Member = { id: string; name: string }
type Item = { id: string; pet_id: string; kind: 'nest' | 'toy' | 'water' | 'feeder'; name: string;
  x: number; y: number; note: string }
type Task = { id: string; pet_id: string; kind: Care; title: string; due_at: string;
  interval_days: number | null; assigned_to: string | null; completed: boolean;
  last_completed_at: string | null; version?: number }
type Note = { id: string; pet_id: string; text: string; scope: string; activity: string;
  actor_id: string; created_at: string }
type Diary = { author_name?: string; id: string; pet_id: string; title: string; text: string; happened_on: string;
  actor_id: string; photo_id: string | null }
type Entry = { id: string; pet_id: string; actor: string; actor_id?: string | null; text: string; created_at: string }
type Home = { pets: Pet[]; members: Member[]; objects: Item[]; tasks: Task[]; notes: Note[];
  diary: Diary[]; history: Entry[]; photo_recognition_enabled: boolean }
type Insights = { suggestion: string; likes: string; dislikes: string; evidence: Note[];
  weekly: { text: string; completed_count: number; records: Entry[] } }
const CARE: Record<Care, string> = { feeding: '人工喂食', water: '换水', play: '陪玩',
  brush: '梳毛', bath: '洗澡', nails: '剪指甲', clean: '清洁窝 / 环境', walk: '散步' }
const OBJECTS = { nest: '窝', toy: '玩具', water: '水碗', feeder: '喂食器' }
const COATS: Record<Coat, string> = { gold: '暖橘', gray: '银灰', cream: '奶油', black: '黑色', white: '白色' }
const photoUrl = (id: string) => `/api/home/photos/${id}`
const localDate = (date = new Date()) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
const localTime = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16)
const timeText = (value: string) => new Date(value).toLocaleString(locale(), { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
const value = (form: FormData, key: string) => String(form.get(key) ?? '').trim()
const defaultPet: Omit<Pet, 'id' | 'source'> = { name: '', species: 'cat', breed: '', gender: 'unknown',
  birthday: null, birthday_estimated: false, neutered: null, expected_adult_weight_kg: null, age_years: null, coat: 'gold', pattern: 'solid', size: 'medium', likes: '', dislikes: '', photo_id: null }

function PixelPet({ pet, small = false }: { pet: Pet; small?: boolean }) {
  return <PetAvatar pet={pet} small={small} />
}

function Room({ pet, items, run, onItem }: { pet: Pet; items: Item[]; run: RunView | null;
  onItem: (item: Item) => void }) {
  return <div className="ph-room" aria-label={t("2D 俯视小屋 · 位置为展示布局")}>
    <div className="ph-window" /><div className="ph-sofa"><i /><i /><i /></div>
    <div className="ph-rug" /><div className="ph-table" /><div className="ph-plant">✦</div>
    <div className="ph-kitchen"><div className="ph-counter" /></div>
    <span className="ph-room-label">{t("客厅")}</span><span className="ph-room-label kitchen">{t("喂食区")}</span>
    {t(items.map(item => <button type="button" key={item.id} className={`ph-object ${item.kind}`}
      style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => onItem(item)} aria-label={t(tf("查看{0}", itemText(item, 'name')))}>
      <span className="ph-object-art" aria-hidden="true" /><span className="ph-object-name">{itemText(item, 'name')}</span>
    </button>))}
    <div className={`ph-character ${run?.state === 'succeeded' ? 'near-feeder' : ''}`}>
      <div className="ph-speech">{t(run?.state === 'awaiting_approval' ? '等待主人确认' : run?.state === 'succeeded' ? '已收到模拟成功回执' : tf("{0} 的小屋", pet.name))}</div>
      <PixelPet pet={pet} />
    </div>
  </div>
}

export default function PetHome({ onLogout, account, selectedPet, onPetChange, externalTab, onHomeChanged, onCareNavigate, onObservationNavigate, onObservationReady, timezone, embedded = false }: {
  onLogout: () => void;
  account?: { user_id: string; role: string; canFeed: boolean };
  selectedPet?: string; onPetChange?: (id: string, expectedPetId?: string) => void; externalTab?: string;
  onHomeChanged?: () => Promise<void>;
  onCareNavigate?: (kind?: Care) => void; onObservationNavigate?: () => void; timezone?: string;
  onObservationReady?: (field: HTMLTextAreaElement) => void;
  embedded?: boolean;
}) {
  const timeText = (date: string) => timezone ? familyTime(date, timezone) : new Date(date).toLocaleString(locale(), { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  const [home, setHome] = useState<Home | null>(null), [selected, setSelected] = useState(() => selectedPet ?? sessionStorage.getItem('pawtwin-home-pet') ?? 'mochi')
  const [tab, setTab] = useState(externalTab ?? '小屋'), [actor, setActor] = useState('')
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState<Pet | null | undefined>(undefined)
  const [formPet, setFormPet] = useState(defaultPet), [draftMessage, setDraftMessage] = useState('')
  const [itemEdit, setItemEdit] = useState<Item | null>(null), [kind, setKind] = useState<Care>('water')
  const [insight, setInsight] = useState<Insights | null>(null), [insightActivity, setInsightActivity] = useState<Care>('play')
  const [run, setRun] = useState<RunView | null>(null), [diaryPhoto, setDiaryPhoto] = useState<string | null>(null)
  const [deviceRuns, setDeviceRuns] = useState<RunView[]>([])
  const [feedingFacts, setFeedingFacts] = useState<FactsView | null>(null)
  const [postponing, setPostponing] = useState(''), [postponeTime, setPostponeTime] = useState(localTime())
  const observationField = useRef<HTMLTextAreaElement>(null)
  const draftScope = useRef(0)
  const mounted = useRef(true)
  const petScope = useRef({ id: '', epoch: 0 })
  const pet = home?.pets.find(p => p.id === selected) ?? home?.pets[0]
  const currentPetId = selectedPet ?? pet?.id ?? selected
  if (petScope.current.id !== currentPetId) {
    petScope.current = { id: currentPetId, epoch: petScope.current.epoch + 1 }
  }
  const canWrite = hasCsrf() && account?.role !== 'guest'
  const canManage = canWrite && (!account || account.role === 'admin')
  useEffect(() => { if (selectedPet) setSelected(selectedPet) }, [selectedPet])
  useEffect(() => { if (externalTab) setTab(externalTab) }, [externalTab])
  useEffect(() => { if (tab === '成长日记' && observationField.current) onObservationReady?.(observationField.current) }, [tab, pet?.id, onObservationReady])
  useEffect(() => { if (account) setActor(account.user_id) }, [account?.user_id])
  useEffect(() => { if (pet) onPetChange?.(pet.id) }, [pet?.id, onPetChange])

  function failure(err: unknown) {
    if (err instanceof ApiError) { try { setError(JSON.parse(err.message).detail ?? err.message) } catch { setError(err.message) } }
    else setError('无法完成操作，请检查连接后重试。')
  }
  const refresh = useCallback(async () => {
    try { const data = await request<Home>('/api/home/state'); setHome(data); setActor(a => account?.user_id || a || data.members[0]?.id || '') }
    catch (e) { failure(e) }
  }, [account?.user_id])
  useEffect(() => { void refresh() }, [refresh])
  useEffect(() => { if (!account) return; const timer = setInterval(() => void refresh(), 10000); return () => clearInterval(timer) }, [account?.user_id, refresh])
  useEffect(() => {
    if (!pet) return
    let valid = true
    setInsight(null)
    request<Insights>(`/api/home/pets/${pet.id}/insights?activity=${insightActivity}`).then(x => { if (valid) setInsight(x) }).catch(failure)
    return () => { valid = false }
  }, [pet, home, insightActivity])
  useEffect(() => { draftScope.current++; sessionStorage.setItem('pawtwin-home-pet', selected); setRun(null); setItemEdit(null); setEditing(undefined); setFormPet({ ...defaultPet }); setDraftMessage(''); setDiaryPhoto(null); setPostponing(''); setError(''); setNotice(''); setBusy(false) }, [selected])
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; draftScope.current++ } }, [])
  useEffect(() => {
    if (pet?.id !== 'mochi' || (account && !account.canFeed)) { setDeviceRuns([]); setFeedingFacts(null); return }
    let alive = true
    getState().then(snapshot => { if (alive) { setDeviceRuns(snapshot.runs); setFeedingFacts(snapshot.facts); setRun(old => old ?? snapshot.runs[0] ?? null) } }).catch(failure)
    return () => { alive = false }
  }, [pet?.id, run?.state, account?.canFeed])
  useEffect(() => {
    if (!run || !['queued', 'analyzing', 'executing'].includes(run.state)) return
    let alive = true, timer: ReturnType<typeof setTimeout>
    const poll = async () => { try { const updated = await getRun(run.run_id); if (alive) { setRun(updated); if (['queued', 'analyzing', 'executing'].includes(updated.state)) timer = setTimeout(poll, 1000) } } catch (e) { if (alive) failure(e) } }
    timer = setTimeout(poll, 1000)
    return () => { alive = false; clearTimeout(timer) }
  }, [run])

  function writeScope() {
    const { id: petId, epoch } = petScope.current, draft = draftScope.current
    return {
      petId,
      samePet: () => petScope.current.epoch === epoch,
      active: () => mounted.current && petScope.current.epoch === epoch && draftScope.current === draft,
    }
  }
  async function save(path: string, body: object, method = 'POST', detachedCreate = false): Promise<Home | null> {
    const scope = writeScope()
    setBusy(true); setError(''); setNotice('')
    try {
      const next = await request<Home>(`/api/home${path}`, { method, body: JSON.stringify(body) })
      if (!scope.samePet()) return null
      if (scope.active()) setHome(old => ({ ...old, ...next }))
      await onHomeChanged?.()
      if (scope.active()) { setNotice('已保存'); return next }
      // A created pet still reaches the parent after page navigation. The parent
      // validates its expected source pet before accepting that selection.
      if (detachedCreate && path === '/pets' && method === 'POST' && !mounted.current && scope.samePet()) return next
      return null
    } catch (e) { if (scope.active()) failure(e); return null }
    finally { if (scope.active()) setBusy(false) }
  }
  async function upload(file: File | undefined): Promise<string | null> {
    if (!file) return null
    if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 3 * 1024 * 1024) { setError('请选择不超过 3 MB 的 JPG 或 PNG 照片。'); return null }
    const data = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = reject; reader.readAsDataURL(file) })
    return (await request<{ id: string }>('/api/home/photos', { method: 'POST', body: JSON.stringify({ data_url: data }) })).id
  }
  async function profilePhoto(file: File | undefined) {
    const scope = draftScope.current
    setBusy(true); setError('')
    try {
      const id = await upload(file); if (!id) return
      if (scope !== draftScope.current) return
      setFormPet(p => ({ ...p, photo_id: id })); setDraftMessage('照片已保存，可以手动确认资料。')
      if (home?.photo_recognition_enabled) {
        const data = await request<{ draft: Partial<Pet> & { uncertainty: string }; request_id: string; model_id: string }>(`/api/home/photos/${id}/recognize`, { method: 'POST' })
        if (scope !== draftScope.current) return
        setFormPet(p => ({ ...p, species: data.draft.species ?? p.species, breed: data.draft.breed ?? p.breed,
          coat: data.draft.coat ?? p.coat, pattern: data.draft.pattern ?? p.pattern }))
        setDraftMessage(tf("识别草稿，保存前请确认：{0} 模型：{1}，请求：{2}", data.draft.uncertainty || '品种仅为候选；年龄与喜好需要主人填写。', data.model_id, data.request_id))
      } else setDraftMessage('照片已保存；当前未启用自动识别，请手动填写资料。')
    } catch (e) { if (scope === draftScope.current) failure(e) } finally { if (scope === draftScope.current) setBusy(false) }
  }
  function openPet(p: Pet | null) { draftScope.current++; setEditing(p); setFormPet(p ? { ...defaultPet, ...p } : { ...defaultPet }); setDraftMessage(''); setTab('档案与物品') }
  async function sendFood() {
    const scope = writeScope()
    setBusy(true); setError('')
    try { const result = await postEvent('food_request', 'kitchen'); if (!scope.active()) return; const next = await getRun(result.run_id); if (scope.active()) setRun(next) }
    catch (e) { if (scope.active()) failure(e) } finally { if (scope.active()) setBusy(false) }
  }
  async function approve(decision: 'approve' | 'decline') {
    if (!run?.action_digest) return
    const scope = writeScope()
    setBusy(true)
    try { await postApproval(run.run_id, { decision, proposal_version: run.proposal_version, action_digest: run.action_digest }); if (!scope.active()) return; const next = await getRun(run.run_id); if (scope.active()) { setRun(next); await refresh() } }
    catch (e) { if (scope.active()) failure(e) } finally { if (scope.active()) setBusy(false) }
  }
  async function taskAction(task: Task, action: 'complete' | 'postpone') {
    if (await save(`/tasks/${task.id}/action`, { event_id: crypto.randomUUID(), actor_id: actor, action,
      ...(account ? { version: task.version } : {}),
      next_due: action === 'postpone' ? new Date(postponeTime).toISOString() : null })) setPostponing('')
  }
  if (!home || !pet) return <main className="pet-home"><h1>{t("宠物小屋")}</h1><p>{t(error || '正在打开小屋…')}</p><a href="#workbench">{t("返回详细信息")}</a></main>
  const items = home.objects.filter(o => o.pet_id === pet.id), tasks = home.tasks.filter(t => t.pet_id === pet.id)
  const notes = home.notes.filter(n => n.pet_id === pet.id), diary = home.diary.filter(d => d.pet_id === pet.id)
  const history = home.history.filter(h => h.pet_id === pet.id).slice().reverse()
  const age = pet.birthday ? Math.max(0, (Date.now() - new Date(pet.birthday).getTime()) / 31557600000).toFixed(1) : pet.age_years
  const ageLabel = age == null ? '年龄未填' : Number(age) < 1 ? tf("约 {0} 周 / {1} 月", Math.max(1, Math.round(Number(age) * 52)), Math.max(1, Math.round(Number(age) * 12))) : tf("{0} 岁", age)
  const pendingTasks = tasks.filter(t => !t.completed && new Date(t.due_at).getTime() <= Date.now())
  const memberName = (id: string | null) => {
    const member = home.members.find(m => m.id === id)
    return member ? actorName(member.name, member.id) : t('未分配')
  }

  function taskCard(task: Task) {
    const waiting = task.completed || (!!task.last_completed_at && new Date(task.due_at).getTime() > Date.now())
    return <article className={`ph-task ${waiting ? 'done' : ''}`} key={task.id}>
      <div><strong>{task.title}</strong><span className="ph-tag">{t(CARE[task.kind])}</span></div>
      <p>{t(task.completed ? '已完成' : tf("计划：{0}", timeText(task.due_at)))} · {memberName(task.assigned_to)}{t(task.interval_days ? tf(" · 每 {0} 天", task.interval_days) : '')}</p>
      {t(task.last_completed_at && <small>{t("最近完成：")}{t(timeText(task.last_completed_at))}</small>)}
      {t(!waiting && <div className="ph-actions"><button disabled={busy || !canWrite} onClick={() => void taskAction(task, 'complete')}>{t("标记完成")}</button><button className="ph-secondary" onClick={() => { setPostponing(task.id); setPostponeTime(localTime()) }}>{t("延期")}</button></div>)}
      {t(postponing === task.id && <div className="ph-actions"><label>{t("延期到")}<input type="datetime-local" aria-label={t("延期时间")} value={postponeTime} onChange={e => setPostponeTime(e.target.value)} /></label><button disabled={busy || !canWrite || !postponeTime} onClick={() => void taskAction(task, 'postpone')}>{t("保存延期")}</button></div>)}
    </article>
  }

  const Container = embedded ? 'section' : 'main'
  return <Container className={tf("pet-home{0}{1}", embedded ? ' ph-embedded' : '', tab === '成长日记' ? ' ph-journal' : '')} aria-label={t(embedded ? tf("{0} 的{1}", pet.name, t(tab === '成长日记' ? '日记与观察' : '小屋')) : undefined)}>
    {t(!embedded && <><header className="ph-header"><div><p className="ph-eyebrow">PAWTWIN · YOUR PET, YOUR HOME</p><h1>{pet.name}{t(" 的小屋")}</h1></div><div className="ph-header-actions"><a href="#workbench">{t("详细信息")}</a><button className="ph-secondary" onClick={onLogout}>{t("退出")}</button></div></header>
    <div className="ph-toolbar"><label>{t("当前宠物")}<select value={pet.id} onChange={e => setSelected(e.target.value)}>{t(home.pets.map(p => <option key={p.id} value={p.id}>{p.name}</option>))}</select></label><button disabled={!canManage} onClick={() => openPet(null)}>{t("＋ 添加宠物")}</button>{t(!account && <label>{t("记录人")}<select value={actor} onChange={e => setActor(e.target.value)}>{t(home.members.map(m => <option key={m.id} value={m.id}>{actorName(m.name, m.id)}</option>))}</select></label>)}<span className="ph-boundary">{t("本机保存 · 小屋位置为模拟 · 执行器为模拟")}</span></div>
    <nav className="ph-tabs" aria-label={t("小屋功能")}>{t(['小屋', '档案与物品', '照护计划', '成长日记', '家庭交接'].filter(t => !account || t !== '家庭交接').map(tabName => <button key={tabName} className={tab === tabName ? 'active' : ''} aria-pressed={tab === tabName} onClick={() => tabName === '照护计划' && onCareNavigate ? onCareNavigate() : tabName === '成长日记' && onObservationNavigate ? onObservationNavigate() : setTab(tabName)}>{t(tabName)}</button>))}</nav></>)}
    {t(embedded && externalTab !== '成长日记' && <nav className="ph-local-tools" aria-label={t("小屋管理")}><div><span className="ph-eyebrow">{t("你的宠物空间")}</span><p>{t(tab === '档案与物品' ? '档案与生活物品' : '看看家里的日常')}</p></div><div className="ph-actions">{t(tab !== '小屋' && <button type="button" className="ph-secondary" onClick={() => { setEditing(undefined); setItemEdit(null); setTab('小屋') }}>{t("返回小屋")}</button>)}<button type="button" className="ph-secondary" disabled={!canManage || busy} onClick={() => openPet(pet)}>{t("编辑档案")}</button><button type="button" className="ph-secondary" onClick={() => { setEditing(undefined); setTab('档案与物品') }}>{t("布置小屋")}</button><button type="button" disabled={!canManage || busy} onClick={() => openPet(null)}>{t("＋ 添加宠物")}</button></div></nav>)}
    {t(error && <p role="alert" className="ph-error">{t(error)}</p>)}{t(notice && <p role="status" className="ph-notice">{t(notice)}</p>)}
    {t(tab === '小屋' && pet.id === 'mochi' && feedingFacts && <div className="ph-facts-bar"><span>{t("上次喂食距今：")}{t(feedingFacts.last_fed_minutes_ago == null ? '未知' : tf("{0} 分钟", feedingFacts.last_fed_minutes_ago))}</span><span>{t("当日已出粮：")}{t(feedingFacts.daily_dispensed_grams == null ? '未知' : feedingFacts.daily_dispensed_grams)} / {t(feedingFacts.daily_limit_grams)}{t(" 克")}</span><span>{t("数据来自当前模拟照护记录")}</span></div>)}
    {t(!canWrite && <p className="ph-error">{t(account?.role === 'guest' ? '当前为访客，只能查看获授权的家庭资料。' : '当前可以查看资料。请退出后重新登录，恢复编辑和确认操作。')}</p>)}
    {t(tab === '小屋' && <div className="ph-layout">
      <section className="ph-card ph-scene-card"><div className="ph-card-title"><h2>{t("家里的日常")}</h2><span className="ph-tag">{t("2D 俯视房间 · 正面像素宠物")}</span></div><Room pet={pet} items={items} run={run} onItem={item => { setItemEdit(item); setTab('档案与物品') }} />
        <div className="ph-scene-footer">{t(items.map(item => <button className="ph-secondary" key={item.id} onClick={() => { setItemEdit(item); setTab('档案与物品') }}>{itemText(item, 'name')}</button>))}{t(!embedded && <button className="ph-secondary" onClick={() => setTab('档案与物品')}>{t("布置小屋")}</button>)}<span className="ph-scene-hint">{t("点选物品，查看使用习惯与相关照护")}</span></div>
        <div className="ph-home-summary"><h3>{t("到期待办 · ")}{t(pendingTasks.length)}{t(" 项")}</h3>{t(pendingTasks.slice(0, 3).map(taskCard))}{t(!pendingTasks.length && <p>{t("当前暂无到期任务。可以安排洗澡、剪指甲、陪玩或换水。")}</p>)}<button className="ph-secondary" onClick={() => onCareNavigate ? onCareNavigate() : setTab('照护计划')}>{t("管理照护计划")}</button></div>
      </section>
      <aside className="ph-side"><section className="ph-card ph-profile-card"><div className="ph-profile-heading"><PixelPet pet={pet} small /><div><h2>{pet.name}</h2><p>{t(pet.species === 'cat' ? '猫咪' : '狗狗')} · {pet.breed || t('品种未填')} · {t(ageLabel)}{t(pet.birthday_estimated && pet.birthday ? "（生日估计）" : "")}</p></div>{t(pet.photo_id && <img className="ph-avatar" src={photoUrl(pet.photo_id)} alt={t(tf("{0} 的照片", pet.name))} />)}</div><dl className="ph-preferences"><div><dt>{t("喜欢")}</dt><dd>{pet.likes || t('尚未记录')}</dd></div><div><dt>{t("请留意")}</dt><dd>{pet.dislikes || t('尚未记录')}</dd></div></dl>{t(!embedded && <button className="ph-secondary" disabled={!canManage || busy} onClick={() => openPet(pet)}>{t("编辑档案")}</button>)}</section>
        <section className="ph-card"><h2>{t("照护建议")}</h2><label>{t("照护场景")}<select value={insightActivity} onChange={e => setInsightActivity(e.target.value as Care)}>{t(Object.entries(CARE).map(([k, label]) => <option key={k} value={k}>{t(label)}</option>))}</select></label><p>{insight ? serverText(insight.suggestion, items.filter(item => item.kind === 'toy').map(item => ({ name: item.name, displayName: itemText(item, 'name') }))) : t('正在读取主人记录…')}</p><small>{t("依据主人资料的规则建议 · 不表示模型识别了宠物心理")}</small>{t(insight?.evidence.map(n => <blockquote key={n.id}>{n.text}<small>{t(n.scope === 'today' ? '仅今天' : n.scope === 'preference' ? '主人确认偏好' : '主人观察')}</small></blockquote>))}{t(pet.dislikes && <p className="ph-note">{t("请留意主人记录：")}{pet.dislikes}</p>)}<button className="ph-secondary" onClick={() => onObservationNavigate ? onObservationNavigate() : setTab('成长日记')}>{t("补充观察与偏好")}</button></section>
        <section className="ph-card"><h2>{t("喂食请求")}</h2>{t(pet.id === 'mochi' && (!account || account.canFeed) ? <><p>{t("沿用现有审批与配额检查，成功回执后才表现完成。")}</p><button disabled={busy || !canWrite || (!!run && ['queued', 'analyzing', 'awaiting_approval', 'executing'].includes(run.state))} onClick={() => void sendFood()}>{t("发送模拟吃饭请求")}</button>{t(run && <div className="ph-run" aria-live="polite"><p>{t("任务：")}{t(({ awaiting_approval: '等待主人确认', succeeded: '模拟执行成功', declined: '已拒绝', blocked: '策略已阻止', analyzing: '分析中', queued: '排队中', executing: '执行中', needs_info: '信息不足', expired: '已过期', failed: '执行失败', unknown: '结果未知' })[run.state])}</p><p>{serverText(run.proposal?.explanation || run.policy_reason || run.failure_reason || '')}</p>{t(run.proposal?.action.kind === 'dispense_food' && <p>{t("本次建议：")}{t(run.proposal.action.grams)}{t(" 克")}</p>)}{t(run.state === 'awaiting_approval' && <div className="ph-actions"><button disabled={busy || !canWrite} onClick={() => void approve('approve')}>{t("批准本次动作")}</button><button className="ph-secondary" disabled={busy || !canWrite} onClick={() => void approve('decline')}>{t("拒绝")}</button></div>)}</div>)}</> : <p>{t("这只宠物尚未接入自动喂食策略。可以在照护计划中记录人工喂食，不会调用其他宠物的设备或额度。")}</p>)}</section>
      </aside>
    </div>)}
    {t(tab === '档案与物品' && <>
      {t(editing !== undefined && <section className="ph-card ph-profile-editor"><div className="ph-card-title"><div><p className="ph-eyebrow">{t("档案 · 由主人确认")}</p><h2>{t(editing ? '编辑宠物档案' : '认识一位新伙伴')}</h2></div><span className="ph-tag">{editing ? pet.name : t('新伙伴')}</span></div><p className="ph-section-intro">{t("名字和种类就能建档，其他资料可以以后补充。形象会跟随下方选择实时变化。")}</p>
        <div className="ph-photo-setup">{t(formPet.photo_id && <img src={photoUrl(formPet.photo_id)} alt={t("宠物建档照片")} />)}<PixelPet pet={{ ...formPet, id: 'preview', source: 'draft' }} /><div><h3>{t("照片与形象预览")}</h3><label className="ph-upload">{t("上传照片")}<input type="file" accept="image/png,image/jpeg" disabled={busy || !canManage} onChange={e => void profilePhoto(e.target.files?.[0])} /></label><label className="ph-upload">{t("拍照")}<input type="file" accept="image/png,image/jpeg" capture="environment" disabled={busy || !canManage} onChange={e => void profilePhoto(e.target.files?.[0])} /></label><small>{t("JPG / PNG，最多 3 MB。")}{t(home.photo_recognition_enabled ? '识别结果需主人确认。' : '自动识别未启用；可以手动填写。')}</small><p role="status">{t(draftMessage)}</p></div></div>
        <form className="ph-profile-form" onSubmit={async e => {
          e.preventDefault()
          const scope = writeScope(), creating = editing === null
          const data = Object.fromEntries(Object.keys(defaultPet).map(key => [key, formPet[key as keyof typeof defaultPet]]))
          const oldIds = home.pets.map(p => p.id)
          const next = await save(editing ? `/pets/${editing.id}` : '/pets', data, editing ? 'PUT' : 'POST', creating)
          if (next) {
            if (scope.active()) setEditing(undefined)
            if (creating) {
              const added = next.pets.find(p => !oldIds.includes(p.id))
              if (added) {
                if (scope.active()) setSelected(added.id)
                // save already refreshed the parent snapshot. Notify it directly
                // even when navigation has unmounted this child before success.
                onPetChange?.(added.id, scope.petId)
              }
            }
          }
        }}>
          <fieldset className="ph-fieldset" disabled={busy || !canManage}><legend>{t("基本资料")}</legend><div className="ph-form-grid"><label>{t("名字 *")}<input required maxLength={40} value={formPet.name} onChange={e => setFormPet(p => ({ ...p, name: e.target.value }))} /></label><label>{t("种类")}<select value={formPet.species} onChange={e => setFormPet(p => ({ ...p, species: e.target.value as Species }))}><option value="cat">{t("猫")}</option><option value="dog">{t("狗")}</option></select></label><label>{t("品种（候选需确认）")}<input maxLength={80} value={formPet.breed} onChange={e => setFormPet(p => ({ ...p, breed: e.target.value }))} /></label><label>{t("性别")}<select value={formPet.gender} onChange={e => setFormPet(p => ({ ...p, gender: e.target.value }))}><option value="unknown">{t("未填写")}</option><option value="female">{t("母")}</option><option value="male">{t("公")}</option></select></label><label>{t("生日")}<input type="date" max={localDate()} value={formPet.birthday ?? ''} onChange={e => setFormPet(p => ({ ...p, birthday: e.target.value || null }))} /></label><label>{t("生日是否估计")}<select value={formPet.birthday_estimated ? "yes" : "no"} onChange={e => setFormPet(p => ({ ...p, birthday_estimated: e.target.value === "yes" }))}><option value="no">{t("确切生日")}</option><option value="yes">{t("主人估计")}</option></select></label><label>{t("绝育状态")}<select value={formPet.neutered == null ? "unknown" : formPet.neutered ? "yes" : "no"} onChange={e => setFormPet(p => ({ ...p, neutered: e.target.value === "unknown" ? null : e.target.value === "yes" }))}><option value="unknown">{t("未填写")}</option><option value="yes">{t("已绝育")}</option><option value="no">{t("未绝育")}</option></select></label><label>{t("预期成年体重（kg，可留空）")}<input type="number" min="0.01" max="200" step="0.01" value={formPet.expected_adult_weight_kg ?? ""} onChange={e => setFormPet(p => ({ ...p, expected_adult_weight_kg: e.target.value ? Number(e.target.value) : null }))} /></label><label>{t("年龄（不知道生日时填写）")}<input type="number" min={0} max={50} step="0.1" value={formPet.age_years ?? ''} onChange={e => setFormPet(p => ({ ...p, age_years: e.target.value === '' ? null : Number(e.target.value) }))} /></label></div>
          <details><summary>{t("像素形象与个体喜好")}</summary><div className="ph-form-grid"><label>{t("毛色")}<select value={formPet.coat} onChange={e => setFormPet(p => ({ ...p, coat: e.target.value as Coat }))}>{t(Object.entries(COATS).map(([k,v]) => <option key={k} value={k}>{t(v)}</option>))}</select></label><label>{t("花纹")}<select value={formPet.pattern} onChange={e => setFormPet(p => ({ ...p, pattern: e.target.value }))}><option value="solid">{t("纯色")}</option><option value="stripes">{t("条纹")}</option><option value="spots">{t("斑块")}</option></select></label><label>{t("形象大小")}<select value={formPet.size} onChange={e => setFormPet(p => ({ ...p, size: e.target.value }))}><option value="small">{t("小")}</option><option value="medium">{t("中")}</option><option value="large">{t("大")}</option></select></label><label>{t("喜欢的食物 / 互动")}<input maxLength={300} value={formPet.likes} onChange={e => setFormPet(p => ({ ...p, likes: e.target.value }))} /></label><label>{t("不喜欢的事")}<input maxLength={300} value={formPet.dislikes} onChange={e => setFormPet(p => ({ ...p, dislikes: e.target.value }))} /></label></div></details>
          </fieldset><div className="ph-actions ph-form-actions"><button disabled={busy || !canManage}>{t(busy ? '正在保存…' : '确认并保存档案')}</button><button type="button" className="ph-secondary" onClick={() => { setEditing(undefined); setDraftMessage('') }}>{t("取消")}</button></div>
        </form></section>)}
      <section className="ph-card ph-room-editor"><div className="ph-card-title"><h2>{pet.name}{t(" 的档案与物品")}</h2>{t(!embedded && <button className="ph-secondary" disabled={!canManage || busy} onClick={() => openPet(pet)}>{t("编辑档案")}</button>)}</div><p className="ph-section-intro">{t("摆放常用物品，留下使用习惯。这里的位置用于小屋展示，照护安排仍由你确认。")}</p>{t(!canManage && <p className="ph-note">{t("档案与物品由家庭管理员修改；照护成员可查看并安排人工照护。")}</p>)}<Room pet={pet} items={items} run={null} onItem={setItemEdit} />
        <div className="ph-item-list">{t(items.map(o => <button key={o.id} className="ph-secondary" onClick={() => setItemEdit(o)}>{t(OBJECTS[o.kind])} · {itemText(o, 'name')}</button>))}</div>
        <form className="ph-item-editor" key={itemEdit?.id ?? `new-${pet.id}`} onSubmit={async e => {
          e.preventDefault()
          const f = e.currentTarget, d = new FormData(f)
          const kind = value(d, 'kind')
          if (await save(itemEdit ? `/objects/${itemEdit.id}` : `/pets/${pet.id}/objects`, {
            kind, name: storedInputValue(f, 'name', itemEdit?.name ?? ''),
            x: Number(value(d, 'x')), y: Number(value(d, 'y')),
            note: storedInputValue(f, 'note', itemEdit?.note ?? ''),
          }, itemEdit ? 'PUT' : 'POST')) { setItemEdit(null); f.reset() }
        }}>
          <p className="ph-eyebrow">{t("生活物品 · ")}{t(items.length)}{t(" 件已保存")}</p><h3>{t(itemEdit ? tf("调整 {0}", itemText(itemEdit, 'name')) : '添加生活物品')}</h3><fieldset className="ph-fieldset" disabled={busy || !canManage}><div className="ph-form-grid"><label>{t("物品类型")}<select name="kind" defaultValue={itemEdit?.kind ?? 'nest'}>{t(Object.entries(OBJECTS).map(([k,v]) => <option value={k} key={k}>{t(v)}</option>))}</select></label><label>{t("名称")}<LocalizedInput name="name" required maxLength={80} storedValue={itemEdit?.name ?? ''} displayValue={itemEdit ? itemText(itemEdit, 'name') : ''} placeholder={t("例如：窗边的小窝、羽毛棒")} /></label><label>{t("水平位置")}<input name="x" type="range" min={8} max={88} defaultValue={itemEdit?.x ?? 25} /></label><label>{t("垂直位置")}<input name="y" type="range" min={18} max={82} defaultValue={itemEdit?.y ?? 65} /></label><label>{t("使用习惯 / 清洁备注")}<LocalizedInput name="note" maxLength={300} storedValue={itemEdit?.note ?? ''} displayValue={itemEdit ? itemText(itemEdit, 'note') : ''} /></label></div></fieldset><div className="ph-actions ph-form-actions"><button disabled={busy || !canManage}>{t(itemEdit ? '保存物品与位置' : '添加到小屋')}</button>{t(itemEdit && <button className="ph-secondary" type="button" onClick={() => setItemEdit(null)}>{t("添加另一个")}</button>)}<button className="ph-secondary" type="button" disabled={busy || !canWrite} onClick={() => { const relatedKind = itemEdit?.kind === 'toy' ? 'play' : itemEdit?.kind === 'water' ? 'water' : 'clean'; setKind(relatedKind); if (onCareNavigate) onCareNavigate(relatedKind); else setTab('照护计划') }}>{t("安排相关照护")}</button></div>
        </form></section>
    </>)}
    {t(tab === '照护计划' && <div className="ph-two-columns"><section className="ph-card"><h2>{t("安排照护")}</h2><p>{t("频率由主人决定。洗澡和剪指甲不会自动预设周期。")}</p><div className="ph-actions">{t((['bath','nails','brush','water'] as Care[]).map(k => <button key={k} className="ph-secondary" onClick={() => setKind(k)}>{t("安排")}{t(CARE[k])}</button>))}</div>
      <form key={kind} onSubmit={async e => { e.preventDefault(); const f = e.currentTarget, d = new FormData(f); if (await save(`/pets/${pet.id}/tasks`, { kind, title: value(d,'title'), due_at: new Date(value(d,'due')).toISOString(), interval_days: value(d,'interval') ? Number(value(d,'interval')) : null, assigned_to: value(d,'assigned') || null })) f.reset() }}><div className="ph-form-grid"><label>{t("类型")}<select value={kind} onChange={e => setKind(e.target.value as Care)}>{t(Object.entries(CARE).map(([k,v]) => <option key={k} value={k}>{t(v)}</option>))}</select></label><label>{t("任务名称")}<input name="title" required maxLength={80} defaultValue={t(CARE[kind])} /></label><label>{t("计划时间")}<input name="due" type="datetime-local" required defaultValue={localTime()} /></label><label>{t("负责照护的人")}<select name="assigned"><option value="">{t("未分配")}</option>{t(home.members.map(m => <option key={m.id} value={m.id}>{actorName(m.name, m.id)}</option>))}</select></label><label>{t("重复间隔（天，留空为一次性）")}<input name="interval" type="number" min={1} max={365} placeholder={t("由主人设置")} /></label></div><p className="ph-note">{t("“人工喂食”表示主人手动记录，不触发自动出粮。")}</p><button disabled={busy || !canWrite}>{t("保存照护计划")}</button></form>
      </section><section className="ph-card"><h2>{pet.name}{t(" 的照护清单")}</h2>{t(tasks.map(taskCard))}{t(!tasks.length && <p>{t("还没有照护计划，从一项日常小事开始。")}</p>)}</section></div>)}
    {t(tab === '成长日记' && <div className="ph-two-columns ph-journal-layout">
      <div className="ph-journal-compose">
        <section className="ph-card ph-observation-card" aria-label={t(tf("{0} 的主人观察", pet.name))}>
          <p className="ph-eyebrow">{t("今天看到了什么")}</p><h2>{t("主人观察与偏好")}</h2><p className="ph-section-intro">{t("记录 ")}{pet.name}{t(" 的真实日常，再选择这条记录的作用范围。")}</p>
          <form key={`notes-${pet.id}`} onSubmit={async e => { e.preventDefault(); const f = e.currentTarget, d = new FormData(f); if (await save(`/pets/${pet.id}/notes`, { text: value(d, 'text'), scope: value(d, 'scope'), activity: value(d, 'activity'), actor_id: actor })) f.reset() }}>
            <fieldset className="ph-fieldset" disabled={busy || !canWrite}><label>{t("记录原文")}<textarea ref={observationField} id={account ? 'family-observation-input' : 'pet-home-observation-input'} name="text" required maxLength={500} placeholder={t("例如：饭后不想玩 / 喜欢羽毛棒")} /></label>
            <div className="ph-form-grid"><label>{t("适用范围")}<select name="scope"><option value="today">{t("仅今天")}</option><option value="preference">{t("主人确认的长期偏好")}</option><option value="observation">{t("一般观察")}</option></select></label><label>{t("关联照护")}<select name="activity"><option value="general">{t("一般观察")}</option>{t(Object.entries(CARE).map(([k, v]) => <option key={k} value={k}>{t(v)}</option>))}</select></label></div></fieldset>
            <button disabled={busy || !canWrite}>{t("保存主人记录")}</button>
          </form><small className="ph-form-help">{t("今天的记录只参与今天的建议；长期偏好是主人确认资料，未冒充 AI 提炼记忆。")}</small>
          {t(!!notes.length && <div className="ph-observation-list"><h3>{t("已保存观察 · ")}{t(notes.length)}{t(" 条")}</h3>{t(notes.slice().reverse().map(n => <blockquote key={n.id}>{n.text}<small>{t(n.scope === 'today' ? '仅今天' : n.scope === 'preference' ? '主人确认偏好' : '观察')} · {t(timeText(n.created_at))}</small></blockquote>))}</div>)}
        </section>
        <section className="ph-card ph-diary-editor" aria-label={t(tf("{0} 的日记记录", pet.name))}>
          <p className="ph-eyebrow">{t("把小事留下来")}</p><h2>{t("写一篇成长日记")}</h2><p className="ph-section-intro">{t("文字和照片都属于当前宠物。切换宠物会清空未保存的草稿。")}</p>
          <form key={`diary-${pet.id}`} onSubmit={async e => { e.preventDefault(); const f = e.currentTarget, d = new FormData(f), scope = draftScope.current; if (await save(`/pets/${pet.id}/diary`, { title: value(d, 'title'), text: value(d, 'text'), happened_on: value(d, 'date'), actor_id: actor, photo_id: diaryPhoto })) { f.reset(); if (scope === draftScope.current) setDiaryPhoto(null) } }}>
            <fieldset className="ph-fieldset" disabled={busy || !canWrite}><div className="ph-form-grid"><label>{t("标题")}<input name="title" required maxLength={80} placeholder={t("第一次在新窝睡着")} /></label><label>{t("发生日期")}<input name="date" type="date" required defaultValue={localDate()} /></label></div><label>{t("内容")}<textarea name="text" maxLength={2000} placeholder={t("这一刻发生了什么？")} /></label>
            <label className="ph-diary-upload">{t("日记照片")}<input type="file" accept="image/png,image/jpeg" disabled={busy || !canWrite} onChange={async e => { const scope = draftScope.current; setBusy(true); try { const id = await upload(e.target.files?.[0]); if (scope === draftScope.current) setDiaryPhoto(id) } catch (err) { if (scope === draftScope.current) failure(err) } finally { if (scope === draftScope.current) setBusy(false) } }} /></label></fieldset>
            {t(diaryPhoto && <img className="ph-diary-photo" src={photoUrl(diaryPhoto)} alt={t("日记照片预览")} />)}<button disabled={busy || !canWrite}>{t("保存日记")}</button>
          </form>
        </section>
      </div>
      <section className="ph-card ph-timeline-card"><div className="ph-card-title"><div><p className="ph-eyebrow">{t("每一件小事都有日期")}</p><h2>{t("成长时间线")}</h2></div><span className="ph-tag">{t(diary.length)}{t(" 篇日记")}</span></div>{t(pet.birthday && <p className="ph-note">{t("生日：")}{t(pet.birthday)}{t(" · 当前约 ")}{t(age)}{t(" 岁")}</p>)}<div className="ph-weekly"><h3>{t("本周记录摘要")}</h3><p>{insight ? serverText(insight.weekly.text) : t('正在读取已保存记录…')}</p><small>{t("仅统计已保存的实际记录")}</small></div>{t(diary.slice().sort((a, b) => b.happened_on.localeCompare(a.happened_on)).map(d => <article className="ph-diary" key={d.id}><small>{t(d.happened_on)} · {d.author_name ? actorName(d.author_name, d.actor_id) : memberName(d.actor_id)}</small><h3>{d.title}</h3><p>{d.text}</p>{t(d.photo_id && <img loading="lazy" src={photoUrl(d.photo_id)} alt={d.title} />)}</article>))}{t(!diary.length && <div className="ph-empty-records"><span aria-hidden="true">✦</span><p>{t("还没有日记，记录一张照片或一件小事吧。")}</p><small>{t("每一次保存，都会留在 ")}{pet.name}{t(" 的时间线里。")}</small></div>)}</section>
    </div>)}
    {t(tab === '家庭交接' && <div className="ph-two-columns"><section className="ph-card"><h2>{t("一起照顾 ")}{pet.name}</h2><p>{t("家庭成员使用同一演示登录，记录人是家庭显示名，尚未建立独立账号。")}</p><form onSubmit={async e=>{e.preventDefault();const f=e.currentTarget;if(await save('/members',{name:value(new FormData(f),'name')}))f.reset()}}><label>{t("添加家庭显示名")}<input name="name" required maxLength={40} placeholder={t("例如：姐姐")} /></label><button disabled={busy || !canWrite}>{t("添加照护人")}</button></form><ul>{t(home.members.map(m=><li key={m.id}>{actorName(m.name, m.id)}</li>))}</ul><h3>{t("最近完成的照护")}</h3>{t(insight?.weekly.records.slice().reverse().slice(0,8).map(h=><p key={h.id}>{actorName(h.actor, h.actor_id)} · {serverText(h.text)} · {t(timeText(h.created_at))}</p>))}<small>{t("完成记录来自主人手动操作；自动设备结果在详细信息页查看。")}</small></section><section className="ph-card"><h2>{t("交接记录")}</h2>{t(history.slice(0,100).map(h=><article className="ph-history" key={h.id}><span>{actorName(h.actor, h.actor_id)}</span><p>{serverText(h.text)}</p><small>{t(timeText(h.created_at))}</small></article>))}{t(!history.length && <p>{t("尚无交接记录。")}</p>)}</section></div>)}
    {t(tab === '家庭交接' && pet.id === 'mochi' && <section className="ph-card"><h2>{t("模拟设备回执")}</h2>{t(deviceRuns.filter(r=>r.receipt).map(r=><article className="ph-history" key={r.run_id}><span>{t("已认证主人审批 · 模拟执行器")}</span><p>{t(r.receipt?.status === 'succeeded' ? '成功回执' : r.receipt?.status === 'failed' ? '失败回执' : '未知回执')}{t(r.proposal?.action.kind==='dispense_food'?tf(" · {0} 克", r.proposal.action.grams):'')}</p><small>{t("请求时间：")}{t(timeText(r.created_at))}</small></article>))}</section>)}
  </Container>
}
