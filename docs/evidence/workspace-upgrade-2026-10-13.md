# UI-05 家庭应用与照护工作台升级

2026-10-13。本轮依据当前宣传页的视觉与功能叙事升级两个实际入口。用户选择两个入口一起调整、完善现有能力、统一设计并保留独立业务流程。

## 完成范围

共用暖白背景、灰绿导航、蓝色主操作、线条图标、卡片和标题层级。家庭主导航为今日、照护、成长、分身、家庭；工作台为请求与审批、运行记录、演示设置。原家庭账号与演示口令、数据及操作权限分别保留。

- 今日概览采用已存储的人工完成事实，体重保留来源与时间；小屋去掉重复导航和选择器，保留档案、物品、建宠与对应照护跳转。
- 猫/狗像素形象由已保存的毛色、花纹和大小驱动，房间保持 2D 俯视，宠物保持正常正面造型。
- 照护默认待办，“我负责”包含指派和领取；卡片显示领取人，重复计划保留最近完成及下一次时间。
- 成长拆为概览、实测与饮食、日记与观察、报告；快捷录入直接切到相应表单，保留纠正、删除、独立重试、报告和就诊卡。
- 分身将提问、人工方案与待确认记忆整理为不同区域；家庭 guest 查看资料，不显示后端禁止的写入控件。Alexa 网页模拟使用真实独立入口。
- 工作台事实和硬限制始终可见，历史可按状态筛选和时间排序；详细证据按需展开，事实/回执注入/原文反馈/新会话集中于演示设置。
- 旧宠物回执不会关闭新宠物草稿或解除新保存锁；新宠创建后切页仍可选中新宠。已接收请求保留编号，首次状态返回前临时锁历史选择，持续分析/执行时阻止重复请求。75 秒读取到期会中止卡住的 GET 并允许重查，不推断后台失败；401 失效后旧响应不能恢复工作台。

没有新增预约、订单、市场或支付流程。本轮前端增量修改不改变后端接口、权限、数据库结构或云配置。

## 验证

修改前 `scripts/verify.ps1` 的 425 passed / 1 skipped / 21 live-AWS deselected、Ruff、契约、类型与构建作为基线。各实现包先写有实际行为断言的回归，在旧实现上确认 RED，随后集成 GREEN；额外的迟到保存、首读占用、卡住 GET 和 401 回归同样先复现失败。

最终浏览器覆盖 **100 个不同测试、19 个文件，0 retries**。使用既有 Chrome 与 bundled Node，独立服务 `:8833`、内存数据库、本地规则/替身；分组不改变注册限流与服务权限。

| 测试范围 | 最终通过 |
| --- | ---: |
| application-upgrade、workbench-upgrade、pet-visual-upgrade、workspace-shell、family | 25 |
| acceptance、approve、decline、feedback、shell、showcase、product-page、product-visuals、zz-unknown | 34 |
| pet-home、platform | 14 |
| alexa | 9 |
| usability | 17 |
| demo-rehearsal 双账号共享记忆→方案确认→人工完成→报告→删除记忆 | 1 |

旧测试相应切换至新导航、成长分区及待办/已完成筛选，保留实际 API、来源、权限、报告计算与回执断言。此前原小屋链接与排练的产品导航定位失败已按当前界面适配并复验。最终 `scripts/verify.ps1`：**425 passed / 1 skipped / 21 live-AWS deselected（51.31 秒）**，Ruff、生成契约、TypeScript、生产构建通过，输出保存在 [verify.txt](workspace-upgrade-2026-10-13/verify.txt)。既有 Starlette/AnyIO 弃用提示保留；真实云测试未执行。全工作区 diff 检查及六份入口文档的本地链接通过。

独立只读审查复核代码、回归设计及实际截图，确认上述竞态修复后无待解决 P1/P2。320/390/768/1440 的 **38 张截图**、尺寸/无水平溢出检查与采集脚本见 [visual-checks.json](workspace-upgrade-2026-10-13/visual-checks.json)、[capture.cjs](workspace-upgrade-2026-10-13/capture.cjs)，41 个产物的 SHA256 见 [manifest.json](workspace-upgrade-2026-10-13/manifest.json)。移动长图中固定底部导航显示在初始视口底部，另存滚动后的视口图以验证实际任务操作和房间可见。

| 页面 | 桌面 | 手机 |
| --- | --- | --- |
| 今日与小屋 | [1440](workspace-upgrade-2026-10-13/today-1440.png) | [390](workspace-upgrade-2026-10-13/today-390.png)、[滚动视口](workspace-upgrade-2026-10-13/room-scrolled-viewport-390.png) |
| 照护 | [1440](workspace-upgrade-2026-10-13/care-1440.png) | [320](workspace-upgrade-2026-10-13/care-320.png)、[实际操作视口](workspace-upgrade-2026-10-13/care-scrolled-viewport-390.png) |
| 成长 | [1440](workspace-upgrade-2026-10-13/growth-1440.png) | [390](workspace-upgrade-2026-10-13/growth-390.png) |
| 分身 | [1440](workspace-upgrade-2026-10-13/twin-1440.png) | [390](workspace-upgrade-2026-10-13/twin-390.png) |
| 请求与审批 | [1440](workspace-upgrade-2026-10-13/workbench-requests-1440.png) | [320](workspace-upgrade-2026-10-13/workbench-requests-320.png) |
| 历史/设置 | [历史](workspace-upgrade-2026-10-13/workbench-history-1440.png)、[设置](workspace-upgrade-2026-10-13/workbench-settings-1440.png) | [历史](workspace-upgrade-2026-10-13/workbench-history-390.png)、[设置](workspace-upgrade-2026-10-13/workbench-settings-390.png) |

## 本机预览与数据

[家庭应用](http://127.0.0.1:8834/#app/home)、[成长](http://127.0.0.1:8834/#app/growth)、[照护工作台](http://127.0.0.1:8834/#workbench)、[产品介绍](http://127.0.0.1:8834/)。家庭演示账号 `workspace-preview-20261013`，非秘密的本地演示密码 `local-preview-password`；原工作台使用独立演示口令 `local-demo-passphrase`。

服务使用新建 `data/workspace-preview-2026-10-13.db`。家庭名称及手工示例文字明确为虚构，体重来源为 `demo_sample`，不代表真实宠物资料；就诊卡默认排除演示测量。默认家庭后端 `local_rules`，工作台 `local_fake`，设备回执为模拟，未启用照片识别。没有真实 AWS、Alexa、AgentCore 或硬件验证。

完整 dirty 工作区继续增量维护，未从 HEAD 恢复文件；修改前 55 个前端/测试/入口文档文件保存在仓库外 `outputs/PawTwin-before-workspace-2026-10-13`，最终逐项 SHA256 复核 **55/55 一致**。旧代码、原数据库和媒体保留。未提交、推送、发布、部署或创建云资源。
