# 2026-10-11 比赛检查与当前 demo

**本地功能、复现材料和展示成片完成本轮验收；正式提交仍有外部交付门。** 检查的是完整当前工作区，基线 `31da349 / chore/bootstrap` 加现有未提交功能；保留原数据库、既有 8807 服务和历史产物，没有重置、切分支、推送、上传或提交。

## 官方要求与状态

2026-10-11 实时核对 [官方规则](https://amazonappdev2026.devpost.com/rules)、[首页](https://amazonappdev2026.devpost.com/) 和 [FAQ](https://amazonappdev2026.devpost.com/details/faqs)。截止 **2026-10-23 12:00 PDT / 北京时间 2026-10-24 03:00**。完整依据见 [当前规则清单](../submission/rules-check-2026-10-11.md)。

| 要求 | 本轮结果 / 剩余门 |
|---|---|
| Alexa+ 网页模拟路径 | 官网、家庭 App、独立模拟器与原工作台可运行；规则允许模拟与 AI/agentic 工具。Codex 开发/复核有记录，实际展示 local_rules；最终路径及工具申报需本人确认 |
| 英文材料 | [项目说明](../submission/project-description.en.md)、[评委指南](../submission/judge-guide.en.md)、[当前 runbook](../submission/demo-runbook-2026-10-11.md) 已完成；中文 UI 有英语操作对应 |
| 少于 3 分钟的视频 | 当前英语成片170.0185034秒，带字幕；还需人工全片播放/听审及公开 YouTube/Vimeo 链接 |
| GitHub 评审源码访问 | 完整工作区可安全导出；无 remote、未选择 LICENSE。正式提交需公开仓库与开源许可，或规定的私有评审访问 |
| 工具反馈 | [实际工具/摩擦记录](../submission/product-feedback.en.md) 已更新；本人 reuse Yes/No 和个人上手体验不能代填 |
| 资格、报名、素材权利、最终申报 | 需本人核对与确认，不能从项目文件或所在地推定 |
| AWS Builder | 可选；离线适配器测试不证明实际 AWS 使用，本轮不宣称达标 |

公开托管 App、真实 Alexa 设备或付费云部署不是模拟路径强制要求；GitHub 访问和公开视频仍须落实。

## 修复与独立复核

| 经复现问题 | 改动与证据 |
|---|---|
| 不同 pending 喂食共享旧额度并发执行 | 持久 owner 执行门闩；SQLite 同一写事务读取当前事实/硬策略并绑定方案版本和状态。两个独立文件连接竞态仅一次设备调用 |
| 未知回执/中断后可能重复批准 | 未知结果保留门闩，重启和事实重置不解除；失败不记账并释放，成功只记一次；旧未知/执行中请求也阻止新批准 |
| 迟到同状态重评覆盖已完成请求 | 完整 pending 重评写入原子绑定旧 proposal version 与 pending 状态，保留已完成状态和回执 |
| 回执提交后后续保存崩溃留下 EXECUTING | 回执、终态、成功额度、门闩释放同事务；模拟后续 save_run 异常仍保留可恢复终态 |
| 原始 X-Forwarded-For 绕过登录/注册限流 | API仅用服务器解析的peer IP；三个本地脚本与Playwright显式 --no-proxy-headers，实际Uvicorn配置和认证回归覆盖 |
| Dynamo 旧 facts 没有安全 guard | 未迁移旧记录拒绝批准，新事务绑定 facts version/guard、owner 门闩和 saved run；只离线事务形状检查/静态复核，无AWS调用 |
| 旧展示没有新版官网/独立模拟器 | 重新双账号采集，用当前实测截图编排英语视频；保留原始WebM，不套用旧剪辑时点 |

协调者写入代码，repair_review 独立只读复核无本轮剩余阻断项，独立定向 reservation 11项通过。未来代理部署需限制 Uvicorn forwarded-allow-ips 并核对代理转发链，不能仅用 PAWTWIN_TRUST_PROXY_HEADERS=true 建立客户端身份边界。Dynamo旧数据需单独审计迁移，本轮未做云迁移。

## 最终验证

| 检查 | 实际结果 |
|---|---|
| ./scripts/verify.ps1 | **393 passed / 1 skipped / 21 live AWS deselected**，55.41秒；Ruff、生成契约、TypeScript、生产构建全部通过。[日志](submission-readiness-2026-10-11/verify.log) |
| ./scripts/test-e2e.ps1 | **42 passed，1.4分钟，0 retries**；权限、批准/拒绝/失败/未知、记录修改、Alexa闭环、320/390/1440、键盘/减少动画。[日志](submission-readiness-2026-10-11/e2e.log) |
| 独立定向复验 | python -B -m pytest tests/test_feeding_reservation.py -q -p no:cacheprovider →11 passed |
| 专用展示采集 | 1 passed，39.7秒；14实际PNG、owner/carer WebM、schema2 JSON。[日志](hackathon-capture/2026-10-11-final/capture.log) |
| 实际MP4/AAC解码 | 1920×1080 H.264/AAC，170.0185034秒，26句、13实际帧，字幕无溢出，句子均落入分镜；peak −5.203dBFS，clipped samples 0 |
| 画面复核 | 实际13帧contact sheet与局部大图已查看，英语标签/字幕及当前操作可见；人工全片播放/听审尚未执行 |

跳过项为 test_kill_a_running_server_mid_analysis_then_relaunch：默认不执行易受端口/启动时序影响的强杀uvicorn场景；已有两个子进程/逻辑恢复检查不等于该项执行。21个实时AWS检查由默认选择器排除，不能计入通过。另有一条Starlette/AnyIO上游弃用提示。

首次浏览器复验发现两条过期状态文字断言，已按实际诚实标签修正。未知回执测试最后运行，避免共享服务被有意保留的未知门闩影响；没有用事实重置绕过执行保护。

## 当前 demo 与材料

- 本机 [官网](http://127.0.0.1:8816/)、[App](http://127.0.0.1:8816/#app)、[Alexa模拟器](http://127.0.0.1:8816/#alexa)。内置浏览器已打开虚构演示家庭；loopback地址仅本机可访问。
- 独立新库 data/judge-demo-2026-10-11.db 和 .family.db，原数据和8807服务保留。[当前截图](submission-readiness-2026-10-11/live-app.jpg)、[服务状态](submission-readiness-2026-10-11/preview.json)。账号/家庭/体重/偏好均为虚构fixture，测量为demo_sample。
- 新机器先setup/build，再 ./scripts/dev-home.ps1 -Port 8816 -DatabasePath ./data/judge-demo-02.db；每次清洁排练选新库路径。
- [最新英语MP4](submission-video-2026-10-11/local-review-01/pawtwin-local-review.en.mp4)、[字幕](submission-video-2026-10-11/local-review-01/captions.en.srt)、[解码检查](submission-video-2026-10-11/local-review-01/verification.json)、[视觉复核](submission-video-2026-10-11/local-review-01/visual-review.json)、[制作指南](../submission/video-build-guide.md)。MP4 SHA-256：07332b9aa6e1b17023a53152aae8700931ceab0446d36af9e7d28e64294235e3。
- [真实采集证据](hackathon-capture/2026-10-11-final/demo-evidence.json)：候选不入答→确认→新登录/新页面会话复用及来源→草案→准备→明确确认→另一成员人工完成→日报→删除后新回答不引用。样例1.20→1.35kg，跨度7天，150g/12.5%；不把出粮当摄入。
- [当前完整源码包](../../../pawtwin-review-2026-10-11.zip) 与 [整包/逐文件清单](../../../pawtwin-review-2026-10-11.manifest.json)。[导出器](../../scripts/export-review-source.py) 读取完整dirty工作区并回读CRC、逐文件SHA-256及必需文件，外置清单记录实际归档字节；排除数据库、依赖、缓存和凭据。

展示固定local_rules，照片模型关闭，云调用0。家庭Bedrock网关已接线/离线测试，真实调用/质量/延迟未验证；记忆为主人确认SQLite数据，设备/传感器/Alexa为模拟。

## 正式提交前

1. 本人完整播放/听审视频，确认资格、权利、主路径与工具申报，补reuse Yes/No与理由。
2. 选择公开许可或私有评审访问，授权发布完整源码到GitHub并核对访问。
3. 授权上传英语MP4为公开YouTube/Vimeo视频，填入有效链接。
4. 截止前完成Devpost表单、条款与提交，核对链接与状态。当前没有正式提交。
