# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> care started from a toy preserves the intended play type
- Location: frontend\e2e\usability.spec.ts:186:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toHaveValue(expected) failed

Locator: getByLabel('照护类型', { exact: true })
Expected: "play"
Error: element(s) not found

Call log:
  - Expect "toHaveValue" getByLabel('照护类型', { exact: true }) with timeout 20000ms
  - waiting for getByLabel('照护类型', { exact: true })
  - Test timeout of 30000ms exceeded.

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
  - status: 已保存
  - text: 当前宠物
  - combobox "当前宠物":
    - option "Mochi" [selected]
  - text: 记录人：日常主人 · 家庭成员
  - button "同步最新记录"
  - region "照护队列":
    - paragraph: DAILY CARE
    - heading "照护与交接" [level=2]
    - text: 家庭时间 · 2026-10-12
    - button "全部" [pressed]
    - button "今天"
    - button "逾期"
    - button "我负责"
    - button "已完成"
    - paragraph: Asia/Shanghai · 待办按计划时间排列；人工照护与模拟设备分开记录。
    - strong: 还没有照护计划。
    - paragraph: 可切换筛选，或安排下一件日常小事。
  - group: ＋ 安排日常照护
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
  177 |   await expect(overview).toContainText("资料不足");
  178 |   await expect(overview).not.toContainText("实际跨度 0 天");
  179 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 1.5, measured_at: "2026-09-30T04:00:00Z" });
  180 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  181 |   await expect(overview).toContainText("500 g");
  182 |   await expect(overview).toContainText("实际跨度 1 天");
  183 | });
  184 | 
  185 | for (const [kind, care] of [["toy", "play"], ["water", "water"], ["nest", "clean"]]) {
  186 |   test(`care started from a ${kind} preserves the intended ${care} type`, async ({ page }) => {
  187 |     await start(page);
  188 |     await mutate(page, "/api/home/pets/mochi/objects", { kind, name: "专属生活物品" });
  189 |     await page.getByRole("button", { name: "同步最新记录" }).click();
  190 |     await page.getByRole("button", { name: "查看专属生活物品", exact: true }).click();
  191 |     await page.getByRole("button", { name: "安排相关照护", exact: true }).click();
  192 |     await expect(page).toHaveURL(/#app\/care$/);
> 193 |     await expect(page.getByLabel("照护类型", { exact: true })).toHaveValue(care);
      |                                                            ^ Error: expect(locator).toHaveValue(expected) failed
  194 |     await expect(page.getByLabel("照护类型", { exact: true })).toBeVisible();
  195 |   });
  196 | }
  197 | 
  198 | test("a forbidden child read removes previously shown household data", async ({ page }) => {
  199 |   await start(page);
  200 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 2.25, measured_at: "2026-10-01T12:00:00Z" });
  201 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  202 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  203 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("2.25 kg");
  204 |   await page.route("**/api/family/pets/mochi/measurements", route => route.fulfill({ status: 403, json: { detail: "No household access" } }));
  205 |   await mutate(page, "/api/home/pets/mochi/notes", { text: "触发一次实际资料修订", scope: "observation", activity: "general" });
  206 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  207 |   await expect(page.getByText("当前家庭资料不可访问，请重试或退出后重新登录。", { exact: true })).toBeVisible();
  208 |   await expect(page.getByRole("region", { name: "成长概览" })).toHaveCount(0);
  209 | });
  210 | 
  211 | for (const width of [320, 390, 1440]) {
  212 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  213 |     await page.setViewportSize({ width, height: 900 });
  214 |     await start(page);
  215 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  216 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  217 |       await page.keyboard.press("Enter");
  218 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  219 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  220 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  221 |     }
  222 |   });
  223 | }
  224 | 
```