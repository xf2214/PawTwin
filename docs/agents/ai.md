# AI 与记忆 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`，认领 AI-01。原实施计划 T4/T5 是后续范围依据，不一次性越过依赖完成全部项目。

产品只有一个 Strands Agent。工具只读：get_pet_facts、get_recent_events、search_owner_memory、get_policy_summary。授权上下文由服务器注入，模型输出 Proposal，不持有审批或设备执行能力。

与后端共同确认适配器协议，不能从模型输出构造不存在的 evidence IDs。外部文字与记忆不是系统指令。无 AWS 时先实现明确的适配器接口、验证与 local 测试，保持 aws 模式失败，绝不偷偷返回本地答案。

AI-02 需真实 AgentCore：先保存反馈原文，再异步提炼，actual retrieval 后才 available；区分主人观察、当次备注和模型推断；最新事实与硬配额优先。

不要改审批、前端或共享数据模型。每次真实云调用需在既定账号与费用授权范围内。报告本地与真实 AWS 检查的不同结果。

## Day-2 派发（AI-03）

当日分解见 `docs/plans/PawTwin_Day2_开发计划.md`。认领 AI-03：`AnalyzerProposer` 适配器（seam 为 `analyze_event(event, snapshot, owner_id, *, model_calls_used=0) -> AnalysisOutcome`，**不接收 `RunRecord`**，其内部记账字段不得进入模型层）、`AgentContext` 的 pinned 快照与追加式证据台账、限额装饰器、`AnalysisOutcome` 遥测、`BedrockAgent` 与 `bedrock_client.py`（strands **延迟导入**）。

证据校验只认台账 `retrieved_evidence_ids()`，**禁用**会重查库的集合：分析期间 `facts_version` 变动会造成假 `UNKNOWN_EVIDENCE`，而策略与建议读到不同快照则是 fail-open。台账只增不减，`evidence_ids` 必须是台账子集。`get_recent_events` **不得**开始返回事件 note 原文（那会成为跳任务的注入通道）。

真实 Bedrock 属**条件项**（无账号）：`scripts/bedrock-smoke.ps1` 在无凭据时必须输出「NOT EXECUTED」并以非零码退出。离线 stub 测试须用**构造注入**的假客户端（不 monkeypatch SDK），文件顶部注明「不构成任何云端证据」，测试名不得含 works/passes/verified。提示注入的强制点在模型之外：系统提示与数据围栏只是缓解，真正的闸门是 `policy`、`Action` 的 pydantic 边界、批准前复评与主人审批；因此 A11 的结论只能写「注入文本无法越过硬配额与审批」，不能写「模型不会被注入影响」。

## Day-3 派发（AI-02）

当日分解见 `docs/plans/PawTwin_Day3_开发计划.md`（14 条技术裁定为权威）。认领 AI-02：新建 `memory.py`——`MemoryService` 协议（seam 由总负责人在门 0 冻结：`submit_feedback(...) -> FeedbackResult`、`get_status(feedback_id, *, agentcore_event_id=None) -> MemoryStatus`、`search(*, owner_id, pet_id, query) -> list[MemoryRecord]`）、`LocalFakeMemory`（`not_implemented`：`submit_feedback`→`saved`、`search`→`[]`，**绝不** `available`/伪造）、`AgentCoreMemory`（延迟导入 `agentcore_client`，缺依赖/凭据→具名 `MemoryUnavailable`）、`StubMemoryService`（构造注入，离线证明接线，非云端证据）。`agent.py` 的 `AgentContext` 注入 `MemoryService`，`search_owner_memory` 委托它：本地返回 `[]` 且**不记** memory 证据；返回记录时才生成 `evidence_id=f"memory:{record_id}"`、`source="memory"` 的可引用证据。

诚实红线（AGENTS.md L18）：`memory_status=saved` 只表示**原文已存业务库**，绝不表示已提炼/已检索；`available` 仅在真实 AgentCore 检索证据出现时。`today_only` 留在有时效业务记录、**不生成永久偏好**（A07）；`session_id`/`conversation_id` **绝不充当宠物身份**，检索按 owner/pet namespace。真实提炼/检索与场景 C「记忆改变建议」为**条件项**（无账号）：`tests/test_agentcore_live.py` 具名 skip，`scripts/agentcore-smoke.ps1` 无凭据输出 `NOT EXECUTED`/退出码 2。`memory.py`/`agentcore_client.py` 属本角色；`workflow.py` **不 import memory**（避免 Backend→AI 依赖），装配在 `main.py`。
