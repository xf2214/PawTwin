// Local visual QA only: writes fictional fixtures to the dedicated :8834
// workspace-preview-2026-10-13.db. Never point this script at a user database.
const { chromium, expect } = require('../../../frontend/node_modules/@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const baseURL = 'http://127.0.0.1:8834';
const account = { username: 'workspace-preview-20261013', password: 'local-preview-password', display_name: '演示主人' };
const output = __dirname;

async function mutate(page, url, body, method = 'POST') {
  return page.evaluate(async ({ url, body, method }) => {
    const me = await (await fetch('/api/family/me')).json();
    const response = await fetch(url, { method, headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': me.csrf_token }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${url}: ${response.status} ${await response.text()}`);
    return response.json();
  }, { url, body, method });
}

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  const context = await browser.newContext({ baseURL, timezoneId: 'Asia/Shanghai', reducedMotion: 'reduce' });
  const page = await context.newPage();
  const checks = [];
  try {
    await page.goto('/#app/home');
    const existing = await page.request.post('/api/family/login', { data: { username: account.username, password: account.password } });
    if (existing.status() === 401) {
      await page.getByRole('button', { name: '创建本地账号', exact: true }).click();
      await page.getByLabel('账号名').fill(account.username);
      await page.getByLabel('密码', { exact: true }).fill(account.password);
      await page.getByLabel('昵称').fill(account.display_name);
      await page.getByRole('button', { name: '注册并登录', exact: true }).click();
      await page.getByLabel('家庭名称', { exact: true }).fill('PawTwin 虚构演示家庭');
      await page.getByRole('button', { name: '创建家庭', exact: true }).click();
      await expect(page.getByRole('navigation', { name: 'App 主导航' })).toBeVisible();
      const now = Date.now();
      // Explicit demo_sample, never invented owner/vet measurements.
      for (const [days, value] of [[7, 2.05], [0, 2.1]]) {
        await mutate(page, '/api/family/pets/mochi/measurements', { kind: 'weight', value, unit: 'kg', measured_at: new Date(now - days * 86400000).toISOString(), source: 'demo_sample', note: '虚构演示样本，仅供界面检查' });
      }
      await mutate(page, '/api/home/pets/mochi/notes', { text: '虚构演示：午后喜欢在窗边休息，陪玩时偏爱羽毛棒。', scope: 'observation', activity: 'play' });
      await mutate(page, '/api/home/pets/mochi/diary', { title: '虚构演示 · 窗边的一小段时光', text: '这些文字用于检查日记页面，不代表真实宠物健康资料。', happened_on: new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Shanghai' }) });
      for (const [kind, title, hours, interval_days] of [['water', '虚构演示 · 换一碗清水', -1, 1], ['play', '虚构演示 · 晚间陪玩', 4, null], ['brush', '虚构演示 · 整理毛发', 8, 3]]) {
        await mutate(page, '/api/home/pets/mochi/tasks', { kind, title, due_at: new Date(now + hours * 3600000).toISOString(), interval_days });
      }
    } else {
      if (!existing.ok()) throw new Error(`Preview login failed: ${existing.status()}`);
      await page.reload();
    }
    await expect(page.getByRole('navigation', { name: 'App 主导航' })).toBeVisible();
    await page.getByRole('button', { name: '同步最新记录', exact: true }).click();

    async function capture(name, width, fullPage = true) {
      if (fullPage) await page.evaluate(() => window.scrollTo(0, 0));
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const size = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
      if (size.document > size.viewport) throw new Error(`${name}: horizontal overflow ${JSON.stringify(size)}`);
      const file = `${name}-${width}.png`;
      await page.screenshot({ path: path.join(output, file), fullPage });
      checks.push({ file, width, ...size, fullPage, url: page.url() });
    }

    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const [hash, name] of [
        ['home', 'today'], ['care', 'care'], ['growth', 'growth'], ['assistant', 'twin'], ['family', 'family'],
      ]) {
        await page.goto(`/#app/${hash}`);
        await expect(page.getByRole('navigation', { name: 'App 主导航' })).toBeVisible();
        if (hash === 'home') await expect(page.locator('.ph-room')).toBeVisible();
        if (hash === 'growth') await expect(page.getByRole('heading', { name: '成长曲线', exact: true })).toBeVisible();
        // Read the rendered page, never inject visual-only content into its DOM.
        await capture(name, width);
      }
    }
    await page.setViewportSize({ width: 390, height: 850 });
    await page.goto('/#app/care');
    await expect(page.locator('.fa-task-card').first()).toBeVisible();
    await page.locator('.fa-task-card').first().evaluate(element => element.scrollIntoView({ block: 'center' }));
    await capture('care-scrolled-viewport', 390, false);
    await page.goto('/#app/home');
    await expect(page.locator('.ph-room')).toBeVisible();
    await page.locator('.ph-room').evaluate(element => element.scrollIntoView({ block: 'center' }));
    await capture('room-scrolled-viewport', 390, false);
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto('/#app/growth');
    const sections = page.getByRole('navigation', { name: '成长分区' });
    for (const [label, name] of [['实测与饮食', 'measurements'], ['日记与观察', 'diary'], ['报告', 'reports']]) {
      await sections.getByRole('button', { name: label, exact: true }).click();
      if (name === 'diary') await expect(page.getByLabel('记录原文', { exact: true })).toBeVisible();
      await capture(name, 1440);
    }
    await page.goto('/#app/home');
    await page.getByRole('button', { name: '编辑档案', exact: true }).click();
    await expect(page.getByLabel('名字 *', { exact: true })).toBeVisible();
    await capture('profile', 1440);
    // Legacy login is deliberately separate from the family account.
    await page.goto('/#workbench');
    await page.getByLabel('演示口令').fill('local-demo-passphrase');
    await page.getByRole('button', { name: '登录演示', exact: true }).click();
    await expect(page.getByTestId('facts')).toBeVisible();
    if (await page.getByTestId('decline').isVisible()) {
      await page.getByTestId('decline').click();
      await expect(page.getByTestId('run-status')).toHaveText('已拒绝');
    }
    await page.getByRole('button', { name: '发送吃饭请求', exact: true }).click();
    await expect(page.getByTestId('run-status')).toHaveText('等待主人确认', { timeout: 20000 });
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const [hash, name] of [['', 'requests'], ['/history', 'history'], ['/settings', 'settings']]) {
        await page.goto(`/#workbench${hash}`);
        await expect(page.getByTestId('facts')).toBeVisible();
        await capture(`workbench-${name}`, width);
      }
    }
    fs.writeFileSync(path.join(output, 'visual-checks.json'), JSON.stringify({ generated_at: new Date().toISOString(), database: 'data/workspace-preview-2026-10-13.db', fictional: true, measurements: 'demo_sample', checks }, null, 2));
    console.log(JSON.stringify({ screenshots: checks.length, widths: [320, 390, 768, 1440], horizontal_overflow: false }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
