# Batch模式配额系统全面修复 + self_purchase 模式账户过期拦截

## 问题现象

Batch 模式下，管理员给用户新建/分配一个新批次（批次时间有效），用户端显示：
1. **有效期错误**（已修复 — Fix 1 + Fix 2）
2. **空间容量为 0.0G**（预期：读取默认空间配额 5GB — Fix 3 + Fix 4）
3. **可用 token 显示 0 / 隐藏**（已修复 — Fix 5）
4. **对话报错"Token 额度已用尽"**（已修复 — Fix 6）
5. **对话不扣 token、无明细记录**（已修复 — Fix 7 + Fix 8）
6. **Token 明细看不到消费记录**（已修复 — Fix 9）
7. **self_purchase 模式看不到 C 端套餐**（已修复 — Fix 10）

## 根因与修复

### Fix 1：`assignMemberToBatch` 不清理 `validFrom`/`validTo`

`enterprise-token-batch-quota.service.ts:176-188`，upsert 的 `update` 分支只更新 `batchId`/`assignedAt`/`updatedAt`，**不清理 `validFrom`/`validTo`**。

如果用户之前通过 `assignMemberToDefaultBatchWithDynamicValidity` 被分配过（设了自定义 `validFrom`/`validTo`），重新分配到新批次时旧日期残留。

**修复**：upsert `update` 分支增加 `validFrom: null, validTo: null`。

### Fix 2：`computeAccountValidity` 缺少有效分支 return

`enterprise-token-batch-quota.service.ts:1051-1064`，zclaw batch 有效（`effectiveTo >= now`）时没有 return，fall through 到 frozen 检查后返回 `null`。

**修复**：zclaw batch 有效时返回 `status: this.validityStatus(effectiveTo, now)`。

### Fix 3：删除 zclawMember 冗余检查

`zclaw.service.ts:10285-10301`，在 `computeAccountValidity` 已检查账户有效性后，又对 zclawMember 单独做了一次批次有效性检查。此检查与 `computeAccountValidity` 冗余，且语义错误：zclaw batch 过期应只影响 token 配额，不应清零存储配额。

**修复**：删除 zclawMember 检查。

### Fix 4：月包有效但席位冻结时短路返回 0

数据库验证发现：企业有企业级月包（`subjectType: "enterprise"`, `status: "active"`），`hasActiveB2BMonthlyPlan = true`。但用户的席位 entitlement 全部 `frozen`（旧月包席位已冻结，新月包未分配席位）→ `packageStorageBytes = 0n`。

`zclaw.service.ts:10240` 条件 `if (hasActiveB2BMonthlyPlan)` 直接返回 `quotaBytes: 0n`，跳过了 `memberDefaultWorkspaceQuotaBytes`（5GB）的 default quota 逻辑。

**修复**：条件改为 `if (hasActiveB2BMonthlyPlan && packageStorageBytes > 0n)`。有活跃席位时用席位配额；无活跃席位时 fall through 到 default quota。

### Fix 5：batch 模式跳过 hasUserTokenEntitlement

前端 `resolveVisibleTokenBalance` 在使用 `legacyQuota`（zclaw batch 数据）前，先检查 `hasUserTokenEntitlement(entitlementSummary)`。API 响应 `batches` 字段含 frozen token batches → `hasUserTokenEntitlement` 返回 true → 使用 `availableTokens`（=0，因 frozen 被过滤 + `resolveLegacyB2BAvailableTokens` 返回 0 因 `hasActiveMonthlyPlan=true`）→ 显示 0 而非 zclaw batch 的 945591。

**修复**：`ZclawShell.tsx:257` batch 模式跳过 `hasUserTokenEntitlement`，直接用 legacy quota（zclaw batch 数据），与 token/conversation 模式同样的 pattern。

### Fix 6：freezeEntitlements 不跳过 batch 模式

`entitlement.service.ts:1660` `freezeEntitlements` 跳过 `unlimited`/`token`/`conversation` 模式，但**不跳过 batch 模式**。batch 模式下仍尝试从 entitlement 扣减 → 所有批次 frozen → `INSUFFICIENT_CREDITS`（"Token 额度已用尽，请联系管理员充值或购买补充包"）。

batch 模式的 token 消费通过 `zclaw_enterprise_token_usage_settlements` 跟踪，不走 entitlement 批次。

**修复**：条件加 `|| quotaConfig?.quotaMode === 'batch'`。

### Fix 7：settleEnterpriseTokenUsageIfNeeded 中 batch 结算被 hasConsumable 拦截

`zclaw.service.ts:2234-2247`，`hasConsumableBillingTokenEntitlement` 在 B2B 企业有月包时返回 `true`，导致 batch 模式走非 batch 结算路径（`enterpriseTokenQuotaService.settleMessageTokenUsage`）并 return，跳过 batch 结算路径（`enterpriseTokenBatchQuotaService.settleMessageTokenUsage`）。

**修复**：将 batch 模式检查移到 `hasConsumable` 之前（与 conversation/unlimited/token 同 pattern）。

### Fix 8：useBillingEntitlements 不排除 batch 模式

`zclaw.service.ts:2035-2039`，`useBillingEntitlements` 排除了 `conversation`/`unlimited`/`token`，但没排除 `batch`。B2B 企业有月包 → `hasConsumableBillingEntitlement = true` → `useBillingEntitlements = true` → 走 billing 路径（freeze/capture）→ 跳过 `settleEnterpriseTokenUsageIfNeeded` → batch 结算表无记录。

**修复**：排除条件加 `quotaMode !== ZCLAW_QUOTA_MODE_BATCH`。

### Fix 9：UserTokenDetailsDialog batch 特判用错 API

`UserTokenDetailsDialog.tsx:269-274`，ledgers tab 对 batch 模式调 `listUserTokenLedgersApi`（查 entitlement ledger 表），但 Fix 6+8 后 batch 消费写入 settlement 表（`listUserTokenQuotaRecordsApi` 查的表）。所有模式结算都写 settlement 表，batch 特判是 Fix 6 前的遗留。

**修复**：ledgers tab 统一用 `listUserTokenQuotaRecordsApi`，删除 batch 特判及 orphan（`LedgerRow`/`ledgerItems`/`ledgerTypeLabel`/`listUserTokenLedgersApi`/`UserTokenLedgerItem`）。grant 发放记录仍在"套餐记录"tab（batch 模式该 tab 可见）。

### Fix 10：BillingPurchaseDialog allowedPlanTypes 不考虑 postExpiryPurchaseMode

`BillingPurchaseDialog.tsx:272`，`allowedPlanTypes` 没考虑 `postExpiryPurchaseMode`。B2B 企业一律用 `B2B_PLAN_TYPES` 过滤，把后端 `listPreview`（self_purchase 模式返回 consumer plans）的结果全滤掉了。

**修复**：`enterpriseKind === 'b2b' && postExpiryPurchaseMode !== 'self_purchase'` 时才用 B2B_PLAN_TYPES，否则用 CONSUMER_PLAN_TYPES。

## Fix 11：self_purchase 模式下 zclaw batch token 检查缺 account_expired 拦截

### 问题现象（用户 d975f2e1）

self_purchase 模式下，对话时仍报 "Token 额度不够"（`tokenQuotaExhausted` i18n key），而期望显示 "账户已过期"（`accountExpired`） + "立即续费" action。

### 根因

`assertEnterpriseTokenQuotaIfNeeded`（`zclaw.service.ts:2054-2090`）在 batch 模式下调用 `assertBatchTokenQuotaAvailable`（`enterprise-token-batch-quota.service.ts:398`），后者只检查 zclaw batch 自身的 validity + 余额：

- `ZclawTokenBatchExpiredError`（"Token 配额已过期，请联系组织管理员调整额度"）
- `ZclawTokenBatchQuotaExceededError`（"Token 配额已用尽，请联系组织管理员调整额度"）

但**没有**像 `getWorkspaceQuotaConfig:10345-10357` 那样先检查 `postExpiryConfig.mode === 'self_purchase' && !hasActiveConsumerMonthlyPlan` → `ACCOUNT_EXPIRED`。

### 触发场景

1. 用户之前 session 存在（workspace check 跳过 — `createSession` line 5517 `if (dto.sessionId?.trim()) return`）
2. zclaw batch 已过有效期 / token 用完（self_purchase 模式下 zclaw batch 只是历史遗留分配）
3. 用户没有 active consumer monthly plan
4. → `assertBatchTokenQuotaAvailable` 抛 `ZclawTokenBatchQuotaExceededError` / `ZclawTokenBatchExpiredError`
5. → 前端翻译为 `tokenQuotaExhausted` / `tokenQuotaExpiredAdmin` — 而不是 `accountExpired`

### 修复

在 `assertEnterpriseTokenQuotaIfNeeded`（`zclaw.service.ts:2082`）调用 `assertBatchTokenQuotaAvailable` 之前，先调用私有方法 `assertSelfPurchaseAccountValidity(enterpriseId, userId)`：
- 查 `enterprisePostExpiryPurchaseConfig` 取 `mode`
- `mode === 'self_purchase'` → 调 `hasActiveConsumerMonthlyPlan`（已有 zclaw.service.ts:10370）
- 无 consumer plan → 抛 `ForbiddenException({ code: 'ACCOUNT_EXPIRED', message: '账户已过期，请续费', reason: 'account_expired' })`

复用 `assertWorkspaceConversationAllowed` 的 `ACCOUNT_EXPIRED` 错误结构（同一 code 字符串），前端 `resolveZclawStreamCaughtError` 通过 `'account_expired'` reason 命中 `accountExpired` / `accountExpiredAction` 文案与"立即续费"按钮。

### 验收标准

- self_purchase 模式 + 无 consumer plan + zclaw batch expired / token 用完 → 抛 `ACCOUNT_EXPIRED`（非 `ZCLAW_TOKEN_BATCH_*`）
- admin_purchase / contact_admin 模式行为不变（仍走原 zclaw batch 错误）
- `accountExpired` / `accountExpiredAction` 文案与"立即续费"action 正常显示
- `hasActiveConsumerMonthlyPlan` 单元测试 + batch token check 集成测试覆盖

## 验收标准

1. ✅ `assignMemberToBatch` upsert update 分支含 `validFrom: null, validTo: null`
2. ✅ `computeAccountValidity` 对有效 zclaw batch 返回 active/expiring_soon（非 null）
3. ✅ 删除 zclawMember 冗余检查
4. ✅ `hasActiveB2BMonthlyPlan && packageStorageBytes > 0n` — 席位冻结时 fall through
5. ✅ batch 模式跳过 `hasUserTokenEntitlement`，直接用 zclaw batch 数据
6. ✅ `freezeEntitlements` 跳过 batch 模式
7. ✅ batch 结算路径在 `hasConsumable` 之前
8. ✅ `useBillingEntitlements` 排除 batch 模式
9. ✅ ledgers tab 统一用 `listUserTokenQuotaRecordsApi`
10. ✅ `allowedPlanTypes` 考虑 `postExpiryPurchaseMode`
11. ✅ `assertWorkspaceConversationAllowed` / `assertWorkspaceWriteAllowed` 抛 `ACCOUNT_EXPIRED`
12. ✅ `assertEnterpriseTokenQuotaIfNeeded` 在 batch 分支前 self_purchase + !hasConsumerPlan → `ACCOUNT_EXPIRED`（Fix 11）
13. ✅ 61+/61+ zclaw 测试通过（含新测试）
14. ✅ spec 文档已更新（`quota-mode-architecture.md` + `component-patterns.md` + `quota-display-patterns.md`）
