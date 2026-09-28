# Day-3 本地证据（2026-09-26）

> 三列体例：**命令 / 实测结果 / 这不证明什么**。全部在本机项目目录内由总负责人运行。任何本地替身、离线 stub 或 SQLite/两连接 PASS **都不计入**云端验证；被阻塞的云端项见 [day3-cloud-blocked.md](day3-cloud-blocked.md)。

## 1 后端测试

- **命令**：`uv run --frozen pytest -p no:cacheprovider -o addopts="" -q`
- **结果**：**182 passed, 11 skipped**（连续 2 次运行一致，无 flaky）。11 skip 全部**具名**：5 `agentcore_live` + 4 `bedrock_live`（`BLOCKED: no AWS account…`）、1 `bedrock_offline`（`optional 'bedrock' extra not installed`，base 环境未装 strands）、1 `restart`（尽力项 uvicorn kill/relaunch 占位）。
- **这不证明什么**：不证明真实 AgentCore 提炼/检索、真实 Bedrock 推理、DynamoDB 语义或跨副本并发。`StubMemoryService` 只证明**我们自己的**接线（记忆→`source="memory"` 证据→proposal 可引用→非法 id 被拒），**不是**云端记忆证据。

## 2 Day-3 新增/扩展测试的覆盖面

- **命令**：`uv run --frozen pytest tests/test_memory.py tests/test_feedback_api.py tests/test_restart.py tests/test_restart_subprocess.py tests/test_concurrency_crossprocess.py -o addopts="" -q`
- **结果**：全绿。覆盖：`memory_status` 诚实（本地恒 `saved`、绝不 `available`；`today_only` 不成永久偏好）、`search_owner_memory` 本地返回 `[]` 且不记证据、stub 记忆生成可引用的 `source="memory"` 证据、伪造记忆 id 落 `UNKNOWN_EVIDENCE`、`AgentCoreMemory` 无 client/无 id 时 fail-closed、`build_memory` 与 config 交叉校验；反馈端点原文入库/幂等去重/401/403/404/422、new-session 轮换 `conversation_id` 且保留事实/登录；文件库两实例逻辑重启（等待审批/终态/过期租约/`ANALYZING`+活租约不二次分析）、subprocess 真进程恢复且恰执行一次；跨连接并发双批准 → `count_receipts==1`、恰一个 `SUCCEEDED`、配额一次、败者 409、活租约不可被第二连接窃取。
- **这不证明什么**：跨连接（两个 SQLite 连接）**不等价于** DynamoDB 多副本条件写；subprocess 真进程覆盖的是「干净退出后新进程恢复」，**不是**「运行中被 kill 于 ANALYZING」（后者由逻辑测试的活租约不重分析覆盖）。

## 3 worker 真并发（闭合 Day-2 nit#6）

- **命令**：`uv run --frozen pytest tests/test_worker.py -o addopts="" -q -k "parallel or per_session"`
- **结果**：`test_worker_analyzes_two_owners_in_parallel_up_to_the_global_ceiling` 断言 `peak_concurrency == 2`（三 owner、全站上限 2，第三个等待）；`test_worker_serializes_one_owner_at_the_per_session_ceiling` 断言 `peak_concurrency == 1`（单 owner 两 run、会话上限 1）。
- **这不证明什么**：并发上限仍**仅进程内**（`AdmissionControl` 为进程内计数）；跨副本上限需数据库级计数（Day-4/T7），未验证。

## 4 静态检查与契约

- **命令**：`uv run --frozen ruff check .` / `uv run --frozen python scripts/export_contracts.py --check`
- **结果**：`All checks passed`；`Contracts are current`（**14 条路径** = 11 + `/api/feedback` + `/api/feedback/{feedback_id}` + `/api/demo/new-session`）。`domain.schema.json` 的 `$defs` 仍**恰为** 6 输入模型 + `RunState`（断言由 `==` 强制，`FeedbackView`/`NewSessionView` 未泄漏进领域 schema）。
- **这不证明什么**：契约一致不代表云端行为正确；OpenAPI 的 `responses` 声明不等于真实错误路径已在云上跑通。

## 5 依赖锁（memory extra 硬门）

- **命令**：`uv lock` → `uv lock --check` → `uv sync --frozen --extra memory`
- **结果**：`uv lock` Resolved 65 packages；`uv lock --check` exit 0；`uv sync --frozen --extra memory` exit 0（`boto3==1.43.102`，本已是 strands-agents 传递依赖，**无新增下载**）。
- **这不证明什么**：装上 boto3 **不等于** AgentCore 可用——无账号/无凭据时 `agentcore_client` 仍 fail-closed（`MemoryUnavailable`），`aws_connected` 恒 False。

## 6 前端类型/构建/浏览器 e2e

- **命令**：`npm run typecheck` / `npm run build` / `npx playwright test`（`workers:1`、`PAWTWIN_WORKER_MODE=background`、`PAWTWIN_MODEL_BACKEND=local_fake`、chromium-1194）
- **结果**：typecheck 与 build 通过（Node 24.19.0，vite 8.3.0）；e2e **10 passed**（8.9s）——approve 闭环 / 设备失败不记账 / needs-info / stale approval / decline 闭环 / **feedback 诚实保存+reload 持久 / today_only 不成永久偏好 / new-session 轮换 conversation** / 2 项 shell 门禁与边界。
- **这不证明什么**：e2e 用 `local_fake` 与 `not_implemented` 记忆，**不含**任何真实模型或真实记忆；记忆区显示「已保存原文（未提炼）」，e2e 显式断言记忆区**不含**「已检索到记忆」。浏览器为缓存的 chromium-1194（Playwright 1.63 默认浏览器未下载），未下载任何二进制。

## 7 集成基线与只读预检

- **命令**：`./scripts/verify.ps1` / `./scripts/preflight.ps1` / `./scripts/agentcore-smoke.ps1`
- **结果**：`verify.ps1` 全绿 EXIT=0；`preflight.ps1` 通过，AgentCore 段输出 `PAWTWIN_MEMORY_BACKEND: unset -> not_implemented`、`AGENTCORE_MEMORY_ID set: False`、`'memory' extra (boto3) installed: False`、`NOT EXECUTED`；`agentcore-smoke.ps1` 输出 `NOT EXECUTED: no AWS credential source found.`、**退出码 2**。
- **这不证明什么**：预检全部只读，**不发起任何 AWS 调用**，不由环境变量推断已连通；smoke 无凭据时**绝不 `exit 0` 报成功**，一旦运行会产生计费调用。

## 8 零副作用核对

- **命令**：秘密 grep（AWS key/私钥/token）、`git status`
- **结果**：无秘密入库；无云资源创建；**无 AWS 费用**；无远程推送；**无镜像构建**（本机无 Docker）。
- **这不证明什么**：未以本地替身、离线 stub 或 SQLite/两连接 PASS 冒充任何云端完成。
