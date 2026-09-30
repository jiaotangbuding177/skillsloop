# Run 03 状态勘误：失败优先于预算部分完成

日期：2026-09-26。

Run 03 的正确实验结论为 **FAILED**。其冻结的 `acceptance-summary.json` 原本已正确记录 FAILED；研究侧混合驱动器另写的 `mixed-experiment-summary.json` 将它误分类为 PARTIAL，并错误标记 `budgetStopped: true`。这份勘误保留原文件、脚本、manifest 和数据库，不覆盖历史记录。

证据为三个候选的真实状态：**1 READY、1 FAILED、1 QUEUED**。第二个 creator 已完成远端执行，但最终回复含前言和唯一 JSON 围栏，旧宿主解析器在封装前拒绝该文本。后续第三个候选尚未派发。因此阶段 5 的直接停止原因是输出解析失败，不能用已用完四次新派发额度解释或掩盖该失败。

混合驱动器原判断只检查“阶段 5、四次新派发、仍有 QUEUED、已有交付”，没有先排除 FAILED／GENERATING／未知状态。后续状态判断应遵循：

1. 只要存在 FAILED、执行状态未知或确定的验证错误，整轮结论先记 FAILED。
2. 只有所有已尝试候选均 READY，剩余候选均 QUEUED，且实际停止原因为额度拒绝，才允许记预算 PARTIAL。
3. 只有所有批准候选均通过校验并交付，才记 PASSED。

已准备的“2 READY＋1 QUEUED，仅补第三个 creator”阶段 5 续接脚本对此状态必须拒绝，不能直接用于 Run 03。新的处理应另开运行：保留八条原 agent 响应与两份原草稿，在修正的严格解析器下重新运行宿主处理，只给从未执行的第三个 creator 一次新增派发。该运行必须明确标注保存响应复用及解析器改版，不能称为五阶段全部重新调用模型的独立成功实验。

- 原宿主结论：[acceptance-summary.json](../../cases/038_contract_multi_review/private/051-first5-run03/acceptance-summary.json)。
- 被更正的混合摘要：[mixed-experiment-summary.json](../../cases/038_contract_multi_review/private/051-first5-run03/mixed-experiment-summary.json)。
- 原候选状态：[stage-5.json](../../cases/038_contract_multi_review/private/051-first5-run03/stage-5.json)。
- 新运行入口：[run_saved_responses_one_creator.py](run_saved_responses_one_creator.py)。

本项为状态核对和独立勘误；没有付费调用，没有修改 Run 03 的任何既有字节。
