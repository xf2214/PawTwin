import { expect, test, type Locator, type Page } from '@playwright/test'
import { login, PASSPHRASE, resetDemo } from './helpers'

test.setTimeout(35_000)

const steps = [
  { zh: '小狗饮食', en: 'Dog food safety', title: '这只小狗，能吃巧克力吗？' },
  { zh: '猫咪状态', en: 'Cat wellbeing', title: '猫咪没精神，先看哪些记录？' },
  { zh: '上下文随行', en: 'Context included', title: '少一次介绍，多一份了解。' },
] as const

function scenario(page: Page, english = false) {
  return page.getByRole('region', { name: english ? 'Pet concierge scenarios' : '宠物管家案例演示', exact: true })
}

function choices(region: Locator, english = false) {
  return region.getByRole('group', { name: english ? 'Choose a pet concierge scenario' : '选择宠物管家案例', exact: true }).getByRole('button')
}

async function signInAtCase(page: Page, english = false) {
  await page.goto('/#workbench/concierge')
  await page.getByLabel(english ? 'Demo passphrase' : '演示口令', { exact: true }).fill(PASSPHRASE)
  await page.getByRole('button', { name: english ? 'Sign in to demo' : '登录演示', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: english ? 'Pet concierge' : '宠物管家', exact: true })).toBeVisible()
  const region = scenario(page, english)
  await expect(region.locator('.pt-case-preview[data-case="concierge"]')).toBeVisible()
  return region
}

async function selectWithKeyboard(page: Page, region: Locator, index: number, english = false) {
  const buttons = choices(region, english)
  await expect(buttons).toHaveCount(3)
  await expect(buttons.nth(index)).toContainText(english ? steps[index].en : steps[index].zh)
  await buttons.nth(index).focus()
  await page.keyboard.press(index === 1 ? 'Space' : 'Enter')
  await expect(buttons.nth(index)).toBeFocused()
  await expect(buttons.nth(index)).toHaveAttribute('aria-pressed', 'true')
  const preview = region.locator('.pt-case-preview[data-case="concierge"]')
  if (!english) await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(steps[index].title)
  await expect(preview.locator('footer')).toContainText(english ? 'Alexa is a web simulation' : 'Alexa 为网页模拟')
  return preview
}

test.describe('English default at the protected deep link', () => {
  // The production language key is pawtwin-language. Empty storage must use
  // English, independently of the Chinese state shared by ordinary e2e tests.
  test.use({ storageState: { cookies: [], origins: [] } })

  test('requires demo login and opens the requested case without the Mochi facts card', async ({ page }) => {
    await page.goto('/#workbench/concierge')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.getByLabel('Demo passphrase', { exact: true })).toBeVisible()
    await expect(scenario(page, true)).toHaveCount(0)
    await expect(page.getByTestId('facts')).toHaveCount(0)
    const region = await signInAtCase(page, true)
    await expect(page).toHaveURL(/#workbench\/concierge$/)
    const nav = page.getByRole('navigation', { name: 'Workbench navigation', exact: true })
    await expect(nav.getByRole('link', { name: 'Pet concierge', exact: true })).toHaveAttribute('aria-current', 'page')
    await expect(region).toContainText('Miso')
    await expect(region).toContainText('Fictional pet profile')
    await expect(page.getByTestId('facts')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Send food request', exact: true })).toHaveCount(0)
    await page.getByRole('button', { name: 'Sign out', exact: true }).click()
    await expect(page.getByRole('button', { name: 'Sign in to demo', exact: true })).toBeVisible()
    await expect(scenario(page, true)).toHaveCount(0)
  })
})

test('keyboard scenarios and language changes preserve pet context without writing business records', async ({ page }) => {
  const region = await signInAtCase(page)
  const mutations: string[] = []
  const errors: string[] = []
  page.on('request', request => {
    if (new URL(request.url()).pathname.startsWith('/api/') && !['GET', 'HEAD', 'OPTIONS'].includes(request.method())) mutations.push(`${request.method()} ${new URL(request.url()).pathname}`)
  })
  page.on('pageerror', error => errors.push(error.message))

  let preview = await selectWithKeyboard(page, region, 0)
  for (const context of ['Miso', '9.40 kg', '彭布罗克威尔士柯基犬', '主人确认的偏好', '喜欢鸡肉']) await expect(preview).toContainText(context)
  const reply = preview.locator('.pc-assistant-message')
  await expect(reply).toContainText('巧克力对狗有中毒风险，与品种无关')
  await expect(reply).toContainText('少量原味全熟去骨鸡肉')
  await expect(reply).toContainText('先确认不过敏')
  await expect(reply).toContainText('若已经误食巧克力，请立即联系兽医')

  preview = await selectWithKeyboard(page, region, 1)
  for (const context of ['Luna', '3.68 kg', '家猫', '3 岁']) await expect(preview).toContainText(context)
  await expect(reply).toContainText('但不能据此排除生病')
  for (const check of ['进食', '饮水', '排尿', '呼吸', '呕吐', '腹泻']) await expect(reply).toContainText(check)
  await expect(reply).toContainText('呼吸困难或排尿困难应立即就医')
  const activity = preview.getByRole('region', { name: 'Luna 的模拟家庭活动记录', exact: true })
  await expect(activity.getByRole('listitem')).toHaveCount(3)
  await expect(activity).toContainText('到过饮水区 ≠ 已饮水')

  await page.getByRole('button', { name: 'English', exact: true }).click()
  const englishRegion = scenario(page, true)
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expect(choices(englishRegion, true).nth(1)).toHaveAttribute('aria-pressed', 'true')
  await expect(englishRegion).toContainText('Luna')
  await expect(englishRegion).toContainText('3.68 kg')
  await expect(englishRegion).toContainText('cannot rule out illness')
  await expect(englishRegion).toContainText('A visit to the water area does not confirm drinking')
  preview = await selectWithKeyboard(page, englishRegion, 2, true)
  await expect(preview.getByRole('heading', { level: 4, name: 'A new chat without a pet profile', exact: true })).toBeVisible()
  await expect(preview.getByRole('heading', { level: 4, name: 'PawTwin Pet Concierge', exact: true })).toBeVisible()
  const context = preview.locator('.pc-carried-context')
  for (const value of ['Miso', '9.40 kg', 'chicken', 'Owner confirmed']) await expect(context).toContainText(value)
  await page.getByRole('button', { name: '中文', exact: true }).click()
  await expect(choices(region).nth(2)).toHaveAttribute('aria-pressed', 'true')
  await expect(region).toContainText('主人已确认')
  expect(mutations, 'illustrative case selection and language changes must not create tasks, memories or model calls').toEqual([])
  expect(errors).toEqual([])
})

test('visiting the concierge preserves ownership of an accepted request until its real state returns', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  let release!: () => void
  let captured!: () => void
  let delivered!: () => void
  let first = true
  let runId = ''
  let events = 0
  const gate = new Promise<void>(resolve => { release = resolve })
  const reached = new Promise<void>(resolve => { captured = resolve })
  const finished = new Promise<void>(resolve => { delivered = resolve })
  page.on('request', request => { if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/events') events++ })
  // Hold only the browser delivery of a real stored run. The API response is
  // unchanged, and no synthetic run/proposal/approval is manufactured here.
  await page.route('**/api/runs/*', async route => {
    if (route.request().method() !== 'GET' || !first) { await route.continue(); return }
    first = false
    const response = await route.fetch()
    runId = (await response.json()).run_id
    captured()
    await gate
    try { await route.fulfill({ response }) } catch { /* A failed implementation may abort tracking on route change. */ } finally { delivered() }
  })
  try {
    await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
    await reached
    const nav = page.getByRole('navigation', { name: '工作台导航', exact: true })
    await nav.getByRole('link', { name: '宠物管家', exact: true }).click()
    await expect(scenario(page)).toBeVisible()
    await selectWithKeyboard(page, scenario(page), 1)
    await nav.getByRole('link', { name: '请求与审批', exact: true }).click()
    await expect(page.getByRole('button', { name: '发送吃饭请求', exact: true })).toBeDisabled()
    await expect(page.getByRole('button', { name: '发送互动请求', exact: true })).toBeDisabled()
    expect(events).toBe(1)
    release()
    await finished
    await page.unroute('**/api/runs/*')
    await expect(page.getByTestId('active-run-id')).toHaveText(runId)
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
    await expect(page.getByTestId('proposal-action')).toContainText('出粮 15 克')
    expect(events, 'switching a demonstration page must not resend the accepted event').toBe(1)
    await page.getByTestId('decline').click()
    await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
    await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  } finally { release() }
})

test('all three workbench examples remain readable and keyboard reachable at four widths', async ({ page }, testInfo) => {
  test.setTimeout(60_000)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  const region = await signInAtCase(page)
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 })
    for (let index = 0; index < steps.length; index++) {
      const preview = await selectWithKeyboard(page, region, index)
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      await expect.poll(() => preview.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true)
      const button = choices(region).nth(index)
      await button.scrollIntoViewIfNeeded()
      const bounds = await button.boundingBox()
      expect(bounds && bounds.x >= 0 && bounds.x + bounds.width <= width && bounds.y >= 0 && bounds.y + bounds.height <= 1000, `${width}px case ${index + 1} must be keyboard reachable within the viewport`).toBe(true)
      if (index < 2) await region.screenshot({ path: testInfo.outputPath(`workbench-concierge-${width}-step-${index + 1}.png`), animations: 'disabled' })
    }
  }
})
