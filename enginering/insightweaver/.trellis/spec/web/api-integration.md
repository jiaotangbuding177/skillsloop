# API Integration

## Architecture Overview

The API layer has two tiers:
1. **Core client** at `apps/web/lib/api-client.ts` - wraps native `fetch` with timeout, envelope unwrapping, and error chain
2. **Module functions** at `apps/web/src/api/moudles/*.ts` - typed per-endpoint functions, barrel-exported from `apps/web/src/api/index.ts`

Pages import from `@/api`, which resolves to `src/api/index.ts`.

## API Client (`apps/web/lib/api-client.ts`)

### TimeoutController

Custom timeout implementation using `AbortController`:
- Each request gets a timeout (default 20 seconds)
- On timeout, the abort signal fires and the fetch promise rejects with `TimeoutError`
- No reliance on `AbortSignal.timeout()` (for broader compatibility)

### Request Flow

```
Page calls apiModule.listItems()
  → apiClient.get<T>('/api/zclaw/items')
    → apiClient.request<T>(path, config)
      → injects x-enterprise-id header (for /api/zclaw/* paths)
      → fetch(url, { ...config, signal: timeoutController.signal })
      → parseResponse<T>(response)
        → json = await response.json()
        → unwraps: json.data (the ApiEnvelope<T> envelope)
        → checks: json.code === 0 (success) or throws ApiError
      → error chain (see below)
```

### Response Envelope

All backend responses follow this shape:

```typescript
interface ApiEnvelope<T> {
  code: number;      // 0 = success, non-zero = error
  message: string;   // Human-readable message (may be Chinese or English)
  data: T;           // Actual payload
}
```

The client unwraps `data` automatically. Pages receive `T` directly, never the envelope.

### ApiError Class

Defined in `apps/web/lib/api-types.ts`:

```typescript
class ApiError extends Error {
  status: number;      // HTTP status code
  code: number;        // Business error code from envelope
  data: unknown;       // Response data (if any)
  rawMessage: string;  // Original message from backend before translation
}
```

## Error Handling Chain

After `parseResponse` throws an `ApiError`, the following chain executes in order:

### 1. Insufficient Credits (code === 4001)

```typescript
if (error.code === 4001 || error.rawMessage?.includes('insufficient credits')) {
  emitInsufficientCredits();  // triggers InsufficientCreditsDialog globally
  return;
}
```

The `InsufficientCreditsDialog` component (mounted in the locale layout) listens for this event and shows a purchase prompt.

### 2. Non-401 Errors

```typescript
if (error.status !== 401) {
  emitError(error, { path, page });  // triggers toast via ErrorHandlerProvider
}
```

The `emitError` function (in `src/lib/error-handler.ts`) determines severity, translates the message, and dispatches a custom event. The `ErrorHandlerProvider` subscribes and calls `toast.error()`.

### 3. 401 Unauthorized

```typescript
if (error.status === 401) {
  const refreshed = await refreshSession();
  if (refreshed) {
    return apiClient.request<T>(path, config);  // retry original request
  }
  clearCurrentUser('expired');
  window.location.href = '/login';
}
```

Session refresh attempts to get a new access token. If it fails, the user is logged out and redirected to the login page.

### 4. 登录态就绪等待（ensureSessionReady，2026-08-08 教训）

**Problem**: 页面挂载时多个业务请求（`enterprises/me`、`zclaw/status`、`model-config` 等）与 `useSession` 的 `/api/auth/me` 探测**并发**发出。未登录（无 localStorage 用户缓存）时全部 401，每个请求各触发一次 `refreshSession`（刷新 token 的网络往返）→ 首屏 6+ 次无谓 401 + refresh，控制台噪音。

**Solution**: `executeRequest` 入口等待登录态就绪（`apps/web/lib/api-client.ts`）：

```typescript
// 模块级共享 Promise：首个业务请求发现无本地用户时创建 /api/auth/me 探测，
// 并发请求共享等待（复用 refreshSession 的 ongoingRefresh 模式）
let sessionReadyPromise: Promise<void> | null = null;

function ensureSessionReady(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve();
  // 已有本地用户（localStorage 'insightweaver:current-user'）→ 直接放行，零开销
  try {
    if (window.localStorage.getItem('insightweaver:current-user')) {
      return Promise.resolve();
    }
  } catch { /* ignore */ }
  if (sessionReadyPromise) return sessionReadyPromise;
  const url = new URL('/api/auth/me', API_CONFIG.BASE_URL).toString();
  sessionReadyPromise = fetch(url, { credentials: 'include' })
    .then((res) => { if (!res.ok) throw new Error(`session check failed: ${res.status}`); })
    .catch(() => { /* 探测失败（真未登录）→ 放行，让业务请求自己报 401 走 refresh */ })
    .finally(() => { sessionReadyPromise = null; });
  return sessionReadyPromise;
}
```

**接入条件**（`executeRequest` 开头）：

```typescript
if (!config.skipAuthRefresh && pathname !== '/api/auth/me' && !isAuthEndpoint(pathname)) {
  await ensureSessionReady();
}
```

**排除矩阵**（避免死锁）：

| 场景 | 是否等待 | 原因 |
|------|---------|------|
| 业务请求（enterprises/me、zclaw/*、model-config） | ✅ 等待 | 延后到登录态确认后再发 |
| auth 端点（login/sms/refresh/logout） | ❌ 不等待 | `isAuthEndpoint` 排除，登录流程不能被探测阻塞 |
| `/api/auth/me` 本身 | ❌ 不等待 | 否则探测自我死锁 |
| `skipAuthRefresh: true` 的请求 | ❌ 不等待 | 调用方自行处理登录态 |
| 已登录（localStorage 有缓存用户） | ❌ 直接放行 | 探测零开销 |

**关键**：
- 等待失败**必须放行**（catch 后 resolve），否则未登录用户永远卡住——探测失败 = 真未登录，业务请求的 401 + refresh 是正确兜底
- 共享 Promise 使并发请求只发一次探测（与 `refreshSession` 的 `ongoingRefresh` 同一模式）
- 实测：清缓存首次访问，业务请求全部延后到 `auth/me` 200 后发出，零 401 零 refresh

## Enterprise Context Injection

For requests to `/api/zclaw/*`, the client automatically adds the `x-enterprise-id` header:

```typescript
// In api-client.ts request method:
if (path.startsWith('/api/zclaw/')) {
  const headers = withActiveEnterpriseHeader(config.headers);
  // x-enterprise-id is read from localStorage key 'zclaw:active-enterprise-id'
}
```

This is handled by `withActiveEnterpriseHeader()` from `src/lib/enterprise-context.ts`.

## API Module Organization

### Directory Structure

```
apps/web/src/api/
├── index.ts            # Barrel: export * from './moudles/*'
└── moudles/            # Note: directory name is a typo, but it's the real name
    ├── auth.ts         # login, logout, refreshSession, getCurrentUser
    ├── billing.ts      # listBillingPlans, createBillingOrder
    ├── credits.ts      # getCreditLedger, getCreditSummary
    ├── dashboard.ts    # getDashboardStats
    ├── enterprise.ts   # listEnterprises, getEnterpriseDetail
    ├── enterprise-branding.ts
    ├── skills.ts       # listSkills, createSkill, updateSkill
    ├── agents.ts       # listAgents, createAgent
    ├── zclaw.ts        # chat-related endpoints
    ├── research.ts     # research session endpoints
    ├── pay.ts          # payment processing
    ├── attachments.ts  # file upload/download
    ├── super-lobster.ts
    └── admin-users.ts  # admin user management
```

### Module Function Pattern

Each module file exports typed functions:

```typescript
// apps/web/src/api/moudles/billing.ts
import { apiClient } from '../../../lib/api-client';

export interface BillingPlan {
  id: string;
  name: string;
  price: string;       // BigInt serialized as string
  creditQuota: string;  // BigInt serialized as string
}

export async function listAdminBillingPlans(): Promise<BillingPlan[]> {
  return apiClient.get<BillingPlan[]>('/api/admin/billing-plans');
}

export async function createBillingPlan(data: CreateBillingPlanInput): Promise<BillingPlan> {
  return apiClient.post<BillingPlan>('/api/admin/billing-plans', data);
}
```

### Import Pattern in Pages

```typescript
// In a page component:
import { listAdminBillingPlansApi, type BillingPlan } from '@/api';
```

The `@/api` alias resolves to `src/api/index.ts`, which re-exports everything from all module files.

## BigInt Handling

The backend returns `bigint` fields as strings (e.g., `"1000000000000"`). The API layer preserves them as strings. UI code converts to display units:

```typescript
// In page component:
const displayQuota = BigInt(plan.creditQuota) / BigInt(1_000_000);
// or with formatting helpers
const formatted = formatTokenAmount(plan.creditQuota);
```

## Idempotency Keys

Create/update operations include idempotency keys generated client-side:

```typescript
function generateIdempotencyKey(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

// Usage:
await apiClient.post('/api/zclaw/items', {
  ...formData,
  idempotencyKey: generateIdempotencyKey('item-create'),
});
```
