import { expect, test } from '@playwright/test'

import { login, resetDemo } from './helpers'

// The analysis path is asynchronous under PAWTWIN_WORKER_MODE=background, so the
// budget is generous; retries stay at 0 so a real race is never masked.
test('approve executes once, shows real evidence and survives reload', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)

  // Every implementation label comes from the backend, never from this source.
  await expect(page.getByTestId('mode-badge')).toContainText('LOCAL')
  await expect(page.getByTestId('mode-badge')).toContainText('AWS 未连接')
  await expect(page.getByTestId('impl-labels')).toContainText('本地替身')
  await expect(page.getByTestId('impl-labels')).toContainText('SQLite')
  await expect(page.getByTestId('impl-labels')).toContainText('长期记忆：未实现')

  await resetDemo(page)

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('proposal-action')).toContainText('出粮 15 克')

  // Evidence ledger: real tool calls, with source and retrieval time.
  await expect(page.getByTestId('evidence-item')).toHaveCount(2)
  const evidence = page.getByTestId('evidence-list')
  await expect(evidence).toContainText('查询宠物当前事实')
  await expect(evidence).toContainText('读取策略摘要')
  await expect(evidence).toContainText('业务数据库')
  await expect(evidence).toContainText('硬性策略')

  // Telemetry is explicit about NOT being a cloud call.
  const telemetry = page.getByTestId('telemetry')
  await expect(telemetry).toContainText('本地替身')
  await expect(telemetry).toContainText('0 次（上限 4）')
  await expect(telemetry).toContainText('无（未发生真实云调用）')

  await page.getByTestId('approve').click()
  await expect(page.getByTestId('run-status')).toHaveText('已完成')
  await expect(page.getByTestId('receipt')).toContainText('模拟执行成功')
  await expect(page.getByTestId('receipt')).toContainText('simulated=true')

  // Quota accounted exactly once; a terminal run disables both decisions.
  await expect(page.getByTestId('facts')).toContainText('15 / 30 克')
  await expect(page.getByTestId('approve')).toBeDisabled()
  await expect(page.getByTestId('decline')).toBeDisabled()

  // Reload: the outcome is durable and still not double-accounted.
  await page.reload()
  await expect(page.getByTestId('run-status')).toHaveText('已完成')
  await expect(page.getByTestId('receipt')).toContainText('模拟执行成功')
  await expect(page.getByTestId('facts')).toContainText('15 / 30 克')
  await expect(page.getByTestId('evidence-item')).toHaveCount(2)
  await page.screenshot({ path: 'test-results/approve.png', fullPage: true })
})

test('an injected device failure never accounts quota', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await page.getByTestId('device-mode').selectOption('failed')
  await expect(page.getByTestId('notice')).toContainText('仅影响之后的新命令')

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('proposal-action')).toContainText('出粮 15 克')
  await page.getByTestId('approve').click()

  await expect(page.getByTestId('run-status')).toHaveText('执行失败')
  await expect(page.getByTestId('receipt')).toContainText('模拟执行失败')
  // A failure is not accounting: the quota stays at zero.
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  // Execution failure is not an analysis failure: no failure_reason is shown.
  await expect(page.getByTestId('failure-reason')).toHaveCount(0)

  await page.getByTestId('device-mode').selectOption('succeeded')
  await page.screenshot({ path: 'test-results/approve-device-failed.png', fullPage: true })
})

test('an unknown fact reaches needs-info and is never shown as zero', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await page.locator('#clear-last-fed').check()
  await page.getByTestId('apply-facts').click()
  await expect(page.getByTestId('facts')).toContainText('未知')

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('信息不足')
  await expect(page.getByTestId('policy-reason')).toContainText('缺少必要事实')
  // No feeding without the facts, and nothing to approve.
  await expect(page.getByTestId('approve')).toBeDisabled()
  await expect(page.getByTestId('receipt')).toHaveCount(0)
  await page.screenshot({ path: 'test-results/needs-info.png', fullPage: true })
})

test('changing facts invalidates a pending approval with a readable notice', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')

  // The owner injects a recent feed while an approval is pending (A03).
  await page.getByLabel('上次喂食距今（分钟，0–1440）').fill('10')
  await page.getByTestId('apply-facts').click()
  await expect(page.getByTestId('notice')).toContainText('facts_version')

  await page.getByTestId('approve').click()

  await expect(page.getByTestId('notice')).toContainText('旧批准失效')
  await expect(page.getByTestId('notice')).toContainText('未调用模型')
  await expect(page.getByTestId('run-status')).toHaveText('已阻止')
  await expect(page.getByTestId('policy-reason')).toContainText('距上次喂食过近')
  await expect(page.getByTestId('receipt')).toHaveCount(0)
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  await page.screenshot({ path: 'test-results/stale-approval.png', fullPage: true })
})
