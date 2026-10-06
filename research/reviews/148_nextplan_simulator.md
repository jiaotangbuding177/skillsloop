# 148 用户模拟器核对与下一步关系机制目标

本轮只读核对既有记录、保存配置和固定官方源码；没有运行模型、实验或服务，没有修改实验库。本文件不代替新的实验授权。

## task0 的感谢是否说明用户模型差

**单看末尾感谢，不能这样判断。** task0 的客服先向用户说明初次交换出错，随后连续宣称已经重新核验、再次处理，最终声称交换成功。用户没有看到后台的完整工具调用和回执；在这种信息条件下，相信客服的新解释并表示感谢可以理解。可证实的冲突是：完整科研记录里唯一写调用失败，而客服后续宣称成功。用户对这个宣称的认可不能升级为操作成功。[task0 L32–51](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_0.txt:32)

**感谢可合理，scenario fidelity 可定位偏离。** 保存的用户场景只提供姓名、邮编、订单号和换货要求，没有提供物品编号。用户在 L4、L27 给出了 `KB12345`、`TH67890`、`KB67890`；这些编号没有场景或此前客服核验支撑。原始要求是找不到 clicky/RGB/full-size 键盘时接受无背光键盘，L21 却转成只换温控器。前者属于场景外信息，后者属于要求保持问题。它们支持“这条模拟存在偏离”，不能证明用户模型总体质量差，也不能把它们归结为末尾感谢错误。[保存场景 L9–17](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/inputs/retail_tasks_v1.0.1.json:9)、[用户首次提供编号 L4](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_0.txt:4)、[替代编号 L27](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_0.txt:27)、[要求变化 L21](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_0.txt:21)

## 用户实际被给予什么信息

核对的是实验保存的上游版本 `fc0055dc4e0a316c3f83133267fbd6faaa770992`，没有用当前 main 代替旧协议。实验保存信息记载学习用户为 `openai/glm-4-flash`、temperature 0，v4 测试用户为 `openai/deepseek-flash`、temperature 0。固定官方构建器给客服传入 domain policy；给模拟用户传入其 `task.user_scenario`、用户自己的工具及模型参数，没有把业务 policy 或评价标准直接放进用户构造参数。用户系统提示另含全局模拟指南。[本地学习用户配置](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/runs/collect/evolution.json:8)、[v4 用户配置](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/runs/test_v4/no_skill.json:8)、[官方 build.py L106–162](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/runner/build.py)、[官方 user_simulator.py](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/user/user_simulator.py)

| 信息 | 固定文本协议中的用户可见性 | 对 task0 的解释 |
|---|---|---|
| 用户场景与全局模拟指南 | 直接提供 | 用户应保持任务条件，不编造场景信息。 |
| 客服说给用户的话、此前用户自己的话 | 直接提供 | 用户能听到初次失败和后来的“核验、成功”陈述。 |
| 客服的工具调用与工具回执 | 直接回客服，不交给用户 | 用户不能直接检查是否真的进行了后续交换。 |
| 用户自己调用的工具回执 | 允许；retail 环境没有配置用户工具 | 不能由用户自行查询后台订单来确认客服说法。 |
| 全域客服政策、gold actions、评价标准、最终业务得分 | 未直接注入用户构造上下文 | 用户感谢不相当于政策审计或业务判分。 |

该路由可由官方 `user_simulator_base.py` L39–45、L57–101 与 `orchestrator.py` 的消息路由共同核对；retail 环境只构建客服工具。用户可以从客服话语间接得知政策或错误，但这不等于直接得到后台记录。[官方用户历史过滤](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/user/user_simulator_base.py)、[官方消息路由](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/orchestrator/orchestrator.py)、[官方 retail 环境](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/domains/retail/environment.py)

本地 wrapper 指定标准 `user_simulator`；所见运行改写是 judge 模型、重试和 JSON 格式处理，没有发现把客服工具记录或 policy 注入模拟用户的代码。[run_wrapper.py L31–124](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/scripts/run_wrapper.py:31)、[L184–206](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/scripts/run_wrapper.py:184)

**证据边界：** 本地缺少历史 vendor checkout 的完整运行时副本和逐次用户 API 请求，保存 metadata 的 git_commit 是适配仓库 commit。上述结论是固定官方协议、保存配置及本地 wrapper 的一致性核对，不是逐字还原历史每一请求。不能据此断言历史服务绝无额外行为。

## STOP、认可与业务得分应分开

全局指南让模拟用户在它认为目标已满足时输出 `###STOP###`。代码检测该标记后结束交互；这只是用户停止信号。官方随后独立执行评价，按任务 `reward_basis` 汇总数据库、沟通、动作或 NL 条件，而非直接读取“感谢”作为成功标签。[官方模拟指南](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/data/tau2/user_simulator/simulation_guidelines.md)、[官方交互停止规则](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/user/user_simulator.py)、[官方 run_simulation.py L52–76](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/runner/simulation.py)、[官方 evaluator.py](https://raw.githubusercontent.com/sierra-research/tau2-bench/fc0055dc4e0a316c3f83133267fbd6faaa770992/src/tau2/evaluator/evaluator.py)

task0 为 `user_stop`，原生 reward=0、DB=false；task50 同样 `user_stop` 且 reward=1，但只有承诺撤销、没有执行，gold transfer 的 action_match=false 又不进入该任务主评分。这两例说明“用户停止”“客服承诺”“用户认可”“任务评分”“真实能力”是不同证据。reward=1 也未必验证了会话里的每一个承诺。[已有案例审计](D:/skillsgen-industry_track/research/reviews/autoskill_148_readonly/case_review.md:24)

## 主线应收窄成什么可检验目标

建议检验的问题是：**完整会话已经含有要求、操作与反馈时，显式恢复它们的关系，能否比直接归纳整段会话减少错误方法入库，并提高同一消费者的后续任务成功率？** 这是当前 stage2/3 轨迹关系主线，不把贡献缩成三条禁止撤销、禁止下单、禁止虚报成功的规则。

最小关系表示应保留事件原文位置，至少恢复以下四类关系：

1. **任务与对象。** 这次要求针对哪个订单、哪些 item、哪个候选集合；“该订单其余耳塞”不扩大成全目录。同一话题、同一用户或同一长会话不能自动合并成一个任务实例。
2. **执行尝试。** 每次 tool call 与对应 result 绑定；准备执行、声称执行、实际调用、成功回执分开。task0 中失败属于那次真实交换；后续自称重试没有新调用支持。
3. **反馈归属及含义。** 用户反馈指向哪次回复、哪次尝试或哪版产物；感谢可支持“用户认可可见陈述”，不单独支持“后台操作完成”。真实用户、模拟用户、工具错误、任务评价分别标来源。
4. **要求版本与变化。** 初始约束、补充澄清、条件分支、真实改需求分开保存。后续改变目标不能回写成最初尝试已经完成；场景漂移也不应被悄悄当成 gold 目标改变。

工具可用性作为“从某段经历能抽出什么方法”的证据边界：task50 可以支持身份核验、澄清请求、能力不足时的处理证据，不能从未执行的承诺推得撤销能力；task96 可以支持地址/对象失败事实，不能从“已下单”陈述推得下单能力。冻结条款已有确认、合法 payload、成功后汇报等保护，应准确表述为**条件性流程仍预设了未被验证的操作能力**，不能夸张为盲目直接撤销或下单。[task50、96 来源与版本链](D:/skillsgen-industry_track/research/reviews/autoskill_148_readonly/case_review.md:20)

这与历史 contract 一致：040 区分任务线索和轨迹；046 明确先恢复归属，再连接非连续尝试/反馈/修订，并区分“准备做、声称完成、工具真实结果”；071 的 reply 匹配验收不能充当任务轨迹真值。073 曾提出同证据、同生成器和消费者，仅改变关系组织的比较。因此新独立方法应给出可检查的关系决策与方法抽取接口；AutoSkill 是其中一个对照生成器，不能用改它几条 retail 规则替代方法问题。[040](D:/skillsgen-industry_track/research/memory/040_2026-09-26_twelve_stage_contract_and_task_detection.md)、[046](D:/skillsgen-industry_track/research/memory/046_2026-09-26_revised_contract_stage23.md)、[071](D:/skillsgen-industry_track/research/memory/071_2026-09-29_final_annotation_acceptance.md)、[073 方案](D:/skillsgen-industry_track/research/reports/073_rq1_trace_recovery_controlled_experiment.md)

## 当前 70/40 能承担的最小检验

- **先做来源审查。** 在 70 条学习源中按统一定义标注上述关系；不仅挑 0/50/96，也检查普通成功例和失败后真重试例。判断直接归纳究竟丢了哪类关系、频率多少，以及生成正文有没有真的使用错证据。人工标注不把 reward、隐藏 gold 或旧 task 标签暴露给自动恢复输入。
- **分开现有结构与构造结构。** 这 70 条源已经按任务分段，不能宣称天然存在多任务交错。可在相同完整事件块上构造串行/交错副本，保持每个任务内部顺序、工具调用—回执配对、内容集合与长度，标明是构造压力测试。原始单任务会话上的尝试/反馈/要求版本问题必须同时评估。
- **保持公平输入。** 直接 AutoSkill、预算匹配的普通 LLM 整理、显式关系恢复三者获得相同原始事件和可用工具信息；下游生成器、消费入口及测试协议固定。关系消融保留所有正文，只移除关系连接，不能删掉关键失败回执来制造优势。
- **把中间正确与最终收益连接起来。** 先报告对象/尝试/反馈/修订连接的正确率和错误方法入库率，再看 40 题、每题 4 次的官方业务成功率。不能只因关系图更漂亮便声称 bench 提升；也不能把 160 次当 160 个独立任务。
- **后续使用这 40 题是探索性检验。** 原正式 148 实验当时的冻结协议与资格保留，不追溯撤销；现已读过结果与选择性失败案例，后续不能再称从未接触的最终测试集。若按它调新方法，应保留该事实；泛化和最终显著性仍需预先冻结方案及独立验证数据。

**目前未知：** 四类关系错误在 70 条源中的总体占比；它们在 AutoSkill 生成中造成多少实质错误；修复后能影响 40 题中的多少消费者失败；相比强普通 LLM 整理是否仍有增益；效果能否超出 retail 和构造交错。当前案例不能许诺“显著提升”。若可修复机会不足，应调整机制覆盖或验证数据，而不是持续增加相同 40 题的重复次数。

本轮新增的是协议可见性和 task0 场景偏离的审计观察；没有新增实验结果。
