# 阶段4/5交接契约：workflow与技能封装

版本：设计稿v1，2026-09-26；轮次049已据此实现阶段4/5，运行事实及剩余差距见[049验收报告](../reports/049_stage45_implementation_and_harness_acceptance.md)。上位依据为[046用户契约第5节](046_twelve_stage_contract_user_revision.md)。本文件新增的是逻辑对象与校验约束，不新增数据库表，不修改十二阶段顺序。[机制说明](../reports/048_stage45_contract_and_design.md)。

## 1. 不变的责任边界

| 阶段 | 输入 | 输出 | 完成条件 |
| --- | --- | --- | --- |
| 3→4 | 当前有效task-trace-v2及受控证据引用 | LearningBatchInput | 要求/反馈/attempt/未知项与用途均可回查，没有从助手声明制造真实检查 |
| 4 | 一条或多条轨迹、权限、技能使用依据、精确基准、预算 | LearningDecisionSet；零到多个WorkflowCandidate | 全部输入及方法有归宿，聚类/条件可解释，版本及证据冻结 |
| 5 | NEW WorkflowCandidate及生成规范/验证能力 | DraftSkillPackage或GenerationFailure | 真实文件、官方封装与分层验证可查；失败原因和usage同样留存 |
| 6 | READY候选及其限制 | 用户采纳/拒绝/暂缓/提交等真实选择 | 不由阶段5自动代替用户选择 |
| 9 | UPDATE workflow及实际使用的精确基准 | 候选新版本与保留/回退证据 | 可复用阶段5的底层构建器，不改变阶段9责任 |

业务UNKNOWN、历史附件缺失不等于全任务DEFER。阶段5包存在不等于已消费、遵循或业务成功。

## 2. LearningBatchInput

以下字段为拟新增适配契约，实际取值必须由宿主从现有对象映射，不能要求模型自己填写权限、hash或执行回执。

| 字段 | 来源及语义 |
| --- | --- |
| schemaVersion | `learning-batch-v1` |
| batchId / owner / authorizationScope | 宿主创建；同组织不自动具有同一材料授权 |
| purposeSplit | 本次来源用途；038只允许generation；holdout不进入模型视图 |
| sourceRefs | traceId、revision/hash、taskId、pair/fragment引用；对应当前已完成恢复结果 |
| traceEvidence | requirementTimeline、feedbackEdges、attempts、observations、unresolved、来源span；不退化为仅goal/turns |
| executionEvidenceRefs | pair/fragment→sourceTurn/run→tool/artifact/check；每项有可解析的对象与attempt关联 |
| skillUseBindings | 见下表，作用到具体attempt/方法范围，不按skillId覆盖历史版本 |
| availableValidation | 真实存在的附件、工具、检查器及其覆盖范围；缺失项明确列出 |
| budgetReservation / analysisConfig | 外层额度、各请求/输出上限、可选诊断开关、模型及prompt/schema版本 |
| inputHash | 对规范化证据内容与版本计算；不得包含凭据 |

技能使用依据统一映射为：

| state | 必要字段 | 对路由的作用 |
| --- | --- | --- |
| KNOWN_NONE | 来源范围与basisRef，例如用户确认的历史无技能初始化 | 可支持该范围NEW，不要求全库检索 |
| USED_EXACT | skillId、version、bundleHash、run/receipt、作用范围 | 可评估UPDATE/SUPPORT；实际提供/读取与行为遵循仍分开 |
| UNKNOWN | 缺失或矛盾说明 | 不伪造基准；受影响方法保存但路由DEFER |

多个精确版本不能压成一个。能分清作用范围则分池，不能分清则只延期相关方法。任何历史无技能前提不得扩展成未来所有执行永远KNOWN_NONE。

## 3. WorkflowFrame、MethodProposal及关系

### 3.1 WorkflowFrame：决定聚类粒度

必须包含`frameId/sourceTraceRefs/reusableGoal/inputContract/outputContract/processSketch/applicability/parameters/methodIds/targetBinding`。

- processSketch描述同一可复用目标下的处理阶段、依赖及可选分支。
- 一个trace可贡献多个frame，但每个拆分须有独立目标/交付理由；步骤多不等于多个frame。
- `targetBinding`先由宿主按实际使用范围分为NEW候选、精确基准UPDATE候选或待归因。它是聚池边界，不是最终学习决策。
- frame不能只是一条主题标签；“合同”“写报告”不足以据此合并。

### 3.2 MethodProposal：保留可追溯的方法提议

```json
{
  "methodId": "method-example",
  "frameId": "frame-example",
  "action": "按当前要求完成一个有明确输出的步骤",
  "inputs": ["所需输入"],
  "outputs": ["步骤输出"],
  "conditions": ["适用条件"],
  "parameters": [{"name": "deliveryMode", "scope": "CURRENT_TASK"}],
  "requires": [],
  "completionChecks": [{"description": "可检查的完成标准", "verification": "NOT_RUN"}],
  "evidenceRefs": [{"traceRef": "trace-example", "attemptRef": "attempt-example", "spanRef": "span-example"}],
  "evidenceKinds": ["USER_REQUIREMENT"],
  "assessment": {"businessOutcome": "UNKNOWN", "methodEffect": "UNVERIFIED"},
  "unknowns": ["缺少历史业务验收"]
}
```

示例为字段说明，不是038模型输出。运行时evidenceRefs应引用宿主已编号材料；模型不生成任意文件路径。涉及反馈归因的提议额外包含`requirementVersion/feedbackRef/targetAttempt/causeStatus/repairRef/verificationRef`。无法对应的项为null及原因，不得填虚构ID。

证据来源枚举：`USER_REQUIREMENT / VISIBLE_PROCESS / USER_ACCEPTANCE / VERIFIED_CHECK / ASSISTANT_CLAIM / DESIGN_POLICY / MODEL_HYPOTHESIS`。不同来源可以并存，不能通过一个confidence阈值将声明升级为已验证。

### 3.3 两种关系不能混用

| 对象 | 关系 | 必填解释 |
| --- | --- | --- |
| 两个frame | SHARE_CORE | 共同处理过程、对应步骤、兼容输入输出 |
| 两个frame | CONDITIONAL | 共同过程、条件变量、作用步骤、互斥/重叠情况、分支输入输出 |
| 两个frame | INCOMPATIBLE | 具体目标/契约/规则冲突 |
| 两个frame | INSUFFICIENT | 尚缺何种判断依据；不能当作已经证实不兼容 |
| 簇内方法 | EQUIVALENT / CONDITIONAL_VARIANT | 等价依据或差异生效条件 |
| 簇内方法 | COMPLEMENTS / REQUIRES | 共同目标、过程位置/依赖及来源；输入输出能接上本身不够 |
| 簇内方法 | CONFLICT | 冲突要求及可否由条件消解；不能按多数票抹去 |

轮廓约束聚类可用complete-link；局部步骤的相似度仅用于方法去重。必须检查组级条件一致性；两两看似兼容也可能形成无法同时满足的整体。

## 4. LearningDecisionSet与WorkflowCandidate

LearningDecisionSet保存：`inputCoverage/frameRelations/clusterMembership/methodLedger/workflowRefs/unresolved/usageRefs/configVersions`。没有提取出方法的输入也要记录理由；不能从台账消失。

每条methodLedger含`methodId / decision / disposition / reason / workflowRef / targetBase / duplicateOf / reprocessWhen / evidenceRefs`。

- decision：NEW、UPDATE、SUPPORT、DEFER。
- disposition：INCLUDED、DUPLICATE、EXCLUDED、DEFERRED。没有可复用价值可表示DEFER＋EXCLUDED＋具体原因，保持四种上位决策，不新增第五个学习动作。
- INCLUDED只进入一个明确目标版本的workflow；同一可共享规则若在多个workflow引用，需显式复用关系，不重复计算独立证据。
- SUPPORT/DEFER不生成空技能包；保留有效少数方法的条件，不为了减少包数丢弃。

WorkflowCandidate的必需字段：

```json
{
  "schemaVersion": "workflow-candidate-v1",
  "id": "workflow-example",
  "revision": 1,
  "owner": "owner-reference",
  "action": "NEW",
  "targetBase": null,
  "sourceRefs": [{"traceId": "trace-example", "revision": 1, "hash": "source-hash"}],
  "skillUseBasisRef": "private-basis-reference",
  "clusterRef": "cluster-example",
  "workflow": {
    "title": "可复用目标",
    "triggers": [],
    "inputs": [],
    "steps": [{"id": "step-1", "methodIds": ["method-example"], "action": "动作", "requires": [], "conditions": [], "outputs": [], "completionChecks": []}],
    "outputs": [],
    "parameters": [],
    "branches": [],
    "dependencies": [],
    "limitations": [],
    "evidenceStatement": "流程有来源；业务效果未验证"
  },
  "includedMethodIds": ["method-example"],
  "methodLedgerRef": "private-ledger-reference",
  "privateEvidenceRef": "private-evidence-reference",
  "generationViewHash": "public-view-hash",
  "workflowHash": "frozen-workflow-hash"
}
```

数组在示例中省略实际内容；生产验收需检查触发/输入/步骤/输出/检查等必要内容存在，不能把空示例当合法成品。UPDATE必须有唯一精确targetBase并转阶段9。一个初始簇归纳后可因目标/条件冲突拆开或全部延期，不强求一簇一包；每个最终workflow revision至多有一个当前有效生成包，其重试/旧包另存历史。

冻结包括来源revision/hash、方法及关系hash、聚类/分析版本、生成视图hash和基准版本。来源改变则相关workflow与候选STALE；不能仅查旧turn hash。相同冻结输入复用缓存，不自动重新生成。

## 5. GenerationInput与临时会话

宿主保留完整WorkflowCandidate；模型只收到以下生成视图：

- `algorithm=workflow-to-skill-v1`、workflow内容及公开方法别名。
- `formatSpec`：现有SKILL.md/frontmatter/市场字段与资源路径规范。
- `allowedFileRoles`：SKILL.md、必要reference/template/script；不含私有索引/原会话。
- `capabilityManifest`：分支、输入前提、实际可用工具、验证能力、未验证项。
- `creatorManifest`：官方creator来源版本及文件hash，由宿主生成。
- `coverageRequirements`：方法、条件、分支与未知项的公开别名，生成结果必须说明对应落点。

不自动携带原轨迹、其他用户材料、留出样本或完整技能库。私有依据与生成视图单独存储。独立run/workspace/state避免历史会话污染；该run标为学习用途，从采集入口排除。目录隔离不宣称为OS级沙箱。

会话收到契约后必须真实读取creator文件、生成实际草稿及coverage manifest；只允许表达与结构化封装。需更改workflow时返回NEEDS_WORKFLOW_REVISION，不能在生成器中扩展学习范围。宿主执行官方打包，禁止模型压缩整个workspace后当作技能包。

## 6. DraftSkillPackage与失败结果

DraftSkillPackage必须包含：

| 字段 | 验收要求 |
| --- | --- |
| schemaVersion / candidateId / workflowRevision / workflowHash | `draft-skill-package-v1`；绑定真实冻结输入 |
| status / adoptionState | READY / AWAITING_USER_CHOICE；不能自动变成ACCEPTED |
| runId / sessionId / creatorManifest | 可追溯生成运行与creator版本 |
| files | 每个公开文件的路径、bytes、sha256及受控可读取入口；不能只有虚构清单 |
| archive | 实际.skill路径、bytes、sha256及授权下载入口 |
| methodCoverage | method/branch/condition别名→文件与章节/资源；机器可查与人工可审阅 |
| validation | creatorRead、hostBundle、resourceReferences、workflowCoverage、contentBoundary、officialPackage、helperTests分别记录 |
| capabilities / unknowns | 文本/文件等分支各自状态及前置条件；业务与未运行能力保留未知 |
| usageRef / privateAuditRef | 模型运行及私有侧记；不得打入公开包 |

validation各项使用`PASS / FAIL / NOT_RUN / NOT_APPLICABLE / UNKNOWN`及evidenceRef；不能一个布尔verified概括所有验证。结构覆盖PASS只代表项目有落点，不表示语义完全正确。内容扫描通过不等于完备脱敏。没有新增脚本时helperTests=NOT_APPLICABLE，不虚构已测试。

失败结果记录`status / reasonCode / affectedMethodIds / workflowHash / runId / retainedArtifacts / usageRef / retryCondition`。状态至少区分VALIDATION_FAILED、NEEDS_WORKFLOW_REVISION、STALE、BUDGET_EXHAUSTED、RUNTIME_FAILED。保留已发生消耗；超时/不完整/未知usage不自动归零，也不自动反复请求直到成功。

## 7. 持久化与事务

- 复用`records/events/runs`；frame、方法、关系、workflow与包都是逻辑记录或内容受控引用，不提出新物理表。
- 先在短事务中冻结与预留，事务外运行模型，提交时复核来源和基准；长模型调用不持有写事务。
- 生成请求以workflowHash＋生成配置版本为幂等依据。并发重复不能产生两个当前有效候选；失败运行保留独立run账目。
- 原始trace、关系提议、程序分组、归纳结果、生成视图和文件hash可逐层定位。模型证据引用与执行工具回执分开。
- 所有新增分析/生成purpose计入现有预算；初版可保留purpose=learn并增加stage字段，避免改名漏计。内部累计请求/tokens若无法实时强制，明确仅有外层硬额度与内部事后账目，不能宣传内部硬预算已实现。

## 8. 不允许发生的替代行为

1. 通过直接解除v2门禁绕过适配，或用旧词法规则静默回退。
2. 为了聚类读取留出正文；为了组织聚合读取无授权个人材料。
3. 把整任务业务UNKNOWN转换成无方法可学，或转换成SUCCESS。
4. 把新要求当旧失败、把不相关通过检查当修正验证。
5. 将分散方法拼接成没有共同目标依据的workflow；为数量目标强行并包。
6. 在阶段5重新提炼全部轨迹，补回阶段4已排除的结论。
7. 用模型文字声称替代creator读取、真实文件、官方封装或实际消费。
8. 私有侧记随公开包发布；生成后自动个人采纳或组织共享。
