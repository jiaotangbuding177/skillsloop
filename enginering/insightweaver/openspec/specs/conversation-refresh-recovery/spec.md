# Conversation Refresh Recovery (Reusable Spec)

> 从 conversation-refresh-recovery 变更（Phase 0 !62 → Phase 9 205f9acb）沉淀的可复用规范。

## Concept

Super Lobster 对话页在刷新、URL 直达、SSE 断线、生成中轮询时，需要从 **API 历史消息** + **sessionStorage draft** + **本地 in-flight 快照** 三路合并出正确的对话状态。

核心原则：
- 合并逻辑在 `lib/`，组件只做编排
- 排序按对话轮次，不按 `createdAt`
- 轮询与 hydrate 对 API 终端标志采用不同信任策略

## Architecture

```
API messages ──→ normalizeOpenClawHistoryMessages ──→ message-filters
                                                          │
sessionStorage draft ─────────────────────────────────────┤
                                                          ▼
                                          shouldMergeDraftOnRefresh
                                                          │
                                                          ▼
                                    mergeConversationMessagesWithDraft
                                                          │
                                                          ▼
                                    resolveConversationStillGenerating
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                          stillGenerating=true                        stillGenerating=false
                    mergeGeneratingConversationSnapshots              mergeSessionMessagePages
                                    │                                           │
                                    └─────────────────────┬─────────────────────┘
                                                          ▼
                                            sortConversationMessages
                                                          │
                                                          ▼
                                                    SET_MESSAGES
```

## Four Recovery Paths

| Path | Trigger | trustApiTerminal | Key function |
|------|---------|------------------|--------------|
| Hydrate | F5 / URL sessionId | `false` | loadConversationDraft → merge |
| Polling | generating / in-flight | `true` | 500ms poll → merge |
| Subscribe | SSE reconnect | N/A (stream events) | conversation-stream-events |
| Prepend | "加载更早" click | N/A | prependOlderConversationMessages |

## Core Modules

| Module | Path | Responsibility |
|--------|------|----------------|
| Draft storage | `conversationDraftStorage.ts` | sessionStorage read/write |
| Message merge | `conversationMessageMerge.ts` | merge, sort, dedupe, state resolve |
| History normalize | `normalize-openclaw-history-messages.ts` | toolCall/toolResult → tool |
| Stream events | `conversation-stream-events.ts` | SSE tool event handling |
| Message filters | `message-filters.ts` | placeholder / silent filtering |
| Orchestration | `SuperLobsterPage.tsx` | four paths wiring |
| Backend flag | `zclaw.service.ts` | `activeGeneration` |

## Key Behaviors

### 1. Message sort order (per turn)

```
user (content-deduped) → tools (callId-deduped) → other → assistant (merged)
```

Never use global `createdAt` sort as final order.

### 2. trustApiTerminal

| Value | Path | When apiActiveGeneration=false |
|-------|------|-------------------------------|
| `true` | polling | End immediately, ignore stale draft |
| `false` | hydrate | Allow draft recovery if sessionMarkedGenerating |

### 3. Draft merge decision (shouldMergeDraftOnRefresh)

- `apiActiveGeneration === false` + `trustApiTerminal` → do not merge draft
- Otherwise merge if `resolveConversationStillGenerating` or draft has in-flight

### 4. Assistant content merge

- Prefer natural language over raw tool JSON (`isLikelyRawToolPayloadContent`)
- API terminal status wins over draft sending
- Non-client ID (`assistant-draft-*`) preferred over client ID

### 5. OpenClaw history normalization

Must call `normalizeOpenClawHistoryMessages` before mapping to `SuperLobsterMessage`. Handles: `toolCall`, `toolResult`, `tool_use`, `function_call`, etc.

### 6. Backend activeGeneration

True when `activeConversationRuns.status === 'running'` OR any message has `status === 'streaming'` with role `assistant` or `tool`.

## Anti-Patterns

| Pattern | Why it fails | Correct approach |
|---------|--------------|------------------|
| Global `createdAt` sort | OpenClaw timestamps unreliable | `sortConversationMessages` by turn |
| Same trust policy for poll & hydrate | Stale draft blocks poll end, or hydrate loses in-flight | `trustApiTerminal` split |
| `isSessionApiExplicitlyComplete` guard | Overlaps trustApiTerminal, adds state complexity | Use trustApiTerminal only (removed Phase 9) |
| `sessionDetailHydratedRef` in deps | Triggers effect re-run loops | `loadingSessionIdRef` guard (see useeffect spec) |
| `receivedStreamEvent` to end generation | False positive on reconnect | API poll + resolveConversationStillGenerating |
| Inline merge in component | Untestable, duplicated logic | Extract to conversationMessageMerge.ts |
| Skip normalize step | Raw tool JSON renders as assistant | Always normalize before map |

## Lessons

- **R-40**: Sort by turn (user → tool → assistant), not global createdAt
- **R-41**: Always `normalizeOpenClawHistoryMessages` before render
- **R-42**: Split trustApiTerminal: true (poll) vs false (hydrate)
- **R-43**: Do not reintroduce isSessionApiExplicitlyComplete; use trustApiTerminal
- **R-44**: After API+draft merge, run sortConversationMessages + mergeDuplicateUserOnlyTurns
- **R-45**: Detect raw tool JSON in assistant merge; prefer natural language
- **R-46**: Backend activeGeneration must include tool streaming
- **R-47**: SSE subscribe must not end generation based solely on event receipt
- **R-48**: Extract merge logic to lib/ with unit tests

## Test Coverage

| File | Covers |
|------|--------|
| `conversationMessageMerge.test.ts` | merge, sort, dedupe, trustApiTerminal, duplicate user |
| `normalize-openclaw-history-messages.test.ts` | toolCall/toolResult conversion |
| `conversation-stream-events.test.ts` | tool stream event handling |
| `message-filters.test.ts` | placeholder / silent filtering |

Run: `pnpm --filter @insightweaver/web test src/lib/__tests__/conversationMessageMerge.test.ts`

## Related Files

- `apps/web/src/lib/conversationMessageMerge.ts`
- `apps/web/src/lib/conversationDraftStorage.ts`
- `apps/web/src/lib/normalize-openclaw-history-messages.ts`
- `apps/web/src/lib/conversation-stream-events.ts`
- `apps/web/src/lib/message-filters.ts`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
- `apps/api/src/zclaw/zclaw.service.ts`
- `openspec/specs/useeffect-circular-dependency/spec.md` — effect loop prevention
- `openspec/changes/archive/2026-06-26-conversation-refresh-recovery/retrospective.md` — full pitfall history

## Change Archive

Full evolution (Phase 0–9): `openspec/changes/archive/2026-06-26-conversation-refresh-recovery/`
