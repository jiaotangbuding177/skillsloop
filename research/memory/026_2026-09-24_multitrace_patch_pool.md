# 026｜现有聚类、成功失败埋点与多轨迹 Patch 池

日期：2026-09-24。

## 用户问题

用户指出当前已经有聚类合并和成功失败埋点，询问是否已经等同于 Trace2Skill 的多轨迹 patch 池和层次合并，并要求评估能否加入。

## 代码核对

- InsightWeaver 已有 `SkillEmergenceObservation` 的 SUCCESS/PARTIAL/FAILURE/UNKNOWN、`SkillEmergenceAnalysisSnapshot` 的可修订 task_revision、`SkillEmergenceTaskCluster` 的任务聚类、频率/深度/价值门禁及候选封装。
- `SkillTraceLearningService.discover()` 当前以一个 sealed `TaskTrace` 构建一个 `TraceLearningInput` 和候选；`buildTraceLearningInput()` 的 `traceEvidence` 属于该任务轨迹，`methodSignature` 做精确去重，不生成逐轨迹 patch 池。
- 当前门禁主要只统计 SUCCESS；FAILURE/UNKNOWN 有结果记录，但尚没有“失败原因—修正—验证”的独立 patch 分析阶段。
- 独立 OpenClaw demo 没有 InsightWeaver 的任务聚类表，不能把 demo 的单候选流程称为已有聚类合并。

## 已确认观察

1. 现有聚类是“轨迹是否属于同一任务族”的索引和资格层；patch pool 是“每条轨迹对固定技能提出的局部修改”的证据层，二者不是同一个对象。
2. 现有成功／失败埋点是必要前置，但结果标签本身不等于失败因果分析或业务正确性标签。
3. 多轨迹 patch 算法可复用现有表，通过 Candidate.inputSnapshot、PackagingJob 分阶段结果、TaskCluster workflow 和 Evaluation evidenceSnapshot 保存逻辑 patch pool，不要求首版新增物理表。
4. 严格 Trace2Skill 对齐需要逐轨迹 patch 提议和 many-to-one merge；预算兼容版可一次批量提炼并返回结构化 patches，但不能称严格复现。

## 研究建议（尚未实施）

- 先以 cluster + baseBundleHash 冻结轨迹池。
- SUCCESS、FAILURE、PARTIAL/UNKNOWN 分路分析；只有可解释且可验证的失败进入可应用 patch。
- 先做规则去重、目标归一、冲突检查，再进行一次批量 merge；保留证据 watermark 和基准 hash。
- 先实现预算兼容版，再以 Trace2Skill 对齐版作为可选开关和对照，避免违背模型调用至少不增加的工程约束。

## 未解决问题

- 真实企业业务结果如何作为正确性证据。
- 多轨迹之间的冲突如何转为待审而不是自动覆盖。
- 批量 merge 的 token、失败重试和最终技能数量是否真的下降。

本轮无新增企业实证；新增的是源码核对后的机制边界和可复用现有表的 patch pool 适配方案。
