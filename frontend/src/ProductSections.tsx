import { t } from './i18n'
import './product-page.css'

const BENEFITS = [
  { number: '01', question: '今天谁来照顾？', title: '安排清楚，接手有数。', text: '换水、梳毛、陪玩，把需要做的小事交给家人。待办、领取和完成，各有清楚的状态。', detail: '安排 → 领取 → 完成后记录', link: '看看家庭照护', route: '#app/care', icon: '♡' },
  { number: '02', question: '它最近有什么变化？', title: '点滴记录，连成日常。', text: '把实际测量、饮食、照片和观察留在一起。回看成长时，也能找到时间和原始记录。', detail: '测量 · 日记 · 日／周报告', link: '看看成长记录', route: '#app/growth', icon: '↗' },
  { number: '03', question: '交接时该从哪里说起？', title: '带上了解，安心交接。', text: '给照护者一份有期限的只读资料；就诊前核对并导出信息卡，把已有记录带在身边。', detail: '临时只读分身 · 就诊信息卡', link: '了解交接与就诊', route: '#vision', icon: '↗' },
]

export function ProductBenefits() {
  return <section className="pt-benefits" id="why-pawtwin" aria-labelledby="benefits-title">
    <div className="pt-benefits-heading" data-reveal>
      <p className="pt-eyebrow">{t("关心它的人很多。日常，可以更清楚。")}</p>
      <h2 id="benefits-title">{t("让照顾更有默契。")}</h2>
      <p>{t("从“有没有做过”，到“下一步谁来”。")}<br />{t("把分散的照护和记录，放进全家共用的日常。")}</p>
    </div>
    <div className="pt-benefit-grid">{BENEFITS.map(item => <article key={item.number} data-reveal>
      <div className="pt-benefit-meta"><span>{item.number}</span><span aria-hidden="true">{item.icon}</span></div>
      <p className="pt-benefit-question">{t(item.question)}</p><h3>{t(item.title)}</h3><p>{t(item.text)}</p>
      <div className="pt-benefit-detail">{t(item.detail)}</div><a className="pt-text-link" href={item.route}>{t(item.link)}<span aria-hidden="true">›</span></a>
    </article>)}</div>
  </section>
}

const QUESTIONS = [
  { question: '现在可以在哪里使用？', answer: '当前提供本地网页体验。进入应用后注册账号、创建家庭，再添加宠物档案。家庭身份和记录保存在当前本地服务中；公网访问、云同步与跨设备部署尚未验证。' },
  { question: '家人和临时照护者有什么区别？', answer: '家庭成员按照角色参与照护。临时照护者只能在授权期限内查看指定宠物的资料并提问，不能修改记录、确认任务或操作设备。家庭管理员可以随时撤销临时访问。' },
  { question: '宠物分身会自动执行照护吗？', answer: '分身会依据档案、主人确认的偏好和已有记录回答，并说明来源。当前默认使用本地规则；提出的照护计划需要你明确确认。人工照护仍由人实际完成后记录。' },
  { question: '就诊信息卡会自动补齐资料吗？', answer: '不会。信息卡整理已保存的资料，保留测量时间、原始来源与缺项，默认排除演示测量。主人核对后可打印、另存 PDF 或下载 HTML，供就诊时参考；它不提供诊断，也不替代兽医检查。' },
  { question: '需要购买项圈或喂食器吗？', answer: '体验家庭档案、人工照护、成长记录、只读交接与就诊信息卡，不需要购买硬件。PawLink 项圈仍是概念，设备执行为模拟；Alexa+ 目前提供网页文字模拟体验。' },
]

export function ProductFAQ() {
  return <section className="pt-faq" id="faq" aria-labelledby="faq-title">
    <div className="pt-faq-intro" data-reveal><p className="pt-eyebrow">{t("常见问题")}</p><h2 id="faq-title">{t("开始之前，")}<br />{t("你可能想知道。")}</h2><p>{t("了解当前的体验方式，")}<br />{t("也了解每一份记录的边界。")}</p><a className="pt-text-link" href="#care">{t("看看如何开始")}<span aria-hidden="true">›</span></a></div>
    <div className="pt-faq-list">{QUESTIONS.map(item => <details key={item.question}><summary>{t(item.question)}<span aria-hidden="true">+</span></summary><p>{t(item.answer)}</p></details>)}</div>
  </section>
}

export function ProductStart() {
  return <div className="pt-start-panel" data-reveal>
    <div><span className="pt-release-label"><i aria-hidden="true" />{t("当前版本 · 本地网页体验")}</span><h3>{t("从它的名字开始。")}</h3><p>{t("进入应用，注册账号，建立家庭和宠物档案。")}<br />{t("再安排今天的第一件照护小事。")}</p></div>
    <div className="pt-start-actions"><a className="pt-button" href="#app/home">{t("创建宠物档案")}<span aria-hidden="true">›</span></a><span>{t("通过浏览器体验 · 无需购买硬件")}</span></div>
  </div>
}
