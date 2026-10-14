# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: demo-rehearsal.spec.ts >> demonstration rehearses two family accounts, real report arithmetic and shared memory to care
- Location: frontend\e2e\demo-rehearsal.spec.ts:28:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('article').filter({ has: getByRole('heading', { name: /^日报 ·/ }) })
Expected substring: "人工照护完成 1 次"
Received string:    "日报 · 2026/10/12 00:00 — 2026/10/13 00:00人工照护完成1次待办0逾期0至少需要两次有效测量实际摄入：未记录 · 记录出粮：未记录统计依据与版本截止 2026/10/12 16:03 · 版本 9实测体重 · 1.35 kg · 2026/10/2 12:00 · 演示样本源记录 29f5a9c8-80cb-416a-a2ca-dbd2a300a622 · 版本 1家庭记录 · 家人小林 · 领取：陪 Mochi 玩耍 · 2026/10/12 16:03源记录 0c79e08f-c8d1-470d-83dd-b5c83ef9673a · 版本 1家庭记录 · 家人小林 · 完成：陪 Mochi 玩耍 · 2026/10/12 16:03源记录 f29d3f3d-4f0f-4638-afe8-cacad7326a8e · 版本 1人工照护完成 · 2026/10/12 16:03 · 家人小林源记录 da971237-ad7e-424e-b54b-0a16b51e7f0f · 版本 1模拟设备：未连接；模拟出粮 未记录。出粮不代表实际摄入。"
Timeout: 20000ms

Call log:
  - Expect "toContainText" locator('article').filter({ has: getByRole('heading', { name: /^日报 ·/ }) }) with timeout 20000ms
  - waiting for locator('article').filter({ has: getByRole('heading', { name: /^日报 ·/ }) })
    42 × locator resolved to <article class="fa-report-card">…</article>
       - unexpected value "日报 · 2026/10/12 00:00 — 2026/10/13 00:00人工照护完成1次待办0逾期0至少需要两次有效测量实际摄入：未记录 · 记录出粮：未记录统计依据与版本截止 2026/10/12 16:03 · 版本 9实测体重 · 1.35 kg · 2026/10/2 12:00 · 演示样本源记录 29f5a9c8-80cb-416a-a2ca-dbd2a300a622 · 版本 1家庭记录 · 家人小林 · 领取：陪 Mochi 玩耍 · 2026/10/12 16:03源记录 0c79e08f-c8d1-470d-83dd-b5c83ef9673a · 版本 1家庭记录 · 家人小林 · 完成：陪 Mochi 玩耍 · 2026/10/12 16:03源记录 f29d3f3d-4f0f-4638-afe8-cacad7326a8e · 版本 1人工照护完成 · 2026/10/12 16:03 · 家人小林源记录 da971237-ad7e-424e-b54b-0a16b51e7f0f · 版本 1模拟设备：未连接；模拟出粮 未记录。出粮不代表实际摄入。"

```

```yaml
- article:
  - heading "日报 · 2026/10/12 00:00 — 2026/10/13 00:00" [level=3]
  - text: 人工照护完成
  - strong: 1次
  - text: 待办
  - strong: "0"
  - text: 逾期
  - strong: "0"
  - paragraph: 至少需要两次有效测量
  - paragraph: 实际摄入：未记录 · 记录出粮：未记录
  - group: 统计依据与版本
  - paragraph: 模拟设备：未连接；模拟出粮 未记录。出粮不代表实际摄入。
```

# Test source

```ts
  113 |     await owner.getByRole("button", { name: "生成周报", exact: true }).click();
  114 |     await expect(owner.getByText("体重变化 150 g / 12.5% · 实际跨度 7 天", { exact: true })).toBeVisible();
  115 |     await expect(owner.getByText("实际摄入：未记录 · 记录出粮：未记录", { exact: true })).toBeVisible();
  116 |     const reports = await (await owner.request.get("/api/family/pets/mochi/reports")).json();
  117 |     const weekly = reports.reports.find((r: { period: string; status: string }) => r.period === "weekly" && r.status === "current");
  118 |     expect(weekly.weight).toMatchObject({ change_g: 150, change_percent: 12.5, span_days: 7 });
  119 |     expect(weekly.source_record_ids.length).toBeGreaterThanOrEqual(2);
  120 |     const weeklyCard = owner.locator("article").filter({ has: owner.getByRole("heading", { name: /^周报 ·/ }) });
  121 |     await weeklyCard.getByText("统计依据与版本", { exact: true }).click();
  122 |     for (const id of weekly.source_record_ids) await expect(weeklyCard).toContainText(id);
  123 |     await capture(owner, "02-growth");
  124 | 
  125 |     await nav(owner, "助手");
  126 |     await owner.getByLabel("偏好原文").fill("喜欢羽毛棒，饭后先休息");
  127 |     await owner.getByRole("button", { name: "保存候选记忆" }).click();
  128 |     await expect(owner.getByRole("button", { name: "确认记忆", exact: true })).toBeVisible();
  129 |     const candidate = await ask(carer);
  130 |     expect(candidate.answer).not.toContain("喜欢羽毛棒，饭后先休息");
  131 |     await owner.getByRole("button", { name: "确认记忆", exact: true }).click();
  132 |     await expect(owner.getByText(/主人已确认/)).toBeVisible();
  133 |     await capture(owner, "08-memory-confirmed");
  134 |     const memories = await (await owner.request.get("/api/family/pets/mochi/memories")).json();
  135 |     const confirmedMemory = memories.memories.find((m: { text: string }) => m.text === "喜欢羽毛棒，饭后先休息");
  136 |     // Logout and login create a new authenticated session, beyond a page refresh.
  137 |     await carer.getByRole("button", { name: "退出账号", exact: true }).click();
  138 |     await carer.getByRole("button", { name: "已有账号，去登录", exact: true }).click();
  139 |     await expect(carer.getByRole("heading", { name: "独立账号登录" })).toBeVisible();
  140 |     await carer.getByLabel("账号名").fill(carerUsername);
  141 |     await carer.getByLabel("密码", { exact: true }).fill(demoPassword);
  142 |     await carer.getByRole("button", { name: "登录账号", exact: true }).click();
  143 |     await expect(carer.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
  144 |     await carer.goto("/#alexa");
  145 |     const reused = await ask(carer);
  146 |     expect(reused.source_record_ids).toContain(confirmedMemory.id);
  147 |     const replyCard = carer.getByRole("article", { name: "Alexa 分身回复" }).last();
  148 |     await expect(replyCard).toContainText("喜欢羽毛棒，饭后先休息");
  149 |     await replyCard.getByText(/查看这轮依据/).click();
  150 |     await expect(replyCard).toContainText(confirmedMemory.id);
  151 |     await capture(carer, "03-assistant");
  152 |     await carer.getByRole("button", { name: "新会话", exact: true }).click();
  153 |     await expect(carer.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
  154 |     const newSessionReply = await ask(carer);
  155 |     expect(newSessionReply.source_record_ids).toContain(confirmedMemory.id);
  156 |     await capture(carer, "13-alexa-new-session");
  157 | 
  158 |     await owner.goto("/#alexa");
  159 |     const draft = await ask(owner, "安排陪玩");
  160 |     expect(draft.care_draft).toMatchObject({ kind: "play", title: "陪 Mochi 玩耍" });
  161 |     await expect(owner.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  162 |     const due = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(Date.now() - 60_000)).replace(" ", "T");
  163 |     await owner.getByLabel("草案照护时间").fill(due);
  164 |     await capture(owner, "09-alexa-draft");
  165 |     const preparing = owner.waitForResponse(r => r.url().endsWith("/api/family/pets/mochi/proposals") && r.request().method() === "POST");
  166 |     await owner.getByRole("button", { name: "准备待确认方案", exact: true }).click();
  167 |     const proposalResponse = await preparing;
  168 |     expect(proposalResponse.ok()).toBe(true);
  169 |     const proposal = await proposalResponse.json();
  170 |     await expect(owner.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
  171 |     let home = await (await owner.request.get("/api/home/state")).json();
  172 |     expect(home.tasks.some((t: { title: string }) => t.title === draft.care_draft.title)).toBe(false);
  173 |     await capture(owner, "10-alexa-pending");
  174 |     const confirming = owner.waitForResponse(r => r.url().endsWith(`/proposals/${proposal.id}/confirm`) && r.request().method() === "POST");
  175 |     await owner.getByRole("button", { name: "确认安排人工照护", exact: true }).click();
  176 |     const confirmedResponse = await confirming;
  177 |     expect(confirmedResponse.ok()).toBe(true);
  178 |     const confirmedProposal = await confirmedResponse.json();
  179 |     await expect(owner.getByRole("region", { name: "照护结果" })).toContainText("已安排，等待人工完成");
  180 |     await capture(owner, "11-alexa-confirmed");
  181 |     await carer.goto("/#app");
  182 |     await nav(carer, "照护");
  183 |     await carer.getByRole("button", { name: "同步最新记录" }).click();
  184 |     const taskCard = carer.locator("article").filter({ has: carer.getByRole("heading", { name: draft.care_draft.title, exact: true }) });
  185 |     await expect(taskCard).toBeVisible();
  186 |     await expect(taskCard).toContainText("陪玩");
  187 |     await taskCard.getByRole("button", { name: "领取", exact: true }).click();
  188 |     await expect(taskCard).toContainText("已领取");
  189 |     await taskCard.getByRole("button", { name: "完成照护", exact: true }).click();
  190 |     await expect(taskCard).toContainText("已完成");
  191 |     await capture(carer, "04-care");
  192 |     home = await (await owner.request.get("/api/home/state")).json();
  193 |     const completed = home.occurrences.find((o: { task_id: string }) => o.task_id === confirmedProposal.task_id);
  194 |     expect(completed.completed_by).toBe(member.user.user_id);
  195 |     expect(completed.source).toBe("manual_care");
  196 |     await nav(carer, "家庭");
  197 |     const historyCard = carer.locator("article.fa-record").filter({ hasText: `完成：${draft.care_draft.title}` });
  198 |     await expect(historyCard).toContainText(member.user.display_name);
  199 |     await capture(carer, "07-completing-actor");
  200 |     await carer.goto("/#alexa");
  201 |     const resultReply = await ask(carer, "最近完成了什么");
  202 |     expect(resultReply.answer).toContain(draft.care_draft.title);
  203 |     expect(resultReply.answer).toContain("人工完成记录");
  204 |     expect(resultReply.source_record_ids).toContain(completed.id);
  205 |     await capture(carer, "12-alexa-result");
  206 | 
  207 |     await owner.goto("/#app");
  208 |     await nav(owner, "成长");
  209 |     const day = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Shanghai" }).format(new Date());
  210 |     await owner.getByLabel("统计日期").fill(day);
  211 |     await owner.getByRole("button", { name: "生成日报", exact: true }).click();
  212 |     const dailyCard = owner.locator("article").filter({ has: owner.getByRole("heading", { name: /^日报 ·/ }) });
> 213 |     await expect(dailyCard).toContainText("人工照护完成 1 次");
      |                             ^ Error: expect(locator).toContainText(expected) failed
  214 |     await capture(owner, "05-daily");
  215 |     const dailyReports = await (await owner.request.get("/api/family/pets/mochi/reports")).json();
  216 |     const daily = dailyReports.reports.find((r: { period: string; date: string; status: string }) => r.period === "daily" && r.date === day && r.status === "current");
  217 | 
  218 |     await nav(owner, "助手");
  219 |     await owner.getByRole("button", { name: "删除记忆", exact: true }).click();
  220 |     await expect(owner.getByRole("button", { name: "删除记忆", exact: true })).toHaveCount(0);
  221 |     await carer.goto("/#alexa");
  222 |     await carer.getByRole("button", { name: "新会话", exact: true }).click();
  223 |     const deleted = await ask(carer);
  224 |     const after = carer.getByRole("article", { name: "Alexa 分身回复" }).last();
  225 |     await expect(after).not.toContainText("喜欢羽毛棒，饭后先休息");
  226 |     await expect(after).toContainText("还没有已确认的偏好记忆");
  227 |     expect(deleted.source_record_ids).not.toContain(confirmedMemory.id);
  228 |     await expect(carer.getByText("本地独立账号 · 云认证未接通")).toBeVisible();
  229 |     await capture(carer, "06-deleted-memory");
  230 |     await info.attach("demo-evidence", {
  231 |       body: JSON.stringify({
  232 |         schema_version: 2, captured_at: new Date().toISOString(),
  233 |         source: "actual_local_ui_and_api", identity_backend: "local_account",
  234 |         backend: "local_rules", cloud_calls: 0, pet_id: "mochi",
  235 |         shared_memory: { memory_id: confirmedMemory.id, before, candidate, confirmed_in_new_login: reused, confirmed_in_new_page_session: newSessionReply, after_deletion: deleted },
  236 |         alexa_care: { draft, proposal, confirmed_proposal: confirmedProposal, result_reply: resultReply },
  237 |         screenshots: shots,
  238 |         timing_boundary: "Screenshot timestamps are test elapsed wall-clock milliseconds, not WebM seek positions. The edit uses complete actual screenshots and generates its own exact encoded timeline; no guessed replay cuts.",
  239 |         weekly_report: weekly, daily_report: daily,
  240 |         manual_care: { occurrence_id: completed.id, source: completed.source, completed_by: completed.completed_by, expected_actor_id: member.user.user_id },
  241 |         boundaries: ["demo_sample measurements", "owner-confirmed database memory", "independent Alexa web simulation", "rule draft with explicit manual-care confirmation", "no live model or hardware"],
  242 |       }, null, 2), contentType: "application/json",
  243 |     });
  244 |   } finally {
  245 |     await otherContext.close();
  246 |     if (recordDemo) {
  247 |       await owner.context().close();
  248 |       for (const [role, page] of [["owner", owner], ["carer", carer]] as const) {
  249 |         const video = page.video();
  250 |         if (video) await info.attach(`${role}-recording`, { path: await video.path(), contentType: "video/webm" });
  251 |       }
  252 |     }
  253 |   }
  254 | });
  255 | 
```