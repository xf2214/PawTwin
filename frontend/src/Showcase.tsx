import { t, LanguageSwitch } from './i18n'
import { useEffect, useId, useRef, useState, type MouseEvent } from 'react'
import './showcase.css'
import { ProductBenefits, ProductFAQ, ProductStart } from './ProductSections'
import { PET_PROFILES, PetArtwork, PetPortrait, type PetKind } from './PetPortrait'
import { PhonePreview, TabletPreview } from './ProductDevices'
import { CasePreview } from './CasePreview'
import { ProductGrowth } from './ProductGrowth'
import { CONCIERGE_STEPS } from './concierge-scenario'
import './pet-gallery.css'
import './visual-polish.css'

function TitlePhrases({ text }: { text: string }) {
  const translated = t(text)
  const comma = translated.search(/[，,]/)
  if (comma < 0) return <>{translated}</>
  return <><span className="pt-title-phrase">{translated.slice(0, comma + 1)}</span><wbr /><span className="pt-title-phrase">{translated.slice(comma + 1)}</span></>
}

export function PawMark() {
  return <svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true">
    <ellipse cx="8" cy="10" rx="3.1" ry="4" transform="rotate(-25 8 10)" />
    <ellipse cx="15" cy="6.5" rx="3" ry="4" />
    <ellipse cx="23" cy="9" rx="3" ry="4" transform="rotate(24 23 9)" />
    <ellipse cx="27" cy="16" rx="2.5" ry="3.5" transform="rotate(38 27 16)" />
    <path d="M6 23c0-4 5-10 10-10s10 6 10 10c0 7-6 3-10 3S6 30 6 23Z" />
  </svg>
}

function HomeIllustration({ pet = 'mochi' }: { pet?: PetKind }) {
  const patternId = useId()
  return <svg viewBox="0 0 580 420" role="img" aria-label={t(`俯视的宠物小屋，中央是正面造型的${PET_PROFILES[pet].species}`, `Top-down pet home with a front-facing ${t(PET_PROFILES[pet].species)} in the center`)}>
    <defs>
      <pattern id={`${patternId}-floor`} width="64" height="32" patternUnits="userSpaceOnUse">
        <rect width="64" height="32" fill="#ecddbd" />
        <path d="M0 31.5h64M63.5 0v32" stroke="#d7c69e" strokeWidth="1" />
      </pattern>
      <pattern id={`${patternId}-tile`} width="30" height="30" patternUnits="userSpaceOnUse">
        <rect width="30" height="30" fill="#e1e6ce" />
        <path d="M0 29.5h30M29.5 0v30" stroke="#c9d1b5" />
      </pattern>
    </defs>
    <rect x="24" y="27" width="532" height="362" rx="13" fill="#b6bea0" />
    <rect x="35" y="38" width="510" height="340" rx="4" fill={`url(#${patternId}-floor)`} />
    <path d="M395 38h150v340H395Z" fill={`url(#${patternId}-tile)`} />
    <path d="M391 38v120m0 87v133" stroke="#a2ae8d" strokeWidth="9" />
    <rect x="98" y="28" width="151" height="17" rx="2" fill="#789b8e" />
    <path d="M104 35h139" stroke="#cde5d9" strokeWidth="9" />
    <path d="M175 29v13" stroke="#789b8e" strokeWidth="5" />
    <rect x="66" y="76" width="200" height="79" rx="10" fill="#6c825e" />
    <rect x="78" y="91" width="80" height="48" rx="5" fill="#a6b78e" />
    <rect x="164" y="91" width="80" height="48" rx="5" fill="#b6c49b" />
    <path d="M73 92v45m181-45v45" stroke="#82976c" strokeWidth="12" />
    <rect x="65" y="184" width="257" height="147" rx="45" fill="#b6c39c" />
    <rect x="75" y="194" width="237" height="127" rx="35" fill="none" stroke="#d0d8b8" strokeWidth="3" strokeDasharray="4 5" />
    <rect x="97" y="211" width="100" height="65" rx="17" fill="#c6a875" />
    <rect x="103" y="212" width="88" height="56" rx="14" fill="#e7cda2" />
    <rect x="127" y="224" width="26" height="29" rx="2" fill="#faf2dd" transform="rotate(-13 127 224)" />
    <path d="M135 231h10m-10 5h10" stroke="#bac49d" strokeWidth="2" />
    <rect x="331" y="66" width="33" height="35" rx="6" fill="#bb916b" />
    <g fill="#6e936c"><ellipse cx="340" cy="64" rx="12" ry="20" transform="rotate(-35 340 64)" /><ellipse cx="357" cy="66" rx="10" ry="21" transform="rotate(28 357 66)" /><ellipse cx="347" cy="57" rx="10" ry="22" /></g>
    <rect x="418" y="62" width="105" height="50" rx="5" fill="#9cab8c" />
    <rect x="426" y="69" width="40" height="36" rx="4" fill="#c3d4c3" />
    <circle cx="448" cy="87" r="12" fill="#7f9e92" />
    <rect x="480" y="69" width="34" height="36" rx="3" fill="#cdd4b8" />
    <rect x="427" y="165" width="86" height="100" rx="10" fill="#71866b" />
    <rect x="435" y="172" width="70" height="58" rx="8" fill="#e7ebd8" />
    <rect x="448" y="184" width="44" height="7" rx="3" fill="#c5d2b1" />
    <ellipse cx="470" cy="247" rx="24" ry="10" fill="#ddd6b7" />
    <ellipse cx="470" cy="245" rx="17" ry="6" fill="#b68e56" />
    <ellipse cx="462" cy="315" rx="26" ry="19" fill="#acbfad" />
    <ellipse cx="462" cy="312" rx="20" ry="13" fill="#d9e9e1" />
    <rect x="323" y="316" width="51" height="43" rx="18" fill="#bd9a7c" />
    <rect x="330" y="323" width="37" height="29" rx="12" fill="#e8cfad" />
    <circle cx="225" cy="321" r="9" fill="#bb7961" />
    <path d="M219 319h12" stroke="#e4b397" strokeWidth="2" />
    <svg x="250" y="197" width="96" height="108" viewBox="0 0 128 144" aria-hidden="true"><PetArtwork pet={pet} /></svg>
    <g fontFamily="system-ui, sans-serif" fontSize="11" fill="#727960">
      <text x="147" y="361" textAnchor="middle">{t("陪伴的角落")}</text>
      <text x="471" y="360" textAnchor="middle">{t("照护区")}</text>
    </g>
  </svg>
}

const STORIES = [
  { label: '宠物小屋', icon: '⌂', title: '给每个小家伙，一个自己的家。', text: '从今日概览看待办、照护进度和成长记录，再回到它的小屋。档案、玩具、熟悉的窝和你确认的偏好，让照护从了解它开始。', tags: ['今日概览', '独立宠物档案', '像素小屋'], note: '每只宠物都有自己的记录与偏好', route: '#app/home' },
  { label: '家庭照护', icon: '✓', title: '照顾它，是全家人的默契。', text: '先看逾期与今天的照护，再安排换水、陪玩、梳毛。谁来接手、什么时候实际完成，都留下一条清楚的记录。', tags: ['今日与逾期', '领取与交接', '完成记录'], note: '按时间与状态找到下一件照护小事', route: '#app/care' },
  { label: '成长记录', icon: '↗', title: '把成长，留在时间里。', text: '记录实际测量的体重，保存日常照片和观察。用曲线与日／周报告回看变化、照护进度和记录来源，也看见还没有记录的部分。', tags: ['实测曲线', '照护统计', '有来源的报告'], note: '模拟数据展示 · 在应用中记录它的真实成长', route: '#app/growth' },
  { label: '宠物分身', icon: '✦', title: '每次交流，从你们的记录开始。', text: '从档案、成长记录和主人确认的偏好中找到依据。App 与 Alexa 网页模拟共用这些记录；查询近况、回顾照护，提出仍需确认的人工照护计划。', tags: ['个体上下文', '确认偏好', '照护提议'], note: '实际回答后端与依据见每轮回复；Alexa 为网页模拟', route: '#app/assistant' },
]

function CatPortrait({ pet = 'mochi' }: { pet?: PetKind }) {
  return <PetPortrait pet={pet} />
}

function ProductDevice({ compact = false, pet = 'mochi' }: { compact?: boolean; pet?: PetKind }) {
  return <TabletPreview compact={compact} pet={pet} room={<HomeIllustration pet={pet} />} />
}

function StoryPreview({ selected, pet }: { selected: number; pet: PetKind }) {
  if (selected === 0) return <ProductDevice compact pet={pet} />
  return <div className="pt-preview-card" aria-label={t(`${STORIES[selected].label}界面示意`, `${t(STORIES[selected].label)} interface preview`)}>
    <div className="pt-preview-header"><span className="pt-avatar"><CatPortrait pet={pet} /></span><div><strong>{PET_PROFILES[pet].name}</strong><small>{t(STORIES[selected].label)} {t("· 产品界面示意")}</small></div><span className="pt-preview-dot" /></div>
    {selected === 1 && <><h4>{t("下一件小事，清楚可见。")}</h4><p className="pt-preview-muted">{t("先看逾期，再看今日；也能回顾已完成。")}</p><div className="pt-preview-filters"><span>{t("全部")}</span><span>{t("今日")}</span><span>{t("逾期")}</span><span>{t("已完成")}</span></div><div className="pt-preview-tasks">{[['换一碗新鲜的水', '换水', '逾期'], ['和它玩一会儿', '陪玩', '今日待办'], ['梳理一下毛发', '梳毛', '已领取']].map(([title, kind, state], index) => <div key={kind}><span className="pt-preview-check">○</span><div><strong>{t(title)}</strong><small>{t(kind)} {t("· 人工照护")}</small></div><span className={index === 0 ? 'pt-preview-overdue' : undefined}>{t(state)}</span></div>)}</div><div className="pt-preview-foot">{t("安排 → 领取 → 实际完成后记录")}<br />{t("状态为虚构示意，实际任务见应用。")}</div></>}
    {selected === 2 && <ProductGrowth pet={pet} />}
    {selected === 3 && <><h4>{t("多一点了解，多一点默契。")}</h4><div className="pt-preview-conversation"><p>{t("它最近有哪些照护记录？")}</p><div><span>{t("✦ 宠物分身 · 交互示意")}</span><p>{t("从你们保存的记录出发，回顾它的近况，并在需要时提出待确认的照护计划。")}</p><small>{t("依据：档案 · 主人确认偏好 · 照护记录")}</small></div></div><div className="pt-preview-foot">{t("界面示意 · 实际回答后端见应用内每轮回复")}</div></>}
  </div>
}

const CASES = [
  { label: '家庭交接', route: '#app/care', title: '你出门了，照顾还在继续。', intro: '出门前为 Miso 安排换水。家人接手后，在实际完成时留下记录，彼此不用反复确认。', icon: '♡', outcome: '任务的每一次交接，都有清楚的去向。', steps: [
    { label: '主人安排', title: '换一碗新鲜的水', status: '待领取', detail: '主人创建一项人工照护事项，等待家人接手。' },
    { label: '家人接手', title: '小林领取了照护事项', status: '已领取', detail: '负责人变得清楚。领取不代表已经完成。' },
    { label: '完成并回写', title: '实际完成后留下记录', status: '已完成', detail: '家人换水后记录完成，照护记录进入日常回顾。' },
  ] },
  { label: '成长回顾', route: '#app/growth', title: '一次次记录，看见成长的轨迹。', intro: '用 Luna 的四次模拟测量，看看记录如何连成曲线。日期、来源和阶段变化一起保留，日常小记也能回看。', icon: '↗', outcome: '看见变化，也能回到每一条原始记录。', steps: [
    { label: '记录测量', title: '留下第一条测量', status: '模拟数据', detail: '示例从 09/22 的记录开始，体重、测量日期与录入来源一起展示。' },
    { label: '持续记录', title: '慢慢积累成长记录', status: '模拟数据', detail: '四次模拟测量各自保留日期和来源；日常照片与手记独立记录。' },
    { label: '回看变化', title: '回看这一段成长', status: '模拟数据', detail: '曲线与阶段变化使用同一组模拟记录，仅供产品展示，不写入家庭数据。' },
  ] },
  { label: '偏好接续', route: '#app/assistant', title: '下一次交流，从已有了解开始。', intro: '把“它喜欢安静的陪玩”作为待确认偏好。主人确认后，再在新会话里查询，让对话接上已有记录。', icon: '✦', outcome: '偏好由主人确认，照护提议仍需确认。', steps: [
    { label: '记录偏好', title: '它喜欢安静的陪玩', status: '待确认', detail: '这是一条虚构情景中的偏好草稿，尚未进入确认偏好。' },
    { label: '主人确认', title: '主人确认了这条偏好', status: '已确认偏好', detail: '确认后的偏好可以复用，也可以修改、失效或删除。' },
    { label: '接续对话', title: '按确认偏好提出陪玩计划', status: '待主人确认', detail: '本地规则助手引用确认偏好提出人工照护计划，不自动执行。' },
  ] },
  { label: '宠物管家', route: '#alexa', title: '你只管问，它记得是哪一只。', intro: '问小狗能不能吃巧克力，也问猫咪为什么没精神。已保存的品种、性别、年龄、确认偏好和近期记录，随这只宠物的提问一起带入。', icon: '✧', outcome: '资料先保存，提问更自然；回答始终带着依据。', steps: CONCIERGE_STEPS },
]

function CaseShowcase() {
  const [selected, setSelected] = useState(0)
  const [step, setStep] = useState(0)
  const scenario = CASES[selected]
  const frame = scenario.steps[step]
  return <section className="pt-cases" id="cases" aria-labelledby="cases-title">
    <div className="pt-section-heading" data-reveal><p className="pt-eyebrow">{t("四个场景，一起看看。")}</p><h2 id="cases-title">{t("把功能，放进日常。")}</h2><p>{t("不是功能清单，是你和它的一天。")}</p></div>
    <div className="pt-case-tabs" role="group" aria-label={t("选择日常案例")}>{CASES.map((item, index) => <button key={item.label} aria-pressed={selected === index} onClick={() => { setSelected(index); setStep(0) }}>{t(item.label)}</button>)}</div>
    <div className={`pt-case-layout pt-case-theme-${selected}`}>
      <div className="pt-case-art pt-case-art-rich" aria-label={t("案例画面")}><CasePreview key={selected} scenario={(['handoff', 'growth', 'preferences', 'concierge'] as const)[selected]} step={step} frame={frame} />
        <small>{t("虚构情景演示 · 不会创建真实照护任务")}</small>
      </div>
      <div className="pt-case-copy"><div className="pt-case-intro" key={selected}><span className="pt-story-number">{t("案例 0")}{selected + 1} / {t(scenario.label)}</span><h3 aria-label={t(scenario.title)}><TitlePhrases text={scenario.title} /></h3><p>{t(scenario.intro)}</p></div>
        <div className="pt-case-steps" role="group" aria-label={t("查看案例步骤")}>{scenario.steps.map((item, index) => <button key={item.label} aria-pressed={step === index} onClick={() => setStep(index)}><span>0{index + 1}</span><strong>{t(item.label)}</strong><span aria-hidden="true">{step === index ? '−' : '+'}</span></button>)}</div>
        <p className="pt-case-active" aria-live="polite" aria-atomic="true">{t(frame.detail)}</p><p className="pt-case-outcome">{t(scenario.outcome)}</p><a className="pt-text-link" href={scenario.route}>{t(selected === 3 ? '打开 Alexa+ 网页模拟器' : '在应用中开始')} <span aria-hidden="true">›</span></a>
      </div>
    </div>
  </section>
}

type VisionStep = {
  label: string;
  title: string;
  status: string;
  detail: string;
  fields: [string, string][];
  sources: string[];
}
type VisionScenario = {
  label: string;
  title: string;
  intro: string;
  feature: string;
  action: string;
  route: string;
  steps: VisionStep[];
}
const VISION_SCENARIOS: VisionScenario[] = [
  {
    label: '照护交接', title: '先了解它，再接手照顾。',
    intro: '外出或临时托付时，让照护者先了解它。选择一只宠物、设置访问期限，分享只读分身链接；管理员可以随时结束授权。',
    feature: '应用功能 · 家庭管理员可管理临时只读访问', action: '在应用中管理临时访问', route: '#app/family',
    steps: [
      {
        label: '选择资料', title: '选择宠物与资料', status: '管理员设置',
        detail: '在家庭应用中选择要交接的宠物，先核对档案、确认偏好与最近的照护记录。授权范围限定到这只宠物。',
        fields: [['指定宠物', 'Mochi · 虚构宠物示意'], ['档案资料', '主人填写并核对'], ['习惯与喜好', '只使用主人确认的偏好'], ['近期照护', '保留时间与原始记录']],
        sources: ['当前宠物的已有记录', '不包含其他宠物或家庭资料'],
      },
      {
        label: '授权分身卡', title: '临时只读分身卡', status: '指定宠物 · 只读',
        detail: '照护者通过授权分身询问档案、主人确认喜好与最近照护。访问有期限、可撤销；不能修改记录、确认任务或操作设备。',
        fields: [['指定宠物', 'Mochi · 虚构宠物示意'], ['有效期限', '由管理员设置'], ['可撤销', '管理员可随时撤销'], ['只读内容', '档案 · 确认喜好 · 最近照护'], ['可询问什么', '它喜欢什么？最近完成了哪些照护？']],
        sources: ['主人填写的档案', '主人确认偏好', '最近照护原始记录'],
      },
      {
        label: '只读查看', title: '照护者只读查看', status: '查看与询问',
        detail: '照护者打开专属链接，查看这只宠物的资料，并询问确认喜好与近期照护。只读访问不允许修改记录、领取或完成任务。',
        fields: [['如何进入', '通过管理员分享的临时链接'], ['可以查看', '宠物档案与有来源的记录'], ['可以询问', '确认喜好与最近照护'], ['操作范围', '只读 · 不能操作设备']],
        sources: ['回答依据授权宠物的已有资料', '不创建预约或订单'],
      },
      {
        label: '结束授权', title: '到期或撤销', status: '访问可控',
        detail: '期限届满后，临时链接停止访问。管理员也可以在应用中提前撤销，让资料只在需要的时间里被查看。',
        fields: [['到期结束', '达到设定期限后停止访问'], ['提前撤销', '家庭管理员可随时操作'], ['撤销之后', '原链接不能继续查看或提问'], ['原始记录', '仍在家庭应用中管理']],
        sources: ['应用内管理有效期和撤销状态', '本页仅演示，不创建访问链接'],
      },
    ],
  },
  {
    label: '就诊准备', title: '临出门，把已有记录说清楚。',
    intro: '在应用中选择资料范围，核对年龄、实测体重、饮食与照护记录，再导出就诊信息卡。保留来源与空白，给兽医提供可核对的诊断资料。',
    feature: '应用功能 · 登录后核对资料并导出信息卡', action: '导出就诊信息卡（诊断资料）', route: '#app/growth',
    steps: [
      {
        label: '查看已有记录', title: '已有记录概览', status: '有记录才整理',
        detail: '整理当前宠物已有资料，年龄、体重和食量未知时保持未记录。本页使用结构字段，不填入虚构测量或健康数值。',
        fields: [['年龄与生日', '未记录 · 估计生日需注明'], ['最新实测体重', '未记录 · 保留测量时间'], ['吃了什么、何时吃', '待填写 · 区分实际摄入与出粮'], ['最近做了什么', '已完成照护与主人观察']],
        sources: ['档案与生日：主人填写', '体重与饮食：已有原始记录', '照护与观察：注明记录人和时间'],
      },
      {
        label: '核对缺项与来源', title: '缺项与来源', status: '请主人核对',
        detail: '查看缺项与来源，纠正后再导出。主人观察保留原文；提供食物、记录出粮与实际摄入分别呈现，计划不算已经完成。',
        fields: [['尚缺资料', '年龄、测量或饮食细节未记录时提示'], ['饮食含义', '实际摄入 / 提供食物 / 记录出粮'], ['时间与来源', '保留事件时间、记录来源'], ['主人核对', '补充或纠正原始记录']],
        sources: ['缺失项目保持未记录', '不从照片推算体重或食量', '观察不是自动诊断'],
      },
      {
        label: '预览就诊卡', title: '就诊信息卡（诊断资料）', status: '信息卡结构示意',
        detail: '真实导出在应用中读取当前记录，支持打印、另存 PDF 与自包含 HTML。官网只预览结构，不生成或下载私人资料；信息卡不替代兽医检查。',
        fields: [['宠物资料', '年龄：未记录 · 体重：未记录'], ['饮食与照护时间线', '记录吃了什么、何时吃、做了什么'], ['资料范围与截止时间', '由应用显示所选范围、截至时间与时区'], ['原始来源与缺项', '记录时间、来源与未记录项目']],
        sources: ['默认排除演示测量', '有效的原始记录与版本', '给主人与兽医核对的资料'],
      },
    ],
  },
]

function VisionShowcase() {
  const [selected, setSelected] = useState(0)
  const [step, setStep] = useState(0)
  const scenario = VISION_SCENARIOS[selected]
  const frame = scenario.steps[step]
  return <section className="pt-vision" id="vision" aria-labelledby="vision-title">
    <div className="pt-section-heading" data-reveal><p className="pt-eyebrow">{t("从日常记录，到安心交接。")}</p><h2 id="vision-title">{t("把了解它的记录，带到下一次照护。")}</h2><p>{t("两个功能演示：宠物分身交接，与就诊资料准备。")}</p></div>
    <div className="pt-case-tabs pt-vision-tabs" role="group" aria-label={t("选择交接与就诊演示")}>{VISION_SCENARIOS.map((item, index) => <button key={item.label} aria-pressed={selected === index} onClick={() => { setSelected(index); setStep(0) }}>{t(item.label)}</button>)}</div>
    <div className={`pt-vision-layout pt-vision-theme-${selected}`}>
      <div className="pt-vision-art" aria-label={t("交接与就诊功能界面示意")}>
        <div className="pt-vision-card" key={`${selected}-${step}`}>
          <div className="pt-vision-card-top"><span>{t("功能界面示意")}</span><span>{t("步骤")} {step + 1} / {scenario.steps.length}</span></div>
          <div className="pt-vision-pet"><span className="pt-avatar"><CatPortrait /></span><div><strong>Mochi</strong><small>{t("虚构宠物 · 无真实家庭资料")}</small></div></div>
          <h3>{t(frame.title)}</h3><span className="pt-case-status">{t(frame.status)}</span>
          <dl className="pt-vision-fields">{frame.fields.map(([label, value]) => <div key={label}><dt>{t(label)}</dt><dd>{t(value)}</dd></div>)}</dl>
          <div className="pt-vision-sources"><strong>{t("资料来源与边界")}</strong>{frame.sources.map(source => <p key={source}>{t(source)}</p>)}</div>
        </div>
        <p className="pt-vision-boundary">{t("虚构情景演示 · 只切换画面，不读取家庭记录或创建业务记录")}</p>
      </div>
      <div className="pt-vision-copy"><span className="pt-story-number">{t("功能演示 0")}{selected + 1} / {t(scenario.label)}</span><h3>{t(scenario.title)}</h3><p>{t(scenario.intro)}</p>
        <div className="pt-case-steps" role="group" aria-label={t("查看交接与就诊演示步骤")}>{scenario.steps.map((item, index) => <button key={item.label} aria-pressed={step === index} onClick={() => setStep(index)}><span>0{index + 1}</span><strong>{t(item.label)}</strong><span aria-hidden="true">{step === index ? '−' : '+'}</span></button>)}</div>
        <p className="pt-vision-live" aria-live="polite" aria-atomic="true">{t(frame.detail)}</p>
        <div className="pt-vision-action"><p>{t(scenario.feature)}</p><a className="pt-text-link" href={scenario.route}>{t(scenario.action)} <span aria-hidden="true">›</span></a>{selected === 0 && <a className="pt-vision-twin-link" href="#app/assistant">{t("在应用中询问当前宠物分身")} <span aria-hidden="true">›</span></a>}</div>
      </div>
    </div>
    <p className="pt-vision-future"><strong>{t("未来服务愿景")}</strong><span>{t("服务预约、下单、接单、市场与支付仍为规划中。")}</span></p>
  </section>
}

export default function Showcase() {
  const [selected, setSelected] = useState(0)
  const [selectedPet, setSelectedPet] = useState<PetKind>('mochi')
  const [menuOpen, setMenuOpen] = useState(false)
  const menuButton = useRef<HTMLButtonElement>(null)
  const navigationId = useId()
  const [motionPaused, setMotionPaused] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const root = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!menuOpen) return
    const close = () => setMenuOpen(false)
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
        menuButton.current?.focus()
      }
    }
    const desktop = window.matchMedia('(min-width: 701px)')
    const resized = () => { if (desktop.matches) close() }
    window.addEventListener('hashchange', close)
    window.addEventListener('keydown', escape)
    desktop.addEventListener('change', resized)
    return () => {
      window.removeEventListener('hashchange', close)
      window.removeEventListener('keydown', escape)
      desktop.removeEventListener('change', resized)
    }
  }, [menuOpen])
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const changed = () => setReducedMotion(preference.matches)
    preference.addEventListener('change', changed)
    return () => preference.removeEventListener('change', changed)
  }, [])
  useEffect(() => {
    if (!root.current || !('IntersectionObserver' in window)) return
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('pt-revealed')
          observer.unobserve(entry.target)
        }
      }
    }, { threshold: 0.12 })
    root.current.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element))
    return () => observer.disconnect()
  }, [])
  const story = STORIES[selected]
  const paused = motionPaused || reducedMotion
  function followMobileLink(event: MouseEvent<HTMLElement>) {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    const link = (event.target as HTMLElement).closest('a')
    const destination = link?.getAttribute('href')
    if (!destination) return
    event.preventDefault()
    setMenuOpen(false)
    window.location.hash = destination
    // Fragment navigation must finish before restoring focus to the closed menu.
    requestAnimationFrame(() => {
      document.getElementById(destination.slice(1))?.scrollIntoView()
      menuButton.current?.focus({ preventScroll: true })
    })
  }
  return <div className="showcase" id="product" ref={root} data-motion={paused ? 'paused' : 'running'}>
    <a className="pt-skip" href="#product-content">{t("跳到产品内容")}</a>
    <header className="pt-nav"><div className="pt-nav-inner">
      <a className="pt-brand" href="#product" aria-label={t("PawTwin 产品首页")}><PawMark />PawTwin</a>
      <nav className="pt-desktop-nav" aria-label={t("产品导航")}><a href="#features">{t("产品体验")}</a><a href="#cases">{t("日常案例")}</a><a href="#care">{t("如何使用")}</a><a href="#faq">{t("常见问题")}</a></nav>
      <div className="pt-nav-actions"><LanguageSwitch /><a className="pt-button pt-button-small" href="#app">{t("进入应用")}</a><button className="pt-mobile-toggle" type="button" ref={menuButton} aria-label={menuOpen ? t('收起产品导航') : t('展开产品导航')} aria-expanded={menuOpen} aria-controls={navigationId} onClick={() => setMenuOpen(!menuOpen)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">{menuOpen ? <path d="m6 6 12 12M6 18 18 6" /> : <path d="M4 8h16M4 16h16" />}</svg></button></div>
    </div><nav id={navigationId} className="pt-mobile-nav" aria-label={t("移动产品导航")} hidden={!menuOpen} onClick={followMobileLink}><a href="#features">{t("产品体验")}</a><a href="#cases">{t("日常案例")}</a><a href="#vision">{t("交接与就诊")}</a><a href="#care">{t("如何使用")}</a><a href="#faq">{t("常见问题")}</a></nav></header>
    <button className="pt-motion-toggle" aria-pressed={paused} disabled={reducedMotion} title={reducedMotion ? t('已遵循系统减少动画设置') : undefined} onClick={() => setMotionPaused(!motionPaused)}><span aria-hidden="true">{paused ? '▷' : 'Ⅱ'}</span>{reducedMotion ? t('已遵循系统减少动画') : paused ? t('开启动画') : t('暂停动画')}</button>
    <main className="pt-main" id="product-content">
      <section className="pt-hero">
        <div className="pt-hero-copy"><p className="pt-eyebrow"><span className="pt-hero-status" />{t("PawTwin · 家庭宠物照护")}</p>
          <h1>{t("宠物的每一天，")}<br />{t("全家")}<span className="pt-emphasis">{t("一起照顾。")}</span></h1>
          <p className="pt-lead">{t("家庭宠物照护与成长记录应用。")}<br />{t("安排今天的小事，接上家人的照顾，")}<br className="pt-desktop-break" />{t("把每一次成长和交接，都留得清楚。")}</p>
          <div className="pt-hero-actions"><a className="pt-button" href="#app">{t("进入本地体验")}<span aria-hidden="true">›</span></a><a className="pt-text-link" href="#features">{t("了解产品")} <span aria-hidden="true">›</span></a></div>
          <div className="pt-hero-reassurance"><span>{t("✓ 多宠物档案")}</span><span>{t("✓ 家庭协作")}</span><span>{t("✓ 有来源的记录")}</span></div>
          <p className="pt-hero-access">{t("当前为本地网页体验 · 进入应用后注册账号")}</p>
        </div>
        <div className="pt-hero-stage" aria-label={t("产品界面示意")}><div className="pt-stage-glow" /><ProductDevice pet={selectedPet} /><PhonePreview /></div>
        <div className="pt-product-strip"><span>{t("一个地方，接起它的日常。")}</span><a href="#features">{t("宠物档案")}</a><i aria-hidden="true" /><a href="#app/care">{t("家庭照护")}</a><i aria-hidden="true" /><a href="#app/growth">{t("成长记录")}</a><i aria-hidden="true" /><a href="#vision">{t("交接与就诊")}</a></div>
      </section>

      <ProductBenefits />

      <section className="pt-world" aria-labelledby="world-title"><div className="pt-world-copy" data-reveal><p className="pt-eyebrow">{t("每一个它，都有自己的样子。")}</p><h2 id="world-title">{t("各自的档案。")}<br /><span>{t("共同的关心。")}</span></h2><p>{t("温暖的橘猫，活泼的柯基，安静的奶牛猫，")}<br />{t("还有蓬松的卷毛犬。不同的它，同样值得被了解。")}</p><div className="pt-audience"><span>{t("初次养宠 · 从日常建立习惯")}</span><span>{t("家人共养 · 看清谁已接手")}</span><span>{t("多宠家庭 · 分别记录与回顾")}</span></div><p className="pg-current" aria-live="polite" aria-atomic="true">{t("当前产品示意：")}{PET_PROFILES[selectedPet].name} · {t(PET_PROFILES[selectedPet].species)}</p></div><div className="pt-world-scene pg-gallery" data-reveal><div className="pg-grid" role="group" aria-label={t("选择示例宠物")}>{(Object.keys(PET_PROFILES) as PetKind[]).map((pet, index) => <button className={`pg-pet pg-pet-${pet}`} type="button" key={pet} aria-label={t(`查看 ${PET_PROFILES[pet].name} 的产品示意`, `View ${PET_PROFILES[pet].name} product preview`)} aria-pressed={selectedPet === pet} onClick={() => setSelectedPet(pet)}><span className="pg-pet-number">0{index + 1}<span>{selectedPet === pet ? t('正在预览') : t('查看示意')}</span></span><span className={`pg-portrait ${pet === 'mochi' ? 'pt-world-cat' : ''}`}><PetPortrait pet={pet} /></span><strong>{PET_PROFILES[pet].name}<small>{t(PET_PROFILES[pet].species)}</small></strong><span className="pg-pet-detail">{t(PET_PROFILES[pet].description)}</span></button>)}</div><p className="pg-gallery-note">{t("四位虚构的小伙伴 · 点击切换设备与功能预览")}</p></div><p className="pt-world-foot">{t("角色与界面为产品示意 · 不创建真实宠物档案")}</p></section>

      <section className="pt-feature-section" id="features"><div className="pt-section-heading" data-reveal><p className="pt-eyebrow">{t("彼此连接的四种体验。")}</p><h2>{t("从一只宠物，到一个家。")}</h2><p>{t("让记录有归处，让照护有回应。")}</p></div>
        <div className="pt-story-tabs" role="group" aria-label={t("查看产品体验")}>{STORIES.map((s, index) => <button key={s.label} aria-pressed={index === selected} onClick={() => setSelected(index)}><span aria-hidden="true">{s.icon}</span>{t(s.label)}</button>)}</div>
        <div className={`pt-story pt-story-${selected}`}><div className="pt-story-visual"><StoryPreview key={selected} selected={selected} pet={selectedPet} /><p className="pt-story-caption">{t(story.note)}</p><small>{t("产品界面示意 · 功能以应用内实际状态为准")}</small></div><div className="pt-story-copy" aria-live="polite" aria-atomic="true"><span className="pt-story-number">0{selected + 1} / {t(story.label)}</span><h3 key={selected} aria-label={t(story.title)}><TitlePhrases text={story.title} /></h3><p>{t(story.text)}</p><div className="pt-tags">{story.tags.map(tag => <span key={tag}>{t(tag)}</span>)}</div><div className="pt-story-actions"><a className="pt-text-link" href={story.route}>{t("在应用中体验")} <span aria-hidden="true">›</span></a>{selected === 3 && <a className="pt-text-link" href="#alexa">{t("打开 Alexa+ 网页模拟器")} <span aria-hidden="true">›</span></a>}</div></div></div>
      </section>

      <CaseShowcase />
      <section className="pt-memory"><div className="pt-memory-copy" data-reveal><p className="pt-eyebrow">{t("每一份了解，都有来处。")}</p><h2>{t("记住它。")}<br /><span>{t("也记住为什么。")}</span></h2><p>{t("档案、实测成长和你确认的偏好，串起它的日常。")}<br />{t("留下来源，保留空白，让每一次回顾都有依据。")}</p><a className="pt-text-link" href="#features" onClick={() => setSelected(2)}>{t("探索成长记录")} <span aria-hidden="true">›</span></a></div><div className="pt-memory-records" data-reveal aria-label={t("记录来源示意")}><div className="pt-memory-line" />{[['01', '实测成长', '来自你记录的测量与时间'], ['02', '确认偏好', '由主人确认，可修改与删除'], ['03', '照护记录', '实际完成之后，才留下记录']].map(([number, title, text]) => <div className="pt-memory-record" key={number}><span>{number}</span><div><h3>{t(title)}</h3><p>{t(text)}</p></div></div>)}<small>{t("记录结构示意 · 非真实宠物数据")}</small></div></section>

      <VisionShowcase />

      <section className="pt-care-section" id="care"><div className="pt-section-heading" data-reveal><p className="pt-eyebrow">{t("从今天的一件小事开始。")}</p><h2>{t("让关心，变成有回应的日常。")}</h2><p>{t("认识它，一起安排，接手照顾，再回看成长。")}</p></div><div className="pt-steps">{[['01', '认识它', '注册账号、建立家庭，再创建自己的宠物档案。'], ['02', '一起安排', '邀请家人，安排需要完成的照护事项。'], ['03', '接手照顾', '领取任务，在实际完成后留下记录。'], ['04', '回看成长', '在日记与报告里，看见点滴变化。']].map(([number, title, text]) => <article key={number} data-reveal><span className="pt-step-number">{number}</span><h3>{t(title)}</h3><p>{t(text)}</p></article>)}</div><ProductStart /></section>

      <ProductFAQ />

      <section className="pt-closing" data-reveal><span className="pt-closing-paw"><PawMark /></span><p className="pt-eyebrow">{t("PawTwin · 一起，好好照顾。")}</p><h2>{t("它的每一天，")}<br /><span>{t("值得被好好记住。")}</span></h2><p>{t("从一份档案，到全家一起照顾的日常。")}</p><a className="pt-button" href="#app/home">{t("建立我的宠物小屋")} <span aria-hidden="true">›</span></a><small>{t("本地网页体验 · 照护由你掌握")}</small></section>
    </main>
    <footer className="pt-footer"><div className="pt-footer-inner"><div className="pt-footer-top"><div><a className="pt-brand" href="#product"><PawMark />PawTwin</a><p className="pt-footer-tagline">{t("家庭宠物照护与成长记录应用。")}<br />{t("一起照顾，也一起记得。")}</p></div><nav aria-label={t("页脚产品导航")}><strong>{t("了解 PawTwin")}</strong><a href="#features">{t("产品体验")}</a><a href="#cases">{t("日常案例")}</a><a href="#care">{t("开始使用")}</a><a href="#faq">{t("常见问题")}</a></nav><nav aria-label={t("更多体验")}><strong>{t("更多体验")}</strong><a href="#app">{t("家庭应用")}</a><a href="#alexa">{t("体验 Alexa+ 网页模拟")}</a><a href="#workbench">{t("照护工作台")}</a></nav></div><div className="pt-footer-status"><span>{t("当前体验状态")}</span><p>{t("家庭身份与记录为本地服务；分身默认使用本地规则，实际回答后端与依据见每轮回复。Alexa 为网页模拟，PawLink 项圈为概念，设备执行为模拟，云端能力尚未验证。")}</p></div><p className="pt-footer-bottom">{t("PawTwin · 每只宠物，各有不同。")}<a href="#app">{t("进入家庭应用")} <span aria-hidden="true">↗</span></a></p></div></footer>
  </div>
}
