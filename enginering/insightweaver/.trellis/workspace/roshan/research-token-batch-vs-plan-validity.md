# Research: Batch 模式 + 月度计划同时存在时的资源与有效期计算

> 研究日期: 2026-07-22
> 范围: B2B 企业同时拥有 zclaw token batch (batch mode) 和 entitlement batches (b2b_monthly_seat_plan 等) 时的行为

---

## 1. 总结表：各 quotaMode 下的资源来源

| 资源 | batch 模式 (无月度计划) | batch 模式 + B2B 月度计划 | token 模式 | conversation 模式 | unlimited 模式 |
|------|------------------------|--------------------------|-----------|------------------|---------------|
| **Token 配额** | zclaw batch (`getMemberBatchUsageSummary`) | **zclaw batch** (同左，月度计划不影响) | token quota 表 | conversation quota 表 | 无限制 |
| **Token 结算表** | `zclaw_enterprise_token_usage_settlements` | **同左** (batch 检查在 hasConsumable 之前) | `zclaw_enterprise_conversation_quota_usages` | 同左 | 同左 (仅记录) |
| **Storage 配额** | `default_quota` (baseQuotaBytes) + entitlement storage batches | **monthly_plan** (entitlement storage batches, `packageStorageBytes`) | default_quota config | default_quota config | MAX_SAFE_INTEGER |
| **有效期来源** | `computeAccountValidity` → zclaw batch 窗口 | `computeAccountValidity` → **优先 entitlement monthly_plan** | token quota 月度窗口 | 无 | 无 |
| **Billing 路由** | `useBillingEntitlements = false` | **`useBillingEntitlements = false`** (batch 排除) | `false` | `false` | `false` |
| **freezeEntitlements** | 跳过 (返回空) | **跳过** (返回空) | 跳过 | 跳过 | 跳过 |

---

## 2. 逐函数详细分析

### 2.1 `getMyEnterpriseTokenQuotaSummary` — Token 配额展示

**文件**: `apps/api/src/zclaw/zclaw.service.ts:7013-7127`

**batch 模式行为** (line 7068-7098):
```
if (config?.quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  const batchSummary = await this.enterpriseTokenBatchQuotaService
    .getMemberBatchUsageSummary(trimmedEnterpriseId, userId);
  // ...
  return {
    tokenUsed: batchSummary?.tokenUsed ?? "0",
    effectiveTokenLimit: batchSummary?.tokenLimit ?? null,
    windowStart: batchSummary?.validFrom ?? null,
    windowEnd: batchSummary?.validTo ?? null,
    isBatchMode: true,
  };
}
```

**关键发现**: batch 模式下 token 数据 **完全来自 zclaw batch 表** (`zclawEnterpriseTokenQuotaBatch` + `zclawEnterpriseTokenQuotaMember`)。即使企业有活跃的 B2B 月度计划，token 配额展示也不读取 entitlement batches。

**月度计划的影响**: 无。此函数在 batch 模式分支中不检查 `hasActiveB2BMonthlyPlan`。

---

### 2.2 `getEnterpriseWorkspaceQuotaConfig` — Storage 配额

**文件**: `apps/api/src/zclaw/zclaw.service.ts:10123-10299`

**batch 模式 + B2B 月度计划** (line 10182 → 10244):
1. Line 10182: batch 模式满足条件 `quotaConfig?.quotaMode === ZCLAW_QUOTA_MODE_BATCH`，查询 entitlement batches
2. Line 10196-10208: 计算 `packageStorageBytes` (storage 类型的 entitlement batch 的 `grantedAmount` 之和)
3. Line 10244: `if (hasActiveB2BMonthlyPlan && packageStorageBytes > 0n)` → 返回 `quotaSource: "monthly_plan"`, `quotaBytes: packageStorageBytes`

**batch 模式 + 无月度计划** (line 10254-10298):
1. Line 10254: 检查 `defaultQuotaEffective`
2. Line 10268-10275: 读取 `enterpriseWorkspaceQuotaConfig.memberDefaultWorkspaceQuotaBytes` 作为 `baseQuotaBytes`
3. Line 10276-10288: batch 模式下额外检查 `computeAccountValidity`，若过期则返回 0 空间
4. Line 10290: `quotaBytes = baseQuotaBytes + packageStorageBytes`

**关键发现**: Storage 在 batch 模式下**有月度计划时来自 entitlement batches**，无月度计划时来自 **默认配额配置 (default_quota)**。

---

### 2.3 `settleEnterpriseTokenUsageIfNeeded` — Token 结算路径

**文件**: `apps/api/src/zclaw/zclaw.service.ts:2186-2268`

**batch 模式** (line 2235-2246):
```typescript
// Batch mode settles to zclaw_enterprise_token_usage_settlements (batch table).
// Must be checked BEFORE hasConsumable, otherwise B2B enterprises with an
// active monthly plan would settle to the wrong table and batch usage shows 0.
if (quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  await this.enterpriseTokenBatchQuotaService.settleMessageTokenUsage(
    enterpriseId, userId, messageId, adjusted,
  );
  return;
}
```

**关键发现**: batch 模式的检查在 `hasConsumableBillingTokenEntitlement` 检查**之前**。即使月度计划活跃使得 `hasConsumable` 为 true，batch 模式也始终结算到 `zclaw_enterprise_token_usage_settlements` 表，不走 billing 路径。

**注释明确说明**: 如果顺序颠倒，B2B 企业有活跃月度计划时会结算到错误的表，导致 batch 使用量显示为 0。

---

### 2.4 `resolveQuotaContext` → `useBillingEntitlements` — Billing 路由

**文件**: `apps/api/src/zclaw/zclaw.service.ts:2024-2042`

```typescript
const useBillingEntitlements =
  hasConsumableBillingEntitlement &&
  quotaMode !== 'conversation' &&
  quotaMode !== 'unlimited' &&
  quotaMode !== 'token' &&
  quotaMode !== ZCLAW_QUOTA_MODE_BATCH;  // ← batch 模式排除
```

**关键发现**: batch 模式下 `useBillingEntitlements` **始终为 false**，即使 `hasConsumableBillingEntitlement` 为 true。这意味着 batch 模式的消息流永远不会走 billing service 路径。

**影响**:
- Line 5905-5906: `!useBillingEntitlements` → 走 `assertEnterpriseTokenQuotaIfNeeded` (batch 路径)
- Line 5911-5912: `!useBillingEntitlements` → 走 `consumeEnterpriseConversationQuotaIfNeeded`

---

### 2.5 `hasConsumableBillingTokenEntitlement` — 可消费权益检查

**文件**: `apps/api/src/billing/entitlement.service.ts:1149-1237`

**B2B 企业** (line 1171-1204):
1. 检查 `hasActiveB2BMonthlyPlan` → 若活跃直接返回 true
2. 检查 `hasActiveBatchWindowForUser` → 若有活跃批次窗口返回 true
3. 检查自购 token entitlements (consumer_token_topup, default_quota_batch 等)

**关键发现**: 此函数**不考虑 quotaMode**。B2B 企业有活跃月度计划时返回 true，无论当前是 batch 模式还是其他模式。但由于调用方 (`settleEnterpriseTokenUsageIfNeeded`, `resolveQuotaContext`) 在 batch 模式下会跳过此检查结果，因此不影响实际路由。

---

### 2.6 `freezeEntitlements` — 冻结/扣费逻辑

**文件**: `apps/api/src/billing/entitlement.service.ts:1642-1738`

**batch 模式** (line 1660-1664):
```typescript
if (quotaConfig?.quotaMode === 'unlimited' || quotaConfig?.quotaMode === 'token'
    || quotaConfig?.quotaMode === 'conversation' || quotaConfig?.quotaMode === 'batch') {
  // Batch mode tracks token usage via zclaw_enterprise_token_usage_settlements
  return this.consumptionResultFromLedgers([], 'freeze');
}
```

**关键发现**: batch 模式下 `freezeEntitlements` 直接返回空结果，**不冻结任何 entitlement batch**。所有四种非默认模式 (unlimited/token/conversation/batch) 都跳过 entitlement batch 冻结。

---

### 2.7 `resolveLegacyB2BAvailableTokens` — 可用 Token 计算

**文件**: `apps/api/src/billing/entitlement.service.ts:1071-1147`

**关键逻辑** (line 1078-1085):
```typescript
if (input.enterpriseKind !== "b2b" || !input.userId
    || input.hasActiveMonthlyPlan || !input.memberCanUse) {
  return 0n;  // ← 有月度计划时直接返回 0
}
```

**batch 模式 + 月度计划活跃**: 返回 **0n** (因为 `hasActiveMonthlyPlan = true`)

**batch 模式 + 无月度计划** (line 1097-1108):
```typescript
if (config.quotaMode === "batch") {
  const batchSummary = await this.enterpriseTokenBatchQuotaService
    .getMemberBatchUsageSummary(input.enterpriseId, input.userId);
  if (!batchSummary?.isEffective) return 0n;
  const tokenLimit = BigInt(batchSummary.tokenLimit);
  const tokenUsed = BigInt(batchSummary.tokenUsed);
  return tokenLimit > tokenUsed ? tokenLimit - tokenUsed : 0n;
}
```

**关键发现**: 当月度计划活跃时，`resolveLegacyB2BAvailableTokens` 返回 0。这影响 `getSummary` 中的 `availableTokens` 计算 (line 964-965): `availableTokens = sumRemaining(usableBatches, "token") + legacyB2BAvailableTokens`。月度计划活跃时 legacy 部分为 0，availableTokens 仅来自 usable entitlement batches。

---

### 2.8 `getSummary` — Entitlement 摘要

**文件**: `apps/api/src/billing/entitlement.service.ts:871-1069`

**关键流程**:
1. Line 903-911: `hasActiveMonthlyPlan` 对 B2B 通过 `hasActiveB2BMonthlyPlan` 判断
2. Line 913-922: `hasActiveBatchWindow` 仅在 `!hasActiveMonthlyPlan` 时计算
3. Line 934-953: `usableBatches` 过滤链 — 当 `hasActiveMonthlyPlan` 为 true 时，`isUsableEntitlementBatch` 和 `isUsableInBillingContext` 使用不同的过滤逻辑
4. Line 955-965: `availableTokens = sumRemaining(usableBatches, "token") + legacyB2BAvailableTokens`
5. Line 1029: `accountValidity` 仅在 `quotaMode === 'batch'` 时计算

**batch 模式 + 月度计划**:
- `accountValidity` 由 `computeAccountValidity` 计算
- `availableTokens` 主要来自 entitlement batches (usableBatches)
- `legacyB2BAvailableTokens` = 0 (因为 hasActiveMonthlyPlan)
- `hasActiveBatchWindow` = false (因为 hasActiveMonthlyPlan 为 true)

---

### 2.9 `computeAccountValidity` — 有效期计算

**文件**: `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts:1000-1098`

**优先级顺序**:
1. **用户级 entitlement batch** (`entitlementType: "monthly_plan"`, active, valid) — line 1013-1037
2. **`calculateUserTimeWindow`** 合并 zclaw batch + entitlement batches 的时间线 — line 1040-1050
3. **zclaw batch membership** 日期 (batch 存在但已过期) — line 1053-1072
4. **frozen entitlement batch** — line 1075-1095

**关键发现**: 当用户有活跃的 entitlement monthly_plan batch 时，`computeAccountValidity` 返回该 batch 的 `validFrom/validUntil`，**而非 zclaw batch 的日期**。

**`calculateUserTimeWindow`** (line 872-997):
- 合并 zclaw batch 和 entitlement batches 为统一时间线
- 按 `effectiveFrom` 排序
- 返回当前有效窗口和队列

---

### 2.10 前端 `resolveVisibleTokenBalance` — Token 展示

**文件**: `apps/web/src/components/zclaw/ZclawShell.tsx:220-292`

**batch 模式** (line 258-271):
```typescript
// Batch mode: use zclaw batch quota data, skip entitlement batches
// (frozen entitlement batches would otherwise intercept via hasUserTokenEntitlement)
if (quotaMode === 'batch') {
  if (!legacyQuota || legacyQuota.isBatchExpired) return null;
  const effectiveLimit = parseTokenBigInt(legacyQuota.effectiveTokenLimit);
  if (effectiveLimit === null) return null;
  const tokenUsed = parseTokenBigInt(legacyQuota.tokenUsed) ?? 0n;
  const remaining = effectiveLimit > tokenUsed ? effectiveLimit - tokenUsed : 0n;
  return { available: formatQuotaTokenNumber(remaining.toString()), isConversationMode: false };
}
```

**关键发现**: batch 模式下前端**完全使用 legacyQuota** (来自 `getMyEnterpriseTokenQuotaSummary`)，不读取 entitlement summary 的 `availableTokens`。注释明确说明是为了避免被冻结的 entitlement batches 拦截。

---

### 2.11 前端 `resolveValidityDates` — 有效期展示

**文件**: `apps/web/src/components/zclaw/ZclawShell.tsx:294-337`

**优先级**:
1. `entitlementSummary?.accountValidity` (来自 `computeAccountValidity`) — line 300-305
2. Token 模式: `legacyTokenQuota.windowStart` — line 308-334
3. 其他: null

**batch 模式**: 使用 `accountValidity`，即 `computeAccountValidity` 的结果。当有活跃月度计划时，展示的是 **entitlement monthly_plan batch 的有效期**，而非 zclaw batch 的有效期。

---

### 2.12 `UserTokenDetailsDialog` — Ledgers Tab

**文件**: `apps/web/src/components/zclaw/UserTokenDetailsDialog.tsx:201-347`

**Ledgers tab 数据源** (line 231-232):
```typescript
const request = tab === 'ledgers'
  ? listUserTokenQuotaRecordsApi({ enterpriseId, page, pageSize: PAGE_SIZE })
  : listUserPackageRecordsApi({ enterpriseId, page, pageSize: PAGE_SIZE });
```

**后端 `listUserTokenQuotaRecords`** (entitlement.service.ts:1595-1631):
- 读取 `zclawEnterpriseTokenUsageSettlement` 表
- 返回 `messageId, tokens, quotaMode, occurredAt`

**Tab 可见性** (line 280):
```typescript
.filter((item) => item !== 'packages' || (quotaMode !== 'token' && quotaMode !== 'conversation' && quotaMode !== 'unlimited'))
```

**关键发现**:
- Ledgers tab 在所有 quotaMode 下都可见，数据来自 `zclawEnterpriseTokenUsageSettlement` (batch 结算表)
- Packages tab 仅在非 token/conversation/unlimited 模式下可见 (即 batch 模式或无特定模式时可见)
- Ledgers tab 不区分 quotaMode，展示的是同一张结算表的数据

---

## 3. 当 batch 和月度计划同时活跃时的最终答案

| 资源/行为 | 胜出方 | 机制 |
|----------|--------|------|
| **Token 配额展示** | **zclaw batch** | `getMyEnterpriseTokenQuotaSummary` 在 batch 模式下只读 zclaw batch 表 |
| **Token 结算** | **zclaw batch** | `settleEnterpriseTokenUsageIfNeeded` 在 batch 模式下走 batch 结算，在 hasConsumable 之前 |
| **Billing 路由** | **zclaw batch** | `useBillingEntitlements` 在 batch 模式下强制为 false |
| **freezeEntitlements** | **跳过** | batch 模式直接返回空，不冻结 entitlement batches |
| **Storage 配额** | **entitlement batches (monthly_plan)** | `getEnterpriseWorkspaceQuotaConfig` 在有月度计划时返回 `quotaSource: "monthly_plan"` |
| **有效期展示** | **entitlement monthly_plan batch** | `computeAccountValidity` 优先返回 entitlement monthly_plan 的日期 |
| **availableTokens (Summary API)** | **entitlement batches** | `resolveLegacyB2BAvailableTokens` 在有月度计划时返回 0，availableTokens 仅来自 usableBatches |

---

## 4. 已识别的冲突与不一致

### 4.1 Token 展示 vs Summary API 的不一致

- **前端 sidebar** (`resolveVisibleTokenBalance`): batch 模式下显示 **zclaw batch** 的剩余 token
- **Summary API** (`getSummary`): `availableTokens` 在有月度计划时来自 **entitlement batches** (legacy 部分为 0)
- **影响**: sidebar 和详情面板可能显示不同的 token 余额

### 4.2 Storage 来源的切换

- batch 模式 + 无月度计划: storage 来自 `default_quota` 配置
- batch 模式 + 有月度计划: storage 来自 entitlement batches (`packageStorageBytes`)
- **切换点**: `hasActiveB2BMonthlyPlan && packageStorageBytes > 0n` (line 10244)
- **风险**: 如果月度计划过期但 batch 仍有效，storage 会突然从 entitlement batches 回退到 default_quota

### 4.3 有效期的多源合并

- `computeAccountValidity` 有 4 层回退逻辑
- 月度计划活跃时展示 entitlement batch 的有效期
- zclaw batch 的有效期被遮蔽（即使 zclaw batch 先过期）
- **风险**: 用户看到的有效期 (entitlement) 和实际 token 可用期 (zclaw batch) 可能不同

### 4.4 `resolveLegacyB2BAvailableTokens` 的月度计划短路

- 月度计划活跃时直接返回 0n，不检查 batch 模式下的实际可用 token
- 这导致 `getSummary.availableTokens` 在有月度计划时不包含 zclaw batch 的剩余
- 但 sidebar 展示的是 zclaw batch 的剩余 — 数据源不一致

---

## 5. Consumer 企业的 batch 模式行为

Consumer 企业**不支持 batch 模式**:
- `DefaultQuotaPolicyService.resolveBlockedReason` (line 218): consumer 企业返回 `'consumer_enterprise'`
- `isDefaultQuotaEffective` (line 24): consumer 企业 `effectiveEnabled` 始终为 false
- Batch 模式是 B2B 专属功能

Consumer 企业在 batch 模式下的行为等同于无月度计划的 consumer:
- `hasActiveB2BMonthlyPlan` = false (enterpriseKind !== 'b2b')
- Storage 走 consumer 路径 (line 10210-10238)
- 如果有 consumer_monthly_plan → `quotaSource: "monthly_plan"`
- 如果无月度计划但有 admin_grant → `quotaSource: "admin_grant"`
- 否则 → `quotaSource: "none"`, `entitlementExpiredReason: "consumer_monthly_expired"`

---

## 6. 代码引用索引

| 函数 | 文件 | 行号 |
|------|------|------|
| `getMyEnterpriseTokenQuotaSummary` | `apps/api/src/zclaw/zclaw.service.ts` | 7013-7127 |
| `getEnterpriseWorkspaceQuotaConfig` | `apps/api/src/zclaw/zclaw.service.ts` | 10123-10299 |
| `settleEnterpriseTokenUsageIfNeeded` | `apps/api/src/zclaw/zclaw.service.ts` | 2186-2268 |
| `resolveQuotaContext` | `apps/api/src/zclaw/zclaw.service.ts` | 2024-2042 |
| `hasConsumableBillingTokenEntitlement` (zclaw) | `apps/api/src/zclaw/zclaw.service.ts` | 2319-2324 |
| `hasActiveB2BMonthlyPlanForEnterprise` | `apps/api/src/zclaw/zclaw.service.ts` | 2270-2284 |
| `hasActiveMonthlyPlanForBilling` | `apps/api/src/zclaw/zclaw.service.ts` | 2286-2317 |
| `hasConsumableBillingTokenEntitlement` (billing) | `apps/api/src/billing/entitlement.service.ts` | 1149-1237 |
| `hasActiveB2BMonthlyPlan` (billing) | `apps/api/src/billing/entitlement.service.ts` | 5966-5982 |
| `hasActiveB2BMonthlyPlan` (default-quota) | `apps/api/src/billing/default-quota-policy.service.ts` | 117-140 |
| `freezeEntitlements` | `apps/api/src/billing/entitlement.service.ts` | 1642-1738 |
| `resolveLegacyB2BAvailableTokens` | `apps/api/src/billing/entitlement.service.ts` | 1071-1147 |
| `getSummary` | `apps/api/src/billing/entitlement.service.ts` | 871-1069 |
| `listUserTokenQuotaRecords` | `apps/api/src/billing/entitlement.service.ts` | 1595-1631 |
| `computeAccountValidity` | `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts` | 1000-1098 |
| `getMemberBatchUsageSummary` | `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts` | 828-861 |
| `calculateUserTimeWindow` | `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts` | 872-997 |
| `settleMessageTokenUsage` (batch) | `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts` | 447-510 |
| `resolveVisibleTokenBalance` | `apps/web/src/components/zclaw/ZclawShell.tsx` | 220-292 |
| `resolveValidityDates` | `apps/web/src/components/zclaw/ZclawShell.tsx` | 294-337 |
| `hasUserTokenEntitlement` | `apps/web/src/components/zclaw/ZclawShell.tsx` | 210-218 |
| `UserTokenDetailsDialog` | `apps/web/src/components/zclaw/UserTokenDetailsDialog.tsx` | 201-347 |
| `resolveAccountValidityDisplay` | `apps/web/src/lib/account-validity-display.ts` | 22-54 |
