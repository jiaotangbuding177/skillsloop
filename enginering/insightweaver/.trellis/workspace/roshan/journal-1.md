# Journal - roshan (Part 1)

> AI development session journal
> Started: 2026-07-14

---

## Session 1: Fix Safari blob download (WebKitBlobResource error 1)

**Date**: 2026-07-14
**Task**: Fix Safari blob download (WebKitBlobResource error 1)
**Branch**: `feat/quota-expiry-ui-optimization`

### Summary

Fix Safari-only file download bug where immediate URL.revokeObjectURL() after anchor.click() caused WebKitBlobResource error 1. Routed 4 download callsites through existing triggerBlobDownload helper (60s delayed revoke). Changes committed in isolated git worktree (iw-safari-fix, commit 55bddef8), pushed to fix/safari-blob-download, PR merged to release. Two rounds of CR (Oracle + ocr/qwen3.7-max) clean. Zero impact on main feat/quota-expiry-ui-optimization branch.

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

(No commits - planning session)

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete

## Session 3: B2B seat pool auto-allocate + order bug fix

**Date**: 2026-07-16
**Task**: B2B auto-distribution member batch rollover
**Branch**: `feat/quota-expiry-ui-optimization`

### Summary

Reactivated prematurely archived task 07-16-b2b-member-batch-rollover and implemented the full B2B seat pool unification. Also diagnosed and fixed a critical order creation bug where `b2b_monthly_seat_plan` was missing from `B2B_PLAN_TYPES` in `billing-order.service.ts`.

### Main Changes

**Backend (6 files):**

- `billing-order.service.ts` — Fixed missing `b2b_monthly_seat_plan` in B2B_PLAN_TYPES array (line 28) and `assertPlanSnapshotComplete` (lines 449, 452). This was causing error 1001 "不支持的套餐类型" when purchasing seat monthly plans.
- `entitlement.service.ts` (+609 lines) — Added `autoAllocate` param to `grantMonthlySeatPlan()` and `createB2BMonthlySeatGrantGroup()`. Added 4 new public methods: `listAutoAllocateAnchors()`, `autoAllocateForNewMembers()`, `autoRenewExpiringBatches()`, `autoReclaimLeftMemberSeats()` plus `voidActiveAutoAllocatedBatch()` helper.
- `entitlement-auto-allocate.scheduler.ts` (NEW) — Daily 02:00 scheduler following EntitlementExpiryScheduler pattern. Iterates auto-allocate anchors and runs new-member allocation, expiring-batch renewal, and departed-member reclaim with date-based idempotency keys.
- `billing.module.ts` — Registered EntitlementAutoAllocateScheduler in providers.
- `billing-plan.service.ts` + `dto/billing-plan.dto.ts` — metadata passthrough for plan CRUD.

**Frontend (4 files):**

- `billing-plans/page.tsx` — Removed `b2b_enterprise_plan` from PLAN_TYPES; added allocation mode radio group (auto/manual) for B2B monthly seat plans; cleaned dead code.
- `billing.ts` — Added `metadata` to SaveBillingPlanRequest.
- `zh.json` / `en.json` — Added allocationMode i18n section.

**Quality check fixes (by trellis-check):**

- Seat-cap check: filtered voided batches to prevent permanent capacity leak after reclaim.
- `autoRenewExpiringBatches`: added `validUntil > now` lower bound to exclude already-expired batches.
- `voidActiveAutoAllocatedBatch`: added missing ledger entries for member batch void and storage pool return.
- `listAutoAllocateAnchors`: added `validUntil > now` filter to exclude expired anchors.
- `autoReclaimLeftMemberSeats`: added fallback for storage-only users.

### Git Commits

| Hash       | Message                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------- |
| `fe9c4c90` | feat(billing): unify B2B seat pool with auto-allocate and fix order creation for monthly_seat_plan |

### Git Commits

| Hash       | Message                                                                                            |
| ---------- | -------------------------------------------------------------------------------------------------- |
| `fe9c4c90` | feat(billing): unify B2B seat pool with auto-allocate and fix order creation for monthly_seat_plan |
| `c4350d70` | fix(billing): check fixes for auto-allocate pool balance and paired batch handling                 |
| `1cab3c5b` | test(billing): add unit tests for B2B auto-allocate scheduler and clean orphan i18n key            |

### Testing

- `pnpm build`: PASSED (4/4 packages)
- `pnpm lint`: 0 errors in modified files (42 pre-existing errors in unrelated files)
- Unit tests: 29/29 auto-allocate tests passed (318/318 total, 2 pre-existing failures in unrelated file)

### Status

[OK] **Completed**

### Next Steps

- Phase 3.2 (e2e integration tests) from implement.md remains unimplemented
- Phase 4 (documentation) from implement.md remains unimplemented
- Advisory lock (pg_advisory_lock) deferred — idempotency keys mitigate concurrency risk
- Manual testing on staging recommended before production deploy

## Session 2: Fix account validity & batch window fallback, unify UI

**Date**: 2026-07-16
**Task**: Fix account validity & batch window fallback, unify UI
**Branch**: `feat/quota-expiry-ui-optimization`

### Summary

1. Fixed computeAccountValidity to accept any time window type (not just 'batch'), enabling seat pool users to see validity. 2. Merged hasAccountValidity/showAccountInvalid branches for consistent UI across all enterprise types. 3. C-end enterprises default to self_purchase mode. 4. Added CSS hover tooltips for token validity, agent ID, and account validity. 5. Removed redundant hasValidity section and showWarning banner.

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash       | Message       |
| ---------- | ------------- |
| `8b84e715` | (see git log) |
| `5889e311` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 3: Batch mode quota permission gating + monthly seat pool UI + quota simplification

**Date**: 2026-07-22
**Task**: Batch mode quota permission gating + monthly seat pool UI + quota simplification
**Branch**: `feat/quota-expiry-ui-optimization`

### Summary

1) batch 模式权限门控: 企业管理员在 admin_purchase/self_purchase 下隐藏批次管理菜单+后端 8 个 wrapper 拦截; 2) 非 batch 模式不叠加存储 entitlement; 3) b2b 月包分支+无月包到期分支; 4) 企业管理员月席位池 API+UI 优化(4列精简表格+剩余席位修复+分配下拉格式); 5) BillingPurchaseDialog 修复 b2b_monthly_seat_plan 3 处遗漏; 6) dotenv override 修复 shell 环境变量遮蔽; 7) 套餐记录只显示 active+scheduled; 8) i18n frozen 翻译+daysRemaining 参数修复; 9) 创建 CONTEXT.md 领域模型; 10) spec 更新 3 个文件

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `b82b67f5` | (see git log) |
| `b7d0815c` | (see git log) |
| `175dc6ff` | (see git log) |
| `c7da6e2d` | (see git log) |
| `148c7538` | (see git log) |
| `967c40ca` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 4: Batch Member Stale Validity Fix

**Date**: 2026-07-23
**Task**: Batch Member Stale Validity Fix
**Branch**: `feat/quota-expiry-ui-optimization`

### Summary

Fixed batch member stale validity issue where assignMemberToBatch upsert did not clear validFrom/validTo, causing computeAccountValidity to return expired and quota to reset to zero. Implemented isUsableInBillingContext to allow C-end packages in self_purchase mode, removed admin role skip from settlement for audit completeness, and fixed token package query to include scheduled status.

### Main Changes

- Detailed change bullets were not supplied; see the summary above.

### Git Commits

| Hash | Message |
|------|---------|
| `eeaa5a3e` | (see git log) |
| `fa8a5742` | (see git log) |
| `426bc642` | (see git log) |
| `6e28b4b9` | (see git log) |
| `f66c21c1` | (see git log) |

### Testing

- Validation was not recorded for this session.

### Status

[OK] **Completed**

### Next Steps

- None - task complete
