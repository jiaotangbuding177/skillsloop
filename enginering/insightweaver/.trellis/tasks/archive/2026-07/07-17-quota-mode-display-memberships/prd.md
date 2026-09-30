# enterprise-memberships页面按配额模式显示对应消耗/限额数据

## Goal

`admin/enterprise-memberships` 列表页的"消耗/限额"列和点击后的详情页，根据企业当前配额模式显示对应的数据，所有模式的显示格式配套统一。

## Background

### 当前行为

**列表页** `MemberTokenUsageCell`（`enterprise-memberships/page.tsx:1700-1823`）：
- 列头 `consumptionLimit` = "消耗 / 限额"（已通用）
- conversation 模式 → 显示 "—"（问题：应有数据可显示）
- token 模式 → 显示 token used / token limit
- batch 模式 → 显示批次状态（过期/耗尽/正常）
- unlimited 模式 → 显示 "—"（正确，无配额限制）

**详情页** `[membershipId]/page.tsx`：
- 页面标题 `tokenUsageTitle` = "Token消耗详情"（conversation 模式下不合适）
- `MonthlyQuotaSection`（line 88-222）：只处理 token 模式，conversation 模式显示 "tokenNotEnabled"
- `TokenUsageTrendSection`（line 368-374）：token 使用趋势图，所有模式都显示

### 数据结构

`EnterpriseConversationQuotaMemberRow`（`zclaw.ts:1120-1152`）已有字段：

**会话相关**（conversation 模式）：
- `remainingConversations` — 剩余会话次数
- `effectiveLimit` — 有效会话限额
- `limitSnapshot` — 会话限额快照
- `enterpriseConversationLimit` — 企业会话限额
- `isQuotaExempt` — 是否免配额

**Token 相关**（token 模式）：
- `tokenUsed` — token 使用量
- `effectiveTokenLimit` — 有效 token 限额
- `tokenEntitlements` — token 权益明细

**批次相关**（batch 模式）：
- `batchQuota` — 批次配额摘要

**模式字段**：
- `enterpriseQuotaMode` — 企业配额模式

### 计算公式

- 会话消耗 = `effectiveLimit - remainingConversations`（当 `effectiveLimit` 和 `remainingConversations` 都不为 null 时）
- 会话限额 = `effectiveLimit`
- token 消耗 = `tokenUsed`（或 `sumTokenEntitlementAmount(tokenEntitlements, 'usedAmount')`）
- token 限额 = `effectiveTokenLimit`（或 `sumTokenEntitlementAmount(tokenEntitlements, 'grantedAmount')`）

## Requirements

- R1: 列表页 conversation 模式下，"消耗/限额"列显示会话消耗/限额，格式与 token 模式配套（used / limit）
- R2: 列表页 token 模式下，保持现有逻辑不变
- R3: 列表页 batch 模式下，保持现有逻辑不变
- R4: 列表页 unlimited 模式下，显示 "—"（正确，不变）
- R5: 详情页 conversation 模式下，`MonthlyQuotaSection` 显示会话用量详情（消耗/限额 + 进度条），格式与 token 模式配套
- R6: 详情页 token 模式下，保持现有逻辑不变
- R7: 详情页 batch 模式下，保持现有逻辑不变
- R8: 详情页页面标题根据配额模式调整（conversation 模式不显示"Token消耗详情"）
- R9: 详情页 `TokenUsageTrendSection`（token 趋势图）在所有模式下保留（token 是底层消耗单位，会话模式下也有 token 消耗）
- R10: 点击列表页单元格仍可跳转到详情页

## Acceptance Criteria

- [ ] AC1: conversation 模式下，列表页"消耗/限额"列显示"会话消耗 / 会话限额"（如 35 / 100）
- [ ] AC2: conversation 模式下，`isQuotaExempt` 时显示"消耗 / ∞"
- [ ] AC3: conversation 模式下，`effectiveLimit` 为 null 时显示"消耗 / 未配置"
- [ ] AC4: conversation 模式下，详情页 `MonthlyQuotaSection` 显示会话用量（消耗/限额 + 进度条）
- [ ] AC5: conversation 模式下，详情页标题不显示"Token消耗详情"，改为通用标题（如"用量详情"）
- [ ] AC6: token 模式下，列表页和详情页显示不变
- [ ] AC7: batch 模式下，列表页和详情页显示不变
- [ ] AC8: 详情页 token 趋势图在所有模式下保留
- [ ] AC9: 列表页点击单元格可跳转到详情页

## Out of Scope

- 后端 API 改动（数据已有，只是前端没展示）
- 配额模式切换 UI（已在父任务完成）
- 会话使用趋势图（后端无"每日会话使用量"API，只保留 token 趋势图）

## Technical Notes

### 涉及文件

1. `apps/web/src/app/[locale]/(zclaw-shell)/admin/enterprise-memberships/page.tsx`
   - `MemberTokenUsageCell` 组件 (line 1700-1823)：添加 conversation 模式分支，显示会话消耗/限额

2. `apps/web/src/app/[locale]/(zclaw-shell)/admin/enterprise-memberships/[membershipId]/page.tsx`
   - `MonthlyQuotaSection` 组件 (line 88-222)：添加 conversation 模式分支，显示会话用量 + 进度条
   - 页面标题 (line 340)：根据配额模式动态显示

3. `apps/web/messages/zh.json` + `en.json`
   - 新增 conversation 模式相关文案（如"用量详情"标题、"会话消耗/限额"标签）
   - 现有 `tokenNotEnabled` 文案调整或新增 conversation 模式专用文案

### 改动思路

**列表页 `MemberTokenUsageCell`**：
在现有 `enterpriseQuotaMode !== 'token' && enterpriseQuotaMode !== 'batch' && !hasTokenEntitlements` 判断之前，增加 conversation 模式分支：
```typescript
if (enterpriseQuotaMode === 'conversation') {
  const conversationLimit = quotaRow.effectiveLimit;
  const remaining = quotaRow.remainingConversations;
  const used = conversationLimit != null && remaining != null
    ? conversationLimit - remaining : null;
  // 显示 used / limit，格式与 token 模式一致
}
```

**详情页 `MonthlyQuotaSection`**：
在现有 `enterpriseMode !== 'token' && !hasTokenEntitlements` 判断之前，增加 conversation 模式分支：
- 计算会话消耗/限额
- 显示进度条（复用 `TokenUsageProgressBar`）
- 标题用通用文案（如"用量 / 限额"）

**详情页标题**：
```typescript
const titleKey = enterpriseMode === 'conversation' ? 'usageDetail' : 'tokenUsageTitle';
```

## Open Questions

无
