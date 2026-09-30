# Fix Safari blob download failure (WebKitBlobResource error 1)

## Goal

Fix the Safari-only `WebKitBlobResource error 1` that occurs when triggering anchor-click blob downloads where `URL.revokeObjectURL` is called immediately after `.click()`. The fix delays revoke by 60s to allow the download to start.

## Root Cause (Already Diagnosed)

Creating a blob URL, clicking an anchor with `download` attribute, then _immediately_ calling `URL.revokeObjectURL(url)`. In Safari, `.click()` starts the download asynchronously; WebKit invalidates the blob before the download begins → `WebKitBlobResource error 1`. Chrome/Firefox tolerate this via internal refcounting.

## Correct Pattern to Reuse

`apps/web/src/lib/workspace-batch-download.ts` exports:

- `triggerBlobDownload(blob, filename)` — delegates to a shared anchor-download flow
- Uses `BLOB_URL_REVOKE_DELAY_MS = 60_000` for the delayed revoke

`apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx` (L254) already uses this pattern correctly.

## Scope (5 files)

| File                                                                                                        | Pattern                      | ~Line                   |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------------- |
| `apps/web/src/components/ResearchInterface.tsx`                                                             | Module-scoped `downloadBlob` | ~175                    |
| `apps/web/src/app/[locale]/(home)/history/page.tsx`                                                         | Module-scoped `downloadBlob` | ~51                     |
| `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`                                                | 4 `revokeObjectURL` calls    | ~2992, 3272, 3351, 3366 |
| `apps/web/src/app/[locale]/(zclaw-shell)/admin/enterprise-memberships/page.tsx`                             | `revokeObjectURL` call       | ~782                    |
| `apps/web/src/app/[locale]/(zclaw-shell)/admin/enterprise-departments/_components/departmentGroupExport.ts` | `revokeObjectURL` call       | ~161                    |

**ONLY fix download flows** (anchor create → set href to blob URL → click → revoke). Leave preview/cleanup/unmount revokes unchanged.

## Constraints

- Isolated worktree off `release` branch — touches must NOT leak to `feat/quota-expiry-ui-optimization`
- Surgical/minimal changes — only blob-revoke timing + necessary imports
- Reuse existing `triggerBlobDownload`, do NOT write a new helper
- No `as any` / `@ts-ignore`

## Acceptance Criteria

- [x] 4 files fixed (SuperLobsterPage.tsx skipped — all 4 revokes are preview/cleanup, not download)
- [x] eslint 0 errors on changed files
- [x] Per-file diff verified clean (8 insertions, 30 deletions, single-quote style preserved)
- [x] Every skipped `revokeObjectURL` call documented with reason
- [x] Committed `55bddef8` on `fix/safari-blob-download`, pushed to Gitee, PR merged to release
- [x] Worktree isolated — zero impact on main `feat/quota-expiry-ui-optimization` branch

## Completion Notes (2026-07-14)

- **Actually changed**: 4 files (SuperLobsterPage intentionally skipped)
- **Commit**: `55bddef8` on worktree branch `fix/safari-blob-download`
- **CR**: Oracle approved + ocr (qwen3.7-max) clean — 0 issues
- **Environment caveat**: LSP daemon format-on-save with double-quote defaults conflicts with project single-quote style; edits required `git apply` to bypass
