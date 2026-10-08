# 第292轮：RecreationBench 工作上下文恢复与终态进度核对

日期：2026-10-05（北京时间）。用户原 RecreationBench 会话无法恢复，要求读取研究记忆、恢复工作并核对进度。

## 用户已确认要求与本轮范围

- 本轮恢复研究上下文、核对现有证据、形成接续入口。没有自动重启实验、模型调用、技能学习或评测，没有改执行代码/配置。
- 持续有效：独立 26 应用 pilot 为后续 skills 建库提供素材；每 canonical 应用家族至多三轮含首轮、成功即停，版本/设施恢复不得重置额度。旧 corravale STOP 保持；其他聊天独立。
- 50 应用扩容只是未确认建议；AutoSkill 学习和 250 正式评测未由本轮请求启动。

## 证据支持的观察与更正

先读研究 README、CHARTER、STATE，再按 RW 索引读取 283/284/285/286/290 等相关记忆，并核对 280 来源池、283 方案及 285/288 实际产物。形成 [恢复报告](../reports/292_recreationbench_recovery_status.md)，保存路线沿革、当前证据、硬约束及待办。

1. 来源取得已完成：27 固定来源（26 主候选 + MacPass 候补），主候选 Ubuntu7/Windows5/macOS3/Android6/Web5。它们是自建独立来源，不是已取得的官方 35,000 训练轨迹。
2. 当前实际准入 2/26（7.69%），均为 Web：miniPaint 三轮、Squoosh 一轮实际 agent 执行已结束；其余 24 尚待参考/构建/独立验证器及平台准入。四次执行不是四个独立应用，也不表示四份完整素材最终验收通过。
3. miniPaint 第三轮最终 0.4228，功能4/6、SSIM0.179，未达既定训练成功条件，3/3 耗尽，不能第四轮。第一轮0.3394；第二轮原评分 OOM，恢复评分最终0.1带 read_answer_leak，原 test_score0.4228及全部异常保留，不挑分覆盖。
4. **更正 [记忆290](290_2026-10-05_rw_parallel_evolution_collection.md) 的“首轮继续”截面：Squoosh 已于 2026-10-05 01:07:12 结束。** `parallel_health_state.json`、`active/squoosh.json`、launcher终态和实际 nested scores 一致：原生退出0、final0.5246、功能1/6、SSIM0.8826，未满足全部六项必要功能通过。没有第二轮已启动的落盘证据；预算1/3。
5. `observer_completion.json` 记录 both_workers_finished=true、no_new_model_round_started=true，proxy cleanup returncode=1。全轨迹最终验收仍 pending audit；不把 agent 正常结束、流水线 passed 或未自动开新轮等同于应用成功/全部服务清理。
6. 本轮实际复算Squoosh copy_manifest的主session11,227,903bytes和四个tool-result文件、miniPaint第三轮主session19,984,024bytes，大小/SHA全部与源/复制manifest一致，size_cap=null。Squoosh本轮trajectory864行/11,496,515bytes/0坏JSON，candidate output/index.html已落盘；这是归档和原生记录证据，不能替代事件/图像消费与原创性最终审计。轮次继承历史必须去重。
7. OOM 历史、2GiB→3GiB外部资源变化、重叠窗口共享proxy导致route混合全保留。不能把 Squoosh route 的457请求全归给该应用，也不宣称2倍吞吐或任何skills收益。v2.7独立端口仅准备未激活。
8. 外层 metrics 的 task_score/program_score=0与实际nested score不同，passed=true表示流水线完成，不表示训练成功；继续依据实际 `recreation/eval_results/scores.json`，不热改或覆盖原文件。
9. 当前只读运行核验：WSL boot与旧记录一致；两个controller、Squoosh actor和外部observer原PID均不存在；两容器exited/Pid0/ExitCode0，miniPaint OOMKilled=false/2GiB、Squoosh OOMKilled=true/实际3GiB。8788/8791/8792/8793无监听；285/288 relay仍在但不是actor。观察器曾有临时ledger FileNotFoundError、后续快照恢复；原cleanup rc1保留，不推断任务仍运行。本轮核验不等同于启动/恢复服务。

范围：以上是本批两应用及已存报告的恢复核对，不是五平台整体能力、生产事实或新因果实验。250 正式评测与 RW skills 学习仍未启动，成功验收0；canonical及学习视图最终验收尚未闭合。

## 研究假设与工作建议

跨应用真实探索、失败修正和验证经验可能生成可复用 skills，这是待验证假设。此实验关联企业闭环的经验学习/使用后演化/复用，不覆盖自然企业多轮会话、采纳与组织共享，也不预设贡献成立。

先验收现有两应用 raw→canonical→机械学习视图、图像consumer、反馈/候选hash与父轮去重。miniPaint封存，Squoosh若接续则先反馈/checkpoint及独立新freeze准入再开始第二轮，最多余两轮；本轮未执行。推进其余等价参考准入；正式建库另定输入粒度、成败标签与截断策略，不能套用另一聊天tau决定。最终评测须处理旧corravale暴露与来源家族隔离，不直接称250全未见held-out。

## 未知项

可用的 canonical 完整链数量、图像实际消费覆盖、原创性最终验收、失败功能与 OOM 的具体影响、按原生事件归属后的每路成本、其余平台宿主准入、学习产量/正确性、迁移收益与充分规模均未确定。旧5+245方案保留为历史，当前26独立采集已实际执行；来源获取/采集授权不自动将245正式评测重划为250，新评测合同未冻结。

## 关键产物与下一步

- [完整恢复报告](../reports/292_recreationbench_recovery_status.md)。
- [最终健康快照](../experiments/288_rw_parallel_evolution_collection/reports/parallel_health_state.json)、[观察器完成记录](../experiments/288_rw_parallel_evolution_collection/reports/observer_completion.json)。
- [Squoosh实际评分](../experiments/288_rw_parallel_evolution_collection/runs/squoosh_recreation_eval_1791129536850164583/recreation/eval_results/scores.json)、[原始复制manifest](../experiments/288_rw_parallel_evolution_collection/runs/squoosh_recreation_eval_1791129536850164583/private_raw_sessions/copy_manifest.json)。

本轮新增证据为290之后已落盘的 Squoosh 终态和双worker收尾，未产生新增模型/实验结果。接续从现有素材验收开始，保留全部历史、负结果、STOP和轮次预算。
