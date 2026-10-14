# PRODUCT-02：设备界面、差异化场景与多宠物展示

日期：2026-10-13。用户在 PRODUCT-01 基础上要求：提升平板和手机里的 App 界面；让三个案例更丰富且每个不同；加入更多宠物角色。

## 对应交付

| 用户要求 | 当前实现 |
| --- | --- |
| 高级的设备内界面 | 平板改为完整照护仪表盘，含侧栏、宠物切换信息、小屋、任务状态和来源入口；手机改为 Luna 日记、照护事项、图标底栏和独立硬件细节。统一字级、线性图标、留白与柔和底色。 |
| 三个案例有不同结构 | 家庭交接使用 Miso 接力泳道与回写票据；成长回顾使用 Luna 双日记插画、记录时间线与报告页；偏好接续使用 Coco 问答气泡、草稿/主人确认卡与待确认计划。每个案例的三步都会改变内容。 |
| 更多宠物 | 新增独立轮廓的 Mochi 橘猫、Miso 柯基、Luna 奶牛猫、Coco 卷毛犬。宠物展示区支持键盘切换，并同步设备与功能示意；手机和三案例使用不同角色。 |

采用既有 SVG/像素系统扩展，房间继续俯视，宠物保持正常正面或侧面。四角色的耳朵、体型、毛纹、尾巴与口鼻不同，既有来源材料和应用界面未被覆盖。

新增 `PetPortrait.tsx`、`ProductDevices.tsx`、`CasePreview.tsx` 及独立样式，集成到 `Showcase.tsx`。未新增依赖，未修改真实业务应用、后端、契约、权限或数据库。

## 验证与审查

- `npm run build`：TypeScript 与最终生产构建通过。
- `playwright test e2e/showcase.spec.ts e2e/product-page.spec.ts e2e/product-visuals.spec.ts e2e/shell.spec.ts`：最终 20 passed，0 retries，30.2s。
- 新浏览器验收覆盖四种宠物在设备和所有功能预览中同步、三案例九个步骤、320/390/1440 三种宽度、键盘、暂停和动态减少动画。
- 公开展示、角色切换与案例操作的 `/api/*` 请求为 0，无 pageerror；无水平溢出。
- `uv run --frozen pytest`：425 passed，1 skipped，21 deselected，47.85s。
- Ruff：All checks passed；生成契约：Contracts are current；本轮源文件无尾随空白。
- 独立只读源码及截图审查已完成，检查范围内无待解决问题。

命名跳过仍为项目已有 `test_kill_a_running_server_mid_analysis_then_relaunch`，原因是单运行器上的实际杀进程/重启容易产生端口与启动波动，另有子进程和逻辑恢复测试覆盖。21 个真实 Bedrock/AgentCore/DynamoDB 测试按默认标记排除，本轮没有真实云验证。

截图复核发现窄屏手机因绝对定位未参与舞台高度而遮挡首屏。已改为同一网格轨道叠放，手机参与高度计算；新增边界框断言保证其顶边不越过文案底边。320/390 新截图和独立复核确认问题关闭。

## 当前截图

- [平板与手机](product-visuals-2026-10-13/devices-hero-1440.png)
- [320 首屏](product-visuals-2026-10-13/devices-hero-320.png) / [390 首屏](product-visuals-2026-10-13/devices-hero-390.png)
- [四宠物展示](product-visuals-2026-10-13/pet-gallery-1440.png)
- [家庭交接](product-visuals-2026-10-13/case-handoff-1440.png)
- [成长记录册](product-visuals-2026-10-13/case-growth-1440.png)
- [偏好对话](product-visuals-2026-10-13/case-preferences-1440.png)
- [完整桌面页](product-visuals-2026-10-13/product-desktop-full.png) / [完整手机页](product-visuals-2026-10-13/product-mobile-full.png)

共 17 张截图，涵盖三个案例和宠物展示在全部宽度下的画面；SHA256 清单见同目录 `screenshots.json`。查看了设备桌面/320首屏、宠物桌面/320画面和三案例的桌面/320关键内容。案例区域截图临时隐藏固定导航、跳转链接与动画按钮，以避免滚动截图叠层；实际页面仍显示它们。所有截图禁用动画取得稳定最终帧。

## 范围与运行

延续完整 dirty 工作区，基线 HEAD `31da3490c424f925db5c02214d7d3a945add8fcd`。修改前副本在仓库外 `C:\Users\11831\AppData\Local\Temp\pawtwin-product-visuals-20261013`。无提交、推送、部署或比赛提交；未修改原有数据库或原始图片。

预览继续使用现有 `http://127.0.0.1:8807/#product` 服务，HTTP 200。浏览器回归使用独立 8813 端口与内存数据库，服务器随测试结束退出。

设备和角色均为虚构产品示意，三个案例不创建任务，不填入虚构体重/年龄/健康数值；实际照护需人完成和确认。原有本地身份、规则回答、Alexa 网页模拟和概念/模拟硬件边界继续明确。
