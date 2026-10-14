# PawTwin 本地演示素材采集

本脚本把已经通过的双账号演示排练录成两个独立角色的原始素材，同时保存实际测试附件、来源证据和校验清单。画面是中文界面、无旁白的自动化操作；不是正式英文成片、公开视频、真实 Alexa 录音或云部署证据。

当前版本为 2026-10-11：实际官网 → App 成长/记忆确认 → 独立 `/#alexa` 偏好/新会话 → 规则照护草案/选时间/准备/明确确认 → 第二账号领取完成 → 模拟器完成记录/日报 → 删除后新回答。完整操作见 [当前英文运行表](demo-runbook-2026-10-11.md)。

历史对应主线见 [展示方案](PawTwin_展示方案_2026-10-03.md)，测试行为见 [演示排练](../../frontend/e2e/demo-rehearsal.spec.ts)。主人记录与确认偏好，家人从相同宠物上下文读取资料，主人确认后创建人工任务，家人领取完成，日报更新；删除记忆后新的回答不再引用旧内容。

## 执行

项目依赖和 Playwright Chromium 须已安装。首次准备使用现有 `scripts/setup.ps1`；浏览器安装沿用 `scripts/test-e2e.ps1 -InstallBrowser`，它还会执行全量检查，不属于素材脚本本身。已有浏览器可在当前 PowerShell 进程设置 `PAWTWIN_BROWSER_EXECUTABLE` 为其实际可执行路径。

在项目目录执行：

```powershell
./scripts/capture-demo.ps1
```

默认端口是 8812。默认目录是 `docs/evidence/hackathon-capture/<时间戳>-<唯一后缀>/`；每次创建新目录。选择其他端口或目录：

```powershell
./scripts/capture-demo.ps1 -Port 8813 -OutputDirectory docs/evidence/hackathon-capture/2026-10-11-final
# 必要时增加 -NodeDirectory '<兼容 Node 安装目录>'
```

相对输出目录以项目根目录为基准。已有非空目录或文件会被拒绝，素材不会覆盖；重拍使用新目录。端口被占用时选择其他端口，脚本不会终止已有服务。

脚本使用项目兼容 Node runtime，先 production build，再仅运行 `demo-rehearsal.spec.ts`，固定 1 worker、0 retries。数据库强制为隔离内存库，模式为 local，模型为 local_fake，记忆为 not_implemented，照片识别关闭；不会读取或修改用户原库。进程环境变量在结束或失败时恢复。两位角色是独立 browser context，内存资料不进入 8807 等持久预览库。

## 产物与真实性

| 文件 | 内容 |
|---|---|
| `owner.webm` | 展示主人的原始中文无声录屏，由带 owner 标签的真实 WebM attachment 收集 |
| `carer.webm` | 家人小林的原始中文无声录屏，由带 carer 标签的真实 WebM attachment 收集 |
| PNG 附件 | 排练实际生成并附加的画面，十四张当前镜头；录制时聚焦实际视口，未录制的普通排练保留全页验收图 |
| `demo-evidence.json` | 排练实际附加的本地 API 与源记录证据，不由采集脚本补造 |
| `results.json` | Playwright 原始 JSON 报告，包含结果、附件名称和实际路径 |
| `capture.log` | build 和该次排练的命令输出及采集状态 |
| `raw/` | Playwright 该次输出，保留原始录屏和附件 |
| `sha256-manifest.json` | 成功后生成的文件字节数、SHA-256、附件与收集文件映射，以及本地/模拟边界；不包含清单自身的哈希 |

采集脚本从 JSON reporter 的实际 attachments 获取文件路径或 base64 内容，不猜测 UUID 视频文件名。只有进程退出成功、报告确认一条用例首次通过、必要附件完整且非空时，才收集素材并写成功清单。失败保留已有 raw、report 和 log 供排查，不能把失败目录或未生成清单的目录当作成功采集包。脚本不安装依赖、调用 AWS、发布素材或提交比赛。

`results.json` 保留当次机器上的实际绝对路径，分享前核对个人路径和日志；演示账号资料为临时虚构数据。将收集包和清单一起保留，避免只留剪辑后的视频而丢失来源。视频需人工播放检查画面与角色，自动化完成不代表最终视频已经验收。

## 从素材到正式展示

1. 人工播放两个 WebM，确认画面可读、角色明确、界面保留“本地”“规则”“Alexa 网页模拟”等标签。
2. 按现有 3 分钟脚本剪辑主人与家人镜头，补两位角色标题、英文旁白/字幕及结尾状态卡。自动化等待和填表不是最终展示节奏。
3. 展示 150 g / 12.5% / 实际 7 天时同时保留“演示样本”、源记录和摄入缺失；确认照护方案由当前模拟器按明确指令生成规则草案，主人核对并选择时间，再明确确认；任务完成是人工照护。
4. 展示实际作者时，可补拍家庭页“最近家庭动态”；任务卡的“负责人”与完成操作人是不同的证据字段。原始 JSON 中的完成者核对不能替代需要观众看清的画面。
5. 写一页本地检查摘要，引用这次采集与检查结果；云身份、真实模型、AgentCore、真实 Alexa/设备、真实家庭试用和公网访问分别列为尚未完成。

最终英文成片、人工计时排练、真实家庭反馈及比赛规则/资格核对仍是后续工作。任何对外发布与提交沿用项目授权要求。

当前 `demo-evidence.json` 为 schema_version=2，保存实际草案、准备方案、确认结果、模拟器完成回复及截图角色/URL/测试起点后毫秒数。测试时码不是 WebM seek 时码，不能直接当剪辑切点。当前成片使用完整真实截图并重新计算编码时间轴；原始双角色 WebM 保留，不冒充实时播放。旧截图名保留，新增 00-product、08-memory-confirmed、09-alexa-draft、10-alexa-pending、11-alexa-confirmed、12-alexa-result、13-alexa-new-session。
