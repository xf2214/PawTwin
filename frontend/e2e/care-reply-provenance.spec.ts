import { expect, test, type Page } from '@playwright/test'

test.use({ storageState: { cookies: [], origins: [] }, timezoneId: 'Asia/Shanghai' })

const literalTitle = '人工照护（历史名称未记录）'
const fallbackTitle = 'Manual care (historical title not recorded)'

async function createHousehold(page: Page) {
  await page.goto('/#app')
  await page.getByRole('button', { name: 'Create local account', exact: true }).click()
  await page.getByLabel('Username', { exact: true }).fill(`care-title-${Date.now()}-${Math.floor(Math.random() * 999999)}`)
  await page.getByLabel('Password', { exact: true }).fill('care-title-browser-password')
  await page.getByLabel('Display name', { exact: true }).fill('Care title owner')
  await page.getByRole('button', { name: 'Register and sign in', exact: true }).click()
  await page.getByLabel('Household name', { exact: true }).fill('Care title household')
  await page.getByRole('button', { name: 'Create household', exact: true }).click()
  await expect(page.getByRole('navigation', { name: 'App main navigation', exact: true })).toBeVisible()
}

async function mutate(page: Page, path: string, body: object, method = 'POST') {
  const me = await (await page.request.get('/api/family/me')).json()
  const response = await page.request.fetch(path, { method, headers: { 'X-CSRF-Token': me.csrf_token }, data: body })
  expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBe(true)
  return response.json()
}

async function addTask(page: Page) {
  const home = await mutate(page, '/api/home/pets/mochi/tasks', {
    kind: 'water', title: literalTitle, due_at: new Date(Date.now() - 60000).toISOString(),
  })
  return home.tasks.find((task: { title: string }) => task.title === literalTitle)
}

async function askApp(page: Page, text: string) {
  await page.getByRole('textbox', { name: 'What would you like to know?', exact: true }).fill(text)
  const answering = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
  const button = page.getByRole('button', { name: 'Ask the twin', exact: true })
  await button.click()
  const response = await answering
  expect(response.ok()).toBe(true)
  await expect(button).toBeEnabled()
  return page.locator('article[aria-label="Twin reply"] > p')
}

async function askAlexa(page: Page, text: string) {
  const input = page.getByRole('textbox', { name: 'Simulated speech', exact: true })
  await input.fill(text)
  const answering = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
  const button = page.getByRole('button', { name: 'Send to the Alexa simulator', exact: true })
  await button.click()
  expect((await answering).ok()).toBe(true)
  await expect(input).toBeEnabled()
  return page.locator('.alx-reply > p').last()
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('pawtwin-language', 'en'))
})

test('App and Alexa keep literal care titles and the reply snapshot after records change', async ({ page }) => {
  await createHousehold(page)
  let task = await addTask(page)
  await page.goto('/#app/assistant')
  const pending = await askApp(page, 'What tasks are pending?')
  expect.soft(await pending.innerText()).toContain(literalTitle)
  expect.soft(await pending.innerText()).not.toContain(fallbackTitle)

  const edited = await mutate(page, `/api/home/tasks/${task.id}/action`, {
    event_id: crypto.randomUUID(), version: task.version, action: 'edit', title: 'Renamed care task',
  })
  task = edited.tasks.find((item: { id: string }) => item.id === task.id)
  await mutate(page, '/api/home/pets/mochi', { name: 'Renamed pet', species: 'cat' }, 'PUT')
  await page.getByRole('button', { name: 'Refresh records', exact: true }).click()
  await expect(page.locator('.fa-petbar')).toContainText('Renamed pet')
  expect.soft(await pending.innerText()).toContain('Mochi')
  expect.soft(await pending.innerText()).toContain(literalTitle)
  expect.soft(await pending.innerText()).not.toContain('Renamed care task')
  await page.getByRole('article', { name: 'Twin reply', exact: true }).getByText('View supporting records', { exact: true }).click()
  const pendingSources = page.locator('.fa-source-list')
  expect.soft(await pendingSources.innerText()).toContain(literalTitle)
  expect.soft(await pendingSources.innerText()).not.toContain('Renamed care task')
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  expect.soft(await page.locator('.fa-twin-answer article > p').innerText()).toContain(literalTitle)
  expect.soft(await pendingSources.innerText()).toContain(literalTitle)
  await page.getByRole('button', { name: 'English', exact: true }).click()
  expect.soft(await pending.innerText()).toContain(literalTitle)

  const restored = await mutate(page, `/api/home/tasks/${task.id}/action`, {
    event_id: crypto.randomUUID(), version: task.version, action: 'edit', title: literalTitle,
  })
  task = restored.tasks.find((item: { id: string }) => item.id === task.id)
  await page.goto('/#alexa')
  const alexaPending = await askAlexa(page, 'What tasks are pending?')
  expect.soft(await alexaPending.innerText()).toContain(literalTitle)
  expect.soft(await alexaPending.innerText()).not.toContain(fallbackTitle)

  const completedHome = await mutate(page, `/api/home/tasks/${task.id}/action`, {
    event_id: crypto.randomUUID(), version: task.version, action: 'complete',
  })
  const completedAt = completedHome.occurrences.find((item: { task_id: string }) => item.task_id === task.id).completed_at
  const alexaCompleted = await askAlexa(page, 'What was completed?')
  expect.soft(await alexaCompleted.innerText()).toContain(literalTitle)
  expect.soft(await alexaCompleted.innerText()).not.toContain(fallbackTitle)
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  expect.soft(await page.locator('.alx-reply > p').last().innerText()).toContain(literalTitle)
  await page.getByRole('button', { name: 'English', exact: true }).click()
  expect.soft(await alexaCompleted.innerText()).toContain(literalTitle)

  await page.goto('/#app/assistant')
  const completed = await askApp(page, 'What was completed?')
  expect.soft(await completed.innerText()).toContain(literalTitle)
  expect.soft(await completed.innerText()).not.toContain(fallbackTitle)
  await page.getByRole('article', { name: 'Twin reply', exact: true }).getByText('View supporting records', { exact: true }).click()
  const completedSources = page.locator('.fa-source-list')
  expect.soft(await completedSources.innerText()).toContain(literalTitle)
  const recordedTime = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(new Date(completedAt))
  expect.soft(await completedSources.innerText()).toContain(recordedTime)
})

test('read-only completed-care replies distinguish a true fallback from the identical owner title', async ({ page }) => {
  await createHousehold(page)
  const task = await addTask(page)
  const home = await mutate(page, `/api/home/tasks/${task.id}/action`, {
    event_id: crypto.randomUUID(), version: task.version, action: 'complete',
  })
  const occurrence = home.occurrences.find((item: { task_id: string }) => item.task_id === task.id)
  const access = await mutate(page, '/api/family/pets/mochi/care-access', { expires_in_hours: 1 })

  // A browser cannot create missing historical metadata. Keep the real grant and
  // transport, and supply a legacy API projection with explicit title provenance.
  await page.route('**/api/care-access/chat', async route => {
    const response = await route.fetch()
    const reply = await response.json()
    const records = [
      { id: occurrence.id, title: literalTitle, title_is_fallback: false, completed_at: occurrence.completed_at },
      { id: 'legacy-missing-title', title: literalTitle, title_is_fallback: true, completed_at: occurrence.completed_at },
    ]
    await route.fulfill({ response, json: {
      ...reply,
      answer: '近七天实际人工完成记录：' + records.map(record => `${record.title}（${record.completed_at}）`).join('；'),
      source_record_ids: records.map(record => record.id),
      care_summary: { kind: 'completed', pet_name: null, total_count: records.length, records },
    } })
  })
  await page.goto(`/#pet-access=${encodeURIComponent(access.token)}`)
  await page.getByRole('textbox', { name: 'What would you like to know?', exact: true }).fill('做过哪些照护')
  await page.getByRole('button', { name: 'Ask the read-only twin', exact: true }).click()
  const reply = page.locator('.ca-chat [role="log"] article > p').last()
  await expect(reply).toBeVisible()
  const english = await reply.innerText()
  expect.soft(english).toContain(fallbackTitle)
  expect.soft(english.split(literalTitle).length - 1).toBe(1)
  expect.soft(english).toContain(occurrence.completed_at)
  expect.soft(english.replace(literalTitle, '')).not.toMatch(/\p{Script=Han}/u)
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  const chinese = await reply.innerText()
  expect.soft(chinese.split(literalTitle).length - 1).toBe(2)
  await page.getByRole('button', { name: 'English', exact: true }).click()
  expect.soft(await reply.innerText()).toBe(english)
})
