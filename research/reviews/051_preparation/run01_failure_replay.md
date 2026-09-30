# Run 01：保存响应的拒绝路径重放

日期：2026-09-26。此项为零网络的宿主处理重放，**技能生成验收结果仍是 FAILED**。

原实验输入为索引选出的 A/B 两会话、48 条原始事件。原 run 01 在第二个 session 的任务识别输出引用校验处被拒绝；远端已经完成的三个响应和一条已恢复轨迹均保留。此次把三个保存响应按 `purpose + digest(request)` 精确回放到一个全新数据库，由同一应用代码重新完成阶段 1、处理阶段 2/3，并在同一处停止。

| 比较项 | 结果 |
| --- | --- |
| 保存响应消费 | 3/3，逐项精确匹配 |
| 新模型推理／网络连接尝试 | 0／0 |
| sourceHash 或原响应文本改写 | 无 |
| 原／重放验收状态 | FAILED／FAILED |
| 原／重放停止阶段 | 2/3／2/3 |
| 顶层 error、各 session 状态与 error | 一致 |
| 阶段 1 来源、阶段 2 已接受标注、阶段 3 已恢复轨迹 | 规范化 hash 一致 |
| 阶段 4/5 产物 | 两边均为空；没有把拒绝路径当作技能生成成功 |

这些证据说明：**对这三个保存响应，引用校验的拒绝和此前完成的处理可确定性重现**。它排除了本次重放中的网络可达性、远端模型波动或隐藏旧数据库作为停止原因；不证明所有新模型调用都会成功，也不证明所有拒绝都源自模型。

- 原实验：[私有验收摘要](../../cases/038_contract_multi_review/private/051-first5-run01/acceptance-summary.json)。
- 重放：[私有逐项比较](../../cases/038_contract_multi_review/private/051-run01-failure-replay/failure-replay-comparison.json)。
- 脚本：[replay_failed_responses.py](replay_failed_responses.py)。

原始和重放的企业正文、模型响应均保留在各自 `private/` 目录。未修改冻结应用代码、提示词、原始响应、原实验数据库，未采纳或发布任何技能。
