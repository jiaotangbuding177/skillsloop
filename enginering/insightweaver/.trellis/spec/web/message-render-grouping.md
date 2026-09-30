# Message Render Grouping: Turn Split → Tool Blocks → Display Sequence

会话消息从 state 到页面展示的分组管线契约（!278/!279/!280 三连修复沉淀）。

## 管线总览

```
API/DB (225 行, ASC)
  → mapApiMessagesToSuperLobster (normalize + filter 空段/NO_REPLY)
  → merge (prepend/append/draft, 按 id 去重)
  → sortConversationMessages (state 层轮次重排: [users, tools, assistants])
  → MessageList visibleMessages (isVisibleConversationMessage 过滤 + createdAt ASC 排序)  ← !280
  → groupConversationMessagesForDisplay (turn 切分 + 分组)                                 ← 本契约核心
  → React 渲染 (MessageBubble / ToolActivityGroup)
```

## 核心契约

### 1. 分组入口前置条件（!280）

`groupConversationMessagesForDisplay(messages, scope)` 的输入**必须已按 createdAt 升序**（调用方负责排序）。

- turn 划分（`splitMessagesIntoTurns`）按输入顺序中 user 的位置切轮——**输入非时间序时轮归属错误**（线上实证：14:29 轮中段被划入 14:46 turn，轮尾总结被中间段顶替）。
- 排序职责在调用方 `MessageList.tsx` 的 `visibleMessages` useMemo（filter 后 `.sort` 按 createdAt ASC）。
- **禁止**在 group 函数内重新加排序（职责分离，/improve-codebase-architecture 候选 1 已裁决）。

### 2. turn 划分规则

`user` 消息开启新 turn；`user` 之前（数组开头）的消息构成 orphan turn。同一 turn 内消息保持输入序。

### 3. groupSingleTurn 展示规则（合并模式，!285 修订；!291 规范序+空草稿豁免）

| turn 类型 | 渲染规则 |
|-----------|---------|
| 有 tool 穿插（agent 工作流） | 连续 tool 合并为一个执行块（ToolActivityGroup）；**只显示最后一条可见 assistant**（中间过程段隐藏，可点工具块展开） |
| 无 tool（纯文本轮） | user 全显示；assistant **只显示最后一条可见**（SSE 期间多段文本累积在同一条草稿，历史只显示最终回复与之对齐） |
| 空 assistant 段（content.trim()===''） | 跳过；**唯一豁免：轮内最后一条 assistant 且 status='sending'**——它是发送后/流式首包前安检动效与思考点的渲染载体（!291；一律丢弃会让等待期整块空白） |
| 输出顺序（!291） | **轮内规范序：user/其他 → 工具块 → 最终 assistant**，与 createdAt 时间戳解耦——实时工具消息（createdAt=插入时刻）、API 占位行（createdAt 早于工具行）、上游历史行（createdAt 晚于工具行）三种时间语义互相矛盾，按时间戳/输入序锚定工具块会让它在回复上下跳动（生成中/生成后/刷新后不一致，线上实证 2026-09-04） |

### 4. tools 块 computed 字段（!280）

```typescript
{
  type: 'tools';
  reactKey: `${scope}-tools-block-${turnStartIndex + toolBufferStart}`;
  messages: SuperLobsterMessage[];   // 连续 tool 行
  nextMessage?: SuperLobsterMessage; // 块后第一条消息（ToolActivityGroup 的 isRunning 判断依赖）
  startTime: string | null;          // 首条 tool 的 createdAt
  endTime: string | null;            // 末条 tool 的 completedAt ?? createdAt
  status: 'completed' | 'running' | 'failed'; // 末条 status: done→completed / sending→running / error→failed
}
```

`ToolActivityGroup` 组件 props 接收这三个字段（可选，未传时 fallback 自算，向后兼容）。

## Wrong vs Correct

### Wrong：state 层对 turn 结构做破坏性重排

```typescript
// !279 前的 orderTurnMessages：每轮全部 assistant 合并为一条（最新）
mergedAssistant = { ...sorted[sorted.length - 1] };  // 32 段 → 1 段，中间段永久丢失
```

渐进加载（p2→p3→p4 逐页 prepend）+ 每次 sort 重排 = 劈开固化：p2 时期轮尾总结成 orphan 被并入相邻轮并重排，后续页到场时 user 已在输入序中位于这些段之前，sort 无法归位。

### Wrong：coalesce 用时间阈值判 orphan 归属

```typescript
// !279：orphan 末条与下一 user 间隔 ≤30min 才并入
if (userTime - lastPrefixTime <= ORPHAN_COALESCE_MAX_GAP_MS) { ... }
```

时间阈值无法区分「时钟倒挂（秒级，须并入）」与「分页 orphan（任意间隔，须独立）」——13min 间隔的 14:29 轮照样劈开。入口稳定排序（!280）使 coalesce 输入恒为时间序，该场景不再产生错误归属；阈值保留仅防御历史 state。

### Correct：入口稳定排序 + 全段显示

```typescript
// MessageList.tsx
const visibleMessages = useMemo(
  () => messages.filter(...).sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()),
  [isStreaming, messages],
);
// groupConversationMessagesForDisplay 假设输入已排序，只做分组
```

## 验证矩阵

| 场景 | 期望 |
|------|------|
| 渐进加载 5 页后 state（劈开形态） | 14:29 轮 = user → 开工段 → 工具块(46) → ✅总结(835 字) |
| 同毫秒消息跨轮 | 保持输入序，user 不得前置吞掉前轮回复 |
| 同毫秒 user 与 assistant | user 开轮（输入序保证） |
| 无工具纯文本轮多条 assistant | 只显示最后一条非空 |
| 工具间空段 | 不渲染 |
| 空 sending 草稿（轮尾） | 保留渲染（安检动效/思考点载体，!291） |
| 实时序（工具 createdAt 晚于草稿） | 工具块在草稿上方（规范序，!291） |
| API 序（占位行早于工具行） | 工具块在最终回复上方（规范序，!291） |
| 生成中会话 | fast path 不触发（activeGeneration），SSE 实时视图为单草稿+工具行 |

## 测试锚点

- `group-conversation-messages.test.ts`：12 用例（连续工具块/合并模式/无工具轮/劈开归位/同毫秒保序/空草稿载体/实时序工具块/API 序工具块）
- `conversationMessageMerge.test.ts`：37 用例（!279 保留段/同内容合并/链式 loadOlder/大间隔 orphan）
- `conversation-stream-events.test.ts`：11 用例（含 !291 新建工具消息 createdAt 继承 in-flight 草稿）
- 回归测试输入**必须复刻线上 state 真实形态**（fiber dump / 故障数据序），不能用理想升序——理想序掩盖不了劈开 bug 与工具块错位

## SSE 工具消息 createdAt 契约（!285/!291）

新建工具消息的 createdAt **必须继承 in-flight assistant 草稿**（insertBeforeDraftId 指向的草稿 → 兜底最后一条 in-flight assistant），**禁止 `new Date()`**——展示层曾按 createdAt 排序，晚于草稿的时间戳把工具排到流式回复后。两处 SSE 处理面都要遵守：`useZclawChat.ts`（!285）与 `conversation-stream-events.ts applyToolStreamEvent`（!291，此前漏修）。终极防线是分组层规范序（与时间戳解耦），继承只是 state 层一致性。

## 排查入口（下次同类工单）

1. DB 行全吗（`isDeleted=false` 计数）
2. 接口翻页并集 vs DB 全集 diff（bsk evaluate 逐页收集 id + db-inspect 导出，comm 求差集）
3. React fiber dump 线上 state：`document.querySelector('[data-message-id]')` → `__reactFiber*` key → 沿 `.return` 找 `memoizedProps.messages`
4. 渲染管线离线复现：esbuild bundle 渲染函数（`--alias:@weblib=<dir>/lib`）+ 真实 API 数据
