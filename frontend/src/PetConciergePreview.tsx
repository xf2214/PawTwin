import { t } from './i18n'
import { PetPortrait } from './PetPortrait'
import './pet-concierge.css'

type PreviewFrame = { title: string; status: string; detail: string }
type ConciergeIcon = 'spark' | 'profile' | 'check' | 'link' | 'arrow' | 'voice'

function Icon({ name }: { name: ConciergeIcon }) {
  const paths: Record<ConciergeIcon, string> = {
    spark: 'm12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6L12 3Z',
    profile: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-2a8 8 0 0 1 16 0v2',
    check: 'm5 12 4 4L19 6',
    link: 'M9 7H6a3 3 0 0 0-3 3v7a3 3 0 0 0 3 3h7a3 3 0 0 0 3-3v-3M13 4h7v7m0-7L10 14',
    arrow: 'M4 12h15m-5-5 5 5-5 5',
    voice: 'M5 10v4m4-7v10m4-13v16m4-12v8m4-6v4',
  }
  return <svg className="pc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
}

function PetProfile({ cat = false }: { cat?: boolean }) {
  return <div className={`pc-profile ${cat ? 'pc-profile-cat' : ''}`}>
    <span className="pc-pet-art"><PetPortrait pet={cat ? 'luna' : 'miso'} /></span>
    <div className="pc-profile-copy">
      <span className="pc-label">{t('宠物资料 · 虚构', 'Fictional pet profile')}</span>
      <strong className="pc-pet-name">{cat ? 'Luna' : 'Miso'}</strong>
      <span className="pc-pet-breed">{cat ? t('家猫 · 短毛黑白双色', 'Domestic shorthair · Bicolor') : t('彭布罗克威尔士柯基犬', 'Pembroke Welsh Corgi')}</span>
      <div className="pc-profile-chips">
        <span>{cat ? t('雌性', 'Female') : t('雄性', 'Male')}</span>
        <span>{cat ? t('3 岁', '3 years') : t('2 岁', '2 years')}</span>
        <span>{cat ? '3.68 kg' : '9.40 kg'}</span>
      </div>
    </div>
    {!cat && <div className="pc-preference"><Icon name="check" /><span>{t('主人确认的偏好', 'Owner-confirmed preference')}<strong>{t('喜欢鸡肉', 'Likes chicken')}</strong></span></div>}
  </div>
}

function OwnerQuestion({ cat = false }: { cat?: boolean }) {
  return <div className="pc-owner-message">
    <span className="pc-speaker">{t('主人', 'Owner')}</span>
    <p>{cat ? t('我的猫咪有点没有精神，怎么办？', 'My cat seems a little low on energy. What should I do?') : t('我的这只小狗能吃巧克力吗？', 'Can my dog eat chocolate?')}</p>
  </div>
}

function AssistantReply({ cat = false }: { cat?: boolean }) {
  return <div className="pc-assistant-message">
    <span className="pc-alexa-mark"><Icon name="voice" /></span>
    <div className="pc-answer">
      <span className="pc-speaker">{t('Alexa · 预设回复', 'Alexa · Preset reply')}</span>
      {cat ? <>
        <p><strong>{t('Luna 是 3 岁雌性家猫。', 'Luna is a 3-year-old female domestic shorthair.')}</strong> {t('模拟活动记录接近平日，但不能据此排除生病。', 'Her simulated activity is close to her usual pattern, but that cannot rule out illness.')}</p>
        <p>{t('请检查进食、饮水、排尿、呼吸，有无呕吐或腹泻。', 'Check her eating, drinking, urination and breathing, and look for vomiting or diarrhea.')}</p>
        <p className="pc-care-note">{t('持续没精神请尽快就诊；呼吸困难或排尿困难应立即就医。', 'See a vet promptly if low energy persists. Difficulty breathing or urinating needs immediate veterinary care.')}</p>
      </> : <>
        <p><strong>{t('Miso 是你的彭布罗克威尔士柯基犬。', 'Miso is your Pembroke Welsh Corgi.')}</strong> {t('不可以。巧克力对狗有中毒风险，与品种无关。', 'No. Chocolate can poison dogs, regardless of breed.')}</p>
        <p>{t('按你确认的鸡肉偏好，少量原味全熟去骨鸡肉可能更合它口味；作为零食前，先确认不过敏。', 'Since you confirmed he likes chicken, a small plain, fully cooked, boneless piece may suit his tastes. Check for allergies before offering it as a treat.')}</p>
        <p className="pc-care-note">{t('若已经误食巧克力，请立即联系兽医。', 'If he has already eaten chocolate, contact a vet immediately.')}</p>
      </>}
      <div className="pc-answer-basis"><span>{t('参考依据', 'Context used')}</span><span><Icon name="profile" />{t('宠物档案示例', 'Sample pet profile')}</span><span><Icon name="check" />{cat ? t('模拟活动记录', 'Simulated activity') : t('已确认偏好示例', 'Sample confirmed preference')}</span></div>
    </div>
  </div>
}

function ActivityTrace() {
  return <section className="pc-activity" aria-label={t('Luna 的模拟家庭活动记录', 'Luna’s simulated household activity record')}>
    <div className="pc-activity-heading"><strong>{t('今日家庭活动记录', 'Today’s household activity')}</strong><span>{t('模拟轨迹', 'Simulated trace')}</span></div>
    <svg className="pc-activity-map" viewBox="0 0 360 96" role="img" aria-label={t('示意轨迹从窗边经过客厅到饮水区', 'Illustrative path from the window through the living room to the water area')}>
      <rect x="1" y="1" width="358" height="94" rx="13" fill="#f4f5ed" stroke="#dce3d8" />
      <path d="M116 1v26m0 38v30M243 1v26m0 38v30" stroke="#dce3d8" strokeWidth="2" />
      <rect x="15" y="13" width="53" height="33" rx="3" fill="#e4ece4" stroke="#c2d4cb" />
      <path d="M41 14v31M16 29h51" stroke="#c2d4cb" strokeWidth="2" />
      <path d="M154 14h51a8 8 0 0 1 8 8v23h-67V22a8 8 0 0 1 8-8Z" fill="#d6dfcf" />
      <rect x="142" y="25" width="9" height="27" rx="4" fill="#b9cbb8" />
      <rect x="208" y="25" width="9" height="27" rx="4" fill="#b9cbb8" />
      <path d="M153 39h53v13h-53" fill="#c4d2bd" />
      <ellipse cx="316" cy="33" rx="17" ry="7" fill="#b3cfc8" />
      <path d="M300 33h32l-4 13h-24Z" fill="#d3e6e0" stroke="#a3bdb6" />
      <ellipse cx="316" cy="33" rx="12" ry="3" fill="#93bdbb" />
      <path d="M54 67c30 18 54-33 91-6s52 24 80 0 57-7 81 8" stroke="#658d7c" strokeWidth="2" strokeDasharray="4 5" strokeLinecap="round" fill="none" />
      <circle cx="54" cy="67" r="8" fill="#e9f0e7" stroke="#73947c" strokeWidth="2" />
      <circle cx="179" cy="72" r="8" fill="#e9f0e7" stroke="#73947c" strokeWidth="2" />
      <circle cx="306" cy="69" r="9" fill="#3d7b71" stroke="#fffdf8" strokeWidth="3" />
    </svg>
    <ol className="pc-activity-log">
      <li><time>07:40</time><span>{t('窗边', 'Window')}</span></li>
      <li><time>12:20</time><span>{t('客厅', 'Living room')}</span></li>
      <li><time>18:10</time><span>{t('饮水区', 'Water area')}</span></li>
    </ol>
    <p>{t('到过饮水区 ≠ 已饮水。轨迹不能用于判断健康。', 'A visit to the water area does not confirm drinking. A path cannot establish health.')}</p>
  </section>
}

function References({ cat = false }: { cat?: boolean }) {
  return <div className="pc-references"><span>{t('健康文案参考', 'Health copy references')}</span>{cat ? <a href="https://vcahospitals.com/know-your-pet/recognizing-signs-of-illness-in-cats" target="_blank" rel="noreferrer">{t('VCA · 猫咪生病的迹象', 'VCA · Signs of illness in cats')}<Icon name="link" /></a> : <><a href="https://www.merckvetmanual.com/toxicology/food-hazards/chocolate-toxicosis-in-animals" target="_blank" rel="noreferrer">{t('Merck · 巧克力中毒', 'Merck · Chocolate toxicity')}<Icon name="link" /></a><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet" target="_blank" rel="noreferrer">{t('PDSA · 狗狗饮食', 'PDSA · Dog diet')}<Icon name="link" /></a></>}</div>
}

function ContextComparison() {
  return <div className="pc-comparison">
    <div className="pc-context-summary"><span className="pc-context-pet"><PetPortrait pet="miso" /></span><div><span className="pc-label">{t('同一个问题，同一只 Miso', 'Same question. Same Miso.')}</span><strong>{t('少重复一点，多了解一点。', 'Less repeating. More understanding.')}</strong></div></div>
    <section className="pc-comparison-card pc-new-session">
      <div className="pc-comparison-title"><span className="pc-session-icon"><Icon name="profile" /></span><h4>{t('没有宠物资料的新会话', 'A new chat without a pet profile')}</h4></div>
      <span className="pc-speaker">{t('主人 · 重新补充背景', 'Owner · Repeating the context')}</span>
      <p>{t('我的狗 Miso 是彭布罗克威尔士柯基犬，雄性，2 岁，9.40 kg，喜欢鸡肉。它能吃巧克力吗？', 'My dog Miso is a male Pembroke Welsh Corgi, 2 years old, weighing 9.40 kg. He likes chicken. Can he eat chocolate?')}</p>
      <span className="pc-comparison-caption">{t('需要在问句中重新补充宠物资料', 'Pet details must be repeated in the question')}</span>
    </section>
    <div className="pc-comparison-bridge"><Icon name="arrow" /><span>{t('背景随问题一起带入', 'The context comes with the question')}</span></div>
    <section className="pc-comparison-card pc-pawtwin-session">
      <div className="pc-comparison-title"><span className="pc-session-icon"><Icon name="spark" /></span><h4>{t('PawTwin 宠物管家', 'PawTwin Pet Concierge')}</h4></div>
      <span className="pc-speaker">{t('主人', 'Owner')}</span>
      <p>{t('我的这只小狗能吃巧克力吗？', 'Can my dog eat chocolate?')}</p>
      <div className="pc-carried-context">
        <span className="pc-carried-label"><Icon name="check" />{t('自动带入的上下文 · 示意', 'Automatically included context · Preview')}</span>
        <div className="pc-context-chips"><span>Miso</span><span>{t('彭布罗克威尔士柯基犬', 'Pembroke Welsh Corgi')}</span><span>{t('雄性 · 2 岁 · 9.40 kg', 'Male · 2 years · 9.40 kg')}</span><span>{t('喜欢鸡肉 · 主人已确认', 'Likes chicken · Owner confirmed')}</span></div>
      </div>
      <span className="pc-comparison-caption">{t('档案与确认偏好随问句呈现', 'Profile and confirmed preferences accompany the question')}</span>
    </section>
    <p className="pc-comparison-boundary">{t('已保存的资料随问句带入，更换宠物后使用对应档案。', 'Saved details accompany the question; switching pets uses that pet’s profile.')}</p>
  </div>
}

export function PetConciergePreview({ step, frame }: { step: number; frame: PreviewFrame }) {
  const stage = Math.max(0, Math.min(2, step))
  return <div className="pc-preview">
    <div className="pc-topline"><span><Icon name="spark" />{t('宠物管家 · 产品示意', 'Pet Concierge · Product preview')}</span><span>{t('步骤', 'Step')} {stage + 1} / 3</span></div>
    <div className="pc-frame-heading"><h3>{t(frame.title)}</h3><span className="pc-status"><i />{t(frame.status)}</span></div>
    {stage === 2 ? <ContextComparison /> : <>
      <PetProfile cat={stage === 1} />
      <div className="pc-context-ribbon"><Icon name="link" /><span>{t('提问时，一起带上它的资料', 'Their context travels with the question')}</span></div>
      <div className="pc-conversation" aria-label={t('主人与 Alexa 的预设对话示意', 'Preset conversation between the owner and Alexa')}><OwnerQuestion cat={stage === 1} />{stage === 1 && <ActivityTrace />}<AssistantReply cat={stage === 1} /></div>
      <References cat={stage === 1} />
    </>}
    <p className="pc-frame-detail">{t(frame.detail)}</p>
    <footer className="pc-demo-boundary"><span className="pc-demo-mark">{t('演示', 'DEMO')}</span><span>{t('预设对话与活动轨迹为虚构示意 · Alexa 为网页模拟', 'Preset conversations and activity traces are fictional illustrations · Alexa is a web simulation')}<small>{t('非实时 AI 或实际追踪，不进行临床诊断。', 'No real-time AI, actual tracking or clinical diagnosis.')}</small></span></footer>
  </div>
}
