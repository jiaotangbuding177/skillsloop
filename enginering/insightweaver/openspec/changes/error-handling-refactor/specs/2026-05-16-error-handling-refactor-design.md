# Error Handling System Refactor — Design

## Architecture

Event bus pattern: api-client emits errors to a global CustomEvent bus, consumed by a single ErrorHandlerProvider component.

```
                 HTTP Request
                     ↓
 api-client.ts (parseResponse) → dispatch ErrorEvent
                     ↓
 ErrorEventBus (CustomEvent on window.EventTarget)
                     ↓
 ErrorHandlerProvider (check Override → severity → dedup → display)
                  ↙        ↓         ↘
           Console.log   Toast       Dialog
              (L0)      (L1/L2)     (L3)
```

- `api-client.ts:parseResponse()` dispatches error event before throwing `ApiError`
- `ErrorHandlerProvider` (mounted in `layout.tsx`) listens, classifies, deduplicates, displays
- Non-HTTP errors (component try/catch) reach the bus via `emitError(error, { path })`
- Existing `toast.error()` calls continue working — old and new systems coexist during migration

## Severity Levels

| Level | Name | Trigger | Display |
|-------|------|---------|---------|
| L0 | SILENT | NetworkError/TypeError/AbortError/TimeoutError, code 5000, repeated errors in window | `console.warn()` only |
| L1 | LIGHT | code 1001/1002/2003/2004/4002/5001, HTTP 4xx (non-401) | Bottom-right toast, 1.5s, 13px, grey tones |
| L2 | NORMAL | code 3001/3002/4003 | Bottom-right toast, 3s, 13px, warm warning |
| L3 | CRITICAL | code 4001, 2001/2002 | Modal dialog (credits) or silent redirect |

## Default Severity Map

```ts
const DEFAULT_SEVERITY: Record<number, ErrorSeverity> = {
  5000: L0, // INTERNAL_ERROR
  5001: L1, // DEPENDENCY_UNAVAILABLE
  1001: L1, // INVALID_ARGUMENT
  1002: L1, // VALIDATION_FAILED
  2003: L1, // SMS_CODE_INVALID
  2004: L1, // SMS_RATE_LIMITED
  4002: L1, // IDEMPOTENCY_CONFLICT
  3001: L2, // FORBIDDEN
  3002: L2, // ACCOUNT_DISABLED
  4003: L2, // WORKSPACE_QUOTA_EXCEEDED
  2001: L3, // UNAUTHORIZED
  2002: L3, // TOKEN_EXPIRED
  4001: L3, // INSUFFICIENT_CREDITS
};
```

## Override List

Per-endpoint severity override, checked before the default map:

```ts
const OVERRIDE_LIST: Record<string, ErrorSeverity> = {};
// Example:
//   '/api/zclaw/stream-message': L0,
//   '/api/files/upload': L2,
```

Empty by default. Configurable at runtime.

## Severity Resolution Flow

```
error.constructor === NetworkError/TypeError/AbortError/TimeoutError? → L0
  ↓
OVERRIDE_LIST[requestPath]? → use override severity
  ↓
DEFAULT_SEVERITY[error.code]? → use mapped severity
  ↓
fallback → L1 (for unknown errors)
```

## Global Dedup (Throttle)

- **Window:** 30 seconds
- **Scope:** All errors system-wide
- **Rule:** Only the first error (by resolved severity) displays; subsequent errors in window → L0 (console only)
- **Exception:** L3 errors always display (credits/auth must not be suppressed)
- **Reset:** Window expiry resets the counter

## Toast Styling

- Position: `bottom-right`
- L1: grey bg `#f5f5f5`, grey text `#666`, no icon, 1.5s, 13px
- L2: warm bg `#fef3e2`, orange text `#c26d0d`, small warning icon, 3s, 13px
- `richColors` disabled; custom muted palette
- Border-radius 8px, subtle shadow

## User-Friendly Messages

Backend English/technical messages mapped to Chinese:

| Source | Mapped |
|--------|--------|
| `network error` / TypeError | "网络连接异常" |
| `Failed to fetch` | "网络请求失败，请检查连接" |
| Code 5000 | "服务暂时不可用，请稍后重试" |
| Code 5001 | "服务暂时不可用，请稍后重试" |
| Code 1001/1002 | Pass-through (backend already Chinese) |
| Code 4003 | "工作区容量已达上限" |
| Code 3001 | "权限不足" |
| Other custom messages | Pass-through |

## Files to Create/Modify

### New
- `apps/web/src/lib/error-handler.ts` — core: event bus, classify, dedup, display
- `apps/web/src/lib/error-codes.ts` — severity map, message map, override list
- `apps/web/src/components/ui/ErrorHandlerProvider.tsx` — listener component

### Modified
- `apps/web/src/components/ui/ToastProvider.tsx` — position, style
- `apps/web/lib/api-client.ts` — dispatch error event in parseResponse()
- `apps/web/src/app/layout.tsx` — mount ErrorHandlerProvider
- Incremental: replace `toast.error()` in component files

## No Changes
- Backend API (no changes needed)
- SSE streaming error path
- Credits dialog (existing L3 pattern reused)
- Session refresh/redirect (existing logic kept)
