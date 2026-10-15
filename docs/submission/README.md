# 参赛材料准备区

## 当前入口 142秒最终本地材料

[最终材料入口](2026-10-15/README.md)统一使用`PawTwin-hackathon-submission-2026-10-15.en.mp4`（142.379秒），对应最终英文Word、完整源码ZIP和材料ZIP；身份与哈希见最终包外置manifest及[修复验证](../evidence/submission-repairs-2026-10-15/verification.json)。2026-10-16完成本地代码验收：495 backend与122 browser通过，Ruff/契约/类型/生产构建通过。下方150/170秒成片及其ZIP均为保留的历史版本。

## 2026-10-15 优化版展示视频

[优化版视频与核验记录](2026-10-15/video-optimization-v2.md)：150.2583 秒、1080p、24 fps，扩大实际界面画面，加入动态特写、转场、自然英文旁白和原创轻音乐；约 101.8 秒正常速度的实际界面片段（包含阅读停留），28 句字幕。关键操作、实际解码画面与音轨已复核，完整人工播放听审仍待完成；上一版保留。[最新材料入口](2026-10-15/README.md)。

## 2026-10-15 英文提交文档与家庭照护展示视频

[本轮材料总入口](2026-10-15/README.md)：六页可编辑英文 Word，Devpost 英文介绍、评委运行指南、工具反馈草稿与提交清单；首版 170.0185 秒 1080p 英文 MP4，配音和 26 句烧录字幕，包含 58.8 秒当前英文界面的实际操作片段。展示家庭协作、确认记忆、人工照护、日报、临时只读访问和就诊卡。文档逐页与实际视频解码画面已复核，完整人工听审及公开上传仍待本人完成；旧材料保留。

[视频制作及核验说明](2026-10-15/video-production.md)。实际展示为本地规则、SQLite、Alexa 网页模拟与虚构家庭，不宣称真实云服务或硬件。个人 Product Feedback、资格/权利、源码评审访问和正式提交仍需完成。

## 2026-10-12：英文比赛演示视频

[新版视频与完整制作/核验说明](demo-video-2026-10-12.md)：170.0185034秒、1080p H.264/AAC，英文旁白与26句烧录字幕；8段实际录屏1×共18.4秒，其余实际结果截图停留。37实际解码帧/字幕/音轨检查通过，完整人工播放听审待本人完成；旧版保留，没有上传或提交。


## 当前交付（2026-10-11）：比赛准备与当前 demo

- [最新验收与剩余提交门](../evidence/submission-readiness-2026-10-11.md)：393 backend / 42 browser通过，1 skipped / 21 live AWS deselected，独立复核通过。
- [当前规则](rules-check-2026-10-11.md)、[英语说明](project-description.en.md)、[评委指南](judge-guide.en.md)、[实际工具反馈](product-feedback.en.md)。
- [当前runbook](demo-runbook-2026-10-11.md)、[14PNG/双账号采集](../evidence/hackathon-capture/2026-10-11-final/demo-evidence.json)。
- [新版2:50英语MP4](../evidence/submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4)、[字幕](../evidence/submission-video-2026-10-11/local-review-01/captions.en.srt)、[实际解码检查](../evidence/submission-video-2026-10-11/local-review-01/verification.json)、[视觉复核](../evidence/submission-video-2026-10-11/local-review-01/visual-review.json)。完整人工听审未执行。
- [完整当前源码导出指南](source-export-guide.md)，包含现有未提交功能，排除用户数据、依赖和凭据。

本机展示http://127.0.0.1:8816/，App与/#alexa使用独立虚构样例库。模拟路径不强制公开托管App；仍需GitHub评审源码访问、公开YouTube/Vimeo视频、本人工具反馈与资格/权利/最终申报。本轮无云调用。下方10/3内容为历史记录。

本目录保存本地展示与参赛材料草稿，已有英语审核视频；公开视频与正式提交尚未完成。
2026-10-03 已实时复核候选 Build, Ship, Shape 规则：Alexa+ 允许 AI/agentic 网页模拟，
当前 local_rules 的技术适配仍需确认；AWS Builder 是需实际使用证据的可选附加挑战。
最终报名与个人资格未确认，2025 示例保留为历史参考。

## 本轮补齐入口

- [完整度评估、修复与实测](../evidence/hackathon-completeness-2026-10-03.md)。
- [英语项目说明与实际架构](project-description.en.md)。
- [英语评委运行与检查手册](judge-guide.en.md)。
- [实际工具 Product Feedback 与摩擦记录](product-feedback.en.md)。
- [当前规则与发布前清单](rules-check-2026-10-03.md)。
- [当前源码的安全审阅导出](source-export-guide.md)，包含未提交的家庭扩展。
- [可复现录屏采集](capture-guide.md)，[最终实际源证据](../evidence/hackathon-capture/2026-10-03-final/demo-evidence.json)。
- [2:50 本地英文审核 MP4](../evidence/submission-video-2026-10-03/local-review-02/pawtwin-local-review.en.mp4)，
  [对齐该成片的字幕](../evidence/submission-video-2026-10-03/local-review-02/captions.en.srt)，
  [制作/重建指南](video-build-guide.md)。170.019 秒、真实操作片段和结果截图、英语 SAPI 配音；
  实际解码帧/音轨与哈希已核验，尚未人工全片听审或上传。
- [2:55 英语旁白/字幕草稿](narration.en.srt)：按规划时间轴编写，尚未对齐原始快速录屏，也未烧录成片。

实际 WebM 是无声自动排练原素材；新 MP4 是带配音/字幕的本地审核成片，尚未上传为正式视频。源码访问、
个人工具反馈、报名资格、许可/私有分享和正式提交仍是外部交付门。

## 既有材料记录

当前需求以 [附加计划](../plans/PawTwin_附加开发计划_2026-10-02.md) 为准；材料任务 EXT-12，真实 AWS 宣称需要 EXT-10 证据。账号/统计/规则分身已本地实现；真实云接入待开发/验收。英文初稿/演示脚本/空白试用表见 [demo guide](extension-demo-guide.md)，没有用户反馈或已拍视频宣称。
材料展示家庭协作、记录改变个体回答、跨会话记忆与受控行动；真实/模拟/未验证分列。
2026-10-03 追加：[功能复验（284 后端 / 27 浏览器）](../evidence/functional-check-2026-10-03.md)、[中文展示方案（3 分钟视频 / 5 分钟现场）](PawTwin_展示方案_2026-10-03.md)，包含操作顺序、分镜、演示数据、当前边界与临场恢复；视频仍待录制。
参考：[官方规则](https://amazonappdev2026.devpost.com/rules)、[主办方说明](https://amazonappdev2026.devpost.com/updates/46456-got-an-idea)。

完成 QA 后在此整理：英文项目说明、真实/模拟/路线图、架构、真实测试结果、视频与测试访问说明。口令不提交到公开仓库，正式提交前再次核对比赛要求。
