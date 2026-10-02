# Day-5 本地（离线）实现证据 — 2026-09-30

> 本文只记录 **Day-5 离线实现切片** 的命令、结果与「**这不证明什么**」。真实云门（G0/D1′/G5/G6/G7/G9/G10）因**无 AWS 凭据**未执行，逐条见 [day5-cloud-blocked.md](day5-cloud-blocked.md)。诚实红线（AGENTS.md L18/L21/L22）延续：**绝不以替身、离线 stub、SQLite PASS、脚本文本存在或「配置项已设」冒充云端已完成**。

## 0 前提与本轮定位

用户 2026-09-30 裁定「先做全部离线实现」。本轮完成 Day-5 计划中**一切不需凭据的代码与离线测试**（提交序列 D1–D8 的编码部分），真实云测试用 `dynamodb_live`/`bedrock_live`/`agentcore_live` marker 具名 skip，待凭据到位再跑。**双轨策略仍终止**：替身/SQLite/离线 stub 只作离线测试后端，**未**充当任何验收凭据。

**基线**：分支 `chore/bootstrap`，起始 HEAD=`9354804`（Day-4 末，工作树含未提交的 Day-5 规划文档）。**本轮改动尚未提交**（提交需用户明确授权，沿用前四日纪律）。

## 1 命令 / 结果 / 这不证明什么

| 检查 | 命令 | 结果 | 这不证明什么 |
|---|---|---|---|
| G1 基线复跑（改动前） | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q -rs` | **195 passed, 10 skipped**（与计划基线一致，非引用） | — |
| 后端全量（默认 addopts） | `uv run --frozen pytest -p no:cacheprovider` | **232 passed, 1 skipped, 21 deselected** | 不含任何真实云调用；21 deselected = 4 bedrock_live + 5 agentcore_live + 12 dynamodb_live |
| 后端全量（收集 live marker） | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q -rs` | **232 passed, 22 skipped**（22 skip 全具名：5 agentcore_live + 4 bedrock_live + 12 dynamodb_live + 1 restart 尽力项） | 12 个 `dynamodb_live` 全 **skip**（无真表），`repo_dynamo` 行为**未经真表验证** |
| 静态检查 | `uv run --frozen ruff check .` | All checks passed | — |
| 契约一致性 | `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current；**OpenAPI 仍恰 14 条路径**；`domain.schema.json` 仍恰 6 输入模型 + `RunState` | 契约含 `/api/login` 429 与 `FeedbackView.memory_record_count`，均为**生成物**，未手改 |
| 依赖锁 | `uv lock --check` | exit 0（**未新增依赖、未动 `uv.lock`**；`repo_dynamo` 复用 `memory` extra 的 `boto3==1.43.102`） | — |
| 前端类型/构建 | `npm run typecheck` / `npm run build` | 均通过 | 真实态标签只在 aws 态可见，本地 e2e 不触发 |
| 浏览器 e2e | `PAWTWIN_BROWSER_EXECUTABLE=<chromium-1194>` + `npx playwright test` | **16 passed（13.3s）**，禁串断言未放宽 | 本地跑 local_fake + 内存库；**不证明**任何云端行为 |
| 集成 baseline | `./scripts/verify.ps1` | 全绿，**EXIT=0** | — |
| 编排器离线 plan | `./scripts/deploy.ps1 -PlanOnly` | **EXIT=0**，打印「9 resources would be created; MISSING values: …」+「No AWS API was called」 | 这是**离线 plan**（等价 dry-run），**未创建任何资源**；MISSING 项为运行期注入值 |
| 清理门（无 state） | `./scripts/cleanup.ps1` | `NOT EXECUTED`（无 `infra/deploy_state.json`），**退出码 2** | 从未部署，无可清理；ids 绝不臆测 |

## 2 本轮落地的实现（离线可判定部分）

- **D1（C1）`repo_dynamo.py`**：按裁定 5 实现 `Repository` 全协议（单表 `pk/sk` + `entity-index` GSI；`create_or_get_run` 去重靠 `attribute_not_exists`；`record_receipt_once` 用 `TransactWriteItems[Put+Update]` + `CancellationReasons` 判 `inserted`；`claim/renew/release/transition` 条件写；时间统一 ISO8601 字符串，从 `repo_sqlite` 导入 `_dt/_run_uuid/_feedback_uuid` 等**共享**，杜绝漂移）。**离线守卫**：`DynamoRepository` 公开方法集合 ⊇ `Repository` 协议（`tests/test_repo_dynamo.py`）+ 空表名/`available` 无 ids 的 fail-closed（无需凭据即触发）。**12 个真表行为测试全部 `dynamodb_live` 具名 skip**（`tests/test_repo_dynamo_live.py`）。
- **D1（C1）`SCHEMA_VERSION` 3→4**：`FeedbackRecord.agentcore_session_id`（G-G：`GetEvent` 需 `sessionId`）+ `repo_sqlite` 幂等 `ALTER` 迁移 + **v3→v4 回归测试**（预置 v3 文件库 `DROP COLUMN` 后重开→自动加列、`user_version==4`）；原 v2→v3 测试的版本断言精确更新为 `SCHEMA_VERSION`（未放宽）。
- **D2（C2/C3）公网三门**：(a) `mode=aws` 且口令为内置默认或 <12 字符 → `Settings` model_validator **拒启**（本地默认不变）；(b) 会话 TTL + idle 过期（`Session.last_seen_at` 新增，`created_at` **首次获得消费者**）；(c) 登录失败限速 `LoginRateLimiter`（进程内按 IP、指数退避封顶、429 + `Retry-After`）。`/api/login` 契约加 **429**（路径仍 14）。新 4 个 settings 别名补入 `conftest.py` 清理清单（20→24）。**诚实边界**：限速与会话仅进程内，只在单 task 成立（副本 1×1，裁定 15）。
- **D3（C4）AgentCore 真实化 + 轮询接线**：`agentcore_client.py` 按 §2 真实形状重写（`CreateEvent` 会话 payload + `extractionConfig.namespaceVariables`；`GetEvent(memoryId,sessionId,actorId,eventId)`；`RetrieveMemoryRecords(namespacePath,searchCriteria)`；旧 `search_memory`/`list_events(memoryId=…)`/`create_event(namespace=…)` **在真实 API 不存在**，已删）；`memory.py` `get_status` 改**两段式**（先 `GetEvent` 终态、再检索取证，事件成功但检索空 → 保持 `processing`，返回 `MemoryStatusResult(status, record_ids)`）；`_namespace` 改 `/owner/<o>/pet/<p>`；`worker.py` 新增 `MemoryPoller`（复用 `LeaseRenewer` 线程范式，仅 `agentcore`+background 启动，**只传递返回值不写状态字面量**）。**守卫 re-ruling（裁定 12，改作用域非放宽）**：`get_status` 生产调用者断言由 `== []` 改为 `<= {"worker.py"}` + **AST 双层守卫**钉死调用只在 `MemoryPoller.poll_once` 内；**静态字面量白名单未扩**（`repo_*`/`worker` 用 `models.MEMORY_AVAILABLE`/`MEMORY_PROCESSING` 常量，`offenders == []` 仍真）；仓储层新增 `available` 无 ids → `ValueError` 不变式（含 SQLite/Dynamo 双实现 + 负向测试）。
- **D4（C5）编排器**：`.gitignore` **先行**加 `infra/deploy_state.json`（裁定 2）；`infra/deploy_plan.json`（9 资源声明 + 依赖序 + `delete_order`）；`scripts/deploy_aws.py`（离线 `plan` 纯函数 + 门控 `apply`）、`cleanup_aws.py`（逆依赖删除 + 读回）、`aws_probe.py`（只读零计费）；`deploy.ps1`/`cleanup.ps1` 门控判据由「cdk/CFN 模板」改为「boto3/deploy_plan.json」，`-PlanOnly` 现为**真实离线 plan**、`-Apply`/`-Destroy` 委派编排器（缺前提仍 `NOT EXECUTED`/exit 2）。**离线守卫**：`tests/test_deploy_plan.py`（单表键schema/GSI、**命名模板与 `_namespace()` 跨源一致性**、`/healthz`、1×1、删除序、无硬编码区域/账号）+ `tests/test_deploy_aws.py`（拓扑序、占位符解析、plan 不触 AWS）。
- **D5（C5）镜像/CI**：`Dockerfile` **解耦**烤死的 `PAWTWIN_MODE`（改由运行环境注入）；`.github/workflows/image.yml`（仅 `workflow_dispatch`、OIDC `id-token: write`、单架构 `linux/amd64`、推 `pawtwin:<sha>`+`latest`、报 digest）。**镜像未构建**（本机无 Docker，且无 GitHub remote → workflow 从未运行）。
- **D6（C2/C3/C6）云装配 + 前端**：`main.py` **移除** `mode=aws` 拒启，改真实装配（`DynamoRepository` + `AgentCoreMemory` + bedrock）+ **只读零计费探活**（DynamoDB `GetItem` + AgentCore `GetMemory`；**Bedrock 不探活**，其证据只能是真实 `request_id`）+ 探活失败**拒启**（`app.state.aws_connected` 真实标志）；`/readyz` 由恒 503 改为**探活通过→200 `{status:ready}`**（LB/HEALTHCHECK 仍 `/healthz`，裁定 9）；`api.py` `storage` 标签由硬编码 `"sqlite"` 改为按适配器真实给出、`aws_connected` 读 `app.state`。前端 `App.tsx` 真实态标签**证据驱动**（`storage=dynamodb`+`aws_connected`、`已提炼（真实 AgentCore 记录 N 条）` 仅当 `memory_record_count>0`），`FeedbackView` 加非秘密 `memory_record_count`；`test_frontend_labels.py` 禁串守卫**扩到新常量** `MEMORY_EXTRACTED_LABEL` + 新增「提炼标签必须与 `memory_record_count` 配对渲染」守卫。
- **D7**：`tests/cases/scenarios.json`（**24 例**，覆盖 A01–A14 + 注入/信息不足/失败回执/限速/默认口令拒启）+ `scripts/evaluate.py`（`--base-url` 指已部署 HTTPS、口令**只从环境变量**读、逐例输出 输入/期望/实际/`request_id`/耗时/判定 + 总通过率、记忆案例轮询 ≤180s 超时**如实记 TIMEOUT**、**不预填准确率**、全advisory 案例降级为 ERROR 防假绿）+ `tests/test_scenarios.py`（离线校验 24 例/唯一 id/A01–A14 覆盖/**无预填指标**）。

## 3 明确未做 / 未验证（不拆成半通过）

- **真实云全链路未执行**：G0 只读探测、D1′ 真表 `dynamodb_live`、G5 真实 AgentCore 往返、G6 CI 真实构建推 ECR、G7 `apply` + HTTPS、G8 部署面 A01–A14、G9 真机 24 案例、G10 `cleanup -Destroy` 读回——**全部因无凭据未执行**，逐条见 [day5-cloud-blocked.md](day5-cloud-blocked.md)。
- **`repo_dynamo` 未经真表验证**：其事务/条件语义等价性（vs SQLite 锁）**只有真表能证**；离线仅证「方法集合 ⊇ 协议」+ 无需凭据的 fail-closed 分支。
- **AgentCore 响应字段名/状态词表未验证**：`GetEvent`/`RetrieveMemoryRecords` 的**响应**形状与状态 VALUE 无账号无法核实，解析用 `_field` 防御式容错、未知状态一律 `processing`（不上调终态）。
- **镜像未构建、workflow 未运行、无 remote、未推送、未提交**。
- **参赛材料**（英文提交/录屏/概念图/三态表/架构文档）按裁定⑤**整体顺延 Day-6**，本轮不含。

## 4 副作用口径

本轮**零 AWS 调用、零云资源、零费用**（`deploy.ps1 -PlanOnly` 为离线 plan；`apply` 未执行）。`deploy_aws.py --plan` 与 `aws_probe.py` 均设计为不在无凭据时发起计费调用。改动**尚未提交**（43 项工作树变更），提交分组与授权待用户确认。
