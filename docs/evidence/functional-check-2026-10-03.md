# PawTwin 功能复验与演示排练

检查日期：2026-10-03，Asia/Shanghai；最后一次浏览器全量运行约 17:21。
仓库：`C:\Users\11831\Desktop\hks\outputs\pawtwin-app`；HEAD `31da349` / `chore/bootstrap`，检查对象包含当前未提交实现。

## 结论

本轮重新运行后端、构建和浏览器检查，并增加两个独立浏览器会话的完整演示排练。当前检查范围内没有未解决的功能失败，可以展示本地家庭协作流程。

本轮只新增演示回归测试与检查/展示文档，没有修改产品实现。未新增独立代码审查。自动化通过不代表云接入、真实家庭效果或完整生产验收完成。

## 本次实测

| 检查 | 实际结果 | 说明 |
|---|---|---|
| `./scripts/verify.ps1` | EXIT 0；284 passed、1 skipped、21 deselected，23.72 秒 | 全量默认后端测试；ruff、契约 freshness、TypeScript、production build 同时通过 |
| Playwright 全量 | EXIT 0；27 passed，27.3 秒 | 1 worker、0 retries；端口 8810、内存数据库、异步 worker；新增 1 条完整排练 |
| API 契约 | OpenAPI 52 路径，生成物 current | 原六设备输入及 RunState domain 契约保持稳定 |
| 当前预览 | `http://127.0.0.1:8807/healthz` → `{"status":"live"}` | 独立 `data/extension-preview.db`；内置浏览器登录页已查看，当前捕获的 error/warn 日志为空 |
| 图像检查 | 小屋、成长、助手、照护、日报 5 张排练截图已实际查看 | 是实际测试过程截图；不是正式宣传图或已录制视频 |
| 响应式回归 | 390px / 1440px 浏览器用例通过 | 检查横向溢出、导航及宠物资料隔离；不是全设备兼容性认证 |

唯一 skip 是 `tests/test_restart_subprocess.py::test_kill_a_running_server_mid_analysis_then_relaunch`：现有测试具名跳过“分析中强杀正在运行的 Uvicorn 并重启”尽力项，原因是单机端口/启动不稳定。两个已有子进程恢复测试和逻辑租约测试不等价于该强杀场景。
21 项被默认 marker 排除的是 Bedrock / AgentCore / DynamoDB 真实 AWS 检查，本轮没有执行。上游 Starlette/AnyIO 弃用提示及 Node 颜色环境提示未改变退出结果。

## 功能矩阵

“通过”仅指本轮运行的本地行为检查。

| 功能 | 结果及关键依据 | 测试入口 |
|---|---|---|
| 独立账号与会话 | 注册、刷新恢复、未登录拒绝、CSRF 通过；服务重启后仍需重新登录 | `test_family_extension.py`；`family.spec.ts`；`acceptance.spec.ts` |
| 家庭邀请与角色 | 有限期、撤销、重复接受、称呼不提升权限、管理员移交/退出、即时撤权及异家庭拒绝通过 | `test_family_extension.py`；双账号排练 |
| 档案与多宠物 | 字段编辑、归档恢复、记录保留、新宠物切换和延迟回复隔离通过 | `test_family_completeness.py`；`family.spec.ts` |
| 像素小屋与旧 Home | 俯视房间、正常正面宠物；档案、物品、照片、日记保存与新旧入口共享通过 | `pet-home.spec.ts`；`test_family_extension.py` |
| 人工照护交接 | 领取、转交、完成、延期、编辑、取消、周期实例、版本冲突及双连接只完成一次通过；作者来自实际会话 | `test_family_extension.py`；双账号排练 |
| 成长事实 | kg/g 归一、两次有效记录、纠正/删除、缺失保留、饮食分类通过 | `test_family_extension.py`；`test_family_completeness.py`；`family.spec.ts` |
| 日/周统计 | 实际跨度、家庭当地日、DST、时区变更、历史截点、有效源记录通过 | `test_family_extension.py`；`test_family_completeness.py`；双账号排练 |
| 后台报告与恢复 | 持久化进度、失败重试、导入先于游标推进、重开补跑、迟到/修订后重建通过；报告尚未发送通知 | `test_family_extension.py`；`test_family_completeness.py` |
| 公共记忆与回答 | 候选确认、跨成员/入口引用、纠正/删除/过期失效、冲突与源 ID 通过；实际后端为本地规则 | `test_family_extension.py`；`family.spec.ts`；双账号排练 |
| 受控照护方案 | 待确认不创建任务、确认才安排人工任务、旧上下文不可重绑定、重试不执行设备通过 | `test_family_extension.py`；双账号排练 |
| 参考问答 | 已有年龄资料复用、缺品种/适用依据时说明缺项通过；无数值参考曲线或完整品种知识库 | `test_family_completeness.py` |
| 模拟设备闭环 | 审批/拒绝/失败/未知/额度/重复执行防护通过；模拟出粮与实际摄入分列 | `approve.spec.ts`；`decline.spec.ts`；`acceptance.spec.ts`；`test_family_receipts.py` |
| 迁移可靠性 | 临时库上幂等导入、故障回滚、照片恢复、原库不变及原设备额度共用通过 | `test_family_extension.py` |

## 新增完整排练

代码：[`demo-rehearsal.spec.ts`](../../frontend/e2e/demo-rehearsal.spec.ts)。两个 browser context 独立账号，真实调用本地 API，没有伪造返回值。

1. 展示主人创建家庭；家人小林接受邀请并自选“爸爸”。读取会话确认其角色仍是 `carer`，管理邀请界面不对其开放。
2. 输入两条明确标为 `demo_sample` 的称重：2026-09-25 12:00 为 1.20 kg、2026-10-02 12:00 为 1.35 kg；家庭时区为 Asia/Shanghai。生成 10 月 2 日所属周报，断言 **150 g、12.5%、实际 7 天**，展开来源并核对源 ID。9 月 25 日是该周之前的比较基线，不声称两条记录都在周窗口内。
3. 主人确认“喜欢羽毛棒，饭后先休息”；另一位成员在 Alexa 网页模拟入口提问“它喜欢什么”，得到同一条已确认资料。
4. 主人手动选择方案类型“陪玩”并填写名称；建立待确认方案时检查任务尚不存在；明确确认后才创建人工任务。
5. 家人小林同步、领取并完成，任务卡显示“陪玩 · 已完成”，API 记录其真实 user_id 与 `manual_care` 来源。
6. 主人生成当日日报，日报卡显示人工照护完成 1 次。随后删除该公共记忆，另一账号刷新后重新提问，旧文字不再进入新回答。

初次排练失败是测试定位同时匹配日报和周报中的“人工照护完成 1 次”。查看错误快照确认产品两份报告均正确；将断言限定到日报卡片后全量通过。截图检查还发现排练没有选择陪玩类型、沿用了表单默认人工喂食类型，因此修正演示输入并新增类型断言；无需改变产品代码。增加来源展开检查后再次完整运行，最终为上述 27 passed。

留存证据：[小屋](functional-check-2026-10-03/01-home.png)、[成长与周报](functional-check-2026-10-03/02-growth.png)、[另一成员的回答](functional-check-2026-10-03/03-assistant.png)、[照护完成](functional-check-2026-10-03/04-care.png)、[日报回写](functional-check-2026-10-03/05-daily.png)。截图来自隔离内存测试；测试账号/资料不会出现在预览库。全页截图的固定导航可能出现在页面中段，录屏应按实际视口滚动取景。

## 复现命令

```powershell
Set-Location 'C:\Users\11831\Desktop\hks\outputs\pawtwin-app'
./scripts/verify.ps1

# 独立测试端口/内存库；已有 Chromium 路径只设置在当前进程
. ./scripts/node-runtime.ps1
$runtime = Get-PawTwinNodeRuntime
$env:PAWTWIN_E2E_PORT = '8810'
$env:PAWTWIN_DB_PATH = ':memory:'
$env:PAWTWIN_BROWSER_EXECUTABLE = "$env:LOCALAPPDATA\ms-playwright\chromium-1194\chrome-win\chrome.exe"
& $runtime.NodeExe frontend/node_modules/@playwright/test/cli.js test --config frontend/playwright.config.ts
```

浏览器命令使用 verify 已构建的前端；浏览器路径必须换成检查机器实际安装的版本。当前环境变量只影响该 PowerShell 进程；不要将本机绝对路径写入共享配置。

## 展示前需要保留的实际边界

- AWS 云身份/新家庭存储/模型推理/AgentCore、真实 Alexa 和真实硬件尚未完成接通验收。旧适配器存在不代表已部署；本轮零 AWS 调用。
- 回答与公共记忆是本地规则和确认后的数据库资料。方案类型、标题及时间由主人填写，不能演示成模型自动理解偏好后自行安排。
- 真实家庭试用、真实模型质量/延迟、视频录制、公网访问及赛事资格核查尚未完成。
- 完整离线/未保存表单、屏幕阅读器、生产多副本、长停机压力和分析中进程强杀专项尚未验证。
- 本轮没有打开、迁移或清空原用户 `data/pet-home.db`。此前预览进程已停止，本轮重新启动独立预览；它只在本机服务运行期间可访问。

展示安排见 [`PawTwin_展示方案_2026-10-03.md`](../submission/PawTwin_展示方案_2026-10-03.md)。
