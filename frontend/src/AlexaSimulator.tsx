import { t, locale, serverText, chatInput } from "./i18n";
import { useEffect, useRef, useState } from "react";
import { ApiError, request } from "./api";
import type { Pet, Proposal, Reply, Task } from "./family-api";
import "./alexa-simulator.css";

type Turn = { id: string; text: string; quickPrompt?: boolean; reply?: Reply; failed?: boolean };
type Props = {
  pet: Pet;
  householdName: string;
  revision: number;
  tasks: Task[];
  canWrite: boolean;
  onChanged: () => Promise<void>;
  onCare: () => void;
};
const PROMPTS = ["它喜欢什么", "最近体重是多少", "今天有哪些待办", "今天有什么观察", "最近完成了什么", "安排陪玩", "安排换水"];
const CARE: Record<string, string> = { feeding: "人工喂食", water: "换水", play: "陪玩", brush: "梳毛", bath: "洗澡", nails: "剪指甲", clean: "清洁", walk: "散步" };
const localTime = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);
const taskStatus = (task: Task) => task.status === "cancelled" ? t("已取消") : task.completed ? t("主人已记录人工完成") : t("已安排，等待人工完成");

export default function AlexaSimulator({ pet, householdName, revision, tasks, canWrite, onChanged, onCare }: Props) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [session, setSession] = useState(1);
  const [draft, setDraft] = useState<Reply | null>(null);
  const [pending, setPending] = useState<Proposal | null>(null);
  const [result, setResult] = useState<Proposal | null>(null);
  const [due, setDue] = useState(localTime);
  const alive = useRef(false);
  const working = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const log = useRef<HTMLDivElement>(null);
  const canSpeak = typeof window.speechSynthesis !== "undefined" && typeof window.SpeechSynthesisUtterance !== "undefined";
  const scopedTasks = tasks.filter((t) => t.pet_id === pet.id);
  const resultTask = scopedTasks.find((t) => t.id === result?.task_id);
  const expectedVersion = pending?.context_version ?? draft?.context_version;
  const expires = pending?.context_valid_until ?? draft?.context_valid_until;
  const stale = expectedVersion != null && (revision !== expectedVersion || (expires != null && Date.parse(expires) <= Date.now()));

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      controller.current?.abort();
      if (canSpeak) window.speechSynthesis.cancel();
    };
  }, [canSpeak]);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [turns, busy]);

  async function run(action: (signal: AbortSignal) => Promise<void>) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const ctrl = new AbortController();
    controller.current = ctrl;
    try {
      await action(ctrl.signal);
    } catch (e) {
      if (!alive.current || ctrl.signal.aborted) return;
      setError(e instanceof ApiError
        ? e.status === 409 ? "记录已变化或依据已过期，请重新提问并生成新方案。"
          : e.status === 401 ? "会话已过期，请重新登录。"
            : e.status === 403 ? "当前账号没有操作权限，请检查家庭成员权限。"
              : "请求未完成，请检查内容并重试。"
        : "连接失败，请重试。任务状态请以照护页为准。");
      if (e instanceof ApiError && [401, 403].includes(e.status)) await onChanged();
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }

  function send(text: string, quickPrompt = false) {
    const value = text.trim();
    if (!value || !canWrite || working.current) return;
    const id = crypto.randomUUID();
    setInput("");
    setDraft(null);
    setPending(null);
    setTurns((old) => [...old.slice(-19), { id, text: value, quickPrompt }]);
    void run(async (signal) => {
      try {
        const reply = await request<Reply>(`/api/family/pets/${pet.id}/chat`, {
          method: "POST", body: JSON.stringify({ text: chatInput(value), entry: "alexa_simulator" }), signal,
        });
        if (!alive.current || signal.aborted) return;
        setTurns((old) => old.map((t) => t.id === id ? { ...t, reply } : t));
        setDraft(reply.care_draft ? reply : null);
        setDue(localTime());
        await onChanged();
      } catch (e) {
        if (alive.current && !signal.aborted) {
          setTurns((old) => old.map((t) => t.id === id ? { ...t, failed: true } : t));
          setInput(value);
        }
        throw e;
      }
    });
  }

  function prepare() {
    if (!draft?.care_draft || !due) return;
    void run(async (signal) => {
      const proposal = await request<Proposal>(`/api/family/pets/${pet.id}/proposals`, {
        method: "POST", signal, body: JSON.stringify({
          ...draft.care_draft, due_at: new Date(due).toISOString(),
          context_version: draft.context_version, context_valid_until: draft.context_valid_until,
        }),
      });
      if (!alive.current || signal.aborted) return;
      setPending(proposal);
      setDraft(null);
      await onChanged();
    });
  }

  function confirm() {
    if (!pending) return;
    void run(async (signal) => {
      const proposal = await request<Proposal>(`/api/family/pets/${pet.id}/proposals/${pending.id}/confirm`, {
        method: "POST", signal, body: JSON.stringify({ version: pending.version, context_version: pending.context_version }),
      });
      if (!alive.current || signal.aborted) return;
      setResult(proposal);
      setPending(null);
      setNotice("已安排人工照护；等待家人实际完成并记录。");
      await onChanged();
    });
  }

  function newSession() {
    if (working.current) return;
    if (canSpeak) window.speechSynthesis.cancel();
    setTurns([]); setDraft(null); setPending(null); setResult(null);
    setInput(""); setError(""); setSession((n) => n + 1);
    setNotice("已开始新会话。家庭档案、确认记忆和照护任务仍保留。");
  }

  function speak(text: string) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(serverText(text));
    utterance.lang = locale();
    utterance.onerror = () => { if (alive.current) setNotice("浏览器未能朗读，可以直接阅读回复。"); };
    window.speechSynthesis.speak(utterance);
  }

  return <section className="alexa-simulator" aria-label={t("Alexa 网页模拟体验")}>
    <header className="alx-header">
      <div><p className="alx-eyebrow">PAWTWIN × ALEXA+ CONCEPT</p><h2>{t("Alexa+ 网页模拟器")}</h2><p>{t("从一句话，到一起完成的小事。")}</p></div>
      <button className="fa-secondary" disabled={busy} onClick={newSession}>{t("新会话")}</button>
    </header>
    <p className="alx-boundary">{t("文字输入模拟口述 · App 共用家庭后端 · 真实 Alexa 平台和设备未连接")}</p>
    <div className="alx-layout">
      <aside className="alx-device" aria-label={t("当前模拟设备与宠物")}>
        <div className={`alx-orb ${busy ? "alx-orb--busy" : ""}`} aria-hidden="true"><span /></div>
        <p className="alx-device-state">{busy ? t("正在读取与核对…") : t("准备好了，聊聊它的今天。")}</p>
        <h3>{pet.name}</h3><p>{householdName}</p>
        <dl><div><dt>{t("当前上下文")}</dt><dd>{t("版本")} {revision}</dd></div><div><dt>{t("回答来源")}</dt><dd>{t("家庭档案与主人记录")}</dd></div><div><dt>{t("操作方式")}</dt><dd>{t("确认后安排人工照护")}</dd></div></dl>
        <button className="fa-secondary" onClick={onCare}>{t("查看照护任务")}</button>
        <a href="#app">{t("返回家庭应用 ↗")}</a>
      </aside>
      <div className="alx-conversation">
        <div className="alx-session"><span>{t("本页会话")} {session}</span><span>{t("最多保留 20 轮")}</span></div>
        <div className="alx-log" role="log" aria-label={t("Alexa 模拟对话")} aria-live="polite" aria-relevant="additions text" ref={log}>
          {!turns.length && <div className="alx-empty"><span aria-hidden="true">✦</span><h3>{t("“它喜欢什么？”")}</h3><p>{t("试试快捷提问，或输入照护需求。每轮读取当前宠物的最新记录；本页对话在离开或刷新后清空。")}</p></div>}
          {turns.map((turn) => <div className="alx-turn" key={turn.id}>
            <div className="alx-user"><small>{t("你 · 模拟口述")}</small><p>{turn.quickPrompt ? t(turn.text) : turn.text}</p></div>
            {turn.reply && <article className="alx-reply" aria-label={t("Alexa 分身回复")}><small>{t("Alexa 网页模拟 ·")} {turn.reply.backend === "bedrock" ? t("Bedrock 模型回答") : t("本地规则")}</small><p>{serverText(turn.reply.answer)}</p>
              <details><summary>{t("查看这轮依据 · 版本")} {turn.reply.context_version}</summary><p>{t("源记录：")}{turn.reply.source_record_ids.join(t("、", ", ")) || t("暂无相关记录")}</p><p>{t("历史回复保留当时的记录；新提问会重新读取。未执行动作。")}</p><p>{t("真实模型请求：")}{turn.reply.request_id || t("无")}</p>{turn.reply.model_id && <p>{t("模型：")}{turn.reply.model_id} {t("· 输入")} {turn.reply.input_tokens} {t("/ 输出")} {turn.reply.output_tokens} tokens</p>}</details>
              {canSpeak && <button className="fa-secondary alx-read" onClick={() => speak(turn.reply!.answer)}>{t("浏览器朗读这条回复")}</button>}
            </article>}
            {turn.failed && <p className="alx-failed">{t("这轮未获得回复，内容已放回输入框，可重新发送。")}</p>}
          </div>)}
          {busy && <p className="alx-working" role="status">{t("正在处理，请稍候…")}</p>}
        </div>
        <div className="alx-prompts" aria-label={t("快捷模拟口述")}>{PROMPTS.map((prompt) => <button className="fa-secondary" key={prompt} disabled={busy || !canWrite} onClick={() => send(prompt, true)}>{t(prompt)}</button>)}</div>
        <form className="alx-compose" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <label>{t("模拟口述内容")}<textarea value={input} onChange={(e) => setInput(e.target.value)} required maxLength={2000} disabled={busy || !canWrite} placeholder={t("例如：安排陪玩 / 今天有哪些待办")} rows={2} /></label>
          <button disabled={busy || !canWrite || !input.trim()}>{t("发送给 Alexa 模拟器")}</button>
        </form>
        {!canWrite && <p className="alx-failed">{t("访客为只读权限，不能发起对话或安排照护。")}</p>}
        <p className="alx-help">{t("回答后端和请求依据会显示在每轮回复中。“安排”类指令仅生成草案；本页不采集麦克风。")}</p>
        {error && <p role="alert" className="fa-error">{t(error)}</p>}
        {notice && <p role="status" className="fa-notice">{t(notice)}</p>}
        {draft?.care_draft && <section className="alx-action" aria-label={t("待确认照护草案")}><p className="alx-eyebrow">{t("01 · 查看草案")}</p><h3>{serverText(draft.care_draft.title)}</h3><p>{t(CARE[draft.care_draft.kind])} {t("· 尚未创建任务")}</p><form onSubmit={(e) => { e.preventDefault(); prepare(); }}><label>{t("草案照护时间")}<input type="datetime-local" required value={due} onChange={(e) => setDue(e.target.value)} /></label><p>{t("按此浏览器的本地时区显示。请核对具体日期与时间。")}</p><button disabled={busy || !canWrite}>{t("准备待确认方案")}</button><button type="button" className="fa-secondary" disabled={busy} onClick={() => setDraft(null)}>{t("放弃草案")}</button></form></section>}
        {pending && <section className="alx-action" aria-label={t("待确认照护方案")}><p className="alx-eyebrow">{t("02 · 明确确认")}</p><h3>{serverText(pending.title)}</h3><p>{t(CARE[pending.kind])} · {new Date(pending.due_at).toLocaleString(locale())}</p><p>{t("确认后创建一项人工照护任务。安排不代表完成；不会触发设备。")}</p><button disabled={busy || !canWrite || stale} onClick={confirm}>{t("确认安排人工照护")}</button><button className="fa-secondary" disabled={busy} onClick={() => setPending(null)}>{t("暂不安排")}</button></section>}
        {stale && <p className="alx-failed">{t("依据已变化或过期，请重新提问。原方案不能直接确认。")}</p>}
        {result && <section className="alx-action alx-result" aria-label={t("照护结果")}><p className="alx-eyebrow">{t("03 · 家庭接力")}</p><h3>{serverText(result.title)}</h3><p>{resultTask ? taskStatus(resultTask) : t("已确认，请到照护页核对最新任务状态")}</p><button className="fa-secondary" onClick={onCare}>{t("查看照护任务")}</button></section>}
      </div>
    </div>
  </section>;
}
