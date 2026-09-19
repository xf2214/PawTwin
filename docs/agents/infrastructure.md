# 云部署 Agent 起始任务

先读 `AGENTS.md`、`docs/STATUS.md`、`docs/TASKBOARD.md`，认领 OPS-01。当前没有 AWS 账号和部署授权。

先验证本地工具、容器构建与部署输入。默认设计为单容器 FastAPI/React、ECS Express Mode、Bedrock、DynamoDB、AgentCore Memory；执行时查官方当前可用性与实际区域/权限，不照搬历史服务假设。

交付可审查的角色权限、项目资源清单、具体费用估算、预检/部署/清理流程。先 plan-only，再在用户确认具体费用范围后 apply。现有 bootstrap 不包含真正可用业务，不能作为正式比赛网址对外发布。

不要改用户系统代理、全局工具或账号设置；缺 Docker/AWS CLI 时报告并给安装选择，不静默安装。不要索要聊天中的长期密钥。凭据通过本地登录或短期角色使用。

所有资源带项目标识，清理先列出精确资源再删除；预算提醒不等于停止计费。报告 Docker 构建和真实 AWS 验证是否实际运行。
