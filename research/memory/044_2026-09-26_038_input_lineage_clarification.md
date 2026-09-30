# 044 038案例初始输入与041预分组语义澄清

## 本轮问题及用户要求

用户要求明确说明：038真实案例最开始输入哪个文件、具体如何输入、各字段和预处理的语义。承接043第3阶段设计与040固定契约，本轮只核对数据血缘和表述，未授权算法代码实现。

## 证据与产物

- [044输入血缘说明](../reports/044_038_input_lineage_and_semantics.md)逐文件、逐代码步骤解释原导出→038子集→预整理回合→041 Demo→第2阶段模型输入。
- [原始导出README](C:/Users/39835/Downloads/zkys-raw-export-20260925/README.md)、[038准备脚本](../cases/038_contract_multi_review/prepare_case.py)、[041验收脚本](../../enginering/demo/scripts/check_038_task_detection.py)、[Demo导入/模型视图源码](../../enginering/demo/skilldemo/core.py)为依据；本地仅输出私有JSON键与类型，未复制企业正文或凭据。
- 对[041报告](../reports/041_task_detection_implementation_and_038_validation.md)追加显式更正，并在[043设计](../reports/043_trace_recovery_stage3_implementation_design.md)改准“人工恢复”的措辞；保留历史结论，不静默抹除。

## 观察、解释及更正

- **证据观察：** 原企业消息源是旧包`zclaw_messages.jsonl`；038复制3会话70原行到`private/raw_messages.jsonl`，另以新包`user_messages.json`给14条用户消息按原ID补UTC时间。旧包AI时间不可用，附件二进制及全量工具结果缺失。
- **关键更正：** `recovered_trajectories.json`的用户—连续AI分组由`prepare_case.py`按原导出行序**确定性预计算**，不是研究者逐条手工配对；但其中`task`和`split`是案例标注。041的`source_turns()`读取该预分组来构造14条Demo turn，丢失56个AI原ID。阶段2模型只收到去敏用户文本，**没有**收到任务标签或AI正文；所以没有任务标签泄漏证据，却也没有第3阶段自动恢复证据。
- **语义区分：** 原`status=done`及导入`COMPLETED`只表示技术状态；`sourceLine`只表示本案例原文件局部行序；`rawPayload.files`只是附件元数据；缺文件与无用户验收时`businessOutcome=UNKNOWN`。
- **未知：** 第3阶段从消息级70事件自行恢复分组、尝试与反馈边的质量尚未运行验证；本轮无新增模型实证。

## 决策与下一步

043设计的第3阶段验收保持原始70事件输入，人工案例文件只用于比较；041任务识别的4任务/14用户归属结论在其既有预处理条件下保留。若后续实现第3阶段，应输出原56条AI消息ID的覆盖和每条边的来源依据，再判断有无轨迹恢复收益。章程与040责任契约不变。
