# 固定远端快照 τ² 三域统计复核

来源提交：`14f5b59ab29351973429777fb013afafd15297ce`。本轮仅用 Python 标准库离线读取六个正式结果 JSON；未执行模型、实验或服务，未修改原始实验。数值由原始 `simulations` 复算，脚本报告只用于比较。

## 正式对照

| 域 | 任务×试验 | B0成功 | B1成功 | 差值pp | B1胜/负/平（场） | 精确McNemar p | 任务bootstrap 95% CI pp | 任务胜/负/平 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 零售 | 40×4=160 | 126/160（78.75%） | 134/160（83.75%） | +5.00 | 20/12/128 | 0.215327 | [-2.50, +12.50] | 15/7/18 |
| 航空 | 20×4=80 | 54/80（67.50%） | 58/80（72.50%） | +5.00 | 12/8/60 | 0.503445 | [-5.00, +13.75] | 7/3/10 |
| 电信 | 40×4=160 | 127/160（79.38%） | 119/160（74.38%） | -5.00 | 23/31/106 | 0.340891 | [-16.25, +5.63] | 10/13/17 |

三域场级检验均未显著、任务区间均跨零。40/20/40题各四次，场次嵌套在同题中；McNemar场级p不消除题内相关性。任务bootstrap按任务均差重采样，10,000次、seed 42、B0原始出现顺序、索引250/9749、奖励单位四位小数，已核对三域原 `paired_summary_v4.py` 定义。独立复算的配对人数、胜负平、均差、p和CI均匹配保存报告（p按报告六位小数比较）。任务层符号检验另见JSON，不与场级p混用。

## 学习源采集阶段更正

| 域 | 原始场数 | 保存reward=1 / reward=0 | reward均值 | 原生终态 |
|---|---:|---:|---:|---|
| 零售 | 70 | 5 / 65 | 0.071428571 | timeout: 10；too_many_errors: 5；user_stop: 55 |
| 航空 | 26 | 19 / 7 | 0.730769231 | user_stop: 26 |
| 电信 | 70 | 53 / 17 | 0.757142857 | user_stop: 70 |

航空为19成功+7失败/26=0.730769231；电信为53成功+17失败/70=0.757142857。报告中的航空0.72、电信52+18/0.75不能作为原始结果真值。零售是5成功、50个user_stop零分、10个timeout零分、5个too_many_errors零分；后15场保存reward=0但没有正常reward_breakdown，机制归因需另查流程证据。学习源采集与正式评测分开，不把collect分数并入B0/B1。

## 四次重复稳定性

| 域 | 组 | 0/1/2/3/4次成功任务数 | 曾成功任务/全体题 | 四次全成功/全体题 | 曾成功但四次不稳定/曾成功 | pass^1 / pass^2 / pass^3 / pass^4 | pass@1 / pass@2 / pass@3 / pass@4 |
|---|---|---:|---:|---:|---:|---|---|
| 零售 | B0 | 1/5/3/9/22 | 39/40 | 22/40 | 17/39 | 78.75% / 67.50% / 60.62% / 55.00% | 78.75% / 90.00% / 94.38% / 97.50% |
| 零售 | B1 | 1/2/4/8/25 | 39/40 | 25/40 | 14/39 | 83.75% / 74.17% / 67.50% / 62.50% | 83.75% / 93.33% / 96.25% / 97.50% |
| 航空 | B0 | 3/2/1/6/8 | 17/20 | 8/20 | 9/17 | 67.50% / 55.83% / 47.50% / 40.00% | 67.50% / 79.17% / 82.50% / 85.00% |
| 航空 | B1 | 1/3/3/3/10 | 19/20 | 10/20 | 9/19 | 72.50% / 60.00% / 53.75% / 50.00% | 72.50% / 85.00% / 91.25% / 95.00% |
| 电信 | B0 | 1/5/2/10/22 | 39/40 | 22/40 | 17/39 | 79.38% / 68.33% / 61.25% / 55.00% | 79.38% / 90.42% / 94.38% / 97.50% |
| 电信 | B1 | 0/6/6/11/17 | 40/40 | 17/40 | 23/40 | 74.38% / 58.75% / 49.38% / 42.50% | 74.38% / 90.00% / 96.25% / 100.00% |

pass^k为每题四次观测中均匀抽取k次全部成功的估计：均值 C(c,k)/C(4,k)；pass@k为至少一次成功：均值 [1−C(4−c,k)/C(4,k)]。二者各用完整四次、二元评分任务；本次六组均无排除。pass^4=四次全成功题比例，pass@4=四次至少一次成功题比例。不能把成功率直接取k次幂或把22/40一类四次全成功计为pass@4。

## 耗时、消息、业务工具与原生成本字段

| 域 | 组 | 耗时均值/P50/P95秒 | 平均消息数 | 平均业务工具调用（助手/用户） | 原生tool.error=True/工具回复 | 受影响场次 | 平均用户非终止消息（含初始） | 用户prompt/completion tokens |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 零售 | B0 | 468.43/446.37/660.80 | 25.562 | 7.331（7.331/0.000） | 23/1173（1.96%） | 21/160 | 4.450 | 806155/241331 |
| 零售 | B1 | 600.92/597.00/697.01 | 26.062 | 7.812（7.812/0.000） | 38/1250（3.04%） | 28/160 | 4.219 | 882677/268425 |
| 航空 | B0 | 835.61/750.82/1165.40 | 26.550 | 7.800（7.800/0.000） | 5/624（0.80%） | 5/80 | 4.475 | 466655/164715 |
| 航空 | B1 | 848.33/816.33/1181.52 | 29.600 | 9.662（9.662/0.000） | 8/773（1.03%） | 8/80 | 4.138 | 485604/172290 |
| 电信 | B0 | 749.37/675.41/1230.45 | 54.219 | 16.925（6.619/10.306） | 5/2708（0.18%） | 4/160 | 18.806 | 15897128/350025 |
| 电信 | B1 | 776.23/705.93/1205.45 | 47.362 | 15.088（6.906/8.181） | 30/2414（1.24%） | 27/160 | 15.369 | 13686717/307061 |

耗时按保存的每场duration，P50/P95使用线性插值；跨场耗时之和不是并发批次墙钟。业务工具为tau² messages里的tool_calls，电信含用户侧工具；外部技能Read、模型请求均不计入。错误仅指工具回复原生error字段为true，不做语义错误推断；每组总量、均值和角色分解见JSON。非终止用户消息排除STOP/TRANSFER/OUT-OF-SCOPE控制标记，含初始消息；减一版本只是对首条非终止用户消息为初始的约定。

六组assistant消息usage均为空，agent/user每场cost字段均为空；用户消息usage可观察。消息cost的保存零值不能证明实际免费，agent tokens、技能生成/读取tokens、实际金额与正式评测资源归因均未知。请求日志全账本累计不得当作本表评测成本。

## 评分完整性与分解

| 域 | 组 | reward缺失/无效/非二元 | 分解缺失 | basis列出但分解缺项 | 保存reward分解组合 |
|---|---|---:|---:|---|---|
| 零售 | B0 | 0/0/0 | 0 | {} | DB=0.0;NL_ASSERTION=1.0: 34；DB=1.0: 4；DB=1.0;NL_ASSERTION=1.0: 122 |
| 零售 | B1 | 0/0/0 | 0 | {} | DB=0.0;NL_ASSERTION=0.0: 1；DB=0.0;NL_ASSERTION=1.0: 24；DB=1.0: 4；DB=1.0;NL_ASSERTION=0.0: 1；DB=1.0;NL_ASSERTION=1.0: 130 |
| 航空 | B0 | 0/0/0 | 0 | {} | COMMUNICATE=0.0;DB=0.0: 2；COMMUNICATE=1.0;DB=0.0: 24；COMMUNICATE=1.0;DB=1.0: 54 |
| 航空 | B1 | 0/0/0 | 0 | {} | COMMUNICATE=1.0;DB=0.0: 22；COMMUNICATE=1.0;DB=1.0: 58 |
| 电信 | B0 | 0/0/0 | 0 | {} | ACTION=0.0;ENV_ASSERTION=1.0: 2；ACTION=1.0;ENV_ASSERTION=1.0: 46；ENV_ASSERTION=0.0: 31；ENV_ASSERTION=1.0: 81 |
| 电信 | B1 | 0/0/0 | 0 | {} | ACTION=1.0;ENV_ASSERTION=1.0: 48；ENV_ASSERTION=0.0: 41；ENV_ASSERTION=1.0: 71 |

reward_basis与分解的缺项逐场保留在JSON，不直接视为评分失败：可选NL断言未应用时可能缺少NL_ASSERTION分解。额外action/env/nl/communicate检查统计只是描述，不替换官方最终reward。

## 电信事后子组诊断

| 切分 | 子组 | B0成功/场数（题数） | B1成功/场数（题数） | 差值pp |
|---|---|---:|---:|---:|
| 问题类型 | mms_issue | 39/64（16） | 38/64（16） | -1.56 |
| 问题类型 | mobile_data_issue | 31/36（9） | 21/36（9） | -27.78 |
| 问题类型 | service_issue | 57/60（15） | 60/60（15） | +5.00 |
| PERSONA | Easy | 48/56（14） | 40/56（14） | -14.29 |
| PERSONA | Hard | 39/52（13） | 39/52（13） | +0.00 |
| PERSONA | None | 40/52（13） | 40/52（13） | +0.00 |

子组由保存task_id中的[问题类型]/[PERSONA:...]解析，仅作事后机制线索；未作多重检验校正，不能据某个子组称算法胜利。

## 配对、适用范围与未知

- 六组无重复task×trial、缺失reward或非二元reward；三域完整配对，seed分别160/160、80/80、160/160一致。所有保存正式场次termination_reason均为user_stop；具体STOP/TRANSFER/OUT-OF-SCOPE控制标记另计，user_stop不等于业务成功。
- 本表仅包含固定快照中的指定正式结果。零售OLDlib_8partial文件不入正式分母；此前失败、重跑、选择最终保存结果的过程不能由这六份结果排除。全部保存终态正常不证明尝试历史或基础设施无故障。
- seed=42的单一实验设定、同题四次和同任务家族相关性限制泛化；模型别名不证明物理后端、资源并发或harness过程完全相同。当前比较是技能库与显式读取提示等整个处理包的效果，不能归因于某个独立算法机制。
- 历史159/160及其他读取率如果只由保存audit的read调用/路径判断，只能记读取尝试；不能证明调用成功、非空SKILL全文交付或全文被模型消费。本脚本没有读取外部私有session，未新增验证技能全文读取率。
- 这三域没有合并总体p值，也没有把电信的下降删除；正式成功、稳定性、耗时和错误需同时报告。

## 复现与来源

脚本：`analyze_saved_results.py`；机器可读结果：`statistics_audit.json`；中文表头：`metrics.csv`。JSON记录各原始文件绝对路径、SHA-256、字段定义、异常列表、任务明细和脚本报告对照。

- 零售 B0: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/148_tau2_retail_autoskill/runs/test_v4/no_skill.json`；SHA-256 `cd10e6d910772f52ce6fd4005e7983ea79cd7f05c3515560ccf3291869e151b2`
- 零售 B1: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/148_tau2_retail_autoskill/runs/test_v4/autoskill_library.json`；SHA-256 `49ec025591721ba9d3e93e0f15897d4e19043bccd9051be25d97c61ec158cfdb`
- 航空 B0: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/runs/test/no_skill.json`；SHA-256 `127edc34ddefd0901a5ac837bd27dfb5e7a35d2729b1191dc1bf00e3661f62cf`
- 航空 B1: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/runs/test/autoskill_library.json`；SHA-256 `dc2c6f7945c52e0c2c2819a205edbb35314967087e19be205e10e165c830fd7f`
- 电信 B0: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/runs/test/no_skill.json`；SHA-256 `2c71a8e0165ec24c29d436c21d0b37655ef70339800819523f4ed8bb47896a13`
- 电信 B1: `D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/runs/test/autoskill_library.json`；SHA-256 `589e1d9f321ebc8b11a08b1310122a66ffa3c7e54e507dc2b4f3a4ed72affe91`
