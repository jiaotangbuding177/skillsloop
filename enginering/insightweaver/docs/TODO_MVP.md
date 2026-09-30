# InsightWeaver TODO（MVP：Next.js + NestJS + 远程 RDS/Tair）

> 前后端同域名，通过 `/api/*` 前缀分流；本地不启动 Postgres/Redis，直接连接远程 RDS PostgreSQL 与 Tair Redis。

## 1. 仓库与工程
- 初始化仓库：创建 monorepo（`pnpm + turborepo`），目录 `apps/web`、`apps/api`、`packages/db`、`packages/shared`
- 锁定版本：配置 `node@22`、`pnpm@9`、TypeScript、ESLint/Prettier
- 环境变量：定义 `DATABASE_URL`（数据库 `insight_weaver`）、`REDIS_URL`（远程），并准备 dev/test/prod 的变量模板

## 2. 数据库（Prisma）
- Prisma 落地：在 `packages/db` 创建 `schema.prisma`（按方案模型），配置生成 client
- 数据库迁移：首次迁移 `prisma migrate dev --name init`（连接远程开发库）并验证建表成功

## 3. 后端（NestJS）
- NestJS 初始化：创建 `apps/api`（Nest v11），接入 PrismaClient（复用 `packages/db`）
- 全局规范：实现统一响应 envelope（`{code,message,data}`）与全局异常过滤器（映射错误码）
- requestId：实现 `X-Request-Id` 中间件（生成/透传）+ 日志带 `requestId`
- 健康检查：实现 `GET /api/healthz`、`GET /api/readyz`（DB `SELECT 1`、Redis `PING`）

## 4. 登录（手机号验证码）
- 短信模块：实现 `/api/auth/sms/send`（验证码生成+hash 存 Redis+频控）与 `/api/auth/sms/verify`（校验+失败次数+锁定）
- 测试万能码：实现 `ALLOW_TEST_SMS_CODE` 仅非生产生效（生产启动校验禁用）
- 用户体系：实现 `users` + `user_identities(provider=phone)` 创建/绑定（手机号规范化 E.164）
- Token 模块：实现 access/refresh JWT 签发与 Cookie 下发（属性按方案）
- refresh 轮换：实现 `/api/auth/refresh`（rotate on refresh、并发/重放策略）
- 登出：实现 `/api/auth/logout`（吊销 refresh + 清 cookie）
- 当前用户：实现 `GET /api/me`（JwtAuthGuard + status 校验）

## 5. 积分（账本化 + 按次扣费）
- 钱包初始化：用户首次创建时创建 `wallets(balance=0)`（事务）
- 积分发放：实现 `POST /api/credits/grant`（内部密钥 `INTERNAL_GRANT_SECRET`、Idempotency-Key、写账本+更新钱包+审计）
- 积分扣减：实现 `POST /api/credits/debit`（按次扣费：`CREDIT_COSTS_JSON`，事务锁钱包、余额不足 409/4001、幂等冲突 409/4002）
- 余额/流水：实现 `GET /api/auth/me` 返回余额、`GET /api/credits/ledger`（分页/排序）
- 软删除策略：实现 Prisma middleware 默认过滤（User/UserIdentity/RefreshToken），并确保账本/审计不删除

## 6. 前端（Next.js）
- Next.js 初始化：创建 `apps/web`（Next v15），实现路由 `/`、`/login`、`/app`、`/app/credits`、`/settings`
- Web 登录流程：`/login` 调用 `/api/auth/sms/*`，成功跳转 `/app`
- Web 路由保护：实现 `middleware.ts`（未登录访问 `/app/*`、`/settings*` 跳 `/login`）
- 前端调用封装：封装 API client（同域 `/api/*`，默认带 cookie）

## 7. OpenAPI
- OpenAPI：接入 `@nestjs/swagger`，导出 `GET /openapi.json`（非生产/受保护）

## 8. CI/CD 与部署（阿里云）
- CI：GitHub Actions（install/lint/typecheck/test/build）
- 镜像构建：为 `apps/web`、`apps/api` 添加 Dockerfile（Next standalone / Nest 多阶段），CI 构建并 push ACR（tag `git_sha` + `vX.Y.Z`）
- SAE 部署：创建 SAE 应用 `listenhub-web`、`listenhub-api`，配置环境变量（含 `SMS_CODE_PEPPER`、`CREDIT_COSTS_JSON`）
- ALB 路由：配置同域名路径分流：`/api/*` → api，其余 → web
- 发布策略：API 启动阶段执行 `prisma migrate deploy`（发布窗口 api 最小实例数=1）

## 9. 可观测
- 观测：输出 JSON 日志字段（`requestId/userId/idempotencyKey/status/latencyMs`），SLS 建索引并加基础告警
