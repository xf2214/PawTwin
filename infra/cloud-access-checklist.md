# OPS-01 云接入清单（仅计划，未执行）

> 状态：**未执行**。当前无 AWS 账号授权，未创建任何云资源，未调用任何收费模型，未产生费用，未远程推送。
> 本文是 Day-1 并行准备项，供账号就绪后按序核对；配置示例不证明服务已接通。编制日期：2026-09-23。

## 0 前置授权（缺失即停在“未执行”）

- [ ] 用户完成 AWS 注册、身份/付款验证、MFA、服务条款。
- [ ] 用户给出**具体预算上限**与**运行期限**，并确认资源清单。
- [ ] 用户提供本次赛事官方链接/规则（赛道、指定服务、时间限制、模拟边界）。
- [ ] 通过本机登录或临时角色授权开发；**不将长期密钥粘贴到聊天或写入仓库**。

在上述任一项缺失时，只做只读 preflight 并记录“未执行”，不 `apply`、不建资源、不调收费模型。

## 1 区域与模型

| 项 | 计划 | 未验证 |
|---|---|---|
| 首选区域 | `us-west-2`（先检查） | 服务/模型可用性需账号内实测 |
| 区域回退 | 若 Bedrock 模型或 ECS Express Mode 不支持，记录区域×服务×模型交集后再选，不硬编码账号 | 待实测 |
| Bedrock 模型 | 账号就绪后选定一个支持结构化输出/工具调用的模型 ID，写入 `BEDROCK_MODEL_ID` | 待选定 |
| 模型访问 | 在 Bedrock 控制台为该模型申请访问（model-access） | 待开通 |

## 2 权限（最小化，角色分离）

- **应用 Task Role**（运行时）：仅授权
  - `bedrock:InvokeModel*` 限定到**选定模型**的 ARN；
  - `dynamodb:` 读写限定到**本项目表**（含条件写/事务所需动作）；
  - `bedrock-agentcore:` 记忆读写限定到**本项目 memory**；
  - CloudWatch Logs 写入限定到本服务日志组。
- **镜像执行角色**与**基础设施/部署角色**分开；部署角色仅用于 CI/脚本，不进运行时。
- 不使用 `AdministratorAccess`，不使用通配 `*` 资源；所有资源带 `project` 标签。
- 口令/凭据只经环境变量或密钥服务注入，**不写入源码、前端、日志、镜像层**。

## 3 资源与预算清单（先估算，授权后才创建）

| 资源 | 规格计划 | 计费项 |
|---|---|---|
| ECS Express Mode 服务 | 默认 1 副本，允许滚动更新（短暂双进程） | Fargate vCPU/内存、负载均衡、公网 IP |
| 容器镜像 | 单镜像（页面+API+轻量 worker），ECR 托管 | ECR 存储/拉取 |
| DynamoDB | 单表，`PAY_PER_REQUEST`，条件写/事务与去重键 | 读写请求单元、存储 |
| AgentCore Memory | 单个 memory，按 owner/pet namespace 隔离 | 记忆存储/调用 |
| Bedrock | 每任务≤4 次调用、输出≤800 tokens、SDK 超时/重试 | 按 token 计费 |
| CloudWatch Logs | 保留 7 天，不写凭据/完整会话 | 日志摄取/存储 |

预算提醒**不是**硬性停费；应用限额也**不能**停止底层容器与负载均衡计费。默认不添加 NAT 网关或自定义域名。App Runner 对新客户关闭，不作为默认。

### 3.1 Bedrock 用量估算（Day-2 补）

**模型尚未选定，单价必须在账号就绪后于 Bedrock 控制台核实；本清单不预填任何价格数字，也不声称已算出具体金额。**

- 已落地的应用侧硬限额：每任务 ≤4 次模型调用（`PAWTWIN_MAX_MODEL_CALLS`）、单次输出 ≤800 tokens（`PAWTWIN_MAX_OUTPUT_TOKENS`）、单次分析 45 秒超时（`PAWTWIN_ANALYSIS_TIMEOUT_SECONDS`）、每任务 ≤2 次处理尝试（`PAWTWIN_MAX_ATTEMPTS`）、会话内 1 / 全站 2 并发（**仅进程内**）。超限一律 fail-closed，不回退替身。
- 输入侧量级：系统提示 ≈0.2k tokens + 事件数据 ≈0.1k + 四次只读工具返回 ≈0.3k ≈ **每次调用 0.6k 输入 tokens**。
- 按「每天 50 次演示分析」的**上限**：≤200 次调用、输出 ≤160k tokens、输入 ≤120k tokens。
- 实际预期远低于上限：本地替身为 **0 次**调用；真实模型通常 1–2 次调用即产出结构化结果，故日均更可能落在 50–100 次调用、≤40k 输出 tokens。
- 计费公式 = (输入 tokens × 模型输入单价) + (输出 tokens × 模型输出单价)。**在拿到实际单价前不给出金额**，避免用编造数字误导预算决策。
- 跨副本并发上限需要数据库级计数，Day-2 未实现；部署多副本前必须重新核算调用量上限。

## 4 部署与清理（Day-4 起为 fail-closed 门控脚本；脚本存在 ≠ 可部署）

现状命令（`scripts/deploy.ps1`/`scripts/cleanup.ps1` 已入库，但均为 fail-closed 门控：缺 AWS CLI/CDK、缺 IaC 源、缺必填参数/授权标记即打印 `NOT EXECUTED: <原因>` 并以退出码 2 结束，绝不调用任何 AWS API）：

```powershell
./scripts/preflight.ps1              # 只读环境自检（含 Bedrock/AgentCore 段），工具齐备时 exit 0，缺凭据逐段报 NOT EXECUTED
./scripts/deploy.ps1 -PlanOnly       # 当前必然 NOT EXECUTED：本机无 AWS CLI/CDK，且 infra/ 无任何 IaC 源
# 仅在用户对具体资源与预算确认后（且前两道门真实存在时）：
./scripts/deploy.ps1 -Apply -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT   # Day-4 明确未实现，即便过门也 exit 2
./scripts/cleanup.ps1                # 默认 dry-run；当前同样 NOT EXECUTED/exit 2（无部署记录可列）
```

目标命令（待真实实现，**不得被读成现状**）：`deploy.ps1 -PlanOnly` 产出经 `cdk synth`/CFN 模板的配置文件与费用清单；`-Apply` 在用户确认具体资源与费用后创建资源；`cleanup.ps1` 按下列顺序删除并验证无残留。

注意：`preflight.ps1` 当前**没有** `-Mode` 参数（早期文档承诺过，属 F4 失真，已在此修正）；它是只读自检，无凭据仍以 0 退出但逐段打印 `NOT EXECUTED`；与计费/资源类脚本（smoke/deploy/cleanup）的退出码语义分级见 `docs/agents/infrastructure.md`。

清理要求：先列出本项目拥有的资源，确认后按依赖删除（服务 → 负载均衡 → 镜像库 → 日志 → 记忆资源 → 表），验证负载均衡、服务、镜像、日志及记忆资源无残留；评审要求的可访问期间不自动关闭服务。

## 5 账号就绪后的最小云端验证（Day-2 起，不晚于 T7）

- [ ] 一次真实 Bedrock 工具往返，记录 request ID/时间。**入口已就位**：`./scripts/bedrock-smoke.ps1`（需先 `uv sync --frozen --extra bedrock` 并设置 `BEDROCK_MODEL_ID`/`AWS_REGION` 与已授权凭据）。无凭据时它输出「NOT EXECUTED」并以退出码 2 结束，**绝不虚报成功**；一旦运行即产生计费调用。
- [ ] 一次 DynamoDB 条件写入（去重语义），**不用 SQLite PASS 替代**。
- [ ] 一个 AgentCore memory strategy `ACTIVE` 检查。**入口已就位**：`./scripts/agentcore-smoke.ps1`（需先 `uv sync --frozen --extra memory` 并设置 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 与已授权凭据）。无凭据时它输出「NOT EXECUTED」并以退出码 2 结束，**绝不虚报已检索**；一旦运行即产生计费调用。提炼为异步，smoke 只做 submit + 一次 search，`available` 需另行验证轮询生命周期。
- [ ] 从未登录浏览器验证拒绝访问，再登录完成三场景。
- [ ] 证据写入 `docs/evidence/`，移除任何秘密；本地通过与云端验证**分列**。

只读前提核对：`./scripts/preflight.ps1` 现已输出 Bedrock 就绪度（后端、模型 ID/区域是否设置、`bedrock` extra 是否安装、凭据来源是否存在），全部只读、不发起任何 AWS 调用，也不由环境变量推断已连通。

## 6 实际状态

### Day-1（2026-09-23）

- 只读 preflight：**未执行**（无授权身份）。
- 创建资源：**无**。调用收费模型：**无**。费用：**无**。远程推送：**无**。
- 本地 Docker/AWS CLI 未在 PATH 中发现；镜像构建与 Linux/云端验证顺延到有账号与 Docker 环境时进行。

### Day-2（2026-09-25）

- 账号：**仍无**。因此本节全部云端验证项**依旧未执行**，`docs/evidence/day2-cloud-blocked.md` 逐项记录了阻塞原因。
- 已就位但未执行的入口：`scripts/bedrock-smoke.ps1` + `scripts/bedrock_smoke.py`（本次运行结果为 `NOT EXECUTED`，退出码 2）、`scripts/preflight.ps1` 的 Bedrock 只读段（输出 `credential source present: False`）。
- 依赖：`strands-agents==1.57.0` 已作为 **optional extra `bedrock`** 写入 `pyproject.toml` 与 `uv.lock`；`uv lock --check` 与 `uv sync --frozen --extra bedrock` 均已在本地验证可复现。**CI 与默认本地环境不安装它**，因此 bedrock 代码路径在 CI 中**未被执行**，属已命名的未覆盖面。
- 创建资源：**无**。调用收费模型：**无**。费用：**无**。远程推送：**无**。
- Docker：`Dockerfile` 已加 `--extra bedrock` 与 `PAWTWIN_WORKER_MODE=background`、并明确单进程；本机 PATH 仍无 Docker，**镜像未构建验证**。
- 部署/清理脚本（`deploy.ps1`/`cleanup.ps1`）：**仍未编写**，不提供伪装成功的空脚本；属 T7。

### Day-3（2026-09-26）

- 账号：**仍无**。故本节全部云端验证项**依旧未执行**，`docs/evidence/day3-cloud-blocked.md` 逐项记录阻塞原因（AgentCore 提炼/检索、场景 C 真实记忆影响、跨会话 retrieve）。
- 记忆后端：新增 `PAWTWIN_MEMORY_BACKEND=not_implemented|agentcore`（默认 local→`not_implemented`）。本地反馈**仅保存原文**（`memory_status=saved`），`search_owner_memory` 返回空且**不记** memory 证据，**绝不**以 `saved` 冒充「已提炼/已检索」（AGENTS.md L18）。
- 依赖：`boto3==1.43.102` 作为 **optional extra `memory`** 写入 `pyproject.toml` 与 `uv.lock`（boto3 本已是 strands-agents 的传递依赖，无新增下载）；`uv lock --check` 与 `uv sync --frozen --extra memory` 均已本地验证可复现（硬门通过）。**CI 与默认本地环境不安装它**，故 agentcore 代码路径在 CI 中**未被执行**，属已命名的未覆盖面。
- 已就位但未执行的入口：`scripts/agentcore-smoke.ps1` + `scripts/agentcore_smoke.py`（本次运行结果 `NOT EXECUTED`，退出码 2）、`scripts/preflight.ps1` 的 AgentCore 只读段（输出 `AGENTCORE_MEMORY_ID set: False`、`'memory' extra (boto3) installed: False`）。
- 创建资源：**无**。调用收费模型/记忆：**无**。费用：**无**。远程推送：**无**。
- Docker：`Dockerfile` 已加 `--extra memory`（与 `--extra bedrock` 并列）；本机 PATH 仍无 Docker，**镜像未构建验证**。

### Day-4（2026-09-29）

- 账号：用户已启动注册；截至本轮文档写入时本机仍 **无 AWS CLI、无凭据源**（`$HOME\.aws\credentials` 不存在、无凭据环境变量）。故本节全部云端验证项**依旧未执行**，逐条阻断与解锁前提见 `docs/evidence/day4-cloud-blocked.md`。
- 已入库的 fail-closed 入口：`scripts/deploy.ps1`、`scripts/cleanup.ps1`（语法 lint 0 错误；本机干跑 deploy 5 组合 / cleanup 4 组合实测 `NOT EXECUTED` + 退出码 2，零 AWS 调用。因无 AWS CLI 所有组合都停在 Gate 1，Gate 2–4 与「过门仍拒」路径仅经代码审读确认、未执行）。**脚本存在不等于可部署**：无 CLI、无 IaC 源、`-Apply`/`-Destroy` 未实现，三重前提均未满足。
- 依赖闭包部分实测：`uv sync --frozen --extra bedrock --extra memory` 本机 exit 0（镜像依赖闭包可复现从纯推断升为部分实测）；但 CI（无 extra）与镜像（两 extra）两闭包互不覆盖的缺口仍在；`uv lock --check` 同步通过。`pyproject.toml` 原「CI 与镜像默认都不装」假陈述已改正。
- 健康检查端点硬裁定：容器 `HEALTHCHECK` 与未来 LB/target group 一律 `/healthz`；`/readyz` 恒 503 只作诊断，不为部署改码。
- 创建资源：**无**。调用收费模型/记忆：**无**。费用：**无**。远程推送：**无**。镜像：**未构建**（用户裁定不装 Docker）。
