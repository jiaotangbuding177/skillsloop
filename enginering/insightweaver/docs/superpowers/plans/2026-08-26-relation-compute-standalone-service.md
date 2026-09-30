# relation-compute 独立服务（P1+P2 完全独立）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `.tmp/relation-compute/` 构建一个完全独立、可单独部署的 relation-compute 服务：承载 LLM 计算（v1 complete）+ relation_* 图数据存储 + 证据授权 + 图查询 + 智能分析（摘要/工作流/风险/问答）+ 后台状态页，evomind 后续通过 url+apikey 接入。

**Architecture:** 新建独立 NestJS 11 服务（与 evomind 技术栈一致，便于移植），自带 PostgreSQL（Prisma），部署 7 张 relation 表 + 3 张权限镜像表。上游 `.tmp/insightweaver/apps/api/src/relation-space/` 的核心服务（投影/查询/授权/语义AI/智能分析）按"逐文件复制 + 精确 diff"移植；evomind 专属逻辑（读 zclaw/组织源表、投影任务队列）不移植，由 evomind 侧后续通过 HTTP 调用替代。协议 v1（health/complete）保持路径与行为完全兼容，v2 新增 ingest/permissions/graph/intelligence/admin 五组端点。

**Tech Stack:** NestJS 11 + Prisma 5 + PostgreSQL 16 + class-validator/class-transformer + openai SDK（DashScope 兼容端点）+ node:test（tsx --test，与上游一致）+ Docker/docker-compose

**Spec:** `docs/superpowers/reports/2026-08-26-relation-compute-extraction-feasibility-review.md`（设计审核，用户已确认 P1+P2 范围）

## Global Constraints

- 上游源码位置：`.tmp/insightweaver/`（只读参照，绝不修改）；新服务全部文件创建在 `D:\AWORKSPACE\insightweaver\.tmp\relation-compute\`
- 版本对齐 evomind：`@nestjs/*` ^11.1.9、`typescript` ^5.6.3、`openai` ^4.104.0、`class-validator` ^0.14.3、`class-transformer` ^0.5.1、`reflect-metadata` ^0.2.2、`rxjs` ^7.8.2
- 测试命令统一 `pnpm test`（`tsx --test src/**/*.test.ts`），测试风格照抄上游：直接 new 服务实例 + stub PrismaClient，不起 Nest 容器
- 所有端口路径前缀 `/api/internal/relation-compute/`；v1 路径与上游逐字节一致（`/v1/health`、`/v1/complete`）
- 鉴权：除 `GET /admin`（静态页壳）外全部端点要求 `Authorization: Bearer <RELATION_COMPUTE_SERVER_API_KEY>`，用 `timingSafeEqual` 比较
- 镜像授权 fail-closed：镜像行缺失 = 不可见，绝不放行
- 零新增业务语义：移植代码的行为与上游等价，仅替换数据来源（本地表 → payload / 镜像表）
- 每个任务结束跑 `pnpm test` + `pnpm exec tsc -p tsconfig.json --noEmit`（Task 1 建好脚手架后）
- Windows/bash 环境；目录创建用 `mkdir -p`；涉及 pnpm 的命令在 `.tmp/relation-compute/` 内执行

---

## Task 1: 项目脚手架 + Prisma schema + 本地数据库

**Files:**
- Create: `.tmp/relation-compute/package.json`
- Create: `.tmp/relation-compute/tsconfig.json`
- Create: `.tmp/relation-compute/.env.example`
- Create: `.tmp/relation-compute/.gitignore`
- Create: `.tmp/relation-compute/prisma/schema.prisma`
- Create: `.tmp/relation-compute/docker-compose.yml`（仅 postgres，服务容器在 Task 9 加）
- Create: `.tmp/relation-compute/src/main.ts`（最小占位，Task 2 重写）

**Interfaces:**
- Consumes: 无
- Produces: 可运行的 pnpm 项目；PrismaClient 带 7 个 relation 模型 + 3 个 mirror 模型；`pnpm exec prisma migrate dev` 可对本地 PG 建表

- [ ] **Step 1: 创建项目骨架**

`.tmp/relation-compute/package.json`：

```json
{
  "name": "relation-compute-service",
  "private": true,
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/main.ts",
    "build": "tsc -p tsconfig.json",
    "start": "node dist/main.js",
    "test": "tsx --test src/**/*.test.ts",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "db:migrate": "prisma migrate dev",
    "db:deploy": "prisma migrate deploy"
  },
  "dependencies": {
    "@nestjs/common": "^11.1.9",
    "@nestjs/config": "^4.0.2",
    "@nestjs/core": "^11.1.9",
    "@nestjs/platform-express": "^11.1.9",
    "@prisma/client": "^5.22.0",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.3",
    "openai": "^4.104.0",
    "reflect-metadata": "^0.2.2",
    "rxjs": "^7.8.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^22.10.2",
    "prisma": "^5.22.0",
    "tsx": "^4.21.0",
    "typescript": "^5.6.3"
  }
}
```

`.tmp/relation-compute/tsconfig.json`：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "resolveJsonModule": true,
    "declaration": false,
    "sourceMap": true
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

`.tmp/relation-compute/.gitignore`：

```
node_modules/
dist/
.env
*.local
```

`.tmp/relation-compute/.env.example`：

```bash
# --- 必填 ---
DATABASE_URL="postgresql://relation:relation@localhost:5433/relation_brain?schema=public"
RELATION_COMPUTE_SERVER_API_KEY="change-me-to-a-long-random-string"
INSIGHTWEAVER_RELEASE_SHA="0000000000000000000000000000000000000000"
DASHSCOPE_API_KEY="sk-your-dashscope-key"

# --- 可选（有默认值） ---
PORT=8080
DASHSCOPE_MODEL="qwen-plus-latest"
DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- 集成测试（Task 10 用；不设则跳过集成测试） ---
# TEST_DATABASE_URL="postgresql://relation:relation@localhost:5433/relation_brain_test?schema=public"
```

`.tmp/relation-compute/docker-compose.yml`（本任务只含 DB）：

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: relation
      POSTGRES_PASSWORD: relation
      POSTGRES_DB: relation_brain
    ports:
      - "5433:5432"
    volumes:
      - relation-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U relation -d relation_brain"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  relation-pgdata:
```

- [ ] **Step 2: 写 Prisma schema**

`.tmp/relation-compute/prisma/schema.prisma` —— 7 张 relation 表从上游 `.tmp/insightweaver/packages/db/prisma/schema.prisma` **逐字段复制**（上游这 7 个模型没有外部 FK，可原样搬），再加 3 张镜像表：

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============ 从上游 schema.prisma 原样复制的 7 个模型 ============
// RelationNode / RelationEdge / RelationEvidence / RelationSessionDigest /
// RelationAnalysisSnapshot / RelationWorkstreamReview / RelationQuestionHistory
// （用 awk 从上游文件提取，命令见 Step 3；唯一允许的修改：删除无关注释行）

// ============ 新增：权限/成员镜像表（fail-closed 授权依据） ============

/// evomind 推送的企业成员镜像：授权（活跃成员）+ 工作流推断（姓名/部门/组别）双用途
model RelationMirrorMember {
  id           String   @id @default(uuid())
  enterpriseId String
  userId       String
  realName     String?
  department   String?
  role         String
  groups       Json?
  syncedAt     DateTime @updatedAt

  @@unique([enterpriseId, userId], map: "relation_mirror_members_enterprise_user_uq")
  @@index([userId], map: "relation_mirror_members_user_idx")
  @@index([enterpriseId], map: "relation_mirror_members_enterprise_idx")
  @@map("relation_mirror_members")
}

/// ragflow 文档可见性镜像：rule 由 evomind 侧预计算；grants 为显式授权 userId 列表
model RelationMirrorDocument {
  id           String   @id @default(uuid())
  documentId   String   @unique
  rule         String // 'enterprise_member' | 'owner_only' | 'denied'
  ownerUserId  String?
  enterpriseId String?
  grants       Json?
  syncedAt     DateTime @updatedAt

  @@map("relation_mirror_documents")
}

/// 共享工作区路径授权镜像：grants 为可读该路径的 userId 列表
model RelationMirrorSharedPath {
  id           String   @id @default(uuid())
  enterpriseId String
  path         String
  grants       Json?
  syncedAt     DateTime @updatedAt

  @@unique([enterpriseId, path], map: "relation_mirror_shared_paths_enterprise_path_uq")
  @@map("relation_mirror_shared_paths")
}
```

- [ ] **Step 3: 从上游提取 7 个模型并拼入 schema**

```bash
cd /d/AWORKSPACE/insightweaver/.tmp/relation-compute
for m in RelationNode RelationEdge RelationEvidence RelationSessionDigest RelationAnalysisSnapshot RelationWorkstreamReview RelationQuestionHistory; do
  awk "/^model $m \{/,/^\}$/" ../insightweaver/packages/db/prisma/schema.prisma >> prisma/schema.models.prisma
  echo "" >> prisma/schema.models.prisma
done
# 人工核对 prisma/schema.models.prisma 内容后，把整块插入 prisma/schema.prisma
# 的"从上游原样复制的 7 个模型"注释下方，然后删除 schema.models.prisma
```

核对要点：7 个模型的 `@@map` 表名与 `docs/superpowers/reports/2026-08-26-relation-space-db-upgrade.sql` 里的 CREATE TABLE 一致；RelationEdge/RelationEvidence 的 FK 只指向 RelationNode/RelationEdge（内部）；不出现 `users`/`enterprises`/`zclaw_sessions`/`ragflow_datasets` 的引用。

- [ ] **Step 4: 安装依赖 + 生成客户端 + 迁移**

```bash
cd /d/AWORKSPACE/insightweaver/.tmp/relation-compute
pnpm install
docker compose up -d postgres
cp .env.example .env
pnpm exec prisma migrate dev --name init
pnpm exec prisma generate
```

期望：迁移成功创建 10 张表（psql 或 `pnpm exec prisma db pull --print` 抽查）。

- [ ] **Step 5: 最小 main.ts 占位 + 类型检查**

`src/main.ts`（临时，Task 2 重写）：

```ts
console.log("relation-compute scaffold");
```

```bash
pnpm typecheck
```

期望：PASS。

- [ ] **Step 6: 提交**

```bash
cd /d/AWORKSPACE/insightweaver
git add .tmp/relation-compute/package.json .tmp/relation-compute/tsconfig.json \
        .tmp/relation-compute/.env.example .tmp/relation-compute/.gitignore \
        .tmp/relation-compute/prisma .tmp/relation-compute/docker-compose.yml \
        .tmp/relation-compute/src/main.ts
git commit -m "chore(relation-compute): scaffold standalone service with prisma schema + mirrors"
```

（注：`.tmp/` 当前未被主仓库跟踪——若 `.gitignore` 排除了它，则在 `.tmp/relation-compute/` 内执行 `git init` 建独立仓库后提交，后续任务同理。以 Task 1 实际执行时 `git check-ignore .tmp/relation-compute` 的结果为准，两条路线二选一并在整个计划中保持一致。）

---

## Task 2: 契约包（v1 原样 + v2 新增）+ ApiKey 守卫 + 服务引导 + v1 compute 端点

**Files:**
- Create: `.tmp/relation-compute/src/contract/index.ts`
- Create: `.tmp/relation-compute/src/contract/index.test.ts`
- Create: `.tmp/relation-compute/src/infra/api-key.guard.ts`
- Create: `.tmp/relation-compute/src/infra/database.module.ts`
- Create: `.tmp/relation-compute/src/compute/model-client.ts`
- Create: `.tmp/relation-compute/src/compute/compute.controller.ts`
- Create: `.tmp/relation-compute/src/compute/compute.module.ts`
- Create: `.tmp/relation-compute/src/app.module.ts`
- Modify: `.tmp/relation-compute/src/main.ts`（重写）
- Create: `.tmp/relation-compute/src/bootstrap.test.ts`

**Interfaces:**
- Consumes: Task 1 的 PrismaClient
- Produces:
  - `src/contract/index.ts` 导出：v1 全部符号（与上游 `@insightweaver/relation-contract` 同名同形）+ v2 类型 `RelationV2Space`、`ProjectFactRequest`、`ProjectFactResult`、`RetractRequest`、`PermissionSyncRequest`、`AdminStatusResponse` 等（后续任务逐一引用）
  - `ApiKeyGuard`（NestJS CanActivate，全局注册于各 controller）
  - 运行中的 HTTP 服务：`GET /api/internal/relation-compute/v1/health`（200 带 health 载荷）、`POST /api/internal/relation-compute/v1/complete`（透传 LLM）

- [ ] **Step 1: 契约文件**

`src/contract/index.ts`：把上游 `.tmp/insightweaver/packages/relation-contract/src/index.ts` **整文件复制**，然后在文件末尾追加 v2 类型：

```ts
// ===================== v2（图数据 / 授权 / 智能分析） =====================

export const RELATION_COMPUTE_PROTOCOL_V2_VERSION = "2.0.0" as const;

/** 与上游 relation-projection.types.ts 的 RelationSpaceInput 同形（JSON 传输） */
export type RelationV2Space =
  | { type: "personal"; ownerUserId: string }
  | { type: "enterprise"; enterpriseId: string; ownerUserId?: string | null };

export interface RelationV2NodeInput {
  identityKey: string;
  nodeType: string;
  displayName: string;
  canonicalName?: string | null;
  language?: string | null;
  properties?: Record<string, unknown> | null;
}

export interface RelationV2EdgeInput {
  edgeKey: string;
  relationType: string;
  factType: "system" | "extracted" | "inferred";
  weight?: number;
  confidence?: number;
  occurredAt?: string | null;
  validFrom?: string | null;
  validTo?: string | null;
  properties?: Record<string, unknown> | null;
}

export interface RelationV2EvidenceInput {
  evidenceKey: string;
  sourceType: string;
  sourceId: string;
  sourceVersion?: string | null;
  locator?: Record<string, unknown> | null;
  excerpt?: string | null;
  confidence?: number;
  occurredAt?: string | null;
  accessScope: "owner_only" | "enterprise_member" | "ragflow_document" | "shared_workspace_path";
  permissionSourceType?: string | null;
  permissionSourceId?: string | null;
  permissionVersion?: number | null;
}

export interface RelationV2FactInput {
  space: RelationV2Space;
  subject: RelationV2NodeInput;
  relation: RelationV2EdgeInput;
  object: RelationV2NodeInput;
  evidence: RelationV2EvidenceInput;
}

export interface RelationV2FactResult {
  index: number;
  ok: boolean;
  error?: string;
  spaceKey?: string;
  subjectNodeId?: string;
  objectNodeId?: string;
  edgeId?: string;
  evidenceId?: string;
}

export interface RelationV2IngestFactsRequest {
  facts: RelationV2FactInput[];
}

export interface RelationV2IngestFactsResponse {
  results: RelationV2FactResult[];
}

export interface RelationV2RetractRequest {
  space: RelationV2Space;
  sourceType: string;
  sourceIds: string[];
}

export interface RelationV2RetractResult {
  sourceId: string;
  retractedEvidenceCount: number;
  retractedEdgeCount: number;
  retractedNodeCount: number;
}

export interface RelationV2RetractResponse {
  results: RelationV2RetractResult[];
}

export interface RelationV2DigestMessageInput {
  id: string;
  role: "user" | "assistant";
  content: string;
  updatedAt: string; // ISO 8601
}

export interface RelationV2DigestRequest {
  actorUserId: string;
  sessionId: string;
  ownerUserId: string;
  title?: string | null;
  locale?: string | null;
  agentEnterpriseId?: string | null;
  publishToEnterprise?: boolean;
  enterpriseId?: string | null;
  messages: RelationV2DigestMessageInput[];
}
```

- [ ] **Step 2: 契约测试（先写，验证复制无漏）**

`src/contract/index.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import {
  RELATION_COMPUTE_PROTOCOL_VERSION,
  RELATION_COMPUTE_PROTOCOL_V2_VERSION,
  validateRelationComputeRequest,
  isCompatibleRelationComputeHealth,
  type RelationV2FactInput,
} from "./index.js";

test("v1 contract symbols survive the copy", () => {
  assert.equal(RELATION_COMPUTE_PROTOCOL_VERSION, "1.0.0");
  assert.equal(validateRelationComputeRequest({ responseType: "json", system: "s", content: "c" }).ok, true);
  assert.equal(isCompatibleRelationComputeHealth({
    ok: true, service: "insightweaver-relation-compute", protocolVersion: "1.0.0",
    releaseSha: "abc", capabilities: [], model: "m",
  }), true);
});

test("v2 fact input type accepts a full fact shape", () => {
  const fact: RelationV2FactInput = {
    space: { type: "enterprise", enterpriseId: "e1" },
    subject: { identityKey: "user:u1", nodeType: "person", displayName: "张三" },
    relation: { edgeKey: "k", relationType: "member_of", factType: "system" },
    object: { identityKey: "department:d1", nodeType: "department", displayName: "产研" },
    evidence: { evidenceKey: "ek", sourceType: "enterprise_department", sourceId: "d1", accessScope: "enterprise_member", permissionSourceType: "enterprise", permissionSourceId: "e1" },
  };
  assert.equal(fact.relation.factType, "system");
});

test("protocol v2 version is exported", () => {
  assert.equal(RELATION_COMPUTE_PROTOCOL_V2_VERSION, "2.0.0");
});
```

```bash
pnpm test -- src/contract/index.test.ts
```

期望：PASS（若 FAIL 说明 v1 复制缺符号，补齐后重跑）。

- [ ] **Step 3: ApiKey 守卫 + 数据库模块**

`src/infra/api-key.guard.ts`：

```ts
import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { timingSafeEqual } from "node:crypto";

@Injectable()
export class ApiKeyGuard implements CanActivate {
  constructor(private readonly config: ConfigService) {}

  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const expected = this.config.get<string>("RELATION_COMPUTE_SERVER_API_KEY")?.trim() ?? "";
    if (!expected) throw new UnauthorizedException("服务端未配置 API Key");
    const actual = String(request.headers.authorization ?? "").replace(/^Bearer\s+/i, "").trim();
    if (!actual) throw new UnauthorizedException("缺少 Bearer API Key");
    const left = Buffer.from(actual);
    const right = Buffer.from(expected);
    if (left.length !== right.length || !timingSafeEqual(left, right)) {
      throw new UnauthorizedException("API Key 不正确");
    }
    return true;
  }
}
```

`src/infra/database.module.ts`：

```ts
import { Global, Module } from "@nestjs/common";
import { PrismaClient } from "@prisma/client";

export const PRISMA_CLIENT = "PrismaClient";

@Global()
@Module({
  providers: [
    {
      provide: PRISMA_CLIENT,
      useFactory: () => new PrismaClient(),
      inject: [],
    },
  ],
  exports: [PRISMA_CLIENT],
})
export class DatabaseModule {}
```

- [ ] **Step 4: v1 compute 端点（模型客户端 + 控制器 + 模块）**

`src/compute/model-client.ts`：从上游 `.tmp/insightweaver/apps/relation-compute/src/model-client.ts` **整文件复制**（不改一字）。

`src/compute/compute.controller.ts`：

```ts
import { Body, Controller, Get, HttpCode, Injectable, Post, UseGuards } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import {
  RELATION_COMPUTE_CAPABILITIES,
  RELATION_COMPUTE_LIMITS,
  RELATION_COMPUTE_PROTOCOL_VERSION,
  RELATION_COMPUTE_SERVICE_NAME,
  validateRelationComputeRequest,
  type RelationComputeHealth,
  type RelationComputeResponse,
} from "../contract/index.js";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import { createModelCompletion } from "./model-client.js";

const V1 = "api/internal/relation-compute/v1";

@Injectable()
@Controller(V1)
@UseGuards(ApiKeyGuard)
export class ComputeController {
  private readonly health: RelationComputeHealth;
  private readonly completeFn: ReturnType<typeof createModelCompletion>;

  constructor(config: ConfigService) {
    const model = config.get<string>("DASHSCOPE_MODEL")?.trim() || "qwen-plus-latest";
    this.health = {
      ok: true,
      service: RELATION_COMPUTE_SERVICE_NAME,
      protocolVersion: RELATION_COMPUTE_PROTOCOL_VERSION,
      releaseSha: config.get<string>("INSIGHTWEAVER_RELEASE_SHA")?.trim() || "",
      capabilities: [...RELATION_COMPUTE_CAPABILITIES],
      model,
    };
    this.completeFn = createModelCompletion({
      apiKey: config.get<string>("DASHSCOPE_API_KEY")?.trim() || "",
      baseUrl: config.get<string>("DASHSCOPE_BASE_URL")?.trim() || "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model,
    });
  }

  @Get("health")
  healthEndpoint() {
    return this.health;
  }

  @Post("complete")
  @HttpCode(200)
  async complete(@Body() body: unknown) {
    const parsed = validateRelationComputeRequest(body);
    if (!parsed.ok) {
      return { statusCode: 400, message: parsed.error };
    }
    try {
      const result = await this.completeFn(parsed.value);
      const payload: RelationComputeResponse = {
        result,
        protocolVersion: RELATION_COMPUTE_PROTOCOL_VERSION,
        releaseSha: this.health.releaseSha,
        model: this.health.model,
      };
      return payload;
    } catch (error) {
      return {
        statusCode: 502,
        message: error instanceof Error ? error.message : String(error),
      };
    }
  }
}
```

注意：NestJS 校验管道在 Task 2 的 app 级别未启用前，`@Body() body: unknown` 直接拿原始 JSON；v1 端点自己用 `validateRelationComputeRequest` 校验（与上游 server.ts 行为一致：400/502 语义）。上游对非法 JSON/超大体返回非 2xx——为保持简单，非法体返回 400 载荷（`{statusCode:400,...}` 由 Nest 默认异常过滤器渲染为 400 响应时需抛异常）。**修正**：直接抛异常而非返回对象，把 `return { statusCode: 400, ... }` 换成 `throw new BadRequestException(parsed.error)`，`502` 同理换 `throw new BadGatewayException(...)`（顶部 import 补 `BadRequestException, BadGatewayException`）。

`src/compute/compute.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { ComputeController } from "./compute.controller.js";

@Module({
  controllers: [ComputeController],
})
export class ComputeModule {}
```

- [ ] **Step 5: app.module + main.ts**

`src/app.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { ComputeModule } from "./compute/compute.module.js";
import { DatabaseModule } from "./infra/database.module.js";

@Module({
  imports: [ConfigModule.forRoot({ isGlobal: true }), DatabaseModule, ComputeModule],
})
export class AppModule {}
```

`src/main.ts`（重写 Task 1 占位）：

```ts
import "reflect-metadata";
import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module.js";

function required(name: string) {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`缺少环境变量 ${name}`);
  return value;
}

const port = Number(process.env.PORT ?? "8080");
if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new Error("PORT 必须是有效端口");

required("DATABASE_URL");
required("RELATION_COMPUTE_SERVER_API_KEY");
required("INSIGHTWEAVER_RELEASE_SHA");
required("DASHSCOPE_API_KEY");

const app = await NestFactory.create(AppModule);
app.enableShutdownHooks();
await app.listen(port, "0.0.0.0");
console.log(JSON.stringify({ service: "relation-compute", port, protocol: "1.0.0+v2" }));
```

- [ ] **Step 6: 引导冒烟测试（起真服务、打真请求）**

`src/bootstrap.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";

test("server boots and v1 health/complete respond with apikey auth", async (t) => {
  process.env.RELATION_COMPUTE_SERVER_API_KEY = "test-key-1234567890";
  process.env.INSIGHTWEAVER_RELEASE_SHA = "deadbeef".repeat(5);
  process.env.DASHSCOPE_API_KEY = "sk-test";
  process.env.DATABASE_URL = process.env.DATABASE_URL ?? "postgresql://relation:relation@localhost:5433/relation_brain?schema=public";
  process.env.PORT = "18080";

  const { AppModule } = await import("./app.module.js");
  const { NestFactory } = await import("@nestjs/core");
  const app = await NestFactory.create(AppModule, { logger: false });
  await app.listen(18080, "127.0.0.1");
  t.after(() => app.close());

  const base = "http://127.0.0.1:18080/api/internal/relation-compute/v1";

  const unauthorized = await fetch(`${base}/health`);
  assert.equal(unauthorized.status, 401);

  const health = await fetch(`${base}/health`, {
    headers: { authorization: "Bearer test-key-1234567890" },
  });
  assert.equal(health.status, 200);
  const healthBody = await health.json();
  assert.equal(healthBody.ok, true);
  assert.equal(healthBody.protocolVersion, "1.0.0");
  assert.deepEqual(healthBody.capabilities.length > 0, true);

  // complete 走真实 LLM——测试里只验证鉴权与错误路径（假 key → 502）
  const bad = await fetch(`${base}/complete`, {
    method: "POST",
    headers: { authorization: "Bearer test-key-1234567890", "content-type": "application/json" },
    body: JSON.stringify({ responseType: "text", system: "s", content: "c" }),
  });
  assert.ok([200, 502].includes(bad.status), `unexpected status ${bad.status}`);
});
```

```bash
pnpm test -- src/bootstrap.test.ts
```

期望：PASS（PG 未起时 PrismaClient 懒连接不阻塞启动；若报连接错可先 `docker compose up -d postgres`）。

- [ ] **Step 7: 全量类型检查 + 提交**

```bash
pnpm typecheck && pnpm test
```

```bash
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): v1 compute endpoints + apikey guard + bootstrap"
```

---

## Task 3: 投影核心（原样移植）+ v2 ingest 端点

**Files:**
- Create: `.tmp/relation-compute/src/projection/relation-projection.types.ts`（上游原样复制）
- Create: `.tmp/relation-compute/src/projection/relation-projection.service.ts`（上游原样复制）
- Create: `.tmp/relation-compute/src/projection/ingest.controller.ts`
- Create: `.tmp/relation-compute/src/projection/ingest.dto.ts`
- Create: `.tmp/relation-compute/src/projection/projection.module.ts`
- Create: `.tmp/relation-compute/src/projection/relation-projection.service.test.ts`（上游对应测试适配）
- Create: `.tmp/relation-compute/src/projection/ingest.controller.test.ts`
- Modify: `.tmp/relation-compute/src/app.module.ts`（注册 ProjectionModule）

**Interfaces:**
- Consumes: Task 2 的 `PRISMA_CLIENT`、`ApiKeyGuard`；契约 v2 类型
- Produces:
  - `RelationProjectionService.projectFact(input: ProjectRelationFactInput)` —— 与上游签名/行为完全一致（Task 7 的智能分析直接调用）
  - `RelationProjectionService.retractSource(input: RetractRelationSourceInput)` / `retractOrphanNodes(space)` / `listActiveSourceIds(input)`
  - HTTP：`POST /v2/ingest/facts`、`POST /v2/ingest/retract`、`POST /v2/ingest/retract-orphan-nodes`、`GET /v2/ingest/source-ids`

- [ ] **Step 1: 原样复制两个上游文件**

```bash
cd /d/AWORKSPACE/insightweaver/.tmp/relation-compute
mkdir -p src/projection
cp ../insightweaver/apps/api/src/relation-space/relation-projection.types.ts src/projection/
cp ../insightweaver/apps/api/src/relation-space/relation-projection.service.ts src/projection/
```

**唯一允许的改动**：`relation-projection.types.ts` 第 1 行 `import type { Prisma } from "@prisma/client"` 保留（本服务有自己的 @prisma/client）；两个文件的相对导入路径 `./relation-projection.types.js` 不变（同目录布局）。

- [ ] **Step 2: 移植上游投影服务测试**

```bash
cp ../insightweaver/apps/api/src/relation-space/relation-projection.service.test.ts src/projection/
```

打开复制的测试，核对它 mock PrismaClient 的方式（stub `$transaction`/`relationNode.upsert` 等）。若它 import 了 evomind 专属模块（如 `../auth/...`），删除该 import 并替换为本地等价 stub。跑：

```bash
pnpm test -- src/projection/relation-projection.service.test.ts
```

期望：PASS（上游测试与实现同为本任务的复制件，语义未动）。

- [ ] **Step 3: ingest DTO**

`src/projection/ingest.dto.ts`：

```ts
import { Type } from "class-transformer";
import {
  ArrayMaxSize, ArrayMinSize, IsArray, IsIn, IsInt, IsObject, IsOptional,
  IsString, IsUUID, Max, Min, ValidateNested,
} from "class-validator";
import { RelationV2FactInput } from "../contract/index.js";

export class SpaceDto {
  @IsIn(["personal", "enterprise"])
  type!: "personal" | "enterprise";

  @IsOptional()
  @IsUUID("4")
  ownerUserId?: string;

  @IsOptional()
  @IsUUID("4")
  enterpriseId?: string;
}

export class IngestFactsDto {
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(500)
  @ValidateNested({ each: true })
  facts!: RelationV2FactInput[];
}

export class RetractDto {
  @ValidateNested()
  @Type(() => SpaceDto)
  space!: SpaceDto;

  @IsString()
  sourceType!: string;

  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(1000)
  @IsString({ each: true })
  sourceIds!: string[];
}

export class RetractOrphanNodesDto {
  @ValidateNested()
  @Type(() => SpaceDto)
  space!: SpaceDto;
}
```

- [ ] **Step 4: ingest 控制器**

`src/projection/ingest.controller.ts`：

```ts
import { Body, Controller, Get, Injectable, Post, Query, UseGuards } from "@nestjs/common";
import { Inject } from "@nestjs/common";
import type { PrismaClient } from "@prisma/client";
import {
  RelationV2FactResult,
  RelationV2IngestFactsResponse,
  RelationV2RetractResponse,
} from "../contract/index.js";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import { PRISMA_CLIENT } from "../infra/database.module.js";
import {
  RelationProjectionService,
} from "./relation-projection.service.js";
import type { RelationSpaceInput } from "./relation-projection.types.js";
import type { ProjectRelationFactInput } from "./relation-projection.types.js";

const V2 = "api/internal/relation-compute/v2/ingest";

@Injectable()
@Controller(V2)
@UseGuards(ApiKeyGuard)
export class IngestController {
  constructor(private readonly projection: RelationProjectionService) {}

  @Post("facts")
  async ingestFacts(@Body() dto: { facts: unknown[] }): Promise<RelationV2IngestFactsResponse> {
    const results: RelationV2FactResult[] = [];
    for (let index = 0; index < dto.facts.length; index += 1) {
      try {
        const fact = this.toFactInput(dto.facts[index]!);
        const outcome = await this.projection.projectFact(fact);
        results.push({ index, ok: true, ...outcome });
      } catch (error) {
        results.push({
          index,
          ok: false,
          error: (error instanceof Error ? error.message : String(error)).slice(0, 500),
        });
      }
    }
    return { results };
  }

  @Post("retract")
  async retract(@Body() dto: { space: RelationSpaceInput; sourceType: string; sourceIds: string[] }): Promise<RelationV2RetractResponse> {
    const results = [];
    for (const sourceId of dto.sourceIds) {
      const outcome = await this.projection.retractSource({
        space: dto.space,
        sourceType: dto.sourceType,
        sourceId,
      });
      results.push({ sourceId, ...outcome });
    }
    return { results };
  }

  @Post("retract-orphan-nodes")
  async retractOrphanNodes(@Body() dto: { space: RelationSpaceInput }) {
    return this.projection.retractOrphanNodes(dto.space);
  }

  @Get("source-ids")
  async sourceIds(
    @Query("spaceType") spaceType: "personal" | "enterprise",
    @Query("ownerUserId") ownerUserId: string | undefined,
    @Query("enterpriseId") enterpriseId: string | undefined,
    @Query("sourceType") sourceType: string,
  ) {
    const space: RelationSpaceInput =
      spaceType === "personal"
        ? { type: "personal", ownerUserId: ownerUserId! }
        : { type: "enterprise", enterpriseId: enterpriseId! };
    return { sourceIds: await this.projection.listActiveSourceIds({ space, sourceType }) };
  }

  /** 契约 v2（ISO 字符串日期/JSON 属性）→ 上游 ProjectRelationFactInput（Date/Prisma.JsonValue） */
  private toFactInput(raw: unknown): ProjectRelationFactInput {
    const value = raw as Record<string, any>;
    const space = value.space as RelationSpaceInput;
    const toNode = (node: any) => ({
      identityKey: node.identityKey,
      nodeType: node.nodeType,
      displayName: node.displayName,
      canonicalName: node.canonicalName ?? null,
      language: node.language ?? null,
      properties: node.properties ?? undefined,
    });
    const toDate = (input: unknown) =>
      typeof input === "string" && input ? new Date(input) : null;
    return {
      space,
      subject: toNode(value.subject),
      object: toNode(value.object),
      relation: {
        edgeKey: value.relation.edgeKey,
        relationType: value.relation.relationType,
        factType: value.relation.factType,
        weight: value.relation.weight,
        confidence: value.relation.confidence,
        occurredAt: toDate(value.relation.occurredAt),
        validFrom: toDate(value.relation.validFrom),
        validTo: toDate(value.relation.validTo),
        properties: value.relation.properties ?? undefined,
      },
      evidence: {
        evidenceKey: value.evidence.evidenceKey,
        sourceType: value.evidence.sourceType,
        sourceId: value.evidence.sourceId,
        sourceVersion: value.evidence.sourceVersion ?? null,
        locator: value.evidence.locator ?? undefined,
        excerpt: value.evidence.excerpt ?? null,
        confidence: value.evidence.confidence,
        occurredAt: toDate(value.evidence.occurredAt),
        accessScope: value.evidence.accessScope,
        permissionSourceType: value.evidence.permissionSourceType ?? null,
        permissionSourceId: value.evidence.permissionSourceId ?? null,
        permissionVersion: value.evidence.permissionVersion ?? null,
      },
    };
  }
}
```

`src/projection/projection.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { IngestController } from "./ingest.controller.js";
import { RelationProjectionService } from "./relation-projection.service.js";

@Module({
  controllers: [IngestController],
  providers: [RelationProjectionService],
  exports: [RelationProjectionService],
})
export class ProjectionModule {}
```

`src/app.module.ts` 的 imports 数组追加 `ProjectionModule`（对应 import 语句一并加）。

- [ ] **Step 5: ingest 控制器测试**

`src/projection/ingest.controller.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import { IngestController } from "./ingest.controller.js";
import { RelationProjectionService } from "./relation-projection.service.js";

function controllerWith(stub) {
  const service = new RelationProjectionService(stub as any);
  return new IngestController(service);
}

test("ingest facts returns per-fact results and isolates failures", async () => {
  const outcomes = [
    { spaceKey: "personal:u1", subjectNodeId: "n1", objectNodeId: "n2", edgeId: "e1", evidenceId: "v1" },
  ];
  let call = 0;
  const stub = {
    projectFact: async () => {
      call += 1;
      if (call === 1) return outcomes[0];
      throw new Error("boom");
    },
  };
  const controller = controllerWith(stub);
  const fact = (key: string) => ({
    space: { type: "personal", ownerUserId: "u1" },
    subject: { identityKey: "user:u1", nodeType: "person", displayName: "我" },
    relation: { edgeKey: key, relationType: "owns", factType: "system" },
    object: { identityKey: `agent:${key}`, nodeType: "agent", displayName: "a" },
    evidence: { evidenceKey: `ev-${key}`, sourceType: "personal_agent", sourceId: key, accessScope: "owner_only" },
  });
  const response = await controller.ingestFacts({ facts: [fact("k1"), fact("k2")] } as any);
  assert.equal(response.results.length, 2);
  assert.equal(response.results[0]!.ok, true);
  assert.equal(response.results[0]!.edgeId, "e1");
  assert.equal(response.results[1]!.ok, false);
  assert.equal(response.results[1]!.error, "boom");
});

test("toFactInput converts ISO dates to Date and keeps access scope", async () => {
  // 直接测私有转换：构造合法 fact 走 projectFact stub 捕获入参
  let captured: any;
  const stub = {
    projectFact: async (input: any) => {
      captured = input;
      return { spaceKey: "personal:u1", subjectNodeId: "n1", objectNodeId: "n2", edgeId: "e1", evidenceId: "v1" };
    },
  };
  const controller = controllerWith(stub);
  await controller.ingestFacts({
    facts: [{
      space: { type: "personal", ownerUserId: "u1" },
      subject: { identityKey: "user:u1", nodeType: "person", displayName: "我" },
      relation: { edgeKey: "k", relationType: "owns", factType: "system", occurredAt: "2026-08-26T10:00:00.000Z" },
      object: { identityKey: "agent:a", nodeType: "agent", displayName: "a" },
      evidence: { evidenceKey: "ev", sourceType: "personal_agent", sourceId: "a", accessScope: "owner_only", occurredAt: "2026-08-26T10:00:00.000Z" },
    }],
  } as any);
  assert.ok(captured.relation.occurredAt instanceof Date);
  assert.ok(captured.evidence.occurredAt instanceof Date);
  assert.equal(captured.evidence.accessScope, "owner_only");
});
```

```bash
pnpm test -- src/projection/ingest.controller.test.ts
```

期望：PASS。

- [ ] **Step 6: 类型检查 + 全量测试 + 提交**

```bash
pnpm typecheck && pnpm test
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): port projection core + v2 ingest endpoints"
```

---

## Task 4: 权限镜像 + 证据授权重写 + v2 permissions 端点

**Files:**
- Create: `.tmp/relation-compute/src/permissions/mirror.service.ts`
- Create: `.tmp/relation-compute/src/permissions/mirror.service.test.ts`
- Create: `.tmp/relation-compute/src/permissions/relation-evidence-authorization.service.ts`（重写版）
- Create: `.tmp/relation-compute/src/permissions/authorization.test.ts`
- Create: `.tmp/relation-compute/src/permissions/permissions.controller.ts`
- Create: `.tmp/relation-compute/src/permissions/permissions.module.ts`
- Modify: `.tmp/relation-compute/src/app.module.ts`（注册 PermissionsModule）
- Modify: `.tmp/relation-compute/src/contract/index.ts`（追加 PermissionSyncRequest 类型）

**Interfaces:**
- Consumes: `PRISMA_CLIENT`、`ApiKeyGuard`
- Produces（后续 Task 5/7 依赖）：
  - `RelationMirrorService.syncMembers(enterpriseId, members[])`（全量替换语义）、`syncDocuments(docs[])`、`syncSharedPaths(paths[])`
  - `RelationMirrorService.activeMembership(userId, enterpriseId): Promise<{ role: string; realName: string | null } | null>`
  - `RelationMirrorService.activeEnterpriseIds(userId): Promise<Set<string>>`
  - `RelationMirrorService.membersByUserIds(enterpriseId, userIds): Promise<Array<{ userId, realName, department, role, groups }>>`
  - `RelationEvidenceAuthorizationService.authorizedEvidenceIds(actorUserId, evidences)` —— 与上游同名同签名，行为等价（依据镜像表判定）
  - HTTP：`POST /api/internal/relation-compute/v2/permissions/sync`

- [ ] **Step 1: 契约追加类型**

在 `src/contract/index.ts` 末尾追加：

```ts
export interface RelationV2MirrorMemberInput {
  userId: string;
  realName?: string | null;
  department?: string | null;
  role: string;
  groups?: Array<{ id: string; name: string }>;
}

export interface RelationV2MirrorDocumentInput {
  documentId: string;
  rule: "enterprise_member" | "owner_only" | "denied";
  ownerUserId?: string | null;
  enterpriseId?: string | null;
  grants?: string[];
}

export interface RelationV2MirrorSharedPathInput {
  enterpriseId: string;
  path: string;
  grants: string[];
}

export interface RelationV2PermissionSyncRequest {
  members?: Array<{ enterpriseId: string; members: RelationV2MirrorMemberInput[] }>;
  documents?: RelationV2MirrorDocumentInput[];
  sharedPaths?: RelationV2MirrorSharedPathInput[];
}

export interface RelationV2PermissionSyncResponse {
  memberEnterpriseCount: number;
  memberCount: number;
  documentCount: number;
  sharedPathCount: number;
}
```

- [ ] **Step 2: 镜像服务（先写失败测试）**

`src/permissions/mirror.service.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import { RelationMirrorService } from "./mirror.service.js";

function stubPrisma(overrides: Record<string, unknown> = {}) {
  return {
    relationMirrorMember: {
      deleteMany: async () => ({ count: 0 }),
      createMany: async () => ({ count: 0 }),
      findFirst: async () => null,
      findMany: async () => [],
    },
    relationMirrorDocument: {
      deleteMany: async () => ({ count: 0 }),
      createMany: async () => ({ count: 0 }),
    },
    relationMirrorSharedPath: {
      deleteMany: async () => ({ count: 0 }),
      createMany: async () => ({ count: 0 }),
    },
    $transaction: async (fn: any) => fn({}),
    ...overrides,
  } as any;
}

test("syncMembers replaces all rows of the enterprise in one transaction", async () => {
  const calls: string[] = [];
  const prisma = stubPrisma({
    $transaction: async (fn: any) => fn({
      relationMirrorMember: {
        deleteMany: async (args: any) => { calls.push(`delete:${JSON.stringify(args.where)}`); return { count: 2 }; },
        createMany: async (args: any) => { calls.push(`create:${args.data.length}`); return { count: args.data.length }; },
      },
    }),
  });
  const service = new RelationMirrorService(prisma);
  const result = await service.syncMembers("e1", [
    { userId: "u1", role: "owner", realName: "张三", department: "产研" },
    { userId: "u2", role: "member", realName: "李四" },
  ]);
  assert.equal(result, 2);
  assert.equal(calls[0], 'delete:{"enterpriseId":"e1"}');
  assert.equal(calls[1], "create:2");
});

test("activeMembership returns null when mirror row is missing (fail-closed)", async () => {
  const prisma = stubPrisma({
    relationMirrorMember: { findFirst: async () => null, findMany: async () => [] },
  });
  const service = new RelationMirrorService(prisma);
  assert.equal(await service.activeMembership("u1", "e1"), null);
});

test("activeMembership returns role and realName from mirror", async () => {
  const prisma = stubPrisma({
    relationMirrorMember: {
      findFirst: async () => ({ userId: "u1", enterpriseId: "e1", role: "admin", realName: "张三", department: null, groups: [] }),
      findMany: async () => [],
    },
  });
  const service = new RelationMirrorService(prisma);
  const membership = await service.activeMembership("u1", "e1");
  assert.equal(membership?.role, "admin");
  assert.equal(membership?.realName, "张三");
});
```

```bash
pnpm test -- src/permissions/mirror.service.test.ts
```

期望：FAIL（模块不存在）。

- [ ] **Step 3: 实现镜像服务**

`src/permissions/mirror.service.ts`：

```ts
import { Inject, Injectable } from "@nestjs/common";
import type { Prisma, PrismaClient } from "@prisma/client";
import { PRISMA_CLIENT } from "../infra/database.module.js";
import type {
  RelationV2MirrorDocumentInput,
  RelationV2MirrorMemberInput,
  RelationV2MirrorSharedPathInput,
} from "../contract/index.js";

export interface MirrorMemberRow {
  userId: string;
  realName: string | null;
  department: string | null;
  role: string;
  groups: Array<{ id: string; name: string }>;
}

@Injectable()
export class RelationMirrorService {
  constructor(@Inject(PRISMA_CLIENT) private readonly prisma: PrismaClient) {}

  /** 全量替换该企业的成员镜像（evomind 保证推送完整列表） */
  async syncMembers(enterpriseId: string, members: RelationV2MirrorMemberInput[]) {
    return this.prisma.$transaction(async (tx: Prisma.TransactionClient) => {
      await tx.relationMirrorMember.deleteMany({ where: { enterpriseId } });
      if (members.length === 0) return 0;
      const result = await tx.relationMirrorMember.createMany({
        data: members.map((member) => ({
          enterpriseId,
          userId: member.userId,
          realName: member.realName ?? null,
          department: member.department ?? null,
          role: member.role,
          groups: (member.groups ?? []) as Prisma.InputJsonValue,
        })),
      });
      return result.count;
    });
  }

  async syncDocuments(documents: RelationV2MirrorDocumentInput[]) {
    for (const document of documents) {
      await this.prisma.relationMirrorDocument.upsert({
        where: { documentId: document.documentId },
        create: {
          documentId: document.documentId,
          rule: document.rule,
          ownerUserId: document.ownerUserId ?? null,
          enterpriseId: document.enterpriseId ?? null,
          grants: (document.grants ?? []) as Prisma.InputJsonValue,
        },
        update: {
          rule: document.rule,
          ownerUserId: document.ownerUserId ?? null,
          enterpriseId: document.enterpriseId ?? null,
          grants: (document.grants ?? []) as Prisma.InputJsonValue,
        },
      });
    }
    return documents.length;
  }

  async syncSharedPaths(paths: RelationV2MirrorSharedPathInput[]) {
    for (const item of paths) {
      await this.prisma.relationMirrorSharedPath.upsert({
        where: {
          enterpriseId_path: { enterpriseId: item.enterpriseId, path: item.path },
        },
        create: {
          enterpriseId: item.enterpriseId,
          path: item.path,
          grants: (item.grants ?? []) as Prisma.InputJsonValue,
        },
        update: { grants: (item.grants ?? []) as Prisma.InputJsonValue },
      });
    }
    return paths.length;
  }

  /** 活跃成员资格；镜像缺失返回 null（fail-closed） */
  async activeMembership(userId: string, enterpriseId: string) {
    return this.prisma.relationMirrorMember.findFirst({
      where: { userId, enterpriseId },
      select: { userId: true, enterpriseId: true, role: true, realName: true, department: true, groups: true },
    });
  }

  async activeEnterpriseIds(userId: string) {
    const rows = await this.prisma.relationMirrorMember.findMany({
      where: { userId },
      select: { enterpriseId: true },
    });
    return new Set(rows.map((row) => row.enterpriseId));
  }

  async membersByUserIds(enterpriseId: string, userIds: string[]): Promise<MirrorMemberRow[]> {
    if (userIds.length === 0) return [];
    const rows = await this.prisma.relationMirrorMember.findMany({
      where: { enterpriseId, userId: { in: userIds } },
    });
    return rows.map((row) => ({
      userId: row.userId,
      realName: row.realName,
      department: row.department,
      role: row.role,
      groups: Array.isArray(row.groups) ? (row.groups as Array<{ id: string; name: string }>) : [],
    }));
  }
}
```

- [ ] **Step 4: 授权服务重写（先写失败测试）**

`src/permissions/authorization.test.ts` —— 覆盖上游 `authorizedEvidenceIds` 的全部四类 accessScope + fail-closed：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import { RelationEvidenceAuthorizationService } from "./relation-evidence-authorization.service.js";

function evidence(overrides: Record<string, unknown>) {
  return {
    id: "ev1",
    spaceType: "enterprise",
    enterpriseId: "e1",
    ownerUserId: null,
    accessScope: "enterprise_member",
    permissionSourceType: "enterprise",
    permissionSourceId: "e1",
    locator: null,
    ...overrides,
  } as any;
}

function serviceWith(prismaOverrides: Record<string, unknown> = {}) {
  const prisma = {
    relationMirrorMember: {
      findMany: async () => [{ enterpriseId: "e1" }],
    },
    relationMirrorDocument: {
      findMany: async () => [],
    },
    relationMirrorSharedPath: {
      findMany: async () => [],
    },
    ...prismaOverrides,
  } as any;
  return new RelationEvidenceAuthorizationService(prisma);
}

test("owner_only evidence authorizes only the space owner", async () => {
  const service = serviceWith();
  const own = await service.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "owner_only", spaceType: "personal", ownerUserId: "u1" }),
    evidence({ id: "b", accessScope: "owner_only", spaceType: "personal", ownerUserId: "u2" }),
  ]);
  assert.deepEqual([...own].sort(), ["a"]);
});

test("enterprise_member evidence requires mirror membership and permission source = enterprise", async () => {
  const service = serviceWith();
  const ok = await service.authorizedEvidenceIds("u1", [
    evidence({ id: "a" }),
    evidence({ id: "b", permissionSourceId: "other" }),
  ]);
  assert.deepEqual([...ok], ["a"]);
});

test("enterprise_member fails closed when mirror membership missing", async () => {
  const service = serviceWith({
    relationMirrorMember: { findMany: async () => [] },
  });
  const ids = await service.authorizedEvidenceIds("u1", [evidence({ id: "a" })]);
  assert.deepEqual([...ids], []);
});

test("ragflow_document evidence follows mirror rule", async () => {
  const doc = (rule: string, extra: Record<string, unknown> = {}) => ({
    documentId: "d1", rule, ownerUserId: "u1", enterpriseId: "e1", grants: [], ...extra,
  });
  // enterprise_member 规则 + 成员镜像 → 可见
  const memberCase = serviceWith({
    relationMirrorDocument: { findMany: async () => [doc("enterprise_member")] },
  });
  assert.deepEqual([...await memberCase.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "ragflow_document", permissionSourceType: "ragflow_document", permissionSourceId: "d1" }),
  ])], ["a"]);

  // owner_only 规则：仅 owner 可见
  const ownerCase = serviceWith({
    relationMirrorDocument: { findMany: async () => [doc("owner_only", { ownerUserId: "u9" })] },
  });
  assert.deepEqual([...await ownerCase.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "ragflow_document", permissionSourceType: "ragflow_document", permissionSourceId: "d1" }),
  ])], []);

  // denied 规则：不可见
  const deniedCase = serviceWith({
    relationMirrorDocument: { findMany: async () => [doc("denied")] },
  });
  assert.deepEqual([...await deniedCase.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "ragflow_document", permissionSourceType: "ragflow_document", permissionSourceId: "d1" }),
  ])], []);

  // grants 显式授权：可见（即使规则是 owner_only）
  const grantCase = serviceWith({
    relationMirrorDocument: { findMany: async () => [doc("owner_only", { ownerUserId: "u9", grants: ["u1"] })] },
  });
  assert.deepEqual([...await grantCase.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "ragflow_document", permissionSourceType: "ragflow_document", permissionSourceId: "d1" }),
  ])], ["a"]);

  // 镜像缺行 → fail-closed
  const missingCase = serviceWith({
    relationMirrorDocument: { findMany: async () => [] },
  });
  assert.deepEqual([...await missingCase.authorizedEvidenceIds("u1", [
    evidence({ id: "a", accessScope: "ragflow_document", permissionSourceType: "ragflow_document", permissionSourceId: "d1" }),
  ])], []);
});

test("shared_workspace_path evidence requires mirror grants + membership", async () => {
  const base = evidence({
    id: "a",
    accessScope: "shared_workspace_path",
    permissionSourceType: "enterprise",
    permissionSourceId: "e1",
    locator: { path: "/shared/spec" },
  });
  const allowed = serviceWith({
    relationMirrorSharedPath: {
      findMany: async () => [{ enterpriseId: "e1", path: "/shared/spec", grants: ["u1"] }],
    },
  });
  assert.deepEqual([...await allowed.authorizedEvidenceIds("u1", [base])], ["a"]);

  const notGranted = serviceWith({
    relationMirrorSharedPath: {
      findMany: async () => [{ enterpriseId: "e1", path: "/shared/spec", grants: ["u2"] }],
    },
  });
  assert.deepEqual([...await notGranted.authorizedEvidenceIds("u1", [base])], []);
});
```

```bash
pnpm test -- src/permissions/authorization.test.ts
```

期望：FAIL。

- [ ] **Step 5: 实现授权服务（重写版）**

`src/permissions/relation-evidence-authorization.service.ts` —— 保持上游导出的接口 `RelationEvidenceAuthorizationRecord` 与方法 `authorizedEvidenceIds(actorUserId, evidences): Promise<Set<string>>` 同形，内部全部查镜像：

```ts
import { Inject, Injectable } from "@nestjs/common";
import type { Prisma, PrismaClient } from "@prisma/client";
import { PRISMA_CLIENT } from "../infra/database.module.js";

export interface RelationEvidenceAuthorizationRecord {
  id: string;
  spaceType: string;
  enterpriseId: string | null;
  ownerUserId: string | null;
  accessScope: string;
  permissionSourceType: string | null;
  permissionSourceId: string | null;
  locator: Prisma.JsonValue | null;
}

interface MirrorDocumentRow {
  documentId: string;
  rule: string;
  ownerUserId: string | null;
  enterpriseId: string | null;
  grants: Prisma.JsonValue | null;
}

interface MirrorSharedPathRow {
  enterpriseId: string;
  path: string;
  grants: Prisma.JsonValue | null;
}

@Injectable()
export class RelationEvidenceAuthorizationService {
  constructor(@Inject(PRISMA_CLIENT) private readonly prisma: PrismaClient) {}

  async authorizedEvidenceIds(
    actorUserId: string,
    evidences: RelationEvidenceAuthorizationRecord[],
  ) {
    if (evidences.length === 0) return new Set<string>();
    const enterpriseIds = [
      ...new Set(evidences.map((evidence) => evidence.enterpriseId).filter((value): value is string => Boolean(value))),
    ];
    const memberships = enterpriseIds.length
      ? await this.prisma.relationMirrorMember.findMany({
          where: { userId: actorUserId, enterpriseId: { in: enterpriseIds } },
          select: { enterpriseId: true },
        })
      : [];
    const activeEnterpriseIds = new Set(memberships.map((row) => row.enterpriseId));

    const documentIds = [
      ...new Set(
        evidences
          .filter(
            (evidence) =>
              evidence.accessScope === "ragflow_document" &&
              evidence.permissionSourceType === "ragflow_document",
          )
          .map((evidence) => evidence.permissionSourceId)
          .filter((value): value is string => Boolean(value)),
      ),
    ];
    const documents = documentIds.length
      ? await this.prisma.relationMirrorDocument.findMany({
          where: { documentId: { in: documentIds } },
        })
      : [];
    const documentsById = new Map(documents.map((row) => [row.documentId, row]));

    const pathKeys = [
      ...new Set(
        evidences
          .filter((evidence) => evidence.accessScope === "shared_workspace_path")
          .map((evidence) => this.locatorText(evidence.locator, "path"))
          .filter((value): value is string => Boolean(value)),
      ),
    ];
    const sharedPaths = pathKeys.length
      ? await this.prisma.relationMirrorSharedPath.findMany({
          where: {
            enterpriseId: { in: [...activeEnterpriseIds] },
            path: { in: pathKeys },
          },
        })
      : [];
    const sharedPathByKey = new Map(sharedPaths.map((row) => [`${row.enterpriseId}:${row.path}`, row]));

    const authorized = new Set<string>();
    for (const evidence of evidences) {
      if (evidence.accessScope === "owner_only") {
        if (evidence.spaceType === "personal" && evidence.ownerUserId === actorUserId) {
          authorized.add(evidence.id);
        }
        continue;
      }
      if (evidence.accessScope === "enterprise_member") {
        if (
          evidence.spaceType === "enterprise" &&
          evidence.enterpriseId &&
          activeEnterpriseIds.has(evidence.enterpriseId) &&
          evidence.permissionSourceType === "enterprise" &&
          evidence.permissionSourceId === evidence.enterpriseId
        ) {
          authorized.add(evidence.id);
        }
        continue;
      }
      if (evidence.accessScope === "ragflow_document") {
        const document = evidence.permissionSourceId
          ? documentsById.get(evidence.permissionSourceId)
          : null;
        if (document && this.canReadMirrorDocument(evidence, document, activeEnterpriseIds, actorUserId)) {
          authorized.add(evidence.id);
        }
        continue;
      }
      if (evidence.accessScope === "shared_workspace_path") {
        const path = this.locatorText(evidence.locator, "path");
        const row = path && evidence.enterpriseId
          ? sharedPathByKey.get(`${evidence.enterpriseId}:${path}`)
          : null;
        if (
          evidence.spaceType === "enterprise" &&
          evidence.enterpriseId &&
          path &&
          activeEnterpriseIds.has(evidence.enterpriseId) &&
          row &&
          this.grantList(row.grants).includes(actorUserId)
        ) {
          authorized.add(evidence.id);
        }
      }
    }
    return authorized;
  }

  private canReadMirrorDocument(
    evidence: RelationEvidenceAuthorizationRecord,
    document: MirrorDocumentRow,
    activeEnterpriseIds: Set<string>,
    actorUserId: string,
  ) {
    const grants = this.grantList(document.grants);
    if (grants.includes(actorUserId)) return true;
    if (document.rule === "denied") return false;
    if (document.rule === "enterprise_member") {
      return Boolean(
        evidence.spaceType === "enterprise" &&
          evidence.enterpriseId &&
          document.enterpriseId === evidence.enterpriseId &&
          activeEnterpriseIds.has(evidence.enterpriseId),
      );
    }
    if (document.rule === "owner_only") {
      return document.ownerUserId === actorUserId;
    }
    return false; // 未知规则 → fail-closed
  }

  private grantList(value: Prisma.JsonValue | null): string[] {
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  }

  private locatorText(locator: Prisma.JsonValue | null, key: string) {
    if (!locator || typeof locator !== "object" || Array.isArray(locator)) return null;
    const value = (locator as Record<string, Prisma.JsonValue>)[key];
    return typeof value === "string" && value.trim() ? value.trim() : null;
  }
}
```

- [ ] **Step 6: permissions 控制器 + 模块**

`src/permissions/permissions.controller.ts`：

```ts
import { Body, Controller, Injectable, Post, UseGuards } from "@nestjs/common";
import type {
  RelationV2PermissionSyncRequest,
  RelationV2PermissionSyncResponse,
} from "../contract/index.js";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import { RelationMirrorService } from "./mirror.service.js";

const V2 = "api/internal/relation-compute/v2/permissions";

@Injectable()
@Controller(V2)
@UseGuards(ApiKeyGuard)
export class PermissionsController {
  constructor(private readonly mirror: RelationMirrorService) {}

  @Post("sync")
  async sync(@Body() dto: RelationV2PermissionSyncRequest): Promise<RelationV2PermissionSyncResponse> {
    let memberCount = 0;
    for (const entry of dto.members ?? []) {
      memberCount += await this.mirror.syncMembers(entry.enterpriseId, entry.members ?? []);
    }
    const documentCount = await this.mirror.syncDocuments(dto.documents ?? []);
    const sharedPathCount = await this.mirror.syncSharedPaths(dto.sharedPaths ?? []);
    return {
      memberEnterpriseCount: dto.members?.length ?? 0,
      memberCount,
      documentCount,
      sharedPathCount,
    };
  }
}
```

`src/permissions/permissions.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { PermissionsController } from "./permissions.controller.js";
import { RelationMirrorService } from "./mirror.service.js";
import { RelationEvidenceAuthorizationService } from "./relation-evidence-authorization.service.js";

@Module({
  controllers: [PermissionsController],
  providers: [RelationMirrorService, RelationEvidenceAuthorizationService],
  exports: [RelationMirrorService, RelationEvidenceAuthorizationService],
})
export class PermissionsModule {}
```

`src/app.module.ts` imports 追加 `PermissionsModule`。

- [ ] **Step 7: 跑测试 + 提交**

```bash
pnpm test -- src/permissions && pnpm typecheck && pnpm test
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): permission mirrors + fail-closed evidence authorization + v2 sync endpoint"
```

---

## Task 5: 查询引擎移植 + v2 graph 端点

**Files:**
- Create: `.tmp/relation-compute/src/query/dto.ts`
- Create: `.tmp/relation-compute/src/query/relation-query.service.ts`（移植 + 2 处 diff）
- Create: `.tmp/relation-compute/src/query/query.controller.ts`
- Create: `.tmp/relation-compute/src/query/query.module.ts`
- Create: `.tmp/relation-compute/src/query/relation-query.service.test.ts`（上游测试适配）
- Modify: `.tmp/relation-compute/src/app.module.ts`（注册 QueryModule）

**Interfaces:**
- Consumes: `RelationEvidenceAuthorizationService`（Task 4）、`RelationMirrorService`（Task 4）、`PRISMA_CLIENT`、`ApiKeyGuard`
- Produces:
  - `RelationQueryService.subgraph(actorUserId, input)` / `.path` / `.timeline` / `.aiContext` / `.evidenceDetail` —— 与上游同名同签名，响应序列化逐字段一致（这是 evomind 前端无缝接入的契约）
  - HTTP：`GET /v2/graph/subgraph|path|timeline|context`、`GET /v2/graph/evidences/:evidenceId`（全部带 `actorUserId` 查询参数）

- [ ] **Step 1: 复制上游查询服务 + 应用 diff**

```bash
cp ../insightweaver/apps/api/src/relation-space/relation-query.service.ts src/query/
cp ../insightweaver/apps/api/src/relation-space/relation-query.service.test.ts src/query/ 2>/dev/null || true
```

对 `src/query/relation-query.service.ts` 应用**恰好 3 处 diff**（其余逐字保留，包括 `selectCoherentEdges`/`serializeNode`/`serializeEdge`/`loadAuthorizedEdges`/`evidenceWhere`）：

**Diff 1 —— import 与构造函数**（上游第 1-92 行区域）：

```ts
// 删除上游的 JwtAuthGuard / dto 导入；构造函数注入镜像服务：
import { RelationMirrorService } from "../permissions/mirror.service.js";
import { RelationEvidenceAuthorizationService } from "../permissions/relation-evidence-authorization.service.js";

  constructor(
    @Inject(PRISMA_CLIENT) private readonly prisma: PrismaClient,
    private readonly authorization: RelationEvidenceAuthorizationService,
    private readonly mirror: RelationMirrorService,
  ) {}
```

（上游构造函数原本就注入 `authorization`，保留；追加 `mirror`。）

**Diff 2 —— `resolveSpace` 中企业空间鉴权改走镜像**（上游第 705-714 行）：

```ts
    // 上游：
    // const membership = await this.prisma.enterpriseMembership.findFirst({
    //   where: { userId: actorUserId, enterpriseId, status: "active", isDeleted: false,
    //            enterprise: { status: "active", isDeleted: false } },
    //   select: { id: true },
    // });
    // if (!membership) throw new ForbiddenException("enterprise relation space unavailable");
    // 改为：
    const membership = await this.mirror.activeMembership(actorUserId, enterpriseId);
    if (!membership) throw new ForbiddenException("enterprise relation space unavailable");
```

**Diff 3 —— 文件顶部**：`import { PRISMA_CLIENT } from "../infra/database.module.js";` 替换上游的 `@Inject("PrismaClient")` 写法（上游就是 `@Inject("PrismaClient")`，改成本服务的 token 常量导入并把 `@Inject("PrismaClient")` 换成 `@Inject(PRISMA_CLIENT)`）。

- [ ] **Step 2: 查询 DTO（照上游 relation-query.dto.ts + actorUserId）**

`src/query/dto.ts`：从上游 `.tmp/insightweaver/apps/api/src/relation-space/dto/relation-query.dto.ts` 整文件复制，然后：
1. 文件末尾追加：

```ts
import { IsUUID } from "class-validator";

export function requireActorUserId(query: { actorUserId?: string }): string {
  const value = query.actorUserId?.trim();
  if (!value) throw new Error("actorUserId is required");
  return value;
}

declare module "./dto.js" {
  interface ActorQuery {
    actorUserId?: string;
  }
}
```

（简化实现：不改成声明合并——直接在 `RelationSubgraphQueryDto` / `RelationPathQueryDto` / `RelationTimelineQueryDto` 三个类里各加一个字段：）

```ts
  @IsUUID("4")
  actorUserId!: string;
```

2. `RelationPathQueryDto` 若上游放在别的 dto 文件，同样复制过来（核对上游 `relation-query.service.ts` 顶部 import 的 dto 来源文件，把 `RelationPathQueryDto` 一并搬进 `dto.ts`）。

- [ ] **Step 3: 控制器**

`src/query/query.controller.ts`：

```ts
import { Controller, Get, Injectable, Param, ParseUUIDPipe, Query, UseGuards } from "@nestjs/common";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import {
  RelationPathQueryDto,
  RelationSubgraphQueryDto,
  RelationTimelineQueryDto,
} from "./dto.js";
import { RelationQueryService } from "./relation-query.service.js";

const V2 = "api/internal/relation-compute/v2/graph";

@Injectable()
@Controller(V2)
@UseGuards(ApiKeyGuard)
export class QueryController {
  constructor(private readonly queries: RelationQueryService) {}

  @Get("subgraph")
  subgraph(@Query() query: RelationSubgraphQueryDto) {
    return this.queries.subgraph(query.actorUserId, query);
  }

  @Get("path")
  path(@Query() query: RelationPathQueryDto) {
    return this.queries.path(query.actorUserId, query);
  }

  @Get("timeline")
  timeline(@Query() query: RelationTimelineQueryDto) {
    return this.queries.timeline(query.actorUserId, query);
  }

  @Get("context")
  context(@Query() query: RelationSubgraphQueryDto) {
    return this.queries.aiContext(query.actorUserId, query);
  }

  @Get("evidences/:evidenceId")
  evidence(
    @Query("actorUserId") actorUserId: string,
    @Param("evidenceId", new ParseUUIDPipe({ version: "4" })) evidenceId: string,
  ) {
    return this.queries.evidenceDetail(actorUserId, evidenceId);
  }
}
```

`src/query/query.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { PermissionsModule } from "../permissions/permissions.module.js";
import { QueryController } from "./query.controller.js";
import { RelationQueryService } from "./relation-query.service.js";

@Module({
  imports: [PermissionsModule],
  controllers: [QueryController],
  providers: [RelationQueryService],
  exports: [RelationQueryService],
})
export class QueryModule {}
```

`src/app.module.ts` imports 追加 `QueryModule`。

- [ ] **Step 4: 移植/适配查询测试**

若 Step 1 复制到 `relation-query.service.test.ts`：打开并做两类适配：
1. 构造服务处补第三个参数：`new RelationQueryService(prismaStub, authorizationStub, mirrorStub)`；`mirrorStub = { activeMembership: async () => ({ role: "member", realName: null }) }`
2. 原测试里 mock `prisma.enterpriseMembership.findFirst` 的用例，改为断言 `mirror.activeMembership` 被调用/返回 null 时抛 Forbidden

若上游测试依赖 evomind 专属工具（如 ZclawService），删除该依赖项相关用例并在提交信息里注明。

```bash
pnpm test -- src/query && pnpm typecheck
```

- [ ] **Step 5: 提交**

```bash
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): port query engine + v2 graph endpoints (mirror-based space auth)"
```

---

## Task 6: 语义 AI 移植（LLM 直连）

**Files:**
- Create: `.tmp/relation-compute/src/intelligence/relation-semantic-ai.service.ts`
- Create: `.tmp/relation-compute/src/intelligence/relation-semantic-ai.service.test.ts`（上游测试适配）
- Modify: `.tmp/relation-compute/src/app.module.ts`（暂不注册——Task 7 随 IntelligenceModule 一起）

**Interfaces:**
- Consumes: `ConfigService`（DASHSCOPE_* 环境变量）
- Produces:
  - `RelationSemanticAiService`，与上游公开方法完全同名同签名：`summarizeSession`、`consolidateActivities`、`consolidateArtifacts`、`inferWorkstreams`、`normalizeBusinessObjects`、`modelName()`、以及常量 `RELATION_SESSION_PROMPT_VERSION` 等 5 个版本常量
  - 移除项（不再存在）：`completeLocally` 的 remote 分支、`RelationComputeConfigService` 依赖

- [ ] **Step 1: 复制 + 应用 diff**

```bash
cp ../insightweaver/apps/api/src/relation-space/relation-semantic-ai.service.ts src/intelligence/
cp ../insightweaver/apps/api/src/relation-space/relation-semantic-ai.service.test.ts src/intelligence/ 2>/dev/null || true
```

对 `relation-semantic-ai.service.ts` 应用**恰好 2 处 diff**：

**Diff 1 —— 删除 remoteCompute 依赖**（上游第 4 行 import 与第 95 行构造参数）：

```ts
// 删除：import { RelationComputeConfigService } from "./relation-compute-config.service.js";
// 构造函数改为：
  constructor(config: ConfigService) {
    this.model = config.get<string>("DASHSCOPE_MODEL") ?? "qwen-plus-latest";
    const apiKey = config.get<string>("DASHSCOPE_API_KEY")?.trim();
    const baseURL = config.get<string>("DASHSCOPE_BASE_URL")?.trim();
    this.client = apiKey && baseURL ? new OpenAI({ apiKey, baseURL }) : null;
  }
```

**Diff 2 —— `completeText`/`completeJson` 删远程分支**（上游第 1573-1602 行）：

```ts
  private async completeText(system: string, content: string) {
    const answer = await this.completeTextLocally(system, content);
    return answer;
  }

  private async completeJson(system: string, content: string): Promise<Record<string, unknown>> {
    return this.completeJsonLocally(system, content);
  }
```

（`completeTextLocally`/`completeJsonLocally` 与全部 prompt 构造/normalize 方法**逐字保留**。）

- [ ] **Step 2: 适配测试并跑**

上游 `relation-semantic-ai.service.test.ts` 若构造服务时传了第二参数（remoteCompute mock），删掉；其余（mock OpenAI client 断言 prompt/解析）应原样通过：

```bash
pnpm test -- src/intelligence/relation-semantic-ai.service.test.ts && pnpm typecheck
```

- [ ] **Step 3: 提交**

```bash
git add .tmp/relation-compute/src/intelligence
git commit -m "feat(relation-compute): port semantic AI service (direct LLM, no remote compute hop)"
```

---

## Task 7: 工作智能移植 + v2 intelligence 端点

**Files:**
- Create: `.tmp/relation-compute/src/intelligence/relation-work-intelligence.service.ts`（移植 + 精确 diff 清单）
- Create: `.tmp/relation-compute/src/intelligence/intelligence.controller.ts`
- Create: `.tmp/relation-compute/src/intelligence/intelligence.module.ts`
- Create: `.tmp/relation-compute/src/intelligence/relation-work-intelligence.service.test.ts`（上游测试适配）
- Create: `.tmp/relation-compute/src/intelligence/intelligence.controller.test.ts`
- Modify: `.tmp/relation-compute/src/app.module.ts`（注册 IntelligenceModule）
- Modify: `.tmp/relation-compute/src/contract/index.ts`（追加 DigestRequest 相关已在前文；此处如缺 ask/review 请求类型则补）

**Interfaces:**
- Consumes: `RelationProjectionService`（Task 3）、`RelationQueryService`（Task 5）、`RelationSemanticAiService`（Task 6）、`RelationMirrorService`（Task 4）、`PRISMA_CLIENT`
- Produces:
  - `RelationWorkIntelligenceService`：`generateSessionDigest(input)`（payload 版）、`getSessionDigest`、`rebuildEnterpriseWorkstreams`、`listWorkstreamReviews`、`reviewWorkstream`、`analyzeEnterpriseRisks`、`getEnterpriseRiskAnalysis`、`refreshEnterpriseRiskAnalysis`、`askEnterpriseQuestion`、`listEnterpriseQuestionHistory`
  - HTTP：`POST /v2/intelligence/digest`、`GET /v2/intelligence/digests/:sessionId`、`GET /v2/intelligence/digests/status`、`POST /v2/intelligence/workstreams/rebuild`、`GET|POST /v2/intelligence/workstreams/reviews`、`GET /v2/intelligence/risks`、`GET /v2/intelligence/risk-analysis`、`POST /v2/intelligence/risk-analysis/refresh`、`POST /v2/intelligence/ask`、`GET /v2/intelligence/questions/history`

- [ ] **Step 1: 复制上游文件**

```bash
cp ../insightweaver/apps/api/src/relation-space/relation-work-intelligence.service.ts src/intelligence/
cp ../insightweaver/apps/api/src/relation-space/relation-work-intelligence.service.test.ts src/intelligence/ 2>/dev/null || true
```

- [ ] **Step 2: 应用 diff 清单（共 10 处，逐处核对）**

**Diff 1 —— import 区 + 构造函数**：删除 `RelationIdentityProjectionService` import 与注入；追加 `RelationMirrorService` 注入；`RelationSemanticAiService`/`RelationProjectionService`/`RelationQueryService` 保留：

```ts
  constructor(
    @Inject(PRISMA_CLIENT) private readonly prisma: PrismaClient,
    private readonly ai: RelationSemanticAiService,
    private readonly projection: RelationProjectionService,
    private readonly queries: RelationQueryService,
    private readonly mirror: RelationMirrorService,
  ) {}
```

**Diff 2 —— `generateSessionDigest` 改 payload 输入**（上游第 66-97 行替换为）：

```ts
  async generateSessionDigest(input: {
    actorUserId: string;
    sessionId: string;
    ownerUserId: string;
    title?: string | null;
    locale?: string | null;
    agentEnterpriseId?: string | null;
    publishToEnterprise?: boolean;
    enterpriseId?: string | null;
    messages: Array<{ id: string; role: string; content: string; updatedAt: Date }>;
  }) {
    const actorUserId = this.requireText(input.actorUserId, "actorUserId");
    const sessionId = this.requireText(input.sessionId, "sessionId");
    if (!Array.isArray(input.messages) || input.messages.length === 0) {
      throw new BadRequestException("会话尚无可分析的完成态消息");
    }
    const messages = input.messages.filter(
      (message) => STABLE_ROLES.has(message.role) && message.content.trim(),
    );
    if (messages.length === 0) throw new BadRequestException("会话尚无可分析的完成态消息");
    const session = {
      id: sessionId,
      userId: this.requireText(input.ownerUserId, "ownerUserId"),
      title: input.title ?? null,
      locale: input.locale ?? null,
      agentInstance: { enterpriseId: input.agentEnterpriseId ?? null },
      messages,
    };
    const enterpriseId = input.publishToEnterprise
      ? this.requireText(input.enterpriseId ?? session.agentInstance.enterpriseId ?? undefined, "enterpriseId")
      : null;
    if (enterpriseId) await this.assertActiveMembership(actorUserId, enterpriseId);
    // ↑ 以下接上游第 98 行起的 sourceVersion/previousCurrent/生成/投影逻辑，逐字保留
```

（上游第 98-184 行逐字保留：`sessionSourceVersion`、摘要复用/生成事务、旧摘要 retract、`projectDigest` 双空间投影、返回值。）

**Diff 3 —— `getSessionDigest` 删会话属主校验**（上游第 186-197 行）：

```ts
  async getSessionDigest(actorUserId: string, sessionId: string) {
    sessionId = this.requireText(sessionId, "sessionId");
    // 上游的 zclawSession.findFirst 属主校验由 evomind 调用方负责，这里直接查摘要
    const digest = await this.prisma.relationSessionDigest.findFirst({
      where: { sessionId, ownerUserId: this.requireText(actorUserId, "actorUserId"), isCurrent: true, isDeleted: false },
      orderBy: { createdAt: "desc" },
    });
    return digest ? this.toDigest(digest) : null;
  }
```

**Diff 4 —— 删除 4 个 evomind 侧编排方法**（整段删除，不移植）：
- `getEnterpriseBuildCoverage`（上游第 199-254 行）
- `enqueueEnterpriseSemanticBuild`（第 256-329 行）
- `getLatestEnterpriseSemanticBuild`（第 329-336 行）
- `buildEnterpriseSemanticGraph`（第 338-447 行）
- `enterpriseBuildCoverage`（第 1409-1491 行）
- 辅助 `semanticBuildJob`（第 1493-1519 行）
- 相关常量 `ENTERPRISE_SEMANTIC_BUILD_JOB_TYPE`、`ACTIVE_BUILD_STATUSES`、`RelationEnterpriseBuildMode`/`RelationEnterpriseGraphTarget` 类型中未被保留代码引用的部分（保留代码引用到哪个就留哪个；`rebuildEnterpriseWorkstreams` 返回值不含这些类型即可）

（这些是"扫描 zclaw 会话→逐个摘要→推进任务游标"的 evomind 编排；evomind 集成时用自己的投影任务循环调 `POST /v2/intelligence/digest` + `POST /v2/intelligence/workstreams/rebuild` 替代。）

**Diff 5 —— `rebuildEnterpriseWorkstreams` 删除身份同步行**（上游第 451 行）：

```ts
    // 删除：await this.identityProjection.syncEnterpriseOrganization(enterpriseId);
    // （组织骨架由 evomind 的身份投影经 /v2/ingest/facts 推送，服务侧不再主动拉取）
    await this.normalizeCurrentEnterpriseArtifacts(enterpriseId);
```

方法其余部分（第 452-650 行：digests → `ai.inferWorkstreams` → `applyWorkstreamReviews` → retract + 重建 workstream/business_object 节点与 contributes_to/collaborates_on/overlaps_on 边）**逐字保留**。

**Diff 6 —— `listWorkstreamReviews`/`reviewWorkstream` 的鉴权**：方法内 `assertActiveMembership`/`assertEnterpriseOperator` 调用保留（方法本身改走镜像，见 Diff 9）；其余逻辑（第 766-945 行）逐字保留。

**Diff 7 —— `projectDigest` 成员姓名改镜像**（上游第 1225-1230 行）：

```ts
    const enterpriseMembership = scope === "enterprise"
      ? await this.mirror.activeMembership(digest.ownerUserId, digest.enterpriseId!)
      : null;
```

（下游使用处 `enterpriseMembership?.realName?.trim()` 不变——镜像行字段名兼容。）

**Diff 8 —— `enterpriseDigestInputs` 改镜像**（上游第 1323-1350 行替换为）：

```ts
  private async enterpriseDigestInputs(enterpriseId: string) {
    const rows = await this.currentEnterpriseDigests(enterpriseId);
    const userIds = [...new Set(rows.map((row) => row.ownerUserId))];
    const members = await this.mirror.membersByUserIds(enterpriseId, userIds);
    const memberByUser = new Map(members.map((row) => [row.userId, row]));
    const displayNameByUser = this.memberDisplayNames(
      members.map((row) => ({ userId: row.userId, realName: row.realName, department: row.department })),
    );
    return rows.map((digest) => {
      const member = memberByUser.get(digest.ownerUserId);
      const groups = member?.groups ?? [];
      return {
        digest,
        personName: displayNameByUser.get(digest.ownerUserId) || "成员 · 未分配部门",
        groups,
        groupName: groups.map((group) => group.name).join("、") || member?.department || null,
      };
    });
  }
```

（`memberDisplayNames`、`currentEnterpriseDigests` 原样保留。）

**Diff 9 —— `assertActiveMembership`/`assertEnterpriseOperator` 改镜像**（上游第 1556-1568 行）：

```ts
  private async assertActiveMembership(userId: string, enterpriseId: string) {
    const membership = await this.mirror.activeMembership(userId, enterpriseId);
    if (!membership) throw new ForbiddenException("无权访问该企业关系空间");
    return membership;
  }

  private async assertEnterpriseOperator(userId: string, enterpriseId: string) {
    const membership = await this.assertActiveMembership(userId, enterpriseId);
    if (!["owner", "admin", "operator"].includes(membership.role)) throw new ForbiddenException("仅企业管理员可重新归纳工作主线");
  }
```

**Diff 10 —— 新增 digests 状态查询方法**（文件尾部，服务 controller 用）：

```ts
  async listDigestStatus(sessionIds: string[]) {
    const rows = await this.prisma.relationSessionDigest.findMany({
      where: { sessionId: { in: sessionIds }, isDeleted: false },
      orderBy: [{ createdAt: "desc" }, { id: "desc" }],
      select: {
        id: true, sessionId: true, sourceVersion: true, isCurrent: true,
        enterpriseId: true, visibility: true, createdAt: true,
      },
    });
    const latest = new Map<string, (typeof rows)[number]>();
    for (const row of rows) {
      if (!latest.has(row.sessionId) && row.isCurrent) latest.set(row.sessionId, row);
    }
    return sessionIds.map((sessionId) => {
      const digest = latest.get(sessionId) ?? null;
      return {
        sessionId,
        digestId: digest?.id ?? null,
        sourceVersion: digest?.sourceVersion ?? null,
        isCurrent: digest?.isCurrent ?? false,
        enterpriseId: digest?.enterpriseId ?? null,
        visibility: digest?.visibility ?? null,
      };
    });
  }
```

其余一切（`analyzeEnterpriseRisks`、风险快照、`answerEnterpriseQuestion`/`askEnterpriseQuestion`、`listEnterpriseQuestionHistory`、`applyWorkstreamReviews`、`normalizeCurrentEnterpriseArtifacts`、`projectBusinessObjects`、`workstreamEvidence`、`activityNode`、`activities`/`artifacts`、`toDigest`、`digest`、`record`、`requireText`、STABLE_ROLES 等）**逐字保留**。

- [ ] **Step 3: intelligence 控制器**

`src/intelligence/intelligence.controller.ts`：

```ts
import { Body, Controller, Get, Injectable, Param, ParseUUIDPipe, Post, Query, UseGuards } from "@nestjs/common";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import { RelationWorkIntelligenceService } from "./relation-work-intelligence.service.js";

const V2 = "api/internal/relation-compute/v2/intelligence";

@Injectable()
@Controller(V2)
@UseGuards(ApiKeyGuard)
export class IntelligenceController {
  constructor(private readonly intelligence: RelationWorkIntelligenceService) {}

  @Post("digest")
  generateDigest(@Body() dto: any) {
    return this.intelligence.generateSessionDigest({
      actorUserId: dto.actorUserId,
      sessionId: dto.sessionId,
      ownerUserId: dto.ownerUserId ?? dto.actorUserId,
      title: dto.title ?? null,
      locale: dto.locale ?? null,
      agentEnterpriseId: dto.agentEnterpriseId ?? null,
      publishToEnterprise: dto.publishToEnterprise === true,
      enterpriseId: dto.enterpriseId ?? null,
      messages: (dto.messages ?? []).map((message: any) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        updatedAt: new Date(message.updatedAt),
      })),
    });
  }

  @Get("digests/status")
  digestStatus(@Query("sessionIds") sessionIds: string) {
    const ids = (sessionIds ?? "").split(",").map((item) => item.trim()).filter(Boolean).slice(0, 500);
    return this.intelligence.listDigestStatus(ids);
  }

  @Get("digests/:sessionId")
  getDigest(@Query("actorUserId") actorUserId: string, @Param("sessionId") sessionId: string) {
    return this.intelligence.getSessionDigest(actorUserId, sessionId);
  }

  @Post("workstreams/rebuild")
  rebuild(@Body() dto: { actorUserId: string; enterpriseId: string }) {
    return this.intelligence.rebuildEnterpriseWorkstreams(dto.actorUserId, dto.enterpriseId);
  }

  @Get("workstreams/reviews")
  reviews(@Query("actorUserId") actorUserId: string, @Query("enterpriseId") enterpriseId: string) {
    return this.intelligence.listWorkstreamReviews(actorUserId, enterpriseId);
  }

  @Post("workstreams/reviews")
  review(@Body() dto: any) {
    return this.intelligence.reviewWorkstream(dto.actorUserId, dto);
  }

  @Get("risks")
  risks(@Query("actorUserId") actorUserId: string, @Query("enterpriseId") enterpriseId: string) {
    return this.intelligence.analyzeEnterpriseRisks(actorUserId, enterpriseId);
  }

  @Get("risk-analysis")
  riskAnalysis(@Query("actorUserId") actorUserId: string, @Query("enterpriseId") enterpriseId: string) {
    return this.intelligence.getEnterpriseRiskAnalysis(actorUserId, enterpriseId);
  }

  @Post("risk-analysis/refresh")
  refreshRisk(@Body() dto: { actorUserId: string; enterpriseId: string }) {
    return this.intelligence.refreshEnterpriseRiskAnalysis(dto.actorUserId, dto.enterpriseId);
  }

  @Post("ask")
  ask(@Body() dto: any) {
    return this.intelligence.askEnterpriseQuestion(
      dto.actorUserId,
      dto.enterpriseId,
      dto.question,
      dto.anchorNodeId,
      { questionScope: dto.questionScope, departmentNodeId: dto.departmentNodeId },
    );
  }

  @Get("questions/history")
  history(
    @Query("actorUserId") actorUserId: string,
    @Query("enterpriseId") enterpriseId: string,
    @Query("limit") limit: string | undefined,
    @Query("anchorNodeId") anchorNodeId: string | undefined,
    @Query("questionScope") questionScope: any,
    @Query("departmentNodeId") departmentNodeId: string | undefined,
  ) {
    return this.intelligence.listEnterpriseQuestionHistory(
      actorUserId,
      enterpriseId,
      limit ? Math.min(Math.max(Number(limit) || 10, 1), 50) : 10,
      anchorNodeId,
      { questionScope, departmentNodeId },
    );
  }
}
```

`src/intelligence/intelligence.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { PermissionsModule } from "../permissions/permissions.module.js";
import { ProjectionModule } from "../projection/projection.module.js";
import { QueryModule } from "../query/query.module.js";
import { IntelligenceController } from "./intelligence.controller.js";
import { RelationSemanticAiService } from "./relation-semantic-ai.service.js";
import { RelationWorkIntelligenceService } from "./relation-work-intelligence.service.js";

@Module({
  imports: [PermissionsModule, ProjectionModule, QueryModule],
  controllers: [IntelligenceController],
  providers: [RelationSemanticAiService, RelationWorkIntelligenceService],
  exports: [RelationWorkIntelligenceService],
})
export class IntelligenceModule {}
```

`src/app.module.ts` imports 追加 `IntelligenceModule`。

**注意** `askEnterpriseQuestion` 上游签名为 `(actorUserId, enterpriseId, question, options, anchorNodeId?, scopeOptions?)` —— 复制上游 `relation-work-intelligence.controller.ts` 第 76-82 行的调用姿势到上面的 `ask` 端点，参数顺序以移植后服务的实际签名为准（先读被移植文件确认，再写控制器调用；两边必须一致，不允许 any 绕过类型检查）。

- [ ] **Step 4: 适配上游智能测试 + 新增 controller 测试**

上游 `relation-work-intelligence.service.test.ts` 的适配点（构造服务处）：

```ts
const service = new RelationWorkIntelligenceService(
  prismaStub,
  aiStub,
  projectionStub,
  queriesStub,
  mirrorStub, // 新增：{ activeMembership: async () => ({ role: "owner", realName: "张三", department: null, groups: [] }), membersByUserIds: async () => [] }
);
```

删除测试中针对被删除方法（coverage/enqueue/build）的用例；保留 digest/rebuild/reviews/risks/ask/history 用例并适配 mock（zclawSession mock → payload 直调；enterpriseMembership mock → mirrorStub）。

新增 `intelligence.controller.test.ts`（digest 参数转换）：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import { IntelligenceController } from "./intelligence.controller.js";

test("digest endpoint converts ISO updatedAt strings to Date and defaults ownerUserId", async () => {
  let captured: any;
  const controller = new IntelligenceController({
    generateSessionDigest: async (input: any) => { captured = input; return {}; },
  } as any);
  await controller.generateDigest({
    actorUserId: "u1",
    sessionId: "s1",
    title: "周会",
    messages: [{ id: "m1", role: "user", content: "hello", updatedAt: "2026-08-26T10:00:00.000Z" }],
  });
  assert.equal(captured.ownerUserId, "u1");
  assert.equal(captured.title, "周会");
  assert.ok(captured.messages[0].updatedAt instanceof Date);
  assert.equal(captured.publishToEnterprise, false);
});
```

```bash
pnpm test -- src/intelligence && pnpm typecheck
```

- [ ] **Step 5: 全量测试 + 提交**

```bash
pnpm test
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): port work intelligence (payload digest, mirror auth) + v2 endpoints"
```

---

## Task 8: 管理后台（状态页）

**Files:**
- Create: `.tmp/relation-compute/src/admin/admin.controller.ts`
- Create: `.tmp/relation-compute/src/admin/admin.module.ts`
- Create: `.tmp/relation-compute/src/admin/public/index.html`
- Create: `.tmp/relation-compute/src/admin/admin.controller.test.ts`
- Modify: `.tmp/relation-compute/src/app.module.ts`（注册 AdminModule；静态页需 `NestStaticModule` 或手动读文件，用最简单的手动读文件方案）

**Interfaces:**
- Consumes: `PRISMA_CLIENT`（各表 count/findMany）、`ApiKeyGuard`、ConfigService
- Produces:
  - `GET /admin` → 静态 HTML 状态页（无鉴权，纯壳；数据经 `/v2/admin/status` + Bearer key 拉取，key 存 localStorage）
  - `GET /api/internal/relation-compute/v2/admin/status`（Bearer）→ `{ health, counts, mirror, recentDigests, recentQuestions, uptimeSeconds }`

- [ ] **Step 1: 管理状态 API**

`src/admin/admin.controller.ts`：

```ts
import { Controller, Get, Injectable, UseGuards } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { Inject } from "@nestjs/common";
import type { PrismaClient } from "@prisma/client";
import {
  RELATION_COMPUTE_CAPABILITIES,
  RELATION_COMPUTE_PROTOCOL_VERSION,
  RELATION_COMPUTE_SERVICE_NAME,
} from "../contract/index.js";
import { ApiKeyGuard } from "../infra/api-key.guard.js";
import { PRISMA_CLIENT } from "../infra/database.module.js";

const startedAt = Date.now();

@Injectable()
@Controller()
export class AdminController {
  constructor(
    @Inject(PRISMA_CLIENT) private readonly prisma: PrismaClient,
    private readonly config: ConfigService,
  ) {}

  @Get("admin")
  async adminPage() {
    const html = await readFile(join(import.meta.dirname, "public", "index.html"), "utf8");
    return html;
  }

  @Get("api/internal/relation-compute/v2/admin/status")
  @UseGuards(ApiKeyGuard)
  async status() {
    const [
      nodes, edges, evidences, digests, reviews, questions, snapshots,
      members, documents, sharedPaths,
    ] = await Promise.all([
      this.prisma.relationNode.count({ where: { isDeleted: false } }),
      this.prisma.relationEdge.count({ where: { isDeleted: false } }),
      this.prisma.relationEvidence.count({ where: { isDeleted: false } }),
      this.prisma.relationSessionDigest.count({ where: { isDeleted: false } }),
      this.prisma.relationWorkstreamReview.count(),
      this.prisma.relationQuestionHistory.count(),
      this.prisma.relationAnalysisSnapshot.count(),
      this.prisma.relationMirrorMember.count(),
      this.prisma.relationMirrorDocument.count(),
      this.prisma.relationMirrorSharedPath.count(),
    ]);
    const [recentDigests, recentQuestions, mirrorFreshness] = await Promise.all([
      this.prisma.relationSessionDigest.findMany({
        orderBy: { createdAt: "desc" }, take: 10,
        select: { id: true, sessionId: true, generatedTitle: true, visibility: true, isCurrent: true, createdAt: true },
      }),
      this.prisma.relationQuestionHistory.findMany({
        orderBy: { generatedAt: "desc" }, take: 10,
        select: { id: true, question: true, model: true, generatedAt: true },
      }),
      this.prisma.relationMirrorMember.findMany({
        orderBy: { syncedAt: "desc" }, take: 1, select: { syncedAt: true, enterpriseId: true },
      }),
    ]);
    return {
      health: {
        ok: true,
        service: RELATION_COMPUTE_SERVICE_NAME,
        protocolVersion: RELATION_COMPUTE_PROTOCOL_VERSION,
        releaseSha: this.config.get<string>("INSIGHTWEAVER_RELEASE_SHA") ?? null,
        model: this.config.get<string>("DASHSCOPE_MODEL") ?? "qwen-plus-latest",
        capabilities: [...RELATION_COMPUTE_CAPABILITIES],
      },
      counts: { nodes, edges, evidences, digests, reviews, questions, snapshots },
      mirror: { members, documents, sharedPaths, lastSyncedAt: mirrorFreshness[0]?.syncedAt ?? null, lastSyncedEnterpriseId: mirrorFreshness[0]?.enterpriseId ?? null },
      recentDigests,
      recentQuestions,
      uptimeSeconds: Math.floor((Date.now() - startedAt) / 1000),
    };
  }
}
```

（`@Get("admin")` 返回字符串会被 Nest 以 text/html？——不会，默认 JSON。**实现修正**：用 `@Header("content-type", "text/html; charset=utf-8")` 装饰该方法，import `Header` from `@nestjs/common`。）

`src/admin/admin.module.ts`：

```ts
import { Module } from "@nestjs/common";
import { AdminController } from "./admin.controller.js";

@Module({
  controllers: [AdminController],
})
export class AdminModule {}
```

`src/app.module.ts` imports 追加 `AdminModule`。

- [ ] **Step 2: 状态页 HTML（零依赖单文件）**

`src/admin/public/index.html` —— 要点：深色简洁、key 输入框存 localStorage、自动刷新 30s、分区渲染 health/counts/mirror/最近摘要/最近问题。完整文件：

```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relation Compute · 状态页</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; font: 14px/1.6 system-ui, sans-serif; background: #0b0f14; color: #dbe4ee; }
  header { padding: 20px 28px; border-bottom: 1px solid #1d2733; display: flex; align-items: center; gap: 12px; }
  h1 { font-size: 18px; margin: 0; }
  main { max-width: 1080px; margin: 0 auto; padding: 24px 28px; display: grid; gap: 20px; }
  section { background: #111823; border: 1px solid #1d2733; border-radius: 10px; padding: 16px 20px; }
  h2 { font-size: 13px; margin: 0 0 12px; color: #7d93ad; text-transform: uppercase; letter-spacing: .08em; }
  .kv { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px 24px; }
  .kv div { display: flex; justify-content: space-between; gap: 12px; }
  .kv span:first-child { color: #7d93ad; }
  .num { font-variant-numeric: tabular-nums; font-weight: 600; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #1d2733; }
  th { color: #7d93ad; font-weight: 500; font-size: 12px; }
  #keybar { margin-left: auto; display: flex; gap: 8px; }
  input { background: #0b0f14; border: 1px solid #2a3849; color: #dbe4ee; border-radius: 6px; padding: 6px 10px; }
  button { background: #2563eb; border: 0; color: #fff; border-radius: 6px; padding: 6px 14px; cursor: pointer; }
  button:disabled { background: #1d2733; cursor: default; }
  .ok { color: #34d399; } .bad { color: #f87171; } .muted { color: #7d93ad; }
  #error { color: #f87171; }
</style>
</head>
<body>
<header>
  <h1>Relation Compute 服务状态</h1>
  <div id="keybar">
    <input id="key" type="password" placeholder="API Key" style="width:220px">
    <button id="load">加载</button>
    <span id="auto" class="muted"></span>
  </div>
</header>
<main>
  <section><h2>服务</h2><div id="health" class="kv"></div><div id="error"></div></section>
  <section><h2>图数据规模</h2><div id="counts" class="kv"></div></section>
  <section><h2>权限镜像</h2><div id="mirror" class="kv"></div></section>
  <section><h2>最近会话摘要</h2><table id="digests"><thead><tr><th>标题</th><th>会话</th><th>可见性</th><th>当前</th><th>生成时间</th></tr></thead><tbody></tbody></table></section>
  <section><h2>最近图谱问答</h2><table id="questions"><thead><tr><th>问题</th><th>模型</th><th>时间</th></tr></thead><tbody></tbody></table></section>
</main>
<script>
const API = "/api/internal/relation-compute/v2/admin/status";
const $ = (id) => document.getElementById(id);
$("key").value = localStorage.getItem("rc_admin_key") ?? "";
const kv = (el, entries) => {
  $(el).innerHTML = entries.map(([k, v]) => `<div><span>${k}</span><span class="num">${v}</span></div>`).join("");
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
async function load() {
  const key = $("key").value.trim();
  if (!key) { $("error").textContent = "请输入 API Key"; return; }
  localStorage.setItem("rc_admin_key", key);
  $("load").disabled = true;
  try {
    const res = await fetch(API, { headers: { authorization: `Bearer ${key}` } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    $("error").textContent = "";
    kv("health", [
      ["状态", `<span class="ok">正常</span>`],
      ["协议版本", esc(data.health.protocolVersion)],
      ["模型", esc(data.health.model)],
      ["Release SHA", `<span class="muted">${esc(data.health.releaseSha?.slice(0, 8))}</span>`],
      ["能力数", data.health.capabilities.length],
      ["运行时长", `${Math.floor(data.uptimeSeconds / 60)} 分钟`],
    ]);
    kv("counts", Object.entries(data.counts).map(([k, v]) => [k, Number(v)]));
    kv("mirror", [
      ["成员镜像行", data.mirror.members],
      ["文档镜像行", data.mirror.documents],
      ["共享路径镜像行", data.mirror.sharedPaths],
      ["最近镜像同步", data.mirror.lastSyncedAt ? new Date(data.mirror.lastSyncedAt).toLocaleString() : "从未"],
    ]);
    $("digests").querySelector("tbody").innerHTML = (data.recentDigests ?? []).map((d) =>
      `<tr><td>${esc(d.generatedTitle)}</td><td class="muted">${esc(d.sessionId.slice(0, 8))}</td><td>${esc(d.visibility)}</td><td>${d.isCurrent ? "✓" : ""}</td><td class="muted">${new Date(d.createdAt).toLocaleString()}</td></tr>`).join("");
    $("questions").querySelector("tbody").innerHTML = (data.recentQuestions ?? []).map((q) =>
      `<tr><td>${esc(q.question.slice(0, 60))}</td><td class="muted">${esc(q.model)}</td><td class="muted">${new Date(q.generatedAt).toLocaleString()}</td></tr>`).join("");
  } catch (error) {
    $("error").textContent = `加载失败：${error.message}（检查 Key 与服务状态）`;
  } finally {
    $("load").disabled = false;
  }
}
$("load").addEventListener("click", load);
if ($("key").value) load();
setInterval(() => { if ($("key").value && !document.hidden) load(); }, 30_000);
</script>
</body>
</html>
```

- [ ] **Step 3: 控制器测试**

`src/admin/admin.controller.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";
import { AdminController } from "./admin.controller.js";
import { ConfigService } from "@nestjs/config";

function prismaStub() {
  const counts: Record<string, number> = {};
  return {
    count: async () => 3,
    relationNode: { count: async () => 11 },
    relationEdge: { count: async () => 22 },
    relationEvidence: { count: async () => 33 },
    relationSessionDigest: {
      count: async () => 2,
      findMany: async () => [{ id: "d1", sessionId: "s1", generatedTitle: "周会", visibility: "enterprise_member", isCurrent: true, createdAt: new Date() }],
    },
    relationWorkstreamReview: { count: async () => 0 },
    relationQuestionHistory: {
      count: async () => 1,
      findMany: async () => [{ id: "q1", question: "风险?", model: "qwen", generatedAt: new Date() }],
    },
    relationAnalysisSnapshot: { count: async () => 0 },
    relationMirrorMember: { count: async () => 5, findMany: async () => [] },
    relationMirrorDocument: { count: async () => 7 },
    relationMirrorSharedPath: { count: async () => 1 },
  } as any;
}

test("status aggregates counts, mirror info, and recents", async () => {
  const controller = new AdminController(prismaStub(), new ConfigService());
  const status = await controller.status();
  assert.equal(status.counts.nodes, 11);
  assert.equal(status.counts.edges, 22);
  assert.equal(status.mirror.members, 5);
  assert.equal(status.recentDigests.length, 1);
  assert.equal(status.recentQuestions[0].question, "风险?");
  assert.equal(status.health.ok, true);
  assert.ok(status.uptimeSeconds >= 0);
});
```

```bash
pnpm test -- src/admin && pnpm typecheck
```

- [ ] **Step 4: 提交**

```bash
git add .tmp/relation-compute/src
git commit -m "feat(relation-compute): admin status API + zero-dependency dashboard page"
```

---

## Task 9: Dockerfile + 部署编排 + README 集成契约

**Files:**
- Create: `.tmp/relation-compute/Dockerfile`
- Modify: `.tmp/relation-compute/docker-compose.yml`（追加 service）
- Create: `.tmp/relation-compute/README.md`

**Interfaces:**
- Consumes: Task 1-8 全部
- Produces: `docker compose up -d` 一键起 postgres+服务；README 记录全部端点契约与 evomind 集成义务

- [ ] **Step 1: Dockerfile（独立项目版，非 monorepo 过滤版）**

`.tmp/relation-compute/Dockerfile`：

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
ENV NPM_CONFIG_REGISTRY=https://registry.npmmirror.com/
RUN corepack enable && corepack prepare pnpm@9.11.0 --activate

COPY package.json ./
RUN --mount=type=cache,id=rc-pnpm-store,target=/pnpm/store \
    pnpm config set store-dir /pnpm/store && pnpm install --no-frozen-lockfile

COPY prisma ./prisma
COPY tsconfig.json ./
COPY src ./src
RUN pnpm exec prisma generate && pnpm exec tsc -p tsconfig.json

FROM node:22-slim AS runner
ARG INSIGHTWEAVER_RELEASE_SHA
WORKDIR /app
ENV NODE_ENV=production PORT=8080 INSIGHTWEAVER_RELEASE_SHA=${INSIGHTWEAVER_RELEASE_SHA}
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/package.json ./
USER node
EXPOSE 8080
CMD ["sh", "-c", "pnpm exec prisma migrate deploy && node dist/main.js"]
```

- [ ] **Step 2: docker-compose 追加服务**

在 `docker-compose.yml` 的 `services:` 下追加（postgres 服务保留）：

```yaml
  relation-compute:
    build:
      context: .
      args:
        INSIGHTWEAVER_RELEASE_SHA: "local-dev"
    environment:
      DATABASE_URL: "postgresql://relation:relation@postgres:5432/relation_brain?schema=public"
      RELATION_COMPUTE_SERVER_API_KEY: "${RELATION_COMPUTE_SERVER_API_KEY:-dev-key-change-me}"
      INSIGHTWEAVER_RELEASE_SHA: "local-dev"
      DASHSCOPE_API_KEY: "${DASHSCOPE_API_KEY:-}"
      DASHSCOPE_MODEL: "${DASHSCOPE_MODEL:-qwen-plus-latest}"
      DASHSCOPE_BASE_URL: "${DASHSCOPE_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
```

- [ ] **Step 3: README（部署 + 集成契约文档）**

`.tmp/relation-compute/README.md` 必须包含以下全部章节（内容照写，可润色不可缺节）：

```markdown
# Relation Compute Service（独立部署版）

组织关系大脑的独立后端：LLM 计算 + 关系图谱存储 + 证据授权 + 图查询 + 智能分析。
与 evomind 完全解耦，仅通过 HTTP（Bearer API Key）交互。

## 快速启动
（docker compose up -d；.env 说明；首检 curl health 示例）

## 环境变量
| 变量 | 必填 | 说明 |
（DATABASE_URL / RELATION_COMPUTE_SERVER_API_KEY / INSIGHTWEAVER_RELEASE_SHA / DASHSCOPE_API_KEY / PORT / DASHSCOPE_MODEL / DASHSCOPE_BASE_URL —— 表格逐项）

## API 一览
### v1（与上游 evomind 内置 relation-compute 逐字节兼容）
- GET  /api/internal/relation-compute/v1/health
- POST /api/internal/relation-compute/v2/complete → 实际路径 /v1/complete（列真实路径）

### v2 ingest（evomind 投影管线调用）
- POST /v2/ingest/facts        —— projectFact 批量版（幂等，per-fact 结果）
- POST /v2/ingest/retract      —— 按 sourceType+sourceIds 回收
- POST /v2/ingest/retract-orphan-nodes
- GET  /v2/ingest/source-ids   —— reconcileSources 对账用

### v2 permissions（权限镜像，fail-closed）
- POST /v2/permissions/sync    —— members 全量替换 / documents、sharedPaths upsert

### v2 graph（evomind 渲染端调用，actorUserId 必传）
- GET /v2/graph/subgraph|path|timeline|context
- GET /v2/graph/evidences/:evidenceId

### v2 intelligence（智能分析）
- POST /v2/intelligence/digest（消息在 payload，服务侧 LLM+存储+投影）
- GET  /v2/intelligence/digests/:sessionId、/digests/status
- POST /v2/intelligence/workstreams/rebuild
- GET|POST /v2/intelligence/workstreams/reviews
- GET  /v2/intelligence/risks、/risk-analysis；POST /risk-analysis/refresh
- POST /v2/intelligence/ask；GET /questions/history

### 管理页
- GET /admin（HTML 状态页；数据走 GET /v2/admin/status + Bearer key）

## evomind 集成契约（后续接入方必读）
1. 数据归属：7 张 relation 表 + 3 张镜像表在本服务库；evomind 保留源表与投影任务队列（relation_projection_jobs/checkpoints/memory_snapshots/compute_configs 留在 evomind）。
2. 写入义务：
   - 身份/聊天结构/RAGFlow/记忆四类投影：evomind 侧计算 facts（照抄上游 relation-identity/chat/ragflow/memory projection 的 projectFact 调用参数），POST /v2/ingest/facts
   - 摘要生成：evomind 侧发消息内容 POST /v2/intelligence/digest
   - 权限镜像：成员变更/文档权限变更时 POST /v2/permissions/sync（成员列表必须全量）
3. 读取：图视图直接 GET /v2/graph/*，actorUserId 传当前登录用户；响应形状与上游 RelationSubgraphResponse 完全一致。
4. 缓存建议：evomind 对 (actorUserId, 查询参数) 做 30-60s TTL 缓存。
5. 版本锁：INSIGHTWEAVER_RELEASE_SHA 两端一致；协议版本 1.0.0（v1）/ 2.0.0（v2）。

## 与上游代码的对应关系（移植来源表）
（列每个 src 文件 ← 上游 .tmp/insightweaver 路径 + 已应用 diff 摘要，逐文件一行）
```

- [ ] **Step 4: 验证 + 提交**

```bash
docker compose build 2>&1 | tail -5   # 可选：本机无 Docker 则跳过并注明
pnpm typecheck && pnpm test
git add .tmp/relation-compute/Dockerfile .tmp/relation-compute/docker-compose.yml .tmp/relation-compute/README.md
git commit -m "build(relation-compute): dockerfile + compose + integration contract README"
```

---

## Task 10: 端到端冒烟 + 最终验证

**Files:**
- Create: `.tmp/relation-compute/src/e2e.smoke.test.ts`
- Modify: 视发现的问题修复对应文件

**Interfaces:**
- Consumes: 全部端点
- Produces: 一条脚本化证据链：ingest → 镜像 → 授权查询 → 回收

- [ ] **Step 1: 端到端冒烟测试（真实 PG，环境变量门控）**

`src/e2e.smoke.test.ts`：

```ts
import test from "node:test";
import assert from "node:assert/strict";

const DATABASE_URL = process.env.TEST_DATABASE_URL;
const API_KEY = "e2e-test-key-0123456789";

test("ingest → mirror → authorized subgraph → retract", { skip: !DATABASE_URL }, async (t) => {
  process.env.DATABASE_URL = DATABASE_URL;
  process.env.RELATION_COMPUTE_SERVER_API_KEY = API_KEY;
  process.env.INSIGHTWEAVER_RELEASE_SHA = "e2e".padEnd(40, "0");
  process.env.DASHSCOPE_API_KEY = "sk-unused";
  process.env.PORT = "18081";

  const { AppModule } = await import("./app.module.js");
  const { NestFactory } = await import("@nestjs/core");
  const app = await NestFactory.create(AppModule, { logger: false });
  await app.listen(18081, "127.0.0.1");
  t.after(() => app.close());

  const base = "http://127.0.0.1:18081/api/internal/relation-compute";
  const auth = { authorization: `Bearer ${API_KEY}`, "content-type": "application/json" };
  const enterpriseId = crypto.randomUUID();
  const ownerId = crypto.randomUUID();
  const outsiderId = crypto.randomUUID();

  // 1) 成员镜像：owner 在企业内，outsider 不在
  const sync = await fetch(`${base}/v2/permissions/sync`, {
    method: "POST", headers: auth,
    body: JSON.stringify({ members: [{ enterpriseId, members: [{ userId: ownerId, role: "owner", realName: "张三", department: "产研" }] }] }),
  });
  assert.equal(sync.status, 200);

  // 2) ingest 一条企业事实（person —member_of_department→ department）
  const fact = {
    space: { type: "enterprise", enterpriseId },
    subject: { identityKey: `user:${ownerId}`, nodeType: "person", displayName: "张三" },
    relation: { edgeKey: "dept:d1", relationType: "member_of_department", factType: "system" },
    object: { identityKey: "department:d1", nodeType: "department", displayName: "产研部" },
    evidence: {
      evidenceKey: "dept:d1:enterprise", sourceType: "enterprise_department", sourceId: "d1",
      accessScope: "enterprise_member", permissionSourceType: "enterprise", permissionSourceId: enterpriseId,
    },
  };
  const ingest = await fetch(`${base}/v2/ingest/facts`, {
    method: "POST", headers: auth, body: JSON.stringify({ facts: [fact] }),
  });
  assert.equal(ingest.status, 200);
  const ingestBody = await ingest.json();
  assert.equal(ingestBody.results[0].ok, true);

  // 3) 成员能查到边；外人查不到（fail-closed 授权）
  const query = (actorUserId: string) =>
    fetch(`${base}/v2/graph/subgraph?scope=enterprise&enterpriseId=${enterpriseId}&actorUserId=${actorUserId}&hops=2&includeAllNodes=true`, { headers: auth });
  const memberView = await (await query(ownerId)).json();
  assert.equal(memberView.edges.length, 1);
  assert.equal(memberView.nodes.length, 2);
  const outsiderView = await (await query(outsiderId)).json();
  assert.equal(outsiderView.edges.length, 0);

  // 4) 收回证据源 → 边消失
  const retract = await fetch(`${base}/v2/ingest/retract`, {
    method: "POST", headers: auth,
    body: JSON.stringify({ space: fact.space, sourceType: "enterprise_department", sourceIds: ["d1"] }),
  });
  assert.equal(retract.status, 200);
  const afterRetract = await (await query(ownerId)).json();
  assert.equal(afterRetract.edges.length, 0);
});
```

```bash
docker compose up -d postgres
pnpm exec prisma migrate deploy  # 确保 TEST_DATABASE_URL 指向的库已迁移
TEST_DATABASE_URL="postgresql://relation:relation@localhost:5433/relation_brain?schema=public" pnpm test -- src/e2e.smoke.test.ts
```

期望：PASS（无 TEST_DATABASE_URL 时自动 skip，不阻塞 CI）。

- [ ] **Step 2: 全量验证**

```bash
pnpm typecheck && pnpm test
```

期望：全部 PASS。

- [ ] **Step 3: 对照本计划自检并修复**

- v1 health 响应与上游 `isCompatibleRelationComputeHealth` 兼容（用上游校验函数测一遍）
- 每个 v2 端点都在 README API 一览里
- 移植文件与 README"对应关系表"一一对应
- `pnpm build` 产物可 `node dist/main.js` 启动（本地试跑一次）

- [ ] **Step 4: 提交**

```bash
git add .tmp/relation-compute
git commit -m "test(relation-compute): e2e smoke (ingest→mirror→authz→retract) + final verification"
```

---

## 自检记录（写计划时已核对）

1. **Spec 覆盖**：可行性报告 §四 的目标架构逐项落任务——计算服务提取（T2）、表分离+协议 v2（T3-T5）、智能编排迁移（T6-T7）、管理页（T8）、部署（T9）、权限镜像 fail-closed（T4）、幂等 ingest（T3）、验收（T10）。evomind 侧改造不在本计划（报告 §五 明确为后续，README 契约承接）。
2. **占位符扫描**：所有"复制+diff"任务均给出 diff 前后代码；新文件全文给出；无 TBD/TODO。
3. **类型一致性**：`PRISMA_CLIENT` token（T2 定义，T3/4/5/7/8 使用）；`RelationMirrorService.activeMembership/membersByUserIds`（T4 定义，T5/T7 使用）；`RelationEvidenceAuthorizationService.authorizedEvidenceIds`（T4 定义，T5 使用）；`RelationProjectionService.projectFact/retractSource`（T3 定义，T7 使用）；契约类型集中 `src/contract/index.ts`。
