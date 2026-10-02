# Day-5 独立审查（非作者）— 2026-09-30

审查者：**非作者**（CodeReview 子代理，独立于本轮实现者；`docs/agents/reviewer.md:10` 要求 Reviewer 不得由作者充当）。范围：本轮 Day-5 离线实现切片的**全部工作树改动**（review_scope = current_session，未提交）。基线：`chore/bootstrap` HEAD=`9354804` + 43 项未提交变更。

审查者被明确要求：以新鲜、怀疑的视角复核；**不得采信实现者的标签**，一律回源码核实；重点查「虚报云验证 / 假绿测试 / 守卫被放宽 / `repo_dynamo` 与 SQLite 语义等价性 / aws 探活失败是否拒启 / 秘密硬编码 / 契约路径数」。

## 1 结论

**PASS-WITH-NITS**：发现 **1 个 BLOCKER + 0 个 IMPORTANT + 2 个 NIT**；**诚实红线未违反**（逐项核实，见 §3）。BLOCKER 与 2 个 NIT 均已由总负责人修复并复跑（§2）。修复后本地全绿：pytest **232 passed**、ruff 干净、契约 **14 路径 current**、`verify.ps1` EXIT=0、e2e **16 passed**。

> 关键背景：BLOCKER 位于 `dynamodb_live` 路径，**离线套件无法触发**（无真表，12 项全 skip）。它是**真实缺陷**（真表上会 `ValidationException`），由非作者审查在部署前发现——这正是「同视角复核不能替代覆盖面更广的独立审查」（Day-4 教训）的再次印证。

## 2 发现与处理（每条记「处理 / 复测」）

### BLOCKER-1：`state` 是 DynamoDB 保留字，`list_claimable_runs` 的 FilterExpression 未别名

- **位置**：`backend/pawtwin/repo_dynamo.py` `list_claimable_runs` + `_scan`。
- **问题**：`save_run`/`claim_run`/`renew_lease`/`transition_run` 都正确用了 `#state` 别名 + `ExpressionAttributeNames`，但 `list_claimable_runs` 直接写裸 `state`，且 `_scan` 不传 `ExpressionAttributeNames`。真表上会抛 `ValidationException: Invalid FilterExpression: Attribute name is a reserved keyword`，使 **aws 模式下 worker 取不到待处理 run、整条分析管线瘫痪**。
- **为何重要**：这是二次出粮之外的另一类真实故障——不是记账失真，而是**部署即崩**；且离线套件（无真表）永远发现不了。
- **处理**：`_scan` 增 `names` 形参并透传 `ExpressionAttributeNames`；`list_claimable_runs` 改用 `#state` 别名 + `names={"#state": "state"}`，并加注释钉死「`state` 是保留字必须别名」。
- **复测**：ruff 干净；`test_repo_dynamo.py` 协议集合守卫仍绿；`dynamodb_live` 12 项仍具名 skip（真表验证待凭据，本修复的真表生效属 D1′ 解锁项）。**离线不可触发该路径，故以代码审读 + 别名一致性确认修复**（诚实标注：真表复验待凭据）。

### NIT-1：`list_runs`/`count_runs`/`count_receipts` 未处理 Query 分页

- **问题**：DynamoDB 单页 Query 上限 1 MB，超出静默截断；SQLite 版返回全部行，语义不完全等价（demo 规模无实际影响）。
- **处理**：新增 `_query_items`/`_query_count` 两个**分页**助手（跟随 `LastEvaluatedKey`），三处改用它，恢复「返回全部」的等价语义。
- **复测**：ruff 干净、后端全绿；真表分页行为待 `dynamodb_live` 复验。

### NIT-2：`deploy_aws.py._create_resource` 每个资源都重读 plan 文件

- **问题**：`load_plan()` 在每次资源创建时重新读盘解析；调用方 `_apply` 已持有 `plan`。
- **处理**：`_apply` 计算一次 `tags_map` 并传入 `_create_resource`；CloudWatch 日志组用 dict 形 tags、其余用 list 形 tags，均取自同一 `tags_map`。
- **复测**：`test_deploy_aws.py`（拓扑序/占位符/plan 不触 AWS）全绿；`deploy.ps1 -PlanOnly` EXIT=0。

## 3 诚实红线核实（逐项，审查者回源码确认）

| 检查项 | 结论 |
|---|---|
| 标签/状态是否虚报云验证 | ✅ `aws_connected` 仅真实探活通过后为 True；`/readyz` 200 仅映射探活结果；前端「已提炼」仅与 `memory_record_count>0` 配对；STATUS/TASKBOARD/evidence 明标「云端未验证」 |
| 反伪造守卫是否被**放宽** | ✅ 静态字面量白名单 `_ALLOWED_LIFECYCLE_WRITERS` **未扩**；`get_status` 调用者守卫由 `== []` **改作用域**为 `<= {"worker.py"}` + AST 钉死 `poll_once`（裁定 12，非删除/弱化） |
| worker/repo 是否写裸 `available`/`processing` 字面量 | ✅ grep 确认 `worker.py`/`repo_dynamo.py`/`repo_sqlite.py` 无裸字面量，均用 `models.MEMORY_AVAILABLE`/`MEMORY_PROCESSING` |
| aws 探活失败是否**拒启**（不回退替身） | ✅ `repository.probe()`/`memory.probe()` 无 try-except 包裹，异常直接传播出 `create_app`；离线测试 `test_aws_mode_refuses_to_start_when_the_cloud_probe_fails` 断言无凭据→`DynamoUnavailable` |
| Bedrock 是否被启动探活（应否） | ✅ **未探活**（注释明确「Converse 计费，其证据只能是真实 `request_id`」，裁定 7） |
| 凭据/口令是否硬编码或入日志/镜像 | ✅ `evaluate.py` 口令只从环境读；`aws_probe.py` 只打印账号 id/ARN（非秘密）；`deploy_plan.json` 无区域/账号硬编码（`test_no_region_or_account_id_is_hardcoded` 守卫）；镜像不烤口令 |
| 契约路径数 / domain schema | ✅ `export_contracts.py --check` current；OpenAPI **恰 14 路径**；`domain.schema.json` 恰 6 输入模型 + `RunState`；生成物未手改 |
| 假绿测试 | ✅ 未发现永真断言；实现者主动修正了两处 truthiness 断言（`test_auth.py` 的 Response/status_code），并把「全 advisory 案例」在 `evaluate.py` 降级为 ERROR |

## 4 复跑数字（BLOCKER + 2 NIT 修复后，本机干净树）

- `uv run --frozen pytest -p no:cacheprovider` → **232 passed, 1 skipped, 21 deselected**
- `uv run --frozen pytest -o addopts="" -q -rs` → **232 passed, 22 skipped**（全具名）
- `uv run --frozen ruff check .` → All checks passed
- `uv run --frozen python scripts/export_contracts.py --check` → Contracts are current（14 路径）
- `./scripts/verify.ps1` → EXIT=0
- e2e（chromium-1194）→ **16 passed**

## 5 遗留（不在本轮、待凭据）

BLOCKER-1 与 NIT-1 的**真表复验**属 D1′（`dynamodb_live`）解锁项：无凭据时这两条路径离线不可触发，本审查以代码审读 + 别名/分页一致性确认修复，**不声称已在真表验证**。真实 AgentCore 往返、真实 Bedrock、镜像构建、HTTPS、`-Apply`/`-Destroy`、真机 24 案例的独立复核同样待凭据，见 [day5-cloud-blocked.md](../evidence/day5-cloud-blocked.md)。
