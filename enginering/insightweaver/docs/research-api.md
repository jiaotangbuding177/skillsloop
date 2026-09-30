# Research API 文档（前端联调）

Base URL：`/api`

统一响应格式：
```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

认证：需要登录态（Cookie），所有接口需 `credentials: 'include'`。

日志排查：
- 每个请求都会生成 `requestId`，返回在响应头 `X-Request-Id`，也可在请求头传入 `x-request-id` 便于关联前后端日志。
- 日志格式示例：`[2025-12-24T06:51:40.175Z] [requestId=...] Research outline start userId=...`
- 全局异常会记录：`Handled HttpException: <message>`，并附带 `{ path, method, status, code, requestId }`。

---

## 1) POST /research/outline
**接口类型：普通 HTTP 接口**

生成研究大纲（可能触发追问）。

### Request Body
```json
{
  "sessionId": "uuid",
  "prompt": "人工智能产业的发展情况和未来趋势，从政府和企业家的视角入手"
}
```

字段说明：
- `sessionId` (string, optional)：已有会话 ID；不传则创建新会话。
- `prompt` (string, required)：用户自然语言需求，最长 5000 字符。

### Response
**直接返回大纲**
```json
{
  "sessionId": "uuid",
  "outlineId": "uuid",
  "outline": "## 一、...\n### ..."
}
```

字段说明：
- `sessionId` (string)：会话 ID。
- `outlineId` (string)：大纲 ID，后续编辑/保存/生成正文都需要。
- `outline` (string)：Markdown 格式的大纲内容。

日志信息（关键字）：
- `Research outline start userId=...`
- `Research outline complete outlineId=... durationMs=...`
- 解析失败时：`Failed to parse outline from text content` 或 `Failed to parse outline from content text`
- 失败响应：`Handled HttpException: outline generation failed`

**触发追问**
```json
{
  "sessionId": "uuid",
  "outlineId": "uuid",
  "elicitation": {
    "id": 0,
    "mode": "form",
    "message": "{\"content\":\"关于…您希望重点关注哪些方面？\",\"options\":{\"A\":\"...\",\"B\":\"...\"}}",
    "requestedSchema": {
      "properties": { "value": { "title": "Value", "type": "string" } },
      "required": ["value"],
      "title": "ScalarElicitationType",
      "type": "object"
    }
  }
}
```

字段说明：
- `sessionId` (string)：会话 ID。
- `outlineId` (string)：大纲 ID。
- `elicitation` (object)：追问信息。
  - `id` (number)：追问 ID，提交答案时必须回传。
  - `mode` (string)：追问类型，当前为 `form`。
  - `message` (string)：JSON 字符串，包含 `content`（问题文本）与 `options`（选项）。
  - `requestedSchema` (object)：约束输入结构，通常 `value` 为 string。

---

## 2) POST /research/outline/elicitation
**接口类型：普通 HTTP 接口**

提交追问答案，继续生成大纲（可能继续追问）。

### Request Body
```json
{
  "outlineId": "uuid",
  "elicitationId": 0,
  "value": "[\"A\",\"C\"]"
}
```

字段说明：
- `outlineId` (string, required)：大纲 ID。
- `elicitationId` (number, required)：追问 ID（来自上一条 `elicitation.id`）。
- `value` (string, required)：选项值，支持单选（如 `"A"`）或多选 JSON 字符串（如 `"[\"A\",\"C\"]"`）。

### Response
**继续追问**
```json
{
  "sessionId": "uuid",
  "outlineId": "uuid",
  "elicitation": { "id": 1, "mode": "form", "message": "...", "requestedSchema": { ... } }
}
```

**生成完成**
```json
{
  "sessionId": "uuid",
  "outlineId": "uuid",
  "outline": "## 一、...\n### ..."
}
```

日志信息（关键字）：
- `Research elicitation response outlineId=...`
- `Research outline complete outlineId=... durationMs=...`
- 常见异常：`outline session not found`、`missing pending request id`

---

## 3) POST /research/outline/edit
**接口类型：普通 HTTP 接口**

对话修改大纲（LLM-only）。

### Request Body
```json
{
  "outlineId": "uuid",
  "instruction": "将第3章拆成两部分，并补充政策部分"
}
```

字段说明：
- `outlineId` (string, required)：大纲 ID。
- `instruction` (string, required)：修改指令，最长 5000 字符。

### Response
```json
{
  "outlineId": "uuid",
  "outline": "## 一、...\n### ..."
}
```

字段说明：
- `outline` (string)：修改后的 Markdown 大纲。

日志信息（关键字）：
- `Research outline edit outlineId=...`
- `Research outline edit complete outlineId=... durationMs=...`

---

## 4) POST /research/outline/save
**接口类型：普通 HTTP 接口**

手动保存用户编辑后的大纲。

### Request Body
```json
{
  "outlineId": "uuid",
  "outline": "## 一、...\n### ..."
}
```

字段说明：
- `outlineId` (string, required)：大纲 ID。
- `outline` (string, required)：Markdown 大纲文本，最长 50000 字符。

### Response
```json
{
  "outlineId": "uuid",
  "outline": "## 一、...\n### ..."
}
```

日志信息（关键字）：
- 当前接口无专用业务日志，建议使用 `X-Request-Id` 和全局异常日志排查

---

## 5) POST /research/content
**接口类型：普通 HTTP 接口**

根据大纲生成正文。

### Request Body
```json
{
  "outlineId": "uuid",
  "topic": "人工智能产业发展研究",
  "supplementaryRequirements": {
    "audience": "政府和企业家",
    "depth": "中观"
  },
  "version": 1
}
```

字段说明：
- `outlineId` (string, required)：大纲 ID。
- `topic` (string, optional)：报告主题，最长 5000 字符。为空时使用大纲生成时的 prompt。
- `supplementaryRequirements` (any, optional)：补充需求，结构不限（对象/字符串皆可）。
- `version` (0|1, optional)：检索源版本。`0`=基础版，`1`=进阶版，默认 1。

### Response
```json
{
  "content": "...正文内容（Markdown 或纯文本）..."
}
```

字段说明：
- `content` (string)：正文内容（Markdown 或纯文本）。

日志信息（关键字）：
- `Research content start outlineId=...`
- `Research content complete outlineId=... durationMs=...`
- 失败响应：`Handled HttpException: content generation failed`

---

## 错误码（约定）
- `DEPENDENCY_UNAVAILABLE`：MCP/LLM 依赖不可用
- `INSUFFICIENT_CREDITS`：余额不足
- `IDEMPOTENCY_CONFLICT`：幂等冲突
- `INVALID_ARGUMENT`：参数不合法

---

## 接口类型说明

### 普通 HTTP 接口
所有接口目前均为普通 HTTP 接口，返回 JSON 格式响应：
- `POST /research/outline` - 生成研究大纲
- `POST /research/outline/elicitation` - 提交追问答案
- `POST /research/outline/edit` - 对话修改大纲
- `POST /research/outline/save` - 手动保存大纲
- `POST /research/content` - 根据大纲生成正文

**注意**：生成类接口（`/research/outline` 和 `/research/content`）可能需要较长时间处理，未来可能会改为 SSE（Server-Sent Events）流式接口以提供实时进度反馈。

### SSE 接口
当前无 SSE 接口。如未来改为 SSE，响应格式将使用 `text/event-stream`，前端需使用 `EventSource` 或 `fetch` 配合流式解析。

---

## 前端对接提示
- 如果返回 `elicitation`，前端需展示问答表单并继续调用 `/research/outline/elicitation`。
- `outlineId` 必须在后续编辑/保存/正文生成中携带。
- `outline` 建议使用 Markdown 编辑器或纯文本编辑器。
