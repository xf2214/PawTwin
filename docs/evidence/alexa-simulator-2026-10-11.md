# ALX-01 Alexa+ 网页模拟体验交付

2026-10-11；用户目标：完成 Alexa+ 网页模拟体验。
工作区：Desktop/hks/outputs/pawtwin-app，chore/bootstrap；起始提交 31da349 加全部现有未提交内容。协调者串行写入，alexa_audit / alexa_ux_review 独立只读复核。无新提交、依赖或锁文件改动；未推送/发布。

## 可体验的流程

1. 打开 http://127.0.0.1:8807/#alexa ，注册本地账号、创建或加入家庭。家庭应用顶部和助手页也有入口。
2. 在助手页保存并确认宠物偏好。进入 Alexa 模拟器，询问“它喜欢什么”，查看同一来源和上下文版本。
3. 点击“新会话”清空本页对话，再问偏好。家庭记录保留，每轮重新读取；历史回复保留当时依据，不充当新事实。
4. 说“安排陪玩”或“安排换水”，核对草案并选择具体时间，准备方案。此时没有任务或设备执行。
5. 明确点击“确认安排人工照护”才创建人工任务。进入照护页，家人实际操作后记录“完成照护”。
6. 返回模拟器，询问“最近完成了什么”，显示最近七天的人工完成记录和 occurrence 来源 ID。修改未来重复任务的名称不会改写过去完成描述。

支持偏好、实测体重、待办、观察、完成记录，以及八类明确“安排”照护指令。名字指向其他已建档宠物时要求切换；多项动作、否定和自动设备请求不产生草案。未解析自然语言日期，用户在草案里选择时间，以浏览器时区显示。

最多保留 20 轮页面内对话；离开/刷新/切宠/切账号清空。不保存聊天历史到家庭库，不提供跨刷新聊天检索，也没有真实模型多轮推理。支持浏览器具备语音合成时手动朗读回复，音色由浏览器决定；未做音频录制/听辨验收。不采集麦克风。

## 接口与安全

- 复用 `/api/family/pets/{pet_id}/chat`、`proposals`、`confirm` 和 Home 人工任务接口，没有新业务路由。
- 回复新增 `care_draft` 与 `context_valid_until`。ProposalInput 可选原 `context_version`/`context_valid_until`，原手工方案客户端仍可使用。
- 方案创建的版本检查和写入在同一存储事务内；确认检查方案版本、当前家庭版本与时间有效期。确认重试保持幂等，任务安排与完成分开。
- 角色、CSRF、撤权和家庭/宠物范围沿用服务端约束。访客不能发起对话/照护写操作。切宠时中止旧请求并重建组件，旧回复/方案不会进入新宠物页面。
- 聊天读取不修改家庭事实版本；数据库记忆原文只作引用，不会作为指令执行。
- `backend=local_rules`、`entry=alexa_simulator`、`request_id=null`、`action_executed=false` 和本地模拟边界可查看。确认只创建人工任务，不调用设备。

修改文件：frontend/src/AlexaSimulator.tsx、alexa-simulator.css、FamilyApp.tsx、main.tsx、family-api.ts；backend/pawtwin/family_api.py、family_models.py、family_views.py、pet_context.py；tests/test_alexa_simulator.py、frontend/e2e/alexa.spec.ts；自动导出的 contracts/openapi.json；README/STATUS/TASKBOARD 和本轮证据。其余现有未提交内容保留。

## 验证

最终已执行：

| 检查 | 命令与结果 |
|---|---|
| 后端/静态/契约/类型/构建 | `./scripts/verify.ps1`：346 passed / 1 skipped / 21 deselected；56.77 秒；ruff、契约、TypeScript、生产构建 PASS，退出 0 |
| 新增后端回归 | `uv run --frozen pytest tests/test_alexa_simulator.py`：13 passed |
| Alexa 定向浏览器 | `npm run test:e2e -- alexa.spec.ts`：8 passed，15.2 秒 |
| 最终全量浏览器 | `npm run test:e2e`：41 passed，1.2 分钟，0 retries，退出 0 |
| 最终静态/契约复查 | 相关 Python 文件 `ruff check` 与 `export_contracts.py --check` PASS |
| 预览 | `/healthz` 与 `/` HTTP 200，8807 本地监听 |

浏览器命令通过仓库 node-runtime.ps1 的兼容 Node 运行。测试设置 `PAWTWIN_E2E_PORT=8811`、`PAWTWIN_BROWSER_EXECUTABLE=<本机 Chromium 路径>`；由 Playwright 启动独立内存测试库，不复用预览或用户库。旧工作台审批/回执/限额、家庭报告/成员/记忆删除与宣传页回归保留。

新增行为覆盖：草案无副作用、原上下文版本和时间失效、访客写入拒绝、实际观察/完成来源、另一宠物名字澄清；共享确认记忆→新会话→照护确认→人工完成、陈旧草案拒绝、延迟响应切宠、失败重试、320/390/1440 方案卡无横向溢出、键盘与减少动画。

首次测试发现缺少草案/版本校验，随后新增时效/观察/历史标题回归并确认红→绿。浏览器初轮存在测试定位错误（完成按钮名称、包含下拉选项文本的 label 精确匹配）；按实际页面快照修正，未增加超时或重试来掩盖失败。

最终截图已保存：[320](alexa-simulator-2026-10-11/alexa-320.png)、[390](alexa-simulator-2026-10-11/alexa-390.png)、[1440](alexa-simulator-2026-10-11/alexa-1440.png)。桌面/手机实际图片已查看，包含待确认方案、能力标记和底部导航。

独立复核发现并修复：中英文相邻宠物名错误匹配、修改重复任务名称污染历史完成描述、账户按钮保留 #alexa 导致无法重新打开。两位 reviewer 最终无待处理发现；后端 reviewer 独立纯函数复验 4/4 PASS。

## 运行与真实性边界

构建后可运行 `./scripts/dev-home.ps1 -Port 8807 -DatabasePath ./data/alexa-preview.db`。本轮隐藏预览服务已启动，数据独立，不覆盖旧 showcase-preview.db/pet-home.db。服务重启需重新登录，家庭记录/任务留在本地 SQLite。旧页面需要刷新加载新构建。

1 skipped 是既有强杀尽力测试；21 项真实 AWS 检查未执行。没有真实 Alexa、Bedrock、AgentCore、硬件、真人试用或参赛资格验收证据；云调用、资源与新增费用 0。后续真实集成仍需独立授权与实际服务证据，本次网页模拟目标已完成。
