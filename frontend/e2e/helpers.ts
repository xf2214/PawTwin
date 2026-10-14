import { expect, type Page } from '@playwright/test'

declare const process: { env: Record<string, string | undefined> }

// Non-secret LOCAL demo default; the judge passphrase is injected via
// PAWTWIN_DEMO_PASSPHRASE and delivered through private test instructions.
export const PASSPHRASE = process.env.PAWTWIN_DEMO_PASSPHRASE ?? 'local-demo-passphrase'

export async function login(page: Page): Promise<void> {
  await page.goto('/#workbench')
  await page.getByLabel('演示口令').fill(PASSPHRASE)
  await page.getByRole('button', { name: '登录演示' }).click()
  await expect(page.getByTestId('facts')).toBeVisible()
}

/**
 * Every spec shares ONE server process and ONE in-memory SQLite database, so a
 * previous spec's accounting (which also sets last_fed_minutes_ago to 0) would
 * otherwise turn the next spec's food request into a policy BLOCK. Each business
 * spec therefore resets through the demo controls instead of relying on the order
 * in which Playwright happens to run the files.
 */
export async function resetDemo(page: Page): Promise<void> {
  await page.getByRole('button', { name: '展开演示控制区' }).click()
  await page.getByTestId('device-mode').selectOption('succeeded')
  await page.getByTestId('reset-facts').click()
  await expect(page.getByTestId('notice')).toContainText('已恢复演示事实默认值')
  await expect(page.getByTestId('facts')).toContainText('360 分钟')
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
}

/** Open the demo area without resetting anything. */
export async function openDemo(page: Page): Promise<void> {
  const toggle = page.getByRole('button', { name: '展开演示控制区' })
  if (await toggle.isVisible()) await toggle.click()
}
