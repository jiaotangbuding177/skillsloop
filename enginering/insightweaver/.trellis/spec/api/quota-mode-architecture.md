# Quota Mode Architecture

## Overview

B2B enterprises can switch between four quota modes: `conversation`, `token`, `batch`, `unlimited`. Each mode is completely independent — switching modes does not read data from other modes. The admin who switches bears responsibility.

## Mode Independence Principle

**Pattern**: Each quota mode reads only its own data. No cross-mode data reading.

**Why**: Prevents unintended side effects when switching modes. E.g., switching to conversation mode should not read token batch entitlements, even if they exist in the database.

**Example**:
```typescript
// CORRECT: conversation mode skips token checks entirely
if (config?.quotaMode === 'conversation') { return; }
if (config?.quotaMode === 'unlimited') { return; }

// WRONG: reading token entitlements in conversation mode
const useBillingEntitlements = await hasConsumableBillingTokenEntitlement(enterpriseId, userId);
// ↑ This returns true if token batches exist, bypassing conversation mode
```

## UNLIMITED_WORKSPACE_QUOTA_SENTINEL Convention

**What**: Use `-1n` as sentinel value for unlimited workspace quota.

**Why**: `0n` blocks users (no space). `BigInt(Number.MAX_SAFE_INTEGER)` displays as "8192 TB" in frontend. `-1` is recognized by frontend as `♾️`.

```typescript
const UNLIMITED_WORKSPACE_QUOTA_SENTINEL = -1n;

// Backend: return sentinel for unlimited mode
const effectiveQuotaBytes = isUnlimitedMode
  ? UNLIMITED_WORKSPACE_QUOTA_SENTINEL
  : defaultQuotaBytes;

// Backend: skip isOverLimit for unlimited
isOverLimit: effectiveQuotaBytes >= 0n && usageBytes >= effectiveQuotaBytes,

// Frontend: recognize -1 as unlimited
const isUnlimited = effectiveQuotaBytes < 0;
// Display: '♾️' instead of formatBytes(-1)
```

## Billing Flow Bypass（resolveQuotaContext 单次解析）

**Problem**: `streamMessage` 曾对 quota 配置多次读取（≥3 次），且 billing 判定散落在多处。

**Fix**: `resolveQuotaContext(enterpriseId, userId)` 单次读取 config + hasConsumable，推导 `useBillingEntitlements`：

```typescript
const quotaContext = await this.resolveQuotaContext(enterpriseIdForEfficiency, userId);
const useBillingEntitlements = quotaContext.useBillingEntitlements;
// useBillingEntitlements = hasConsumable && quotaMode ∉ {conversation, unlimited, token}
```

`assertEnterpriseTokenQuotaIfNeeded` / `settleEnterpriseTokenUsageIfNeeded` 接受可选 `ctx?: QuotaContext`；`streamMessage` 传入已 resolve 的 ctx（单次读），测试直接调用时 ctx 为 undefined 则内部自 resolve（向后兼容）。

> **Warning**: `quota-mode-backend.test.ts` 直接在 `ZclawService` 实例上调用 assert/settle 并 mock 实例级依赖。任何将逻辑抽为独立 Injectable 的重构都会破坏这些测试。逻辑必须保留为 `ZclawService` 方法。

## Admin Role: Count But Don't Limit

**What**: Admin/owner roles have unlimited conversations but usage is still recorded for analytics.

**Why**: Admins need to see their usage stats, but must never be blocked.

```typescript
// CORRECT: record usage for admins, but don't throw
const isAdmin = ZCLAW_ENTERPRISE_ADMIN_ROLES.has(membership.role);
// ... insert/update usage row ...
const consumed = await this.prisma.$executeRaw`
  UPDATE ... SET "remainingConversations" = "remainingConversations" - 1
  WHERE ... AND "remainingConversations" > 0
`;
if (consumed === 0 && !isAdmin) {
  throw new ZclawConversationQuotaExceededError();
}
```

## Batch Mode: 豁免判定矩阵（isQuotaExempt，2026-08-06 更新）

### Problem

Batch mode owner/admin were excluded from batch assignment (`syncActiveMembersToDefaultBatch` skips admin/owner). This caused `getMyEnterpriseTokenQuotaSummary` to return `effectiveTokenLimit: "0"` and `accountValidity: null`, which the frontend interpreted as "account expired, 0 tokens".

### 豁免矩阵（统一语义，`packages/shared/src/quota-exemption.ts`）

**`isQuotaExemptByMatrix`** 是唯一豁免判定源（billing 扣减、存储豁免、isQuotaExempt 字段、成员列表全部接入）：

| 企业 kind | quotaMode | 豁免条件 |
|-----------|-----------|---------|
| C 端（consumer/evomind_consumer） | 任意 | **不豁免**（所有用户，含平台 admin） |
| B 端（b2b） | `batch` | **仅平台 admin**（`users.role === 'admin'`）——企业 admin/owner 可能是外部人员，不豁免 |
| B 端（b2b） | 非 batch（unlimited/conversation/token/null） | 平台 admin / 企业 admin / 企业 owner |

**双重身份**（平台 admin + 企业 admin）：batch 模式取平台身份 → 豁免生效。

**豁免用户行为**：
- billing 路径（`freezeEntitlements`/`captureEntitlements`）返回空 consumption——**不扣减**（只记录 settlement）
- `getMyEnterpriseTokenQuotaSummary` batch 分支返回 `isQuotaExempt: true` + `effectiveTokenLimit: null`
- `getEnterpriseWorkspaceQuotaConfig` 返回 unlimited 存储（`quotaSource: "unlimited"`）
- `assertEnterpriseTokenQuotaIfNeeded` 直接放行（不拦截）
- 前端：token 显示 ∞（Seam 1 跳过豁免用户）；**有效期块整体不显示**（showBlock 含 `!isQuotaExempt`）

**非豁免（企业 admin/owner 在 batch）**：照常扣减、显示套餐余额、有效期块含徽章/续费按钮。

### isQuotaExempt Field Flow (4 layers)

| Layer | File | Field |
|-------|------|-------|
| 矩阵纯函数 | `packages/shared/src/quota-exemption.ts` | `isQuotaExemptByMatrix` |
| Backend interface | `zclaw.service.ts:235` | `isQuotaExempt?: boolean` |
| Backend return | `zclaw.service.ts`（batch 分支） | `isQuotaExempt: true`（仅平台 admin） |
| Backend return | `zclaw.service.ts`（batch 分支） | `isQuotaExempt: false`（企业 admin/owner/member） |
| API response | `workspace/usage.conversationQuotaSummary` | serialized from backend |
| Frontend type | `apps/web/src/api/moudles/zclaw.ts:3413` | `isQuotaExempt?: boolean` |
| Frontend UI | `ZclawShell.tsx` | Seam 1 跳过豁免用户（batch 分支返回 ∞） |
| Frontend validity | `account-validity-display.ts` | `showBlock` 含 `!input.isQuotaExempt`（豁免用户整块不显示） |

### Backend Implementation

```typescript
// getMyEnterpriseTokenQuotaSummary — batch branch（仅平台 admin 豁免）
const platformUser = await this.prisma.user.findUnique({ where: { id: userId }, select: { role: true } });
if (platformUser?.role === "admin") {
  return { enterpriseId, membershipRole, tokenUsed: "0", effectiveTokenLimit: null,
           isBatchExpired: false, isBatchMode: true, isBatchQuotaExceeded: false, isQuotaExempt: true };
}

// billing 路径（freeze/capture）——豁免用户不扣减
if (await this.isQuotaExemptUser(enterpriseId, userId)) {
  return this.consumptionResultFromLedgers([], 'freeze');
}
```

### Frontend Implementation

```typescript
// resolveVisibleTokenBalance — Seam 1 跳过豁免用户
if (quotaMode === "batch" && postExpiryPurchaseMode === "self_purchase"
    && !legacyQuota?.isQuotaExempt && hasUserTokenEntitlement(entitlementSummary)) { ... }
// batch 分支：isQuotaExempt → ∞

// resolveAccountValidityDisplay
const showBlock = !input.isQuotaExempt && (hasAccountValidity || showInvalid);
```

### Storage Quota Exemption

`getEnterpriseWorkspaceQuotaConfig` 的豁免同样走矩阵（`isQuotaExemptByMatrix`）——返回 `quotaBytes: BigInt(Number.MAX_SAFE_INTEGER)` + `quotaSource: "unlimited"`：

```typescript
// 豁免判定按统一矩阵（C 端不豁免 / batch 仅平台 admin / 非 batch 管理者豁免）
const platformUser = await this.prisma.user.findUnique({ where: { id: userId }, select: { role: true } });
if (isQuotaExemptByMatrix({
  enterpriseKind: enterprise?.enterpriseKind,
  quotaMode: quotaConfig?.quotaMode,
  userRole: platformUser?.role,
  membershipRole: membership.role,
})) {
  return {
    quotaBytes: BigInt(Number.MAX_SAFE_INTEGER),
    hasActiveMonthlyPlan: true,
    hasUsableBillingEntitlement: true,
    quotaSource: "unlimited",
    entitlementExpiredReason: null,
    entitlementExpiredMessage: null,
  };
}
```

### Common Mistake: 豁免判定散落各处绕过矩阵

**Symptom**: batch 模式下企业 admin/owner 仍显示豁免（∞/unlimited）；billing 路径扣减平台 admin 的 C 端套餐。

**Cause**: 各调用点各自写 `ZCLAW_ENTERPRISE_ADMIN_ROLES.has(role)` 或完全不检查角色（freeze/capture 无豁免 → 平台 admin 被扣光自购套餐；成员配额列表遗漏接入矩阵）。

**Fix**: 所有豁免判定（isQuotaExempt 字段、存储豁免、billing freeze/capture、assert 放行、管理后台成员列表）必须走 `isQuotaExemptByMatrix`（`packages/shared/src/quota-exemption.ts`），禁止散落的角色判断。

**Prevention**: 豁免语义变更时，grep `ZCLAW_ENTERPRISE_ADMIN_ROLES` / `membership.role === "admin"` 全量排查；新增豁免场景默认接入矩阵纯函数。

## Unified Enterprise Config Pattern

**What**: Extend existing `getWorkspaceUsageSummary` response instead of creating new API endpoints.

**Why**: Prevents redundant API calls and 403 errors. Frontend calls one endpoint on Shell init, shares via Context.

```typescript
// Backend: getWorkspaceUsageSummary returns all enterprise config
async getWorkspaceUsageSummary(userId: string) {
  // ... existing workspace usage logic ...
  
  // Append enterprise config
  const [quotaConfigCheck, postExpiryConfig] = await Promise.all([
    this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique(...),
    this.prisma.enterprisePostExpiryPurchaseConfig.findUnique(...),
  ]);
  const conversationQuotaSummary = await this.getMyEnterpriseTokenQuotaSummary(
    userId, context.enterpriseId,
  );
  
  return { ...existingFields, postExpiryPurchaseMode, conversationQuotaSummary };
}

// Frontend: derive from context, no independent API calls
const postExpiryPurchaseMode = workspaceUsage?.postExpiryPurchaseMode ?? null;
```

## Workspace Quota Strategy Matrix

| Scenario | effectiveQuotaBytes | quotaSource |
|----------|-------------------|-------------|
| quotaMode = unlimited | `MAX_SAFE_INTEGER` | `unlimited` |
| C-end + active consumer monthly plan | `packageStorageBytes` | `monthly_plan` |
| C-end + admin grant (no monthly plan) | `adminGrantStorageBytes` | `admin_grant` |
| C-end + no plan + no grant | `0n` | `none` (consumer_monthly_expired) |
| B2B + active b2b monthly plan + active seats | `packageStorageBytes` | `monthly_plan` |
| B2B + active b2b monthly plan + no active seats | `baseQuotaBytes` (fall through) | `default_quota` |
| B2B + no monthly plan + defaultQuota OFF | `0n` | `none` (b2b_enterprise_entitlement_expired) |
| B2B + no monthly plan + defaultQuota ON + batch mode | `baseQuotaBytes + packageStorageBytes` (with account validity gate) | `default_quota` |
| B2B + no monthly plan + defaultQuota ON + non-batch mode | `baseQuotaBytes` (no stacking) | `default_quota` |

## Conversation Mode API Flow

| Method | Behavior |
|--------|------|
| `assertEnterpriseTokenQuotaIfNeeded` | Call `assertConversationQuotaAvailable` (check remainingConversations > 0) |
| `settleEnterpriseTokenUsageIfNeeded` | Record token usage for analytics via `settleMessageTokenUsage` |
| `getMyEnterpriseTokenQuotaSummary` | Return conversation data with `isConversationMode: true` |

## Token Mode API Flow

| Method | Behavior |
|--------|------|
| `assertEnterpriseTokenQuotaIfNeeded` | Call `assertTokenQuotaAvailable` (check tokenUsed < effectiveLimit) |
| `settleEnterpriseTokenUsageIfNeeded` | Record token usage via `settleMessageTokenUsage` |
| `getMyEnterpriseTokenQuotaSummary` | Return token quota data from `zclawEnterpriseConversationQuotaUsage` |

> **Warning**: Token mode MUST appear BEFORE `hasConsumableBillingTokenEntitlement` check in `settleEnterpriseTokenUsageIfNeeded`. If billing check comes first with true result, token settlement is skipped and usage is never recorded.

## All Modes Record Token Consumption

**Principle**: ALL quota modes (unlimited, conversation, token, batch) record token consumption via `settleMessageTokenUsage` for analytics. The difference is where the settlement data goes:

| Mode | Settlement table | Used for |
|------|-----------------|---------|
| unlimited | `zclawEnterpriseTokenUsageSettlement` | Analytics only |
| conversation | `zclawEnterpriseTokenUsageSettlement` | Analytics only |
| token | `zclawEnterpriseTokenUsageSettlement` + update `tokenUsed` | Quota enforcement + analytics |
| batch | `zclawEnterpriseTokenUsageSettlement` | Quota enforcement + analytics |

## Historical quotaMode on Settlement Records

**Schema**: `ZclawEnterpriseTokenUsageSettlement.quotaMode` (String?, nullable)

Each settlement record stores the `quotaMode` active at the time of creation. This enables per-record mode display in the Token明细 dialog.

```typescript
// settlement creation in settleMessageTokenUsage
await this.prisma.zclawEnterpriseTokenUsageSettlement.create({
  data: {
    // ... existing fields ...
    quotaMode: quotaMode ?? null,
  },
});
```

**Migration**:
```sql
ALTER TABLE "zclaw_enterprise_token_usage_settlements"
ADD COLUMN IF NOT EXISTS "quotaMode" TEXT;
```

## assertConversationQuotaAvailable

**What**: Checks if the user has remaining conversations. Admins always pass.

```typescript
private async assertConversationQuotaAvailable(enterpriseId: string, userId: string) {
  const membership = await this.prisma.enterpriseMembership.findFirst({ ... });
  if (!membership || membership.role === "admin" || membership.role === "owner") return;

  const usage = await this.prisma.zclawEnterpriseConversationQuotaUsage.findUnique({
    where: { enterpriseId_userId: { enterpriseId, userId } },
    select: { remainingConversations: true },
  });
  if (usage?.remainingConversations != null && usage.remainingConversations <= 0) {
    throw new ZclawTokenQuotaExceededError();
  }
}
```

## `settleMessageTokenUsage` Signature

```typescript
async settleMessageTokenUsage(
  enterpriseId: string,
  userId: string,
  messageId: string,
  usagePayload: ZclawTokenUsagePayload,
  quotaMode?: string | null,  // NEW: stored on settlement record
)
```

## `listUserTokenQuotaRecords` Response

```typescript
items: {
  messageId: string;
  tokens: string;
  quotaMode: string | null;  // NEW: historical quota mode per record
  occurredAt: string;
}[]
```

## Common Mistake: Reading config.tokenLimit and returning early

**Symptom**: Token usage always shows 0 in unlimited mode.

**Cause**: `settleMessageTokenUsage` checks `if (!config?.tokenLimit) return;` — for unlimited mode, `tokenLimit` is null, so usage is never recorded.

**Fix**: Remove the early return, use `0n` as fallback for `ensureUsageRow`:

```typescript
// WRONG
if (!config?.tokenLimit) { return; }

// CORRECT
await this.ensureUsageRow(enterpriseId, userId, config?.tokenLimit ?? 0n, isQuotaExempt);
```

### Common Mistake: hasConsumableBillingTokenEntitlement before quotaMode check

**Symptom**: Unlimited mode shows `0 / ♾️` — token usage not recorded.

**Cause**: `settleEnterpriseTokenUsageIfNeeded` checks `hasConsumableBillingTokenEntitlement` before checking `quotaMode === 'unlimited'`. In unlimited mode, `streamMessage` forces `useBillingEntitlements = false`, but `settleEnterpriseTokenUsageIfNeeded` independently checks billing entitlements again. If billing token entitlements exist (common for B2B enterprises), the method returns immediately without recording usage.

**Root**: Cross-check between `settleEnterpriseTokenUsageIfNeeded` and `streamMessage` — the billing bypass logic needs to be applied in BOTH places.

**Fix**: Move unlimited mode handling before the billing entitlement check:

```typescript
// WRONG order: billing check blocks unlimited mode
if (config?.quotaMode === 'conversation') { return; }
if (await this.hasConsumableBillingTokenEntitlement(enterpriseId, userId)) { return; } // ← blocks unlimited
// ... never reaches unlimited handling

// CORRECT order: quota mode checks first, then billing
if (config?.quotaMode === 'conversation') { return; }
if (config?.quotaMode === 'unlimited') {
  await this.enterpriseTokenQuotaService.settleMessageTokenUsage(...);
  return;
}
if (await this.hasConsumableBillingTokenEntitlement(enterpriseId, userId)) { return; }
// ... token/batch mode billing handling
```

**Checklist when adding a new quota mode**:
- [ ] `assertEnterpriseTokenQuotaIfNeeded`: add mode handling (skip, check conversation quota, or check token/batch quota)
- [ ] `settleEnterpriseTokenUsageIfNeeded`: add mode BEFORE billing check — must record token usage for ALL modes
- [ ] `streamMessage`: add mode to billing bypass list (`quotaMode === 'conversation' || 'unlimited' || 'token' || 'batch'`)
- [ ] `freezeEntitlements`: add mode to skip list (`quotaMode === 'conversation' || 'unlimited' || 'token' || 'batch'`)
- [ ] `getMyEnterpriseTokenQuotaSummary`: return data for the mode (not null)
- [ ] `settleMessageTokenUsage`: pass `quotaMode` for historical record
- [ ] `useBillingEntitlements`: add mode to exclusion list in `resolveQuotaContext`
- [ ] `hasConsumableBillingTokenEntitlement`: verify batch mode doesn't incorrectly return true for B2B enterprises with active monthly plans

## Batch Mode: Settlement Must Precede hasConsumable Check

**Symptom**: Token consumption not recorded in batch mode. User sees "Token 额度已用尽" error or no consumption records in "Token 明细".

**Cause**: `settleEnterpriseTokenUsageIfNeeded` checks `hasConsumableBillingTokenEntitlement` BEFORE checking `quotaMode === 'batch'`. For B2B enterprises with active monthly plans, `hasConsumableBillingTokenEntitlement` returns `true` (because the enterprise has a monthly plan), so the method calls `enterpriseTokenQuotaService.settleMessageTokenUsage` (writes to `zclawEnterpriseTokenUsageSettlement` but with wrong quotaMode) and returns — skipping the batch-specific settlement path.

**Root**: Two-level routing conflict:
1. `useBillingEntitlements` (in `resolveQuotaContext`) routes to billing path (freeze/capture) for batch mode → bypasses settlement
2. Even if settlement is reached, `hasConsumable` check intercepts before batch mode check

**Fix**: In `settleEnterpriseTokenUsageIfNeeded`, check `quotaMode === 'batch'` BEFORE `hasConsumable`:

```typescript
// WRONG: billing check intercepts batch mode
if (config?.quotaMode === 'conversation') { return; }
if (config?.quotaMode === 'unlimited') { return; }
if (config?.quotaMode === 'token') { return; }
if (await this.hasConsumableBillingTokenEntitlement(enterpriseId, userId)) {
  await this.enterpriseTokenQuotaService.settleMessageTokenUsage(...);
  return;
}
if (quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  await this.enterpriseTokenBatchQuotaService.settleMessageTokenUsage(...);
  return;
}

// CORRECT: batch mode before billing check
if (config?.quotaMode === 'conversation') { return; }
if (config?.quotaMode === 'unlimited') { return; }
if (config?.quotaMode === 'token') { return; }
if (quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  await this.enterpriseTokenBatchQuotaService.settleMessageTokenUsage(...);
  return;
}
if (await this.hasConsumableBillingTokenEntitlement(enterpriseId, userId)) {
  await this.enterpriseTokenQuotaService.settleMessageTokenUsage(...);
  return;
}
```

**Also required**: `useBillingEntitlements` in `resolveQuotaContext` must exclude batch mode:

```typescript
// WRONG: batch mode uses billing path (freeze/capture)
const useBillingEntitlements =
  hasConsumableBillingEntitlement &&
  quotaMode !== 'conversation' &&
  quotaMode !== 'unlimited' &&
  quotaMode !== 'token';

// CORRECT: batch mode uses settlement path
const useBillingEntitlements =
  hasConsumableBillingEntitlement &&
  quotaMode !== 'conversation' &&
  quotaMode !== 'unlimited' &&
  quotaMode !== 'token' &&
  quotaMode !== ZCLAW_QUOTA_MODE_BATCH;
```

**Why**: Batch mode tracks token usage via `zclaw_enterprise_token_usage_settlements` (settlement table), not via entitlement ledger (freeze/capture). The billing path writes to `entitlementLedger`, which is wrong for batch mode.

## Batch Mode: freezeEntitlements Must Skip

**Symptom**: "Token 额度已用尽，请联系管理员充值或购买补充包" error when trying to chat in batch mode.

**Cause**: `freezeEntitlements` in `entitlement.service.ts` skips `unlimited`/`token`/`conversation` modes but NOT `batch`. In batch mode, it tries to freeze from entitlement batches, but all batches are frozen (old monthly plan seats), so it throws `INSUFFICIENT_CREDITS`.

**Fix**: Add batch mode to the skip list:

```typescript
// WRONG
if (quotaConfig?.quotaMode === 'unlimited' || quotaConfig?.quotaMode === 'token' || quotaConfig?.quotaMode === 'conversation') {
  return this.consumptionResultFromLedgers([], 'freeze');
}

// CORRECT
if (quotaConfig?.quotaMode === 'unlimited' || quotaConfig?.quotaMode === 'token' || quotaConfig?.quotaMode === 'conversation' || quotaConfig?.quotaMode === 'batch') {
  return this.consumptionResultFromLedgers([], 'freeze');
}
```

## Batch Mode: assignMemberToBatch Must Clear Validity Dates

**Symptom**: After reassigning a user to a new batch, storage quota shows 0GB even though the new batch is active and within dates.

**Cause**: `assignMemberToBatch` upsert's `update` branch only updates `batchId`, `assignedAt`, `updatedAt` — it does NOT clear `validFrom`/`validTo`. If the user was previously assigned via `assignMemberToDefaultBatchWithDynamicValidity` (which sets custom `validFrom`/`validTo`), the old dates persist. When the old `validTo` is in the past, `computeAccountValidity` returns `expired`, causing storage quota to be 0.

**Fix**: Clear `validFrom`/`validTo` in the update branch:

```typescript
// WRONG: old dates persist
update: {
  batchId,
  assignedAt: new Date(),
  updatedAt: new Date(),
}

// CORRECT: clear dates so member inherits new batch's dates
update: {
  batchId,
  validFrom: null,
  validTo: null,
  assignedAt: new Date(),
  updatedAt: new Date(),
}
```

## Batch Mode: computeAccountValidity Must Return Valid for Active Batches

**Symptom**: `computeAccountValidity` returns `null` for active zclaw batches, causing storage quota to be 0.

**Cause**: The zclaw member check at the end of `computeAccountValidity` only handles the expired case (`if (effectiveTo < now) return expired`). When the batch is active and within dates, it falls through to the frozen batch check and eventually returns `null`.

**Fix**: Return a valid result when the zclaw batch is active and within dates:

```typescript
// WRONG: only handles expired case
if (member && member.batch.status === BATCH_STATUS_ACTIVE) {
  const effectiveTo = member.validTo ?? member.batch.validTo;
  if (effectiveTo < now) {
    return { validFrom: ..., validUntil: effectiveTo, status: "expired" };
  }
  // Falls through to null
}

// CORRECT: also return valid result
if (member && member.batch.status === BATCH_STATUS_ACTIVE) {
  const effectiveFrom = member.validFrom ?? member.batch.validFrom;
  const effectiveTo = member.validTo ?? member.batch.validTo;
  if (effectiveTo < now) {
    return { validFrom: effectiveFrom, validUntil: effectiveTo, status: "expired" };
  }
  return { validFrom: effectiveFrom, validUntil: effectiveTo, status: this.validityStatus(effectiveTo, now) };
}
```

## Batch Mode: hasActiveB2BMonthlyPlan with Frozen Seats

**Symptom**: Storage quota shows 0GB even though `memberDefaultWorkspaceQuotaBytes` is configured (e.g., 5GB).

**Cause**: `hasActiveB2BMonthlyPlan` returns `true` (enterprise has an active monthly plan), so `getEnterpriseWorkspaceQuotaConfig` returns early with `quotaBytes: packageStorageBytes`. But if all seat entitlements are frozen (old monthly plan), `packageStorageBytes = 0n`, so the user gets 0 storage instead of falling through to the default quota config.

**Fix**: Only short-circuit if the user actually has active storage entitlements:

```typescript
// WRONG: returns 0 when seats are frozen
if (hasActiveB2BMonthlyPlan) {
  return { quotaBytes: packageStorageBytes, ... };
}

// CORRECT: fall through to default quota when no active seats
if (hasActiveB2BMonthlyPlan && packageStorageBytes > 0n) {
  return { quotaBytes: packageStorageBytes, ... };
}
```

## Workspace Quota Strategy Matrix (Updated)

| Scenario | effectiveQuotaBytes | quotaSource |
|----------|-------------------|-------------|
| quotaMode = unlimited | `MAX_SAFE_INTEGER` | `unlimited` |
| **owner/admin (quota-exempt)** | **`MAX_SAFE_INTEGER`** | **`unlimited`** |
| C-end + active consumer monthly plan | `packageStorageBytes` | `monthly_plan` |
| C-end + admin grant (no monthly plan) | `adminGrantStorageBytes` | `admin_grant` |
| C-end + no plan + no grant | `0n` | `none` (consumer_monthly_expired) |
| B2B + active b2b monthly plan + active seats | `packageStorageBytes` | `monthly_plan` |
| B2B + active b2b monthly plan + no active seats | `baseQuotaBytes` (fall through) | `default_quota` |
| B2B + no monthly plan + defaultQuota OFF | `0n` | `none` (b2b_enterprise_entitlement_expired) |
| B2B + no monthly plan + defaultQuota ON + batch mode | `baseQuotaBytes + packageStorageBytes` (with account validity gate) | `default_quota` |
| B2B + no monthly plan + defaultQuota ON + non-batch mode | `baseQuotaBytes` (no stacking) | `default_quota` |

## applyToolBillingAdjustment（纯函数）

**位置**: `enterprise-token-quota.constants.ts`

**What**: 将 toolBillingTokens 调整合并到 usage payload。正数加 output（÷6 向上取整）；负数先抵 output 再抵 input（clamp≥0）；零返回原对象。

**Why**: 原 settle 中 3 处重复调整块（unlimited/token/batch）收敛为单一纯函数调用。

```typescript
export function applyToolBillingAdjustment(
  usage: ZclawTokenUsagePayload,
  toolBillingTokens: number,
): ZclawTokenUsagePayload {
  if (toolBillingTokens === 0) return usage;
  if (toolBillingTokens > 0) {
    return { ...usage, output: (usage.output ?? 0) + Math.ceil(toolBillingTokens / 6) };
  }
  const rewardUnits = Math.abs(Math.ceil(toolBillingTokens / 6));
  let remaining = rewardUnits;
  const newOutput = Math.max(0, (usage.output ?? 0) - remaining);
  remaining -= (usage.output ?? 0) - newOutput;
  const newInput = Math.max(0, (usage.input ?? 0) - remaining);
  return { ...usage, output: newOutput, input: newInput };
}
```

## Enterprise Admin Batch Management Permission Gating

**Pattern**: `*ForEnterpriseAdmin` wrapper methods in `zclaw.service.ts` are the ONLY place to add enterprise-admin-only permission checks. Platform admin routes call `*ForAdmin` methods directly via `AdminGuard`, bypassing wrappers entirely.

**Why**: Separation of concerns — platform admin should never be affected by enterprise-level purchase mode restrictions.

### Wrapper Methods (7 total)

| Method | Line (approx) |
|--------|---------------|
| `getEnterpriseTokenQuotaBatchForEnterpriseAdmin` | 1715 |
| `listEnterpriseTokenQuotaBatchMembersForEnterpriseAdmin` | 1759 |
| `listEnterpriseTokenQuotaBatchesForEnterpriseAdmin` | 1773 |
| `createEnterpriseTokenQuotaBatchForEnterpriseAdmin` | 1820 |
| `updateEnterpriseTokenQuotaBatchForEnterpriseAdmin` | 1870 |
| `cancelEnterpriseTokenQuotaBatchForEnterpriseAdmin` | 1886 |
| `moveEnterpriseTokenQuotaMemberForEnterpriseAdmin` | 1935 |
| `migrateEnterpriseTokenQuotaBatchForEnterpriseAdmin` | 1996 |

### Permission Check Pattern

```typescript
import { resolvePurchaseMode } from "../billing/purchase-mode.js";

async someMethodForEnterpriseAdmin(callerUserId: string, enterpriseId: string) {
  await this.enterpriseService.assertEnterpriseAdminOrOwner(callerUserId, enterpriseId);
  const purchaseMode = await resolvePurchaseMode(this.prisma, enterpriseId);
  if (purchaseMode !== "contact_admin") {
    throw new ForbiddenException("当前模式下企业管理员无权管理批次");
  }
  return this.someMethodForAdmin(enterpriseId);
}
```

### Frontend Counterpart

`ZclawShell.tsx` gates the "批次管理" nav item:
```typescript
canAccessBatchManagement: workspaceUsage?.quotaMode === 'batch' &&
  (canAccessManagementBackend || workspaceUsage?.postExpiryPurchaseMode === 'contact_admin')
```

### Visibility Matrix

| Role | contact_admin | admin_purchase | self_purchase |
|------|--------------|----------------|---------------|
| Platform admin | ✅ | ✅ | ✅ |
| Enterprise admin | ✅ | ❌ | ❌ |

## switchQuotaMode（DefaultQuotaPolicyService）

**What**: 从 `updatePolicy` 提取的 public 方法，负责 quotaMode 联动（upsert config + audit log）。

```typescript
async switchQuotaMode(
  tx: Pick<Prisma.TransactionClient, "zclawEnterpriseConversationQuotaConfig" | "auditLog">,
  enterpriseId: string,
  actorUserId: string,
  quotaMode: string,
): Promise<void>
```

**行为**: 读 existing config → upsert quotaMode → 仅 mode 变化时写 auditLog（action=`quota_mode_switched`）。`updatePolicy` 以 `enabled ? "batch" : "unlimited"` 调用。

## Design Decision: D-A3 — 逻辑保留在 ZclawService 而非独立 Injectable

**Context**: 原设计规划独立 `QuotaModeRouter` + `EnterpriseEntitlementResolver` Injectable。

**Options Considered**:
1. 独立 Injectable（原设计）— 更清晰的模块边界
2. ZclawService 方法 + 可选 ctx 参数 — 保持测试兼容

**Decision**: 选 2。`quota-mode-backend.test.ts` 为不可改动硬约束，12 个原始用例直接在 `ZclawService` 实例上调用 assert/settle 并 mock 实例级依赖。抽为独立 Injectable 需迁移测试到 NestJS testing-module。

**Extensibility**: 未来迁移测试后可提取独立 Injectable，接口不变。

## 账户有效期（Account Validity）与空间有效期

**原则（D2）**：空间有效期 = 账户有效期（`accountValidity.validUntil`）。后端不做空间维度独立过期清理，仅驱动到期展示与行为门控。

**展示链路**：`computeAccountValidity`（`enterprise-token-batch-quota.service.ts`）→ `getWorkspaceUsageSummary.conversationQuotaSummary.accountValidity` → 前端 `resolveAccountValidityDisplay`（`apps/web/src/lib/account-validity-display.ts`）→ `WorkspaceIdentityMetaPanel` / `ZclawShell` 侧边栏。

**状态三态**：`active` / `expiring_soon` / `expired`，前端 badge 分别渲染绿/琥珀/红色。i18n key：`accountValidityActive` / `accountValidityExpiringSoon` / `accountValidityExpired`。

## Batch 模式 Fixed vs Dynamic 有效期

| 模式 | member 有效期 | 账户有效期 |
|------|-------------|-----------|
| **fixed** | = batch 有效期（`validFrom` ~ `validUntil`） | = member 有效期 |
| **dynamic** | = 加入起算 `batchDynamicValidityMonths` 个月 | = member 有效期 |

- `assignMemberToDefaultBatchWithDynamicValidity`：dynamic 模式下 member 的 `validFrom`/`validTo` 由加入时间 + 配置月数计算。
- `computeAccountValidity`：取当前用户关联 batch 的时间窗口，返回 `{validFrom, validUntil, status}`。
- 两种模式下"账户有效期"均即 member 有效期，不存在独立的空间维度过期。

## postExpiryMode 数据源隔离矩阵（2026-07-22 重构）

### 三种模式数据源

| 模式 | Token 来源 | 存储来源 | 账户有效期判定 |
|------|-----------|---------|---------------|
| **contact_admin** | 仅 zclaw 批次 | 仅默认配额 | 批次过期 → 账户过期（无 fallback） |
| **self_purchase** | 批次 + C端包 | 默认 + C端包 | 批次过期且无C端月包 → 账户过期 |
 | **admin_purchase** | 批次 + B端包 | 默认 + B端包 | 批次过期 + 无B2B席位 → 账户过期；有B2B席位 → 有效 |

### 关键规则

1. **contact_admin**：不叠加任何包（无论C端B端），只看批次 + 默认配额
2. **self_purchase**：不叠加B端数据（企业级月包、B端token/空间包）
3. **admin_purchase**：不叠加C端数据（用户自购的套餐、token包、空间包）

### 批次过期时的 token 处理

| 模式 | 批次有效 | 批次过期 + 有席位/月包 | 批次过期 + 无席位/月包 |
|------|---------|---------------------|---------------------|
| contact_admin | 批次 token | account_expired | account_expired |
| self_purchase | 批次 + C端包 | C端包 token | account_expired |
| admin_purchase | 批次 + B端包 | B端包 token（不含批次） | account_expired |

- **批次过期时，批次 token 不参与叠加**：`effectiveBatchTokenLimit = 0`，`effectiveBatchRemaining = 0`

### 后端实现要点

#### `getEnterpriseWorkspaceQuotaConfig`（存储配额）

- 包查询按 `postExpiryMode` 过滤 `sourceType`：
  - contact_admin → `allowedStorageSourceTypes = null`（跳过查询）
  - self_purchase → `CEND_SOURCE_TYPES`
  - admin_purchase → `BEND_SOURCE_TYPES`
- B2B 月包 early return（`hasActiveB2BMonthlyPlan && packageStorageBytes > 0n`）仅限 `admin_purchase`
- **存储 = baseQuota + packageStorageBytes**（叠加，非替换）
- **contact_admin / admin_purchase 模式跳过 `computeAccountValidity`**：直接查 `zclawEnterpriseTokenQuotaMember` + `batch.validTo` 判断过期。`computeAccountValidity` 会优先查 `monthly_plan` entitlement batch（含C端包），返回错误的 C端包日期。
- admin_purchase 模式批次过期时检查 B2B 席位分配（`b2b_monthly_seat_plan`, `status: "active"`, `validFrom <= now < validUntil`）作为 fallback
- self_purchase 模式仍用 `computeAccountValidity`（查 C端月包 + 批次窗口）

#### `getMyEnterpriseTokenQuotaSummary`（侧边栏 Token 显示）

- 始终以 zclaw 批次为基线（`batchTokenLimit` + `batchTokenUsed`）
- **批次过期时 `effectiveBatchTokenLimit = 0`，`effectiveBatchRemaining = 0`**
- 按 `postExpiryMode` 叠加模式特定包：
  - contact_admin → `packageTokenGranted = 0`（不叠加）
  - self_purchase → `CEND_TOKEN_SOURCE_TYPES`（consumer_monthly_plan, consumer_token_topup）
  - admin_purchase → `BEND_TOKEN_SOURCE_TYPES`（b2b_enterprise_plan, b2b_monthly_seat_plan, b2b_token_topup, admin_grant）
- **admin_purchase 模式批次过期但有 B2B 席位时**：`isBatchExpired = false`，`windowEnd` 用席位 `validUntil`（前端正常显示）
- **admin_purchase 模式 B2B 月包 active 时**：`windowEnd` 用 B2B 月包 `validUntil`（前端显示 B2B 月包有效期）

#### `resolveQuotaContext`（消费链路切换）

- **admin_purchase + 批次过期 + 有B端包 → 强制 `useBillingEntitlements = true`**
  - 否则 `useBillingEntitlements = false` 导致 billing freeze 不触发 + batch check 被 hasConsumable 绕过 → token 消费无扣减
- self_purchase + 有C端包 → `useBillingEntitlements = true`（不变）

#### `freezeEntitlements`（billing path）

- 部分冻结：`remaining > 0n && ledgers.length > 0` 时不抛 INSUFFICIENT_CREDITS
- 全空（`ledgers.length === 0`）才抛 INSUFFICIENT_CREDITS
- self_purchase 模式消息改为"请购买套餐续期"
- 默认预扣从 100,000 降为 10,000（`resolveAiHoldTokens`）

#### `isUsableInBillingContext`（billing path 批次过滤）

- **B2B 企业非 self_purchase 排除所有 C端包**（consumer_monthly_plan, consumer_token_topup, consumer_storage_topup）
- **self_purchase 模式 C端包直接返回 true**（绕过 priority/gift/batch-window 检查）
- **self_purchase 模式非 C端包直接返回 false**（排除 B2B 来源：b2b_token_topup, b2b_monthly_seat_plan 等）
- Consumer 企业 C端包正常使用
- `hasActiveMonthlyPlan` 优先级最高（priority <= 3 可用）— self_purchase C端包不经过此检查
- `consumptionPriority` 中 `b2b_token_topup` 返回 2（不是 4），`b2b_monthly_seat_plan` 返回 4

#### `resolveLegacyB2BAvailableTokens`（legacy 批次 token 叠加）

- **self_purchase 跳过 `hasActiveMonthlyPlan` 检查**：B2B 月包存在不应阻止批次 token 计入
- **batch 分支必须在 `config.tokenLimit` null check 之前**：batch 模式 token limit 来自批次而非 config
- 批次过期时 `getMemberBatchUsageSummary.isEffective = false` → 返回 0

#### `getSummary` - self_purchase 模式适配

- 查询 `enterprisePostExpiryPurchaseConfig` 推导 `isSelfPurchase`，传入 `isUsableInBillingContext` 和 `resolveLegacyB2BAvailableTokens`
- **accountValidity 双源回退**：优先 C端月包日期 → 无则回退 `computeAccountValidity`（批次有效期）
- **legacyB2BAvailableTokens 仅非 self_purchase 受 `hasActiveMonthlyPlan` 拦截**

#### `resolveConsumableBatchesInternal`（billing 批次解析）

- `hasActiveMonthlyPlan = hasActiveB2BPlan || hasActiveConsumerMonthlyPlan`（B2B 月包有效时短路不查 consumer）
- self_purchase 模式：无 B2B 月包时 fallthrough 查 consumer 月包
- **`isSelfPurchase` 用 `let` 声明在函数级，不在 `if` 块内**（修复 var/const 作用域 bug：消费路径永远读到 undefined）

#### `assertSelfPurchaseAccountValidity`（self_purchase 账户有效期检查）

- **双重检查**：先查 C端月包 → 无则查批次有效性
- 仅当 C端月包无效 **且** 批次过期（`getMemberBatchUsageSummary.isEffective = false`）时抛出 `ACCOUNT_EXPIRED`
- 批次有效时即使无 C端月包也允许使用（批次有效期作为账户有效期门控）

#### `grantConsumerMonthlyPlan` - 批次窗口后推日

- **`effectiveStart` 推进到批次窗口结束日的次日**（`addBillingBusinessDays(validTo, 1)`），不再是同一日
- 1天套餐不再显示为同日（如 7/24~7/24），正确为次日（7/25~7/25）
- 队列中后续批次同样使用 `addBillingBusinessDays` 推进

#### `allocateMonthlySeatEntitlement`（席位分配排队）

- **B端席位只查 B端 sourceType**（`b2b_monthly_seat_plan`, `b2b_enterprise_plan`），C端包不参与排队
- `findEarliestAvailableSlot`：**即使空档 < periodDays，也返回空档开始日期**（优先早激活）

#### `calculateUserTimeWindow`（时间线计算）

- **B端和 C端月包分离排队**：B端（batch + b2b_*）和 C端（consumer_monthly_plan）各自独立时间线
- 合并检测 currentWindow/queue，但各自条目不互相阻塞

### 前端实现要点（ZclawShell.tsx）

#### `resolveVisibleTokenBalance`（Token 余额显示）

- 增加 `postExpiryPurchaseMode` 参数
- batch 模式：`self_purchase` + 有C端包 → 用 `entitlementSummary.availableTokens`
- batch 模式：`contact_admin` / `admin_purchase` → 用 `legacyQuota`（批次数据）

#### `resolveValidityDates`（有效期显示）

- 增加 `postExpiryPurchaseMode` 参数
- `self_purchase` → 用 `entitlementSummary.accountValidity`（C端包日期）
- `contact_admin` / `admin_purchase` → 用 `legacyTokenQuota.windowStart/windowEnd`（批次日期）

#### `accountValidity` 变量（账户有效期块）

- 非self_purchase 模式 + `legacyTokenQuota.windowEnd` 存在 → 用批次/席位日期构建 `AccountValidityInfo`，覆盖 `entitlementSummary.accountValidity`
- `status` 用 `legacyTokenQuota.isBatchExpired`（已修复：有 B2B 席位时 `isBatchExpired = false`）

### Common Mistake: computeAccountValidity 返回错误日期

**Symptom**: contact_admin / admin_purchase 模式显示 C端包日期（如 08-13）而非批次日期（07-21）
**Cause**: `computeAccountValidity` 优先查 `monthly_plan` entitlement batch（含 consumer_monthly_plan），返回C端包 validUntil
**Fix**: contact_admin / admin_purchase 模式跳过 `computeAccountValidity`，直接查 `zclawEnterpriseTokenQuotaMember.batch.validTo`
**Prevention**: 前端 + 后端都按 `postExpiryMode` 选择数据源，不依赖单一 API 响应

### Common Mistake: 批次过期 token 仍参与叠加

**Symptom**: 批次过期（validTo 07-21），UI 仍显示 ~10,000,000 可用 token
**Cause**: `getMyEnterpriseTokenQuotaSummary` 的 `totalGranted = batchTokenLimit + packageTokenGranted` 始终包含批次 limit
**Fix**: 批次过期时 `effectiveBatchTokenLimit = 0`，`effectiveBatchRemaining = 0`
**Prevention**: 所有 token 计算点都检查 `isBatchExpiredRaw`

### Common Mistake: `isSelfPurchase` 作用域 bug

**Symptom**: self_purchase 用户消费 token 时仍扣 B2B 包而非 C端包
**Cause**: `resolveConsumableBatchesInternal` 中 `const isSelfPurchase` 在 `if` 块内声明，块外 `var isSelfPurchase` 在 `else` 块才赋值。当 `enterpriseTokenBatchQuotaService` 存在时 `isSelfPurchase` 为 `undefined`
**Fix**: 函数级 `let isSelfPurchase = false`，`if` 块内仅赋值不声明
**Prevention**: 避免在 `if/else` 分支分别声明同名变量，用 `let` 提升到统一作用域

### Common Mistake: `config.tokenLimit = null` 阻断 batch token

**Symptom**: batch 有效但 self_purchase 用户不显示批次 token
**Cause**: `resolveLegacyB2BAvailableTokens` 中 `if (!config?.tokenLimit) return 0n` 在 batch 分支**之前**执行。batch 模式 token limit 来自批次（`batchSummary.tokenLimit`），但 quota config 的 `tokenLimit` 可能为 null
**Fix**: batch 分支移到 `tokenLimit` null check 之前
**Prevention**: batch 模式的 token 数据流与 quota config tokenLimit 无关，不应受其约束

### Common Mistake: `sumTokenUsageInWindow` SQL 隐式时区转换

**Symptom**: contact_admin/self_purchase/admin_purchase 模式可用 Token 不随消费减少；token 明细有扣减记录但 `sumTokenUsageInWindow` 返回 0

**Cause**: `enterprise-token-batch-quota.service.ts` 的 `sumTokenUsageInWindow` 将 JS `Date` 对象直接传入 `$queryRaw`。Prisma/node-postgres 发送带 `Z`/`+00:00` 时区标记的参数，PostgreSQL 对 `timestamp without time zone` 列隐式转换为服务器时区（Asia/Shanghai +8），导致窗口起止时间移位 8 小时

**Fix**: 将 `Date` 格式化为无时区 UTC 字符串 `YYYY-MM-DD HH24:MI:SS.MS`，配合 `::timestamp` 强转

```typescript
// Before (broken — 0 tokens returned)
AND "createdAt" >= ${validFrom}
AND "createdAt" <= ${validTo}

// After (correct)
const fromStr = validFrom.toISOString().replace("T", " ").replace("Z", "");
const toStr = validTo.toISOString().replace("T", " ").replace("Z", "");
// ...
AND "createdAt" >= ${fromStr}::timestamp
AND "createdAt" <= ${toStr}::timestamp
```

**Prevention**: `$queryRaw` 传 `Date` 参数到 `timestamp without time zone` 列时，始终用字符串 + `::timestamp`，避免 PostgreSQL 隐式时区转换

## Common Mistake: ESM `require()` in Production Build

**Symptom**: `ensureDefaultBatch` throws `ReferenceError: require is not defined` in Docker/production build. Local dev passes because `tsx` tolerates CJS/ESM mix.

**Cause**: `const batchId = require("crypto").randomUUID()` — the project uses `"type": "module"`, so `require` is not available at runtime.

**Fix**: Use ESM import instead:
```typescript
import { randomUUID } from "node:crypto";
const batchId = randomUUID();
```

**Prevention**: Always run `pnpm --filter @insightweaver/api build` (TypeScript compilation) before pushing. `tsx --test` alone does not catch ESM/CJS incompatibility.

## C 端企业默认行为模式（Consumer Enterprise Default Pattern）

### 问题

Consumer / evomind_consumer 企业**不创建** `EnterprisePostExpiryPurchaseConfig` 和 `ZclawEnterpriseConversationQuotaConfig` 配置行——这两张表是 B 端概念。但多个后端函数在配置缺失时默认走了 B 端逻辑，导致：

| 症状 | 根因函数 | 错误默认值 |
|------|---------|-----------|
| 存储配额显示 0 | `getEnterpriseWorkspaceQuotaConfig:10786` | `postExpiryMode ?? "admin_purchase"` → 查 B 端 source types |
| 账号有效期不显示 | `getSummary:1047` | `quotaConfig?.quotaMode === 'batch'` 为 false → 跳过计算 |
| Token 消费不走 billing 路径 | `resolveQuotaContext:2077` | `postExpiryConfig?.mode === 'self_purchase'` 为 false → `useBillingEntitlements = false` |
| 账户有效期校验被跳过 | `assertSelfPurchaseAccountValidity:2133` | `postExpiryConfig?.mode !== "self_purchase"` → 直接 return |

### 原则

**C 端企业不看 `postExpiryPurchaseConfig` 和 `quotaConfig` 配置表。** 这两张表是 B 端概念。C 端企业始终使用 C 端逻辑：

- **存储配额**：只看 `consumer_monthly_plan` / `consumer_storage_topup` 等 C 端 source types
- **Token 消费**：始终走 billing 路径（freeze → capture → release）
- **账户有效期**：直接从月包 entitlement batch 的 `validFrom`/`validUntil` 计算
- **账户有效期门控**：检查 `hasActiveConsumerMonthlyPlan`

### 实现模式

在所有读取 `postExpiryPurchaseConfig` 或 `quotaConfig` 的函数中，**先判断 `isConsumerEnterprise`，再读配置**：

```typescript
// ✅ CORRECT: 模式
const enterprise = await this.prisma.enterprise.findFirst({
  where: { id: enterpriseId, isDeleted: false },
  select: { enterpriseKind: true },
});
const isConsumerEnterprise =
  enterprise?.enterpriseKind === "consumer" ||
  enterprise?.enterpriseKind === "evomind_consumer";

// 然后根据 isConsumerEnterprise 决定行为，不依赖 postExpiryConfig
if (isConsumerEnterprise) {
  allowedStorageSourceTypes = CEND_SOURCE_TYPES;  // 存储配额
}
// isSelfPurchaseWithConsumerEntitlement 也应包含 isConsumerEnterprise
```

```typescript
// ❌ WRONG: 依赖可能不存在的配置表
const postExpiryMode = postExpiryConfig?.mode ?? "admin_purchase";
if (postExpiryMode === "self_purchase") { /* C端逻辑 */ }
```

### 受影响函数清单（需全部覆盖）

| 函数 | 文件 | 行号 | 修复要点 |
|------|------|------|---------|
| `getEnterpriseWorkspaceQuotaConfig` | `zclaw.service.ts` | ~10799 | C 端企业强制 `allowedStorageSourceTypes = CEND_SOURCE_TYPES` |
| `getSummary` | `entitlement.service.ts` | ~1047 | C 端企业直接从 `activeMonthlyPlans` 取有效期，不等 `quotaConfig` |
| `resolveQuotaContext` | `zclaw.service.ts` | ~2077 | `isConsumerEnterprise` 时 `useBillingEntitlements = true` |
| `assertSelfPurchaseAccountValidity` | `zclaw.service.ts` | ~2133 | `isConsumerEnterprise` 时不跳过有效期校验 |
| `resolveAccountValidityDisplay` (FE) | `account-validity-display.ts` | ~29 | `quotaMode == null` 时也允许展示有效期 |

### 前端配合

`resolveAccountValidityDisplay` 的 `hasAccountValidity` 条件从：

```typescript
// ❌ WRONG: 强制要求 batch mode
const hasAccountValidity = isBatch && Boolean(input.accountValidity);
```

改为：

```typescript
// ✅ CORRECT: C 端企业 quotaMode 为 null 时也允许展示
const hasAccountValidity = Boolean(input.accountValidity) &&
  (isBatch || input.quotaMode == null);
```

### 测试要点

1. consumer 企业无 `EnterprisePostExpiryPurchaseConfig` 行时，存储配额 = 月包 storage batch 总和
2. consumer 企业无 `ZclawEnterpriseConversationQuotaConfig` 行时，`accountValidity` 非 null
3. consumer 企业 `useBillingEntitlements = true`（不管配置是否存在）
4. consumer 企业月包过期时，`assertSelfPurchaseAccountValidity` 抛出 `ACCOUNT_EXPIRED`
5. consumer 企业 Token 耗尽（`remainingAmount = 0`）时，`freezeEntitlements` 抛出 `INSUFFICIENT_CREDITS`

## B2B Batch 窗口 ≠ Billing 权益（hasActiveBatchWindowForUser 误判）

### 问题

B2B 企业（`quotaMode = batch`，`postExpiryMode = self_purchase`），用户只有 zclaw 批次没有 entitlement batch 时，发消息报 "Token 额度已用尽"。

### 根因

`hasConsumableBillingTokenEntitlement`（`entitlement.service.ts:1284`）中：

```typescript
// ❌ 问题代码
if (await this.hasActiveBatchWindowForUser(...))  return true;
```

`hasActiveBatchWindowForUser` 检查的是 zclaw 批次窗口是否活跃。用户在批次中 → 返回 `true` → `hasConsumableBillingTokenEntitlement = true` → `resolveQuotaContext` 设置 `useBillingEntitlements = true` → 走 billing 路径 → `freezeEntitlements` 找不到任何 entitlement batch → 抛 `INSUFFICIENT_CREDITS`。

**核心矛盾**：zclaw 批次活跃 ≠ 有 billing 权益可消费。批次走 legacy 路径，billing 走 entitlement batch 路径，两者不能混用。

### 修复

删除 `hasActiveBatchWindowForUser` 的短路返回。B2B 企业只在以下情况返回 `true`：
1. 有企业级 B2B 月包（`hasActiveB2BMonthlyPlan`）
2. 用户实际持有自购的 token entitlement batch（`remainingAmount > 0`）

```typescript
// ✅ 修复后：batch 窗口不再误导走 billing
if (await this.hasActiveB2BMonthlyPlan(...)) return true;
// hasActiveBatchWindowForUser 检查已删除 —— batch 走 batch 路径
const selfPurchased = await this.prisma.entitlementBatch.findMany({...});
if (selfPurchased.some(b => this.isEffectiveActive(b, now))) return true;
```

### 消费路径优先级（B2B self_purchase）

| 用户持有 | 消费路径 | 说明 |
|----------|---------|------|
| zclaw 批次（无 C 端套餐） | legacy batch 路径 | `useBillingEntitlements = false`，批次 token 扣减 |
| zclaw 批次 + C 端套餐 token | legacy batch 路径 | 批次优先，C 端套餐 token **暂不叠加消费**（显示叠加，消费走批次） |
| 无批次，有 C 端套餐 | billing 路径 | `useBillingEntitlements = true`，freeze/capture C 端 token |

### 与 C 端企业模式的关系

- **C 端企业**：无批次，`isConsumerEnterprise` 强制走 billing（前面的修复）
- **B2B self_purchase**：有批次走批次路径，有 entitlement 走 billing 路径，两者不混淆

### 测试要点

1. B2B batch 模式 + 用户有批次无 entitlement → `hasConsumableBillingTokenEntitlement = false`
2. B2B batch 模式 + 用户有批次 + 有 C 端 token batch → `hasConsumableBillingTokenEntitlement = true`
3. B2B batch 模式 + 用户有批次无 entitlement → `useBillingEntitlements = false`，`assertBatchTokenQuotaAvailable` 正常执行

## Token 模式：tokenLimitSnapshot 同步与 Admin 排除

### 问题

Admin 在后台将 `tokenLimit` 从 1000 万改为 2000 万后，前端仍显示可用 Token 为 0。

### 根因（两处 bug）

**Bug 1**：`resetVersion` 仅在 `conversationLimit` 变更时递增，`tokenLimit` 变更被忽略（`zclaw.service.ts:2503-2506`）：

```typescript
// ❌ 只检查了 conversationChanged
const resetVersion = conversationChanged
  ? (existing?.resetVersion ?? 0) + 1
  : (existing?.resetVersion ?? 0);
```

**Bug 2**：`syncEnterpriseTokenLimitSnapshots` 排除了 admin/owner（`enterprise-token-quota.service.ts:166`）：

```sql
-- ❌ admin 的快照不更新
AND membership."role" NOT IN ('admin', 'owner')
```

Admin 改配额 → `syncEnterpriseTokenLimitSnapshots` 跳过 admin → admin 的 `tokenLimitSnapshot` 停留在旧值 → `resolveEffectiveTokenLimit` 优先取 snapshot → 显示不更新。

### 修复

```typescript
// ✅ tokenLimit 变更也触发 resetVersion
const resetVersion =
  conversationChanged || tokenChanged
    ? (existing?.resetVersion ?? 0) + 1
    : (existing?.resetVersion ?? 0);
```

```sql
-- ✅ 所有活跃成员（包括 admin）的快照都更新
--    删除了 AND membership."role" NOT IN ('admin', 'owner')
```

### Admin 门控设计

Admin/owner 角色的 Token 配额门控**故意跳过**（`enterprise-token-quota.service.ts:36`），消费不限额但照常记录 settlement。这是设计行为，非 bug。Admin 的 `tokenLimitSnapshot` 仅用于前端展示，不参与门控。快照同步不应排除 admin。

---

## 代码质量改进（2026-07-23）

### Promise.all 并行化

`resolveQuotaContext` 中 4 个独立查询（quotaConfig、hasConsumableBillingEntitlement、postExpiryConfig、enterprise）串行执行会导致不必要的延迟。使用 `Promise.all` 并行化可减少热路径延迟。

```typescript
// ✅ 并行化独立查询
const [quotaConfigResult, hasConsumableBillingEntitlement, postExpiryConfig, enterprise] = await Promise.all([
  this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({ ... }),
  this.hasConsumableBillingTokenEntitlement(enterpriseId, userId),
  this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({ ... }),
  this.prisma.enterprise.findFirst({ ... }),
]);
```

### QuotaContext 传递 enterpriseKind

`assertSelfPurchaseAccountValidity` 和 `resolveQuotaContext` 都查询 `enterprise.findFirst` 获取 `enterpriseKind`。当 `assertEnterpriseTokenQuotaIfNeeded` 先调用 `resolveQuotaContext` 再调用 `assertSelfPurchaseAccountValidity` 时，会产生重复查询。

**解决方案**：`QuotaContext` 增加 `enterpriseKind` 字段，`assertSelfPurchaseAccountValidity` 接收可选参数复用。

```typescript
export interface QuotaContext {
  quotaMode?: string;
  useBillingEntitlements: boolean;
  hasConsumableBillingEntitlement: boolean;
  enterpriseKind?: string | null;  // ✅ 避免重复查询
}

private async assertSelfPurchaseAccountValidity(
  enterpriseId: string,
  userId: string,
  enterpriseKind?: string | null,  // ✅ 可选参数
) {
  const effectiveEnterpriseKind = enterpriseKind ?? (await this.prisma.enterprise.findFirst({ ... }))?.enterpriseKind;
  // ...
}
```

### isConsumerEnterpriseKind 统一使用

C 端企业类型检查应使用 `isConsumerEnterpriseKind`（来自 `@insightweaver/shared`），而非内联 `=== "consumer" || === "evomind_consumer"`。

```typescript
// ❌ 内联检查（重复 5 次）
const isConsumerEnterprise =
  enterprise?.enterpriseKind === "consumer" ||
  enterprise?.enterpriseKind === "evomind_consumer";

// ✅ 使用共享工具函数
import { isConsumerEnterpriseKind } from "@insightweaver/shared";
const isConsumerEnterprise = isConsumerEnterpriseKind(enterprise?.enterpriseKind);
```

### computeValidityStatus 辅助函数

`entitlement.service.ts` 中 validity status 计算逻辑（daysUntilExpiry + 三元表达式）重复 4 次。提取为共享函数消除重复。

```typescript
function computeValidityStatus(
  validFrom: Date,
  validUntil: Date,
  now: Date,
): { validFrom: string; validUntil: string; status: "active" | "expiring_soon" | "expired" } {
  const daysUntilExpiry = Math.ceil(
    (validUntil.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
  );
  let status: "active" | "expiring_soon" | "expired";
  if (daysUntilExpiry <= 0) {
    status = "expired";
  } else if (daysUntilExpiry <= 7) {
    status = "expiring_soon";
  } else {
    status = "active";
  }
  return { validFrom: validFrom.toISOString(), validUntil: validUntil.toISOString(), status };
}
```

### 死代码删除：self_purchase 冗余查询

`getSummary` 的 `self_purchase` 分支中，`consumer_monthly_plan` DB 查询是冗余的：
- 如果有效 plan 存在，已在 `activeMonthlyPlans` 内存过滤中找到（使用更严格的 `isEffectiveActive`）
- 如果内存中未找到，DB 查询（使用更宽松的条件）也不可能找到
- 直接调用 `computeAccountValidity` 即可

---

## 统一账户资源判定（2026-07-23）

### 问题

之前账户资源判定逻辑分散在多个服务中，存在 6 处不一致：

1. **状态计算粒度**：`computeValidityStatus` 用天级 `Math.ceil`，`validityStatus` 用毫秒级
2. **月包状态过滤**：`computeAccountValidity` 只用 `status: "active"`，`getSummary` 用 `isEffectiveActive`（含 scheduled）
3. **B2B 月包 frozen 处理**：`default-quota-policy` 不排除 frozen，`entitlement.service` 排除
4. **Batch 回退顺序**：`assertActiveMonthlyPlanForTopup` 先查 membership 再查 window，`getSummary` 只查 window
5. **Consumer 月包 sourceType**：`entitlement.service` 不过滤 sourceType，`zclaw.service` 过滤
6. **前后端不一致**：前端重新计算后端已提供的值

### 解决方案

**1. 共享工具函数**（`packages/shared/src/account-validity.ts`）

```typescript
// 统一状态计算
export function computeValidityStatus(validFrom: Date, validUntil: Date, now: Date): AccountValidityInfo;

// 统一活跃判断（排除 voided/expired/frozen）
export function isBatchEffectivelyActive(status: string, validFrom: Date, validUntil: Date | null, now: Date): boolean;
```

**2. 扩展 workspaceUsage 为单一数据源**

`getWorkspaceUsageSummary` 新增字段（从 EntitlementSummary 合并）：

```typescript
interface ZclawWorkspaceUsageResponse {
  // ... existing fields ...
  availableTokens?: string | null;
  availableStorageBytes?: string | null;
  accountValidity?: { validFrom: string; validUntil: string; status: string } | null;
}
```

前端只需调用 `/api/zclaw/workspace/usage` 一个接口获取所有资源信息。

**3. 统一判断逻辑**

- `isEffectiveActive` 统一使用 `isBatchEffectivelyActive`
- `computeAccountValidity` 返回字符串日期（与 API 响应格式一致）
- `default-quota-policy.service.hasActiveB2BMonthlyPlan` 排除 frozen 状态
- `assertActiveMonthlyPlanForTopup` 优先检查 batch membership（简单直接）

### 设计原则

1. **单一数据源**：`getWorkspaceUsageSummary` 作为前端资源显示的唯一来源
2. **共享工具函数**：跨服务重复逻辑提取到 `@insightweaver/shared`
3. **并行查询**：独立 DB 查询使用 `Promise.all` 减少延迟
4. **前端不重算**：后端提供所有需要的字段，前端只做展示逻辑

---

## 前端有效性判定规则（2026-07-24）

### 前端所有有效性检查必须使用 `workspaceUsage.accountValidity`

**错误模式**（只查月包，遗漏 batch）：
```typescript
// ❌ BillingPurchaseDialog 旧代码
const hasMonthlyPlan = postExpiryPurchaseMode === 'self_purchase'
  ? Boolean(summary.activeMonthlyPlans?.length)  // 只查 consumer_monthly_plan
  : Boolean(summary.hasActiveMonthlyPlan);
```

**正确模式**：
```typescript
// ✅ 使用 accountValidity（后端已综合月包 + batch 回退）
const canPurchase = accountValidity !== null && accountValidity.status !== 'expired';
```

### 受影响的前端位置

| 组件 | 正确字段 | 说明 |
|------|---------|------|
| `ZclawShell.canPurchaseBillingPlan` | `accountValidity?.status !== 'expired'` | 控制购买入口显示 |
| `BillingPurchaseDialog.hasActiveMonthlyPlan` | `accountValidity?.status !== 'expired'` | 阻止 topup 购买 |
| `SuperLobsterPage` 过期拦截 | `accountValidity?.status === 'expired'` | 阻止消息发送 |
| `resolveAccountValidityDisplay` | `accountValidity` 直接传入 | badge 显示 |

### `accountValidityExpired` 字段不存在

后端 `getWorkspaceUsageSummary` 从未设置 `accountValidityExpired` 布尔字段。
前端类型定义中有此字段但实际始终为 `undefined`。
**正确做法**：使用 `accountValidity?.status === 'expired'`。

---

## Topup 购买校验链路（2026-07-24）

### 前端拦截（`BillingPurchaseDialog`）

```
handleCreateOrder:
  if (isTopupPlan && !hasActiveMonthlyPlan) {
    toast.error('请先购买并生效月包后再购买补充包');
    return;  // ← 不发 API 请求
  }
  await createBillingOrderApi(...);
```

`hasActiveMonthlyPlan` 必须使用 `accountValidity`（包含 batch 回退），
否则有 active batch 但无 active 月包的用户会被前端错误拦截。

### 后端校验（`assertActiveMonthlyPlanForTopup`）

```
1. 查 active consumer_monthly_plan（status in ['active','scheduled'], validFrom<=now, validUntil>now）
2. hasActiveBatchMembership（zclaw batch member + batch.active + validTo>=now）
3. hasActiveBatchWindowForUser（calculateUserTimeWindow）
4. 全部失败 → 抛 BadRequestException
```

检查顺序：batch membership **优先于** batch window（更简单直接）。

---

## 有效期 Badge 布局规则（2026-07-24）

### 问题

Validity 行包含三个元素：标签 + 日期 + Badge。
当容器宽度不足时，Badge 会与日期文本重叠。

### 解决方案

使用 `flex-shrink` 让日期文本优先收缩，而非 `overflow-hidden` 截断 Badge：

```typescript
<div className="flex items-center gap-2">
  <span className="shrink-0">Validity</span>  {/* 标签固定 */}
  <div className="min-w-0 flex-shrink">        {/* 日期优先收缩 */}
    <span className="truncate">Valid until 2026-07-24</span>
  </div>
  <span className="shrink-0">Expiring soon</span>  {/* Badge 固定 */}
</div>
```

### 规则

1. **Label**: `shrink-0` — 始终显示
2. **日期文本**: `flex-shrink` + `truncate` — 空间不足时省略号截断
3. **Badge**: `shrink-0` — 始终完整显示

**不要使用** `overflow-hidden` — 会截断 Badge 但日期文本仍延伸造成重叠。

---

## 批次状态自动同步（2026-07-24）

### 问题

`entitlement_batches.status` 字段只在创建时通过 `statusForPeriod` 设置一次：
- `validFrom > now` → `scheduled`
- `validUntil <= now` → `expired`
- 其余 → `active`

之后无定时任务更新状态。导致 `validFrom` 已到达的 scheduled 批次始终停留在 scheduled，影响配额计算和展示。

### 修复

1. `EntitlementService.activateScheduledBatches(now)` — TDD 实现
   - 查找 status='scheduled' AND validFrom<=now AND validUntil>now 的批次
   - 更新为 active
   - 创建 activate 类型的 ledger

2. 集成到 `EntitlementExpiryScheduler.runOnce()` — 每天执行

```typescript
const activateResult = await this.entitlementService.activateScheduledBatches(now);
```

3. `expireEntitlements` 已覆盖 frozen/active/scheduled → expired（无需额外实现）

### 影响

部署后首次执行会修复存量 scheduled 批次。之后 scheduled 计划在 validFrom 到达后 24h 内自动激活。

---

## 购买入口策略（2026-07-24）

### 前端

```
canPurchaseBillingPlan:
  C-end → 始终 true（月包始终可买，用于续期）
  B2B self_purchase → true
  B2B admin_purchase → owner/admin 才可

BillingPurchaseDialog.handleCreateOrder:
  topup + !hasActiveMonthlyPlan → toast.warning 提示，不阻止提交
  后端 assertActiveMonthlyPlanForTopup 做最终校验
```

### 后端（最终防线）

```
assertActiveMonthlyPlanForTopup:
  CONSUMER topup:
    1. consumer_monthly_plan (active|scheduled, validFrom<=now, validUntil>now)
    2. hasActiveBatchMembership (zclaw batch)
    3. hasActiveBatchWindowForUser
    4. → throw BadRequestException
```

### 原则

- **月包永远可买**（续期入口）
- **topup 前端提示不拦截**，后端最终校验
- **batch 和月包等同效力**（有其一即可买 topup）
