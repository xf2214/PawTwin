# PawTwin Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 用户已选择由 Agent 全程开发，不再重复询问执行方式。

**Goal:** 在五个工作包内交付真实 AWS 软件核心、明确模拟输入与执行边界的单宠物照护原型。

**Architecture:** React 页面与 FastAPI API 作为一个应用容器运行；Strands 使用 Bedrock 调用只读事实和记忆工具并提出建议。业务层负责审批、硬性策略、幂等、模拟动作及回执；DynamoDB 持久化，AgentCore 提供异步长期记忆。

**Tech Stack:** React、TypeScript、Vite、Python 3.12、FastAPI、Pydantic、Strands、boto3、pytest、Playwright；ECS Express Mode、Bedrock、DynamoDB、AgentCore Memory、ECR、CloudWatch。依赖在开工时选择互相兼容的稳定版并锁定，不预填未经验证的版本号。

**Spec:** [PawTwin 五日开发总方案](PawTwin_五日开发总方案.md)。执行者先读两个文件；本文件规定默认技术接口，任何变更由总负责人同时更新接口、测试和本文。

## Global Constraints

- 一个网页、一个产品 Agent、一个模拟执行器、三种核心场景。
- 开发过程可以使用多个 Agent，产品不使用多 Agent 编排。
- 正式云端模式禁用悄悄回退到替身。
- 传感器事件为模拟；设备执行为模拟；项圈为概念设计。
- 当前事实、配额与审批来自业务数据库；长期记忆不能承担执行授权。
- 所有喂食动作在本次 MVP 中必须获得主人明确审批；硬配额不允许通过审批绕过。
- 未授权请求不能读取业务数据、触发模型或批准任务。
- 不在任务描述、源码、日志或前端存放 AWS 长期凭据。
- 本机按 Windows 原生环境执行，不假设 WSL；容器由已可用的 Docker 环境提供。缺少 Docker 时先完成源码与测试，部署 Agent 另行列明构建依赖，不静默安装或重构系统。
- 目前用户没有 AWS 账号；本地联调和真实 AWS 验证分别记账。
- 本次只编制计划；开始实施时先读对应实施技能，再创建项目，不把此计划的示例代码当作已实现代码。

## 1 项目与文件职责

实施时拟创建项目根目录 `outputs/pawtwin-app/`。以下路径均相对该根目录，目前尚不存在。总负责人拥有根级依赖、共享契约、容器和集成文件；子 Agent 不得同时修改共享文件。

```text
AGENTS.md                         范围、命令、所有权与交接要求
README.md                         本地/云端启动及真实与模拟边界
pyproject.toml / uv.lock           Python 依赖与测试配置
contracts/openapi.json            从后端类型导出，唯一 API 契约
backend/pawtwin/main.py            生命周期、路由挂载、静态页面
backend/pawtwin/config.py          模式、区域、模型、限额
backend/pawtwin/models.py          全部请求/响应与状态枚举
backend/pawtwin/auth.py            演示登录、会话、CSRF、访问检查
backend/pawtwin/repository.py      持久化协议
backend/pawtwin/repo_sqlite.py     本地事务与去重
backend/pawtwin/repo_dynamo.py     云端条件写入与事务
backend/pawtwin/policy.py          硬性策略与执行前检查
backend/pawtwin/workflow.py        任务、建议、审批和回执转换
backend/pawtwin/worker.py          租约领取、期限、恢复
backend/pawtwin/device_sim.py      显式模拟执行器
backend/pawtwin/agent.py           Strands / Bedrock 与有限工具
backend/pawtwin/memory.py          AgentCore 写入、状态、检索
backend/pawtwin/api.py             API 输入、权限、错误映射
backend/pawtwin/local_fakes.py     仅 local 模式使用的替身
frontend/src/App.tsx              三个主区与演示控制区
frontend/src/api.ts               类型化接口与轮询
frontend/src/components/          请求、建议审批、任务记忆组件
frontend/src/styles.css           页面样式
frontend/package.json             构建、类型检查与浏览器测试
tests/test_*.py                   策略、数据库、审批、记忆等测试
tests/e2e/                        浏览器完整场景
tests/cases/scenarios.json        20–30 条独立验收输入
infra/                            资源定义与 IAM 权限模板
scripts/preflight.ps1             本机/AWS/模型/记忆检查
scripts/deploy.ps1                可重复部署与输出清单
scripts/cleanup.ps1               先列出再删除，验证残留
scripts/evaluate.py               执行案例并记录实际指标
Dockerfile                       构建页面并打包单应用
docs/evidence/                    测试结果与调用摘要，无秘密
docs/submission/                  英文说明、演示、边界声明
```

不额外拆微服务，不先建设组件库、插件系统、泛化 Agent 平台或多租户产品。

## 2 共享数据与接口契约

以下字段为必需的最小契约。所有外部输入严格校验、禁止额外字段；时间使用带时区 UTC，`pet_id` 固定为 `mochi`。ID 使用 UUID；服务端校验会话，客户端不能自行指定家庭或操作者身份。

```python
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class RunState(StrEnum):
    QUEUED = 'queued'
    ANALYZING = 'analyzing'
    NEEDS_INFO = 'needs_info'
    BLOCKED = 'blocked'
    AWAITING_APPROVAL = 'awaiting_approval'
    DECLINED = 'declined'
    EXPIRED = 'expired'
    EXECUTING = 'executing'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    UNKNOWN = 'unknown'

class EventIn(StrictModel):
    event_id: str
    pet_id: Literal['mochi'] = 'mochi'
    kind: Literal['food_request', 'attention_request']
    room: Literal['kitchen', 'living_room', 'unknown']
    note: str = Field(default='', max_length=500)
    source: Literal['simulator'] = 'simulator'

class Action(StrictModel):
    kind: Literal['dispense_food', 'create_play_task', 'observe']
    grams: int = Field(default=0, ge=0, le=15)

class Proposal(StrictModel):
    action: Action
    explanation: str = Field(max_length=1200)
    evidence_ids: list[str]
    missing_fields: list[str] = []

class ApprovalIn(StrictModel):
    decision: Literal['approve', 'decline']
    proposal_version: int
    action_digest: str

class FeedbackIn(StrictModel):
    text: str = Field(min_length=1, max_length=500)
    scope: Literal['observation', 'today_only']

class Receipt(StrictModel):
    command_id: str
    status: Literal['succeeded', 'failed', 'unknown']
    simulated: Literal[True] = True
```

业务记录还包含 `run_id`、`owner_id`、`facts_version`、`proposal_version`、`action_digest`、`expires_at`、`lease_owner`、`lease_until`、`attempt_count`。服务端创建这些字段。展示型宠物表达是推测文案，不能作为策略输入。

| HTTP 接口 | 输入与输出 | 约束 |
|---|---|---|
| POST /api/login | 演示口令 → HttpOnly 会话 | HTTPS、限速、口令服务端哈希验证 |
| POST /api/logout | 会话 → 204 | 撤销会话 |
| GET /api/state | → 宠物当前事实、任务、模式标签 | 需登录，响应不含凭据 |
| POST /api/events | EventIn → 202 `{run_id,state}` | 按 owner_id + event_id 去重 |
| GET /api/runs/{run_id} | → 任务、Proposal、证据、回执 | 不暴露隐藏推理或完整模型请求 |
| POST /api/runs/{run_id}/approval | ApprovalIn → 任务状态 | 需登录与 CSRF，绑定参数与版本 |
| POST /api/feedback | FeedbackIn → `{feedback_id,memory_status}` | 来源固定为主人观察 |
| GET /api/feedback/{feedback_id} | → saved/processing/available/failed | available 需要真实检索证据 |
| POST /api/demo/facts | last_fed_minutes_ago、daily_dispensed_grams | 合法范围，更新 facts_version |
| POST /api/demo/device-mode | success/failure/unknown | 仅演示模拟器，影响新命令 |
| POST /api/demo/new-session | → 新 conversation_id | 保留宠物记忆，不重置登录/事实 |
| GET /healthz | → 200 liveness | 不触发模型、不泄露配置 |
| GET /readyz | → ready/degraded | 检查必需配置与依赖缓存状态 |

演示事实初值：上次喂食距今 360 分钟、当日模拟出粮 0 g；演示配额 30 g、单次 15 g、最短间隔 120 分钟。这些仅用于软件测试，页面标注非喂养建议。新会话不重置配额。

`grams=0` 仅允许 observe/create_play_task；dispense_food 必须为 1–15。缺少最近喂食时间、当日累计或来源失效时停止喂食建议。硬限制只由程序判定。

执行器接口 `execute(command_id: str, action: Action) -> Receipt`；`command_id` 从 run_id 和 proposal_version 确定生成，重试不能更换。数据库唯一键保证一条逻辑回执与一次记账。

产品 Agent 只提供四种工具：`get_pet_facts(pet_id)`、`get_recent_events(pet_id, limit)`、`search_owner_memory(pet_id, query)`、`get_policy_summary(pet_id)`。工具由服务端注入授权范围；模型不能传入任意 owner_id。最终输出 Proposal，不能直接执行设备或批准自己的提案。

## 3 并行安排与依赖

```text
T0 环境与账号路线 → T1 数据契约与状态 → T2 策略/审批/执行
                            ├→ T3 单页前端（按冻结接口并行）
                            └→ T4 Bedrock 与工具 → T5 个体记忆
T2 + T3 + T4 + T5 → T6 集成与独立审查 → T7 云部署 → T8 材料与发布候选
```

云端最小调用在账号就绪后立即进行，不等到 T7。T7 是完整应用部署验收。最多同时运行总负责人和三个子 Agent；作者不能独自批准自己的任务。

每个任务将检查拆为可复现动作，先运行相关测试见到预期失败，再实现，再通过检查后提交。可逆的样式/文字修改不编写镜像实现的低价值测试，以浏览器检查验收。

## T0 环境、账号与真实调用预检

**Owner:** 总负责人 + 云部署 Agent。**Files:** `AGENTS.md`、`scripts/preflight.ps1`、`docs/evidence/preflight.md`、根级依赖。**Produces:** 本地工具清单、明确的 local/aws 配置、账号阻塞记录、选定区域与模型。

- [ ] 检查 Git、Node、Python、Docker 与 AWS CLI 实际路径/版本；读本机已有配置但不输出凭据；缺少工具记录依赖。
- [ ] 建立项目与 Git；锁定依赖；将编译产物、虚拟环境、密钥和本地会话排除。
- [ ] 获得本次赛事官方链接后立即核对赛道、指定服务、开发时间限制和模拟边界；缺少链接时将赛事资格标为未核实，只推进通用本地核心，T8 再核对提交材料。
- [ ] 定义 `PAWTWIN_MODE=local|aws`；aws 模式缺模型 ID、区域、表或记忆 ID 时启动失败，不回退替身。
- [ ] 用户注册期间完成本地 smoke；其登录后用已授权身份核实账号、可用区域与权限。
- [ ] 候选区域先检查 us-west-2；若服务或模型不满足，记录交集后选择实际区域，不硬编码账号。
- [ ] 先输出最小云端验证与后续部署的费用估算和资源清单，获得对应费用授权后再创建资源或调用收费模型；不会凭本计划创建收费资源。
- [ ] 在已授权的最小验证资源中完成一次真实模型工具往返、一次数据库条件写入、一个 memory strategy ACTIVE 检查；记录 request ID/时间，移除秘密。

配置预期检查：
```python
def test_aws_mode_never_silently_uses_fake(monkeypatch):
    monkeypatch.setenv('PAWTWIN_MODE', 'aws')
    monkeypatch.delenv('BEDROCK_MODEL_ID', raising=False)
    from pawtwin.config import load_settings
    import pytest
    with pytest.raises(ValueError, match='BEDROCK_MODEL_ID'):
        load_settings()
```

命令约定：Python 检查使用 `uv run pytest`；前端使用 `npm run typecheck`、`npm run build`、`npm run test:e2e`，均在其所属目录执行。预检必须真实配置这些命令后再派发任务。

## T1 数据契约与持久化任务

**Owner:** 后端 Agent。**Files:** models、repository、repo_sqlite、repo_dynamo、worker、`tests/test_repository.py`。**Consumes:** T0 settings。**Produces:** `Repository.create_or_get_run(owner_id, event)`、`claim_run(run_id, worker_id, lease_until)`、`get_run(run_id)`、`append_fact(...)`、`record_receipt_once(...)`。

- [ ] 用共享契约建立 Pydantic 类型；校验 UUID、文本长度、受支持的事件类型和宠物 ID。
- [ ] 写去重测试：相同 owner/event_id 返回同一 run；新 event_id 创建独立 run。
- [ ] SQLite 使用事务和唯一约束；DynamoDB 使用条件写入/事务实现同一语义。创建单表与用于可领取任务的索引，不扫描整表轮询。
- [ ] 领取租约默认为 60 秒、每 15 秒续约；分析任务最多两次处理尝试；单次分析超时 45 秒，终止为 FAILED 并记录原因。
- [ ] 重启时领取过期租约；终态不重复处理；未知执行状态仅核对同一 command_id 回执，不重新出粮。
- [ ] 导出 OpenAPI，冻结契约后通知前端和 AI Agent；通过测试后提交。

测试样例（`repo` fixture 是两种实现共用的适配器 fixture）：
```python
def test_event_redelivery_does_not_create_second_run(repo, food_event):
    a = repo.create_or_get_run('demo-owner', food_event)
    b = repo.create_or_get_run('demo-owner', food_event)
    assert a.run_id == b.run_id
    assert repo.count_runs('demo-owner') == 1
```

`food_event` fixture 使用 EventIn，独立 UUID；`repo.count_runs` 仅测试适配器辅助方法。DynamoDB 云测试需要真实测试表，未运行要单列，不得用 SQLite PASS 代替。

## T2 策略、审批与模拟执行

**Owner:** 后端 Agent。**Files:** policy、workflow、device_sim、auth、api、`tests/test_policy.py`、`tests/test_approval.py`、`tests/test_recovery.py`。**Consumes:** T1 repository + Proposal。**Produces:** 可通过 API 真实执行的状态机。

- [ ] 实现 `evaluate_policy(action, facts) -> PolicyResult(allowed, reason)`，涵盖缺失事实、最近喂食、单次/每日额度。
- [ ] 新提案只进入 AWAITING_APPROVAL/BLOCKED/NEEDS_INFO；批准期限为十分钟；owner/版本/digest/有效期全部匹配才接受。
- [ ] 批准与执行前都检查必要事实；facts_version 改变时先拒绝旧授权，重新分析再请求批准。
- [ ] 在一个事务中预留配额并进入 EXECUTING，避免两个不同任务竞争同一配额；成功确认预留，失败释放，unknown 保留并核对，不盲目重试。
- [ ] 用固定 command_id 调用模拟执行器，成功/失败/unknown 都有真实回执；只在成功后记账。
- [ ] 演示口令服务端哈希存储；会话 HttpOnly、Secure（仅本地 HTTP 模式例外）、SameSite、CSRF；未授权 API 返回 401/403。
- [ ] 运行拒绝、过期、参数篡改、双标签批准、不同任务配额竞争及重启测试；通过后提交。

策略测试示例（Facts 与 PolicyResult 在 policy.py 定义，字段不可另起名称）：
```python
def test_recent_feed_blocks_even_if_model_suggests_food():
    from pawtwin.policy import Facts, evaluate_policy
    from pawtwin.models import Action
    facts = Facts(last_fed_minutes_ago=20, daily_dispensed_grams=15,
                  daily_limit_grams=30, minimum_interval_minutes=120)
    result = evaluate_policy(Action(kind='dispense_food', grams=15), facts)
    assert result.allowed is False
    assert result.reason == 'RECENT_FEED'
```

## T3 单页界面与演示输入

**Owner:** 前端 Agent，与 T2/T4 并行。**Files:** frontend 内文件与 `tests/e2e/approval.spec.ts`。**Consumes:** T1 OpenAPI。**Produces:** 实际请求 API 的单页，不内置结果脚本。

- [ ] 做宠物请求、建议审批、任务记忆三块区域；模拟标签固定可见；local/aws 连接状态来自后端。
- [ ] 演示控制只支持契约字段；同场景允许不同时间和反馈内容，不能以场景名称选择固定答案。
- [ ] POST 事件后每两秒 GET 任务，终态停止；超过任务期限显示明确失败/未知，不无限 loading。
- [ ] 只有服务端状态为 AWAITING_APPROVAL 才显示批准；提交中禁用按钮，但幂等仍由后端保证。
- [ ] 记忆展示 saved/processing/available/failed；反馈归因为主人观察，短期备注不显示为永久偏好。
- [ ] 检查桌面 1440px 和窄屏 390px；无溢出、重要状态不只靠颜色。
- [ ] 运行类型/构建检查和一条有意义的审批浏览器测试，提交。

浏览器测试示例（测试服务在 local 模式，fixture 完成 demo 登录）：
```typescript
test('decline never becomes simulated execution', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: '发送吃饭请求' }).click();
  await expect(page.getByText('等待主人确认', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: '拒绝本次动作' }).click();
  await expect(page.getByText('已拒绝', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('已拒绝', { exact: true })).toBeVisible();
  await expect(page.getByText('模拟执行成功', { exact: true })).toHaveCount(0);
});
```

## T4 Bedrock 推理与证据工具

**Owner:** AI Agent。**Files:** agent、local_fakes、`tests/test_agent.py`、真实调用证据。**Consumes:** T1 repo、T2 policy summary、T5 memory 接口（可先用显式空结果）。**Produces:** `analyze_event(event, context) -> Proposal`。

- [ ] 四个只读工具读取实际 repo/memory adapter；每次调用生成 evidence_id 与来源，绑定当前 owner/pet。
- [ ] 限制每个任务四次模型调用，输出上限 800 tokens；配置 SDK 超时/重试使应用能在 45 秒任务期限内结束。
- [ ] 用结构化输出解析 Proposal；不存在的 evidence_id、越界参数、空事实下的肯定结论拒绝或转 NEEDS_INFO。
- [ ] 将用户内容、事件 note、检索记忆视为资料；不能修改策略和工具权限。
- [ ] local 替身仅验证 UI/状态机；aws 测试实际调用已选模型，不允许异常时返回预制建议。
- [ ] 做相同请求/不同喂食事实的对照及指令注入测试；记录工具结果和最终简短解释，不保存隐藏思维链。
- [ ] 独立审查核实 AWS request ID、工具记录和页面对应，提交。

关键验证示例：
```python
def test_unknown_evidence_id_is_rejected():
    from pawtwin.agent import validate_proposal_evidence
    from pawtwin.models import Proposal, Action
    import pytest
    proposal = Proposal(action=Action(kind='observe'), explanation='观察',
                        evidence_ids=['invented-id'])
    with pytest.raises(ValueError, match='UNKNOWN_EVIDENCE'):
        validate_proposal_evidence(proposal, available_ids={'fact-1'})
```

## T5 主人反馈与真实长期记忆

**Owner:** AI Agent，T4 后。**Files:** memory、相关 API、`tests/test_memory.py`、`docs/evidence/memory.md`。**Consumes:** FeedbackIn 与 repo。**Produces:** `submit_feedback(...)`、`search_owner_memory(...)`、明确的 processing 状态。

- [ ] 先保存反馈原文、反馈 ID、主人来源与 scope；today_only 留在有时效的业务记录，不生成永久偏好。
- [ ] AgentCore strategy 必须 ACTIVE 后才发送需长期提炼的 observation；按 owner/pet namespace 隔离，session_id 不充当宠物身份。
- [ ] 使用官方支持的 SDK 载荷提交反馈，记录实际 event ID；重试复用本地 feedback ID 并记录已提交状态，防止重复发送。
- [ ] 每十秒查询提炼是否可检索，最长等待三分钟后仍显示 processing 并允许继续检查，不宣称已生成。
- [ ] available 必须能列出实际 memory record ID、namespace 和来源关联。若内置策略无法可靠保留 feedback ID，用来源 metadata/原始反馈映射验证，不仅依据模型生成的相似文案。
- [ ] 新会话实际 retrieve；近期原始反馈可辅助建议，但在证据中与 AgentCore 记忆分开显示。
- [ ] 测试相互矛盾的旧观察、today_only、来源缺失、服务失败；跨会话云端测试独立记录后提交。

关键测试示例：
```python
def test_saved_feedback_is_not_available_memory(memory_service):
    result = memory_service.submit_feedback(
        owner_id='demo-owner', pet_id='mochi',
        text='我观察它饭后有时想玩', scope='observation')
    assert result.feedback_saved is True
    assert result.memory_status in {'saved', 'processing'}
    assert result.memory_record_ids == []
```

`memory_service` fixture 使用可控 SDK adapter，保证提炼未完成；另一个真实 AWS 测试才用于证明云端 memory available。

## T6 集成与独立审查

**Owner:** 总负责人 + 未编写对应模块的审查 Agent。**Files:** scenarios.json、evaluate.py、测试与 evidence。**Consumes:** T2–T5。**Produces:** 可审查的候选版本。

- [ ] 建立至少 24 条工作流案例，覆盖总方案 A01–A14；记录 expected_state、expected_policy、maximum_receipt_count 和 required_evidence_sources。
- [ ] 固定案例核对状态与副作用；AI 文案仅检查依据、行为和不确定性，不比较完整字符串。
- [ ] 明确测试夹具、local 替身、真实 AWS 三类结果，不混合计算成功率。
- [ ] 做同事件重复、不同事件并发配额、审批篡改、处理重启、设备 unknown、未授权读取与注入。
- [ ] 独立 Agent 先审范围，再审实现；记录发现、修复及复测结果。
- [ ] 只报告真实测量的延迟、通过率和失败，不预设获奖或准确率；通过后提交。

案例格式示例：
```json
{"case_id":"A02-decline","mode":"local","event_kind":"food_request",
 "facts":{"last_fed_minutes_ago":360,"daily_dispensed_grams":0},
 "decision":"decline","expected_state":"declined",
 "maximum_receipt_count":0,"required_evidence_sources":["facts"]}
```

## T7 AWS 部署与访问验证

**Owner:** 云部署 Agent + 总负责人。**Files:** Dockerfile、infra、deploy/cleanup/preflight 脚本、README。**Consumes:** T6 候选、真实账号、已确认资源预算。**Produces:** HTTPS 测试地址与资源清单。

- [ ] 构建单镜像；验证容器中静态页面、API、worker 与 healthz；静态文件路径不能覆盖 /api。
- [ ] 配置应用 Task Role，仅授权所需模型、项目表、项目记忆；镜像执行角色与基础设施角色分开。
- [ ] 默认一个副本，允许滚动发布；DynamoDB PAY_PER_REQUEST；日志七天；不默认添加 NAT 网关或自定义域名。
- [ ] 使用 ECS Express Mode 支持的资源定义或官方 API 幂等脚本；先生成配置与费用清单，得到用户具体费用授权后才 apply。
- [ ] 建立应用并发/调用上限、预算提醒、所有资源 project 标签；不得把预算提醒说成硬性停费。
- [ ] 从未登录浏览器验证拒绝访问，再登录完成三场景；云端真实 memory 检索、重启与重复批准复验。
- [ ] cleanup 默认 dry-run，仅列本项目 resource IDs；删除前确认范围与保留期限；记录残留检查。
- [ ] 将部署版本、镜像 digest、region、model ID、URL 和测试时间存入 evidence；不记录口令和临时凭据。

部署入口预期形态：
```powershell
./scripts/preflight.ps1 -Mode aws
./scripts/deploy.ps1 -PlanOnly
# 在具体资源与预算确认后执行：
./scripts/deploy.ps1 -Apply
./scripts/cleanup.ps1 -PlanOnly
```

这些脚本在本任务中编写后才能运行，不是当前已经存在的命令。不得跳过角色与区域检查直接复制官方示例中的账号 ID。

## T8 演示与参赛材料

**Owner:** 前端/材料 Agent + 总负责人。**Files:** docs/submission、README、最终 outputs。**Consumes:** T7 实际版本与结果。**Produces:** 用户可审阅的提交包，不自动提交比赛。

- [ ] 核对本次赛事官方规则、截止时间、指定服务、视频/语言要求、源码开放要求及模拟材料边界；2025 历史规则不能代替本次确认。
- [ ] 生成一张项圈佩戴概念图即可，按 imagegen 技能制作并标注概念；不影响主线验收。
- [ ] 三分钟视频：20 秒边界/问题、60 秒正常闭环、40 秒近期已喂变化、40 秒已可检索的个体记忆、20 秒实际验证/架构。
- [ ] 不在三分钟内强行等待新记忆生成；新反馈处理流程可附补充演示，并保留真实状态。
- [ ] 现场测试允许修改受支持的事实/反馈/模拟回执；不得通过场景名称选择预制答案。
- [ ] 准备英文问题说明、AWS 职责、真实/模拟/路线图、测试结果、已知限制、测试访问与部署说明。
- [ ] 记录代码版本并冻结功能；得到用户公开发布/提交授权后再执行对应动作。

## 4 执行结束标准

代码存在不等于完成。正式参赛候选必须同时有：真实 AWS 验证、三场景、A01–A14 的结果、可访问测试版本、访问与费用控制、准确的模拟边界、与实现一致的材料。任一项未完成就列为剩余任务。

如果 AWS 账号或权限未及时就绪，只能交付本地原型与待验证清单，不能标为云端完成。遇到素材或录屏工具限制，应明确说明实际已生成的产物，不以脚本代替视频却称视频交付完成。

## 5 计划自检

- 范围覆盖：正常闭环 T1–T4；个体记忆 T5；可靠性 A01–A14 在 T6；云端与费用 T0/T7；比赛材料 T8。
- 单页与产品单 Agent 上限贯穿各任务；硬件只在 T8 概念展示。
- 依赖顺序：先接口再并行，先状态/策略再设备执行，账号就绪即做云 smoke，完整部署不晚于验证工作包。
- 示例代码为明确的测试与契约，未声称实现已存在；适配器 fixture 在对应任务创建。
- 授权区分：用户已选择 Agent 开发方式；账号注册/条款、具体费用和外部发布分别处理，不重复询问一般编码权限。
