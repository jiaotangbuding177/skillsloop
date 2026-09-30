# Tasks: 对话消息刷新恢复

> 按 Phase 0–9 记录全部已完成任务。最终态：`205f9acb`

---

## Phase 0: 初始设计（!62, 758616f7）

### Task 0.1: 创建 sessionStorage draft 存储
**File:** `apps/web/src/lib/conversationDraftStorage.ts`

- [x] 定义 `ConversationDraftSnapshot` 类型
- [x] 实现 `saveConversationDraft` / `loadConversationDraft` / `clearConversationDraft`
- [x] 实现 `saveGeneratingSessions` / `loadGeneratingSessions` / `removeGeneratingSession`
- [x] sessionStorage key 前缀 `super-lobster:conversation-messages:`

### Task 0.2: 创建基础消息合并逻辑
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] 实现 `mergeConversationMessagesWithDraft` — 按 ID 合并
- [x] 实现 `hasInFlightConversationMessages`
- [x] 初始按 `createdAt` 排序

### Task 0.3: SuperLobsterPage 刷新恢复编排
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] hydrate 时 `loadConversationDraft` → `mergeConversationMessagesWithDraft`
- [x] 生成中 2s 轮询 `getZclawSessionMessagesApi`
- [x] `generationPollRequestSeqRef` 防竞态
- [x] 生成完成时 `clearConversationDraft` + `finishGeneratingSession`

### Task 0.4: 后端消息流处理
**Files:** `apps/api/src/zclaw/zclaw.service.ts`, `zclaw.controller.ts`

- [x] 消息流处理和异常中止功能
- [x] `send-zclaw-message.dto.ts` 扩展

**Verification:** 刷新生成中会话，draft 消息可恢复

---

## Phase 1: activeGeneration（!63, ccda85ad）

### Task 1.1: 后端 activeGeneration 标志
**File:** `apps/api/src/zclaw/zclaw.service.ts`

- [x] `hasActiveLocalGeneration` 检查 `activeConversationRuns`
- [x] session detail / messages API 返回 `activeGeneration: true | false`
- [x] 远程历史同步失败时返回 `recover_empty` / `recover_failed` 状态

### Task 1.2: 会话艺术品同步
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] `syncSessionArtifacts` — 生成中轮询时同步关联文件
- [x] `buildSessionArtifactSignature` 变更检测

### Task 1.3: 流式 UI 指示器
**Files:** `MessageBubble.tsx`, `MessageList.tsx`, `AssistantLoadingIndicator.tsx`

- [x] 流媒体回复指示器

**Verification:** 生成中会话 API 返回 `activeGeneration: true`

---

## Phase 2: 合并增强（!65, b8814a77）

### Task 2.1: user 去重与 terminal 状态优先
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] `hasMatchingUserMessage` — 跳过重复 user draft
- [x] `mergeInFlightAssistantMessage` — API terminal 不被 draft 覆盖
- [x] `isApiSessionStillGenerating`
- [x] assistant ID 不一致时合并到最后一个 in-flight assistant

**Verification:** `pnpm test` — conversationMessageMerge tests pass

---

## Phase 3: SSE 网络错误重试（!68, d24085e0）

### Task 3.1: SSE 自动重试
**File:** `apps/web/lib/sse.ts`

- [x] 网络错误自动重试 3 次
- [x] 指数退避 1s / 2s / 4s

**Verification:** 模拟网络断开后 SSE 自动重连

---

## Phase 4: SSE Recovery 合并（!77, 417d2760）

### Task 4.1: fix/sse-recovery 分支合并
- [x] 合并 sse-recovery 相关修复到 release

**Verification:** SSE 断线重连后消息不丢

---

## Phase 5: 历史分页 + 占位过滤（!95, ef5969c5）

### Task 5.1: 分页合并函数
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] `mergeMessagesById`
- [x] `mergeSessionMessagePages`
- [x] `prependOlderConversationMessages`
- [x] `areConversationMessagesEqual`

### Task 5.2: 占位消息过滤
**File:** `apps/web/src/lib/message-filters.ts`

- [x] `isPlaceholderAssistantMessage` — `(no output)` / `NO_REPLY`
- [x] `isVisibleConversationMessage` 更新
- [x] `message-filters.test.ts`

### Task 5.3: 加载更早消息 UI
**Files:** `MessageList.tsx`, `ConversationPanel.tsx`, `SuperLobsterPage.tsx`

- [x] 加载更早按钮 + 滚动位置保持
- [x] `nextCursor` / `hasMore` 状态管理
- [x] OpenClaw 时间戳前缀清理

**Verification:** 长会话可加载更早消息，顺序正确

---

## Phase 6: Tool 流事件 + 轮次排序（!111, 1352a9e9）

### Task 6.1: conversation-stream-events 模块
**File:** `apps/web/src/lib/conversation-stream-events.ts`

- [x] tool 流事件处理（426 行）
- [x] `mergeInFlightToolMessage`
- [x] `dedupeToolMessagesByCallId`
- [x] `readMessageToolCallId`
- [x] `conversation-stream-events.test.ts`

### Task 6.2: 轮次排序
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] `sortConversationMessages` — user → tool → assistant
- [x] `splitMessagesIntoTurns` / `coalesceOrphanTurnPrefixes` / `orderTurnMessages`
- [x] `dedupeAssistantMessages` 委托 sortConversationMessages
- [x] tool 消息合并集成 `conversation-stream-events`

### Task 6.3: draft 流事件序列
**File:** `apps/web/src/lib/conversationDraftStorage.ts`

- [x] `lastEventSeq` 字段支持

### Task 6.4: SuperLobsterPage SSE 重构
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] subscribe 恢复逻辑重构
- [x] 轮询间隔改为 500ms

**Verification:** `pnpm test` — all conversation tests pass

---

## Phase 7: OpenClaw 历史规范化（!112, 94e1a07e）

### Task 7.1: normalize-openclaw-history-messages
**File:** `apps/web/src/lib/normalize-openclaw-history-messages.ts`

- [x] `toolCall`/`toolResult`/`tool_use` → 标准 tool 消息
- [x] pending tool call 队列处理
- [x] `normalize-openclaw-history-messages.test.ts`

### Task 7.2: raw JSON 检测与合并优化
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] `isLikelyRawToolPayloadContent`
- [x] `preferAssistantDisplayContent`
- [x] `dedupeUserMessagesByContent`
- [x] `mergeDuplicateUserOnlyTurns`
- [x] `resolveConversationStillGenerating` / `shouldMergeDraftOnRefresh`
- [x] `mergeGeneratingConversationSnapshots`

### Task 7.3: mapApiMessagesToSuperLobster 集成
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] `normalizeOpenClawHistoryMessages` 在 map 前调用
- [x] 过滤 silent / placeholder assistant

### Task 7.4: 后端 tool streaming activeGeneration
**File:** `apps/api/src/zclaw/zclaw.service.ts`

- [x] `activeGeneration` 含 `tool + streaming`

**Verification:** 刷新后无 raw JSON assistant 气泡；无重复 user

---

## Phase 8: trustApiTerminal + 死循环修复（!113, cb3de4a6）

### Task 8.1: trustApiTerminal 参数
**File:** `apps/web/src/lib/conversationMessageMerge.ts`

- [x] `resolveConversationStillGenerating({ trustApiTerminal })`
- [x] `shouldMergeDraftOnRefresh({ trustApiTerminal })`
- [x] poll 路径 `trustApiTerminal: true`
- [x] hydrate 路径默认 `false`

### Task 8.2: 死循环修复
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] polling 仅 `shouldMergeDraft` 时传 draft
- [x] `shouldPoll` 扩展 in-flight 检查
- [x] ~~`isSessionApiExplicitlyComplete`~~（Phase 9 移除）
- [x] ~~`sessionDetailHydratedRef`~~（Phase 9 移除）

### Task 8.3: 测试覆盖
**File:** `apps/web/src/lib/__tests__/conversationMessageMerge.test.ts`

- [x] poll path trusts api terminal case
- [x] hydrate path recovers in-flight case

**Verification:** Network 面板无_burst 请求；生成结束后轮询停止

---

## Phase 9: 简化回归（205f9acb）

### Task 9.1: 移除过度设计
**Files:** `conversationMessageMerge.ts`, `SuperLobsterPage.tsx`, tests

- [x] 移除 `isSessionApiExplicitlyComplete` 及测试
- [x] 移除 `sessionDetailHydratedRef` / `sessionDetailHydratedTick`
- [x] 移除 `receivedStreamEvent` 过早结束逻辑
- [x] hydrate 路径回归简洁 `shouldMergeDraftOnRefresh` 调用

### Task 9.2: draft 持久化条件优化
**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- [x] `shouldPersist` 使用 `generatingSessionIdsRef` 替代仅看 active stream

**Verification:** `pnpm test` — conversationMessageMerge tests pass

---

## 最终验证

- [x] `pnpm test` — conversationMessageMerge + normalize + stream-events tests pass
- [x] `pnpm build` — web 构建通过
- [x] 人工验收 — 见 `tests/manual-acceptance.md`
