import { expect, test, type BrowserContext, type Page, type Route } from "@playwright/test";

test.use({ timezoneId: "Asia/Shanghai" });

const password = "browser-isolation-password";

async function createHousehold(context: BrowserContext, baseURL: string, name: string) {
  const username = `isolation-${Date.now()}-${Math.floor(Math.random() * 999999)}`;
  const registered = await context.request.post(`${baseURL}/api/family/register`, {
    data: { username, password, display_name: name },
  });
  expect(registered.ok()).toBe(true);
  const user = await registered.json();
  const created = await context.request.post(`${baseURL}/api/family/households`, {
    headers: { "X-CSRF-Token": user.csrf_token },
    data: { name, timezone: "Asia/Shanghai" },
  });
  expect(created.ok()).toBe(true);
  return username;
}

async function mutate(page: Page, path: string, body: object) {
  const me = await (await page.request.get("/api/family/me")).json();
  const response = await page.request.post(path, {
    headers: { "X-CSRF-Token": me.csrf_token }, data: body,
  });
  expect(response.ok()).toBe(true);
  return response.json();
}

async function holdHome(page: Page) {
  let reached!: () => void, release!: () => void, delivered!: () => void;
  const captured = new Promise<void>(resolve => { reached = resolve; });
  const gate = new Promise<void>(resolve => { release = resolve; });
  const completed = new Promise<void>(resolve => { delivered = resolve; });
  await page.route("**/api/home/state", async (route: Route) => {
    const response = await route.fetch();
    reached();
    await gate;
    try { await route.fulfill({ response }); } catch { /* Superseded reads can be aborted. */ }
    finally { delivered(); }
  }, { times: 1 });
  return { captured, release: async () => {
    release();
    await completed;
    await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
  } };
}

test("a fresh signed-out visit opens the login form without an expired-session warning", async ({ page }) => {
  await page.goto("/#app");
  await expect(page.getByRole("button", { name: "登录账号", exact: true })).toBeEnabled();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("a stuck initial refresh reaches its deadline and offers a working retry despite background polling", async ({ page, context, baseURL }) => {
  await createHousehold(context, baseURL!, "Refresh deadline");
  await page.clock.install();
  let reached!: () => void, release!: () => void, hold = true;
  const captured = new Promise<void>(resolve => { reached = resolve; });
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/family/me", async route => {
    if (!hold) { await route.continue(); return; }
    const response = await route.fetch();
    reached(); await gate;
    try { await route.fulfill({ response }); } catch { /* Timed-out reads cannot apply. */ }
  });
  try {
    await page.goto("/#app");
    await captured;
    await page.clock.runFor(15001);
    await expect(page.getByRole("alert")).toContainText("连接失败，请检查网络后重试。");
    await expect(page.getByRole("button", { name: "重试", exact: true })).toBeEnabled();
    hold = false; release();
    await page.getByRole("button", { name: "重试", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Refresh deadline", exact: true })).toBeVisible();
  } finally { release(); }
});

test("signing into another household clears the previous household's raw invitation token", async ({ page, context, browser, baseURL }) => {
  await createHousehold(context, baseURL!, "Invitation source household");
  await page.goto("/#app/family");
  await page.getByRole("button", { name: "生成家庭邀请", exact: true }).click();
  await expect(page.getByLabel(/新邀请口令/)).toBeVisible();
  const token = await page.getByLabel(/新邀请口令/).inputValue();
  expect(token.length).toBeGreaterThan(20);
  const other = await browser.newContext({ baseURL });
  try {
    const username = await createHousehold(other, baseURL!, "Invitation destination household");
    await page.getByRole("button", { name: "退出账号", exact: true }).click();
    await page.getByLabel("账号名", { exact: true }).fill(username);
    await page.getByLabel("密码", { exact: true }).fill(password);
    await page.getByRole("button", { name: "登录账号", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Invitation destination household", exact: true })).toBeVisible();
    await expect(page.getByLabel(/新邀请口令/)).toHaveCount(0);
  } finally { await other.close(); }
});

test("a late invitation creation cannot expose its raw token after switching accounts", async ({ page, context, browser, baseURL }) => {
  await createHousehold(context, baseURL!, "Late invitation source");
  await page.goto("/#app/family");
  await expect(page.getByRole("button", { name: "生成家庭邀请", exact: true })).toBeEnabled();
  const other = await browser.newContext({ baseURL });
  let reached!: () => void, release!: () => void, delivered!: () => void;
  const captured = new Promise<void>(resolve => { reached = resolve; });
  const gate = new Promise<void>(resolve => { release = resolve; });
  const completed = new Promise<void>(resolve => { delivered = resolve; });
  try {
    const username = await createHousehold(other, baseURL!, "Late invitation destination");
    await page.route("**/api/family/invitations", async route => {
      if (route.request().method() !== "POST") { await route.continue(); return; }
      const response = await route.fetch();
      reached(); await gate;
      try { await route.fulfill({ response }); } finally { delivered(); }
    });
    await page.getByRole("button", { name: "生成家庭邀请", exact: true }).click();
    await captured;
    await page.getByRole("button", { name: "退出账号", exact: true }).click();
    await page.getByLabel("账号名", { exact: true }).fill(username);
    await page.getByLabel("密码", { exact: true }).fill(password);
    await page.getByRole("button", { name: "登录账号", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Late invitation destination", exact: true })).toBeVisible();
    release(); await completed;
    await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
    await expect(page.getByLabel(/新邀请口令/)).toHaveCount(0);
  } finally { release(); await other.close(); }
});

test("switching pets clears an unsaved new measurement before it can be saved for another pet", async ({ page, context, baseURL }) => {
  await createHousehold(context, baseURL!, "Measurement isolation");
  await page.goto("/#app/growth");
  const home = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  const luna = home.pets.find((pet: { name: string }) => pet.name === "Luna");
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "实测与饮食", exact: true }).click();
  await page.getByLabel("测量数值", { exact: true }).fill("1.234");
  await page.getByLabel("备注", { exact: true }).fill("Mochi's unsaved measurement");
  await page.locator(".fa-petbar select").selectOption(luna.id);
  await expect(page.getByRole("heading", { name: "Luna 的成长记录", exact: true })).toBeVisible();
  await expect(page.getByLabel("测量数值", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("备注", { exact: true })).toHaveValue("");
  await page.getByLabel("测量数值", { exact: true }).fill("3.21");
  await page.getByRole("button", { name: "保存成长记录", exact: true }).click();
  await expect(page.getByText("3.21 kg · 主人实测", { exact: true })).toBeVisible();
  const saved = await (await page.request.get(`/api/family/pets/${luna.id}/measurements`)).json();
  expect(saved.records.map((record: { value: number; note: string }) => [record.value, record.note])).toEqual([[3.21, ""]]);
});

test("a delayed previous household response cannot reveal records after signing into another account", async ({ page, context, browser, baseURL }) => {
  await createHousehold(context, baseURL!, "First household");
  await page.goto("/#app/assistant");
  await mutate(page, "/api/home/pets/mochi/notes", { text: "Private first-household observation", scope: "observation", activity: "general" });
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await expect(page.locator(".fa-context-overview")).toContainText("Private first-household observation");
  const other = await browser.newContext({ baseURL });
  try {
    const username = await createHousehold(other, baseURL!, "Second household");
    const held = await holdHome(page);
    await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
    await held.captured;
    await page.getByRole("button", { name: "退出账号", exact: true }).click();
    await page.getByLabel("账号名", { exact: true }).fill(username);
    await page.getByLabel("密码", { exact: true }).fill(password);
    await page.getByRole("button", { name: "登录账号", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Second household", exact: true })).toBeVisible();
    await expect(page.locator(".fa-context-overview")).not.toContainText("Private first-household observation");
    await held.release();
    await expect(page.getByRole("heading", { name: "Second household", exact: true })).toBeVisible();
    await expect(page.locator(".fa-context-overview")).not.toContainText("Private first-household observation");
  } finally { await other.close(); }
});

test("a superseded refresh cannot replace a newer owner observation", async ({ page, context, baseURL }) => {
  await createHousehold(context, baseURL!, "Refresh ordering");
  await page.goto("/#app/assistant");
  await mutate(page, "/api/home/pets/mochi/notes", { text: "Older observation", scope: "observation", activity: "general" });
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await expect(page.locator(".fa-context-overview")).toContainText("Older observation");
  const held = await holdHome(page);
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await held.captured;
  await mutate(page, "/api/home/pets/mochi/notes", { text: "Newest observation", scope: "observation", activity: "general" });
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await expect(page.locator(".fa-context-overview")).toContainText("Newest observation");
  await held.release();
  await expect(page.locator(".fa-context-overview")).toContainText("Newest observation");
});

test("superseding a stuck refresh releases the Alexa response instead of leaving its controls busy", async ({ page, context, baseURL }) => {
  await createHousehold(context, baseURL!, "Alexa refresh recovery");
  await page.goto("/#alexa");
  await expect(page.getByRole("button", { name: "它喜欢什么", exact: true })).toBeEnabled();
  let reached!: () => void, release!: () => void;
  const captured = new Promise<void>(resolve => { reached = resolve; });
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/family/me", async route => {
    const response = await route.fetch();
    reached(); await gate;
    try { await route.fulfill({ response }); } catch { /* An aborted refresh is expected. */ }
  }, { times: 1 });
  try {
    await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
    await captured;
    await expect(page.getByRole("article", { name: "Alexa 分身回复", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
    await expect(page.getByRole("button", { name: "安排陪玩", exact: true })).toBeEnabled({ timeout: 4000 });
    await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
    await expect(page.getByRole("region", { name: "待确认照护草案", exact: true })).toBeVisible();
  } finally { release(); }
});
