// Fresh English UI capture. Never uses the user's existing database or cloud.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const repo = path.resolve(__dirname, '../../../../');
const { chromium, expect } = require(path.join(repo, 'frontend/node_modules/@playwright/test'));
const attempt = process.env.PAWTWIN_CAPTURE_ATTEMPT || `attempt-${new Date().toISOString().replace(/\D/g, '').slice(0, 17)}`;
if (!/^[a-zA-Z0-9_-]+$/.test(attempt)) throw new Error('Capture attempt must be a simple directory name');
const out = path.join(repo, 'docs/evidence/hackathon-capture/2026-10-15-english', attempt);
const baseURL = 'http://127.0.0.1:8845';
const browserExe = 'C:\\Users\\11831\\AppData\\Local\\ms-playwright\\chromium-1194\\chrome-win\\chrome.exe';
if (fs.existsSync(path.join(out, 'demo-evidence.json'))) throw new Error('This attempt already has evidence. Use a fresh PAWTWIN_CAPTURE_ATTEMPT to preserve originals.');
fs.mkdirSync(out, { recursive: true });
const dictionaries = {};
for (const file of ['base-messages.ts', 'showcase-messages.ts', 'family-messages.ts', 'support-messages.ts', 'server-messages.ts']) {
  const src = fs.readFileSync(path.join(repo, 'frontend/src', file), 'utf8');
  Object.assign(dictionaries, Function('return (' + src.slice(src.indexOf('{')).replace(/;\s*$/, '') + ')')());
}
const en = text => dictionaries[text] || text;
const button = (page, zh) => page.getByRole('button', { name: en(zh), exact: true });
const label = (page, zh) => page.getByLabel(en(zh), { exact: true });
const heading = (page, text) => page.getByRole('heading', { name: text, exact: true });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const data = { schema_version: 2, captured_at: new Date().toISOString(), source: 'actual_local_ui_and_api', identity_backend: 'local_account', backend: 'local_rules', cloud_calls: 0, pet_id: 'mochi', screenshots: [], recordings: {}, staging: [], checks: [] };
const origins = new Map();
const roles = new Map();
const contexts = [];
let browser, service;
const serverLog = fs.openSync(path.join(out, 'server.log'), 'w');
function safeURL(url) { return url.replace(/#pet-access=.*/, '#pet-access=[redacted]'); }
async function api(page, route) {
  const response = await page.request.get(route);
  assert(response.ok(), `${route}: ${response.status()} ${await response.text()}`);
  return response.json();
}
async function change(page, route, body, method = 'POST') {
  return page.evaluate(async ({ route, body, method }) => {
    const meResponse = await fetch('/api/family/me');
    if (!meResponse.ok) throw new Error('Failed to read the local authenticated session');
    const me = await meResponse.json();
    const response = await fetch(route, { method, headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': me.csrf_token }, body: JSON.stringify(body) });
    if (!response.ok) throw new Error(`${route}: ${response.status} ${await response.text()}`);
    return response.json();
  }, { route, body, method });
}
async function makePage(role) {
  const context = await browser.newContext({ baseURL, timezoneId: 'Asia/Shanghai', viewport: { width: 1280, height: 720 }, recordVideo: { dir: path.join(out, `raw-${role}`), size: { width: 1280, height: 720 } } });
  contexts.push(context);
  await context.addInitScript(() => {
    localStorage.setItem('pawtwin-language', 'en');
    const protect = () => {
      if (!document.documentElement || document.getElementById('capture-secret-mask')) return;
      const style = document.createElement('style'); style.id = 'capture-secret-mask';
      style.textContent = 'input[name="token"], input[readonly], input[type="password"] { color: transparent !important; text-shadow: none !important; caret-color: transparent !important; }';
      document.documentElement.appendChild(style);
    };
    new MutationObserver(protect).observe(document, { childList: true, subtree: true }); protect();
  });
  const before = Date.now();
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const after = Date.now();
  origins.set(page, before); roles.set(page, role);
  data.recordings[role] = { video: `${role}.webm`, recording_origin_before_new_page_utc: new Date(before).toISOString(), recording_origin_after_new_page_utc: new Date(after).toISOString(), origin_uncertainty_ms: after - before, first_blank_hold_ms: 600, timing_note: 'Raw WebM starts with the first blank page. Elapsed ranges are role-specific wall clock since before newPage; visually calibrate the small startup uncertainty against raw frames.' };
  await page.waitForTimeout(600);
  return page;
}
async function capture(page, file, focus) {
  if (focus) await focus.scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  const before = Date.now() - origins.get(page);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(out, `${file}.png`), fullPage: false });
  await page.waitForTimeout(2500);
  const after = Date.now() - origins.get(page);
  const text = await page.locator('body').innerText();
  const cjk = text.match(/[\u3400-\u9fff]+/g) || [];
  const unexpectedCjk = cjk.filter(value => value !== '中文');
  data.screenshots.push({ file: `${file}.png`, role: roles.get(page), url: safeURL(page.url()), raw_video_elapsed_hold_ms: { start: before, screenshot: before + 2500, end: after }, suggested_clip_ms: { start: Math.max(0, before - 600), end: after }, cjk_text_except_language_toggle: unexpectedCjk });
  console.log(`Captured ${file} (${roles.get(page)}) at ${before}..${after} ms`);
}
async function nav(page, zh) { const name = zh === '助手' ? '分身' : zh === '小屋' ? '今日' : zh; await page.getByRole('navigation', { name: en('App 主导航') }).getByRole('button', { name: en(name), exact: true }).click(); }
async function register(page, role, name) {
  await page.goto('/#app'); await button(page, '创建本地账号').click();
  const username = `english-demo-${Date.now()}-${role}`;
  await label(page, '账号名').fill(username); await label(page, '密码').fill('fictional-recording-password'); await label(page, '昵称').fill(name);
  await button(page, '注册并登录').click(); await expect(heading(page, en('建立一个家庭'))).toBeVisible();
  return username;
}
async function ask(page, prompt = 'What does my pet like?') {
  await label(page, '模拟口述内容').fill(prompt);
  const awaiting = page.waitForResponse(r => r.url().endsWith('/api/family/pets/mochi/chat') && r.request().method() === 'POST');
  await button(page, '发送给 Alexa 模拟器').click(); const response = await awaiting;
  assert(response.ok(), `chat failed: ${response.status()} ${await response.text()}`);
  const reply = await response.json();
  assert.equal(reply.backend, 'local_rules'); assert.equal(reply.request_id, null); assert.equal(reply.action_executed, false); assert.equal(reply.entry, 'alexa_simulator');
  await expect(page.getByRole('article', { name: en('Alexa 分身回复') }).last()).toBeVisible();
  await expect(button(page, '新会话')).toBeEnabled();
  return reply;
}
async function main() {
  service = spawn('C:\\Users\\11831\\.local\\bin\\uv.exe', ['run', '--frozen', 'uvicorn', 'pawtwin.main:create_app', '--factory', '--host', '127.0.0.1', '--port', '8845', '--no-proxy-headers', '--no-access-log'], { cwd: repo, windowsHide: true, stdio: ['ignore', serverLog, serverLog], env: { ...process.env, PAWTWIN_MODE: 'local', PAWTWIN_WORKER_MODE: 'background', PAWTWIN_MODEL_BACKEND: 'local_fake', PAWTWIN_DB_PATH: ':memory:', PAWTWIN_MEMORY_BACKEND: 'not_implemented', PAWTWIN_PHOTO_RECOGNITION_ENABLED: 'false', PAWTWIN_FAMILY_MODEL_BACKEND: 'local_rules' } });
  for (let attempt = 0; attempt < 120; attempt++) { if (service.exitCode !== null) throw new Error('isolated backend exited'); try { if ((await fetch(`${baseURL}/healthz`)).ok) break; } catch {} if (attempt === 119) throw new Error('isolated backend did not start'); await delay(500); }
  data.bootstrap = await (await fetch(`${baseURL}/api/bootstrap`)).json(); assert.equal(data.bootstrap.aws_connected, false);
  browser = await chromium.launch({ executablePath: browserExe, headless: true });
  const owner = await makePage('owner');
  await owner.goto('/'); await expect(owner.locator('.pt-nav').getByRole('link', { name: en('进入应用'), exact: true })).toBeVisible(); await capture(owner, '00-product', owner.locator('.pt-hero'));
  await register(owner, 'owner', 'Emma'); await label(owner, '家庭名称').fill('Mochi Family · Fictional Demo'); await button(owner, '创建家庭').click();
  await expect(owner.getByRole('navigation', { name: en('App 主导航') })).toBeVisible();
  // Name the fictional default belongings through the real local API; do not rewrite replies.
  const seed = await api(owner, '/api/home/state');
  for (const item of seed.objects || []) { const names = { nest: 'Window nook', toy: 'Feather toy', feeder: 'Simulated feeder', water: 'Water bowl' }; await change(owner, `/api/home/objects/${item.id}`, { kind: item.kind, name: names[item.kind], x: item.x, y: item.y, note: '' }, 'PUT'); }
  data.staging.push('Fictional seeded object names changed to English through the local API before capture.');
  await owner.reload(); await capture(owner, '01-home', owner.locator('.ph-room').first());
  await nav(owner, '家庭'); await button(owner, '生成家庭邀请').click(); const token = await owner.getByLabel(/^New invitation code/).inputValue(); assert(token.length > 20);
  const carer = await makePage('carer'); const carerUsername = await register(carer, 'carer', 'Alex'); await label(carer, '邀请口令').fill(token); await button(carer, '加入家庭').click();
  await nav(carer, '家庭'); await label(carer, '家庭称呼').fill('Dad'); await button(carer, '保存个人设置').click(); await expect(button(carer, '保存个人设置')).toBeEnabled();
  const member = await api(carer, '/api/family/me'); assert.equal(member.membership.role, 'carer');
  await carer.goto('/#alexa'); const before = await ask(carer); assert(before.answer.includes('还没有已确认的偏好记忆'));
  await nav(owner, '成长');
  for (const fact of [{ value: '1.20', at: '2026-09-25T12:00' }, { value: '1.35', at: '2026-10-02T12:00' }]) {
    await owner.getByRole('navigation', { name: en('成长分区') }).getByRole('button', { name: en('实测与饮食'), exact: true }).click();
    await label(owner, '测量数值').fill(fact.value); await owner.getByLabel('Measurement time', { exact: true }).fill(fact.at); await owner.locator('#family-measurement-form select[name="source"]').selectOption('demo_sample'); await button(owner, '保存成长记录').click(); await expect(button(owner, '保存成长记录')).toBeEnabled();
  }
  await owner.getByRole('navigation', { name: en('成长分区') }).getByRole('button', { name: en('报告'), exact: true }).click(); await label(owner, '统计日期').fill('2026-10-02'); await button(owner, '生成周报').click();
  const weekly = (await api(owner, '/api/family/pets/mochi/reports')).reports.find(r => r.period === 'weekly' && r.date === '2026-10-02' && r.status === 'current'); assert.equal(weekly.weight.change_g, 150); assert.equal(weekly.weight.change_percent, 12.5); assert.equal(weekly.weight.span_days, 7);
  const weeklyCard = owner.locator('article').filter({ has: owner.getByRole('heading', { name: /^Weekly report.*9\/28\/2026/ }) }); await expect(weeklyCard).toContainText('150 g'); await capture(owner, '02-growth', weeklyCard);
  await nav(owner, '助手'); const memoryText = 'Loves the feather toy. Rest after meals.'; await label(owner, '偏好原文').fill(memoryText); await button(owner, '保存候选记忆').click(); await expect(button(owner, '确认记忆')).toBeVisible();
  const candidate = await ask(carer); assert(!candidate.answer.includes(memoryText)); await button(owner, '确认记忆').click(); await expect(owner.getByText(/Emma.*Confirmed by owner/)).toBeVisible(); await capture(owner, '08-memory-confirmed', owner.getByText(/Emma.*Confirmed by owner/));
  const confirmedMemory = (await api(owner, '/api/family/pets/mochi/memories')).memories.find(m => m.text === memoryText); assert.equal(confirmedMemory.status, 'confirmed');
  await button(carer, '退出账号').click(); await button(carer, '已有账号，去登录').click(); await label(carer, '账号名').fill(carerUsername); await label(carer, '密码').fill('fictional-recording-password'); await button(carer, '登录账号').click(); await expect(carer.getByRole('navigation', { name: en('App 主导航') })).toBeVisible(); await carer.goto('/#alexa');
  const reused = await ask(carer); assert(reused.source_record_ids.includes(confirmedMemory.id)); const replyCard = carer.getByRole('article', { name: en('Alexa 分身回复') }).last(); await expect(replyCard).toContainText(memoryText); await replyCard.getByText(/View this turn’s sources/).click(); await capture(carer, '03-assistant', replyCard);
  await button(carer, '新会话').click(); await expect(carer.getByRole('article', { name: en('Alexa 分身回复') })).toHaveCount(0); const newSessionReply = await ask(carer); assert(newSessionReply.source_record_ids.includes(confirmedMemory.id)); await capture(carer, '13-alexa-new-session', carer.getByRole('article', { name: en('Alexa 分身回复') }).last());
  await owner.goto('/#alexa'); const draft = await ask(owner, 'plan playtime'); assert.equal(draft.care_draft.kind, 'play');
  const due = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(Date.now() - 60000)).replace(' ', 'T'); await label(owner, '草案照护时间').fill(due); await capture(owner, '09-alexa-draft', owner.getByRole('region', { name: en('待确认照护草案') }));
  const preparing = owner.waitForResponse(r => r.url().endsWith('/api/family/pets/mochi/proposals') && r.request().method() === 'POST'); await button(owner, '准备待确认方案').click(); const proposalResponse = await preparing; assert(proposalResponse.ok()); const proposal = await proposalResponse.json(); assert(!(await api(owner, '/api/home/state')).tasks.some(t => t.title === draft.care_draft.title)); await capture(owner, '10-alexa-pending', owner.getByRole('region', { name: en('待确认照护方案') }));
  const confirming = owner.waitForResponse(r => r.url().endsWith(`/proposals/${proposal.id}/confirm`) && r.request().method() === 'POST'); await button(owner, '确认安排人工照护').click(); const confirmedResponse = await confirming; assert(confirmedResponse.ok()); const confirmedProposal = await confirmedResponse.json(); await expect(owner.getByRole('region', { name: en('照护结果') })).toContainText(en('已安排，等待人工完成')); await capture(owner, '11-alexa-confirmed', owner.getByRole('region', { name: en('照护结果') }));
  await carer.goto('/#app/care'); await expect(button(carer, '同步最新记录')).toBeVisible(); await button(carer, '同步最新记录').click();
  let taskCard = carer.locator('article').filter({ has: heading(carer, draft.care_draft.title) }); await expect(taskCard).toBeVisible(); await taskCard.getByText(en('编辑或延期'), { exact: true }).click(); await taskCard.getByLabel(en('任务标题'), { exact: true }).fill('Playtime with Mochi'); await taskCard.getByRole('button', { name: en('保存任务编辑'), exact: true }).click();
  data.staging.push('Carer used the real Care UI to rename the server-generated rule title to Playtime with Mochi, before claiming and completing. The original rule title is preserved in proposal evidence.');
  taskCard = carer.locator('article').filter({ has: heading(carer, 'Playtime with Mochi') }); await expect(taskCard).toBeVisible(); await taskCard.getByRole('button', { name: en('领取'), exact: true }).click(); await expect(taskCard).toContainText('Alex'); await taskCard.getByRole('button', { name: en('完成照护'), exact: true }).click(); await button(carer, '已完成').click(); await expect(taskCard).toContainText(en('已完成')); await capture(carer, '04-care', taskCard);
  const home = await api(owner, '/api/home/state'); const completed = home.occurrences.find(o => o.task_id === confirmedProposal.task_id); assert.equal(completed.completed_by, member.user.user_id); assert.equal(completed.source, 'manual_care');
  await nav(carer, '家庭'); const historyCard = carer.locator('article.fa-record').filter({ hasText: 'Completed: Playtime with Mochi' }); await expect(historyCard).toContainText('Alex'); await capture(carer, '07-completing-actor', historyCard);
  await carer.goto('/#alexa'); const resultReply = await ask(carer, 'What was completed recently?'); assert(resultReply.source_record_ids.includes(completed.id)); await capture(carer, '12-alexa-result', carer.getByRole('article', { name: en('Alexa 分身回复') }).last());
  const day = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date()); await owner.goto('/#app/growth'); await owner.getByRole('navigation', { name: en('成长分区') }).getByRole('button', { name: en('报告'), exact: true }).click(); await label(owner, '统计日期').fill(day); await button(owner, '生成日报').click();
  const daily = (await api(owner, '/api/family/pets/mochi/reports')).reports.find(r => r.period === 'daily' && r.date === day && r.status === 'current'); const dailyCard = owner.locator('article').filter({ has: owner.getByRole('heading', { name: new RegExp(`^Daily report · ${Number(day.slice(5, 7))}/${Number(day.slice(8))}/${day.slice(0, 4)},`) }) }); await expect(dailyCard).toContainText('Manual care completions 1'); await capture(owner, '05-daily', dailyCard);
  await owner.getByRole('button', { name: 'Export a vet visit card (clinical background)', exact: true }).click(); await label(owner, '包含演示样本（仅作演示）').check(); await button(owner, '生成信息卡').click(); const card = owner.getByRole('region', { name: 'Vet visit card snapshot', exact: true }); await expect(card).toContainText(memoryText); await expect(card).toContainText('Playtime with Mochi'); await capture(owner, '15-visit-card', card); await button(owner, '关闭信息卡').click();
  await nav(owner, '家庭'); await owner.locator('.ca-manager select').selectOption('24'); await button(owner, '授权照护者访问分身').click(); const link = await label(owner, '新的只读访问链接').inputValue(); assert(link.includes('#pet-access='));
  const visitor = await makePage('caregiver'); await visitor.goto(link); await expect(visitor.getByRole('heading', { name: /Mochi.*read-only twin/ })).toBeVisible(); await button(visitor, '它喜欢什么').click(); await expect(visitor.getByRole('log', { name: en('只读分身对话') })).toContainText(memoryText); await capture(visitor, '14-caregiver', visitor.locator('.ca-hero')); data.caregiver = { pet_id: 'mochi', read_only: true, token_redacted: true, context: await visitor.evaluate(async () => { const token = location.hash.split('=')[1]; const r = await fetch('/api/care-access/context', { headers: { Authorization: `Bearer ${token}` } }); if (!r.ok) throw new Error('caregiver context failed'); return r.json(); }) };
  await button(owner, '撤销只读访问').click(); await button(visitor, '刷新授权资料').click(); await expect(visitor.getByRole('alert')).toContainText('no longer'); data.caregiver.revocation_verified = true;
  await nav(owner, '助手'); await button(owner, '删除记忆').click(); await expect(button(owner, '删除记忆')).toHaveCount(0); await carer.goto('/#alexa'); await button(carer, '新会话').click(); const deleted = await ask(carer); assert(!deleted.source_record_ids.includes(confirmedMemory.id)); assert(!deleted.answer.includes(memoryText)); await capture(carer, '06-deleted-memory', carer.getByRole('article', { name: en('Alexa 分身回复') }).last());
  await owner.goto('/#app/home'); await capture(owner, '16-home-closing', owner.locator('.ph-room').first());
  Object.assign(data, { shared_memory: { memory_id: confirmedMemory.id, before, candidate, confirmed_in_new_login: reused, confirmed_in_new_page_session: newSessionReply, after_deletion: deleted }, alexa_care: { draft, proposal, confirmed_proposal: confirmedProposal, result_reply: resultReply }, weekly_report: weekly, daily_report: daily, manual_care: { occurrence_id: completed.id, source: completed.source, completed_by: completed.completed_by, expected_actor_id: member.user.user_id }, boundaries: ['fictional Emma/Alex household', 'demo_sample measurements', 'owner-confirmed SQLite database memory', 'independent Alexa web simulation', 'rule draft with explicit manual-care confirmation', 'no live model or hardware', 'caregiver read-only scoped access', 'vet card is a frozen record summary, not diagnosis'] });
  data.timing_boundary = 'Role-specific WebM starts at the first blank page. Holds have approximate raw seek ranges measured from newPage creation; calibrate first-frame uncertainty and transitions visually. API credentials and caregiver link are excluded; screenshots do not show invitation codes.';
}
main().then(() => { data.status = 'passed'; }).catch(async error => { data.status = 'failed'; data.error = String(error.stack || error); console.error(data.error); if (browser) for (const context of contexts) for (const page of context.pages()) { try { await page.screenshot({ path: path.join(out, `failure-${roles.get(page)}.png`) }); fs.writeFileSync(path.join(out, `failure-${roles.get(page)}.txt`), await page.locator('body').innerText()); } catch {} } process.exitCode = 1; }).finally(async () => {
  for (const context of contexts) { const pages = context.pages(); await context.close(); for (const page of pages) if (page.video()) { const target = path.join(out, `${roles.get(page)}.webm`); await page.video().saveAs(target); data.recordings[roles.get(page)].bytes = fs.statSync(target).size; } }
  if (browser) await browser.close();
  if (service?.pid) { const kill = spawn('taskkill', ['/PID', String(service.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' }); await new Promise(resolve => kill.on('exit', resolve)); }
  fs.closeSync(serverLog); fs.writeFileSync(path.join(out, 'demo-evidence.json'), JSON.stringify(data, null, 2));
  console.log(`Capture ${data.status}; evidence written to ${out}`);
});
