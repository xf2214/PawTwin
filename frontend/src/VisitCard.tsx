import { t, locale, serverText } from "./i18n";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ApiError, request } from "./api";
import { SOURCE, type VisitCare, type VisitSummary } from "./family-api";
import { CARE, familyTime } from "./family-time";
import "./visit-card.css";

const escapeHtml = (value: unknown) => String(value ?? t("未记录")).replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]!);
const dietLabels: Record<string, string> = { actual_intake: "主人记录实际摄入", food_offered: "提供食物", dispensed: "记录出粮（非实际摄入）", remaining: "剩余食物" };
export const visitDietLabel = (kind: string | null) => t(dietLabels[kind ?? ""] ?? "饮食记录（含义未记录）");
export const visitSource = (source: string) => t(SOURCE[source] ?? ({ owner_record: "主人陈述", owner_confirmed: "主人确认", manual_care: "人工完成记录", owner_plan: "主人计划", simulated_device: "模拟设备" }[source] ?? "记录来源未说明"));
export const visitCareTitle = (record: VisitCare) => record.title_is_fallback ? t("人工照护（历史名称未记录）", "Manual care (historical title not recorded)") : record.title;
const known = (value: string | null | undefined) => value || t("未记录");
const table = (headings: string[], rows: unknown[][], empty: string) => rows.length ? `<div class="vc-table"><table><thead><tr>${headings.map(h => `<th scope="col">${escapeHtml(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>` : `<p class="vc-empty">${escapeHtml(empty)}</p>`;

// One whitelisted, escaped document powers both preview and offline exports.
export function visitCardBody(summary: VisitSummary) {
  const { pet, age, latest_weight: weight } = summary;
  const time = (value: string) => familyTime(value, summary.timezone);
  const day = (value: string) => new Date(`${value}T12:00:00`).toLocaleDateString(locale());
  const ageText = age.years === null ? t("未记录") : t(
    `${age.years} 岁${age.basis === "birthday" ? ` · 按${age.estimated ? "估计" : "记录"}生日截至当日计算${age.days === null ? "" : `（${age.days} 天）`}` : " · 主人手填年龄，未自动增长"}`,
    `${age.years} years${age.basis === "birthday" ? ` · Calculated as of today from the ${age.estimated ? "estimated" : "recorded"} birthday${age.days === null ? "" : ` (${age.days} days)`}` : " · Owner-entered age; does not increase automatically"}`,
  );
  const species = pet.species === "cat" || pet.species === "猫" ? t("猫") : pet.species === "dog" || pet.species === "狗" ? t("狗") : known(pet.species);
  const profile = [
    [t("宠物", "Pet"), pet.name],
    [t("物种 / 品种", "Species / Breed"), `${species} / ${known(pet.breed)}`],
    [t("年龄", "Age"), ageText],
    [t("生日"), `${pet.birthday ? day(pet.birthday) : t("未记录")}${pet.birthday_estimated ? ` ${t("（主人估计）", "(owner estimate)")}` : ""}`],
    [t("性别 / 绝育", "Sex / Neutering"), `${t(({ male: "雄性", female: "雌性", unknown: "未知" }[pet.gender] ?? known(pet.gender)))} / ${pet.neutered === null ? t("未记录") : pet.neutered ? t("已绝育", "Neutered") : t("未绝育", "Not neutered")}`],
    [t("档案喜好 / 不喜欢", "Profile likes / dislikes"), `${known(pet.likes)} / ${known(pet.dislikes)} ${t("（主人陈述）", "(owner statement)")}`],
  ];
  const section = (heading: string, body: string) => `<section><h2>${escapeHtml(heading)}</h2>${body}</section>`;
  return `<article class="vc-document"><header><p class="vc-eyebrow">PAWTWIN · ${t("就诊信息卡（诊断资料）", "Vet visit card (clinical background)")}</p><h1>${escapeHtml(pet.name)}</h1><p>${t("当前已记录资料，供就诊时向兽医说明；不作诊断或医疗建议。", "Recorded information to share with your veterinarian; this is not a diagnosis or medical advice.")}</p><p>${t("截至", "As of")} ${escapeHtml(time(summary.as_of))} · ${escapeHtml(summary.timezone)}</p><p>${t("窗口：", "Window: ")}${escapeHtml(time(summary.window_start))} — ${escapeHtml(time(summary.window_end))} · ${t(`近 ${summary.days} 天`, `Last ${summary.days} days`)}</p><p>${summary.include_demo ? t("包含演示样本，请勿当作真实测量", "Includes demo samples; do not treat them as real measurements") : t(`已排除演示 / 模拟测量 ${summary.demo_excluded_count} 条`, `Excluded ${summary.demo_excluded_count} demo / simulated measurements`)}</p></header>
    ${section(t("基本档案", "Profile"), table([t("字段", "Field"), t("已记录资料", "Recorded information")], profile, t("档案未记录", "Profile not recorded")))}
    ${section(t("最新称重", "Latest weight"), weight ? `<p class="vc-weight"><strong>${escapeHtml(weight.value)} ${escapeHtml(weight.unit)}</strong> · ${escapeHtml(visitSource(weight.source))}</p><p>${t("测量于", "Measured")} ${escapeHtml(time(weight.measured_at))}${Date.parse(weight.measured_at) < Date.parse(summary.window_start) ? t(" · 在所选窗口之前", " · Before the selected window") : ""}</p><p>${t("备注原文：", "Original notes: ")}${escapeHtml(weight.note || t("无备注"))}</p>` : `<p>${t("资料不足：尚无有效体重测量。", "Insufficient information: no valid weight measurement.")}</p>`)}
    ${section(t("窗口内体重测量", "Weight measurements in the selected window"), table([t("测量时间", "Measurement time"), t("数值", "Value"), t("来源 / 录入时间", "Source / Entry time"), t("备注原文", "Original notes")], summary.measurements.filter(m => m.kind === "weight").map(m => [time(m.measured_at), `${m.value} ${m.unit}`, `${visitSource(m.source)} · ${m.recorded_at ? time(m.recorded_at) : t("录入时间未记录", "Entry time not recorded")}`, m.note || t("无备注")]), t("所选窗口内无体重测量；最新称重单独列于上方。", "No weight measurements in the selected window. The latest weight is listed above.")))}
    ${section(t("饮食记录", "Diet records"), `<p>${t("提供食物、出粮和剩余量不能推定实际摄入；食物种类仅保留备注中已写明的原文。", "Food offered, dispensed and remaining cannot establish actual intake. Food details are retained only where written in the original notes.")}</p>${table([t("记录对应时间", "Event time"), t("含义 / 数值", "Meaning / Value"), t("来源", "Source"), t("食物与备注原文", "Original food details and notes")], summary.measurements.filter(m => m.kind === "diet").map(m => [time(m.measured_at), `${visitDietLabel(m.diet_type)} · ${m.value} ${m.unit}`, visitSource(m.source), m.note || t("食物说明未记录", "Food details not recorded")]), t("所选窗口内无饮食记录，吃了什么、何时吃、实际吃多少均未据此补全。", "No diet records in the selected window. Food, eating time and actual intake have not been inferred."))}`)}
    ${section(t("人工完成的照护", "Manually completed care"), table([t("实际完成时间", "Actual completion time"), t("照护记录", "Care record"), t("原计划时间 / 来源", "Original planned time / Source")], summary.care.map(c => [time(c.completed_at), `${visitCareTitle(c)} · ${t(CARE[c.kind ?? ""] ?? c.kind ?? "类型未记录", c.kind ? undefined : "Type not recorded")}`, `${c.due_at ? time(c.due_at) : t("原计划未记录", "Original plan not recorded")} · ${t("人工完成记录")}`]), t("所选窗口内无人工完成记录，待办计划不代表已经执行。", "No manual completion records in the selected window. Planned tasks do not establish completion.")))}
    ${section(t("主人观察原文", "Original owner observations"), table([t("记录于（录入时间）", "Recorded (entry time)"), t("观察陈述", "Observation"), t("范围 / 来源", "Scope / Source")], summary.observations.map(o => [time(o.created_at), o.text, `${o.scope === "today" ? t("当日观察", "Observation that day") : t("观察", "Observation")} · ${t("主人陈述")}`]), t("所选窗口内无主人观察。", "No owner observations in the selected window.")))}
    ${section(t("主人确认的偏好", "Owner-confirmed preferences"), table([t("记录于", "Recorded"), t("原文", "Original text"), t("有效状态", "Validity")], summary.preferences.map(p => [time(p.created_at), p.text, `${p.active ? t("当前有效", "Currently active") : t("历史偏好", "Past preference")}${p.valid_until ? ` ${t("· 有效至")} ${time(p.valid_until)}` : ""} · ${t("主人确认")}`]), t("暂无已确认偏好。")))}
    ${section(t("日记原文", "Original diary entries"), table([t("主人填写的日期", "Owner-entered date"), t("标题 / 原文", "Title / Original text"), t("来源", "Source")], summary.diary.map(d => [day(d.happened_on), `${d.title}\n${d.text}`, t("主人陈述；日期由主人填写", "Owner statement; date entered by the owner")]), t("所选窗口内无日记。", "No diary entries in the selected window.")))}
    <section class="vc-missing"><h2>${t("仍需补充的资料", "Information still needed")}</h2>${summary.missing_fields.length ? `<ul>${summary.missing_fields.map(field => `<li>${escapeHtml(serverText(field))}</li>`).join("")}</ul>` : `<p>${t("本卡所列字段已有记录；未记录的临床信息仍需就诊时说明。", "The fields listed on this card have records. Discuss any unrecorded clinical information during the visit.")}</p>`}</section>
    <footer><p>${escapeHtml(serverText(summary.label))}</p><p>${t(`冻结快照 · 上下文版本 ${summary.context_version} · 原始记录保持原文。生成后新增或更正资料需重新生成。`, `Frozen snapshot · Context version ${summary.context_version} · Original records retain their wording. Generate a new card after adding or correcting records.`)}</p></footer></article>`;
}

const documentCss = `body{margin:0;color:#292e25;background:#fff;font:15px/1.65 system-ui,sans-serif}*{box-sizing:border-box}.vc-document{max-width:1000px;margin:auto;padding:36px;overflow-wrap:anywhere}.vc-eyebrow{font-size:12px;letter-spacing:.08em;color:#66724c}h1{font-size:38px;margin:6px 0}h2{font-size:20px;margin:28px 0 10px}p{margin:8px 0}.vc-weight strong{font-size:28px}.vc-table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;vertical-align:top;padding:10px;border:1px solid #deded4;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#f4f4e9}thead{display:table-header-group}tr{break-inside:avoid}.vc-missing{padding:14px;background:#f8f4e9}footer{margin-top:24px;border-top:1px solid #deded4;color:#66705c;font-size:13px}@media(max-width:500px){.vc-document{padding:16px}h1{font-size:30px}th,td{padding:7px}}@media print{@page{size:A4;margin:14mm}.vc-document{padding:0;max-width:none}.vc-table{overflow:visible}h2{break-after:avoid}header,footer{break-inside:avoid}}`;
export function visitCardHtml(summary: VisitSummary) {
  return `<!doctype html><html lang="${locale()}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(summary.pet.name)} · ${t("就诊信息卡", "Vet visit card")}</title><style>${documentCss}</style></head><body>${visitCardBody(summary)}</body></html>`;
}
function fingerprint(summary: VisitSummary) {
  return JSON.stringify({ pet: summary.pet, age: summary.age, latest_weight: summary.latest_weight,
    sources: Object.entries(summary.source_versions).sort(([a], [b]) => a.localeCompare(b)),
    records: [summary.measurements, summary.observations, summary.care, summary.preferences, summary.diary].map(rows => [...rows].sort((a, b) => a.id.localeCompare(b.id))), missing: summary.missing_fields });
}

export default function VisitCard({ petId, petName, onUnauthorized }: { petId: string; petName: string; onUnauthorized: (status: number) => void }) {
  const [open, setOpen] = useState(false), [days, setDays] = useState(7), [includeDemo, setIncludeDemo] = useState(false);
  const [snapshot, setSnapshot] = useState<VisitSummary | null>(null), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null), launcher = useRef<HTMLButtonElement>(null);
  const active = useRef(true), pending = useRef<AbortController | null>(null), sequence = useRef(0);
  useEffect(() => { active.current = true; return () => { active.current = false; sequence.current++; pending.current?.abort(); }; }, []);
  useEffect(() => { if (open && dialog.current && !dialog.current.open) dialog.current.showModal(); }, [open]);
  function close() { sequence.current++; pending.current?.abort(); setBusy(false); setOpen(false); setSnapshot(null); setError(""); launcher.current?.focus(); }
  async function fetchSummary(frozen?: VisitSummary) {
    pending.current?.abort(); const controller = new AbortController(); pending.current = controller;
    const id = ++sequence.current;
    const result = await request<VisitSummary>(`/api/family/pets/${encodeURIComponent(petId)}/visit-summary?days=${frozen?.days ?? days}&include_demo=${frozen?.include_demo ?? includeDemo}`, { signal: controller.signal, cache: "no-store" });
    return active.current && id === sequence.current ? result : null;
  }
  function failed(exception: unknown) {
    if (!active.current || (exception instanceof DOMException && exception.name === "AbortError")) return;
    if (exception instanceof ApiError && [401, 403, 404].includes(exception.status)) { setSnapshot(null); setError("当前家庭或宠物权限已失效，无法导出。"); if (exception.status !== 404) onUnauthorized(exception.status); }
    else setError("资料读取失败，请检查连接后重试。");
  }
  async function generate() {
    const before = sequence.current + 1; setBusy(true); setError(""); setSnapshot(null);
    try { const result = await fetchSummary(); if (result) setSnapshot(result); } catch (exception) { if (before === sequence.current) failed(exception); }
    finally { if (active.current && before === sequence.current) setBusy(false); }
  }
  async function exportSnapshot(print: boolean) {
    if (!snapshot) return;
    const frozen = snapshot, before = sequence.current + 1; setBusy(true); setError("");
    try {
      const current = await fetchSummary(frozen);
      if (!current) return;
      if (fingerprint(current) !== fingerprint(frozen)) { setSnapshot(null); setError("资料已新增、更正或失效，请重新生成信息卡后导出。"); return; }
      if (print) window.print();
      else {
        const url = URL.createObjectURL(new Blob([visitCardHtml(frozen)], { type: "text/html;charset=utf-8" }));
        const link = document.createElement("a"); link.href = url; link.download = `${petName.replace(/[\\/:*?"<>|]/g, "_")}-${t("就诊信息卡", "vet-visit-card")}-${frozen.as_of.slice(0, 10)}.html`; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (exception) { if (before === sequence.current) failed(exception); }
    finally { if (active.current && before === sequence.current) setBusy(false); }
  }
  return <>
    <section className="fa-card vc-launch"><div><h2>{t("把记录带到诊室")}</h2><p>{t(`将 ${petName} 的档案、实测与主人原文整理成可核对的信息卡。`, `Organize ${petName}’s profile, measurements and original owner notes into a card you can review.`)}</p></div><button ref={launcher} type="button" onClick={() => setOpen(true)}>{t("导出就诊信息卡（诊断资料）")}</button></section>
    {open && createPortal(<dialog ref={dialog} className="vc-dialog" aria-labelledby="vc-title" onCancel={close}>
      <div className="vc-controls"><div className="vc-heading"><h2 id="vc-title">{t(`${petName} 的就诊信息卡`, `${petName}’s vet visit card`)}</h2><button type="button" className="vc-secondary" onClick={close}>{t("关闭信息卡")}</button></div>
        <p>{t("以已记录资料为准。打印或下载前会重新核对权限及资料版本。")}</p>
        <div className="vc-options"><label>{t("记录窗口")}<select value={days} disabled={busy} onChange={event => { setDays(Number(event.target.value)); setSnapshot(null); }}><option value="7">{t("近 7 天")}</option><option value="30">{t("近 30 天")}</option><option value="90">{t("近 90 天")}</option></select></label>
          <label className="vc-checkbox"><input type="checkbox" checked={includeDemo} disabled={busy} onChange={event => { setIncludeDemo(event.target.checked); setSnapshot(null); }} />{t("包含演示样本（仅作演示）")}</label><button type="button" disabled={busy} onClick={() => void generate()}>{busy ? t("正在核对资料…") : t("生成信息卡")}</button></div>
        {error && <p role="alert" className="vc-error">{t(error)}</p>}
        {snapshot && <div className="vc-actions"><button type="button" disabled={busy} onClick={() => void exportSnapshot(true)}>{t("打印 / 另存为 PDF")}</button><button type="button" className="vc-secondary" disabled={busy} onClick={() => void exportSnapshot(false)}>{t("下载自包含 HTML")}</button><small>{t("下载的文件可离线打开；导出后由你自行保管。")}</small></div>}
      </div>
      {snapshot && <section aria-label={t("就诊信息卡快照")} dangerouslySetInnerHTML={{ __html: visitCardBody(snapshot) }} />}
    </dialog>, document.body)}
    {snapshot && createPortal(<div className="vc-print-host" aria-hidden="true" dangerouslySetInnerHTML={{ __html: visitCardBody(snapshot) }} />, document.body)}
  </>;
}
