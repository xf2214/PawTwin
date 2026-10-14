import { t } from "./i18n";
import { SOURCE, type Home, type Me, type Measurement } from "./family-api";
import type { FamilyResource } from "./family-data";
import { CARE, familyDay, familyTime } from "./family-time";
import WorkspaceIcon from "./WorkspaceIcon";

export default function FamilyToday({ home, me, petId, name, measurements, onCare, onWeight, onObservation }: {
  home: Home; me: Me; petId: string; name: string; measurements: FamilyResource<Measurement>;
  onCare: () => void; onWeight: () => void; onObservation: () => void;
}) {
  const timezone = me.household!.timezone, now = Date.now(), day = familyDay(new Date(), timezone);
  const tasks = home.tasks.filter(task => task.pet_id === petId && !task.completed && task.status !== "cancelled").sort((a, b) => Date.parse(a.due_at) - Date.parse(b.due_at));
  const overdue = tasks.filter(task => Date.parse(task.due_at) < now), today = tasks.filter(task => familyDay(task.due_at, timezone) === day);
  const next = tasks[0], weights = measurements.data.filter(record => record.kind === "weight").sort((a, b) => Date.parse(b.measured_at) - Date.parse(a.measured_at));
  const latest = weights[0];
  const completedToday = home.occurrences?.filter(record => record.pet_id === petId && record.status === "completed" && record.source === "manual_care" && familyDay(record.completed_at, timezone) === day).length;
  const canWrite = me.membership?.role !== "guest";
  return <section className="fa-today" aria-label={t("今日概览")}>
    <div className="fa-section-heading"><div><p className="fa-eyebrow">TODAY, TOGETHER</p><h2>{t(`${name} 的今日概览`, `${name}'s day at a glance`)}</h2><p className="fa-today-greeting">{t("每一件被记下的小事，都让下一次照护更安心。")}</p></div><p className="fa-subtle">{day} · {timezone}</p></div>
    <div className="fa-today-grid">
      <div className="fa-today-stat"><span>{t("今天的待办")}</span><strong>{today.length}<small>{t("项")}</small></strong><p>{overdue.length ? t(`${overdue.length} 项已逾期，先看看这些`, `${overdue.length} tasks are overdue; check these first`) : t("按自己的节奏，照顾每一件小事")}<br />{completedToday === undefined ? t("历史完成资料暂未提供") : t(`今天已保存 ${completedToday} 次人工完成记录`, `Saved ${completedToday} manual care completions today`)}</p></div>
      <div className="fa-today-next"><span>{next && Date.parse(next.due_at) < now ? t("优先处理") : t("下一件照护")}</span><strong>{next ? next.title : t("暂时没有待办")}</strong><p>{next ? `${t(CARE[next.kind])} · ${familyTime(next.due_at, timezone)}` : t("可安排换水、陪玩或其他人工照护")}</p>{next && <small>{t("负责人：")}{me.members.find(member => member.user_id === next.assigned_to)?.display_name ?? t("未分配")}{next.claimed_by && t(` · ${me.members.find(member => member.user_id === next.claimed_by)?.display_name ?? t("原成员")}已领取`, ` · ${me.members.find(member => member.user_id === next.claimed_by)?.display_name ?? t("原成员")} has claimed this task`)}</small>}</div>
      <div className="fa-today-weight"><span>{t("最近实测体重")}</span><strong>{latest ? `${Number((latest.value_g / 1000).toFixed(3))} kg` : measurements.status === "loading" ? t("正在读取…") : measurements.status === "error" ? t("暂时无法读取") : t("暂无称重")}</strong><p>{latest ? `${familyDay(latest.measured_at, timezone)} · ${t(SOURCE[latest.source])}` : t("有记录才显示，照片不会推测体重")}</p></div>
    </div>
    <div className="fa-actions fa-today-actions"><button onClick={onCare}>{t("查看照护")} <WorkspaceIcon name="arrow" /></button>{canWrite && <><button className="fa-secondary" onClick={onWeight}>{t("记体重")}</button><button className="fa-secondary" onClick={onObservation}>{t("记观察")}</button></>}</div>
    {!canWrite && <p className="fa-readonly-note">{t("家庭访客 · 可查看已记录的近况，记录和完成照护需照护成员权限。")}</p>}
  </section>;
}
