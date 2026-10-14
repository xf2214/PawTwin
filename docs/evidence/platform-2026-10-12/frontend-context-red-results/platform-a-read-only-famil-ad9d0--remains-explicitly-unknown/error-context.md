# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: platform.spec.ts >> a read-only family member can query the twin and failed context data remains explicitly unknown
- Location: frontend\e2e\platform.spec.ts:146:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('.fa-context-overview')
Expected substring: "偏好读取失败"
Received string:    "照护前快速了解 Mochi档案喜好：未填写 · 主人陈述当前待办：0 项，计划不代表已执行。最近观察：暂无记录 · 主人陈述确认偏好：暂无已确认记忆"
Timeout: 20000ms

Call log:
  - Expect "toContainText" locator('.fa-context-overview') with timeout 20000ms
  - waiting for locator('.fa-context-overview')
    43 × locator resolved to <details open="" class="fa-context-overview">…</details>
       - unexpected value "照护前快速了解 Mochi档案喜好：未填写 · 主人陈述当前待办：0 项，计划不代表已执行。最近观察：暂无记录 · 主人陈述确认偏好：暂无已确认记忆"

```

```yaml
- group:
  - text: 照护前快速了解 Mochi
  - paragraph: 档案喜好：未填写 · 主人陈述
  - paragraph: 当前待办：0 项，计划不代表已执行。
  - paragraph: 最近观察：暂无记录 · 主人陈述
  - paragraph: 确认偏好：暂无已确认记忆
```

# Test source

```ts
  58  |   const download = await downloading;
  59  |   expect(download.suggestedFilename()).toMatch(/\.html$/);
  60  |   const stream = await download.createReadStream();
  61  |   if (!stream) throw new Error("Downloaded HTML stream is unavailable");
  62  |   const decoder = new TextDecoder(); let html = "";
  63  |   for await (const chunk of stream) html += decoder.decode(chunk as Uint8Array, { stream: true });
  64  |   html += decoder.decode();
  65  |   expect(html).toContain("2.12");
  66  |   expect(html).toContain("&lt;script&gt;");
  67  |   expect(html).not.toMatch(/<(script|iframe|link|img)\b/i);
  68  |   expect(html).not.toContain("其他宠物不可导出");
  69  |   expect(html).not.toContain(me.user.user_id);
  70  |   expect(html).not.toContain(me.household.household_id);
  71  |   const offline = await browser.newPage();
  72  |   try { await offline.setContent(html); await expect(offline.getByText("Mochi", { exact: true }).first()).toBeVisible(); expect(await offline.evaluate(() => "exportWasUnsafe" in window)).toBe(false); } finally { await offline.close(); }
  73  | });
  74  | 
  75  | test("an administrator grants one pet and a separate visitor reads and chats until revocation", async ({ page, browser, baseURL }) => {
  76  |   await start(page);
  77  |   await mutate(page, "/api/home/pets/mochi/notes", { text: "只喜欢蓝色小球", scope: "preference", activity: "play" });
  78  |   await mutate(page, "/api/home/pets/mochi/diary", { title: "私人日记不开放", text: "私人日记秘密", happened_on: new Date().toISOString().slice(0, 10) });
  79  |   await page.getByRole("button", { name: "家庭", exact: true }).click();
  80  |   await page.getByLabel("访问有效期").selectOption("24");
  81  |   await page.getByRole("button", { name: "授权照护者访问分身", exact: true }).click();
  82  |   const link = await page.getByLabel("新的只读访问链接").inputValue();
  83  |   expect(link).toContain("#pet-access=");
  84  |   const context = await browser.newContext({ baseURL });
  85  |   const visitor = await context.newPage();
  86  |   const familyRequests: string[] = [];
  87  |   visitor.on("request", request => { if (request.url().includes("/api/family/") || request.url().includes("/api/home/")) familyRequests.push(request.url()); });
  88  |   try {
  89  |     await visitor.goto(link);
  90  |     await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toBeVisible();
  91  |     await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toBeVisible();
  92  |     await expect(visitor.getByText("私人日记秘密", { exact: true })).toHaveCount(0);
  93  |     await expect(visitor.getByText("仅供测试的家庭名称", { exact: true })).toHaveCount(0);
  94  |     await visitor.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  95  |     await expect(visitor.getByRole("log", { name: "只读分身对话" })).toContainText("只喜欢蓝色小球");
  96  |     expect(familyRequests).toEqual([]);
  97  |     expect(await visitor.evaluate(() => Object.keys(localStorage).some(key => /access|token/i.test(key)))).toBe(false);
  98  |     await page.getByRole("button", { name: "撤销只读访问", exact: true }).click();
  99  |     await visitor.getByRole("button", { name: "刷新授权资料", exact: true }).click();
  100 |     await expect(visitor.getByRole("alert")).toContainText("失效");
  101 |     await expect(visitor.getByRole("log", { name: "只读分身对话" })).toHaveCount(0);
  102 |     await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toHaveCount(0);
  103 |   } finally { await context.close(); }
  104 | });
  105 | 
  106 | test("card download requires current household permission and cannot replace a frozen changed snapshot", async ({ page, browser, baseURL }) => {
  107 |   await start(page);
  108 |   const record = await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.4, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured" });
  109 |   await openCard(page);
  110 |   await mutate(page, `/api/family/pets/mochi/measurements/${record.id}`, { kind: "weight", value: 1.6, unit: "kg", measured_at: record.measured_at, source: "owner_measured", version: record.version }, "PUT");
  111 |   let downloads = 0;
  112 |   page.on("download", () => downloads++);
  113 |   await page.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  114 |   await expect(page.getByRole("alert")).toContainText("重新生成");
  115 |   expect(downloads).toBe(0);
  116 |   await page.getByRole("button", { name: "关闭信息卡", exact: true }).click();
  117 |   const invitation = await mutate(page, "/api/family/invitations", { role: "carer", expires_in_hours: 48, max_uses: 1 });
  118 |   const context = await browser.newContext({ baseURL, timezoneId: "Asia/Shanghai" });
  119 |   const carer = await context.newPage();
  120 |   try {
  121 |     await register(carer);
  122 |     await carer.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
  123 |     await carer.getByRole("button", { name: "加入家庭", exact: true }).click();
  124 |     await openCard(carer);
  125 |     const me = await (await carer.request.get("/api/family/me")).json();
  126 |     let deniedDownloads = 0;
  127 |     carer.on("download", () => deniedDownloads++);
  128 |     await mutate(page, `/api/family/members/${me.user.user_id}`, {}, "DELETE");
  129 |     await carer.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  130 |     await expect(carer.getByRole("alert")).toContainText(/权限|家庭|重新登录/);
  131 |     expect(deniedDownloads).toBe(0);
  132 |     await expect(carer.getByRole("region", { name: "就诊信息卡快照" })).toHaveCount(0);
  133 |   } finally { await context.close(); }
  134 | });
  135 | 
  136 | test("invalid access ignores an owner cookie and never restores family session data", async ({ page }) => {
  137 |   await start(page);
  138 |   const familyRequests: string[] = [];
  139 |   page.on("request", request => { if (request.url().includes("/api/family/me")) familyRequests.push(request.url()); });
  140 |   await page.goto("/#pet-access=invalid-bearer-secret-for-test");
  141 |   await expect(page.getByRole("alert")).toContainText(/无效|失效/);
  142 |   expect(familyRequests).toEqual([]);
  143 |   await expect(page.getByRole("navigation", { name: "App 主导航" })).toHaveCount(0);
  144 | });
  145 | 
  146 | test("a read-only family member can query the twin and failed context data remains explicitly unknown", async ({ page, browser, baseURL }) => {
  147 |   await start(page);
  148 |   await mutate(page, "/api/home/pets/mochi/notes", { text: "喜欢蓝色软球", scope: "preference", activity: "play" });
  149 |   const invitation = await mutate(page, "/api/family/invitations", { role: "guest", expires_in_hours: 24, max_uses: 1 });
  150 |   const context = await browser.newContext({ baseURL }), guest = await context.newPage();
  151 |   try {
  152 |     await guest.route("**/api/family/pets/mochi/memories", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"unavailable"}' }));
  153 |     await register(guest);
  154 |     await guest.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
  155 |     await guest.getByRole("button", { name: "加入家庭", exact: true }).click();
  156 |     await guest.getByRole("button", { name: "访问宠物分身", exact: true }).click();
  157 |     await guest.getByText("照护前快速了解 Mochi", { exact: true }).click();
> 158 |     await expect(guest.locator(".fa-context-overview")).toContainText("偏好读取失败");
      |                                                         ^ Error: expect(locator).toContainText(expected) failed
  159 |     await expect(guest.locator(".fa-context-overview")).not.toContainText("暂无已确认记忆");
  160 |     await guest.getByLabel("想了解什么").fill("它喜欢什么");
  161 |     await expect(guest.getByRole("button", { name: "询问分身", exact: true })).toBeEnabled();
  162 |     await guest.getByRole("button", { name: "询问分身", exact: true }).click();
  163 |     await expect(guest.getByRole("article", { name: "分身回复" })).toContainText("喜欢蓝色软球");
  164 |     await expect(guest.getByRole("button", { name: "生成照护方案", exact: true })).toBeDisabled();
  165 |   } finally { await context.close(); }
  166 | });
  167 | 
  168 | test("manual copy fallback and a mobile visitor preserve real diet and completion meanings", async ({ page, browser, baseURL }, info) => {
  169 |   await start(page);
  170 |   for (const measurement of [{ value: 35, diet_type: "food_offered", note: "提供蓝袋干粮" }, { value: 21, diet_type: "actual_intake", note: "主人观察实际吃下" }]) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "diet", unit: "g", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured", ...measurement });
  171 |   const home = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "water", title: "访客看见的换水", due_at: new Date(Date.now() - 3600000).toISOString() });
  172 |   const task = home.tasks.find((item: { title: string }) => item.title === "访客看见的换水");
  173 |   await mutate(page, `/api/home/tasks/${task.id}/action`, { action: "complete", version: task.version, event_id: crypto.randomUUID() });
  174 |   await page.getByRole("button", { name: "家庭", exact: true }).click();
  175 |   await page.getByRole("button", { name: "授权照护者访问分身", exact: true }).click();
  176 |   const input = page.getByLabel("新的只读访问链接"), link = await input.inputValue();
  177 |   await page.evaluate(() => Object.defineProperty(navigator, "clipboard", { value: undefined, configurable: true }));
  178 |   await page.getByRole("button", { name: "复制只读链接", exact: true }).click();
  179 |   await expect(page.getByRole("status")).toContainText("手动复制");
  180 |   await expect(input).toBeFocused();
  181 |   expect(await input.evaluate(element => [(element as HTMLInputElement).selectionStart, (element as HTMLInputElement).selectionEnd])).toEqual([0, link.length]);
  182 |   const context = await browser.newContext({ baseURL, viewport: { width: 320, height: 900 }, timezoneId: "Asia/Shanghai" });
  183 |   const visitor = await context.newPage();
  184 |   try {
  185 |     await visitor.goto(link);
  186 |     await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toBeVisible();
  187 |     await visitor.getByRole("button", { name: "最近吃了什么", exact: true }).focus(); await visitor.keyboard.press("Enter");
  188 |     const log = visitor.getByRole("log", { name: "只读分身对话" });
  189 |     await expect(log).toContainText("提供食物"); await expect(log).toContainText("35");
  190 |     await expect(log).toContainText("实际摄入"); await expect(log).toContainText("21");
  191 |     await expect(log).toContainText("提供蓝袋干粮");
  192 |     await visitor.getByRole("button", { name: "最近做了哪些照护", exact: true }).click();
  193 |     await expect(log).toContainText("访客看见的换水");
  194 |     await expect(log).toContainText("人工");
  195 |     expect(await visitor.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  196 |     await visitor.screenshot({ path: info.outputPath("visitor-320.png"), fullPage: true });
  197 |     await expect(visitor.getByRole("button", { name: /确认|完成任务|创建任务|出粮|生成方案/ })).toHaveCount(0);
  198 |   } finally { await context.close(); }
  199 | });
  200 | 
  201 | test("a delayed visitor response cannot reveal the previously authorized pet after switching links", async ({ page, browser, baseURL }) => {
  202 |   await start(page);
  203 |   const home = await mutate(page, "/api/home/pets", { name: "独立访客第二宠物", species: "dog" });
  204 |   const other = home.pets.find((pet: { name: string }) => pet.name === "独立访客第二宠物");
  205 |   await mutate(page, "/api/home/pets/mochi/notes", { text: "旧授权宠物专属观察", scope: "observation", activity: "general" });
  206 |   const first = await mutate(page, "/api/family/pets/mochi/care-access", { expires_in_hours: 1 });
  207 |   const second = await mutate(page, `/api/family/pets/${other.id}/care-access`, { expires_in_hours: 4 });
  208 |   const context = await browser.newContext({ baseURL }), visitor = await context.newPage();
  209 |   let release!: () => void, captured!: () => void, finished!: () => void, blocked = false;
  210 |   const gate = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve), done = new Promise<void>(resolve => finished = resolve);
  211 |   await visitor.route("**/api/care-access/context", async route => {
  212 |     if (blocked) { await route.continue(); return; } blocked = true;
  213 |     const response = await route.fetch(); captured(); await gate;
  214 |     try { await route.fulfill({ response }); } catch { /* Changing the link aborts the previous request. */ } finally { finished(); }
  215 |   });
  216 |   try {
  217 |     await visitor.goto(`/#pet-access=${encodeURIComponent(first.token)}`); await ready;
  218 |     await visitor.goto(`/#pet-access=${encodeURIComponent(second.token)}`);
  219 |     await expect(visitor.getByRole("heading", { name: /独立访客第二宠物.*只读分身/ })).toBeVisible();
  220 |     release(); await done;
  221 |     await expect(visitor.getByText("旧授权宠物专属观察", { exact: true })).toHaveCount(0);
  222 |     await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toHaveCount(0);
  223 |   } finally { release(); await context.close(); }
  224 | });
  225 | 
  226 | test("latest real weight outside the selected window retains its date and demo inclusion is explicit", async ({ page }) => {
  227 |   await start(page);
  228 |   const measured_at = new Date(Date.now() - 40 * 86400000).toISOString();
  229 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.23, unit: "kg", measured_at, source: "owner_measured", note: "四十天前实测" });
  230 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 8.88, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "demo_sample" });
  231 |   await openCard(page);
  232 |   const snapshot = page.getByRole("region", { name: "就诊信息卡快照" });
  233 |   await expect(snapshot).toContainText("1.23 kg");
  234 |   await expect(snapshot).toContainText("在所选窗口之前");
  235 |   await expect(snapshot).toContainText("所选窗口内无体重测量");
  236 |   await expect(snapshot).not.toContainText("8.88");
  237 |   await page.getByLabel("包含演示样本（仅作演示）").check();
  238 |   await expect(snapshot).toHaveCount(0);
  239 |   await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  240 |   await expect(snapshot).toContainText("8.88 kg");
  241 |   await expect(snapshot).toContainText("包含演示样本，请勿当作真实测量");
  242 | });
  243 | 
  244 | test("closing a delayed card and switching pets isolates late data and allows an actual retry", async ({ page }) => {
  245 |   await start(page);
  246 |   const created = await mutate(page, "/api/home/pets", { name: "切换目标宠物", species: "dog" });
  247 |   const other = created.pets.find((pet: { name: string }) => pet.name === "切换目标宠物");
  248 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2.56, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured", note: "原宠物私有测量" });
  249 |   let release!: () => void, captured!: () => void, finished!: () => void;
  250 |   const gate = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve), done = new Promise<void>(resolve => finished = resolve);
  251 |   await page.route("**/api/family/pets/mochi/visit-summary?*", async route => {
  252 |     const response = await route.fetch(); captured(); await gate;
  253 |     try { await route.fulfill({ response }); } catch { /* A closed card aborts its request. */ } finally { finished(); }
  254 |   });
  255 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  256 |   await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
  257 |   await page.getByRole("button", { name: "生成信息卡", exact: true }).click(); await ready;
  258 |   await page.getByRole("button", { name: "关闭信息卡", exact: true }).click();
```