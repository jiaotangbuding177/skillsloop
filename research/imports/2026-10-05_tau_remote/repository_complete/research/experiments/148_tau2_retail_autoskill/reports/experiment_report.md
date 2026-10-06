# 148 实验报告（AutoSkill x tau2-bench Retail，v1.0.1）

- 结论：**未检出技能收益（也未检出损害）**——B1 组 0/160 场读取过任何技能（技能仅被列出、从未使用），B0/B1 差异不可归因于技能；配对胜利 11:9、p=0.824。
- 材料：演化 70 场采集（55 user_stop / 10 timeout / 5 too_many_errors，基建错误 0）；测试 40 题 x 4 trials x 2 组 = 320 场（两组均无基建错误）；技能库 5 个（frozen_skills/，sha256 manifest）。
- 分数：B0 平均 reward 0.0688 / pass^1 0.0688；B1 平均 reward 0.0813 / pass^1 0.0813；pass^4 两组均为 0。
- 内容口径（逐题读完）：B0 理想12/部分27/错误101/异常20（理想:非理想 1:10.7）；B1 理想17/部分48/错误80/异常15（1:7.5）。
- 限制（不可跨比）：消费者/模拟器/判分均为 GLM-4-Flash；τ³ 修订版任务；本地 OpenClaw harness；单套 trial seed；模拟器占位符噪声（两组同等）。
- 明细：reports/final_review_b0.md、reports/final_review_b1.md、reports/summary.json、ledger/requests.jsonl、runs/ 与 frozen_skills_manifest.json。
