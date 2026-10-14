import { expect, test } from '@playwright/test'

const headline = /宠物的每一天，\s*全家一起照顾。/

test('explores illustrative care cases without writing business data', async ({ page }) => {
  const requests: string[] = []
  page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/#cases')
    const cases = page.getByRole('region', { name: '把功能，放进日常。' })
    await expect(cases).toBeVisible({ timeout: 5000 })
    await expect(cases.getByText('虚构情景演示 · 不会创建真实照护任务')).toBeVisible()
    for (const [label, title] of [['家庭交接', '你出门了，照顾还在继续。'], ['成长回顾', '一次次记录，看见成长的轨迹。'], ['偏好接续', '下一次交流，从已有了解开始。']]) {
      await cases.getByRole('button', { name: label, exact: true }).click()
      await expect(cases.getByRole('heading', { name: title })).toBeVisible()
      const steps = cases.getByRole('group', { name: '查看案例步骤' }).getByRole('button')
      await expect(steps.nth(0)).toHaveAttribute('aria-pressed', 'true')
      await steps.nth(2).focus()
      await page.keyboard.press('Enter')
      await expect(steps.nth(2)).toHaveAttribute('aria-pressed', 'true')
      await expect(cases.getByLabel('案例画面')).toContainText('步骤 3 / 3')
      await steps.nth(0).click()
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    }
  }
  expect(requests).toEqual([])
})

test('can pause motion while retaining case interactions and reduced-motion readability', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '暂停动画', exact: true }).click({ timeout: 5000 })
  await expect(page.locator('.showcase')).toHaveAttribute('data-motion', 'paused')
  await page.locator('.pt-world-cat').scrollIntoViewIfNeeded()
  expect(await page.locator('.pt-world-cat').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  await page.getByRole('navigation', { name: '产品导航', exact: true }).getByRole('link', { name: '日常案例', exact: true }).click()
  await page.getByRole('button', { name: '成长回顾', exact: true }).click()
  await expect(page.getByRole('heading', { name: '一次次记录，看见成长的轨迹。' })).toBeVisible()
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.reload()
  await expect(page.getByRole('heading', { name: '把功能，放进日常。' })).toBeVisible()
  expect(await page.locator('.pt-world-cat').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  await expect(page.getByRole('button', { name: '已遵循系统减少动画', exact: true })).toBeDisabled()
})

test('introduces the product without requesting private business data, then opens the app', async ({ page }) => {
  const businessRequests: string[] = []
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/api/')) businessRequests.push(request.url())
  })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: headline })).toBeVisible({ timeout: 5000 })
  await expect(page.getByLabel('产品界面示意')).toBeVisible()
  await expect(page.getByLabel('演示口令')).toHaveCount(0)
  expect(businessRequests).toEqual([])
  await page.screenshot({ path: 'test-results/showcase-desktop.png', fullPage: true, animations: 'disabled' })

  await page.getByRole('link', { name: '了解产品' }).click()
  await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
  await page.getByRole('button', { name: '成长记录' }).click()
  await expect(page.getByRole('heading', { name: '把成长，留在时间里。' })).toBeVisible()
  expect(businessRequests).toEqual([])

  await page.getByRole('link', { name: '进入应用', exact: true }).first().click()
  await expect(page).toHaveURL(/#app$/)
  await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  await expect(page).toHaveURL(/#product$/)
  await expect(page.getByRole('heading', { name: headline })).toBeVisible()
})

test('keeps the showcase readable on mobile and the original workbench reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: headline })).toBeVisible({ timeout: 5000 })
  const fits = () => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
  expect(await fits()).toBe(true)
  await page.screenshot({ path: 'test-results/showcase-mobile.png', fullPage: true, animations: 'disabled' })
  await page.getByRole('link', { name: '照护工作台', exact: true }).click()
  await expect(page.getByLabel('演示口令')).toBeVisible()
  expect(await fits()).toBe(true)
  await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  await expect(page.getByRole('heading', { name: headline })).toBeVisible()
})

test('supports direct product anchors and distinct preview panels at narrow widths', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/#features')
    await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
    for (const label of ['家庭照护', '成长记录', '宠物分身']) {
      await page.getByRole('button', { name: label, exact: true }).click()
      await expect(page.getByLabel(`${label}界面示意`, { exact: true })).toBeVisible()
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    }
  }
  await page.goto('/#care')
  await expect(page.getByRole('heading', { name: '让关心，变成有回应的日常。' })).toBeInViewport()
  expect(errors).toEqual([])
})

test('supports keyboard exploration, reduced motion and the growth shortcut', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: '跳到产品内容' })).toBeFocused()
  await page.keyboard.press('Enter')
  expect(await page.locator('.pt-hero-copy').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  await page.locator('.pt-memory').getByRole('link', { name: '探索成长记录' }).click()
  await expect(page.getByRole('button', { name: '成长记录', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
  const twin = page.getByRole('button', { name: '宠物分身', exact: true })
  const announcer = await page.locator('.pt-story-copy').elementHandle()
  await twin.focus()
  await page.keyboard.press('Enter')
  await expect(twin).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByLabel('宠物分身界面示意')).toContainText('实际回答后端见应用内每轮回复')
  await expect(page.locator('.pt-story-copy')).toHaveAttribute('aria-live', 'polite')
  expect(await announcer!.evaluate(element => element.isConnected)).toBe(true)
})

test('routes each product experience to its application feature with the keyboard', async ({ page }) => {
  for (const [label, route] of [
    ['宠物小屋', '#app/home'],
    ['家庭照护', '#app/care'],
    ['成长记录', '#app/growth'],
    ['宠物分身', '#app/assistant'],
  ]) {
    await page.goto('/#features')
    await page.getByRole('button', { name: label, exact: true }).click()
    await page.getByRole('link', { name: '在应用中体验', exact: true }).focus()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL(new RegExp(`${route}$`), { timeout: 3000 })
    await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
    await page.getByRole('link', { name: '产品介绍', exact: true }).click()
    await expect(page.getByRole('heading', { name: headline })).toBeVisible()
  }
})

test('opens the relevant application feature from each illustrative case', async ({ page }) => {
  for (const [label, route] of [
    ['家庭交接', '#app/care'],
    ['成长回顾', '#app/growth'],
    ['偏好接续', '#app/assistant'],
  ]) {
    await page.goto('/#cases')
    const cases = page.getByRole('region', { name: '把功能，放进日常。' })
    await cases.getByRole('button', { name: label, exact: true }).click()
    await cases.getByRole('link', { name: '在应用中开始', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`${route}$`), { timeout: 3000 })
    await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  }
})

test('makes the Alexa web simulation discoverable on mobile before opening it by keyboard', async ({ page }) => {
  const requests: string[] = []
  page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  await page.setViewportSize({ width: 320, height: 844 })
  await page.goto('/')
  const shortcut = page.getByRole('link', { name: '体验 Alexa+ 网页模拟', exact: true })
  await expect(shortcut).toBeVisible({ timeout: 3000 })
  await shortcut.focus()
  expect(requests).toEqual([])
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/#alexa$/)
  await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
})

test('explores handoff and visit demonstrations without business requests at all supported widths', async ({ page }, testInfo) => {
  const requests: string[] = [], errors: string[] = []
  page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  page.on('pageerror', error => errors.push(error.message))
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/#vision')
    const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
    await expect(vision).toBeVisible({ timeout: 3000 })
    const announcer = await vision.locator('.pt-vision-live').elementHandle()
    for (const [label, titles] of [
      ['照护交接', ['选择宠物与资料', '临时只读分身卡', '照护者只读查看', '到期或撤销']],
      ['就诊准备', ['已有记录概览', '缺项与来源', '就诊信息卡（诊断资料）']],
    ] as const) {
      await vision.getByRole('button', { name: label, exact: true }).click()
      const steps = vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button')
      await expect(steps.nth(0)).toHaveAttribute('aria-pressed', 'true')
      for (let index = 0; index < titles.length; index++) {
        await steps.nth(index).focus()
        await page.keyboard.press('Enter')
        await expect(steps.nth(index)).toHaveAttribute('aria-pressed', 'true')
        await expect(vision.getByRole('heading', { name: titles[index], exact: true })).toBeVisible()
        await expect(vision.getByLabel('交接与就诊功能界面示意')).toContainText(`步骤 ${index + 1} / ${titles.length}`)
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
        if ((label === '照护交接' && index === 1) || (label === '就诊准备' && index === 2)) {
          await vision.screenshot({ path: testInfo.outputPath(`vision-${width}-${label}.png`), animations: 'disabled' })
        }
      }
      expect(await announcer!.evaluate(element => element.isConnected)).toBe(true)
    }
    await vision.getByRole('button', { name: '照护交接', exact: true }).click()
    await expect(vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button').first()).toHaveAttribute('aria-pressed', 'true')
  }
  expect(requests).toEqual([])
  expect(errors).toEqual([])
})

test('routes real access management and visit-card export from their demonstration', async ({ page }) => {
  for (const [scenario, shortcut, route] of [
    ['照护交接', '在应用中管理临时访问', '#app/family'],
    ['就诊准备', '导出就诊信息卡（诊断资料）', '#app/growth'],
  ]) {
    await page.goto('/#vision')
    const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
    await expect(vision).toBeVisible({ timeout: 3000 })
    await vision.getByRole('button', { name: scenario, exact: true }).click()
    await vision.getByRole('link', { name: shortcut, exact: true }).focus()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL(new RegExp(`${route}$`))
    await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  }
})

test('keeps new demonstration steps usable while motion is paused or reduced', async ({ page }) => {
  await page.goto('/#vision')
  const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
  await expect(vision).toBeVisible({ timeout: 3000 })
  await page.getByRole('button', { name: '暂停动画', exact: true }).click()
  await vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button', { name: /^02\s+授权分身卡$/ }).click()
  await expect(vision.getByRole('heading', { name: '临时只读分身卡', exact: true })).toBeVisible()
  expect(await vision.locator('.pt-vision-card').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await vision.getByRole('button', { name: '就诊准备', exact: true }).click()
  await vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button', { name: /^03\s+预览就诊卡$/ }).click()
  await expect(vision.getByRole('heading', { name: '就诊信息卡（诊断资料）', exact: true })).toBeVisible()
  expect(await vision.locator('.pt-vision-card').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  await expect(page.getByRole('button', { name: '已遵循系统减少动画', exact: true })).toBeDisabled()
})
