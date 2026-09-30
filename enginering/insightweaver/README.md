# InsightWeaver Monorepo (Next.js + NestJS)

基于 pnpm + turborepo 的前后端同域项目，后端提供手机号验证码登录与积分账本，前端为 Next.js App Router。

## 目录结构
- `apps/api`：NestJS API（认证、积分、健康检查）
- `apps/web`：Next.js 前端（登录、余额、流水、设置）
- `packages/db`：Prisma schema 与 client
- `packages/shared`：共享类型/常量（预留）
- `env/.env.*.example`：环境变量模板

## 环境要求
- Node.js 22.x（`engines: >=22 <23`）
- pnpm 9.x（建议：`corepack enable`）
- 远程 PostgreSQL（库：`insight_weaver`）
- 远程 Redis（Tair）

## 本地快速启动（必读）
1) 准备环境变量  
   - 复制示例：`cp env/.env.development.example .env`，按需修改。  
   - 关键项：  
     - DB/Redis：`DATABASE_URL`、`SHADOW_DATABASE_URL`（迁移需要）、`REDIS_URL`  
     - JWT：`JWT_ACCESS_SECRET`、`JWT_REFRESH_SECRET`、`JWT_ACCESS_TTL`、`JWT_REFRESH_TTL`  
     - 短信：`SMS_CODE_PEPPER`（必填，不然验证码流程报错）、`SMS_CODE_TTL`、`SMS_SEND_COOLDOWN_SECONDS`、`SMS_MAX_ATTEMPTS`、`ALLOW_TEST_SMS_CODE`（本地可设 true，用 000000 测试或用返回的 testCode）  
     - 阿里云短信（生产/联调时）：`ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`、`ALIYUN_SMS_SIGN_NAME`、`ALIYUN_SMS_TEMPLATE_CODE`  
     - 积分：`INTERNAL_GRANT_SECRET`（保护发放接口）、`CREDIT_COSTS_JSON`（扣费映射）  
     - 跨域：`WEB_ORIGIN`（默认 http://localhost:3100），`PORT`（API 端口，默认 8787）
   - 前端：`apps/web/.env.local` 中 `PORT=3100`、`NEXT_PUBLIC_API_BASE_URL=http://localhost:8787`（可复制 `apps/web/env.local.example`）

2) 安装依赖（根目录）  
   ```bash
   COREPACK_HOME=$PWD/.corepack PNPM_STORE_PATH=$PWD/.pnpm-store corepack pnpm install
   ```

3) 生成 Prisma Client（必要，node_modules 内无生成物）  
   ```bash
   TURBO_FORCE=1 pnpm db:generate
   # 如需迁移：pnpm db:migrate
   ```

4) 启动 API（NestJS）  
   ```bash
   cd apps/api
   pnpm dev   # 使用 ts-node/esm，读取根 .env
   ```

5) 启动 Web（Next.js 15）  
   ```bash
   cd apps/web
   pnpm dev   # 读取 .env.local，默认端口 3100
   ```

默认前端 http://localhost:3100，API http://localhost:8787，跨域已在 API 启动时开启（`WEB_ORIGIN` 需与前端地址一致）。

## 主要功能
- 手机号验证码登录：`POST /api/auth/sms/send`、`POST /api/auth/sms/verify`；`/api/auth/me` 获取当前用户（包含余额）
- Token 轮换：`/api/auth/refresh`、`/api/auth/logout`
- 健康检查：`/api/healthz`、`/api/readyz`
- 积分：
  - 流水：`GET /api/credits/ledger`
  - 发放：`POST /api/credits/grant`（需 `X-Internal-Secret` + `Idempotency-Key`）
  - 扣减：`POST /api/credits/debit`（需登录 + `Idempotency-Key`，扣费来自 `CREDIT_COSTS_JSON`）

## 前端路由
- `/login`：手机号验证码登录
- `/app`：控制台（显示余额）
- `/app/credits`：积分流水
- `/settings`：账号信息
- Middleware：未登录访问 `/app*`、`/settings*` 会跳转 `/login`

## 常见问题
- **引擎警告（Node 版本）**：确保使用 Node 22，避免 pnpm “Unsupported engine” 警告。
- **Prisma 迁移**：生成迁移需 `SHADOW_DATABASE_URL`。运行：`corepack pnpm --filter @insightweaver/db db:migrate --name <change>`.
- **短信测试**：非生产可设置 `ALLOW_TEST_SMS_CODE=true` 使用万能码 `000000`；生产请关闭并使用阿里云短信。
- **幂等**：发放/扣减接口需 `Idempotency-Key`，相同键防重复。

## 构建
```bash
corepack pnpm --filter @insightweaver/api build
corepack pnpm --filter @insightweaver/web build
```
