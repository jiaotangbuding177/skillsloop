# 148 v4 只读案例审计

本报告仅核对既有结果、学习轨迹、来源索引和冻结技能，没有运行模型、实验、服务或改写实验库。消息位置 `mN` 指原始 `simulations[].messages[N]` 的零基索引；seed 是结果文件保存值。精简结构化证据见 [case_evidence.json](D:/skillsgen-industry_track/research/reviews/autoskill_148_readonly/case_evidence.json)。这些是选择性案例，不能估计现象总体占比或证明生成侧因果。

## 两个有行为实差的正收益案例

| task / trial / seed | 已观察的差异 | 技能对应与解释边界 |
|---|---|---|
| 49 / 0 / 670487；B0=0，B1=1 | 用户要求换成“该订单其余耳塞中最便宜”的款式。B0 m20 把候选扩大到目录中所有 IPX4，选 $226.49 / `8555936349`，m22 成功写入；该款不属于原订单的其余耳塞。B1 m20 明确限定原订单，选其余两款中 $232.49 / `1646531091`，m22 成功写入。B0/B1 sim 分别 `56498a22-1180-43e5-bf3e-6257d716c380` / `3c4a706a-0dde-4f2b-91c4-2942de555971`。 | 对象集合边界在 B1 保留。exchange [SKILL L37](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_exchange_and_change_workflow/SKILL.md:37)、L54–55、L64要求保留硬约束后才选最便宜；[variant runbook L3](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_exchange_and_change_workflow/references/variant-matching-runbook.md:3)要求提取全部约束。但冻结正文没有显式“同单其余物品”集合规则；B1 自述借助参考清单，缺完整阅读内容证据，不能归因于某一条款。技能 ancestry 包含 task105→v0.1.2（同一用户的茶壶任务）及 task75→v0.1.9（耳塞任务），未发现与本集合限定完全一致的学习经历。 |
| 97 / 3 / 777572；B0=0，B1=1 | 两组都找到正确绿色 speaker。B0 m14/16/20 凭空要求新地址必须由用户直接提供，拒绝使用已验证用户另一订单中的 NYC 地址；只做 speaker 写入。B1 m14 从另一订单取出地址，请用户确认；m16 地址写入、m18 item 写入均成功。B0/B1 sim `665b60c6-76dd-4692-a850-e761789772d5` / `78792f40-092d-4fef-84e5-d0abef868b20`。 | 产品 [SKILL L46](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_product_order_orchestration/SKILL.md:46) 和 support L44–45 支持核验地址/账户订单；不是提供地址来源禁令。[task96 L2](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_96.txt:2)是相同用户、相同两订单、几乎相同诉求的学习源，并对应 exchange v0.1.13。因此这是明确的行为胜出，但有共享对象/近似任务暴露，不能作为独立跨任务泛化证据。源 task96 实际曾取错订单、伪造地址、两次 write 失败，正例没有照抄其错误执行。 |

## 一个与技能使用有关的真实退步，尚无读取失败实证

task55 / trial1 / seed116739：B0=1，B1=0。B0 sim `2e150b42-96cc-4a7d-ace6-f401881ebdf8` 在 m26/28 取消两订单、m30/32 返回两订单的全部物品，四次 write 成功。B1 sim `a298851f-476e-4f6b-a2c6-09b4a01e9c7f` 虽读取账户和六订单，却在 m2、m22 反复把两大技能“无法在读取预算中打开”当作执行阻塞，最终 m23 用户请求转人工，未出现取消/返回 write 或 transfer tool。

观察成立的是**消费者因技能读取的自述阻塞而没有执行**。当前 checkout 没有其外部 Read 的原 session/sqlite 轨迹；历史 read audit 只证明路径匹配的读取尝试，不能独立证明正文读取失败或证明完整阅读成功。故此例定位技能交付/消费接口风险，不是已证实的生成遗漏或文件大小根因。[support SKILL L58–60](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_support_orchestration/SKILL.md:58)其实有多请求逐次执行、只有阻塞时才转人工的正确指导。

补充消费例：task111 / trial0 / seed670487，B0=1/B1=0。B1 `6b07067f-698c-4b42-9cd5-416fcdc2771d` 完成 laptop 两写，但 m20/22/30 仅建议 pending watch 等到交付再交换，漏掉允许的 pending-item modification；B0 m19 用户接受此替代，m30 正确改成黑表盘且保留皮带。冻结库已有 pending 修改路线，因此还不能把这一条件分支遗漏归于生成；两组后续用户反馈也已不同。

## 源→版本→冻结条款的两个风险链

来源索引统一为 [online_skill_provenance_tau_retail_pool_v2.json](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json)。其 `history.messages` 保存“整条轨迹作为一个 user 消息”的输入，`metadata.trajectory_success` 是处理元数据，不能替代原生 reward。

1. **task50 → support v0.1.19 → cancellation reversal。** [task50 L7](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_50.txt:7)及 L13 是全部两个工具调用：身份查找、账户读取；无订单状态读取、无撤销 write。L15/17 承诺将取消撤销、确保交付，没有真正执行完成。原生 sim `f6067836-ede1-4bbf-b76f-54759b159386`，seed670487，user_stop；[manifest L131](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/manifest.json:131)记 reward1.0，原始 DB=true、NL为空，gold transfer action_match=false。奖励基于 DB/NL，因此这次满分不能证明撤销或转人工完成。

   provenance [L2373](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json:2373)的 v0.1.18 预览没有 reversal；v0.1.19 在 description、role preview 和 triggers 加入 reversal。[history L5214](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json:5214)关联 task50；skill_id `30d538b0-6b0f-43b6-b466-fdd93a8b5e2e`，source_key `842c8221071d2da303d515d558660a881cf77c2b`，message_hash `a51cf7ac3b31f434f7b2a04e00e049dc4438e877`。冻结 [SKILL L49](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_support_orchestration/SKILL.md:49)规定 cancelled→confirmation→reversal write；[reversal checklist L6](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_support_orchestration/references/retail_order_reversal_checklist.md:6)同样要求对应 write 成功。现行 policy scope 不含取消撤销；[固定官方工具边界](retail_tools_verification.md)已由主审计核对，不含撤销操作，历史运行时schema字节仍待补。生成物保留“只在工具成功后报告”的保护，但仍把未证明有执行能力的任务扩成了常规流程。

2. **task96 → exchange v0.1.13 → new-order fallback。** [task96 L15](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_96.txt:15)伪造订单/地址写入失败；L23 对另一订单地址写入亦失败。L25/27/33 承诺下新单；L39 自报已下单并扣 PayPal，但其间只有目录、产品和账户读取，没有下单工具。原生 sim `018b2ee5-1af0-4a67-84f3-ef60f1620f32`，seed670487，user_stop；[manifest L245](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/manifest.json:245)记 reward0、DB=false。

   provenance [L158](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json:158)的 v0.1.12 不含 new-order fallback；v0.1.13 的 description、trigger 加入该分支；[history L1923](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json:1923)关联 task96。skill_id `d0f9cb64-8f61-4a8a-8a2c-a0dddabab10d`，source_key `373e375ec30238975a111731746c021aaa008abf`，message_hash `b3e9749f1ec7bff79e54721145273da78fd54239`。冻结 [SKILL L70](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/frozen_skills_v2/retail_order_exchange_and_change_workflow/SKILL.md:70)要求同意后用 appropriate tool 下单并核验；policy 没有此操作。这里不是把源虚报成功逐字搬进技能：生成物加入了成功核验保护，却没有消除不存在操作的能力扩张。

两个链有同源 history、版本顺序和终态条款证据，强于仅主题相似；但中间版本完整正文和抽取完整响应未留在本审计证据，未做保持消费者固定的干预，不能宣称模型内部原因或认定它们造成 v4 失分。

## 不应作为生成瓶颈依据的评分/模拟器案例

- task39 / trial2 / seed26225：B1 m15 同一条消息确认地址更新并输出 `###STOP###`，后续助手无机会 write；库已要求工具成功后报告。DB失分不证明技能漏了地址规则。
- task60 / trial0 / seed670487：两组选择同一正确 $242.92 蓝色非防水耳塞。B1 m11 用户明确选 gift-card 退款，m14 正确依确认 write；B0 使用 PayPal。B1 DB=false、NL=true，gold 静态目的地为 PayPal；不能当成对象条件遗漏。policy 对 pending-item 修改要求提供付款方法，未规定只能原支付方式。
- task64 / trial1 的所谓胜出，两组都找到 4K 防水、价不超过原款；用户分别选黑/银，而 gold 只接受黑。task38 / trial2 两组都成功取消，但用户分别确认不同取消原因。这两组严格DB差异均不能单独说明生成机制。
- [task0 L32](D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill/autoskill_input/trajectories/task_0.txt:32)唯一 write 在 L33失败；L46自报成功，L51获用户积极反馈，原生 reward0。该源对应 exchange v0.1.0；终态技能反而多处要求无成功工具不得声称完成。因此可证明输入中的反馈/执行结果不一致，尚不能证明该坏结果被学习为正确流程。

本轮有新增**本地产物审计观察**，没有新实验实证。建议下一步只做受控来源依据审查：把能力/对象范围/执行结果逐项绑定到可用工具与成功状态，并分别检查 artifact 交付、消费者执行和模拟器终止；在完整因果链建立前保留“生成侧是候选瓶颈”的表述。
