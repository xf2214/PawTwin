import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import FamilyApp from './FamilyApp'
import CareAccess from './CareAccess'
import Showcase, { PawMark } from './Showcase'
import './styles.css'
import './application-shell.css'
import './workspace-theme.css'
import { LanguageSwitch, t, useLanguage } from './i18n'

function Root() {
  const language = useLanguage()
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const changed = () => setHash(window.location.hash)
    window.addEventListener('hashchange', changed)
    return () => window.removeEventListener('hashchange', changed)
  }, [])
  const mode = hash.startsWith('#pet-access=') ? 'access' : hash === '#app' || hash.startsWith('#app/') || hash === '#alexa' ? 'family' : hash.startsWith('#workbench/') || ['#workbench', '#home'].includes(hash) ? 'workbench' : 'product'
  useEffect(() => {
    document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN'
    document.title = `PawTwin · ${t(mode === 'access' ? '临时只读分身' : hash === '#alexa' ? 'Alexa+ 网页模拟器' : mode === 'product' ? '家庭宠物照护' : mode === 'family' ? '家庭应用' : '照护工作台')}`
    const description = t('家庭照护、成长记录、临时只读交接与就诊资料，一起留得清楚。', 'Keep family care, growth records, temporary read-only handoffs, and visit information together.')
    document.querySelector('meta[name="description"]')?.setAttribute('content', description)
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', description)
    document.querySelector('meta[property="og:title"]')?.setAttribute('content', document.title)
  }, [mode, hash, language])
  useEffect(() => {
    const section = mode === 'product' && hash ? document.getElementById(hash.slice(1)) : null
    if (section) section.scrollIntoView()
    else window.scrollTo(0, 0)
  }, [mode, hash])
  if (mode === 'access') {
    let token = ''
    try { token = decodeURIComponent(hash.slice('#pet-access='.length)) } catch { /* Invalid links fail closed. */ }
    return <><div className="access-language"><LanguageSwitch /></div><CareAccess key={hash} token={token} /></>
  }
  if (mode === 'product') return <Showcase />
  return <div className={`application-shell application-shell--${mode}`}>
    <header className="as-header">
      <a className="as-brand" href="#product" aria-label={t('PawTwin 产品首页')}><PawMark />PawTwin<span>{t(mode === 'family' ? '家庭应用' : '照护工作台')}</span></a>
      <nav aria-label={t('页面导航')}><a href="#product">{t('产品介绍')}</a><a href="#alexa">{t('Alexa+ 模拟器')}</a><a href={mode === 'family' ? '#workbench' : '#app'}>{t(mode === 'family' ? '原工作台' : '家庭应用')} <span aria-hidden="true">↗</span></a></nav>
      <LanguageSwitch />
    </header>
    {mode === 'family' ? <FamilyApp alexaMode={hash === '#alexa'} /> : <App />}
  </div>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
