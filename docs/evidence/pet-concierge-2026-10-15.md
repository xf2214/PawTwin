# 宠物管家宣传场景验收

日期：2026-10-15。任务：PRODUCT-05。用户要求新增宠物管家场景，演示主人直接提问、Alexa 带上已有宠物上下文回答；所有 xxx 必须替换为具体内容。

## 交付内容

现有三场景保留，新增第四项“宠物管家”，包括三个可键盘切换的画面：

1. 小狗饮食：Miso，彭布罗克威尔士柯基犬，雄性、2 岁、9.40 kg，主人确认喜欢鸡肉。主人直接问能否吃巧克力；预设回复说明风险，并按确认偏好推荐少量原味全熟去骨鸡肉、先确认不过敏；已误食时及时联系兽医。
2. 猫咪状态：Luna，短毛黑白双色家猫，雌性、3 岁、3.68 kg。展示 07:40 窗边、12:20 客厅、18:10 饮水区的虚构轨迹。回答说明活动接近平日仍不能排除生病，并列出进食、饮水、排尿、呼吸、呕吐/腹泻观察项与就诊提醒。到过饮水区不等于已饮水。
3. 上下文随行：将“没有宠物资料的新会话”的完整背景问句与直接提问对照，显示自动带入的具体档案和确认偏好。比较限定是否提供上下文，不声称所有其他 AI 产品均无记忆能力。

所有示例为宣传组件中的静态预设对话，不发送业务/模型请求，不写入真实家庭记录。Alexa 为网页模拟，活动为虚构示意，不代表实际追踪或临床诊断。CTA 进入现有 Alexa 网页模拟器；当前业务助手仍按既有后端能力工作。

## 健康文案依据

2026-10-15 实际读取以下页面，改写为短小提示，没有复制长段落。界面提供同样的直接来源链接：

- [Merck Veterinary Manual：Chocolate toxicosis](https://www.merckvetmanual.com/toxicology/food-hazards/chocolate-toxicosis-in-animals)：巧克力风险来自其中的甲基黄嘌呤类成分，不能用犬种判断可以喂食。
- [PDSA：Your dog's diet](https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet)：少量熟瘦肉可作为偶尔的零食。
- [VCA：Recognizing signs of illness in cats](https://vcahospitals.com/know-your-pet/recognizing-signs-of-illness-in-cats)：关注精神、进食饮水、排泄和呼吸变化；出现不对劲的状态应联系兽医。

## 范围与保留

基线为 `chore/bootstrap` / `6342b96a874daa595b2150080ab64adad70b3d7b`。保留原有视频资料和提交文档改动。修改前文件在仓库外 `C:/Users/11831/AppData/Local/Temp/pawtwin-concierge-20261015`。本次未提交或推送。

Coordinator 改 `Showcase.tsx`、`CasePreview.tsx`、`showcase.css`、`showcase-messages.ts` 与文档；concierge_visual 新增 `PetConciergePreview.tsx`、`pet-concierge.css`；concierge_tests 只新增 `pet-concierge.spec.ts`；concierge_review 只读审查。交接后由 Coordinator 修正重复容器、次要文本对比度与对比说明，再统一构建验证。无依赖、锁文件、接口、数据库或后端修改。

## 验证命令与结果

通过 `scripts/node-runtime.ps1` 的 Codex Node runtime 运行：

```powershell
. ./scripts/node-runtime.ps1
$runtime = Get-PawTwinNodeRuntime
$env:PAWTWIN_E2E_PORT = '8813'
$env:PAWTWIN_BROWSER_EXECUTABLE = Join-Path $env:LOCALAPPDATA 'ms-playwright\chromium-1194\chrome-win\chrome.exe'
Push-Location frontend
try {
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','build')
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','test:e2e','--','e2e/pet-concierge.spec.ts','e2e/product-growth.spec.ts','e2e/showcase.spec.ts','e2e/product-page.spec.ts','e2e/product-visuals.spec.ts','e2e/shell.spec.ts','--output=test-results/concierge-20261015')
  $env:PAWTWIN_E2E_PORT = '8814'
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','test:e2e','--','e2e/i18n.spec.ts','--output=test-results/concierge-i18n-20261015')
} finally { Pop-Location }
```

结果：**26 passed（55.9 秒）+ 4 passed（7.1 秒），0 retries**。独立本地测试服务使用内存库，没有读取演示数据库。类型和生产构建 PASS；保留既有超过 500 kB 的分块警告（主 JS 600.62 kB / gzip 187.80 kB）。`git diff --check` PASS。后端全套不在本次验证范围。

新测试覆盖四个场景入口、三步键盘操作/回到首步、具体档案/个性化依据/安全提示/来源 href、模拟边界、公开页零 API 请求和错误；320/390/768/1440 适配及减少动画；英文首次打开和保持当前步骤的语言切换。原有视觉回归继续覆盖 1024 等尺寸。独立审查查看桌面三页与 320 小屏，无裁切或重叠；已修复发现，无开放 P1/P2。

内置浏览器现有标签已刷新并选中中文版“宠物管家”。本机 `8807` 为本次新建的内存预览；原持久化数据库保持原样。服务没有新增云调用。

## 实际截图

[桌面小狗饮食](pet-concierge-2026-10-15/pet-concierge-1440-step-1.png) · [桌面猫咪状态](pet-concierge-2026-10-15/pet-concierge-1440-step-2.png) · [桌面上下文对比](pet-concierge-2026-10-15/pet-concierge-1440-step-3.png)

[320 小狗](pet-concierge-2026-10-15/pet-concierge-320-step-1.png) · [320 猫咪](pet-concierge-2026-10-15/pet-concierge-320-step-2.png) · [320 对比](pet-concierge-2026-10-15/pet-concierge-320-step-3.png) · [390 猫咪](pet-concierge-2026-10-15/pet-concierge-390-step-2.png)
