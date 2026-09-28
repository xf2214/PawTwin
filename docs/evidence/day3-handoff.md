# Day-3 交接与证据（2026-09-26）

> 依 `docs/HANDOFF_TEMPLATE.md` 的 12 项结构。本机为单一开发环境，Day-3 由**总负责人 Agent 串行**完成 Coordinator/Backend/AI/Frontend/OPS 各角色工作，逻辑上遵守 `AGENTS.md` 的文件所有权与不重叠写入；未拉起并行工作树（与 Day-1/Day-2 同一执行方式，用户已确认）。独立审查以只读代码审查（非作者）补充，见 `docs/reviews/day3.md`。

## 1 任务 ID 与范围

- **门 0（C1）契约与配置冻结**（Coordinator 独占）：`models.py` 新增 `MemoryStatus`/`MemoryBackend`/`FeedbackScope`/`FeedbackView`/`NewSessionView`，`StateView` 增 `conversation_id`/`feedback`；`config.py` 增 `memory_backend` 设置与交叉校验；书面冻结 `MemoryService` seam 与 `FeedbackRecord`；OpenAPI 补 3 条路径与 401/403/404/422。
- **AI-02**：`memory.py`（`MemoryService` 协议 + `LocalFakeMemory` + `AgentCoreMemory` 骨架 + `StubMemoryService` + `build_memory`）、`agentcore_client.py`（boto3 延迟导入、fail-closed）、`agent.py` 的 `AgentContext` 注入 `MemoryService` 与 `search_owner_memory` 接线。
- **BE-04**：反馈持久化（`feedback` 表、迁移 v3、WAL、`FeedbackRecord` + `save/get/list/set_feedback_status`、幂等）、`worker.py` 有界线程池真并发、`api.py` 的 `feedback`/`new-session` 路由与 `get_state` 回显、`auth.py` 的 `Session.conversation_id` + `new_conversation`、跨进程双批准与真实进程重启复验。
- **FE-03**：`api.ts` 记忆/反馈类型与调用、`App.tsx` 记忆区（反馈输入 + 状态徽章 + 新会话）、`styles.css`、`shell.spec.ts` 更新、`feedback.spec.ts` 新增。
- **OPS-03**：`memory` optional extra（`boto3==1.43.102`）+ `uv.lock`、`Dockerfile --extra memory`、`.env.example`、`preflight.ps1` AgentCore 只读段、`agentcore-smoke.ps1` + `agentcore_smoke.py`、`infra/cloud-access-checklist.md`、README 与角色简报。
- **C3**：`main.py` 装配 `MemoryService`、`readyz`/`bootstrap` 分组件诚实反映记忆后端。

## 2 起始提交 / 交付提交

- 起始基线：`dc8dc10`（分支 `chore/bootstrap`，Day-1 完成）。**Day-2 与 Day-3 改动均未提交**，共处同一脏工作区（Day-2 交付时即未提交，等待用户授权）。
- 交付提交：**待用户授权后按逻辑分组提交**（见第 12 项）。本文件记录交付内容与实测证据，不预填提交 ID。
- Day-1 契约冻结 ID `94216df` 保留为历史冻结点，未改写。Day-3 的契约冻结点将在提交后记入 `docs/STATUS.md` 与 `docs/TASKBOARD.md`。

## 3 工作树 / 分支

单一工作区 `c:\Users\11831\Desktop\hks\outputs\pawtwin-app`，分支 `chore/bootstrap`。未新建隔离工作树（串行执行，无并发写冲突）；临界段按 C1（契约/配置/记忆 seam）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）顺序串行通过。

## 4 改动文件

- **新增（Day-3，13 + 4 文档）**：`backend/pawtwin/memory.py`、`backend/pawtwin/agentcore_client.py`、`tests/test_memory.py`、`tests/test_feedback_api.py`、`tests/test_restart.py`、`tests/test_restart_subprocess.py`、`tests/test_concurrency_crossprocess.py`、`tests/test_agentcore_live.py`、`frontend/e2e/feedback.spec.ts`、`scripts/agentcore-smoke.ps1`、`scripts/agentcore_smoke.py`、`docs/plans/PawTwin_Day3_开发计划.md`，及本目录 `day3-handoff.md`/`day3-local.md`/`day3-cloud-blocked.md` 与 `docs/reviews/day3.md`。
- **契约与配置（Coordinator）**：`backend/pawtwin/models.py`、`config.py`、`main.py`、`contracts/openapi.json`（重生成，14 条路径）、`pyproject.toml`、`uv.lock`、`Dockerfile`、`.env.example`。`contracts/domain.schema.json` **未变**（仍恰为 6 输入模型 + `RunState`）。
- **后端（Backend）**：`repository.py`、`repo_sqlite.py`、`worker.py`、`api.py`、`auth.py`。
- **AI**：`agent.py`（+ 上述新增 `memory.py`/`agentcore_client.py`）。
- **前端**：`src/api.ts`、`src/App.tsx`、`src/styles.css`、`e2e/shell.spec.ts`（+ 新增 `e2e/feedback.spec.ts`）。
- **测试同步**：`tests/conftest.py`、`test_contracts.py`、`test_app.py`、`test_worker.py`（+2 并发用例）。
- **文档/OPS**：`README.md`、`infra/cloud-access-checklist.md`、`scripts/preflight.ps1`、`docs/TASKBOARD.md`、`docs/STATUS.md`、`docs/agents/{ai,backend,frontend,infrastructure}.md`。
- 注：工作区还含 Day-2 未提交改动（如 `docs/agents/reviewer.md`、`tests/test_repository.py`、`bedrock_client.py` 等），不属本次 Day-3 交付，未在此重复列举。

## 5 已实现行为

- **记忆 seam 接线**：`MemoryService` 协议冻结；`LocalFakeMemory`（`not_implemented`）保存原文报 `saved`、`search` 返回 `[]`，**绝不** `available`/伪造；`AgentCoreMemory` 延迟导入 `agentcore_client`，缺依赖/凭据 → 具名 `MemoryUnavailable`；`StubMemoryService` 供离线证明接线。`build_memory` 与 `config` 双向 fail-closed（`mode=aws ⇒ memory=agentcore` 且需 `AGENTCORE_MEMORY_ID`；`memory=agentcore` 需 id+region）。
- **检索证据**：`AgentContext.search_owner_memory` 委托 `MemoryService`；本地返回 `[]` 且**不记** memory 证据；stub/真实返回记录时生成 `evidence_id=f"memory:{record_id}"`、`source="memory"` 台账项，proposal 可引用并经 `validate_proposal_evidence` 校验，伪造 id 仍落 `UNKNOWN_EVIDENCE`。
- **反馈端点**：`POST /api/feedback`（先入原文，`Idempotency-Key` 幂等去重；本地 `memory_status=saved`，仅未提交过的记录才交后端处理）、`GET /api/feedback/{id}`（回读状态，owner 校验 404）、`POST /api/demo/new-session`（轮换 `conversation_id`，保留登录/事实/记忆）；均需登录，写操作需 CSRF。`StateView` 回显 `memory`/`conversation_id`/`feedback`。
- **worker 真并发**：有界线程池（`max_concurrent_global`），先准入后 claim、per-task 唯一 `worker_id`、处理完 release、取消的排队任务归还准入；`peak_concurrency` 高水位。Day-2 的 CAS/白名单/租约/`_settle` 原语在真并行下不变。
- **持久化/恢复**：`feedback` 表迁移（`SCHEMA_VERSION` 2→3，`CREATE TABLE IF NOT EXISTS` + `PRAGMA user_version` 闸）；文件库 WAL + busy_timeout；跨进程（两连接）双批准 → DB 不变式；文件库两实例逻辑重启 + subprocess 真进程重启（等待审批/终态/过期租约/`ANALYZING`+活租约不二次分析）。
- **前端**：记忆区（反馈输入 + scope 选择 + `memory_status` 徽章 + `memory_backend` 标签 + 新会话按钮 + `conversation_id`），`not_implemented` 时诚实显示「未实现（无 AWS 账号）」「已保存原文（未提炼）」，绝不声称检索到记忆；`impl-labels` 保留「长期记忆：未实现」子串，`mode-badge` 保留 `LOCAL`/`AWS 未连接`。

## 6 仍然模拟或未实现的内容

- 传感器事件与设备执行**始终为模拟**（`source=simulator`、`receipt.simulated=True`）；PawLink 项圈为概念。
- **未实现/未验证**：真实 AgentCore 提炼与检索（无账号）、真实 Bedrock 调用（无账号）、DynamoDB 真表与**跨副本多 replica**、云部署与访问控制、HTTPS、镜像构建、Alexa+。
- **已实现但未验证**：`agentcore_client.py` 依 boto3 `bedrock-agentcore` 数据面签名编写，**未经真实账号验证**，异步提炼轮询生命周期未跑；`Dockerfile` 已改（`--extra memory`）但本机无 Docker，**镜像未构建**。
- **已知局限（诚实披露）**：会话仍进程内存（裁定 6，重启后需重登录；A13 的 run 状态恢复由文件库保证）；`conversation_id` owner 级进程内、重启复位；worker 并发上限仍**仅进程内**（跨副本需数据库级计数，Day-4/T7）；跨进程双批准以「两个 SQLite 连接」为本地代理，**不等价于** DynamoDB 多副本条件写；本地 `search_owner_memory` 恒返回空，故场景 C「记忆改变建议」的真实价值为条件项。

## 7 接口变化与消费者影响

- OpenAPI 路径由 **11 → 14**（+`/api/feedback`、+`/api/feedback/{feedback_id}`、+`/api/demo/new-session`），业务路由补 401/403/404/422 的 `responses`。`domain.schema.json` 的 6 个输入模型**未变**（`FeedbackIn` 早已在冻结集内；`FeedbackView`/`NewSessionView` 是响应 DTO，只进 OpenAPI）。
- `StateView` 新增 `conversation_id: str|null` 与 `feedback: list[FeedbackView]`（`memory` 字段类型由内联 Literal 改为等价 `MemoryBackend` 别名，schema 不变）。前端 `api.ts` 已在同一交付内同步，`npm run typecheck` 通过。
- 新增公开响应 DTO：`FeedbackView`/`NewSessionView`；新增内部记录 `FeedbackRecord`（`owner_id`/`idempotency_key` 不入响应）。
- 内部 seam 新增：`MemoryService`（`submit_feedback`/`get_status`/`search`）；`AgentContext.__init__` 与 `AnalyzerProposer.__init__` 增可选 `memory` 参数（默认 `None`，向后兼容）；`Repository` 协议增 `save_feedback`/`get_feedback`/`list_feedback`/`set_feedback_status`（Day-4 DynamoDB 须同构实现）。
- 配置新增 `PAWTWIN_MEMORY_BACKEND`（`conftest.py` autouse 清理清单已同步）；`pyproject.toml` 新增 `memory` optional extra 与 `agentcore_live`/`restart` markers，`addopts` 排除 `agentcore_live`（计费）。

## 8 运行的检查（命令 / 结果）

| 命令 | 结果 |
|---|---|
| `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **184 passed, 11 skipped**（审查后 +2 回归；多次运行一致）；11 skip = 5 `agentcore_live` + 4 `bedrock_live` + 1 `bedrock_offline`（base 环境未装 strands）+ 1 `restart` 尽力项占位，均具名 |
| `uv run --frozen ruff check .` | All checks passed |
| `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current（14 条路径） |
| `uv lock --check` / `uv sync --frozen --extra memory` | 均 exit 0（`boto3==1.43.102`，无新增下载） |
| `npm run typecheck` / `npm run build` | 通过（Node 24.19.0，vite 8.3.0） |
| `npx playwright test`（`workers:1`、background、local_fake、chromium-1194） | **10 passed**（8.9s）：approve×4 / decline / feedback×3 / shell×2 |
| `./scripts/verify.ps1` | 全绿，EXIT=0 |
| `./scripts/preflight.ps1` | 通过；AgentCore 段 `NOT EXECUTED`（memory id/boto3 均 False） |
| `./scripts/agentcore-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2** |

明细与「这不证明什么」见 [day3-local.md](day3-local.md)。

## 9 未运行的检查及原因

- **真实 AgentCore 提炼/检索往返、strategy ACTIVE 检查、场景 C 真实记忆影响、A06/A07/A08 真实记忆部分**：无 AWS 账号授权，未执行。`tests/test_agentcore_live.py` 以 5 条**具名 skip** 留痕（理由 `BLOCKED: no AWS account is authorised…`），`scripts/agentcore-smoke.ps1` 输出 `NOT EXECUTED` 并退出码 2。详见 [day3-cloud-blocked.md](day3-cloud-blocked.md)。
- **真实 Bedrock 往返 / 真模型参与场景**：无账号，未执行（同 Day-2，`test_bedrock_live.py` 4 条具名 skip）。
- **DynamoDB 条件写/事务/跨副本多 replica 并发**：无账号，`repo_dynamo` 未实现；**不以 SQLite/两连接 PASS 替代**（Day-4/T7）。
- **Docker 镜像构建、Linux 运行时、HTTPS/访问控制、部署与清理**：本机 PATH 无 Docker/AWS CLI，未执行（Day-4/T7）。`Dockerfile` 改动只记为「已修改、未构建验证」。
- **真实 uvicorn 进程 kill-mid-analysis 后重启**：`test_restart_subprocess.py` 覆盖了「子进程写库→退出→新进程恢复并恰执行一次」的真进程边界；「运行中被 kill 于 ANALYZING」的定时杀进程用例作为**具名 skip 的尽力项**保留（单机上端口绑定/启动时序易 flaky），其语义由 `test_restart.py` 的「`ANALYZING`+活租约不二次分析、过期后可领」逻辑测试覆盖。
- **GitHub Actions 远程运行**（含 `memory` extra 的 `uv lock --check`）：未推送远程，CI 改动未在远端执行过。
- **`agentcore_client` 的 boto3 `bedrock-agentcore` 调用路径**：需真实 SDK 与账号，离线不可验证；已标注为未覆盖面。

## 10 独立审查发现与处理

见 [docs/reviews/day3.md](../reviews/day3.md)：非作者只读审查（CodeReview 子代理），结论 **PASS-WITH-NITS**（8 项高信号逐条核实全 ✅，14 条裁定与诚实红线未破），发现 3 个 nit（worker 关闭期准入槽泄漏、`post_feedback` 未归约 `MemoryUnavailable`、缺 v2→v3 迁移回归测试），均已修并复跑（**184 passed**、e2e **10 passed**、`verify.ps1` EXIT=0）；其中 nit-2 附负向验证（回退后新测试因 500 转红）。

## 11 云资源或费用变化

**无**。未创建任何云资源、未调用任何收费模型或记忆服务、未产生任何费用、未推送远程、未构建镜像。`boto3==1.43.102` 仅作为 optional extra 写入锁文件（本已是 strands-agents 的传递依赖，无新增下载），CI 与默认本地环境不安装它。

## 12 下一步依赖 / 需总负责人决定

1. **提交授权**：Day-2 与 Day-3 改动均未提交。Day-3 建议分组：①门 0 契约与配置冻结（= Day-3 冻结提交）②后端反馈持久化/worker 并发/跨进程重启 ③AI 记忆适配器与 AgentCore 客户端 ④前端记忆区与 e2e ⑤OPS 依赖/脚本/镜像 ⑥文档与证据。是否提交、是否先提交 Day-2、以及是否推送远程，需用户明确授权。
2. **账号就绪即刻执行**：`uv sync --frozen --extra memory` → 设置 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 与凭据 → 确认 memory strategy `ACTIVE` → `./scripts/agentcore-smoke.ps1`（计费调用，须在授权预算内）→ `uv run --frozen pytest -m agentcore_live` → 把真实 record id/namespace/event id/时间写入 `docs/evidence/agentcore-call-*.md`，并把 `docs/STATUS.md` 对应条件项从 blocked 改为已验证；随后跑通场景 C（新会话后真实 retrieve 影响建议）。
3. **Day-4/T7 依赖**：`repo_dynamo` 必须同构实现反馈持久化与 Day-2/Day-3 的 CAS/续约/白名单/幂等语义；跨副本并发上限需数据库级计数；`deploy.ps1`/`cleanup.ps1` 尚未编写；T6 的 24 案例集 `scenarios.json` + `evaluate.py` 与非作者集成审查在 Day-4。
4. **需裁定的遗留**：会话是否落 DB 持久化（裁定 6 现为进程内存、重启重登录）；`test_contracts.py` 是否把 `FeedbackView`/`StateView` 字段名集合也冻结成断言（当前仅由 `typecheck` 与 e2e 间接守卫）。
