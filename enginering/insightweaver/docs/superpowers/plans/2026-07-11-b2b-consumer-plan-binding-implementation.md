# B端企业绑定C端套餐 & 三种购买模式严格分离 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 允许平台 admin 为B端企业创建C端套餐，并通过三种购买模式（contact_admin / admin_purchase / self_purchase）严格控制谁可以购买什么类型的套餐。

**Architecture:** 放松 `validatePlanConfig` 中的套餐类型-企业类型绑定校验，允许C端套餐绑定到B端企业。在下单、权益发放、套餐预览/列表各层通过 `enterprisePostExpiryPurchaseConfig.mode` 实现三种模式的严格分离。

**Tech Stack:** NestJS (API), Next.js 15 (Web), Prisma, node:test

## Global Constraints

- TypeScript strict mode, ESM, NodeNext resolution
- 2-space indentation, logical import sorting
- `pnpm lint` must pass after each task
- B2B_PLAN_TYPES = `['b2b_enterprise_plan', 'b2b_token_topup', 'b2b_storage_topup']`
- CONSUMER_PLAN_TYPES = `['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup']`
- 模式权限矩阵：
  - `contact_admin` → 无人可购买
  - `admin_purchase` → 仅 admin/owner 购买 B端套餐
  - `self_purchase` → 所有人（含admin）购买 C端套餐（个人自购）
- C端套餐只能购买绑定在本企业的
- 不要修改 `private_deployment_lead` 相关逻辑
- 不要修改 `consumptionPriority` 逻辑

---

### Task 1: 放松套餐类型校验 + 单元测试

**Files:**
- Modify: `apps/api/src/billing/billing-plan.service.ts:359-361`
- Modify: `apps/api/src/billing/billing-plan.service.test.ts`

**Interfaces:**
- Produces: `validatePlanConfig` 允许 consumer plan types 绑定到 B2B enterprises
- 不影响 B2B plan types 的校验（仍然只允许 B2B enterprise）

#### Context

`validatePlanConfig` 位于 `billing-plan.service.ts` line 350-453。当前 line 359-361 拦截了 consumer plan 绑定到非 consumer enterprise。需要删除此拦截。

#### Steps

- [ ] **Step 1: 写失败测试 — consumer 套餐绑定到 B2B 企业应通过**

在 `apps/api/src/billing/billing-plan.service.test.ts` 中添加测试：

```typescript
test('consumer plans can be bound to b2b enterprises for self_purchase', () => {
  // consumer_monthly_plan on b2b enterprise — should NOT throw
  const result = normalizeAndValidate(
    {
      planType: 'consumer_monthly_plan',
      periodDays: 30,
      planLevel: 1,
      tokenAmount: '1000000',
      storageBytes: '1073741824',
    },
    'b2b',
  );
  assert.equal(result.planType, 'consumer_monthly_plan');
  assert.deepEqual(result.allowedEnterpriseKinds, ['b2b']);
});

test('consumer token topup can be bound to b2b enterprises', () => {
  const result = normalizeAndValidate(
    {
      planType: 'consumer_token_topup',
      periodDays: 30,
      planLevel: 1,
      tokenAmount: '1000000',
      requiresActiveMonthlyPlan: true,
    },
    'b2b',
  );
  assert.equal(result.planType, 'consumer_token_topup');
  assert.deepEqual(result.allowedEnterpriseKinds, ['b2b']);
});

test('consumer storage topup can be bound to b2b enterprises', () => {
  const result = normalizeAndValidate(
    {
      planType: 'consumer_storage_topup',
      periodDays: 30,
      planLevel: 1,
      storageBytes: '1073741824',
      requiresActiveMonthlyPlan: true,
    },
    'b2b',
  );
  assert.equal(result.planType, 'consumer_storage_topup');
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts
```
Expected: 3 个新测试 FAIL with `BadRequestException: C 端套餐只能绑定 C 端企业`

- [ ] **Step 3: 修改 validatePlanConfig 删除 consumer 类型拦截**

在 `apps/api/src/billing/billing-plan.service.ts` line 359-361，将：

```typescript
if (this.isConsumerPlan(planType) && !isConsumerEnterpriseKind(enterpriseKind)) {
  throw new BadRequestException('C 端套餐只能绑定 C 端企业');
}
```

改为删除这两行（仅保留 B2B plan 的正向校验）。

- [ ] **Step 4: 运行测试确认通过**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts
```
Expected: 所有测试 PASS

- [ ] **Step 5: 添加回归测试 — B2B plan 仍然只能绑定 B2B 企业**

```typescript
test('b2b plans still cannot be bound to consumer enterprises', () => {
  assert.throws(
    () =>
      normalizeAndValidate(
        {
          planType: 'b2b_enterprise_plan',
          periodDays: 30,
          planLevel: 1,
          memberLimit: 10,
          tokenAmount: '1000000',
          storageBytes: '1073741824',
        },
        'consumer',
      ),
    (err: any) => err.message.includes('B 端企业套餐只能绑定 B 端企业'),
  );
});
```

- [ ] **Step 6: 运行全部测试确认通过**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts
```

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/billing/billing-plan.service.ts apps/api/src/billing/billing-plan.service.test.ts
git commit -m "feat: allow consumer plans to bind to b2b enterprises for self_purchase"
```

---

### Task 2: 下单拦截增强 + 单元测试

**Files:**
- Modify: `apps/api/src/billing/billing-order.service.ts:64-97`
- Modify: `apps/api/src/billing/billing-order.service.test.ts`

**Interfaces:**
- Consumes: `EnterprisePostExpiryPurchaseConfig` (mode field)
- Produces: 三种模式严格隔离的下单校验

#### Context

`billing-order.service.ts` line 64-97 已有 consumer plan 在 B2B 企业下的 `self_purchase` 检查。需要在两个分支中补充反向拦截和 `contact_admin` 拦截。

当前逻辑摘要：
- Line 69-81: `isConsumerPlan` 分支 — B2B 企业时要求 mode=`self_purchase`
- Line 82-94: `isB2BPlan` 分支 — B2B 企业时检查 mode≠`contact_admin`
- Line 96: 不支持的套餐类型报错

#### Steps

- [ ] **Step 1: 写失败测试 — 三种模式的拦截矩阵**

在 `apps/api/src/billing/billing-order.service.test.ts` 中添加测试：

```typescript
// ===== admin_purchase mode =====

test('admin_purchase mode: admin can buy b2b plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => b2bPlan() },
    membership: { findFirst: async () => ({ role: 'admin', status: 'active' }) },
    activeMonthlyPlan: { count: async () => 1 },
    purchaseConfig: { findUnique: async () => ({ mode: 'admin_purchase' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    membershipRole: { findFirst: async () => ({ role: 'admin' }) },
    order: { create: async (data: any) => order({ ...data, id: 'new-order' }) },
  });

  const result = await service.createOrder(
    { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
    USER_ID,
  );
  assert.equal(result.subjectType, 'enterprise');
});

test('admin_purchase mode: member cannot buy b2b plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => b2bPlan() },
    membership: { findFirst: async () => ({ role: 'member', status: 'active' }) },
    activeMonthlyPlan: { count: async () => 1 },
    purchaseConfig: { findUnique: async () => ({ mode: 'admin_purchase' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    membershipRole: { findFirst: async () => ({ role: 'member' }) },
    order: { create: async () => { throw new Error('should not reach'); } },
  });

  await assert.rejects(
    () => service.createOrder(
      { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
      USER_ID,
    ),
    ForbiddenException,
  );
});

test('admin_purchase mode: cannot buy consumer plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => consumerPlan() },
    membership: { findFirst: async () => ({ role: 'admin', status: 'active' }) },
    purchaseConfig: { findUnique: async () => ({ mode: 'admin_purchase' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    order: { create: async () => { throw new Error('should not reach'); } },
  });

  await assert.rejects(
    () => service.createOrder(
      { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
      USER_ID,
    ),
    ForbiddenException,
  );
});

// ===== self_purchase mode =====

test('self_purchase mode: member can buy consumer plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => consumerPlan() },
    membership: { findFirst: async () => ({ role: 'member', status: 'active' }) },
    purchaseConfig: { findUnique: async () => ({ mode: 'self_purchase' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    order: { create: async (data: any) => order({ ...data, id: 'new-order' }) },
  });

  const result = await service.createOrder(
    { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
    USER_ID,
  );
  assert.equal(result.subjectType, 'enterprise_user');
  assert.equal(result.subjectUserId, USER_ID);
});

test('self_purchase mode: cannot buy b2b plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => b2bPlan() },
    membership: { findFirst: async () => ({ role: 'admin', status: 'active' }) },
    purchaseConfig: { findUnique: async () => ({ mode: 'self_purchase' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    order: { create: async () => { throw new Error('should not reach'); } },
  });

  await assert.rejects(
    () => service.createOrder(
      { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
      USER_ID,
    ),
    ForbiddenException,
  );
});

// ===== contact_admin mode =====

test('contact_admin mode: cannot buy any plan', async () => {
  const service = createService({
    billingPlan: { findUnique: async () => b2bPlan() },
    membership: { findFirst: async () => ({ role: 'admin', status: 'active' }) },
    purchaseConfig: { findUnique: async () => ({ mode: 'contact_admin' }) },
    enterprise: { findUnique: async () => ({ id: ENTERPRISE_ID, enterpriseKind: 'b2b', name: 'B2B enterprise' }) },
    order: { create: async () => { throw new Error('should not reach'); } },
  });

  await assert.rejects(
    () => service.createOrder(
      { enterpriseId: ENTERPRISE_ID, planId: PLAN_ID, payType: 'NATIVE' },
      USER_ID,
    ),
    ForbiddenException,
  );
});
```

注意：`b2bPlan()` 和 `consumerPlan()` 是测试辅助函数，需要在测试文件中定义（参考现有的 `plan()` 函数，添加一个 B2B 版本）。

- [ ] **Step 2: 运行测试确认失败**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-order.service.test.ts
```
Expected: 新测试 FAIL（部分通过是因为已有逻辑覆盖了部分场景，但 `admin_purchase` 禁 consumer、`self_purchase` 禁 b2b、`contact_admin` 全禁 的测试应失败）

- [ ] **Step 3: 修改 createOrder 授权逻辑**

在 `apps/api/src/billing/billing-order.service.ts`，找到 line 64-97 的授权决策树。

**修改 `isConsumerPlan` 分支 (line 69-81)**：在 B2B 企业的 `self_purchase` 检查之后（line 77 之后），添加 `admin_purchase` 模式的拦截：

```typescript
if (isConsumerPlan) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId: dto.enterpriseId },
      select: { mode: true },
    });
    if (config?.mode !== 'self_purchase') {
      throw new ForbiddenException('当前企业未开放成员自行购买权限');
    }
    // 新增：admin_purchase 模式下禁止购买C端套餐
    if (config?.mode === 'admin_purchase') {
      throw new ForbiddenException('当前企业模式下不允许购买C端套餐');
    }
  } else if (!['consumer', 'evomind_consumer'].includes(enterpriseKind)) {
    throw new ForbiddenException('C 端套餐仅适用于 C 端企业');
  }
  await this.assertActiveMembership(dto.enterpriseId, buyerUserId);
}
```

实际上，由于上面已经检查了 `config?.mode !== 'self_purchase'` 会 throw，所以 `admin_purchase` 的额外检查在 B2B 分支是冗余的。**但**对于 `contact_admin` 模式，`config?.mode !== 'self_purchase'` 已经会 throw，所以 B2B + consumer 的所有非 self_purchase 模式都被拦截了。

**关键改动在 `isB2BPlan` 分支 (line 82-94)**：当前只检查了 `contact_admin`，需要补充 `self_purchase` 模式的拦截：

当前代码 (line 83-89):
```typescript
if (enterpriseKind === 'b2b') {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId: dto.enterpriseId },
    select: { mode: true },
  });
  if (config != null && config.mode === 'contact_admin') {
    throw new ForbiddenException('当前企业未开放管理员购买权限');
  }
}
```

改为：
```typescript
if (enterpriseKind === 'b2b') {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId: dto.enterpriseId },
    select: { mode: true },
  });
  if (config?.mode === 'contact_admin') {
    throw new ForbiddenException('当前企业模式下不允许在线购买套餐');
  }
  if (config?.mode === 'self_purchase') {
    throw new ForbiddenException('当前企业模式下不允许购买B端套餐');
  }
  // admin_purchase 或 null 时放行
}
```

注意改动：
1. `config != null && config.mode === 'contact_admin'` → `config?.mode === 'contact_admin'`（简化，`null` 时 `config?.mode` 为 `undefined`，不等于 `'contact_admin'`）
2. 新增 `self_purchase` 模式拦截

**对于 consumer plan 的 B2B 分支**，当前 `config?.mode !== 'self_purchase'` 已经拦截了 `admin_purchase` 和 `contact_admin`，所以**不需要额外修改**。但为了错误消息更明确，可以改为：

```typescript
if (isConsumerPlan) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId: dto.enterpriseId },
      select: { mode: true },
    });
    if (config?.mode === 'contact_admin') {
      throw new ForbiddenException('当前企业模式下不允许在线购买套餐');
    }
    if (config?.mode === 'admin_purchase') {
      throw new ForbiddenException('当前企业模式下不允许购买C端套餐');
    }
    if (config?.mode !== 'self_purchase') {
      throw new ForbiddenException('当前企业未开放成员自行购买权限');
    }
  } else if (!['consumer', 'evomind_consumer'].includes(enterpriseKind)) {
    throw new ForbiddenException('C 端套餐仅适用于 C 端企业');
  }
  await this.assertActiveMembership(dto.enterpriseId, buyerUserId);
}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-order.service.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/billing/billing-order.service.ts apps/api/src/billing/billing-order.service.test.ts
git commit -m "feat: enforce strict mode separation in order creation"
```

---

### Task 3: 权益发放拦截增强 + 单元测试

**Files:**
- Modify: `apps/api/src/billing/entitlement.service.ts:3082-3101` (assertPlanGrantTarget 中的 consumer plan 校验)
- Modify: `apps/api/src/billing/entitlement.service.test.ts` (添加对应测试)

**Interfaces:**
- Consumes: `EnterprisePostExpiryPurchaseConfig` mode
- Produces: 与 Task 2 对称的权益发放拦截

#### Context

`entitlement.service.ts` 的 `assertPlanGrantTarget` 方法（约 line 3082-3101）有与 `billing-order.service.ts` 类似的 consumer plan 校验。需要添加对称的反向拦截。

当前 consumer plan 分支 (line 3082-3101):
```typescript
if (['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup'].includes(plan.planType)) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({...});
    if (config?.mode !== 'self_purchase') {
      throw new BadRequestException('当前企业未开放成员自行购买权限');
    }
  } else if (!['consumer', 'evomind_consumer'].includes(enterpriseKind)) {
    throw new BadRequestException('C 端套餐只能发放给 C 端企业');
  }
  if (dto.subjectType !== 'enterprise_user' || !dto.userId) {
    throw new BadRequestException('C 端套餐只能发放给企业用户主体');
  }
}
```

B2B plan 分支没有检查 mode。需要添加。

#### Steps

- [ ] **Step 1: 写失败测试**

在 `apps/api/src/billing/entitlement.service.test.ts` 中添加测试（参考现有测试的模式，使用 `node:test`）：

```typescript
test('assertPlanGrantTarget: self_purchase mode rejects b2b plan grant', async () => {
  // B2B enterprise + self_purchase mode + b2b plan → should reject
  // 具体 mock 结构参考现有 entitlement.service.test.ts 的测试模式
});

test('assertPlanGrantTarget: admin_purchase mode rejects consumer plan grant', async () => {
  // B2B enterprise + admin_purchase mode + consumer plan → should reject
});

test('assertPlanGrantTarget: contact_admin mode rejects all plan grants', async () => {
  // B2B enterprise + contact_admin mode → should reject both b2b and consumer plans
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd apps/api && pnpm exec tsx --test src/billing/entitlement.service.test.ts --test-name-pattern="assertPlanGrantTarget"
```

- [ ] **Step 3: 修改 assertPlanGrantTarget**

在 B2B plan 校验分支（约 line 3073-3080）添加 mode 检查：

```typescript
// B2B enterprise plan check
if (plan.planType === 'b2b_enterprise_plan') {
  if (enterpriseKind !== 'b2b') {
    throw new BadRequestException('B 端企业套餐只能发放给 B 端企业');
  }
  // 新增 mode 检查
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId: dto.enterpriseId },
    select: { mode: true },
  });
  if (config?.mode === 'contact_admin') {
    throw new BadRequestException('当前企业模式下不允许发放套餐');
  }
  if (config?.mode === 'self_purchase') {
    throw new BadRequestException('当前企业模式下不允许发放B端套餐');
  }
  if (dto.subjectType !== 'enterprise' || dto.userId) {
    throw new BadRequestException('B 端企业套餐只能发放给企业主体');
  }
}
```

在 B2B topup 校验分支（约 line 3064-3071）添加同样的 mode 检查。

在 consumer plan 校验分支（约 line 3082-3101），将现有的 `config?.mode !== 'self_purchase'` 拆分为更明确的错误消息：

```typescript
if (['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup'].includes(plan.planType)) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId: dto.enterpriseId },
      select: { mode: true },
    });
    if (config?.mode === 'contact_admin') {
      throw new BadRequestException('当前企业模式下不允许发放套餐');
    }
    if (config?.mode === 'admin_purchase') {
      throw new BadRequestException('当前企业模式下不允许发放C端套餐');
    }
    if (config?.mode !== 'self_purchase') {
      throw new BadRequestException('当前企业未开放成员自行购买权限');
    }
  } else if (!['consumer', 'evomind_consumer'].includes(enterpriseKind)) {
    throw new BadRequestException('C 端套餐只能发放给 C 端企业');
  }
  if (dto.subjectType !== 'enterprise_user' || !dto.userId) {
    throw new BadRequestException('C 端套餐只能发放给企业用户主体');
  }
}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd apps/api && pnpm exec tsx --test src/billing/entitlement.service.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/billing/entitlement.service.ts apps/api/src/billing/entitlement.service.test.ts
git commit -m "feat: enforce strict mode separation in entitlement grant"
```

---

### Task 4: 套餐预览/列表可见性按 mode 过滤

**Files:**
- Modify: `apps/api/src/billing/billing-plan.service.ts:505-538` (assertPreviewAccess)
- Modify: `apps/api/src/billing/billing-plan.service.ts` (listPreview / listAdmin 方法的 where 条件)
- Modify: `apps/api/src/billing/billing-plan.service.test.ts`

**Interfaces:**
- Produces: 不同模式下返回不同的套餐列表

#### Context

`assertPreviewAccess`（line 505-538）控制谁能预览套餐。`listPreview`（line 56-69）和 `listAdmin`（line 46-54）调用 `buildWhere`（line 187-203）构建查询条件。

需要：
1. `contact_admin` → 直接拒绝预览（或返回空列表）
2. `admin_purchase` → 仅 admin/owner 可预览，仅返回 B端套餐
3. `self_purchase` → 所有成员可预览，仅返回 C端套餐

#### Steps

- [ ] **Step 1: 写失败测试**

```typescript
test('listPreview: contact_admin returns empty for b2b enterprise', async () => {
  // B2B enterprise + contact_admin → no plans visible
});

test('listPreview: admin_purchase returns only b2b plans for admin', async () => {
  // B2B enterprise + admin_purchase + admin role → only b2b plans
});

test('listPreview: admin_purchase rejects member access', async () => {
  // B2B enterprise + admin_purchase + member role → ForbiddenException
});

test('listPreview: self_purchase returns only consumer plans', async () => {
  // B2B enterprise + self_purchase → only consumer plans, any member
});
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts --test-name-pattern="listPreview"
```

- [ ] **Step 3: 修改 assertPreviewAccess**

在 `billing-plan.service.ts` line 523-534，将：

```typescript
if (isB2BEnterpriseKind(enterprise.enterpriseKind)) {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId },
    select: { mode: true },
  });
  if (config?.mode === 'self_purchase') {
    return; // Allow all active members to preview
  }
  if (!['owner', 'admin'].includes(membership.role)) {
    throw new ForbiddenException('billing plan preview requires enterprise admin permission');
  }
}
```

改为：

```typescript
if (isB2BEnterpriseKind(enterprise.enterpriseKind)) {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId },
    select: { mode: true },
  });
  const mode = config?.mode ?? 'contact_admin';
  if (mode === 'contact_admin') {
    throw new ForbiddenException('当前企业模式下不可查看计费套餐');
  }
  if (mode === 'admin_purchase' && !['owner', 'admin'].includes(membership.role)) {
    throw new ForbiddenException('billing plan preview requires enterprise admin permission');
  }
  // self_purchase: allow all active members
  // admin_purchase: allow admin/owner only (already checked above)
}
```

- [ ] **Step 4: 修改 listPreview 的 where 条件按 mode 过滤套餐类型**

在 `listPreview` 方法中（line 56-69），在调用 `buildWhere` 之后、执行查询之前，根据 mode 添加 `planType` 过滤：

```typescript
async listPreview(enterpriseId: string, actorUserId: string) {
  await this.assertPreviewAccess(enterpriseId, actorUserId);
  const enterprise = await this.prisma.enterprise.findUnique({
    where: { id: enterpriseId },
    select: { enterpriseKind: true },
  });
  if (!enterprise) throw new NotFoundException('enterprise not found');

  let where = this.buildWhere({ enterpriseId, isActive: true });

  // 按 mode 过滤套餐类型
  if (isB2BEnterpriseKind(enterprise.enterpriseKind)) {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId },
      select: { mode: true },
    });
    const mode = config?.mode ?? 'contact_admin';
    if (mode === 'admin_purchase') {
      where = { ...where, planType: { in: [...B2B_PLAN_TYPES] as any } };
    } else if (mode === 'self_purchase') {
      where = { ...where, planType: { in: [...CONSUMER_PLAN_TYPES] as any } };
    }
  }

  const plans = await this.prisma.billingPlan.findMany({
    where,
    include: { enterprise: { select: { id: true, name: true, slug: true, enterpriseKind: true, status: true } } },
  });
  return plans.filter(p => !p.isDeleted).map(p => this.toPreviewResponse(p));
}
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/billing/billing-plan.service.ts apps/api/src/billing/billing-plan.service.test.ts
git commit -m "feat: filter plan visibility by purchase mode"
```

---

### Task 5: 前端 B端企业套餐管理页面按 mode 展示

**Files:**
- Modify: B端企业套餐/配额相关前端页面（需确认具体文件路径）

**Interfaces:**
- Consumes: `EnterprisePostExpiryPurchaseConfig.mode` from API
- Produces: 按 mode 展示不同的套餐购买 UI

#### Context

前端需要：
1. 获取当前企业的 `EnterprisePostExpiryPurchaseConfig.mode`
2. 根据 mode 展示不同的 UI：
   - `contact_admin` → 不展示计费套餐购买入口
   - `admin_purchase` → 展示B端套餐列表 + 购买按钮（仅 admin）
   - `self_purchase` → 展示C端套餐列表 + 购买按钮（所有人）

#### Steps

- [ ] **Step 1: 确认前端文件位置**

需要先确定前端哪个页面负责B端企业的套餐购买展示。可能的候选：
- `apps/web/src/app/[locale]/(zclaw-shell)/admin/billing-plans/page.tsx` — 平台admin管理所有套餐
- `apps/web/src/app/[locale]/(zclaw-shell)/enterprise/` 下的某个页面 — 企业级视图
- `apps/web/src/app/[locale]/(zclaw-shell)/admin/conversation-quota/page.tsx` — 配额管理

需要搜索前端代码中使用 `listPreview` 或 `billing-plan` API 的位置。

- [ ] **Step 2: 实现前端 mode 过滤逻辑**

根据 Step 1 确定的文件，添加 mode 判断和 UI 条件渲染。

- [ ] **Step 3: 运行 lint 确认通过**

```bash
cd apps/web && pnpm lint
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/...
git commit -m "feat: filter billing plan UI by purchase mode"
```

---

### Task 6: 全局验证

**Files:** 无新建，验证所有改动

#### Steps

- [ ] **Step 1: 运行全部 API 测试**

```bash
cd apps/api && pnpm exec tsx --test src/billing/billing-plan.service.test.ts src/billing/billing-order.service.test.ts src/billing/entitlement.service.test.ts
```
Expected: 所有测试 PASS

- [ ] **Step 2: 运行 lint**

```bash
pnpm lint
```
Expected: 无错误

- [ ] **Step 3: 验证构建**

```bash
pnpm build
```
Expected: 构建成功

- [ ] **Step 4: 手动验证场景矩阵**

| 场景 | 期望结果 |
|---|---|
| 平台admin为B端企业创建C端套餐 | ✅ 成功 |
| B端企业 self_purchase + 成员买C端套餐 | ✅ 成功 |
| B端企业 self_purchase + 成员买B端套餐 | ❌ ForbiddenException |
| B端企业 self_purchase + admin买C端套餐 | ✅ 成功（个人自购） |
| B端企业 self_purchase + admin买B端套餐 | ❌ ForbiddenException |
| B端企业 admin_purchase + admin买B端套餐 | ✅ 成功 |
| B端企业 admin_purchase + admin买C端套餐 | ❌ ForbiddenException |
| B端企业 admin_purchase + 成员买任何套餐 | ❌ ForbiddenException |
| B端企业 contact_admin + 任何人买任何套餐 | ❌ ForbiddenException |
| C端企业不受上述逻辑影响 | ✅ 维持现有行为 |
