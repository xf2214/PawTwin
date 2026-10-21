import { t, serverText, chatInput } from "./i18n";
import { actorName, localizeDemoMe } from "./system-defaults";
import { LocalizedInput, storedInputValue } from "./LocalizedInput";
import { useCallback, useEffect, useRef, useState } from "react";
import PetHome from "./PetHome";
import FamilyRecords from "./FamilyRecords";
import FamilyCare from "./FamilyCare";
import FamilyToday from "./FamilyToday";
import { FamilyGrowthOverview, FamilyWeightChart, FamilyReports, FamilyResourceStatus } from "./FamilyGrowth";
import { useFamilyData } from "./family-data";
import { APP_LABELS, APP_TABS, appTab, browserInput, CARE, familyTime } from "./family-time";
import WorkspaceIcon, { type WorkspaceIconName } from "./WorkspaceIcon";
import AlexaSimulator from "./AlexaSimulator";
import VisitCard from "./VisitCard";
import { CareAccessManager } from "./CareAccess";
import { ApiError, logout, request, restoreCsrf } from "./api";
import {
  SOURCE,
  type Home,
  type Me,
  type Measurement,
  type Proposal,
  type Reply,
  type Task,
  type Invitation,
  type Pet,
} from "./family-api";
import "./family-app.css";
import "./family-workspace.css";

const dateInput = browserInput;
const val = (f: FormData, key: string) => String(f.get(key) ?? "").trim();
const AVATARS: Record<string, string> = {
  paw: "🐾",
  cat: "🐱",
  dog: "🐶",
  leaf: "🌿",
  star: "⭐",
};
const NAV_ICONS: Record<string, WorkspaceIconName> = { 小屋: "today", 照护: "care", 成长: "growth", 助手: "twin", 家庭: "family" };

export default function FamilyApp({ alexaMode = false }: { alexaMode?: boolean }) {
  const [storedMe, setMe] = useState<Me | null>(null),
    [home, setHome] = useState<Home | null>(null);
  const me = storedMe ? localizeDemoMe(storedMe) : null;
  const [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false);
  const [tab, setTab] = useState(() => alexaMode ? "Alexa+" : appTab()),
    [petId, setPetId] = useState("mochi");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [register, setRegister] = useState(false);
  const [reply, setReply] = useState<Reply | null>(null),
    [proposal, setProposal] = useState<Proposal | null>(null);
  const [invite, setInvite] = useState(""),
    [kind, setKind] = useState("weight");
  const [editing, setEditing] = useState<Measurement | null>(null),
    [version, setVersion] = useState(0);
  const [growthSection, setGrowthSection] = useState("overview");
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [archivedPets, setArchivedPets] = useState<Pet[]>([]);
  const [focusTarget, setFocusTarget] = useState("");
  const [careIntent, setCareIntent] = useState<string | null>(null);
  const mounted = useRef(true), authenticationPending = useRef(false);
  const seenSession = useRef(false);
  const sessionEpoch = useRef(0), refreshSequence = useRef(0), operationSequence = useRef(0);
  const refreshController = useRef<AbortController | null>(null);
  const invalidateReads = useCallback(() => {
    sessionEpoch.current++;
    refreshSequence.current++;
    refreshController.current?.abort();
    refreshController.current = null;
  }, []);
  const selectPet = useCallback((id: string, expectedPetId?: string) => {
    setPetId(current => expectedPetId === undefined || current === expectedPetId ? id : current);
  }, []);
  const pet = home?.pets.find((p) => p.id === petId) ?? home?.pets[0];
  const timezone = me?.household?.timezone ?? "Asia/Shanghai";
  const timeText = (time: string) => familyTime(time, timezone);
  const unauthorized = useCallback((status: number, showError = true) => {
    invalidateReads();
    if (status === 401) { seenSession.current = false; setMe(null); }
    setHome(null); setInvite(""); setInvitations([]); setArchivedPets([]); setReply(null); setProposal(null); setEditing(null);
    setBusy(false); setLoading(false);
    if (showError) setError(status === 401 ? "会话已过期，请重新登录。" : "家庭权限已发生变化，请重新检查成员权限。");
  }, [invalidateReads]);
  const resources = useFamilyData(me?.household?.household_id, pet?.id, home?.revision ?? 0, version, unauthorized);
  const records = resources.measurements.data, memories = resources.memories.data;
  const latestObservation = home?.notes.filter(note => note.pet_id === pet?.id && note.scope !== "preference").sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];
  useEffect(() => {
    const changed = () => setTab(appTab());
    changed();
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, [alexaMode]);
  useEffect(() => {
    if (tab !== "成长" || focusTarget !== "weight") return;
    const target = document.querySelector<HTMLInputElement>("#family-measurement-form input[name=value]");
    if (target) { target.focus(); target.scrollIntoView({ block: "center" }); setFocusTarget(""); }
  }, [tab, growthSection, focusTarget]);
  const canWrite = me?.membership?.role !== "guest",
    admin = me?.membership?.role === "admin";
  const scope = useRef(""),
    generation = useRef(0);
  const currentScope = `${me?.household?.household_id}:${petId}`;
  if (scope.current !== currentScope) {
    scope.current = currentScope;
    generation.current += 1;
  }
  async function ask(
    path: string,
    body: object,
    setter: (data: Reply) => void,
  ): Promise<void>;
  async function ask(
    path: string,
    body: object,
    setter: (data: Proposal) => void,
  ): Promise<void>;
  async function ask(
    path: string,
    body: object,
    setter: ((data: Reply) => void) | ((data: Proposal) => void),
  ) {
    const before = generation.current;
    const session = sessionEpoch.current;
    const response = await request<Reply & Proposal>(path, {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (mounted.current && session === sessionEpoch.current && before === generation.current) setter({ ...response, presentation_breed: pet?.breed });
  }

  const failure = useCallback((e: unknown) => {
    if (e instanceof ApiError) {
      if (e.status === 401 || e.status === 403) {
        unauthorized(e.status);
        return;
      }
      try {
        const detail = JSON.parse(e.message).detail;
        setError(typeof detail === "string" ? detail : "请检查填写内容。");
      } catch {
        setError(e.message);
      }
    } else setError("连接失败，请检查网络后重试。");
  }, [unauthorized]);
  const refresh = useCallback(async () => {
    if (!mounted.current || authenticationPending.current) return;
    refreshController.current?.abort();
    const controller = new AbortController();
    refreshController.current = controller;
    const sequence = ++refreshSequence.current, session = sessionEpoch.current;
    const current = () => mounted.current && session === sessionEpoch.current && sequence === refreshSequence.current;
    let timedOut = false;
    const timeout = window.setTimeout(() => { if (current()) { timedOut = true; controller.abort(); } }, 15000);
    try {
      // Restore CSRF only after this whole snapshot is still current. A late
      // previous-account /me response must not replace the new account's token.
      const info = await request<Me>("/api/family/me", { signal: controller.signal });
      if (!current() || controller.signal.aborted) return;
      const admin = info.membership?.role === "admin";
      const [nextHome, invitations, archived] = await Promise.all([
        info.household ? request<Home>("/api/home/state", { signal: controller.signal }) : Promise.resolve(null),
        admin ? request<{ invitations: Invitation[] }>("/api/family/invitations", { signal: controller.signal }) : Promise.resolve({ invitations: [] }),
        admin ? request<{ pets: Pet[] }>("/api/family/pets/archived", { signal: controller.signal }) : Promise.resolve({ pets: [] }),
      ]);
      if (!current() || controller.signal.aborted) return;
      restoreCsrf(info.csrf_token);
      seenSession.current = true;
      setMe(info); setHome(nextHome); setInvitations(invitations.invitations); setArchivedPets(archived.pets);
      setError(previous => previous === "连接失败，请检查网络后重试。" ? "" : previous);
    } catch (e) {
      if (!current()) return;
      if (controller.signal.aborted) { if (timedOut) setError("连接失败，请检查网络后重试。"); return; }
      if (e instanceof ApiError && e.status === 401) { unauthorized(401, seenSession.current); return; }
      failure(e);
    } finally {
      window.clearTimeout(timeout);
      if (current()) { setLoading(false); refreshController.current = null; }
    }
  }, [failure, unauthorized]);
  useEffect(() => {
    mounted.current = true;
    void refresh();
    const focus = () => void refresh();
    window.addEventListener("focus", focus);
    const timer = setInterval(() => { if (!refreshController.current) focus(); }, 10000);
    return () => {
      mounted.current = false;
      invalidateReads();
      clearInterval(timer);
      window.removeEventListener("focus", focus);
    };
  }, [refresh, invalidateReads]);
  useEffect(() => {
    if (pet) setPetId(pet.id);
  }, [pet]);
  useEffect(() => {
    setReply(null);
    setProposal(null);
    setEditing(null);
  }, [petId, me?.household?.household_id]);
  useEffect(() => { setInvite(""); }, [me?.user.user_id, me?.household?.household_id]);

  async function act(action: () => Promise<unknown>, message = "已保存") {
    const before = generation.current;
    const session = sessionEpoch.current, operation = ++operationSequence.current;
    const current = () => mounted.current && session === sessionEpoch.current && operation === operationSequence.current;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      if (!current()) return false;
      if (before === generation.current) setNotice(message);
      await refresh();
      if (!current()) return false;
      setVersion((v) => v + 1);
      return true;
    } catch (e) {
      if (current() && before === generation.current) failure(e);
      return false;
    } finally {
      if (current()) setBusy(false);
    }
  }
  const mutate = (path: string, body?: object, method = "POST") =>
    request(path, { method, ...(body ? { body: JSON.stringify(body) } : {}) });
  function sourceSummary(id: string) {
    const careSummary = reply?.care_summary;
    const care = careSummary?.records.find(record => record.id === id);
    if (care && careSummary) {
      // Care citations describe the same snapshot as the answer, even after an
      // editable task has been renamed or a later occurrence has been completed.
      const title = care.title_is_fallback
        ? t("人工照护（历史名称未记录）", "Manual care (historical title not recorded)") : care.title;
      const label = careSummary.kind === "pending"
        ? t("照护计划 · ", "Care plan · ") : t("人工完成记录 · ", "Manual completion record · ");
      return `${label}${title}${care.completed_at ? ` · ${timeText(care.completed_at)}` : ""}`;
    }
    const measurement = records.find(record => record.id === id);
    if (measurement) return `${measurement.kind === "weight" ? t("实测体重") : t("饮食记录")} · ${measurement.value} ${measurement.unit} · ${timeText(measurement.measured_at)} · ${t(SOURCE[measurement.source])}`;
    const note = home?.notes.find(record => record.id === id);
    if (note) return t(`主人记录 · ${note.text} · ${timeText(note.created_at)}`, `Owner record · ${note.text} · ${timeText(note.created_at)}`);
    const memory = memories.find(record => record.id === id);
    if (memory) return t(`偏好记忆 · ${memory.text} · ${memory.status === "confirmed" ? t("主人已确认") : t("未确认")}`, `Preference memory · ${memory.text} · ${memory.status === "confirmed" ? t("主人已确认") : t("未确认")}`);
    const record = home?.diary.find(item => item.id === id);
    if (record) return t(`成长日记 · ${record.title} · ${record.happened_on}`, `Growth diary · ${record.title} · ${record.happened_on}`);
    const task = home?.tasks.find(item => item.id === id);
    if (task) return t(`照护计划 · ${task.title} · ${timeText(task.due_at)}`, `Care plan · ${task.title} · ${timeText(task.due_at)}`);
    const occurrence = home?.occurrences?.find(item => item.id === id);
    if (occurrence) return t(`人工完成记录 · ${timeText(occurrence.completed_at)}`, `Manual completion record · ${timeText(occurrence.completed_at)}`);
    return t("已保存的个体资料；详情请在对应记录中核验");
  }
  function selectTab(name: string) {
    setTab(name);
    if (name !== "照护") setCareIntent(null);
    window.location.hash = name === "Alexa+" ? "alexa" : `app/${APP_TABS[name] ?? "home"}`;
  }
  function navigateCare(kind?: string) {
    setCareIntent(kind ?? null);
    selectTab("照护");
  }
  async function auth(form: HTMLFormElement) {
    const f = new FormData(form);
    invalidateReads();
    setInvite("");
    const session = sessionEpoch.current;
    authenticationPending.current = true;
    await act(async () => {
      try {
        const info = await request<Me>(
          `/api/family/${register ? "register" : "login"}`,
          {
            method: "POST",
            body: JSON.stringify({
              username: val(f, "username"),
              password: val(f, "password"),
              ...(register ? { display_name: val(f, "name") } : {}),
            }),
          },
        );
        if (!mounted.current || session !== sessionEpoch.current) return;
        restoreCsrf(info.csrf_token);
        seenSession.current = true;
        setMe(info); setHome(null);
        form.reset();
      } finally { if (session === sessionEpoch.current) authenticationPending.current = false; }
    }, "已登录本地账号");
  }
  function signOut() {
    invalidateReads();
    seenSession.current = false;
    authenticationPending.current = true;
    setMe(null); setHome(null); setInvite(""); setInvitations([]); setArchivedPets([]); setReply(null); setProposal(null); setEditing(null);
    void act(async () => {
      try { await logout(); } finally { authenticationPending.current = false; }
    }, "已退出");
  }
  const taskAction = (task: Task, action: string, extra: object = {}) =>
    act(() =>
      mutate(`/api/home/tasks/${task.id}/action`, {
        event_id: crypto.randomUUID(),
        version: task.version,
        action,
        ...extra,
      }),
    );

  if (loading)
    return (
      <main className="family-app">
        <p role="status">{t("正在恢复会话…")}</p>
      </main>
    );
  if (!me)
    return (
      <main className="family-app fa-welcome">
        <p className="fa-eyebrow">PAWTWIN · HOME TOGETHER</p>
        <h1>{t("欢迎回到你们的小屋。")}</h1>
        <p>{t("登录后查看宠物近况、接手照护，或记下今天的新变化。")}</p>
        <section className="fa-card">
          <h2>{register ? t("创建本地账号") : t("独立账号登录")}</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void auth(e.currentTarget);
            }}
          >
            <label>{t("账号名")} <input
                name="username"
                required
                minLength={3}
                maxLength={64}
                autoComplete="username"
                pattern="[a-zA-Z0-9_.-]+"
              />
            </label>
            <label>{t("密码")} <input
                name="password"
                type="password"
                required
                minLength={register ? 12 : 1}
                maxLength={128}
                autoComplete={register ? "new-password" : "current-password"}
              />
            </label>
            {register && (
              <label>{t("昵称")} <input name="name" required maxLength={40} />
              </label>
            )}
            <button disabled={busy}>
              {register ? t("注册并登录") : t("登录账号")}
            </button>
          </form>
          <button
            className="fa-secondary"
            onClick={() => setRegister(!register)}
          >
            {register ? t("已有账号，去登录") : t("创建本地账号")}
          </button>
          <p>{t("本地独立账号 · 云认证未接通")}</p>
          <a href="#workbench">{t("原工作台 / 演示登录")}</a>
        </section>
        {error && <p role="alert">{serverText(t(error))}<button type="button" className="fa-secondary" disabled={busy} onClick={() => void refresh()}>{t("重试")}</button></p>}
      </main>
    );

  return (
    <main className="family-app">
      <header className="fa-header">
        <div>
          <p className="fa-eyebrow">PAWTWIN · HOME TOGETHER</p>
          <h1>{me.household?.name ?? t("欢迎回家")}</h1>
        </div>
        <div>
          <button className="fa-secondary" onClick={() => selectTab("家庭")}>
            {me.user.display_name}
          </button>
          <button
            className="fa-secondary"
            onClick={signOut}
          >{t("退出账号")} </button>
        </div>
      </header>
      <p className="fa-boundary">{t("本地独立账号 · 云认证未接通")}</p>
      {error && (
        <p role="alert" className="fa-error">
          {serverText(t(error))}
          <button className="fa-secondary" onClick={() => void refresh()}>{t("重试")} </button>
        </p>
      )}
      {notice && (
        <p role="status" className="fa-notice">
          {t(notice)}
        </p>
      )}
      {!me.household ? (
        <div className="fa-grid">
          <section className="fa-card">
            <h2>{t("建立一个家庭")}</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                void act(() =>
                  mutate("/api/family/households", {
                    name: val(f, "name"),
                    timezone: val(f, "timezone"),
                  }),
                );
              }}
            >
              <label>{t("家庭名称")} <input name="name" required maxLength={80} />
              </label>
              <label>{t("家庭时区")} <input name="timezone" defaultValue="Asia/Shanghai" required />
              </label>
              <button disabled={busy}>{t("创建家庭")}</button>
            </form>
          </section>
          <section className="fa-card">
            <h2>{t("接受家人邀请")}</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                void act(() =>
                  mutate("/api/family/invitations/accept", {
                    token: val(f, "token"),
                  }),
                );
              }}
            >
              <label>{t("邀请口令")} <input name="token" required autoComplete="off" />
              </label>
              <button disabled={busy}>{t("加入家庭")}</button>
            </form>
          </section>
        </div>
      ) : home && pet ? (
        <>
          <div className="fa-petbar">
            <label>{t("当前宠物")} <select value={pet.id} onChange={(e) => setPetId(e.target.value)}>
                {home.pets.map((p) => (
                  <option value={p.id} key={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <span>{t("记录人：")}{me.user.display_name} ·{" "}
              {me.membership?.family_label || t("家庭成员")}
            </span>
            <button className="fa-secondary" onClick={() => void refresh()}>{t("同步最新记录")} </button>
            <button className="fa-secondary" onClick={() => selectTab("助手")}>{t("访问宠物分身")}</button>
          </div>
          {tab === "小屋" && (
            <>
            <FamilyToday home={home} me={me} petId={pet.id} name={pet.name} measurements={resources.measurements}
              onCare={() => selectTab("照护")}
              onWeight={() => { setEditing(null); setKind("weight"); setGrowthSection("measurements"); selectTab("成长"); setFocusTarget("weight"); }}
              onObservation={() => { setGrowthSection("diary"); selectTab("成长"); setFocusTarget("observation"); }} />
            <PetHome
              key={me.household.household_id}
              embedded
              onLogout={signOut}
              account={{
                user_id: me.user.user_id,
                role: me.membership?.role ?? "guest",
                canFeed:
                  me.membership?.feeding_pet_ids.includes("mochi") ?? false,
              }}
              selectedPet={pet.id}
              onPetChange={selectPet}
              onHomeChanged={refresh}
              onCareNavigate={navigateCare}
              onObservationNavigate={() => { setGrowthSection("diary"); selectTab("成长"); setFocusTarget("observation"); }}
              timezone={timezone}
            />
            </>
          )}
          {tab === "照护" && <FamilyCare key={pet.id} tasks={home.tasks} members={me.members} petId={pet.id} userId={me.user.user_id} timezone={timezone} busy={busy} canWrite={canWrite} initialKind={careIntent} taskAction={taskAction} act={act} mutate={mutate} />}
          {tab === "成长" && (
            <>
              <div className="fa-workspace-heading"><div><p className="fa-eyebrow">A LITTLE MORE ABOUT YOU</p><h2>{t(`${pet.name} 的成长记录`, `${pet.name}'s growth records`)}</h2><p>{t("从实测到日常原文，慢慢看见它的变化。")}</p></div>{canWrite && <div className="fa-actions"><button onClick={() => { setEditing(null); setKind("weight"); setGrowthSection("measurements"); setFocusTarget("weight"); }}>{t("记体重")}</button><button className="fa-secondary" onClick={() => { setGrowthSection("diary"); setFocusTarget("observation"); }}>{t("照片日记与主人观察")}</button></div>}</div>
              <nav className="fa-section-nav" aria-label={t("成长分区")}>{[["overview", "概览"], ["measurements", "实测与饮食"], ["diary", "日记与观察"], ["reports", "报告"]].map(([key, label]) => <button key={key} type="button" aria-pressed={growthSection === key} onClick={() => setGrowthSection(key)}>{t(label)}</button>)}</nav>
              <VisitCard key={`${me.household.household_id}:${pet.id}`} petId={pet.id} petName={pet.name} onUnauthorized={unauthorized} />
              {growthSection === "overview" && <>
              <FamilyGrowthOverview resource={resources.measurements} timezone={timezone} />
              <section className="fa-card"><div className="fa-section-heading"><h2>{t("成长曲线")}</h2><button className="fa-secondary" onClick={() => setGrowthSection("measurements")}>{canWrite ? t("记录一次实测") : t("查看实测记录")}</button></div><FamilyResourceStatus resource={resources.measurements} name="成长记录" />{(resources.measurements.status === "ready" || records.length > 0) && <FamilyWeightChart key={pet.id} records={records} timezone={timezone} />}</section>
              <div className="fa-growth-context"><p><strong>{t("最近主人观察")}</strong>{latestObservation ? latestObservation.text : t("还没有保存观察，可以从日记与观察开始。")}</p><button className="fa-secondary" onClick={() => setGrowthSection("diary")}>{t("查看日记与观察")}</button></div>
              </>}
              {growthSection === "measurements" && <div className={`fa-grid fa-growth-grid${!canWrite ? " fa-readonly-grid" : ""}`}>
                {canWrite && <section className="fa-card">
                  <h2>{editing ? t("纠正成长记录") : t("记录实测与饮食")}</h2>
                  <form
                    id="family-measurement-form"
                    key={`${me.household.household_id}:${pet.id}:${editing?.id ?? "new"}`}
                    onSubmit={(e) => {
                      e.preventDefault();
                      const f = e.currentTarget,
                        d = new FormData(f);
                      void act(async () => {
                        await mutate(
                          `/api/family/pets/${pet.id}/measurements${editing ? `/${editing.id}` : ""}`,
                          {
                            kind,
                            value: Number(val(d, "value")),
                            unit: val(d, "unit"),
                            measured_at: new Date(
                              val(d, "measured"),
                            ).toISOString(),
                            source: val(d, "source"),
                            diet_type:
                              kind === "diet" ? val(d, "diet_type") : null,
                            note: val(d, "note"),
                            ...(editing ? { version: editing.version } : {}),
                          },
                          editing ? "PUT" : "POST",
                        );
                        setEditing(null);
                        f.reset();
                      });
                    }}
                  >
                    <label>{t("记录类型")} <select
                        value={kind}
                        onChange={(e) => setKind(e.target.value)}
                      >
                        <option value="weight">{t("实测体重")}</option>
                        <option value="diet">{t("饮食事实")}</option>
                      </select>
                    </label>
                    <label>{t("测量数值")} <input
                        name="value"
                        type="number"
                        required
                        min="0.001"
                        step="any"
                        defaultValue={editing?.value}
                      />
                    </label>
                    <label>{t("单位")} <select key={kind} name="unit" defaultValue={editing?.unit ?? (kind === "diet" ? "g" : "kg")}>
                        <option value="kg">kg</option>
                        <option value="g">g</option>
                      </select>
                    </label>
                    <label>{t("测量时间")} <input
                        name="measured"
                        type="datetime-local"
                        required
                        defaultValue={
                          editing ? browserInput(editing.measured_at) : dateInput()
                        }
                      />
                    </label>
                    <label>{t("资料来源")} <select
                        name="source"
                        defaultValue={editing?.source ?? "owner_measured"}
                      >
                        {Object.entries(SOURCE).map(([k, v]) => (
                          <option value={k} key={k}>
                            {t(v)}
                          </option>
                        ))}
                      </select>
                    </label>
                    {kind === "diet" && (
                      <label>{t("饮食含义")} <select
                          name="diet_type"
                          defaultValue={editing?.diet_type ?? "actual_intake"}
                        >
                          <option value="actual_intake">{t("主人记录实际摄入")} </option>
                          <option value="food_offered">{t("提供食物")}</option>
                          <option value="dispensed">{t("记录出粮")}</option>
                          <option value="remaining">{t("剩余食物")}</option>
                        </select>
                      </label>
                    )}
                    <label>{t("备注")} <textarea
                        name="note"
                        defaultValue={editing?.note}
                        maxLength={1000}
                      />
                    </label>
                    <p className="fa-subtle">{t(`时间输入使用本机时区；记录按家庭时区 ${timezone} 显示。`, `Time entry uses your device time zone. Records use the household time zone (${timezone}).`)}</p>
                    <button disabled={busy || !canWrite}>{t("保存成长记录")}</button>
                    {editing && (
                      <button
                        type="button"
                        className="fa-secondary"
                        onClick={() => setEditing(null)}
                      >{t("取消纠正")} </button>
                    )}
                  </form>
                </section>}
                <section className="fa-card">
                  <h2>{t("成长记录明细")}</h2>
                  <FamilyResourceStatus resource={resources.measurements} name="成长记录" />
                  {resources.measurements.status === "ready" && !records.length && <div className="fa-empty"><strong>{t("还没有有效成长记录。")}</strong><p>{t("可保存实测或饮食事实；资料不足时，不会补填摄入量或体重。")}</p></div>}
                  {records.map((r) => (
                    <article className="fa-record" key={r.id}>
                      <strong>
                        {r.value} {r.unit} · {t(SOURCE[r.source])}
                      </strong>
                      <p>
                        {timeText(r.measured_at)} ·{" "}
                        {r.kind === "weight" ? t("实测体重") : ({ actual_intake: t("实际摄入"), food_offered: t("提供食物"), dispensed: t("记录出粮"), remaining: t("剩余食物") }[r.diet_type ?? ""] ?? t("饮食事实"))}
                      </p>
                      {canWrite && <div className="fa-actions">
                        <button
                          className="fa-secondary"
                          disabled={busy || !canWrite}
                          onClick={() => {
                            setEditing(r);
                            setKind(r.kind);
                          }}
                        >{t("纠正记录")} </button>
                        <button
                          className="fa-secondary"
                          disabled={busy || !canWrite}
                          onClick={() =>
                            void act(() =>
                              mutate(
                                `/api/family/pets/${pet.id}/measurements/${r.id}?version=${r.version}`,
                                undefined,
                                "DELETE",
                              ),
                            )
                          }
                        >{t("删除记录")} </button>
                      </div>}
                    </article>
                  ))}
                </section>
              </div>}
              {growthSection === "reports" && <FamilyReports key={pet.id} resource={resources.reports} records={records} home={home} members={me.members} timezone={timezone} busy={busy} canWrite={canWrite}
                onGenerate={(period, date) => act(() => mutate(`/api/family/pets/${pet.id}/reports/generate`, { period, date }))} />}
              {growthSection === "diary" && <>
                <PetHome
                  embedded
                  account={{
                    user_id: me.user.user_id,
                    role: me.membership?.role ?? "guest",
                    canFeed: false,
                  }}
                  selectedPet={pet.id}
                  onPetChange={selectPet}
                  onHomeChanged={refresh}
                  externalTab="成长日记"
                  onCareNavigate={navigateCare}
                  onObservationReady={(field) => { if (focusTarget === "observation") { field.focus(); field.scrollIntoView({ block: "center" }); setFocusTarget(""); } }}
                  timezone={timezone}
                  onLogout={signOut}
                />
              <FamilyRecords
                home={home}
                petId={pet.id}
                userId={me.user.user_id}
                admin={admin}
                canWrite={canWrite}
                busy={busy}
                timezone={timezone}
                act={act}
                mutate={mutate}
              />
              </>}
            </>
          )}
          {tab === "Alexa+" && (
            <AlexaSimulator
              key={`${me.user.user_id}:${me.household.household_id}:${pet.id}`}
              pet={pet}
              householdName={me.household.name}
              revision={home.revision}
              tasks={home.tasks}
              canWrite={canWrite}
              onChanged={refresh}
              onCare={() => selectTab("照护")}
            />
          )}
          {tab === "助手" && (
            <>
            <div className="fa-workspace-heading"><div><p className="fa-eyebrow">KNOWING YOUR LITTLE COMPANION</p><h2>{t(`${pet.name} 的分身`, `${pet.name}'s twin`)}</h2><p>{t("先了解已记录的事实，再决定下一件照护。")}</p></div><a className="fa-text-link" href="#alexa">{t("体验 Alexa+ 网页模拟")} <WorkspaceIcon name="arrow" /></a></div>
            {!canWrite && <p className="fa-readonly-note">{t("当前为家庭访客，可查看个体资料；提问、记忆纠正和安排照护需照护成员权限。")}</p>}
            <div className="fa-grid fa-twin-grid">
              <section className="fa-card fa-twin-answer">
                <h2>{t(`${pet.name} 的个体分身`, `${pet.name}'s personal twin`)}</h2>
                <p>{t("依据当前档案和主人记录回答。每轮显示实际后端；Alexa 为网页模拟。")} </p>
                <details className="fa-context-overview" open={!canWrite}>
                  <summary>{t("照护前快速了解")} {pet.name}</summary>
                  <p>{t("档案喜好：")}{pet.likes || t("未填写")} {t("· 主人陈述")}</p>
                  <p>{t("主人确认的偏好记录：")}{home.notes.filter(note => note.pet_id === pet.id && note.scope === "preference").map(note => note.text).join("；") || t("暂无记录")}</p>
                  <p>{t("当前待办：")}{home.tasks.filter(task => task.pet_id === pet.id && !task.completed).length} {t("项，计划不代表已执行。")}</p>
                  <p>{t("最近保存的观察：")}{latestObservation ? <>{latestObservation.text}<br /><small>{t("主人陈述 · 记录于")} {timeText(latestObservation.created_at)}</small></> : t("暂无记录")}</p>
                  <p>{t("确认偏好：")}{resources.memories.status === "loading" ? t("正在读取偏好…") : resources.memories.status === "error" ? t("偏好读取失败，请在下方重试。") : memories.filter(memory => memory.status === "confirmed" && (!memory.valid_until || Date.parse(memory.valid_until) > Date.now())).map(memory => memory.text).join("；") || t("暂无已确认记忆")}</p>
                </details>
                {canWrite && <>
                <div className="fa-actions fa-context-questions" aria-label={t("照护快捷提问")}>
                  {["它喜欢什么", "最近饮食记录", "最近体重是多少", "现在有哪些待办"].map(text => <button type="button" key={text} className="fa-secondary" disabled={busy || !canWrite} onClick={() => void act(() => ask(`/api/family/pets/${pet.id}/chat`, { text, entry: "app" }, setReply), "已读取最新个体记录")}>{t(text)}</button>)}
                </div>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const d = new FormData(e.currentTarget);
                    void act(
                      async () =>
                        ask(
                          `/api/family/pets/${pet.id}/chat`,
                          { text: chatInput(val(d, "text")), entry: "app" },
                          setReply,
                        ),
                      "已读取最新个体记录",
                    );
                  }}
                >
                  <label>{t("想了解什么")} <textarea
                      name="text"
                      required
                      maxLength={2000}
                      defaultValue={t("它喜欢什么")}
                    />
                  </label>
                  <button disabled={busy || !canWrite}>{t("询问分身")}</button>
                </form>
                </>}
                {reply && (
                  <article aria-label={t("分身回复")} className="fa-record">
                    <p>{serverText(reply.answer, [], { breed: reply.presentation_breed, care_summary: reply.care_summary })}</p>
                    <small>{t("上下文版本")} {reply.context_version} · {reply.backend === "bedrock" ? t("Bedrock 模型回答") : t("本地规则")}</small>
                    <details>
                      <summary>{t("查看依据")}</summary>
                      <p>{t("真实模型请求：")}{reply.request_id || t("无")}</p>
                      {reply.model_id && <p>{t("模型：")}{reply.model_id} {t("· 输入")} {reply.input_tokens} {t("/ 输出")} {reply.output_tokens} tokens</p>}
                      {reply.source_record_ids.length ? <ul className="fa-source-list">{reply.source_record_ids.map(id => <li key={id}><span>{sourceSummary(id)}</span><small>{t("源记录")} {id}</small></li>)}</ul> : <p>{t("目前无相关记录")}</p>}
                      {reply.references.map((r) => (
                        <p key={r.id}>
                          <a href={r.url} target="_blank" rel="noreferrer">
                            {r.title}
                          </a>
                        </p>
                      ))}
                    </details>
                  </article>
                )}
                {canWrite && <div className="fa-twin-plan">
                <h3>{t("把建议安排成一次人工照护")}</h3>
                <p className="fa-subtle">{t("先准备方案，再由你明确确认。确认仅创建人工任务，不操作设备。")}</p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const d = new FormData(e.currentTarget);
                    void act(
                      async () =>
                        ask(
                          `/api/family/pets/${pet.id}/proposals`,
                          {
                            kind: val(d, "kind"),
                            title: val(d, "title"),
                            due_at: new Date(val(d, "due")).toISOString(),
                          },
                          setProposal,
                        ),
                      "方案待确认",
                    );
                  }}
                >
                  <label>{t("方案类型")} <select name="kind">
                      {Object.entries(CARE).map(([k, v]) => (
                        <option key={k} value={k}>
                          {t(v)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>{t("方案名称")} <input name="title" required maxLength={80} />
                  </label>
                  <label>{t("计划时间")} <input
                      name="due"
                      type="datetime-local"
                      defaultValue={dateInput()}
                      required
                    />
                  </label>
                  <button disabled={busy || !canWrite}>{t("建立待确认方案")}</button>
                </form>
                {proposal && (
                  <article className="fa-record">
                    <p>
                      {proposal.title} ·{" "}
                      {proposal.status === "confirmed"
                        ? t("已安排人工照护")
                        : t("待确认")}
                    </p>
                    {proposal.status !== "confirmed" && (
                      <button
                        disabled={busy || !canWrite}
                        onClick={() =>
                          void act(async () => {
                            await ask(
                              `/api/family/pets/${pet.id}/proposals/${proposal.id}/confirm`,
                              {
                                version: proposal.version,
                                context_version: proposal.context_version,
                              },
                              setProposal,
                            );
                          }, "已安排人工照护；未执行设备")
                        }
                      >{t("确认安排照护")} </button>
                    )}
                  </article>
                )}
                </div>}
              </section>
              <section className="fa-card fa-twin-memory">
                <h2>{t("可查看和纠正的记忆")}</h2>
                <p className="fa-subtle">{t("记录偏好，确认有效范围。已确认内容才进入家庭共同使用的上下文。")}</p>
                {canWrite && <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const f = e.currentTarget,
                      d = new FormData(f);
                    void act(async () => {
                      await mutate(`/api/family/pets/${pet.id}/memories`, {
                        text: val(d, "text"),
                        topic: val(d, "topic"),
                        status: "candidate",
                      });
                      f.reset();
                    });
                  }}
                >
                  <label>{t("偏好原文")} <textarea name="text" required maxLength={1000} />
                  </label>
                  <label>{t("主题")} <select name="topic" defaultValue="play"><option value="general">{t("日常偏好")}</option>{Object.entries(CARE).map(([key, label]) => <option key={key} value={key}>{t(label)}</option>)}</select>
                  </label>
                  <button disabled={busy || !canWrite}>{t("保存候选记忆")}</button>
                </form>}
                <p>{t("候选经主人确认后才进入公共上下文；家庭公共资料，未使用 AgentCore 提炼。")} </p>
                <FamilyResourceStatus resource={resources.memories} name="个体记忆" />
                {resources.memories.status === "ready" && !memories.length && <p className="fa-empty">{t("还没有已保存的偏好记忆，可以先记录一件它喜欢的小事。")}</p>}
                {memories.map((m) => (
                  <article className="fa-record" key={m.id}>
                    <p>{m.text}</p>
                    <small>
                      {actorName(m.author_name, m.author_user_id)} ·{" "}
                      {m.status === "confirmed" ? t("主人已确认") : m.status === "rejected" ? t("已拒绝") : t("候选待确认")}{m.valid_until && ` · ${Date.parse(m.valid_until) <= Date.now() ? t("已过期") : t("有效至")} ${timeText(m.valid_until)}`}
                    </small>
                    {canWrite && <div className="fa-actions">
                      {m.status !== "confirmed" && (
                        <button
                          disabled={busy || !canWrite}
                          onClick={() =>
                            void act(() =>
                              mutate(
                                `/api/family/pets/${pet.id}/memories/${m.id}`,
                                { version: m.version, status: "confirmed" },
                                "PATCH",
                              ),
                            )
                          }
                        >{t("确认记忆")} </button>
                      )}
                      <button
                        className="fa-secondary"
                        disabled={busy || !canWrite}
                        onClick={() =>
                          void act(() =>
                            mutate(
                              `/api/family/pets/${pet.id}/memories/${m.id}?version=${m.version}`,
                              undefined,
                              "DELETE",
                            ),
                          )
                        }
                      >{t("删除记忆")} </button>
                    </div>}
                    {canWrite && <details>
                      <summary>{t("纠正内容与有效期")}</summary>
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          const d = new FormData(e.currentTarget);
                          void act(() =>
                            mutate(
                              `/api/family/pets/${pet.id}/memories/${m.id}`,
                              {
                                version: m.version,
                                status: "confirmed",
                                text: val(d, "text"),
                                valid_until: val(d, "until")
                                  ? new Date(val(d, "until")).toISOString()
                                  : null,
                              },
                              "PATCH",
                            ),
                          );
                        }}
                      >
                        <label>{t("修订原文")} <textarea
                            name="text"
                            defaultValue={m.text}
                            required
                          />
                        </label>
                        <label>{t("有效期")} <input name="until" type="datetime-local" defaultValue={m.valid_until ? browserInput(m.valid_until) : ""} />
                        </label>
                        <button disabled={busy || !canWrite}>{t("保存记忆纠正")} </button>
                      </form>
                    </details>}
                  </article>
                ))}
              </section>
            </div>
            </>
          )}
          {tab === "家庭" && (
            <>
            <div className="fa-workspace-heading"><div><p className="fa-eyebrow">CARE IS BETTER TOGETHER</p><h2>{t("家人，和每一次交接")}</h2><p>{t("家庭成员一起记录；外部照护者通过独立的临时只读授权了解宠物。")}</p></div></div>
            <div className="fa-grid fa-family-settings">
              {admin && <div className="fa-wide"><CareAccessManager key={`${me.household.household_id}:${pet.id}`} petId={pet.id} petName={pet.name} timezone={timezone} onUnauthorized={unauthorized} /></div>}
              <section className="fa-card">
                <h2>{t("个人设置")}</h2>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const d = new FormData(e.currentTarget);
                    void act(() =>
                      mutate(
                        "/api/family/me",
                        {
                          display_name: storedInputValue(e.currentTarget, "name", storedMe!.user.display_name),
                          family_label: storedInputValue(e.currentTarget, "label", storedMe!.membership?.family_label ?? ""),
                          avatar_ref: val(d, "avatar"),
                        },
                        "PATCH",
                      ),
                    );
                  }}
                >
                  <label>{t("个人头像")} <select
                      name="avatar"
                      defaultValue={me.user.avatar_ref || "paw"}
                    >
                      {Object.entries(AVATARS).map(([key, icon]) => (
                        <option key={key} value={key}>
                          {icon}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>{t("个人昵称")} <LocalizedInput
                      name="name"
                      storedValue={storedMe!.user.display_name}
                      displayValue={me.user.display_name}
                      required
                      maxLength={40}
                    />
                  </label>
                  <label>{t("家庭称呼")} <LocalizedInput
                      name="label"
                      storedValue={storedMe!.membership?.family_label ?? ""}
                      displayValue={me.membership?.family_label ?? ""}
                      maxLength={40}
                      list="family-labels"
                    />
                  </label>
                  <datalist id="family-labels">
                    {["爸爸", "妈妈", "姐姐", "哥哥", "室友", "照护人"].map(
                      (n) => (
                        <option key={n} value={t(n)} label={t(n)} />
                      ),
                    )}
                  </datalist>
                  <p>{t("称呼由你选择，权限由管理员授权。")}</p>
                  <button disabled={busy}>{t("保存个人设置")}</button>
                </form>
                <h3>{t("当前家人")}</h3>
                {me.members.map((m) => (
                  <article className="fa-record" key={m.user_id}>
                    <strong>
                      {AVATARS[m.avatar_ref] || "🐾"} {m.display_name} ·{" "}
                      {m.family_label || t("家庭成员")}
                    </strong>
                    <p>
                      {
                        { admin: t("管理员"), carer: t("照护成员"), guest: t("访客") }[
                          m.role
                        ]
                      }
                    </p>
                    {admin && (
                      <div className="fa-actions">
                        {me.household?.household_id === "demo-owner" && (
                          <label>{t("允许审批 Mochi 喂食")} <input
                              type="checkbox"
                              disabled={busy || m.role === "guest"}
                              checked={m.feeding_pet_ids.includes("mochi")}
                              onChange={(e) =>
                                void act(() =>
                                  mutate(
                                    `/api/family/members/${m.user_id}`,
                                    {
                                      role: m.role,
                                      feeding_pet_ids: e.target.checked
                                        ? ["mochi"]
                                        : [],
                                    },
                                    "PATCH",
                                  ),
                                )
                              }
                            />
                          </label>
                        )}
                        <label>{t("成员权限")} <select
                            aria-label={t(`${m.display_name} 的权限`, `${m.display_name}'s permissions`)}
                            value={m.role}
                            onChange={(e) =>
                              void act(() =>
                                mutate(
                                  `/api/family/members/${m.user_id}`,
                                  {
                                    role: e.target.value,
                                    feeding_pet_ids: m.feeding_pet_ids,
                                  },
                                  "PATCH",
                                ),
                              )
                            }
                          >
                            <option value="admin">{t("管理员")}</option>
                            <option value="carer">{t("照护成员")}</option>
                            <option value="guest">{t("访客")}</option>
                          </select>
                        </label>
                        {m.user_id !== me.user.user_id && (
                          <button
                            className="fa-secondary"
                            disabled={busy}
                            onClick={() =>
                              void act(() =>
                                mutate(
                                  `/api/family/members/${m.user_id}`,
                                  undefined,
                                  "DELETE",
                                ),
                              )
                            }
                          >{t("移除成员")} </button>
                        )}
                      </div>
                    )}
                  </article>
                ))}
                <button
                  className="fa-secondary"
                  disabled={busy}
                  onClick={() =>
                    void act(() =>
                      mutate("/api/family/members/me", undefined, "DELETE"),
                    )
                  }
                >{t("退出家庭")} </button>
              </section>
              <section className="fa-card">
                <h2>{t("邀请与家庭交接")}</h2>
                {admin && (
                  <details>
                    <summary>{t("宠物资料管理")}</summary>
                    <p>{t("归档保留原始记录，暂停新照护；恢复后继续使用。Mochi 保留为固定设备档案。")} </p>
                    {home.pets
                      .filter((p) => p.id !== "mochi")
                      .map((p) => (
                        <article className="fa-record" key={p.id}>
                          <strong>{p.name}</strong>
                          <button
                            disabled={busy}
                            className="fa-secondary"
                            aria-label={t(`归档 ${p.name}`, `Archive ${p.name}`)}
                            onClick={() =>
                              void act(
                                () =>
                                  mutate(
                                    `/api/family/pets/${p.id}/lifecycle`,
                                    { archived: true },
                                    "PATCH",
                                  ),
                                "宠物资料已归档",
                              )
                            }
                          >{t("归档资料")} </button>
                        </article>
                      ))}
                    {archivedPets.map((p) => (
                      <article className="fa-record" key={p.id}>
                        <strong>{p.name} {t("· 已归档")}</strong>
                        <button
                          disabled={busy}
                          className="fa-secondary"
                          aria-label={t(`恢复 ${p.name}`, `Restore ${p.name}`)}
                          onClick={() =>
                            void act(
                              () =>
                                mutate(
                                  `/api/family/pets/${p.id}/lifecycle`,
                                  { archived: false },
                                  "PATCH",
                                ),
                              "宠物资料已恢复",
                            )
                          }
                        >{t("恢复资料")} </button>
                      </article>
                    ))}
                  </details>
                )}
                {admin ? (
                  <>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const d = new FormData(e.currentTarget);
                        const session = sessionEpoch.current, before = generation.current;
                        void act(async () => {
                          const i = await request<{ token: string }>(
                            "/api/family/invitations",
                            {
                              method: "POST",
                              body: JSON.stringify({
                                role: val(d, "role"),
                                expires_in_hours: Number(val(d, "hours")),
                                max_uses: Number(val(d, "uses")),
                              }),
                            },
                          );
                          if (mounted.current && session === sessionEpoch.current && before === generation.current) setInvite(i.token);
                        }, "邀请已创建");
                      }}
                    >
                      <label>{t("授予权限")} <select name="role">
                          <option value="carer">{t("照护成员")}</option>
                          <option value="guest">{t("访客")}</option>
                          <option value="admin">{t("管理员")}</option>
                        </select>
                      </label>
                      <label>{t("邀请有效小时")} <input
                          name="hours"
                          type="number"
                          min="1"
                          max="168"
                          defaultValue="48"
                          required
                        />
                      </label>
                      <label>{t("允许使用次数")} <input
                          name="uses"
                          type="number"
                          min="1"
                          max="20"
                          defaultValue="1"
                          required
                        />
                      </label>
                      <button disabled={busy}>{t("生成家庭邀请")}</button>
                    </form>
                    {invite && (
                      <label>{t("新邀请口令（按上方有效期和次数生效）")} <input readOnly value={invite} />
                      </label>
                    )}
                    {invitations.map((i) => (
                      <article className="fa-record" key={i.invitation_id}>
                        <p>
                          {i.role === "admin"
                            ? t("管理员")
                            : i.role === "carer"
                              ? t("照护成员")
                              : t("访客")}{" "}{t("· 使用")} {i.use_count}/{i.max_uses} {t("· 到期")}{" "}
                          {timeText(i.expires_at)}
                        </p>
                        <p>
                          {i.revoked
                            ? t("已撤销")
                            : Date.parse(i.expires_at) <= Date.now()
                              ? t("已过期")
                              : i.use_count >= i.max_uses
                                ? t("已用完")
                                : t("有效")}
                        </p>
                        {!i.revoked && (
                          <button
                            className="fa-secondary"
                            disabled={busy}
                            onClick={() =>
                              void act(
                                () =>
                                  mutate(
                                    `/api/family/invitations/${i.invitation_id}`,
                                    undefined,
                                    "DELETE",
                                  ),
                                "邀请已撤销",
                              )
                            }
                          >{t("撤销邀请")} </button>
                        )}
                      </article>
                    ))}
                    <details>
                      <summary>{t("家庭设置")}</summary>
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          const d = new FormData(e.currentTarget);
                          void act(() =>
                            mutate(
                              "/api/family/household",
                              {
                                name: storedInputValue(e.currentTarget, "name", storedMe!.household!.name),
                                timezone: val(d, "timezone"),
                              },
                              "PATCH",
                            ),
                          );
                        }}
                      >
                        <label>{t("新家庭名称")} <LocalizedInput
                            name="name"
                            storedValue={storedMe!.household!.name}
                            displayValue={me.household.name}
                            required
                          />
                        </label>
                        <label>{t("新家庭时区")} <input
                            name="timezone"
                            defaultValue={me.household.timezone}
                            required
                          />
                        </label>
                        <button disabled={busy}>{t("保存家庭设置")}</button>
                      </form>
                    </details>
                  </>
                ) : (
                  <p>{t("邀请和权限由家庭管理员管理。")}</p>
                )}
                <h3>{t("最近家庭动态")}</h3>
                {home.history
                  .slice()
                  .reverse()
                  .slice(0, 25)
                  .map((h) => (
                    <article className="fa-record" key={h.id}>
                      <p>
                        {actorName(h.actor, h.actor_id)} · {serverText(h.text)}
                      </p>
                      <small>{timeText(h.created_at)}</small>
                    </article>
                  ))}
                <p>{t("模拟执行器回执仍在原工作台核验。")}</p>
                <a href="#workbench">{t("原工作台与证据入口")}</a>
              </section>
            </div>
            </>
          )}
          <nav className="fa-nav" aria-label={t("App 主导航")}>
            {["小屋", "照护", "成长", "助手", "家庭"].map((n) => (
              <button
                key={n}
                aria-current={tab === n || (tab === "Alexa+" && n === "助手") ? "page" : undefined}
                onClick={() => {
                  selectTab(n);
                  setNotice("");
                  setError("");
                }}
              >
                <WorkspaceIcon name={NAV_ICONS[n]} />
                {t(APP_LABELS[n])}
              </button>
            ))}
          </nav>
        </>
      ) : (
        <section className="fa-card">
          <p>{t("当前家庭资料不可访问，请重试或退出后重新登录。")}</p>
          <button onClick={() => void refresh()}>{t("重新检查成员权限")}</button>
        </section>
      )}
    </main>
  );
}
