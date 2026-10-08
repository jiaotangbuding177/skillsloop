# RecreationBench 工作恢复与进度核对

日期：2026-10-05（北京时间）。本轮按研究入口、章程、当前状态、相关轮次记忆及实际落盘产物恢复上下文。范围是研究接续与只读核对；没有启动模型、采集、学习或评分，没有修改实验执行代码和配置。以下是已恢复的工作背景和可继续使用的检查点，不表示原聊天界面已恢复。

## 1. 现在正在做什么

当前 RW 主线是：**独立开源 GUI 应用 → 观察参考并自主复刻 → 保存最多三轮真实纠错轨迹 → 后续构建 skills 库 → 验证跨应用复用**。

这项工作为企业 skills 闭环中的“从执行经验生成技能、使用后演化、跨任务复用”提供受控实验素材。RecreationWorld 的 agent 与工具交互不是企业用户自然多轮会话，本批也没有验证个人采纳、组织审核、跨成员共享或真实企业部署。

当前采集使用自己的独立训练来源，不是作者的官方 train split。来源目标 26 个应用家族：Ubuntu 7、Windows 5、macOS 3、Android 6、Web 5；另有 MacPass 条件候补，不计入主集合。26 是首批 pilot，最终充分规模尚未证明；50 应用扩容只是建议，未确认或执行。

有效运行目录是 [288 并发采集](../experiments/288_rw_parallel_evolution_collection/)，首轮及历史证据保存在 [285 首轮采集](../experiments/285_rw_evolution_collection/)。旧 corravale 实验保持 STOP。

采集使用固定官方 RecreationWorld vendor `b5cda868f44932dc84ea68e3b3053bc418621aa3` 和原生 Claude Code harness，必要桥接/资源修复另记版本。模型请求别名 `deepseek-v4-flash-vision-exp`，返回别名 `deepseek-v4.1-flash`；物理 checkpoint 未知，不将别名当作已核实身份。

## 2. 已完成的准备和实际进度

| 工作 | 已有证据和当前状态 |
|---|---|
| 评测任务登记 | 250 个公开 task ID 已逐项核对，五平台各 50；未完成正式评测 |
| 独立来源取得 | 27 个固定版本源码来源已归档，26 主候选 + 1 候补；约 296.90 MiB、26,742 文件 |
| 采集方案与输入审计 | 283 方案已保存，明确完整事件、图像、父轮、产物、真实反馈和学习视图合同 |
| 实际参考准入 | miniPaint、Squoosh 两个 Web 应用，2/26（7.69%）；其余 24 待准入 |
| 实际 agent 执行 | miniPaint 三轮 + Squoosh 首轮，共四次实际执行已结束；评分异常和恢复单列 |
| 达到训练成功条件 | 当前两应用均未达到；成功验收 0 |
| 完整素材最终验收 | 原始记录已落盘；canonical 链、去重、实际可消费输入和完整原创性审计仍待验收 |
| RW skills 学习 | 未启动，尚无本批已学习并验收的技能库 |
| RecreationBench 250 题评测 | 未启动，无本批 skills 迁移收益结果 |

“2/26”是已准入并进入采集的应用比例，不能当作完成或成功比例。四次执行也不是四个独立应用。

### miniPaint：已用完三轮，必须保留失败并停止

| 轮次 | 功能 | 视觉 SSIM | 官方最终结果 | 说明 |
|---|---:|---:|---:|---|
| 1 | 3/6 | 0.1789 | 0.3394 | 原生正常结束，首轮在 285 目录 |
| 2 | 4/6（仅评分恢复） | 0.179 | 0.1 | agent 已实际交付；原评分 OOM；恢复评分触发 `read_answer_leak`，未封顶的 test_score 0.4228 不能替代官方最终分 |
| 3 | 4/6 | 0.179 | 0.4228 | 原生自然结束，未达成功条件，额度 3/3 耗尽 |

当前接受条件包括全部六项必要功能通过、视觉 >= 0.85、合法构建交付及最终原创性审计。miniPaint 未满足。不能跑第四轮、以版本变更重置次数、选择最高分轮改称成功。

三轮原始 session 均已保存，历史核验记录的大小分别约 11.60 MB、16.45 MB、19.98 MB。后两轮继承前轮历史，后续学习必须按父链去重，不能把重复历史计作新独立素材。第二轮原始评分 OOM、两个评分 adapter 结果及路径标记都保留。

关键来源：[记忆290](../memory/290_2026-10-05_rw_parallel_evolution_collection.md)、[第三轮原始评分](../experiments/288_rw_parallel_evolution_collection/runs/minipaint_recreation_eval_1791129685783416430/recreation/eval_results/scores.json)。

### Squoosh：首轮已经结束，纠正旧“仍在运行”截面

首轮 `squoosh_recreation_eval_1791129536850164583` 于 **2026-10-05 01:07:12（北京时间）**结束，原生退出码 0。实际嵌套评分：

- 功能 1/6，失败 5 项。
- 视觉 SSIM 0.8826。
- 最终分 0.5246，未达到全部六项功能通过的成功条件。
- `full_trajectory_acceptance` 仍为 `pending audit`，不能将正常退出或界面相似解释为成功素材已验收。

原始记录保留浏览器 MEMCG OOM 历史；同 actor 执行中外部资源修复由 2 GiB 增至 3 GiB。终态健康快照仍有 `OOMKilled=true`，不能称全程无故障或执行资源未变。视觉较高而功能低是本样本的观察，是否支持可迁移技能仍未知。

旧记忆290和 `current_phase_v261_manifest.json` 当时记为首轮运行中；更晚的 [最终健康快照](../experiments/288_rw_parallel_evolution_collection/reports/parallel_health_state.json)、[原始评分](../experiments/288_rw_parallel_evolution_collection/runs/squoosh_recreation_eval_1791129536850164583/recreation/eval_results/scores.json)、[观察器收尾](../experiments/288_rw_parallel_evolution_collection/reports/observer_completion.json) 已显示两路结束。本次更正保留旧记录。

外层 `metrics.json` 有 task_score/program_score=0、passed=true、score_passed=false，与嵌套评分不是同一含义。沿既有 285 核对规则使用实际 `recreation/eval_results/scores.json`，不把流水线 `passed` 当任务成功。尚无 Squoosh 第二轮已启动的证据，现有预算是 1/3。

本轮还实际复算 Squoosh 主session 11,227,903 bytes及四个tool-result文件、miniPaint第三轮主session 19,984,024 bytes的大小/SHA，全部与原复制manifest一致；Squoosh未发生64MiB归档跳过。其本轮原生trajectory为864行、11,496,515 bytes、无坏JSON，candidate构建产物已落盘。原生result正常表示执行结束，不能代替功能成功或完整输入验收；miniPaint本轮stream与含前轮历史的raw session也应分别处理。

当前只读运行核验：WSL boot与旧记录相同，两个controller、Squoosh原生actor及外部observer PID均已不存在；两容器均exited、Pid0、ExitCode0。8788/8791/8792/8793均无监听，现未见这些代理端口残留；285与288的relay服务仍在，它们不是agent worker。无需恢复旧监控脚本才能读取已完成产物。

## 3. 已确定的实验约束与历史路线

用户已确认：每 canonical 应用家族最多三轮含首轮、成功即停；未达标准就是未达。版本、端口、平台路径或设施恢复不重置轮数。不同应用不互传旧代码和增量 skills。本次采集为后续建库提供素材，不自动开始 AutoSkill 学习或 250 题评测；其他聊天实验独立。

历史路线依次是：216 接入评估 → 220 独立管道与 Web canary → 237 首次“完整能力基线”结论被传输失败证据纠正 → 238 视觉模型切换 → 241 corravale 过度迭代后用户停止 → 270 Web 两折建议 → 272 五平台各一题演化/245 测试 → 279–281 取得独立训练来源 → 284 将 26 定位为 pilot → 285 真实采集启动 → 290 两路并行与三轮封顶。

270 两折已被 272 替代；272 的 5+245 方案是历史方案，当前已执行采集路线是 26 个独立应用。独立来源取得与285采集授权并未自动将旧245正式评测方案重划为250。**250 仍是目标评测登记，不代表新正式评测协议已经冻结**。旧 corravale 已有 17 个版本/18 个启动片段、多次指导与评分暴露，最后一份完整视觉评分结果 0.7006 < 0.75；不能恢复 STOP 或将整个公开 250 直接称作完全未见的 held-out。正式评测前须重新处理历史暴露和来源家族隔离。

论文所述 35,000 是独立训练应用上采集并筛选的轨迹数，不是 250 个应用的本地已下载训练包。本项目未取得该官方训练包/完整训练应用清单，不能与当前自建来源混称。

## 4. 现在阻在哪里

1. **素材验收未闭合。** 先核对原始公开工具调用与回执、模型实际收到的图像、父轮与候选 hash、真实验证反馈、继承历史去重，形成 canonical 链和机械学习视图。raw 私有 session 不能直接作为公开学习输入。
2. **其余 24 应用未准入。** 新 reference、固定构建、重置与独立训练 verifier 都要通过；Windows/macOS/Android 真实宿主和控制通道尚缺准入证据，不能伪装成 Web 或填模型失败 0 分。
3. **学习器的实际输入尚待核对。** 既有 AutoSkill trajectory 入口扁平化为 user 文本且使用 synthetic success；其并非任务成功标注。现有输入 text-only、长链可能尾截断；图像文件存在不表示学习器看到像素。若每应用链 ingest 一次，候选上限为一次一个，最终可能空抽取/合并后更少，不保证 26 个技能。
4. **并发与成本归属有历史缺口。** 两路真实重叠约 20.8 分钟，但共享 8788 proxy 在重叠窗口造成 route 混合；不能把整个 Squoosh route 的 457 次请求全归 Squoosh，更不能宣称测得固定 2 倍提速。v2.7 的独立端口仅准备、未激活。
5. **收尾异常保留。** 观察器记录两 worker 已结束且未自动开新轮；其自有 proxy cleanup 返回码 1，且日志曾有一次临时 ledger FileNotFoundError、之后快照恢复。本轮实际确认两容器退出且上述代理端口无监听，但不将旧清理返回码改成成功，也不将其推断为 agent 仍运行。

## 5. 建议的接续顺序（尚未执行）

先完成现有两应用的终态、完整性、图像与事件对应、来源与学习视图验收；保存失败链和成本归属限制。miniPaint 停在 3/3。Squoosh 若按已有三轮采集授权继续，应先完成上一轮反馈与 checkpoint 准入，再启动独立冻结的第二轮，最多还剩两轮；本轮恢复检查没有启动它。

随后推进其余 Web/Ubuntu 的等价参考准入，原生平台按真实资源条件推进。取得完整素材后再明确 RW 的学习输入粒度、成败标签是否进入学习、截断/去重策略；不要自动套用另一聊天 tau 域的盲提取决定。建库冻结后，处理 corravale 历史暴露并冻结正式评测与比较口径。

研究假设仍是：跨应用的真实探索、失败修正与验证经验能够形成可复用 skills。当前证据只能支持“来源已取得、两应用实际采集、保留了真实失败和设施问题”；尚不支持学习有效、跨平台迁移提升或论文贡献成立。

## 6. 接续入口

- [本轮恢复记忆](../memory/292_2026-10-05_recreationbench_work_recovery.md)：用户请求、证据、更正和下一步。
- [26 来源总览](280_gui_pool_sufficiency/README.md)及[固定任务登记](280_gui_pool_sufficiency/evolution_task_registry.json)。
- [283 采集方案](283_rw_evolution_trajectory_plan/PLAN.md)与[输入合同审计](283_rw_evolution_trajectory_plan/trajectory_contract_audit.md)。
- [285 记忆](../memory/285_2026-10-04_rw_evolution_first_trajectory_started.md)与[290 记忆](../memory/290_2026-10-05_rw_parallel_evolution_collection.md)。
- [288 最新终态快照](../experiments/288_rw_parallel_evolution_collection/reports/parallel_health_state.json)。285 的 collection_status 和早期 phase manifest 是旧截面，不能单独用来统计当前全批进度。
