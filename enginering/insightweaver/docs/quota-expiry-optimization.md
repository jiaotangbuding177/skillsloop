# B端企业配额到期优化 - 技术实现文档

> **分支**: `feat/quota-expiry-ui-optimization`
> **基于**: `main`
> **总提交数**: 50+ commits

## 目录

- [1. 概述](#1-概述)
- [2. 双模型月包系统](#2-双模型月包系统)
- [3. 批次到期后购买引导配置](#3-批次到期后购买引导配置)
- [4. 池模型配额管理](#4-池模型配额管理)
- [5. 批次生命周期管理（回收/冻结/解冻）](#5-批次生命周期管理回收冻结解冻)
- [6. 消费优先级系统](#6-消费优先级系统)
- [7. 前端UI改动](#7-前端ui改动)
- [8. 已知问题与限制](#8-已知问题与限制)

---

## 1. 概述

本次优化为 B 端企业引入了一套完整的配额管理体系，核心目标：

1. **双模型月包系统** — 支持旧模型（自动分发）和新池模型（手动分配）共存
2. **到期后购买引导** — 管理员可配置批次到期后成员的行为：联系管理员 / 管理员分配 / 自行购买
3. **批次生命周期管理** — 支持回收未生效批次、冻结/解冻已生效批次
4. **消费优先级** — 池分配配额优先级低于普通月包，支持排队生效

---

## 2. 双模型月包系统

### 2.1 旧模型：`b2b_enterprise_plan`

**特点**：购买后立即自动分配给所有成员。

**数据结构**：
```
anchor 批次 (subjectType: enterprise)
  ├── grantedAmount = 1n (代表 1 个计划周期)
  ├── remainingAmount = 1n
  └── metadata: { b2bMonthly: true }

成员 token/storage 批次 (subjectType: enterprise_user)
  ├── grantedAmount = plan.tokenAmount
  ├── validFrom = period.validFrom
  ├── validUntil = period.validUntil
  └── metadata: { b2bMonthlyAnchorBatchId, b2bMonthly: true }
```

**适用场景**：成员稳定、需要自动分配的企业。

### 2.2 新模型：`b2b_monthly_seat_plan`

**特点**：购买后创建席位池，管理员手动分配。

**数据结构**：
```
anchor 批次 (subjectType: enterprise)
  ├── grantedAmount = memberLimit (席位数)
  ├── remainingAmount = memberLimit
  └── metadata: { poolModel: true, b2bMonthly: true }

token pool 批次 (subjectType: enterprise)
  ├── grantedAmount = memberLimit × tokenAmount
  ├── remainingAmount = 初始等于 granted
  ├── sourceRefId = anchor.id
  └── metadata: { poolModel: true, anchorBatchId }

storage pool 批次 (subjectType: enterprise)
  ├── 同 token pool 结构
  └── metadata: { poolModel: true, anchorBatchId }

分配的成员批次 (subjectType: enterprise_user)
  ├── grantedAmount = tokenPerSeat / storagePerSeat
  ├── sourceRefId = poolBatch.id
  └── metadata: { poolModel: true, anchorBatchId, poolBatchId }
```

**适用场景**：需要精细控制、成员变动频繁、需要席位复用的企业。

### 2.3 模型选择

在 `/admin/billing-plans` 页面创建套餐时选择：
- **席位月包** → `b2b_enterprise_plan`（旧模型，memberLimit 自动填入当前成员数）
- **席位月包（池分配）** → `b2b_monthly_seat_plan`（新模型，memberLimit 手动输入）

---

## 3. 批次到期后购买引导配置

### 3.1 数据模型

**表**: `EnterprisePostExpiryPurchaseConfig`

| 字段 | 类型 | 说明 |
|------|------|------|
| enterpriseId | String (unique) | 企业 ID |
| mode | String | 模式：`contact_admin` / `admin_purchase` / `self_purchase` |
| enabledBy | String? | 操作人 |
| enabledAt | DateTime? | 启用时间 |

### 3.2 三种模式

| 模式 | 说明 | 前端行为 |
|------|------|----------|
| `contact_admin`（默认） | 联系管理员 | 不显示购买按钮，提示"请联系管理员" |
| `admin_purchase` | 管理员分配 | 管理员看到 B 端套餐购买入口 |
| `self_purchase` | 自行购买 | 成员看到 C 端套餐购买入口 |

### 3.3 五道消费闸门

所有闸门根据 `postExpiryPurchaseMode` 控制：

| 闸门 | 文件 | 控制内容 |
|------|------|----------|
| 1. 套餐列表过滤 | `BillingPurchaseDialog.tsx` | `allowedPlanTypes` 按模式过滤 |
| 2. 套餐预览权限 | `billing-plan.service.ts` | `assertPreviewAccess` 校验 |
| 3. 下单校验 | `billing-order.service.ts` | `createOrder` 校验 |
| 4. 套餐发放校验 | `billing-plan.service.ts` | `validatePlanConfig` 校验 |
| 5. 权益发放校验 | `entitlement.service.ts` | `assertPlanGrantTarget` 校验 |

**闸门逻辑**：
- `contact_admin` → 所有闸门关闭
- `admin_purchase` → 仅 B 端套餐通过（闸门 1 过滤 C 端套餐）
- `self_purchase` → 仅 C 端套餐通过（闸门 1-4 过滤 B 端套餐，闸门 5 允许 C 端绑定 B 端企业）

### 3.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/billing/post-expiry-purchase-config/:enterpriseId` | 获取配置 |
| PUT | `/api/admin/billing/post-expiry-purchase-config/:enterpriseId` | 更新配置（仅 owner） |

---

## 4. 池模型配额管理

### 4.1 席位分配

**API**: `POST /api/admin/billing/monthly-seats/:anchorBatchId/allocate`

**参数**：
```json
{
  "enterpriseId": "...",
  "userId": "..."
}
```

**逻辑**：
1. 校验席位上限：`allocatedUserIds.size >= memberLimit` 则拒绝
2. 允许同一成员多次分配（支持席位复用）
3. 检查排队位置：找到用户所有月包相关 token 批次的最晚 `validUntil`
4. 新批次从该时间点开始生效（排队）
5. 执行 freeze-capture 循环：
   - freeze pool 批次
   - create member 批次
   - capture pool 批次
6. 写入 ledger 记录

**排队计算纳入的批次类型**：
- `b2b_monthly_seat_plan` — 池分配月包
- `b2b_enterprise_plan` — 旧模型自动分配
- `consumer_monthly_plan` — C 端月包（B 端企业开放自购时）

**排除的批次类型**：
- `b2b_token_topup` — B 端补充包
- `consumer_token_topup` — C 端补充包
- `admin_grant` — 管理员赠送

### 4.2 池列表查询

**API**: `GET /api/admin/billing/monthly-seats/pools?enterpriseId=...`

**返回**：
```json
{
  "items": [
    {
      "anchorBatchId": "...",
      "planName": "...",
      "tokenPoolRemaining": "...",
      "tokenPoolGranted": "...",
      "storagePoolRemaining": "...",
      "storagePoolGranted": "...",
      "memberLimit": 10,
      "allocatedSeats": 3,
      "validFrom": "...",
      "validUntil": "...",
      "status": "active"
    }
  ]
}
```

---

## 5. 批次生命周期管理（回收/冻结/解冻）

### 5.1 状态机

```
                  void (回收)
scheduled ──────────────────────→ voided

                  freeze (冻结)
active ─────────────────────────→ frozen
                  unfreeze (解冻)
frozen ─────────────────────────→ active

                  auto-expire (自动过期)
frozen ─────────────────────────→ expired
```

### 5.2 回收（Void）

**API**: `POST /api/admin/billing/entitlements/void-batch`

**条件**：批次 `status === 'scheduled'` 且 `metadata.poolModel === true`

**逻辑**：
1. 将批次 `status` 改为 `voided`
2. 找到关联的 pool 批次（通过 `metadata.poolBatchId`）
3. 增加 pool 的 `remainingAmount`（退回额度）
4. 写入 ledger：`changeType: 'void'`

### 5.3 冻结（Freeze）

**API**: `POST /api/admin/billing/entitlements/freeze-batch`

**条件**：批次 `status === 'active'` 且 `metadata.poolModel === true`

**逻辑**：
1. 将批次 `status` 改为 `frozen`
2. 写入 ledger：`changeType: 'freeze'`
3. 冻结的批次不参与消费（`effectiveStatus` 返回 `'frozen'`）

### 5.4 解冻（Unfreeze）

**API**: `POST /api/admin/billing/entitlements/unfreeze-batch`

**条件**：批次 `status === 'frozen'` 且 `metadata.poolModel === true`

**逻辑**：
1. 检查 `validUntil`：如果已过期则拒绝解冻
2. 将批次 `status` 改为 `active`
3. 写入 ledger：`changeType: 'unfreeze'`

### 5.5 自动过期

`entitlement-expiry.scheduler.ts` 已更新，查询条件包含 `frozen` 状态：
```typescript
status: { in: ['active', 'scheduled', 'paused', 'frozen'] }
```

冻结的批次到期后自动变为 `expired`。

---

## 6. 消费优先级系统

### 6.1 优先级定义

```typescript
consumptionPriority(batch, enterpriseKind):
  - 0: 月包 (b2b_enterprise_plan, consumer_monthly_plan)
  - 1: 池分配月包 (b2b_monthly_seat_plan + poolModel)
  - 2: 补充包 (b2b_token_topup, consumer_token_topup, ...)
  - 3: 管理员赠送 (admin_grant)
  - 4: 其他
```

**数字越小优先级越高**，先消费。

### 6.2 排队生效

当用户有多个同优先级批次时，按 `validUntil` 升序消费（先到期的先消费）。

**池分配排队逻辑**：新分配的池批次从已有月包批次的最晚 `validUntil` 开始生效，实现"排队"效果。

### 6.3 effectiveStatus

```typescript
effectiveStatus(batch, now):
  - voided → 'voided'
  - expired → 'expired'
  - frozen → 'frozen'
  - validUntil <= now → 'expired'
  - validFrom > now → 'scheduled'
  - 否则 → 'active'
```

---

## 7. 前端UI改动

### 7.1 配额配置页面

**路径**: `/admin/conversation-quota`

新增"批次到期后行为"配置卡片，仅在配额模式为"按批次"时显示：

```
┌─────────────────────────────────────────┐
│ 批次到期后行为                            │
│                                         │
│ ○ 联系管理员（默认）                      │
│   成员到期后提示联系管理员                 │
│                                         │
│ ○ 管理员分配                              │
│   管理员购买 B 端套餐分配给成员            │
│                                         │
│ ○ 自行购买                                │
│   成员可自行购买 C 端套餐                  │
└─────────────────────────────────────────┘
```

### 7.2 权益批次管理页面

**路径**: `/admin/entitlement-batches`

新增操作按钮列：

| 状态 | 按钮 | 颜色 |
|------|------|------|
| scheduled | 回收 | 橙色 |
| active | 冻结 | 蓝色 |
| frozen | 解冻 | 绿色 |

每个操作都有确认对话框和 toast 通知。

新增 `frozen` 状态标签，橙色样式。

### 7.3 补充包分配页面

**路径**: `/admin/topup-inventories`

新增"月包席位"tab，显示池列表和分配表单：

- **池列表**：表格显示所有池的剩余/总额度、已分配/总席位、有效期、到期提醒
- **分配表单**：选择池 → 选择成员 → 提交分配

**到期提醒**：
- ≤ 30 天：红色
- ≤ 90 天：橙色
- ≤ 180 天：黄色

### 7.4 购买对话框

**组件**: `BillingPurchaseDialog`

根据 `postExpiryPurchaseMode` 过滤套餐列表：
- `admin_purchase` → 显示 B 端套餐（排除 `b2b_enterprise_plan`）
- `self_purchase` → 显示 C 端套餐

---

## 8. 已知问题与限制

### 8.1 既有测试失败

`entitlement-consumption.service.test.ts` 中有一个既有失败：
```
freezeEntitlements consumes monthly, purchased topup, then admin gift when monthly is active
```

原因：测试数据中 `adminGiftTopup.validUntil: 2026-07-10` 已过期（当前 2026-07-14），被 `effectiveStatus` 过滤。这不是本次改动引入的。

### 8.2 旧数据兼容

修复前创建的 anchor 批次 `grantedAmount = 1n`，但新代码期望 `grantedAmount = memberLimit`。旧数据不受影响（席位计数基于 allocated user count 而非 anchor remainingAmount）。

### 8.3 Trellis 文件

提交中包含了 `.trellis/` 目录文件（任务管理工具），这些文件不影响功能。

---

## 附录：关键文件索引

| 文件 | 说明 |
|------|------|
| `apps/api/src/billing/entitlement.service.ts` | 核心权益服务：分配、回收、冻结、解冻、消费 |
| `apps/api/src/billing/entitlement.controller.ts` | API 端点 |
| `apps/api/src/billing/billing-plan.service.ts` | 套餐管理：创建、校验、预览 |
| `apps/api/src/billing/billing-order.service.ts` | 下单逻辑 |
| `apps/api/src/billing/entitlement-expiry.scheduler.ts` | 自动过期调度器 |
| `apps/api/src/billing/dto/entitlement.dto.ts` | DTO 定义 |
| `apps/web/src/app/[locale]/(zclaw-shell)/admin/entitlement-batches/page.tsx` | 权益批次管理页面 |
| `apps/web/src/app/[locale]/(zclaw-shell)/admin/topup-inventories/page.tsx` | 补充包/席位分配页面 |
| `apps/web/src/app/[locale]/(zclaw-shell)/admin/conversation-quota/page.tsx` | 配额配置页面 |
| `apps/web/src/components/zclaw/BillingPurchaseDialog.tsx` | 购买对话框 |
| `apps/web/src/api/moudles/billing.ts` | 前端 API 函数 |
| `packages/db/prisma/schema.prisma` | 数据库模型 |
