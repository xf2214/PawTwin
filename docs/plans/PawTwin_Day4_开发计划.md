# PawTwin 第四日（Day-4）开发计划

> 本文是 [五日开发总方案](PawTwin_五日开发总方案.md) 第 6 节「第 4 日」与 [实施任务单](PawTwin_Agent_实施任务单.md) **T7**（+T6 的独立审查/证据体例、OPS 部署材料）的当日可执行分解；承接 [Day-3 开发计划](PawTwin_Day3_开发计划.md) 与 [Day-3 完成记录](../STATUS.md)。
> 由三视角（后端契约与云部署、前端+AI/云就绪、独立审查）交叉校验，对每条关键断言回源码二次核查，并由总负责人亲自复核存疑项后定稿。
> 执行者无需再做设计决策；如与两份权威计划冲突，以权威计划为准并回报总负责人。编制日期：2026-09-28。
> **基线**：分支 `chore/bootstrap`，HEAD=`dc8dc10`（Day-1 末，实测 `git log`）；**Day-2 与 Day-3 改动全部未提交**，同一脏工作区实测 **39 modified + 31 untracked**（Day-3 计划 §0 写的 38+14 已过时）；`uv.lock` 含 `boto3==1.43.102` 与 `strands-agents==1.57.0`；OpenAPI 工作区为 **14 条路径**。Day-4 的第一步就是把这批改动入库（S0），因此本文所有行号引用均以**当前工作区文件**为准。

## 0 前提、实测事实与当日验收（三档）

**前提（用户 2026-09-28 确认四点）**：①**仍无 AWS 账号，但即刻着手注册** → Day-4 只做本地可验证项，真实云为条件项，账号就绪日按 §7.5 手顺执行；②**开工前先分组提交 Day-2/Day-3**（S0）；③范围**只取 T7（云部署与可删除，含 HTTPS、访问控制）+ 独立审查 + 浏览器验收 + 针对失败修复**，**明确不含** T6 的 24 案例集 `scenarios.json`+`evaluate.py`、`repo_dynamo`、会话 DB 持久化与登录限速；④**不安装 Docker**（照任务单 L23「缺 Docker 时先完成源码与测试，不静默安装」）→ 镜像在 Day-4 **完全不可解锁构建验证**，只能记「已静态审读、未构建」。

诚实红线延续：AGENTS.md L18/L22/L53 与总方案 L39/L69/L106/L153 —— **绝不以本地替身、stub、SQLite 或「脚本文本存在」冒充云端已完成**；未验证项一律分列并具名。

### 0.1 规划阶段实测事实（Day-4 判据的地基，均已回源码/命令核实）

| # | 事实 | 证据 |
|---|---|---|
| F1 | 本机 `docker`/`aws`/`cdk`/`podman` **均不在 PATH**，`C:\Program Files\Docker` 不存在 | 主控实测 `Get-Command` → CommandNotFound |
| F2 | **Day-2 的「11 路径契约冻结点」从未入库**：`94216df` 的 `contracts/openapi.json` = 9 条路径、HEAD `dc8dc10` = 9 条、工作区 = 14 条 | 主控实测 `git show <ref>:contracts/openapi.json` 正则计数 |
| F3 | HEAD 的 `.gitignore` **不含 `*.db`/`*.db-journal`**（只有 `Thumbs.db`）；这两行属未提交的 Day-2 改动 | `git show HEAD:.gitignore` vs 工作区 `.gitignore:17-19` |
| F4 | `infra/cloud-access-checklist.md:64-68` 与任务单 `:349` 承诺的 `preflight.ps1 -Mode aws` **参数不存在**（`scripts/preflight.ps1:1` 只有 `param([string]$NodeDirectory)`）；该脚本无 `exit`，无凭据仍打印「preflight passed」并以 **0** 退出（L34-38 打印 NOT EXECUTED、L57 收尾） | `docs/agents/infrastructure.md:17` 却要求 preflight 无凭据「以非零码退出」→ 文档与脚本互相矛盾 |
| F5 | `scripts/deploy.ps1`、`scripts/cleanup.ps1`、`backend/pawtwin/repo_dynamo.py`、`scripts/evaluate.py`、`tests/cases/scenarios.json`、`frontend/src/components/`、`tests/e2e/` **全部不存在**；`infra/` 无任何 IaC 源（仅两份 md） | `Test-Path` 实测 |
| F6 | `create_app` 对 `mode=="aws"` **无条件 `raise NotImplementedError`**；`config.py` 的 aws 交叉校验只查 4 个环境变量字符串、不检查 storage 实现 → 唯一阻塞点在 `main.py:82`，不在 config | `main.py:81-82`、`tests/test_settings.py:34-45` |
| F7 | `/readyz` **无条件 503**（装饰器硬编码、函数体无分支），`storage` 恒 `"sqlite_local"`；`/healthz` 恒 200；Dockerfile 的 `HEALTHCHECK` 打的是 `/healthz` | `main.py:121-138`、`Dockerfile:29-30` |
| F8 | 登录 cookie 的 `secure` 判据是 `mode == "aws"` 而非请求 scheme，而镜像把 `PAWTWIN_MODE=local` 烤死 → **部署到 HTTPS 后 cookie 不带 Secure**；`get_state` 的 `storage` 亦硬编码 `"sqlite"`（前端 `DynamoDB` 分支不可达） | `api.py:181-189`（L187）、`Dockerfile:14`、`api.py:208-213`（L212）、`App.tsx:476` |
| F9 | `pyproject.toml:18-19` 声称「CI 与容器镜像默认都不装该 extra」，但 `Dockerfile:24` 明确 `--extra bedrock --extra memory` 都装 → **假陈述**；CI 只有 `uv sync --frozen`（无 extra），与镜像依赖闭包互不覆盖 | 两文件原文对读 |
| F10 | A12 测试缺口：`POST /api/runs/{run_id}/approval` **既无未登录 401 也无缺 CSRF 403 断言**；`POST /api/logout` 无未登录 401 断言；`demo/*`、`feedback/*` 均已覆盖 | `tests/test_auth.py:11-14`（仅 state/events/runs GET）、`test_demo_api.py:73-74/79-80`、`test_feedback_api.py:32-34/39-40` |
| F11 | 记忆生命周期是「**未接线**」而非「已实现待验证」：`MemoryService.get_status` 生产端**零调用者**（唯一调用在 `tests/test_memory.py:112`），`GET /api/feedback/{feedback_id}` 只回读库中状态；`agentcore_client.py:151-152` 的 `return "available"` 因 `event_status` 无调用方而**不可达** → 无任何路径能把状态推进到 `available` | `api.py:411-415`、`memory.py:221-236` |
| F12 | 登录限速/失败计数/会话 TTL **零实现**（`Session.created_at` 赋值后从未被读取）；会话与 CSRF 为进程内 `dict`，cookie 值即 `session_id` 明文；默认口令 `local-demo-passphrase` 随源码公开 | `auth.py:24-33`（L33）、`auth.py:42`、`auth.py:51-65`、`config.py:36-39` |
| F13 | 现有 e2e **恰 10 条**（approve×4 / decline×1 / feedback×3 / shell×2，用例名已逐条核对）；`webServer` **未设 `PAWTWIN_DB_PATH`** → 进程内内存库；**全仓无任何视口设置**，总方案 T3 的 1440px/390px 检查从未做过 | `frontend/playwright.config.ts:34-43`、`approve.spec.ts:7/57/81/99`、`decline.spec.ts:5`、`feedback.spec.ts:11/38/53`、`shell.spec.ts:5/15` |
| F14 | 无 git remote、无 upstream → CI 从未在远端运行过；`.gitignore` 对 9 条忽略项覆盖完整（`git status --ignored` 实测恰 9 条 `!!`），无产物漏网，全仓无秘密 | `git remote -v` 空、`ci.yml:33` |
| F15 | `uv.lock` 中 `boto3`（1.43.102）与 `strands-agents`（1.57.0）各为**单一节点**、strands 对 boto3 无版本约束 → 两 extra 合并**静态无冲突迹象**；但合并安装能否成功只有实跑才能定论 | `pyproject.toml:21-33`、`uv.lock:45-56/769-791` |

### 0.2 当日验收（三档）

| 档位 | 内容 |
|---|---|
| **必过 Gate** | **G0** S0 基线入库（含 F2/F3 两条书面披露 + 最终 HEAD 全绿实测）；**G1** 干净树全量回归**重新实测**（禁引用 Day-3 的 184/11/10 数字代替）；**G2** 访问控制补口（cookie `Secure` 按 scheme 解耦 + approval/logout 的 401/403 矩阵 + 无凭据入前端/仓的证据）；**G3** 健康检查端点**硬裁定**成文（LB 与容器 HEALTHCHECK 一律 `/healthz`，`/readyz` 保持 503 且不为部署改码）；**G4** `deploy.ps1`/`cleanup.ps1` **fail-closed 骨架**（缺 CLI/缺 IaC 源/缺参数 → `NOT EXECUTED` + 退出码 2，绝不调用 AWS、绝不 `exit 0`）；**G5** 镜像**静态审读** + 修 F9 假陈述 + `uv sync --frozen --extra bedrock --extra memory` 合并实测；**G6** 浏览器验收矩阵**新增 6 条 e2e**（含 T3 从未做的 1440px/390px 视口检查），每条写「这不证明什么」；**G7** 前端标签**改为证据驱动** + `available` **反伪造守卫测试**；**G8** 非作者独立审查 + 修复 + 复跑；**G9** 文档诚实四件套 + 零副作用声明 + **Day-4 字面验收整体顺延的上报** |
| **尽力项** | `preflight.ps1` 增加**真实存在**的 `-Mode` 参数（只读、缺 CLI 仍逐段 NOT EXECUTED、由 §1 裁定 8 的语义分级约束退出码）；`infra/` 出**纯文本** IAM 策略与资源草案（显式标注「未经 cdk/CLI 校验，不可 apply」）；费用表把**公网 IP / ALB LCU 拆为独立行**（现并入 ECS 行属现有缺口）+ 按依赖的删除顺序表；`/readyz` 真实连通判据的**设计文档**（不含实现）；角色简报补 Day-4 段（`docs/agents/reviewer.md` 现只写到 Day-2）；§7.5「账号就绪即执行手顺」成文 |
| **条件项**（分档解锁） | **仅需账号 + AWS CLI** → 区域×Bedrock 模型×ECS Express Mode 可用性实测、IAM 边界实测、`cdk/CFN` 真实 plan 与 diff、一次真实 Bedrock 往返并记录 `request_id`、一次真实 AgentCore strategy `ACTIVE` + submit→轮询→`available`、`repo_dynamo` 真表条件写。**仅需 Docker**（用户已裁定不装 → Day-4 不可解锁）→ 镜像构建成功、linux 下 extra 闭包、容器内 `healthz`/静态页不覆盖 `/api`/worker 随 lifespan 实际运行、HEALTHCHECK 生效。**需三者齐备** → HTTPS 演示地址可访问、公网未登录拒绝（A12 真实面）、双副本滚动下 A04 与跨副本上限、容器内重启与失败回执复验、`deploy.ps1 -Apply` 与 `cleanup.ps1` dry-run→删除→残留核对全链 |

**明确不写进 Day-4 承诺（显式顺延）**：`repo_dynamo` 与数据库级跨副本计数（→ 账号就绪日）；T6 的 `scenarios.json`+`evaluate.py`（→ Day-5 或正式放弃，见 §7.4 冲突上报）；记忆提炼轮询与 `available` 接线（→ 账号就绪日）；会话 DB 持久化与登录限速实现（→ 公网部署确认要做时才做，Day-4 只出裁定议题）；HTTPS/镜像构建/云资源创建/远程推送；A10 的「迟到回执真异步入口」（Day-2 已书面归约，仍不归 Day-4）。

## 1 技术裁定（前置须落定；每条已回源码或命令核实）

| # | 议题 | 裁定 | 依据 |
|---|---|---|---|
| 1 | **当日验收重定义** | 总方案 L103 的「HTTPS 演示可访问；访问控制、刷新、重启和失败回执通过；可部署可删除」**逐短语判定**：HTTPS 可访问 / 可部署 / 可删除 = **整体不可达成**（F1+F5+F6+无证书）；刷新、失败回执 = 回归必过；访问控制 = **仅本地子集可达**；重启 = 部分可达（落盘跨进程已验证，容器/服务级不可）。当日主线改为「**基线入库 + 访问控制补口 + 部署前置材料的诚实完备性 + 浏览器验收 + 独立审查**」，并**向用户上报阻塞**而非拆成半通过（总方案 L106 要求云端里程碑按实际阻塞顺延、保留对应工作量） | F1/F5/F6/F7/F8；总方案 L103/L106/L153 |
| 2 | **config 不是阻塞点（剔除因果混淆）** | `config.py` 的 aws 校验只查 4 个环境变量字符串、不检查 storage 实现，这是**正确设计**（Settings 不做 IO、不导入可选云 SDK）；`aws_connected` 恒 False 正是履行「不得由环境变量推断已连通」。唯一阻塞点是 `main.py:82` 的 raise。**Day-4 不得为让云端 demo 起得来而移除该 raise**：无 `repo_dynamo` 时移除即等于用 SQLite 冒充云端存储。文档须把「aws 模式启动被禁」写成 T7 的第一个真实阻塞点，**不是 bug** | F6；`main.py:81-82`、`config.py:157-166`、`config.py:176-186`、AGENTS.md L69 |
| 3 | **S0 分组判据** | **先行组 S0-a** = `.gitignore`（补 `*.db`/`*.db-journal`）+ `pyproject.toml` + `uv.lock`，**必须最先入库**（F3：否则 `*.db` 未被忽略，单独 checkout 跑重启类测试即弄脏工作区、误纳风险陡增；对齐 `ci.yml:35-38` 的「锁必须与 pyproject 同提交」）。其后**六组按逻辑子系统**而非按「天」拆：**S0-b** 门 0 契约冻结（`models.py`+`contracts.py`+`contracts/openapi.json`+`contracts/domain.schema.json`+`config.py`+`tests/test_contracts.py`+`tests/test_settings.py`+`tests/conftest.py`，**四者必须同组**，否则 `export_contracts.py --check` 对中间态必红）、**S0-c** 后端持久化/并发/worker/恢复/`main.py`/`api.py`/`auth.py` 及其测试、**S0-d** AI 适配器与两个云客户端及测试、**S0-e** 前端与 e2e、**S0-f** OPS 镜像/CI/脚本/`.env.example`/`.dockerignore`、**S0-g** 文档与证据。注：依赖三件已从原 OPS 组抽出并入 S0-a | F2/F3/F14；AGENTS.md L43/L44；Day-3 计划 §2 |
| 4 | **只回填一个真实存在的冻结 ID** | 实测历史里不存在 11 路径快照（F2），且契约是生成物不可手改 → **Day-2 与 Day-3 的「两个契约冻结提交 ID」预期不可达成**。改为一项披露 + 一项回填：回填**含终态 14 路径 `openapi.json` 的那一次提交**为「Day-2/Day-3 合并契约冻结 ID」，并在 `docs/STATUS.md` 与 `docs/TASKBOARD.md` **书面披露**「Day-2 的 11 路径冻结点从未入库（实测 `94216df`=9、`dc8dc10`=9）；两日改动在 `models.py`/`api.py`/`contracts/` 同批纠缠，终态互依赖，中间提交不逐个复验」。**禁止**为凑数手工捏造 11 路径 openapi.json | F2/F14；AGENTS.md L43；STATUS.md L74/L152、TASKBOARD.md L89/L124、Day-3 计划 §2 L46（三处预期须改为披露） |
| 5 | **cookie `Secure` 与 `mode` 解耦** | `api.py:187` 由 `mode == "aws"` 改为**按请求 scheme 判定**（`https` 直连，或**仅在受信代理链下**采信 `X-Forwarded-Proto`），使公网 HTTPS 自动带 Secure、本地 HTTP 仍省略。**不新增环境变量**（避免动契约与 conftest 清理清单）。回归面：`tests/test_auth.py:34` 的 `"secure" not in cookie` 在 TestClient（`http://testserver`）下仍为真不破；须**新增配对断言**「scheme=https → 含 Secure」。诚实边界：本地无证书，**不得**据此声称「HTTPS 会话安全已达标」 | F8/F12；`api.py:181-189`、`Dockerfile:14`、`tests/test_auth.py:24-34` |
| 6 | **A12 本地补口 = 必过，但不得记 A12 通过** | 补三项缺口：`POST /api/runs/{run_id}/approval` 未登录 401 + 缺/错 CSRF 403、`POST /api/logout` 未登录 401、「`frontend/dist` 产物与全仓 grep 无 AWS 凭据/口令」的 A12 本地证据（grep 记录进 evidence）。**未闭合缺口必须分列**：无登录限速、会话无 TTL（`created_at` 无消费者）、默认口令随源码公开 → 公网部署前须由 §1 裁定 14 的门回答 | F10/F12；任务单 L133；`tests/test_auth.py:11-14` |
| 7 | **健康检查端点硬裁定（防部署自伤）** | 容器 `HEALTHCHECK` 与 ALB/target group **一律用 `/healthz`**；`/readyz` 恒 503 只作人工诊断读取，**严禁**为让部署走完而改成 200（用状态码撒谎，同时违反 reviewer.md 的「不得高报也不得低报」）。理由：`readyz` 无分支硬编码 503，若目标组指它则任务永远不健康、服务永远 DEPLOYING，而失败表象会被误读为「镜像有问题」 | F7；`main.py:121-138`、`Dockerfile:29-30` |
| 8 | **preflight 与 deploy/cleanup 的退出码语义分级** | 两类脚本必须分开定义并写进文档：**环境自检**（`preflight.ps1`）无凭据仍 exit 0，但须逐段打印 `NOT EXECUTED` 且不得由 env 推断连通；**计费/资源类**（`bedrock-smoke`、`agentcore-smoke`、`deploy`、`cleanup`）fail-closed，缺前提即 `NOT EXECUTED` + 退出码 2。据此**修正 `docs/agents/infrastructure.md:17` 的笼统要求**，并把 `cloud-access-checklist.md:64-68` 的代码块改为「现状命令 + 目标命令（标注脚本未编写）」；给 preflight 真加 `-Mode` 列为尽力项（若做则参数必须真实存在） | F4/F5；`scripts/preflight.ps1:1/34-38/57`、`scripts/agentcore-smoke.ps1:27-36` |
| 9 | **deploy/cleanup 的诚实形态 = fail-closed 骨架** | 检查顺序固定为：①`Get-Command aws`/`cdk` 存在性 → ②IaC 源存在性（`infra/` 现无任何模板）→ ③必填参数齐备性（`AWS_REGION`/`DYNAMODB_TABLE_NAME`/`AGENTCORE_MEMORY_ID`/`BEDROCK_MODEL_ID`；account id **仅运行期注入、绝不预填**）→ 任一缺失打印 `NOT EXECUTED: <缺什么>` 并 **exit 2**；**绝不调用任何 AWS API、绝不 `exit 0`**。`-PlanOnly` **保留任务单字面命名**（改名会破坏与权威计划一致性），但 `.SYNOPSIS` 首行钉死「无 AWS CLI / 无 IaC 源时本脚本不产出任何 plan；`-PlanOnly` 的含义是只 plan 不 apply，不承诺必然有 plan 输出」。`-Apply` 分支存在 ≠ 可一键部署，且必须再要求显式费用授权标记。`cleanup.ps1` 默认 dry-run，无账号时的诚实输出就是「拒绝列出并解释原因」。自检方式：PowerShell 语法静态解析（`[System.Management.Automation.Language.Parser]::ParseFile`）+ 空 env 干跑断言退出码 2，**不依赖真实 CLI** | F1/F5；任务单 L344/L349/L356；复用 smoke 体例 |
| 10 | **镜像只能记「已静态审读、未构建」，但依赖闭包可部分实测** | 用户裁定不装 Docker → 容器内行为完全不可验证。Day-4 必做两件事：(a) **修 F9** 的 `pyproject.toml:18-19` 假陈述（改为「CI 不装、镜像装」的真实描述）；(b) 本地实跑 `uv sync --frozen --extra bedrock --extra memory`（无需 Docker/账号），exit 0 即把「镜像依赖闭包可复现」从纯推断升为部分实测，并记录 CI（`ci.yml:33` 无 extra）与镜像闭包互不覆盖的缺口。第三条解锁路径（在 GitHub Actions 上构建镜像）**需用户另行授权创建 remote 并推送**，本轮不假设 | F1/F9/F15；`Dockerfile:20-24`、`ci.yml:33` |
| 11 | **`available` 的措辞归真 + 反伪造守卫** | 记忆项必须写成「`MemoryService.get_status` 接口已就位、**生产端无调用方**，`processing→available` 生命周期**未接线**，真实轮询词表离线不可证真」；**不得**写「已实现待验证」（方法确实存在），也**不得**写「完全未实现」。Day-4 新增守卫测试：断言本地配置下**不存在任何能把 `memory_status` 写成 `available`/`processing` 的路径**（保护 F11 的不可达性不被「顺手实现」破坏——四处零件都在、只差接线，正是最易越界处）。真实轮询接线顺延到有账号日 | F11；`api.py:411-415`、`memory.py:221-236`、`agentcore_client.py:151-152`、AGENTS.md L18、总方案 L39 |
| 12 | **撤销「Day-4 可达真实模型往返」** | 解耦路径（`PAWTWIN_MODE=local` + `PAWTWIN_MODEL_BACKEND=bedrock`）在代码上存在，但无凭据即 `BACKEND_UNAVAILABLE`/`MemoryUnavailable`，其唯一实际效果是让前端标签由**配置**推导出「AWS Bedrock（真实模型）」而与 `telemetry.request_id` 恒 null 同屏矛盾 → **不作为可做项**，而是由 §1 裁定 13 主动堵住该失真入口 | F6/F11；`config.py:124-147`、`App.tsx:48-52/475-477/630`、`memory.py:266-273` |
| 13 | **前端标签改为证据驱动** | `App.tsx` 的 `BACKEND_LABELS.bedrock`=「AWS Bedrock（真实模型）」与 memory 标签「AgentCore（真实检索）」、`MEMORY_STATUS_LABELS.available`=「已可检索（真实记忆）」，一律改为**证据驱动**：仅当 `request_id != null`（模型）/ 存在真实 memory record id（记忆）时才允许「真实」字样，否则显示「已配置、未经真实验证」。`api.py:212` 的 `storage="sqlite"` 与 `App.tsx:476` 的 `DynamoDB` 死分支一并诚实化（保留 sqlite 实值 + 标注 `repo_dynamo` 未实现）。**注意文案陷阱**（Day-3 已踩）：诚实提示语不得字面包含被 e2e 断言禁止的子串（如「已检索到记忆」） | F8/F11；`App.tsx:48-52/75-80/455-477`、`api.py:208-213` |
| 14 | **会话/限速/默认口令 = 公网部署前置硬门（本轮只出裁定，不实现）** | 用户未选 → 不实现。Day-4 必须产出一份**书面裁定议题**交用户决：公网 HTTPS 部署前是否必须先补 (a) 登录限速/失败退避、(b) 会话 TTL（`created_at` 目前无消费者）、(c) 强制以环境变量覆盖 `local-demo-passphrase`。三者由 F12 从「可选优化」升格为**部署前置硬门**。同时写入诚实边界：会话进程内 + cookie 值即 `session_id` 明文 → **多副本必致 401**；`AdmissionControl` 仅进程内计数 → 滚动两副本实际全站并发 = 副本数 × 2 | F12；`auth.py:24-33/42/51-65`、`api.py:181-189`、`Dockerfile:31-34`、`config.py:36-39` |

## 2 S0 · 基线入库（前置串行，需用户逐组在场授权）

命令级检查清单（按序执行，全部只读或在 HEAD 上运行；**不含推送**）：

- [ ] `git status --porcelain=v1 -uall` → 复核 39 modified + 31 untracked，逐项确认无 `*.db`/`test-results/*.json`/快照/图片类文件。
- [ ] `git check-ignore -v .venv frontend/dist frontend/test-results .pytest_cache .ruff_cache .superpowers data` → 七条全部命中（实测覆盖完整，F14）。
- [ ] **S0-a（先行组）** = `.gitignore`（含 `*.db`/`*.db-journal`）+ `pyproject.toml` + `uv.lock`（裁定 3）。
- [ ] `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` → 记录**本次实测** passed/skipped 与具名 skip 全名单（Day-3 记录值为 184/11，不得直接引用，G1 复验）。
- [ ] `uv run --frozen ruff check .`；`uv run --frozen python scripts/export_contracts.py --check`（期望 Contracts are current，**14 条路径**）。
- [ ] `uv lock --check`。
- [ ] `./scripts/test-e2e.ps1` → 期望 ≥10 passed，记录用例名（现 10 条，F13）。
- [ ] `./scripts/verify.ps1` → EXIT=0。
- [ ] 秘密 grep 记录（`AKIA`、`aws_secret`、`api_key`、口令字面量；确认 `.env` 既不存在也未被跟踪）写入 `docs/evidence/day4-local.md`，履行 Day-3 计划 §6 的「附 grep 记录」。
- [ ] **S0-b…S0-g** 逐组 `git diff --cached --stat` 后再提交；提交信息**必须携带当时的实测数字**（否则入库后看不出交付时点状态）。
- [ ] 只在**最终 HEAD** 声明全绿；`docs/STATUS.md` 提交表下方写裁定 4 的披露原文（中间提交未逐个复验 + 11 路径点从未入库）。
- [ ] 回填合并契约冻结提交 ID 到 `docs/STATUS.md` 与 `docs/TASKBOARD.md`；Day-1 冻结 ID `94216df` 保留为历史冻结点，**不改写**。
- [ ] **不 `git push`**（无 remote，且需用户明确授权）。

## 3 并行实现（受 S0 与 C1 约束）

### 3.1 Backend（BE-05：访问控制补口）
- [ ] `api.py`：`secure` 改按请求 scheme（裁定 5），新增 `_cookie_secure(request)` helper；不动 `httponly`/`samesite`/`path`。
- [ ] `tests/test_auth.py`：补 `POST /api/runs/{run_id}/approval` 未登录 401、缺 CSRF 403、错 CSRF 403；补 `POST /api/logout` 未登录 401；补 scheme=https → 含 Secure 的配对断言（先红后绿，须做回退负向验证）。
- [ ] 不引入登录限速/会话 TTL（顺延，仅在 `STATUS.md` 未闭合缺口分列）。

### 3.2 OPS/Coordinator（OPS-04：部署前置材料）
- [ ] `scripts/deploy.ps1`、`scripts/cleanup.ps1`：按裁定 9 的 fail-closed 骨架与检查顺序；`-Apply` 需显式费用授权参数方可走到分支且仍先做 CLI/IaC 门。
- [ ] 自检：`Parser::ParseFile` 语法 lint + 空 env 干跑断言退出码 2（**不依赖真实 CLI**）。
- [ ] 修 F9：`pyproject.toml:18-19` 注释归真；修 F4：`docs/agents/infrastructure.md:17` 退出码语义分级、`infra/cloud-access-checklist.md:64-68` 命令块改「现状 + 目标」。
- [ ] 实跑并记录 `uv sync --frozen --extra bedrock --extra memory`（裁定 10）。
- [ ] 尽力项：`infra/` 纯文本 IAM/资源草案、费用表拆出公网 IP 与 ALB LCU 独立行、删除依赖顺序表、`preflight -Mode` 真实参数、`/readyz` 连通判据设计文档。

### 3.3 Frontend（FE-04：浏览器验收矩阵 + 标签证据驱动）
- [ ] `App.tsx`：裁定 13 的标签证据驱动改造；`api.ts` 若需暴露 `request_id` 判据则沿用已冻结字段，**不改契约模型**。
- [ ] 新增 6 条 e2e（裁定/门 G6，每条附「这不证明什么」注释）：`unauthorized deep-link returns to login`（A12 本地面）、`unknown device receipt shows 状态未知 and never success`（A10，现仅测 `failed`）、`reload while awaiting_approval keeps awaiting`、`desktop 1440px and narrow 390px have no overflow and state is not color-only`（T3 从未做，F13）、`raising daily dispensed shifts the proposed grams`（A14 浏览器半边，`local_fakes.py:101-105` 已具备由事实推导克数）、`new session rotates conversation and memory stays honestly unretrieved`（回归）。
- [ ] 沿用 `workers:1`、`expect.timeout`、各 spec 自复位；**禁止**在同一轮 e2e 声称重启恢复已验证（`webServer` 用内存库，F13）；禁止把 `local_fake` 写成真实模型；禁止用单浏览器冒充跨副本。

### 3.4 Coordinator（G3 裁定 + G7 守卫 + G9 文档）
- [ ] 健康检查端点硬裁定写入 `STATUS.md`/`infra/` 与 §7.5 手顺（裁定 7）。
- [ ] `tests/test_feedback_api.py`/`test_memory.py`：`available` 反伪造守卫测试（裁定 11）。
- [ ] `docs/STATUS.md` 新增 Day-4 三档表 + 本地/云端双列 + 提交表；`docs/evidence/day4-handoff.md`（按 `HANDOFF_TEMPLATE.md` 12 项，含「未运行的检查及原因」）、`day4-local.md`（命令/结果/**这不证明什么**）、`day4-cloud-blocked.md`（逐条列 F1/F5/F6 造成的阻断与各自解锁前提）；`docs/reviews/day4.md`（**非作者**只读审查）。Day-1/2/3 历史文档**只可追加后记，不改写**；但 `STATUS.md`/`TASKBOARD.md` 中「回填两个冻结 ID」的**预期句**按裁定 4 改为披露（属预期更正，非历史改写）。

## 4 串行临界段与执行顺序（单机现实，≤4 活动 Agent）

不可并行临界段：**C1** = `api.py`+`auth.py`+`tests/test_auth.py`（G2 与 G7 共享 `api.py`，须同批串行）；**C2** = `pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`+`scripts/*`；**C3** = `frontend/src/App.tsx`+`frontend/e2e/*`；**C4** = `STATUS`+`TASKBOARD`+`evidence`。

```
S0 基线入库（Coordinator，~2h，需用户在场）
G1 干净树全量回归实测（~1h）
G2 访问控制补口（Backend，~3h；C1）        ┐ 可与 G3 并行
G3 健康检查硬裁定 + G9 骨架文档（~1h）     ┘
G4 deploy/cleanup fail-closed 骨架（OPS/Coordinator，~3h；C2）
G5 镜像静态审读 + pyproject 修正 + 合并 extra 实测（~2h；C2）
G7 标签证据驱动 + available 守卫（Frontend+Coordinator，~2h；C1/C3）
G6 浏览器验收矩阵 6 条（Frontend，~4h；C3，G7 之后）
G9 文档四件套 + 上报（Coordinator，~2h；C4）
G8 非作者独立审查 + 修复 + 复跑（~2.5h）
```
合计 ≈ **20–23h 串行 Agent 工时**（= 全量 Day-4 **减去**一切云端项）。常驻 = Coordinator + Backend + Frontend（=3）；OPS 与 Reviewer 用空槽串行复用，**Reviewer 不得由作者充当**（`docs/agents/reviewer.md` L15）。派发前在 TASKBOARD 追加认领记录。新增任务行：`BE-05 访问控制补口`、`FE-04 浏览器验收矩阵与标签证据驱动`、`OPS-04 部署前置材料与 fail-closed 脚本`。

## 5 A01–A14 在 Day-4 的覆盖

| 编号 | Day-4 判定 | 说明 |
|---|---|---|
| A01/A02 正常·拒绝 | **回归必过** | Day-2/3 闭环 + approve/decline e2e 仍须全绿；`STATUS.md` 的 Day-3 门表须按 §3.4 与 skip 清单互引后重述 |
| A03 审批后事实变化 | **回归必过** | 零模型调用重评估不变 |
| A04 双批准 | **回归必过（同进程 + 两连接）** | **跨副本 = 条件项**；断言处必须紧贴一句「两 SQLite 连接 ≠ DynamoDB 两副本」 |
| A05 事件重传 | **回归必过** | 去重 + 不二次调模型 |
| A06/A07/A08 记忆三项 | **回归 + 守卫** | `available` 反伪造守卫为新增必过；真实 retrieve/提炼/冲突仍条件项，**不得声称通过** |
| A09 信息不足 | **回归必过** | 「未知事实显示未知」e2e 已有（`approve.spec.ts:81`） |
| **A10 失败/超时/迟到回执** | **补口必过** | 新增 `unknown receipt` 浏览器用例（现仅测 `failed`）；真异步迟到回执仍属已书面归约项 |
| A11 恶意指令 | **回归必过（本地）** | note/记忆文本注入仍被 policy/审批挡住；模型在环为条件项 |
| **A12 未授权** | **补口必过（不得记通过）** | 新增 approval/logout 401/403 + dist grep；限速/会话 TTL/默认口令三项列为**未闭合缺口**并接裁定 14 |
| **A13 重启/租约** | **回归必过 + 高报更正** | 落盘跨进程与 subprocess 恢复为已验证；`test_restart_subprocess.py:128-137` 的具名 skip 必须在门表**互引披露**（Day-3 的「✅ 通过」表述需加后记更正）；容器内重启 = 条件项 |
| **A14 随机改事实** | **补口必过（浏览器半边）** | 新增改事实→克数变化 e2e；真模型依据变化 = 条件项 |

SQLite/两连接/本地 e2e 的 PASS **不得**替代云测；Day-4 证据须把「本地通过」与「云端未验证」分列（沿用 `STATUS.md` 体例）。

## 6 完成的硬性证据（Definition of Done）

> 每项给**命令与实测数字**，不接受「全绿」二字。

- [ ] `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` → 通过数 = **184 + Day-4 新增数**（明列新增文件与用例名）；具名 skip 名单原样列出并解释每条等待条件；`ruff check .` 无告警。
- [ ] `uv run --frozen python scripts/export_contracts.py --check` → Contracts are current；**OpenAPI 仍恰为 14 条路径**、`domain.schema.json` 的 `$defs` **仍恰为** 6 输入模型 + `RunState`（Day-4 不应动契约；若某改动触发了契约变化，须回门 0 重议，**禁止**放宽 `tests/test_contracts.py:54-58` 的 `==` 断言）。
- [ ] `uv lock --check`；`uv sync --frozen --extra bedrock --extra memory` → exit 0（记录 resolved 包数，作为裁定 10 的部分实测）。
- [ ] `npm run typecheck`/`build` 通过；e2e **≥16 项**（Day-3 的 10 + 新增 6），列用例名与配置；`./scripts/verify.ps1` EXIT=0。
- [ ] **访问控制**：approval 的 401/403 与 logout 的 401 断言存在且**回退后转红**（负向验证）；scheme=https → 含 Secure 的配对断言存在；`frontend/dist` 与全仓凭据 grep **0 命中**记录在案。
- [ ] **反伪造守卫**：测试证明本地配置下无任何路径可把 `memory_status` 写成 `available`/`processing`；`search_owner_memory` 本地仍返回 `[]` 且**不记**证据。
- [ ] **fail-closed 脚本**：`deploy.ps1`/`cleanup.ps1` 在本机（无 CLI、无 IaC 源）实测输出 `NOT EXECUTED: …` 且**退出码 2**；语法 lint 无错误；文档中不存在承诺这两脚本已能 plan/apply 的句子。
- [ ] **健康检查裁定**：文档写明 LB/target group 与容器 HEALTHCHECK 一律 `/healthz`，并记录 `/readyz` 仍恒 503（`tests/test_app.py:17` 精确断言未放宽）。
- [ ] **文档一致性修正可核查**：`pyproject.toml:18-19` 假陈述已改；`docs/agents/infrastructure.md:17` 退出码语义分级；`infra/cloud-access-checklist.md:64-68` 命令块改为现状+目标；`docs/TASKBOARD.md` 的 OPS-01/02/03 三行补注「done 指计划与脚本准备，不含镜像构建与部署」。
- [ ] **S0 完成度**：分组提交序列落定、合并契约冻结提交 ID 已回填、F2/F3 两条披露已写入 `STATUS.md` 与 `TASKBOARD.md`。
- [ ] 文档：`STATUS.md` Day-4 三档表 + 本地/云端双列 + 提交表；`evidence/day4-handoff.md`（12 项）；`day4-local.md`（含「这不证明什么」）；`day4-cloud-blocked.md`（逐条阻断 + 解锁前提）；`reviews/day4.md`（**非作者**，逐条记「处理/复测」）；`TASKBOARD.md` 第 4 日派发与认领。Day-1/2/3 历史文档只可追加后记。
- [ ] 零副作用：无秘密入库（附 grep 记录）、**无云资源**、**无 AWS 费用**、无远程推送、**无镜像构建**（本机无 Docker，须明写「未构建」）、未以本地替身/stub/SQLite PASS/脚本文本存在冒充云端完成。

**禁止出现的表述**（文档/提交/前端文案，括号内为本次最易踩的触发点）：「HTTPS 演示可访问 / 已部署 / 演示已上线」（`cloud-access-checklist.md:64-68` 的目标命令被读成现状）；「可一键部署 / 一键清理」（`-Apply` 分支存在 + TASKBOARD 里 OPS 已标 done 的双重误导）；「镜像已构建 / 容器已验证 / HEALTHCHECK 已生效」（F1）；「访问控制通过 / A12 通过 / 会话安全已达标」（F12）；「已验证云端并发 / DynamoDB 条件写通过 / 跨副本上限生效 / 两副本双批准」（F13、两连接 ≠ 两副本）；「已实现记忆提炼轮询 / 反馈可进入 available」（F11）；「真实模型已参与分析 / 页面显示真实模型即为真实」（标签由配置推导）；「真实进程重启已验证（含分析中被 kill）」（skip 与 ✅ 并存）；「readyz 已就绪 / 已改健康检查使部署通过」；「CI 全绿 / 流水线已跑过 e2e / 已推远程」（F14，无 remote）；「契约冻结提交 ID 已回填两个 / 分组提交每步均已复验」（F2）；「24 案例集已通过 / 验收用例全覆盖」（用户未选 T6）；任何**预填**的费用金额/延迟/准确率/成功率；「本版本可作为参赛原型 / 发布候选」（总方案 L153）。

## 7 降级、关键路径与上报

### 7.1 关键路径
S0（~2h）→ G2 访问控制 → G4 fail-closed 脚本 → G7 标签与守卫 → G6 浏览器矩阵（~4h）→ G8 独立审查。**最易滑期**：6 条新 e2e 里的**视口溢出检查**（首次引入 1440/390 视口，样式缺陷会当场暴露并需 `styles.css` 修复）与 **`unknown` 回执用例**（前端「状态未知」渲染路径已有但 e2e 从未触发）。

### 7.2 降级预案
- **A** `Secure` 按 scheme 判定在 ALB 之后依赖 `X-Forwarded-Proto` 可信链路 → 若本地无法验证代理语义，则实现为「直连 scheme 判定 + 代理头读取按受信开关默认关闭」，并把代理场景记为「**已实现未验证**」，**不得**动契约。
- **B** deploy/cleanup 无法自证有效（无 CLI）→ 保底为「语法 lint + 空 env 干跑 exit 2」两证齐全即算 G4 通过，真实 plan 顺延；**不得**为凑通过而让脚本在无 CLI 时返回 0。
- **C** 视口 e2e 当日未收敛 → G6 降为「5 条必过 + 视口项记为滑期」，**不得**以「样式已响应式」推断代替浏览器证据。
- **D** 用户不在场无法完成 S0 → Day-4 其余门可先做，但 `STATUS.md` 必须标注「本轮数字基于**脏工作区**，S0 提交后须复跑」，且不得回填任何提交 ID。
- **E** 独立审查发现需要动契约才能修 → 暂停该项、回门 0 重议，不在当日随手改 `models.py`/`contracts/`。

### 7.3 需用户确认的点（已随本计划批准）
①裁定 4 的披露口径（只回填一个合并契约冻结 ID + 声明 Day-2 的 11 路径冻结点从未入库）替代 Day-3 计划 §2 与 `STATUS.md` 的双 ID 预期；②裁定 7 的健康检查硬裁定（LB→`/healthz`、`/readyz` 不为部署改码）；③裁定 14 把登录限速 / 会话 TTL / 默认口令强制覆盖列为**公网 HTTPS 部署前置硬门**，本轮只出议题不实现；④裁定 10 明确镜像在本机**完全不可解锁**（用户已裁定不装 Docker），构建验证需另找 Docker 环境或授权推送 CI；⑤S0 的逐组提交需用户在场授权，且本轮不推送远程。

### 7.4 上报的依赖冲突（不得静默吸收）
- **T6 与 Day-5 验收同源**：用户未选 24 案例集 + `evaluate.py`，而 Day-5 的「测试与评委自由输入」判据与该案例集同源（总方案 L138、任务单 L315-317）。不补做则 Day-5 该项只能降级表述为「人工现场脚本，无固定案例集量化报告」。请用户在 Day-5 开工前二选一：补做案例集，或接受降级并写入材料。
- **Day-5 容量**：Day-5 字面已含「冻结功能 + 评委自由输入 + 概念图 + 演示脚本 + 英文材料 + 录屏」（总方案 L104）。无账号期间被顺延的云端块（镜像、HTTPS、DynamoDB、真实 Bedrock/AgentCore）**压不进同一天**；账号就绪日应优先做「最小云端切片」（一次真实模型往返 + 一个 HTTPS 演示地址），材料按总方案 L155 的出口降级为「已录制片段 + 完整脚本」。
- **交付命名门禁**：无 AWS 验证时 Day-5 产物必须写作「**本地验证候选（非参赛版）**」（总方案 L153），Day-4 先把该命名写入计划以免 Day-5 误标。

### 7.5 账号就绪即执行手顺（成文但 Day-4 不执行）
`uv sync --frozen --extra bedrock --extra memory` → 设置 `AWS_REGION`/`BEDROCK_MODEL_ID`/`AGENTCORE_MEMORY_ID`/`DYNAMODB_TABLE_NAME` 与**短期凭据**（不落盘、不入仓）→ `./scripts/preflight.ps1` 只读段应显示凭据源存在 → `./scripts/bedrock-smoke.ps1`、`./scripts/agentcore-smoke.ps1`（**计费调用，须在已确认预算内**）→ 记录 `request_id`/event id/namespace/时间到 `docs/evidence/*-call-*.md` → `uv run --frozen pytest -m bedrock_live -m agentcore_live` → 修 `api.py:212` 与 `App.tsx:476` 前先做 `repo_dynamo`（同构实现 CAS/幂等/白名单/租约谓词）→ `mode=aws` 的 `main.py:82` raise 仅在 storage+model+memory **三项均实测连通**后移除，同时 `readyz` 才允许按真实判据上调 → `deploy.ps1 -PlanOnly` → 费用与删除清单确认 → `-Apply`。**每一步的失败都记录为真实失败，不回退替身。**
