# InsightWeaver（Next.js + NestJS：手机号登录 + 积分账本）技术方案

项目名：`InsightWeaver`
数据库名（PostgreSQL）：`insight_weaver`

适用场景：类似 listenhub.ai 的“登录后使用 + 积分体系（账本）”的 Web 应用；基础设施使用阿里云（SAE 为主）。

---

## 1. 目标与范围

## 1.1 版本选型（建议锁定）

> 版本以“稳定 + 长期维护”为原则；如你公司已有统一版本基线，以公司基线为准。

**运行时与包管理**
- Node.js：`v22 LTS`
- pnpm：`v9`
- TypeScript：`v5.6`
- Docker：`v27+`（用于 CI 构建镜像）

**前端**
- Next.js：`v15`（App Router）
- React：`v19`
- TailwindCSS：`v4`

**后端**
- NestJS：`v11`
- Passport（Nest 集成）：`@nestjs/passport v11` + `passport v0.7`
- JWT：`passport-jwt v4`（配合 `jsonwebtoken v9`）

**数据库与 ORM**
- PostgreSQL：`v16`（RDS）
- Prisma：`v6`
- Redis：`v7`（Tair）

**可观测（阿里云侧）**
- 日志：SLS（采集 stdout/stderr）
- APM：ARMS（NestJS/Node 监控）

**必须包含**
- Web 应用（SEO/SSR/登录后体验）
- 手机号验证码登录（阿里云短信）
- 积分体系（账本化、幂等、可审计）
- 阿里云 SAE 部署与 CI/CD

**基础设施（阿里云）**
- 计算：SAE（容器化）
- 镜像：ACR
- 数据库：RDS PostgreSQL
- 缓存：Tair（Redis）
- 日志：SLS
- 监控：ARMS（可选同时接入 Sentry）
- 入口：SLB/ALB（可选 WAF）
- 文件（可选）：OSS + CDN

---

## 2. 总体架构

**服务拆分（MVP）**
- `web`：Next.js（用户端）
- `api`：NestJS（认证、积分、审计、业务 API）

**可演进（后续）**
- `worker`：异步任务（定时任务、清理过期 refresh token、批处理发放等）
- `mq`：RocketMQ（或先用 Redis 队列/BullMQ）

**数据流（关键路径）**
- 登录：Web → API（短信校验）→ 签发 Token（Cookie/JWT）
- 积分：Web → API → 发放/扣减（写账本）→ 返回余额/流水（用于展示与审计）

---

## 3. 代码仓库（推荐单仓 Monorepo）

工具建议：`pnpm` + `turborepo`（或 Nx），统一构建/测试/发布并共享类型。

```
repo/
  apps/
    web/                # Next.js（用户端）
    api/                # NestJS（核心 API）
    worker/             # 可选：异步任务（后续）
  packages/
    db/                 # Prisma schema + migrations
    shared/             # 共享 DTO/常量/错误码/schema
    api-client/         # 可选：OpenAPI 生成的 TS client
  .github/workflows/    # CI/CD
```

**约定**
- 业务规则（积分、幂等、审计）只在 `apps/api`，避免分散在 BFF/前端。
- `apps/web` 只负责 UI 与调用后端。

---

## 4. 前端（Next.js）选型与实现要点

**推荐栈**
- Next.js App Router + TypeScript
- UI：TailwindCSS + 组件库（如 shadcn/ui）
- API 调用：封装 `fetch`/`axios`（建议 OpenAPI 生成 client）

**页面与路由**
- 见「页面与路由定义」。

**鉴权（Web 侧）**
- refresh token 放 `HttpOnly Secure SameSite=Lax` Cookie（由 API 设置）
- access token 可短期 cookie 或仅内存（由 API 颁发，web 透传 cookie 请求 API）

---

## 5. 页面与路由定义（Next.js App Router）

目标：第一版覆盖“手机号登录 + 积分体系（余额/流水展示与通用扣减）”，不包含后台、不包含充值、不包含第三方集成。

### 5.1 用户端页面（必做）
- `/`：主页（产品介绍 + 登录入口；已登录可展示余额摘要与快捷入口）
- `/login`：登录页（手机号 + 验证码）
- `/logout`：登出（触发 API `POST /auth/logout` 后跳转 `/`）
- `/app`：登录后首页（余额、流水入口、使用说明）
- `/app/credits`：积分余额 + 流水列表（分页、筛选 `reason/refType`）
- `/settings`：设置（账号信息、手机号展示、会话管理入口）
- `/settings/security`：安全设置（刷新会话、查看最近登录；MVP 可合并到 `/settings`）

### 5.2 错误与系统页（建议）
- `/403`：无权限（账户禁用/访问受限）
- `/404`：未找到
- `/500`：系统错误（展示 `requestId` 便于排障）

### 5.3 路由保护策略（建议）
- 公开路由：`/`、`/login`、`/403`、`/404`、`/500`
- 需登录：`/app/*`、`/settings*`
- 实现方式：
  - Next.js `middleware.ts`：根据 cookie 判断是否已登录（弱校验），未登录跳转 `/login`
  - 服务端兜底：所有敏感数据由 API 鉴权返回，前端只做 UX 级别拦截

### 5.4 URL 设计原则
- 登录后业务页面统一挂在 `/app/*`，便于后续扩展与权限控制
- 设置页统一挂在 `/settings*`
- 不在 URL 中暴露敏感标识（手机号等）

---

## 6. 后端（NestJS）认证与权限（贴合产品形态）

### 6.1 认证选型
- `@nestjs/passport` + `passport-jwt`
- Token：`access JWT (15–30min)` + `refresh token (7–30d, 轮换)`

### 6.2 手机号验证码登录
- `POST /auth/sms/send`：验证码写 Redis（含 IP/手机号/设备频控）
- `POST /auth/sms/verify`：校验通过后绑定/创建用户 → 签发 Token

### 6.4 短信登录细则（默认值，可调整）

**验证码**
- 形态：6 位数字
- TTL：5 分钟
- 验证失败上限：同一验证码 TTL 内最多 5 次；超过后锁定 10 分钟（返回 `429` + `2004 SMS_RATE_LIMITED`）

**发送频控（建议默认）**
- 同一手机号：
  - 发送冷却：60 秒内只能发送 1 次
  - 每小时最多 5 次
  - 每自然日最多 10 次
- 同一 IP：每小时最多 20 次
- 同一设备标识（可选，header `X-Device-Id`）：每小时最多 10 次

**Redis 存储（建议）**
- Key：
  - `sms:code:<phone>`：验证码 hash（TTL=300s）
  - `sms:attempts:<phone>`：失败次数（TTL=300s）
  - `sms:lock:<phone>`：验证锁定（TTL=600s）
  - `sms:cooldown:<phone>`：发送冷却（TTL=60s）
- Value：
  - 不存明文验证码；存 `sha256(code + SMS_CODE_PEPPER)`，校验时同样 hash

**测试环境“万能码”（默认）**
- 非生产允许：`ALLOW_TEST_SMS_CODE=true` 时验证码固定为 `000000`
- 生产强制禁用：生产环境忽略该开关或直接启动失败

### 6.5 Token/Session 细则（第一版定稿：Cookie-only）

**Token TTL（建议默认）**
- `JWT_ACCESS_TTL=900`（15 分钟）
- `JWT_REFRESH_TTL=1209600`（14 天）

**Cookie（同域名 + `/api/*` 前缀分流）**
- `access_token`：`HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=900`
- `refresh_token`：`HttpOnly; Secure; SameSite=Lax; Path=/api/auth/refresh; Max-Age=1209600`
- `Domain`：不设置（host-only）

**Refresh 轮换与吊销（建议默认）**
- refresh token 单次使用即轮换（rotate on refresh）
- DB 仅存 `refresh_tokens.tokenHash`（SHA-256），不存明文
- `/api/auth/refresh` 在事务内完成：校验 → 吊销旧 token → 写入新 token → 下发新 cookie

**并发与重放防护（建议默认）**
- 同一个 refresh token 并发刷新：只允许第一个成功，其余返回 `401` + `2002 TOKEN_EXPIRED`
- 已吊销 refresh token 再次被使用：记录审计日志（可选后续升级为吊销全会话）

### 6.3 权限（第一版最小化）
- 第一版如果没有后台管理与多角色需求，可先只做 `JwtAuthGuard`（登录即拥有基础权限）。
- 若需要区分普通用户/高级用户/封禁状态：在 `users.status` 上做服务端校验即可。
- 后续再引入 RBAC（`roles/permissions`）扩展。

---

## 7. 后端 API 契约（OpenAPI）与鉴权方式

### 7.1 OpenAPI 交付物
目标：让前端/后端/测试对接口达成一致，并支持生成 TS client。

**建议输出**
- OpenAPI 3.0/3.1 文档（JSON/YAML）：
  - `GET /openapi.json`（生产可只在内网或受保护）
  - 或通过 CI 导出到制品/仓库（例如 `packages/openapi/openapi.json`）
- Swagger UI（仅非生产或受保护）：
  - `GET /docs`

**NestJS 实现建议**
- 使用 `@nestjs/swagger` 生成 OpenAPI
- DTO 统一使用 `class-validator`/`class-transformer` 并在 Swagger 中体现

### 7.2 鉴权方式（Cookie vs Bearer）

第一版推荐以 Web 为主的 **Cookie Session（JWT in Cookie）**，并同时兼容 **Bearer** 以便未来扩展到多端/脚本调用。

#### A) Cookie（推荐给浏览器 Web）
- `refresh`：`HttpOnly Secure SameSite=Lax` Cookie（只能由服务端设置/更新）
- `access`：两种方式二选一
  1) access 也放 `HttpOnly` Cookie（实现最简单，前端无需管理 token）
  2) access 放内存，刷新时由后端返回（安全性更强但实现复杂）
- 优点：减少 XSS 风险、前端不接触 refresh
- 注意：同域名 + 路径前缀分流（`/api/*`）时最省心，通常不需要 CORS；跨域时才需要配置 `CORS + withCredentials`

#### B) Bearer（可选/为未来预留）
- Header：`Authorization: Bearer <access_token>`
- 适合：小程序/App/CLI/第三方调用
- 注意：refresh token 的下发/轮换策略需单独设计（可以继续用 cookie 或单独 refresh endpoint）

### 7.4 第一版决策：只做 Cookie Refresh（延后无 Cookie Refresh）
为降低第一版复杂度并减少安全风险，第一版做如下约束：
- `refresh_token` **仅**通过 `HttpOnly` Cookie 存储与轮换
- `POST /api/auth/refresh` **仅**接受 Cookie 中的 `refresh_token`
- 不实现“无 cookie 的 refresh”（例如 header/body 传 refresh token）的模式

**未来扩展（需要时再做）**
- 当你确实需要支持 App/CLI 这类无 cookie 场景，再新增一种 refresh 机制（例如 refresh token 存客户端安全存储，通过 header 发送），并配套：
  - refresh token 旋转、吊销、设备绑定（device id）、重放防护
  - 更严格的风控与审计（异常刷新频率、地理位置、UA 变化）

### 7.3 API 分组与最小接口清单（建议）

> 下面是第一版建议的“最小可用”接口集合；以 OpenAPI 固化字段与响应结构。
> 同域名 + 前缀分流方案下，所有接口实际路径为 `/api/*`（例如 `/api/auth/sms/send`）。

**Auth**
- `POST /auth/sms/send`：发送短信验证码（含频控）
- `POST /auth/sms/verify`：验证码登录/注册（返回用户信息 + 设置 cookie）
- `POST /auth/refresh`：刷新 access（轮换 refresh）
- `POST /auth/logout`：登出（吊销 refresh + 清 cookie）
- `GET /me`：当前用户信息

**Credits**
- `GET /credits/balance`：获取余额
- `GET /credits/ledger`：获取流水（分页）
- `POST /credits/grant`：发放积分（第一版建议仅内部调用或加服务端密钥保护）
- `POST /credits/debit`：扣减积分（通用扣减，幂等）

**Health**
- `GET /healthz`：健康检查（进程存活）
- `GET /readyz`：就绪检查（DB/Redis 可用）

### 7.5 OpenAPI DTO 细化（建议字段）

> 以下为第一版建议字段集合与示例，落地时用 `@nestjs/swagger` 的 DTO 固化。

**POST `/api/auth/sms/send`**
- Request body：
  - `phone`：string（建议 E.164，如 `+8613xxxx`；也可接受 11 位并在后端规范化）
- Response：
  - `data.cooldownSeconds`：number（默认 60）

**POST `/api/auth/sms/verify`**
- Request body：
  - `phone`：string
  - `code`：string（6 位）
- Response：
  - `Set-Cookie`：`access_token`、`refresh_token`
  - `data.user`：`{ id: string, status: string }`

**GET `/api/credits/ledger`（分页）**
- Query（page-based，默认按 `createdAt desc`）：
  - `page`：number（默认 1）
  - `pageSize`：number（默认 20，最大 100）
  - `reason`：string（可选）
  - `refType`：string（可选）
- Response：
  - `data.items`：流水数组
  - `data.page/pageSize/total`

**POST `/api/credits/debit`（按次扣费的通用扣减）**
- Headers（推荐）：
  - `Idempotency-Key`：string（必填；也可放 body，但 header 更通用）
- Request body：
  - `reason`：string（用于服务端查 `reason -> cost`）
  - `refType/refId`：string（可选，用于业务追踪）
- Response：
  - `data.balance`：扣减后的余额
  - `data.ledgerId`：本次流水 ID

**POST `/api/credits/grant`（受保护的发放接口）**
- 建议只用于内部/运营脚本，不对普通用户开放：
  - 方式 A：仅允许来自内网/白名单 IP（依赖网关能力）
  - 方式 B：增加 `X-Internal-Secret`（与 SAE 环境变量一致）
- Headers（推荐）：
  - `Idempotency-Key`：string（必填）
- Request body：
  - `userId`：string
  - `amount`：number（正整数）
  - `reason`：string（如 `signup_bonus`/`campaign`）
  - `refType/refId`：string（可选）

### 7.6 requestId 规范（建议）
- 网关层生成 `requestId`（UUID）并写入响应头：`X-Request-Id`
- 如果请求已带 `X-Request-Id` 则透传（便于链路追踪）
- 服务端日志必须包含 `requestId`（用于 SLS/ARMS 关联排障）

---

## 8. 错误码规范（API 统一返回）

### 8.1 响应 envelope（建议）
为便于前端与日志统一处理，建议使用统一结构：
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

### 8.2 code 约定（建议分段）
- `0`：成功
- `1xxx`：参数/校验错误（客户端可修复）
- `2xxx`：认证错误（未登录/登录过期/验证码错误）
- `3xxx`：授权错误（无权限/账号被封禁）
- `4xxx`：资源/业务状态错误（余额不足、幂等冲突、频控）
- `5xxx`：系统错误（依赖不可用、未知异常）

### 8.3 常用错误码（建议最小集合）
- `1001`：INVALID_ARGUMENT（参数错误）
- `1002`：VALIDATION_FAILED（校验失败）
- `2001`：UNAUTHORIZED（未登录/Token 无效）
- `2002`：TOKEN_EXPIRED（Token 过期）
- `2003`：SMS_CODE_INVALID（验证码错误）
- `2004`：SMS_RATE_LIMITED（短信频控）
- `3001`：FORBIDDEN（无权限）
- `3002`：ACCOUNT_DISABLED（账号已禁用）
- `4001`：INSUFFICIENT_CREDITS（余额不足）
- `4002`：IDEMPOTENCY_CONFLICT（同幂等键不同请求）
- `5000`：INTERNAL_ERROR（系统错误）
- `5001`：DEPENDENCY_UNAVAILABLE（DB/Redis/短信服务不可用）

### 8.4 HTTP 状态码建议
- `200/201`：成功
- `400`：参数错误（`100x`）
- `401`：未认证（`200x`）
- `403`：无权限/禁用（`300x`）
- `409`：幂等冲突（`4002`）
- `429`：频控/限流（`2004`/自定义）
- `500/503`：系统/依赖错误（`500x`）


---

## 9. 积分系统（账本化 + 幂等）

**强制原则**
- 余额变动必须写流水（ledger），余额只是快照（wallet）
- 所有外部触发必须幂等（`idempotency_key` 唯一索引）

### 9.1 数据表（最小集合建议）
- `users`
- `user_identities`（provider=phone）
- `wallets(user_id, balance, version)`
- `credit_ledger(id, user_id, delta, reason, ref_type, ref_id, idempotency_key, created_at)`
- `audit_logs(id, actor_user_id, action, resource_type, resource_id, meta, created_at)`
- `refresh_tokens(id, user_id, token_hash, revoked_at, expires_at, created_at)`（或存 Redis + DB）

### 9.2 初始积分来源（无充值版）
第一版不做充值时，积分来源通常有三种：
1) **注册赠送**：新用户注册后写一笔 `credit_ledger(+delta, reason=signup_bonus)`。
2) **活动发放**：后端提供受保护的“发放接口”（仅内部调用）或脚本（需审计与幂等）。
3) **管理员手工调整**：后续引入后台管理后再做。

### 9.3 扣减（通用扣减接口）
积分扣减不绑定特定业务。建议以“业务引用 + 幂等键”的方式实现通用扣减：
- 传入：`userId`、`delta`（负数）、`reason`、`ref_type/ref_id`、`idempotency_key`
- 在同一 DB 事务内：锁定 `wallets` 行 → 校验余额 → 写 `credit_ledger` → 更新 `wallets.balance`

### 9.4 扣费规则（按次扣费）
第一版采用**按次扣费**（per-call / per-action）：
- 每一次“可计费动作”对应一个固定扣减额度（例如 `COST_PER_ACTION=5`）
- 不依赖用量（token/时长/字数），便于保证一致性与对账

**实现建议**
- 在后端配置中维护 `reason -> cost` 的映射（例如 `consume_basic: 5`、`consume_pro: 20`），避免把 cost 写死在前端
- 扣费时由服务端决定 `delta = -cost`，客户端只传 `reason/ref_type/ref_id/idempotency_key`
- 并发一致性：扣费事务内 `SELECT ... FOR UPDATE` 锁定 `wallets` 行，确保不会超扣

### 9.5 幂等冲突与余额不足的行为定义（默认）

**幂等（idempotencyKey）**
- 同一个 `idempotencyKey` 重复请求且 payload 完全一致：返回第一次结果（200），不重复扣费/发放
- 同一个 `idempotencyKey` 重复请求但 payload 不一致：返回 `409` + `4002 IDEMPOTENCY_CONFLICT`

**余额不足**
- 返回：`409` + `4001 INSUFFICIENT_CREDITS`
- 前端交互（第一版无充值）：提示“积分不足”，给出可执行路径（例如联系管理员/申请发放/查看规则说明）

---

## 10. 数据库表结构（Prisma + PostgreSQL）

> 目标：覆盖第一版（手机号登录 + 积分账本），并为后续扩展保留空间。以下为推荐的最小集合与关键索引。

### 10.1 Prisma 模型（建议字段与索引）

#### User（用户）
- 主键：`id`（UUID）
- 关键字段：
  - `status`：`active|disabled`（封禁/停用）
  - `createdAt/updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）
- 关系：
  - 1:N `UserIdentity`
  - 1:1 `Wallet`
  - 1:N `CreditLedger`
  - 1:N `RefreshToken`
  - 1:N `AuditLog`（actor）

#### UserIdentity（身份绑定：手机号）
- 主键：`id`（UUID）
- 唯一约束（软删除友好）：
  - `provider + providerUserId + isDeleted` UNIQUE（保证“未删除”的绑定唯一；软删除后允许重新绑定）
- 建议字段：
  - `provider`：`phone`
  - `providerUserId`：手机号（建议存 E.164 格式，如 `+8613xxxx`）
  - `phoneMasked`：脱敏显示（可选）
  - `createdAt/updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）

#### RefreshToken（刷新令牌）
- 主键：`id`（UUID）
- 安全建议：
  - 只存 `tokenHash`（例如 SHA-256），不存明文
  - 支持轮换：每次刷新生成新 token，旧 token 标记 `revokedAt`
- 索引建议：
  - `userId` INDEX
  - `tokenHash` UNIQUE
  - `expiresAt` INDEX（便于清理）
  - `createdAt/updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）

#### Wallet（钱包余额快照）
- 主键：`userId`（与 User 1:1）
- 字段：
  - `balance`：BIGINT（建议用“积分最小单位”，避免浮点）
  - `version`：INT（可用于乐观锁；也可仅用 `SELECT ... FOR UPDATE`）
  - `createdAt/updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）
- 约束：
  - `balance >= 0`（可选 check constraint，或在事务里保证）

#### CreditLedger（积分账本流水）
- 主键：`id`（UUID）
- 字段：
  - `delta`：BIGINT（正为发放，负为扣减）
  - `reason`：字符串或枚举（如 `signup_bonus` / `consume` / `adjustment`）
  - `refType/refId`：业务引用（例如 `mcp_call`/`order`/`manual` 等，第一版可先泛化为字符串）
  - `idempotencyKey`：幂等键（必须）
  - `createdAt`
- 索引/约束：
  - `idempotencyKey` UNIQUE（防重复发放/扣减）
  - `userId, createdAt` INDEX（查流水列表）
  - `refType, refId` INDEX（按业务追踪）
  - `updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）

#### AuditLog（审计日志）
- 主键：`id`（UUID）
- 字段：
  - `actorUserId`：操作者（可以为系统操作，允许 NULL 或用 system user）
  - `action`：如 `auth.login`/`credits.grant`/`credits.debit`
  - `resourceType/resourceId`
  - `meta`：JSONB（脱敏）
  - `createdAt`
- 索引建议：
  - `actorUserId, createdAt` INDEX
  - `resourceType, resourceId` INDEX
  - `updatedAt`
  - `isDeleted`：软删除标志位（默认 `false`）

### 10.2 Prisma schema（示例骨架）

> 注意：这是“设计参考骨架”，便于你在落地时快速建模；字段可按业务调整（例如 enum、长度、nullable）。

```prisma
model User {
  id        String   @id @default(uuid())
  status    String   @default("active")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  isDeleted Boolean  @default(false)

  identities    UserIdentity[]
  wallet        Wallet?
  creditLedgers CreditLedger[]
  refreshTokens RefreshToken[]
  auditLogs     AuditLog[] @relation("AuditActor")
}

model UserIdentity {
  id             String   @id @default(uuid())
  userId         String
  provider       String
  providerUserId String
  phoneMasked    String?
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt
  isDeleted      Boolean  @default(false)

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerUserId, isDeleted])
  @@index([userId])
}

model RefreshToken {
  id        String   @id @default(uuid())
  userId    String
  tokenHash String   @unique
  revokedAt DateTime?
  expiresAt DateTime
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  isDeleted Boolean  @default(false)

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId])
  @@index([expiresAt])
}

model Wallet {
  userId    String   @id
  balance   BigInt   @default(0)
  version   Int      @default(0)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  isDeleted Boolean  @default(false)

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model CreditLedger {
  id             String   @id @default(uuid())
  userId         String
  delta          BigInt
  reason         String
  refType        String?
  refId          String?
  idempotencyKey String   @unique
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt
  isDeleted      Boolean  @default(false)

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId, createdAt])
  @@index([refType, refId])
}

model AuditLog {
  id           String   @id @default(uuid())
  actorUserId  String?
  action       String
  resourceType String?
  resourceId   String?
  meta         Json?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  isDeleted    Boolean  @default(false)

  actor User? @relation("AuditActor", fields: [actorUserId], references: [id], onDelete: SetNull)

  @@index([actorUserId, createdAt])
  @@index([resourceType, resourceId])
}
```

### 10.3 软删除策略与 Prisma 默认过滤（建议）

**软删除适用范围（建议默认）**
- 允许软删除（会设置 `isDeleted=true`）：
  - `users`（账号注销/合规要求）
  - `user_identities`（解绑/换绑手机号）
  - `refresh_tokens`（安全事件/主动登出）
- 不建议删除（字段存在但不使用软删；只追加）：
  - `credit_ledger`（账本流水必须可追溯）
  - `audit_logs`（审计日志必须可追溯）
  - `wallets`（余额快照通常不删；账号注销时可冻结）

**Prisma 默认过滤实现（示例）**
在 `PrismaClient` 初始化时，通过 middleware 对“可软删表”默认追加 `isDeleted=false`：
```ts
prisma.$use(async (params, next) => {
  const softDeleteModels = new Set(["User", "UserIdentity", "RefreshToken"]);
  if (!params.model || !softDeleteModels.has(params.model)) return next(params);
  if (!["findMany", "findFirst"].includes(params.action)) return next(params);

  params.args ??= {};
  params.args.where ??= {};
  if (params.args.where.isDeleted === undefined) params.args.where.isDeleted = false;
  return next(params);
});
```

**注意事项**
- `UserIdentity` 使用了 `@@unique([provider, providerUserId, isDeleted])`：查询“当前绑定”应带 `isDeleted=false`
- 对账本/审计不要做默认过滤（否则会影响历史追溯）

---

## 11. 数据库迁移策略（Prisma Migrate）

### 11.1 环境划分与迁移命令
- 本地开发：使用 `prisma migrate dev`（生成迁移 + 更新本地库）
- 预发/生产：使用 `prisma migrate deploy`（只应用已存在迁移，不生成新迁移）

### 11.2 迁移流程（推荐）
1) 开发阶段修改 `schema.prisma`
2) 执行 `prisma migrate dev --name <change>` 生成迁移并在本地验证
3) PR 合并后，CI 构建镜像（迁移文件随镜像发布或随代码发布）
4) 部署到 SAE 时，在 **API 服务启动阶段** 执行：
   - `prisma migrate deploy`
5) 迁移完成后再对外提供服务（确保 readiness 通过）

### 11.3 SAE 上如何避免“多实例同时迁移”
第一版建议采用 **方案 B（更易在 SAE 落地）**：
- API 启动时执行 `prisma migrate deploy`
- 发布窗口将 API 最小实例数设为 1，避免并发迁移；迁移成功并就绪后再扩容

> 需要更强控制时再升级到“方案 A：流水线单独迁移步骤 + 再滚动发布”。

### 11.4 兼容性与回滚策略
- 避免破坏性迁移：优先用“新增列（nullable）→ 回填 → 再加约束/去 nullable”的两阶段策略
- 对外接口改动遵循向后兼容：先写入新字段再读新字段
- 生产回滚：应用版本回滚不等于数据库回滚；迁移尽量设计为“向前兼容”，必要时做补偿迁移而不是硬回滚

### 11.5 数据清理与维护（建议）
- 定期清理过期 `refresh_tokens`（按 `expiresAt`）
- 审计日志与账本流水按合规要求保留（账本通常不删）

---
## 12. CI/CD（GitHub Actions 示例流程）

### 12.1 分支/发布策略
- PR：质量门禁（lint/typecheck/test/build）
- main：部署预发（可选）
- tag（`v*.*.*`）：部署生产

### 12.2 流水线阶段
**PR**
- `pnpm install`
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`（web/api）

**Release（tag）**
- 构建镜像：`web`、`api`（可选 worker）
- Push 到 ACR
- 调 SAE OpenAPI 更新应用版本（滚动发布）
- Smoke check：`GET /api/healthz`、`GET /api/readyz`、关键业务探针（可选）

### 12.4 镜像 tag 与回滚策略（建议默认）
- 镜像 tag：
  - 每次构建：`:<git_sha>`
  - 发版：`:vX.Y.Z`（与 git tag 对齐）
- 回滚：
  - SAE 回滚到上一个可用镜像 tag（建议固定回滚目标为上一个 `:vX.Y.Z`）
- 不建议生产依赖 `:latest`

### 12.5 Dockerfile 约定（建议）

**Next.js（standalone）**
- 使用 `next build` 的 standalone 输出（减小镜像体积）
- 多阶段构建：deps → builder → runner

**NestJS**
- 多阶段构建：deps → builder（`nest build`/`tsc`）→ runner（只带 `dist` + 生产依赖）

**Dockerfile 轮廓（示例）**

Next.js（standalone）：
```dockerfile
# deps
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm i --frozen-lockfile

# builder
FROM deps AS builder
COPY . .
RUN pnpm -C apps/web build

# runner
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./.next/static
COPY --from=builder /app/apps/web/public ./public
EXPOSE 3000
CMD ["node","server.js"]
```

NestJS：
```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm i --frozen-lockfile

FROM deps AS builder
COPY . .
RUN pnpm -C apps/api build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/api/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
EXPOSE 8080
CMD ["node","dist/main.js"]
```

> 以上是“轮廓示例”，monorepo 实际 COPY 路径可根据最终目录调整。

### 12.6 SAE 发布方式（建议默认）
第一版建议使用“镜像发布”：
1) CI 构建并推送镜像到 ACR（tag 使用 `:<git_sha>` / `:vX.Y.Z`）
2) CI 调用 SAE 的“应用更新/部署”接口，更新镜像地址并滚动发布

**参数清单（建议）**
- `AppId`：SAE 应用 ID（web/api 各一个）
- `ImageUrl`：ACR 完整镜像（包含 tag）
- `BatchWaitTime/MinReadyInstances`：滚动发布控制参数（按你的可用性目标设置）

> 具体调用命令可用阿里云控制台、阿里云 CLI 或 OpenAPI 实现；落地到项目时再把命令/脚本固化到 CI。

### 12.7 CI Secrets（最少）
- `ALIYUN_ACCESS_KEY_ID`
- `ALIYUN_ACCESS_KEY_SECRET`
- `ALIYUN_REGION`
- `ACR_REGISTRY`、`ACR_NAMESPACE`
- `SAE_APP_ID_WEB`、`SAE_APP_ID_API`

> 业务密钥（短信/JWT 等）不建议放 CI，统一放 SAE 环境变量。

---

## 13. 阿里云 SAE 部署（容器化）

### 13.1 资源准备
- ACR：创建命名空间与仓库
- RDS PostgreSQL：创建实例与库，配置白名单/VPC
- Tair Redis：创建实例
- SLS：日志项目与 Logstore（可选）
- ARMS：应用监控（可选）
- 域名与入口：ALB/SLB（同域名 + `/api/*` 前缀分流）

### 13.2 SAE 应用拆分
- `listenhub-web`：端口 `3000`
- `listenhub-api`：端口 `8080`

### 13.3 域名与路径前缀分流（同域名部署，方案 A）
目标：前后端使用同一域名，通过路径前缀区分（最省心的 Cookie/CORS 方案）。

**域名**
- `https://example.com`

**路径约定**
- 前端（Next.js）：`/`、`/app/*`、`/login`、`/settings/*`、错误页等
- 后端（NestJS API）：统一前缀 `/api/*`
  - 例如：`POST /api/auth/sms/send`、`GET /api/auth/me`
  - 健康检查：`GET /api/healthz`、`GET /api/readyz`

**网关/负载均衡（ALB/SLB）路由规则**
- Path 以 `/api/` 开头 → 转发到 `listenhub-api`（SAE 应用）
- 其他请求 → 转发到 `listenhub-web`（SAE 应用）

**好处**
- 同域名下 Cookie 默认即可工作，无需复杂 CORS 与跨域 credentials 配置
- 前端与后端共享一个 TLS 证书与一个入口，发布与运维更简单

### 13.4 环境变量（在 SAE 配置）
**通用**
- `NODE_ENV`
- `APP_BASE_URL`（例如 `https://example.com`）
- `API_BASE_URL`（例如 `https://example.com/api`）

**DB/Redis**
- `DATABASE_URL`
- `REDIS_URL`

**JWT**
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `JWT_ACCESS_TTL`
- `JWT_REFRESH_TTL`

**积分计费（按次）**
- `CREDIT_COSTS_JSON`（例如 `{\"consume_basic\":5,\"consume_pro\":20}`）

**短信**
- `ALIYUN_SMS_ACCESS_KEY_ID`
- `ALIYUN_SMS_ACCESS_KEY_SECRET`
- `SMS_SIGN`
- `SMS_TEMPLATE_ID`
- `SMS_CODE_PEPPER`（用于验证码 hash 的服务端 pepper）
- `ALLOW_TEST_SMS_CODE`（仅非生产：允许 `000000` 万能码）

**内部接口（可选）**
- `INTERNAL_GRANT_SECRET`（若启用 `/api/credits/grant` 的内部密钥保护）

> 第一版不包含第三方集成，因此无需配置相关回调或第三方密钥。

### 13.5 发布顺序与迁移
- 先发布 `api`（必要时执行 DB migration，例如 `prisma migrate deploy`）
- 再发布 `web`

### 13.6 健康检查与就绪检查（默认）
- `/api/healthz`（存活）：进程存活即返回 200
- `/api/readyz`（就绪）：满足以下条件返回 200，否则 503
  - DB：执行 `SELECT 1` 成功（建议超时 200ms，可调）
  - Redis：`PING` 成功（建议超时 100ms，可调）

### 13.7 日志结构化与 SLS 索引建议（默认）
建议服务端输出 JSON 日志（stdout），字段至少包含：
- `ts`、`level`、`msg`
- `requestId`（对应 `X-Request-Id`）
- `userId`（已登录时）
- `path`、`method`、`status`
- `latencyMs`
- `idempotencyKey`（涉及积分发放/扣减时）

SLS 索引建议（便于检索与统计）：
- 对 `requestId`、`userId`、`path`、`status`、`idempotencyKey` 建索引（键值索引或全文索引按团队习惯）

---

## 14. 安全与合规要点（必须落地）
- Token：refresh 放 HttpOnly Cookie；支持 refresh 轮换与吊销
- 短信：频控（IP/手机号/设备）、验证码 TTL、风控黑名单
- 积分：所有发放/扣减都要幂等；建议对“发放接口/脚本”写审计

---

## 15. 后续演进路线（可选）
- 引入 `worker` + MQ：承载定时任务、批处理发放、风控扫描等
- 更细粒度数据权限：RBAC + 资源级校验（owner/orgId）
- 灰度与多环境：dev/staging/prod 三套 SAE 应用与配置
