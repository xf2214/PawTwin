# 当前开发状态

更新日期：2026-09-26（Day-3）。

Day-3 主线已完成并通过本地全部检查：**门 0 契约/配置冻结（C1，含记忆 seam）→ AI-02 `memory.py` 与 `search_owner_memory` 接线 → BE-04 反馈持久化 + worker 真并发 + 跨进程/重启 → C3 `main.py` 装配 → FE-03 记忆区 → OPS-03 `memory` extra 与脚本 → 集成与文档（C4）**。计划中的 **G0–G10 必过门全部达成**；真实 AgentCore 提炼/检索（条件项）因无账号**未执行，不以本地替身或 stub 冒充「已检索记忆」**。当日计划与 14 条技术裁定见 [Day-3 开发计划](plans/PawTwin_Day3_开发计划.md)。

执行方式：与 Day-1/Day-2 相同——单一开发环境，总负责人 Agent 串行完成各角色工作（逻辑上遵守 `AGENTS.md` 文件所有权与不重叠写入），用户已确认此方式；独立审查以**非作者**只读代码审查补充，见 [reviews/day3.md](reviews/day3.md)。

## Day-3 验收结果（三档）

| 档位 | 内容 | 结果 |
|---|---|---|
| **必过 G0** | 契约/配置冻结：**14 条路径**（+`/api/feedback`、+`/api/feedback/{feedback_id}`、+`/api/demo/new-session`）、记忆 seam 书面冻结、`domain.schema.json` 仍**恰为** 6 输入模型 + `RunState` | ✅ 通过；`--check` current |
| **必过 G1** | 反馈持久化（`feedback` 表、迁移 `SCHEMA_VERSION` 2→3）+ `POST/GET /api/feedback`（原文入库、`Idempotency-Key` 幂等去重、登录+CSRF） | ✅ 通过 |
| **必过 G2** | `memory_status` 诚实：本地恒 `saved`+`not_implemented`，**绝不** `available`/`processing` 伪造；`today_only` 不成为永久偏好（A07） | ✅ 通过 |
| **必过 G3** | `search_owner_memory` 接线 `MemoryService`：本地返回 `[]` 且**不记** memory 证据；stub→`source="memory"` 证据链 + proposal 可引用 + `validate_proposal_evidence` 校验；伪造 id 仍被拒 | ✅ 通过 |
| **必过 G4** | `POST /api/demo/new-session`：轮换 `conversation_id`，保留记忆/事实/登录 | ✅ 通过 |
| **必过 G5** | worker 由顺序 drain 改**有界线程池真并发**；准入 会话 1/全站 2 获得生产触发路径（闭合 Day-2 nit#6） | ✅ 通过；`peak_concurrency` 断言 |
| **必过 G6** | **跨进程双批准**（文件库两连接 + WAL）：`device.execute` 恰一次、`count_receipts==1`、配额一次、败者 409 | ✅ 通过（DB 不变式；跨副本 DynamoDB 顺延 Day-4） |
| **必过 G7** | **真实进程重启复验**：文件库两实例逻辑重启 + subprocess 真进程；等待审批仍在、终态不重跑、过期租约可领、`ANALYZING`+活租约**不二次分析** | ✅ 通过 |
| **必过 G8** | 前端记忆区（反馈输入 + `memory_status` 徽章 + `memory_backend` 标签 + 新会话），诚实标注，`feedback` e2e | ✅ 通过；e2e **10 项** |
| **必过 G9** | 三场景本地打通（A 正常 / B 已喂过回归 / C 记忆管线结构） | ✅ 通过（C 的**真实记忆影响**=条件项） |
| **必过 G10** | 回归全绿 + 契约 current + 文档诚实分列 + 非作者独立审查 | ✅ 通过（非作者审查 **PASS-WITH-NITS**，3 nit 已修，见 reviews/day3.md） |
| **尽力** | `AgentCoreMemory` + `agentcore_client.py` 实装（boto3 延迟导入、fail-closed）；`memory` extra（`boto3==1.43.102`，**硬门通过**）；subprocess 真进程重启测试；`agentcore-smoke.ps1`（NOT EXECUTED/退出码 2）；`preflight.ps1` AgentCore 只读段 | ✅ 全部完成 |
| **条件** | 一次真实 AgentCore strategy `ACTIVE` + 提炼/检索往返；场景 C 真实记忆影响；A06/A07/A08 真实记忆部分 | ⛔ **未执行**（无账号）；`test_agentcore_live.py` **5 项具名 skip**，`agentcore-smoke.ps1` 退出码 2 |

## Day-3 本地检查结果（2026-09-26，总负责人在项目目录内运行）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **184 passed, 11 skipped**（审查后 +2 回归；多次运行一致）；11 skip = 5 `agentcore_live` + 4 `bedrock_live` + 1 `bedrock_offline`（base 环境未装 strands）+ 1 `restart` 尽力项占位，均**具名** |
| 静态检查 | `uv run --frozen ruff check .` | All checks passed |
| 契约一致性 | `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current（**14 条路径**） |
| 依赖锁 | `uv lock --check` / `uv sync --frozen --extra memory` | 均 exit 0（`boto3==1.43.102`，本已是 strands 传递依赖，**无新增下载**） |
| 前端类型/构建 | `npm run typecheck` / `npm run build` | 通过（Node 24.19.0，vite 8.3.0） |
| 浏览器 e2e | `npx playwright test`（`workers:1`、background、local_fake、chromium-1194） | **10 passed**（8.9s）：approve×4 / decline / **feedback×3** / shell×2 |
| 集成 baseline | `./scripts/verify.ps1` | 全绿，EXIT=0 |
| 只读预检 | `./scripts/preflight.ps1` | 通过；AgentCore 段 `AGENTCORE_MEMORY_ID set: False`、`'memory' extra (boto3) installed: False` → `NOT EXECUTED` |
| 真实记忆 smoke | `./scripts/agentcore-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2**（未虚报已检索） |

逐条「命令 / 结果 / 这不证明什么」见 [evidence/day3-local.md](evidence/day3-local.md)；被阻塞的云端项见 [evidence/day3-cloud-blocked.md](evidence/day3-cloud-blocked.md)；完整交接见 [evidence/day3-handoff.md](evidence/day3-handoff.md)。

## Day-3 独立审查后补修（2026-09-26）

交付后由非作者独立审查（CodeReview 子代理）复核，结论 **PASS-WITH-NITS**（8 项高信号逐条核实全 ✅，14 条裁定与诚实红线 L18/L19/L22/L53 未破），发现 3 个 nit，均已修并复跑（**184 passed**）：

1. **worker 关闭期 `pool.submit` 失败泄漏准入槽（nit，已修）**：`stop()` 与扫描线程竞态时 `submit` 抛 `RuntimeError`，已获取的准入槽无路径释放。修法：`try/except RuntimeError` → 释放槽并 `break`。仅关闭期、进程内计数，实际影响可忽略，但补上了「获取必释放」的确定性。
2. **`post_feedback` 未归约 `MemoryUnavailable`（nit，已修）**：真实 AgentCore 提交失败会冒泡 500（仅运维显式选 `agentcore` 且无凭据时可达，出厂/已测配置不可达；原文已先落库无丢失）。修法：包 `try/except MemoryUnavailable` → `set_feedback_status("failed")` 并返回 200，复用已冻结的 `MemoryStatus` 词汇诚实报告「提炼失败」，绝不回退成「已生成记忆」。新增回归测试（负向验证：回退后转红）。
3. **缺 v2→v3 迁移回归测试（nit，已补）**：新增 `test_a_pre_day3_database_file_gains_the_feedback_table_idempotently`（预置 v2 文件库重开 → `feedback` 表自动建、`user_version==3`、反馈持久化可用）。

详见 [reviews/day3.md](reviews/day3.md)。上表「本地检查结果」为修复后的实测数字（184 passed、e2e 10 passed、verify.ps1 EXIT=0）。

## Day-3 关键实现与裁定落地

1. **记忆 seam（AI-02）**：`memory.py` 定义 `MemoryService` 协议（门 0 冻结）+ `LocalFakeMemory`（`not_implemented`：`submit_feedback`→`saved`、`search`→`[]`）+ `AgentCoreMemory`（延迟导入 `agentcore_client`，缺依赖/凭据→具名 `MemoryUnavailable`）+ `StubMemoryService`（构造注入，离线证明接线）；`build_memory(settings)` fail-closed 工厂。`AgentContext` 注入 `MemoryService`，`search_owner_memory` 委托它——本地返回 `[]` 且**不记** memory 证据（不伪造），返回记录时才生成 `evidence_id=f"memory:{record_id}"`、`source="memory"` 的可引用证据。
2. **反馈持久化（BE-04）**：`feedback` 表（`SCHEMA_VERSION` 2→3，`CREATE TABLE IF NOT EXISTS` + `PRAGMA user_version` 闸）；`FeedbackRecord` 内部记录（原文/scope/status/ids，`owner_id`/`idempotency_key` 不入响应）；`save_feedback` 以 `UNIQUE(owner_id, idempotency_key)` + 确定性 id 幂等去重；文件库启用 **WAL + busy_timeout** 支持两连接并发。
3. **worker 真并发（裁定 7，闭合 nit#6）**：有界线程池（池=`max_concurrent_global`），先 `AdmissionControl.try_acquire` 再 claim、per-task 唯一 `worker_id`、处理完 release；`peak_concurrency` 高水位证明会话 1/全站 2 上限有真实生产触发路径（两 owner 并行、第三 owner 等待；单 owner 两 run 串行）。CAS/白名单/租约原语在真并行下不变。
4. **跨进程双批准（裁定 8）**：两个 `SqliteRepository` 指同一文件库并发批准 → CAS 使 `device.execute` 恰一次、`count_receipts==1`、配额一次、败者 409；断言 **DB 不变式**（执行器为进程内对象，不共享计数器）。
5. **真实进程重启（裁定 9）**：`test_restart.py` 文件库两实例逻辑复验（含 `ANALYZING`+活租约不二次分析、过期后可领）；`test_restart_subprocess.py`（marker `restart`）真 spawn 子进程写库退出后由新进程恢复并恰执行一次。
6. **诚实边界**：`memory_status=saved` 仅表示原文入库，`FeedbackView.memory_backend` 与 `StateView.memory` 双标签使其绝不被读成「已提炼」；前端记忆区 `not_implemented` 时显示「未实现（无 AWS 账号）」「已保存原文（未提炼）」，e2e 断言记忆区**不含**「已检索到记忆」。

## 本地通过 vs 云端未验证（截至 Day-3，分列）

- **本地通过**：以上全部，另含反馈原文入库与幂等、`memory_status` 诚实语义、记忆 seam 与 stub 证据链、worker 真并发与准入上限、跨进程（两 SQLite 连接）双批准、文件库逻辑重启 + subprocess 真进程重启、前端记忆区与浏览器 e2e（10 项）、Day-2 全部本地项。
- **云端未验证**：真实 AgentCore 提炼/检索与时效（`memory_status` 真实 `processing`/`available`、真实 record id/namespace）；场景 C 真实记忆影响建议；A06/A07/A08 真实记忆部分；真实 Bedrock 推理（同 Day-2，`request_id` 恒 null）；DynamoDB 真表条件写与**跨副本多 replica** 并发（**不以 SQLite/两连接 PASS 替代**，Day-4/T7）；HTTPS/访问控制/**镜像构建**/Linux/部署（Day-4/T7，本机无 Docker）；GitHub Actions 远程运行（未推送）。
- **已实现但未验证**：`agentcore_client.py`（依 boto3 `bedrock-agentcore` 数据面签名编写，**未经真实账号验证**，异步提炼轮询生命周期未跑）；`Dockerfile` 改动（已加 `--extra memory`，**未构建**）。

## 尚未实现（截至 Day-3）

真实 Bedrock 调用、真实 AgentCore 提炼/检索、DynamoDB 真表、云部署与访问控制、真实传感器/设备、Alexa+；会话仍仅存进程内存（裁定 6：重启后重登录，A13 的 run 状态恢复已由文件库保证）；`conversation_id` 为 owner 级进程内、重启复位；worker 并发上限仍**仅进程内**（跨副本需数据库级计数，Day-4/T7）；登录限速未实现（HTTPS 属 Day-4）；`deploy.ps1`/`cleanup.ps1`、T6 的 24 案例集 `scenarios.json` + `evaluate.py` 未编写（Day-4）。

## 提交状态

**Day-2 与 Day-3 改动均尚未提交**（等待用户授权）。Day-3 建议分组：①门 0 契约与配置冻结（= Day-3 冻结提交）②后端反馈持久化/worker 并发/跨进程重启 ③AI 记忆适配器与 AgentCore 客户端 ④前端记忆区与 e2e ⑤OPS 依赖/脚本/镜像 ⑥文档与证据。提交后需把 **Day-3 契约冻结提交 ID** 回填到本文件与 `docs/TASKBOARD.md`。

无秘密入库、无云资源创建、**无费用**、无远程推送、**无镜像构建**。

---

# Day-2 记录（2026-09-25，历史，不改写）

Day-2 主线已完成并通过本地全部检查：**门 0 契约/配置冻结（C1）→ BE-03 并发原语与异步 worker → AI-03 分析器接线与证据/遥测 → FE-02 证据面板与演示控制 → OPS-02 依赖/CI/镜像/脚本 → 集成与文档（C4）**。计划中的 **G0–G11 必过门全部达成**；真实 Bedrock（条件项）因无账号**未执行，不以本地替身或离线 stub 冒充**。当日计划与 25 条技术裁定见 [Day-2 开发计划](plans/PawTwin_Day2_开发计划.md)。

执行方式：与 Day-1 相同——单一开发环境，总负责人 Agent 串行完成各角色工作（逻辑上遵守 `AGENTS.md` 文件所有权与不重叠写入），用户已确认此方式；独立审查以**非作者**只读代码审查补充，见 [reviews/day2.md](reviews/day2.md)（PASS-WITH-NITS，1 重要 + 6 nit，已处理）。

## Day-2 验收结果（三档）

| 档位 | 内容 | 结果 |
|---|---|---|
| **必过 G0** | 契约与配置冻结：11 条路径（+`demo/facts`、+`demo/device-mode`）、401/403/404/409/422 显式声明、`domain.schema.json` 仍**恰为** 6 输入模型 + `RunState`（断言由 `<=` 收紧为 `==`）、seam 签名书面冻结 | ✅ 通过；`--check` current |
| **必过 G1** | 分析器接线：`inline`/`local_fake`/`bedrock` 三后端，证据校验无条件强制（pinned 快照 + 追加式台账） | ✅ 通过；18 项 Day-1 审批/拒绝测试仍绿 |
| **必过 G2** | 45s 超时 / ≤4 次调用（**持久化**预算）/ ≤800 tokens 机制级 fail-closed，超限落 `FAILED` + 有界原因码，**不回退替身** | ✅ 通过（由可编程替身验证；真模型计量属条件项） |
| **必过 G3** | 异步 worker：可领取**白名单**（仅 `queued`/`analyzing`）、`renew_lease`/`release_run`、`attempt_count` 原子自增且 ≤2 次、准入上限、只在 lifespan 启停 | ✅ 通过；`create_app` 无副作用已测 |
| **必过 G4** | A03 重评估**零模型调用**（保留原 action、version+1、digest 不变、`retrieved_at` 不伪造） | ✅ 通过；telemetry/evidence 逐项相等已断言 |
| **必过 G5** | A04 并发双批准：CAS 使 `device.execute` **恰一次**、`count_receipts==1`、配额只加一次 | ✅ 通过（同进程；跨副本顺延） |
| **必过 G6** | `demo/facts` + `demo/device-mode`（登录+CSRF、硬限额不可注入）；A09 事实可置空并显示「未知」 | ✅ 通过；浏览器与 API 双证据 |
| **必过 G7** | 证据与遥测持久化（reload 可见）、不含 note 原文与隐藏推理、`RunView` 不泄露内部记账字段 | ✅ 通过 |
| **必过 G8** | schema 幂等迁移（`PRAGMA user_version` + 列存在性）+ **文件库**重启复验 | ✅ 通过；`.gitignore` 补 `*.db` |
| **必过 G9** | OpenAPI 错误响应补全 | ✅ 通过 |
| **必过 G10** | 浏览器 **approve 闭环** e2e（Day-1 只有 decline） | ✅ 通过；e2e **7 项**全绿 |
| **必过 G11** | 回归全绿 + 文档诚实分列 | ✅ 通过 |
| **尽力** | `BedrockAgent` + `bedrock_client.py` 真实实装（strands 1.57.0，延迟导入）；离线 stub 测试；A14 对照；A11 本地注入；`readyz`/`bootstrap` 分组件诚实上调 | ✅ 全部完成；依赖硬门（`uv lock --check` + `uv sync --frozen --extra bedrock`）**已通过** |
| **条件** | 一次真实 Bedrock 工具往返；真实模型参与正常与重复喂食场景 | ⛔ **未执行**（无账号）；`scripts/bedrock-smoke.ps1` 返回 `NOT EXECUTED`/退出码 2，`tests/test_bedrock_live.py` **4 项具名 skip** |

## Day-2 本地检查结果（2026-09-25，总负责人在项目目录内运行）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **139 passed, 4 skipped**（基线 71 → 新增 68；4 skipped = `bedrock_live` 具名 blocked） |
| 静态检查 | `uv run --frozen ruff check .` | All checks passed |
| 契约一致性 | `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current（11 条路径） |
| 依赖锁 | `uv lock --check` / `uv sync --frozen --extra bedrock` | 均成功（Resolved 65 packages；`strands-agents==1.57.0`） |
| 前端类型/构建 | `npm run typecheck` / `npm run build` | 通过（Node 24.19.0，vite 8.3.0） |
| 浏览器 e2e | `npx playwright test`（`workers: 1`、`expect.timeout: 20s`、webServer env = background + local_fake） | **7 passed**（8.7s）：approve 闭环 / 设备失败不记账 / needs-info / stale approval / decline 闭环 / 2 项门禁与边界 |
| 集成 baseline | `./scripts/verify.ps1` | 全绿 |
| 只读预检 | `./scripts/preflight.ps1` | 通过；`credential source present: False` → `NOT EXECUTED` |
| 真实模型 smoke | `./scripts/bedrock-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2**（未虚报成功） |
| 三方审查后复跑（2026-09-26） | 同上四项 + `scripts/test-e2e.ps1` | pytest **144 passed, 4 skipped**（新增 5 项回归，连续 20 次全量重跑零失败）、ruff 无告警、契约 current、e2e **7 passed**（8.9s，`PAWTWIN_BROWSER_EXECUTABLE` 指向系统 Chrome；Playwright 1.63 默认浏览器未下载，与 Day-1 同一处置） |

逐条「命令 / 结果 / 这不证明什么」见 [evidence/day2-local.md](evidence/day2-local.md)；被阻塞的云端项见 [evidence/day2-cloud-blocked.md](evidence/day2-cloud-blocked.md)；完整交接见 [evidence/day2-handoff.md](evidence/day2-handoff.md)。

## Day-2 修复的关键缺陷（计划阶段由三视角智能体发现，实施阶段已修）

1. **`claim_run` 用「非终态取反」→ `EXECUTING` 可被重领**：重分析会抹掉已有回执、递增 `proposal_version`、派生**新 `command_id`** → `INSERT OR IGNORE` 因主键不同而**第二次记账**（二次出粮）。已改为可领取白名单 + 穷举 11 个状态的测试。
2. **`save_run` 无条件写回租约**而分析路径又显式置 `None` → worker 自己清空租约，使已等审批的 run 可被再领取。已改为 `save_run` 不写租约/`attempt_count`，由 `renew_lease`/`release_run` 专管；`claim_run` 也无法续约（谓词对持有者同样为假），故新增 `renew_lease`。
3. **证据校验若用重查库的集合会产生假 `UNKNOWN_EVIDENCE`**（分析期间 `facts_version` 被 bump），且策略读旧快照、建议读新快照属 fail-open。已改为 pinned 快照 + 只增台账。
4. **A03 重分析跑在 HTTP 请求线程内**：接真模型后每次 stale approval 都是一次未预算、不受 45s/≤4 次保护的付费调用。已改为零调用的策略重评估。
5. **`_facts_view` 的 `or 0` + `FactsView` 非可空**：事实未知时页面显示「上次喂食距今 0 分钟」而策略判 `MISSING_FACTS`，对评委失真，且 A09 经 API 不可达（`NEEDS_INFO` 原本零行为测试）。已改为可空 + 前端显示「未知」。
6. **独立审查发现（已修）**：本地替身用 `or 0` 把 NULL 伪造成 0 并提议出粮 15 克，与「信息不足」同屏矛盾；修复后**连带暴露**出 `observe` 动作使 `evaluate_policy` 返回 `NON_FEEDING`、A09 退化为 `AWAITING_APPROVAL` 的语义缺口，已按 `proposal.missing_fields` 判 `NEEDS_INFO` 且 `policy_reason=MISSING_FACTS`。

## Day-2 三方审查后补修（2026-09-26）

交付后由独立审查代理复核未提交改动，总负责人回源码仲裁并实测确认两处缺陷，均已修：

7. **审批路径的非 CAS 写入可覆盖已完成的 run（阻断级，已修）**：`handle_approval` 的过期分支与 A03 重评 `_reevaluate_under_new_facts` 都用「读记录 → 改内存 → `save_run`」盲写，而 `save_run` 的 UPDATE 同时写 `state`/`expires_at`/`receipt_json`。交错后果实测两种：① 过期分支把并发已执行成功的 run 写成 `EXPIRED` 且**回执被抹成 NULL**（设备已出粮、配额已扣，run 上却查不到回执）；② 重评分支把 `SUCCEEDED` 覆盖成 `BLOCKED`（重评读到已被对手扣减的配额）。两者都不造成二次出粮（`command_id` 幂等 + 执行 CAS 守住），但属记账/审计失真，命中「禁止失真」红线。修法：新增唯一写入原语 `_settle(record, new)`——先 `transition_run(AWAITING_APPROVAL → new)` CAS 成功才 `save_run`，失败即放弃写入；过期、拒绝、A03 重评、执行前策略阻止四个分支全部改走它。
8. **`inline` 测试后端不报 `missing_fields`（已修）**：Day-2 第 6 项只补在 `local_fakes`，`workflow._inline_proposal` 仍从不声明缺口，于是同一事实在两个后端下状态不同（A09 退化为 `AWAITING_APPROVAL`）。已对齐 `_feeding_proposal`：任一必填事实为 NULL 即提议 `observe` 并列出 `missing_fields`，文案改为「缺少必要事实（…）」而非把「未知」拼进数值句。

回归测试新增 5 项：`tests/test_worker.py` 的过期迟到写入不得抹掉已执行回执、A03 重评不得覆盖已执行 run、`inline` 后端两个必填事实各自报 `NEEDS_INFO`，以及 `tests/test_demo_api.py` 的 A03 重评后必须重挂新审批窗口（不得清空 `expires_at`）。**前 4 项在回退修复后全部转红**（负向验证已做，非假绿）。另修正一处**先前就存在**的测试脆弱性：`test_concurrent_approvals_execute_the_device_exactly_once` 把败方拒绝码写死为 `NOT_AWAITING_APPROVAL`，但若赢家已在败方读记录前记账（bump `facts_version`），败方会抛 `STALE_APPROVAL_FACTS_CHANGED`（同为正确结果，实测 25 次重跑中复现 1 次）；已改为断言二元集合，`execute_calls == 1`/`count_receipts == 1` 等真不变式不变。上表「三方审查后复跑」为修复后的实测结果。

## 本地通过 vs 云端未验证（截至 Day-2，分列）

- **本地通过**：以上全部，另含 SQLite 持久化与幂等记账、拒绝/正常闭环、鉴权/CSRF、租约与白名单、CAS 双批准、demo 现场注入、证据与遥测持久化、schema 迁移与文件库重启、前端联调与浏览器 e2e（7 项）。
- **云端未验证**：真实 Bedrock 推理与证据（`request_id` 恒为 null）；真实模型下的 45s/≤4 次/≤800 tokens 计量；DynamoDB 真表条件写/事务与并发（**不以 SQLite PASS 替代**，Day-4/T7）；AgentCore 记忆检索与时效（Day-3）；跨进程/滚动双副本双标签批准（Day-3/T6）；真实 OS 进程重启复验（Day-3）；HTTPS/访问控制/**镜像构建**/Linux/部署（Day-4/T7，本机无 Docker）；GitHub Actions 远程运行（未推送）。
- **已实现但未验证**：`bedrock_client.py`（依 strands 1.57.0 本地内省签名编写，`_build_tools` 的工具注册离线不可验证）；`Dockerfile` 改动（已修改、**未构建**）。

## 尚未实现（截至 Day-2）

真实 Bedrock 调用、AgentCore 长期记忆与 `feedback`/`demo/new-session` 端点、DynamoDB 真表、云部署与访问控制、真实传感器/设备、Alexa+；会话仍仅存进程内存（Day-3 持久化/多副本）；worker 为**顺序** drain，故实际并发为 1，`AdmissionControl` 的会话 1/全站 2 上限当前无生产触发路径（仅单测覆盖，Day-3 引入并发执行时须复验）；登录限速未实现（HTTPS 属 Day-4）；`deploy.ps1`/`cleanup.ps1` 未编写。

## 提交状态

**Day-2 改动尚未提交**（等待用户授权）。建议分组：①门 0 契约与配置冻结（= Day-2 冻结提交）②后端并发原语与 worker ③AI 适配器与 Bedrock 客户端 ④前端与 e2e ⑤OPS 依赖/CI/镜像/脚本 ⑥文档与证据。提交后需把 **Day-2 契约冻结提交 ID** 回填到本文件与 `docs/TASKBOARD.md`。

无秘密入库、无云资源创建、**无费用**、无远程推送、**无镜像构建**。

---

# Day-1 记录（2026-09-23 / 09-24，历史，不改写）

Day-1 主线已完成并通过本地全部检查：**门 0 契约冻结 → BE-01/BE-02 最小集 → AI-01 适配接口 → FE-01 接真实本地 API → OPS-01 云接入计划**。三档验收中的**必过 Gate 全部达成**，正常闭环（尽力项）本地跑通，真实 Bedrock（条件项）因无账号**未执行、不以本地替身冒充**。

执行方式说明：本机为单一开发环境，Day-1 由总负责人 Agent 串行完成各角色工作（逻辑上遵守 `AGENTS.md` 文件所有权与不重叠写入），未按计划拉起并行工作树；独立审查以只读代码审查形式补充。

> 下方各小节为 Day-1 当时的记录。其中「尚未实现」与「本地通过 vs 云端未验证」已被上方的 Day-2 同名小节取代；「二次检查」中承诺的 **Day-2 上调 `capabilities`/`readyz`、补 OpenAPI 错误响应、接入 worker 租约**三项已于 Day-2 完成。

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
| 后端测试 | `uv run --frozen pytest` | **71 项通过**（基线 26 + Day-1 新增 45），1 项第三方弃用警告（不影响通过） |
| 静态检查 | `uv run --frozen ruff check .` | 无告警 |
| 契约一致性 | `python scripts/export_contracts.py --check` | Contracts are current |
| 前端类型/构建 | `npm run typecheck` / `npm run build` | 通过（Node 24.19.0；系统 Node 22.11.0 低于 Vite 要求，用项目脚本选择的运行时） |
| 浏览器 e2e | `scripts/test-e2e.ps1` 等价（baseURL 指后端同源 `:8000`） | **3 项通过**（登录门禁/边界标识 + 拒绝闭环 reload 仍「已拒绝」、零执行） |
| 集成 baseline | `scripts/verify.ps1` | 全绿 |

浏览器 e2e 通过 `PAWTWIN_BROWSER_EXECUTABLE` 使用本机已缓存的 Chromium 1194；Playwright 1.63 默认浏览器版本未下载。e2e 直指后端同源 `:8000`（`main.py` 服务 `frontend/dist`），非 vite preview、非 mock。

## 二次检查（Day-1，2026-09-24）

在已提交的 HEAD（`5d2b750`）上以新鲜视角复核，非仅重跑测试：

- **重跑全绿**：`verify.ps1` 通过（pytest/ruff/契约 `--check`/typecheck/build）；浏览器 e2e 3 通过；工作树干净。
- **契约核验**：`domain.schema.json` 恰为 6 输入模型 + `RunState`，无响应 DTO 泄漏；`EventIn.event_id` 为普通 UUID（`format: uuid`），`command_id` 才是 `uuid5(run_id:proposal_version)`；`ApprovalIn.action_digest` 正则 `^[0-9a-f]{64}$` 已在 schema 确认；`openapi.json` 含 9 条路径。
- **安全**：全仓 grep 无 AWS 密钥/私钥/api_key，无秘密入库。
- **逻辑复核**：审批路径五道闸（owner→404、惰性过期→EXPIRED、须 AWAITING_APPROVAL、digest+version 绑定、facts_version 变更重分析、执行前策略复评）逐行确认；`claim_run` 参数化无注入；`record_receipt_once` 事务内 `INSERT OR IGNORE`+rowcount 守卫，仅成功记账一次。
- **补强（本次新增）**：`test_approval.py` 增 2 条——policy-BLOCKED 运行不可被强行批准、已拒绝运行不可被重新批准为执行（A02/A08/A11）；后端测试 69→**71**。
- **文档修正**：README 原称“登录/数据库仍待开发”“页面读 /api/bootstrap”已过时，改为反映 Day-1 本地实现与 `/api/state` 业务源；e2e 段删除已废弃的 `PAWTWIN_E2E_PORT`/preview 说法改为同源 `:8000`；`.env.example` 补 `PAWTWIN_DB_PATH`/`PAWTWIN_DEMO_PASSPHRASE` 占位（标注非秘密）。
- **如实保留的已知边界（非缺陷，顺延）**：`/api/bootstrap` 的 `capabilities:"planned"` 按计划冻结未改（前端不以其为业务源，属保守低报，Day-2 连同 `test_app` 一并上调）；审批过期为惰性转换，前端未做倒计时（服务端已保证过期不可批准）；摄入热路径未接租约（Day-2 worker）；会话仅进程内存（Day-3）；OpenAPI 未声明 401/403/404/409（Day-2 补 responses）。

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
