const { chromium, expect } = require('../../../frontend/node_modules/@playwright/test')
const fs = require('node:fs')
const path = require('node:path')

;(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true })
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8807', viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
  const page = await context.newPage()
  await page.addInitScript(() => localStorage.setItem('pawtwin-language', 'zh'))
  const checks = []
  try {
    await page.goto('/?preview=workbench-concierge-20261015#workbench/concierge')
    await page.getByLabel('演示口令', { exact: true }).fill('local-demo-passphrase')
    await page.getByRole('button', { name: '登录演示', exact: true }).click()
    await expect(page.locator('.wb-concierge')).toBeVisible()
    for (const language of ['zh', 'en']) {
      if (language === 'en') await page.getByRole('button', { name: 'English', exact: true }).click()
      const buttons = page.locator('.wb-concierge-choices').getByRole('button')
      for (const width of [1440, 390]) {
        await page.setViewportSize({ width, height: 1000 })
        for (const step of [0, 1]) {
          await buttons.nth(step).click()
          await expect(buttons.nth(step)).toHaveAttribute('aria-pressed', 'true')
          await page.evaluate(() => window.scrollTo(0, 0))
          const geometry = await page.evaluate(() => ({ width: innerWidth, document: document.documentElement.scrollWidth }))
          if (geometry.document > geometry.width) throw new Error('Horizontal overflow')
          const file = `full-${language}-${width}-step-${step + 1}.png`
          await page.screenshot({ path: path.join(__dirname, file), fullPage: true, animations: 'disabled' })
          checks.push({ file, language, step, ...geometry })
        }
      }
    }
    fs.writeFileSync(path.join(__dirname, 'full-page-checks.json'), JSON.stringify(checks, null, 2))
    console.log(JSON.stringify({ screenshots: checks.length, languages: ['zh', 'en'], horizontal_overflow: false }))
  } finally { await browser.close() }
})().catch(error => { console.error(error); process.exitCode = 1 })
