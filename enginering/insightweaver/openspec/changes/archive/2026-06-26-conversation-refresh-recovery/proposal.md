# Proposal: 对话消息刷新恢复

## What & Why

Super Lobster 对话页在用户**刷新浏览器**、**URL 直达会话**、**SSE 断线重连**、或**会话仍在生成中**时，需要从 API 历史消息与本地 `sessionStorage` draft 中恢复正确的对话状态。

### 初始痛点（Phase 0, !62）

- 用户刷新页面后 SSE 流中断，in-flight 的 assistant / tool 消息丢失
- API 返回的历史消息滞后于本地流式状态，刷新后对话「断档」
- 生成中的会话无法在无 SSE 连接时继续展示进度

### 演进过程中暴露的问题

| 问题 | 发现阶段 |
|------|----------|
| 消息顺序错乱（assistant 跑到 user 上方） | Phase 5–6 |
| 刷新后出现重复 user 气泡 | Phase 2 部分缓解，Phase 7 彻底解决 |
| raw tool JSON 被当成 assistant 气泡渲染 | Phase 7 |
| 生成已结束却被 stale draft 误判为仍在生成 | Phase 8 |
| 轮询/hydrate 触发 useEffect 死循环 | Phase 8 |
| 历史会话记录展示不全（分页） | Phase 5 |
| SSE 断线后恢复不稳定 | Phase 3–6 |

### 目标

- 刷新后正确恢复 in-flight 消息，不丢、不乱、不重复
- 生成中会话在无 SSE 时通过轮询继续更新
- API 历史 + draft + 本地快照三路合并有明确规则
- 纯逻辑下沉到可测试模块，组件只做编排
- 轮询与 hydrate 对 API 终端标志采用不同信任策略

## Scope

### In Scope

- `conversationDraftStorage.ts` — sessionStorage draft + generating sessions
- `conversationMessageMerge.ts` — 合并、排序、去重、生成状态判定
- `conversation-stream-events.ts` — tool 流事件处理与 callId 去重
- `normalize-openclaw-history-messages.ts` — OpenClaw 历史消息规范化
- `message-filters.ts` — 占位 assistant / 内部消息过滤
- `SuperLobsterPage.tsx` — hydrate / polling / subscribe / prepend 四条路径编排
- `zclaw.service.ts` — `activeGeneration` 标志（含 tool streaming）
- SSE 网络错误自动重试（!68）与 sse-recovery 分支合并（!77）
- 单元测试与人工验收场景

### Out of Scope

- `session-refresh.ts` — 登录 token 刷新（独立功能）
- `file-tree-refresh-scopes.ts` — 文件树刷新
- Ragflow 文档状态刷新
- 消息 UI 样式（MessageBubble 等）的非恢复相关改动

## End-to-End User Path

| 场景 | 入口 | 操作 | 结果 |
|------|------|------|------|
| 刷新生成中会话 | 浏览器 F5 / 重新打开标签 | 自动 hydrate + 轮询 | 继续显示流式回复，输入框保持禁用直至完成 |
| 刷新已完成会话 | 浏览器 F5 | hydrate | 显示完整历史，无重复气泡 |
| URL 直达会话 | `/super-lobster?sessionId=xxx` | 自动加载 | 正确展示该会话消息 |
| SSE 断线 | 网络抖动 | 自动重试 + subscribe 恢复 | 消息不丢、不重复请求 |
| 加载更早消息 | 消息列表顶部按钮 | 点击「加载更早」 | prepend 更早分页，顺序正确 |

## Backend Constraints

- `getZclawSessionMessagesApi` 返回 `messages`、`nextCursor`、`hasMore`、`activeGeneration`
- `getZclawSessionDetailApi` 返回 `activeGeneration`（Phase 1 引入）
- `activeGeneration` 判定：`activeConversationRuns.status === 'running'` 或消息中存在 `status === 'streaming'`（Phase 7 扩展含 tool）
- OpenClaw 远程历史可能返回 `toolCall`/`toolResult` 等非标准 role，前端必须规范化
- 历史消息 `createdAt` 不可靠，不能作为唯一排序依据

## Impact

### Files Changed（累计，Phase 0 → 9）

| 文件 | 性质 |
|------|------|
| `apps/web/src/lib/conversationDraftStorage.ts` | 新建 + 扩展 |
| `apps/web/src/lib/conversationMessageMerge.ts` | 新建 + 持续演进 |
| `apps/web/src/lib/conversation-stream-events.ts` | 新建 |
| `apps/web/src/lib/normalize-openclaw-history-messages.ts` | 新建 |
| `apps/web/src/lib/message-filters.ts` | 扩展 |
| `apps/web/src/components/super-lobster/SuperLobsterPage.tsx` | 核心编排 |
| `apps/api/src/zclaw/zclaw.service.ts` | activeGeneration |
| `apps/web/src/lib/__tests__/conversationMessageMerge.test.ts` | 测试 |
| `apps/web/src/lib/__tests__/normalize-openclaw-history-messages.test.ts` | 测试 |
| `apps/web/src/lib/__tests__/conversation-stream-events.test.ts` | 测试 |

### No Breaking Changes

- API 接口签名不变（仅扩展 `activeGeneration` 返回值）
- 现有 SSE 流式发送流程不变
