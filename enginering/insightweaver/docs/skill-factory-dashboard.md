# Skill 工厂看板数据说明

## 使用对象与权限

Skill 工厂看板用于企业所有者和管理员查看企业 Skill 库存、生命周期、成功使用情况和复用建议。接口为 `GET /api/dashboard/skill-factory?enterpriseId=...`，沿用企业管理员鉴权和企业隔离。

## 指标口径

| 指标 | 口径 | 数据来源 |
| --- | --- | --- |
| 已生成 Skill | 企业所有有效成员当前存在的个人 Skill 总数 | KM Agent Skill 列表的库存快照 |
| 本月新增 Skill | 上海时区本月首次盘点发现、且当前仍然存在的个人 Skill | 库存首次发现时间 |
| 高复用 Skill | 最近 30 天被不少于 5 次成功完成对话携带的不同 Skill | `SkillUsageEvent` |
| 模板 Skill | 企业 Skill 列表中「是否展示=展示」的 Skill 数量（与后台列表口径一致） | `listEnterpriseAdminVisibleSkillsForDashboard` |
| Skill 节省工时 | 成功完成的 Skill 对话和真实 Skill 产物的规则估算工时 | `SkillUsageEvent`、`HumanEfficiencyEvent` |

“已生成 Skill”和“本月新增 Skill”均只统计当前存在的个人 Skill；后者是前者在上海时区本月首次发现的子集，因此不会大于前者。KM Agent 不提供创建时间，功能上线前已存在但首次被盘点的 Skill 会以首次发现时间为准，不补造历史。

“模板 Skill”与「Skill 分类分布」均基于企业管理后台 Skill 列表同一套合并逻辑：KM 已安装 + 全局/企业配置合并后的可见 Skill；内置 Skill 分类来自平台 catalog 映射。个人 Skill 不计入。

## 成功使用与工时估算

- 只有 KM Agent 返回 `run.completed` 后才记录 Skill 使用；失败、中止和未完成请求不计入。
- “复用”表示成功完成的对话携带了该 Skill，不表示模型内部一定调用了独立工具。
- 一次完成请求的基础节省工时为现有人效规则中的 0.5 小时；携带多个不同 Skill 时平均分摊，避免重复计算。
- 真实 Skill 文件产物继续采用现有人效产物规则。
- 使用事件以“企业 + 请求事件 + Skill 作用域 + Skill 标识”唯一约束去重。

## 自动涌现流水线与推荐

- 识别高频任务：最近 30 天成功完成、未携带现有 Skill 的普通对话，经后台脱敏分析后累计的任务观察数量。
- 分析执行路径：同一企业内同类任务最近 30 天至少出现 5 次且跨越至少 2 个上海自然日后，完成工作流建模的任务聚类数量。
- 已涌现、已上线和持续进化：`emerged` 为最近 30 天创建的 `SkillEmergenceCandidate`（排除 `FAILED` / `REJECTED`）；`online` 为组织已上架（`type=custom` 且 `isVisible`）且 skillKey 能关联到本企业已封装涌现候选（状态 ∈ `AWAITING_CONFIRM` / `INSTALLED` / `SUBMITTED` 的 `skillKey` / `acceptedSkillKey`）的当前数量——仅统计自动涌现链路，个人手动或对话生成后再上架的不计；`evolving` 本期仍为 0（V1.1 Darwin），上线后也只计涌现链路产物的进化。
- 推荐排除用的「已在组织上线」仍为全部已上架 custom（与流水线 `online` 来源隔离口径不同），避免把手动上架的再推「最值得封装」。
- 页面进行状态以「已涌现」或「分析执行路径」为主高亮；「已上线」有数量时显示为完成态，不挂「进行中」。
- 封装链路受 `SKILL_EMERGENCE_MODE` 控制：默认 / 推荐 `active`（真正建草稿）；设为 `shadow` 时只写评估记录不建候选（排障干跑）。

对话的原始请求和最终回答只在后台分析时按消息 ID 短暂读取。新表仅保存脱敏任务指纹、粗粒度工具类别、结构化步骤、状态和必要的消息标识，不复制原始文本。观察记录保留 90 天，看板按最近 30 天聚合；部署前历史对话不回填。

“最值得封装”从尚未进入企业技能库的个人 Skill 与企业 / Global Skill 中选择，按最近 30 天成功完成次数、活跃天数和预计节省工时排序。推荐理由由 AI 生成短句标签式定性描述（如「重复性高、规则清晰，ROI 明显」），聚焦业务痛点与封装价值；统计数字展示在「预估节省」列，不在理由中复述。AI 不可用或超时时回退为规则文案。分类分布直接使用 Skill 已配置的分类，缺失分类归入“未分类”，不通过关键词或 Prompt 猜测。

EvoMind 建议的事实、排名和数值由确定性规则生成，主看板接口立即返回规则 fallback 文案（`title` + `body`）。独立异步接口 `GET /api/dashboard/skill-factory/suggestions` 在 24 小时内按企业缓存 AI 润色结果；AI 不可用时回退为同一套规则文案。AI 不得编造未提供的数字或 Skill 名称；低基数增长场景禁止输出「增长 100%」等误导表述。

## 同步、失败策略与隐私

- 看板读取时以最多 4 个成员为一批同步 KM Agent 库存，并保留最近一次成功快照。
- 单个成员同步失败不会清除其旧库存；页面显示“部分同步”提示。
- Skill 完成埋点在业务完成结果确定后旁路、非阻塞执行，写入失败只记录脱敏告警。
- 自动涌现观察同样只在 `run.completed` 且本次未选择 Skill 后旁路登记；隐藏消息、定时任务、失败和取消请求不计入。
- 后台任务使用数据库原子状态抢占，避免多实例重复分析；单次 AI 分析超时后有限重试，失败不会生成模拟统计。
- 埋点失败不会改变对话、上传、审核、发布、流式响应、HTTP 状态或事务结果。
- 分析表和日志不保存 Prompt、最终回答、文件内容、完整路径、密码、验证码、手机号或 JWT。

## 排障

1. 检查企业 KM Agent 实例是否可用，以及目标成员是否为有效企业成员。
2. 检查 Prisma 迁移 `20260822213000_add_skill_factory_analytics`、`20260822233000_add_skill_emergence` 与 `20260915140000_skill_emergence_user_progress`（per-user 水位/覆盖）是否已执行。
3. 查看 `SkillFactoryDashboardService`、`SkillAnalyticsRecorder`、`SkillEmergenceRecorder` 和 `SkillEmergenceProcessor` 的脱敏告警。
4. 确认 `SKILL_EMERGENCE_MODE=active`（`shadow` 只记评估不建草稿）。平台超管「主动触发涌现」返回摘要含 `evaluated / eligible / candidatesCreated / covered`。
5. 需要暂停后台涌现分析时设置 `SKILL_EMERGENCE_ANALYSIS_ENABLED=false`；这不会停止现有对话和 Skill 功能。
6. 新部署后历史热度和流水线为空属于正常情况；只有上线后的成功完成请求才会累计精确数据。
7. 覆盖判定与水位在 `skill_emergence_user_progress`（按 user×cluster）；企业共享 cluster 上的 `coveredBySkillKey` 仅作看板遗留字段，不再互斥其他成员。
