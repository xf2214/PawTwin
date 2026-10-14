# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: platform.spec.ts >> visit HTML download is a self-contained escaped pet snapshot and printing uses it
- Location: frontend\e2e\platform.spec.ts:34:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: '导出就诊信息卡（诊断资料）', exact: true })

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - link "PawTwin 产品首页" [ref=e5] [cursor=pointer]:
      - /url: "#product"
      - text: PawTwin
      - generic [ref=e12]: 家庭应用
    - navigation "页面导航" [ref=e13]:
      - link "产品介绍" [ref=e14] [cursor=pointer]:
        - /url: "#product"
      - link "Alexa+ 模拟器" [ref=e15] [cursor=pointer]:
        - /url: "#alexa"
      - link "原工作台" [ref=e16] [cursor=pointer]:
        - /url: "#workbench"
        - text: 原工作台 ↗
  - main [ref=e17]:
    - generic [ref=e18]:
      - generic [ref=e19]:
        - paragraph [ref=e20]: PAWTWIN · HOME TOGETHER
        - heading "仅供测试的家庭名称" [level=1] [ref=e21]
      - generic [ref=e22]:
        - button "照护主人" [ref=e23] [cursor=pointer]
        - button "退出账号" [ref=e24] [cursor=pointer]
    - paragraph [ref=e25]: 本地独立账号 · 云认证未接通
    - generic [ref=e26]:
      - generic [ref=e27]:
        - text: 当前宠物
        - combobox "当前宠物" [ref=e28]:
          - option "Mochi" [selected]
          - option "其他宠物绝密资料"
      - generic [ref=e29]: 记录人：照护主人 · 家庭成员
      - button "同步最新记录" [ref=e30] [cursor=pointer]
    - region "成长概览" [ref=e31]:
      - paragraph [ref=e32]: GROWING, ONE RECORD AT A TIME
      - generic [ref=e33]:
        - generic [ref=e34]:
          - generic [ref=e35]: 最近实测体重
          - strong [ref=e36]: 9.99 kg
          - paragraph [ref=e37]: 2026/10/12 22:26 · 演示样本
        - generic [ref=e38]:
          - generic [ref=e39]: 与上一次实测比较
          - strong [ref=e40]: 资料不足
          - paragraph [ref=e41]: 至少需要两次不同时间的有效测量。
      - text: 仅比较实际保存的测量；体重变化不代表健康诊断。
    - generic [ref=e42]:
      - generic [ref=e43]:
        - heading "记录实测与饮食" [level=2] [ref=e44]
        - generic [ref=e45]:
          - generic [ref=e46]:
            - text: 记录类型
            - combobox "记录类型" [ref=e47]:
              - option "实测体重" [selected]
              - option "饮食事实"
          - generic [ref=e48]:
            - text: 测量数值
            - spinbutton "测量数值" [ref=e49]
          - generic [ref=e50]:
            - text: 单位
            - combobox "单位" [ref=e51]:
              - option "kg" [selected]
              - option "g"
          - generic [ref=e52]:
            - text: 测量时间
            - textbox "测量时间" [ref=e53]: 2026-10-12T23:26
          - generic [ref=e54]:
            - text: 资料来源
            - combobox "资料来源" [ref=e55]:
              - option "主人实测" [selected]
              - option "兽医资料"
              - option "演示样本"
          - generic [ref=e56]:
            - text: 备注
            - textbox "备注" [ref=e57]
          - paragraph [ref=e58]: 时间输入使用本机时区；记录按家庭时区 Asia/Shanghai 显示。
          - button "保存成长记录" [ref=e59] [cursor=pointer]
      - generic [ref=e60]:
        - heading "成长曲线" [level=2] [ref=e61]
        - region "体重曲线与明细" [ref=e62]:
          - generic [ref=e63]:
            - generic [ref=e64]: 2 次实际测量 · Asia/Shanghai
            - generic [ref=e65]:
              - text: 曲线时间范围
              - combobox "曲线时间范围" [ref=e66]:
                - option "全部记录" [selected]
                - option "最近 30 天"
                - option "最近 90 天"
          - figure "按实际测量时间绘制；连线用于阅读，不代表每日测量或健康诊断。纵轴范围随记录调整。" [ref=e67]:
            - img "主人实测体重曲线，2 次测量，未补填缺失日期" [ref=e68]:
              - generic [ref=e69]: "11.171"
              - generic [ref=e71]: "7.76"
              - generic [ref=e73]: "4.35"
              - generic [ref=e75]: "0.94"
              - generic [ref=e77]: kg
              - generic [ref=e78]:
                - generic "2026/10/12 22:26 · 2.12 kg · 主人实测" [ref=e79] [cursor=pointer]
                - generic [ref=e80]: 2.12 kg
              - generic [ref=e81]:
                - generic "2026/10/12 22:26 · 9.99 kg · 演示样本" [ref=e82] [cursor=pointer]
                - generic [ref=e83]: 9.99 kg
              - generic [ref=e84]: 2026-10-12
          - generic [ref=e86]:
            - text: 测量点详情
            - combobox "测量点详情" [ref=e87]:
              - option "2026/10/12 22:26 · 2.12 kg"
              - option "2026/10/12 22:26 · 9.99 kg" [selected]
          - generic [ref=e88]:
            - strong [ref=e89]: 9.99 kg
            - generic [ref=e90]: 2026/10/12 22:26 · 演示样本
          - group [ref=e91]:
            - generic "查看测量明细" [ref=e92] [cursor=pointer]
        - article [ref=e93]:
          - strong [ref=e94]: 2.12 kg · 主人实测
          - paragraph [ref=e95]: 2026/10/12 22:26 · 实测体重
          - generic [ref=e96]:
            - button "纠正记录" [ref=e97] [cursor=pointer]
            - button "删除记录" [ref=e98] [cursor=pointer]
        - article [ref=e99]:
          - strong [ref=e100]: 9.99 kg · 演示样本
          - paragraph [ref=e101]: 2026/10/12 22:26 · 实测体重
          - generic [ref=e102]:
            - button "纠正记录" [ref=e103] [cursor=pointer]
            - button "删除记录" [ref=e104] [cursor=pointer]
    - region "日报与周报" [ref=e105]:
      - generic [ref=e106]:
        - generic [ref=e107]:
          - paragraph [ref=e108]: A LOOK BACK
          - heading "日报与周报" [level=2] [ref=e109]
        - generic [ref=e110]:
          - text: 报告周期
          - combobox "报告周期" [ref=e111]:
            - option "全部周期" [selected]
            - option "日报"
            - option "周报"
      - generic [ref=e112]:
        - generic [ref=e113]:
          - text: 统计日期
          - textbox "统计日期" [ref=e114]: 2026-10-12
        - button "生成日报" [ref=e115] [cursor=pointer]
        - button "生成周报" [ref=e116] [cursor=pointer]
      - paragraph [ref=e117]: 按家庭时区 Asia/Shanghai 统计。服务运行时自动生成，重启后补跑；生成后尚未发送通知。
      - generic [ref=e118]:
        - strong [ref=e119]: 还没有这个周期的报告。
        - paragraph [ref=e120]: 已有记录会在报告中回顾；缺少资料时会如实说明。
    - button "照片日记与主人观察" [ref=e121] [cursor=pointer]
    - region "观察与日记管理" [ref=e122]:
      - heading "观察与日记管理" [level=2] [ref=e123]
      - paragraph [ref=e124]: 保留当时作者和修订历史；修改后的有效内容同步用于统计和分身。
      - article [ref=e125]:
        - strong [ref=e126]: 观察原文 <script>window.exportWasUnsafe=true</script>
        - paragraph [ref=e127]: 照护主人 · 一般观察
        - text: 2026/10/12 23:26
        - group [ref=e128]:
          - generic "纠正观察" [ref=e129] [cursor=pointer]
          - option "仅今天"
          - option "一般观察" [selected]
          - option "确认偏好"
    - navigation "App 主导航" [ref=e130]:
      - text: 你的宠物世界
      - button "小屋" [ref=e131] [cursor=pointer]:
        - generic [aria-hidden] [ref=e132]: ⌂
        - text: 小屋
      - button "照护" [ref=e133] [cursor=pointer]:
        - generic [aria-hidden] [ref=e134]: ✓
        - text: 照护
      - button "助手" [ref=e135] [cursor=pointer]:
        - generic [aria-hidden] [ref=e136]: ✦
        - text: 助手
      - button "成长" [active] [ref=e137] [cursor=pointer]:
        - generic [aria-hidden] [ref=e138]: ↗
        - text: 成长
      - button "家庭" [ref=e139] [cursor=pointer]:
        - generic [aria-hidden] [ref=e140]: ♡
        - text: 家庭
      - text: 小小的日常，慢慢的了解。
```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | import { readFile } from "node:fs/promises";
  3   | 
  4   | test.use({ timezoneId: "Asia/Shanghai" });
  5   | async function register(page: Page) {
  6   |   await page.goto("/#app");
  7   |   await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  8   |   await page.getByLabel("账号名").fill(`platform-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  9   |   await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  10  |   await page.getByLabel("昵称").fill("照护主人");
  11  |   await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  12  | }
  13  | async function start(page: Page) {
  14  |   await register(page);
  15  |   await page.getByLabel("家庭名称").fill("仅供测试的家庭名称");
  16  |   await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  17  |   await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
  18  | }
  19  | async function mutate(page: Page, path: string, body: object, method = "POST") {
  20  |   return page.evaluate(async ({ path, body, method }) => {
  21  |     const me = await (await fetch("/api/family/me")).json();
  22  |     const response = await fetch(path, { method, headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify(body) });
  23  |     if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  24  |     return response.json();
  25  |   }, { path, body, method });
  26  | }
  27  | async function openCard(page: Page) {
  28  |   await page.getByRole("button", { name: "成长", exact: true }).click();
> 29  |   await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
      |                                                                          ^ Error: locator.click: Test timeout of 30000ms exceeded.
  30  |   await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  31  |   await expect(page.getByRole("region", { name: "就诊信息卡快照" })).toBeVisible();
  32  | }
  33  | 
  34  | test("visit HTML download is a self-contained escaped pet snapshot and printing uses it", async ({ page, browser }) => {
  35  |   await start(page);
  36  |   const measured_at = new Date(Date.now() - 3600000).toISOString();
  37  |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2.12, unit: "kg", measured_at, source: "owner_measured" });
  38  |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 9.99, unit: "kg", measured_at, source: "demo_sample" });
  39  |   await mutate(page, "/api/home/pets/mochi/notes", { text: "观察原文 <script>window.exportWasUnsafe=true</script>", scope: "observation", activity: "general" });
  40  |   const created = await mutate(page, "/api/home/pets", { name: "其他宠物绝密资料", species: "dog" });
  41  |   const other = created.pets.find((pet: { name: string }) => pet.name === "其他宠物绝密资料");
  42  |   await mutate(page, `/api/home/pets/${other.id}/notes`, { text: "其他宠物不可导出", scope: "observation", activity: "general" });
  43  |   const me = await (await page.request.get("/api/family/me")).json();
  44  |   await openCard(page);
  45  |   const snapshot = page.getByRole("region", { name: "就诊信息卡快照" });
  46  |   await expect(snapshot).toContainText("2.12 kg");
  47  |   await expect(snapshot).not.toContainText("9.99");
  48  |   await page.evaluate(() => { window.print = () => { window.dispatchEvent(new Event("beforeprint")); }; window.addEventListener("beforeprint", () => document.body.dataset.cardPrintRequested = "yes"); });
  49  |   await page.getByRole("button", { name: "打印 / 另存为 PDF", exact: true }).click();
  50  |   await expect(page.locator("body")).toHaveAttribute("data-card-print-requested", "yes");
  51  |   const downloading = page.waitForEvent("download");
  52  |   await page.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  53  |   const download = await downloading;
  54  |   expect(download.suggestedFilename()).toMatch(/\.html$/);
  55  |   const html = await readFile((await download.path())!, "utf8");
  56  |   expect(html).toContain("2.12");
  57  |   expect(html).toContain("&lt;script&gt;");
  58  |   expect(html).not.toMatch(/<(script|iframe|link|img)\b/i);
  59  |   expect(html).not.toContain("其他宠物不可导出");
  60  |   expect(html).not.toContain(me.user.user_id);
  61  |   expect(html).not.toContain(me.household.household_id);
  62  |   const offline = await browser.newPage();
  63  |   try { await offline.setContent(html); await expect(offline.getByText("Mochi", { exact: true }).first()).toBeVisible(); expect(await offline.evaluate(() => "exportWasUnsafe" in window)).toBe(false); } finally { await offline.close(); }
  64  | });
  65  | 
  66  | test("an administrator grants one pet and a separate visitor reads and chats until revocation", async ({ page, browser, baseURL }) => {
  67  |   await start(page);
  68  |   await mutate(page, "/api/home/pets/mochi/notes", { text: "只喜欢蓝色小球", scope: "preference", activity: "play" });
  69  |   await mutate(page, "/api/home/pets/mochi/diary", { title: "私人日记不开放", text: "私人日记秘密", happened_on: new Date().toISOString().slice(0, 10) });
  70  |   await page.getByRole("button", { name: "家庭", exact: true }).click();
  71  |   await page.getByLabel("访问有效期").selectOption("24");
  72  |   await page.getByRole("button", { name: "授权照护者访问分身", exact: true }).click();
  73  |   const link = await page.getByLabel("新的只读访问链接").inputValue();
  74  |   expect(link).toContain("#pet-access=");
  75  |   const context = await browser.newContext({ baseURL });
  76  |   const visitor = await context.newPage();
  77  |   const familyRequests: string[] = [];
  78  |   visitor.on("request", request => { if (request.url().includes("/api/family/") || request.url().includes("/api/home/")) familyRequests.push(request.url()); });
  79  |   try {
  80  |     await visitor.goto(link);
  81  |     await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toBeVisible();
  82  |     await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toBeVisible();
  83  |     await expect(visitor.getByText("私人日记秘密", { exact: true })).toHaveCount(0);
  84  |     await expect(visitor.getByText("仅供测试的家庭名称", { exact: true })).toHaveCount(0);
  85  |     await visitor.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  86  |     await expect(visitor.getByRole("log", { name: "只读分身对话" })).toContainText("只喜欢蓝色小球");
  87  |     expect(familyRequests).toEqual([]);
  88  |     expect(await visitor.evaluate(() => Object.keys(localStorage).some(key => /access|token/i.test(key)))).toBe(false);
  89  |     await page.getByRole("button", { name: "撤销只读访问", exact: true }).click();
  90  |     await visitor.getByRole("button", { name: "刷新授权资料", exact: true }).click();
  91  |     await expect(visitor.getByRole("alert")).toContainText("失效");
  92  |     await expect(visitor.getByRole("log", { name: "只读分身对话" })).toHaveCount(0);
  93  |     await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toHaveCount(0);
  94  |   } finally { await context.close(); }
  95  | });
  96  | 
  97  | test("card download requires current household permission and cannot replace a frozen changed snapshot", async ({ page, browser, baseURL }) => {
  98  |   await start(page);
  99  |   const record = await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.4, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured" });
  100 |   await openCard(page);
  101 |   await mutate(page, `/api/family/pets/mochi/measurements/${record.id}`, { kind: "weight", value: 1.6, unit: "kg", measured_at: record.measured_at, source: "owner_measured", version: record.version }, "PUT");
  102 |   let downloads = 0;
  103 |   page.on("download", () => downloads++);
  104 |   await page.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  105 |   await expect(page.getByRole("alert")).toContainText("重新生成");
  106 |   expect(downloads).toBe(0);
  107 |   await page.getByRole("button", { name: "关闭信息卡", exact: true }).click();
  108 |   const invitation = await mutate(page, "/api/family/invitations", { role: "carer", expires_in_hours: 48, max_uses: 1 });
  109 |   const context = await browser.newContext({ baseURL, timezoneId: "Asia/Shanghai" });
  110 |   const carer = await context.newPage();
  111 |   try {
  112 |     await register(carer);
  113 |     await carer.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
  114 |     await carer.getByRole("button", { name: "加入家庭", exact: true }).click();
  115 |     await openCard(carer);
  116 |     const me = await (await carer.request.get("/api/family/me")).json();
  117 |     let deniedDownloads = 0;
  118 |     carer.on("download", () => deniedDownloads++);
  119 |     await mutate(page, `/api/family/members/${me.user.user_id}`, {}, "DELETE");
  120 |     await carer.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  121 |     await expect(carer.getByRole("alert")).toContainText(/权限|家庭|重新登录/);
  122 |     expect(deniedDownloads).toBe(0);
  123 |     await expect(carer.getByRole("region", { name: "就诊信息卡快照" })).toHaveCount(0);
  124 |   } finally { await context.close(); }
  125 | });
  126 | 
  127 | test("invalid access ignores an owner cookie and never restores family session data", async ({ page }) => {
  128 |   await start(page);
  129 |   const familyRequests: string[] = [];
```