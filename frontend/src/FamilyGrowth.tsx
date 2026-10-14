import { t, serverText } from "./i18n";
import { useId, useState } from "react";
import { SOURCE, type Home, type Measurement, type Report, type Member } from "./family-api";
import type { FamilyResource } from "./family-data";
import { familyDay, familyTime } from "./family-time";

const weightRecords = (records: Measurement[]) => records.filter(record => record.kind === "weight").slice().sort((a, b) => Date.parse(a.measured_at) - Date.parse(b.measured_at));
const number = (value: number, digits = 3) => Number(value.toFixed(digits));

export function FamilyResourceStatus<T>({ resource, name }: { resource: FamilyResource<T>; name: string }) {
  if (resource.status === "loading") return <p className="fa-subtle" role="status">{t(`正在读取${name}…`, `Loading ${t(name)}…`)}</p>;
  if (resource.status === "error") return <div className="fa-resource-error" role="alert"><span>{t(`${name}暂时无法读取。`, `${t(name)} are temporarily unavailable.`)}</span><button className="fa-secondary" onClick={resource.retry}>{t(`重试${name}`, `Retry ${t(name)}`)}</button>{resource.data.length > 0 && <small>{t("下方保留上次读取的记录，重试后更新。")}</small>}</div>;
  return null;
}

export function FamilyGrowthOverview({ resource, timezone }: { resource: FamilyResource<Measurement>; timezone: string }) {
  const points = weightRecords(resource.data), latest = points.at(-1);
  const previous = points.slice(0, -1).reverse().find(point => latest && Date.parse(point.measured_at) < Date.parse(latest.measured_at));
  const change = latest && previous ? number(latest.value_g - previous.value_g, 1) : null;
  const span = latest && previous ? number((Date.parse(latest.measured_at) - Date.parse(previous.measured_at)) / 86400000, 2) : null;
  return <section className="fa-growth-overview" aria-label={t("成长概览")}>
    <p className="fa-eyebrow">GROWING, ONE RECORD AT A TIME</p>
    <div className="fa-growth-summary">
      <div><span>{t("最近实测体重")}</span><strong>{latest ? `${number(latest.value_g / 1000)} kg` : resource.status === "loading" ? t("正在读取…") : resource.status === "error" ? t("暂时无法读取") : t("暂无称重")}</strong><p>{latest ? `${familyTime(latest.measured_at, timezone)} · ${t(SOURCE[latest.source])}` : t("记下一次实测，慢慢了解它的变化。")}</p></div>
      <div><span>{t("与上一次实测比较")}</span><strong>{change === null ? t("资料不足") : `${change > 0 ? "+" : ""}${change} g`}</strong><p>{latest && previous ? t(`${number((latest.value_g - previous.value_g) / previous.value_g * 100, 2)}% · 实际跨度 ${span} 天`, `${number((latest.value_g - previous.value_g) / previous.value_g * 100, 2)}% · Actual span ${span} days`) : t("至少需要两次不同时间的有效测量。")}</p></div>
    </div><small>{t("仅比较实际保存的测量；体重变化不代表健康诊断。")}</small>
  </section>;
}

export function FamilyWeightChart({ records, timezone }: { records: Measurement[]; timezone: string }) {
  const [range, setRange] = useState("all"), [selected, setSelected] = useState("");
  const captionId = useId(), all = weightRecords(records), today = familyDay(new Date(), timezone);
  const cutoff = range === "all" ? "" : new Date(Date.parse(`${today}T00:00:00Z`) - (Number(range) - 1) * 86400000).toISOString().slice(0, 10);
  const points = all.filter(point => !cutoff || (familyDay(point.measured_at, timezone) >= cutoff && familyDay(point.measured_at, timezone) <= today));
  const chosen = points.find(point => point.id === selected) ?? points.at(-1);
  const weights = points.map(point => point.value_g / 1000), times = points.map(point => Date.parse(point.measured_at));
  const low = Math.min(...weights), high = Math.max(...weights), padding = Math.max((high - low) * .15, high * .03, .05);
  const min = Math.max(0, low - padding), max = high + padding;
  const first = times[0], last = times.at(-1) ?? first;
  const x = (index: number) => first === last ? 315 : 70 + (times[index] - first) / (last - first) * 490;
  const y = (index: number) => 190 - (weights[index] - min) / (max - min) * 155;
  return <section className="fa-chart" aria-label={t("体重曲线与明细")}>
    <div className="fa-section-heading"><span className="fa-subtle">{points.length} {t("次实际测量 ·")} {timezone}</span><label>{t("曲线时间范围")}<select value={range} onChange={event => setRange(event.target.value)}><option value="all">{t("全部记录")}</option><option value="30">{t("最近 30 天")}</option><option value="90">{t("最近 90 天")}</option></select></label></div>
    {!points.length ? <p className="fa-empty">{all.length ? t("这个时间范围内没有有效测量，可切换范围。") : t("还没有有效成长记录。")}</p> : <>
      <figure><svg viewBox="0 0 600 245" role="img" aria-label={t(`主人实测体重曲线，${points.length} 次测量，未补填缺失日期`, `Owner-measured weight chart, ${points.length} measurements; missing dates have not been filled in`)} aria-describedby={captionId}>
        {[0, 1, 2, 3].map(index => { const position = 35 + index / 3 * 155; return <g key={index}><line x1="70" y1={position} x2="560" y2={position} stroke="#e1e6d8" /><text x="58" y={position + 4} textAnchor="end" fontSize="12" fill="#5c6b57">{number(max - index / 3 * (max - min))}</text></g>; })}
        <text x="25" y="18" fontSize="12" fill="#5c6b57">kg</text>
        {points.length > 1 && <polyline points={points.map((_, index) => `${x(index)},${y(index)}`).join(" ")} fill="none" stroke="#46694f" strokeWidth="3" />}
        {points.map((point, index) => <g key={point.id}><circle cx={x(index)} cy={y(index)} r={point.id === chosen?.id ? 6 : 4} fill={point.id === chosen?.id ? "#a16839" : "#46694f"} onClick={() => setSelected(point.id)}><title>{`${familyTime(point.measured_at, timezone)} · ${number(point.value_g / 1000)} kg · ${t(SOURCE[point.source])}`}</title></circle>{(points.length <= 5 || index === points.length - 1) && <text x={x(index)} y={y(index) - 12} textAnchor={index === points.length - 1 ? "end" : "middle"} fontSize="12" fill="#314c38">{number(point.value_g / 1000)} kg</text>}</g>)}
        <text x="70" y="221" fontSize="12" fill="#5c6b57">{familyDay(points[0].measured_at, timezone)}</text>{first !== last && <text x="560" y="221" textAnchor="end" fontSize="12" fill="#5c6b57">{familyDay(points[points.length - 1].measured_at, timezone)}</text>}
      </svg><figcaption id={captionId}>{points.length === 1 ? t("目前只有一次测量，尚不能计算变化。") : t("按实际测量时间绘制；连线用于阅读，不代表每日测量或健康诊断。")} {t("纵轴范围随记录调整。")}</figcaption></figure>
      <label>{t("测量点详情")}<select value={chosen?.id ?? ""} onChange={event => setSelected(event.target.value)}>{points.map(point => <option key={point.id} value={point.id}>{familyTime(point.measured_at, timezone)} · {number(point.value_g / 1000)} kg</option>)}</select></label>
      {chosen && <div className="fa-point-detail"><strong>{number(chosen.value_g / 1000)} kg</strong><span>{familyTime(chosen.measured_at, timezone)} · {t(SOURCE[chosen.source])}</span>{chosen.note && <p>{chosen.note}</p>}</div>}
      <details><summary>{t("查看测量明细")}</summary><div className="fa-table-scroll"><table aria-label={t("体重测量明细")}><thead><tr><th>{t("实测时间")}</th><th>{t("体重")}</th><th>{t("来源")}</th></tr></thead><tbody>{points.slice().reverse().map(point => <tr key={point.id}><td>{familyTime(point.measured_at, timezone)}</td><td>{number(point.value_g / 1000)} kg</td><td>{t(SOURCE[point.source])}</td></tr>)}</tbody></table></div></details>
    </>}
  </section>;
}

export function FamilyReports({ resource, records, home, members, timezone, busy, canWrite, onGenerate }: {
  resource: FamilyResource<Report>; records: Measurement[]; home: Home; members: Member[]; timezone: string; busy: boolean; canWrite: boolean;
  onGenerate: (period: string, date: string) => Promise<boolean>;
}) {
  const [period, setPeriod] = useState("all"), [date, setDate] = useState(() => familyDay(new Date(), timezone));
  const current = resource.data.filter(report => report.status === "current" && (period === "all" || report.period === period)).slice().sort((a, b) => Date.parse(b.window_start) - Date.parse(a.window_start));
  const time = (value: string) => familyTime(value, timezone);
  function sourceText(id: string) {
    const measurement = records.find(record => record.id === id);
    if (measurement) return `${measurement.kind === "weight" ? t("实测体重") : t("饮食事实")} · ${measurement.value} ${measurement.unit} · ${time(measurement.measured_at)} · ${t(SOURCE[measurement.source])}`;
    const note = home.notes.find(record => record.id === id);
    if (note) return t(`主人观察 · ${note.text} · ${note.author_name || t("历史作者")}`, `Owner observation · ${note.text} · ${note.author_name || t("历史作者")}`);
    const diary = home.diary.find(record => record.id === id);
    if (diary) return t(`成长日记 · ${diary.title} · ${diary.happened_on}`, `Growth diary · ${diary.title} · ${diary.happened_on}`);
    const event = home.history.find(record => record.id === id);
    if (event) return t(`家庭记录 · ${event.actor} · ${serverText(event.text)} · ${time(event.created_at)}`, `Household record · ${event.actor} · ${serverText(event.text)} · ${time(event.created_at)}`);
    const occurrence = home.occurrences?.find(record => record.id === id);
    if (occurrence) return t(`人工照护完成 · ${time(occurrence.completed_at)} · ${members.find(member => member.user_id === occurrence.completed_by)?.display_name ?? t("历史成员，当前姓名不可核验")}`, `Manual care completion · ${time(occurrence.completed_at)} · ${members.find(member => member.user_id === occurrence.completed_by)?.display_name ?? t("历史成员，当前姓名不可核验")}`);
    return t("已保存的来源记录；详情需在对应记录中核验");
  }
  return <section className="fa-card fa-reports" aria-label={t("日报与周报")}>
    <div className="fa-section-heading"><div><p className="fa-eyebrow">A LOOK BACK</p><h2>{t("日报与周报")}</h2></div><label>{t("报告周期")}<select value={period} onChange={event => setPeriod(event.target.value)}><option value="all">{t("全部周期")}</option><option value="daily">{t("日报")}</option><option value="weekly">{t("周报")}</option></select></label></div>
    <div className="fa-actions"><label>{t("统计日期")}<input type="date" value={date} onChange={event => setDate(event.target.value)} /></label>{["daily", "weekly"].map(value => <button key={value} disabled={busy || !canWrite || !date} onClick={() => void onGenerate(value, date).then(saved => { if (saved) setPeriod(value); })}>{value === "daily" ? t("生成日报") : t("生成周报")}</button>)}</div>
    <p className="fa-subtle">{t(`按家庭时区 ${timezone} 统计。服务运行时自动生成，重启后补跑；生成后尚未发送通知。`, `Reports use the household time zone (${timezone}). They generate while the service runs and catch up after restart. Generated reports have not sent notifications.`)}</p>
    <FamilyResourceStatus resource={resource} name="照护报告" />
    {resource.status === "ready" && !current.length && <div className="fa-empty"><strong>{t("还没有这个周期的报告。")}</strong><p>{t("已有记录会在报告中回顾；缺少资料时会如实说明。")}</p></div>}
    {current.map(report => <article className="fa-report-card" key={report.report_id}>
      <h3>{report.period === "weekly" ? t("周报") : t("日报")} · {time(report.window_start)} — {time(report.window_end)}</h3>
      <div className="fa-report-metrics"><div role="group" aria-label={t("人工照护完成")}><span>{t("人工照护完成")} </span><strong>{report.care.manual_completed}<small> {t("次")}</small></strong></div><div role="group" aria-label={t("待办")}><span>{t("待办")}</span><strong>{report.care.pending}</strong></div><div role="group" aria-label={t("逾期")}><span>{t("逾期")}</span><strong>{report.care.overdue}</strong></div></div>
      <p className="fa-weight-change">{report.weight.change_g === null ? t("至少需要两次有效测量") : t(`体重变化 ${report.weight.change_g} g / ${report.weight.change_percent}% · 实际跨度 ${report.weight.span_days} 天`, `Weight change ${report.weight.change_g} g / ${report.weight.change_percent}% · Actual span ${report.weight.span_days} days`)}</p>
      <p>{t("实际摄入：")}{report.diet.actual_intake_g === null ? t("未记录") : `${report.diet.actual_intake_g} g`} {t("· 记录出粮：")}{report.diet.dispensed_g === null ? t("未记录") : `${report.diet.dispensed_g} g`}</p>
      <details><summary>{t("统计依据与版本")}</summary><p>{t("截止")} {time(report.cutoff)} {t("· 版本")} {report.stat_version}</p>{report.source_record_ids.length ? <ul className="fa-source-list">{report.source_record_ids.map(id => <li key={id}><span>{sourceText(id)}</span><small>{t("源记录")} {id}{report.source_versions?.[id] ? t(` · 版本 ${report.source_versions[id]}`, ` · Version ${report.source_versions[id]}`) : ""}</small></li>)}</ul> : <p>{t("本期没有来源记录。")}</p>}</details>
      <p className="fa-subtle">{t("模拟设备：")}{report.care.device_success == null ? t("未连接") : t(`成功 ${report.care.device_success} 次，失败 ${report.care.device_failed} 次，未知 ${report.care.device_unknown} 次`, `Succeeded ${report.care.device_success} times, failed ${report.care.device_failed} times, unknown ${report.care.device_unknown} times`)}{t("；模拟出粮")} {report.diet.simulated_device_dispensed_g == null ? t("未记录") : `${report.diet.simulated_device_dispensed_g} g`}{t("。出粮不代表实际摄入。")}</p>
    </article>)}
  </section>;
}
