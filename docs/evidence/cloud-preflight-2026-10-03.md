# AWS 云验证前置证据（2026-10-03）

状态：**CLOUD BLOCKED — AWS 账户仍在官方审核，真实云验证尚未执行。**

用户本轮已授权真实云验证，**总费用上限为 10 美元，服务范围不限**。随后用户确认账户还在官方审核，预计约两天后可用；这是用户提供的预期，并非 AWS 保证的完成时间。账户解锁前暂停全部 AWS 账户调用、资源创建和收费动作；预算授权继续有效，不需要重复申请。

本记录仅包含公开官方资料、公开无签名价目表读取、离线 SDK service shape 和本地脚本审阅。没有读取凭据、发起账户 SDK 请求、调用模型、创建或删除云资源。账户可用性、IAM 授权、服务配额、真实响应和实际账单均未验证。本记录不实施新的生产接线或部署。

## Nova Lite v1：区域、模型 ID 与当前公开价格

最小验证候选为 `us-east-1`（US East / N. Virginia）的 **Amazon Nova Lite v1**。官方模型卡列出该区域支持 in-region 和 US geo cross-region；模型生命周期显示 Active。文档支持不等于本账户已可调用，解锁后仍须实测。[官方模型卡](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html)

| 用途 | 标识 |
|---|---|
| 区域内 `bedrock-runtime` | `amazon.nova-lite-v1:0` |
| 美国跨区域 inference profile（可选） | `us.amazon.nova-lite-v1:0` |
| 本次首选端点 | `https://bedrock-runtime.us-east-1.amazonaws.com` |

本次先选区域内标准按需推理。Nova Lite v1 模型卡未支持 Global inference ID；不要自行构造 `global.amazon.nova-lite-v1:0`，也不要把 **Nova 2 Lite** 的标识或价格混入此估算。[官方程序访问与区域表](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-lite.html)

2026-10-03 通过无签名 HTTP GET 读取 AWS 公开 **AmazonBedrock / us-east-1** 价目表，筛选 `model = Nova Lite`、`feature = On-demand Inference`、`regionCode = us-east-1`。读取成功；没有使用 AWS 账户客户端。[官方区域价目表 JSON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json)；[Bedrock 定价入口](https://aws.amazon.com/bedrock/pricing/)

| 标准按需项目 | USD / 1,000 tokens | USD / 1,000,000 tokens | 价目表 SKU |
|---|---:|---:|---|
| 输入 token | 0.00006 | 0.06 | `QRGWJ3P8FT28EYX2` |
| 输出 token | 0.00024 | 0.24 | `CBZ6A6U7XK8WJ3KA` |

公开价目表元数据：`offerCode = AmazonBedrock`、`publicationDate = 2026-10-03T00:11:38Z`、`version = 20261003001138`；上述两个条目的 `effectiveDate = 2026-10-01T00:00:00Z`，单位均为 `1K tokens`。本估算不使用 batch、缓存折扣、定制模型或预置吞吐价格。实际执行当天应再核对价目表和选定模型 ID。

访问仍需要有效的账户及 IAM 授权：区域内 Converse 需要 `bedrock:InvokeModel`；如走流式接口还需要 `bedrock:InvokeModelWithResponseStream`。跨区域 profile 还需要覆盖 profile 及目的区域模型的权限。Amazon 模型不属于 AWS Marketplace 有 product ID 的第三方模型；不要机械套用 Anthropic 首次使用表单或第三方模型订阅流程。[模型访问说明](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)；[Converse 权限](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)；[跨区域推理权限](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)

## AgentCore Memory：计费单位与区域

官方区域表列出 `us-east-1` 支持 AgentCore Memory；本账户授权和服务访问仍待解锁实测。[AgentCore 区域表](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html)

| 项目 | 公开 USD 价格 | 计费边界 |
|---|---:|---|
| 短期 raw event | 0.25 / 1,000 新事件 | 按 CreateEvent 请求计费 |
| 内置策略长期记录 | 0.75 / 1,000 records / 月 | 包含自动提炼；存储按小时计费，以 31 天月折算 |
| 内置策略 override / self-managed 长期记录 | 0.25 / 1,000 records / 月 | 另可能产生客户账户内的模型费用 |
| 长期记忆检索 | 0.50 / 1,000 检索请求 | 按 retrieval calls 计费，不按一条响应返回的 record 数量计费 |

以上来自当前 [AgentCore 官方定价页](https://aws.amazon.com/bedrock/agentcore/pricing/)。该页没有为短期 raw event 单列额外的 GB-month 存储费，不应自行添加一个费率。最小验证选择内置策略，避免把内置自动提炼再次按客户侧 Bedrock 模型调用计费。CloudWatch 观测费用另计；估算不假设免费额度或抵扣券。

最小流程需要限定专用 Memory 的控制面 CreateMemory / GetMemory / DeleteMemory，以及数据面 CreateEvent / RetrieveMemoryRecords；若检查失败提炼，则需要 ListMemoryExtractionJobs。具体 IAM resource scope、策略状态和配额须在解锁后核对；本轮没有授予权限。[Memory API 权限索引](https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock-agentcore.html)

## 提炼完成证据：SDK 与官方 API 的真实边界

离线实际检查环境：`boto3 == 1.43.102`、`botocore == 1.43.102`、`strands-agents == 1.57.0`。读取安装包 service model，无客户端、无网络请求、无凭据解析。

```python
from importlib.metadata import version
import botocore.session
service = botocore.session.Session().get_service_model("bedrock-agentcore")
op = service.operation_model("ListMemoryExtractionJobs")
job = op.output_shape.members["jobs"].member
print(version("botocore"))
print("GetMemoryExtractionJob" in service.operation_names)
print(op.input_shape.members["filter"].members["status"].enum)
print(job.members["status"].enum)
print(list(job.members["messages"].members["messagesList"].member.members))
```

本次实际输出：`1.43.102`、`False`、`['FAILED']`、`['FAILED']`、`['eventId', 'messageIndex']`。

| 离线 service shape | 结果 |
|---|---|
| `ListMemoryExtractionJobs` | 存在；输入 `memoryId, maxResults, filter, nextToken`，输出 `jobs, nextToken` |
| `filter` | `strategyId, sessionId, actorId, status`；`status` 枚举仅 `FAILED` |
| `jobs[]` | `jobID, messages, status, failureReason, strategyId, sessionId, actorId`；`status` 枚举仅 `FAILED` |
| `jobs[].messages.messagesList[]` | `eventId, messageIndex`，可以准确关联失败事件 |
| `GetMemoryExtractionJob` | 锁定 SDK 不存在此 operation |
| `GetEvent.event` | 只有事件数据及 metadata，没有提炼 `status` / `state` |

官方 ListMemoryExtractionJobs 的含义是列出可重新启动的提炼任务，CLI 文档的 filter 和输出枚举也只有 `FAILED`。**它能证明某 eventId 的失败，不能证明成功；任务列表为空也不能推出提炼完成。** GetEvent 返回原始事件存在同样不能证明长期记忆已生成。[官方 API](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_ListMemoryExtractionJobs.html)；[官方 CLI 枚举](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore/list-memory-extraction-jobs.html)；[GetEvent 响应](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_GetEvent.html)

当前 adapter 对没有官方状态的提炼查询明确返回 `EVENT_EXTRACTION_STATUS_UNSUPPORTED`。本前置记录不扩展业务协议，不伪造 processed，也不采用永久盲轮询。

内置提炼是异步流程，应先确认 Memory strategy 为 `ACTIVE`，再提交事件。最小隔离探针可用全新 actor / namespace、含唯一标记的事实、空检索基线，以及随后真正 RetrieveMemoryRecords 返回的新 record ID 和对应内容，证明该探针产生了可在新 session 检索的长期记忆。这只是隔离验证证据，不是现有共享 namespace 下任意 feedback 的通用成功状态。[官方保存与检索流程](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html)

若业务以后要求准确关联单条 feedback，需设计真实 record 关联证据。官方 strict-consistent metadata schema 可把声明的事件字段精确传入长期记录；用于筛选的字段还需 indexedKeys。未声明字段不会自动复制。本轮仅记录此候选方案，没有修改 schema、协议或生产接线。[官方长期记忆 metadata](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-memory-metadata.html)

## 既有 smoke 与部署脚本的云验收边界

本节来源为当前 checkout 的只读审阅，未运行 smoke：

| 文件 | 阻止完整证据或预算保证的缺口 |
|---|---|
| `scripts/bedrock_smoke.py:41,57,77,97` | 直接调用 BedrockAgent，绕过应用结果守卫；仅打印调用数、输出 token 和截止时间。当前 Strands metrics 不提供脚本期待的 request ID，通常只能显示 `NOT RETURNED BY SDK`。没有美元累计上限或输入 token 限额，也没有外层硬截止；输出 token 的 Strands 限制是回合边界软限制，不能据此保证不超总量。 |
| `scripts/agentcore_smoke.py:40,43,51,81` | 提交后立即检索一次；未等待 strategy ACTIVE，未做与新事件关联的提炼证据，固定 demo namespace 可能命中历史记录，空结果也返回 0。打印的 namespace 少了实际 `/owner/.../pet/...` 路径，未保存 AWS request ID、未设美元上限，提交事件后没有清理。 |
| `scripts/bedrock-smoke.ps1`、`scripts/agentcore-smoke.ps1` | wrapper 可保存 exit 0 的文本报告，但未增加累计美元预算、调用次数或清理验收。 |
| `scripts/cleanup_aws.py` | 本轮离线修复：全部 7 类资源删除后都必须有界读回确认；仅接受各服务已核实的不存在错误码，权限、网络或其他错误继续失败并保留 state。日志组完整分页、精确匹配名称；ECS 仅使用已记录 service_arn，缺失时拒绝执行。删除请求自身 NotFound 允许重试，但仍必须独立读回，不提前宣称成功。真实云清理尚未执行，宽范围 teardown 仍不代替隔离探针的清理方案。 |
| `scripts/deploy_aws.py:302,305,342` | **部署仍有阻挡缺陷，未修复。** 锁定 SDK 的 ECS Create/Describe 返回值在 `response.service`，当前脚本却读取顶层 serviceArn / statusCode；Describe 还错误传 serviceName，而 SDK 必填 serviceArn。这可能造成等待失败或无法记录真实 ARN；账户通过审核不代表此脚本即可部署。 |
| `scripts/deploy_aws.py:145,399` | **失败后的资源追踪风险，未修复。** `_apply` 仅在内存累积资源，主流程等全量创建成功才写 deploy_state.json；中途失败可能留下已经创建、但未落盘追踪的资源。本轮不部署、不猜 ID、不扩展部署修改范围。 |

清理 SDK 契约核实为 botocore 1.43.102：ECS Delete 的不存在码是 `ServiceNotFoundException`，Describe 则是 `ResourceNotFoundException`；IAM GetRole / GetOpenIDConnectProvider 的 wire error code 是 `NoSuchEntity`（不是 exception shape 名 `NoSuchEntityException`）；AgentCore GetMemory / DynamoDB DescribeTable 为 `ResourceNotFoundException`，ECR DescribeRepositories 为 `RepositoryNotFoundException`。CloudWatch DescribeLogGroups 无专用 NotFound，必须遍历分页且目标全名不存在才可确认。[ECS Delete](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeleteExpressGatewayService.html)；[ECS Describe](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeExpressGatewayService.html)；[IAM GetRole](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetRole.html)；[IAM GetOIDC](https://docs.aws.amazon.com/IAM/latest/APIReference/API_GetOpenIDConnectProvider.html)；[GetMemory](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_GetMemory.html)；[DescribeTable](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_DescribeTable.html)；[DescribeRepositories](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_DescribeRepositories.html)；[DescribeLogGroups](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DescribeLogGroups.html)

ECS `service.status.statusCode` 仅有 ACTIVE / DRAINING / INACTIVE；本轮清理不把 INACTIVE 单独当成不存在。Express 管理的共享资源可能保留，因此读取确认覆盖的是 state 登记的资源，不能声称 AWS 账户全部基础设施零残留。[ECS 状态](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ExpressGatewayServiceStatus.html)；[Express 删除与共享资源保留](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-delete-task.html)

本轮 TDD：有效初始复现 23 failed / 1 passed，最小修复后 24 passed；追加部分成功重试用例先 9 failed / 24 passed，修复后清理回归 33 passed；再补旧 state 未被当前计划覆盖的 3 failed，修复后清理回归 **36 passed**，连同部署纯逻辑/计划测试共 **46 passed**。destroy 开始前必须确认全部非空 state 登记项都被当前 delete_order 与类型映射覆盖，否则保留原 state，任何资源都不开始删除。测试使用 SDK Stubber 校验请求，禁用网络发送，只操作专用 `.cache` 测试目录中的 state；没有运行真实 `--destroy`。最终全量 verify 333 passed / 1 skipped / 21 deselected，真实云验证仍为 BLOCKED。

Strands 的真实汇总字段是 `cycle_count` 与 `accumulated_usage`；`Limits.output_tokens` 为软限制。[官方 metrics](https://strandsagents.com/docs/api/python/strands.telemetry.metrics/)；[官方 Agent / Limits](https://strandsagents.com/docs/api/python/strands.types.agent/)。此处记录剩余缺口，不改既有 smoke 或 deploy 文件；cleanup 的离线修复已另行完成。

## 解锁后的最小验证步骤（尚未执行）

1. 由用户确认 AWS 官方审核已经完成；采用本地短期授权，核对 us-east-1 的 IAM 和所选服务访问。仅凭环境变量存在不能视为解锁。
2. 实施测试级的固定模型、固定短输入、每次 maxTokens、累计调用/检索次数及费用估算守卫，再执行任何收费请求；显式限制重试并计入全部尝试。先单次区域内 Nova Lite Converse，保存真实 `ResponseMetadata.RequestId`、选定 model ID、usage 和时间；随后单独验证 Strands / 工具调用路径及应用守卫。
3. 创建并记录本次专用临时 Memory ID，配置一种内置长期策略；有界等待 strategy ACTIVE。使用全新 actor / namespace，提交一条唯一事实并保存 event ID、session ID 和 request ID。
4. 有界检索直到拿到实际新 record ID 和事实内容；在新 session 再检索。检查 FAILED jobs 的 eventId 仅用于记录失败。超时或空结果应报告未证实，不能标记提炼成功。
5. 只清理本次创建并登记的资源，finally 中发起专用 Memory 删除；有界读回确认明确 ResourceNotFound。其他异常保留为清理未证实。保存无凭据证据及费用记录，核对延迟到达的账单。

以上步骤仍受本次 **10 美元总授权**约束。这里的守卫要求是待实现的执行前置条件，并非宣称既有 smoke 已具有硬预算。最小探针无需部署 Runtime、ECS、DynamoDB、S3 或自动开启云观测；若后续引入其他服务，其费用也必须计入同一个总额。

## 费用估算（场景计算，非实际账单或硬成本保证）

按今日区域按需价格估算一个小探针，预留最多 8 次模型收费请求，每次最多 16,000 输入 token、800 输出 token；最多 2 个 raw events、40 次长期检索。为存储保守估算，假设最多 100 条内置长期记录并计算完整 31 天月费用，即使计划及时清理。内置提炼记录数是此估算假设，需要观察和清理，不能仅凭事件数量视为硬上限。

| 项目 | 计算 | 估算 USD |
|---|---|---:|
| Nova Lite 输入 | 8 × 16,000 / 1,000,000 × 0.06 | 0.007680 |
| Nova Lite 输出 | 8 × 800 / 1,000,000 × 0.24 | 0.001536 |
| raw event | 2 / 1,000 × 0.25 | 0.000500 |
| 长期检索 | 40 / 1,000 × 0.50 | 0.020000 |
| 内置长期记录完整月 | 100 / 1,000 × 0.75 | 0.075000 |
| 合计 | 上述场景 | **0.104716（约 0.11）** |

建议将此最小探针的内部停止阈值设为 1 美元，给重试、清理滞后和价格差异留余量；用户授权的累计总上限仍是 10 美元。税费、汇率、额外服务及实际用量变化不在上述五项小场景内，必须计入最终总费用。没有假设 Free Tier credits。账户审核期间实际云验证仍为 **BLOCKED / 未执行**。
