# Tool Output Protection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Intercept and sanitize tool outputs in the SSE stream to protect skill instructions and standardize brand names.
**Architecture:** A new `tool-output-sanitizer.ts` utility will check all tool events against rules (skill patterns, YAML frontmatter, `openclaw` keywords) before the `yield` in `streamMessage`.
**Tech Stack:** NestJS, TypeORM, SSE (Server-Sent Events), Vitest.

---

### Task 1: Create Tool Output Sanitizer (TDD)

**Files:**
- Test: `apps/api/src/zclaw/__tests__/tool-output-sanitizer.test.ts`
- Create: `apps/api/src/zclaw/tool-output-sanitizer.ts`

- [ ] **Step 1: Write failing test (RED)**

```typescript
// apps/api/src/zclaw/__tests__/tool-output-sanitizer.test.ts
import { describe, expect, it } from 'vitest';
import { sanitizeToolOutputForStream } from '../tool-output-sanitizer';
import { Logger } from '@nestjs/common';

const mockLogger = { debug: () => {} } as unknown as Logger;

describe('sanitizeToolOutputForStream', () => {
  it('replaces openclaw with evomind', () => {
    const input = { msg: 'use openclaw skills' };
    const res = sanitizeToolOutputForStream(input, mockLogger);
    expect(JSON.stringify(res)).toContain('evomind');
    expect(JSON.stringify(res)).not.toContain('openclaw');
  });

  it('masks skill frontmatter structures', () => {
    const input = { content: '---\nname: Patent Scanner\ndescription: test\n---' };
    const res = sanitizeToolOutputForStream(input, mockLogger);
    expect(JSON.stringify(res)).not.toContain('Patent Scanner');
    expect(JSON.stringify(res)).not.toContain('description:');
  });

  it('handles nested JSON objects', () => {
    const input = { tool: { args: { path: '/skills/xyz', openclaw_version: '1.0' } } };
    const res = sanitizeToolOutputForStream(input, mockLogger);
    expect(JSON.stringify(res)).toContain('evomind_version');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pnpm test -- apps/api/src/zclaw/__tests__/tool-output-sanitizer.test.ts`
Expected: FAIL with "Cannot find module '../tool-output-sanitizer'" or "sanitizeToolOutputForStream is not defined".

- [ ] **Step 3: Write minimal implementation (GREEN)**

```typescript
// apps/api/src/zclaw/tool-output-sanitizer.ts
import { Logger } from '@nestjs/common';

const SKILL_FRONTMATTER = /(^---[\s\S]*?^---|(^|\n)(name|description|homepage|user-invokable|emoji|tags):\s.*)+/gm;
const OPENCLAW_PATTERN = /openclaw-?/gi;

export function sanitizeToolOutputForStream(
  data: Record<string, unknown>,
  _logger: Logger,
): Record<string, unknown> {
  const text = JSON.stringify(data);
  
  // Rule 1: Skill content masking
  // Replace frontmatter block or individual skill fields
  const sanitized1 = text.replace(SKILL_FRONTMATTER, '');
  
  // Rule 2: OpenClaw replacement
  const sanitized2 = sanitized1.replace(OPENCLAW_PATTERN, 'evomind');
  
  return JSON.parse(sanitized2);
}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pnpm test -- apps/api/src/zclaw/__tests__/tool-output-sanitizer.test.ts`
Expected: PASS.

### Task 2: Integrate into SSE Stream

**Files:**
- Modify: `apps/api/src/zclaw/zclaw.service.ts:4170`

- [ ] **Step 1: Import the sanitizer**

```typescript
import { sanitizeToolOutputForStream } from './tool-output-sanitizer';
```

- [ ] **Step 2: Apply sanitizer before `yield`**

Modify the `streamMessage` loop at line 4170:
```typescript
// From:
yield { event: upstreamEvent.event, data: payload };

// To:
const sanitizedPayload = sanitizeToolOutputForStream(payload, this.logger);
yield { event: upstreamEvent.event, data: sanitizedPayload };
```

- [ ] **Step 3: Commit**

- [ ] **Step 4: Verification**
Run: `pnpm build && pnpm test`
Expected: Build success and all tests pass.

Plan complete and saved to `docs/superpowers/plans/2026-06-09-tool-output-protection.md`. Two execution options:

1. Subagent-Driven (recommended)
2. Inline Execution

Which approach?