# 宣传页成长记录模拟数据验收

日期：2026-10-13。任务：PRODUCT-04。用户要求“宣传页面成长记录里面放上模拟的数据，不要空着”。本次明确授权仅在宣传页面加入虚构样本。

## 本次结果

成长记录展示四次体重、日期、来源、最新体重、阶段变化、曲线与日常手记。切换示例宠物后，数字和曲线同步变化。成长回顾案例从 Luna 第一条测量到最新测量，再到阶段回顾，使用同一组样本。

| 虚构宠物 | 09/22 | 09/29 | 10/06 | 10/13 | 阶段变化 |
| --- | --- | --- | --- | --- | --- |
| Mochi | 4.10 kg | 4.16 kg | 4.14 kg | 4.22 kg | +0.12 kg |
| Miso | 9.20 kg | 9.32 kg | 9.28 kg | 9.40 kg | +0.20 kg |
| Luna | 3.60 kg | 3.64 kg | 3.62 kg | 3.68 kg | +0.08 kg |
| Coco | 5.20 kg | 5.26 kg | 5.24 kg | 5.30 kg | +0.10 kg |

日期均为 2026 年，来源显示“电子秤 · 主人录入（模拟）”。各数值区域标注模拟，界面不表示真实健康判断。数据只在 `ProductGrowth.tsx` 静态定义，摘要由样本计算，展示组件没有业务 API 或持久化调用。

## 范围与保留

沿用 `chore/bootstrap` 完整 dirty 工作区，基线 HEAD 为 `31da3490c424f925db5c02214d7d3a945add8fcd`，未提交。修改前相关文件复制至仓库外 `C:/Users/11831/AppData/Local/Temp/pawtwin-growth-demo-20261013`。保留 UI-05、实际应用、数据库和其它既有修改。

修改 `Showcase.tsx`、`CasePreview.tsx`，新增 `ProductGrowth.tsx`、`product-growth.css`。growth_tests 只写新测试 `frontend/e2e/product-growth.spec.ts`；growth_review 只读审查代码和最终截图。

## 验证

使用 `scripts/node-runtime.ps1` 的 Codex Node runtime，不修改系统 Node。测试服务独占 `8813`、内存数据库、本地规则和模拟设备，浏览器为现有 Chromium。

```powershell
. ./scripts/node-runtime.ps1
$runtime = Get-PawTwinNodeRuntime
$env:PAWTWIN_E2E_PORT = '8813'
$env:PAWTWIN_BROWSER_EXECUTABLE = Join-Path $env:LOCALAPPDATA 'ms-playwright\chromium-1194\chrome-win\chrome.exe'
Push-Location frontend
try {
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','build')
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','test:e2e','--','e2e/product-growth.spec.ts','e2e/showcase.spec.ts','e2e/product-page.spec.ts','e2e/product-visuals.spec.ts','e2e/shell.spec.ts')
} finally { Pop-Location }
```

最终 **23 passed（41.9 秒，0 retries）**；TypeScript/生产构建 PASS；`git diff --check` PASS。新测试覆盖四宠样本/差值/曲线方向、刷新后的选择重置、案例三步数据一致、320/390/768/1440 适配及零业务请求/页面错误。已有视觉回归继续覆盖 320/390/768/1024/1440。后端代码未变，本次未重新运行后端套件。

独立审查发现的刻度小数精度与旧占位颜色覆盖问题均修正；首尾点标签错开坐标轴，窄屏字体放大，案例 SVG 明确使用自动高度。六张最终截图独立复核无待修复 P1/P2。

内置浏览器现有 `http://127.0.0.1:8807/#features` 已刷新、选中成长记录并显示新曲线。未部署、发布、推送或创建真实成长数据。

## 最终画面

[桌面成长记录](product-growth-2026-10-13/growth-records-1440.png) · [390 宽成长记录](product-growth-2026-10-13/growth-records-390.png) · [320 宽成长记录](product-growth-2026-10-13/growth-records-320.png)

[桌面成长案例](product-growth-2026-10-13/growth-case-1440.png) · [390 宽成长案例](product-growth-2026-10-13/growth-case-390.png) · [320 宽成长案例](product-growth-2026-10-13/growth-case-320.png)
