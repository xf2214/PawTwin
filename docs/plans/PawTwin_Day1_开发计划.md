# PawTwin 第一日（Day-1）开发计划

> 本文是 [五日开发总方案](PawTwin_五日开发总方案.md) 第 6 节「第 1 日」与 [实施任务单](PawTwin_Agent_实施任务单.md) T0→T1→T2(+T3 联调 + OPS 计划) 的当日可执行分解。
> 由多个智能体两轮交叉校验，并对每条断言回源码二次核查后定稿。
> 执行者无需再做设计决策；如与两份权威计划冲突，以权威计划为准并回报总负责人。编制日期：2026-09-23。基线：INIT 骨架（26 项后端测试 + 前端类型/构建/e2e 通过，分支 chore/bootstrap）。

## 0 当日验收（三档）

| 档位 | 内容 |
|---|---|
| **必过 Gate** | ① 契约冻结且含业务路由（OpenAPI + domain schema 重生成、`--check` 通过、记录冻结提交）；② SQLite 去重/持久化/幂等/租约测试转绿；③ **拒绝闭环**跑通（登录→发事件→等待确认→拒绝→刷新仍「已拒绝」、零执行） |
| **尽力项** | 正常批准→模拟执行→成功回执→记账闭环 + 前端真实联调；未达即顺延 Day-2，**不得用替身冒充闭环通过** |
| **条件项** | 账号就绪时一次真实 Bedrock 工具往返（非必过，缺席不阻塞，绝不以本地替身标为云端完成） |

明确**不写进 Day-1 承诺**：真实 Bedrock 参与（A01 完整证据、A14 随机改事实依模型而变）、A06–A09 记忆（Day-3）、DynamoDB 真表并发（Day-4/T7）、跨进程/真实重启复验（Day-3/集成）。

## 1 技术裁定（冻结前须落定，均已回 `tests/test_models.py` 核验一致）

| 议题 | 裁定 |
|---|---|
| 契约权威 | **以 `backend/pawtwin/models.py` 代码为准**，反向修订任务单 §2 文本：基类 `ContractModel`（非 `StrictModel`）、`EventIn.event_id: UUID`、`Receipt.command_id: UUID`、`Proposal.evidence_ids` 默认 `[]` |
| `command_id` | `UUID`，`uuid5(NAMESPACE, f"{run_id}:{proposal_version}")`；同 run+version 恒定，满足「重试不换」；不同 version 自然不同 |
| `action_digest` | `sha256(canonical_json(Action)).hexdigest()`；`canonical_json = json.dumps(model_dump(mode='json'), sort_keys=True, separators=(',',':'))`；BE/AI 共用同一 helper（放 `policy.py` 或 `models.py` helper），格式须匹配 `^[0-9a-f]{64}$` |
| CSRF | Synchronizer Token + `SameSite=Lax` 双防线；`POST /api/login` 响应体返回 `csrf_token`（前端存内存）；写请求带 `X-CSRF-Token` 头，服务端校验与会话绑定；**本地 HTTP 仅省略 `Secure`，绝不省略 CSRF 校验** |
| DTO 分层 | 公开响应模型入 `models.py`：`EventAccepted{run_id:UUID, state:RunState}`、`RunView{run_id, state, facts_version, proposal:Proposal|None, receipt:Receipt|None, expires_at:datetime|None, created_at:datetime}`；内部字段 `owner_id/proposal_version/action_digest/attempt_count/lease_owner/lease_until` **仅入 repo 内部记录，不出现在响应** |
| 演示初值 | 上次喂食距今 360 分钟、当日出粮 0g、日配额 30g、单次 15g、最短间隔 120 分钟；页面标注「非喂养建议」，新会话不重置配额（Day-1 用固定 seed，`demo/facts` 端点尽力项） |

## 2 门 0 · 契约冻结（总负责人独占，前置串行）

**所有权依据 `AGENTS.md`：`backend/pawtwin/models.py`、`contracts/`、`docs/STATUS.md`、`docs/TASKBOARD.md`、根锁文件仅总负责人可写。** 子 Agent 不得自行改这些文件。

- [ ] 在 `models.py` 补 §1 的公开响应 DTO 与 `RunState`（已存在）；业务字段进 repo 记录不进 DTO。
- [ ] `main.py` **仅追加 `include_router(...)`**，具体 handler 实现落在 `api.py`（Backend 拥有）；**router 必须先于 `StaticFiles('/')` 挂载注册**，保证 `/api/*` 404 仍返回 JSON。
- [ ] **强制同步更新基线测试（否则 `verify.ps1` 直接红）：**
      - `tests/test_contracts.py`：L10 与 **L24** 两处 `set(paths) == {"/healthz","/readyz","/api/bootstrap"}` 需扩为含 login/state/events/runs/{id}/approval(/demo) 的精确集合；删 L11 `not any("run"/"approval")`；domain schema 保持只校验 6 个输入模型——`EventAccepted/RunView` **不加入** `DOMAIN_MODELS`，故 L30-31 不动。
      - `tests/test_app.py`：**Day-1 不改 `/api/bootstrap` 语义**（保留 `stage:"scaffold"`、capabilities 全 `"planned"`，故 L21-45 不破）；`readyz` 在闭环完成前保持 `degraded`。新增一条 `/api/runs`（无 id）仍 `404` JSON 的回归断言。
- [ ] 重生成 `contracts/openapi.json`、`contracts/domain.schema.json`；`uv run --frozen python scripts/export_contracts.py --check` 通过。
- [ ] 记录冻结提交 ID，书面通知 FE/AI。**冻结前 FE 只做标注性组件预览、AI 只做 test skeleton/适配接口，均不写 `models.py`/`contracts/`。**

## 3 并行实现（受冻结门约束）

### 3.1 Backend（BE-01 → BE-02 最小集）
- [ ] `repo_sqlite`：事务 + 唯一约束；`create_or_get_run`（同 `owner_id`+`event_id`→同 `run_id`，新 `event_id`→独立 run）；`record_receipt_once`（同 `command_id` 二次→回执数=1、记账一次）；`claim_run`（60s 租约、过期可重领、终态不重处理）。
- [ ] `policy.evaluate_policy(action, facts)->PolicyResult(allowed, reason)`：缺事实/最近喂食(`RECENT_FEED`)/单次/每日额度。
- [ ] `workflow` 状态机：新提案只进 `AWAITING_APPROVAL/BLOCKED/NEEDS_INFO`；审批期限 10 分钟；`owner/proposal_version/action_digest/expires_at` 全匹配才接受；`facts_version` 变化即拒旧授权重分析。
- [ ] **Day-1 inline proposal stub**：workflow 收到事件直接产确定性 Proposal（读 `Facts`，禁按场景名/事件文案硬编码）→ 进 `AWAITING_APPROVAL`，使**拒绝闭环不依赖 AI local_fakes**；Day-2 换 `agent.analyze_event`。
- [ ] `auth`：demo 口令服务端哈希、会话 `HttpOnly/SameSite=Lax/CSRF`；未登录业务 API → 401/403。
- [ ] `device_sim.execute(command_id, action)->Receipt`：固定 `command_id`，success/failure/unknown 三态真实回执，**仅成功后记账**；`api.py` 挂 login/state/events/runs/{id}/approval(+demo)。
- [ ] 测试先红后绿：`test_repository`（去重/幂等/租约）、`test_policy`、`test_approval`（绑定+失效）、`test_recovery`（租约/终态逻辑级）、`test_auth`（401/CSRF）。
- 范围护栏：`repo_dynamo` 仅留接口，云测顺延；worker 恢复语义仅进程内逻辑级验证。

### 3.2 AI（AI-01 边界）
- [ ] `analyze_event(event, context)->Proposal` 协议 + 四只读工具签名 `get_pet_facts/get_recent_events/search_owner_memory/get_policy_summary`（授权由服务端注入，模型不传任意 owner_id）。
- [ ] `local_fakes`：mode-gated（仅 `PAWTWIN_MODE=local`），`evidence_ids` 只来自真实 repo 结果，不绕过 `policy`；输出标「本地替身」。
- [ ] `test_agent`：`validate_proposal_evidence` 对未知 evidence 抛 `UNKNOWN_EVIDENCE`。
- [ ] `aws` 模式缺 `BEDROCK_MODEL_ID` 即启动失败、不回退（配置校验迁移，`test_aws_mode_never_silently_uses_fake`）。

### 3.3 Frontend（FE-01 部分，尽力项）
- [ ] 三主区（宠物与请求 / 建议与确认 / 任务与记忆占位）+ 可折叠演示控制区；模式/边界标识（`local` vs `aws`、AWS 未连接、模拟传感器/执行器/项圈概念）全部取自 `/api/state`、`/api/runs/{id}`，不写死、不当 `/api/bootstrap` 为业务源。
- [ ] 仅服务端 `AWAITING_APPROVAL` 显批准；提交中禁用按钮（幂等交后端）；`BLOCKED/NEEDS_INFO` 如实区分。
- [ ] POST 事件后每 2s GET run，命中终态集合 `{declined,succeeded,failed,expired,blocked,needs_info}` 停止；超 10 分钟/45s 期限显式提示失败/未知，禁无限 loading。
- [ ] 记忆区/`available`/feedback 状态整块**顺延 Day-3**；`demo/facts`、`demo/device-mode` 现场注入**顺延 Day-2**。
- [ ] 新增依赖（类型生成/请求库）走总负责人审批；Day-1 可先用「手写、以冻结契约为唯一来源」的类型避免阻塞。

### 3.4 OPS-01（仅计划，不占计费）
- [ ] 产出云接入清单文档（区域/模型/权限/预算/资源与清理清单）；**不 apply、不建资源、不调收费模型**；无授权身份时只读 preflight 记「未执行」。

## 4 并发与所有权（≤4 活动 Agent，含总负责人；作者不批准自己）

- 常驻 = **Coordinator + Backend + (Frontend 或 AI)**；**Reviewer 与 OPS 用空槽串行复用**，不超 4。
- 独立工作树从冻结提交建立；只 stage 自己拥有文件，禁 `git add .`；不切他人分支、不 `git reset/clean`。
- 非重叠写所有权：Coordinator=`models.py`/`contracts/`/`STATUS`/`TASKBOARD`/锁/`main.py`/集成；Backend=`repository*/policy/workflow/auth/api/worker/device_sim`+对应测试；AI=`agent/local_fakes/memory`接口+`test_agent`；Frontend=`frontend/src`、`e2e`；OPS=`infra/`、`docs/evidence/` 计划。

## 5 A01–A14 在 Day-1 的覆盖（本地判据 vs 顺延）

| 编号 | Day-1 判定 | 说明 |
|---|---|---|
| A02 拒绝 | **可覆盖（必过）** | 状态机 + 拒绝 e2e（reload 仍已拒绝、零执行）；云端访问控制 Day-4 |
| A03 审批后事实变化 | 可覆盖 | `facts_version` 变→旧批准失效重分析 |
| A05 事件重传 | 可覆盖 | SQLite 唯一约束去重；Dynamo 条件写单列云测 |
| A12 未授权 | 可覆盖 | 401/403、CSRF、无凭据下发；HTTPS/口令 Day-4 |
| A13 重启/租约 | 逻辑级可覆盖 | 过期租约可领、终态不重跑；**真实进程重启复验 → Day-3** |
| A08/A09 | 可覆盖（结构） | 记忆/模型文本不授权、缺信息 NEEDS_INFO |
| A01 正常 | 部分 | fake/inline stub 闭环可跑；**证据可追溯需真模型 → Day-2** |
| A04 双标签批准 | 部分（进程内） | **跨进程/滚动双副本 → Day-3/T6** |
| A10 失败/超时/迟到 | 部分 | 三态注入 + 成功才记账；**45s 超时终止 → Day-2** |
| A11 恶意指令 | 部分 | 硬配额/审批域内可挡；**模型在环注入 → Day-2/4** |
| A14 随机改事实 | 部分 | inline stub 随 facts 变；**真模型依据变化 → Day-2** |
| A06/A07 | 顺延 Day-3 | AgentCore 真实检索与时效 |

SQLite PASS **不得**替代云测；Day-1 证据须把「本地通过」与「云端未验证」分列。

## 6 完成的硬性证据（Definition of Done）

- [ ] `uv run --frozen pytest`：基线 26 项之上，新增 test_repository/policy/approval/recovery/auth/agent 全绿，报通过数。
- [ ] `uv run --frozen ruff check .` 无告警；`export_contracts.py --check` 通过且 `openapi.json` 含业务路由。
- [ ] `npm run typecheck`、`npm run build` 通过。
- [ ] 拒绝闭环：**优先** e2e 指向后端同源 `http://127.0.0.1:8000/`（`main.py` 已服务 `frontend/dist`，非 vite preview、非 mock），走 `playwright.config.ts` 拆分：静态 scaffold 用例（改造/退役，其断言「本地骨架已连接」+三禁用按钮在替换后必失效）与业务闭环用例（baseURL→`:8000`）。**降级**：FE 滑期则改用 `httpx TestClient` 做 login→POST event→断言 AWAITING→decline→断言 DECLINED→重新 GET 仍 DECLINED，browser e2e 转 Day-2。
- [ ] 每角色一份 `docs/HANDOFF_TEMPLATE.md`（改动文件、起止提交、已跑/未跑检查及原因、真实/模拟/未实现边界、下一依赖）+ 一条非作者的独立 Reviewer PASS。
- [ ] 无秘密入库、无云资源创建、无费用、无远程推送。

## 7 降级与关键路径

- 关键路径 ≈ 门 0（2–3h 串行）→ 并行 Backend(repo+workflow+auth+decline)/AI(local_fakes 或 inline stub)/FE → 拒绝闭环集成（≈ 8h）。
- **最易滑期**：前端从 scaffold 到可交互闭环 + e2e 基建改造。
- 降级预案：A FE 未就绪→必过用 API 集成测试保底；B AI local_fakes 未就绪→workflow inline stub（已在 §3.1 内置，不阻塞必过）；C 门 0 超时→先冻结 models+openapi 骨架，`demo/facts` 推 Day-2 上午，不阻塞 Backend/AI。
