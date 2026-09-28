import { expect, test } from '@playwright/test'

import { login } from './helpers'

test('gates business data behind the demo login', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
  // Unauthenticated: no pet facts, no approval controls, no implementation labels.
  await expect(page.getByTestId('facts')).toHaveCount(0)
  await expect(page.getByTestId('approve')).toHaveCount(0)
  await expect(page.getByTestId('impl-labels')).toHaveCount(0)
})

test('keeps simulation boundaries and the local/aws label visible after login', async ({ page }) => {
  test.setTimeout(60_000)
  await login(page)

  await expect(page.getByTestId('mode-badge')).toContainText('LOCAL')
  await expect(page.getByTestId('mode-badge')).toContainText('AWS 未连接')
  await expect(page.getByText('模拟传感器事件', { exact: true })).toBeVisible()
  await expect(page.getByText('模拟执行器', { exact: true })).toBeVisible()
  await expect(page.getByText('项圈为概念设计', { exact: true })).toBeVisible()
  // Day-3: the memory area is live, and honest that long-term memory is not wired.
  await expect(page.getByTestId('memory-area')).toBeVisible()
  await expect(page.getByTestId('memory-backend')).toContainText('未实现（无 AWS 账号）')
  // Day-2: the stand-in is labelled where it is actually used, and the storage is
  // named as local/unverified so the page can never imply a cloud connection.
  await expect(page.getByTestId('impl-labels')).toContainText('本地替身')
  await expect(page.getByTestId('impl-labels')).toContainText('未经云端验证')
  await expect(page.getByTestId('impl-labels')).toContainText('长期记忆：未实现')
  await page.screenshot({ path: 'test-results/shell.png', fullPage: true })
})
