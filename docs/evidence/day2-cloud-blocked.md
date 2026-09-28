# Day-2 云端被阻塞项（2026-09-25）

> **状态：全部未执行。** 唯一原因是**没有已授权的 AWS 账号**（用户 2026-09-24 确认仍无账号）。本文件逐项记录被阻塞的检查、阻塞原因、就绪后的最小验证步骤，以及"已就位但未运行"的入口。
>
> 本地通过与云端未验证**分列**：本地证据见 [day2-local.md](day2-local.md)。任何本地替身或离线 stub 的通过**都不计入**本文件的任何一项。

## 1 被阻塞的检查

| # | 检查项 | 对应验收/任务 | 阻塞原因 | 就绪后的最小验证 |
|---|---|---|---|---|
| C1 | 一次真实 Bedrock 工具往返，记录 request ID / 时间 / 模型 ID / 区域 / 调用数 / 输出 tokens / 延迟 | 总方案第 2 日验收「模型与工具调用记录可核查」；任务单 T0/T4 | 无账号、无凭据、模型未选定、model access 未开通 | `uv sync --frozen --extra bedrock` → 设置 `BEDROCK_MODEL_ID`/`AWS_REGION` 与凭据 → `./scripts/bedrock-smoke.ps1`（自动写入 `docs/evidence/bedrock-call-*.md`） |
| C2 | 真实模型参与**场景 A（正常照护）** | 总方案第 2 日验收；A01 | 同上 | `uv run --frozen pytest -m bedrock_live`（`test_real_bedrock_round_trip_records_a_request_id`）+ 浏览器中以 `PAWTWIN_MODEL_BACKEND=bedrock` 跑通登录→事件→建议→批准→回执，并在 UI 证据面板看到非空 `request_id` |
| C3 | 真实模型参与**场景 B（已经喂过）**：读到新事实后停止额外喂食；同事件 ID 重传不产生第二个任务 | 总方案第 2 日验收；A05/A14 | 同上 | `test_real_model_participates_in_the_normal_and_repeat_feeding_scenarios`；用 `POST /api/demo/facts` 注入近期喂食后重发同类事件 |
| C4 | A14 真模型对照：同一事件在不同事实下建议随之变化（非按场景名返回预制答案） | A14 | 同上 | `test_real_model_proposal_varies_with_the_facts` |
| C5 | A11 模型在环注入：事件 note 内的指令不能越过审批/配额/工具范围 | A11 | 同上 | `test_model_in_the_loop_injection_cannot_exceed_the_hard_quota`（断言**结果**，不断言模型措辞） |
| C6 | 真实模型的延迟是否落在 45 秒分析期限内、SDK 超时/重试配置是否生效 | 任务单 T4；A10 | 同上 | 在 C1 的证据文件里记录实测 wall clock 与 `duration_ms`，与 `PAWTWIN_ANALYSIS_TIMEOUT_SECONDS` 对照 |
| C7 | ≤4 次调用 / ≤800 输出 tokens 在**真实模型**上的计量是否与 `Limits`/`maxOutputTokens` 一致 | 任务单 T4；总方案 §9 | 同上（本地只能证明我们把参数放进了请求） | 记录真实 usage 与调用轮数；若模型不遵守则调整参数或换模型 |
| C8 | 一次 DynamoDB 条件写入（去重语义），以及 Day-2 新增的 CAS/续约/白名单在真表上的同构行为 | A04/A05/A13；任务单 T1/T7 | 无账号、`repo_dynamo` 未实现 | **不以 SQLite PASS 替代**；Day-4/T7 建真表后跑同一组语义测试 |
| C9 | 一个 AgentCore memory strategy `ACTIVE` 检查 | A06–A09；任务单 T5 | 无账号；Day-3 范围 | Day-3 建 memory 后检查 strategy 状态与 namespace 隔离 |
| C10 | 从未登录浏览器验证拒绝访问，再登录完成三场景（真实部署地址） | A12；任务单 T7 | 无账号、无部署 | Day-4/T7 |
| C11 | Docker 镜像构建、Linux 运行时、HTTPS、访问控制、部署与清理 | 任务单 T7 | 本机 PATH 无 Docker/AWS CLI；无账号 | Day-4/T7；`Dockerfile` 已改（`--extra bedrock`、`PAWTWIN_WORKER_MODE=background`、单进程），当前只能记为「**已修改、未构建验证**」 |
| C12 | GitHub Actions 远程运行（含新增的 `uv lock --check`） | 工程基线 | 未配置远程、未推送（需用户授权） | 用户授权推送后观察首个 workflow 运行 |

## 2 已就位但**未运行**的入口（编写完成不等于验证完成）

| 入口 | 当前运行结果 | 说明 |
|---|---|---|
| `scripts/bedrock-smoke.ps1` | `NOT EXECUTED: no AWS credential source found.`，**退出码 2** | 无凭据时绝不 `exit 0`；一旦运行会产生**计费**调用，须在用户授权预算内 |
| `scripts/bedrock_smoke.py` | 未运行（由上者调用） | 输出仅含 request ID/模型 ID/区域/调用数/tokens/延迟/证据 id，无凭据、无完整模型请求、无隐藏推理 |
| `tests/test_bedrock_live.py` | **4 skipped**，理由 `BLOCKED: no AWS account is authorised…` | 由 `addopts = "-q -m 'not bedrock_live'"` 默认排除；blocked 被**命名**而非静默缺失（AGENTS.md L53） |
| `scripts/preflight.ps1` 的 Bedrock 段 | `'bedrock' extra installed: True`、`BEDROCK_MODEL_ID set: False`、`credential source present: False` → `NOT EXECUTED` | 全部只读，不发起任何 AWS 调用，不由环境变量推断已连通 |
| `backend/pawtwin/bedrock_client.py` | 未对真实服务运行 | 依 `strands-agents==1.57.0` 的**本地内省签名**编写（`BedrockModel(region_name=…, model_id=…, max_tokens=…)`、`Agent(model=…, tools=…, system_prompt=…)`、`agent(prompt, structured_output_model=…, limits=Limits(turns=…, output_tokens=…))`）。离线 stub 只验证**我们的**请求构造/解析/限额/错误映射；`_build_tools` 的 strands 工具注册**离线不可验证**，属已命名的未覆盖面 |

## 3 代码中已就位的"云就绪"部分（不是云验证）

- `PAWTWIN_MODEL_BACKEND=bedrock` 的配置校验：缺 `BEDROCK_MODEL_ID`/`AWS_REGION` 即启动失败（`test_bedrock_backend_requires_a_model_id_and_region`）。
- `mode=aws` 仍抛 `NotImplementedError`，且 `mode=aws` 禁止搭配替身后端（`test_aws_mode_rejects_a_stand_in_analyzer`）。
- `aws_connected` 硬编码 `False`，直到存储、模型与记忆**都**真实连通——因此 `analyzer=bedrock` 且 `aws_connected=false` 是诚实表述。
- 失败路径：依赖缺失 → `BACKEND_UNAVAILABLE: STRANDS_NOT_INSTALLED`；凭据缺失 → `BACKEND_UNAVAILABLE: BEDROCK_NOT_CONFIGURED`；调用异常 → `BACKEND_UNAVAILABLE: BEDROCK_CALL_FAILED`；输出违约 → `MODEL_INVALID_OUTPUT`。四者都使 run 落 `FAILED`，**绝不回退**替身或预制答案。
- `AnalysisTelemetry.request_id` 字段已就位（`test_a_real_request_id_is_recorded_when_the_sdk_returns_one` 证明插槽可用），真实调用后即可填入并持久化。
- IAM 最小权限与预算清单见 [infra/cloud-access-checklist.md](../../infra/cloud-access-checklist.md) §2 与 §3.1。

## 4 解除阻塞后的记账要求

1. 每一项从本文件移到 `docs/STATUS.md` 的「本地通过」→「云端已验证」列，并附**实测**数字（不得填估算值）。
2. 真实调用证据落 `docs/evidence/bedrock-call-<时间戳>.md`，提交前复查无秘密。
3. 若真实调用失败：如实记录失败与原因，**不得**用本地替身结果填补，也不得把该验收项标记为通过（总方案 L69：云服务失败必须显示失败或降级，不能返回预制成功答案）。
4. 里程碑顺延按总方案 L106 处理：账号未就绪期间继续本地工作，云端里程碑按实际阻塞顺延，保留 Day-4/Day-5 的验证与材料工作量，**不能把本地替身标记为参赛完成**。
