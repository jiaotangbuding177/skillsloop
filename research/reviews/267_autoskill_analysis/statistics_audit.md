# 148 v4 独立统计审计

日期：2026-10-04。范围：本地保存结果的只读重算与证据资格审查；未启动、恢复、修改任何实验、服务或模型调用。完整数字、方法与当前来源 SHA256 见 [statistics_audit.json](statistics_audit.json)。执行工具的沙箱初始化失败后，仅使用自动审核通过的宿主 Python 做只读计算；未触及凭据。

## 已独立复现的正式 v4 数字

来源：`research/experiments/148_tau2_retail_autoskill/runs/test_v4/{no_skill,autoskill_library}.json`。两组各40题×4 trial，task/trial无重复；全部160配对的单场seed相同。两组保存结果均为160 `user_stop`、无空奖励。保存test task集合与split_manifest一致，演化ID与测试ID无交集。

| 指标 | B0无技能 | B1技能库＋显式读取提示 |
|---|---:|---:|
| 成功/已保存场次 | 126/160 | 134/160 |
| 平均reward / pass^1 | 0.7875 | 0.8375 |
| pass^4：同题四次全成功 | 22/40=0.5500 | 25/40=0.6250 |
| pass@4：同题至少一次成功 | 39/40=0.9750 | 39/40=0.9750 |
| 非终止用户消息/场，含初始 | 4.4500 | 4.21875 |
| 非终止用户消息/场，初始之后 | 3.4500 | 3.21875 |
| 业务工具调用/场 | 7.33125 | 7.8125 |
| 原生工具error=True次数/场 | 23/160=0.14375 | 38/160=0.2375 |
| 有上述工具错误的场次 | 21/160 | 28/160 |
| 平均场耗时/秒 | 468.4287 | 600.9205 |
| 保存的user prompt tokens | 806,155 | 882,677 |
| 保存的user completion tokens | 241,331 | 268,425 |

配对列联计数：两组都成功114、两组都失败14、B1成功而B0失败20、B0成功而B1失败12。差值+0.05；二侧 exact McNemar p=0.2153271497（与二元配对确切符号检验相同）。按任务均值为15改善、7退步、18持平，确切符号p=0.1338005066。以上均未达到0.05显著性。

主报告原脚本的任务cluster bootstrap，保持B0首次出现任务的顺序、10,000重采样、random seed=42，95%区间 **[-0.025,+0.125]** 已复现。它按40题重采样，保留每题四trial整体；不是160场独立bootstrap。160配对的McNemar是名义场级检验，题内相关性使其独立性假设需限定，不能忽略40个任务的聚类结构。

附注：10,000次抽样存在离散Monte Carlo波动。按task排序后同seed10k区间[-0.03125,+0.125]；用经验task delta分布进行40次抽样的离散卷积，确定性percentile区间也是[-0.03125,+0.125]。这只是相同bootstrap目标的数值复核，不作为新增试验或额外显著性检验，也不替换主表原可复现区间。

成本口径仅涉及这320个保存终态；全账本累计不能当它们的成本。用户非终止消息减少0.23125/场，但业务工具增加0.48125/场、显式错误增加、耗时增加132.4918秒/场（28.28%）；不能据此宣称总体效率改善。assistant消息usage全null；user usage有记录，缺消费者/judge完整归属，不代表两组总tokens。保存message.cost=0.0而agent_cost/user_cost均null，不能证明免费，实际费用未知。

## 演化70条的来源质量

来源：`runs/collect/evolution.json`。Collector与模拟用户为GLM-4-Flash，正式v4消费者与模拟用户为DeepSeek Flash，属于跨资源学习与消费，必须明确区别。

- 奖励65条0、5条1，均分0.0714286。
- 55条user_stop：50条0、5条1；10条timeout和5条too_many_errors均保存reward0。
- 15条异常终态的reward_breakdown为null，不能把它们描述为完成官方DB/NL检查后的能力失败，更不能只凭终态标签定性模型或基础设施根因。
- 55条正常user_stop的breakdown为36×DB0/NL1、12×DB0/NL0、1×DB0-only、1×DB1/NL0、5×DB1/NL1。
- 原始消息assistant1452（1125公开内容非空）、user1117、tool327。149工具返回的原生error=True，覆盖40/70题；源材料的失败和错误不是task_0单例。
- v2实际trajectory输入保留1125 AGENT、1117 USER、327 AGENT_TOOL_CALL、149 TOOL_RESULT_ERROR、178 TOOL_RESULT标签。conversation canonical将tool转为assistant展示，不能据角色名直接认为工具事实被丢弃。
- `scripts/canonicalize_trajectory.py:44`含工具返回[:4000]上限，但这70条所有角色消息content>4000的数量均为0，**本批未发生该上限导致的实际截断**。

## 读取率和冻结资格

保存的`reports/v4_paired_summary.json`报告160匹配/159有read证据，99.375%；本地当前checkout未包含原`runs/autoskill_library`会话目录、prompt或sqlite，不能独立复核这160映射。保存审计也未带prompt epoch或显式sim→session表。原matcher按task内prompt mtime±300秒选最近者，不强制一对一、未保存候选歧义，故它是历史匹配口径，而不是当前已复核的唯一身份链。

`scripts/scan_skill_reads.py:138`—`140`的判定是从read调用或result片段取skill path后`triggered=bool(read_skills)`；未要求tool成功、返回全文非空、body hash或所有正文进入预算。`verify_skill_reads_direct.py:57`也只抽查toolCall和SKILL.md路径。**可支持“保存审计报告159/160场有原生读取尝试”，不能支持“159/160场完整正文成功进入上下文”**。库内read尝试、read成功、全文完整及实际遵循是不同证据层级。该审计不证明库资源都被完整消费。

全历史审计当前543会话、523有sqlite、206含引用、190含引用并read、191有read；239记忆和final报告中的188/172属于较早快照，需标明日期/版本和分母，不混用。

当前技能manifest30文件中，仅空文件严格字节hash一致；另29文件均因CRLF变化而不同，规范化为LF后全部30文件匹配。能核验当前文字内容对应旧manifest；不能称当前checkout逐字节冻结验明，也不能据此认定当时运行热改。一个原本为空的参考文件是`retail_order_support_orchestration/references/retail-order-change-runbook.md`。

## 实验设置和解释限制

1. 实际处理是**冻结技能库＋B1专有行动前读取提示**。`final_report_v4.md:29`的“提示完全一致、唯一差异skills目录”与实际首轮$技能引用矛盾。它检验整个处理包，不能拆出纯正文、仅发现列表或自主检索机制的效果。
2. 当前protocol.md/experiment.yaml/versions.json仍为准备期配置：conversation路径、GLM、原超时/并发及自主读取。实际已换trajectory库v2、DS消费、显式引用和judge容错。存在dev_frozen_p1/p2/p4；当前checkout未见独立完整v4/v6 source freeze。后期报告与结果metadata能说明实际配置，不能替代完整版本证据。
3. `run_test_phase_v4.sh`请求两组各8并发，理论合计16；B1 resume请求12并发。报告“最大并发12”需要实际运行日志证据。不同时间和并发下的耗时只作描述性比较。
4. 保留单base seed、40题、单技能库、API模型别名、共同政策/工具/数据库，以及官方train/test订单族与近似指令重叠的限制。它不证明独立订单族、语义任务族或跨域泛化。
5. benchmark为tau3-era修订的tau2-bench v1.0.1；NL judge替换为GLM并用fence-strip/重试，属于资源与harness适配，不能直接对原论文排行榜数字排名。
6. 旧test可见结果后的读取机制与库/资源变更、已报告磁盘/WSL恢复，使结果应按探索性pilot解释。320保存终态完整，不等于全部尝试无故障、排除选择或恢复历史已完整独立审查。本审计未认定按高分挑样，也未把“无null reward”升级为从未故障。

## 来源订单重叠子集：补充描述

按保存的`workflow_split_audit.md:46`定义的11个“未共享train订单”题：39/40/64/65/74/77/79/90/100/102/108，B0 32/44→B1 39/44，+0.15909；10胜3负31平，名义exact McNemar p=0.0922852。其余29题94/116→95/116，+0.00862；10胜9负97平，p=1。

本切分是补充posthoc描述，未在本轮重新读取gold参数来重算来源订单定义。共有政策/DB与同域能力仍存在，不能称OOD证明；不据此挑选主结果或增加显著性声明。

本轮新增的是对已有产物的独立统计与证据资格核对，无新增模型实验。
