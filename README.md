# PawTwin

宠物照护 Agent 项目，面向 AWS 黑客松原型开发。产品范围为一只宠物、一个家庭、一个网页和一个照护 Agent。

**Day-1 本地核心已实现并通过检查**：在骨架（运行环境、共享契约、多 Agent 协作入口）之上，已落地演示登录/会话/CSRF、事件摄入与去重、SQLite 持久化、硬性策略、审批状态机、模拟执行与回执，以及拒绝闭环（浏览器 e2e + 集成测试双证据）。

**Day-2 已把分析器真正接线并补上可靠性与证据**：分析器 seam（`inline` / `local_fake` / `bedrock` 三后端，可切换且不静默互相回退）、可领取状态白名单 + 租约续约 + 状态 CAS + 尝试上限、45 秒分析超时与「每任务 ≤4 次模型调用 / ≤800 输出 tokens」的 fail-closed 限额、后台 worker、`demo/facts` 与 `demo/device-mode` 现场注入、可持久化的证据台账与调用遥测、OpenAPI 错误响应补全，以及浏览器 approve 闭环 e2e。**真实 Bedrock 推理仍未执行（无 AWS 账号），AgentCore 记忆、DynamoDB 真表与 AWS 部署仍待后续开发**；本地通过与云端未验证分列，不能将此版本作为完整参赛原型。详见 [当前状态与验证](docs/STATUS.md)。

**Day-3 已接入记忆抽象层、主人反馈与可靠性升档**：`memory.py`（`MemoryService` seam + 诚实本地后端 + AgentCore 骨架 + 离线 stub）、`POST/GET /api/feedback`（原文入库、幂等去重、`memory_status` 诚实为 `saved`）、`POST /api/demo/new-session`（轮换 `conversation_id`、保留记忆/事实/登录）、`search_owner_memory` 接线（本地返回空、不伪造证据）、worker 由顺序 drain 改为有界线程池真并发（准入上限获得生产触发路径）、跨进程双批准（文件库两连接 + WAL）与真实 OS 进程重启复验、前端记忆区。**真实 AgentCore 提炼/检索与场景 C「记忆改变建议」仍未执行（无 AWS 账号），DynamoDB 真表、跨副本多 replica 与部署仍待 Day-4**；本地通过与云端未验证分列。详见 [当前状态与验证](docs/STATUS.md)。

## 快速入口

- [当前状态与验证](docs/STATUS.md)
- [Agent 协作规则](AGENTS.md)
- [任务看板](docs/TASKBOARD.md)
- [各角色起始任务](docs/agents/README.md)
- [五日产品方案](docs/plans/PawTwin_五日开发总方案.md)
- [完整实施任务单](docs/plans/PawTwin_Agent_实施任务单.md)
- [本次初始化范围](docs/INITIALIZATION.md)

## 环境

- Python 3.12 与 uv。
- Node.js 24 推荐；npm 用于锁定前端依赖。
- PowerShell 用于仓库提供的 Windows 脚本。
- 本地初始化不需要 AWS 账号、AWS CLI 或 Docker。

本机系统 Node 版本较旧时，脚本优先使用可用的兼容版本；可通过 `PAWTWIN_NODE_DIR` 指定包含 node 的目录。Codex 运行时仅作本机便利选项，项目不依赖用户绝对路径，另一台机器正常安装 Node 24 即可。

## 本地启动

在项目根目录执行：

```powershell
./scripts/preflight.ps1
./scripts/setup.ps1
./scripts/dev-backend.ps1
```

保留后端终端，在另一个终端运行：

```powershell
./scripts/dev-frontend.ps1
```

开发页面默认 `http://127.0.0.1:5173`（Vite 代理 `/api` 到 `:8000`），后端默认 `http://127.0.0.1:8000`（同源服务已构建的 `frontend/dist` 与 API）。端口被占用时应更改配置或停止自己启动的进程，不终止其他任务的服务。页面从真实 `/api/state` 显示模式与业务状态（`/api/bootstrap` 仅为非敏感骨架状态，不作业务源），不生成虚假业务结果。登录口令取自 `PAWTWIN_DEMO_PASSPHRASE`（本地默认值为非秘密演示门禁；评委口令经私有测试说明交付，不写入公开源码）。

配置字段参见 `.env.example`。启动参数与环境变量以 `backend/pawtwin/config.py` 为准；不要假设配置示例已设置到环境中，更不要把凭据写进前端。

## 验证

```powershell
./scripts/verify.ps1
```

脚本检查后端测试、静态检查、契约是否需要重新导出、前端类型和构建。浏览器 smoke 另外在项目根目录执行：

```powershell
./scripts/test-e2e.ps1 -InstallBrowser
```

脚本使用与开发脚本一致的兼容 Node。首次安装 Chromium 会下载测试浏览器；不安装或修改用户的桌面浏览器。已安装后可省略 `-InstallBrowser`。具体本机已执行的结果见状态文档。

浏览器 e2e 直指后端同源 `http://127.0.0.1:8000`（`main.py` 服务已构建的 `frontend/dist` 与 API，无需 Vite preview/proxy）；运行前先 `npm run build`（`scripts/test-e2e.ps1` 会自动构建）。受限网络下已有可用 Chromium 时可将 `PAWTWIN_BROWSER_EXECUTABLE` 设置为其可执行文件绝对路径；默认仍使用 Playwright 管理的浏览器。测试不会复用或终止其他任务的服务；后端 8000 须空闲。

## API 与共享契约

- `/healthz`：进程存活，不调用 AWS。
- `/readyz`：仍返回 degraded/503，但按组件诚实报告——`reason=cloud_adapters_not_verified`，并分列 `business`/`model`/`storage`/`memory`/`cloud`。本地业务闭环已就绪，缺的是任何经验证的云端适配器；继续报「业务未就绪」同样是失真。
- `/api/bootstrap`：不含秘密的骨架状态（`stage`/`capabilities`/`analyzer`），仅供连接验证，非业务源。
- 业务路由（需登录；写操作需 CSRF）：`POST /api/login`、`POST /api/logout`、`GET /api/state`、`POST /api/events`、`GET /api/runs/{run_id}`、`POST /api/runs/{run_id}/approval`、`POST /api/feedback`、`GET /api/feedback/{feedback_id}`、`POST /api/demo/facts`、`POST /api/demo/device-mode`、`POST /api/demo/new-session`。未授权返回 401，CSRF 失败返回 403；这些错误响应已在 OpenAPI 中显式声明。
- `GET /api/runs/{run_id}` 返回 `evidence`（工具名/来源/检索时间/摘要）与 `telemetry`（后端、模型调用次数、输出 tokens、耗时、`request_id`），以及 `policy_reason`/`failure_reason`。无真实云调用时 `request_id` 为 `null`，页面如实显示「无（未发生真实云调用）」。
- `POST /api/events` 的返回状态取决于 `PAWTWIN_WORKER_MODE`：`background` 返回 `queued` 由 worker 处理，`inline` 返回受理后的当前状态。
- `contracts/openapi.json`：当前真实路由（14 条路径，含上述业务、反馈与 demo 路由）。
- `contracts/domain.schema.json`：**恰为** 6 个输入模型 + `RunState`；公开响应 DTO 只出现在 OpenAPI，不进领域 schema。

`demo/facts` 只能修改 `last_fed_minutes_ago` 与 `daily_dispensed_grams`（或把它们置为「未知」以触发 `NEEDS_INFO`）；日配额、单次上限与最短间隔是硬性限制，**不在请求模型内**，任何请求都无法修改。`demo/device-mode` 只影响之后的新命令、仅存于进程内、重启复位。`POST /api/feedback` 保存主人反馈原文（以 `Idempotency-Key` 头幂等去重），本地 `memory_status` 恒为 `saved`（原文已存业务库）、**绝不**谎报 `available`；`GET /api/feedback/{feedback_id}` 回读该状态；`POST /api/demo/new-session` 轮换 `conversation_id` 而保留登录/事实/记忆。真实 AgentCore 提炼与检索为条件项（无账号），不会用返回成功的空接口冒充实现。Python 模型是契约来源，生成文件不要手动修改。修改模型后运行导出工具并纳入同一个审查提交。

```powershell
uv run --frozen python scripts/export_contracts.py
uv run --frozen python scripts/export_contracts.py --check
```

领域 schema 表达基础类型与范围；动作类型和投喂克数的组合约束由 Python 模型校验，消费者仍须以服务端验证结果为准。

## 多 Agent 如何开始

把本文件所在目录作为项目根目录。先让后端 Agent 执行 BE-01 冻结业务接口，再并行推进前端和 AI 工具。每个 Agent 使用独立工作树/分支，并读取对应角色入口。总负责人独占共享契约、依赖锁和集成记录。

当前基线分支为 `chore/bootstrap`，没有配置远程仓库。新 Agent 从已通过验证的提交开始，不直接在其他 Agent 的检出目录切换分支。

## 真实与模拟边界

PawLink 项圈是概念；传感器事件与喂食设备是模拟对象。真实 AgentCore 长期记忆的提炼/检索与部署尚未验证（无账号）；主人反馈原文本地真实入库，但本地**不提炼**为长期记忆。真实 Bedrock 推理与 AgentCore 记忆的适配器已写好但**未经真实账号验证**。`aws` 模式会明确拒绝启动，直至后续任务提供真实适配器与验证；配置齐全也不能被误认为已经连接 AWS。

分析后端与存储分别标注：页面同时显示 `analyzer`（`inline`/`local_fake`/`bedrock`）、`storage`（`sqlite`）与 `memory`（`not_implemented`）。`aws_connected` 只有在存储、模型与记忆**都**真实连通时才为真，因此「analyzer=bedrock 且 aws_connected=false」是诚实表述而非矛盾。

真实模型调用需要安装可选依赖并具备凭据：`uv sync --frozen --extra bedrock`，然后设置 `BEDROCK_MODEL_ID`/`AWS_REGION` 与一个已授权的凭据来源。缺失时不会回退到替身，而是让该次分析显式失败（`BACKEND_UNAVAILABLE`）。`scripts/preflight.ps1` 只读核对这些前提，`scripts/bedrock-smoke.ps1` 在无凭据时输出「NOT EXECUTED」并以非零码退出，绝不虚报成功；它一旦运行就会产生**计费**调用。真实 AgentCore 记忆同理：`uv sync --frozen --extra memory` + 设置 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 与凭据；缺失时 `search_owner_memory` 失败关闭（`MEMORY_UNAVAILABLE`）而非伪造记忆，`scripts/agentcore-smoke.ps1` 无凭据时输出「NOT EXECUTED」并以退出码 2 结束。

云端资源创建、费用和对外发布均未执行。Dockerfile 为后续部署准备（已加 `--extra bedrock --extra memory` 与单进程说明），但本机无 Docker，**镜像未构建验证**；实际是否构建通过以状态文档为准。
