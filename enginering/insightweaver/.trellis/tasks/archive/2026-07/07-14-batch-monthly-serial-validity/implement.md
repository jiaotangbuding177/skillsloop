# 执行计划：批次与月包串行有效期排队模型（Phase 1 修订）

## 前置条件

- PRD 已审查并确认
- design.md 已审查并确认

## 实施步骤

### Step 1: computeAccountValidity 简化（后端）

**文件**: `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts`

**改动**:
1. `computeAccountValidity` 方法重写：查 active monthly_plan 批次，直接返回 `{ validFrom, validUntil, status }`
2. 删除 `findContinuousRangeContainingNow` 方法
3. 删除回退查 token/storage 的逻辑（line 1005-1020）
4. 新增 `validityStatus` 辅助方法（active/expiring_soon/expired 判断）

**验证**:
- `pnpm --filter @insightweaver/api test` — 更新涉及 computeAccountValidity 的测试
- 手动验证：有 active 批次返回日期；无 active 返回 null

**风险**: 返回值结构变化（增加 status），需检查调用点 `entitlement.service.ts:1005` 和 `4964`

### Step 2: 更新 computeAccountValidity 测试（后端）

**文件**: `apps/api/src/zclaw/enterprise-token-batch-quota.service.test.ts`

**改动**:
1. 更新 `computeAccountValidity returns validUntil for single monthly plan` 测试
2. 更新 `computeAccountValidity merges overlapping monthly plans` 测试——改为"只读 active 批次，不合并"
3. 更新 `computeAccountValidity returns first continuous range end when gap exists` 测试——改为"无 active 返回 null"
4. 更新 `computeAccountValidity returns null when no monthly plan` 测试
5. 新增"冻结后返回 null"测试

**验证**: `pnpm --filter @insightweaver/api test` — 所有 computeAccountValidity 测试通过

### Step 3: 冻结/解冻 monthly_plan anchor API（后端）

**文件**:
- `apps/api/src/billing/entitlement.service.ts` — 新增 `freezeMonthlyPlanAnchor` / `unfreezeMonthlyPlanAnchor`
- `apps/api/src/billing/entitlement.controller.ts` — 新增 `POST freeze-monthly-plan` / `POST unfreeze-monthly-plan`

**改动**:
1. 新增 `freezeMonthlyPlanAnchor` 方法（参考 `freezeActivePoolBatch` 结构，放宽限制）
2. 新增 `unfreezeMonthlyPlanAnchor` 方法（参考 `unfreezePoolBatch` 结构）
3. Controller 新增两个端点
4. 验证 ledger 写入正确

**验证**:
- `pnpm --filter @insightweaver/api test` — 现有测试不破坏
- 新增测试：冻结 → status=frozen + ledger；解冻 → status=active + ledger
- 新增测试：冻结后 hasActiveMonthlyPlan=false，解冻后=true

### Step 4: 前端 API 函数（前端）

**文件**: `apps/web/src/api/moudles/billing.ts`

**改动**: 新增 `freezeMonthlyPlanApi` / `unfreezeMonthlyPlanApi` 函数

**验证**: `pnpm --filter @insightweaver/web lint` — 无 lint 错误

### Step 5: 批次列表页冻结/解冻按钮（前端）

**文件**: `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/page.tsx`

**改动**:
1. 对 `isB2bMonthlyAnchor(batch)` 的批次，在操作区显示冻结/解冻按钮
2. active → "冻结"按钮；frozen → "解冻"按钮
3. 调用 `freezeMonthlyPlanApi` / `unfreezeMonthlyPlanApi`

**验证**:
- `pnpm --filter @insightweaver/web lint` — 无 lint 错误
- 手动验证：列表页对 monthly_plan anchor 显示按钮

### Step 6: 批次详情页冻结/解冻按钮（前端）

**文件**: `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/[batchId]/page.tsx`

**改动**: 对 `isB2bMonthlyAnchor(batch)` 的批次，在详情页操作区显示冻结/解冻按钮

**验证**:
- `pnpm --filter @insightweaver/web lint` — 无 lint 错误
- 手动验证：详情页对 monthly_plan anchor 显示按钮

### Step 7: 前端引导逻辑（前端，复用已有逻辑）

**文件**: `apps/web/src/components/zclaw/ZclawShell.tsx`

**已有逻辑**: `apps/web/src/lib/workspace-quota-message.ts` 的 `resolveWorkspaceQuotaLimitMessage` 已实现完整的 purchaseMode 引导（self_purchase/admin_purchase/contact_admin）。i18n 键已存在。

**改动**:
1. accountValidity = null 时，展示"账号失效" + 复用已有引导逻辑
2. purchaseMode 从 workspaceUsage 或 enterprise 配置获取

**i18n**: 无需新增（已有 `consumerMonthlyExpiredAction` / `b2bEnterpriseEntitlementExpiredSelfPurchaseAction` / `b2bEnterpriseEntitlementExpiredAdminPurchaseAction`）

**验证**:
- `pnpm --filter @insightweaver/web lint` — 无 lint 错误
- 手动验证：accountValidity=null 时按 purchaseMode 显示引导

### Step 8: 批次审计页面 summary 卡片验证

**文件**: `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/page.tsx`

**改动**: 验证 accountValidity=null 时显示"账号失效"（已有 i18n key `accountValidityExpired`）

**验证**: 手动验证 null 场景

### Step 9: 全量测试 + 类型检查

**命令**:
- `pnpm tsgo` — 类型检查
- `pnpm --filter @insightweaver/api test` — 后端测试
- `pnpm --filter @insightweaver/web lint` — 前端 lint

**验证**: 所有测试通过，无类型错误，无 lint 错误

## 验证命令汇总

```bash
# 后端测试
pnpm --filter @insightweaver/api test

# 前端 lint
pnpm --filter @insightweaver/web lint

# 类型检查
pnpm tsgo
```

## 风险文件

| 文件 | 风险 | 回滚点 |
|---|---|---|
| `enterprise-token-batch-quota.service.ts` | computeAccountValidity 重写 | git revert |
| `entitlement.service.ts` | 新增冻结/解冻方法 | 独立方法，可单独回滚 |
| `entitlement.controller.ts` | 新增端点 | 独立端点，可单独回滚 |
| `ZclawShell.tsx` | 引导逻辑 | 引导分支独立，可单独回滚 |

## 实施顺序

1. Step 1-2（后端 computeAccountValidity）→ 测试通过
2. Step 3（后端冻结/解冻 API）→ 测试通过
3. Step 4-6（前端 API + 按钮）→ lint 通过
4. Step 7-8（前端引导 + 验证）→ lint 通过
5. Step 9（全量测试）→ 全部通过
