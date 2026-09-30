# 组织关系图谱 — 每个视图所需数据清单

> 基于上游 `.tmp/insightweaver`（分支 `feature/relation-space-workstream-risk`）实际代码核对：
> 前端 `ZclawRelationSpacePage.tsx` + `relation-space.ts`（API 模块），
> 后端 `relation-query.controller.ts` / `relation-query.service.ts` / `relation-work-intelligence.controller.ts` / `relation-work-intelligence.service.ts`。
> 所有读库操作均为 Prisma（无 raw SQL）。

## 总览：视图 → API → 数据表

| # | 视图 | API | 读取的数据表 |
|---|------|-----|-------------|
| V1 | 个人视角 | `GET /relation-space/subgraph` | relation_edges、relation_nodes、relation_evidences |
| V2 | 工作主线视角 | `GET /relation-space/subgraph` | 同上 |
| V3 | 跨组协作视角 | `GET /relation-space/subgraph` | 同上 |
| V4 | 工作重叠视角 | `GET /relation-space/subgraph` | 同上 |
| V5 | 部门视角 | `GET /relation-space/subgraph` | 同上 |
| V6 | 节点/边详情侧栏 | 无（复用 subgraph 数据） | — |
| V7 | 证据详情 | `GET /relation-space/evidences/:id` | relation_evidences、relation_nodes + 授权 |
| V8 | AI 上下文 | `GET /relation-space/context` | 同 V1（图数据转 facts 文本） |
| V9 | 规则风险 | `GET /relation-space/risks` | relation_nodes、relation_edges、relation_session_digests、enterprise_memberships |
| V10 | AI 风险分析 | `GET/POST /relation-space/risk-analysis` | relation_analysis_snapshots（刷新时 + V11 的读取 + relation_nodes 聚合） |
| V11 | 图谱问答 + 历史 | `POST /relation-space/ask`、`GET /relation-space/questions/history` | 图数据（同 V1）+ relation_question_history（写） |
| V12 | 工作主线人工评审 | `GET/POST /relation-space/workstreams/reviews` | relation_workstream_reviews、relation_nodes、relation_edges |
| V13 | 构建覆盖度 / 增量·全量重建 | `GET /relation-space/enterprise-builds/coverage`、`POST /enterprise-builds`、`GET /enterprise-builds/latest` | zclaw_sessions、zclaw_messages、relation_session_digests、relation_projection_jobs、relation_nodes、relation_workstream_reviews |
| V14 | 会话摘要生成/共享 | `GET/POST /relation-space/sessions/:id/digest` | zclaw_sessions、zclaw_messages、relation_session_digests |
| V15 | 管理端·计算服务配置 | `GET/POST /relation-space/admin/compute-config(+test)` | relation_compute_configs |
| — | 所有企业视图的前置鉴权 | （每次请求） | enterprise_memberships、enterprises |
| — | 证据授权（嵌入每次图查询） | （每次请求） | enterprise_memberships、ragflow_documents |

**核心结论：图谱画布 5 个视角共用同一个 `subgraph` 接口，只是前端传入不同的 `nodeTypes`/`relationTypes` 过滤条件；真正的数据只有 3 张表（nodes/edges/evidences），视角差异完全是过滤条件的差异。**

---

## V1 个人视角（personal）

**前端入口：** `perspective='personal'` 且无企业 → `scope=personal`
**API：** `GET /relation-space/subgraph?scope=personal&hops=3&limit=500&nodeTypes=...&relationTypes=...&sourceTypes=chat_semantic_digest`
**后端：** `RelationQueryService.subgraph()` → `loadAuthorizedEdges()`

**前端传入的过滤条件：**
```
nodeTypes:      person, conversation, activity, workstream, agent, skill (+artifact 可选)
relationTypes:  owns, participated_in, contains_activity, produced, contributes_to, configured_for
sourceTypes:    chat_semantic_digest
```

**读库明细：**

| 表 | 操作 | 用到的字段 |
|----|------|-----------|
| `relation_edges` | findMany | `spaceKey`(=`personal:<userId>`)、`status='active'`、`isDeleted=false`、`relationType in [...]`、`sourceNodeId/targetNodeId`（锚点遍历）、`updatedAt`/`id`（排序） |
| ↳ include `sourceNode`/`targetNode`（= `relation_nodes`） | | `id`、`identityKey`、`nodeType`（过滤 in [...]）、`displayName`、`canonicalName`、`language`、`properties`、`updatedAt` |
| ↳ include `evidences`（= `relation_evidences`） | | `status='active'`、`isDeleted=false`、`sourceType in [...]`、`occurredAt`（时间范围过滤+排序）、`id`、`confidence` |
| `enterprise_memberships` + `ragflow_documents` | 授权（`authorizedEvidenceIds`） | membership: `userId`、`enterpriseId`、`status`、`isDeleted`；ragflowDocument: `id`、`userId`、`status` |

**返回给前端的数据形状（`RelationSubgraphResponse`）：**
- `nodes[]`: id, identityKey, nodeType, displayName, canonicalName, language, properties, updatedAt
- `edges[]`: id, sourceNodeId, targetNodeId, relationType, factType, properties, weight（=证据 confidence 求和）, confidence（=最大值）, occurredAt（=最新证据时间）, evidenceCount, evidences[]（id/sourceType/confidence/occurredAt）
- `meta`: anchorNodeId, viewerNodeId（`identityKey='user:<userId>'` 的节点）, hops, limit, edgeCount, nodeCount, truncated

---

## V2 工作主线视角（workstreams）

**API：** 同 V1，`scope=enterprise&enterpriseId=...`（`includeAllNodes=true`）
**前置：** `resolveSpace()` 读 `enterprise_memberships`（联 `enterprises`）校验活跃成员资格 → 决定 `spaceKey=enterprise:<enterpriseId>`

**过滤条件：**
```
nodeTypes:      department, department_group, person, conversation, activity, workstream, business_object (+artifact)
relationTypes:  has_department, has_group, member_of_department, member_of_group, participated_in,
                contains_activity, produced, contributes_to, belongs_to_business_object, collaborates_on, overlaps_on
```

**读库：** 与 V1 完全相同（3 张 relation 表 + 授权），仅 `spaceKey` 换成企业空间。
前端再对返回数据做客户端过滤（`filterFocusedWorkstreamGraph` 等，纯前端逻辑，不读库）。

---

## V3 跨组协作视角（collaboration）

**API：** 同 V1，`scope=enterprise`
**过滤条件：**
```
nodeTypes:      department_group, person, conversation, activity, workstream, business_object (+artifact)
relationTypes:  member_of_group, participated_in, contains_activity, produced, contributes_to,
                belongs_to_business_object, collaborates_on
```
前端用 `filterConfirmedCollaborationGraph` 只保留 `properties.collaborationConfirmed=true` 的边（客户端过滤）。

**读库：** 同 V2。

---

## V4 工作重叠视角（overlap）

**API：** 同 V1，`scope=enterprise`
**过滤条件：** 与 V3 相同，仅把 `collaborates_on` 换成 `overlaps_on`。
前端用 `filterConfirmedOverlapGraph` 只保留 `overlapConfirmed=true` 的边。

**读库：** 同 V2。

---

## V5 部门视角（department）

**API：** 同 V1，`scope=enterprise`
**过滤条件：** 与 V2 相同（含部门结构的全套类型）。
前端用 `filterDepartmentGraph` 按选中的 `departmentNodeId` 聚焦（客户端过滤）。

**读库：** 同 V2。

> 注：路径查询 `GET /relation-space/path` 与时间线 `GET /relation-space/timeline` 端点存在（同一 service），数据源同为 3 张 relation 表；当前页面的 5 个视角不直接调用它们，`path` 复用 `subgraph` 的结果做两跳寻路。

---

## V6 节点/边详情侧栏

**无独立请求。** 选中节点/边后，详情（displayName、properties、relationType、factType、证据列表）全部来自 V1–V5 已返回的 `nodes[]`/`edges[]` 数据。

产物预览（`ArtifactPreviewDialog`）需要的 `evidenceIds` 也来自边上的 `evidences[]`，再用 V7 拉取正文。

---

## V7 证据详情

**API：** `GET /relation-space/evidences/:evidenceId`
**后端：** `RelationQueryService.evidenceDetail()`

| 表 | 操作 | 字段 |
|----|------|------|
| `relation_evidences` | findFirst（include node + edge.sourceNode/targetNode） | `id`、`status='active'`、`isDeleted=false`、`sourceType`、`sourceId`、`sourceVersion`、`locator`(Json)、`excerpt`、`confidence`、`occurredAt`、`accessScope`、`permissionVersion` |
| `relation_nodes` | include | 证据挂靠的节点 + 边的两端节点（同 V1 节点字段） |
| 授权 | 同 V1 | memberships / ragflow_documents |

前端用途：显示来源（聊天消息→跳 `/?sessionId=`、记忆文件→`/memory`、RAGFlow→`/workspace`）、原文摘录、置信度、发生时间。

---

## V8 AI 上下文

**API：** `GET /relation-space/context?...`（参数与 subgraph 完全相同）
**后端：** `RelationQueryService.aiContext()` → 复用 `loadAuthorizedEdges()`

**读库：** 与 V1–V5 相同（3 张 relation 表 + 授权）。
**返回：** 把边序列化为 `facts[]`（subject/predicate/object + factType/weight/confidence/evidenceRefs）并拼出 `contextText` 纯文本，供前端展示/复制到 AI 对话。

---

## V9 规则风险（结构风险扫描）

**API：** `GET /relation-space/risks?enterpriseId=...`
**后端：** `RelationWorkIntelligenceService.analyzeEnterpriseRisks()`

| 表 | 操作 | 字段 |
|----|------|------|
| `enterprise_memberships` | findFirst（鉴权） | `userId`、`enterpriseId`、`status`、`isDeleted`、enterprise 状态 |
| `relation_session_digests` | findMany（`enterpriseDigestInputs`） | `enterpriseId`、`visibility='enterprise_member'`、`isCurrent`、`isDeleted`、`summary`、`activities`(Json)、`artifacts`(Json)、`ownerUserId`（联 users 取 personName） |
| `relation_nodes` | findMany | `spaceKey`、`nodeType='workstream'`、`status`、`isDeleted`、`id`、`identityKey`、`displayName` |
| `relation_edges` | findMany（每条主线一次） | `spaceKey`、`targetNodeId`、`relationType='contributes_to'`、`status`、`isDeleted`、`confidence` + `sourceNode`（nodeType/identityKey/displayName） |

**输出：** 三类风险（跨组交接 cross_group_handoff、单点集中 key_person_concentration、覆盖限制 coverage），纯规则计算，不调 LLM。

---

## V10 AI 风险分析（快照）

**读取：** `GET /relation-space/risk-analysis` → `relation_analysis_snapshots` findUnique（`enterpriseId + analysisType='organization_risk'` 复合唯一键），字段：`question`、`answer`、`model`、`evidenceCount`、`truncated`、`graphUpdatedAt`、`generatedByUserId`、`generatedAt`。

**刷新：** `POST /relation-space/risk-analysis/refresh`：
1. 走 V11 的问答流程（读图数据 + LLM）
2. `relation_nodes` aggregate（`_max.updatedAt` → `graphUpdatedAt`）
3. `relation_analysis_snapshots` upsert 写回快照

---

## V11 图谱问答 + 历史

**提问：** `POST /relation-space/ask`（`enterpriseId`、`question`、可选 `anchorNodeId`、`questionScope=enterprise|personal|department`、`departmentNodeId`）
**后端：** `askEnterpriseQuestion()` → `answerEnterpriseQuestion()`

| 步骤 | 表 | 说明 |
|------|----|------|
| 鉴权 | `enterprise_memberships` | 活跃成员 |
| 上下文 | 3 张 relation 表（同 V1，`aiContext`/`scopedAiContext`） | department scope 时用 `filterOrganizationalQuestionGraph` 按部门子图过滤；personal scope 按当前用户节点过滤 |
| 调用模型 | — | 本地模型或 relation-compute 远程（见 V15 配置） |
| 写历史 | `relation_question_history` create | `enterpriseId`、`question`、`answer`、`model`、`evidenceCount`、`truncated`、`generatedByUserId`、`anchorNodeId/Name/Type`、`questionScope`、`departmentNodeId/Name`、`generatedAt` |

**历史：** `GET /relation-space/questions/history?enterpriseId=&limit=&anchorNodeId=&questionScope=&departmentNodeId=` → `relation_question_history` findMany。

---

## V12 工作主线人工评审

**列表：** `GET /relation-space/workstreams/reviews?enterpriseId=...` → `listWorkstreamReviews()`

| 表 | 操作 | 字段 |
|----|------|------|
| `relation_nodes` | findMany | workstream/activity 节点（`spaceKey`、`nodeType`、`identityKey`、`displayName`、`properties`） |
| `relation_edges` | findMany | `contains_activity`/`contributes_to`（把 activity 归到 workstream 下） |
| `relation_workstream_reviews` | findMany | `enterpriseId`、`anchorKey`、`action`、`title`、`targetAnchorKey`、`reason`、`updatedAt` |

**提交：** `POST /relation-space/workstreams/reviews` → upsert `relation_workstream_reviews`，随后 `applyWorkstreamReviews()` 按评审结论改写图：
- `relation_nodes` updateMany/update（重命名 workstream、标记合并/拆分、写 `properties.reviewStatus/reviewAction`）
- 合并/拆分时重建 workstream 相关 `relation_edges` 与 `relation_evidences`

---

## V13 构建覆盖度 / 增量·全量重建

**覆盖度：** `GET /relation-space/enterprise-builds/coverage?enterpriseId=&target=`

| 表 | 操作 | 字段 |
|----|------|------|
| `zclaw_sessions` | findMany | 联 `agentInstance`（`enterpriseId`、`scope='enterprise'`）+ `user`（活跃且为该企业成员）+ `messages` some（`status='done'`、role user/assistant）；取 `id`、`userId`、`updatedAt` |
| ↳ `zclaw_messages` | include | `id`、`content`（计算 `sourceVersion`）、`updatedAt`（**需要新增的字段**） |
| `relation_session_digests` | findMany | `sessionId in [...]`、`isCurrent`、`sourceVersion`、`enterpriseId`、`visibility` |
| `relation_projection_jobs` | findFirst | 当前活跃的 `enterprise_semantic_build` 任务：`status`、`cursor`、`result`、`attemptCount`、`maxAttempts`、`startedAt/finishedAt` |
| `relation_nodes` + `relation_workstream_reviews` | workstreamAnalysis | 活跃 workstream 数、已确认协作/重叠数、promptVersion 状态 |

**发起构建：** `POST /relation-space/enterprise-builds` → `relation_projection_jobs` 事务性创建/去重（`idempotencyKey`）。
**最近构建：** `GET /relation-space/enterprise-builds/latest` → `relation_projection_jobs` findFirst。

---

## V14 会话摘要（生成 / 查看 / 共享到企业）

**查看：** `GET /relation-space/sessions/:sessionId/digest` → `relation_session_digests` findUnique（`sessionId+sourceVersion`）

**生成：** `POST /relation-space/sessions/:sessionId/digest`

| 步骤 | 表 | 字段 |
|------|----|------|
| 读会话 | `zclaw_sessions` findFirst + `zclaw_messages` | `content`、`role`、`status`、`createdAt`、`updatedAt` |
| 调模型 | — | 本地或 relation-compute 远程 |
| 写摘要 | `relation_session_digests` 事务 upsert/update | `sessionId`、`ownerUserId`、`enterpriseId`、`sourceVersion`、`promptVersion`、`model`、`language`、`generatedTitle`、`summary`、`activities`(Json)、`artifacts`(Json)、`subjects`(Json)、`visibility`、`confidence`、`isCurrent` |
| 投影入图 | 3 张 relation 表（`projectDigest`） | person/conversation/activity/artifact 节点 + owns/participated_in/contains_activity/produced 边 + 证据 |

---

## V15 管理端 · 关系计算服务配置

**API：** `GET/POST /relation-space/admin/compute-config`、`POST .../test`（仅平台管理员）
**表：** `relation_compute_configs`（单行 `id='default'`）
**字段：** `baseUrl`、`apiKeyEncrypted`（AES-256-GCM）、`apiKeyMask`、`status`、`requestTimeoutMs`、`healthStatus`、`serviceVersion`、`protocolVersion`、`releaseSha`、`model`、`capabilities`(Json)、`lastHealthCheckAt`、`lastHealthError`

该配置决定 V11/V14 的 AI 计算走本地模型还是远程 relation-compute 服务。

---

## 数据依赖汇总（按表）

| 表 | 被哪些视图读 |
|----|-------------|
| `relation_nodes` | V1–V5（include）、V7、V8、V9、V10、V11、V12、V13 |
| `relation_edges` | V1–V5、V7、V8、V9、V11、V12 |
| `relation_evidences` | V1–V5（include）、V7、V8、V11 |
| `relation_session_digests` | V9、V13、V14 |
| `relation_question_history` | V11 |
| `relation_workstream_reviews` | V12、V13 |
| `relation_analysis_snapshots` | V10 |
| `relation_projection_jobs` | V13 |
| `relation_compute_configs` | V15 |
| `enterprise_memberships` / `enterprises` | 所有企业视图鉴权 + 证据授权 |
| `ragflow_documents` | 证据授权（accessScope=ragflow_document 的证据） |
| `zclaw_sessions` / `zclaw_messages` | V13、V14（源数据） |
