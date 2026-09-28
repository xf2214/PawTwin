# Day-2 交接与证据（2026-09-25）

> 依 `docs/HANDOFF_TEMPLATE.md` 的 12 项结构。本机为单一开发环境，Day-2 由**总负责人 Agent 串行**完成 Coordinator/Backend/AI/Frontend/OPS 各角色工作，逻辑上遵守 `AGENTS.md` 的文件所有权与不重叠写入；未拉起并行工作树（与 Day-1 同一执行方式，用户已确认）。独立审查以只读代码审查（非作者）补充，见 `docs/reviews/day2.md`。

## 1 任务 ID 与范围

- **门 0（C1）契约与配置冻结**（Coordinator 独占）：`models.py` 新增 `EvidenceItem`/`AnalysisTelemetry`/`AnalysisOutcome`/`ErrorResponse`/`DemoFactsIn`/`DemoDeviceModeIn`/`DemoAck`，`RunView` 增 `evidence`/`telemetry`/`policy_reason`/`failure_reason`，`FactsView` 两字段改可空，`StateView` 增 `analyzer`/`storage`/`memory`/`device_mode`；`config.py` 增 10 项 settings 与交叉校验；书面冻结 seam 签名；OpenAPI 补 401/403/404/409/422。
- **BE-03**：并发原语（claim 白名单、`renew_lease`、`release_run`、`transition_run` CAS、`attempt_count` 原子自增）、schema 幂等迁移、`worker.py`、`demo/facts` 与 `demo/device-mode`、A03 零调用重评估、fail-closed 失败映射。
- **AI-03**：`AnalyzerProposer` 适配器、`AgentContext` pinned 快照与证据台账、限额装饰器、`BedrockAgent` + `bedrock_client.py`（strands 延迟导入）、离线 stub 测试。
- **FE-02**：证据面板、调用遥测、`impl-labels`、演示控制区、可空事实显示、中间态与显式超期提示、approve 闭环 e2e。
- **OPS-02**：`bedrock` optional extra + `uv.lock`、CI `uv lock --check`、Dockerfile、`.env.example`、`.gitignore`、README、角色简报、`preflight.ps1`、`bedrock-smoke.ps1`、成本估算。

## 2 起始提交 / 交付提交

- 起始基线：`dc8dc10`（分支 `chore/bootstrap`，Day-1 完成，71 项后端测试 + 3 项 e2e 绿）。
- 交付提交：**待用户授权后按逻辑分组提交**（见第 12 项）。本文件记录的是交付内容与实测证据，不预填提交 ID。
- Day-1 契约冻结提交 ID `94216df` 保留为历史冻结点，未改写。Day-2 的契约冻结点将在提交后记入 `docs/STATUS.md`。

## 3 工作树 / 分支

单一工作区 `c:\Users\11831\Desktop\hks\outputs\pawtwin-app`，分支 `chore/bootstrap`。未新建隔离工作树（串行执行，无并发写冲突）；临界段 C1（契约/配置）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）按计划顺序串行通过。

## 4 改动文件

- **新增（12）**：`backend/pawtwin/worker.py`、`backend/pawtwin/bedrock_client.py`、`tests/test_worker.py`、`tests/test_demo_api.py`、`tests/test_bedrock_adapter_offline.py`、`tests/test_bedrock_live.py`、`frontend/e2e/approve.spec.ts`、`frontend/e2e/helpers.ts`、`scripts/bedrock-smoke.ps1`、`scripts/bedrock_smoke.py`、`docs/plans/PawTwin_Day2_开发计划.md`、`docs/reviews/day2.md`。
- **契约与配置（Coordinator）**：`backend/pawtwin/models.py`、`config.py`、`contracts.py`、`main.py`、`contracts/openapi.json`（重生成，11 条路径）、`pyproject.toml`、`uv.lock`、`.github/workflows/ci.yml`、`Dockerfile`、`.env.example`、`.gitignore`。
- **后端（Backend）**：`repository.py`、`repo_sqlite.py`、`workflow.py`、`api.py`。
- **AI**：`agent.py`、`local_fakes.py`。
- **前端**：`src/api.ts`、`src/App.tsx`、`src/styles.css`、`playwright.config.ts`、`e2e/decline.spec.ts`、`e2e/shell.spec.ts`。
- **测试同步**：`tests/conftest.py`、`test_contracts.py`、`test_app.py`、`test_agent.py`、`test_repository.py`。
- **文档/OPS**：`README.md`、`infra/cloud-access-checklist.md`、`scripts/preflight.ps1`、`docs/TASKBOARD.md`、`docs/agents/{ai,backend,frontend,infrastructure,reviewer}.md`、`docs/STATUS.md`、本目录三份 Day-2 证据文件。
- 合计：37 个修改文件 + 12 个新增文件（`git diff --shortstat` 为 37 files changed, +3719/−313，未含新增文件）。

## 5 已实现行为

- **分析器 seam 接线**：`Workflow` 不再硬编码 inline 建议；三后端 `inline`（确定性测试后端，不检索、不引用证据 id）/ `local_fake`（标注「本地替身」，引用真实台账）/ `bedrock`（真实模型，缺依赖或缺凭据即显式失败）。`build_analyzer` 与 `config` 双向 fail-closed：`mode=aws` 必须 `bedrock`，`bedrock` 必须有 model id + region，`aws_connected` 恒 False。
- **证据与遥测**：`AgentContext` pinned 快照 + 追加式台账；`validate_proposal_evidence` 只认台账；`EvidenceItem`/`AnalysisTelemetry` 持久化到 `runs.evidence_json`/`telemetry_json`，reload 后仍可见；`request_id` 无真实云调用时为 `null`，前端如实显示「无（未发生真实云调用）」。
- **限额与超时**：45s 分析超时（`AnalysisGuard` + app 级 executor，`shutdown(wait=False, cancel_futures=True)`）、每任务 ≤4 次模型调用（**持久化** `model_calls_used`，重启不可绕过）、≤800 输出 tokens（作为请求参数下发）。超限一律 `FAILED` + 有界原因码，**不回退 inline/替身**，未捕获异常不冒泡成 500。
- **并发与幂等**：`claim_run` 改可领取**白名单**（仅 `queued`/`analyzing`），`EXECUTING` 绝不重分析；`renew_lease`/`release_run`；`attempt_count` 在 claim 的同一条 UPDATE 内原子自增且 ≤2 次；`transition_run` CAS 使并发双批准下 `device.execute` **恰调用一次**；`save_run` 不再写租约与尝试次数。
- **A03**：`_reevaluate_under_new_facts` 零模型调用（保留原 action、`proposal_version+1`、digest 不变、`evidence`/`telemetry` 与 `retrieved_at` 原样保留）。
- **A09**：`update_facts` 支持 `UNSET`/写 NULL；`FactsView` 两字段可空且删除 `or 0`；前端显示「未知」；替身在事实未知时提议 `observe` 并填 `missing_fields`，workflow 据此判 `NEEDS_INFO` 且 `policy_reason=MISSING_FACTS`（不再出现「信息不足」与「出粮 15 克 / 0 分钟」同屏矛盾）。
- **demo 端点**：`POST /api/demo/facts`（仅两个可注入字段 + `clear` + `reset`；`extra="forbid"` 使硬限额**不可**经演示端点修改；空 body 不 bump 版本）、`POST /api/demo/device-mode`（进程内、仅影响新命令、重启复位）；均需登录 + CSRF。
- **worker**：`worker.py` 顺序 drain、`threading.Event` 唤醒（队列等待 <1s）、租约续约线程、`AdmissionControl`（会话 1/全站 2，**仅进程内**）、只在 lifespan 启停（`create_app` 无副作用，契约导出不起线程）；`POST /api/events` 在 `background` 下返回 `202 + queued`，`inline`（默认）下返回受理后状态。
- **持久化**：`PRAGMA user_version` + 列存在性双保险的幂等迁移；`.gitignore` 补 `*.db`/`*.db-journal`。
- **契约完整性**：11 条路径，业务路由显式声明 401/403/404/409/422；`domain.schema.json` 仍**恰为** 6 输入模型 + `RunState`（断言已由 `<=` 收紧为 `==`）。
- **就绪度诚实上调**：`readyz` 仍 503/degraded 但 `reason=cloud_adapters_not_verified` 并分列 business/model/storage/memory/cloud；`bootstrap` 的 `capabilities` 改为 `implemented_local`/`implemented_simulated`/`not_implemented`；`test_app.py` 为**精确字典相等**更新，未放宽。
- **前端**：证据面板（工具名/来源/检索时间/evidence_id/摘要，不含 note 原文与隐藏推理）、遥测面板、`impl-labels`、演示控制区三段（注入事件/修改事实/注入回执）、`mode-badge` 保留 `LOCAL` 与 `AWS 未连接`、轮询预算 75s + 15s 后退避、超期只显示「仍在处理，请刷新」（**前端不宣告失败**）、409 给出人类可读提示并重读任务、`failed` 区分「分析失败/执行失败」。

## 6 仍然模拟或未实现的内容

- 传感器事件与设备执行**始终为模拟**（`source=simulator`、`receipt.simulated=True`）；PawLink 项圈为概念。
- **未实现**：真实 Bedrock 调用（无账号）、AgentCore 长期记忆与 `feedback`/`new-session` 端点、DynamoDB 真表、跨进程/滚动双副本并发、云部署与访问控制、HTTPS、Alexa+。
- **已实现但未验证**：`bedrock_client.py` 依 strands 1.57.0 的本地内省签名编写，**未经真实账号验证**；`Dockerfile` 已改但本机无 Docker，**镜像未构建**。
- **已知局限（诚实披露）**：worker 顺序处理 → 实际并发为 1，`AdmissionControl` 的会话/全站上限当前只有单测覆盖、无生产路径触发；登录限速未实现（HTTPS 属 Day-4）；`demo/device-mode` 为进程级单值，多标签会互相影响且重启复位；A10「迟到回执」在同步模拟执行器下无实现基础，已书面归约为「重复回执幂等 + UNKNOWN 不盲目重试」，真异步回执入口顺延 Day-3/T6。

## 7 接口变化与消费者影响

- OpenAPI 路径由 **9 → 11**（+`/api/demo/facts`、+`/api/demo/device-mode`），并为业务路由补 401/403/404/409/422 的 `responses`。`domain.schema.json` 的 6 个输入模型**未变**。
- `RunView` 新增 `evidence`/`telemetry`/`policy_reason`/`failure_reason`；`FactsView.last_fed_minutes_ago` 与 `daily_dispensed_grams` 由 `int` 改为 **`int | null`**（破坏性：消费者必须处理 null）；`StateView` 新增 `analyzer`/`storage`/`memory`/`device_mode`（`analyzer` 为必填）。前端 `api.ts` 已在同一交付内同步，`npm run typecheck` 通过。
- 内部 seam 变更：`Proposer.analyze_event(event, snapshot, owner_id, *, model_calls_used=0) -> AnalysisOutcome`（不再传 `RunRecord`，避免内部记账字段进入模型层）；`EventAnalyzer.analyze_event(event, context) -> AnalysisOutcome`（原为 `-> Proposal`）。
- `Repository` 协议**放开**了 Day-1 的「只加字段不改签名」约束：新增 `list_claimable_runs`/`renew_lease`/`release_run`/`transition_run`/`reset_facts`，`claim_run` 增 `max_attempts` 关键字参数，`update_facts` 改用 `UNSET` sentinel。Day-4 的 DynamoDB 适配必须同构实现这些语义（尤其 CAS 与条件写）。
- 配置新增 10 个环境变量（见 `.env.example`）；`tests/conftest.py` 的 autouse 清理清单已同步全部别名。
- 新增 pytest markers `bedrock_offline`/`bedrock_live`，`addopts` 默认排除 `bedrock_live`（计费用例）。

## 8 运行的检查（命令 / 结果）

| 命令 | 结果 |
|---|---|
| `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **139 passed, 4 skipped**（基线 71 → 新增 68 项；4 skipped = `bedrock_live` 具名 blocked） |
| `uv run --frozen ruff check .` | All checks passed |
| `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current |
| `uv lock --check` | Resolved 65 packages，exit 0 |
| `uv sync --frozen --extra bedrock` | 成功（strands-agents==1.57.0 及依赖可复现安装） |
| `npm run typecheck` / `npm run build` | 通过（Node 24.19.0，vite 8.3.0） |
| `npx playwright test`（`workers: 1`、`PAWTWIN_WORKER_MODE=background`、`PAWTWIN_MODEL_BACKEND=local_fake`、Chromium 1194） | **7 passed**（8.7s）：approve 闭环 + 设备失败不记账 + needs-info + stale approval + decline 闭环 + 2 项 shell/门禁 |
| `./scripts/verify.ps1` | 全绿 |
| `./scripts/preflight.ps1` | 通过；输出 `credential source present: False` 与 `NOT EXECUTED` |
| `./scripts/bedrock-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2**（未虚报成功） |

明细与「这不证明什么」见 [day2-local.md](day2-local.md)。

## 9 未运行的检查及原因

- **真实 Bedrock 往返 / 真实模型参与正常与重复喂食场景 / A14 真模型对照 / A11 模型在环注入**：无 AWS 账号授权，未执行。`tests/test_bedrock_live.py` 以 4 条**具名 skip** 留痕（理由 `BLOCKED: no AWS account is authorised…`），`scripts/bedrock-smoke.ps1` 输出 `NOT EXECUTED` 并退出码 2。详见 [day2-cloud-blocked.md](day2-cloud-blocked.md)。
- **DynamoDB 条件写/事务/并发**：无账号，未执行；**不以 SQLite PASS 替代**（Day-4/T7）。
- **AgentCore memory strategy ACTIVE 检查**：无账号，未执行（Day-3）。
- **Docker 镜像构建、Linux 运行时、HTTPS/访问控制、部署与清理**：本机 PATH 无 Docker/AWS CLI，未执行（Day-4/T7）。`Dockerfile` 改动只记为「已修改、未构建验证」。
- **跨进程/滚动双副本的双标签批准、真实进程重启下的「处理中」恢复**：单进程环境无法验证，顺延 Day-3/T6。文件库下的「等待审批重启」已用两个 repository 实例（等价新进程）验证。
- **GitHub Actions 远程运行**：未推送远程，CI 改动未在远端执行过。
- **`bedrock_client._build_tools` 的 strands 工具注册**：需真实 SDK 调用路径，离线不可验证；已标注为未覆盖面。

## 10 独立审查发现与处理

见 [docs/reviews/day2.md](../reviews/day2.md)：非作者只读审查，结论 **PASS-WITH-NITS**，15 项核实 14 ✅ / 1 ⚠️，1 个重要缺陷 + 6 个 nit。重要缺陷（替身在 NULL 事实下伪造 0 并产出自相矛盾文案）与 5 个 nit 已修并复测；第 6 个 nit（worker 顺序处理使准入上限无生产触发路径）已接受并在文档中诚实披露。修复过程中另**自行发现并修正**两处：`_fail_unclaimed` 在 claim 失败路径被租约守卫挡掉（改为 CAS 写入且仅在无活租约时判定）、`_inline_proposal` 文案在 NULL 事实下打印 "None"。

## 11 云资源或费用变化

**无**。未创建任何云资源、未调用任何收费模型、未产生任何费用、未推送远程、未构建镜像。`strands-agents==1.57.0` 仅作为 optional extra 写入锁文件并在本地安装，CI 与默认本地环境不安装它。

## 12 下一步依赖 / 需总负责人决定

1. **提交授权**：改动尚未提交。建议分组：①门 0 契约与配置冻结（= Day-2 冻结提交）②后端并发原语与 worker ③AI 适配器与 Bedrock 客户端 ④前端与 e2e ⑤OPS 依赖/CI/镜像/脚本 ⑥文档与证据。是否提交、以及是否推送远程，需用户明确授权。
2. **账号就绪即刻执行**：`uv sync --frozen --extra bedrock` → 设置 `BEDROCK_MODEL_ID`/`AWS_REGION` 与凭据 → `./scripts/bedrock-smoke.ps1`（产生计费调用，须在授权预算内）→ `uv run --frozen pytest -m bedrock_live` → 把真实 request ID/时间/模型 ID/调用数/tokens/延迟写入 `docs/evidence/bedrock-call-*.md`，并把 `docs/STATUS.md` 的对应条件项从 blocked 改为已验证。
3. **Day-3 依赖**：AgentCore 记忆（AI-02）、`feedback` 与 `demo/new-session` 端点、会话持久化（当前仅进程内存）、跨进程双批准与真实进程重启复验、worker 并发执行（届时必须复验 `AdmissionControl` 与跨副本上限）。
4. **Day-4/T7 依赖**：`repo_dynamo` 必须同构实现 Day-2 新增的 CAS/续约/白名单语义；`deploy.ps1`/`cleanup.ps1` 尚未编写。
5. **需裁定的遗留**：`test_contracts.py` 是否要把 `RunView`/`StateView`/`EvidenceItem` 的字段名集合也冻结成断言（防止前端漏字段），当前仅由 `typecheck` 与 e2e 间接守卫。
