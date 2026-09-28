# Day-3 云端被阻塞项（2026-09-26）

> **状态：全部未执行。** 唯一原因是**没有已授权的 AWS 账号**（用户 2026-09-26 再次确认仍无账号）。本文件逐项记录被阻塞的检查、阻塞原因、就绪后的最小验证步骤，以及「已就位但未运行」的入口。
>
> 本地通过与云端未验证**分列**：本地证据见 [day3-local.md](day3-local.md)。任何本地替身、离线 stub 或 `saved` 反馈的通过**都不计入**本文件的任何一项；`saved` 绝不等于「已提炼/已检索」。

## 1 被阻塞的检查

| # | 检查项 | 对应验收/任务 | 阻塞原因 | 就绪后的最小验证 |
|---|---|---|---|---|
| M1 | 一个 AgentCore memory strategy `ACTIVE` 检查，并确认 owner/pet namespace 隔离（session_id 不充当宠物身份） | A06；任务单 T5；总方案第 3 日 | 无账号、无凭据、memory 未创建 | `uv sync --frozen --extra memory` → 设置 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 与凭据 → 控制台/CLI 确认 strategy `ACTIVE` |
| M2 | 一次真实反馈提炼：submit `observation` → 记录 event id → 轮询（每 10s，最长 3min）→ `available` 时列出真实 record id/namespace/来源关联 | A06；任务单 T5 | 同上 | `./scripts/agentcore-smoke.ps1`（submit + 一次 search，写 `docs/evidence/agentcore-call-*.md`）；完整 `available` 需跑轮询生命周期（`test_saved_feedback_becomes_available_only_after_real_retrieval`） |
| M3 | **场景 C**：新会话后真实 retrieve 到主人早先观察，Agent 引用它提出陪玩建议并保留不确定性 | 总方案场景 C；A06 | 同上 | `test_a_new_session_really_retrieves_the_owners_prior_observation`；浏览器中 `PAWTWIN_MEMORY_BACKEND=agentcore` 跑「反馈→new-session→相关事件→证据面板出现 `source=memory` 真实 record id」 |
| M4 | **A08**：当前事实/硬配额与旧记忆冲突时，事实与策略优先，记忆文本不授权 | A08 | 同上 | `test_a_current_fact_or_hard_quota_overrides_a_conflicting_old_memory`（断言**结果**，不断言模型措辞） |
| M5 | **A07**：`today_only` 反馈不被提炼成永久偏好；`observation` 与模型推断分离归因 | A07 | 同上 | `test_today_only_feedback_is_not_extracted_into_a_permanent_preference`（真实 strategy 下核对未产生持久 trait） |
| M6 | 真实 AgentCore 检索延迟是否落在分析期限内、SDK 超时/重试是否生效 | 任务单 T5；A10 | 同上 | 在 M2 的证据文件记录实测 wall clock 与轮询次数 |
| M7 | 一次真实 Bedrock 工具往返（含 `search_owner_memory` 走真实记忆） | 总方案第 2/3 日；A01 | 无账号（同 Day-2） | 见 [day2-cloud-blocked.md](day2-cloud-blocked.md) C1；`./scripts/bedrock-smoke.ps1` |
| M8 | DynamoDB 真表条件写，以及反馈持久化/CAS/续约/白名单在真表上的同构行为 | A04/A05/A13；任务单 T1/T7 | 无账号、`repo_dynamo` 未实现 | **不以 SQLite/两连接 PASS 替代**；Day-4/T7 建真表后跑同一组语义测试 |
| M9 | 跨**副本**（多容器/滚动发布）双标签批准与并发上限（数据库级计数） | A04；总方案 L71 | 无账号、无部署 | Day-4/T7 部署双副本后复验；worker 进程内上限不足以跨副本 |
| M10 | 从未登录浏览器验证拒绝访问，再登录完成三场景（真实部署地址，含真实记忆） | A12；任务单 T7 | 无账号、无部署 | Day-4/T7 |
| M11 | Docker 镜像构建（含 `--extra bedrock --extra memory`）、Linux 运行时、HTTPS、访问控制、部署与清理 | 任务单 T7 | 本机 PATH 无 Docker/AWS CLI；无账号 | Day-4/T7；`Dockerfile` 已改，当前只能记为「**已修改、未构建验证**」 |
| M12 | GitHub Actions 远程运行（含 `memory` extra 的 `uv lock --check`） | 工程基线 | 未配置远程、未推送（需用户授权） | 用户授权推送后观察首个 workflow 运行 |

## 2 已就位但**未运行**的入口（编写完成不等于验证完成）

| 入口 | 当前运行结果 | 说明 |
|---|---|---|
| `scripts/agentcore-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2** | 无凭据时绝不 `exit 0`；一旦运行会产生**计费**记忆调用，须在用户授权预算内 |
| `scripts/agentcore_smoke.py` | 未运行（由上者调用） | 输出仅含 memory id/region/namespace/event id/record id/状态/延迟，无凭据、无隐藏推理；空检索如实报告为 0 条 |
| `tests/test_agentcore_live.py` | **5 skipped**，理由 `BLOCKED: no AWS account is authorised…` | 由 `addopts = "-q -m 'not bedrock_live and not agentcore_live'"` 默认排除；blocked 被**命名**而非静默缺失（AGENTS.md L53） |
| `scripts/preflight.ps1` 的 AgentCore 段 | `PAWTWIN_MEMORY_BACKEND: unset -> not_implemented`、`AGENTCORE_MEMORY_ID set: False`、`'memory' extra (boto3) installed: False` → `NOT EXECUTED` | 全部只读，不发起任何 AWS 调用，不由环境变量推断已连通或已检索 |
| `backend/pawtwin/agentcore_client.py` | 未对真实服务运行 | 依 boto3 `bedrock-agentcore` 数据面签名（`create_event`/`search_memory`/`list_events`）编写。离线只验证**我们的** fail-closed（无凭据/无 id → `MemoryUnavailable`）；真实调用路径与**异步提炼轮询生命周期离线不可验证**，属已命名的未覆盖面 |

## 3 代码中已就位的「云就绪」部分（不是云验证）

- `PAWTWIN_MEMORY_BACKEND=agentcore` 的配置校验：缺 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 即启动失败（`test_agentcore_backend_requires_a_memory_id_and_region`）；`mode=aws` 禁止搭配 `not_implemented`（`test_aws_mode_rejects_unimplemented_memory`）。
- `aws_connected` 硬编码 `False`，直到存储、模型与记忆**都**真实连通——因此 `memory=agentcore` 且 `aws_connected=false` 是诚实表述。
- 失败路径：依赖缺失 → `MEMORY_UNAVAILABLE: SDK_NOT_INSTALLED`；凭据缺失 → `MEMORY_UNAVAILABLE: AGENTCORE_NOT_CONFIGURED`；memory id 缺失 → `MEMORY_UNAVAILABLE: AGENTCORE_MEMORY_ID_MISSING`；提交/检索/轮询异常 → `SUBMIT_FAILED`/`RETRIEVE_FAILED`/`STATUS_FAILED`。全部 fail-closed，**绝不回退**替身或伪造记忆。
- `MemoryRecord.record_id`/`namespace` 与 `FeedbackResult.agentcore_event_id`/`memory_record_ids` 字段已就位，真实调用后即可填入并持久化到 `feedback` 表（`set_feedback_status`）。
- `search_owner_memory` 的证据链（`source="memory"`、`evidence_id=f"memory:{record_id}"`）已由 `StubMemoryService` 离线证明可用；真实检索只需把 stub 换成 `AgentCoreMemory`。
- IAM 最小权限（`bedrock-agentcore:` 限定本项目 memory）与预算清单见 [infra/cloud-access-checklist.md](../../infra/cloud-access-checklist.md) §2 与 §3。

## 4 解除阻塞后的记账要求

1. 每一项从本文件移到 `docs/STATUS.md` 的「本地通过」→「云端已验证」列，并附**实测**数字（不得填估算值）。
2. 真实调用证据落 `docs/evidence/agentcore-call-<时间戳>.md`，提交前复查无秘密、无完整模型请求、无隐藏推理。
3. 若真实调用失败：如实记录失败与原因，**不得**用本地替身或 `saved` 反馈填补，也不得把该验收项标记为通过（总方案 L69：云服务失败必须显示失败或降级，不能返回预制成功答案）。
4. 里程碑顺延按总方案 L106 处理：账号未就绪期间继续本地工作，云端里程碑按实际阻塞顺延，保留 Day-4/Day-5 的验证与材料工作量，**不能把本地替身标记为参赛完成**。
