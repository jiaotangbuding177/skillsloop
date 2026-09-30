# Implementation Plan: Master Quota Policy Toggle

## Phase 1: Backend Implementation

### Step 1.1: Modify computeAccountValidity()

**File:** `apps/api/src/zclaw/zclaw.service.ts`

**Action:** Add quotaMode check at the beginning of the function

```typescript
async computeAccountValidity(enterpriseId: string, userId: string) {
  // Check if enterprise is in unlimited mode
  const quotaConfig = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
    where: { enterpriseId },
    select: { quotaMode: true },
  });
  
  if (quotaConfig?.quotaMode === 'unlimited') {
    return null; // No validity constraint for unlimited mode
  }
  
  // ... existing logic continues
}
```

**Validation:**
```bash
cd apps/api
npm test -- zclaw.service.spec.ts
```

**Expected result:** Test passes, function returns null when quotaMode is unlimited

---

### Step 1.2: Modify getWorkspaceQuotaConfig()

**File:** `apps/api/src/zclaw/zclaw.service.ts`

**Action:** Add quotaMode check at the beginning of the function

```typescript
async getWorkspaceQuotaConfig(enterpriseId: string, userId: string) {
  // Check if enterprise is in unlimited mode
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
  
  // ... existing logic continues
}
```

**Validation:**
```bash
cd apps/api
npm test -- zclaw.service.spec.ts
```

**Expected result:** Test passes, function returns MAX_SAFE_INTEGER when quotaMode is unlimited

---

### Step 1.3: Add quotaMode to API Response

**File:** `apps/api/src/zclaw/zclaw.service.ts`

**Action:** Modify getWorkspaceQuotaLimitText() to include quotaMode in response

```typescript
async getWorkspaceQuotaLimitText(enterpriseId: string, userId: string) {
  // Get quotaMode
  const quotaConfig = await this.prisma.zclawEnterpriseConversationQuotaConfig.findUnique({
    where: { enterpriseId },
    select: { quotaMode: true },
  });
  
  // ... existing logic
  
  return {
    usageBytes: usage.usageBytes,
    quotaBytes: quotaConfig?.quotaBytes ?? 0,
    effectiveQuotaBytes: effectiveQuotaBytes,
    remainingBytes: remainingBytes,
    fileCount: usage.fileCount,
    directoryCount: usage.directoryCount,
    isOverLimit: usage.usageBytes >= effectiveQuotaBytes,
    accountValidityExpired: accountValidityExpired,
    accountValidityExpiredMessage: accountValidityExpiredMessage,
    quotaMode: quotaConfig?.quotaMode ?? 'conversation', // Add this field
  };
}
```

**Validation:**
```bash
cd apps/api
npm run build
```

**Expected result:** Build succeeds, no TypeScript errors

---

### Step 1.4: Backend Testing

**Action:** Create test cases for unlimited mode

**File:** `apps/api/src/zclaw/zclaw.service.spec.ts`

```typescript
describe('Quota Mode: Unlimited', () => {
  it('computeAccountValidity returns null when quotaMode is unlimited', async () => {
    // Setup: Set quotaMode to 'unlimited'
    await prisma.zclawEnterpriseConversationQuotaConfig.create({
      data: {
        enterpriseId: testEnterpriseId,
        quotaMode: 'unlimited',
      },
    });
    
    const result = await zclawService.computeAccountValidity(testEnterpriseId, testUserId);
    expect(result).toBeNull();
  });
  
  it('getWorkspaceQuotaConfig returns MAX_SAFE_INTEGER when quotaMode is unlimited', async () => {
    // Setup: Set quotaMode to 'unlimited'
    await prisma.zclawEnterpriseConversationQuotaConfig.create({
      data: {
        enterpriseId: testEnterpriseId,
        quotaMode: 'unlimited',
      },
    });
    
    const result = await zclawService.getWorkspaceQuotaConfig(testEnterpriseId, testUserId);
    expect(result.quotaBytes).toBe(BigInt(Number.MAX_SAFE_INTEGER));
    expect(result.accountValidityExpired).toBe(false);
  });
  
  it('API response includes quotaMode field', async () => {
    // Setup: Set quotaMode to 'unlimited'
    await prisma.zclawEnterpriseConversationQuotaConfig.create({
      data: {
        enterpriseId: testEnterpriseId,
        quotaMode: 'unlimited',
      },
    });
    
    const result = await zclawService.getWorkspaceQuotaLimitText(testEnterpriseId, testUserId);
    expect(result.quotaMode).toBe('unlimited');
  });
});
```

**Validation:**
```bash
cd apps/api
npm test -- zclaw.service.spec.ts
```

**Expected result:** All tests pass

---

## Phase 2: Frontend Implementation

### Step 2.1: Update API Type Definitions

**File:** `apps/web/src/api/moudles/zclaw.ts`

**Action:** Add quotaMode to WorkspaceQuotaLimitTextResponse interface

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
  quotaMode: 'conversation' | 'token' | 'batch' | 'unlimited'; // Add this field
}
```

**Validation:**
```bash
cd apps/web
npm run build
```

**Expected result:** Build succeeds, no TypeScript errors

---

### Step 2.2: Modify SuperLobsterPage.tsx

**File:** `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

**Action:** Check quotaMode before showing quota warnings

```typescript
// In the component where quota warnings are rendered
const quotaConfig = useWorkspaceQuotaConfig(); // Assuming this hook exists

// Skip quota warnings if unlimited
if (quotaConfig?.quotaMode === 'unlimited') {
  return null; // Don't render quota warnings
}

// Existing warning logic
if (accountValidityExpired) {
  return <AccountValidityWarning />;
}
if (isOverLimit) {
  return <StorageCapacityWarning />;
}
```

**Validation:**
```bash
cd apps/web
npm run build
```

**Expected result:** Build succeeds, no TypeScript errors

---

### Step 2.3: Modify ZclawShell.tsx

**File:** `apps/web/src/components/zclaw/ZclawShell.tsx`

**Action:** Hide quota displays when quotaMode is unlimited

```typescript
// In the sidebar rendering section
const quotaConfig = useWorkspaceQuotaConfig(); // Assuming this hook exists

// Skip quota displays if unlimited
if (quotaConfig?.quotaMode === 'unlimited') {
  return <SidebarWithoutQuota />; // Render simplified sidebar
}

// Existing quota UI
return <SidebarWithQuota />;
```

**Validation:**
```bash
cd apps/web
npm run build
```

**Expected result:** Build succeeds, no TypeScript errors

---

### Step 2.4: Frontend Testing

**Action:** Manual testing of all four quota modes

**Test Case 1: Unlimited Mode**
1. Set enterprise quotaMode to "unlimited" in admin panel
2. Navigate to chat interface
3. Verify no account validity warnings appear
4. Verify no storage capacity warnings appear
5. Verify sidebar doesn't show quota indicators
6. Try sending messages - should work without quota errors

**Test Case 2: Conversation Mode**
1. Set enterprise quotaMode to "conversation" with limit
2. Navigate to chat interface
3. Verify conversation count displays in sidebar
4. Verify conversation limit warnings appear when approaching limit
5. Verify message sending blocked when limit reached

**Test Case 3: Token Mode**
1. Set enterprise quotaMode to "token" with limit
2. Navigate to chat interface
3. Verify token usage displays in sidebar
4. Verify token limit warnings appear when approaching limit
5. Verify message sending blocked when limit reached

**Test Case 4: Batch Mode**
1. Set enterprise quotaMode to "batch" with batch configuration
2. Navigate to chat interface
3. Verify batch period displays in sidebar
4. Verify batch expiration warnings appear when batch expires
5. Verify message sending blocked when batch expired

---

## Phase 3: Integration Testing

### Step 3.1: End-to-End Test

**Action:** Create test enterprise and verify all scenarios

```bash
# Start both API and Web
cd apps/api && npm run dev
cd apps/web && npm run dev
```

**Test Scenario:**
1. Create new enterprise
2. Set quotaMode to "unlimited"
3. Add user to enterprise
4. Login as user
5. Verify chat works without quota warnings
6. Switch quotaMode to "conversation"
7. Verify conversation limits work
8. Switch quotaMode to "token"
9. Verify token limits work
10. Switch quotaMode to "batch"
11. Verify batch limits work

---

### Step 3.2: Regression Testing

**Action:** Verify existing functionality still works

**Test Cases:**
1. Existing enterprises with quota modes continue to work
2. Quota enforcement still active for non-unlimited modes
3. Admin can still change quota modes
4. Quota usage still tracked for non-unlimited modes

---

## Deployment Checklist

- [ ] Backend changes deployed to staging
- [ ] Frontend changes deployed to staging
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing completed for all four quota modes
- [ ] No regression in existing functionality
- [ ] Code reviewed by team
- [ ] Documentation updated (if needed)

---

## Rollback Plan

If issues arise after deployment:

1. **Backend rollback:**
   ```bash
   cd apps/api
   git revert <commit-hash>
   npm run build
   ```

2. **Frontend rollback:**
   ```bash
   cd apps/web
   git revert <commit-hash>
   npm run build
   ```

3. **No data migration needed** - quotaMode field already exists in database

---

## Success Criteria

- ✅ Backend returns correct values when quotaMode is unlimited
- ✅ Frontend hides quota UI when quotaMode is unlimited
- ✅ All four quota modes work correctly
- ✅ No regression in existing functionality
- ✅ Code passes all tests
- ✅ Documentation is up to date
