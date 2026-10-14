# 本地源码审阅导出

此导出用于检查当前工作区，不代表已发布 GitHub 仓库、已授予开源许可或已正式提交。
仅检出 `31da349` 不包含本地家庭扩展；导出同时包含已修改文件和未忽略的新文件。
源码、测试、生成契约、锁文件、脚本、英文材料与实际证据必须一并审阅。

在项目根执行：

```powershell
uv run --frozen python scripts/export-review-source.py ../pawtwin-review-2026-10-11.zip
```

输出必须在 checkout 外，ZIP 或清单已存在时拒绝覆盖；下一次选择新的文件名。
脚本使用 Git 的 tracked/nonignored 文件清单，不复制 `.git`、依赖、构建结果、
用户数据库、缓存或私密凭据路径；大小写变体也拒绝。`.env.example` 仅包含占位符。
明确补入忽略规则排除的本轮通过日志与实际采集日志。原工作区不移动、不清空。

ZIP 顶层 `pawtwin-app/` 为实际源码；`REVIEW_EXPORT_MANIFEST.json` 记录起点 HEAD、
分支以及每个归档文件的大小/哈希。相邻 `.manifest.json` 另外记录整个 ZIP 的 SHA-256。
脚本回读 ZIP 验证 CRC、每个文件的实际哈希及家庭扩展必需文件，才输出成功。
它不包含 Git 历史；本地验证依赖按照锁文件重新安装。

独立审查已复核路径大小写与家庭运行文件门禁，见
[复核记录](../reviews/hackathon-2026-10-03.md)。实际包路径与最终验证结果见
[本轮完整验收](../evidence/submission-readiness-2026-10-11.md)。

后续 GitHub 上传需保留全部当前源码，再选择公开许可证或官方要求的私有分享。
此 ZIP 是本地审阅文件，不能代替规则要求的评委源码访问。

2026-10-11 导出门禁还要求当前官网、独立 Alexa 组件/样式/浏览器排练、family_assistant.py/离线 Bedrock 测试、当前英文 demo runbook 及 `docs/evidence/submission-readiness-2026-10-11/verify.log`、`e2e.log`。明确补入本轮 verify/e2e/rehearsal 日志、所有采集 capture.log 和各日期 submission-video 的 build.log；新成片与当前采集文件跟随 Git tracked/nonignored 清单。导出前完成本轮验证与视频检查，重新使用新ZIP文件名，避免把旧84MB快照当当前版本。导出包含私有机器路径与虚构临时账户活动证据，分享前审阅。此ZIP没有Git历史，可重新安装并运行App，但重新导出本身需要Git检出。
