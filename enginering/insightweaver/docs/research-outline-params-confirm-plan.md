# 研究大纲参数确认（方案 A）

## 目标
- 在调用 MCP 生成大纲前，先由 LLM 抽取“参数草案”并返回前端确认
- 用户确认/修改后，再调用 MCP 生成大纲
- 保持现有大纲生成逻辑可追溯、可计费、可重试

---

## 现状简述
- `POST /research/outline` 由 `ReportAgentService.generateOutline` 直接触发 MCP 工具调用
- `toolCallArgs` 只在后端内部使用，没有返回前端确认的中间态
- SSE 已用于大纲生成和 MCP 消息流转

---

## 方案 A 流程
1) 前端提交 `prompt/attachmentIds/sessionId` → `POST /research/outline/params`
2) 后端运行 LLM 只做参数抽取，返回 `paramsDraft`
3) 前端展示可编辑表单，用户确认/修改
4) 前端提交确认参数 → `POST /research/outline`（或新接口 `POST /research/outline/confirm`）
5) 后端调用 MCP 生成大纲（SSE 保持不变）

---

## API 设计（建议）

### 1) 生成参数草案
`POST /research/outline/params`
- 请求：
  - `prompt: string`
  - `sessionId?: string`
  - `attachmentIds?: string[]`
  - `mode?: string`
- 响应：
  - `sessionId: string`
  - `outlineId: string`（用于串联后续流程）
  - `paramsDraft: Record<string, unknown>`（即 `toolCallArgs`）
  - `title?: string`（如有）

### 2) 确认后生成大纲
`POST /research/outline`
- 请求：
  - `outlineId: string`
  - `paramsConfirmed: Record<string, unknown>`
  - `mode?: string`
- 响应：
  - 维持现有 SSE 输出（`meta/message/done/error`）

---

## 后端改造点

### Controller
- 新增 `POST /research/outline/params`
- `POST /research/outline` 改为接收 `outlineId + paramsConfirmed`（与旧请求体不兼容）
- 若需兼容旧前端，可在 `GenerateOutlineDto` 中保留 `prompt` 并分支处理

### Service
新增方法：
- `generateOutlineParams(...)`
  - 创建/绑定 `ResearchSession`
  - 保存 user message + attachments
  - 调用 `AgentRuntime.runOutlineAgent`
  - 仅返回 `toolCallArgs`，不调用 MCP
  - 生成并返回 `outlineId`
  - 可写入 Redis/DB 作为参数草案临时存储（可选）

调整方法：
- `generateOutline(...)`
  - 接收 `paramsConfirmed`
  - 直接调用 `ToolInvoker.callOutlineTool` 进入 MCP
  - 保持计费/Session/消息记录逻辑不变

### Agent / ToolInvoker
- `ReportAgentService` 添加 `generateOutlineParams(...)`（仅返回 `toolCallArgs`）
- `ToolInvoker.callOutlineTool` 新增重载或新方法，支持直接使用 `paramsConfirmed`

---

## 数据与缓存
- `outlineId` 作为草案与最终大纲的关联键
- 可选：将 `paramsDraft` 暂存 Redis（TTL 与大纲一致）
- 最终大纲仍落库，草案可不落库

---

## 兼容性与迁移策略
- 若不需要兼容旧前端，直接修改 `POST /research/outline` 入参即可
- 若需要兼容：
  - `POST /research/outline` 保留旧逻辑
  - 新增 `POST /research/outline/confirm` 用于新流程
  - 前端切换完成后再移除旧逻辑

---

## 前端改造点（摘要）
- 新增参数确认页/弹窗
- 表单字段与 `paramsDraft` 结构对齐，可自由编辑
- 二次确认后调用 `POST /research/outline` 并进入 SSE 流

---

## 错误处理
- LLM 未返回 `toolCallArgs`：返回 400 并提示“参数抽取失败”
- MCP 调用失败：沿用现有 SSE `error`
- `outlineId` 不存在或过期：返回 404/409

---

## 测试建议
- `generateOutlineParams` 成功返回 `paramsDraft`
- `generateOutline` 接收确认参数后调用 MCP
- 兼容分支（如保留旧入口）

---

## 里程碑
1) 后端新增 `/research/outline/params` 与 DTO
2) 前端接入参数确认
3) 旧流程下线（如需要）
