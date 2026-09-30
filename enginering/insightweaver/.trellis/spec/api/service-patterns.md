# Service Patterns

## Overview

Services contain all business logic. They are injected with Prisma via string token and orchestrate database operations, cross-module calls, and error handling. The largest service in the codebase is `apps/api/src/billing/entitlement.service.ts` at 6511 lines.

## Constructor Injection Pattern

Every service follows this constructor pattern:

```typescript
// apps/api/src/billing/billing-plan.service.ts
@Injectable()
export class BillingPlanService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    @Optional() private readonly otherService?: OtherService,
  ) {}
}
```

Key points:
- `@Inject('PrismaClient')` — string token, not class token
- `private readonly` — all injected dependencies are immutable
- `@Optional()` — used for cross-module deps that may not be available

## Transaction Pattern

All multi-step writes use Prisma's interactive transaction. The transaction client is typed as `Prisma.TransactionClient` and aliased for readability.

### Type Alias

```typescript
type EntitlementTx = Prisma.TransactionClient;
```

### Standard Transaction Block

```typescript
// apps/api/src/billing/entitlement.service.ts
async deductCredits(userId: string, amount: bigint) {
  return this.prisma.$transaction(async (tx: EntitlementTx) => {
    // Step 1: Read with lock
    const entitlement = await tx.entitlement.findFirst({
      where: { userId, status: 'ACTIVE' },
    });

    if (!entitlement || entitlement.balance < amount) {
      throw new BusinessException(
        ErrorCode.INSUFFICIENT_CREDITS,
        '余额不足',
      );
    }

    // Step 2: Atomic deduction
    await tx.entitlement.updateMany({
      where: {
        id: entitlement.id,
        balance: { gte: amount },  // atomic guard
      },
      data: {
        balance: { decrement: amount },
      },
    });

    // Step 3: Record the transaction
    await tx.creditTransaction.create({
      data: { userId, amount: -amount, type: 'DEDUCTION' },
    });

    return { success: true };
  });
}
```

### Why the tx Alias

The `EntitlementTx = Prisma.TransactionClient` alias exists because:
1. It improves readability in deeply nested transaction blocks
2. It allows module-specific transaction types when a module needs extended client methods
3. It makes the transaction boundary explicit in method signatures

## Atomic Updates

The codebase prefers `updateMany` with `gte` (greater-than-or-equal) conditions over read-then-update for atomicity:

### Preferred: Atomic updateMany

```typescript
// Atomic — no race condition
const result = await tx.entitlement.updateMany({
  where: {
    id: entitlementId,
    balance: { gte: deductionAmount },
  },
  data: {
    balance: { decrement: deductionAmount },
  },
});

if (result.count === 0) {
  throw new BusinessException(
    ErrorCode.INSUFFICIENT_CREDITS,
    '余额不足',
  );
}
```

### Fallback: Read-then-Update

Used when test mocking requires simpler query shapes:

```typescript
// Fallback pattern — used when mocking is a priority
const entitlement = await tx.entitlement.findUnique({
  where: { id: entitlementId },
});

if (!entitlement || entitlement.balance < deductionAmount) {
  throw new BusinessException(
    ErrorCode.INSUFFICIENT_CREDITS,
    '余额不足',
  );
}

await tx.entitlement.update({
  where: { id: entitlementId },
  data: { balance: entitlement.balance - deductionAmount },
});
```

**Trade-off:** The read-then-update pattern is susceptible to race conditions without row locking. Use `SELECT ... FOR UPDATE` (see raw SQL below) when using this pattern.

## Raw SQL for Row Locking

When atomic `updateMany` is insufficient (e.g., complex multi-table locking), use raw SQL:

```typescript
// apps/api/src/billing/entitlement.service.ts
const [entitlement] = await tx.$queryRaw`
  SELECT * FROM entitlement
  WHERE user_id = ${userId}
    AND status = 'ACTIVE'
  FOR UPDATE
`;
```

Key points:
- Use tagged template literals (`$queryRaw` backtick syntax) — Prisma parameterizes values automatically
- `FOR UPDATE` acquires an exclusive row lock within the transaction
- Returns raw database rows (not Prisma model instances)
- Cast results as needed: `(rows as Entitlement[])[0]`

## BigInt for Monetary and Quantity Values

All monetary amounts, token counts, and byte quantities use `BigInt`:

```typescript
// Literal syntax
const FREE_TIER_TOKENS = 100000n;
const ZERO = 0n;

// Arithmetic
const remaining = entitlement.balance - deductionAmount;

// Prisma schema mapping
// BigInt fields in schema.prisma -> bigint in TypeScript
await tx.entitlement.update({
  where: { id },
  data: { tokenBalance: { decrement: 1000n } },
});

// Comparison
if (balance >= amount) { ... }
if (balance === 0n) { ... }
```

**Never use `number` for monetary/token/byte values.** BigInt avoids floating-point precision issues and supports values beyond `Number.MAX_SAFE_INTEGER`.

## Idempotency Implementation

Services implement idempotency via unique constraints and duplicate-key handling:

```typescript
async createPlan(dto: CreateBillingPlanDto, idempotencyKey?: string) {
  try {
    return await this.prisma.billingPlan.create({
      data: {
        ...dto,
        idempotencyKey,  // unique constraint in schema
      },
    });
  } catch (error) {
    if (
      error instanceof PrismaClientKnownRequestError &&
      error.code === 'P2002'
    ) {
      // Duplicate idempotency key — return existing record
      const existing = await this.prisma.billingPlan.findFirst({
        where: { idempotencyKey },
      });
      return existing;
    }
    throw error;
  }
}
```

## Optional Service Usage

When a service has an `@Optional()` dependency, guard its usage:

```typescript
@Injectable()
export class BillingService {
  constructor(
    @Inject('PrismaClient') private readonly prisma: PrismaClient,
    @Optional() private readonly wechatPayService?: WechatPayService,
  ) {}

  async processPayment(orderId: string) {
    const order = await this.prisma.order.findUnique({ where: { id: orderId } });

    if (order.paymentMethod === 'WECHAT' && this.wechatPayService) {
      return this.wechatPayService.createPayment(order);
    }

    // Fallback for non-WeChat payments
    return this.processDirectPayment(order);
  }
}
```

## Error Throwing Pattern

Services throw `BusinessException` (custom exception) with error codes from `apps/api/src/common/constants/error-codes.ts`:

```typescript
import { ErrorCode } from '../common/constants/error-codes';

// Insufficient credits
throw new BusinessException(
  ErrorCode.INSUFFICIENT_CREDITS,
  '余额不足',
);

// Not found
throw new BusinessException(
  ErrorCode.INVALID_ARGUMENT,
  '套餐不存在',
);

// Forbidden
throw new BusinessException(
  ErrorCode.FORBIDDEN,
  '无权访问此资源',
);
```

The `AllExceptionsFilter` catches these and normalizes them to the `{ code, message, data }` response envelope.

## Service Method Naming Conventions

| Operation | Prefix | Example |
|-----------|--------|---------|
| Read single | `get` / `find` | `getPlan(id)` |
| Read list | `list` | `listPlans(filters)` |
| Create | `create` | `createPlan(dto)` |
| Update | `update` | `updatePlan(id, dto)` |
| Delete | `delete` / `remove` | `deletePlan(id)` |
| Complex action | verb | `deductCredits(userId, amount)` |
| Check/validate | `check` / `validate` | `checkEntitlement(userId)` |

## Monthly Plan Gate Check (PRD N3)

### Context

B2B enterprise users must have an active monthly plan anchor to use token/storage entitlements. The gate is enforced via `dependencyPolicy: { requiresActiveMonthlyPlan: true }` on token/storage batches.

### Gate Check Flow

```
consume/freeze entitlements
  → isUsableEntitlementBatch(batch, now, hasActiveMonthlyPlan, hasActiveBatchWindow)
    → if dependency.requiresActiveMonthlyPlan && !hasActiveMonthlyPlan → return false (blocked)
```

### `isBatchBackedByActiveMonthlyAnchor` Logic

This method filters batches that are backed by an active monthly grant group. **Only pool allocation batches (`enterprise_allocation`) need this check.** Monthly plan anchors themselves (`b2b_enterprise_plan`, `b2b_monthly_seat_plan`) and consumer batches always pass.

```typescript
private isBatchBackedByActiveMonthlyAnchor(
  batch: Pick<EntitlementBatch, "sourceType" | "metadata">,
  activeMonthlyGrantGroupIds: Set<string>,
) {
  if (!this.isMonthlyEntitlementSource(batch.sourceType)) return true;
  // Only pool allocation batches need to be backed by an active monthly anchor
  if (batch.sourceType !== "enterprise_allocation") return true;
  if (activeMonthlyGrantGroupIds.size === 0) return false;
  const grantGroupId = this.batchGrantGroupId(batch);
  return Boolean(grantGroupId && activeMonthlyGrantGroupIds.has(grantGroupId));
}
```

### Common Mistake: Returning `true` When No Active Monthly Plans

```typescript
// WRONG: Returns true when no active monthly plans, allowing all batches through
if (activeMonthlyGrantGroupIds.size === 0) return true;

// CORRECT: Returns false — no active anchor means pool allocations are not usable
if (activeMonthlyGrantGroupIds.size === 0) return false;
```

**Why**: When `activeMonthlyGrantGroupIds` is empty, it means the user has no active monthly plan. Pool allocation batches should be blocked, not allowed through.

### `hasActiveMonthlyPlan` Query

```typescript
// Queries status: { in: ["active", "scheduled"] } — frozen is NOT included
const candidates = await tx.entitlementBatch.findMany({
  where: {
    enterpriseId, userId,
    subjectType: "enterprise_user",
    entitlementType: "monthly_plan",
    status: { in: ["active", "scheduled"] },
    isDeleted: false,
  },
});
```

**Key**: `frozen` status is excluded from the query. When a monthly plan anchor is frozen, `hasActiveMonthlyPlan` returns `false`, and the checkpoint gate blocks token/storage consumption.

### Freezing Monthly Plan Anchor

```typescript
// POST /api/admin/billing/entitlements/freeze-monthly-plan
// Only freezes the monthly_plan anchor itself — does NOT cascade to token/storage
// The checkpoint gate (hasActiveMonthlyPlan → false) automatically blocks consumption
```

**Do NOT cascade freeze**: Freezing the monthly plan anchor should NOT freeze token/storage batches. The checkpoint gate handles the blocking. Cascading freeze would be redundant and could cause issues when unfreezing.

## Unlimited Quota Mode: Skip-in-Caller Pattern

### Context

When `ZclawEnterpriseConversationQuotaConfig.quotaMode === "unlimited"`, ALL quota enforcement for that enterprise is disabled — no account validity, token limit, storage capacity, or conversation count restrictions apply, and the frontend hides all quota UI.

### Convention: Skip in the orchestrator, not in the leaf calculator

The unlimited bypass is implemented by **skipping the quota-enforcement calls in the orchestrator** (`getWorkspaceUsageSummary` in `zclaw.service.ts`, `resolveConsumableBatchesInternal` in `entitlement.service.ts`), NOT by modifying the leaf domain function (`computeAccountValidity`) to return null.

**Why**: `computeAccountValidity` is a pure domain calculation (validity window from batches). `quotaMode` is a policy concern. Coupling policy into the calculator would force every caller (display, enforcement, billing) to inherit the bypass and make the calculator's return ambiguous (null could mean "no batches" OR "unlimited"). Keeping the calculator pure and bypassing in the caller makes each call site's intent explicit.

```typescript
// In getWorkspaceUsageSummary and resolveConsumableBatchesInternal:
const quotaConfig = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
  where: { enterpriseId },
  select: { quotaMode: true },
});
if (quotaConfig?.quotaMode !== "unlimited") {
  // run computeAccountValidity / checkTokenQuotaStatus / storage gate
}
// else: skip — no validity constraint, accountValidityExpired stays false
```

### Storage Capacity

`getEnterpriseWorkspaceQuotaConfig` returns `quotaBytes: BigInt(Number.MAX_SAFE_INTEGER)` + `quotaSource: "unlimited"` early, so `isOverLimit` is always false for unlimited enterprises.

### API Contract

`getWorkspaceUsageSummary` response includes `quotaMode: string | null`. Frontend components (`SuperLobsterPage`, `ZclawShell`, `ZclawWorkspaceSidebar`) conditionally render quota UI based on `quotaMode === "unlimited"`.

### Wrong vs Correct

```typescript
// WRONG: couple policy into the pure calculator
async computeAccountValidity(enterpriseId, userId) {
  const cfg = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique(...);
  if (cfg?.quotaMode === "unlimited") return null; // mixes policy into domain calc
  // ...existing logic
}

// CORRECT: bypass in the orchestrator; keep the calculator pure
const quotaMode = await this.fetchQuotaMode(enterpriseId);
if (quotaMode !== "unlimited") {
  accountValidity = await this.enterpriseTokenBatchQuotaService.computeAccountValidity(...);
}
```

## Display Contract: Account Validity for Batch and Token Modes

**Scope/Trigger**: `EntitlementService.getSummary` (feeds `ZclawShell`) returns `accountValidity` for **batch** and **token** modes. Conversation/unlimited return `null`.

**Why**: batch mode derives validity from batch windows; token mode derives validity from `windowStart` in `zclawEnterpriseConversationQuotaUsage`. Conversation/unlimited have no quota expiry concept.

**Backend gate** (`getSummary`):
```typescript
if (quotaConfig?.quotaMode === "batch") {
  accountValidity = await this.enterpriseTokenBatchQuotaService.computeAccountValidity(...);
}
// Token mode: backend returns null; frontend computes from conversationQuotaSummary.windowStart
```

**Frontend gate** (`ZclawShell.tsx:resolveValidityDates` and `resolveAccountValidityDisplay`):
```typescript
// Web: account-validity-display.ts
const isBatch = input.quotaMode === "batch";
const isToken = input.quotaMode === "token";
const hasAccountValidity = (isBatch || isToken) && Boolean(input.accountValidity);

// ZclawShell.tsx: token mode accountValidity from legacyTokenQuota.windowStart
if (quotaMode === 'token' && legacyTokenQuota?.windowStart) {
  // Compute month-end validity from windowStart (timezone-safe)
}
```

**Contract**: `accountValidity` non-null for:
- `quotaMode === "batch"` AND resolvable window exists
- `quotaMode === "token"` AND `legacyTokenQuota.windowStart` exists
- Conversation/unlimited ⇒ `null`

---

## Billing Order Grant: Batch Split Pattern

C 端支付订单（`billing_orders`）发放时，按 `planType` 拆分成不同数量的 `entitlement_batch` 记录。**一个订单可能对应多条 batch**。

### Pattern

```typescript
// apps/api/src/billing/entitlement.service.ts → grantPaidOrderSnapshot
// 按 planType 分发到不同的 grant 函数，每个函数在单个事务内创建 1~N 条 batch

async grantPaidOrderSnapshot(actorUserId, order, idempotencyKey) {
  return this.prisma.$transaction(async (tx) => {
    if (plan.planType === "consumer_monthly_plan") {
      // 月包：anchor + N 条规格 batch（≥3 条：monthly_plan + token + storage）
      return { batches: await this.grantConsumerMonthlyPlan(tx, ctx, adjustedValidFrom) };
    }
    if (plan.planType === "consumer_token_topup") {
      // Topup：仅 1 条 batch
      return { batches: await this.grantConsumerTopup(tx, ctx, validFrom, "token") };
    }
    // ...其他 planType
  });
}
```

### 月包拆分规则（`createMonthlyGrantGroup`）

```
1. 创建 monthly_plan anchor batch（1 plan_period，账号有效期）
2. 调用 planEntitlementSpecs 按套餐配置生成 token/storage/member/feature batch
3. 所有 batch 共享同一 grantGroupId、sourceRefId、validFrom/validUntil
```

Plus套餐实测产出 3 条：
- `monthly_plan`（1 plan_period）
- `token`（30,000,000 billing_token）
- `storage`（10,737,418,240 byte = 10 GB）

### 查询时注意

```sql
-- ⚠️ 一个订单对应多条 batch，COUNT 时要 GROUP BY
SELECT o."orderNo", COUNT(eb.id) AS batch_count
FROM billing_orders o
JOIN entitlement_batches eb ON eb."orderId" = o.id
WHERE o."paymentStatus" = 'SUCCESS'
GROUP BY o."orderNo";

-- 月包订单 batch_count ≥ 3；topup 订单 batch_count = 1
```

详见 [billing-payment-flow.md](./billing-payment-flow.md) §3.3。

## Local Snapshot Merge: Position Matching over Content Matching

**Problem**: 用户消息附件（`files`）在实时发送时存入本地 DB 快照（`rawPayload.files`，UUID id），但远程 agent 历史不返回 inline 内容 → 刷新时 `files` 丢失。

**Solution**: `mergeMessagesWithLocalToolSnapshots` 合并策略：

1. **按位置匹配**（非内容）：本地第 N 个有 `files` 的用户消息 → 远程第 N 个用户消息
2. 内容匹配不可靠——agent 可能富化用户消息（时间戳前缀 `[Wed ... GMT+8]`、PromptGuard 块等），匹配失败率高

```typescript
// Correct: position-based
const localUserFiles = localMessages
  .filter(m => m.role === "user" && m.files?.length)
  .map(m => m.files);
let idx = 0;
return remoteMessages.map(m => {
  if (m.role === "user") {
    const files = localUserFiles[idx++];
    if (files?.length && !m.files?.length) return { ...m, files };
  }
  return m;
});

// Wrong: 按内容匹配 —— agent 富化后不一致
const contentKey = normalizeContent(m.content);
```

**Call sites**:
- `getSessionDetail`: `mergeRemoteDetailWithLocalToolSnapshots` 合并 local UUID files → sync trusted
- `getSessionMessagesPage`: 同上

**Related**: 
- `pruneUntrustedLocalMessages` 在 merge+sync 后删除 UUID 快照
- 前端 `mergeConversationMessagesWithDraft` 保留 draft 的 `files`
- 前端 `shouldMergeDraftOnRefresh` 即使 API 已完成，若 draft 有附件仍触发合并

### Gotcha: 流式完成时草稿被清空

> **Warning**: 前端 `clearConversationDraft` 在流式生成完成时清空 sessionStorage 草稿（唯一含 `files` 的副本）。
>
> 因此**刷新一定依赖后端 merge 路径**——如果 merge 在此前未执行（如首次刷新），UUID 快照必须还在（`isDeleted=false`），否则附件永久丢失。prune 只在 refresh 的 remote 路径中、merge + sync 完成后才执行，保证时序安全。

### 约束：getSessionDetail 同步+prune 写库后必须重查本地（2026-08-10 教训）

**Files**: `apps/api/src/zclaw/zclaw.service.ts` — `getSessionDetail`

**问题**：`getSessionDetail` 远程同步路径中，`syncRemoteSessionDetail`（upsert 消息）+ `pruneUntrustedLocalMessages`（软删 untrusted）**都写库**。优化时曾直接返回内存中的 `mergedRemoteDetail`（merge 产物），导致：

1. 返回内容与 DB 实际状态不一致——已被软删的 untrusted 消息仍出现在响应中
2. 前端后续轮询/刷新读到的 DB 状态与首屏不一致，消息"闪现/消失"

**规则**：任何写库（sync/prune/finalize）之后，**必须重查 `getLocalSessionDetail`** 再返回，不得直接返回内存合并对象：

```typescript
// Correct: sync + prune 写库后重查
await this.syncRemoteSessionDetail(userId, mergedRemoteDetail);
await this.syncOpenClawSessionBinding(userId, mergedRemoteDetail);
await this.pruneUntrustedLocalMessages(userId, sessionId);
const syncedDetail =
  (await this.getLocalSessionDetail(userId, sessionId)) ?? remoteDetail;
return { ...syncedDetail, activeGeneration: false };

// Wrong: 直接返回内存合并对象（与 DB 状态不一致）
await this.pruneUntrustedLocalMessages(userId, sessionId);
return { ...mergedRemoteDetail, activeGeneration: false };
```

**例外**：写库**之前**的重复查询可以删除（同一参数、无中间写入，结果必然相同）——如 `isActiveLocalGeneration` 分支前、trusted 检查前的重复 `getLocalSessionDetail`。

### 约束：isActiveLocalGeneration finalize 后必须重查 localDetail（2026-08-10 教训）

**问题**：`localDetail` 存在 streaming 消息或 `status === "generating"` 时，`isActiveLocalGeneration` 会调用 `finalizeStaleLocalGenerationMessages` **写库**（更新消息状态/内容）后返回 `false`。此时 `localDetail` 仍是写库前的旧快照（streaming 状态），直接 fall-through 到 trusted 检查会返回过期数据。

**规则**：streaming/generating 状态下，`isActiveLocalGeneration` 返回 `false` 后必须重查一次：

```typescript
if (
  localDetail &&
  (localDetail.messages.some((m) => m.status === "streaming") ||
    localDetail.status === "generating")
) {
  if (await this.isActiveLocalGeneration(userId, sessionId, localDetail)) {
    return { ...localDetail, activeGeneration: true };
  }
  // finalize 可能已写库，重查获取最新状态
  const refreshed = await this.getLocalSessionDetail(userId, sessionId);
  if (refreshed) localDetail = refreshed;
}
```

**判断标准**：`isActiveLocalGeneration` 内部 `hasStaleStreaming || status === "generating"` 时才会 finalize 写库——调用方用同样条件判断是否需要重查，避免无谓查询。

**Tests**: `zclaw.service.test.ts` — `getSessionDetail re-queries local after remote sync + prune`（findFirst ≥3 + updateMany ≥1）、`getSessionDetail finalizes stale streaming messages when no active memory run exists`（finalize 后返回 false 且清理被调用）。

### 约束：getSessionMessagesPage 本地快速路径必须 DB 分页（2026-08-11 教训）

**Files**: `apps/api/src/zclaw/zclaw.service.ts` — `getSessionMessagesPage`

**问题**：`getSessionMessagesPage` 的本地快速路径（无 cursor 首屏、最近消息 trusted）曾通过 `getLocalSessionDetail` 拉取全量消息（104 条含大 rawPayload 约 1.6s），再内存 slice(50)。首屏耗时 6s+，实际只需要 50 条。

**规则**：本地快速路径**禁止**走 `getLocalSessionDetail`（全量、无 limit），必须独立 DB 分页查询：

```typescript
// Correct: DB 分页 + 轻量预判
if (!query.cursor) {
  // 1. 轻量预判：仅查最后一条消息 id（select: { id: true }），判断 trusted
  const lastMessage = await this.prisma.zclawMessage.findFirst({
    where: { sessionId, isDeleted: false },
    orderBy: { createdAt: "desc" },
    select: { id: true },
  });
  if (lastMessage && this.isTrustedLocalSnapshotMessageId(sessionId, lastMessage.id)) {
    // 2. DB 分页：按 createdAt desc + take limit，代码层 reverse 恢复 asc
    const rows = await this.prisma.zclawMessage.findMany({
      where: { sessionId, isDeleted: false },
      orderBy: { createdAt: "desc" },
      take: limit,
      select: { id: true, role: true, content: true, status: true, rawPayload: true, createdAt: true },
    });
    const messages = rows.reverse().map(row => /* 映射 + extractSnapshotFiles + dedupe */ ({...}));
    // 3. count 查询计算 hasMore（不能依赖 retrieved < limit，去重后可能少于 limit）
    const totalCount = await this.prisma.zclawMessage.count({ where: { sessionId, isDeleted: false } });
    return { messages, nextCursor: totalCount > limit ? `local:${limit}` : null, ... };
  }
}

// Wrong: 快速路径走全量拉取（1.6s + dedupe + toolActivity，仅用 50 条）
const localDetail = await this.getLocalSessionDetail(userId, sessionId);
return localDetail.messages.slice(-50).map(...);
```

**关键约束**：
1. **desc + take**：保证取到最新的 N 条（结合 reverse 还原 asc 顺序）
2. **count 独立计算 hasMore**：不能依赖 `retrieved.length < limit`——去重后可能少于 limit 但仍有更多消息
3. **轻量预判**：先 `findFirst(select: { id })` 判断 trusted，命中才查询——避免"先查全量再判断"的双重开销
4. **dedupe 仅作用于返回集合**：DB 分页只取部分消息，同内容副本若跨页可能重复出现——接受此权衡（已同步会话极少副本）
5. **不可用 `isTrustedLocalSessionDetail`** 判定——历史遗留的 assistant untrusted 副本（`dedupeUserMessagesBySnapshot` 仅处理 user）会让该判定永远 false

**Tests**: `zclaw.service.test.ts` — `getSessionMessagesPage returns local quickly when recent message is trusted`（historyCalls=0、source=local、messages.length=4）；`getSessionMessagesPage still calls remote when recent message is NOT trusted`（historyCalls=1、source=remote）。

**Tests**: `account-validity-display.test.ts` — `resolveAccountValidityDisplay` `showBlock` true for token+accountValidity, false for token+null. `ZclawShell.accountValidity.test.tsx` — token mode renders validity block when accountValidity exists, hides when null.

### 约束：getSessionDetail 对外响应瘦身，内部全量保留（2026-08-14 第三波）

**Files**: `apps/api/src/zclaw/zclaw.service.ts` — `getSessionDetail` / `toSlimSessionDetail` / `countStreamingMessages`

**问题**：对外 detail 响应携带全量 `messages`（生产实测 5.9MB/4.5s），而前端只消费 `detailStatus`/`activeGeneration` 等元信息（消息走分页接口）。

**规则**：
1. **对外响应不含 `messages` 数组**，以 `messageCount`（`zclawMessage.count`）+ 显式 `detailStatus` 替代。所有 return 路径（activeGeneration/trusted/远程同步/recover_empty×2/history 同步/recover_failed）统一经 `toSlimSessionDetail` 收敛：

```typescript
// Correct: 对外裁剪，内部全量
private async toSlimSessionDetail<T extends { sessionId: string; messages: unknown[] }>(
  detail: T,
): Promise<Omit<T, "messages"> & { messageCount: number }> {
  const messageCount = await this.prisma.zclawMessage.count({
    where: { sessionId: detail.sessionId, isDeleted: false },
  });
  const { messages: _ignored, ...rest } = detail;
  return { ...rest, messageCount };
}

// Wrong: 直接 return localDetail（5.9MB messages 全量外泄）
return { ...localDetail, activeGeneration: false };
```

2. **内部 `getLocalSessionDetail` 签名与返回不变**——sync/prune/merge 等内部逻辑依赖全量 messages，只裁对外响应。
3. **streaming 判断改 DB count**：`localDetail.messages.some(streaming)` → `countStreamingMessages`（`count({ where: { sessionId, isDeleted: false, status: "streaming" } })`）。写库后重查/finalize 后重查两条既有约束保持不动。
4. **前端消费方迁移**：detail.messages 兜底改分页接口重试（`fetchSessionMessagesWithRetry` ≤2 次），重试耗尽必须给用户可见错误态（error 系统消息 + errorToast），禁止静默空白。字段变更 breaking：前后端同 PR 部署。

**Tests**: `zclaw.service.test.ts` — `getSessionDetail returns slim response without messages`（`!("messages" in detail)` + messageCount + count 调用次数）、`getSessionDetail returns messageCount=0 and recover_empty for empty session`、`getSessionDetail detects stale streaming via DB count query`（streaming count 调用 + finalize 执行）。

### 流式接口三层超时：SSE 挂起快速失败（2026-08-15 bugfix，2026-08-17 CR 补完，2026-08-18 工具预算修复）

**Files**: `apps/api/src/zclaw/zclaw-km-agent.client.ts` — `streamConversationMessage`

**问题**：KM Agent 挂起分三阶段，每阶段都需要不同超时保护：

1. **连接/TTFB 挂起**：KM Agent 挂起时 fetch 永不 resolve → 请求无限挂起（前端「一直进行中」）
2. **首事件挂起**：网关返回 200 + `: connected` 注释行（连接超时因此清除），但实例不产任何 `data:` 事件
3. **中途空闲挂起**（2026-08-17 CR 修复）：首个 `data:` 到达后若 KM Agent 僵死，流永远 pending
4. **长任务误杀**（2026-08-18 修复）：PPT 生成等长任务在 `tool.started` -> `tool.completed/failed` 之间数分钟无任何 `data:` 事件**属正常执行**，固定 120s idle 会误杀正在执行的任务

**规则**：SSE 流式 fetch 必须加**三层超时**，每层独立计时、独立清除；idle 层需**工具感知**（活跃工具期用长预算）：

```typescript
// 常量定义
const KM_STREAM_START_TIMEOUT_MS = 15_000;        // 连接/TTFB
const KM_STREAM_FIRST_EVENT_TIMEOUT_MS = 20_000;  // 首事件
const KM_STREAM_IDLE_TIMEOUT_MS = 120_000;        // 常规中途空闲
const KM_STREAM_TOOL_BUDGET_TIMEOUT_MS = 12 * 60 * 60 * 1000; // 工具执行期（PPT 等长任务，最长 12h）

// Layer 1: 连接超时（fetch resolve 前）
const connectController = new AbortController();
const connectTimeoutId = setTimeout(() => connectController.abort(), KM_STREAM_START_TIMEOUT_MS);
try {
  response = await fetch(url, {
    signal: input.signal
      ? AbortSignal.any([input.signal, connectController.signal])
      : connectController.signal,
  });
} catch (error) {
  if (connectController.signal.aborted && !input.signal?.aborted) {
    throw new BadGatewayException('EvoMind流式接口响应超时');
  }
  throw error;
} finally {
  clearTimeout(connectTimeoutId);
}

// Layer 2: 首事件超时（连接建立但零数据）
let firstEventTimer: ReturnType<typeof setTimeout> | undefined;
let firstEventArrived = false;
const armFirstEventTimeout = () => {
  firstEventTimer = setTimeout(() => connectController.abort(), KM_STREAM_FIRST_EVENT_TIMEOUT_MS);
};
armFirstEventTimeout();

// Layer 3: 中途空闲超时（首个 data: 到达后启动，每个后续 data: 重置）
// 工具感知：活跃工具存在期间用长预算，避免误杀长任务
let idleTimer: ReturnType<typeof setTimeout> | undefined;
let idleTimeoutFired = false;
let activeToolCount = 0;
const resetIdleTimeout = () => {
  if (idleTimer !== undefined) clearTimeout(idleTimer);
  const budgetMs = activeToolCount > 0
    ? KM_STREAM_TOOL_BUDGET_TIMEOUT_MS
    : KM_STREAM_IDLE_TIMEOUT_MS;
  idleTimer = setTimeout(
    () => {
      idleTimeoutFired = true;
      connectController.abort();
    },
    budgetMs,
  );
};

// 读取循环
try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // ... 解析 SSE 事件
    for (const line of lines) {
      yield* handleLine(line);
      if (line.startsWith('data:')) {
        // 工具活跃度追踪：事件块首个 data: 行按 eventName 计数（多 data 行
        // 只计一次；SSE 协议 event: 行先于 data: 到达，此时 eventName 即当前块名）
        if (dataLines.length === 1) {
          if (eventName === 'tool.started') activeToolCount += 1;
          else if (eventName === 'tool.completed' || eventName === 'tool.failed') {
            activeToolCount = Math.max(0, activeToolCount - 1);
          }
        }
        if (!firstEventArrived) {
          firstEventArrived = true;
          clearTimeout(firstEventTimer);
          firstEventTimer = undefined;
          resetIdleTimeout();  // 首个 data: 启动 idle 超时
        } else {
          resetIdleTimeout();  // 后续 data: 重置 idle 超时
        }
      }
    }
  }
} catch (error) {
  if (connectController.signal.aborted && !input.signal?.aborted) {
    // 区分超时类型给前端精准错误提示
    const reason = !idleTimeoutFired
      ? 'EvoMind流式接口响应超时'
      : activeToolCount > 0
        ? 'EvoMind流式接口响应超时（工具执行超时）'
        : 'EvoMind流式接口响应超时（传输中途挂起）';
    throw new BadGatewayException(reason);
  }
  throw error;
} finally {
  if (firstEventTimer !== undefined) clearTimeout(firstEventTimer);
  if (idleTimer !== undefined) clearTimeout(idleTimer);
}
```

**要点**：
1. `AbortSignal.any` 合并调用方 signal（用户取消）与超时 signal——任一触发中止
2. catch 里区分「超时 abort」（包装 BadGateway）与「调用方 abort」（原样透传）
3. `finally clearTimeout` 覆盖所有路径（resolve/reject/抛错）
4. **三个 timer 独立管理**：
   - `connectTimeoutId`：fetch resolve 时清除
   - `firstEventTimer`：首个 `data:` 到达时清除
   - `idleTimer`：每个 `data:` 行重置，无数据时触发
5. `idleTimeoutFired` + `activeToolCount` 标记区分超时类型（首事件/工具执行/常规挂起），前端可据此给更精准的错误态
6. **idle 预算工具感知**（2026-08-18）：`tool.started` -> `tool.completed/failed` 之间无 `data:` 事件是长任务（PPT 生成可达数分钟）的正常行为，不是挂起。活跃工具（`activeToolCount > 0`）期间 idle 预算切换为 12h（用户 2026-08-18 要求放宽，覆盖超长任务）；工具结束恢复 120s。用计数而非布尔--并行工具（A started、B started、A completed）下 B 仍在执行期
7. **多 data 行只计一次**：一个事件块可能有多行 `data:`（SSE 规范允许），用 `dataLines.length === 1` 判定块首行，避免重复计数泄漏

**Wrong vs Correct**:
```typescript
// Wrong: 只用 AbortSignal.timeout（从创建计时，流读到一半会被掐断）
await fetch(url, { signal: AbortSignal.timeout(15_000) });

// Wrong: 只有连接超时（首事件/中途挂起无保护）
const timeoutId = setTimeout(() => controller.abort(), 15_000);
// ... fetch 后 clearTimeout(timeoutId) ← 只保护连接，不保护流

// Wrong: 固定 idle timeout 不区分工具执行期（误杀 PPT 生成等长任务）
idleTimer = setTimeout(() => controller.abort(), 120_000);  // 工具跑 3 分钟就被杀

// Correct: 三层超时 + 工具感知 idle 预算
// 见上方完整示例
```

**Tests**: `zclaw-km-agent.client.test.ts` — 6 个测试覆盖三层超时 + 工具预算：
- `streamConversationMessage fails fast with BadGateway when KM Agent hangs` (connect timeout)
- `streamConversationMessage fails fast with BadGateway when gateway returns headers but no events` (first event timeout)
- `streamConversationMessage passes through events once first data arrives` (first event timeout cleared)
- `streamConversationMessage fails with BadGateway when stream hangs after first data` (idle timeout)
- `streamConversationMessage arms long tool budget while a tool is running` (tool budget, 2026-08-18)
- `streamConversationMessage restores regular idle budget after tool completes` (budget restore, 2026-08-18)

**Known Limits**:
- 即使三层超时，若 KM Agent 以极低速率（如每 121s 一个 `data:`）持续输出，idle 超时不会触发--这是设计取舍，避免误杀正常长回复。
- 工具真挂死（`tool.started` 后实例僵死）要等满 12h 工具预算才失败--这是长任务容忍度的代价；由前端 stale 检测与用户主动中断兜底。
- `tool.started`/`tool.completed` 不配对（如流在工具执行中被网关掐断后不再有 completed）会使 `activeToolCount` 悬挂为正--但流已终止，计数随调用栈销毁，不影响后续请求。

