# 148 后续强基线核查：关系恢复与技能学习分层

日期：2026-10-04。性质：主源文献和公开代码核查、实验设计建议；未启动模型、训练、服务或新实验，未修改 README／STATE。公开仓库的“可取得代码”不等于已在本机复现；正式比较前仍须固定完整 commit、提示、依赖和输入。

## 已确认的研究定位

AutoSkill 是强基线之一，不是本项目已经选定的采用方案。主问题持续是理解会话中的任务、要求、尝试、工具结果、反馈及修订关系，再检验这种理解能否改善经验学习。历史 [073 记忆](../memory/073_2026-09-30_rq1_trace_recovery_experiment.md) 已明确以 Trace2Skill 为强基线、比较有无恢复；[046 契约](../contracts/046_twelve_stage_contract_user_revision.md) 则区分任务识别和轨迹恢复。此次调研补充比较对象，没有改变研究问题或确认某方案有效。

需要分开两类比较：关系恢复算法回答“哪些片段属于同一任务，反馈作用于哪次尝试”；技能学习算法回答“已有执行经验怎样归纳、验证和更新技能”。只与直接技能生成器比较，无法证明关系算法本身更强；只提高关系标签分数，也不能证明技能复用受益。

## 七项最相关方法及可用性

下表每项只概述与当前问题有关的机制；论文结果不能直接迁移为本项目效果。

| 方法与核对版本 | 已有核心机制 | 关系恢复边界与建议用途 | 作者代码状态 |
| --- | --- | --- | --- |
| **Trace2Skill**，2603.25158 **v5，2026-06-04** | 冻结模型生成逐任务成功／失败轨迹；成功分析和可检查产物、验证修正的失败分析分别提 patch；层次合并为技能目录，不更新权重。[§2、§4](https://arxiv.org/html/2603.25158v5) | 很适合作为真实 rollout→技能的主要强基线。原方法按已知任务生成带结果轨迹；这不是交错输入恢复测试。不能把“失败归因／验证修正”称为我们的首次贡献。 | 论文直链 [Qwen-Applications/Trace2Skill](https://github.com/Qwen-Applications/Trace2Skill)；公开有 error／success analysis、parallel evolution 和发布技能。 |
| **EvoSkill**，2603.02766 **v1，2026-03-03** | 失败轨迹、预测和训练答案供 Proposer 诊断；Builder 创建／编辑技能；验证集和有界 frontier 选程序，记录提案及分数历史；基础模型冻结。[§2](https://arxiv.org/html/2603.02766v1#S2) | 适合检验恢复效果是否依赖某一种技能归纳器。其训练／验证／测试任务已知；程序演化历史不等同于自然会话中的反馈→尝试恢复。 | 论文直链 [sentient-agi/EvoSkill](https://github.com/sentient-agi/EvoSkill)；有 src、CLI／API、skill_only 模式和评测入口。 |
| **WikiSkill**，2608.27454 **v1，2026-08-27** | 原始经历、持续 wiki、技能三层；成功／失败经验更新 pattern 与演化日志，再提原子技能修改；验证 gate／rollback。[§2–3](https://arxiv.org/html/2608.27454v1#S2) | 很直接的“先理解和积累经历，再生成技能”近邻。原文定义为已知任务及评分轨迹；不能把增加中间知识层或历史证据称新。交错任务归属与迟到要求修订是否另做，当前未核实。 | 本轮未从论文核实作者仓库。检索到的同名实现不能代替官方；例如 [Stahl-G/wikiskill](https://github.com/Stahl-G/wikiskill) 明示 independent implementation。宜先列文献近邻，不能立即承诺官方可运行基线。 |
| **SkillEvoReg**，2609.30861 **v1，2026-09-25** | 保留原生 updater；更新阶段 skill dropout、局部复杂度正则、候选相关 CCV；比较旧／新技能在原例和针对性扰动上的行为，至多一次限定范围修复。[§4](https://arxiv.org/html/2609.30861v1#S4) | 属于更新可靠性层，不能把反例验证、复杂度约束称新。“training-time”这里是外部技能演化阶段，不自动意味着神经网络 SFT／RL。§3 的给定轨迹更新接口不能证明它已评测混合会话恢复。 | 本轮未核实作者发布代码；有论文伪代码和提示。宜作为必须对照的机制近邻，取得可复现实现后再决定执行。 |
| **SAPO**，Co-Evolving Skill Generation and Policy Optimization，2606.08755 **v1，2026-06-07** | 同任务、同检索上下文，用基础／新增单技能两组 rollout 的奖励差估计边际效用；训练 policy 的 skill generator，并用 GRPO 更新 actor、重排和清理技能。[§4、附录B–C](https://arxiv.org/html/2606.08755v1#S4) | 是技能效用归因及参数训练近邻；分组输入明确标注 Task 1／Task K，不能当作自然交错解缠证据。不要声称“RL 学技能／效用反向监督”首次。完整训练不宜与冻结模型方法混作等资源主对照。 | 论文官方链接 [zzwjames/skill_augmented_agent](https://github.com/zzwjames/skill_augmented_agent)；本轮取得页面仅 README，且 [raw README](https://raw.githubusercontent.com/zzwjames/skill_augmented_agent/main/README.md) 仅标题 SAPO。尚无已核实可运行实现。 |
| **Unsupervised Conversation Disentanglement through Co-Training**，2109.03199 **v1，2021-09-07／EMNLP 2021** | 伪数据初始化消息对与 session 分类器；用局部关系奖励训练 session 分配策略，互相增广训练数据，含 RL。[主文](https://aclanthology.org/2021.emnlp-main.181/) | 可训练的关系层基线，确实分解交错消息；其 session 奖励不是业务成功奖励。原任务是对话分组，不直接给出工具成功、要求替代等业务边类型；需明确适配和域迁移。 | 论文 PDF 指向 [LayneIns/Unsupervised_dialo_disentanglement](https://github.com/LayneIns/Unsupervised_dialo_disentanglement)，已核实 pretrain／co-training 和训练入口；未本机运行。 |
| **Revisiting Conversation Discourse for Dialogue Disentanglement**，2306.03975 **v2，2023-06-10** | 说话者、mention、距离、部分 reply 四种异质图；监督分层 ranking，easy-first 推断 reply-to 后得到线程。[§3–5](https://arxiv.org/html/2306.03975v2) | 直接防止“关系图／全局恢复”被夸为首创。可作为监督训练算法参考，但 reply-to 线程划分不自动等于任务—尝试—修订关系。 | 原文写接受后发布代码，本轮未核实对应作者仓库；不据此声称已具备可运行版本，也不声称现在一定没有代码。 |

**范围判断是本轮推论**：前五项的方法定义使用任务／轨迹及其评测结果，后两项显式学习交错消息关系。本轮没有取得前五项对 A→B→A 的成员归属、迟到反馈对象和要求替代边进行独立评分的证据；这只能说明本轮未核实该评测，不能证明它们无法理解这些关系，更不能据此断言不存在其他相关工作。

名称应严格区分：上述 EvoSkill 不等于 **SkillEvo**（2608.13120 v1，2026-08-13）。后者已用多轮模拟用户追问生成反馈，并以独立治理层处理事实退化和结构膨胀；“多轮反馈推动修订”也已是已有研究。[SkillEvo §3](https://arxiv.org/html/2608.13120v1#S3)。本轮未核实其作者代码，未列为立即可运行首选。

## 已有反馈学习对照与评测载体

**ACE** 当前为 2510.04618 v3（2026-03-29），Generator／Reflector／Curator 用执行反馈增量维护 playbook；论文指向已公开的 [ace-agent/ace](https://github.com/ace-agent/ace)。它适合作为“额外反思与经验维护是否已经足够”的扩展基线，不能当作没有失败反馈的弱总结器。[ACE §3](https://arxiv.org/html/2510.04618v3#S3)。**Reflexion** v4（2023-10-10）早已用任务反馈生成反思并保存为 episodic memory；其 verbal RL 不更新模型权重。若只需轻量反馈对照，可考虑该机制，本文未把未取得的仓库内容算作代码验收。[Reflexion v4](https://arxiv.org/abs/2303.11366v4)。

**SkillEvolBench** v1（2026-05-22）是评测载体而非新的关系恢复算法。它已有 acquisition／replay／frozen deployment、NO-SKILL 和 RAW-TRAJECTORY 控制，180 任务、六环境，并检查 context shift、adversarial、composition；作者代码已公开。适合避免把直接经验复用当作抽象技能收益，不能替代交错任务关系真值。[论文](https://arxiv.org/abs/2605.24117v1)、[官方项目](https://skillevolbench.github.io/)、[作者仓库](https://github.com/AIoT-MLSys-Lab/SkillEvolBench)。

## 建议的分层强对照

以下是建议，尚未执行，也未决定采用其中任何实现。

1. **关系层**：同一批可回查混合会话，比较普通 LLM 全文结构化抽取、可合理分片的 LLM 归属／关系抽取、可训练解缠模型、我们的方法，以及只供评分或上界参考的人工正确关系。不能仅以弱关键词分段作为唯一基线。训练模型需要独立训练／开发／测试分组，不能让同来源片段跨组；普通 LLM 与本方法使用同样可见事实。
2. **技能层**：先固定同一个学习器，只改变输入组织与关系证据，才能定位恢复的作用。Trace2Skill 和 AutoSkill 各自可做这种控制实验；再用 EvoSkill 的另一种学习机制检验结论是否稳健。这里使用现成学习器作为评测工具，不代表产品架构要采用它。
3. **完整系统层**：保留 NO-SKILL、直接 RAW-TRAJECTORY 复用和强技能学习器，最终测未参与恢复、生成或选版本的新任务。成功分析、失败诊断、反馈反思、验证 gate 都须留在基线中；不得为制造差异删掉原生能力。

训练可以是后续路线：在同一份关系标注上，训练消息／片段归属及有类型的关联预测器，与同模型结构化 prompt 或 SFT 输出关系表比较。它是待实施基线设计，不是本轮确认的原创算法。新增贡献若成立，应落在特殊关系如何被识别、歧义怎样保留、恢复为何改变学习结果；不能只落在“用了图／SFT／RL／反例验证”。

## 成本与证据公平

- **输入权限**：Trace2Skill／EvoSkill 的失败诊断可以看演化侧答案或检查产物；若企业输入只能看到公开回执与用户反馈，应分别报告“观察证据”与“演化侧验证证据”两种条件。各组获得相同权限，不给恢复器隐藏归属、测试答案或私有评分；不能让有答案基线与无答案方法的差异冒充算法差异。
- **计算预算**：统计所有归属／恢复、诊断、技能生成、合并、维护、验证、重试、检索与消费调用。报告 token、费用、墙钟时间和实际 rollout 数；并行降低时延不等于减少总计算。我们多次分片提技能时，基线也要有相当的候选机会及总预算。
- **训练预算**：SFT／RL 需额外记录 GPU 时间、样本与标注／teacher 成本，分别给训练后推理成本和在明确任务量下摊销的总成本。SAPO 的“无额外 rollout”是相对其标准训练 rollout 预算的分配，不是训练免费；不能直接套用于 API 冻结模型组。
- **干预范围**：首先只改组织关系，例如 A1→B1→A2→B2，保留每个任务内顺序和完整调用—返回证据块；再独立检验迟到反馈和要求修订。关系整理、来源质量改善、公开 API 能力验收和技能更新 gate 要有分开的对照，不能全部包装成阶段2／3贡献。
- **判定标准**：成员／反馈／修订关系指标和来源可追溯性先验收，再测技能支持性、未支持规则及新任务效用。若普通 LLM 整理已足够、恢复未改善或成本不合算，保留该结果并收敛研究范围。

## 下一步最小决策

立即可核实的技能学习代码以 Trace2Skill／EvoSkill 最明确，AutoSkill 继续保留强基线身份；关系层先完成标注契约与强 LLM 对照设计，同时审计已有 co-training 代码的适配成本。WikiSkill、SkillEvoReg、SAPO 是必须纳入相关工作和机制排重的近邻，官方可复现性未核实之前不承诺执行。此顺序不授权模型实验或代码开发。
