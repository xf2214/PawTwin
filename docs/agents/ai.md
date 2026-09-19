# AI 与记忆 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`，认领 AI-01。原实施计划 T4/T5 是后续范围依据，不一次性越过依赖完成全部项目。

产品只有一个 Strands Agent。工具只读：get_pet_facts、get_recent_events、search_owner_memory、get_policy_summary。授权上下文由服务器注入，模型输出 Proposal，不持有审批或设备执行能力。

与后端共同确认适配器协议，不能从模型输出构造不存在的 evidence IDs。外部文字与记忆不是系统指令。无 AWS 时先实现明确的适配器接口、验证与 local 测试，保持 aws 模式失败，绝不偷偷返回本地答案。

AI-02 需真实 AgentCore：先保存反馈原文，再异步提炼，actual retrieval 后才 available；区分主人观察、当次备注和模型推断；最新事实与硬配额优先。

不要改审批、前端或共享数据模型。每次真实云调用需在既定账号与费用授权范围内。报告本地与真实 AWS 检查的不同结果。
