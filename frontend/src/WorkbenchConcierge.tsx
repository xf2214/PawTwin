import { useState } from 'react'
import { CasePreview } from './CasePreview'
import { CONCIERGE_STEPS } from './concierge-scenario'
import { t } from './i18n'
import WorkspaceIcon from './WorkspaceIcon'

export default function WorkbenchConcierge() {
  const [step, setStep] = useState(0)
  const frame = CONCIERGE_STEPS[step]
  return <section className="wb-concierge" aria-label={t('宠物管家案例演示', 'Pet concierge scenarios')}>
    <div className="panel wb-concierge-intro">
      <div className="wb-card-heading"><div><p className="section-label">PET CONCIERGE · SCENARIOS</p><h2>{t('你只管问，它记得是哪一只。')}</h2></div><span className="wb-soft-badge">{t('预设案例 · 可切换', 'Preset scenarios · Explore')}</span></div>
      <p>{t('从饮食问题到日常状态，看看档案、确认偏好和记录如何随提问一起带入。', 'From food questions to everyday wellbeing, see how profiles, confirmed preferences and records accompany a question.')}</p>
      <div className="wb-concierge-choices" role="group" aria-label={t('选择宠物管家案例', 'Choose a pet concierge scenario')}>
        {CONCIERGE_STEPS.map((item, index) => <button type="button" key={item.label} className="ghost" aria-pressed={step === index} onClick={() => setStep(index)}><span>0{index + 1}</span>{t(item.label)}</button>)}
      </div>
      <p className="wb-concierge-current" aria-live="polite" aria-atomic="true">{t(frame.detail)}</p>
    </div>
    <div className="wb-concierge-layout">
      <div className="panel wb-concierge-stage"><CasePreview scenario="concierge" step={step} frame={frame} /></div>
      <aside className="panel wb-concierge-guide" aria-label={t('案例阅读提示', 'Scenario guide')}>
        <p className="section-label">CONTEXT, THEN CARE</p><h2>{t('每次回答，从已有资料开始。', 'Start with what is already known.')}</h2>
        <ol>
          <li><WorkspaceIcon name="family" /><div><strong>{t('先了解这只宠物', 'Know this pet first')}</strong><p>{t('品种、年龄和体重来自示例档案；切换案例会使用对应角色。', 'Breed, age and weight come from the sample profile. Each scenario uses its own pet.')}</p></div></li>
          <li><WorkspaceIcon name="care" /><div><strong>{t('参考已确认的偏好', 'Use confirmed preferences')}</strong><p>{t('Miso 的鸡肉偏好来自演示设定。推荐表达可能更喜欢，同时保留饮食注意事项。', 'Miso’s chicken preference is part of the fictional scenario. Suggestions express a possible preference and keep food precautions visible.')}</p></div></li>
          <li><WorkspaceIcon name="history" /><div><strong>{t('分清记录与健康判断', 'Separate records from health conclusions')}</strong><p>{t('Luna 的轨迹仅为模拟线索，回答会提示需要检查的情况与就医时机。', 'Luna’s simulated path is a clue. The reply highlights what to check and when veterinary care is needed.')}</p></div></li>
        </ol>
        <div className="wb-concierge-boundary"><strong>{t('当前为独立案例演示', 'A separate illustrative scenario')}</strong><p>{t('Miso 与 Luna 是固定的虚构角色。本页播放预设对话，不读取家庭档案、不发起模型调用或创建照护任务。', 'Miso and Luna are fictional characters. This page plays preset conversations without reading family profiles, calling a model or creating care tasks.')}</p></div>
        <button type="button" className="ghost" onClick={() => setStep(0)}>{t('重新开始演示', 'Restart scenario')}</button>
      </aside>
    </div>
  </section>
}
