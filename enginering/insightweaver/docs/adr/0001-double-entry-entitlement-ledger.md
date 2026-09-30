# 权益系统采用双分录账本模式

权益（token、存储）的余额变动需要完整的审计追踪能力。我们选择了双分录账本模式：每个 `EntitlementBatch` 持有实时余额（`remainingAmount` + `freezeAmount`），每个变动同时在 `EntitlementLedger` 中记录 before/after 快照。

选择此模式因为权益涉及真实货币价值（用户付费购买），需要可审计、可重建的余额历史。简单地在批次上更新 `remainingAmount` 无法回答"这个用户的 token 是什么时候被谁消耗的"这类问题。

**Considered Options:**
- 仅维护实时余额（简单但不审计）：被否决，因为 token 消费需要溯源到具体的 `BillingTask`
- 事件溯源（所有状态从事件重建）：被否决，因为查询性能不可接受（余额查询需要扫描全量事件流）
- 当前方案（余额 + 事件日志双写）：兼顾查询性能和审计能力

**Consequences:**
- 每次余额变动必须同时写两条记录（批次更新 + 账本条目），需要事务保证
- 账本条目的 `idempotencyKey` 防止重复记录，与批次的幂等性机制联动
- `consumedAmount` 是隐式的（= granted - remaining - freeze），未在 schema 中存储。如果未来需要显式存储，需要在账本中增加累计消费字段
