# EvoMind C 端企业替换默认空间清空式切换实施方案

## 1. 背景与目标

当前系统同时存在两套空间语义：

- **默认空间**：面向 C 端用户，历史上作为个人/默认工作区处理。
- **企业空间**：面向 B 端用户，用户通过企业成员关系加入某个企业，并进入该企业的 EvoMind / KMAgent 实例。

默认空间已经逐步具备类似企业空间的能力，例如 RagFlow 配置、知识图谱、工作区配额、默认空间启用/禁用和用户准入管理。但它仍然不是一个真实企业，导致代码里长期存在 `personal`、空 `enterpriseId`、`enterpriseId="-1"`、默认 KMAgent 配置等多套口径。

本次目标是把默认空间彻底替换为一个真实企业：

```text
企业名称：EvoMind C端企业
企业定位：系统内置 C 端企业，承载 C 端用户后续的新实例、新工作区、新知识库和新图谱数据
```

重要前提：

- 已向业务领导确认：当前默认空间用户均为试用用户，默认空间内历史业务资产丢失可以接受。
- 本方案从“完整数据迁移”调整为“清空式切换”：保留 C 端用户账号、准入和可进入能力，不承诺迁移历史默认空间资产。
- 用户侧目标是入口和账号无感：老用户登录后能进入 `EvoMind C端企业` 并继续使用新空间；历史默认空间内文件、会话、知识库、图谱、排序、分享、个性化配额可以不可见。

迁移完成后的目标状态：

- 前端不再展示“默认空间”，统一展示 `EvoMind C端企业`。
- C 端用户也处于一个真实企业上下文中。
- 新数据全部写入 `EvoMind C端企业` 相关企业模型。
- 不保留默认空间长期兼容逻辑。
- 原默认空间用户账号和可用状态迁入默认企业，历史默认空间资产可丢弃。
- B 端企业空间现有能力不受影响。

### 1.1 明确不做的事

本方案不是兼容式渐进方案，而是一次架构语义替换方案：

- 不长期保留空 `enterpriseId` 表示默认空间。
- 不长期保留 `enterpriseId="-1"` 表示默认空间。
- 不长期保留 `zclaw_agent_instances.scope="personal"` 表示默认空间 Agent 实例。
- 不再把默认空间作为企业以外的独立准入、实例和管理分支。
- 不迁移或不保证展示旧默认空间历史文件、历史会话、历史知识库、历史知识图谱、历史分享和历史排序。
- 不要求 `EvoMind C端企业` 必须复用当前默认空间所在 KMAgent 实例；只要求新企业实例可用、后续新数据写入正确。
- 不在本方案执行阶段重新设计 KMAgent 远端数据模型。

## 2. 当前实现盘点

### 2.1 默认空间准入

默认空间当前通过 `zclaw_access_requests` 管理申请和审核。

相关入口：

- `apps/api/src/zclaw/zclaw.service.ts`
  - `getMyAccessRequest`
  - `createAccessRequest`
  - `approveAccessRequest`
  - `rejectAccessRequest`
  - `disableDefaultSpaceUserForAdmin`
  - `enableDefaultSpaceUserForAdmin`

当前语义：

- 用户提交默认空间申请。
- 管理员审批通过后，申请状态变为 `approved`。
- 审批通过本身不一定立即创建远端 Agent。
- 用户后续进入或 provision 时才可能调用 KMAgent bootstrap。

迁移后语义：

- 默认空间申请要转为 `EvoMind C端企业` 的成员申请。
- `zclaw_access_requests` 可以作为历史申请记录迁移依据，但不应继续作为默认空间独立主链路。
- 启用/禁用 C 端用户应落到 `enterprise_memberships.status` 和对应企业 Agent 状态。

### 2.2 默认空间 Agent

默认空间 Agent 当前落在 `zclaw_agent_instances`：

```text
scope = "personal"
enterpriseId = null
enterpriseOpenClawInstanceId = null
```

相关表：

- `zclaw_agent_instances`
- `zclaw_sessions`
- `zclaw_chat_bindings`
- `zclaw_messages`

关键关系：

- `zclaw_sessions.agentInstanceId` 外键指向 `zclaw_agent_instances.id`。
- 在完整迁移方案中，删除重建实例行会导致会话链路断开。
- 在本次清空式切换方案中，历史会话可丢弃，因此不再要求原地更新 personal agent instance。
- 推荐保留旧 personal agent instance 作为归档数据，不再从主业务入口读取；新 C 端企业用户进入后按企业逻辑创建或绑定新的 enterprise agent instance。

如果后续临时决定保留历史资产，以下字段才必须保持不变：

- `zclaw_agent_instances.id`
- `agentId`
- `userId`
- `workspacePath`
- `agentDir`
- 已有关联会话和消息数据

### 2.3 企业实例分配

企业空间当前通过以下模型工作：

- `enterprises`
- `enterprise_memberships`
- `enterprise_openclaw_instances`
- `zclaw_agent_instances.scope="enterprise"`

相关后端：

- `apps/api/src/enterprises/enterprise.service.ts`
  - `resolveZclawTargetForUser`
  - `resolveSharedWorkspaceTargetForUser`
  - `ensureOpenClawInstanceAssignmentForEnterpriseUser`
  - `toZclawTarget`

当前企业逻辑：

- 请求带企业 ID。
- 后端检查用户是否是 active 企业成员。
- 后端在 `enterprise_openclaw_instances` 中选择该企业可用实例。
- 若用户没有企业实例绑定，会创建企业 assignment placeholder。
- 后续 KMAgent 请求在企业 target 下运行。

迁移后：

- `EvoMind C端企业` 也必须有真实 `enterprise_openclaw_instances`。
- 该实例的 `kmAgentBaseUrl` 和 token 只需指向可用的 C 端企业 KMAgent/Gateway 实例。
- 若希望降低切换风险，可以沿用当前默认空间实际解析出的 KMAgent/Gateway 实例；但在历史资产可丢弃前提下，这不是硬性要求。
- 原默认空间用户应迁为 `EvoMind C端企业` active membership。

### 2.4 KMAgent 默认实例

默认空间当前不通过企业实例表分配，而是当请求没有 active enterprise target 时，直接使用全局配置解析默认 target。

```text
baseUrl = ZCLAW_KM_AGENT_BASE_URL ?? ZCLAW_GATEWAY_BASE_URL
token = ZCLAW_GATEWAY_TOKEN
```

相关代码：

- `apps/api/src/zclaw/zclaw-km-agent.client.ts`
  - `buildUrl`
  - `buildHeaders`
- `apps/api/src/enterprises/enterprise.service.ts`
  - `resolveDefaultZclawTarget`

关键判断：

- 默认空间当前实际就是一个全局 KMAgent/Gateway 配置实例。
- 代码优先支持 `ZCLAW_KM_AGENT_BASE_URL`，没有配置时 fallback 到 `ZCLAW_GATEWAY_BASE_URL`。
- 当前环境若未配置 `ZCLAW_KM_AGENT_BASE_URL`，默认空间实际使用的是 `ZCLAW_GATEWAY_BASE_URL` 和 `ZCLAW_GATEWAY_TOKEN`。
- 企业空间则通过 `enterprise_openclaw_instances` 获取 baseUrl / token。
- 在完整迁移方案中，若 `EvoMind C端企业` 配到另一台 KMAgent，原 workspace、远端 agent binding、会话和文件可能不可见。
- 当前已确认历史默认空间资产可丢弃，因此允许默认企业实例指向新的或现有的可用 KMAgent/Gateway；Preflight 只需要记录实际旧 target 作为影响面说明，并验证新 target 可 bootstrap 和读写。

### 2.5 RagFlow 默认空间

当前 RagFlow 默认空间使用特殊企业 ID：

```text
enterpriseId = "-1"
```

相关代码：

- `apps/api/src/zclaw/ragflow/ragflow.service.ts`
  - `DEFAULT_RAGFLOW_ENTERPRISE_ID = "-1"`
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts`
  - `DEFAULT_RAGFLOW_ENTERPRISE_ID = "-1"`

相关表：

- `enterprise_ragflow_configs`
- `ragflow_datasets`
- `ragflow_documents`
- `ragflow_sync_jobs`
- `ragflow_graph_jobs`

历史文档也明确存在旧口径：

- `docs/ragflow-enterprise-config-plan.md`：默认空间固定使用 `enterpriseId="-1"`。
- `docs/ragflow-knowledge-graph-plan.md`：默认空间图谱使用 `enterpriseId="-1"`。

迁移后：

- `-1` 不再作为默认空间主键。
- 历史 `enterpriseId="-1"` 的 RagFlow 配置和映射可以归档或废弃，不作为主业务迁移对象。
- 新 RagFlow 数据全部使用 `EvoMind C端企业` 真实企业 ID。

### 2.6 前端 active enterprise 空字符串语义

当前前端常用空字符串表示默认空间：

- `apps/web/src/hooks/useActiveEnterpriseSpace.ts`
- `apps/web/src/components/zclaw/ZclawShell.tsx`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`

## 3. 关键风险

### 3.1 历史默认空间资产丢失的用户感知风险

当前已确认默认空间用户仍处于试用阶段，历史默认空间资产丢失可以接受。

可丢弃范围：

- personal agent 历史 workspace 文件。
- 历史会话、chat binding、message。
- `enterpriseId="-1"` 的 RagFlow 配置、dataset、document、sync job、graph job。
- 默认空间排序、分享、个性化配额。

不可丢弃范围：

- 用户账号。
- 用户登录能力。
- 用户是否能进入 `EvoMind C端企业`。
- 管理员对 C 端用户启用/禁用的能力。
- B 端企业数据和实例。

要求：

- Preflight 仍需统计旧数据规模，但统计目的从“保证迁移完整”改为“确认丢弃影响面”。
- 对外口径要明确：历史试用空间资产不承诺保留，切换后进入新的 `EvoMind C端企业`。

### 3.2 新 C 端企业实例必须可用

历史 KMAgent 数据可以不迁，但新企业实例必须可用。

风险：

- 默认企业实例 baseUrl/token 配错，导致 C 端用户无法 bootstrap。
- 新用户或老用户进入后无法创建 enterprise agent。
- 文件树、workspace usage、会话创建、RagFlow 配置在新企业上下文下不可用。

要求：

- 记录旧默认 target：`ZCLAW_KM_AGENT_BASE_URL ?? ZCLAW_GATEWAY_BASE_URL`，token 来源为 `ZCLAW_GATEWAY_TOKEN`。
- 明确新默认企业实例 target，可以沿用旧 target，也可以使用新的 C 端实例。
- Cutover 前必须验证新默认企业实例的 bootstrap、workspace usage、文件树、会话创建、RagFlow 基础能力。

### 3.3 旧默认空间数据不能继续被主业务写入

清空式切换的关键不是迁完旧数据，而是切断旧入口。

风险：

- 后端继续在缺 enterpriseId 时回退到默认 KMAgent 全局配置。
- 后端继续创建 `scope="personal"` 的默认空间 agent。
- RagFlow 继续把 C 端请求写到 `enterpriseId="-1"`。
- 前端继续发送空 enterpriseId 或 `-1`。

要求：

- C 端用户必须拥有 `EvoMind C端企业` membership。
- protected ZClaw / RagFlow 主业务请求必须有真实企业上下文。
- 缺 enterpriseId 不应静默落回旧默认空间。
- 旧 personal / `-1` 数据可保留归档，但不再作为主业务查询来源。

### 3.4 前端不能继续发空 ID 或 `-1`

迁移后后端不再承诺默认空间兼容逻辑。

风险：

- 前端仍发空 enterpriseId，后端可能走默认 KMAgent 全局配置，重新产生旧默认空间数据。
- 前端仍发 `-1`，RagFlow 新数据可能写回旧哨兵口径。

要求：

- active enterprise 初始化必须得到真实默认企业 ID。
- 代码扫描必须无 `activeEnterpriseId || "-1"`。
- 业务请求缺 enterpriseId 应被视为错误，或由前端统一补默认企业 ID。

### 3.5 B 端企业不能受影响

本次只替换 C 端默认空间语义，不应改变已有 B 端企业：

- B 端 membership 不改。
- B 端企业实例池不改。
- B 端 workspace、RagFlow、知识图谱、配额不改。
- 企业切换器仍允许用户从 `EvoMind C端企业` 切到真实 B 端企业。

## 4. 分阶段实施步骤

每个阶段都要形成小闭环：可单独开发、可单独验证、失败可定位。

### 4.1 Step 1：Preflight 审计闭环

目的：

在动代码和数据前确认当前默认空间数据丢弃范围，并确认新的 `EvoMind C端企业` target 可正常使用。

本阶段默认只产出可执行审计清单，不连接线上库、不访问 KMAgent、不改代码、不执行迁移。后续真正执行审计时，需要显式允许只读访问远程 `DATABASE_URL` 和 KMAgent/Gateway。

实施内容：

1. 统计默认空间 Agent 数据：
   - `zclaw_agent_instances.scope='personal' AND enterpriseOpenClawInstanceId IS NULL` 的总量和状态分布。
   - 这些 agent 关联的 `zclaw_sessions`、`zclaw_chat_bindings`、`zclaw_messages` 数量。
   - 抽取样本用户：active/provisioned、disabled、有会话、有文件/知识库的用户。
2. 统计默认空间准入数据：
   - `zclaw_access_requests` 最新状态分布。
   - approved 但未 provision 的用户。
   - disabled agent 与申请状态不一致的用户。
   - pending/rejected 孤立用户。
3. 统计默认空间配额、排序、分享：
   - `zclaw_workspace_quota_configs.scope='personal' AND enterpriseOpenClawInstanceId IS NULL`。
   - `zclaw_workspace_child_orders.enterpriseId=''`。
   - `zclaw_file_shares.enterpriseId IS NULL` 或默认空间口径分享。
4. 统计 RagFlow / 知识图谱：
   - `enterprise_ragflow_configs.enterpriseId='-1'`。
   - `ragflow_datasets`、`ragflow_documents`、`ragflow_sync_jobs`、`ragflow_graph_jobs` 中默认空间 `enterpriseId='-1'` 的数量。
   - `scope='personal'` 与 `scope='enterprise'` 的 dataset 分布，避免迁移时误删个人知识库语义。
5. 记录默认 KMAgent target：
   - 默认 baseUrl 解析规则为 `ZCLAW_KM_AGENT_BASE_URL ?? ZCLAW_GATEWAY_BASE_URL`。
   - 当前环境若无 `ZCLAW_KM_AGENT_BASE_URL`，实际 default target baseUrl 为 `ZCLAW_GATEWAY_BASE_URL`。
   - token 来源为 `ZCLAW_GATEWAY_TOKEN`。
6. 输出审计报告，未产出报告不得进入 Step 2。

审计口径：

- 以下 SQL 仍然保留，因为后续需要知道会丢弃多少历史默认空间资产。
- 这些计数不再要求迁移前后保持一致。
- 如果业务再次要求保留历史资产，必须切回完整迁移方案，重新启用 agent/RagFlow/workspace 数据一致性校验。

审计 SQL 清单：

后续执行者用只读连接运行以下查询，输出保存为迁移前报告。

```sql
-- 1. personal agent 状态分布
SELECT status, COUNT(*)::bigint AS count
FROM zclaw_agent_instances
WHERE scope = 'personal'
  AND "enterpriseOpenClawInstanceId" IS NULL
  AND "isDeleted" = false
GROUP BY status
ORDER BY status;

-- 2. personal agent 总量与关联会话
SELECT
  COUNT(DISTINCT agent.id)::bigint AS personal_agent_count,
  COUNT(session.id)::bigint AS session_count
FROM zclaw_agent_instances agent
LEFT JOIN zclaw_sessions session
  ON session."agentInstanceId" = agent.id
 AND session."isDeleted" = false
WHERE agent.scope = 'personal'
  AND agent."enterpriseOpenClawInstanceId" IS NULL
  AND agent."isDeleted" = false;

-- 2b. personal agent 关联 binding/message 数量
SELECT
  COUNT(DISTINCT agent.id)::bigint AS personal_agent_count,
  COUNT(DISTINCT binding.id)::bigint AS chat_binding_count,
  COUNT(message.id)::bigint AS message_count
FROM zclaw_agent_instances agent
LEFT JOIN zclaw_sessions session
  ON session."agentInstanceId" = agent.id
 AND session."isDeleted" = false
LEFT JOIN zclaw_chat_bindings binding
  ON binding."sessionId" = session.id
 AND binding."isDeleted" = false
LEFT JOIN zclaw_messages message
  ON message."sessionId" = session.id
 AND message."isDeleted" = false
WHERE agent.scope = 'personal'
  AND agent."enterpriseOpenClawInstanceId" IS NULL
  AND agent."isDeleted" = false;

-- 3. 默认空间申请最新状态分布
WITH latest_request AS (
  SELECT DISTINCT ON ("userId")
    "userId", status, "createdAt", "reviewedAt"
  FROM zclaw_access_requests
  WHERE "isDeleted" = false
  ORDER BY "userId", "createdAt" DESC
)
SELECT status, COUNT(*)::bigint AS count
FROM latest_request
GROUP BY status
ORDER BY status;

-- 4. approved 但无 personal agent 的用户
WITH latest_request AS (
  SELECT DISTINCT ON ("userId") "userId", status
  FROM zclaw_access_requests
  WHERE "isDeleted" = false
  ORDER BY "userId", "createdAt" DESC
)
SELECT COUNT(*)::bigint AS approved_without_agent_count
FROM latest_request request
LEFT JOIN zclaw_agent_instances agent
  ON agent."userId" = request."userId"
 AND agent.scope = 'personal'
 AND agent."enterpriseOpenClawInstanceId" IS NULL
 AND agent."isDeleted" = false
WHERE request.status = 'approved'
  AND agent.id IS NULL;

-- 5. personal workspace quota
SELECT COUNT(*)::bigint AS personal_quota_count
FROM zclaw_workspace_quota_configs
WHERE scope = 'personal'
  AND "enterpriseOpenClawInstanceId" IS NULL;

-- 6. 默认空间排序记录
SELECT COUNT(*)::bigint AS default_space_order_count
FROM zclaw_workspace_child_orders
WHERE "enterpriseId" = '';

-- 7. 默认空间分享记录
SELECT COUNT(*)::bigint AS default_space_share_count
FROM zclaw_file_shares
WHERE "enterpriseId" IS NULL
  AND "isDeleted" = false;

-- 8. RagFlow -1 配置
SELECT COUNT(*)::bigint AS default_ragflow_config_count
FROM enterprise_ragflow_configs
WHERE "enterpriseId" = '-1'
  AND "isDeleted" = false;

-- 9. RagFlow dataset 分布
SELECT scope, "enterpriseId", COUNT(*)::bigint AS count
FROM ragflow_datasets
WHERE "isDeleted" = false
GROUP BY scope, "enterpriseId"
ORDER BY scope, "enterpriseId";

-- 10. RagFlow document -1 数量
SELECT COUNT(*)::bigint AS default_ragflow_document_count
FROM ragflow_documents document
JOIN ragflow_datasets dataset
  ON dataset.id = document."datasetMappingId"
WHERE dataset."enterpriseId" = '-1'
  AND document."isDeleted" = false;

-- 11. RagFlow sync job -1 数量
SELECT COUNT(*)::bigint AS default_ragflow_sync_job_count
FROM ragflow_sync_jobs job
LEFT JOIN ragflow_datasets dataset
  ON dataset.id = job."datasetMappingId"
LEFT JOIN ragflow_documents document
  ON document.id = job."documentMappingId"
WHERE dataset."enterpriseId" = '-1'
   OR document."enterpriseId" = '-1';

-- 12. RagFlow graph job -1 数量
SELECT COUNT(*)::bigint AS default_ragflow_graph_job_count
FROM ragflow_graph_jobs
WHERE "enterpriseId" = '-1';

-- 13. 样本用户候选
SELECT
  agent."userId",
  agent.id AS "agentInstanceId",
  agent."agentId",
  agent.status,
  agent."createdAt",
  COUNT(session.id)::bigint AS session_count
FROM zclaw_agent_instances agent
LEFT JOIN zclaw_sessions session
  ON session."agentInstanceId" = agent.id
 AND session."isDeleted" = false
WHERE agent.scope = 'personal'
  AND agent."enterpriseOpenClawInstanceId" IS NULL
  AND agent."isDeleted" = false
GROUP BY agent."userId", agent.id, agent."agentId", agent.status, agent."createdAt"
ORDER BY session_count DESC, agent."createdAt" ASC
LIMIT 20;
```

KMAgent 验证步骤：

旧默认 target 记录：

- 记录实际 baseUrl：优先 `ZCLAW_KM_AGENT_BASE_URL`，否则 `ZCLAW_GATEWAY_BASE_URL`。
- 记录 token 来源，不记录 token 明文；当前应为 `ZCLAW_GATEWAY_TOKEN`。
- 旧 target 不再要求验证历史 workspace、文件树、会话是否能在企业 target 下继续读取。

新默认企业 target 验证：

- 使用即将写入 `enterprise_openclaw_instances` 的 baseUrl/token 构造 enterprise target。
- 对样本用户调用 bootstrap，记录 `agentId`、`agentCreated`、`bindingCreated`。
- 对样本用户调用 workspace usage，记录 bytes/fileCount/directoryCount。
- 对样本用户调用文件树根目录，确认接口可读。
- 创建或读取一条测试会话，确认企业 target 下会话主链路可用。
- 若使用新 KMAgent 实例，历史文件/会话为空是可接受结果。

产出物：

- `preflight-audit-report.md` 或同等格式报告。
- 可直接复制填写的报告模板见 [evomind-consumer-enterprise-preflight-audit-report-template.md](./evomind-consumer-enterprise-preflight-audit-report-template.md)。
- 报告必须包含执行时间、数据库连接环境名、default target 实际 baseUrl、每条 SQL 结果、样本用户列表、新默认企业 target 验证结果、停止条件是否触发、是否允许进入 Step 2。
- 报告不得包含数据库密码、`ZCLAW_GATEWAY_TOKEN` 明文或用户敏感内容明文。

验收标准：

- 能列出所有需要处理和允许丢弃的默认空间数据范围。
- 能列出所有允许丢弃的默认空间历史资产范围。
- 新默认企业 target 可 bootstrap、可读 workspace usage、可读文件树、可创建或读取会话。
- 审计 SQL 均为 `SELECT`，不得包含 `INSERT/UPDATE/DELETE/ALTER/DROP/TRUNCATE`。
- SQL 能覆盖 Agent、申请、配额、排序、分享、RagFlow、图谱、样本用户。
- 没有审计报告，不允许进入 Step 2。

停止条件：

- 新默认企业 target 无法 bootstrap。
- 新默认企业 target 无法读 workspace usage 或文件树。
- 新默认企业 target 无法创建或读取会话。
- C 端用户无法建立默认企业 membership。
- 任一审计查询发现 B 端企业数据被错误纳入默认空间丢弃范围，必须先修正范围，不得继续 Step 2。

### 4.2 Step 2：创建 EvoMind C 端企业基础数据闭环

目的：

让系统中存在真实默认企业和真实企业实例。

实施内容：

1. 定义固定系统常量：
   - `EVO_MIND_CONSUMER_ENTERPRISE_ID`
   - `EVO_MIND_CONSUMER_ENTERPRISE_SLUG`
   - `EVO_MIND_CONSUMER_ENTERPRISE_NAME = "EvoMind C端企业"`
2. 使用 Prisma migration SQL 自动初始化：
   - migration：`packages/db/prisma/migrations/20260630130000_seed_evomind_consumer_enterprise/migration.sql`。
   - 发布时由 `prisma migrate deploy` 自动执行，不需要手动创建企业。
3. 初始化数据：
   - 插入 `enterprises` 记录。
   - 插入 `enterprise_openclaw_instances` 记录。
   - 默认实例 `kmAgentBaseUrl` 和 `gatewayBaseUrl` 先写当前默认空间实际 baseUrl。
   - 默认实例 token 写占位值 `__MANUAL_UPDATE_REQUIRED__`。
   - `sharedWorkspacePrimary = true`。
   - `instanceKey = "default"`。
4. 发布后手动更新默认实例 token：
   - 在企业实例配置页编辑 `EvoMind C端企业默认实例`。
   - 填入真实 gateway token，让后端按现有加密逻辑保存。
   - token 未更新前，后端会明确提示默认企业实例 token 未配置，不会静默调用 KMAgent。
5. 增加保护：
   - 默认企业不可删除。
   - 默认企业不可被普通企业管理动作停用。
   - 默认企业主实例不可删除。

验收标准：

- 企业管理中能查询到 `EvoMind C端企业`。
- 默认企业实例存在，且 `sharedWorkspacePrimary=true`。
- token 仍为占位值时，`EnterpriseService.toZclawTarget` 返回明确错误。
- 手动更新 token 后，默认企业实例能解析出正确 baseUrl/token。
- `enterprise_openclaw_instances` 中默认企业只有一个 `sharedWorkspacePrimary=true`。
- 旧 personal agent、旧 RagFlow `-1`、旧 quota/order/share 未在 Step 2 被修改。

### 4.3 Step 3：迁移 membership 准入闭环

目的：

把默认空间准入状态转为默认企业成员状态。

迁移规则：

| 来源状态 | 目标 membership |
| --- | --- |
| 有 active/provisioned personal agent | `active` |
| personal agent disabled | `disabled` |
| 最新 access request approved 且无 agent | `active` |
| 最新 access request pending 且无 agent | `pending` |
| 最新 access request rejected 且无 agent | `rejected` |
| 无申请、无 agent | 不创建，后续首次申请或登录时按新逻辑创建 |

实施内容：

1. 通过 Step 2 的同一条 Prisma migration SQL 批量写入 `enterprise_memberships`。
2. 角色默认 `member`；已存在 `owner/admin` 不降级、不禁用。
3. `joinedAt` 对 active 用户可取：
   - personal agent `createdAt`
   - 或 approved request `reviewedAt`
   - 或迁移执行时间
4. 保留 `zclaw_access_requests` 历史记录，但不再作为主准入模型。
5. 管理端审批、拒绝、启用、禁用逻辑改为同步默认企业 membership。
6. 老默认空间接口可临时保留路由外壳，避免前端立刻断；内部语义切到默认企业 membership。

验收标准：

- 原可用默认空间用户都有默认企业 active membership。
- 原禁用用户在默认企业中不可用。
- pending/rejected 用户状态可在默认企业成员管理中表达。
- B 端企业 membership 不受影响。

### 4.4 Step 4：切换 Agent Instance 主链路闭环

目的：

停止使用默认空间 personal agent 主链路，让 C 端用户后续全部使用默认企业 enterprise agent。

处理规则：

满足以下条件的旧默认空间 agent 不再要求迁移：

```sql
scope = 'personal'
AND enterpriseOpenClawInstanceId IS NULL
AND isDeleted = false
```

推荐处理方式：

- 保留旧行作为归档数据，不从主业务入口读取。
- 可选：增加 metadata 标记，例如 `metadata.archivedByConsumerEnterpriseCutover = true`，便于后续清理和审计。
- 不要求保持旧 `agentId`、`workspacePath`、`agentDir` 在新企业中继续可见。
- 新默认企业 agent 由企业逻辑创建，`scope="enterprise"`，`enterpriseId=EVO_MIND_CONSUMER_ENTERPRISE_ID`，`enterpriseOpenClawInstanceId=默认企业实例 ID`。

实施内容：

1. 迁移前审计旧 personal agent 数量，作为可丢弃资产范围。
2. 修改后端默认入口：
   - C 端用户进入时走企业 target。
   - 默认企业成员缺 agent 时，按企业逻辑 bootstrap。
   - 不再创建 `scope="personal"` 的默认空间 agent。
3. 重新计算或重新生成默认企业实例 `activeAgents`。
4. 可选执行归档标记，避免旧 personal agent 被误认为待迁移数据。

验收标准：

- 老用户登录后会进入默认企业 enterprise agent 主链路。
- 历史 personal agent 文件树、会话、workspace usage 不承诺可见。
- 新用户不再生成 personal agent instance。
- 新 C 端用户和老 C 端用户的新会话都绑定 enterprise agent。

### 4.5 Step 5：重置 workspace quota / order / share 闭环

目的：

停止默认空间配额、排序和分享主链路，后续全部按默认企业上下文写入。

名词解释：

- `workspace quota`：空间容量配置。旧默认空间主要通过 `zclaw_workspace_quota_configs` 表达个人/实例容量；新模型已经改为企业共享空间容量、企业成员默认个人空间容量、成员个人空间覆盖容量。
- `workspace child order`：文件树子节点排序记录。用户在左侧工作区文件树里调整文件夹、文件、知识库目录顺序时，后端会把同一个父目录下的子路径顺序保存到 `zclaw_workspace_child_orders`。它不存真实文件，只存 UI 排序偏好。
- `file share`：文件/文件夹分享链接。用户把个人工作区或企业共享工作区中的文件生成分享链接时，后端会把分享主记录写入 `zclaw_file_shares`，把分享包含的文件/文件夹条目写入 `zclaw_file_share_items`。

为什么它们也要闭环：

- 旧默认空间中，个人工作区排序可能以 `enterpriseId=""` 存储。
- 旧默认空间中，分享可能以 `enterpriseId IS NULL` 存储。
- 如果 C 端默认企业切换后仍允许这些空值新写入，用户看起来可以使用，但数据库会继续产生“旧默认空间”数据，后续会出现排序丢失、分享读取跨空间、RagFlow/工作区 target 混用等隐蔽问题。
- 本次历史排序和历史分享可丢弃，但切换后的新排序、新分享必须全部落到真实默认企业 ID。

涉及表：

- `zclaw_workspace_quota_configs`
- `zclaw_workspace_child_orders`
- `zclaw_file_shares`
- `zclaw_file_share_items`

处理规则：

1. `zclaw_workspace_quota_configs`
   - personal/null 旧配置可归档，不要求迁移。
   - 默认企业使用统一的 C 端企业配额策略或重新创建企业实例配额。
2. `zclaw_workspace_child_orders`
   - 原默认空间空 enterpriseId 排序记录可丢弃。
   - 新排序记录必须写入默认企业 ID。
3. `zclaw_file_shares`
   - 默认空间分享可失效或归档，不要求继续访问。
   - 新分享记录必须写入默认企业 ID。

后端改造要求：

- workspace quota 查询不再接受 personal scope。
- child order service 不再用空字符串表达 C 端默认空间；C 端默认场景必须解析为 `EVO_MIND_CONSUMER_ENTERPRISE_ID`。
- 文件分享创建、更新、复制、读取默认走真实企业 target。
- 不能只依赖 `readEnterpriseId(req)` 的原始入参，因为 C 端请求可能没有显式传企业 ID；必须使用“最终解析后的企业上下文 ID”写库。
- 如果请求没有显式 B 端企业 ID，后端必须把该请求归一化到 `EVO_MIND_CONSUMER_ENTERPRISE_ID`，再传入排序、分享、RagFlow 和 workspace 写入逻辑。
- 如果默认企业实例 token 仍是占位值，分享复制、文件读取、排序依赖的 KMAgent 操作要返回明确错误，不能静默落回旧默认空间。

前端改造要求：

- `getZclawWorkspaceChildOrdersApi`、`saveZclawWorkspaceChildOrdersApi`、`getZclawSharedWorkspaceChildOrdersApi`、`saveZclawSharedWorkspaceChildOrdersApi` 必须在 C 端默认企业上下文中带上真实默认企业 ID，或由全局请求层保证 header 为真实默认企业 ID。
- 创建分享、编辑分享、复制分享时，不能再因为 `activeEnterpriseId` 为空而省略企业上下文。
- 删除 `activeEnterpriseId || undefined` 作为 C 端默认空间语义的用法。
- 删除 `activeEnterpriseId || "-1"` 作为 C 端默认空间或知识图谱语义的用法。
- `share/files/:publicId/copy` 当前会把 `getActiveEnterpriseId()` 写入 body；切换后 `getActiveEnterpriseId()` 不能再为空。

验收标准：

- 默认企业配额展示符合新的 C 端策略。
- 老默认空间排序和分享不承诺保留。
- 新增排序、配额、分享数据全部写入默认企业 ID。
- 切换后 C 端用户调整个人工作区文件树顺序，`zclaw_workspace_child_orders.enterpriseId` 为 `EVO_MIND_CONSUMER_ENTERPRISE_ID`，不再是空字符串。
- 切换后 C 端用户创建文件分享，`zclaw_file_shares.enterpriseId` 为 `EVO_MIND_CONSUMER_ENTERPRISE_ID`，不再是 `NULL`。
- 切换后 C 端用户复制分享到个人工作区，新文件写入默认企业 target，不写入旧 personal/default target。

### 4.6 Step 6：重置 RagFlow / 知识图谱闭环

目的：

去除默认空间 RagFlow 的 `-1` 哨兵值，后续新 RagFlow / 知识图谱数据全部写入真实默认企业 ID。

涉及表：

- `enterprise_ragflow_configs`
- `ragflow_datasets`
- `ragflow_file_blobs`
- `ragflow_documents`
- `ragflow_sync_jobs`
- `ragflow_graph_jobs`

处理规则：

1. `enterprise_ragflow_configs.enterpriseId = "-1"` 旧配置可归档，不要求迁移。
2. `ragflow_datasets.enterpriseId = "-1"` 旧 dataset 可归档或逻辑隐藏。
3. `ragflow_documents.enterpriseId = "-1"` 旧 document 可归档或逻辑隐藏。
4. `ragflow_sync_jobs` 旧任务可取消、忽略或保留审计，不要求继续执行。
5. `ragflow_graph_jobs.enterpriseId = "-1"` 旧图谱任务可归档，不要求继续展示。
6. 为 `EvoMind C端企业` 创建新的 RagFlow 配置和 dataset 初始化路径。

代码改造要求：

- 删除 `DEFAULT_RAGFLOW_ENTERPRISE_ID = "-1"`。
- RagFlow config/capability/dataset/document/status/graph 逻辑必须要求真实企业 ID。
- 默认企业 personal knowledge dataset 可以继续使用 `scope="personal"` 表示个人知识库，但 `enterpriseId` 必须是真实默认企业 ID。
- 企业共享知识库继续使用 `scope="enterprise"`。

前端改造要求：

- 知识图谱面板不再传 `-1`。
- RagFlow 配置页不再展示“默认空间 ID”。
- 所有 graph status 测试和 mock 使用默认企业真实 ID。

验收标准：

- 默认企业 RagFlow 配置可保存、读取、测试。
- 老用户历史个人知识库和知识图谱不承诺可见。
- 新上传文档、新图谱任务全部写入真实默认企业 ID。
- 代码和测试中不再以 `-1` 表示默认空间。

实施状态（Step 6 已落地）：

- `apps/api/src/zclaw/ragflow/ragflow.service.ts`
  - `normalizeOptionalEnterpriseId()` 已从 `-1` fallback 改为 `EvoMind C端企业` ID。
  - 显式传入旧 `-1` 时也归一化为默认企业 ID，避免前端缓存或旧调用继续写入 `-1`。
  - `ensurePersonalDataset()` / `ensureEnterpriseDataset()` 新建 dataset 名称统一包含真实企业 ID，不再生成 `*-default`。
  - RagFlow 管理列表不再手工拼接“默认空间 -1”行，只展示 `enterprises` 表中的真实企业。
  - 保存 RagFlow 配置时拒绝 `enterpriseId='-1'`，提示配置 `EvoMind C端企业`。
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts`
  - personal 图谱上下文、capability、read target 的空企业 ID 已归一化为默认企业 ID。
  - `-1` 仅保留为 legacy 防护常量，用于拒绝 shared-workspace 企业上下文或兼容旧入参判断，不作为新写入 ID。
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
  - RagFlow capability 本地 fallback 不再使用 `activeEnterpriseId || "-1"`，改为固定默认企业 ID。
- `apps/web/src/app/(zclaw-shell)/admin/ragflow/page.tsx`
  - 概览卡不再显示“默认空间 ID -1”，改为显示 C 端企业 ID。

上线后校验 SQL：

```sql
-- cutover 后不应再新增 -1 dataset
SELECT COUNT(*)::bigint AS legacy_dataset_created_after_cutover
FROM ragflow_datasets
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at;

-- cutover 后不应再新增 -1 document
SELECT COUNT(*)::bigint AS legacy_document_created_after_cutover
FROM ragflow_documents
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at;

-- cutover 后不应再新增 -1 图谱任务
SELECT COUNT(*)::bigint AS legacy_graph_job_created_after_cutover
FROM ragflow_graph_jobs
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at;

-- cutover 后不应再有新 sync job payload 写 -1
SELECT COUNT(*)::bigint AS legacy_sync_job_payload_after_cutover
FROM ragflow_sync_jobs
WHERE "createdAt" >= :cutover_at
  AND payload::text LIKE '%"enterpriseId":"-1"%';
```

### 4.7 Step 7：替换前端 enterprise 上下文闭环

目的：

前端彻底从“空企业 ID = 默认空间”切换为“企业 membership = 可进入空间”。前端不写死默认企业 ID；C 端默认企业 ID 只由后端 consumer membership 接口返回。

改造点：

- `apps/web/src/hooks/useActiveEnterpriseSpace.ts`
- `apps/web/src/components/zclaw/ZclawShell.tsx`
- `apps/web/src/components/zclaw/ZclawChatProvider.tsx`
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
- dashboard hooks
- admin users/access/membership/quota/ragflow pages
- knowledge graph components and tests

实施内容：

1. 登录后通过 consumer membership 接口解析是否可进入 `EvoMind C端企业`。
2. 新增 `GET /api/enterprises/consumer/membership` 和 `POST /api/enterprises/consumer/join`，前端不传固定 ID/slug。
3. C 端申请页从 `zclaw_access_requests` 切到默认企业 membership 申请，只收集昵称和申请备注。
4. 企业切换器中显示真实企业列表中的 `EvoMind C端企业`，不再展示虚拟“默认空间”项。
5. 删除“默认空间”主文案。
6. 删除 `activeEnterpriseId || "-1"`。
7. 删除空字符串表示默认空间的逻辑。
8. 所有业务请求携带真实 active enterpriseId；没有 active enterprise 时进入申请/待审核/禁用页，不进入工作区主界面。

文案规则：

- 主空间名称使用 `EvoMind C端企业`。
- 如果页面描述用户自己的文件区，可以使用“个人工作区”。
- 管理端不得再显示“默认空间 ID”。

验收标准：

- 刷新页面后默认进入 `EvoMind C端企业`。
- 切换 B 端企业后上下文正确。
- 无业务请求发送空 enterpriseId 或 `-1`。
- UI 不再出现默认空间主概念。

### 4.8 Step 8：删除后端默认空间逻辑闭环

目的：

移除默认空间作为独立主业务分支的后端逻辑。

当前实施口径：

- C 端状态只读取 `EvoMind C端企业` membership，不再把 `zclaw_access_requests` 作为主状态 fallback。
- 用户侧旧 `/api/zclaw/access-request/me`、`/api/zclaw/access-requests` 可以短期保留兼容壳，但返回/写入语义必须是默认企业 membership。
- 后台旧 `/api/zclaw/admin/access-requests*` 只作为隐藏历史记录入口，审核入口必须迁到 `组织管理 / 成员管理`。
- 旧 `approve/reject access request` 不允许继续更新 `zclaw_access_requests` 或恢复 personal agent；应返回明确提示，让管理员到成员管理审核。
- 旧 `default-space-users/:userId/enable|disable` 如果短期保留，只能更新默认企业 membership 状态。
- 删除或停止调用 `getDefaultSpaceAgentInstanceForAdmin`、`restoreDisabledDefaultSpaceAgent` 等旧 personal agent 管理辅助。
- admin-users 中主状态字段必须是 `EvoMind C端企业状态`，不能再展示“默认空间已开通”。

保留语义边界：

- `scope="personal"` 可以继续用于 RagFlow 个人知识库 dataset scope。
- `scope="personal"` 不再用于默认空间 Agent 实例。
- 工作区、会话、Agent、配额都应处于 enterprise context。
- `scope="personal" AND enterpriseOpenClawInstanceId IS NULL` 的旧 agent 仅作为历史归档，不用于准入、启停、工作区状态或成员审核。

验收标准：

- 后端不再存在默认空间启停主流程。
- 新 C 端申请只写默认企业 `enterprise_memberships`，不新增 `zclaw_access_requests`。
- pending/rejected/disabled/active 状态均以默认企业 membership 为准。
- protected ZClaw 业务请求必须有真实 enterprise context。
- 缺 enterpriseId 的请求不会悄悄落回旧默认空间。
- 旧 personal agent 不会因为旧兼容接口被恢复或重新启用。

### 4.9 Step 9：切换后一致性校验清单

目的：

在切换后证明新主链路干净可用，且没有新旧口径混写。

定位：

- Step 9 不再作为大代码开发阶段。
- Step 9 是发布验收清单，必须在 cutover 后执行并留存结果。
- 如果以下校验失败，应立即停止放量，回到 Step 8 或对应功能步骤修复。

必须校验：

```sql
-- 切换后不应继续新建默认空间 personal agent 活跃记录
SELECT COUNT(*)
FROM zclaw_agent_instances
WHERE scope = 'personal'
  AND "enterpriseOpenClawInstanceId" IS NULL
  AND "isDeleted" = false;

-- 切换后不应继续使用默认空间 personal quota
SELECT COUNT(*)
FROM zclaw_workspace_quota_configs
WHERE scope = 'personal'
  AND "enterpriseOpenClawInstanceId" IS NULL;

-- 切换后不应继续使用 -1 RagFlow 配置
SELECT COUNT(*)
FROM enterprise_ragflow_configs
WHERE "enterpriseId" = '-1';

-- 切换后不应继续写入 -1 RagFlow dataset
SELECT COUNT(*)
FROM ragflow_datasets
WHERE "enterpriseId" = '-1';

-- 默认企业 active 成员数量应覆盖原默认空间 active/provisioned 用户
SELECT COUNT(*)
FROM enterprise_memberships
WHERE "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND status = 'active'
  AND "isDeleted" = false;
```

业务抽样：

- 老 active 用户：登录、进入企业、创建或打开新会话、查看新企业文件树、发起聊天。
- 老 disabled 用户：登录后不能进入 `EvoMind C端企业`。
- 新用户：申请或加入后创建 enterprise agent。
- 平台管理员：查看成员、配额、RagFlow、新图谱任务。
- B 端用户：切换真实企业，工作区和配置不受影响。

验收标准：

- 老用户账号无感进入 `EvoMind C端企业`。
- 老默认空间历史资产可不可见，不作为失败条件。
- 新数据全部落到默认企业真实 ID。
- 无 `-1` 和空企业 ID 新写入。

### 4.10 Step 10：Cutover 与回滚清单

目的：

确保迁移上线有明确顺序、验证点和回滚路径。

定位：

- Step 10 不再作为独立功能开发阶段。
- Step 10 是上线操作清单和应急回滚口径。
- 历史默认空间资产已确认可丢弃，因此不设计复杂数据反迁移；回滚重点是入口控制、代码回退和默认企业实例配置恢复。

建议 cutover 顺序：

1. 低峰期进入维护窗口。
2. 暂停 ZClaw / EvoMind 写入入口。
3. 执行 preflight audit，确认可丢弃资产范围。
4. 备份关键表，便于审计和必要时恢复入口。
5. 执行默认企业、membership、实例初始化和旧入口切断。
6. 执行切换后一致性校验。
7. 部署后端。
8. 部署前端。
9. 执行 smoke test。
10. 恢复入口。

关键备份表：

- `enterprises`
- `enterprise_memberships`
- `enterprise_openclaw_instances`
- `zclaw_agent_instances`
- `zclaw_sessions`
- `zclaw_workspace_quota_configs`
- `zclaw_workspace_child_orders`
- `zclaw_file_shares`
- `enterprise_ragflow_configs`
- `ragflow_datasets`
- `ragflow_documents`
- `ragflow_sync_jobs`
- `ragflow_graph_jobs`

回滚原则：

- 由于采用清空式切换，回滚优先回滚前后端入口和 membership/默认企业实例配置。
- 旧 personal agent 和 `-1` RagFlow 数据建议保留归档，回滚时可重新开放旧默认空间入口。
- 如果后端已部署但发现新默认企业 KMAgent 不可用，应先关闭新入口并恢复旧入口，随后修正默认企业实例配置。
- 若新默认企业 target 验证未通过，不进入正式 cutover。

## 5. 数据库迁移清单

### 5.1 `enterprises`

新增系统内置企业：

```text
id = EVO_MIND_CONSUMER_ENTERPRISE_ID
name = EvoMind C端企业
slug = evomind-consumer
status = active
isDeleted = false
```

约束：

- `name` 和 `slug` 不能与现有企业冲突。
- 不允许普通删除。

### 5.2 `enterprise_memberships`

为原默认空间用户创建默认企业成员。

字段建议：

```text
enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID
userId = 原用户 ID
role = member
status = active / disabled / pending / rejected
joinedAt = 原 agent 创建时间或审核通过时间
```

### 5.3 `enterprise_openclaw_instances`

创建默认企业实例。

字段来源：

```text
enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID
instanceKey = default
kmAgentBaseUrl = 当前默认空间实际解析出的 baseUrl
gatewayBaseUrl = 默认企业实例实际使用的 gateway base url，如有
gatewayTokenEncrypted = 默认企业实例 token 加密值
sharedWorkspacePrimary = true
status = active
```

说明：

- 可以沿用当前默认空间实际解析出的 baseUrl/token，也可以配置新的 C 端企业实例。
- 若配置新实例，历史默认空间 workspace 不可见是可接受结果。

### 5.4 `zclaw_agent_instances`

旧默认空间实例不再要求原地迁移。

推荐：

- 保留 `scope="personal" AND enterpriseOpenClawInstanceId IS NULL` 的旧行作为归档数据。
- 可选在 `metadata` 增加归档标记，便于后续清理。
- 新 C 端企业 agent 由企业 bootstrap 逻辑创建。

新建或绑定企业 agent 时应满足：

- `scope = "enterprise"`
- `enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID`
- `enterpriseOpenClawInstanceId = 默认企业实例 ID`
- `metadata` 中补齐企业信息

不再保证：

- 旧 `agentId` 不变。
- 旧 `workspacePath` 可见。
- 旧 `zclaw_sessions.agentInstanceId` 继续用于主业务读取。

### 5.5 `zclaw_workspace_quota_configs`

默认空间配额可丢弃或归档。

推荐：

- 默认企业使用统一 C 端企业配额策略。
- 如需保留特殊 quota，只迁明确需要保留的用户，不作为默认要求。

可丢弃：

- `scope="personal" AND enterpriseOpenClawInstanceId IS NULL` 的旧 quota。

### 5.6 `zclaw_workspace_child_orders`

默认空间排序可丢弃或归档。

新写入要求：

- `enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID`

可丢弃：

- `enterpriseId=""` 的旧排序记录。

### 5.7 `zclaw_file_shares`

默认空间分享可失效、归档或后续按需重建。

新写入要求：

- `enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID`

不再保证：

- 旧默认空间分享链接继续可访问。
- 旧分享项路径继续指向可读文件。

### 5.8 `enterprise_ragflow_configs`

旧数据处理：

- `enterpriseId="-1"` 可归档，不要求迁移。

新写入要求：

- 为 `EvoMind C端企业` 创建真实企业 ID 的 RagFlow 配置。
- 后续配置读写必须使用真实企业 ID。

### 5.9 `ragflow_datasets`

旧数据处理：

- `enterpriseId="-1"` 的旧 dataset 可归档或逻辑隐藏。

新写入要求：

- 新 dataset 必须使用 `enterpriseId=EVO_MIND_CONSUMER_ENTERPRISE_ID`。

说明：

- 新 `scope="personal"` 仍可表示个人知识库 dataset。
- 新 `scope="enterprise"` 表示企业共享知识库 dataset。
- 两者都必须挂真实默认企业 ID。

### 5.10 `ragflow_documents` / `ragflow_sync_jobs` / `ragflow_graph_jobs`

旧数据处理：

- `enterpriseId="-1"` 相关 document/job 可归档、取消或逻辑隐藏。
- 不要求迁移 JSON payload / metadata 中的旧 `enterpriseId="-1"`。

新写入要求：

- 新 document/job 必须使用真实默认企业 ID。
- 不得再生成 `enterpriseId="-1"`。

## 6. KMAgent 验证清单

### 6.1 样本用户选择

至少选择以下用户：

- 一个 active 默认空间老用户。
- 一个有历史会话的老用户，用于确认历史会话丢弃影响面。
- 一个有个人知识库文件的老用户，用于确认历史知识库丢弃影响面。
- 一个 workspace 文件较多的老用户，用于确认历史文件丢弃影响面。
- 一个 disabled 默认空间用户。

### 6.2 迁移前验证

旧默认 target 下记录：

- 实际解析出的 default target baseUrl。
- 实际使用的 token 来源，当前应为 `ZCLAW_GATEWAY_TOKEN`。
- 旧 workspace usage、文件树、会话数量、RagFlow document 状态、知识图谱状态。
- 以上记录只用于确认丢弃影响面，不作为迁移一致性验收。

### 6.3 新默认企业 target 可用性验证

将临时 enterprise target 指向即将用于 `EvoMind C端企业` 的 KMAgent/Gateway baseUrl/token，验证：

- 默认企业实例配置的 baseUrl/token 可用。
- bootstrap 可成功返回 enterprise agent。
- workspace usage 可读取。
- 文件树根目录可读取。
- 新会话可创建或读取。
- 新文件上传、读取、删除链路可用。
- 如果使用新 KMAgent 实例，历史 usage、文件树、会话为空是可接受结果。

### 6.4 失败判断

以下任一情况必须停止：

- 新默认企业 target bootstrap 失败。
- workspace usage 或文件树基础接口失败。
- 新会话创建或读取失败。
- token 或 gateway 配置导致访问失败。
- 旧默认空间 target 与新默认企业 target 混用，导致新数据仍写回 personal/default 口径。

## 7. 前端替换清单

### 7.1 必改语义

迁移前：

```text
enterpriseId = ""       -> 默认空间
enterpriseId = "-1"     -> 默认空间 RagFlow / 图谱
```

迁移后：

```text
enterpriseId = EVO_MIND_CONSUMER_ENTERPRISE_ID -> EvoMind C端企业
```

### 7.2 必查代码模式

执行阶段必须扫描并处理：

```bash
rg "默认空间|activeEnterpriseId \\|\\| '-1'|activeEnterpriseId \\|\\| \"-1\"|enterpriseId: '-1'|enterpriseId: \"-1\"|getActiveEnterpriseId\\(\\) \\|\\| ''|hasDefaultInstance" apps/web/src
```

### 7.3 UI 文案

替换规则：

- 空间名称：`默认空间` -> `EvoMind C端企业`
- 管理页字段：`默认空间状态` -> `C端企业状态` 或 `EvoMind C端企业状态`
- RagFlow：`默认空间 ID` -> `企业 ID`
- 错误信息：`默认空间已禁用` -> `EvoMind C端企业账号已禁用`

### 7.4 active enterprise 初始化

要求：

- 登录后若无用户选择，先调用 `GET /api/enterprises/consumer/membership`。
- 如果 C 端企业 membership 为 active，使用接口返回的 `enterprise.id` 设置 active enterprise。
- 如果没有 C 端 active membership，但用户有其他 active B 端企业，使用第一个 active B 端企业。
- 如果没有任何 active 企业，展示 C 端企业申请/待审核/禁用状态页。
- localStorage 不再用空字符串代表默认空间。
- 企业列表中必须包含 `EvoMind C端企业`。
- 用户切换 B 端企业后，仍保留真实企业 ID。

## 8. 后端替换清单

### 8.1 必改文件

- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/enterprises/enterprise.service.ts`
- `apps/api/src/zclaw/zclaw-km-agent.client.ts`
- `apps/api/src/zclaw/zclaw-enterprise-id.util.ts`
- `apps/api/src/zclaw/ragflow/ragflow.service.ts`
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts`
- `apps/api/src/admin-users/admin-users.service.ts`
- `packages/db/prisma/schema.prisma`

### 8.2 必查代码模式

执行阶段必须扫描：

```bash
rg "DEFAULT_RAGFLOW_ENTERPRISE_ID|ZCLAW_SCOPE_PERSONAL|DEFAULT_SPACE_DISABLED_MESSAGE|enterpriseOpenClawInstanceId: null|scope: ZCLAW_SCOPE_PERSONAL|scope: 'personal'|enterpriseId.*-1|defaultSpace" apps/api/src packages/db/prisma
```

说明：

- `scope="personal"` 如果是 RagFlow 个人知识库 dataset，可保留。
- `scope="personal"` 如果表示默认空间 Agent、配额、访问控制，必须删除或替换。

## 9. 验收标准

### 9.1 用户账号与入口无感

- 老用户无需重新申请。
- 老用户登录后直接看到 `EvoMind C端企业`。
- 老用户可以在 `EvoMind C端企业` 中创建新会话、使用新工作区、上传新知识库文件。
- 历史默认空间文件、会话、个人知识库、知识图谱、分享、排序、个性化配额不承诺可见。
- disabled 用户仍不可使用 C 端企业能力。

### 9.2 新数据口径一致

- 新 C 端 agent 使用 `scope="enterprise"` 和默认企业真实 ID。
- 新会话绑定默认企业 enterprise agent。
- 新 workspace quota/order/share 写入默认企业上下文。
- 新 RagFlow dataset/document/job 写入默认企业真实 ID。
- 旧默认空间数据可保留归档，但不再进入主业务查询和写入。

### 9.3 新逻辑干净

- 新用户不再创建默认空间 personal agent。
- 新 RagFlow 数据不再写入 `-1`。
- 前端不再发送空 enterpriseId 或 `-1`。
- 后端不再把缺 enterpriseId 静默解释为默认空间。
- 默认空间文案从主业务 UI 消失。

### 9.4 B 端企业不受影响

- B 端企业成员列表正常。
- B 端企业实例池分配正常。
- B 端共享工作区正常。
- B 端 RagFlow 配置和知识图谱正常。
- B 端配额和 token batch 正常。

## 10. 推荐执行顺序

1. 补充并运行 preflight 审计脚本。
2. 验证新默认企业 target 可用。
3. 新增默认企业和默认企业实例。
4. 迁移 membership。
5. 切换 agent instance 主链路，不再创建 personal agent。
6. 重置 workspace quota/order/share 新写入路径。
7. 重置 RagFlow 和知识图谱新写入路径。
8. 后端切换到真实企业主链路。
9. 前端切换到真实默认企业 ID。
10. 删除默认空间旧逻辑和旧文案。
11. 运行一致性校验。
12. 灰度或维护窗口 cutover。
13. 观察并确认无旧口径新写入。

## 11. 后续执行注意事项

- 这是长任务，不建议一次提交完成所有代码。
- 每个阶段都要有独立 PR 或至少独立 commit。
- 数据初始化使用 Prisma migration SQL；提交前必须人工审查 SQL，确认不包含旧资产清理语句。
- 正式切换前必须导出 preflight 审计报告，确认默认空间历史资产可丢弃范围。
- 每次阶段完成后都要执行针对该阶段的一致性校验。
- 最后阶段才删除旧默认空间入口，避免开发过程中缺少对照；但 cutover 后旧入口必须关闭。

## 12. 关键路径索引

后续执行者重点阅读：

- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/enterprises/enterprise.service.ts`
- `apps/api/src/zclaw/zclaw-km-agent.client.ts`
- `apps/api/src/zclaw/ragflow/ragflow.service.ts`
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts`
- `apps/api/src/admin-users/admin-users.service.ts`
- `packages/db/prisma/schema.prisma`
- `apps/web/src/hooks/useActiveEnterpriseSpace.ts`
- `apps/web/src/components/zclaw/ZclawShell.tsx`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`

## 13. 当前已落地实现同步

本章节同步当前代码已经调整过的内容，后续继续实施时以本章节作为最新口径。历史方案中关于“成员空间用量直接批量请求 KMAgent”或“初始化成员空间用量按钮”的描述已经被替换。

### 13.1 企业空间容量模型

空间容量已经按企业语义拆分：

- 企业共享空间容量配置在 `enterprise_openclaw_instances.sharedWorkspaceQuotaBytes`。
- 企业成员默认个人空间容量配置在 `enterprise_workspace_quota_configs.memberDefaultWorkspaceQuotaBytes`，默认值为 `10737418240`，即 10GB。
- 单个成员个人空间覆盖容量配置在 `enterprise_memberships.workspaceQuotaBytes`。
- 旧 `zclaw_workspace_quota_configs` 只作为历史兼容模型，不再作为企业成员个人空间容量主模型。

前端入口当前口径：

- “成员默认配额”页面包含两个真实表格列：`成员默认额度` 和 `成员默认个人空间容量`。
- 个人空间容量输入不直接要求用户填写字节，而是使用数值 + 单位输入，支持 `TB / GB / MB`，默认单位为 `GB`。
- “成员默认个人空间容量”保存时仍以 bytes 字符串写入后端，避免新增单位字段。
- “成员管理”页面的成员行展示个人空间容量上限来源：继承企业默认或单独设置。

### 13.2 成员空间用量展示口径

成员列表展示的个人空间用量不再实时批量请求 KMAgent。当前设计改为本地快照：

- 新增 `enterprise_member_workspace_usage_snapshots` 保存成员空间用量快照。
- 成员列表 usage 接口只读数据库快照，并结合当前企业默认容量和成员覆盖容量计算 `effectiveQuotaBytes`、`remainingBytes`、`isOverLimit`。
- 没有快照时展示为 `未同步 / 上限`。
- 快照状态为 `missing` 时展示为 `未初始化空间 / 上限`。
- 快照状态为 `error` 时展示为 `用量读取失败 / 上限`。
- 快照状态为 `ok` 且 `usageAvailable=true` 时展示真实 `已用 / 上限`。

单位展示规则：

- 容量展示必须自动换算为 `B / KB / MB / GB / TB`。
- 只有小于 1KB 时才展示 `B`。
- 示例：`0B`、`512KB`、`10MB`、`1.25GB`、`2TB`。
- 不允许在成员列表中展示大段裸字节数字。

### 13.3 成员空间用量刷新任务

当前已经废弃“初始化成员空间用量”同步按钮。新的刷新方式是异步任务：

- 系统管理员创建任务：`POST /api/zclaw/admin/enterprise-workspace-usages/refresh-jobs?enterpriseId=...`
- 系统管理员查询任务：`GET /api/zclaw/admin/enterprise-workspace-usages/refresh-jobs/:jobId`
- 组织管理员创建任务：`POST /api/zclaw/enterprise-admin/workspace-usages/refresh-jobs?enterpriseId=...`
- 组织管理员查询任务：`GET /api/zclaw/enterprise-admin/workspace-usages/refresh-jobs/:jobId`

任务数据表：

- `enterprise_workspace_usage_refresh_jobs`
- `enterprise_workspace_usage_refresh_job_items`

任务行为：

- 创建任务接口立即返回 `{ jobId/status/progress }`，不等待 KMAgent 全量刷新完成。
- 同一企业同一时间只允许一个 `pending/running` 任务；重复创建时返回已有任务。
- 后端进程内异步执行任务，默认并发为 5。
- 任务只处理 `enterprise_memberships.status='active'` 的成员；非 active 成员计入 skipped。
- 单个成员失败不终止整个任务，失败原因写入任务明细。
- 每处理一个成员，都会 upsert `enterprise_member_workspace_usage_snapshots`。
- token、实例配置或 KMAgent 调用失败时，快照写入 `bindingStatus='error'` 和 `lastError`。
- KMAgent 返回 binding 不存在时，快照写入 `bindingStatus='missing'`。

前端行为：

- 成员管理页按钮文案为 `刷新空间用量`。
- 超级管理员必须选择单个企业后才能刷新；未选择或多选企业时按钮禁用，并提示先选择一个企业。
- 组织管理员只刷新当前 active 企业。
- 点击后进入 `刷新中...` 状态，并轮询任务进度。
- 进度展示格式为 `已处理 processedCount/totalCount，失败 failedCount`。
- 任务完成或失败后自动重新加载成员空间用量快照。

### 13.4 用户自身使用空间时的快照更新

当用户在企业上下文中正常读取个人 workspace usage 时：

- 后端会 best-effort 更新 `enterprise_member_workspace_usage_snapshots`。
- 更新快照失败只记录 warn 日志，不影响用户正常使用空间。
- 这样活跃用户的用量会自然刷新；管理员列表只需要读取本地快照。

后续如果需要更实时的快照，可继续在文件上传、删除、移动、复制等 workspace 写操作成功后刷新当前用户快照。

### 13.5 相关代码和迁移文件

当前已涉及的关键文件：

- `packages/db/prisma/schema.prisma`
- `packages/db/prisma/migrations/20260701170000_add_enterprise_workspace_usage_snapshots/migration.sql`
- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/zclaw-admin.controller.ts`
- `apps/api/src/zclaw/zclaw.controller.ts`
- `apps/web/src/api/moudles/zclaw.ts`
- `apps/web/src/app/(zclaw-shell)/admin/conversation-quota/page.tsx`
- `apps/web/src/app/(zclaw-shell)/admin/enterprise-memberships/page.tsx`
- `apps/web/src/components/admin/StorageQuotaInput.tsx`

### 13.6 当前验证状态

已完成验证：

- `prisma validate --schema packages/db/prisma/schema.prisma` 通过。
- `pnpm --filter @insightweaver/api build` 通过。
- `git diff --check` 通过。

当前已知阻塞：

- `prisma generate` 在本地 Windows 环境出现 `EPERM rename query_engine-windows.dll.node`，属于 Prisma query engine 文件锁问题。
- `pnpm --filter @insightweaver/web build` 仍被既有缺失依赖阻塞：`enterprise-departments/_components/departmentGroupExport.ts` 找不到 `exceljs`。

常见模式：

```ts
activeEnterpriseId || undefined
activeEnterpriseId || "-1"
getActiveEnterpriseId() || "none"
```

迁移后：

- active enterprise 不能再为空。
- C 端默认值必须是 `EvoMind C端企业` 的真实企业 ID。
- 前端不得再发送空企业 ID 或 `-1` 来表达 C 端空间。

## 14. 方案审查补全与防漏清单

本章节用于回答“默认空间改成 EvoMind C 端企业，到底还要改什么”，也用于后续 PR 审查。任何阶段如果没有通过本章节对应验收，不应认为默认空间企业化已经完成。

### 14.1 当前结论

当前已经落地较多的是“企业成员个人空间容量”和“成员个人空间用量快照”相关能力；这部分属于 Step 5 的容量模型子任务。

但默认空间彻底企业化还没有完全结束，原因是代码中仍存在以下旧口径：

- 前端仍存在空 `activeEnterpriseId` 表示默认空间的逻辑。
- 前端仍存在 `activeEnterpriseId || undefined`、`activeEnterpriseId || "-1"`、`getActiveEnterpriseId() || "none"` 等模式。
- RagFlow / 知识图谱代码和测试中仍存在 `DEFAULT_RAGFLOW_ENTERPRISE_ID = "-1"`。
- 管理后台仍有“默认空间”文案和默认空间启用/禁用入口。
- `zclaw_workspace_child_orders.enterpriseId` schema 默认值仍是空字符串。
- `zclaw_file_shares.enterpriseId` schema 仍允许 `NULL`。
- 后端部分写库逻辑仍直接使用 `readEnterpriseId(req)` 原始值，而不是使用“最终解析后的默认企业 ID”。

因此，当前状态只能认为：

- 企业容量模型子任务基本可验收。
- 默认空间替换为 EvoMind C 端企业的全链路尚未完成。
- order/share/RagFlow/前端 active enterprise/管理后台旧入口仍需要继续闭环。

### 14.2 order 和 share 是什么

`order` 在本文档中指 `workspace child order`，即工作区文件树排序。

用户在个人工作区或企业共享工作区里看到文件夹、文件、知识库目录时，前端需要一个稳定顺序。这个顺序不是 KMAgent 文件本身的一部分，而是业务库中的 UI 偏好记录：

- 表：`zclaw_workspace_child_orders`
- 关键字段：
  - `userId`：个人工作区排序时通常为当前用户。
  - `enterpriseId`：企业上下文 ID。旧默认空间可能是空字符串。
  - `source`：`workspace` 或 `shared-workspace`。
  - `parentKey`：父目录标识。
  - `childPath`：子节点路径。
  - `sortOrder`：排序值。

`share` 在本文档中指文件分享链接。

用户把工作区文件或文件夹生成分享链接时，业务库保存分享配置和分享条目：

- 表：`zclaw_file_shares`
- 表：`zclaw_file_share_items`
- 关键字段：
  - `zclaw_file_shares.enterpriseId`：分享所属企业上下文。旧默认空间可能是 `NULL`。
  - `ownerUserId`：分享创建者。
  - `publicId`：对外分享 ID。
  - `source`：分享条目来自个人工作区还是共享工作区。
  - `path`：分享条目路径。

本次切换不要求迁移旧排序和旧分享，但必须保证切换后新排序和新分享都写入 `EVO_MIND_CONSUMER_ENTERPRISE_ID`。

### 14.3 统一上下文规则

上线后必须只存在以下企业上下文语义：

```text
C 端默认企业 = EVO_MIND_CONSUMER_ENTERPRISE_ID
B 端企业 = 用户显式选择的真实 enterpriseId
RagFlow 个人知识库 scope = personal，但 enterpriseId 仍然是真实企业 ID
RagFlow 企业知识库 scope = enterprise，enterpriseId 仍然是真实企业 ID
```

禁止继续使用以下语义：

```text
enterpriseId = ""       表示默认空间
enterpriseId = NULL     表示默认空间
enterpriseId = "-1"     表示默认空间 RagFlow / 图谱
scope = "personal"      表示默认空间 Agent
```

后端推荐新增或统一使用一个“业务上下文解析”方法：

```text
resolveEffectiveEnterpriseId(req/userId/explicitEnterpriseId)
```

规则：

1. 如果请求显式传入 B 端企业 ID，使用该 ID，并校验用户是 active membership。
2. 如果没有显式企业 ID，使用 `EVO_MIND_CONSUMER_ENTERPRISE_ID`。
3. 如果用户不是默认企业 active membership，返回未开通、待审核、已拒绝或已禁用。
4. 所有 workspace、session、agent、quota、order、share、RagFlow 写库逻辑都使用解析后的 effective enterprise ID。
5. `readEnterpriseId(req)` 只能作为读取原始入参的工具，不能直接代表最终业务企业 ID。

### 14.4 后端必改域

#### 14.4.1 企业 target 和 agent 主链路

关键文件：

- `apps/api/src/enterprises/enterprise.service.ts`
- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/interceptors/zclaw-enterprise-context.interceptor.ts`
- `apps/api/src/zclaw/zclaw-enterprise-id.util.ts`

必须满足：

- 无显式 enterpriseId 的 C 端请求解析到 `EVO_MIND_CONSUMER_ENTERPRISE_ID`。
- C 端用户必须通过默认企业 membership 校验。
- C 端新建 agent 必须是 `zclaw_agent_instances.scope="enterprise"`。
- C 端新建 agent 必须写入 `enterpriseId=EVO_MIND_CONSUMER_ENTERPRISE_ID`。
- C 端新建 agent 必须绑定 `enterpriseOpenClawInstanceId`。
- 不再创建 `scope="personal" AND enterpriseOpenClawInstanceId IS NULL` 的默认空间 agent。

#### 14.4.2 准入和管理状态

关键文件：

- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/zclaw-admin.controller.ts`
- `apps/api/src/admin-users/admin-users.service.ts`

必须满足：

- 默认空间申请、审批、拒绝、启用、禁用语义切到 `enterprise_memberships`。
- `zclaw_access_requests` 可保留为历史申请记录或兼容入口，但不能继续作为 C 端能否进入的唯一主判断。
- 管理后台用户列表中的默认空间状态应改为默认企业 membership 状态。
- disabled/rejected/pending 用户不能通过缺省企业 ID 绕过校验。

#### 14.4.3 工作区文件和会话

关键文件：

- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/zclaw.controller.ts`

必须满足：

- C 端个人工作区 root、children、path、file-content、file-raw、upload、create file、create folder、rename、delete 都使用默认企业 target。
- 新会话、chat binding、message 必须绑定默认企业 enterprise agent。
- 旧 personal agent 的历史会话可不可见，不作为失败条件。
- `workspace usage` 返回和快照更新使用新企业容量模型。

#### 14.4.4 工作区排序 order

关键文件：

- `apps/api/src/zclaw/zclaw-workspace-child-order.service.ts`
- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/zclaw.controller.ts`
- `apps/web/src/api/moudles/zclaw.ts`
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`

必须满足：

- 个人工作区排序 `source="workspace"` 时，C 端默认企业也必须写真实企业 ID。
- 共享工作区排序 `source="shared-workspace"` 本来就要求企业 ID，继续保持。
- `createWorkspaceScope(userId, enterpriseId)` 不能把 C 端默认场景归一化为空字符串。
- 前端获取和保存排序请求必须携带真实 active enterprise header，或由全局 active enterprise 保证不是空字符串。
- 旧 `enterpriseId=""` 排序记录可保留归档，不迁移。

验收 SQL：

```sql
-- cutover 后不允许新写入空企业排序
SELECT COUNT(*)::bigint AS new_empty_enterprise_order_count
FROM zclaw_workspace_child_orders
WHERE "enterpriseId" = ''
  AND "createdAt" >= :cutover_at;

-- C 端默认企业应能写入排序
SELECT COUNT(*)::bigint AS consumer_enterprise_order_count
FROM zclaw_workspace_child_orders
WHERE "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND "createdAt" >= :cutover_at;
```

#### 14.4.5 文件分享 share

关键文件：

- `apps/api/src/zclaw/zclaw-file-share.controller.ts`
- `apps/api/src/zclaw/zclaw-file-share.service.ts`
- `apps/web/src/api/moudles/zclaw.ts`
- `apps/web/src/components/zclaw/share/FileShareDialog.tsx`
- `apps/web/src/components/zclaw/share/ShareCopyDestinationDialog.tsx`
- `apps/web/src/components/zclaw/share/PublicFileSharePage.tsx`

必须满足：

- C 端创建分享时 `zclaw_file_shares.enterpriseId` 必须是真实默认企业 ID。
- C 端编辑分享时不能把已有企业 ID 清成 `NULL`。
- C 端复制分享到个人工作区时，目标 workspace 必须是默认企业 target。
- 分享读取文件时，优先使用分享记录上的 `enterpriseId` 解析 owner target。
- 旧 `enterpriseId IS NULL` 分享可失效、归档或按需重建，不作为上线失败条件。

验收 SQL：

```sql
-- cutover 后不允许新建 NULL 企业分享
SELECT COUNT(*)::bigint AS new_null_enterprise_share_count
FROM zclaw_file_shares
WHERE "enterpriseId" IS NULL
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

-- C 端默认企业应能创建分享
SELECT COUNT(*)::bigint AS consumer_enterprise_share_count
FROM zclaw_file_shares
WHERE "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;
```

#### 14.4.6 RagFlow 和知识图谱

关键文件：

- `apps/api/src/zclaw/ragflow/ragflow.service.ts`
- `apps/api/src/zclaw/ragflow/ragflow-graph.service.ts`
- `apps/api/src/zclaw/zclaw-ragflow.controller.ts`
- `apps/web/src/components/super-lobster/KnowledgeBaseSidebarSection.tsx`
- `apps/web/src/components/super-lobster/KnowledgeGraphExplorer.tsx`
- `apps/web/src/app/(zclaw-shell)/admin/ragflow/page.tsx`
- `apps/web/src/app/(zclaw-shell)/admin/ragflow/jobs/page.tsx`

必须满足：

- 不再用 `DEFAULT_RAGFLOW_ENTERPRISE_ID="-1"` 表达 C 端默认空间。
- 新 config、dataset、document、sync job、graph job 全部写真实默认企业 ID。
- `scope="personal"` 可以保留为“个人知识库”语义，但必须挂在真实企业 ID 下。
- 管理后台 RagFlow 页面不再显示“默认空间 ID”。
- 测试中的 `enterpriseId="-1"` 用例要改成真实默认企业 ID 或标记为历史归档场景。

验收 SQL：

```sql
SELECT COUNT(*)::bigint AS new_default_ragflow_dataset_count
FROM ragflow_datasets
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

SELECT COUNT(*)::bigint AS new_default_ragflow_graph_job_count
FROM ragflow_graph_jobs
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at;
```

#### 14.4.7 容量、用量和刷新任务

关键文件：

- `packages/db/prisma/schema.prisma`
- `apps/api/src/zclaw/zclaw.service.ts`
- `apps/api/src/zclaw/zclaw-admin.controller.ts`
- `apps/web/src/app/(zclaw-shell)/admin/conversation-quota/page.tsx`
- `apps/web/src/app/(zclaw-shell)/admin/enterprise-memberships/page.tsx`
- `apps/web/src/components/admin/StorageQuotaInput.tsx`

必须满足：

- 企业共享空间容量使用 `enterprise_openclaw_instances.sharedWorkspaceQuotaBytes`。
- 企业成员默认个人空间容量使用 `enterprise_workspace_quota_configs.memberDefaultWorkspaceQuotaBytes`。
- 成员覆盖容量使用 `enterprise_memberships.workspaceQuotaBytes`。
- 成员列表只读 `enterprise_member_workspace_usage_snapshots`，不在打开列表时批量打 KMAgent。
- 刷新空间用量必须是单企业异步任务，不能支持超管全系统一键刷新。
- 用量展示必须自动换算单位，不能展示裸字节长数字。

### 14.5 前端必改域

关键目标：前端不能再把空字符串当作 C 端默认空间。

必须检查：

- `apps/web/src/lib/enterprise-context.ts`
- `apps/web/src/hooks/useActiveEnterpriseSpace.ts`
- `apps/web/src/components/zclaw/ZclawShell.tsx`
- `apps/web/src/components/zclaw/ZclawChatProvider.tsx`
- `apps/web/src/components/zclaw/ZclawWorkspaceSidebar.tsx`
- `apps/web/src/components/super-lobster/SuperLobsterPage.tsx`
- `apps/web/src/api/moudles/zclaw.ts`
- dashboard hooks
- admin users/access/ragflow/quota/membership pages

必须满足：

- 登录后如果用户有默认企业 active membership，active enterprise 初始化为 consumer membership 接口返回的真实企业 ID。
- localStorage 中不再用缺失值或空字符串代表默认空间。
- 企业切换器显示 `EvoMind C端企业`，而不是“默认空间”。
- 所有 `/api/zclaw` 主业务请求都能带上真实企业上下文。
- `skipEnterpriseContext` 只允许用于登录、公开分享详情、访问状态等确实不应带企业上下文的接口。
- 搜索以下模式必须逐项解释或删除：

```bash
rg "默认空间|activeEnterpriseId \\|\\| undefined|activeEnterpriseId \\|\\| '-1'|activeEnterpriseId \\|\\| \"-1\"|getActiveEnterpriseId\\(\\) \\|\\| 'none'|hasDefaultInstance" apps/web/src
```

### 14.6 数据库和 migration 必改域

必须包含的初始化 SQL：

- 固定插入 `enterprises.id = '00000000-0000-0000-0000-000000000001'`。
- 固定插入默认企业主实例 `enterprise_openclaw_instances.instanceKey='default'`。
- 默认实例 token 可先用占位值，但后端必须识别占位值并返回明确错误。
- 批量把旧默认空间可进入用户写入 `enterprise_memberships`。

可以不迁移的历史数据：

- 旧 personal agent。
- 旧 session/message/chat binding。
- 旧 workspace 文件。
- 旧 `zclaw_workspace_quota_configs` personal 配置。
- 旧 `zclaw_workspace_child_orders.enterpriseId=''`。
- 旧 `zclaw_file_shares.enterpriseId IS NULL`。
- 旧 `enterpriseId='-1'` RagFlow/graph 数据。

不允许的 migration 行为：

- 不允许删除旧历史资产。
- 不允许写入真实 token 明文或真实 token 密文到仓库。
- 不允许修改 B 端企业 membership、实例、RagFlow 数据。
- 不允许通过 SQL 伪造 KMAgent binding 或 enterprise agent 远端状态。

### 14.7 上线前 smoke test

至少覆盖以下路径：

1. C 端老 active 用户登录，默认进入 `EvoMind C端企业`。
2. C 端老 active 用户创建新会话，消息正常发送。
3. C 端老 active 用户打开个人工作区文件树。
4. C 端老 active 用户上传文件、创建文件夹、重命名、删除。
5. C 端老 active 用户调整文件树顺序，确认 order 写默认企业 ID。
6. C 端老 active 用户创建分享，确认 share 写默认企业 ID。
7. C 端老 active 用户复制公开分享到个人工作区，确认文件进入默认企业 target。
8. C 端用户上传知识库文件，确认 RagFlow dataset/document/job 写默认企业 ID。
9. C 端用户打开知识图谱，确认不再使用 `-1`。
10. C 端 disabled 用户登录后不能进入默认企业能力。
11. B 端用户切换到真实企业，个人工作区、共享工作区、分享、RagFlow 均正常。
12. 平台管理员进入成员管理，查看空间用量，刷新单企业空间用量任务。
13. 组织管理员进入成员管理，只能管理当前企业。

### 14.8 切换后一致性 SQL 总表

```sql
-- 1. cutover 后不应新增旧默认 personal agent
SELECT COUNT(*)::bigint AS new_personal_agent_count
FROM zclaw_agent_instances
WHERE scope = 'personal'
  AND "enterpriseOpenClawInstanceId" IS NULL
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

-- 2. cutover 后 C 端新 agent 应为 enterprise scope
SELECT COUNT(*)::bigint AS consumer_enterprise_agent_count
FROM zclaw_agent_instances
WHERE scope = 'enterprise'
  AND "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

-- 3. cutover 后不应新增空企业排序
SELECT COUNT(*)::bigint AS new_empty_order_count
FROM zclaw_workspace_child_orders
WHERE "enterpriseId" = ''
  AND "createdAt" >= :cutover_at;

-- 4. cutover 后不应新增 NULL 企业分享
SELECT COUNT(*)::bigint AS new_null_share_count
FROM zclaw_file_shares
WHERE "enterpriseId" IS NULL
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

-- 5. cutover 后不应新增 -1 RagFlow dataset
SELECT COUNT(*)::bigint AS new_minus_one_dataset_count
FROM ragflow_datasets
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at
  AND "isDeleted" = false;

-- 6. cutover 后不应新增 -1 graph job
SELECT COUNT(*)::bigint AS new_minus_one_graph_job_count
FROM ragflow_graph_jobs
WHERE "enterpriseId" = '-1'
  AND "createdAt" >= :cutover_at;

-- 7. 默认企业 membership 应存在
SELECT status, COUNT(*)::bigint AS count
FROM enterprise_memberships
WHERE "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND "isDeleted" = false
GROUP BY status
ORDER BY status;

-- 8. 默认企业主实例必须存在且唯一
SELECT COUNT(*)::bigint AS primary_instance_count
FROM enterprise_openclaw_instances
WHERE "enterpriseId" = '<EVO_MIND_CONSUMER_ENTERPRISE_ID>'
  AND "sharedWorkspacePrimary" = true
  AND status = 'active'
  AND "isDeleted" = false;
```

验收要求：

- 查询 1、3、4、5、6 结果必须为 0。
- 查询 2 应随着 C 端用户进入逐步增加。
- 查询 7 应覆盖旧默认空间可进入用户。
- 查询 8 必须等于 1。

### 14.9 当前未闭环事项

截至本次文档审查，以下事项不应标记为完成：

- 前端 active enterprise 空字符串语义完全删除。
- 前端所有 `-1` 默认空间 RagFlow/图谱语义完全删除。
- 后端 `readEnterpriseId(req)` 原始值和 effective enterprise ID 的写库语义完全统一。
- `zclaw_workspace_child_orders` 新写入空 enterpriseId 的风险完全消除。
- `zclaw_file_shares` 新写入 `NULL` enterpriseId 的风险完全消除。
- 管理后台“默认空间”文案和默认空间启停入口完全替换。
- RagFlow / 知识图谱 `DEFAULT_RAGFLOW_ENTERPRISE_ID="-1"` 主业务路径完全替换。

### 14.10 PR 拆分建议

推荐后续按以下 PR 顺序推进：

1. 默认企业常量、effective enterprise ID 解析和后端上下文统一。
2. 前端 active enterprise 默认值改为真实默认企业 ID。
3. agent/session/workspace 主链路切到默认企业。
4. order/share 新写入路径闭环。
5. RagFlow/知识图谱 `-1` 替换。
6. 管理后台默认空间文案、状态和启停入口替换。
7. 容量模型和成员用量快照最终验收。
8. 全量一致性 SQL、smoke test、cutover 文档和回滚预案确认。
