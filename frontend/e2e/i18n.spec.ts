import { expect, test } from '@playwright/test'

test.use({ storageState: { cookies: [], origins: [] } })

test('starts in English and keeps the chosen language across routes and reloads', async ({ page }) => {
  const business: string[] = []
  page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) business.push(request.url()) })
  await page.goto('/')
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expect(page.getByRole('link', { name: /^Open (?:the )?app$/ }).first()).toBeVisible()
  expect(business).toEqual([])
  await page.getByRole('button', { name: '中文', exact: true }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')
  await expect(page.getByRole('link', { name: '进入应用', exact: true }).first()).toBeVisible()
  await page.getByRole('link', { name: '进入应用', exact: true }).first().click()
  await expect(page.getByRole('button', { name: '创建本地账号', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Create local account', exact: true })).toBeVisible()
  await page.goto('/#workbench')
  await expect(page.getByLabel('Demo passphrase')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in to demo', exact: true })).toBeVisible()
  await expect(page).toHaveTitle(/Care workbench/)
})

test('English workbench remains usable and switching language preserves entered data', async ({ page }) => {
  await page.goto('/#workbench')
  await page.getByLabel('Demo passphrase').fill('local-demo-passphrase')
  await page.getByRole('button', { name: 'Sign in to demo', exact: true }).click()
  await expect(page.getByTestId('facts')).toBeVisible()
  await expect(page.getByTestId('facts')).toContainText('minutes')
  await page.getByRole('button', { name: '中文', exact: true }).click()
  await expect(page.getByTestId('facts')).toContainText('分钟')
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await expect(page.getByTestId('facts')).toContainText('minutes')
  await page.goto('/#app')
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await page.getByRole('button', { name: 'Create local account', exact: true }).click()
  await page.getByLabel('Display name', { exact: true }).fill('中文宠物主人')
  await page.getByRole('button', { name: '中文', exact: true }).click()
  await expect(page.getByLabel('昵称', { exact: true })).toHaveValue('中文宠物主人')
})

test('English family forms preserve original records and translate local assistant output', async ({ page }) => {
  await page.goto('/#app')
  await page.getByRole('button', { name: 'Create local account', exact: true }).click()
  await page.getByLabel('Username', { exact: true }).fill(`english-${Date.now()}`)
  await page.getByLabel('Password', { exact: true }).fill('english-test-password')
  await page.getByLabel('Display name', { exact: true }).fill('中文宠物主人')
  await page.getByRole('button', { name: 'Register and sign in', exact: true }).click()
  await page.getByLabel('Household name', { exact: true }).fill('我的中文家庭')
  await page.getByRole('button', { name: 'Create household', exact: true }).click()
  await expect(page.getByRole('heading', { name: '我的中文家庭', exact: true })).toBeVisible()
  await page.getByRole('button', { name: '中文', exact: true }).click()
  await expect(page.getByRole('heading', { name: '我的中文家庭', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await page.goto('/#app/assistant')
  await page.getByRole('button', { name: /What.*like/ }).click()
  await expect(page.locator('article').filter({ hasText: 'records:' }).first()).toContainText('No confirmed preference memories')
  await page.getByRole('textbox', { name: 'What would you like to know?', exact: true }).fill('plan playtime')
  await page.getByRole('button', { name: 'Ask the twin', exact: true }).click()
  await expect(page.getByRole('article', { name: 'Twin reply', exact: true })).toContainText('manual care draft', { timeout: 4000 })
  // A record can contain exactly the same words as a UI label or a generated
  // template. Those owner-authored words must remain verbatim in the export.
  await page.evaluate(async () => {
    const me = await (await fetch('/api/family/me')).json()
    const headers = { 'Content-Type': 'application/json', 'X-CSRF-Token': me.csrf_token }
    const response = await fetch('/api/home/pets/mochi/tasks', { method: 'POST', headers, body: JSON.stringify({ kind: 'water', title: '为 Mochi 换水', due_at: new Date().toISOString() }) })
    if (!response.ok) throw new Error(await response.text())
    const home = await response.json()
    const task = home.tasks.find((item: { title: string }) => item.title === '为 Mochi 换水')
    const complete = await fetch(`/api/home/tasks/${task.id}/action`, { method: 'POST', headers, body: JSON.stringify({ event_id: crypto.randomUUID(), version: task.version, action: 'complete' }) })
    if (!complete.ok) throw new Error(await complete.text())
  })
  await page.goto('/#app/growth')
  await page.getByRole('button', { name: 'Export a vet visit card (clinical background)', exact: true }).click()
  await page.getByRole('button', { name: 'Generate card', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Vet visit card snapshot', exact: true })).toContainText('为 Mochi 换水')
  await page.getByRole('button', { name: 'Close card', exact: true }).click()
})

test('language control stays reachable without horizontal overflow on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 })
  for (const route of ['/', '/#app', '/#workbench', '/#pet-access=invalid']) {
    await page.goto(route)
    await expect(page.getByRole('button', { name: '中文', exact: true })).toBeVisible()
    for (const name of ['English', '中文']) {
      const bounds = await page.getByRole('button', { name, exact: true }).boundingBox()
      expect(bounds && bounds.x >= 0 && bounds.x + bounds.width <= 320).toBe(true)
    }
    if (route === '/') {
      const menu = page.getByRole('button', { name: 'Open product navigation', exact: true })
      const bounds = await menu.boundingBox()
      expect(bounds && bounds.x >= 0 && bounds.x + bounds.width <= 320).toBe(true)
      await menu.click()
      await expect(page.getByRole('navigation', { name: 'Mobile product navigation', exact: true })).toBeVisible()
    }
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
})
