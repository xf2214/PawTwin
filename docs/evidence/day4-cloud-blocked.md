# Day-4 云端被阻塞项（2026-09-29）

> **状态：全部未执行。** Day-4 的字面验收（总方案 L103「HTTPS 演示可访问；访问控制、刷新、重启和失败回执通过；可部署可删除」）经实测存在**四重独立阻断**，任一条都足以使「可部署/可访问」不成立：
>
> 1. **无 AWS 账号与凭据**（用户 2026-09-28 确认仍无，并已着手注册）；
> 2. **本机无 Docker / AWS CLI / CDK**（实测 `Get-Command` 三者均 CommandNotFound；用户已裁定**不安装 Docker**）；
> 3. **`infra/` 无任何 IaC 源**（仅两份 md），`deploy.ps1`/`cleanup.ps1` 为 fail-closed 门控，`-Apply`/`-Destroy` 明确未实现；
> 4. **`create_app` 对 `mode == "aws"` 无条件 `raise NotImplementedError`**（`backend/pawtwin/main.py:81-82`，并被 `tests/test_settings.py` 钉死）——这是**正确的 fail-closed 设计，不是缺陷**：`repo_dynamo` 未实现前移除它等于用 SQLite 冒充云端存储。
>
> 按总方案 L106/L153：**云端里程碑整体顺延并上报，Day-4 产物不得标为参赛完成**；无 AWS 验证时 Day-5 产物须命名为「**本地验证候选（非参赛版）**」。
>
> 本地通过与云端未验证**分列**：本地证据见 [day4-local.md](day4-local.md)。Day-3 的 12 项阻塞（M1–M12，见 [day3-cloud-blocked.md](day3-cloud-blocked.md)）**全部仍未解除**，本文件不重复计数，只记 Day-4 新增/推进的部分。

## 1 Day-4 新增的被阻塞项

| # | 检查项 | 对应验收/任务 | 阻塞原因 | 就绪后的最小验证 |
|---|---|---|---|---|
| N1 | `deploy.ps1 -PlanOnly` 产出**真实** plan（资源配置 + 费用清单） | 任务单 T7；总方案 L103「可部署」 | 阻断 1+2+3：无 CLI/CDK、无 IaC 源 | 先写 `infra/` 的 CDK/CFN 源 → 装 AWS CLI 与 CDK → `./scripts/deploy.ps1 -PlanOnly` 应产出经 `cdk synth`/`validate-template` 校验的配置与费用清单（**当前必然 `NOT EXECUTED`，退出码 2**） |
| N2 | `deploy.ps1 -Apply` 创建资源并给出 URL/镜像 digest/region/model id | 任务单 T7 | 同上 + 需用户对**具体资源与预算**书面授权 | `-Apply -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT`（脚本要求显式令牌）；把版本、digest、URL、测试时间写入 `docs/evidence/`，**不记口令与临时凭据** |
| N3 | `cleanup.ps1` dry-run 列出本项目 resource IDs → 按依赖删除 → 核对无残留 | 任务单 T7；总方案 L103「可删除」、L148 | 阻断 1+2+3；且从未部署过，无清单可列 | 部署后运行 `./scripts/cleanup.ps1`（默认 dry-run）→ 核对清单 → `-Destroy -ConfirmProjectId <id> -CostAuthorization …` → 逐项验证负载均衡/服务/镜像/日志/记忆/表**无残留** |
| N4 | 容器镜像构建（`--extra bedrock --extra memory`）、Linux 运行时、容器内 `/healthz`、静态页不覆盖 `/api`、worker 随 lifespan 启动、`HEALTHCHECK` 生效 | 任务单 T7 第 1 条 | 阻断 2（用户裁定不装 Docker） | 需**任一** Docker 环境：`docker build` → `docker run` → 容器内 `curl /healthz`、`GET /api/state` 401、`GET /` 返回构建后的 SPA、确认未知 `/api/*` 仍是 JSON 404。**替代路径**：授权创建远程仓库并推送，让 GitHub Actions 构建镜像（亦未验证，见 N8） |
| N5 | ALB/target group 健康检查指向 `/healthz` 后服务真的进入 healthy；`/readyz` 恒 503 不导致部署卡死 | 任务单 T7；Day-4 裁定 7 | 阻断 1+2+3 | 部署时把目标组健康检查配为 `/healthz`（**严禁**指 `/readyz`：它无分支恒 503，会让任务永不健康且表象被误读为镜像故障）；`/readyz` 上调为 200 的判据是 storage+model+memory **三项均实测连通**，届时才可改码 |
| N6 | 真实 HTTPS 下会话 cookie 带 `Secure`、CSRF 与 `SameSite` 行为、公网未登录访问被拒 | A12；任务单 T7「访问控制」 | 阻断 1+2+3+4（无证书、无公网地址） | 部署后：从未登录浏览器访问 → 401/登录门；登录后 DevTools 核对 cookie 的 `Secure`/`HttpOnly`/`SameSite=Lax`；经真实 TLS 终结（非 TestClient 的 scheme 伪造）复验。Day-4 已在本地把判据从 `mode` 改为**按连接 scheme**，但**本地无证书，不等于 HTTPS 已验证** |
| N7 | 双副本滚动发布下的 A04 双批准、跨副本并发上限、会话可用性 | A04；总方案 L71 | 阻断 1+2+3；且 `repo_dynamo` 未实现、会话仍在进程内存 | 需先实现 `repo_dynamo`（同构 CAS/幂等/白名单/租约谓词）+ 数据库级并发计数 + 会话持久化或粘性路由；否则两副本会**各自**计上限（全站实际 = 副本数×2）且跨副本请求 401 |
| N8 | GitHub Actions 远程运行（pytest/ruff/契约/typecheck/build/e2e + `uv lock --check`） | 工程基线 | 无 remote、未推送（需用户授权） | 授权创建远程并推送后观察首个 workflow；注意 CI **不装任何 extra**，故 `test_bedrock_adapter_offline.py` 在 CI 上仍 skip（与本机 192/10 的数字差异属依赖闭包不同，已在 day4-local.md §1 说明） |
| N9 | 真实 Bedrock 往返与 `request_id` 落库；真实 AgentCore strategy `ACTIVE` → submit → 轮询 → `available` | A01/A06；Day-3 的 M1/M2/M7 | 阻断 1 | 见 [day3-cloud-blocked.md](day3-cloud-blocked.md) 与 Day-4 计划 §7.5 手顺。**注意**：`MemoryService.get_status` 目前在生产端**无调用方**，`processing→available` 生命周期**未接线**（不是「已实现待验证」），账号就绪日需先接线再验证 |
| N10 | `repo_dynamo` 真表条件写/事务/幂等与 `PAWTWIN_MODE=aws` 启动 | A04/A05/A13；任务单 T1/T7 | 阻断 1+4；用户本轮**未选** `repo_dynamo` | 实现 `repo_dynamo` 并通过与 SQLite 同一组语义测试后，才可移除 `main.py:82` 的 raise；`aws_connected` 仍须等三项全连通才可为 True |

## 2 已就位但**未运行**的入口（编写完成不等于验证完成）

| 入口 | 当前实测结果 | 说明 |
|---|---|---|
| `scripts/deploy.ps1` | `-PlanOnly` → `NOT EXECUTED: aws CLI is not on PATH…`，**退出码 2** | 门顺序固定：CLI 存在性 → IaC 源存在性 → 必填参数 → 授权令牌；任一路径都**绝不调用 AWS、绝不 `exit 0`**；account id 仅运行期注入、绝不预填 |
| `scripts/cleanup.ps1` | 默认 dry-run → `NOT EXECUTED: aws CLI is not on PATH…`，**退出码 2** | `-Destroy` 另需 `-ConfirmProjectId` 与 `-CostAuthorization I-AUTHORIZE-BILLABLE-READ`；即便过门也明确「未实现」并以 2 结束，**拒绝伪造清理成功** |
| `scripts/agentcore-smoke.ps1` / `bedrock-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2** | 一旦运行会产生**计费**调用，须在用户授权预算内 |
| `scripts/preflight.ps1` | 退出码 **0**，但 `docker/aws available on PATH: False`、`credential source present: False`、Bedrock 与 AgentCore 两段均打印 `NOT EXECUTED` | 环境自检类脚本按裁定 8 恒 0 退出（否则「环境正常但无凭据」会被误报为预检失败）；**不得**由环境变量推断已连通 |
| `Dockerfile` | **未构建** | 两阶段构建、`npm run build`、`--extra bedrock --extra memory`、单进程 `--factory`、`HEALTHCHECK` 打 `/healthz`；已静态审读，容器内行为**零验证** |
| `tests/test_agentcore_live.py` / `test_bedrock_live.py` | **5 + 4 条具名 skip**（`BLOCKED: no AWS account is authorised…`） | blocked 被命名而非静默缺失（AGENTS.md L53） |

## 3 Day-4 在本地推进的「云就绪」部分（不是云验证）

- **cookie `Secure` 与 `mode` 解耦**：改为按请求 scheme（含 `X-Forwarded-Proto`，该头只能**加**不能**减** `Secure`），使未来 HTTPS 部署自动生效；本地 HTTP 仍省略。
- **健康检查端点硬裁定**：容器 `HEALTHCHECK` 与未来 LB/target group 一律 `/healthz`；`/readyz` 保持恒 503 且 `tests/test_app.py` 的精确断言**未放宽**（不为部署改状态码）。
- **部署/清理入口的 fail-closed 形态**已落地并可自检（语法 lint + 无 CLI 干跑断言退出码 2）。
- **依赖闭包部分实测**：`uv sync --frozen --extra bedrock --extra memory` 本机 exit 0（Audited 63 packages，无新增下载）；CI（无 extra）与镜像（两 extra）两闭包**互不覆盖**的缺口已在 `pyproject.toml` 注释中如实写明。
- **前端标签改为证据驱动**：无 `request_id`/无真实记忆证据时只显示「已配置，未经真实调用验证」，杜绝「配置即真实」的失真；`storage` 标签明写「`repo_dynamo` 未实现」。
- **`available` 反伪造守卫**：4 条测试（含 1 条静态字面量守卫）确保本地配置下没有任何路径能把 `memory_status` 写成 `available`/`processing`。

## 4 解除阻塞后的记账要求

1. 每一项从本文件移到 `docs/STATUS.md` 的「云端已验证」列，并附**实测**数字（不得填估算值、不得预填费用金额）。
2. 真实调用证据落 `docs/evidence/bedrock-call-<时间戳>.md` / `agentcore-call-<时间戳>.md`；部署证据须含版本、镜像 digest、region、model id、URL、测试时间，**不含**口令与临时凭据。
3. 若真实调用失败：如实记录失败与原因，**不得**用本地替身、`saved` 反馈或「脚本已存在」填补，也不得把该验收项标记为通过（总方案 L69）。
4. 账号就绪日的执行顺序见 [Day-4 开发计划](../plans/PawTwin_Day4_开发计划.md) §7.5：extras → 环境变量与短期凭据 → `preflight` → 两个 smoke（计费）→ live 测试 → `repo_dynamo` → 才可移除 `main.py:82` 的 raise 并上调 `readyz` → `-PlanOnly` → 费用与删除清单确认 → `-Apply`。
