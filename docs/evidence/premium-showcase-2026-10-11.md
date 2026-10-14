# UI-02 产品官网视觉升级验收

日期：2026-10-11。任务：优化展示页面、增加高级感、形成类似 Apple 产品官网的体验。

- Owner：Codex 协调者串行实施；premium_review 独立只读复核。
- 起点/分支：31da349 / chore/bootstrap。交付为当前工作区，未提交、推送或发布；保留所有既有未提交家庭扩展与云适配。
- 代码范围：frontend/src/Showcase.tsx、showcase.css；测试 frontend/e2e/showcase.spec.ts；README/STATUS/TASKBOARD 和本证据。
- API、后端、路由、应用逻辑、契约、依赖锁及原用户数据库未修改。当前预览为独立 data/showcase-preview.db。

## 成果与要求核对

| 要求 | 当前实现 | 实证 |
|---|---|---|
| 精致产品官网，而非业务工作台 | 居中大标题、白色留白、半透明吸顶导航、暖色文字与蓝色行动入口 | [桌面全页](premium-showcase-2026-10-11/product-1440.png) |
| 大幅产品画面 | 悬浮平板与手机 UI 示意、俯视房间和正面像素橘猫，沿用 PawTwin 自有视觉 | [首屏](premium-showcase-2026-10-11/hero-1440.png) |
| 完整介绍路径 | 首屏 → 深色宠物章节 → 四项可切换体验 → 记录来源 → 家庭流程 → 应用入口 | 桌面/手机全页及四项预览 |
| 介绍与应用分离 | / 与 /#product 为宣传；/#app 家庭应用；/#workbench 原工作台；/#home 原小屋 | 31 项浏览器全量，包括应用会话往返、刷新和工作台入口 |
| 手机适配 | 320/390/1440 实测 document.scrollWidth 等于 viewport；四项预览均能操作 | [手机全页](premium-showcase-2026-10-11/product-390.png)、[320 首屏](premium-showcase-2026-10-11/hero-320.png)、[运行结果](premium-showcase-2026-10-11/visual-check.json) |
| 键盘与减少动画 | 跳转内容、原生按钮及明显 focus；减少动画时 animation=none；功能说明 aria-live | showcase.spec.ts 第四项与独立 live 检查 |
| 公开页不读取私人业务 | 公开页及全部预览请求 /api 数量 0，无 pageerror | visual-check.json、原宣传页回归、独立 live 检查 |
| 真实能力边界 | 示例不含真实测量；本地规则、Alexa 网页模拟、概念项圈、模拟设备和云未验证说明保留 | 全页页脚、宠物分身预览及独立审查 |

## 本轮实际验证

1. scripts/verify.ps1：退出 0，pytest **333 passed / 1 skipped / 21 deselected**，24.46 秒；ruff、生成契约、TS 类型与生产构建 PASS。
2. 最终样式对比度修正后 npm run build：退出 0；31 项全量 npm run test:e2e **31 passed，31.4 秒，0 retries**。端口 8810、临时内存库、现有 Chromium；无 AWS 调用。
3. 独立本地预览 8807：/healthz 与 / 均 HTTP 200。1440/390/320 全页、首屏及各宽度四组功能预览均已生成；已查看桌面全页、手机全页和 320 首屏/分身面板。
4. git diff --check：退出 0。仅既有文件的 CRLF 提示，无差异空白错误。
5. 真实 AWS 检查 21 项仍排除；后台强杀尽力测试 1 项仍 skip。本轮是展示改版，没有云、设备、真人试用或模型质量验收宣称。

验证日志：[基线输出](premium-showcase-2026-10-11/verify.log)。运行截图的短暂首屏动画已以 animations:disabled 截取稳定最终帧，正常运行仍有轻量淡入，减少动画模式禁用。

## 独立复核

premium_review 独立只读复核完成，检查范围内无待解决发现。已发现并修复：步骤序号对比度、主标题渐变中段对比度、过早截图导致首屏淡入未完成。步骤序号 4.136:1，渐变中段 3.388:1，来源章节灰色大标题 4.644:1。独立 live 复测确认三种宽度/全部预览均无溢出，公开页零业务请求，跳转内容与键盘焦点有效，减少动画内容完整可见；已查看稳定桌面/手机/窄屏截图。

## 预览与边界

本地预览：http://127.0.0.1:8807/ 。已请求 Codex 浏览器打开，工具返回 queued；成功 HTTP 和实际浏览器截图可核验。
实际应用：http://127.0.0.1:8807/#app 。原工作台：http://127.0.0.1:8807/#workbench 。
云资源创建/模型调用/新增费用为 0。网页仅本机可用，宣传改版不改变当前服务接入状态。
