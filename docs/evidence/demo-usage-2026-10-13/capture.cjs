// Inspect the persisted demo records through the shipped UI. No record creation.
const { chromium, expect } = require('../../../frontend/node_modules/@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const output = __dirname;
const checks = [];

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    for (const identity of ['legacy', 'family']) {
      const context = await browser.newContext({ baseURL: 'http://127.0.0.1:8834', viewport: { width: 1440, height: 1000 }, timezoneId: 'Asia/Shanghai', reducedMotion: 'reduce' });
      const page = await context.newPage();
      if (identity === 'legacy') {
        await page.goto('/#workbench');
        await page.getByLabel('演示口令').fill('local-demo-passphrase');
        await page.getByRole('button', { name: '登录演示', exact: true }).click();
        await expect(page.getByTestId('facts')).toBeVisible();
        await page.locator('.as-header').getByRole('link', { name: /家庭应用/ }).click();
      } else {
        await page.goto('/#app/home');
        await page.getByLabel('账号名', { exact: true }).fill('workspace-preview-20261013');
        await page.getByLabel('密码', { exact: true }).fill('local-preview-password');
        await page.getByRole('button', { name: '登录账号', exact: true }).click();
      }
      const nav = page.getByRole('navigation', { name: 'App 主导航' });
      await expect(nav).toBeVisible();
      await nav.getByRole('button', { name: '今日', exact: true }).click();
      await expect(page.getByRole('region', { name: '今日概览' })).toContainText('今天已保存 3 次人工完成记录');
      await expect(page.locator('.ph-profile-card')).toContainText('中华田园猫（虚构演示）');
      await expect(page.locator('.ph-profile-card')).toContainText('羽毛棒');

      async function capture(name, width = 1440) {
        await page.evaluate(() => window.scrollTo(0, 0));
        const size = await page.evaluate(() => ({ document: document.documentElement.scrollWidth, viewport: innerWidth }));
        if (size.document > size.viewport) throw new Error(`${identity}/${name}: horizontal overflow`);
        const file = `${identity}-${name}-${width}.png`;
        await page.screenshot({ path: path.join(output, file), fullPage: true });
        checks.push({ identity, name, file, width, url: page.url(), ...size });
      }

      await capture('today');
      await page.getByRole('button', { name: '编辑档案', exact: true }).click();
      await expect(page.getByLabel('生日', { exact: true })).toHaveValue('2026-05-21');
      await expect(page.getByRole('combobox', { name: '性别', exact: true })).toHaveValue('male');
      await capture('profile');

      await nav.getByRole('button', { name: '照护', exact: true }).click();
      const queue = page.getByRole('region', { name: '照护队列' });
      await expect(queue).toContainText('下一次人工喂食 · 演示');
      await expect(queue).toContainText('领取人');
      await capture('care-pending');
      await page.getByRole('button', { name: '已完成', exact: true }).click();
      await expect(queue).toContainText('晨间换水 · 演示');
      await expect(queue).toContainText('羽毛棒陪玩 · 演示');
      await expect(queue).toContainText('本次梳毛 · 演示');
      await capture('care-completed');

      await nav.getByRole('button', { name: '成长', exact: true }).click();
      const sections = page.getByRole('navigation', { name: '成长分区' });
      const count = identity === 'legacy' ? 7 : 9;
      await expect(page.getByRole('img', { name: new RegExp(`体重曲线，${count} 次测量`) })).toBeVisible();
      await expect(page.getByRole('region', { name: '成长概览' })).toContainText('演示样本');
      await capture('growth');
      await sections.getByRole('button', { name: '实测与饮食', exact: true }).click();
      await expect(page.getByText('1.96 kg · 演示样本', { exact: true })).toBeVisible();
      await capture('measurements');
      await sections.getByRole('button', { name: '日记与观察', exact: true }).click();
      await expect(page.getByRole('heading', { name: '换水与羽毛棒 · 演示', exact: true })).toBeVisible();
      await capture('diary');
      await sections.getByRole('button', { name: '报告', exact: true }).click();
      const reports = page.getByRole('region', { name: '日报与周报' });
      await expect(reports).toContainText('人工照护完成 3 次');
      await expect(reports).toContainText('实际摄入：44 g');
      await expect(reports).toContainText('周报');
      await capture('reports');

      await nav.getByRole('button', { name: '分身', exact: true }).click();
      await expect(page.locator('.fa-twin-memory article.fa-record').filter({ hasText: '主人已确认' })).toHaveCount(3);
      await page.getByRole('button', { name: '询问分身', exact: true }).click();
      const reply = page.getByRole('article', { name: '分身回复' });
      await expect(reply).toContainText('羽毛棒');
      await expect(reply).toContainText('本地规则');
      await capture('confirmed-preferences');

      await page.setViewportSize({ width: 390, height: 850 });
      await capture('confirmed-preferences', 390);
      await nav.getByRole('button', { name: '成长', exact: true }).click();
      await sections.getByRole('button', { name: '概览', exact: true }).click();
      await expect(page.getByRole('img', { name: new RegExp(`体重曲线，${count} 次测量`) })).toBeVisible();
      await capture('growth', 390);
      await sections.getByRole('button', { name: '报告', exact: true }).click();
      await expect(reports).toContainText('人工照护完成 3 次');
      await capture('reports', 390);
      await nav.getByRole('button', { name: '照护', exact: true }).click();
      await expect(queue).toContainText('下一次人工喂食 · 演示');
      await capture('care-pending', 390);
      await page.reload();
      await expect(queue).toContainText('下一次人工喂食 · 演示');
      await context.close();
    }
    fs.writeFileSync(path.join(output, 'ui-verification.json'), JSON.stringify({ generated_at: new Date().toISOString(), screenshots: checks.length, checks }, null, 2));
    console.log(JSON.stringify({ identities: 2, screenshots: checks.length, persisted_after_refresh: true, horizontal_overflow: false }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
