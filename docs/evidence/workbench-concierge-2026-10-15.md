# 工作台宠物管家演示验收

日期：2026-10-15。任务：WORK-CASE-01。用户要求将宠物管家案例加入工作台演示。

## 交付与入口

[当前本地预览](http://127.0.0.1:8807/?preview=workbench-concierge-20261015#workbench/concierge)。保留原演示口令保护；登录后侧栏新增“宠物管家”，直接打开或刷新深链均停留在本页。英语默认，支持中文切换。

复用已完成的宣传页案例，避免两处示例和文案漂移。`concierge-scenario.ts` 提供共用步骤；新 `WorkbenchConcierge.tsx` 只维护本页步骤状态，通过已有 `CasePreview` 和 `PetConciergePreview` 渲染：

1. **小狗饮食**：Miso，彭布罗克威尔士柯基犬，雄性、2 岁、9.40 kg，已确认喜欢鸡肉。主人询问能否吃巧克力，预设回复说明风险，并参考偏好给出替代零食及注意事项。
2. **猫咪状态**：Luna，短毛黑白双色家猫，雌性、3 岁、3.68 kg。结合窗边、客厅、饮水区的模拟轨迹，列出进食、饮水、排尿、呼吸和呕吐/腹泻观察项与就医提示。活动接近平日不能排除生病；到过饮水区不表示已喝水。
3. **上下文随行**：比较没有提供宠物资料的新会话与随提问带入档案、确认偏好的会话，展示具体可见资料，不泛化其他产品的能力。

工作台增加场景切换、阅读提示与重新开始按钮；手机导航调整为四项。案例页面隐藏原 Mochi 事实卡，避免把它与 Miso/Luna 混用。原请求所有权、运行追踪、审批与退出行为保留。

## 数据与能力范围

本页角色、档案、偏好、对话和轨迹均为固定虚构示例。Alexa 是预设网页回复，没有新增实时模型分析、实际定位或诊断能力。切换步骤、语言和重新开始不会发送业务 POST、创建任务、生成报告或读写家庭资料。工作台原有身份验证与只读状态查询仍按原流程执行。

没有后端、接口、依赖、锁文件或业务数据库修改；现有 `PetConciergePreview.tsx` 健康文案未变。保留当前完整工作区及既有视频材料，未提交、推送或发布。修改前 7 个文件及 SHA256 清单保存在仓库外 `outputs/PawTwin-before-workbench-concierge-2026-10-15`，快照文件校验一致。

健康提示沿用已核对的直接来源，组件内可点击：

- [Merck Veterinary Manual：Chocolate toxicosis](https://www.merckvetmanual.com/toxicology/food-hazards/chocolate-toxicosis-in-animals)
- [PDSA：Your dog's diet](https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet)
- [VCA：Recognizing signs of illness in cats](https://vcahospitals.com/know-your-pet/recognizing-signs-of-illness-in-cats)

## 本轮验证

新增测试先在旧构建确认缺少新页面而失败，再构建实现验证通过。以下命令通过项目运行时执行；测试服务使用独立内存 SQLite、`local_fake` 和 `local_rules`，不会读取持久化演示库。

```powershell
. ./scripts/node-runtime.ps1
$runtime = Get-PawTwinNodeRuntime
$env:PAWTWIN_E2E_PORT = '8833'
$env:PAWTWIN_BROWSER_EXECUTABLE = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
Push-Location frontend
try {
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','build')
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','test:e2e','--','e2e/workbench-concierge.spec.ts','e2e/workbench-upgrade.spec.ts','e2e/workspace-shell.spec.ts','e2e/i18n.spec.ts','e2e/pet-concierge.spec.ts')
  Invoke-PawTwinNpm -Runtime $runtime -NpmArguments @('run','test:e2e','--','e2e/approve.spec.ts','e2e/showcase.spec.ts')
} finally { Pop-Location }
```

结果：**19 passed（31.9 秒）+ 16 passed（23.2 秒），共 35 项，0 retries**。两次命令分别启动独立内存服务。

- 新增 4 项覆盖英文首次打开、登录前不可见/退出后隐藏、深链、三步键盘切换、双语保持当前步骤与角色值、四种宽度以及案例操作零业务写入。
- 原运行追踪测试暂时延迟真实运行 GET 的传输，不伪造响应。进入案例再返回后保留同一请求编号和操作锁，释放真实响应后可继续审批/拒绝。
- 既有工作台、壳层、双语、审批和公开案例测试覆盖兼容性。
- TypeScript 与生产构建 PASS。Vite 保留既有超过 500 kB 的分块提示：主 JS 604.61 kB / gzip 189.66 kB，CSS 155.08 kB / gzip 33.40 kB。
- `git -c core.safecrlf=false diff --check` PASS；修改前快照 7/7 SHA256 一致；原共享宠物管家展示组件与快照一致。
- 后端代码未改，本轮未重跑后端全套；之前的全量结果属于历史证据。

独立 reviewer 只读复核登录保护、请求所有权、零业务调用、双语和样式作用域，以及五张区域图和两张完整页图，无开放 P1/P2。完整页截图确认桌面/手机无内容裁切，区域截图中固定页头产生的画面遮挡未出现在实际完整页布局中。

## 画面与复核材料

16 张截图：8 张 320/390/768/1440 案例区域图，加 8 张中英文 1440/390 完整页图。全部宽度无水平溢出，三个步骤均做键盘和布局检查。

- 完整页：[中文桌面小狗](workbench-concierge-2026-10-15/full-zh-1440-step-1.png)、[中文桌面猫咪](workbench-concierge-2026-10-15/full-zh-1440-step-2.png)、[中文手机小狗](workbench-concierge-2026-10-15/full-zh-390-step-1.png)、[中文手机猫咪](workbench-concierge-2026-10-15/full-zh-390-step-2.png)
- 英文：[桌面小狗](workbench-concierge-2026-10-15/full-en-1440-step-1.png)、[桌面猫咪](workbench-concierge-2026-10-15/full-en-1440-step-2.png)、[手机小狗](workbench-concierge-2026-10-15/full-en-390-step-1.png)、[手机猫咪](workbench-concierge-2026-10-15/full-en-390-step-2.png)
- 区域：[320 小狗](workbench-concierge-2026-10-15/workbench-concierge-320-step-1.png)、[320 猫咪](workbench-concierge-2026-10-15/workbench-concierge-320-step-2.png)、[768 小狗](workbench-concierge-2026-10-15/workbench-concierge-768-step-1.png)、[768 猫咪](workbench-concierge-2026-10-15/workbench-concierge-768-step-2.png)
- [验证摘要](workbench-concierge-2026-10-15/verification.json)、[完整页宽度](workbench-concierge-2026-10-15/full-page-checks.json)、[截图脚本](workbench-concierge-2026-10-15/capture.cjs)

本机 `8807` 沿用当前内存预览，不代表原持久化演示库；原数据库没有被本轮截图或测试写入。
