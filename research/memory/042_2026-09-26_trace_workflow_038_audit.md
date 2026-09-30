# 042 轨迹恢复与学习聚合对038案例的审阅

## 本轮问题及用户要求

用户要求审阅独立Demo现有第3阶段轨迹恢复和第4阶段学习决策与聚合，判断能否在038真实合同案例得到理想输出。依据项目科研模式，本轮只做源码核查、隔离本地推演和Markdown沉淀；没有授权算法代码修改或新模型调用。

## 证据与产物

- [详细审阅报告](../reports/042_trace_recovery_and_workflow_review_038.md)逐项对照[040十二阶段契约](../reports/040_twelve_stage_contract_and_task_detection.md)与[038案例](../reports/038_contract_multi_review_case_preparation.md)。
- 在041验收数据库的SQLite备份上实际执行当前`Loop.discover('alice')`，保留[无正文推演摘要](../../enginering/demo/artifacts/038-stage34-review-20260926/stage34-summary.json)；原库未改，临时备份已删除，未发模型请求。
- 实际输出：4项任务均`NEW/METHOD_MATERIAL`，生成4个单来源候选/池。T1/T2当前识别目标词相似度0.1768，低于0.72聚合阈值。4项`evidence().outcome`均UNKNOWN，0真实产物、0客观检查。价格问答的用户文本`method_signal=false`、助手文本`true`，故被错误放入NEW候选。

## 证据支持的观察

- **第3阶段仅完成基础拼接。** 14条用户消息的任务归属正确，但原56条助手消息被压成14个合并文本，trace没有原助手消息ID、attempt、反馈指向、要求时间线或历史文件回执。T3许可子问题在第2阶段为`SUBGOAL_HINT`，拼接后压成`CONTINUE`；T1/T2各类修订同样只剩`CONTINUE`。存储`revision`不是用户要求版本。
- **结果UNKNOWN是正确保守状态。** 原合同与历史交付文件缺失，`COMPLETED/SEALED`不能证明法律审查成功。当前`evidence()`依赖`CORRECT`或客观check来识别失败，但真实识别拼接只给`REQUEST/CONTINUE`，因此不能据现有输入可靠启动失败处理器。
- **第4阶段NEW/UPDATE主路由方向正确，价值与聚合不足。** 用户确认历史无skills，因此不是UPDATE；但`method_signal`扫描助手文字导致价格问答通过门槛，词面complete-link无法合并条件相似的T1/T2。当前pool只是轨迹集合，没有明示方法步骤、角色变量、适用/禁用条件，不符合040的workflow输出契约。

## 判断、建议与未知

判断：当前实现**不能**自动得到038理想的第3/4阶段输出。T1/T2同一“立场参数化重大风险审查”方法族只能作为待核假设；若共同方法过于空泛，应保留分开或延期，不能强制合并。T3是较晚留出，隔离审阅可看其边界，但生成时不得读取其历史回答。建议先补源事件与反馈/要求/产物边，再做选择性学习和带条件的方法族归纳，价格问答无方法证据应DEFER。以上为建议，未实施、未证明减少无效skills或成本不增加；合同正文与客观参考仍缺。
