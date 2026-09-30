# Quota Display Patterns

## Overview

Frontend displays different data based on enterprise quota mode. Each mode has its own display logic, derived from `useZclawChatContext().workspaceUsage`.

## Context Derivation Pattern

**What**: Derive quota display data from `workspaceUsage` (single API call), not independent API calls.

**Why**: Prevents redundant requests, 403 errors for non-admin users, and data inconsistency.

```typescript
// CORRECT: derive from context
const postExpiryPurchaseMode = workspaceUsage?.postExpiryPurchaseMode ?? null;
const conversationQuotaSummary = workspaceUsage?.conversationQuotaSummary ?? null;

// WRONG: independent API call per component
const [postExpiryPurchaseMode, setPostExpiryPurchaseMode] = React.useState(null);
React.useEffect(() => {
  getPostExpiryPurchaseConfigApi(enterpriseId).then(config => setPostExpiryPurchaseMode(config.mode));
}, [enterpriseId]);
```

## Quota Mode Display Matrix

### ZclawShell sidebar (resolveVisibleTokenBalance)

| Mode | Label | Value | Data Source | Fallback |
|------|-------|-------|-------------|----------|
| conversation (admin) | "剩余会话" | `∞` | `conversationQuotaSummary` | — |
| conversation (member) | "剩余会话" | `limit - used` | `conversationQuotaSummary` | — |
| token | "可用 Token" | `effectiveLimit - tokenUsed` | `conversationQuotaSummary` | null (hide balance, NOT fallback to batch) |
| batch (member) | "可用 Token" | `effectiveLimit - tokenUsed` | `conversationQuotaSummary` (zclaw batch data) | — |
| **batch (owner/admin)** | **"可用 Token"** | **`∞`** | **`isQuotaExempt: true`** | **—** |
| unlimited | — | — | — | — |

> **Batch mode MUST skip `hasUserTokenEntitlement` check**. Frozen entitlement batches would otherwise return `availableTokens: 0` and hide the actual zclaw batch balance. Add explicit batch mode branch before the `hasUserTokenEntitlement` check:
> ```typescript
> // CORRECT: batch mode uses legacy quota (zclaw batch data)
> if (quotaMode === 'batch') {
>   if (!legacyQuota || legacyQuota.isBatchExpired) return null;
>   // compute remaining from legacyQuota.effectiveTokenLimit - tokenUsed
>   return { available: ..., isConversationMode: false };
> }
> // Then check hasUserTokenEntitlement for other modes...
> ```

### Token明细 dialog (UserTokenDetailsDialog)

| Mode | API | Row Component | Packages Tab |
|------|-----|-------------|-------------|
| unlimited | `listUserTokenQuotaRecordsApi` | `TokenQuotaRecordRow` | Hidden |
| conversation | `listUserTokenQuotaRecordsApi` | `TokenQuotaRecordRow` | Hidden |
| token | `listUserTokenQuotaRecordsApi` | `TokenQuotaRecordRow` | Hidden |
| batch | `listUserTokenQuotaRecordsApi` | `TokenQuotaRecordRow` | Shown |

> **All modes use `listUserTokenQuotaRecordsApi`** which queries `zclawEnterpriseTokenUsageSettlement`. Previously batch mode used `listUserTokenLedgersApi` (ledger table), but after Fix 6+8 batch mode writes to settlement table, not ledger.

### Token明细 mode labels (per-record from `item.quotaMode`)

| quotaMode | Display Label |
|-----------|------|
| `unlimited` | "无限模式" |
| `conversation` | "会话数模式" |
| `token` | "月Token模式" |
| `batch` | "Token批次模式" |
| null/unknown | "Token 配额" |

### Token明细 menu visibility

| Mode | Menu Item | Condition |
|------|-----------|-----------|
| All modes with enterprise | Shown | `activeEnterpriseSummary && quotaMode != null` |

### Validity period display

| Mode | Data Source | Behavior |
|------|-------------|----------|
| batch | `entitlementSummary.accountValidity` | Direct from backend |
| C-end (quotaMode = null) | `entitlementSummary.accountValidity` | 从月包 entitlement batch 直接计算，不依赖 quotaConfig |
| token | `conversationQuotaSummary.windowStart` | Client-computed monthEnd (timezone-safe) |
| conversation/unlimited | — | Hidden |

> **C-end 企业 `quotaMode = null`**：`resolveAccountValidityDisplay` 的 `hasAccountValidity` 从 `isBatch && accountValidity` 改为 `Boolean(accountValidity) && (isBatch || quotaMode == null)`，使得 C 端企业即使没有 batch 配置也能正常展示有效期 badge。

> **Timezone-safe monthEnd computation**: Always use local date components (`getFullYear()`, `getMonth()`, `getDate()`) to build ISO strings. Never use `Date.toISOString()` which shifts by UTC offset:
> ```typescript
> const y = startDate.getFullYear();
> const m = startDate.getMonth();
> const lastDay = new Date(y, m + 1, 0).getDate();
> return `${y}-${String(m+1).padStart(2,'0')}-${String(lastDay).padStart(2,'0')}T23:59:59.000Z`;
> ```

### UI behavior by mode

| Behavior | unlimited | conversation | token | batch |
|------|:---:|:---:|:---:|:---:|
| Token number shown | ❌ | ✅ (conversations) | ✅ | ✅ |
| Click opens topup | ❌ | ❌ | ❌ | ✅ |
| "充值" hover text | ❌ | ❌ | ❌ | ✅ |
| Validity tooltip | ❌ | ❌ | ✅ | ✅ |
| Packages tab | ❌ | ❌ | ❌ | ✅ |

## Token明细 Rendering Logic

**All modes use `listUserTokenQuotaRecordsApi`** (settlement table). The `isTokenMode` variable and batch-specific ledger rendering have been removed.

```typescript
// CORRECT: all modes use quota records from settlement table
const items = tab === 'ledgers' ? quotaRecordItems : packageItems;

// WRONG: batch mode uses ledger API (old behavior, pre-Fix 9)
const isTokenMode = tab === 'ledgers' && quotaMode !== 'batch';
const items = tab === 'ledgers' ? (isTokenMode ? quotaRecordItems : ledgerItems) : packageItems;
```

**Why**: All quota modes (including batch) now write token consumption to `zclawEnterpriseTokenUsageSettlement`. The ledger table (`entitlementLedger`) is only written by `freezeEntitlements`/`captureEntitlements`, which are skipped in batch mode.

## Token Mode: No Batch Fallback

**Principle**: When `quotaMode === 'token'`, `resolveVisibleTokenBalance` must NOT fall through to `hasUserTokenEntitlement` check. If `conversationQuotaSummary` data is unavailable, return `null` (hide display) rather than showing batch balance.

```typescript
// CORRECT: early return for token mode, no fallthrough
if (quotaMode === 'token') {
  if (legacyQuota?.effectiveTokenLimit != null) {
    // compute remaining...
    return { available: ..., isConversationMode: false };
  }
  return null; // Don't fall through to batch system
}
```

### Workspace quota card

| Mode | Display | Progress bar |
|------|---------|-------------|
| unlimited | `已用 / ♾️` | Hidden |
| quota policy ON | `已用 / 限额` | Show percentage |
| C-end | `已用 / 月包额度` | Show percentage |

## Unlimited Sentinel Handling

**Backend returns**: `effectiveQuotaBytes = -1` for unlimited mode

**Frontend recognition**:
```typescript
// Check before formatBytes (which would show "-1 B")
const isUnlimited = effectiveQuotaBytes < 0;
const displayText = isUnlimited ? '♾️' : formatBytes(effectiveQuotaBytes);
```

**Affected components**:
- `MemberTokenUsageCell`: conversation/unlimited mode shows `used / ♾️`
- `ZclawShell.workspaceSummary`: `used/♾️` in bottom bar
- `ZclawShell` tooltip: `总容量: ♾️`, `剩余: ♾️`
- `MonthlyQuotaSection` (detail page): conversation mode with progress bar

## Conversation Mode: Admin vs Member

```typescript
// Admin: show ∞ (unlimited, but usage still counted)
if (legacyQuota.membershipRole === 'admin' || legacyQuota.membershipRole === 'owner') {
  return { available: '♾️', isConversationMode: true };
}
// Member: show actual remaining
const remaining = limit != null ? limit - used : null;
return { available: remaining != null ? String(remaining) : '∞', isConversationMode: true };
```

## isConversationMode Flag

Backend `getMyEnterpriseTokenQuotaSummary` returns `isConversationMode: true` in conversation mode. Frontend `resolveVisibleTokenBalance` checks this to switch display logic:

```typescript
function resolveVisibleTokenBalance(
  entitlementSummary, legacyQuota, quotaMode
) {
  if (quotaMode === 'conversation' && legacyQuota?.isConversationMode) {
    // Return conversation data, not token data
    return { available: '...', isConversationMode: true };
  }
  // ... token/batch logic ...
}
```

## Hide Token-Related UI

- Hide "充值" button and tooltip when `isConversationMode || quotaMode === 'token'`
- Hide click-to-topup when `isConversationMode || quotaMode === 'token'`
- Hide progress bar when `isUnlimitedSpace`
- **Token明细 is now shown for ALL modes** (updated from previously hiding for conversation/unlimited)
- **Packages tab hidden for non-batch modes** (unlimited, conversation, token)
