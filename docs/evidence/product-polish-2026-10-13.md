# PRODUCT-03：标题显示、手机比例与可爱像素宠物

日期：2026-10-13。用户要求修整网页标题和显示效果、缩短手机、让像素宠物更可爱协调。

## 交付

- 标题统一字距、字重、行高和字号，收敛首屏与章节的视觉层级。功能和案例标题按完整分句断行，保留完整的可访问名称；768px 的故事右栏减少留白，避免短语侵入边距。浏览器标题缩短为 `PawTwin · 家庭宠物照护`。
- 手机整机使用 `aspect-ratio: 1 / 2.18`，保留正常的高度参与网格布局。内容缩为品牌、Luna 日常、小幅日记、一个照护摘要、底栏与示意标签，不通过隐藏重要内容裁切来缩短。
- 四只角色统一大头短身、短爪、明亮眼睛、小鼻口和轻腮红，减少孤立细碎像素和粗硬边缘。保留橘猫条纹与弯尾、柯基立耳白胸、奶牛猫不对称花脸长尾、卷毛犬垂耳与卷毛；正常正面造型及原有 API 保留。
- 新 `visual-polish.css` 只针对产品展示区域；平板展示角度与阴影也有所收敛。真实家庭应用、工作台、后端、权限和数据未修改。

## 本轮验证

1. `npm run build`：TypeScript 与最终生产构建通过。
2. `playwright test e2e/showcase.spec.ts e2e/product-page.spec.ts e2e/product-visuals.spec.ts e2e/shell.spec.ts`：20 passed，0 retries，38.5s。
3. 320 / 390 / 768 / 1024 / 1440 五种宽度均验证手机布局高度/宽度介于 2 与 2.4，内部 scrollHeight 没有超出 clientHeight，设备不遮挡窄屏首屏文案。
4. 每个功能与案例标题的分句实际边界都在标题内容框内；角色切换、三个案例九步、键盘、暂停与动态减少动画通过。
5. 展示页和示例操作 `/api/*` 请求为 0，无 pageerror、无水平溢出。
6. 独立只读代码及截图复核：320/768 首屏、1440 宠物画廊与关键案例内容完整，未发现待修复的 P1/P2 问题。

本轮只修改展示层，不重跑未受影响的后端。上一轮 PRODUCT-02 的 425 passed / 1 skipped / 21 live-AWS deselected、Ruff 和契约新鲜度证据仍见其独立记录，未混作本轮测试结果。

## 截图

- [桌面首屏与正常比例手机](product-polish-2026-10-13/devices-hero-1440.png)
- [320 手机宽度](product-polish-2026-10-13/devices-hero-320.png) / [390](product-polish-2026-10-13/devices-hero-390.png)
- [768 平板宽度](product-polish-2026-10-13/devices-hero-768.png) / [1024](product-polish-2026-10-13/devices-hero-1024.png)
- [四只新版宠物](product-polish-2026-10-13/pet-gallery-1440.png)
- [案例标题与成长记录册](product-polish-2026-10-13/case-growth-768.png)
- [完整桌面页](product-polish-2026-10-13/product-desktop-full.png) / [完整手机页](product-polish-2026-10-13/product-mobile-full.png)

共 27 张当前构建截图，覆盖五尺寸设备和宠物、五尺寸三案例与完整页面；校验清单见同目录 `screenshots.json`。所有截图禁用动画取得最终帧，案例截图临时隐藏固定导航以避免滚动截图叠层，实际导航正常保留。

## 文件与范围

修改 `Showcase.tsx`、`ProductDevices.tsx`、`device-preview.css`、`PetPortrait.tsx`、`index.html`、`main.tsx` 的产品标题及 `product-visuals.spec.ts`；新增 `visual-polish.css`。沿用完整 dirty 工作区，HEAD 基线 `31da3490c424f925db5c02214d7d3a945add8fcd`，修改前副本保存在仓库外 `C:\Users\11831\AppData\Local\Temp\pawtwin-product-polish-20261013`。

预览为现有 `http://127.0.0.1:8807/#product`，HTTP 200。测试使用独立 8813 端口和内存数据库。未改原始数据库、照片、依赖或锁文件，未提交、推送、部署或调用云资源。

所有角色与设备内容继续标为虚构产品示意，案例不创建照护事项或补齐健康数据，本地/规则/Alexa 网页模拟/概念硬件边界继续保留。
