# EvoMind 月包、补充包与权益批次 API 文档（当前实现版）

本文对齐当前代码实现，覆盖月包方案新增接口、仍保留接口和明确废弃的历史接口。若旧 Phase 文档或历史 PR 描述与本文冲突，以本文为准。

## 1. 基本约定

### 1.1 认证与权限

- 普通用户接口使用 `Authorization: Bearer <access_token>`。
- 超管后台接口额外要求 `AdminGuard`。
- B 端企业管理员能力以企业成员角色 `owner/admin` 为准。
- C 端用户只查询和操作当前登录用户在当前企业下的权益。

### 1.2 核心枚举

`enterpriseKind`：

| 值 | 含义 |
| --- | --- |
| `b2b` | B 端企业，支持席位月包、席位补充包库存、默认配额兜底 |
| `consumer` | C 端企业，用户购买个人月包和个人补充包 |
| `evomind_consumer` | 平台默认 C 端企业，业务上仍按 C 端个人权益处理 |

数据库同步时，除固定 EvoMind C 端企业 `00000000-0000-0000-0000-000000000001` 外，存量企业默认按 `b2b` 处理。B 端企业的默认成员配额策略会被回填为开启；`consumer` 和 `evomind_consumer` 默认配额策略强制关闭且不能开启。

`planType`：

| 值 | 含义 | 主体 |
| --- | --- | --- |
| `b2b_enterprise_plan` | B 端企业席位月包 | `enterprise` |
| `b2b_token_topup` | B 端席位 Token 补充包 | 库存归企业，分配后归成员 |
| `b2b_storage_topup` | B 端席位空间补充包 | 库存归企业，分配后归成员 |
| `consumer_monthly_plan` | C 端个人月包 | `enterprise_user` |
| `consumer_token_topup` | C 端个人 Token 补充包 | `enterprise_user` |
| `consumer_storage_topup` | C 端个人空间补充包 | `enterprise_user` |
| `private_deployment_lead` | 私有化线索套餐 | 不发放权益 |

`entitlementType`：

| 值 | 含义 |
| --- | --- |
| `monthly_plan` | 月包周期锚点 |
| `token` | 计费 Token |
| `storage` | 空间容量 |
| `member` | 席位/成员权益展示批次 |
| `feature` | 功能权益展示批次 |

`subjectType`：

| 值 | 含义 |
| --- | --- |
| `enterprise` | 企业主体，当前主要用于 B 端月包锚点、B 端补充包库存 |
| `enterprise_user` | 企业用户身份，所有可消费 Token/空间最终归属到这里 |

`sourceType` 当前必须保留业务来源，不再用 `admin_grant` 覆盖套餐来源：

| 值 | 含义 |
| --- | --- |
| `b2b_enterprise_plan` | B 端月包锚点及其成员 token/storage 子批次 |
| `b2b_token_topup` | B 端 token 补充包库存或成员分配批次 |
| `b2b_storage_topup` | B 端空间补充包库存或成员分配批次 |
| `consumer_monthly_plan` | C 端月包锚点及 token/storage 子批次 |
| `consumer_token_topup` | C 端 token 补充包 |
| `consumer_storage_topup` | C 端空间补充包 |
| `admin_grant` | 真正非套餐的后台赠送旧来源 |

`paymentStatus`：

| 值 | 含义 |
| --- | --- |
| `PENDING` | 订单已创建，尚未进入支付中 |
| `PAYING` | 已创建微信 Native 支付单，等待支付 |
| `SUCCESS` | 支付成功 |
| `FAILED` | 创建支付单失败或支付失败 |
| `CLOSED` | 订单关闭 |

`grantStatus`：

| 值 | 含义 |
| --- | --- |
| `PENDING` | 未发放权益 |
| `PROCESSING` | 正在发放权益 |
| `SUCCESS` | 权益已发放 |
| `FAILED` | 权益发放失败，可后台重试 |

## 2. 套餐配置接口

### 2.1 超管套餐列表

```http
GET /api/admin/billing/plans
```

查询参数：

| 参数 | 必填 | 含义 |
| --- | --- | --- |
| `enterpriseId` | 否 | 按企业过滤 |
| `name` | 否 | 套餐名称模糊查询 |
| `planType` | 否 | 按套餐类型过滤 |
| `enterpriseKind` | 否 | 按企业类型过滤 |
| `isActive` | 否 | 是否上架 |
| `includeDeleted` | 否 | 是否包含软删除套餐 |

### 2.2 获取套餐详情

```http
GET /api/admin/billing/plans/{planId}
```

返回套餐配置、企业信息、是否已发放过等后台字段。

### 2.3 创建套餐

```http
POST /api/admin/billing/plans
```

请求示例：

```json
{
  "enterpriseId": "uuid",
  "name": "B端套餐-月包2",
  "code": "b2b-monthly-l2",
  "planType": "b2b_enterprise_plan",
  "priceCents": 1,
  "periodDays": 30,
  "planLevel": 2,
  "tokenAmount": "20000000",
  "storageBytes": "2147483648",
  "memberLimit": 50,
  "requiresActiveMonthlyPlan": false,
  "isActive": true
}
```

核心校验：

- `b2b_enterprise_plan`：企业必须是 `b2b`，必须有 `periodDays`、正整数 `planLevel`、正数 `memberLimit`、正数 `tokenAmount`、正数 `storageBytes`。
- `b2b_token_topup`：企业必须是 `b2b`，`memberLimit` 表示库存席位数，必须有 `periodDays` 和正数 `tokenAmount`，不能配置空间。
- `b2b_storage_topup`：企业必须是 `b2b`，`memberLimit` 表示库存席位数，必须有 `periodDays` 和正数 `storageBytes`，不能配置 token。
- `consumer_monthly_plan`：企业必须是 C 端，必须有正整数 `planLevel`，可配置 token 和空间。
- `consumer_token_topup`：企业必须是 C 端，必须有 `periodDays` 和正数 `tokenAmount`。
- `consumer_storage_topup`：企业必须是 C 端，必须有 `periodDays` 和正数 `storageBytes`。
- `private_deployment_lead` 不发放权益，不进入套餐订单主链路。

### 2.4 更新套餐

```http
PATCH /api/admin/billing/plans/{planId}
```

规则：

- 未发放过的套餐可以调整配置。
- 已产生权益批次、库存或订单的套餐，不允许原地修改 `enterpriseId`、`planType`、`subjectType` 这类会改变历史语义的字段。
- 价格、名称、上下架等只影响后续订单；历史订单按 `planSnapshot` 发放。

### 2.5 上下架套餐

```http
PATCH /api/admin/billing/plans/{planId}/status
```

请求：

```json
{ "isActive": true }
```

### 2.6 删除套餐

```http
DELETE /api/admin/billing/plans/{planId}
```

软删除。已产生历史订单或权益的套餐仍保留历史快照，不影响已发放权益。

### 2.7 用户侧套餐预览

```http
GET /api/billing/plans
```

用途：工作台购买套餐弹窗读取当前企业可购买套餐。

查询参数同后台列表，但只返回可展示字段。前端按企业类型过滤：

- B 端企业：展示 `b2b_enterprise_plan`、`b2b_token_topup`、`b2b_storage_topup`，入口只对企业 `owner/admin` 可见。
- C 端企业：展示 `consumer_monthly_plan`、`consumer_token_topup`、`consumer_storage_topup`，入口对 active 成员可见。

## 3. 套餐订单与微信支付接口

### 3.1 创建套餐订单

```http
POST /api/billing/orders
```

请求：

```json
{
  "enterpriseId": "uuid",
  "planId": "uuid",
  "payType": "NATIVE"
}
```

规则：

- `payType` 当前仅支持 `NATIVE`。
- 套餐必须属于请求企业、已上架、未删除、价格大于 0。
- C 端套餐订单主体为 `enterprise_user`，权益归属当前登录用户。
- B 端套餐订单主体为 `enterprise`，购买人必须是该企业 `owner/admin`。
- 创建订单时保存不可变 `planSnapshot`；支付后发放只读取快照。
- 微信支付真实模式需要 `WX_MCH_ID`、`WX_APP_ID`、`MCH_SERIAL_NO`、`WX_API_V3_KEY`、`WX_NOTIFY_URL`、`MCH_PRIVATE_KEY_PATH`、`WX_PUBLIC_KEY_PATH`。
- 本地 `WX_PAY_TEST=true` 时走 mock 支付：创建订单后立即标记支付成功并发放权益。

返回示例：

```json
{
  "order": {
    "orderNo": "BILL20260709134508902927",
    "paymentStatus": "PAYING",
    "grantStatus": "PENDING",
    "planSnapshot": {
      "planType": "consumer_monthly_plan",
      "planLevel": 2,
      "periodDays": 30,
      "tokenAmount": "40000000",
      "storageBytes": "4294967296"
    }
  },
  "payment": {
    "outTradeNo": "IWBILL20260709134508902927",
    "codeUrl": "weixin://wxpay/...",
    "expireAt": "2026-07-09T06:15:08.000Z",
    "order": {
      "orderNo": "BILL20260709134508902927",
      "paymentStatus": "SUCCESS",
      "grantStatus": "SUCCESS"
    }
  }
}
```

说明：真实支付时 `payment.order` 通常为空或不是最终态，前端继续轮询订单；mock 支付时 `payment.order` 可能已经是最终成功态，前端应优先使用。

### 3.2 查询套餐订单

```http
GET /api/billing/orders/{orderNo}
```

规则：

- C 端用户只能查自己的订单。
- B 端企业订单只有该企业 `owner/admin` 可查。
- 前端轮询直到 `paymentStatus=SUCCESS && grantStatus=SUCCESS` 或失败状态。

### 3.3 后台重试权益发放

```http
POST /api/admin/billing/orders/{orderNo}/retry-grant
```

规则：

- 仅超管。
- 订单必须 `paymentStatus=SUCCESS`。
- 如果已经 `grantStatus=SUCCESS`，幂等返回已有结果。
- 发放仍使用订单快照，不读取当前套餐配置。

### 3.4 后台标记已支付

```http
POST /api/admin/billing/orders/{orderNo}/mark-paid
```

用途：测试、联调或人工核验场景。该接口不能绕开发放逻辑，会调用与微信回调相同的履约链路。

### 3.5 微信支付回调

```http
POST /api/pay/wechat/notify
```

规则：

- `IWBILL` 前缀订单进入套餐订单履约。
- 历史充值订单仍进入 `recharge_orders` 钱包充值逻辑。
- 金额必须等于 `billing_orders.amountCents`。
- 重复回调幂等，不重复发放权益。
- 支付成功但发放失败时不回滚支付状态，订单进入 `grantStatus=FAILED`，后台可重试。

### 3.6 旧充值接口保留但不属于月包主链路

以下接口属于旧积分充值体系，保留兼容，不作为新套餐订单接口：

```http
GET  /api/pay/wechat/packages
POST /api/pay/wechat/create
GET  /api/pay/wechat/status
```

## 4. 默认配额策略接口

默认配额策略是月包迁移期的旧链路兼容开关：B 端企业默认开启，用于无 active B 端月包时继续发放旧成员默认配额；一旦企业存在 active B 端月包，策略即使开启也不生效。C 端企业和 EvoMind C 端企业永远不支持开启。

### 4.1 超管读取默认配额策略

```http
GET /api/admin/billing/default-quota-policy?enterpriseId={enterpriseId}
```

返回字段：

| 字段 | 含义 |
| --- | --- |
| `enabled` | 默认配额策略是否开启；B 端同步回填默认开启，也可由超管后续调整 |
| `effectiveEnabled` | 当前是否实际生效 |
| `blockedReason` | 不生效原因 |
| `activeMonthlyPlan` | 当前阻断默认配额的 active B 端月包摘要 |

`blockedReason`：

| 值 | 含义 |
| --- | --- |
| `consumer_enterprise` | C 端企业不支持默认配额 |
| `unsupported_enterprise_kind` | 不支持的企业类型 |
| `active_b2b_monthly_plan` | B 端 active 月包正在生效 |
| `null` | 未被阻断 |

### 4.2 超管更新默认配额策略

```http
PATCH /api/admin/billing/default-quota-policy
```

请求：

```json
{
  "enterpriseId": "uuid",
  "enabled": true,
  "reason": "manual fallback"
}
```

规则：

- C 端企业不能开启。
- B 端企业有 active B 端月包时不能开启。
- B 端企业默认开启；开启成功只代表旧 token quota 和成员默认空间配额可以作为兜底。
- 一旦 B 端月包 active，`effectiveEnabled=false`。
- `consumer` 和 `evomind_consumer` 不能开启；企业类型切换为 C 端时策略会同步关闭。

### 4.3 组织管理员只读

```http
GET /api/billing/default-quota-policy?enterpriseId={enterpriseId}
```

规则：调用人必须是该企业 `owner/admin`。组织管理员只能查看，不能切换。

## 5. 权益发放与批次接口

### 5.1 超管发放套餐

```http
POST /api/admin/billing/entitlements/grant-plan
```

请求：

```json
{
  "enterpriseId": "uuid",
  "subjectType": "enterprise_user",
  "userId": "uuid",
  "planId": "uuid",
  "validFrom": "2026-07-09T00:00:00.000+08:00",
  "sourceRefType": "admin_grant",
  "sourceRefId": "manual-001"
}
```

规则：

- `sourceType` 默认使用 `plan.planType`。后台发放只通过 `sourceRefType/sourceRefId` 记录操作来源，不能把套餐来源覆盖成 `admin_grant`。
- B 端月包和 B 端补充包发放主体为 `enterprise`，不需要 `userId`。
- C 端月包和 C 端补充包发放主体为 `enterprise_user`，必须提供 `userId`。
- `validFrom` 为空时取当前本地业务日开始。
- 发放使用幂等键，重复请求不得重复生成权益。

### 5.2 手动过期处理

```http
POST /api/admin/billing/entitlements/expire
```

请求：

```json
{
  "now": "2026-08-08T00:00:00.000+08:00",
  "entitlementTypes": ["monthly_plan", "token", "storage"]
}
```

规则：将已到期 active/scheduled 批次置为 `expired`，剩余额度归零并写过期流水。页面上的“手动补跑过期处理”调用该能力。

### 5.3 B 端补充包库存列表

```http
GET /api/admin/billing/topup-inventories?enterpriseId={enterpriseId}
```

返回企业购买或后台发放的 B 端补充包库存：

- `totalSeats`：总库存席位数。
- `remainingSeats`：未分配席位数。
- `amountPerSeat`：每席 token 或空间额度。
- `periodDays`：分配给成员后的有效期天数。
- `status`：库存状态。

### 5.4 分配 B 端补充包库存

```http
POST /api/admin/billing/topup-inventories/{inventoryId}/assign
```

请求：

```json
{
  "enterpriseId": "uuid",
  "userId": "uuid"
}
```

规则：

- 只能分配 `b2b_token_topup` 或 `b2b_storage_topup` 库存。
- 企业必须存在 active B 端月包。
- 成员必须是该企业 active 成员。
- 每次分配消耗 1 个库存席位，生成该成员的 `enterprise_user` 批次。
- 分配当天开始计算该成员补充包有效期。

### 5.5 C 端批量后台赠送

```http
POST /api/admin/billing/entitlements/bulk-grant
```

请求：

```json
{
  "enterpriseId": "uuid",
  "userIds": ["uuid1", "uuid2"],
  "entitlementType": "token",
  "amount": "100000",
  "periodDays": 30,
  "reason": "活动赠送"
}
```

规则：

- 仅用于 C 端企业。
- 只给 active 成员发放。
- 生成 `sourceType=admin_grant` 的非套餐赠送批次。
- 非套餐赠送包不进入月包队列。
- active 月包期间，旧/后台来源不参与 AI token 扣费；无 active 月包时可作为兜底可用批次。

### 5.6 后台权益汇总

```http
GET /api/admin/billing/entitlements/summary
```

查询参数：

| 参数 | 必填 | 含义 |
| --- | --- | --- |
| `enterpriseId` | 是 | 企业 |
| `subjectType` | 是 | `enterprise` 或 `enterprise_user` |
| `userId` | 取决于主体 | `enterprise_user` 必填 |

返回 token、storage、member、feature 的授权、剩余、冻结、可用等摘要。

### 5.7 权益批次列表

```http
GET /api/admin/billing/entitlement-batches
```

查询参数：

| 参数 | 含义 |
| --- | --- |
| `enterpriseId` | 企业 |
| `userId` | 用户 |
| `subjectType` | 主体类型 |
| `entitlementType` | 权益类型 |
| `status` | 批次状态 |
| `sourceType` | 来源 |
| `planId` | 套餐 |
| `scope` | `subject` 或 `enterprise_aggregate` |
| `page/pageSize` | 分页 |

视图规则：

- B 端只选企业：使用 `enterprise_aggregate` 展示企业月包锚点和补充包库存摘要；成员级批次可用于排障，但不能计入企业套餐数量。
- B 端选择企业 + 手机号/用户：展示该成员自己的月包 token/storage 批次、补充包批次、赠送批次。
- C 端只选企业：按企业下用户套餐聚合展示，用户对象优先显示手机号。
- C 端选择企业 + 手机号/用户：展示该用户自己的套餐和批次。

storage 展示口径：

- `remainingAmount` 是批次账务字段，不代表实时剩余空间。
- 业务展示字段使用 `displayGrantedAmount/displayUsedAmount/displayRemainingAmount`。
- 同一用户多个 active storage 批次按“月包优先、空间补充包其次”分摊实际工作台用量。

### 5.8 权益批次详情

```http
GET /api/admin/billing/entitlement-batches/{batchId}
```

返回：

- 批次业务信息、套餐快照、企业展示信息、用户展示信息。
- 技术 ID 默认不用于业务理解。
- storage 使用“授权空间 / 已用空间 / 可用空间”。
- token 使用“发放 Token / 剩余 Token / 冻结 Token / 已用 Token”。

### 5.9 批次流水

```http
GET /api/admin/billing/entitlement-batches/{batchId}/ledgers
```

流水动作业务文案：

| changeType | 展示含义 |
| --- | --- |
| `grant` | 权益发放 |
| `allocate` | 权益分配 |
| `freeze` | 对话预占额度 |
| `capture` | 对话实际扣费 |
| `release` | 释放未使用预占额度 |
| `expire` | 过期 |
| `adjust` | 后台调整 |

后台详情页可展示 freeze/capture/release，但用户侧 Token 明细不能展示 freeze/release。

## 6. 用户侧权益接口

### 6.1 当前用户权益摘要

```http
GET /api/billing/entitlements/summary?enterpriseId={enterpriseId}&subjectType=enterprise_user
```

规则：

- 只能查当前登录用户。
- `enterpriseId` 允许 nil UUID 形式，但权限仍按当前用户 active 成员身份校验。
- active 月包期间只汇总可消费的月包和补充包，不把旧后台批次算入余额。

用途：工作台头像菜单 token 余额。

### 6.2 Token 明细

```http
GET /api/billing/entitlements/token-ledgers?enterpriseId={enterpriseId}&page=1&pageSize=20
```

规则：

- 只返回当前用户 token 入账和真实出账。
- 包含 `grant/allocate/capture` 等业务动作。
- 排除 `freeze/release`，避免用户看到技术性预占流水。
- 展示余额使用业务余额字段：`displayBeforeAmount/displayAfterAmount = remaining + freeze`，不是数据库内部剩余字段。

### 6.3 Token 消费记录

```http
GET /api/billing/entitlements/token-consumptions?enterpriseId={enterpriseId}&page=1&pageSize=20
```

规则：

- 只展示真实扣费 `capture`。
- 按 AI 对话/任务聚合为消费记录。
- 当前头像弹窗已不再把该接口作为“套餐记录”数据源；保留用于消费审计或后续消费页。

### 6.4 套餐记录

```http
GET /api/billing/entitlements/package-records?enterpriseId={enterpriseId}&page=1&pageSize=20
```

规则：

- 以当前用户在当前企业下的 `entitlementBatch` 为主数据源。
- C 端：展示本人购买或后台发放的月包、token 补充包、空间补充包。
- B 端：展示成员被企业月包生成的 token/storage 权益，以及分配到的 token/空间补充包。
- 同一次套餐发放按 `grantGroupId`、订单或来源信息聚合，避免月包 token/storage/monthly_plan 拆成多条重复套餐。
- storage 组件使用按月包优先分摊后的展示字段。

## 7. AI Token 扣费接口关联

对话入口：

```http
POST /api/zclaw/chat/message/stream
```

扣费规则：

- 请求头 `x-enterprise-id` 决定当前企业身份。
- 发起对话前按 `BILLING_AI_FIXED_HOLD_TOKENS` 预冻结，默认 `100000`。
- 对话成功并拿到 usage 后按真实 usage `capture`，释放未使用预占额度。
- 对话失败、取消或无 usage 结束时释放冻结。
- C/B 端 active 月包期间：月包批次优先，其次补充包；旧 quota 和旧批次不参与。
- 没有 active 月包时：B 端只有默认配额策略 effective 或旧手动批次可作为兜底；C 端按当前可用非套餐/赠送批次兜底。

### 7.1 后台计费任务审计

```http
GET /api/admin/billing/tasks
```

查询参数：

| 参数 | 含义 |
| --- | --- |
| `enterpriseId` | 企业 |
| `userId` | 用户 |
| `status` | 任务状态 |
| `page/pageSize` | 分页 |

用途：查看 AI 任务冻结、扣费、释放的任务级审计记录。

```http
GET /api/admin/billing/tasks/{taskId}
```

用途：查看单个计费任务，包含 `fixedHoldTokens`、`heldTokens`、`capturedTokens`、`releasedTokens`、`billingUsageTokens`、`billingOverrunTokens` 等字段。

```http
GET /api/admin/billing/tasks/{taskId}/events
```

用途：查看任务事件，例如 reserve、capture、release、error 等内部事件。

## 8. 成员管理与旧配额接口

以下接口仍存在，但在 active 月包期间会被前后端禁用或后端拒绝写入：

```http
POST /api/zclaw/admin/conversation-quotas
POST /api/zclaw/admin/conversation-quotas/members
POST /api/zclaw/admin/token-quota-batches
PUT  /api/zclaw/admin/token-quota-batches/{batchId}
POST /api/zclaw/admin/token-quota-batches/{batchId}/migrate
POST /api/zclaw/admin/token-quota-batches/members/move
```

组织管理员路径同理：

```http
POST /api/zclaw/enterprise-admin/conversation-quotas
POST /api/zclaw/enterprise-admin/conversation-quotas/members
POST /api/zclaw/enterprise-admin/token-quota-batches
PUT  /api/zclaw/enterprise-admin/token-quota-batches/{batchId}
POST /api/zclaw/enterprise-admin/token-quota-batches/{batchId}/migrate
POST /api/zclaw/enterprise-admin/token-quota-batches/members/move
```

展示接口仍会返回 tokenEntitlements，用于成员管理“消耗/限额”和 Token 消耗详情：

```http
GET /api/zclaw/admin/conversation-quotas/{enterpriseId}/members
GET /api/zclaw/enterprise-admin/conversation-quotas/{enterpriseId}/members
```

## 9. 明确废弃或仅兼容的接口

以下接口是旧 B 端企业池模型能力，不再作为月包 v2 主流程使用：

```http
POST /api/admin/billing/entitlements/allocate
POST /api/admin/billing/entitlements/reclaim
GET  /api/admin/billing/entitlements/enterprise-pool-summary
```

废弃原因：

- v2 不再把 B 端 token/storage 放入企业总池。
- B 端月包直接为占席成员生成成员批次。
- B 端补充包先进入库存，分配后生成成员批次。
- 新消费链路只从成员自己的 `enterprise_user` 批次扣费。

保留策略：

- 可用于历史数据查看或迁移辅助。
- 新页面和新业务不得新增依赖。
- active 月包期间不得通过这些接口让旧企业池额度重新参与消费。

## 10. 关键场景示例

### 10.1 C 端用户已有等级 1 月包，再购买等级 2 月包

前提：

- 月包 1：等级 1，`2026/07/08 - 2026/08/07`，active。
- 用户在 `2026/07/09` 购买月包 2：等级 2，30 天。

结果：

- 月包 2 立即 active：`2026/07/09 - 2026/08/08`。
- 月包 1 被打断后排到月包 2 后，只保留剩余天数。
- 如果月包 1 已使用 1 天，剩余周期示例为：`2026/08/08 - 2026/09/06`。
- 月包 1 同一 `grantGroupId` 下的 `monthly_plan/token/storage/member/feature` 子批次一起变为 scheduled，周期一起移动。
- Token/空间汇总只统计月包 2 和可用补充包，不叠加 scheduled 月包 1。

### 10.2 B 端企业已有等级 1 月包，再由管理员发放等级 2 月包

前提：

- 月包 1：B 端企业月包，等级 1，50 席，active。
- 月包 2：B 端企业月包，等级 2，50 席，由超管后台发放，`validFrom` 为空。

结果：

- `validFrom` 为空时使用当前业务日。
- 月包 2 等级更高，立即 active。
- 月包 1 企业锚点和所有成员 token/storage 子批次一起 scheduled。
- 成员管理、权益批次、工作台套餐记录均不能把月包 1 和月包 2 同时算作 active。
- B 端 token/空间补充包不属于月包队列，只要存在 active B 端月包且补充包未过期，仍可用。

### 10.3 同等级或低等级月包购买

前提：

- 当前 active 月包等级 2。
- 再购买等级 2 或等级 1 月包。

结果：

- 新月包不打断当前 active 月包。
- 新月包排到队列尾部，或排到更高等级 scheduled 月包之后。
- active 月包和其子批次周期不变。
- scheduled 月包尚未使用，保留完整 `periodDays`。

### 10.4 补充包依赖 active 月包

前提：

- C 端用户有 token 补充包，但月包过期。

结果：

- 补充包自身有效期继续倒计时。
- 没有 active 月包时，该补充包不能参与 token 消费。
- 用户重新获得 active 月包后，未过期补充包恢复可用。

### 10.5 空间展示不是批次扣费

前提：

- 用户有 1GB 月包空间 + 1GB 空间补充包。
- 工作台实际使用 19.7MB。

展示：

- 用户总空间：2GB，总剩余约 1.98GB。
- 月包空间批次：授权 1GB，已用 19.7MB，可用约 1004MB。
- 空间补充包批次：授权 1GB，已用 0，可用 1GB。

说明：空间不写 `capture/release` 批次流水；展示层按“月包优先、补充包其次”分摊实际 workspace usage。
## 2026-07-09 修订：月包安全修复后的 API 行为

### `/billing/plans` 前台套餐预览
- `enterpriseId` 现在为必填查询参数。
- C 端企业要求当前用户是该企业 active member。
- B 端企业要求当前用户是该企业 active owner/admin。
- 返回字段仅包含购买弹窗需要的展示字段：套餐 id/name/code、planType、价格、周期、等级、token/storage/memberLimit、active 状态、排序、displayConfig、featureConfig 等。
- 前台响应不再返回后台管理字段，例如企业 slug、后台 metadata、删除标记和创建/更新时间。
- `/admin/billing/plans` 保持后台完整字段不变。

### 订单发放与支付回调
- `grantStatus=SUCCESS` 的订单发放请求幂等返回既有发放结果。
- 只有 `PENDING` 和 `FAILED` 可以切换到 `PROCESSING` 并执行发放。
- `PROCESSING` 会返回冲突，调用方应稍后重试或等待对账任务补偿。
- 支付金额不一致时只记录回调信息，不发放权益。
- 微信支付成功但权益发放失败时返回失败语义，保留微信重试和后台对账补偿机会。
- 后台 `retryGrant` 和 `markPaidForAdmin` 走同一状态机，不能覆盖已成功发放订单。

### 数字字符串约束
- 金额/额度字符串统一要求 1 到 19 位正整数：`^[1-9]\d{0,18}$`。
- 适用字段包括企业分配/回收额度、批量赠送额度、套餐 token/storage 配置。
- `priceCents`、`periodDays`、`planLevel`、`memberLimit` 继续使用整数边界校验，并补充最大值保护。

### Storage quota
- storage 批次的 `remainingAmount` 不是实时剩余空间。
- 企业空间配置和成员空间列表以 active storage 授权总量为 quota 基数，再减 usage snapshot 得到展示剩余量。
- usage snapshot 缺失或不可用时返回 `usageAvailable=false`，不会展示为确定可用空间。
