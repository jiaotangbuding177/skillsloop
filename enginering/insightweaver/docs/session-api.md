# Session API 文档（前端联调）

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

---

## 1) GET /research/sessions
获取研究会话列表。

### Query Params
- `page` (number, optional)：页码，默认 1。
- `pageSize` (number, optional)：每页条数，默认 20，最大 100。
- `status` (string, optional)：`draft` / `outline_ready` / `content_ready` / `archived`。

### Response
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "人工智能产业发展",
      "status": "outline_ready",
      "createdAt": "2025-01-01T00:00:00.000Z",
      "updatedAt": "2025-01-01T00:10:00.000Z",
      "latestOutline": {
        "id": "uuid",
        "version": 1,
        "updatedAt": "2025-01-01T00:05:00.000Z"
      },
      "latestContent": {
        "id": "uuid",
        "version": 1,
        "createdAt": "2025-01-01T00:10:00.000Z"
      }
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 1
}
```

---

## 2) GET /research/sessions/:sessionId
获取单个会话详情（消息 + 大纲 + 历史版本 + 正文）。

### Path Params
- `sessionId` (string, required)：会话 ID。

### Response
```json
{
  "session": {
    "id": "uuid",
    "title": "人工智能产业发展",
    "status": "content_ready",
    "createdAt": "2025-01-01T00:00:00.000Z",
    "updatedAt": "2025-01-01T00:20:00.000Z"
  },
  "messages": [
    {
      "id": "uuid",
      "sessionId": "uuid",
      "role": "user",
      "content": "...",
      "createdAt": "2025-01-01T00:00:00.000Z",
      "isDeleted": false
    }
  ],
  "outline": {
    "id": "uuid",
    "sessionId": "uuid",
    "userId": "uuid",
    "prompt": "...",
    "outlineMd": "...",
    "version": 1,
    "createdAt": "2025-01-01T00:05:00.000Z",
    "updatedAt": "2025-01-01T00:06:00.000Z",
    "isDeleted": false
  },
  "outlineVersions": [
    {
      "id": "uuid",
      "outlineId": "uuid",
      "version": 1,
      "outlineMd": "...",
      "source": "llm",
      "createdAt": "2025-01-01T00:05:00.000Z",
      "isDeleted": false
    }
  ],
  "contents": [
    {
      "id": "uuid",
      "sessionId": "uuid",
      "outlineId": "uuid",
      "topic": "...",
      "version": 1,
      "contentMd": "...",
      "createdAt": "2025-01-01T00:10:00.000Z",
      "updatedAt": "2025-01-01T00:10:00.000Z",
      "isDeleted": false
    }
  ]
}
```
