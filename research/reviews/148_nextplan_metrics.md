# 148 AutoSkill 基线完整指标核对

日期：2026-10-04。仅分析保存产物、复算描述统计，无模型调用、实验执行、服务操作或技能库修改。主结果是**v4 B0无技能与B1冻结v2库＋显式读取提示**；旧GLM批次、70条采集、整个148账本分别列出，避免混合分母。机器可读全值见 [148_nextplan_metrics.json](148_nextplan_metrics.json)；前次统计资格审计见 [statistics_audit.md](267_autoskill_analysis/statistics_audit.md)。

## 正式 v4：质量与重复稳定性

来源：`research/experiments/148_tau2_retail_autoskill/runs/test_v4/no_skill.json`、`autoskill_library.json`及`reports/v4_paired_summary.json`。各40题、每题4trial，task/trial无重复；160配对seed一致。消费者与用户模拟器保存配置为DeepSeek Flash，NL judge为GLM-4-Flash。这里只有一个base seed和一套同域test划分。

| 指标 | B0 | B1 | 变化或定义 |
|---|---:|---:|---|
| 保存场次/有效奖励 | 160/160 | 160/160 | 均40题×4trial |
| reward=1 | 126 | 134 | +8场 |
| 平均reward / pass^1 | 78.75% | 83.75% | +5.00pp |
| pass^2 | 67.50% | 74.1667% | +6.6667pp |
| pass^3 | 60.625% | 67.50% | +6.875pp |
| pass^4 | 55.00% | 62.50% | 四次全成功22→25题 |
| 至少一次成功pass@4 | 97.50% | 97.50% | 均39/40题 |
| 四次全失败 | 1/40 | 1/40 | 不能与全成功混淆 |
| 每题成功次数0/1/2/3/4的题数 | 1/5/3/9/22 | 1/2/4/8/25 | 共40题 |
| DB reward=1的场次 | 126/160 | 135/160 | B1有1场DB过但NL不过 |
| NL reward=1的场次 | 156/156 | 154/156 | 4场只有DB；不是逐断言数量 |

pass^k按每题的`C(c,k)/C(4,k)`再平均40题，其中c是该题四trial成功数；它是k次重复都成功的估计，**不是把全体成功率直接做k次方，也不是至少一次通过的pass@k**。只复算k≤4，不外推更多重复。

| 配对与任务cluster统计 | 数值 | 资格 |
|---|---:|---|
| 160配对B1胜/负/平 | 20/12/128 | 两组都成功114、都失败14 |
| 平均差B1−B0 | +0.05 | 正向点估计 |
| nominal exact McNemar双侧p | 0.21532715 | 场级独立性需限定，未显著 |
| 40题改善/退步/持平 | 15/7/18 | 按题平均reward |
| task exact sign双侧p | 0.13380051 | 未显著 |
| 原任务cluster bootstrap 95% CI | [-2.5pp,+12.5pp] | 10k、seed42、原任务顺序，已复现 |

cluster bootstrap以40题为抽样单位，保留同题四trial，不能把160场当160独立任务。原10k百分位区间有Monte Carlo离散波动；相同经验分布的确定性卷积区间为[-3.125pp,+12.5pp]，只作数值附注，不替换原主报告或新增检验。总体仍只能称探索性正向结果。

## 正式 v4：耗时、沟通和工具投入

耗时分位数对160个已保存`simulation.duration`做线性插值，位置为q×(n−1)。单场耗时相加不是并发批次的实际墙钟时间；两个阶段并发/运行时间差异也使耗时只能作描述性比较。

| 指标 | B0 | B1 |
|---|---:|---:|
| 单场耗时mean/P50/P95，秒 | 468.43 / 446.37 / 660.80 | 600.92 / 597.00 / 697.01 |
| 单场耗时min/max，秒 | 337.42 / 792.65 | 366.39 / 733.28 |
| 单场耗时总和，秒 | 74,948.59 | 96,147.28 |
| 全部user消息 | 872 | 835 |
| 非终止user消息总数 | 712 | 675 |
| 非终止user消息mean/P50/P95 | 4.45 / 4 / 7 | 4.21875 / 4 / 6 |
| 初始请求后的非终止user消息mean | 3.45 | 3.21875 |
| 业务工具调用总数 | 1,173 | 1,250 |
| 业务工具调用mean/P50/P95 | 7.33125 / 7 / 11.05 | 7.8125 / 7 / 12.05 |
| 原生tool error=True总数 | 23 | 38 |
| 显式工具错误mean/P50/P95 | 0.14375 / 0 / 1 | 0.2375 / 0 / 2 |
| 显式错误占tool返回比例 | 1.9608% | 3.0400% |
| 有显式工具错误的场次/占比 | 21/160=13.125% | 28/160=17.50% |
| user_stop终态 | 160 | 160 |
| 空reward终态 | 0 | 0 |

非终止消息排除STOP、TRANSFER、OUT-OF-SCOPE控制标记；“含初始”和“初始后”必须分别看，不能换算企业人工时。业务工具是τ²记录的官方环境调用，不含本地技能read或LLM请求。error=True只表示显式环境错误，不统计所有语义错误。B1平均耗时增加132.49秒（28.28%），用户消息少0.23125/场、工具多0.48125/场；当前不能归纳成整体效率提高。

## 正式 v4：usage与费用可用性

| 指标 | B0 | B1 | 能否当完整成本 |
|---|---:|---:|---|
| user usage记录数 | 872 | 835 | 覆盖保存user消息 |
| user prompt tokens | 806,155 | 882,677 | 仅模拟用户 |
| user completion tokens | 241,331 | 268,425 | 按保存usage原值 |
| user保存tokens合计 | 1,047,486 | 1,151,102 | 不含消费者和judge |
| assistant非空usage记录 | 0 | 0 | 消费者tokens未知 |
| agent_cost非空场次 | 0/160 | 0/160 | 实际消费者费用未知 |
| user_cost非空场次 | 0/160 | 0/160 | 实际模拟用户费用未知 |
| judge tokens/费用 | 未知 | 未知 | 没有正式分组归属 |
| 全组总tokens/人民币等费用 | 未知 | 未知 | 不能补0或以累计账本替代 |

保存message.cost虽有0.0，但它与代理harness缺失的真实账单不是同一量；不能解释成免费。当前无法给出每多成功一次的真实费用、总成本效率或学习成本摊销。

## 学习源与技能库

来源：`runs/collect/evolution.json`、`autoskill_input/trajectories/manifest.json`、`scripts/autoskill_build_trajectory.py`、`frozen_skills_v2_manifest.json`及trajectory向量meta。

| 指标 | 实际值 | 解释 |
|---|---:|---|
| 官方train/dev/演化/test | 74 / 4 / 70 / 40题 | 演化/test ID无交集；不等于订单族/语义隔离 |
| 采集reward=1 / reward=0 | 5 / 65 | 均分7.1429% |
| 正常user_stop评分通过/不过 | 5 / 50 | 共55 |
| timeout / too_many_errors | 10 / 5 | 15条均reward0且breakdown=null |
| 采集assistant/user/tool消息 | 1,452 / 1,117 / 327 | assistant公开非空1,125 |
| tool显式错误/涉及任务 | 149 / 40题 | 错误源不限单例 |
| 工具content>4000字符 | 0条 | 代码上限存在，本批未实际截断 |
| trajectory学习输入 | 70条 | 工具调用与成功/错误返回保留 |
| 实际build记录 | processed70 / failed0 | 入口处理状态，不是技能语义验收 |
| 最终主技能 / reference文件 | 3 / 27 | 共30文件，1空reference |
| 主SKILL.md正文总UTF-8字节 | 84,013 | 规范LF，不是tokens |
| 全库总UTF-8字节 | 106,986 | 约104.48KiB，含references |
| 持久向量 | 3×1024 float32 | 12,288字节，ecnu-embedding-small |

采集者/模拟用户是GLM-4-Flash；v2生成脚本配置DeepSeek Flash，走`user`路由、官方agentic trajectory入口，`include_tool_events=True`、`success_only=False`并有手写零售HINT；正式消费也是DS。不能把准备期conversation/GLM文档当最终设置，也不能把65条零分全部归为能力失败：15条异常没有完成评分分项，根因须另查。

| 主技能 | SKILL.md规范LF字节 | references | 含references总字节 |
|---|---:|---:|---:|
| retail_order_exchange_and_change_workflow | 29,158 | 7 | 36,488 |
| retail_order_support_orchestration | 46,536 | 19 | 61,362 |
| retail_product_order_orchestration | 8,319 | 1 | 9,136 |

当前30文件规范LF后全部匹配旧manifest；29个原严格字节hash因CRLF迁移不符，仅原空文件严格相同。这验证当前文本内容对应旧库，不能宣称已独立重验原运行时逐字节freeze。技能质量precision、覆盖率、每个技能独立效果、v2-only学习调用/tokens/时间/费用目前没有可用完整量化。

## 技能读取：保留159/160的证据限定

保存`v4_paired_summary.json`报告159/160=99.375%会话有原生技能read路径证据，各主技能尝试会话数159/159/158；另1场读库外browser-automation，未读例为task32 trial0（reward1）。这是**历史保存审计的读取尝试率**。

扫描谓词从toolCall或result路径片段取skill名，没有要求成功返回、非空完整正文、body hash或读取/上下文预算完整；直接抽样也只查toolCall路径。当前checkout没有原session/sqlite及唯一sim→session表，无法独立重建159映射。完整正文成功加载率、完整消费率、遵循技能率都仍未知，不能将99.375%写成完整读取成功率。

全历史扫描另有543会话、523当时有sqlite、206有引用、190引用且有read证据，混合旧批/smoke/中断attempt，不是正式v4的分母；旧188/172是不同快照。旧GLM exposure-only报告为5技能、读取0/162、B0 11/160、B1 13/160，配对11胜9负140平、p≈0.824，应独立保留，不合并成v4收益。

## 全148账本：能计路由，不能完整计阶段

独立重算`ledger/requests.jsonl`共36,359条，UTC起始2026-10-02 09:52:29.163546至2026-10-03 18:17:34.782358（北京时间末尾10-04 02:17:34.782358）。seq值跨运行段复用；按(seq,started_at,role)没有重复记录。下表是整个实验历史的**路由角色**，包括准备、学习、旧批、smoke、正式评测、重试/恢复。

| 路由角色 | 累计条数 | logged completed | transport error | HTTP error |
|---|---:|---:|---:|---:|
| consumer | 20,253 | 20,248 | 4 | 1 |
| user | 14,469 | 14,450 | 19 | 0 |
| judge | 1,037 | 1,037 | 0 | 0 |
| autoskill | 205 | 200 | 0 | 5 |
| embed | 370 | 362 | 0 | 8 |
| plus | 25 | 25 | 0 | 0 |
| 合计 | **36,359** | **36,322** | **23** | **14** |

model_hint还显示consumer GLM16,125/DS4,128；user GLM12,364/DS2,105；judge GLM1,037；autoskill GLM205；embed ECNU370；plus ECNU25。它们是请求标签，不是物理模型checkpoint证明。尤须注意**v2 AutoSkill生成走user路由**，故“autoskill205”不能代表全部或仅v2学习成本，“user14,469”也不等于只模拟用户。

账本没有phase/stage/group/task/trial/simulation/session标识，也没有usage/cost字段；现有metadata不能将36,359完整唯一分配到采集/生成/dev/各版本test/重试，更不能拆成正式B0/B1。role只支持上面的路由分解。正式v4调用总数及每组请求/总tokens/费用，应标未知；logged completed也不是任务正确、技能完整交付的证明。

这些指标能说明当前AutoSkill处理包在同域40题上的初步表现及消费开销；尚不能证明技能收益成立、独立技能贡献、使用后演化收益或拟议任务关系恢复算法有效。
