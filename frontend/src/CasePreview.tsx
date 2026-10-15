import { t } from './i18n'
import { PetPortrait } from './PetPortrait'
import { GrowthTrend, demoGrowthSummary, formatDemoWeight, formatDemoChange } from './ProductGrowth'
import { PetConciergePreview } from './PetConciergePreview'
import './case-preview.css'

type CaseScenario = 'handoff' | 'growth' | 'preferences' | 'concierge'
type PreviewFrame = { title: string; status: string; detail: string }
type PreviewIcon = 'water' | 'check' | 'book' | 'message' | 'source' | 'spark' | 'arrow'

function Icon({ name }: { name: PreviewIcon }) {
  const paths: Record<PreviewIcon, string> = {
    water: 'M12 3C9 7 5 11 5 15a7 7 0 0 0 14 0c0-4-4-8-7-12ZM8 15a4 4 0 0 0 4 4',
    check: 'm5 12 4 4L19 6',
    book: 'M12 5C8 3 5 3 3 4v15c3-1 6-1 9 1m0-15c4-2 7-2 9-1v15c-3-1-6-1-9 1V5Z',
    message: 'M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 3V6a2 2 0 0 1 1-2ZM8 9h8m-8 4h5',
    source: 'M9 7H6a3 3 0 0 0-3 3v7a3 3 0 0 0 3 3h7a3 3 0 0 0 3-3v-3M13 4h7v7m0-7L10 14',
    spark: 'm12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6L12 3Z',
    arrow: 'M4 12h15m-5-5 5 5-5 5',
  }
  return <svg className="cv-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
}

function FamilyAvatar({ person }: { person: 'owner' | 'lin' }) {
  const isOwner = person === 'owner'
  return <svg viewBox="0 0 44 44" aria-hidden="true">
    <circle cx="22" cy="22" r="22" fill={isOwner ? '#e7e1d5' : '#e1e8de'} />
    <path d="M8 44v-6c0-9 6-14 14-14s14 5 14 14v6" fill={isOwner ? '#ba7459' : '#7e9272'} />
    <path d="M17 26v5c0 4 10 4 10 0v-5" fill="#e8b89a" />
    <ellipse cx="22" cy="19" rx="10" ry="12" fill="#f3c7a8" />
    <path d={isOwner ? 'M12 22C8 5 16 4 23 4c10 0 13 9 9 19l-2-8c-6 0-10-3-12-5-2 4-4 4-6 5Z' : 'M12 20C8 7 15 3 22 4c11-2 14 10 10 16l-3-7c-7 2-9-3-13-1Z'} fill={isOwner ? '#674c3e' : '#3f4540'} />
    <path d="M17 20h1m8 0h1" stroke="#674c3e" strokeWidth="2" strokeLinecap="round" />
    <path d="M19 26c2 1 4 1 6 0" stroke="#b76f58" strokeWidth="1.5" strokeLinecap="round" fill="none" />
  </svg>
}

function Topline({ step, icon, label }: { step: number; icon: PreviewIcon; label: string }) {
  return <div className="cv-topline"><span><Icon name={icon} />{t(label)}</span><span>{t("步骤")} {step + 1} / 3</span></div>
}

function FrameHeading({ frame }: { frame: PreviewFrame }) {
  return <div className="cv-frame-heading"><h3>{t(frame.title)}</h3><span className="cv-status">{t(frame.status)}</span></div>
}

function HandoffPreview({ step, frame }: { step: number; frame: PreviewFrame }) {
  const stages = ['待领取', '已领取', '已完成']
  return <>
    <Topline step={step} icon="water" label={t("家庭接力 · 虚构示意")} />
    <div className="cv-handoff-scene">
      <div className="cv-pet-caption"><span className="cv-kicker">{t("照顾它，一起接力。")}</span><strong>Miso<span>{t("柯基")}</span></strong><small>{t("虚构宠物与家庭")}</small></div>
      <div className="cv-handoff-pet"><PetPortrait pet="miso" /></div>
      <div className="cv-family-members"><div className="cv-family-person"><span className="cv-person-avatar"><FamilyAvatar person="owner" /></span><span>{t("主人")}<small>{t("安排照护")}</small></span></div><span className="cv-family-arrow"><Icon name="arrow" /></span><div className="cv-family-person"><span className="cv-person-avatar"><FamilyAvatar person="lin" /></span><span>{t("小林")}<small>{t("家人接手")}</small></span></div></div>
    </div>
    <div className="cv-handoff-board">
      <div className="cv-panel-label"><span>{t("家庭接力任务板")}</span><span>{t("人工照护")}</span></div>
      <FrameHeading frame={frame} />
      <div className="cv-lanes" aria-label={t("接力流程示意")}>
        {stages.map((stage, index) => <div className={`cv-lane ${index === step ? 'cv-lane-current' : ''} ${index < step ? 'cv-lane-passed' : ''}`} key={stage}>
          <div className="cv-lane-title"><i />{t(stage)}</div>
          {index === step ? <div className="cv-task-slip"><span className="cv-slip-icon"><Icon name={step === 2 ? 'check' : 'water'} /></span><strong>{t("换一碗水")}</strong><small>{step === 0 ? t('等家人领取') : step === 1 ? t('负责人：小林') : t('完成记录示意')}</small></div> : <div className="cv-lane-placeholder">{index < step ? <><Icon name="check" /><span>{t("已流转")}</span></> : <><span className="cv-placeholder-line" /><small>{t("等待接力")}</small></>}</div>}
        </div>)}
      </div>
      <div className="cv-responsibility"><span>{t("当前负责人")}</span><strong>{step === 0 ? t('等待领取') : t('小林 · 家人')}</strong><span className="cv-responsibility-note">{step === 0 ? t('主人已安排 · 示意') : step === 1 ? t('领取后仍待实际完成') : t('实际完成后才可回写')}</span></div>
    </div>
    <div className={`cv-handoff-receipt ${step === 2 ? 'cv-receipt-ready' : ''}`}><span className="cv-receipt-seal"><Icon name={step === 2 ? 'check' : 'source'} /></span><div><strong>{step === 2 ? t('演示回写凭证') : t('完成凭证，等待留下')}</strong><p>{step === 2 ? t('记录人 · 完成时间 · 原始照护事项') : t('实际完成后，由接手家人记录。')}</p></div><span className="cv-receipt-tag">{step === 2 ? t('示意') : t('待回写')}</span></div>
    <p className="cv-frame-detail">{t(frame.detail)}</p>
  </>
}

function DiaryPicture({ scene }: { scene: 'window' | 'cushion' }) {
  return <div className={`cv-diary-picture cv-diary-${scene}`} aria-hidden="true">
    {scene === 'window' ? <svg className="cv-diary-backdrop" viewBox="0 0 200 130"><rect width="200" height="130" fill="#e6e9df" /><rect x="103" y="13" width="76" height="72" rx="3" fill="#a3b7a6" /><rect x="108" y="18" width="66" height="62" fill="#d3e4dd" /><path d="M141 18v62m-33-31h66" stroke="#f7f6ed" strokeWidth="4" /><path d="m112 76 28-33 34 36" fill="#bccfbc" /><rect y="91" width="200" height="39" fill="#d4c5ac" /><rect x="22" y="69" width="28" height="24" rx="3" fill="#b68d6d" /><path d="M34 70c-16-16-8-29 1-12 10-18 20-6 1 12" fill="#79916f" /><path d="M0 105h200" stroke="#bfac8e" /></svg> : <svg className="cv-diary-backdrop" viewBox="0 0 200 130"><rect width="200" height="130" fill="#efe0ca" /><path d="M0 90h200v40H0" fill="#d9c9ae" /><path d="M0 103h200" stroke="#c7b592" /><rect x="125" y="35" width="53" height="47" rx="4" fill="#f8f0dc" /><path d="M151 43v32m-9-9c10 4 20-8 10-13-8-4-8 11-10 13" stroke="#9eaf8d" fill="none" strokeWidth="3" /><ellipse cx="94" cy="114" rx="57" ry="12" fill="#b8b396" /><ellipse cx="94" cy="108" rx="54" ry="15" fill="#cbc9ae" /><path d="m29 87-9 8 10 7 9-8Z" fill="#b57c67" /><path d="m17 84 8 4m8 18 6 5" stroke="#b57c67" strokeWidth="2" strokeLinecap="round" /></svg>}
    <span className="cv-diary-cat"><PetPortrait pet="luna" /></span>
  </div>
}

function GrowthPreview({ step, frame }: { step: number; frame: PreviewFrame }) {
  const { first, latest, change, count } = demoGrowthSummary('luna')
  const record = step === 0 ? first : latest
  const phases = [['录入', '测量值与来源'], ['积累', '四次模拟测量'], ['回顾', '曲线与阶段变化']]
  return <>
    <Topline step={step} icon="book" label={t("成长记录册 · 模拟数据")} />
    <div className="cv-journal-cover"><div><span className="cv-kicker">{t("把日常，留在时间里。")}</span><strong>{t("Luna 的记录册")}</strong><small>{t("奶牛猫 · 虚构宠物")}</small></div><span className="cv-journal-tab">{t("日常 / 记录")}</span></div>
    <div className="cv-diary-spread">
      <figure className="cv-diary-card cv-diary-card-first"><DiaryPicture scene="window" /><figcaption><strong>{t("窗边小记")}</strong><span>{t("主人手记 · 插画示意")}</span></figcaption><span className="cv-photo-pin" aria-hidden="true" /></figure>
      <figure className="cv-diary-card cv-diary-card-second"><DiaryPicture scene="cushion" /><figcaption><strong>{t("陪伴小记")}</strong><span>{t("日常照片 · 插画示意")}</span></figcaption><span className="cv-photo-pin" aria-hidden="true" /></figure>
    </div>
    <div className="cv-journal-page">
      <FrameHeading frame={frame} />
      <div className="cv-record-layout"><ol className="cv-record-timeline" aria-label={t("记录流程示意")}>{phases.map(([name, detail], index) => <li className={index === step ? 'cv-timeline-current' : index < step ? 'cv-timeline-passed' : ''} key={name}><span className="cv-timeline-mark">{index < step ? <Icon name="check" /> : index + 1}</span><strong>{t(name)}</strong><small>{t(detail)}</small></li>)}</ol>
        <div className="cv-record-content">{step < 2 ? <><span className="cv-record-caption">{step === 0 ? t('第一条测量 · 模拟数据') : t(`第 ${count} 条测量 · 模拟数据`, `Measurement ${count} · Simulated data`)}</span><dl className="cv-measure-fields"><div><dt>{t("测量值")}</dt><dd className="pg-measure-value">{formatDemoWeight(record.weight)}</dd></div><div><dt>{t("测量时间")}</dt><dd><time dateTime={record.date}>{record.date.replaceAll('-', '/')}</time> · 09:00</dd></div><div><dt>{t("记录来源")}</dt><dd>{t(record.source)}</dd></div></dl><p className="cv-record-note"><Icon name="source" />{step === 0 ? t('插画与测量分别保存') : t('每条记录都有独立日期与来源')}</p></> : <><span className="cv-record-caption">{t("阶段回顾 · 模拟数据")}</span><dl className="cv-report-fields"><div><dt>{t("最新体重")}</dt><dd className="pg-latest">{formatDemoWeight(latest.weight)}</dd></div><div><dt>{t("阶段变化")}</dt><dd className="pg-change">{formatDemoChange(change)} {t("· 相较 09/22")}</dd></div><div><dt>{t("记录来源")}</dt><dd>{t(`${count} 次模拟测量 · 电子秤录入`, `${count} simulated measurements · Digital scale entry`)}</dd></div></dl><span className="cv-report-footer"><Icon name="book" />{t("每一个点，都对应一条记录")}</span></>}</div>
      </div>
      {step === 2 && <GrowthTrend pet="luna" compact />}
      <p className="cv-journal-boundary">{t("模拟数据 · 仅用于产品展示，不写入真实成长记录。")}</p>
    </div>
    <p className="cv-frame-detail">{t(frame.detail)}</p>
  </>
}

function PreferencesPreview({ step, frame }: { step: number; frame: PreviewFrame }) {
  const replies = ['先留成一条偏好草稿，等主人核对。', '主人确认后，这条偏好可以继续使用。', '可以按确认偏好提出陪玩计划，仍等你确认。']
  const sources = step === 0 ? ['主人陈述', '偏好草稿'] : step === 1 ? ['主人确认', '可修改或失效'] : ['已确认偏好', '人工照护提议']
  return <>
    <Topline step={step} icon="message" label={t("偏好与对话 · 虚构示意")} />
    <div className="cv-conversation-pet"><div className="cv-coco-portrait"><PetPortrait pet="coco" /></div><div className="cv-coco-intro"><span className="cv-kicker">{t("多了解一点，再聊下一次。")}</span><strong>Coco<span>{t("棕色卷毛犬")}</span></strong><small>{t("虚构宠物 · 偏好由主人确认")}</small></div><span className="cv-conversation-spark" aria-hidden="true"><Icon name="spark" /></span></div>
    <div className="cv-conversation" aria-label={t("对话结构示意")}><div className="cv-owner-message"><span>{t("主人")}</span><p>{step < 2 ? t('它喜欢安静的陪玩。') : t('按照它的偏好，可以怎么陪玩？')}</p></div><div className="cv-assistant-message"><span className="cv-assistant-mark"><Icon name="spark" /></span><div><span>{t("本地规则 · 对话示意")}</span><p>{t(replies[step])}</p></div></div></div>
    <div className={`cv-preference-card cv-preference-stage-${step}`}>
      <div className="cv-preference-label"><span>{step === 0 ? t('偏好草稿') : step === 1 ? t('主人核对与确认') : t('人工照护计划')}</span><span>{step === 0 ? 'DRAFT' : step === 1 ? 'CONFIRMED' : 'PROPOSAL'}</span></div>
      <FrameHeading frame={frame} />
      <div className="cv-preference-body">{step === 0 ? <><span className="cv-confirm-outline"><Icon name="message" /></span><p>{t("来自主人陈述")}<br /><strong>{t("等待主人确认后再复用")}</strong></p></> : step === 1 ? <><span className="cv-confirm-stamp"><Icon name="check" /></span><p>{t("主人确认示意")}<br /><strong>{t("安静的陪玩")}</strong></p></> : <><span className="cv-confirm-outline"><Icon name="message" /></span><dl><div><dt>{t("照护事项")}</dt><dd>{t("安静地陪玩")}</dd></div><div><dt>{t("安排时间")}</dt><dd>{t("待主人选择")}</dd></div><div><dt>{t("执行方式")}</dt><dd>{t("确认后由家人人工照护")}</dd></div></dl></>}</div>
      <div className="cv-source-chips" aria-label={t("依据来源")}><span className="cv-source-caption"><Icon name="source" />{t("依据")}</span>{sources.map(source => <span key={source}>{t(source)}</span>)}</div>
      {step === 2 && <div className="cv-plan-confirmation"><span className="cv-plan-dot" /><span>{t("待主人确认 · 本页仅演示")}</span></div>}
    </div>
    <p className="cv-frame-detail">{t(frame.detail)}</p>
  </>
}

export function CasePreview({ scenario, step, frame }: { scenario: CaseScenario; step: number; frame: PreviewFrame }) {
  return <div className="pt-case-preview" data-case={scenario}>
    {scenario === 'handoff' ? <HandoffPreview step={step} frame={frame} /> : scenario === 'growth' ? <GrowthPreview step={step} frame={frame} /> : scenario === 'concierge' ? <PetConciergePreview step={step} frame={frame} /> : <PreferencesPreview step={step} frame={frame} />}
  </div>
}
