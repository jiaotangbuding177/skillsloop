# Research: Unlimited Mode & Conversation Mode Quota Logic

> Date: 2026-07-21
> Investigator: roshan
> Status: Complete

---

## 1. Unlimited Mode Logic

### 1.1 `assertEnterpriseTokenQuotaIfNeeded` — skips all quota checks

**File:** `apps/api/src/zclaw/zclaw.service.ts:2007–2043`

```typescript
private async assertEnterpriseTokenQuotaIfNeeded(
  enterpriseId: string,
  userId: string,
  ctx?: QuotaContext,
) {
  const hasConsumable =
    ctx !== undefined
      ? ctx.hasConsumableBillingEntitlement
      : await this.hasConsumableBillingTokenEntitlement(enterpriseId, userId);
  if (hasConsumable) {
    return;
  }
  const quotaMode =
    ctx !== undefined
      ? ctx.quotaMode
      : (
          await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
            where: { enterpriseId },
            select: { quotaMode: true },
          })
        )?.quotaMode;
  if (quotaMode === 'unlimited') {
    return;   // <-- skips all quota assertions
  }
  // ... other modes
}
```

**Status:** ✅ Intact. Unlimited mode short-circuits before any token/batch assertion.

**Note:** When `hasConsumableBillingEntitlement` is true, the function returns early BEFORE checking quotaMode. In unlimited mode, `resolveQuotaContext` (line 1999–2003) forces `useBillingEntitlements = false`, so the billing path is bypassed at the `streamMessage` level (line 5864), and `assertEnterpriseTokenQuotaIfNeeded` is called directly. This means the `hasConsumable` early return at line 2016 is a defense-in-depth path, not the primary unlimited path.

### 1.2 `resolveQuotaContext` — forces billing off for unlimited

**File:** `apps/api/src/zclaw/zclaw.service.ts:1988–2005`

```typescript
private async resolveQuotaContext(enterpriseId: string, userId: string): Promise<QuotaContext> {
  const quotaMode = (
    await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
      where: { enterpriseId },
      select: { quotaMode: true },
    })
  )?.quotaMode;
  const hasConsumableBillingEntitlement = await this.hasConsumableBillingTokenEntitlement(
    enterpriseId,
    userId,
  );
  const useBillingEntitlements =
    hasConsumableBillingEntitlement &&
    quotaMode !== 'conversation' &&
    quotaMode !== 'unlimited' &&
    quotaMode !== 'token';
  return { quotaMode, useBillingEntitlements, hasConsumableBillingEntitlement };
}
```

**Status:** ✅ Intact. `useBillingEntitlements` is forced to `false` for unlimited/conversation/token modes.

### 1.3 `settleEnterpriseTokenUsageIfNeeded` — records usage, no enforcement

**File:** `apps/api/src/zclaw/zclaw.service.ts:2149–2227`

```typescript
if (quotaMode === 'unlimited') {
  await this.enterpriseTokenQuotaService.settleMessageTokenUsage(
    enterpriseId,
    userId,
    messageId,
    applyToolBillingAdjustment(usage, toolBillingTokens),
    quotaMode,
  );
  return;
}
```

**Status:** ✅ Intact. Records token usage via `settleMessageTokenUsage` with `quotaMode: 'unlimited'` for analytics. No limit enforcement.

### 1.4 `getEnterpriseWorkspaceQuotaConfig` — returns unlimited sentinel

**File:** `apps/api/src/zclaw/zclaw.service.ts:10082–10101`

```typescript
if (quotaConfig?.quotaMode === 'unlimited') {
  return {
    quotaBytes: BigInt(Number.MAX_SAFE_INTEGER),
    hasActiveMonthlyPlan: true,
    hasUsableBillingEntitlement: true,
    quotaSource: 'unlimited',
    entitlementExpiredReason: null,
    entitlementExpiredMessage: null,
  };
}
```

**Status:** ✅ Intact. Returns `Number.MAX_SAFE_INTEGER` as quotaBytes (effectively unlimited). Note: the `UNLIMITED_WORKSPACE_QUOTA_SENTINEL` (-1n) is used at line 10191 for the B2B non-default-quota path, NOT for the unlimited quotaMode path. The unlimited quotaMode uses `Number.MAX_SAFE_INTEGER` instead.

**Observation:** There are TWO representations of "unlimited" workspace quota:
1. `UNLIMITED_WORKSPACE_QUOTA_SENTINEL = -1n` (line 192) — used when default quota policy is disabled (line 10191) and in member listing (line 9614)
2. `BigInt(Number.MAX_SAFE_INTEGER)` (line 10094) — used when quotaMode === 'unlimited' in `getEnterpriseWorkspaceQuotaConfig`

This inconsistency could cause confusion. The sentinel `-1n` is the canonical "unlimited" marker in the member listing code (line 9618: `effectiveQuotaBytes < 0n`), while `Number.MAX_SAFE_INTEGER` is used in the per-user config.

### 1.5 `consumeEnterpriseConversationQuotaIfNeeded` — skips entirely in unlimited

**File:** `apps/api/src/zclaw/zclaw.service.ts:6868–6870`

```typescript
if (config?.quotaMode === 'unlimited') {
  return;
}
```

**Status:** ✅ Intact. Conversation count decrement is fully skipped.

### 1.6 `getMyEnterpriseTokenQuotaSummary` — returns null in unlimited

**File:** `apps/api/src/zclaw/zclaw.service.ts:7000–7001`

```typescript
if (config?.quotaMode === 'unlimited') {
  return null;
}
```

**Status:** ✅ Intact. Sidebar token balance is hidden.

### 1.7 `enterprise-token-quota.service.ts` — `settleMessageTokenUsage`

**File:** `apps/api/src/zclaw/enterprise-token-quota.service.ts:72–148`

The service does NOT differentiate by quotaMode. It always:
1. Creates a `ZclawEnterpriseTokenUsageSettlement` record (with `quotaMode` stored for analytics)
2. Increments `tokenUsed` on the usage row
3. Resets monthly window if needed

**Status:** ✅ Intact. The service records usage regardless of mode. The `quotaMode` parameter is stored in the settlement record for historical tracking.

### 1.8 Entitlement service — unlimited mode bypasses

**File:** `apps/api/src/billing/entitlement.service.ts`

- Line 1023–1029: Account validity check skipped for non-batch modes
- Line 1656: `freezeEntitlements` skips consumption for unlimited/token/conversation
- Line 6106: Topup account validity gate skipped for unlimited

**Status:** ✅ Intact.

### 1.9 Frontend: unlimited mode hides token/space quota displays

**File:** `apps/web/src/components/zclaw/ZclawShell.tsx`

- Line 1079: Space display shows `♾️` for unlimited: `workspaceUsage.quotaMode === 'unlimited' ? '♾️' : formatCompactStorageValue(...)`
- Line 1164: `isUnlimited={workspaceUsage?.quotaMode === 'unlimited'}` passed to `WorkspaceIdentityMetaPanel`
- Lines 1311, 1317: Capacity/remaining show `♾️` for unlimited

**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

- Line 2805: `if (workspaceUsage?.quotaMode === 'unlimited') return undefined;` — skips all quota warnings

**File:** `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`

- Lines 930, 940, 953, 971: Workspace limit checks skip unlimited mode

**Status:** ✅ Intact.

---

## 2. Conversation Mode Logic

### 2.1 `assertEnterpriseTokenQuotaIfNeeded` — calls `assertConversationQuotaAvailable`

**File:** `apps/api/src/zclaw/zclaw.service.ts:2031–2034`

```typescript
if (quotaMode === 'conversation') {
  await this.assertConversationQuotaAvailable(enterpriseId, userId);
  return;
}
```

**Status:** ✅ Intact.

### 2.2 `assertConversationQuotaAvailable` — checks remaining conversations

**File:** `apps/api/src/zclaw/zclaw.service.ts:2045–2067`

```typescript
private async assertConversationQuotaAvailable(enterpriseId: string, userId: string) {
  const membership = await this.prisma.enterpriseMembership.findFirst({
    where: {
      enterpriseId,
      userId,
      status: "active",
      isDeleted: false,
      enterprise: { status: "active", isDeleted: false },
    },
    select: { role: true },
  });
  if (!membership || membership.role === "admin" || membership.role === "owner") {
    return;  // Admin/owner exempt from conversation limits
  }

  const usage = await this.prisma.zclawEnterpriseConversationQuotaUsage.findUnique({
    where: { enterpriseId_userId: { enterpriseId, userId } },
    select: { remainingConversations: true },
  });
  if (usage?.remainingConversations != null && usage.remainingConversations <= 0) {
    throw new ZclawTokenQuotaExceededError();
  }
}
```

**Status:** ✅ Intact. Admin/owner bypass, members blocked when `remainingConversations <= 0`.

### 2.3 `settleEnterpriseTokenUsageIfNeeded` — records token usage in conversation mode

**File:** `apps/api/src/zclaw/zclaw.service.ts:2166–2175`

```typescript
if (quotaMode === 'conversation') {
  await this.enterpriseTokenQuotaService.settleMessageTokenUsage(
    enterpriseId,
    userId,
    messageId,
    usage,
    quotaMode,
  );
  return;
}
```

**Status:** ✅ Intact. Records token usage for analytics but does NOT apply tool billing adjustment (unlike unlimited/token modes which call `applyToolBillingAdjustment`). This is intentional — conversation mode tracks raw usage.

### 2.4 `consumeEnterpriseConversationQuotaIfNeeded` — decrements conversation count

**File:** `apps/api/src/zclaw/zclaw.service.ts:6835–6970`

Flow:
1. Check quotaMode — skip if unlimited (line 6868)
2. Skip if no config or no conversationLimit (line 6871)
3. INSERT usage row if not exists (ON CONFLICT DO NOTHING)
4. UPDATE usage row if resetVersion changed (admin changed limit)
5. DECREMENT `remainingConversations` by 1 (WHERE remainingConversations > 0)
6. If decrement returns 0 and user is not admin → throw `ZclawConversationQuotaExceededError`

**Status:** ✅ Intact.

### 2.5 Conversation quota reset logic

**Two reset mechanisms:**

1. **Admin-initiated reset** (`resetEnterpriseConversationQuotaForAdmin`):
   - File: `apps/api/src/zclaw/zclaw.service.ts:2478–2493`
   - Increments `resetVersion` on the config
   - Calls `resetEnterpriseConversationQuotaUsages` which resets all members' `remainingConversations` to the configured `conversationLimit`

2. **Config change reset** (`saveEnterpriseConversationQuota`):
   - File: `apps/api/src/zclaw/zclaw.service.ts:2366–2403`
   - When `conversationLimit` changes, `resetVersion` is incremented
   - On next `consumeEnterpriseConversationQuotaIfNeeded`, the usage row's `resetVersion < config.resetVersion` triggers a reset (line 6953)

3. **Token monthly window reset** (`resetMonthlyWindowIfNeeded`):
   - File: `apps/api/src/zclaw/enterprise-token-quota.service.ts:278–304`
   - Resets `tokenUsed` to 0 at the start of each month
   - Only applies to the token tracking side, NOT to `remainingConversations`

**Status:** ✅ Intact. Conversation count reset is admin-triggered via `resetVersion`. Token tracking resets monthly.

### 2.6 `getMyEnterpriseTokenQuotaSummary` — returns conversation data

**File:** `apps/api/src/zclaw/zclaw.service.ts:7005–7025`

```typescript
if (config?.quotaMode === 'conversation') {
  const usage = await this.prisma.zclawEnterpriseConversationQuotaUsage.findUnique({
    where: { enterpriseId_userId: { enterpriseId, userId } },
    select: { remainingConversations: true, limitSnapshot: true },
  });
  const conversationLimit = config.conversationLimit ?? usage?.limitSnapshot ?? null;
  const remaining = usage?.remainingConversations ?? conversationLimit;
  const used = conversationLimit != null && remaining != null
    ? conversationLimit - remaining
    : 0;
  return {
    enterpriseId: trimmedEnterpriseId,
    membershipRole,
    tokenUsed: String(used),
    effectiveTokenLimit: conversationLimit != null ? String(conversationLimit) : null,
    windowStart: null,
    windowEnd: null,
    isBatchMode: false,
    isConversationMode: true,
  };
}
```

**Status:** ✅ Intact. Returns conversation count data with `isConversationMode: true`. The `tokenUsed` field is repurposed to hold "conversations used" and `effectiveTokenLimit` holds "conversation limit".

### 2.7 Frontend: conversation mode displays remaining conversations

**File:** `apps/web/src/components/zclaw/ZclawShell.tsx:220–237`

```typescript
function resolveVisibleTokenBalance(...) {
  if (quotaMode === 'conversation' && legacyQuota?.isConversationMode) {
    if (legacyQuota.membershipRole === 'admin' || legacyQuota.membershipRole === 'owner') {
      return { available: '∞', isConversationMode: true };
    }
    const limit = legacyQuota.effectiveTokenLimit ? Number(legacyQuota.effectiveTokenLimit) : null;
    const used = Number(legacyQuota.tokenUsed) || 0;
    const remaining = limit != null ? limit - used : null;
    return {
      available: remaining != null ? String(remaining) : '',
      isConversationMode: true,
    };
  }
  // ...
}
```

**Status:** ✅ Intact. Admin/owner see `∞`. Members see remaining conversation count.

**Sidebar display** (line 549):
```
{tokenMeta?.isConversationMode ? tShell("remainingConversations") : tShell("availableTokenBalance")}
```

**Status:** ✅ Intact. Label changes to "remaining conversations" in conversation mode.

---

## 3. Test Coverage

### 3.1 `quota-mode-backend.test.ts` (305 lines)

**File:** `apps/api/src/zclaw/__tests__/quota-mode-backend.test.ts`

**Unlimited mode tests:**
- ✅ Line 108: `"unlimited mode: skips all quota checks"` — verifies assert skips token/batch
- ✅ Line 117: `"unlimited mode: skips even with billing entitlement"` — verifies billing doesn't interfere
- ✅ Line 173: `"unlimited mode: records token usage for analytics"` — verifies settlement records usage with quotaMode='unlimited'

**Conversation mode tests:**
- ✅ Line 126: `"conversation mode: checks conversation quota NOT token quota"` — verifies correct assertion path
- ✅ Line 187: `"conversation Mode: records token usage for analytics"` — verifies settlement records with quotaMode='conversation'

**resolveQuotaContext tests:**
- ✅ Line 247: `"reads config once and derives useBilling for batch + consumable"`
- ✅ Line 256: `"forces useBilling false for conversation/unlimited/token"`
- ✅ Line 264: `"useBilling false when no consumable entitlement"`

**ctx reuse tests:**
- ✅ Line 274: `"assert with ctx does not re-read config"`
- ✅ Line 283: `"settle with ctx does not re-read config"`
- ✅ Line 292: `"resolve+assert+settle path reads config exactly once"`
- ✅ Line 300: `"settle with ctx applies toolBilling adjustment in batch mode"`

### 3.2 `zclaw.service.test.ts` (679 lines)

**File:** `apps/api/src/zclaw/zclaw.service.test.ts`

**Unlimited mode tests:**
- ✅ Line 572: `"workspace usage summary bypasses quota checks when quotaMode is unlimited"`
- ✅ Line 625: `"conversation quota consumption skips entirely when quotaMode is unlimited"`
- ✅ Line 660: `"getMyEnterpriseTokenQuotaSummary returns null when quotaMode is unlimited"`

**Conversation mode tests:**
- ✅ Line 555: `"b2b conversation mode keeps default workspace quota without validity gate"`

### 3.3 `enterprise-token-quota.service.test.ts` (135 lines)

**File:** `apps/api/src/zclaw/enterprise-token-quota.service.test.ts`

- ✅ 6 tests for `resetMonthlyWindowIfNeeded` covering: current month (no reset), previous month (reset), null windowStart (reset), far past (reset), exact month boundary (no reset), empty query result (no reset)

### 3.4 `entitlement.service.test.ts`

**File:** `apps/api/src/billing/entitlement.service.test.ts`

- ✅ Line 2622: `"resolveConsumableBatches skips account validity gate when quotaMode is unlimited"`
- ✅ Line 2641: `"resolveConsumableBatches runs account validity gate when quotaMode is not unlimited"`
- ✅ Line 2839: `"getSummary returns null accountValidity when quotaMode is unlimited"`
- ✅ Line 2997: `"freezeEntitlements skips consumption when quotaMode is unlimited"`

### 3.5 Frontend tests

**`quota-mode-display.test.ts`** (416 lines):
- ✅ Tests `resolveVisibleTokenBalance` for conversation/token/batch modes
- ✅ Tests admin `∞` display in conversation mode
- ✅ Tests remaining conversation count display

**`quota-mode-ui-behavior.test.ts`** (171 lines):
- ✅ Tests topup hint visibility per mode
- ✅ Tests click behavior per mode
- ✅ Tests tooltip visibility per mode
- ✅ Tests packages tab visibility (only in batch mode)

---

## 4. Gaps in Test Coverage

### 4.1 Backend gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| **`getEnterpriseWorkspaceQuotaConfig` unlimited path** | Medium | The `quotaMode === 'unlimited'` early return at line 10092 is only tested indirectly via `getWorkspaceUsageSummary`. No direct unit test verifies the returned `WorkspaceQuotaConfig` shape (quotaBytes = MAX_SAFE_INTEGER, quotaSource = 'unlimited'). |
| **`assertConversationQuotaAvailable` admin bypass** | Medium | No test verifies that admin/owner roles bypass conversation quota check while members are blocked. |
| **`assertConversationQuotaAvailable` exhaustion** | Medium | No test verifies that `remainingConversations <= 0` throws `ZclawTokenQuotaExceededError` for non-admin members. |
| **`consumeEnterpriseConversationQuotaIfNeeded` decrement** | Medium | Only one test (line 625) verifies the unlimited skip. No test verifies the actual decrement flow or the `ZclawConversationQuotaExceededError` throw when `consumed === 0`. |
| **`settleMessageTokenUsage` mode-specific behavior** | Low | The `enterprise-token-quota.service.test.ts` only tests `resetMonthlyWindowIfNeeded`. No tests for `settleMessageTokenUsage` itself (idempotency via settlement ID, token increment, monthly window reset). |
| **Conversation mode settlement skips tool billing adjustment** | Low | In `settleEnterpriseTokenUsageIfNeeded`, conversation mode passes raw `usage` without `applyToolBillingAdjustment`, while unlimited/token modes apply the adjustment. No test verifies this difference. |
| **`UNLIMITED_WORKSPACE_QUOTA_SENTINEL` vs `Number.MAX_SAFE_INTEGER` inconsistency** | Medium | Two different representations of "unlimited" workspace quota exist. No test documents or verifies which is used where. |

### 4.2 Frontend gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| **Unlimited mode workspace display** | Low | No test verifies that `ZclawShell` renders `♾️` for unlimited workspace quota. Tests are in `ZclawShell.accountValidity.test.tsx` but don't cover the `♾️` rendering. |
| **SuperLobsterPage unlimited skip** | Low | No test verifies that `conversationQuotaResult` returns `undefined` for unlimited mode (line 2805). |
| **Conversation mode admin ∞ display** | Medium | The `resolveVisibleTokenBalance` function returns `'∞'` for admin/owner in conversation mode. The test at `quota-mode-display.test.ts` tests this via mock but the actual function is private in `ZclawShell.tsx`. |
| **`ZclawWorkspaceSidebar` unlimited workspace limit** | Low | Lines 930/940/953/971 skip workspace limit enforcement for unlimited mode. No test coverage. |

---

## 5. Summary

### Unlimited mode: ✅ Fully implemented, well-tested

All code paths correctly:
- Skip token/batch quota assertions
- Force `useBillingEntitlements = false`
- Record token usage for analytics via settlement
- Skip conversation count consumption
- Return null for token quota summary (hides sidebar token balance)
- Display `♾️` for workspace quota in frontend
- Skip workspace limit warnings in SuperLobsterPage

### Conversation mode: ✅ Fully implemented, moderately tested

All code paths correctly:
- Call `assertConversationQuotaAvailable` (admin exempt, members blocked at 0)
- Decrement `remainingConversations` on each message
- Record token usage for analytics
- Return conversation data via `getMyEnterpriseTokenQuotaSummary` with `isConversationMode: true`
- Display remaining conversations in sidebar (admin sees `∞`)
- Reset via `resetVersion` mechanism (admin-triggered or config change)

### Key architectural observations

1. **Mode isolation**: Each mode operates independently. No cross-mode data leakage.
2. **Billing bypass**: `resolveQuotaContext` forces `useBillingEntitlements = false` for unlimited/conversation/token — only batch mode uses billing.
3. **Dual settlement path**: Both unlimited and conversation modes record token usage via `enterpriseTokenQuotaService.settleMessageTokenUsage` for analytics, but conversation mode does NOT apply tool billing adjustment.
4. **Conversation reset is admin-triggered**: Unlike token quota which resets monthly via `resetMonthlyWindowIfNeeded`, conversation count only resets when admin explicitly triggers it via `resetVersion` increment.
5. **Two "unlimited" workspace representations**: `UNLIMITED_WORKSPACE_QUOTA_SENTINEL = -1n` (default quota disabled) vs `BigInt(Number.MAX_SAFE_INTEGER)` (quotaMode = unlimited). This is a potential source of confusion.
