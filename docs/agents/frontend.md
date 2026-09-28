# 前端 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`。认领 FE-01；范围为单页三个主要区域和可折叠演示输入。

保留宠物与请求、建议审批、任务与记忆。传感器模拟、执行器模拟、项圈概念、AWS 未连接等标识必须真实。不要用固定成功结果填补缺失后端；后端契约未冻结时可做明确标注的组件预览，不宣称系统已工作。

初始化中的 bootstrap API 不是业务契约。后端 BE-01 发布业务 OpenAPI 后再实现类型化调用。由后端状态决定批准按钮与执行结果，反馈保存与长期记忆 available 分开显示。

仅写 frontend/src、样式和前端测试；依赖与共享生成文件通过总负责人协调。验证类型、构建、关键浏览器行为、桌面及窄屏，不做对源码字符串的无意义测试。按交接模板交付。

## Day-2 派发（FE-02）

当日分解见 `docs/plans/PawTwin_Day2_开发计划.md`。认领 FE-02：证据面板（`evidence-list`/`evidence-item`，只显示工具名/来源/检索时间/摘要，**不显示事件 note 原文与任何隐藏推理**）、调用遥测（后端/调用次数/tokens/耗时/`request_id`，为 null 时如实显示「无（未发生真实云调用）」）、`impl-labels`（analyzer/storage/memory）、演示控制区接 `demo/facts` 与 `demo/device-mode`、事实为 null 时显示「未知」而非 0、中间态与显式超期提示。

轮询预算必须**严格大于**后端 45 秒分析超时（现取 75 秒，15 秒后退避），且**前端无权宣告失败**：超期只显示「仍在处理，请刷新」。`mode-badge` 必须保留 `LOCAL` 与 `AWS 未连接` 两个子串，新标签放在新的 testid 上，且不得复用 truth-strip 的精确文案（Playwright 严格模式下多命中即失败）。

e2e：`playwright.config.ts` 用 `workers: 1` + `expect.timeout: 20s` + `webServer.env` 显式指定 `PAWTWIN_WORKER_MODE=background`；每个业务 spec 开头经 `helpers.resetDemo` 复位事实与设备模式，因为所有 spec 共享同一进程与同一内存库（上一个 spec 的记账会把 `last_fed_minutes_ago` 置 0，使下一个吃饭请求变 `BLOCKED`）。`retries` 保持 0，不得用重试掩盖真实竞态。仍为零新增运行时依赖。

## Day-3 派发（FE-03）

当日分解见 `docs/plans/PawTwin_Day3_开发计划.md`。认领 FE-03：把「任务与记忆」区的 Day-2 占位换成**记忆区**——主人反馈输入（text + scope `observation`/`today_only`）、提交 `POST /api/feedback`、反馈列表带 `memory_status` 徽章与 `memory_backend` 标签、「开启新会话」按钮 `POST /api/demo/new-session` 并显示 `conversation_id`；`api.ts` 增 `FeedbackView`/`MemoryStatus`/`postFeedback`/`getFeedback`/`postNewSession` 与 `StateView.conversation_id`/`feedback`，**零新增依赖**。

诚实红线：`memory=not_implemented` 时显示「长期记忆：未实现（无 AWS 账号）」、反馈状态「已保存原文（未提炼）」，**绝不**显示「已检索到记忆」或把 `saved` 说成已提炼；`impl-labels` 仍须保留子串「长期记忆：未实现」，`mode-badge` 仍须保留 `LOCAL`/`AWS 未连接`。e2e 新增 `feedback.spec.ts`（提交→`saved`+未实现标签、new-session→`conversation_id` 变化、reload 后反馈仍在、记忆区绝不声称检索到记忆）；沿用 `workers:1`/`expect.timeout:20s`/各 spec 自复位。
