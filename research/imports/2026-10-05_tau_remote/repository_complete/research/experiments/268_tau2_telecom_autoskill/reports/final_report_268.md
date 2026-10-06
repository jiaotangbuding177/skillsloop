# 268 最终实验报告：AutoSkill × τ²-bench Telecom（v1 批次）

- 生成时间：2026-10-05（北京时间）；状态：**配对评测完成**（B0 160/160；B1 160/160）
- 用户决策（2026-10-04）：telecom 用当前 deepseek-flash；**学习按 AutoSkill 原生链路（不修复盲提取）**——记忆 282 的归因纪律生效
- 数据来源：`runs/test/{no_skill,autoskill_library}.json`、`reports/{skill_read_audit_268,paired_summary_268}.json`、`runs/collect/evolution.json`

## 0. 结论摘要

1. **B1（有技能）= 119/160 场满分（均值 0.7438）；B0（无技能）= 127/160（0.7937）。差值 −5.0pp（负向）。**
2. 配对（同题同 trial，160 对）：B1 更好 23、B0 更好 31、持平 106；确切符号检验 p=0.341；任务级 bootstrap 95% CI = [−16.3pp, +5.6pp]（含 0）。**方向为负但同样未达显著。**
3. 任务级（40 题）：改善 10、退步 13、持平 17（p=0.678）。最大改善 0.25→1.0（mms 类多故障组合题）；最大退步 1.0→0.25（多个 airplane_mode 组合题）。
4. **技能真实读取率 100%（160/160 已完成 B1 场匹配到真实原生 `read` 调用；160/160 会话含 `$技能` 引用并全部触发读取）。**
5. 口径：三域（148 零售 +5.0pp、267 机票 +5.0pp、268 电信 −5.0pp）**方向不一致、均不显著**——与"技能库对配对结果无稳定方向性影响"的观察一致；不得选择性报告涨的那些。**学习为盲提取、无成败监督**（70 条采集轨迹全部进入提取，其中 52 成功+18 失败），解释必须保留此限制。

## 1. 实验设置

| 项目 | 取值 |
|---|---|
| 基准 | τ²-bench v1.0.1（fc0055dc）telecom 文本域；官方 split train 74 / test 40 |
| 拆集 | dev=4（覆盖 3 类，PERSONA 混合）；演化 70（采集 70/70，均分 0.75）；测试 40 |
| 评测规模 | test 40 题 × 4 trials × 2 组 = 320 场（B0/B1 各 160） |
| 消费者/用户模拟器 | deepseek-flash（relay 8181）；用户模拟器带 30 个用户侧工具 |
| 判分 | glm-4-flash（NL 断言）；telecom 奖励=ENV_ASSERTION（状态断言，无判分模型） |
| 技能库 | `frozen_skills/`（namespace `tau_telecom_pool_v1`，sha256 清单）：**1 个技能**（`telecom_no_service_mms_data_diagnosis_restoration_escalation`，含 29 个参考文件，共 30 文件） |
| 学习 | AutoSkill 原生离线 agentic 轨迹路径；70/70 处理；**盲提取（无 reward/成败标签）** |
| 技能注入 | v6 原生 `$技能` 引用（首轮 prompt），模型以原生 read 读取正文+参考文件 |
| 运行质量 | 320 场全部完成、正常终止；无缺失奖励；平均时长 B0 749s / B1 776s |

## 2. 主要结果

| 指标 | B0 无技能 | B1 有技能 |
|---|---|---|
| 完成场次 | 160 | 160 |
| 平均 reward | **0.7937** | 0.7438 |
| pass@1 | 79.4% | 74.4% |
| 全 4 场全过任务 | 22/40 | 17/40 |
| 全 4 场全 0 任务 | 1/40 | 0/40 |
| 平均单场时长 | 749s | 776s |

配对（160 对）：B1 更好 23 / B0 更好 31 / 持平 106；均值差 **−0.05**；符号检验 p=0.341；任务级 bootstrap 95% CI **[−0.1625, +0.0563]**。任务级 10 改善 / 13 退步 / 17 持平（p=0.678）。
逐题表见 `reports/paired_report_268.md`。

## 3. 技能读取审计

- 方法：扫描 B1 会话归档 sqlite 中真实 `read ... skills/<name>/SKILL.md` 调用；sim↔session 按启动时间匹配（目录名安全化后匹配 160/160）。
- 结果：**160/160 会话含 `$技能` 引用且全部触发真实读取（100%）；已完成 160 场全部匹配到读取（100%）**。读取技能为该库唯一技能（1 场额外读取了插件技能 browser-automation，属库外噪音）。
- 说明：telecom 的技能含 29 个参考文件，会话除 SKILL.md 外可能继续读取 references（本次审计按 SKILL.md 计触发）。

## 4. 限制与不可比声明

- 单 seed（42）、n=40 题；配对 CI 含 0，方向为负但不显著；绝对分不与论文排名对比。
- **学习侧**：盲提取、无成败监督（52 成功+18 失败轨迹混合）；**负向结果不得被解释为"技能把模型带坏"的确定结论**，同样也不得被淡化——应作为"该库条件下的配对观察"如实报告。
- 技能库仅 1 个（复合）技能；treatment 强度与 148/267 不同（telecom 技能带大量参考文件）。
- 基建：本批次经历 WSL VM 周期重建事故与多次重启（自愈循环+守护恢复）；失败尝试保留、不计入统计。

## 5. 三域并列速览（同口径）

| 域 | B0 | B1 | 差值 | 配对(胜/负/平) | p | 技能读取率 |
|---|---|---|---|---|---|---|
| 148 retail（v4） | 0.7875 | 0.8375 | **+5.0pp** | 20/12/128 | 0.215 | 99.4%（159/160） |
| 267 airline | 0.675 | 0.725 | **+5.0pp** | 12/8/60 | 0.503 | 100%（80/80） |
| 268 telecom | 0.7937 | 0.7438 | **−5.0pp** | 23/31/106 | 0.341 | 100%（160/160） |

三域方向不一致、全部不显著；读取率均在 99–100%（v6 `$技能` 机制在三个域均被验证有效）。

## 6. 产物清单

`runs/{collect/evolution.json, dev/no_skill.json, test/no_skill.json, test/autoskill_library.json}`；`reports/{skill_read_audit_268.json/.md, paired_summary_268.json, paired_report_268.md, final_report_268.md}`；`frozen_skills_manifest.json`；`ledger/requests.jsonl`；脚本 `scripts/{run_eval_loop.sh, completed_count.sh, scan_skill_reads.py, paired_summary_v4.py}`。
