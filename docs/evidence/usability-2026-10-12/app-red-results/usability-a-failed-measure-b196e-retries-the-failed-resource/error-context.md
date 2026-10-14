# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> a failed measurement read preserves reports and retries the failed resource
- Location: frontend\e2e\usability.spec.ts:89:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('成长记录暂时无法读取。', { exact: true })
Expected: visible
Timeout: 20000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('成长记录暂时无法读取。', { exact: true }) with timeout 20000ms
  - waiting for getByText('成长记录暂时无法读取。', { exact: true })

```

```yaml
- banner:
  - link "PawTwin 产品首页":
    - /url: "#product"
    - text: PawTwin 家庭应用
  - navigation "页面导航":
    - link "产品介绍":
      - /url: "#product"
    - link "Alexa+ 模拟器":
      - /url: "#alexa"
    - link "原工作台":
      - /url: "#workbench"
- main:
  - paragraph: PAWTWIN · HOME TOGETHER
  - heading "我们的日常" [level=1]
  - button "日常主人"
  - button "退出账号"
  - paragraph: 本地独立账号 · 云认证未接通
  - text: 当前宠物
  - combobox "当前宠物":
    - option "Mochi" [selected]
  - text: 记录人：日常主人 · 家庭成员
  - button "同步最新记录"
  - heading "记录实测与饮食" [level=2]
  - text: 记录类型
  - combobox "记录类型":
    - option "实测体重" [selected]
    - option "饮食事实"
  - text: 测量数值
  - spinbutton "测量数值"
  - text: 单位
  - combobox "单位":
    - option "kg" [selected]
    - option "g"
  - text: 测量时间
  - textbox "测量时间": 2026-10-12T15:51
  - text: 资料来源
  - combobox "资料来源":
    - option "主人实测" [selected]
    - option "兽医资料"
    - option "演示样本"
  - text: 备注
  - textbox "备注"
  - button "保存成长记录"
  - heading "成长曲线" [level=2]
  - paragraph: 还没有有效成长记录。
  - heading "日报与周报" [level=2]
  - text: 统计日期
  - textbox "统计日期": 2026-10-12
  - button "生成日报"
  - button "生成周报"
  - paragraph: 服务运行时自动生成，重启按持久化进度补跑；报告生成后尚未发送通知。
  - button "照片日记与主人观察"
  - region "观察与日记管理":
    - heading "观察与日记管理" [level=2]
    - paragraph: 保留当时作者和修订历史；修改后的有效内容同步用于统计和分身。
    - paragraph: 还没有观察或日记，可在小屋记录。
  - navigation "App 主导航":
    - text: 你的宠物世界
    - button "小屋"
    - button "照护"
    - button "助手"
    - button "成长"
    - button "家庭"
    - text: 小小的日常，慢慢的了解。
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
  54  | test("daily queue uses household day and keeps completed care out of active filters", async ({ page }) => {
  55  |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  56  |   await start(page, "Pacific/Honolulu");
  57  |   const me = await (await page.request.get("/api/family/me")).json();
  58  |   for (const task of [
  59  |     { title: "昨天换水", due_at: "2026-10-10T21:00:00Z" },
  60  |     { title: "今天陪玩", due_at: "2026-10-12T02:00:00Z", assigned_to: me.user.user_id },
  61  |     { title: "以后梳毛", due_at: "2026-10-13T20:00:00Z" },
  62  |     { title: "已做清洁", due_at: "2026-10-11T20:00:00Z" },
  63  |   ]) await mutate(page, "/api/home/pets/mochi/tasks", { kind: "play", ...task });
  64  |   const home = await (await page.request.get("/api/home/state")).json();
  65  |   const done = home.tasks.find((t: { title: string }) => t.title === "已做清洁");
  66  |   await mutate(page, `/api/home/tasks/${done.id}/action`, { action: "complete", version: done.version, event_id: crypto.randomUUID() });
  67  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  68  |   const overview = page.getByRole("region", { name: "今日概览" });
  69  |   await expect(overview).toContainText("2026-10-11");
  70  |   await overview.getByRole("button", { name: "查看照护" }).click();
  71  |   await page.getByRole("button", { name: "今天", exact: true }).click();
  72  |   const queue = page.getByRole("region", { name: "照护队列" });
  73  |   await expect(queue).toContainText("今天陪玩");
  74  |   await expect(queue).not.toContainText("以后梳毛");
  75  |   await expect(queue).not.toContainText("已做清洁");
  76  |   await page.getByRole("button", { name: "逾期", exact: true }).click();
  77  |   await expect(queue).toContainText("昨天换水");
  78  |   await expect(queue).not.toContainText("今天陪玩");
  79  |   await page.getByRole("button", { name: "我负责", exact: true }).click();
  80  |   await expect(queue).toContainText("今天陪玩");
  81  |   await expect(queue).not.toContainText("昨天换水");
  82  |   await page.getByRole("button", { name: "已完成", exact: true }).click();
  83  |   await expect(queue).toContainText("已做清洁");
  84  |   await page.getByRole("button", { name: "小屋", exact: true }).first().click();
  85  |   await page.getByRole("button", { name: "管理照护计划", exact: true }).click();
  86  |   await expect(page).toHaveURL(/#app\/care$/);
  87  | });
  88  | 
  89  | test("a failed measurement read preserves reports and retries the failed resource", async ({ page }) => {
  90  |   await start(page);
  91  |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.2, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "owner_measured" });
  92  |   await mutate(page, "/api/family/pets/mochi/reports/generate", { period: "weekly", date: "2026-10-02" });
  93  |   let failed = false;
  94  |   await page.route("**/api/family/pets/mochi/measurements", async route => {
  95  |     if (!failed && route.request().method() === "GET") { failed = true; await route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } }); }
  96  |     else await route.continue();
  97  |   });
  98  |   await page.goto("/#app");
  99  |   await page.reload();
  100 |   await page.getByRole("button", { name: "成长", exact: true }).click();
> 101 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
      |                                                                ^ Error: expect(locator).toBeVisible() failed
  102 |   await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  103 |   await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  104 |   await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  105 |   await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  106 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
  107 | });
  108 | 
  109 | test("a late growth read cannot replace the selected pet data", async ({ page }) => {
  110 |   await start(page);
  111 |   const created = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  112 |   const luna = created.pets.find((p: { name: string }) => p.name === "Luna");
  113 |   await mutate(page, `/api/family/pets/${luna.id}/measurements`, { kind: "weight", value: 3, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "vet" });
  114 |   let release!: () => void;
  115 |   const gate = new Promise<void>(resolve => { release = resolve; });
  116 |   let reached!: () => void;
  117 |   const received = new Promise<void>(resolve => { reached = resolve; });
  118 |   await page.route("**/api/family/pets/mochi/measurements", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  119 |   await page.goto("/#app");
  120 |   await page.reload({ waitUntil: "domcontentloaded" });
  121 |   await received;
  122 |   try {
  123 |     await page.getByRole("button", { name: "成长", exact: true }).click();
  124 |     await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption(luna.id);
  125 |     await expect(page.getByRole("region", { name: "成长概览" })).toContainText("3 kg");
  126 |   } finally { release(); }
  127 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("兽医资料");
  128 |   await expect(page.getByRole("region", { name: "成长概览" })).not.toContainText("暂无称重");
  129 | });
  130 | 
  131 | test("constant and dense real measurements remain accessible and range-filtered", async ({ page }) => {
  132 |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  133 |   await start(page);
  134 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.5, unit: "kg", measured_at: "2026-06-01T12:00:00Z", source: "vet" });
  135 |   for (let day = 1; day <= 10; day++) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2, unit: "kg", measured_at: `2026-10-${String(day).padStart(2, "0")}T12:00:00Z`, source: "owner_measured" });
  136 |   await page.goto("/#app");
  137 |   await page.reload();
  138 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  139 |   await page.getByLabel("曲线时间范围").selectOption("30");
  140 |   const chart = page.getByRole("region", { name: "体重曲线与明细" });
  141 |   await chart.getByText("查看测量明细", { exact: true }).click();
  142 |   await expect(chart.getByRole("table", { name: "体重测量明细" }).getByRole("row")).toHaveCount(11);
  143 |   await expect(chart).not.toContainText("2026-06-01");
  144 |   await expect(chart.getByRole("img", { name: /主人实测体重曲线/ })).toBeVisible();
  145 |   expect(await chart.locator("svg circle").evaluateAll(elements => elements.every(el => Number.isFinite(Number(el.getAttribute("cy")))))).toBe(true);
  146 |   await page.getByLabel("曲线时间范围").selectOption("all");
  147 |   await expect(chart.getByRole("table").getByRole("row")).toHaveCount(12);
  148 | });
  149 | 
  150 | for (const width of [320, 390, 1440]) {
  151 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  152 |     await page.setViewportSize({ width, height: 900 });
  153 |     await start(page);
  154 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  155 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  156 |       await page.keyboard.press("Enter");
  157 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  158 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  159 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  160 |     }
  161 |   });
  162 | }
  163 | 
```