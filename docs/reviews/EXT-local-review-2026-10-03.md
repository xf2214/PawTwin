# EXT 本地开发独立复核与裁定

2026-10-03，`31da349` 基线上未提交工作区。按照 executing-plans / requesting-code-review，请独立只读 reviewer 审查身份、共享、统计、记忆与 UI；没有让 reviewer 修改源码。
reviewer 发现 11 项 Important、1 项 Minor，没有 Critical。按使用影响，旧家庭显示名入口会使独立账号误认共享身份，因此该 Minor 重新评为 Important 后修复，没有剩余延期 Minor。
只进行一次独立审查；修复由实现者用行为复现和测试验证，没有第二轮独立复审。之后补齐的头像/邀请界面、记录管理、档案字段/归档、时区修改及回执投影由实现者和自动化验证，独立审查覆盖强度不夸大。

## 发现与处理

| 发现 | 修复与复现测试 |
|---|---|
| 旧 Home 与新家庭写入分叉 | LegacyHomeView 共用新家庭文档；`test_legacy_and_new_home_entrypoints_share_writes_after_migration` |
| 删除偏好仍进入 Home insights | state/insights 排除软删除；`test_expired_memory_today_observation_and_deleted_preferences_are_excluded` |
| 日记 UTC 与家庭当地日混用 | 当地日期边界；`test_daily_diary_uses_household_date_and_report_retry_is_idempotent` |
| 下一周期未到期时也不能取消/编辑 | due guard 仅限制 complete；`test_next_recurring_occurrence_can_be_cancelled_before_due` |
| 已推进调度游标后的失败报告不重试 | 先重试 failed，再补跑；`test_failed_report_rebuild_retries_even_after_cursor_advanced` |
| 历史报告按今天任务状态计待办 | 时间截点和任务版本历史；`test_historical_report_excludes_tasks_created_later` |
| 客户端可重绑定旧提议到新上下文 | 请求、保存、当前版本三者相等；`test_client_cannot_rebind_old_proposal_to_new_context_and_tiny_weight_rejected` |
| 极小体重舍入为零/除零 | 正常化后必须为正，计算比较值守卫；同上 |
| 名字修改改写历史作者/部分写入无作者 | ID 与当时名字快照，迁移保留来源；`test_author_display_name_is_snapshot_and_actor_is_present_for_all_home_writes` |
| 新宠物父组件选择延迟 | Home 变更等待父 refresh；浏览器 immediate assertion |
| 慢回复显示到另一只宠物 | household/pet generation 过滤；浏览器 delayed reply |
| 独立账号仍看到旧家庭显示名入口 | 在账号模式隐藏，真实成员由 invitation 管理；浏览器回归 |

另由实现者验出家庭时区修改造成两个 current 报告、档案缺少成长参考字段，均有 RED→GREEN；补齐可逆归档与参考问答缺项判定，见 `test_family_completeness.py`。
设备回执以只读投影进入报告，原额度仓储不复制；成功出粮单列模拟值，不当成摄入，见 `test_family_receipts.py`。
启动前导入顺序另有 RED→GREEN 测试，后台不会先生成空种子报告后推进进度。重启补跑测试装配原设备 source 与 create_app 一致，恢复原依赖后不重复创建报告。

## reviewer 未判定项的裁定

1. 修复后完整回归与契约：已实际运行 284 后端、26 浏览器、ruff/契约/TS/build；覆盖本地行为。若覆盖不足，仍可能存在未触发路径的问题。
2. 实际视口/键盘/网络/未保存表单/撤权/慢请求：390/1440 图像已查看，role/label/导航/刷新/错误与慢切换有测试；完整屏幕阅读器、离线和未保存表单专项未做。若遗漏，可能损失输入或出现可访问性缺陷。
3. 两连接/多进程/真实崩溃：新增两连接竞争与 reopen，旧套件真实进程重启/审批保留；新增家庭进程强杀与生产多副本未测。若遗漏，可能有恢复或并发异常。
4. 迁移失败、照片、额度：SQLite trigger 故障回滚、恢复后照片字节、原库不变、Mochi 共用额度均已测试；生产数据大规模迁移未测。若遗漏，会影响数据关联和恢复。
5. 邀请与权限所有交错：覆盖过期、撤销、重复、移除后旧邀请、跨家庭、CSRF、伪造作者与最后管理员；未宣称完整安全审计。若遗漏，会造成越权或邀请竞态。
6. DST/时区修改/长期停机：DST 窗口、家庭换时区重建、reopen 补跑、失败重试已测；长时间停机的大量报告和停机中途强杀未做压力验收。若遗漏，会出现延迟或资源压力。
7. 恶意记录、冲突、今日/删除/过期：均有反向行为测试；规则后端把记录当数据，没有实际生成模型红队结果。若升级模型未保留边界，可能误引失效内容或遭注入。
8. AWS/Cognito/AgentCore/Alexa/硬件/试用/材料真实性：全具名未接通或未执行，保持模拟/规则标签，准备材料不声称反馈/视频已完成。若忽略这些门，会形成错误的云能力或参赛宣称。

完整检查与命令见 [验收交接](../evidence/extension-local-2026-10-03.md)。
