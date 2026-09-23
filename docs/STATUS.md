# 当前开发状态

更新日期：2026-09-23（Day-1）。

Day-1 主线已完成并通过本地全部检查：**门 0 契约冻结 → BE-01/BE-02 最小集 → AI-01 适配接口 → FE-01 接真实本地 API → OPS-01 云接入计划**。三档验收中的**必过 Gate 全部达成**，正常闭环（尽力项）本地跑通，真实 Bedrock（条件项）因无账号**未执行、不以本地替身冒充**。

执行方式说明：本机为单一开发环境，Day-1 由总负责人 Agent 串行完成各角色工作（逻辑上遵守 `AGENTS.md` 文件所有权与不重叠写入），未按计划拉起并行工作树；独立审查以只读代码审查形式补充。

## Day-1 验收结果（三档）

| 档位 | 内容 | 结果 |
|---|---|---|
| **必过 ①** | 契约冻结且含业务路由（OpenAPI + domain schema 重生成、`--check` 通过） | ✅ 通过；`openapi.json` 含 login/logout/state/events/runs/{id}/approval |
| **必过 ②** | SQLite 去重/持久化/幂等/租约测试转绿 | ✅ 通过；`test_repository`/`test_recovery` 覆盖 |
| **必过 ③** | 拒绝闭环（登录→发事件→等待确认→拒绝→刷新仍「已拒绝」、零执行） | ✅ 通过；**浏览器 e2e** 与 **TestClient 集成**双证据 |
| **尽力** | 正常批准→模拟执行→成功回执→记账闭环 + 前端真实联调 | ✅ 本地跑通（集成测试 + 前端）；证据可追溯需真模型 → Day-2 |
| **条件** | 一次真实 Bedrock 工具往返 | ⛔ 未执行（无账号），不以本地替身标为云端完成 |

## 已实现与验证（本地）

- **契约（门 0，总负责人冻结）**：`models.py` 增公开响应 DTO（`EventAccepted/RunView/FactsView/StateView/LoginRequest/LoginResponse`）与共享 helper（`canonical_json`/`compute_action_digest`/`make_command_id`）；`RunView` 依总负责人裁定额外暴露 `proposal_version/action_digest`（审批防篡改绑定，客户端须回显；`owner_id/attempt_count/lease_*` 仍不入响应）。
- **后端**：`repository` 协议 + `repo_sqlite`（事务、唯一约束去重、幂等回执、仅成功记账、可重领租约、终态不重处理）；`policy`（硬配额，缺事实 fail-closed）；`workflow`（状态机 + Day-1 确定性 inline proposer，拒绝闭环不依赖 AI 替身）；`auth`（口令服务端哈希、HttpOnly/SameSite=Lax 会话、同步令牌 CSRF）；`device_sim`（三态真实回执，`simulated=True`）；`api`（业务路由，未授权 401、CSRF 失败 403）。
- **AI-01**：`agent`（四只读工具、owner 范围服务端注入、`validate_proposal_evidence` 拒绝未知证据、`build_analyzer` fail-closed）+ `local_fakes`（mode-gated、标注「本地替身」、只引用真实证据、不绕过 policy）。真实 Bedrock 为 Day-2。
- **前端 FE-01**：三主区（宠物与请求 / 建议与确认 / 任务与记忆占位）+ 可折叠演示控制区；模式/边界标识取自 `/api/state`；仅 `awaiting_approval` 显批准、提交中禁用；发事件后 2s 轮询至终态；记忆区/feedback 顺延 Day-3，`demo/facts`、`demo/device-mode` 顺延 Day-2。无新增前端依赖（手写类型以冻结契约为唯一来源）。
- **路由顺序**：业务 router 先于 `StaticFiles('/')` 注册，`/api/*` 未知路径仍返回 JSON 404（回归断言在 `test_app.py`）。

## 本地检查结果（2026-09-23，总负责人在项目目录内运行）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run --frozen pytest` | **69 项通过**（基线 26 + Day-1 新增 43），1 项第三方弃用警告（不影响通过） |
| 静态检查 | `uv run --frozen ruff check .` | 无告警 |
| 契约一致性 | `python scripts/export_contracts.py --check` | Contracts are current |
| 前端类型/构建 | `npm run typecheck` / `npm run build` | 通过（Node 24.19.0；系统 Node 22.11.0 低于 Vite 要求，用项目脚本选择的运行时） |
| 浏览器 e2e | `scripts/test-e2e.ps1` 等价（baseURL 指后端同源 `:8000`） | **3 项通过**（登录门禁/边界标识 + 拒绝闭环 reload 仍「已拒绝」、零执行） |
| 集成 baseline | `scripts/verify.ps1` | 全绿 |

浏览器 e2e 通过 `PAWTWIN_BROWSER_EXECUTABLE` 使用本机已缓存的 Chromium 1194；Playwright 1.63 默认浏览器版本未下载。e2e 直指后端同源 `:8000`（`main.py` 服务 `frontend/dist`），非 vite preview、非 mock。

## 本地通过 vs 云端未验证（分列）

- **本地通过**：以上全部（SQLite 持久化、拒绝/正常闭环、幂等记账、租约逻辑级、鉴权/CSRF、前端联调、浏览器 e2e）。
- **云端未验证**：DynamoDB 真表条件写/事务与并发（**不以 SQLite PASS 替代**，Day-4/T7）；真实 Bedrock 推理与证据可追溯（Day-2）；AgentCore 记忆检索与时效（Day-3）；跨进程/滚动双副本双标签批准（Day-3/T6）；真实进程重启复验（Day-3）；HTTPS/访问控制/镜像/Linux/部署（Day-4/T7）。

## 环境修复（重要）

项目从旧位置复制到当前工作区时，随附的 `.venv` 内 `Scripts\pytest.exe` 启动器仍指向旧源码树，导致 `uv run pytest` 实际导入**旧** `pawtwin`（`uv run python` 却用新源码，二者不一致，契约测试因此假红）。已用 `uv venv --clear --python 3.12` + `uv sync --frozen` 在**工作区**重建虚拟环境，`pawtwin` 经 editable `.pth` 指向工作区 `backend/`，pytest/python 导入一致。未改系统安装、未改锁文件的依赖项。

## 尚未实现

真实 Bedrock 推理、AgentCore 长期记忆、DynamoDB 真表、云部署与访问控制、真实传感器/设备、Alexa+；`demo/facts`、`demo/device-mode`、`feedback`/记忆状态端点；异步 worker（当前分析为同步）。

## 提交状态

Day-1 改动已按逻辑分组提交到分支 `chore/bootstrap`（用户授权；**未推送远程**）：

| 提交 | 内容 |
|---|---|
| `94216df` | **门 0 契约冻结** + 后端最小实现（= 冻结提交 ID） |
| `f2927cb` | 后端测试（BE-01/BE-02 + 拒绝闭环集成） |
| `e20336d` | AI-01 适配接口 + 本地替身 |
| `f45edb8` | FE-01 三主区 + 拒绝闭环 e2e |
| 本提交 | OPS-01 云接入清单 + Day-1 文档（STATUS/TASKBOARD/交接/审查） |

契约**冻结提交 ID = `94216df`**。无秘密入库、无云资源创建、无费用、无远程推送。

原五日计划仍是后续路线；Day-1 完成不代表 T1–T8 完成。实际赛事规则仍待官方链接核实。
