# 批次与月包串行有效期排队模型

## Goal

将批次和月包的关系从"并行 + 优先级"改为**用户级串行排队**模型。monthly_plan anchor 批次即账号有效期权益，支持冻结/解冻操作，通过检查点门控控制 token/storage 权益的可用性。

## Background

企业配置按 token 批次模式后，管理员代码或用户自购发放月包。月包发放时包含三个权益项，默认有效期一致：
- **账号有效期**（monthly_plan anchor，串行排队生效）
- **Token 量**（自带有效期，重叠时叠加计算）
- **云盘空间容量**（自带有效期，重叠时叠加计算）

## Requirements

### N1: monthly_plan anchor 即账号有效期权益
席位月包 anchor 批次本身就是账号有效期权益（不新增 account_validity 类型）。前端在批次列表/详情页可见其发放记录，并支持冻结/解冻操作。

### N2: 账号有效期读取
读取当前 active 的 monthly_plan anchor 批次的 validFrom/validUntil 作为账号有效期。废弃 computeAccountValidity 的连续区间算法，简化为直接读 active 批次。排队场景下，当前生效的只有一个 active 批次（其他为 scheduled），排队的后续区间通过"月包状态"卡片（activeMonthlyPlans/scheduledMonthlyPlans）展示，不合并进 accountValidity。

### N3: 门控约束（检查点门控）
用户必须有**有效的 monthly_plan anchor**（status=active 且在有效期内），才能使用带 `dependencyPolicy: { requiresActiveMonthlyPlan: true }` 的 token/storage 批次。门控逻辑已有（`hasActiveMonthlyPlan` + `isUsableEntitlementBatch`），无需新增。

### N4: 冻结/解冻 monthly_plan anchor
- 手动冻结 monthly_plan anchor → status 改为 frozen
- 冻结后 `hasActiveMonthlyPlan` 返回 false（frozen 不在 `status: { in: ["active", "scheduled"] }` 查询范围）
- token/storage 批次的 `isUsableEntitlementBatch` 自动返回 false → 消费被拒绝
- 解冻 → status 回 active → 门控实时恢复，无需级联操作
- **不级联冻结** token/storage 批次，由检查点门控统一拦截
- **只冻结当前 active 批次**，scheduled 批次保持不变，到期自动生效
- 需放开 `freezeActivePoolBatch`/`unfreezePoolBatch` 对 `sourceType: "b2b_monthly_seat_plan"` + `poolModel === true` 的限制，支持 monthly_plan anchor

### N5: 账号失效引导策略
accountValidity 为 null 时（冻结/过期/未发放月包），前端按用户角色引导：
- **用户自购场景**：引导去套餐购买页
- **管理员代码场景**：管理员引导去 B 端套餐购买
- **其他成员**：提示"账号失效，联系管理员"

不区分冻结和过期，统一为 null + 引导。管理员要看冻结详情，去批次列表页看 frozen 状态的 monthly_plan 批次。

### N6: 用户侧展示（分层）
```
账号有效期：2026/07/14 - 2027/07/13（生效中）
├── Token：30 万（可用/已冻结）
├── 空间：10 GB（可用/已冻结）
└── 月包状态：生效 1 / 待生效 0 / 暂停 0
```
accountValidity 为 null 时，展示"账号失效" + 按角色引导（N5）。

### N8: Token 与空间容量批次共享有效期
Token 批次和空间容量批次共享相同的 `validFrom`/`validUntil`。空间容量值从现有配置读取（`memberDefaultStorageBytes` 或套餐配置中的 `storageBytes`），不需要在批次表中新增容量字段。两个批次独立创建，但有效期一致，门控逻辑统一。
- 顶部：分配统计（已分配/待分配）
- 中部：月包列表
- 底部：用户明细（可展开）

---

## 分阶段交付

### Phase 1：核心逻辑
- 账号有效期读取（简化为读 active 批次，废弃连续区间算法）
- 冻结/解冻 monthly_plan anchor（放开 API 限制）
- 检查点门控（已有，无需新增）
- 用户侧分层展示 + 账号失效引导
- 批次审计页面 summary 卡片（已有，验证 null 场景）

### Phase 2：完整功能
- 企业侧主月包查询页面
- 冻结/解冻自动化（主月包过期自动冻结、续期自动解冻）
- 用户明细展开

---

## Acceptance Criteria

### AC1: 账号有效期读取
- 有 active monthly_plan 批次时，`accountValidity` 返回该批次的 `{ validFrom, validUntil, status }`
- 无 active 批次（frozen/过期/未发放）时，`accountValidity` 返回 null
- 不合并 scheduled 批次日期

### AC2: 冻结 monthly_plan anchor
- 管理员可在批次列表/详情页对 monthly_plan anchor 执行冻结
- 冻结后 status = frozen，写入 ledger（changeType: "freeze"）
- 冻结后 `hasActiveMonthlyPlan` 返回 false
- 带 `requiresActiveMonthlyPlan` 的 token/storage 批次不可用（isUsableEntitlementBatch 返回 false）
- scheduled 批次不受影响，保持 scheduled 状态

### AC3: 解冻 monthly_plan anchor
- 管理员可对 frozen 的 monthly_plan anchor 执行解冻
- 解冻后 status = active，写入 ledger（changeType: "release"）
- 解冻后 `hasActiveMonthlyPlan` 重新返回 true
- token/storage 批次恢复可用

### AC4: 账号失效引导
- accountValidity = null 时，ZclawShell 侧栏展示"账号失效"
- 用户自购场景：展示"去购买套餐"链接
- 管理员代码场景：展示"联系管理员购买 B 端套餐"提示
- 其他成员：展示"账号失效，联系管理员"

### AC5: 批次审计页面
- summary 卡片显示 accountValidity（日期范围 + 状态标签）
- accountValidity = null 时显示"账号失效"
- monthly_plan anchor 在批次列表可见，可执行冻结/解冻

### AC6: 测试
- 现有 530 个测试不破坏
- 新增测试：冻结 monthly_plan → token/storage 不可用；解冻 → 恢复
- 新增测试：accountValidity 读取 active 批次；无 active 返回 null

---

## 已确认

| Q | 结论 |
|---|---|
| 账号有效期权益载体 | monthly_plan anchor 批次本身（不新增 account_validity 类型） |
| 前端可见发放记录 | 已有（列表页筛选 monthly_plan + 详情页 isB2bMonthlyAnchor 专门展示） |
| 冻结/解冻操作 | 需放开 freezeActivePoolBatch 对 sourceType/poolModel 的限制，支持 monthly_plan anchor |
| 门控机制 | 检查点门控（已有）：冻结 monthly_plan → hasActiveMonthlyPlan=false → token/storage 的 isUsableEntitlementBatch 返回 false |
| 门控生效路径 | hasActiveMonthlyPlan 查询 status: { in: ["active", "scheduled"] }，frozen 不在范围内，冻结后自动失效 |
| 账号有效期读取 | 只读 active 批次的 validFrom/validUntil，不合并 scheduled，废弃连续区间算法 |
| 排队后续信息 | 通过月包状态卡片（activeMonthlyPlans/scheduledMonthlyPlans）展示 |
| 解冻恢复 | 解冻后 status→active，门控实时计算自动恢复，无需级联操作 |
| 是否级联冻结 | 否，检查点门控替代级联冻结 |
| 冻结范围 | 只冻结当前 active 批次，scheduled 批次保持不变，到期自动生效 |
| 冻结后 accountValidity | 返回 null（不区分冻结/过期/未发放） |
| 账号失效引导 | 用户自购→购买页；管理员代码→B端套餐；其他成员→联系管理员 |
| 用户侧展示 | 分层展示 |
| 企业侧展示 | 混合视图（Phase 2） |
| 交付节奏 | 分阶段（Phase 1 核心 + Phase 2 完整） |

## Out of Scope（本次）

- 企业侧主月包查询页面（Phase 2）
- 冻结/解冻自动化（Phase 2）
- 历史数据迁移策略
