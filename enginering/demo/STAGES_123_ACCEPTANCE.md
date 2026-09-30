# 047 前三阶段实现与验收

日期：2026-09-26。用户明确授权 Demo 代码修改和前三阶段逐阶段端到端验收。依据046新版契约；没有接入企业生产系统，没有生成、采纳或发布技能。

## 最终结果

| 阶段 | 实际输入 | 验收输出 | 结果 |
| --- | --- | --- | --- |
| 1 会话采集／问答整理 | 038原始70消息＋源索引 | 14问答；14个用户ID、56个助手ID全部保留 | 通过 |
| 2 逐对任务识别 | 14个完整user/assistant问答，无人工任务标签或replyTo | 14个候选标注；三会话分别1、1、2个任务 | 通过 |
| 3 轨迹恢复 | 原问答＋阶段2候选 | 4条TaskTrace；成员数4／4／5／1，要求、尝试、反馈、声称及未知项分列 | 通过（允许显式未决） |
| 独立构造控制 | 4轮A→B→A，最后一轮同时新任务C和返回B | 3任务；成员位置[1,3]、[2,4]、[4]，识别RETURN并拆分双目标 | 通过；不是自然企业交错样本 |

软件测试 **56/56通过**（改动前39，新增17），HTTP接口烟测通过，前端JS语法检查通过。浏览器实看8768页面：三会话均为PREPARED→ANNOTATED→RECOVERED，14问答、14标注、4轨迹。HTTP烟测使用固定模型夹具；真实语义结论来自下面单独的真实模型记录。

## 可回查证据

- [最终验收JSON](../../research/cases/038_contract_multi_review/private/047-stages123-network/acceptance-summary.json)：15项检查全部通过。
- [受控案例逐步展示](../../research/cases/038_contract_multi_review/private/047-stages123-network/047_case_walkthrough.md)：每个问答输入、候选标注、任务要求、反馈、实际引用、未知项；包含企业正文，只在private中保存。
- [完整私有快照](../../research/cases/038_contract_multi_review/private/047-stages123-network/private-snapshots.json)及同目录loop.sqlite：原事件、问答、模型请求／输出、校验结果与版本历史。
- [首轮结果](../../research/cases/038_contract_multi_review/private/047-stages123-network/acceptance-summary-initial.json)；[选项证据门禁前结果](../../research/cases/038_contract_multi_review/private/047-stages123-network/acceptance-summary-before-option-guard.json)。失败不删除。
- 隔离验收台：[http://127.0.0.1:8768/](http://127.0.0.1:8768/)，「任务轨迹」查看；Alice是真实案例，Bob是构造控制。学习预算为0、自动学习关闭，防止查看验收时额外付费。现有8767实例未被终止。

## A会话实际恢复了什么

四轮保持一个任务，形成4个回合attempt，未把33条助手进度膨胀成33次独立尝试：

1. 初始版本直接保存首轮用户要求，不把后续要求倒写进去。
2. 对先前建议的商业合理性追问，恢复为ASK_ABOUT_PRIOR_ADVICE，不自动认定任务失败。
3. 用户选取建议方向恢复为SELECT_OPTION；选择方向并不证明助手实现了具体选项，记OPTION_REALIZATION_UNVERIFIED。
4. 不再输出文件、只给条款文本，恢复为CHANGE_OUTPUT，作用范围CURRENT_DELIVERY；不是永久偏好或业务验收。

可见文本、文件声称、局部失败声称和修复声称分别保留。没有真实工具回执／历史文件，就不升级为独立执行事实。四条任务业务结果均UNKNOWN，可核验历史交付文件数为0。

**选项边界必须如实解释**：模型没有明确提取“或→且”的具体组合冲突；程序对所有SELECT_OPTION统一保留未核验的实现关系。这通过的是“不把缺失证据当作正确实现”的完成边界，不能宣称已经实现高精度的逻辑冲突检测。

## 负结果与资源账

- 最初4次派发在沙箱内被WinError 10013拦截，见private/047-stages123-live。无模型输出与usage，不能记成成功请求或把未知费用记0。
- 网络获准后首轮8次请求全部有模型响应，但A/B的恢复输出把省略号摘要当逐字引文，宿主拒绝；C与构造控制完成。HTTP成功不等于语义验收成功。
- 修复采用**程序生成细粒度原文span，模型选择span ID，程序回取原文与位置**；保留用户/助手来源和MESSAGE_SPAN/PAIR_SPAN精度，不用模糊字符串匹配补造引文。恢复提示与输入改变后，明确补跑4次恢复，阶段2复用缓存。
- 补跑后15项中有1项选项未决检查失败；增加通用的“选择不等于执行已核验”门禁，用已存结果重新编译，未追加LLM请求。
- 总计有响应的真实模型请求 **12次**（企业9、构造3），报告 **131,659 tokens**；企业113,959、构造17,700。现金费用未提供，保持未知。最终有效链依赖8个请求，85,541 tokens；这不是一次独立全新运行，不隐去此前修复消耗。
- 最后以每日预算0重放，15项全部通过，总调用仍12。未变化输入不重复调用。

相对旧规则链路，语义识别和恢复增加了模型工作；本次没有证明长期总成本不增加、无效skills减少或企业收益。

## 已完成修改与剩余边界

新增intake、pair_detection、recovery、front_stages四个模块；接通core/runtime/server、页面、原事件导入和导出。继续使用records/events/runs三张表。模型用既有OpenClawAgent配置的qwen3.7-plus；结构化抽取经单请求模型接口，不把它描述成OpenClaw工具执行证据。

独立审查修复了迟到runId关联、双目标整答重复归属、导入与在线会话混用、缺正文显式补齐、初始要求泄漏、重复文本定位、提示更新缓存、区间重叠判断等问题。代码基线保存在artifacts/047-baseline-source，未初始化或伪造Git提交。

当前是**有界完整session快照**，支持session内部交错，尚未实现新schema跨窗口增量和跨session关联。超预算明确延期；模型语义仍需独立数据评估。

阶段4尚未适配新版TaskTrace，设置明确交接状态并阻止旧discover直接消费。旧回放闭环保留。本次结论是前三阶段工程验收通过，不能替代完整12阶段、新技能价值或论文效果实验。

操作命令与字段见[实现契约](STAGES_123_SPEC.md)。
