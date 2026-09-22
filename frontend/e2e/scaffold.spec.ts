import { expect, test } from '@playwright/test'

test('shows a connected scaffold without pretending planned features are ready', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'PawTwin' })).toBeVisible()
  await expect(page.getByText('本地骨架已连接')).toBeVisible()
  await expect(page.getByText('模拟传感器事件', { exact: true })).toBeVisible()
  await expect(page.getByText('模拟执行器', { exact: true })).toBeVisible()
  await expect(page.getByText('项圈为概念设计', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '进入事件台' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '进入审批台' })).toBeDisabled()
  await expect(page.getByRole('button', { name: '查看长期记忆' })).toBeDisabled()
  await page.screenshot({ path: 'test-results/scaffold.png', fullPage: true })
})
