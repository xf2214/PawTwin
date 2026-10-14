# 黑客松完整度补齐执行记录

2026-10-03；用户授权「评价当前项目的完整度，并将不完整的地方补齐」。
目标是交付可检查、可复现的本地原型和参赛准备材料，保留现有工作区。
基线 HEAD 31da349 / chore/bootstrap，包含此前未提交家庭扩展与排练。

## 验收与认领

| 工作 | Owner | 写路径 | 验收 |
|---|---|---|---|
| 当前规则/材料缺口审计 | submission_audit（先只读） | 分配后仅 docs/submission/judge-guide.en.md、project-description.en.md、product-feedback.en.md、rules-check-2026-10-03.md | 与官方规则、当前实现、实测一致；不编造工具使用经历 |
| 核心审计与实际缺陷 | core_audit | agentcore_client.py、bedrock_client.py、growth.py 与对应 tests；追加 scripts/cleanup_aws.py、对应清理 tests 和 cloud-preflight 文档 | SDK 返回/请求、预算遥测、报告来源与真实清理读回语义的离线红绿回归；不执行云操作 |
| 演示审计与交付 | demo_audit | scripts/capture-demo.ps1、docs/submission/capture-guide.md；后续实际竞态修复 FamilyApp/PetHome/family.spec.ts | 隔离采集；保存新宠后快速导航仍保留选择 |
| 演示证据/整体验证/整合 | Codex coordinator | main.py/config.py/test_app.py、.gitignore、playwright.config.ts、demo-rehearsal.spec.ts、docs/evidence/hackathon-*、docs/reviews/hackathon-*、STATUS/TASKBOARD/README/索引、英语字幕与本地源码压缩包 | 完整云标记不因探活升级；全量验证；检查视频和来源证据 |

## 范围与方案

- 沿用现有五入口和双账号排练；补充新会话更新前后证据、录屏和复制导出命令，不引入新系统。
- 录屏是实际本地自动排练素材，必须区别于已剪辑配音、英文字幕、公开视频和正式提交。
- 推荐主路线是 Alexa+ 网页模拟候选；当前 local_rules 的 AI/agentic 证据弱，技术门槛仍需审核。AWS Builder 的真实云验收保持未完成。
- 准确记录最新规则：视频必须少于三分钟；源码仓、英语材料、Product Feedback 和评委测试说明不可遗漏。
- 用户随后授权本次云服务总预算 10 美元、服务范围不限；再确认账户官方验证约两天，故本轮暂停云调用。未发布/推送/提交、未覆盖原用户数据库、未变更许可授权。公开或私有共享仓的选项待最终对外交付时裁定。
- 不将后台自动化、截图、模板或模拟数据说成真实用户试用。

## 执行检查

- [x] 读取协作规则、当前未提交状态与既有证据。
- [x] 三路独立只读审计，实时核对官方规则。
- [x] 补齐英文材料及评委复现说明。
- [x] 补齐录制、结构化证据和当前完整度评估。
- [x] 修复 SDK 契约/遥测、报告来源与探活宣称缺口。
- [x] 修复全量浏览器回归抓到的新宠保存后快速导航竞态；延迟响应确定性红绿测试。
- [x] 全量本地验证：333 后端 passed / 1 skipped / 21 deselected，27 浏览器 passed，ruff/契约/TS/build PASS。
- [x] 独立复核 SDK、状态、报告和初次采集；最后 UI 变更追加复核。
- [x] 修复云清理读回假阳性，权限/网络错误保留失败与原 state；重新全量 verify。
- [x] 完成本地英文演示视频及源码导出脚本，记录质量与发布边界；2:50 MP4 与实际帧/音频/哈希核验通过。
- [x] 更新最终材料状态、全部新链接；源码归档最终文件哈希由导出脚本与外部 manifest 记录。

首次 verify 在受限运行环境遇到 uv cache / pytest 临时目录权限问题；改用仓库内隔离 cache/temp 后复验，不将环境错误归为产品失败。
