# Day-4 本地检查结果（2026-09-29）

> 每条给「命令 / 实测结果 / **这不证明什么**」。全部由总负责人在项目目录内、**干净工作区**（HEAD=`f3b96e4`，Day-4 提交序列末端）运行。
> 本机无 Docker、无 AWS CLI、无 CDK、无 AWS 凭据；用户已裁定**不安装 Docker**。故本轮**零云调用、零资源、零费用、零镜像构建、零远程推送**。

## 1 后端测试

| 命令 | 结果 |
|---|---|
| `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q -rs` | **192 passed, 10 skipped**（4.8s） |
| `uv run --frozen pytest -p no:cacheprovider`（默认 `addopts`） | **192 passed, 1 skipped, 9 deselected** |

10 条 skip 全部**具名**：5 × `tests/test_agentcore_live.py`（`BLOCKED: no AWS account is authorised…`）、4 × `tests/test_bedrock_live.py`（同上，Bedrock）、1 × `tests/test_restart_subprocess.py:128`（`kill-mid-analysis` 尽力项占位，理由为单机端口/启动时序 flaky）。

**skip 计数相对 Day-3 由 11 变 10 的原因（必须说明，否则会被误读为少了一项检查）**：Day-4 按裁定 10 实跑了 `uv sync --frozen --extra bedrock --extra memory`，本机 `.venv` 因此装上 `strands-agents`/`boto3`，`tests/test_bedrock_adapter_offline.py` 从「extra 未安装 → skip」变为**真实执行并通过**（+1 passed）。**CI 不装任何 extra**（`.github/workflows/ci.yml` 仅 `uv sync --frozen`），故 CI 上该文件仍会 skip，表现为 **191 passed, 11 skipped**量级；两个环境的数字不同是**依赖闭包不同**造成的，不是测试被删。

**这不证明**：任何真实 Bedrock/AgentCore 调用（9 条 live 用例全 skip）；分析中被 kill 的真实进程重启（具名 skip）；DynamoDB 真表语义。

## 2 Day-4 新增测试（明列，共 7 条 Python + 6 条 e2e）

Python（`tests/test_auth.py`，G2/BE-05）：

- `test_approval_is_gated_by_session_then_csrf` —— 审批路由未登录 **401**（且不泄露 run 是否存在）、缺 CSRF **403**、错 CSRF **403**、正确令牌才开门（未知 run → 404，证明过门但未执行）。
- `test_logout_requires_a_session` —— 匿名 `POST /api/logout` → **401**。
- `test_secure_cookie_follows_the_connection_not_the_mode` —— `https` → cookie 含 `Secure`；`http` → 不含；`X-Forwarded-Proto: https` → 含。

Python（`tests/test_feedback_api.py`，G7 反伪造守卫）：

- `test_no_feedback_path_can_report_available_or_processing_without_real_retrieval` —— POST/GET/`/api/state` 三个出口都只能是 `saved`。
- `test_the_factory_built_local_memory_never_produces_available_or_processing` —— 出厂 `build_memory` 的 `submit_feedback`/`get_status`/`search` 分别为 `saved`/`saved`/`[]`。
- `test_the_unavailable_agentcore_path_fails_closed_instead_of_faking_available` —— 无凭据的 `AgentCoreMemory` 提交与检索都抛具名 `MemoryUnavailable`，不返回 `available`。
- `test_no_other_backend_module_ever_writes_available_or_processing_literals` —— **静态守卫**：除 `models.py`（冻结词表）与 `memory.py`/`agentcore_client.py`（真实适配器）外，`backend/pawtwin/*.py` 任何文件出现 `"available"`/`"processing"` 字面量即失败。

e2e（`frontend/e2e/acceptance.spec.ts`，G6/FE-04，6 条）：

1. `an unauthenticated session sees the login gate and business APIs return 401 JSON`
2. `an unknown device receipt shows 状态未知 and never a success`
3. `reload while awaiting_approval keeps the pending request pending`
4. `desktop 1440px and narrow 390px show no overflow and states are not color-only`
5. `raising the daily dispensed amount shifts the proposed grams`
6. `a new session rotates the conversation while memory stays honestly unretrieved`

**负向验证（防假绿）**：把 `api.py` 的 `secure=_cookie_secure(request)` 回退为 `mode == "aws"`、并把审批路由依赖从 `CsrfSessionDep` 回退为 `SessionDep` 后，`test_secure_cookie_follows_the_connection_not_the_mode` 与 `test_approval_is_gated_by_session_then_csrf` **均转红**（实测 `2 failed`），随后恢复。

**这不证明**：真实 TLS 终结、真实代理链下的 `Secure` 行为（TestClient 只是把 scheme 设为 https）；跨副本授权；登录限速与会话 TTL（**仍未实现**）。

## 3 静态检查、契约与依赖

| 命令 | 结果 | 这不证明 |
|---|---|---|
| `uv run --frozen ruff check .` | All checks passed | — |
| `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current；`openapi.json` 实测 **14 条路径** | 契约未变（Day-4 未动 `models.py`/`contracts/`），不等于云端接口已验证 |
| `uv lock --check` | exit 0（Resolved 65 packages） | 锁新鲜，不等于镜像内安装成功 |
| `uv sync --frozen --extra bedrock --extra memory` | exit 0（Audited 63 packages，无新增下载） | **两个 extra 合并可复现**已实测；但 linux 容器内的同一闭包**未验证**（无 Docker） |
| `./scripts/verify.ps1` | EXIT=0（pytest + ruff + 契约 + typecheck + build） | 不含浏览器 e2e（脚本自身如此声明） |

## 4 浏览器 e2e

| 命令 | 结果 |
|---|---|
| `./scripts/test-e2e.ps1`（`PAWTWIN_BROWSER_EXECUTABLE` 指向本机 `ms-playwright/chromium-1194`；`workers:1`、`reuseExistingServer:false`、webServer = 后端同源 `:8000`、`PAWTWIN_MODE=local`+`WORKER_MODE=background`+`MODEL_BACKEND=local_fake`） | **16 passed**（15.7s）：acceptance×6 / approve×4 / decline×1 / feedback×3 / shell×2 |

**这不证明**：真实模型参与（后端是 `local_fake`）；重启恢复（webServer **未设** `PAWTWIN_DB_PATH` → 进程内内存库，进程一停数据即消失，故 e2e 内的 reload 只证明「重新读取服务端状态」）；跨副本双批准（单进程单浏览器）；浏览器矩阵（仅 chromium-1194，非 Playwright 默认下载版）；CI 上的 e2e（无 remote，CI 从未远程执行）。

## 5 fail-closed 脚本与只读预检（实测退出码）

| 命令 | 实测输出 | 退出码 |
|---|---|---|
| `./scripts/deploy.ps1 -PlanOnly` | `NOT EXECUTED: aws CLI is not on PATH. Deployment cannot plan or apply…` + `No AWS API was called…` + `Nothing is claimed as deployed or deployable.` | **2** |
| `./scripts/cleanup.ps1` | `NOT EXECUTED: aws CLI is not on PATH. Nothing can be listed or destroyed…` + `Nothing is claimed as cleaned up.` | **2** |
| `./scripts/agentcore-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.` | **2** |
| `./scripts/preflight.ps1` | `docker available on PATH: False`、`aws available on PATH: False`、`'bedrock' extra installed: True`、`'memory' extra (boto3) installed: True`、`credential source present: False`、Bedrock/AgentCore 两段均 `NOT EXECUTED` | **0**（环境自检类，按裁定 8 分级恒 0，但逐段报未执行） |

**这不证明**：可部署、可清理、可 plan。**脚本存在 ≠ 可部署**：本机无 AWS CLI/CDK、`infra/` 无任何 IaC 源、`-Apply`/`-Destroy` 明确未实现，三重前提均未满足；`-PlanOnly` 在当前环境**必然** `NOT EXECUTED`。

## 6 秘密与副作用核查

| 检查 | 结果 |
|---|---|
| `git grep -nIE 'AKIA[0-9A-Z]{12,}\|aws_secret_access_key\|secret_access_key\s*='` | **0 命中**（退出码 1） |
| `.env` | 磁盘不存在（`Test-Path` False）且未被跟踪 |
| `git check-ignore -v .venv frontend/dist frontend/test-results .pytest_cache .ruff_cache .superpowers` | 全部命中忽略规则 |
| 云资源 / 费用 / 远程推送 / 镜像构建 | **无 / 无 / 无 / 未构建**（本机无 Docker） |

## 7 本轮修复的真实缺陷（非新增功能）

1. **公网会话 cookie 缺 `Secure`（G2，阻断级）**：`api.py` 的 `secure` 判据曾是 `mode == "aws"`，而镜像把 `PAWTWIN_MODE=local` 烤死、`create_app` 又拒绝 `aws` 模式 → 该判据**永假**。部署到 HTTPS 后会以无 `Secure` 下发会话 cookie。已改为按请求 scheme（含 `X-Forwarded-Proto`，且该头只能**加**不能**减** `Secure`）。
2. **审批路由零鉴权测试（G2）**：`POST /api/runs/{run_id}/approval` 是唯一能触发执行/记账的写入口，却既无 401 也无 403 断言（其余写路由都有）。已补齐并做负向验证。
3. **390px 窄屏横向溢出 6px（G6）**：总方案 T3 要求的 1440px/390px 检查此前**从未做过**；首次引入视口断言即暴露证据行长文本不可断行导致溢出，已修 `styles.css` 并复测通过。
4. **前端标签由配置推导而非证据推导（G7，失真级）**：`analyzer=bedrock` 就会显示「AWS Bedrock（真实模型）」、`memory=agentcore` 就会显示「AgentCore（真实检索）」，而 `request_id` 可能恒 null。已改为证据驱动（有 `request_id`/真实记忆证据才允许「真实」字样），并把 `storage` 标签补上「`repo_dynamo` 未实现」。
5. **三处文档假陈述（G5）**：`pyproject.toml` 称「CI 与镜像默认都不装 bedrock extra」而 Dockerfile 明确两个 extra 都装；`infra/cloud-access-checklist.md` 给出并不存在的 `preflight.ps1 -Mode aws`；`docs/agents/infrastructure.md` 要求 `preflight` 无凭据非零退出而脚本实际恒 0。三处均已按实况改正，并新增退出码语义分级（环境自检 vs 计费/资源类）。
