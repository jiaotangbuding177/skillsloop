# 038定向会话群：前五阶段实测与技能交付

日期：2026-09-26。**实验准备与阶段1—5结构/封装验收已完成，交付3个READY候选技能包。** 最终[run05验收](../cases/038_contract_multi_review/private/051-first5-run05/acceptance-summary.json)全部程序检查通过，代码/输入/配置冻结无漂移；当前结束在待个人选择的阶段5，没有自动采纳或组织发布。

需要同时保留一个事实：本轮两次全新模型尝试均失败，随后通过修正、保存响应复用及一次剩余creator调用完成。**这不是“首次全新推理、无需修复的一次成功”，也不证明已稳定无断点。** 保存的失败和新版本均可追溯；内容审阅仍发现任务要求过度升版、候选粒度和能力宣称问题。

```mermaid
flowchart LR
    I[索引定位A/B会话] --> S1[阶段1：48条原消息→8个问答]
    S1 --> S2[阶段2：8个问答标注→2个主任务]
    S2 --> S3[阶段3：2条轨迹／8个尝试]
    S3 --> S4[阶段4：5个流程轮廓／7个方法→3个workflow]
    S4 --> S5[阶段5：3个READY技能包]
    S5 --> P[等待个人采纳]
```

| 阶段 | 本次输入与实际输出 | 验收结论 |
| --- | --- | --- |
| 1 会话采集 | 按原消息ID回查48条正文，整理8个问答；保留全部40个助手ID | 来源、正文、覆盖及分组检查通过，无人工replyTo |
| 2 任务识别 | 完整问答交LLM，程序核验8份标注，识别2个主任务 | 主任务与后续需求关联可回查；本组不能验证非任务过滤 |
| 3 轨迹恢复 | 候选关联与原文证据→2条任务轨迹，各4个attempt | 来源/关系结构通过，业务均UNKNOWN；有重复要求过度升版负例 |
| 4 学习决策与聚合 | 2条轨迹→5个流程轮廓、7个方法→3个簇/3个NEW workflow | 来源和归宿台账通过，2个workflow跨轨迹聚合；7项全纳入，未证明选择性减量 |
| 5 技能生成 | 冻结workflow→OpenClaw creator原草稿→内容落点校验及官方打包 | 3/3 READY；标准格式可装载，尚未验收新任务消费和真实文件编辑 |

## 1. 本轮实际输入

按用户要求，索引负责定位正文，集中处理合同/协议多立场审查这个会话群，没有导入企业全量会话。

| 材料 | 用法 |
| --- | --- |
| [recovered_trajectories.json](../cases/038_contract_multi_review/recovered_trajectories.json) | 只读取generation会话及原消息ID清单；不输入人工task、轮次归属或replyTo |
| [raw_messages.jsonl](../cases/038_contract_multi_review/private/raw_messages.jsonl) | 按ID回查真实用户/助手正文 |
| [source_index.json](../cases/038_contract_multi_review/source_index.json) | 核对消息身份、角色、来源行序、原行及正文SHA256 |
| 各run的selected-events.json | 保存本次真正进入阶段1的48条消息正文，全部位于受控目录 |

A为供应商角度审阅会话，37条消息；B为委托方角度审阅会话，11条消息。合计8条用户消息、40条助手消息，形成8个问答。C的22条消息未进入本轮任何模型调用。C曾用于前三阶段开发，不能作为完全未接触的最终论文测试集。

阶段1已独立核验：48个原消息ID全部保留，40个助手ID全部且仅一次归入问答，助手各段及用户正文与所选原始事件逐字一致，无孤儿事件。历史合同正文文件和历史交付文件仍不可用；助手自述不替代实际文件、工具或业务验收。

## 2. 已完成的实验预备与修正

本轮按[科研实验技能](C:/Users/39835/.codex/skills/research-experiment-compass/SKILL.md)的执行有效性、证据边界与负结果原则组织工作，不把包生成等同于论文效果。

| 050指出的断点 | 本轮处理 |
| --- | --- |
| 前三阶段与后两阶段依赖不同历史库 | 新统一runner从原消息开始，在同一新数据库连续1→5；拒绝无manifest旧库 |
| 无效输出先缓存READY、失败/预算永久跳过 | 完整验证后才可复用；运行等待/错误与学习决策分开；失败attempt保留，显式有限重试与默认不重发分开 |
| 缓存未绑定模型/提示/校验器 | 实际请求配置及源码hash进入缓存与manifest；结束再次核对漂移 |
| 方法ID与资源链接在4/5不兼容 | 确定性安全别名；支持包内合法相对引用，继续拒绝越界 |
| 证据强度、投影和workflow内容不足 | 不把无验证声明升级为成功；完整引文及必要执行引用透传；输入/输出/限制必填，超限明确延期 |
| creator只检查marker | 必须定位实际动作、适用条件和完成检查正文；不将内容落点检查称为独立语义验证 |
| 关闭自动学习仍派发、实验可与后台共用目录 | 暂停覆盖全部学习阶段；实验与后台共用目录排他锁 |
| 单个会话失败后仍处理其他会话 | 正式runner设置stop_on_failure，失败落盘后停止后续批次 |

最终应用**85项测试通过**。免费完整宿主夹具从新库走1→5并实际调用官方打包器；实际安装的OpenClaw另通过本地固定响应服务完成creator读取、草稿写入与封装，3次本地模拟请求、0付费请求。最初受限进程环境下该控制超时、stderr为空；相同控制在获准的外部进程环境中通过，原记录保留，不推断未经查证的底层原因。

准备证据：[初始准备](../reviews/051_preparation/summary.json)、[最终版本85项检查](../reviews/051_preparation/verification-final.json)、[真实8响应免费预演](../reviews/051_preparation/run05-real-prefix-dryrun-result.json)、[实际OpenClaw本地控制](../../enginering/demo/artifacts/051-stage5-transport/f26527d099/result.json)。

## 3. 原始失败与最后完成分别记录

| 运行 | 方式 | 已证实的结果 |
| --- | --- | --- |
| [run01](../cases/038_contract_multi_review/private/051-first5-run01/acceptance-summary.json) | workflow v2，全新原事件＋全新模型推理 | 阶段1通过；第一会话2/3完成；第二会话阶段2一条44字符关联引文无法逐字定位，停止。FAILED，3次新外层请求、32,870 tokens |
| [run02](../cases/038_contract_multi_review/private/051-first5-run02/acceptance-summary.json) | 同一代码、提示、原文、模型的独立全新复测 | 阶段1—3通过程序验收；阶段4输出2个frame、5个method，其中4个method跨了所属轨迹证据，停止。FAILED，5次新外层请求、65,634 tokens |
| [run03](../cases/038_contract_multi_review/private/051-first5-run03/acceptance-summary.json) | 新冻结workflow v3；阶段2/3精确复用4个保存响应，4/5真实推理 | 1—4通过；阶段5一READY、一完整返回但解析FAILED、一QUEUED。4次新外层请求、150,690 tokens |
| [run04](../cases/038_contract_multi_review/private/051-first5-run04/acceptance-summary.json) | 通用解析器修正后尝试8响应重放＋最后一次creator | 在缓存匹配时提前拒绝，FAILED；真实新增调用0、tokens 0 |
| [run05](../cases/038_contract_multi_review/private/051-first5-run05/saved-response-completion-summary.json) | 修正限定在creator模块；原事件新库、8保存响应重验＋1个新creator | **PASSED，3个READY**；新增1次外层派发、3次内部请求发起、25,544 tokens |

run01和run02运行中均未改代码、提示或配置，终局漂移检查通过。没有手工改原模型响应或把两次失败拼成成功。run01还完成了[负结果离线重放](../reviews/051_preparation/run01_failure_replay.md)：3/3原响应精确复用，0新增网络尝试，在相同位置产生相同错误及已完成轨迹。

run02结束后才修正阶段4契约表达：v2提示只说使用evidence ID，未明确宿主要求“方法的全部引用必须属于所属frame.traceId”。v3逐轨迹提供`allowedEvidenceIds`并明确先独立抽取、后跨轨迹聚合。校验器没有放宽，新增跨来源拒绝反例通过；这是新的冻结版本，不能归入run02。

run03没有复制047/049或run02业务数据库，没有采用人工trace。阶段5失败的原模型结果实际上包含完整SKILL.md和coverageManifest，只因最终JSON前带一句说明而被旧宿主解析器拒绝。[零调用复核](../cases/038_contract_multi_review/private/051-creator-parser-revalidation/summary.json)证明原内容可通过方法落点校验与官方封装。原run03仍是FAILED；旧mixed摘要误标为预算PARTIAL，已另写[勘误](../reviews/051_preparation/run03_mixed_status_correction.md)，没有覆盖旧记录。

run04暴露了运行血缘和来源指纹的耦合：改通用runtime源码会改上游runId，并传导进下游sourceHash。精确缓存拒绝是正确行为，新增模型请求为0。[诊断](../reviews/051_preparation/run04_hash_lineage_diagnosis.md)后，将兼容解析限定在`creator.parse_creator_result`与封装交接；前面分析runtime恢复为run03相同字节，没有改旧响应hash来强行匹配。正式run05前，已用真实8个响应完整免费演练至最后一次新调用门前。

run05重新从48原事件建立数据库，8个历史响应均以purpose＋完整payload hash精确匹配并重新校验；前两个creator原草稿重新官方封装，第三个creator才做新推理。历史读取回执明确标为历史，新读取只发生在第三个候选。最初本轮自设12次外层额度，在最后请求前登记调整为13次，以覆盖实际3个候选；没有付费重生成前两个包。源run03的产物和草稿保持不变，所有运行的冻结漂移检查均通过。

## 4. 前三阶段内容审阅

run02产生2个主任务，各4个attempt。两会话的合同审阅、条款追问、修订与输出要求保持在对应任务内；8个问答都有具体任务用途，本组没有NON_TASK样本，不能据此证明噪声过滤能力。

A的“追问合理性→选择方向→本轮只要文本”关系合理；局部失败/修复保留为助手声称，选项是否被正确实现继续未验证。B相比run01改善了“粘贴条款就升版”的问题，但末轮重复上一要求仍被判为CHANGE_REQUIREMENT并从v2升到v3，属于**重复要求过度升版的语义负例**。因此程序结构通过不能表述成轨迹含义全部正确。

两条轨迹、8个attempt的业务结果均UNKNOWN；原附件unavailable，无独立工具、文件或check回执；文件只作为CLAIM。详细受控审阅：[run01](../cases/038_contract_multi_review/private/051-run01-semantic-review.md)、[run02前三阶段](../cases/038_contract_multi_review/private/051-run02-stage123-semantic-review.md)。

## 5. 阶段4/5与交付

阶段4的流程轮廓聚类真实发生：`[f1,f3]`、`[f2,f4]`、`[f5]`三个簇形成三个workflow；前两个组合了两条轨迹的相关方法，第三个只来自一次交付形式变化。7/7方法都有来源与INCLUDED台账，未发生跨轨迹借证据；但本组没有产生DEFER或淘汰，不能据此证明无效技能下降。见[阶段4内容审阅](../cases/038_contract_multi_review/private/051-run03-stage4-semantic-review.md)。

最终交付全部保存在run05，**每包当前仅有SKILL.md**，没有生成可执行脚本或企业业务文件：

| 技能候选 | 正文与标准包 | 当前可用范围 |
| --- | --- | --- |
| 合同/协议审阅与修订 | [SKILL.md](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-95e6a640341d673176ebb04b/SKILL.md) · [.skill](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-95e6a640341d673176ebb04b/candidate-95e6a640341d673176ebb04b.skill) | 风险识别、分级和修订流程指引，覆盖4个方法；文件操作仍待工具支持及新任务验收 |
| 特定条款调整与文件更新 | [SKILL.md](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-17027d85bd2b65a14a29e067/SKILL.md) · [.skill](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-17027d85bd2b65a14a29e067/candidate-17027d85bd2b65a14a29e067.skill) | 根据业务背景与选定方案给出条款修改文本，覆盖2个方法；正文要求用户自行写回文件 |
| 特定条款修改文本单独输出 | [SKILL.md](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-ffd24764648b2376594ce589/SKILL.md) · [.skill](../cases/038_contract_multi_review/private/051-first5-run05/deliverables/candidate-ffd24764648b2376594ce589/candidate-ffd24764648b2376594ce589.skill) | 接收已有修改内容并格式化输出，覆盖1个方法；不进行专业条款判断 |

三包均保留标准name/description frontmatter、使用条件、输入、步骤、完成检查与限制；实际creator读取、动作/条件/完成检查正文落点、官方packager和归档字节均有证据。**READY证明规范封装，不证明内容已具备所声明的全部能力。** [两份主包审阅](../cases/038_contract_multi_review/private/051-run03-stage5-semantic-review.md)发现：第一包同时写“自动输出修订文件”和“仅承诺文本流程”，能力描述不一致；第二包标题含文件更新但实际明确依赖人工写回。第三包的内容与其窄范围相符，但独立成skill的增量价值较弱，可能应作为主workflow的输出分支。这些均未通过人工改写生成物来掩盖。

目前适合将这些包视为**可以进入个人选择与后续消费测试的候选**。不建议直接以“已可自动编辑Word合同”的能力发布组织库。下一步应使用有实际附件/工具条件的新任务验证读取、文本产出、文件操作和用户修订，优先检验粒度及条件完整性；不应马上扩到企业全量来累积生成数量。

## 6. 复现材料与边界

各run保留manifest、20份冻结应用源码副本、选定事件正文、阶段JSON、请求状态、实际模型请求/响应、运行用量及失败原因。creator阶段另须保存实际读取回执、草稿、官方打包日志、标准化文件hash及归档核验。密钥不进入manifest或研究记忆。

[051协议](../protocols/051_targeted_first5_acceptance.md)记录每次终止及后续选择；[复现说明与命令](../reviews/051_preparation/README.md)区分产物hash校验、保存响应处理重放、真正新模型独立推理。最终manifest为`01092e3e0981d5167a327eb687474784626e25c9627fc0f736abe22eca6580cd`，选定原事件hash为`802ecdcd5b62bc6aef77df259ae1d1c9ca2a34f17c584f491b11c4c68f521c30`。

本轮有真实请求的run01/02/03/05合计**13次新外层派发、26次内部请求发起、274,738 reported tokens**，包括失败，不重复计算保存响应的历史用量。run04及免费控制无新增模型资源。tokens口径包含模型回报的缓存读写；现金费用**UNKNOWN**，OpenClaw配置未提供可核验的计价，不能把输出中的0解释为免费。`failed_calls=0`只可能表示远端正常返回，不表示模型结构/内容全部通过。

最终[免费复现证据](../reviews/051_preparation/run05-final-offline-verification.json)已通过：15项产物完整性检查通过；完全断网重放精确消费9/9保存响应，从原事件完整重建1—5，六类阶段投影hash全部一致，三个SKILL.md内容一致、官方封装复核通过；新增网络尝试、模型推理和OpenClaw读取均为0。详见[重放比较](../cases/038_contract_multi_review/private/051-run05-offline-replay/replay-comparison.json)。这是宿主处理可复现的证据，不能代替远端模型重新采样的一致性。[资源核算](../reviews/051_preparation/new-resource-accounting.json)保留每次新增用量及缓存排除口径。

技能是否更有效、是否降低无效量、是否节省总体模型资源、是否具备企业业务收益均尚未证明。阶段5终点是待采纳候选，个人选择、实际执行、反馈演化和组织审核仍按原十二阶段契约进行。
