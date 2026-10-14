import { expect, test } from '@playwright/test'
import { login, openDemo, resetDemo } from './helpers'

// Run after feeding-success checks: unknown execution retains the durable feeding
// reservation. Resetting demo facts does not resolve a potentially executed command.
test('an unknown device receipt shows 状态未知 and never a success', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await openDemo(page)
  await page.getByTestId('device-mode').selectOption('unknown')
  await expect(page.getByTestId('notice')).toContainText('仅影响之后的新命令')

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await page.getByTestId('approve').click()

  await expect(page.getByTestId('run-status')).toHaveText('状态未知')
  await expect(page.getByTestId('receipt')).toContainText('执行状态未知')
  await expect(page.getByTestId('receipt')).toContainText('simulated=true')
  // The page must never dress an unknown outcome up as a completed feeding.
  await expect(page.getByTestId('receipt')).not.toContainText('模拟执行成功')
  // Unknown is not success: no quota was accounted.
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  // UNKNOWN is terminal like succeeded/failed: both decisions lock, so no later
  // approval can reinterpret an outcome the device never confirmed. The run stays
  // 'unknown' in the list -- that IS its settled state, nothing pending leaks on.
  await expect(page.getByTestId('approve')).toBeDisabled()
  await expect(page.getByTestId('decline')).toBeDisabled()

  await page.getByTestId('device-mode').selectOption('succeeded')
  // What this does NOT prove: a real device timeout or a genuinely LATE receipt
  // arriving after the run moved on. This is the injected three-state simulator;
  // asynchronous late/arrival races stay a written-down condition item.
  await page.screenshot({ path: 'test-results/acceptance-unknown-receipt.png' })
})
