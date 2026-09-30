# 058｜论文指标正式命名、文献依据与结果表设计

日期：2026-09-28。仅研究设计及模板，不执行实验。承接[057具体数据与例子](057_metrics_data_and_examples.md)；完整可填表格见[论文结果表模板](../templates/058_paper_result_tables.md)。

## 1. 正确理解“九类”和“40项”

**不是9个大指标各有若干子指标、合计40个必测小指标。**M01—M40是完整的候选指标／运行记录字典，其中有重复视角、复合条目、展示方式及尚不执行的项目。

- 九类主指标由11个原编号组成：M02、M07、M10、M12、M13、M18、M19、M21、M32、M33、M37。M12/M13合并呈现候选质量，M19/M21合并呈现任务成功及差值。
- 其余29个编号保留为诊断、运行有效性、后续真实使用或可选扩展；不是九类主指标的全部从属项。
- M04同时含ARI和VI，M37同时含请求、tokens及金额，因此40也不是严格的40个数值列；M20本质是图的组织方式。
- 论文按三个问题组织：**恢复是否正确；沉淀是否少而有用；更新是否帮助未来且不损坏既有能力。**资源和真实使用证据贯穿，不设置一个不透明综合分数。

## 2. 其他论文如何设计指标和结果表

本轮重新查阅以下原文的指标段、表格及图注。前三项Industry身份依据055已核对官方日程／发表记录；后三项用于评价方法参考，不称为Industry论文。这里借鉴设计，不搬用他人的数值作本项目成绩。

| 论文及原文位置 | 论文实际使用的指标／表设计 | 本文借鉴与边界 |
|---|---|---|
| [When Rules Fall Short，WWW 2026 Industry，§6、表1及阶段分析](https://arxiv.org/html/2601.11634v1) | 主表为方法×两个业务集合，报告Precision、Recall、Weighted-F1、Macro-F1；另有聚类ARI、线上业务、治理周期与算力 | 恢复质量与业务收益分开，资源不能省略；不照搬其分类Macro-F1作为我们的任务归属分数 |
| [Data-Driven Function Calling Improvements，WWW 2026 Industry，§4.1.2、表1–3、§5.2](https://arxiv.org/html/2604.05387v1) | 离线工具选择F1，主比较与组件消融分表；在线区分Tool Execution Rate、Final Answer Accuracy、Good/Bad/Same比较 | 读取／执行与最终完成分开。我们的skill读取率不是成功率；候选审核也不是新任务效果 |
| [GenMentor，WWW 2025 Industry，§5、表1–2](https://arxiv.org/html/2501.15749v1) | 技能映射Precision/Recall，目标对齐等任务专门评分；按产物组织表，另做人类校准和用户研究 | 允许针对任务定义新评价项，但要公开评分规则并校准；不能把主观量表写成真实任务成功 |
| [Online Conversation Disentanglement with Pointer Networks，EMNLP 2020，§4.2](https://aclanthology.org/2020.emnlp-main.512.pdf) | Link-level P/R/F1；聚类ARI、VI和Exact Match F1 | 区分连接和完整分组。本文同任务Pairwise F1是标准成对评价的任务化使用，**不是直接复制该论文Link F1**；该文完整匹配排除单消息线程，本文保留单轮任务并说明改动 |
| [SkillsBench v4，§4、Appendix D与N](https://arxiv.org/html/2602.12670v4) | 同条件有／无技能；task-macro pass rate，先在每任务内平均重复，再平均任务；报告绝对增益和置信区间 | 新任务成功率采用明确任务权重与配对差。重复3次不等于三个独立任务，pass@3也不等于平均通过率 |
| [SkillFlow v1，§2.4–2.5、表1](https://arxiv.org/html/2604.17308v1) | 顺序执行后更新，按族重置；任务成功、交互轮数、费用、输出tokens、技能数量和使用率并列，表内比较vanilla与evolution | 借鉴先测后学和效果—资源并列；本文另设同初始冻结库与保持集。原文§2.5与表注对技能数量描述有“最终保留／累计生成”的口径差异，本文主动拆开两者 |

由这些案例归纳的建议是：**成熟论文没有统一的指标数量要求，通常使用少量主效果指标，再用组件、资源和真实使用分析解释结果。**九类是研究材料管理口径，不要求主表有九列，也不要求所有40项出现在投稿稿件中。

## 3. 九类主指标的论文正式名称

标记：**通用**＝采用既有评价形式；**适配**＝形式通用但对象／单位由本研究明确；**本文定义**＝本项目拟定的操作化口径；**运行统计**＝工程量，不包装成新算法评价理论。英文名、缩写是写作约定，不是原创性证据。

| 主类 | 推荐中文名 | 论文英文名／表头 | 对应编号 | 性质 |
|---|---|---|---|---|
| 1 | 任务归属成对F1 | Task Assignment Pairwise F1 / Pair-F1 | M02 | 通用成对P/R/F1，适配到任务片段归属 |
| 2 | 带类型关系F1 | Typed Relation F1 / Rel-F1 | M07 | 通用关系评价形式，关系集合和端点匹配由本文定义 |
| 3 | 无效候选负担 | Invalid Candidate Count / #Invalid；Invalid Candidate Rate / ICR | M12/M13 | 本文候选审核口径；还必须并列Unresolved Rate |
| 4 | 条件化方法召回率 | Condition-aware Method Recall / CMR | M10 | 本文定义；不能冒称领域现成标准 |
| 5 | 任务成功率及绝对增益 | Task Success Rate / SR；Absolute Success Gain / ΔSR | M19/M21 | 通用；任务验收及聚合口径需明确 |
| 6 | 顺序评测成功增益 | Prequential Success Gain / ΔSR_seq | M32 | 本文对冻结库的配对差；原CEG保留作历史别名 |
| 7 | 旧能力退化率 | Regression Rate / RR | M33 | 本文定义的旧成功→新失败比例；**不是直接等同持续学习的BWT或Forgetting** |
| 8 | 技能库规模 | Skill Library Size / #Skills；Library Length | M18 | 通用规模统计；数量小只有在保留效用前提下才好 |
| 9 | 全周期模型资源 | Lifecycle LLM Usage and Cost | M37 | 请求数、各类tokens、金额分开，不能合成无单位单分数 |

不建议把所有指标都发明一个新缩写。Pair-F1、Rel-F1、CMR、SR、ΔSR、RR在表头解释后即可；#Invalid、#Skills、LLM Requests、Tokens、Cost使用直观名称。

## 4. 论文必须写清楚的定义

### 4.1 分组与关系

固定原始可评价片段集合。参考同任务片段对为G，预测为P：Precision=|P∩G|/|P|，Recall=|P∩G|/|G|，F1=2TP/(2TP+FP+FN)。不跨无关用户窗口制造大量容易负例；漏抽的参考片段不能从分母移除。单轮遗漏另以完整轨迹／单轮召回诊断。

Rel-F1对“源端点、目标端点、关系类型”三元组作同样计算；原文片段定位与允许的端点对齐规则在评分前固定。不把模型生成的不同ID直接比较，也不因一句长文本匹配到一句短文本就随意给分。缺少参考的关系记不可评，不当负例。

默认表内报告全评测窗口汇总TP/FP/FN的micro F1，并在附录另报按窗口分布。组内正对和跨窗口关系均受预设评价范围约束。ARI／VI仅用于明确单归属子集，不能把多目标强行压成单标签来计算。

### 4.2 少而有用

固定同一来源窗口，候选数N，判合格V，判无效I，未审／证据不足U，N=V+I+U。ICR=I/N；Unresolved Rate=U/N；判定覆盖=(V+I)/N。比例同时保留数量；已审但无法判定也属于U，另记录人工实际审阅覆盖。

全部候选均定性之前，不能把ICR当最终真实无效率；可报告[I/N,(I+U)/N]的未知界限。这是缺失信息界限，**不是统计置信区间**。只抽样审阅时不能把样本无效数直接写成全量无效数；自然抽样估计及其权重／不确定性另报，主模板默认固定小来源池的候选全审。

独立核验方法集合G_m先从原文建立，含适用条件、动作／检查及必要范围。CMR=被最终产物正确保留的方法数/|G_m|。语义等价去重后计数；条件扩大／缩小到不符合参考不算保留；不同skill重复写同一个方法不重复加分。重要低频方法只作事先定义的分层。

### 4.3 新任务效用与更新

若任务i独立重复R_i次，验收z_ir∈{0,1}，SR=(1/N)Σ_i[(1/R_i)Σ_r z_ir]；表内乘100成为百分数。ΔSR=100×(SR_method−SR_reference)，单位为百分点pp，不能写成相对百分比。公共检查器有不同原生连续分数时另列Native Score，不强改为二值或跨域求平均。

资格在执行前固定。服务未完成不计成功并报告原因；评分未知时主表报告“已确认成功/全部合格”的保守下界及未知数，而不暗填失败真值，另给可评分覆盖。该情况下ΔSR仅是保守观测差，不能当完整真实差。研究基础设施错误是否重跑需预先规则，不能只修复不利于本方法的样本。

顺序评测中先评分再学习。每个任务族f、重复序列r、时点t产生冻结／更新两个结果：d_frt=z_update−z_frozen。主ΔSR_seq对每序列的d均值再按任务族等权平均，乘100；附录另给总成功次数差。不同族长度或重复数不同，不能一会按族、一会按题而不说明。预先固定是否含热身题；本模板默认两边都含第一题，初始库相同。

RR=旧成功且新失败的配对执行数/旧成功的配对执行数。每次审计固定旧／新版本、保持任务和重复配置；按检查点单列。若使用共同初始v0审计长期保持，明确写v0，不和相邻版本RR混算。保持题评分不给更新器；任务或种子配对不消除随机性，需要报告不确定性。

### 4.4 资源与统计

沉淀账固定来源；全周期账再固定后续任务数量／观察期。包括系统自身筛选、生成、验证、执行、更新和失败；外加论文评分人力／模型成本单列研究成本。输入、输出、缓存读／写、未知用量数量分别记录，按服务商计费语义避免重计缓存。现金价格不明记UNKNOWN，不将配置里的0当真实免费。

表内主效果报告估计值及95%置信区间。企业材料优先按用户／完整窗口处理相关性，公开任务按任务族或任务进行配对重采样；顺序演化按完整序列而非单步独立抽样。实际重采样单位和次数需执行前填进模板。簇很少时报告原始结果与限制，不用大量重复运行伪造独立样本量。

能力保留属于非劣问题：若要写“有效能力未降低”，先确定可容忍损失δ，再看配对差置信区间下界是否高于−δ；“p>0.05”不等于保留成立。多重比较和显著性标记在正式分析计划中固定，本模板不预置胜者、星号或效果方向。

## 5. M01—M40论文名称与表位字典

下表是本文建议的英文书写，不声称所有名称都是其他论文原名。标准形式由第2节支撑；具体公式和例子沿用057及本节修订。主表T1—T6；附录A1—A8；条件启用表O1—O3。

| 编号 | 推荐英文名称 | 中文／定义身份 | 结果位置 |
|---|---|---|---|
| M01 | Processing Coverage; Unresolved Annotation Rate | 处理覆盖／待定，运行统计 | A1 |
| M02 | Task Assignment Pairwise F1 | 任务归属成对F1，通用形式适配 | T2 |
| M03 | Antecedent Link Precision/Recall/F1 | 承接连接，通用形式适配 | A3 |
| M04 | Adjusted Rand Index; Variation of Information | ARI／VI，通用；本项目VI用原始bits、越低越好，非文献归一化变体 | A3 |
| M05 | Task Resumption Precision/Recall; Misattachment Count | 返回接回及错接，本文定义 | A3 |
| M06 | Exact-match Trace F1 | 整轨迹完全匹配，适配并保留单轮 | A3 |
| M07 | Typed Relation Precision/Recall/F1 | 类型及端点共同匹配，通用形式适配 | T2、A3 |
| M08 | Non-task Detection F1 | 无任务噪声识别，通用形式适配 | A3 |
| M09 | Unsupported Evidence Upgrade Rate | 无依据提升证据等级，本文定义 | A3 |
| M10 | Condition-aware Method Recall (CMR) | 条件化方法召回，本文定义 | T3、A4 |
| M11 | Critical-method Recall | 事先确认的重要方法召回，本文定义分层 | A4 |
| M12 | Candidate Validity Rate | 已判定候选的合格率，本文审核口径 | T3、A4 |
| M13 | Invalid Candidate Count/Rate | 本文改为固定来源的无效数量／比例；不再强用每100任务 | T3 |
| M14 | Non-incremental Redundancy Rate | 无增量重复，本文定义 | A4 |
| M15 | Conditional Conflict Rate; Unsupported Claim Rate | 同条件冲突／无依据主张，两个分母 | A4 |
| M16 | Utterance–Workflow Matching; Complete-path Coverage | 话语映射／路径覆盖的描述性名称；UMR/CPC原实现尚未接入，不宣称公式等同 | O3 |
| M17 | Package Validation Rate; Skill Load Rate | 封装与执行读取分开，运行统计 | A1 |
| M18 | Skill Library Size; Library Length | 候选／已采纳／版本与长度分开 | T3、T5、A2 |
| M19 | Absolute Success Gain (ΔSR) | 同题配对成功差，通用差值 | T4 |
| M20 | Success–Cost Trade-off | 效果—成本展示，非额外独立分数 | A8 |
| M21 | Task Success Rate (SR) | 独立验收成功率；原DSR为业务验收特例 | T4 |
| M22 | First-delivery Success Rate; Final Success Rate | 同一交互任务首次／最终，本文协议 | A5 |
| M23 | pass@3 | 三次独立机会至少一次通过，通用；非平均SR | O3 |
| M24 | Requirement Satisfaction Rate | 当前适用要求符合率，本文检查表 | A5 |
| M25 | Personalization Gain | 个人化相对通用／摘要的收益，本文对照 | A5 |
| M26 | Cross-user Transfer Gain | 授权未参与生成成员的收益，本文对照 | O1 |
| M27 | Follow-up Rate | 发生至少一次后续询问的任务比例，描述统计 | O3 |
| M28 | Correction Rate; Repeated-instruction Count | 既有要求纠错与重申，本文语义分类 | A5 |
| M29 | Skill Utilization Funnel | 选择、提供、读取、遵循、完成分别计数 | A6 |
| M30 | Conditional Behavior Coverage | 本文技能条件场景覆盖；非未经适配的官方Skill Coverage分数 | O3 |
| M31 | Incompletion Rate; Unscorable Rate | 未完成／无法评分分开 | A1 |
| M32 | Prequential Success Gain (ΔSR_seq) | 本文冻结对照顺序差；历史CEG别名 | T5 |
| M33 | Regression Rate (RR) | 旧成功新失败，本文配对定义 | T5、A7 |
| M34 | Repair Rate | 旧失败新成功，本文配对定义 | A7 |
| M35 | Beneficial Update Rate; Indeterminate Update Rate | 新任务与保持标准判断更新，本文定义 | A7 |
| M36 | Version Attribution Accuracy; Stale-patch Rejection Rate | 版本关联／过期拦截，运行场景统计 | A7 |
| M37 | Lifecycle LLM Usage and Cost | 请求、各类tokens、金额，运行统计 | T3–T5、A2 |
| M38 | Cost per Successful Task | 全部费用/成功数，通用成本形式 | T4、A2 |
| M39 | Active Human Time; Net Human-time Savings | 主动人时／净节省，工业运行度量 | O2 |
| M40 | End-to-end Latency; Queueing Time; Retry Count | 耗时、等待、重试，通用运行量 | A2 |

## 6. 论文表格组织及使用方式

正文先准备六张主表：T1数据、T2恢复、T3沉淀、T4新任务、T5演化、T6机制消融。正文版面不足时把T2诊断列或T6次要消融移附录；不将六张当投稿数量要求。A1—A8保存完整诊断和资源；O1—O3只有对应实验真实开展后才使用。

企业、公开、构造材料使用独立panel；后两者不能填企业列。每张表附数据清单、固定条件、分母、评分器与缺失处理；行名是拟采用对照，不表示已经实现或跑过。未完成近邻适配不能用其论文名称冒充官方复现。

填写顺序：先填T1及配置→锁定评分协议→运行后填原始计数→计算比例／差值和区间→填写资源账→最后决定表格保留及论文结论。模板所有成绩留空，无虚构数值或预设最好成绩。

本轮新增的是文献对标与可直接填写的论文表格；**无新增本项目实验实证**。
