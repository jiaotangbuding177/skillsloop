# 021：请团队提供的数据库与评估材料

2026-09-24。与[执行计划](021_execution_plan.md)配套。现在先给结构、小样本、验收材料；不要求生产数据库账号，也不要求一开始全量导出。

## A. 第一批交付：足够让我开始

1. **数据库说明**：类型/版本、schema或DDL、数据时间范围、粗略组织/用户/会话量；本地只读导出路径。JSONL/CSV/Parquet/离线数据库均可，保留原字段即可。
2. **10—20个完整会话**：覆盖多轮修改、普通交付、失败重试、用过skill和无任务问答。按会话完整导出，不人工切成“成功QA”。缺哪个类型就说明，不能补造。
3. **3—5类业务说明**：员工角色、典型任务、为什么重复、什么算错误、当前怎么验收；现有最终交付物和输入附件各提供若干授权样例。
4. **既有评估**：如果你说的“评估”是满意度、点赞、savedHours、自评分或人工验收，请提供字段定义、谁评、何时评、样本覆盖和原始依据。它们不是同一种标签。
5. **授权与执行边界**：可用于本地研究/哪些模型服务/人工标注/论文汇总或示例披露；模型批次预算；可参与验收的业务人员。可先只允许本地审计，外发默认未定。

交付时只需告诉我文件所在路径和以上说明。稳定假名ID需在各表一致，保留时间顺序和间隔；脱敏要保留任务对象之间的等价关系。原ID映射由企业保管。不要提供密码、token、模型密钥表或无关人事信息。

## B. 已核对源码的表映射

依据：`enginering/insightweaver/packages/db/prisma/schema.prisma`。这是本地源码事实，不保证生产已应用相同迁移；先比对实际DDL再写导出脚本。

| 优先级 | 表/材料 | 所需字段或内容 | 能支持什么 / 缺失边界 |
| --- | --- | --- | --- |
| 必需 | zclaw_sessions | id,userId,agentInstanceId,purpose,originEnterpriseId,createdAt,updatedAt,lastMessageAt,status；可脱敏title | 确定会话与成员；originEnterpriseId只在某些用途存在，不能当所有会话企业归属 |
| 必需 | zclaw_messages | id,sessionId,role,content,status,createdAt,updatedAt,isDeleted；清洗后rawPayload | 完整修订与工具信息；rawPayload未知键先审查，不整包外发 |
| 必需 | 经授权的用户—组织映射 | 稳定假名user/org、角色/部门粗粒度；若跨组织/离职需时间范围 | 不能用当前成员关系倒推历史归属；不需姓名手机号 |
| 优先 | skill_emergence_observations | requestEventId,sessionId,userMessageId,assistantMessageId,outcome,sourceRevision,evidenceRefs,sourceKind等实际存在字段 | 运行关联与来源；标签需校准，不能把outcome默认值当人工验收 |
| 优先 | skill_emergence_analysis_snapshots | kind,taskId,revision,trace,sourceObservationIds,inputEvidenceHash,taskState,createdAt | 旧方案与新任务证据；v2字段可能只在开发库存在 |
| 优先 | skill_usage_events | enterpriseId,userId,requestEventId,sessionId,skillKey,skillScope,skillSource,occurredAt | 选择/使用关联；schema无完整版本hash和read回执，不能单凭此表证明实际遵循 |
| 优先 | skill_emergence_candidates / evaluations / packaging_jobs | 候选、draftFilesSnapshot、inputSnapshot、决策/理由、时间、失败、attemptCount、billingTaskId | 生成量、拒绝、延迟、候选来源；不能只导出INSTALLED |
| 优先 | skill_submissions / skill_submission_versions | 状态、审核时间、版本、filesSnapshot、sourceVersion | 已批准组织skill及其当时版本；未批准不能当共享库 |
| 优先 | 个人skills文件包+索引 | SKILL.md及references/assets/scripts；版本/更新时间/hash；personal_skill_configs元数据 | config表没有完整个人包；仅取表不能重现技能消费；脚本仅作为材料不默认执行 |
| 优先 | generated_artifacts + 原始文件快照 | 会话引用、文件类型、时间、内容/hash与有效期 | 表只保存元数据，内容在个人工作区；最新文件不能假冒历史交付版 |
| 可选 | runtime/模型请求计量 | request/run、模型、输入/输出/缓存tokens、工具、状态、重试、延迟、实际费用 | 不含认证头；账本积分需说明与现金关系；没有记录则未知 |
| 可选 | human_efficiency_events / savedHours | 事件及字段生成逻辑、计量依据、采样方法 | 先核实是固定估计/自报/计时；不能直接当客观净节省 |
| 可选 | 原生OpenClaw轨迹 | 授权的session/toolCall/toolResult与选定skill版本 | 可核验实际读取及动作；需与本地会话映射，缺映射不强拼 |

不要导出UserZclawModelConfig、第三方连接凭据、钱包支付资料等无关敏感表。首批只需A部分，B部分是数据审计后的分阶段补充清单。

## C. 全量离线数据的建议范围

先选择一个授权组织、若干活跃角色、连续时间窗口，例如4—8周（建议而非硬门槛），保留全部符合条件会话，不挑成功者。若业务任务按月复用，应延长窗口；用户数少但每人有持续复用可先做个人案例研究，不夸大跨企业泛化。

数据划分在审计后按日期冻结：较早生成、中间开发、较晚测试；并根据独立任务组避免同一工作单或衍生对象跨集合。是否预留用户取决于组织复用实验。生产数据回填updatedAt需记录，不能把更新时间误当发生时间。

## D. 评估材料表：你提供什么，我如何处理

| 材料 | 团队提供 | 我产出 |
| --- | --- | --- |
| task_catalog | 角色/目标/频率/重要性/输入输出/禁错项 | 任务族边界、采样、可测性判断 |
| task_cases | 独立新任务输入、必要附件、时点规则 | 消费任务包；隔离参考答案 |
| rubric | 必须正确项、可容忍项、偏好项、验收人 | 客观脚本或匿名盲评表 |
| preferences | 用户明确的长期偏好及生效/变更依据 | 个性化标签；与组织强约束分开 |
| feedback | 谁对哪个实际输出做何纠正、依据与时间 | attempt/反馈关联；历史反馈适用性检查 |
| effort | 实际操作计时或可安排抽样观察 | 主动时间、审核维护、问卷分开统计 |
| budget | 单批tokens/请求/金额上限与服务限制 | 预算配置和批次估算；没有额度不批量跑 |

推荐两位懂业务的评审先校准一小批，不要求全员参与。若只能一人评，保留此限制；若只有AI自动评分，暂不宣称已经证明真实业务成功。

## E. 可直接填写的交接信息

```yaml
database_type: 待填写
local_export_path: 待填写
schema_version_or_export_time: 待填写
time_range_and_timezone: 待填写
approx_users_sessions: 待填写
authorized_orgs_roles: 待填写
allowed_processing: local_only_or_named_provider
allowed_publication: aggregate_only_or_reviewed_examples
available_task_families: 待填写
evaluation_definition_and_reviewers: 待填写
attachments_and_skill_versions_available: 待填写
batch_budget: 待填写
known_missing_fields: 待填写
```

这不是额外审批流程，而是决定可以执行哪些实验的输入。缺某项可以继续不依赖它的工作；无法证明的结论保持UNKNOWN。
