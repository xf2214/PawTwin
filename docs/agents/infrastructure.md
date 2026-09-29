# 云部署 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`，认领 OPS-01。当前没有 AWS 账号和部署授权。

先验证本地工具、容器构建与部署输入。默认设计为单容器 FastAPI/React、ECS Express Mode、Bedrock、DynamoDB、AgentCore Memory；执行时查官方当前可用性与实际区域/权限，不照搬历史服务假设。

交付可审查的角色权限、项目资源清单、具体费用估算、预检/部署/清理流程。先 plan-only，再在用户确认具体费用范围后 apply。现有 bootstrap 不包含真正可用业务，不能作为正式比赛网址对外发布。

不要改用户系统代理、全局工具或账号设置；缺 Docker/AWS CLI 时报告并给安装选择，不静默安装。不要索要聊天中的长期密钥。凭据通过本地登录或短期角色使用。

所有资源带项目标识，清理先列出精确资源再删除；预算提醒不等于停止计费。报告 Docker 构建和真实 AWS 验证是否实际运行。

## Day-2 派发（OPS-02）

当日分解见 `docs/plans/PawTwin_Day2_开发计划.md`。认领 OPS-02：`bedrock` **optional extra**（钉版本、不进 `dependencies`）+ `uv.lock` 同批提交、CI 增 `uv lock --check`（`uv sync --frozen` **不校验锁新鲜度**，漏提交锁会「绿着漏装」再变成 ImportError）、`Dockerfile` 加 `--extra bedrock` 与 `PAWTWIN_WORKER_MODE=background` 并保持**单进程**、`.env.example`/`.gitignore(*.db)`/README 同步、`preflight.ps1` 的 Bedrock 只读段与 `bedrock-smoke.ps1`、`infra/cloud-access-checklist.md` 的用量估算。

硬门：先单独提交依赖与锁并验证 `uv sync --frozen --extra bedrock` 可复现；失败则完全不动依赖/CI/Dockerfile。本机无 Docker，Dockerfile 改动只能声明「已修改、**未构建验证**」，不得声称镜像已构建。退出码语义分级（Day-4 裁定 8，修正本文件早期笼统要求）：**环境自检类**（`preflight.ps1`）只读、不发起任何 AWS 调用，在依赖工具（git/uv/Node）齐备时以 0 退出但逐段打印 `NOT EXECUTED`，绝不由环境变量推断已连通（工具缺失时它以异常终止，属环境前置未满足，不是云未验证）；**计费/资源类**（`bedrock-smoke`、`agentcore-smoke`、`deploy`、`cleanup`）fail-closed，缺前提即打印 `NOT EXECUTED` 并以**退出码 2** 结束，绝不 `exit 0` 报成功。不 apply、不建资源、不调收费模型。

## Day-3 派发（OPS-03）

当日分解见 `docs/plans/PawTwin_Day3_开发计划.md`。认领 OPS-03：`memory` **optional extra**（`boto3`，钉已锁定版本、不进 `dependencies`；boto3 本已是 strands-agents 传递依赖，无新增下载）+ `uv.lock` 同批提交；CI 的全局 `uv lock --check` 已覆盖该 extra（无需新装）；`Dockerfile` 加 `--extra memory`（与 `--extra bedrock` 并列）并保持单进程；`.env.example` 补 `PAWTWIN_MEMORY_BACKEND`/`AGENTCORE_MEMORY_ID` 说明；`preflight.ps1` 增 AgentCore 只读段；新增 `scripts/agentcore-smoke.ps1` + `scripts/agentcore_smoke.py`；`infra/cloud-access-checklist.md` 补 AgentCore 最小验证与 Day-3 状态；README 与角色简报同步。

硬门：先单独验证 `uv lock --check` 与 `uv sync --frozen --extra memory` 可复现（本次已通过）；失败则完全不动依赖/CI/Dockerfile，仅保留 `MemoryService` 接口 + 延迟导入 + 缺依赖/凭据映射为 `not_implemented`（绝不伪造记忆）。本机无 Docker，Dockerfile 改动只能声明「已修改、**未构建验证**」。`agentcore-smoke` 属计费/资源类，无凭据必须报「NOT EXECUTED」并以退出码 2 结束（`preflight` 按上文分级为只读自检、恒 0 退出），**不得**由环境变量推断已连通或检索成功。不 apply、不建资源、不调收费记忆。

## Day-4 派发（OPS-04：部署前置材料与 fail-closed 脚本）

当日分解见 `docs/plans/PawTwin_Day4_开发计划.md`。已交付：`scripts/deploy.ps1` + `scripts/cleanup.ps1` 为 **fail-closed 门控脚本**（裁定 9）——检查顺序固定为 CLI 存在性 → IaC 源存在性 → 必填参数/授权标记，任一缺失打印 `NOT EXECUTED: <原因>` 并退出码 2，绝不调用任何 AWS API、绝不 `exit 0`；`-PlanOnly` 的含义是「只 plan 不 apply」，**不承诺必然有 plan 输出**（无 CLI/无 IaC 源时不产出任何 plan）；`-Apply`/`-Destroy` 另需显式授权标记且当日明确「未实现」。account id 仅运行期注入、绝不预填。自检方式与覆盖面（G8 审查后更正措辞）：`Parser::ParseFile` 语法 lint（0 错误）+ 本机干跑 deploy 5 组合 / cleanup 4 组合全部实测 `NOT EXECUTED` + 退出码 2——但因本机无 AWS CLI，**所有组合都停在 Gate 1**；Gate 2（IaC 源）/ Gate 3（必填参数）/ Gate 4（授权令牌）与「过门仍拒」两条路径**仅经代码审读与语法 lint 确认，从未被执行**，其解锁前提是安装 AWS CLI/CDK。另：PowerShell 参数绑定错误（如未知开关）在主体运行前终止，退出码为 1 而非 2，属已知边界。**脚本存在 ≠ 可部署**：本机仍无 AWS CLI/CDK/Docker，真实 plan/apply 顺延至账号与工具就绪日（§7.5 手顺）。

健康检查端点硬裁定（裁定 7）：容器 `HEALTHCHECK` 与未来 ALB/target group **一律用 `/healthz`**；`/readyz` 恒 503 只作人工诊断读取，**严禁**为让部署走完而改码（`tests/test_app.py` 的 503 精确断言不放宽）。
