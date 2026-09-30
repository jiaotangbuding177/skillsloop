# Design: 扩展 getWorkspaceUsage 统一企业配置

## Architecture

### 改动边界

修改 4 个文件：
- `apps/api/src/zclaw/zclaw.service.ts` — `getWorkspaceUsageSummary` 追加字段
- `apps/web/src/api/moudles/zclaw.ts` — `ZclawWorkspaceUsageResponse` 类型追加字段
- `apps/web/src/components/zclaw/ZclawShell.tsx` — 移除独立调用，从 context 读取
- `apps/web/src/hooks/useZclawChat.ts` — 移除独立调用，从 workspaceUsage 读取

不涉及：
- 数据库 schema
- 新建接口
- `ZclawWorkspaceSidebar.tsx` 和 `SuperLobsterPage.tsx` 已经从 `useZclawChatContext` 读取 `postExpiryPurchaseMode`，无需改动

### 数据流

```
用户打开 Shell
    ↓
useZclawChat.bootstrap()
    ↓
getWorkspaceUsageApi()  ← 一次调用
    ↓
返回 { quotaMode, effectiveQuotaBytes, ..., postExpiryPurchaseMode, conversationQuotaSummary }
    ↓
useZclawChatContext().workspaceUsage  ← 全局共享
    ↓
各组件直接读取，不再独立调用
```

## Contracts

### 追加的响应字段

```typescript
// ZclawWorkspaceUsageResponse 追加
postExpiryPurchaseMode?: 'contact_admin' | 'admin_purchase' | 'self_purchase' | null;
conversationQuotaSummary?: ZclawMyEnterpriseTokenQuotaSummary | null;
```

### 后端 getWorkspaceUsageSummary 追加逻辑

```typescript
async getWorkspaceUsageSummary(userId: string) {
  const context = this.getScopeContext();
  // ... 现有逻辑 ...

  // 追加：post-expiry purchase mode
  let postExpiryPurchaseMode: string | null = null;
  if (context.scope === ZCLAW_SCOPE_ENTERPRISE && context.enterpriseId) {
    const postExpiryConfig = await this.prisma.enterprisePostExpiryPurchaseConfig.findUnique({
      where: { enterpriseId: context.enterpriseId },
      select: { mode: true },
    });
    postExpiryPurchaseMode = postExpiryConfig?.mode ?? 'contact_admin';
  }

  // 追加：conversation quota summary
  let conversationQuotaSummary = null;
  if (context.scope === ZCLAW_SCOPE_ENTERPRISE && context.enterpriseId) {
    conversationQuotaSummary = await this.getMyEnterpriseTokenQuotaSummary(
      userId,
      context.enterpriseId,
    );
  }

  return {
    // ... 现有字段 ...
    postExpiryPurchaseMode,
    conversationQuotaSummary,
  };
}
```

### 前端改动

**ZclawShell.tsx**:
- `loadIdentityMeta`：移除 `getMyConversationQuotaApi()` 调用，改从 `workspaceUsage.conversationQuotaSummary` 读取
- `WorkspaceUserIdentity`：移除 `getPostExpiryPurchaseConfigApi` 调用，`postExpiryPurchaseMode` 从 props 传入
- `ZclawShellContent`：移除 `getPostExpiryPurchaseConfigApi` 调用，从 `useZclawChatContext().workspaceUsage.postExpiryPurchaseMode` 读取

**useZclawChat.ts**:
- 移除 `getPostExpiryPurchaseConfigApi` 调用和 `postExpiryPurchaseMode` state
- 从 `workspaceUsage.postExpiryPurchaseMode` 读取

## Compatibility

- 向后兼容：追加字段，不删除现有字段
- 前端旧代码不受影响（可选字段）
- 无 API 变更（同一接口，追加响应字段）

## Rollback

如需回滚：
1. 后端删除追加的 2 个字段
2. 前端恢复独立调用
