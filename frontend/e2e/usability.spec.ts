import { test, expect, type Page } from "@playwright/test";

test.use({ timezoneId: "Asia/Shanghai" });

async function start(page: Page, timezone = "Asia/Shanghai", path = "/#app") {
  await page.goto(path);
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page.getByLabel("账号名").fill(`daily-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("日常主人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  await page.getByLabel("家庭名称").fill("我们的日常");
  await page.getByLabel("家庭时区", { exact: true }).fill(timezone);
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

test("growth deep link survives signup, refresh and browser navigation", async ({ page }) => {
  await start(page, "Asia/Shanghai", "/#app/growth");
  await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "照护", exact: true }).click();
  await expect(page).toHaveURL(/#app\/care$/);
  await page.goBack();
  await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
});

test("editing only a recurring task title preserves its future time and interval", async ({ page }) => {
  await start(page);
  await page.getByRole("button", { name: "照护", exact: true }).click();
  const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "brush", title: "每周梳毛", due_at: "2027-01-20T12:00:00+00:00", interval_days: 7 });
  const original = created.tasks.find((t: { title: string }) => t.title === "每周梳毛");
  await page.getByRole("button", { name: "同步最新记录" }).click();
  const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "每周梳毛", exact: true }) });
  await card.getByText("编辑或延期", { exact: true }).click();
  await card.getByLabel("任务标题").fill("温柔梳毛");
  await card.getByRole("button", { name: "保存任务编辑" }).click();
  await expect(page.getByRole("heading", { name: "温柔梳毛", exact: true })).toBeVisible();
  const updated = (await (await page.request.get("/api/home/state")).json()).tasks.find((t: { id: string }) => t.id === original.id);
  expect(updated.due_at).toBe(original.due_at);
  expect(updated.interval_days).toBe(7);
});

test("repeating care completion stays visible in completed history and keeps its next plan", async ({ page }) => {
  await start(page);
  const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "water", title: "每日换水", due_at: "2026-10-01T12:00:00Z", interval_days: 1 });
  const task = created.tasks.find((item: { title: string }) => item.title === "每日换水");
  await mutate(page, `/api/home/tasks/${task.id}/action`, { action: "complete", version: task.version, event_id: crypto.randomUUID() });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  await page.getByRole("button", { name: "照护", exact: true }).click();
  await page.getByRole("button", { name: "已完成", exact: true }).click();
  const queue = page.getByRole("region", { name: "照护队列" });
  await expect(queue).toContainText("每日换水");
  await expect(queue).toContainText("本次已完成");
  await expect(queue).toContainText("下次待办");
  await expect(queue.getByRole("button", { name: "完成照护", exact: true })).toHaveCount(0);
  const updated = (await (await page.request.get("/api/home/state")).json()).tasks.find((item: { id: string }) => item.id === task.id);
  expect(updated.completed).toBe(false);
  expect(updated.interval_days).toBe(1);
});

test("daily queue uses household day and keeps completed care out of active filters", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  await start(page, "Pacific/Honolulu");
  const me = await (await page.request.get("/api/family/me")).json();
  for (const task of [
    { title: "昨天换水", due_at: "2026-10-10T21:00:00Z" },
    { title: "今天陪玩", due_at: "2026-10-12T02:00:00Z", assigned_to: me.user.user_id },
    { title: "以后梳毛", due_at: "2026-10-13T20:00:00Z" },
    { title: "已做清洁", due_at: "2026-10-11T20:00:00Z" },
  ]) await mutate(page, "/api/home/pets/mochi/tasks", { kind: "play", ...task });
  const home = await (await page.request.get("/api/home/state")).json();
  const done = home.tasks.find((t: { title: string }) => t.title === "已做清洁");
  await mutate(page, `/api/home/tasks/${done.id}/action`, { action: "complete", version: done.version, event_id: crypto.randomUUID() });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  const overview = page.getByRole("region", { name: "今日概览" });
  await expect(overview).toContainText("2026-10-11");
  await overview.getByRole("button", { name: "查看照护" }).click();
  await page.getByRole("button", { name: "今天", exact: true }).click();
  const queue = page.getByRole("region", { name: "照护队列" });
  await expect(queue).toContainText("今天陪玩");
  await expect(queue).not.toContainText("以后梳毛");
  await expect(queue).not.toContainText("已做清洁");
  await page.getByRole("button", { name: "逾期", exact: true }).click();
  await expect(queue).toContainText("昨天换水");
  await expect(queue).not.toContainText("今天陪玩");
  await page.getByRole("button", { name: "我负责", exact: true }).click();
  await expect(queue).toContainText("今天陪玩");
  await expect(queue).not.toContainText("昨天换水");
  await page.getByRole("button", { name: "已完成", exact: true }).click();
  await expect(queue).toContainText("已做清洁");
  await page.getByRole("button", { name: "今日", exact: true }).first().click();
  await page.getByRole("button", { name: "管理照护计划", exact: true }).click();
  await expect(page).toHaveURL(/#app\/care$/);
});

test("a failed measurement read preserves reports and retries the failed resource", async ({ page }) => {
  await start(page);
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.2, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "owner_measured" });
  await mutate(page, "/api/family/pets/mochi/reports/generate", { period: "weekly", date: "2026-10-02" });
  let failed = false;
  await page.route("**/api/family/pets/mochi/measurements", async route => {
    if (!failed && route.request().method() === "GET") { failed = true; await route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } }); }
    else await route.continue();
  });
  await page.goto("/#app");
  await page.reload();
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "报告", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "实测与饮食", exact: true }).click();
  await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
});

test("a late growth read cannot replace the selected pet data", async ({ page }) => {
  await start(page);
  const created = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  const luna = created.pets.find((p: { name: string }) => p.name === "Luna");
  await mutate(page, `/api/family/pets/${luna.id}/measurements`, { kind: "weight", value: 3, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "vet" });
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let reached!: () => void;
  const received = new Promise<void>(resolve => { reached = resolve; });
  await page.route("**/api/family/pets/mochi/measurements", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  await page.goto("/#app");
  await page.reload({ waitUntil: "domcontentloaded" });
  await received;
  try {
    await page.getByRole("button", { name: "成长", exact: true }).click();
    await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption(luna.id);
    await expect(page.getByRole("region", { name: "成长概览" })).toContainText("3 kg");
  } finally { release(); }
  await expect(page.getByRole("region", { name: "成长概览" })).toContainText("兽医资料");
  await expect(page.getByRole("region", { name: "成长概览" })).not.toContainText("暂无称重");
});

test("constant and dense real measurements remain accessible and range-filtered", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  await start(page);
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.5, unit: "kg", measured_at: "2026-06-01T12:00:00Z", source: "vet" });
  for (let day = 1; day <= 10; day++) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2, unit: "kg", measured_at: `2026-10-${String(day).padStart(2, "0")}T12:00:00Z`, source: "owner_measured" });
  await page.goto("/#app");
  await page.reload();
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByLabel("曲线时间范围").selectOption("30");
  const chart = page.getByRole("region", { name: "体重曲线与明细" });
  await chart.getByText("查看测量明细", { exact: true }).click();
  await expect(chart.getByRole("table", { name: "体重测量明细" }).getByRole("row")).toHaveCount(11);
  await expect(chart).not.toContainText("2026-06-01");
  await expect(chart.getByRole("img", { name: /主人实测体重曲线/ })).toBeVisible();
  expect(await chart.locator("svg circle").evaluateAll(elements => elements.every(el => Number.isFinite(Number(el.getAttribute("cy")))))).toBe(true);
  await page.getByLabel("曲线时间范围").selectOption("all");
  await expect(chart.getByRole("table").getByRole("row")).toHaveCount(12);
});

test("equivalent timestamp offsets do not fabricate a zero-day weight change", async ({ page }) => {
  await start(page);
  for (const record of [
    { value: 1, measured_at: "2026-10-01T12:00:00+08:00" },
    { value: 2, measured_at: "2026-10-01T04:00:00Z" },
  ]) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", ...record });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  await page.getByRole("button", { name: "成长", exact: true }).click();
  const overview = page.getByRole("region", { name: "成长概览" });
  await expect(overview).toContainText("资料不足");
  await expect(overview).not.toContainText("实际跨度 0 天");
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 1.5, measured_at: "2026-09-30T04:00:00Z" });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  await expect(overview).toContainText("500 g");
  await expect(overview).toContainText("实际跨度 1 天");
});

for (const [kind, care] of [["toy", "play"], ["water", "water"], ["nest", "clean"]]) {
  test(`care started from a ${kind} preserves the intended ${care} type`, async ({ page }) => {
    await start(page);
    await mutate(page, "/api/home/pets/mochi/objects", { kind, name: "专属生活物品" });
    await page.getByRole("button", { name: "同步最新记录" }).click();
    if (kind === "water") {
      await page.getByRole("button", { name: "成长", exact: true }).click();
      await page.getByRole("button", { name: "照片日记与主人观察", exact: true }).click();
      await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name: "今日", exact: true }).click();
      await page.getByRole("button", { name: "布置小屋", exact: true }).click();
    }
    await page.getByRole("button", { name: "查看专属生活物品", exact: true }).click();
    await page.getByRole("button", { name: "安排相关照护", exact: true }).click();
    await expect(page).toHaveURL(/#app\/care$/);
    await expect(page.getByLabel("照护类型")).toHaveValue(care);
    await expect(page.getByLabel("照护类型")).toBeVisible();
  });
}

test("a forbidden child read removes previously shown household data", async ({ page }) => {
  await start(page);
  await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", unit: "kg", source: "owner_measured", value: 2.25, measured_at: "2026-10-01T12:00:00Z" });
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("button", { name: "同步最新记录" }).click();
  await expect(page.getByRole("region", { name: "成长概览" })).toContainText("2.25 kg");
  await page.route("**/api/family/pets/mochi/measurements", route => route.fulfill({ status: 403, json: { detail: "No household access" } }));
  await mutate(page, "/api/home/pets/mochi/notes", { text: "触发一次实际资料修订", scope: "observation", activity: "general" });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  await expect(page.getByText("当前家庭资料不可访问，请重试或退出后重新登录。", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "成长概览" })).toHaveCount(0);
});

test("the observation shortcut focuses its real field after a delayed home read", async ({ page }) => {
  await start(page);
  await expect(page.getByRole("img", { name: /Mochi.*像素形象/ }).first()).toBeVisible();
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let reached!: () => void;
  const received = new Promise<void>(resolve => { reached = resolve; });
  await page.route("**/api/home/state", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  try {
    await page.getByRole("region", { name: "今日概览" }).getByRole("button", { name: "记观察", exact: true }).click();
    await received;
  } finally { release(); }
  await expect(page.getByLabel("记录原文", { exact: true })).toBeFocused();
  await page.keyboard.type("今天愿意玩小球");
  await expect(page.getByLabel("记录原文", { exact: true })).toHaveValue("今天愿意玩小球");
});

test("changing care type preserves the chosen time, repetition and assignee", async ({ page }) => {
  await start(page);
  const me = await (await page.request.get("/api/family/me")).json();
  await page.getByRole("button", { name: "照护", exact: true }).click();
  await page.locator(".fa-create-summary").click();
  await page.getByLabel("照护名称", { exact: true }).fill("周末陪玩");
  await page.getByLabel("照护时间", { exact: true }).fill("2027-01-20T20:00");
  await page.getByLabel("重复间隔（天）", { exact: true }).fill("3");
  await page.getByLabel("负责人").selectOption(me.user.user_id);
  await page.getByLabel("照护类型").selectOption("play");
  await expect(page.getByLabel("照护时间", { exact: true })).toHaveValue("2027-01-20T20:00");
  await expect(page.getByLabel("重复间隔（天）", { exact: true })).toHaveValue("3");
  await expect(page.getByLabel("负责人")).toHaveValue(me.user.user_id);
  await page.getByRole("button", { name: "保存照护计划", exact: true }).click();
  await expect(page.getByRole("heading", { name: "周末陪玩", exact: true })).toBeVisible();
  const home = await (await page.request.get("/api/home/state")).json();
  const task = home.tasks.find((item: { title: string }) => item.title === "周末陪玩");
  expect(task.interval_days).toBe(3);
  expect(task.assigned_to).toBe(me.user.user_id);
  expect(Date.parse(task.due_at)).toBe(Date.parse("2027-01-20T12:00:00Z"));
});

for (const width of [320, 390, 1440]) {
  test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await start(page);
    for (const name of ["今日", "照护", "成长", "家庭"]) {
      await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      if (name === "今日" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
    }
  });
}
