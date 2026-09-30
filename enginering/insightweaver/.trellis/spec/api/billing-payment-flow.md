# Billing Payment Flow

C 端（消费者）支付订单 → 权益发放的完整链路规格。覆盖微信支付回调、订单状态机、权益批次拆分、生效时间对齐、数据关联约定。

---

## 1. Scope / Trigger

**Trigger**：任何涉及以下领域的改动都需要 code-spec 深度：
- 微信支付回调解析 / 订单创建 / 发放流程
- `billing_orders` / `entitlement_batches` 表 schema 变更
- 套餐类型（`planType`）新增或拆分规则变更
- 生效时间（`validFrom`/`validUntil`）计算逻辑

**Why**：涉及资金流 + 权益发放，错误会导致：少发/多发权益、发放失败无法恢复、对账失败、时区偏差导致有效期偏移 8h。

---

## 2. Signatures

### 核心函数签名

```typescript
// apps/api/src/billing/billing-order.service.ts
async fulfillPaidOrder(order: BillingOrder, actorUserId: string | null): Promise<{
  order: BillingOrder;
  grant: { idempotent: boolean; batches: BatchResponse[]; inventories: InventoryResponse[] };
}>

// apps/api/src/billing/entitlement.service.ts
async grantPaidOrderSnapshot(
  actorUserId: string | null,
  order: BillingOrder,
  idempotencyKey?: string  // 默认 `billing_order:${order.id}:grant`
): Promise<{ idempotent: boolean; batches: BatchResponse[]; inventories: InventoryResponse[] }>

// 内部拆分入口
private async grantConsumerMonthlyPlan(tx, ctx, requestedValidFrom): Promise<EntitlementBatch[]>
private async grantConsumerTopup(tx, ctx, validFrom, kind: "token"|"storage"): Promise<EntitlementBatch[]>
private async grantEnterprisePlan(tx, ctx, validFrom): Promise<EntitlementBatch[]>
private async grantMonthlySeatPlan(tx, ctx, validFrom): Promise<EntitlementBatch[]>
```

### 数据库关键字段

| 表 | 字段 | 类型 | 说明 |
|---|---|---|---|
| `billing_orders` | `id` | UUID (text) | **主键，entitlement_batch 关联用** |
| `billing_orders` | `orderNo` | text | 展示用订单号（如 `BILL20260805...`），**不用于关联** |
| `billing_orders` | `paymentStatus` | enum-text | `PENDING` → `PAYING` → `SUCCESS` / `FAILED` / `CLOSED`（全大写） |
| `billing_orders` | `grantStatus` | enum-text | `PENDING` → `PROCESSING` → `SUCCESS` / `FAILED`（全大写） |
| `billing_orders` | `wechatTransactionId` | text | 微信交易号（明文），**排查必查** |
| `billing_orders` | `notifyRaw` | jsonb | 微信回调**原始加密报文**（见 §Gotcha 1） |
| `billing_orders` | `planSnapshot` | jsonb | 下单时刻的套餐快照（含 name/code/planType/planLevel/metadata） |
| `entitlement_batches` | `sourceRefId` | text | **= billing_orders.id**（UUID，不是 orderNo） |
| `entitlement_batches` | `orderId` | text | **= billing_orders.id**（冗余副本） |
| `entitlement_batches` | `entitlementType` | enum-text | `monthly_plan` / `token` / `storage` / `member` / `feature` |

---

## 3. Contracts

### 3.1 订单状态机

```
创建订单 → PENDING
         → PAYING     (调用微信支付预下单)
         → SUCCESS    (微信回调确认)
         → FAILED     (支付失败)
         → CLOSED     (定时任务关闭超时未付订单)
```

**⚠️ 状态值全大写字符串**：`SUCCESS` 不是 `paid`，`PENDING` 不是 `pending`。前端/后端都用大写比较。

### 3.2 发放流程（fulfillPaidOrder）

```
wechat callback → markBillingOrderPaid (paymentStatus=SUCCESS, grantStatus=PENDING)
                → fulfillPaidOrder
                  ├─ grantStatus 乐观锁: PENDING → PROCESSING
                  ├─ grantPaidOrderSnapshot (事务)
                  │   ├─ idempotency 检查（已有则直接返回）
                  │   ├─ 按 planType 分发到对应 grant 函数
                  │   └─ 创建 entitlement_batch + grant ledger
                  ├─ grantStatus → SUCCESS
                  └─ 异常时 grantStatus → FAILED + metadata.grantError
```

### 3.3 权益批次拆分规则

| planType | 拆分 | 数量 | 说明 |
|---|---|---|---|
| `consumer_monthly_plan` | monthly_plan + token + storage (+ member + feature 视配置) | **≥3 条** | `createMonthlyGrantGroup` 先建 monthly_plan anchor，再按 `planEntitlementSpecs` 追加 |
| `consumer_token_topup` | token | **1 条** | `grantConsumerTopup(tx, ctx, validFrom, "token")` |
| `consumer_storage_topup` | storage | **1 条** | `grantConsumerTopup(tx, ctx, validFrom, "storage")` |
| `b2b_enterprise_plan` | 由 B 端套餐配置决定 | 视配置 | `grantEnterprisePlan` |
| `b2b_monthly_seat_plan` | 座位 + token + storage | 视配置 | `grantMonthlySeatPlan` |
| `b2b_token_topup` | inventory（不是 batch） | 1 条 inventory | `grantB2BTopupInventory` |

**Plus套餐（consumer_monthly_plan, planLevel=1）实测产出**：3 条 batch
1. `monthly_plan`（1 plan_period，账号有效期锚点）
2. `token`（30,000,000 billing_token）
3. `storage`（10,737,418,240 byte = 10 GB）

### 3.4 生效时间规则

**业务日起始计算**（`startOfBillingBusinessDay`，UTC+8 对齐）：

```typescript
// apps/api/src/billing/billing-date.ts
const BUSINESS_TIMEZONE_OFFSET_MS = 8 * 60 * 60 * 1000;

function startOfBillingBusinessDay(date: Date) {
  const shifted = new Date(date.getTime() + BUSINESS_TIMEZONE_OFFSET_MS);
  return new Date(
    Date.UTC(shifted.getUTCFullYear(), shifted.getUTCMonth(), shifted.getUTCDate())
      - BUSINESS_TIMEZONE_OFFSET_MS
  );
}
```

**生产实测（UTC+8 展示）**：

| planType | 购买时间 | validFrom（+8） | 规则 |
|---|---|---|---|
| consumer_monthly_plan | 08-05 20:02 | **08-06 00:00** | 次日零点（business day start of paidAt 经 planMonthlyQueue 推进） |
| consumer_token_topup | 08-05 23:15 | **08-05 00:00** | 当日零点（`startOfBillingBusinessDay(paidAt)`） |
| consumer_token_topup | 08-05 23:15 | validUntil = **11-02 23:59:59** | 90 天（periodDays=90，`addBillingDays(validFrom, 90) - 1ms`） |
| consumer_monthly_plan | 08-05 20:02 | validUntil = **09-04 23:59:59** | 30 天（periodDays=30） |

> **⚠️ 关键差异**：月包和 topup 的 `validFrom` 策略不同。月包经 `planMonthlyQueue`/`calculateEffectiveStart` 计算（可能推进到下一周期），topup 直接 `startOfBillingBusinessDay(paidAt)`。

### 3.5 数据关联约定

```
billing_orders.id (UUID)
    ↓
entitlement_batches.sourceRefId = billing_orders.id   ← 主要关联字段
entitlement_batches.orderId     = billing_orders.id   ← 冗余副本
```

**⚠️ 不要用 `billing_orders.orderNo`（如 `BILL20260805...`）做关联**。`orderNo` 仅用于展示和对账。

### 3.6 微信支付回调报文（notifyRaw）

`notifyRaw` 存储微信回调的**原始加密报文**（`resource_type: encrypt-resource`，AEAD_AES_256_GCM），仅以下字段为明文：

```json
{
  "id": "<uuid>",
  "event_type": "TRANSACTION.SUCCESS",
  "summary": "支付成功",
  "create_time": "2026-08-05T23:15:39+08:00",
  "resource_type": "encrypt-resource",
  "resource": {
    "algorithm": "AEAD_AES_256_GCM",
    "nonce": "...",
    "ciphertext": "...",
    "associated_data": "..."
  }
}
```

**明文交易信息**（微信交易号、openid 等）从以下字段取：

| 字段 | 来源 |
|---|---|
| `wechatTransactionId` | 微信交易号（如 `4500000267202608053175393462`） |
| `wechatOutTradeNo` | 商户订单号（如 `IWBILL20260805151500244636`） |
| `payType` | `NATIVE`（扫码） / `JSAPI` / `H5` 等 |

---

## 4. Validation & Error Matrix

| 条件 | 错误 | 处理方式 |
|---|---|---|
| 月包 `subjectType !== "enterprise_user"` | BadRequest | 发放前校验，不应到达此处（前端拦截） |
| 月包 `plan.periodDays` 缺失 | BadRequest | 套餐配置错误，检查 billing_plans |
| Topup 无活跃月包且非 batch 模式 | BadRequest `"topup requires active monthly plan"` | 前端应在购买入口拦截 |
| Topup token 但 `plan.tokenAmount` 缺失/≤0 | BadRequest | 套餐配置错误 |
| Topup storage 但 `plan.storageBytes` 缺失/≤0 | BadRequest | 套餐配置错误 |
| `grantStatus` 并发竞争 | ConflictException | 乐观锁 `PROCESSING` 状态防重入 |
| 发放过程异常 | grantStatus → `FAILED`，metadata.grantError 记录 | 可重试（fulfillPaidOrder 检测 FAILED 可重入） |

---

## 5. Good / Base / Bad Cases

### Good ✅

```sql
-- 正确：用 billing_orders.id 关联 entitlement_batches
SELECT eb.*
FROM billing_orders o
JOIN entitlement_batches eb ON eb."sourceRefId" = o.id
WHERE o."paymentStatus" = 'SUCCESS'
  AND o."paidAt" >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '3 days';
```

### Base（标准查询模板）

```sql
-- 查最近 3 天成功订单 + 套餐快照 + 手机号
SELECT o."orderNo", ui."providerUserId" AS phone,
       o."amountCents", o."planSnapshot"->>'name' AS plan_name,
       TO_CHAR(o."paidAt" + INTERVAL '8 hours', 'YYYY-MM-DD HH24:MI:SS') AS "paidAt(+8)"
FROM billing_orders o
LEFT JOIN user_identities ui ON o."buyerUserId" = ui."userId"
  AND ui."isDeleted" = false AND ui.provider = 'phone'
WHERE o."paymentStatus" = 'SUCCESS'
  AND o."paidAt" >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '3 days'
ORDER BY o."paidAt" DESC;
```

### Bad ❌

```sql
-- ❌ 用 orderNo 关联（错误，orderNo 不匹配 sourceRefId）
SELECT eb.* FROM entitlement_batches eb
WHERE eb."sourceRefId" = 'BILL20260805120133826131';  -- 永远查不到

-- ❌ 从 notifyRaw 取交易详情（错误，notifyRaw 是加密报文）
SELECT o."notifyRaw"->'resource'->>'transaction_id'  -- 返回 NULL
FROM billing_orders o;

-- ❌ paidAt 直接用 NOW() 比较（8h 时区偏差）
WHERE o."paidAt" >= NOW() - INTERVAL '3 days';  -- 边界订单会漏

-- ❌ paymentStatus 用小写比较
WHERE o."paymentStatus" = 'paid';  -- 永远匹配不到
```

---

## 6. Tests Required

### 6.1 发放拆分测试（`entitlement.service.test.ts`）

| 断言点 | 用例 |
|---|---|
| consumer_monthly_plan 产生 ≥3 条 batch | 验证 monthly_plan + token + storage 三条均存在 |
| consumer_token_topup 产生 1 条 batch | 验证 entitlementType = "token"，amount = plan.tokenAmount |
| 月包 batch 的 validFrom 为业务日起始 | `validFrom === startOfBillingBusinessDay(paidAt)` 或经 planMonthlyQueue 推进 |
| topup batch 的 validUntil = validFrom + periodDays | 精度到秒（addBillingDays，非 endOfBillingBusinessDay） |
| 所有 batch 的 sourceRefId = order.id | 确认关联正确 |

### 6.2 状态机测试（`billing-order.service.test.ts`）

| 断言点 | 用例 |
|---|---|
| fulfillPaidOrder 幂等性 | 同一订单调用两次，第二次返回 `idempotent: true` |
| grantStatus 乐观锁 | 并发调用，一个 PROCESSING，另一个 ConflictException |
| 发放失败可重试 | grantStatus=FAILED 后重新调用能成功 |

### 6.3 时区边界测试

| 断言点 | 用例 |
|---|---|
| 23:59 购买 → validFrom 仍为当日零点 | `startOfBillingBusinessDay(Aug 5 23:59 Beijing)` = Aug 5 00:00 Beijing |
| 00:01 购买 → validFrom 为当日零点 | `startOfBillingBusinessDay(Aug 6 00:01 Beijing)` = Aug 6 00:00 Beijing |

---

## 7. Wrong vs Correct

### Wrong ❌ — 用 notifyRaw.resource 取交易信息

```typescript
// 错误：notifyRaw.resource 是 AEAD_AES_256_GCM 加密的 ciphertext
const transactionId = order.notifyRaw?.resource?.transaction_id; // undefined
```

**Why**: 微信回调的 `resource` 字段包含 `algorithm`/`nonce`/`ciphertext`/`associated_data`，敏感信息已加密。应用层在收到回调后解密并将明文写入 `wechatTransactionId` 等字段。

### Correct ✅ — 从订单表明文取交易信息

```typescript
// 正确：从 billing_orders 的明文字段取
const transactionId = order.wechatTransactionId;  // "4500000267202608053175393462"
const outTradeNo = order.wechatOutTradeNo;        // "IWBILL20260805151500244636"
```

---

### Wrong ❌ — 用 orderNo 关联 entitlement_batches

```sql
-- 错误：orderNo 是展示编号，不是关联键
SELECT eb.* FROM entitlement_batches eb
WHERE eb."sourceRefId" = 'BILL20260805120133826131';  -- NULL result
```

### Correct ✅ — 用 billing_orders.id 关联

```sql
-- 正确：sourceRefId/orderId = billing_orders.id (UUID)
SELECT eb.* FROM entitlement_batches eb
JOIN billing_orders o ON eb."sourceRefId" = o.id
WHERE o."orderNo" = 'BILL20260805120133826131';
```

---

### Wrong ❌ — 时区比较遗漏 AT TIME ZONE

```sql
-- 错误：会话时区 UTC+8，paidAt 按 +8 解释，窗口起点偏移 8h
WHERE o."paidAt" >= NOW() - INTERVAL '3 days';
```

### Correct ✅ — 对齐 UTC 墙钟

```sql
-- 正确：先转 UTC 墙钟再比较
WHERE o."paidAt" >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '3 days';
```

---

## Gotcha 汇总

### Gotcha 1: notifyRaw 是加密报文

`billing_orders.notifyRaw` 存储的是微信回调**原始加密报文**（`resource_type: encrypt-resource`，AEAD_AES_256_GCM），只有外层元数据（id, event_type, create_time, summary）是明文。明文交易号在 `wechatTransactionId`/`wechatOutTradeNo` 字段。

### Gotcha 2: paymentStatus/grantStatus 全大写

枚举值是**全大写字符串**：`SUCCESS`、`PENDING`、`PROCESSING`、`FAILED`、`CLOSED`。不是 `paid`/`pending` 等小写。

### Gotcha 3: sourceRefId = order.id，不是 orderNo

`entitlement_batches.sourceRefId` 和 `orderId` 都关联 `billing_orders.id`（UUID），**不是** `billing_orders.orderNo`（展示编号）。

### Gotcha 4: 月包 vs Topup 的 validFrom 策略不同

- **月包**（consumer_monthly_plan）：经 `calculateEffectiveStart` + `planMonthlyQueue` 计算，观测到次日零点生效
- **Topup**（consumer_token_topup）：直接 `startOfBillingBusinessDay(paidAt)`，观测到当日零点生效

修改发放逻辑时注意这两种策略的差异。

### Gotcha 5: 月包一次发放多条 batch

`consumer_monthly_plan` 通过 `createMonthlyGrantGroup` → `planEntitlementSpecs` 拆分出多条 `entitlement_batch`（至少 monthly_plan + token + storage 三条）。Topup 只创建 1 条。查询"订单对应几条 batch"时，月包要预期 ≥3 条。

### Gotcha 6: paidAt 时区比较陷阱

`paidAt` 是 `timestamp without time zone`（UTC 墙钟），会话时区是 UTC+8。比较窗口时必须用 `(NOW() AT TIME ZONE 'UTC')` 对齐，否则边界订单会漏。详见 [DB timezone timestamp comparison pitfall](../../guides/...) 和 memory。
