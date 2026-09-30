# 企业会话驱动的 Skills 生命周期研究

本目录是研究的持久入口。默认科研模式，开发链路禁用；具体约定见 [AGENTS.md](../AGENTS.md)。

接续顺序：先读 [立项章程](CHARTER.md) 和 [当前状态](STATE.md)，再读取下列相关记忆。章程保存稳定目标，状态保存当前有效判断，轮次记忆保存可追溯历史；存在冲突时核对用户原始要求和证据。

## 轮次记忆索引

**Git上传通道恢复：[076记录](memory/076_2026-09-30_git_upload_recovery.md)**——沙箱外Git执行成功，目标远端暂无可见分支；按文档与记忆范围提交推送，最终结果以远端commit核对为准。

**Git上传续办：[075执行阻塞记录](memory/075_2026-09-30_git_push_blocked.md)**——再次确认环境命令执行器仍报setup refresh错误，故无法核实本地Git、remote或仓库状态；未进行任何远端写入。恢复后先盘点所有非私有文档和文件大小、检查远端历史，再提交推送。

**Git上传准备：[074初始化记录](memory/074_2026-09-30_git_initialization_and_upload_preparation.md)**——根目录`main`分支Git初始化成功，新增排除私有会话、缓存和企业报告的`.gitignore`。GitHub凭据缺失且初始化后命令通道故障；未添加remote、暂存、提交或上传。目标仓库可见性、内容与完整大小清单仍未知。

**第一研究问题实验设计：[073轨迹恢复的受控对照](reports/073_rq1_trace_recovery_controlled_experiment.md)**——同一Trace2Skill后端对比正确归属、混合输入、普通LLM整理和阶段2＋3恢复；先只改变任务交错、不损坏证据。公开任务两轮实际交互后重排，EvoMind补自然问题证据。明确已知目标主实验与开放任务发现的边界、等预算对照、100次开发消费的起步方案及负结果停止条件；未执行。[073记忆](memory/073_2026-09-30_rq1_trace_recovery_experiment.md)。

**最新评测选型：[072公开基准与演化／评测隔离](reports/072_public_benchmarks_and_evolution_evaluation_design.md)**——核查五个候选及Trace2Skill原协议；更正PersonaMem人物／历史口径、WildChat身份推断和SkillsBench版本。建议真实案例＋公开执行＋持续更新三组证据，交错模拟明确标识；六项核心指标、对照和具体输入输出例子均为计划，未运行效果实验。[072记忆](memory/072_2026-09-29_public_benchmark_strategy.md)。

**最终标注归档：[071已完成页](datasets/evomind/accepted_071/private/index.html)**——505会话／2,674项全部完成，2,494匹配、180无匹配、0未决；58项明确人工操作，原51项保留。10项结构与完成性检查通过；不等于独立准确率验收。冻结覆盖层，尚未重写066全量会话。[说明](datasets/evomind/accepted_071/README.md) · [071记忆](memory/071_2026-09-29_final_annotation_acceptance.md)。

**历史标注入口：[070 上下文复核页](datasets/evomind/context_annotation_070/private/index.html)**——新备份51项人工选择原样保留，剩余从50会话／156项降至6会话／7项；2489匹配、178无匹配。61次调用及101项显式正文复核，10组交付检查通过；不是独立标注真值，真实时序与准确率未证明。[说明](datasets/evomind/context_annotation_070/README.md) · [记忆](memory/070_2026-09-29_contextual_annotation_followup.md)。剩余已在071处理，旧版本保留。

**历史标注入口：[069 AI辅助标注页](datasets/evomind/ai_annotation_069/private/index.html)**——28项人工选择原样保留，505会话／2,674项经初标与定向复核，剩54会话／174项；默认只显示剩余项，AI结果可查看修改。205次调用含2次结构失败，1项失败转无法判断；语义准确率未独立测量，浏览器实际点击未验收。[使用说明](datasets/evomind/ai_annotation_069/README.md) · [记忆](memory/069_2026-09-28_example_guided_ai_annotation.md)。

**人工标注入口：[068标注台](datasets/evomind/annotation_068/private/index.html)**——505条会话、2,674项，支持查看完整正文与候选、单多选／无匹配／不确定、保存草稿、确认、撤销及导入导出。数据与状态检查通过；本地文件访问被浏览器工具拦截，实际点击和视觉未验收。[使用说明](datasets/evomind/annotation_068/README.md) · [记忆](memory/068_2026-09-28_human_annotation_desk.md)。

**计数口径：[067会话数量说明](memory/067_2026-09-28_dataset_count_clarification.md)**——主集1,466条；505条待核验＝85条含未归属AI＋420条仅存在用户暂无AI；961条当前两侧均无未配项，不表示全部正确。

**当前会话数据入口：[066去重与回复匹配版](datasets/evomind/matched_066/README.md)**——1,466会话、46,224原记录全部保留；隔离137重试／11,775空AI，折叠480用户同文／5,878AI同文。18,936组AI有对应候选，798组未归属涉及85会话；原136歧义会话中62条全部AI有候选、74条仍有未归属项。模型290批含缓存与离线恢复，不是首次全成功；源记录核验通过，真实时序与语义准确率未证明。[066记忆](memory/066_2026-09-28_dedup_and_reply_alignment.md) · [方法说明](datasets/evomind/matched_066/METHOD.md)。

**单会话问题核对：[065重复AI／控制提示／标题审计](reports/065_retry_duplicates_and_title_mismatch.md)**——案例66记录中4条重试控制、56AI仅13种正文；新核对视图保留全部出现但折叠同文。标题不一致已存在于两份源包，未发现本地跨会话组装错误，上游根因未知；未全量覆盖064。[065记忆](memory/065_2026-09-28_retry_ai_duplicates_title_audit.md)。

**EvoMind清理版：[064入口](datasets/evomind/clean_064/README.md)**——1,466会话不变；移除11,775空AI正文，合并166条疑似短时完全重发；顺序冲突136→103（仅去空AI已为104）。保留原版、移除记录及原冲突标记，不将统计下降等同恢复时序。[064记忆](memory/064_2026-09-28_empty_ai_and_exact_resend_cleaning.md)。

**EvoMind全量交付：[063数据集入口](datasets/evomind/full_063/README.md)**——1,466条用户会话，136条顺序冲突待核验／1,330条未发现规则可见冲突；19条内部用途与39条无消息元数据另存，46,407条原记录全部保留。提供全文网页／MD、会话编号JSON、JSONL及逐条核验清单；未运行模型或技能实验。[063记忆](memory/063_2026-09-28_evomind_full_dataset.md)。

**三条样例表现差异：[062核对记忆](memory/062_2026-09-28_three_preview_order_difference.md)**——同一脚本沿用原文件顺序，只分组未恢复时序；第三条用户31／33／35在源文件相邻，助手32／34在后。数字排序改善局部对应但未证明全条正确；060属于原文预览，不是已完成可靠会话重建。

**顺序口径澄清：[061记忆](memory/061_2026-09-28_order_uncertainty_meaning.md)**——“待核验”表示展示先后及回合归属可能不正确；原文完整不等于时间线已验证。无新增实证发现。

**EvoMind三条样例已生成：[060预览入口与说明](datasets/evomind/preview_060/README.md)**——122条真实原消息（36用户／86助手），提供全文、会话编号JSON及回合视图；原导出顺序与数字编号候选分别注明依据，未宣称顺序已核验。正文一致性和来源哈希检查通过，未运行模型或全量整理。[060记忆](memory/060_2026-09-28_evomind_three_session_preview.md)。

**EvoMind数据集整理前：[059会话顺序依据与组装约定](reports/059_evomind_conversation_order_audit.md)**——用户确认保留全部真实企业历史会话、自然缺陷与回合视图；只读复核90处编号下降中18处同时间、72处严格方向冲突，涉及36会话。解释原包空日期、用户时间与事件序不同；尚未开始生成数据集。[059记忆](memory/059_2026-09-28_evomind_order_clarification.md)。

**论文填数入口：[058结果表模板](templates/058_paper_result_tables.md)**——六张正文候选表、八组附录及三组条件启用表；[正式术语和文献依据](reports/058_paper_metrics_and_table_design.md)区分通用指标／本文定义，覆盖M01—M40。九类由11原编号合并，其余29项非必跑子指标；所有结果留空。[058记忆](memory/058_2026-09-28_paper_metric_names_and_result_tables.md)。

**指标具体怎么测：[057数据、输入输出与九类指标例子](reports/057_metrics_data_and_examples.md)**——逐项绑定038原文、047／051产物、054真实旧新版回答；补齐[原40指标算例](reports/057_all_40_metric_examples.md)。公开任务落实到SkillsBench发票检查器及SkillFlow具体题目；已有结果、构造执行、公开题定义和假设算例分开，未执行新实验。[057记忆](memory/057_2026-09-28_metrics_data_and_examples.md)。

**当前评估框架：[056用户设计审阅与精简方案](reports/056_evaluation_framework_review.md)**——保留恢复／沉淀复用／持续更新三组主实验、九类主指标；其他指标移诊断。企业独立小参考作为主证据，SkillFlow优先、其他基准按缺口补充；核对时间、附件与标签缺口。本轮只定框架，未执行。[056记忆](memory/056_2026-09-28_evaluation_framework_review.md)。

**最新评测规划：[055 Industry实验对标与指标体系](reports/055_industry_experiments_and_metrics.md)**——核实五篇工业论文及2027 CFP；建议E0数据审计＋E1少而有效＋E2未来收益＋E3持续更新＋E4真实使用，成本／消融贯穿。明确分母、未知、资源总量与样本规模口径；本轮未执行实验。[055记忆](memory/055_2026-09-28_industry_experiments_and_metrics.md)。

**最新自进化案例：[054个人使用反馈→原技能v2→新任务复用](reports/054_personal_skill_evolution_case.md)**——真实OpenClaw使用051已有技能；构造后续任务和个人意见，2问答→1轨迹→1workflow→1更新候选→1处补丁，旧/新版同任务新会话对照显示个人格式偏好迁移。保留超时与来源回显失败，最终保存响应续接；92项检查通过，不宣称首次无断点或总体收益。[054记忆](memory/054_2026-09-27_personal_skill_evolution.md) · [新版技能](artifacts/054_personal_skill_evolution/SKILL.md)。

**简要案例入口：[053五阶段案例简版](reports/053_038_case_brief.md)**——严格按会话采集、任务识别与线索标注、轨迹恢复、工作流聚合、技能封装说明真实例子及每步输出；详细依据仍见052和051。[053记忆](memory/053_2026-09-27_brief_case_five_stages.md)。

**最新案例解读：[052逐阶段人话复盘](reports/052_038_first5_case_walkthrough.md)**——用两条真实合同审阅会话说明每一步拿到什么、如何改变信息表示、向下一步交付什么；含一条用户原话贯穿五阶段的例子。它是051结果的可读复盘，没有新增实验。[052记忆](memory/052_2026-09-27_first5_case_explanation.md)。

**最近真实验收：[051定向前五阶段验收与三个技能包](reports/051_targeted_first5_acceptance.md)**——按038索引回查A/B48条原消息→8问答→2轨迹→3workflow→3READY，最终同版断网9响应重放与产物hash通过。两次全fresh失败、后续修正和缓存续接均保留，不能称首次全新推理成功；文件编辑/专业质量未验证，候选粒度及能力宣称仍有问题。[复现命令](reviews/051_preparation/README.md)｜[051记忆](memory/051_2026-09-26_targeted_first5_generation_acceptance.md)。

**历史实验前审查：[050前五阶段开跑审查](reports/050_first5_preflight_review.md)**——原始数据预检通过；指定recovered JSON仅是人工参考索引。当轮发现旧库依赖、预算/坏缓存恢复、方法ID交接及后台调度等断点，判定NOT_READY；主要结构断点现已在051修正。050的免费控制与[证据摘要](reviews/050_preflight/review-summary.json)保留，当轮应用代码未改、付费调用0。

**个人工作台基础：[049阶段4/5实现与个人工作台验收](reports/049_stage45_implementation_and_harness_acceptance.md)**——新版轨迹经workflow轮廓聚类、方法台账与冻结交接，独立OpenClaw creator真实生成、官方打包并由测试人员采纳；个人 `/skills` 与 `/chat` 已可选版对话。038两条生成轨迹产出两个workflow，一份skill被实际读取并在构造后续任务产生文件；企业质量、减量与成本优势未证明。[逐项验收](../enginering/demo/STAGES_45_ACCEPTANCE.md)｜[048设计历史](reports/048_stage45_contract_and_design.md)。

**前三阶段基础：[047前三阶段实现与验收](reports/047_stage123_implementation_and_acceptance.md)**——按046契约完成70原消息→14问答→4任务轨迹；当轮56项测试、真实模型及构造控制验收通过。[逐项验收与私有证据入口](../enginering/demo/STAGES_123_ACCEPTANCE.md)。其“待阶段4适配”由049实施修正；仍不宣称效果/成本收益。

**当前契约：[046用户新版契约快照](contracts/046_twelve_stage_contract_user_revision.md)第5节**——阶段1问答整理、阶段2逐对候选标注、阶段3交错轨迹恢复；[046前后改动报告](reports/046_revised_contract_stage2_stage3_design_delta.md)明确替代040/043冲突项。046当轮仅设计，047已实施前三阶段。

**最新案例展示：[045完整会话四回合](cases/038_contract_multi_review/private/045_conv_f586a09e7356_full_rounds.md)**——受控企业材料，仅放私有目录；原37消息按行序展示4个真实 `{user, assistant}` 回合，解释人工 `replyTo` 与阶段3尚未验收。[044真实案例输入血缘与语义](reports/044_038_input_lineage_and_semantics.md)说明原70消息与041预分组输入；[043轨迹恢复设计](reports/043_trace_recovery_stage3_implementation_design.md)遵循[040十二阶段契约](reports/040_twelve_stage_contract_and_task_detection.md)。仅文档核对，未改Demo。

**真实案例入口：[038合同多立场案例准备](reports/038_contract_multi_review_case_preparation.md)**——同一成员三立场会话，70条原始消息与14轮轨迹已抽取；排除技能请求，前两条生成来源/较晚一条留出。该案例报告的“原句导入”带人工replyTo，039补测无replyTo条件；原DOCX缺失。[037新包结构判断](reports/037_skill_mining_data_feasibility.md)与[036原始导出](reports/036_real_export_structure_review.md)为背景。

**任务与数据：[034任务定义、统计与全链路案例](reports/034_task_data_and_full_loop_case.md)**——035已将第3节按11环节展开任务描述、输入、处理与输出；基于031真实模型构造验收，企业统计待真实数据。

**最新研究判断：[033 Industry技术链条与深化路线](reports/033_industry_technical_chains_and_research_directions.md)**——六篇方法/实验细读；优先深化Agent经验归因与选择性学习，条件性训练小型归因/效用模型；尚未实施或证明收益。

**当前算法：[031实现与验收](memory/031_2026-09-24_multitrace_implementation.md)**——NEW轨迹聚类、UPDATE版本池、成功/失败/UNKNOWN分析、Patch归纳应用已接入；35项测试及构造数据真实闭环通过。独立并行/层次merge、企业效果与成本优势尚未验证。[030方案](reports/030_demo_trace2skill_upgrade_plan.md)为实施前历史。

**当前Demo：[031多轨迹真实验收](../enginering/demo/MULTITRACE_ACCEPTANCE.md)**——3轨迹→1个NEW、2条使用反馈→1个UPDATE，官方封装、组织审核和Bob消费通过；构造业务数据，不是企业效果实验。024验收保留历史。

**论文统一入口：[022论文概念文档v3](reports/022_论文概念文档.md)**——对应正文直接替换为当前聚类/分析/patch方法，25页PDF与六张矢量图；保留四篇Industry对标、E1/E2/E3和完整大纲。[排版PDF](../output/pdf/skillsloop_concept_and_technical_assessment.pdf)｜[技术评估](reports/025_industry_technical_assessment.md)。

021最新：[具体执行计划](reports/021_execution_plan.md)、[需要团队提供的数据与评估](reports/021_data_handoff.md)、[交接模板](templates/021/README.md)。用户已提供模型配置；不接入InsightWeaver，接入场景不冒充部署证据。真实通路状态见021记忆。

020历史交付：[论文大纲与差距评估](reports/020_paper_blueprint.md)、[评测协议](reports/020_evaluation_protocol.md)、[真实agent操作](../enginering/demo/LIVE_AGENT.md)。用户已明确要求实验设计，早期“仅探索、不设计实验”为历史阶段要求。模型配置与通路最新状态见021。

| 编号 | 日期 | 主题 | 记录 |
| --- | --- | --- | --- |
| 066 | 2026-09-28 | 全量去重、重试分流与逐需求回复匹配 | [回复匹配记忆](memory/066_2026-09-28_dedup_and_reply_alignment.md) |
| 065 | 2026-09-28 | 单会话重复AI、重试控制和标题不匹配核对 | [案例审计记忆](memory/065_2026-09-28_retry_ai_duplicates_title_audit.md) |
| 064 | 2026-09-28 | 空AI与短时完全重发清理、顺序冲突前后对照 | [清理记忆](memory/064_2026-09-28_empty_ai_and_exact_resend_cleaning.md) |
| 063 | 2026-09-28 | EvoMind全量会话整理、136条顺序冲突清单 | [全量数据记忆](memory/063_2026-09-28_evomind_full_dataset.md) |
| 060 | 2026-09-28 | 三条真实企业会话、原文回合视图与排序候选预览 | [样例整理记忆](memory/060_2026-09-28_evomind_three_session_preview.md) |
| 059 | 2026-09-28 | EvoMind基础会话数据集口径确认、原始顺序依据审计 | [顺序核对记忆](memory/059_2026-09-28_evomind_order_clarification.md) |
| 058 | 2026-09-28 | 论文指标专业命名、六篇文献对标及可填写结果表 | [论文表格记忆](memory/058_2026-09-28_paper_metric_names_and_result_tables.md) |
| 057 | 2026-09-28 | 每项指标绑定实际数据、输入输出与真实／假设算例 | [指标实例记忆](memory/057_2026-09-28_metrics_data_and_examples.md) |
| 056 | 2026-09-28 | 用户评估框架审阅、指标精简与企业／公共数据分工 | [框架记忆](memory/056_2026-09-28_evaluation_framework_review.md) |
| 055 | 2026-09-28 | Industry实验对标、五个证据单元与指标分母 | [调研记忆](memory/055_2026-09-28_industry_experiments_and_metrics.md) |
| 054 | 2026-09-27 | 个人技能消费、反馈更新与新任务偏好迁移单例 | [演化记忆](memory/054_2026-09-27_personal_skill_evolution.md) |
| 053 | 2026-09-27 | 逐阶段简要案例：采集、识别标注、恢复、聚合、封装 | [简版记忆](memory/053_2026-09-27_brief_case_five_stages.md) |
| 052 | 2026-09-27 | 真实案例前五阶段逐步转换与人话说明 | [案例复盘记忆](memory/052_2026-09-27_first5_case_explanation.md) |
| 051 | 2026-09-26 | 定向会话正文回查、前五阶段生成、失败保留与断网重放 | [生成验收记忆](memory/051_2026-09-26_targeted_first5_generation_acceptance.md) |
| 050 | 2026-09-26 | 前五阶段输入、运行断点、免费预检与可复现开跑标准 | [实验前审查记忆](memory/050_2026-09-26_first5_preflight_review.md) |
| 049 | 2026-09-26 | 阶段4/5实现、真实技能包、个人工作台与用量边界 | [实现验收记忆](memory/049_2026-09-26_stage45_implementation_harness.md) |
| 048 | 2026-09-26 | 阶段4方法与流程聚类、阶段5独立creator封装交接设计 | [契约设计记忆](memory/048_2026-09-26_stage45_contract_design.md) |
| 047 | 2026-09-26 | 前三阶段实现、原事件真实模型验收与证据边界 | [实现记忆](memory/047_2026-09-26_stage123_implementation.md) |
| 001 | 2026-09-18 | 科研立项与工作规范初始化 | [首轮记忆](memory/001_2026-09-18_initialization.md) |
| 002 | 2026-09-18 | WWW Industry 要求、量化方式与近邻研究 | [调研记忆](memory/002_2026-09-18_www_industry_landscape.md) |
| 003 | 2026-09-18 | 现有链路、任务轨迹、价值筛选与使用后演化 | [深度分析记忆](memory/003_2026-09-18_trajectory_value_evolution.md) |
| 004 | 2026-09-18 | 更正报告受众与阶段目标：团队理解、闭环落地 | [报告重写记忆](memory/004_2026-09-18_team_report_revision.md) |
| 005 | 2026-09-18 | 有价值任务与任务轨迹的定义及边界 | [定义调研记忆](memory/005_2026-09-18_task_trajectory_definitions.md) |
| 006 | 2026-09-18 | 现有系统的任务发现、埋点与关联方案 | [任务发现方案记忆](memory/006_2026-09-18_task_discovery_instrumentation.md) |
| 007 | 2026-09-18 | 前后改动、实例行为与阶段效果对照 | [改动对照记忆](memory/007_2026-09-18_before_after_changes.md) |
| 008 | 2026-09-20 | 技能涌现前后流程图 | [流程图记忆](memory/008_2026-09-20_flow_comparison.md) |
| 009 | 2026-09-20 | 组织成员、个人／企业库与涌现源码图谱及 MCP 索引 | [源码索引记忆](memory/009_2026-09-20_scoped_codegraph.md) |
| 010 | 2026-09-20 | 源码核对、任务埋点与可落地升级方案 | [源码方案记忆](memory/010_2026-09-20_source_verified_upgrade_plan.md) |
| 011 | 2026-09-20 | 数据层复用与新增表建议收敛 | [表复用记忆](memory/011_2026-09-20_table_reuse.md) |
| 012 | 2026-09-20 | 已有表复用与零新表方案边界澄清 | [复用澄清](memory/012_2026-09-20_table_reuse_clarification.md) |
| 013 | 2026-09-20 | 全面复核升级方案、Trace2Skill、成本与格式兼容 | [全面复核记忆](memory/013_2026-09-20_comprehensive_upgrade_audit.md) |
| 014 | 2026-09-20 | 减量与预算约束、按使用分流、规则轨迹算法流程图 | [规则轨迹记忆](memory/014_2026-09-20_rule_trace_constraints.md) |
| 015 | 2026-09-20 | Industry Track 独立贡献、近邻重叠与论文成熟度评估 | [贡献评估记忆](memory/015_2026-09-20_industry_contribution_assessment.md) |
| 016 | 2026-09-20 | Skills开发准备、自动封口、对话内标记与grill决策 | [开发准备记忆](memory/016_2026-09-20_development_preparation.md) |
| 017 | 2026-09-20 | 轨迹采集首批代码、128项回归与KM外部依赖 | [实现记忆](memory/017_2026-09-20_trace_capture_implementation.md) |
| 018 | 2026-09-20 | KM v1全链路适配、真实数据库迁移与143项软件测试 | [v1闭环记忆](memory/018_2026-09-20_km_v1_full_loop.md) |
| 019 | 2026-09-23 | 独立OpenClaw demo、整体算法、14项软件测试和原生CLI验证 | [独立原型记忆](memory/019_2026-09-23_standalone_openclaw_demo.md) |
| 020 | 2026-09-24 | 真实模型消费接口、论文大纲、全链路配图与评测方案 | [论文与agent记忆](memory/020_2026-09-24_live_agent_paper_plan.md) |
| 021 | 2026-09-24 | 企业个性化Agent、真实模型配置、详细实验计划与数据交付 | [执行计划记忆](memory/021_2026-09-24_enterprise_experiment_plan.md) |
| 022 | 2026-09-24 | 论文概念、全链路与贡献定位，附三实验及论文大纲 | [概念文档记忆](memory/022_2026-09-24_paper_concept.md) |
| 023 | 2026-09-24 | Demo封装、入库、消费及交付的实现与验证边界 | [现状澄清](memory/023_2026-09-24_demo_status_clarification.md) |
| 024 | 2026-09-24 | 官方skill-creator初始化、Windows执行修复与真实模型全链路验收 | [真实闭环记忆](memory/024_2026-09-24_real_loop_acceptance.md) |
| 025 | 2026-09-24 | 当前实现、Trace2Skill与简单Prompt的边界 | [边界对照记忆](memory/025_2026-09-24_current_vs_trace2skill_prompt.md) |
| 026 | 2026-09-24 | 现有聚类、成功失败埋点与多轨迹Patch池评估 | [Patch池评估记忆](memory/026_2026-09-24_multitrace_patch_pool.md) |
| 027 | 2026-09-24 | 论文技术补充、四篇Industry对标、六张矢量图与PDF | [技术评估记忆](memory/027_2026-09-24_technical_assessment_pdf.md) |
| 028 | 2026-09-24 | Trace2Skill模型微调与成功/失败分析器定义 | [分析器记忆](memory/028_2026-09-24_trace2skill_analyzers.md) |
| 029 | 2026-09-24 | 论文概念文档文案去内部化与PDF重生成 | [PDF修订记忆](memory/029_2026-09-24_concept_pdf_deai.md) |
| 030 | 2026-09-24 | 独立Demo与Trace2Skill差距、升级价值和P0–P4计划 | [升级计划记忆](memory/030_2026-09-24_demo_patch_upgrade_plan.md) |
| 031 | 2026-09-24 | 多轨迹聚类、三类分析、Patch应用、真实验收与PDF原文替换 | [实现记忆](memory/031_2026-09-24_multitrace_implementation.md) |
| 032 | 2026-09-24 | v3目标变化感知与修订归因方法评估 | [方法评估记忆](memory/032_2026-09-24_v3_method_idea_assessment.md) |
| 033 | 2026-09-24 | 六篇Industry技术链、Agent算法与模型层深化路线 | [技术链记忆](memory/033_2026-09-24_industry_technical_chains.md) |
| 034 | 2026-09-24 | 任务定义、数据描述与统计、真实执行全链路案例 | [数据案例记忆](memory/034_2026-09-24_task_data_full_loop_case.md) |
| 035 | 2026-09-24 | 全链路实际案例11步任务描述与输入输出 | [逐步案例记忆](memory/035_2026-09-24_case_step_inputs_outputs.md) |
| 036 | 2026-09-26 | 真实企业原始导出组织理解与时间缺失核验 | [数据初核记忆](memory/036_2026-09-26_real_export_structure_review.md) |
| 037 | 2026-09-26 | 新包关联、短反馈损失与真实会话到skill可行性 | [链路可行性记忆](memory/037_2026-09-26_skill_mining_data_feasibility.md) |
| 038 | 2026-09-26 | 合同多立场原始数据、任务轨迹与无模型案例预检 | [真实案例记忆](memory/038_2026-09-26_contract_multi_review_real_case.md) |
| 039 | 2026-09-26 | 无replyTo补测、LLM任务图和方法族复用升级方案 | [语义升级记忆](memory/039_2026-09-26_llm_task_graph_design.md) |
| 040 | 2026-09-26 | 固定十二阶段交接契约、任务识别LLM算法边界 | [契约与识别记忆](memory/040_2026-09-26_twelve_stage_contract_and_task_detection.md) |
| 041 | 2026-09-26 | LLM任务识别实现、038真实案例验收与负结果 | [实现验收记忆](memory/041_2026-09-26_task_detection_038_validation.md) |
| 042 | 2026-09-26 | 038轨迹恢复与workflow聚合源码及隔离推演审阅 | [第3/4阶段审阅记忆](memory/042_2026-09-26_trace_workflow_038_audit.md) |
| 043 | 2026-09-26 | 遵循040契约的第3阶段轨迹恢复实现改动设计 | [轨迹恢复设计记忆](memory/043_2026-09-26_trace_recovery_stage3_design.md) |
| 044 | 2026-09-26 | 038原始文件、041实际输入及预分组语义澄清 | [输入血缘记忆](memory/044_2026-09-26_038_input_lineage_clarification.md) |
| 045 | 2026-09-26 | 完整会话四回合、人工replyTo及轨迹恢复证据边界 | [会话案例记忆](memory/045_2026-09-26_conv_f586a09e7356_rounds_and_replyto.md) |
| 046 | 2026-09-26 | 新版契约、逐对多目标识别与交错轨迹恢复设计修订 | [新版契约记忆](memory/046_2026-09-26_revised_contract_stage23.md) |

## 调研产物

- **当前载体：[独立OpenClaw demo](../enginering/demo/README.md)**；[019整体算法与边界](reports/019_standalone_algorithm_and_demo.md)。用户暂不嵌入InsightWeaver，以下018集成是历史产物。024真实模型功能验收已通过；企业效果未验证。

- **历史实施：[KM v1闭环适配](../enginering/insightweaver/docs/skills-upgrade/V1_ADAPTATION.md)**：会话任务→受控生成→个人采纳／原组织提审→使用后UPDATE已在本仓接通；零新表，隔离PostgreSQL迁移及143项软件测试通过。真实KM／生产未联调；CAS、内部tokens、草稿沙箱边界和类型检查既有错误见[实施记录](../enginering/insightweaver/docs/skills-upgrade/IMPLEMENTATION.md)。
- **当前论文贡献评估：[015 Industry Track 贡献评估](reports/015_industry_contribution_assessment.md)**：建议以可修订任务证据、增量沉淀和资源约束为主线；Trace2Skill作为近邻参考。潜在贡献尚未实证成立，不改变014落地约束。
- **当前算法与约束：[014 规则轨迹、直接分流与预算方案](reports/014_rule_based_trace_and_budget.md)**：用户要求减少无效及单批沉淀、保留有效能力、模型调用至少不增加；取消全库匹配，明确运行关联与跨回合trace规则流程。尚未实施。
- [013 全面复核版](reports/013_comprehensive_upgrade_plan.md)：继续作为源码事实、零新表与原格式发布／应用的依据；其路由、默认多次提炼和资源增量路线已由014修正。

- 历史方案：[010 源码升级方案](reports/010_source_verified_upgrade_plan.md)、[011 表复用建议](reports/011_reuse_existing_tables.md)。013 已统一其更正，不再将新表数量设为前提。

- **源码理解入口：[限定源码图谱](reports/009_scoped_codegraph.md)**；[CodeGraphMCP 索引与查询方法](codegraph/README.md)。只覆盖组织成员、个人／企业 skills 库、涌现链路及直接边界；静态源码核验，不是生产验证。

- [链路升级流程图对照](reports/008_flow_comparison.md)：双列主流程、三处升级与改稿实例差异。

- [前后改动与最终效果对照](reports/007_before_after_changes.md)：逐环节改动、同一会话前后产物、三个阶段能力与收益边界。

- [任务发现与埋点落地方案](reports/006_task_discovery_and_instrumentation.md)：事件触发位置、字段、后台任务关联、经验提炼时机、旧链路适配与分步落地。

- [有价值任务与任务轨迹：团队判断口径](reports/005_valuable_tasks_and_trajectories.md)：业务价值、沉淀价值、新建必要性、研究依据与贯穿案例。

- [WWW Industry Track 调研与本项目研究定位](reports/002_www_industry_research_landscape.md)：官方要求、三篇工业案例、评估指标、近邻工作、候选创新与否定条件。
- **当前团队报告：[Skills 涌现与演化：当前系统、主要不足与落地方向](reports/初步洞察报告.md)**：当前六阶段链路、主要问题、任务与噪声、使用后演化及落地顺序；量化仅作探索，无实验设计。
- [历史研究分析稿](reports/003_trajectory_value_evolution_report.md)：保留轮次 003 的分析过程，已被团队报告取代，不作为当前阶段的实验或论文计划。

## 记录格式

后续轮次按 `NNN_YYYY-MM-DD_topic.md` 命名，编号递增。同一天可以有多条记录。至少包含：

1. 本轮问题及其与研究主线的关系。
2. 用户新增或确认的要求。
3. 做了什么，以及证据或产物的位置。
4. 洞察与发现：标注“观察 / 假设 / 建议 / 未知”，说明依据与适用范围。
5. 决策与理由，包括否定、停止或修正的路线。
6. 未解决问题及建议的下一步；区分建议与已授权工作。
7. 对章程、当前状态和历史结论的更新。

无实验或无实证发现也要如实记录。每轮结束前检查记忆已落盘、索引可定位、当前状态已同步。
