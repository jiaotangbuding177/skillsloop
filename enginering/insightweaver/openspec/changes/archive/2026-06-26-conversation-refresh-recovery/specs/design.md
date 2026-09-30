# 对话消息刷新恢复 — Design

## 演进时间线

```
Phase 0  !62  (2026-06-11)  初始设计：draft 存储 + 基础合并 + 轮询
Phase 1  !63  (2026-06-12)  activeGeneration + 艺术品同步
Phase 2  !65  (2026-06-12)  合并增强：user 去重、terminal 优先
Phase 3  !68           SSE 网络错误自动重试（指数退避 1s/2s/4s）
Phase 4  !77           fix/sse-recovery 分支合并
Phase 5  !95  (2026-06-23)  历史分页 + 占位消息过滤
Phase 6  !111 (2026-06-26)  tool 流事件 + 轮次排序
Phase 7  !112 (2026-06-26)  OpenClaw 历史规范化 + raw JSON 处理
Phase 8  !113 (2026-06-26)  trustApiTerminal + 死循环修复
Phase 9  205f9acb         移除 isSessionApiExplicitlyComplete，回归简化
```

---

## Phase 0 初始架构（!62）

### 设计目标

刷新页面后从 API + sessionStorage 恢复 in-flight 消息。

### 初始模块

```
sessionStorage
  ├── super-lobster:conversation-messages:{sessionId}  → ConversationDraftSnapshot
  └── super-lobster:generating-sessions:v1             → PersistedGeneratingSession[]

conversationMessageMerge.ts (65 行)
  ├── mergeConversationMessagesWithDraft()  — 按 ID 合并，createdAt 排序
  └── hasInFlightConversationMessages()

SuperLobsterPage
  ├── hydrate: loadConversationDraft → mergeConversationMessagesWithDraft
  └── polling: 2s 间隔 getZclawSessionMessagesApi → merge
```

### 初始局限

- 全局 `createdAt` 排序 → 消息顺序错乱
- 无 user 内容去重 → 重复气泡
- 无 tool 消息处理 → raw JSON 渲染
- 无后端 `activeGeneration` → 仅靠 `status === 'streaming'` 推断

---

## 最终架构（Phase 9）

```
                    ┌─────────────────────────────────────┐
                    │         SuperLobsterPage.tsx          │
                    │  (编排层：四条恢复路径)                │
                    └──────────┬──────────────────────────┘
                               │
         ┌─────────┬───────────┼───────────┬─────────┐
         ▼         ▼           ▼           ▼         ▼
     hydrate    polling    subscribe    prepend   (SSE send)
         │         │           │           │
         └─────────┴─────┬─────┴───────────┘
                         ▼
              mapApiMessagesToSuperLobster()
                         │
                         ▼
         normalizeOpenClawHistoryMessages()  ← Phase 7
                         │
                         ▼
              message-filters (占位过滤)     ← Phase 5
                         │
                         ▼
         shouldMergeDraftOnRefresh()         ← Phase 8
                         │
                         ▼
         mergeConversationMessagesWithDraft()
                         │
                         ▼
         resolveConversationStillGenerating()
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    stillGenerating=true      stillGenerating=false
    mergeGeneratingConversationSnapshots   mergeSessionMessagePages
              │                     │
              └──────────┬──────────┘
                         ▼
              sortConversationMessages()   ← Phase 6
                         │
                         ▼
                   SET_MESSAGES
```

---

## 四条恢复路径

### 1. Hydrate（页面刷新 / URL 直达）

**触发：** `sessionIdFromQuery` 变化，`useEffect` 加载会话详情 + 消息分页。

**流程：**
1. `getZclawSessionDetailApi` + `getZclawSessionMessagesApi(limit: 50)`
2. `loadConversationDraft(sessionId)` + `loadStoredMessageFilePreviews`
3. `mapApiMessagesToSuperLobster` → normalize + filter
4. `shouldMergeDraftOnRefresh({ trustApiTerminal: false })` — 默认不信任 API 终端
5. `mergeConversationMessagesWithDraft(api, draft ?? cached)`
6. `resolveConversationStillGenerating({ trustApiTerminal: false })`
7. 若 stillGenerating → `saveConversationDraft` + `upsertGeneratingSession`
8. 否则 → `clearConversationDraft` + `finishGeneratingSession`

**关键：** hydrate 时 API 可能滞后，允许 stale draft 恢复 in-flight 状态。

### 2. Polling（生成中轮询）

**触发：** `generatingSessionIdsRef.has(sessionId)` 或当前 viewing session 有 in-flight 消息。

**流程：**
1. 500ms 间隔 `getZclawSessionMessagesApi(limit: 50)`
2. `shouldMergeDraftOnRefresh({ trustApiTerminal: true })` — 信任 API 终端
3. `mergeConversationMessagesWithDraft(api, shouldMergeDraft ? draft : undefined)`
4. `resolveConversationStillGenerating({ trustApiTerminal: true })`
5. stillGenerating → `mergeGeneratingConversationSnapshots(api, localSnapshot)`
6. 否则 → `mergeSessionMessagePages(previous, latest)`

**关键：** 轮询时 API 已明确 `activeGeneration=false` 即结束，不被 stale draft 拖住。

### 3. Subscribe（SSE 断线重连）

**触发：** 生成中会话的 SSE 连接断开，自动重试后重新 subscribe。

**流程：**
1. SSE 网络错误自动重试 3 次（指数退避 1s/2s/4s）— Phase 3
2. 重连后通过 `conversation-stream-events.ts` 处理 tool 流事件
3. `lastEventSeq` 追踪事件序列（Phase 6）
4. 本地消息通过 reducer 更新，不经过 merge 路径

**废弃方案（Phase 9 移除）：** `receivedStreamEvent` 标志 — 无事件时过早 `finishGeneratingSession`，误判正常重连。

### 4. Prepend（加载更早消息）

**触发：** 用户点击「加载更早消息」。

**流程：**
1. `getZclawSessionMessagesApi(cursor: nextCursor)`
2. `prependOlderConversationMessages(existing, older)` — 去重 ID 后 prepend + 轮次排序

---

## trustApiTerminal 决策表

| 路径 | `trustApiTerminal` | `apiActiveGeneration === false` 时行为 |
|------|---------------------|----------------------------------------|
| hydrate / subscribe | `false`（默认） | 若 `sessionMarkedGenerating && draftInFlight` → 仍视为生成中 |
| polling | `true` | 立即视为已结束，不合并 stale draft |

### resolveConversationStillGenerating 判定顺序

```
1. apiActiveGeneration === true                          → true
2. isApiSessionStillGenerating(messages)                 → true
3. hasInFlightConversationMessages(messages)             → true
4. apiActiveGeneration === false:
   a. trustApiTerminal === true                          → false
   b. sessionMarkedGenerating && draftInFlight           → true
   c. else                                               → false
5. draftInFlight && sessionMarkedGenerating               → true
6. else                                                   → false
```

---

## 核心模块职责

### conversationDraftStorage.ts

| 导出 | 职责 |
|------|------|
| `saveConversationDraft` | 写入 sessionStorage |
| `loadConversationDraft` | 读取并校验 sessionId |
| `clearConversationDraft` | 清除 draft |
| `saveGeneratingSessions` / `loadGeneratingSessions` | 生成中会话列表持久化 |
| `removeGeneratingSession` | 从列表移除 |

`ConversationDraftSnapshot`: `{ sessionId, messages, isStreaming, updatedAt }`

### conversationMessageMerge.ts

| 导出 | 职责 |
|------|------|
| `mergeConversationMessagesWithDraft` | API + draft 按 ID/role 合并 |
| `sortConversationMessages` | 按对话轮次排序（user → tool → assistant） |
| `mergeSessionMessagePages` | 分页重叠区间合并 |
| `prependOlderConversationMessages` | 更早一页 prepend |
| `mergeGeneratingConversationSnapshots` | 生成中轮询时 API + 本地快照叠加 |
| `resolveConversationStillGenerating` | 是否仍视为生成中 |
| `shouldMergeDraftOnRefresh` | 是否合并 sessionStorage draft |
| `isApiSessionStillGenerating` | 从 API 消息推断 streaming |
| `hasInFlightConversationMessages` | 是否存在 status=sending |
| `areConversationMessagesEqual` | 浅比较避免无效 dispatch |
| `mergeMessagesById` | 按 ID 去重合并 |

### normalize-openclaw-history-messages.ts

将 OpenClaw 远程历史的 `toolCall`/`toolResult`/`tool_use` 等转为标准 `tool` 消息，附带 `toolActivity`。

### conversation-stream-events.ts

处理 SSE 流中的 tool 事件：`mergeInFlightToolMessage`、`dedupeToolMessagesByCallId`、`readMessageToolCallId`。

### message-filters.ts

| 导出 | 职责 |
|------|------|
| `isPlaceholderAssistantMessage` | 过滤 `(no output)` / `NO_REPLY` / 空内容 |
| `isVisibleConversationMessage` | 渲染可见性判定 |
| `isSilentReplyMessage` | NO_REPLY 检测 |
| `isInternalCompactionMessage` | 内部 compaction 消息过滤 |

---

## 消息排序规则（sortConversationMessages）

1. `splitMessagesIntoTurns` — 按 user 消息切分轮次
2. `coalesceOrphanTurnPrefixes` — 并入 orphan 前缀
3. `mergeDuplicateUserOnlyTurns` — 合并重复 user-only 轮次（Phase 7）
4. `orderTurnMessages` — 每轮内：user（内容去重）→ tool（callId 去重）→ other → assistant（合并）

**禁止：** 全局按 `createdAt` 排序作为最终顺序。

---

## Assistant 合并规则（mergeAssistantMessages）

- ID 优先：非 client draft ID（`assistant-draft-*`）优先于 client ID
- 内容优先：`preferAssistantDisplayContent` — 自然语言优于 raw tool JSON
- 状态优先：API terminal（sent/error/aborted）不被 draft sending 覆盖
- toolActivity / files：draft 优先补充

---

## 后端 activeGeneration（zclaw.service.ts）

```ts
// Phase 7 最终逻辑
if (activeRun?.status === 'running') return true;
return detail.messages.some(
  (message) =>
    message.status === 'streaming' &&
    (message.role === 'assistant' || message.role === 'tool'),
);
```

---

## useEffect 防死循环（交叉引用）

见 `openspec/specs/useeffect-circular-dependency/spec.md`：

- hydrate effect：仅用 `sessionIdFromQuery` 等稳定依赖 + `loadingSessionIdRef` 守卫
- polling effect：`generationPollRequestSeqRef` 防竞态；`shouldPoll` 条件收紧
- 禁止将 `state.messages` 等 effect 内部会修改的计算值放入依赖数组

---

## 废弃方案（勿再引入）

| 方案 | 引入 | 移除 | 原因 |
|------|------|------|------|
| `isSessionApiExplicitlyComplete` | Phase 8 | Phase 9 | 与 `trustApiTerminal` 重叠，增加边界复杂度 |
| `sessionDetailHydratedRef` + `sessionDetailHydratedTick` | Phase 8 | Phase 9 | hydration 守卫与 trustApiTerminal 冲突 |
| `receivedStreamEvent` 无事件即结束 | Phase 8 | Phase 9 | 误判 SSE 重连场景 |
| 全局 `createdAt` 排序 | Phase 0 | Phase 6 替代 | OpenClaw 时间戳不可靠 |
