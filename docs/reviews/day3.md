# Day-3 独立审查记录（2026-09-26）

审查者：**非作者**的独立只读代码审查 Agent（CodeReview 子代理）。范围：本次会话在 `chore/bootstrap` 上的 **Day-3** 改动（基线 `dc8dc10`；工作区同时含未提交的 Day-2 改动，审查聚焦 Day-3 新增/修改文件）。审查判据为 `docs/plans/PawTwin_Day3_开发计划.md` 的 14 条裁定与 G0–G10 必过门、`AGENTS.md`（尤其 L18/L19/L22/L53）、五日总方案 A01–A14 与实施任务单 T5。

## 结论

**PASS-WITH-NITS**。无阻断性、无重要级缺陷；14 条裁定与诚实红线（L18/L19/L22/L53）逐条核验通过。发现 **3 个 nit**（均为关闭期竞态或非出厂配置下的健壮性/覆盖缺口，不影响演示与已测路径），已全部处理并复跑。

审查者复跑证据：`pytest` 全绿（默认 addopts 下 `agentcore_live`/`bedrock_live` 正常 deselect，`restart` 尽力项占位具名 skip）；并实证核验了 v2→v3 迁移安全性与反馈幂等语义（同 key→同 id、NULL key→各条独立）。

## 8 项高信号逐条核实

| # | 审查项 | 结论 | 关键依据 |
|---|---|---|---|
| 1 | **诚实性（最高优先级）**：本地/无账号路径能否伪造 `processing`/`available` 或凭空产生 `source="memory"` 证据 | ✅ 红线未破 | `LocalFakeMemory` 恒 `saved`/`search→[]`；`AgentContext.search_owner_memory` 仅在真返回记录时记证据；`StubMemoryService` 全仓**从未接入** `app.state.memory`（grep 确认）；前端显示「已保存原文（未提炼）」，e2e 断言记忆区**不含**「已可检索」 |
| 2 | **worker 真并发（裁定 7）**：准入槽获取/释放、双重释放、竞态、`create_app` 零线程 | ✅（含 nit-1） | `_process.finally` 与 `_on_done`（仅 `future.cancelled()`）互斥释放，无双释放/泄漏；计数由 `_count_lock`/`_inflight_lock` 保护；per-task `worker_id` 唯一；`create_app` 仅构造不起线程（`test_app` 断言）；`peak_concurrency` 测试真实（退化顺序执行会变红） |
| 3 | **跨进程/重启（裁定 8/9）**：断言真实 DB 不变式而非共享计数器；WAL 仅文件库；`ANALYZING`+活租约不重分析 | ✅ | `test_concurrency_crossprocess` 用两独立连接断言 `count_receipts==1`/单一 `SUCCEEDED`/配额一次；WAL/`busy_timeout` 仅 `path != ":memory:"`；`test_restart` 验证活租约下 `proposal_version` 不变、无新 command_id |
| 4 | **反馈持久化**：幂等、迁移 2→3 安全、`_row_to_feedback`、内部字段不泄漏 | ✅（含 nit-3） | `UNIQUE(owner_id, idempotency_key)` + 确定性 `uuid5`；实证 v2 文件库重开→`user_version=3`、`feedback` 表自动建、幂等正常；`_feedback_view` 不投影 `owner_id`/`idempotency_key`（测试断言） |
| 5 | **fail-closed**：`AgentCoreMemory`/`agentcore_client` 缺依赖/凭据/id/SDK 错误 → `MemoryUnavailable`，绝不伪造或"空即成功"；config 交叉校验 | ✅ | `agentcore_client` 全路径抛 `MemoryUnavailable`；`retrieve` 仅真实成功返回记录；`config` 的 aws⇒agentcore+id、agentcore 需 id+region 校验齐全 |
| 6 | **安全**：feedback/new-session 鉴权（401/CSRF 403）、越权 404 不泄露、无秘密/conversation 落日志、反馈原文非注入通道 | ✅ | 写操作经 `CsrfSessionDep`；`GET /api/feedback/{id}` 越权 404；worker 仅 `logger.exception` 固定文案、异常消息只含类名；`_build_prompt` 仅用转义后的 `event.note`，反馈原文不入 prompt |
| 7 | **契约**：openapi 恰 14 路径；domain schema 恰 6 输入模型 + RunState；断言未削弱 | ✅ | 实测 14 paths；`FeedbackView`/`NewSessionView` 未泄漏进领域 schema；`test_contracts` 的 `$defs` 断言由 `<=` **加强为** `==` |
| 8 | **测试完整性**：新测试是否真实（破坏会变红）、有无同义反复、blocked 是否具名 | ✅ | 新测试为真实断言；`test_agentcore_live` 以 marker + 显式 `@pytest.mark.skip(reason=…)` 命名（符合 L53） |

## 发现与处理

### 【nit】#1 关闭期 `pool.submit` 失败会泄漏一个准入槽 — **已修**

- **发现**：`drain_once` 在 `try_acquire` 成功后 `pool.submit`；若此刻 `stop()` 已 `pool.shutdown()`（当 `stop()` 的 `thread.join(timeout=2.0)` 因文件库 `busy_timeout=5000` 下扫描线程阻塞 >2s 超时后关池），`submit` 抛 `RuntimeError`，已获取的准入槽既无 `_process.finally` 释放、也无 `_on_done`（future 未生成）释放 → 泄漏。
- **影响**：仅发生在**关闭期**，准入计数为进程内、随进程销毁，实际影响可忽略；但属"获取后未保证释放"的确定性缺口。
- **处理**：`worker.py` 的 `pool.submit` 包 `try/except RuntimeError` → `self.admission.release(record.owner_id)` 后 `break`（归还刚获取的槽并停止本轮）。
- **复测**：`test_worker.py` 全绿；准入不泄漏路径由既有 `test_admission_control_enforces_both_ceilings` 与并发用例守护。

### 【nit】#2 `post_feedback` 未把 `MemoryUnavailable` 映射为有界结果 — **已修**

- **发现**：`api.post_feedback` 的 `memory.submit_feedback(...)` 未包 try/except，真实 `AgentCoreMemory` 抛 `MemoryUnavailable` 时会冒泡成 500。
- **影响**：**在任何出厂/已测配置下均不可达**（本地默认 `LocalFakeMemory` 永不抛；`mode=aws` 下 `create_app` 直接 `NotImplementedError`）；仅当运维显式设 `PAWTWIN_MEMORY_BACKEND=agentcore`（local 模式）却无凭据时触发。此时反馈原文已先落库为 `saved`（无数据丢失），500 属"响亮失败"而非静默回退，未违反 L22，异常消息只含类名不泄密。仅为错误响应不够整洁。
- **处理**：`api.py` 把 `submit_feedback` 包 `try/except MemoryUnavailable` → 调 `set_feedback_status(..., memory_status="failed")` 并返回该 `FeedbackView`（HTTP 200）。这既避免 500，又复用已冻结的 `MemoryStatus` 词汇诚实报告"提炼失败"，且**绝不**回退成"已生成记忆"。
- **复测**：新增 `test_a_memory_submission_failure_is_reported_as_failed_not_a_500`（注入抛 `MemoryUnavailable` 的记忆后端，断言 200 + `memory_status=="failed"` + 原文仍在 + GET 回读同为 `failed`）。**负向验证**：回退该 try/except 后此测试因 500 转红。

### 【nit】#3 缺少 v2→v3 迁移回归测试 — **已补**

- **发现**：`_migrate` 逻辑经审查者实证在预置 v2 文件库上安全，但 `tests/` 无对应回归测试，未来改 `_SCHEMA`/`SCHEMA_VERSION` 时无自动护栏。
- **处理**：新增 `test_a_pre_day3_database_file_gains_the_feedback_table_idempotently`——先建当前库再回退成 v2（`DROP TABLE feedback` + `PRAGMA user_version=2`），用 `SqliteRepository` 重开，断言 `save_feedback`/`get_feedback`/`list_feedback` 可用且 `user_version==3`。
- **复测**：新测试绿。

## 诚实性检查（审查结论）

- **无以本地替身/stub 冒充云端记忆**：`aws_connected` 恒 False；`memory=not_implemented` 时反馈恒 `saved`、`search_owner_memory` 恒 `[]` 且不记 memory 证据；`StubMemoryService` 仅存在于测试、从未接入生产 `app.state.memory`。
- **fail-closed 未回退**：AgentCore 缺依赖/凭据/id/SDK 错误一律 `MemoryUnavailable`；`memory_status` 只在真实提炼成功时才可能 `available`（当前无账号 → 不可达）。
- **blocked 具名**：`agentcore_live` 5 项、`bedrock_live` 4 项、`restart` 尽力项占位 1 项均具名 skip，非静默缺席。
- **契约断言加强未削弱**：`domain.schema.json` 由子集改 `==`（Day-2 起）保持；Day-3 未新增被放宽的断言。

## 范围合规

**合规**。全部改动落在 Day-3 计划范围内；契约 14 路径与门 0 冻结集一致；无 Day-4/T7（DynamoDB/部署/HTTPS）实现代码；无未授权产品功能；无秘密入库、无云资源创建、无费用、无远程推送、**镜像未构建**（本机 PATH 无 Docker，已如实标注）。

## 后记（总负责人处理 3 个 nit 后的复跑，2026-09-26）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端测试 | `uv run --frozen pytest -p no:cacheprovider -o addopts="" -q` | **184 passed, 11 skipped**（182 → +2：迁移回归 + 记忆提交失败归约；11 skip 均具名） |
| 静态检查 | `uv run --frozen ruff check .` | All checks passed |
| 契约一致性 | `uv run --frozen python scripts/export_contracts.py --check` | Contracts are current（14 路径，本轮无契约变更） |
| 集成 baseline | `./scripts/verify.ps1` | 全绿 EXIT=0（含 typecheck/build） |
| 浏览器 e2e | `scripts/test-e2e.ps1` 等价 | **10 passed**（chromium-1194；未下载任何二进制） |

仍未验证（保持 BLOCKED，不计入通过）：真实 AgentCore 提炼/检索与场景 C 真实记忆影响、真实 Bedrock 往返、DynamoDB 条件写与跨副本、真实 OS 进程被 kill 于 ANALYZING、镜像构建、GitHub Actions 远程运行。

本文件为 Day-3 审查记录；Day-1/Day-2 的 `reviews/day1.md`、`reviews/day2.md` 未改写。
