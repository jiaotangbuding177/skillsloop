# 数据层收敛：优先复用现有表

> 后续更正：012 已明确零新表可行；[013 全面复核版](013_comprehensive_upgrade_plan.md)将其纳入统一首版路线，补齐约束与消费者。本文“一张新表优先”为历史建议，现不作为前提。

日期：2026-09-20。本文更正 [010 方案第 6 节](010_source_verified_upgrade_plan.md)“首版新增三个核心模型”的物理建表建议。用户质疑是否可复用现有表；这不是业务开发或迁移授权。

**可以复用。三个逻辑对象不必对应三张新表。当前建议首版新增一张 TaskInstance，复用并扩展 Observation 和 AnalysisSnapshot。** 这是源码核对后的设计建议，尚未实施，也未被用户逐项确认。

## 1. 对照映射

| 010 提议 | 收敛后建议 | 原因与边界 |
| --- | --- | --- |
| 新建 LearningEvent | 复用 SkillEmergenceObservation 作为回合／运行的学习采集入口，引用 ZclawMessage 及已有工具 rawPayload；必要补状态、来源、版本凭据和证据引用字段 | 已有企业、用da户、session、requestEventId、处理状态和重试机制。不重复建一套消息／工具日志，也不要求把所有细碎工具事件变成 Observation 行 |
| 新建 TaskInstance | 首版保留这一张新表 | 一次具体业务任务需要稳定 ID、目标、当前修订、企业和用户范围；session 可能包含多个任务，cluster 表示同类任务，二者均不能直接充当实例 |
| 新建 TaskTrajectoryRevision | 扩展 SkillEmergenceAnalysisSnapshot，增加任务修订类型、taskId、revision、结构化轨迹与证据引用 | 原表已承接学习用快照；改成区分“旧问答样本”和“任务修订”两种记录。任务修订追加写，旧记录保留原义 |

既有 Candidate、Evaluation、Progress、PackagingJob、SkillUsageEvent、个人／企业配置及发布版本继续复用。NEW／UPDATE、基准版本、证据集合等作为现有对象的扩展，不另建技能库。

## 2. 复用并非只换表名

**Observation：保持采集单位和业务任务分开。** 当前 userMessageId、assistantMessageId 均必填；失败／取消可能没有助手消息，必须允许相关引用缺失。`status` 目前是 worker 的 pending／processing／analyzed，`attempts` 是分析重试次数，不能分别当业务状态和任务尝试次数。技术终态、业务结果、处理状态应分别表达；未验证业务完成时 outcome 保留 UNKNOWN。

首版以稳定回合／运行记录为单位，工具和产物使用引用清单，新增反馈通过其消息／来源记录进入整理。若以后要同一请求多行事件，须重新设计事件幂等键，不能继续只用 `(enterpriseId,requestEventId)`。回合重投、真实重试和运行终态更新也需区别。事实证据版本变化触发重新处理，不能只改 payload 而继续保留“已分析”。

**AnalysisSnapshot：必须调整关联和写入契约。** 当前 observationId 唯一且必填，文本是 userText／assistantText，并在 Observation 删除时级联删除。复用为任务修订，需要：

- 区分 legacy_sample／task_revision 等类型；旧问答样本保留 observation 关系，任务修订改为关联 TaskInstance，并用 `(taskId,revision)` 唯一标识。
- observationId 对任务修订可空；userText／assistantText 不能再强制每种记录都提供。任务专有内容放有版本约束的结构化字段，包含 attempts、结果依据、skill 版本、证据引用及必要脱敏快照。
- 任务修订只追加。修正关联产生 revision 2，revision 1 仍可解释旧候选；不沿用 Recorder 的 upsert 覆盖方式。
- 多个 Observation 可进入同一任务，一条记录也可支持多个任务；在任务修订的证据清单表达关联，不能只在 Observation 加一个 taskId 就宣布支持多对多。
- 任务修订不能因任意一条 Observation 到期而被级联删除；重新明确保留、脱敏和删除联动，不能反过来永久保留本应删除的用户内容。

这些是待实现约束，不是当前表已有能力。源模型见 [schema.prisma](D:/skillsgen-industry_track/enginering/insightweaver/packages/db/prisma/schema.prisma:2403)，快照写入见 [Recorder](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/skill-analytics/skill-emergence-recorder.service.ts:97)，到期清理见 [Processor](D:/skillsgen-industry_track/enginering/insightweaver/apps/api/src/skill-analytics/skill-emergence-processor.service.ts:517)。

## 3. 为什么不直接用 Cluster 或 Session 当 TaskInstance

“季度经营分析”是任务类型，可以对应几十次任务；“张某今天为 A 客户完成的一次分析”才是任务实例。同一实例的三次改稿仍是一件任务。把它们都放进 Cluster 原有行，会混淆企业共享聚类与个人实例、破坏独立任务计频。

Session 是对话容器，同一会话可以换任务；明确续接的任务也可能跨会话。BillingTask 的用途是计费，不承担业务目标生命周期。Candidate 则只覆盖进入候选阶段的证据，无法容纳尚未值得沉淀的任务。

如果强制 **零新表**，可以在扩展 Snapshot 中每条 task_revision 带一个逻辑 taskId，以最新 revision 推导任务当前状态。但这意味着缺少独立任务主记录，要另行解决 taskId 一致性、并发 revision 分配、查找最新状态和索引；不是“原表完全不改就能完成”。不优先采用把所有任务 JSON 塞入一条 Session／Cluster 的做法。

因此首版建议为 **1 张新表 + 扩展现有表**；如果仅先交付 010 的阶段 A（补失败、取消、skill 加载等采集），可以 **0 张新表**，但不能因此声称任务关联层和不可变修订已经完成。

## 4. 决策与适用范围

- 替换“三张新表是首版前提”的建议；保留事件事实、任务实例、任务修订在逻辑上的区分。
- 不以新表数量衡量工作量：Snapshot 的关联、唯一性、消费者、清理与迁移仍需调整。若生产兼容成本高于独立新表，应在开发时基于实际数据重新权衡，不能承诺少建表一定更便宜。
- 本轮只更新方案和记忆，没有修改 schema、业务代码或运行数据库迁移。无新增运行实证发现。
