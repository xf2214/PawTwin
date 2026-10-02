# PawTwin 开发任务看板

本表由总负责人维护。`ready` 表示依赖满足、可认领，不表示已经有人开始。未获得明确开发指令时，不自行启动所有任务。

## 2026-10-02 附加工作包

需求/验收以 [附加计划](plans/PawTwin_附加开发计划_2026-10-02.md) 为准，接手先读 [Qoder 说明](QODER_HANDOFF.md)。本次只同步文档，未派发实施。
全部 Owner 未认领；建议分工不代表已有进度，不与旧任务的本地完成状态混淆。

| ID | 状态 | Owner | 依赖 | 交付 |
|---|---|---|---|---|
| EXT-00 | ready（待认领） | 未认领 | 当前基线检查 | 接口、兼容迁移与写路径冻结 |
| EXT-01 | planned | 未认领 | EXT-00 | 独立身份、作者、会话恢复 |
| EXT-02 | planned | 未认领 | EXT-01 | 家庭/邀请/称呼/权限/撤权 |
| EXT-03 | planned | 未认领 | EXT-02 | 共享迁移、任务生命周期、同步/并发 |
| EXT-04 | planned | 未认领（Qoder 可选） | EXT-03 | 成长记录与纠错 |
| EXT-05 | planned | 未认领（Qoder 可选） | EXT-04 | 日/周统计与自动补跑/重建 |
| EXT-06 | planned | 未认领 | EXT-05 | 个体上下文与记忆确认/失效 |
| EXT-07 | planned | 未认领（建议 Qoder） | EXT-00；联调另依赖 EXT-02–06 | App 导航、小屋/家庭/成长/报告组件 |
| EXT-08 | planned | 未认领 | EXT-06、EXT-07 | App/Alexa 模拟共用分身与受控行动 |
| EXT-09 | planned | 未认领 | EXT-06、EXT-08 | 参考知识、健康问答边界 |
| EXT-10 | planned | 未认领 | EXT-00 起预检；云验收依赖 EXT-03–08 及账号/预算 | 云身份/资料/模型/记忆证据 |
| EXT-11 | planned | 未认领 | 对应已实施包 | 验收、用户试用与独立复核 |
| EXT-12 | planned | 未认领 | EXT-11；AWS 宣称另依赖 EXT-10 | 英文材料、演示和访问检查 |

认领格式：日期 / ID / Owner / 基线与未提交内容 / 可写路径 / 依赖和接口版本 / 验收 / 交接。当前没有认领记录。
共享契约、锁文件、main/config、api.ts 和状态文档串行协调，不覆盖别人的修改。

## 既有 Home 与 Day-1–Day-5 历史

2026-10-02 用户授权「按六项改」并补充洗澡、剪指甲、成长照片：由总负责人串行完成
HOME-01 档案/模板形象、HOME-02 物品管理、HOME-03 照护计划、HOME-04 范围偏好、
HOME-05 家庭显示名与交接、HOME-06 照片日记与摘要。以上本地实现及验证完成，
详见 STATUS。照片识别实际云调用、生成式肖像、独立成员账号、
多宠物自动喂食和新资料层云存储未完成；不将本地扩展升级为云端或参赛验收完成。

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
| BE-05 | done (Day-4, local) | 总负责人(串行) | S0 基线入库 | **Day-4**：访问控制补口——cookie `Secure` 由 `mode` 解耦为按请求 scheme 判定；补 `POST /api/runs/{run_id}/approval` 未登录 401 与缺/错 CSRF 403、`POST /api/logout` 未登录 401；补「`frontend/dist` 与全仓无 AWS 凭据」的 A12 本地证据。**不得记 A12 通过**：登录限速、会话 TTL、默认口令公网暴露三项为未闭合缺口（本轮不实现） |
| FE-04 | done (Day-4, local) | 并行执行体(总负责人独立复核) | S0、BE-05（共享 `api.py` 者须串行） | **Day-4**：浏览器验收矩阵新增 6 条 e2e（未登录深链、`unknown` 回执不显示虚假成功、待批准 reload、**1440px/390px 视口无溢出且不只显示颜色**、改事实→建议克数变化、新会话+记忆诚实回归），每条附「这不证明什么」；标签由**配置驱动改为证据驱动**（`request_id` 为 null 时不得显示「真实模型/真实检索」） |
| OPS-04 | done (Day-4, plan+scripts；**镜像未构建、真实 plan/apply 未实现**) | 并行执行体(总负责人独立复核) | S0、门0不动 | **Day-4**：部署前置材料与 **fail-closed 脚本**——`deploy.ps1`/`cleanup.ps1` 缺 AWS CLI/缺 IaC 源/缺参数即 `NOT EXECUTED` + 退出码 2，绝不调用 AWS、绝不 `exit 0`；健康检查端点硬裁定（LB 与容器 HEALTHCHECK 一律 `/healthz`，`/readyz` 保持 503 不为部署改码）；修 `pyproject.toml` 与 `infrastructure.md`/`cloud-access-checklist.md` 的命令·注释级失真；实跑 `uv sync --frozen --extra bedrock --extra memory`。**镜像仅记「已静态审读、未构建」**（本机无 Docker，用户已裁定不安装） |
| BE-06 | done (Day-5, local; 云端未验证) | Backend(串行) | OPS-05（表与 IAM）、门0不变 | **Day-5**：`repo_dynamo.py` 实现 `Repository` 全协议（条件写/CAS/租约白名单/`TransactWrite` 幂等记账，单表 `pk/sk`+`entity-index` GSI）+ `dynamodb_live` marker + 离线协议集合守卫；公网三门（默认口令 aws 拒启 / 会话 TTL+idle / 登录限速 429+`Retry-After`）+ `/api/login` 429（路径仍 14）；`SCHEMA_VERSION` 3→4 + `agentcore_session_id`。**真表 12 项 `dynamodb_live` 全 skip（无凭据）→ 未云验证** |
| AI-04 | done (Day-5, local; 云端未验证) | AI(串行) | BE-06（`FeedbackRecord` 字段）、门0不变 | **Day-5**：`agentcore_client.py` 按真实 API 重写（`CreateEvent` 会话 payload+`namespaceVariables` / `GetEvent(memoryId,sessionId,actorId,eventId)` / `RetrieveMemoryRecords(namespacePath,searchCriteria)`）；`memory.py` 两段式 `get_status`→`MemoryStatusResult`；`_namespace` `/owner/<o>/pet/<p>` 与 `deploy_plan.json` 命名模板跨源守卫；`worker.py` `MemoryPoller` 接线；守卫按裁定 12 **改作用域非放宽**（`<= {worker.py}`+AST，白名单未扩）。**真实往返 5 项 skip；响应字段/状态词表未核实** |
| FE-05 | done (Day-5, local) | Frontend(串行) | BE-06、AI-04 | **Day-5**：真实态标签**证据驱动**（`storage=dynamodb`+`aws_connected`、`已提炼（真实 AgentCore 记录 N 条）` 仅当 `memory_record_count>0`）；`FeedbackView` 加非秘密 `memory_record_count`；新文案避开 e2e 禁串，`test_frontend_labels.py` 守卫**扩到新常量** `MEMORY_EXTRACTED_LABEL` + 新增「提炼标签必须与 `memory_record_count` 配对」；本地 e2e **16 passed** 未放宽。真实态标签仅 aws 态可见，**未云验证** |
| OPS-05 | done (Day-5, plan+scripts; 镜像未构建、真实 apply 未执行) | Infrastructure/Coordinator(串行) | 用户短期凭据、GitHub 私有仓 | **Day-5**：`infra/deploy_plan.json` + `scripts/deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py`（boto3 声明式编排，**不引入 CDK/CFN**）；`deploy.ps1`/`cleanup.ps1` 门控判据改为「plan 源存在 + boto3/uv 能力」，`-PlanOnly` 现为**真实离线 plan**（EXIT=0，零 AWS 调用）、`-Apply`/`-Destroy` 委派编排器（缺前提仍 `NOT EXECUTED`/exit 2）；`image.yml`（OIDC 构建推 ECR，单架构 amd64）+ `Dockerfile` 解耦 `PAWTWIN_MODE`；`.gitignore` 先行加 `deploy_state.json`。**镜像未构建、workflow 未运行（无 remote/无 Docker）、`-Apply` 未执行（无凭据/无预算确认）** |
| QA-01 | blocked: Day-5 云端证据待凭据 | 未认领 | BE-03、FE-02、AI-03、AI-02、BE-06、AI-04、OPS-05 | A01–A14、云端/本地分开的结果、评委可改输入。**Day-5 进展**：本地可判定子集由 e2e 16 + 后端 232 覆盖；「评委自由输入」量化判据依赖的 24 案例集 + `evaluate.py` **已就绪**（`scenarios.json` A01–A14 全覆盖 + 离线结构校验），但**真机跑批（G9）依赖 G7 部署**，无凭据未执行。A01–A14 的**云端部分仍待凭据** |
| SUBMIT-01 | blocked: Day-6 材料与赛事规则 | 未认领 | QA-01、**Day-5 云端证据**、实际赛事规则 | 英文材料、三分钟视频、概念图、边界声明；不自动提交。Day-5 只出部署与验收，材料整体顺延 Day-6（用户 2026-09-30 裁定） |

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

## 第 4 日完成记录（2026-09-29）

实际以**单一开发环境、两个执行体按不重叠文件批次并行**完成（并行执行体承担 G4/G5/G6/G7 的编码与提交，总负责人承担 S0/G1/G2/G3/G9）；总负责人**未采信**对方绿灯，对其提交后的 HEAD 独立重跑全部检查，并修复 2 处问题（`ruff I001` 会使 `verify.ps1` 直接中断；冗余导入别名 `_MU` 遮蔽模块级导入）。详见 [STATUS](STATUS.md) 与 [day4-handoff](evidence/day4-handoff.md)。

- **S0 基线入库（G0）**：Day-2 与 Day-3 全量改动按 `S0-a…S0-g` 七组入库（`56be355`→`b1f508a`），`.gitignore`（含 `*.db`）+ `pyproject`/`uv.lock` 为先行组。**只回填一个合并契约冻结 ID = `590aa5a`**，并书面披露：实测 `94216df` 与 `dc8dc10` 的 `openapi.json` 均为 **9 条路径**，故 Day-2 的「11 路径冻结点」**从未入库**，且契约为生成物不可手改 → 无法分离为两个快照；中间提交不逐个复验，只在最终 HEAD 声明全绿。
- **G1 干净树回归**：`pytest -o addopts=""` **192 passed, 10 skipped**（均具名）、默认 addopts **192 passed/1 skipped/9 deselected**、`ruff` 无告警、契约 current（仍 **14 路径**，`domain.schema.json` 未变）、`uv lock --check` exit 0、`verify.ps1` EXIT=0。skip 由 11 变 10 的原因已书面说明（本轮装了合并 extra，`test_bedrock_adapter_offline` 改为真实执行；CI 不装 extra 故仍 skip）。
- **G2 访问控制（BE-05）**：cookie `Secure` 由 `mode == "aws"`（部署形态下**永假**）改为按请求 scheme；`X-Forwarded-Proto` 仅在 `PAWTWIN_TRUST_PROXY_HEADERS=true`（默认关，G8 第二轮改正）时采信且只能加不能减；补齐 approval 的 401/403 与 logout 的 401（该路由此前**零鉴权断言**）；**负向验证**已做（回退后转红）。**A12 不记通过**：登录限速、会话 TTL、默认口令公网暴露三项仍未闭合（裁定 14 议题待用户定）。
- **G3 健康检查硬裁定**：LB/target group 与容器 `HEALTHCHECK` 一律 `/healthz`；`/readyz` 恒 503 仅作诊断，**不为部署改码**（`test_app.py` 精确断言未放宽）。
- **G4/G5 部署前置材料（OPS-04）**：`deploy.ps1`/`cleanup.ps1` 为 fail-closed 门控（CLI → IaC 源 → 必填参数 → 授权令牌），实测均 `NOT EXECUTED` + **退出码 2**、零 AWS 调用、无 `exit 0` 路径；`uv sync --frozen --extra bedrock --extra memory` exit 0；修正三处文档假陈述（`pyproject` 的 extra 描述、checklist 不存在的 `-Mode aws`、`infrastructure.md` 的退出码笼统要求）。**镜像仍未构建**（本机无 Docker，用户已裁定不装）。
- **G6/G7 浏览器验收与标签诚实（FE-04）**：新增 `acceptance.spec.ts` 6 条（未登录 401 JSON、`unknown` 回执不显示成功且不记账、待批准 reload、**1440px/390px 无溢出且状态不只靠颜色**、改事实→克数变化、新会话+记忆诚实），e2e **10 → 16 全绿**；标签改为**证据驱动**（无 `request_id`/无真实记忆证据不得称「真实」）；`available` 反伪造守卫 4 条（含静态字面量守卫）。首次引入视口断言即暴露并修复 **390px 横向溢出 6px** 的真实缺陷（改 `styles.css`，**未放宽断言**）。
- **G8 非作者独立审查（共两轮）**：第一轮 ✅ PASS（CodeReview 子代理，范围 `b1f508a..63f3de6`，10 项核实全 ✅，零发现；总负责人另对「零发现」作 3 项独立复核均成立）。第二轮（覆盖 `c4ae5f8..63f3de6` 全部 Day-4 本地提交）**PASS-WITH-NITS：0 阻断 / 4 重要 / 8 nit**，第一轮的「无 important」在更大覆盖面下不成立；4 重要已全部修复（`a575a61`）：①代理头改受信开关（回归裁定 5/预案 A）②标签含 e2e 禁串→重写+新增 `test_frontend_labels.py` 2 项耦合守卫③文档高报「干跑全部路径」→更正为「均停 Gate 1，Gate 2–4 仅代码审读」④样式注释失真→改正；nit 落地含静态守卫盲区声明、`get_status` 未接线不变式断言、「真实模型」与 backend 相与、字符串耦合拆分。复跑 **195 passed/10 skipped** + e2e 16 + verify 全绿。教训：**同视角复核不能替代覆盖面更广的第二轮审查**。见 [reviews/day4.md](reviews/day4.md) §7。
- **G9 文档**：`STATUS.md` 新增 Day-4 三档表 + 本地/云端双列 + 提交表；`evidence/day4-handoff.md`（12 项）、`day4-local.md`（含「这不证明什么」）、`day4-cloud-blocked.md`（N1–N10 逐条阻断与解锁前提）；Day-1/2/3 历史文档**只追加后记**（已就冻结 ID 预期不可达成一事分别追记）。
- **字面验收上报**：总方案 L103 的第 4 日验收「HTTPS 演示可访问；可部署可删除」因**四重独立阻断**整体不可达成，已按 L106/L153 上报顺延；**无 AWS 验证时 Day-5 产物须命名「本地验证候选（非参赛版）」**。未选的 T6 案例集与 Day-5「评委自由输入」验收同源，冲突已上报待用户二选一。
- **提交**：`c4ae5f8`(G2) → `a37c161`(G4/G5) → `94442b5`(G7 标签+390px) → `f3b96e4`(G7 守卫+FE-04 e2e) → `63f3de6`(G9 文档) → `aaaddd3`(G8 第一轮回填) → `a575a61`(G8 第二轮补修) → `ebe3e11`(移出误入库审查临时产物)。**仍未推送远程**（无 remote，需授权）。无秘密入库、无云资源、**无费用**、**无镜像构建**。
- **云端切片前置（2026-09-29 晚）**：用户确认账号注册中、**凭据尚未就绪**且今日不执行计费调用；本机已装 **AWS CLI v1.46.1**（pip --user，不入仓库），deploy/cleanup 实测改停 `cdk` 缺失门（仍 exit 2）；§7.5 手顺停在「凭据注入」一步，待账号就绪后续执行。

## 第 5 日派发（2026-09-30，真实部署专日）

当日可执行分解见 [Day-5 开发计划](plans/PawTwin_Day5_开发计划.md)（规划阶段已用真实账号前置条件下的命令与内省核实环境，含 19 条技术裁定与 G-A…G-Q 实测事实表）。基线：`chore/bootstrap` HEAD=`9354804`，**工作树干净**，无 remote；实测 pytest **195 passed / 10 具名 skip**、e2e **16 passed**、契约 **14 条路径 current**、`verify.ps1` EXIT=0。

**前提（用户 2026-09-30 确认六点）**：①**AWS 账号与凭据已就绪**，由用户本机注入**短期**凭据（不入聊天、`.env`、仓库、镜像层）；②镜像**由 GitHub Actions 远程构建并推送 ECR**，CI 取云权限走 **OIDC 角色**；③**部署深度 = 完整真实部署**（`repo_dynamo` → 移除 `mode=aws` 拒启 → 真实 Bedrock + 真实 AgentCore → ECS Express Mode HTTPS 演示地址）；④**T6 的 24 案例集 + `evaluate.py` 补做并在真实模型上跑**；⑤**Day-5 专做真实部署，参赛材料整体顺延 Day-6**；⑥**公网安全三门全做**（默认口令拒启 / 会话 TTL / 登录限速）。

**双轨策略自本日起终止**：账号就绪后真实推理、真实 DynamoDB、真实 AgentCore 即为唯一交付证据；`local_fake`/`StubMemoryService`/SQLite 只保留为离线测试后端，不得再充当任何验收凭据。

**当日主线** = P0 只读就绪门与用户节点 → G1 基线复跑 → D1/D1' `repo_dynamo` 实现与**真表**全套验证 → D2 公网三门 + 429 契约重生成 → D3 AgentCore 数据面真实化 + 轮询接线 + `SCHEMA_VERSION` 4 → D4 `deploy_plan.json` + boto3 编排器 + OIDC/IAM → D5 CI 真实构建推 ECR → D6 云装配 + 前端真实态标签 → `deploy.ps1 -Apply`（**前置：费用实测 + 用户书面预算确认**）→ G8 部署面 A01–A14 真实子集 → D7 24 案例集真机跑批 → D8 证据文档 → G11 非作者独立审查。合计 ≈ **28–33h**，**超出一日**，执行承接至 Day-6 上午。

**必须先向上报的事实（不得拆成半通过）**

1. **五日变六日**：总方案 L104 的 Day-5 字面同时要求「冻结功能 + 评委自由输入 + 概念素材 + 演示脚本 + 英文材料 + 录屏」，本轮又承接 Day-4 顺延的**全部**云端块。据用户裁定⑤，**材料整体顺延 Day-6**，因此总方案第 6 节实际执行变为六个工作日。
2. **Day-3 的 AgentCore 客户端不能直接跑起来**：`agentcore_client.py:128/144/164` 调的 `create_event(namespace=…)` / `list_events(memoryId=…)` / `search_memory(…)` 在真实 API 中**不存在或参数不足**（真实为 `GetEvent(memoryId,sessionId,actorId,eventId)` 与 `RetrieveMemoryRecords(memoryId,namespacePath,searchCriteria.searchQuery)`）。它现被 fail-closed 吞成 `MemoryUnavailable` 因此本地全绿——**这是假绿风险面，不是「代码已就绪」**。Day-5 必须先重写再接线。
3. **守卫会主动拒绝接线**：`tests/test_feedback_api.py:347` 断言 `get_status` 生产调用者 `== []`、`:310` 静态字面量白名单不含 `worker.py`。接线需按 Day-5 裁定 12 **改作用域并书面记录 re-ruling**，**禁止静默放宽**；白名单不扩（状态映射留在 `agentcore_client.py`/`memory.py`）。
4. **本轮不再是零副作用交付**：会创建真实云资源并产生计费。DoD 口径从「无资源/无费用」改为「精确披露资源清单、区域、预计与真实费用、删除计划」；`AGENTS.md` L69 的预算确认是 `-Apply` 硬门。
5. **环境事实**：本机仍**无 Docker**、WSL 无发行版、`cdk` 未装、`gh` 未装（→ GitHub 仓库只能由用户创建）；`aws-cli` 1.46.1 为 v1（**无 `--cli-dry-run`**）且在当前进程 PATH 不可见 → 编排逻辑走锁内 boto3（实测含 Express 四个操作，**无 Monitor 操作**，需轮询 `DescribeExpressGatewayService`）。
6. **正向事实（降低风险）**：`repo_dynamo` 复用 `memory` extra 已锁定的 `boto3==1.43.102` → **Day-5 不新增依赖、不动 `uv.lock`**；`StateView.storage` 枚举已含 `dynamodb` → 切真实适配器**不需改契约枚举**（路径仍 14 条）。

**必须先落定的高危裁定**（详见计划 §1，共 19 条；承重的 7 条）：①部署编排用 **boto3 声明式编排器**，不引入 CDK/CFN，且 `deploy.ps1` 的 Gate 1/Gate 2 判据必须同步改掉（否则过了假门）；②区域与模型**不预填**，只读探测后由用户确认；③`repo_dynamo` 的原子性等价性基准是 SQLite（`create_or_get_run` 用 TransactWrite[Get+Put]、`record_receipt_once` 用 TransactWrite[Put+Update]、时间统一 ISO8601 字符串）；④真表验证用新 marker `dynamodb_live`，**不引入 moto**；⑤`mode=aws` 启动只做**零计费探活**（DynamoDB/AgentCore），Bedrock 以真实 `request_id` 为证据；⑥`/readyz` 由恒 503 改为按真实探活上调（**LB 与 HEALTHCHECK 仍一律 `/healthz`**，对 Day-4 裁定 7 的书面修订）；⑦副本固定 **1×1**（会话/限速/并发上限均进程内），跨副本不作必过项。

**所有权**（沿用 `AGENTS.md:26-33` 与 Day-2 补裁）：`repo_dynamo.py`(新)/`repo_sqlite.py`/`repository.py`/`auth.py`/`api.py`/`worker.py` = Backend；`agentcore_client.py`/`memory.py`/`bedrock_client.py`/`agent.py` = AI；`models.py`/`config.py`/`contracts/`/`main.py`/`pyproject.toml`/`STATUS`/`TASKBOARD` = Coordinator；`frontend/src/`+`frontend/e2e/` = Frontend；`infra/`/`Dockerfile`/`scripts/*`/`.github/workflows/*` = Infrastructure；**Reviewer 不得由作者充当**（`docs/agents/reviewer.md:10`）。

**不可并行的临界段**：C1=`repository.py`+`repo_sqlite.py`+`repo_dynamo.py`+仓储/恢复测试；C2=`models.py`+`config.py`+`contracts/`+`test_contracts.py`+`conftest.py`；C3=`api.py`+`auth.py`+`test_auth.py`；C4=`agentcore_client.py`+`memory.py`+`worker.py`+`test_feedback_api.py`（**禁止先接线后改守卫**）；C5=`infra/`+`scripts/*`+`Dockerfile`+`workflows/*`（`.gitignore` 的 `infra/deploy_state.json` 必须先于该文件出现）；C6=`frontend/src/*`+`frontend/e2e/*`+`test_frontend_labels.py`；C7=`STATUS`+`TASKBOARD`+`evidence`。**门 0 原则**：路径仍恰 14 条、`domain.schema.json` 仍恰 6 输入模型 + `RunState`；`/api/login` 只增 429 响应，**不得**放宽 `test_contracts.py` 的 `==` 断言。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；OPS、Reviewer 空槽串行复用。单机串行时「并行」= 不重叠文件批次，需按下节格式追加认领记录。新增任务行：`BE-06`、`AI-04`、`FE-05`、`OPS-05`（均 `ready`）；`QA-01` 转 `ready`，`SUBMIT-01` 依赖改指 Day-6。

## 第 5 日完成记录（2026-09-30，离线实现切片）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（逻辑上遵守文件所有权与不重叠写入）。**前提变化**：Day-5 定位为真实部署专日，但实测 **AWS 凭据仍缺失**（事实 G-A：无 `~/.aws/*`、无 `AWS_*` 环境变量、`sts` 报 `Unable to locate credentials`）。经 AskUserQuestion 取得用户裁定「**先做全部离线实现**」，遂完成计划中一切**不需凭据**的代码与离线测试（提交序列 D1–D8 的编码部分），真实云门用 marker 具名 skip。详见 [STATUS](STATUS.md) Day-5 段与 [day5-handoff](evidence/day5-handoff.md)。

- **本地全绿实测**：`verify.ps1` EXIT=0；pytest 默认 addopts **232 passed, 1 skipped, 21 deselected**（收集 live marker 时 **232 passed, 22 skipped**，全具名）；ruff 干净；契约 **14 路径 current**（`domain.schema.json` 仍恰 6 输入模型 + `RunState`）；`uv lock --check` exit 0（**未新增依赖、未动 `uv.lock`**）；e2e **16 passed**；`deploy.ps1 -PlanOnly` EXIT=0（离线 plan、零 AWS 调用）、`cleanup.ps1` `NOT EXECUTED`/exit 2（无 state）。
- **D1（C1）**：`repo_dynamo.py` 实现 `Repository` 全协议（裁定 5 键/原子性；共享 `repo_sqlite` 的确定性 id 与时间戳助手杜绝漂移）+ `dynamodb_live` marker + 离线协议集合守卫；`FeedbackRecord.agentcore_session_id` + `SCHEMA_VERSION` 3→4 幂等迁移 + v3→v4 回归。
- **D2（C2/C3）**：公网三门（默认口令 aws 拒启 / 会话 TTL+idle / 登录限速 429+`Retry-After`）+ `/api/login` 429 契约重生成（路径仍 14）+ `conftest.py` 清理清单 20→24。
- **D3（C4）**：`agentcore_client.py` 按真实 API 重写（`CreateEvent`/`GetEvent`/`RetrieveMemoryRecords`）+ `memory.py` 两段式 `get_status`（`MemoryStatusResult`）+ `_namespace` `/owner/<o>/pet/<p>` + `worker.py` `MemoryPoller` 接线 + **守卫 re-ruling（裁定 12，改作用域非放宽）**：`get_status` 调用者 `== []`→`<= {worker.py}` + AST 钉死 `poll_once`；静态字面量白名单**未扩**（`repo_*`/`worker` 用 `MEMORY_AVAILABLE`/`MEMORY_PROCESSING` 常量）；仓储 `available` 无 ids→`ValueError` 不变式（双实现 + 负向）。
- **D4（C5）**：`.gitignore` **先行**加 `infra/deploy_state.json` + `deploy_plan.json`（9 资源 + 依赖序 + `delete_order`）+ `deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py` + `deploy.ps1`/`cleanup.ps1` 门控判据改写（cdk/CFN→boto3/deploy_plan）+ OIDC/IAM 声明 + 离线守卫（`test_deploy_plan.py` 含**命名模板跨源一致性**、`test_deploy_aws.py` plan 纯函数）。
- **D5（C5）**：`image.yml`（`workflow_dispatch` + OIDC + 单架构 amd64 推 ECR）+ `Dockerfile` 解耦烤死的 `PAWTWIN_MODE`。**镜像未构建**（无 Docker、无 remote）。
- **D6（C2/C3/C6）**：`main.py` **移除** `mode=aws` 拒启 → 真实装配 + 零计费探活（DynamoDB/AgentCore，Bedrock 不探活）+ 探活失败拒启 + `app.state.aws_connected`；`/readyz` 受控修订（探活通过→200，LB 仍 `/healthz`）；`api.py` `storage`/`aws_connected` 真实化；前端证据驱动真实态标签 + `FeedbackView.memory_record_count` + 禁串守卫扩到新常量。
- **D7**：`scenarios.json`（24 例，A01–A14 全覆盖 + 注入/信息不足/失败回执）+ `evaluate.py`（口令只从环境、逐例判定、超时如实记 TIMEOUT、不预填准确率、全 advisory 降级 ERROR 防假绿）+ `test_scenarios.py`。
- **D8（C7）**：`STATUS` Day-5 三档表 + 本地/云端双列 + 命名门禁判定；`evidence/day5-{local,cloud-blocked,handoff}.md`；本完成记录；`reviews/day5.md`（非作者审查）。
- **边界（不拆成半通过）**：真实 DynamoDB 真表、真实 AgentCore 往返、真实 Bedrock、镜像构建、真实 HTTPS/公网三门、CI 远程运行、`-Apply`/`-Destroy`、真机 24 案例、跨副本 A04 **全部未验证**（无凭据/无部署），逐条见 [day5-cloud-blocked](evidence/day5-cloud-blocked.md)。**命名门禁（裁定 19）：G0/D1′/G5–G10 未闭合 → 产物仍为「本地验证候选（非参赛版）」**。
- **提交**：**尚未提交**（工作树 43 项变更；提交需用户明确授权）。**仍无 remote、未推送**；本轮**零 AWS 调用、零云资源、零费用、无镜像构建**。
- **容量冲突上报**：Day-5 字面（材料全套）+ Day-4 顺延的全部云端块 ≈ 28–33h，压不进一日；依裁定⑤**材料整体顺延 Day-6**，五日实际变六个工作日（已在 STATUS/本表留待用户认可）。

## 认领记录格式

每项开始前追加：任务 ID、Agent/任务名称、起始提交、工作树路径、分支、允许写的文件、预计交付、接口变更需求。完成后填写交付提交和验证证据链接。不要让多个 Agent 同时改此表。
