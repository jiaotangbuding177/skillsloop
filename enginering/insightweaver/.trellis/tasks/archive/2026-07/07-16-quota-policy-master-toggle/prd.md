# Master Quota Policy Toggle for Enterprises（企业配额总开关 / unlimited 模式）

## Goal

企业管理员关闭「启用成员配额限制」开关（`enterpriseDefaultQuotaPolicy.enabled = false`）时，企业进入 unlimited 模式（`quotaMode = "unlimited"`）：所有配额强制检查（账户有效期、Token 限额、存储容量、对话次数）全部跳过，发消息不被拦截，前端隐藏所有配额相关 UI。重新打开开关时恢复受限模式（默认 batch，可再手动调整）。

## Background

- `quotaMode` 存于 `ZclawEnterpriseConversationQuotaConfig`（4 值：conversation / token / batch / unlimited；`packages/db/prisma/schema.prisma:580`）。
- 前端改版后，配额模式单选按钮已移除 "unlimited" 选项（`QuotaModeRadioGroup.tsx` 仅剩 对话次数/按月 Token/按批次 Token）。企业进入 unlimited 的**唯一入口**是 conversation-quota 页的「启用成员配额限制」开关（`QuotaPolicyCard.tsx:63`）。
- 开关原本只写 `enterpriseDefaultQuotaPolicy.enabled`，与 `quotaMode` 完全脱钩 → 关闭开关不生效（2026-07-16 用户 cf6cdf46 排障确认：`enabled=false` 但 `quotaMode='batch'`，发消息仍报「Token 额度已用尽」）。
- **原 PRD 断言证伪**：原文声称 "Token quota / Conversation count 已支持 unlimited"。实际上两者只对 `tokenLimit / conversationLimit == null` 放行，**不识别 `quotaMode='unlimited'`**；发消息路径被 `assertEnterpriseTokenQuotaIfNeeded` 落入 legacy `assertTokenQuotaAvailable` 拦截。
- 遗漏根因模式：全代码库的 quotaMode 分支形如 `if (batch) {...} else { legacy 检查 }`，缺 `if (unlimited) return` —— 所有遗漏点均属此模式。

## 配额强制/展示点全量清单（2026-07-16 排障后修订）

### A. 强制闸门（会拦截用户操作）

| ID | 位置 | 触发场景 | 状态 |
|----|------|---------|------|
| E1 | `assertEnterpriseTokenQuotaIfNeeded` `zclaw.service.ts:2346` | 发消息（stream/send）Token 闸门——用户实际报错源 | ✅ 已修，未提交 |
| E2 | `consumeEnterpriseConversationQuotaIfNeeded` `zclaw.service.ts:7179`（throw `ZclawConversationQuotaExceededError` at 7307） | 发消息对话次数扣减；只查 `conversationLimit==null`，不查 quotaMode | ❌ **G1 待修** |
| E3 | `assertWorkspaceConversationAllowed` / `assertWorkspaceWriteAllowed` `zclaw.service.ts:12514/12532` | 工作区容量闸门 | ✅ 经 `getEnterpriseWorkspaceQuotaConfig`（:12234，返回 MAX_SAFE_INTEGER）间接覆盖，bf69643d |
| E4 | N3 topup 有效期闸门 `resolveConsumableBatchesInternal` `entitlement.service.ts` | 消费批次筛选 | ✅ bf69643d |
| E5 | `settleEnterpriseTokenUsageIfNeeded` `zclaw.service.ts:2380` | 消息完成后 Token 结算 | ✅ **决策：保留结算，无需改码**。已验证 legacy settle（`enterprise-token-quota.service.ts:102`）无 tokenLimit 时静默返回、有残留时幂等记账，全程不抛拦截性异常 |

### B. 状态/展示 API（决定前端显示什么）

| ID | 位置 | 前端消费方 | 状态 |
|----|------|-----------|------|
| D1 | `getWorkspaceUsageSummary` `zclaw.service.ts:1246`（含 `checkTokenQuotaStatus` :2245） | 输入框告警、容量条（`workspaceUsage`，含 `quotaMode` 字段） | ✅ bf69643d + checkTokenQuotaStatus 未提交 |
| D2 | `getSummary` accountValidity（N6）`entitlement.service.ts:851` | 侧边栏「有效期」（`entitlementSummary`） | ✅ 2cd69048 |
| D3 | `getSummary` availableTokens | 侧边栏「可用 Token」——unlimited 下仍返回 0 | ❌ **G4 待修（前端隐藏）** |
| D4 | `getMyEnterpriseTokenQuotaSummary` `zclaw.service.ts:7311` | 侧边栏 `legacyTokenQuota` 兜底数据源 | ❌ **G2 待修** |

### C. 模式写入路径（unlimited 如何进入/退出/防篡改）

| ID | 位置 | 行为 | 状态 |
|----|------|------|------|
| W1 | `DefaultQuotaPolicyService.updatePolicy` `default-quota-policy.service.ts:49` | 开关联动（用户决策：方案 A）：关→`quotaMode='unlimited'`，开→`'batch'`；与 policy、auditLog 同事务 | ✅ 已修，未提交 |
| W2 | `saveEnterpriseConversationQuotaForAdmin` `zclaw.service.ts:2500` | 策略禁用期间强制 `quotaMode='unlimited'`，防 admin 保存覆盖 | ✅ 已修，未提交 |

## Requirements

- **R1 发消息全链路放行**：unlimited 下 E1、E2 直接 return，消息流（`/api/zclaw/chat/message/stream`）不得出现任何配额类 error event。
- **R2 展示 API 一致性**：unlimited 下 D1 返回 `quotaMode='unlimited'` + 全部配额状态为"可用/无告警"；D2 `accountValidity=null`；D4 返回 null（不提供 legacy 配额摘要）。
- **R3 开关联动**：关闭开关 → `quotaMode='unlimited'`；打开 → `'batch'`（默认，管理员可再手动改 token/conversation）。写入必须在同一事务（policy + quotaConfig + auditLog）。
- **R4 防覆盖**：策略禁用期间，任何 admin 配额保存路径不得将 quotaMode 改离 unlimited。
- **R5 前端隐藏**：unlimited 下侧边栏（有效期、可用 Token、容量条）与输入框告警全部隐藏；统一以 `workspaceUsage.quotaMode === 'unlimited'` 为判断源（context 中已有，无需新请求）。
- **R6 结算行为（已决策：保留）**：unlimited 期间消息 Token 结算保持现状——legacy settle 在 `tokenLimit` 为 null 时天然静默返回（`enterprise-token-quota.service.ts:102-104`），有残留 tokenLimit 时继续幂等记账（settlement 唯一键防重，:118-134），不产生拦截。切回受限模式时历史用量占额是接受的行为。

## Acceptance Criteria

### 后端
- [ ] unlimited 企业发消息成功，SSE 无 `Token 额度已用尽` / `ZclawConversationQuotaExceededError`（R1，E1+E2）
- [ ] unlimited 且 `conversationLimit` 有残留值时，发消息不扣减对话次数（R1，E2 回归）
- [ ] `GET /api/zclaw/workspace/usage` 返回 `quotaMode='unlimited'`、`accountValidityExpired=false`、`tokenQuotaExpiredMessage=null`、`isOverLimit=false`（R2，D1）
- [ ] `GET /api/billing/entitlements/summary` 返回 `accountValidity=null`（R2，D2）
- [ ] `getMyEnterpriseTokenQuotaSummary` unlimited 时返回 null（R2，D4）
- [ ] 关闭开关后 DB 中 `quotaMode='unlimited'`；打开后为 `'batch'`；auditLog 有记录（R3）
- [ ] 策略禁用期间调用 admin 配额保存 API，quotaMode 仍为 unlimited（R4）

### 前端
- [ ] 侧边栏不显示「有效期」「可用 Token」「容量条」（R5）
- [ ] 输入框无有效期/容量/Token 告警（R5）
- [ ] 开关状态与后端 policy.enabled 一致（刷新后不漂移）

### 测试证据（已落）
- `zclaw.service.test.ts`：unlimited bypasses quota checks ✅
- `entitlement.service.test.ts`：N3 spy ×2、getSummary unlimited accountValidity=null ✅
- `default-quota-policy.service.test.ts`：联动 ×2（off→unlimited / on→batch）✅

## Out of Scope

- 恢复配额模式单选按钮的 "unlimited" 选项（决策：不恢复，开关是唯一入口）
- 计费/支付流程修改
- `freezeAccountPackages`（`entitlement.service.ts:1665`，refType=`account_validity_expired`）：src 内无调用方，冻结语义另行确认，不阻塞本任务

## Open Questions

无——G3 已决策（保留结算，见 R6）。

## Technical Notes（勘误）

- `computeAccountValidity` 实际位于 `enterprise-token-batch-quota.service.ts:984`（原 PRD 误写为 zclaw.service.ts）。
- unlimited 的实现约定为 **skip-in-caller**（编排层跳过，不改纯计算函数）——已录入 `.trellis/spec/api/service-patterns.md:345`。
- 测试 mock 同步 gotcha 已录入 `.trellis/spec/api/testing.md:94`。
