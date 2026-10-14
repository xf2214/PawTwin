# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> daily application at 1440px stays readable and keyboard accessible
- Location: e2e\usability.spec.ts:256:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel('家庭名称')

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
    - paragraph [ref=e18]: PAWTWIN · HOME TOGETHER
    - heading "欢迎回到你们的小屋。" [level=1] [ref=e19]
    - paragraph [ref=e20]: 登录后查看宠物近况、接手照护，或记下今天的新变化。
    - generic [ref=e21]:
      - heading "创建本地账号" [level=2] [ref=e22]
      - generic [ref=e23]:
        - generic [ref=e24]:
          - text: 账号名
          - textbox "账号名" [ref=e25]: daily-1791820226845-37769
        - generic [ref=e26]:
          - text: 密码
          - textbox "密码" [ref=e27]: browser-test-password
        - generic [ref=e28]:
          - text: 昵称
          - textbox "昵称" [ref=e29]: 日常主人
        - button "注册并登录" [ref=e30] [cursor=pointer]
      - button "已有账号，去登录" [ref=e31] [cursor=pointer]
      - paragraph [ref=e32]: 本地独立账号 · 云认证未接通
      - link "原工作台 / 演示登录" [ref=e33] [cursor=pointer]:
        - /url: "#workbench"
    - alert [ref=e34]: RATE_LIMITED
```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | 
  3   | test.use({ timezoneId: "Asia/Shanghai" });
  4   | 
  5   | async function start(page: Page, timezone = "Asia/Shanghai", path = "/#app") {
  6   |   await page.goto(path);
  7   |   await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  8   |   await page.getByLabel("账号名").fill(`daily-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  9   |   await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  10  |   await page.getByLabel("昵称").fill("日常主人");
  11  |   await page.getByRole("button", { name: "注册并登录", exact: true }).click();
> 12  |   await page.getByLabel("家庭名称").fill("我们的日常");
      |                                 ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  13  |   await page.getByLabel("家庭时区", { exact: true }).fill(timezone);
  14  |   await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  15  |   await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
  16  | }
  17  | 
  18  | async function mutate(page: Page, path: string, body: object, method = "POST") {
  19  |   return page.evaluate(async ({ path, body, method }) => {
  20  |     const me = await (await fetch("/api/family/me")).json();
  21  |     const response = await fetch(path, { method, headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify(body) });
  22  |     if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  23  |     return response.json();
  24  |   }, { path, body, method });
  25  | }
  26  | 
  27  | test("growth deep link survives signup, refresh and browser navigation", async ({ page }) => {
  28  |   await start(page, "Asia/Shanghai", "/#app/growth");
  29  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  30  |   await page.reload();
  31  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  32  |   await page.getByRole("button", { name: "照护", exact: true }).click();
  33  |   await expect(page).toHaveURL(/#app\/care$/);
  34  |   await page.goBack();
  35  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  36  | });
  37  | 
  38  | test("editing only a recurring task title preserves its future time and interval", async ({ page }) => {
  39  |   await start(page);
  40  |   await page.getByRole("button", { name: "照护", exact: true }).click();
  41  |   const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "brush", title: "每周梳毛", due_at: "2027-01-20T12:00:00+00:00", interval_days: 7 });
  42  |   const original = created.tasks.find((t: { title: string }) => t.title === "每周梳毛");
  43  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  44  |   const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "每周梳毛", exact: true }) });
  45  |   await card.getByText("编辑或延期", { exact: true }).click();
  46  |   await card.getByLabel("任务标题").fill("温柔梳毛");
  47  |   await card.getByRole("button", { name: "保存任务编辑" }).click();
  48  |   await expect(page.getByRole("heading", { name: "温柔梳毛", exact: true })).toBeVisible();
  49  |   const updated = (await (await page.request.get("/api/home/state")).json()).tasks.find((t: { id: string }) => t.id === original.id);
  50  |   expect(updated.due_at).toBe(original.due_at);
  51  |   expect(updated.interval_days).toBe(7);
  52  | });
  53  | 
  54  | test("repeating care completion stays visible in completed history and keeps its next plan", async ({ page }) => {
  55  |   await start(page);
  56  |   const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "water", title: "每日换水", due_at: "2026-10-01T12:00:00Z", interval_days: 1 });
  57  |   const task = created.tasks.find((item: { title: string }) => item.title === "每日换水");
  58  |   await mutate(page, `/api/home/tasks/${task.id}/action`, { action: "complete", version: task.version, event_id: crypto.randomUUID() });
  59  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  60  |   await page.getByRole("button", { name: "照护", exact: true }).click();
  61  |   await page.getByRole("button", { name: "已完成", exact: true }).click();
  62  |   const queue = page.getByRole("region", { name: "照护队列" });
  63  |   await expect(queue).toContainText("每日换水");
  64  |   await expect(queue).toContainText("本次已完成");
  65  |   await expect(queue).toContainText("下次待办");
  66  |   await expect(queue.getByRole("button", { name: "完成照护", exact: true })).toHaveCount(0);
  67  |   const updated = (await (await page.request.get("/api/home/state")).json()).tasks.find((item: { id: string }) => item.id === task.id);
  68  |   expect(updated.completed).toBe(false);
  69  |   expect(updated.interval_days).toBe(1);
  70  | });
  71  | 
  72  | test("daily queue uses household day and keeps completed care out of active filters", async ({ page }) => {
  73  |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  74  |   await start(page, "Pacific/Honolulu");
  75  |   const me = await (await page.request.get("/api/family/me")).json();
  76  |   for (const task of [
  77  |     { title: "昨天换水", due_at: "2026-10-10T21:00:00Z" },
  78  |     { title: "今天陪玩", due_at: "2026-10-12T02:00:00Z", assigned_to: me.user.user_id },
  79  |     { title: "以后梳毛", due_at: "2026-10-13T20:00:00Z" },
  80  |     { title: "已做清洁", due_at: "2026-10-11T20:00:00Z" },
  81  |   ]) await mutate(page, "/api/home/pets/mochi/tasks", { kind: "play", ...task });
  82  |   const home = await (await page.request.get("/api/home/state")).json();
  83  |   const done = home.tasks.find((t: { title: string }) => t.title === "已做清洁");
  84  |   await mutate(page, `/api/home/tasks/${done.id}/action`, { action: "complete", version: done.version, event_id: crypto.randomUUID() });
  85  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  86  |   const overview = page.getByRole("region", { name: "今日概览" });
  87  |   await expect(overview).toContainText("2026-10-11");
  88  |   await overview.getByRole("button", { name: "查看照护" }).click();
  89  |   await page.getByRole("button", { name: "今天", exact: true }).click();
  90  |   const queue = page.getByRole("region", { name: "照护队列" });
  91  |   await expect(queue).toContainText("今天陪玩");
  92  |   await expect(queue).not.toContainText("以后梳毛");
  93  |   await expect(queue).not.toContainText("已做清洁");
  94  |   await page.getByRole("button", { name: "逾期", exact: true }).click();
  95  |   await expect(queue).toContainText("昨天换水");
  96  |   await expect(queue).not.toContainText("今天陪玩");
  97  |   await page.getByRole("button", { name: "我负责", exact: true }).click();
  98  |   await expect(queue).toContainText("今天陪玩");
  99  |   await expect(queue).not.toContainText("昨天换水");
  100 |   await page.getByRole("button", { name: "已完成", exact: true }).click();
  101 |   await expect(queue).toContainText("已做清洁");
  102 |   await page.getByRole("button", { name: "小屋", exact: true }).first().click();
  103 |   await page.getByRole("button", { name: "管理照护计划", exact: true }).click();
  104 |   await expect(page).toHaveURL(/#app\/care$/);
  105 | });
  106 | 
  107 | test("a failed measurement read preserves reports and retries the failed resource", async ({ page }) => {
  108 |   await start(page);
  109 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.2, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "owner_measured" });
  110 |   await mutate(page, "/api/family/pets/mochi/reports/generate", { period: "weekly", date: "2026-10-02" });
  111 |   let failed = false;
  112 |   await page.route("**/api/family/pets/mochi/measurements", async route => {
```