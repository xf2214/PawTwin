# EXT-00 基线评审与契约草案（2026-10-03，只读）

> **状态：草案 / 待冻结**。本评审为**只读**——未改任何源码、契约、数据库、依赖。契约冻结（门 0）需用户明确授权。
> 权威需求 = [附加开发计划](../plans/PawTwin_附加开发计划_2026-10-02.md) §5–§10；排期 = [后续开发路线](../plans/PawTwin_后续开发路线_2026-10-03.md)。
> 基线：`chore/bootstrap` HEAD=`31da349`、工作树干净、`verify.ps1` 全绿（252 passed、契约 28 路径 current）。

## 1. 已实现接口清单（实测，28 契约路径）

### 1.1 主业务 API（`backend/pawtwin/api.py`，Backend 所有）
| 路由 | 鉴权 | 范围键 | 说明 |
|---|---|---|---|
| `POST /api/login` | 口令 + 限速 | — | 单口令 → 单会话；429 `RATE_LIMITED` |
| `POST /api/logout` | 会话 | — | 204，幂等 |
| `GET /api/state` | 会话 | `session.owner_id` | 投影 facts/runs/feedback + 组件标签 |
| `POST /api/events` | 会话 + CSRF | `session.owner_id` | 事件摄入（`EventIn.pet_id` 硬编码 `mochi`） |
| `GET /api/runs/{run_id}` | 会话 | `owner_id` 校验 | 404 若不属本 owner |
| `POST /api/runs/{run_id}/approval` | 会话 + CSRF | `owner_id` | 审批（CAS + digest 绑定） |
| `POST /api/demo/facts` `/api/demo/device-mode` `/api/demo/new-session` | 会话 + CSRF | `owner_id` | 演示注入（硬限额不可注入） |
| `POST /api/feedback` `GET /api/feedback/{id}` | 会话(+CSRF) | `owner_id` + `DEMO_PET_ID` | 反馈原文入库 + 诚实记忆生命周期 |
| `GET /api/bootstrap`、`/healthz`、`/readyz` | 无/诊断 | — | `main.py`；`readyz` 按真实探活上调 |

### 1.2 Home API（`backend/pawtwin/home_api.py`，`/api/home/*`，14 路径）
`state`、`pets`(POST)、`pets/{id}`(PUT)、`members`(POST)、`pets/{id}/objects`、`objects/{id}`(PUT)、`pets/{id}/tasks`、`tasks/{id}/action`、`pets/{id}/notes`、`pets/{id}/diary`、`pets/{id}/insights`、`photos`(POST)、`photos/{id}`(GET)、`photos/{id}/recognize`。
- 全部以 `session.owner_id`（恒 `demo-owner`）为家庭键；`store(request)` 在 AWS 模式返回 **503**（无云后端）。
- **`actor_id` 由客户端请求体传入**（`TaskAction`/`NoteInput`/`DiaryInput`）→ 命中附加计划 §5.2 禁止项。
- `member_identity: "household_display_name"`、`storage: "sqlite_local"` 已诚实标注。

### 1.3 鉴权/会话（`auth.py`）
`AuthService`：单 `demo_passphrase` → `Session(owner_id="demo-owner")`；进程内 `dict`；Day-5 加会话 TTL/idle + 登录限速（**均进程内**，副本 1×1）。**无 User 账号、无家庭、无角色。**

### 1.4 存储
- `repository.py` `Repository` 协议：Run/Facts/Feedback/Receipt/lease/CAS，**全按 `owner_id` 键**；`repo_sqlite`（`SCHEMA_VERSION` 4）/`repo_dynamo`（离线守卫，真表 skip）。
- `home_store.py` `HomeStore`：**整份家庭状态 = 单 JSON 文档按 `owner` 键**（`pet_home_documents(owner PK, document)` + `pet_home_photos`）；`mutate` 用 `BEGIN IMMEDIATE` + RLock。

## 2. 缺口（对照附加计划目标）

| 目标 | 现状 | 缺口 | 包 |
|---|---|---|---|
| 独立身份 | `owner_id="demo-owner"` 固定 | User 实体、注册/登录、会话携带可信 `user_id` | EXT-01 |
| 家庭/权限/邀请 | `member` 仅显示名 | Household/Membership/Invitation + 角色 + 撤权即时拒绝 | EXT-02 |
| 服务端 actor | 客户端传 `actor_id` | 由 `session.user_id` 派生，禁止冒充 | EXT-02 |
| 归属/迁移 | 单 JSON 文档按 owner | `household_id/pet_id/user_id` 归属 + 副本幂等迁移 | EXT-03 |
| 任务生命周期 | 仅 complete/postpone | 领取/转交/编辑/取消 + 周期实例 + 版本冲突 | EXT-03 |
| 成长记录 | 无 Measurement | 称重/饮食：作者/来源/事件时间/纠错 | EXT-04 |
| 统计/报告 | `insights` 粗 7 日计数 | 准确统计 + 持久化调度 + 修订重建 | EXT-05 |
| 个体上下文 | Agent 未读 Home；`pet_id` 硬编码 | 五层 PetContext + 记忆确认/失效 | EXT-06 |

## 3. 契约草案（待冻结实体；名称非已发布承诺）

> 所有实体带**归属三元组** `household_id`(归属) / `pet_id`(隔离) / `user_id`(追溯，作者由服务端取)。响应 DTO 与领域输入模型分列，`domain.schema.json` 变更见 §5。

### 3.1 身份与家庭
- **User**：`user_id`、`display_name`、`avatar_ref`、`credential_ref`（本地=口令哈希 / 云=Cognito sub，**不入库明文**）、`created_at`、`status`。
- **Household**：`household_id`、`name`、`timezone`(默认 `Asia/Shanghai`)、`created_by`。
- **Membership**：`(household_id,user_id)`、`role`∈{`admin`,`carer`,`guest`}、`family_label`∈{爸爸,妈妈,姐姐,哥哥,室友,照护人,custom}（**本人自选，与 role 分离**）、`display_name`、`joined_at`、`status`∈{active,removed}。
- **Invitation**：`invitation_id`、`household_id`、`token_digest`（**存摘要非明文**）、`invited_by`、`expires_at`、`max_uses`、`use_count`、`revoked`；重复接受幂等（不产生重复 Membership）。

### 3.2 宠物与照护
- **Pet**：`pet_id`、`household_id`、档案字段（沿用 `home_models.PetInput`）；`mochi` 作为迁移种子宠物的稳定引用（见 §4）。
- **CareTask**（定义）：`task_id`、`household_id`、`pet_id`、`kind`(8 类)、`title`、`interval_days`、`assigned_to`(user_id)、`authorization`（喂食类绑定宠物 + 获授权成员）。
- **CareOccurrence**（实例）：`occurrence_id`、`task_id`、`due_at`、`status`∈{pending,claimed,completed,postponed,cancelled}、`claimed_by`、`completed_by`、`version`（乐观并发）、`event_id`（幂等）。

### 3.3 成长记录
- **Measurement**：`measurement_id`、`household_id`、`pet_id`、`kind`∈{weight,diet}、`value`、`unit`、`measured_at`、`recorded_at`、`author_user_id`、`source`∈{owner_measured,vet,verified_device,demo_sample}、`note`、`version`、`corrects`/`deleted`。**照片不生成猜测体重；出粮 ≠ 实际摄入。**
- **Observation**：泛化 `NoteInput`（`scope`∈{today,preference,observation}、`activity`），`author_user_id` 由服务端取。
- **Diary / Photo**：加 `household_id/pet_id/author_user_id`；照片范围校验同其它资源。

### 3.4 报告与上下文
- **Report**：`report_id`、`household_id`、`pet_id`、`period`∈{daily,weekly}、`window_start`/`window_end`、`generated_at`、`coverage`、`source_record_ids`、`stat_version`、`status`∈{current,superseded,failed}。同 (household,pet,period) 仅一个 current；迟到/修订/删除使旧报告 superseded 并重建。
- **PetContext**：`context_version`、`as_of`、`household_id`、`pet_id`、`layers`(profile/growth/memory/recent/reference)、`source_versions`、`valid_until`、`unresolved_conflicts`。结构化可追溯快照，非无限堆叠提示词。

### 3.5 操作与审计（复用 + 扩展）
沿用 `Proposal`/`ApprovalIn`/`Receipt`（`models.py`，`command_id=uuid5(run:version)`、`action_digest`）。新增 **Audit**：`audit_id`、`household_id`、`actor_user_id`、`action`、`target`、`at`、`result`∈{success,failure,unknown}。喂食审批**绑定宠物 + 获授权成员**，硬限额不可被任何角色/模型绕过。

### 3.6 接口族（路由草案，冻结后由 export 生成）
身份/当前家庭、邀请/成员、宠物/照护（含领取/转交/编辑/取消）、成长记录、报告、上下文、对话/确认。**每次请求校验当前成员关系与动作权限，不信任前端传来的家庭 ID。**

### 3.7 只读工具（Agent，先取可信家庭/成员范围）
`get_pet_profile`、`get_care_history`、`get_growth_records`、`get_period_report`、`search_pet_memory`、`get_reference_knowledge`。记录 ID 不是越权授权；写工具不得绕过审批流程。

## 4. 迁移映射（EXT-03 前置设计）

**源**：① `pet_home_documents(owner="demo-owner", document=JSON{pets,members,objects,tasks,notes,diary,history,processed_actions})`；② 喂食仓储（`RunRecord`/`FactsSnapshot`/`FeedbackRecord`，`owner_id="demo-owner"`、`pet_id="mochi"`）。

**目标**：关系表 `households/memberships/users/pets/care_tasks/care_occurrences/measurements/observations/diary/photos/reports` + 喂食仓储改 `household_id/pet_id/user_id` 键。

| 源 | 目标 | 备注 |
|---|---|---|
| `owner="demo-owner"` | 一个种子 `household` + 种子 `admin` User | 旧单口令登录映射为种子家庭管理员 |
| `pets[].id="mochi"` | `pets` 行，保留 `mochi` 稳定引用 | 设备/配额绑定该 pet，不复制 |
| `members[]{id,name}` | `memberships`（display_name）| 显示名**非账号**；EXT-01 前标记 legacy，不冒充云认证 |
| `objects/tasks/notes/diary/history` | 对应关系表 + `author_user_id` | 历史 `actor`（显示名）保留稳定作者 ID + 当时展示名 |
| 喂食 `FactsSnapshot`/配额 | 归 `household+pet`，**唯一一份额度** | 不同账号不得各复制一份额度控制同一设备 |

**可靠性硬门**（附加计划 §5.3 / QODER_HANDOFF）：先**备份**并在 `data/pet-home.db` **副本**上做**幂等**迁移 + 计数/关联核对 + 失败恢复；**未经验证不破坏在用的 `pet-home.db`**，**禁止清库换绿**。任务按周期实例，领取/完成/审批用条件更新或版本冲突控制，两成员同时提交只产生一个有效结果。

## 5. 消费者清单（契约变更影响面，冻结前必须逐项处置）

| 变更点 | 消费者 | 处置 |
|---|---|---|
| `EventIn.pet_id: Literal["mochi"]` 泛化 | `workflow.py`、`agent.py`、`repo_sqlite.DEMO_PET_ID`、`api.post_feedback`、`test_contracts.py`(domain `==6`)、`frontend/api.ts`、e2e | **改 `domain.schema.json` 输入模型**→ 需 Coordinator 门 0 裁定 + 更新 `test_contracts.py` 断言（**列消费者，不得静默放宽 `==`**） |
| `StateView.pet_id: Literal["mochi"]` | `frontend/App.tsx` | 随 pet 泛化同步 |
| `Session.owner_id` / `AuthService.owner_id="demo-owner"` | `api.py`(多处 `session.owner_id`)、`home_api.py`(多处)、`repository` owner_id 形参、`repo_sqlite`/`repo_dynamo`、tests | 引入 `user_id`+`household_id`；`owner_id` 作过渡别名，迁移期双写/映射 |
| 客户端 `actor_id`（`TaskAction`/`NoteInput`/`DiaryInput`） | `home_api` 三写端点、`home_models`、`test_pet_home`、`frontend/PetHome.tsx` | 移除/忽略客户端 `actor_id`，服务端注入；补越权负向测试 |
| `HomeStore.read/mutate(owner)` 单文档 | `home_api`、`main.py` 装配 | 迁移到关系归属；AWS 模式仍 fail-closed（不静默本地回退） |
| `Repository` 协议（owner 键） | `repo_sqlite`/`repo_dynamo`/`workflow`/`worker`/`api`/tests | 归属键扩展；`repo_dynamo` 真表验证仍待凭据 |
| `contracts/openapi.json`（28 路径，生成物） | `export_contracts.py`、`test_contracts.py` | 从源模型重生成、**禁止手改 JSON**；路径将远超 28 |
| `config.demo_passphrase` 单口令 | `auth.py`、`require_strong_demo_passphrase_in_aws` | 多用户凭据（本地口令/云 Cognito）；AWS 强口令门泛化到每用户 |

## 6. 身份适配、本地/云边界、后端审批控制

- **本地多身份**（EXT-01）：本地 User 账号（每用户口令）仅用于**测试**，诚实标注；**不冒充云认证**。
- **云身份**（EXT-10）：优先评估 **Cognito**；**家庭关系由业务后台维护，不能用全局登录组替代家庭权限**。本地多身份 ≠ 真实云登录，分列报告。
- **会话**：当前进程内 `dict`（副本 1×1）；多用户下仍进程内，多副本会 401——如需持久化会话另行裁定（不默认扩范围）。
- **后端审批控制**：喂食审批绑定宠物 + 获授权成员；硬限额（`grams` 1–15、日配额）不可被任何角色/模型/记忆/上下文绕过；模型/记忆/报告**不授予权限**；写入是待确认方案或获授权记录，设备执行仍经规则/审批/回执。撤权/退出后新 API、图片、Agent 工具请求**立即拒绝**（非仅隐藏按钮或等令牌过期）。

## 7. 可写路径与所有权（EXT-00 → 下游，AGENTS）

- **EXT-00（本评审）**：只读，**不写源码**。交付 = 本文 + 待冻结裁定项（§8）。
- **Coordinator（门 0 冻结）**：`models.py`、`contracts/`、`config.py`、`main.py`、`STATUS`、`TASKBOARD`。
- **Backend（EXT-01/02/03，串行）**：`auth.py`、新增身份/家庭模块、`repository.py`、`repo_sqlite.py`、`home_store.py`、`home_api.py`、`api.py` + 对应 Python 测试。
- **AI（EXT-06/08/09）**：`agent.py`、`memory.py`、`agentcore_client.py`、上下文/工具服务 + 测试；**无执行/审批权**。
- **Frontend（EXT-07，可并行）**：`frontend/src/`、`frontend/e2e/`；`api.ts` 经 Coordinator 串行协调。
- **Reviewer 不得由作者充当**。共享 `models/contracts/locks/main/config/api.ts/STATUS/TASKBOARD` 串行、不覆盖他人修改。

## 8. 冻结前待用户裁定项（门 0）

1. **`pet_id` 泛化方式**：保留 `mochi` 为稳定种子宠物引用（迁移友好）还是全部改 UUID + 别名？（影响 `domain.schema.json` 六输入模型不变式与 `test_contracts.py` 断言）
2. **EXT-01 本地多身份**：本地每用户口令（测试用，先落地）还是直接等 Cognito？（决定 G1 是否可在无云下推进）
3. **家庭范围**：首版是否**聚焦单一「当前家庭」**、结构保留多家庭扩展（附加计划 §5.2 建议）？
4. **迁移切换**：`pet-home.db` 副本验证后**原地升级**，还是新 schema + 导入旧数据？
5. **契约冻结范围**：本轮冻结**全部** EXT 实体，还是先冻结 EXT-01/02/03（身份/家庭/归属）关键路径、EXT-04~09 实体待后续增量冻结？

> 冻结后将产生**契约冻结提交 ID**，回填本文、[后续开发路线](../plans/PawTwin_后续开发路线_2026-10-03.md) 与 TASKBOARD，随后派发 EXT-01/02（后端串行）与 EXT-07（前端并行）。
