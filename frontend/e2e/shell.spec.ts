import { expect, test } from '@playwright/test'

declare const process: { env: Record<string, string | undefined> }

// Non-secret LOCAL demo default; the judge passphrase is injected via
// PAWTWIN_DEMO_PASSPHRASE and delivered through private test instructions.
const PASSPHRASE = process.env.PAWTWIN_DEMO_PASSPHRASE ?? 'local-demo-passphrase'

test('gates business data behind the demo login', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
  // Unauthenticated: no pet facts and no approval controls are exposed.
  await expect(page.getByTestId('facts')).toHaveCount(0)
  await expect(page.getByTestId('approve')).toHaveCount(0)
})

test('keeps simulation boundaries and the local/aws label visible after login', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('演示口令').fill(PASSPHRASE)
  await page.getByRole('button', { name: '登录演示' }).click()

  await expect(page.getByTestId('mode-badge')).toContainText('LOCAL')
  await expect(page.getByTestId('mode-badge')).toContainText('AWS 未连接')
  await expect(page.getByText('模拟传感器事件', { exact: true })).toBeVisible()
  await expect(page.getByText('模拟执行器', { exact: true })).toBeVisible()
  await expect(page.getByText('项圈为概念设计', { exact: true })).toBeVisible()
  await expect(page.getByTestId('memory-placeholder')).toBeVisible()
  await page.screenshot({ path: 'test-results/shell.png', fullPage: true })
})
