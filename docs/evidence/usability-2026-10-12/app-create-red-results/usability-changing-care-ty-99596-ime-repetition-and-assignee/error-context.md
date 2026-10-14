# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> changing care type preserves the chosen time, repetition and assignee
- Location: frontend\e2e\usability.spec.ts:233:1

# Error details

```
Error: expect(locator).toHaveValue(expected) failed

Locator:  getByLabel('照护时间', { exact: true })
Expected: "2027-01-20T20:00"
Received: "2026-10-12T16:19"
Timeout:  20000ms

Call log:
  - Expect "toHaveValue" getByLabel('照护时间', { exact: true }) with timeout 20000ms
  - waiting for getByLabel('照护时间', { exact: true })
    43 × locator resolved to <input name="due" required="" type="datetime-local" value="2026-10-12T16:19"/>
       - unexpected value "2026-10-12T16:19"

```

```yaml
- textbox "照护时间": 2026-10-12T16:19
```

# Test source

```ts
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
  190 |     if (kind === "water") {
  191 |       await page.getByRole("button", { name: "成长", exact: true }).click();
  192 |       await page.getByRole("button", { name: "照片日记与主人观察", exact: true }).click();
  193 |       await page.getByRole("navigation", { name: "小屋功能" }).getByRole("button", { name: "档案与物品", exact: true }).click();
  194 |     }
  195 |     await page.getByRole("button", { name: "查看专属生活物品", exact: true }).click();
  196 |     await page.getByRole("button", { name: "安排相关照护", exact: true }).click();
  197 |     await expect(page).toHaveURL(/#app\/care$/);
  198 |     await expect(page.getByLabel("照护类型")).toHaveValue(care);
  199 |     await expect(page.getByLabel("照护类型")).toBeVisible();
  200 |   });
  201 | }
  202 | 
  203 | test("a forbidden child read removes previously shown household data", async ({ page }) => {
  204 |   await start(page);
  205 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 2.25, measured_at: "2026-10-01T12:00:00Z" });
  206 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  207 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  208 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("2.25 kg");
  209 |   await page.route("**/api/family/pets/mochi/measurements", route => route.fulfill({ status: 403, json: { detail: "No household access" } }));
  210 |   await mutate(page, "/api/home/pets/mochi/notes", { text: "触发一次实际资料修订", scope: "observation", activity: "general" });
  211 |   await page.getByRole("button", { name: "同步最新记录" }).click();
  212 |   await expect(page.getByText("当前家庭资料不可访问，请重试或退出后重新登录。", { exact: true })).toBeVisible();
  213 |   await expect(page.getByRole("region", { name: "成长概览" })).toHaveCount(0);
  214 | });
  215 | 
  216 | test("the observation shortcut focuses its real field after a delayed home read", async ({ page }) => {
  217 |   await start(page);
  218 |   await expect(page.getByRole("img", { name: /Mochi.*像素形象/ }).first()).toBeVisible();
  219 |   let release!: () => void;
  220 |   const gate = new Promise<void>(resolve => { release = resolve; });
  221 |   let reached!: () => void;
  222 |   const received = new Promise<void>(resolve => { reached = resolve; });
  223 |   await page.route("**/api/home/state", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  224 |   try {
  225 |     await page.getByRole("region", { name: "今日概览" }).getByRole("button", { name: "记观察", exact: true }).click();
  226 |     await received;
  227 |   } finally { release(); }
  228 |   await expect(page.getByLabel("记录原文", { exact: true })).toBeFocused();
  229 |   await page.keyboard.type("今天愿意玩小球");
  230 |   await expect(page.getByLabel("记录原文", { exact: true })).toHaveValue("今天愿意玩小球");
  231 | });
  232 | 
  233 | test("changing care type preserves the chosen time, repetition and assignee", async ({ page }) => {
  234 |   await start(page);
  235 |   const me = await (await page.request.get("/api/family/me")).json();
  236 |   await page.getByRole("button", { name: "照护", exact: true }).click();
  237 |   await page.locator(".fa-create-summary").click();
  238 |   await page.getByLabel("照护名称", { exact: true }).fill("周末陪玩");
  239 |   await page.getByLabel("照护时间", { exact: true }).fill("2027-01-20T20:00");
  240 |   await page.getByLabel("重复间隔（天）", { exact: true }).fill("3");
  241 |   await page.getByLabel("负责人").selectOption(me.user.user_id);
  242 |   await page.getByLabel("照护类型").selectOption("play");
> 243 |   await expect(page.getByLabel("照护时间", { exact: true })).toHaveValue("2027-01-20T20:00");
      |                                                          ^ Error: expect(locator).toHaveValue(expected) failed
  244 |   await expect(page.getByLabel("重复间隔（天）", { exact: true })).toHaveValue("3");
  245 |   await expect(page.getByLabel("负责人")).toHaveValue(me.user.user_id);
  246 |   await page.getByRole("button", { name: "保存照护计划", exact: true }).click();
  247 |   await expect(page.getByRole("heading", { name: "周末陪玩", exact: true })).toBeVisible();
  248 |   const home = await (await page.request.get("/api/home/state")).json();
  249 |   const task = home.tasks.find((item: { title: string }) => item.title === "周末陪玩");
  250 |   expect(task.interval_days).toBe(3);
  251 |   expect(task.assigned_to).toBe(me.user.user_id);
  252 |   expect(Date.parse(task.due_at)).toBe(Date.parse("2027-01-20T12:00:00Z"));
  253 | });
  254 | 
  255 | for (const width of [320, 390, 1440]) {
  256 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  257 |     await page.setViewportSize({ width, height: 900 });
  258 |     await start(page);
  259 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  260 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  261 |       await page.keyboard.press("Enter");
  262 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  263 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  264 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  265 |     }
  266 |   });
  267 | }
  268 | 
```