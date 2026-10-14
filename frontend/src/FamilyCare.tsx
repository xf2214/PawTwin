import { t } from "./i18n";
import { useState } from "react";
import type { Member, Task } from "./family-api";
import { browserInput, CARE, familyDay, familyTime } from "./family-time";

type Props = {
  tasks: Task[]; members: Member[]; petId: string; userId: string; timezone: string;
  busy: boolean; canWrite: boolean;
  initialKind: string | null;
  taskAction: (task: Task, action: string, extra?: object) => Promise<boolean>;
  act: (action: () => Promise<unknown>, message?: string) => Promise<boolean>;
  mutate: (path: string, body?: object, method?: string) => Promise<unknown>;
};
const value = (data: FormData, name: string) => String(data.get(name) ?? "").trim();
const FILTERS = ["待办", "今天", "逾期", "我负责", "已完成", "全部"];

export default function FamilyCare({ tasks, members, petId, userId, timezone, busy, canWrite, initialKind, taskAction, act, mutate }: Props) {
  const [filter, setFilter] = useState("待办");
  const [creationKind, setCreationKind] = useState(initialKind ?? "water");
  const now = Date.now(), day = familyDay(new Date(), timezone);
  const active = (task: Task) => !task.completed && task.status !== "cancelled";
  const visible = tasks.filter(task => task.pet_id === petId).filter(task => {
    if (filter === "待办") return active(task);
    if (filter === "今天") return active(task) && familyDay(task.due_at, timezone) === day;
    if (filter === "逾期") return active(task) && Date.parse(task.due_at) < now;
    if (filter === "我负责") return active(task) && (task.assigned_to === userId || task.claimed_by === userId);
    if (filter === "已完成") return task.status !== "cancelled" && (task.completed || !!task.last_completed_at);
    return true;
  }).sort((a, b) => Number(!active(a)) - Number(!active(b)) || Date.parse(a.due_at) - Date.parse(b.due_at));
  const carers = members.filter(member => member.role !== "guest");
  const time = (date: string) => familyTime(date, timezone);
  const memberName = (id: string | null) => members.find(member => member.user_id === id)?.display_name ?? t("未分配或原成员");
  return <div className="fa-care-layout">
    <section className="fa-card fa-care-queue" aria-label={t("照护队列")}>
      <div className="fa-section-heading"><div><p className="fa-eyebrow">DAILY CARE</p><h2>{t("照护与交接")}</h2></div><span className="fa-subtle">{t("家庭时间 ·")} {day}</span></div>
      <p className="fa-care-intro">{t("先处理今天的小事，接手之后让家人知道。完成记录只代表人工照护。")}</p>
      <div className="fa-filterbar" aria-label={t("照护筛选")}>
        {FILTERS.map(name => <button key={name} className="fa-secondary" aria-pressed={filter === name} onClick={() => setFilter(name)}>{t(name)}</button>)}
      </div>
      <p className="fa-subtle">{timezone} {t("· 待办按计划时间排列；人工照护与模拟设备分开记录。")}</p>
      {!visible.length && <div className="fa-empty"><strong>{filter === "全部" ? t("还没有照护计划。") : t(`这里暂时没有${filter === "已完成" ? "完成记录" : "待办"}。`, filter === "已完成" ? "No completion records here yet." : "No tasks here yet.")}</strong><p>{canWrite ? t("可切换筛选，或安排下一件日常小事。") : t("当前为只读访问，可以切换筛选查看家庭照护记录。")}</p></div>}
      <div className="fa-task-list">{visible.map(task => {
        const nextOccurrence = active(task) && !!task.last_completed_at && Date.parse(task.due_at) > now;
        const overdue = active(task) && Date.parse(task.due_at) < now;
        const otherClaimant = !!task.claimed_by && task.claimed_by !== userId;
        const status = task.status === "cancelled" ? t("已取消") : task.completed ? t("已完成") : nextOccurrence ? t("下次待办") : task.status === "claimed" ? t("已领取") : overdue ? t("已逾期") : t("待照护");
        return <article className={`fa-record fa-task-card${overdue ? " fa-task-overdue" : ""}${!active(task) ? " fa-task-settled" : ""}`} key={task.id}>
          <div className="fa-section-heading"><h3>{task.title}</h3><span className={`fa-chip${overdue ? " fa-chip-warm" : ""}`}>{status}</span></div>
          <p>{t(CARE[task.kind])} · {time(task.due_at)}{task.interval_days ? t(` · 每 ${task.interval_days} 天`, ` · Every ${task.interval_days} days`) : t(" · 一次性")}</p>
          <p className="fa-subtle">{t("负责人：")}{memberName(task.assigned_to)}</p>
          {task.claimed_by && <p className="fa-task-claimant">{t("领取人：")}{memberName(task.claimed_by)}</p>}
          {task.last_completed_at && <p className="fa-subtle">{nextOccurrence ? t("本次已完成；") : ""}{t("最近完成：")}{time(task.last_completed_at)}{nextOccurrence ? t("。下一次到期后可继续记录。") : ""}</p>}
          {active(task) && canWrite && <>
            <div className="fa-actions">
              {!nextOccurrence && <>
                <button className="fa-secondary" disabled={busy || !canWrite || otherClaimant || task.status === "claimed"} onClick={() => void taskAction(task, "claim")}>{t("领取")}</button>
                <button disabled={busy || !canWrite || otherClaimant} onClick={() => void taskAction(task, "complete")}>{t("完成照护")}</button>
              </>}
              <button className="fa-secondary" disabled={busy || !canWrite} onClick={() => void taskAction(task, "cancel")}>{t("取消")}</button>
            </div>
            {otherClaimant && <p className="fa-subtle">{t("由领取人完成本次照护，或先转交给其他家人。")}</p>}
            <details className="fa-task-details"><summary>{t("编辑或延期")}</summary>
              <form key={`${task.id}:${task.version}`} onSubmit={event => {
                event.preventDefault(); const data = new FormData(event.currentTarget);
                const due = value(data, "due"), interval = value(data, "interval");
                const intervalDays = interval ? Number(interval) : null;
                void taskAction(task, "edit", { title: value(data, "title"),
                  ...(due !== browserInput(task.due_at) ? { next_due: new Date(due).toISOString() } : {}),
                  ...(intervalDays !== task.interval_days ? { interval_days: intervalDays } : {}),
                });
              }}>
                <label>{t("任务标题")}<input name="title" defaultValue={task.title} required maxLength={80} /></label>
                <div className="fa-form-row"><label>{t("新计划时间")}<input name="due" type="datetime-local" defaultValue={browserInput(task.due_at)} required /></label><label>{t("新周期（天）")}<input name="interval" type="number" min={1} max={365} defaultValue={task.interval_days ?? ""} /></label></div>
                <p className="fa-subtle">{t(`时间输入使用本机时区；列表按家庭时区 ${timezone} 显示。周期留空表示一次性。`, `Time entry uses your device time zone. The list uses the household time zone (${timezone}). Leave the interval blank for a one-time task.`)}</p>
                <button disabled={busy || !canWrite}>{t("保存任务编辑")}</button>
              </form>
            </details>
            <details><summary>{t("转交给家人")}</summary><form className="fa-actions" onSubmit={event => { event.preventDefault(); void taskAction(task, "transfer", { assigned_to: value(new FormData(event.currentTarget), "member") }); }}>
              <label>{t("转交给")}<select name="member" defaultValue={task.assigned_to ?? carers[0]?.user_id}>{carers.map(member => <option key={member.user_id} value={member.user_id}>{member.display_name}</option>)}</select></label>
              <button disabled={busy || !canWrite}>{t("转交")}</button>
            </form></details>
          </>}
        </article>;
      })}</div>
    </section>
    {canWrite ? <section className="fa-card fa-care-create">
      <details open={!!initialKind}><summary className="fa-create-summary">{t("＋ 安排日常照护")}</summary>
        <h2>{t("安排日常照护")}</h2><p>{t("选择自己的节奏，洗澡、剪指甲不预设重复周期。")}</p>
        <form onSubmit={event => {
          event.preventDefault(); const form = event.currentTarget, data = new FormData(form);
          void act(async () => { await mutate(`/api/home/pets/${petId}/tasks`, { kind: value(data, "kind"), title: value(data, "title"), due_at: new Date(value(data, "due")).toISOString(), interval_days: value(data, "interval") ? Number(value(data, "interval")) : null, assigned_to: value(data, "assigned") || null }); form.reset(); });
        }}>
          <label>{t("照护类型")}<select name="kind" value={creationKind} onChange={event => setCreationKind(event.target.value)}>{Object.entries(CARE).map(([key, name]) => <option value={key} key={key}>{t(name)}</option>)}</select></label>
          <label>{t("照护名称")}<input name="title" defaultValue={initialKind ? t(CARE[creationKind]) : ""} required maxLength={80} /></label>
          <label>{t("照护时间")}<input name="due" type="datetime-local" defaultValue={browserInput()} required /></label>
          <div className="fa-form-row"><label>{t("重复间隔（天）")}<input name="interval" type="number" min={1} max={365} /></label><label>{t("负责人")}<select name="assigned"><option value="">{t("未分配")}</option>{carers.map(member => <option key={member.user_id} value={member.user_id}>{member.display_name}</option>)}</select></label></div>
          <p className="fa-subtle">{t(`时间输入使用本机时区；家庭时区为 ${timezone}。人工喂食记录不触发设备。`, `Time entry uses your device time zone. The household time zone is ${timezone}. Manual feeding records do not trigger devices.`)}</p>
          <button disabled={busy || !canWrite}>{t("保存照护计划")}</button>
        </form>
      </details>
    </section> : <p className="fa-readonly-note">{t("当前为家庭访客，可查看计划与完成情况；安排、领取和完成照护需照护成员权限。")}</p>}
  </div>;
}
