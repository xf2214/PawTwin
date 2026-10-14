# 附加计划实施记录（2026-10-03）

权威需求：PawTwin_附加开发计划_2026-10-02.md。用户本轮明确要求完成开发，覆盖先前仅文档的限制。
基线：31da349；已有 STATUS/TASKBOARD 修改与两份未跟踪评审/路线文档保留。当前目录串行开发，不从 HEAD 另建遗漏工作内容的工作树，不提交或推送。

## 契约裁定

- Mochi ID 与旧六输入领域模型保持稳定，新增家庭业务独立 `/api/family` API，OpenAPI 自动生成。
- 本地账号使用带盐 scrypt，可信 user_id 注入；角色、家庭称呼、喂食授权独立。单进程会话恢复指页面刷新；服务重启需要重新登录。
- 一次一个当前家庭，成员关系每请求查库；退出/移除立即撤权。
- 新数据库 `<database_path>.family.db`，只读导入旧 Home 文档/照片；幂等迁移先在副本测试，旧数据库与设备额度保留；设备仍仅 demo-owner/Mochi 一份额度。
- Home 文档继续使用事务存储，不无益地改写全部关系表；账号/成员/邀请使用关系表，记录与统计带稳定归属、版本和源 ID。
- 成长数据程序计算；本地分身明确规则后端，App/Alexa 模拟入口共用上下文和受控提议。真实模型/AgentCore/Cognito 和云资料不可冒充已实现。

## 任务与验收

1. EXT-00/01/02：契约、账号/会话/家庭/邀请/权限；三账号、异家庭、撤权、CSRF、冒充、最后管理员、邀请有效期/幂等行为测试。
2. EXT-03：副本导入、共享作者、任务实例与领取/转交/编辑/取消、CAS/幂等；两连接并发、照片隔离、旧额度不复制。
3. EXT-04/05：称重/饮食/观察纠错删除，时区统计与持久化报告调度；kg/g、周边界、单测量、真实跨度、迟到重建、重启补跑。
4. EXT-06/08/09：五层上下文、确认记忆/失效/冲突、双入口对话/照护提议、参考知识与就诊摘要；隔离/注入/过期/删除与受控确认测试。
5. EXT-07：五入口 App，账号与家庭设置、照护、成长曲线/报告、助手与原像素小屋；390/1440 浏览器回归。
6. EXT-10/11/12：本地验收与独立审查、英文演示/试用材料；云验收、真实模型评估、实际家庭试用/视频拍摄/发布具名未执行。

## 预检共享接口

身份→Home：Session.user_id + owner_id=当前家庭；每请求成员校验。
Home→统计/上下文：事务文档 revision + 带 pet_id 的记录与源 ID；删除排除、修订重建。
身份→旧执行：只有种子家庭获宠物授权才可访问 Mochi 自动执行；不增加任何硬限额。
API→UI：新增 DTO 来源 Python；旧工作台与演示登录继续兼容。

## 进度

- 基线 verify.ps1：252 passed / 1 skipped / 21 deselected，ruff/契约/typecheck/build PASS。
- Task 1: complete_local — 独立账号/家庭/角色/邀请/撤权、可信作者，原设备六输入契约不变。
- Task 2: complete_local — SQLite backup 幂等导入、照片/失败回滚、旧新 Home 共用文档、两连接 CAS、任务实例与领取/转交/编辑/取消；原额度共享。
- Task 3: complete_local — 实测/单位/饮食语义/修订删除、观察日记管理、家庭时区统计/持久化报告/失败重试/补跑、回执投影；时区修改使旧窗口失效。
- Task 4: complete_local — 五层上下文、确认记忆/纠正/删除/过期/冲突、规则问答双入口与受控确认、来源元数据/缺项/就诊摘要；真实模型接入依赖 EXT-10。
- Task 5: complete_local — 五入口 App 与像素小屋、头像/邀请撤销/喂食授权、档案字段/归档恢复、曲线/报告、慢回复隔离；390/1440。
- Task 6: complete_local_part — 本地 QA 与一次独立审查、英文演示/空白试用模板；云接入、真实模型/家庭试用、视频/资格/发布/提交未完成。

最终 verify：284 passed / 1 skipped / 21 deselected，ruff/52 路径 OpenAPI/六设备输入/TS/build PASS；Playwright 全量 26 passed，8806 隔离端口，截图实际查看；uv lock --check PASS。
交付：未提交工作区，起点 31da349。没有新分支合并、推送、发布或云调用；不因 skill 的通用分支结束菜单而要求用户决定本任务不涉及的集成动作。全部实施与修复保留可审阅。用户原库未实际导入，行为在副本/临时库验收。

Final review: independent read-only extension_review（GPT-6-astra），一次审查。11 Important 修复；旧显示名入口 Minor 按账号身份误导影响升为 Important 后修复，无 deferred minors。修复和新增收尾项由实现者及自动化验证，没有独立复审。详见 reviews/EXT-local-review-2026-10-03.md。
Final: fixed 旧新资料分叉/删除失效/当地日边界/周期管理限制/失败报告重试/历史待办/提议重绑定/舍入除零/作者快照/新宠物选择/慢回复/旧身份入口；复现后修复，最终全量通过。另以 RED→GREEN 修复时区修改的重复 current 报告与档案缺项，补齐归档和问答，32 个新增后端测试。

## Final rulings（reviewer 未判定项）

Final: Ruling: 修复后回归与契约 — 实跑 284 后端/26 浏览器/全部静态与构建检查，作为本地证据 — cost if wrong: 未触发路径仍可能有缺陷。
Final: Ruling: 视口/键盘/网络/未保存表单/撤权/慢请求 — 390/1440 和语义控件/刷新/权限/慢切换已测；完整辅助技术、离线与未保存专项未验 — cost if wrong: 输入丢失或可访问性缺陷。
Final: Ruling: 两连接/多进程/真实崩溃 — 新增两连接/reopen，复用旧进程重启与审批回归；新家庭强杀/生产多副本未验 — cost if wrong: 恢复或并发异常。
Final: Ruling: 迁移失败/照片/额度 — 故障回滚/字节恢复/源库不变/额度共享已测；生产规模迁移未验 — cost if wrong: 数据关联或恢复问题。
Final: Ruling: 邀请/权限全部交错 — 过期/撤销/重复/移除/跨家/CSRF/作者/末管理员已测；不冒充完整安全审计 — cost if wrong: 越权或竞态。
Final: Ruling: DST/时区修改/长停机 — 窗口/重建/reopen/失败重试已测；大量补跑与中途强杀压力未验 — cost if wrong: 延迟或资源压力。
Final: Ruling: 恶意记录/冲突/今日/失效 — 本地反向测试通过；没有真实生成模型红队结果 — cost if wrong: 后续模型误引或注入。
Final: Ruling: 云/真实 Alexa/硬件/用户试用/材料 — 未接入或未执行具名保留，规则/模拟标签可见 — cost if wrong: 错误能力或参赛宣称。

最后启动顺序检查：test_report_worker_imports_original_before_advancing_seed_report_cursor RED→GREEN，先幂等导入再生成/推进报告，旧合成游标在新库事务中清除。最终 284 后端与 26 浏览器再次通过；预览已启动、healthz live 与 worker ok 实际读回。
