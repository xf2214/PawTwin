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
- link "跳到产品内容":
  - /url: "#product-content"
- banner:
  - link "PawTwin 产品首页":
    - /url: "#product"
    - text: PawTwin
  - navigation "产品导航":
    - link "产品体验":
      - /url: "#features"
    - link "如何使用":
      - /url: "#care"
    - link "日常案例":
      - /url: "#cases"
    - link "进入应用":
      - /url: "#app"
- button "暂停动画"
- main:
  - paragraph: PawTwin · 一起，好好照顾。
  - heading "它的每一天， 值得被好好记住。" [level=1]
  - paragraph: 一个属于它的小屋。 让全家的照顾、成长的瞬间，和一点点了解，在这里相遇。
  - link "进入应用":
    - /url: "#app"
  - link "了解产品":
    - /url: "#features"
  - text: PawTwin Mochi 的小屋
  - complementary:
    - strong: Mochi
    - text: 属于它的小小世界 ⌂ 小屋 ♡ 照护 ✦ 分身 ↗ 成长
  - img "俯视的宠物小屋，中央是正面造型的橘猫": 陪伴的角落 照护区
  - text: 每一个小日常，都值得留下。 产品界面示意
  - paragraph: PawTwin
  - heading "小小的它。 独一无二的日常。" [level=3]
  - text: 档案与偏好 ⌂ 一起照顾 ♡ 成长故事 ↗ 产品界面示意
  - paragraph: 本地体验已开放 从猫和狗的日常照护开始
  - region "小小一间屋。 装下大大的陪伴。":
    - paragraph: 它的世界，从这里开始。
    - heading "小小一间屋。 装下大大的陪伴。" [level=2]
    - paragraph: 喜欢的玩具，熟悉的窝，今天的小故事。 把关于它的点点滴滴，放回属于它的地方。
    - text: 它的习惯 你的记录 全家的关心
    - paragraph: 像素宠物形象示意 · 可在应用中建立自己的宠物档案
  - paragraph: 彼此连接的四种体验。
  - heading "从一只宠物，到一个家。" [level=2]
  - paragraph: 让记录有归处，让照护有回应。
  - group "查看产品体验":
    - button "宠物小屋" [pressed]
    - button "家庭照护"
    - button "成长记录"
    - button "宠物分身"
  - text: PawTwin Mochi 的小屋
  - complementary:
    - strong: Mochi
    - text: ⌂ 小屋 ♡ 照护 ✦ 分身 ↗ 成长
  - img "俯视的宠物小屋，中央是正面造型的橘猫": 陪伴的角落 照护区
  - text: 每一个小日常，都值得留下。 产品界面示意
  - paragraph: 每只宠物都有自己的记录与偏好
  - text: 产品界面示意 · 功能以应用内实际状态为准 01 / 宠物小屋
  - heading "给每个小家伙，一个自己的家。" [level=3]
  - paragraph: 一张档案，一间小屋。把它喜欢的玩具、常睡的窝和你确认的偏好放在一起，让照护从了解它开始。
  - text: ✓独立宠物档案 ✓像素小屋 ✓照片日记
  - link "在应用中体验":
    - /url: "#app"
  - region "把功能，放进日常。":
    - paragraph: 三个场景，一起看看。
    - heading "把功能，放进日常。" [level=2]
    - paragraph: 不是功能清单，是你和它的一天。
    - group "选择日常案例":
      - button "家庭交接" [pressed]
      - button "成长回顾"
      - button "偏好接续"
    - text: 情景示意 步骤 1 / 3
    - heading "换一碗新鲜的水" [level=3]
    - text: 待领取
    - paragraph: 主人创建一项人工照护事项，等待家人接手。
    - text: 虚构情景演示 · 不会创建真实照护任务 案例 01 / 家庭交接
    - heading "你出门了，照顾还在继续。" [level=3]
    - paragraph: 出门前为 Mochi 安排换水。家人接手后，在实际完成时留下记录，彼此不用反复确认。
    - group "查看案例步骤":
      - button "01 主人安排" [pressed]:
        - text: "01"
        - strong: 主人安排
      - button "02 家人接手":
        - text: "02"
        - strong: 家人接手
      - button "03 完成并回写":
        - text: "03"
        - strong: 完成并回写
    - paragraph: 主人创建一项人工照护事项，等待家人接手。
    - paragraph: 任务的每一次交接，都有清楚的去向。
    - link "在应用中开始":
      - /url: "#app"
  - paragraph: 每一份了解，都有来处。
  - heading "记住它。 也记住为什么。" [level=2]
  - paragraph: 档案、实测成长和你确认的偏好，串起它的日常。 留下来源，保留空白，让每一次回顾都有依据。
  - link "探索成长记录":
    - /url: "#features"
  - text: "01"
  - heading "实测成长" [level=3]
  - paragraph: 来自你记录的测量与时间
  - text: "02"
  - heading "确认偏好" [level=3]
  - paragraph: 由主人确认，可修改与删除
  - text: "03"
  - heading "照护记录" [level=3]
  - paragraph: 实际完成之后，才留下记录
  - text: 记录结构示意 · 非真实宠物数据
  - paragraph: 从今天的一件小事开始。
  - heading "让关心，变成有回应的日常。" [level=2]
  - paragraph: 认识它，一起安排，接手照顾，再回看成长。
  - article:
    - text: "01"
    - heading "认识它" [level=3]
    - paragraph: 创建宠物档案，记录它的习惯与偏好。
  - article:
    - text: "02"
    - heading "一起安排" [level=3]
    - paragraph: 邀请家人，安排需要完成的照护事项。
  - article:
    - text: "03"
    - heading "接手照顾" [level=3]
    - paragraph: 领取任务，在实际完成后留下记录。
  - article:
    - text: "04"
    - heading "回看成长" [level=3]
    - paragraph: 在日记与报告里，看见点滴变化。
  - paragraph: PawTwin
  - heading "一起照顾。 也一起记得。" [level=2]
  - paragraph: 为它，也为每一个关心它的人。
  - link "建立我的宠物小屋":
    - /url: "#app"
- contentinfo:
  - link "PawTwin":
    - /url: "#product"
  - text: 给日常一点记忆，给陪伴更多了解。
  - link "照护工作台":
    - /url: "#workbench"
  - paragraph: 家庭身份与记录仍为本地服务；实际回答后端与依据见每轮回复，Alexa 为网页模拟。PawLink 项圈为概念，设备执行为模拟，云端能力尚未验证。
  - paragraph:
    - text: PawTwin · 每只宠物，各有不同。
    - link "进入家庭应用":
      - /url: "#app"
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
  98  |   await page.goto("/#app/growth");
  99  |   await page.reload();
> 100 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
      |                                                                ^ Error: expect(locator).toBeVisible() failed
  101 |   await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  102 |   await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  103 |   await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  104 |   await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  105 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
  106 | });
  107 | 
  108 | test("a late growth read cannot replace the selected pet data", async ({ page }) => {
  109 |   await start(page);
  110 |   const created = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  111 |   const luna = created.pets.find((p: { name: string }) => p.name === "Luna");
  112 |   await mutate(page, `/api/family/pets/${luna.id}/measurements`, { kind: "weight", value: 3, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "vet" });
  113 |   let release!: () => void;
  114 |   const gate = new Promise<void>(resolve => { release = resolve; });
  115 |   let reached!: () => void;
  116 |   const received = new Promise<void>(resolve => { reached = resolve; });
  117 |   await page.route("**/api/family/pets/mochi/measurements", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  118 |   await page.goto("/#app/growth");
  119 |   await page.reload({ waitUntil: "domcontentloaded" });
  120 |   await received;
  121 |   try {
  122 |     await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption(luna.id);
  123 |     await expect(page.getByRole("region", { name: "成长概览" })).toContainText("3 kg");
  124 |   } finally { release(); }
  125 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("兽医资料");
  126 |   await expect(page.getByRole("region", { name: "成长概览" })).not.toContainText("暂无称重");
  127 | });
  128 | 
  129 | test("constant and dense real measurements remain accessible and range-filtered", async ({ page }) => {
  130 |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  131 |   await start(page);
  132 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.5, unit: "kg", measured_at: "2026-06-01T12:00:00Z", source: "vet" });
  133 |   for (let day = 1; day <= 10; day++) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2, unit: "kg", measured_at: `2026-10-${String(day).padStart(2, "0")}T12:00:00Z`, source: "owner_measured" });
  134 |   await page.goto("/#app/growth");
  135 |   await page.reload();
  136 |   await page.getByLabel("曲线时间范围").selectOption("30");
  137 |   const chart = page.getByRole("region", { name: "体重曲线与明细" });
  138 |   await chart.getByText("查看测量明细", { exact: true }).click();
  139 |   await expect(chart.getByRole("table", { name: "体重测量明细" }).getByRole("row")).toHaveCount(11);
  140 |   await expect(chart).not.toContainText("2026-06-01");
  141 |   await expect(chart.getByRole("img", { name: /主人实测体重曲线/ })).toBeVisible();
  142 |   expect(await chart.locator("svg circle").evaluateAll(elements => elements.every(el => Number.isFinite(Number(el.getAttribute("cy")))))).toBe(true);
  143 |   await page.getByLabel("曲线时间范围").selectOption("all");
  144 |   await expect(chart.getByRole("table").getByRole("row")).toHaveCount(12);
  145 | });
  146 | 
  147 | for (const width of [320, 390, 1440]) {
  148 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  149 |     await page.setViewportSize({ width, height: 900 });
  150 |     await start(page);
  151 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  152 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  153 |       await page.keyboard.press("Enter");
  154 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  155 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  156 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  157 |     }
  158 |   });
  159 | }
  160 | 
```