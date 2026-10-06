# EvoMind 全量数据：缺口与补交来源审计

日期：2026-10-05。范围：只读两个用户给定导出包及 InsightWeaver 本地源码；没有连接生产库，没有调用模型，没有调用 KM，没有补造历史数据。

## 1. 本轮确认的来源和数据边界

原始包：`C:/Users/39835/Downloads/zkys-raw-export-20260925/`。README 第3–20行说明从生产库只读导出：37名当前企业成员、1,524条会话、46,407条用户/助手/系统消息，另附1,391条工具结构样本；约9.3万条全量 tool/toolResult 明确未导。附件二进制未导。会话归属通过成员 userId 筛选，不是通过会话 enterpriseId。

第二个挖掘包没有 README。`pull.mjs:26–58`、`pull-msgs.mjs:8–21`证实从 PostgreSQL 的 `insight_weaver_prod` 拉取成员、会话、用户消息；`clean.mjs:16–25`证实 `skill_installs.json` 仅为用户文本中的安装意图，`skill_invokes.json` 仅为用户文本中的技能选择前缀计数。它们不能证明安装成功、真实消费或用了哪个版本。相关下载脚本有硬编码连接凭据，本报告不复制、不使用；数据方应走既有只读账号和环境变量。

本轮逐行解析原始JSONL，只输出结构计数，未输出企业正文：

| 原包字段覆盖 | 计数 | 解释 |
|---|---:|---|
| 用户消息 | 8,856行 | 含UUID/trusted副本，未作最终去重 |
| 助手消息 | 37,533行 | 其中done 37,380 / error 59 / aborted 86 / streaming 8 |
| 用户消息有非空files | 1,026行 | 涉及442个session，不等于独立附件数 |
| 用户文件引用 | 1,666项 | 23项没有path；重复副本未去重 |
| 助手消息有非空files | 88行/112项 | 产物线索，不代表完整成果库 |
| rawPayload有toolActivity | 2,423行 | user 623、assistant 1,800，属于载荷内已有零散快照 |
| 独立工具样本 | 1,391行 | tool 1,369 / toolResult 22，只是抽样 |
| rawPayload有runId | 21行 | 不足以覆盖全部请求和重试 |

原包 session 还带 `skillLearningEnabled/skillLearningExcludedAt/skillLearningExcludedBy`，当前本地 `ZclawSession` schema 没有这三列。这是生产导出与本地源码存在差异的证据，不能认为本地schema完全代表2026-09-25生产版本。补交前先查实际schema。

## 2. 数据方应补什么、从哪里取

| 优先级与缺口 | 已核实来源 | 关联方式与交付要求 |
|---|---|---|
| P0 用户上传文件的实际内容 | PG `zclaw_messages.rawPayload.files`给name/path/source/mimeType/sizeBytes；字节在KM用户工作区，客户端已提供 workspace/shared-workspace 文件content接口 | 用 `sessionId + messageId + userId + source + path` 建清单；按对应企业实例/用户取文件字节，交付文件、SHA256、大小、获取时间、是否历史快照；缺文件逐项列NOT_FOUND/DELETED/PATH_MISSING，不删除会话 |
| P0 AI产物的实际内容与历史修改 | PG `generated_artifacts`给sessionId/filePath/fileName/outputType/generatedAt/skillId；实际文件在个人工作区磁盘，经KM接口读 | 保留每次生成/修订的版本、会话/消息/run对应、hash；仅当前文件要明确CURRENT_SNAPSHOT，不能冒充当时输出。该表按企业+用户+路径upsert，会覆盖同路径元数据，不是完整版本表 |
| P0 全量工具调用和返回 | PG `zclaw_messages`中的tool/toolResult和rawPayload.toolActivity；上游KM会话history | 导出全量role及payload；保留toolCallId、name、args、output、error、startedAt/completedAt、原生事件顺序、run/attempt关联。tool.started/complete/failed被本地聚合快照更新，必要时要KM原生日志补齐尝试史 |
| P0 原生时序、回复关联和重试归属 | `zclaw_chat_bindings.sessionId→openclawSessionKey`；KM `/sessions/{sessionKey}/history` | 请求提供带原始数组顺序/日志行号的原生history，以及可取得的原始事件ID、parent/response关系、run/attempt/status。PG消息表无parentId/replyTo/sequence列；不要要求数据方查询不存在的列。内存SSE seq仅缓冲最多500，不是持久历史依据 |
| P0 企业会话归属 | PG `zclaw_agent_instances`、`zclaw_sessions.agentInstanceId`、`enterprise_memberships` | 按实例的scope/enterpriseId/enterpriseOpenClawInstanceId核对成员会话，交付按发生时间的企业/用户映射；当前成员的全部会话可能含个人或其他实例，不要默认全部属于企业 |
| P1 当时实际选中/注入/使用的skills | PG `skill_usage_events`、`human_efficiency_events`；若线上启用trace则 `skill_emergence_observations.evidenceRefs`、`skill_emergence_analysis_snapshots.trace`；KM原生日志 | 区分SELECTED、PROMPT_INJECTED、FILE_READ、SCRIPT_EXECUTED、APPLIED，每条关联request/session/message/run。当前usage表仅在run.completed记录选中技能；新trace的USED=完整SKILL.md已注入提示，不证明模型遵守。2026-09-25线上是否启用这些表/开关未知 |
| P1 技能正文和版本 | KM `/api/km/skills`、`/{id}/bundle`；个人技能 `/api/km/skills/personal/{key}/revisions`；组织PG `skill_submissions/skill_submission_versions`、`enterprise_skill_configs`、`personal_skill_configs` | 交付SKILL.md及scripts/references/assets全包、版本号、bundleHash、生效区间、个人/组织scope、owner、审核版本。当前版本不能自动替代会话发生时版本；缺历史须标UNKNOWN |
| P1 外部资料/知识库内容 | `ragflow_datasets`、`ragflow_documents`、`ragflow_file_blobs`提供mapping/path/contentHash/远端document ID；原会话注入内容及KM工具日志 | 若会话依赖知识库，补当时检索query、命中chunk/文档、文本及hash；PG映射只是来源索引。RagFlow服务内部库/存储未知，应由该服务负责人导出，不能编造其表名 |
| P1 真正验收、采用和失败原因 | 已有对话反馈；业务系统/人工评审结果不在给定包 | 给出目标、验收标准、评价对象（任务/尝试/产物/条款）、结果、评审者角色、时间、证据链接、修改前后关系。用户感谢/助手自述/done不等于业务完成。业务验收库名和表名未提供，须数据方定位实际系统 |
| P2 模型调用、耗时和真实成本 | PG `billing_tasks.rawUsageSnapshot/metadata`、`billing_task_events.eventPayload`、`zclaw_enterprise_token_usage_settlements`，以及上游usage日志 | 补每请求model/provider、输入输出/缓存tokens、retry、起止时间、账单单价/金额。settlement.tokens是计费数量，不能自动认定原生tokens；映射session/run要检查metadata实际结构。调用费用和人工工时若未实测继续未知 |

### 几个必须区分的证据层

- 附件元数据不等于文件内容。`rawPayload.files` 的路径有助回查，不能据此恢复被覆盖或已删文件。
- 有产物目录记录不等于完整生成史。`generated_artifacts` 同路径会更新；应要历史文件/版本或原生manifest，若无则只报告当前快照。
- 用户说“请使用技能”只证明选择/意图；Prompt注入证明提供了技能正文；read/exec证明具体消费动作；任务结果需要另核验。
- `skill_usage_events.savedHours` 和 `human_efficiency_events.savedHours` 不可当实测节省工时。当前 `SkillAnalyticsRecorder` 将固定0.5小时在选中技能间分摊。
- 原包还存在错误/中止/流式状态。不能沿用“导出已全部排除失败”这一先前口头假定。

## 3. 给数据方的可执行导出方式

先使用受控只读账号，参数 `$1` 为企业ID，不在脚本写连接密码。以下SQL基于已核实本地schema；执行前在实际生产库核对列名。已有全量会话的sessionId清单也应附上，以固定2026-09-25快照的目标范围，防止重新按当前成员导致数据漂移。

### 3.1 先核对生产schema

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
    'enterprise_memberships', 'zclaw_sessions', 'zclaw_messages',
    'zclaw_agent_instances', 'zclaw_chat_bindings', 'generated_artifacts',
    'skill_usage_events', 'human_efficiency_events',
    'personal_skill_configs', 'enterprise_skill_configs',
    'skill_submissions', 'skill_submission_versions',
    'skill_emergence_observations', 'skill_emergence_analysis_snapshots',
    'ragflow_datasets', 'ragflow_documents', 'ragflow_file_blobs',
    'billing_tasks', 'billing_task_events',
    'zclaw_enterprise_token_usage_settlements'
  )
ORDER BY table_name, ordinal_position;
```

### 3.2 补身份、会话绑定与完整消息（包括工具和失败）

```sql
WITH members AS (
  SELECT "userId" FROM enterprise_memberships
  WHERE "enterpriseId" = $1 AND "isDeleted" = false
)
SELECT s.id AS "sessionId", s."userId", s."agentInstanceId", s.purpose,
       s."originEnterpriseId", ai."agentId", ai.scope,
       ai."enterpriseId" AS "instanceEnterpriseId", ai."enterpriseOpenClawInstanceId",
       ai."workspacePath", ai."agentDir", b."openclawSessionKey"
FROM zclaw_sessions s
JOIN zclaw_agent_instances ai ON ai.id = s."agentInstanceId"
LEFT JOIN zclaw_chat_bindings b ON b."sessionId" = s.id AND b."isDeleted" = false
WHERE s."userId" IN (SELECT "userId" FROM members) AND s."isDeleted" = false;

-- 此处不先删重、不排除失败、不用正则去掉工具。
WITH members AS (
  SELECT "userId" FROM enterprise_memberships
  WHERE "enterpriseId" = $1 AND "isDeleted" = false
)
SELECT m.*, s."userId"
FROM zclaw_messages m
JOIN zclaw_sessions s ON s.id = m."sessionId"
WHERE s."userId" IN (SELECT "userId" FROM members)
  AND s."isDeleted" = false AND m."isDeleted" = false
ORDER BY m."sessionId", m."createdAt", m.id;
```

这里ORDER BY仅是导出稳定顺序，`createdAt,id`不是历史reply-to真值。保持UUID和trusted双副本，由处理台账统一去重；依靠原生KM history的顺序核验。软删除内容并非本次自动要求；若需它解释断点，由数据方单独确认可交范围并另包。

### 3.3 先交附件清单，再按清单交字节

```sql
WITH members AS (
  SELECT "userId" FROM enterprise_memberships
  WHERE "enterpriseId" = $1 AND "isDeleted" = false
)
SELECT s."userId", m."sessionId", m.id AS "messageId", m."createdAt", f.ordinality AS "fileIndex", f.value AS "fileMetadata"
FROM zclaw_messages m
JOIN zclaw_sessions s ON s.id = m."sessionId"
CROSS JOIN LATERAL jsonb_array_elements(
  CASE WHEN jsonb_typeof(m."rawPayload"::jsonb -> 'files') = 'array'
       THEN m."rawPayload"::jsonb -> 'files' ELSE '[]'::jsonb END
) WITH ORDINALITY AS f(value, ordinality)
WHERE s."userId" IN (SELECT "userId" FROM members)
  AND s."isDeleted" = false AND m."isDeleted" = false;
```

由KM服务负责人，在正确实例和用户作用域下使用现有接口：

```text
GET /api/km/workspace/files/{逐路径段编码后的path}/content
GET /api/km/shared-workspace/files/{逐路径段编码后的path}/content
GET /sessions/{编码后的openclawSessionKey}/history?limit=...&cursor=...
GET /api/km/skills
GET /api/km/skills/{编码后的skillId}/bundle
GET /api/km/skills/personal/{编码后的skillKey}/revisions
GET /api/km/skills/personal/{编码后的skillKey}/revisions/{revision}
```

客户端以 `x-km-user-id` 选用户，使用既有服务token并按实例baseUrl路由；数据方执行，研究人员无需获取token明文。KM内部数据库表名和对象存储桶没有源码证据，不在本报告猜测。

### 3.4 产物、技能选择、审批和版本元数据

```sql
SELECT * FROM generated_artifacts WHERE "enterpriseId" = $1;
SELECT * FROM skill_usage_events WHERE "enterpriseId" = $1;
SELECT * FROM human_efficiency_events WHERE "enterpriseId" = $1;
SELECT * FROM personal_skill_configs WHERE "enterpriseId" = $1;
SELECT * FROM enterprise_skill_configs WHERE "enterpriseId" = $1;
SELECT * FROM skill_submissions WHERE "enterpriseId" = $1;
SELECT * FROM skill_submission_versions WHERE "enterpriseId" = $1;
-- 仅当线上实际存在、已启用且本批发生时已经采集：
SELECT * FROM skill_emergence_observations WHERE "enterpriseId" = $1;
SELECT * FROM skill_emergence_analysis_snapshots WHERE "enterpriseId" = $1;
```

不要只交累计次数，交逐事件/逐版本行。如果没有历史安装表，交KM版本库和文件备份，说明仅能证明当前库存或恢复出的历史状态。

### 3.5 计费与知识库辅助映射（可选）

```sql
SELECT * FROM billing_tasks WHERE "enterpriseId" = $1;
SELECT e.* FROM billing_task_events e
JOIN billing_tasks t ON t.id = e."taskId"
WHERE t."enterpriseId" = $1;
SELECT * FROM zclaw_enterprise_token_usage_settlements WHERE "enterpriseId" = $1;
SELECT * FROM ragflow_datasets WHERE "enterpriseId" = $1;
SELECT d.* FROM ragflow_documents d
JOIN ragflow_datasets ds ON ds.id = d."datasetMappingId"
WHERE ds."enterpriseId" = $1;
SELECT b.* FROM ragflow_file_blobs b
JOIN ragflow_datasets ds ON ds.id = b."datasetMappingId"
WHERE ds."enterpriseId" = $1;
```

若资料来自个人数据集，要按已经确认的用户/实例范围另取，不将企业条件当全量召回。metadata/eventPayload中关联键以实际返回为准，不先编写未知JSON字段的连接SQL。

## 4. 建议一次性交付的目录和清单

```text
supplement_YYYYMMDD/
  export_manifest.json                 # 快照时间、范围、库schema版本、每文件行数/SHA256
  source_schema.json                  # 实际表列清单
  sessions_and_bindings.jsonl
  messages_all_roles.jsonl
  files_manifest.jsonl                # 输入/输出、message/run、source/path、hash、历史/当前、状态
  files/                              # 原始文件字节；按hash存避免同名覆盖
  km_histories/                        # 原生顺序、游标连续且无漏页
  skill_usage_events.jsonl
  skill_versions_manifest.jsonl
  skill_bundles/                      # SKILL.md + scripts/references/assets，每版独立
  business_outcomes.jsonl              # 若有，逐验收对象与证据
  unresolved_manifest.jsonl           # 无法补取也逐项交原因
```

验收最低要求：原sessionId→绑定→history可串联；每个附件/产物引用对应文件或明确缺失状态；toolCallId调用和结果能关联；每个skill使用关联一个明确版本或UNKNOWN；补到的业务评价有作用对象及证据。历史缺证不能靠当前文件、模型解释、text regex或done状态“补完整”。

## 5. 源码证据位置

以下均是本地静态核对，不证明线上已部署。

- 原始范围/未导项：[原包README](C:/Users/39835/Downloads/zkys-raw-export-20260925/README.md:3)，工具全量和附件缺口第16–20行，双副本及附件字段第36–41行。
- 组织成员与实例：[schema.prisma](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:251)，ZclawAgentInstance第1736行，会话/绑定/消息第1784/1816/1835行。
- 附件写入与上传：[zclaw.service.ts](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:9913)，第5164行向KM工作区上传；[附件DTO](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/dto/send-zclaw-message.dto.ts:70)。
- KM工作区字节/原生history：[zclaw-km-agent.client.ts](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw-km-agent.client.ts:150)，工作区第245–259行，共享第349–363行，技能bundle/revisions第434–503行，作用域认证第1109–1124行。
- 产物表与正文在磁盘：[schema](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:2267)；[同路径upsert](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/human-efficiency/generated-artifact.service.ts:75)；[从run.completed manifest入库](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:10485)。
- 工具快照调用/状态/args/output：[zclaw.service.ts](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:10204)，第13985–14039行解析；第13016–13031行按toolCallId消除流式/同步双副本。
- 请求seq仅内存：[zclaw.service.ts](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:10969)。
- usage表：[schema](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:2318)；[完成时记所选技能](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:10501)；[固定工时](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/skill-analytics/skill-analytics-recorder.service.ts:19)。
- bundleHash和注入回执：[zclaw.service.ts](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/zclaw/zclaw.service.ts:13187)，第10181–10186行标USED/PROMPT_INJECTED；[trace开关](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/skill-analytics/skill-task-trace.service.ts:39)仅capture/active采集；持久evidenceRefs/schema第2405行、snapshot.trace第2451行。
- 组织审批版本/个人配置：[schema](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:582)，第621/651/712行。
- 知识库源索引：[schema](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:2075)，第2104/2130行；计费表第1532/1564/952行。
- 第二包文本抽取：[clean.mjs](C:/Users/39835/Downloads/zkys-skill-mining-20260925/clean.mjs:16)。

