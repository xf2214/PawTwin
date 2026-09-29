import { expect, test } from '@playwright/test'

import { login } from './helpers'

// Day-3 (gate G8, A06/A07 structure). These run against the SHIPPED backend with
// the honest ``not_implemented`` memory backend: feedback is really saved, its
// status never claims extraction, and a new session rotates the conversation while
// login/facts survive. Real AgentCore retrieval stays a CONDITION item, so nothing
// here may be read as "cross-session memory verified".

test('owner feedback is saved honestly and never shown as retrieved memory', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)

  await expect(page.getByTestId('memory-area')).toBeVisible()
  await expect(page.getByTestId('memory-backend')).toContainText('未实现（无 AWS 账号）')

  const marker = `观察-${Date.now()}`
  await page.getByTestId('feedback-text').fill(marker)
  await page.getByTestId('feedback-scope').selectOption('observation')
  await page.getByTestId('submit-feedback').click()

  await expect(page.getByTestId('notice')).toContainText('已保存主人观察原文')

  const item = page.getByTestId('feedback-item').filter({ hasText: marker })
  await expect(item).toBeVisible()
  // ``saved`` = raw stored. It is NEVER dressed up as an extracted/retrieved memory.
  await expect(item.getByTestId('feedback-status')).toContainText('已保存原文')
  await expect(page.getByTestId('memory-area')).not.toContainText('已检索到记忆')
  // Day-4 ruling 13 reworded the ``available`` label to a lifecycle phrasing;
  // the forbidden substring tightens accordingly: nothing may claim retrievability.
  await expect(page.getByTestId('memory-area')).not.toContainText('可检索')

  // Durable: a reload re-reads it from /api/state, not from client memory.
  await page.reload()
  await expect(page.getByTestId('feedback-item').filter({ hasText: marker })).toBeVisible()
  await page.screenshot({ path: 'test-results/feedback.png', fullPage: true })
})

test('today-only feedback is labelled as never becoming a permanent preference', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)

  const marker = `仅今天-${Date.now()}`
  await page.getByTestId('feedback-text').fill(marker)
  await page.getByTestId('feedback-scope').selectOption('today_only')
  await page.getByTestId('submit-feedback').click()

  await expect(page.getByTestId('notice')).toContainText('不会成为永久偏好')
  const item = page.getByTestId('feedback-item').filter({ hasText: marker })
  await expect(item).toContainText('仅今天')
  await expect(item.getByTestId('feedback-status')).toContainText('已保存原文')
})

test('a new session rotates the conversation but keeps login and facts', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)

  const before = await page.getByTestId('memory-backend').textContent()
  await page.getByTestId('new-session').click()
  await expect(page.getByTestId('notice')).toContainText('已开启新会话')

  // Still logged in (facts render) and the memory backend is unchanged/honest.
  await expect(page.getByTestId('facts')).toBeVisible()
  await expect(page.getByTestId('memory-backend')).toContainText('未实现（无 AWS 账号）')
  const after = await page.getByTestId('memory-backend').textContent()
  // The conversation id is part of the label, so it must have rotated.
  expect(after).not.toEqual(before)
  await page.screenshot({ path: 'test-results/new-session.png', fullPage: true })
})
