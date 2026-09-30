# Bilingual Errors

The platform serves users in both Chinese and English. Error messages originate from two sources: our own code (written in Chinese) and framework errors (NestJS/Prisma, in English). This guide documents the dual-layer translation pattern.

---

## The Two-Layer Pattern

### Layer 1: API Error Messages Are Written in Chinese

Our custom error messages in `apps/api/src/common/constants/error-codes.ts` are written **directly in Chinese**. The `ERROR_MESSAGES` record maps each `ErrorCode` to a Chinese string:

```ts
// apps/api/src/common/constants/error-codes.ts
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.SUCCESS]: '成功',
  [ErrorCode.INVALID_ARGUMENT]: '请求参数无效',
  [ErrorCode.UNAUTHORIZED]: '登录已过期，请重新登录',
  [ErrorCode.INSUFFICIENT_CREDITS]: '额度不足，请充值后重试',
  [ErrorCode.INTERNAL_ERROR]: '服务器暂时不可用，请稍后重试',
  // ... all messages are in Chinese
}
```

**Why Chinese-first:**
- The majority of production users are Chinese-locale.
- Writing Chinese directly means the common case requires no translation.
- Business error messages are precise in the language they'll mostly be displayed in.

### Layer 1b: Framework Errors Get Translated to Chinese

When NestJS or Prisma throws an error (in English), `AllExceptionsFilter` at `apps/api/src/common/filters/all-exceptions.filter.ts` applies pattern-based translation:

```
Prisma: "Record not found" -> "记录 不存在"
NestJS: "Unauthorized" -> "未授权"
```

Translation rules in the filter:

| English Pattern | Chinese Translation |
|---|---|
| `X not found` | `X 不存在` |
| `X is required` | `X 为必填项` |
| `X already exists` | `X 已存在` |
| `Invalid X` | `X 无效` |
| `Unauthorized` | `未授权` |
| `Forbidden` | `禁止访问` |

### Layer 2: Web Re-Translates for English Locale

When the user's locale is `en`, the web layer re-translates Chinese error messages back to English. This happens in `apps/web/src/lib/error-codes.ts` using two mechanisms:

**Exact string matches** (`BACKEND_EXACT_MESSAGES`):
```ts
// For known, specific error messages
'conversation not found' -> '历史会话数据加载失败'
```

**Pattern-based rules** (`BACKEND_PATTERN_RULES`):
```ts
// Regex-based translation for English locale users
/(.+?)\s+not\s+found$/i  ->  `${subject} 不存在`
/(.+?)\s+is\s+required$/i  ->  `${subject} 为必填项`
```

The web error handler also uses `translateAutoText()` for English locale, which applies the reverse direction — translating Chinese strings to English for display.

---

## Where Each Piece Lives

### API Side (`apps/api`)

| File | Purpose |
|---|---|
| `src/common/constants/error-codes.ts` | ErrorCode enum + Chinese ERROR_MESSAGES |
| `src/common/filters/all-exceptions.filter.ts` | Catches exceptions, translates English framework errors to Chinese, builds envelope |

### Web Side (`apps/web`)

| File | Purpose |
|---|---|
| `src/lib/error-codes.ts` | Severity mapping, BACKEND_EXACT_MESSAGES, BACKEND_PATTERN_RULES, `hasChinese()` detection |
| `src/lib/error-handler.ts` | `errorToast()`, `DedupManager`, severity-based toast styling |
| `messages/zh.json` | Chinese UI strings for `next-intl` |
| `messages/en.json` | English UI strings for `next-intl` |

---

## Adding a New Error Code

Follow this checklist in order:

### 1. Define the error code in API

In `apps/api/src/common/constants/error-codes.ts`:

```ts
export enum ErrorCode {
  // ... existing codes
  BILLING_PLAN_DOWNGRADE_NOT_ALLOWED = 4005,
}
```

### 2. Add the Chinese message in the same file

```ts
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  // ... existing messages
  [ErrorCode.BILLING_PLAN_DOWNGRADE_NOT_ALLOWED]: '不允许降级计费方案',
}
```

### 3. Throw it from the appropriate service

```ts
throw new BusinessException(ErrorCode.BILLING_PLAN_DOWNGRADE_NOT_ALLOWED)
```

The `AllExceptionsFilter` handles the rest on the API side.

### 4. Add severity and translation in the web error-code map

In `apps/web/src/lib/error-codes.ts`:

```ts
// If this error should be shown with a specific severity:
[ErrorCode.BILLING_PLAN_DOWNGRADE_NOT_ALLOWED]: ErrorSeverity.NORMAL
```

### 5. If English locale needs a different message

Add to `BACKEND_EXACT_MESSAGES` or `BACKEND_PATTERN_RULES` in the same file:

```ts
// Exact match
'不允许降级计费方案': 'Billing plan downgrade is not allowed',

// Or pattern rule (if the message follows a pattern)
```

### 6. Add UI translations if using i18n keys

`apps/web/messages/zh.json`:
```json
{
  "errors": {
    "billing_plan_downgrade_not_allowed": "不允许降级计费方案"
  }
}
```

`apps/web/messages/en.json`:
```json
{
  "errors": {
    "billing_plan_downgrade_not_allowed": "Billing plan downgrade is not allowed"
  }
}
```

---

## Edge Cases

### Unknown Error Code

If the API returns a code that the web error-code map does not recognize:
- For `zh` locale: display the `message` from the envelope as-is (it is already Chinese).
- For `en` locale: `translateAutoText()` attempts to convert the Chinese string to English.

### Internal vs. User-Facing Errors

Not all errors need bilingual translation. Internal errors (database connection failures, unexpected exceptions) should:
- Log the full stack trace server-side via `AppLogger`.
- Return a generic envelope `{ code: 5000, message: "服务器暂时不可用，请稍后重试" }`.
- The web layer shows a generic toast regardless of locale.

Never expose stack traces, SQL errors, or raw Prisma error messages to the client.

---

## Severity System

The web error handler uses four severity levels, each with different toast behavior:

| Severity | Duration | Style | Use Case |
|---|---|---|---|
| `SILENT (0)` | — | — | Console log only (background polling failures) |
| `LIGHT (1)` | 1.5s | Subtle | Validation errors, SMS errors |
| `NORMAL (2)` | 3s | Amber | Forbidden, account disabled |
| `CRITICAL (3)` | 3s | Default | Unauthorized, expired token, insufficient credits |

Silent rules (`SILENT_RULES` in `error-codes.ts`) suppress errors for background API calls on specific pages (e.g., credit ledger polling on the home page) using path+page regex pairs.
