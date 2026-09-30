# Implementation Plan: Safari blob download fix

## Phase 0 — Worktree Setup

1. `git fetch origin release`
2. `git worktree add -b fix/safari-blob-download ../iw-safari-fix origin/release`
3. `cd ../iw-safari-fix` → all subsequent work happens here
4. `pnpm install` (timeout: 600000 ms)
5. `pnpm db:generate` (needed for tsgo)

## Phase 1 — Inspect Each Call Site (read-only)

For each of the 5 files:

- Read the area around the `revokeObjectURL` call
- Classify as: **download** (anchor create → click → revoke) or **non-download** (preview/cleanup)
- Only download callsites get fixed

## Phase 2 — Apply Fixes (surgical)

### 2.1 `ResearchInterface.tsx` — `downloadBlob` (~L175)

- Add import: `import { triggerBlobDownload } from '@/lib/workspace-batch-download';`
- Replace `downloadBlob` body to delegate to `triggerBlobDownload(blob, filename);`

### 2.2 `history/page.tsx` — `downloadBlob` (~L51)

- Add import: `import { triggerBlobDownload } from '@/lib/workspace-batch-download';`
- Replace `downloadBlob` body to delegate to `triggerBlobDownload(blob, filename);`

### 2.3 `SuperLobsterPage.tsx` — 4 revoke calls (~L2992, L3272, L3351, L3366)

- For each: inspect, classify (download vs non-download)
- Download flows → `triggerBlobDownload` or `setTimeout` wrap
- Non-download → leave unchanged, document reason

### 2.4 `enterprise-memberships/page.tsx` — ~L782

- Inspect, classify
- If download → fix with `triggerBlobDownload` or `setTimeout`

### 2.5 `departmentGroupExport.ts` — ~L161

- Inspect, classify
- If download → fix with `triggerBlobDownload` or `setTimeout`

## Phase 3 — Verify

1. `cd ../iw-safari-fix`
2. `pnpm tsgo` → must exit 0
3. `pnpm format:fix` (or prettier on changed files only)
4. `git diff --stat` → summarize
5. `git diff` → record full patch

## Phase 4 — Report

Write summary containing:

- (a) Per-file changes
- (b) Skipped revoke calls + reasons
- (c) `pnpm tsgo` output
- (d) `git diff --stat`
- (e) Smoke-test steps for human

## Rollback Points

- After Phase 2 (before verify): if changes are wrong, `git checkout -- <files>` to revert
- After Phase 3 (type errors): fix type errors before proceeding

## Smoke Test Cases

| Page                           | Action                                     | Expected                                              |
| ------------------------------ | ------------------------------------------ | ----------------------------------------------------- |
| Research workspace             | Click download button on a research result | File downloads on Safari, no WebKitBlobResource error |
| History page                   | Click download on a past result            | File downloads on Safari, no error                    |
| SuperLobster                   | Trigger a blob download (export/save)      | File downloads on Safari                              |
| Admin → Enterprise Memberships | Trigger a blob download                    | File downloads on Safari                              |
| Admin → Enterprise Departments | Trigger a blob export/download             | File downloads on Safari                              |

All must work on Safari. Chrome/Firefox behavior must be unchanged.
