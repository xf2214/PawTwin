import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, getRun, getState, hasCsrf, postApproval, postEvent, request, type FactsView, type RunView } from './api'
import './pet-home.css'

type Species = 'cat' | 'dog'
type Coat = 'gold' | 'gray' | 'cream' | 'black' | 'white'
type Care = 'feeding' | 'water' | 'play' | 'brush' | 'bath' | 'nails' | 'clean' | 'walk'
type Pet = { id: string; name: string; species: Species; breed: string; gender: string;
  birthday: string | null; age_years: number | null; coat: Coat; pattern: string; size: string;
  likes: string; dislikes: string; photo_id: string | null; source: string }
type Member = { id: string; name: string }
type Item = { id: string; pet_id: string; kind: 'nest' | 'toy' | 'water' | 'feeder'; name: string;
  x: number; y: number; note: string }
type Task = { id: string; pet_id: string; kind: Care; title: string; due_at: string;
  interval_days: number | null; assigned_to: string | null; completed: boolean;
  last_completed_at: string | null }
type Note = { id: string; pet_id: string; text: string; scope: string; activity: string;
  actor_id: string; created_at: string }
type Diary = { id: string; pet_id: string; title: string; text: string; happened_on: string;
  actor_id: string; photo_id: string | null }
type Entry = { id: string; pet_id: string; actor: string; text: string; created_at: string }
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
const timeText = (value: string) => new Date(value).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
const value = (form: FormData, key: string) => String(form.get(key) ?? '').trim()
const defaultPet: Omit<Pet, 'id' | 'source'> = { name: '', species: 'cat', breed: '', gender: 'unknown',
  birthday: null, age_years: null, coat: 'gold', pattern: 'solid', size: 'medium', likes: '', dislikes: '', photo_id: null }

function PixelPet({ pet, small = false }: { pet: Pet; small?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const c = ref.current?.getContext('2d'); if (!c) return
    c.clearRect(0, 0, 64, 64)
    const palette: Record<Coat, [string, string]> = { gold: ['#e2b36a', '#f9d897'], gray: ['#89969c', '#cad1d2'],
      cream: ['#cbbf9e', '#f2e7ce'], black: ['#3f4b48', '#76847e'], white: ['#c2cbc5', '#f5f5e8'] }
    const [coat, light] = palette[pet.coat] ?? palette.gold
    const r = (x: number, y: number, w: number, h: number, color: string) => { c.fillStyle = color; c.fillRect(x, y, w, h) }
    r(12, 54, 43, 4, '#253c3028'); r(19, 29, 27, 26, coat); r(24, 34, 17, 17, light)
    r(18, 51, 12, 6, light); r(37, 51, 12, 6, light); r(10, 42, 12, 5, coat); r(8, 34, 5, 12, coat)
    r(15, 13, 36, 23, light); r(17, 5, 9, 14, coat); r(40, 5, 9, 14, coat)
    r(19, 8, 4, 7, '#c28d78'); r(42, 8, 4, 7, '#c28d78')
    if (pet.species === 'dog') { r(10, 15, 9, 21, coat); r(48, 15, 9, 21, coat); r(25, 27, 16, 11, '#eee0c2') }
    if (pet.pattern === 'stripes') { r(28, 14, 3, 7, coat); r(35, 14, 3, 7, coat); r(19, 36, 6, 3, light); r(40, 40, 6, 3, light) }
    if (pet.pattern === 'spots') { r(17, 15, 12, 9, coat); r(36, 39, 8, 9, light) }
    r(22, 24, 4, 5, '#25392f'); r(40, 24, 4, 5, '#25392f'); r(31, 29, 4, 3, '#a47b60')
    r(29, 34, 3, 2, '#715e4d'); r(35, 34, 3, 2, '#715e4d')
  }, [pet])
  return <canvas ref={ref} width={64} height={64} className={small ? 'ph-pixel small' : `ph-pixel ${pet.size}`}
    role="img" aria-label={`${pet.name} 的${COATS[pet.coat]}像素形象`} />
}

function Room({ pet, items, run, onItem }: { pet: Pet; items: Item[]; run: RunView | null;
  onItem: (item: Item) => void }) {
  return <div className="ph-room" aria-label="2D 俯视小屋 · 位置为展示布局">
    <div className="ph-window" /><div className="ph-sofa"><i /><i /><i /></div>
    <div className="ph-rug" /><div className="ph-table" /><div className="ph-plant">✦</div>
    <div className="ph-kitchen"><div className="ph-counter" /></div>
    <span className="ph-room-label">客厅</span><span className="ph-room-label kitchen">喂食区</span>
    {items.map(item => <button type="button" key={item.id} className={`ph-object ${item.kind}`}
      style={{ left: `${item.x}%`, top: `${item.y}%` }} onClick={() => onItem(item)} aria-label={`查看${item.name}`}>
      <span className="ph-object-art" aria-hidden="true" /><span className="ph-object-name">{item.name}</span>
    </button>)}
    <div className={`ph-character ${run?.state === 'succeeded' ? 'near-feeder' : ''}`}>
      <div className="ph-speech">{run?.state === 'awaiting_approval' ? '等待主人确认' : run?.state === 'succeeded' ? '已收到模拟成功回执' : `${pet.name} 的小屋`}</div>
      <PixelPet pet={pet} />
    </div>
  </div>
}

export default function PetHome({ onLogout }: { onLogout: () => void }) {
  const [home, setHome] = useState<Home | null>(null), [selected, setSelected] = useState(() => sessionStorage.getItem('pawtwin-home-pet') ?? 'mochi')
  const [tab, setTab] = useState('小屋'), [actor, setActor] = useState('')
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState<Pet | null | undefined>(undefined)
  const [formPet, setFormPet] = useState(defaultPet), [draftMessage, setDraftMessage] = useState('')
  const [itemEdit, setItemEdit] = useState<Item | null>(null), [kind, setKind] = useState<Care>('water')
  const [insight, setInsight] = useState<Insights | null>(null), [insightActivity, setInsightActivity] = useState<Care>('play')
  const [run, setRun] = useState<RunView | null>(null), [diaryPhoto, setDiaryPhoto] = useState<string | null>(null)
  const [deviceRuns, setDeviceRuns] = useState<RunView[]>([])
  const [feedingFacts, setFeedingFacts] = useState<FactsView | null>(null)
  const [postponing, setPostponing] = useState(''), [postponeTime, setPostponeTime] = useState(localTime())
  const pet = home?.pets.find(p => p.id === selected) ?? home?.pets[0]
  const canWrite = hasCsrf()

  function failure(err: unknown) {
    if (err instanceof ApiError) { try { setError(JSON.parse(err.message).detail ?? err.message) } catch { setError(err.message) } }
    else setError('无法完成操作，请检查连接后重试。')
  }
  const refresh = useCallback(async () => {
    try { const data = await request<Home>('/api/home/state'); setHome(data); setActor(a => a || data.members[0]?.id || '') }
    catch (e) { failure(e) }
  }, [])
  useEffect(() => { void refresh() }, [refresh])
  useEffect(() => {
    if (!pet) return
    let valid = true
    setInsight(null)
    request<Insights>(`/api/home/pets/${pet.id}/insights?activity=${insightActivity}`).then(x => { if (valid) setInsight(x) }).catch(failure)
    return () => { valid = false }
  }, [pet, home, insightActivity])
  useEffect(() => { sessionStorage.setItem('pawtwin-home-pet', selected); setRun(null); setItemEdit(null); setEditing(undefined); setDiaryPhoto(null); setError(''); setNotice('') }, [selected])
  useEffect(() => {
    if (pet?.id !== 'mochi') { setDeviceRuns([]); setFeedingFacts(null); return }
    let alive = true
    getState().then(snapshot => { if (alive) { setDeviceRuns(snapshot.runs); setFeedingFacts(snapshot.facts); setRun(old => old ?? snapshot.runs[0] ?? null) } }).catch(failure)
    return () => { alive = false }
  }, [pet?.id, run?.state])
  useEffect(() => {
    if (!run || !['queued', 'analyzing', 'executing'].includes(run.state)) return
    let alive = true, timer: ReturnType<typeof setTimeout>
    const poll = async () => { try { const updated = await getRun(run.run_id); if (alive) { setRun(updated); if (['queued', 'analyzing', 'executing'].includes(updated.state)) timer = setTimeout(poll, 1000) } } catch (e) { if (alive) failure(e) } }
    timer = setTimeout(poll, 1000)
    return () => { alive = false; clearTimeout(timer) }
  }, [run])

  async function save(path: string, body: object, method = 'POST') {
    setBusy(true); setError(''); setNotice('')
    try { const next = await request<Home>(`/api/home${path}`, { method, body: JSON.stringify(body) }); setHome(old => ({ ...old, ...next })); setNotice('已保存'); return true }
    catch (e) { failure(e); return false } finally { setBusy(false) }
  }
  async function upload(file: File | undefined): Promise<string | null> {
    if (!file) return null
    if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 3 * 1024 * 1024) { setError('请选择不超过 3 MB 的 JPG 或 PNG 照片。'); return null }
    const data = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = reject; reader.readAsDataURL(file) })
    return (await request<{ id: string }>('/api/home/photos', { method: 'POST', body: JSON.stringify({ data_url: data }) })).id
  }
  async function profilePhoto(file: File | undefined) {
    setBusy(true); setError('')
    try {
      const id = await upload(file); if (!id) return
      setFormPet(p => ({ ...p, photo_id: id })); setDraftMessage('照片已保存，可以手动确认资料。')
      if (home?.photo_recognition_enabled) {
        const data = await request<{ draft: Partial<Pet> & { uncertainty: string }; request_id: string }>(`/api/home/photos/${id}/recognize`, { method: 'POST' })
        setFormPet(p => ({ ...p, species: data.draft.species ?? p.species, breed: data.draft.breed ?? p.breed,
          coat: data.draft.coat ?? p.coat, pattern: data.draft.pattern ?? p.pattern }))
        setDraftMessage(`识别草稿，保存前请确认：${data.draft.uncertainty || '品种仅为候选；年龄与喜好需要主人填写。'}`)
      } else setDraftMessage('照片已保存；当前未启用自动识别，请手动填写资料。')
    } catch (e) { failure(e) } finally { setBusy(false) }
  }
  function openPet(p: Pet | null) { setEditing(p); setFormPet(p ? { ...p } : { ...defaultPet }); setDraftMessage(''); setTab('档案与物品') }
  async function sendFood() {
    setBusy(true); setError('')
    try { const result = await postEvent('food_request', 'kitchen'); setRun(await getRun(result.run_id)) }
    catch (e) { failure(e) } finally { setBusy(false) }
  }
  async function approve(decision: 'approve' | 'decline') {
    if (!run?.action_digest) return
    setBusy(true)
    try { await postApproval(run.run_id, { decision, proposal_version: run.proposal_version, action_digest: run.action_digest }); setRun(await getRun(run.run_id)); await refresh() }
    catch (e) { failure(e) } finally { setBusy(false) }
  }
  async function taskAction(task: Task, action: 'complete' | 'postpone') {
    if (await save(`/tasks/${task.id}/action`, { event_id: crypto.randomUUID(), actor_id: actor, action,
      next_due: action === 'postpone' ? new Date(postponeTime).toISOString() : null })) setPostponing('')
  }
  if (!home || !pet) return <main className="pet-home"><h1>宠物小屋</h1><p>{error || '正在打开小屋…'}</p><a href="#workbench">返回详细信息</a></main>
  const items = home.objects.filter(o => o.pet_id === pet.id), tasks = home.tasks.filter(t => t.pet_id === pet.id)
  const notes = home.notes.filter(n => n.pet_id === pet.id), diary = home.diary.filter(d => d.pet_id === pet.id)
  const history = home.history.filter(h => h.pet_id === pet.id).slice().reverse()
  const age = pet.birthday ? Math.max(0, (Date.now() - new Date(pet.birthday).getTime()) / 31557600000).toFixed(1) : pet.age_years
  const pendingTasks = tasks.filter(t => !t.completed && new Date(t.due_at).getTime() <= Date.now())
  const memberName = (id: string | null) => home.members.find(m => m.id === id)?.name ?? '未分配'

  function taskCard(task: Task) {
    const waiting = task.completed || (!!task.last_completed_at && new Date(task.due_at).getTime() > Date.now())
    return <article className={`ph-task ${waiting ? 'done' : ''}`} key={task.id}>
      <div><strong>{task.title}</strong><span className="ph-tag">{CARE[task.kind]}</span></div>
      <p>{task.completed ? '已完成' : `计划：${timeText(task.due_at)}`} · {memberName(task.assigned_to)}{task.interval_days ? ` · 每 ${task.interval_days} 天` : ''}</p>
      {task.last_completed_at && <small>最近完成：{timeText(task.last_completed_at)}</small>}
      {!waiting && <div className="ph-actions"><button disabled={busy || !canWrite} onClick={() => void taskAction(task, 'complete')}>标记完成</button><button className="ph-secondary" onClick={() => { setPostponing(task.id); setPostponeTime(localTime()) }}>延期</button></div>}
      {postponing === task.id && <div className="ph-actions"><label>延期到<input type="datetime-local" aria-label="延期时间" value={postponeTime} onChange={e => setPostponeTime(e.target.value)} /></label><button disabled={busy || !canWrite || !postponeTime} onClick={() => void taskAction(task, 'postpone')}>保存延期</button></div>}
    </article>
  }

  return <main className="pet-home">
    <header className="ph-header"><div><p className="ph-eyebrow">PAWTWIN · YOUR PET, YOUR HOME</p><h1>{pet.name} 的小屋</h1></div><div className="ph-header-actions"><a href="#workbench">详细信息</a><button className="ph-secondary" onClick={onLogout}>退出</button></div></header>
    <div className="ph-toolbar"><label>当前宠物<select value={pet.id} onChange={e => setSelected(e.target.value)}>{home.pets.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><button disabled={!canWrite} onClick={() => openPet(null)}>＋ 添加宠物</button><label>记录人<select value={actor} onChange={e => setActor(e.target.value)}>{home.members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></label><span className="ph-boundary">本机保存 · 小屋位置为模拟 · 执行器为模拟</span></div>
    <nav className="ph-tabs" aria-label="小屋功能">{['小屋', '档案与物品', '照护计划', '成长日记', '家庭交接'].map(t => <button key={t} className={tab === t ? 'active' : ''} aria-pressed={tab === t} onClick={() => setTab(t)}>{t}</button>)}</nav>
    {error && <p role="alert" className="ph-error">{error}</p>}{notice && <p role="status" className="ph-notice">{notice}</p>}
    {tab === '小屋' && pet.id === 'mochi' && feedingFacts && <div className="ph-facts-bar"><span>上次喂食距今：{feedingFacts.last_fed_minutes_ago == null ? '未知' : `${feedingFacts.last_fed_minutes_ago} 分钟`}</span><span>当日已出粮：{feedingFacts.daily_dispensed_grams == null ? '未知' : feedingFacts.daily_dispensed_grams} / {feedingFacts.daily_limit_grams} 克</span><span>数据来自当前模拟照护记录</span></div>}
    {!canWrite && <p className="ph-error">当前可以查看资料。请退出后重新登录，恢复编辑和确认操作。</p>}
    {tab === '小屋' && <div className="ph-layout">
      <section className="ph-card ph-scene-card"><div className="ph-card-title"><h2>家里的日常</h2><span className="ph-tag">2D 俯视房间 · 正面像素宠物</span></div><Room pet={pet} items={items} run={run} onItem={item => { setItemEdit(item); setTab('档案与物品') }} />
        <div className="ph-scene-footer">{items.map(item => <button className="ph-secondary" key={item.id} onClick={() => { setItemEdit(item); setTab('档案与物品') }}>{item.name}</button>)}<button className="ph-secondary" onClick={() => setTab('档案与物品')}>布置小屋</button></div>
        <div className="ph-home-summary"><h3>今天待办 · {pendingTasks.length} 项</h3>{pendingTasks.slice(0, 3).map(taskCard)}{!pendingTasks.length && <p>今天暂时没有到期任务。可以安排洗澡、剪指甲、陪玩或换水。</p>}<button className="ph-secondary" onClick={() => setTab('照护计划')}>管理照护计划</button></div>
      </section>
      <aside className="ph-side"><section className="ph-card"><div className="ph-profile-heading"><PixelPet pet={pet} small /><div><h2>{pet.name}</h2><p>{pet.species === 'cat' ? '猫咪' : '狗狗'} · {pet.breed || '品种未填'} · {age == null ? '年龄未填' : `${age} 岁`}</p></div>{pet.photo_id && <img className="ph-avatar" src={photoUrl(pet.photo_id)} alt={`${pet.name} 的照片`} />}</div><p>喜好：{pet.likes || '还没告诉我'}</p><p>不喜欢：{pet.dislikes || '尚未记录'}</p><button className="ph-secondary" onClick={() => openPet(pet)}>编辑档案</button></section>
        <section className="ph-card"><h2>照护建议</h2><label>照护场景<select value={insightActivity} onChange={e => setInsightActivity(e.target.value as Care)}>{Object.entries(CARE).map(([k, label]) => <option key={k} value={k}>{label}</option>)}</select></label><p>{insight?.suggestion || '正在读取主人记录…'}</p><small>依据主人资料的规则建议 · 不表示模型识别了宠物心理</small>{insight?.evidence.map(n => <blockquote key={n.id}>{n.text}<small>{n.scope === 'today' ? '仅今天' : n.scope === 'preference' ? '主人确认偏好' : '主人观察'}</small></blockquote>)}{pet.dislikes && <p className="ph-note">请留意主人记录：{pet.dislikes}</p>}<button className="ph-secondary" onClick={() => setTab('成长日记')}>补充观察与偏好</button></section>
        <section className="ph-card"><h2>喂食请求</h2>{pet.id === 'mochi' ? <><p>沿用现有审批与配额检查，成功回执后才表现完成。</p><button disabled={busy || !canWrite || (!!run && ['queued', 'analyzing', 'awaiting_approval', 'executing'].includes(run.state))} onClick={() => void sendFood()}>发送模拟吃饭请求</button>{run && <div className="ph-run" aria-live="polite"><p>任务：{({ awaiting_approval: '等待主人确认', succeeded: '模拟执行成功', declined: '已拒绝', blocked: '策略已阻止', analyzing: '分析中', queued: '排队中', executing: '执行中', needs_info: '信息不足', expired: '已过期', failed: '执行失败', unknown: '结果未知' })[run.state]}</p><p>{run.proposal?.explanation || run.policy_reason || run.failure_reason}</p>{run.proposal?.action.kind === 'dispense_food' && <p>本次建议：{run.proposal.action.grams} 克</p>}{run.state === 'awaiting_approval' && <div className="ph-actions"><button disabled={busy || !canWrite} onClick={() => void approve('approve')}>批准本次动作</button><button className="ph-secondary" disabled={busy || !canWrite} onClick={() => void approve('decline')}>拒绝</button></div>}</div>}</> : <p>这只宠物尚未接入自动喂食策略。可以在照护计划中记录人工喂食，不会调用其他宠物的设备或额度。</p>}</section>
      </aside>
    </div>}
    {tab === '档案与物品' && <>
      {editing !== undefined && <section className="ph-card"><h2>{editing ? '编辑宠物档案' : '认识一位新伙伴'}</h2><p>名字和种类就能建档，其他资料可以以后补充。</p>
        <div className="ph-photo-setup">{formPet.photo_id && <img src={photoUrl(formPet.photo_id)} alt="宠物建档照片" />}<PixelPet pet={{ ...formPet, id: 'preview', source: 'draft' }} /><div><label className="ph-upload">上传照片<input type="file" accept="image/png,image/jpeg" disabled={busy || !canWrite} onChange={e => void profilePhoto(e.target.files?.[0])} /></label><label className="ph-upload">拍照<input type="file" accept="image/png,image/jpeg" capture="environment" disabled={busy || !canWrite} onChange={e => void profilePhoto(e.target.files?.[0])} /></label><small>JPG / PNG，最多 3 MB。{home.photo_recognition_enabled ? '识别结果需主人确认。' : '自动识别未启用；可以手动填写。'}</small><p role="status">{draftMessage}</p></div></div>
        <form onSubmit={async e => { e.preventDefault(); const { id: _id, source: _source, ...data } = { ...formPet, id: '', source: '' }; void _id; void _source; const oldIds = home.pets.map(p => p.id); if (await save(editing ? `/pets/${editing.id}` : '/pets', data, editing ? 'PUT' : 'POST')) { setEditing(undefined); if (!editing) { const next = await request<Home>('/api/home/state'); setHome(next); const added = next.pets.find(p => !oldIds.includes(p.id)); if (added) setSelected(added.id) } } }}>
          <div className="ph-form-grid"><label>名字 *<input required maxLength={40} value={formPet.name} onChange={e => setFormPet(p => ({ ...p, name: e.target.value }))} /></label><label>种类<select value={formPet.species} onChange={e => setFormPet(p => ({ ...p, species: e.target.value as Species }))}><option value="cat">猫</option><option value="dog">狗</option></select></label><label>品种（候选需确认）<input maxLength={80} value={formPet.breed} onChange={e => setFormPet(p => ({ ...p, breed: e.target.value }))} /></label><label>性别<select value={formPet.gender} onChange={e => setFormPet(p => ({ ...p, gender: e.target.value }))}><option value="unknown">未填写</option><option value="female">母</option><option value="male">公</option></select></label><label>生日<input type="date" max={localDate()} value={formPet.birthday ?? ''} onChange={e => setFormPet(p => ({ ...p, birthday: e.target.value || null }))} /></label><label>年龄（不知道生日时填写）<input type="number" min={0} max={50} step="0.1" value={formPet.age_years ?? ''} onChange={e => setFormPet(p => ({ ...p, age_years: e.target.value === '' ? null : Number(e.target.value) }))} /></label></div>
          <details><summary>像素形象与个体喜好</summary><div className="ph-form-grid"><label>毛色<select value={formPet.coat} onChange={e => setFormPet(p => ({ ...p, coat: e.target.value as Coat }))}>{Object.entries(COATS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select></label><label>花纹<select value={formPet.pattern} onChange={e => setFormPet(p => ({ ...p, pattern: e.target.value }))}><option value="solid">纯色</option><option value="stripes">条纹</option><option value="spots">斑块</option></select></label><label>形象大小<select value={formPet.size} onChange={e => setFormPet(p => ({ ...p, size: e.target.value }))}><option value="small">小</option><option value="medium">中</option><option value="large">大</option></select></label><label>喜欢的食物 / 互动<input maxLength={300} value={formPet.likes} onChange={e => setFormPet(p => ({ ...p, likes: e.target.value }))} /></label><label>不喜欢的事<input maxLength={300} value={formPet.dislikes} onChange={e => setFormPet(p => ({ ...p, dislikes: e.target.value }))} /></label></div></details>
          <div className="ph-actions"><button disabled={busy || !canWrite}>确认并保存档案</button><button type="button" className="ph-secondary" onClick={() => setEditing(undefined)}>取消</button></div>
        </form></section>}
      <section className="ph-card"><div className="ph-card-title"><h2>{pet.name} 的档案与物品</h2><button className="ph-secondary" onClick={() => openPet(pet)}>编辑档案</button></div><Room pet={pet} items={items} run={null} onItem={setItemEdit} />
        <div className="ph-item-list">{items.map(o => <button key={o.id} className="ph-secondary" onClick={() => setItemEdit(o)}>{OBJECTS[o.kind]} · {o.name}</button>)}</div>
        <form key={itemEdit?.id ?? `new-${pet.id}`} onSubmit={async e => { e.preventDefault(); const f = e.currentTarget, d = new FormData(f); if (await save(itemEdit ? `/objects/${itemEdit.id}` : `/pets/${pet.id}/objects`, { kind: value(d, 'kind'), name: value(d, 'name'), x: Number(value(d,'x')), y: Number(value(d,'y')), note: value(d, 'note') }, itemEdit ? 'PUT' : 'POST')) { setItemEdit(null); f.reset() } }}>
          <h3>{itemEdit ? `调整 ${itemEdit.name}` : '添加生活物品'}</h3><div className="ph-form-grid"><label>物品类型<select name="kind" defaultValue={itemEdit?.kind ?? 'nest'}>{Object.entries(OBJECTS).map(([k,v]) => <option value={k} key={k}>{v}</option>)}</select></label><label>名称<input name="name" required maxLength={80} defaultValue={itemEdit?.name ?? ''} placeholder="例如：窗边的小窝、羽毛棒" /></label><label>水平位置<input name="x" type="range" min={8} max={88} defaultValue={itemEdit?.x ?? 25} /></label><label>垂直位置<input name="y" type="range" min={18} max={82} defaultValue={itemEdit?.y ?? 65} /></label><label>使用习惯 / 清洁备注<input name="note" maxLength={300} defaultValue={itemEdit?.note ?? ''} /></label></div><div className="ph-actions"><button disabled={busy || !canWrite}>{itemEdit ? '保存物品与位置' : '添加到小屋'}</button>{itemEdit && <button className="ph-secondary" type="button" onClick={() => setItemEdit(null)}>添加另一个</button>}<button className="ph-secondary" type="button" onClick={() => { setKind(itemEdit?.kind === 'toy' ? 'play' : itemEdit?.kind === 'water' ? 'water' : 'clean'); setTab('照护计划') }}>安排相关照护</button></div>
        </form></section>
    </>}
    {tab === '照护计划' && <div className="ph-two-columns"><section className="ph-card"><h2>安排照护</h2><p>频率由主人决定。洗澡和剪指甲不会自动预设周期。</p><div className="ph-actions">{(['bath','nails','brush','water'] as Care[]).map(k => <button key={k} className="ph-secondary" onClick={() => setKind(k)}>安排{CARE[k]}</button>)}</div>
      <form key={kind} onSubmit={async e => { e.preventDefault(); const f = e.currentTarget, d = new FormData(f); if (await save(`/pets/${pet.id}/tasks`, { kind, title: value(d,'title'), due_at: new Date(value(d,'due')).toISOString(), interval_days: value(d,'interval') ? Number(value(d,'interval')) : null, assigned_to: value(d,'assigned') || null })) f.reset() }}><div className="ph-form-grid"><label>类型<select value={kind} onChange={e => setKind(e.target.value as Care)}>{Object.entries(CARE).map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select></label><label>任务名称<input name="title" required maxLength={80} defaultValue={CARE[kind]} /></label><label>计划时间<input name="due" type="datetime-local" required defaultValue={localTime()} /></label><label>负责照护的人<select name="assigned"><option value="">未分配</option>{home.members.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></label><label>重复间隔（天，留空为一次性）<input name="interval" type="number" min={1} max={365} placeholder="由主人设置" /></label></div><p className="ph-note">“人工喂食”表示主人手动记录，不触发自动出粮。</p><button disabled={busy || !canWrite}>保存照护计划</button></form>
      </section><section className="ph-card"><h2>{pet.name} 的照护清单</h2>{tasks.map(taskCard)}{!tasks.length && <p>还没有照护计划，从一项日常小事开始。</p>}</section></div>}
    {tab === '成长日记' && <div className="ph-two-columns"><section className="ph-card"><h2>主人观察与偏好</h2><form onSubmit={async e => { e.preventDefault(); const f=e.currentTarget,d=new FormData(f); if(await save(`/pets/${pet.id}/notes`,{text:value(d,'text'),scope:value(d,'scope'),activity:value(d,'activity'),actor_id:actor})) f.reset() }}><label>记录原文<textarea name="text" required maxLength={500} placeholder="例如：饭后不想玩 / 喜欢羽毛棒" /></label><div className="ph-form-grid"><label>适用范围<select name="scope"><option value="today">仅今天</option><option value="preference">主人确认的长期偏好</option><option value="observation">一般观察</option></select></label><label>关联照护<select name="activity"><option value="general">一般观察</option>{Object.entries(CARE).map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select></label></div><button disabled={busy || !canWrite}>保存主人记录</button></form><small>今天的记录只参与今天的建议；长期偏好是主人确认资料，未冒充 AI 提炼记忆。</small>{notes.slice().reverse().map(n => <blockquote key={n.id}>{n.text}<small>{n.scope === 'today' ? '仅今天' : n.scope === 'preference' ? '主人确认偏好' : '观察'} · {timeText(n.created_at)}</small></blockquote>)}
      <h2>写一篇成长日记</h2><form onSubmit={async e => { e.preventDefault(); const f=e.currentTarget,d=new FormData(f); if(await save(`/pets/${pet.id}/diary`,{title:value(d,'title'),text:value(d,'text'),happened_on:value(d,'date'),actor_id:actor,photo_id:diaryPhoto})){f.reset();setDiaryPhoto(null)} }}><label>标题<input name="title" required maxLength={80} placeholder="第一次在新窝睡着" /></label><label>发生日期<input name="date" type="date" required defaultValue={localDate()} /></label><label>内容<textarea name="text" maxLength={2000} /></label><label>日记照片<input type="file" accept="image/png,image/jpeg" disabled={busy || !canWrite} onChange={async e => { setBusy(true);try { setDiaryPhoto(await upload(e.target.files?.[0])) } catch(err){failure(err)} finally{setBusy(false)} }} /></label>{diaryPhoto && <img className="ph-diary-photo" src={photoUrl(diaryPhoto)} alt="日记照片预览" />}<button disabled={busy || !canWrite}>保存日记</button></form></section>
      <section className="ph-card"><h2>成长时间线</h2>{pet.birthday && <p className="ph-note">生日：{pet.birthday} · 当前约 {age} 岁</p>}<div className="ph-weekly"><h3>本周记录摘要</h3><p>{insight?.weekly.text}</p><small>仅统计已保存的实际记录</small></div>{diary.slice().sort((a,b)=>b.happened_on.localeCompare(a.happened_on)).map(d => <article className="ph-diary" key={d.id}><small>{d.happened_on} · {memberName(d.actor_id)}</small><h3>{d.title}</h3><p>{d.text}</p>{d.photo_id && <img loading="lazy" src={photoUrl(d.photo_id)} alt={d.title} />}</article>)}{!diary.length && <p>还没有日记，记录一张照片或一件小事吧。</p>}</section></div>}
    {tab === '家庭交接' && <div className="ph-two-columns"><section className="ph-card"><h2>一起照顾 {pet.name}</h2><p>家庭成员使用同一演示登录，记录人是家庭显示名，尚未建立独立账号。</p><form onSubmit={async e=>{e.preventDefault();const f=e.currentTarget;if(await save('/members',{name:value(new FormData(f),'name')}))f.reset()}}><label>添加家庭显示名<input name="name" required maxLength={40} placeholder="例如：姐姐" /></label><button disabled={busy || !canWrite}>添加照护人</button></form><ul>{home.members.map(m=><li key={m.id}>{m.name}</li>)}</ul><h3>最近完成的照护</h3>{insight?.weekly.records.slice().reverse().slice(0,8).map(h=><p key={h.id}>{h.actor} · {h.text} · {timeText(h.created_at)}</p>)}<small>完成记录来自主人手动操作；自动设备结果在详细信息页查看。</small></section><section className="ph-card"><h2>交接记录</h2>{history.slice(0,100).map(h=><article className="ph-history" key={h.id}><span>{h.actor}</span><p>{h.text}</p><small>{timeText(h.created_at)}</small></article>)}{!history.length && <p>尚无交接记录。</p>}</section></div>}
    {tab === '家庭交接' && pet.id === 'mochi' && <section className="ph-card"><h2>模拟设备回执</h2>{deviceRuns.filter(r=>r.receipt).map(r=><article className="ph-history" key={r.run_id}><span>已认证主人审批 · 模拟执行器</span><p>{r.receipt?.status === 'succeeded' ? '成功回执' : r.receipt?.status === 'failed' ? '失败回执' : '未知回执'}{r.proposal?.action.kind==='dispense_food'?` · ${r.proposal.action.grams} 克`:''}</p><small>请求时间：{timeText(r.created_at)}</small></article>)}</section>}
  </main>
}
