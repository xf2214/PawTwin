# PawTwin 第五日（Day-5）开发计划

> 本文是 [五日开发总方案](PawTwin_五日开发总方案.md) 第 6 节「第 5 日」与 [实施任务单](PawTwin_Agent_实施任务单.md) **T8**（参赛材料）+ **T6 遗留的 24 案例集** + **T7 顺延的全部云端块**的当日可执行分解；承接 [Day-4 开发计划](PawTwin_Day4_开发计划.md) 与 [Day-4 完成记录](../STATUS.md)。
> 编制日期：2026-09-30。**基线**：分支 `chore/bootstrap`，HEAD=`9354804`，工作树干净（实测 `git status --porcelain -uall` 为空），**无 git remote**；实测 pytest **195 passed, 10 skipped**（默认 addopts 下 192/1/9 deselected）、e2e **16 passed**、契约 **14 条路径 current**、`verify.ps1` EXIT=0。本文所有行号引用均以当前工作区文件为准，且全部由规划阶段回源码/命令核实。
> Day-5 与 Day-2/3/4 的根本差别：**双轨策略终止**。账号就绪后真实 Bedrock / 真实 DynamoDB / 真实 AgentCore 即为唯一交付证据，替身（`local_fake`、`StubMemoryService`、SQLite）只保留为离线测试后端，不得再充当任何一日的验收凭据。

## 0 前提、实测事实与当日验收（三档）

**前提（用户 2026-09-30 确认六点）**：①**AWS 账号与凭据已就绪**，由用户在本机注入短期凭据（可立即执行真实调用）；②**镜像构建走 GitHub Actions 远程构建并推送 ECR**，CI 取云权限用 **OIDC 角色**（不放长期密钥）；③**部署深度 = 完整真实部署**：实现 `repo_dynamo` → 移除 `mode=aws` 拒启 → 真实 Bedrock + 真实 AgentCore → ECS Express Mode 的 HTTPS 演示地址；④**T6 的 24 案例集 + `evaluate.py` 补做，并在真实模型上跑**；⑤**Day-5 专做真实部署，参赛材料整体顺延 Day-6**；⑥**公网安全三门全做**（默认口令拒启、会话 TTL、登录限速）。

诚实红线延续：`AGENTS.md` L18/L21/L22/L53/L69/L71 与总方案 L39/L69/L106/L138/L153 —— **绝不以替身、离线 stub、SQLite PASS、脚本文本存在或「配置项已设」冒充云端已完成**；未验证项一律具名分列；凭据绝不入聊天/仓库/镜像层/日志；无 remote 与未推送是事实；**资源创建前必须取得用户对具体预算与运行期限的书面确认**。

### 0.1 规划阶段实测事实（Day-5 判据的地基）

| # | 事实 | 证据 |
|---|---|---|
| G-A | **凭据仍缺失**：`aws sts get-caller-identity` → `Unable to locate credentials`；`$HOME\.aws\credentials` 与 `config` 均不存在；无 `AWS_*` 凭据环境变量 | 主控实测（用户已声明即将注入，故 G0 门的第一项就是它） |
| G-B | 本机**无 Docker**（`C:\Program Files\Docker` 不存在）、**WSL 无任何发行版**、`cdk` 未安装、`gh` CLI 不存在 → **GitHub 仓库只能由用户创建** | 实测 `Test-Path` / `Get-Command` / `wsl -l -v` |
| G-C | `aws` 在**当前进程 PATH 中不可见**（用户 PATH 实测已含 `%APPDATA%\Python\Python313\Scripts`，但 IDE/会话进程未刷新）；`aws.cmd` 全路径可用但伴随无害的「没有为扩展名 .py 找到文件关联」告警；**`--cli-dry-run` 不被支持**（aws-cli 1.46.1，属 v2 专属） | 实测；后果见裁定 17 |
| G-D | 项目 venv 内 **boto3 / botocore 1.43.102 实测含** `CreateExpressGatewayService` / `Update…` / `Delete…` / `Describe…`，**不存在 Monitor 类操作**；`bedrock-agentcore`（67 个操作）与 `bedrock-agentcore-control`（170 个操作）均可解析，`us-west-2` 端点可构造 | 内省 `client.meta.service_model.operation_names` |
| G-E | 真实数据面形状：`CreateEvent` 必填 `memoryId` + `actorId` + `eventTimestamp` + `payload`（`list[结构]`，会话项为 `conversational.content.text` + `role`），**入参里没有 `namespace`**；`GetEvent` 必填 `memoryId` + `sessionId` + `actorId` + `eventId`；检索操作是 `RetrieveMemoryRecords(memoryId, namespace?, namespacePath?, searchCriteria.searchQuery)`；`bedrock-agentcore` 里**没有 `search_memory` 这个操作** | 内省各操作 `input_shape` |
| G-F | 现 `agentcore_client.py:128` 调 `create_event(**request)`（request 含 `namespace`，见 `:117-124`）、`:144` 调 `list_events(memoryId=…)`、`:164` 调 `search_memory(…)` → **接真实账号必然报错**；当前错误被 fail-closed 归约为 `MemoryUnavailable`，因此本地测试全绿——这是一个**已知的假绿风险面**，不是「代码已就绪」 | G-E + 源码原文 |
| G-G | `GetEvent` 需要 `sessionId`，但 `FeedbackRecord` 只持久化 `agentcore_event_id`（`repository.py:105-127`）→ 轮询无法定位事件，**必须补一个内部字段并做 SQLite 迁移** | 源码 |
| G-H | ECS Express Mode 官方：`aws ecs create-express-gateway-service` 创建后自动提供 `https://<service-name>.ecs.<region>.on.aws` 与 **SSL/TLS 终结**、跨 AZ 负载均衡、`--health-check-path` 可指定、`--primary-container` 支持 `containerPort`/`environment`、`--scaling-target` 可设 min/max；需 `ecsTaskExecutionRole`（`AmazonECSTaskExecutionRolePolicy`）与 `ecsInfrastructureRoleForExpressServices`（`AmazonECSInfrastructureRoleforExpressGatewayServices`）两个角色；**默认使用账号默认 VPC 的公有子网**；新建角色有最终一致性，首次 create 可能因无法 assume 角色而失败，需等待重试 | AWS 官方文档实取（本计划编制当日） |
| G-I | AgentCore Memory 官方：**只有 memory strategy 状态进入 `ACTIVE` 之后创建的 event 才会被提炼**（在此之前存的对话永远不会被纳入）；提炼为**异步**，「may take a minute or more」；检索用 `retrieve_memory_records` + 策略定义的 `namespace` | 官方文档实取 |
| G-J | 云装配仍被硬拒：`main.py:81-82` 对 `mode == "aws"` 无条件 `raise NotImplementedError`；`config.py:186-195` `aws_connected` **恒 False**；`api.py:239` 的 `storage="sqlite"` 是**硬编码字面量**；但 `models.py` 的 `StateView.storage` 已是 `Literal["sqlite", "dynamodb"]` → **切真实适配器不需要改契约枚举** | 源码 |
| G-K | 反伪造守卫会在接线当天主动拒绝改动：`tests/test_feedback_api.py:347` 断言 `get_status` 的生产调用者 `== []`；`:310` 静态字面量白名单为 `{models.py, memory.py, agentcore_client.py}`；`:327-332` 断言 `offenders == []`，其 docstring 自述「新增写入点必须显式 re-ruling」并声明只守**字面量**、传播路径靠行为守卫 | 源码 |
| G-L | 公网三门实测零实现：`api.py:199-201` 的 `/api/login` 只声明 `responses=_responses(401, 422)`（**无 429**）；`auth.py` 无限速、无 TTL（`Session.created_at` 在 `auth.py:41` 赋值后无任何读取）；默认口令 `local-demo-passphrase` 写死在 `config.py:36-39` 的默认值里 | 源码 |
| G-M | 测试基础设施的强耦合点：`tests/conftest.py:18-39` 的环境清理清单实测**恰 20 项**（新增任何 settings 别名不补进去就会让开发者 shell 的值得以泄漏、失败不可复现）；`pyproject.toml:56` `addopts = "-q -m 'not bedrock_live and not agentcore_live'"`，markers 在 `:57-62` | 实测 + 源码 |
| G-N | `tests/test_app.py` 对 `/readyz` 是**全等字典断言**（`:17` 状态码 503、`:18-26` 八字段全等、`:23` `"storage": "sqlite_local"`），对 `/api/bootstrap` 同样全等（`:39-53`，`:51` `"long_term_memory": "not_implemented"`）→ 上调必须**精确更新而非放宽**，否则「低报失真」与「假绿」同罪 | 源码 |
| G-O | `Dockerfile:12-17` 把 `PAWTWIN_MODE=local` **烤进镜像 ENV**（这正是 Day-4 cookie `Secure` 判据在部署形态下永假的根因）；`ci.yml:33` 是 `uv sync --frozen`（不装 extra），与镜像的 `--extra bedrock --extra memory` 两个依赖闭包互不覆盖 | 源码 |
| G-P | 无 git remote → CI 从未在远端跑过；`.gitignore` 已含 `*.db`（S0-a 入库）；全仓凭据 grep 0 命中；`frontend/e2e/helpers.ts:7` 的演示口令回退为 `local-demo-passphrase`（仅本地） | 实测 + 源码 |
| G-Q | 依赖侧零风险事实：**boto3 已在锁内**（`pyproject.toml:37-39` 的 `memory` extra 即 `boto3==1.43.102`，且本为 `strands-agents` 传递依赖）→ `repo_dynamo` 复用同一 extra 即可，**Day-5 不需要新增任何依赖、不动 `uv.lock`** | `pyproject.toml:29-39` + 实测 `uv sync` |

### 0.2 当日验收（三档）

| 档位 | 内容 |
|---|---|
| **必过 Gate** | **G0** 只读云就绪门（短期凭据注入、caller identity、区域可达、Bedrock 模型访问核查；**零计费**，产出 `docs/evidence/day5-cloud-probe.md`）；**G1** 改动前后本地全量回归**重新实测**（禁引用 Day-4 的 195/10/16）；**G2** `repo_dynamo` 在**真实表**上跑通全套语义（去重、CAS、并发双批准恰一次执行与一次记账、租约白名单穷举、幂等记账、`UNSET`/NULL 语义、`facts_version` 原子自增）；**G3** 云装配与真实标签（`mode=aws` 可启动、`aws_connected`/`readyz`/`state.storage`/`bootstrap.stage` 按真实判据**精确更新**）；**G4** 公网三门 + `/api/login` 429 契约重生成（**OpenAPI 仍恰 14 条路径**）；**G5** AgentCore 数据面按真实 API 重写 + 接线，并在真实账号完成 `CreateMemory`→strategy `ACTIVE`→提交→轮询→**真实 record id 检索** 的完整往返；**G6** GitHub Actions **真实构建并推送镜像到 ECR**（本仓库镜像首次真正构建，记 digest/尺寸/扫描状态）；**G7** 真实 plan + 费用实测 + 用户书面确认 + `-Apply` → `https://<svc>.ecs.<region>.on.aws` 可访问、`/healthz` 生效；**G8** 部署面 A01–A14 真实子集（见 §6）；**G9** 24 案例集在**真实模型**上跑完并如实出报告；**G10** `cleanup.ps1` 真实现 dry-run→按依赖删除→**读回零残留**；**G11** 非作者独立审查 + 证据四件套 |
| **尽力项** | Express 容器 `secrets` 接管口令（替代明文 env）、ECR 镜像漏洞扫描、CloudWatch 指标/告警看板、arm64（Graviton）成本对比、真实制造双 task 以验证跨副本 A04、`--cli-dry-run` 缺失下的编排器参数级 dry-run 单测、`aws ce get-cost-and-usage` 每日核查脚本化 |
| **条件项** | 跨副本会话持久化（会话仍进程内）、App Runner 对比、真实传感器/设备、Alexa+、赛事官方规则与截止核查（**用户仍未提供官方链接**）、ACM 自定义域名（Express 已给托管 HTTPS，不需要） |

**明确不写进 Day-5 承诺（显式顺延 Day-6 或路线图）**：英文提交材料与三分钟录屏、PawLink 佩戴概念图、已实现/模拟/路线图三态表、架构说明文档（→ Day-6）；跨副本会话表与数据库级全站并发计数（→ 真需要多副本时）；`/readyz` 之外的健康探针体系；成本硬上限自动关停（AWS 无此能力，只能提醒 + 人工核查）。

## 1 技术裁定（前置须落定；每条已回源码或命令核实）

| # | 议题 | 裁定 | 依据 |
|---|---|---|---|
| 1 | **部署编排 = boto3 声明式编排器，不引入 CDK/CloudFormation** | 新增 `infra/deploy_plan.json`（逻辑资源清单：名称、类型、参数、依赖序）+ `scripts/deploy_aws.py`（按声明逐项创建，把实际 ARN/ID 写入 `infra/deploy_state.json`）+ `scripts/cleanup_aws.py`（按 state 逆依赖删除并读回验证）。`scripts/deploy.ps1`/`cleanup.ps1` **保留 fail-closed 门控形态**并改为调用编排器；**Gate 1 的 `cdk` 探测改为 boto3 能力探测，Gate 2 的判据从「`infra/cdk.json` 或 `infra/templates/*.template.json`」改为「`infra/deploy_plan.json` 存在且 schema 校验通过」**——不改则过了假门，属语义失真 | G-B（无 cdk）、G-D（Express 与 AgentCore 操作已在锁内 boto3）；CFN 是否支持 `AWS::ECS::ExpressGatewayService`/`AWS::BedrockAgentCore::Memory` **未核实，不为凑部署预填假设**；现门控见 `scripts/deploy.ps1:59-71` |
| 2 | **生成物/状态文件的忽略规则先行** | `.gitignore` 追加 `infra/deploy_state.json` 必须**与编排器首次落盘同批且在前**（Day-4 的 S0-a 教训：忽略规则留在未提交改动里，单独 checkout 跑测试即弄脏工作区）。`docs/evidence/*.md` 相反——**必须入库**，它是验收凭据 | Day-4 裁定 3；G-P |
| 3 | **区域与模型不预填** | 新增 `scripts/aws_probe.py`（只读、零计费）实报：caller identity 与账号 id、目标区域的 `bedrock-agentcore-control.list_memories` 可达性、`bedrock.list-foundation-models` 返回的账号内**已授权**模型清单。选模只写判据（支持工具调用 + 结构化输出 + 账号已授权 + 单价低者优先），**模型 ID / 区域由用户从候选中确认，只进 `.env`，绝不写入仓库**；`BEDROCK_MODEL_ID`/`AWS_REGION` 的实际值在证据文件里可以出现（非秘密），口令与凭据不可 | G-A、G-D；`config.py:128-175` 的交叉校验已就位 |
| 4 | **公网安全三门全做，且都是启动/契约级硬门** | (a) `mode=aws` 且 `demo_passphrase` 等于内置默认值或短于 12 字符 → `Settings` 校验**直接抛错拒启**（新增 model_validator，不改默认值本身，本地仍可用）；(b) 会话 TTL + 闲置过期：`Session` 增 `last_seen_at`，`get_session` 消费 `created_at`/`last_seen_at` 并过期即删（返回 None → 401），新增 `PAWTWIN_SESSION_TTL_SECONDS`（默认 28800）与 `PAWTWIN_SESSION_IDLE_SECONDS`（默认 1800）；(c) 登录失败限速：进程内按 IP 计失败次数，超阈值返回 **429 `RATE_LIMITED`** + `Retry-After`，指数退避封顶，新增 `PAWTWIN_LOGIN_MAX_FAILURES`（默认 5）/`PAWTWIN_LOGIN_BACKOFF_SECONDS`（默认 60）。**后果清单**：新 settings 别名必须补入 `conftest.py` 清理清单；`/api/login` 的 `responses` 加 429 后重生成契约（**路径数仍 14**，`domain.schema.json` 不变）；诚实边界写明限速与会话**仅进程内**、只在单 task 下成立 | G-L、G-M、G-N；Day-4 裁定 14 把三者列为公网前置硬门，用户本轮选择「全做」 |
| 5 | **`repo_dynamo` 的键与原子性设计（决策完备，照此实现）** | 单表：`pk`(HASH)+`sk`(RANGE)；items —— run `pk="run#<run_id>", sk="R"`；facts `pk="facts#<owner>", sk="F"`；receipt `pk="receipt#<command_id>", sk="C"`；feedback `pk="feedback#<feedback_id>", sk="B"`。一个 GSI `entity-index`：`gpk/sk` —— runs 用 `("owner#<owner>", created_at)`，receipts 用 `("run#<run_id>", created_at)`。`PAY_PER_REQUEST`，全表 `project=pawtwin` 标签，**不建 PITR、不建备份计划**（演示期数据可弃，须在文档写明）。语义映射：`create_or_get_run` = **TransactWrite[Get(facts), Put(run, ConditionExpression: attribute_not_exists(pk))]**（保持与 SQLite「同一锁内读 `facts_version` 再插入」等价），冲突即 `GetItem` 回既有；`record_receipt_once` = **TransactWrite[Put(receipt, attribute_not_exists), Update(facts: ADD daily_dispensed_grams :g, SET last_fed_minutes_ago=0, facts_version = facts_version + :one)]**，用 `TransactionCanceledException` 的 `CancellationReasons` 判 `inserted`（条件失败 → False，**且不得记账**）；`claim_run`/`transition_run`/`renew_lease` = 条件写（谓词逐条照抄 `repo_sqlite.py:333-392` 的白名单 + 租约 + `attempt_count < :max`）；`release_run` 条件失败静默（与 SQLite `rowcount!=1` 等价）；`set_feedback_status` = 条件 `attribute_exists(pk)`，参数为 None 的列**不出现在 UpdateExpression**（等价 `COALESCE`）；`update_facts` 的 `UNSET` 不进表达式、`None` 显式写 DynamoDB NULL。时间统一 **ISO8601 UTC 字符串**（条件表达式按字典序比较即时间序，混用类型会让条件永假）；数字用 DynamoDB number（读写经 `Decimal` 转换） | G-Q、`repo_sqlite.py:232-586`；SQLite 侧的事务/锁语义是等价性基准 |
| 6 | **DynamoDB 验证只能在真表上做** | 新增 marker `dynamodb_live`（注册进 `pyproject.toml:57-62` 并加入 `:56` 的默认 deselect 表达式）；测试表用独立名（`PAWTWIN_DYNAMODB_TABLE_NAME` 注入）+ 用例自复位事实。**不引入 moto / 任何 mock**：离线侧只保留「`DynamoRepository` 的公开方法集合 ⊇ `Repository` 协议方法集合」的静态守卫（防漏实现，且明确声明「这**不是**云证据」）。SQLite/两连接的 PASS **一律不计入**云面通过 | 总方案 L106、`docs/agents/*`；记忆体例「DynamoDB 云测不可用 SQLite PASS 替代」 |
| 7 | **移除 `mode=aws` 拒启的硬门与探活方式** | `main.py:81-82` 的 raise 改为按 settings 装配：`mode=aws` → `DynamoRepository` + `build_memory` 走 `agentcore` + `model_backend=bedrock`。启动时做**只读、零计费探活**：DynamoDB `GetItem` 固定 meta 项、AgentCore `GetMemory`；**Bedrock 不在启动探活**（`Converse`/`InvokeModel` 一律计费），其连通证据只能是首次真实分析返回的 `request_id`。探活失败 → **拒启并打印真实原因**，绝不回退替身（AGENTS.md L22） | G-J、G-D、`config.py:159-174` 已要求 aws 模式四个必填 |
| 8 | **`aws_connected` 与标签改为真实判据** | `config.py:186-195` 的恒 False 改为「由 `create_app` 在三项探活结果上写入的真实标志」（Settings 本身不做 IO，故标志位放 app.state，`api.py:237` 读它）；`api.py:239` 的 `"sqlite"` 字面量改为按实际仓储适配器类型给出；`bootstrap.stage` 与 `/readyz` 的 `storage`/`cloud` 字段同步真实化。**`models.py` 无需改**（`StateView.storage` 已含 `dynamodb`），故契约路径数与 domain schema 不变 | G-J、G-N |
| 9 | **`/readyz` 语义受控修订（对 Day-4 裁定 7 的书面更正）** | LB/target group 与容器 `HEALTHCHECK` **仍一律 `/healthz`，一字不改**；`/readyz` 由「无条件 503」改为「storage+memory 探活成功且 model_backend=bedrock → 200 `{status:"ready"}`，否则维持原 503 全字段」。理由：真实连通后长期 503 是**低报失真**，与高报同罪；裁定 7 的原意（不得为让部署走完而改码撒谎、严禁 LB 指 `/readyz`）完整保留。`tests/test_app.py:17-26` 的 local 断言**逐字保持不破**，另新增 aws 分支测试（用显式注入的探活结果，注释钉死「这是映射逻辑测试，不是云证据」）+ 部署后用真实 curl 结果作证据 | Day-4 裁定 7 与 `docs/agents/infrastructure.md:29`；G-H、G-N |
| 10 | **AgentCore 数据面按真实形状重写** | `agentcore_client.py` 改为：`create_event(memoryId, actorId=<owner_id>, sessionId=<conversation_id>, eventTimestamp=<datetime>, payload=[{"conversational": {"content": {"text": <原文>}, "role": "USER"}}])` → 取 `event.eventId`；`event_status` 改为 `get_event(memoryId, sessionId, actorId, eventId)`（**因此必须持久化 sessionId**）；`retrieve` 改为 `retrieve_memory_records(memoryId, namespacePath=<本资源命名>, searchCriteria={"searchQuery": q, "topK": 5})`。`memory.py:_namespace` 现返回 `owner_id/pet_id`（无 `/` 前缀）→ 统一为 `/owner/<owner>/pet/<pet>`，并与 `CreateMemory` 的 `namespaceTemplates` 严格配对，新增**跨源一致性守卫测试**（`deploy_plan.json` 里的模板串与 `_namespace()` 输出必须可互证，防漂移）。`FeedbackRecord` 增 `agentcore_session_id`；`repo_sqlite` 的 `SCHEMA_VERSION` 3→4 + 幂等加列 + **v3→v4 迁移回归测试**（预置 v3 文件库重开）；`set_feedback_status` 签名扩展为可传 `agentcore_session_id` | G-E、G-F、G-G；真实字段名以 §2 内省结果为准 |
| 11 | **`available` 只能由真实记录支撑** | 轮询实现为两段：先 `get_event` 判终态，**成功后再 `retrieve_memory_records`**，只有拿到真实 `recordId` 列表才返回 `available` 并把 ids 交回上层；事件成功但检索为空 → 保持 `processing`（不猜）。仓储层新增不变式：`set_feedback_status(memory_status="available")` 且 `memory_record_ids` 为空 → **抛 `ValueError`**（fail-closed，防未来接线者手滑），附回退负向测试 | `AGENTS.md:18`；G-K |
| 12 | **守卫 re-ruling：改作用域，不放宽** | `get_status` 零调用者断言（`:347`）从 `callers == []` 改为 `callers <= {"worker.py"}` **且**要求该调用只出现在记忆轮询函数体内（AST/正则双层守卫），测试注释写明「Day-5 裁定 12 授权接线；这不代表云端已验证」。静态字面量白名单 `:310` **不扩**——状态映射全部留在 `agentcore_client.py`/`memory.py` 内，`worker.py` 只传递返回值不写字面量，因此 `:327-332` 的 `offenders == []` 必须继续为真。`:238-256` 的行为守卫作用域本就是 local 配置（`conftest.py` `_local_settings()`），**保持原样全绿**即为回归通过 | G-K；该测试 docstring 自述扩白名单需显式 re-ruling |
| 13 | **提炼前置手顺不可颠倒** | `CreateMemory`（带 long-term strategy）→ 轮询 `GetMemory` 直到 strategy `status == "ACTIVE"` → 才允许提交反馈；编排器与 `evaluate.py` 都实现为显式等待步骤，等待失败即记真实失败。ACTIVE 之前提交的 event **永远不会被提炼**，因此「先建库、后启用、再提交」写进部署文档与验收证据 | G-I；违反它会让 G5 的 `available` 永远拿不到，而以替身补位即破红线 |
| 14 | **镜像与 CI：Actions 构建推 ECR，OIDC 取权限** | `Dockerfile` 移除 `:12-17` 中烤死的 `PAWTWIN_MODE`（改由服务环境注入），其余两 extra 不动。新增 `.github/workflows/image.yml`：仅 `workflow_dispatch`（手动触发，避免每次 push 产生 ECR 存储与 CI 分钟），`permissions: {id-token: write, contents: read}`，用 `aws-actions/configure-aws-credentials` 换 OIDC 短期凭据 + `docker/setup-buildx-action` + `docker/build-push-action` **单架构 linux/amd64**（不启用 QEMU 模拟；Graviton/arm64 成本优化明确不做并记为路线图），推 `pawtwin:<git-sha>` 与 `latest`。**部署与清理不进 CI**。口令注入首选 Express `primary-container.environment`（AWS 内可见、不入仓库、不下发浏览器）；实测若支持容器 `secrets` 则改 Secrets Manager，不支持即如实记为路线图 | G-B、G-O；用户已选「Actions 远程构建 + OIDC」 |
| 15 | **副本固定 1×1** | `create-express-gateway-service` 显式 `--scaling-target {minTaskCount:1,maxTaskCount:1}`、`--health-check-path "/healthz"`、`containerPort 8080`、`--cpu 1 --memory 2`（实际生效值以真实响应为准记录，不猜）。原因写进文档：会话、登录限速与并发上限均为**进程内**（G-L、`worker.py:6-9`），多副本会让 A04 的全站上限变成「副本数 × 2」并把评委会话打成 401。**跨副本验证因此不在 Day-5 必过项内**，不得声称已验证 | G-H、G-L；总方案 L71 只要求「默认一个副本 + 滚动时数据库条件写」 |
| 16 | **费用门是 apply 前的硬停** | `infra/cost-estimate.md` 用 AWS Price List API（`pricing.get-products`/`get-attribute-values`，只读免费）实拉：Fargate vCPU-GB、ALB LCU + 公网 IP、ECR 存储、DynamoDB 请求/存储、CloudWatch Logs 摄取/保留、**选定 Bedrock 模型的输入/输出 token 单价**、AgentCore Memory。**任一项拉不到就写「未取得，需控制台核实」，禁止预填金额**。产出「每小时 + 演示期总额」后，**必须取得用户对预算上限与运行期限的书面确认**才允许 `-Apply`（AGENTS.md L69）。运行期每日 `aws ce get-cost-and-usage` 只读核查并写入 evidence；**不得**写「预算硬上限/自动停费」 | 总方案 L146；G-B（无本地 docker/CDK 时 apply 只能一次成功，费用门更关键） |
| 17 | **CLI 与编排器的分工** | 因 aws-cli 1.46.1 是 v1（G-C：无 `--cli-dry-run`、`.py` 关联告警、进程 PATH 未刷新），**所有编排逻辑走 boto3**，CLI 只留作人工诊断；「plan」= 编排器在**不发送任何请求**的前提下打印将创建的资源清单与参数（等价 dry-run），并单测其参数校验分支。`preflight.ps1` 增加 boto3 能力探测段（实测 express/agentcore 操作是否存在），并保留「无凭据仍以 0 退出但逐段 `NOT EXECUTED`」的既有语义分级 | G-C、G-D；Day-4 裁定 8 的退出码语义分级不变 |
| 18 | **24 案例集打真实部署，且允许真实失败** | `tests/cases/scenarios.json`（24 例，覆盖 A01–A14 与注入/信息不足/失败回执）+ `scripts/evaluate.py`：`--base-url` 指向**已部署的 HTTPS**，口令只从环境变量读，绝不落文件/日志/仓库；逐例输出「输入 / 期望工作流结论 / 实际结果 / `request_id` / 耗时 / 判定」与总通过率；记忆类案例受 G-I 异步时效约束，轮询预算 ≤180s，超时**如实记 FAIL/TIMEOUT**，不得改判为「本地通过」。报告只证**工作流与建议一致性**，**禁止预填准确率**，不得解读为宠物意图准确率（总方案 L138） | 用户已选「补做并在真实模型上跑」；G-P |
| 19 | **交付命名门禁反转条件** | G0–G11 全部有实测证据 → 产物可写作「**AWS 已验证（Bedrock / DynamoDB / AgentCore / ECS Express HTTPS）**」并在 `STATUS.md` 逐项链接证据文件；任一项未闭合 → 继续用「**本地验证候选（非参赛版）**」并逐条具名上报。Day-6 材料依此命名 | 总方案 L153；Day-4 裁定与 `day4-cloud-blocked.md` 体例 |

## 2 真实 API 形状（规划阶段内省所得，实现时照此，不得凭记忆）

```
CreateEvent(memoryId*, actorId*, eventTimestamp*, payload*=[{conversational:{content:{text}, role*}} | {blob} | {json:{content*}}],
            sessionId, branch, clientToken, metadata, extractionMode, extractionConfig.namespaceVariables)
GetEvent(memoryId*, sessionId*, actorId*, eventId*)                    # ← 因此 sessionId 必须持久化（G-G）
ListEvents(memoryId*, sessionId*, actorId*, includePayloads, filter, maxResults, nextToken)
RetrieveMemoryRecords(memoryId*, namespace | namespacePath, searchCriteria*={searchQuery*, memoryStrategyId, topK, metadataFilters})
CreateMemory(name*, eventExpiryDuration*, description, encryptionKeyArn, memoryExecutionRoleArn,
             memoryStrategies=[{semanticMemoryStrategy|summaryMemoryStrategy|userPreferenceMemoryStrategy|
                                 episodicMemoryStrategy|customMemoryStrategy: {name*, namespaces, namespaceTemplates, memoryRecordSchema}}],
             indexedKeys, namespaceKeys, streamDeliveryResources, tags)
CreateExpressGatewayService(infrastructureRoleArn*, executionRoleArn, taskRoleArn, primaryContainer{image,containerPort,environment,...},
             serviceName, cpu, memory, cpuArchitecture, healthCheckPath, scalingTarget{minTaskCount,maxTaskCount}, subnets, …)
```
`bedrock-agentcore` 无 `SearchMemory`；`ecs` 无 `MonitorExpressGatewayService`（**轮询 `DescribeExpressGatewayService` 直到 `statusCode == ACTIVE`**）。boto3 服务名：`bedrock-agentcore`（数据面）、`bedrock-agentcore-control`（建 memory）、`bedrock-runtime`（`Converse`/`InvokeModel`）。

## 3 前置串行段 P0（就绪门，需用户在场；全部只读）

- [ ] 用户在 GitHub 建**私有**仓库并给出 `owner/repo`，明确授权推送范围（G-B：本机无 `gh`，我无法建库）。
- [ ] 用户在本机注入**短期**凭据（`aws configure sso` 或临时会话密钥）；我只验证 `sts.get-caller-identity` 结果，**不索要、不读取、不转写**任何密钥值。
- [ ] `./scripts/preflight.ps1` → 凭据源应显示存在；确认 `aws` 在脚本可见（必要时开新终端或按裁定 17 走 boto3）。
- [ ] `uv run --frozen --extra bedrock --extra memory python scripts/aws_probe.py` → 出 `docs/evidence/day5-cloud-probe.md`：账号 id、区域、`list_memories` 可达、可访问模型清单；**零计费**。
- [ ] 用户从候选中确认 **Bedrock 模型 ID 与区域**；如需控制台开通模型访问/同意条款，由用户完成（G-B/裁定 3）。
- [ ] `infra/cost-estimate.md` 实测单价 → 用户书面确认**预算上限与运行期限**（G7 前置，未确认不 apply）。
- [ ] G1 基线复跑（干净树，pytest/ruff/契约/lock/e2e/verify 全绿）作为 Day-5 的对照数字。

## 4 并行实现（受 P0 与临界段约束）

### 4.1 Backend（BE-06）
- [ ] 新增 `backend/pawtwin/repo_dynamo.py`：按裁定 5 实现 `Repository` 全协议；延迟导入 boto3、缺依赖/凭据具名 fail-closed（与 `memory.py`/`agentcore_client.py` 同构）。
- [ ] 新增 `tests/test_repo_dynamo_live.py`（marker `dynamodb_live`）：去重返回既有 run、`EXECUTING` 不可重领（穷举 11 状态）、CAS 双批准一次执行一次记账、租约过期可重领、`renew_lease` 只对持有者有效、`release_run` 静默、`UNSET` 不动列 / `None` 写 NULL、`facts_version` 原子自增、A09 缺事实 fail-closed、`set_feedback_status` 的 available 不变式（含负向）。
- [ ] `repository.py`：`FeedbackRecord.agentcore_session_id` + `set_feedback_status` 参数扩展；`repo_sqlite.py`：`SCHEMA_VERSION` 3→4 + `_V4_FEEDBACK_COLUMNS` 幂等迁移 + v3→v4 回归测试。
- [ ] `auth.py`：TTL/idle 过期 + 登录失败限速；`api.py`：`/api/login` 加 429 与 `Retry-After`、`storage` 标签真实化、429 响应进 `_responses`。
- [ ] `worker.py`：新增记忆轮询推进器（复用 `LeaseRenewer` 的线程范式），仅在 `memory_backend == "agentcore"` 时启动；**不写状态字面量**（裁定 12）。

### 4.2 AI（AI-04）
- [ ] `agentcore_client.py` 按 §2 重写三个方法 + 事件状态映射（映射表来源在注释里具名，未知值一律 `processing`）。
- [ ] `memory.py`：`AgentCoreMemory.get_status` 两段式（先 event 终态再检索取证）；`_namespace` 改 `/owner/<owner>/pet/<pet>`；`search` 用真实 `namespacePath`；docstring 的「未验证」声明改为「已在 `<region>` 账号实测，证据见 `docs/evidence/day5-cloud-*.md`」——**仅在 G5 真跑通后**才允许这样写。
- [ ] `bedrock_client.py` 保持不动，真实往返证据来自 `request_id`；若 SDK 返回字段与 `:200-207` 的猜测不符，按实测调整 `_summarise` 并加测试。

### 4.3 Frontend（FE-05）
- [ ] `App.tsx`：真实态标签（`storage=dynamodb` 分支、`agentcore` 已提炼态、`AWS 已连接` 徽标）全部由**证据驱动**——`request_id` 非空、`memory_record_ids` 非空、`aws_connected` 真实值；新增文案**必须避开 e2e 禁串**（「可检索」「已检索到记忆」「真实记忆」「真实检索」），措辞用「已提炼（真实 AgentCore 记录）」并把条数放在数据驱动的动态文本里。
- [ ] `tests/test_frontend_labels.py` 与 `frontend/e2e/feedback.spec.ts`/`acceptance.spec.ts`：禁串守卫**同步扩到新增常量**（收紧，不放宽）；新增一条断言：真实态标签必须与 `memory_record_ids`/`request_id` 配对渲染。
- [ ] 本地 e2e 仍跑 local_fake + 内存库，**数量不得因云改造而减少**（仍 ≥16 passed）。

### 4.4 Infrastructure（OPS-05）
- [ ] `.gitignore` 先加 `infra/deploy_state.json`（裁定 2）→ 再写 `infra/deploy_plan.json`、`scripts/deploy_aws.py`、`scripts/cleanup_aws.py`、`scripts/aws_probe.py`。
- [ ] `deploy.ps1`/`cleanup.ps1`：按裁定 1 改门（CLI/boto3 能力 → plan 源 → 必填参数 → 授权令牌），`-Apply`/`-Destroy` 从「明确未实现」改为「按 plan/state 真实现」，但**任一前提缺失仍 `NOT EXECUTED` + 退出码 2**，绝不 `exit 0`。
- [ ] OIDC：GitHub OIDC provider + 仅允许推送到指定 ECR 仓库的 role（信任条件锁到 `repo:owner/name` + `ref: refs/tags/*` 或 workflow 名）；ECR 仓库、DynamoDB 表、日志组、AgentCore memory 均在 plan 中声明并带 `project` 标签。
- [ ] `Dockerfile` 解耦 `PAWTWIN_MODE`；新增 `.github/workflows/image.yml`（裁定 14）。
- [ ] 删除顺序成文并实现：服务 → （Express 托管的 LB）→ ECR 镜像/仓库 → CloudWatch 日志组 → AgentCore memory → DynamoDB 表 → IAM role/OIDC provider；每步读回验证不存在。

### 4.5 Coordinator（门 0/装配/文档）
- [ ] `config.py`：三项新 settings + aws 模式口令校验；`models.py` 不动（无需新 DTO）；重生成契约并 `--check`。
- [ ] `main.py`：`mode=aws` 装配 + 探活 + `app.state.aws_connected`；`pyproject.toml`：`dynamodb_live` marker 注册 + addopts 表达式更新；`conftest.py` 清理清单补新别名。
- [ ] `tests/test_settings.py`/`test_app.py`/`test_auth.py`/`test_feedback_api.py` 精确更新（不放宽）+ 每条关键修复做**回退负向验证**。
- [ ] 文档：`STATUS.md` Day-5 三档表 + 提交表 + 命名门禁判定；`evidence/day5-handoff.md`（12 项，含「未运行的检查及原因」）、`day5-cloud-probe.md`、`day5-cloud-verified.md`（真实 `request_id`/record id/服务 URL/digest/账单核查）、`day5-local.md`（命令 + 结果 + **这不证明什么**）、`day5-cloud-blocked.md`（若有未闭合项，逐条阻断与解锁前提）；`reviews/day5.md`（**非作者**）。Day-1..4 历史只追加后记。

## 5 串行临界段与执行顺序（≤4 活动 Agent）

**不可并行临界段**：C1=`repository.py`+`repo_sqlite.py`+`repo_dynamo.py`+仓储/恢复测试；C2=`models.py`+`config.py`+`contracts/`+`test_contracts.py`+`conftest.py`；C3=`api.py`+`auth.py`+`test_auth.py`；C4=`agentcore_client.py`+`memory.py`+`worker.py`+`test_feedback_api.py`（**禁止先接线后改守卫**，同批）；C5=`infra/`+`scripts/*`+`Dockerfile`+`.github/workflows/*`；C6=`frontend/src/*`+`frontend/e2e/*`+`test_frontend_labels.py`；C7=`STATUS`+`TASKBOARD`+`evidence`。

**提交序列**（每组提交信息必须携带当时的实测数字）：
`D1` C1 repo_dynamo + `dynamodb_live` marker + 协议集合守卫 → `D2` C2/C3 公网三门 + 429 契约重生成 → `D3` C1/C4 AgentCore 真实化 + 轮询接线 + `SCHEMA_VERSION` 4 + 守卫 re-ruling → `D4` C5 `.gitignore` 先行 + `deploy_plan.json` + `deploy_aws.py`/`cleanup_aws.py` + 门控改写 + OIDC/IAM → `D5` C5 `image.yml` + Dockerfile 解耦 → `D6` C2/C3/C6 云装配 + 前端真实态标签与守卫 → `D7` `scenarios.json` + `evaluate.py` → `D8` C7 证据与文档。

只在**最终 HEAD** 声明全绿；**中间提交不逐个复验**（`repo_dynamo`/`api.py`/`contracts/` 终态互依赖），并如实披露这一点（沿用 Day-4 裁定 4 的纪律，禁止为凑快照手改生成物）。

```
P0 就绪门与用户节点（~1.5h，需用户在场）      G1 基线复跑（~0.5h）
D1 repo_dynamo 实现 + 离线守卫（~5h；C1）      ┐ D2 公网三门（~3.5h；C2/C3）可并行批次
D1' 真表 dynamodb_live 全套实跑与修复（~2.5h） ┘
D3 AgentCore 真实化 + 接线 + v4 迁移（~4h；C1/C4）
D4 编排器 + OIDC + 门控改写（~4h；C5）
D5 CI 构建推 ECR（~1.5h；C5，含首次真实构建排障）
D6 云装配 + 前端真实态（~2.5h；C2/C3/C6）
D7 24 案例集 + 真机评测（~4h）
G7 apply + 浏览器三场景验收（~1.5h）
G10 cleanup dry-run→删除→读回（~1.5h，若演示期未结束则推至 Day-6）
D8 证据文档（~2h；C7）                        G11 非作者独立审查 + 复跑（~3h）
```
合计 ≈ **28–33h 串行 Agent 工时**，**明显超出一日**：本计划据用户裁定⑤把 Day-5 定位为「真实部署专日」，执行承接至 Day-6 上午，材料全部落在 Day-6。常驻 = Coordinator + Backend + AI + Frontend；OPS 与 Reviewer 空槽串行复用，**Reviewer 不得由作者充当**（`docs/agents/reviewer.md:10`；Day-4 计划写的「L15」是过时引用，该文件实际只有 10 行，规则原文在第 10 行末句）。新增任务行：`BE-06`、`AI-04`、`FE-05`、`OPS-05`。

## 6 A01–A14 在 Day-5 的判定

| 编号 | Day-5 判定 | 说明与不得声称 |
|---|---|---|
| A01/A02/A03/A05/A09 | **回归必过 + 真实模型补证** | 本地闭环全绿不变；正常与重复喂食场景由真实 Bedrock 出建议、`request_id` 非空、证据面板可追溯 |
| A04 | **真表必过 / 跨副本尽力** | 单 task + DynamoDB 条件写/事务下「并发双批准恰一次执行、一次记账」；**未真实制造双 task 前不得写「跨副本已验证」** |
| A05 | 必过（真表） | 同一 `event_id` 重传返回既有 run，不二次调模型 |
| A06/A07/A08 | **首次转必过** | ACTIVE 前置 → 提交 → 轮询 → 真实 record id；`today_only` 在真实策略下不得成为永久偏好；当前事实与硬策略优先于记忆（模型在环复验） |
| A10 | **必过（真实故障面）** | 真实限流/网络失败/受控延迟下不得出现虚假成功；未知状态不盲目重执行 |
| A11 | 必过（模型在环） | 案例集含恶意指令样本；原文与记忆文本注入仍被 policy/审批/配额挡住 |
| A12 | **必过（公网真实面）** | 未登录 401、approval 401/403、429 限速实测、伪造 `X-Forwarded-Proto` 直连 ALB 域名出定论、浏览器与镜像层无 AWS 凭据；默认口令拒启为新增必过。**仍不得写「A12 完全通过」**，除非跨副本与会话持久化也已验证 |
| A13 | **必过（服务级）** | 真实滚动部署/重启后真表状态可恢复、终态不重跑、租约有期限；容器内 `ANALYZING` 被 kill 为尽力项 |
| A14 | 必过 | 真实模型下事实变化驱动建议变化，由 24 案例集量化覆盖 |

## 7 完成的硬性证据（DoD，每项给命令与数字）

- [ ] `uv run --frozen --extra bedrock --extra memory pytest -m "dynamodb_live or bedrock_live or agentcore_live" -q` → **真账号真表全过**，逐例列 `request_id` / AgentCore `eventId`+`recordId` / 表名与区域；任何 skip 必须具名并写等待条件。
- [ ] 本地全量：`uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` → 通过数 = **195 + Day-5 新增数**（明列新增文件与用例名）；`ruff check .` 无告警；`verify.ps1` EXIT=0。
- [ ] 契约：`python scripts/export_contracts.py --check` → current，**OpenAPI 仍恰 14 条路径**，`/api/login` 含 429；`domain.schema.json` 的 `$defs` **仍恰为** 6 输入模型 + `RunState`（`==` 断言不得放宽）。
- [ ] 依赖：**不新增依赖、不动 `uv.lock`**（`uv lock --check` exit 0）；`pyproject.toml` 注释新增「`repo_dynamo` 复用 `memory` extra 提供的 boto3」这一事实。
- [ ] 测试基础设施一致性：`conftest.py` 清理清单从 20 项扩到新增别名后的项数（明列）；每条关键修复均有**回退转红**的负向验证记录。
- [ ] 前端：`npm run typecheck`/`build` 通过；本地 e2e **≥16 passed** 且禁串断言未放宽；`test_frontend_labels.py` 覆盖新增真实态常量。
- [ ] 云部署：CI run 链接 + 镜像 digest + 尺寸 + 架构；`create-express-gateway-service` 响应（服务 ARN、URL、`healthCheckPath`、cpu/memory、scaling target 实际生效值）；`curl https://<svc>.ecs.<region>.on.aws/healthz` → 200；浏览器三场景记录（截图或文本实录）。
- [ ] 安全：公网未登录 401/403 实测；连续错误口令触发 429 的实测；`Set-Cookie` 在真实 HTTPS 下含 `Secure`；伪造 `X-Forwarded-Proto` 的行为定论并写入文档；全仓凭据 grep **0 命中**；`.env` 与 `infra/deploy_state.json` **未被跟踪**。
- [ ] 费用：`infra/cost-estimate.md` 的实测单价与总额 + 用户确认原文（截图/文本）+ apply 后的 `aws ce get-cost-and-usage` 实际数字；**不出现任何预填金额**。
- [ ] 评测：`docs/evidence/evaluation-<stamp>.md` 的 24 例逐条结果与真实通过率（含失败/超时原文），并写明只证工作流一致性。
- [ ] 可删除：`cleanup.ps1` dry-run 清单 → `-Destroy` 执行 → 每类资源读回不存在的证据。
- [ ] 文档：`STATUS.md` Day-5 三档表 + 本地/云端双列 + 提交表 + 命名门禁判定；`evidence/day5-*`；`reviews/day5.md`（非作者，每条发现记「处理/复测」）；`TASKBOARD.md` 第 5 日派发与完成记录。
- [ ] 副作用口径：本轮**会产生真实云资源与计费**，因此必须精确列出「创建了哪些资源、区域、预计与真实费用、删除计划」，取代前四日的「零副作用」声明；除授权范围外不得创建任何额外资源，不推送未在清单内的远程仓库，不自动提交比赛。

**禁止出现的表述**：「镜像已构建」（本轮必须真构建，否则继续如实标注）、「HTTPS 可访问」出现在 G7 之前、「DynamoDB 条件写通过」缺真表证据、「AgentCore 已检索 / 记忆已提炼」缺真实 record id、「跨副本已验证 / 多副本并发已验证」（单 task，裁定 15）、「会话安全已达标」（跨副本未做）、「readyz 已就绪」出现在探活之前、「已自动停费 / 预算硬上限」、「Graviton 已优化」、「arm64 已验证」、「CI 全绿 / 流水线已跑过 e2e」出现在首次推送之前、「24 案例通过率」出现在跑批之前、「可作为参赛发布版」出现在命名门禁满足之前，以及任何预填的单价、延迟、准确率或成功率。

## 8 降级、关键路径与上报

**8.1 关键路径**：P0 → D1/D1'（repo_dynamo 真表）→ D3（AgentCore 真实化）→ D4/D5（编排与镜像）→ G7（apply）→ G8 → G9。最易滑期：①`repo_dynamo` 的事务/条件语义等价性（DynamoDB 与 SQLite 锁语义差异会在真表测试里当场暴露）；②首次真机 CI 构建（base 层 `uv sync --extra` 与 npm ci 的拉取时间、ECR 权限、OIDC 信任条件）；③AgentCore strategy 进 `ACTIVE` 的等待与提炼时效。

**8.2 降级预案**
- **A** Express Mode 在该账号/区域不可用或创建失败 → **不得**退回明文 HTTP 冒充 HTTPS 验收；改提「标准 ECS + ALB + 自定义域名 + ACM」方案（新增成本与 DNS 验证），**停下上报取得用户确认**后另行执行。
- **B** Bedrock 模型无工具调用/结构化输出能力，或账号未获模型访问 → 换候选；不换则 G8 的 `request_id` 项记真实失败，**不得**把 `local_fake` 的结果写进云验证列。
- **C** strategy 不进 `ACTIVE` 或提炼超 180s → 记忆案例记 TIMEOUT，页面保持 `processing`，绝不写 `available`；A06 记「未闭合」并写明解锁前提。
- **D** OIDC provider/role 需 IAM 管理权限而我没有 → 用户手工创建并提供 role ARN（**不索要长期密钥**），CI 与部署改由用户身份执行清单步骤。
- **E** 费用估算有项取不到（如 AgentCore 定价）→ 该门不放行 apply，改为「仅 D1–D3 的真表/真模型验证 + 材料」并上报。
- **F** 任一必过云门未闭合 → 产物回到「本地验证候选（非参赛版）」命名，`day5-cloud-blocked.md` 逐条列阻断与解锁前提，Day-6 材料如实引用。
- **G** 真表测试或 apply 卡在配额/权限（新账号常见）→ 优先换区域或提限额，不通过降低断言或删测试来「过门」。

**8.3 需用户确认的点**（随本计划批准即生效）：①裁定 1（不引入 CDK/CFN、改 `deploy.ps1` Gate 2 判据）；②裁定 9（`/readyz` 语义受控修订，LB 仍指 `/healthz` 不变，对 Day-4 裁定 7 的书面更正）；③裁定 12（守卫 re-ruling 的新作用域）；④裁定 14（口令先进容器 env、`secrets` 支持与否实测后如实记录）；⑤裁定 15（副本固定 1×1 与跨副本不作必过）；⑥裁定 18（评测打已部署 HTTPS 并允许真实失败）；⑦DoD 第 12 条把「零副作用」改为「精确披露真实资源与费用」的口径变化。

**8.4 上报的容量冲突（不得静默吸收）**：Day-5 字面（总方案 L104）同时要求「冻结功能 + 评委自由输入 + 概念素材 + 演示脚本 + 英文材料 + 录屏」，而本轮又承接了 Day-4 顺延的**全部**云端块（`repo_dynamo`、真实推理与记忆、镜像、HTTPS、可删除）。按 §5 估算 ≈28–33h，**压不进一个工作日**。依用户裁定⑤的处理是：Day-5 只做真实部署与验收，**材料整体顺延 Day-6**；因此总方案第 6 节的「五日」实际变为**六个工作日**，这一变更已在 `STATUS.md`/`TASKBOARD.md` 上报并留待用户认可。

## 9 执行手顺（账号就绪即做，Day-5 的主线本身）

`uv sync --frozen --extra bedrock --extra memory` → 注入短期凭据（不落盘、不入仓）→ `preflight.ps1` 与 `aws_probe.py` 只读探测 → 用户确认区域/模型 → `infra/cost-estimate.md` 实价 → **用户书面确认预算与期限** → `deploy.ps1 -PlanOnly`（编排器不发送请求的参数级 plan）→ OIDC role + ECR + DynamoDB 表 + 日志组 + AgentCore memory（含 strategy，等待 `ACTIVE`）→ `uv run --frozen pytest -m "dynamodb_live or bedrock_live"` 真表真记忆全过 → `image.yml` 构建推 ECR（记 digest）→ `deploy.ps1 -Apply -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT` → `DescribeExpressGatewayService` 轮询至 `ACTIVE` → 真实 HTTPS 浏览器三场景 + A08/A12/A13 实测 → `evaluate.py` 24 案例真机跑批 → `STATUS`/`evidence`/`reviews` 落盘 → 演示期结束后按删除清单 `cleanup.ps1 -Destroy` 并读回零残留。**每一步失败都记录为真实失败，不回退替身。**
