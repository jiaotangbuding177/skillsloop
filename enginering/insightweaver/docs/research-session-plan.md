# Research 会话保存逻辑（会话级别）

## 目标
- 以“会话”为单位保存用户研究任务
- 同一会话内关联对话历史、大纲版本、正文记录
- Redis 只用于短期缓存，数据库为最终存储
- 前端历史列表可展示未生成大纲的会话，并区分状态

---

## 数据模型（概念）

### ResearchSession
- `id`, `userId`, `title`, `status`, `createdAt`, `updatedAt`, `isDeleted`

### ResearchMessage
- `id`, `sessionId`, `role(user/assistant/system)`, `content`, `createdAt`, `isDeleted`

### ResearchOutline（最新版本）
- `id`, `sessionId`, `outlineMd`, `version`, `status`, `updatedAt`

### ResearchOutlineVersion（历史快照）
- `outlineId`, `version`, `outlineMd`, `source`, `createdAt`

### ResearchContent
- `sessionId`, `outlineId`, `contentMd`, `version`, `createdAt`

---

## 会话创建与绑定
- `/research/outline` 若未传 `sessionId`：创建新 `ResearchSession`
- `title` 可取 prompt 前 20~30 字
- 后续接口全部携带 `sessionId`

## 会话状态（建议）
- `draft`：仅有对话/追问，未生成大纲
- `outline_ready`：已有大纲
- `content_ready`：已有正文
- `archived`：过期或手动归档

前端展示建议：
- 默认显示 `outline_ready` / `content_ready`
- `draft` 放在“未完成/草稿”过滤器中
- 超过一定时间（如 7/30 天）可自动归档或隐藏

---

## 对话历史保存
- 用户输入 prompt：写入 `ResearchMessage(role=user, content=prompt)`
- LLM 追问：写入 `ResearchMessage(role=assistant, content=追问内容)`
- LLM 返回大纲：可写入 `ResearchMessage(role=assistant, content=大纲摘要或全文)`
- `/research/outline/edit`：
  - 写入 user 指令
  - 写入 assistant 修改结果摘要

---

## 大纲保存逻辑
- `ResearchOutline` 保存最新版本
- 每次生成/编辑/保存：
  1) 更新 `ResearchOutline`（outlineMd + version）
  2) 插入 `ResearchOutlineVersion`（全量快照）
- `source`：`llm` / `llm_edit` / `manual`

---

## 正文保存逻辑
- `/research/content` 成功后写入 `ResearchContent`
- 关联 `sessionId` + `outlineId`
- 支持多正文版本（按 outline 版本区分）

---

## Redis 缓存
- `research:outline:{outlineId}`：大纲缓存
- `mcp:outline:{outlineId}`：MCP session 暂存
- DB 为最终来源，缓存仅用于性能与中间态

---

## 计费与会话关联
- `CreditLedger.refType/refId` 继续指向 `outlineId` / `contentId`
- 建议在 `meta` 中记录 `sessionId` 便于对账审计

---

## 实施建议（下一步）
1) 增加 `ResearchSession` / `ResearchMessage` 表
2) `/research/outline` 自动创建 session 并写入首条 user message
3) 编辑与追问时追加消息
4) 查询接口：会话列表与详情（含 messages/outlines/contents）
