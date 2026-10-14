# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> a forbidden child read removes previously shown household data
- Location: frontend\e2e\usability.spec.ts:198:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('当前家庭资料不可访问，请重试或退出后重新登录。', { exact: true })
Expected: visible
Timeout: 20000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('当前家庭资料不可访问，请重试或退出后重新登录。', { exact: true }) with timeout 20000ms
  - waiting for getByText('当前家庭资料不可访问，请重试或退出后重新登录。', { exact: true })

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
  - region "成长概览":
    - paragraph: GROWING, ONE RECORD AT A TIME
    - text: 最近实测体重
    - strong: 2.25 kg
    - paragraph: 2026/10/1 20:00 · 主人实测
    - text: 与上一次实测比较
    - strong: 资料不足
    - paragraph: 至少需要两次不同时间的有效测量。
    - text: 仅比较实际保存的测量；体重变化不代表健康诊断。
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
  - textbox "测量时间": 2026-10-12T16:09
  - text: 资料来源
  - combobox "资料来源":
    - option "主人实测" [selected]
    - option "兽医资料"
    - option "演示样本"
  - text: 备注
  - textbox "备注"
  - paragraph: 时间输入使用本机时区；记录按家庭时区 Asia/Shanghai 显示。
  - button "保存成长记录"
  - heading "成长曲线" [level=2]
  - alert:
    - text: 成长记录暂时无法读取。
    - button "重试成长记录"
    - text: 下方保留上次读取的记录，重试后更新。
  - region "体重曲线与明细":
    - text: 1 次实际测量 · Asia/Shanghai 曲线时间范围
    - combobox "曲线时间范围":
      - option "全部记录" [selected]
      - option "最近 30 天"
      - option "最近 90 天"
    - figure "目前只有一次测量，尚不能计算变化。纵轴范围随记录调整。":
      - img "主人实测体重曲线，1 次测量，未补填缺失日期": 2.317 2.272 2.228 2.183 kg 2.25 kg 2026-10-01
      - text: 目前只有一次测量，尚不能计算变化。纵轴范围随记录调整。
    - text: 测量点详情
    - combobox "测量点详情":
      - option "2026/10/1 20:00 · 2.25 kg" [selected]
    - strong: 2.25 kg
    - text: 2026/10/1 20:00 · 主人实测
    - group: 查看测量明细
  - article:
    - strong: 2.25 kg · 主人实测
    - paragraph: 2026/10/1 20:00 · 实测体重
    - button "纠正记录"
    - button "删除记录"
  - region "日报与周报":
    - paragraph: A LOOK BACK
    - heading "日报与周报" [level=2]
    - text: 报告周期
    - combobox "报告周期":
      - option "全部周期" [selected]
      - option "日报"
      - option "周报"
    - text: 统计日期
    - textbox "统计日期": 2026-10-12
    - button "生成日报"
    - button "生成周报"
    - paragraph: 按家庭时区 Asia/Shanghai 统计。服务运行时自动生成，重启后补跑；生成后尚未发送通知。
    - strong: 还没有这个周期的报告。
    - paragraph: 已有记录会在报告中回顾；缺少资料时会如实说明。
  - button "照片日记与主人观察"
  - region "观察与日记管理":
    - heading "观察与日记管理" [level=2]
    - paragraph: 保留当时作者和修订历史；修改后的有效内容同步用于统计和分身。
    - article:
      - strong: 触发一次实际资料修订
      - paragraph: 日常主人 · 一般观察
      - text: 2026/10/12 16:09
      - group: 纠正观察
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
  193 |     await expect(page.getByLabel("照护类型", { exact: true })).toHaveValue(care);
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
> 207 |   await expect(page.getByText("当前家庭资料不可访问，请重试或退出后重新登录。", { exact: true })).toBeVisible();
      |                                                                            ^ Error: expect(locator).toBeVisible() failed
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