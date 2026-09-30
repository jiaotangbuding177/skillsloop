# EvoMind RagFlow 知识图谱接入设计与实施计划

## 0. 与现有 RagFlow 文档的关系

本文档基于 [`docs/ragflow-v2.md`](./ragflow-v2.md) 和 [`docs/ragflow-enterprise-config-plan.md`](./ragflow-enterprise-config-plan.md) 继续展开知识图谱接入方案，不替代两份既有设计。

`ragflow-v2.md` 已经定义并基本落地 RagFlow 基础链路，包括 dataset/document/blob/job 映射、异步同步、文档解析状态、失败重试、文件生命周期同步、拖拽知识库文件定向召回，以及 Phase 6 中知识图谱的后续方向。

`ragflow-enterprise-config-plan.md` 补充了企业级 RagFlow 配置和容量管控规则，明确：

- 默认空间固定使用特殊企业 ID `-1` 读取 RagFlow 配置。
- 真实企业空间使用真实企业 ID 读取 RagFlow 配置。
- RagFlow URL 和 API Key 只能来自数据库企业配置，不再通过环境变量兜底。
- RagFlow 不可用时，文件上传和普通聊天主链路必须降级成功。
- 容量不足只限制新增或变大的 RagFlow 写入，不应影响已经同步数据的读取召回。

本文档聚焦后续需要开始实现的知识图谱能力：

- 接入 RagFlow GraphRAG / 知识图谱构建。
- 支持个人图谱和企业图谱。
- 支持根据图谱节点进行对话。
- 支持手动刷新和定时刷新图谱。
- 图谱更新中在前端提供友好提醒。
- 保持权限边界、配置降级和容量管控一致。

## 0.1 当前实现快照（Phase 2 后端）

截至当前代码状态，已落地的范围是 Phase 1 和 Phase 2 的后端主链路：

- `packages/db/prisma/schema.prisma` 已包含 `RagflowGraphJob`，并复用 `RagflowDataset.graphStatus`、`graphProgress`、`graphProgressMsg`、`lastGraphRunAt` 维护本地图谱状态。
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts` 负责图谱状态、运行记录、构建/刷新/删除任务、进度轮询、失败审计和权限/capability 判断。
- `apps/api/src/zclaw/zclaw-ragflow.controller.ts` 已暴露：
  - `GET /api/zclaw/ragflow/graph/status`
  - `POST /api/zclaw/ragflow/graph/build`
  - `POST /api/zclaw/ragflow/graph/refresh`
  - `DELETE /api/zclaw/ragflow/graph`
  - `GET /api/zclaw/ragflow/graph/runs`
- 请求兼容 `scope=personal|enterprise`，也兼容现有前端口径 `source=workspace|shared-workspace`。企业图谱的 `enterpriseId` 可从 query/body 显式传入，也可从请求上下文读取。
- `delete` 逻辑已在 service、controller 和 `RagflowClient.deleteKnowledgeGraph` 中落地；EvoMind public 路由为 `DELETE /api/zclaw/ragflow/graph`，远端 RagFlow 路径为 `DELETE /api/v1/datasets/:datasetId/graph`。

当前行为边界：

- 个人图谱按当前用户的 personal dataset 处理。
- 企业图谱状态允许企业成员读取；企业写操作只允许企业 `admin/owner` 或平台 `admin`。
- `GET /graph/status` 会根据权限返回 `canBuild`、`canRefresh`、`canDelete`。企业普通成员可读状态，但三个写入能力均为 `false`。
- `POST /graph/build` 和 `POST /graph/refresh` 对无权限用户返回 403。
- 写入型图谱能力受 RagFlow 配置和容量控制；读取状态和已有运行记录不因容量不足而关闭。
- RagFlow 未配置/停用、容量不足、dataset 缺失时，不触发远端 GraphRAG 调用，不把 dataset 改成 `running`，而是写入 `RagflowGraphJob(status="skipped")`，记录 `errorCode`、`errorMessage`、`triggerUserId` 和跳过原因。
- 已有 `queued/running/deleting` 图谱任务时，不重复提交同一 dataset 的新任务，而是返回当前状态和最近任务。
- 远端 GraphRAG 构建通过 `run_graphrag` 启动，通过 `trace_graphrag` 长轮询进度，并在每次拿到进度时同步更新 `RagflowGraphJob.progress/progressMsg` 和 `RagflowDataset.graphProgress/graphProgressMsg`。
- `GET /graph/status` 在 active job 存在时优先读取 job 进度，避免 dataset 与 job 短暂不同步导致前端进度回退。
- 构建完成后通过 `knowledge_graph` 读取节点/边摘要写入 job payload，并由 `completeGraphJob` 写入 `succeeded` 和 `lastGraphRunAt`。
- RagFlow GraphRAG 的 `404`、`405`、`not support`、`unsupported`、`method not allowed` 等错误统一归类为 `errorCode="unsupported"`，并返回友好 message。
- `canChatWithNode` 当前只表示“是否已有可用于节点问答的成功图谱版本”，不表示节点问答接口已经完成。它在 `succeeded/stale`、存在 `lastGraphRunAt`、或 active job 期间存在上一版成功图谱时为 `true`；`idle/failed` 且从未成功构建时为 `false`。
- `/graph/runs` 返回当前 dataset 的 `RagflowGraphJob` 运行记录，包含 `queued/running/succeeded/failed/skipped` 等状态，可用于调试和后续前端运行历史。

当前尚未落地：

- Phase 3 前端图谱状态条、按钮、30 秒轮询和提示已接入知识库侧栏。
- Phase 4 定时刷新调度。
- Phase 5 图谱节点列表 API 和节点缓存。
- Phase 6 根据节点对话 API。
- Phase 7 独立 worker、任务恢复和更完整的运维能力。

## 1. 当前基础与约束

### 1.1 当前已具备的能力

后端已经具备：

- `RagflowClient` 基础 API 封装。
- `RagflowDataset`、`RagflowDocument`、`RagflowFileBlob`、`RagflowSyncJob` 本地映射。
- 文档上传到 RagFlow、触发 parse、刷新 parse 状态。
- 按当前空间解析 RagFlow capability。
- 拖拽知识库文件时基于本地 mapping 和权限校验做受限 retrieve。
- RagFlow 配置不可用或容量不足时的降级判断。

前端已经具备：

- 文档 RagFlow 同步/解析状态展示。
- pending/running 状态下的低频轮询。
- 上传后短轮询。
- 失败重试入口。
- “同步到知识图谱”相关入口的基础能力判断。

数据库已经预留：

```text
RagflowDataset.graphStatus
RagflowDataset.graphProgress
RagflowDataset.graphProgressMsg
RagflowDataset.lastGraphRunAt
```

### 1.2 必须遵守的约束

知识图谱接入必须遵守以下约束：

- 前端不得直接访问 RagFlow。
- 图谱构建、图谱状态刷新、节点问答都必须经过 EvoMind API。
- RagFlow 不负责 EvoMind 权限，所有权限判断必须由 EvoMind 后端兜底。
- 企业图谱可能暴露文件中的实体和关系，MVP 阶段允许企业成员查看企业图谱，但必须收紧企业图谱构建、刷新、删除权限。
- 普通聊天仍不默认触发 RagFlow。
- 根据图谱节点对话时，不得扩大到整个 dataset 的无条件召回。
- prompt 中不得暴露 `RagFlow`、`GraphRAG`、`score`、内部检索过程等实现细节。
- 图谱构建和刷新属于 RagFlow 写入型能力，受配置和容量限制。
- 已有图谱或已同步文档的读取能力不应因为容量不足被关闭。

## 2. 产品目标

### 2.1 MVP 目标

MVP 优先完成：

- 用户可以手动构建个人知识图谱。
- 企业管理员可以手动构建企业知识图谱。
- 可以查看个人/企业图谱构建状态和进度。
- 图谱更新中，前端展示友好提醒。
- 支持图谱定时刷新。
- 支持基于选中的图谱节点发起对话。
- RagFlow 无配置、停用、连接异常或容量不足时，图谱入口清晰降级。

### 2.2 暂缓目标

以下能力暂缓，不纳入第一版 MVP：

- 所有聊天问题默认启用 GraphRAG。
- GraphRAG 与 Vector 自动混合召回策略。
- 企业图谱节点/边按 document 权限做完整过滤。
- 多企业图谱混合问答。
- 大规模图谱运维后台和批量修复页面。
- 节点级引用来源持久化完整展示。

## 3. 核心设计原则

### 3.1 图谱粒度跟随 Dataset

图谱构建以 RagFlow dataset 为单位。

个人图谱：

```text
scope = personal
userId = 当前用户 id
enterpriseId = 当前空间企业 ID
dataset = 当前用户在当前空间的 personal dataset
```

企业图谱：

```text
scope = enterprise
enterpriseId = 当前企业 ID
dataset = 当前企业 enterprise dataset
```

默认空间必须使用企业配置计划中的 `enterpriseId="-1"` 口径。后续如果既有默认空间数据仍存在 `enterpriseId=null`，应按企业配置计划迁移或兼容读取，但新图谱能力应优先按 `-1` 设计。

### 3.2 图谱状态由 EvoMind 本地维护

RagFlow 远端状态可能存在接口差异，因此 EvoMind 必须维护本地图谱状态。

推荐状态：

```text
idle       尚未构建
queued     已提交构建，等待执行
running    正在构建或刷新
succeeded  最近一次构建成功
failed     最近一次构建失败
stale      文档发生变化，图谱可能不是最新
deleting   正在删除远端图谱
disabled   当前空间 RagFlow 不可写
```

状态写入位置：

- MVP 先复用 `RagflowDataset.graphStatus`、`graphProgress`、`graphProgressMsg`、`lastGraphRunAt`。
- 新增独立图谱 job 表，记录每一次构建、刷新、删除、节点对话和失败原因。

### 3.3 图谱更新是最终一致

文档上传、编辑、删除和 RagFlow 图谱构建之间是最终一致。

推荐策略：

- 文档解析成功后，将对应 dataset 标记为 `stale`。
- 文档删除、移出知识库或内容更新后，将对应 dataset 标记为 `stale`。
- 不因图谱 stale 阻塞文件上传、文档解析或普通聊天。
- 手动刷新可以立即提交图谱构建。
- 定时刷新只处理 `stale` 或明确配置为周期重建的 dataset。

### 3.4 图谱构建中允许读取上一版

如果 dataset 已经有过成功图谱，当前又处于 `queued/running`：

- 可以允许基于上一版图谱进行节点问答。
- 前端必须提示：“知识图谱正在更新，当前回答可能基于上一版内容。”
- 后端响应中应返回 `graphWarning`，让前端可以在对话区显示轻量提示。

如果从未成功构建过图谱且当前正在构建：

- 节点问答入口应置灰。
- 可以提示：“知识图谱正在生成，完成后即可基于节点提问。”

## 4. 数据模型设计

### 4.1 复用现有字段

现有 `RagflowDataset` 字段作为 dataset 级图谱状态：

```text
graphStatus
graphProgress
graphProgressMsg
lastGraphRunAt
errorMessage
```

MVP 可直接使用这些字段完成状态展示。

### 4.2 新增图谱 Job 记录

建议新增独立的 `RagflowGraphJob`，不直接复用现有 `RagflowSyncJob`。

原因：

- `RagflowSyncJob` 当前语义是文档同步、解析状态、metadata update、删除等文档生命周期任务。
- 知识图谱任务是 dataset 级能力，操作对象不一定是单个 document。
- 节点对话不是传统异步任务，但需要记录 nodeIds、question、documentIds、图谱上下文和召回审计，放进文档同步 job 会让表语义混乱。
- 独立表可以统一承载图谱构建、刷新、删除、节点对话、定时刷新和失败重试，后续运维查询更清晰。

`RagflowGraphJob` 既是任务表，也是图谱能力的审计表。对于 `build/refresh/delete` 这类异步动作，它按 job 执行；对于 `node_chat` 这类同步动作，它记录一次图谱节点对话审计。

建议字段：

```text
id
datasetMappingId
enterpriseId
scope
jobType
triggerType
status
progress
progressMsg
nodeIds
documentIds
question
sessionId
messageId
startedAt
finishedAt
lockedAt
lockedBy
errorMessage
payload
createdByUserId
createdAt
updatedAt
```

字段说明：

- `jobType`: `build`、`refresh`、`delete`、`status_refresh`、`node_chat`。
- `triggerType`: `manual`、`scheduled`、`document_changed`、`retry`。
- `status`: `queued`、`running`、`succeeded`、`failed`、`cancelled`、`skipped`。
- `nodeIds`: 节点对话使用的图谱节点 ID 列表；非节点对话为空。
- `documentIds`: 节点关联并通过权限校验后的 RagFlow documentIds 或本地 document mapping IDs。
- `question`: 节点对话的用户原始问题；构建/刷新/删除为空。
- `sessionId/messageId`: 节点对话跳转到会话页后对应的会话和消息标识。
- `payload`: 记录 RagFlow 原始 trace 摘要、远端任务 ID、错误码、节点统计、节点可见字段、图谱上下文、召回请求摘要等。

索引建议：

```text
@@index([datasetMappingId, status, createdAt])
@@index([enterpriseId, status, createdAt])
@@index([jobType, status, createdAt])
@@index([status, lockedAt, createdAt])
```

### 4.3 可选节点缓存表

如果 RagFlow trace 接口能稳定返回节点和边，可以先不缓存节点。

如果 RagFlow 节点接口不稳定，建议新增本地缓存：

```text
RagflowGraphNode
RagflowGraphEdge
```

`RagflowGraphNode` 建议字段：

```text
id
datasetMappingId
remoteNodeId
label
type
description
documentIds
chunkIds
metadata
createdAt
updatedAt
```

`RagflowGraphEdge` 建议字段：

```text
id
datasetMappingId
remoteEdgeId
sourceNodeId
targetNodeId
label
weight
metadata
createdAt
updatedAt
```

MVP 不强依赖节点缓存，只有在 RagFlow 无法按需返回节点时再落库。

## 5. 后端 API 设计

### 5.1 图谱状态

```text
GET /api/zclaw/ragflow/graph/status
```

Query：

```ts
{
  scope?: "personal" | "enterprise";
  // 兼容当前前端入口；workspace 等价 personal，shared-workspace 等价 enterprise。
  source?: "workspace" | "shared-workspace";
  enterpriseId?: string;
}
```

Response：

```ts
{
  datasetMappingId: string | null;
  scope: "personal" | "enterprise";
  enterpriseId: string;
  graphStatus: string;
  graphProgress: number | null;
  graphProgressMsg: string | null;
  lastGraphRunAt: string | null;
  errorMessage: string | null;
  latestJob: {
    id: string;
    jobType: string;
    status: string;
    progress: number | null;
    progressMsg: string | null;
    errorCode: string | null;
    errorMessage: string | null;
    createdAt: string;
    updatedAt: string;
  } | null;
  canBuild: boolean;
  canRefresh: boolean;
  canDelete: boolean;
  canChatWithNode: boolean;
  reason: "available" | "ragflow_unavailable" | "ragflow_quota_exceeded" | "permission_denied" | "dataset_missing";
  message: string | null;
  capability: {
    available: boolean;
    reason: string | null;
    message: string | null;
  };
}
```

当前实现补充：

- status 不触发远端 RagFlow 调用，只读取本地 dataset、capability 和最近 job。
- 当存在 `queued/running/deleting` job 时，`graphProgress` 和 `graphProgressMsg` 优先来自 active/latest job。
- 企业普通成员可读取企业图谱 status，但 `canBuild/canRefresh/canDelete=false`。
- `canChatWithNode` 只有在已有成功图谱版本时才为 `true`，不因为 capability 可用或有 dataset 就直接开启。

### 5.2 手动构建或刷新

```text
POST /api/zclaw/ragflow/graph/build
POST /api/zclaw/ragflow/graph/refresh
```

Body：

```ts
{
  scope: "personal" | "enterprise";
  // 兼容当前前端入口；workspace 等价 personal，shared-workspace 等价 enterprise。
  source?: "workspace" | "shared-workspace";
  enterpriseId?: string;
  force?: boolean;
}
```

行为：

- `build` 用于首次构建。
- `refresh` 用于已有图谱或 stale 图谱重建。
- MVP 中两者可以复用同一个 service 方法，但前端文案不同。
- 当前实现要求已有本地 `RagflowDataset` 映射，不会从图谱入口自动创建空 dataset。
- RagFlow 未配置/停用、容量不足、dataset 缺失时会写入 `RagflowGraphJob(status="skipped")`，不会触发远端调用，也不会把 dataset 状态置为 `running`。
- 远端调用失败会写入 `RagflowGraphJob(status="failed")`，其中 GraphRAG 不支持类错误统一写入 `errorCode="unsupported"`。
- 构建/刷新启动后由后端异步处理，长轮询 `trace_graphrag` 并同步 job 与 dataset 进度。

### 5.3 删除图谱

```text
DELETE /api/zclaw/ragflow/graph
```

Body：

```ts
{
  scope: "personal" | "enterprise";
  enterpriseId?: string;
}
```

权限：

- 个人图谱：本人可删除。
- 企业图谱：企业管理员或平台超级管理员可删除。
- 普通成员不可删除。

当前实现补充：

- service 已实现 `enqueueDeleteGraphJob` 和远端 `deleteKnowledgeGraph` 调用。
- controller 已公开 `DELETE /api/zclaw/ragflow/graph`，前端删除按钮使用该路由，不直接访问 RagFlow。

### 5.4 图谱运行记录

```text
GET /api/zclaw/ragflow/graph/runs
```

用于展示最近构建、刷新、删除、节点对话、失败原因和触发来源。

返回记录来自 `RagflowGraphJob`。MVP 可以只在后台和调试面板使用，后续可用于企业管理员查看图谱刷新历史。

当前实现会返回当前 dataset 下最近的图谱 job，包含 skipped 降级记录、unsupported/failed 记录和 succeeded/running 记录。

### 5.5 图谱节点列表

```text
GET /api/zclaw/ragflow/graph/nodes
```

Query：

```ts
{
  scope: "personal" | "enterprise";
  enterpriseId?: string;
  keyword?: string;
  limit?: number;
}
```

Response：

```ts
{
  datasetMappingId: string | null;
  graphStatus: string;
  lastGraphRunAt: string | null;
  canChatWithNode: boolean;
  nodes: Array<{
    id: string;
    label: string;
    type: string | null;
    description: string | null;
    documentIds: string[];
    documentCount: number;
    updatedAt: string | null;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string | null;
    weight: number | null;
  }>;
  summary: {
    nodeCount: number;
    edgeCount: number;
    returnedNodeCount: number;
    returnedEdgeCount: number;
  };
  warning: string | null;
}
```

当前 Phase 5 实现直接读取 RagFlow `GET /api/v1/datasets/:datasetId/knowledge_graph`，按需返回节点和边，不新增本地 `RagflowGraphNode/RagflowGraphEdge` 缓存表。

后端只返回安全白名单字段，不透传 RagFlow 原始 payload、chunk 原文、内部路径或未过滤 metadata。`keyword` 和 `limit` 在后端生效，默认 `limit=80`，最大 `200`；边只返回两端都在当前节点结果集中的关系。

企业共享知识库普通成员可读取节点图谱，但不能构建、刷新或删除图谱。读取已有图谱只校验 RagFlow 配置，不因企业空间配额不足阻止查看上一版图谱。

RagFlow 返回 404/405/unsupported/not support 时归类为 `unsupported`，接口返回友好 `warning`，并记录 `RagflowGraphJob(jobType="status_refresh", status="failed", errorCode="unsupported")` 用于审计。

### 5.6 根据节点对话

Phase 6 不新增独立 `POST /graph/chat`。节点对话复用现有 EvoMind/ZClaw 对话接口：

```text
POST /api/zclaw/chat/message
POST /api/zclaw/chat/message/stream
```

Body 在现有 `sessionId/message/files` 基础上增加可选 `graphNodeContext`：

```ts
{
  sessionId: string;
  message: string;
  files?: ZclawInputFileDto[];
  graphNodeContext?: {
    source?: "workspace" | "shared-workspace";
    scope?: "personal" | "enterprise";
    enterpriseId?: string | null;
    datasetMappingId?: string | null;
    nodeIds: string[];
  };
}
```

行为：

- 前端图谱节点右键“基于该节点对话”会跳转到 EvoMind 对话页，并在聊天框展示选中节点 chip。
- `graphNodeContext` 只对下一次发送生效；发送开始后前端清空 pending context。
- 后端本地 `ZclawMessage(role=user)` 只保存用户原始 `message`。
- 后端发给 KM Agent 的 upstream message 才拼接节点安全摘要、相邻关系、受限 RagFlow retrieve 片段和用户原始问题。
- 历史会话展示和远端历史恢复会通过 graph node prompt marker 过滤拼接内容，只展示用户原始问题。
- 本次节点对话写入 `RagflowGraphJob(jobType=node_chat)`，但不改变 dataset 图谱状态。

## 6. 后端服务设计

### 6.1 Service 职责拆分

建议在 `apps/api/src/zclaw/ragflow` 下继续扩展：

```text
ragflow.client.ts
ragflow.service.ts
ragflow-graph.service.ts
ragflow-graph.types.ts
```

MVP 也可以先在 `RagflowService` 内实现，等复杂度上来后再拆。

职责建议：

- `RagflowClient`: 只负责调用 RagFlow API。
- `RagflowService`: 负责现有文档同步、状态、召回能力。
- `RagflowGraphService`: 负责图谱构建、trace、状态映射、节点解析、节点问答准备。
- `ZclawService`: 负责接入主聊天链路和权限上下文。

### 6.2 图谱构建流程

手动构建流程：

1. 解析当前用户和当前空间。
2. 根据 `scope` 定位 dataset。
3. 校验权限。
4. 调用 `resolveRagflowSpaceCapability`。
5. 如果 RagFlow 不可用，返回降级提示。
6. 如果容量不足，拒绝构建并返回容量提示。
7. 检查 dataset 是否存在已解析文档。
8. 检查是否已有 `queued/running` 图谱任务。
9. 创建本地图谱 run。
10. 更新 dataset `graphStatus=queued`。
11. 后台执行 run。
12. 调用 `RagflowClient.runGraphRag`。
13. 进入 `running`。
14. 调用 `traceGraphRag` 刷新进度。
15. 成功后写入 `succeeded` 和 `lastGraphRunAt`。
16. 失败后写入 `failed` 和 `errorMessage`。

### 6.3 图谱状态刷新流程

状态刷新用于前端轮询和定时任务观察。

流程：

1. 查询本地 dataset。
2. 如果 `graphStatus` 不在 `queued/running/deleting`，直接返回本地状态。
3. 如果 capability 不允许远端读取，返回本地状态和降级提示。
4. 调用 `traceGraphRag`。
5. 映射远端状态到本地状态。
6. 更新 `graphProgress/graphProgressMsg`。
7. 返回最新状态。

### 6.4 文档变更触发 stale

以下事件应标记图谱 stale：

- 文档首次 parse 成功。
- 文档内容更新并重新同步成功。
- 文档从知识库移出。
- 文档删除。
- 企业共享文件权限模型发生变化。

标记规则：

- `idle` 保持 `idle`。
- `succeeded` 改为 `stale`。
- `failed` 可保持 `failed`，但记录 `stale=true` 可选。
- `queued/running` 不打断当前任务。

MVP 可只在文档同步成功、删除成功后标记 `stale`。

## 7. 定时刷新设计

Phase 4 当前实现说明：不做每 5 分钟全量 dataset 扫描。后端调度器每分钟只检查当前是否进入某个企业配置的整点小时窗口；只有进入窗口后才查询该企业候选 dataset，并按批次提交 refresh graph job。

当前配置字段：

```text
graphAutoRefreshEnabled Boolean
graphRefreshScheduleType String  // daily | weekly | custom_hours
graphRefreshIntervalHours Int?
graphRefreshDayOfWeek Int?       // 1..7
graphRefreshHour Int             // 0..23，只支持整点小时
graphRefreshBatchSize Int
graphRefreshBatchIntervalMinutes Int
```

默认行为：

- 自动刷新默认关闭。
- 开启后默认每日 01:00 执行。
- 高级配置默认收起，可选择每日、每周、自定义小时数；不允许分钟级刷新频率。
- 每批默认提交 10 个 dataset，批次间隔固定 10 分钟。
- 多实例使用 Redis 窗口锁 `ragflow:graph:auto-refresh:{enterpriseId}:{yyyy-mm-dd}:{hh}`；Redis 不可用时降级为进程内窗口锁。
- scheduled job payload 写入 `triggerType="scheduled"`、`triggeredBy="ragflow_graph_scheduler"`、`scheduleType`、`scheduleHour`、`scheduledWindowKey`、`batchIndex`、`batchIntervalMinutes`。

### 7.1 配置项

推荐在企业 RagFlow 配置中增加，并在超级管理员 RagFlow 配置管理页面开放配置：

```text
graphAutoRefreshEnabled
graphRefreshIntervalHours
graphRefreshCron
graphRefreshWindowStart
graphRefreshWindowEnd
```

MVP 可简化为：

```text
graphAutoRefreshEnabled Boolean
graphRefreshIntervalHours Int
```

默认：

- 自动刷新关闭。
- 开启后默认每天一次。

超级管理员后台配置要求：

- 在企业 RagFlow 配置列表的操作列提供独立“知识图谱自动更新”按钮。
- 点击后打开独立自动更新表单；不放在 RagFlow URL/API Key/parser 编辑弹窗中。
- 独立表单默认只展示开关和摘要，高级配置默认收起，打开后展示更新频率配置。
- MVP 支持固定频率：每天、每周、自定义小时数。
- 后续可扩展 cron 表达式。
- 配置按企业生效：默认空间使用 `enterpriseId="-1"`，真实企业使用真实企业 ID。
- 普通企业管理员不在该页面维护全局频率；企业管理员只触发手动刷新。

### 7.2 调度策略

后端定时扫描：

```text
整点小时窗口触发；不到窗口不扫描 dataset
```

候选 dataset：

- RagFlow 配置 active。
- capability 允许写入。
- `graphAutoRefreshEnabled=true`。
- `graphStatus=stale` 或距离 `lastGraphRunAt` 超过配置间隔。
- 当前没有 `queued/running/deleting`。
- 至少有一个已解析文档。

执行策略：

- 每轮限制最大提交数量，避免同时触发大量 GraphRAG。
- 同一个 dataset 使用数据库锁或运行记录唯一约束避免重复提交。
- 失败后记录失败，不在同一轮无限重试。

### 7.3 手动刷新优先级

手动刷新优先级高于定时刷新。

当图谱正在定时刷新：

- 手动刷新按钮置灰。
- 提示：“知识图谱正在更新，请稍后再试。”

当图谱定时刷新失败：

- 用户可手动重试。

## 8. 根据图谱节点对话设计

### 8.1 节点对话入口

前端入口：

- 图谱视图中右击节点。
- 右键菜单展示“基于该节点对话”。
- 点击后打开提问弹窗或直接进入会话页。
- 若需要用户补充问题，弹窗中输入问题后提交。
- 提交成功后跳转到会话页面，并在对应会话中展示本轮节点对话。

输入形态：

```text
[节点: 供应链风险] 这个节点和最近上传的合同有什么关系？
```

用户可见层不需要出现 RagFlow 或 GraphRAG 字样。

### 8.2 后端问答流程

流程：

1. 接收 `nodeIds` 和 `question`。
2. 校验 `question` 非空。
3. 校验图谱状态。
4. 校验节点属于当前 dataset。
5. 读取节点详情，提取可展示给用户和可进入 prompt 的安全字段。
6. 组装图谱节点描述，例如节点名称、类型、摘要、关系、邻居节点摘要、RagFlow 返回的可公开 metadata。
7. 如果节点有关联 documentIds，先做 EvoMind 权限过滤。
8. 如果过滤后存在可用 documentIds，则使用用户原始问题对这些 documentIds 做一次受限 retrieve。
9. 将“图谱节点描述 + 可选文档召回内容”拼接为中性知识库上下文。
10. 创建或复用会话，调用现有会话链路生成回答。
11. 将会话 ID 和消息 ID 返回前端，前端跳转到会话页面。
12. 写入 `RagflowGraphJob(jobType=node_chat)`。

节点对话不要求 RagFlow 一定支持节点级问答 API。MVP 后端可以先把节点详情当作结构化上下文，并在存在 documentIds 时补一次受限文档召回。

### 8.3 权限边界

个人图谱：

```text
node.dataset.userId == currentUserId
node.dataset.scope == personal
node.dataset.enterpriseId == currentSpaceEnterpriseId
```

企业图谱：

```text
node.dataset.scope == enterprise
node.dataset.enterpriseId == activeEnterpriseId
currentUser is enterprise member
```

MVP 权限建议：

- 企业成员可以查看企业知识图谱并基于节点提问。
- 普通成员不能构建、刷新或删除企业图谱。
- 企业管理员和平台超级管理员可以构建、刷新、删除企业图谱。
- 普通成员节点问答时，后端必须将节点关联 documentIds 过滤到当前用户可读文件，再进行 retrieve。
- 如果过滤后没有可用文档，返回普通聊天或提示“当前节点关联资料暂无访问权限”。

### 8.4 Prompt 设计

发给模型的增强上下文必须使用中性口径：

```text
以下内容来自用户当前选中的知识节点及其关联资料，可作为回答参考。
回答时请自然使用相关信息，不要提及内部检索、图谱构建、资料编号或系统实现。
如果内容不足以回答问题，请直接说明信息不足，不要编造。
```

资料块标题：

```text
[资料 1]
节点：供应链风险
节点类型：风险主题
节点摘要：与供应商交付、违约条款和库存缓冲有关。
相关关系：影响 合同履约；关联 关键供应商
文件：xxx.pdf
路径：/个人知识库/xxx.pdf
内容：...
```

不得出现：

```text
RagFlow
GraphRAG
score
召回结果
定向召回
remote node id
chunk id
```

内部排查信息写入 audit，不进入用户可见 prompt。

## 9. 前端设计

### 9.1 图谱状态展示

在知识库区域增加图谱状态条或轻量面板。

状态文案：

```text
idle       知识图谱尚未构建
queued     知识图谱已加入更新队列
running    知识图谱正在更新
succeeded  知识图谱已更新
stale      有新内容变更，知识图谱待更新
failed     知识图谱更新失败
disabled   暂未开通知识图谱服务
```

更新中提醒：

```text
知识图谱正在更新，当前问答可能基于上一版内容。
```

首次构建提醒：

```text
知识图谱正在生成，完成后即可基于节点提问。
```

失败提醒：

```text
知识图谱更新失败，可稍后重试。
```

无配置提醒：

```text
暂未开通该服务。
```

容量不足提醒：

```text
企业大脑空间不足，请联系管理员扩容。
```

### 9.2 操作按钮

个人图谱：

- `构建图谱`
- `刷新图谱`
- `重试`

企业图谱：

- 企业管理员可见 `构建图谱`、`刷新图谱`、`重试`、`删除图谱`。
- 平台超级管理员可见所有企业图谱运维操作。
- 普通成员可以查看企业图谱和节点详情，但不展示 `构建图谱`、`刷新图谱`、`重试`、`删除图谱` 等写入或危险操作。

按钮置灰条件：

- RagFlow 无配置。
- RagFlow disabled。
- 容量不足。
- 当前已有 `queued/running/deleting`。
- 当前用户无权限。
- dataset 不存在或没有已解析文档。

### 9.3 轮询策略

前端轮询条件：

- 当前页面可见。
- 图谱状态为 `queued/running/deleting`。
- 上一轮请求已完成。
- 当前空间 capability 允许远端状态读取。

频率：

```text
每 30 秒一次
```

停止条件：

- 状态变为 `succeeded/failed/idle/stale/disabled`。
- 页面隐藏。
- 用户切换企业空间。
- 用户离开知识库页面。

### 9.4 图谱节点 UI

前端图谱展示应采用网状节点视图，而不是普通列表作为主视图。

基础形态：

- 节点以力导向图或可缩放网络图展示。
- 边展示节点之间的关系。
- 支持拖拽画布、缩放、节点高亮。
- 搜索节点后定位到对应节点。
- 节点数量过多时按类型、重要性、关系数或搜索结果做渐进加载。

节点展示字段：

- 节点主标签优先使用 RagFlow 返回的实体名、节点名或 `label/name/title`。
- 节点类型优先使用 RagFlow 返回的 `type/category/entity_type`。
- 节点大小可根据关系数、权重、频次或 RagFlow 返回的 importance 字段决定。
- 节点颜色按节点类型映射。
- 边标签优先使用 RagFlow 返回的关系名或 `relation/type/label`。

鼠标移动到节点上时展示 hover 浮层。浮层字段必须由后端筛选后返回，不能把 RagFlow 原始字段全量透出。

建议可展示字段：

- 节点名称。
- 节点类型。
- 节点摘要。
- 关联文件数。
- 相关关系数量。
- 重要度或权重，前提是 RagFlow 字段含义明确且适合用户理解。
- 最近更新时间。
- 来源范围，例如“来自企业知识库”或“来自个人知识库”。

不建议展示字段：

- remote node id。
- chunk id。
- score。
- 内部 metadata 原文。
- 未经过权限过滤的 documentIds。
- RagFlow 原始响应 JSON。

右键节点交互：

- 右击节点打开上下文菜单。
- 菜单包含“基于该节点对话”。
- 未来可扩展“查看关联文件”“展开相邻节点”“固定节点”等操作。
- 普通成员可以使用“基于该节点对话”，但后端仍必须过滤节点关联 documentIds。
- 点击“基于该节点对话”后，如果已有默认问题模板，可以直接创建会话；否则弹出问题输入框。
- 提交后前端跳转到会话页面，并在会话中展示对应问题和回答。

节点详情：

- 点击节点或 hover 后可打开详情抽屉。
- 详情抽屉展示节点摘要、关联文件、相关节点、关系说明。
- 详情字段同样使用后端筛选后的安全字段。

### 9.5 对话区提醒

用户从节点发起对话时，聊天区展示节点 chip：

```text
已选择节点：供应链风险
```

如果图谱更新中，发送前展示轻量提示：

```text
知识图谱正在更新，本次回答可能基于上一版内容。
```

如果节点关联资料不可访问：

```text
当前节点关联资料暂无访问权限。
```

## 10. 企业配置与容量降级

图谱能力必须复用现有 RagFlow capability。

### 10.1 无配置或停用

当当前空间无 RagFlow 配置、配置停用或配置不完整：

- 不展示图谱构建入口，或置灰。
- 后端拒绝图谱构建和刷新。
- 节点问答不调用 RagFlow。
- 文件上传和普通聊天不受影响。

### 10.2 容量不足

当容量不足：

- 禁止图谱构建、刷新、删除后重建等写入型动作。
- 已有已同步文档仍可拖拽召回。
- 如果已有成功图谱，是否允许节点问答取决于远端读取能力：
  - 如果节点问答只读取已有图谱，可允许。
  - 如果节点问答会触发新的图谱写入或重建，必须拒绝。

前端提示：

```text
企业大脑空间不足，请联系管理员扩容。
```

### 10.3 默认空间

默认空间图谱必须使用：

```text
enterpriseId = "-1"
```

不能继续依赖 `enterpriseId=null` 作为 RagFlow 配置和容量口径。

## 11. 权限设计

### 11.1 个人图谱权限

个人图谱：

- 当前用户可构建自己的个人图谱。
- 当前用户可刷新自己的个人图谱。
- 当前用户可删除自己的个人图谱。
- 其他用户不可查看、构建、刷新、删除。

### 11.2 企业图谱权限

企业图谱：

- 企业成员可查看所属企业的知识图谱。
- 企业成员可右击节点发起节点对话。
- 企业成员不可构建、刷新、删除企业图谱。
- 企业管理员可构建、刷新、删除本企业图谱。
- 平台超级管理员可查看和运维所有企业图谱。
- 普通成员节点问答必须经过节点关联 documentIds 的二次权限过滤。

### 11.3 节点权限风险

企业图谱节点可能来自多个文件，节点本身可能泄露文件中的实体、关系和业务事实。

MVP 建议：

- 企业成员可以看到图谱中的节点和边，但 hover 和详情中只展示后端筛选过的安全字段。
- 普通成员不能看到未过滤的 documentIds、chunkIds、score、内部 metadata 或 RagFlow 原始响应。
- 普通成员节点问答时，只有通过文档权限校验的关联资料可以进入二次 retrieve 和 prompt。
- 如果节点没有可访问关联文档，仍可基于节点名称、类型、摘要、关系等图谱描述回答，但必须提示资料不足，不能编造。

后续若要进一步降低企业图谱泄露风险，需要实现：

- 节点到 document 的关联。
- 当前用户可读 documentIds 计算。
- 节点过滤：只有关联到至少一个可读 document 的节点可见。
- 边过滤：只有两端节点均可见，且边关联资料可读时可见。
- retrieve 后二次权限校验。

## 12. 审计与可观测性

需要记录以下审计：

- 谁触发了个人图谱构建。
- 谁触发了企业图谱构建。
- 图谱构建触发来源：手动、定时、重试。
- 谁删除了图谱。
- RagFlow GraphRAG 请求结果。
- 失败原因。
- 节点问答使用了哪些 nodeIds、datasetIds、documentIds。
- 节点问答跳转到了哪个 sessionId/messageId。
- 节点问答是否因为图谱更新中使用上一版。
- 节点问答是否发生权限过滤。

推荐使用 `RagflowGraphJob.payload` 和现有 `retrieval_audit` 风格记录。

## 13. 分阶段实施计划

### Phase 0：GraphRAG API Spike

目标：

- 验证当前 RagFlow 部署版本的知识图谱 API 能力。
- 当前真实运行结论：基础 dataset、document upload、parse、status polling、retrieve、delete document 可用；旧假设路径 `POST /api/v1/datasets/:datasetId/graphrag` 返回 405。
- 知识图谱路径已确认并重跑：`POST /run_graphrag`、`GET /trace_graphrag`、`GET /knowledge_graph` 可用；当前部署删除图谱的可用路径是 `DELETE /graph`，不是官方文档中的 `DELETE /knowledge_graph`。

任务：

- 增强 spike 脚本并记录 GraphRAG run/trace/delete 的真实响应。
- 调用官方 `runGraphRag` 路径 `POST /api/v1/datasets/:datasetId/run_graphrag` 验证能否触发构建。
- 如果 run 成功，调用 `traceGraphRag` 路径 `GET /api/v1/datasets/:datasetId/trace_graphrag` 验证状态和进度返回。
- 如果 run 成功，调用 `getKnowledgeGraph` 路径 `GET /api/v1/datasets/:datasetId/knowledge_graph` 验证节点和边。
- 如果 run 成功，调用 `deleteKnowledgeGraph` 路径 `DELETE /api/v1/datasets/:datasetId/graph` 验证删除行为。
- 验证重复构建行为。
- 验证构建中状态。
- 验证是否能获得节点/边。
- 验证是否支持节点级问答或节点过滤。

验收：

- 有一份 spike 记录。
- 明确旧假设 GraphRAG 路径不可用，官方 run/trace/get 路径可用。
- 明确 GraphRAG 状态映射以 `trace_graphrag` 为准。
- 明确节点/边数据以 `knowledge_graph` 为准，不从 trace 中读取节点/边。
- 明确 GraphRAG 构建可能耗时 5 分钟以上，必须后台异步长轮询，不能以短轮询空图判断无节点/边。
- 明确完成图谱的节点字段包括 `id/entity_name/entity_type/description/source_id/pagerank`，边字段包括 `source/target/src_id/tgt_id/description/keywords/source_id/weight`。
- 明确当前部署删除图谱路径为 `DELETE /graph`。
- 明确节点问答需要兼容降级：节点描述 + 可访问 documentIds 二次 retrieve + 现有会话链路。

### Phase 1：后端图谱状态与运行记录

当前状态：已完成后端主体能力。

目标：

- 建立本地图谱状态和运行记录。

任务：

- 复用 `RagflowDataset.graphStatus` 等字段。
- 新增 `RagflowGraphJob` migration。
- 增加图谱状态枚举和映射函数。
- 增加图谱运行锁定逻辑。
- 增加 stale 标记方法。
- 将构建、刷新、删除、节点对话统一记录到 `RagflowGraphJob`。

验收：

- dataset 可记录 `idle/queued/running/succeeded/failed/stale`。
- 同一个 dataset 不能并发提交多个 running 图谱任务。
- 文档变更后可标记图谱 stale。
- 节点对话可写入 `node_chat` 记录。

实现说明：

- 已复用 `RagflowDataset` 图谱字段并新增 `RagflowGraphJob`。
- 已实现图谱 job 创建、锁定、完成、失败、active job 并发保护和 stale 标记。
- 当前 `RagflowGraphJob.jobType` 已覆盖 `build`、`refresh`、`delete`、`node_chat`；但 Phase 6 节点问答接口尚未落地，因此 `node_chat` 记录能力仍属于预留。

### Phase 2：手动构建与状态刷新 API

当前状态：已完成后端接口与核心语义；Phase 3 已接入前端状态条和手动操作。

目标：

- 用户可手动构建个人图谱。
- 企业管理员可手动构建企业图谱。
- 前端可查询图谱状态。

任务：

- 增加 `GET /graph/status`。
- 增加 `POST /graph/build`。
- 增加 `POST /graph/refresh`。
- 增加 `GET /graph/runs`。
- 接入 RagFlow capability。
- 接入个人/企业权限校验。
- 按官方路径封装 `runGraphRag`、`traceGraphRag`、`getKnowledgeGraph`。
- `deleteKnowledgeGraph` 按当前部署实测路径 `DELETE /graph` 封装，并保留配置项兼容其他版本。
- 增加 GraphRAG API capability：构建、trace、读取图谱、删除均可启用；失败时，构建/刷新/删除返回友好不可用原因，并写入 `RagflowGraphJob(status=failed|skipped, errorCode=unsupported)`。
- 保留远端调用开关，避免官方路径在某些 RagFlow 部署版本不可用时影响基础文档同步。

验收：

- 个人用户可构建个人图谱。
- 企业管理员可构建企业图谱。
- 普通成员不能构建企业图谱。
- 平台超级管理员可构建、刷新、删除任意企业图谱。
- 图谱进度可刷新。
- RagFlow 不可用时后端拒绝写入并返回友好原因。
- 容量不足时不触发图谱构建。

实现说明：

- 已增加 `GET /api/zclaw/ragflow/graph/status`、`POST /api/zclaw/ragflow/graph/build`、`POST /api/zclaw/ragflow/graph/refresh`、`DELETE /api/zclaw/ragflow/graph`、`GET /api/zclaw/ragflow/graph/runs`。
- 已兼容 `scope=personal|enterprise` 和 `source=workspace|shared-workspace`。
- 已接入 `enterpriseRagflowConfig` capability，默认空间按 `enterpriseId="-1"` 读取配置。
- 已接入容量检查，基于本地 `ragflowFileBlob` 用量判断图谱写入是否可启动。
- 已接入企业成员权限：普通成员可读企业 status，不可 build/refresh/delete；企业 `admin/owner` 与平台 `admin` 可写。
- 已在 skipped 降级路径记录 `ragflow_unavailable`、`ragflow_quota_exceeded`、`dataset_missing`，且不触发远端调用。
- 已在远端调用失败路径记录 `failed`；GraphRAG 不支持类错误归一为 `unsupported`。
- 已实现 trace 进度同时写入 job 和 dataset，status 在 active job 期间优先展示 job 进度。
- 已实现 `canChatWithNode` 的可用上一版语义：只有曾成功构建过图谱时才返回 `true`。
- 已实现 service 层 delete job、controller public delete 路由和 `RagflowClient.deleteKnowledgeGraph`。
- 暂未新增删除路径配置字段，当前仍按 Phase 0 spike 结果使用 `DELETE /graph`。

已覆盖测试：

```bash
pnpm --filter @insightweaver/api test -- src/zclaw/ragflow/ragflow-graph.service.test.ts src/zclaw/zclaw-ragflow.controller.test.ts
pnpm --filter @insightweaver/api build
```

### Phase 3：前端图谱状态展示与手动操作

当前状态：已完成知识库侧栏入口；节点图谱视图仍属于 Phase 5。

目标：

- 前端可展示图谱状态。
- 用户可手动触发构建/刷新。
- 更新中有友好提醒。

任务：

- 在 `apps/web/src/api/moudles/zclaw.ts` 增加 graph API 封装。
- 在知识库页面增加图谱状态条。
- 增加构建、刷新、重试按钮。
- 增加 `queued/running/deleting` 轮询。
- 增加更新中提示。
- 增加无配置、容量不足、无权限置灰提示。

验收：

- 图谱未构建、构建中、成功、失败、stale 状态文案正确。
- 更新中不会重复提交刷新。
- 更新中对话前有提示。
- 无配置和容量不足时入口置灰或隐藏。
- 普通成员看不到企业图谱危险操作。

实现说明：

- 已在 `KnowledgeBaseSidebarSection` 工具栏下方接入轻量 `KnowledgeGraphStatusPanel`。
- 已同时展示个人图谱和企业图谱；企业图谱仅在存在 active enterprise 时显示。
- 已接入 `GET /graph/status`、`POST /graph/build`、`POST /graph/refresh`、`DELETE /graph`。
- 已按后端 `canBuild/canRefresh/canDelete` 控制按钮显示，不在前端重新推断企业角色。
- 已在 `queued/running/deleting` 时启用 30 秒轮询，页面隐藏或进入终态后停止。
- 已在文件树刷新、路径同步、文件解析完成后刷新图谱 status。
- 已将知识库树的 RagFlow 文件状态、重试和同步动作透传到 `FileTree`，保持工作区树现有行为不变。
- 已在 Phase 5 补齐 `GET /graph/nodes` 和节点网络图查看；节点问答仍留到 Phase 6。

### Phase 4：定时刷新

目标：

- 支持图谱按周期自动刷新。

任务：

- 增加图谱自动刷新配置。
- 在超级管理员 RagFlow 配置管理页面开放自动更新开关和频率配置。
- 增加定时扫描任务。
- 扫描 stale 或超过刷新间隔的 dataset。
- 避免并发提交同一个 dataset。
- 记录 triggerType=`scheduled`。

验收：

- 开启自动刷新后，stale 图谱可在周期内自动提交刷新。
- 超级管理员可通过 RagFlow 配置列表操作列的独立按钮，按默认空间或真实企业配置是否自动更新和更新频率。
- 关闭自动刷新后，不自动提交。
- running 图谱不会被重复提交。
- 定时刷新失败可在运行记录中看到原因。

### Phase 5：图谱节点读取

目标：

- 支持查看图谱节点，为节点对话做准备。

任务：

- 已根据 Spike 结果封装 live 节点读取能力，数据源为 RagFlow `knowledge_graph`，不从 trace 读取节点/边。
- Phase 5 不新增节点/边缓存表；如后续发现远端节点接口不稳定，再单独进入缓存设计。
- 已增加 `GET /graph/nodes`，支持 `source/scope/enterpriseId/keyword/limit`。
- 前端已增加网状节点图谱视图，使用现有 ECharts graph series，不新增图谱可视化依赖。
- 前端支持点击/hover 节点查看后端筛选后的安全详情。
- 前端右击节点显示“基于该节点对话（Phase 6）”禁用菜单项，本期不调用问答接口。

验收：

- 用户可看到个人图谱节点。
- 企业成员可看到企业图谱节点。
- 普通成员不能看到危险操作或未过滤的内部字段。
- 节点详情能展示关联文件数量。

### Phase 6：根据图谱节点对话

目标：

- 用户可以选择图谱节点并基于节点发起对话。

任务：

- 不新增 `POST /graph/chat`；已复用现有 `chat/message` 和 `chat/message/stream`，通过可选 `graphNodeContext` 传递节点上下文。
- 已校验 nodeIds、图谱状态和节点读取权限。
- 已拼接图谱节点安全描述、相关关系和相关文件数量，不暴露 raw payload 或内部 metadata。
- 如果节点存在 documentIds，则使用用户原始问题对可访问 documentIds 做一次受限 retrieve；不可访问资料会被过滤。
- 本地历史消息只保存原始问题，发给 KM Agent 的 upstream message 才包含图谱上下文和召回片段。
- 普通用户对话框上方提供明确的“知识图谱”入口，点击后打开当前空间的图谱视图。
- 前端已支持从图谱节点进入对话页，并在聊天框展示可移除的节点 chip。
- 已写入 `RagflowGraphJob(jobType=node_chat)` 审计记录，不改变 dataset 图谱状态。

验收：

- 个人节点问答只使用当前用户个人图谱。
- 企业成员可基于所属企业图谱节点发起对话。
- 图谱更新中可提示使用上一版。
- 无可访问关联资料时不越权召回。
- 节点对话成功后前端跳转到对应会话。
- prompt 不暴露内部实现。

### Phase 7：稳定性与运维

目标：

- 提升图谱能力的可恢复性和可观测性。

任务：

- 增加失败重试。
- 增加图谱删除。
- 增加运行记录列表。
- 增加后台运维入口。
- 增加远端状态对账。
- 增加权限变更后的 stale 或 metadata 更新机制。

验收：

- 失败任务可追踪、可重试。
- 企业管理员可以看到最近图谱运行结果。
- 平台管理员可以定位企业图谱失败原因。
- 权限变更后不会继续向无权限用户暴露节点或资料。

## 14. 测试计划

### 14.1 后端单元测试

- 图谱状态映射。
- capability 不可用时拒绝 build。
- 容量不足时拒绝 build。
- 容量不足时已有读取能力不被关闭。
- 个人图谱权限。
- 企业图谱管理员权限。
- 普通成员不能构建企业图谱。
- 企业成员可以读取所属企业图谱节点。
- 平台超级管理员可以运维企业图谱。
- 同一 dataset 不能重复提交 running run。
- 图谱构建、刷新、删除、节点对话都会写入 `RagflowGraphJob`。
- 文档变更后标记 stale。
- traceGraphRag 失败时写入 failed。
- 节点对话存在 documentIds 时会按用户权限过滤后再 retrieve。
- 节点问答 prompt 不包含内部词。

### 14.2 后端集成测试

- 构建个人图谱。
- 构建企业图谱。
- 图谱状态刷新。
- 手动重试失败图谱。
- 定时刷新 stale 图谱。
- 超级管理员配置图谱自动更新开关和频率后，调度任务按配置执行。
- 无配置空间图谱入口降级。
- 容量不足空间图谱入口降级。
- 节点问答只使用授权节点和授权文档。
- 节点问答完成后返回 sessionId 并可跳转到会话。
- 图谱更新中返回 warning。

### 14.3 前端测试

- 图谱状态条文案。
- 构建中轮询。
- 成功后停止轮询。
- 失败后展示重试。
- 无配置提示。
- 容量不足提示。
- 企业普通成员不展示危险操作。
- 企业普通成员可以查看网状企业图谱。
- 节点 hover 展示后端筛选后的安全详情。
- 右击节点展示“基于该节点对话”。
- 节点 chip 展示。
- 更新中对话提示。

### 14.4 手工验收

- 用户 A 构建个人图谱，用户 B 不可见。
- 用户在默认空间构建图谱时使用 `enterpriseId="-1"` 配置。
- 企业管理员可构建企业图谱。
- 企业普通成员可以查看企业图谱，但不能重建、刷新或删除图谱。
- 超级管理员可以在 RagFlow 配置管理页配置图谱是否自动更新和更新频率。
- 图谱构建中前端展示友好提醒。
- 图谱刷新失败后可重试。
- 文档更新后图谱变为待更新。
- 定时刷新可自动处理待更新图谱。
- 鼠标移动到图谱节点时可以看到节点详情。
- 右击节点发起对话后跳转到对应会话页面。
- 根据节点提问时回答基于该节点描述和可访问关联资料。
- RagFlow 无配置时文件上传和普通聊天仍正常。

## 15. 风险与待确认

### 15.1 RagFlow GraphRAG API 差异

GraphRAG run/trace/get/delete 的请求和响应需要以当前部署版本为准。Phase 0 真实运行已确认，旧假设路径 `POST /api/v1/datasets/:datasetId/graphrag` 返回 405 Method Not Allowed。`POST /run_graphrag`、`GET /trace_graphrag`、`GET /knowledge_graph` 可用；删除图谱在当前部署中使用 `DELETE /graph`，而不是官方文档中的 `DELETE /knowledge_graph`。

风险：

- 官方文档和当前部署在删除图谱路径上不一致。
- trace 不返回进度。
- GraphRAG 构建耗时超过前端请求窗口。
- `knowledge_graph` 在构建未完成时不返回节点/边。
- 重复 run 语义不明确。
- delete 后远端残留数据。

应对：

- Phase 0 已记录旧路径不可用，run/trace/get/delete 的可用路径已确认。
- Phase 1 按实测路径封装能力，并保留配置项兼容其他 RagFlow 版本。
- 图谱构建必须异步运行，由后台 job 长轮询 `trace_graphrag`，前端只展示状态和“正在更新”的友好提示。
- 本地状态不要完全依赖远端字段。
- 节点对话设计保留 retrieve 降级路径。

### 15.2 企业图谱泄露风险

企业图谱节点可能暴露普通成员无权访问文件中的实体和关系。

应对：

- MVP 允许企业成员查看企业图谱，但前端 hover、详情、右键菜单只展示后端筛选后的安全字段。
- 普通成员不能看到未过滤的 documentIds、chunkIds、score、内部 metadata 或 RagFlow 原始响应。
- 普通成员节点问答必须做 documentIds 权限过滤。
- 如果节点关联资料过滤后为空，只允许基于节点描述作有限回答，并提示资料不足。
- 后续再实现更严格的节点/边按 document 权限过滤。

### 15.3 图谱构建成本和容量

GraphRAG 可能产生额外远端存储和计算成本。

应对：

- 图谱构建视为写入型能力。
- 受企业 RagFlow 配置和容量限制。
- 定时刷新限流。
- 平台后台保留运行记录和失败原因。

### 15.4 更新中体验

图谱构建可能较慢，用户可能在构建中继续提问。

应对：

- 前端明确展示更新中。
- 已有成功图谱时允许使用上一版。
- 无成功图谱时禁用节点问答。

## 16. 最终建议

推荐按照以下顺序推进：

```text
先验证 GraphRAG API；
再实现 dataset 级图谱构建和状态；
再做前端状态展示和手动刷新；
然后接入定时刷新；
最后实现节点列表和节点对话。
```

第一版 MVP 的关键验收不是“图谱可视化多炫”，而是：

```text
图谱能构建；
状态能看见；
手动和定时刷新可控；
更新中用户有预期；
节点对话不越权；
RagFlow 不可用时主链路不失败。
```

## 17. 当前状态流转与按钮展示（2026-06-10 修订）

本节描述当前代码应当遵循的知识图谱状态闭环。用户界面不展示内部实现名称；用户可见文案统一使用“知识库”“知识图谱”“知识服务”。

### 17.1 Dataset 级状态

Dataset 级状态记录在图谱所属的数据映射上，用于驱动侧栏、图谱弹窗和节点问答能力。

```text
idle -> queued -> running -> succeeded
idle -> queued -> running -> failed
succeeded|idle|failed -> stale（知识库文件发生变化后）
deleting -> idle（删除成功后清空 lastGraphRunAt）
```

- `idle`：当前范围没有可展示的图谱版本。
- `queued`：图谱新建、更新或删除任务已排队。
- `running`：图谱新建或更新正在执行。
- `succeeded`：已有可展示、可用于节点问答的成功图谱版本。
- `failed`：最近一次新建或更新失败；如果保留 `lastGraphRunAt`，仍可展示上一版。
- `stale`：知识库内容已变化，图谱可展示但需要更新。
- `deleting`：删除任务正在执行；删除完成后回到 `idle`，并清空 `lastGraphRunAt`。

### 17.2 Job 级状态

Job 级状态记录每一次图谱操作的执行结果。

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> skipped
```

- `build`、`refresh`、`delete` 是会影响 Dataset 图谱状态的写操作。
- `status_refresh`、`node_chat` 只记录审计或读取过程，不应锁定 Dataset 图谱状态。
- `skipped` 只用于知识服务未配置、容量不足、数据映射缺失等未真正触发远端任务的场景。

### 17.3 按钮展示规则

按钮展示以 `lastGraphRunAt` 是否存在作为“是否已有图谱版本”的主要判断。

- `lastGraphRunAt` 为空：只展示“新建图谱”。
- `lastGraphRunAt` 非空：展示“更新图谱”；有删除权限时展示“删除图谱”。
- `queued`、`running`、`deleting`：图谱写操作按钮禁用，并显示正在新建、更新或删除的提示。
- 删除完成后：后端状态回到 `idle` 且 `lastGraphRunAt=null`，前端只展示“新建图谱”。
- 普通成员没有写权限时：不展示或禁用写操作按钮；后端仍做权限校验。
- 图谱弹窗不提供单独的“权限”按钮；权限细节由后端控制，前端只展示必要的禁用态和提示。

### 17.4 前端刷新规则

- 新建、更新、删除提交后，前端立即刷新一次 `graph/status`。
- 当状态从 `queued/running/deleting` 进入 `succeeded/stale/failed/idle` 等终态时，前端必须立即刷新 `graph/status` 和 `graph/nodes`。
- 图谱弹窗切换 personal/enterprise tab 时，需要清空旧节点数据并重建图谱渲染实例，避免复用旧 ECharts 实例导致白屏。
- active 状态轮询用于兜底感知后端任务进度，不替代终态后的节点刷新。

### 17.5 节点问答上下文规则

前端发起节点问答时传入：

```json
{
  "graphNodeContext": {
    "source": "workspace",
    "scope": "personal",
    "enterpriseId": "enterprise-1",
    "datasetMappingId": "dataset-mapping-id",
    "nodeIds": ["node-id"]
  }
}
```

- `datasetMappingId` 是节点问答定位图谱数据的权威字段。
- 后端收到 `datasetMappingId` 时，必须先按该 id 定位数据映射，再校验 `source`、`scope`、`enterpriseId`、当前用户和企业成员权限。
- `enterpriseId` 来自状态接口或企业请求上下文，用于一致性校验；不能优先拿 `enterpriseId=null` 去查默认空间后再误报没有图谱数据。
- personal 图谱校验 `userId` 必须等于当前用户。
- enterprise 图谱校验当前用户必须是企业成员；写操作要求企业 `owner/admin` 或平台管理员。
- 如果未传 `datasetMappingId`，后端才回退到 `source/scope/enterpriseId` 的旧定位逻辑。
- 节点问答失败时，用户可见错误不出现内部实现名，统一提示为知识图谱数据暂不可用并引导刷新或重新打开节点。
