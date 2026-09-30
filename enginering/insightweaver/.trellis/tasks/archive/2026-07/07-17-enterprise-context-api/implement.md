# Implementation Plan: 扩展 getWorkspaceUsage 统一企业配置

## Checklist

### Step 1: 后端追加字段

**文件**: `apps/api/src/zclaw/zclaw.service.ts`
**位置**: `getWorkspaceUsageSummary` 方法 (line 1201)
**改动**:
1. 在 `return` 之前，查询 `enterprisePostExpiryPurchaseConfig` 获取 `postExpiryPurchaseMode`
2. 调用 `this.getMyEnterpriseTokenQuotaSummary(userId, enterpriseId)` 获取 `conversationQuotaSummary`
3. 追加到返回对象

**验证**: `pnpm lint` 通过

---

### Step 2: 前端类型追加字段

**文件**: `apps/web/src/api/moudles/zclaw.ts`
**位置**: `ZclawWorkspaceUsageResponse` 接口 (line 406)
**改动**: 追加 `postExpiryPurchaseMode` 和 `conversationQuotaSummary` 字段

**验证**: `tsc --noEmit` 通过

---

### Step 3: useZclawChat 移除独立调用

**文件**: `apps/web/src/hooks/useZclawChat.ts`
**位置**: line 268-299（postExpiryPurchaseMode state 和 useEffect）
**改动**:
1. 移除 `postExpiryPurchaseMode` state 和 ref
2. 移除 `getPostExpiryPurchaseConfigApi` 的 useEffect
3. 从 `workspaceUsage.postExpiryPurchaseMode` 派生 `postExpiryPurchaseMode`
4. 返回值中 `postExpiryPurchaseMode` 改为从 `workspaceUsage` 读取

**验证**: `tsc --noEmit` 通过

---

### Step 4: ZclawShell 移除独立调用

**文件**: `apps/web/src/components/zclaw/ZclawShell.tsx`
**位置**: 
- `loadIdentityMeta` (line 962-968): 移除 `getMyConversationQuotaApi` 调用
- `WorkspaceUserIdentity` useEffect (line 1010-1030): 移除 `getPostExpiryPurchaseConfigApi` 调用
- `ZclawShellContent` useEffect (line 1670-1699): 移除 `getPostExpiryPurchaseConfigApi` 调用

**改动**:
1. `legacyTokenQuota` 改从 `workspaceUsage.conversationQuotaSummary` 读取
2. `postExpiryPurchaseMode` 改从 `useZclawChatContext().workspaceUsage.postExpiryPurchaseMode` 读取
3. 移除 `setPostExpiryPurchaseMode` / `setSidebarPostExpiryPurchaseMode` state

**验证**: `tsc --noEmit` 通过

---

### Step 5: 验证

1. `pnpm --filter @insightweaver/api lint`
2. `pnpm --filter @insightweaver/web exec -- tsc --noEmit`
3. 手动测试：
   - 用户端首页不再出现 `post-expiry-purchase-config` 请求
   - 侧边栏 token/会话配额正常显示
   - 空间配额正常显示
   - 管理页面独立调用仍正常

---

## Risky Files

- `apps/api/src/zclaw/zclaw.service.ts` — 核心改动
- `apps/web/src/components/zclaw/ZclawShell.tsx` — 前端重构
- `apps/web/src/hooks/useZclawChat.ts` — 前端重构

## Rollback Points

- Step 1 可独立回滚：删除追加字段
- Step 3+4 可独立回滚：恢复独立调用
