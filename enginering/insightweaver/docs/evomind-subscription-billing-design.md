# EvoMind 月包、补充包与权益批次设计方案（当前实现版）

本文说明当前已经落地的月包体系底层逻辑。它替代旧 Phase 0-3 中以 B 端企业池为核心的设计描述。接口清单见 `docs/evomind-subscription-billing-api.md`。

## 1. 总体目标

- C/B 端都以企业身份作为系统承载对象。
- C 端权益归属 `enterpriseId + userId`。
- B 端月包按席位为成员生成可消费权益，不再使用企业 token/storage 总池作为主流程。
- B 端补充包先进入企业库存，分配给成员后才成为成员可消费批次。
- active 月包期间，旧默认配额、旧 token 批次、旧企业池分配不参与消费。
- 每次发放、冻结、实际扣费、释放、过期、分配都可追溯。

## 2. 数据模型与字段语义

### 2.1 BillingPlan

套餐配置表表达“可售卖或可后台发放的产品”。

关键字段：

| 字段 | 语义 |
| --- | --- |
| `enterpriseId` | 套餐所属企业。套餐只能在所属企业下购买/发放 |
| `planType` | 套餐类型，决定企业类型、主体和发放逻辑 |
| `priceCents` | 支付金额，单位分 |
| `periodDays` | 月包周期或补充包分配后的有效期天数 |
| `planLevel` | 月包等级，正整数；补充包为 0 或空 |
| `tokenAmount` | 每用户/每席 Token |
| `storageBytes` | 每用户/每席空间 |
| `memberLimit` | B 端月包席位数；B 端补充包库存席位数 |
| `requiresActiveMonthlyPlan` | 补充包是否依赖 active 月包 |
| `isActive` | 是否上架 |

套餐一旦产生订单、库存或权益批次，不允许原地改变会影响历史语义的字段，例如 `enterpriseId`、`planType`、主体类型。需要改变类型时必须新建套餐。

### 2.2 BillingOrder

套餐订单表表达“用户或企业管理员购买了一份套餐”。

关键规则：

- 创建订单时保存 `planSnapshot`。
- 支付成功后发放权益只读取 `planSnapshot`，不读取当前套餐可变配置。
- `paymentStatus` 和 `grantStatus` 分离。
- 支付成功但权益发放失败时，支付状态不回滚，后台可重试发放。

### 2.3 EntitlementBatch

权益批次表表达“某个主体在某段时间拥有一份权益”。

关键字段：

| 字段 | 语义 |
| --- | --- |
| `enterpriseId` | 所属企业 |
| `subjectType` | `enterprise` 或 `enterprise_user` |
| `userId` | `enterprise_user` 主体的用户 |
| `entitlementType` | `monthly_plan/token/storage/member/feature` |
| `sourceType` | 业务来源，必须保留真实 `planType` |
| `sourceRefType/sourceRefId` | 审计来源，如 `billing_order`、`admin_grant` |
| `planSnapshot` | 发放时的套餐快照 |
| `grantedAmount` | 授权额度 |
| `remainingAmount` | token 剩余或 storage 授权账面剩余；storage 业务展示另算 |
| `freezeAmount` | token 预占额度 |
| `validFrom/validUntil` | 有效期半开区间 |
| `status` | `active/scheduled/paused/expired/voided` |
| `metadata.grantGroupId` | 同一次月包发放的批次组 |

### 2.4 EntitlementLedger

权益流水表记录批次账务变化。

| changeType | 业务含义 |
| --- | --- |
| `grant` | 权益发放入账 |
| `allocate` | 权益分配 |
| `freeze` | AI 对话预占 |
| `capture` | AI 对话实际扣费 |
| `release` | 释放未使用预占 |
| `expire` | 过期 |
| `adjust` | 后台调整 |

用户侧 Token 明细只展示入账和真实出账，不展示 `freeze/release`。后台批次详情可以展示完整流水。

### 2.5 BillingTopupInventory / BillingTopupAssignment

B 端补充包库存模型：

- 企业购买或后台发放 B 端补充包后，先生成库存。
- 库存记录 `totalSeats/remainingSeats/amountPerSeat/periodDays`。
- 分配给成员时消耗 1 个库存席位，生成成员级 token 或 storage 批次。
- 分配记录写入 `BillingTopupAssignment`，用于追溯哪个库存分配给哪个成员。

### 2.6 BillingTask / BillingTaskEvent

计费任务模型表达“一次需要冻结和扣费的 AI 任务”。

关键字段：

| 字段 | 语义 |
| --- | --- |
| `enterpriseId` | 本次任务所属企业 |
| `userId` | 发起用户 |
| `subjectType` | 当前实现中 AI 任务使用 `enterprise_user` |
| `idempotencyKey` | 任务幂等键 |
| `fixedHoldTokens` | 发起前固定预冻结 Token，默认 100000 |
| `heldTokens` | 已冻结 Token |
| `capturedTokens` | 已确认扣费 Token |
| `releasedTokens` | 已释放冻结 Token |
| `billingUsageTokens` | 实际计费 usage |
| `billingOverrunTokens` | 实际 usage 超过预冻结后补扣仍不足的记录 |
| `status` | created/reserved/captured/released/failed 等任务状态 |

`BillingTaskEvent` 记录任务生命周期事件，用于后台排障。它不替代 `EntitlementLedger`；前者是任务事件，后者是批次余额账。

## 3. 企业类型和套餐类型边界

| 企业类型 | 支持套餐 | 不支持 |
| --- | --- | --- |
| `b2b` | B 端企业月包、B 端 token 补充包、B 端空间补充包 | C 端个人套餐 |
| `consumer` | C 端个人月包、C 端个人 token 补充包、C 端个人空间补充包 | B 端席位套餐、默认 quota 生效 |
| `evomind_consumer` | 同 C 端 | B 端席位套餐 |

C 端用户加入企业免审批，直接创建或复用 active `enterprise_user` 身份；disabled 身份不能被自动启用。

B 端成员状态：

- `active`：占席，可消费权益。
- `disabled`：占席，生成/保留权益，但不能消费。
- `pending/rejected/deleted`：不占用 active 消费能力。

## 4. 月包发放逻辑

### 4.1 grantGroupId

同一次月包发放会生成一组批次，使用同一个 `metadata.grantGroupId`：

- B 端月包：企业 `monthly_plan` 锚点 + 每个占席成员的 `token/storage/member/feature` 子批次。
- C 端月包：用户 `monthly_plan` 锚点 + 用户 `token/storage/feature` 子批次。

规则：月包锚点和同组子批次必须同周期、同状态。月包升级、顺延、过期、修复时必须移动整组，不能只移动锚点。

### 4.2 B 端月包发放

条件：

- 企业为 `b2b`。
- 主体为 `enterprise`。
- 套餐配置包含 `periodDays/memberLimit/tokenAmount/storageBytes/planLevel`。
- 当前 `active + disabled` 占席成员数不能超过 `memberLimit`。

结果：

- 创建企业级 `monthly_plan` 锚点。
- 为每个占席成员创建成员级 `token`、`storage` 等批次。
- disabled 成员也生成批次并占席，但消费时因为成员不是 active 会被拒绝。
- B 端 active 月包存在时，默认配额策略实际失效。

### 4.3 C 端月包发放

条件：

- 企业为 `consumer` 或 `evomind_consumer`。
- 主体为 `enterprise_user`。
- 用户必须属于该企业身份。

结果：

- 创建用户级 `monthly_plan` 锚点。
- 创建用户级 token/storage/feature 子批次。
- 同一 `enterpriseId + userId` 同一时间只能有一个 active 主月包。

### 4.4 后台发放与用户支付的差异

后台发放和用户支付最终都进入同一个 `grantPlan` 权益发放逻辑。

差异只在审计来源：

- 用户支付：`sourceRefType=billing_order`，`sourceRefId=orderId`。
- 后台发放：`sourceRefType=admin_grant` 或指定来源。

二者的 `sourceType` 都必须等于真实 `plan.planType`。例如后台给 C 端用户发放月包，批次 `sourceType` 仍是 `consumer_monthly_plan`，不能写成 `admin_grant`。

## 5. 月包队列与升级规则

月包队列按主体隔离：

- B 端：队列主体是企业月包锚点，`enterpriseId + subjectType=enterprise + userId=null`。
- C 端：队列主体是用户月包锚点，`enterpriseId + userId + subjectType=enterprise_user`。
- 不同企业、不同行为主体互不影响。

### 5.1 高等级月包立即生效

如果存在 active 月包，且新月包 `planLevel` 高于当前 active 月包：

1. 新月包从本次 `validFrom` 起立即 active。
2. 被打断的旧 active 月包整体排到新月包后。
3. 旧 active 月包只保留剩余周期，不重新赠送完整周期。
4. 旧月包同一 `grantGroupId` 下所有子批次一起移动。

例子：

- 月包 1：等级 1，`2026/07/08 - 2026/08/07`，已使用 1 天。
- `2026/07/09` 发放月包 2：等级 2，30 天。

结果：

- 月包 2：`2026/07/09 - 2026/08/08`，active。
- 月包 1：`2026/08/08 - 2026/09/06`，scheduled，只保留原剩余天数。
- 月包 1 的 token/storage/member/feature 子批次同样变为 `2026/08/08 - 2026/09/06`。

### 5.2 同等级或低等级月包不打断当前 active

如果新月包等级小于或等于当前 active 月包：

- 新月包排入 scheduled 队列。
- 当前 active 月包周期不变。
- 新月包保留完整 `periodDays`。
- 如果队列中已有更高等级 scheduled 月包，新月包排在更高等级后。

例子：

- 当前 active：等级 2，`2026/07/09 - 2026/08/08`。
- 再购买等级 1，30 天。

结果：

- 等级 2 保持 active。
- 等级 1 scheduled：从队列末尾开始，完整 30 天。

### 5.3 scheduled 月包没有被使用过

scheduled 月包尚未开始，所以重排时保留完整周期。只有被高等级月包打断的 active 月包才按剩余天数顺延。

### 5.4 来源不影响队列

队列规则不区分来源：

- 用户自己下单支付的月包。
- 超管后台发放的月包。
- 支付成功后重试发放生成的月包。

只要主体相同、`planType` 是月包，就进入同一队列，按 `planLevel` 和 `validFrom` 计算。

## 6. 补充包规则

### 6.1 C 端补充包

条件：

- 主体为 `enterprise_user`。
- 发放时必须存在 active C 端月包。
- token 补充包要求正数 `tokenAmount`。
- storage 补充包要求正数 `storageBytes`。

使用规则：

- active 月包存在时，未过期补充包可用。
- 月包过期后，补充包继续倒计时但暂停可用。
- 重新获得 active 月包后，未过期补充包恢复可用。
- 补充包不进入月包队列，不参与月包升级重排。

### 6.2 B 端补充包

发放结果不是直接给成员批次，而是企业库存：

- `b2b_token_topup` 生成 token 库存。
- `b2b_storage_topup` 生成空间库存。

分配规则：

- 分配时企业必须有 active B 端月包。
- 被分配用户必须是 active 成员。
- 每次分配消耗 1 个库存席位。
- 成员补充批次从分配当天起计算有效期。

### 6.3 补充包例子

例子 A：C 端用户月包 + token 补充包

- C 端月包：`2026/07/09 - 2026/08/08`。
- token 补充包：`2026/07/10 - 2026/10/18`。

`2026/07/10` 到 `2026/08/08`：月包和补充包均可用。

`2026/08/09` 月包过期后：补充包仍未过期，但暂停可用。

`2026/08/15` 用户重新获得月包：补充包恢复可用，直到自身过期。

例子 B：B 端企业购买 2 席 token 补充包

- 库存：`totalSeats=2`，`remainingSeats=2`。
- 分配给用户 A 后：库存 `remainingSeats=1`，用户 A 获得成员 token 批次。
- 只分配 1 席时，企业库存摘要应显示总库存 2、已分配 1、剩余 1。

## 7. Token 消费逻辑

### 7.1 对话扣费流程

AI 对话流式接口发起前：

1. 读取 `x-enterprise-id` 确定企业身份。
2. 判断该企业用户身份是否 active。
3. 按 `BILLING_AI_FIXED_HOLD_TOKENS` 预冻结，默认 100000。
4. 如果余额不足，拒绝启动对话。

对话结束：

- 有 usage：按真实 usage `capture`，多余冻结 `release`。
- 失败、取消、无 usage：释放全部冻结。

### 7.2 扣费优先级

active 月包存在时，C/B 端统一：

1. 月包批次优先。
2. 补充包其次。
3. 旧后台赠送或旧批次不参与 active 月包期间消费。

无 active 月包时：

- B 端：只有默认配额策略 effective 或旧手动批次可兜底。
- C 端：可用非套餐赠送批次可作为兜底；C 端补充包因为依赖月包而不可用。

capture 时也按相同优先级确认扣费，不能因为补充包更早过期就优先扣补充包。

例子：

- 用户有月包 token 10,000,000。
- 用户有 token 补充包 10,000，剩余 5,534。
- 对话实际消耗 4,466。

结果：先扣月包，补充包不应被扣；除非月包不足以覆盖实际消耗。

### 7.3 月包锚点防御

月包来源的成员 token/storage 子批次必须有 active 月包锚点支撑。

如果旧月包子批次因为历史脏数据仍是 active，但对应 `grantGroupId` 的月包锚点已 scheduled 或 expired，则：

- 不参与余额汇总。
- 不参与扣费。
- 不参与工作台可用余额。
- 修复脚本会把同组子批次周期和状态对齐到锚点。

## 8. 空间容量逻辑

空间不做 token 式 `freeze/capture/release` 批次扣费。

底层原则：

- `entitlement_batches.remainingAmount` 对 storage 更接近授权容量账面字段，不代表实时剩余空间。
- 真实已用空间来自工作台空间 usage snapshot。
- 业务展示的可用空间 = active storage 授权总量 - 实际已用空间。

### 8.1 多个 storage 批次展示分摊

同一用户有多个 active storage 批次时，展示按如下顺序分摊实际用量：

1. 月包空间。
2. 空间补充包。
3. 其他可用空间来源。

例子：

- 月包空间：1GB。
- 空间补充包：1GB。
- 实际工作台用量：19.7MB。

展示：

- 用户总空间：授权 2GB，已用 19.7MB，剩余约 1.98GB。
- 月包空间批次：授权 1GB，已用 19.7MB，可用约 1004MB。
- 空间补充包批次：授权 1GB，已用 0，可用 1GB。

如果实际用量为 1.2GB：

- 月包空间批次：已用 1GB，可用 0。
- 空间补充包批次：已用 0.2GB，可用约 0.8GB。

## 9. 默认配额和旧批次

默认配额策略只用于 B 端无 active 月包时的兜底。

上线同步时，普通存量企业统一按 B 端企业处理，默认成员配额策略自动开启，以保持旧线上成员默认配额行为不被月包迁移打断。固定 EvoMind C 端企业 `00000000-0000-0000-0000-000000000001` 保持 `evomind_consumer`，默认配额策略强制关闭且不能开启。

状态：

- `enabled`：策略开关是否打开；B 端同步回填默认打开，也可由超管后续调整。
- `effectiveEnabled`：当前是否实际生效。
- `blockedReason=active_b2b_monthly_plan`：超管打开了策略，但 B 端 active 月包存在，所以实际不生效。

active 月包期间：

- 成员默认配额页面配置区禁用。
- 成员默认个人空间容量列禁用。
- 旧 token override、旧 token 批次创建、更新、迁移、移动成员到旧批次等写操作被拒绝或前端禁用。
- 成员管理 token 详情只展示可消费口径的月包和补充包。

C 端企业：

- 永远不支持默认配额策略生效。
- C 端 active 月包期间同样不使用旧配额/旧批次作为优先消费来源。

## 10. 权益批次页面展示逻辑

### 10.1 只选企业

B 端企业：

- 顶部摘要展示企业拥有的套餐和库存概览。
- 月包数量只统计企业月包锚点，不统计成员级 token/storage 批次数。
- token/空间补充包展示库存：总库存、已分配、剩余、已生效、待生效。

C 端企业：

- 聚合该企业下用户拥有的 C 端套餐内容。
- 对象列为用户时优先展示手机号，其次姓名，再次 ID。

### 10.2 选企业 + 手机号

展示该用户自己的批次：

- 月包 token/storage。
- token/空间补充包。
- 非套餐赠送包。

B 端用户示例：

- 企业月包生成的成员 token 批次。
- 企业月包生成的成员 storage 批次。
- 分配给该用户的 B 端 token 补充包。
- 分配给该用户的 B 端空间补充包。

### 10.3 批次详情

详情页展示业务字段：

- 企业名称、企业类型。
- 用户手机号、真实姓名、部门、角色、状态。
- 套餐名、来源、有效期、状态。
- token 显示发放、剩余、冻结、已用。
- storage 显示授权、已用、可用。

流水标题使用业务文案，不展示裸 `freeze/capture/release` 枚举。

## 11. 用户侧工作台逻辑

### 11.1 购买入口

B 端：

- 只有当前企业 `owner/admin` 可见。
- 可购买 B 端企业月包、B 端 token 补充包、B 端空间补充包。
- 补充包购买后进入企业库存，不直接给购买人。

C 端：

- active 成员均可见。
- 可购买个人月包、个人 token 补充包、个人空间补充包。

### 11.2 头像余额

头像菜单 token 余额使用用户侧权益摘要接口，口径与成员管理一致：

- active 月包期间只统计月包和补充包。
- 不统计旧默认配额和旧批次。

### 11.3 权益明细弹窗

Token 明细：

- 展示 token 入账和实际扣费。
- 不展示预占和释放。
- 余额展示使用 `remaining + freeze` 的业务余额变化。

套餐记录：

- C 端展示购买或后台发放给自己的套餐记录。
- B 端展示分配到自己的企业月包权益和补充包权益。
- 同一次月包发放按 `grantGroupId` 聚合。

## 12. 过期与修复

### 12.1 过期处理

系统可通过手动接口或定时任务将到期批次过期：

- 批次状态变为 `expired`。
- 剩余额度归零。
- 写 `expire` 流水。

B 端月包过期后：

- B 端企业默认配额策略在迁移/同步时默认开启；但只在没有 active B 端月包时实际生效。
- 企业存在 active B 端月包时，默认配额策略即使开启也会被阻断。

### 12.2 月包组修复脚本

脚本：

```bash
pnpm --filter @insightweaver/api billing:repair-monthly-grant-groups
pnpm --filter @insightweaver/api billing:repair-monthly-grant-groups -- --apply
```

用途：

- 按 active/scheduled 月包锚点的 `grantGroupId` 对齐同组成员子批次周期和状态。
- 只修复 `b2b_enterprise_plan`、`consumer_monthly_plan` 月包来源。
- 不修改 token/空间补充包。
- 不重新推算旧 active 月包剩余周期。

## 13. 典型端到端场景

### 13.1 C 端用户自己购买月包

1. 工作台展示 C 端套餐。
2. 用户创建 `POST /api/billing/orders`。
3. 微信支付成功或 mock 支付成功。
4. 订单 `paymentStatus=SUCCESS`。
5. 系统按 `planSnapshot` 发放用户月包批次。
6. 订单 `grantStatus=SUCCESS`。
7. 头像余额刷新，Token 明细出现入账，套餐记录出现月包。

### 13.2 B 端管理员购买月包

1. 企业管理员创建 B 端月包订单。
2. 支付成功后生成企业月包锚点。
3. 系统为 active + disabled 占席成员生成成员 token/storage 批次。
4. active 成员可消费，disabled 成员不能消费。
5. 默认配额策略自动被 active B 端月包阻断。

### 13.3 B 端企业补充包购买和分配

1. 管理员购买 token 补充包，生成企业库存。
2. 权益批次只选企业时展示库存总量、已分配、剩余。
3. 管理员把库存分配给成员。
4. 成员获得 token 补充批次。
5. 对话扣费时先扣月包，月包不足再扣补充包。

### 13.4 套餐订单发放失败

1. 微信回调已确认支付成功。
2. 发放权益时因席位超限或数据异常失败。
3. 订单保持 `paymentStatus=SUCCESS`，`grantStatus=FAILED`。
4. 后台修复原因后调用 `retry-grant`。
5. 重试仍按订单快照发放。

## 14. 废弃能力

旧 B 端企业池模型不再作为月包 v2 主流程：

- 企业池 token/storage 父批次冻结。
- 企业池分配接口 `allocate/reclaim`。
- 企业池 summary 作为新页面主数据源。
- active 月包期间通过旧 token 批次或旧默认 quota 给成员配置可消费额度。

这些能力只能用于历史兼容、排障或迁移，不允许新功能继续依赖。
## 2026-07-09 修订：月包账务安全与并发约束

### 账务原子性与数据库约束
- `entitlement_batches` 的余额变更统一使用条件更新：冻结要求 `remainingAmount >= amount`，确认冻结要求 `freezeAmount >= amount`，直接扣减要求 `remainingAmount >= amount`，释放要求 `freezeAmount >= amount` 且 `remainingAmount + amount <= grantedAmount`。
- 新增数据库兜底约束：`grantedAmount >= 0`、`remainingAmount >= 0`、`freezeAmount >= 0`、`remainingAmount + freezeAmount <= grantedAmount`。
- 订单发放和 B2B 月包成员补发新增 partial unique index，避免并发回调、对账、审批或导入导致重复批次。
- B2B 补充包库存分配使用 `remainingSeats > 0` 条件更新扣减库存，最后一个 seat 并发分配只能成功一次。

### 订单发放状态机
- `fulfillPaidOrder` 只允许 `PENDING` 或 `FAILED` 进入 `PROCESSING`。
- `SUCCESS` 视为幂等完成，直接读取既有发放结果。
- `PROCESSING` 返回冲突，不能覆盖正在处理的发放。
- 成功/失败回写均要求当前仍为 `PROCESSING`，避免旧并发请求覆盖新状态。
- 微信支付成功但权益发放失败时返回失败语义，保留微信重试或对账补偿机会。

### B2B 席位与成员补发
- 审批、启用、导入激活成员时，同一企业 membership 集合在事务内加锁并重新计算 active/disabled 占用席位。
- `ensureB2BMonthlyEntitlementsForMember` 在事务内重查既有 token/storage 批次；遇到唯一冲突后读取既有批次并幂等返回。

### Storage quota 口径
- storage 批次的 `remainingAmount` 不再表示实时剩余空间。
- 实时可用空间按“active storage 授权总量 `grantedAmount` - workspace usage snapshot”计算。
- usage snapshot 缺失或不可用时，展示 `usageAvailable=false`，不把 missing snapshot 当成已用 0 的确定事实。
