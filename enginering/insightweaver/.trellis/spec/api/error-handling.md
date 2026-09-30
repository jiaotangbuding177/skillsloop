# Error Handling

## Error Code System

All error codes are defined in `apps/api/src/common/constants/error-codes.ts` as an enum:

```typescript
// apps/api/src/common/constants/error-codes.ts
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

Each error code has a corresponding Chinese message in `ERROR_MESSAGES` (same file). Messages are written directly in Chinese — not translated from English at the API level.

Code ranges indicate error categories:

| Range | Category | Examples |
|-------|----------|---------|
| 0 | Success | `SUCCESS` |
| 1xxx | Client input errors | `INVALID_ARGUMENT` |
| 2xxx | Authentication errors | `UNAUTHORIZED` |
| 3xxx | Authorization errors | `FORBIDDEN` |
| 4xxx | Business rule violations | `INSUFFICIENT_CREDITS` |
| 5xxx | Server errors | `INTERNAL_ERROR` |

## Response Envelope

All API responses (success and error) are normalized to a consistent shape by the `ResponseInterceptor`:

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

Error responses:

```json
{
  "code": 4001,
  "message": "余额不足",
  "data": null
}
```

## AllExceptionsFilter

File: `apps/api/src/common/filters/all-exceptions.filter.ts`

This global filter catches **every** exception type and normalizes it into the response envelope. It is registered in `apps/api/src/main.ts`:

```typescript
app.useGlobalFilters(new AllExceptionsFilter());
```

### Filter Behavior

1. **BusinessException** (custom): Extracts `code` and `message` directly
2. **NestJS HttpException**: Maps HTTP status to error code, translates message
3. **PrismaClientKnownRequestError**: Translates Prisma error messages to Chinese
4. **Unknown errors**: Returns `INTERNAL_ERROR` (5000) with generic Chinese message

### Normalization Logic

```typescript
// Pseudocode of the filter's core logic
catch(exception, host) {
  let code: number;
  let message: string;

  if (exception instanceof BusinessException) {
    code = exception.code;
    message = exception.message;
  } else if (exception instanceof HttpException) {
    code = httpStatusToErrorCode(exception.getStatus());
    message = translateEnglishMessage(exception.message);
  } else if (exception instanceof PrismaClientKnownRequestError) {
    code = prismaCodeToErrorCode(exception.code);
    message = translateEnglishMessage(exception.message);
  } else {
    code = ErrorCode.INTERNAL_ERROR;
    message = '服务器内部错误';
  }

  response.json({ code, message, data: null });
}
```

## Bilingual Error Translation

The filter includes a `translateEnglishMessage()` function that converts English error messages from NestJS and Prisma into Chinese. This ensures a consistent user experience for the Chinese-speaking user base.

### Translation Rules

Pattern-based translations applied to error messages:

| English Pattern | Chinese Translation |
|---------------|-------------------|
| `X not found` | `X 不存在` |
| `X is required` | `X 为必填项` |
| `X already exists` | `X 已存在` |
| `Invalid X` | `X 无效` |
| `X must be a Y` | `X 必须是 Y` |
| `Unauthorized` | `未授权` |
| `Forbidden` | `禁止访问` |

### Implementation Pattern

```typescript
// apps/api/src/common/filters/all-exceptions.filter.ts
function translateEnglishMessage(message: string): string {
  // Pattern matching
  if (message.includes('not found')) {
    return message.replace(/(\w+) not found/, '$1 不存在');
  }
  if (message.includes('is required')) {
    return message.replace(/(\w+) is required/, '$1 为必填项');
  }
  // ... more patterns

  // Fallback: return original message if no pattern matches
  return message;
}
```

### Why Bilingual

- **Default messages** in the codebase are written in Chinese (e.g., `'余额不足'`, `'套餐不存在'`)
- **Framework messages** (NestJS validation errors, Prisma errors) arrive in English
- The translation layer bridges this gap so the frontend only needs to handle Chinese error strings

## Throwing Errors in Services

### BusinessException (Preferred)

```typescript
import { ErrorCode } from '../common/constants/error-codes';

// With specific error code
throw new BusinessException(ErrorCode.INSUFFICIENT_CREDITS, '余额不足');

// With invalid argument
throw new BusinessException(ErrorCode.INVALID_ARGUMENT, '套餐 ID 无效');
```

### NestJS Built-in Exceptions (Also Supported)

The filter handles these too, translating their messages:

```typescript
throw new NotFoundException('Billing plan not found');
// -> { code: 1001, message: "Billing plan 不存在" }

throw new ForbiddenException('Access denied');
// -> { code: 3001, message: "禁止访问" }
```

### Unhandled Exceptions

Any uncaught exception is caught by the filter and returned as:

```json
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
```

The original error is logged server-side but never exposed to the client.

## Global Interceptor Order

From `apps/api/src/main.ts`, the interceptor and filter registration order matters:

```typescript
// 1. Logging interceptor (runs first on request, last on response)
app.useGlobalInterceptors(new LoggingInterceptor());

// 2. Response interceptor (wraps the response in envelope)
app.useGlobalInterceptors(new ResponseInterceptor());

// 3. Exception filter (catches errors before response interceptor)
app.useGlobalFilters(new AllExceptionsFilter());
```

Execution order for a request:
1. `LoggingInterceptor` — starts timer, logs request
2. Controller executes
3. On success: `ResponseInterceptor` wraps response -> `LoggingInterceptor` logs duration
4. On error: `AllExceptionsFilter` catches, normalizes -> `LoggingInterceptor` logs duration + error

## DTO 校验消息的用户可读性（2026-09-05）

**问题**：`ZclawInputFileDto.mimeType` 校验失败时，ValidationPipe 抛出的英文详细消息（`files.0.mimeType must be one of the following values: ...`）经 `translateEnglishMessage` 无匹配规则 → 回退笼统的 `ERROR_MESSAGES[1001]`「请求参数无效」，用户完全看不出原因（bugfix-20260905-chat-video-attachment）。

**机制**（`AllExceptionsFilter.getMessage`）：ValidationPipe 的 message 数组会 `join('; ')` 后过 `toPublicMessage`——**整串含中文即原样透传**（`hasChinese`），无匹配且无中文才回退 ERROR_MESSAGES 笼统文案。

**规则**：需要给用户友好报错的 DTO 字段，直接在 decorator 上写中文 message，不要依赖翻译表：

```typescript
@IsIn(ZCLAW_ALLOWED_FILE_MEDIA_TYPES, {
  message: '不支持的附件类型，仅支持图片、PDF、Word/Excel/PPT、文本、CSV、JSON、ZIP 与 MP4/WebM/MOV 视频',
})
mimeType!: (typeof ZCLAW_ALLOWED_FILE_MEDIA_TYPES)[number];
```

- 单字段失败时输出干净中文；多字段同时失败（中文+英文混合 join）整串透出——可接受，但要避免关键报错字段与英文常同时失败的场景设计
- 翻译表（`translateEnglishMessage`）只兜底 service 层英文 `BadRequestException`（如 `unsupported file type: xxx` 已有模式规则）

## Error Handling Checklist for New Endpoints

When adding a new endpoint, ensure:

1. Throw `BusinessException` with appropriate `ErrorCode` for known business failures
2. Write error messages in Chinese for direct user display
3. Do not catch and swallow exceptions — let the global filter handle them
4. Do not manually construct `{ code, message, data }` in controllers — the filter and interceptor handle this
5. Validate inputs via DTO decorators — `ValidationPipe` handles field-level errors automatically
