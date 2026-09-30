# Technical Design: Master Quota Policy Toggle

## Architecture Overview

When `quotaMode = "unlimited"`, the system bypasses all quota enforcement at the service layer, allowing existing business logic to treat the enterprise as having unlimited resources.

## Data Flow

```
Admin sets quotaMode = "unlimited"
           ↓
Database: ZclawEnterpriseConversationQuotaConfig.quotaMode
           ↓
Service Layer: Check quotaMode in quota enforcement functions
           ↓
┌─────────────────────────────────────────────┐
│ computeAccountValidity()                    │
│   → Returns null (no validity constraint)   │
├─────────────────────────────────────────────┤
│ getWorkspaceQuotaConfig()                   │
│   → Returns quotaBytes = MAX_SAFE_INTEGER   │
└─────────────────────────────────────────────┘
           ↓
Upper Layer: Treats as unlimited (no changes needed)
           ↓
Frontend: Hides quota UI based on quotaMode flag
```

## Backend Changes

### 1. computeAccountValidity() - `apps/api/src/zclaw/zclaw.service.ts`

**Current behavior:**
- Always calculates account validity based on entitlement batches
- Returns `null` only when no valid batches exist

**New behavior:**
```typescript
async computeAccountValidity(enterpriseId: string, userId: string) {
  // Add this check at the beginning
  const quotaConfig = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
    where: { enterpriseId },
    select: { quotaMode: true },
  });
  
  if (quotaConfig?.quotaMode === 'unlimited') {
    return null; // No validity constraint
  }
  
  // ... existing logic
}
```

**Impact:**
- `getWorkspaceUsageSummary()` will set `accountValidityExpired = false`
- All downstream checks pass naturally

### 2. getWorkspaceQuotaConfig() - `apps/api/src/zclaw/zclaw.service.ts`

**Current behavior:**
- Always returns actual quota configuration from database
- Uses default quota if no config exists

**New behavior:**
```typescript
async getWorkspaceQuotaConfig(enterpriseId: string, userId: string) {
  // Add this check at the beginning
  const quotaConfig = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
    where: { enterpriseId },
    select: { quotaMode: true },
  });
  
  if (quotaConfig?.quotaMode === 'unlimited') {
    return {
      quotaBytes: BigInt(Number.MAX_SAFE_INTEGER),
      quotaSource: 'unlimited',
      accountValidityExpired: false,
    };
  }
  
  // ... existing logic
}
```

**Impact:**
- `getWorkspaceUsageSummary()` will calculate `isOverLimit = false`
- `workspaceLimitReached` will be `false`

### 3. getWorkspaceQuotaLimitText() - API Response

**Current response:**
```typescript
{
  usageBytes: number,
  quotaBytes: number,
  effectiveQuotaBytes: number,
  remainingBytes: number,
  fileCount: number,
  directoryCount: number,
  isOverLimit: boolean,
  accountValidityExpired: boolean,
  accountValidityExpiredMessage: string | null
}
```

**New response:**
```typescript
{
  usageBytes: number,
  quotaBytes: number,
  effectiveQuotaBytes: number,
  remainingBytes: number,
  fileCount: number,
  directoryCount: number,
  isOverLimit: boolean,
  accountValidityExpired: boolean,
  accountValidityExpiredMessage: string | null,
  quotaMode: 'conversation' | 'token' | 'batch' | 'unlimited' // Add this field
}
```

**Impact:**
- Frontend can check `quotaMode` to conditionally render quota UI

## Frontend Changes

### 1. SuperLobsterPage.tsx - Chat Input Warnings

**Current behavior:**
- Shows account validity warnings when `accountValidityExpired = true`
- Shows storage capacity warnings when `isOverLimit = true`

**New behavior:**
```typescript
// Add quotaMode check before showing warnings
if (quotaConfig?.quotaMode === 'unlimited') {
  // Don't show any quota warnings
  return null;
}

// Existing warning logic
if (accountValidityExpired) {
  return <AccountValidityWarning />;
}
if (isOverLimit) {
  return <StorageCapacityWarning />;
}
```

### 2. ZclawShell.tsx - Sidebar Quota Displays

**Current behavior:**
- Always shows storage capacity bar in sidebar
- Always shows account validity indicator

**New behavior:**
```typescript
// Hide quota displays when unlimited
if (quotaConfig?.quotaMode === 'unlimited') {
  // Don't render quota-related components
  return <SidebarWithoutQuota />;
}

// Existing quota UI
return <SidebarWithQuota />;
```

### 3. API Type Definitions - `apps/web/src/api/moudles/zclaw.ts`

**Add quotaMode to response type:**
```typescript
export interface WorkspaceQuotaLimitTextResponse {
  usageBytes: number;
  quotaBytes: number;
  effectiveQuotaBytes: number;
  remainingBytes: number;
  fileCount: number;
  directoryCount: number;
  isOverLimit: boolean;
  accountValidityExpired: boolean;
  accountValidityExpiredMessage: string | null;
  quotaMode: 'conversation' | 'token' | 'batch' | 'unlimited'; // Add this
}
```

## Implementation Strategy

### Phase 1: Backend (2 functions)
1. Add quotaMode check to `computeAccountValidity()`
2. Add quotaMode check to `getWorkspaceQuotaConfig()`
3. Add quotaMode to API response
4. Test with quotaMode = "unlimited"

### Phase 2: Frontend (3 components)
1. Update API type definitions
2. Modify SuperLobsterPage.tsx to check quotaMode
3. Modify ZclawShell.tsx to hide quota UI
4. Test all four quota modes

### Phase 3: Integration Testing
1. Test "unlimited" mode - no quota warnings
2. Test "conversation" mode - conversation limits work
3. Test "token" mode - token limits work
4. Test "batch" mode - batch limits work

## Risk Assessment

### Low Risk
- Changes are additive (early returns in existing functions)
- No database schema changes
- No breaking API changes (only adding a field)
- Existing logic remains unchanged for other quota modes

### Mitigation
- Test all four quota modes after implementation
- Verify no regression in existing quota enforcement
- Frontend gracefully handles missing quotaMode field (fallback to current behavior)

## Performance Impact

### Database Queries
- **Added:** 2 queries to `ZclawEnterpriseConversationQuotaConfig` per request
- **Impact:** Minimal (simple indexed lookup)
- **Mitigation:** Could cache quotaMode in memory if needed (not recommended initially)

### Response Size
- **Added:** ~10 bytes per API response (quotaMode field)
- **Impact:** Negligible

## Rollback Plan

If issues arise:
1. Revert backend changes (2 function modifications)
2. Revert frontend changes (3 component modifications)
3. No data migration needed (quotaMode field already exists)

## Testing Strategy

### Backend Tests
- Unit test: `computeAccountValidity()` returns null when unlimited
- Unit test: `getWorkspaceQuotaConfig()` returns MAX_SAFE_INTEGER when unlimited
- Integration test: API response includes quotaMode field

### Frontend Tests
- Manual test: Set quotaMode = "unlimited", verify no quota warnings
- Manual test: Set quotaMode = "conversation", verify conversation limits work
- Manual test: Set quotaMode = "token", verify token limits work
- Manual test: Set quotaMode = "batch", verify batch limits work

### E2E Tests
- Create enterprise with unlimited mode
- Verify user can chat without quota warnings
- Verify no quota UI elements visible
- Switch to other modes and verify limits work
