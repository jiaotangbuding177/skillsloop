# Error Handling

## Architecture

Error handling flows through three layers:

```
API Response (non-2xx or code != 0)
  → ApiError thrown by parseResponse()
    → Error chain in api-client.ts (credits check, 401 retry, emitError)
      → emitError() dispatches 'insightweaver:api-error' CustomEvent
        → ErrorHandlerProvider subscribes and calls toast.error()
```

## Error Codes

**File:** `apps/web/src/lib/error-codes.ts`

```typescript
export enum ErrorCode {
  SUCCESS = 0,
  INVALID_ARGUMENT = 1001,
  VALIDATION_FAILED = 1002,
  UNAUTHORIZED = 2001,
  TOKEN_EXPIRED = 2002,
  SMS_CODE_INVALID = 2003,
  SMS_RATE_LIMITED = 2004,
  FORBIDDEN = 3001,
  ACCOUNT_DISABLED = 3002,
  INSUFFICIENT_CREDITS = 4001,
  IDEMPOTENCY_CONFLICT = 4002,
  WORKSPACE_QUOTA_EXCEEDED = 4003,
  BUSINESS_CONFLICT = 4004,
  INTERNAL_ERROR = 5000,
  DEPENDENCY_UNAVAILABLE = 5001,
}
```

## Four-Tier Severity System

**File:** `apps/web/src/lib/error-codes.ts`

```typescript
export enum ErrorSeverity {
  SILENT = 0,    // No user-visible feedback
  LIGHT = 1,     // Subtle feedback, short dedup window (10s)
  NORMAL = 2,    // Standard toast, medium dedup window (20s)
  CRITICAL = 3,  // Prominent feedback, short dedup window (5s)
}
```

### Default Severity Map

Each `ErrorCode` maps to a default severity:

| Severity | Error Codes |
|----------|------------|
| LIGHT | `INTERNAL_ERROR`, `DEPENDENCY_UNAVAILABLE`, `INVALID_ARGUMENT`, `VALIDATION_FAILED`, `SMS_CODE_INVALID`, `SMS_RATE_LIMITED`, `IDEMPOTENCY_CONFLICT`, `BUSINESS_CONFLICT` |
| NORMAL | `FORBIDDEN`, `ACCOUNT_DISABLED`, `WORKSPACE_QUOTA_EXCEEDED` |
| CRITICAL | `UNAUTHORIZED`, `TOKEN_EXPIRED`, `INSUFFICIENT_CREDITS` |

## Silent Rules

**File:** `apps/web/src/lib/error-codes.ts` (lines 53-66)

Silent rules suppress errors for background API calls that should not bother the user on specific pages. Each rule is a `{ path: RegExp, page: RegExp, severity }` tuple:

```typescript
export const SILENT_RULES: SilentRule[] = [
  { path: /\/api\/credits\/ledger/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/status/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/workspace\/usage/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/cron\//, page: /^.*/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/memory/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/assistant-personas/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/conversation-quota\/me/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/research\/featured-sessions/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/file-shares/, page: /^\/($|home|dl)/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/ragflow\//, page: /^.*/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/workspace\/(children|path|file-content|file-raw)/, page: /^.*/, severity: ErrorSeverity.SILENT },
  { path: /\/api\/zclaw\/shared-workspace\/(children|path|file-content|file-raw)/, page: /^.*/, severity: ErrorSeverity.SILENT },
];
```

Rules with `page: /^.*/` are always silent (e.g., cron tasks, ragflow, workspace file operations). Rules with `page: /^\/($|home|dl)/` are only silent on the home/dashboard pages where these calls are background polling.

Remote rules can be injected via `setRemoteSilentRules()` for dynamic suppression.

## Toast Deduplication

**File:** `apps/web/src/lib/error-handler.ts`

The `DedupManager` prevents toast spam using two mechanisms:

### Per-Severity Time Windows

```typescript
const DEDUP_WINDOW: Record<ErrorSeverity, number> = {
  [ErrorSeverity.SILENT]: 0,       // No dedup needed (silent)
  [ErrorSeverity.LIGHT]: 10_000,   // 10 seconds
  [ErrorSeverity.NORMAL]: 20_000,  // 20 seconds
  [ErrorSeverity.CRITICAL]: 5_000, // 5 seconds (shorter - user needs to see critical errors faster)
};
```

If an error of the same severity fires within the window, it is suppressed.

### Message-Level Dedup

Additionally, identical error messages are deduplicated within a 5-second window regardless of severity. This prevents the same error from multiple concurrent API calls from showing multiple toasts.

## Bilingual Error Translation

**File:** `apps/web/src/lib/error-codes.ts`

Backend error messages may arrive in English or Chinese. The system translates English messages to Chinese for `zh` locale users.

### Exact Match Translation

```typescript
export const BACKEND_EXACT_MESSAGES: Record<string, string> = {
  // Exact string matches for known backend messages
  // e.g., 'Resource not found' -> '资源不存在'
};
```

### Pattern-Based Translation

```typescript
export const BACKEND_PATTERN_RULES: Array<{
  pattern: RegExp;
  replacement: string;
}> = [
  // e.g., { pattern: /(.+?)\s+not\s+found$/i, replacement: '${subject} 不存在' }
];
```

Pattern rules use regex capture groups and named substitutions to translate dynamic messages.

### User-Friendly Fallbacks

```typescript
export const USER_FRIENDLY_MESSAGES: Record<number, string> = {
  [ErrorCode.INTERNAL_ERROR]: '服务器暂时不可用，请稍后重试',
  [ErrorCode.DEPENDENCY_UNAVAILABLE]: '依赖服务暂时不可用，请稍后重试',
  // ...
};
```

When no translation matches, the system falls back to these generic messages.

## Error Event System

**File:** `apps/web/src/lib/error-handler.ts`

### Event Target

A singleton `EventTarget` on `window.__insightweaverErrorEventTarget`:

```typescript
function getEventTarget(): EventTarget | null {
  if (typeof window === 'undefined') return null;
  const key = '__insightweaverErrorEventTarget';
  const existing = (window as any)[key];
  if (existing) return existing;
  const target = new EventTarget();
  (window as any)[key] = target;
  return target;
}
```

### Event Name

```typescript
const ERROR_EVENT = 'insightweaver:api-error';
```

### emitError Function

```typescript
export function emitError(
  error: unknown,
  context?: { path?: string; page?: string },
): void { ... }
```

The `emitError` function:
1. Converts the error to `ErrorLike` shape
2. Determines severity via `getErrorSeverity()` (checks silent rules, default map, overrides)
3. Extracts the message (prefers `ApiError.rawMessage`, falls back to Chinese text detection)
4. Translates via `toUserFriendlyMessage()`
5. Checks dedup (both severity-level and message-level)
6. Dispatches the custom event with `{ error, path, severity, message }`

### errorToast Helper

Pages use `errorToast(error)` as a shorthand in catch blocks. This calls `emitError()` internally.

## Chinese Text Detection

```typescript
function hasChinese(value: string): boolean {
  return /[\u3400-\u9fff]/.test(value);
}
```

Used to determine whether a backend message is already in Chinese (pass through) or needs translation.

## SSE 非 200 响应体解析（2026-09-05）

**问题**：`apps/web/lib/sse.ts` 的 `streamSse` 在 `!response.ok` 时把响应体原样塞进 Error——后端统一信封是 JSON（`{"code":1001,"message":"请求参数无效","data":null}`），界面直接显示整串 JSON，用户看不出原因（bugfix-20260905-chat-video-attachment）。

**规则**：SSE/流式端点的非 200 响应必须先解析信封提取 `message` 再展示，禁止整串响应体直出。统一走 `extractSseErrorMessage`（sse.ts）：

- 信封 `message` 为字符串 → 取之；为数组（ValidationPipe 多字段）→ 过滤字符串后 `join('; ')`
- 非 JSON（网关 HTML 错误页）→ 回退原文（与旧行为一致）
- 提取结果为空 → 回退 `SSE 请求失败: ${status}`（命中 SSE_FAIL_PATTERN → 「服务暂时不可用」）

所有 SSE 调用面（`useZclawChat`、`SuperLobsterPage` 等）都经 `streamSse`，修一处即全覆盖——新增流式请求禁止绕过 `streamSse` 手写 fetch 错误处理。

## SSE 空闲看门狗与 abort 身份（2026-09-08）

**问题**：`streamSse` 无任何超时——半开连接（浏览器后台冻结、网络切换、网关半开断连）下 `reader.read()` 永久挂起且不抛错，调用方「非 done 结束 → 拉服务器对账 + 清『生成中』标记」的收尾路径不可达，会话永远显示「正在执行」（bugfix-20260908-sse-idle-watchdog；与 !301 abort 孤儿执行同家族、方向相反）。

**规则**：

- `streamSse` 必须保持两级空闲看门狗，任何字节（含后端 25s 心跳注释行 `: heartbeat`）到达即重置：数据窗口 `SSE_IDLE_TIMEOUT_MS=90_000`（≈心跳 25s×3+余量，心跳与工具执行无关，不影响慢工具）；响应头/错误响应体窗口 `SSE_HEADER_TIMEOUT_MS=30_000`（覆盖两处 `runRequest()` 与非 200 `text()`，text 超时回退空文本按状态码报错）。
- 超时抛 `SseIdleTimeoutError`（专用 name）：**禁止重试**（`eventsReceived` 后重试会重复发送消息）、**禁止经 `toUserFriendlyMessage` 包装**（保留 name 供识别）、数据窗口超时须 `reader.cancel()` 释放连接。调用方无需特判——错误自然流入其既有「非 done 结束 → 静默对账」分支。
- 用户中止的 `AbortError`（DOMException 或 Error、name==='AbortError'）必须**保留原始身份原样抛出**，禁止包装为中文提示——否则调用方 `isAbort`/`isAbortError` 判据（SuperLobsterPage:694、useZclawChat:988）失配，中止被误标为失败。
- 新增流式请求禁止绕过 `streamSse` 手写 fetch/超时处理（重申上方契约）。

**测试**：`apps/web/src/lib/__tests__/sse-idle-watchdog.test.ts`（8 用例：数据窗口判死/心跳重置/正常流/abort 身份/响应头判死/非 200 回退/不命中 isAbort/事件后不重试）。

## 失败降级路径的日志级别（2026-08-15）

**问题**：AI 产物同步（`syncSessionArtifacts`）在 file-tree 请求失败时 `console.error` 输出完整堆栈——网络抖动/上游不稳定时产生大量错误噪音（每次 poll 重试都报）。

**规则**：
- **预期内的失败路径（有重试机制/不阻塞主流程）→ `console.warn`**（含 `[模块]` 前缀），禁止 `console.error`
- `console.error` 仅用于**意外异常**（不该发生却发生的错误）
- 判定标准：失败后是否有自动重试（签名 ref 未更新 → 下次 poll 重试）？是否阻塞用户主流程？两者皆否 → warn

```typescript
// Correct: 预期失败路径降级（有重试机制，不阻塞）
} catch (error) {
  console.warn("[super-lobster] sync session artifacts failed:", error);
}

// Wrong: 网络抖动时每次重试都产生 error 噪音
} catch (error) {
  console.error("Failed to sync session artifacts", error);
}
```
