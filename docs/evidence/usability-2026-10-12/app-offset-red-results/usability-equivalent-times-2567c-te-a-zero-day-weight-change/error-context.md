# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> equivalent timestamp offsets do not fabricate a zero-day weight change
- Location: frontend\e2e\usability.spec.ts:168:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: '成长概览' })
Expected substring: "资料不足"
Received string:    "GROWING, ONE RECORD AT A TIME最近实测体重2 kg2026/10/1 12:00 · 主人实测与上一次实测比较+1000 g100% · 实际跨度 0 天仅比较实际保存的测量；体重变化不代表健康诊断。"
Timeout: 20000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: '成长概览' }) with timeout 20000ms
  - waiting for getByRole('region', { name: '成长概览' })
    43 × locator resolved to <section aria-label="成长概览" class="fa-growth-overview">…</section>
       - unexpected value "GROWING, ONE RECORD AT A TIME最近实测体重2 kg2026/10/1 12:00 · 主人实测与上一次实测比较+1000 g100% · 实际跨度 0 天仅比较实际保存的测量；体重变化不代表健康诊断。"

```

```yaml
- region "成长概览":
  - paragraph: GROWING, ONE RECORD AT A TIME
  - text: 最近实测体重
  - strong: 2 kg
  - paragraph: 2026/10/1 12:00 · 主人实测
  - text: 与上一次实测比较
  - strong: +1000 g
  - paragraph: 100% · 实际跨度 0 天
  - text: 仅比较实际保存的测量；体重变化不代表健康诊断。
```

# Test source

```ts
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
  164 |   await page.getByLabel("曲线时间范围").selectOption("all");
  165 |   await expect(chart.getByRole("table").getByRole("row")).toHaveCount(12);
  166 | });
  167 | 
  168 | test("equivalent timestamp offsets do not fabricate a zero-day weight change", async ({ page }) => {
  169 |   await start(page);
  170 |   for (const record of [
  171 |     { value: 1, measured_at: "2026-10-01T12:00:00+08:00" },
  172 |     { value: 2, measured_at: "2026-10-01T04:00:00Z" },
  173 |   ]) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", ...record });
  174 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  175 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  176 |   const overview = page.getByRole("region", { name: "成长概览" });
> 177 |   await expect(overview).toContainText("资料不足");
      |                          ^ Error: expect(locator).toContainText(expected) failed
  178 |   await expect(overview).not.toContainText("实际跨度 0 天");
  179 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 1.5, measured_at: "2026-09-30T04:00:00Z" });
  180 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  181 |   await expect(overview).toContainText("500 g");
  182 |   await expect(overview).toContainText("实际跨度 1 天");
  183 | });
  184 | 
  185 | for (const width of [320, 390, 1440]) {
  186 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  187 |     await page.setViewportSize({ width, height: 900 });
  188 |     await start(page);
  189 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  190 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  191 |       await page.keyboard.press("Enter");
  192 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  193 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  194 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  195 |     }
  196 |   });
  197 | }
  198 | 
```