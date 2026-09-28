# Day-2 独立审查记录（2026-09-25）

审查者：**非作者**的独立只读代码审查 Agent（CodeReview 子代理）。范围：本次会话在 `chore/bootstrap` 上的全部 Day-2 改动（基线 `dc8dc10`，37 个修改文件 + 8 个新增文件，+3724/−293 行）。审查判据为 `docs/plans/PawTwin_Day2_开发计划.md` 的 25 条裁定与 G0–G11 必过门、`AGENTS.md`、五日总方案与实施任务单。

> **计数更正（2026-09-26）**：上行「37 个修改文件 + 8 个新增文件，+3724/−293」与 `git status`/`git diff --shortstat` 不符，实为 **38 个 modified + 14 个 untracked（含 4 份 docs/证据），+3801/−314**。属本文件笔误，不影响审查结论。

## 结论

**PASS-WITH-NITS**。无阻断性缺陷；15 项逐条核实中 14 项 ✅、1 项 ⚠️。发现 **1 个重要缺陷 + 6 个 nit**，均不影响 fail-closed 安全性（硬性策略在 workflow 层兜底，替身的失真建议不可能被执行）。

审查者复跑证据：`pytest` **130 passed**（当时点）、`ruff` 无告警、`export_contracts.py --check` 返回 "Contracts are current"、`uv lock --check` exit 0（65 包，strands 已入锁）、`git status --porcelain` 范围与声称一致。

## 15 项逐条核实

| # | 审查项 | 结论 | 关键依据 |
|---|---|---|---|
| 1 | 裁定 7：claim 白名单排除 `EXECUTING`/`AWAITING_APPROVAL`/`BLOCKED`/`NEEDS_INFO` | ✅ | `repository.py` `CLAIMABLE_STATES = {QUEUED, ANALYZING}`；`repo_sqlite.claim_run` 的 UPDATE 带 `state IN (白名单)`；`list_claimable_runs` 用同一常量；`test_worker.py` **穷举全部 11 个 RunState** 断言 `claimed is (state in CLAIMABLE_STATES)` |
| 2 | 裁定 10：批准**先 CAS 再** execute；并发双批准；decline 也有 CAS | ✅ | `workflow.handle_approval` 的 approve 分支 `transition_run(AWAITING_APPROVAL→EXECUTING)` 失败即抛 `NOT_AWAITING_APPROVAL`，成功后才 `_execute`；`test_worker.py` 双线程并发批准 → `device.execute_calls == 1`、`count_receipts == 1` |
| 3 | 裁定 8/9：`save_run` 不写租约；`attempt_count` 原子自增；renew/release 仅持有者 | ✅ | `save_run` 的 UPDATE 列表不含 `lease_owner`/`lease_until`/`attempt_count`；`claim_run` 在**同一条 UPDATE** 内 `attempt_count = attempt_count + 1` 且 `AND attempt_count < ?`；`renew_lease` 带 `AND lease_owner = ?` |
| 4 | 裁定 3：pinned 快照 + 台账校验，无 fail-open | ✅ | `AgentContext` 构造时固化 `FactsSnapshot`，工具读内存快照并登记台账；`_apply_outcome` 持久化前再校验一次；策略与建议读**同一份**快照 |
| 5 | 裁定 5/6：fail-closed 不回退；僵尸写拦截；不冒泡 500 | ✅ | `_analyze_claimed` 全捕获 → `_fail(failure_code_from(exc))`；`AnalysisGuard` 超时落 `FAILED`；预算超限 `ModelBudgetExceeded`；`_persist_if_still_owner` 为纵深防御；全库 grep 无"失败后回退 inline/预制答案"路径 |
| 6 | 裁定 11：A03 零模型调用 | ✅ | `_reevaluate_under_new_facts` 只调 `evaluate_policy`（纯函数），不触碰 proposer；`proposal_version += 1` 而 digest 对未变 action 重算得同值；`evidence`/`telemetry` 完全不动，`retrieved_at` 保持原值 |
| 7 | 裁定 12/13：UNSET 语义；删 `or 0`；硬限额不可改；demo 端点鉴权 | ⚠️ 部分 | 后端全部正确（`update_facts` 的 `UNSET`/NULL、`_facts_view` 已无 `or 0`、`DemoFactsIn` 不含三个硬限额字段、两端点均挂 `CsrfSessionDep`）；**但 `or 0` 在替身层复现** → 见缺陷 #1 |
| 8 | 裁定 14：迁移幂等 + 文件库测试 + `default_factory` | ✅ | `_migrate` 以 `PRAGMA user_version` 为闸 + `PRAGMA table_info` 双保险；`test_demo_api.py` 有旧文件库迁移与文件库重启两个测试 |
| 9 | 裁定 15/24：云边界与依赖 | ✅ | `mode=aws` 仍抛 `NotImplementedError`；`aws_connected` 硬编码 False；`model_backend=bedrock` 缺配置启动即拒；strands **延迟导入**且缺失时抛具名错误；pyproject/uv.lock/CI/Dockerfile 一致；原 `NotImplementedError` 断言被改为**更强**断言 |
| 10 | 裁定 17/18：生命周期与默认值 | ✅ | worker 仅在 lifespan 启停；关闭顺序 worker→guard→repository；`create_app` 不起线程（`threading.active_count()` 前后相等实证）；guard executor 为 app 级且 `shutdown(wait=False, cancel_futures=True)`；`worker_mode` 默认 `inline` |
| 11 | 契约与测试诚实性 | ✅ | 11 条路径 + 401/403/404/409/422；`domain.schema.json` 断言已收紧为 `==`（恰为 6 输入模型 + RunState）；`test_app.py` 的 readyz/bootstrap 是**精确字典相等**上调而非放宽；未发现任何被削弱的断言 |
| 12 | 前端与 e2e | ✅ | `POLL_TIMEOUT_MS = 75_000` > 后端 45s；api.ts 类型与 models.py 逐字段一致（含可空事实）；`workers: 1`/`retries: 0`/`expect.timeout: 20_000`/webServer env；各 spec 经 `helpers.resetDemo` 复位；approve.spec **未**把 409 幂等说成"e2e 已验证"（该断言由 pytest 承担） |
| 13 | 范围合规 | ✅ | 无 Day-3（AgentCore/feedback/new-session 路由）或 Day-4/T7（DynamoDB/部署/HTTPS）实现代码；相关字样仅存在于文档与前端"长期记忆：未实现"占位标签；契约 11 路径与冻结集一致；无未授权产品功能 |
| 14 | 安全 | ✅ | 秘密 grep 0 命中；`RunView` 不含 `owner_id`/`attempt_count`/`lease_*`/`model_calls_used`；证据台账不含事件 note 原文与隐藏推理；`bedrock_smoke.py` 输出无凭据；提示注入的真实强制点在模型之外（policy + Action 边界 + 批准 CAS） |
| 15 | 文档一致性 | ✅（附 nit） | README/`.env.example`/checklist/角色简报与代码实况一致，"未构建验证""NOT EXECUTED""仅进程内并发"等限定语准确；nit：证据文档缺失导致悬空引用（#4） |

## 发现与处理

### 【重要】#1 本地替身在 NULL 事实下产出失真数值与失真文案 — **已修**

- **发现**：`local_fakes.py` 用 `facts["daily_dispensed_grams"] or 0` 把 NULL 伪造成 0 并据此提议 `dispense_food 15g`，同时把 `None` 直接拼进解释文案，导致页面同屏出现「信息不足」与「出粮 15 克 … 上次喂食距今 None 分钟」。这正是裁定 12 在 `_facts_view` 消除的失真在替身层原样复现。审查者用截图 `frontend/test-results/needs-info.png` 证实。
- **处理**：替身新增 `_feeding_proposal`，任一关键事实为 `None` 时提议 `observe` 并填 `missing_fields`，文案改为「缺少必要事实（上次喂食时间/当日已出粮量），无法给出喂食建议，仅建议观察」；`workflow._inline_proposal` 的文案同步把 `None` 渲染为「未知」。
- **连带发现（审查未提，修复 #1 后暴露）**：改成 `observe` 后 `evaluate_policy` 返回 `NON_FEEDING`（非喂食动作总是允许），于是 A09 会变成 `AWAITING_APPROVAL` 而**不是** `NEEDS_INFO`，且 `policy_reason` 显示「非喂食动作，不占配额」与「信息不足」并列——又一处自相矛盾。裁定：`_apply_outcome` 与 `_reevaluate_under_new_facts` 均在 `proposal.missing_fields` 非空时判 `NEEDS_INFO`，并把 `policy_reason` 归为 `MISSING_FACTS`。这是 fail-safe 方向：多报一次缺口只损失一次重跑，绝不会多喂。
  - **口径更正（2026-09-26）**：该裁定当时只在 `local_fakes._feeding_proposal` 落地，`workflow._inline_proposal`（TEST 后端）**仍未声明 `missing_fields`**，因此同型缺口在 inline 后端依然存在（默认后端为 `local_fake`，e2e 亦显式注入 `local_fake`，故上线路径与当时全部测试都不触发）。已于本次补修并加回归测试，详见下方「后记二」。
- **复测**：新增 `test_local_fake_never_invents_a_quantity_from_an_unknown_fact`（断言 action=observe、`missing_fields`、explanation 不含 "None"）；`test_demo_api.py` 的 A09 用例补断言 `proposal.action == observe`、`missing_fields == ["last_fed_minutes_ago"]`、explanation 不含 "None"；e2e `approve.spec.ts` 的 needs-info 用例断言状态与 `policy-reason`。**139 passed** 且 e2e **7 passed**。

### 【nit】#2 `get_facts` 注释与代码矛盾 — **已修**

注释称"读路径永不写"，但 `row is None` 分支确实 `_seed_facts` + `commit`。改为准确表述：首次读会惰性播种（锁内、幂等），此后为纯读。

### 【nit】#3 缺 Bedrock 离线/实况测试文件 — **已补**

- 新增 `tests/test_bedrock_adapter_offline.py`（marker `bedrock_offline`，默认运行、零网络零凭据）：12 项，覆盖 note 数据围栏与分隔符转义、系统提示声明、`maxOutputTokens==800`/`model_id`/`output_schema is Proposal` 入参、stub 无 request_id、**真实 request_id 会被记录**（条件项插槽可用）、SDK `read_timeout < 45`、契约违反/不可解析输出被拒、客户端异常不产出 Proposal、无凭据与无 model id 的 fail-closed。文件顶部明写「NOT cloud evidence」。
- 新增 `tests/test_bedrock_live.py`（marker `bedrock_live`）：4 项**具名 skip**，理由固定为 `BLOCKED: no AWS account is authorised…`，对应真实往返、真实模型参与正常/重复喂食、A14 真模型对照、A11 模型在环注入。
- `pyproject.toml` 注册两个 marker，`addopts = "-q -m 'not bedrock_live'"` 使计费用例默认不跑（blocked 被**命名**而非静默缺失）。当前结果：**139 passed, 4 skipped**。
- `test_agent.py` 中重复的 offline 用例已移出，只留 seam/证据/替身/配置校验。

### 【nit】#4 证据文档缺失 + 悬空引用 — **本次补齐**

`docs/evidence/day2-handoff.md`、`day2-local.md`、`day2-cloud-blocked.md` 与本文件此前不存在，而 `test_agent.py`/`test_demo_api.py`/`infra/cloud-access-checklist.md` 已引用 `day2-cloud-blocked.md`。四份文档已随本次交付补齐，`docs/STATUS.md` 已更新。

### 【nit】#5 空 body `POST /api/demo/facts` 仍递增 `facts_version` — **已修**

变更集为空时不再写库（早退返回当前事实），避免无谓地把待批准任务作废成 409。新增回归测试 `test_an_empty_demo_facts_body_does_not_invalidate_a_pending_approval`（断言 version 不变且随后批准成功）。

### 【nit】#6 worker 顺序 drain 使准入上限实际不可触发 — **接受并记录**

`drain_once` 串行处理，故会话 1/全站 2 的上限在当前实现下不会真正生效；`AdmissionControl` 目前只有单测覆盖、无生产路径。`worker.py` 的 docstring 与 `docs/STATUS.md` 均已诚实披露「 realised concurrency = 1，跨副本上限需数据库级计数，Day-3/T6」。不视为缺陷，Day-3 引入并发执行时必须复验。

## 诚实性检查（审查结论）

- **无以本地替身冒充云端**：`aws_connected` 恒 False；`mode=aws` 仍 `NotImplementedError`；readyz 报 `degraded/cloud_adapters_not_verified`；bootstrap 各能力标 `implemented_local`/`implemented_simulated`/`not_implemented`；前端 badge 强制展示 `LOCAL`/`AWS 未连接` 且有 e2e 断言。
- **readyz/bootstrap 是精确上调而非放宽**：diff 确认 `test_app.py` 从旧期望值改为新的**精确字典相等**断言，保留 503 degraded；注释明言"understating readiness is a distortion too"。
- **断言收紧**：`domain.schema.json` 由子集改 `==`；原 `NotImplementedError` 断言升级为具名异常 + 原因码 + 状态落 FAILED；新增全状态穷举白名单断言。未发现被放宽的断言。
- **409 幂等无夸大**：并发双批准由 pytest（真线程 + 真 SQLite）验证，e2e 只声明 UI 闭环。
- 审查当时指出的两处诚实性瑕疵（替身文案失真、悬空引用）均已按上文修复/补齐。

## 范围合规

**合规**。全部改动落在 Day-2 计划范围内；契约 11 路径与门 0 冻结集完全一致；无 Day-3/Day-4 实现代码；无未授权产品功能；无秘密入库、无云资源创建、无费用、无远程推送、**镜像未构建**（本机 PATH 无 Docker，已如实标注）。

## 后记（总负责人处理后的复跑，2026-09-25）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **139 passed, 4 skipped**（4 skipped = `bedrock_live` 具名 blocked） |
| 静态检查 | `uv run --frozen ruff check .` | All checks passed |
| 契约一致性 | `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current |
| 依赖锁 | `uv lock --check` / `uv sync --frozen --extra bedrock` | 均成功（65 包） |
| 前端 | `npm run typecheck` / `npm run build` | 通过（Node 24.19.0） |
| 浏览器 e2e | `npx playwright test`（`workers: 1`、background、local_fake） | **7 passed**（8.7s） |
| 集成基线 | `./scripts/verify.ps1` | 全绿 |

本文件为 Day-2 审查记录；Day-1 的 `reviews/day1.md` 未改写。

## 后记二（三方审查复核与补修，2026-09-26）

交付后对**未提交**的 Day-2 改动再做一轮独立审查（单个 CodeReview 子代理覆盖后端契约+并发 / 前端+AI 云 / 独立审查三视角），总负责人对其每条关键断言回源码仲裁。6 条不变式复核结论：可领取白名单 ✅、租约可对持有者续且 `save_run` 不自清 ✅、批准 CAS ✅、证据与策略同快照且非法 id fail-closed ✅、A03 零模型调用 ✅、NEEDS_INFO 判定 ⚠（见下）。

审查提出 1 项「重要」+ 1 项 nit，仲裁后**一项上调、一项扩充**：

- **【阻断】审批路径的非 CAS 写入可覆盖已完成的 run**。审查只指出过期分支（原判 nit，理由「仅终态展示失真」），仲裁否掉了该理由：`save_run` 的 UPDATE 同时写 `receipt_json`，故过期盲写会把并发已执行成功的 run 写成 `EXPIRED` 并**抹掉回执**（设备已出粮、配额已扣）。回源码复现时又暴露**同一缺陷的另一半**：过期改 CAS 后控制流改走 A03，而 `_reevaluate_under_new_facts` 同样盲写，把 `SUCCEEDED` 覆盖成 `BLOCKED`（重评读到对手已扣减的配额）。修法：新增唯一写入原语 `_settle(record, new)`，CAS 成功才落库、失败即放弃写入；过期/拒绝/A03 重评/执行前策略阻止四分支统一走它。
- **【重要】`inline` 后端不报 `missing_fields`**（即上文 #1 连带发现的未覆盖面）：已对齐 `_feeding_proposal`。

新增 5 项回归测试：`test_worker.py` 的 `test_late_expiry_write_cannot_blank_an_already_executed_receipt`、`test_stale_facts_reevaluation_cannot_overwrite_an_executed_run`、`test_inline_backend_reports_an_unknown_fact_as_needs_info`（参数化 2 项），以及 `test_demo_api.py` 的 `test_stale_approval_that_stays_allowed_keeps_a_fresh_window`（守住重评后必须重挂新审批窗口，不得把 `expires_at` 清空）。**负向验证已做**：把这两处缺陷的代码回退后，前 4 项全部转红（实测到 `succeeded→expired`、`succeeded→blocked`、`needs_info→awaiting_approval` 三种失真），确认非假绿。

**额外发现（先前就存在的测试脆弱性，非本次代码引入）**：`test_concurrent_approvals_execute_the_device_exactly_once` 把败方的拒绝码写死为 `NOT_AWAITING_APPROVAL`，但两个真线程并发批准时，若赢家已在败方读记录之前完成执行并记账（`facts_version` 被 bump），败方会走到 A03 而抛 `STALE_APPROVAL_FACTS_CHANGED`——两种拒绝都是正确结果。实测中确已复现一次（25 次重跑中 1 次）。已改为断言拒绝码属于该二元集合，真正的不变式（`execute_calls == 1`、`count_receipts == 1`、记账一次）不变；修正后连续 20 次全量重跑零失败。

修复后复跑：

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run pytest -p no:cacheprovider -o addopts="" -q` | **144 passed, 4 skipped**（139 → +5）；连续 20 次全量重跑零失败 |
| 静态检查 | `uv run ruff check .` | All checks passed |
| 契约一致性 | `uv run python scripts/export_contracts.py --check` | Contracts are current（本轮无契约变更） |
| 集成 baseline | `./scripts/verify.ps1` | 全绿（含 typecheck/build） |
| 浏览器 e2e | `scripts/test-e2e.ps1` | **7 passed**（8.9s）。**如实标注**：Playwright 1.63 的 `chromium_headless_shell-1243` 未下载（本机缓存只有 1194），本轮用 `PAWTWIN_BROWSER_EXECUTABLE` 指向系统 Chrome（与 Day-1 同一处置），未下载任何二进制 |

仍未验证（保持 BLOCKED，不计入通过）：真实 Bedrock 往返与 `request_id`、DynamoDB 条件写语义、镜像构建、GitHub Actions 远程运行。
