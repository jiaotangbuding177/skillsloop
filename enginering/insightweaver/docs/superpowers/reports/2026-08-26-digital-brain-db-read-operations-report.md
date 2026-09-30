# 组织关系数字大脑 — 读库操作清单 & 远端数据库核对报告

> 生成时间：2026-08-26
> 远端数据库：`postgresql://prod_admin:***@47.96.103.101:5432/insight_weaver?schema=public`
> 上游代码：`.tmp/insightweaver/`

---

## 一、总览：数据库表匹配状况

### 1.1 关系空间专属表（需创建）— 11 张全部缺失

| # | 表名 | Prisma Model | 用途 | 状态 |
|---|-------|-------------|------|------|
| 1 | `relation_nodes` | RelationNode | 图谱节点（人/部门/工作流/活动等） | ❌ **缺失** |
| 2 | `relation_edges` | RelationEdge | 图谱边（关系类型/置信度/权重） | ❌ **缺失** |
| 3 | `relation_evidences` | RelationEvidence | 证据记录（授权+溯源） | ❌ **缺失** |
| 4 | `relation_session_digests` | RelationSessionDigest | AI 生成的会话摘要 | ❌ **缺失** |
| 5 | `relation_analysis_snapshots` | RelationAnalysisSnapshot | 风险分析结果缓存 | ❌ **缺失** |
| 6 | `relation_question_history` | RelationQuestionHistory | 问答历史 | ❌ **缺失** |
| 7 | `relation_workstream_reviews` | RelationWorkstreamReview | 人工审核工作流记录 | ❌ **缺失** |
| 8 | `relation_projection_jobs` | RelationProjectionJob | 后台投影任务队列 | ❌ **缺失** |
| 9 | `relation_projection_checkpoints` | RelationProjectionCheckpoint | 变更检测游标 | ❌ **缺失** |
| 10 | `relation_memory_snapshots` | RelationMemorySnapshot | 记忆文件同步状态 | ❌ **缺失** |
| 11 | `relation_compute_configs` | RelationComputeConfig | 远程计算服务配置 | ❌ **缺失** |

### 1.2 源数据表（已存在，被关系空间读取）— 14 张全部匹配

| # | 表名 | 状态 | 字段匹配 |
|---|-------|------|---------|
| 1 | `users` | ✅ 存在 | ✅ 完全匹配 |
| 2 | `enterprises` | ✅ 存在 | ✅ 完全匹配 |
| 3 | `enterprise_memberships` | ✅ 存在 | ✅ 完全匹配 |
| 4 | `enterprise_departments` | ✅ 存在 | ✅ 完全匹配 |
| 5 | `enterprise_department_groups` | ✅ 存在 | ✅ 完全匹配 |
| 6 | `enterprise_department_group_members` | ✅ 存在 | ✅ 完全匹配 |
| 7 | `enterprise_builtin_agent_configs` | ✅ 存在 | ✅ 完全匹配 |
| 8 | `global_builtin_agent_configs` | ✅ 存在 | ✅ 完全匹配 |
| 9 | `zclaw_agent_instances` | ✅ 存在 | ✅ 完全匹配 |
| 10 | `zclaw_sessions` | ✅ 存在 | ✅ 完全匹配 |
| 11 | `zclaw_messages` | ✅ 存在 | ⚠️ **缺少 `updatedAt` 字段** |
| 12 | `ragflow_datasets` | ✅ 存在 | ✅ 完全匹配 |
| 13 | `ragflow_documents` | ✅ 存在 | ✅ 完全匹配 |
| 14 | `ragflow_graph_jobs` | ✅ 存在 | ✅ 完全匹配 |

### 1.3 字段级差异

| 表 | 字段 | 上游 Prisma 定义 | 远端 DB | 影响 |
|----|------|-----------------|---------|------|
| `zclaw_messages` | `updatedAt` | `DateTime @updatedAt` | **不存在** | ChangeScanner 中 `scanChatMessages` 读取 `updatedAt` 做增量变更检测会报错 |

**修复方案：**
```sql
ALTER TABLE zclaw_messages ADD COLUMN "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
-- 回填已有数据
UPDATE zclaw_messages SET "updatedAt" = "createdAt";
-- 添加索引（上游 schema 有此索引）
CREATE INDEX "zclaw_messages_updated_idx" ON zclaw_messages("updatedAt", "id");
```

---

## 二、每张缺失表的完整字段定义

### 2.1 `relation_nodes` — 图谱节点

```sql
CREATE TABLE "relation_nodes" (
    "id"            TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "spaceKey"      TEXT NOT NULL,        -- 'personal:{userId}' 或 'enterprise:{enterpriseId}'
    "spaceType"     TEXT NOT NULL,        -- 'personal' | 'enterprise'
    "enterpriseId"  TEXT,
    "ownerUserId"   TEXT,
    "identityKey"   TEXT NOT NULL,        -- 如 'user:{id}', 'department:{id}', 'workstream:{...}'
    "nodeType"      TEXT NOT NULL,        -- person/enterprise/department/workstream/activity/artifact 等
    "displayName"   TEXT NOT NULL,
    "canonicalName" TEXT,
    "language"      TEXT,
    "properties"    JSONB,
    "status"        TEXT NOT NULL DEFAULT 'active',
    "createdAt"     TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"     TIMESTAMP(3) NOT NULL,
    "isDeleted"     BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_nodes_pkey" PRIMARY KEY ("id")
);
-- 唯一约束
CREATE UNIQUE INDEX "relation_nodes_space_identity_uq" ON "relation_nodes"("spaceKey", "identityKey");
-- 查询索引
CREATE INDEX "relation_nodes_space_type_status_idx" ON "relation_nodes"("spaceKey", "nodeType", "status", "isDeleted");
CREATE INDEX "relation_nodes_enterprise_status_idx" ON "relation_nodes"("enterpriseId", "status", "isDeleted");
CREATE INDEX "relation_nodes_owner_status_idx" ON "relation_nodes"("ownerUserId", "status", "isDeleted");
```

### 2.2 `relation_edges` — 图谱边

```sql
CREATE TABLE "relation_edges" (
    "id"            TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "spaceKey"      TEXT NOT NULL,
    "spaceType"     TEXT NOT NULL,
    "enterpriseId"  TEXT,
    "ownerUserId"   TEXT,
    "edgeKey"       TEXT NOT NULL,        -- 唯一边标识
    "sourceNodeId"  TEXT NOT NULL,
    "targetNodeId"  TEXT NOT NULL,
    "relationType"  TEXT NOT NULL,        -- owns/member_of/contributes_to/collaborates_on 等
    "factType"      TEXT NOT NULL,        -- system/extracted/inferred
    "weight"        DOUBLE PRECISION NOT NULL DEFAULT 1,
    "confidence"    DOUBLE PRECISION NOT NULL DEFAULT 1,
    "occurredAt"    TIMESTAMP(3),
    "validFrom"     TIMESTAMP(3),
    "validTo"       TIMESTAMP(3),
    "properties"    JSONB,
    "status"        TEXT NOT NULL DEFAULT 'active',
    "createdAt"     TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"     TIMESTAMP(3) NOT NULL,
    "isDeleted"     BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_edges_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relation_edges_sourceNodeId_fkey" FOREIGN KEY ("sourceNodeId") REFERENCES "relation_nodes"("id") ON DELETE CASCADE,
    CONSTRAINT "relation_edges_targetNodeId_fkey" FOREIGN KEY ("targetNodeId") REFERENCES "relation_nodes"("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX "relation_edges_space_edge_uq" ON "relation_edges"("spaceKey", "edgeKey");
CREATE INDEX "relation_edges_space_source_status_idx" ON "relation_edges"("spaceKey", "sourceNodeId", "status", "isDeleted");
CREATE INDEX "relation_edges_space_target_status_idx" ON "relation_edges"("spaceKey", "targetNodeId", "status", "isDeleted");
CREATE INDEX "relation_edges_space_relation_status_idx" ON "relation_edges"("spaceKey", "relationType", "status", "isDeleted");
```

### 2.3 `relation_evidences` — 证据/授权记录

```sql
CREATE TABLE "relation_evidences" (
    "id"                   TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "spaceKey"             TEXT NOT NULL,
    "spaceType"            TEXT NOT NULL,
    "enterpriseId"         TEXT,
    "ownerUserId"          TEXT,
    "evidenceKey"          TEXT NOT NULL,
    "nodeId"               TEXT,
    "edgeId"               TEXT,
    "sourceType"           TEXT NOT NULL,    -- chat_session/ragflow_graph/memory_file 等
    "sourceId"             TEXT NOT NULL,
    "sourceVersion"        TEXT,
    "locator"              JSONB,
    "excerpt"              TEXT,
    "confidence"           DOUBLE PRECISION NOT NULL DEFAULT 1,
    "occurredAt"           TIMESTAMP(3),
    "accessScope"          TEXT NOT NULL,    -- owner_only/enterprise_member/ragflow_document
    "permissionSourceType" TEXT,
    "permissionSourceId"   TEXT,
    "permissionVersion"    INTEGER,
    "status"               TEXT NOT NULL DEFAULT 'active',
    "createdAt"            TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"            TIMESTAMP(3) NOT NULL,
    "isDeleted"            BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_evidences_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relation_evidences_nodeId_fkey" FOREIGN KEY ("nodeId") REFERENCES "relation_nodes"("id") ON DELETE CASCADE,
    CONSTRAINT "relation_evidences_edgeId_fkey" FOREIGN KEY ("edgeId") REFERENCES "relation_edges"("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX "relation_evidences_space_evidence_uq" ON "relation_evidences"("spaceKey", "evidenceKey");
CREATE INDEX "relation_evidences_space_source_status_idx" ON "relation_evidences"("spaceKey", "sourceType", "sourceId", "status", "isDeleted");
CREATE INDEX "relation_evidences_edge_status_idx" ON "relation_evidences"("edgeId", "status", "isDeleted");
CREATE INDEX "relation_evidences_node_status_idx" ON "relation_evidences"("nodeId", "status", "isDeleted");
CREATE INDEX "relation_evidences_permission_source_idx" ON "relation_evidences"("permissionSourceType", "permissionSourceId");
```

### 2.4 `relation_session_digests` — 会话摘要

```sql
CREATE TABLE "relation_session_digests" (
    "id"             TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "sessionId"      TEXT NOT NULL,
    "ownerUserId"    TEXT NOT NULL,
    "enterpriseId"   TEXT,
    "sourceVersion"  TEXT NOT NULL,
    "promptVersion"  TEXT NOT NULL,
    "model"          TEXT NOT NULL,
    "language"       TEXT NOT NULL DEFAULT 'zh',
    "generatedTitle" TEXT NOT NULL,
    "summary"        TEXT NOT NULL,
    "activities"     JSONB NOT NULL,
    "artifacts"      JSONB NOT NULL,
    "subjects"       JSONB NOT NULL,
    "visibility"     TEXT NOT NULL DEFAULT 'owner_only',
    "confidence"     DOUBLE PRECISION NOT NULL DEFAULT 1,
    "isCurrent"      BOOLEAN NOT NULL DEFAULT true,
    "createdAt"      TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"      TIMESTAMP(3) NOT NULL,
    "isDeleted"      BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_session_digests_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "relation_session_digests_session_version_uq" ON "relation_session_digests"("sessionId", "sourceVersion");
CREATE INDEX "relation_session_digests_owner_current_idx" ON "relation_session_digests"("ownerUserId", "isCurrent", "isDeleted");
CREATE INDEX "relation_session_digests_enterprise_current_idx" ON "relation_session_digests"("enterpriseId", "visibility", "isCurrent", "isDeleted");
CREATE INDEX "relation_session_digests_session_current_idx" ON "relation_session_digests"("sessionId", "isCurrent", "isDeleted");
```

### 2.5 `relation_analysis_snapshots` — 分析快照

```sql
CREATE TABLE "relation_analysis_snapshots" (
    "id"                TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "enterpriseId"      TEXT NOT NULL,
    "analysisType"      TEXT NOT NULL,
    "question"          TEXT NOT NULL,
    "answer"            TEXT NOT NULL,
    "model"             TEXT NOT NULL,
    "evidenceCount"     INTEGER NOT NULL DEFAULT 0,
    "truncated"         BOOLEAN NOT NULL DEFAULT false,
    "graphUpdatedAt"    TIMESTAMP(3),
    "generatedByUserId" TEXT NOT NULL,
    "generatedAt"       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt"         TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"         TIMESTAMP(3) NOT NULL,
    CONSTRAINT "relation_analysis_snapshots_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "relation_analysis_snapshots_enterprise_type_uq" ON "relation_analysis_snapshots"("enterpriseId", "analysisType");
CREATE INDEX "relation_analysis_snapshots_enterprise_generated_idx" ON "relation_analysis_snapshots"("enterpriseId", "generatedAt");
```

### 2.6 `relation_question_history` — 问答历史

```sql
CREATE TABLE "relation_question_history" (
    "id"                 TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "enterpriseId"       TEXT NOT NULL,
    "question"           TEXT NOT NULL,
    "answer"             TEXT NOT NULL,
    "model"              TEXT NOT NULL,
    "evidenceCount"      INTEGER NOT NULL DEFAULT 0,
    "truncated"          BOOLEAN NOT NULL DEFAULT false,
    "generatedByUserId"  TEXT NOT NULL,
    "anchorNodeId"       TEXT,
    "anchorNodeName"     TEXT,
    "anchorNodeType"     TEXT,
    "questionScope"      TEXT NOT NULL DEFAULT 'enterprise',
    "departmentNodeId"   TEXT,
    "departmentNodeName" TEXT,
    "generatedAt"        TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt"          TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "relation_question_history_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "relation_question_history_enterprise_user_time_idx" ON "relation_question_history"("enterpriseId", "generatedByUserId", "generatedAt");
CREATE INDEX "relation_question_history_scope_time_idx" ON "relation_question_history"("enterpriseId", "generatedByUserId", "questionScope", "departmentNodeId", "generatedAt");
```

### 2.7 `relation_workstream_reviews` — 工作流审核

```sql
CREATE TABLE "relation_workstream_reviews" (
    "id"              TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "enterpriseId"    TEXT NOT NULL,
    "anchorKey"       TEXT NOT NULL,
    "action"          TEXT NOT NULL,       -- rename/merge/split/reject_workstream 等
    "title"           TEXT,
    "targetAnchorKey" TEXT,
    "splitGroups"     JSONB,
    "reason"          TEXT,
    "createdByUserId" TEXT NOT NULL,
    "createdAt"       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"       TIMESTAMP(3) NOT NULL,
    "isDeleted"       BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_workstream_reviews_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "relation_workstream_reviews_enterprise_anchor_uq" ON "relation_workstream_reviews"("enterpriseId", "anchorKey");
CREATE INDEX "relation_workstream_reviews_enterprise_action_idx" ON "relation_workstream_reviews"("enterpriseId", "action", "isDeleted");
```

### 2.8 `relation_projection_jobs` — 投影任务队列

```sql
CREATE TABLE "relation_projection_jobs" (
    "id"                TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "jobType"           TEXT NOT NULL,     -- personal_identity/enterprise_identity/chat_session/ragflow_graph 等
    "idempotencyKey"    TEXT NOT NULL,
    "scopeType"         TEXT NOT NULL,     -- personal/enterprise
    "ownerUserId"       TEXT,
    "enterpriseId"      TEXT,
    "datasetMappingId"  TEXT,
    "sourceId"          TEXT,
    "sourceVersion"     TEXT,
    "payload"           JSONB,
    "cursor"            JSONB,
    "result"            JSONB,
    "status"            TEXT NOT NULL DEFAULT 'pending',
    "attemptCount"      INTEGER NOT NULL DEFAULT 0,
    "maxAttempts"       INTEGER NOT NULL DEFAULT 3,
    "nextAttemptAt"     TIMESTAMP(3),
    "lockedAt"          TIMESTAMP(3),
    "lockedBy"          TEXT,
    "startedAt"         TIMESTAMP(3),
    "finishedAt"        TIMESTAMP(3),
    "lastError"         TEXT,
    "requestedByUserId" TEXT,
    "createdAt"         TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"         TIMESTAMP(3) NOT NULL,
    "isDeleted"         BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT "relation_projection_jobs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "relation_projection_jobs_requestedByUserId_fkey" FOREIGN KEY ("requestedByUserId") REFERENCES "users"("id") ON DELETE SET NULL,
    CONSTRAINT "relation_projection_jobs_datasetMappingId_fkey" FOREIGN KEY ("datasetMappingId") REFERENCES "ragflow_datasets"("id") ON DELETE SET NULL
);
CREATE UNIQUE INDEX "relation_projection_jobs_idempotencyKey_key" ON "relation_projection_jobs"("idempotencyKey");
CREATE INDEX "relation_projection_jobs_ready_idx" ON "relation_projection_jobs"("status", "nextAttemptAt", "createdAt");
CREATE INDEX "relation_projection_jobs_owner_idx" ON "relation_projection_jobs"("scopeType", "ownerUserId", "createdAt");
CREATE INDEX "relation_projection_jobs_enterprise_idx" ON "relation_projection_jobs"("scopeType", "enterpriseId", "createdAt");
CREATE INDEX "relation_projection_jobs_type_idx" ON "relation_projection_jobs"("jobType", "createdAt");
CREATE INDEX "relation_projection_jobs_dataset_idx" ON "relation_projection_jobs"("datasetMappingId", "createdAt");
CREATE INDEX "relation_projection_jobs_source_idx" ON "relation_projection_jobs"("jobType", "sourceId", "createdAt");
```

### 2.9 `relation_projection_checkpoints` — 变更检测游标

```sql
CREATE TABLE "relation_projection_checkpoints" (
    "key"             TEXT NOT NULL,       -- 如 'relation_identity_changes:users'
    "cursorTimestamp"  TIMESTAMP(3),
    "cursorId"        TEXT,
    "lastScanAt"      TIMESTAMP(3),
    "lastSuccessAt"   TIMESTAMP(3),
    "lastError"       TEXT,
    "version"         INTEGER NOT NULL DEFAULT 0,
    "createdAt"       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"       TIMESTAMP(3) NOT NULL,
    CONSTRAINT "relation_projection_checkpoints_pkey" PRIMARY KEY ("key")
);
CREATE INDEX "relation_projection_checkpoints_success_idx" ON "relation_projection_checkpoints"("lastSuccessAt");
```

### 2.10 `relation_memory_snapshots` — 记忆文件同步

```sql
CREATE TABLE "relation_memory_snapshots" (
    "id"                           TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    "ownerUserId"                  TEXT NOT NULL,
    "enterpriseId"                 TEXT NOT NULL,
    "enterpriseOpenClawInstanceId"  TEXT NOT NULL,
    "path"                         TEXT NOT NULL,
    "entryType"                    TEXT NOT NULL,
    "sourceVersion"                TEXT NOT NULL,
    "contentHash"                  TEXT,
    "remoteSize"                   INTEGER,
    "remoteUpdatedAt"              TIMESTAMP(3),
    "lastSeenScanId"               TEXT NOT NULL,
    "status"                       TEXT NOT NULL DEFAULT 'active',
    "missingAt"                    TIMESTAMP(3),
    "createdAt"                    TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"                    TIMESTAMP(3) NOT NULL,
    CONSTRAINT "relation_memory_snapshots_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "relation_memory_snapshots_owner_instance_path_uq" ON "relation_memory_snapshots"("ownerUserId", "enterpriseOpenClawInstanceId", "path");
CREATE INDEX "relation_memory_snapshots_owner_instance_status_idx" ON "relation_memory_snapshots"("ownerUserId", "enterpriseOpenClawInstanceId", "status");
CREATE INDEX "relation_memory_snapshots_scan_idx" ON "relation_memory_snapshots"("lastSeenScanId");
```

### 2.11 `relation_compute_configs` — 远程计算配置

```sql
CREATE TABLE "relation_compute_configs" (
    "id"                TEXT NOT NULL DEFAULT 'default',
    "baseUrl"           TEXT NOT NULL,
    "apiKeyEncrypted"   TEXT NOT NULL,
    "apiKeyMask"        TEXT,
    "status"            TEXT NOT NULL DEFAULT 'active',
    "requestTimeoutMs"  INTEGER NOT NULL DEFAULT 180000,
    "healthStatus"      TEXT,
    "serviceVersion"    TEXT,
    "protocolVersion"   TEXT,
    "releaseSha"        TEXT,
    "model"             TEXT,
    "capabilities"      JSONB,
    "lastHealthCheckAt" TIMESTAMP(3),
    "lastHealthError"   TEXT,
    "createdAt"         TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"         TIMESTAMP(3) NOT NULL,
    CONSTRAINT "relation_compute_configs_pkey" PRIMARY KEY ("id")
);
```

---

## 三、按模块/接口详列读操作 → 表 → 字段

### 模块 1: RelationQueryService — 图谱查询引擎

**源文件:** `apps/api/src/relation-space/relation-query.service.ts`

| API 接口 | 方法 | 读取表 | 读取字段 | WHERE 条件 |
|---------|------|--------|---------|-----------|
| `GET /relation-space/subgraph` | `resolveSpace()` | `enterprise_memberships` | `id` | userId, enterpriseId, status='active', isDeleted=false; JOIN enterprises(status='active') |
| | `loadAuthorizedEdges()` | `relation_edges` | ALL + include sourceNode, targetNode, evidences | spaceKey, status='active', isDeleted=false, relationType(可选) |
| | | `relation_nodes` | via include | anchorNodeIds OR 条件 |
| `GET /relation-space/path` | 内部调用 subgraph | 同上 | 同上 | 路径过滤 |
| `GET /relation-space/timeline` | 内部调用 subgraph | 同上 | 同上 | 时间排序 |
| `GET /relation-space/context` | `aiContext()` → subgraph | 同上 | 同上 | AI上下文 |
| `GET /relation-space/evidences/:id` | `evidenceDetail()` | `relation_evidences` | ALL + include node, edge→sourceNode, targetNode | id, status='active', isDeleted=false |

### 模块 2: RelationProjectionService — 投影写入引擎

**源文件:** `apps/api/src/relation-space/relation-projection.service.ts`

| 操作 | 读取表 | 读取字段 | 条件 |
|------|--------|---------|------|
| `projectFact()` 检查边 | `relation_edges` | sourceNodeId, targetNodeId, relationType, factType | spaceKey + edgeKey |
| `projectFact()` 检查证据 | `relation_evidences` | edgeId, sourceType, sourceId | spaceKey + evidenceKey |
| `retractSource()` | `relation_evidences` | edgeId | spaceKey, sourceType, sourceId, status='active' |
| `retractSource()` 计数 | `relation_evidences` | COUNT | spaceKey, edgeId, status='active' |
| `retractOrphanNodes()` | `relation_nodes` | UPDATE 无活跃边/证据的节点 | spaceKey, status='active' |
| `listActiveSourceIds()` | `relation_evidences` | DISTINCT sourceId | spaceKey, sourceType, status='active' |

### 模块 3: RelationIdentityProjectionService — 身份投影

**源文件:** `apps/api/src/relation-space/relation-identity-projection.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `syncPersonalAgentInstances()` | `users` | id WHERE id, status='active' |
| | `zclaw_agent_instances` | id, agentId, status, toolProfile, createdAt, updatedAt WHERE userId, scope='personal', status IN [active,provisioned] |
| `syncEnterpriseOrganization()` | `enterprises` | id, name, updatedAt WHERE id, status='active' |
| | `enterprise_memberships` | id, userId, role, realName, department, joinedAt, createdAt, updatedAt WHERE enterpriseId, status='active', user active |
| | `enterprise_departments` | id, name, sortOrder, createdAt, updatedAt WHERE enterpriseId |
| | `enterprise_department_groups` | id, departmentId, name, sortOrder, createdAt, updatedAt WHERE enterpriseId |
| | `enterprise_department_group_members` | id, groupId, departmentId, userId, createdAt WHERE groupId IN active groups |
| `syncEnterpriseAgentSkillConfiguration()` | `enterprises` | id, name |
| | `global_builtin_agent_configs` | id, agentKey, name, skillKeys, visibilityScope, createdAt, updatedAt WHERE isDeleted=false, isEnabled=true |
| | `enterprise_builtin_agent_configs` | id, agentKey, type, name, skillKeys, isEnabled, createdAt, updatedAt WHERE enterpriseId |

### 模块 4: ChatRelationProjectionService — 聊天投影

**源文件:** `apps/api/src/relation-space/chat-relation-projection.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `syncSession()` | `zclaw_sessions` | id, userId, title, locale, status, createdAt, updatedAt, isDeleted + user{status,isDeleted} + agentInstance{id,agentId,scope,enterpriseId,status,isDeleted} + messages{id,role,content,status,createdAt,updatedAt,isDeleted} |
| | `zclaw_messages` | 同上（通过 include） |

### 模块 5: RagflowGraphRelationProjectionService — RAGFlow 图谱投影

**源文件:** `apps/api/src/relation-space/ragflow-graph-relation-projection.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `projectGraphVersion()` | `ragflow_documents` | id, ragflowDocumentId, path, filename, permissionVersion WHERE datasetMappingId, ragflowDocumentId NOT NULL, uploadStatus != 'deleted' |
| `retractDataset()` | `ragflow_datasets` | id, scope, userId, enterpriseId WHERE id, isDeleted=false |

### 模块 6: MemoryRelationProjectionService — 记忆投影

**源文件:** `apps/api/src/relation-space/memory-relation-projection.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `syncScope()` | `relation_memory_snapshots` | upsert + findMany: id, path WHERE ownerUserId, enterpriseOpenClawInstanceId, status='active', lastSeenScanId != scanId |
| `retractUnavailableScope()` | `relation_memory_snapshots` | id, path WHERE ownerUserId, enterpriseOpenClawInstanceId, status='active' |

### 模块 7: RelationEvidenceAuthorizationService — 证据授权

**源文件:** `apps/api/src/relation-space/relation-evidence-authorization.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `authorizedEvidenceIds()` | `enterprise_memberships` | enterpriseId WHERE userId, enterpriseId IN [...], status='active' |
| | `ragflow_documents` | id, source, userId, enterpriseId, path, visibilityType, uploadStatus, isDeleted + dataset{scope,userId,enterpriseId,status,isDeleted} |

### 模块 8: RelationWorkIntelligenceService — 工作智能

**源文件:** `apps/api/src/relation-space/relation-work-intelligence.service.ts`

| API 接口 | 读取表 | 读取字段 |
|---------|--------|---------|
| `POST /sessions/:id/digest` | `zclaw_sessions` | id, userId, title, locale, updatedAt, agentInstance{enterpriseId}, messages{id,role,content,updatedAt} |
| | `relation_session_digests` | ALL WHERE sessionId, isCurrent=true |
| `GET /sessions/:id/digest` | `zclaw_sessions` | id |
| | `relation_session_digests` | ALL WHERE sessionId, ownerUserId, isCurrent=true |
| `GET /enterprise-builds/coverage` | `relation_projection_jobs` | ALL WHERE jobType='enterprise_semantic_build', enterpriseId |
| | `relation_nodes` | properties WHERE spaceKey, nodeType='workstream', status='active' |
| `POST /enterprise-builds` | `relation_projection_jobs` | ALL WHERE jobType, enterpriseId |
| `GET /enterprise-builds/latest` | `relation_projection_jobs` | ALL WHERE jobType, enterpriseId |
| `POST /workstreams/rebuild` | `relation_nodes` | UPDATE status='retracted' WHERE nodeType IN [workstream, business_object] |
| `GET /workstreams/reviews` | `relation_nodes` | ALL + include incomingEdges WHERE spaceKey, nodeType='workstream', status='active' |
| | `relation_workstream_reviews` | ALL WHERE enterpriseId, isDeleted=false |
| `POST /workstreams/reviews` | `relation_nodes` | id, identityKey WHERE id IN [...], spaceKey, nodeType='activity' |
| `GET /risks` | `relation_nodes` | id, identityKey, displayName WHERE spaceKey, nodeType='workstream' |
| | `relation_edges` | sourceNode{nodeType,identityKey,displayName}, confidence WHERE spaceKey, targetNodeId, relationType='contributes_to' |
| `GET /risk-analysis` | `relation_analysis_snapshots` | ALL WHERE enterpriseId + analysisType |
| `POST /risk-analysis/refresh` | `relation_nodes` | MAX(updatedAt) WHERE spaceKey, status='active' |
| `POST /ask` | `relation_edges` + nodes + evidences | 完整图谱查询链 |
| | `relation_question_history` | CREATE 返回 ALL |
| `GET /questions/history` | `relation_question_history` | ALL WHERE enterpriseId, generatedByUserId, anchorNodeId, questionScope |
| (内部) `enterpriseDigestInputs()` | `relation_session_digests` | ALL (分页) WHERE enterpriseId, visibility='enterprise_member', isCurrent=true |
| | `enterprise_memberships` | userId, realName, department |
| | `enterprise_department_group_members` | userId, groupId + group{name} |
| (内部) `enterpriseBuildCoverage()` | `zclaw_sessions` | id, userId, messages{id,content,updatedAt} |
| | `relation_session_digests` | ALL WHERE sessionId IN [...] |
| (内部) `assertActiveMembership()` | `enterprise_memberships` | role WHERE userId, enterpriseId, status='active' |

### 模块 9: RelationProjectionJobService — 投影任务管理

**源文件:** `apps/api/src/relation-space/relation-projection-job.service.ts`

| API 接口 | 读取表 | 读取字段 |
|---------|--------|---------|
| `POST /admin/projection-jobs` | `relation_projection_jobs` | ALL WHERE idempotencyKey |
| `GET /admin/projection-jobs` | `relation_projection_jobs` | ALL WHERE isDeleted=false + 过滤器 |
| `GET /admin/projection-jobs/:id` | `relation_projection_jobs` | ALL WHERE id |
| `POST /admin/projection-jobs/:id/retry` | `relation_projection_jobs` | ALL WHERE id, status='failed' |
| (内部) `claimNext()` | `relation_projection_jobs` | ALL WHERE pending/retry_pending/stale |

### 模块 10: RelationComputeConfigService — 计算配置管理

**源文件:** `apps/api/src/relation-space/relation-compute-config.service.ts`

| API 接口 | 读取表 | 读取字段 |
|---------|--------|---------|
| `GET /admin/compute-config` | `relation_compute_configs` | ALL WHERE id='default' |
| `POST /admin/compute-config` | `relation_compute_configs` | ALL WHERE id='default' + upsert |
| `POST /admin/compute-config/test` | `relation_compute_configs` | ALL WHERE id='default' + update |

### 模块 11: ChangeScannerService — 变更检测扫描

**源文件:** `apps/api/src/relation-space/relation-projection-change-scanner.service.ts`

| 扫描源 | 读取表 | 读取字段 |
|--------|--------|---------|
| users | `users` | id, updatedAt |
| personal_agent_instances | `zclaw_agent_instances` | id, userId, updatedAt WHERE scope='personal' |
| enterprises | `enterprises` | id, updatedAt |
| enterprise_memberships | `enterprise_memberships` | id, enterpriseId, updatedAt |
| enterprise_departments | `enterprise_departments` | id, enterpriseId, updatedAt |
| enterprise_department_groups | `enterprise_department_groups` | id, enterpriseId, updatedAt |
| enterprise_department_group_members | `enterprise_department_group_members` | id, createdAt + group{enterpriseId} |
| enterprise_agent_configs | `enterprise_builtin_agent_configs` | id, enterpriseId, updatedAt |
| global_agent_configs | `global_builtin_agent_configs` | id, updatedAt → 然后所有 enterprises.id |
| ragflow_graph_jobs | `ragflow_graph_jobs` | ALL + dataset{scope,userId,enterpriseId,status,isDeleted} WHERE status='succeeded' |
| zclaw_sessions | `zclaw_sessions` | id, userId, updatedAt |
| zclaw_messages | `zclaw_messages` | id, sessionId, **updatedAt**, session{userId} |

### 模块 12: MemoryProjectionScannerService — 记忆扫描

**源文件:** `apps/api/src/relation-space/memory-projection-scanner.service.ts`

| 操作 | 读取表 | 读取字段 |
|------|--------|---------|
| `scanOnce()` | `relation_projection_checkpoints` | ALL WHERE key (upsert + updateMany) |
| `enqueueUnavailableScopeRetractions()` | `relation_memory_snapshots` | DISTINCT ownerUserId, enterpriseOpenClawInstanceId WHERE status='active' |

---

## 四、数据流全景图

```
┌─────────────────────────────────────────┐
│         源数据表 (14张, 已存在)           │
│                                         │
│  users               enterprises        │
│  enterprise_memberships                 │
│  enterprise_departments                 │
│  enterprise_department_groups           │
│  enterprise_department_group_members    │
│  enterprise_builtin_agent_configs       │
│  global_builtin_agent_configs           │
│  zclaw_agent_instances                  │
│  zclaw_sessions                         │
│  zclaw_messages      ← ⚠️ 缺 updatedAt │
│  ragflow_datasets                       │
│  ragflow_documents                      │
│  ragflow_graph_jobs                     │
└────────────────┬────────────────────────┘
                 │ 读取
                 ▼
┌─────────────────────────────────────────┐
│      ChangeScanner (轮询11+张源表)       │
│      → 检测 updatedAt/cursor 变化        │
│      → 入队 ProjectionJobs              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Projection Adapters                │
│  Identity / Chat / RAGFlow / Memory     │
│      → projectFact()                    │
│      → 写入 relation_nodes/edges/       │
│        evidences                        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      关系空间专属表 (11张, 全部缺失)       │
│                                         │
│  relation_nodes          (图谱节点)      │
│  relation_edges          (图谱边)        │
│  relation_evidences      (证据/授权)     │
│  relation_session_digests (会话摘要)     │
│  relation_analysis_snapshots (分析缓存)  │
│  relation_question_history (问答历史)    │
│  relation_workstream_reviews (人工审核)  │
│  relation_projection_jobs (任务队列)     │
│  relation_projection_checkpoints (游标)  │
│  relation_memory_snapshots (记忆同步)    │
│  relation_compute_configs (计算配置)     │
└────────────────┬────────────────────────┘
                 │ 读取
                 ▼
┌─────────────────────────────────────────┐
│      Query API → 前端可视化              │
│  subgraph / path / timeline / context   │
│  risks / risk-analysis / ask            │
│  workstreams / digests / history        │
└─────────────────────────────────────────┘
```

---

## 五、执行计划：需要做什么

### Step 1: 修复 `zclaw_messages` 缺失字段

```sql
ALTER TABLE "zclaw_messages" ADD COLUMN "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP;
UPDATE "zclaw_messages" SET "updatedAt" = "createdAt";
CREATE INDEX "zclaw_messages_updated_idx" ON "zclaw_messages"("updatedAt", "id");
```

### Step 2: 合并上游 Prisma Schema

将 `.tmp/insightweaver/packages/db/prisma/schema.prisma` 中新增的 11 个 model + User model 的 `requestedRelationProjectionJobs` 关系 + RagflowDataset 的 `relationProjectionJobs` 关系合并到主工作区 `packages/db/prisma/schema.prisma`。

### Step 3: 执行数据库迁移

```bash
cd packages/db
npx prisma migrate dev --name add_relation_space_tables
# 或
npx prisma db push
```

### Step 4: 验证

```bash
npx prisma migrate status  # 确认迁移成功
npx prisma generate        # 生成 Prisma Client
```

---

## 六、统计摘要

| 类别 | 数量 |
|------|------|
| 需创建的关系空间表 | **11 张** |
| 已存在的源数据表 | **14 张** |
| 需修复的字段差异 | **1 处** (zclaw_messages.updatedAt) |
| 读操作涉及的 Service 文件 | **12 个** |
| 总计不同读操作 | **72+ 处** |
| API 端点（触发读） | **20+ 个** |
| 核心图谱表 | 3 (nodes, edges, evidences) |
| 任务/配置表 | 3 (projection_jobs, checkpoints, compute_configs) |
| 摘要/分析表 | 4 (session_digests, analysis_snapshots, question_history, workstream_reviews) |
| 记忆跟踪表 | 1 (memory_snapshots) |
