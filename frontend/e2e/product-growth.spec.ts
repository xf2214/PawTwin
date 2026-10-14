import { expect, test, type Locator, type Page } from '@playwright/test'

// Independent expected samples: a UI calculation or pet-switching regression
// must not silently change the test's expected values with the implementation.
const samples = [
  { name: 'Mochi', weights: [4.10, 4.16, 4.14, 4.22] },
  { name: 'Miso', weights: [9.20, 9.32, 9.28, 9.40] },
  { name: 'Luna', weights: [3.60, 3.64, 3.62, 3.68] },
  { name: 'Coco', weights: [5.20, 5.26, 5.24, 5.30] },
] as const
const dates = ['09/22', '09/29', '10/06', '10/13'] as const

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

async function openGrowth(page: Page) {
  const features = page.locator('#features')
  await features.getByRole('button', { name: '成长记录', exact: true }).click()
  const preview = features.getByLabel('成长记录界面示意', { exact: true })
  await expect(preview.locator('.pg-demo')).toBeVisible()
  return preview
}

async function expectCurve(preview: Locator, petName: string) {
  const trend = preview.getByLabel(`${petName} 的模拟体重曲线`, { exact: true })
  await expect(trend).toBeVisible()
  const points = trend.locator('.pg-chart-point')
  await expect(points).toHaveCount(4)
  const coordinates = await points.evaluateAll(elements => elements.map(element => ({
    x: Number(element.getAttribute('cx')),
    y: Number(element.getAttribute('cy')),
    hasCoordinates: element.hasAttribute('cx') && element.hasAttribute('cy'),
  })))
  expect(coordinates.every(point => point.hasCoordinates && Number.isFinite(point.x) && Number.isFinite(point.y))).toBe(true)
  for (let index = 1; index < coordinates.length; index++) {
    expect(coordinates[index].x).toBeGreaterThan(coordinates[index - 1].x)
  }
  // All four illustrative pets gain, dip slightly, then reach their maximum.
  // Check the rendered chart's direction rather than only counting SVG nodes.
  expect(coordinates[1].y).toBeLessThan(coordinates[0].y)
  expect(coordinates[2].y).toBeGreaterThan(coordinates[1].y)
  expect(coordinates[3].y).toBeLessThan(Math.min(...coordinates.slice(0, 3).map(point => point.y)))
}

async function expectSamples(preview: Locator, sample: typeof samples[number]) {
  const demo = preview.locator('.pg-demo')
  await expect(demo).toContainText('模拟数据')
  await expect(demo).toContainText('2026')
  const latest = sample.weights[sample.weights.length - 1]
  const change = latest - sample.weights[0]
  await expect(demo.locator('.pg-latest')).toContainText(`${latest.toFixed(2)} kg`)
  await expect(demo.locator('.pg-change')).toContainText(`+${change.toFixed(2)} kg`)
  const rows = demo.locator('.pg-records').getByRole('listitem')
  await expect(rows).toHaveCount(4)
  for (let index = 0; index < dates.length; index++) {
    await expect(rows.nth(index)).toContainText(dates[index])
    await expect(rows.nth(index)).toContainText(`${sample.weights[index].toFixed(2)} kg`)
    await expect(rows.nth(index)).toContainText('电子秤 · 主人录入（模拟）')
  }
  await expectCurve(preview, sample.name)
}

test('uses pet-specific simulated records and derives summaries from the displayed samples without business requests', async ({ page }) => {
  const verifyPublicPage = observePublicPage(page)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/#features')
  const preview = await openGrowth(page)
  const choices = page.getByRole('group', { name: '选择示例宠物', exact: true })
  for (const sample of samples) {
    const choice = choices.getByRole('button', { name: `查看 ${sample.name} 的产品示意`, exact: true })
    await choice.focus()
    await page.keyboard.press('Enter')
    await expect(choice).toHaveAttribute('aria-pressed', 'true')
    await expectSamples(preview, sample)
  }

  // These fixtures belong only to this public preview; the selected example
  // does not become a persisted household/pet selection on reload.
  await page.reload()
  await expect(choices.getByRole('button', { name: '查看 Mochi 的产品示意', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expectSamples(await openGrowth(page), samples[0])
  verifyPublicPage()
})

test('keeps the growth case first measurement, latest measurement, and final curve consistent', async ({ page }) => {
  const verifyPublicPage = observePublicPage(page)
  await page.goto('/#cases')
  const cases = page.getByRole('region', { name: '把功能，放进日常。', exact: true })
  await cases.getByRole('button', { name: '成长回顾', exact: true }).click()
  const preview = cases.locator('.pt-case-preview[data-case="growth"]')
  const steps = cases.getByRole('group', { name: '查看案例步骤', exact: true }).getByRole('button')
  for (const [index, date, weight] of [[0, dates[0], '3.60 kg'], [1, dates[3], '3.68 kg']] as const) {
    await steps.nth(index).focus()
    await page.keyboard.press('Enter')
    await expect(steps.nth(index)).toHaveAttribute('aria-pressed', 'true')
    await expect(preview).toContainText('模拟数据')
    await expect(preview).toContainText(date)
    await expect(preview).toContainText(weight)
    await expect(preview).toContainText('电子秤 · 主人录入（模拟）')
    await expect(preview).not.toContainText(/未提供|无有效测量|本页没有测量数值|待实际测量后填写/)
  }
  await steps.last().click()
  await expect(preview.locator('.pg-latest')).toContainText('3.68 kg')
  await expect(preview.locator('.pg-change')).toContainText('+0.08 kg')
  await expect(preview).toContainText('模拟数据')
  await expectCurve(preview, 'Luna')

  // Returning to this scenario starts at the first example instead of carrying
  // another scenario's step into its measurements.
  await cases.getByRole('button', { name: '家庭交接', exact: true }).click()
  await cases.getByRole('button', { name: '成长回顾', exact: true }).click()
  await expect(steps.first()).toHaveAttribute('aria-pressed', 'true')
  await expect(preview).toContainText('3.60 kg')
  verifyPublicPage()
})

test('keeps populated growth previews readable at supported widths', async ({ page }, testInfo) => {
  test.setTimeout(60_000)
  const verifyPublicPage = observePublicPage(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.goto('/#features')
    const preview = await openGrowth(page)
    await expectSamples(preview, samples[0])
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(await preview.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true)
    if (width !== 768) {
      await page.locator('#features').screenshot({ path: testInfo.outputPath(`growth-records-${width}.png`), animations: 'disabled', style: '.pt-nav, .pt-skip, .pt-motion-toggle { visibility: hidden !important; }' })
    }

    const cases = page.getByRole('region', { name: '把功能，放进日常。', exact: true })
    await cases.getByRole('button', { name: '成长回顾', exact: true }).click()
    await cases.getByRole('group', { name: '查看案例步骤', exact: true }).getByRole('button').last().click()
    const casePreview = cases.locator('.pt-case-preview[data-case="growth"]')
    await expectCurve(casePreview, 'Luna')
    await expect(casePreview.locator('.pg-latest')).toContainText('3.68 kg')
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(await casePreview.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true)
    if (width !== 768) {
      await cases.screenshot({ path: testInfo.outputPath(`growth-case-${width}.png`), animations: 'disabled', style: '.pt-nav, .pt-skip, .pt-motion-toggle { visibility: hidden !important; }' })
    }
  }
  verifyPublicPage()
})
