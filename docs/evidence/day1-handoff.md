# Day-1 交接与证据（2026-09-23）

> 依 `docs/HANDOFF_TEMPLATE.md` 结构。本机为单一开发环境，Day-1 由**总负责人 Agent 串行**完成 Coordinator/Backend/AI/Frontend/OPS 各角色工作，逻辑上遵守 `AGENTS.md` 文件所有权与不重叠写入；未拉起并行工作树。独立审查以只读代码审查（非作者）补充，见 `docs/reviews/day1.md`。

## 任务 ID 与范围

- **门 0 契约冻结**（Coordinator 独占）：BE-01 契约面。
- **BE-01 + BE-02 最小集**：持久化、策略、审批、鉴权、模拟执行、恢复（逻辑级）。
- **AI-01**：只读工具适配接口、本地替身、证据校验（真实 Bedrock 顺延 Day-2）。
- **FE-01**：三主区 + 真实本地 API 联调 + 拒绝闭环 e2e。
- **OPS-01**：云接入清单（仅计划）。

## 起始提交 / 交付提交

- 起始基线：`2751a58`（分支 `chore/bootstrap`，INIT 骨架，26 项后端测试绿）。
- 交付提交（用户授权，未推送远程）：`94216df` 门0冻结（= 冻结提交 ID）→ `f2927cb` 后端测试 → `e20336d` AI-01 → `f45edb8` FE-01 → 本提交 OPS+文档。

## 工作树 / 分支

- 单一工作区 `c:\Users\11831\Desktop\hks\outputs\pawtwin-app`，分支 `chore/bootstrap`。未新建隔离工作树（串行执行，无并发写冲突）。

## 改动文件

- **契约/后端（Coordinator+Backend）**：`backend/pawtwin/models.py`（+响应 DTO、+共享 helper）、`config.py`（+`database_path`/`demo_passphrase`）、`main.py`（app.state 装配、router 先于 StaticFiles、lifespan 关闭 repo）；新增 `repository.py`、`repo_sqlite.py`、`policy.py`、`workflow.py`、`auth.py`、`device_sim.py`、`api.py`。`contracts/openapi.json` 重生成（`domain.schema.json` 未变）。
- **AI**：新增 `agent.py`、`local_fakes.py`。
- **前端**：`src/main.tsx`（改为纯入口）、新增 `src/App.tsx`、`src/api.ts`、`src/styles.css`（扩展）；`playwright.config.ts`（baseURL→后端同源 `:8000`、去 preview）；删 `e2e/scaffold.spec.ts`，新增 `e2e/shell.spec.ts`、`e2e/decline.spec.ts`。
- **测试**：`tests/conftest.py`（fixtures + 清理新 env）、`test_app.py`（+`/api/runs` 404 与鉴权回归）、`test_contracts.py`（路径集合扩为业务集合、删旧否定断言）；新增 `test_policy.py`、`test_repository.py`、`test_recovery.py`、`test_approval.py`、`test_auth.py`、`test_decline_loop.py`、`test_agent.py`。
- **OPS/文档**：新增 `infra/cloud-access-checklist.md`；更新 `docs/STATUS.md`、`docs/TASKBOARD.md`。

## 已实现行为

- 事件按 `(owner_id,event_id)` 去重；新事件独立 run。回执按 `command_id` 幂等，**仅成功记账一次**。租约 60s，可重领过期租约，终态不重处理。
- 硬策略：缺事实 fail-closed、最近喂食、单次上限、日配额；非喂食动作不占配额。
- 状态机：新提案只进 `AWAITING_APPROVAL/BLOCKED/NEEDS_INFO`；审批绑定 `owner+proposal_version+action_digest+有效期`；`facts_version` 变化即拒旧授权并重分析（A03）；拒绝→`DECLINED` 零执行；批准→`EXECUTING`→三态回执→仅成功记账。
- 鉴权：口令服务端哈希、`HttpOnly/SameSite=Lax` 会话、同步令牌 CSRF（本地 HTTP 仅省 `Secure`）；未授权 401、CSRF 失败 403。
- AI：四只读工具（owner 范围服务端注入）、`validate_proposal_evidence` 拒未知证据、`build_analyzer` fail-closed（aws→Bedrock 或报错，绝不静默用替身）。
- 前端：登录门禁、三主区、模式/边界标识取自 `/api/state`、仅 `awaiting_approval` 可批准、发事件后 2s 轮询至终态、reload 后仍显示持久状态。

## 仍然模拟或未实现

- 传感器事件、设备执行均为**模拟**（`source=simulator`、`receipt.simulated=True`）；项圈为概念。
- 未实现：真实 Bedrock 推理、AgentCore 记忆、DynamoDB 真表、异步 worker（当前分析同步）、`demo/facts`/`demo/device-mode`/`feedback` 端点、云部署与访问控制、Alexa+。

## 接口变化与消费者影响

- OpenAPI 路径集合由 3 条 scaffold 扩为 9 条（+`login/logout/state/events/runs/{id}/runs/{id}/approval`）。前端与 e2e 以冻结契约为唯一来源，已同步。`domain.schema.json` 六个输入模型未变。
- **裁定**：`RunView` 暴露 `proposal_version/action_digest`（客户端回显以构造 `ApprovalIn`）；`owner_id/attempt_count/lease_*` 不入响应。

## 运行的检查（命令 / 结果）

| 命令 | 结果 |
|---|---|
| `uv run --frozen pytest` | **71 passed**（基线 26 + 新增 45；含二次检查补强 2 条），1 项第三方弃用警告 |
| `uv run --frozen ruff check .` | All checks passed |
| `python scripts/export_contracts.py --check` | Contracts are current |
| `npm run typecheck` / `npm run build` | 通过（Node 24.19.0） |
| 浏览器 e2e（baseURL `:8000`，Chromium 1194） | **3 passed**（登录门禁/边界 + 拒绝闭环 reload 仍「已拒绝」、零执行） |
| `scripts/verify.ps1` | 全绿 |

## 未运行的检查及原因

- **真实 AWS/Bedrock/DynamoDB/AgentCore**：无账号授权，未执行；不以本地替身或 SQLite PASS 冒充云端完成。
- **Docker 镜像 / Linux / 部署**：本机 PATH 无 Docker/AWS CLI，顺延 T7。
- **Playwright 默认 Chromium 版本**：未下载（网络超时），改用本机已缓存 Chromium 1194 经 `PAWTWIN_BROWSER_EXECUTABLE`。
- **GitHub CI 远程运行**：未推送。

## 独立审查发现与处理

见 `docs/reviews/day1.md`（非作者只读审查）。

## 云资源或费用变化

**无**。未创建资源、未调收费模型、未产生费用、未远程推送。

## 环境修复（重要）

项目从旧位置复制而来，随附 `.venv\Scripts\pytest.exe` 启动器仍指向旧源码树，导致 `uv run pytest` 导入**旧** `pawtwin`（`uv run python` 用新源码，二者不一致，契约测试假红）。已 `uv venv --clear --python 3.12` + `uv sync --frozen` 在工作区重建；`pawtwin` 经 editable `.pth` 指向工作区 `backend/`。未改系统安装、未改锁文件依赖项。

## 下一步依赖 / 需总负责人决定

1. **推送/发布**：分逻辑提交已完成（见上），未推送远程；推送或公开发布需另行明确授权。
2. **Day-2**：接入真实 Bedrock（换 `workflow` 的 inline proposer 为 `agent.analyze_event`）、`demo/facts`+`demo/device-mode` 现场注入、45s 超时终止、证据可追溯。
3. **账号就绪**：按 `infra/cloud-access-checklist.md` 做最小云端验证（Bedrock 往返、DynamoDB 条件写、memory ACTIVE），本地/云端结果分列。

## 二次检查补强（2026-09-24）

在已提交 HEAD 上复核（详 `docs/STATUS.md` “二次检查”节）：重跑全绿、契约/无秘密/审批五道闸逐行确认。修正项：

- 新增 2 条审批安全测试（BLOCKED 不可强批、DECLINED 不可重批为执行），后端测试 69→**71**。
- README 修正陈旧描述（登录/数据库已本地实现、页面业务源为 `/api/state`、e2e 同源 `:8000`）；`.env.example` 补 `PAWTWIN_DB_PATH`/`PAWTWIN_DEMO_PASSPHRASE` 占位。
- 保留已知边界（`/api/bootstrap` 冻结语义、惰性过期、摄入未接租约、内存会话、OpenAPI 错误响应）均顺延 Day-2/3，未夸大完成。
