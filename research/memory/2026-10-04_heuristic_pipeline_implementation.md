# 启发式全管道实现与隔离验收

本轮2026-10-04开始，跨日于10-05继续；run目录为UTC编号。

## 用户已确认要求

- 用户明确开始实现已讨论的启发式算法全管道。授权限本项独立Demo，不永久切换科研模式。
- 保持十二阶段契约；重点是关系轨迹恢复与有条件、可复用的工作流归纳，不采用AutoSkill作为本项目方法。
- 未验证来源正常处理，缺失与未知不补猜；个人采纳、组织提交审核及精确版本治理沿用原链路。
- 本轮不启动微调、强化学习或大规模benchmark；此前模型训练方案仍为后续设计。

## 实施及证据支持的观察

- 新增evidence、relational和relational_workflow，接入front/core/runtime/cache，复用creator、学习patch与原治理。真实模式默认heuristic，旧legacy路径和旧库保留，新数据目录隔离，无新增业务表。
- E/C/V保留实际调用、结果、公开上下文和稀疏评价。来源范围、调用编号、要求维度和有效版本贯通；任务总分不证明步骤，技术结果不变业务结果，计划/进度/自述不变已执行能力。
- 模型只提出语义候选；程序实施引用、时间、归属、依赖、覆盖及有界beam检查，未决项传至聚合。whole-cluster相容检查与clauseLedger约束技能条款；更新检查获准方法、来源范围、实际skill基准版本和hash。
- 最终冻结回归271项全通过、39.749秒；此前冻结256/224项、改动前92项均为历史实跑结果。新增29项预绑定更新矩阵、15项限定解析/core及调用回执测试，独立审阅同构反例通过。用例来源为人工构造，证明程序约束而非语义准确率。
- 最终冻结版本十二阶段fixture（185704014384Z-a7064f26）通过：13宿主派发，真实模型请求0；本地文件读取、非空交付、官方校验打包、个人v1→v2及组织复用后再次反馈恢复均执行。组织审核决策为合成测试，未自动发布反馈更新。

## 失败与修正保留

首轮真实模型完整返回，但seeds/memberships为字典、同任务多OPEN、分片/引用结构不合契约，宿主拒绝，未产生轨迹和技能。1真实请求，qwen3.7-plus，5585总tokens，非benchmark有效0。原失败、输入、响应和源码快照全部保留。只补全输出模板并加模板契约测试，没有对真实响应填补语义或放松validator；新版本另目录运行。开发中还修复了无参数工具调用消失、公开/私有workflow hash混用、要求格式变化误伤其他维度与同回合工具结果归因等具体缺口，记录为软件修正，不升级为算法效用结论。

第二次真实run完成生成、采纳、读取技能、交付与反馈，但恢复器拒绝同维度两条可并存ADD，未到更新。7宿主派发/17真实模型开始，原run保留；修正为同维度同范围ADD并存、只有明确REPLACE覆盖，并保留未来与本次应用两个范围。

第三次真实run（live-20261004T153848122242Z-332ccbbe）完成阶段1—8且反馈关系恢复成功，7宿主派发/15真实模型开始；阶段4材料145105字符超过原110000上限，系统延期，未出UPDATE。重复工具正文及结构导致膨胀，不是R恢复失败；不增加预算、不截断来源。已实现无损索引，原材料145105→92222字符（-36.4%），展开严格相等，全部8尝试/23类型化来源/43关系/8要求/6结果/29来源目录行保留。字符缩减不等于token/费用下降。旧失败/源码/响应保留。

第三run的R保持未来规则与当前交付应用分离，保留真实read失败和随后write成功，业务均UNKNOWN。语义覆盖尚有局限：模型只引用部分助手标题，未完整类型化全部正文；助手答复把用户未来偏好缩为当前，但R依用户原文恢复未来要求。合法结构不证明完整语义恢复。

第三run的v1结构范围检查通过，但自由正文仍把历史纯文本写成默认成果；最终采用逐工作流步骤的范围约束与确定性组装：METHOD/STEP分别覆盖，同方法多步分别绑定；元信息按本次要求重新绑定，原模型稿留作审计。格式合法与组装不能证明专业语义正确或辅助资源有效。阶段9最低范围保留弱于阶段5逐步覆盖，新增范围的跨版本位置仍未全面保证。反馈实际写出修订文件但旧outputs读取失败，不称原位修订；已完成同会话已登记文件权限/哈希交接，4项测试通过，历史副本只放inputs/history、不计新交付。

第四run（161518468674Z-9ab23862）和第五run（164427858281Z-c9ab0513）各4宿主派发/6真实开始，1—4完成，creator审计被拒：前者实际单一Get-Content读取但旧审计只识read；后者实际读安装官方文件但旧审计只认副本。两个官方文件2304字节、SHA3b7b93823a496cedc957fc91bbc8f8be132f2edd095dcaa46cee5394c742f0e4相同。修正后免费重算均FULL_FILE；原FAILED/DB/响应不改，不追认通过。限定官方别名核对初始化SHA和两原文件，保留actualPath，通用读取仍workspace内；官方收据从未截断native工具记录形成。第五实际读取安装源已确证，系统技能提示如何注入未从nativeDB独立核实。

前五真实run合计23宿主派发/45真实模型开始，记录runtime tokens448105、运行墙钟1861.177秒；两类缓存/API字段混合，不推正式费用。供应商传输重试未测，免费预演不计真实通过。

## 真实模型最终验收

第六run（live-20261004T170427883275Z-feb3ae06）已FAILED，1—6通过、官方完整读取及封装采纳v1。消费唯一Get-Content为Encoding在Path前、绝对目标且没有workdir；旧审计误拒。stdout与当前v1全文件相等，stored/workspace规范化文本filesDigest同adb78866a1c8f80b7f853269e05a4dd91be1f558507e84830028afc96f9de2c0，实际输出review.md1586字节；反馈/v2未执行，原失败不改。已修严格allowlist合法顺序、绝对精确目标与selected正文身份核验；相对路径仍要求工作目录。两份物理正文仅CRLF/LF不同，不能误报版本变化，也不忽略其他空白差异。

六次累计28宿主派发/54模型开始、533174记录runtime tokens、2118.027秒运行墙钟，费用/传输重试未测。第六31份源码前后/fixture完全相同，canonical=fc3b3625e45c4151d10b1c74debb2e7dea5e26b9c3e51bbfc9e8ef6a7fe61aba；input SHA22df9d28f8098a4f9788277e66a70ca362cc1964a5fd6b932cc4111ec4c038e6。对六run已存10原生会话/28工具免费预演，5官方+5selected v1均完整，selected正文身份与5份bundle摘要均匹配，DB主文件SHA不变。原六次FAILED均保留，不追认完整通过。

第七run（live-20261004T172148621668Z-a6baae0c）真实1—8通过、最终FAILED。10派发/20模型开始、366841记录runtime tokens/688.069秒；七次累计38/74/900015/2806.095秒。两轮v1 FULL_FILE+identity VERIFIED，1610/2338字节交付及历史文件交接真实执行。更新器只引用m2证据:e11却选择m1+m2，validator正确拒绝；还存在scope带说明、完整future引文欠缺及原引号被改写。没有v2，不改原状态/响应；31源码前后/fixture相同(dd80ff182710a905bb1a60bb14d303c90146c0fe33437b27dfe3b02ff490f2b5)，159产物清单匹配，旧六FAILED哈希不变。当前实施宿主冻结prebound提议，使model选择获准增量和ops，不重猜来源范围、不放松检查。

第七R正确分开2未来要求与2本次应用，未来版本2不入当前尝试，本次版本3入修订；7要求/4尝试/18关系/13类型化来源保持UNKNOWN。语义缺口：完成自述被误标VISIBLE_TEXT；仅2write绑定、8执行绑定未决未进W类型化输入，原来源仍存。不能说完整恢复所有工具或整体语义准确。W索引实际预算60005、展开84696字符(原110000)，完整往返；不是tokens或上游完整性证明。本案例及反馈合成，不属于企业自然会话或独立效果评测。

最终修正：已合法绑定call的同pair/run/callId唯一后续result由宿主客观补齐，basis=HOST_EXPLICIT_CALL_RESULT_LINK。第七保存响应免费重放补2write结果到attempt/typedSources/W catalog，其他6条仍未决、业务UNKNOWN、原DB哈希前后相同。原模型仅提2call，补齐非改写模型UNKNOWN建议，保留客观补齐审计；完成自述误标仍是已知语义限制。

阶段9新contract由宿主冻结method×scope单元自己的完整引文、来源、范围和插入正文；模型仅选单元、唯一METHOD/STEP锚、insert_after和NO_CONFLICT理由。禁止自由content/analyses/title，保留基准旧段/市场。独立复现发现可用HTML/Markdown遮guard以及混合不同scope动作泄漏，最终采取来源数据转义及同维同值客观对齐；多scope部分SOURCE_BOUND没有dimension/value也不能忽略，必须延期并保留来源。正常同值future+current副本允许。NO_CONFLICT仍NOT_INDEPENDENTLY_VERIFIED，基准最低保留不等于stage5完整逐步覆盖。

最终第七静态免费预演为APPROVED1(CURRENT_TASK)、DEFERRED2(CURRENT_DELIVERY/FUTURE_TASKS)，当前单元人工选择位置编译/官方校验通过、provider0，8原静态材料hash不变。这不是未来偏好更新或真实v2通过。公共投影3696字符、原50961字符，非token或费用测量；私有完整引文不删除。原生learn公开配置更正为实际两提示变体、投影/附加指令、8192/DEMO_AGENT_TIMEOUT/tempNone，cache身份同步，旧run配置不追改。

第八真实run已启动新冻结目录live-20261004T1825-final-prebound-a3c07162，同输入SHA22df9d28f8098a4f9788277e66a70ca362cc1964a5fd6b932cc4111ec4c038e6；31 source与最终fixture相同，canonical b6eaabcf0585c262bced46907eeb572661789f71ac6b2c0aef0e35e2b2d80d5c。完成结果待写；不在运行中改source。若合法DEFER/SUPPORT导致烟测READY断言失败，分别记录算法正确延期与未达成v2，不能称越界或追认成功。

更正该运行阶段状态：第八实际完成1—8/最终FAILED，10派发/19开始/274583记录runtime tokens/876.319秒；八次累计48/93/1174598/3682.414秒≈61.37分。两回合v1 FULL_FILE+identity VERIFIED，1296/2817字节交付真实。失败非合法DEFER：final中文解释+唯一json围栏→pure parse char0拒绝；analysis.json与围栏对象相同，原compiler可7applied/3deferred，但第八未包装/采纳v2。163产物/31source前后及该版本fixture相同，前七FAILED hash不变。阶段5creator official完整读取通过；阶段9另read错误repo根路径真实失败。其R执行绑定为空、10原工具全未决未进W，初始化自述正确为CLAIM，但部分可见回复仍含自述；业务UNKNOWN。

最终新分支解析只接受严格对象或唯一明确完整json fence；多块/无标记/截断/猜花括号拒，原text及SHA/块位置审计保留，同一compiler/legacy/R/W不变。第八fenced源原文SHA95be57839cf8253c7e6dfa46eac4f30661d721f3ff2b0ad93365ee0df622ab88，解析obj等于已写分析文件；免费预演不追認第八通过。

为减少重复模型调用，独立stage9 continuation runner复制已完成source state、创建新candidate/new run，只继承第八真实1—8。最终免费190116-e7cb1128 PASS，0real/1dispatch：原捕获stdout硬绑source candidate runId且与stored text逐字一致，v2同skill id/hash3838fe498e89e7c57f3867bf73685dd1833a5796b89eeddfa7dbaf9820ae990c，旧v1 files/hash精保，官方receipt从新run结果取得、ZIP逐项等于采纳正文。源state及八原FAILED报告不变；32代码canonical34ec504c1e2b04ee74cec90849c7b7d75f7799eb68bec49361733fdb72ff499b/common31与最终fixture相同(d150e2d575692dd059065261f1abdbab8393605c906a69713a087128cb16e69f)。早一免费run package字段取错对象为null，原不改，新runner修并另run验证，不隐去元数据缺口。

更正续验终态：stage9-live-20261004T190145188788Z-4ef5824d已FAILED，1—8继承、新1派发/7真实开始、114240记录runtime.total。原生CLI exit2/ok=false/status=timeout/final为空，embedded约299232ms限时，实际elapsed319502ms，在宿主345秒communicate前返回，非宿主kill或parser拒绝。7请求HTTP200及7工具0失败不证明最终完成；工作outputs/analysis.json不回填权威text。源码32项前后相同、源state不改。memory-reindex报错仅观察，无超时因果证据。修正方向仅精确新冻结契约一次结构化选择，公开输入已含基准/单元/锚，宿主仍校验和官方包装；creator/chat/legacy原生能力保留，新版本另冻结，旧超时不追认成功。金额/传输重试、语义质量/独立技能收益仍未知；无新benchmark或训练。

## 研究假设、未知与下一步

最终选择执行路径调整后源码再次冻结，281全回归通过/44.875秒，新增10个direct路由及失败mock测试；fixture192259637816Z-30c0e72e PASS13dispatch/0real，31source前后与快照一致，canonical=c395fd2d40edf1207721a7e9272e3b34420378ef58dc27240954067d5be37776，55项产物清单一致。独立AST核对：去除新增learn早分流后native run与185704旧版相同，creator提示不变；因此未放宽阶段5、chat、legacy原生通路。缓存口径澄清：learn本身未接入R/W结构化结果缓存；runtime源码指纹变化使已有缓存身份失效，公开路由配置用于复现。新stage9-live-20261004T192338068556Z-7ace1613只继承旧真实1—8、发一次direct选择，终态待记录；不自动重发。

- 假设：关系恢复与条款作用范围控制可减少无证据能力扩张，并提高独立任务复用；目前没有增益对照证据。
- 阶段2—3单次冷启动语义派发替代分开派发，整体tokens、费用和有效技能覆盖仍待匹配条件测量；不承诺全面资源下降。
- 模板合规、beam结果、来源引用或完整功能loop不证明语义正确、全球创新、skill实用性、更新收益或论文达标。
- 下一步冻结本方法后设计同输入的强基线对照，分别验证关系准确/覆盖、技能条款变化、独立任务效用及全成本。微调和RL不混入本轮。

## 本轮最终交付与未通过项

最后direct续验192338068556Z-7ace1613已FAILED，180.202秒socket read TimeoutError；不是模型合法DEFER，尚无完整回复、usage或patch/v2。输入与公开branch配置逐字一致：qwen3.7-plus/anthropic-messages/8192/temp0/180秒，7APPROVED/3宿主DEFERRED/8锚，无tools或native控制工作区。仅新增1run/1dispatch/1记录请求开始，继承10旧run不重复计。32source前后/快照/当前一致，canonical=eabb1a407a0dc2060c22e369523442106e716ba69de3b60ce54fda86c5178f7c，共同31等于最终fixture c395fd2d40edf1207721a7e9272e3b34420378ef58dc27240954067d5be37776；167产物清单匹配，129源state文件不变。旧八FAILED/上一原生续验FAILED/免费v2 PASS报告SHA均保持，原candidate/skill v1对象逐字不变；凭据字面复扫168文件无当前key字节，非全面凭据审计。acceptance SHA02775d5f16ba320ddd4b411e3af074cb362cfd648c151604e039163fdb2e0da8。独立只读审计通过。

本轮停止新增真实调用，未启动新服务/训练/大规模benchmark。全体十次实际尝试50宿主派发/101记录开始，已知runtime.total1288838＋最后1次UNKNOWN，费用/传输重试未知。软件功能原型与281回归/十二阶段fixture已交付；真实1—8及捕获真实回复免费回放v2已完成；同一冻结版本真实1—9完整闭环未通过、实时更新仍受响应超时阻断。原生memory错误与direct超时的底层原因未证，不能说代码修正已解决服务问题。无效技能减少、有效方法保留、语义准确率及独立benchmark提升仍是待验证目标，不是本轮实证结论。

## 来源与产物

- [人话实现报告](../reports/2026-10-04_heuristic_pipeline_implementation.md)。
- [规格](../../enginering/demo/HEURISTIC_PIPELINE_SPEC.md)、[计划](../../enginering/demo/HEURISTIC_PIPELINE_PLAN.md)、[清单](../../enginering/demo/HEURISTIC_PIPELINE_TODO.md)、[验收汇总](../../enginering/demo/HEURISTIC_PIPELINE_ACCEPTANCE.md)。
- [最终fixture](../../enginering/demo/artifacts/heuristic-acceptance/runs/fixture-20261004T192259637816Z-30c0e72e/acceptance.json)；[前一冻结fixture](../../enginering/demo/artifacts/heuristic-acceptance/runs/fixture-20261004T185704014384Z-a7064f26/acceptance.json)。
- [第七真实run](../../enginering/demo/artifacts/heuristic-acceptance/runs/live-20261004T172148621668Z-a6baae0c/acceptance.json)。
- [最终预绑定更新免费预演](../../enginering/demo/artifacts/heuristic-acceptance/preflights/seventh-run-prebound-update-final-d0620aa6/preflight.json)。
- [调用返回免费重放](../../enginering/demo/artifacts/heuristic-acceptance/relational-call-result-preflight-20261004T180547-0555349d.json)。
- [第八真实失败](../../enginering/demo/artifacts/heuristic-acceptance/runs/live-20261004T1825-final-prebound-a3c07162/acceptance.json)。
- [最终固定回复续验](../../enginering/demo/artifacts/heuristic-acceptance/runs/stage9-captured-20261004T190116866877Z-e7cb1128/acceptance.json)。
- [原生更新超时](../../enginering/demo/artifacts/heuristic-acceptance/runs/stage9-live-20261004T190145188788Z-4ef5824d/acceptance.json)；[最后单请求更新超时](../../enginering/demo/artifacts/heuristic-acceptance/runs/stage9-live-20261004T192338068556Z-7ace1613/acceptance.json)。
- [全部原生读取免费复核](../../enginering/demo/artifacts/heuristic-acceptance/all-native-read-preflight-20261004T172019-242aa385.json)。
- [第四/第五官方读取免费复核](../../enginering/demo/artifacts/heuristic-acceptance/creator-read-preflight-20261004T170330-2e744239.json)。
- [原真实失败](../../enginering/demo/artifacts/heuristic-acceptance/runs/live-20261004T143246915143Z-95fd9e4e/acceptance.json)。

其他聊天的实验、服务和历史负结果未操作；不改变其状态。
