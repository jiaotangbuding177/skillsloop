# Token Mode 配额系统研究：月度重置与账户有效性

**研究日期**: 2026-07-21  
**研究目标**: 验证 token mode 的月度自动重置逻辑、账户有效性检查的门控机制、测试覆盖率

---

## 研究目标 1: Token Mode 月度自动重置

### 核心逻辑位置

**文件**: `apps/api/src/zclaw/enterprise-token-quota.service.ts`

#### 1.1 月度窗口重置函数 (Lines 278-304)

```typescript
private async resetMonthlyWindowIfNeeded(
  enterpriseId: string,
  userId: string,
  windowStart: Date | null,
) {
  const monthStartRows = await this.prisma.$queryRaw<{ monthStart: Date }[]>`
    SELECT DATE_TRUNC('month', NOW()) AS "monthStart"
  `;
  const currentMonthStart = monthStartRows[0]?.monthStart;
  if (!currentMonthStart) {
    return;
  }
  if (windowStart && windowStart >= currentMonthStart) {
    return;  // 窗口还在当月，不重置
  }

  await this.prisma.$executeRaw`
    UPDATE "zclaw_enterprise_conversation_quota_usages"
    SET
      "tokenUsed" = 0,
      "windowStart" = DATE_TRUNC('month', NOW()),
      "windowEnd" = DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 microsecond',
      "updatedAt" = NOW()
    WHERE "enterpriseId" = ${enterpriseId}
      AND "userId" = ${userId}
  `;
}
```

**状态**: ✅ **完整**

**逻辑说明**:
- 使用 PostgreSQL 的 `DATE_TRUNC('month', NOW())` 计算当月起始时间
- 如果 `windowStart >= currentMonthStart`，说明窗口还在当月，跳过重置
- 否则将 `tokenUsed` 重置为 0，更新 `windowStart` 和 `windowEnd` 为新的月度窗口

#### 1.2 Token 使用结算时触发重置 (Lines 72-148)

```typescript
async settleMessageTokenUsage(
  enterpriseId: string,
  userId: string,
  messageId: string,
  usagePayload: ZclawTokenUsagePayload,
  quotaMode?: string | null,
) {
  // ... 前置检查和 settlement 记录 ...
  
  const usage = await this.prisma.zclawEnterpriseConversationQuotaUsage.findUnique({
    where: { enterpriseId_userId: { enterpriseId, userId } },
    select: { windowStart: true },
  });
  await this.resetMonthlyWindowIfNeeded(enterpriseId, userId, usage?.windowStart ?? null);

  await this.prisma.zclawEnterpriseConversationQuotaUsage.update({
    where: { enterpriseId_userId: { enterpriseId, userId } },
    data: {
      tokenUsed: { increment: tokens },
      updatedAt: new Date(),
    },
  });
}
```

**状态**: ✅ **完整**

**逻辑说明**:
- 每次结算 token 使用时（Line 139），都会调用 `resetMonthlyWindowIfNeeded`
- 这确保了跨月时自动重置 token 使用量
- 适用于所有使用 `enterpriseTokenQuotaService.settleMessageTokenUsage` 的模式，包括 **token mode**

#### 1.3 Token Mode 结算路径 (zclaw.service.ts Lines 2186-2195)

```typescript
if (quotaMode === 'token') {
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

**状态**: ✅ **完整**

**逻辑说明**:
- Token mode 直接调用 `enterpriseTokenQuotaService.settleMessageTokenUsage`
- 该函数内部会触发月度窗口检查和重置
- 不受 billing entitlement 影响（Line 2186-2195 在 billing 检查之前）

### 月度重置结论

✅ **Token mode 的月度自动重置逻辑完整**：
- 通过 `resetMonthlyWindowIfNeeded` 实现
- 在每次 token 结算时自动检查并重置
- 使用 PostgreSQL 的 `DATE_TRUNC` 函数确保月度边界准确

---

## 研究目标 2: Token Mode 不检查账户有效性

### 后端门控机制

#### 2.1 getEnterpriseWorkspaceQuotaConfig (zclaw.service.ts Lines 10207-10237)

```typescript
if (quotaConfig?.quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  const validity = await this.enterpriseTokenBatchQuotaService
    .computeAccountValidity(enterpriseId, userId, now);
  if (!validity || validity.status === "expired") {
    return {
      quotaBytes: 0n,
      hasActiveMonthlyPlan: false,
      hasUsableBillingEntitlement: false,
      quotaSource: "default_quota",
      entitlementExpiredReason: "account_expired",
      entitlementExpiredMessage: "账户已过期，空间配额不可用",
    };
  }
  // ... batch mode 的额外检查 ...
}
```

**状态**: ✅ **完整**

**逻辑说明**:
- `computeAccountValidity` **仅在** `quotaMode === ZCLAW_QUOTA_MODE_BATCH` 时调用
- Token mode、conversation mode、unlimited mode **完全跳过**账户有效性检查
- 这些模式直接返回 `quotaBytes = baseQuotaBytes + packageStorageBytes`（Line 10238）

#### 2.2 Entitlement Service getSummary (entitlement.service.ts Lines 1028-1047)

```typescript
// account validity is a batch-mode-only concept; conversation/token/unlimited do not surface it
if (quotaConfig?.quotaMode === 'batch') {
  const validity = await this.enterpriseTokenBatchQuotaService
    .computeAccountValidity(query.enterpriseId, query.userId, now);
  if (validity) {
    const daysUntilExpiry = Math.ceil(
      (validity.validUntil.getTime() - now.getTime()) / (1000 * 60 * 60 * 24),
    );
    accountValidity = {
      validFrom: validity.validFrom.toISOString(),
      validUntil: validity.validUntil.toISOString(),
      status:
        daysUntilExpiry <= 0
          ? "expired"
          : daysUntilExpiry <= 7
            ? "expiring_soon"
            : "active",
    };
  }
}
```

**状态**: ✅ **完整**

**逻辑说明**:
- 注释明确说明："account validity is a batch-mode-only concept"
- 只有 `quotaMode === 'batch'` 时才计算 `accountValidity`
- Token mode 返回 `accountValidity = null`

### 前端门控机制

#### 2.3 resolveAccountValidityDisplay (account-validity-display.ts Lines 28-30)

```typescript
export function resolveAccountValidityDisplay(input: {
  quotaMode: string | null | undefined;
  accountValidity: AccountValidityInfo | null;
  hasOrg: boolean;
  effectivePurchaseMode: PurchaseMode;
}): AccountValidityDisplay {
  const isBatch = input.quotaMode === "batch";
  const hasAccountValidity = isBatch && Boolean(input.accountValidity);
  const showInvalid = isBatch && !hasAccountValidity && input.hasOrg;
  // ...
}
```

**状态**: ✅ **完整**

**逻辑说明**:
- `hasAccountValidity` 仅在 `isBatch && accountValidity != null` 时为 true
- Token mode 下 `isBatch = false`，因此 `hasAccountValidity = false`
- 前端不会显示账户有效期相关的 UI 元素（徽章、过期提示等）

#### 2.4 ZclawShell 中的使用 (ZclawShell.tsx Lines 391-393)

```typescript
const validityDisplay = resolveAccountValidityDisplay({
  quotaMode,
  accountValidity,
  hasOrg: Boolean(orgId),
  effectivePurchaseMode: /* ... */,
});
```

**状态**: ✅ **完整**

**逻辑说明**:
- 传入 `quotaMode` 和 `accountValidity`
- 对于 token mode，`accountValidity` 从后端返回 `null`
- `resolveAccountValidityDisplay` 进一步确保只显示 batch mode 的有效期

### 账户有效性结论

✅ **Token mode 不检查账户有效性的逻辑完整**：
- 后端 `getEnterpriseWorkspaceQuotaConfig` 仅在 batch mode 调用 `computeAccountValidity`
- 后端 `entitlement.service.getSummary` 仅在 batch mode 计算 `accountValidity`
- 前端 `resolveAccountValidityDisplay` 仅在 batch mode 显示有效期信息
- 三层门控确保 token mode 完全绕过账户有效性检查

---

## 研究目标 3: 测试覆盖率

### 3.1 Token Mode 行为测试

**文件**: `apps/api/src/zclaw/__tests__/quota-mode-backend.test.ts`

#### 测试用例 (Lines 203-227)

```typescript
test("token mode: settles via token quota service [regression B2]", async () => {
  // Even with billing entitlement, token mode should settle via token quota service
  const svc = createService({ quotaMode: "token", hasBillingEntitlement: true });

  await svc.settleEnterpriseTokenUsageIfNeeded(
    "ent-1", "user-1", "msg-1",
    { input: 100, output: 200 },
  );

  assert.equal(svc._tokenQuotaSettleCalled, true);
  assert.equal(svc._batchQuotaSettleCalled, undefined);
  // quotaMode should be "token" in the settlement [TDD]
  assert.equal(svc._lastSettleArgs?.quotaMode, "token");
});

test("token mode (no billing): settles via token quota service", async () => {
  const svc = createService({ quotaMode: "token", hasBillingEntitlement: false });

  await svc.settleEnterpriseTokenUsageIfNeeded(
    "ent-1", "user-1", "msg-1",
    { input: 100, output: 200 },
  );

  assert.equal(svc._tokenQuotaSettleCalled, true);
});
```

**状态**: ✅ **覆盖完整**

**覆盖内容**:
- Token mode 使用 `enterpriseTokenQuotaService` 结算
- 即使有 billing entitlement，token mode 也不走 billing 路径
- 验证 `quotaMode` 参数正确传递

### 3.2 账户有效性门控测试

**文件**: `apps/api/src/billing/entitlement.service.test.ts`

#### 测试用例 (Lines 2915-2951)

```typescript
test('getSummary returns null accountValidity when quotaMode is token', async () => {
  const prisma: any = {
    enterprise: {
      findFirst: async () => ({ id: ENTERPRISE_B, enterpriseKind: 'b2b' }),
    },
    enterpriseMembership: {
      findFirst: async () => ({ status: 'active' }),
    },
    entitlementBatch: {
      findMany: async () => [],
    },
    zclawEnterpriseConversationQuotaConfig: {
      findUnique: async () => ({ quotaMode: 'token' }),
    },
  };

  const enterpriseTokenBatchQuotaService = {
    computeAccountValidity: async () => {
      throw new Error('computeAccountValidity should not be called in token mode');
    },
    calculateUserTimeWindow: async () => ({ currentWindow: null, queue: [] }),
    getMemberBatchUsageSummary: async () => null,
  };

  const service = new EntitlementService(
    prisma as any,
    enterpriseTokenBatchQuotaService as any,
  );

  const summary = await service.getSummary({
    enterpriseId: ENTERPRISE_B,
    subjectType: 'enterprise_user',
    userId: USER_ID,
  });

  assert.equal(summary.accountValidity, null, 'accountValidity should be null in token mode');
});
```

**状态**: ✅ **覆盖完整**

**覆盖内容**:
- Token mode 下 `accountValidity` 返回 `null`
- 如果 `computeAccountValidity` 被调用，测试会抛出错误（防御性断言）
- 确保 token mode 完全绕过账户有效性计算

#### 对比测试 (Lines 2953-2994)

```typescript
test('getSummary computes accountValidity when quotaMode is batch', async () => {
  // ... batch mode 的测试设置 ...
  
  const summary = await service.getSummary({
    enterpriseId: ENTERPRISE_B,
    subjectType: 'enterprise_user',
    userId: USER_ID,
  });

  assert.ok(summary.accountValidity, 'accountValidity should be computed in batch mode');
  assert.equal(summary.accountValidity!.status, 'active');
  assert.equal(summary.accountValidity!.validUntil, validUntil.toISOString());
});
```

**状态**: ✅ **覆盖完整**

**覆盖内容**:
- Batch mode 下 `accountValidity` 被正确计算
- 验证了 batch mode 和 token mode 的行为差异

### 3.3 前端显示测试

**文件**: `apps/web/src/lib/__tests__/account-validity-display.test.ts`

**状态**: ✅ **覆盖完整**（137 行测试代码）

**覆盖内容**:
- 不同 quotaMode 下的显示逻辑
- Token mode 不显示账户有效期
- Batch mode 显示有效期状态（active/expiring_soon/expired）

### 3.4 月度重置测试

**状态**: ⚠️ **无直接测试**

**说明**:
- `enterprise-token-quota.service.ts` 没有专门的测试文件
- `resetMonthlyWindowIfNeeded` 是私有方法，通过 `settleMessageTokenUsage` 间接调用
- 现有测试通过 mock 验证了 token mode 的结算路径，但未验证月度重置的具体逻辑
- 月度重置依赖 PostgreSQL 的 `DATE_TRUNC` 函数，属于数据库层面的行为

**建议**:
- 可以考虑添加集成测试，验证跨月场景下的 token 使用量重置
- 或者在 `enterprise-token-quota.service.test.ts` 中添加单元测试（需要 mock Prisma 的 raw query）

### 测试覆盖率结论

✅ **Token mode 的核心行为测试覆盖完整**：
- Token mode 结算路径有明确的测试用例
- 账户有效性门控有防御性测试（调用即报错）
- 前端显示逻辑有完整测试
- Batch mode 和 token mode 的行为差异有对比测试

⚠️ **月度重置逻辑缺少直接测试**：
- 依赖数据库函数，未做单元测试
- 建议添加集成测试覆盖跨月场景

---

## 近期变更验证

### 相关提交

**提交**: `f74d1339` - "fix(quota): 策略开关收紧为 owner-only 且账户有效期仅限 batch 模式"

**日期**: 2026-07-17

**变更内容**:
- `entitlement.service.ts`: `getSummary` 门控改为 `quotaMode === 'batch'`
- `ZclawShell.tsx`: `resolveAccountValidityDisplay` 仅 batch mode 渲染
- 新增测试文件：`account-validity-display.test.ts` (137 行)
- 新增测试文件：`ZclawShell.accountValidity.test.tsx` (121 行)
- 新增测试文件：`entitlement.service.test.ts` 中的 accountValidity 测试 (120 行)

### 未提交变更检查

**检查时间**: 2026-07-21

**变更文件**:
- `apps/api/src/zclaw/zclaw.service.ts` - 有未提交变更
- `apps/api/src/billing/entitlement.service.ts` - 无变更
- `apps/web/src/lib/account-validity-display.ts` - 有未提交变更

**验证结果**:

✅ `zclaw.service.ts` 的变更**未破坏** token mode 行为：
- `getEnterpriseWorkspaceQuotaConfig` 中的 `computeAccountValidity` 仍然包裹在 `if (quotaConfig?.quotaMode === ZCLAW_QUOTA_MODE_BATCH)` 中
- Token mode 仍然跳过账户有效性检查

✅ `account-validity-display.ts` 的变更**未破坏** token mode 行为：
- `resolveAccountValidityDisplay` 仍然使用 `const isBatch = input.quotaMode === "batch"` 门控
- Token mode 仍然不显示账户有效期

### 变更验证结论

✅ **近期变更未破坏 token mode 的行为**：
- 账户有效性检查仍然仅限 batch mode
- Token mode 的月度重置逻辑未受影响
- 前端显示逻辑保持一致

---

## 总结

### 研究目标 1: Token Mode 月度自动重置

✅ **逻辑完整且正确**
- 通过 `resetMonthlyWindowIfNeeded` 实现
- 在每次 token 结算时自动触发
- 使用 PostgreSQL 的 `DATE_TRUNC` 确保月度边界准确
- 适用于所有使用 `enterpriseTokenQuotaService` 的模式

### 研究目标 2: Token Mode 不检查账户有效性

✅ **三层门控机制完整**
1. 后端 `getEnterpriseWorkspaceQuotaConfig` 仅 batch mode 调用 `computeAccountValidity`
2. 后端 `entitlement.service.getSummary` 仅 batch mode 计算 `accountValidity`
3. 前端 `resolveAccountValidityDisplay` 仅 batch mode 显示有效期

### 研究目标 3: 测试覆盖率

✅ **核心行为测试覆盖完整**
- Token mode 结算路径有测试
- 账户有效性门控有防御性测试
- 前端显示逻辑有测试
- Batch mode 和 token mode 的差异有对比测试

⚠️ **月度重置缺少直接测试**
- 建议添加集成测试覆盖跨月场景

### 近期变更验证

✅ **未破坏 token mode 行为**
- `computeAccountValidity` 仍然仅限 batch mode
- 前端显示逻辑保持一致
- Token mode 的月度重置未受影响

---

## 引用索引

| 功能点 | 文件路径 | 行号 |
|--------|----------|------|
| 月度窗口重置函数 | `apps/api/src/zclaw/enterprise-token-quota.service.ts` | 278-304 |
| Token 结算触发重置 | `apps/api/src/zclaw/enterprise-token-quota.service.ts` | 139 |
| Token mode 结算路径 | `apps/api/src/zclaw/zclaw.service.ts` | 2186-2195 |
| Workspace 配额门控 | `apps/api/src/zclaw/zclaw.service.ts` | 10207-10237 |
| Entitlement summary 门控 | `apps/api/src/billing/entitlement.service.ts` | 1028-1047 |
| 前端显示门控 | `apps/web/src/lib/account-validity-display.ts` | 28-30 |
| Token mode 结算测试 | `apps/api/src/zclaw/__tests__/quota-mode-backend.test.ts` | 203-227 |
| Token mode 账户有效性测试 | `apps/api/src/billing/entitlement.service.test.ts` | 2915-2951 |
| Batch mode 账户有效性测试 | `apps/api/src/billing/entitlement.service.test.ts` | 2953-2994 |
| 关键提交 | Git commit `f74d1339` | 2026-07-17 |
