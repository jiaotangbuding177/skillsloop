# 013｜全面复核升级方案、Trace2Skill 适配与成本／格式边界

日期：2026-09-20。

## 用户要求

用户指出此前方案不全面，要求全面核查并更新，同时回答：升级后能否称 Trace2Skill 算法原型驱动、无效 skills 数量增减、模型资源增减、存储与应用规范是否对齐原项目。科研模式、团队落地优先、无实验设计继续有效。本次是研究方案与源码分析，不是开发授权。

## 工作与产物

先读 README、CHARTER、STATE、010／011 报告和012记忆。使用 arxiv 科研 skill，核对 Trace2Skill v5 原论文及官方核心实现／组合演化入口。三项并行只读核查分别覆盖文件／应用契约、模型资源、数据／状态链，主代理整合。

当前完整产物：[013 全面复核版升级方案](../reports/013_comprehensive_upgrade_plan.md)。该报告统一取代010—012分散建议作为当前方案；旧稿保留更正入口。

没有修改业务源码、数据库、部署或运行系统实验。FastCtx 本轮已恢复可用。论文与官方实现仅阅读，未下载运行或接入。

## 证据支持的新增观察

1. 失败学习不仅卡在采集：Processor 双消息要求、Scheduler 两处 SUCCESS 目标筛选、Evaluator 选簇、Gate 成功过滤都必须调整。
2. AgentRuntime→normalizeWorkflow→封装 safe 字段不一致；输入输出约束和新增失败／修正信息可能在封装前丢失。
3. 候选详情读取当前 cluster 的 SUCCESS 观察与 workflow，不能作为冻结候选证据。
4. 拒绝、删除失败候选、撤销采纳会按候选key隐藏／软删个人配置；UPDATE不能直接沿用。现采纳只变可见，也不足以发布隔离草稿。
5. 生成成功即推进 covered 和水位，未区分待审、被拒和已发布能力。
6. Evaluation.clusterId 必填，前置噪声不能无条件写入；零新表需同时考虑Snapshot记录类型、唯一、作用域、幂等、并发、追加修订与清理。
7. 组织提审依赖个人导出包／本人快照，已有组织同key对其他发布者有限制，不能假设任意成员能直接更新。
8. 加载函数未明确携带 scope/source/revision，实际同key来源在远端尚未知；完整包导出与个人revision能力已有，但reliability导出失败会退为仅SKILL.md，hash覆盖不恒定。
9. 指纹、workflow为LLM请求；生成／市场修复为agent run；quality／reliability主要本地规则。分析usage未回传；主生成billingTask不能代表修复全成本；超时Promise拒绝不取消底层。
10. 本地检索未发现Trace2Skill命名或直接接入，核验链路也非该补丁合并流程。原论文／官方实现强调冻结基准、局部补丁、合并／应用；旧方案尚不足以冠名。

完整路径行号见013报告。

## 工作建议与方向结论

- 零新表作为首版路线：扩展Observation和Snapshot，逻辑任务以taskId/revision表达。新表非必要，仍需完整迁移和读写约束；独立TaskInstance仅作后续可选取舍。
- 拟议生成／演化引擎采用Trace2Skill核心机制，外围保留企业任务发现、权限、审核。只有核心落实后才称企业适配原型；当前仍是方案，不能声称已经驱动或完整复现。
- 相同需求范围预期减少重复／噪声NEW及无效比例；扩大覆盖后无效绝对数量未定。UPDATE、SUPPORT、待判分开，拒绝／未用不直接等于无效；旧库存量不会自动减少。
- 完整升级按模型消耗可能增加规划预算。新增整理、诊断、合并、刷新与节省封装抵消方向未知；并行加速不等于资源下降。加入增量、缓存、限额、合并批次、重试对账，在线正文长度单独管理。
- 最终包沿用SKILL.md、原辅助文件、frontmatter兼容和五市场字段。轨迹／补丁留后台。补齐草稿到正式发布、所有权、版本及加载回执后才可声称应用兼容。
- 新建／更新动作与生命周期分离；拒绝更新仅弃草稿。候选冻结证据，基准冲突阻止覆盖。前聚类噪声在Observation，有任务后在Snapshot，进入cluster再用Evaluation。

以上为建议及条件性预期，用户尚未逐项确认；没有模型质量、成本下降或算法创新成立的实证结论。

## 来源

- https://arxiv.org/html/2603.25158v5
- https://github.com/Qwen-Applications/Trace2Skill
- https://github.com/Qwen-Applications/Trace2Skill/blob/main/skill_evolver/parallel_evolving_agent.py
- https://github.com/Qwen-Applications/Trace2Skill/blob/main/skill_evolver/run_parallel_combined_skill_evolution.py
- 本项目限定源码；具体链接见报告。

## 未知与后续

运行实例的skill-creator/quick_validate规则、隔离草稿、版本固定加载、发布回执、真实usage、生产数据规模和效果尚未知。先按013的四阶段合同细化；未获得业务开发、数据接入或部署授权。本轮无新增运行实证发现。

已更新README索引、STATE当前口径，010／011增加取代说明。长期章程不变。

