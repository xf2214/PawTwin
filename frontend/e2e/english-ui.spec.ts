import { expect, test, type Page } from '@playwright/test'
import { PASSPHRASE } from './helpers'

test.use({ storageState: { cookies: [], origins: [] }, timezoneId: 'Asia/Shanghai' })

type OriginalText = { selector: string; text: string; attribute?: string }

// Remove only a known owner-authored value at its owning node. The surrounding
// text and attributes are still checked, including system text in the same card.
async function expectEnglishUi(page: Page, state: string, originals: OriginalText[] = []) {
  const leaks = await page.evaluate((originals) => {
    const han = /\p{Script=Han}/u
    const findings = new Set<string>()
    const visible = (element: Element) => {
      const optionParent = element.tagName === 'OPTION' ? element.closest('select') : null
      const target = optionParent ?? element
      const style = getComputedStyle(target)
      return target.getClientRects().length > 0 && style.visibility !== 'hidden' && style.display !== 'none'
    }
    const inspect = (element: Element, text: string, attribute = 'text') => {
      let systemText = text
      for (const original of originals) {
        if (element.matches(original.selector) && (original.attribute ?? 'text') === attribute) {
          systemText = systemText.split(original.text).join('')
        }
      }
      if (han.test(systemText)) {
        const location = `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ''}${element.classList.length ? `.${[...element.classList].join('.')}` : ''}`
        findings.add(`${location} [${attribute}]: ${systemText.trim().slice(0, 240)}`)
      }
    }
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
    while (walker.nextNode()) {
      const node = walker.currentNode
      const parent = node.parentElement
      if (parent && !parent.closest('script, style, noscript') && visible(parent)) inspect(parent, node.textContent ?? '')
    }
    for (const element of document.body.querySelectorAll('*')) {
      if (visible(element)) {
        for (const name of ['aria-label', 'title', 'placeholder', 'alt']) {
          if (element.hasAttribute(name)) inspect(element, element.getAttribute(name) ?? '', name)
        }
        if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) inspect(element, element.value, 'value')
      }
    }
    // Native option menus are not laid out as regular DOM nodes. Their offered
    // labels and datalist insertion values are part of the visible form too.
    for (const option of document.querySelectorAll('option')) {
      const select = option.closest('select')
      const list = option.closest('datalist')
      const input = list?.id ? document.querySelector(`input[list="${CSS.escape(list.id)}"]`) : null
      if ((select && visible(select)) || (input && visible(input))) {
        inspect(option, option.textContent ?? '')
        inspect(option, option.label, 'label')
        if (list) inspect(option, option.value, 'value')
      }
    }
    if (han.test(document.title)) findings.add(`document title: ${document.title}`)
    return [...findings]
  }, originals)
  expect.soft(leaks, `${state}: English system UI must contain no Han characters`).toEqual([])
}

async function mutate(page: Page, path: string, body: object, method = 'POST') {
  const me = await (await page.request.get('/api/family/me')).json()
  const response = await page.request.fetch(path, { method, headers: { 'X-CSRF-Token': me.csrf_token }, data: body })
  expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBe(true)
  return response.json()
}

async function openApp(page: Page, route = 'home') {
  await page.goto(`/#app/${route}`)
  await expect(page.getByRole('navigation', { name: 'App main navigation', exact: true })).toBeVisible()
}

async function createEnglishHousehold(page: Page) {
  await page.goto('/#app')
  await page.getByRole('button', { name: 'Create local account', exact: true }).click()
  await page.getByLabel('Username', { exact: true }).fill(`english-ui-${Date.now()}-${Math.floor(Math.random() * 999999)}`)
  await page.getByLabel('Password', { exact: true }).fill('english-browser-test-password')
  await page.getByLabel('Display name', { exact: true }).fill('English test owner')
  await page.getByRole('button', { name: 'Register and sign in', exact: true }).click()
  await page.getByLabel('Household name', { exact: true }).fill('English test household')
  await page.getByRole('button', { name: 'Create household', exact: true }).click()
  await expect(page.getByRole('navigation', { name: 'App main navigation', exact: true })).toBeVisible()
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('pawtwin-language', 'en'))
})

test('English demo routes and profile/item forms do not expose Chinese seed or system text', async ({ page }) => {
  await page.goto('/#app')
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await expectEnglishUi(page, 'signed-out household login')
  await page.goto('/#workbench')
  await expectEnglishUi(page, 'demo login')
  await page.getByLabel('Demo passphrase', { exact: true }).fill(PASSPHRASE)
  await page.getByRole('button', { name: 'Sign in to demo', exact: true }).click()
  await expect(page.getByTestId('facts')).toBeVisible()
  await mutate(page, '/api/home/pets/mochi/notes', { text: 'English demo owner observation', scope: 'observation', activity: 'general' })
  await mutate(page, '/api/home/pets/mochi/diary', { title: 'English demo owner diary', text: 'A quiet afternoon recorded by the demo owner', happened_on: new Date().toISOString().slice(0, 10) })
  await mutate(page, '/api/family/pets/mochi/memories', { text: 'English demo candidate preference', topic: 'play', status: 'candidate' })

  for (const route of ['home', 'care', 'growth', 'assistant', 'family']) {
    await openApp(page, route)
    if (route === 'assistant') await expect(page.locator('.fa-twin-memory .fa-record').filter({ hasText: 'English demo candidate preference' }).first()).toBeVisible()
    await expectEnglishUi(page, `demo ${route}`)
    if (route === 'growth') {
      await page.getByRole('navigation', { name: 'Growth sections', exact: true }).getByRole('button', { name: 'Diary & observations', exact: true }).click()
      await expect(page.locator('.ph-diary > h3').filter({ hasText: 'English demo owner diary' }).first()).toBeVisible()
      await expectEnglishUi(page, 'demo observations, diary and record-management author labels')
    }
  }
  const labels = page.locator('#family-labels option')
  const suggestions = await labels.evaluateAll(options => options.map(option => (option as HTMLOptionElement).value))
  expect.soft(suggestions.filter(value => /\p{Script=Han}/u.test(value)), 'English family-label suggestions must insert English values').toEqual([])
  await page.getByText('Household settings', { exact: true }).click()
  await expectEnglishUi(page, 'expanded household settings and label suggestions')

  await openApp(page)
  await page.getByRole('button', { name: 'Edit profile', exact: true }).first().click()
  await expect(page.getByLabel('Name *', { exact: true })).toBeVisible()
  await page.getByText('Pixel avatar & preferences', { exact: true }).click()
  await expectEnglishUi(page, 'pet profile, avatar options and preferences')
  await page.getByRole('button', { name: 'Cancel', exact: true }).click()
  await page.getByRole('button', { name: 'Arrange home', exact: true }).click()
  await expectEnglishUi(page, 'room item creation')
  const items = page.locator('.ph-item-list > button')
  for (let index = 0; index < await items.count(); index++) {
    await items.nth(index).click()
    await expectEnglishUi(page, `seed item editor ${index + 1}`)
  }
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.getByRole('button', { name: 'Back to pet home', exact: true }).click()
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    if (width !== 320) await page.screenshot({ path: `test-results/english-ui-home-${width}.png`, fullPage: true })
    await page.getByRole('button', { name: 'Arrange home', exact: true }).click()
    await items.last().click()
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
  await page.getByRole('button', { name: 'Add another', exact: true }).click()
  const editor = page.locator('.ph-item-editor')
  const beforeCreation = await (await page.request.get('/api/home/state')).json()
  const previousIds = beforeCreation.objects.map((item: { id: string }) => item.id)
  const additions = [
    { name: 'English reading cushion', note: 'Keep beside the window' },
    { name: 'English travel bowl', note: 'Wash after each outing' },
  ]
  for (const addition of additions) {
    await editor.getByRole('textbox', { name: 'Name', exact: true }).fill(addition.name)
    await editor.getByRole('textbox', { name: 'Usage / cleaning notes', exact: true }).fill(addition.note)
    await editor.getByRole('button', { name: 'Add to home', exact: true }).click()
    await expect(items.filter({ hasText: addition.name })).toBeVisible()
    await expect(editor.getByRole('textbox', { name: 'Name', exact: true })).toHaveValue('')
    await expect(editor.getByRole('textbox', { name: 'Usage / cleaning notes', exact: true })).toHaveValue('')
  }
  const afterCreation = await (await page.request.get('/api/home/state')).json()
  const created = afterCreation.objects.filter((item: { id: string }) => !previousIds.includes(item.id))
  expect(created.map((item: { name: string; note: string }) => ({ name: item.name, note: item.note }))).toEqual(additions)
  expect(new Set(created.map((item: { id: string }) => item.id)).size).toBe(2)
  await expectEnglishUi(page, 'two consecutive item creations reset their English form fields')
})

test('English care, growth, diary and report forms translate their populated branches', async ({ page }) => {
  await createEnglishHousehold(page)
  const home = await mutate(page, '/api/home/pets/mochi/tasks', { kind: 'water', title: 'Morning water change', due_at: new Date(Date.now() - 3600000).toISOString(), interval_days: 2 })
  expect(home.tasks.some((task: { title: string }) => task.title === 'Morning water change')).toBe(true)
  const measuredAt = new Date(Date.now() - 3600000).toISOString()
  for (const record of [
    { kind: 'weight', value: 4.12, unit: 'kg', note: 'Digital scale reading' },
    { kind: 'diet', value: 21, unit: 'g', diet_type: 'actual_intake', note: 'Owner observed eaten dry food' },
  ]) await mutate(page, '/api/family/pets/mochi/measurements', { ...record, measured_at: measuredAt, source: 'owner_measured' })

  await openApp(page, 'care')
  const task = page.locator('.fa-task-card').filter({ has: page.getByRole('heading', { name: 'Morning water change', exact: true }) })
  await expect(task).toBeVisible()
  await task.getByText('Edit or postpone', { exact: true }).click()
  await task.getByText('Transfer to a household member', { exact: true }).click()
  await page.getByText('＋ Plan everyday care', { exact: true }).click()
  await expectEnglishUi(page, 'populated care, edit, transfer and creation forms')

  await openApp(page, 'growth')
  const sections = page.getByRole('navigation', { name: 'Growth sections', exact: true })
  await expectEnglishUi(page, 'growth overview and weight curve')
  await sections.getByRole('button', { name: 'Measurements and diet', exact: true }).click()
  await page.getByRole('combobox', { name: 'Record type', exact: true }).selectOption('diet')
  await expectEnglishUi(page, 'diet meaning, sources and saved measurements')
  await page.getByRole('button', { name: 'Correct record', exact: true }).first().click()
  await expectEnglishUi(page, 'measurement correction')
  await sections.getByRole('button', { name: 'Diary & observations', exact: true }).click()
  await expectEnglishUi(page, 'diary and observation forms')
  await sections.getByRole('button', { name: 'Reports', exact: true }).click()
  await page.getByRole('button', { name: 'Generate daily report', exact: true }).click()
  const report = page.getByRole('region', { name: 'Daily and weekly reports', exact: true })
  await expect(report.locator('.fa-report-card')).not.toHaveCount(0)
  await report.getByText('Source records and version', { exact: true }).first().click()
  await expectEnglishUi(page, 'generated report metrics and source records')
})

test('English assistant and Alexa-generated care remain English in tasks and offline vet exports', async ({ page, browser }) => {
  await createEnglishHousehold(page)
  await mutate(page, '/api/home/pets/mochi/notes', { text: 'Likes blue soft balls', scope: 'preference', activity: 'play' })
  await mutate(page, '/api/family/pets/mochi/measurements', { kind: 'diet', value: 18, unit: 'g', diet_type: 'actual_intake', measured_at: new Date(Date.now() - 3600000).toISOString(), source: 'owner_measured', note: 'Observed eating dry food' })
  await openApp(page, 'assistant')
  await page.locator('.fa-context-overview > summary').click()
  for (const name of ['What does my pet like?', 'Recent diet records', 'What is the latest weight?', 'What tasks are pending?']) {
    const button = page.locator('.fa-context-questions').getByRole('button', { name, exact: true })
    const answering = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
    await button.click()
    expect((await answering).ok()).toBe(true)
    await expect(button).toBeEnabled()
    const reply = page.getByRole('article', { name: 'Twin reply', exact: true })
    await expect(reply).toBeVisible()
    if (!await reply.locator('details').evaluate(element => element.hasAttribute('open'))) await reply.locator('summary').click()
    await expectEnglishUi(page, `assistant answer and sources: ${name}`)
  }

  for (const question of ['breed', 'What was observed today?']) {
    await page.getByRole('textbox', { name: 'What would you like to know?', exact: true }).fill(question)
    const answering = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Ask the twin', exact: true }).click()
    expect((await answering).ok()).toBe(true)
    await expect(page.getByRole('button', { name: 'Ask the twin', exact: true })).toBeEnabled()
    await expectEnglishUi(page, `assistant missing-data branch: ${question}`)
  }
  await mutate(page, '/api/home/pets/mochi/notes', { text: 'Resting after meals', scope: 'today', activity: 'play' })
  await openApp(page)
  await page.getByRole('combobox', { name: 'Care activity', exact: true }).selectOption('play')
  await expect(page.locator('.ph-side')).toContainText('Resting after meals')
  await expectEnglishUi(page, 'home suggestion with a relevant observation today')

  await page.goto('/#alexa')
  await page.getByRole('button', { name: 'Plan some playtime', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Care draft awaiting confirmation', exact: true })).toBeVisible()
  await expectEnglishUi(page, 'Alexa generated draft')
  await page.getByRole('button', { name: 'Prepare a proposal', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Care proposal awaiting confirmation', exact: true })).toBeVisible()
  await expectEnglishUi(page, 'Alexa pending proposal')
  await page.getByRole('button', { name: 'Confirm manual care plan', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Care result', exact: true })).toBeVisible()
  await expectEnglishUi(page, 'Alexa confirmed care result')
  await openApp(page, 'care')
  const generated = page.locator('.fa-task-card').filter({ has: page.getByRole('heading', { name: 'Play with Mochi', exact: true }) })
  await expect(generated).toBeVisible()
  await expectEnglishUi(page, 'persisted generated care title')
  await generated.getByRole('button', { name: 'Complete care', exact: true }).click()
  await openApp(page, 'growth')
  await page.getByRole('button', { name: 'Export a vet visit card (clinical background)', exact: true }).click()
  await page.getByRole('button', { name: 'Generate card', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Vet visit card snapshot', exact: true })).toContainText('Play with Mochi')
  await expectEnglishUi(page, 'vet card preview')
  const downloading = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download standalone HTML', exact: true }).click()
  const download = await downloading
  expect(download.suggestedFilename()).not.toMatch(/\p{Script=Han}/u)
  const stream = await download.createReadStream()
  if (!stream) throw new Error('Downloaded HTML stream is unavailable')
  const decoder = new TextDecoder()
  let html = ''
  for await (const chunk of stream) html += decoder.decode(chunk as Uint8Array, { stream: true })
  html += decoder.decode()
  const offline = await browser.newPage()
  try {
    await offline.setContent(html)
    await expect(offline.locator('html')).toHaveAttribute('lang', 'en-US')
    await expect(offline.locator('.vc-document')).toContainText('Play with Mochi')
    await expectEnglishUi(offline, 'downloaded offline vet card')
  } finally { await offline.close() }
})

test('English UI preserves literal Chinese owner names, observations, customized items and manual care titles', async ({ page }) => {
  await createEnglishHousehold(page)
  const title = '为 Mochi 换水'
  const observation = '只喜欢蓝色软球'
  const diaryTitle = '中文日记标题'
  const owner = '中文宠物主人'
  const itemName = '窗边小窝'
  const itemNote = '主人手写的窗边清洁说明'
  const toyName = '球、绳组合'
  const breed = '未填写'
  await page.getByRole('button', { name: 'Arrange home', exact: true }).click()
  await page.locator('.ph-item-list > button').first().click()
  const itemEditor = page.locator('.ph-item-editor')
  await itemEditor.getByRole('textbox', { name: 'Name', exact: true }).fill(itemName)
  await itemEditor.getByRole('textbox', { name: 'Usage / cleaning notes', exact: true }).fill(itemNote)
  await itemEditor.getByRole('button', { name: 'Save item & position', exact: true }).click()
  const item = page.locator('.ph-item-list > button').filter({ hasText: itemName })
  await expect(item).toBeVisible()
  await item.click()
  await expect(itemEditor.getByRole('textbox', { name: 'Name', exact: true })).toHaveValue(itemName)
  await expect(itemEditor.getByRole('textbox', { name: 'Usage / cleaning notes', exact: true })).toHaveValue(itemNote)
  await expectEnglishUi(page, 'a starter label with an owner-written note is preserved as user content', [
    { selector: '.ph-room .ph-object-name', text: itemName },
    { selector: '.ph-room button.ph-object', attribute: 'aria-label', text: itemName },
    { selector: '.ph-item-list > button', text: itemName },
    { selector: '.ph-item-editor > h3', text: itemName },
    { selector: '.ph-item-editor input[name="name"]', attribute: 'value', text: itemName },
    { selector: '.ph-item-editor input[name="note"]', attribute: 'value', text: itemNote },
  ])
  await openApp(page, 'care')
  await page.getByText('＋ Plan everyday care', { exact: true }).click()
  await page.getByLabel('Care task name', { exact: true }).fill(title)
  await page.getByRole('button', { name: 'Save care plan', exact: true }).click()
  const task = page.locator('.fa-task-card').filter({ has: page.getByRole('heading', { name: title, exact: true }) })
  await expect(task.getByRole('heading', { name: title, exact: true })).toBeVisible()
  await task.getByText('Edit or postpone', { exact: true }).click()
  await expect(task.getByLabel('Task title', { exact: true })).toHaveValue(title)
  await expectEnglishUi(page, 'manual title remains verbatim', [
    { selector: '.fa-task-card h3', text: title },
    { selector: '.fa-task-card input[name="title"]', attribute: 'value', text: title },
  ])
  await task.getByRole('button', { name: 'Complete care', exact: true }).click()

  await openApp(page, 'growth')
  await page.getByRole('navigation', { name: 'Growth sections', exact: true }).getByRole('button', { name: 'Diary & observations', exact: true }).click()
  await page.getByLabel('Original observation', { exact: true }).fill(observation)
  await page.getByRole('combobox', { name: 'Applies to', exact: true }).selectOption('observation')
  await page.getByRole('button', { name: 'Save owner record', exact: true }).click()
  await page.getByLabel('Title', { exact: true }).fill(diaryTitle)
  await page.getByLabel('Content', { exact: true }).fill('Owner-written diary content')
  await page.getByRole('button', { name: 'Save diary entry', exact: true }).click()
  const management = page.getByRole('region', { name: 'Manage observations and diary', exact: true })
  await expect(management.locator('strong').filter({ hasText: observation })).toHaveText(observation)
  await expect(management.locator('strong').filter({ hasText: diaryTitle })).toHaveText(diaryTitle)
  const recordOriginals: OriginalText[] = [
    { selector: '.ph-observation-list blockquote', text: observation },
    { selector: '.fa-record > strong', text: observation },
    { selector: '.fa-record > strong', text: diaryTitle },
    { selector: '.ph-diary > h3', text: diaryTitle },
    { selector: 'section[aria-label="Manage observations and diary"] textarea[name="text"]', text: observation },
    { selector: 'section[aria-label="Manage observations and diary"] textarea[name="text"]', attribute: 'value', text: observation },
    { selector: 'section[aria-label="Manage observations and diary"] input[name="title"]', attribute: 'value', text: diaryTitle },
  ]
  await expectEnglishUi(page, 'saved owner observation and diary title', recordOriginals)
  await page.getByRole('button', { name: 'Export a vet visit card (clinical background)', exact: true }).click()
  await page.getByRole('button', { name: 'Generate card', exact: true }).click()
  const card = page.getByRole('region', { name: 'Vet visit card snapshot', exact: true })
  for (const original of [title, observation, diaryTitle]) await expect(card).toContainText(original)
  await expectEnglishUi(page, 'vet card keeps original Chinese records', [
    ...recordOriginals,
    { selector: '.vc-document td', text: title },
    { selector: '.vc-document td', text: observation },
    { selector: '.vc-document td', text: diaryTitle },
  ])
  await page.getByRole('button', { name: 'Close card', exact: true }).click()

  await openApp(page)
  await page.getByRole('button', { name: 'Edit profile', exact: true }).first().click()
  await page.getByRole('textbox', { name: 'Breed (confirm suggested candidates)', exact: true }).fill(breed)
  await page.getByRole('button', { name: 'Confirm & save profile', exact: true }).click()
  await page.getByRole('button', { name: 'Arrange home', exact: true }).click()
  await page.locator('.ph-item-list > button').filter({ hasText: 'Feather wand' }).click()
  await itemEditor.getByRole('textbox', { name: 'Name', exact: true }).fill(toyName)
  await itemEditor.getByRole('textbox', { name: 'Usage / cleaning notes', exact: true }).fill('Owner selected a ball and rope toy')
  await itemEditor.getByRole('button', { name: 'Save item & position', exact: true }).click()
  await page.getByRole('button', { name: 'Back to pet home', exact: true }).click()
  await page.getByRole('combobox', { name: 'Care activity', exact: true }).selectOption('play')
  const suggestion = page.locator('.ph-side > section:nth-of-type(2) > p')
  await expect(suggestion).toContainText(toyName)
  await expectEnglishUi(page, 'owner toy names retain their original separator in care suggestions', [
    { selector: '.ph-profile-heading > div > p', text: breed },
    ...[itemName, toyName].flatMap(text => [
      { selector: '.ph-room .ph-object-name', text },
      { selector: '.ph-room button.ph-object', attribute: 'aria-label', text },
      { selector: '.ph-scene-footer > button', text },
    ]),
    { selector: '.ph-side > section:nth-of-type(2) > p', text: toyName },
    { selector: '.ph-side > section:nth-of-type(2) > blockquote', text: observation },
  ])
  await openApp(page, 'assistant')
  await page.getByRole('textbox', { name: 'What would you like to know?', exact: true }).fill('breed')
  const answering = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Ask the twin', exact: true }).click()
  expect((await answering).ok()).toBe(true)
  const breedReply = page.getByRole('article', { name: 'Twin reply', exact: true })
  await expect(breedReply).toContainText(`Owner-confirmed breed: ${breed}`)
  await expectEnglishUi(page, 'a literal owner breed is different from a generated missing-value label', [
    { selector: 'article[aria-label="Twin reply"] > p', text: breed },
    { selector: '.fa-context-overview > p', text: observation },
  ])
  await mutate(page, '/api/home/pets/mochi', { name: 'Mochi', species: 'cat', breed: '' }, 'PUT')
  const refreshing = page.waitForResponse(response => response.url().endsWith('/api/home/state') && response.request().method() === 'GET')
  await page.getByRole('button', { name: 'Refresh records', exact: true }).click()
  expect((await refreshing).ok()).toBe(true)
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))))
  await expect(breedReply).toContainText(`Owner-confirmed breed: ${breed}`)
  await expectEnglishUi(page, 'a saved breed reply retains its original field snapshot after profile refresh', [
    { selector: 'article[aria-label="Twin reply"] > p', text: breed },
    { selector: '.fa-context-overview > p', text: observation },
  ])
  const askingAgain = page.waitForResponse(response => response.url().endsWith('/api/family/pets/mochi/chat') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Ask the twin', exact: true }).click()
  expect((await askingAgain).ok()).toBe(true)
  await expect(breedReply).toContainText('Owner-confirmed breed: Not provided.')
  await expectEnglishUi(page, 'a new breed reply describes the now-missing field in English', [
    { selector: '.fa-context-overview > p', text: observation },
  ])

  await openApp(page, 'family')
  await page.getByLabel('Display name', { exact: true }).fill(owner)
  await page.getByRole('button', { name: 'Save personal settings', exact: true }).click()
  await expect(page.getByLabel('Display name', { exact: true })).toHaveValue(owner)
  await expect(page.locator('.fa-family-settings > section:first-of-type > article > strong')).toContainText(owner)
  await expectEnglishUi(page, 'owner display name remains verbatim in controls and member summary', [
    { selector: '.fa-header > div:last-child > button:first-child', text: owner },
    { selector: '.fa-petbar > span', text: owner },
    { selector: '.fa-family-settings > section:first-of-type > form input[name="name"]', attribute: 'value', text: owner },
    { selector: '.fa-family-settings > section:first-of-type > article > strong', text: owner },
    { selector: '.fa-family-settings select[aria-label]', attribute: 'aria-label', text: owner },
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: title },
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: observation },
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: diaryTitle },
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: itemName },
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: toyName },
  ])
})

test('pristine demo fields follow the language while edited fields and raw starter records stay unchanged', async ({ page }) => {
  await page.goto('/#workbench')
  await page.getByLabel('Demo passphrase', { exact: true }).fill(PASSPHRASE)
  await page.getByRole('button', { name: 'Sign in to demo', exact: true }).click()
  await expect(page.getByTestId('facts')).toBeVisible()
  await openApp(page)
  const before = await (await page.request.get('/api/home/state')).json()
  const starter = before.objects.find((item: { kind: string }) => item.kind === 'nest')
  expect(starter).toBeTruthy()
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  await page.getByRole('button', { name: '布置小屋', exact: true }).click()
  await page.locator('.ph-item-list > button').first().click()
  const editor = page.locator('.ph-item-editor')
  const name = editor.locator('input[name="name"]')
  const note = editor.locator('input[name="note"]')
  await expect(name).toHaveValue(starter.name)
  await expect(note).toHaveValue(starter.note)
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await expect(name).toHaveValue('Window bed')
  await expect(note).toHaveValue('Starter display item; you can edit it')
  await expectEnglishUi(page, 'a pristine starter editor opened in Chinese follows English')
  await editor.getByRole('button', { name: 'Save item & position', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Add to home', exact: true })).toBeVisible()
  const after = await (await page.request.get('/api/home/state')).json()
  const saved = after.objects.find((item: { id: string }) => item.id === starter.id)
  expect({ name: saved.name, note: saved.note }).toEqual({ name: starter.name, note: starter.note })

  await page.locator('.ph-item-list > button').first().click()
  const original = '用户手写的中文小窝'
  await name.fill(original)
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  await expect(name).toHaveValue(original)
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await expect(name).toHaveValue(original)
  await expectEnglishUi(page, 'switching languages preserves a dirty owner field', [
    { selector: '.ph-item-editor input[name="name"]', attribute: 'value', text: original },
  ])

  await openApp(page, 'family')
  const settings = page.locator('.fa-family-settings > section:first-of-type > form')
  const displayName = settings.locator('input[name="name"]')
  const familyLabel = settings.locator('input[name="label"]')
  await expect(displayName).toHaveValue('Owner')
  await expect(familyLabel).toHaveValue('Owner')
  await page.getByRole('button', { name: 'Chinese', exact: true }).click()
  await expect(displayName).toHaveValue('主人')
  await expect(familyLabel).toHaveValue('主人')
  await page.getByRole('button', { name: 'English', exact: true }).click()
  await expect(displayName).toHaveValue('Owner')
  await expect(familyLabel).toHaveValue('Owner')
  await expectEnglishUi(page, 'pristine default owner and family label follow the language', [
    { selector: '.fa-family-settings > section:last-of-type .fa-record > p', text: starter.name },
  ])
})
