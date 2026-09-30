# 关系空间后端集成设计方案（最小可跑 · relation-compute 独立服务架构）

> 日期：2026-08-26 ｜ 分支：feature/wtcfix ｜ 前置：前端已全部就绪（Task 1-11 + 弹窗化 1399fc8f）
> 来源分支：feature/relation-space-workstream-risk（克隆于 .tmp/insightweaver）
> **架构要求（用户明确）：relation-compute 必须作为独立服务部署运行，主平台 api 通过远程调用使用它。**

## 1. 目标与范围

将上游的关系空间后端完整迁移到主工作区，使组织关系大脑弹窗的全部交互在真实数据上可用，且**语义计算一律经由独立部署的 relation-compute 服务**：

- **迁移 3 个代码单元**：`packages/relation-contract`（协议契约）、`apps/relation-compute`（独立 LLM 代理服务，**必部署**）、`apps/api/src/relation-space`（NestJS 模块，约 8.6k 行生产代码）
- **新增 12 张数据表**（Prisma 模型 + migration）
- **补齐 2 个主工作区缺口**（见 §4.2）
- **零新增 npm 依赖**（openai@^4.104.0 主工作区 apps/api 已有）

不在范围内：数据回填历史数据、性能调优、多实例部署策略。

## 2. 架构总览（独立服务拓扑）

```
┌─────────────── 主平台（已有，全部验证就绪） ───────────────┐
│  web (Next.js)          api (NestJS)         PostgreSQL   │
│  ├─ 组织关系大脑弹窗 ──→ /api/relation-space/*             │
│  │   (前端已完成)         └→ relation-space 模块 【迁移物3】 │
│  ├─ 知识库大脑 ──────────→ zclaw 模块 (ragflow)            │
│  └─ 管理端 compute 配置页→   │  │                           │
│        （前端已完成）        │  │ 投影管线（3 源）            │
│  evomind 会话/消息 ─────────┘  │  ├─ Chat 投影（会话→关系）  │
│  zclaw agent memory ──────────┤  ├─ Memory 投影（记忆→关系）│
│  ragflow 知识图谱 ────────────┘  └─ Ragflow 图投影（图→关系）│
│                              ↓                             │
│                    relation_nodes/edges/evidences          │
│                    (+digests/snapshots/jobs/…)  12 张表    │
└──────────────────┬─────────────────────────────────────────┘
                   │ HTTP + Bearer（全部 LLM 语义调用）
                   │ /api/internal/relation-compute/v1/{health,complete}
┌──────────────────▼─────────────────────────────────────────┐
│  apps/relation-compute 【迁移物2 · 独立进程，独立端口】        │
│  无状态 LLM 代理：鉴权(时序安全比较)→请求校验→OpenAI SDK     │
│  → DashScope → 结构化返回（协议版本+releaseSha+model 回显） │
└──────────────────┬─────────────────────────────────────────┘
                   └──→ DashScope (compatible-mode API)
```

**关键结论（依赖验证，2026-08-26 全部实测）**：

| 验证项 | 结果 |
|---|---|
| pnpm-workspace.yaml（apps/* + packages/*） | ✅ 两仓库完全一致 |
| auth/AdminGuard、JwtAuthGuard、AuthModule | ✅ 存在 |
| agents/builtin-agent-catalog（CUSTOM_ENTERPRISE_AGENT_SPACE_ID） | ✅ 存在 |
| infra/DatabaseModule（"PrismaClient" 注入令牌） | ✅ 存在 |
| ZclawModule / ZclawKmAgentClient | ✅ providers+exports 齐 |
| openai@^4.104.0 | ✅ 主工作区 api 已有 |
| RagflowDataset / User / ZclawAgentInstance（enterpriseOpenClawInstanceId 字段） | ✅ schema 齐 |
| ZclawService.canReadSharedWorkspacePath | ⚠️ **缺此方法**，但底层 withSharedWorkspaceTarget / assertSharedWorkspacePermission 均在（34 处引用） |
| zclaw-memory-projection-source.service.ts | ⚠️ **整文件缺失**（205 行） |
| 前端 API URL ↔ NestJS 路由 | ✅ 全部对齐（/api/relation-space/* ↔ @Controller("relation-space")） |
| 调度机制 | ✅ 纯 setInterval + OnModuleInit/Destroy，无需 @nestjs/schedule |
| 加密密钥来源 | ✅ ZCLAW_ENTERPRISE_INSTANCE_SECRET ∥ ZCLAW_MODEL_CONFIG_SECRET ∥ JWT_ACCESS_SECRET（主工作区均有） |

## 3. 数据模型（12 张表，Prisma 完整定义）

所有模型从上游 `packages/db/prisma/schema.prisma` 原样拷贝（行 376-2200 区间），加一次 migration。字段清单：

**① relation_compute_configs** — compute 服务配置（管理端配置页的后端）
- `id`(固定"default") / `baseUrl` / `apiKeyEncrypted`(AES-256-GCM) / `apiKeyMask`
- `status`(active) / `requestTimeoutMs`(180s) / 健康检查字段（healthStatus/serviceVersion/protocolVersion/releaseSha/model/capabilities/lastHealthCheckAt/lastHealthError）

**② relation_nodes** — 关系节点（人/组/事项/产物）
- 身份：`spaceKey`+`identityKey`（唯一键）、`spaceType`、`nodeType`、`displayName`、`canonicalName`、`language`
- 归属：`enterpriseId`?、`ownerUserId`?；状态：`status`/`isDeleted`（软删）
- 索引：space+type+status / enterprise+status / owner+status

**③ relation_edges** — 关系边
- `spaceKey`+`edgeKey`（唯一键）、`sourceNodeId`→`targetNodeId`（Cascade）
- 语义：`relationType`、`factType`、`weight`、`confidence`、`occurredAt`、`validFrom/validTo`（时间有效期）

**④ relation_evidences** — 证据（可追溯性核心）
- `spaceKey`+`evidenceKey`（唯一键）、挂载 `nodeId`?/`edgeId`?（Cascade）
- 来源：`sourceType`/`sourceId`/`sourceVersion`/`locator`(Json 定位)/`excerpt`
- **权限镜像**：`accessScope` + `permissionSourceType/permissionSourceId/permissionVersion` —— 证据读取时按此做授权检查（§5 evidences 接口）

**⑤ relation_session_digests** — 会话摘要（LLM 生成）
- `sessionId`+`sourceVersion`（唯一键）、`ownerUserId`、`generatedTitle`/`summary`
- `activities`/`artifacts`/`subjects`(Json 三元组)、`visibility`(owner_only/…)、`isCurrent`
- 按需生成：POST sessions/:id/digest 触发，LLM 摘要后入库

**⑥ relation_analysis_snapshots** — 分析快照（风险分析结果缓存）
- `enterpriseId`+`analysisType`（唯一键）、`question`/`answer`/`model`
- `evidenceCount`/`truncated`、`graphUpdatedAt`（快照对应的图版本）

**⑦ relation_question_history** — 提问历史（"向图谱提问"）
- `enterpriseId`+`generatedByUserId`+`generatedAt` 索引；scope 过滤索引
- `anchorNodeId/Name/Type`（锚点）、`questionScope`(enterprise/department/personal)、`departmentNodeId/Name`

**⑧ relation_workstream_reviews** — 工作主线人工复核
- `enterpriseId`+`anchorKey`（唯一键）、`action`、`targetAnchorKey`?、`splitGroups`(Json)、`reason`?

**⑨ relation_projection_jobs** — 投影任务队列
- `idempotencyKey`（唯一）、`jobType`、`scopeType`/`ownerUserId`?/`enterpriseId`?
- 执行控制：`status`(pending/…)/`attemptCount`/`maxAttempts`(3)/`nextAttemptAt`/`lockedAt`/`lockedBy`（多实例安全锁）
- 关联：`datasetMappingId`→RagflowDataset(SetNull)、`requestedByUserId`→User(SetNull)
- `cursor`(Json) 支持增量断点

**⑩ relation_projection_checkpoints** — 增量扫描检查点
- `key`(主键)、`cursorTimestamp`/`cursorId`、`lastScanAt`/`lastSuccessAt`/`lastError`、`version`

**⑪ relation_memory_snapshots** — memory 文件快照（Memory 投影的变更检测）
- `ownerUserId`+`enterpriseOpenClawInstanceId`+`path`（唯一键）
- `entryType`/`sourceVersion`/`contentHash`/`remoteSize`/`remoteUpdatedAt`/`lastSeenScanId`/`status`/`missingAt`

**⑫ 无独立表**：workstream（工作主线）数据存于 ⑤ 的 activities + 投影产物，视图层从 subgraph 动态聚合。

## 4. 代码迁移清单

### 4.1 迁移物（从 .tmp/insightweaver 原样拷贝）

| # | 路径 | 规模 | 说明 |
|---|---|---|---|
| 1 | `packages/relation-contract/` | 120 行 | 协议契约：常量(协议版本1.0.0/8个能力/限制)、类型、请求校验。零外部依赖 |
| 2 | `apps/relation-compute/` | 236 行 + Dockerfile | **独立 LLM 代理服务（必部署）**：`/health`、`/complete`，Bearer 时序安全比较，OpenAI SDK 调 DashScope |
| 3 | `apps/api/src/relation-space/` | 40 文件 ~13.7k 行（生产 ~8.6k） | NestJS 模块全量：4 控制器 28 路由 + 19 服务 + 4 DTO |
| 4 | `apps/api/src/zclaw/zclaw-memory-projection-source.service.ts` | 205 行 | Memory 投影数据源（读 zclawAgentInstance + enterpriseMembership + kmAgentClient.runWithTarget） |
| 5 | schema.prisma 12 个模型 | ~244 行 | §3 |

### 4.2 需要的适配点（仅 3 处，均为小改动）

1. **`ZclawService` 补 `canReadSharedWorkspacePath(userId, enterpriseId, targetPath)` 方法**（~20 行）：上游 zclaw.service.ts L4504 的实现直接拷贝——底层 `withSharedWorkspaceTarget`/`assertSharedWorkspacePermission` 主工作区已有。
2. **`zclaw.module.ts`**：providers + exports 注册 `ZclawMemoryProjectionSourceService`（上游同文件有参照，L36）。
3. **`app.module.ts`**：imports 注册 `RelationSpaceModule`（上游 app.module.ts L24/L49 参照）。

### 4.3 明确不改的

- relation-space 模块内部代码**零修改**（其外部依赖 §2 表全部就绪）
- **relation-compute 独立服务形态零修改**（独立 package.json / 独立端口 / 独立进程，仅依赖 relation-contract 契约包）
- turbo.json 无需改动（build pipeline 由 workspace 通配覆盖；上游也未加 relation 条目）
- 前端零改动（URL 已对齐）

## 5. API 面 → 组织关系大脑交互完整映射

前端已移植的 19 个 API 函数（relation-space.ts）+ 管理端 3 个（zclaw.ts）对应后端 28 个路由，覆盖弹窗内**全部交互**：

| 弹窗交互 | 请求 | 后端服务 | 数据表 |
|---|---|---|---|
| 打开弹窗/切 5 视图（工作主线/跨组协同/工作重叠/部门图谱/个人图谱） | `GET /api/relation-space/subgraph?scope&perspective&…` | RelationQueryService | ②③④ |
| 风险分析按钮 | `POST …/risk-analysis/refresh` → `GET …/risk-analysis` → `GET …/risks` | WorkIntelligence + SemanticAi→**compute** | ⑥ |
| 向图谱提问（个人/部门/企业 scope） | `POST …/ask`；历史 `GET …/questions/history` | WorkIntelligence + SemanticAi→**compute** | ⑦ |
| 工作主线复核（合并/拆分/重命名） | `GET/POST …/workstreams/reviews`、`POST …/workstreams/rebuild` | WorkIntelligence + SemanticAi→**compute** | ⑧⑤ |
| AI 上下文准备（复制到剪贴板） | `GET …/context` | WorkIntelligence | ②③⑤ |
| 会话摘要生成/查看 | `POST/GET …/sessions/:id/digest` | WorkIntelligence + SemanticAi→**compute** | ⑤ |
| 节点/边证据面板 | `GET …/evidences/:evidenceId`（经 RelationEvidenceAuthorizationService 授权检查） | Query + EvidenceAuth | ④ |
| 企业构建（覆盖/触发/轮询进度） | `GET …/enterprise-builds/coverage`、`POST …/enterprise-builds`、`GET …/enterprise-builds/latest` | ProjectionJob（投影语义→**compute**） | ⑨ |
| 关系路径/时间线（图内下钻） | `GET …/path`、`GET …/timeline` | Query | ②③④ |
| 管理端 compute 配置页（前端 Task 4 已有） | `GET/POST …/admin/compute-config`、`POST …/admin/compute-config/test` | ComputeConfig | ① |
| 管理端投影任务（重试等） | `POST/GET /api/admin/relation-space/projection-jobs(/…)` | ProjectionJob | ⑨ |

**投影管线（后台自动运行，数据从哪来）**——3 个调度器（setInterval，默认由 env 开关控制）：

1. **ChatProjection**：evomind 会话消息 → **compute** 摘要 → ⑤ → 归一化投影到 ②③④
2. **MemoryProjection**：zclaw agent memory 文件（经 ⑪ contentHash 变更检测）→ 关系投影
3. **RagflowGraphProjection**：知识库大脑的图（RagflowDataset）→ 关系投影
4. **ChangeScanner + JobScheduler**：增量扫描（⑩ checkpoint 断点续传）+ 任务队列（⑨ 重试/锁/多实例安全）

## 6. 独立服务调用链与配置语义（实测源码确认）

### 6.1 调用分流（relation-compute-config.service.ts L112-150 实测）

```
complete(responseType, system, content)
  └→ resolveRemote(false)
       ├─ ① 表有 active 配置行 → 用库表配置（baseUrl + 解密 apiKey）
       ├─ 无 active 行，但 env RELATION_COMPUTE_BASE_URL + RELATION_COMPUTE_API_KEY 都设了 → 用 env 配置
       └─ 都没有 → 返回 null
  └→ remote == null 时：
       ├─ RELATION_LOCAL_COMPUTE_ENABLED=true → 返回 null（SemanticAi 收到 null 后进程内直连 DashScope）
       └─ 否则 → 直接抛 BadGatewayException("未配置可用的远程关系计算服务")
```

**对本方案的意义**：本地直连模式**仅**由 `RELATION_LOCAL_COMPUTE_ENABLED=true` 显式触发；不设该 env 时，未配置远程即报错，**不会静默回退**。因此只要保证该 env 不设（或不为 "true"），系统强制走独立服务——这正是"独立服务架构"的行为保证，无需改任何上游代码。

### 6.2 协议校验（防版本漂移）

- **complete 响应**：校验 `protocolVersion`（必须 1.0.0）+ releaseSha（见下）
- **health 响应**：`isCompatibleRelationComputeHealth` 校验协议兼容性 + releaseSha
- **releaseSha 匹配**（L249-254 实测）：api 侧若设置了 `INSIGHTWEAVER_RELEASE_SHA`，则必须与 compute 服务回显的一致，否则 `BadGatewayException("主平台与关系计算服务版本不一致")`；api 侧未设则跳过校验
  - **部署要求**：两个服务要么设置**同一个** `INSIGHTWEAVER_RELEASE_SHA`（推荐，均用当前 git sha 或同一固定串），要么 api 侧不设

### 6.3 配置矩阵

**relation-compute 服务侧（独立进程）：**
```
PORT=8081                                              # 独立端口，不与 api/web 冲突
RELATION_COMPUTE_SERVER_API_KEY=<openssl rand -hex 32> # 服务鉴权 key（主平台侧配同一个）
INSIGHTWEAVER_RELEASE_SHA=<与 api 侧一致的 sha>         # 协议回显 + 版本一致性校验
DASHSCOPE_API_KEY=sk-…                                 # 必需：LLM 上游
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 可选，默认即此
DASHSCOPE_MODEL=qwen-plus-latest                       # 可选，默认即此
```

**主平台 api 侧（连接独立服务，二选一）：**

*方式一：env 直配（最小可跑推荐）*
```
RELATION_COMPUTE_BASE_URL=http://127.0.0.1:8081        # compute 服务地址（可跨机）
RELATION_COMPUTE_API_KEY=<与服务侧相同>                 # Bearer key
RELATION_COMPUTE_REQUEST_TIMEOUT_MS=180000             # 可选，默认 180s
INSIGHTWEAVER_RELEASE_SHA=<与服务侧相同>               # 可选但推荐，启用版本一致性校验
# 关键：不设 RELATION_LOCAL_COMPUTE_ENABLED（或确保非 "true"）
```

*方式二：管理端页面配置（运行时可改，AES-256-GCM 加密落 ① 表）*
- 打开 `/admin/relation-compute`（前端 Task 4 已就绪）→ 填 baseUrl + apiKey 保存 → 点"测试"触发健康检查
- ① 表存在 active 行后优先生效（覆盖 env）

> 优先级：① 表 active 行 > env 直配 > 报错。管理端"测试"按钮会回写 healthStatus/protocolVersion/releaseSha/model/capabilities 到 ① 表，配置页直接展示健康状态。

### 6.4 本地直连模式（仅作为代码保留，本方案不启用）

上游代码含进程内直连 DashScope 的回退路径（`RELATION_LOCAL_COMPUTE_ENABLED=true` 时生效）。按零修改原则随迁移保留，但**本集成不启用**——保持独立服务架构纯度。若未来需要应急降级，设该 env 即可，无需改码。

## 7. 实施步骤（可直接照做，预计 1 天内完成）

### Step 1 — 契约包 + compute 服务（纯拷贝 + 起服务，~20 分钟）
```bash
cp -r .tmp/insightweaver/packages/relation-contract packages/
cp -r .tmp/insightweaver/apps/relation-compute apps/
pnpm install          # workspace 通配自动识别新包
pnpm --filter @insightweaver/relation-contract build
pnpm --filter @insightweaver/relation-compute test   # 3 个测试

# 起独立服务（开发态）
cd apps/relation-compute
PORT=8081 \
RELATION_COMPUTE_SERVER_API_KEY=dev-local-key \
INSIGHTWEAVER_RELEASE_SHA=dev \
DASHSCOPE_API_KEY=sk-… \
pnpm dev
```
验证：
```bash
# 无 key → 401；带 key → 200 健康 payload（含 protocolVersion/releaseSha/model/capabilities）
curl -s http://127.0.0.1:8081/api/internal/relation-compute/v1/health -H "Authorization: Bearer dev-local-key"
```

### Step 2 — 数据库（~30 分钟）
```bash
# 1. 拷贝 12 个模型到 packages/db/prisma/schema.prisma（§3 区间原样）
# 2. 生成并应用 migration
pnpm --filter @insightweaver/db prisma migrate dev --name add_relation_space_tables
# 3. 重新生成 client
pnpm --filter @insightweaver/db prisma generate
```
验证：psql `\dt relation_*` 见 11 张表；`prisma.relationComputeConfig` 等 client 属性可用。

### Step 3 — api 模块迁移（~2 小时，含验证）
```bash
cp -r .tmp/insightweaver/apps/api/src/relation-space apps/api/src/
cp .tmp/insightweaver/apps/api/src/zclaw/zclaw-memory-projection-source.service.ts apps/api/src/zclaw/
```
然后 3 处适配（§4.2）：
- zclaw.service.ts 补 `canReadSharedWorkspacePath`（从上游 L4504-4521 拷贝）
- zclaw.module.ts 注册/导出 ZclawMemoryProjectionSourceService（参照上游同文件）
- app.module.ts 注册 RelationSpaceModule

验证：
```bash
cd apps/api && pnpm tsc --noEmit          # 零新错误
pnpm test src/relation-space              # 上游自带 ~20 个测试文件
```

### Step 4 — 主平台连接独立服务（~10 分钟）
api 侧 env 按 §6.3 方式一配置（`RELATION_COMPUTE_BASE_URL` + `RELATION_COMPUTE_API_KEY`，**不设** `RELATION_LOCAL_COMPUTE_ENABLED`）→ 起 api → 验证调用链：
1. 管理端 `/admin/relation-compute` 页面加载正常（显示 env 配置回显）
2. 点"测试"→ 健康检查通过（healthStatus: ok，protocolVersion/releaseSha/model/capabilities 回显）
3. 浏览器打开组织关系大脑弹窗（空数据态正常）
4. 在有过会话的账号下触发 `POST sessions/:id/digest` → 观察请求经 compute 服务（其日志可见 /complete 调用）→ ⑤ 表出现摘要行 → `POST workstreams/rebuild` → ②③④ 出现投影数据 → 5 视图有图

### Step 5 —（生产部署形态）
- relation-compute 用上游 Dockerfile 独立构建/独立容器/独立端口（或独立服务器，跨机只需 api 能访问其 baseUrl）
- 生产配置建议用管理端页面（方式二）：apiKey 加密落库、健康状态可视、无需重启 api 即可切换 compute 实例
- `INSIGHTWEAVER_RELEASE_SHA` 两服务同设发布 git sha，防版本漂移（§6.2）

## 8. 验收清单

> **实施状态（2026-08-26）**：Step 1–4 已完成并实测通过（本节前 7 项含实测记录）。
> 偏离说明：因主库 schema 与上游分歧（ZclawMessage 无 updatedAt、RagflowGraphService 接口不同等），
> chat/memory/ragflow 三源投影服务暂未启用（调度器未注册，job 执行抛 "schema adaptation pending"）；
> 语义计算主链路（会话摘要/主线/业务对象/归属审计/归并/图谱问答）不受影响，全部经独立 compute 服务。
> 另新增：compute 调用日志（relation_compute_call_logs 表 + 管理端日志面板，对应用户要求的服务日志可见性）。

- [x] `pnpm --filter @insightweaver/relation-compute test` 通过（2/2）
- [x] compute 服务独立进程运行：health 带 key 200 / 无 key 401（实测：401 与 200+protocolVersion/releaseSha 回显）
- [x] `cd apps/api && pnpm tsc --noEmit` 零错误
- [x] `cd apps/api && pnpm test src/relation-space` 全绿（110/110，含 5 个禁用路径适配测试）
- [x] 12 张表 migration 成功应用（prisma migrate diff 提取纯新增语句，55 条 SQL 全部执行，pg_tables 验证 12 表存在）
- [x] 管理端配置页"测试"按钮健康检查通过（全链路实测：health_check 日志落库 ok/http=200/36ms）
- [x] 调用日志全链路：complete_error 路径实测落库（capability=graph_question, err=远程关系计算失败: HTTP 502，由 dummy DashScope key 预期触发）；logsForAdmin 汇总 {total:2, errorCount:1}
- [ ] 弹窗 5 视图空态 → 有会话数据账号下 subgraph 返回真实图（需真实 DashScope key + 浏览器验收）
- [ ] 风险分析/向图谱提问/工作主线复核/AI 上下文/证据面板/会话摘要 全交互走通，**且 /admin/relation-compute 日志面板可见对应调用**（需真实 key 后浏览器验收）
- [ ] 投影调度器（chat/memory/ragflow 三源）—— **暂缓**（schema 适配待做，见上方偏离说明）
- [x] `RELATION_LOCAL_COMPUTE_ENABLED` 未设置（保证语义计算全部走独立服务）

## 9. 风险与注意事项

| 风险 | 缓解 |
|---|---|
| 12 表 migration 在有存量数据的库上执行 | 全部为**新建表**，无 alter 存量表，风险极低；上线前备份即可 |
| releaseSha 两服务不一致导致 BadGateway | §6.2：两服务同设同一 sha，或 api 侧不设；验收清单含健康检查项 |
| LLM 调用成本（投影+问答都经 compute 服务） | compute 服务无状态可独立扩缩容；投影调度器 env 开关默认可关（逐个启用） |
| compute 服务单点 | 无状态设计，重启无数据丢失（配置在主平台侧 ① 表/env）；生产可多实例 + 负载均衡 |
| `canReadSharedWorkspacePath` 拷贝后与主库 zclaw 逻辑不一致 | 上游方法体仅组合主库已有私有方法，行为一致；api 测试套覆盖 |
| 多实例 api 部署时投影调度器重复执行 | ⑨ 表 lockedAt/lockedBy 已做行锁；同上游 |
| schema.prisma 手工合并冲突 | 12 个模型全部追加在文件尾部区间，无删改既有模型 |
| 测试文件迁移（node:test 风格） | 上游 api 测试即项目现行风格（apps/api 已用 node:test），直接可用 |

## 10. 后续（不在本方案内）

- CI/CD 接入 relation-compute 独立构建（上游 Dockerfile 已随迁移物带走）
- 历史数据回填策略（当前投影从 checkpoint 起点增量，存量会话可手动 POST digest 补跑）
- 性能：subgraph 大图分页/缓存；compute 服务限流/熔断
