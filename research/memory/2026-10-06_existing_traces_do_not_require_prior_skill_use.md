# 2026-10-06｜已有轨迹不以事先使用技能为学习门槛

## 用户要求与本轮范围

用户强调已经提供执行轨迹，询问是否必须使用skills后产生。仅澄清来源要求和更正此前可能过度设置的门槛；未启动模型、改源码或生成技能。

## 证据支持的结论

1. **离线技能学习不要求历史轨迹曾使用待生成或当前待更新技能。**初始技能目录是演化器的修改对象，历史轨迹是经验来源，二者是独立输入。
2. 官方成功分析与LLM-only失败分析的示例均读取`agent_output/cli_only_logs`，实例分析不要求当前skill目录或技能hash；combined记录只归一化实例、来源、经验和成败类别。演化器独立读取初始技能再对经验做MAP，没有核验历史使用过同一初始技能。
3. [论文§2.2](https://arxiv.org/html/2603.25158v5#S2.SS2)的主实验则确实让冻结agent加载初始技能采样，属于受控实验设置。使用企业既有历史不逐项复现该采样设置，须披露来源差异；不能因此声称这些历史不能生成技能。
4. 成败与材料证据是另一条轴。没有使用技能不等于失败、未知或噪声；已经存在轨迹不自动证明业务成功。原成功/失败分析的证据前提仍应逐任务核对，文件缺失只影响需要文件验证的具体分支。

源码：[成功入口示例](../baselines/Trace2Skill/analysis/run_success_analysis_llm.py:14)、[失败LLM入口示例](../baselines/Trace2Skill/analysis/run_error_analysis_llm.py:11)、[初始技能独立读取及MAP](../baselines/Trace2Skill/skill_evolver/parallel_evolving_agent.py:3074)、[combined归一化](../baselines/Trace2Skill/skill_evolver/parallel_success_evolving_agent.py:46)。未用LLM-only替换Agentic主分支执行；上述仅证明输入来源机制。

## 更正与后续

更正[前轮核查](2026-10-06_trace2skill_native_completion_requirement.md)的解释边界：不能把论文采样顺序升格为“用户必须重新使用初稿跑旧任务”的门槛。已有[固定历史研究设定](../reports/2026-10-05_frozen_history_evomind_supply.md)继续有效：使用已经提供的企业轨迹，不要求重跑或改成公开benchmark。

此前6整会话的结果未知判断仅针对那个冻结输入，不扩展为用户所有已提供轨迹都无成败证据。后续应优先核对已有具体轨迹的来源、任务边界、可见动作及结果，再决定原处理器能实际覆盖哪些；不以轨迹没使用技能为排除理由。弱初稿的初始化来源问题仍与轨迹来源分开。

本轮无新增实验实证，既有19请求/已报告265639tokens＋1超时未知、原生成物和失败保持。
