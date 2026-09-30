# Design: Safari blob download fix

## Boundary

**What this fixes**: 5 call sites in the web app where a blob object URL is created, an anchor `.click()` is triggered for file download, and `URL.revokeObjectURL` is called too soon for Safari.

**What this does NOT change**: Preview image object URLs, cleanup/unmount revoke calls, avatar caches, or any non-download `revokeObjectURL` usage.

## Approach

For each affected callsite, one of two fixes:

1. **Preferred**: Delegate to the existing `triggerBlobDownload(blob, filename)` from `@/lib/workspace-batch-download`. This encapsulates the correct delayed-revoke pattern in one place.
2. **Fallback**: If the block structure makes a full refactor risky (e.g., complex surrounding logic), minimally wrap the existing `URL.revokeObjectURL(url)` in `window.setTimeout(() => URL.revokeObjectURL(url), 60_000)`.

## Data Flow

```
[Component] → triggerBlobDownload(blob, filename)
             ↓
             Create blob URL via URL.createObjectURL
             Create <a> element, set href + download + click()
             Set timeout: revokeObjectURL after 60s
```

## Tradeoffs

- **60s delay**: Object URL lives longer than necessary in Chrome/Firefox, but the memory impact of a short-lived URL is negligible. Safety margin > strictness.
- **Reusing triggerBlobDownload**: Adds an import but ensures single source of truth. If a callsite's existing code already handles the anchor creation but only needs delayed revoke, `triggerBlobDownload` may be overkill (but still safe).

## Compatibility

- Safari: Fixes the blob download error.
- Chrome/Firefox: No behavioral change (already worked via internal refcounting).
- Mobile Safari / iOS: Same fix applies (WebKit engine).

## Rollback

Each change is limited to replacing a function body or adding a setTimeout. Reverting requires restoring the original line(s) from `git diff`.
