import { expect, test, type Locator, type Page } from '@playwright/test'

const chineseStages = [
  { label: '小狗饮食', title: '这只小狗，能吃巧克力吗？' },
  { label: '猫咪状态', title: '猫咪没精神，先看哪些记录？' },
  { label: '上下文随行', title: '少一次介绍，多一份了解。' },
] as const
const englishStages = [
  { label: 'Dog food safety', title: 'Can this dog eat chocolate?' },
  { label: 'Cat wellbeing', title: 'A low-energy cat: which records help?' },
  { label: 'Context included', title: 'Less repetition. More understanding.' },
] as const

function observePublicPage(page: Page) {
  const businessRequests: string[] = []
  const errors: string[] = []
  page.on('request', request => {
    if (/^\/api(?:\/|$)/.test(new URL(request.url()).pathname)) businessRequests.push(request.url())
  })
  page.on('pageerror', error => errors.push(error.message))
  return () => {
    expect(businessRequests).toEqual([])
    expect(errors).toEqual([])
  }
}

async function openConcierge(page: Page, english = false) {
  const cases = page.locator('#cases')
  const choices = cases.getByRole('group', { name: english ? 'Choose an everyday scenario' : '选择日常案例', exact: true })
  await expect(choices.getByRole('button')).toHaveCount(4)
  const choice = choices.getByRole('button', { name: english ? 'Pet concierge' : '宠物管家', exact: true })
  await choice.focus()
  await page.keyboard.press('Enter')
  await expect(choice).toHaveAttribute('aria-pressed', 'true')
  await expect(cases.getByRole('heading', { name: english ? 'Just ask. Your pet’s context comes along.' : '你只管问，它记得是哪一只。', exact: true })).toBeVisible()
  const preview = cases.locator('.pt-case-preview[data-case="concierge"]')
  await expect(preview).toBeVisible()
  return { cases, preview }
}

function stageChoices(cases: Locator, english = false) {
  return cases.getByRole('group', { name: english ? 'View scenario steps' : '查看案例步骤', exact: true }).getByRole('button')
}

async function selectStage(page: Page, cases: Locator, preview: Locator, index: number, english = false, key = 'Enter') {
  const stages = english ? englishStages : chineseStages
  const choices = stageChoices(cases, english)
  await expect(choices).toHaveCount(3)
  await expect(choices.nth(index)).toContainText(stages[index].label)
  await choices.nth(index).focus()
  await page.keyboard.press(key)
  await expect(choices.nth(index)).toBeFocused()
  await expect(choices.nth(index)).toHaveAttribute('aria-pressed', 'true')
  await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(stages[index].title)
  await expect(preview).not.toContainText(/\bxxx\b|TODO|Lorem ipsum|占位符/i)
  const boundary = preview.locator('footer')
  await expect(boundary).toContainText(english ? /Preset conversations.*fictional illustrations/ : /预设对话.*虚构示意/)
  await expect(boundary).toContainText(english ? 'Alexa is a web simulation' : 'Alexa 为网页模拟')
  await expect(boundary).toContainText(english ? 'No real-time AI' : '非实时 AI')
}

async function expectNoOverflow(page: Page, preview: Locator) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await expect.poll(() => preview.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true)
}

async function expectReferences(preview: Locator, references: readonly (readonly [string, string])[]) {
  const links = preview.getByRole('link')
  await expect(links).toHaveCount(references.length)
  for (const [name, href] of references) {
    const link = preview.getByRole('link', { name, exact: true })
    await expect(link).toHaveAttribute('href', href)
    await expect(link).toHaveAttribute('target', '_blank')
    await expect(link).toHaveAttribute('rel', /(?:^|\s)(?:noreferrer|noopener)(?:\s|$)/)
  }
}

test('adds a fourth illustrative case with keyboard steps, concrete pet context and preset safety replies', async ({ page }) => {
  const verifyPublicPage = observePublicPage(page)
  await page.goto('/#cases')
  const { cases, preview } = await openConcierge(page)
  await expect(cases.getByRole('group', { name: '选择日常案例', exact: true }).getByRole('button')).toHaveText(['家庭交接', '成长回顾', '偏好接续', '宠物管家'])
  await expect(cases).toContainText('虚构情景演示')
  await expect(cases.getByRole('link', { name: '打开 Alexa+ 网页模拟器', exact: true })).toHaveAttribute('href', '#alexa')

  await selectStage(page, cases, preview, 0)
  for (const fact of ['Miso', '9.40 kg', '鸡肉', '预设对话']) await expect(preview).toContainText(fact)
  await expect(preview).toContainText(/彭布罗克.*柯基/)
  await expect(preview).toContainText(/2\s*岁/)
  await expect(preview).toContainText(/公|雄性/)
  const dogQuestion = await preview.locator('.pc-owner-message p').innerText()
  expect(dogQuestion).toMatch(/小狗.*巧克力/)
  const reply = preview.locator('.pc-assistant-message')
  await expect(reply).toContainText('Alexa · 预设回复')
  await expect(reply).toContainText(/不可以|不能吃/)
  await expect(reply).toContainText(/巧克力.*(?:中毒|有毒|风险)/)
  await expect(reply).toContainText(/与(?:品种|犬种)无关|(?:所有|任何).*(?:品种|犬种)/)
  await expect(reply).toContainText(/确认.*鸡肉/)
  await expect(reply).toContainText(/少量/)
  await expect(reply).toContainText(/原味|无调味|无盐/)
  await expect(reply).toContainText(/全熟|熟透/)
  await expect(reply).toContainText(/去骨|无骨/)
  await expect(reply).toContainText(/先确认.*(?:不过敏|无过敏)/)
  await expect(reply).toContainText(/误食.*立即.*兽医/)
  await expectReferences(preview, [
    ['Merck · 巧克力中毒', 'https://www.merckvetmanual.com/toxicology/food-hazards/chocolate-toxicosis-in-animals'],
    ['PDSA · 狗狗饮食', 'https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet'],
  ])

  await selectStage(page, cases, preview, 1, false, 'Space')
  for (const fact of ['Luna', '3.68 kg', '模拟记录']) await expect(preview).toContainText(fact)
  await expect(preview).toContainText(/短毛/)
  await expect(preview).toContainText(/3\s*岁/)
  await expect(preview).toContainText(/母|雌性/)
  await expect(preview.locator('.pc-owner-message')).toContainText(/猫咪.*没有精神/)
  for (const observation of ['进食', '饮水', '排尿', '呼吸', '呕吐', '腹泻']) await expect(reply).toContainText(observation)
  await expect(reply).toContainText(/不能.*(?:排除|证明|判断)|不代表.*健康/)
  await expect(reply).toContainText(/持续.*(?:就诊|兽医)/)
  await expect(reply).toContainText(/呼吸困难.*排尿困难.*立即.*就医/)
  const activity = preview.getByRole('region', { name: 'Luna 的模拟家庭活动记录', exact: true })
  const activityRows = activity.getByRole('listitem')
  await expect(activityRows).toHaveCount(3)
  for (const [index, time, place] of [[0, '07:40', '窗边'], [1, '12:20', '客厅'], [2, '18:10', '饮水区']] as const) {
    await expect(activityRows.nth(index)).toContainText(time)
    await expect(activityRows.nth(index)).toContainText(place)
  }
  await expect(activity).toContainText(/饮水区.*(?:≠|不代表|不能确认).*饮水/)
  await expect(activity).toContainText(/不能.*判断健康/)
  await expectReferences(preview, [['VCA · 猫咪生病的迹象', 'https://vcahospitals.com/know-your-pet/recognizing-signs-of-illness-in-cats']])

  await selectStage(page, cases, preview, 2)
  const newSession = preview.locator('section').filter({ has: page.getByRole('heading', { level: 4, name: '没有宠物资料的新会话', exact: true }) })
  const conciergeSession = preview.locator('section').filter({ has: page.getByRole('heading', { level: 4, name: 'PawTwin 宠物管家', exact: true }) })
  const longQuestion = newSession.locator(':scope > p')
  const shortQuestion = conciergeSession.locator(':scope > p')
  for (const context of ['Miso', '9.40 kg', '鸡肉', '巧克力']) await expect(longQuestion).toContainText(context)
  await expect(shortQuestion).toHaveText(dogQuestion)
  expect((await shortQuestion.innerText()).length).toBeLessThan((await longQuestion.innerText()).length)
  const includedContext = conciergeSession.locator('.pc-carried-context')
  await expect(includedContext).toContainText(/自动带入.*上下文/)
  for (const context of ['Miso', '9.40 kg', '鸡肉']) await expect(includedContext).toContainText(context)
  await expect(includedContext).toContainText(/主人(?:已)?确认/)

  // A case change starts its own first step rather than inheriting this one's
  // final comparison; returning must also clear the previously selected step.
  await cases.getByRole('button', { name: '家庭交接', exact: true }).click()
  await expect(stageChoices(cases).first()).toHaveAttribute('aria-pressed', 'true')
  await cases.getByRole('button', { name: '宠物管家', exact: true }).click()
  await expect(stageChoices(cases).first()).toHaveAttribute('aria-pressed', 'true')
  await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(chineseStages[0].title)
  await expect(preview).toContainText('Miso')
  await expect(preview).not.toContainText('没有宠物资料的新会话')
  verifyPublicPage()
})

test('keeps every concierge step readable at four widths with reduced motion', async ({ page }, testInfo) => {
  test.setTimeout(90_000)
  const verifyPublicPage = observePublicPage(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.goto('/#cases')
    const { cases, preview } = await openConcierge(page)
    await expect(page.getByRole('button', { name: '已遵循系统减少动画', exact: true })).toBeDisabled()
    for (let index = 0; index < chineseStages.length; index++) {
      await selectStage(page, cases, preview, index)
      await expectNoOverflow(page, preview)
      if (width === 320 || width === 1440 || (width === 390 && index === 1)) {
        await cases.screenshot({
          path: testInfo.outputPath(`pet-concierge-${width}-step-${index + 1}.png`),
          animations: 'disabled',
          style: '.pt-nav, .pt-skip, .pt-motion-toggle { visibility: hidden !important; }',
        })
      }
    }
  }
  verifyPublicPage()
})

test.describe('English default and language continuity', () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('keeps the active pet example and values when switching between English and Chinese', async ({ page }) => {
    const verifyPublicPage = observePublicPage(page)
    await page.setViewportSize({ width: 390, height: 1000 })
    await page.goto('/#cases')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    const { cases, preview } = await openConcierge(page, true)
    await selectStage(page, cases, preview, 0, true)
    for (const fact of ['Miso', '9.40 kg', 'Pembroke Welsh Corgi', 'Male', '2 years', 'chicken']) await expect(preview).toContainText(fact)
    await expect(preview.locator('.pc-assistant-message')).toContainText('Alexa · Preset reply')
    await expectNoOverflow(page, preview)

    await selectStage(page, cases, preview, 1, true)
    for (const fact of ['Luna', '3.68 kg', 'Domestic shorthair', 'Female', '3 years', 'Simulated records']) await expect(preview).toContainText(fact)
    await expectNoOverflow(page, preview)
    await page.getByRole('button', { name: 'Chinese', exact: true }).click()
    await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')
    await expect(stageChoices(cases).nth(1)).toHaveAttribute('aria-pressed', 'true')
    await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(chineseStages[1].title)
    for (const fact of ['Luna', '3.68 kg', '模拟记录']) await expect(preview).toContainText(fact)
    await page.getByRole('button', { name: 'English', exact: true }).click()
    await expect(stageChoices(cases, true).nth(1)).toHaveAttribute('aria-pressed', 'true')
    await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(englishStages[1].title)
    for (const fact of ['Luna', '3.68 kg']) await expect(preview).toContainText(fact)

    await selectStage(page, cases, preview, 2, true)
    for (const fact of ['Miso', '9.40 kg', 'chicken']) await expect(preview).toContainText(fact)
    await expectNoOverflow(page, preview)
    await page.getByRole('button', { name: 'Chinese', exact: true }).click()
    await expect(stageChoices(cases).nth(2)).toHaveAttribute('aria-pressed', 'true')
    await expect(preview.getByRole('heading', { level: 3 }).first()).toHaveText(chineseStages[2].title)
    for (const fact of ['Miso', '9.40 kg', '鸡肉']) await expect(preview).toContainText(fact)
    verifyPublicPage()
  })
})
