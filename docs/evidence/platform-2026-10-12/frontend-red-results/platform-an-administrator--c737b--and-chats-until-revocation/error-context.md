# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: platform.spec.ts >> an administrator grants one pet and a separate visitor reads and chats until revocation
- Location: frontend\e2e\platform.spec.ts:66:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.selectOption: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel('访问有效期')

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
      - generic [ref=e29]: 记录人：照护主人 · 家庭成员
      - button "同步最新记录" [ref=e30] [cursor=pointer]
    - generic [ref=e31]:
      - generic [ref=e32]:
        - heading "个人设置" [level=2] [ref=e33]
        - generic [ref=e34]:
          - generic [ref=e35]:
            - text: 个人头像
            - combobox "个人头像" [ref=e36]:
              - option "🐾" [selected]
              - option "🐱"
              - option "🐶"
              - option "🌿"
              - option "⭐"
          - generic [ref=e37]:
            - text: 个人昵称
            - textbox "个人昵称" [ref=e38]: 照护主人
          - generic [ref=e39]:
            - text: 家庭称呼
            - combobox "家庭称呼" [ref=e40]
          - paragraph [ref=e41]: 称呼由你选择，权限由管理员授权。
          - button "保存个人设置" [ref=e42] [cursor=pointer]
        - heading "当前家人" [level=3] [ref=e43]
        - article [ref=e44]:
          - strong [ref=e45]: 🐾 照护主人 · 家庭成员
          - paragraph [ref=e46]: 管理员
          - generic [ref=e48]:
            - text: 成员权限
            - combobox "照护主人 的权限" [ref=e49]:
              - option "管理员" [selected]
              - option "照护成员"
              - option "访客"
        - button "退出家庭" [ref=e50] [cursor=pointer]
      - generic [ref=e51]:
        - heading "邀请与家庭交接" [level=2] [ref=e52]
        - group [ref=e53]:
          - generic "宠物资料管理" [ref=e54] [cursor=pointer]
        - generic [ref=e55]:
          - generic [ref=e56]:
            - text: 授予权限
            - combobox "授予权限" [ref=e57]:
              - option "照护成员" [selected]
              - option "访客"
              - option "管理员"
          - generic [ref=e58]:
            - text: 邀请有效小时
            - spinbutton "邀请有效小时" [ref=e59]: "48"
          - generic [ref=e60]:
            - text: 允许使用次数
            - spinbutton "允许使用次数" [ref=e61]: "1"
          - button "生成家庭邀请" [ref=e62] [cursor=pointer]
        - group [ref=e63]:
          - generic "家庭设置" [ref=e64] [cursor=pointer]
        - heading "最近家庭动态" [level=3] [ref=e65]
        - article [ref=e66]:
          - paragraph [ref=e67]: 照护主人 · 添加成长日记：私人日记不开放
          - text: 2026/10/12 23:26
        - article [ref=e68]:
          - paragraph [ref=e69]: 照护主人 · 记录主人观察：只喜欢蓝色小球
          - text: 2026/10/12 23:26
        - paragraph [ref=e70]: 模拟执行器回执仍在原工作台核验。
        - link "原工作台与证据入口" [ref=e71] [cursor=pointer]:
          - /url: "#workbench"
    - navigation "App 主导航" [ref=e72]:
      - text: 你的宠物世界
      - button "小屋" [ref=e73] [cursor=pointer]:
        - generic [aria-hidden] [ref=e74]: ⌂
        - text: 小屋
      - button "照护" [ref=e75] [cursor=pointer]:
        - generic [aria-hidden] [ref=e76]: ✓
        - text: 照护
      - button "助手" [ref=e77] [cursor=pointer]:
        - generic [aria-hidden] [ref=e78]: ✦
        - text: 助手
      - button "成长" [ref=e79] [cursor=pointer]:
        - generic [aria-hidden] [ref=e80]: ↗
        - text: 成长
      - button "家庭" [active] [ref=e81] [cursor=pointer]:
        - generic [aria-hidden] [ref=e82]: ♡
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
  29  |   await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
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
> 71  |   await page.getByLabel("访问有效期").selectOption("24");
      |                                  ^ Error: locator.selectOption: Test timeout of 30000ms exceeded.
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
  130 |   page.on("request", request => { if (request.url().includes("/api/family/me")) familyRequests.push(request.url()); });
  131 |   await page.goto("/#pet-access=invalid-bearer-secret-for-test");
  132 |   await expect(page.getByRole("alert")).toContainText(/无效|失效/);
  133 |   expect(familyRequests).toEqual([]);
  134 |   await expect(page.getByRole("navigation", { name: "App 主导航" })).toHaveCount(0);
  135 | });
  136 | 
  137 | for (const width of [320, 390, 1440]) {
  138 |   test(`visit preview and grant controls stay readable at ${width}px`, async ({ page }, info) => {
  139 |     await page.setViewportSize({ width, height: 900 });
  140 |     await start(page);
  141 |     await openCard(page);
  142 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  143 |     await page.screenshot({ path: info.outputPath(`visit-${width}.png`), fullPage: true });
  144 |     await page.getByRole("button", { name: "关闭信息卡", exact: true }).focus();
  145 |     await page.keyboard.press("Enter");
  146 |     await page.getByRole("button", { name: "家庭", exact: true }).click();
  147 |     await expect(page.getByRole("button", { name: "授权照护者访问分身", exact: true })).toBeVisible();
  148 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  149 |   });
  150 | }
  151 | 
```