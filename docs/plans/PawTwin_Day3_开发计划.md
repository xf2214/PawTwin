# PawTwin 第三日（Day-3）开发计划

> 本文是 [五日开发总方案](PawTwin_五日开发总方案.md) 第 6 节「第 3 日」与 [实施任务单](PawTwin_Agent_实施任务单.md) T5（+T1/T2 并发·恢复补强、AI-02、OPS）的当日可执行分解；承接 [Day-2 开发计划](PawTwin_Day2_开发计划.md) 与 [Day-2 完成记录](../STATUS.md)。
> 由三视角（后端契约与并发、前端+AI/云、独立审查）交叉校验，并对每条关键断言回源码二次核查后定稿。
> 执行者无需再做设计决策；如与两份权威计划冲突，以权威计划为准并回报总负责人。编制日期：2026-09-26。
> **基线**：分支 `chore/bootstrap`，HEAD=`dc8dc10`（Day-1），**Day-2 改动全部未提交**（38 modified + 14 untracked），`uv run --frozen pytest` **144 passed, 4 skipped**（4=`bedrock_live` 具名 blocked），契约 `--check` current（11 路径），e2e 7 项绿。Day-3 建立在未提交的 Day-2 工作区之上（是否先提交 Day-2 由用户授权决定）。

## 0 前提与当日验收（三档）

**前提（用户 2026-09-26 确认）**：①**仍无 AWS 账号** → AgentCore 真实提炼/检索为**条件项**，缺席不阻塞，**绝不以本地替身或 stub 冒充「已检索记忆」**（AGENTS.md L18、总方案 L69/L106）；②范围**按五日计划原样**（记忆+反馈+跨会话 / 并发+持久化+重启恢复 / 三场景打通），**T6 的 24 案例集 `scenarios.json`+`evaluate.py` 顺延 Day-4**。

| 档位 | 内容 |
|---|---|
| **必过 Gate** | **G0** 门 0 契约/配置冻结（14 路径 + 记忆 seam + Day-3 冻结提交 ID）；**G1** 反馈持久化 + `POST/GET /api/feedback`（存原文、幂等去重、登录+CSRF）；**G2** `memory_status` 诚实（本地=`saved`+「未实现」标签，**绝不** `available`/`processing` 伪造；`today_only` 不成为永久偏好）；**G3** `search_owner_memory` 接线 `MemoryService`（本地返回 `[]`、不伪造证据；stub 测试证明 `source="memory"` 证据链与 proposal 引用可用）；**G4** `POST /api/demo/new-session`（新 `conversation_id`，保留记忆/事实/登录）；**G5** worker **真并发**（`AdmissionControl` 会话 1/全站 2 获得生产触发路径，复验 Day-2 nit#6）；**G6** **跨进程双批准**（文件库两连接，`device.execute` 恰一次 + DB 不变式）；**G7** **真实 OS 进程重启复验**（等待审批/终态/过期租约/**处理中**）；**G8** 前端记忆区（反馈输入+状态+新会话，诚实标注，e2e）；**G9** 三场景本地打通（A 正常/B 已喂过/C 记忆管线结构）；**G10** 回归全绿 + 契约 current + 文档诚实分列 + 非作者独立审查 |
| **尽力项** | `AgentCoreMemory` 适配器真实实装（**带硬门**，延迟导入，缺依赖/凭据→具名 `MemoryUnavailable`）；**真实 OS 进程 kill/relaunch** 集成测试（subprocess，marker `restart`）；`memory`/`agentcore` optional extra 锁定（`uv sync --frozen --extra` 可复现）；`agentcore-smoke.ps1`（无凭据→`NOT EXECUTED`/退出码 2）；`preflight.ps1` AgentCore 只读段 |
| **条件项**（账号就绪才做） | 一次真实 AgentCore memory strategy `ACTIVE` 检查 + 提炼/检索往返，记录 record ID/namespace/event ID 到 `docs/evidence/`；**场景 C 真实记忆影响建议**（跨会话 retrieve、引用主人观察、保留不确定性）；A06/A07/A08 的真实记忆部分 |

**明确不写进 Day-3 承诺**：T6 的 `scenarios.json`+`evaluate.py`（Day-4）；DynamoDB 真表/跨**副本**多 replica/部署/HTTPS/镜像构建（Day-4/T7）；真实 Bedrock（仍条件项，同 Day-2）；**会话 DB 持久化**（裁定 6 顺延）；A10 真异步「迟到回执」入口（Day-2 已书面归约）。

## 1 技术裁定（门 0 前须落定；每条已回源码核查）

| # | 议题 | 裁定 | 依据 |
|---|---|---|---|
| 1 | **MemoryService seam** | `memory.py`（AI 所有）定义 `MemoryService` 协议：`submit_feedback(owner_id, pet_id, text, scope, conversation_id) -> FeedbackResult`、`get_status(feedback_id) -> MemoryStatus`、`search(owner_id, pet_id, query) -> list[MemoryRecord]`。`MemoryService` 由 **Coordinator 在门 0 冻结签名**，注入 `AgentContext`（与 `repo` 同构），**workflow 不 import memory**（避免 Backend→AI 依赖）；装配在 `main.py` | agent.py L87-99（`AgentContext.__init__` 已注入 repo）；workflow.py L64-80（`Proposer` seam 不碰 AI）；AGENTS.md L30 |
| 2 | **`memory_status` 诚实语义** | 无账号（`memory_backend=not_implemented`）时反馈一律 `saved`（**原文已存业务库**），**绝不** `processing`/`available`——后两者意味着一个本地根本无法运行的提炼任务。`available` **仅**在真实 AgentCore 检索证据出现时（AGENTS.md L18）。`FeedbackView` 同时携带 `memory_backend` 标签，使 `saved` 永不被读成「已提炼」。`today_only` → `saved` 且留在有时效业务记录，**不生成永久偏好**（A07） | 任务单 T5 L294/L298；ai.md L9；models.py L302-313（`StateView.memory` 已有 `not_implemented`/`agentcore`） |
| 3 | **`search_owner_memory` 接线** | agent.py L184-188 现返回 `[]` 且不记证据 → 改为委托注入的 `MemoryService.search`；本地返回 `[]` → **仍不记 memory 证据**（不伪造）；stub/真实服务返回记录时 → 证据 `source="memory"`、`evidence_id=f"memory:{record_id}"`，proposal 可引用并经 `validate_proposal_evidence` 校验。用**构造注入**的 `StubMemoryService` 离线证明接线（镜像 Day-2 `StubBedrockClient`）。**场景 C「记忆改变建议」= 条件项** | agent.py L184-188、L108-132（台账机制）；models.py L198-209（`EvidenceItem.source` 已含 `memory`）；reviews/day2.md nit#3（构造注入范式） |
| 4 | **反馈持久化（Backend）** | 新增 `feedback` 表（`SCHEMA_VERSION` 2→3；用 `CREATE TABLE IF NOT EXISTS` 建新表，无需 `ALTER`，但仍 bump `user_version` 以纳入迁移闸）。`repository.py` 增 `FeedbackRecord` 内部 dataclass（原文/scope/status/ids，**非响应 DTO**，同 `RunRecord` 口径）+ `save_feedback`/`get_feedback`/`list_feedback`。幂等：T5「重试复用本地 feedback ID 防止重复发送」→ 以幂等键 `UNIQUE(owner_id, idempotency_key)` 去重实现 | repo_sqlite.py L43-94（`SCHEMA_VERSION`/`_migrate`/`_SCHEMA`）；repository.py L62-86（`RunRecord` 内部字段口径）；任务单 T5 L296 |
| 5 | **`conversation_id` / new-session** | `POST /api/demo/new-session` 服务端生成新 `conversation_id`，**保留宠物记忆、事实与登录**（不重置配额）。`conversation_id` 作为 AgentCore `session_id`，**绝不充当宠物身份**；记忆检索走 owner/pet namespace，故跨 new-session 不丢记忆（这正是场景 C 跨会话演示的机制）。响应回显 `conversation_id`，`StateView` 增该字段。会话仍进程内（裁定 6），故 `conversation_id` 存于 owner 级进程内映射，重启复位（诚实标注） | 任务单 L143/T5 L295；Day-2 计划 L18（`conversation_id` 无消费者，顺延 Day-3） |
| 6 | **会话持久化（裁定顺延）** | 裁定 **Day-3 会话仍留进程内存**（auth.py L33/L38 不改）：A13 验收是 **run 状态可恢复**（SQLite 已持久），单操作者重启后重登录成本极低且更安全；把 session/CSRF token 落盘会新增「静态密钥」面而**零验收收益**。重启复验测试**重新登录**。作为**诚实边界**披露，非缺陷。（handoff §12 曾列「会话持久化」为 Day-3 依赖，故此处显式裁定顺延） | auth.py L32-38；handoff §9/§12；总方案 L135（A13=状态可恢复） |
| 7 | **worker 真并发（闭合 Day-2 nit#6）** | worker 由**顺序 drain** 改为**有界线程池**（池大小=`max_concurrent_global`=2）：先 `AdmissionControl.try_acquire` 再 claim，处理完 release；每个在处理的 run 用**唯一 worker_id**（per-task）以免并行下租约归属含糊。复验会话 1/全站 2 上限**有真实生产触发路径**（慢 `ProgrammableProposer` + 断言并发数 ≤N）。Day-2 的 CAS/白名单/租约原语必须在**真并行**下继续成立 | worker.py L36-67（`AdmissionControl`）、L166-203（顺序 `drain_once`）；reviews/day2.md nit#6（「Day-3 引入并发执行时必须复验」） |
| 8 | **跨进程双批准（A04）** | 用**两个独立 `SqliteRepository` 实例指向同一文件库**（= 两进程/两副本的 DB 争用面）。文件库启用 **WAL + busy_timeout** 保证跨连接写安全。断言 **DB 不变式**（`count_receipts==1`、恰一个 `SUCCEEDED`、配额只加一次、败者 409），**不依赖共享 device 计数器**（执行器是进程内对象）。诚实边界：SQLite 两连接 **≠** DynamoDB 多副本（Day-4/T7） | repo_sqlite.py L128-140（连接/锁）、L340-348（`transition_run` CAS）；test_worker.py L419-467（同进程并发范式）；handoff §9 |
| 9 | **真实 OS 进程重启（A13）** | (a) **必过** = 文件库两 repo 实例的**逻辑重启**测试：等待审批仍在且可批准、终态不重跑、过期租约可重领、**`ANALYZING`+活租约不被二次分析**（租约到期后可领）；(b) **尽力** = 真 **subprocess kill/relaunch** 集成测试（marker `restart`，uvicorn 跑临时文件库，healthz 门控），产出「真实进程重启」证据。「处理中」恢复是相对 Day-2 的**新覆盖面** | test_recovery.py L18-34；repo_sqlite.py L233-249（`list_claimable_runs` 租约谓词）；handoff §9（真实进程重启顺延 Day-3） |
| 10 | **`memory_backend` 配置（镜像 Day-2 裁定 15）** | `config.py` 增 `PAWTWIN_MEMORY_BACKEND=not_implemented\|agentcore`（默认由 mode 推导：local→`not_implemented`，aws→`agentcore`）。`model_validator` 加：`mode=aws ⇒ memory=agentcore` 且必须有 `AGENTCORE_MEMORY_ID`（L118-127 已要求）；禁止 `mode=aws`+`not_implemented`。`aws_connected` 继续**恒 False** 直到存储+模型+记忆全真实连通。`StateView.memory` 字段已存在，前端同时展示 analyzer/storage/memory 三标签 | config.py L27-30、L96-146；models.py L302-313 |
| 11 | **AgentCore 依赖 extra（镜像 Day-2 strands 硬门）** | 做成 `[project.optional-dependencies]` 的 `memory` extra（**版本由 `uv add`/`uv lock` 当时解析锁定，不预填**）。**单独提交先行验证** `uv sync --frozen --extra memory` 可复现；`memory.py` **强制延迟导入**，缺失/无凭据 → 具名 `MemoryUnavailable`，`memory_backend` 保持 `not_implemented`，**绝不伪造**。**锁更新失败则 Day-3 完全不动 `pyproject/uv.lock/Dockerfile/CI`**。CI 增该 extra 的 `uv lock --check` | pyproject.toml L16-23（`bedrock` extra 范式）、L35-44（markers/addopts）；Day-2 计划 §7 硬门 |
| 12 | **契约（门 0）** | openapi 路径 **11→14**（+`/api/feedback`、+`/api/feedback/{feedback_id}`、+`/api/demo/new-session`），补 401/403/404/422 `responses`。`domain.schema.json` **仍恰为 6 输入模型 + `RunState`**（`FeedbackIn` 已在冻结集内；`FeedbackView`/`NewSessionView` 是响应 DTO，**只进 OpenAPI**）。`test_contracts.py`：`ACTIVE_PATHS` +3、**改写 L6-8 注释**（「Feedback and memory routes … NOT in this set」将成假陈述）、`$defs == 6` 断言不动 | test_contracts.py L6-21、L46-53；contracts.py L8-10（`DOMAIN_MODELS` 已含 `FeedbackIn`）；models.py L70-72 |
| 13 | **前端记忆区** | 替换 App.tsx L564-566 的 `memory-placeholder`：反馈输入（text + scope `observation`/`today_only`）+ 提交、反馈列表带 `memory_status` 徽章与 `memory_backend` 标签、「新会话」按钮显示 `conversation_id`。诚实红线：`memory=not_implemented` → 显示「长期记忆：未实现（无账号）」、反馈「已保存原文（未提炼）」，**绝不**「已检索到记忆」。`api.ts` 增 `FeedbackView`/`MemoryStatus`/`postFeedback`/`getFeedback`/`postNewSession`，**零新增依赖**。新增 e2e feedback/memory spec | App.tsx L551-567（任务与记忆区）、L57-61（`SOURCE_LABELS.memory` 已有）；api.ts L96-106（`StateView`）；Day-2 裁定 22（badge 严格模式） |
| 14 | **所有权与临界段** | `memory.py` = **AI**；`repository.py`/`repo_sqlite.py`（反馈持久化）+ `worker.py`（并发）+ `api.py`（feedback/new-session 路由）= **Backend**；`models.py`/`config.py`/`contracts/`/`main.py` = **Coordinator**（门 0/C1/C3）；`frontend/src/` = **Frontend**；`pyproject/uv.lock/Dockerfile/ci.yml/preflight/smoke` = **OPS/Coordinator**。`MemoryService` 协议 + `AgentContext` 注入 seam + `FeedbackRecord` **由 Coordinator 在门 0 冻结**，否则 Backend/AI 会各造不一致接口 | AGENTS.md L26-33；Day-2 计划 §2 所有权补裁 |

## 2 门 0 · 契约与配置冻结（Coordinator 独占，前置串行，单独提交）

- [ ] `models.py`：`MemoryStatus`（`Literal["saved","processing","available","failed"]`）、`MemoryBackend`（`Literal["not_implemented","agentcore"]`）、`FeedbackView{feedback_id,scope,text,memory_status,memory_backend,created_at,conversation_id?}`、`NewSessionView{conversation_id}`、`StateView` +`conversation_id`（裁定 5/13）。**保持** `FeedbackIn` 不动（已冻结）、内部记账字段不入响应。
- [ ] `config.py`：`memory_backend` 设置 + `model_validator` 交叉校验（裁定 10）。
- [ ] **书面冻结 `MemoryService` seam 与 `FeedbackRecord`**（裁定 1/4）并通知 Backend/AI。
- [ ] `contracts/`：新增 3 条路径 + `responses`；`domain.schema.json` **仍恰为 6 输入模型 + `RunState`**；重生成并 `--check` 逐字节通过。
- [ ] 同步测试：`test_contracts.py`（`ACTIVE_PATHS` +3、改写 L6-8 注释、`$defs == 6` 不动）；`conftest.py` autouse 清理清单**补齐每一个新环境变量**（`PAWTWIN_MEMORY_BACKEND` 等）+ 新增 `memory_service`/文件库 `file_repo`(tmp_path)/`StubMemoryService` fixture；`contracts.py` 导出时**钉死** `memory_backend="not_implemented"`（防宿主 env 漂移）。
- [ ] 记录 **Day-3 契约冻结提交 ID**（保留 `94216df`/Day-2 冻结点为历史）。**冻结前** Backend 只写 test skeleton、AI 只做适配器骨架、Frontend 只做标注性组件。

## 3 并行实现（受门 0 约束）

### 3.1 AI（AI-02：记忆适配器与检索接线）
- [ ] `memory.py`（新增）：`MemoryService` 协议 + `LocalFakeMemory`（`not_implemented`：`submit_feedback`→`saved`、`search`→`[]`，**绝不** `available`）+ `AgentCoreMemory` 骨架（**延迟导入**，裁定 11；缺依赖/凭据→具名 `MemoryUnavailable`）+ `StubMemoryService`（构造注入，离线测试用，镜像 Day-2 `StubBedrockClient`）。
- [ ] `agent.py`：`AgentContext` 注入 `MemoryService`（裁定 1），`search_owner_memory` 委托服务、返回记录时记 `source="memory"` 证据（裁定 3）；**保持** `get_recent_events` 不返回 note 原文（注入通道）。
- [ ] 测试：`tests/test_memory.py`（`saved`≠`available`、`today_only` 不成永久偏好、stub 记忆→`source="memory"` 证据链 + proposal 引用 + 证据校验、缺依赖/凭据 fail-closed 不伪造）；真实 AgentCore 往返放 `tests/test_agentcore_live.py`（marker `agentcore_live`，默认排除，具名 skip `BLOCKED: 无 AWS 账号`）。测试名不得含 works/passes/verified 等云端暗示。

### 3.2 Backend（BE-04：反馈持久化 → worker 并发 → 跨进程/重启）
- [ ] `repo_sqlite`：`feedback` 表 + 迁移 bump（裁定 4）；文件库 **WAL + busy_timeout**（裁定 8）；`save_feedback`/`get_feedback`/`list_feedback` + 幂等去重。
- [ ] `repository.py`：`FeedbackRecord` + 协议方法同步（Day-4 DynamoDB 需同构）。
- [ ] `worker.py`：有界线程池并发 + per-task worker_id + 先准入后 claim（裁定 7）。
- [ ] `api.py`：`POST/GET /api/feedback`（登录+CSRF、`memory_status` 诚实投影）、`POST /api/demo/new-session`（裁定 5）；`get_state` 回显 `memory_backend`/`conversation_id`。
- [ ] 测试先红后绿：`test_worker.py` 扩（**真并发**下会话 1/全站 2 上限有生产路径、per-task 租约归属）；`test_recovery.py`/新 `test_restart.py`（文件库两实例逻辑重启 + `ANALYZING`+活租约不二次分析）；新 `test_concurrency_crossprocess.py`（两文件库连接并发双批准 → DB 不变式）；`test_feedback_api.py`（saved 原文、幂等、401/403/404/422、new-session）。

### 3.3 Frontend（FE-03：记忆区）
- [ ] `api.ts` + `App.tsx`：裁定 13 的反馈输入/状态徽章/新会话/诚实标注；`memory-placeholder` 移除。
- [ ] e2e：新增 `feedback.spec.ts`（提交 observation→`saved`+「未实现」标签、new-session→`conversation_id` 变化、记忆区**绝不**声称检索到记忆）；沿用 `workers:1`/`expect.timeout`/各 spec 自复位。

### 3.4 OPS/Coordinator（OPS-03）
- [ ] `memory` extra + `uv.lock`（**独立提交先行验证**，裁定 11 硬门）；CI 增该 extra 的 `uv lock --check`；`Dockerfile` 加 `--extra memory`（**本机无 Docker → 只声明「已修改、未构建验证」**）。
- [ ] `.env.example` 补 `PAWTWIN_MEMORY_BACKEND`/`AGENTCORE_MEMORY_ID` 说明；`preflight.ps1` 增 AgentCore 只读段（无凭据→`NOT EXECUTED`，不由 env 推断连通）；`scripts/agentcore-smoke.ps1`（无凭据→退出码 2，**绝不 `exit 0`**）；扩 `infra/cloud-access-checklist.md` 的 AgentCore 最小验证与用量行。

## 4 串行临界段与执行顺序（单机现实，≤4 活动 Agent）

不可并行临界段：**C1**=`models.py`+`config.py`+`contracts/`+契约测试+**记忆 seam 冻结**；**C2**=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`（单独提交）；**C3**=`main.py` 装配（注入 `MemoryService`、worker 池、conversation；也是契约导出入口）；**C4**=`STATUS`+`TASKBOARD`+`evidence`。

```
S0 C1 门0冻结（Coordinator，~2h）
S1 Backend 反馈持久化+迁移（~3h）        ┐ 可与 S2 并行（seam 已冻结）
S2 AI memory.py+search接线+stub+test（~3h） ┘
S3 Backend worker真并发+跨进程+重启（~4h）
S4 C3 main.py 装配（Coordinator+Backend，~2h；须让出 Backend 槽）
S5 Frontend 记忆区+反馈+新会话+e2e（~4h；S0 之后即可与 S1–S4 并行）
S6 C2 memory extra/CI/Docker/preflight/smoke（Coordinator+OPS，~2h，硬门）
S7 集成 + verify.ps1 + e2e 全跑 + C4 文档（Coordinator，~2h）
S8 非作者独立审查 + 修复 + 复跑（~2h）
```
合计 ≈ **22–24h 串行 Agent 工时**（= 全量 Day-3 **减去** AgentCore 真实实装）。常驻 = Coordinator + Backend + AI + Frontend（=4）；Reviewer 与 OPS 用空槽串行复用，**Reviewer 不得由作者充当**。派发前在 TASKBOARD 追加认领记录。新增任务行建议：`BE-04 反馈持久化+worker并发+跨进程/重启`、`AI-02 记忆适配器+检索接线`、`FE-03 记忆区+反馈+新会话`、`OPS-03 memory extra/preflight/smoke`。

## 5 A01–A14 在 Day-3 的覆盖（本地判据 vs 顺延）

| 编号 | Day-3 判定 | 说明 |
|---|---|---|
| A01/A02 正常·拒绝 | **回归必过** | Day-2 闭环 + approve/decline e2e 仍须全绿 |
| A03 审批后事实变化 | **回归必过** | 零模型调用重评估（Day-2 已实现） |
| A04 双批准 | **必过（升档：跨进程）** | 裁定 8 文件库两连接 → DB 不变式；**跨副本 DynamoDB → Day-4** |
| A05 事件重传 | **回归必过** | 去重 + 不二次调模型 |
| **A06 反馈与新会话** | **部分（结构）** | 本地：反馈 `saved` + new-session + `conversation_id` 管线；**真实 retrieve → 条件项** |
| **A07 观察 vs 推断** | **部分（结构）** | 本地：`today_only` 不成永久偏好、`observation` 无云不提炼（`saved`+未实现）；真实提炼 → 条件项 |
| **A08 事实与旧记忆冲突** | **部分（结构）** | 记忆为空 → 只能验证「硬策略优先、记忆文本不授权」；真实冲突 → 条件项，**不得声称通过** |
| A09 信息不足 | **回归必过** | Day-2 已实现 |
| A10 失败/超时/迟到回执 | **回归（部分）** | 沿用 Day-2 归约（重复回执幂等 + UNKNOWN 不盲目重试） |
| A11 恶意指令 | **回归必过（本地）** | note/记忆文本注入仍被 policy/审批挡住；模型在环 → 条件项 |
| A12 未授权 | **必过** | 现有 401/403 + **feedback/new-session 端点同样受保护** + 全仓无凭据 |
| **A13 重启/租约** | **必过（升档：真实进程）** | 裁定 9：文件库逻辑重启 + `ANALYZING`+活租约不二次分析；尽力项 subprocess 真重启 |
| A14 随机改事实 | **回归必过（本地）** | Day-2 已实现；真模型依据变化 → 条件项 |

SQLite/两连接 PASS **不得**替代云测；Day-3 证据须把「本地通过」与「云端未验证」分列（沿用 STATUS.md L63-67 体例）。

## 6 完成的硬性证据（Definition of Done）

> 每项给**命令与实测数字**，不接受「全绿」二字。

- [ ] `uv run --frozen pytest` → 通过数 = **144 + Day-3 新增数**（明列新增文件与用例名）；`ruff check .` 无告警；`uv lock --check`（若动依赖）一致。
- [ ] `export_contracts.py --check` → `Contracts are current`；`openapi.json` 路径数 = **14**；`domain.schema.json` 的 `$defs` **恰为** 6 输入模型 + `RunState`。
- [ ] `npm run typecheck`/`build` 通过；e2e **≥8 项**（Day-2 的 7 + feedback/memory ≥1），列用例名与配置。
- [ ] **记忆诚实**：测试证明无账号时反馈恒 `saved`+`memory_backend=not_implemented`、`search_owner_memory` 返回 `[]` 且**不产生** memory 证据；stub 服务返回记录时才出现 `source="memory"` 证据且 proposal 可引用；`today_only` 不生成永久偏好。
- [ ] **并发/幂等**：worker 真并发下会话 1/全站 2 上限被生产路径触发（慢 proposer 断言并发 ≤N）；跨进程（两文件库连接）双批准 → `count_receipts==1`、恰一个 `SUCCEEDED`、配额一次、败者 409。
- [ ] **重启恢复**：文件库新实例复验（等待审批仍可批准、终态不重跑、过期租约可领、**`ANALYZING`+活租约不二次分析**）；尽力项 subprocess 真 kill/relaunch 证据（若仅逻辑级则**明写「真实进程重启未验证」**）。
- [ ] 文档：`STATUS.md` 新增 Day-3 三档表 + 本地/云端双列 + 提交表 + **Day-3 冻结提交 ID**；`evidence/day3-handoff.md`（按 `HANDOFF_TEMPLATE.md` 12 项，含「未运行的检查及原因」）；`evidence/day3-local.md`（命令/结果/**这不证明什么**）；`evidence/day3-cloud-blocked.md`（AgentCore 条件项 + 就绪后最小验证）；`reviews/day3.md`（**非作者**只读审查，逐条记「处理/复测」）；`TASKBOARD.md` 第 3 日派发与认领。Day-1/Day-2 历史文档**只可追加后记，不改写**。
- [ ] 零副作用：无秘密入库（附 grep 记录）、无云资源、**无 AWS 费用**、无远程推送、无镜像构建（未构建则明写）、未以本地替身/stub/SQLite PASS 冒充云端完成。

**禁止出现的表述**（文档/提交/前端文案）：「AgentCore 记忆已检索/已提炼/available」（无真实检索证据时）；「跨会话记忆已验证」；「三场景全部通过」（场景 C 真实记忆为条件项时）；「真实进程重启已验证」（若仅两实例逻辑级）；「跨副本双批准已验证」（SQLite 两连接 ≠ DynamoDB 多副本）；「worker 支持多副本并发」（仅进程内并发）；「AWS 已连接」；把 `saved` 原文说成「已生成记忆」；把 stub/`local_fake` 输出称作真实模型/记忆而不带标注；任何**预填**的准确率/成功率/延迟；任何口令/CSRF token/session id/conversation 密钥入文档或日志。

## 7 降级与关键路径

- **关键路径** ≈ 门 0（C1，~2h）→ Backend 反馈持久化 ‖ AI memory.py → worker 并发 → 跨进程/重启 → `main.py` 装配（C3）→ 集成 e2e → 独立审查（≈ 22–24h 串行）。**最易滑期**：worker 从顺序到**真并行**后 CAS/租约/准入的正确性（裁定 7），以及**真实 OS 进程重启**测试的稳定性（裁定 9b，Windows subprocess + 端口绑定 + healthz 门控）。
- **AgentCore 实装硬门**：先只做 `uv add --optional memory boto3`（或官方 AgentCore SDK）+ `uv lock` 的**独立提交**，验证 `uv sync --frozen --extra memory` 可复现；**失败则 Day-3 完全不动 `pyproject/uv.lock/Dockerfile/CI`**，改为「保留 `MemoryService` 接口 + 延迟导入 + 缺依赖/凭据映射为 `not_implemented`（绝不伪造记忆）」，真实实装顺延到有账号日。
- **降级预案**：A 真并行引入竞态未收敛 → 保留顺序 drain 为默认（业务闭环不破），把并发路径记为「已实现未验证」并顺延，**不得**删除 CAS/白名单/准入；B subprocess 真重启不稳定 → 以文件库两实例逻辑测试为**必过**保底，真进程项**记为滑期而非通过**；C 前端滑期 → G8 降为 API 级 feedback 集成测试保底，浏览器项记为滑期；D 门 0 超时 → 先冻结 `models.py`+`config.py`+记忆 seam，feedback 路由契约推当日午后，不阻塞 Backend/AI。
- **需用户确认的点（已随计划批准）**：①裁定 6「会话仍留进程内存、重启后重登录」；②裁定 8「跨进程 = SQLite 两连接，非 DynamoDB 多副本」与裁定 9「真实 OS 进程重启为尽力项、逻辑重启为必过」的诚实边界；③Day-3 建在未提交的 Day-2 工作区之上（提交需用户授权）；④Day-3 继续单机串行 + 总负责人代写各角色 + 非作者独立审查（照 Day-1/Day-2 体例）。
