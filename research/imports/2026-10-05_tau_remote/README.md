# τ²-bench 最新远端结果快照

- 拉取日期：2026-10-05（北京时间）。
- 来源仓库：`https://github.com/jiaotangbuding177/skillsloop.git`，分支 `main`。
- 固定提交：`14f5b59ab29351973429777fb013afafd15297ce`。
- 提交时间：2026-10-05 07:24:36 +08:00。
- 提交说明：`Add experiments 267 (airline) and 268 (telecom) v1 paired results`。

成功取出到 `repository_complete/`，原项目实验目录与本地研究状态没有被远端内容覆盖。快照包含三个相关实验的原始结果、采集材料、冻结技能、脚本及报告；只取 Git 已提交的文件，不等同于完整远端运行时归档。

| 实验 | 快照入口 | 核心原始结果 |
| --- | --- | --- |
| 148 零售 v4 | [原报告](repository_complete/research/experiments/148_tau2_retail_autoskill/reports/final_report_v4.md) | `runs/test_v4/no_skill.json`、`runs/test_v4/autoskill_library.json` |
| 267 航空 v1 | [原报告](repository_complete/research/experiments/267_tau2_airline_autoskill/reports/final_report_267.md) | `runs/test/no_skill.json`、`runs/test/autoskill_library.json` |
| 268 电信 v1 | [原报告](repository_complete/research/experiments/268_tau2_telecom_autoskill/reports/final_report_268.md) | `runs/test/no_skill.json`、`runs/test/autoskill_library.json` |

下载完整性检查：成功快照的 `git rev-parse HEAD` 与上述提交相同；三个实验目录 `git -c core.longpaths=true diff --exit-code HEAD -- ...` 返回 0、无差异。独立统计复核及文件 SHA256 位于 `research/reviews/tau_remote_2026-10-05/`，综合报告另存于 `research/reports/`。

取出过程中，首次局部克隆的对象读取失败，改用完整对象浅克隆；Windows 长路径错误通过本次 Git 命令的 `core.longpaths=true` 解决。失败下载目录 `repository/` 保留作过程记录，**不要从它取分析输入**。成功目录为 `repository_complete/`。

本轮没有运行模型、重跑评测或更改技能。远端报告的指标用语须经过本地复核，特别是“读取调用发生”不能自动等于“成功读取全文”。

