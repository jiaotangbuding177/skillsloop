# Database Package Specification

## Overview

`packages/db` is the Prisma-based database layer for the InsightWeaver Quota UI platform. It wraps `@prisma/client` with a singleton pattern, ESM/CJS interop shims, and schema-version pinning to survive hot-reload safely.

**Schema location:** `packages/db/prisma/schema.prisma` (1743 lines, ~50 models)
**Package type:** ESM (`"type": "module"`)
**Database:** PostgreSQL with a shadow database for safe migration dry-runs

---

## ESM/CJS Interop

Prisma Client ships as CommonJS. The db package is ESM. The boundary lives in `packages/db/src/index.ts`:

```ts
import PrismaClientModule from '@prisma/client'
// Default import gets the CJS module namespace object
const { PrismaClient, Prisma } = PrismaClientModule

export { PrismaClient, Prisma }
export type * from '@prisma/client'  // type-only re-export avoids runtime CJS named-import crash
```

**Rule:** Never add a bare `export { SomeModel } from '@prisma/client'` — named runtime exports from CJS break under Node ESM resolution. Use `export type *` for all Prisma-generated types.

---

## Singleton with Schema-Version Pinning

`packages/db/src/index.ts` exports a singleton that pins `PRISMA_SCHEMA_VERSION`:

```ts
const PRISMA_SCHEMA_VERSION = 'v47-2026-07-10'
let cached: PrismaClient | undefined
let cachedVersion: string | undefined

export function getPrismaClient(): PrismaClient {
  if (cached && cachedVersion === PRISMA_SCHEMA_VERSION) return cached
  cached?.disconnect()
  cached = new PrismaClient()
  cachedVersion = PRISMA_SCHEMA_VERSION
  return cached
}
```

**When to bump:** After any `prisma migrate deploy` or schema change that alters the generated client types, update the version string. This prevents a stale client from serving requests after a hot-reload picks up a new schema but reuses the old process.

---

## Naming Conventions

| Layer | Convention | Example |
|---|---|---|
| Table names | `snake_case` via `@@map()` | `@@map("billing_orders")` |
| Model names | PascalCase (Prisma) | `BillingOrder` |
| Field names | camelCase | `enterpriseId`, `createdAt` |
| Relation fields | camelCase, singular | `enterprise`, `billingPlan` |
| Enum values | SCREAMING_SNAKE_CASE | `EnterpriseKind.B2B` |

Every model must include:

```prisma
createdAt DateTime @default(now())
updatedAt DateTime @updatedAt
isDeleted Boolean @default(false)
```

---

## Soft Deletion

`isDeleted Boolean @default(false)` is present on nearly every model. All queries in API services must filter `where: { isDeleted: false }` unless explicitly reading deleted records (e.g., audit recovery). There is no global Prisma middleware for this — it is enforced per-query to keep the filter visible in code review.

**Never** delete with `delete()` or `deleteMany()`. Always use:

```ts
await prisma.someModel.update({
  where: { id },
  data: { isDeleted: true },
})
```

---

## BigInt for Monetary and Token Amounts

All fields that represent monetary values (cents), token counts, or byte sizes use `BigInt`:

```prisma
totalTokens   BigInt
amountCents   BigInt
bytesUsed     BigInt
```

**Interop note:** BigInt is not JSON-serializable by default. API serializers must convert to string (`amount.toString()`) before sending over the wire. Web clients receive these as strings and parse with `BigInt()` only when arithmetic is needed.

---

## Domain Aggregates

The schema is organized around these aggregate roots. When adding a new model, attach it to the correct aggregate — do not create orphan top-level models without a clear ownership path.

### User Aggregate
`User` -> `UserIdentity`, `UserWallet`, `CreditLedger`, `UserRefreshToken`, `AuditLog`

### Enterprise Aggregate
`Enterprise` -> `EnterpriseMembership`, `Department`, `DepartmentGroup`, `OpenClawInstance`, `RagflowConfig`, `BillingPlan`, `BillingOrder`, `EnterpriseDefaultQuotaPolicy`

### Billing/Entitlement Sub-domain
`BillingPlan`, `BillingOrder`, `EntitlementBatch`, `EntitlementLedger`, `BillingTask`, `BillingTaskEvent`, `BillingTopupInventory`

### ZClaw (AI Assistant) Sub-domain
`ZclawAgentInstance`, `ZclawSession`, `ZclawMessage`, `ZclawModelConfig`, `PersonalAssistant`

### Enterprise Quota Sub-domain
`ConversationQuotaConfig`, `ConversationQuotaUsage`, `TokenQuotaBatch`, `TokenQuotaMember`, `TokenQuotaSettlement`

### Research Sub-domain
`ResearchSession`, `ResearchMessage`, `ResearchOutline` (with `ResearchOutlineVersion`), `ResearchContent`, `ResearchAttachment`

### System
`AuditLog`, `SystemBootstrapJobRun`, `HumanEfficiencyEvent`

---

## Migrations

- Always use `prisma migrate dev --create-only` to generate the migration SQL without applying it.
- Review the SQL, then apply with `prisma migrate deploy`.
- The shadow database (`shadowDatabaseUrl` in `schema.prisma`) catches destructive changes before they hit the real database.
- Never hand-edit a migration file after it has been applied to any shared environment.

### Non-Interactive Environments

`prisma migrate dev` requires an interactive TTY — it will fail with "Prisma Migrate has detected that the environment is non-interactive" in CI pipelines, agent tools, or any non-TTY shell. In these contexts:

```bash
# WRONG — fails in non-interactive shells
pnpm db:migrate   # runs prisma migrate dev

# CORRECT — applies existing migration files without prompts
npx prisma migrate deploy --schema prisma/schema.prisma
```

`migrate deploy` only applies pending migration files; it cannot create new migrations. Use `migrate dev --create-only` locally first, then `migrate deploy` in CI/staging.

### Migration Drift Detection

> **Warning**: `_prisma_migrations` table can mark a migration as "applied" (`finished_at` set, `rolled_back_at = null`) while the actual table is **missing** from the database. This happens when someone manually drops a table or manually inserts a migration record without running the SQL.

`prisma migrate status` says "Database schema is up to date!" based solely on `_prisma_migrations` records — it does NOT verify that the tables actually exist. To detect drift:

```js
// Verification script — query the table directly
const count = await prisma.someModel.count();
// If this throws "The table does not exist" but migrate status says "up to date",
// you have drift. Fix by running the CREATE TABLE SQL from the migration file.
```

**Fix for drift**: Run the `CREATE TABLE` / `CREATE INDEX` SQL from the migration file directly against the DB (use `prisma.$executeRawUnsafe` — one statement per call, since Prisma prepared statements reject multi-command SQL). Do NOT delete the `_prisma_migrations` record — that would cause `migrate deploy` to re-run the entire migration (including `ALTER TABLE` statements that would fail on existing columns).

---

## Prisma Client Synchronization

### When to Regenerate the Client

The Prisma client is TypeScript code generated from `schema.prisma`. It must be regenerated whenever the schema changes — otherwise the client won't have new models, causing `TypeError: Cannot read properties of undefined (reading 'findMany')` at runtime.

**Triggers requiring `pnpm db:generate`:**

| Trigger | Why |
|---------|-----|
| Added/removed a model in `schema.prisma` | Client must include the new model property |
| Renamed a model or field | Client property name changes |
| Changed a field type or enum | TypeScript types in client must match |
| **Merged a branch that touched `schema.prisma`** | The merge brings schema changes, but the client is NOT auto-regenerated |
| Pulled latest from a branch with migration files | Same — migrations exist but client is stale |

**The most common mistake**: merging a feature branch that adds a Prisma model, then starting the dev server without running `pnpm db:generate`. The running process has a stale client and throws `undefined.findMany` errors.

### Dev Server Does Not Watch `node_modules`

The API dev script is:

```json
"dev": "cross-env TS_NODE_TRANSPILE_ONLY=1 node --watch --watch-path src --loader ts-node/esm src/main.ts"
```

`--watch-path src` only watches the `src/` directory. The regenerated Prisma client lives in `node_modules/`, which is NOT watched. After running `pnpm db:generate`, you must **manually restart the dev server** for the new client to take effect.

### Client Location & Freshness Verification

The generated client is NOT at `packages/db/node_modules/.prisma/client` (that path does not exist in this repo). The actual location is:

```
node_modules/.pnpm/@prisma+client@6.0.1_prisma@6.0.1/node_modules/.prisma/client/
```

To verify the client has a specific model (e.g., after `db:generate`):

```bash
rg -c 'personalSkillConfig' \
  node_modules/.pnpm/@prisma+client@6.0.1_prisma@6.0.1/node_modules/.prisma/client/index.d.ts
# 0 = client is STALE (model missing) — run pnpm db:generate
# >0 = client is fresh
```

### Connection to Schema-Version Pinning

`packages/db/src/index.ts` pins `PRISMA_SCHEMA_VERSION` (see Singleton section above). After regenerating the client, bump this version string so that hot-reloaded code creates a fresh `PrismaClient` instance instead of reusing a cached one from the old client.

---

## Deployment & Production Migration Flow

### Docker Build

The `apps/api/Dockerfile` runs `pnpm db:generate` during the build stage (line 46):

```dockerfile
RUN pnpm --filter @insightweaver/db db:generate
```

This means the Docker image always contains a Prisma client matching the schema at build time. **Stale client errors (error #2 pattern) cannot occur in Docker deployments.**

### Docker Entrypoint Disables Migrations

`apps/api/docker-entrypoint.sh` explicitly skips migrations (line 13):

```sh
echo "entrypoint: skipping prisma migrate deploy (disabled in entrypoint)"
```

**Migrations are NOT applied automatically during container startup.** They must be run manually or via a dedicated migration script before deploying new code.

### Environment Separation

| Environment | Database | Migration Method |
|-------------|----------|-----------------|
| Dev (local) | `47.96.103.101:5432/insight_weaver` (`prod_admin`) | Manual `prisma migrate deploy` or `pnpm db:migrate` |
| Production | Separate RDS instance | Dedicated migration script (external) |

The dev database at `47.96.103.101` is a shared dev/staging server — NOT production. Production has its own database and a dedicated migration script that runs before deployment.

**Pre-deployment checklist:**
1. Ensure all new migrations are committed and pushed
2. Run `prisma migrate status` against the production DB to verify pending migrations
3. Apply migrations via the dedicated production migration script
4. Build and deploy the Docker image (which runs `db:generate` internally)

---

## Adding a New Model

1. Add the model to `packages/db/prisma/schema.prisma` following naming conventions above.
2. Include `createdAt`, `updatedAt`, `isDeleted` fields.
3. Map the table name with `@@map("snake_case_name")`.
4. Run `prisma migrate dev --create-only --name add_<model_name>`.
5. Run `pnpm db:generate` to regenerate the client with the new model.
6. Bump `PRISMA_SCHEMA_VERSION` in `packages/db/src/index.ts`.
7. Re-export any new types needed by API via `export type *` (already in place).

---

## Billing ↔ Entitlement 关联约定

### 关联键：`billing_orders.id`（UUID）

`entitlement_batches` 通过两个字段关联 `billing_orders`：

| 字段 | 关联目标 | 用途 |
|---|---|---|
| `sourceRefId` | `billing_orders.id`（UUID） | **主要关联键**，通用设计（所有来源类型都用） |
| `orderId` | `billing_orders.id`（UUID） | **冗余副本**，仅 `billing_order` 来源时有值 |

### ⚠️ 不要用 `orderNo` 做关联

`billing_orders.orderNo`（如 `BILL20260805120133826131`）是**展示编号**，不参与 entitlement 关联。`entitlement_batches.sourceRefId` 存的是 UUID，不是 orderNo。

```sql
-- ❌ 错误：orderNo 不匹配 sourceRefId
SELECT eb.* FROM entitlement_batches eb
WHERE eb."sourceRefId" = 'BILL20260805120133826131';  -- 永远查不到

-- ✅ 正确：通过 orderNo 找到 id，再用 id 关联
SELECT eb.* FROM entitlement_batches eb
JOIN billing_orders o ON eb."sourceRefId" = o.id
WHERE o."orderNo" = 'BILL20260805120133826131';
```

### sourceRefType 枚举

| sourceRefType | sourceRefId 含义 |
|---|---|
| `billing_order` | `billing_orders.id` |
| `admin_grant` | 管理员手动发放 ID（无订单） |
| `batch_allocation` | B 端 batch 分配 ID |

### 查询模板：按订单号查权益

```sql
-- 按订单号查发放的权益批次
SELECT eb."entitlementType", eb."grantedAmount", eb."remainingAmount",
       eb."unit", eb."status",
       eb."validFrom" AT TIME ZONE 'UTC' + INTERVAL '8 hours' AS "validFrom(+8)",
       eb."validUntil" AT TIME ZONE 'UTC' + INTERVAL '8 hours' AS "validUntil(+8)"
FROM entitlement_batches eb
JOIN billing_orders o ON eb."sourceRefId" = o.id
WHERE o."orderNo" = '<ORDER_NO>';
```

详见 [billing-payment-flow.md](../api/billing-payment-flow.md) §3.5。
8. Restart the API dev server (it does not watch `node_modules`).

---

## Task Board Tables (2026-09-08, feature-20260908-task-board)

- `task_boards`：每企业一块默认看板，`enterpriseId @unique`；无种子数据（首访问懒初始化）。
- `task_column_configs`：7 固定工作流列（planning/todo/doing/review/done/canceled/discarded），`@@unique([boardId, columnKey])`；`name`/`hidden` 可改（重命名/隐藏为看板级共享配置），`sortOrder` 固定 1-7 不可改。
- `task_cards`：`@@unique([boardId, seq])`（seq 全量 max+1 含软删行 → TASK-N 永不复用）；`position Int` 列内排序（间隔 1024，间隙耗尽整列重排）；`tags`/`attachments` 为 Json；软删 `isDeleted` 行保留占 seq。
- 外键：两子表 `boardId` → `task_boards.id` ON DELETE CASCADE；`assigneeUserId` 为软引用（服务层校验企业 active 成员，无 FK）。
- 迁移：`20260907170340_task_board`（shadow 库对 `20260904170000_align_ai_memory_schema` 有存量重放漂移——新迁移需用 `prisma migrate diff --from-schema-datamodel` 生成后 `db execute` + `migrate resolve --applied` 手工落地，勿跑 `migrate dev`）。

## Core Table Reference for Analytics Features

> Verified against production database on 2026-08-11 during the Token Analytics module integration.
> **Rule: any analytics/reporting feature MUST read the real schema (schema.prisma / information_schema) BEFORE writing code. Do NOT assume table shapes.**

### Token consumption — `zclaw_enterprise_token_usage_settlements` is the ONLY source of truth

```prisma
model TokenUsageSettlement {
  id           String   @id              // zclaw-token-settle-{enterpriseId}-{userId}-{messageId}
  enterpriseId String
  userId       String                    // references users.id (NOT enterprise_memberships.id)
  messageId    String?                   // format: msg_run_xxx
  tokens       BigInt                    // total tokens for that run
  createdAt    DateTime
  quotaMode    String?                   // 'batch' | null
}
```

- **This table is the single source for token consumption** — `zclaw_messages` has NO token columns.
- `messageId` (prefix `msg_run_`) does NOT match `zclaw_messages.id` (prefix `conv_...:tool:...`). **Do NOT attempt to join them** for analytics.
- `zclaw_messages.rawPayload` is tool-call activity (exec/write output), not LLM metadata. No model/skill info there.
- Volume: ~35K records / ~7.4B tokens (as of 2026-08-11), ~1-2B tokens per active day.

### User identity — display name lives on the membership, not the user

- `users` table has **no nickname/name column** (only id/status/role/avatarOssKey/passwordHash/locale).
- Display name = `enterprise_memberships.realName` (nullable → fallback '未知').
- Phone lives in `user_identities.providerUserId` (e.g. `+8618014913087`), `provider = 'phone'`.

### Department — free-text, not a foreign key

- `enterprise_memberships.department` is a **text field** (e.g. '0801B班', '技术支持'), NOT a FK.
- `enterprise_departments` is a flat list (id/enterpriseId/name/sortOrder) — **no parentId/level**.
- `enterprise_department_groups` exists but is largely unused (empty in production).
- **Filter by department name string**, not by joining department tables.

### Naming reality check

| Layer | Reality |
|---|---|
| Column names | **camelCase** (`createdAt`, `isDeleted`) — no `@map` needed on fields |
| Table names | snake_case via `@@map()` (`zclaw_enterprise_token_usage_settlements`) |
| bigint columns | Prisma `BigInt` — must `Number()` convert before JSON/cache serialization (JSON.stringify throws on BigInt) |

### Analytics query template (verified working)

```sql
-- Per-member token totals for an enterprise
SELECT s."userId", COALESCE(em."realName", '未知') AS name, em.department,
       SUM(s.tokens) AS tokens, COUNT(*) AS records
FROM "zclaw_enterprise_token_usage_settlements" s
JOIN "enterprise_memberships" em
  ON em."userId" = s."userId" AND em."enterpriseId" = s."enterpriseId"
WHERE s."enterpriseId" = :enterpriseId
  AND em."isDeleted" = false
  AND s."createdAt" >= :start AND s."createdAt" <= :end
GROUP BY s."userId", em."realName", em.department
ORDER BY tokens DESC;
```

### Migration of this section's history

This section was added after the Token Analytics demo (ZCodeProject/token-analytics) hit a full schema-mismatch rewrite:
an initial schema assumed snake_case columns, token fields on `zclaw_messages`, and a department FK — all three were wrong.
**The cost: all service-layer queries rewritten. The lesson: read the schema first, write code second.**
