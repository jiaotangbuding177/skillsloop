# Shared Package Specification

## Overview

`packages/shared` is the cross-application utilities package. It contains types, constants, and pure functions consumed by both `apps/api` and `apps/web`. It has zero runtime dependencies on either consumer — it knows nothing about HTTP, databases, or React.

**Entry point:** `packages/shared/src/index.ts` (barrel re-export)

---

## Module Map

### `locale.ts`

| Export | Kind | Purpose |
|---|---|---|
| `APP_LOCALES` | `const ['zh', 'en'] as const` | Canonical list of supported locales |
| `AppLocale` | type (union of `APP_LOCALES`) | Used wherever a locale string is required |
| `resolveBrowserLocale()` | function | Reads `navigator.language` / `Accept-Language` and maps to `AppLocale` |
| `resolveSessionTitle()` | function | Derives a display title from a session object, locale-aware |
| `buildAgentLocaleInstruction()` | function | Returns a system-prompt snippet telling the AI agent which language to use |

**Consumer:** Web uses `resolveBrowserLocale()` in routing config. API uses `buildAgentLocaleInstruction()` when assembling LLM prompts.

### `enterprise-kind.ts`

Three enterprise kinds drive branching logic across the entire stack:

| Kind | Description |
|---|---|
| `b2b` | Business-to-business enterprise with admin-managed billing |
| `consumer` | Individual consumer account |
| `evomind_consumer` | Consumer account provisioned via EvoMind integration |

**Type guards exported:**
- `isB2BEnterpriseKind(kind)` — returns `true` for `'b2b'`
- `isConsumerEnterpriseKind(kind)` — returns `true` for `'consumer'` or `'evomind_consumer'`
- `isDefaultQuotaAllowedKind(kind)` — returns `true` when the kind permits default quota allocation (currently `b2b` only)

**Purchase modes** are also defined here: `contact_admin`, `admin_purchase`, `self_purchase`. These drive the UI flow for quota top-ups and plan upgrades.

**Consumer:** API imports guards for entitlement logic. Web imports them for conditional rendering of billing pages.

### `deliverables/`

Handles parsing of file references embedded in assistant messages:

- `extractLinkedFilenamesFromText(text: string): string[]` — regex parser that finds filenames in:
  - Markdown links: `[name.pdf](https://...)`
  - Backtick code spans: `` `report.xlsx` ``
  - Bare paths: `/uploads/data.csv`
- File extension pattern constants used to filter which linked files count as deliverables

**Consumer:** API uses this to build the deliverables list shown in the billing/usage dashboard.

### Message Limits

```ts
export const ZCLAW_MESSAGE_MAX_CHARS = 32_000
export const ZCLAW_MESSAGE_SOFT_WARN_CHARS = 8_000
```

| Export | Purpose |
|---|---|
| `getZclawMessageLengthHint(text)` | Returns a human-readable hint like "8,500 / 32,000 characters" |
| `isZclawMessageWithinLimit(text)` | Returns `true` if text is under `ZCLAW_MESSAGE_MAX_CHARS` |

**Consumer:** Web calls these in the message input component to show warnings and block submission.

---

## Import Conventions

**From API:**
```ts
import { isB2BEnterpriseKind, type EnterpriseKind } from '@insightweaver/shared'
```

**From Web:**
```ts
import { APP_LOCALES, type AppLocale } from '@insightweaver/shared'
```

The package is consumed as a workspace dependency (`"@insightweaver/shared": "workspace:*"`) in both `apps/api/package.json` and `apps/web/package.json`.

---

## Adding a New Shared Utility

1. Create a new `.ts` file in `packages/shared/src/` (or add to an existing file if the concept is small).
2. Export the new symbol from `packages/shared/src/index.ts`.
3. Keep it pure — no side effects, no imports from `api` or `web`.
4. If the utility needs a database call or HTTP fetch, it belongs in `api`, not `shared`.
5. Add JSDoc to exported symbols — these are consumed by developers in other packages who may not read the source.

---

## What Does NOT Belong Here

- Zod/class-validator schemas that validate API request bodies (those live in `apps/api/src/` as DTOs)
- React hooks or components
- Prisma queries or database access
- Environment-specific configuration values
- Anything that requires `process.env` at import time

If a utility needs any of the above, it should live in the consuming package and call into `shared` for the pure logic it needs.
