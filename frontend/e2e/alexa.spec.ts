import { test, expect, type Page } from "@playwright/test";

async function start(page: Page) {
  await page.goto("/#alexa");
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page.getByLabel("账号名").fill(`alexa-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("模拟体验主人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  await page.getByLabel("家庭名称").fill("Alexa 体验家庭");
  await page.getByRole("button", { name: "创建家庭", exact: true }).click();
}

test("Alexa simulator reads shared memory and confirms manual care exactly once", async ({ page }) => {
  await start(page);
  await expect(page.getByRole("heading", { name: "Alexa+ 网页模拟器", exact: true })).toBeVisible({ timeout: 1500 });
  await page.getByRole("button", { name: "分身", exact: true }).click();
  await page.getByLabel("偏好原文").fill("喜欢蓝色羽毛棒");
  await page.getByRole("button", { name: "保存候选记忆" }).click();
  await page.getByRole("button", { name: "确认记忆", exact: true }).click();
  await page.getByRole("link", { name: "体验 Alexa+ 网页模拟" }).click();
  await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  const log = page.getByRole("log", { name: "Alexa 模拟对话" });
  await expect(log).toContainText("喜欢蓝色羽毛棒");
  await page.getByRole("button", { name: "新会话", exact: true }).click();
  await expect(log).not.toContainText("喜欢蓝色羽毛棒");
  await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  await expect(log).toContainText("喜欢蓝色羽毛棒");
  await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
  await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  await page.getByRole("button", { name: "准备待确认方案" }).click();
  await expect(page.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
  await page.getByRole("button", { name: "确认安排人工照护", exact: true }).click();
  await expect(page.getByRole("region", { name: "照护结果" })).toContainText("已安排，等待人工完成");
  await page.getByRole("region", { name: "照护结果" }).getByRole("button", { name: "查看照护任务" }).click();
  const task = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "陪 Mochi 玩耍", exact: true }) });
  await expect(task).toHaveCount(1);
  await task.getByRole("button", { name: "完成照护" }).click();
  await page.getByRole("link", { name: "Alexa+ 模拟器", exact: true }).click();
  await page.getByRole("button", { name: "最近完成了什么", exact: true }).click();
  await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("陪 Mochi 玩耍");
  await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("人工完成记录");
});

test("new session clears transcript and stale drafts require a fresh question", async ({ page }) => {
  await start(page);
  await page.getByRole("button", { name: "安排换水", exact: true }).click();
  await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  await page.evaluate(async () => {
    const me = await (await fetch("/api/family/me")).json();
    await fetch("/api/home/pets/mochi/notes", {
      method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token },
      body: JSON.stringify({ text: "刚刚已经换水" }),
    });
  });
  await page.getByRole("button", { name: "准备待确认方案" }).click();
  await expect(page.getByRole("alert")).toContainText("记录已变化");
  await expect(page.getByRole("button", { name: "确认安排人工照护" })).toHaveCount(0);
  await page.getByRole("button", { name: "新会话", exact: true }).click();
  await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).not.toContainText("刚刚已经换水");
  await expect(page.getByRole("region", { name: "待确认照护草案" })).toHaveCount(0);
  await page.getByRole("button", { name: "今天有什么观察", exact: true }).click();
  await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("刚刚已经换水");
});

for (const width of [320, 390, 1440]) {
  test(`Alexa simulator is usable at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await start(page);
    await page.getByLabel("模拟口述内容").fill("它喜欢什么");
    await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
    await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("还没有已确认的偏好记忆");
    await page.getByRole("button", { name: "安排换水", exact: true }).click();
    await page.getByRole("button", { name: "准备待确认方案" }).click();
    await expect(page.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: `test-results/alexa-${width}.png`, fullPage: true });
  });
}

test("pet switching drops a delayed response and resets draft scope", async ({ page }) => {
  await start(page);
  const pet = await page.evaluate(async () => {
    const me = await (await fetch("/api/family/me")).json();
    const home = await (await fetch("/api/home/pets", {
      method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token },
      body: JSON.stringify({ name: "Luna" }),
    })).json();
    return home.pets.find((p: { name: string }) => p.name === "Luna");
  });
  await page.getByRole("button", { name: "同步最新记录" }).click();
  let release!: () => void;
  let arrived!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  const fetched = new Promise<void>((resolve) => { arrived = resolve; });
  await page.route("**/api/family/pets/mochi/chat", async (route) => {
    const response = await route.fetch();
    arrived();
    await gate;
    await route.fulfill({ response }).catch(() => {}); // switching aborts the old fetch
  });
  try {
    await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
    await fetched;
    await page.getByRole("combobox", { name: "当前宠物", exact: true }).selectOption(pet.id);
    release();
    await expect(page.getByRole("complementary", { name: "当前模拟设备与宠物" })).toContainText("Luna");
    await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).not.toContainText("Mochi");
    await expect(page.getByRole("region", { name: "待确认照护草案" })).toHaveCount(0);
    await page.getByRole("button", { name: "安排换水", exact: true }).click();
    await expect(page.getByRole("region", { name: "待确认照护草案" })).toContainText("Luna");
  } finally { release(); }
});

test("a failed chat restores the input and can be retried without inventing a reply", async ({ page }) => {
  await start(page);
  await page.route("**/api/family/pets/mochi/chat", (route) => route.fulfill({ status: 503, body: "unavailable" }), { times: 1 });
  await page.getByLabel("模拟口述内容").fill("它喜欢什么");
  await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("模拟口述内容")).toHaveValue("它喜欢什么");
  await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
  await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
  await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(1);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("keyboard input and account navigation can return to Alexa", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await start(page);
  await page.getByRole("button", { name: "模拟体验主人", exact: true }).click();
  await expect(page).toHaveURL(/#app\/family$/);
  await expect(page.getByRole("heading", { name: "个人设置", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Alexa+ 模拟器", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Alexa+ 网页模拟器", exact: true })).toBeVisible();
  const input = page.getByLabel("模拟口述内容");
  await input.fill("它喜欢什么");
  await input.press("Tab");
  await expect(page.getByRole("button", { name: "发送给 Alexa 模拟器" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toBeVisible();
  await expect(page.getByRole("button", { name: "新会话", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "新会话", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
  expect(await page.locator(".alx-orb").evaluate((element) => getComputedStyle(element).animationName)).toBe("none");
});

test("Alexa displays the response backend and same-response model evidence", async ({ page }) => {
  await start(page);
  // Transport fixture tests rendering only; this is never evidence of AWS connectivity.
  await page.route("**/api/family/pets/mochi/chat", async (route) => {
    const response = await route.fetch();
    const local = await response.json();
    await route.fulfill({ response, json: {
      ...local, backend: "bedrock", answer_origin: "model",
      request_id: "offline-browser-response-1", model_id: "amazon.nova-lite-v1:0",
      input_tokens: 900, output_tokens: 70, inference_status: "completed",
    }});
  }, { times: 1 });
  await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  const replies = page.getByRole("article", { name: "Alexa 分身回复" });
  await expect(replies.first()).toContainText("Bedrock 模型回答");
  await replies.first().getByText(/查看这轮依据/).click();
  await expect(replies.first()).toContainText("offline-browser-response-1");
  await expect(replies.first()).toContainText("输入 900 / 输出 70 tokens");
  await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
  await expect(replies.last()).toContainText("本地规则");
  await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
});
