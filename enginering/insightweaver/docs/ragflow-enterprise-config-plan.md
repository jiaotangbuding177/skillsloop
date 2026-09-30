# EvoMind RagFlow 企业配置与容量管控实施计划

## 0. 与 ragflow-v2 的关系

本文档是 [`docs/ragflow-v2.md`](./ragflow-v2.md) 的补充实施计划，不替代 v2 设计。

`ragflow-v2.md` 已经定义并落地了 RagFlow 基础接入主链路，包括 dataset/document/blob/job 映射、异步同步、上传后 parse、状态刷新、失败重试、文件生命周期同步、拖拽知识库文件定向召回，以及知识图谱入口的后续方向。

本文档只补充后续企业化配置能力：

- 支持超级管理员按企业配置 RagFlow URL、API Key 和容量上限。
- 默认空间不引入新的“租户”概念，而是视为一个特殊企业，企业 ID 固定为 `-1`。
- 用户当前工作空间为默认空间时，读取 `enterpriseId=-1` 的 RagFlow 配置。
- 用户当前工作空间为真实企业时，读取该真实企业 ID 的 RagFlow 配置。
- 默认空间的 RagFlow 本地映射也应使用 `enterpriseId=-1`，避免默认空间上传知识库文件时因为缺少企业 ID 而无法创建 dataset 或同步到 RagFlow。
- 禁止 RagFlow 环境变量兜底。数据库没有配置，就代表当前空间 RagFlow 不可用。

这是一个长任务。原因是它会影响数据库配置模型、RagFlow client 调用方式、上传同步链路、聊天召回链路、知识图谱入口、超级管理员后台、容量统计、测试和历史配置迁移。因此后续实施必须按 Phase 分阶段推进。

## 1. 核心结论

### 1.1 不引入租户概念

系统仍然只讨论“企业 RagFlow 配置”。默认空间只是一个特殊企业，固定企业 ID 为：

```text
-1
```

后续文档、API、后台页面和判断逻辑都应使用“企业配置”口径，不引入 tenant、租户配置、默认租户等新概念，避免和当前组织/企业模型混淆。

### 1.2 当前工作空间决定读取哪份配置

RagFlow 配置读取规则：

```text
当前工作空间 = 默认空间   -> 读取 enterpriseId = "-1" 的 RagFlow 配置
当前工作空间 = 真实企业   -> 读取 enterpriseId = 当前企业 id 的 RagFlow 配置
```

注意：

- 默认空间中的个人知识库需要从 v2 的 `RagflowDataset.enterpriseId = null` 调整为 `RagflowDataset.enterpriseId = "-1"`。
- 默认空间中的共享知识库如果会同步 RagFlow，对应的 dataset、document、blob、job 关联也必须使用 `enterpriseId="-1"`。
- 真实企业中的组织个人知识库仍然沿用 v2 的数据语义：`RagflowDataset.enterpriseId = 当前企业 id`。
- 企业共享知识库仍然沿用 v2 的数据语义：`scope=enterprise + enterpriseId=当前企业 id`。
- `enterpriseId="-1"` 不只是配置查询 ID，也应成为默认空间 RagFlow 同步链路里的企业 ID。这样默认空间和真实企业在 RagFlow dataset 创建、容量统计、状态查询、重试和知识图谱同步时都使用一致的企业 ID 口径。

### 1.3 禁止环境变量兜底

后续实现必须移除代码中所有 RagFlow URL、Key 的环境变量兜底读取。

禁用目标包括但不限于：

```text
RAGFLOW_BASE_URL
RAGFLOW_API_KEY
RAGFLOW_DEFAULT_EMBEDDING_MODEL
RAGFLOW_DEFAULT_CHUNK_METHOD
RAGFLOW_DEFAULT_PARSER_CONFIG_JSON
```

原则：

- RagFlow URL 和 API Key 只能来自数据库中的企业 RagFlow 配置。
- 如果当前工作空间没有配置 RagFlow，则 RagFlow 能力就是不可用。
- 即使环境变量仍然存在，也不能让 RagFlow 自动启用。
- 后续 env 示例文件中的 RagFlow 环境变量应删除或明确标记为历史方案。

### 1.4 RagFlow 不可用时主链路不失败

RagFlow 是增强能力，不是 EvoMind 文件系统的必要依赖。

当当前空间没有 RagFlow 配置、配置被停用、配置不完整或连接不可用时：

- 用户上传个人知识库文件仍然应保存到 EvoMind 文件系统。
- 用户上传企业共享知识库文件仍然应保存到 EvoMind 文件系统。
- 不创建 RagFlow dataset/document/blob/sync job。
- 不进入 RagFlow 上传、解析、状态刷新流程。
- 拖拽文件到对话框时不走 RagFlow 召回检索。
- “同步到知识图谱”按钮不展示，或置灰并展示友好提示。

当当前空间 RagFlow 配置可用但本次写入会导致容量超限时：

- 新上传知识库文件仍然应保存到 EvoMind 文件系统，但不再提交到 RagFlow。
- 更新已经在 RagFlow 中的同一个文件时，也必须重新做容量检查；如果更新后的文件会让总容量超限，则不提交 RagFlow 更新同步。
- 已经成功同步在 RagFlow 中的历史文件仍然可以用于问答召回。容量不足不是关闭检索能力，而是限制新增或变大的同步写入。
- “同步到知识图谱”按钮应置灰并展示容量不足提示，避免触发新的 RagFlow 写入。

## 2. RagFlow 容量接口结论

当前阶段没有确认 RagFlow 官方 API 提供“某个 dataset 总字节大小”的直接汇总接口。

已知可行方向：

- RagFlow dataset 列表通常更偏向文档数、chunk 数、token 数等摘要信息，不应假设其一定提供总字节大小。
- RagFlow document 列表若返回单文档 `size`，可作为后续低频对账依据。
- 实时容量限制必须由 EvoMind 本地数据库强约束，不依赖 RagFlow 远端临时查询。

本系统容量计算建议：

```text
当前已用容量 = 当前企业配置范围内，所有未删除 RagFlowFileBlob 的 sizeBytes 按唯一 blob 汇总
```

原因：

- v2 已经在同一个 dataset 内做内容去重，多个业务文件可能复用同一个 `RagflowFileBlob`。
- 按 `RagflowDocument` 业务映射累加会重复计费。
- 按唯一 blob 统计更接近实际传给 RagFlow 的存储占用。

默认空间容量口径：

```text
enterpriseId = "-1" 配置的容量
= 所有默认空间用户个人知识库 RagFlow blob 总和
+ 默认空间共享知识库 RagFlow blob 总和
```

默认空间的 personal dataset、默认空间共享知识库 dataset 以及对应 document/blob/job 的本地映射都应写入 `enterpriseId="-1"`，而不是 `null`。这能让默认空间 RagFlow 能力和真实企业空间保持同一套配置读取、容量统计、状态查询和重试逻辑。

真实企业容量口径：

```text
enterpriseId = 当前企业 id 配置的容量
= 该企业下组织个人知识库 RagFlow blob 总和
+ 该企业共享知识库 RagFlow blob 总和
```

后续如果需要和 RagFlow 远端对账，可增加后台“刷新远端用量”功能，分页读取 RagFlow documents 并汇总远端 size。但该功能只用于巡检、告警或修复，不作为上传前实时容量判断的唯一来源。

## 3. 分阶段实施计划

### Phase 0：文档与现状确认

目标：

- 只完成本文档。
- 明确本阶段不修改代码、不修改数据库 schema、不修改环境变量、不修改前端页面。
- 梳理 v2 已有能力和本计划新增能力的边界。

任务：

- 新增 `docs/ragflow-enterprise-config-plan.md`。
- 说明本计划与 `docs/ragflow-v2.md` 的关系。
- 明确默认空间使用 `enterpriseId="-1"` 的企业配置。
- 明确默认空间 personal dataset 和默认空间共享知识库同步 RagFlow 时，也要写入 `enterpriseId="-1"`。
- 明确不引入租户概念。
- 明确移除环境变量兜底的目标。
- 明确 Phase 1-6 的后续实施拆分。

验收：

- 文档存在且内容完整。
- 文档中明确说明“当前只落地规划文档，不执行代码实现”。
- 文档中明确说明该任务是长任务，并已经分 Phase。

### Phase 1：数据库配置模型

目标：

- 增加企业 RagFlow 配置的数据库承载能力。
- 支持真实企业 ID 和默认空间特殊企业 ID `-1`。

规划任务：

- 新增 Prisma 模型，例如 `EnterpriseRagflowConfig`。
- 建议字段：

```text
id
enterpriseId
baseUrl
apiKeyEncrypted
apiKeyMask
status
quotaBytes
healthStatus
lastHealthCheckAt
lastUsageReconciledAt
createdAt
updatedAt
isDeleted
```

- `enterpriseId` 唯一，允许真实企业 ID，也允许 `-1`。
- 不建立 `enterpriseId -> Enterprise.id` 外键，避免 `-1` 破坏现有企业关系。
- API Key 加密复用现有企业实例配置中的 AES-GCM 模式。
- 增加 migration。
- 增加数据迁移规划：
  - 将默认空间既有 personal RagFlow dataset/document/blob/job 映射从 `enterpriseId=null` 迁移为 `enterpriseId="-1"`。
  - 如果当前系统存在默认空间共享知识库，也将其 RagFlow 映射统一迁移为 `enterpriseId="-1"`。
  - 迁移后默认空间状态查询、刷新、重试、容量统计都应只按 `-1` 过滤。

验收：

- 可以保存 `enterpriseId="-1"` 的默认空间 RagFlow 配置。
- 可以保存真实企业 ID 的 RagFlow 配置。
- 同一个 `enterpriseId` 只能有一份有效配置。
- API Key 不明文落库，只保存密文和掩码。
- 默认空间历史 RagFlow 映射可迁移到 `enterpriseId="-1"`，不会继续依赖 `null` 企业 ID。

### Phase 2：移除环境变量兜底

目标：

- RagFlow 调用不再隐式读取环境变量。
- 所有 RagFlow 请求都必须显式使用数据库配置。
- 只改变 RagFlow 调用配置来源；“无配置时上传仍成功并跳过 RagFlow”留给 Phase 3。

规划任务：

- 改造 `RagflowClient`：
  - 不再从 `ConfigService` 读取 RagFlow base URL 和 API Key。
  - 每次请求必须传入当前企业 RagFlow target。
  - target 至少包含 `baseUrl` 和解密后的 `apiKey`。
- 全仓搜索并移除 RagFlow 环境变量读取点。
- 处理企业级 dataset 默认配置：
  - Phase 1 已新增 `embeddingModel`、`chunkMethod`、`parserConfig`、`permission`、`parseType`、`pipelineId` 字段。
  - 创建 RagFlow dataset 时优先使用数据库中的企业配置字段。
  - 字段为空时使用代码内置默认值，例如 `chunkMethod=naive` 和当前硬编码 `parserConfig`。
  - 字段为空不表示读取环境变量，后续运行时绝不读取 `RAGFLOW_DEFAULT_*` 或 `RAGFLOW_DEFAULT_PERMISSION`。
  - `pipelineId` 有值时走 pipeline 模式；无值时使用 `chunkMethod + parserConfig`。
- 更新 env 示例文件和文档：
  - 删除 RagFlow 环境变量。
  - 或明确标记为历史配置，后续不会生效。

验收：

- 数据库没有配置时，RagFlow 能力不可用。
- 即使机器上存在 RagFlow 环境变量，也不会启用 RagFlow。
- 数据库有配置且状态 active 时，RagFlow 正常可用。

### Phase 3：上传同步与容量控制

目标：

- 上传知识库文件时，按当前工作空间读取对应企业 RagFlow 配置。
- 无配置时只保存 EvoMind 文件，不进入 RagFlow 同步链路。
- 容量检查不通过时限制新增或变大的 RagFlow 写入，但不影响已经同步文件的后续召回。

规划任务：

- 增加统一能力判断方法，例如：

```text
resolveRagflowCapabilityForCurrentSpace(...)
```

- 判断当前企业 ID：

```text
默认空间 -> "-1"
企业空间 -> 当前企业 id
```

- 默认空间 RagFlow 映射写入规则：
  - 默认空间 personal dataset 创建时，`RagflowDataset.enterpriseId` 写入 `-1`。
  - 默认空间个人知识库 document/blob/job 映射写入 `enterpriseId=-1`。
  - 默认空间共享知识库如果同步 RagFlow，也写入 `enterpriseId=-1`。
  - 不再让默认空间 RagFlow 同步链路通过 `enterpriseId=null` 进入 dataset 创建、同步或容量统计。
- 上传前检查：
  - 是否存在 active RagFlow 配置。
  - `baseUrl` 和 API Key 是否完整。
  - 当前已用容量是否小于配置上限。
  - 本次文件大小加入后是否超过配置上限。
- 更新前检查：
  - 如果文件已经同步到 RagFlow，更新内容时要比较旧 blob 和新文件大小。
  - 当新文件会新增 blob 或使实际占用增加时，必须检查更新后的总容量。
  - 如果更新后的文件会导致容量超限，则 EvoMind 文件内容可以按产品决策保存，但不得提交 RagFlow upload/update sync job。
- 无配置、disabled、配置不完整、容量检查不通过时：
  - 不创建 RagFlow dataset。
  - 不创建 RagFlow document mapping。
  - 不创建 RagFlow file blob。
  - 不创建 RagFlow sync job。
  - 文件上传主流程继续成功。
- 对更新同一个已同步文件：
  - 如果更新后不增加实际占用，或替换后的总容量仍未超过上限，可以继续提交 RagFlow 更新同步。
  - 如果更新后会产生更大的新 blob 并导致总容量超限，则不提交 RagFlow 更新同步。
- 对已经在 RagFlow 的文件：
  - 容量不足不影响已有 `ragflowDocumentId` 的召回。
  - 容量不足只阻止新的上传、重新上传、内容变更同步和知识图谱写入。
- 配置可用且容量足够时：
  - 沿用 v2 的 dataset/document/blob/job 同步机制。

并发策略：

- MVP 至少做上传前本地数据库检查。
- 如果需要强约束，应在事务内增加容量占用记录或锁定配置行，避免多个并发上传同时通过检查后突破容量。
- 若 Phase 3 暂不实现强并发占用，必须在代码注释和测试说明中标记为后续风险。

验收：

- 默认空间读取 `enterpriseId="-1"` 配置。
- 默认空间创建 personal dataset 时写入 `enterpriseId="-1"`，不会因为企业 ID 为空导致 dataset 创建失败。
- 默认空间共享知识库上传同步 RagFlow 时写入 `enterpriseId="-1"`。
- 真实企业空间读取真实企业 ID 配置。
- 无配置时文件能上传成功，但不会进入 RagFlow。
- 新上传文件导致容量超限时，文件能上传成功，但不会进入 RagFlow。
- 容量不足时更新同一个已同步文件，如果新文件会导致容量超限，不提交 RagFlow 更新同步。
- 更新同一个已同步文件时，如果更新后仍未超过容量上限，可以继续提交 RagFlow 更新同步。
- 容量不足时，已经同步在 RagFlow 的历史文件仍可召回。
- 容量充足时沿用 v2 同步流程。

### Phase 4：召回与知识图谱降级

目标：

- RagFlow 不可用时，聊天召回和知识图谱入口都要清晰降级。
- 后端必须兜底，前端只做体验提示。

规划任务：

- 拖拽知识库文件到对话框时：
  - 当前空间 RagFlow 无配置或 disabled：不调用 retrieve。
  - 当前空间容量不足：不影响已同步文件 retrieve；只要文件已有可用 `ragflowDocumentId` 且权限校验通过，仍可召回。
  - 文件没有 RagFlow mapping 或 `ragflowDocumentId`：沿用 v2 行为，忽略该文件。
  - 没有可用知识库文件时，直接走普通聊天。
- “同步到知识图谱”右键入口：
  - 无配置时不展示，或置灰并提示：“暂未开通该服务”。
  - 容量不足时置灰并提示：“企业大脑空间不足，请联系管理员扩容”。
  - 配置可用且容量充足时，允许进入现有或后续知识图谱同步流程。
- 状态轮询：
  - 对没有 RagFlow mapping 的文件不发起 RagFlow 状态轮询。
  - 对当前空间 RagFlow 不可用的情况不启动解析状态刷新。

验收：

- 无配置时拖拽文件聊天不走 RagFlow 召回。
- 容量不足时，已同步文件拖拽聊天仍可走 RagFlow 召回。
- 容量不足时，未同步或更新后未能同步的文件不会被召回。
- 知识图谱按钮在无配置或容量不足时有明确提示。
- 后端不会因为前端绕过限制而调用 RagFlow。

### Phase 5：超级管理员后台

目标：

- 超级管理员可以在可视化后台维护默认空间和真实企业的 RagFlow 配置。
- 后台页面需要对管理员友好，不暴露裸字节、不要求直接理解未说明的 JSON 字段。
- 配置页面即使没有任何 RagFlow 配置，也必须能列出默认空间和所有真实企业，方便管理员直接进入编辑。

规划任务：

- 管理后台新增“企业 RagFlow”入口。
- 管理后台左侧导航也应增加“企业 RagFlow”入口，仅平台超级管理员可见。
- 页面固定支持默认空间配置：

```text
企业 ID：-1
展示名称：默认空间
```

- 页面支持真实企业配置：
  - 企业名称。
  - 企业 ID。
  - RagFlow URL。
  - API Key 输入与掩码展示。
  - 状态：active/disabled。
  - 总容量上限。
  - 当前已用容量。
  - 剩余容量。
  - 连接测试。
  - 用量刷新/对账。
- UI 风格复用现有超级后台“企业实例”和“空间配额”页面。
- 仅超级管理员可操作。
- 配置列表兜底：
  - 第一行固定展示默认空间 `enterpriseId="-1"`。
  - 后续展示所有未删除真实企业。
  - 没有配置时 `baseUrl/status/quotaBytes/configId` 可以为空，但仍展示该空间行。
  - 状态和健康使用紧凑 badge 展示，避免在表格中像输入框一样撑满单元格。
  - 状态建议展示：`启用`、`停用`、`未配置`。
  - 健康建议展示：`正常`、`异常`、`未测试`。
- 配置弹窗：
  - 弹窗主体滚动，底部“取消 / 保存配置”固定在底部，不遮挡表单。
  - 必填项需要在 label 后显示红色 `*`。
  - 点击“保存配置”时统一做表单校验，缺少必填项时阻止提交，字段下方展示错误文案，并 toast 提示“请先补全必填项”。
  - `RagFlow URL` 始终必填。
  - 新建配置时 `API Key` 必填；编辑已有配置时可留空，表示不替换原 Key。
  - 选择“设置容量上限”时，容量值必填且必须大于 0。
  - Pipeline 模式下 `parse_type` 和 `pipeline_id` 必填；`parse_type` 必须是正整数，`pipeline_id` 必须是 32 位小写十六进制字符串。
- Dataset 创建参数表单：
  - `permission` 字段从可视化表单中隐藏，不让管理员直接配置。
  - 后端字段保留兼容；新建配置默认使用 `me`，编辑已有配置时保留原权限值。
  - `embeddingModel` 和 `datasetDescription` 保持可配置。
  - `datasetAvatarBase64` 字段后端保留，前端可以先不展示。
- 摄取模式表单：
  - 内置切块和 Pipeline 二选一。
  - 内置切块模式下只提交 `chunkMethod + parserConfig`，不提交 `parseType/pipelineId`。
  - Pipeline 模式下只提交 `parseType + pipelineId`，不提交 `chunkMethod/parserConfig`。
  - 切换到内置切块时清空 Pipeline 字段。
- 高级配置体验：
  - “切块与 parser 参数”默认收起，点击后展开。
  - “高级 JSON 预览/编辑”默认收起，点击后展开。
  - Pipeline 模式下提示不会提交 `chunk_method` 或 `parser_config`。

验收：

- 可以新增或编辑 `enterpriseId="-1"` 的默认空间配置。
- 可以新增或编辑真实企业 RagFlow 配置。
- 无企业、无配置时，配置页仍至少展示默认空间 `-1`。
- 有企业但未配置 RagFlow 时，配置页仍展示企业行并允许编辑。
- API Key 保存后不回显明文。
- 连接测试能更新健康状态。
- 用量展示按默认空间或企业分别计算。
- 状态和健康标签为紧凑 badge，不出现类似输入框的长条展示。
- 必填项显示红色 `*`，保存时缺失必填项会有字段级错误提示。
- Dataset 权限框在表单中不可见。
- 切块参数和高级 JSON 默认收起。

### Phase 6：测试与验收

目标：

- 覆盖默认空间、企业空间、无配置、容量不足和环境变量不兜底等关键路径。

后端测试：

- 默认空间解析为 `enterpriseId="-1"`。
- 默认空间 personal dataset 创建写入 `enterpriseId="-1"`。
- 默认空间共享知识库同步写入 `enterpriseId="-1"`。
- 真实企业解析为当前企业 ID。
- 数据库无配置时 RagFlow 不可用。
- 环境变量存在但数据库无配置时，RagFlow 仍不可用。
- 无配置时上传知识库文件不创建 RagFlow sync job。
- disabled 时上传知识库文件不创建 RagFlow sync job。
- 新上传文件导致容量超限时，不创建 RagFlow sync job。
- 容量不足时更新已同步文件，如果新内容会导致超限，不创建 RagFlow update/upload sync job。
- 更新已同步文件但不导致容量超限时，仍可创建 RagFlow update/upload sync job。
- 容量不足时已同步文件仍可被拖拽召回。
- 容量充足时沿用 v2 同步流程。
- 默认空间容量统计不串到真实企业。
- 真实企业容量统计不串到默认空间或其他企业。
- 拖拽聊天在 RagFlow 不可用时不调用 retrieve。

前端测试：

- 后台可以配置默认空间 `-1`。
- 后台可以配置真实企业。
- RagFlow 配置页在无配置时仍展示默认空间和所有真实企业。
- 状态和健康字段使用紧凑 badge 展示。
- 新建配置缺少 RagFlow URL 或 API Key 时，保存会展示字段错误并阻止提交。
- 编辑已有配置时 API Key 可留空。
- 设置容量上限时，非法容量值会展示字段错误并阻止提交。
- Pipeline 模式下缺少 `parse_type/pipeline_id` 或格式错误时，保存会展示字段错误并阻止提交。
- Dataset 权限框不展示。
- “切块与 parser 参数”和“高级 JSON 预览/编辑”默认收起，点击后可以展开。
- 无配置时知识图谱入口不展示或置灰。
- 容量不足时知识图谱入口置灰并展示正确提示。
- 无 RagFlow mapping 文件不进入状态轮询。

手工验收：

- 配置 `enterpriseId="-1"` 后，默认空间用户使用同一 RagFlow 入口。
- 默认空间个人知识库和共享知识库同步 RagFlow 时，映射里都能看到 `enterpriseId="-1"`。
- 企业 A 已配置、企业 B 未配置时，A 正常同步和召回，B 自动降级。
- 删除或停用默认空间配置后，默认空间文件上传仍成功，但不进入 RagFlow。
- 存在 RagFlow 环境变量但数据库无配置时，RagFlow 不生效。

## 4. 验收标准

最终完整实现需要满足：

- 默认空间固定使用 `enterpriseId="-1"` 的企业 RagFlow 配置。
- 默认空间 personal dataset 和默认空间共享知识库 RagFlow 映射固定写入 `enterpriseId="-1"`。
- 真实企业固定使用自身企业 ID 的 RagFlow 配置。
- 系统中不出现“租户 RagFlow 配置”的概念。
- RagFlow URL 和 API Key 不再通过环境变量兜底。
- 数据库无配置时，RagFlow 功能不可用。
- 文件上传主链路不因 RagFlow 不可用失败。
- 无配置时不创建 RagFlow 同步任务。
- 容量检查不通过时不创建 RagFlow 同步任务；更新同一个已同步文件且不导致容量超限时可以继续同步。
- 无配置时，拖拽文件聊天不走 RagFlow 召回。
- 容量不足时，已经同步在 RagFlow 中的文件仍可召回；容量不足只限制新增或变大的写入同步。
- 无配置或容量不足时，知识图谱入口有明确降级展示。
- 超级管理员可以配置默认空间 `-1` 和真实企业的 RagFlow。
- 企业 RagFlow 后台列表在无配置时仍展示默认空间和真实企业入口。
- 企业 RagFlow 后台表单对必填项、容量值和 Pipeline 参数有清晰校验提示。
- 企业 RagFlow 后台隐藏 Dataset 权限框，高级切块参数和 JSON 默认收起。

## 5. 风险与待确认

### 5.1 RagFlow 远端容量对账

当前不应依赖 RagFlow 远端实时容量接口作为上传强约束。后续仍需结合实际 RagFlow 版本确认：

- document 列表是否稳定返回 size。
- size 单位是否为字节。
- 删除、解析失败、重复上传、GraphRAG 派生数据是否计入远端存储。
- 远端统计与本地唯一 blob 统计之间允许多大误差。

建议：

- Phase 3 先以本地唯一 blob 统计做实时限制。
- Phase 5 或后续运维 Phase 增加远端对账功能。

### 5.2 并发上传强约束

如果多个大文件同时上传，单纯上传前查询可能出现并发超额。

建议：

- MVP 可以先实现上传前检查，并在文档和测试中标记风险。
- 更稳妥的实现应增加容量 reservation 或在事务内锁定企业 RagFlow 配置行。

### 5.3 历史数据迁移

当前 v2 已经存在 RagFlow 数据和环境变量配置。后续实现时需要明确迁移策略：

- 是否把现有环境变量迁移为 `enterpriseId="-1"` 的默认空间配置。
- 已经创建的默认空间 dataset/document/blob/job 是否从 `enterpriseId=null` 迁移为 `enterpriseId="-1"`。
- 已经创建的真实企业 dataset/document/blob 是否按其真实企业 ID 归入配置。
- 未配置企业的历史 RagFlow mapping 是否保留、停用、还是迁移后再启用。

### 5.4 默认空间共享知识库口径

需求中提到默认空间可以理解为企业，是因为共享空间也在一起。后续实现前需要核对当前默认空间共享知识库在代码中的具体表示：

- 如果默认空间存在共享知识库，则其 RagFlow dataset/document/blob/job 映射都应写入 `enterpriseId="-1"`，并纳入 `-1` 的配置和容量。
- 如果当前只有企业共享知识库，没有默认空间共享知识库，则 `-1` 暂只统计默认空间个人知识库。

### 5.5 容量不足与召回能力边界

容量不足的限制对象是 RagFlow 写入能力，不是已经同步数据的读取能力。

需要避免两类误判：

- 不能因为容量不足就让已经同步在 RagFlow 的文件无法问答召回。
- 不能因为是“更新同一个文件”就绕过容量检查；如果更新后的文件更大、产生新 blob 或导致实际占用增加，仍然要按更新后的总量判断是否允许同步到 RagFlow。

## 6. 当前阶段说明

本文档最初作为规划文档落地；后续已按 Phase 逐步推进数据库、后端、前端和测试实现。

后续继续实现或修正时，应保持本文档与代码一致：每个 Phase 的新增行为、交互细节、测试和手工验收结果都需要同步更新到本文档，避免 `docs/ragflow-v2.md`、本计划和实际实现之间出现偏差。
