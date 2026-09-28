import { expect, test } from '@playwright/test'

import { login, resetDemo } from './helpers'

test('decline never becomes simulated execution and survives reload', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  // Shared in-memory database: reset instead of trusting the file order.
  await resetDemo(page)

  // Send a simulated food request; the run settles at awaiting_approval.
  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('proposal-action')).toContainText('出粮')

  // Decline: zero execution, no receipt.
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  await expect(page.getByTestId('receipt')).toHaveCount(0)
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')

  // Reload: the durable decision persists and never shows a simulated success.
  await page.reload()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  await expect(page.getByText('模拟执行成功', { exact: true })).toHaveCount(0)
  await page.screenshot({ path: 'test-results/decline.png', fullPage: true })
})
