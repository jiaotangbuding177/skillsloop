# Research: Batch Mode Quota Configuration — Implementation vs Requirements

- **Query**: Compare current implementation against product requirements for batch mode quota configuration across three purchase behaviors (contact_admin / admin_purchase / self_purchase)
- **Scope**: internal
- **Date**: 2026-07-21

---

## Executive Summary

1. **Purchase flow gating is well-implemented**: `contact_admin` blocks all plan visibility/purchase; `admin_purchase` shows only B2B plans to admin/owner; `self_purchase` shows consumer plans to all members. Backend and frontend are aligned.
2. **Batch management permission gap**: Both platform admin (超管, `AdminGuard`) and enterprise admin (`assertEnterpriseAdminOrOwner`) can CRUD token quota batches. The requirement states that in `admin_purchase` mode, ALL batch operations should be **platform admin only** — enterprise admin should not have batch CRUD access in this mode.
3. **Frontend `b2b_monthly_seat_plan` missing from BillingPurchaseDialog**: The backend `B2B_PLAN_TYPES` includes `b2b_monthly_seat_plan`, but the frontend `BillingPurchaseDialog.tsx` B2B_PLAN_TYPES array does not. Plans of this type returned by the API are silently filtered out in the UI.
4. **Topup prerequisite validation matches requirements**: Both consumer and B2B topups correctly require an active monthly plan OR an active batch window (`hasActiveBatchWindowForUser`), enforced at both API and UI layers.
5. **Quota calculation in batch mode is correct**: `getEnterpriseWorkspaceQuotaConfig` properly gates on `computeAccountValidity` — expired accounts get `quotaBytes = 0`, and active batch members get `baseQuotaBytes + packageStorageBytes`.

---

## Per-Mode Analysis

### 1. contact_admin (联系管理员)

**Requirement**: Users CANNOT see or buy any plans. Only admin manages batches via admin backend.

#### Purchase Flow

| Layer | Implementation | File:Line |
|---|---|---|
| `listPreview` | `assertPreviewAccess` throws `ForbiddenException('当前企业模式下不可查看计费套餐')` when mode is `contact_admin` | `billing-plan.service.ts:578-579` |
| `createOrder` | Throws `ForbiddenException('当前企业模式下不允许在线购买套餐')` for both consumer and B2B plans | `billing-order.service.ts:85-86, 98-99` |
| Frontend `canPurchaseBillingPlan` | Returns `false` when `postExpiryPurchaseMode` is not `self_purchase` or `admin_purchase` | `ZclawShell.tsx:1106-1116` |
| Frontend purchase button | Hidden when `canPurchaseBillingPlan` is false | `ZclawShell.tsx:1182-1190` |
| `WorkspaceIdentityMetaPanel` | `effectivePurchaseMode` defaults to `"contact_admin"` → no renew button, no "contact admin" text shown (actionType = "none") | `ZclawShell.tsx:366-369`, `account-validity-display.ts:39-44` |

**Verdict**: ✅ MATCH — Users cannot see or purchase plans.

#### Batch Management

| Layer | Implementation | File:Line |
|---|---|---|
| Platform admin routes | `zclaw-admin.controller.ts` with `@UseGuards(JwtAuthGuard, AdminGuard)` — full batch CRUD | `zclaw-admin.controller.ts:34, 124-165` |
| Enterprise admin routes | `zclaw.controller.ts` `enterprise-admin/token-quota-batches/*` — calls `assertEnterpriseAdminOrOwner` | `zclaw.controller.ts:220-304`, `zclaw.service.ts:1769-1773` |

**Verdict**: ⚠️ PARTIAL — Both platform admin AND enterprise admin can manage batches. The requirement says "only admin manages batches via admin backend" which is ambiguous — it could mean platform admin only, or enterprise admin too. **Needs clarification**.

---

### 2. admin_purchase (管理员代购)

**Requirement**: Platform admin configures B2B seat monthly plan (`b2b_monthly_seat_plan`), token topup (`b2b_token_topup`), storage topup (`b2b_storage_topup`). Enterprise admin/owner purchases. ALL batch operations are platform admin only. Topup requires valid batch OR valid B2B seat monthly plan.

#### Purchase Flow

| Layer | Implementation | File:Line |
|---|---|---|
| `listPreview` | Filters to `B2B_PLAN_TYPES` = `['b2b_enterprise_plan', 'b2b_monthly_seat_plan', 'b2b_token_topup', 'b2b_storage_topup']`; requires `admin` or `owner` role | `billing-plan.service.ts:72-73, 581-583` |
| `createOrder` | Allows B2B plans only when mode is `admin_purchase`; calls `assertEnterpriseAdminOrOwner` | `billing-order.service.ts:96-107` |
| Frontend `canPurchaseBillingPlan` | Returns `true` only for `admin`/`owner` roles | `ZclawShell.tsx:1110-1111` |
| Frontend plan filtering | `BillingPurchaseDialog` filters by `B2B_PLAN_TYPES` = `['b2b_enterprise_plan', 'b2b_token_topup', 'b2b_storage_topup']` — **MISSING `b2b_monthly_seat_plan`** | `BillingPurchaseDialog.tsx:20-24` |

**Verdict**: ⚠️ GAP — Backend returns `b2b_monthly_seat_plan` plans, but frontend silently filters them out. Enterprise admin cannot see/purchase `b2b_monthly_seat_plan` in the UI even though the API allows it.

#### Topup Prerequisite

| Layer | Implementation | File:Line |
|---|---|---|
| B2B topup validation | Checks for active `b2b_enterprise_plan` or `b2b_monthly_seat_plan` entitlement batch (enterprise-level, `userId: null`); falls back to `hasActiveBatchWindowForUser` | `billing-order.service.ts:424-448` |
| Frontend topup gating | `BillingPurchaseDialog` checks `hasActiveMonthlyPlan` from entitlement summary; blocks topup selection if false | `BillingPurchaseDialog.tsx:442-444, 534-536` |

**Verdict**: ✅ MATCH — Topup requires valid B2B monthly plan OR active batch window.

#### Batch Management Permissions

| Layer | Implementation | File:Line |
|---|---|---|
| Platform admin | Full CRUD via `zclaw-admin.controller.ts` (AdminGuard) | `zclaw-admin.controller.ts:124-165` |
| Enterprise admin | Also has full CRUD via `zclaw.controller.ts` enterprise-admin routes (`assertEnterpriseAdminOrOwner`) | `zclaw.controller.ts:220-304`, `zclaw.service.ts:1816-1821` |
| Mode check | `createEnterpriseTokenQuotaBatchForAdmin` checks `quotaMode === 'batch'` but does NOT check `postExpiryPurchaseMode` | `zclaw.service.ts:1787-1788` |

**Verdict**: ❌ GAP — Requirement says "ALL batch operations are done by **platform admin only**" in `admin_purchase` mode. Currently enterprise admin also has full batch CRUD access. No `postExpiryPurchaseMode` check exists in batch management methods.

---

### 3. self_purchase (用户自购)

**Requirement**: Platform admin configures C-end monthly plan (`consumer_monthly_plan`), token topup (`consumer_token_topup`), storage topup (`consumer_storage_topup`). Users buy directly, takes effect immediately. Topup requires valid C-end monthly plan. Multiple monthly plans queue by effective date.

#### Purchase Flow

| Layer | Implementation | File:Line |
|---|---|---|
| `listPreview` | Filters to `CONSUMER_PLAN_TYPES` = `['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup']`; allows all active members | `billing-plan.service.ts:74-75, 584` |
| `createOrder` | Allows consumer plans when mode is `self_purchase`; requires active membership | `billing-order.service.ts:82-94` |
| Frontend `canPurchaseBillingPlan` | Returns `true` for all active members | `ZclawShell.tsx:1109` |
| Frontend plan filtering | `BillingPurchaseDialog` filters by `CONSUMER_PLAN_TYPES` = `['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup']` | `BillingPurchaseDialog.tsx:25-29` |

**Verdict**: ✅ MATCH — All members can see and purchase consumer plans.

#### Topup Prerequisite

| Layer | Implementation | File:Line |
|---|---|---|
| Consumer topup validation | Checks for active `consumer_monthly_plan` entitlement batch (user-level); falls back to `hasActiveBatchWindowForUser` | `billing-order.service.ts:398-421` |
| Frontend topup gating | Same as admin_purchase — checks `hasActiveMonthlyPlan` | `BillingPurchaseDialog.tsx:442-444` |

**Verdict**: ✅ MATCH — Topup requires valid consumer monthly plan OR active batch window.

#### Monthly Plan Queuing

| Layer | Implementation | File:Line |
|---|---|---|
| Grant logic | `grantConsumerMonthlyPlan` creates entitlement batches with `validFrom`/`validUntil` based on plan `periodDays` | `entitlement.service.ts:4929+` |
| Multiple plans | Entitlement batches support `scheduled` status with future `validFrom`, enabling queuing | `entitlement.service.ts:497, 625` |

**Verdict**: ✅ MATCH — Multiple monthly plans can queue via scheduled entitlement batches.

---

## Quota Calculation Analysis (`getEnterpriseWorkspaceQuotaConfig`)

**File**: `zclaw.service.ts:10083-10276`

### Flow by enterprise kind and mode:

```
1. quotaMode === 'unlimited' → MAX_SAFE_INTEGER quota (short-circuit)
2. Consumer enterprise:
   a. hasActiveConsumerMonthlyPlan → packageStorageBytes (quotaSource: 'monthly_plan')
   b. hasAdminGrantEntitlement → adminGrantStorageBytes (quotaSource: 'admin_grant')
   c. else → 0 bytes (consumer_monthly_expired)
3. B2B with active monthly plan → packageStorageBytes (quotaSource: 'monthly_plan')
4. B2B without monthly plan:
   a. defaultQuotaEffective = false → 0 bytes (b2b_enterprise_entitlement_expired)
   b. defaultQuotaEffective = true:
      - quotaMode === 'batch':
        * computeAccountValidity → expired → 0 bytes (account_expired)
        * zclawMember batch not effective → baseQuotaBytes = 0
      - quotaBytes = baseQuotaBytes + packageStorageBytes
```

### Per-mode impact:

| Mode | Quota Calc Impact |
|---|---|
| `contact_admin` | No direct impact on quota calc. The mode only affects purchase visibility. Quota is determined by quotaMode (batch/conversation/token/unlimited) and entitlement state. |
| `admin_purchase` | B2B monthly plan → `packageStorageBytes` from entitlement batches. Without monthly plan → default quota + batch storage (if batch mode). |
| `self_purchase` | Consumer monthly plan → `packageStorageBytes`. Without → admin_grant or 0. In batch mode, `computeAccountValidity` gates access. |

### Batch mode specifics (`zclaw.service.ts:10236-10266`):

1. Calls `computeAccountValidity(enterpriseId, userId, now)` — if null or expired → `quotaBytes = 0`
2. Checks `ZclawEnterpriseTokenQuotaMember` — if member's batch is not currently effective → `baseQuotaBytes = 0`
3. Final: `quotaBytes = baseQuotaBytes + packageStorageBytes`

---

## Token Quota Settlement

**File**: `zclaw.service.ts:2149-2228`

### `settleEnterpriseTokenUsageIfNeeded` routing:

| quotaMode | Handler | Tables Used |
|---|---|---|
| `conversation` | `enterpriseTokenQuotaService.settleMessageTokenUsage` | Legacy token quota tables |
| `unlimited` | `enterpriseTokenQuotaService.settleMessageTokenUsage` | Legacy token quota tables (analytics only) |
| `token` | `enterpriseTokenQuotaService.settleMessageTokenUsage` | Legacy token quota tables |
| `batch` (with consumable billing entitlement) | `enterpriseTokenQuotaService.settleMessageTokenUsage` | Legacy token quota tables |
| `batch` (without consumable billing entitlement) | `enterpriseTokenBatchQuotaService.settleMessageTokenUsage` | `ZclawEnterpriseTokenQuotaBatch` + `ZclawEnterpriseTokenQuotaMember` + `ZclawEnterpriseTokenUsageSettlement` |
| default (no mode) | `enterpriseTokenQuotaService.settleMessageTokenUsage` | Legacy token quota tables |

### Batch settlement details (`enterprise-token-batch-quota.service.ts:445-508`):

1. Skips admin/owner roles (`ENTERPRISE_ADMIN_ROLES`)
2. Gets member batch context via `getMemberBatchContext`
3. Checks batch effectiveness (`isBatchCurrentlyEffective`)
4. Validates effective date window (member-level overrides batch-level)
5. Calculates weighted tokens via `estimateZclawWeightedTokens`
6. Creates idempotent settlement record (`zclaw-token-settle-{enterpriseId}-{userId}-{messageId}`)

**Note**: The settlement records token usage but does NOT decrement the batch's `tokenLimit`. The batch token limit appears to be a soft cap checked elsewhere (likely in the entitlement summary / streaming gate).

---

## Account Validity (`computeAccountValidity`)

**File**: `enterprise-token-batch-quota.service.ts:998-1090`

### Priority chain:

1. **Active monthly plan** (user-level `entitlementBatch` with `entitlementType: 'monthly_plan'`) → use its `validFrom`/`validUntil`
2. **Active batch window** (via `calculateUserTimeWindow`) → use batch `validFrom`/`validTo`
3. **Expired zclaw batch** (member exists, batch is active but `effectiveTo < now`) → return `status: 'expired'`
4. **Frozen batch** (entitlement batch with `status: 'frozen'`, non-topup) → return `status: 'expired'`
5. **None found** → return `null`

### Status determination (`validityStatus`):

- `remainingMs <= 0` → `expired`
- `remainingMs <= 7 days` → `expiring_soon` (inferred from frontend usage)
- else → `active`

---

## Frontend Gating

### `ZclawShell.tsx` — `canPurchaseBillingPlan` (line 1106-1116)

```typescript
if (enterpriseKind === "b2b") {
  if (postExpiryPurchaseMode === 'self_purchase') return true;      // all members
  if (postExpiryPurchaseMode === 'admin_purchase') {
    return ["owner", "admin"].includes(membershipRole);              // admin/owner only
  }
  return false;                                                      // contact_admin → hidden
}
return ["consumer", "evomind_consumer"].includes(enterpriseKind);    // C-end always
```

### `WorkspaceIdentityMetaPanel` (line 340-508)

- `effectivePurchaseMode`: C-end → always `"self_purchase"`; B2B → uses `postExpiryPurchaseMode` (default `"contact_admin"`)
- Account validity block: shown only in `batch` quotaMode
- Action buttons:
  - `self_purchase` → "续费" (renew) button → opens BillingPurchaseDialog
  - `admin_purchase` → "联系管理员续费" (contact admin) text
  - `contact_admin` → no action

### `BillingPurchaseDialog.tsx` (line 250-469)

- Fetches plans via `listBillingPlansPreviewApi`
- Filters by `allowedPlanTypes` based on `enterpriseKind` (B2B vs consumer)
- Fetches entitlement summary for `hasActiveMonthlyPlan`
- Topup plans disabled when `hasActiveMonthlyPlan !== true`
- Creates order via `createBillingOrderApi` with WeChat pay

### `account-validity-display.ts` (line 22-54)

- `showBlock`: only when `quotaMode === 'batch'` AND (has accountValidity OR has org)
- `actionType`: `self_purchase` → "renew", `admin_purchase` → "contact_admin", else → "none"

---

## Gap Analysis

| # | Requirement | Current Implementation | Status | Risk |
|---|---|---|---|---|
| G1 | `admin_purchase`: ALL batch operations by **platform admin only** | Enterprise admin also has full batch CRUD via `zclaw.controller.ts` enterprise-admin routes. No `postExpiryPurchaseMode` check in batch methods. | ❌ GAP | Medium — Enterprise admin can create/modify/assign batches in admin_purchase mode, contradicting the requirement. |
| G2 | `admin_purchase`: Platform admin configures `b2b_monthly_seat_plan` | Backend `B2B_PLAN_TYPES` includes `b2b_monthly_seat_plan`. Frontend `BillingPurchaseDialog` B2B_PLAN_TYPES does NOT include it — plans are silently filtered out. | ❌ GAP | High — Enterprise admin cannot purchase `b2b_monthly_seat_plan` through the UI despite backend support. |
| G3 | `contact_admin`: Users cannot see/buy plans | `listPreview` throws ForbiddenException; `createOrder` throws ForbiddenException; frontend hides purchase button. | ✅ MATCH | — |
| G4 | `admin_purchase`: Enterprise admin/owner purchases B2B plans | `listPreview` requires admin/owner role; `createOrder` calls `assertEnterpriseAdminOrOwner`; frontend gates by role. | ✅ MATCH | — |
| G5 | `self_purchase`: Users buy consumer plans directly | `listPreview` allows all active members; `createOrder` requires active membership; frontend shows for all. | ✅ MATCH | — |
| G6 | Topup requires valid monthly plan OR valid batch | `assertActiveMonthlyPlanForTopup` checks monthly plan then `hasActiveBatchWindowForUser`. Frontend checks `hasActiveMonthlyPlan`. | ✅ MATCH | — |
| G7 | `self_purchase`: Topup requires valid C-end monthly plan | Checks `consumer_monthly_plan` entitlement batch then batch window. | ✅ MATCH | — |
| G8 | `admin_purchase`: Topup requires valid B2B seat monthly plan or batch | Checks `b2b_enterprise_plan`/`b2b_monthly_seat_plan` entitlement batch then batch window. | ✅ MATCH | — |
| G9 | Batch mode: expired account → no quota | `computeAccountValidity` → expired → `quotaBytes = 0` in `getEnterpriseWorkspaceQuotaConfig`. | ✅ MATCH | — |
| G10 | Token settlement uses batch tables in batch mode | `settleEnterpriseTokenUsageIfNeeded` routes to `enterpriseTokenBatchQuotaService.settleMessageTokenUsage` when `quotaMode === 'batch'` and no consumable billing entitlement. | ✅ MATCH | — |
| G11 | `contact_admin`: No billing/purchase flow involved | No purchase UI shown; API blocks plan listing and order creation. | ✅ MATCH | — |
| G12 | `self_purchase`: Multiple monthly plans queue by effective date | `grantConsumerMonthlyPlan` creates batches with `validFrom`/`validUntil`; `scheduled` status supports future queuing. | ✅ MATCH | — |
| G13 | `self_purchase`: Topups take effect immediately and can stack | Topup grants create entitlement batches effective immediately; multiple topup batches can coexist. | ✅ MATCH | — |

---

## Open Questions

1. **G1 — Batch management in `admin_purchase` mode**: The requirement says "ALL batch operations (default batch info, create batch, assign batch to members) are done by **platform admin only**". Should enterprise admin routes (`zclaw.controller.ts` enterprise-admin) be blocked when `postExpiryPurchaseMode === 'admin_purchase'`? Or is the requirement describing the *typical workflow* rather than a hard permission boundary?

2. **G2 — `b2b_monthly_seat_plan` in frontend**: Is the omission of `b2b_monthly_seat_plan` from `BillingPurchaseDialog.tsx` B2B_PLAN_TYPES intentional (e.g., this plan type is only created/managed by platform admin and never purchased via the dialog)? Or should it be added so enterprise admin can purchase it?

3. **Batch token limit enforcement**: `settleMessageTokenUsage` in batch mode records usage but does not decrement `tokenLimit`. Where is the actual token limit enforcement (blocking messages when batch tokens are exhausted)? Is it in the streaming gate or entitlement check?

4. **`contact_admin` + batch mode interaction**: In `contact_admin` mode with `quotaMode: 'batch'`, the account validity block is still shown in the frontend (with no action button). Is this the desired UX, or should the validity block be hidden entirely in `contact_admin` mode?

5. **C-end enterprise in batch mode**: The `WorkspaceIdentityMetaPanel` forces `effectivePurchaseMode = "self_purchase"` for consumer enterprises regardless of `postExpiryPurchaseMode`. Is batch mode even applicable to C-end enterprises, or is it B2B-only?

---

## Key File Reference

| File | Key Functions/Lines |
|---|---|
| `apps/api/src/billing/purchase-mode.ts` | `resolvePurchaseMode` (line 12-21) — reads `enterprisePostExpiryPurchaseConfig.mode`, defaults to `contact_admin` |
| `apps/api/src/billing/billing-plan.service.ts:62-85` | `listPreview` — filters plans by purchase mode |
| `apps/api/src/billing/billing-plan.service.ts:554-591` | `assertPreviewAccess` — role + mode gating |
| `apps/api/src/billing/billing-order.service.ts:52-110` | `createOrder` — purchase mode validation |
| `apps/api/src/billing/billing-order.service.ts:392-449` | `assertActiveMonthlyPlanForTopup` — topup prerequisite |
| `apps/api/src/billing/entitlement.service.ts:1243-1252` | `hasActiveBatchWindowForUser` — batch window check |
| `apps/api/src/zclaw/zclaw.service.ts:10083-10276` | `getEnterpriseWorkspaceQuotaConfig` — workspace quota calc |
| `apps/api/src/zclaw/zclaw.service.ts:2149-2228` | `settleEnterpriseTokenUsageIfNeeded` — token settlement routing |
| `apps/api/src/zclaw/zclaw.service.ts:1769-1822` | Enterprise admin batch CRUD (with `assertEnterpriseAdminOrOwner`) |
| `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts:445-508` | `settleMessageTokenUsage` — batch token settlement |
| `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts:541-596` | `createBatch` — batch creation |
| `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts:998-1090` | `computeAccountValidity` — account validity chain |
| `apps/api/src/zclaw/zclaw-admin.controller.ts:34` | Platform admin routes (`AdminGuard`) |
| `apps/api/src/zclaw/zclaw.controller.ts:220-304` | Enterprise admin batch routes |
| `apps/web/src/components/zclaw/ZclawShell.tsx:1106-1116` | `canPurchaseBillingPlan` — frontend purchase gating |
| `apps/web/src/components/zclaw/ZclawShell.tsx:340-508` | `WorkspaceIdentityMetaPanel` — validity display + actions |
| `apps/web/src/components/zclaw/BillingPurchaseDialog.tsx:20-29` | Frontend plan type constants (missing `b2b_monthly_seat_plan`) |
| `apps/web/src/components/zclaw/BillingPurchaseDialog.tsx:439-469` | `handleCreateOrder` — topup prerequisite UI check |
| `apps/web/src/lib/account-validity-display.ts:22-54` | `resolveAccountValidityDisplay` — validity block visibility |
| `packages/shared/src/enterprise-kind.ts:27-37` | `PurchaseMode` constants |
