# 后端 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`。首次只认领 BE-01；完整设计依据是 `docs/plans/PawTwin_Agent_实施任务单.md` 的数据契约、T1、T2。

BE-01 建立 repository 协议与本地 SQLite 适配器、任务持久化、同事件 ID 去重、完整业务请求/响应契约。业务 DTO 变更先交总负责人批准并统一导出生成文件。DynamoDB 适配器可以后续独立补齐，未测试不声称完成。

BE-02 在后续明确派发后实现登录/授权、硬策略、审批与模拟执行。关键约束：模型不能执行设备；未批准零执行；审批绑定参数/版本/有效期；执行前重查事实；重复批准与不同任务的配额竞争都只能产生允许的副作用；unknown 回执不盲目重试。

所有权依照 AGENTS.md。不要改前端、AI 模块或根级锁文件；依赖变更提交给总负责人。使用独立工作树，检查原有修改后再动手；完成后按交接模板提交真实测试与未运行云检查。

## Day-2 派发（BE-03）

当日分解见 `docs/plans/PawTwin_Day2_开发计划.md`（其 25 条技术裁定为权威）。认领 BE-03：并发原语（`claim_run` 可领取**白名单**、`renew_lease`、`release_run`、`transition_run` CAS、`attempt_count` 在 claim 的同一条 UPDATE 内**原子**自增）、schema 幂等迁移（`PRAGMA user_version` + 列存在性检查）、`worker.py`（租约循环、准入上限、只在 lifespan 启停）、`demo/facts` 与 `demo/device-mode`、`api.py` 的响应投影与 OpenAPI 错误响应。

Day-2 的三条硬约束：`EXECUTING` 与任何等待人工的状态（`awaiting_approval`/`blocked`/`needs_info`）**绝不可被重新分析**——重分析会递增 `proposal_version`、派生新 `command_id`，从而二次记账；批准必须先 CAS 成功才调用执行器；分析失败一律 `FAILED` + 有界原因码，**绝不回退 inline 或预制答案**。`save_run` 不再写租约与 `attempt_count`。

`repository.py`/`api.py`/`repo_sqlite.py`/`workflow.py`/`worker.py`/`device_sim.py` 属本角色；`models.py`/`config.py`/`main.py`/`contracts/` 属总负责人，跨角色接口（如 `Proposer` seam）必须先在门 0 冻结。

## Day-3 派发（BE-04）

当日分解见 `docs/plans/PawTwin_Day3_开发计划.md`。认领 BE-04：反馈持久化（`feedback` 表、`SCHEMA_VERSION` 2→3、`FeedbackRecord` + `save_feedback`/`get_feedback`/`list_feedback`/`set_feedback_status`、`Idempotency-Key` 幂等去重）；文件库启用 **WAL + busy_timeout** 以支持两连接并发；`worker.py` 由顺序 drain 改为**有界线程池真并发**（池=`max_concurrent_global`，先 `AdmissionControl.try_acquire` 再 claim、per-task 唯一 `worker_id`、处理完 release），闭合 Day-2 nit#6（准入上限获得生产触发路径）；`api.py` 的 `POST/GET /api/feedback` 与 `POST /api/demo/new-session`，`get_state` 回显 `memory`/`conversation_id`/`feedback`。

硬约束：并发不得削弱 Day-2 的 CAS/白名单/租约原语——`EXECUTING` 与等待人工的状态绝不可被重分析；跨进程双批准（两 `SqliteRepository` 指同一文件库）必须 `device.execute` 恰一次、`count_receipts==1`、配额只加一次、败者 409（断言 **DB 不变式**，不依赖共享 device 计数器）。真实 OS 进程重启：文件库两实例逻辑复验（等待审批仍在、终态不重跑、过期租约可领、`ANALYZING`+活租约不二次分析）。会话仍进程内存（裁定 6，重启后重登录），`conversation_id` 存 owner 级进程内、重启复位。跨副本 DynamoDB 属 Day-4，**不以 SQLite/两连接 PASS 冒充**。
