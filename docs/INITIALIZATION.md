# 项目初始化范围

用户在 2026-09-19 请求初始化项目，以便多个 Agent 后续开发。此次仅建立工作基线，不执行完整五日计划。

## 本次验收

- 独立 Git 仓库，初始分支 chore/bootstrap；无远程推送。
- Python 3.12 + uv + FastAPI 最小后端，healthz、readyz 与非敏感 bootstrap 状态。
- React + TypeScript + Vite 可启动页面，显示开发阶段和真实连接状态。
- 本地和 AWS 模式边界：未实现的 AWS 模式必须明确失败，不能伪装成功或自动使用替身。
- 共享数据模型与 OpenAPI 导出；业务路由仅在契约中标注 planned，不暴露无身份校验的业务接口。
- 锁定依赖、配置示例、启动与验证脚本、CI、Docker 构建文件。
- AGENTS.md、文件所有权、任务看板、交接模板、各角色起始指令和原计划副本。
- 实际通过后端测试、前端类型与构建检查，以及本地页面/API 联通检查。

## 本次不实现

数据库适配器、审批/策略状态机、模拟设备业务、模型工具、长期记忆、登录系统、AWS 资源和部署。页面不能出现虚假的已喂食、已学习或已连接 AWS 状态。

## 文件所有权

初始化实现 Agent：backend/、tests/、frontend/、contracts/、pyproject.toml、uv.lock、.python-version、.env.example、Dockerfile、.dockerignore、scripts/ 中实现脚本。

总负责人：README.md、AGENTS.md、docs/、.github/、根级版本控制约定。

独立审查 Agent：只读，不改文件；向总负责人报告可复现发现。

## 接口与实现顺序

初始化骨架先固定基础模型与非业务状态 API。完整业务接口待后端任务冻结，前端和 AI Agent 可按书面契约开发但不得自行篡改共享模型。生成契约的唯一来源为 Python 数据模型；生成文件不得手工修改。

## 裁定

- 原计划覆盖完整产品，本次授权范围只有初始化，不将 T1–T8 自动执行。
- 这是新建的独立项目目录，没有原有分支或代码需要隔离。当前使用专用 chore/bootstrap 分支；后续每个开发 Agent 从同一通过验证的提交建立独立工作树。
- 云端部署和业务端点未实现时，readyz 必须呈现 degraded，不对评委声称可用产品。
- 当前系统 Node 22.11 低于新版 Vite 要求。优先使用已提供的兼容运行时，只调整项目脚本进程 PATH，不修改系统 Node 安装。
