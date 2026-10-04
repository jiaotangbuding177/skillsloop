# 289：267（Airline）配对评测完成——+5.0pp（不显著）、技能读取率 100%

## 用户已确认要求（继承）

airline 用当前 deepseek-flash；学习按 AutoSkill 原生链路（盲提取、不修复）——记忆 282 的归因纪律生效。

## 证据支持的观察（267，评测 160/160 完成）

- **B0 无技能 54/80 = 0.675；B1 有技能 58/80 = 0.725；差 +5.0pp**（与 148 零售的 +5.0pp 数值相同；两例均不显著，不得合并宣称增益）。
- 配对 80 对：B1 更好 12 / B0 更好 8 / 持平 60；符号检验 p=0.503；任务级 bootstrap 95% CI [-0.05, +0.1375]；任务级 7 改善 / 3 退步 / 10 持平（p=0.344）。最大改善 task 29（0.25→0.75）；最大退步 task 16（0.75→0.25）。
- **技能真实读取率 100%**：82/82 会话含 `$技能` 引用且全部触发原生读取；已完成 80 场 80/80 匹配到读取；证据为会话 sqlite 中 `read .../skills/airline_reservation_cancellation_refund_policy_check/SKILL.md` 的原生 toolCall。
- 运行质量：160 场全完成、全 user_stop、无缺失奖励；B0/B1 平均时长 836s/848s；无基建失败计入。
- 学习侧：26 条轨迹（19 成功+7 失败）盲提取 → 冻结库 1 技能（无 references）；treatment 强度有限。

## 产物与来源

- 报告：`experiments/267_tau2_airline_autoskill/reports/final_report_267.md`；明细 `paired_report_267.md`、`skill_read_audit_267.md/.json`、`paired_summary_267.json`。
- 数据：`runs/{collect/evolution.json, test/no_skill.json, test/autoskill_library.json}`、`frozen_skills_manifest.json`、`ledger/requests.jsonl`。

## 边界与下一步

- 单 seed、n=20 题功效有限；CI 含 0；绝对分不与论文可比；**结果解释必须保留"盲提取、无成败监督"限制**。
- 268（telecom）评测进行中（00:02 时 B0 32/160、B1 39/160），预计通宵完成；完成后按同口径出报告，与 148/267 并列汇总。
- 基建：WSL 事故 #2 后持续稳定（PID1 19:26:20 起）；Docker Desktop 保持停止（是否恢复待用户）。
