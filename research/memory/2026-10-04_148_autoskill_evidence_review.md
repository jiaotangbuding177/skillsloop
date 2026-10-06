# 148 v4结果与AutoSkill轨迹分析证据复核

日期：2026-10-04。承接[239原结果](239_2026-10-04_148_v4_paired_final.md)。本轮保持科研模式；采用research-experiment-compass做问题归因；只分析已有结果和固定上游，没有改Demo、运行模型、启动或恢复实验／服务。

## 用户已确认

- 用户提供148结果、账本、采集与冻结库路径，要求读取本地结果，形成实验报告，点对点分析AutoSkill轨迹痛点，为自己的算法建立依据。
- 本轮强基线为AutoSkill；[073](../reports/073_rq1_trace_recovery_controlled_experiment.md)的Trace2Skill方案保留历史，不冒充本轮基线。
- 十二阶段主线和阶段2语义抽取、阶段3关系核验／程序拼接的责任保持；无新增开发或实验执行授权。

## 证据支持的新增观察

1. 实际材料位于当前项目`research/experiments/148_tau2_retail_autoskill`，不是用户原D:/skillloop路径。直接重算B0/B1各160场，126→134成功，20胜12负128平、+5pp；原10k任务cluster bootstrap[-2.5,+12.5]pp可复现。40任务，不是160独立任务；未证显著收益。
2. 平均耗时468.43→600.92秒（+28.28%），业务工具7.33→7.81、原生显式错误23→38；消费者usage缺失，成本未知。整个148累计36359请求不能当v4成本。
3. 演化70条仅5奖励1；50正常结束后评分未通过，15异常终态0且无评分分项。GLM采集、DeepSeek正式消费。149工具错误覆盖40/70条来源。
4. 本适配每条工具结果有4000字符上限，但本批没有实际超限；不能把截断作为效果原因。工具文本保留，调用/result身份未结构化保留，reward/termination仅存manifest未进学习入口。
5. 最终使用trajectory抽取，`include_tool_events=True/success_only=False`，并有手写零售HINT。初始protocol/versions/source_audit的conversation口径过时，原论文query-only不能概括实际入口。官方固定源码已经支持错误恢复、任务边界、技能维护和反馈更新；不能声称完全没有这些能力。
6. 原生trajectory把来源整体包装成单条user文本，选择主要完成链，每次ingest最多1候选；没有独立输出本项目的问答归属／反馈→尝试／要求替代关系。包装success=True未直接进抽取prompt，不能当“模型被喂成功标签”的解释。
7. task0仅有一次失败交换，后续成功为自述且用户认可。task50对应support0.1.19，相邻描述／触发词加入撤销分支而源无撤销写；task96对应exchange0.1.13，源自报下单而无下单调用，后续描述加入new-orderfallback、冻结正文包含步骤。相邻完整正文和抽取响应未补齐，因果边界保留。
8. task50虽然官方奖励1，但转人工action未匹配、评分只用DB/NL，不能据此证明撤销完成。task39/60/38/64的部分差异受模拟器提前结束／选择变化及静态DBgold影响，不能一律归生成；task55消费阻塞为助手自述，实际read返回根因未知。task49/97有行为正差，97与源96对象／需求近似，不能当OOD证据。
9. 历史159/160只能支持保存审计的读取尝试率，脚本不核成功返回或完整正文；当前无原sqlite及完整session映射，不能独立重建，也不能排除加载故障。对239“真实读取率”增加资格更正，旧文不删除。
10. 当前库30文件LF规范化后都匹配原hash，29严格字节差异为CRLF迁移；不认定历史热改。原最终报告“唯一差异skillsDir”与B1显式读取提示不一致，效果属于处理包。运行／协议最终快照尚需补齐。

## 研究假设与建议，尚未证明

- 将贡献聚焦于混合会话中任务、对象、要求版本、尝试、回执、反馈和修订关系恢复；由证据状态控制经验泛化，而非增加一段总结prompt。
- 比较正确分组、混合直接、普通LLM整理、阶段2+3恢复，共用同一个AutoSkill后端，保持源内容／工具证据／HINT／预算及消费条件一致；不能偷偷削弱基线或给本方法多次生成机会不计成本。
- 先验归属F1、反馈与修订归属、无证据完成判定，再看独立任务成功率／退化／总资源。未知仍正常纳入，不能伪装成功。
- 任务恢复、下游API验收、技能消费错误分开归因。更多完整尝试不等于更多应入库技能；有效覆盖与总skills／资源预算均待测。
- 当前已审阅test案例，后续方法开发属于事后探索；需要演化侧开发留出和冻结独立评测，不把再调这40题包装为全新泛化结果。

## 未知与没有发生的工作

SkillsLoop与AutoSkill恢复前后的直接效果差值未知；本轮没有新增方法效果实验。原生加载成功率、完整消费token／费用、历史实际vendor／schema字节、问题占比及能力扩展对12场退化的因果作用未知。未改变其他聊天的活动实验状态，不撤销其已有授权。

## 产物与后续入口

- [综合实验报告](../reports/2026-10-04_148_autoskill_baseline_and_trajectory_recovery.md)。
- [统计审计](../reviews/267_autoskill_analysis/statistics_audit.md)与[JSON](../reviews/267_autoskill_analysis/statistics_audit.json)。
- [作者机制](../reviews/autoskill_148_readonly/author_mechanism.md)。
- [案例及版本来源](../reviews/autoskill_148_readonly/case_review.md)与[JSON](../reviews/autoskill_148_readonly/case_evidence.json)。
- [固定官方工具边界](../reviews/autoskill_148_readonly/retail_tools_verification.md)。

下一步优先补v4最终协议／完整read返回与source快照，再冻结同后端的恢复对照。此为建议，不自动启动付费实验。
