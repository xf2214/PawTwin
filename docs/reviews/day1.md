# Day-1 独立审查记录（2026-09-23）

审查者：非作者的独立只读代码审查 Agent（CodeReview 子代理）。范围：本次会话在 `chore/bootstrap` 上的全部 Day-1 改动。审查者独立通读了关键文件、核对 diff，并复跑了契约一致性检查与完整测试套件。

## 结论

**PASS-WITH-NITS**。必过 Gate 全部真实达成，五项安全/正确性确认全部为「是」，**未发现阻断性缺陷**。

复跑证据：`pytest` 69 项全绿；`export_contracts.py --check` 返回 “Contracts are current”。

## 五项逐项确认

| 项 | 结论 | 关键依据 |
|---|---|---|
| (a) 拒绝不执行任何动作 | ✅ 确认 | `device.execute` 唯一调用链仅在 approve 分支；decline 直接置 `DECLINED` 返回。`test_decline_loop`/`test_approval` 断言 `receipt is None`、`count_receipts==0`、配额不变、reload 仍 declined；`decline.spec.ts` 验证 reload 后无「模拟执行成功」。 |
| (b) 配额仅记账一次 | ✅ 确认 | `record_receipt_once` 以 `command_id` 主键 `INSERT OR IGNORE`+`rowcount==1`+`succeeded`+`grams>0` 四重守卫；`command_id` 由 `uuid5(run,version)` 确定性派生。重放返回 409 且配额不变。 |
| (c) 无未鉴权业务访问 | ✅ 确认 | `state/events/runs/{id}/approval` 均依赖 `current_session`（缺失 401），两个业务写叠加 `require_csrf`（失败 403）；公开端点不含宠物/任务/秘密数据（`test_app` 验证配置不泄漏）；Cookie `HttpOnly`+`SameSite=Lax`，本地仅省 `Secure`；演示口令默认值明确标注为非秘密、真口令经 env 注入。 |
| (d) domain.schema.json 仍仅 6 输入模型 | ✅ 确认 | `$defs` 恰为 6 输入模型 + `RunState`；公开响应 DTO 仅出现在 openapi，未混入 domain schema；`--check` 实测字节一致，无漂移。 |
| (e) aws 绝不静默用本地替身 | ✅ 确认 | aws 缺任一环境变量即 `ValidationError`；aws 模式 `create_app` 抛 `NotImplementedError`；`build_analyzer` aws→`BedrockAgent`（`analyze_event` 抛错），仅 local→`LocalFakeAgent`；`aws_connected` 恒 `False`；替身全程带 `simulated/本地替身/local_fake` 标签。 |

## 非阻断 nit 与处理

1. **logout 未强制 CSRF，与模块自述口径不一致**（`api.py`）。风险极低（`SameSite=Lax` 已阻断跨站携带会话，伪造登出先 401）。
   - **处理（已修）**：保留 logout 为会话级、幂等——若强制 CSRF，则页面 reload 丢失内存令牌后用户将无法登出（前端 `onLogout` 亦会因 403 产生未处理拒绝）。据此**改写 `api.py` 文档串**使口径精确（业务写强制 CSRF，logout 会话级），并将前端 `logout()` 改为**尽力式**（无论服务端结果如何都清理本地状态）。未削弱任何安全检查。
2. **摄入热路径未接租约，理论上并发重复分析竞态**（`workflow.handle_event`）。Day-1 单主人、单进程串行，无影响；`claim_run` 租约已实现且被 `test_recovery` 覆盖，接入属 Day-2 异步 worker 范畴（STATUS 已声明“当前分析为同步”）。**处理：记录为 Day-2 待办**（接入 worker 时用 `claim_run` 串行化分析）。
3. **会话仅存进程内存**（`auth.py`）。已在 docstring 与 STATUS 注明为 Day-1 限制；单进程 e2e 不受影响。**处理：记录为 Day-3 持久化/多副本待办**。
4. **OpenAPI 未声明 401/403/404/409 错误响应**。FastAPI 常见做法，`test_contracts` 仅冻结路径集合，不构成漂移。**处理：Day-2 补 `responses` 完整性**。
5. **`readyz` 仍报 `scaffold_business_not_ready`（503）**。符合“冻结基线测试诚实更新而非削弱”（`test_app` 断言未改），保守报 degraded 不属过度声明。**处理：保持不动**（正常闭环 + 云端就绪后再上调语义）。

## 范围合规

改动严格落在 Day-1 计划范围内，未新增未授权产品功能；无秘密入库、无云资源创建、无费用、无远程推送。本地通过与云端未验证在 `STATUS.md` 分列，未以 SQLite PASS 或本地替身冒充云端完成。

---

> **二次检查后记（2026-09-24）**：在本次审查之后又做了一轮源码级复核，补强 2 条审批安全测试（BLOCKED 不可强批、DECLINED 不可重批为执行），后端测试由 69 增至 **71** 全绿；并修正 README/`.env.example` 陈旧描述。上文“69”为本审查当时的计数。
