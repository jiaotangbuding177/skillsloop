# State Management

## Overview

The application uses **no global state library** (no Redux, Zustand, Jotai, or similar). State is managed through three mechanisms:

1. **CustomEvent dispatch** on `window` - for cross-component communication (enterprise context)
2. **React Context providers** - for theme, locale, error handling, and UI concerns
3. **Page-level state** - `useState`/`useReducer` within each page component, with `sessionStorage` for filter persistence

## Enterprise Context Events

**File:** `apps/web/src/lib/enterprise-context.ts`

The enterprise context system uses `localStorage` + `CustomEvent` for loose coupling between components that need to react to enterprise changes.

### Storage Key

```typescript
export const ACTIVE_ENTERPRISE_STORAGE_KEY = 'zclaw:active-enterprise-id';
```

### Event Constants

```typescript
export const ACTIVE_ENTERPRISE_CHANGED_EVENT = 'zclaw:active-enterprise-changed';
export const AGENT_DISPLAY_CHANGED_EVENT = 'zclaw:agent-display-changed';
export const TOKEN_QUOTA_CHANGED_EVENT = 'zclaw:token-quota-changed';
export const ENTERPRISE_BRANDING_CHANGED_EVENT = 'zclaw:enterprise-branding-changed';
export const OPEN_BILLING_PURCHASE_EVENT = 'zclaw:open-billing-purchase';
```

### Setter Function

```typescript
export function setActiveEnterpriseId(enterpriseId: string) {
  const normalized = enterpriseId.trim();
  if (normalized) {
    window.localStorage.setItem(ACTIVE_ENTERPRISE_STORAGE_KEY, normalized);
  } else {
    window.localStorage.removeItem(ACTIVE_ENTERPRISE_STORAGE_KEY);
  }
  window.dispatchEvent(
    new CustomEvent(ACTIVE_ENTERPRISE_CHANGED_EVENT, {
      detail: { enterpriseId: normalized }
    })
  );
}
```

### Emit Functions

Each event type has a dedicated emitter:

| Function | Event | Purpose |
|----------|-------|---------|
| `setActiveEnterpriseId()` | `ACTIVE_ENTERPRISE_CHANGED_EVENT` | User switches enterprise |
| `emitAgentDisplayChanged()` | `AGENT_DISPLAY_CHANGED_EVENT` | Agent display settings updated |
| `emitTokenQuotaChanged()` | `TOKEN_QUOTA_CHANGED_EVENT` | Token quota refreshed |
| `emitEnterpriseBrandingChanged()` | `ENTERPRISE_BRANDING_CHANGED_EVENT` | Branding/logo updated |
| `emitOpenBillingPurchase()` | `OPEN_BILLING_PURCHASE_EVENT` | Open billing dialog (with tab: 'monthly'/'storage'/'token') |

### Consuming Events in Components

Components subscribe to events with `useEffect`:

```typescript
'use client';
import { ACTIVE_ENTERPRISE_CHANGED_EVENT, getActiveEnterpriseId } from '@/lib/enterprise-context';

function EnterpriseSensitiveComponent() {
  const [enterpriseId, setEnterpriseId] = useState(getActiveEnterpriseId());

  useEffect(() => {
    function handler(e: Event) {
      const detail = (e as CustomEvent).detail;
      setEnterpriseId(detail.enterpriseId);
    }
    window.addEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handler);
    return () => window.removeEventListener(ACTIVE_ENTERPRISE_CHANGED_EVENT, handler);
  }, []);

  // ...
}
```

### Enterprise Header Injection

`withActiveEnterpriseHeader()` reads the current enterprise ID from `localStorage` and adds it to request headers:

```typescript
export function withActiveEnterpriseHeader(headersInit?: HeadersInit) {
  const headers = new Headers(headersInit || {});
  const enterpriseId = getActiveEnterpriseId();
  if (enterpriseId) {
    headers.set('x-enterprise-id', enterpriseId);
  } else {
    headers.delete('x-enterprise-id');
  }
  return headers;
}
```

This is called automatically by the API client for `/api/zclaw/*` requests.

### Chat Workspace Reset

When the enterprise changes on the main chat page, the session needs to be reset:

```typescript
export function shouldResetChatWorkspaceOnEnterpriseChange(pathname: string) {
  return pathname === '/';
}
```

## React Context Providers

Composed in `apps/web/src/app/[locale]/layout.tsx`:

| Provider | Purpose |
|----------|---------|
| `NextIntlClientProvider` | Provides locale and translation functions |
| `ThemeProvider` | Dark/light mode toggle, persisted in localStorage |
| `ErrorHandlerProvider` | Subscribes to `insightweaver:api-error` events, renders toasts |
| `LocaleSyncProvider` | Keeps locale in sync across navigation |
| `Tooltip.Provider` | Radix UI tooltip portal configuration |
| `ToastProvider` | Sonner toast container and configuration |

### InsufficientCreditsDialog

Not a Context provider, but a global component mounted in the locale layout. It listens for the `insufficientCredits` event (emitted by the API client on error code 4001) and shows a modal prompting the user to purchase credits.

## Page-Level State

### useState / useReducer

Each page manages its own state. Typical patterns:

```typescript
// List page
const [items, setItems] = useState<Item[]>([]);
const [loading, setLoading] = useState(true);
const [filters, setFilters] = useState<Filters>(defaultFilters);

// Form page
const [formData, setFormData] = useState<FormData>(initialState);
const [submitting, setSubmitting] = useState(false);
```

### sessionStorage for Filter Persistence

List pages persist their filter state in `sessionStorage` so that navigating away and back (within the same tab session) restores the filters:

```typescript
const STORAGE_KEY = 'admin-users-filters';

function loadFilters(): Filters {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : defaultFilters;
  } catch {
    return defaultFilters;
  }
}

// On filter change:
sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
```

### conversationDraft: 只持久化恢复所需最小集（2026-08-07 教训）

**Problem**: `saveConversationDraft`（`conversationDraftStorage.ts`）在生成中轮询时把**完整消息列表**（`mergedMessages`）写入 sessionStorage。刷新后 `mergeConversationMessagesWithDraft` 把全部历史重新合并——tool 消息无条件 push、assistant 错误匹配 → **历史消息重复显示**（线上 `conv_05a1114102cf` 复现：draft 含 47 条完整历史）。

**根因链**：
1. 生成中轮询 → `saveConversationDraft({ messages: mergedMessages })` 保存全部历史
2. 刷新 → `loadConversationDraft` 读回全部历史 → `mergeConversationMessagesWithDraft(api, draft)` 合并
3. draft 中已完成的 tool/toolResult 被无条件 push、assistant 被错误匹配 → 重复
4. merge 后的完整列表被再次 `saveConversationDraft` 存回 → 恶性循环

**Solution**: 三层防御——

| 层 | 位置 | 规则 |
|---|------|------|
| **保存端** | `saveConversationDraft` | `filterPersistableDraftMessages`: 只持久化 in-flight（`sending`）消息 + 带 files 的 user 消息；已完成的 assistant/tool/toolResult 以 API 为权威 |
| **加载端** | `loadConversationDraft` | 同样过滤，兼容旧格式 |
| **合并端** | `mergeConversationMessagesWithDraft` 入口 | 过滤 draft：只处理 in-flight + user + assistant（assistant 可能含比 API 更新的流式内容） |

**关键原则**：draft 的语义是「刷新后恢复**生成中**的本地状态」——in-flight streaming、用户输入、附件——**不是**整个会话历史的缓存。历史以 API 为权威。

**相关**：`mergeGeneratingConversationSnapshots` 的 `olderLocal` 补回同样会误补回 UUID 副本（id 与 trusted 不同但内容相同）→ 增加 `hasMatchingUserMessage` 内容去重。

### 生成轮询必须有停滞/错误超时（2026-08-07 教训）

**Problem**: 后端 streaming 状态卡死时（KM Agent 挂起但 assistant 消息永远停在 `status: "streaming"`、`activeGeneration: true` 不清除），前端轮询 `GET /api/zclaw/chat/sessions/{id}/messages?limit=50` 每 500ms 无限重发（线上 `conv_638711012f0a` 复现：40+ 次请求）。轮询 effect（`SuperLobsterPage.tsx`）的停止条件依赖 `finishGeneratingSession` 清除 `generatingSessionIds`，而后端不报终态 → 死循环。

**根因链**：
1. `poll()` 计算 `stillGenerating = activeGeneration ?? isApiSessionStillGenerating(messages)` → true
2. `stillGenerating` → `upsertGeneratingSession()` 保持会话在 `generatingSessionIds`
3. effect 的 `shouldPoll` 恒为 true → interval 永远不清除
4. `catch {}` 静默吞掉 403/3001 等错误，`generatingSessionIds` 不清除

**Solution**: `forceStopPolling()`（抽出的公共结束函数）——连续无进展或连续错误超阈值时：

| 检测 | 阈值 | 结束动作 |
|------|------|---------|
| 内容停滞（消息签名 `id:status:content长度` 连续无变化） | 120 次 = 60s | `cancelled=true` + `clearInterval(timer)` + `finishGeneratingSession` + `clearConversationDraft` + `finalizeInterruptedConversationMessages`（in-flight 收尾为 aborted） |
| 连续错误 4xx（401/403/404） | 10 次 = 5s | 同上（权限丢失不可恢复，快速结束） |
| 连续错误 5xx/网络 | 60 次 = 30s | 同上（短暂抖动慢速重试） |

**关键原则**（CR 教训）：
- 强制结束分支**必须**真正停止 interval（`clearInterval` + `cancelled=true`）——否则 `setInterval` 继续发请求，且 `hasInFlightConversationMessages` 仍为 true 导致 effect 重启后再轮询
- **必须**收尾 in-flight 消息为 `aborted`（`finalizeInterruptedConversationMessages`），否则消息永远停在"生成中"
- 区分错误类型：`error instanceof ApiError && (status 401|403|404)` 才快速结束，5xx 可能瞬时抖动
- 消息签名要含 `status`（内容长度不变但状态在变时不算停滞）

**测试**：`conversationDraftStorage.test.ts` 覆盖 draft 最小集过滤；轮询超时逻辑在组件内（无纯函数 seam），后续可抽 `resolvePollStaleDecision` 纯函数便于单测。

### 约束：停滞计数器必须用 ref 持久化（2026-08-10 教训）

**问题**：`stalePollCount` / `lastContentSignature` 若用 effect 内局部变量，SSE 重连（`stream/subscribe` abort → 重建）会触发轮询 effect 重跑（`requestSeq` 递增），局部变量归零 → 60s 停滞检测永不触发 → 无限轮询回归。

**规则**：停滞计数器必须用模块级 ref（按 sessionId 索引），跨 effect 运行持久化；生成结束/强制结束时清理条目防内存泄漏：

```typescript
const generationPollStaleCountRef = React.useRef<Record<string, number>>({});
const generationPollLastSignatureRef = React.useRef<Record<string, string>>({});

// poll() 内：
const prevSignature = generationPollLastSignatureRef.current[targetSessionId];
if (contentSignature === prevSignature) {
  generationPollStaleCountRef.current[targetSessionId] =
    (generationPollStaleCountRef.current[targetSessionId] ?? 0) + 1;
} else {
  generationPollStaleCountRef.current[targetSessionId] = 0;
}
generationPollLastSignatureRef.current[targetSessionId] = contentSignature;
if (generationPollStaleCountRef.current[targetSessionId] >= GENERATION_POLL_STALE_LIMIT) {
  forceStopPolling();
}
```

**关键**：SSE 重连依赖（`subscribeRetrySignal`、`isViewingSessionGenerating`）变化会重建轮询 effect——任何"跨 effect 生命周期必须保留"的计数/签名都必须放 ref。

### 约束：停滞检测必须豁免工具执行期（2026-08-18 与后端 12h 工具预算对齐）

**问题**：PPT 等长任务在 `tool.started` -> `tool.completed/failed` 之间数分钟无新消息，后端 `activeGeneration` 一直为 true（任务正常执行），但前端内容签名 60s 无变化就 `forceStopPolling`——把执行中的任务标为 `aborted` 并清 draft（与后端 120s idle 误杀同源，后端已改工具预算 12h）。

**规则**：有 tool 消息处于 `sending`（工具执行期，API streaming 状态映射为 SuperLobsterMessage 的 sending）时重置停滞计数，不算停滞：

```typescript
const hasRunningTool = mergedMessages.some(
  (m) => m.role === "tool" && m.status === "sending",
);
if (hasRunningTool) {
  generationPollStaleCountRef.current[targetSessionId] = 0;
  generationPollLastSignatureRef.current[targetSessionId] = "";
} else {
  // ...原签名对比逻辑
}
```

**关键**：停滞检测的语义是「后端确认还在生成但前端无进展」——工具执行期无进展是正常业务行为，必须豁免；后端状态（`apiActiveGeneration`）才是生成是否结束的权威来源。中断收尾文案为「已停止生成，请重新发送消息」，引导用户手动重发。

### Common Mistake: SuperLobsterMessage.status 没有 "streaming"（2026-08-18 CI 教训）

**Symptom**: CI `next build` 报 `This comparison appears to be unintentional because the types ... and '"streaming"' have no overlap`，本地 `apps/api` 的 tsc 查不出来。

**Cause**: `SuperLobsterMessage["status"]` 类型是 `"sending" | "sent" | "error" | "aborted"`（`apps/web/src/types/super-lobster.ts`）。API 的 `"streaming"` 状态在 `mapApiMessageStatus` 中被映射为 `"sending"`——**前端类型里没有 `"streaming"`**。判断"工具还在执行"要用 `m.status === "sending"`（配合 `m.role === "tool"`），写 `"streaming"` 会编译报错。

**Fix**: `m.role === "tool" && m.status === "sending"`。

**Prevention**: 改动 SuperLobsterPage 前先确认消息状态枚举值（看 `super-lobster.ts` 类型而非 API 语义）；改 Web 代码后必须跑 `cd apps/web && npx tsc --noEmit`，只跑 api 的 tsc 检查不到 Web 文件。

## Error Event System

**Event name:** `insightweaver:api-error`

The API client dispatches this via `emitError()` (in `src/lib/error-handler.ts`). The `ErrorHandlerProvider` subscribes to it and shows toasts. This is a one-way data flow: API layer -> event -> provider -> toast.

The event target is a singleton `EventTarget` stored on `window.__insightweaverErrorEventTarget`.

## What is NOT Used

- No Redux, Zustand, Jotai, Valtio, or MobX
- No React Query or SWR for data fetching (raw `useEffect` + `useState`)
- No global store or reducer
- No URL-based state management (searchParams are read directly, not synced)

## GET Request Deduplication

**File:** `apps/web/lib/api-client.ts`

The API client prevents duplicate concurrent GET requests from React StrictMode double-mounting and component re-renders. A `Map<string, Promise<unknown>>` tracks in-flight requests, and duplicate GET requests to the same URL return the shared pending Promise.

### Scope

```typescript
  private buildDedupKey(method: string, url: string, body: unknown): string | null {
    if (method !== 'GET') return null;
    const parsed = new URL(url);
    // 2026-08-11: 新增 /api/auth/me——页面多组件并发 bootstrap 导致
    // auth/me 被调 3 次，加入去重后降至 1-2 次
    if (
      parsed.pathname.startsWith('/api/zclaw') ||
      parsed.pathname.startsWith('/api/agents') ||
      parsed.pathname.startsWith('/api/enterprises') ||
      parsed.pathname === '/api/auth/me'
    ) {
      return `${method}:${url}${body ? ':' + JSON.stringify(body) : ''}`;
    }
    return null;
  }
```

**Rules:**
- Only GET requests are deduplicated
- Only zclaw, agents, enterprises, and auth/me endpoints are covered (high-frequency repeated call sources)
- POST/PUT/PATCH/DELETE never deduplicate
- Pass `skipDedup: true` in `ApiRequestConfig` to opt-out

### Anti-Pattern: Unbounded map growth

The `inFlightRequests` map only holds active promises. When a promise resolves or rejects, it's removed from the map. No manual cleanup is needed.

### Gotcha: 请求去重缓存的登出竞态（2026-08-10 教训）

> **Warning**: 模块级 Promise 缓存（`currentUserPromise`）在请求 in-flight 期间用户登出/过期时，`.then` 回调仍会执行 `saveCurrentUser(response.user)` **写回 localStorage**——撤销登出、静默重新登录。
>
> 修复：`.then` 回调内先检查 `getCurrentUser()`，已登出（null）则丢弃结果返回 null，不得写回：
>
> ```typescript
> currentUserPromise = getMeApi()
>   .then(response => {
>     // 登出/过期竞态保护：请求 in-flight 期间用户可能已登出，
>     // 此时不得再写回当前用户（否则撤销登出）
>     if (!getCurrentUser()) return null;
>     saveCurrentUser(response.user, { emitLoginEvent: false });
>     return response.user;
>   })
>   .catch(() => null)
>   .finally(() => { currentUserPromise = null; });
> ```
>
> **适用面**：任何把"写回全局状态"放在异步请求 `.then` 中的场景（认证信息、会话 token 等），都必须考虑请求期间状态可能已失效。

### Ref-based dependency avoidance

When a `useEffect` dependency array causes excessive re-fetching (e.g., `skillMarketItems` changing with every market API resolve), use a `useRef` to track the latest value without triggering effects:

```typescript
// WorkbenchRailPanel.tsx
const skillMarketItemsRef = React.useRef(skillMarketItems);
React.useEffect(() => {
  skillMarketItemsRef.current = skillMarketItems;
}, [skillMarketItems]);

// In the effect that needs the value:
{ mapAgentDisplayToInstalledRecord(agent, skillMarketItemsRef.current) }
//                                                      ↑ ref, not state
// Dependency array: [activeEnterpriseId] — NOT [skillMarketItems]

## Conversation Draft State (SSE + Polling)

**File:** `apps/web/src/lib/conversationDraftStorage.ts`

Draft state persists in-flight messages during SSE streaming and handles recovery after page refresh.

### Storage Key Pattern

```typescript
function buildMessagesStorageKey(sessionId: string): string {
  return `zclaw:draft:${sessionId}`;
}
```

### What to Persist (Minimal Set)

**Rule**: Only persist messages needed for recovery, not the entire history.

```typescript
function filterPersistableDraftMessages(
  messages: SuperLobsterMessage[],
): SuperLobsterMessage[] {
  return messages.filter(
    (message) =>
      message.status === 'sending' ||
      message.role === 'user',  // ✅ Keep ALL user messages (local-only copy)
  );
}
```

**Why `role === 'user'` (not `message.files?.length`)?**
- User messages without attachments are also local-only until backend persists them
- Filtering only messages with files causes plain-text user messages to be lost on refresh

### When to Save

1. **During SSE streaming**: After each `delta` event → `flushConversationDraft()`
2. **Before page unload**: `beforeunload`/`pagehide` event → `flushConversationDraft()`

### When to Merge on Refresh

**File:** `apps/web/src/lib/conversationMessageMerge.ts`

```typescript
export function shouldMergeDraftOnRefresh(options: {
  apiActiveGeneration?: boolean | null;
  messages: SuperLobsterMessage[];
  draft?: ConversationDraftSnapshot | null;
  sessionMarkedGenerating?: boolean;
  trustApiTerminal?: boolean;
}) {
  if (options.apiActiveGeneration === false) {
    if (options.trustApiTerminal) {
      // ✅ Merge draft if it has ANY user messages (with or without files)
      return draftHasUserMessages(options.draft);
    }
    // ...
  }
  // ...
}

function draftHasUserMessages(draft): boolean {
  return draft?.messages?.some((m) => m.role === 'user') ?? false;
}
```

**Common Mistake**: Using `draftHasUserFiles()` instead of `draftHasUserMessages()` causes plain-text user messages to be lost on refresh when `apiActiveGeneration === false` and `trustApiTerminal === true`.

### Status Mapping on Bootstrap

**File:** `apps/web/src/hooks/useZclawChat.ts`

```typescript
const mapSessionDetailMessage = (
  message: ZclawSessionDetailMessage,
): ZclawChatMessage => {
  const status: ZclawChatMessage['status'] =
    message.status === 'error' ? 'error'
    : message.status === 'streaming' ? 'streaming'  // ✅ Preserve streaming state
    : 'done';
  // ...
};
```

**Gotcha**: Mapping `streaming` → `done` loses the in-flight state, causing:
- `isApiSessionStillGenerating()` returns false → polling doesn't start
- Draft not merged → user messages lost

### Polling Effect Triggers

Polling starts when ANY of these is true:

1. `generatingSessionIds.has(targetSessionId)` — session marked as generating
2. `hasInFlightConversationMessages(messages)` — messages with `status === 'sending'`

**Anti-Pattern**: If `finishGeneratingSession()` is called before refresh (e.g., SSE disconnects but backend still generating), `generatingSessionIds` won't have the session, and polling won't start.

**Fix**: Query `activeGeneration` from backend before calling `finishGeneratingSession()`:
```typescript
// SuperLobsterPage.tsx: finally block
let backendStillGenerating = false;
try {
  const statusPage = await getZclawSessionMessagesApi(sessionId, { limit: 1 });
  backendStillGenerating = statusPage.activeGeneration === true;
} catch {}
if (!backendStillGenerating) {
  finishGeneratingSession(sessionId);
  clearConversationDraft(sessionId);
}
```

## File Preview Blob URL 生命周期（2026-08-08 教训）

**File**: `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

### 核心问题：blob URL 跨刷新失效

上传图片时 `URL.createObjectURL(file)` 生成的 blob URL **绑定当前页面 document**——刷新后 blob 对象销毁，URL 全部失效。任何把 blob URL 存入 sessionStorage/draft 的行为都**无法**在刷新后恢复预览。

### 三层约束

| 约束 | 规则 | 原因 |
|------|------|------|
| 1. 恢复来源 | 刷新后用 `downloadWorkspaceFileBlob(path)` 重新下载生成新 blob URL | 文件已上传到工作区，path 可重新拉取 |
| 2. previewMap 持久化 | 恢复成功后写入 sessionStorage previewMap（`persistMessageFilePreviews`），轮询重建消息时 `file.previewUrl \|\| previewMap[key]` 回退 | 轮询用 API 数据重建消息会丢失内存中的 previewUrl |
| 3. revoke 管理 | 恢复的 blob 只注册 `previewUrlsRef`，由 unmount cleanup 统一 revoke | `scheduleRevokePreviewUrl`（2s 后 revoke）会立即销毁刚恢复的预览；恢复时 revoke 旧 URL 会让 previewMap 引用的 URL 失效 |

### 竞态陷阱（多文件并发恢复）

恢复 effect 依赖 `state.messages`，**每个下载完成 `setSessionMessages` 都会触发 effect 重跑**，旧 effect cleanup 设 `cancelled=true` 会取消其他在途下载。必须：

1. **下载启动前**先 reserve key（`restoredPreviewKeysRef.add`），effect 重跑时 filter 跳过已 reserve 项，避免重复下载
2. **下载完成后无论 cancelled 与否**都写 previewMap + 更新消息（cancelled 只阻止未来下载，已完成的下载必须完成消息更新，否则当前渲染仍引用旧失效 blob）
3. **bootstrap 完成时清空恢复标记**（`isBootstrapping` true→false）——刷新后旧 blob 失效但 key 占位会阻止重新恢复

### 判定函数

```typescript
export function getFilesNeedingPreviewRestore(messages) {
  // 图片 + 有 path + (previewUrl 缺失 或 blob: URL)
  // blob: URL 视为 stale——刷新后必然失效
}
```

**Gotcha**: `isSameUserMessageContent` 的 `endsWith` 前缀匹配专为 user 消息设计（系统注入前缀），**assistant 消息内容比较必须用精确相等**（`normalizeComparableContent(a) === b`），否则误判不同回复为重复。

## 工作台首屏加载优化（2026-08-09 教训）

**Files**: `apps/web/src/hooks/useZclawChat.ts`（Phase A）, `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`（Phase B）

### 核心问题：loading 屏等待最慢 API

工作台首屏有两道 loading 门：`state.loading`（"正在加载EvoMind工作台..."）和 `isBootstrapping`（"正在加载 EvoMind 状态..."）。两者都在所有 API 完成后才解除，用户卡 10-24s。

### 两阶段优化

| 阶段 | 瓶颈 | 优化 |
|------|------|------|
| Phase A (`useZclawChat.bootstrap`) | status -> usage -> sessions 串行 | usage 与 sessions 无依赖，`Promise.all` 并行 |
| Phase B (`SuperLobsterPage` main effect) | `SET_LOADING false` 在 `finally` 等 detail(5-12s) | messages 渲染后立即 `SET_LOADING false`，detail 后台补充 `historyDetailState` |

### 关键约束

1. **`SET_LOADING false` 必须在 messages `SET_MESSAGES` 之后**：messages 先渲染到 DOM，再解除 loading 屏，否则用户看到空白闪烁
2. **`finally` 块改为兜底**：仅在 `loadingSessionIdRef.current === ownSessionId` 时才 dispatch `SET_LOADING false`（error/early-return 路径）。正常路径已在阶段 1 提前解除 + 清空 ref
3. **空会话路径显式解除**：`targetSessionId` 为空时 `ownSessionId = ""`，`loadingSessionIdRef` 未设置，`finally` 条件不满足 -> 必须在空会话分支显式 `SET_LOADING false`
4. **detail 后台失败不阻塞**：messages 已渲染，detail catch 只更新 `historyDetailState` 为 `recover_failed`，不影响已渲染消息

## file-tree 后台化与 ref 拆分纪律（2026-08-14 第三波）

**Files**: `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

### 核心模式：阻塞首屏的慢接口后台化

file-tree（生产实测 16.7s/2MB）从 `load()` 的 `await Promise.all` 中解耦：project 水合（内存对象，瞬间）后立即放行会话区渲染，file-tree 走后台链（`.then` 落地 + `.catch` 失败隔离）。会话区与文件树无渲染依赖，任何此类无依赖慢接口都应后台化而非 await。

### 水合 ref 拆分

单一 `hasWorkspaceHydratedRef` 拆为两个独立 ref：

| ref | 语义 | 置 true 时机 |
|-----|------|-------------|
| `workspaceHydratedRef` | 会话区数据就绪（不等树） | project SET_PROJECT 后 |
| `fileTreeReadyRef` | 树已落地（首次或缓存） | 后台链 .then commit 后 |

所有原 `hasWorkspaceHydratedRef` 读取点按语义迁移：预取 effect 守卫 → workspaceHydratedRef；预取 onRevalidated 守卫 → fileTreeReadyRef；企业切换 effect 守卫 → fileTreeReadyRef。

### 企业切换补跑模式（空树窗口）

```typescript
// 守卫前注册 ref——注册在守卫后则补跑时 ref 恒为 null（CR 实测 bug）
reloadWorkspaceForEnterpriseRef.current = () => { void reloadWorkspaceForEnterprise(); };

if (!fileTreeReadyRef.current) {
  pendingEnterpriseReloadRef.current = true;  // 树未就绪：记录待补跑
  return;
}
void reloadWorkspaceForEnterprise();
```

树落地处（commitFileTreeToWorkspace）消费标记并补跑。**两条硬纪律**：
1. 补跑依赖的 ref 必须注册在守卫之前（守卫提前 return 后 ref 永不赋值，补跑静默空操作——三审查轴独立发现的 CRITICAL）
2. 补跑标记在消费时立即置 false（防泄漏到下一次切换）

### 空树守卫（子树刷新覆盖竞态）

`reloadFileTree` 是唯一漏斗，统一用 `resolveFileTreeRefreshScope`（`lib/file-tree-refresh-guard.ts`）：空树 + subtree/source scope → 退回 `{ mode: "full", fresh: true }`。否则上传成功触发的 subtree 刷新对空树静默返回 `[]` 并 `SET_FILE_TREE([])` 清空整树，且与飞行中的初始树落地竞态覆盖。

### 后台链落地：mountedRef vs effect 局部 alive（二轮 CR 死锁教训）

file-tree 后台链的 `.then` 落地属于**进度推进**，必须用挂载级 `mountedRef` 拦截（跨 effect 实例共享），**禁止**用 effect 局部 `alive`——首次树加载窗口切企业时：旧 load 的 alive 被 cleanup 置 false → 落地被丢弃；新 load 因 `workspaceHydratedRef` 已 true 不再启动后台链 → `fileTreeReadyRef` 恒 false → 企业切换永远走 pending → 骨架卡死。补跑机制保证最终一致性（落地旧树 → pending 补跑 REPLACE 新企业树），数据正确性不依赖 alive。

区分两类拦截：
| 场景 | 用哪个 |
|------|--------|
| 数据归属正确性（预取结果切企业后必须丢弃，如 preloadedDetailPromise/onRevalidated） | effect 局部 alive |
| 进度推进（树落地、状态机推进，丢弃会死锁） | 挂载级 mountedRef |

effect 提前 return 分支也要返回 cleanup（`return () => { alive = false; }`），否则在途请求落地竞态覆盖新实例数据。

### mountedRef 初始化：StrictMode 双挂载竞态（2026-08-15 反复修教训）

**问题**：`const mountedRef = React.useRef(true); useEffect(() => () => { mountedRef.current = false; }, [])`——effect 只在 cleanup 置 false，**重挂载时 ref 不恢复 true**。React 18 StrictMode（dev 默认）双挂载流程：mount → effect 运行 → 模拟卸载 cleanup（`mountedRef=false`）→ 重挂载 effect 重跑（**ref 保留，仍 false**）→ 后台链 `.then(commit)` 被 `if (!mountedRef.current) return` 拦截 → file-tree 永不落地。

**概率性特征**（为什么难复现）：有 session 缓存时 `loadFileTreeWithSessionCache` 同步 resolve 缓存树，commit 可能在第一次 effect 窗口内完成（正常）；无缓存走网络时 commit 必然在 cleanup 之后（被拦截）。**取决于缓存/网络时序 → 偶发**。连带影响：`state.fileTree` 未更新 → AI 产物（resolveSessionLinkedFiles 依赖完整树）不召回。

**修复（每次 effect 运行恢复 true）**：
```typescript
// Correct: effect 每次运行开头恢复 true（StrictMode 重挂载安全）
const mountedRef = React.useRef(true);
React.useEffect(() => {
  mountedRef.current = true;
  return () => { mountedRef.current = false; };
}, []);

// Wrong: 只在 cleanup 置 false（StrictMode 下恒 false，概率性拦截落地）
const mountedRef = React.useRef(true);
React.useEffect(() => () => { mountedRef.current = false; }, []);
```

**通用纪律**：任何「挂载级标记」ref（mountedRef 等）的 effect 必须**每次运行开头恢复初始值**，不能只写 cleanup——StrictMode 双挂载会先 cleanup 再重跑 effect，只写 cleanup 的 ref 在重跑后保持 false。

### 失败隔离（局部错误态）

后台链失败只 set `fileTreeError`（局部 state），**不 dispatch `SET_ERROR`**（那是整页错误）；portal 渲染门按 `fileTreeError` 显示错误态+重试按钮。渲染门读 ref 安全：ref 变化恒伴随 dispatch/setState 触发重渲染。

**演进（2026-08-15）**：失败态不再显示错误 UI（用户感知失败）——改为**保持真实 UI + 透明遮罩层**（`absolute inset-0 z-10`），用户看不出失败；点击遮罩触发 `reloadFileTree({ mode: "full", fresh: true })` 重试，成功则遮罩消失，失败则 toast 提示。**交互反馈模式**：加载/失败期用透明遮罩拦截点击给 toast（友好提示），而非错误态 UI。

### 透明遮罩交互拦截模式（2026-08-15）

**问题**：加载期/失败期需要「视觉保持真实 UI + 交互禁用 + 点击给反馈」，但 `pointer-events:none`/`inert` 会**吞掉点击事件**（无法触发 toast）。

**方案**：透明遮罩层覆盖在真实 UI 上：
```tsx
<div className="relative h-full">
  <div className="absolute inset-0 z-10 cursor-not-allowed"
    onClick={async (e) => {
      e.stopPropagation(); e.preventDefault();
      try {
        const tree = await reloadFileTree({ mode: "full", fresh: true });
        if (tree) fileTreeReadyRef.current = true;  // 成功 → 遮罩消失（伴随 setState 重渲染）
      } catch { toast.info(ws.toast("treeLoading")); }  // 失败 → toast
    }} />
  {workspacePanel(EMPTY_FILE_TREE_PLACEHOLDER)}
</div>
```

**要点**：
1. 遮罩 `absolute inset-0 z-10` 覆盖真实组件，点击被遮罩捕获（真实按钮不响应）
2. 点击触发**重试**（而非纯 toast）——后端恢复后用户点一下就能恢复，不必刷新页面
3. 失败提示用 `toast.info`（轻提示），不打断用户
4. 成功路径必须伴随 setState（`reloadFileTree` 内部 dispatch SET_FILE_TREE）触发重渲染，遮罩随渲染门条件消失
5. 遮罩层不放 `pointer-events-none`/`inert`（会吞点击）；键盘可访问性由真实组件承担（加载期短暂可接受）

### 预览 blob 缓存与懒加载（2026-08-15，preview-cache.ts，2026-08-17 CR 修订跨租户隔离）

**问题**：刷新后 blob URL 失效 → 自动重新下载所有预览（数百张图并发请求风暴）；用户上传的图片一般不变，重复下载浪费。

**IndexedDB 永久缓存 + 内存降级层**（`apps/web/src/lib/preview-cache.ts`）：
- 主存储 IndexedDB（keyPath `cacheKey = ${enterpriseId}:${path}`），跨刷新复用 blob——用户上传图片不变，刷新零请求
- 内存 Map 降级层：IndexedDB 不可用（隐私模式/存储满/老 Safari）时会话级缓存
- 单文件 >10MB 跳过 IndexedDB（防占满配额）
- 全部操作 fail-safe：任何失败静默降级，不阻塞预览恢复
- **跨租户隔离**（2026-08-17 CR 修复）：缓存 key 必须带 `enterpriseId` 前缀——不同企业同名 path 不会串读

**懒加载 + 并发控制**（SuperLobsterPage 恢复逻辑）：
- 首次只恢复前 5 条消息预览（`LAZY_INITIAL_COUNT = 5`）
- IntersectionObserver 监听 `[data-message-id]` 元素，进入视口（rootMargin 100px）才恢复——数百张图只下载可见的
- 并发限制 `CONCURRENT_LIMIT = 3`（队列 + downloadNext 链式）

**要点**：
1. 恢复流程：`getCachedFileBlob(enterpriseId, path)` → 命中直接 `URL.createObjectURL`（零网络）；未命中下载 → `cacheFileBlob(enterpriseId, path, blob)` 写缓存
2. 懒加载需要消息元素带 `data-message-id` 属性（MessageList 渲染时加）
3. IntersectionObserver 在 effect cleanup 时 `disconnect()`（防泄漏）
4. 缓存 key 用 `${enterpriseId}:${path}`——**必须带企业维度**，否则跨企业同名文件串读

**IndexedDB 版本升级**：
- v1→v2（2026-08-17）：keyPath 从 `path` 改为 `cacheKey`，`onupgradeneeded` 删旧 store 重建
- **onblocked 处理**（2026-08-17 CR）：若另一标签页持有 v1 连接，`indexedDB.open` 被阻塞——`onblocked` 回调降级内存层 + `dbPromise=null` 允许重试，否则永久 pending
- `store.put` + `store.get` 对称：两者都接 `request.onerror = () => resolve()`，不能只接 `tx.onerror`

**登出清缓存**（2026-08-17 CR 接线）：
```typescript
// apps/web/src/lib/user.ts → clearCurrentUser
window.localStorage.removeItem(STORAGE_KEY);
void clearPreviewCache(); // 用户身份消失，隐私数据不留存
emitSessionEvent(eventType, reason);
```

**Wrong vs Correct**:
```typescript
// Wrong: 缓存 key 仅 path，跨企业同名文件串读
await cacheFileBlob(path, blob);
await getCachedFileBlob(path);

// Wrong: store.put 只接 tx.onerror，DataCloneError 时可能挂起
store.put(entry);
tx.onerror = () => resolve();

// Correct: 带企业维度 + put 接 request.onerror
await cacheFileBlob(enterpriseId, path, blob);
await getCachedFileBlob(enterpriseId, path);

// In cacheFileBlob:
const request = store.put(entry);
request.onerror = () => resolve(); // 与 store.get 对称
tx.oncomplete = () => resolve();
```

### Tests

- `file-tree-refresh-guard.test.ts`（6 用例：空树/非空树 × 单 scope/数组 scope）
- `detail-status-resolve.test.ts`（5 用例：显式 status / messageCount 推断 / 负数防御）
- `session-messages-retry.test.ts`（8 用例：成功不重试 / 重试 / 耗尽抛错 / maxRetries=0 / fake timers 延迟 / 4xx 快抛 / 429 重试 / statusCode 形态）

### 跨企业持久化状态隔离（2026-08-15 bugfix，2026-08-17 CR 修订）

**Files**: `apps/web/src/components/zclaw/ZclawChatProvider.tsx` + `apps/web/src/lib/conversationDraftStorage.ts`

**问题**：`super-lobster:generating-sessions:v1`（sessionStorage）单一 key 无企业维度——切换企业后旧企业生成中会话显示在新企业列表（带「正在生成中」徽标）。

**规则**：任何跨企业保留的前端持久化状态（sessionStorage/localStorage）必须带 enterpriseId 维度，且满足三条：

1. **读取按企业过滤**：加载时按企业过滤，谓词统一用 `isSessionVisibleForEnterprise(session, getActiveEnterpriseId())`（conversationDraftStorage.ts 导出）——无企业标记（legacy 旧数据）**视为当前企业可见**，只有明确属于其他企业的才跳过。⚠️ 不要用 `s.enterpriseId === current` 严格相等：旧数据 `undefined !== "entX"` 恒 true → 在途生成中会话对所有企业永久不可见不可清理（2026-08-17 CR 发现的回归）。legacy 会话恢复后随 persist 归入当前企业，可完成/清理。
2. **写入合并不覆盖**：persist 时先读 storage 保留其他企业会话，再合并当前企业更新——整体覆盖写会丢失其他企业会话（切回时无法恢复）。legacy（无 enterpriseId）归当前企业随 payload 覆盖/清理，不永久残留。
3. **切换时重载**：企业切换事件里从 storage 重载新企业会话（非只剪内存 Map）——只剪内存会导致切回时无法恢复。

**附加**：打标（upsert）用 `getActiveEnterpriseId()`（同步读 localStorage）而非 state——state 异步更新有 stale 窗口（切换事件同 tick 内会用旧企业打标）。

```typescript
// Correct: persist 合并（保留其他企业；legacy 归当前企业）
const otherEnterpriseSessions = loadGeneratingSessions()
  .filter((s) => !isSessionVisibleForEnterprise(s, currentEnterpriseId));
saveGeneratingSessions([...otherEnterpriseSessions, ...currentPayload]);

// Wrong 1: 整体覆盖（切企业后 persist 丢失其他企业会话）
saveGeneratingSessions(currentPayload);

// Wrong 2: 严格相等过滤（legacy undefined 会话被永久跳过，不可见不可清理）
const visible = sessions.filter((s) => s.enterpriseId === currentEnterpriseId);
```
