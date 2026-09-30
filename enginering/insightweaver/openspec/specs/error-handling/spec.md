# Error Handling (Reusable Spec)

## Concept

Multi-tier error display system using an event bus pattern. API-client dispatches errors to a global event target; a single React provider listens, classifies severity, deduplicates across time windows, and routes to the appropriate display channel (console, toast, dialog).

## Architecture

```
API Client → ErrorEvent (CustomEvent) → ErrorHandlerProvider → Display
```

- `error-codes.ts`: Error code enum, severity map, user-friendly message map, override list, network/timeout/abort patterns
- `error-handler.ts`: Event bus (`emitError`/`onError`), `DedupManager` (30s window), `handleError`, `showToast` (5s message dedup)
- `ErrorHandlerProvider.tsx`: Listens to events and calls `handleError`

## Severity Levels

| Level | Name | Display | Use case |
|-------|------|---------|----------|
| 0 SILENT | console.warn | Network drops, timeouts, server 500, abort |
| 1 LIGHT | Bottom-right toast, 1.5s, grey | Validation, SMS limits, dependency errors |
| 2 NORMAL | Bottom-right toast, 3s, warm | Forbidden, quota exceeded |
| 3 CRITICAL | Dialog or redirect | Insufficient credits, auth expiry |

## User-Friendly Messages

### Error code mapping
| Code | Message |
|------|---------|
| 5000, 5001 | 服务暂时不可用，请稍后重试 |
| 4003 | 工作区容量已达上限 |
| 3001 | 权限不足 |
| 3002 | 账号已被禁用，请联系管理员 |
| 4001 | 额度不足，请充值后重试 |

### Pattern matching
| Pattern | Message |
|---------|---------|
| `Failed to fetch`, `fetch failed` | 网络请求失败，请检查连接 |
| `network error`, `NetworkError`, `ERR_NETWORK`, `ERR_INTERNET` | 网络连接异常 |
| `TimeoutError`, `timeout`, `timedout`, `ETIMEDOUT` | 请求超时，请稍后重试 |
| `AbortError`, `abort` | 请求已被中止 |
| `ECONNREFUSED`, `ENOTFOUND`, `ERR_CONNECTION` | 服务器连接失败，请稍后重试 |
| `SSE 请求失败` | 服务暂时不可用，请稍后重试 |

## Key Behaviors

1. **Override list** checked first, then default severity map, then fallback to L1
2. **Two-level dedup**: global 30s window per severity + per-message 5s dedup
3. **All errors** thrown from api-client carry user-friendly `.message` for component display
4. **SSE transport errors** also run through `toUserFriendlyMessage`
5. **Error messages** mapped to user-friendly Chinese via `toUserFriendlyMessage`

## Lessons

- R-26: `edit` tool requires enough surrounding context in `oldString` to uniquely identify the match location
- R-27: Error classification by name must consider source context (code, status), not just message patterns
- R-28: Dedup window's `lastShowTime` should always be updated regardless of severity level
- R-29: When replacing all thrown error messages to be user-friendly, BOTH `emitError` (for centralized display) AND the throw (for component display) must carry the friendly message
- R-30: SSE errors bypass api-client — they need their own `toUserFriendlyMessage` call in transport layer and component catch blocks
- R-31: useEffect circular dependencies cause repeated API calls — use ref-based guards instead of state-dependent computed values in dependency arrays (see `useeffect-circular-dependency/spec.md`)
