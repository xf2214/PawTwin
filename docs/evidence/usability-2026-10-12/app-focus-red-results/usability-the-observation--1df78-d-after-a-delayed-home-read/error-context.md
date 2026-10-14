# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> the observation shortcut focuses its real field after a delayed home read
- Location: frontend\e2e\usability.spec.ts:211:1

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByLabel('记录原文', { exact: true })
Expected: focused
Received: inactive
Timeout:  20000ms

Call log:
  - Expect "toBeFocused" getByLabel('记录原文', { exact: true }) with timeout 20000ms
  - waiting for getByLabel('记录原文', { exact: true })
    43 × locator resolved to <textarea name="text" required="" maxlength="500" placeholder="例如：饭后不想玩 / 喜欢羽毛棒"></textarea>
       - unexpected value "inactive"

```

```yaml
- textbox "记录原文":
  - /placeholder: 例如：饭后不想玩 / 喜欢羽毛棒
```

# Test source

```ts
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
  207 |   await expect(page.getByText("当前家庭资料不可访问，请重试或退出后重新登录。", { exact: true })).toBeVisible();
  208 |   await expect(page.getByRole("region", { name: "成长概览" })).toHaveCount(0);
  209 | });
  210 | 
  211 | test("the observation shortcut focuses its real field after a delayed home read", async ({ page }) => {
  212 |   await start(page);
  213 |   await expect(page.getByRole("img", { name: /Mochi.*像素形象/ }).first()).toBeVisible();
  214 |   let release!: () => void;
  215 |   const gate = new Promise<void>(resolve => { release = resolve; });
  216 |   let reached!: () => void;
  217 |   const received = new Promise<void>(resolve => { reached = resolve; });
  218 |   await page.route("**/api/home/state", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  219 |   try {
  220 |     await page.getByRole("region", { name: "今日概览" }).getByRole("button", { name: "记观察", exact: true }).click();
  221 |     await received;
  222 |   } finally { release(); }
> 223 |   await expect(page.getByLabel("记录原文", { exact: true })).toBeFocused();
      |                                                          ^ Error: expect(locator).toBeFocused() failed
  224 |   await page.keyboard.type("今天愿意玩小球");
  225 |   await expect(page.getByLabel("记录原文", { exact: true })).toHaveValue("今天愿意玩小球");
  226 | });
  227 | 
  228 | for (const width of [320, 390, 1440]) {
  229 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  230 |     await page.setViewportSize({ width, height: 900 });
  231 |     await start(page);
  232 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  233 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  234 |       await page.keyboard.press("Enter");
  235 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  236 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  237 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  238 |     }
  239 |   });
  240 | }
  241 | 
```