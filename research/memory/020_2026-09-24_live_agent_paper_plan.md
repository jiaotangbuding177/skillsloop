# 020 真实模型消费接口、论文大纲与测评方案

日期：2026-09-23—24。承接[019](019_2026-09-23_standalone_openclaw_demo.md)。

## 用户确认要求

加入真实消耗模型资源、能够使用skills的agent；提供完整论文大纲、全链路配图，并搜索顶会Industry Track评估方案，评估走向论文的缺口。因此早期004“不设计实验”的阶段限制在本轮被用户明确更新：现在授权评测方案与本项demo开发，不等于授权生产部署或大规模付费实验。独立OpenClaw载体不变。

## 实施与证据

- demo增加.env配置、live-check入口、技能文件清单、原生read回执和交付物hash清单。真实模型在工作区读取完整选定技能包，提示不重复注入全文。
- 缺失成功读取证据的真实运行不能仅凭选中技能归因为UPDATE。读取不等于遵循，更不等于任务成功；多技能归因仍有边界。
- 19项单元测试通过，JS语法检查通过。实际OpenClaw连接本地合成模型服务，7次HTTP请求完成NEW→SUPPORT→UPDATE并观察read回执；最终记录位于`enginering/demo/artifacts/openclaw-contract/run-c5e63db01d/result.json`。合成usage不作为真实成本。
- 测试曾暴露Windows SQLite连接未关闭导致清理失败，已修正并通过回归。另有一次原生测试在触达服务前超时，独立目录后两次通过；尚未证明超时唯一原因，保留失败记录。
- 本机缺少DEMO_MODEL/API_KEY配置及.env；已询问非密钥模型信息和本机配置，未获答复。真实LLM调用尚未完成，不把合成服务说成真实模型效果。密钥不得进入记忆。

## 研究产物

- [完整论文大纲与投稿差距](../reports/020_paper_blueprint.md)。
- [分层评估协议](../reports/020_evaluation_protocol.md)。
- `research/figures/020/`内三张PNG/SVG/PDF及生成源码，均已视觉检查：全链路、轨迹/演化示意、未来任务与长期评估设计。无虚构实验结果。
- [真实agent说明](../../enginering/demo/LIVE_AGENT.md)。开发plan/spec/test/todolist已同步。
- 使用research-experiment-compass、research-paper-writer、engineering-figure-agent；项目章程优先于技能中不适用的旧范围要求。

## 观察、假设、建议、未知

**文献观察：** 已读取WWW2026 Industry CFP及录用信息、WWW2027公开页面、KDD2026 ADS和ACL2026 Industry CFP，以及When Rules Fall Short、Function Calling、GenMentor、EMNLP2025 AutoQual评估内容。各会场要求不同：WWW强调Web相关的实际问题、部署/发布与持续时间、现实约束及影响；KDD ADS对部署后证据要求更严格；不能把Industry概括为放松科研要求。2027 Research日期不能冒充Industry截止日。详细来源和案例量化口径见报告。

**观察：** AutoSkill、SkillClaw、Trace2Skill、AWM、ACE等已有相邻机制。完整闭环、会话变技能、失败经验或持续更新本身不能主张首创。当前固定规则和精确去重未实现完整重要/高频排序，外层额度并非内部tokens硬预算。

**研究假设：** 可修订任务证据、增量沉淀和资源约束联合作用，可能在保留有效方法前提下减少无效候选并改善后续任务。这不是已验证结论。

**建议：** 同时测无效数量/比例、有效方法保留、未来任务成功和全生命周期成本；匹配预算强整段摘要基线，避免仅对比弱问答对。使用时间/用户隔离与先测后更新，冻结库作为长期对照，统计全部合格任务和延期覆盖。读取、遵循、成功三层分开验收。

**未知：** 真实模型连通性与质量、企业效果、真实资源变化、规则关联精度、跨用户净收益及投稿创新性。本轮无新增企业效果实证发现；软件测试不是论文效果实验。

## 下一步与状态更新

完成本机模型配置后先做控制技能真实live-check，再用授权的少量真实任务建立独立验收。按照评估协议首个决策卡比较强摘要与规则轨迹，不直接启动大规模付费实验。补充真实业务任务、Web关联和部署证据是论文首要工作。

本轮更新README索引、STATE和CHARTER；历史019及更早结论保留，并明确本轮更正。
