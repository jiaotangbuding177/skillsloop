# 设计文档：B端企业绑定C端套餐 & 三种购买模式严格分离

**日期**: 2026-07-11  
**分支**: feat/quota-expiry-ui-optimization  
**状态**: 待用户审查

---

## 背景

当前系统对B端和C端套餐实行**严格隔离**：B端企业只能绑定B端套餐，C端企业只能绑定C端套餐。这是通过 `billing-plan.service.ts` 的 `validatePlanConfig` 方法实现的。

当B端企业配置 `self_purchase`（个人购买）模式后，企业成员需要能购买C端套餐。但目前C端套餐只能绑定到C端企业，导致B端企业没有属于自己的C端套餐可供成员购买。

## 目标

1. 允许平台 admin 为B端企业创建C端套餐（放松套餐类型校验）
2. 三种购买模式严格分离：
   - `contact_admin`：无人可购买，管理员通过传统批次配额管理
   - `admin_purchase`：仅管理员/Owner可购买B端套餐
   - `self_purchase`：所有人（含admin）可购买C端套餐（个人自购，非统一采购）
3. B端企业成员在 self_purchase 模式下只能购买**本企业绑定的**C端套餐

---

## 模式权限矩阵

| 模式 | 角色 | 可购买套餐 | 购买主体 | subjectType |
|---|---|---|---|---|
| `contact_admin` | 所有人 | 不可购买 | — | — |
| `admin_purchase` | 管理员/Owner | B端套餐 | 企业 | enterprise |
| `admin_purchase` | 普通成员 | 不可购买 | — | — |
| `self_purchase` | 所有人（含admin） | C端套餐 | 个人 | enterprise_user |

---

## 改动范围

### Section 1: 后端 — 套餐类型校验放松

**文件**: `apps/api/src/billing/billing-plan.service.ts`  
**方法**: `validatePlanConfig` (line 350-453)

**当前逻辑** (line 359-361):
```ts
if (this.isConsumerPlan(planType) && !isConsumerEnterpriseKind(enterpriseKind)) {
  throw new BadRequestException('C 端套餐只能绑定 C 端企业');
}
```

**改动**: 删除或放宽此拦截，允许B端企业绑定C端套餐。

```ts
// 方案：删除跨类型拦截，仅保留 B端套餐→B端企业的正向校验
// C端套餐允许绑定到B端或C端企业
if (this.isB2BPlan(planType) && !isB2BEnterpriseKind(enterpriseKind)) {
  throw new BadRequestException('B 端企业套餐只能绑定 B 端企业');
}
// 删除: if (this.isConsumerPlan(planType) && !isConsumerEnterpriseKind(enterpriseKind)) { ... }
```

**理由**:
- `allowedEnterpriseKinds` 字段按企业 kind 设置（`[enterprise.enterpriseKind]`），C端套餐绑定到B端企业时值为 `['b2b']`
- 购买权限由 `billing-order.service.ts` 和 `entitlement.service.ts` 中的 mode 检查控制，与套餐创建时的类型校验解耦
- `private_deployment_lead` 的B端校验保持不变（line 450-452）

**`allowedEnterpriseKinds` 设置逻辑** (约 line 332): 保持不变。C端套餐绑定到B端企业时，`allowedEnterpriseKinds = ['b2b']`。

---

### Section 2: 后端 — 套餐预览/列表可见性（按 mode 过滤）

**文件**: `apps/api/src/billing/billing-plan.service.ts`  
**方法**: `assertCanPreviewBillingPlan` (line ~510-538)

**当前逻辑** (line 523-534):
```ts
if (isB2BEnterpriseKind(enterprise.enterpriseKind)) {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({...});
  if (config?.mode === 'self_purchase') {
    return; // Allow all active members to preview
  }
  if (!['owner', 'admin'].includes(membership.role)) {
    throw new ForbiddenException('billing plan preview requires enterprise admin permission');
  }
}
```

**问题**: `self_purchase` 模式下直接 return 放行所有成员预览，但没有区分B端/C端套餐类型。如果B端企业同时绑了B端和C端套餐（历史遗留），成员会看到不该看的B端套餐。

**改动**: 需要确认套餐列表 API 是否按 `enterpriseId` 查询。如果是，B端企业只会有自己绑定的套餐（B端或C端），不存在跨类型问题。但为了安全，建议在套餐列表返回时也做 mode 过滤：

```
B端 + contact_admin   → 不返回任何套餐（前端不展示购买入口）
B端 + admin_purchase  → 仅返回 B端套餐 (planType IN b2b_*)，且仅 admin/owner 可访问
B端 + self_purchase   → 仅返回 C端套餐 (planType IN consumer_*)，所有 active 成员可访问
C端                   → 维持现有逻辑
```

**实现方式**: 在套餐列表查询的 Prisma `where` 条件中加入 `planType` 过滤：
- `admin_purchase` + B端 → `planType: { in: B2B_PLAN_TYPES }`
- `self_purchase` + B端 → `planType: { in: CONSUMER_PLAN_TYPES }`

---

### Section 3: 后端 — 下单拦截增强

**文件**: `apps/api/src/billing/billing-order.service.ts`  
**方法**: `createOrder` (line ~64-96)

**现有逻辑已处理**:
- `self_purchase` + B端企业 + C端套餐 → 放行 ✅
- `admin_purchase` 的 admin 权限检查 ✅

**需要新增的反向拦截**:

```ts
// self_purchase 模式下，禁止购买 B端套餐
if (isB2BPlan && config?.mode === 'self_purchase') {
  throw new ForbiddenException('当前企业模式下不允许购买B端套餐');
}

// admin_purchase 模式下，禁止购买 C端套餐
if (isConsumerPlan && config?.mode === 'admin_purchase') {
  throw new ForbiddenException('当前企业模式下不允许购买C端套餐');
}

// contact_admin 模式下，禁止购买任何套餐
if (config?.mode === 'contact_admin') {
  throw new ForbiddenException('当前企业模式下不允许在线购买套餐');
}
```

**注意**: 这些检查应在现有的 `isConsumerPlan` / `isB2BPlan` 分支内部添加，不影响非B端企业的逻辑。

---

### Section 4: 后端 — 权益发放拦截增强

**文件**: `apps/api/src/billing/entitlement.service.ts`  
**方法**: `grantPaidOrderSnapshot` 中的套餐类型校验 (line ~3082-3101)

**与 Section 3 对称**，新增反向拦截：

```ts
// admin_purchase 模式下，禁止发放 C端套餐
if (isConsumerPlan(plan.planType) && config?.mode === 'admin_purchase') {
  throw new BadRequestException('当前企业模式下不允许发放C端套餐');
}

// self_purchase 模式下，禁止发放 B端套餐
if (isB2BPlan(plan.planType) && config?.mode === 'self_purchase') {
  throw new BadRequestException('当前企业模式下不允许发放B端套餐');
}
```

---

### Section 5: 前端 — B端企业后台按模式动态展示

**文件**: B端企业套餐管理相关页面（admin 后台）

**改动**:
- `contact_admin` → 不展示计费套餐购买入口，维持现有批次配额管理 UI
- `admin_purchase` → 展示B端套餐列表 + 管理员购买按钮
- `self_purchase` → 展示C端套餐列表 + 购买按钮（所有人可见含admin）

前端需要根据 `EnterprisePostExpiryPurchaseConfig.mode` 决定展示哪些套餐卡片和操作按钮。

---

### 不需要改动的部分

| 模块 | 原因 |
|---|---|
| `consumptionPriority` (entitlement.service.ts) | B端和C端月套餐同为 priority 0，token topup 同为 priority 1，已按有效期优先排序 |
| `hasConsumableBillingTokenEntitlement` | 已同时检查 B端月套餐和自购C端套餐 |
| `ensureB2BMonthlyEntitlementsForMember` | 仅处理 B端月套餐的 late-join 成员分发，与C端套餐无关 |
| `enterprise.service.ts` 类型切换逻辑 | 已有套餐不能切换类型的约束保持不变 |
| `allowedEnterpriseKinds` 设置逻辑 | 按企业 kind 设置即可，无需特殊处理 |

---

## 风险点

1. **历史数据兼容**: 如果已有B端企业绑定了B端套餐，切换到 `self_purchase` 后，这些B端套餐应不可见/不可购买。需要确保前端和列表 API 正确过滤。

2. **`contact_admin` 模式**: 当前 `billing-order.service.ts` 中 `contact_admin` 模式的处理逻辑需要确认——如果 mode 为 null/undefined 时的默认行为是否是 `contact_admin`。

3. **C端企业的模式**: 当前 C端企业的 `post_expiry_purchase_config` 可能为 null。需要确认 C端企业不受 B端 mode 逻辑影响。

---

## 验证计划

1. 平台 admin 为B端企业创建C端套餐 → 应成功
2. B端企业配置 `admin_purchase` → 管理员可见B端套餐、可购买；成员不可见
3. B端企业配置 `self_purchase` → 所有成员（含admin）可见C端套餐、可购买；不可购买B端套餐
4. B端企业配置 `contact_admin` → 所有人不可购买任何套餐
5. Token 消耗：同时有B端和C端权益时，按有效期优先消费
