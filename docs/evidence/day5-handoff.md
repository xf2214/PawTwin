# Day-5 交接（离线实现切片）— 2026-09-30

承接 [Day-5 开发计划](../plans/PawTwin_Day5_开发计划.md) 与 [Day-4 完成记录](../STATUS.md)。本轮 = 用户裁定「先做全部离线实现」，完成 Day-5 计划中一切**不需凭据**的代码与离线测试（提交序列 D1–D8 的编码部分）；真实云门因**无凭据**未执行，见 [day5-cloud-blocked.md](day5-cloud-blocked.md)。

## 1 一句话结论

Day-5 的**离线实现全部落地并本地全绿**（`verify.ps1` EXIT=0、pytest **232 passed**、e2e **16 passed**、契约 **14 路径 current**、ruff 干净、`uv.lock` 未动）；**真实云验收（G0/D1′/G5/G6/G7/G8/G9/G10）无一闭合**，故产物命名仍为「**本地验证候选（非参赛版）**」（裁定 19）。

## 2 改动清单（按临界段，均未提交）

- **C1**：`backend/pawtwin/repo_dynamo.py`（新）、`repository.py`（`agentcore_session_id` + `set_feedback_status` 扩展 + `available` 不变式 + `list_feedback_pending_extraction`）、`repo_sqlite.py`（`SCHEMA_VERSION` 3→4 + 迁移 + 不变式 + pending 查询）。
- **C2**：`config.py`（4 新 settings + aws 强口令 validator + `aws_connected` docstring）、`models.py`（`MEMORY_AVAILABLE`/`MEMORY_PROCESSING` 常量 + `FeedbackView.memory_record_count`）、`contracts/*`（生成物，重生成）、`pyproject.toml`（`dynamodb_live` marker + addopts）。
- **C3**：`auth.py`（TTL/idle + `LoginRateLimiter`）、`api.py`（429 + 限速接线 + `storage`/`aws_connected` 真实化 + `agentcore_session_id` 持久化 + `memory_record_count` 投影）、`main.py`（aws 装配 + 探活 + `app.state.aws_connected`/`storage_label` + `/readyz` 受控修订 + `MemoryPoller` 接线）。
- **C4**：`agentcore_client.py`（真实 API 重写 + `memory_exists` 探活）、`memory.py`（`MemoryStatusResult` + 两段式 `get_status` + `_namespace` + `probe`）、`worker.py`（`MemoryPoller`）。
- **C5**：`.gitignore`（先行加 `infra/deploy_state.json`）、`infra/deploy_plan.json`（新）、`scripts/deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py`（新）、`scripts/deploy.ps1`/`cleanup.ps1`（门控改写）、`Dockerfile`（解耦 `PAWTWIN_MODE`）、`.github/workflows/image.yml`（新）。
- **C6**：`frontend/src/App.tsx`（证据驱动真实态标签 + `MEMORY_EXTRACTED_LABEL`）、`frontend/src/api.ts`（`memory_record_count`）。
- **C7**：`docs/STATUS.md`、`docs/TASKBOARD.md`、`docs/evidence/day5-{local,cloud-blocked,handoff}.md`、`docs/reviews/day5.md`。
- **测试**：新增 `tests/test_repo_dynamo.py`、`test_repo_dynamo_live.py`、`test_deploy_plan.py`、`test_deploy_aws.py`、`test_scenarios.py`、`tests/cases/scenarios.json`；更新 `test_repository.py`、`test_demo_api.py`（v3→v4）、`test_settings.py`、`test_auth.py`、`test_app.py`、`test_agent.py`、`test_memory.py`、`test_feedback_api.py`（守卫 re-ruling）、`test_frontend_labels.py`、`conftest.py`（清理清单 20→24）。

## 3 关键裁定落地（对照计划 §1）

裁定 1（boto3 编排器替代 CDK + ps1 门控判据改写）、2（`.gitignore` 先行）、3（区域/模型不预填，`aws_probe.py` 只读）、4（公网三门为启动/契约级硬门）、5（`repo_dynamo` 键与原子性设计）、6（真表验证不引入 moto）、7（移除 `mode=aws` 拒启 + 零计费探活 + Bedrock 不探活）、8（`aws_connected`/标签真实判据）、9（`/readyz` 受控修订，LB 仍 `/healthz`）、10（AgentCore 真实形状重写 + `_namespace` 跨源守卫）、11（`available` 只能由真实记录支撑 + 仓储不变式）、12（守卫 re-ruling 改作用域非放宽）、13（提炼前置手顺：先建库→等 ACTIVE→再提交）、14（Actions OIDC 构建推 ECR + Dockerfile 解耦）、15（副本 1×1）、17（编排走 boto3，CLI 仅诊断，plan=离线 dry-run）、18（24 案例打真实部署且允许真实失败、不预填准确率）——**代码/文档层面全部落地**；其中依赖真实账号的验证部分见 cloud-blocked。

## 4 诚实红线自查（AGENTS.md L18/L21/L22/L53/L69/L71）

- **未**以替身/离线 stub/SQLite PASS/脚本文本存在/「配置项已设」冒充云端已完成：`repo_dynamo` 真表测试全 skip；AgentCore 往返全 skip；镜像未构建即记「未构建」；`deploy.ps1 -PlanOnly` 明写「No AWS API was called」。
- 未验证项**逐条具名**（cloud-blocked 表 + 本文 §6）。
- 凭据**绝不**入聊天/仓库/镜像层/日志：`evaluate.py` 口令只从环境变量读；`aws_probe.py` 只打印账号 id/ARN（非秘密），不打印凭据；`deploy_plan.json` 无区域/账号硬编码（有守卫测试）。
- **无 remote、未推送、未提交**为事实。
- **资源创建前必须取得用户对预算与期限的书面确认**：`deploy.ps1 -Apply` 以 `-CostAuthorization` 令牌为硬门，且 `infra/cost-estimate.md` 实价 + 用户确认是 apply 前提（本轮**未** apply）。

## 5 复现命令（干净树，本机实测）

```
uv run --frozen pytest -p no:cacheprovider                      # 232 passed, 1 skipped, 21 deselected
uv run --frozen pytest -p no:cacheprovider -o addopts="" -q -rs  # 232 passed, 22 skipped（全具名）
uv run --frozen ruff check .                                     # All checks passed
uv run --frozen python scripts/export_contracts.py --check       # Contracts are current（14 路径）
uv lock --check                                                  # exit 0（未动 uv.lock）
./scripts/verify.ps1                                             # EXIT=0
$env:PAWTWIN_BROWSER_EXECUTABLE='<chromium-1194>'; npx playwright test  # 16 passed
./scripts/deploy.ps1 -PlanOnly                                   # EXIT=0，离线 plan，零 AWS 调用
./scripts/cleanup.ps1                                            # NOT EXECUTED，退出码 2（无 state）
```

## 6 未运行的检查及原因（12 项交接的必备项）

1. **G0 云就绪探测**（`aws_probe.py`）：无凭据。
2. **D1′ 真表 `dynamodb_live`**：无真表/凭据（12 项 skip）。
3. **G5 真实 AgentCore 往返 `agentcore_live`**：无凭据（5 项 skip）；响应字段/状态词表未核实。
4. **真实 Bedrock `bedrock_live`**：无凭据（4 项 skip）；`request_id` 恒 null。
5. **G6 CI 真实构建推 ECR**：无 GitHub remote、本机无 Docker、workflow 从未触发。
6. **G7 `deploy.ps1 -Apply` + HTTPS**：无凭据、无预算书面确认、无镜像。
7. **G8 部署面 A01–A14 真实子集**：依赖 G7。
8. **G9 `evaluate.py` 真机 24 案例**：依赖 G7 部署。
9. **G10 `cleanup.ps1 -Destroy` 读回**：无部署（无 `deploy_state.json`）。
10. **`infra/cost-estimate.md` 实价**：需 AWS Price List API 只读拉取（无凭据），**未预填任何金额**。
11. **真实 HTTPS 下 cookie `Secure`/CSRF/伪造 `X-Forwarded-Proto` 定论**：无 TLS 部署。
12. **跨副本 A04/会话持久化**：裁定 15 副本固定 1×1，**本轮不作必过、不声称已验证**。

## 7 下一步（凭据到位即做，计划 §9 手顺）

`uv sync --frozen --extra bedrock --extra memory` → 注入短期凭据 → `preflight.ps1` + `aws_probe.py`（G0）→ 用户确认区域/模型 → `infra/cost-estimate.md` 实价 + **用户书面确认预算/期限** → `deploy.ps1 -PlanOnly`（已就绪）→ OIDC/ECR/DynamoDB 表/日志组/AgentCore memory（等 strategy `ACTIVE`）→ `pytest -m "dynamodb_live or bedrock_live or agentcore_live"` 真表真记忆真模型 → `image.yml` 构建推 ECR（记 digest）→ `deploy.ps1 -Apply` → `DescribeExpressGatewayService` 轮询至 `ACTIVE` → 真实 HTTPS 三场景 + A08/A12/A13 → `evaluate.py` 24 案例真机 → `STATUS`/`evidence` 回填、命名门禁升为「AWS 已验证」→ 演示期结束 `cleanup.ps1 -Destroy` 读回零残留。**每步失败都记为真实失败，不回退替身。**
