# PawTwin — judge setup and testing guide

Updated on **11 October 2026**. This guide reproduces the **single-instance local** product, including its website and independent Alexa web simulator. It requires no AWS credentials and makes no live Alexa claim. Final track acceptance and actual AI/agentic-tool evidence remain submission gates. Read the [project description](project-description.en.md) and [current rule check](rules-check-2026-10-11.md).

## Access and source package

No GitHub URL, published demo URL or final video URL has been supplied in the current workspace. The source is the current project directory, including the uncommitted household extension; checking out baseline commit `31da349` alone will omit that extension. A release must include its Python modules, frontend sources, tests, generated contracts, lockfiles, scripts, assets and this guide.

The submission must provide a GitHub repository. It can be public with an open-source license, or private with access for `testing@devpost.com` and the listed Amazon reviewers. A public hosted App is not mandatory: judging access can be through the repository and demonstration video. A private website, if used, also needs testing login instructions. No license has been chosen or added by this pass. [Official rules, Submission Requirements and Testing](https://amazonappdev2026.devpost.com/rules)

For a private repository, grant access to `chris-trag`, `knmeiss`, `giolaq`, `anishamalde`, `mosesroth` and `emersonsklar`, as well as Devpost's testing address. Check that invitations remain valid; the official update notes that GitHub invitations expire after seven days and require acceptance. Do this as part of authorized submission preparation. [Organizer's repository-access update](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea)

## Requirements and launch

The provided scripts target Windows/PowerShell. Install Git, Python 3.12, `uv`, and Node.js 24 with npm. The lockfiles are part of the source package. Initial dependency and test-browser installation needs network access. AWS CLI and Docker are optional for this local demonstration.

From the project root, run:

```powershell
./scripts/setup.ps1
./scripts/preflight.ps1
./scripts/verify.ps1
./scripts/dev-home.ps1 -Port 8807 -DatabasePath ./data/judge-demo.db
```

Use a new, disposable database path for each clean rehearsal, for example `judge-demo-02.db` on the second run. Do not clear an existing user's database to reset a demonstration. The script starts a foreground server on `127.0.0.1`, pins local mode, disables photo recognition and restores its process environment on exit. [Launch source](../../scripts/dev-home.ps1)

Open [the local App](http://127.0.0.1:8807/#app). Keep the server terminal running. If 8807 is occupied, select an unused port and use that port consistently; do not stop an unrelated service. `http://127.0.0.1:8807/healthz` should return `{"status":"live"}`. A local `/readyz` response of 503/degraded is expected: it does not claim cloud readiness.

The original device approval/receipt store uses `judge-demo.db`; new family records use `judge-demo.db.family.db`. Local accounts and records persist. Refresh restores the browser session, but restarting the server requires another login. This is a local SQLite deployment in one application instance. The original workbench's `local_fake` analyzer and the family assistant's `local_rules` backend are different components. `dev-home.ps1` explicitly pins both, disables photo recognition and restores its process environment on exit.

Visit `/` for the product website, `/#cases` for fictional product scenarios, `/#app` for the household App and `/#alexa` for the independent simulator. Website device screens are illustrations; the actual App/simulator read authenticated household records. Product animations have a pause control and respect the system's reduced-motion setting.

The optional family Bedrock path is wired in [family_assistant.py](../../backend/pawtwin/family_assistant.py); [test_family_bedrock.py](../../tests/test_family_bedrock.py) uses an injected SDK-shaped client and never contacts AWS. Live validation is not recorded. The user has reported AWS account review passed, so an account-review wait is not a current demo blocker. Run the local instructions above for reproducible judging; do not substitute cloud smoke/deployment scripts. In optional Bedrock mode, protected care/health requests can return `server_guard` without a model call. Only actual response evidence can substantiate a live invocation.

## English map of the current Chinese interface

The current interface is Chinese. Use this table with the English test steps; final video narration and all other submitted documentation need English or an English translation. [Official language requirement](https://amazonappdev2026.devpost.com/rules)

| Visible text | English meaning / action |
|---|---|
| 小屋 / 照护 / 助手 / 成长 / 家庭 | Home / Care / Assistant / Growth / Household; five bottom-navigation sections |
| 创建本地账号 / 注册并登录 | Create a local account / Register and sign in |
| 账号名 / 密码 / 昵称 | Account name / Password / Display name |
| 家庭名称 / 家庭时区 / 创建家庭 | Household name / Household time zone / Create household |
| 生成家庭邀请 / 新邀请口令 / 邀请口令 / 加入家庭 | Generate invitation / New invitation token / Invitation token / Join household |
| 家庭称呼 / 保存个人设置 | Chosen family label / Save personal settings |
| 管理员 / 照护成员 / 访客 | Administrator / Carer / Guest; actual permission roles |
| 实测体重 / 测量数值 / 单位 / 测量时间 | Measured weight / Value / Unit / Measurement time |
| 资料来源 / 演示样本 / 保存成长记录 | Record source / Demo sample / Save growth record |
| 统计日期 / 生成周报 / 生成日报 | Report date / Generate weekly report / Generate daily report |
| 统计依据与版本 / 实际摄入：未记录 | Sources and version / Actual intake: not recorded |
| 偏好原文 / 保存候选记忆 / 确认记忆 | Preference text / Save candidate memory / Confirm memory |
| 候选待确认 / 主人已确认 / 删除记忆 | Candidate awaiting confirmation / Owner confirmed / Delete memory |
| 对话入口 / App 助手 / Alexa 网页模拟 | Conversation entry / App assistant / Alexa web simulator |
| 想了解什么 / 询问分身 / 分身回复 | Question / Ask pet context / Pet-context response |
| 方案类型 / 陪玩 / 方案名称 / 计划时间 | Proposal type / Play / Proposal title / Scheduled time |
| 建立待确认方案 / 待确认 / 确认安排照护 | Create pending proposal / Awaiting confirmation / Confirm care arrangement |
| 已安排人工照护 / 未执行设备 | Manual care arranged / Device not executed |
| 同步最新记录 / 领取 / 已领取 / 完成照护 / 已完成 | Sync latest records / Claim / Claimed / Complete care / Completed |
| 本地独立账号 · 云认证未接通 | Independent local account; cloud authentication not connected |
| 本地规则分身 / Alexa 网页模拟 | Local rule-based pet context / Alexa web simulation |
| 新会话 / 模拟口述内容 / 发送 | New session / Typed speech simulation / Send |
| 查看这轮依据 / 源记录 / 真实模型请求 | Inspect this turn's sources / Source records / Model request ID; “none” is expected in local mode |
| 浏览器朗读这条回复 | Read this reply with browser speech synthesis, if supported |
| 安排陪玩 / 安排换水 | Arrange play / Arrange a water change; request a manual-care draft |
| 草案照护时间 / 准备待确认方案 / 放弃草案 | Care time / Prepare pending proposal / Discard draft |
| 确认安排人工照护 / 暂不安排 / 查看照护任务 | Confirm manual-care arrangement / Do not arrange yet / View care tasks |
| 依据已变化或过期，请重新提问 | Sources changed or expired; ask again before confirmation |

Family labels such as `爸爸` (“Dad”) describe a person; they do not change their role. Candidate/confirmed database memory describes a record's review status, not AI extraction or successful AgentCore retrieval.

## Two-account functional walkthrough

Use **two independent browser profiles or browser contexts**. Two tabs in one profile share cookies and will not demonstrate two users. Set the browser/OS test time zone to Asia/Shanghai for the exact example below; measurement date/time inputs use the browser's local time. Create a household with the same time zone. The existing automated rehearsal explicitly fixes that browser time zone.

1. In the owner profile, open `/#app`, select “Create a local account” and register a unique account name, a display name and a password of at least 12 characters. Choose the password locally. Create “Mochi Demo Household” in Asia/Shanghai. The seeded Mochi profile is the pet for the walkthrough.
2. Open Household and generate a carer invitation. In the second profile, register a different account, paste the invitation token and join. Set that member's chosen family label to `爸爸` (“Dad”), then save. Expected: they remain a **carer** and cannot manage invitations. Keep passwords and invitation tokens out of recorded footage and public artifacts.
3. In the owner's Growth section, select measured weight and enter **1.20 kg at 2026-09-25 12:00** and **1.35 kg at 2026-10-02 12:00**. For both records, select “Demo sample” as the source. Save each record. These are fictional staging data, not actual pet measurements or trial results.
4. Set report date to **2026-10-02** and generate the weekly report. Expected: **150 g / 12.5% / seven actual days**, with actual intake and recorded dispensing still “not recorded.” Expand “Sources and version” and inspect the measurement IDs. The weekly window is 28 September–5 October; 25 September is the earlier comparison baseline, not a second in-window measurement.
5. In the owner's Assistant section, enter `喜欢羽毛棒，饭后先休息` (“Likes a feather toy; rests after meals”) and save a candidate. Before confirmation, ask `它喜欢什么` (“What does it like?”) in the other profile's independent `/#alexa` page: the candidate must not be cited as confirmed memory. Confirm it in the owner profile. In the carer's simulator, select **New session** and ask again. Expected: the new answer cites the confirmed record. Expand **Inspect this turn's sources** to see the source ID, context version and absent model request ID. This is rule-based retrieval from SQLite; it is not live Alexa or a cloud model. Starting a new page session does not delete the household's memory.
6. In the simulator, ask `安排陪玩` (“Arrange play”). Inspect the **draft**: its type/title come from server rules and no task exists. Choose a concrete, already-due time in **Care time**, using the browser-local time zone, then select **Prepare pending proposal**. This still creates no care task. Check the displayed type/title/time and select **Confirm manual-care arrangement**. Expected: one manual Play task is arranged; no device executes. Pending confirmation uses the original saved context version and expiry, so changed/expired sources require a fresh request. Natural-language dates are not parsed into a schedule.
7. In the carer's Care section, sync, find that task, claim it and complete it. Expected: Play / Completed. The task card shows the assigned member; that is distinct from the actual completing actor. Open Household → Recent household activity to check the author's display name; the automated evidence separately checks the authenticated `completed_by` user ID. In the owner's Growth section, select today's household-local date and generate the **daily** report. Check that daily card, rather than a weekly card: it should count one completed manual-care occurrence in this fresh demo.
8. Delete the confirmed memory in the owner's Assistant. Refresh or sync the other account and ask the preference question again. Expected: the **new** answer no longer includes the deleted text and reports no confirmed preference memory. Previous answers remain historical; deletion does not rewrite them.

9. Return to the independent simulator and ask `最近完成了什么` (“What was recently completed?”). Expected: it reports the recorded manual completion with its occurrence source ID, rather than treating an arrangement as completion. The result uses the latest household record; previous replies retain their historical sources.

The [automated rehearsal](../../frontend/e2e/demo-rehearsal.spec.ts) calls real local APIs and checks source IDs, confirmation boundaries, the actual completing `user_id` and `manual_care` provenance. Its isolated test data does not populate your file-backed judge database. The dedicated capture passed **one rehearsal in 39.7 seconds** and produced [schema-2 evidence](../evidence/hackathon-capture/2026-10-11-final/demo-evidence.json), 14 actual screenshots and two account WebMs. The final full browser run passed **42 tests in 1.4 minutes with zero retries**. The coordinator's final artifact/source record is `docs/evidence/submission-readiness-2026-10-11.md`; the [10/3 recheck](../evidence/functional-check-2026-10-03.md) is historical only.

## Simulator behavior and recovery

The simulator keeps at most 20 turns in page memory. Leaving, refreshing, changing pet/account or selecting **New session** clears that conversation; household records and confirmed tasks remain in SQLite. It does not persist or retrieve a cross-refresh chat history. Each fresh question reads the current scoped context. Guest users have read-only records and cannot submit chat/care writes. Switching pet discards late responses for the old pet.

If preparation/confirmation fails because sources changed or expired, read the visible message and ask again to create a fresh draft. If a connection fails, check **View care tasks** for current persisted status before retrying. Arrangement is not completion, and completion is the family's manual record. If browser speech synthesis is available, the optional read-reply button can speak a reply; no microphone is collected and audio/device quality has not been evaluated.

## Optional original actuator demonstration

The original workbench is `/#workbench`; the legacy Home is `/#home`. Use a third independent session and the original local demonstration login described in the [project README](../../README.md). This path has its own simulated Mochi actuator, approval gate, hard limits and receipts. A new family's Mochi profile does not inherit device execution rights.

Show approval/decline or success/failure/unknown receipt behavior only with its simulation labels visible. Success means simulated dispensing, not proven intake. Failure or unknown status must not be narrated as completed. This optional path is separate from the manual family-care walkthrough.

## Automated checks

`verify.ps1` runs backend tests, Ruff, generated-contract freshness, TypeScript and the production build. It does not run browser tests. For browser testing, first stop **your own** judge server if it occupies the configured test port, then run:

```powershell
$env:PAWTWIN_E2E_PORT = '8810'
$env:PAWTWIN_DB_PATH = ':memory:'
./scripts/test-e2e.ps1 -InstallBrowser
```

Use an unused test port. Initial `-InstallBrowser` downloads Playwright Chromium; omit the switch after installation. Test accounts/data are isolated from your file-backed judge demonstration. The latest 11 October verification passed **393 backend tests / one skipped / 21 live AWS tests deselected**, with Ruff, generated contracts, TypeScript and production build passing. The final full browser run passed **42 tests in 1.4 minutes with zero retries**. See the [verification transcript](../evidence/submission-readiness-2026-10-11/verify.log) and [browser transcript](../evidence/submission-readiness-2026-10-11/e2e.log). Results describe this local environment; they do not guarantee another installation or live AWS behavior.

The skipped analysis-in-progress forced-kill case is not a passing test. Live Bedrock, AgentCore and DynamoDB checks remain excluded by default and have not been performed as part of these materials. Do not run cloud smoke/deployment/live-marker commands merely to reproduce this local demonstration.

The local launcher now adds Uvicorn `--no-proxy-headers`. Authentication throttling uses the server-resolved peer address rather than a caller-supplied raw `X-Forwarded-For` value. A future reverse-proxy deployment must separately configure trusted proxy addresses; the local instructions do not establish a production proxy configuration.

The original workbench's current safety checks include different feeding runs across separate local database connections, a persisted owner feeding gate, unknown/interrupted execution holding that gate, delayed facts reevaluation preserving a completed run, and atomic receipt/accounting/terminal-state persistence. [Regressions](../../tests/test_feeding_reservation.py) exercise these local cases. [DynamoDB shape tests](../../tests/test_feeding_dynamo_offline.py) use offline clients; old facts without the new guard version refuse feeding rather than executing without a gate. They do not establish live DynamoDB transactions or distributed deployment.

## Common recovery checks

| Observation | Expected interpretation / action |
|---|---|
| Empty page or stale assets | Confirm `verify.ps1` completed the frontend build and open the server's exact port. |
| Login expires after server restart | Sign in again in both profiles; persistent accounts and records remain. |
| Other member has not yet seen a change | Verify household and selected pet, then sync; normal polling is approximately ten seconds. This is not a WebSocket push claim. |
| Version/context conflict | Sync and create/confirm a current proposal. The server rejects stale confirmations. |
| Unexpected report total | Use a fresh demo database, inspect record dates/units/source IDs, and check the correct daily or weekly card. |
| Different measurement times | Check the browser's time zone; the date/time input uses it, while reports use the household time zone. |
| Local `/readyz` returns 503 | Expected degraded cloud-readiness state; check `/healthz` for process liveness. |
| New family API unavailable in AWS mode | New family cloud storage is unimplemented and fails explicitly; run the documented local script. |

## Final video and submission access

The [current English local review MP4](../evidence/submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4) has been generated: **170.0185034 seconds**, 1920×1080 H.264/AAC. It edits the 14 current actual screenshots with English narration and burned-in captions; the two raw account WebMs are retained as source recordings. This is a screenshot edit, not continuous real-time motion replay. [Mechanical verification](../evidence/submission-video-2026-10-11/local-review-01/verification.json) checks 26 complete sentences, 13 decoded frames, subtitle fit and unclipped decoded audio. The [actual contact sheet](../evidence/submission-video-2026-10-11/local-review-01/review-frames/actual-contact-sheet.png) has been visually reviewed; full human playback/pronunciation/listening is still unperformed.

Record functioning source-derived behavior, with current local/rule/simulation labels, in a final English-narrated or English-translated video of **less than three minutes**; target 2:45–2:55 to leave a margin. The final video must be publicly viewable on YouTube or Vimeo and linked in the entry. Local automated recordings, still screenshots and scripts are supporting artifacts, not proof of a published final video. Keep the source free of credentials and include private website test credentials only through the appropriate private testing instructions if such a website is later used. [Official video, language and testing requirements](https://amazonappdev2026.devpost.com/rules)
