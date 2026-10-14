# UI-03 动画与情景案例验收

2026-10-11；Codex 协调者串行实现，premium_review 独立只读审查。
起点 31da349 / chore/bootstrap，加既有 UI-02 与家庭扩展未提交工作区；交付仍在工作区，未提交、推送或发布。

改动：frontend/src/Showcase.tsx、showcase.css、frontend/e2e/showcase.spec.ts，以及 README/STATUS/TASKBOARD/本证据。无 API、后端、依赖、契约或原数据库变更。

## 已实现体验

- 装饰画面轻微浮动、呼吸光晕；章节首次进入视口渐显上移；四项功能切换及案例步骤更新有短入场反馈。
- 持续可见的全局暂停按钮；系统减少动画优先，并动态响应偏好变化。暂停/减少动画后没有运行中的后代动画。
- IntersectionObserver 只触发一次、卸载时 disconnect；媒体偏好监听卸载时清理。内容默认可见，未依赖观察器隐藏。
- 三组案例：家庭交接、成长回顾、偏好接续。每组三步骤，切换场景重置第一步，键盘 Enter/Space 可操作。
- 情景与任务状态明确示意；不创建真实任务、调用业务 API 或编造体重；本地规则助手提议保留主人确认。
- 全局暂停不影响案例手动查看；footer 预留底部空间避免控制按钮覆盖链接。
- 稳定的 aria-live 说明区域；只重建动画中的画面/标题，不重建读屏提示容器。

## 当前验证

- 新增两项交互测试先因缺少案例/暂停按钮失败，实现后专项 6 passed（7.5 秒）。
- independent reviewer 发现 feature panel key 重建 live region；新增持久容器连接性断言复现 false 后修复。最终完整结果见 e2e-final.log。
- scripts/verify.ps1 退出 0：333 passed / 1 skipped / 21 deselected（24.69 秒）；ruff、契约、类型和生产构建 PASS。
- 最终无障碍修正后类型/生产构建退出 0。
- 最终完整浏览器 **33 passed（34.3 秒，0 retries）**；[完整输出](motion-cases-2026-10-11/e2e-final.log)。独立 live 复测四次功能选择均 isConnected=true、sameRegion=true、aria-live=polite，无待解决发现。
- [实测结果](motion-cases-2026-10-11/runtime.json)：320/390/1440 scrollWidth 等于 viewport；正常 pt-float、进入视口 pt-revealed；暂停 runningAnimations=0；动态减少动画 disabled=true；pageerror=0、公开业务请求=0。
- 独立全部 27 案例组合（3 宽度 × 3 案例 × 3 步骤）键盘检查通过，无文本/按钮越界。
- [全页手机](motion-cases-2026-10-11/full-390.png)、[家庭交接桌面](motion-cases-2026-10-11/case-1440-0-2.png)、[窄屏偏好接续](motion-cases-2026-10-11/case-320-2-2.png)已查看。案例单独截图临时隐藏视口固定导航/暂停控件，避免长元素截图叠加；全页图保留实际页面控件。独立确认跳转内容链接在真实未聚焦视口保持屏外，截图叠加不是产品问题。

真实 AWS 检查仍 21 deselected；1 项后台强杀尽力测试 skip；没有模型、真人试用、真实硬件或云验收宣称。云调用/资源/新增费用为 0。

## 预览

http://127.0.0.1:8807/#cases 。既有预览服务复用、独立 showcase-preview.db；/ 与 /healthz HTTP 200。
产品入口、家庭应用、原工作台和小屋路由沿用；旧网页需刷新以加载新构建。
