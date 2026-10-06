# 关系恢复驱动的启发式全管道

本轮授权：实现已讨论的启发式算法，不启动微调、强化学习或大规模benchmark。十二阶段契约不变；新算法贯通证据输入、阶段2—5与使用后更新，复用个人采纳、真实执行、精确版本治理及组织审核机制。

## 输入与证据

输入为 `E/C/V`：原事件、公开上下文、可为空的稀疏评价。`import_experience` 接收events/context/evaluations；旧import_events继续可用。上下文与评价必须有稳定ID和来源，所有内容进入来源指纹。benchmark的reward_info、金标actions、assertions、hidden goals不属于默认学习输入；只接收显式allowlist字段的评价。来源原文不静默截断，超预算延期。

新增 `evidence.py` 负责规范化。给恢复器的目录项为id/kind/text/ref/metadata，其中ref保留原事件和pair身份。工具调用/结果保留callId、name、公开arguments/result、原记录顺序，结果不能与邻近但不同callId的调用拼接。检查/评价区分技术、业务与用户主观反馈，任务级评价不得下放到单步。缺失即UNKNOWN。

## 阶段2—3：一次语义抽取，程序联合恢复

`relational.prepare(pairs, context, evaluations)` 提供完整问答、证据span、工具目录及评价目录。`relational_extract` 是一次受缓存及额度控制的模型请求，同时提出：

- seeds、annotations沿用pair_detection格式，全部用户正文有处置；
- memberships每个fragment给options（task/status/score/reason）；
- relations每项id/source/options（target/kind/score/evidence/reason/delta/scope），允许UNKNOWN；
- observations沿用source-span引用，增加PROGRESS_TEXT；
- requirements（fragment/dimension/op=ADD或REPLACE或RETRACT/value/evidence）；
- executionBindings（evidenceId/fragment），evaluationBindings（evaluationId/fragment/scope/requirementVersion），不自行生成工具结果或评价。

模型score只是排序值。宿主进行有界beam搜索，检查候选任务合法、引用确在源中、同任务关系、反馈不能指向未来、依赖无环、显式对象/调用绑定、全部片段覆盖；保留接近的可行备选及未决项。缺证据不能由最高分消除。输出仍为task-trace-v2以兼容当前治理，附relationalSchema和searchAudit。

标准轨迹新增：requirements按维度和作用范围继承/替换/撤销。同一维度同一范围的独立ADD共存，重复值累计真实来源，REPLACE才替换该维度该范围；不凭字符串差异判断相斥。timeline单值兼容原字符串，多值用数组，scopeValues保留分范围状态。未来规则与用户明确要求的本次应用可同时登记，未来规则本身不进入本次attempt。attempts只围绕可见交付或实际调用建立；typedRelations记录要求、反馈、动作和评价指向；outcomeEvidence含id/sourceType/outcomeType/status/scope/targetIds/criterion/ref/verified/unknownReason。任务闭合只表示本观察窗口已整理，不代表成功。quality不以成功分数代替。

对已合法且唯一绑定到片段的TOOL_CALL，宿主可补其同pair、同run、同callId、明确后续顺序的唯一TOOL_RESULT，记录HOST_EXPLICIT_CALL_RESULT_LINK及原调用/回执来源。不覆盖已有模型绑定，不猜其他动作或结果的任务归属；缺编号/顺序、重复、跨来源或冲突时保持未决。技术状态沿用真实回执，业务结果仍为UNKNOWN。

## 阶段4—5：有证据范围的workflow与skills

保留现有LLM局部方法提议与complete-link聚类；程序对整个簇的相容性、方法证据和关系依赖进行复核。typedSources贯通恢复到聚合。task整体评价不能支持method成功；技术工具成功不能证明业务目标；仅计划/自述的方法不进入已执行能力，保留假设或待定。

每条最终步骤形成clauseLedger：触发、方法、出处、支持范围、依赖关系、未决边界；源条款和关系被修订时沿用既有hash失效机制。公开SKILL.md不含受控原文/客户ID/评价金标，仍使用官方creator读取、宿主覆盖检查和打包。实际用过的技能走精确版本UPDATE。

阶段4的模型传输允许workflow-input-index-v1：完整正文和重复结构按内容哈希单存，原位置为索引引用；宿主展开后必须与未索引原对象严格相等，模型不能改目录或创造证据ID。只在索引JSON比原JSON小时使用，原私有catalog与allowlist不变；110000/100000字符预算保持，不能靠删除事实或提高额度绕过延期。

新方法还输出scopeContract：CURRENT_TASK/CURRENT_DELIVERY为待重新绑定的实例参数，FUTURE_TASKS仅在有用户来源时作为明确个人偏好，未知范围保留未决。私有requirementApplicability保存维度与来源；公开bindings只含范围、模式和宿主固定说明。creator必须在对应方法正文逐字写入范围说明，并在coverageManifest.scopeQuotes提供scopeId与原文；宿主精确检查，不接受文末通用免责声明。这证明范围契约被覆盖，不证明自由正文不存在语义矛盾。

新封装另有stepScopeContract：宿主为每个冻结工作流步骤规范化stepId，逐项映射获准方法和范围。同一方法复用在多个步骤时，每个步骤都需保留范围；不能只覆盖一次方法卡。独立OpenClaw仍读取skill-creator并生成原草稿；程序根据冻结方法、步骤、条件、依赖和范围确定性组装最终SKILL.md，使用按本次要求绑定的描述/市场模板。原provider草稿及其清单保留审计，最终清单分别验证METHOD与STEP正文，不用自由扩写替代冻结事实。官方验证和打包仍执行；此结构保障不等于语义/业务正确性已验证。

阶段9的新关系分支采用approved-method-proposals-v1。宿主从获准方法逐作用范围冻结更新单元，私有部分含该方法自己的完整来源引文、来源轨迹、证据类型、范围、增量正文、基准文件与哈希，并先通过原方法/引文/范围validator；UNKNOWN或不符合原检查的单元明确延期。模型只接收公开投影，不重复填写来源、范围或自由正文。

模型只能选择获准单元、基准SKILL.md中唯一的METHOD/STEP锚及insert_after，并明确NO_CONFLICT理由。宿主把选择编译为保留原锚段的局部replace，新增正文来自冻结方法动作、条件、完成检查、范围说明和UNKNOWN边界。禁止整包重写、任意追加、自由content或凭方法局部编号猜替换关系；缺锚、冲突或替代关系不明则DEFER。基准已有范围与市场段保留，旧legacy输出契约继续有效。模型的无冲突判断仍不构成语义兼容证明；基准范围最低保留也不等同于阶段5完整逐步骤覆盖。

一个方法包含多种作用范围时，只有客观可对齐的同维度、同值规则副本才可分别冻结；不同规则的混合动作缺少范围内分支绑定时延期，不机械把整段复制到每个范围，也不另调模型补猜。新增正文中的来源动作/条件/检查按数据转义，不能用HTML或Markdown格式隐藏宿主范围与未知说明；这种检查不等于完整语义或专业质量验收。

同会话使用后的文件修订复用真实交付：仅同成员、同session已登记产物，经原权限入口和内容哈希核对后复制到下一回合inputs/history。提供来源与可用状态、按时间排序；历史输入副本不计本次新交付。缺失/哈希变化/尺寸超限明确记录，不猜内容。消费者读取最近可用的旧稿再写outputs；用户明确未来偏好不能被助手缩成当前，后台仍走候选更新和个人采纳，不能提前声明已修改注册库。

原生文件访问证据兼容专用read与明确单一PowerShell Get-Content。后者只接纳成功native回执、唯一带引号的精确目标路径与严格allowlist文法，允许合法参数顺序；绝对目标不依赖工作目录，相对目标仍要求已知匹配工作目录。返回正文还须与实际文件全文或合法非空前缀相等；复合命令和不能核验的输出保持未观察到。FILE_READ表示访问证据，readRange另记全文/部分/未知，均不证明模型遵循或业务收益。真实selected输入带技能正文时，还核对读取入口与选定正文的身份；仅按已知CRLF/LF换行规范比较，保留物理文件SHA和文本身份依据，不删除空白或猜版本。缺正文的旧测试访问证据明确不作内容身份验证。

官方creator另有一个限定别名：OpenClaw系统可能提示精确的安装版skill-creator入口。宿主只认可该固定官方路径或工作区.foundation副本；安装入口、工作区副本和初始化时保存的SHA须一致，并保留实际读取路径和别名核验依据。任意同内容文件、用户指定别名或缺失初始化依据不获批准。专用官方收据在未截断的原生工具记录层形成，公共工具摘要仍按8000字符显式截取；不能从摘要或助手自述假造读取。

## 运行与验收

算法选择显式记录为heuristic或legacy；旧数据不原地迁移，新验收独立目录。真实模式启用heuristic，旧回放和旧测试可显式legacy。新增测试覆盖交错回归、延迟反馈、单维要求替换、call绑定、成功自述与工具失败冲突、任务评价不下放、缺材料、未决保持、簇传递冲突及creator/个人使用/反馈更新。模型fixture验宿主逻辑；真实模型烟测验通路，均不声称显著bench增益。

learn按精确proposalContractVersion选择执行方式。approved-method-proposals-v1的公开输入已包含基准正文、获准/延期单元和唯一锚，因此使用一次结构化模型请求选择，无工具循环、不要求再次读取creator，不从超时工作文件补答案；随后仍由原宿主校验、编译、官方打包和个人采纳。该请求输出上限8192、温度0、超时来自DEMO_DETECT_TIMEOUT且上限240秒，原文/请求/响应及请求开始计数独立保存。阶段5官方creator与实际chat仍使用OpenClaw；legacy learn仍保持原生代理方式。公开配置、路由、提示与投影进入缓存身份，未知非空契约拒绝，不能凭任意truthy字段选择新分支。密钥不进入公开配置或源码快照。

新冻结学习分支接收严格JSON对象；若完整最终回复带解释，仅可接收其中唯一、明确标记json且完整的独立代码块。多块、无标记、截断和猜花括号均拒绝。保留原回复及解析格式、原文哈希和块位置审计；解析后的对象仍经过完全相同的单元/来源/范围/锚检查。旧legacy及R/W解析保持原契约。此为输出包装接收，不是补字段、修语义或追认旧失败。

实施顺序：规范化与契约测试 → 关系内核 → workflow条款约束 → CLI/宿主接入 → 全量回归及独立端到端 → 研究记忆。当前不存在项目Trellis状态机；按本项目已有研究契约和Demo规格执行，不初始化无关全局开发框架、不提交、不推送。
