# 统一企业账户配置：扩展 getWorkspaceUsage 响应

## Goal

在现有 `GET /api/zclaw/workspace/usage` 响应中追加 `postExpiryPurchaseMode` 和 `conversationQuotaSummary` 字段，前端移除 5 处独立的 `getPostExpiryPurchaseConfigApi` 调用，统一从 `useZclawChatContext` 读取。

## Background

### 当前问题

- `postExpiryPurchaseMode` 在前端 5 处独立获取（`ZclawShell` x2、`ZclawWorkspaceSidebar`、`useZclawChat`、`SuperLobsterPage`）
- `getMyConversationQuotaApi` 在 `ZclawShell.loadIdentityMeta` 独立获取
- `useZclawChat` 已经有 `postExpiryPurchaseMode` state 但其他组件不复用

### 现有接口

`GET /api/zclaw/workspace/usage` → `getWorkspaceUsageSummary` 已返回：
- `quotaMode`、`effectiveQuotaBytes`、`remainingBytes`、`usageBytes`
- `entitlementExpiredReason`、`hasActiveMonthlyPlan`、`quotaSource`

追加字段后，前端只需一次调用即可获得全部配置。

## Requirements

- R1: `getWorkspaceUsageSummary` 响应追加 `postExpiryPurchaseMode` 字段
- R2: `getWorkspaceUsageSummary` 响应追加 `conversationQuotaSummary` 字段（复用 `getMyEnterpriseTokenQuotaSummary` 逻辑）
- R3: 所有活跃成员可读（不限制 admin/owner）
- R4: 前端移除 `ZclawShell` 中 2 处 `getPostExpiryPurchaseConfigApi` 调用
- R5: 前端移除 `ZclawWorkspaceSidebar` 中 `getPostExpiryPurchaseConfigApi` 调用
- R6: 前端移除 `SuperLobsterPage` 中 `getPostExpiryPurchaseConfigApi` 调用
- R7: `useZclawChat` 中的 `getPostExpiryPurchaseConfigApi` 改为从 `workspaceUsage` 读取
- R8: `ZclawShell.loadIdentityMeta` 中的 `getMyConversationQuotaApi` 改为从 `workspaceUsage` 读取
- R9: 管理页面（conversation-quota/page.tsx）保留独立调用

## Acceptance Criteria

- [ ] AC1: `GET /api/zclaw/workspace/usage` 响应包含 `postExpiryPurchaseMode`
- [ ] AC2: `GET /api/zclaw/workspace/usage` 响应包含 `conversationQuotaSummary`
- [ ] AC3: 普通成员调用不报 403
- [ ] AC4: 前端不再有独立的 `getPostExpiryPurchaseConfigApi` 调用（管理页面除外）
- [ ] AC5: 用户端首页不再出现 `post-expiry-purchase-config` 请求

## Out of Scope

- 管理页面的独立 API 调用（保留）
- 数据库 schema 变更
- 新建独立接口

## Technical Notes

### 后端改动

`getWorkspaceUsageSummary`（`zclaw.service.ts:1201`）：
1. 获取 `postExpiryPurchaseMode`：查询 `enterprisePostExpiryPurchaseConfig` 表
2. 获取 `conversationQuotaSummary`：调用 `getMyEnterpriseTokenQuotaSummary`
3. 追加到响应对象

### 前端改动

`ZclawWorkspaceUsageResponse` 类型追加字段：
```typescript
postExpiryPurchaseMode?: 'contact_admin' | 'admin_purchase' | 'self_purchase' | null;
conversationQuotaSummary?: ZclawMyEnterpriseTokenQuotaSummary | null;
```

各组件改为从 `useZclawChatContext().workspaceUsage` 读取。

## Open Questions

无
