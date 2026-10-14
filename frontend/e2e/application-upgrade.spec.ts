import { expect, test, type Page } from "@playwright/test";

test.use({ timezoneId: "Asia/Shanghai" });

async function register(page: Page) {
  await page.goto("/#app");
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page.getByLabel("账号名").fill(`workspace-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("日常照护人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
}

async function start(page: Page) {
  await register(page);
  await page.getByLabel("家庭名称", { exact: true }).fill("我们的照护日常");
  await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
}

async function mutate(page: Page, path: string, body: object) {
  return page.evaluate(async ({ path, body }) => {
    const me = await (await fetch("/api/family/me")).json();
    const response = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    return response.json();
  }, { path, body });
}

test("today uses one application navigation while profile and room operations remain discoverable", async ({ page }) => {
  await start(page);
  await expect(page.getByRole("navigation", { name: "小屋功能" })).toHaveCount(0);
  const navigation = page.getByRole("navigation", { name: "App 主导航" });
  await expect(navigation.getByRole("button", { name: "今日", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("region", { name: "今日概览" })).toBeVisible();
  await expect(page.getByRole("img", { name: /Mochi.*像素形象/ }).first()).toBeVisible();
  await page.getByRole("button", { name: "编辑档案", exact: true }).first().click();
  await expect(page.getByLabel("名字 *", { exact: true })).toBeVisible();
  await navigation.getByRole("button", { name: "照护", exact: true }).click();
  await navigation.getByRole("button", { name: "今日", exact: true }).click();
  await expect(page).toHaveURL(/#app\/home$/);
  await expect(page.getByRole("navigation", { name: "小屋功能" })).toHaveCount(0);
});

test("my care includes an unassigned task claimed by the current member", async ({ page }) => {
  await start(page);
  const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "water", title: "我接手的换水", due_at: new Date(Date.now() - 3600000).toISOString(), assigned_to: null });
  const task = created.tasks.find((item: { title: string }) => item.title === "我接手的换水");
  await mutate(page, `/api/home/tasks/${task.id}/action`, { action: "claim", version: task.version, event_id: crypto.randomUUID() });
  await page.getByRole("button", { name: "同步最新记录", exact: true }).click();
  await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name: "照护", exact: true }).click();
  await page.getByRole("button", { name: "我负责", exact: true }).click();
  const card = page.getByRole("region", { name: "照护队列" }).getByRole("article").filter({ has: page.getByRole("heading", { name: "我接手的换水", exact: true }) });
  await expect(card).toBeVisible();
  await expect(card).toContainText("领取人：日常照护人");
  await card.getByRole("button", { name: "完成照护", exact: true }).click();
  await expect(page.getByRole("region", { name: "照护队列" })).not.toContainText("我接手的换水");
});

test("growth sections preserve actual measurement recording and report generation", async ({ page }) => {
  await start(page);
  await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name: "成长", exact: true }).click();
  const sections = page.getByRole("navigation", { name: "成长分区" });
  await sections.getByRole("button", { name: "实测与饮食", exact: true }).click();
  await page.getByLabel("测量数值", { exact: true }).fill("2.05");
  await page.getByRole("button", { name: "保存成长记录", exact: true }).click();
  await sections.getByRole("button", { name: "概览", exact: true }).click();
  await expect(page.getByRole("region", { name: "成长概览" })).toContainText("2.05 kg");
  await sections.getByRole("button", { name: "报告", exact: true }).click();
  await page.getByRole("button", { name: "生成日报", exact: true }).click();
  await expect(page.getByRole("region", { name: "日报与周报" })).toContainText("日报");
  await sections.getByRole("button", { name: "日记与观察", exact: true }).click();
  await expect(page.getByLabel("记录原文", { exact: true })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "小屋功能" })).toHaveCount(0);
  await sections.getByRole("button", { name: "实测与饮食", exact: true }).click();
  await expect(page.getByText("2.05 kg · 主人实测", { exact: true })).toBeVisible();
});

test("a family guest reads the twin overview without unavailable write interactions", async ({ page, browser, baseURL }) => {
  await start(page);
  await mutate(page, "/api/home/pets/mochi/notes", { text: "喜欢蓝色软球", scope: "preference", activity: "play" });
  const invitation = await mutate(page, "/api/family/invitations", { role: "guest", expires_in_hours: 24, max_uses: 1 });
  const context = await browser.newContext({ baseURL, timezoneId: "Asia/Shanghai" });
  await context.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  const guest = await context.newPage();
  try {
    await register(guest);
    await guest.getByLabel("邀请口令", { exact: true }).fill(invitation.token);
    await guest.getByRole("button", { name: "加入家庭", exact: true }).click();
    await guest.getByRole("button", { name: "访问宠物分身", exact: true }).click();
    await expect(guest.getByText("当前为家庭访客，可查看个体资料；提问、记忆纠正和安排照护需照护成员权限。", { exact: true })).toBeVisible();
    await expect(guest.getByRole("button", { name: "询问分身", exact: true })).toHaveCount(0);
    await expect(guest.getByRole("button", { name: "建立待确认方案", exact: true })).toHaveCount(0);
    await expect(guest.getByRole("button", { name: "保存候选记忆", exact: true })).toHaveCount(0);
    await expect(guest.locator(".fa-context-overview")).toContainText("喜欢蓝色软球");
    expect(await guest.evaluate(async () => {
      const me = await (await fetch("/api/family/me")).json();
      return (await fetch("/api/family/pets/mochi/chat", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify({ text: "它喜欢什么", entry: "app" }) })).status;
    })).toBe(403);
  } finally { await context.close(); }
});
