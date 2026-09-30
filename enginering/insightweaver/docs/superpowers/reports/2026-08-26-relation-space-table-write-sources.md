# relation_* 11 张表的数据来源清单（写入管线）

> 所有视图读的是 11 张 relation_* 表；这 11 张表的内容由 **5 条投影管线 + 3 条运行记录管线** 生成。
> 核心写入入口：`RelationProjectionService.projectFact()` —— 一次调用幂等地 upsert 一组
> `relation_nodes`（两端节点）+ `relation_edges`（一条边）+ `relation_evidences`（证据），
> 靠 `identityKey` / `edgeKey` / `evidenceKey` 唯一约束去重。

## 一图看懂

```
 源数据（现有业务表 + 外部服务）                投影管线                      生成的 relation_* 表
──────────────────────────────          ────────────────                ──────────────────────
users / enterprises / memberships  ┐
departments / groups / group_members├→ ① 身份投影（identity）─────────→ nodes/edges/evidences
agent_instances / agent_configs    ┘    (system 事实)                  （组织骨架）

zclaw_sessions + zclaw_messages ─────→ ② 聊天投影（chat）────────────→ relation_session_digests
                                        ├ LLM 生成摘要                 → nodes/edges/evidences
                                        └ 摘要投影进图                   （会话/事项/产物）

OpenClaw 工作区实时文件列表 ─────────→ ③ 记忆投影（memory）───────────→ relation_memory_snapshots
（ZclawKmAgentClient 远程列举）                                        → nodes/edges/evidences
                                                                        （记忆文件）

ragflow_graph_jobs + ragflow_datasets┐
+ RAGFlow API 实时图谱（entities/    ├→ ④ RAGFlow 图谱投影 ───────────→ nodes/edges/evidences
  relations）+ ragflow_documents     ┘                                 （文档实体/关系）

relation_session_digests（已共享）────→ ⑤ 工作流推断（semantic build）─→ nodes/edges/evidences
                                        └ LLM（本地或 relation-compute） （workstream/协作/重叠）
                                        + relation_workstream_reviews
                                          （人工评审修正）

任意用户对图谱提问 ──────────────────→ 问答（ask）─────────────────────→ relation_question_history
图谱上下文 + LLM ────────────────────→ 风险分析刷新 ──────────────────→ relation_analysis_snapshots

定时扫描器（change scanner）─────────→ 增量发现 ──────────────────────→ relation_projection_jobs
（游标 = 各源表 updatedAt）                                            + relation_projection_checkpoints

管理员配置表单 ─────────────────────→ 配置保存 ──────────────────────→ relation_compute_configs
```

---

## ① 身份投影 → nodes/edges/evidences（组织骨架，factType=system）

**服务：** `relation-identity-projection.service.ts`；**任务类型：** `personal_identity` / `enterprise_identity`

### 个人空间

| 源表 | 读取字段 | 生成内容 |
|------|---------|---------|
| `users` | `id`、`status`、`isDeleted`（校验） | person 节点（identityKey=`user:<id>`，displayName="我"） |
| `zclaw_agent_instances` | `id`、`agentId`、`scope='personal'`、`status`、`toolProfile`、`createdAt`、`updatedAt` | agent 节点（`agent-instance:<id>`）+ `owns` 边；证据 sourceType=`personal_agent`，accessScope=`owner_only` |

### 企业空间

| 源表 | 读取字段 | 生成内容 |
|------|---------|---------|
| `enterprises` | `id`、`name`、`updatedAt` | enterprise 节点（`enterprise:<id>`） |
| `enterprise_departments` | `id`、`name`、`sortOrder`、`createdAt`、`updatedAt` | department 节点 + `has_department` 边 |
| `enterprise_department_groups` | `id`、`departmentId`、`name`、`sortOrder`、`createdAt/updatedAt` | department_group 节点 + `has_group` 边 |
| `enterprise_department_group_members` | `id`、`groupId`、`departmentId`、`userId`、`createdAt` | person→group 的 `member_of_group` 边 |
| `enterprise_memberships` | `id`、`userId`、`role`、`realName`、`department`、`joinedAt`、`createdAt/updatedAt` | person 节点（displayName=realName）+ `member_of` / `member_of_department` 边（properties.role） |
| `global_builtin_agent_configs` + `enterprise_builtin_agent_configs` | `id`、`isEnabled`、名称/描述类字段 | agent/skill 节点 + `offers_agent` 边 |
| `zclaw_agent_instances`（enterprise scope） | 同个人空间 | agent 节点 + 边 |

**字段映射规律：** 源记录 id → `identityKey`（如 `department:<id>`）；源名称 → `displayName`；源 `updatedAt` → 证据 `sourceVersion`；源 `createdAt` → 边 `occurredAt`。

---

## ② 聊天投影 → relation_session_digests + nodes/edges/evidences

**服务：** `chat-relation-projection.service.ts` + `RelationWorkIntelligenceService.generateSessionDigest`；**任务类型：** `chat_session`

| 源表 | 读取字段 | 用途 |
|------|---------|------|
| `zclaw_sessions` | `id`、`userId`、`isDeleted`、联 `user`（status/isDeleted）、联 `agentInstance`（`enterpriseId`、`scope` → 决定摘要归属个人还是企业空间） | 会话节点 + `participated_in` 边 |
| `zclaw_messages` | `id`、`role`（user/assistant）、`content`、`status='done'`、`isDeleted`、`createdAt`、**`updatedAt`** | 消息内容 → 送 LLM 生成摘要；每条稳定消息也生成 chat_message 证据 |

**LLM 输出写入 `relation_session_digests`：**

| 摘要字段 | 来源 |
|---------|------|
| `sourceVersion` | 消息内容计算的版本指纹（消息变了 → 摘要重新生成） |
| `generatedTitle` / `summary` | LLM 从消息全文提炼 |
| `activities` (Json) | LLM 提炼的工作事项（key/title/description/status/evidenceMessageIds） |
| `artifacts` (Json) | LLM 提炼的产物（含 variants 明细） |
| `subjects` (Json) | LLM 提炼的主题词 |
| `visibility` | 用户选择：`owner_only` / `enterprise_member`（是否共享给企业） |
| `confidence`、`model`、`promptVersion`、`language` | 生成时的元数据 |

**摘要再投影进图（projectDigest）：** activity 节点（`digest-activity:<digestId>:<key>`）+ artifact/artifact_variant 节点 + `contains_activity`、`produced`、`has_variant`、`contributes_to` 边；证据 sourceType=`chat_semantic_digest`，locator 指向 digestId/sessionId。

---

## ③ 记忆投影 → relation_memory_snapshots + nodes/edges/evidences

**服务：** `memory-projection-scanner.service.ts`（定时）+ `memory-relation-projection.service.ts`；**任务类型：** `memory_scope` / `memory_scope_delete`

| 数据源 | 读取内容 | 说明 |
|--------|---------|------|
| `zclaw_agent_instances` + `enterprise_memberships` | 投影目标（哪些实例的记忆目录要扫描） | `listExistingTargetsAfter` 按游标分批 |
| **OpenClaw Agent 工作区（实时远程）** | 经 `ZclawKmAgentClient` 列举记忆文件：`path`、`type`（root/file）、`size`、更新时间 | 不在本地数据库，来自 Agent 运行环境 |

**写入：**
- `relation_memory_snapshots`：每个文件一行（`ownerUserId` + `enterpriseOpenClawInstanceId` + `path` 唯一）；字段 `entryType`、`remoteSize`、`remoteUpdatedAt`、`lastSeenScanId`、`status`、`missingAt`（文件消失 → 标记缺失并回收图数据）
- 图：memory 节点 + 边，证据 sourceType=`memory_file`，accessScope=`owner_only`

---

## ④ RAGFlow 图谱投影 → nodes/edges/evidences

**服务：** `ragflow-graph-relation-projection.service.ts`；**任务类型：** `ragflow_graph` / `ragflow_graph_delete`
**触发：** zclaw 的 `ragflow-graph.service.ts` 在 RAGFlow 图谱构建/刷新完成时入队（第 531/785 行附近）

| 数据源 | 读取内容 | 说明 |
|--------|---------|------|
| `ragflow_graph_jobs` + `ragflow_datasets` | `readGraphProjectionSource(graphJobId)`：图谱任务状态 + 数据集归属（决定个人/企业空间） | 投影入口 |
| **RAGFlow API（实时）** | knowledge graph 的 `entities[]` / `relations[]`（实体名、关系、来源文档 id） | 图谱内容本身不存本地，每次从 RAGFlow 拉 |
| `ragflow_documents` | `id`、`ragflowDocumentId`、`path`、`filename`、`permissionVersion` | 把远端文档 id 映射回本地文档 → 决定证据的 `permissionVersion`（文档权限变更时证据可见性随之回收） |

**写入：** 实体节点（entity/document）+ `mentions` / 关系边；证据 sourceType=`ragflow_graph`，accessScope=`ragflow_document`。

---

## ⑤ 工作流推断 → nodes/edges/evidences（factType=inferred）

**服务：** `relation-work-intelligence.service.ts` 的 `rebuildEnterpriseWorkstreams` / `buildEnterpriseSemanticGraph`；**任务类型：** `enterprise_semantic_build`

| 数据源 | 读取内容 | 说明 |
|--------|---------|------|
| `relation_session_digests` | 企业内 `visibility='enterprise_member'` 且 `isCurrent` 的摘要：`activities`、`artifacts`、`subjects`、`ownerUserId`（→ 人员名） | 推断的原料：只有成员**主动共享**的摘要才进入组织分析 |
| `relation_workstream_reviews` | 历史人工评审结论（rename/merge/split/reject_*） | LLM 结果要套用人工修正 |
| LLM | 本地模型或 **relation-compute 远程**（`POST /api/internal/relation-compute/v1/complete`，配置来自 `relation_compute_configs`） | 推断工作主线、跨组协作、工作重叠 |

**写入：** workstream / business_object 节点 + `contributes_to`、`collaborates_on`（properties.collaborationReason/Confidence/Confirmed）、`overlaps_on`、`belongs_to_business_object` 边；证据 sourceType=`relation_workstream`，accessScope=`enterprise_member`。

---

## 其余 5 张运行/配置表的来源

| 表 | 写入方 | 数据来源 |
|----|--------|---------|
| `relation_projection_jobs` | 各触发点入队 | ① change scanner 增量发现；② ragflow 图谱完成/删除回调；③ 聊天会话消息完成；④ 前端发起 `enterprise_semantic_build`；字段含 `jobType`、`idempotencyKey`、`scopeType`、`ownerUserId/enterpriseId/datasetMappingId`、`sourceId/sourceVersion`、`status`、`attemptCount/maxAttempts`、`cursor/result`(Json) |
| `relation_projection_checkpoints` | `relation-projection-change-scanner.service.ts` | 定时扫描以下源表的**增量游标**：`users`、`enterprises`、`enterprise_memberships`、`enterprise_departments`、`enterprise_department_groups`、`enterprise_department_group_members`、`zclaw_agent_instances`、`global/enterprise_builtin_agent_configs`、`zclaw_sessions`、`zclaw_messages`、`ragflow_graph_jobs`。每张源表一个 key：`cursorTimestamp`/`cursorId`/`lastScanAt`/`lastSuccessAt`/`lastError`。**这就是 `zclaw_messages` 必须补 `updatedAt` 的原因** |
| `relation_memory_snapshots` | 记忆投影（见 ③） | 远程文件列表对账结果 |
| `relation_question_history` | `POST /relation-space/ask` | 用户问题 + 图谱上下文 + LLM 回答；每次问答 append 一行 |
| `relation_analysis_snapshots` | `POST /relation-space/risk-analysis/refresh` | 固定组织风险问题走问答流程后按 `enterpriseId+analysisType` upsert；`graphUpdatedAt` 取自 `relation_nodes` max(updatedAt) |
| `relation_compute_configs` | 管理端配置表单 | `baseUrl`、`apiKey`（AES-256-GCM 加密存 `apiKeyEncrypted`）、`requestTimeoutMs`、健康检查回填 `healthStatus`/`serviceVersion`/`protocolVersion`/`releaseSha`/`model`/`capabilities` |

---

## 汇总：现有源表 → relation_* 表

| 现有源表/外部源 | 贡献给哪些 relation_* 表 |
|----------------|------------------------|
| `users` | nodes（person）、jobs（触发） |
| `enterprises` | nodes（enterprise） |
| `enterprise_memberships` | nodes/edges（成员关系）、鉴权、记忆投影目标 |
| `enterprise_departments` / `..._groups` / `..._group_members` | nodes/edges（部门/组结构） |
| `zclaw_agent_instances` / `global_builtin_agent_configs` / `enterprise_builtin_agent_configs` | nodes/edges（agent/skill） |
| `zclaw_sessions` / `zclaw_messages` | session_digests → nodes/edges（会话/事项/产物）；**需要 updatedAt** |
| OpenClaw 工作区（远程文件列表） | memory_snapshots → nodes/edges |
| RAGFlow API + `ragflow_datasets` / `ragflow_documents` / `ragflow_graph_jobs` | nodes/edges（文档实体/关系） |
| LLM（本地 / relation-compute） | digests 内容、workstream 推断、问答与风险分析文本 |
| 用户操作（共享开关/评审/提问/配置） | digests.visibility、workstream_reviews、question_history、compute_configs |

**结论：生成这 11 张表不需要任何新的业务数据 —— 全部来自你现有的业务表（组织/成员/Agent/会话/消息/文档映射）+ 两个既有外部服务（RAGFlow、OpenClaw 工作区）+ LLM。唯一的前置改动仍是那一条：`zclaw_messages` 补 `updatedAt`（增量扫描游标依赖它）。**
