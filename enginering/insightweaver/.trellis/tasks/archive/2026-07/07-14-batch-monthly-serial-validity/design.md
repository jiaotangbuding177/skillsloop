# 技术设计：批次与月包串行有效期排队模型（Phase 1 修订）

## 架构总览

```
monthly_plan anchor 批次
  ├── status: active   → 账号有效期有效 → token/storage 可用（检查点门控）
  ├── status: frozen   → 账号有效期失效 → token/storage 不可用
  ├── status: scheduled → 排队中，到期自动生效
  └── status: expired  → 账号失效 → token/storage 不可用
```

**核心不变量**：冻结 monthly_plan anchor 不级联冻结 token/storage，由检查点门控（`hasActiveMonthlyPlan` → `isUsableEntitlementBatch`）统一拦截。

## 后端改动

### D1: computeAccountValidity 简化

**文件**: `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts:983`

**当前**: 连续区间算法（`findContinuousRangeContainingNow`），合并多个 monthly_plan 批次日期

**改为**: 查 active monthly_plan 批次，直接返回其 validFrom/validUntil + status

```typescript
async computeAccountValidity(enterpriseId, userId, now = new Date()) {
  const activePlan = await this.prisma.entitlementBatch.findFirst({
    where: {
      enterpriseId, userId,
      subjectType: "enterprise_user",
      entitlementType: "monthly_plan",
      status: "active",
      isDeleted: false,
    },
    orderBy: { validFrom: "desc" },
  });
  if (activePlan && activePlan.validFrom <= now && activePlan.validUntil && activePlan.validUntil > now) {
    return {
      validFrom: activePlan.validFrom,
      validUntil: activePlan.validUntil,
      status: this.validityStatus(activePlan, now),
    };
  }
  return null;
}
```

**删除**: `findContinuousRangeContainingNow` 方法 + 回退查 token/storage 的逻辑

**status 计算**: active（>7天剩余）/ expiring_soon（≤7天）/ expired（已过期）——已有逻辑复用

**返回值变化**: `{ validFrom, validUntil }` → `{ validFrom, validUntil, status }`（status 前端已使用，兼容）

**影响调用点**:
- `entitlement.service.ts:1005`（getSummary）
- `entitlement.service.ts:4964`（另一个调用点）

### D2: 冻结/解冻 monthly_plan anchor API

**文件**: `apps/api/src/billing/entitlement.service.ts`

**不改动** `freezeActivePoolBatch`/`unfreezePoolBatch`——保持 pool 批次冻结逻辑不变。

**新增** `freezeMonthlyPlanAnchor` / `unfreezeMonthlyPlanAnchor`：

```typescript
async freezeMonthlyPlanAnchor(actorUserId, batchId, idempotencyKey) {
  // 1. 幂等检查（refType: "monthly_plan_freeze"）
  // 2. 查找 monthly_plan anchor（entitlementType=monthly_plan, status=active, isDeleted=false）
  // 3. status → frozen，写入 ledger（changeType: "freeze", refType: "monthly_plan_freeze"）
  // 4. 不级联 token/storage
}

async unfreezeMonthlyPlanAnchor(actorUserId, batchId, idempotencyKey) {
  // 1. 幂等检查（refType: "monthly_plan_unfreeze"）
  // 2. 查找 frozen 的 monthly_plan anchor
  // 3. 检查 validUntil 未过期
  // 4. status → active，写入 ledger（changeType: "release", refType: "monthly_plan_unfreeze"）
}
```

**Controller**: `apps/api/src/billing/entitlement.controller.ts`
- 新增 `POST entitlements/freeze-monthly-plan`
- 新增 `POST entitlements/unfreeze-monthly-plan`

**前端 API**: `apps/web/src/api/moudles/billing.ts`
- 新增 `freezeMonthlyPlanApi(batchId, idempotencyKey)`
- 新增 `unfreezeMonthlyPlanApi(batchId, idempotencyKey)`

### D3: 前端引导逻辑（复用已有逻辑）

**已有逻辑**: `apps/web/src/lib/workspace-quota-message.ts` 的 `resolveWorkspaceQuotaLimitMessage` 已实现完整的 purchaseMode 引导：
- `consumer_monthly_expired` → 引导去月包 tab（`consumerMonthlyExpiredAction`）
- `b2b_enterprise_entitlement_expired` + `self_purchase` → 自购引导（`b2bEnterpriseEntitlementExpiredSelfPurchaseAction`）
- `b2b_enterprise_entitlement_expired` + `admin_purchase` → 管理员引导（`b2bEnterpriseEntitlementExpiredAdminPurchaseAction`）

**已有 i18n**: `zh.json`/`en.json` 中上述键已存在

**文件**: `apps/web/src/components/zclaw/ZclawShell.tsx`

**改动**: accountValidity = null 时，复用 `resolveWorkspaceQuotaLimitMessage` 或直接展示对应 i18n 引导文案。purchaseMode 从 `workspaceUsage` 或 enterprise 配置获取。

**角色判断来源**: `purchaseMode` 字段（`'contact_admin' | 'admin_purchase' | 'self_purchase'`），定义在 `packages/shared/src/enterprise-kind.ts:27-29`

## 前端改动

### D4: 批次列表/详情页冻结/解冻按钮

**文件**:
- `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/page.tsx`
- `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/[batchId]/page.tsx`

**新增**: 对 `isB2bMonthlyAnchor(batch)` 的批次，在操作区显示冻结/解冻按钮
- `status=active` → 显示"冻结"按钮，调用 `freezeMonthlyPlanApi`
- `status=frozen` → 显示"解冻"按钮，调用 `unfreezeMonthlyPlanApi`

### D5: 批次审计页面 summary 卡片

**文件**: `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/page.tsx`

**已有**: accountValidity 卡片（上一步实现）
**验证**: accountValidity = null 时显示"账号失效"，i18n key `summary.accountValidity` + `accountValidityExpired` 已有

## 数据流

```
管理员冻结 monthly_plan anchor
  → POST /api/admin/billing/entitlements/freeze-monthly-plan
    → freezeMonthlyPlanAnchor()
      → batch.status = frozen
      → ledger: { changeType: "freeze", refType: "monthly_plan_freeze" }

用户消费 token
  → hasActiveMonthlyPlan (查 status: { in: ["active", "scheduled"] })
    → frozen 不在范围 → 返回 false
  → isUsableEntitlementBatch
    → requiresActiveMonthlyPlan && !hasActiveMonthlyPlan → 返回 false
    → 消费被拒绝

管理员解冻
  → POST /api/admin/billing/entitlements/unfreeze-monthly-plan
    → unfreezeMonthlyPlanAnchor()
      → batch.status = active
      → ledger: { changeType: "release", refType: "monthly_plan_unfreeze" }
  → 用户消费
    → hasActiveMonthlyPlan → true
    → isUsableEntitlementBatch → true
    → 消费成功
```

## 兼容性

- `computeAccountValidity` 返回值增加 `status` 字段——前端已使用，兼容
- `freezeActivePoolBatch`/`unfreezePoolBatch` 不改动，pool 批次冻结逻辑不受影响
- 现有测试中涉及 `computeAccountValidity` 连续区间算法的测试用例需更新

## 风险点

1. **computeAccountValidity 返回值变化**: `{ validFrom, validUntil }` → `{ validFrom, validUntil, status }`——需确认 `entitlement.service.ts:1005` 和 `4964` 调用点处理 status
2. **冻结 API 新增端点**: 需新增 controller + service 方法 + 前端 API + 前端按钮，改动面较大
3. **前端角色判断**: 引导策略需区分用户角色，需确认 enterprise 配置中是否有"用户自购开关"字段
