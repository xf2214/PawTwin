# PawTwin 开发任务看板

本表由总负责人维护。`ready` 表示依赖满足、可认领，不表示已经有人开始。未获得明确开发指令时，不自行启动所有任务。

| ID | 状态 | Owner | 依赖 | 交付与验收 |
|---|---|---|---|---|
| INIT | done | 初始化 Agent + 总负责人 + 独立审查 Agent | 无 | 可启动骨架、契约、协作资料；26 项后端测试及前端/浏览器检查通过，详见 STATUS |
| BE-01 | done (Day-1, local) | 总负责人+后端(串行) | INIT | 契约已冻结（OpenAPI 含业务路由）；SQLite 持久化/去重/幂等回执/租约；DynamoDB 云测顺延 |
| BE-02 | done (Day-1 最小集, local) | 后端(串行) | BE-01 | 策略/登录/CSRF/审批/模拟执行/恢复(逻辑级)；A02/A03/A05/A12/A13(逻辑级) 本地绿；A04 跨进程、真实重启顺延 |
| FE-01 | done (Day-1, local 联调) | 前端(串行) | INIT；联调需 BE-01 | 三主区 + 真实 /api 联调 + 拒绝闭环 e2e；记忆区/feedback 顺延 Day-3，demo/facts、device-mode 顺延 Day-2 |
| AI-01 | done (Day-1, local interfaces) | AI(串行) | INIT；真实调用需 AWS | 四只读工具 + owner 注入 + 证据校验 + mode-gated 本地替身；真实 Bedrock 与云测顺延 Day-2 |
| AI-02 | blocked: AI-01 | 未认领 | AI-01、反馈持久化、AWS | 真实长期记忆处理与检索、来源和时效；A06–A09 |
| OPS-01 | done (Day-1, plan only) | OPS(串行) | INIT；部署需账号预算 | `infra/cloud-access-checklist.md`；未执行、无资源、无费用 |
| QA-01 | blocked: integration | 未认领 | BE-02、FE-01、AI-02 | A01–A14、云端/本地分开的结果、评委可改输入 |
| SUBMIT-01 | blocked: QA-01 | 未认领 | QA-01、实际赛事规则 | 英文材料、三分钟视频、概念图、边界声明；不自动提交 |

## 推荐派发顺序

1. BE-01 先冻结完整业务契约。它是后续并行最重要的依赖。
2. FE-01 的视觉/组件与 AI-01 的适配器设计可以并行，不能各自发明与后端不一致的接口。
3. BE-02、FE-01 联调、AI-01 工具实现分工作树推进。
4. AI-02 与 OPS-01 受账号条件影响；无账号先准备测试替身和部署计划，明确未云验证。
5. QA-01 独立检查，最后才制作参赛包装。

## 第 1 日派发（2026-09-23）

当日可执行分解见 [Day-1 开发计划](plans/PawTwin_Day1_开发计划.md)（多智能体两轮交叉校验 + 回源码二次核查后定稿）。当日主线 = 门 0 契约冻结 → BE-01/BE-02 最小集 + AI-01 适配接口/inline stub → FE-01 接真实本地 API（尽力）。必过门仅为「契约冻结 + SQLite 去重/持久化/幂等/租约 + 拒绝闭环」；正常闭环与前端联调为尽力项，真实模型调用为条件项，均不得以本地替身标为云端完成。

契约漂移裁定（由总负责人在门 0 统一落地，子 Agent 不得擅改 `models.py`/`contracts/`）：以 `models.py` 代码为权威——`EventIn.event_id:UUID`、`Receipt.command_id:UUID`（`uuid5(run_id:proposal_version)`）、`ApprovalIn.action_digest` 匹配 `^[0-9a-f]{64}$`、`Proposal.evidence_ids` 默认 `[]`；CSRF 走 `X-CSRF-Token` 头 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。

门 0 强制同步项（否则 `verify.ps1` 必红）：`tests/test_contracts.py` L10 与 L24 两处路径相等断言 + 删 L11；`tests/test_app.py` Day-1 保持 `/api/bootstrap` 语义不动、加 `/api/runs` 404 回归；`main.py` router 先于 `StaticFiles('/')` 注册；e2e 拆静态用例与业务用例（baseURL 指后端同源 `:8000`）。

并发上限（≤4，含总负责人）：常驻 Coordinator + Backend + (Frontend 或 AI)；Reviewer、OPS-01（仅计划）用空槽串行复用。

## 第 1 日完成记录（2026-09-23）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。详见 [STATUS](STATUS.md)。

- **门 0 契约冻结**：`models.py` 公开响应 DTO + 共享 `compute_action_digest`/`make_command_id`；`main.py` 业务 router 先于 `StaticFiles('/')` 注册；`contracts/openapi.json` 重生成含业务路由，`--check` 通过；基线测试同步（`test_contracts.py` 两处路径相等断言扩为业务集合并删旧否定断言；`test_app.py` 保 `/api/bootstrap` 语义、`readyz` 仍 degraded、新增 `/api/runs` 404 JSON 回归）。
- **裁定落地**：`command_id=uuid5(run_id:proposal_version)`；`action_digest=sha256(canonical_json(Action))` 匹配 `^[0-9a-f]{64}$`；CSRF 同步令牌 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。**新增裁定**：`RunView` 暴露 `proposal_version/action_digest`（审批防篡改须由客户端回显，否则冻结的 `ApprovalIn` 无法构造）；`owner_id/attempt_count/lease_*` 仍不入响应。
- **本地检查**：`pytest` 71 通过（二次检查补强 2 条审批安全测试）、`ruff` 无告警、契约 current、`typecheck`/`build` 通过、浏览器 e2e 3 通过（拒绝闭环 reload 仍「已拒绝」、零执行）、`verify.ps1` 全绿。
- **环境修复**：重建工作区 `.venv`（复制来的 `pytest.exe` 启动器指向旧源码树，致 pytest 导入旧 `pawtwin`）。
- **边界**：真实 Bedrock/AgentCore/DynamoDB 真表/跨进程双批准/真实重启/部署**未验证**，不以 SQLite 或本地替身冒充云端完成。
- **提交**：已按逻辑分组提交到 `chore/bootstrap`（用户授权，未推送远程）；**冻结提交 ID = `94216df`**；后续 `f2927cb`(后端测试)/`e20336d`(AI)/`f45edb8`(前端)/本提交(OPS+文档)。

## 认领记录格式

每项开始前追加：任务 ID、Agent/任务名称、起始提交、工作树路径、分支、允许写的文件、预计交付、接口变更需求。完成后填写交付提交和验证证据链接。不要让多个 Agent 同时改此表。
