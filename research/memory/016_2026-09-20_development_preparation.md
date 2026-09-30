# 016｜Skills 升级开发准备与 grill 决策

日期：2026-09-20。范围：基于enginering现有源码形成plan、spec、test和todolist，未开始业务实现。

## 用户授权与已确认要求

- 用户要求做好开发代码准备，只升级skills链路，不确定方向使用grillme。
- 本轮仅开启该项准备所需的开发入口与grill-me／grilling，未安装开发环境、建分支或工作树、迁移、业务编码、运行测试或实验。研究主线和每轮记忆仍有效，不永久切换开发模式。
- Q1：未验证候选正常处理。用户通常不说满意／完成，系统应自行判定链路结束。
- Q2：模型在原对话提出任务标记／澄清，根据用户反馈记录；禁止增加会话界面操作。
- Q3：严格复用原用户提交、组织审核后的技能共享链路；企业级聚类不构成跨成员共享会话授权。
- 继承减少无效／单批产物、保留有效能力、模型资源尽量减少且至少不增加、零新表优先、原技能格式与直接使用归因路线。

## 产物

开发包位于 [docs/skills-upgrade](../../enginering/insightweaver/docs/skills-upgrade/README.md)：

- [PLAN](../../enginering/insightweaver/docs/skills-upgrade/PLAN.md)：P0—P6顺序、范围、数据兼容、回退。
- [SPEC](../../enginering/insightweaver/docs/skills-upgrade/SPEC.md)：S01—S12，数据／事件／规则／自动封口／预算／发布／应用与源码依据。
- [TEST](../../enginering/insightweaver/docs/skills-upgrade/TEST.md)：合成夹具、单元／DB／runtime／Web测试矩阵及现有命令；全部待实施执行。
- [TODOLIST](../../enginering/insightweaver/docs/skills-upgrade/TODOLIST.md)：准备清单、T01—T24实施依赖与验收。
- [DECISIONS](../../enginering/insightweaver/docs/skills-upgrade/DECISIONS.md)：grill设计树、用户答复和待决策。

## 新增静态源码观察

三项并行只读核查覆盖数据／运行、发布／测试、模型预算；随后对文档进行边界复核。开始时源仓Git状态干净。

1. Observation一request一行，但技术stream重试可能多run；规格以evidenceRefs.runs[]保留，不允许标量覆盖。activeRun为内存对象，不能冒充持久runId。准备阶段可在主要finally前失败。
2. Snapshot旧observation唯一、文本必填、upsert及Cascade与任务追加修订不同；零新表需要kind、任务修订、索引、CAS claim和协调清理。
3. 当前企业共享workflow实际可含其他用户样本；只在Evaluator过滤本人Observation仍会读取共享workflow。Q3要求v2同表按用户隔离，旧共享文本不作v2输入。
4. 当前没有skills周期调用／token硬预算。批20、尝试3次、计费hold等不是硬额度；fingerprint／workflow没有完整usage回传；creator可多轮及repair；KM请求没有已核实的底层限额、运行幂等、完整终态／取消协议。
5. 当前KM包PUT没有可见expectedRevision／expectedHash／expectedAbsent。API先读后写不是原子条件更新。正文与文件树读取也未显式绑定实际来源版本。
6. 当前NEW已有autoAcceptPersonal配置，默认false；是否继承UPDATE是产品决策，不能默认。
7. API用node:test/tsx，Web用Vitest；旧失败候选删除测试锁定隐藏同key技能的行为，需要按NEW／UPDATE改预期。原scheduler竞争mock与注入mock不能代替真实并发／版本证明。

精确路径和行锚点见SPEC S12以及TEST现有回归部分。本轮无新增运行实证发现。

交付前核查：Git status仅新增docs/skills-upgrade目录；git diff --exit-code -- apps packages返回0。确认四份主文档和决策表已落盘，D01—D03无遗留待答分支；测试仅设计，未执行。

## 当前设计建议及边界

- 自动封口与业务成功分开；纯文本结果可正常处理。复用现有tick和DB到期字段，不加独立模型判定调用；无用户回复也能进入原预算提炼。
- 原用户任务本地断流／远端未知允许incomplete封口并处理已有材料，不重放业务；后台学习job未知则保留预算，不重复发模型。
- 封口／重开可追加状态修订，但材料hash排除纯状态变化；累计引用保留旧稿归属，支持后来纠正第一稿。
- typed taskSignals不是既有协议，首版有终态／引用／静默窗口fallback；不在正文塞JSON，不加report_task工具造成额外轮次。
- NEW要求原子不存在条件，UPDATE要求基准条件；迟到纠正在远端发出后不能原子撤回，记录实际发布与需复审状态。
- 不为少建表把运行预算塞入全平台计费状态；远端限额、隔离草稿、条件发布、一致版本读取是显式依赖，不伪装本仓已有能力。

## 未解决及下一步

- 已发Q4：不增加资源比较基准，是同等输入旧链路实际消耗、已有批准预算，还是先完成计量／配置而暂不定数值。
- 已发Q5：NEW是否沿用原自动采纳配置、UPDATE明确采纳，或其他用户选择。
- D04／D05答复后同步四份主文档及决策表。实际预算数值、远端能力验证与部署仍为实施／启用依赖，不编造完成。
- 用户尚未授权业务实现，本轮不是测试已通过、系统已升级或论文贡献已成立。

## 更正记录

014的默认0-LLM轨迹路线保留；“未知结果暂存”不能解释为无验收永远不提炼，已按Q1更正。原准备稿D02加UI推荐被用户否定，现改为原对话内模型提议与反馈。013历史企业共性workflow建议在v2私有材料范围内收窄，组织共享仅走原提交审核。
