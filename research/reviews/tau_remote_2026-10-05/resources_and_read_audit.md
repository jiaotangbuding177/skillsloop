# 267航空、268电信：资源与技能读取审计

日期：2026-10-05。固定提交：`14f5b59ab29351973429777fb013afafd15297ce`。本轮仅离线读取、复算及保存本审计；没有运行模型、重跑实验或修改原实验。

快照根：`D:/skillsgen-industry_track/research/imports/2026-10-05_tau_remote/repository_complete/research/experiments`。下文267/268分别指根目录中的`267_tau2_airline_autoskill`和`268_tau2_telecom_autoskill`。原报告中的错误数值保留，本文另作更正。机器可读复算值见[resources_and_read_audit.json](resources_and_read_audit.json)。

## 证据支持的结论与未知项

可以独立核验：采集结果及其成功/零分/异常构成、学习输入文件数、冻结技能/资源的原始字节和清单哈希、正式B0/B1场次及耗时、user消息中可观察的token部分、账本的逐行请求/路由/状态/字节/延迟、读取报告自身的计数及scanner的判定规则。

不能从本快照独立核验：消费者的全部模型token、两组总token和真实金额、每条轨迹的学习模型调用数、B0/B1各自的账本请求总数、成功读到技能全文及其冻结版本身份、29个参考文件的实际读取覆盖、记录之外的API尝试/传输重试。快照未包含正式会话的原生SQLite、prompt或逐轮stdout；这表示证据未随该Git快照交付，不能反推远端当时没有归档或模型没有读取。

## 生成来源与成败：更正原报告

以下直接复算`runs/collect/evolution.json`，并与`autoskill_input/trajectories/manifest.json`逐task/reward比对；两者一致。成功定义为reward=1；零分轨迹仍为合法学习来源，不能等同于API失败。

| 指标 | 267航空 | 268电信 |
|---|---:|---:|
| 采集/学习输入轨迹数 | 26 | 70 |
| reward=1 | 19 | 53 |
| reward=0 | 7 | 17 |
| 部分分数 | 0 | 0 |
| reward缺失 | 0 | 0 |
| termination=user_stop | 26 | 70 |
| termination=exception | 0 | 0 |
| 采集均值 | 0.7307692308 | 0.7571428571 |
| 已存在的task文本文件数 | 26 | 70 |
| manifest记录的输入字符合计 | 245,753 | 765,908 |

航空原`final_report_267.md`写采集均分0.72，实际为19/26≈0.7308。电信原`final_report_268.md`写52成功+18失败、均分0.75，实际原结果和输入manifest都是53成功+17零分、均值53/70≈0.7571。不把这两个采集指标错误传播到正式B0/B1统计。

原航空报告称26/26处理、0失败，原电信报告称70/70处理。这是原报告值；本快照缺实际学习打印日志，不能独立确认每条均形成技能、每个内部API调用完成或学习无异常。`autoskill_build_trajectory.py`传入`success_only=False`、`continue_on_error=True`，外层没有抛出异常不等于每条内部提取成功。manifest保留reward用于来源审计，而轨迹文本生成代码没有把reward/成败标签写入学习材料。

来源：[航空采集结果](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/runs/collect/evolution.json)、[航空输入manifest](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/autoskill_input/trajectories/manifest.json)、[电信采集结果](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/runs/collect/evolution.json)、[电信输入manifest](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/autoskill_input/trajectories/manifest.json)。

## 冻结技能、资源和字节

字节采用固定Git提交的原始blob，逐文件SHA-256全部匹配`frozen_skills_manifest.json`。Windows检出转为CRLF，使工作区文件稍大；这不是冻结内容发生变化。不能用工作区原始字节直接误判原manifest哈希失效。

| 指标 | 267航空 | 268电信 |
|---|---:|---:|
| 技能数 | 1 | 1 |
| 文件总数 | 1 | 30 |
| SKILL.md原始字节 | 7,247 | 32,100 |
| references文件数 | 0 | 29 |
| references原始总字节 | 0 | 30,604 |
| 全库原始总字节 | 7,247 | 62,704 |
| 空参考文件 | 0 | 2 |
| 清单原始blob SHA匹配 | 1/1 | 30/30 |

电信两个真正空文件为：

- `references/device_side_remediation_checklist.md`
- `references/no_service_diagnostic_ladder.md`

这只描述产物，不把空文件或资源大小直接归因于评测的负差值。工作区CRLF字节为航空7,322、电信SKILL.md 32,303+references 31,154=63,457；正式资源比较应采用上表Git/LF原始字节。

来源：[航空冻结清单](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/frozen_skills_manifest.json)、[电信冻结清单](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/frozen_skills_manifest.json)。逐文件原始字节、工作区字节、CRLF数量和SHA核验见伴随JSON。

## 使用组的已知资源与未知成本

时长由正式`runs/test/{no_skill,autoskill_library}.json`中每场start_time/end_time复算；合计是各场时长的和，含并行场次，不能当整个实验墙钟。

| 域/组 | 场次 | 平均单场秒 | 各场时长合计秒 | 可观察user prompt tokens | 可观察user completion tokens |
|---|---:|---:|---:|---:|---:|
| 航空B0 | 80 | 835.6135 | 66,849.0780 | 466,655 | 164,715 |
| 航空B1 | 80 | 848.3369 | 67,866.9509 | 485,604 | 172,290 |
| 电信B0 | 160 | 749.3769 | 119,900.2969 | 15,897,128 | 350,025 |
| 电信B1 | 160 | 776.2378 | 124,198.0429 | 13,686,717 | 307,061 |

这里的token只来自结果内user消息的usage，分别覆盖航空438/411条user消息、电信3169/2619条user消息。assistant消息没有usage字典，原生代理可能包含结果消息没有呈现的模型/工具多轮。因此可以比较“结果中可观察的user部分”，不能把该表叫B0/B1总模型消耗、消费者消耗或整个方法成本。账本本身无usage字段，也不意味着结果的所有角色均无usage。

两域两组所有simulation级`agent_cost`和`user_cost`均为NULL。user消息的cost值为0；assistant消息中首条cost为0、其余为NULL。0或缺失均未经过真实账单/价格核验，不能据此称免费。消费者token、学习token、两组完整token及金额保持UNKNOWN。中途审查曾使用`value or 0`求和，把NULL压成0；本文已纠正，伴随JSON保存原值分类，不使用该错误和。

## 全账本：逐路由、传输状态与资源

按`ledger/requests.jsonl`的已落盘行复算。相同seq可在不同重启段重复，不能按seq去重请求。整行精确重复数两域均为0。

| 域 | 路由角色 | 已记录请求 | completed/HTTP200 | 已记录错误 | 请求字节 | 响应字节 | 请求延迟合计秒 |
|---|---|---:|---:|---:|---:|---:|---:|
| 航空 | consumer chat | 1,720 | 1,720 | 0 | 83,862,257 | 78,581,748 | 2,460.722 |
| 航空 | user chat | 1,047 | 1,047 | 0 | 5,416,435 | 2,414,900 | 2,742.124 |
| 航空 | embed | 6 | 6 | 0 | 29,886 | 77,594 | 1.715 |
| 电信 | consumer chat | 6,890 | 6,890 | 0 | 368,160,904 | 173,236,771 | 7,444.200 |
| 电信 | user chat | 7,856 | 7,856 | 0 | 173,337,528 | 11,569,025 | 11,338.644 |
| 电信 | embed | 154 | 154 | 0 | 1,286,835 | 1,988,356 | 42.067 |

航空已记录2,773条，电信14,900条，合计17,673条。路线名称仍沿用`tau2_retail`，不能凭复制的路径名称把这两域结果误当零售结果。账本中的user角色同时服务用户模拟器和AutoSkill学习，角色不是独立实验组标识。

- 航空：seq唯一值2,359，范围1–2,375，重复seq行414；最新budget_state的requests_reserved=2,375。
- 电信：seq唯一值14,769，范围2–14,962，重复seq行131；最新requests_reserved=14,962。
- relay源码初始化内存计数为0，并在启动时写budget_state；重启段重复seq与该设计一致。不能用最新预算计数替代累计落盘行数，也不能把seq缺口直接判成特定失败次数。
- 这些行内未记录upstream_http_error、transport_error或rejected_by_cap；这只证明已落盘范围内的状态。进程终止前来不及落盘的尝试、其他历史段和供应商内部重试没有完整覆盖证明。
- completed说明relay结束转发；HTTP200和响应字节不等于正文完整、模型成功、合法评分或API费用已知。
- 延迟合计会受并发影响，不能当墙钟。请求/响应字节不是token，不能按字节换算真实费用。

B0与B1并行且共用路由；账本无task/session/group/purpose字段，不能精确分解两组各自的请求数、字节或延迟。来源：[航空账本](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/ledger/requests.jsonl)、[电信账本](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/ledger/requests.jsonl)、[relay记录实现](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/scripts/model_relay.py)。

## 学习相关时间窗口：可复算但不能精确归因

两域`run_learn_chain.sh`均按canonicalize→build→freeze顺序执行，学习日志写在Git快照外的/var/tmp。本文用“最后一场collect结束→正式B0/B1最早开始”的宽窗口筛账本，明确把无时区的simulation时间按UTC+8解释。它与脚本阶段顺序相符，但缺少实际开始/结束日志和per-request runID，不能把所有窗口行都严格认定为学习，也不能按输入文件均摊为学习调用。

| 域 | 窗口当地时间，2026-10-04 | 窗口记录 | user chat | embed | 请求字节 | 响应字节 | 延迟合计秒 |
|---|---|---:|---:|---:|---:|---:|---:|
| 航空 | 18:09:01.950757–20:33:55.278124 | 16 | 10 | 6 | 397,728 | 180,324 | 105.059 |
| 电信 | 20:46:02.392990–22:00:43.800391 | 319 | 165 | 154 | 7,041,007 | 5,532,415 | 3,036.244 |

精确学习调用/用量/金额仍UNKNOWN。这张表只能称“采集结束至评测开始窗口的资源记录”。不能把航空10或电信165直接当经过逐轨迹绑定的学习模型调用总数。

## 技能读取：保留报告触发率，不升级为全文读取

原`skill_read_audit_267.json/.md`报告82/82会话触发（航空正式B1为80场）；电信报告160/160。原最终报告进一步声称完成的80/80和160/160场都匹配到read调用。本文保留这些远端报告值，不把它们改成读取失败率。

| 读取指标 | 航空267 | 电信268 | 本轮证据级别 |
|---|---:|---:|---|
| 报告的会话数 | 82 | 160 | 原审计JSON可复算 |
| 报告的有归档会话 | 82 | 160 | 报告值，原归档未随本快照交付 |
| 报告的prompt含技能引用 | 82 | 160 | 报告值，prompt未随本快照交付 |
| 报告的触发会话 | 82 | 160 | 原审计JSON可复算 |
| 报告的技能读取触发率 | 100% | 100% | 调用/结果字符串命中口径 |
| 固定快照中的正式原生SQLite | 0 | 0 | 本轮递归与Git树核验 |
| 固定快照中的turn_000_prompt.txt | 0 | 0 | 本轮递归与Git树核验 |
| 成功全文读取/冻结版本身份 | UNKNOWN | UNKNOWN | 不足以独立验证 |
| 参考文件实际覆盖 | 不涉及 | UNKNOWN | scanner只统计SKILL.md触发 |

scanner的`scan_sqlite`扫描toolCall附近字符串和trajectory事件中的path；会话只要read_calls或read_results任一命中就triggered。它没有逐callId闭合调用和结果、检查工具成功、比较正文完整度、检测截断/分页或核对frozen manifest的文件身份。trajectory分支也没有依文档所述限定事件type='tool.call'。因此即使远端原归档存在，该scanner输出本身也不足以证明全文成功读取。其call和result计数可能重复描述同一次事件，不能当独立工具调用数。

航空JSON保存986条候选call命中、read_results为空；电信保存3080条候选call命中、9条result命中，其中主电信技能的call命中2921条。每会话列表又被截至前20项。这些是报告保存的候选项，不能由空result列表反推所有read失败，也不能用call总数称全文读取次数。

电信另1会话被报告命中库外browser-automation技能；scanner的triggered并不限制为冻结库。但本报告的主技能自身在160会话均有报告命中，因此这一库外项没有替代主技能报告计数。29个references是否读过、读成功或读全，在这次仅统计SKILL.md的审计中未知。原设置段“读取正文+参考文件”应作为预期方式，不作为逐场已核验事实。

固定Git树中的runs仅含汇总结果、index，以及航空一个wrong-port旧尝试的openclaw.json/AGENTS.md；不含正式会话的SQLite、prompt、逐轮stdout或可展开这些内容的归档包。index的session_dir是定位信息，不是原生回执。直接验证脚本仍依赖不存在的原prompt/sqlite，并按时间近邻匹配会话、抽样查看toolCall；不能在本快照执行后声称逐场全文读取已证实。

来源：[航空读取审计](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/reports/skill_read_audit_267.json)、[电信读取审计](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/268_tau2_telecom_autoskill/reports/skill_read_audit_268.json)、[scanner源码](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/scripts/scan_skill_reads.py)、[直接验证脚本](../../imports/2026-10-05_tau_remote/repository_complete/research/experiments/267_tau2_airline_autoskill/scripts/verify_skill_reads_direct.py)。

## 解释边界与后续证据

原报告的“真实读取率100%”在科研汇总中应写为“报告的技能读取触发率100%”，同时保留原值、场次范围和回执未交付的限制。已知读取触发、格式或库哈希不能证明有效遵循技能，更不能单独解释正负收益。

若以后要回答完整读取率、消费者token或费用，应补交原生call/result归档和运行/会话绑定的完整usage/计费记录；只需补证，不需先重跑模型。本文没有授权或执行该补取/实验，也未修改README、STATE或原报告。

