import { expect, test, type Page } from '@playwright/test'
import { login, resetDemo } from './helpers'

// Only delay the transport for an actual stored run. This covers browser race
// handling; it is not evidence of slow real-model analysis or cloud connectivity.
async function delayedRun(page: Page) {
  let release!: () => void
  let reached!: () => void
  let finished!: () => void
  let first = true
  let runId = ''
  const gate = new Promise<void>(resolve => { release = resolve })
  const captured = new Promise<void>(resolve => { reached = resolve })
  const delivered = new Promise<void>(resolve => { finished = resolve })
  await page.route('**/api/runs/*', async route => {
    if (route.request().method() !== 'GET') { await route.continue(); return }
    const response = await route.fetch()
    const run = await response.json()
    if (first) {
      first = false
      runId = run.run_id
      await route.fulfill({ response, json: { ...run, state: 'analyzing', proposal: null, action_digest: null, receipt: null } })
      return
    }
    if (run.run_id !== runId) { await route.fulfill({ response }); return }
    reached()
    await gate
    try { await route.fulfill({ response }) } catch { /* Selection/logout aborts the old request. */ } finally { finished() }
  })
  return { captured, delivered, release, id: () => runId }
}

test('workbench navigation keeps demo settings and run decisions in their own pages', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 780 })
  await login(page)
  await resetDemo(page)
  const nav = page.getByRole('navigation', { name: '工作台导航' })
  await nav.getByRole('link', { name: '演示设置' }).click()
  await expect(page).toHaveURL(/#workbench\/settings$/)
  await page.getByTestId('fact-dispensed').fill('20')
  await page.getByTestId('apply-facts').click()
  await expect(page.getByTestId('facts')).toContainText('20 / 30 克')
  await page.getByTestId('reset-facts').click()
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  await nav.getByRole('link', { name: '请求与审批' }).click()
  await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await nav.getByRole('link', { name: '运行记录' }).click()
  await expect(page).toHaveURL(/#workbench\/history$/)
  await page.getByLabel('运行状态筛选').selectOption('awaiting_approval')
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  await page.getByLabel('运行状态筛选').selectOption('declined')
  await expect(page.getByTestId('runs')).toContainText('已拒绝')
  await expect(page.getByTestId('facts')).toContainText('0 / 30 克')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})

test('a pending run blocks duplicate requests while demo controls remain available and the next run is tracked', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  const delayed = await delayedRun(page)
  try {
    await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
    await delayed.captured
    await expect(page.getByTestId('run-status')).toHaveText('分析中')
    await expect(page.getByRole('button', { name: '发送吃饭请求', exact: true })).toBeDisabled()
    await expect(page.getByRole('button', { name: '发送互动请求', exact: true })).toBeDisabled()
    await expect(page.getByTestId('reset-facts')).toBeEnabled()
    await expect(page.getByTestId('device-mode')).toBeEnabled()
    delayed.release()
    await delayed.delivered
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
    await page.unroute('**/api/runs/*')
    await page.getByTestId('decline').click()
    await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
    await page.getByRole('button', { name: '发送互动请求', exact: true }).click()
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
    await expect(page.getByTestId('proposal-action')).toContainText('创建陪玩任务')
    await page.getByTestId('decline').click()
  } finally { delayed.release() }
})

test('choosing a history run and logging out invalidate delayed updates from the previously tracked run', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  const previous = await page.getByTestId('active-run-id').textContent()
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  const delayed = await delayedRun(page)
  try {
    await page.getByRole('button', { name: '发送互动请求', exact: true }).click()
    await delayed.captured
    await page.getByRole('navigation', { name: '工作台导航' }).getByRole('link', { name: '运行记录' }).click()
    await page.getByTestId('runs').locator(`[data-run-id="${previous?.trim()}"]`).click()
    await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
    delayed.release()
    await delayed.delivered
    await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))))
    await expect(page.getByTestId('active-run-id')).toHaveText(previous!)
    await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
    await page.unroute('**/api/runs/*')
    const afterLogout = await delayedRun(page)
    try {
      await page.getByTestId('runs').locator(`[data-run-id="${delayed.id()}"]`).click()
      await afterLogout.captured
      await page.getByRole('button', { name: '退出', exact: true }).click()
      await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
      let privateReads = 0
      page.on('request', request => { if (/\/api\/(state|runs\/)/.test(request.url()) && request.method() === 'GET') privateReads++ })
      afterLogout.release()
      await afterLogout.delivered
      await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))))
      expect(privateReads, 'an invalidated poll must not restart private reads after logout').toBe(0)
      await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
      await expect(page.getByTestId('run-status')).toHaveCount(0)
      await expect(page.getByTestId('facts')).toHaveCount(0)
    } finally { afterLogout.release() }
  } finally { delayed.release() }
})

test('a stalled run read reaches the client deadline without inventing failure and can be queried again', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  await page.clock.install()
  let release!: () => void
  let captured!: () => void
  let delivered!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  const reached = new Promise<void>(resolve => { captured = resolve })
  const finished = new Promise<void>(resolve => { delivered = resolve })
  await page.route('**/api/runs/*', async route => {
    if (route.request().method() !== 'GET') { await route.continue(); return }
    const response = await route.fetch()
    captured()
    await gate
    try { await route.fulfill({ response }) } catch { /* The client deadline aborts the stalled read. */ } finally { delivered() }
  })
  try {
    await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
    await reached
    const aborted = page.waitForEvent('requestfailed', request => request.method() === 'GET' && /\/api\/runs\//.test(request.url()))
    await page.clock.fastForward(76_000)
    await expect(page.getByTestId('poll-deadline')).toContainText('任务仍在后端处理')
    await aborted
    await expect(page.getByTestId('failure-reason')).toHaveCount(0)
    await expect(page.getByTestId('reset-facts')).toBeEnabled()
    release()
    await finished
    await page.unroute('**/api/runs/*')
    await page.getByRole('button', { name: '刷新状态', exact: true }).click()
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
    await expect(page.getByTestId('proposal-action')).toContainText('出粮 15 克')
    await expect(page.getByTestId('poll-deadline')).toHaveCount(0)
    await page.getByTestId('decline').click()
  } finally { release() }
})

test('a 401 invalidates the session before an older state response can reopen the workbench', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  await page.getByRole('button', { name: '发送互动请求', exact: true }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  let release!: () => void
  let delivered!: () => void
  let invalidated!: () => void
  let reads = 0
  const gate = new Promise<void>(resolve => { release = resolve })
  const finished = new Promise<void>(resolve => { delivered = resolve })
  const unauthorized = new Promise<void>(resolve => { invalidated = resolve })
  await page.route('**/api/state', async route => {
    reads++
    if (reads === 1) {
      const response = await route.fetch()
      await gate
      try { await route.fulfill({ response }) } catch { /* Invalidated reads cannot restore the session. */ } finally { delivered() }
    } else {
      await route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"UNAUTHENTICATED"}' })
      invalidated()
    }
  })
  try {
    // Refreshing the state and the selected run makes two independent reads;
    // hold the earlier success until the later refresh reports session expiry.
    await page.getByRole('button', { name: '刷新状态', exact: true }).click()
    await unauthorized
    await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
    const staleResponse = page.waitForResponse(response => response.url().endsWith('/api/state') && response.status() === 200)
    release()
    await finished
    await (await staleResponse).finished()
    await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))))
    await expect(page.getByRole('button', { name: '登录演示' })).toBeVisible()
    await expect(page.getByTestId('facts')).toHaveCount(0)
    await expect(page.getByTestId('run-status')).toHaveCount(0)
  } finally { release() }
})

test('an accepted request keeps history selection locked until its first real state read returns', async ({ page }) => {
  await login(page)
  await resetDemo(page)
  await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click()
  await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
  const previous = await page.getByTestId('active-run-id').textContent()
  await page.getByTestId('decline').click()
  await expect(page.getByTestId('run-status')).toHaveText('已拒绝')
  let release!: () => void
  let captured!: () => void
  let delivered!: () => void
  let first = true
  let posts = 0
  const gate = new Promise<void>(resolve => { release = resolve })
  const reached = new Promise<void>(resolve => { captured = resolve })
  const finished = new Promise<void>(resolve => { delivered = resolve })
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith('/api/events')) posts++ })
  await page.route('**/api/runs/*', async route => {
    if (route.request().method() !== 'GET' || !first) { await route.continue(); return }
    first = false
    const response = await route.fetch()
    captured()
    await gate
    try { await route.fulfill({ response }) } catch { /* A logout may invalidate this first read. */ } finally { delivered() }
  })
  try {
    await page.getByRole('button', { name: '发送互动请求', exact: true }).click()
    await reached
    const nav = page.getByRole('navigation', { name: '工作台导航' })
    await nav.getByRole('link', { name: '运行记录' }).click()
    await expect(page.getByTestId('runs').locator(`[data-run-id="${previous?.trim()}"]`)).toBeDisabled()
    await nav.getByRole('link', { name: '请求与审批' }).click()
    await expect(page.getByRole('button', { name: '发送吃饭请求', exact: true })).toBeDisabled()
    expect(posts, 'the accepted request must keep ownership before its first state response').toBe(1)
    release()
    await finished
    await page.unroute('**/api/runs/*')
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认')
    await expect(page.getByTestId('proposal-action')).toContainText('创建陪玩任务')
    await page.getByTestId('decline').click()
  } finally { release() }
})
