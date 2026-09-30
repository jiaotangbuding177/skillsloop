# Cross-Cutting Guides

These guides document patterns that span multiple packages (`api`, `web`, `db`, `shared`). They exist because no single package's README can fully describe a flow that touches all three layers.

## Guides in This Section

### [Cross-Layer Data Flow](cross-layer-data-flow.md)

The complete lifecycle of a request from a user click in the browser to a PostgreSQL row and back. Covers the API response envelope, how `ApiClient` unwraps it, error code propagation, enterprise context injection via headers, and the **workspace file flow** (how path constants like `'个人知识库'` / `'对话附件'` flow through backend proxy to km-agent / EvoMind).

**Read this when:** You are building a new feature that adds an API endpoint and a corresponding UI call. You need to know the exact shape your API response must take and how the web layer will consume it. Also read when working with workspace file uploads, knowledge base paths, or km-agent integration.

### [Bilingual Errors](bilingual-errors.md)

The dual-layer translation pattern for error messages. Custom API error messages are written directly in Chinese. Framework errors (NestJS/Prisma) get pattern-translated to Chinese by the filter. The web layer can re-translate Chinese messages to English for `en` locale users.

**Read this when:** You are adding a new error condition. You need to know where to define the Chinese message, how the filter handles framework errors, and how the web layer decides which language to display.

### [Idempotency](idempotency.md)

End-to-end idempotency for mutation endpoints. The web layer generates a client-side idempotency key, passes it as a header, and the API layer validates it via database unique constraints. Covers key format, P2002 handling, and retry semantics.

**Read this when:** You are building a new mutation endpoint (create, purchase, top-up) that must be safe against double-submit and network retries.

### [Voice Feature Release Checklist](voice-release-checklist.md)

语音功能发布专项检查：环境变量（缺失即 API 启动崩）、无 DB 迁移确认、工具扣费配置（tool_call_billing_configs voice_input 行）、配额行为矩阵、P0 抽验清单、分支发布顺序。

**Read this when:** 发布语音功能或改动语音计费/配额行为时。
### [Pre-Push Checklist](pre-push-checklist.md)

Quick checklist to run before `git push`: TS compilation, full test suite, type-field cross-layer sync, and i18n key completeness. Includes the critical gotcha that `tsx --test` is NOT a substitute for `tsc` compilation check.

### [Performance Optimization Verification](performance-optimization-verification.md)Two hard rules for loading/perf optimization tasks: waterfall-based segment attribution with quantified goal baselines, and enumerating all consumer state combinations (panel expanded × enterprise switch × search) when changing data-loading semantics.

**Read this when:** You are changing how data is loaded (limit/first-N, lazy load, local-first, background sync) or writing a perf PRD's acceptance criteria.

---

## How These Guides Relate to Package Specs

- **Package specs** (`db/index.md`, `shared/index.md`) describe what a package IS — its exports, conventions, and internal structure.
- **Cross-cutting guides** describe how packages INTERACT — the contracts and flows that span package boundaries.

When adding a new feature, consult the package spec for the layer you are modifying, then consult the relevant cross-cutting guide to ensure the integration with other layers follows established patterns.

---

## Conventions Across All Guides

- All HTTP responses use the envelope `{ code: number, message: string, data: T }`. No endpoint should return a bare object.
- Enterprise context always flows via the `x-enterprise-id` request header, never as a query parameter or body field.
- Error codes are numeric enums defined in `apps/api/src/common/constants/error-codes.ts`, with severity mapping in `apps/web/src/lib/error-codes.ts`. Never use raw numeric literals for error codes in either layer.
- All monetary and token amounts cross the wire as strings (BigInt serialization). Parse with `BigInt()` only when arithmetic is required.
### [Local Worktree Environment](local-worktree-environment.md)

Windows 上 devflow worktree 开发的环境踩坑与解法：深路径双态（vitest/tsc 用 junction、next build 用真实安装）、pnpm junction 穿透重建、Prisma client 重新生成、next@16 无 exports map + RangeError、hook cwd 解析、.env 拷贝与状态真相源。

**Read this when:** 在 worktree 内跑测试/构建/dev 遇到深路径、symlink、EPERM、Prisma 类型、next build 报错类问题；或新建 worktree 任务需要初始化本地环境。
