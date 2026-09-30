---
schema: spec-driven
---

# Tool Output Protection Spec

## Context
Tool messages returned by the system can leak sensitive information through two channels:
1. **SKILL.md content**: Full skill instruction files appear in tool output (`[read]\n{JSON}` format)
2. **Brand names**: `openclaw`, `@mariozechner/pi-*`, `hermes` appear in paths/package names

Protection must cover ALL data exit points: SSE stream, REST endpoints, and frontend rendering.

## Architecture: Defense in Depth (3 Layers)

```
km-agent (raw tool output)
        │
        ▼
┌─── API Layer ──────────────────────────────────────────────┐
│                                                             │
│  Layer 1: SSE Stream (streamMessage)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ sanitizeToolOutputForStream(payload) → yield         │  │
│  │ ✅ Already implemented                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 2: REST Endpoints (getSessionDetail,                │
│           getSessionMessagesPage)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ extractToolActivity() → sanitize output/args/error   │  │
│  │ sanitizeRagflowRetrievalDisplayMessage() → sanitize   │  │
│  │   tool content                                        │  │
│  │ ✅ Implemented                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 2b: DB Persistence (upsertLocalToolMessage)          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ sanitize rawPayload before writing to DB              │  │
│  │ ✅ Implemented                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─── Frontend Layer ──────────────────────────────────────────┐
│                                                             │
│  Layer 3: Message Loading                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ sanitizeRagflowRetrievalDisplayMessage(role, content) │  │
│  │ → sanitizeToolOutputForDisplay() for tool role        │  │
│  │ ✅ Already implemented                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Layer 3b: Rendering                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ MessageBubble: sanitizeToolOutputRecursive(output)    │  │
│  │ ToolActivityGroup: sanitizeToolOutputRecursive(...)   │  │
│  │ ZclawMarkdown: sanitizeToolOutputForDisplay(content)  │  │
│  │ ✅ Already implemented                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Brand Replacement Patterns

Applied in ALL layers (both API and frontend). Patterns ordered by specificity:

| # | Pattern | Replacement | Matches |
|---|---------|-------------|---------|
| 1 | `/@mariozechner\/pi-/gi` | `@evomind/evomind-` | Full npm package path (highest priority) |
| 2 | `/@mariozechner/gi` | `@evomind` | Standalone npm scope |
| 3 | `/openclaw/gi` | `evomind` | Paths, filenames, text |
| 4 | `/\bpi-(agent-core\|ai\|coding-agent\|tui\|cli\|shared\|config\|hooks\|memory\|tools\|utils\|core)\b/gi` | `evomind-$1` | Bare package names |
| 5 | `/\bhermes\b/gi` | `evomind` | Standalone word |

> **Design note**: Pattern 1 must be applied before pattern 2 to prevent partial replacement of `@mariozechner/pi-*` by the standalone `@mariozechner` rule. The regex `/openclaw/gi` intentionally does NOT include `-?` to avoid eating the hyphen in `openclaw-shared-skills`.

## API Layer: Implementation

### Change 1: `extractToolActivity()` — Sanitize return values
**File**: `apps/api/src/zclaw/zclaw.service.ts` (~line 6098)

After building the activity object, sanitize `output`, `args`, `error`, `deltas` before returning. This is the single chokepoint — all 5 callers benefit automatically:
- `getLocalSessionDetail` (line 5335)
- `mapSessionDetailMessage` (line 7630)
- `mergeMessagesWithLocalToolSnapshots` (line 5583)
- `formatToolSnapshotContent` (line 6087)
- `hasUsefulToolActivitySnapshot` (line 5607)

### Change 2: `getLocalSessionDetail()` — Sanitize tool message content
**File**: `apps/api/src/zclaw/zclaw.service.ts` (~line 5325)

For tool role, apply brand + skill sanitization to `content` field via `sanitizeToolContentForResponse()`.

### Change 3: `mapSessionDetailMessage()` — Sanitize tool message content
**File**: `apps/api/src/zclaw/zclaw.service.ts` (~line 7610)

Same as Change 2, for remote km-agent messages.

### Change 4: `upsertLocalToolMessage()` — Sanitize rawPayload before DB write
**File**: `apps/api/src/zclaw/zclaw.service.ts` (~line 5942)

Sanitize `rawPayload` before passing to `upsertLocalToolMessage`. New data stored in DB will be clean.

### New Function: `sanitizeToolContentForResponse(content: string): string`
**File**: `apps/api/src/zclaw/tool-output-sanitizer.ts`

Parses `[toolName]\n{JSON}` format, recursively sanitizes nested values (brand replacement + skill content detection), re-serializes.

## Frontend Layer: Already Implemented

### Files Modified (Frontend)
| File | Purpose |
|------|---------|
| `apps/web/src/lib/tool-output-sanitizer.ts` | Frontend sanitizer (JSON parsing + recursive + brand patterns) |
| `apps/web/src/lib/zclaw-ragflow-message.ts` | Message loading sanitization routing |
| `apps/web/src/components/super-lobster/MessageBubble.tsx` | Rendering sanitization (MessageBubble + ToolActivityGroup) |
| `apps/web/src/components/zclaw/ZclawMarkdown.tsx` | Markdown rendering sanitization |
| `apps/web/src/hooks/useZclawChat.ts` | NO_REPLY message filtering |
| `apps/web/src/components/super-lobster/SuperLobsterPage.tsx` | NO_REPLY filtering + history rendering |
| `apps/web/src/lib/cron-task-helpers.ts` | Cron run summary sanitization |

### ToolActivityGroup Rendering Checklist

All 5 sanitization points in grouped tool message rendering:

| Point | Content | Status |
|-------|---------|--------|
| `activities.output` | `sanitizeToolOutputRecursive` | ✅ |
| `activities.deltas` | `sanitizeToolOutputRecursive` | ✅ |
| `activities.args` | `sanitizeToolOutputRecursive` | ✅ |
| `activities.error` | `sanitizeToolOutputRecursive` | ✅ |
| `detail.body` | `sanitizeToolOutputForDisplay(mapWorkspacePathsForDisplay())` | ✅ |

## Skill Content Detection

Used across all layers. Detects SKILL.md content by:
1. YAML frontmatter with `name:` or `description:` keys (supports both `\n` and `\r\n`)
2. Skill-specific markdown patterns like `## What I do`, `## How to use`, etc.

When detected, replaces entire string with `[已读取 ${skillName}]`.
