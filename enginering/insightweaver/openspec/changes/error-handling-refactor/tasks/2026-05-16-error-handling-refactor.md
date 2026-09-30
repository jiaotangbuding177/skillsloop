# Error Handling System Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified error handling system with 4-tier severity, global dedup, backend error code → user-friendly Chinese message mapping, and a per-endpoint override list.

**Architecture:** Event bus pattern. `api-client.ts` dispatches `ErrorEvent` on a global `CustomEvent` target; `ErrorHandlerProvider` listens, classifies severity (checking override list first, then default code map), applies global 30s dedup, and routes errors to console (L0), bottom-right toast (L1/L2), or dialog (L3).

**Tech Stack:** TypeScript, React 19, sonner v2, vitest, jsdom

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `apps/web/src/lib/error-codes.ts` | CREATE | Error code enum, severity map, message map, override list, classify functions |
| `apps/web/src/lib/error-handler.ts` | CREATE | Event bus, emitError, DedupManager, handleError, showToast |
| `apps/web/src/components/ui/ErrorHandlerProvider.tsx` | CREATE | React listener component subscribing to error events |
| `apps/web/src/components/ui/ToastProvider.tsx` | MODIFY | Change position to bottom-right, custom muted styles |
| `apps/web/lib/api-client.ts` | MODIFY | Dispatch error event in parseResponse() and fetchRaw() |
| `apps/web/src/app/layout.tsx` | MODIFY | Mount ErrorHandlerProvider |

---

### Task 1: Error Codes & Severity Constants

**Files:**
- Create: `apps/web/src/lib/error-codes.ts`
- Create: `apps/web/src/lib/__tests__/error-codes.test.ts`

- [ ] **Step 1: Write the test file**

```ts
// apps/web/src/lib/__tests__/error-codes.test.ts
import { describe, it, expect } from 'vitest';
import {
  ErrorCode,
  ErrorSeverity,
  DEFAULT_SEVERITY_MAP,
  USER_FRIENDLY_MESSAGES,
  OVERRIDE_LIST,
  toUserFriendlyMessage,
  getErrorSeverity,
} from '../error-codes';

describe('ErrorCode', () => {
  it('has expected error codes', () => {
    expect(ErrorCode.SUCCESS).toBe(0);
    expect(ErrorCode.INVALID_ARGUMENT).toBe(1001);
    expect(ErrorCode.UNAUTHORIZED).toBe(2001);
    expect(ErrorCode.INSUFFICIENT_CREDITS).toBe(4001);
    expect(ErrorCode.INTERNAL_ERROR).toBe(5000);
  });
});

describe('DEFAULT_SEVERITY_MAP', () => {
  it('maps INTERNAL_ERROR to L0', () => {
    expect(DEFAULT_SEVERITY_MAP[ErrorCode.INTERNAL_ERROR]).toBe(ErrorSeverity.SILENT);
  });

  it('maps INVALID_ARGUMENT to L1', () => {
    expect(DEFAULT_SEVERITY_MAP[ErrorCode.INVALID_ARGUMENT]).toBe(ErrorSeverity.LIGHT);
  });

  it('maps WORKSPACE_QUOTA_EXCEEDED to L2', () => {
    expect(DEFAULT_SEVERITY_MAP[ErrorCode.WORKSPACE_QUOTA_EXCEEDED]).toBe(ErrorSeverity.NORMAL);
  });

  it('maps INSUFFICIENT_CREDITS to L3', () => {
    expect(DEFAULT_SEVERITY_MAP[ErrorCode.INSUFFICIENT_CREDITS]).toBe(ErrorSeverity.CRITICAL);
  });
});

describe('USER_FRIENDLY_MESSAGES', () => {
  it('maps INTERNAL_ERROR to Chinese', () => {
    expect(USER_FRIENDLY_MESSAGES[ErrorCode.INTERNAL_ERROR]).toBe('服务暂时不可用，请稍后重试');
  });

  it('maps WORKSPACE_QUOTA_EXCEEDED to Chinese', () => {
    expect(USER_FRIENDLY_MESSAGES[ErrorCode.WORKSPACE_QUOTA_EXCEEDED]).toBe('工作区容量已达上限');
  });
});

describe('toUserFriendlyMessage', () => {
  it('returns mapped message for error code 5000', () => {
    const err = { code: 5000, message: 'Internal Server Error', status: 500 };
    expect(toUserFriendlyMessage(err as any)).toBe('服务暂时不可用，请稍后重试');
  });

  it('returns mapped message for error code 3001', () => {
    const err = { code: 3001, message: 'Forbidden', status: 403 };
    expect(toUserFriendlyMessage(err as any)).toBe('权限不足');
  });

  it('falls back to original message if no mapping', () => {
    const err = { code: 9999, message: '文件已存在', status: 400 };
    expect(toUserFriendlyMessage(err as any)).toBe('文件已存在');
  });

  it('detects network errors from message', () => {
    const err = { message: 'network error' };
    expect(toUserFriendlyMessage(err as any)).toBe('网络连接异常');
  });

  it('detects Failed to fetch', () => {
    const err = { message: 'Failed to fetch' };
    expect(toUserFriendlyMessage(err as any)).toBe('网络请求失败，请检查连接');
  });

  it('handles missing message gracefully', () => {
    expect(toUserFriendlyMessage({} as any)).toBe('未知错误');
  });
});

describe('getErrorSeverity', () => {
  it('uses override list when path matches', () => {
    OVERRIDE_LIST['/api/test'] = ErrorSeverity.LIGHT;
    const err = { code: ErrorCode.INTERNAL_ERROR, status: 500 };
    expect(getErrorSeverity(err as any, '/api/test')).toBe(ErrorSeverity.LIGHT);
    delete OVERRIDE_LIST['/api/test'];
  });

  it('falls back to default code map when no override', () => {
    const err = { code: ErrorCode.INSUFFICIENT_CREDITS, status: 403 };
    expect(getErrorSeverity(err as any, '/api/billing')).toBe(ErrorSeverity.CRITICAL);
  });

  it('returns L0 for network errors regardless of path', () => {
    const err = { message: 'network error' };
    expect(getErrorSeverity(err as any, '/api/any')).toBe(ErrorSeverity.SILENT);
  });

  it('returns L1 for unknown errors', () => {
    const err = { code: 9999, status: 418 };
    expect(getErrorSeverity(err as any, '/api/unknown')).toBe(ErrorSeverity.LIGHT);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pnpm --filter @insightweaver/web test -- --run src/lib/__tests__/error-codes.test.ts
```
Expected: FAIL — module not found

- [ ] **Step 3: Write error-codes.ts**

```ts
// apps/web/src/lib/error-codes.ts

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
  INTERNAL_ERROR = 5000,
  DEPENDENCY_UNAVAILABLE = 5001,
}

export enum ErrorSeverity {
  SILENT = 0,
  LIGHT = 1,
  NORMAL = 2,
  CRITICAL = 3,
}

export const DEFAULT_SEVERITY_MAP: Record<number, ErrorSeverity> = {
  [ErrorCode.INTERNAL_ERROR]: ErrorSeverity.SILENT,
  [ErrorCode.DEPENDENCY_UNAVAILABLE]: ErrorSeverity.LIGHT,
  [ErrorCode.INVALID_ARGUMENT]: ErrorSeverity.LIGHT,
  [ErrorCode.VALIDATION_FAILED]: ErrorSeverity.LIGHT,
  [ErrorCode.SMS_CODE_INVALID]: ErrorSeverity.LIGHT,
  [ErrorCode.SMS_RATE_LIMITED]: ErrorSeverity.LIGHT,
  [ErrorCode.IDEMPOTENCY_CONFLICT]: ErrorSeverity.LIGHT,
  [ErrorCode.FORBIDDEN]: ErrorSeverity.NORMAL,
  [ErrorCode.ACCOUNT_DISABLED]: ErrorSeverity.NORMAL,
  [ErrorCode.WORKSPACE_QUOTA_EXCEEDED]: ErrorSeverity.NORMAL,
  [ErrorCode.UNAUTHORIZED]: ErrorSeverity.CRITICAL,
  [ErrorCode.TOKEN_EXPIRED]: ErrorSeverity.CRITICAL,
  [ErrorCode.INSUFFICIENT_CREDITS]: ErrorSeverity.CRITICAL,
};

export const OVERRIDE_LIST: Record<string, ErrorSeverity> = {};

export const USER_FRIENDLY_MESSAGES: Record<number, string> = {
  [ErrorCode.INTERNAL_ERROR]: '服务暂时不可用，请稍后重试',
  [ErrorCode.DEPENDENCY_UNAVAILABLE]: '服务暂时不可用，请稍后重试',
  [ErrorCode.WORKSPACE_QUOTA_EXCEEDED]: '工作区容量已达上限',
  [ErrorCode.FORBIDDEN]: '权限不足',
  [ErrorCode.ACCOUNT_DISABLED]: '账号已被禁用，请联系管理员',
  [ErrorCode.INSUFFICIENT_CREDITS]: '额度不足，请充值后重试',
};

const NETWORK_ERROR_PATTERNS: RegExp[] = [
  /network error/i,
  /Failed to fetch/i,
  /fetch failed/i,
  /NetworkError/i,
  /ERR_NETWORK/i,
  /TypeError/i,
  /AbortError/i,
];

export function isNetworkError(error: unknown): boolean {
  const message = extractErrorMessage(error);
  if (!message) return false;
  return NETWORK_ERROR_PATTERNS.some((p) => p.test(message));
}

function extractErrorMessage(error: unknown): string {
  if (!error) return '';
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  if (typeof (error as any).message === 'string') return (error as any).message;
  return '';
}

export function toUserFriendlyMessage(error: unknown): string {
  const code = (error as any)?.code;
  const rawMessage = extractErrorMessage(error);

  if (typeof code === 'number' && USER_FRIENDLY_MESSAGES[code]) {
    return USER_FRIENDLY_MESSAGES[code];
  }

  if (isNetworkError(error)) {
    if (/Failed to fetch/i.test(rawMessage) || /fetch failed/i.test(rawMessage)) {
      return '网络请求失败，请检查连接';
    }
    return '网络连接异常';
  }

  if (rawMessage) return rawMessage;

  return '未知错误';
}

export interface ErrorLike {
  code?: number;
  message?: string;
  status?: number;
  name?: string;
  constructor?: { name?: string };
}

export function getErrorSeverity(error: ErrorLike, requestPath?: string): ErrorSeverity {
  if (isNetworkError(error)) {
    return ErrorSeverity.SILENT;
  }

  const errorName = error?.name || error?.constructor?.name || '';
  if (errorName === 'TimeoutError' || errorName === 'AbortError' || errorName === 'TypeError') {
    return ErrorSeverity.SILENT;
  }

  if (requestPath && OVERRIDE_LIST[requestPath] !== undefined) {
    return OVERRIDE_LIST[requestPath];
  }

  if (error?.code !== undefined && DEFAULT_SEVERITY_MAP[error.code] !== undefined) {
    return DEFAULT_SEVERITY_MAP[error.code];
  }

  return ErrorSeverity.LIGHT;
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pnpm --filter @insightweaver/web test -- --run src/lib/__tests__/error-codes.test.ts
```
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/error-codes.ts apps/web/src/lib/__tests__/error-codes.test.ts
git commit -m "web: add error codes, severity map, and user-friendly messages"
```

---

### Task 2: Error Handler Core (Event Bus + Dedup + Display)

**Files:**
- Create: `apps/web/src/lib/error-handler.ts`
- Create: `apps/web/src/lib/__tests__/error-handler.test.ts`

- [ ] **Step 1: Write the test file**

```ts
// apps/web/src/lib/__tests__/error-handler.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  emitError,
  onError,
  DedupManager,
  handleError,
  ErrorEventDetail,
} from '../error-handler';
import { ErrorSeverity } from '../error-codes';

describe('DedupManager', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('allows first error through', () => {
    const dm = new DedupManager(30000);
    expect(dm.shouldShow(ErrorSeverity.LIGHT)).toBe(true);
  });

  it('blocks second error within window', () => {
    const dm = new DedupManager(30000);
    dm.shouldShow(ErrorSeverity.LIGHT);
    expect(dm.shouldShow(ErrorSeverity.LIGHT)).toBe(false);
  });

  it('allows error after window expires', () => {
    const dm = new DedupManager(30000);
    dm.shouldShow(ErrorSeverity.LIGHT);
    vi.advanceTimersByTime(31000);
    expect(dm.shouldShow(ErrorSeverity.LIGHT)).toBe(true);
  });

  it('always allows CRITICAL errors', () => {
    const dm = new DedupManager(30000);
    dm.shouldShow(ErrorSeverity.LIGHT);
    expect(dm.shouldShow(ErrorSeverity.CRITICAL)).toBe(true);
  });

  it('CRITICAL does not block subsequent errors after window', () => {
    const dm = new DedupManager(30000);
    dm.shouldShow(ErrorSeverity.CRITICAL);
    vi.advanceTimersByTime(31000);
    expect(dm.shouldShow(ErrorSeverity.LIGHT)).toBe(true);
  });

  it('L0 SILENT does not consume the window slot', () => {
    const dm = new DedupManager(30000);
    dm.shouldShow(ErrorSeverity.SILENT);
    expect(dm.shouldShow(ErrorSeverity.LIGHT)).toBe(true);
  });
});

describe('emitError / onError', () => {
  it('dispatches and receives error events', () => {
    const listener = vi.fn();
    const unsubscribe = onError(listener);

    const error = new Error('test error');
    emitError(error, { path: '/api/test' });

    expect(listener).toHaveBeenCalledTimes(1);
    const detail: ErrorEventDetail = listener.mock.calls[0][0];
    expect(detail.error).toBe(error);
    expect(detail.path).toBe('/api/test');

    unsubscribe();
    emitError(error, { path: '/api/test2' });
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it('handles non-Error objects', () => {
    const listener = vi.fn();
    const unsubscribe = onError(listener);

    emitError({ code: 5000, message: 'oops' }, { path: '/api/boom' });

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener.mock.calls[0][0].error).toEqual({ code: 5000, message: 'oops' });

    unsubscribe();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pnpm --filter @insightweaver/web test -- --run src/lib/__tests__/error-handler.test.ts
```
Expected: FAIL — module not found

- [ ] **Step 3: Write error-handler.ts**

```ts
// apps/web/src/lib/error-handler.ts
import { toast } from 'sonner';
import {
  ErrorSeverity,
  ErrorLike,
  getErrorSeverity,
  toUserFriendlyMessage,
} from './error-codes';

export interface ErrorEventDetail {
  error: ErrorLike;
  path?: string;
  severity: ErrorSeverity;
  message: string;
}

const ERROR_EVENT = 'insightweaver:api-error';

function getEventTarget(): EventTarget | null {
  if (typeof window === 'undefined') return null;
  const key = '__insightweaverErrorEventTarget';
  const existing = (window as any)[key];
  if (existing) return existing;
  const target = new EventTarget();
  (window as any)[key] = target;
  return target;
}

export function emitError(
  error: unknown,
  context?: { path?: string },
): void {
  const target = getEventTarget();
  if (!target) return;

  const errorLike: ErrorLike = error instanceof Error
    ? { code: (error as any).code, message: error.message, name: error.name }
    : (error as ErrorLike);

  const severity = getErrorSeverity(errorLike, context?.path);
  const message = toUserFriendlyMessage(errorLike);

  target.dispatchEvent(
    new CustomEvent<ErrorEventDetail>(ERROR_EVENT, {
      detail: { error: errorLike, path: context?.path, severity, message },
    }),
  );
}

export function onError(
  listener: (detail: ErrorEventDetail) => void,
): () => void {
  const target = getEventTarget();
  if (!target) return () => {};

  const handler = (event: Event) => {
    listener((event as CustomEvent<ErrorEventDetail>).detail);
  };

  target.addEventListener(ERROR_EVENT, handler);
  return () => {
    target.removeEventListener(ERROR_EVENT, handler);
  };
}

export class DedupManager {
  private lastShowTime = 0;
  private windowMs: number;

  constructor(windowMs: number = 30000) {
    this.windowMs = windowMs;
  }

  shouldShow(severity: ErrorSeverity): boolean {
    if (severity === ErrorSeverity.SILENT) return false;

    if (severity === ErrorSeverity.CRITICAL) return true;

    const now = Date.now();
    if (now - this.lastShowTime < this.windowMs) return false;

    this.lastShowTime = now;
    return true;
  }

  reset(): void {
    this.lastShowTime = 0;
  }
}

const dedupManager = new DedupManager(30000);

export function handleError(detail: ErrorEventDetail): void {
  const { severity, message, path } = detail;

  if (severity === ErrorSeverity.SILENT) {
    console.warn(`[ErrorHandler] ${message}`, { path, ...detail.error });
    return;
  }

  if (severity === ErrorSeverity.CRITICAL) {
    dedupManager.shouldShow(severity);
    return;
  }

  if (!dedupManager.shouldShow(severity)) {
    console.warn(`[ErrorHandler][deduped] ${message}`, { path });
    return;
  }

  showToast(message, severity);
}

function showToast(message: string, severity: ErrorSeverity): void {
  if (severity === ErrorSeverity.LIGHT) {
    toast(message, {
      duration: 1500,
      style: {
        fontSize: '13px',
        background: '#f5f5f5',
        color: '#666',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      },
    });
  } else if (severity === ErrorSeverity.NORMAL) {
    toast(message, {
      duration: 3000,
      style: {
        fontSize: '13px',
        background: '#fef3e2',
        color: '#c26d0d',
        border: '1px solid #fde4c3',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      },
    });
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pnpm --filter @insightweaver/web test -- --run src/lib/__tests__/error-handler.test.ts
```
Expected: PASS — all tests pass

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/error-handler.ts apps/web/src/lib/__tests__/error-handler.test.ts
git commit -m "web: add error handler core with event bus, dedup, and display"
```

---

### Task 3: ErrorHandlerProvider Component

**Files:**
- Create: `apps/web/src/components/ui/ErrorHandlerProvider.tsx`

- [ ] **Step 1: Write the component**

```tsx
// apps/web/src/components/ui/ErrorHandlerProvider.tsx
'use client';

import { useEffect } from 'react';
import { onError, handleError } from '@/lib/error-handler';

export default function ErrorHandlerProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const unsubscribe = onError(handleError);
    return unsubscribe;
  }, []);

  return <>{children}</>;
}
```

- [ ] **Step 2: Mount in layout.tsx**

Edit `apps/web/src/app/layout.tsx`:

Add import after line 5:
```tsx
import ErrorHandlerProvider from "../components/ui/ErrorHandlerProvider";
```

Wrap children with ErrorHandlerProvider on line 109-111. Change from:
```tsx
        <ThemeProvider>
          <ToastProvider>
            {children}
            <InsufficientCreditsDialog />
          </ToastProvider>
        </ThemeProvider>
```
To:
```tsx
        <ThemeProvider>
          <ErrorHandlerProvider>
            <ToastProvider>
              {children}
              <InsufficientCreditsDialog />
            </ToastProvider>
          </ErrorHandlerProvider>
        </ThemeProvider>
```

- [ ] **Step 3: Verify build**

```bash
pnpm --filter @insightweaver/web build
```
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/ui/ErrorHandlerProvider.tsx apps/web/src/app/layout.tsx
git commit -m "web: add ErrorHandlerProvider and mount in layout"
```

---

### Task 4: Modify ToastProvider (Position & Style)

**Files:**
- Modify: `apps/web/src/components/ui/ToastProvider.tsx`

- [ ] **Step 1: Update ToastProvider**

Replace `apps/web/src/components/ui/ToastProvider.tsx`:

```tsx
'use client';

import React from 'react';
import { Toaster } from 'sonner';

interface Props {
  children: React.ReactNode;
}

const ToastProvider: React.FC<Props> = ({ children }) => {
  return (
    <>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 1500,
          style: {
            fontSize: '13px',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          },
        }}
      />
      {children}
    </>
  );
};

export default ToastProvider;
```

- [ ] **Step 2: Verify build**

```bash
pnpm --filter @insightweaver/web build
```
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/ui/ToastProvider.tsx
git commit -m "web: change toast position to bottom-right with muted styling"
```

---

### Task 5: Integrate Error Dispatch in api-client

**Files:**
- Modify: `apps/web/lib/api-client.ts`

- [ ] **Step 1: Add import for emitError**

Add to the imports in `api-client.ts` (after line 12):
```ts
import { emitError } from '@/lib/error-handler';
```

- [ ] **Step 2: Dispatch error event in parseResponse**

In `parseResponse()` (around line 176-181), after the `throw new ApiError(...)` but before it, add dispatch. Change this block:

```ts
    if (!response.ok || (json && json.code && json.code !== 0)) {
      const message = json?.message || `请求失败: ${response.status}`;
      if (json?.code === 4001 || json?.message === 'insufficient credits') {
        emitInsufficientCredits({ code: json?.code, message: json?.message });
      }
      throw new ApiError(message, response.status, json?.code, json?.data);
    }
```

To:

```ts
    if (!response.ok || (json && json.code && json.code !== 0)) {
      const message = json?.message || `请求失败: ${response.status}`;
      if (json?.code === 4001 || json?.message === 'insufficient credits') {
        emitInsufficientCredits({ code: json?.code, message: json?.message });
      }
      const apiError = new ApiError(message, response.status, json?.code, json?.data);
      emitError(apiError, { path: response.url });
      throw apiError;
    }
```

- [ ] **Step 3: Dispatch error event in fetchRaw error handling**

In `fetchRaw()` (around line 376-389), change the error block:

```ts
      let message = `请求失败: ${response.status}`;
      try {
        const text = await response.text();
        const parsed = text ? (JSON.parse(text) as ApiEnvelope<unknown>) : null;
        message = parsed?.message || message;
        if (parsed?.code === 4001 || parsed?.message === 'insufficient credits') {
          emitInsufficientCredits({ code: parsed?.code, message: parsed?.message });
        }
        throw new ApiError(message, response.status, parsed?.code, parsed?.data);
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        throw new ApiError(message, response.status);
      }
```

To:

```ts
      let message = `请求失败: ${response.status}`;
      try {
        const text = await response.text();
        const parsed = text ? (JSON.parse(text) as ApiEnvelope<unknown>) : null;
        message = parsed?.message || message;
        if (parsed?.code === 4001 || parsed?.message === 'insufficient credits') {
          emitInsufficientCredits({ code: parsed?.code, message: parsed?.message });
        }
        const apiError = new ApiError(message, response.status, parsed?.code, parsed?.data);
        emitError(apiError, { path: response.url });
        throw apiError;
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        const fallbackError = new ApiError(message, response.status);
        emitError(fallbackError, { path: response.url });
        throw fallbackError;
      }
```

- [ ] **Step 4: Dispatch error event for non-ApiError network errors in executeRequest catch**

In `executeRequest()` (around line 234-263), the `try/catch` block. After `if (err instanceof TimeoutError)` (line ~236), add emit for network-level errors. Before `throw err` on line 237, add:

```ts
      if (err instanceof TimeoutError) {
        emitError(err, { path });
        throw err;
      }
```

And for the final `throw err` on line 262, add emit for unknown errors that escaped the previous handlers. Before `throw err` on line 262, add:

```ts
      if (!(err instanceof ApiError)) {
        emitError(err, { path });
      }
      throw err;
```

- [ ] **Step 5: Verify build and run all tests**

```bash
pnpm --filter @insightweaver/web test -- --run && pnpm --filter @insightweaver/web build
```
Expected: all tests pass, build succeeds

- [ ] **Step 6: Commit**

```bash
git add apps/web/lib/api-client.ts
git commit -m "web: integrate error event dispatch into api-client"
```

---

### Task 6: Full Test Suite Verification

- [ ] **Step 1: Run all web tests**

```bash
pnpm --filter @insightweaver/web test -- --run
```
Expected: all tests pass

- [ ] **Step 2: Run full build**

```bash
pnpm build
```
Expected: build succeeds (all packages)

- [ ] **Step 3: Run lint**

```bash
pnpm lint
```
Expected: no new errors

---

### Task 7: Manual Verification Checkpoints

These are not code steps but behavior verification for the developer:

- [ ] **Checkpoint 1:** Navigate to the app → trigger a route that fails (e.g., disconnect network) → verify error appears in bottom-right (not top-center), with muted colors
- [ ] **Checkpoint 2:** Trigger multiple rapid errors → verify only first toast shows, others are deduped
- [ ] **Checkpoint 3:** Wait 30s and trigger an error again → verify toast shows again
- [ ] **Checkpoint 4:** Trigger credits error (code 4001) → verify existing credits dialog still works
- [ ] **Checkpoint 5:** Check browser console → verify network errors are logged as warnings, not shown as toasts
