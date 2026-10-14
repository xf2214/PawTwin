import { expect, test } from '@playwright/test'

test('workbench deep links preserve their own login gate and stay separate from family accounts', async ({ page }) => {
  for (const path of ['history', 'settings']) {
    await page.goto(`/#workbench/${path}`)
    await expect(page.getByRole('button', { name: '登录演示', exact: true })).toBeVisible({ timeout: 4000 })
    await expect(page).toHaveTitle(/照护工作台/)
    await expect(page.getByTestId('facts')).toHaveCount(0)
  }
  await page.locator('.as-header').getByRole('link', { name: /家庭应用/ }).click()
  await expect(page.getByRole('button', { name: '创建本地账号', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '登录演示', exact: true })).toHaveCount(0)
  await page.locator('.as-header').getByRole('link', { name: /原工作台/ }).click()
  await expect(page.getByRole('button', { name: '登录演示', exact: true })).toBeVisible()
})

test('application navigation stays reachable at narrow widths', async ({ page }) => {
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 850 })
    await page.goto('/#app/home')
    await expect(page.getByRole('link', { name: '产品介绍', exact: true })).toBeVisible()
    await expect(page.locator('.as-header').getByRole('link', { name: /原工作台/ })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  }
})
