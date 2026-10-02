# Day-5 云端阻断项（逐条 + 解锁前提）— 2026-09-30

> Day-5 是「真实部署专日」，但**AWS 凭据仍缺失**（实测：无 `~/.aws/credentials`、`config`，无 `AWS_*` 环境变量，`aws sts get-caller-identity` → `Unable to locate credentials`；即计划事实 **G-A**）。计划已**终止双轨**，替身不得充当验收凭据，因此下列真实云门**全部未闭合**，逐条具名。按裁定 19，任一项未闭合 → 产物继续命名「**本地验证候选（非参赛版）**」，**不得**写作「AWS 已验证」。

**统一解锁前提（P0 用户节点）**：①用户在本机注入**短期**凭据（不入聊天/`.env`/仓库/镜像层/日志）；②用户在 GitHub 建**私有**仓库并给出 `owner/repo` + 授权推送范围（本机无 `gh`，无法自建）；③`scripts/aws_probe.py` 只读探测后由用户确认**区域/模型 ID**（只进 `.env`）；④`infra/cost-estimate.md` 实价 + 用户对**预算上限与运行期限**的**书面确认**（`AGENTS.md` L69，`-Apply` 硬门）。

| 门 | 内容 | 状态 | 阻断原因 | 解锁前提 |
|---|---|---|---|---|
| **G0** | 只读云就绪门（caller identity、区域可达、`list_memories`、可访问模型清单；零计费，产出 `day5-cloud-probe.md`） | ⛔ 未执行 | 无凭据 | P0①③；`aws_probe.py` 已就绪，注入凭据即可跑（只读、不调 `Converse`/`InvokeModel`） |
| **D1′** | `repo_dynamo` **真表** `dynamodb_live` 全套（去重、CAS 双批准恰一次执行+一次记账、租约白名单穷举、`UNSET`/NULL、`facts_version` 原子自增、`available` 不变式） | ⛔ 12 项具名 skip | 无真表、无凭据 | P0①④ + `deploy_plan.json` 建表（`pk/sk`+`entity-index`，`PAY_PER_REQUEST`）；`PAWTWIN_DYNAMODB_TABLE_NAME` 注入后 `pytest -m dynamodb_live` |
| **G3** | 云装配真实标签（`mode=aws` 可启动、探活通过、`aws_connected`/`readyz`/`storage`/`bootstrap` 真实） | ⚠ 代码就绪，**未云验证** | 无凭据（离线仅证「无凭据→拒启」的 fail-closed 分支） | P0①④ + 真表 + 真 memory；`create_app(mode=aws)` 探活通过后可见真实标签 |
| **G4** | 公网三门 + `/api/login` 429 契约 | ⚠ **本地已实现并测**，公网真实面未验 | 无 HTTPS 部署 | G7 部署后：真实 HTTPS 下 401/403/429、`Set-Cookie` 含 `Secure`、伪造 `X-Forwarded-Proto` 定论 |
| **G5** | AgentCore 数据面真实往返（`CreateMemory`→strategy `ACTIVE`→提交→轮询→**真实 record id 检索**） | ⛔ 5 项具名 skip | 无凭据；响应字段/状态词表未核实 | P0①④ + `CreateMemory` 并**等 strategy ACTIVE**（裁定 13，ACTIVE 前提交的 event 永不提炼）；`pytest -m agentcore_live` |
| **G6** | GitHub Actions **真实构建并推送镜像到 ECR**（记 digest/尺寸/扫描状态） | ⛔ 未运行 | 无 GitHub remote、无 Docker、workflow 从未触发 | P0②（私有仓 + OIDC role）→ 手动 `workflow_dispatch` `image.yml`；本机无 Docker 故只能远程构建 |
| **G7** | 真实 `plan` + 费用实测 + 用户书面确认 + `-Apply` → `https://<svc>.ecs.<region>.on.aws` 可访问、`/healthz` 生效 | ⛔ 未执行（`-PlanOnly` 为离线 plan，未 apply） | 无凭据、无预算确认、无镜像 | P0①②③④ 全备 + G6 镜像已推 ECR + `infra/cost-estimate.md` 实价 + 用户书面预算/期限确认 → `deploy.ps1 -Apply -CostAuthorization I-AUTHORIZE-BILLABLE-DEPLOYMENT` |
| **G8** | 部署面 A01–A14 真实子集 | ⛔ 未执行 | 依赖 G7 部署 | G7 后按 §6 判定逐项实测（A04 单 task 必过、**跨副本不作必过**，裁定 15） |
| **G9** | 24 案例集在**真实模型**上跑完并如实出报告 | ⛔ 未执行（`evaluate.py` + `scenarios.json` 已就绪） | 无部署、无凭据 | G7 后 `evaluate.py --base-url https://<svc>...`（口令从环境变量）；记忆案例受 G-I 异步时效约束，超时如实记 TIMEOUT |
| **G10** | `cleanup.ps1` dry-run→按依赖删除→**读回零残留** | ⛔ 未执行（`cleanup_aws.py` 已就绪，无 state 故 dry-run 亦 `NOT EXECUTED`） | 无部署（无 `deploy_state.json`） | G7 部署并演示期结束后 `cleanup.ps1 -Destroy -CostAuthorization I-AUTHORIZE-BILLABLE-READ`，逐类读回不存在 |
| **G11** | 非作者独立审查 + 证据四件套 | ⚠ 进行中 | — | 本轮以 CodeReview 子代理做**非作者**审查，结论记入 `reviews/day5.md` |

## 降级预案触发情况（计划 §8.2）

- 未触发 A（Express 不可用）/B（模型无能力）/C（strategy 不进 ACTIVE）/D（无 IAM 权限）/E（费用取不到）/G（配额）——**因为这些都需要真实账号才能判定**，当前一律停在「无凭据」这一上游阻断。
- **触发 F**：任一必过云门未闭合 → 产物回到「**本地验证候选（非参赛版）**」命名，本文逐条列阻断与解锁前提，Day-6 材料如实引用。

## 已实现但**未云验证**（不以「已实现」冒充「已验证」）

`repo_dynamo.py`（真表条件写/事务）、`agentcore_client.py` 三方法（真实响应形状）、`memory.py` 两段式轮询、`worker.py` `MemoryPoller`、`main.py` aws 装配与探活、`scripts/deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py` 的 apply/destroy/probe 路径、`Dockerfile`（未构建）、`.github/workflows/image.yml`（未运行）、`scripts/evaluate.py`（未对真机跑）。这些**离线可判定的部分**（协议集合守卫、fail-closed 分支、契约、plan 纯函数、命名跨源一致性、前端标签守卫、场景集结构）已测；**云端行为一律待凭据**。
