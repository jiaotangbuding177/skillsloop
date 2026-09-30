# 对话消息刷新恢复 — 失败经验与优化总结

> **变更：** conversation-refresh-recovery
> **时间跨度：** 2026-06-11（!62）→ 2026-06-26（205f9acb）
> **最终态提交：** `205f9acb`

---

## Phase 0 初始设计局限

### 当时为什么这样设计

- 刷新丢消息是最高优先级问题，先用最小方案：`sessionStorage` + 按 ID 合并 + `createdAt` 排序
- 2s 轮询作为 SSE 断开的 fallback

### 遗留问题（后续 Phase 逐步修复）

| 局限 | 影响 | 修复 Phase |
|------|------|------------|
| 全局 `createdAt` 排序 | assistant 跑到 user 上方 | Phase 6 |
| 无 user 内容去重 | 重复 user 气泡 | Phase 2 部分，Phase 7 彻底 |
| 无 tool 消息处理 | raw JSON 当 assistant 渲染 | Phase 6–7 |
| 无 `activeGeneration` | 前端只能靠 streaming 状态猜 | Phase 1 |
| 轮询 2s 间隔 | 生成中更新偏慢 | 后续改为 500ms |

---

## 事件 1：刷新后消息顺序错乱

### 现象

assistant 回复显示在 user 提问上方，tool 消息穿插位置错误。

### 根因

OpenClaw 历史消息的 `createdAt` 不可靠；Phase 0 全局按时间排序无法保证对话轮次结构。

### 尝试过的方案

- Phase 2：仅在 merge 时按 ID 匹配，未解决排序
- Phase 5：`mergeSessionMessagePages` 处理分页重叠，但排序仍靠 `createdAt`

### 最终方案（Phase 6）

- `sortConversationMessages`：按 user 切分轮次 → 每轮内 user → tool → assistant
- `coalesceOrphanTurnPrefixes`：处理 orphan 前缀
- `orderTurnMessages`：轮内 assistant 多条合并为一条

### 测试

- `conversationMessageMerge.test.ts` — `sortConversationMessages` 相关 cases

---

## 事件 2：刷新后出现重复 user 气泡

### 现象

同一问题出现 2~3 个 user 消息（如「生成一篇量子力学的 SCI 论文附录」）。

### 根因

API 历史与 sessionStorage draft 各存一份 user，ID 不同但内容相同。

### 尝试过的方案

- Phase 2 `hasMatchingUserMessage`：merge 时跳过重复 user draft，但未处理已合并后的多轮次

### 最终方案（Phase 7）

- `dedupeUserMessagesByContent`：轮内按内容去重
- `mergeDuplicateUserOnlyTurns`：合并仅含重复 user 的空轮次

### 测试

- `duplicate user recovery` case in `conversationMessageMerge.test.ts`

---

## 事件 3：raw tool JSON 被当成 assistant 气泡

### 现象

刷新后显示 `{"query":"...","provider":"tavily"}` 而非自然语言回复。

### 根因

1. OpenClaw 历史返回 `toolCall`/`toolResult` 非标准 role
2. API assistant 消息 content 可能是 tool 搜索结果的 JSON 快照
3. draft 中有自然语言 in-flight 内容

### 最终方案

- Phase 7：`normalizeOpenClawHistoryMessages` — toolCall+toolResult → 标准 tool 消息
- Phase 7：`preferAssistantDisplayContent` + `isLikelyRawToolPayloadContent` — 合并时优先自然语言
- Phase 5：`isPlaceholderAssistantMessage` — 过滤 `(no output)` 占位

### 测试

- `normalize-openclaw-history-messages.test.ts`
- `assistant raw tool payload merge` case

---

## 事件 4：生成已结束却被 stale draft 误判

### 现象

轮询永远不停止；或刷新后输入框仍 disabled。

### 根因

sessionStorage draft 的 `isStreaming=true` 滞后于 API `activeGeneration=false`。

### 尝试过的方案（Phase 8，已废弃）

- `isSessionApiExplicitlyComplete`：额外判断 API 是否明确完成
- `sessionDetailHydratedRef`：hydrate 完成前阻止 polling

### 最终方案（Phase 8 bugfix + Phase 9 简化）

- `trustApiTerminal` 参数分离两条路径：
  - 轮询 `true`：API false → 立即结束
  - hydrate `false`：允许 draft 恢复
- Phase 9 移除 `isSessionApiExplicitlyComplete`，回归 `trustApiTerminal` 单一机制

### 测试

- `resolveConversationStillGenerating` — 4 cases 覆盖 poll/hydrate 路径

---

## 事件 5：刷新过程 useEffect 死循环

### 现象

Network 面板反复请求 `/api/zclaw/chat/sessions/{id}/messages`。

### 根因

1. polling effect 在 hydrate 完成前启动
2. `SET_MESSAGES` 触发依赖 `state.messages` 的计算值重算
3. polling 无条件传 draft 导致 merge → dispatch → 再 poll

### 最终方案（Phase 8）

- polling 传 `trustApiTerminal: true`
- 仅 `shouldMergeDraft` 为 true 时才传 draft 给 `resolveConversationStillGenerating`
- `shouldPoll` 扩展：检查 `hasInFlightConversationMessages(currentMessagesRef)`
- 交叉引用：`useeffect-circular-dependency/spec.md` — ref 守卫

### 测试

- 人工：Network 面板仅 1 次 hydrate + 周期性 poll，无_burst 请求

---

## 事件 6：历史会话记录展示不全

### 现象

长会话只能看到最近 50 条，无法加载更早消息。

### 根因

初始只拉取第一页，无分页 prepend 逻辑。

### 最终方案（Phase 5）

- `prependOlderConversationMessages` + `mergeSessionMessagePages`
- `MessageList` 加载更早按钮 + 滚动位置保持
- `nextCursor` / `hasMore` 状态管理

### 测试

- `prependOlderConversationMessages` unit test
- 人工：点击加载更早，消息顺序正确且无重复 ID

---

## 事件 7：SSE 断线恢复不稳定

### 现象

网络抖动后消息丢失或重复；subscribe 无事件时过早结束生成。

### 根因

- 无 SSE 重试机制
- tool 流事件未统一处理
- `receivedStreamEvent` 误判（Phase 8 引入，Phase 9 移除）

### 最终方案

- Phase 3：SSE 网络错误自动重试 3 次（1s/2s/4s 指数退避）
- Phase 4：fix/sse-recovery 分支合并
- Phase 6：`conversation-stream-events.ts` + `lastEventSeq`
- Phase 9：移除 `receivedStreamEvent` 过早结束逻辑

---

## 事件 8：tool streaming 未计入 activeGeneration

### 现象

仅 tool 在 streaming 时，前端认为生成已结束，轮询停止。

### 根因

后端 `hasActiveLocalGeneration` 只检查 `assistant + streaming`。

### 最终方案（Phase 7）

```ts
message.status === 'streaming' &&
(message.role === 'assistant' || message.role === 'tool')
```

---

## 废弃方案详细记录

### isSessionApiExplicitlyComplete（Phase 8 → 9）

**引入动机：** hydrate 时想更精确判断「API 已明确完成」以跳过 draft 合并。

**为什么不 work：**
- 与 `trustApiTerminal` 逻辑重叠
- 需要额外的 `sessionDetailHydratedRef` 协调 polling 时机
- 增加状态机复杂度，边界 case 增多

**替代方案：** `trustApiTerminal` 参数在 `resolveConversationStillGenerating` / `shouldMergeDraftOnRefresh` 中统一处理。

### sessionDetailHydratedRef + sessionDetailHydratedTick（Phase 8 → 9）

**引入动机：** 防止 polling 在 hydrate 完成前启动导致死循环。

**为什么不 work：**
- `setSessionDetailHydratedTick` 本身触发 effect 重跑
- 与 `loadingSessionIdRef` 守卫功能重叠

**替代方案：** ref 守卫 + `shouldPoll` 条件收紧 + `trustApiTerminal`。

### receivedStreamEvent（Phase 8 → 9）

**引入动机：** SSE subscribe 重连后若未收到任何事件，认为流已结束。

**为什么不 work：** 正常重连场景可能短暂无事件，导致过早 `finishGeneratingSession` + `clearConversationDraft`。

**替代方案：** 依赖 `activeGeneration` API 轮询 + `resolveConversationStillGenerating` 判定。

---

## 优化点汇总

| 优化 | Phase | 说明 |
|------|-------|------|
| 纯函数下沉 | 0→9 | 合并逻辑全在 lib，组件只做编排 |
| 测试驱动 | 2→7 | 每个坑点有 unit test 回归 |
| 轮询间隔 | 0→6 | 2s → 500ms |
| draft 持久化条件 | 9 | `generatingSessionIdsRef` 替代仅看 active stream |
| 占位消息过滤 | 5 | 减少空白 assistant 气泡 |
| 消息相等浅比较 | 5 | `areConversationMessagesEqual` 避免无效 dispatch |
| 请求序列号 | 0 | `generationPollRequestSeqRef` 防竞态 |

---

## Lessons（沉淀至 config.yaml）

- **R-40**: 对话消息排序必须按轮次（user → tool → assistant），禁止全局 `createdAt` 排序作为最终顺序
- **R-41**: OpenClaw 历史消息必须先 `normalizeOpenClawHistoryMessages` 再渲染
- **R-42**: 轮询与 hydrate 对 API 终端标志必须分离：`trustApiTerminal=true`（poll）vs `false`（hydrate）
- **R-43**: 已移除 `isSessionApiExplicitlyComplete`，勿再引入类似 hydration 守卫；用 `trustApiTerminal` 统一处理
- **R-44**: API+draft 合并后必须 `sortConversationMessages`，并处理重复 user-only 轮次
- **R-45**: assistant 合并时检测 raw tool JSON（`isLikelyRawToolPayloadContent`），优先自然语言内容
- **R-46**: 后端 `activeGeneration` 必须包含 tool `streaming` 状态，不仅 assistant
- **R-47**: SSE subscribe 恢复不可仅凭「是否收到事件」判断结束；依赖 API 轮询 + `resolveConversationStillGenerating`
- **R-48**: 刷新恢复相关纯逻辑必须提取到 `lib/` 并写 unit test，禁止在组件内内联合并逻辑
