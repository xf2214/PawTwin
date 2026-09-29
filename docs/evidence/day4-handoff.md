# Day-4 交接与证据（2026-09-29）

> 依 `docs/HANDOFF_TEMPLATE.md` 的 12 项结构。本机为单一开发环境，Day-4 由**总负责人 Agent** 与另一执行体**按不重叠文件批次**并行推进（见第 3 项的并发说明），逻辑上遵守 `AGENTS.md` 的所有权与临界段；未拉起隔离工作树。
> 当日计划与 14 条技术裁定见 [Day-4 开发计划](../plans/PawTwin_Day4_开发计划.md)。

## 1 任务 ID 与范围

- **S0 基线入库**（Coordinator，前置串行）：把 Day-2 与 Day-3 的全部未提交改动按 `S0-a…S0-g` 七组入库，并回填**唯一真实存在**的合并契约冻结提交 ID。
- **BE-05 / G2 访问控制补口**：`api.py` 的 cookie `Secure` 判据由 `mode` 改为**按请求 scheme**；补齐 `POST /api/runs/{run_id}/approval` 的 401/403 与 `POST /api/logout` 的 401 断言；`auth.py` 文档写明 Secure 语义与三项未闭合缺口。
- **OPS-04 / G4+G5 部署前置材料**：新增 `scripts/deploy.ps1`、`scripts/cleanup.ps1`（fail-closed 门控）；修 `pyproject.toml` 的 extra 假陈述；`docs/agents/infrastructure.md` 增退出码语义分级；`infra/cloud-access-checklist.md` 的命令块改为「现状 + 目标」并补 Day-4 状态段；实跑 `uv sync --frozen --extra bedrock --extra memory`。
- **G3 健康检查端点硬裁定**：LB/target group 与容器 `HEALTHCHECK` 一律 `/healthz`；`/readyz` 保持恒 503，不为部署改码（裁定成文于 `docs/agents/infrastructure.md` 与 `infra/cloud-access-checklist.md`）。
- **FE-04 / G6+G7 浏览器验收与标签诚实**：`frontend/e2e/acceptance.spec.ts` 新增 6 条验收用例（含 1440px/390px 视口）；`App.tsx` 标签改为**证据驱动**；`styles.css` 修 390px 横向溢出；`tests/test_feedback_api.py` 增 4 条 `available` 反伪造守卫（含 1 条静态字面量守卫）。
- **G9 文档**（Coordinator，C4 临界段）：本文件 + `day4-local.md` + `day4-cloud-blocked.md` + `STATUS.md` 的 Day-4 段 + `TASKBOARD.md` 的第 4 日完成记录。

**明确不在本轮范围**（用户 2026-09-28 裁定）：T6 的 24 案例集 `scenarios.json` + `evaluate.py`、`repo_dynamo`、会话 DB 持久化、登录限速。

## 2 起始提交 / 交付提交

- **起始基线**：`dc8dc10`（Day-1 末），Day-2 与 Day-3 改动全部未提交，实测 **39 modified + 31 untracked**。
- **S0 序列**（7 组）：`56be355`(S0-a `.gitignore`+`pyproject`+`uv.lock`) → **`590aa5a`(S0-b 门 0 契约冻结 = 合并契约冻结提交 ID)** → `b25e5f1`(S0-c 后端) → `81a362d`(S0-d AI) → `2193349`(S0-e 前端+e2e) → `d0f3d20`(S0-f OPS/CI/镜像) → `b1f508a`(S0-g 文档与证据)。
- **Day-4 交付**：`c4ae5f8`(G2) → `a37c161`(G4/G5) → `94442b5`(G7 标签证据驱动 + 390px 溢出修复) → `f3b96e4`(G7 守卫 + FE-04 六条 e2e) → 本文档所在提交(G9)。
- **关于「两个冻结 ID」的书面披露（裁定 4）**：实测 `git show 94216df:contracts/openapi.json` 与 `git show dc8dc10:contracts/openapi.json` **均为 9 条路径**，工作区为 14 条 → **Day-2 的「11 路径契约冻结点」从未入库**，事后也无法分离（契约是 `export_contracts.py` 的生成物，禁止手改）。因此只回填 `590aa5a` 一个合并冻结 ID；Day-3 计划 §2 与 `STATUS.md` 中「回填 Day-2 与 Day-3 两个冻结 ID」的预期**不可达成**，已按实况改为披露。
- **中间提交未逐个复验**：Day-2/Day-3 改动在 `models.py`/`api.py`/`contracts/` 同批纠缠且终态互依赖，任一中间组单独 checkout 都会使 `export_contracts.py --check` 变红，故只在**最终 HEAD** 声明全绿（数字见第 8 项）。

## 3 工作树 / 分支

单一工作区 `c:\Users\11831\Desktop\hks\outputs\pawtwin-app`，分支 `chore/bootstrap`，无远程（`git remote -v` 为空，未推送）。

**并发说明（如实记录）**：Day-4 执行期间有**两个执行体**同时在本工作区推进。文件批次不重叠——另一执行体负责 `scripts/*.ps1`、`infra/`、`pyproject.toml`、`frontend/src/`、`frontend/e2e/`、`tests/test_feedback_api.py`（G4/G5/G6/G7）；总负责人负责 `backend/pawtwin/api.py`、`auth.py`、`tests/test_auth.py`（G2）与 C4 文档段（G9）。总负责人**未采信**对方的绿灯声明，对其提交后的 HEAD 独立重跑了全部检查（第 8 项），并在复核中发现并修复了两处问题：`tests/test_feedback_api.py` 的 `ruff I001`（导入未排序，会使 `verify.ps1` 中断）与一处冗余的 `MemoryUnavailable as _MU` 局部导入别名（模块级已导入）。工作区遗留对方审查产物 `_review_diff_day4.txt`（未入库、未被忽略），处置见第 12 项。

## 4 改动文件

- **S0（70 个文件，Day-2+Day-3 全量入库）**：后端 `models/contracts/config/repository/repo_sqlite/workflow/worker/main/api/auth/agent/local_fakes/memory/bedrock_client/agentcore_client`、`contracts/openapi.json`、`tests/*`（14 个）、`frontend/src/*` 与 `frontend/e2e/*`、`pyproject.toml`/`uv.lock`/`Dockerfile`/`.gitignore`/`.env.example`/`ci.yml`、`scripts/*`、`README.md`/`docs/**`/`infra/**`。
- **Day-4（13 个文件，+695/−28）**：`backend/pawtwin/api.py`、`backend/pawtwin/auth.py`、`tests/test_auth.py`、`tests/test_feedback_api.py`、`frontend/src/App.tsx`、`frontend/src/styles.css`、`frontend/e2e/acceptance.spec.ts`（新增）、`frontend/e2e/feedback.spec.ts`、`scripts/deploy.ps1`（新增）、`scripts/cleanup.ps1`（新增）、`pyproject.toml`、`docs/agents/infrastructure.md`、`infra/cloud-access-checklist.md`。
- **G9 文档（本次新增/修改）**：`docs/evidence/day4-handoff.md`、`day4-local.md`、`day4-cloud-blocked.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`。
- **未改动**：`backend/pawtwin/models.py`、`contracts/*`、`main.py`、`config.py`、`Dockerfile`、`ci.yml`（Day-4 刻意不动契约与镜像，见第 7 项）。

## 5 已实现行为

- **cookie `Secure` 跟随连接而非模式**：`https` 直连或 `X-Forwarded-Proto: https` 时下发 `Secure`，本地 HTTP 仍省略；该头只能**加**不能**减** `Secure`，故无需受信代理开关也不会削弱安全。修掉了「部署到 HTTPS 后公网会话 cookie 无 `Secure`」这一阻断级缺陷。
- **审批与登出路由的鉴权矩阵**：审批路由未登录 401（且不泄露 run 是否存在）、缺/错 CSRF 403、正确令牌才开门；匿名登出 401。
- **部署/清理入口的 fail-closed 形态**：门顺序固定为 CLI 存在性 → IaC 源存在性 → 必填参数 → 显式授权令牌；任一缺失即 `NOT EXECUTED: <原因>` + **退出码 2**，任何路径都**不调用 AWS、不 `exit 0`**；account id 只运行期注入。
- **前端标签证据驱动**：无 `request_id` 时分析器只显示「AWS Bedrock（已配置，未经真实调用验证）」，无真实记忆证据时只显示「AgentCore（已配置，未经真实检索证据验证）」；`storage` 标签明写「`repo_dynamo` 未实现」；`memory_status` 词表去掉「真实记忆」字样。
- **`available` 反伪造守卫**：三个 API 出口与出厂 `build_memory` 只能是 `saved`；无凭据的 `AgentCoreMemory` 必须抛具名 `MemoryUnavailable`；静态守卫禁止 `models.py`/`memory.py`/`agentcore_client.py` 之外的后端模块出现 `available`/`processing` 字面量。
- **浏览器验收矩阵**：未登录访问 → 401 JSON + 登录门；`unknown` 回执 → 「状态未知」且绝不显示成功、不记账；待批准刷新 → 状态保留且**诚实提示需重新登录**（CSRF 令牌按设计仅存内存）；1440px/390px 无横向溢出且状态不只靠颜色；改事实 → 建议克数随之变化（A14 浏览器半边）；新会话轮换 `conversation_id` 且记忆区不声称检索到记忆。
- **390px 溢出修复**：证据行长文本不可断行导致窄屏溢出 6px，已在 `styles.css` 修复并复测。

## 6 仍然模拟或未实现的内容

- 传感器事件与设备执行**始终为模拟**（`source=simulator`、`receipt.simulated=true`）；PawLink 项圈为概念。
- **未实现**：`repo_dynamo`（DynamoDB 真表）、跨副本数据库级并发计数、会话 DB 持久化与 TTL、登录限速、记忆提炼轮询与 `available` 接线（`MemoryService.get_status` 在生产端**无调用方**）、`deploy.ps1 -Apply`/`cleanup.ps1 -Destroy` 的真实实现、`infra/` 的 IaC 源、T6 的 24 案例集与 `evaluate.py`。
- **未验证**：容器镜像（本机无 Docker，用户裁定不安装，**从未构建**）、Linux 运行时、HTTPS/真实 TLS、公网访问控制、真实 Bedrock/AgentCore 调用、GitHub Actions 远程运行（无 remote）。
- **已实现但未验证**：`bedrock_client.py`（strands 1.57.0 调用形态）、`agentcore_client.py`（boto3 `bedrock-agentcore` 数据面签名与状态词表）、两个 fail-closed 脚本的**真实** plan/apply 路径。
- **诚实边界（Day-4 明写）**：`/readyz` 恒 503，仅 `/healthz` 可作部署健康检查；`PAWTWIN_MODE=aws` 会**拒绝启动**（`main.py:81-82`），这是 fail-closed 而非缺陷；e2e 的 webServer 用**内存库**，故浏览器层的 reload **不证明**重启恢复；跨进程双批准用「两个 SQLite 连接」为本地代理，**不等价于** DynamoDB 多副本；worker 并发上限**仅进程内**，滚动两副本会使全站实际并发 = 副本数 × 2，且会话进程内导致跨副本 401。

## 7 接口变化与消费者影响

- **契约零变化**：`openapi.json` 仍 **14 条路径**，`domain.schema.json` 仍恰为 6 输入模型 + `RunState`，`export_contracts.py --check` = current，`tests/test_contracts.py` 的 `==` 断言未放宽。`models.py`/`contracts/`/`config.py`/`main.py` 本轮**未改**。
- **行为变化（非契约）**：`Set-Cookie` 的 `Secure` 属性判据变化 —— 本地 HTTP 下不变（仍无 `Secure`），HTTPS/代理头下**新增** `Secure`。消费者：浏览器与未来 TLS 终结层；`tests/test_auth.py` 原有的「本地不含 secure」断言仍成立，另加配对断言。
- **前端文案变化**：`impl-labels`/`memory-backend`/`telemetry` 的标签文本改为证据驱动，`feedback.spec.ts` 的断言已同步（Day-4 提交内含）。任何依赖旧文案「AWS Bedrock（真实模型）」「AgentCore（真实检索）」「已可检索（真实记忆）」的外部脚本或断言都需更新。
- **新增脚本参数面**：`deploy.ps1 -PlanOnly|-Apply -CostAuthorization <token>`；`cleanup.ps1 -Destroy -ConfirmProjectId <id> -CostAuthorization <token>`。二者当前**必然** `NOT EXECUTED`（退出码 2）。
- **依赖闭包**：`uv sync --frozen --extra bedrock --extra memory` 本机可复现（exit 0）；CI 仍不装 extra，故 `test_bedrock_adapter_offline.py` 在 CI 上 skip、在本机执行 —— 两侧数字差异是闭包不同，非测试增删。

## 8 运行的检查（命令 / 结果）

| 命令 | 结果 |
|---|---|
| `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q -rs` | **192 passed, 10 skipped**（10 = 5 `agentcore_live` + 4 `bedrock_live` + 1 `restart` 尽力项占位，均具名） |
| `uv run --frozen pytest -p no:cacheprovider`（默认 `addopts`） | **192 passed, 1 skipped, 9 deselected** |
| `uv run --frozen ruff check .` | All checks passed（复核中曾发现 1 处 `I001`，已修） |
| `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current（实测 **14 条路径**） |
| `uv lock --check` | exit 0（Resolved 65 packages） |
| `uv sync --frozen --extra bedrock --extra memory` | exit 0（Audited 63 packages，无新增下载） |
| `./scripts/verify.ps1` | EXIT=0（pytest + ruff + 契约 + typecheck + build） |
| `./scripts/test-e2e.ps1` | **16 passed**（15.7s；acceptance×6 / approve×4 / decline×1 / feedback×3 / shell×2） |
| `./scripts/deploy.ps1 -PlanOnly` / `./scripts/cleanup.ps1` / `./scripts/agentcore-smoke.ps1` | 均 `NOT EXECUTED`，**退出码 2** |
| `./scripts/preflight.ps1` | 退出码 **0**；`docker/aws available on PATH: False`、`credential source present: False`、两个 extra 均 `installed: True`、Bedrock 与 AgentCore 段均 `NOT EXECUTED` |
| 秘密核查 | `git grep -nIE 'AKIA…\|aws_secret_access_key\|secret_access_key\s*='` → **0 命中**；`.env` 不存在且未跟踪 |

逐条「命令 / 结果 / **这不证明什么**」见 [day4-local.md](day4-local.md)。

## 9 未运行的检查及原因

- **全部云端项**：无账号、无凭据、本机无 Docker/AWS CLI/CDK、`infra/` 无 IaC 源、`mode=aws` 被 `main.py` 拒绝启动 —— 四重独立阻断。逐条（N1–N10）与解锁前提见 [day4-cloud-blocked.md](day4-cloud-blocked.md)；Day-3 的 M1–M12 **全部仍未解除**。
- **真实 HTTPS 下的 cookie `Secure`**：本地无证书，只能用 TestClient 把 scheme 设为 `https` 验证判据，**不等于** TLS 终结链路已验证。
- **容器内 healthz / 静态页 / worker / HEALTHCHECK**：无 Docker，仅静态审读 `Dockerfile`。
- **`deploy.ps1 -PlanOnly` 的真实 plan 输出**：无 CLI 与 IaC 源，脚本按设计 `NOT EXECUTED`。
- **分析中被 kill 的真实进程重启**：`tests/test_restart_subprocess.py:128` 的具名 skip（单机端口/启动时序 flaky），语义由 `test_restart.py` 的「`ANALYZING`+活租约不二次分析、过期后可领」逻辑测试覆盖。
- **GitHub Actions 远程运行**：无 remote、未推送（需用户授权）。
- **T6 的 24 案例集与 `evaluate.py`**：用户本轮未选，顺延；其与 Day-5「评委自由输入」验收同源，冲突已上报（见第 12 项）。

## 10 独立审查发现与处理

- **G8（非作者独立审查）已出具结论：PASS**（CodeReview 子代理，审查范围 `b1f508a..63f3de6`）：10 项高信号逐条核实全 ✅，**无 blocker / important / nit**，无需修复故无复测；诚实红线逐条**负面确认**未破（未以替身/SQLite/脚本存在冒充云端、skip 全具名、生成契约未手改、未声称已部署/A12 通过/两个冻结 ID）。详见 [docs/reviews/day4.md](../reviews/day4.md)。
- **总负责人对「零发现」的复核（不采信自评）**：Day-2/Day-3 均为 PASS-WITH-NITS，故将「零 nit」当作待验证断言，亲自回源码复核三条最易自我美化的判断：①`feedback.spec.ts` 的改动是把禁止子串由「已可检索」**收紧**为「可检索」（非放宽）；②390px 修复用的是 `flex-wrap`/`overflow-wrap: anywhere`/`min-width: 0` 且**限定在 `@media (max-width: 900px)` 内**，无 `overflow-x: hidden`/截断/缩小字体，断言仍为 `<= 0`；③静态守卫白名单恰等于实测含该字面量的 3 个文件（不过宽）。三项均成立 → PASS 可采信。
- **总负责人对已提交代码的独立复核**：不采信并行执行体的绿灯，对 HEAD 重跑第 8 项全部命令并逐项核对退出码；发现并修复 2 处（`ruff I001` 会使 `verify.ps1` 直接中断；冗余导入别名 `_MU` 遮蔽模块级导入）。
- **审查遗留项（非阻断）**：尽力项中的 IAM/CFN 草案、费用表拆行、`preflight -Mode` 真实参数、`/readyz` 连通判据设计文档**未做**（已顺延）；裁定 14 的三项公网前置硬门仍待用户定；工作区遗留的 `_review_diff_day4.txt` 不得入库。
- **复核中确认的高信号点**：`available` 静态守卫的白名单只含 `models.py`/`memory.py`/`agentcore_client.py`（未过度放宽）；`/readyz` 的 503 精确断言未被放宽；`export_contracts.py --check` 仍 current 且路径数为 14；`deploy.ps1`/`cleanup.ps1` 无任何 `exit 0` 路径；390px 修复落在 `styles.css`（+37 行）而非**放宽断言**（`overflow <= 0` 仍在）。

## 11 云资源或费用变化

**无**。未创建任何云资源、未调用任何收费模型或记忆服务、未产生任何费用、未推送远程、**未构建镜像**。`uv sync --extra bedrock --extra memory` 只从本地缓存审计已锁定依赖（`Audited 63 packages`，无新增下载）。

## 12 下一步依赖 / 需总负责人决定

1. **账号注册进度**：用户已着手注册。就绪后按 [Day-4 计划 §7.5](../plans/PawTwin_Day4_开发计划.md) 手顺执行（extras → 短期凭据 → `preflight` → 两个 smoke（**计费**，需预算授权）→ live 测试 → `repo_dynamo` → 才可移除 `main.py:82` 的 raise 并上调 `readyz` → `-PlanOnly` → 费用与删除清单确认 → `-Apply`）。
2. **镜像构建路径需用户选择**：本机不装 Docker（已裁定）→ 要么另找 Docker 环境，要么**授权创建远程仓库并推送**让 GitHub Actions 构建（这同时解锁 N8 的 CI 远程运行）。二者都未发生前，镜像只能记「已静态审读、未构建」。
3. **公网部署前置硬门（裁定 14，待用户裁定）**：登录限速/失败退避、会话 TTL（`Session.created_at` 目前无消费者）、强制以环境变量覆盖默认口令 `local-demo-passphrase`。这三项在公网 HTTPS 前**必须**有明确决定；本轮只出议题、未实现。
4. **T6 与 Day-5 的取舍（冲突上报）**：24 案例集 + `evaluate.py` 未在 Day-4 做，而 Day-5「测试与评委自由输入」的量化判据与它同源。请在 Day-5 开工前二选一：补做案例集，或接受降级表述「人工现场脚本、无固定案例集量化报告」。同时 Day-5 已含材料全套，被顺延的云端块压不进同一天；无 AWS 验证时产物须命名「**本地验证候选（非参赛版）**」（总方案 L153）。
5. **G8 已完成**：`docs/reviews/day4.md` 已由**非作者**审查者出具（PASS，覆盖到 `63f3de6`）；若后续再改动 `api.py`/`App.tsx`/脚本，需按该文件 §6 的复测清单重跑并追加审查记录。另一执行体遗留的 `_review_diff_day4.txt` 属临时工作产物，应删除或加入 `.gitignore`，**不得入库**。
6. **是否推送远程**：仍无 remote；推送需用户明确授权（AGENTS.md L71）。
7. **STATUS/TASKBOARD 的历史预期更正**：Day-3 文档中「回填两个契约冻结 ID」的表述已按裁定 4 改为披露（只回填 `590aa5a`）；Day-1 冻结 ID `94216df` 保留为历史冻结点，未改写。
