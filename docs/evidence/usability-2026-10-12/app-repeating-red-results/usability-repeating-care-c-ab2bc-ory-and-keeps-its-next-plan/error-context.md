# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> repeating care completion stays visible in completed history and keeps its next plan
- Location: frontend\e2e\usability.spec.ts:54:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: '照护队列' })
Expected substring: "每日换水"
Received string:    "DAILY CARE照护与交接家庭时间 · 2026-10-12全部今天逾期我负责已完成Asia/Shanghai · 待办按计划时间排列；人工照护与模拟设备分开记录。这里暂时没有完成记录。可切换筛选，或安排下一件日常小事。"
Timeout: 20000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: '照护队列' }) with timeout 20000ms
  - waiting for getByRole('region', { name: '照护队列' })
    43 × locator resolved to <section aria-label="照护队列" class="fa-card fa-care-queue">…</section>
       - unexpected value "DAILY CARE照护与交接家庭时间 · 2026-10-12全部今天逾期我负责已完成Asia/Shanghai · 待办按计划时间排列；人工照护与模拟设备分开记录。这里暂时没有完成记录。可切换筛选，或安排下一件日常小事。"

```

```yaml
- region "照护队列":
  - paragraph: DAILY CARE
  - heading "照护与交接" [level=2]
  - text: 家庭时间 · 2026-10-12
  - button "全部"
  - button "今天"
  - button "逾期"
  - button "我负责"
  - button "已完成" [pressed]
  - paragraph: Asia/Shanghai · 待办按计划时间排列；人工照护与模拟设备分开记录。
  - strong: 这里暂时没有完成记录。
  - paragraph: 可切换筛选，或安排下一件日常小事。
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
  12  |   await page.getByLabel("家庭名称").fill("我们的日常");
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
> 63  |   await expect(queue).toContainText("每日换水");
      |                       ^ Error: expect(locator).toContainText(expected) failed
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
  113 |     if (!failed && route.request().method() === "GET") { failed = true; await route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } }); }
  114 |     else await route.continue();
  115 |   });
  116 |   await page.goto("/#app");
  117 |   await page.reload();
  118 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  119 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
  120 |   await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  121 |   await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  122 |   await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  123 |   await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  124 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
  125 | });
  126 | 
  127 | test("a late growth read cannot replace the selected pet data", async ({ page }) => {
  128 |   await start(page);
  129 |   const created = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  130 |   const luna = created.pets.find((p: { name: string }) => p.name === "Luna");
  131 |   await mutate(page, `/api/family/pets/${luna.id}/measurements`, { kind: "weight", value: 3, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "vet" });
  132 |   let release!: () => void;
  133 |   const gate = new Promise<void>(resolve => { release = resolve; });
  134 |   let reached!: () => void;
  135 |   const received = new Promise<void>(resolve => { reached = resolve; });
  136 |   await page.route("**/api/family/pets/mochi/measurements", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  137 |   await page.goto("/#app");
  138 |   await page.reload({ waitUntil: "domcontentloaded" });
  139 |   await received;
  140 |   try {
  141 |     await page.getByRole("button", { name: "成长", exact: true }).click();
  142 |     await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption(luna.id);
  143 |     await expect(page.getByRole("region", { name: "成长概览" })).toContainText("3 kg");
  144 |   } finally { release(); }
  145 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("兽医资料");
  146 |   await expect(page.getByRole("region", { name: "成长概览" })).not.toContainText("暂无称重");
  147 | });
  148 | 
  149 | test("constant and dense real measurements remain accessible and range-filtered", async ({ page }) => {
  150 |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  151 |   await start(page);
  152 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.5, unit: "kg", measured_at: "2026-06-01T12:00:00Z", source: "vet" });
  153 |   for (let day = 1; day <= 10; day++) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2, unit: "kg", measured_at: `2026-10-${String(day).padStart(2, "0")}T12:00:00Z`, source: "owner_measured" });
  154 |   await page.goto("/#app");
  155 |   await page.reload();
  156 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  157 |   await page.getByLabel("曲线时间范围").selectOption("30");
  158 |   const chart = page.getByRole("region", { name: "体重曲线与明细" });
  159 |   await chart.getByText("查看测量明细", { exact: true }).click();
  160 |   await expect(chart.getByRole("table", { name: "体重测量明细" }).getByRole("row")).toHaveCount(11);
  161 |   await expect(chart).not.toContainText("2026-06-01");
  162 |   await expect(chart.getByRole("img", { name: /主人实测体重曲线/ })).toBeVisible();
  163 |   expect(await chart.locator("svg circle").evaluateAll(elements => elements.every(el => Number.isFinite(Number(el.getAttribute("cy")))))).toBe(true);
```