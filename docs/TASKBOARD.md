# PawTwin 开发任务看板

## 2026-10-14：当前版本代码、逻辑与应用审查

REVIEW-01 done_local。用户授权检查当前完整版本，问题修复并验证后提交本地 Git。基线为 `chore/bootstrap` / `31da349` 加完整既有工作区；保留原源码、演示库和媒体，不从 HEAD 另起缺失功能的版本。Coordinator 串行整合与提交；审查阶段只读，确认缺陷后再分配互不重叠的修复范围。

| Owner | 修复写范围 |
| --- | --- |
| backend_review / BE-REVIEW-01 | `backend/pawtwin/family_models.py`、`tests/test_family_memory_validation.py` |
| integration_review / INTEG-REVIEW-01 | 六个本地测试模块的 Settings 构造、`tests/test_local_fixture_isolation.py` |
| frontend_review / FE-REVIEW-01 | `frontend/src/FamilyApp.tsx`、`frontend/e2e/family-session-isolation.spec.ts` |
| Coordinator | 前端修复整合、演示测试日期选择、导出与 Git 排除规则、分片验证脚本/CI、对应导出测试、README/状态/看板与审查证据 |

最终后端 **447 passed / 1 skipped / 21 live-AWS deselected**；完整浏览器 **115 passed，0 retries**；Ruff、契约、类型、生产构建、锁文件和 diff 检查通过。三个独立 reviewer 已复核修复，无开放发现。用户授权本地 Git 提交，未授权推送或部署，仓库当前没有远程地址。完整[审查记录](reviews/current-version-2026-10-14.md)包含测试命令、证据及未验证范围。

## 2026-10-14：全界面英语 / 中文

I18N-01 done_local。基线为 `chore/bootstrap` / `31da349` 加当前完整 dirty 工作区；修改前源码快照在 `%TEMP%/pawtwin-i18n-20261014/baseline-src`。Coordinator 串行整合，保留既有改动；三个翻译 Agent 只写仓库外 staging，独立 reviewer 只读。

增量写范围：相关 `frontend/src/` 组件、语言字典与样式、`frontend/index.html`、`frontend/playwright.config.ts`、新增双语测试及三个已有多浏览器场景的语言设置、README/STATUS/本节及验证材料。不写后端、契约、依赖锁、业务数据库或照片。完整回归 107 passed，后端基线 425 passed / 1 skipped / 21 deselected；见[交付与证据](evidence/i18n-2026-10-14.md)。

## 2026-10-13：演示登录使用记录

DEMO-01 done_local：按用户要求为演示登录补齐档案、体重、照护任务、报告和确认偏好。Coordinator 串行使用已有认证/CSRF API，限定现有 `8807`、`8834` 的 `demo-owner` 与 `8834` 的已知家庭演示账号，不写其他家庭、不修改后端/界面/接口。两个预览 family 数据库已在线备份，所有样例明确虚构，原有记录保留。三个上下文各新增 7 次体重、6 个照护计划/3 次服务器演示完成、3 条确认偏好和 4 份实际计算报告；同日重放无重复。demo_data_audit 独立复核数据/报告一致，两种登录方式的实际页面/刷新/本地规则引用通过，26 张桌面与手机截图已保存。Ruff、diff 检查通过；旧 8807 的来源历史兼容差异见[完整记录](evidence/demo-usage-2026-10-13.md)，当前主演示为 8834。

## 2026-10-13：宣传页成长记录模拟数据

PRODUCT-04 done_local：用户明确要求宣传页成长记录填入模拟数据。只填公开产品示意与成长回顾案例，不写入家庭账号、业务记录或数据库。四只虚构宠物各用一组静态体重记录，显示日期、来源、变化和曲线；数值区域明确标注模拟。

沿用 `chore/bootstrap` 当前完整 dirty 工作区，修改前快照在仓库外 `%TEMP%/pawtwin-growth-demo-20261013`。共享源码由 Coordinator 串行修改，保留 UI-05 和既有工作。

| Owner | 独占写路径 |
| --- | --- |
| Coordinator | `frontend/src/Showcase.tsx`、`CasePreview.tsx`，新增 `ProductGrowth.tsx`、`product-growth.css`；状态、看板和本次证据 |
| growth_tests | 新增 `frontend/e2e/product-growth.spec.ts`，只写测试；不构建、不启动服务 |
| growth_review | 只读审查数据计算、模拟标识和公开页边界 |

验收：曲线/列表/摘要数值一致，切宠切场景正确，320/390/768/1440 无溢出，公开页面零业务请求，相关浏览器回归及类型/构建通过。

最终 23 项相关浏览器测试通过（41.9 秒，0 retries），TypeScript/生产构建和 diff 检查通过。六张最终截图经独立复核无开放 P1/P2；刻度精度、坐标标签碰撞及测量数字颜色覆盖已修正。[本次证据与画面](evidence/product-growth-2026-10-13.md)。本机 `8807/#features` 已刷新到成长记录，未提交或发布。

## 2026-10-13：家庭应用与照护工作台同步升级

UI-05 done_local：用户确认两个入口一起调整，完善现有能力与操作流程，统一设计并保留各自账号、数据和权限。沿用当前完整 dirty 工作区；界面基线已复制至仓库外 `outputs/PawTwin-before-workspace-2026-10-13`，逐文件 SHA256 见该目录 `baseline.json`，最终 55/55 复核一致。不从 HEAD 工作树覆盖尚未提交的功能。

| Owner | 独占写路径 |
| --- | --- |
| application_audit | `frontend/src/FamilyApp.tsx`、`FamilyCare.tsx`、`FamilyToday.tsx`、`family-app.css`、`family-time.ts`；新增 `family-workspace.css`、`frontend/e2e/application-upgrade.spec.ts` |
| showcase_audit | `frontend/src/App.tsx`；新增 `workbench.css`、`frontend/e2e/workbench-upgrade.spec.ts` |
| capability_audit | `frontend/src/PetHome.tsx`、`pet-home.css`；新增 `PetAvatar.tsx`、`pet-avatar.css`、`frontend/e2e/pet-visual-upgrade.spec.ts` |
| Coordinator | 共用导航/视觉样式、`main.tsx`、已有 e2e 的界面适配、文档、基线与集成验证；接口和后端保持不变 |

先由各包编写操作回归，Coordinator 在旧实现上确认预期失败后再交付实现。共享文件串行整合，不同时构建或运行会争用服务的浏览器测试。验收覆盖家庭日常闭环、重复照护、分身权限、授权/导出、审批/回执/运行切换、独立登录、深链、键盘及 320/390/768/1440 页面；既有后台、契约、构建与浏览器基线同步检查。不新增云调用、部署或服务交易。

完成证据：[UI-05 验收](evidence/workspace-upgrade-2026-10-13.md)。最终 100 个不同浏览器测试通过（19 文件、独立测试服务、0 retries），425 backend passed / 1 skipped / 21 live-AWS deselected（51.31 秒），Ruff/契约/TS/build PASS。新添回归先 RED 再 GREEN；独立代码/截图复核无待修复 P1/P2。38 张四宽截图无水平溢出，预览在独立虚构库 `:8834`，保留原数据与既有修改。

## 2026-10-13：完整产品介绍页

PRODUCT-03 done_local：用户要求修整网页标题与显示效果、缩短手机、让像素宠物更可爱协调。沿用完整 dirty 工作区与现有产品/案例，不改业务应用与数据。

写路径：Coordinator 独占 `Showcase.tsx` 的标题排版、新 `visual-polish.css`、页面 title/metadata 与相关文档；phone_polish 独占 `ProductDevices.tsx` 中 PhonePreview 与 `device-preview.css` 的手机样式；pet_polish 独占 `PetPortrait.tsx`；polish_review 只读。新增验证或既有测试调整由 Coordinator 串行处理。验收为 320/390/768/1024/1440 标题可读、固定且合理的手机比例、设备不遮挡文案、角色一致且可切换、无业务请求、构建和相关回归。

完成证据：[PRODUCT-03 验收](evidence/product-polish-2026-10-13.md)。类型与生产构建通过，最终 20 项相关浏览器回归通过；五宽标题分句边界与手机比例/内容不裁切通过，独立代码和截图复核无待修复 P1/P2，27 张截图与校验清单已保存。

PRODUCT-02 done_local：用户追加要求提升平板与手机示意界面、让三个场景有不同结构与更丰富内容、加入其他宠物角色。保留 PRODUCT-01 的产品叙事和应用入口，宣传演示仍为虚构内容且不请求业务 API。

本轮完整 dirty 工作区串行集成；Coordinator 独占 `Showcase.tsx`、新 `ProductDevices.tsx`/`device-preview.css`、新 `pet-gallery.css` 与任务文档；pet_art 独占新 `PetPortrait.tsx`；case_visuals 独占新 `CasePreview.tsx`/`case-preview.css`；visual_tests 独占新 `frontend/e2e/product-visuals.spec.ts`。不写业务应用、后端、契约、锁文件或用户数据库。

验收：设备内完整且精致的示意 UI；家庭接力、成长记录册、偏好对话三种不同构图；至少四种不同猫狗角色；角色切换、案例九步骤、320/390/1440 适配、键盘和减少动画、公开页零业务请求；生产构建及相关回归。

完成证据：[视觉升级验收](evidence/product-visuals-2026-10-13.md)。最终 20 项浏览器回归通过；425 项后端测试通过、1 项命名跳过、21 项真实云排除；Ruff、契约与构建通过。独立审查发现的手机遮挡首屏问题已改用参与高度的网格叠放并验证，当前无待解决问题；17 张截图和校验清单已保存。

PRODUCT-01 done_local：用户要求将现有宣传页优化为真正的产品页面。基线为 `31da349` 上的完整 dirty 工作区，保留现有平台、就诊卡、只读授权和应用改动，不从 HEAD 恢复或交叉同步项目。

可写路径：Coordinator 独占 `frontend/src/Showcase.tsx`、`showcase.css`、新增 `ProductSections.tsx`/`product-page.css`、`frontend/index.html`、`frontend/src/main.tsx` 的产品标题及本任务文档；product_tests 独占 `frontend/e2e/showcase.spec.ts`、`family.spec.ts` 的受影响产品标题断言和新增 `product-page.spec.ts`。product_audit / product_review 只读。使用现有完整工作区；不创建遗漏未提交功能的 HEAD 工作树。

验收：明确产品类别、用户价值与适用人群；可体验功能和未来服务分开表达；真实只读交接流程；开始使用及 FAQ；移动导航、键盘、减少动画、应用深链；公开页零业务请求；类型、构建及相关浏览器回归。本任务不部署、不发布、不提交比赛、不新增依赖或云调用。

完成证据：[产品页验收](evidence/product-page-2026-10-13.md)。37 项相关浏览器回归通过，最终产品复测 15 项通过；425 项后端基线通过，1 项命名跳过，21 项真实云测试排除；Ruff、契约与生产构建通过。只读独立审查的手机菜单规则和修饰键问题均已修复，内置浏览器保留预览。

## 2026-10-12：照护交接、分身临时访问与就诊卡

PLATFORM-01 done_local（2026-10-13 完成验收）：用户批准产品方案与官网概念展示，并明确增加实际就诊信息卡导出及指定宠物、有效期、可撤销的分身只读访问。上门代喂、换水、清洁、陪玩、遛狗为未来服务场景；订单市场与支付仍后置。

基线：当前完整 dirty 工作区；修改前文件保存在工作文件夹 outputs/PawTwin-before-platform-2026-10-12，SHA256 在 evidence/platform-2026-10-12/baseline.json。源码备份放在仓库外以免被开发检查误认作当前代码。保留此前 UI-04 和所有既有修改，不从 HEAD 覆盖文件、不提交/推送/部署。

| Owner | 本轮独占写路径 |
|---|---|
| feature_audit | backend/pawtwin/family_api.py、family_views.py、family_store.py、api.py、main.py；新增 visit_summary.py、care_access.py；tests/test_visit_summary.py、test_care_access.py |
| ux_audit | frontend/src/FamilyApp.tsx、family-api.ts、family-app.css、main.tsx；新增 VisitCard、CareAccess 组件及独立样式；frontend/e2e/platform.spec.ts |
| showcase_audit | frontend/src/Showcase.tsx、showcase.css、frontend/e2e/showcase.spec.ts |
| Coordinator | docs、项目/工作区 README、contracts 生成与检查、验证/隔离预览和集成；其他路径变更先协调 |

执行裁定：导出使用当前已记录事实、来源、所选窗口和截至时间，默认排除演示测量；支持浏览器打印/另存 PDF 和可下载的自包含 HTML 信息卡。数据未知保留空白。分身访问仅限所授权宠物的照护资料，使用可撤销的临时密钥，密钥只在创建响应返回且存储哈希；只读访问不授予家庭成员、记录修改、照护确认、设备或交易权限。访问期限 1/4/24/72 小时，默认 24 小时，创建/撤销需家庭管理员。新功能不引入云调用或依赖。

契约：GET /api/family/pets/{pet_id}/visit-summary?days=7|30|90&include_demo=false 保留旧字段并补充照护、日记、偏好、时区/窗口/缺项；POST/GET /api/family/pets/{pet_id}/care-access，POST /api/family/pets/{pet_id}/care-access/{access_id}/revoke。独立 GET /api/care-access/context 与 POST /api/care-access/chat 从 Authorization Bearer 密钥验证授权，不复用家庭登录权限。/#pet-access=<密钥> 为独立只读入口；公开官网始终不读取家庭资料。

验收：来源/历史/演示隔离、跨宠与跨家庭、过期/撤销/归档、管理员与只读权限、请求/响应隐私、临时分身无写入、打印/下载与错误重试、移动/键盘/动画、官网零业务请求；全量相关回归与独立审查。

最终：425 backend passed / 1 skipped / 21 live AWS deselected；77 browser passed（48+17+12 独立服务、0 retries），Ruff/契约/TS/build PASS。权限、归档恢复后旧授权不可复活、只读快问语义、500 不缓存、切宠/切密钥与导出快照均验证；独立复核无开放问题。原全局家庭 guest POST 权限未放宽。已实际下载演示 HTML，并在内置浏览器验证授权→读取/问答→撤销。当前预览 8820，独立虚构库，代码未提交；[完整证据](evidence/platform-2026-10-12.md)。

## 2026-10-12：应用实用性与可视化

UI-04 done_local：用户确认先完善实际应用，再同步官网。沿用当前业务接口，修复重复计划编辑、子数据加载重试、历史完成统计；增加今日概览、照护筛选、实测曲线与报告摘要、明确功能跳转。

基线：chore/bootstrap / 31da349，393 backend passed / 1 skipped / 21 live AWS deselected，Ruff/契约/TS/build PASS。保留全部既有未提交内容；本轮前快照在工作文件夹 outputs/PawTwin-before-usability-2026-10-12.zip，逐文件基线见 evidence/usability-2026-10-12/baseline.json。

| Owner | 本轮独占写路径 |
|---|---|
| feature_audit | backend/pawtwin/growth.py、home_api.py（仅完成事件来源关联）、tests/test_care_statistics.py |
| ux_audit | frontend/src/FamilyApp.tsx、FamilyRecords.tsx、family-api.ts、family-app.css、PetHome.tsx、main.tsx；新增 family 组件/工具；frontend/e2e/usability.spec.ts，必要的既有 family/demo 测试适配 |
| showcase_audit | frontend/src/Showcase.tsx、showcase.css、frontend/e2e/showcase.spec.ts |
| Coordinator | 本轮 docs、项目/工作文件夹 README、验证日志、预览与整体验收；frontend/e2e/alexa.spec.ts（已批准深链的导航断言） |

裁定：在已授权的现有专用分支上，以本轮完整工作区为基线，按互不重叠写路径推进；不从仅含 HEAD 的工作树覆盖当前家庭功能。不改依赖、生成契约、工作数据库、云或原始媒体。验证仍使用隔离测试库/端口。feature 深链统一为 #app/home、#app/care、#app/growth、#app/assistant、#app/family；#app 和 #alexa 继续兼容。

最终：408 backend passed / 1 skipped / 21 live AWS deselected；Ruff/契约/TS/build PASS；62 browser passed，按 45+17 两个全新测试服务覆盖全部文件，0 retries，未放宽真实注册限流。独立复核问题和 Alexa 往返竞态已修复并验证。内置浏览器预览 8820，独立虚构库。交付在未提交工作区，下一依赖为真实家庭试用和单独的云验证；见 [功能指南](FEATURES.md)、[完整验收](evidence/usability-2026-10-12.md)。

## 2026-10-12：英文比赛演示视频

VIDEO-01 done_local：协调者负责制作/核验/媒体脚本；demo_audit只读定位真实WebM时段，repair_review独立复核。用户已选择英文比赛版，13场景、170.0185034秒、1080p、26句字幕、8段真实1×动作18.4秒；37实际帧和音轨检查通过。保留旧素材，未调用云/上传/提交。完整人类播放听审待本人完成。[本轮交付](submission/demo-video-2026-10-12.md)。


## 2026-10-11：比赛准备与当前 demo

SUB-READY-01 done_local：协调者负责修复/验证/集成；demo_audit负责采集/视频/导出器；rules_audit负责规则和四份英语材料；repair_review独立只读复核。完整dirty基线31da349/chore/bootstrap，写路径见[执行计划](plans/submission-readiness-2026-10-11.md)。393 backend / 42 browser通过，1 skipped / 21 live AWS deselected，Ruff/契约/TS/build PASS，独立复核通过。14PNG、双账号WebM、170.0185034秒英语视频解码/画面检查通过，完整人工听审待本人完成。[验收证据](evidence/submission-readiness-2026-10-11.md)。

SUB-RELEASE-01 待本人决定/授权：资格/权利、主路径与实际工具个人反馈、GitHub许可或私有访问、公开YouTube/Vimeo视频及Devpost提交。未推送/发布/提交；AWS Builder实际使用证据为可选另行验收。

本表由总负责人维护。`ready` 表示依赖满足、可认领，不表示已经有人开始。未获得明确开发指令时，不自行启动所有任务。

## 2026-10-11：Alexa+ 网页模拟体验

ALX-01：done_local。用户目标：完成 Alexa+ 网页模拟体验。
Owner：Codex 协调者在当前工作区串行写入；alexa_audit / alexa_ux_review 只读复核。
基线：31da349 / chore/bootstrap 加当前全部未提交功能；不从 HEAD 另建遗漏现有功能的副本。
可写：FamilyApp/main/family-api、独立 AlexaSimulator 组件及样式、family_api/models/views、pet_context、对应测试、生成契约与本轮文档。
范围：独立模拟入口、当前页面连续对话与新会话、共享宠物上下文及来源、规则照护草案→明确确认→人工任务→结果查看；加载/错误/无权限/多宠隔离、移动和键盘验收。
接口：沿用 chat/proposals/confirm/home；回复新增可选照护草案，草案转方案可校验原上下文版本。
边界：本地规则、本地存储、网页输入模拟；真实 Alexa、模型、AWS 与硬件未接通。无依赖/部署/发布/云调用。

验收：346 后端 passed / 1 skipped / 21 deselected，ruff/契约/TS/build PASS；8 项 Alexa 定向和最终 41 项浏览器 PASS，0 retries。真实存储闭环、版本/时间失效拒绝、宠物切换延迟回复、错误重试、320/390/1440、键盘与减少动画通过。两位独立 reviewer 发现已修复，当前范围无待处理项。[证据与运行说明](evidence/alexa-simulator-2026-10-11.md)。

## 2026-10-11：动画与情景案例

UI-03：done_local。Owner：Codex 协调者串行实现，premium_review 独立只读复核。
基线：31da349 / chore/bootstrap 加现有 UI-02 工作区；保留其他未提交内容。
可写：Showcase.tsx、showcase.css、showcase.spec.ts、README/STATUS/TASKBOARD 和本轮证据。
范围：可暂停的轻量动态、滚动入场、功能切换反馈，三组逐步查看的照护情景案例。案例明确虚构示意、手动操作，无真实账号、测量、模型或业务请求。
验收：案例切换/步骤重置、键盘/减少动画/全局暂停、移动无溢出和直接锚点、零公开业务请求、现有浏览器回归与独立复核；无后端/依赖/API/发布。
结果：verify 333 passed / 1 skipped / 21 deselected 与 ruff/契约/TS/build PASS；最终 33 浏览器 passed（34.3 秒，0 retries）。独立全部 27 案例组合验证通过；提示容器重建问题已修复并复验。[证据](evidence/motion-cases-2026-10-11.md)。

## 2026-10-11：产品官网视觉升级

UI-02：done_local。Owner：Codex 协调者串行实现，premium_review 独立只读复核。
基线：chore/bootstrap / 31da349，保留当前未提交家庭功能、云适配与 UI-01 成果。
可写路径：frontend/src/Showcase.tsx、showcase.css、frontend/e2e/showcase.spec.ts、本轮 README/STATUS/TASKBOARD 与证据。
目标：Apple 风格的简洁产品官网；居中大标题、设备画面、明暗章节、四项体验、清晰应用入口与移动端适配。仍为 PawTwin 自有内容。
验收：类型/构建、现有全量浏览器回归、320/390/1440 视觉与溢出、键盘及减少动画偏好、公开页无业务请求、能力标签和路由/会话保留；独立审查。
不改后端、API、锁、数据库或真实云状态；不部署、推送或发布。
验证：基线 333 passed / 1 skipped / 21 deselected，ruff/契约/TS/build PASS；最终 31 浏览器 passed，0 retries。实际桌面/手机截图、320/390/1440 全部预览、键盘与减少动画、零公开页业务请求均通过；独立复核问题修复后无待解决发现。[交付证据](evidence/premium-showcase-2026-10-11.md)。

## 2026-10-04：产品宣传页与应用界面分离

UI-01：done_local。Owner：Codex 协调者串行写入；navigation_audit/ui_review 只读。
基线：chore/bootstrap / 31da349，保留现有未提交的家庭功能与展示材料。
可写路径：本轮 frontend/src 页面/导航/样式、frontend/e2e 入口与行为验证、frontend/index.html、README、TASKBOARD、STATUS 与本轮证据。
接口沿用现有 API；首页为无登录产品介绍，/#app 为家庭应用，/#workbench 为原照护工作台，/#home 保留原小屋。无依赖、契约、后端或数据库变更。
验证：333 后端 passed / 1 skipped / 21 deselected，30 浏览器 passed，ruff/契约/TS/build PASS；独立复核的文字对比度问题已修复。见 [本轮证据](evidence/product-and-app-2026-10-04.md)。

## 2026-10-03：黑客松补齐更新（当前）

本地缺陷修复与全量复验完成：333 后端 passed / 1 skipped / 21 deselected，27 浏览器 passed，ruff/契约/TS/build PASS；独立复核和最新材料见 [完整度报告](evidence/hackathon-completeness-2026-10-03.md)。EXT-11 的本地自动化部分通过；真实家庭试用与模型质量评估仍待执行。EXT-12 已补英语材料、真实录屏和 170.019 秒英文审核 MP4；人工听审、公开访问、个人反馈与资格裁定、正式提交仍待做。

EXT-10 仍 blocked：用户授权 10 美元、本次服务范围不限；账户官方验证约两天，预算已给出，当前阻挡是服务/短期本地授权可用性和真实接线，不能继续列为未获得预算。本轮没有云调用、资源创建或费用。以下当前附加任务表是补齐前快照。

## 当前附加任务状态：2026-10-03 开发验收

Owner：Codex 协调者串行实施，独立 reviewer 只读；起点 31da349。可写路径 backend/frontend/tests/contracts、锁/装配与本轮状态/交接。原 STATUS/TASKBOARD 和路线/基线评审内容保留，契约与锁串行。

| ID | 当前状态 | 交付/下一依赖 |
|---|---|---|
| EXT-00 | done_local | 接口冻结，52 路径 OpenAPI，六设备输入稳定 |
| EXT-01 | done_local | scrypt 本地账号、CSRF、刷新会话、可信作者；重启重新登录 |
| EXT-02 | done_local | 家庭/时区/邀请/撤销/角色/称呼/头像/移交/撤权 |
| EXT-03 | done_local | 幂等副本迁移/照片/旧新共享/原额度/任务 CAS 与实例/10 秒同步 |
| EXT-04 | done_local | 实测/单位/饮食/纠错删除/观察日记管理/档案与归档恢复 |
| EXT-05 | done_local | 日周统计/持久化 worker/失败重试/补跑/重建；通知未发送 |
| EXT-06 | done_local（本地数据库） | 五层上下文/确认记忆/失效/冲突；无 AgentCore 提炼 |
| EXT-07 | done_local | 五入口 App、小屋/曲线/报告、390/1440 |
| EXT-08 | done_local（规则与网页模拟） | 共用上下文/慢回复隔离/确认人工照护；真实推理依赖 EXT-10 |
| EXT-09 | done_local（保守参考） | 来源/范围/缺项/就诊摘要；无数值曲线或完整品种库 |
| EXT-10 | blocked | 10 美元预算与不限服务范围已授权；官方账户审核约两天；新家庭云接入/真实推理记忆及短期凭据仍待验证 |
| EXT-11 | in_progress | 当前后端 333 + 浏览器 27 通过；双账号排练和独立复核完成；真实家庭试用/模型评估/生产专项未做 |
| EXT-12 | in_progress | 英语项目/评委指南/工具反馈草稿、实际录屏和 170.019 秒英文审核版就绪；人工听审/公开访问/个人反馈裁定/资格/提交未完成 |

[实测证据](evidence/extension-local-2026-10-03.md) · [审查裁定](reviews/EXT-local-review-2026-10-03.md)。未提交/推送/发布，done_local 不等于 done_cloud。以下历史表格不再作为当前派发状态。

本轮追加：[完整度补齐与最终验证](evidence/hackathon-completeness-2026-10-03.md) · [展示方案](submission/PawTwin_展示方案_2026-10-03.md)。检查范围内无未解决功能失败；已新增独立审查，真实云验收仍未完成。

## 2026-10-03 后续开发路线派发

用户裁定「根据当前进度规划后续开发」：①路线图 + 启动 EXT-00；②先分组提交固化基线；③本地优先、云后插入。

**基线已固化**：65 项未提交按 4 组入库，**HEAD=`31da349`、工作树干净**（`cf93e5e` Day-5 / `430e729` Home / `3bec7be` 共享装配 / `31da349` 文档）；提交前 `verify.ps1` 全绿（252 passed、契约 28 路径 current、build 通过），e2e 未重跑。**后续开发基线起点 = `31da349`**。路线详见 [后续开发路线](plans/PawTwin_后续开发路线_2026-10-03.md)（EXT-00→12 对齐 G0–G5；脊柱 EXT-00→01→02→03）。

**EXT-00 进行中**（本轮，只读）：基线评审 + 身份/家庭/成长/报告/上下文契约草案 + 迁移映射与消费者清单，见 [EXT-00 评审](reviews/EXT-00-baseline-review.md)。**未写业务代码、未改数据库、未迁移**；契约冻结（门 0）待用户授权后才派发 EXT-01/02/07。云仍无凭据，EXT-10 维持 blocked。

## 2026-10-02 附加工作包

需求/验收以 [附加计划](plans/PawTwin_附加开发计划_2026-10-02.md) 为准，接手先读 [Qoder 说明](QODER_HANDOFF.md)。本次只同步文档，未派发实施。
全部 Owner 未认领；建议分工不代表已有进度，不与旧任务的本地完成状态混淆。

| ID | 状态 | Owner | 依赖 | 交付 |
|---|---|---|---|---|
| EXT-00 | in_progress（本轮，只读评审+契约草案） | 总负责人（规划） | 当前基线检查（✅ `31da349`） | 接口、兼容迁移与写路径冻结 |
| EXT-01 | planned | 未认领 | EXT-00 | 独立身份、作者、会话恢复 |
| EXT-02 | planned | 未认领 | EXT-01 | 家庭/邀请/称呼/权限/撤权 |
| EXT-03 | planned | 未认领 | EXT-02 | 共享迁移、任务生命周期、同步/并发 |
| EXT-04 | planned | 未认领（Qoder 可选） | EXT-03 | 成长记录与纠错 |
| EXT-05 | planned | 未认领（Qoder 可选） | EXT-04 | 日/周统计与自动补跑/重建 |
| EXT-06 | planned | 未认领 | EXT-05 | 个体上下文与记忆确认/失效 |
| EXT-07 | planned | 未认领（建议 Qoder） | EXT-00；联调另依赖 EXT-02–06 | App 导航、小屋/家庭/成长/报告组件 |
| EXT-08 | planned | 未认领 | EXT-06、EXT-07 | App/Alexa 模拟共用分身与受控行动 |
| EXT-09 | planned | 未认领 | EXT-06、EXT-08 | 参考知识、健康问答边界 |
| EXT-10 | planned | 未认领 | EXT-00 起预检；云验收依赖 EXT-03–08 及账号/预算 | 云身份/资料/模型/记忆证据 |
| EXT-11 | planned | 未认领 | 对应已实施包 | 验收、用户试用与独立复核 |
| EXT-12 | planned | 未认领 | EXT-11；AWS 宣称另依赖 EXT-10 | 英文材料、演示和访问检查 |

认领格式：日期 / ID / Owner / 基线与未提交内容 / 可写路径 / 依赖和接口版本 / 验收 / 交接。当前没有认领记录。
共享契约、锁文件、main/config、api.ts 和状态文档串行协调，不覆盖别人的修改。

## 既有 Home 与 Day-1–Day-5 历史

2026-10-02 用户授权「按六项改」并补充洗澡、剪指甲、成长照片：由总负责人串行完成
HOME-01 档案/模板形象、HOME-02 物品管理、HOME-03 照护计划、HOME-04 范围偏好、
HOME-05 家庭显示名与交接、HOME-06 照片日记与摘要。以上本地实现及验证完成，
详见 STATUS。照片识别实际云调用、生成式肖像、独立成员账号、
多宠物自动喂食和新资料层云存储未完成；不将本地扩展升级为云端或参赛验收完成。

| ID | 状态 | Owner | 依赖 | 交付与验收 |
|---|---|---|---|---|
| INIT | done | 初始化 Agent + 总负责人 + 独立审查 Agent | 无 | 可启动骨架、契约、协作资料；26 项后端测试及前端/浏览器检查通过，详见 STATUS |
| BE-01 | done (Day-1, local) | 总负责人+后端(串行) | INIT | 契约已冻结（OpenAPI 含业务路由）；SQLite 持久化/去重/幂等回执/租约；DynamoDB 云测顺延 |
| BE-02 | done (Day-1 最小集, local) | 后端(串行) | BE-01 | 策略/登录/CSRF/审批/模拟执行/恢复(逻辑级)；A02/A03/A05/A12/A13(逻辑级) 本地绿；A04 跨进程、真实重启顺延 |
| BE-03 | done (Day-2, local) | 总负责人+后端(串行) | BE-02、门0冻结 | 并发原语（claim 白名单/续约/CAS/尝试上限原子自增）+ schema 幂等迁移 + 异步 worker + demo/facts、demo/device-mode；A04(同进程)/A09/A13(文件库)/A05(不重复调模型) 本地绿；跨进程顺延 |
| BE-04 | done (Day-3, local) | 总负责人+后端(串行) | BE-03、门0冻结(记忆 seam) | 反馈持久化(feedback 表/幂等)+ worker 真并发(有界池/per-task worker_id/先准入后 claim)+ 跨进程双批准(文件库两连接/WAL)+ 真实进程重启复验；A04(跨进程)/A13(真实进程) 本地绿；跨副本 DynamoDB 顺延 Day-4 |
| FE-01 | done (Day-1, local 联调) | 前端(串行) | INIT；联调需 BE-01 | 三主区 + 真实 /api 联调 + 拒绝闭环 e2e；记忆区/feedback 顺延 Day-3，demo/facts、device-mode 顺延 Day-2 |
| FE-02 | done (Day-2, local) | 总负责人+前端(串行) | 门0冻结；联调需 BE-03 | 证据面板+遥测、analyzer/storage/memory 标签、演示控制区接 demo 端点、中间态与显式超时提示、approve 闭环 e2e（共 7 项绿，各 spec 自行复位）；记忆区仍顺延 Day-3 |
| FE-03 | done (Day-3, local) | 总负责人+前端(串行) | 门0冻结；联调需 BE-04 | 任务与记忆区（反馈输入+memory_status 徽章+memory_backend 标签+新会话/conversation_id）；诚实标注「未实现（无账号）」，绝不声称已检索记忆；feedback e2e（e2e 共 10 项绿） |
| AI-01 | done (Day-1, local interfaces) | AI(串行) | INIT；真实调用需 AWS | 四只读工具 + owner 注入 + 证据校验 + mode-gated 本地替身；真实 Bedrock 与云测顺延 Day-2 |
| AI-03 | done (Day-2, local + 未验证云代码) | 总负责人+AI(串行) | AI-01、门0冻结(seam 签名) | `AnalyzerProposer` 适配器 + pinned 快照/证据台账 + 限额与超时 fail-closed + `AnalysisOutcome` 遥测；`BedrockAgent`/`bedrock_client.py` 已实装（strands 1.57.0、延迟导入、离线 stub 测试）但**未经真实账号验证**；真实往返仍为条件项（4 项具名 skip） |
| AI-02 | done (Day-3, local + 未验证云代码) | 总负责人+AI(串行) | AI-03、门0冻结(记忆 seam) | `memory.py`：`MemoryService` 协议 + `LocalFakeMemory`(saved/`search`→[]，绝不 available) + `AgentCoreMemory` 骨架(延迟导入，缺依赖/凭据→具名 `MemoryUnavailable`) + `StubMemoryService`；`search_owner_memory` 接线(source="memory" 证据链)；A06/A07/A08 结构本地绿；真实提炼/检索为条件项(无账号，5 项具名 skip) |
| OPS-01 | done (Day-1, plan only；**done 指计划与清单，不含镜像构建与部署**) | OPS(串行) | INIT；部署需账号预算 | `infra/cloud-access-checklist.md`；未执行、无资源、无费用 |
| OPS-02 | done (Day-2, plan+scripts；**done 指依赖/脚本准备，Dockerfile 未构建、smoke 未真实调用**) | 总负责人+OPS(串行) | 门0冻结 | `bedrock` optional extra（strands-agents==1.57.0）+ `uv.lock` + CI `uv lock --check` + Dockerfile `--extra`（**未构建验证**）+ `.env.example`/`.gitignore(*.db)`/README/角色简报 + `preflight.ps1` Bedrock 只读段 + `bedrock-smoke.ps1`（实测输出 NOT EXECUTED/退出码 2）+ 用量估算；未执行、无资源、无费用 |
| OPS-03 | done (Day-3, plan+scripts；**done 指依赖/脚本准备，Dockerfile 未构建、smoke 未真实调用**) | 总负责人+OPS(串行) | 门0冻结 | `memory` optional extra（`boto3==1.43.102`，硬门：`uv lock --check` + `uv sync --frozen --extra memory` 均成功）+ CI 全局 `uv lock --check` 覆盖 + Dockerfile `--extra memory`（**未构建验证**）+ `.env.example`/README/角色简报 + `preflight.ps1` AgentCore 只读段 + `agentcore-smoke.ps1`（实测 NOT EXECUTED/退出码 2）；未执行、无资源、无费用 |
| BE-05 | done (Day-4, local) | 总负责人(串行) | S0 基线入库 | **Day-4**：访问控制补口——cookie `Secure` 由 `mode` 解耦为按请求 scheme 判定；补 `POST /api/runs/{run_id}/approval` 未登录 401 与缺/错 CSRF 403、`POST /api/logout` 未登录 401；补「`frontend/dist` 与全仓无 AWS 凭据」的 A12 本地证据。**不得记 A12 通过**：登录限速、会话 TTL、默认口令公网暴露三项为未闭合缺口（本轮不实现） |
| FE-04 | done (Day-4, local) | 并行执行体(总负责人独立复核) | S0、BE-05（共享 `api.py` 者须串行） | **Day-4**：浏览器验收矩阵新增 6 条 e2e（未登录深链、`unknown` 回执不显示虚假成功、待批准 reload、**1440px/390px 视口无溢出且不只显示颜色**、改事实→建议克数变化、新会话+记忆诚实回归），每条附「这不证明什么」；标签由**配置驱动改为证据驱动**（`request_id` 为 null 时不得显示「真实模型/真实检索」） |
| OPS-04 | done (Day-4, plan+scripts；**镜像未构建、真实 plan/apply 未实现**) | 并行执行体(总负责人独立复核) | S0、门0不动 | **Day-4**：部署前置材料与 **fail-closed 脚本**——`deploy.ps1`/`cleanup.ps1` 缺 AWS CLI/缺 IaC 源/缺参数即 `NOT EXECUTED` + 退出码 2，绝不调用 AWS、绝不 `exit 0`；健康检查端点硬裁定（LB 与容器 HEALTHCHECK 一律 `/healthz`，`/readyz` 保持 503 不为部署改码）；修 `pyproject.toml` 与 `infrastructure.md`/`cloud-access-checklist.md` 的命令·注释级失真；实跑 `uv sync --frozen --extra bedrock --extra memory`。**镜像仅记「已静态审读、未构建」**（本机无 Docker，用户已裁定不安装） |
| BE-06 | done (Day-5, local; 云端未验证) | Backend(串行) | OPS-05（表与 IAM）、门0不变 | **Day-5**：`repo_dynamo.py` 实现 `Repository` 全协议（条件写/CAS/租约白名单/`TransactWrite` 幂等记账，单表 `pk/sk`+`entity-index` GSI）+ `dynamodb_live` marker + 离线协议集合守卫；公网三门（默认口令 aws 拒启 / 会话 TTL+idle / 登录限速 429+`Retry-After`）+ `/api/login` 429（路径仍 14）；`SCHEMA_VERSION` 3→4 + `agentcore_session_id`。**真表 12 项 `dynamodb_live` 全 skip（无凭据）→ 未云验证** |
| AI-04 | done (Day-5, local; 云端未验证) | AI(串行) | BE-06（`FeedbackRecord` 字段）、门0不变 | **Day-5**：`agentcore_client.py` 按真实 API 重写（`CreateEvent` 会话 payload+`namespaceVariables` / `GetEvent(memoryId,sessionId,actorId,eventId)` / `RetrieveMemoryRecords(namespacePath,searchCriteria)`）；`memory.py` 两段式 `get_status`→`MemoryStatusResult`；`_namespace` `/owner/<o>/pet/<p>` 与 `deploy_plan.json` 命名模板跨源守卫；`worker.py` `MemoryPoller` 接线；守卫按裁定 12 **改作用域非放宽**（`<= {worker.py}`+AST，白名单未扩）。**真实往返 5 项 skip；响应字段/状态词表未核实** |
| FE-05 | done (Day-5, local) | Frontend(串行) | BE-06、AI-04 | **Day-5**：真实态标签**证据驱动**（`storage=dynamodb`+`aws_connected`、`已提炼（真实 AgentCore 记录 N 条）` 仅当 `memory_record_count>0`）；`FeedbackView` 加非秘密 `memory_record_count`；新文案避开 e2e 禁串，`test_frontend_labels.py` 守卫**扩到新常量** `MEMORY_EXTRACTED_LABEL` + 新增「提炼标签必须与 `memory_record_count` 配对」；本地 e2e **16 passed** 未放宽。真实态标签仅 aws 态可见，**未云验证** |
| OPS-05 | done (Day-5, plan+scripts; 镜像未构建、真实 apply 未执行) | Infrastructure/Coordinator(串行) | 用户短期凭据、GitHub 私有仓 | **Day-5**：`infra/deploy_plan.json` + `scripts/deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py`（boto3 声明式编排，**不引入 CDK/CFN**）；`deploy.ps1`/`cleanup.ps1` 门控判据改为「plan 源存在 + boto3/uv 能力」，`-PlanOnly` 现为**真实离线 plan**（EXIT=0，零 AWS 调用）、`-Apply`/`-Destroy` 委派编排器（缺前提仍 `NOT EXECUTED`/exit 2）；`image.yml`（OIDC 构建推 ECR，单架构 amd64）+ `Dockerfile` 解耦 `PAWTWIN_MODE`；`.gitignore` 先行加 `deploy_state.json`。**镜像未构建、workflow 未运行（无 remote/无 Docker）、`-Apply` 未执行（无凭据/无预算确认）** |
| QA-01 | blocked: Day-5 云端证据待凭据 | 未认领 | BE-03、FE-02、AI-03、AI-02、BE-06、AI-04、OPS-05 | A01–A14、云端/本地分开的结果、评委可改输入。**Day-5 进展**：本地可判定子集由 e2e 16 + 后端 232 覆盖；「评委自由输入」量化判据依赖的 24 案例集 + `evaluate.py` **已就绪**（`scenarios.json` A01–A14 全覆盖 + 离线结构校验），但**真机跑批（G9）依赖 G7 部署**，无凭据未执行。A01–A14 的**云端部分仍待凭据** |
| SUBMIT-01 | blocked: Day-6 材料与赛事规则 | 未认领 | QA-01、**Day-5 云端证据**、实际赛事规则 | 英文材料、三分钟视频、概念图、边界声明；不自动提交。Day-5 只出部署与验收，材料整体顺延 Day-6（用户 2026-09-30 裁定） |

## 推荐派发顺序

1. BE-01 先冻结完整业务契约。它是后续并行最重要的依赖。
2. FE-01 的视觉/组件与 AI-01 的适配器设计可以并行，不能各自发明与后端不一致的接口。
3. BE-02、FE-01 联调、AI-01 工具实现分工作树推进。
4. AI-02 与 OPS-01 受账号条件影响；无账号先准备测试替身和部署计划，明确未云验证。
5. QA-01 独立检查，最后才制作参赛包装。

## 第 1 日派发（2026-09-23）

当日可执行分解见 [Day-1 开发计划](plans/PawTwin_Day1_开发计划.md)（多智能体两轮交叉校验 + 回源码二次核查后定稿）。当日主线 = 门 0 契约冻结 → BE-01/BE-02 最小集 + AI-01 适配接口/inline stub → FE-01 接真实本地 API（尽力）。必过门仅为「契约冻结 + SQLite 去重/持久化/幂等/租约 + 拒绝闭环」；正常闭环与前端联调为尽力项，真实模型调用为条件项，均不得以本地替身标为云端完成。

契约漂移裁定（由总负责人在门 0 统一落地，子 Agent 不得擅改 `models.py`/`contracts/`）：以 `models.py` 代码为权威——`EventIn.event_id:UUID`、`Receipt.command_id:UUID`（`uuid5(run_id:proposal_version)`）、`ApprovalIn.action_digest` 匹配 `^[0-9a-f]{64}$`、`Proposal.evidence_ids` 默认 `[]`；CSRF 走 `X-CSRF-Token` 头 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。

门 0 强制同步项（否则 `verify.ps1` 必红）：`tests/test_contracts.py` L10 与 L24 两处路径相等断言 + 删 L11；`tests/test_app.py` Day-1 保持 `/api/bootstrap` 语义不动、加 `/api/runs` 404 回归；`main.py` router 先于 `StaticFiles('/')` 注册；e2e 拆静态用例与业务用例（baseURL 指后端同源 `:8000`）。

并发上限（≤4，含总负责人）：常驻 Coordinator + Backend + (Frontend 或 AI)；Reviewer、OPS-01（仅计划）用空槽串行复用。

## 第 1 日完成记录（2026-09-23）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。详见 [STATUS](STATUS.md)。

- **门 0 契约冻结**：`models.py` 公开响应 DTO + 共享 `compute_action_digest`/`make_command_id`；`main.py` 业务 router 先于 `StaticFiles('/')` 注册；`contracts/openapi.json` 重生成含业务路由，`--check` 通过；基线测试同步（`test_contracts.py` 两处路径相等断言扩为业务集合并删旧否定断言；`test_app.py` 保 `/api/bootstrap` 语义、`readyz` 仍 degraded、新增 `/api/runs` 404 JSON 回归）。
- **裁定落地**：`command_id=uuid5(run_id:proposal_version)`；`action_digest=sha256(canonical_json(Action))` 匹配 `^[0-9a-f]{64}$`；CSRF 同步令牌 + `SameSite=Lax`，本地 HTTP 仅省 `Secure`。**新增裁定**：`RunView` 暴露 `proposal_version/action_digest`（审批防篡改须由客户端回显，否则冻结的 `ApprovalIn` 无法构造）；`owner_id/attempt_count/lease_*` 仍不入响应。
- **本地检查**：`pytest` 71 通过（二次检查补强 2 条审批安全测试）、`ruff` 无告警、契约 current、`typecheck`/`build` 通过、浏览器 e2e 3 通过（拒绝闭环 reload 仍「已拒绝」、零执行）、`verify.ps1` 全绿。
- **环境修复**：重建工作区 `.venv`（复制来的 `pytest.exe` 启动器指向旧源码树，致 pytest 导入旧 `pawtwin`）。
- **边界**：真实 Bedrock/AgentCore/DynamoDB 真表/跨进程双批准/真实重启/部署**未验证**，不以 SQLite 或本地替身冒充云端完成。
- **提交**：已按逻辑分组提交到 `chore/bootstrap`（用户授权，未推送远程）；**冻结提交 ID = `94216df`**；后续 `f2927cb`(后端测试)/`e20336d`(AI)/`f45edb8`(前端)/本提交(OPS+文档)。

## 第 2 日派发（2026-09-24）

当日可执行分解见 [Day-2 开发计划](plans/PawTwin_Day2_开发计划.md)（三视角智能体交叉校验 + 回源码二次核查后定稿，含 25 条技术裁定）。基线：`dc8dc10`，71 项 pytest + 3 项 e2e 绿，工作区干净。

**前提**：用户确认**仍无 AWS 账号** → 双轨：必过门（G0–G11）全部本地可验证，真实 Bedrock 往返与「云模型参与正常/重复喂食场景」为**条件项**，不以本地替身或离线 stub 冒充云端完成。范围取「全量」，估算 ≈ 24h 串行工时（不含 strands 实装）。

**当日主线** = 门 0 契约/配置冻结（C1）→ Backend 并发原语+迁移 ‖ AI 适配器+遥测 → worker+demo 端点 → `main.py` 装配（C3）→ Frontend 证据面板/演示控制/approve e2e → 依赖与脚本（C2）→ 集成与文档（C4）→ 非作者独立审查。

**必须先落定的高危裁定**（详见计划 §1，不改会造成二次出粮、假红或对评委失真）：

1. `claim_run` 改**可领取白名单**（仅 `queued`/`analyzing`）。现谓词只排除 5 个终态，`EXECUTING` 可被重领 → 抹掉已有回执 + `proposal_version` 变化 → 派生**新 `command_id`** → **第二次记账**，击穿 A01/A04 与任务单「重试不能更换 command_id」。
2. 新增 `transition_run` **CAS**：批准必须先 `AWAITING_APPROVAL→EXECUTING` 成功才执行，否则并发双批准会调两次 `device.execute`。
3. 证据校验用 **pinned 快照 + 追加式台账**，禁用 `available_evidence_ids()`（它重查库，分析期间 `facts_version` 被 bump 即产生假 `UNKNOWN_EVIDENCE`；且策略读旧快照、建议读新快照会 fail-open）。
4. `_inline_proposal` 的 `evidence_ids=["pet_facts"]` **不是合法 id**，必改（否则无条件强制校验会让 18 项测试全红）；`inline` 保留为测试专用后端以继续满足 Day-1「拒绝闭环不依赖 AI 替身」裁定。
5. A03 重评估拆为 `_reevaluate_under_new_facts`，**不调模型**（现在跑在 HTTP 请求线程内，接真模型后每次 stale approval 都是一次未预算、不受 45s/≤4 次保护的付费调用）。
6. `FactsView` 两字段改可空 + 删 `_facts_view` 的 `or 0`：否则事实未知时页面显示「上次喂食距今 0 分钟」而策略判 `MISSING_FACTS`，**对评委失真**；A09 也因此经 API 不可达（现零测试覆盖）。
7. schema **幂等迁移**（`PRAGMA user_version` + `ALTER TABLE ADD COLUMN`）+ `.gitignore` 补 `*.db`：现建表用 `IF NOT EXISTS` 且无迁移，新增列对持久库会崩，而测试全用 `:memory:` 永远发现不了。
8. `worker_mode` **默认 inline**，background 由 e2e `webServer.env` 与独立 fixture 显式开启；否则 `test_decline_loop.py` L30/L33-35/L64-66 必红。
9. `readyz`/`bootstrap` 上调为**分组件诚实**（reason 改 `cloud_adapters_not_verified`、capabilities 改 `implemented_local`/`implemented_simulated`/`not_implemented`），`test_app.py` L13-18/L31-42 **精确更新而非放宽**——履行 Day-1 审查 nit 5 的「正常闭环后再上调」处置；业务已实现却续报「业务未就绪」属**低报失真**。
10. strands 实装设**硬门**：先单独提交 `bedrock` optional extra + `uv.lock` 并验证 `uv sync --frozen --extra bedrock`；失败则 Day-2 完全不动依赖/CI/Dockerfile，仅保留接口 + 延迟导入 + 依赖缺失映射为显式 `FAILED`。

**所有权补裁（本日起生效）**：`AGENTS.md` L26-33 两份表**均未列** `main.py`/`config.py`/`Dockerfile`（Day-1 事实上归总负责人）→ 裁定由 **Coordinator 串行独占**；`repository.py`/`api.py`/`repo_sqlite.py`/`workflow.py`/`worker.py`/`device_sim.py` 属 **Backend**（不得划给 Coordinator）；`Proposer` 协议住 `workflow.py`（Backend）而适配器住 `agent.py`（AI），故 **seam 签名必须由 Coordinator 在门 0 冻结**。

**不可并行的临界段**：C1=`models.py`+`config.py`+`contracts/`+契约测试+seam 签名；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`；C3=`main.py` 装配（也是契约导出入口）；C4=`STATUS`+`TASKBOARD`+`evidence`。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；Reviewer、OPS 用空槽串行复用。**Reviewer 不得由作者充当**。单机串行时「并行」= 不重叠文件批次，必须按下方格式追加认领记录。

## 第 2 日完成记录（2026-09-25）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（用户已确认此方式；逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。临界段按 C1（契约/配置）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）顺序串行通过。详见 [STATUS](STATUS.md) 与 [day2-handoff](evidence/day2-handoff.md)。

- **门 0（C1）**：`models.py` 新增 `EvidenceItem`/`AnalysisTelemetry`/`AnalysisOutcome`/`ErrorResponse`/`DemoFactsIn`/`DemoDeviceModeIn`/`DemoAck`，`RunView` 增 `evidence`/`telemetry`/`policy_reason`/`failure_reason`，`FactsView` 两字段改可空，`StateView` 增 `analyzer`/`storage`/`memory`/`device_mode`；`config.py` 增 10 项 settings 与交叉校验；seam 签名冻结为 `analyze_event(event, snapshot, owner_id, *, model_calls_used=0) -> AnalysisOutcome`（**不传 `RunRecord`**）；openapi 重生成至 **11 条路径**并补 401/403/404/409/422；`test_contracts.py` 的 `$defs` 断言由 `<=` **收紧为 `==`**；`test_app.py` 的 readyz/bootstrap **精确上调**（未放宽）。
- **裁定落地**：25 条全部落地，其中高危项均已测试固化：claim 白名单（穷举 11 个状态）、批准 CAS（双线程并发只执行一次）、pinned 快照 + 台账校验、A03 零模型调用（telemetry/evidence 逐项相等）、持久化调用预算（第 5 次被拒）、schema 幂等迁移（旧文件库回归）、`worker_mode` 默认 inline、`readyz`/`bootstrap` 分组件诚实。
- **本地检查**：`pytest` **139 passed, 4 skipped**（基线 71 → 新增 68；4 skipped 为 `bedrock_live` 具名 blocked）、`ruff` 无告警、契约 current、`uv lock --check` 与 `uv sync --frozen --extra bedrock` 均成功、`typecheck`/`build` 通过、浏览器 e2e **7 passed**（`workers: 1`、background、local_fake）、`verify.ps1` 全绿。
- **独立审查**：非作者只读审查结论 **PASS-WITH-NITS**（15 项核实 14✅/1⚠），1 个重要缺陷 + 6 个 nit；重要缺陷（替身将 NULL 伪造成 0）5 个 nit 已修并复测，第 6 个（worker 顺序 drain 使准入上限无生产触发路径）已接受并在 STATUS 诚实披露。见 [reviews/day2.md](reviews/day2.md)。
- **边界**：真实 Bedrock/AgentCore/DynamoDB 真表/跨进程双批准/真实 OS 重启/部署与镜像构建**未验证**，不以 SQLite、本地替身或离线 stub 冒充云端完成；`bedrock-smoke.ps1` 实测输出 `NOT EXECUTED` 且退出码 2。
- **提交**：**尚未提交**，等待用户授权；建议分六组（门0冻结 / 后端 / AI / 前端+e2e / OPS / 文档），提交后回填 **Day-2 契约冻结提交 ID**。Day-1 冻结 ID `94216df` 保留为历史冻结点。无秘密入库、无云资源、**无费用**、无远程推送、**无镜像构建**。

## 第 3 日派发（2026-09-26）

当日可执行分解见 [Day-3 开发计划](plans/PawTwin_Day3_开发计划.md)（三视角交叉校验 + 回源码二次核查后定稿，含 14 条技术裁定）。基线：`dc8dc10`（Day-1），**Day-2 改动全部未提交**（38 modified + 14 untracked），144 项 pytest + 7 项 e2e 绿。

**前提**：用户确认**仍无 AWS 账号** → 双轨：必过门（G0–G10）全部本地可验证，AgentCore 真实提炼/检索与场景 C 真实记忆影响为**条件项**，不以本地替身或 stub 冒充「已检索记忆」。范围**按五日计划原样**；T6 的 24 案例集 + `evaluate.py` 顺延 Day-4。

**当日主线** = 门 0 契约/配置冻结（C1，含记忆 seam）→ Backend 反馈持久化 ‖ AI `memory.py`+检索接线 → worker 真并发 → 跨进程双批准/真实进程重启 → `main.py` 装配（C3）→ Frontend 记忆区/反馈/新会话 e2e → memory extra 与脚本（C2，硬门）→ 集成与文档（C4）→ 非作者独立审查。

**必须先落定的高危裁定**（详见计划 §1）：

1. `memory_status` 诚实语义：无账号时反馈恒 `saved`（原文已存业务库），**绝不** `processing`/`available`（本地无提炼任务）；`available` 仅在真实 AgentCore 检索证据出现时（AGENTS.md L18）。`FeedbackView` 携 `memory_backend` 标签使 `saved` 不被读成「已提炼」。
2. `search_owner_memory` 接线 `MemoryService`：本地返回 `[]` 且**不记** memory 证据（不伪造）；stub/真实服务返回记录时才出 `source="memory"` 证据、proposal 可引用。场景 C「记忆改变建议」= 条件项。
3. worker 由**顺序 drain** 改**有界线程池**（池=`max_concurrent_global`）：先准入后 claim、per-task worker_id；**闭合 Day-2 nit#6**（准入上限获得生产触发路径），且 CAS/白名单/租约在真并行下继续成立。
4. 跨进程双批准 = **两个 `SqliteRepository` 指向同一文件库**（WAL + busy_timeout），断言 **DB 不变式**（非共享 device 计数器）。诚实边界：SQLite 两连接 **≠** DynamoDB 多副本（Day-4）。
5. 真实 OS 进程重启：**必过** = 文件库两实例逻辑重启（含 `ANALYZING`+活租约不二次分析）；**尽力** = subprocess kill/relaunch 真重启（marker `restart`）。
6. 会话仍进程内存（裁定 6 顺延 DB 持久化）：重启后重登录，作为诚实边界披露；`conversation_id` 存 owner 级进程内映射，重启复位。
7. memory extra 设**硬门**：先单独提交 `uv add --optional memory` + `uv lock` 并验证 `uv sync --frozen --extra memory`；失败则 Day-3 完全不动 `pyproject/uv.lock/Dockerfile/CI`，仅保留 `MemoryService` 接口 + 延迟导入 + 缺依赖/凭据映射为 `not_implemented`（绝不伪造）。

**所有权**（沿用 Day-2 补裁）：`memory.py` = AI；`repository.py`/`repo_sqlite.py`/`worker.py`/`api.py` = Backend；`models.py`/`config.py`/`contracts/`/`main.py` = Coordinator；`frontend/src/` = Frontend；`pyproject/uv.lock/Dockerfile/ci.yml/preflight/smoke` = OPS/Coordinator。`MemoryService` 协议 + `AgentContext` 注入 seam + `FeedbackRecord` **由 Coordinator 在门 0 冻结**。

**不可并行的临界段**：C1=`models.py`+`config.py`+`contracts/`+契约测试+记忆 seam；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`；C3=`main.py` 装配；C4=`STATUS`+`TASKBOARD`+`evidence`。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；Reviewer、OPS 用空槽串行复用。**Reviewer 不得由作者充当**。

## 第 3 日完成记录（2026-09-26）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（用户已确认此方式；逻辑上遵守文件所有权与不重叠写入），未拉起并行工作树。临界段按 C1（契约/配置/记忆 seam）→ C2（依赖/CI/镜像）→ C3（`main.py` 装配）→ C4（文档）顺序串行通过。详见 [STATUS](STATUS.md) 与 [day3-handoff](evidence/day3-handoff.md)。

- **门 0（C1）**：`models.py` 新增 `MemoryStatus`/`MemoryBackend`/`FeedbackScope`/`FeedbackView`/`NewSessionView`，`StateView` 增 `conversation_id`/`feedback`；`config.py` 增 `memory_backend` 与交叉校验；书面冻结 `MemoryService` seam（`submit_feedback`/`get_status`/`search`）与 `FeedbackRecord`；openapi 重生成至 **14 条路径**并补 401/403/404/422；`domain.schema.json` 仍**恰为** 6 输入模型 + `RunState`（`==` 断言）；`test_contracts.py` 的 `ACTIVE_PATHS` +3 并改写旧注释。
- **裁定落地**：14 条全部落地，高危项均已测试固化：`memory_status` 本地恒 `saved`（绝不 `available`）、`search_owner_memory` 本地返回 `[]` 不伪造证据、stub 记忆→`source="memory"` 可引用证据、worker 有界线程池真并发（`peak_concurrency` 断言、闭合 nit#6）、跨进程（两连接）双批准 DB 不变式、文件库逻辑重启 + subprocess 真进程重启（`ANALYZING`+活租约不二次分析）、会话仍进程内存（裁定 6）。
- **本地检查**：`pytest` **184 passed, 11 skipped**（审查后 +2 回归；多次运行一致；11 skip 均具名 = 5 agentcore_live + 4 bedrock_live + 1 bedrock_offline + 1 restart 尽力项）、`ruff` 无告警、契约 current（14 路径）、`uv lock --check` 与 `uv sync --frozen --extra memory` 均成功（`boto3==1.43.102`，无新增下载）、`typecheck`/`build` 通过、浏览器 e2e **10 passed**、`verify.ps1` 全绿。
- **独立审查**：非作者只读审查结论 **PASS-WITH-NITS**（8 项高信号逐条核实全 ✅），3 个 nit（worker 关闭期准入槽泄漏、`post_feedback` 未归约 `MemoryUnavailable`、缺 v2→v3 迁移回归测试）均已修并复跑。见 [reviews/day3.md](reviews/day3.md)。
- **边界**：真实 AgentCore 提炼/检索、场景 C 真实记忆影响、DynamoDB 真表/跨副本、真实 OS 进程被 kill 于 ANALYZING、部署与镜像构建**未验证**，不以 SQLite/两连接/本地替身/stub 冒充云端完成；`agentcore-smoke.ps1` 实测输出 `NOT EXECUTED` 且退出码 2。
- **提交**：**尚未提交**（Day-2 与 Day-3 改动共处同一脏工作区），等待用户授权；建议分六组（门0冻结 / 后端 / AI / 前端+e2e / OPS / 文档），提交后回填 **Day-3 契约冻结提交 ID**。Day-1 冻结 ID `94216df` 保留为历史冻结点。无秘密入库、无云资源、**无费用**、无远程推送、**无镜像构建**。

## 第 4 日派发（2026-09-28）

当日可执行分解见 [Day-4 开发计划](plans/PawTwin_Day4_开发计划.md)（三视角交叉校验 + 存疑项源码核验 + 总负责人回源码仲裁后定稿，含 14 条技术裁定与 F1–F15 实测事实表）。基线：`dc8dc10`（Day-1 末），**Day-2 与 Day-3 改动全部未提交**，实测 **39 modified + 31 untracked**（Day-3 计划记的 38+14 已过时）；`.gitignore` 覆盖完整、无秘密、无 remote。

**前提（用户 2026-09-28 确认）**：①**仍无 AWS 账号，但用户即刻注册** → 双轨继续，真实云为条件项，账号就绪日按 Day-4 计划 §7.5 手顺执行；②**开工前先分组提交 Day-2/Day-3**（S0，逐组需用户在场授权）；③范围**只取 T7 + 独立审查 + 浏览器验收 + 针对失败修复**，**不含** T6 的 24 案例集与 `evaluate.py`、`repo_dynamo`、会话 DB 持久化与登录限速；④**不安装 Docker** → 镜像完全不可解锁构建验证，只记「已静态审读、未构建」。

**当日主线** = S0 基线入库（C0）→ G1 干净树全量回归实测 → G2 访问控制补口 ‖ G3 健康检查端点硬裁定 → G4 `deploy.ps1`/`cleanup.ps1` fail-closed 门控脚本 → G5 镜像静态审读 + `pyproject.toml` 假陈述修正 + 合并 extra 实测 → G7 标签证据驱动 + `available` 反伪造守卫 → G6 浏览器验收矩阵（6 条新 e2e）→ G9 文档四件套与上报 → G8 非作者独立审查。合计 ≈ **20–23h 串行工时**（= 全量 Day-4 减去一切云端项）。

**必须先向上报的事实（不得拆成半通过）**：总方案 L103 的第 4 日字面验收「HTTPS 演示可访问；可部署可删除」经实测存在**四重独立阻断**——本机无 Docker/AWS CLI/CDK（F1）、`infra/` 无任何 IaC 源且 `deploy`/`cleanup` 脚本不存在（F5）、`create_app` 对 `mode==aws` 无条件拒启（F6，且这是**正确设计不是 bug**，禁止为了 demo 而移除）、无证书与公网地址。按总方案 L106/L153：**云端里程碑整体顺延并上报，当日产物不得标为参赛完成**。

**必须先落定的高危裁定**（详见计划 §1）：

1. **只回填一个真实存在的契约冻结提交 ID**：实测 `94216df` 与 HEAD 的 `openapi.json` 均为 **9 条路径**、工作区为 14 条 → **Day-2 的 11 路径冻结点从未入库**。禁止为凑两个 ID 手改生成文件；须在 `STATUS.md`/本表**书面披露**该事实，并声明中间提交不逐个复验（`models.py`/`api.py`/`contracts/` 终态互依赖）。
2. **`.gitignore`（含 `*.db`）+ `pyproject`/`uv.lock` 为第一组**：HEAD 的 `.gitignore` 实测**不含 `*.db`**，否则单独 checkout 跑重启类测试即产生未忽略的库文件、工作区变脏。
3. **cookie `Secure` 与 `mode` 解耦**：现判据为 `mode == "aws"`（`api.py:187`）而镜像烤死 `PAWTWIN_MODE=local` → 部署到 HTTPS 后 **cookie 不带 Secure**。改为按请求 scheme 判定；本地无证书仍不得声称「HTTPS 会话安全已达标」。
4. **健康检查端点硬裁定**：`/readyz` 无分支硬编码 **503**（`main.py:125-138`），若 ALB/target group 指它则任务**永不健康**且表象会被误读为镜像问题 → 一律用 `/healthz`，`/readyz` 保持 503 且**严禁**为部署而改码。
5. **`deploy.ps1`/`cleanup.ps1` 的诚实形态 = fail-closed 门控脚本**：检查顺序固定为 CLI 存在性 → IaC 源存在性 → 必填参数；缺任何一项即 `NOT EXECUTED` + **退出码 2**，绝不调用 AWS、绝不 `exit 0`；`-PlanOnly` 保留任务单命名但 `.SYNOPSIS` 须钉死「无 CLI 时不产出任何 plan」；account id 仅运行期注入、**绝不预填**。（与 `preflight.ps1` 的退出码语义分级：环境自检无凭据仍 exit 0，**计费/资源类才 fail-closed**）
6. **前端标签改为证据驱动**：`App.tsx:48-52/475-477` 的「AWS Bedrock（真实模型）」「AgentCore（真实检索）」当前**由配置推导**；而 `MemoryService.get_status` 生产端**零调用者**、`agentcore_client.py:151-152` 的 `return "available"` 为**不可达代码** → 措辞必须写「接口已就位、生命周期**未接线**」（既非「已实现待验证」也非「完全未实现」），并新增**反伪造守卫测试**：本地配置下不得存在任何能把 `memory_status` 写成 `available`/`processing` 的路径。
7. **登录限速 / 会话 TTL / 默认口令 = 公网部署前置硬门**：三者实测**零实现**（`Session.created_at` 无消费者、口令 `local-demo-passphrase` 随源码公开），且会话为进程内 `dict` + cookie 值即 `session_id` 明文 → **多副本必致 401**、`AdmissionControl` 仅进程内计数 → 滚动两副本实际全站并发 = 副本数 × 2。本轮**不实现**，只出书面裁定议题。

**上报的依赖冲突（不得静默吸收）**：① T6 的 24 案例集与 `evaluate.py` 被用户排除在 Day-4 外，而 **Day-5 的「测试与评委自由输入」判据与它同源**（总方案 L138、任务单 L315-317）→ 不补做则 Day-5 该项只能降级为「人工现场脚本、无固定案例集量化报告」；② Day-5 字面已含材料全套（冻结功能 + 概念图 + 演示脚本 + 英文材料 + 录屏），**被顺延的云端块压不进同一天**；③ 无 AWS 验证时，Day-5 产物必须写作「**本地验证候选（非参赛版）**」（总方案 L153）。

**所有权**（沿用 Day-2 补裁）：`api.py`/`auth.py` = Backend；`frontend/src/`+`frontend/e2e/` = Frontend；`scripts/*.ps1`/`infra/` = OPS/Coordinator；`main.py`/`config.py`/`contracts/`/`Dockerfile`/`STATUS`/`TASKBOARD` = Coordinator；Reviewer **不得由作者充当**。

**不可并行的临界段**：C1=`api.py`+`auth.py`+`tests/test_auth.py`（G2 与 G7 共享 `api.py`）；C2=`pyproject.toml`+`uv.lock`+`Dockerfile`+`ci.yml`+`scripts/*`；C3=`frontend/src/App.tsx`+`frontend/e2e/*`；C4=`STATUS`+`TASKBOARD`+`evidence`。**门 0 不动**：Day-4 应保持 OpenAPI 恰 14 条路径、`domain.schema.json` 的 `$defs` 恰为 6 输入模型 + `RunState`；若某项改动触发契约变化，回门 0 重议，**不得**放宽 `test_contracts.py` 的 `==` 断言。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + Frontend；OPS、Reviewer 用空槽串行复用。单机串行时「并行」= 不重叠文件批次，需按下节格式追加认领记录。新增任务行：`BE-05`、`FE-04`、`OPS-04`（均 `ready`）。

## 第 4 日完成记录（2026-09-29）

实际以**单一开发环境、两个执行体按不重叠文件批次并行**完成（并行执行体承担 G4/G5/G6/G7 的编码与提交，总负责人承担 S0/G1/G2/G3/G9）；总负责人**未采信**对方绿灯，对其提交后的 HEAD 独立重跑全部检查，并修复 2 处问题（`ruff I001` 会使 `verify.ps1` 直接中断；冗余导入别名 `_MU` 遮蔽模块级导入）。详见 [STATUS](STATUS.md) 与 [day4-handoff](evidence/day4-handoff.md)。

- **S0 基线入库（G0）**：Day-2 与 Day-3 全量改动按 `S0-a…S0-g` 七组入库（`56be355`→`b1f508a`），`.gitignore`（含 `*.db`）+ `pyproject`/`uv.lock` 为先行组。**只回填一个合并契约冻结 ID = `590aa5a`**，并书面披露：实测 `94216df` 与 `dc8dc10` 的 `openapi.json` 均为 **9 条路径**，故 Day-2 的「11 路径冻结点」**从未入库**，且契约为生成物不可手改 → 无法分离为两个快照；中间提交不逐个复验，只在最终 HEAD 声明全绿。
- **G1 干净树回归**：`pytest -o addopts=""` **192 passed, 10 skipped**（均具名）、默认 addopts **192 passed/1 skipped/9 deselected**、`ruff` 无告警、契约 current（仍 **14 路径**，`domain.schema.json` 未变）、`uv lock --check` exit 0、`verify.ps1` EXIT=0。skip 由 11 变 10 的原因已书面说明（本轮装了合并 extra，`test_bedrock_adapter_offline` 改为真实执行；CI 不装 extra 故仍 skip）。
- **G2 访问控制（BE-05）**：cookie `Secure` 由 `mode == "aws"`（部署形态下**永假**）改为按请求 scheme；`X-Forwarded-Proto` 仅在 `PAWTWIN_TRUST_PROXY_HEADERS=true`（默认关，G8 第二轮改正）时采信且只能加不能减；补齐 approval 的 401/403 与 logout 的 401（该路由此前**零鉴权断言**）；**负向验证**已做（回退后转红）。**A12 不记通过**：登录限速、会话 TTL、默认口令公网暴露三项仍未闭合（裁定 14 议题待用户定）。
- **G3 健康检查硬裁定**：LB/target group 与容器 `HEALTHCHECK` 一律 `/healthz`；`/readyz` 恒 503 仅作诊断，**不为部署改码**（`test_app.py` 精确断言未放宽）。
- **G4/G5 部署前置材料（OPS-04）**：`deploy.ps1`/`cleanup.ps1` 为 fail-closed 门控（CLI → IaC 源 → 必填参数 → 授权令牌），实测均 `NOT EXECUTED` + **退出码 2**、零 AWS 调用、无 `exit 0` 路径；`uv sync --frozen --extra bedrock --extra memory` exit 0；修正三处文档假陈述（`pyproject` 的 extra 描述、checklist 不存在的 `-Mode aws`、`infrastructure.md` 的退出码笼统要求）。**镜像仍未构建**（本机无 Docker，用户已裁定不装）。
- **G6/G7 浏览器验收与标签诚实（FE-04）**：新增 `acceptance.spec.ts` 6 条（未登录 401 JSON、`unknown` 回执不显示成功且不记账、待批准 reload、**1440px/390px 无溢出且状态不只靠颜色**、改事实→克数变化、新会话+记忆诚实），e2e **10 → 16 全绿**；标签改为**证据驱动**（无 `request_id`/无真实记忆证据不得称「真实」）；`available` 反伪造守卫 4 条（含静态字面量守卫）。首次引入视口断言即暴露并修复 **390px 横向溢出 6px** 的真实缺陷（改 `styles.css`，**未放宽断言**）。
- **G8 非作者独立审查（共两轮）**：第一轮 ✅ PASS（CodeReview 子代理，范围 `b1f508a..63f3de6`，10 项核实全 ✅，零发现；总负责人另对「零发现」作 3 项独立复核均成立）。第二轮（覆盖 `c4ae5f8..63f3de6` 全部 Day-4 本地提交）**PASS-WITH-NITS：0 阻断 / 4 重要 / 8 nit**，第一轮的「无 important」在更大覆盖面下不成立；4 重要已全部修复（`a575a61`）：①代理头改受信开关（回归裁定 5/预案 A）②标签含 e2e 禁串→重写+新增 `test_frontend_labels.py` 2 项耦合守卫③文档高报「干跑全部路径」→更正为「均停 Gate 1，Gate 2–4 仅代码审读」④样式注释失真→改正；nit 落地含静态守卫盲区声明、`get_status` 未接线不变式断言、「真实模型」与 backend 相与、字符串耦合拆分。复跑 **195 passed/10 skipped** + e2e 16 + verify 全绿。教训：**同视角复核不能替代覆盖面更广的第二轮审查**。见 [reviews/day4.md](reviews/day4.md) §7。
- **G9 文档**：`STATUS.md` 新增 Day-4 三档表 + 本地/云端双列 + 提交表；`evidence/day4-handoff.md`（12 项）、`day4-local.md`（含「这不证明什么」）、`day4-cloud-blocked.md`（N1–N10 逐条阻断与解锁前提）；Day-1/2/3 历史文档**只追加后记**（已就冻结 ID 预期不可达成一事分别追记）。
- **字面验收上报**：总方案 L103 的第 4 日验收「HTTPS 演示可访问；可部署可删除」因**四重独立阻断**整体不可达成，已按 L106/L153 上报顺延；**无 AWS 验证时 Day-5 产物须命名「本地验证候选（非参赛版）」**。未选的 T6 案例集与 Day-5「评委自由输入」验收同源，冲突已上报待用户二选一。
- **提交**：`c4ae5f8`(G2) → `a37c161`(G4/G5) → `94442b5`(G7 标签+390px) → `f3b96e4`(G7 守卫+FE-04 e2e) → `63f3de6`(G9 文档) → `aaaddd3`(G8 第一轮回填) → `a575a61`(G8 第二轮补修) → `ebe3e11`(移出误入库审查临时产物)。**仍未推送远程**（无 remote，需授权）。无秘密入库、无云资源、**无费用**、**无镜像构建**。
- **云端切片前置（2026-09-29 晚）**：用户确认账号注册中、**凭据尚未就绪**且今日不执行计费调用；本机已装 **AWS CLI v1.46.1**（pip --user，不入仓库），deploy/cleanup 实测改停 `cdk` 缺失门（仍 exit 2）；§7.5 手顺停在「凭据注入」一步，待账号就绪后续执行。

## 第 5 日派发（2026-09-30，真实部署专日）

当日可执行分解见 [Day-5 开发计划](plans/PawTwin_Day5_开发计划.md)（规划阶段已用真实账号前置条件下的命令与内省核实环境，含 19 条技术裁定与 G-A…G-Q 实测事实表）。基线：`chore/bootstrap` HEAD=`9354804`，**工作树干净**，无 remote；实测 pytest **195 passed / 10 具名 skip**、e2e **16 passed**、契约 **14 条路径 current**、`verify.ps1` EXIT=0。

**前提（用户 2026-09-30 确认六点）**：①**AWS 账号与凭据已就绪**，由用户本机注入**短期**凭据（不入聊天、`.env`、仓库、镜像层）；②镜像**由 GitHub Actions 远程构建并推送 ECR**，CI 取云权限走 **OIDC 角色**；③**部署深度 = 完整真实部署**（`repo_dynamo` → 移除 `mode=aws` 拒启 → 真实 Bedrock + 真实 AgentCore → ECS Express Mode HTTPS 演示地址）；④**T6 的 24 案例集 + `evaluate.py` 补做并在真实模型上跑**；⑤**Day-5 专做真实部署，参赛材料整体顺延 Day-6**；⑥**公网安全三门全做**（默认口令拒启 / 会话 TTL / 登录限速）。

**双轨策略自本日起终止**：账号就绪后真实推理、真实 DynamoDB、真实 AgentCore 即为唯一交付证据；`local_fake`/`StubMemoryService`/SQLite 只保留为离线测试后端，不得再充当任何验收凭据。

**当日主线** = P0 只读就绪门与用户节点 → G1 基线复跑 → D1/D1' `repo_dynamo` 实现与**真表**全套验证 → D2 公网三门 + 429 契约重生成 → D3 AgentCore 数据面真实化 + 轮询接线 + `SCHEMA_VERSION` 4 → D4 `deploy_plan.json` + boto3 编排器 + OIDC/IAM → D5 CI 真实构建推 ECR → D6 云装配 + 前端真实态标签 → `deploy.ps1 -Apply`（**前置：费用实测 + 用户书面预算确认**）→ G8 部署面 A01–A14 真实子集 → D7 24 案例集真机跑批 → D8 证据文档 → G11 非作者独立审查。合计 ≈ **28–33h**，**超出一日**，执行承接至 Day-6 上午。

**必须先向上报的事实（不得拆成半通过）**

1. **五日变六日**：总方案 L104 的 Day-5 字面同时要求「冻结功能 + 评委自由输入 + 概念素材 + 演示脚本 + 英文材料 + 录屏」，本轮又承接 Day-4 顺延的**全部**云端块。据用户裁定⑤，**材料整体顺延 Day-6**，因此总方案第 6 节实际执行变为六个工作日。
2. **Day-3 的 AgentCore 客户端不能直接跑起来**：`agentcore_client.py:128/144/164` 调的 `create_event(namespace=…)` / `list_events(memoryId=…)` / `search_memory(…)` 在真实 API 中**不存在或参数不足**（真实为 `GetEvent(memoryId,sessionId,actorId,eventId)` 与 `RetrieveMemoryRecords(memoryId,namespacePath,searchCriteria.searchQuery)`）。它现被 fail-closed 吞成 `MemoryUnavailable` 因此本地全绿——**这是假绿风险面，不是「代码已就绪」**。Day-5 必须先重写再接线。
3. **守卫会主动拒绝接线**：`tests/test_feedback_api.py:347` 断言 `get_status` 生产调用者 `== []`、`:310` 静态字面量白名单不含 `worker.py`。接线需按 Day-5 裁定 12 **改作用域并书面记录 re-ruling**，**禁止静默放宽**；白名单不扩（状态映射留在 `agentcore_client.py`/`memory.py`）。
4. **本轮不再是零副作用交付**：会创建真实云资源并产生计费。DoD 口径从「无资源/无费用」改为「精确披露资源清单、区域、预计与真实费用、删除计划」；`AGENTS.md` L69 的预算确认是 `-Apply` 硬门。
5. **环境事实**：本机仍**无 Docker**、WSL 无发行版、`cdk` 未装、`gh` 未装（→ GitHub 仓库只能由用户创建）；`aws-cli` 1.46.1 为 v1（**无 `--cli-dry-run`**）且在当前进程 PATH 不可见 → 编排逻辑走锁内 boto3（实测含 Express 四个操作，**无 Monitor 操作**，需轮询 `DescribeExpressGatewayService`）。
6. **正向事实（降低风险）**：`repo_dynamo` 复用 `memory` extra 已锁定的 `boto3==1.43.102` → **Day-5 不新增依赖、不动 `uv.lock`**；`StateView.storage` 枚举已含 `dynamodb` → 切真实适配器**不需改契约枚举**（路径仍 14 条）。

**必须先落定的高危裁定**（详见计划 §1，共 19 条；承重的 7 条）：①部署编排用 **boto3 声明式编排器**，不引入 CDK/CFN，且 `deploy.ps1` 的 Gate 1/Gate 2 判据必须同步改掉（否则过了假门）；②区域与模型**不预填**，只读探测后由用户确认；③`repo_dynamo` 的原子性等价性基准是 SQLite（`create_or_get_run` 用 TransactWrite[Get+Put]、`record_receipt_once` 用 TransactWrite[Put+Update]、时间统一 ISO8601 字符串）；④真表验证用新 marker `dynamodb_live`，**不引入 moto**；⑤`mode=aws` 启动只做**零计费探活**（DynamoDB/AgentCore），Bedrock 以真实 `request_id` 为证据；⑥`/readyz` 由恒 503 改为按真实探活上调（**LB 与 HEALTHCHECK 仍一律 `/healthz`**，对 Day-4 裁定 7 的书面修订）；⑦副本固定 **1×1**（会话/限速/并发上限均进程内），跨副本不作必过项。

**所有权**（沿用 `AGENTS.md:26-33` 与 Day-2 补裁）：`repo_dynamo.py`(新)/`repo_sqlite.py`/`repository.py`/`auth.py`/`api.py`/`worker.py` = Backend；`agentcore_client.py`/`memory.py`/`bedrock_client.py`/`agent.py` = AI；`models.py`/`config.py`/`contracts/`/`main.py`/`pyproject.toml`/`STATUS`/`TASKBOARD` = Coordinator；`frontend/src/`+`frontend/e2e/` = Frontend；`infra/`/`Dockerfile`/`scripts/*`/`.github/workflows/*` = Infrastructure；**Reviewer 不得由作者充当**（`docs/agents/reviewer.md:10`）。

**不可并行的临界段**：C1=`repository.py`+`repo_sqlite.py`+`repo_dynamo.py`+仓储/恢复测试；C2=`models.py`+`config.py`+`contracts/`+`test_contracts.py`+`conftest.py`；C3=`api.py`+`auth.py`+`test_auth.py`；C4=`agentcore_client.py`+`memory.py`+`worker.py`+`test_feedback_api.py`（**禁止先接线后改守卫**）；C5=`infra/`+`scripts/*`+`Dockerfile`+`workflows/*`（`.gitignore` 的 `infra/deploy_state.json` 必须先于该文件出现）；C6=`frontend/src/*`+`frontend/e2e/*`+`test_frontend_labels.py`；C7=`STATUS`+`TASKBOARD`+`evidence`。**门 0 原则**：路径仍恰 14 条、`domain.schema.json` 仍恰 6 输入模型 + `RunState`；`/api/login` 只增 429 响应，**不得**放宽 `test_contracts.py` 的 `==` 断言。

**并发上限**（≤4，含总负责人）：Coordinator + Backend + AI + Frontend；OPS、Reviewer 空槽串行复用。单机串行时「并行」= 不重叠文件批次，需按下节格式追加认领记录。新增任务行：`BE-06`、`AI-04`、`FE-05`、`OPS-05`（均 `ready`）；`QA-01` 转 `ready`，`SUBMIT-01` 依赖改指 Day-6。

## 第 5 日完成记录（2026-09-30，离线实现切片）

实际以**单一开发环境、总负责人 Agent 串行**完成各角色工作（逻辑上遵守文件所有权与不重叠写入）。**前提变化**：Day-5 定位为真实部署专日，但实测 **AWS 凭据仍缺失**（事实 G-A：无 `~/.aws/*`、无 `AWS_*` 环境变量、`sts` 报 `Unable to locate credentials`）。经 AskUserQuestion 取得用户裁定「**先做全部离线实现**」，遂完成计划中一切**不需凭据**的代码与离线测试（提交序列 D1–D8 的编码部分），真实云门用 marker 具名 skip。详见 [STATUS](STATUS.md) Day-5 段与 [day5-handoff](evidence/day5-handoff.md)。

- **本地全绿实测**：`verify.ps1` EXIT=0；pytest 默认 addopts **232 passed, 1 skipped, 21 deselected**（收集 live marker 时 **232 passed, 22 skipped**，全具名）；ruff 干净；契约 **14 路径 current**（`domain.schema.json` 仍恰 6 输入模型 + `RunState`）；`uv lock --check` exit 0（**未新增依赖、未动 `uv.lock`**）；e2e **16 passed**；`deploy.ps1 -PlanOnly` EXIT=0（离线 plan、零 AWS 调用）、`cleanup.ps1` `NOT EXECUTED`/exit 2（无 state）。
- **D1（C1）**：`repo_dynamo.py` 实现 `Repository` 全协议（裁定 5 键/原子性；共享 `repo_sqlite` 的确定性 id 与时间戳助手杜绝漂移）+ `dynamodb_live` marker + 离线协议集合守卫；`FeedbackRecord.agentcore_session_id` + `SCHEMA_VERSION` 3→4 幂等迁移 + v3→v4 回归。
- **D2（C2/C3）**：公网三门（默认口令 aws 拒启 / 会话 TTL+idle / 登录限速 429+`Retry-After`）+ `/api/login` 429 契约重生成（路径仍 14）+ `conftest.py` 清理清单 20→24。
- **D3（C4）**：`agentcore_client.py` 按真实 API 重写（`CreateEvent`/`GetEvent`/`RetrieveMemoryRecords`）+ `memory.py` 两段式 `get_status`（`MemoryStatusResult`）+ `_namespace` `/owner/<o>/pet/<p>` + `worker.py` `MemoryPoller` 接线 + **守卫 re-ruling（裁定 12，改作用域非放宽）**：`get_status` 调用者 `== []`→`<= {worker.py}` + AST 钉死 `poll_once`；静态字面量白名单**未扩**（`repo_*`/`worker` 用 `MEMORY_AVAILABLE`/`MEMORY_PROCESSING` 常量）；仓储 `available` 无 ids→`ValueError` 不变式（双实现 + 负向）。
- **D4（C5）**：`.gitignore` **先行**加 `infra/deploy_state.json` + `deploy_plan.json`（9 资源 + 依赖序 + `delete_order`）+ `deploy_aws.py`/`cleanup_aws.py`/`aws_probe.py` + `deploy.ps1`/`cleanup.ps1` 门控判据改写（cdk/CFN→boto3/deploy_plan）+ OIDC/IAM 声明 + 离线守卫（`test_deploy_plan.py` 含**命名模板跨源一致性**、`test_deploy_aws.py` plan 纯函数）。
- **D5（C5）**：`image.yml`（`workflow_dispatch` + OIDC + 单架构 amd64 推 ECR）+ `Dockerfile` 解耦烤死的 `PAWTWIN_MODE`。**镜像未构建**（无 Docker、无 remote）。
- **D6（C2/C3/C6）**：`main.py` **移除** `mode=aws` 拒启 → 真实装配 + 零计费探活（DynamoDB/AgentCore，Bedrock 不探活）+ 探活失败拒启 + `app.state.aws_connected`；`/readyz` 受控修订（探活通过→200，LB 仍 `/healthz`）；`api.py` `storage`/`aws_connected` 真实化；前端证据驱动真实态标签 + `FeedbackView.memory_record_count` + 禁串守卫扩到新常量。
- **D7**：`scenarios.json`（24 例，A01–A14 全覆盖 + 注入/信息不足/失败回执）+ `evaluate.py`（口令只从环境、逐例判定、超时如实记 TIMEOUT、不预填准确率、全 advisory 降级 ERROR 防假绿）+ `test_scenarios.py`。
- **D8（C7）**：`STATUS` Day-5 三档表 + 本地/云端双列 + 命名门禁判定；`evidence/day5-{local,cloud-blocked,handoff}.md`；本完成记录；`reviews/day5.md`（非作者审查）。
- **边界（不拆成半通过）**：真实 DynamoDB 真表、真实 AgentCore 往返、真实 Bedrock、镜像构建、真实 HTTPS/公网三门、CI 远程运行、`-Apply`/`-Destroy`、真机 24 案例、跨副本 A04 **全部未验证**（无凭据/无部署），逐条见 [day5-cloud-blocked](evidence/day5-cloud-blocked.md)。**命名门禁（裁定 19）：G0/D1′/G5–G10 未闭合 → 产物仍为「本地验证候选（非参赛版）」**。
- **提交**：**尚未提交**（工作树 43 项变更；提交需用户明确授权）。**仍无 remote、未推送**；本轮**零 AWS 调用、零云资源、零费用、无镜像构建**。
- **容量冲突上报**：Day-5 字面（材料全套）+ Day-4 顺延的全部云端块 ≈ 28–33h，压不进一日；依裁定⑤**材料整体顺延 Day-6**，五日实际变六个工作日（已在 STATUS/本表留待用户认可）。

## 认领记录格式

- BE-CLOUD-01（2026-10-11）：`/root` Coordinator，`chore/bootstrap` @ `31da349`，保留当前完整 dirty checkout，串行修改后端服务/测试/配置/生成契约/前端标签/部署脚本和文档；只读 Agent 研究与审查。计划见 [backend-services-2026-10-11](plans/backend-services-2026-10-11.md)。用户确认 AWS 已审核通过；总预算 $10 沿用；Alexa+ 平台比赛不开放。真实 AWS 接入仍须短期凭证与现场往返验证。

每项开始前追加：任务 ID、Agent/任务名称、起始提交、工作树路径、分支、允许写的文件、预计交付、接口变更需求。完成后填写交付提交和验证证据链接。不要让多个 Agent 同时改此表。
