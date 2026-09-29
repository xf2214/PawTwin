import { expect, test } from '@playwright/test'

import { login, openDemo, resetDemo } from './helpers'

// Day-4 FE-04 browser acceptance matrix. Every case carries its own honest
// boundary ("what this does NOT prove"). None of these may be read as cloud,
// cross-replica, restart-in-flight, or real-model evidence: the server runs
// local_fake + background worker on an IN-MEMORY database (playwright webServer),
// one browser, one process.

test('an unauthenticated session sees the login gate and business APIs return 401 JSON', async ({
  page,
}) => {
  // A12 local surface: no routing exists in this SPA, so the deep-link surface is
  // the API itself. Navigate straight at /api/state without a session cookie.
  const [response] = await Promise.all([
    page.waitForResponse((r) => r.url().endsWith('/api/state')),
    page.goto('/api/state'),
  ])
  expect(response.status()).toBe(401)
  const body = await page.textContent('body')
  expect(body ?? '').toContain('UNAUTHENTICATED')
  expect(body ?? '').not.toContain('awaiting_approval')

  await page.goto('/')
  await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
  await expect(page.getByTestId('facts')).toHaveCount(0)
  await expect(page.getByTestId('impl-labels')).toHaveCount(0)
  // What this does NOT prove: authorisation across replicas, rate limiting,
  // session TTL, or HTTPS cookie flags. Local HTTP only; the passphrase check
  // lives server-side but is a single shared demo secret.
  await page.screenshot({ path: 'test-results/acceptance-unauthorized.png' })
})

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

test('reload while awaiting_approval keeps the pending request pending', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')

  await page.reload()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('receipt')).toHaveCount(0)
  // The CSRF token is memory-only BY DESIGN (api.ts keeps it out of localStorage),
  // so a reload drops it. The honest behaviour is to say so and disable the
  // decision buttons, never to offer a click that would 403.
  await expect(page.getByTestId('reauth-hint')).toBeVisible()
  await expect(page.getByTestId('approve')).toBeDisabled()

  // Re-authenticating restores a token for the SAME pending run.
  await page.getByRole('button', { name: '退出' }).click()
  await login(page)
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  // What this does NOT prove: restart durability. The webServer keeps an
  // in-memory database, so this only shows a reload re-reads server state.
  // Process restart recovery is covered by the backend restart tests, NOT here.
})

test('desktop 1440px and narrow 390px show no overflow and states are not color-only', async ({
  page,
}) => {
  test.setTimeout(120_000)
  // Login ONCE, before the loop: the session cookie survives a viewport change, so
  // a second login() would find no login form at all. resetDemo leaves the demo area
  // open, and declining never accounts quota, so the facts stay 360 min / 0 g and the
  // second width can send its own request without another reset.
  await page.setViewportSize({ width: 1440, height: 900 })
  await login(page)
  await resetDemo(page)
  for (const viewport of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport)
    await page.getByRole('button', { name: '发送吃饭请求' }).click()
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')

    // No horizontal overflow at either width.
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    await page.screenshot({
      path: `test-results/acceptance-viewport-before-assert-${viewport.width}.png`,
      fullPage: true,
    })
    if (overflow > 0) {
      // Named diagnostics keep a future regression triage possible from CI logs.
      console.log(
        'OVERFLOW_REPORT',
        JSON.stringify(
          await page.evaluate(() => {
            const vw = document.documentElement.clientWidth
            return Array.from(document.querySelectorAll('*'))
              .map((e) => ({
                tag: e.tagName,
                cls: String(e.className).slice(0, 22),
                right: Math.round(e.getBoundingClientRect().right),
                t: (e.textContent ?? '').replace(/\s+/g, ' ').slice(0, 22),
              }))
              .filter((e) => e.right > vw + 0.5)
              .sort((a, b) => b.right - a.right)
              .slice(0, 8)
          }),
        ),
      )
    }
    expect(overflow, `${viewport.width}px overflows by ${overflow}px`).toBeLessThanOrEqual(0)

    // State is carried by WORDS, not colour: the status text itself names the
    // state and the approval buttons are labelled.
    await expect(page.getByTestId('run-status')).toContainText('等待主人确认')
    await expect(page.getByTestId('approve')).toBeVisible()
    await expect(page.getByTestId('decline')).toBeVisible()
    await page.screenshot({
      path: `test-results/acceptance-viewport-${viewport.width}.png`,
      fullPage: true,
    })

    await page.getByTestId('decline').click()
    await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  }
  // What this does NOT prove: every device/browser combination or long-text
  // robustness (e.g. judge-typed paragraph input). Two fixed widths only. The
  // assertion is DOCUMENT-level horizontal overflow; a container that clips its
  // own overflow (.truth-strip { overflow: hidden }) could hide an inner
  // spill from scrollWidth -- no such clipping is relied on here, but the
  // e2e wording is 「无文档级横向滚动」, not 「任何元素无溢出」.
})

test('raising the daily dispensed amount shifts the proposed grams', async ({ page }) => {
  test.setTimeout(120_000)
  await login(page)
  await resetDemo(page)

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('proposal-action')).toContainText('出粮 15 克')
  await page.getByTestId('decline').click()

  // The owner raises today's dispensed amount to 20 g: remaining quota is 10 g,
  // so the proposed serving drops from 15 g to 10 g (facts-derived, not constant).
  await openDemo(page)
  await page.getByTestId('fact-dispensed').fill('20')
  await page.getByTestId('apply-facts').click()
  await expect(page.getByTestId('facts')).toContainText('20 / 30 克')

  await page.getByRole('button', { name: '发送吃饭请求' }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await expect(page.getByTestId('proposal-action')).toContainText('出粮 10 克')
  await page.getByTestId('decline').click()
  // What this does NOT prove: real-model reasoning over the changed facts. The
  // grams come from the deterministic local stand-in deriving from facts; the
  // analyzer backend label still reads 本地替身（非真实模型）.
})

test('a new session rotates the conversation while memory stays honestly unretrieved', async ({
  page,
}) => {
  test.setTimeout(120_000)
  await login(page)

  const marker = `验收-仅今天-${Date.now()}`
  await page.getByTestId('feedback-text').fill(marker)
  await page.getByTestId('feedback-scope').selectOption('today_only')
  await page.getByTestId('submit-feedback').click()
  await expect(page.getByTestId('notice')).toContainText('不会成为永久偏好')

  const before = await page.getByTestId('memory-backend').textContent()
  await page.getByTestId('new-session').click()
  await expect(page.getByTestId('notice')).toContainText('已开启新会话')
  const after = await page.getByTestId('memory-backend').textContent()
  expect(after).not.toEqual(before) // conversation id rotated

  await expect(page.getByTestId('memory-backend')).toContainText('未实现（无 AWS 账号）')
  await expect(page.getByTestId('feedback-item').filter({ hasText: marker })).toBeVisible()
  const memoryText = await page.getByTestId('memory-area').textContent()
  expect(memoryText ?? '').not.toContain('已检索到记忆')
  expect(memoryText ?? '').not.toContain('可检索')
  // What this does NOT prove: cross-session AgentCore memory. The record visible
  // after rotation is the raw feedback row in the business DB; extraction and
  // retrieval remain condition items with no AWS account wired.
})
