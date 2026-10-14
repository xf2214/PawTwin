import { test, expect, type Page } from "@playwright/test";

test.use({ timezoneId: "Asia/Shanghai" });
async function register(page: Page) {
  await page.goto("/#app");
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page.getByLabel("账号名").fill(`platform-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("照护主人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
}
async function start(page: Page) {
  await register(page);
  await page.getByLabel("家庭名称").fill("仅供测试的家庭名称");
  await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
}
async function mutate(page: Page, path: string, body: object, method = "POST") {
  return page.evaluate(async ({ path, body, method }) => {
    const me = await (await fetch("/api/family/me")).json();
    const response = await fetch(path, { method, headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    return response.json();
  }, { path, body, method });
}
async function openCard(page: Page) {
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
  await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  await expect(page.getByRole("region", { name: "就诊信息卡快照" })).toBeVisible();
}

test("visit HTML download is a self-contained escaped pet snapshot and printing uses it", async ({ page, browser }) => {
  await start(page);
  const measured_at = new Date(Date.now() - 3600000).toISOString();
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2.12, unit: "kg", measured_at, source: "owner_measured" });
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 9.99, unit: "kg", measured_at, source: "demo_sample" });
  await mutate(page, "/api/home/pets/mochi/notes", { text: "观察原文 <script>window.exportWasUnsafe=true</script>", scope: "observation", activity: "general" });
  const created = await mutate(page, "/api/home/pets", { name: "其他宠物绝密资料", species: "dog" });
  const other = created.pets.find((pet: { name: string }) => pet.name === "其他宠物绝密资料");
  await mutate(page, `/api/home/pets/${other.id}/notes`, { text: "其他宠物不可导出", scope: "observation", activity: "general" });
  const me = await (await page.request.get("/api/family/me")).json();
  await openCard(page);
  const snapshot = page.getByRole("region", { name: "就诊信息卡快照" });
  await expect(snapshot).toContainText("2.12 kg");
  await expect(snapshot).not.toContainText("9.99");
  await page.evaluate(() => { window.print = () => { window.dispatchEvent(new Event("beforeprint")); }; window.addEventListener("beforeprint", () => document.body.dataset.cardPrintRequested = "yes"); });
  await page.getByRole("button", { name: "打印 / 另存为 PDF", exact: true }).click();
  await expect(page.locator("body")).toHaveAttribute("data-card-print-requested", "yes");
  await page.emulateMedia({ media: "print" });
  await expect(page.locator("#root")).toBeHidden();
  await expect(page.locator(".vc-print-host")).toBeVisible();
  await expect(page.locator(".vc-print-host")).toContainText("2.12 kg");
  await expect(page.locator(".vc-print-host")).not.toContainText("其他宠物绝密资料");
  await page.emulateMedia({ media: "screen" });
  const downloading = page.waitForEvent("download");
  await page.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  const download = await downloading;
  expect(download.suggestedFilename()).toMatch(/\.html$/);
  const stream = await download.createReadStream();
  if (!stream) throw new Error("Downloaded HTML stream is unavailable");
  const decoder = new TextDecoder(); let html = "";
  for await (const chunk of stream) html += decoder.decode(chunk as Uint8Array, { stream: true });
  html += decoder.decode();
  expect(html).toContain("2.12");
  expect(html).toContain("&lt;script&gt;");
  expect(html).not.toMatch(/<(script|iframe|link|img)\b/i);
  expect(html).not.toContain("其他宠物不可导出");
  expect(html).not.toContain(me.user.user_id);
  expect(html).not.toContain(me.household.household_id);
  const offline = await browser.newPage();
  try { await offline.setContent(html); await expect(offline.getByText("Mochi", { exact: true }).first()).toBeVisible(); expect(await offline.evaluate(() => "exportWasUnsafe" in window)).toBe(false); } finally { await offline.close(); }
});

test("an administrator grants one pet and a separate visitor reads and chats until revocation", async ({ page, browser, baseURL }) => {
  await start(page);
  await mutate(page, "/api/home/pets/mochi/notes", { text: "只喜欢蓝色小球", scope: "preference", activity: "play" });
  await mutate(page, "/api/home/pets/mochi/diary", { title: "私人日记不开放", text: "私人日记秘密", happened_on: new Date().toISOString().slice(0, 10) });
  await page.getByRole("button", { name: "家庭", exact: true }).click();
  await page.getByLabel("访问有效期").selectOption("24");
  await page.getByRole("button", { name: "授权照护者访问分身", exact: true }).click();
  const link = await page.getByLabel("新的只读访问链接").inputValue();
  expect(link).toContain("#pet-access=");
  const context = await browser.newContext({ baseURL });
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  const visitor = await context.newPage();
  const familyRequests: string[] = [];
  visitor.on("request", request => { if (request.url().includes("/api/family/") || request.url().includes("/api/home/")) familyRequests.push(request.url()); });
  try {
    await visitor.goto(link);
    await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toBeVisible();
    await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toBeVisible();
    await expect(visitor.getByText("私人日记秘密", { exact: true })).toHaveCount(0);
    await expect(visitor.getByText("仅供测试的家庭名称", { exact: true })).toHaveCount(0);
    await visitor.getByRole("button", { name: "它喜欢什么", exact: true }).click();
    await expect(visitor.getByRole("log", { name: "只读分身对话" })).toContainText("只喜欢蓝色小球");
    expect(familyRequests).toEqual([]);
    expect(await visitor.evaluate(() => Object.keys(localStorage).some(key => /access|token/i.test(key)))).toBe(false);
    await page.getByRole("button", { name: "撤销只读访问", exact: true }).click();
    await visitor.getByRole("button", { name: "刷新授权资料", exact: true }).click();
    await expect(visitor.getByRole("alert")).toContainText("失效");
    await expect(visitor.getByRole("log", { name: "只读分身对话" })).toHaveCount(0);
    await expect(visitor.getByText("只喜欢蓝色小球", { exact: true })).toHaveCount(0);
  } finally { await context.close(); }
});

test("card download requires current household permission and cannot replace a frozen changed snapshot", async ({ page, browser, baseURL }) => {
  await start(page);
  const record = await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.4, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured" });
  await openCard(page);
  await mutate(page, `/api/family/pets/mochi/measurements/${record.id}`, { kind: "weight", value: 1.6, unit: "kg", measured_at: record.measured_at, source: "owner_measured", version: record.version }, "PUT");
  let downloads = 0;
  page.on("download", () => downloads++);
  await page.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("重新生成");
  expect(downloads).toBe(0);
  await page.getByRole("button", { name: "关闭信息卡", exact: true }).click();
  const invitation = await mutate(page, "/api/family/invitations", { role: "carer", expires_in_hours: 48, max_uses: 1 });
  const context = await browser.newContext({ baseURL, timezoneId: "Asia/Shanghai" });
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  const carer = await context.newPage();
  try {
    await register(carer);
    await carer.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
    await carer.getByRole("button", { name: "加入家庭", exact: true }).click();
    await openCard(carer);
    const me = await (await carer.request.get("/api/family/me")).json();
    let deniedDownloads = 0;
    carer.on("download", () => deniedDownloads++);
    await mutate(page, `/api/family/members/${me.user.user_id}`, {}, "DELETE");
    await carer.getByRole("button", { name: "下载自包含 HTML", exact: true }).click();
    await expect(carer.getByRole("alert")).toContainText(/权限|家庭|重新登录/);
    expect(deniedDownloads).toBe(0);
    await expect(carer.getByRole("region", { name: "就诊信息卡快照" })).toHaveCount(0);
  } finally { await context.close(); }
});

test("invalid access ignores an owner cookie and never restores family session data", async ({ page }) => {
  await start(page);
  const familyRequests: string[] = [];
  page.on("request", request => { if (request.url().includes("/api/family/me")) familyRequests.push(request.url()); });
  await page.goto("/#pet-access=invalid-bearer-secret-for-test");
  await expect(page.getByRole("alert")).toContainText(/无效|失效/);
  expect(familyRequests).toEqual([]);
  await expect(page.getByRole("navigation", { name: "App 主导航" })).toHaveCount(0);
});

test("a family guest reads the overview with honest missing state while existing POST permissions stay enforced", async ({ page, browser, baseURL }) => {
  await start(page);
  await mutate(page, "/api/home/pets/mochi/notes", { text: "喜欢蓝色软球", scope: "preference", activity: "play" });
  const invitation = await mutate(page, "/api/family/invitations", { role: "guest", expires_in_hours: 24, max_uses: 1 });
  const context = await browser.newContext({ baseURL }), guest = await context.newPage();
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  try {
    await guest.route("**/api/family/pets/mochi/memories", route => route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"unavailable"}' }));
    await register(guest);
    await guest.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
    await guest.getByRole("button", { name: "加入家庭", exact: true }).click();
    await guest.getByRole("button", { name: "访问宠物分身", exact: true }).click();
    await guest.getByText("照护前快速了解 Mochi", { exact: true }).click();
    await expect(guest.locator(".fa-context-overview")).toContainText("偏好读取失败");
    await expect(guest.locator(".fa-context-overview")).not.toContainText("暂无已确认记忆");
    await expect(guest.getByRole("button", { name: "询问分身", exact: true })).toHaveCount(0);
    await expect(guest.getByRole("button", { name: "它喜欢什么", exact: true })).toHaveCount(0);
    await expect(guest.getByRole("button", { name: "建立待确认方案", exact: true })).toHaveCount(0);
    expect(await guest.evaluate(async () => {
      const me = await (await fetch("/api/family/me")).json();
      return (await fetch("/api/family/pets/mochi/chat", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify({ text: "它喜欢什么", entry: "app" }) })).status;
    })).toBe(403);
  } finally { await context.close(); }
});

test("manual copy fallback and a mobile visitor preserve real diet and completion meanings", async ({ page, browser, baseURL }, info) => {
  await start(page);
  for (const measurement of [{ value: 35, diet_type: "food_offered", note: "提供蓝袋干粮" }, { value: 21, diet_type: "actual_intake", note: "主人观察实际吃下" }]) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "diet", unit: "g", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured", ...measurement });
  const home = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "water", title: "访客看见的换水", due_at: new Date(Date.now() - 3600000).toISOString() });
  const task = home.tasks.find((item: { title: string }) => item.title === "访客看见的换水");
  await mutate(page, `/api/home/tasks/${task.id}/action`, { action: "complete", version: task.version, event_id: crypto.randomUUID() });
  await page.getByRole("button", { name: "家庭", exact: true }).click();
  await page.getByRole("button", { name: "授权照护者访问分身", exact: true }).click();
  const input = page.getByLabel("新的只读访问链接"), link = await input.inputValue();
  await page.evaluate(() => Object.defineProperty(navigator, "clipboard", { value: undefined, configurable: true }));
  await page.getByRole("button", { name: "复制只读链接", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("手动复制");
  await expect(input).toBeFocused();
  expect(await input.evaluate(element => [(element as HTMLInputElement).selectionStart, (element as HTMLInputElement).selectionEnd])).toEqual([0, link.length]);
  const context = await browser.newContext({ baseURL, viewport: { width: 320, height: 900 }, timezoneId: "Asia/Shanghai" });
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  const visitor = await context.newPage();
  try {
    await visitor.goto(link);
    await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toBeVisible();
    await visitor.getByRole("button", { name: "最近吃了什么", exact: true }).focus(); await visitor.keyboard.press("Enter");
    const log = visitor.getByRole("log", { name: "只读分身对话" });
    await expect(log).toContainText("提供食物"); await expect(log).toContainText("35");
    await expect(log).toContainText("实际摄入"); await expect(log).toContainText("21");
    await expect(log).toContainText("提供蓝袋干粮");
    await visitor.getByRole("button", { name: "最近做了哪些照护", exact: true }).click();
    await expect(log).toContainText("访客看见的换水");
    await expect(log).toContainText("人工");
    expect(await visitor.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await visitor.screenshot({ path: info.outputPath("visitor-320.png"), fullPage: true });
    await expect(visitor.getByRole("button", { name: /确认|完成任务|创建任务|出粮|生成方案/ })).toHaveCount(0);
  } finally { await context.close(); }
});

test("a delayed visitor response cannot reveal the previously authorized pet after switching links", async ({ page, browser, baseURL }) => {
  await start(page);
  const home = await mutate(page, "/api/home/pets", { name: "独立访客第二宠物", species: "dog" });
  const other = home.pets.find((pet: { name: string }) => pet.name === "独立访客第二宠物");
  await mutate(page, "/api/home/pets/mochi/notes", { text: "旧授权宠物专属观察", scope: "observation", activity: "general" });
  const first = await mutate(page, "/api/family/pets/mochi/care-access", { expires_in_hours: 1 });
  const second = await mutate(page, `/api/family/pets/${other.id}/care-access`, { expires_in_hours: 4 });
  const context = await browser.newContext({ baseURL }), visitor = await context.newPage();
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  let release!: () => void, captured!: () => void, finished!: () => void, blocked = false;
  const gate = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve), done = new Promise<void>(resolve => finished = resolve);
  await visitor.route("**/api/care-access/context", async route => {
    if (blocked) { await route.continue(); return; } blocked = true;
    const response = await route.fetch(); captured(); await gate;
    try { await route.fulfill({ response }); } catch { /* Changing the link aborts the previous request. */ } finally { finished(); }
  });
  try {
    await visitor.goto(`/#pet-access=${encodeURIComponent(first.token)}`); await ready;
    await visitor.goto(`/#pet-access=${encodeURIComponent(second.token)}`);
    await expect(visitor.getByRole("heading", { name: /独立访客第二宠物.*只读分身/ })).toBeVisible();
    release(); await done;
    await expect(visitor.getByText("旧授权宠物专属观察", { exact: true })).toHaveCount(0);
    await expect(visitor.getByRole("heading", { name: /Mochi.*只读分身/ })).toHaveCount(0);
  } finally { release(); await context.close(); }
});

test("latest real weight outside the selected window retains its date and demo inclusion is explicit", async ({ page }) => {
  await start(page);
  const measured_at = new Date(Date.now() - 40 * 86400000).toISOString();
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.23, unit: "kg", measured_at, source: "owner_measured", note: "四十天前实测" });
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 8.88, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "demo_sample" });
  await openCard(page);
  const snapshot = page.getByRole("region", { name: "就诊信息卡快照" });
  await expect(snapshot).toContainText("1.23 kg");
  await expect(snapshot).toContainText("在所选窗口之前");
  await expect(snapshot).toContainText("所选窗口内无体重测量");
  await expect(snapshot).not.toContainText("8.88");
  await page.getByLabel("包含演示样本（仅作演示）").check();
  await expect(snapshot).toHaveCount(0);
  await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  await expect(snapshot).toContainText("8.88 kg");
  await expect(snapshot).toContainText("包含演示样本，请勿当作真实测量");
});

test("closing a delayed card and switching pets isolates late data and allows an actual retry", async ({ page }) => {
  await start(page);
  const created = await mutate(page, "/api/home/pets", { name: "切换目标宠物", species: "dog" });
  const other = created.pets.find((pet: { name: string }) => pet.name === "切换目标宠物");
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2.56, unit: "kg", measured_at: new Date(Date.now() - 3600000).toISOString(), source: "owner_measured", note: "原宠物私有测量" });
  let release!: () => void, captured!: () => void, finished!: () => void;
  const gate = new Promise<void>(resolve => release = resolve), ready = new Promise<void>(resolve => captured = resolve), done = new Promise<void>(resolve => finished = resolve);
  await page.route("**/api/family/pets/mochi/visit-summary?*", async route => {
    const response = await route.fetch(); captured(); await gate;
    try { await route.fulfill({ response }); } catch { /* A closed card aborts its request. */ } finally { finished(); }
  });
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
  await page.getByRole("button", { name: "生成信息卡", exact: true }).click(); await ready;
  await page.getByRole("button", { name: "关闭信息卡", exact: true }).click();
  await page.getByLabel("当前宠物").selectOption(other.id);
  let failed = false;
  await page.route(`**/api/family/pets/${other.id}/visit-summary?*`, async route => { if (!failed) { failed = true; await route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"temporary"}' }); } else await route.continue(); });
  await page.getByRole("button", { name: "导出就诊信息卡（诊断资料）", exact: true }).click();
  await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("重试");
  await page.getByRole("button", { name: "生成信息卡", exact: true }).click();
  const snapshot = page.getByRole("region", { name: "就诊信息卡快照" });
  await expect(snapshot).toContainText("切换目标宠物");
  release(); await done;
  await expect(snapshot).not.toContainText("原宠物私有测量");
  await expect(snapshot).not.toContainText("2.56 kg");
});

for (const width of [320, 390, 1440]) {
  test(`visit preview and grant controls stay readable at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await start(page);
    await openCard(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`visit-${width}.png`), fullPage: true });
    await page.getByRole("button", { name: "关闭信息卡", exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.getByRole("button", { name: "家庭", exact: true }).click();
    await expect(page.getByRole("button", { name: "授权照护者访问分身", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
