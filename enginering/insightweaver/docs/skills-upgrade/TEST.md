# Skills 升级测试方案

## 018实际验证入口

当前行为契约以[V1_ADAPTATION.md](V1_ADAPTATION.md)为准。新增 `skill-trace-loop.postgres.test.ts` 在明确指定的本地 `trace_test` PostgreSQL数据库运行；未提供 `SKILL_TRACE_TEST_DATABASE_URL` 时会显式跳过，不能计为数据库验证通过。真实事务锁／迁移与v1接口替身测试分开解释，未伪造远端CAS或内部usage验证。`zclaw-trace-packaging.test.ts`覆盖隐藏草稿内部校验与禁用重发。最终执行结果见IMPLEMENTATION；以下用例表仍是扩展目标，未逐项全部验收。

日期：2026-09-20。**以下是待实现的软件测试规格，不是已运行或通过的报告。** 不调用真实模型、不访问生产、不设计论文实验。D04／D05相关策略用例在答复后冻结。

## 测试层与夹具

- U：纯函数／服务单元测试，复用API的`node:test`、strict assert、Prisma／runtime stub和假时钟。
- D：临时独立PostgreSQL集成测试，验证唯一约束、事务锁、租约和迁移；不能用mock通过代替真实并发正确性。
- R：受控测试runtime的协议集成，验证条件写、执行幂等、内部限额、完整包和取消回执；不使用生产凭据。远端能力未实现时标BLOCKED，不能mock后记通过。
- W：现有Vitest/jsdom下skills候选页面／API契约测试；会话页不得增加操作控件。

拟增合成夹具目录：`apps/api/src/skill-emergence/__fixtures__/v2/`，包含显式消息ID、runId、事件顺序、假时间、来源、加载收据、预期task关系和完整小技能包。全部合成，不复制企业会话。

| 夹具 | 内容 |
| --- | --- |
| F01 改稿报表 | A技能第一稿→退款遗漏→第二稿→用户离开→稍后纠正；一task、多attempt |
| F02 多任务交错 | 甲报告、乙邮件、模糊“再改一下”、明确引用后续接 |
| F03 非任务与失败 | 自言自语、概念问答、内部creator、纯工具报错、有局部有效方法的失败 |
| F04 身份与作用域 | 企业E1用户A/B、企业E2；个人/组织同key；未审与已审包 |
| F05 文件版本 | SKILL.md＋引用＋脚本三文件；旧包、新草稿、人工改包、部分实例 |
| F06 资源回执 | 正常、多轮creator、repair、SDK重试、重复usage、超时未终止、窗口切换 |

测试中的阈值、额度、费用都是固定合成值，不得复用为生产默认预算。

## P0：采集、任务与自动结束

| ID | 输入／触发 | 预期断言 | 层／Spec |
| --- | --- | --- | --- |
| EVT01 | 同一个终态回调到达两次 | 一份事实，无重复task、频次、usage | U/D S03—04 |
| EVT02 | worker读revision1后收到revision2再完成 | 只确认1，2仍待处理，不丢迟到纠正 | D S04 |
| EVT03 | 准备／加载阶段失败，无助手消息 | Observation可写，technicalFailure；不伪造SUCCESS | U S03 |
| EVT04 | 同用户attempt发生两次技术stream重试，toolCallId重复 | run分开、task一次，工具证据不串运行 | U S03 |
| EVT05 | 产物只有session归属／URL被脱敏 | 不伪造run归属；受控对象ID先保存 | U S03 |
| EVT06 | 内部creator/repair产生完整对话 | 资源计账，学习源排除，不自我生成循环 | U S01/S03 |
| TR01 | F01多次修订，其中后续未选skill | 同task、多attempt，保留A使用关联 | U S05 |
| TR02 | “照甲的模板给乙另做一份” | 新task＋derivedFrom，频次2，不自动继承skill | U S05 |
| TR03 | 同一表中加入乙作为比较列 | 对象与目标明确时extends原task | U S05 |
| TR04 | F02模糊修改请求 | pending，0额外LLM；后续明确引用才归属 | U S05 |
| TR05 | 两worker同时首次关联同一request | 一个任务实例；冲突重读不重复创建 | D S04 |
| TR06 | 跨会话明确续接与同会话修订并发 | 同task连续revision，无重复或丢失；锁顺序不死锁 | D S04 |
| TR07 | 同动作但不同客户／期间／金额单位 | 不因粗签名误合成一次任务／一个条件 | U S05 |
| TR08 | 一消息包含两个目标，工具只明确属于其中一个 | 可分task；不把工具事实复制给另一task | U S05 |
| TR09 | 两次重写后引用第一稿；另有被纠正归属边 | 第一稿仍可关联重开；仅错误归属边不再命中 | U S04—05 |
| END01 | 纯文本最终交付、无artifact、无用户回复 | 稳定期后SEALED，正常有资格提炼；verification=UNKNOWN | U S06 |
| END02 | 只有澄清问句，用户离开 | 空闲封口且progress=awaiting_user/incomplete；无方法不生成，不能计成功 | U S06—07 |
| END03 | 失败但含可提炼局部方法／只有原始错误日志 | 前者正常资格判断，后者诊断；两者均不伪装成功 | U S06—07 |
| END04 | 原用户任务有真实活动tool/run，达到静默时间 | 暂不封口，不以静默强判终止 | U S06 |
| END10 | 原用户任务已本地断流，无活动工具，远端终态未知 | 宽限后封incomplete，可提炼现有材料一次；不重放业务执行、不宣称成功 | U S06 |
| END05 | 稳定截止时同时收到新纠正 | 锁内重读，不能封旧证据并漏新内容 | D S06 |
| END06 | 封口后用户修改原结果 | 重开原task，频次仍1，相关待审候选失效 | U/D S06/S08 |
| END07 | 服务重启／旧revision的due时间到达 | 从最新修订恢复；旧定时不重复封口／提炼 | D S06 |
| END08 | 只有心跳／租约更新时间变化 | 不推迟sealDueAt；不造成永久OPEN | U S06 |
| END09 | 仅封口／重开状态变化，材料事实未变 | materialEvidenceHash不变，不产生新的模型作业 | U S06/S08 |
| DLG01 | 模型提出单一续作问题，用户明确答复 | 提议与反馈关联，服务端验证引用后记标记 | U S06 |
| DLG02 | 模型自行输出userAccepted或verifiedSuccess | 不提升证据强度；模型无权制造用户验收 | U S06 |
| DLG03 | 多问题后用户说“好”／模型提议无回复 | 不强配接受；无回复仍自动封口和正常提炼 | U S06 |
| DLG04 | runtime无typed taskSignals | 终态／引用／静默fallback可工作，无额外请求、不泄漏机器JSON | U/R S06 |
| DLG05 | 升级会话入口 | 无新增任务按钮／反馈表单；只有原聊天交互 | W S01/S11 |

## P0：资格、增量与证据隔离

| ID | 输入／触发 | 预期断言 | 层／Spec |
| --- | --- | --- | --- |
| GATE01 | 高频闲聊／重复问答但无复用方法 | 高频不能绕过共同资格直接封装 | U S07 |
| GATE02 | 有具体过程的单次任务，结果未验证 | 正常进入原预算提炼，不要求用户说满意或最少N次 | U S07 |
| GATE03 | 未使用skill的合格轨迹 | NEW通道；无全库语义查找／自动更新未用skill | U S07 |
| GATE04 | 使用A且存在与A相关新规避方法 | 对应UPDATE；基准和来源明确 | U S07 |
| GATE05 | 使用A，合成夹具中规范化方法字段与已有条款完全相同 | SUPPORT，0封装，正式版本不变；不推及任意语义等价 | U S07 |
| GATE06 | 同时使用A/B但纠正目标不清 | 不广播更新，归因不明部分DEFER | U S07 |
| GATE07 | 规范化字段完全重复与条件字段明确不同两种夹具 | 前者去重；后者保留，不把模糊语义相似强判等价 | U S07 |
| GATE08 | 提炼模型返回SUPPORT／DEFER | 不强制生成空技能；记录原因 | U S08 |
| EVD01 | 数量不变但旧事实被纠正／删除 | evidence hash变，相关缓存／候选失效 | U/D S08 |
| EVD02 | 候选生成后共享／当前workflow变化 | 详情与封装仍引用冻结输入，不能偷换证据 | U S08/S11 |
| EVD03 | 字段经建模、normalize、canonical、creator | 条件／失败规避／证据强度均保留；输入输出契约映射正确 | U S08 |
| EVD04 | 同输入重新调度／被拒候选再调度 | 同hash不重生成、不重复展示；真新增证据可进入 | U/D S08 |
| SCOPE01 | 同企业A/B同任务族 | v2 Cluster分开；A输入不含B内容／标题／workflow | U/D S01/S04 |
| SCOPE02 | legacy共享workflow中含B私有标记 | A的v2提炼、详情和包均不含该标记 | U S04/S11 |
| SCOPE03 | A/B使用相同已发布组织skill | targetRef可相同，原始证据与候选仍各自隔离，不自动合批 | U S07/S10 |
| SCOPE04 | A身份访问B候选／跨企业同key | 拒绝，缓存和索引也不串scope | U/D S01/S04 |
| SCOPE05 | A提交组织但尚未审核／审核通过 | 前者B不可复用；后者只共享正式skill和允许说明，不共享原对话 | U/R S10 |

## P0：预算与生成

| ID | 输入／触发 | 预期断言 | 层／Spec |
| --- | --- | --- | --- |
| BUD01 | 剩一个槽位，两个worker竞争 | 只有一方在预留成功后真实发送 | D S09 |
| BUD02 | MODEL、NEW、UPDATE、REPAIR交错 | 消耗同份预算，不另开演化额度 | U/D/R S09 |
| BUD03 | creator内部第二轮超过calls或tokens／费用上限 | 发送前拒绝；仅完成后报警不算通过 | R S09 EXT01 |
| BUD04 | API超时但远端继续运行 | 预留不释放、同操作不重复发送；后续对账 | U/R S09 |
| BUD05 | 已确认取消，但已有部分消耗 | 结算已用、仅释放未用，不把实际usage清零 | U/R S09 |
| BUD06 | 人工重试重置attemptCount | 已用及未结算预算不清零 | U S09 |
| BUD07 | 重复usage／旧lease回执 | callId只结算一次；真实usage不丢，旧worker不能改新作业状态 | D/R S09 |
| BUD08 | 窗口切换／额度降低／旧调用仍运行 | 旧预留与债务保留，不因新窗口重置而丢账 | D S09 |
| BUD09 | 缺usage／只有BillingTask hold或主账单 | 标unknown／不完整，不计0，不拿预扣当实际 | U S09 |
| BUD10 | SDK／stream retry／repair | 所有实际请求都受限并计账，无隐含免费重试 | R S09 |
| BUD11 | trace／索引／去噪／路由完整处理 | 直接模型调用次数严格0 | U S01/S05 |
| BUD12 | 预算不足／配置缺失 | 留证待处理并说明，不标生成成功、不静默删材料 | U S09 |
| BUD13 | 缓存命中；随后base／evidence／model变化 | 命中不发送；必要变化失效后仍先预算检查 | U S08—09 |
| PKG01 | 生成UPDATE并做市场信息修复 | 正式包字节、版本、可见性不变 | U/R S10 EXT02 |
| PKG02 | 完整包缺脚本、越界路径、重复路径、引用不存在 | 校验拒绝；SKILL.md单文件hash不能冒充完整包 | U S10 |
| PKG03 | UPDATE仅改目标条款 | 未相关步骤及辅助文件完整保留，差异可解释 | U S10 |
| PKG04 | 草稿校验后内容变化 | validationHash失效，接受前需重验 | U S08/S10 |

## P0：发布、组织、加载和兼容

| ID | 输入／触发 | 预期断言 | 层／Spec |
| --- | --- | --- | --- |
| PUB01 | 拒绝／删除失败UPDATE | 不调用正式包hide/delete/update | U S10 |
| PUB02 | 双击接受／接受与拒绝并发 | 同操作一次；一个转换胜出，失败方无正式副作用 | D/R S10 |
| PUB03 | 两UPDATE同基准／人工编辑插入读写间 | 原子CAS一个成功或冲突；不覆盖更新版本 | R S10 EXT03 |
| PUB04 | 多实例部分成功、写包成功后DB失败 | 保存／恢复回执，不重复增版本，不宣告全量成功 | R S10 |
| PUB05 | 网络超时实际已写成功 | 先按operationId对账，重试返回原结果 | R S10 |
| PUB06 | 已发布UPDATE撤销 | 走版本恢复，整个skill仍可用 | U/R S10 |
| PUB07 | 远端发送前新增否定证据／权限撤回 | 拒绝STALE／无权，不发送正式写入 | U/D S10 |
| PUB08 | 远端发送后才到否定证据 | 记录evidenceChangedDuringPublish及实际结果，进入修订，不伪报能原子阻断在途写 | U/R S10 |
| PUB09 | NEW同key已存在／两NEW并发创建同key | expectedAbsent原子拒绝冲突，既有包不被覆盖 | R S10 EXT03 |
| ORG01 | prepare-submit后个人正式包被修改 | 提交仍绑定候选snapshot/hash或冲突，不偷换包 | U/R S10—11 |
| ORG02 | 普通成员更新他人组织key | 走提交建议／有权维护者审核，不借NEW覆盖 | U S10 |
| ORG03 | 客户端mark-submitted但实际提交失败 | 不标SUBMITTED；重试关联同一真实submission | U S11 |
| ORG04 | 审核期间目标版本变化 | 审核发布再次CAS，不覆盖较新版本 | R S10 |
| LOAD01 | 个人／组织同key | requested与resolved分别记录；实际owner/version可追溯 | U/R S02/S03 |
| LOAD02 | 选中但加载失败／正文和脚本版本不一致 | 不生成虚假的使用成功或完整版本归因 | R S03/S10 EXT04 |
| LOAD03 | 远端无法返回版本 | attributionIncomplete，不凭key补造版本 | U/R S03 |
| COMP01 | legacy Snapshot与task_revision混读 | kind严格隔离；旧upsert不覆盖任务修订 | U/D S04 |
| COMP02 | 旧候选无action/base/hash | 保留legacy NEW语义，不猜成UPDATE；不能复用跨用户旧workflow | U S04/S11 |
| COMP03 | 90天清理／用户删除原消息／待运行作业仍存在 | 清理符合留存；证据失效可见，不误级联删操作账或继续学习已删原文 | D S04 |
| COMP04 | 开关关闭／重启／新旧processor竞争 | 同源不双执行；在用技能可用，待处理可恢复 | D PLAN P6 |
| CFG01 | 自动采纳配置开启 | 按D05冻结NEW／UPDATE预期；不能绕过权限与CAS | U/W S10 |
| UI01 | 列表／详情／批量采纳混合NEW/UPDATE/冲突 | action、验证和发布状态分开，逐项结果；无新增会话操作 | W S11 |

## 现有回归与命令

源码可确认API使用node:test/tsx，Web使用Vitest。API build排除test文件，build通过不能替代测试。以下从任意目录使用绝对工作路径；命令静态核实，依赖可用性尚未执行验证。

```powershell
pnpm -C "D:/skillsgen-industry_track/enginering/insightweaver/apps/api" exec tsx --test src/skill-analytics/skill-emergence-recorder.service.test.ts src/skill-analytics/skill-emergence-processor.service.test.ts src/skill-emergence/skill-emergence-gate.test.ts src/skill-emergence/skill-emergence-packaging.service.test.ts src/skill-emergence/skill-emergence-evaluator.delete.test.ts src/skill-emergence/skill-emergence-scheduler.test.ts src/skill-emergence/skill-emergence-state-machine.test.ts src/skill-emergence/skill-emergence-quality.util.test.ts
pnpm -C "D:/skillsgen-industry_track/enginering/insightweaver/apps/api" exec tsx --test src/skills/skill-submission-version.util.test.ts src/skills/skill-zip.util.test.ts src/skills/skill-market-personal-scope.market.test.ts src/zclaw/zclaw-hidden-orchestration-skill-injection.test.ts
pnpm -C "D:/skillsgen-industry_track/enginering/insightweaver/apps/web" exec vitest run src/lib/__tests__/enterprise-skill-picker.test.ts src/lib/__tests__/skill-market-md.test.ts src/components/super-lobster/__tests__/skill-market-display.test.ts
pnpm -C "D:/skillsgen-industry_track/enginering/insightweaver" --filter @insightweaver/api build
```

新建trace、budget、publish、scope等测试后把明确文件名加入命令，不能假定原命令覆盖新行为。需要Prisma client更新时在开发隔离环境执行，`db:migrate`会写数据库，本轮不运行。

需有意修正的旧测试：`skill-emergence-evaluator.delete.test.ts`目前要求删除FAILED隐藏同key个人skill，必须分NEW／UPDATE改断言；原packaging测试要求生成后正式安装／隐藏的部分随隔离草稿契约更新。现有scheduler mock竞争与技能注入mock不证明真实DB并发或实际版本加载。

## 完成记录模板

执行时逐项记录：ID、实现文件、层级、命令／环境、PASS/FAIL/BLOCKED、失败证据、外部依赖。P0 BLOCKED不能算PASS；只检查了代码的项标STATIC_REVIEW。测试证明契约行为，不证明真实任务收益、零误判或论文创新成立。
