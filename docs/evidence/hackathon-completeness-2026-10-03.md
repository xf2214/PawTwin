# PawTwin 黑客松完整度评估与补齐

2026-10-03，Asia/Shanghai；对象是 `outputs/pawtwin-app` 当前工作区，
HEAD `31da349` / `chore/bootstrap` 加此前未提交的家庭扩展。

## 评价

**本地产品闭环已经较完整，适合演示；尚不是可以直接提交的完整参赛成品。**
最有竞争力的点是同一宠物的记录在家庭成员、入口和新登录之间连续生效，
并能通过来源、权限、任务完成和报告回写检查。账号/照片/小屋的数量不是
核心说服力；需要让评委看到有效资料如何改变后续回答与受控行动。

最大的技术缺口是当前 family assistant 的回答仍是关键词规则，照护方案
类型/标题/时间仍由主人输入。它是可信的记录协作原型，尚不能证明生成式
理解或自主规划。**允许 Alexa 网页模拟，不等于现有 local_rules 肯定满足
AI/agentic 技术资格。** 技术适配与最终资格均保持未确认。

按官方四个同权重评审维度判断：

| 维度 | 当前评价 | 依据 / 主要缺口 |
|---|---|---|
| 技术实现 | 本地工程可靠；赛道 AI/agentic 证据弱 | 权限、来源、版本、统计和闭环有行为测试；新家庭未接真实模型/云记忆 |
| 产品设计 | 已形成连续体验 | 五入口、正常视角宠物/俯视小屋、家庭交接；中文界面需要英语说明/视频译文 |
| 潜在影响 | 问题具体，效果尚未证实 | 能展示交接和重复信息的解决思路；没有真实家庭前后对比，不宣称节省时间 |
| 创意质量 | 个体上下文与可撤销照护有辨识度 | 跨成员/跨会话的来源链强于单轮问答；真实智能规划仍待建立 |

以上是工程与参赛准备判断，不是官方评分、资格认定或获奖预测。

## 当前完整度矩阵

| 交付面 | 状态 | 可检查证据 |
|---|---|---|
| 独立账号、家庭、角色、多宠档案、记录共享 | 本地已完成 | 家庭行为测试及全量浏览器验证 |
| 实测成长、日周报告、纠错/删除、来源版本 | 本地已完成；本轮补旧单条体重来源 | `test_family_completeness.py` |
| 候选确认、另一成员新登录复用、删除失效 | 本地已完成；本轮补全过程对比 | 实际 `demo-evidence.json` |
| 照护待确认→确认→家人完成→日报 | 本地已完成 | 真实 UI/API；`manual_care` 与完成者 ID |
| 自动设备 | 明确模拟 | 原 Mochi 审批/硬限额/回执；新家庭不继承执行权 |
| 英语项目说明、架构、测试说明、工具反馈 | 本轮已补齐草稿 | submission 下四份新材料；提交人个人反馈选择待确认 |
| 实际录屏、截图、采集来源 | 本轮已补齐 | 双角色 WebM、7 PNG、JSON、成功日志和 SHA-256 |
| 少于三分钟英语成片与字幕 | 本轮已补本地审核版 | 170.019 秒 H.264/AAC、22 句英语字幕；人工听审尚未执行 |
| 正式公开视频与最终比赛交付 | 未完成 | 未上传/提交，不能用本地文件代替公开视频 URL |
| 当前源码审阅导出 | 本轮已补脚本与门禁 | 包含 dirty/untracked 家庭扩展，CRC/哈希/必需文件校验；不选择许可证 |
| 评委可访问 GitHub 源码 | 未完成 | 尚无 remote；需包含全部当前扩展，不能只发布旧 HEAD |
| 真实 AI/Agent 规划与家庭云存储 | 未完成 | App/Alexa 实际 `local_rules`；AWS family 返回 503 |
| AgentCore 反馈到提炼完成的关联 | 未完成，显式失败 | GetEvent 不提供提炼状态；需 job/record 关联协议 |
| AWS Builder 附加挑战 | 未满足实际使用证据 | SDK/offline 通过不等于使用 AWS 服务 |
| 真实家庭效果、真实模型质量 | 未执行 | 空白试用模板；没有捏造反馈 |
| 活动报名、个人资格、代码访问/许可、正式提交 | 未确认 / 未执行 | 需参与者与对外交付裁定 |

## 本轮实际补齐

1. **修复 AgentCore 请求和响应契约**：metadata 使用 `{stringValue: ...}`；
   检索读取 `memoryRecordSummaries` / `content.text`。以前会提交失败或丢全部记录。
2. **修复不存在的提炼状态盲轮询**：GetEvent 仅证明原始事件存在，当前明确
   `EVENT_EXTRACTION_STATUS_UNSUPPORTED`，不无限等待或虚报长期记忆可用。
3. **修复 Strands 预算遥测**：从 `metrics.cycle_count`、
   `accumulated_usage.outputTokens` 取实际累计指标，缺项/无效项显式失败；
   5 次调用或 801 tokens 的结果会被既有业务限额拒绝。实际云计费上限未实测。
4. **修复报告来源缺口**：旧单条窗口外体重只要显示为 `latest_g`，其 ID 和
   version 必须被引用；修改/删除后引用同步变更；不虚构变化量或测量跨度。
5. **修复云状态过度宣称**：DynamoDB/GetMemory 探活只说明组件访问。
   `aws_connected` 不会仅因模型配置升级为 true；AWS `/readyz` 保留 503 并
   分列模型未验证、提炼不支持、家庭未接通。`/healthz` 仍是正常存活检查。
6. **完善复现与证据**：e2e 固定内存库、local 模式、关真实记忆/照片识别；
   新增候选/确认/新登录/删除四次回答和源 ID。录屏按实际附件导出，目标非空
   会拒绝覆盖，调用后恢复环境；邀请码在画面中遮蔽，不修改业务返回。
7. **补齐参赛包装**：英语项目说明、实际架构、两账号评委指南、中文 UI
   英译表、逐项工具 Product Feedback、有来源摩擦记录、实时规则检查。
   修正 28/52 路径与 AWS 拒启动等入口文档冲突；视频规划目标改为 2:45–2:55。
8. **修复新宠保存后快速切页竞态**：服务已保存但 POST 返回较慢，用户先进入
   成长页时，小屋已卸载，原本仅设置小屋本地选择不能更新家庭当前宠物。
   保存现在直接使用变更响应快照，等待父级刷新后明确传递新宠 ID；不补多余 GET。
   测试刻意延迟真实响应，导航后才释放，原实现红灯，修复后通过。
9. **修复云清理假阳性与不可重试**：七类资源均有独立、有界读回，只有服务
   明确 NotFound 或准确空查询才确认不存在。权限/网络/超时不吞掉，失败保留
   state；已删除项在重试时也读回确认。ECS 使用已记录 ARN，区分删除/读取
   的不同缺失异常；日志组完整分页并精确匹配名称。全部只在离线 stub 中验证。
   当前计划若遗漏旧 state 登记项，删除开始前拒绝执行并保留全部 ID，不误删 state。
   既有部署脚本的 ECS 契约/失败后追踪问题仍待解决，不宣称可以直接部署。

## 新鲜验证

`scripts/verify.ps1`：**333 passed / 1 skipped / 21 deselected**（35.13 秒），
ruff、生成契约、TypeScript、build PASS；日志
`hackathon-verify-delivery-2026-10-03.log`。此前 297/330 项通过日志保留为阶段记录。
最后浏览器全量：**27 passed（46.8 秒，0 retries）**；日志
`hackathon-e2e-accepted-2026-10-03.log`。切页竞态修复后的前端类型与构建再次通过。
1 skipped 是具名的进程强杀尽力项，21 deselected 是未执行的真实 AWS 项。
初次全量浏览器抓到的失败与修复前后记录保留，不能引用初次结果声称全绿。

本轮 SDK 负向测试先复现 AgentCore 返回字段 2 failed、metadata 1 failed、
Strands 指标 8 failed，再修复；相关组 67 passed。报告来源回归先 1 failed、
修复后家庭组 33 passed。AWS 探活假阳性先 1 failed、修复后 app 组 7 passed。
以上均离线，不是云调用。

云清理初始 23 failed / 1 passed → 24 passed；再补重试恢复先 9 failed，修复后
清理组 33 passed；再复现旧 state 覆盖漏洞 3 failed → 修复后清理 36 passed、
相关 cleanup/deploy 纯逻辑组 46 passed。最终全量包含这些新项。
复跑曾遇旧 pytest 临时缓存 ACL 导致 72 个 fixture setup errors，已保留失败日志；
选择全新仓内 basetemp/temp 后得到最终全绿，未修改系统权限或用户资料库。

独立复核无未解决 P0/P1/P2，详见 [review](../reviews/hackathon-2026-10-03.md)。
原资料库未打开/清空，保留所有此前改动，未创建云资源、未推送、未发布或提交。

## 实际采集材料

- [主人原始录屏](hackathon-capture/2026-10-03-final/owner.webm)：1280×800，19.48 秒。
- [家人原始录屏](hackathon-capture/2026-10-03-final/carer.webm)：1280×800，19.40 秒。
- [实际结构化证据](hackathon-capture/2026-10-03-final/demo-evidence.json)。
- [采集清单与哈希](hackathon-capture/2026-10-03-final/sha256-manifest.json)。
- [小屋](hackathon-capture/2026-10-03-final/01-home.png)、
  [成长](hackathon-capture/2026-10-03-final/02-growth.png)、
  [新登录回答](hackathon-capture/2026-10-03-final/03-assistant.png)、
  [人工完成](hackathon-capture/2026-10-03-final/04-care.png)、
  [日报](hackathon-capture/2026-10-03-final/05-daily.png)、
  [删除后回答](hackathon-capture/2026-10-03-final/06-deleted-memory.png)、
  [可信完成者](hackathon-capture/2026-10-03-final/07-completing-actor.png)。

最后采集恰 **1 passed（25.0 秒）/ 0 retries**；七张截图以及两段视频抽帧已实际查看。
这是未减速、未配音的自动排练素材，适合核验与后续取镜头；不是三分钟成片。
31 个最终采集文件的大小与 SHA-256 全部匹配；候选未引用、确认后新登录引用、
删除后停止引用也再次核对。更早的 `2026-10-03-review` 采集保留未覆盖。

## 本地英文审核视频

[MP4 成片](submission-video-2026-10-03/local-review-02/pawtwin-local-review.en.mp4)：
**170.019 秒（2:50），1920×1080，H.264/AAC**。包含 11 个连续场景、两个真实
操作片段、离线英语 SAPI 配音与 22 句烧录字幕。owner 实际片段对应照护方案，
候选/记忆确认的说明使用真实确认结果截图并指向 JSON 证据。

实际 MP4 解码的 13 张帧全部查看；实际 AAC 解码为 170.017 秒，峰值 −5.533 dBFS，
0 截幅，最后有效音在 165.736 秒，22 句完整落在时段内。32 项产物及 13 项来源
的大小/哈希全部匹配。独立复核已修正 manifest 自哈希和动作片段错配两项 P2。
这证明实际容器、画面、字幕和音频信号，不等于人工全片听审/发音审校或公开发布。

[字幕](submission-video-2026-10-03/local-review-02/captions.en.srt) ·
[实际验证](submission-video-2026-10-03/local-review-02/verification.json) ·
[产物哈希](submission-video-2026-10-03/local-review-02/sha256-manifest.json) ·
[制作与重建指南](../submission/video-build-guide.md)。

## 赛事与下一门

候选 Build, Ship, Shape 提交截止 **2026-10-24 03:00 北京时间**。
Alexa+ 允许 AI/agentic 工具驱动的网页模拟；必须提供源码、测试说明、项目说明、
少于三分钟公开视频、工具反馈和英语材料/译文。公网 App 和真实家庭试用不是
统一必交项。公开仓须开源许可证，也可用规则规定的私有评委分享路线。
[官方规则](https://amazonappdev2026.devpost.com/rules) ·
[FAQ](https://amazonappdev2026.devpost.com/details/faqs)。

解锁方案、官方价格、Memory 成功证据与旧 smoke/deploy 缺口见
[云前置证据](cloud-preflight-2026-10-03.md)。本地源码安全导出见
[源码审阅导出](../submission/source-export-guide.md)；它包括未提交家庭扩展，
不包含用户数据库、凭据、Git 历史、依赖或构建输出，不能代替 GitHub 评委访问。

**当前云阻挡**：用户授权本次预算总额 **10 美元，服务范围不限**，随后确认
账户正在 Amazon 官方验证，约两天后才能使用服务。控制台也显示账户验证与
us-east-1 区域不可用。当前不继续探测/收费调用、不升级账户方案；本轮云调用、
创建资源和新增费用均为 0。账户可用后以短期本地凭据、确认单次模型价格、
严格限定次数与输出、实际 request_id/usage 先验证模型，然后补真实家庭 AI 接线。
AgentCore 成功提炼要关联新 record 与本次唯一事件事实，不能用 GetEvent 或只
枚举失败任务的 ListMemoryExtractionJobs 宣称成功。预算许可不等于账号/云接线通过。
发布/分享仓库/上传视频/参赛
提交需另行明确对外交付授权，见 [协作规则](../../AGENTS.md) 的 Cloud and publication。
不应为了 AWS Builder 附加挑战让核心演示和英语提交包装失去完成余量。

入口：[英语项目说明](../submission/project-description.en.md)、
[评委复现指南](../submission/judge-guide.en.md)、
[工具反馈](../submission/product-feedback.en.md)、
[规则核查](../submission/rules-check-2026-10-03.md)、
[录屏指南](../submission/capture-guide.md)。
