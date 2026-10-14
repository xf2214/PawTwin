import { expect, test, type Locator, type Page } from '@playwright/test'

const petNames = ['Mochi', 'Miso', 'Luna', 'Coco'] as const
const widths = [320, 390, 768, 1024, 1440] as const
const scenarios = [
  { label: '家庭交接', id: 'handoff', title: '你出门了，照顾还在继续。' },
  { label: '成长回顾', id: 'growth', title: '一次次记录，看见成长的轨迹。' },
  { label: '偏好接续', id: 'preferences', title: '下一次交流，从已有了解开始。' },
] as const

function observePublicPage(page: Page) {
  const businessRequests: string[] = []
  const errors: string[] = []
  page.on('request', request => {
    if (new URL(request.url()).pathname.startsWith('/api/')) businessRequests.push(request.url())
  })
  page.on('pageerror', error => errors.push(error.message))
  return () => {
    expect(businessRequests).toEqual([])
    expect(errors).toEqual([])
  }
}

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
}

async function selectPet(page: Page, gallery: Locator, name: typeof petNames[number]) {
  const choices = gallery.getByRole('group', { name: '选择示例宠物', exact: true })
  const selected = choices.getByRole('button', { name: `查看 ${name} 的产品示意`, exact: true })
  await selected.focus()
  await page.keyboard.press('Enter')
  await expect(selected).toHaveAttribute('aria-pressed', 'true')
  await expect(choices.locator('[aria-pressed="true"]')).toHaveCount(1)
}

test('shows distinct tablet and phone interfaces and synchronizes the selected pet across previews', async ({ page }, testInfo) => {
  test.setTimeout(60_000)
  const verifyPublicPage = observePublicPage(page)
  for (const width of widths) {
    await page.setViewportSize({ width, height: width === 1440 ? 1100 : 900 })
    await page.goto('/')
    const hero = page.getByLabel('产品界面示意', { exact: true })
    const tablet = hero.getByLabel('平板应用界面示意', { exact: true })
    const phone = hero.getByLabel('手机应用界面示意', { exact: true })
    for (const device of [tablet, phone]) {
      await expect(device).toBeVisible()
      await expect(device).toContainText('产品界面示意')
      await expect(device).toContainText(/今日|日常/)
      await expect(device).toContainText('照护')
    }
    await expect(tablet).toContainText('Mochi')
    await expect(phone).toContainText('Luna')
    const phoneSize = await phone.evaluate(element => ({ width: (element as HTMLElement).offsetWidth, height: (element as HTMLElement).offsetHeight, client: element.clientHeight, scroll: element.scrollHeight }))
    expect(phoneSize.height / phoneSize.width).toBeGreaterThanOrEqual(2)
    expect(phoneSize.height / phoneSize.width).toBeLessThanOrEqual(2.4)
    expect(phoneSize.scroll).toBeLessThanOrEqual(phoneSize.client + 1)
    if (width < 701) {
      await expect.poll(async () => {
        const [copyBounds, phoneBounds] = await Promise.all([page.locator('.pt-hero-copy').boundingBox(), phone.boundingBox()])
        return !!copyBounds && !!phoneBounds && phoneBounds.y >= copyBounds.y + copyBounds.height
      }).toBe(true)
    }
    await page.screenshot({ path: testInfo.outputPath(`devices-hero-${width}.png`), animations: 'disabled' })

    const gallery = page.getByRole('region', { name: /各自的档案。\s*共同的关心。/ })
    const choices = gallery.getByRole('group', { name: '选择示例宠物', exact: true })
    await gallery.scrollIntoViewIfNeeded()
    await expect(choices.getByRole('button')).toHaveCount(4)
    await expect(choices.getByRole('button', { name: '查看 Mochi 的产品示意', exact: true })).toHaveAttribute('aria-pressed', 'true')
    await gallery.screenshot({ path: testInfo.outputPath(`pet-gallery-${width}.png`), animations: 'disabled' })

    const features = page.locator('#features')
    for (const name of petNames) {
      await selectPet(page, gallery, name)
      await expect(tablet).toContainText(name)
      await expect(phone).toContainText('Luna')
      await expect(features.locator('.pt-story-visual')).toContainText(name)
      await expectNoOverflow(page)
    }
    for (const label of ['宠物小屋', '家庭照护', '成长记录', '宠物分身']) {
      const button = features.getByRole('button', { name: label, exact: true })
      await button.click()
      await expect(button).toHaveAttribute('aria-pressed', 'true')
      await expect(features.locator('.pt-story-visual')).toContainText('Coco')
      const titleFits = await features.locator('.pt-story-copy h3').evaluate(heading => {
        const bounds = heading.getBoundingClientRect()
        return [...heading.querySelectorAll('.pt-title-phrase')].every(phrase => {
          const part = phrase.getBoundingClientRect()
          return part.left >= bounds.left - 1 && part.right <= bounds.right + 1
        })
      })
      expect(titleFits).toBe(true)
      await expectNoOverflow(page)
    }
  }
  verifyPublicPage()
})

test('exposes three distinct case previews with nine readable keyboard steps at supported widths', async ({ page }, testInfo) => {
  test.setTimeout(60_000)
  const verifyPublicPage = observePublicPage(page)
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/#cases')
    const cases = page.getByRole('region', { name: '把功能，放进日常。', exact: true })
    await expect(cases).toBeVisible()
    const art = cases.getByLabel('案例画面', { exact: true })
    for (const scenario of scenarios) {
      const tab = cases.getByRole('button', { name: scenario.label, exact: true })
      await tab.click()
      await expect(tab).toHaveAttribute('aria-pressed', 'true')
      await expect(cases.getByRole('heading', { name: scenario.title, exact: true })).toBeVisible()
      expect(await cases.locator('.pt-case-intro h3').evaluate(heading => {
        const bounds = heading.getBoundingClientRect()
        return [...heading.querySelectorAll('.pt-title-phrase')].every(phrase => phrase.getBoundingClientRect().right <= bounds.right + 1)
      })).toBe(true)
      const preview = art.locator('.pt-case-preview')
      await expect(preview).toHaveAttribute('data-case', scenario.id)
      const steps = cases.getByRole('group', { name: '查看案例步骤', exact: true }).getByRole('button')
      await expect(steps).toHaveCount(3)
      await expect(steps.first()).toHaveAttribute('aria-pressed', 'true')
      const titles: string[] = []
      for (let index = 0; index < 3; index++) {
        await steps.nth(index).focus()
        await page.keyboard.press('Enter')
        await expect(steps.nth(index)).toHaveAttribute('aria-pressed', 'true')
        await expect(cases.getByRole('group', { name: '查看案例步骤', exact: true }).locator('[aria-pressed="true"]')).toHaveCount(1)
        await expect(art).toContainText(`步骤 ${index + 1} / 3`)
        const heading = preview.getByRole('heading').first()
        await expect(heading).toBeVisible()
        await expect(heading).toHaveText(/\S/)
        titles.push((await heading.innerText()).trim())
        await expectNoOverflow(page)
      }
      expect(new Set(titles).size).toBe(3)
      await expect(cases).toContainText('虚构情景演示')
      await cases.screenshot({ path: testInfo.outputPath(`case-${scenario.id}-${width}.png`), animations: 'disabled', style: '.pt-nav, .pt-skip, .pt-motion-toggle { visibility: hidden !important; }' })
    }
  }
  verifyPublicPage()
})

test('retains pet and case keyboard interactions while motion is paused or dynamically reduced', async ({ page }) => {
  const verifyPublicPage = observePublicPage(page)
  await page.setViewportSize({ width: 390, height: 900 })
  await page.goto('/')
  await page.getByRole('button', { name: '暂停动画', exact: true }).click()
  const showcase = page.locator('.showcase')
  const gallery = page.getByRole('region', { name: /各自的档案。\s*共同的关心。/ })
  const cases = page.getByRole('region', { name: '把功能，放进日常。', exact: true })
  for (const [reducedMotion, pet, scenario] of [
    ['no-preference', 'Miso', scenarios[0]],
    ['reduce', 'Luna', scenarios[1]],
  ] as const) {
    await page.emulateMedia({ reducedMotion })
    await expect(showcase).toHaveAttribute('data-motion', 'paused')
    if (reducedMotion === 'reduce') await expect(page.locator('.pt-motion-toggle')).toBeDisabled()
    await selectPet(page, gallery, pet)
    await expect(page.getByLabel('产品界面示意', { exact: true }).getByLabel('平板应用界面示意', { exact: true })).toContainText(pet)
    await cases.getByRole('button', { name: scenario.label, exact: true }).click()
    const lastStep = cases.getByRole('group', { name: '查看案例步骤', exact: true }).getByRole('button').last()
    await lastStep.focus()
    await page.keyboard.press('Enter')
    await expect(lastStep).toHaveAttribute('aria-pressed', 'true')
    await expect(cases.getByLabel('案例画面', { exact: true })).toContainText('步骤 3 / 3')
    await expect(cases.locator('.pt-case-preview')).toHaveAttribute('data-case', scenario.id)
    await expect(showcase).toHaveAttribute('data-motion', 'paused')
    await expect.poll(() => showcase.evaluate(element => element.getAnimations({ subtree: true }).filter(animation => animation.playState === 'running').length)).toBe(0)
    await expectNoOverflow(page)
  }
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await expect(showcase).toHaveAttribute('data-motion', 'paused')
  await expect(page.getByRole('button', { name: '开启动画', exact: true })).toBeEnabled()
  verifyPublicPage()
})
