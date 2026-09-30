# EvoMind 技术深度调研 — 基于代码实际实现

> 本文档基于 InsightWeaver 代码库的实际代码调研，每条回答均附带真实做法 + 关键类名/表名/字段名

---

## 1. relation-compute 解耦重构（8.6k 行抽取）

### 1.1 为什么要从 8.6k 代码里抽出来

**原痛点**：

| 痛点 | 具体表现 |
|------|----------|
| **耦合严重** | 旧的 `apps/api/src/relation-space/` 包含 37+ 文件，`RelationSemanticAiService`（1816 行）直接调用 DashScope LLM API，LLM API Key（付费、敏感）与主平台进程混合，主要是计费机制的需求，无法正常进行计费隔离 |
| **编译慢** | 单体应用 30+ NestJS 模块，TypeScript 增量编译耗时长 |
| **难测试** | 图谱构建、LLM 推理、权限校验、数据同步全在一个进程，单元测试需 mock 大量外部依赖 |
| **部署耦合** | 图谱计算（有状态、CPU 密集）与主平台（请求密集）共享资源，无法独立扩缩容 |

**解耦目标**：

- **独立部署**：relation-compute 作为独立服务，可独立扩缩容、独立发布
- **API Key 隔离**：DashScope API Key 仅存于 compute 服务，不暴露给主平台
- **协议版本化**：双协议版本（v1 健康检查 + v2 数据面）允许独立演进
- **关注点分离**：主平台负责源数据同步 + UI 渲染；compute 负责 LLM 推理 + 图谱存储 + 智能分析

### 1.2 服务边界划分

**evomind（主平台）保留**：

```
apps/api/src/relation-space/
├── RelationComputeConfigService       # 配置 + HTTP 客户端（AES-256-GCM 加密 API Key）
├── RelationDataPlaneGatewayService    # 鉴权 + 源数据同步 + 代理转发
├── RelationTokenSettlementScheduler   # 计费同步（60s 周期）
└── Controllers:
    ├── RelationQueryController        # 图谱查询（subgraph, evidence）
    ├── RelationWorkIntelligenceController  # 摘要、构建、提问
    └── RelationComputeAdminController      # 配置、测试、日志
```

**主平台拥有的数据**：
- `User`, `Enterprise`, `EnterpriseMembership`（用户/企业/成员）
- `ZclawSession`, `ZclawMessage`（会话/消息）
- `RelationComputeConfig`（远程 compute 配置）
- `RelationComputeTenantState`（租户状态游标）

**relation-compute（独立服务）拥有**：

```
/api/internal/relation-compute/
├── v1/health              # 健康检查
├── v1/complete            # LLM 推理（遗留）
├── v2/tenants/:key/
│   ├── sources/sync       # 源数据同步
│   ├── builds             # 图谱构建
│   ├── graph/query        # 图谱查询
│   ├── questions          # 智能提问
│   ├── workstream-reviews # 工作流评审
│   └── ...
├── v2/logs                # 调用日志
└── v2/token-settlements   # 计费结算
```

**compute 拥有的数据**（11 张 relation 图表，已迁至独立数据库）：
- `RelationNode`, `RelationEdge`, `RelationEvidence`
- `RelationSessionDigest`, `RelationAnalysisSnapshot`
- `RelationWorkstreamReview`, `RelationQuestionHistory`
- `RelationProjectionJob`, `RelationProjectionCheckpoint`
- `RelationMemorySnapshot`
- `RelationMirrorMember`, `RelationMirrorDocument`, `RelationMirrorSharedPath`（权限镜像表）

### 1.3 输入输出契约

**协议包**：`packages/relation-contract/src/index.ts`

```typescript
// 协议版本
RELATION_COMPUTE_PROTOCOL_VERSION = "1.0.0"        // 控制面（health + complete）
RELATION_DATA_PLANE_PROTOCOL_VERSION = "2.0.0"     // 数据面（完整图谱操作）

// 能力声明（13 项）
RELATION_COMPUTE_CAPABILITIES = [
  'session_digest',           // 会话摘要
  'activity_normalization',   // 活动归一化
  'artifact_normalization',   // 产物归一化
  'workstream_inference',     // 工作流推理
  'business_object_normalization',  // 业务对象归一化
  'risk_analysis',            // 风险分析
  'graph_question',           // 图谱提问
  'node_question',            // 节点提问
  'persistent_graph',         // 持久化图谱
  'source_sync',              // 源数据同步
  'projection_jobs',          // 投影任务
  'graph_query',              // 图谱查询
  'review_feedback'           // 评审反馈
]

// 请求限制
RELATION_COMPUTE_LIMITS = {
  systemCharacters: 100_000,
  contentCharacters: 1_500_000,
  requestBytes: 2_000_000,
  sourceSyncRequestBytes: 32_000_000
}
```

**核心类型**：

```typescript
// 请求（v1 complete）
interface RelationComputeRequest {
  responseType: "json" | "text"
  system: string
  content: string
}

// 响应
interface RelationComputeResponse {
  result: Record<string, unknown> | string
  protocolVersion: string
  releaseSha: string
  model: string
}

// 健康检查
interface RelationComputeHealth {
  ok: true
  service: "insightweaver-relation-compute"
  protocolVersion: string
  releaseSha: string
  capabilities: RelationComputeCapability[]
  model: string
}

// 数据面信封（v2）
interface RelationDataPlaneEnvelope<T> {
  data: T
  protocolVersion: "2.0.0"
  releaseSha: string
}
```

### 1.4 服务间通信方式

**HTTP + Bearer Token**

```typescript
// RelationComputeConfigService.requestForEnterprise()
async requestForEnterprise<T>(enterpriseId: string, path: string, init: RequestInit = {}) {
  const remote = await this.resolveRemote(false)
  if (!remote) return null
  
  const resolvedPath = path.replace(":tenantKey", encodeURIComponent(this.tenantKeyFor(enterpriseId)))
  const response = await this.fetchWithTimeout(
    `${remote.baseUrl}${resolvedPath}`,
    {
      ...init,
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${remote.apiKey}`,
        ...(init.headers ?? {})
      }
    },
    remote.timeoutMs
  )
  
  const payload = await response.json() as RelationDataPlaneEnvelope<T>
  if (payload.protocolVersion !== RELATION_DATA_PLANE_PROTOCOL_VERSION) {
    throw new BadGatewayException(`协议不兼容`)
  }
  return { data: payload.data }
}
```

**租户标识**：

```typescript
// 当前一对一拓扑：tenantKey === enterpriseId
tenantKeyFor(enterpriseId: string) {
  return enterpriseId
}
```

### 1.5 部署模型

**独立进程，同 repo 模块（待拆分）**

- 当前状态：compute 服务代码在 `.tmp/relation-compute/`（独立项目，未纳入主 workspace）
- 目标架构：compute 作为独立微服务部署，通过 HTTPS + API Key 与主平台通信
- 本地降级：`RELATION_LOCAL_COMPUTE_ENABLED=true` 环境变量可启用本地 fallback（生产环境不设置）

---

## 2. 手绘 SVG 力导向图

### 2.1 算法：自研同心环布局（非 d3-force）

**文件**：`apps/web/src/components/relation-space/RelationGraphView.tsx`

**关键发现**：关系图谱使用**完全自研的确定性布局算法**，无任何物理模拟，非 d3-force，非 sigma.js。

**两种布局策略**：

| 模式 | 算法 | 入口函数 | 行号 |
|------|------|----------|------|
| workstreams / department / personal | **同心环布局** | `buildSingleConcentricRelationLayout()` | 800 |
| collaboration / overlap | **分层层次布局** | `buildLayeredCollaborationLayout()` | 1024 |

**同心环布局核心逻辑**：

```typescript
// 1. 节点按 nodeType 分配整数 rank（层级）
const nodeRank = (nodeType: string): number => {
  switch (nodeType) {
    case 'enterprise': return 0
    case 'department': return 1
    case 'department_group': case 'group': return 2
    case 'person': return 3
    case 'conversation': return 4
    case 'activity': return 5
    case 'workstream': case 'artifact': return 6
    case 'business_object': return 7
    default: return 6
  }
}

// 2. BFS 从锚点（department/business_object）出发，分配"分支"
buildStructuralBranches()  // line 492
buildLayoutBranches()      // line 582

// 3. 每个 rank 形成一个环，环的半径由节点数量决定
relationGraphRings()       // line 746
// 常量：FIRST_RING_RADIUS = 110, RING_GAP = 150, NODE_ARC_GAP = 118

// 4. 节点在环上的角度位置由其所属分支的节点数比例决定
buildRankBranchArcs()      // line 714
```

**分层层次布局核心逻辑**：

```typescript
// 7 层水平分层
const layers = [
  'business_object',  // 第 0 层
  'workstream',       // 第 1 层
  'activity',         // 第 2 层
  'conversation',     // 第 3 层
  'person',           // 第 4 层
  'group',            // 第 5 层
  'department'        // 第 6 层
]

// 重心法排序（4 次迭代）最小化边交叉
for (let i = 0; i < 4; i++) {
  // forward + backward passes
  // lines 995-1002
}
```

### 2.2 布局计算位置：100% 在浏览器端

**后端返回的数据不包含坐标**：

```typescript
// 后端 API：GET /api/relation-space/subgraph
// 返回：RelationSubgraphResponse
{
  nodes: RelationGraphNodeRecord[]  // 无 x, y 坐标
  edges: RelationGraphEdgeRecord[]
  availableNodeCount: number
  availableEdgeCount: number
  truncated: boolean
}

// 前端在 React useMemo 中计算布局
const layout = React.useMemo(() => {
  return buildConcentricRelationLayout(filteredNodes, filteredEdges, perspective)
}, [filteredNodes, filteredEdges, perspective])
// line 1194
```

**用户可拖拽节点**：

```tsx
<circle
  cx={node.x}
  cy={node.y}
  r={nodeRadius}
  onPointerDown={(e) => handleNodeDragStart(e, node)}
/>
// line 1672-1678
```

### 2.3 节点/边数据来源：远程 compute 服务

**数据流**：

```
前端 → GET /api/relation-space/subgraph
     → RelationQueryController.subgraph()
     → RelationDataPlaneGatewayService.query()
     → HTTP POST {compute}/v2/tenants/{enterpriseId}/graph/query
     → 返回 RelationGraphQueryResult
```

**数据面网关**：

```typescript
// apps/api/src/relation-space/relation-data-plane-gateway.service.ts
async query(userId: string, enterpriseId: string, input: RelationSubgraphInput) {
  const response = await this.compute.requestForEnterprise<RelationGraphQueryResult>(
    enterpriseId,
    this.path(enterpriseId, "graph/query"),
    {
      method: "POST",
      body: JSON.stringify({
        scope: input.scope,
        anchorNodeId: input.anchorNodeId,
        hops: input.hops,
        limit: input.limit,
        nodeLimit: input.nodeLimit,
        relationTypes: input.relationTypes,
        nodeTypes: input.nodeTypes
      })
    }
  )
  return response.data
}
```

**数据库不存储图谱数据**：

Prisma 数据库仅用于：
- `assertMember()` 权限校验
- `RelationComputeTenantState` 存储构建状态游标

图谱数据（节点、边、证据）全部存储在远程 compute 服务的独立数据库。

---

## 3. GraphRAG

### 3.1 哈希去重：SHA-256 对完整文件二进制

**文件**：`apps/api/src/zclaw/ragflow/ragflow.service.ts`

**哈希算法**：

```typescript
// line 4287-4292
private toFileInfo(file: FileBinary) {
  return {
    sizeBytes: BigInt(file.contentLength ?? file.buffer.length),
    contentHash: createHash('sha256').update(file.buffer).digest('hex')
  }
}
```

**哈希对象**：完整文件二进制 buffer（非文本、非 chunk）

**存储模型**：

```prisma
// packages/db/prisma/schema.prisma, line 1954-1978
model RagflowFileBlob {
  id               String   @id @default(uuid())
  datasetMappingId String
  contentHash      String   // SHA-256 hex
  ragflowDocumentId String?
  filename         String
  mimeType         String
  sizeBytes        BigInt?
  refCount         Int      @default(0)  // 引用计数
  status           String   @default("uploaded")  // uploaded | deleted | parsing
  
  @@unique([datasetMappingId, contentHash], map: "ragflow_blob_dataset_hash_uq")
  @@map("ragflow_file_blobs")
}
```

**去重逻辑**：

```typescript
// ensureFileBlob() line 2957-3042
async ensureFileBlob(datasetMappingId: string, file: FileBinary) {
  const { contentHash, sizeBytes } = this.toFileInfo(file)
  
  // 1. 查找同哈希的 blob
  const existing = await this.prisma.ragflowFileBlob.findUnique({
    where: { datasetMappingId_contentHash: { datasetMappingId, contentHash } }
  })
  
  if (existing) {
    if (existing.status === 'deleted') {
      // 2a. 已删除的 blob → 原地复活（同哈希，重传 Ragflow）
      const remoteDocId = await this.ragflowClient.uploadDocument(...)
      await this.prisma.ragflowFileBlob.update({
        where: { id: existing.id },
        data: {
          status: 'uploaded',
          ragflowDocumentId: remoteDocId,
          filename: file.originalname,
          mimeType: file.mimetype,
          sizeBytes
        }
      })
      return { record: existing, wasUploaded: true }
    }
    
    // 2b. 存在的 blob → 纯去重命中（不上传）
    return { record: existing, wasUploaded: false }
  }
  
  // 3. 新 blob → 上传并创建记录
  try {
    const remoteDocId = await this.ragflowClient.uploadDocument(...)
    const record = await this.prisma.ragflowFileBlob.create({
      data: {
        datasetMappingId,
        contentHash,
        ragflowDocumentId: remoteDocId,
        filename: file.originalname,
        mimeType: file.mimetype,
        sizeBytes,
        refCount: 1,
        status: 'uploaded'
      }
    })
    return { record, wasUploaded: true }
  } catch (error) {
    if (error.code === 'P2002') {
      // 唯一约束冲突（并发）→ 补偿删除远程文档，返回已存在的记录
      await this.ragflowClient.deleteDocuments(target, [remoteDocId])
      const raced = await this.prisma.ragflowFileBlob.findUnique(...)
      return { record: raced, wasUploaded: false }
    }
    throw error
  }
}
```

**配额计量也使用哈希**：

```typescript
// resolveRagflowCapability() line 3686-3753
const existingBlob = await this.prisma.ragflowFileBlob.findFirst({
  where: { datasetMappingId, contentHash, status: 'uploaded' }
})

if (existingBlob) {
  // 已存在 → 不增加配额消耗
  projectedBytes = usedBytes
} else {
  // 新文件 → 增加配额
  projectedBytes = usedBytes + sizeBytes
}
```

### 3.2 状态机：7 态图谱状态 + 6 态任务状态

**图谱状态（`RagflowDataset.graphStatus`）**：

```typescript
// ragflow-graph.service.ts line 25-32
type RagflowGraphDatasetStatus =
  | 'idle'        // 空闲（无图谱或已删除）
  | 'queued'      // 已入队（等待处理）
  | 'running'     // 运行中（Ragflow 异步任务）
  | 'succeeded'   // 成功完成
  | 'failed'      // 失败
  | 'stale'       // 过期（文档更新后需重建）
  | 'deleting'    // 删除中
```

**存储位置**：`ragflow_datasets.graphStatus` 字段（默认 `'idle'`）

**任务状态（`RagflowGraphJob.status`）**：

```typescript
// ragflow-graph.service.ts line 17-24
type RagflowGraphJobType = 'build' | 'refresh' | 'delete' | 'status_refresh' | 'node_chat'
type RagflowGraphJobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | 'skipped'
```

**存储位置**：`ragflow_graph_jobs.status` 字段

**状态转换**：

| 转换 | 触发 | 位置 |
|------|------|------|
| `idle` → `queued` | `enqueueBuildGraphJob()` / `enqueueRefreshGraphJob()` | line 468 |
| `*` → `deleting` | `enqueueDeleteGraphJob()` | line 469 |
| `queued` → `running` | `lockGraphJob()`（原子 UPDATE） | line 525 |
| `running` → `succeeded` | `completeGraphJob()`（当 `progress === 1` 或匹配 `/Knowledge Graph done\|graph ready\|KB merge done/i`） | line 536-588, 2130 |
| `running` → `failed` | `failGraphJob()`（异常） | line 590-632 |
| `queued`/`running` → `cancelled` | `cancelGraphJob()`（用户取消 + 远程任务取消） | line 634-705 |
| `succeeded`/`failed`/`stale` → `stale` | `markDatasetGraphStale()`（文档上传/删除/更新） | ragflow.service.ts line 1964, 2010, 2043, 2057, 2060-2069 |
| `*` → `idle` | 成功 `delete` 任务 或 取消时无历史图谱 | line 771-780, 688-695 |

**原子更新**：

```typescript
// updateDatasetGraphStatus() line 2102-2119
async updateDatasetGraphStatus(datasetId: string, status: RagflowGraphDatasetStatus, jobId?: string) {
  await this.prisma.$transaction([
    this.prisma.ragflowDataset.update({
      where: { id: datasetId },
      data: { graphStatus: status }
    }),
    jobId && this.prisma.ragflowGraphJob.update({
      where: { id: jobId },
      data: { status: status === 'running' ? 'running' : 'succeeded' }
    })
  ].filter(Boolean))
}
```

**调度器驱动的转换**：

```typescript
// RagflowGraphSchedulerService.runDueSchedules() line 56
// 每 60s 检查一次，仅在整点执行
if (now.getMinutes() !== 0) return

// 1. 加载启用自动刷新的配置
const configs = await this.prisma.enterpriseRagflowConfig.findMany({
  where: {
    graphAutoRefreshEnabled: true,
    status: 'active',
    isDeleted: false
  }
})

// 2. 判断是否到期（daily/weekly/custom_hours）
const isDue = this.isConfigDue(config, now)

// 3. 获取 Redis 分布式锁（窗口锁，TTL 1h）
const lockKey = `ragflow:graph:auto-refresh:${windowKey}`
const acquired = await this.redis.set(lockKey, '1', 'EX', 3600, 'NX')

// 4. 查找候选数据集（graphStatus = 'stale' 或 超过刷新窗口）
const datasets = await this.findCandidateDatasets(config.id)

// 5. 批量入队（batchSize = 10, interval = 10min）
for (const dataset of datasets) {
  await this.graphService.enqueueScheduledRefreshGraphJob(dataset.id)
  await sleep(graphRefreshBatchIntervalMinutes * 60 * 1000)
}
```

### 3.3 鉴权自愈：Ragflow 权限拒绝的自动恢复

**错误检测**：

```typescript
// ragflow.client.ts line 25-28
export function isRagflowAuthorizationError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error)
  return /code 10[29]\b|no authorization|lacks permission|don'?t own/i.test(message)
}
```

匹配 Ragflow 错误码 **102** 和 **109**（跨租户/非所有者访问），这是**永久性条件**（数据集属于不同 Ragflow 账号），非瞬态错误。

**错误分类**：

```typescript
// ragflow-graph.service.ts line 2152-2165
function classifyGraphError(error: unknown): string {
  if (isRagflowAuthorizationError(error)) return 'dataset_unauthorized'
  if (error instanceof Error && /404|405/.test(error.message)) return 'unsupported'
  if (error instanceof Error && /timeout|ETIMEDOUT/.test(error.message)) return 'timeout'
  // ... 其他分类
}
```

`dataset_unauthorized` 优先级最高，在 `ragflow_unavailable` / `ragflow_quota_exceeded` 之前判断。

**用户可见消息**：

```typescript
// ragflow-graph.service.ts line 124-125
const GRAPH_DATASET_UNAUTHORIZED_MESSAGE =
  '当前 Ragflow 账号无权访问该知识库（dataset 归属账号与 API key 不一致）：请重新同步文件以自动重建知识库，或在管理后台更换正确的 API key'
```

**自愈流程**：

**场景 1：数据集访问失败**

```typescript
// ragflow.service.ts line 4033-4057
async verifyRemoteDatasetAlive(target, ragflowDatasetId): Promise<boolean> {
  try {
    const datasets = await this.ragflowClient.listDatasets(target, {
      id: ragflowDatasetId,
      page: 1,
      pageSize: 1
    })
    return datasets.length > 0
  } catch (error) {
    if (isRagflowAuthorizationError(error)) {
      // 权限拒绝 → 确定已失效 → 返回 false → 触发重建
      return false
    }
    // 其他错误（网络、超时）→ fail-open → 返回 true（不退役健康映射）
    return true
  }
}

// ensurePersonalDataset() line 302 / ensureEnterpriseDataset() line 344
if (!await this.verifyRemoteDatasetAlive(target, ragflowDatasetId)) {
  // 退役旧映射
  await this.retireStaleDatasetMapping(mapping.id)
  // 下一行自动以当前凭证创建新数据集
}
```

**场景 2：文档访问失败（上传过程中）**

```typescript
// processUploadJob() line 1855-1876
if (localDocument && !await this.verifyRemoteDocumentAlive(target, ragflowDatasetId, ragflowDocumentId)) {
  // 软删除本地文档
  await this.prisma.ragflowDocument.update({
    where: { id: localDocument.id },
    data: { isDeleted: true }
  })
  // 标记 blob 为 deleted → 下一步 ensureFileBlob 走"原地复活"路径
  await this.prisma.ragflowFileBlob.update({
    where: { id: localDocument.fileBlobId },
    data: { status: 'deleted' }
  })
}
```

**场景 3：图谱操作失败**

```typescript
// classifyGraphError() line 2161
// 权限错误 → dataset_unauthorized → 用户可见消息建议重新同步或更换 API key
// 无自动重试（视为永久性条件）
```

**场景 4：管理员保存配置后的协调**

```typescript
// reconcileEnterpriseDatasets() line 4087
// 当 baseUrl 或 apiKeyEncrypted 变更时
async reconcileEnterpriseDatasets(enterpriseId: string) {
  const mappings = await this.prisma.ragflowDataset.findMany({
    where: { enterpriseId, isDeleted: false }
  })
  
  let probed = 0, retired = 0
  for (const mapping of mappings) {
    probed++
    const alive = await this.verifyRemoteDatasetAlive(target, mapping.ragflowDatasetId)
    if (!alive) {
      await this.retireStaleDatasetMapping(mapping.id)
      retired++
    }
  }
  
  return { probed, retired }
}
```

---

## 4. 14 连接器抽象 & 金融级计费 & Monorepo 组织

### 4.1 14 连接器：约定优于接口

**文件**：`apps/api/src/app.module.ts` line 23-36, 62-75

**14 个连接器模块**：

| # | 连接器 | 目录 | 服务类 | 目标系统 |
|---|--------|------|--------|----------|
| 1 | 飞书 (Feishu/Lark) | `feishu-connector/` | `FeishuConnectorService` | IM、日历、文档、邮件、云盘 |
| 2 | 企业微信 (WeCom) | `wecom-connector/` | `WecomConnectorService` | 消息、日历、文档、邮件 |
| 3 | 钉钉 (DingTalk) | `dingtalk-connector/` | `DingtalkConnectorService` | IM、日历、文档 |
| 4 | 腾讯会议 (WeMeet) | `wemeet-connector/` | `WemeetConnectorService` | 腾讯会议 |
| 5 | 腾讯文档 | `tencent-docs-connector/` | `TencentDocsConnectorService` | 腾讯文档 |
| 6 | 金山文档 (KDocs) | `kdocs-connector/` | `KdocsConnectorService` | 金山文档 |
| 7 | IMA（阿里） | `ima-connector/` | `ImaConnectorService` | 阿里 IMA |
| 8 | 网易邮箱 | `netease-mail-connector/` | `NeteaseMailConnectorService` | IMAP/SMTP |
| 9 | GetNote | `getnote-connector/` | `GetnoteConnectorService` | GetNote 笔记 |
| 10 | 企查查 (QCC) | `qcc-connector/` | `QccConnectorService` | 企业数据查询 |
| 11 | QQ 邮箱 | `qq-mail-connector/` | `QqMailConnectorService` | IMAP/SMTP |
| 12 | 可画 (Canva) | `canva-connector/` | `CanvaConnectorService` | Canva 设计平台 |
| 13 | Gitee 企业版 | `gitee-ent-connector/` | `GiteeEntConnectorService` | 源代码管理 |
| 14 | 状态聚合 | `connector-status-aggregate/` | `ConnectorStatusAggregateService` | 聚合上述 13 个状态 |

**统一接口（约定模式，无抽象基类）**：

```typescript
// 每个连接器服务暴露相同签名
getStatus(userId: string, enterpriseId: string): Promise<ConnectorStatusEntry>

interface ConnectorStatusEntry {
  bound: boolean
  status: 'unbound' | 'pending' | 'connected' | 'error'
  syncedAt?: string
  error?: string
}
```

**状态聚合服务**：

```typescript
// connector-status-aggregate.service.ts
@Injectable()
export class ConnectorStatusAggregateService {
  async getAllStatuses(userId: string, enterpriseId: string): Promise<ConnectorStatusesView> {
    const results = await Promise.allSettled([
      this.feishu.getStatus(userId, enterpriseId),
      this.wecom.getStatus(userId, enterpriseId),
      this.dingtalk.getStatus(userId, enterpriseId),
      // ... 13 个连接器
    ])
    
    // 单个失败降级为 error，不阻塞其他
    return results.map((r, i) => 
      r.status === 'fulfilled' 
        ? r.value 
        : { bound: false, status: 'error', error: String(r.reason) }
    )
  }
}
```

**认证策略差异**：

| 连接器 | 认证方式 | 关键文件 |
|--------|----------|----------|
| 飞书 | Device Flow + OAuth 2.0，AES-256-GCM 加密 token | `feishu-oauth.client.ts`, `feishu-device-session.store.ts` |
| 企业微信 | 沙箱 agent 编排（wecom-cli QR 扫描，凭证仅存沙箱） | `wecom-connector-orchestrator.ts`, `wecom-cli.runner.ts` |
| 钉钉 | Device Flow via DWS CLI，沙箱编排 | `dingtalk-connector-orchestrator.ts`, `dws-cli.runner.ts` |
| Canva | OAuth 2.0 PKCE + DCR 注册，MCP initialize 探针 | `canva-oauth.client.ts`, `canva-mcp.client.ts` |
| QQ 邮箱 / 网易邮箱 | IMAP/SMTP 凭证 via script runner | `*-imap-light.ts`, `*-smtp-bundle.ts` |

### 4.2 金融级计费：两阶段提交 + 原子扣减

**模块结构**：`apps/api/src/billing/billing.module.ts`

**11 个服务**：

| 服务 | 职责 |
|------|------|
| `BillingService` | 核心：token 预授权（hold/capture/release） |
| `BillingOrderService` | 订单生命周期：创建 → 支付（微信支付）→ 发放 |
| `BillingPlanService` | 套餐 CRUD，7 种套餐类型 |
| `EntitlementService` | 批次生命周期：冻结/扣减/释放/发放/过期/分配 |
| `DefaultQuotaPolicyService` | 默认配额策略 |
| `ToolCallBillingService` | 工具调用计费（图片生成、网页搜索、语音输入） |
| `EntitlementExpiryScheduler` | 每日午夜：过期批次、激活计划批次 |
| `EntitlementAutoAllocateScheduler` | 每日：自动分配池座位给成员 |
| `BillingTaskCleanupScheduler` | 每 10 分钟：释放过期的冻结任务（1h 超时） |

**计量单位**：

| entitlementType | 单位 | 描述 |
|-----------------|------|------|
| `token` | `billing_token` | LLM token 用量（加权） |
| `storage` | bytes | 云存储消耗 |
| `monthly_plan` | — | 订阅锚点（不直接消耗） |

**Token 加权计费**：

```typescript
// enterprise-token-quota.constants.ts line 59-68
function estimateZclawWeightedTokens(usage: ZclawTokenUsagePayload): number {
  const realInput = Math.max(inputTokens - cacheRead, 0)
  const weighted = realInput + cacheWrite + cacheRead * 0.2 + outputTokens * 6
  return Math.max(0, Math.round(weighted))
}
```

输出 token 权重 **6x**，缓存读取 **0.2x**，实现成本均等化计费。

**防超卖机制**：

**1. 预授权（Hold/Freeze 模式）**

```typescript
// BillingService.reserveAiTask() line 48-128
async reserveAiTask(userId: string, enterpriseId: string, amount: number, idempotencyKey: string) {
  // 1. 创建 BillingTask（唯一约束防重复扣费）
  const task = await this.prisma.billingTask.create({
    data: {
      userId,
      enterpriseId,
      amount,
      idempotencyKey,  // 唯一约束
      status: 'created'
    }
  })
  
  // 2. 原子冻结额度
  await this.entitlementService.freezeEntitlements(userId, enterpriseId, amount, task.id)
  
  return task
}

// EntitlementService.freezeBatch() line 182-219
async freezeBatch(batchId: string, amount: number) {
  const result = await this.prisma.entitlementBatch.updateMany({
    where: {
      id: batchId,
      isDeleted: false,
      remainingAmount: { gte: amount }  // 乐观锁：余额必须 >= 扣减额
    },
    data: {
      remainingAmount: { decrement: amount },
      freezeAmount: { increment: amount }
    }
  })
  
  if (result.count !== 1) {
    // 并发修改导致 count=0 → 事务失败
    throw new ForbiddenException({
      code: ErrorCode.INSUFFICIENT_CREDITS,
      message: '余额不足'
    })
  }
}
```

**数据库级原子 CAS**：如果 `remainingAmount` 被其他请求并发修改，`updateMany` 返回 `count: 0`，事务失败。

**2. PostgreSQL 行级锁（遗留 Credit 系统）**

```typescript
// BillingService.charge() line 326-414
await this.prisma.$transaction(async (tx) => {
  // 悲观行锁
  await tx.$queryRaw`SELECT 1 FROM wallets WHERE "userId" = ${userId} FOR UPDATE`
  
  const wallet = await tx.wallet.findUnique({ where: { userId } })
  if (wallet.balance < amount) throw new ForbiddenException('余额不足')
  
  await tx.wallet.update({
    where: { userId },
    data: { balance: { decrement: amount } }
  })
  
  await tx.creditLedger.create({
    data: {
      userId,
      amount: -amount,
      idempotencyKey: `${taskId}:charge`  // 幂等键
    }
  })
})
```

**3. 幂等键**

每个操作携带唯一 `idempotencyKey`：

- `BillingTask.idempotencyKey`（唯一约束）
- `CreditLedger.idempotencyKey`（唯一约束）
- `CreditHold.idempotencyKey`（唯一约束）
- `EntitlementLedger.idempotencyKey`（唯一约束）

冻结/扣减/释放组合键如 `${taskId}:freeze`, `${taskId}:capture`。

**4. 过期冻结任务清理**

```typescript
// BillingTaskCleanupScheduler
// 每 10 分钟运行，释放超过 1 小时的冻结任务
const staleTasks = await this.prisma.billingTask.findMany({
  where: {
    status: 'frozen',
    frozenAt: { lt: new Date(Date.now() - FREEZE_TIMEOUT_MS) }
  }
})

for (const task of staleTasks) {
  await this.entitlementService.releaseFrozenAmount(task.id)
  await this.prisma.billingTask.update({
    where: { id: task.id },
    data: { status: 'expired' }
  })
}
```

**5. 订单发放状态机**

```typescript
// BillingOrderService.fulfillPaidOrder()
async fulfillPaidOrder(orderId: string) {
  // 1. 认领订单（CAS）
  const claimed = await this.prisma.billingOrder.updateMany({
    where: {
      id: orderId,
      grantStatus: { in: ['PENDING', 'FAILED'] }
    },
    data: { grantStatus: 'PROCESSING' }
  })
  
  if (claimed.count !== 1) {
    // 状态竞争 → 抛出冲突异常
    throw new ConflictException('订单已在处理中')
  }
  
  try {
    // 2. 发放权益
    await this.entitlementService.grantEntitlements(orderId)
    
    // 3. 标记成功
    await this.prisma.billingOrder.update({
      where: { id: orderId },
      data: { grantStatus: 'SUCCESS' }
    })
  } catch (error) {
    // 4. 标记失败（可重试）
    await this.prisma.billingOrder.update({
      where: { id: orderId },
      data: { grantStatus: 'FAILED', lastError: String(error) }
    })
    throw error
  }
}
```

### 4.3 Monorepo 组织：pnpm workspaces + Turborepo

**根配置**：

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "test": {},
    "lint": {}
  }
}
```

**包清单**：

| 类型 | 包名 | 栈 | 职责 |
|------|------|-----|------|
| App | `@insightweaver/api` | NestJS 11 + Express | 后端 API（30+ 模块） |
| App | `@insightweaver/web` | Next.js 16 + React 19 + Tailwind 4 | 前端 Web |
| Package | `@insightweaver/db` | Prisma ORM | PostgreSQL schema + migrations + client |
| Package | `@insightweaver/shared` | TypeScript | 共享类型、常量、工具函数 |
| Package | `@insightweaver/relation-contract` | TypeScript | relation-compute 服务协议契约 |

**依赖图**：

```
@insightweaver/web ──────→ @insightweaver/shared

@insightweaver/api ──┬──→ @insightweaver/db
                     ├──→ @insightweaver/shared
                     └──→ @insightweaver/relation-contract

@insightweaver/db ────→ @prisma/client (generated)
```

`@insightweaver/shared` 是叶子依赖，无 workspace 依赖。  
`@insightweaver/db` 仅被 `@insightweaver/api` 消费。  
`@insightweaver/relation-contract` 定义 API 与外部 relation-compute 服务的协议。

**数据库包内容**：

```
packages/db/
├── prisma/
│   ├── schema.prisma          # 60+ 模型
│   ├── migrations/            # 迁移历史
│   ├── seed/                  # 种子数据
│   └── scripts/               # 迁移工具
├── src/
│   ├── index.ts               # 重导出
│   └── migration.test.ts      # 迁移测试
└── package.json
```

**API 模块组织**：

```typescript
// apps/api/src/app.module.ts
@Module({
  imports: [
    // 基础设施
    DatabaseModule,
    RedisModule,
    AuthModule,
    CommonModule,
    HealthModule,
    
    // 业务域
    BillingModule,              // 11 providers, 11 controllers
    EnterpriseModule,
    ZclawModule,                // 最大模块：AI agent 工作区
    RelationSpaceModule,        // 知识图谱 / 关系计算
    ResearchModule,
    SkillModule,
    AgentModule,
    
    // 13 个连接器 + 1 个状态聚合
    FeishuConnectorModule,
    WecomConnectorModule,
    DingtalkConnectorModule,
    // ... 10 more
    ConnectorStatusAggregateModule,
    
    // 支持模块
    DashboardModule,
    AdminUsersModule,
    AdminConfigModule,
    CreditsModule,
    WechatPayModule,
    SpeechModule,
    AttachmentModule,
    McpModule,
    HumanEfficiencyModule
  ]
})
export class AppModule {}
```

---

## 附录：关键数据库表

### relation-compute 相关

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `RelationComputeConfig` | `relation_compute_configs` | `id="default"`, `baseUrl`, `apiKeyEncrypted` (AES-256-GCM), `status`, `requestTimeoutMs` |
| `RelationComputeTenantState` | `relation_compute_tenant_states` | `enterpriseId` (unique), `tenantKey`, `sourceCursor`, `lastSourceSyncAt`, `graphUpdatedAt`, `lastJobId`, `lastJobStatus` |
| `RelationComputeCallLog` | `relation_compute_call_logs` | `kind`, `capability`, `status`, `durationMs`, `errorMessage` |

### GraphRAG 相关

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `EnterpriseRagflowConfig` | `enterprise_ragflow_configs` | `enterpriseId` (unique), `baseUrl`, `apiKeyEncrypted`, `quotaBytes` (BigInt), `embeddingModel`, `graphAutoRefreshEnabled`, `graphRefreshScheduleType` |
| `RagflowDataset` | `ragflow_datasets` | `ragflowDatasetId`, `graphStatus` (idle/queued/running/succeeded/failed/stale/deleting), `graphProgress`, `graphProgressMsg`, `lastGraphRunAt` |
| `RagflowFileBlob` | `ragflow_file_blobs` | `contentHash` (SHA-256), `refCount`, `status`, **`@@unique([datasetMappingId, contentHash])`** |
| `RagflowDocument` | `ragflow_documents` | `ragflowDocumentId`, `contentHash`, `uploadStatus`, `parseStatus`, `metadataSyncStatus` |
| `RagflowSyncJob` | `ragflow_sync_jobs` | `jobType` (upload/delete/metadata_update/retrieval_audit), `status`, `retryCount`, `nextRetryAt` |
| `RagflowGraphJob` | `ragflow_graph_jobs` | `jobType` (build/refresh/delete/status_refresh/node_chat), `status`, `progress`, `progressMsg`, `remoteTaskId` |

### 计费相关

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `BillingPlan` | `billing_plans` | `planType` (7 种), `price`, `tokenQuota`, `storageQuota` |
| `BillingOrder` | `billing_orders` | `orderNo`, `planId`, `amount`, `grantStatus` (PENDING/PAYING/SUCCESS/FAILED) |
| `BillingTask` | `billing_tasks` | `idempotencyKey` (unique), `amount`, `status` (created/frozen/captured/expired) |
| `EntitlementBatch` | `entitlement_batches` | `remainingAmount`, `freezeAmount`, `expiresAt` |
| `EntitlementLedger` | `entitlement_ledgers` | `idempotencyKey` (unique), `amount`, `type` (debit/credit) |
| `Wallet` | `wallets` | `balance` (BigInt), `version` (乐观锁) |
| `CreditLedger` | `credit_ledger` | `idempotencyKey` (unique), `amount` |

---

## 总结

1. **relation-compute 解耦**：主平台变为薄代理层（配置+鉴权+源数据同步），所有智能计算（LLM 调用、图谱存储、推理）迁至独立服务；双协议版本 v1(1.0.0)/v2(2.0.0)；DashScope API Key 隔离；11 张 relation 图表迁至独立数据库。

2. **SVG 力导向图**：**自研同心环/分层布局算法**（非 d3-force），纯 SVG 渲染，布局 100% 在浏览器端计算；数据来自远程 compute 服务（`POST /v2/tenants/:key/graph/query`），数据库不存储图谱。

3. **GraphRAG**：SHA-256 对**完整文件二进制**做哈希，`(datasetMappingId, contentHash)` 复合唯一索引去重；7 态图谱状态机 + 6 态任务状态机；鉴权自愈匹配 Ragflow error code 102/109 → 退役旧映射 → 自动以当前凭证重建。

4. **14 连接器**：13 个外部数据源集成 + 1 个状态聚合；**约定优于接口**（无抽象基类）；金融级计费使用**两阶段提交**（冻结→扣减/释放）+ 数据库级原子 CAS + 幂等键；Monorepo 使用 pnpm workspaces + Turborepo，2 apps + 3 shared packages。
