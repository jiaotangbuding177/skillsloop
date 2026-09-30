# EvoMind 接入 RagFlow v2 设计与实施计划

## 0. 当前实现快照（截至 2026-06-05）

当前代码已基本完成 Phase 0-5 的 MVP 主链路，并修复了几处联调中暴露的问题：

- 后端已实现 RagFlow client、dataset/document/blob/job 映射、异步同步任务、上传后 parse、状态刷新、失败重试。
- 个人知识库 dataset 已从“仅按 `userId` 绑定”调整为“按 `userId + enterpriseId/null` 绑定”：
  - 默认空间：`enterpriseId = null`，dataset 名称形如 `evomind-personal-${userId}-default`。
  - 组织空间：`enterpriseId = 当前组织 id`，dataset 名称形如 `evomind-personal-${userId}-enterprise-${enterpriseId}`。
  - 企业共享知识库仍按 `scope=enterprise + enterpriseId` 绑定。
- 数据库索引已调整：personal dataset 需要两个 partial unique index，分别约束默认个人空间和组织个人空间。旧的 `ragflow_dataset_personal_uq(userId)` 必须删除，否则组织空间 dataset 创建会触发 `Unique constraint failed on the fields: (userId)`。
- 个人知识库上传会在主文件上传成功后创建本地 pending document 映射并提交 sync job，避免“RagFlow dataset 创建成功但本地没有文档记录、文件没有进入知识库”的空窗。
- personal 文档状态查询、刷新、重试均按当前请求组织上下文过滤 `enterpriseId`；默认空间只看 `enterpriseId=null`，组织空间只看该组织 id，避免切换组织后串状态。
- 前端状态展示已覆盖两个上传入口：
  - `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
  - `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`
- 前端刷新机制已从“页面加载后刷新一次”扩展为：
  - 保留首次 `list -> refresh once`。
  - 当前文件树里存在 `uploadStatus=pending` 或 `parseStatus=queued/running` 的 RagFlow 文档时，每 10 秒低频批量刷新一次。
  - 页面隐藏、未启用、未登录、文件树为空、没有未完成文档、上一轮请求未完成时不发起刷新。
  - 普通上传、拖拽上传、节点菜单上传、文件夹上传成功后，会对上传成功的文件做短轮询，尽快拉到 pending/running 状态。
  - `parsed` 成功勾只在当前页面内从非 parsed 变为 parsed 时展示 3 秒；刷新页面或重新进入时不常驻展示。
- Phase 4 文件生命周期同步已完成 MVP 接入：
  - 个人知识库和企业共享知识库的编辑会重新提交 upload sync job；内容 hash 不变时复用原 blob，内容变化时切换 blob 并维护 `refCount`。
  - 重命名/移动会更新本地 `ragflow_documents.path/filename` 并提交 metadata update job，不重复上传 RagFlow。
  - 个人文件从知识库移出会软删除 mapping；文件移入个人知识库会提交同步。
  - 文件删除和目录删除会软删除对应 mapping，并在最后引用释放时异步删除 RagFlow document。
  - RagFlow metadata update 若当前部署返回 405/MethodNotAllowed，会将文档标记为 `metadataSyncStatus=unsupported`，不让主同步 job 因此失败。
- Phase 5 拖拽文件定向召回已完成 MVP 接入：
  - 普通聊天不触发 RagFlow；只有拖拽知识库文件并发送问题时才尝试召回。
  - 召回前解析本地 mapping 和权限，只向 RagFlow 传后端确认可用的 `dataset_ids` 与 `document_ids`。
  - 同一企业上下文内支持组织个人知识库文件与企业共享知识库文件一起定向召回，但仍严格限定到被拖拽文件。
  - 普通聊天附件、非知识库路径、未同步或缺少 `ragflowDocumentId` 的文件会被忽略；没有可用知识库文件时跳过 RagFlow。
  - 已接入低信息问题 query rewrite、`retrieval_audit` job 记录、`streamMessage(...)` 前置 prompt 注入；召回失败会降级为普通聊天。
  - 前置 prompt 已改为中性的“知识库文件内容/资料”口径，不向模型暴露 `RagFlow`、`定向召回`、`召回结果`、`score` 等内部实现细节。
  - 前后端历史消息与展示层均有兜底清洗：用户消息只展示原始问题；助手消息只在出现“召回片段/召回结果/定向召回/上述片段”等内部泄漏特征时做保守替换。
- 当前仍未完成的后续重点：知识图谱、历史 backfill、失败任务批量补偿、运维入口、图谱权限风险控制，以及更完整的 metadata 能力差异处理。

## 1. 背景

EvoMind 当前已经具备个人知识库、企业共享知识库、文件上传、文件更新、文件删除、聊天会话、聊天窗口附件上传等能力。现阶段需要把 RagFlow 接入为后端知识引擎，负责文档解析、切片、向量检索、指定文档召回、解析进度展示，以及个人/企业知识图谱构建。

本版本在第一版设计基础上明确了几个关键产品决策：

- RagFlow 只作为知识引擎，不作为 EvoMind 权限系统、文件系统或会话系统。
- EvoMind 前端不直接访问 RagFlow。
- 每个用户在每个个人空间对应一个 personal dataset；个人空间由 `userId + enterpriseId/null` 标识，默认空间 `enterpriseId=null`，组织空间 `enterpriseId=当前组织 id`。
- 每个企业对应一个 enterprise dataset。
- MVP 阶段普通聊天不默认触发 RagFlow retrieve。
- 只有用户把知识库文件拖拽到聊天输入框并基于这些文件提问时，才触发 RagFlow 定向召回。
- 拖拽文件召回必须限定 `document_ids`，不能扩大到整个 dataset。
- 同一个 dataset 内做内容去重；重复业务文件允许有多条本地映射，但不重复上传 RagFlow。
- 需要为未来部门、组织、指定用户、权限组等共享权限预留 metadata 和本地权限模型扩展空间。

## 2. 当前项目落点

### 2.1 后端现状

当前 RagFlow 接入应优先落在 `apps/api/src/zclaw` 模块内，后续可按复杂度拆成独立 `ragflow` 子目录或模块。

可复用能力：

- `ZclawController`
  - 已有个人工作区上传：`POST /api/zclaw/workspace/upload`。
  - 已有共享工作区上传：`POST /api/zclaw/shared-workspace/upload`。
  - 已有聊天附件上传：`POST /api/zclaw/chat/files`。
  - 已有聊天流式消息：`POST /api/zclaw/chat/message/stream`。
- `ZclawService`
  - 已有个人 workspace 文件上传、创建、更新、移动、删除。
  - 已有 shared-workspace 文件上传、创建、更新、移动、删除。
  - 已有共享空间权限校验 `assertSharedWorkspacePermission(...)`。
  - 已有 `streamMessage(...)` conversation 主链路。
- `ZclawKmAgentClient`
  - 已有 EvoMind workspace/shared-workspace/conversation HTTP 封装。
- `EnterpriseService`
  - 已有企业成员校验、企业 OpenClaw 实例上下文解析。
- `packages/db/prisma/schema.prisma`
  - 已有 `User`、`Enterprise`、`EnterpriseMembership`、`SharedWorkspacePermission`、`ZclawSession`、`ZclawMessage` 等模型。

### 2.2 前端现状

主要接入点：

- `apps/web/src/api/moudles/zclaw.ts`
  - 增加 RagFlow 状态、同步、召回、图谱 API 封装。
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
  - 现有工作区文件树、上传任务、聊天输入和附件逻辑主要在这里。
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`
  - admin workspace route 中仍会渲染的独立工作区侧边栏；它也会直接上传 workspace/shared-workspace 文件，必须同步维护 RagFlow 状态展示和上传后短轮询。
- `apps/web/src/components/zclaw/ZclawAssistantPage.tsx`
  - 也存在聊天附件上传和消息发送能力；实现时需要确认当前产品实际使用入口，避免只改一个聊天页。
- `apps/web/src/lib/workspace-paths.ts`
  - 定义了个人知识库、对话附件等工作区路径常量。

### 2.3 当前剩余不足

Phase 0-5 的基础接入、上传同步、状态展示、文件生命周期同步、拖拽文件定向召回和重试已经落地。后续主要不足集中在：

- 知识图谱构建、状态展示、权限控制尚未落地。
- 历史文件 backfill、失败任务批量补偿、批量运维入口尚未完整实现。
- 企业图谱可能暴露无权限实体/关系，图谱查看、构建、删除权限需要继续收口。
- RagFlow metadata 更新策略仍需结合当前 RagFlow 版本能力继续验证。

## 3. 核心设计原则

### 3.1 RagFlow 只作为知识引擎

RagFlow 负责：

- dataset 管理。
- document 管理。
- 文档解析。
- 文档切片。
- 向量检索。
- GraphRAG / 知识图谱。

RagFlow 不负责：

- EvoMind 用户权限。
- EvoMind 企业权限。
- 共享工作区权限。
- 部门、组织、指定用户共享权限。
- 聊天会话管理。
- 文件业务生命周期管理。

这些能力仍由 EvoMind 后端维护。

### 3.2 前端不直接调用 RagFlow

RagFlow API key 只保存在后端环境变量中。前端所有 RagFlow 相关操作必须通过 EvoMind API 完成。

新增环境变量：

```text
RAGFLOW_BASE_URL
RAGFLOW_API_KEY
RAGFLOW_DEFAULT_EMBEDDING_MODEL
RAGFLOW_DEFAULT_CHUNK_METHOD
```

### 3.3 Dataset 划分

RagFlow dataset 按业务主体划分：

```text
userId + enterpriseId/null -> personal ragflowDatasetId
enterpriseId -> enterprise ragflowDatasetId
```

personal dataset 的空间语义：

```text
enterpriseId = null -> 默认个人空间
enterpriseId = 当前组织 id -> 该组织上下文下的个人空间
```

因此同一用户在默认空间、组织 A、组织 B 的个人知识库互相隔离；同内容文件只在同一个 dataset 内去重，不跨默认空间/组织空间复用 blob。企业共享知识库仍按 `enterpriseId -> enterprise ragflowDatasetId` 绑定。

MVP 不按部门、文件夹、自组织、项目组拆分企业共享 dataset。未来更细粒度权限通过 EvoMind 权限体系、本地映射表、RagFlow metadata、召回后二次权限校验实现。

## 4. 会话与召回规则

### 4.1 EvoMind 仍使用统一会话

EvoMind 不新增 RagFlow 会话，也不把现有会话拆成“个人会话”和“企业会话”。当前 `ZclawSession` 和 EvoMind/OpenClaw conversation 仍是主会话体系。

用户可以在同一个聊天输入框中拖拽知识库文件，但 MVP 要限制一次消息只能使用同一知识范围的文件。

### 4.2 普通聊天不触发 RagFlow

MVP 阶段只有一种情况触发 RagFlow retrieve：

```text
用户把知识库文件拖拽到聊天输入框，并基于这些文件发送问题。
```

如果用户没有拖拽知识库文件：

- 不调用 RagFlow retrieve。
- 不拼接知识库召回上下文。
- 直接走现有 `streamMessage(...)` 到 EvoMind conversation 的流程。

这和第一版“默认检索 personal/enterprise dataset”的设计不同，v2 以“拖拽文件定向召回”为 MVP 范围。

### 4.3 拖拽个人知识库文件

召回范围：

```text
dataset_ids = [当前用户当前个人空间 personal datasetId]
document_ids = [拖拽文件对应的 ragflowDocumentId]
```

后端流程：

1. 接收消息中绑定的文件信息。
2. 根据 `source/path` 查询本地 `ragflow_documents` 映射。
3. 确认文档属于当前用户个人知识库。
4. 根据当前请求组织上下文确认 personal `enterpriseId`：默认空间为 `null`，组织空间为当前组织 id。
5. 校验当前用户对该文件有读取权限，且文档映射属于当前 personal 空间。
6. 获取 personal `ragflowDatasetId` 和对应 `ragflowDocumentId`。
7. 调用 RagFlow retrieve，并限定 `document_ids`。
8. 将知识库内容上下文拼接到 prompt。
9. 调用现有 EvoMind conversation 流式逻辑。

### 4.4 拖拽企业共享知识库文件

召回范围：

```text
dataset_ids = [该企业 enterprise datasetId]
document_ids = [拖拽文件对应的 ragflowDocumentId]
```

后端流程：

1. 接收消息中绑定的共享知识库文件信息。
2. 根据 `source/path/enterpriseId` 查询本地 `ragflow_documents` 映射。
3. 确认该文件属于对应企业共享知识库。
4. 调用统一权限方法校验当前用户可读该文件。
5. 获取 enterprise `ragflowDatasetId` 和对应 `ragflowDocumentId`。
6. 调用 RagFlow retrieve，并限定 `document_ids`。
7. 将知识库内容上下文拼接到 prompt。
8. 调用现有 EvoMind conversation 流式逻辑。

注意：

```text
不是因为当前会话处于企业上下文才检索企业 dataset，
而是因为被拖拽文件来自企业共享知识库，所以检索该企业 dataset。
```

### 4.5 多文件召回

同一消息内支持多文件。当前 MVP 已支持同一知识范围内多文件召回，也支持同一企业上下文内的“组织个人知识库文件 + 企业共享知识库文件”一起定向召回。

允许：

```text
个人知识库文件 A + 个人知识库文件 B
同一企业共享知识库文件 A + 同一企业共享知识库文件 B
同一企业上下文内：组织个人知识库文件 A + 该企业共享知识库文件 B
```

仍暂缓：

```text
企业 A 文件 + 企业 B 文件
默认个人空间文件 + 企业共享知识库文件
个人文件 + 多企业文件
```

召回约束：

```text
无论涉及一个还是多个 dataset，后端都必须限定到当前消息中可用文件对应的 document_ids。
不能因为处于企业上下文就扩大到整个 enterprise dataset。
```

普通聊天附件、非知识库路径、未同步或没有 `ragflowDocumentId` 的文件会被忽略。如果没有任何可用知识库文件，本次消息跳过 RagFlow，直接走普通聊天链路。

共享知识库文件召回必须处于 active enterprise context，并复用 `shared-workspace` read 权限校验。缺少企业上下文或无读取权限时，后端拒绝召回，不能只依赖前端。

### 4.6 召回上下文与用户可见文本

RagFlow 是内部知识引擎，不应出现在发给模型的可见上下文提示词里，也不应被模型自然复述给用户。当前已落地规则：

- 前置上下文使用中性口径：

```text
以下内容来自用户当前选中的知识库文件，可作为回答参考。
回答时请自然地使用相关信息，不要提及这些内容的来源、检索过程、资料编号或内部上下文。
如果内容不足以回答问题，请直接说明信息不足，不要编造。
```

- 资料块标题使用 `[资料 n]`，只保留 `文件`、`路径` 等对回答有帮助的信息。
- prompt 中不出现 `RagFlow`、`定向召回`、`召回结果`、`score`。
- `score`、chunk 原文、rewrite、retrieve request 等排查信息仍保留在 `retrieval_audit` job payload 中，不放入用户可见 prompt。
- 用户消息历史返回前必须清洗增强上下文，只展示 `用户原始问题`；清洗逻辑需兼容旧的 RagFlow 前缀和新的知识库前缀。
- 助手消息展示前做保守清洗：只有出现“召回片段/召回结果/定向召回/上述片段”等内部泄漏特征时，才替换为“知识库内容/相关内容”等自然表达，避免普通聊天中用户主动讨论 RagFlow 时被误改。
- 前端渲染层保留同样的兜底清洗，防止远端历史或旧本地快照穿透到 UI。

## 5. 低信息问题优化

低信息问题示例：

```text
这个文件讲什么？
这个文件说了什么？
总结一下这个文件。
这份文档主要内容是什么？
帮我概括一下。
这个文档有什么重点？
```

这些问题只有在用户拖拽了知识库文件时才触发优化。没有拖拽文件时，不触发 RagFlow。

Query rewrite 规则：

```text
总结文件《{filename}》的主题、结构、关键结论、重要内容、关键数据、待办事项和风险点。
```

即使问题很泛，也只能检索当前消息绑定的 `document_ids`，不能扩大到整个 dataset。

## 6. 个人知识库设计

### 6.1 范围识别

当前项目中个人知识库物理路径为 `个人知识库`。实现时应使用已有路径常量，而不是在多处硬编码。

建议新增后端工具方法：

```ts
isPersonalKnowledgePath(path: string): boolean
```

规则：

```text
path === "个人知识库" 或 path startsWith "个人知识库/"
```

对话附件目录不等同于个人知识库。聊天附件是否同步到 RagFlow，要由“聊天附件接入策略”单独决定，避免把所有临时附件都沉淀为知识库文档。

### 6.2 权限

个人知识库召回前必须校验：

```text
document.userId == currentUserId
document.scope == personal
document.source == workspace
document.enterpriseId == currentRequestEnterpriseId/null
```

个人文档不可跨用户召回，也不可跨个人空间召回：

- 默认空间请求只允许访问 `enterpriseId = null` 的 personal 文档。
- 组织空间请求只允许访问 `enterpriseId = 当前组织 id` 的 personal 文档。
- 同一用户切换组织后，个人知识库 RagFlow 状态、dataset、document mapping 都应独立。

### 6.3 生命周期

个人知识库文件支持：

- 上传。
- 更新。
- 重命名。
- 移动。
- 删除。
- 目录删除。
- 解析状态刷新。
- 同步失败重试。

## 7. 企业共享知识库设计

### 7.1 Dataset

每个企业对应一个 RagFlow dataset：

```text
enterpriseId -> enterprise ragflowDatasetId
```

企业共享知识库中的文档都同步到该企业 dataset。

### 7.2 MVP 权限

MVP 可以先按企业成员身份判断读取权限：

```text
当前用户是该企业 active member -> 可以读取企业共享知识库文件
当前用户不是该企业 active member -> 不可读取
```

但代码结构不能写死为简单成员判断。必须抽象统一权限方法：

```ts
canReadPersonalKnowledgeFile(userId, fileMeta)
canReadSharedKnowledgeFile(userId, enterpriseId, fileMeta)
```

当前项目已有 `SharedWorkspacePermission` 和 `assertSharedWorkspacePermission(...)`，RagFlow 权限方法应复用或包裹现有逻辑，后续部门、组织、指定用户共享都接入这里。

### 7.3 未来共享层级预留

企业共享知识库未来可能支持：

- 企业全员可见。
- 部门可见。
- 多部门可见。
- 项目组可见。
- 指定用户可见。
- 指定角色可见。
- 文件夹继承权限。
- 文件单独覆盖权限。

因此本地映射和 metadata 预留：

- `sharedFolderId`
- `parentFolderId`
- `orgUnitId`
- `allowedOrgUnitIds`
- `allowedUserIds`
- `allowedRoleIds`
- `visibilityType`
- `permissionGroupId`
- `permissionVersion`

## 8. RagFlow Metadata 设计

### 8.1 目的

虽然 MVP 只对拖拽文件召回，并且 retrieve 阶段限定 `document_ids`，但 metadata 仍有价值：

- 标记来源。
- 支持未来默认知识库检索时做权限过滤。
- 支持召回后二次审计。
- 支持图谱来源追踪。
- 支持文件移动、重命名后的 metadata 更新。

metadata 不能替代 EvoMind 权限体系。retrieve 前后都应由 EvoMind 做权限校验。

### 8.2 个人知识库 metadata

```json
{
  "evomind": {
    "scope": "personal",
    "source": "workspace",
    "bizDocumentId": "local-ragflow-document-id",
    "datasetMappingId": "local-dataset-id",
    "fileBlobId": "local-blob-id",
    "ownerUserId": "user-id",
    "enterpriseId": null,
    "sharedFolderId": null,
    "orgUnitIds": [],
    "visibilityType": "owner_only",
    "permissionGroupIds": [],
    "permissionVersion": 1,
    "path": "个人知识库/项目总结.md",
    "filename": "项目总结.md",
    "isDeleted": false,
    "updatedAt": "2026-06-02T00:00:00+08:00"
  }
}
```

### 8.3 企业共享知识库 metadata

```json
{
  "evomind": {
    "scope": "enterprise",
    "source": "shared-workspace",
    "bizDocumentId": "local-ragflow-document-id",
    "datasetMappingId": "local-dataset-id",
    "fileBlobId": "local-blob-id",
    "ownerUserId": "upload-user-id",
    "enterpriseId": "enterprise-id",
    "sharedFolderId": "shared-folder-id",
    "orgUnitIds": [],
    "visibilityType": "enterprise_all",
    "allowedUserIds": [],
    "allowedOrgUnitIds": [],
    "allowedRoleIds": [],
    "permissionGroupIds": [],
    "permissionVersion": 1,
    "path": "研发部/API设计文档.md",
    "filename": "API设计文档.md",
    "isDeleted": false,
    "updatedAt": "2026-06-02T00:00:00+08:00"
  }
}
```

### 8.4 MVP 使用策略

- 上传 RagFlow 时写入 metadata。
- retrieve 仍优先限定 `document_ids`。
- 权限校验仍由 EvoMind 完成。
- metadata 主要用于来源标识、未来扩展和结果审计。
- 如果 RagFlow 当前版本不支持上传或更新 metadata，需要在 Phase 0 spike 中确认替代方式；本地映射表必须保留完整 metadata 快照。

## 9. 数据库表设计

### 9.1 `ragflow_datasets`

用途：记录用户/企业到 RagFlow dataset 的映射。

字段建议：

```text
id
scope: personal | enterprise
userId
enterpriseId
ragflowDatasetId
name
status: active | disabled | failed
graphStatus: idle | queued | running | done | failed
graphProgress
graphProgressMsg
lastGraphRunAt
errorMessage
createdAt
updatedAt
isDeleted
```

约束：

```text
scope = personal 时 userId 必填，enterpriseId 可为空；enterpriseId 为空表示默认个人空间，不为空表示组织上下文下的个人空间
scope = enterprise 时 enterpriseId 必填，userId 为空
personal 默认空间按 userId 唯一
personal 组织空间按 userId + enterpriseId 唯一
enterprise dataset 按 enterpriseId 唯一
ragflowDatasetId 建索引
```

PostgreSQL partial unique index：

```sql
DROP INDEX IF EXISTS "ragflow_dataset_personal_uq";

CREATE UNIQUE INDEX "ragflow_dataset_personal_default_uq"
ON "ragflow_datasets"("userId")
WHERE "scope" = 'personal' AND "enterpriseId" IS NULL AND "isDeleted" = false;

CREATE UNIQUE INDEX "ragflow_dataset_personal_enterprise_uq"
ON "ragflow_datasets"("userId", "enterpriseId")
WHERE "scope" = 'personal' AND "enterpriseId" IS NOT NULL AND "isDeleted" = false;
```

### 9.2 `ragflow_file_blobs`

用途：记录同一 dataset 内真正上传到 RagFlow 的文件内容。

字段建议：

```text
id
datasetMappingId
contentHash
ragflowDocumentId
filename
mimeType
sizeBytes
refCount
status: uploading | uploaded | parsing | parsed | failed | deleting | deleted | delete_failed
parseProgress
parseProgressMsg
errorMessage
createdAt
updatedAt
```

约束：

```text
datasetMappingId + contentHash 唯一
ragflowDocumentId 建索引
refCount 不允许小于 0
```

并发要求：

- 通过唯一约束避免重复 blob。
- 通过事务和原子 update 维护 `refCount`。
- 只有成功创建 blob 的请求真正上传 RagFlow；唯一冲突的请求复用已有 blob。

### 9.3 `ragflow_documents`

用途：记录 EvoMind 业务文件到 RagFlow document/blob 的映射。

字段建议：

```text
id
datasetMappingId
fileBlobId

source: workspace | shared-workspace | chat-upload

userId
enterpriseId

sharedFolderId
parentFolderId
orgUnitId

path
filename
mimeType
sizeBytes
contentHash

ragflowDocumentId

visibilityType: owner_only | enterprise_all | org_unit | selected_users | selected_org_units | permission_group
permissionGroupId
permissionVersion

uploadStatus: pending | syncing | uploaded | failed
parseStatus: unstarted | queued | running | parsed | failed | canceled
parseProgress
parseProgressMsg

metadataSyncedAt
metadataSyncStatus
metadataErrorMessage

lastSyncedAt
errorMessage
createdAt
updatedAt
isDeleted
```

唯一约束建议：

个人知识库：

```text
datasetMappingId + source + userId + path + isDeleted
```

企业共享知识库：

```text
datasetMappingId + source + enterpriseId + path + isDeleted
```

如果后续有稳定 fileId，优先用 fileId 做业务唯一键，而不是 path。

### 9.4 `ragflow_sync_jobs`

用途：处理异步同步任务、失败重试和补偿。

字段建议：

```text
id
jobType: upload | update | delete | parse | refresh_status | metadata_update | backfill
datasetMappingId
documentMappingId
fileBlobId
source
path
payload
status: pending | running | success | failed | canceled
retryCount
maxRetryCount
nextRetryAt
lockedAt
lockedBy
errorMessage
createdAt
updatedAt
```

用途：

- 文件上传同步。
- 文件内容更新同步。
- 文件删除同步。
- RagFlow parse 触发。
- 解析状态刷新。
- metadata 更新。
- 历史文件 backfill。
- 失败重试。

### 9.5 `ragflow_document_permissions`

用途：未来更细粒度权限扩展。MVP 可以建表但不实现完整逻辑，也可以只在设计中保留，等部门/组织能力明确后落地。

字段建议：

```text
id
documentMappingId
enterpriseId
subjectType: enterprise | org_unit | user | role | permission_group
subjectId
permission: read | write | admin
permissionVersion
createdAt
updatedAt
```

### 9.6 `ragflow_message_citations`

用途：保存聊天回答引用来源。MVP 可暂缓，若前端需要刷新后仍展示引用来源，则需要落地。

字段建议：

```text
id
sessionId
messageId
datasetMappingId
documentMappingId
fileBlobId
ragflowDocumentId
chunkId
contentPreview
score
createdAt
```

## 10. 文件同步与去重

### 10.1 去重范围

只在同一 dataset 内去重：

```text
同一用户同一个人空间 personal dataset 内可去重
同一企业 enterprise dataset 内可去重
同一用户不同个人空间之间不去重
不同用户之间不去重
不同企业之间不去重
personal dataset 与 enterprise dataset 之间不去重
```

### 10.2 去重依据

```text
contentHash = sha256(fileBuffer)
```

同一 dataset 下 `contentHash` 相同则认为内容重复。

### 10.3 同步策略

文件操作成功后不应长时间阻塞等待 RagFlow。推荐：

1. EvoMind 文件操作成功。
2. 创建 `ragflow_sync_jobs`。
3. 返回前端文件操作结果。
4. 后端异步执行 RagFlow 上传、parse、metadata 更新。
5. 前端通过文档状态接口展示同步和解析进度。

### 10.4 删除策略

删除业务文件时：

1. 软删除 `ragflow_documents`。
2. `ragflow_file_blobs.refCount - 1`。
3. 如果 `refCount > 0`，不删除 RagFlow document。
4. 如果 `refCount = 0`，创建 delete job。
5. delete job 调用 RagFlow 删除 document。
6. 删除失败进入 `delete_failed`，允许重试。

### 10.5 更新策略

内容更新：

- 重新读取 buffer。
- 重新计算 hash。
- hash 不变：更新 document metadata 和 `lastSyncedAt`。
- hash 已存在：切换到已有 blob，调整旧 blob/new blob refCount。
- hash 不存在：创建新 blob，上传 RagFlow，触发 parse。

重命名/移动：

- 不重新上传。
- 更新本地 `path/filename`。
- 尝试更新 RagFlow metadata。
- metadata 更新失败时进入 `metadataSyncStatus = failed`，允许重试。

目录删除：

- 根据 path 前缀批量找 `ragflow_documents`。
- 逐条执行删除映射和 refCount 逻辑。

## 11. 解析状态

RagFlow 没有 Dify 风格 batch indexing-status。EvoMind 通过 document 的 `run`、`progress`、`progress_msg` 轮询。

状态映射：

| RagFlow | EvoMind |
| --- | --- |
| `UNSTART` | `unstarted` |
| `RUNNING` | `running` |
| `DONE` | `parsed` |
| `FAIL` | `failed` |

刷新策略：

- 文件树加载时只返回本地状态，不阻塞 RagFlow。
- 前端首次加载状态时执行 `list -> refresh once`，用于快速拿到本地状态并刷新一次远端进度。
- 前端当前文件树中如果存在 `workspace:个人知识库/...` 或当前组织 `shared-workspace:...` 的未完成文档，启动 10 秒低频批量刷新。
- 未完成文档定义：`uploadStatus=pending` 或 `parseStatus=queued/running`。
- 页面隐藏、未启用、未登录、文件树为空、没有未完成文档、上一轮刷新未结束时不发请求。
- 普通上传、拖拽上传、节点菜单上传、文件夹上传成功后，对成功上传的文件做短轮询，尽快拿到 pending/running 状态。
- 当前已覆盖 `SuperLobsterPage` 和 `ZclawWorkspaceSidebar` 两个前端上传入口。
- 聊天发送前，如果拖拽文件未解析完成，可触发一次状态刷新。
- 后台 job 定期刷新 `running` 文档。
- `parsed` 成功勾只在当前页面内从非 parsed 过渡为 parsed 时展示 3 秒；刷新页面或重新进入时不常驻展示。

前端展示必须区分：

- 文件上传进度：浏览器到 EvoMind。
- RagFlow 同步进度：EvoMind 到 RagFlow。
- RagFlow 解析进度：RagFlow 解析、切片、索引。

## 12. 后端模块设计

### 12.1 `RagflowClient`

建议路径：

```text
apps/api/src/zclaw/ragflow/ragflow.client.ts
```

职责：只封装 RagFlow HTTP API。

方法：

```text
createDataset(input)
uploadDocument(datasetId, file, metadata)
updateDocumentMetadata(datasetId, documentId, metadata)
deleteDocuments(datasetId, documentIds)
parseDocuments(datasetId, documentIds)
listDocuments(datasetId, query)
retrieve(input)
runGraphRag(datasetId)
traceGraphRag(datasetId)
deleteKnowledgeGraph(datasetId)
```

### 12.2 `RagflowService` 与召回展示清洗工具

建议路径：

```text
apps/api/src/zclaw/ragflow/ragflow.service.ts
apps/api/src/zclaw/ragflow-retrieval-message.ts
```

职责：业务编排。

方法：

```text
ensurePersonalDataset(userId, enterpriseId?)
findPersonalDataset(userId, enterpriseId?)
ensureEnterpriseDataset(enterpriseId)

enqueueSyncPersonalWorkspaceFile(userId, path, enterpriseId?)
enqueueSyncEnterpriseSharedWorkspaceFile(userId, enterpriseId, path)
syncPersonalWorkspaceFileChanged(userId, path, enterpriseId?)
syncEnterpriseSharedWorkspaceFileChanged(userId, enterpriseId, path)
syncPersonalWorkspacePathMoved({ userId, fromPath, toPath, enterpriseId?, entryType? })
syncEnterpriseSharedWorkspacePathMoved({ userId, enterpriseId, fromPath, toPath })
syncPersonalWorkspacePathDeleted(userId, path, enterpriseId?)
syncEnterpriseSharedWorkspacePathDeleted(enterpriseId, path)

processSyncJob(jobId)
retrySyncJob(jobId)

refreshDocumentStatus(documentMappingId, enterpriseId?)
refreshDocumentStatuses(documentMappingIds, enterpriseId?)
retryDocumentSync(documentMappingId, enterpriseId?)
refreshDatasetDocumentStatuses(datasetMappingId)

retrieveForDraggedFiles(userId, messageFiles, question)
buildRetrievalContext(chunks)
stripRagflowRetrievalContextFromUserMessage(content)
sanitizeRagflowRetrievalAssistantMessage(content)
sanitizeRagflowRetrievalDisplayMessage(role, content)

runPersonalKnowledgeGraph(userId)
runEnterpriseKnowledgeGraph(userId, enterpriseId)
refreshKnowledgeGraphStatus(datasetMappingId)
deleteKnowledgeGraph(datasetMappingId)
```

当前已落地的 sync job 类型：

```text
upload -> 上传/更新文件、内容 hash 去重、触发 parse、写入或更新 document mapping
metadata_update -> 重命名/移动/同 blob 映射变化后的 RagFlow document name/metadata 同步
delete -> blob refCount 归零后的 RagFlow document 异步删除
retrieval_audit -> 记录拖拽文件召回的 selected/ignored files、rewrite、retrieve request、chunks 和错误
```

召回 prompt 与展示清洗语义：

```text
buildRetrievalContext -> 只生成“知识库文件内容/资料”中性上下文，不暴露 RagFlow、定向召回、召回结果、score
stripRagflowRetrievalContextFromUserMessage -> 兼容旧 RagFlow 前缀和新知识库前缀，只保留用户原始问题
sanitizeRagflowRetrievalAssistantMessage -> 仅在检测到内部泄漏话术时，把“召回片段/召回结果/RagFlow”等替换为自然表达
sanitizeRagflowRetrievalDisplayMessage -> 后端历史返回、本地快照保存和前端渲染兜底共用的展示清洗入口
```

metadata update 降级策略：

```text
如果当前 RagFlow 部署对 document config/metadata update 返回 405 或 MethodNotAllowed，
文档标记为 metadataSyncStatus=unsupported，并记录 metadataErrorMessage。
该情况不视为主同步失败，文件上传、解析、召回仍按本地 mapping 继续工作。
```

### 12.3 权限服务抽象

建议先放在 RagFlow service 内部或新增：

```text
apps/api/src/zclaw/ragflow/ragflow-permission.service.ts
```

方法：

```text
canReadPersonalKnowledgeFile(userId, fileMeta)
canReadSharedKnowledgeFile(userId, enterpriseId, fileMeta)
assertDraggedFilesInSameKnowledgeScope(userId, files)
```

MVP：

- personal：校验 `userId` 与当前个人空间 `enterpriseId/null`。
- enterprise：复用企业 active member 与现有 shared-workspace read 权限。

未来：

- 接入部门。
- 接入组织。
- 接入权限组。
- 接入指定用户共享。
- 接入文件夹继承权限。

## 13. 后端 API 设计

所有接口挂在 `JwtAuthGuard` 和现有 zclaw 企业上下文体系下。

### 13.1 Dataset 状态

```http
GET /api/zclaw/ragflow/dataset
```

用途：

- 查询当前用户 personal dataset 状态。
- 查询当前企业 enterprise dataset 状态。

### 13.2 文档状态

```http
GET /api/zclaw/ragflow/documents
```

查询参数：

```text
source=workspace | shared-workspace | chat-upload
path=个人知识库/xxx.pdf
enterpriseId=xxx
```

用途：

- 查询文件 RagFlow 同步状态。
- 查询文件解析进度。
- 查询失败原因。

### 13.3 状态刷新

```http
POST /api/zclaw/ragflow/documents/:id/status/refresh
POST /api/zclaw/ragflow/documents/status/refresh
```

用途：

- 刷新单个文件状态。
- 批量刷新当前目录文件状态。

### 13.4 同步重试

```http
POST /api/zclaw/ragflow/documents/:id/retry
```

用途：

- 重试上传。
- 重试解析。
- 重试 metadata 同步。
- 重试删除。

### 13.5 指定路径同步

```http
POST /api/zclaw/ragflow/sync/path
```

请求：

```json
{
  "source": "workspace",
  "path": "个人知识库/xxx.pdf",
  "recursive": false
}
```

用途：

- 手动同步指定文件。
- 手动同步指定目录。
- backfill 复用。

### 13.6 拖拽文件召回调试

```http
POST /api/zclaw/ragflow/retrieval
```

请求：

```json
{
  "question": "这个文件讲什么？",
  "files": [
    {
      "source": "workspace",
      "path": "个人知识库/A.pdf"
    }
  ]
}
```

限制：

- 前端不能直接传任意 RagFlow datasetId 或 documentId。
- 后端必须通过本地映射和权限校验解析可用 `document_ids`。

### 13.7 知识图谱

```http
POST /api/zclaw/ragflow/knowledge-graph/run
GET /api/zclaw/ragflow/knowledge-graph/status
DELETE /api/zclaw/ragflow/knowledge-graph
```

用途：

- 触发个人图谱构建。
- 触发企业图谱构建。
- 查询图谱状态。
- 删除图谱。

## 14. 前端改造范围

### 14.1 API 模块

在 `apps/web/src/api/moudles/zclaw.ts` 新增：

- `listZclawRagflowDocumentStatusesApi`
- `refreshZclawRagflowDocumentStatusApi`
- `refreshZclawRagflowDocumentStatusesApi`
- `retryZclawRagflowDocumentSyncApi`
- `getZclawRagflowDatasetApi`
- `listZclawRagflowDocumentsApi`
- `syncZclawRagflowPathApi`
- `retrieveZclawRagflowApi`
- `runZclawRagflowKnowledgeGraphApi`
- `getZclawRagflowKnowledgeGraphStatusApi`
- `deleteZclawRagflowKnowledgeGraphApi`

### 14.2 文件树

文件节点展示：

- RagFlow 同步状态。
- RagFlow 解析状态。
- 解析进度。
- 失败原因。
- 最近同步时间。

失败时提供：

- 重试同步。
- 刷新状态。

文件树加载不等待 RagFlow 状态刷新。

当前已实现展示入口：

- `SuperLobsterPage`：主工作区、知识库浏览面板、聊天输入框附件。
- `ZclawWorkspaceSidebar`：admin workspace route 中的独立工作区侧边栏。

当前刷新机制：

- 首次加载执行状态 list，并对未完成文档 refresh once。
- 当前文件树存在未完成文档时每 10 秒批量刷新一次。
- 上传成功后对单文件短轮询，文件夹上传则对每个成功上传的文件短轮询。
- `parsed` 成功徽标只展示 3 秒，不在刷新页面/重新进入后常驻显示。

### 14.3 文件详情

展示：

- 是否已同步 RagFlow。
- 解析是否完成。
- 解析失败原因。
- metadata 同步状态。
- 所属 dataset。

### 14.4 聊天输入框

支持：

- 拖拽个人知识库文件。
- 拖拽企业共享知识库文件。
- 展示文件来源。
- 展示文件解析状态。
- 阻止混合知识范围文件一起发送。

发送前判断：

- 未解析完成：允许发送，但提示召回可能不完整。
- 解析失败：提示重试同步或继续普通提问。
- 无权限：禁止发送或移除该文件。

### 14.5 聊天回答引用来源

MVP 可选展示：

- 已引用文件。
- 引用片段。
- 文件路径。

如果需要刷新页面后保留引用来源，再落地 `ragflow_message_citations`。

### 14.6 知识图谱入口

个人知识库页面：

- 展示个人图谱状态。
- 提供构建、重建、刷新入口。

企业共享知识库页面：

- 展示企业图谱状态。
- 管理员提供构建、重建、删除入口。
- 普通成员只展示状态。

## 15. 知识图谱设计

图谱按 dataset 维度管理。

个人图谱：

```text
personal dataset -> GraphRAG
```

企业图谱：

```text
enterprise dataset -> GraphRAG
```

状态来源：

```text
RagFlow trace_graphrag progress/progress_msg/task_type
```

保存到：

```text
ragflow_datasets.graphStatus
ragflow_datasets.graphProgress
ragflow_datasets.graphProgressMsg
```

MVP：

- 手动触发构建。
- 文档变更后提示可能需要重建。
- 不自动重建。

风险：

- 企业图谱可能暴露普通成员无权访问文件中的实体和关系。
- MVP 建议限制企业图谱查看和构建权限，只开放给企业 admin/owner 或拥有完整企业知识库权限的用户。

## 16. 降级策略

### 16.1 文件操作

EvoMind 文件上传、编辑、删除成功后，不应因 RagFlow 暂时不可用而整体失败。

策略：

- 文件操作成功后创建 sync job。
- RagFlow 失败则标记同步失败。
- 前端展示失败状态并允许重试。

### 16.2 聊天召回

如果用户拖拽知识库文件，但 retrieve 失败：

- 不应直接中断整个 conversation。
- 可以提示“知识库召回失败，本次将不使用该文件上下文回答”。
- 是否继续调用 conversation 由产品决定；MVP 建议继续，但在 prompt 中不注入伪造上下文。

如果文档尚未解析完成：

- 允许发送。
- 提示“文档仍在解析中，召回结果可能不完整”。

## 17. 实施计划

### Phase 0：RagFlow API Spike

状态：已完成基础 API spike，当前实现已能创建 dataset、上传 document、触发 parse、查询文档解析状态。

目标：验证当前部署版本 RagFlow API 能力。

确认项：

- 创建 dataset 是否可用。
- 上传 document 是否可用。
- 上传 metadata 是否可用。
- 更新 metadata 是否可用。
- 触发 parse 是否可用。
- 查询 parse 状态是否可用。
- retrieve 是否支持 `document_ids` 限定。
- retrieve 是否支持 metadata filter。
- GraphRAG run/trace/delete 是否可用。
- 删除 document 后是否不再被召回。

输出：

- 一份简短 spike 记录。
- 确认 RagFlow request/response 示例。
- 标记与本设计不一致的接口差异。

### Phase 1：数据库与基础 Client

状态：已完成。已新增 RagFlow Prisma models、migration、client、dataset 创建与本地映射。personal dataset 已按 `userId + enterpriseId/null` 隔离。

任务：

- 新增 Prisma models：
  - `RagflowDataset`
  - `RagflowFileBlob`
  - `RagflowDocument`
  - `RagflowSyncJob`
- 新增 migration。
- 实现 `RagflowClient`。
- 实现 dataset 创建与本地映射。
- 增加环境变量模板。

验收：

- 能为用户当前个人空间创建 personal dataset。
- 同一用户默认空间复用默认 personal dataset。
- 同一用户不同组织空间创建不同 personal dataset。
- 能为企业创建 enterprise dataset。
- 重复 ensure 不重复创建 dataset。
- RagFlow 错误可记录。

建议测试：

- `apps/api/src/zclaw/ragflow/ragflow.client.test.ts`
- `apps/api/src/zclaw/ragflow/ragflow.service.test.ts`

### Phase 2：异步任务与文档上传同步

状态：已完成 MVP 主链路。个人知识库上传、企业共享知识库上传均会创建本地 pending document 映射并提交 sync job；后台 job 上传 RagFlow、触发 parse，并按 `datasetMappingId + contentHash` 去重。

任务：

- 实现 `ragflow_sync_jobs` 创建与锁定执行。
- 实现文件 hash 计算。
- 实现 fileBlob 去重。
- 实现 document 映射。
- 接入个人知识库上传后的 sync job。
- 接入企业共享知识库上传后的 sync job。
- 触发 RagFlow parse。
- 写入 metadata。

验收：

- 上传文件后能同步到 RagFlow。
- 同一 dataset 内重复文件不重复上传。
- 不同个人空间/不同组织空间不复用 blob。
- 本地映射可追踪业务文件路径。
- RagFlow 不可用时文件上传主流程不失败。

### Phase 3：解析状态展示

状态：已完成 MVP 展示与刷新。`SuperLobsterPage` 和 `ZclawWorkspaceSidebar` 两个上传入口均已覆盖上传后短轮询、首次刷新、10 秒低频刷新、失败重试、解析进度徽标展示。

任务：

- 实现状态刷新接口。
- 实现状态映射。
- 前端文件树展示同步/解析状态。
- 前端失败重试。
- 聊天附件展示解析状态。

验收：

- 用户能看到文件解析进度。
- 失败文件可重试。
- 文件树加载不被 RagFlow 阻塞。
- 解析完成绿色勾只在当前页面过渡为完成时短暂展示 3 秒，刷新或重新进入不常驻。

### Phase 4：完整文件生命周期

状态：已完成 MVP 生命周期同步。个人知识库和企业共享知识库的编辑、重命名/移动、删除、目录删除已接入 RagFlow mapping、blob 引用计数、metadata update 和异步删除流程。

任务：

- 接入文件编辑。
- 接入重命名。
- 接入移动。
- 接入删除。
- 接入目录删除。
- 实现 refCount 增减。
- 实现 RagFlow document 异步删除。
- 实现 metadata 更新。

验收：

- 内容 hash 不变时复用原 blob，不重复上传。
- 内容 hash 变化时切换 blob，旧 blob `refCount` 递减，新 blob `refCount` 递增。
- 重命名/移动只更新本地 mapping、RagFlow document name 和 metadata，不重复上传。
- 从个人知识库移出时软删除 mapping；移入个人知识库时提交 upload sync job。
- 删除最后引用时异步删除 RagFlow document。
- 目录删除能处理所有子文件 mapping。
- RagFlow metadata update 不支持时标记 `metadataSyncStatus=unsupported`，不阻断文件生命周期主流程。

### Phase 5：拖拽文件召回

状态：已完成 MVP 拖拽文件定向召回。`retrieveForDraggedFiles` 已接入主聊天链路前置流程，并通过本地 mapping 和权限校验生成受限 `dataset_ids/document_ids`。

任务：

- 实现 `retrieveForDraggedFiles`。
- 支持个人知识库文件召回。
- 支持企业共享知识库文件召回。
- 支持同一企业上下文内个人知识库文件 + 企业共享知识库文件混合定向召回。
- 实现权限校验。
- 实现 `document_ids` 限定。
- 实现低信息问题 query rewrite。
- 实现 `retrieval_audit` job。
- 接入 `ZclawService.streamMessage(...)` conversation 前置流程，并注入中性的知识库内容上下文。
- 实现历史返回和前端渲染的用户可见文本清洗。

验收：

- 普通聊天不触发 RagFlow。
- 拖拽个人文件只检索当前消息选中的个人文件。
- 拖拽企业文件只检索当前消息选中的企业共享文件。
- 同一企业上下文内 personal + shared 文件可一起召回，但仍限定到选中的 `document_ids`。
- 普通聊天附件、非知识库路径、未同步或缺少 `ragflowDocumentId` 的文件会被忽略。
- shared 文件缺少 active enterprise context 时拒绝召回。
- 无权限文件不可召回。
- query rewrite 失败时回退原始问题。
- retrieve 失败时主聊天降级为普通聊天，不注入伪造上下文。
- 注入 prompt 不包含 `RagFlow`、`定向召回`、`召回结果`、`score`，资料块使用 `[资料 n]`。
- 历史返回和前端展示不会暴露增强 prompt；用户消息只展示原始问题。
- 助手消息出现“根据召回片段”等内部话术时展示为自然表达；普通聊天中主动讨论 RagFlow 不被误改。
- “这个文件讲什么”可以正确召回。

### Phase 6：知识图谱

任务：

- 实现个人图谱构建。
- 实现企业图谱构建。
- 实现图谱状态刷新。
- 前端展示图谱状态。
- 企业图谱操作加权限控制。

验收：

- 用户可构建个人图谱。
- 企业管理员可构建企业图谱。
- 普通成员不能删除或重建企业图谱。
- 图谱进度可见。

### Phase 7：补偿任务与稳定性

任务：

- 历史文件 backfill。
- 失败任务重试。
- 批量状态刷新。
- 基础审计日志。
- RagFlow 不可用降级。
- 权限变更后的 metadata 更新机制。

验收：

- 可以安全补同步历史知识库。
- 失败任务可追踪、可重试。
- 权限变更后不会召回无权限文件。

## 18. MVP 范围

MVP 优先实现：

- 一个用户在每个个人空间一个 personal dataset（默认空间 `enterpriseId=null`，组织空间 `enterpriseId=组织 id`）。
- 一个企业一个 enterprise dataset。
- 个人知识库文件同步 RagFlow。
- 企业共享知识库文件同步 RagFlow。
- 同 dataset 内文件内容去重。
- 文件解析状态展示。
- 拖拽知识库文件时定向召回。
- 普通聊天不触发 RagFlow。
- 低信息问题 query rewrite。
- 基础权限校验。
- RagFlow metadata 写入。
- 个人/企业图谱手动构建和状态展示。

暂缓实现：

- 所有聊天问题默认检索知识库。
- 跨企业、多企业、默认个人空间 + 企业共享知识库的混合召回。
- 部门级权限完整实现。
- 指定用户共享完整实现。
- 权限组完整实现。
- GraphRAG 与 Vector 混合召回。
- 图谱节点/边按 document 权限过滤。
- 大规模 backfill 运维页面。
- 聊天引用来源持久化。

## 19. 测试计划

### 后端单元测试

- dataset 创建与复用。
- personal 默认空间/组织空间/enterprise dataset 唯一性。
- personal 状态查询、刷新、重试按当前 `enterpriseId/null` 空间隔离。
- document 去重。
- refCount 增减。
- 编辑 hash 不变时不重复上传。
- 编辑 hash 变化时切换 blob/refCount，并删除旧 blob 最后引用。
- 重命名只更新 mapping/name/metadata，不重复上传。
- 移出个人知识库软删除 mapping，并在最后引用时删除 RagFlow document。
- 删除目录处理所有子文件 mapping。
- 企业共享知识库重命名使用 enterprise dataset 并同步 metadata。
- sync job 状态流转。
- parse 状态映射。
- retrieval 参数生成。
- 低信息 query rewrite。
- `retrieveForDraggedFiles` 跳过普通聊天附件。
- 未同步或缺少 `ragflowDocumentId` 的知识库文件不触发 RagFlow。
- 同一企业上下文下 personal + shared 文件可一起召回，且请求同时限定 `dataset_ids` 与 `document_ids`。
- shared 文件缺少企业上下文时拒绝召回。
- query rewrite 失败时回退原始问题。
- `buildRetrievalContext` 生成中性知识库上下文，不包含 `RagFlow`、`定向召回`、`召回结果`、`score`，并使用 `[资料 n]`。
- 用户消息清洗兼容旧 RagFlow 前缀和新知识库前缀，只返回 `用户原始问题`。
- 助手消息清洗将“根据召回片段”等内部话术替换为自然表达。
- 普通助手消息中单独讨论 RagFlow 时不被误替换。
- graph 状态映射。
- RagFlow client 错误处理。

### 后端集成测试

- 上传个人知识库文件后创建 sync job。
- 默认个人空间上传写入 `enterpriseId=null`。
- 组织个人空间上传写入当前组织 `enterpriseId`。
- 上传企业共享知识库文件后创建 sync job。
- 同一 dataset 内重复文件不会重复上传 RagFlow。
- 不同个人空间上传同内容文件会进入各自独立 dataset。
- 删除文件后 RagFlow document 引用正确变化。
- 普通聊天不调用 retrieval。
- 拖拽文件聊天调用 retrieval。
- 拖拽召回只使用后端解析出的 `document_ids`，不能扩大到整个 dataset。
- RagFlow retrieve 失败时聊天链路降级为普通聊天。
- 历史详情和分页历史返回前会清洗用户增强 prompt 与助手内部泄漏话术。
- 企业权限限制仍生效。

### 前端测试

- 文件树状态展示。
- `SuperLobsterPage` 和 `ZclawWorkspaceSidebar` 两个上传入口均展示 RagFlow 状态。
- 存在 pending/queued/running 状态时 10 秒低频刷新。
- 无未完成状态、页面隐藏、文件树为空时不轮询。
- 前端展示层兜底清洗旧/新增强 prompt。
- 前端展示层兜底清洗“根据召回片段”等内部话术，但不误伤普通 RagFlow 讨论。
- 上一轮刷新未完成时不并发刷新。
- 文件夹上传后点开目标文件夹能看到每个文件的 RagFlow 解析进度。
- parsed 成功勾只短暂展示 3 秒，刷新或重新进入后不常驻。
- 失败重试按钮。
- 混合来源文件发送拦截。
- 聊天附件解析状态。
- 图谱状态展示。
- 企业图谱操作权限展示。

### 手工验收

- 用户 A 上传个人文件，用户 B 不可见、不可检索。
- 同一用户在默认空间、组织 A、组织 B 上传个人知识库文件，三处 RagFlow dataset、document 状态互不串扰。
- 企业成员上传共享文件，同企业成员可拖拽召回。
- 非企业成员不可召回企业文件。
- 同一企业上下文下，组织个人知识库文件与该企业共享知识库文件可以一起拖拽召回。
- 同一 dataset 内重复文件不重复上传 RagFlow；不同个人空间上传同内容文件不复用 blob。
- 编辑文件内容不变时不重复上传；内容变化时切换 blob 并释放旧引用。
- 重命名、移动、删除、目录删除后 RagFlow mapping 与远端 document 引用保持一致。
- 上传知识库文件后，页面无需手动刷新即可在约 10 秒内看到 RagFlow 解析进度变化。
- 文件夹上传后点开对应文件夹，能看到其中各文件的 RagFlow 解析进度。
- “这个文件讲什么”能基于指定文件回答。
- 图谱构建进度可见。

## 20. 风险与约束

### 权限风险

未来如果支持默认知识库检索，不能直接对整个企业 dataset 无条件 retrieve。必须先计算可访问 documentIds，retrieve 后还要做二次权限校验。

### Metadata 能力不确定

RagFlow metadata 是否支持上传、更新和 retrieve 阶段过滤，需要 Phase 0 验证。即使支持 metadata filter，也不能替代 EvoMind 权限校验。

### 图谱泄露风险

企业图谱可能暴露无权限文件中的实体和关系。MVP 阶段建议限制企业图谱查看、构建、删除权限。

### 同步一致性风险

文件上传、更新、删除与 RagFlow 同步之间是最终一致。必须通过 sync job、状态字段、失败重试保证可恢复。

### 去重并发风险

相同文件并发上传时，必须通过唯一约束和事务避免重复上传、refCount 错乱和孤儿 document。

## 21. 最终结论

推荐设计：

```text
RagFlow 作为知识引擎；
EvoMind 作为权限主系统；
个人知识库按 userId + enterpriseId/null dataset 管理；
企业共享知识库按企业 dataset 管理；
MVP 只对拖拽到聊天框的知识库文件做定向召回；
召回必须限定 document_ids；
普通聊天不触发 RagFlow；
上传文档时写入 metadata，为未来权限过滤和图谱过滤预留空间；
共享知识库未来组织层级权限不通过拆分 dataset 实现，而通过 EvoMind 权限体系、文档映射、metadata 和权限快照扩展实现。
```

MVP 应优先保证：

```text
文档能同步；
状态能展示；
重复文件能去重；
拖拽文件能定向召回；
权限不越界；
图谱能手动构建；
后续部门级权限有扩展空间。
```
