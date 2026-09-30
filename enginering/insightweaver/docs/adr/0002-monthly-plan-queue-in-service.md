# 月计划排队机制嵌入 EntitlementService

月计划的排队（新方案在当前方案到期后自动生效、升级立即生效并按比例调整）逻辑直接实现在 `EntitlementService` 内部，而非引入独立的 `Subscription` 或 `SubscriptionQueue` 实体。

选择嵌入式方案因为当前业务场景中"订阅"就是一次性的月计划购买，不需要 SaaS 行业典型的自动续费、升降级历史追踪等复杂订阅语义。引入独立实体会增加不必要的概念负担。

**Considered Options:**
- 独立 `Subscription` 实体 + 队列管理：被否决，因为当前业务不需要自动续费、订阅状态机、pro-ration 历史等完整 SaaS 订阅能力
- 当前方案（在 EntitlementBatch 上用 `validFrom`/`validUntil` + `grantGroupId` 编排队列）：复用已有的时间窗口机制，无需新实体

**Consequences:**
- 排队逻辑分散在 `grantConsumerMonthlyPlan`、`grantEnterprisePlan`、`recalculateQueuePeriods` 等多个方法中（~500 行），增加了 `EntitlementService` 的复杂度
- `grantGroupId` 将同一次 grant 创建的所有批次关联，是队列重算的关键
- 升级的"按比例调整"通过修改当前方案的 `validUntil` 和新方案的 `validFrom` 实现，没有单独的 pro-ration 记录
- 如果未来引入自动续费或多方案并行，此决策需要重新评估
