# 267 最终实验报告：AutoSkill × τ²-bench Airline（v1 批次）

- 生成时间：2026-10-05（北京时间）；状态：**配对评测完成**（B0 80/80；B1 80/80）
- 用户决策（2026-10-04）：airline 用当前 deepseek-flash；**学习按 AutoSkill 原生链路（不修复盲提取）**——见记忆 282 的归因纪律
- 数据来源：`runs/test/{no_skill,autoskill_library}.json`、`reports/{skill_read_audit_267,paired_summary_267}.json`、`runs/collect/evolution.json`

## 0. 结论摘要

1. **B1（有技能）= 58/80 场满分（均值 0.725）；B0（无技能）= 54/80（0.675）。差值 +5.0pp。**
2. 配对（同题同 trial，80 对）：B1 更好 12、B0 更好 8、持平 60；确切符号检验 p=0.503；任务级 bootstrap 95% CI = [-5.0pp, +13.8pp]（含 0）。
3. 任务级（20 题）：改善 7、退步 3、持平 10（p=0.344）。最大改善 task 29（0.25→0.75）、48/8（0.75→1.0）；最大退步 task 16（0.75→0.25）。
4. **技能真实读取率 100%（80/80 已完成 B1 场匹配到真实原生 `read` 调用；全部 82 个会话含 `$技能` 引用且全部触发读取）。** 证据：会话归档 sqlite 的 `read ... skills/airline_reservation_cancellation_refund_policy_check/SKILL.md` 调用。
5. 口径：方向为正、未达统计显著；与 148 零售的配对差值（+5.0pp）数值相同但两例均不显著，不能合并宣称增益。**学习为盲提取、无成败监督**（26 条采集轨迹中 19 成功+7 失败混合进入提取，`success_only=False`），解释结果时必须保留此限制。

## 1. 实验设置

| 项目 | 取值 |
|---|---|
| 基准 | τ²-bench v1.0.1（fc0055dc）airline 文本域；50 题（train 30 / test 20） |
| 拆集 | dev=4（`42/21/20/12`）；演化 26（采集 26/26，均分 0.72）；测试 20 |
| 评测规模 | test 20 题 × 4 trials × 2 组 = 160 场（B0/B1 各 80） |
| 消费者/用户模拟器 | deepseek-flash（DeepSeek 官方 API，relay 8180） |
| 判分 | glm-4-flash（NL 断言）；airline 评分=DB+COMMUNICATE（COMMUNICATE 为字符串匹配，无模型） |
| 技能库 | `frozen_skills/`（namespace `tau_airline_pool_v1`，sha256 清单）：**1 个技能**（`airline_reservation_cancellation_refund_policy_check`，无 references） |
| 学习 | AutoSkill 原生离线 agentic 轨迹路径；26/26 处理、0 失败；**盲提取（无 reward/成败标签）** |
| 技能注入 | v6 原生 `$技能` 引用（首轮 prompt），模型以原生 read 读取正文 |
| 运行质量 | 160 场全部完成；全部 user_stop 正常终止；无缺失奖励；平均时长 B0 836s / B1 848s |

## 2. 主要结果

| 指标 | B0 无技能 | B1 有技能 |
|---|---|---|
| 完成场次 | 80 | 80 |
| 平均 reward | 0.675 | **0.725** |
| pass@1 | 67.5% | 72.5% |
| 全 4 场全过任务 | 8/20 | 10/20 |
| 全 4 场全 0 任务 | 3/20 | 1/20 |
| 平均单场时长 | 836s | 848s |

配对（80 对）：B1 更好 12 / B0 更好 8 / 持平 60；均值差 **+0.05**；符号检验 p=0.503；任务级 bootstrap 95% CI **[-0.05, +0.1375]**。任务级 7 改善 / 3 退步 / 10 持平（p=0.344）。
逐题表见 `reports/paired_report_267.md`。

## 3. 技能读取审计

- 方法：扫描 B1 会话归档 sqlite（transcript_events / trajectory_runtime_events）中的真实 `read ... skills/<name>/SKILL.md` 调用；sim↔session 按启动时间匹配。
- 结果：**82/82 会话含 `$技能` 引用且 82/82 触发真实读取（100%）；已完成 80 场全部匹配到读取（80/80 = 100%）**；读取的技能为该库唯一技能。
- 直接证据样例：`/var/tmp/skillsloop267/<hash>/workspace/skills/airline_reservation_cancellation_refund_policy_check/SKILL.md`（原生 toolCall，归档于各会话 sqlite）。

## 4. 限制与不可比声明

- τ²-bench v1.0.1 airline 数据未与论文发布版逐项比对；绝对分不与论文排名对比（同 148 口径）。
- 单 seed（42）、n=20 题（airline test 集本身较小），检验功效有限；配对 CI 含 0。
- **学习侧**：盲提取、无成败监督（19 成功+7 失败轨迹混合）；不得把结果解释为"只学了正确流程"。banking 等未做域不涉及。
- 技能库仅 1 个技能（无 references），treatment 强度有限；结果是在"单技能库"条件下的观察。
- 基建：本批次受 WSL VM 周期重建事故影响（18:31-19:26），已用自愈循环与 Windows 守护恢复；失败尝试保留、未计入统计。

## 5. 产物清单

`runs/{collect/evolution.json, dev/no_skill.json, test/no_skill.json, test/autoskill_library.json}`；`reports/{skill_read_audit_267.json/.md, paired_summary_267.json, paired_report_267.md, final_report_267.md}`；`frozen_skills_manifest.json`；`ledger/requests.jsonl`；脚本 `scripts/{run_eval_loop.sh, completed_count.sh, scan_skill_reads.py, paired_summary_v4.py}`。
