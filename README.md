# PawTwin

**2026-10-14：当前版本代码与应用审查通过**：修复家庭账号切换时的迟到数据/邀请码残留、跨宠物测量草稿、读取超时和记忆空值错误；本地测试隔离 `.env`，源码包与 Git 排除会话追踪和数据库备份。最终 **447 backend passed / 1 skipped / 21 live-AWS deselected；115 browser passed（四个独立服务分片，0 retries）**，Ruff、契约、类型和生产构建通过。审查范围、修复依据与保留限制见[当前版本审查](docs/reviews/current-version-2026-10-14.md)。这是本地规则/模拟设备版本的 Git 快照，真实 AWS、Alexa 和硬件仍未验证；下方数字保留为历史记录。

**2026-10-14：英语 / 中文界面**：展示页、家庭应用、原工作台、Alexa 网页模拟、临时只读访问及就诊信息卡已支持双语。首次打开默认英语，页头 **English / 中文** 可即时切换并记住选择。用户填写的名称、任务、观察和日记保留原文。构建通过，完整浏览器回归 107 passed，详见[双语验证](docs/evidence/i18n-2026-10-14.md)。

**2026-10-13 工作空间升级**：家庭应用与照护工作台按宣传页统一视觉，保留独立登录、数据和权限。今日/照护/成长/分身/家庭导航与成长四分区、档案像素形象、领取筛选、访客只读界面已整理；原工作台拆为请求与审批/运行记录/演示设置，并修复迟到回执、重复请求、卡住读取和会话失效状态。

**100 browser passed / 19 files / 0 retries；425 backend passed / 1 skipped / 21 live-AWS deselected**，Ruff/契约/类型/生产构建通过，独立复核无待修复 P1/P2。38 张四宽截图见[验收记录](docs/evidence/workspace-upgrade-2026-10-13.md)，操作路径见[功能指南](docs/FEATURES.md)。本机[家庭应用](http://127.0.0.1:8834/#app/home)、[照护工作台](http://127.0.0.1:8834/#workbench)、[官网](http://127.0.0.1:8834/)使用独立虚构库，演示测量明确标注；旧库和已有修改保留，默认本地规则/网页及设备模拟。以下为日期历史记录。

**2026-10-13 照护交接与就诊卡**：新增管理员指定宠物、期限、可撤销的分身只读访问；护工独立问答；就诊卡预览、打印/另存 PDF 和离线 HTML 导出；官网照护交接/就诊准备案例与功能演示。**425 backend passed / 1 skipped / 21 live AWS deselected；77 browser passed（48+17+12，独立服务，0 retries）**，Ruff/契约/TS/build PASS，独立复核无开放发现。

[功能演示](http://127.0.0.1:8820/#vision) · [就诊卡导出](http://127.0.0.1:8820/#app/growth) · [管理员临时授权](http://127.0.0.1:8820/#app/family) · [产品方案](docs/plans/PawTwin_照护平台与就诊信息卡_2026-10-12.md) · [完整验收](docs/evidence/platform-2026-10-12.md)。12 日启动、13 日完成本地验收；本机预览改用独立虚构 `data/platform-preview-2026-10-12.db`。旧库与全部既有修改保留，默认本地规则/网页模拟；服务预约、接单、交易仍为未来规划，无云调用或发布。

**2026-10-12 应用实用性与可视化**：今日概览、优先照护队列与筛选、可读实测曲线和来源报告、统一功能直达及官网同步已本地交付。修复重复计划编辑、子数据重试/撤权/切宠、历史完成统计及同一时钟刻度报告遗漏。**408 backend passed / 1 skipped / 21 live AWS deselected；62 browser passed（45+17，独立服务，0 retries）**；Ruff/契约/TS/build PASS，独立复核问题已处理。

[功能与使用指南](docs/FEATURES.md) · [完整验收](docs/evidence/usability-2026-10-12.md) · 本机[新版家庭应用](http://127.0.0.1:8820/#app/home)、[成长](http://127.0.0.1:8820/#app/growth)、[官网](http://127.0.0.1:8820/)。内置浏览器使用独立虚构演示家庭，测量标注为演示样本；原库和既有修改保留。默认本地规则，Alexa/硬件仍为模拟，未新增云调用或发布。下方按日期保留此前交付。

**2026-10-12：英文比赛演示视频**：[新版2:50 MP4](../PawTwin-demo-2026-10-12.en.mp4) · [独立字幕](../PawTwin-demo-2026-10-12.en.srt) · [制作和核验](docs/submission/demo-video-2026-10-12.md)。1080p、英文旁白/烧录字幕，加入8段实际操作录屏；保留旧版。真实素材来自已验收的11 October双账号排练，仍为本地规则和设备模拟；没有上传/提交。


**2026-10-11 比赛准备与当前 demo**：393 backend passed / 1 skipped / 21 live AWS deselected，42 browser passed（0 retries），Ruff/契约/TS/build PASS。并发喂食、迟到重评、回执恢复、转发头限流修复已独立复核。[完整验收与剩余提交门](docs/evidence/submission-readiness-2026-10-11.md) · [新版2:50英语视频](docs/evidence/submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4) · [英文评委指南](docs/submission/judge-guide.en.md)。本机 [官网](http://127.0.0.1:8816/)、[App](http://127.0.0.1:8816/#app)、[Alexa模拟器](http://127.0.0.1:8816/#alexa)，使用独立虚构样例库。

本地脚本禁用代理头。未来代理部署需限制Uvicorn forwarded-allow-ips并核对转发链，不能仅用PAWTWIN_TRUST_PROXY_HEADERS=true建立客户端身份边界。Dynamo旧facts无guard标记时拒绝喂食，需另行审计迁移。展示local_rules/SQLite/模拟设备；可选家庭Bedrock已接线/离线测试，真实验证未记录。本轮无AWS调用。GitHub访问、许可/分享、公开视频、本人工具反馈/资格/权利与提交仍待完成。以下数字与旧账号状态为各日期历史记录。

宠物照护 Agent 项目，面向 Alexa/AWS 黑客松原型开发。自动照护核心仍围绕虚构宠物 Mochi；小屋已支持本地多宠物档案。独立本地家庭账号、成长统计和规则分身已实现；云接入待开发与验证。

**2026-10-11 Alexa+ 网页模拟体验**：`/#alexa` 新增独立模拟器，共用家庭账号和宠物记录。支持文字模拟口述、快捷提问、最多 20 轮本页对话、新会话、依据查看、规则照护草案→选择时间→明确确认→人工任务→完成记录查询。切宠/离开清空对话，刷新后家庭记录和任务仍保留；访客只读，失效依据拒绝确认。346 后端 passed / 1 skipped / 21 deselected，41 浏览器 passed，ruff/契约/TS/build PASS；独立复核问题已修复。本地预览 [Alexa 模拟器](http://127.0.0.1:8807/#alexa)，注册账号并创建家庭后体验。仍是本地规则与网页模拟，无真实 Alexa/模型/硬件连接。[验收记录](docs/evidence/alexa-simulator-2026-10-11.md)。

**2026-10-11 动画与案例**：新增可暂停的轻量动画、滚动入场和三组逐步查看的虚构照护案例，支持键盘与系统减少动画。最终 33 浏览器检查通过，独立复核问题已修复。预览 http://127.0.0.1:8807/#cases ，[验证记录](docs/evidence/motion-cases-2026-10-11.md)。

**2026-10-11 产品官网升级**：宣传页采用居中大标题、悬浮设备画面、明暗章节和四项可切换体验；320/390/1440 适配、键盘和减少动画模式已检查。应用与原工作台入口保留。当前 31 浏览器检查通过、333 后端 passed / 1 skipped / 21 deselected，类型/构建/ruff/契约通过，独立复核问题已修复。详见 [改版验收](docs/evidence/premium-showcase-2026-10-11.md)。本地预览 http://127.0.0.1:8807/ ，未发布。

**2026-10-04 页面更新**：首页 `/` 现在是独立产品宣传页，展示产品价值、界面示意与使用流程；`/#app` 进入实际家庭应用（桌面侧栏、手机底部导航）。原照护工作台移至 `/#workbench`，`/#home` 保留兼容。宣传页首次加载不请求业务 API，界面示意不代表私人数据。最新验证：333 后端 passed / 1 skipped / 21 deselected，30 浏览器 passed，ruff/契约/TS/build PASS；详见 [页面交付与验证](docs/evidence/product-and-app-2026-10-04.md)。

**最新黑客松补齐（2026-10-03）**：后端 333 passed / 1 skipped / 21 deselected，浏览器 27 passed，ruff/契约/TS/build PASS；修复真实 SDK 契约、累计预算遥测、报告来源、云状态误报、新宠保存后切页竞态及云清理读回/重试/旧 state 覆盖缺陷。英语说明、评委指南、工具反馈草稿、双账号录屏和 170.019 秒[英文审核视频](docs/evidence/submission-video-2026-10-03/local-review-02/pawtwin-local-review.en.mp4)已补齐，详见 [完整度评估与证据](docs/evidence/hackathon-completeness-2026-10-03.md)。用户已授权 10 美元云服务预算，AWS 账户仍在官方审核；真实云验收及对外提交尚未完成。下列旧验收数字保留为历史记录。

**2026-10-03 附加计划本地交付**：五入口 /#app（小屋/照护/助手/成长/家庭），账号/邀请/撤权、可信作者、任务生命周期、实测成长和自动报告、确认记忆及 App/Alexa 网页模拟共用上下文。实测 284 后端 passed、26 浏览器 passed，ruff/契约/TS/build PASS。见 [验收交接](docs/evidence/extension-local-2026-10-03.md)、[任务看板](docs/TASKBOARD.md)、[附加需求](docs/plans/PawTwin_附加开发计划_2026-10-02.md)。

构建后运行 ./scripts/dev-home.ps1，打开 http://127.0.0.1:8000/#app，注册本地账号并创建/加入家庭。密码至少 12 字符；刷新恢复，服务重启重新登录。原数据库设备额度保留，新家庭资料在 <数据库路径>.family.db；旧 Home 首次读取会备份后幂等导入。没有真实模型/AgentCore/Alexa/硬件或真实家庭试用宣称；新家庭 AWS 数据层明确拒绝未接入能力。

原工作台和 /#home 继续兼容。下方 Day-1–3 与旧小屋段落是历史范围；当前状态以本段及 STATUS 顶部为准。

**Day-1 本地核心已实现并通过检查**：在骨架（运行环境、共享契约、多 Agent 协作入口）之上，已落地演示登录/会话/CSRF、事件摄入与去重、SQLite 持久化、硬性策略、审批状态机、模拟执行与回执，以及拒绝闭环（浏览器 e2e + 集成测试双证据）。

**Day-2 已把分析器真正接线并补上可靠性与证据**：分析器 seam（`inline` / `local_fake` / `bedrock` 三后端，可切换且不静默互相回退）、可领取状态白名单 + 租约续约 + 状态 CAS + 尝试上限、45 秒分析超时与「每任务 ≤4 次模型调用 / ≤800 输出 tokens」的 fail-closed 限额、后台 worker、`demo/facts` 与 `demo/device-mode` 现场注入、可持久化的证据台账与调用遥测、OpenAPI 错误响应补全，以及浏览器 approve 闭环 e2e。**真实 Bedrock 推理仍未执行（无 AWS 账号），AgentCore 记忆、DynamoDB 真表与 AWS 部署仍待后续开发**；本地通过与云端未验证分列，不能将此版本作为完整参赛原型。详见 [当前状态与验证](docs/STATUS.md)。

**Day-3 已接入记忆抽象层、主人反馈与可靠性升档**：`memory.py`（`MemoryService` seam + 诚实本地后端 + AgentCore 骨架 + 离线 stub）、`POST/GET /api/feedback`（原文入库、幂等去重、`memory_status` 诚实为 `saved`）、`POST /api/demo/new-session`（轮换 `conversation_id`、保留记忆/事实/登录）、`search_owner_memory` 接线（本地返回空、不伪造证据）、worker 由顺序 drain 改为有界线程池真并发（准入上限获得生产触发路径）、跨进程双批准（文件库两连接 + WAL）与真实 OS 进程重启复验、前端记忆区。**真实 AgentCore 提炼/检索与场景 C「记忆改变建议」仍未执行（无 AWS 账号），DynamoDB 真表、跨副本多 replica 与部署仍待 Day-4**；本地通过与云端未验证分列。详见 [当前状态与验证](docs/STATUS.md)。

## 快速入口

### 原宠物小屋（2026-10-02 历史实现，保留兼容）

前端构建后运行 `./scripts/dev-home.ps1`，打开 `http://127.0.0.1:8000/#home`。
沿用演示登录；默认口令 `local-demo-passphrase`。数据与照片保存在本机
`data/pet-home.db`（已被 Git 忽略），刷新和重启后保留。原工作台入口为 `/#workbench`。

- 多宠物档案：名字、种类、品种候选、性别、生日/年龄、主人喜好、照片。
- 正面/侧面像素宠物：主人选择毛色、花纹、大小；房间保持 2D 俯视。
- 物品管理：窝、玩具、水碗、喂食器，支持命名、备注、位置编辑和关联照护入口。
- 照护计划：人工喂食、换水、陪玩、梳毛、洗澡、剪指甲、清洁、散步；
  主人设置一次性/重复周期、负责人、完成或延期，记录真实手动操作。
- 个体偏好：仅今天/长期主人确认偏好/一般观察，按宠物与照护类型隔离；
  建议引用已有记录，当前为明确标注的规则建议，不冒充模型推断或 AgentCore 提炼。
- 家庭交接：家庭显示名、负责人、完成记录；同一演示登录，尚无独立账号和权限角色。
- 成长日记：日期、照片、标题、文字、时间线、生日/年龄和依据实际记录的七日摘要。

照片上传和手动确认可直接使用。Bedrock 照片识别适配器已接线，但默认关闭，
需另行授权云调用、配置支持视觉的模型和凭据后启用
`PAWTWIN_PHOTO_RECOGNITION_ENABLED=true`；本轮仅验证注入 SDK 响应的映射与草稿校验，
未调用云端、未验证识别准确率。识别只生成待确认种类/毛色/花纹/品种候选，
不推断年龄、性别、健康或喜好。像素形象是可编辑的模板组合，不是生成式肖像。

新宠物的照护任务仅记录主人手动操作；自动喂食仍只沿用 Mochi 的审批与配额流程。
新页面数据层为本地 SQLite，AWS 模式访问会明确返回 503，不静默回退。
未经云部署验证；没有上传、发布、提交或创建云资源。

- [当前状态与验证](docs/STATUS.md)
- [Agent 协作规则](AGENTS.md)
- [任务看板](docs/TASKBOARD.md)
- [各角色起始任务](docs/agents/README.md)
- [五日产品方案](docs/plans/PawTwin_五日开发总方案.md)
- [完整实施任务单](docs/plans/PawTwin_Agent_实施任务单.md)
- [本次初始化范围](docs/INITIALIZATION.md)

## 环境

- Python 3.12 与 uv。
- Node.js 24 推荐；npm 用于锁定前端依赖。
- PowerShell 用于仓库提供的 Windows 脚本。
- 本地初始化不需要 AWS 账号、AWS CLI 或 Docker。

本机系统 Node 版本较旧时，脚本优先使用可用的兼容版本；可通过 `PAWTWIN_NODE_DIR` 指定包含 node 的目录。Codex 运行时仅作本机便利选项，项目不依赖用户绝对路径，另一台机器正常安装 Node 24 即可。

## 本地启动

在项目根目录执行：

```powershell
./scripts/preflight.ps1
./scripts/setup.ps1
./scripts/dev-backend.ps1
```

保留后端终端，在另一个终端运行：

```powershell
./scripts/dev-frontend.ps1
```

开发页面默认 `http://127.0.0.1:5173`（Vite 代理 `/api` 到 `:8000`），后端默认 `http://127.0.0.1:8000`（同源服务已构建的 `frontend/dist` 与 API）。端口被占用时应更改配置或停止自己启动的进程，不终止其他任务的服务。页面从真实 `/api/state` 显示模式与业务状态（`/api/bootstrap` 仅为非敏感骨架状态，不作业务源），不生成虚假业务结果。登录口令取自 `PAWTWIN_DEMO_PASSPHRASE`（本地默认值为非秘密演示门禁；评委口令经私有测试说明交付，不写入公开源码）。

配置字段参见 `.env.example`。启动参数与环境变量以 `backend/pawtwin/config.py` 为准；不要假设配置示例已设置到环境中，更不要把凭据写进前端。

## 验证

```powershell
./scripts/verify.ps1
```

脚本检查后端测试、静态检查、契约是否需要重新导出、前端类型和构建。浏览器 smoke 另外在项目根目录执行：

```powershell
./scripts/test-e2e.ps1 -InstallBrowser
```

脚本使用与开发脚本一致的兼容 Node。首次安装 Chromium 会下载测试浏览器；不安装或修改用户的桌面浏览器。已安装后可省略 `-InstallBrowser`。具体本机已执行的结果见状态文档。

浏览器 e2e 直指后端同源 `http://127.0.0.1:8000`（`main.py` 服务已构建的 `frontend/dist` 与 API，无需 Vite preview/proxy）。`scripts/test-e2e.ps1` 先构建，再依次运行四个分片，每片新建隔离内存服务，避免全套注册用例触发业务限流；CI 使用相同入口，生产限流不变。构建与浏览器检查应顺序执行。受限网络下已有可用 Chromium 时可将 `PAWTWIN_BROWSER_EXECUTABLE` 设置为其可执行文件绝对路径；默认仍使用 Playwright 管理的浏览器。测试不会复用或终止其他任务的服务；后端 8000 须空闲，也可用 `PAWTWIN_E2E_PORT` 指定空闲端口。

## API 与共享契约

- `/healthz`：进程存活，不调用 AWS。
- `/readyz`：本地模式为 degraded/503；AWS 模式只有真实装配与必要探活通过才可报告 ready。组件状态不能代替真实模型、记忆和新小屋云数据层验收。
- `/api/bootstrap`：不含秘密的骨架状态（`stage`/`capabilities`/`analyzer`），仅供连接验证，非业务源。
- 业务路由（需登录；写操作需 CSRF）：`POST /api/login`、`POST /api/logout`、`GET /api/state`、`POST /api/events`、`GET /api/runs/{run_id}`、`POST /api/runs/{run_id}/approval`、`POST /api/feedback`、`GET /api/feedback/{feedback_id}`、`POST /api/demo/facts`、`POST /api/demo/device-mode`、`POST /api/demo/new-session`。未授权返回 401，CSRF 失败返回 403；这些错误响应已在 OpenAPI 中显式声明。
- `GET /api/runs/{run_id}` 返回 `evidence`（工具名/来源/检索时间/摘要）与 `telemetry`（后端、模型调用次数、输出 tokens、耗时、`request_id`），以及 `policy_reason`/`failure_reason`。无真实云调用时 `request_id` 为 `null`，页面如实显示「无（未发生真实云调用）」。
- `POST /api/events` 的返回状态取决于 `PAWTWIN_WORKER_MODE`：`background` 返回 `queued` 由 worker 处理，`inline` 返回受理后的当前状态。
- `contracts/openapi.json`：当前 57 条路径，含原业务/反馈/demo、`/api/home` 与 `/api/family` 路由；以后端源模型导出检查为准。
- `contracts/domain.schema.json`：**恰为** 6 个输入模型 + `RunState`；公开响应 DTO 只出现在 OpenAPI，不进领域 schema。

`demo/facts` 只能修改 `last_fed_minutes_ago` 与 `daily_dispensed_grams`（或把它们置为「未知」以触发 `NEEDS_INFO`）；日配额、单次上限与最短间隔是硬性限制，**不在请求模型内**，任何请求都无法修改。`demo/device-mode` 只影响之后的新命令、仅存于进程内、重启复位。`POST /api/feedback` 保存主人反馈原文（以 `Idempotency-Key` 头幂等去重），本地 `memory_status` 恒为 `saved`（原文已存业务库）、**绝不**谎报 `available`；`GET /api/feedback/{feedback_id}` 回读该状态；`POST /api/demo/new-session` 轮换 `conversation_id` 而保留登录/事实/记忆。真实 AgentCore 提炼与检索为条件项（无账号），不会用返回成功的空接口冒充实现。Python 模型是契约来源，生成文件不要手动修改。修改模型后运行导出工具并纳入同一个审查提交。

```powershell
uv run --frozen python scripts/export_contracts.py
uv run --frozen python scripts/export_contracts.py --check
```

领域 schema 表达基础类型与范围；动作类型和投喂克数的组合约束由 Python 模型校验，消费者仍须以服务端验证结果为准。

## 多 Agent 如何开始

把本文件所在目录作为项目根目录。先让后端 Agent 执行 BE-01 冻结业务接口，再并行推进前端和 AI 工具。每个 Agent 使用独立工作树/分支，并读取对应角色入口。总负责人独占共享契约、依赖锁和集成记录。

当前基线分支为 `chore/bootstrap`，没有配置远程仓库。新 Agent 从已通过验证的提交开始，不直接在其他 Agent 的检出目录切换分支。

## 真实与模拟边界

PawLink 项圈是概念；传感器事件与喂食设备是模拟对象。真实 AgentCore 长期记忆的提炼/检索与部署尚未验证；主人反馈原文本地真实入库，但本地**不提炼**为长期记忆。旧工作台 `aws` 模式可装配真实 DynamoDB/AgentCore 适配器并探活，缺配置或探活失败会拒绝启动；探活成功也不证明模型推理、记忆提炼或新家庭云存储已验证。`aws_connected` 在完整证据未闭合前保持 false，`/readyz` 分列未完成项。新家庭云层访问明确 503。本轮修复 SDK 请求/响应与预算遥测，真实反馈到提炼完成的关联仍显式不支持；详见[本轮评估](docs/evidence/hackathon-completeness-2026-10-03.md)。

分析后端与存储分别标注：页面同时显示 `analyzer`（`inline`/`local_fake`/`bedrock`）、`storage`（`sqlite`）与 `memory`（`not_implemented`）。`aws_connected` 只有在存储、模型与记忆**都**真实连通时才为真，因此「analyzer=bedrock 且 aws_connected=false」是诚实表述而非矛盾。

真实模型调用需要安装可选依赖并具备凭据：`uv sync --frozen --extra bedrock`，然后设置 `BEDROCK_MODEL_ID`/`AWS_REGION` 与一个已授权的凭据来源。缺失时不会回退到替身，而是让该次分析显式失败（`BACKEND_UNAVAILABLE`）。`scripts/preflight.ps1` 只读核对这些前提，`scripts/bedrock-smoke.ps1` 在无凭据时输出「NOT EXECUTED」并以非零码退出，绝不虚报成功；它一旦运行就会产生**计费**调用。真实 AgentCore 记忆同理：`uv sync --frozen --extra memory` + 设置 `AGENTCORE_MEMORY_ID`/`AWS_REGION` 与凭据；缺失时 `search_owner_memory` 失败关闭（`MEMORY_UNAVAILABLE`）而非伪造记忆，`scripts/agentcore-smoke.ps1` 无凭据时输出「NOT EXECUTED」并以退出码 2 结束。

云端资源创建、费用和对外发布均未执行。Dockerfile 为后续部署准备（已加 `--extra bedrock --extra memory` 与单进程说明），但本机无 Docker，**镜像未构建验证**；实际是否构建通过以状态文档为准。
