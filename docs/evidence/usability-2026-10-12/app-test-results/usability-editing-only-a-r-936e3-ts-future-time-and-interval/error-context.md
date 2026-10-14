# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> editing only a recurring task title preserves its future time and interval
- Location: frontend\e2e\usability.spec.ts:38:1

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "2027-01-20T12:00:00Z"
Received: "2026-10-12T07:49:00+00:00"
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
        - heading "我们的日常" [level=1] [ref=e21]
      - generic [ref=e22]:
        - button "日常主人" [ref=e23] [cursor=pointer]
        - button "退出账号" [ref=e24] [cursor=pointer]
    - paragraph [ref=e25]: 本地独立账号 · 云认证未接通
    - status [ref=e26]: 已保存
    - generic [ref=e27]:
      - generic [ref=e28]:
        - text: 当前宠物
        - combobox "当前宠物" [ref=e29]:
          - option "Mochi" [selected]
      - generic [ref=e30]: 记录人：日常主人 · 家庭成员
      - button "同步最新记录" [ref=e31] [cursor=pointer]
    - generic [ref=e32]:
      - generic [ref=e33]:
        - heading "安排日常照护" [level=2] [ref=e34]
        - paragraph [ref=e35]: 由主人选择周期；人工喂食记录不触发设备。
        - generic [ref=e36]:
          - generic [ref=e37]:
            - text: 照护类型
            - combobox "照护类型" [ref=e38]:
              - option "人工喂食" [selected]
              - option "换水"
              - option "陪玩"
              - option "梳毛"
              - option "洗澡"
              - option "剪指甲"
              - option "清洁"
              - option "散步"
          - generic [ref=e39]:
            - text: 照护名称
            - textbox "照护名称" [ref=e40]
          - generic [ref=e41]:
            - text: 照护时间
            - textbox "照护时间" [ref=e42]: 2026-10-12T15:49
          - generic [ref=e43]:
            - text: 重复间隔（天）
            - spinbutton "重复间隔（天）" [ref=e44]
          - generic [ref=e45]:
            - text: 负责人
            - combobox "负责人" [ref=e46]:
              - option "未分配" [selected]
              - option "日常主人"
          - button "保存照护计划" [ref=e47] [cursor=pointer]
      - generic [ref=e48]:
        - heading "照护与交接" [level=2] [ref=e49]
        - article [ref=e50]:
          - heading "温柔梳毛" [level=3] [ref=e51]
          - paragraph [ref=e52]: 梳毛 · 待照护 · 2026/10/12 15:49:00
          - paragraph [ref=e53]: 负责人：未分配或原成员
          - generic [ref=e54]:
            - button "领取" [ref=e55] [cursor=pointer]
            - button "完成照护" [ref=e56] [cursor=pointer]
            - button "取消" [ref=e57] [cursor=pointer]
          - generic [ref=e58]:
            - generic [ref=e59]:
              - text: 转交给
              - combobox "转交给" [ref=e60]:
                - option "日常主人" [selected]
            - button "转交" [ref=e61] [cursor=pointer]
          - group [ref=e62]:
            - generic "编辑或延期" [ref=e63] [cursor=pointer]
            - generic [ref=e64]:
              - generic [ref=e65]:
                - text: 任务标题
                - textbox "任务标题" [ref=e66]: 温柔梳毛
              - generic [ref=e67]:
                - text: 新计划时间
                - textbox "新计划时间" [ref=e68]: 2026-10-12T15:49
              - generic [ref=e69]:
                - text: 新周期（天）
                - spinbutton "新周期（天）" [ref=e70]
              - button "保存任务编辑" [ref=e71] [cursor=pointer]
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
      - button "家庭" [ref=e81] [cursor=pointer]:
        - generic [aria-hidden] [ref=e82]: ♡
        - text: 家庭
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
> 50  |   expect(updated.due_at).toBe(original.due_at);
      |                          ^ Error: expect(received).toBe(expected) // Object.is equality
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
  100 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
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
```