import { test, expect, type Page } from "@playwright/test";

declare const process: { env: Record<string, string | undefined> };
const recordDemo = process.env.PAWTWIN_RECORD_DEMO === "1";
const demoPassword = "rehearsal-only-password";
test.use({ timezoneId: "Asia/Shanghai" });

async function register(page: Page, suffix: string, label: string) {
  await page.goto("/#app");
  if (recordDemo) {
    // Mask temporary invitation tokens in footage without changing API data.
    await page.addStyleTag({ content: 'input[name="token"], input[readonly] { color: transparent !important; text-shadow: none !important; }' });
  }
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  const username = `demo-${Date.now()}-${suffix}`;
  await page.getByLabel("账号名").fill(username);
  await page.getByLabel("密码", { exact: true }).fill(demoPassword);
  await page.getByLabel("昵称").fill(label);
  await page.getByRole("button", { name: "注册并登录" }).click();
  await expect(page.getByRole("heading", { name: "建立一个家庭" })).toBeVisible();
  return username;
}

async function nav(page: Page, name: string) {
  const displayName = name === "助手" ? "分身" : name === "小屋" ? "今日" : name;
  await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name: displayName, exact: true }).click();
}

test("demonstration rehearses two family accounts, real report arithmetic and shared memory to care", async ({ page: owner, browser, baseURL }, info) => {
  // Fourteen readable presentation holds add 22.4s only when recording.
  // Assertions and retries retain the normal suite settings.
  if (recordDemo) test.setTimeout(60_000);
  const started = Date.now();
  const day = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai" }).format(new Date());
  const dailyHeading = new RegExp(`^日报 · ${day.split("-").map(Number).join("/")} `);
  const weeklyHeading = /^周报 · 2026\/9\/28 /;
  const shots: { file: string; role: string; test_elapsed_ms: number; url: string }[] = [];
  const otherContext = await browser.newContext({
    baseURL, timezoneId: "Asia/Shanghai", viewport: { width: 1280, height: 800 },
    ...(recordDemo ? { recordVideo: { dir: info.outputPath("carer-video"), size: { width: 1280, height: 800 } } } : {}),
  });
  await otherContext.addInitScript(() => localStorage.setItem("pawtwin-language", "zh"));
  const carer = await otherContext.newPage();
  const capture = async (page: Page, name: string) => {
    if (recordDemo) {
      const focus = name === "00-product" ? page.locator(".pt-hero")
        : name === "01-home" ? page.getByRole("heading", { name: "家里的日常", exact: true })
        : name === "02-growth" ? page.locator("article").filter({ has: page.getByRole("heading", { name: weeklyHeading }) })
        : name === "05-daily" ? page.locator("article").filter({ has: page.getByRole("heading", { name: dailyHeading }) })
        : name === "07-completing-actor" ? page.getByRole("heading", { name: "最近家庭动态", exact: true })
        : name === "08-memory-confirmed" ? page.getByText(/主人已确认/).first()
        : name === "09-alexa-draft" ? page.getByRole("region", { name: "待确认照护草案" })
        : name === "10-alexa-pending" ? page.getByRole("region", { name: "待确认照护方案" })
        : name === "11-alexa-confirmed" ? page.getByRole("region", { name: "照护结果" })
        : ["03-assistant", "06-deleted-memory", "12-alexa-result", "13-alexa-new-session"].includes(name) ? page.getByRole("article", { name: "Alexa 分身回复" }).last()
        : page.getByRole("heading", { name: "陪 Mochi 玩耍", exact: true });
      await focus.scrollIntoViewIfNeeded();
      // A presentation hold for readable raw footage, not an assertion/retry delay.
      await page.waitForTimeout(1600);
    }
    const path = info.outputPath(`${name}.png`);
    shots.push({ file: `${name}.png`, role: page === owner ? "owner" : "carer", test_elapsed_ms: Date.now() - started, url: page.url() });
    await page.screenshot({ path, fullPage: !recordDemo });
    await info.attach(`${name}.png`, { path, contentType: "image/png" });
  };
  const ask = async (page: Page, text = "它喜欢什么") => {
    await page.getByLabel("模拟口述内容").fill(text);
    const pending = page.waitForResponse(r => r.url().endsWith("/api/family/pets/mochi/chat") && r.request().method() === "POST");
    await page.getByRole("button", { name: "发送给 Alexa 模拟器", exact: true }).click();
    const response = await pending;
    expect(response.ok()).toBe(true);
    const reply = await response.json();
    expect(reply.backend).toBe("local_rules");
    expect(reply.request_id).toBeNull();
    expect(reply.action_executed).toBe(false);
    expect(reply.entry).toBe("alexa_simulator");
    await expect(page.getByRole("article", { name: "Alexa 分身回复" }).last()).toContainText(reply.answer);
    await expect(page.getByRole("button", { name: "新会话", exact: true })).toBeEnabled();
    return reply;
  };
  try {
    await owner.goto("/");
    await expect(owner.locator(".pt-nav").getByRole("link", { name: "进入应用", exact: true })).toBeVisible();
    await capture(owner, "00-product");
    await register(owner, "owner", "展示主人");
    await owner.getByLabel("家庭名称").fill("Mochi 的演示家庭");
    await owner.getByRole("button", { name: "创建家庭", exact: true }).click();
    await expect(owner.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
    await capture(owner, "01-home");

    await nav(owner, "家庭");
    await owner.getByRole("button", { name: "生成家庭邀请" }).click();
    const token = await owner.getByLabel(/新邀请口令/).inputValue();
    expect(token.length).toBeGreaterThan(20);
    const carerUsername = await register(carer, "carer", "家人小林");
    await carer.getByLabel("邀请口令", { exact: true }).fill(token);
    await carer.getByRole("button", { name: "加入家庭", exact: true }).click();
    await nav(carer, "家庭");
    await carer.getByLabel("家庭称呼").fill("爸爸");
    await carer.getByRole("button", { name: "保存个人设置" }).click();
    await expect(carer.getByRole("button", { name: "保存个人设置" })).toBeEnabled();
    const member = await (await carer.request.get("/api/family/me")).json();
    expect(member.membership.role).toBe("carer");
    await expect(carer.getByText("邀请和权限由家庭管理员管理。")).toBeVisible();
    await carer.goto("/#alexa");
    const before = await ask(carer);
    expect(before.answer).toContain("还没有已确认的偏好记忆");

    await nav(owner, "成长");
    for (const fact of [{ value: "1.20", at: "2026-09-25T12:00" }, { value: "1.35", at: "2026-10-02T12:00" }]) {
      await owner.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "实测与饮食", exact: true }).click();
      await owner.getByLabel("测量数值").fill(fact.value);
      await owner.getByLabel("测量时间").fill(fact.at);
      await owner.getByLabel("资料来源").selectOption("demo_sample");
      await owner.getByRole("button", { name: "保存成长记录" }).click();
      await expect(owner.getByRole("button", { name: "保存成长记录" })).toBeEnabled();
    }
    await owner.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "报告", exact: true }).click();
    await owner.getByLabel("统计日期").fill("2026-10-02");
    await owner.getByRole("button", { name: "生成周报", exact: true }).click();
    const weeklyCard = owner.locator("article").filter({ has: owner.getByRole("heading", { name: weeklyHeading }) });
    await expect(weeklyCard.getByText("体重变化 150 g / 12.5% · 实际跨度 7 天", { exact: true })).toBeVisible();
    await expect(weeklyCard.getByText("实际摄入：未记录 · 记录出粮：未记录", { exact: true })).toBeVisible();
    const reports = await (await owner.request.get("/api/family/pets/mochi/reports")).json();
    const weekly = reports.reports.find((r: { period: string; date: string; status: string }) => r.period === "weekly" && r.date === "2026-10-02" && r.status === "current");
    expect(weekly.weight).toMatchObject({ change_g: 150, change_percent: 12.5, span_days: 7 });
    expect(weekly.source_record_ids.length).toBeGreaterThanOrEqual(2);
    await weeklyCard.getByText("统计依据与版本", { exact: true }).click();
    for (const id of weekly.source_record_ids) await expect(weeklyCard).toContainText(id);
    await capture(owner, "02-growth");

    await nav(owner, "助手");
    await owner.getByLabel("偏好原文").fill("喜欢羽毛棒，饭后先休息");
    await owner.getByRole("button", { name: "保存候选记忆" }).click();
    await expect(owner.getByRole("button", { name: "确认记忆", exact: true })).toBeVisible();
    const candidate = await ask(carer);
    expect(candidate.answer).not.toContain("喜欢羽毛棒，饭后先休息");
    await owner.getByRole("button", { name: "确认记忆", exact: true }).click();
    await expect(owner.getByText(/主人已确认/)).toBeVisible();
    await capture(owner, "08-memory-confirmed");
    const memories = await (await owner.request.get("/api/family/pets/mochi/memories")).json();
    const confirmedMemory = memories.memories.find((m: { text: string }) => m.text === "喜欢羽毛棒，饭后先休息");
    // Logout and login create a new authenticated session, beyond a page refresh.
    await carer.getByRole("button", { name: "退出账号", exact: true }).click();
    await carer.getByRole("button", { name: "已有账号，去登录", exact: true }).click();
    await expect(carer.getByRole("heading", { name: "独立账号登录" })).toBeVisible();
    await carer.getByLabel("账号名").fill(carerUsername);
    await carer.getByLabel("密码", { exact: true }).fill(demoPassword);
    await carer.getByRole("button", { name: "登录账号", exact: true }).click();
    await expect(carer.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
    await carer.goto("/#alexa");
    const reused = await ask(carer);
    expect(reused.source_record_ids).toContain(confirmedMemory.id);
    const replyCard = carer.getByRole("article", { name: "Alexa 分身回复" }).last();
    await expect(replyCard).toContainText("喜欢羽毛棒，饭后先休息");
    await replyCard.getByText(/查看这轮依据/).click();
    await expect(replyCard).toContainText(confirmedMemory.id);
    await capture(carer, "03-assistant");
    await carer.getByRole("button", { name: "新会话", exact: true }).click();
    await expect(carer.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
    const newSessionReply = await ask(carer);
    expect(newSessionReply.source_record_ids).toContain(confirmedMemory.id);
    await capture(carer, "13-alexa-new-session");

    await owner.goto("/#alexa");
    const draft = await ask(owner, "安排陪玩");
    expect(draft.care_draft).toMatchObject({ kind: "play", title: "陪 Mochi 玩耍" });
    await expect(owner.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
    const due = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(Date.now() - 60_000)).replace(" ", "T");
    await owner.getByLabel("草案照护时间").fill(due);
    await capture(owner, "09-alexa-draft");
    const preparing = owner.waitForResponse(r => r.url().endsWith("/api/family/pets/mochi/proposals") && r.request().method() === "POST");
    await owner.getByRole("button", { name: "准备待确认方案", exact: true }).click();
    const proposalResponse = await preparing;
    expect(proposalResponse.ok()).toBe(true);
    const proposal = await proposalResponse.json();
    await expect(owner.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
    let home = await (await owner.request.get("/api/home/state")).json();
    expect(home.tasks.some((t: { title: string }) => t.title === draft.care_draft.title)).toBe(false);
    await capture(owner, "10-alexa-pending");
    const confirming = owner.waitForResponse(r => r.url().endsWith(`/proposals/${proposal.id}/confirm`) && r.request().method() === "POST");
    await owner.getByRole("button", { name: "确认安排人工照护", exact: true }).click();
    const confirmedResponse = await confirming;
    expect(confirmedResponse.ok()).toBe(true);
    const confirmedProposal = await confirmedResponse.json();
    await expect(owner.getByRole("region", { name: "照护结果" })).toContainText("已安排，等待人工完成");
    await capture(owner, "11-alexa-confirmed");
    await carer.goto("/#app");
    await nav(carer, "照护");
    await carer.getByRole("button", { name: "同步最新记录" }).click();
    const taskCard = carer.locator("article").filter({ has: carer.getByRole("heading", { name: draft.care_draft.title, exact: true }) });
    await expect(taskCard).toBeVisible();
    await expect(taskCard).toContainText("陪玩");
    await taskCard.getByRole("button", { name: "领取", exact: true }).click();
    await expect(taskCard).toContainText(`领取人：${member.user.display_name}`);
    await taskCard.getByRole("button", { name: "完成照护", exact: true }).click();
    await carer.getByRole("button", { name: "已完成", exact: true }).click();
    await expect(taskCard).toContainText("已完成");
    await capture(carer, "04-care");
    home = await (await owner.request.get("/api/home/state")).json();
    const completed = home.occurrences.find((o: { task_id: string }) => o.task_id === confirmedProposal.task_id);
    expect(completed.completed_by).toBe(member.user.user_id);
    expect(completed.source).toBe("manual_care");
    await nav(carer, "家庭");
    const historyCard = carer.locator("article.fa-record").filter({ hasText: `完成：${draft.care_draft.title}` });
    await expect(historyCard).toContainText(member.user.display_name);
    await capture(carer, "07-completing-actor");
    await carer.goto("/#alexa");
    const resultReply = await ask(carer, "最近完成了什么");
    expect(resultReply.answer).toContain(draft.care_draft.title);
    expect(resultReply.answer).toContain("人工完成记录");
    expect(resultReply.source_record_ids).toContain(completed.id);
    await capture(carer, "12-alexa-result");

    await owner.goto("/#app");
    await nav(owner, "成长");
    await owner.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "报告", exact: true }).click();
    await owner.getByLabel("统计日期").fill(day);
    await owner.getByRole("button", { name: "生成日报", exact: true }).click();
    const dailyCard = owner.locator("article").filter({ has: owner.getByRole("heading", { name: dailyHeading }) });
    await expect(dailyCard).toContainText("人工照护完成 1 次");
    await capture(owner, "05-daily");
    const dailyReports = await (await owner.request.get("/api/family/pets/mochi/reports")).json();
    const daily = dailyReports.reports.find((r: { period: string; date: string; status: string }) => r.period === "daily" && r.date === day && r.status === "current");

    await nav(owner, "助手");
    await owner.getByRole("button", { name: "删除记忆", exact: true }).click();
    await expect(owner.getByRole("button", { name: "删除记忆", exact: true })).toHaveCount(0);
    await carer.goto("/#alexa");
    await carer.getByRole("button", { name: "新会话", exact: true }).click();
    const deleted = await ask(carer);
    const after = carer.getByRole("article", { name: "Alexa 分身回复" }).last();
    await expect(after).not.toContainText("喜欢羽毛棒，饭后先休息");
    await expect(after).toContainText("还没有已确认的偏好记忆");
    expect(deleted.source_record_ids).not.toContain(confirmedMemory.id);
    await expect(carer.getByText("本地独立账号 · 云认证未接通")).toBeVisible();
    await capture(carer, "06-deleted-memory");
    await info.attach("demo-evidence", {
      body: JSON.stringify({
        schema_version: 2, captured_at: new Date().toISOString(),
        source: "actual_local_ui_and_api", identity_backend: "local_account",
        backend: "local_rules", cloud_calls: 0, pet_id: "mochi",
        shared_memory: { memory_id: confirmedMemory.id, before, candidate, confirmed_in_new_login: reused, confirmed_in_new_page_session: newSessionReply, after_deletion: deleted },
        alexa_care: { draft, proposal, confirmed_proposal: confirmedProposal, result_reply: resultReply },
        screenshots: shots,
        timing_boundary: "Screenshot timestamps are test elapsed wall-clock milliseconds, not WebM seek positions. The edit uses complete actual screenshots and generates its own exact encoded timeline; no guessed replay cuts.",
        weekly_report: weekly, daily_report: daily,
        manual_care: { occurrence_id: completed.id, source: completed.source, completed_by: completed.completed_by, expected_actor_id: member.user.user_id },
        boundaries: ["demo_sample measurements", "owner-confirmed database memory", "independent Alexa web simulation", "rule draft with explicit manual-care confirmation", "no live model or hardware"],
      }, null, 2), contentType: "application/json",
    });
  } finally {
    await otherContext.close();
    if (recordDemo) {
      await owner.context().close();
      for (const [role, page] of [["owner", owner], ["carer", carer]] as const) {
        const video = page.video();
        if (video) await info.attach(`${role}-recording`, { path: await video.path(), contentType: "video/webm" });
      }
    }
  }
});
