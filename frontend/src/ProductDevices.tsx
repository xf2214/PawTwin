import { t } from './i18n'
import type { ReactNode } from 'react'
import { PET_PROFILES, PetPortrait, type PetKind } from './PetPortrait'
import './device-preview.css'

type IconName = 'home' | 'care' | 'growth' | 'twin' | 'check' | 'arrow' | 'diary' | 'more' | 'water'
export function ProductIcon({ name, className }: { name: IconName; className?: string }) {
  const paths: Record<IconName, ReactNode> = {
    home: <><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" /><path d="M9 7h6" /></>,
    care: <path d="M20.8 5.2a5.5 5.5 0 0 0-7.8 0l-1 1-1-1a5.5 5.5 0 0 0-7.8 7.8L12 22l8.8-9a5.5 5.5 0 0 0 0-7.8Z" />,
    growth: <><path d="M4 4v16h16M7 15l5-5 4 3 5-8" /><path d="M17 5h4v4" /></>,
    twin: <><path d="m12 2 2.8 7.2L22 12l-7.2 2.8L12 22l-2.8-7.2L2 12l7.2-2.8Z" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    arrow: <path d="m9 5 7 7-7 7" />,
    diary: <><rect x="4" y="3" width="16" height="18" rx="3" /><path d="M8 3v18m4-12h4m-4 4h4" /></>,
    more: <><circle cx="5" cy="12" r=".8" /><circle cx="12" cy="12" r=".8" /><circle cx="19" cy="12" r=".8" /></>,
    water: <path d="M12 2s7 8 7 13a7 7 0 0 1-14 0c0-5 7-13 7-13Zm-3 14c0 2 1 3 3 3" />,
  }
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

export function TabletPreview({ pet, compact = false, room }: { pet: PetKind; compact?: boolean; room: ReactNode }) {
  const profile = PET_PROFILES[pet]
  return <div className={`pt-device pd-tablet ${compact ? 'pt-device-compact' : ''}`} data-pet={pet} aria-label={t("平板应用界面示意")}>
    <div className="pt-device-screen pd-tablet-screen">
      <div className="pd-shell">
        <aside className="pd-sidebar">
          <div className="pd-logo"><span><ProductIcon name="care" /></span><strong>PawTwin</strong></div>
          <span className="pd-sidebar-caption">{t("家庭空间")}</span>
          <div className="pd-side-items" aria-label={t("界面导航示意")}>{([['home', '今日'], ['care', '照护'], ['growth', '成长'], ['twin', '分身']] as const).map(([icon, name], index) => <span key={name} className={index === 0 ? 'is-active' : ''}><ProductIcon name={icon} />{t(name)}</span>)}</div>
          <div className="pd-side-bottom"><div className="pd-member-avatars"><span>{t("你")}</span><span>{t("林")}</span></div><small>{t("一起，好好照顾。")}</small></div>
        </aside>
        <div className="pd-main">
          <header className="pd-app-header"><div><small>YOUR EVERYDAY, TOGETHER</small><h3>{t(`给 ${profile.name} 的每一天。`, `Every day with ${profile.name}.`)}</h3></div><span className="pd-profile-chip"><PetPortrait pet={pet} /><span>{profile.name}</span><ProductIcon name="arrow" /></span></header>
          <div className="pd-main-grid">
            <div className="pd-room-card"><div className="pd-card-heading"><strong>{t("它的小屋")}</strong><span>{t(profile.species)}</span></div><div className="pd-room-art">{room}</div><div className="pd-room-note"><span><i />{t("属于它的日常空间")}</span><ProductIcon name="home" /></div></div>
            <section className="pd-care-card" aria-label={t("照护列表示意")}><div className="pd-card-heading"><strong>{t("今日照护")}</strong><ProductIcon name="more" /></div><p>{t("下一件小事，一起接上。")}</p><div className="pd-care-rows">{([
              ['water', '换一碗新鲜的水', '等待家人接手', '待领取'],
              ['care', '留一点陪玩的时间', '小林已接手', '已领取'],
              ['check', '梳理一下毛发', '实际完成后记录', '已记录'],
            ] as const).map(([icon, title, detail, state], index) => <div key={title} className={`pd-care-row pd-care-row-${index}`}><span className="pd-task-icon"><ProductIcon name={icon} /></span><span><strong>{t(title)}</strong><small>{t(detail)}</small></span><em>{t(state)}</em></div>)}</div><div className="pd-care-footer"><span className="pd-member-avatars"><span>{t("你")}</span><span>{t("林")}</span></span><span>{t("照护的每一步，都有回应。")}</span></div></section>
          </div>
          <div className="pd-record-strip"><span className="pd-record-icon"><ProductIcon name="diary" /></span><div><strong>{t("把点滴，留在日常里。")}</strong><small>{t("实测记录 · 照片日记 · 确认偏好")}</small></div><span className="pd-source-chip">{t("保留来源")}<ProductIcon name="check" /></span></div>
          <div className="pd-app-foot"><span>{t("界面内容为虚构示意")}</span><span>{t("产品界面示意")}</span></div>
        </div>
      </div>
    </div>
  </div>
}

export function PhonePreview() {
  return <div className="pt-phone pd-phone" aria-label={t("手机应用界面示意")}>
    <div className="pd-phone-screen">
      <div className="pd-phone-hardware"><span /><i /></div>
      <div className="pd-phone-top"><strong>PawTwin</strong><span><ProductIcon name="more" /></span></div>
      <div className="pd-phone-title"><small>EVERYDAY TOGETHER</small><h3>{t("Luna 的日常。")}</h3></div>
      <div className="pd-phone-journal"><span className="pd-phone-leaf pd-phone-leaf-one" /><span className="pd-phone-leaf pd-phone-leaf-two" /><PetPortrait pet="luna" /><div><span>{t("照片日记")}</span><h4>{t("午后的陪伴。")}</h4></div></div>
      <div className="pd-phone-section"><strong>{t("今日照护")}</strong><ProductIcon name="arrow" /></div>
      <div className="pd-phone-task"><span><ProductIcon name="water" /></span><div><strong>{t("换一碗新鲜的水")}</strong><small>{t("等待家人接手")}</small></div><i /></div>
      <div className="pd-phone-tabs" aria-label={t("手机导航示意")}>{([['home', '日常'], ['care', '照护'], ['growth', '成长']] as const).map(([icon, text], index) => <span className={index === 0 ? 'is-active' : ''} key={text}><ProductIcon name={icon} /><small>{t(text)}</small></span>)}</div>
      <small className="pd-phone-caption">{t("产品界面示意 · 虚构内容")}</small><span className="pd-phone-home-indicator" />
    </div>
  </div>
}
