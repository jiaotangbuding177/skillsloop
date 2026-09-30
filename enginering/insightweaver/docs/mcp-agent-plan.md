# MCP Agent 方案（DashScope + MCP SDK）

## 目标
- 自然语言输入后生成行业研究大纲。
- 用户可手动编辑大纲，或与大模型对话修改大纲。
- 用户确认大纲后生成完整正文。

## 依赖与环境
- Node 22, pnpm workspace
- LLM: DashScope OpenAI 兼容模式（model: qwen-plus-latest）
- MCP SDK: `@modelcontextprotocol/sdk`
- OpenAI client: `openai`

建议新增环境变量（写到本地 .env，不提交仓库）：
- `DASHSCOPE_API_KEY=...`
- `DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `DASHSCOPE_MODEL=qwen-plus-latest`
- `MCP_OUTLINE_URL=http://47.116.218.181:8005/mcp`
- `MCP_CONTENT_URL=http://47.116.218.181:8015/mcp`

## 工具信息
- `generate_industry_research_outline`
  - request.industry: string (必填)
  - request.additional_requirements: unknown (可选)
- `generate_research_content`
  - request.topic: string (必填)
  - request.outline: string (必填)
  - request.supplementary_requirements: unknown
  - request.llm_provider: unknown
  - request.version: enum<int> (0/1)

## MCP 返回与交互特性（基于日志）
- MCP 使用 `text/event-stream` 流式响应，期间会发送 `notifications/message` 进度事件。
- 在生成大纲过程中可能出现 `elicitation/create`（表单式追问）。需要客户端回应：
  - 请求：`{"jsonrpc":"2.0","id":<elicitation_id>,"result":{"action":"accept","content":{"value":"..."} } }`
  - `value` 支持单选或多选的字符串（如 `"A"` 或 `"[\"A\",\"C\"]"`）。
- 最终结果通常在 `result.content[0].text`（JSON 字符串）与 `structuredContent` 中提供：
  - 大纲：`structuredContent.outline_md`
  - 正文：预计类似 `structuredContent.content_md`（以实际返回为准）

## MCP SDK 调用方式（细化）
### 会话初始化
- SDK 自动完成 `initialize` + `notifications/initialized` 并维护 `mcp-session-id`
- 若不用 SDK，需要手动 POST `initialize` 并从响应头读取 `mcp-session-id`

### 工具调用
- 使用 SDK `client.callTool({ name, arguments })` 执行 `tools/call`
- 监听流式事件以接收进度与 `elicitation/create`

### Elicitation 往返
- 收到 `elicitation/create` 后保存 `{ sessionId, elicitationId, schema, message }`
- 前端提交答案后，用同一 session 发送 `result`（action=accept）
- 直到收到最终 `result` 才结束会话

## 模块设计（apps/api）
- `mcp/`
  - `mcp.service.ts`: MCP 客户端封装（连接两个 MCP）
  - `mcp-session.ts`: session 管理、SSE 事件解析、elicitation 往返
  - `tool-registry.ts`: 拉取工具 schema，建立工具白名单
- `agent/`
  - `agent-runtime.ts`: LLM 对话与 tool-calling 循环
  - `tool-invoker.ts`: 将 LLM tool call 转成 MCP 调用
  - `report-agent.service.ts`: 对外提供“生成大纲”的 agent 接口
- `research/`
  - `research.controller.ts`: 对外 API
  - `research.service.ts`: 业务编排（含大纲缓存/编辑/正文生成）
- `billing/`
  - `billing.service.ts`: 积分扣减（固定积分，幂等）

## 交互流程
### A. 生成初始大纲（Agent + MCP）
1) 用户输入自然语言需求
2) AgentRuntime 使用 LLM 产生 tool call：`generate_industry_research_outline`
3) MCP 返回流式进度与可能的 `elicitation/create`
4) 若有 `elicitation/create`：前端展示问答表单，提交答案后继续同一 MCP 会话（同一 `mcp-session-id`）
5) MCP 返回大纲 Markdown
6) API 返回给前端：`outline + outlineId`

### B. 编辑/对话修改大纲（LLM-only）
1) 用户提交修改说明或直接编辑后的大纲
2) 若是“对话修改”，调用 LLM（不走 MCP）输出新的 Markdown 大纲
3) 存储新的大纲版本，返回给前端

### C. 生成正文（MCP）
1) 用户确认大纲
2) 调用 `generate_research_content`
3) 返回完整正文

## API 设计（建议）
- `POST /research/outline`
  - body: `{ prompt: string }`
  - return: `{ outlineId: string, outline?: string, elicitation?: {...} }`
- `POST /research/outline/elicitation`
  - body: `{ outlineId: string, elicitationId: number, value: string }`
  - return: `{ outlineId: string, outline?: string, elicitation?: {...} }`
  - 说明：通过 `outlineId` 找到 sessionId，继续同一 MCP 会话
- `POST /research/outline/edit`
  - body: `{ outlineId: string, instruction: string }`
  - return: `{ outlineId: string, outline: string }`
- `POST /research/outline/save`
  - body: `{ outlineId: string, outline: string }` (用户手动编辑保存)
  - return: `{ outlineId: string, outline: string }`
- `POST /research/content`
  - body: `{ outlineId: string, topic?: string, supplementaryRequirements?: unknown, version?: 0|1 }`
  - return: `{ content: string }`

## 大纲缓存建议
- 轻量方案：内存 Map（单实例）
- 可用现有 Redis (`ioredis`)：`outline:{outlineId}` -> Markdown
- 持久化：写入数据库（见“数据库持久化设计”）

## 数据库持久化设计（参考现有表结构）
现有表普遍具备：`id`、`createdAt`、`updatedAt`、`isDeleted`，并与 `User` 关联。建议新增两张表：

### ResearchOutline
- `id` String @id @default(uuid())
- `userId` String (关联 User)
- `prompt` String (原始自然语言需求)
- `industry` String (抽取后行业名)
- `additionalRequirements` Json? (MCP 请求中的 additional_requirements)
- `outlineMd` String (大纲 Markdown)
- `title` String? (若 MCP 生成标题可存)
- `status` String @default("draft") (draft/edited/locked)
- `version` Int @default(1) (编辑版本号)
- `createdAt` DateTime @default(now())
- `updatedAt` DateTime @updatedAt
- `isDeleted` Boolean @default(false)

索引建议：
- `@@index([userId, createdAt])`
- `@@index([status])`

### ResearchContent
- `id` String @id @default(uuid())
- `userId` String (关联 User)
- `outlineId` String (关联 ResearchOutline)
- `topic` String
- `supplementaryRequirements` Json?
- `llmProvider` String? (如 dashscope)
- `version` Int (0/1)
- `contentMd` String (正文 Markdown 或全文)
- `createdAt` DateTime @default(now())
- `updatedAt` DateTime @updatedAt
- `isDeleted` Boolean @default(false)

索引建议：
- `@@index([userId, createdAt])`
- `@@index([outlineId])`

关系建议：
- `ResearchOutline` 1 - N `ResearchContent`
- `User` 1 - N `ResearchOutline` / `ResearchContent`

写入时机：
- 大纲生成成功后写入 `ResearchOutline`
- 大纲编辑保存时更新 `outlineMd`、`version`、`status`
- 正文生成成功后写入 `ResearchContent`

## Agent Runtime 规则
- 只允许调用 `generate_industry_research_outline`
- 单次请求最多 1 次工具调用
- tool schema 校验失败则要求 LLM 重新输出
- 超时与错误处理：返回友好错误给前端

## LLM 提示词（建议）
### 生成大纲 tool-calling（System）
你是行业研究报告代理。只能使用提供的工具。必须先生成大纲，且每次调用严格遵守工具参数 schema。

### 大纲编辑（System）
你是行业研究大纲编辑助手。输入包含原始大纲和用户修改指令。请返回修改后的 Markdown 大纲，保持结构清晰，可读性强。只输出大纲 Markdown。

## 参数策略
- 大纲生成：
  - `industry`: 从用户输入中抽取行业名
  - `additional_requirements`: 用户输入中除行业外的约束
- 正文生成：
  - `topic`: 使用用户原始主题句（优先）
  - `outline`: 使用最新大纲 Markdown
  - `supplementary_requirements`: 透传用户的补充指令
  - `llm_provider`: 固定传 `dashscope` 或留空
  - `version`: 默认 1（全检索源）

## MCP 调用策略
- 大纲工具固定走 `MCP_OUTLINE_URL`
- 正文工具固定走 `MCP_CONTENT_URL`
- 若其中一个不可用，可配置 fallback 到另一个
- 需要保留同一 `mcp-session-id` 以完成 `elicitation` 交互
- 建议将 `outlineId -> sessionId` 暂存（Redis 或 DB），用于后续 `elicitation` 继续调用

## 日志与可观测性
- 每次请求生成 `traceId`
- 记录 LLM 输入/输出摘要、tool call 参数、MCP 耗时、错误类型

## 错误码与异常策略（细化）
- MCP 请求失败/超时：`ErrorCode.DEPENDENCY_UNAVAILABLE`
- 余额不足：`ErrorCode.INSUFFICIENT_CREDITS`
- 幂等冲突：`ErrorCode.IDEMPOTENCY_CONFLICT`
- 参数非法：`ErrorCode.INVALID_ARGUMENT`

## 实施步骤
1) 在 `apps/api` 添加依赖：`@modelcontextprotocol/sdk`、`openai`
2) 新增 MCP 客户端封装与工具注册
3) 实现 AgentRuntime 与 ToolInvoker
4) 增加 research API 路由与 service
5) 接入 DashScope LLM（baseURL + model）
6) 前端对接：展示大纲 + 允许编辑 + 触发正文生成

## 风险与控制
- LLM 输出非法参数：强校验 + 重新生成
- MCP 失败：返回失败原因并提示重试
- 成本控制：限制 tool call 次数、响应大小、超时

## 积分扣减逻辑（建议）
> 参考现有 `CreditLedger` + `Wallet` 体系，所有扣减须具备幂等性与可追溯性。

### 计费点设计
- 生成大纲：扣 1 次基础费用（可按 token 或固定值）
- 生成正文：扣 1 次正文费用（通常高于大纲）
- 大纲编辑（LLM-only）：如需计费，可按“轻量修改”扣 1 次轻量费用

### 扣减时机
- **成功后扣费**：MCP/LLM 成功返回结果后写入 `CreditLedger` 并更新 `Wallet`
- **失败不扣费**：请求失败或被取消，不记账
- **幂等保护**：每次计费需生成 `idempotencyKey`，避免重试多扣

### CreditLedger 建议字段
- `delta`: 负值（扣减）
- `reason`: `outline_generation` | `outline_edit` | `content_generation`
- `refType`: `ResearchOutline` | `ResearchContent`
- `refId`: 相关记录 ID
- `idempotencyKey`: `traceId:action` 或 `outlineId:action` + hash

### 钱包更新策略
- 使用乐观锁（`Wallet.version`）更新
- 余额不足时：直接拒绝请求并返回 402/业务错误码

### 计费配置建议（环境变量）
- `OUTLINE_COST`：大纲生成扣减积分（整数）
- `CONTENT_COST`：正文生成扣减积分（整数）
- `EDIT_COST`：大纲编辑扣减积分（整数，默认可设为 0）

### 审计建议
- 关键扣费操作写入 `AuditLog`（action: `credit_deducted`，resourceType: `CreditLedger`）
