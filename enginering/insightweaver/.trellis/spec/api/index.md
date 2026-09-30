# API Layer Overview

The API layer is a NestJS (ESM) backend located at `apps/api/src/`. It serves as the primary backend for the InsightWeaver Quota UI platform, handling billing, authentication, enterprise management, AI agent orchestration, and payment processing.

## Architecture at a Glance

- **Framework:** NestJS with ESM modules
- **Bootstrap:** `apps/api/src/main.ts` — creates app with `bufferLogs: true, bodyParser: false`
- **Global prefix:** `api` (all routes are `/api/...`)
- **Database:** Prisma ORM with string-token DI (`@Inject('PrismaClient')`)
- **Testing:** Node.js built-in `node:test` via `tsx --test`
- **Body limit:** 20MB with raw-body preservation for WeChat webhook

## Spec Files

| File | Description |
|------|-------------|
| [module-structure.md](./module-structure.md) | NestJS module organization, DI patterns, cross-module dependencies |
| [controller-patterns.md](./controller-patterns.md) | Routing conventions, guard composition, access tiers, idempotency |
| [service-patterns.md](./service-patterns.md) | Transaction handling, BigInt usage, atomic updates, optional injection |
| [error-handling.md](./error-handling.md) | Error codes, AllExceptionsFilter, bilingual error translation |
| [database-access.md](./database-access.md) | Prisma injection, transaction client typing, raw SQL, singleton pattern |
| [testing.md](./testing.md) | node:test runner, Prisma mocking, assertion patterns |
| [quota-mode-architecture.md](./quota-mode-architecture.md) | Quota mode independence, unlimited sentinel, billing bypass, admin role handling, unified config pattern |
| [billing-payment-flow.md](./billing-payment-flow.md) | C 端支付订单状态机、权益批次拆分规则、生效时间对齐、微信回调报文、数据关联约定 |
| [token-calculation.md](./token-calculation.md) | Token 加权公式、工具调用计费、数据来源链路、SSE 断连恢复、gotcha 汇总 |
| [speech-proxy-websocket.md](./speech-proxy-websocket.md) | 语音输入代理网关、WS 鉴权、计时结算、兜底调度、配额计费契约（会话扣减/start 拦截/明细标记） |
| [message-lifecycle.md](./message-lifecycle.md) | 消息三写入路径、UUID/Trusted/tool 三类 ID 格式、prune 守卫缺失导致的数据丢失 bug + 修复矩阵 |
| [task-board.md](./task-board.md) | 任务看板契约：七端点、seq 不复用、position 落位算法、assigneeName 回填、前端对接约定 |
| [users-table-timestamp-contract.md](./users-table-timestamp-contract.md) | users 四表时间戳口径契约：Prisma=UTC、导入 SQL 必须 AT TIME ZONE 'UTC'、历史脏行判读规则、裸 NOW() 禁令 |

## Environment Variable Loading

**Pattern**: `main.ts` uses `dotenv.config({ override: true })` before NestJS bootstrap.

**Why**: Shell environment variables (even empty strings or `"False"`) can shadow `.env` file values because dotenv's default `override: false` doesn't overwrite existing `process.env` keys. With `override: true`, `.env` file values always win during local development.

```typescript
// apps/api/src/main.ts
import 'reflect-metadata';
import { config as dotenvConfig } from 'dotenv';
dotenvConfig({ override: true }); // .env overrides shell env vars
```

**Production impact**: Low risk. If no `.env` file exists in production (typical for Docker/K8s deployments), `override: true` has no effect. If both `.env` and `process.env` have the same key, `.env` wins — this is usually the desired behavior (local `.env` for dev, platform env vars for production).

**Gotcha**: Without `override: true`, developers may see `WX_PAY_TEST="False"` or other stale shell values blocking `.env` changes, causing confusing "why isn't my .env change working?" bugs.

## Key Entry Points

| File | Purpose |
|------|---------|
| `apps/api/src/main.ts` | Bootstrap, middleware, global pipes/interceptors/filters |
| `apps/api/src/app.module.ts` | Root module importing all 18 feature modules |
| `apps/api/src/common/` | Shared utilities: logger, filters, interceptors, guards, constants |
| `apps/api/src/auth/` | JWT authentication guards and strategies |

## Module Count

Feature modules registered in `app.module.ts` (2026-09 起含 TaskBoardModule):

DatabaseModule, RedisModule, CommonModule, AuthModule, BillingModule, EnterpriseModule, ZclawModule, SkillModule, AgentModule, AgentManagementModule, ResearchModule, AttachmentModule, CreditsModule, DashboardModule, AdminUsersModule, McpModule, WechatPayModule, HealthModule

## Cross-Cutting Concerns

- **Logging:** `AppLogger` (extends `ConsoleLogger`) with per-request ID via `RequestContextService` + `RequestIdMiddleware`
- **Validation:** Global `ValidationPipe` with `whitelist: true`, `transform: true`
- **Interceptors:** `LoggingInterceptor` (logs method, URL, duration, params) then `ResponseInterceptor` (normalizes response envelope)
- **Error filter:** `AllExceptionsFilter` normalizes all errors to `{ code, message, data }`
- **CORS:** Origin from `WEB_ORIGIN` env var
- **Caching:** ETags disabled, `Cache-Control: no-store` on every response
- **Idempotency:** Mutating endpoints accept `Idempotency-Key` header
