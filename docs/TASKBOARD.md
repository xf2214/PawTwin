# PawTwin 开发任务看板

本表由总负责人维护。`ready` 表示依赖满足、可认领，不表示已经有人开始。未获得明确开发指令时，不自行启动所有任务。

| ID | 状态 | Owner | 依赖 | 交付与验收 |
|---|---|---|---|---|
| INIT | done | 初始化 Agent + 总负责人 + 独立审查 Agent | 无 | 可启动骨架、契约、协作资料；26 项后端测试及前端/浏览器检查通过，详见 STATUS |
| BE-01 | done (Day-1, local) | 总负责人+后端(串行) | INIT | 契约已冻结（OpenAPI 含业务路由）；SQLite 持久化/去重/幂等回执/租约；DynamoDB 云测顺延 |
| BE-02 | done (Day-1 最小集, local) | 后端(串行) | BE-01 | 策略/登录/CSRF/审批/模拟执行/恢复(逻辑级)；A02/A03/A05/A12/A13(逻辑级) 本地绿；A04 跨进程、真实重启顺延 |
| BE-03 | done (Day-2, local) | 总负责人+后端(串行) | BE-02、门0冻结 | 并发原语（claim 白名单/续约/CAS/尝试上限原子自增）+ schema 幂等迁移 + 异步 worker + demo/facts、demo/device-mode；A04(同进程)/A09/A13(文件库)/A05(不重复调模型) 本地绿；跨进程顺延 |
| BE-04 | done (Day-3, local) | 总负责人+后端(串行) | BE-03、门0冻结(记忆 seam) | 反馈持久化(feedback 表/幂等)+ worker 真并发(有界池/per-task worker_id/先准入后 claim)+ 跨进程双批准(文件库两连接/WAL)+ 真实进程重启复验；A04(跨进程)/A13(真实进程) 本地绿；跨副本 DynamoDB 顺延 Day-4 |
| FE-01 | done (Day-1, local 联调) | 前端(串行) | INIT；联调需 BE-01 | 三主区 + 真实 /api 联调 + 拒绝闭环 e2e；记忆区/feedback 顺延 Day-3，demo/facts、device-mode 顺延 Day-2 |
| FE-02 | done (Day-2, local) | 总负责人+前端(串行) | 门0冻结；联调需 BE-03 | 证据面板+遥测、analyzer/storage/memory 标签、演示控制区接 demo 端点、中间态与显式超时提示、approve 闭环 e2e（共 7 项绿，各 spec 自行复位）；记忆区仍顺延 Day-3 |
| FE-03 | done (Day-3, local) | 总负责人+前端(串行) | 门0冻结；联调需 BE-04 | 任务与记忆区（反馈输入+memory_status 徽章+memory_backend 标签+新会话/conversation_id）；诚实标注「未实现（无账号）」，绝不声称已检索记忆；feedback e2e（e2e 共 10 项绿） |
| AI-01 | done (Day-1, local interfaces) | AI(串行) | INIT；真实调用需 AWS | 四只读工具 + owner 注入 + 证据校验 + mode-gated 本地替身；真实 Bedrock 与云测顺延 Day-2 |
| AI-03 | done (Day-2, local + 未验证云代码) | 总负责人+AI(串行) | AI-01、门0冻结(seam 签名) | `AnalyzerProposer` 适配器 + pinned 快照/证据台账 + 限额与超时 fail-closed + `AnalysisOutcome` 遥测；`BedrockAgent`/`bedrock_client.py` 已实装（strands 1.57.0、延迟导入、离线 stub 测试）但**未经真实账号验证**；真实往返仍为条件项（4 项具名 skip） |
| AI-02 | done (Day-3, local + 未验证云代码) | 总负责人+AI(串行) | AI-03、门0冻结(记忆 seam) | `memory.py`：`MemoryService` 协议 + `LocalFakeMemory`(saved/`search`→[]，绝不 available) + `AgentCoreMemory` 骨架(延迟导入，缺依赖/凭据→具名 `MemoryUnavailable`) + `StubMemoryService`；`search_owner_memory` 接线(source="memory" 证据链)；A06/A07/A08 结构本地绿；真实提炼/检索为条件项(无账号，5 项具名 skip) |
| OPS-01 | done (Day-1, plan only；**done 指计划与清单，不含镜像构建与部署**) | OPS(串行) | INIT；部署需账号预算 | `infra/cloud-access-checklist.md`；未执行、无资源、无费用 |
| OPS-02 | done (Day-2, plan+scripts；**done 指依赖/脚本准备，Dockerfile 未构建、smoke 未真实调用**) | 总负责人+OPS(串行) | 门0冻结 | `bedrock` optional extra（strands-agents==1.57.0）+ `uv.lock` + CI `uv lock --check` + Dockerfile `--extra`（**未构建验证**）+ `.env.example`/`.gitignore(*.db)`/README/角色简报 + `preflight.ps1` Bedrock 只读段 + `bedrock-smoke.ps1`（实测输出 NOT EXECUTED/退出码 2）+ 用量估算；未执行、无资源、无费用 |
| OPS-03 | done (Day-3, plan+scripts；**done 指依赖/脚本准备，Dockerfile 未构建、smoke 未真实调用**) | 总负责人+OPS(串行) | 门0冻结 | `memory` optional extra（`boto3==1.43.102`，硬门：`uv lock --check` + `uv sync --frozen --extra memory` 均成功）+ CI 全局 `uv lock --check` 覆盖 + Dockerfile `--extra memory`（**未构建验证**）+ `.env.example`/README/角色简报 + `preflight.ps1` AgentCore 只读段 + `agentcore-smoke.ps1`（实测 NOT EXECUTED/退出码 2）；未执行、无资源、无费用 |
| BE-05 | ready | 未认领 | S0 基线入库 | **Day-4**：访问控制补口——cookie `Secure` 由 `mode` 解耦为按请求 scheme 判定；补 `POST /api/runs/{run_id}/approval` 未登录 401 与缺/错 CSRF 403、`POST /api/logout` 未登录 401；补「`frontend/dist` 与全仓无 AWS 凭据」的 A12 本地证据。**不得记 A12 通过**：登录限速、会话 TTL、默认口令公网暴露三项为未闭合缺口（本轮不实现） |
| FE-04 | ready | 未认领 | S0、BE-05（共享 `api.py` 者须串行） | **Day-4**：浏览器验收矩阵新增 6 条 e2e（未登录深链、`unknown` 回执不显示虚假成功、待批准 reload、**1440px/390px 视口无溢出且不只显示颜色**、改事实→建议克数变化、新会话+记忆诚实回归），每条附「这不证明什么」；标签由**配置驱动改为证据驱动**（`request_id` 为 null 时不得显示「真实模型/真实检索」） |
| OPS-04 | ready | 未认领 | S0、门0不动 | **Day-4**：部署前置材料与 **fail-closed 脚本**——`deploy.ps1`/`cleanup.ps1` 缺 AWS CLI/缺 IaC 源/缺参数即 `NOT EXECUTED` + 退出码 2，绝不调用 AWS、绝不 `exit 0`；健康检查端点硬裁定（LB 与容器 HEALTHCHECK 一律 `/healthz`，`/readyz` 保持 503 不为部署改码）；修 `pyproject.toml` 与 `infrastructure.md`/`cloud-access-checklist.md` 的命令·注释级失真；实跑 `uv sync --frozen --extra bedrock --extra memory`。**镜像仅记「已静态审读、未构建」**（本机无 Docker，用户已裁定不安装） |
| QA-01 | blocked: integration | 未认领 | BE-03、FE-02、AI-03、AI-02 | A01–A14、云端/本地分开的结果、评委可改输入。**注**：Day-4 的 G6 浏览器矩阵 + G8 独立审查覆盖其本地可判定的子集；「评委自由输入」的量化判据依赖 T6 的 24 案例集 + `evaluate.py`，用户已于 2026-09-28 裁定**不在 Day-4 范围**，故 QA-01 仍不闭合（见第 4 日派发段的依赖冲突上报） |
| SUBMIT-01 | blocked: QA-01 | 未认领 | QA-01、实际赛事规则 | 英文材料、三分钟视频、概念图、边界声明；不自动提交 |

## 推荐派发顺序

1. BE-01 先冻结完整业务契约。它是后续并行最重要的依赖。
2. FE-01 的视觉/组件与 AI-01 的适配器设计可以并行，不能各自发明与后端不一致的接口。
3. BE-02、FE-01 联调、AI-01 工具实现分工作树推进。
4. AI-02 与 OPS-01 受账号条件影响；无账号先准备测试替身和部署计划，明确未云验证。
5. QA-01 独立检查，最后才制作参赛包装。

## 第 1 日派发（2026-09-23）

当日可执行分解见 [Day-1 开发计划](plans/PawTwin_Day1_开发计划.md)（多智能体两轮交叉校验 + 回源码二次核查后定稿）。当日主线 = 门 0 契约冻结 → BE-01/BE-02 最小集 + AI-01 适配接口/inline stub → FE-01 接真实本地 API（尽力）。必过门仅为「契约冻结 + SQLite 去重/持久化/幂等/租约 + 拒绝闭环」；正常闭环与前端联调为尽力项，真实模型调用为条件项，均不得以本地替身标为云端完成。

契约漂移裁定（由总负责人在门 0 统一落地，子 Agent 不得擅改 `models.py`/`contracts/`）：以 `models.py` 代码为权威——`EventIn.event_id:UUID`、`Receipt.command_id:UUID`（`uuid5(run_id:proposal_version)`）、`ApprovalIn.action_digest` 匹配 `^[0-9a-f]{64}$`、`Proposal.evidence_ids` 默认 `[]`；CSRF 走 `X-CSRF-Token` 头 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。

门 0 强制同步项（否则 `verify.ps1` 必红）：`tests/test_contracts.py` L10 与 L24 两处路径相等断言 + 删 L11；`tests/test_app.py` Day-1 保持 `/api/bootstrap` 语义不动、加 `/api/runs` 404 回归；`main.py` router 先于 `StaticFiles('/')` 注册；e2e 拆静态用例与业务用例（baseURL 指后端同源 `:8000`）。

并发上限（≤4，含总负责人）：常驻 Coordinator + Backend + (Frontend 或 AI)；Reviewer、OPS-01（仅计划）用空槽串行复用。

## 第 1 日完成记录（2026-09-23）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。详见 [STATUS](STATUS.md)。

- **门 0 契约冻结**：`models.py` 公开响应 DTO + 共享 `compute_action_digest`/`make_command_id`；`main.py` 业务 router 先于 `StaticFiles('/')` 注册；`contracts/openapi.json` 重生成含业务路由，`--check` 通过；基线测试同步（`test_contracts.py` 两处路径相等断言扩为业务集合并删旧否定断言；`test_app.py` 保 `/api/bootstrap` 语义、`readyz` 仍 degraded、新增 `/api/runs` 404 JSON 回归）。
- **裁定落地**：`command_id=uuid5(run_id:proposal_version)`；`action_digest=sha256(canonical_json(Action))` 匹配 `^[0-9a-f]{64}$`；CSRF 同步令牌 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。**新增裁定**：`RunView` 暴露 `proposal_version/action_digest`（审批防篡改须由客户端回显，否则冻结的 `ApprovalIn` 无法构造）；`owner_id/attempt_count/lease_*` 仍不入响应。
- **本地检查**：`pytest` 71 通过（二次检查补强 2 条审批安全测试）、`ruff` 无告警、契约 current、`typecheck`/`build` 通过、浏览器 e2e 3 通过（拒绝闭环 reload 仍「已拒绝」、零执行）、`verify.ps1` 全绿。
- **环境修复**：重建工作区 `.venv`（复制来的 `pytest.exe` 启动器指向旧源码树，致 pytest 导入旧 `pawtwin`）。
- **边界**：真实 Bedrock/AgentCore/DynamoDB 真表/跨进程双批准/真实重启/部署**未验证**，不以 SQLite 或本地替身冒充云端完成。
- **提交**：已按逻辑分组提交到 `chore/bootstrap`（用户授权，未推送远程）；**冻结提交 ID = `94216df`**；后续 `f2927cb`(后端测试)/`e20336d`(AI)/`f45edb8`(前端)/本提交(OPS+文档)。

## 第 2 日派发（2026-09-24）

当日可执行分解见 [Day-2 开发计划](plans/PawTwin_Day2_开发计划.md)（三视角智能体交叉校验 + 回源码二次核查后定稿，含 25 条技术裁定）。基线：`dc8dc10`，71 项 pytest + 3 项 e2e 绿，工作区干净。

**前提**：用户确认**仍无 AWS 账号** → 双轨：必过门（G0–G11）全部本地可验证，真实 Bedrock 往返与「云模型参与正常/重复喂食场景」为**条件项**，不以本地替身或离线 stub 冒充云端完成。范围取「全量」，估算 ≈ 24h 串行工时（不含 strands 实装）。

**当日主线** = 门 0 契约/配置冻结（C1）→ Backend 并发原语+迁移 ‖ AI 适配器+遥测 → worker+demo 端点 → `main.py` 装配（C3）→ Frontend 证据面板/演示控制/approve e2e → 依赖与脚本（C2）→ 集成与文档（C4）→ 非作者独立审查。

**必须先落定的高危裁定**（详见计划 §1，不改会造成二次出粮、假红或对评委失真）：

1. `claim_run` 改**可领取白名单**（仅 `queued`/`analyzing`）。现谓词只排除 5 个终态，`EXECUTING` 可被重领 → 抹掉已有回执 + `proposal_version` 变化 → 派生**新 `command_id`** → **第二次记账**，击穿 A01/A04 与任务单「重试不能更换 command_id」。
2. 新增 `transition_run` **CAS**：批准必须先 `AWAITING_APPROVAL→EXECUTING` 成功才执行，否则并发双批准会调两次 `device.execute`。
3. 证据校验用 **pinned 快照 + 追加式台账**，禁用 `available_evidence_ids()`（它重查库，分析期间 `facts_version` 被 bump 即产生假 `UNKNOWN_EVIDENCE`；且策略读旧快照、建议读新快照会 fail-open）。
4. `_inline_proposal` 的 `evidence_ids=["pet_facts"]` **不是合法 id**，必改（否则无条件强制校验会让 18 项测试全红）；`inline` 保留为测试专用后端以继续满足 Day-1「拒绝闭环不依赖 AI 替身」裁定。
5. A03 重评估拆为 `_reevaluate_under_new_facts`，**不调模型**（现在跑在 HTTP 请求线程内，接真模型后每次 stale approval 都是一次未预算、不受 45s/≤4 次保护的付费调用）。
6. `FactsView` 两字段改可空 + 删 `_facts_view` 的 `or 0`：否则事实未知时页面显示「上次喂食距今 0 分钟」而策略判 `MISSING_FACTS`，**对评委失真**；A09 也因此经 API 不可达（现零测试覆盖）。
7. schema **幂等迁移**（`PRAGMA user_version` + `ALTER TABLE ADD COLUMN`）+ `.gitignore` 补 `*.db`：现建表用 `IF NOT EXISTS` 且无迁移，新增列对持久库会崩，而测试全用 `:memory:` 永远发现不了。
8. `worker_mode` **默认 inline**，background 由 e2e `webServer.env` 与独立 fixture 显式开启；否则 `test_decline_loop.py` L30/L33-35/L64-66 必红。
9. `readyz`/`bootstrap` 上调为**分组件诚实**（reason 改 `cloud_adapters_not_verified`、capabilities 改 `implemented_local`/`implemented_simulated`/`not_implemented`），`test_app.py` L13-18/L31-42 **精确更新而非放宽**——履行 Day-1 审查 nit 5 的「正常闭环后再上调」处置；业务已实现却续报「业务未就绪」属**低报失真**。
10. strands 实装设**硬门**：先单独提交 `bedrock` optional extra + `uv.lock` 并验证 `uv sync --frozen --extra bedrock`；失败则 Day-2 完全不动依赖/CI/Dockerfile，仅保留接口 + 延迟导入 + 依赖缺失映射为显式 `FAILED`。

**所有权补裁（本日起生效）**：`AGENTS.md` L26-33 两份表**均未列** `main.py`/`config.py`/`Dockerfile`（Day-1 事实上归总负责人）→ 裁定由 **Coordinator 串行独占**；`repository.py`/`api.py`/`repo_sqlite.py`/`workflow.py`/`worker.py`/`device_sim.py` 属 **Backend**（不得划给 Coordinator）；`Proposer` 协议住 `workflow.py`（Backend）而适配器住 `agent.py`（AI），故 **seam 签名必须由 Coordinator 在门 0 冻结**。

**不可并行的临界段**：C1=`models.py`+`config.py`+`contracts/`+契约测试+seam 签名；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`；C3=`main.py` 装配（也是契约导出入口）；C4=`STATUS`+`TASKBOARD`+`evidence`。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；Reviewer、OPS 用空槽串行复用。**Reviewer 不得由作者充当**。单机串行时「并行」= 不重叠文件批次，必须按下方格式追加认领记录。

## 第 2 日完成记录（2026-09-25）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（用户已确认此方式；逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。临界段按 C1（契约/配置）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）顺序串行通过。详见 [STATUS](STATUS.md) 与 [day2-handoff](evidence/day2-handoff.md)。

- **门 0（C1）**：`models.py` 新增 `EvidenceItem`/`AnalysisTelemetry`/`AnalysisOutcome`/`ErrorResponse`/`DemoFactsIn`/`DemoDeviceModeIn`/`DemoAck`，`RunView` 增 `evidence`/`telemetry`/`policy_reason`/`failure_reason`，`FactsView` 两字段改可空，`StateView` 增 `analyzer`/`storage`/`memory`/`device_mode`；`config.py` 增 10 项 settings 与交叉校验；seam 签名冻结为 `analyze_event(event, snapshot, owner_id, *, model_calls_used=0) -> AnalysisOutcome`（**不传 `RunRecord`**）；openapi 重生成至 **11 条路径**并补 401/403/404/409/422；`test_contracts.py` 的 `$defs` 断言由 `<=` **收紧为 `==`**；`test_app.py` 的 readyz/bootstrap **精确上调**（未放宽）。
- **裁定落地**：25 条全部落地，其中高危项均已测试固化：claim 白名单（穷举 11 个状态）、批准 CAS（双线程并发只执行一次）、pinned 快照 + 台账校验、A03 零模型调用（telemetry/evidence 逐项相等）、持久化调用预算（第 5 次被拒）、schema 幂等迁移（旧文件库回归）、`worker_mode` 默认 inline、`readyz`/`bootstrap` 分组件诚实。
- **本地检查**：`pytest` **139 passed, 4 skipped**（基线 71 → 新增 68；4 skipped 为 `bedrock_live` 具名 blocked）、`ruff` 无告警、契约 current、`uv lock --check` 与 `uv sync --frozen --extra bedrock` 均成功、`typecheck`/`build` 通过、浏览器 e2e **7 passed**（`workers: 1`、background、local_fake）、`verify.ps1` 全绿。
- **独立审查**：非作者只读审查结论 **PASS-WITH-NITS**（15 项核实 14✅/1⚠），1 个重要缺陷 + 6 个 nit；重要缺陷（替身将 NULL 伪造成 0）5 个 nit 已修并复测，第 6 个（worker 顺序 drain 使准入上限无生产触发路径）已接受并在 STATUS 诚实披露。见 [reviews/day2.md](reviews/day2.md)。
- **边界**：真实 Bedrock/AgentCore/DynamoDB 真表/跨进程双批准/真实 OS 重启/部署与镜像构建**未验证**，不以 SQLite、本地替身或离线 stub 冒充云端完成；`bedrock-smoke.ps1` 实测输出 `NOT EXECUTED` 且退出码 2。
- **提交**：**尚未提交**，等待用户授权；建议分六组（门0冻结 / 后端 / AI / 前端+e2e / OPS / 文档），提交后回填 **Day-2 契约冻结提交 ID**。Day-1 冻结 ID `94216df` 保留为历史冻结点。无秘密入库、无云资源、**无费用**、无远程推送、**无镜像构建**。

## 第 3 日派发（2026-09-26）

当日可执行分解见 [Day-3 开发计划](plans/PawTwin_Day3_开发计划.md)（三视角交叉校验 + 回源码二次核查后定稿，含 14 条技术裁定）。基线：`dc8dc10`（Day-1），**Day-2 改动全部未提交**（38 modified + 14 untracked），144 项 pytest + 7 项 e2e 绿。

**前提**：用户确认**仍无 AWS 账号** → 双轨：必过门（G0–G10）全部本地可验证，AgentCore 真实提炼/检索与场景 C 真实记忆影响为**条件项**，不以本地替身或 stub 冒充「已检索记忆」。范围**按五日计划原样**；T6 的 24 案例集 + `evaluate.py` 顺延 Day-4。

**当日主线** = 门 0 契约/配置冻结（C1，含记忆 seam）→ Backend 反馈持久化 ‖ AI `memory.py`+检索接线 → worker 真并发 → 跨进程双批准/真实进程重启 → `main.py` 装配（C3）→ Frontend 记忆区/反馈/新会话 e2e → memory extra 与脚本（C2，硬门）→ 集成与文档（C4）→ 非作者独立审查。

**必须先落定的高危裁定**（详见计划 §1）：

1. `memory_status` 诚实语义：无账号时反馈恒 `saved`（原文已存业务库），**绝不** `processing`/`available`（本地无提炼任务）；`available` 仅在真实 AgentCore 检索证据出现时（AGENTS.md L18）。`FeedbackView` 携 `memory_backend` 标签使 `saved` 不被读成「已提炼」。
2. `search_owner_memory` 接线 `MemoryService`：本地返回 `[]` 且**不记** memory 证据（不伪造）；stub/真实服务返回记录时才出 `source="memory"` 证据、proposal 可引用。场景 C「记忆改变建议」= 条件项。
3. worker 由**顺序 drain** 改**有界线程池**（池=`max_concurrent_global`）：先准入后 claim、per-task worker_id；**闭合 Day-2 nit#6**（准入上限获得生产触发路径），且 CAS/白名单/租约在真并行下继续成立。
4. 跨进程双批准 = **两个 `SqliteRepository` 指向同一文件库**（WAL + busy_timeout），断言 **DB 不变式**（非共享 device 计数器）。诚实边界：SQLite 两连接 **≠** DynamoDB 多副本（Day-4）。
5. 真实 OS 进程重启：**必过** = 文件库两实例逻辑重启（含 `ANALYZING`+活租约不二次分析）；**尽力** = subprocess kill/relaunch 真重启（marker `restart`）。
6. 会话仍进程内存（裁定 6 顺延 DB 持久化）：重启后重登录，作为诚实边界披露；`conversation_id` 存 owner 级进程内映射，重启复位。
7. memory extra 设**硬门**：先单独提交 `uv add --optional memory` + `uv lock` 并验证 `uv sync --frozen --extra memory`；失败则 Day-3 完全不动 `pyproject/uv.lock/Dockerfile/CI`，仅保留 `MemoryService` 接口 + 延迟导入 + 缺依赖/凭据映射为 `not_implemented`（绝不伪造）。

**所有权**（沿用 Day-2 补裁）：`memory.py` = AI；`repository.py`/`repo_sqlite.py`/`worker.py`/`api.py` = Backend；`models.py`/`config.py`/`contracts/`/`main.py` = Coordinator；`frontend/src/` = Frontend；`pyproject/uv.lock/Dockerfile/ci.yml/preflight/smoke` = OPS/Coordinator。`MemoryService` 协议 + `AgentContext` 注入 seam + `FeedbackRecord` **由 Coordinator 在门 0 冻结**。

**不可并行的临界段**：C1=`models.py`+`config.py`+`contracts/`+契约测试+记忆 seam；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`；C3=`main.py` 装配；C4=`STATUS`+`TASKBOARD`+`evidence`。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；Reviewer、OPS 用空槽串行复用。**Reviewer 不得由作者充当**。

## 第 3 日完成记录（2026-09-26）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（用户已确认此方式；逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。临界段按 C1（契约/配置/记忆 seam）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）顺序串行通过。详见 [STATUS](STATUS.md) 与 [day3-handoff](evidence/day3-handoff.md)。

- **门 0（C1）**：`models.py` 新增 `MemoryStatus`/`MemoryBackend`/`FeedbackScope`/`FeedbackView`/`NewSessionView`，`StateView` 增 `conversation_id`/`feedback`；`config.py` 增 `memory_backend` 与交叉校验；书面冻结 `MemoryService` seam（`submit_feedback`/`get_status`/`search`）与 `FeedbackRecord`；openapi 重生成至 **14 条路径**并补 401/403/404/422；`domain.schema.json` 仍**恰为** 6 输入模型 + `RunState`（`==` 断言）；`test_contracts.py` 的 `ACTIVE_PATHS` +3 并改写旧注释。
- **裁定落地**：14 条全部落地，高危项均已测试固化：`memory_status` 本地恒 `saved`（绝不 `available`）、`search_owner_memory` 本地返回 `[]` 不伪造证据、stub 记忆→`source="memory"` 可引用证据、worker 有界线程池真并发（`peak_concurrency` 断言、闭合 nit#6）、跨进程（两连接）双批准 DB 不变式、文件库逻辑重启 + subprocess 真进程重启（`ANALYZING`+活租约不二次分析）、会话仍进程内存（裁定 6）。
- **本地检查**：`pytest` **184 passed, 11 skipped**（审查后 +2 回归；多次运行一致；11 skip 均具名 = 5 agentcore_live + 4 bedrock_live + 1 bedrock_offline + 1 restart 尽力项）、`ruff` 无告警、契约 current（14 路径）、`uv lock --check` 与 `uv sync --frozen --extra memory` 均成功（`boto3==1.43.102`，无新增下载）、`typecheck`/`build` 通过、浏览器 e2e **10 passed**、`verify.ps1` 全绿。
- **独立审查**：非作者只读审查结论 **PASS-WITH-NITS**（8 项高信号逐条核实全 ✅），3 个 nit（worker 关闭期准入槽泄漏、`post_feedback` 未归约 `MemoryUnavailable`、缺 v2→v3 迁移回归测试）均已修并复跑。见 [reviews/day3.md](reviews/day3.md)。
- **边界**：真实 AgentCore 提炼/检索、场景 C 真实记忆影响、DynamoDB 真表/跨副本、真实 OS 进程被 kill 于 ANALYZING、部署与镜像构建**未验证**，不以 SQLite/两连接/本地替身/stub 冒充云端完成；`agentcore-smoke.ps1` 实测输出 `NOT EXECUTED` 且退出码 2。
- **提交**：**尚未提交**（Day-2 与 Day-3 改动共处同一脏工作区），等待用户授权；建议分六组（门0冻结 / 后端 / AI / 前端+e2e / OPS / 文档），提交后回填 **Day-3 契约冻结提交 ID**。Day-1 冻结 ID `94216df` 保留为历史冻结点。无秘密入库、无云资源、**无费用**、无远程推送、**无镜像构建**。

## 第 4 日派发（2026-09-28）

当日可执行分解见 [Day-4 开发计划](plans/PawTwin_Day4_开发计划.md)（三视角交叉校验 + 存疑项源码核验 + 总负责人回源码仲裁后定稿，含 14 条技术裁定与 F1–F15 实测事实表）。基线：`dc8dc10`（Day-1 末），**Day-2 与 Day-3 改动全部未提交**，实测 **39 modified + 31 untracked**（Day-3 计划记的 38+14 已过时）；`.gitignore` 覆盖完整、无秘密、无 remote。

**前提（用户 2026-09-28 确认）**：①**仍无 AWS 账号，但用户即刻注册** → 双轨继续，真实云为条件项，账号就绪日按 Day-4 计划 §7.5 手顺执行；②**开工前先分组提交 Day-2/Day-3**（S0，逐组需用户在场授权）；③范围**只取 T7 + 独立审查 + 浏览器验收 + 针对失败修复**，**不含** T6 的 24 案例集与 `evaluate.py`、`repo_dynamo`、会话 DB 持久化与登录限速；④**不安装 Docker** → 镜像完全不可解锁构建验证，只记「已静态审读、未构建」。

**当日主线** = S0 基线入库（C0）→ G1 干净树全量回归实测 → G2 访问控制补口 ‖ G3 健康检查端点硬裁定 → G4 `deploy.ps1`/`cleanup.ps1` fail-closed 门控脚本 → G5 镜像静态审读 + `pyproject.toml` 假陈述修正 + 合并 extra 实测 → G7 标签证据驱动 + `available` 反伪造守卫 → G6 浏览器验收矩阵（6 条新 e2e）→ G9 文档四件套与上报 → G8 非作者独立审查。合计 ≈ **20–23h 串行工时**（= 全量 Day-4 减去一切云端项）。

**必须先向上报的事实（不得拆成半通过）**：总方案 L103 的第 4 日字面验收「HTTPS 演示可访问；可部署可删除」经实测存在**四重独立阻断**——本机无 Docker/AWS CLI/CDK（F1）、`infra/` 无任何 IaC 源且 `deploy`/`cleanup` 脚本不存在（F5）、`create_app` 对 `mode==aws` 无条件拒启（F6，且这是**正确设计不是 bug**，禁止为了 demo 而移除）、无证书与公网地址。按总方案 L106/L153：**云端里程碑整体顺延并上报，当日产物不得标为参赛完成**。

**必须先落定的高危裁定**（详见计划 §1）：

1. **只回填一个真实存在的契约冻结提交 ID**：实测 `94216df` 与 HEAD 的 `openapi.json` 均为 **9 条路径**、工作区为 14 条 → **Day-2 的 11 路径冻结点从未入库**。禁止为凑两个 ID 手改生成文件；须在 `STATUS.md`/本表**书面披露**该事实，并声明中间提交不逐个复验（`models.py`/`api.py`/`contracts/` 终态互依赖）。
2. **`.gitignore`（含 `*.db`）+ `pyproject`/`uv.lock` 为第一组**：HEAD 的 `.gitignore` 实测**不含 `*.db`**，否则单独 checkout 跑重启类测试即产生未忽略的库文件、工作区变脏。
3. **cookie `Secure` 与 `mode` 解耦**：现判据为 `mode == "aws"`（`api.py:187`）而镜像烤死 `PAWTWIN_MODE=local` → 部署到 HTTPS 后 **cookie 不带 Secure**。改为按请求 scheme 判定；本地无证书仍不得声称「HTTPS 会话安全已达标」。
4. **健康检查端点硬裁定**：`/readyz` 无分支硬编码 **503**（`main.py:125-138`），若 ALB/target group 指它则任务**永不健康**且表象会被误读为镜像问题 → 一律用 `/healthz`，`/readyz` 保持 503 且**严禁**为部署而改码。
5. **`deploy.ps1`/`cleanup.ps1` 的诚实形态 = fail-closed 门控脚本**：检查顺序固定为 CLI 存在性 → IaC 源存在性 → 必填参数；缺任何一项即 `NOT EXECUTED` + **退出码 2**，绝不调用 AWS、绝不 `exit 0`；`-PlanOnly` 保留任务单命名但 `.SYNOPSIS` 须钉死「无 CLI 时不产出任何 plan」；account id 仅运行期注入、**绝不预填**。（与 `preflight.ps1` 的退出码语义分级：环境自检无凭据仍 exit 0，**计费/资源类才 fail-closed**）
6. **前端标签改为证据驱动**：`App.tsx:48-52/475-477` 的「AWS Bedrock（真实模型）」「AgentCore（真实检索）」当前**由配置推导**；而 `MemoryService.get_status` 生产端**零调用者**、`agentcore_client.py:151-152` 的 `return "available"` 为**不可达代码** → 措辞必须写「接口已就位、生命周期**未接线**」（既非「已实现待验证」也非「完全未实现」），并新增**反伪造守卫测试**：本地配置下不得存在任何能把 `memory_status` 写成 `available`/`processing` 的路径。
7. **登录限速 / 会话 TTL / 默认口令 = 公网部署前置硬门**：三者实测**零实现**（`Session.created_at` 无消费者、口令 `local-demo-passphrase` 随源码公开），且会话为进程内 `dict` + cookie 值即 `session_id` 明文 → **多副本必致 401**、`AdmissionControl` 仅进程内计数 → 滚动两副本实际全站并发 = 副本数 × 2。本轮**不实现**，只出书面裁定议题。

**上报的依赖冲突（不得静默吸收）**：① T6 的 24 案例集与 `evaluate.py` 被用户排除在 Day-4 外，而 **Day-5 的「测试与评委自由输入」判据与它同源**（总方案 L138、任务单 L315-317）→ 不补做则 Day-5 该项只能降级为「人工现场脚本、无固定案例集量化报告」；② Day-5 字面已含材料全套（冻结功能 + 概念图 + 演示脚本 + 英文材料 + 录屏），**被顺延的云端块压不进同一天**；③ 无 AWS 验证时，Day-5 产物必须写作「**本地验证候选（非参赛版）**」（总方案 L153）。

**所有权**（沿用 Day-2 补裁）：`api.py`/`auth.py` = Backend；`frontend/src/`+`frontend/e2e/` = Frontend；`scripts/*.ps1`/`infra/` = OPS/Coordinator；`main.py`/`config.py`/`contracts/`/`Dockerfile`/`STATUS`/`TASKBOARD` = Coordinator；Reviewer **不得由作者充当**。

**不可并行的临界段**：C1=`api.py`+`auth.py`+`tests/test_auth.py`（G2 与 G7 共享 `api.py`）；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`+`scripts/*`；C3=`frontend/src/App.tsx`+`frontend/e2e/*`；C4=`STATUS`+`TASKBOARD`+`evidence`。**门 0 不动**：Day-4 应保持 OpenAPI 恰 14 条路径、`domain.schema.json` 的 `$defs` 恰为 6 输入模型 + `RunState`；若某项改动触发契约变化，回门 0 重议，**不得**放宽 `test_contracts.py` 的 `==` 断言。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + Frontend；OPS、Reviewer 用空槽串行复用。单机串行时「并行」= 不重叠文件批次，需按下节格式追加认领记录。新增任务行：`BE-05`、`FE-04`、`OPS-04`（均 `ready`）。

## 认领记录格式

每项开始前追加：任务 ID、Agent/任务名称、起始提交、工作树路径、分支、允许写的文件、预计交付、接口变更需求。完成后填写交付提交和验证证据链接。不要让多个 Agent 同时改此表。
