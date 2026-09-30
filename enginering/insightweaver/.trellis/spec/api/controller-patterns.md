# Controller Patterns

## Routing Conventions

Controllers use the `@Controller()` decorator with a path string. The global prefix `api` is applied in `apps/api/src/main.ts`, so all routes resolve to `/api/...`.

```typescript
// apps/api/src/main.ts
app.setGlobalPrefix('api');
```

### Route Path Patterns

| Category | Pattern | Example | Resolved Path |
|----------|---------|---------|---------------|
| Admin | `admin/{resource}` | `@Controller('admin/billing')` | `/api/admin/billing` |
| User-facing | `{resource}/{sub}` | `@Controller('billing/entitlements')` | `/api/billing/entitlements` |
| Enterprise | `{resource}` | `@Controller('enterprises')` | `/api/enterprises` |

## Guard Composition

Guards are applied at the controller level or method level using `@UseGuards()`. The codebase uses a three-tier access model.

### Tier 1: Platform Admin (JwtAuthGuard + AdminGuard)

For routes only accessible to platform administrators:

```typescript
// apps/api/src/admin/admin-billing.controller.ts
@Controller('admin/billing')
@UseGuards(JwtAuthGuard, AdminGuard)
export class AdminBillingController {
  // Only platform admins can access any method
}
```

Both guards run in sequence: `JwtAuthGuard` validates the JWT token, then `AdminGuard` checks platform-level admin privileges.

### Tier 2: Enterprise Admin (JwtAuthGuard + method-level AdminGuard)

For routes where some actions require enterprise admin and others are available to all authenticated users:

```typescript
// apps/api/src/enterprise/enterprise.controller.ts
@Controller('enterprises')
@UseGuards(JwtAuthGuard)
export class EnterpriseController {

  @Get()
  listEnterprises() {
    // Any authenticated user
  }

  @Post(':id/members')
  @UseGuards(AdminGuard)
  addMember(@Param('id') id: string) {
    // Only enterprise admins
  }
}
```

### Tier 3: Regular Authenticated User (JwtAuthGuard only)

For user-facing endpoints:

```typescript
// apps/api/src/billing/entitlement.controller.ts
@Controller('billing/entitlements')
@UseGuards(JwtAuthGuard)
export class EntitlementController {
  @Get()
  getMyEntitlements(@Req() req: Request) {
    // Uses req.user.userId from JWT
  }
}
```

### Optional Auth (OptionalJwtAuthGuard)

For endpoints that work for both authenticated and anonymous users:

```typescript
@Controller('public/plans')
@UseGuards(OptionalJwtAuthGuard)
export class PublicPlanController {
  @Get()
  listPlans(@Req() req: Request) {
    // req.user may be undefined for anonymous
  }
}
```

## Guard Implementation Details

### JwtAuthGuard

File: `apps/api/src/auth/jwt-auth.guard.ts`

- Extracts JWT from `Authorization: Bearer <token>` header
- Falls back to `access_token` cookie
- Sets `req.user = { userId: payload.sub }`
- Throws `UnauthorizedException` if token is missing or invalid

### AdminGuard

- Checks `req.user.userId` against platform admin list
- Applied after `JwtAuthGuard` (depends on `req.user` being set)

## Idempotency

Every mutating endpoint (POST, PUT, PATCH, DELETE) accepts an `Idempotency-Key` header. The header is extracted using a shared utility function.

### Pattern

```typescript
// apps/api/src/billing/billing-plan.controller.ts
@Controller('admin/billing/plans')
@UseGuards(JwtAuthGuard, AdminGuard)
export class BillingPlanController {

  @Post()
  createPlan(
    @Body() dto: CreateBillingPlanDto,
    @Headers() headers: Record<string, string>,
  ) {
    const idempotencyKey = getIdempotencyKey(headers);
    return this.service.createPlan(dto, idempotencyKey);
  }

  @Put(':id')
  updatePlan(
    @Param('id') id: string,
    @Body() dto: UpdateBillingPlanDto,
    @Headers() headers: Record<string, string>,
  ) {
    const idempotencyKey = getIdempotencyKey(headers);
    return this.service.updatePlan(id, dto, idempotencyKey);
  }
}
```

### getIdempotencyKey Utility

```typescript
// Shared utility (likely in src/common/)
export function getIdempotencyKey(
  headers: Record<string, string>,
): string | undefined {
  return headers['idempotency-key'] || headers['Idempotency-Key'];
}
```

Services use the idempotency key as a unique constraint value. On duplicate key (`PrismaClientKnownRequestError` code `P2002`), the service returns the existing record instead of creating a new one.

## Request Parameter Patterns

### Path Parameters

```typescript
@Get(':id')
getPlan(@Param('id') id: string) {}
```

### Query Parameters

```typescript
@Get()
listPlans(
  @Query('page') page?: number,
  @Query('pageSize') pageSize?: number,
) {}
```

### Request Body with DTO Validation

```typescript
@Post()
createPlan(@Body() dto: CreateBillingPlanDto) {}
```

DTOs use `class-validator` decorators. The global `ValidationPipe` (configured in `main.ts`) enforces:
- `whitelist: true` — strips properties not decorated in the DTO
- `transform: true` — transforms types (string -> number, etc.)

### Accessing the Authenticated User

```typescript
@Get('me')
getMyProfile(@Req() req: Request & { user: { userId: string } }) {
  const userId = req.user.userId;
}
```

## Response Patterns

All responses pass through the `ResponseInterceptor`, which wraps the return value in a standard envelope:

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

Controllers return raw data — the interceptor handles wrapping. Do not manually wrap responses in controllers.

## Validation Pipe Configuration

From `apps/api/src/main.ts`:

```typescript
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    transform: true,
  }),
);
```

This means:
- Unknown DTO properties are silently stripped
- Query/path params are auto-transformed to declared types
- Validation errors throw `BadRequestException` with field-level details

## Owner-Only Mutations (vs Admin-or-Owner)

**What**: sensitive enterprise-config **mutations** that alter the quota/billing model must call `assertEnterpriseOwner`; reads and general admin actions use `assertEnterpriseAdminOrOwner`. Defense-in-depth: backend rejects (403) AND frontend disables the control.

**Why**: enterprise `admin` is a delegated role (manage members, view config) but must NOT alter the fundamental quota model. `owner` is the account authority.

**Methods** (`apps/api/src/enterprises/enterprise.service.ts`):
- `assertEnterpriseOwner(userId, enterpriseId)` — throws 403 unless user is the enterprise **owner**. Use for: default-quota-policy toggle, post-expiry purchase-mode config, and any mutation that reshapes how the enterprise is billed/quota'd.
- `assertEnterpriseAdminOrOwner(userId, enterpriseId)` — allows admin OR owner. Use for: reads, member management, general admin.

**Example** (`apps/api/src/billing/default-quota-policy.controller.ts`):
```typescript
@Controller('billing/default-quota-policy')
@UseGuards(JwtAuthGuard)
export class DefaultQuotaPolicyController {
  @Get()
  async get(@Req() req, @Query() q) {
    await this.enterpriseService.assertEnterpriseAdminOrOwner(req.user.userId, q.enterpriseId); // admins may view
    return this.defaultQuotaPolicyService.getPolicy(q.enterpriseId);
  }
  @Patch()
  async update(@Req() req, @Body() dto) {
    await this.enterpriseService.assertEnterpriseOwner(req.user.userId, dto.enterpriseId); // owner only
    return this.defaultQuotaPolicyService.updatePolicy(req.user.userId, dto);
  }
}
```

**Frontend mirror**: compute the `disabled` prop via a pure rule (`resolvePolicyCardDisabled({ policy, enterpriseRole })` → `true` when `enterpriseRole !== "owner"`) so it is unit-testable; the card is a thin consumer. Super-admin path (`Admin*Controller` + `AdminGuard`) bypasses the enterprise-role check entirely — platform admins always can.

**Precedent**: `PostExpiryBehaviorCard` is already owner-only (rendered when `enterpriseRole === "owner"`).

**Wrong vs Correct**:
```typescript
// WRONG: admins can toggle the master quota switch
await this.enterpriseService.assertEnterpriseAdminOrOwner(req.user.userId, dto.enterpriseId);
// CORRECT: only the owner (super-admin uses the Admin* path)
await this.enterpriseService.assertEnterpriseOwner(req.user.userId, dto.enterpriseId);
```

## File Upload Patterns

### Scenario: Large-File Upload (diskStorage + streaming forward)

#### 1. Scope / Trigger
Upload endpoints that accept files up to 500MB (`/api/zclaw/workspace/upload`, `/api/zclaw/shared-workspace/upload`, `/api/zclaw/chat/files`) and forward them to the KM Agent upstream. **Trigger**: `memoryStorage()` loads the whole file into the V8 heap, and the forward step copies it twice (`new Uint8Array` + `new Blob`) — peak ~3x file size (260MB file → ~780MB) → container OOM crash, all routes 502.

#### 2. Signatures
- Controller: `POST /api/zclaw/{workspace|shared-workspace}/upload`, `POST /api/zclaw/chat/files` (multer `FileInterceptor` + shared `uploadTempStorage`)
- Client: `ZclawKmAgentClient.uploadWorkspaceFile(userId, targetPath, file: UploadFileInput)` / `uploadSharedWorkspaceFile(...)` → private `forwardMultipartFile(userId, routePath, targetPath, file, failureMessage)`
- `interface UploadFileInput { filePath?: string; buffer?: Buffer; filename: string; mimeType: string }` (`zclaw-km-agent.client.ts`)

#### 3. Contracts
- **Ingress**: multer `diskStorage` into `process.cwd()/.upload-temp/` via module-level shared `uploadTempStorage` (dedupe the `filename` callback); `limits: { fileSize: 500MB, files: 1 }`. Ext name sanitized: `replace(/[^a-zA-Z0-9]/g, "").slice(0, 16) || "bin"` (originalname is client-controlled; prevents path-separator/null-byte injection).
- **Forward**: Node 22 `openAsBlob(filePath, { type: mimeType })` lazy Blob + standard Web `FormData` as `fetch` body — streams from disk, V8 heap ~0. Content-Type with boundary is generated by fetch. Keep the `buffer` branch for in-memory callers (e.g. `copyCrossSpaceFile`).
- **Cleanup**: controller wraps the service call in `try { return await service(...) } finally { if (file.path) await unlink(file.path).catch(() => undefined) }` — **must `await`**, otherwise `finally` runs before the service completes and deletes the file mid-read. Client does NOT unlink.
- **Env**: `.upload-temp` needs ≥2GB free disk; upstream limit `KM_AGENT_MAX_UPLOAD_BYTES` (500MB).

#### 4. Validation & Error Matrix
| Condition | Behavior |
|-----------|----------|
| Service pre-flight validation throws (`assertWorkspaceWriteAllowed`, `assertSharedWorkspacePermission`, `validateUploadedFile`, …) | Controller `finally` unlinks the temp file |
| `openAsBlob` fails (ENOENT/EACCES) | Wrapped as `InternalServerErrorException` (no raw SystemError / stack leak) |
| Upstream returns non-2xx | `BadGatewayException(detail)` |
| File > 500MB | multer limit → 400 |
| `uploadAgentAvatar` (2MB) | **stays `memoryStorage()`** — service reads `file.buffer` for OSS put; 2MB is harmless in RAM |

#### 5. Good/Base/Bad Cases
- **Good**: 260MB upload → disk-backed ingress, streamed forward, temp file removed after response
- **Base**: validation failure (oversized/unsupported type) → clean 4xx + temp file removed
- **Bad**: `memoryStorage` + buffer copying → OOM; client-only cleanup → temp files leak on every validation failure

#### 6. Tests Required
`apps/api/src/zclaw/zclaw.controller.upload-cleanup.test.ts` — 4 cases: 3 endpoints assert temp file removed when the service throws; 1 success path asserts removal. Direct controller invocation with a real temp file as `file.path` (mock service), no HTTP layer needed. Note `uploadSharedWorkspaceFile` has 4 params `(req, path, orgVisibility, file)` — pass `undefined` for orgVisibility.

#### 7. Wrong vs Correct
```typescript
// WRONG: memoryStorage + 3x memory amplification (OOM at 260MB)
storage: memoryStorage(),
// CORRECT: diskStorage + shared uploadTempStorage (V8 heap 0 on ingress)

// WRONG: cleanup in the KM-agent client finally — service pre-flight throws
// before the client call, temp file leaks permanently
// CORRECT: cleanup owned by the controller try/finally, client never unlinks

// WRONG: fetch body = form-data pkg instance (needs duplex:'half', missing from
// @types/node@22.19.3 RequestInit → TS hack)
// CORRECT: openAsBlob + Web FormData — zero deps, no type hack
```

### Design Decision: openAsBlob vs form-data

**Context**: Streaming the temp file to the upstream without loading it into memory.

**Options Considered**:
1. `form-data@4.0.5` (CJS, already in pnpm store) + `createReadStream` — undici streaming body needs `duplex: 'half'`, but the repo's `@types/node@22.19.3` `RequestInit` type lacks that field → compile error / `as any` hack.
2. Node native `openAsBlob(path, { type })` + global Web `FormData` — lazy Blob backed by a file descriptor; fetch generates the multipart Content-Type itself.

**Decision**: `openAsBlob`. Zero new deps, standard API, no type hacks; measured 100MB upload → ~0.5MB heap growth. `blob.size` is known (internal stat) so multipart can carry Content-Length. fd lifecycle: no dispose API — undici consumes `blob.stream()` on transfer/abort and closes the fd; on Linux an unlinked inode survives until fd close, so no leak under sustained failures.

### Design Decision: Temp-file Cleanup Ownership

**Context**: multer `diskStorage` writes the file *before* the controller handler runs; service-side `await` validations can throw before the KM-agent client is reached.

**Decision**: Cleanup lives in the **controller** layer (`try/finally` around the whole service call). Any inner-layer cleanup (client/service) is unreachable on pre-flight validation failures and leaks temp files permanently — under attack or frequent validation errors this exhausts disk. The controller is the outermost owner of `file.path`, so it is the single responsibility holder.
