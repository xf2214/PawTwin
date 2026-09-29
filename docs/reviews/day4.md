# Day-4 独立审查（2026-09-29）

> **审查者**：非作者独立审查（CodeReview 子代理）。**Reviewer 未编写被审代码**，符合 `docs/agents/reviewer.md` L15「不得由作者充当」。
> **审查范围（explicit target）**：`b1f508a..HEAD` 共 5 个提交 —— `c4ae5f8`(G2 访问控制)、`a37c161`(G4/G5 fail-closed 脚本与文档一致性)、`94442b5`(G7 标签证据驱动 + 390px 修复)、`f3b96e4`(G7 反伪造守卫 + FE-04 六条 e2e)、`63f3de6`(G9 文档)。
> **判定基准**：[Day-4 开发计划](../plans/PawTwin_Day4_开发计划.md) 的 14 条裁定、G0–G9 门、§6 的 DoD 与禁止表述清单、§0.1 的 F1–F15 实测事实表；`AGENTS.md` 诚实红线；总方案 A01–A14 与 L103/L106/L153。
> **审查方式**：只读（`git diff`/`git show`/源码与文档核对），未修改任何文件。

## 1 总体结论

**PASS**（无 blocker、无 important、无 nit）。

Day-4 的五个提交在代码正确性、fail-closed 设计、测试鉴别力与文档诚实性上均未发现需修复项；改动严格对应计划裁定，未越界实现用户明确排除的项。

> **总负责人对「零发现」的处理**：Day-2 为 PASS-WITH-NITS（1 重要 + 6 nit）、Day-3 为 PASS-WITH-NITS（3 nit），故本轮「零 nit」本身被当作**待验证的断言**而非结论。总负责人独立复核了其中三条最可能自我美化的判断，全部成立（见 §4）。

## 2 逐条核实表（审查者结论）

| # | 检查点 | 结论 | 证据 | 要点 |
|---|---|---|---|---|
| 1 | cookie `Secure` 改造正确性 | ✅ | `backend/pawtwin/api.py` 的 `_cookie_secure` | `https` 直连**先于**读头即返回 True，不存在被削弱的输入；`X-Forwarded-Proto` 取首值、`.lower()`、空值安全；该头**只能加**不能减 `Secure`；本地 HTTP 仍不带 `Secure`（现有 e2e 不受影响） |
| 2 | A12 测试鉴别力 | ✅ | `tests/test_auth.py` 新增 3 条 | 401→403→404 门序断言正确表达「未登录不泄露 run 是否存在」；`https` 用例在 docstring 内**诚实标注**为 TestClient 的 scheme 伪造、不等于真实 TLS 验证；负向验证已做（回退后 2 条转红） |
| 3 | `available` 反伪造守卫 | ✅ | `tests/test_feedback_api.py:310/321-327` | 白名单恰为 `{models.py, memory.py, agentcore_client.py}`；正则覆盖单/双引号变体，注释中出现同样触发（设计如此：强制显式重新裁定）；三条运行时守卫覆盖 POST/GET/`state` + `build_memory` + 无凭据 `AgentCoreMemory`，`pytest.fail` 位于 `else` 分支（方向正确） |
| 4 | 390px 溢出是「真修」而非遮掩 | ✅ | `frontend/src/styles.css`（+37 行） | 手段为 `flex-wrap: wrap`、`overflow-wrap: anywhere`、`min-width: 0`；**无** `overflow-x: hidden`、`display: none`、字体缩小或文本截断；断言仍是 `toBeLessThanOrEqual(0)`，未放宽、未 `test.skip` |
| 5 | 标签证据驱动是否彻底 | ✅ | `frontend/src/App.tsx` | 「真实模型」仅在 `request_id` 非空时出现；「可检索」仅在 feedback 列表真有 `available` 时出现（本地不可达）；`aws_connected` 由服务端字段驱动、本地恒 false；`storage` 明写「`repo_dynamo` 未实现」 |
| 6 | 两条 fail-closed 脚本 | ✅ | `scripts/deploy.ps1`、`scripts/cleanup.ps1` | **所有**代码路径终于 `Stop-NotExecuted`（exit 2）：deploy 6 个出口、cleanup 5 个出口，无 `exit 0`；CLI 存在性门在任何 AWS 调用之前；无预填 account id/region/表名/memory id/模型 id；授权令牌为**运行期参数**而非硬编码放行；`.SYNOPSIS` 首句即声明「无 CLI 时不产出任何 plan」 |
| 7 | 契约与门 0 不变式 | ✅ | `git diff` 实测 | `contracts/*`、`tests/test_contracts.py`、`tests/test_app.py` **零改动**；`openapi.json` 仍 14 路径；`domain.schema.json` 的 `$defs` 仍恰为 6 输入模型 + `RunState`；`==` 断言与 `/readyz` 503 精确断言均未放宽 |
| 8 | 文档诚实性 | ✅ | `docs/STATUS.md` Day-4 段、`docs/evidence/day4-*.md`、`docs/TASKBOARD.md` | 计划 §6 禁止表述逐条 grep **0 命中**；G8 在结论出具前被诚实标注为「未出具结论」；实测数字（192/10、e2e 16、14 路径、退出码 2 与 0、Audited 63、Resolved 65）与 evidence 自洽；Day-1/2/3 历史段**只追加后记**未改写 |
| 9 | 范围合规 | ✅ | `git diff --stat` | 无 `repo_dynamo.py`、无 `scenarios.json`/`evaluate.py`、无登录限速、无会话持久化、无记忆轮询接线；变更文件严格限于计划所列 |
| 10 | 测试质量通病 | ✅ | 全部新增测试 | 无缩进/作用域错误致断言不执行（本项目历史缺陷）；无 `waitForTimeout` 掩盖竞态；`toHaveCount(0)` 为有效的「元素不存在」断言而非空断言 |

## 3 诚实红线专项（负面确认）

审查者逐条确认**未发现**下列红线被违反：以本地替身/stub/SQLite 冒充云端完成；skipped 未具名（10 条 skip 全部具名）；生成契约被手改；声称「已部署 / HTTPS 可访问 / 镜像已构建 / 可一键部署」；声称「A12 通过」（文档明写「**A12 不记通过**」）；声称「G8 通过」；声称「CI 全绿 / 已推远程」；声称「契约冻结 ID 已回填两个」（文档明写只回填 `590aa5a` 并披露 Day-2 的 11 路径点从未入库）；预填费用金额/延迟/准确率。

审查者认为文档措辞整体严谨，未提出必须改写的句子。

## 4 总负责人对审查结论的独立复核（不采信自评）

对三条最关键、最可能「自我美化」的判断亲自回源码验证：

1. **`feedback.spec.ts` 的 4 行改动是收紧还是放宽** → **收紧**：禁止子串由 `已可检索` 改为 `可检索`（`not.toContainText` 的匹配面变宽），断言强度提升，非放宽。`[证据: git diff b1f508a..HEAD -- frontend/e2e/feedback.spec.ts]`
2. **390px 修复是否用裁切遮掩溢出** → **否**：新增规则为 `@media (max-width: 900px)` 内的 `.actions { flex-wrap: wrap }` + `.actions button { flex: 1 1 45% }`，以及证据行的 `.evidence-list li { display:flex; flex-wrap:wrap; min-width:0 }` + `li > * { min-width:0; overflow-wrap:anywhere }`；**限定在窄屏媒体查询内，桌面布局不变**；全 diff 无 `overflow-x: hidden`/`display:none`/字体缩小/文本截断。注释还给出了根因算式（三个 `flex-basis:140px` 按钮 + 2×10 gap + 44 padding = **384px** > 390px 视口下的 366px 可用宽）。`[证据: frontend/src/styles.css:459-474 及证据行规则]`
3. **静态守卫白名单是否过宽** → **不过宽**：实测 `Select-String -Path backend/pawtwin/*.py -Pattern '["''](available|processing)["'']'` 命中的文件**恰为** `agentcore_client.py`、`memory.py`、`models.py`，与 `_ALLOWED_LIFECYCLE_WRITERS` 完全一致，无多余放行。

复核结论：审查者的 PASS 判定**可采信**；无需修复项，故无复测。

## 5 遗留与后续（不属本轮阻断）

1. **G8 之后的改动需重新审查**：本审查覆盖到 `63f3de6`。若后续为落地审查建议或 Day-5 工作再改动 `api.py`/`App.tsx`/脚本，须重跑本文件 §6 的复测清单并追加审查记录。
2. **仍未闭合的三项公网前置硬门**（裁定 14，待用户裁定，审查者确认未实现且未被声称为已实现）：登录限速/失败退避、会话 TTL（`Session.created_at` 无消费者）、默认口令 `local-demo-passphrase` 必须被环境变量覆盖。
3. **尽力项未完成部分**（顺延，非阻断）：`infra/` 纯文本 IAM/CFN 草案、费用表把公网 IP 与 ALB LCU 拆为独立行、`preflight.ps1` 的真实 `-Mode` 参数、`/readyz` 真实连通判据的设计文档。
4. **工作区遗留物**：另一执行体的审查工作产物 `_review_diff_day4.txt`（97 KB）未入库、未被忽略，应删除或加入 `.gitignore`，**不得入库**。

## 6 若后续修改，建议复测清单

```powershell
uv run --frozen pytest tests/test_auth.py -v          # A12 门序 + Secure 配对断言
uv run --frozen pytest tests/test_feedback_api.py -v  # available 反伪造守卫 4 条
uv run --frozen pytest -q -o addopts=""               # 全量（当前 192 passed / 10 skipped）
./scripts/test-e2e.ps1                                # 16 条 e2e（含 1440/390 视口）
./scripts/deploy.ps1 -PlanOnly; $LASTEXITCODE         # 期望 2
./scripts/cleanup.ps1; $LASTEXITCODE                  # 期望 2
./scripts/verify.ps1                                  # 期望 EXIT=0
```

## 7 第二轮独立审查（同日，覆盖 `c4ae5f8..63f3de6` 全部 Day-4 本地提交，2026-09-29 晚）

第一轮「零发现」后，总负责人对 Day-4 全部本地改动（含第一轮审查之后的提交）另起**第二轮非作者审查**。结论 **PASS-WITH-NITS：0 阻断 / 4 重要 / 8 nit**——第一轮的「无 important」判定在覆盖面扩大后**不成立**，本轮发现已全部回源码核实并处理：

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| 1 | 重要 | `X-Forwarded-Proto` 被**无条件采信**，偏离裁定 5/降级预案 A（「受信开关默认关闭」）；伪造头可让自身会话 cookie 在 http 上带 `Secure`，表现为静默登录循环 | ✅ 已修（`a575a61`）：新增 `PAWTWIN_TRUST_PROXY_HEADERS`（默认 false），采信仅在开关打开时发生；配对测试含「伪造头默认无效」；负向验证（删守卫行→转红）已做 |
| 2 | 重要 | 诚实标签 `available`/`processing` 自身含 e2e 禁串「可检索」——云端合法解锁当日两条 e2e 必假红，且「收紧禁串」的注释前提不成立 | ✅ 已修（`a575a61`）：措辞改为不含禁串的生命周期表述；新增 `tests/test_frontend_labels.py` 2 项源码级耦合守卫（标签禁串 + 「真实模型」只允许出现在证据配对行） |
| 3 | 重要 | 文档高报验证广度：「本机干跑全部路径/全部分支实测」——实际所有组合停在 Gate 1（无 AWS CLI），Gate 2–4 与「过门仍拒」路径从未被执行 | ✅ 已修（`a575a61`）：`infrastructure.md`/`cloud-access-checklist.md` 更正为「5+4 组合实测 exit 2 均停 Gate 1；其余仅代码审读」，并披露参数绑定错误退出码为 1 的边界 |
| 4 | 重要→更正 | 390px 修复注释失真：所称 nowrap 行实际基线已 `flex-wrap: wrap`；算式 `140*3+2*10+44=384` 应为 484；死规则冗余 | ✅ 已修（`a575a61`）：删死规则、注释改正确机制（两 140px 按钮/行 → min-content≈334 + 证据行长 token）；`overflow-wrap: anywhere` 的「桌面不变」降级为「预计不变、未逐项测量」 |
| 5–12 | nit | 静态守卫只证字面量写入（盲区未声明）/ `get_status` 零调用者不变式未固化为断言 / 「真实模型」未与 `backend==='bedrock'` 相与 / `replace('（已配置…）','')` 字符串耦合 / `.truth-strip{overflow:hidden}` 文档级断言盲区 / preflight「恒 0」绝对化（工具缺失时 throw） / 授权令牌两种拼法 / e2e 视口「这不证明什么」措辞 | ✅ 前五项已在 `a575a61` 落地（盲区声明、`get_status` 不变式断言、证据相与、常量拆分、断言措辞）；令牌命名与 preflight 措辞已随 #3 一并更正 |

**复跑（第二轮修复后，干净 HEAD）**：`pytest` **195 passed, 10 skipped**（具名不变）、`ruff` 无告警、契约 current（14 路径）、`typecheck`/`build` 通过、e2e **16 passed**、`deploy.ps1`/`cleanup.ps1` 仍全组合 `NOT EXECUTED`+exit 2。

**对第一轮结论的更正**：§1「无 important」仅对第一轮自身覆盖范围成立；§5.4 所指工作产物 `_review_diff_day4.txt` 已删除（曾一度误入库，`ebe3e11` 移出）。第一轮 §4 的三项独立复核未发现上述问题，说明**同一作者视角的复核不能替代覆盖面更广的第二轮审查**——此教训适用于后续各日。
