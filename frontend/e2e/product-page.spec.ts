import { expect, test, type Page } from '@playwright/test'

const headline = /宠物的每一天，\s*全家一起照顾。/
const faqHeadline = /开始之前，\s*你可能想知道。/

function trackBusinessRequests(page: Page) {
  const requests: string[] = []
  page.on('request', request => {
    if (/^\/api(?:\/|$)/.test(new URL(request.url()).pathname)) requests.push(request.url())
  })
  return requests
}

async function expectNoHorizontalOverflow(page: Page) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
}

test('explains the product and opens native FAQs with the keyboard without business requests', async ({ page }, testInfo) => {
  const requests = trackBusinessRequests(page)
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: headline })).toBeVisible()
  await expect(page.locator('.pt-hero')).toContainText('家庭宠物照护与成长记录应用')
  await page.screenshot({ path: testInfo.outputPath('product-hero-1440.png'), animations: 'disabled' })

  const values = page.locator('section').filter({ has: page.getByRole('heading', { name: '让照顾更有默契。', exact: true }) })
  const experiences = values.getByRole('link')
  await expect(experiences).toHaveCount(3)
  for (const experience of await experiences.all()) {
    await expect(experience).toHaveAttribute('href', /^#(?:app\/(home|care|growth|assistant|family)|[a-z][a-z-]*)$/)
    const destination = await experience.getAttribute('href')
    if (destination && !destination.startsWith('#app/')) await expect(page.locator(destination)).toHaveCount(1)
  }

  await page.getByRole('navigation', { name: '产品导航', exact: true }).getByRole('link', { name: '常见问题', exact: true }).focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#faq$/)
  const faq = page.getByRole('region', { name: faqHeadline })
  await expect(faq.getByRole('heading', { name: faqHeadline })).toBeInViewport()
  for (const question of [
    '现在可以在哪里使用？',
    '家人和临时照护者有什么区别？',
    '宠物分身会自动执行照护吗？',
    '就诊信息卡会自动补齐资料吗？',
    '需要购买项圈或喂食器吗？',
  ]) {
    const disclosure = faq.locator('details').filter({ has: page.locator('summary', { hasText: question }) })
    const summary = disclosure.locator('summary')
    await expect(summary).toHaveAccessibleName(question)
    await expect(disclosure).toHaveJSProperty('open', false)
    await expect(disclosure.locator('p')).not.toBeVisible()
    await summary.focus()
    await page.keyboard.press('Enter')
    await expect(disclosure).toHaveJSProperty('open', true)
    await expect(disclosure.locator('p')).toBeVisible()
    await expect(summary).toBeFocused()
    await page.keyboard.press('Space')
    await expect(disclosure).toHaveJSProperty('open', false)
    await expect(disclosure.locator('p')).not.toBeVisible()
  }
  expect(requests).toEqual([])
})

test('reveals mobile navigation, restores focus on close and supports FAQ deep links at 320 and 390 pixels', async ({ page }, testInfo) => {
  const requests = trackBusinessRequests(page)
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 })
    await page.goto('/')
    const closedToggle = page.getByRole('button', { name: '展开产品导航', exact: true })
    const openToggle = page.getByRole('button', { name: '收起产品导航', exact: true })
    const navigation = page.getByRole('navigation', { name: '移动产品导航', exact: true })
    const faqLink = navigation.getByRole('link', { name: '常见问题', exact: true })
    await expect(closedToggle).toBeVisible()
    await expect(closedToggle).toHaveAttribute('aria-expanded', 'false')
    await expect(faqLink).not.toBeVisible()
    await expect(page.getByRole('heading', { level: 1, name: headline })).toBeVisible()
    await expectNoHorizontalOverflow(page)
    await page.screenshot({ path: testInfo.outputPath(`product-hero-${width}.png`), animations: 'disabled' })

    await closedToggle.click()
    await expect(openToggle).toHaveAttribute('aria-expanded', 'true')
    for (const label of ['产品体验', '日常案例', '交接与就诊', '如何使用', '常见问题']) {
      await expect(navigation.getByRole('link', { name: label, exact: true })).toBeVisible()
    }
    await expectNoHorizontalOverflow(page)
    await page.screenshot({ path: testInfo.outputPath(`product-menu-${width}.png`), animations: 'disabled' })
    await faqLink.click()
    await expect(page).toHaveURL(/#faq$/)
    await expect(closedToggle).toHaveAttribute('aria-expanded', 'false')
    await expect(closedToggle).toBeFocused()
    await expect(faqLink).not.toBeVisible()
    await expect(page.getByRole('heading', { name: faqHeadline })).toBeInViewport()

    await closedToggle.click()
    await expect(openToggle).toHaveAttribute('aria-expanded', 'true')
    await navigation.getByRole('link', { name: '产品体验', exact: true }).focus()
    await page.keyboard.press('Escape')
    await expect(closedToggle).toHaveAttribute('aria-expanded', 'false')
    await expect(closedToggle).toBeFocused()
    await expect(faqLink).not.toBeVisible()
    await expectNoHorizontalOverflow(page)

    await page.goto('/#faq')
    await expect(page.getByRole('region', { name: faqHeadline }).getByRole('heading', { name: faqHeadline })).toBeInViewport()
    await expect(closedToggle).toHaveAttribute('aria-expanded', 'false')
    await expectNoHorizontalOverflow(page)
  }
  expect(requests).toEqual([])
})

test('starts a pet profile from the care section through the login gate and returns to the product', async ({ page }) => {
  const requests = trackBusinessRequests(page)
  await page.goto('/#care')
  const care = page.locator('#care')
  await expect(care).toContainText('当前版本 · 本地网页体验')
  const start = care.getByRole('link', { name: '创建宠物档案', exact: true })
  await expect(start).toHaveAttribute('href', '#app/home')
  await start.scrollIntoViewIfNeeded()
  await expect(start).toBeInViewport()
  expect(requests).toEqual([])
  await start.focus()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#app\/home$/)
  await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'App 主导航', exact: true })).toHaveCount(0)

  const appRequestCount = requests.length
  await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  await expect(page).toHaveURL(/#product$/)
  await expect(page.getByRole('heading', { level: 1, name: headline })).toBeVisible()
  expect(requests).toHaveLength(appRequestCount)
})
