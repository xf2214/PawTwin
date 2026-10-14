import { t, locale, serverText, chatInput } from "./i18n";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, request } from "./api";
import { accessRequest, type CareAccessContext, type CareAccessGrant, type CareAccessReply } from "./family-api";
import { CARE, familyTime } from "./family-time";
import { visitDietLabel, visitSource } from "./VisitCard";
import "./care-access.css";

const grantStatus = { active: "有效", expired: "已过期", revoked: "已撤销", pet_archived: "宠物已归档" };
export function CareAccessManager({ petId, petName, timezone, onUnauthorized }: { petId: string; petName: string; timezone: string; onUnauthorized: (status: number) => void }) {
  const [grants, setGrants] = useState<CareAccessGrant[]>([]), [duration, setDuration] = useState("24");
  const [created, setCreated] = useState<{ token: string; grant: CareAccessGrant } | null>(null);
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const live = useRef(true), pending = useRef<AbortController | null>(null), linkInput = useRef<HTMLInputElement>(null);
  const path = `/api/family/pets/${encodeURIComponent(petId)}/care-access`;
  const fail = useCallback((exception: unknown) => {
    if (!live.current || (exception instanceof DOMException && exception.name === "AbortError")) return;
    if (exception instanceof ApiError && [401, 403, 404].includes(exception.status)) { setCreated(null); setGrants([]); setError("管理员或宠物权限已失效，无法管理只读访问。"); if (exception.status !== 404) onUnauthorized(exception.status); }
    else setError("只读访问资料读取失败，请重试。");
  }, [onUnauthorized]);
  const reload = useCallback(async () => {
    pending.current?.abort(); const controller = new AbortController(); pending.current = controller;
    try {
      const result = await request<{ grants: CareAccessGrant[] }>(path, { signal: controller.signal, cache: "no-store" });
      if (!live.current || controller.signal.aborted) return;
      setGrants(result.grants); setError("");
      setCreated(previous => previous && result.grants.some(g => g.id === previous.grant.id && g.status === "active" && Date.parse(g.expires_at) > Date.now()) ? previous : null);
    } catch (exception) { fail(exception); }
    finally { if (live.current && !controller.signal.aborted) setLoading(false); }
  }, [path, fail]);
  useEffect(() => {
    live.current = true; void reload(); const focus = () => void reload(); window.addEventListener("focus", focus); const timer = setInterval(focus, 10000);
    return () => { live.current = false; pending.current?.abort(); clearInterval(timer); window.removeEventListener("focus", focus); };
  }, [reload]);
  useEffect(() => { if (!created) return; const timer = setTimeout(() => setCreated(null), Math.max(0, Date.parse(created.grant.expires_at) - Date.now())); return () => clearTimeout(timer); }, [created]);
  async function create() {
    setBusy(true); setError(""); setNotice(""); setCreated(null);
    try {
      const result = await request<{ token: string; grant: CareAccessGrant }>(path, { method: "POST", body: JSON.stringify({ expires_in_hours: Number(duration) }) });
      if (!live.current) return;
      await reload(); if (live.current) { setCreated(result); setNotice("已授权。请复制此链接；关闭或切换宠物后无法再次查看密钥。"); }
    } catch (exception) { fail(exception); }
    finally { if (live.current) setBusy(false); }
  }
  async function revoke(grant: CareAccessGrant) {
    setBusy(true); setError(""); setNotice("");
    try {
      await request(`${path}/${encodeURIComponent(grant.id)}/revoke`, { method: "POST" });
      if (!live.current) return;
      setCreated(previous => previous?.grant.id === grant.id ? null : previous); await reload(); if (live.current) setNotice("只读访问已撤销，对方再次读取或提问会被拒绝。");
    } catch (exception) { fail(exception); }
    finally { if (live.current) setBusy(false); }
  }
  const link = created ? `${window.location.origin}${window.location.pathname}#pet-access=${encodeURIComponent(created.token)}` : "";
  async function copy() {
    try { if (!navigator.clipboard) throw new Error("clipboard unavailable"); await navigator.clipboard.writeText(link); if (live.current) setNotice("只读链接已复制。"); }
    catch { if (live.current) { linkInput.current?.focus(); linkInput.current?.select(); setNotice("自动复制不可用，链接已选中，请手动复制。"); } }
  }
  return <section className="fa-card ca-manager" aria-label={t("临时只读分身授权")}>
    <div className="ca-section-heading"><div><p className="ca-eyebrow">{t("照护交接 · 指定宠物")}</p><h2>{t("让照护者了解")} {petName}</h2></div><span className="ca-badge">{t("管理员授权 · 只读")}</span></div>
    <p>{t("开放此宠物的档案、偏好与近 7 天照护资料。对方可向本地规则分身提问；不能修改记录、完成任务或操作设备。私人日记、家庭成员与其他宠物不开放。")}</p>
    <div className="ca-create"><label>{t("访问有效期")}<select value={duration} disabled={busy} onChange={event => setDuration(event.target.value)}>{[1, 4, 24, 72].map(hours => <option key={hours} value={hours}>{hours} {t("小时")}</option>)}</select></label><button type="button" disabled={busy} onClick={() => void create()}>{t("授权照护者访问分身")}</button></div>
    {error && <p role="alert" className="ca-error">{t(error)}<button type="button" className="fa-secondary" disabled={busy} onClick={() => void reload()}>{t("重试授权列表")}</button></p>}
    {notice && <p role="status">{t(notice)}</p>}
    {created && <div className="ca-created"><p><strong>{t("仅")} {created.grant.pet_name}</strong> {t("· 有效至")} {familyTime(created.grant.expires_at, timezone)}</p><label>{t("新的只读访问链接")}<input ref={linkInput} value={link} readOnly autoComplete="off" spellCheck={false} /></label><button type="button" className="fa-secondary" onClick={() => void copy()}>{t("复制只读链接")}</button><p>{t("持有链接即可读取授权范围内的资料，请仅交给本次照护者。")}</p></div>}
    <h3>{t("访问记录")}</h3>{loading ? <p role="status">{t("正在读取访问记录…")}</p> : grants.length === 0 ? <p className="fa-subtle">{t("尚未创建只读访问。")}</p> : <ul className="ca-grants">{grants.map(grant => <li key={grant.id}><div><strong>{grant.pet_name} · {t(grantStatus[grant.status])}</strong><p>{t("创建于")} {familyTime(grant.created_at, timezone)}<br />{t("有效至")} {familyTime(grant.expires_at, timezone)}</p></div>{grant.status === "active" && <button type="button" className="fa-secondary" disabled={busy} onClick={() => void revoke(grant)}>{t("撤销只读访问")}</button>}</li>)}</ul>}
  </section>;
}

type Message = { question: string; quickPrompt?: boolean; reply: CareAccessReply };
export default function CareAccess({ token }: { token: string }) {
  const [context, setContext] = useState<CareAccessContext | null>(null), [messages, setMessages] = useState<Message[]>([]), [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const alive = useRef(true), contextRequest = useRef<AbortController | null>(null), chatRequest = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const clear = useCallback((message: string) => { generation.current++; contextRequest.current?.abort(); chatRequest.current?.abort(); setContext(null); setMessages([]); setQuestion(""); setLoading(false); setBusy(false); setError(message); }, []);
  const failure = useCallback((exception: unknown) => {
    if (!alive.current || (exception instanceof DOMException && exception.name === "AbortError")) return;
    clear(exception instanceof ApiError ? exception.status === 401 ? "只读链接无效，请向宠物主人获取新的链接。" : exception.status === 410 ? "只读访问已失效：可能已撤销、到期或宠物已归档。" : exception.status === 429 ? "读取过于频繁，请稍后重试。" : "无法读取此只读资料，请重试。" : "连接失败，已清空本页资料。请检查连接后重试。");
  }, [clear]);
  const refresh = useCallback(async () => {
    contextRequest.current?.abort(); const controller = new AbortController(); contextRequest.current = controller;
    const before = generation.current; setLoading(true);
    try {
      const result = await accessRequest<CareAccessContext>(token, "context", { signal: controller.signal });
      if (!alive.current || controller.signal.aborted || before !== generation.current) return;
      if (Date.parse(result.grant.expires_at) <= Date.now()) { clear("只读访问已失效：授权期限已到。"); return; }
      setContext(result); setError("");
    } catch (exception) { failure(exception); }
    finally { if (alive.current && !controller.signal.aborted) setLoading(false); }
  }, [token, clear, failure]);
  useEffect(() => {
    alive.current = true; void refresh(); const focus = () => void refresh(); window.addEventListener("focus", focus); const timer = setInterval(focus, 10000);
    return () => { alive.current = false; generation.current++; contextRequest.current?.abort(); chatRequest.current?.abort(); clearInterval(timer); window.removeEventListener("focus", focus); };
  }, [refresh]);
  useEffect(() => { if (!context) return; const timer = setTimeout(() => clear("只读访问已失效：授权期限已到。"), Math.max(0, Date.parse(context.grant.expires_at) - Date.now())); return () => clearTimeout(timer); }, [context, clear]);
  async function ask(text: string, quickPrompt = false) {
    if (!context || busy || !text.trim()) return;
    const before = generation.current; const controller = new AbortController(); chatRequest.current = controller; setBusy(true); setError("");
    try {
      const reply = await accessRequest<CareAccessReply>(token, "chat", { method: "POST", body: JSON.stringify({ text: chatInput(text.trim()) }), signal: controller.signal });
      if (alive.current && before === generation.current && !controller.signal.aborted) { setMessages(previous => [...previous.slice(-19), { question: text.trim(), quickPrompt, reply }]); setQuestion(""); }
    } catch (exception) { failure(exception); }
    finally { if (alive.current && before === generation.current) setBusy(false); }
  }
  const time = (value: string) => familyTime(value, context?.timezone ?? "Asia/Shanghai");
  return <main className="ca-visitor">
    <header className="ca-visitor-header"><a href="#product">PawTwin</a><span className="ca-badge">{t("临时授权 · 只读访问")}</span></header>
    <div className="ca-visitor-toolbar"><p>{t("此链接仅用于了解指定宠物的照护资料。分身使用本地规则回答，不提供诊断，不执行操作。")}</p><button type="button" className="ca-secondary" disabled={loading} onClick={() => void refresh()}>{t("刷新授权资料")}</button></div>
    {loading && !context && <p role="status">{t("正在验证只读授权…")}</p>}
    {error && <p role="alert" className="ca-error">{t(error)}</p>}
    {context && <>
      <section className="ca-hero"><p className="ca-eyebrow">{t("给这次照护的一份介绍")}</p><h1>{t(`${context.pet.name} 的只读分身`, `${context.pet.name}’s read-only twin`)}</h1><p>{context.pet.species === "cat" ? t("猫") : context.pet.species === "dog" ? t("狗") : context.pet.species} · {context.pet.breed || t("品种未记录")} · {context.pet.birthday ? `${t("生日")} ${new Date(`${context.pet.birthday}T12:00:00`).toLocaleDateString(locale())}${context.pet.birthday_estimated ? ` ${t("（估计）")}` : ""}` : context.pet.age_years === null ? t("年龄未记录") : `${t("主人手填")} ${context.pet.age_years} ${t("岁")}`}</p><p>{t("资料截至")} {time(context.as_of)} · {context.timezone}<br />{t("访问有效至")} {time(context.grant.expires_at)}</p><p>{serverText(context.label)}</p></section>
      <div className="ca-visitor-grid"><section className="ca-panel"><h2>{t("照护前先了解")}</h2><h3>{t("档案喜好")}</h3><p>{context.pet.likes || t("尚未填写喜好")} {t("· 主人陈述")}</p><p>{t("不喜欢：")}{context.pet.dislikes || t("未记录")}</p><h3>{t("当前确认的偏好")}</h3>{context.preferences.length ? <ul>{context.preferences.map(preference => <li key={preference.id}><p>{preference.text}</p><small>{t("主人确认 · 记录于")} {time(preference.created_at)}{preference.valid_until && ` ${t("· 有效至")} ${time(preference.valid_until)}`}</small></li>)}</ul> : <p>{t("暂无已确认偏好。")}</p>}<h3>{t("近 7 天主人观察")}</h3>{context.observations.length ? <ul>{context.observations.map(observation => <li key={observation.id}><p>{observation.text}</p><small>{t("主人陈述 · 记录于")} {time(observation.created_at)}</small></li>)}</ul> : <p>{t("暂无观察记录。")}</p>}</section>
        <section className="ca-panel"><h2>{t("近 7 天记录与当前计划")}</h2><h3>{t("体重与饮食事实")}</h3>{context.measurements.length ? <ul>{context.measurements.map(measurement => <li key={measurement.id}><strong>{measurement.kind === "weight" ? t("实测体重") : visitDietLabel(measurement.diet_type)} · {measurement.value} {measurement.unit}</strong><p>{measurement.note || t("无备注")}</p><small>{t("测量 / 对应时间")} {time(measurement.measured_at)} · {visitSource(measurement.source)}</small></li>)}</ul> : <p>{t("暂无真实测量或饮食记录，无法推定摄入量。")}</p>}<h3>{t("人工完成记录")}</h3>{context.completed_care.length ? <ul>{context.completed_care.map(care => <li key={care.id}><strong>{care.title} · {t(CARE[care.kind ?? ""] ?? "照护")}</strong><p>{t("实际完成于")} {time(care.completed_at)} {t("· 人工记录")}</p></li>)}</ul> : <p>{t("暂无人工完成记录。")}</p>}<h3>{t("待办计划（尚未完成）")}</h3>{context.tasks.length ? <ul>{context.tasks.map(task => <li key={task.id}><strong>{task.title}</strong><p>{t("计划于")} {time(task.due_at)} · {task.status === "claimed" ? t("已认领") : t("待办")}</p></li>)}</ul> : <p>{t("暂无待办计划。")}</p>}</section></div>
      <section className="ca-panel ca-chat"><h2>{t("向只读分身提问")}</h2><div className="ca-questions">{["它喜欢什么", "最近吃了什么", "最近做了哪些照护", "最近体重是多少"].map(text => <button key={text} type="button" className="ca-secondary" disabled={busy || loading} onClick={() => void ask(text, true)}>{t(text)}</button>)}</div><form onSubmit={event => { event.preventDefault(); void ask(question); }}><label>{t("想了解什么")}<textarea value={question} onChange={event => setQuestion(event.target.value)} maxLength={2000} required /></label><button disabled={busy || loading}>{busy ? t("正在读取…") : t("询问只读分身")}</button></form><div role="log" aria-label={t("只读分身对话")} aria-live="polite">{messages.map((message, index) => <article key={index}><p className="ca-question">{t("你：")}{message.quickPrompt ? t(message.question) : message.question}</p><p>{serverText(message.reply.answer)}</p><small>{t("本地规则 · 未执行任何操作 · 资料截至")} {time(message.reply.as_of)} {t("· 上下文版本")} {message.reply.context_version} {t("· 引用")} {message.reply.source_record_ids.length} {t("条记录")}</small></article>)}</div></section>
    </>}
  </main>;
}
