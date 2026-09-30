# MCP Agent 开发 TODO

## 1. 配置与依赖
- [x] 引入 MCP SDK 与 DashScope OpenAI 兼容客户端
  - `apps/api/package.json`
- [x] 配置环境变量（本地 `.env`）
  - `DASHSCOPE_API_KEY`
  - `DASHSCOPE_BASE_URL`
  - `DASHSCOPE_MODEL`
  - `MCP_OUTLINE_URL`
  - `MCP_CONTENT_URL`
  - `OUTLINE_COST` / `CONTENT_COST` / `EDIT_COST`

## 2. MCP 接入层
- [x] 创建 MCP 客户端封装（保持 session、处理 SSE 流）
  - 目标目录：`apps/api/src/mcp/`
  - 重点：保存 `mcp-session-id`，支持 `elicitation/create` 往返
- [x] 增加 sessionId 暂存策略（outlineId -> sessionId）
  - Redis 持久化（`mcp:outline:{outlineId}`）
- [x] Tool Registry：拉取并缓存两个 MCP 的 tool schema
  - 支持 tool 白名单与命名空间

## 3. Agent 运行时
- [x] AgentRuntime：LLM 对话循环 + 工具调用约束
  - 最大调用次数
  - tool schema 校验
- [x] ToolInvoker：把 LLM tool call 转成 MCP `tools/call`
- [x] 大纲编辑模式：LLM-only（不走 MCP）

## 4. Research 业务模块
- [x] Controller + Service
  - `POST /research/outline`：生成大纲
  - `POST /research/outline/elicitation`：处理追问
  - `POST /research/outline/edit`：对话修改大纲
  - `POST /research/outline/save`：手动保存
  - `POST /research/content`：生成正文

## 5. 数据库持久化
- [x] Prisma 增加模型（参考方案文档）
  - `ResearchOutline`
  - `ResearchContent`
- [x] 生成迁移并应用（`pnpm db:migrate`）
- [x] 在 ResearchService 中写入：
  - 大纲生成成功后保存
  - 大纲编辑/保存时更新
  - 正文生成成功后保存

## 6. 计费与积分扣减
- [x] 独立 BillingService（固定积分扣减 + 幂等）
  - `apps/api/src/billing/billing.service.ts`
- [x] 在 ResearchService 中调用 `BillingService.charge(...)`
  - 大纲生成成功后扣 `OUTLINE_COST`
  - 正文生成成功后扣 `CONTENT_COST`
  - 编辑大纲如需收费再扣 `EDIT_COST`

## 7. 可观测性与错误处理
- [x] TraceId 贯穿 MCP/LLM 调用
- [x] 记录 LLM/MCP 耗时、错误码、工具参数摘要
- [x] 统一异常抛出（沿用 `ErrorCode`）

## 8. 前端对接（可选）
- [ ] 大纲展示 + 编辑
- [ ] 追问表单交互（elicitation/create）
- [ ] 触发正文生成并展示

## 9. 验证与测试
- [ ] 本地联调 MCP（大纲生成 + 追问）
- [ ] 正文生成联调
- [ ] 扣费幂等验证
