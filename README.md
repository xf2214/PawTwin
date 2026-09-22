# PawTwin

宠物照护 Agent 项目，面向 AWS 黑客松原型开发。产品范围为一只宠物、一个家庭、一个网页和一个照护 Agent。

**项目骨架已初始化并通过本地检查**：提供运行环境、共享数据模型、前后端连接检查和多 Agent 协作入口。完整照护流程、登录、数据库、Bedrock、AgentCore Memory 和 AWS 部署仍待后续开发，不能将此版本作为完整参赛原型。

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

开发页面默认 `http://127.0.0.1:5173`，后端默认 `http://127.0.0.1:8000`。端口被占用时应更改配置或停止自己启动的进程，不终止其他任务的服务。页面由实际 `/api/bootstrap` 响应显示连接状态，不生成虚假业务结果。

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

测试默认使用前端端口 4173、后端端口 8000。前端测试端口被占用时可设置 `$env:PAWTWIN_E2E_PORT = '4174'`；受限网络下已有可用 Chromium 时可将 `PAWTWIN_BROWSER_EXECUTABLE` 设置为其可执行文件绝对路径。默认仍使用 Playwright 管理的浏览器。测试不会复用或终止其他任务的服务；后端 8000 须空闲。

## API 与共享契约

- `/healthz`：进程存活，不调用 AWS。
- `/readyz`：初始化阶段返回 degraded/503，表示业务尚未就绪。
- `/api/bootstrap`：不含秘密的开发状态，仅用于前后端连接验证。
- `contracts/openapi.json`：当前真实路由。
- `contracts/` 下领域模型 schema：后续 Agent 共享的数据边界。

完整业务接口仍属于计划；不会用返回成功的空接口冒充实现。Python 模型是契约来源，生成文件不要手动修改。修改模型后运行导出工具并纳入同一个审查提交。

```powershell
uv run --frozen python scripts/export_contracts.py
uv run --frozen python scripts/export_contracts.py --check
```

领域 schema 表达基础类型与范围；动作类型和投喂克数的组合约束由 Python 模型校验，消费者仍须以服务端验证结果为准。

## 多 Agent 如何开始

把本文件所在目录作为项目根目录。先让后端 Agent 执行 BE-01 冻结业务接口，再并行推进前端和 AI 工具。每个 Agent 使用独立工作树/分支，并读取对应角色入口。总负责人独占共享契约、依赖锁和集成记录。

当前基线分支为 `chore/bootstrap`，没有配置远程仓库。新 Agent 从已通过验证的提交开始，不直接在其他 Agent 的检出目录切换分支。

## 真实与模拟边界

PawLink 项圈是概念；传感器事件与喂食设备是模拟对象。AWS 推理、记忆和部署尚未实现。`aws` 模式会明确拒绝启动，直至后续任务提供真实适配器与验证；配置齐全也不能被误认为已经连接 AWS。

云端资源创建、费用和对外发布均未执行。Dockerfile 为后续部署准备，实际镜像是否构建通过以状态文档为准。
