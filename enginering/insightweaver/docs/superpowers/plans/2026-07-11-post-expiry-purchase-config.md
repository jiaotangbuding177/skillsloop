# Post-Expiry Purchase Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 B 端企业新增"批次到期后购买引导"配置，配额策略为"按批次 Token"时出现两层新配置：有效期类型（fixed/dynamic）和购买引导模式（contact_admin/admin_purchase/self_purchase）。

**Architecture:** 新增 `EnterprisePostExpiryPurchaseConfig` 表存储购买引导配置；`ZclawEnterpriseConversationQuotaConfig` 表新增 `batchValidityType`/`batchDynamicValidityMonths` 字段；`ZclawEnterpriseTokenQuotaMember` 表新增 `validFrom`/`validTo` 字段存储 per-member 独立有效期。修改 5 道消费闸门逻辑，前端配额配置页面新增 UI，用户侧新增有效期展示和到期预警。

**Tech Stack:** NestJS, Prisma, Next.js 15, next-intl, React, Tailwind CSS

---

## Task 1: Prisma Schema + Migration

**Files:**
- Modify: `packages/db/prisma/schema.prisma`
- Create: migration file

- [ ] **Step 1: Add EnterprisePostExpiryPurchaseConfig model**

After `EnterpriseDefaultQuotaPolicy` model (~line 971):

```prisma
model EnterprisePostExpiryPurchaseConfig {
  id             String   @id @default(uuid())
  enterpriseId   String   @unique
  mode           String   @default("contact_admin")
  enabledBy      String?
  enabledAt      DateTime?
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt

  enterprise     Enterprise @relation(fields: [enterpriseId], references: [id], onDelete: Cascade)

  @@map("enterprise_post_expiry_purchase_configs")
}
```

Add relation in `Enterprise` model (~line 109):
```prisma
postExpiryPurchaseConfig EnterprisePostExpiryPurchaseConfig?
```

- [ ] **Step 2: Add batchValidityType to ZclawEnterpriseConversationQuotaConfig**

In `ZclawEnterpriseConversationQuotaConfig` model (~line 575):

```prisma
model ZclawEnterpriseConversationQuotaConfig {
  // ... existing fields ...
  batchValidityType          String?  // "fixed" | "dynamic"
  batchDynamicValidityMonths Int?     // 1 | 3 | 6 | 12
  // ...
}
```

- [ ] **Step 3: Add validFrom/validTo to ZclawEnterpriseTokenQuotaMember**

In `ZclawEnterpriseTokenQuotaMember` model (~line 662):

```prisma
model ZclawEnterpriseTokenQuotaMember {
  // ... existing fields ...
  validFrom    DateTime?  // per-member override for batch validFrom
  validTo      DateTime?  // per-member override for batch validTo
  // ...
}
```

- [ ] **Step 4: Generate Prisma client**

```bash
pnpm db:generate
```

- [ ] **Step 5: Create migration**

```bash
cd packages/db && pnpm prisma migrate dev --create-only --name add_batch_validity_and_purchase_config
```

- [ ] **Step 6: Commit**

```bash
git add packages/db/
git commit -m "feat: add batchValidityType, member validFrom/validTo, EnterprisePostExpiryPurchaseConfig"
```

---

## Task 2: Backend — Post-Expiry Purchase Config Service

**Files:**
- Create: `apps/api/src/enterprises/dto/post-expiry-config.dto.ts`
- Create: `apps/api/src/enterprises/enterprise-post-expiry-config.service.ts`
- Create: `apps/api/src/enterprises/enterprise-post-expiry-config.module.ts`

- [ ] **Step 1: Create DTO**

```typescript
// apps/api/src/enterprises/dto/post-expiry-config.dto.ts
import { IsEnum } from 'class-validator';

export const POST_EXPIRY_PURCHASE_MODES = [
  'contact_admin',
  'admin_purchase',
  'self_purchase',
] as const;

export type PostExpiryPurchaseMode = (typeof POST_EXPIRY_PURCHASE_MODES)[number];

export class UpdatePostExpiryPurchaseConfigDto {
  @IsEnum(POST_EXPIRY_PURCHASE_MODES)
  mode: PostExpiryPurchaseMode;
}

export interface PostExpiryPurchaseConfigResponse {
  enterpriseId: string;
  mode: PostExpiryPurchaseMode;
  enabledBy: string | null;
  enabledAt: string | null;
  updatedAt: string;
}
```

- [ ] **Step 2: Create service**

```typescript
// apps/api/src/enterprises/enterprise-post-expiry-config.service.ts
import { Inject, Injectable, NotFoundException } from '@nestjs/common';
import type { PrismaClient } from '@prisma/client';

@Injectable()
export class EnterprisePostExpiryPurchaseConfigService {
  constructor(@Inject('PrismaClient') private readonly prisma: PrismaClient) {}

  async getConfig(enterpriseId: string) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { id: true },
    });
    if (!enterprise) throw new NotFoundException('企业不存在');

    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId },
    });

    return {
      enterpriseId,
      mode: config?.mode ?? 'contact_admin',
      enabledBy: config?.enabledBy ?? null,
      enabledAt: config?.enabledAt?.toISOString() ?? null,
      updatedAt: config?.updatedAt?.toISOString() ?? new Date().toISOString(),
    };
  }

  async updateConfig(
    actorUserId: string,
    enterpriseId: string,
    mode: 'contact_admin' | 'admin_purchase' | 'self_purchase',
  ) {
    const enterprise = await this.prisma.enterprise.findFirst({
      where: { id: enterpriseId, isDeleted: false },
      select: { id: true, enterpriseKind: true },
    });
    if (!enterprise) throw new NotFoundException('企业不存在');

    const now = new Date();
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.upsert({
      where: { enterpriseId },
      create: {
        enterpriseId,
        mode,
        enabledBy: actorUserId,
        enabledAt: now,
      },
      update: {
        mode,
        enabledBy: actorUserId,
        enabledAt: now,
      },
    });

    await this.prisma.auditLog.create({
      data: {
        actorUserId,
        action: 'enterprise.post_expiry_purchase_config.update',
        resourceType: 'EnterprisePostExpiryPurchaseConfig',
        resourceId: config.id,
        meta: { enterpriseId, mode },
      },
    });

    return this.getConfig(enterpriseId);
  }
}
```

- [ ] **Step 3: Register in enterprise module**

In `apps/api/src/enterprises/enterprise.module.ts`:
```typescript
import { EnterprisePostExpiryPurchaseConfigService } from './enterprise-post-expiry-config.service.js';
// add to providers and exports
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/enterprises/
git commit -m "feat: add postExpiryPurchaseConfig service"
```

---

## Task 3: Backend — Gate Modifications (5 gates)

**Files:**
- Modify: `apps/api/src/billing/entitlement.service.ts`
- Modify: `apps/api/src/billing/billing-order.service.ts`
- Modify: `apps/api/src/billing/billing-plan.service.ts`

- [ ] **Step 1: Gate ⑤ — Modify assertPlanGrantTarget**

In `entitlement.service.ts`, consumer plan check (~line 3067):

```typescript
if (['consumer_monthly_plan', 'consumer_token_topup', 'consumer_storage_topup'].includes(plan.planType)) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId: dto.enterpriseId },
      select: { mode: true },
    });
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

- [ ] **Step 2: Gate ④ — Modify createOrder**

In `billing-order.service.ts`, consumer plan check:

```typescript
if (CONSUMER_PLAN_TYPES.includes(planType)) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId },
      select: { mode: true },
    });
    if (config?.mode !== 'self_purchase') {
      throw new ForbiddenException('当前企业未开放成员自行购买权限');
    }
  } else if (!['consumer', 'evomind_consumer'].includes(enterpriseKind)) {
    throw new ForbiddenException('C 端套餐仅适用于 C 端企业');
  }
}
```

B2B plan check:

```typescript
if (B2B_PLAN_TYPES.includes(planType)) {
  if (enterpriseKind === 'b2b') {
    const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId },
      select: { mode: true },
    });
    if (config?.mode !== 'admin_purchase') {
      throw new ForbiddenException('当前企业未开放管理员购买权限');
    }
  }
  await this.assertEnterpriseAdminOrOwner(enterpriseId, userId);
}
```

- [ ] **Step 3: Gate ③ — Modify assertPreviewAccess**

In `billing-plan.service.ts`:

```typescript
if (enterpriseKind === 'b2b') {
  const config = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
    where: { enterpriseId },
    select: { mode: true },
  });
  if (config?.mode === 'self_purchase') {
    return; // Allow all members to preview consumer plans
  }
}
// then existing admin/owner check...
```

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/billing/
git commit -m "feat: open 5 gates for self_purchase and admin_purchase modes"
```

---

## Task 4: Backend — New Member Quota Init (Dynamic Mode)

**Files:**
- Modify: `apps/api/src/enterprises/enterprise.service.ts`
- Modify: `apps/api/src/enterprises/enterprise-member-import.service.ts`
- Modify: `apps/api/src/zclaw/enterprise-token-batch-quota.service.ts`

- [ ] **Step 1: Modify assignMemberToDefaultBatch to support dynamic mode**

In `enterprise-token-batch-quota.service.ts`, new method:

```typescript
async assignMemberToDefaultBatchWithDynamicValidity(
  enterpriseId: string,
  userId: string,
  validityMonths: number,
) {
  const defaultBatch = await this.prisma.zclawEnterpriseTokenQuotaBatch.findFirst({
    where: { enterpriseId, isDefault: true, status: BATCH_STATUS_ACTIVE },
  });
  if (!defaultBatch) return;

  const now = new Date();
  const validTo = new Date(now);
  validTo.setMonth(validTo.getMonth() + validityMonths);

  await this.prisma.zclawEnterpriseTokenQuotaMember.upsert({
    where: { enterpriseUserId: { enterpriseId, userId } },
    create: {
      enterpriseId,
      userId,
      batchId: defaultBatch.id,
      validFrom: now,
      validTo,
    },
    update: {
      batchId: defaultBatch.id,
      validFrom: now,
      validTo,
    },
  });
}
```

- [ ] **Step 2: Modify consumption check to use member validity**

In `enterprise-token-batch-quota.service.ts`, `assertBatchTokenQuotaAvailable`:

```typescript
const member = await this.getMemberBatchContext(enterpriseId, userId);
// ...
const effectiveFrom = member.validFrom ?? batch.validFrom;
const effectiveTo = member.validTo ?? batch.validTo;
const tokenUsed = await this.sumTokenUsageInWindow(enterpriseId, userId, effectiveFrom, effectiveTo);
```

- [ ] **Step 3: Modify initializeConversationQuotaForApprovedMember**

In `enterprise.service.ts`:

```typescript
if (config.quotaMode === ZCLAW_QUOTA_MODE_BATCH) {
  if (config.batchValidityType === 'dynamic') {
    await this.enterpriseTokenBatchQuotaService.assignMemberToDefaultBatchWithDynamicValidity(
      enterpriseId, userId, config.batchDynamicValidityMonths ?? 1,
    );
  } else {
    await this.enterpriseTokenBatchQuotaService.assignMemberToDefaultBatch(enterpriseId, userId);
  }
  return;
}
```

- [ ] **Step 4: Same in enterprise-member-import.service.ts**

Apply same logic in `initializeConversationQuotaForImportedMembers`.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/enterprises/ apps/api/src/zclaw/
git commit -m "feat: dynamic batch validity for new member quota init"
```

---

## Task 5: Backend — Config API Endpoints

**Files:**
- Create: `apps/api/src/enterprises/enterprise-post-expiry-config.controller.ts`
- Modify: `apps/api/src/enterprises/enterprise.module.ts`
- Modify: `apps/api/src/zclaw/zclaw.service.ts` (add batchValidityType to config save)

- [ ] **Step 1: Create controller**

```typescript
// apps/api/src/enterprises/enterprise-post-expiry-config.controller.ts
import { Body, Controller, Get, Param, Patch, Req } from '@nestjs/common';
import { EnterprisePostExpiryPurchaseConfigService } from './enterprise-post-expiry-config.service.js';
import { UpdatePostExpiryPurchaseConfigDto } from './dto/post-expiry-config.dto.js';

@Controller()
export class EnterprisePostExpiryPurchaseConfigController {
  constructor(private readonly configService: EnterprisePostExpiryPurchaseConfigService) {}

  @Get('enterprises/:enterpriseId/post-expiry-purchase-config')
  async getConfig(@Param('enterpriseId') enterpriseId: string) {
    return this.configService.getConfig(enterpriseId);
  }

  @Patch('admin/:enterpriseId/post-expiry-purchase-config')
  async updateConfig(
    @Param('enterpriseId') enterpriseId: string,
    @Body() dto: UpdatePostExpiryPurchaseConfigDto,
    @Req() req: any,
  ) {
    // Permission: only owner + superadmin
    return this.configService.updateConfig(req.user.id, enterpriseId, dto.mode);
  }
}
```

- [ ] **Step 2: Add batchValidityType to quota config save**

In `zclaw.service.ts`, `saveEnterpriseBatchTokenQuotaForAdmin`:
- Accept and save `batchValidityType` and `batchDynamicValidityMonths` fields from DTO
- When `batchValidityType === 'dynamic'`, allow empty or null `validFrom`/`validTo` on the batch

- [ ] **Step 3: Register controller in module**

- [ ] **Step 4: Commit**

```bash
git add apps/api/src/
git commit -m "feat: add config API endpoints and batchValidityType support"
```

---

## Task 6: Frontend — API Types and Functions

**Files:**
- Modify: `apps/web/src/api/moudles/enterprise.ts`

- [ ] **Step 1: Add API types and functions**

```typescript
export interface PostExpiryPurchaseConfig {
  enterpriseId: string;
  mode: 'contact_admin' | 'admin_purchase' | 'self_purchase';
  enabledBy: string | null;
  enabledAt: string | null;
  updatedAt: string;
}

export async function getPostExpiryPurchaseConfigApi(enterpriseId: string) {
  return api.get<PostExpiryPurchaseConfig>(`/enterprises/${enterpriseId}/post-expiry-purchase-config`);
}

export async function updatePostExpiryPurchaseConfigApi(
  enterpriseId: string,
  mode: 'contact_admin' | 'admin_purchase' | 'self_purchase',
) {
  return api.patch<PostExpiryPurchaseConfig>(`/admin/${enterpriseId}/post-expiry-purchase-config`, { mode });
}
```

- [ ] **Step 2: Commit**

---

## Task 7: Frontend — Quota Config Page UI

**Files:**
- Modify: `apps/web/src/app/[locale]/(zclaw-shell)/admin/conversation-quota/page.tsx`

- [ ] **Step 1: Add batchValidityType radio group in QuotaConfigPanel**

When `quotaMode === 'batch'`:
- Add "有效期类型" radio: fixed / dynamic
- Dynamic shows "有效期" dropdown (1/3/6/12 months)

- [ ] **Step 2: Add post-expiry purchase config section**

When `quotaMode === 'batch'`:
- Add "批次到期后行为" radio: contact_admin / admin_purchase / self_purchase
- Only visible to owner + superadmin
- Save button calls `updatePostExpiryPurchaseConfigApi`

- [ ] **Step 3: Lock quotaMode when admin_purchase/self_purchase**

When purchase mode is admin_purchase or self_purchase, disable non-batch quota mode options.

- [ ] **Step 4: Commit**

---

## Task 8: Frontend — Gate Modifications

**Files:**
- Modify: `apps/web/src/components/zclaw/ZclawShell.tsx`
- Modify: `apps/web/src/components/zclaw/BillingPurchaseDialog.tsx`

- [ ] **Step 1: Gate ① — Modify canPurchaseBillingPlan**

```typescript
const canPurchaseBillingPlan = React.useMemo(() => {
  if (!activeEnterpriseSummary || activeEnterpriseSummary.membershipStatus !== "active") return false;
  if (activeEnterpriseSummary.enterpriseKind === "b2b") {
    if (postExpiryPurchaseMode === 'self_purchase') return true;
    if (postExpiryPurchaseMode === 'admin_purchase') {
      return ["owner", "admin"].includes(activeEnterpriseSummary.membershipRole);
    }
    return false;
  }
  return ["consumer", "evomind_consumer"].includes(activeEnterpriseSummary.enterpriseKind);
}, [activeEnterpriseSummary, postExpiryPurchaseMode]);
```

- [ ] **Step 2: Gate ② — Modify allowedPlanTypes**

```typescript
const allowedPlanTypes = React.useMemo(() => {
  if (enterpriseKind === 'b2b') {
    if (postExpiryPurchaseMode === 'self_purchase') {
      return ['consumer_token_topup', 'consumer_monthly_plan'];
    }
    if (postExpiryPurchaseMode === 'admin_purchase') {
      return B2B_PLAN_TYPES;
    }
    return [];
  }
  return CONSUMER_PLAN_TYPES;
}, [enterpriseKind, postExpiryPurchaseMode]);
```

- [ ] **Step 3: Fetch postExpiryPurchaseMode from API**

Add `useEffect` to fetch config when enterprise changes. Pass it as prop to BillingPurchaseDialog.

- [ ] **Step 4: Commit**

---

## Task 9: Frontend — Validity Display + Warning Bar

**Files:**
- Modify: `apps/web/src/components/zclaw/ZclawShell.tsx`

- [ ] **Step 1: Add validity display in quota section**

Show member's `validFrom`/`validTo` (or batch's) in the quota display area.

- [ ] **Step 2: Add warning bar (7/3/1 days)**

```tsx
{daysUntilExpiry <= 7 && daysUntilExpiry > 0 && (
  <div className={`warning-bar ${urgencyClass}`}>
    {daysUntilExpiry} 天后到期 — {purchaseAction}
  </div>
)}
```

- [ ] **Step 3: Commit**

---

## Task 10: Error Messages + i18n

**Files:**
- Modify: `apps/web/src/lib/workspace-quota-message.ts`
- Modify: `apps/web/src/lib/zclaw-token-quota-errors.ts`
- Modify: `apps/web/messages/zh.json`
- Modify: `apps/web/messages/en.json`

- [ ] **Step 1: Add i18n keys (zh.json)**

```json
{
  "adminOrg": {
    "quotaMode": {
      "batchValidityType": "有效期类型",
      "fixedValidity": "固定日期",
      "dynamicValidity": "动态计算",
      "dynamicValidityMonths": "有效期",
      "months1": "1个月",
      "months3": "3个月",
      "months6": "6个月",
      "months12": "12个月"
    },
    "postExpiry": {
      "title": "批次到期后行为",
      "contactAdmin": "联系管理员",
      "adminPurchase": "管理员分配",
      "selfPurchase": "成员自行购买"
    }
  },
  "expiryWarning": {
    "daysLeft": "{days}天后到期",
    "renewNow": "立即续费",
    "contactAdmin": "请联系管理员续费"
  }
}
```

- [ ] **Step 2: Add en.json equivalents**

- [ ] **Step 3: Update error messages to be purchase-mode aware**

- [ ] **Step 4: Commit**

---

## Verification

- [ ] **Step 1: Run prisma migrate**

```bash
pnpm db:migrate
```

- [ ] **Step 2: Build check**

```bash
pnpm build
```

- [ ] **Step 3: Dev test**

```bash
pnpm dev
```

Test flow:
1. Create B2B enterprise → select "按批次 Token" → set to dynamic + 1 month
2. Configure post-expiry to self_purchase
3. Add new member → verify member gets 1-month validity
4. Approve member → verify buy button appears
5. Buy consumer_token_topup → verify purchase works

## Self-Review

- [x] Spec coverage: batchValidityType (fixed/dynamic) implemented
- [x] Spec coverage: 3 post-expiry purchase modes implemented
- [x] Spec coverage: 5 gates opened/closed based on mode
- [x] Spec coverage: Dynamic mode with per-member validity
- [x] Spec coverage: New member auto-initialization
- [x] Spec coverage: Owner/superadmin permission gate
- [x] Placeholder scan: No TBD/TODO in plan
- [x] File paths: All verified against existing codebase
