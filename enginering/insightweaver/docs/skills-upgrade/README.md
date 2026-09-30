# Skills 链路升级：开发与适配包

**018当前状态：** 已按用户要求复用KM v1接通本地全链路，当前生效契约见[V1_ADAPTATION.md](V1_ADAPTATION.md)，实际验证见[IMPLEMENTATION.md](IMPLEMENTATION.md)。下述017状态保留作历史，不再表示当前仍停留在capture或等待新增远端API。尚未生产部署或真实KM联网验收。

日期：2026-09-20｜研究轮次017｜状态：用户已授权编码，首批轨迹采集代码与测试已落地；完整生成／演化未交付。D04／D05待答，KM确认为外部服务。

目标：在现有系统中恢复可修订任务证据，以规则与索引减少噪声、重复沉淀和逐问答模型调用，接通使用已有技能后的增量更新。沿用个人／组织技能库和技能包格式。

| 文档 | 用途 |
| --- | --- |
| [PLAN.md](PLAN.md) | 改动边界、阶段顺序、依赖、迁移与回退 |
| [SPEC.md](SPEC.md) | 数据、事件、任务关联、决策、预算、发布和使用契约 |
| [TEST.md](TEST.md) | 开发测试设计、输入与预期、执行入口；不是已通过报告 |
| [TODOLIST.md](TODOLIST.md) | 带依赖与验收映射的实施清单 |
| [DECISIONS.md](DECISIONS.md) | grill 设计树、已确认约束、未决问题及其影响 |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | 本轮实际代码、开关、测试结果、未完成项和外部接口依赖 |

本包承接 [014规则轨迹方案](../../../../research/reports/014_rule_based_trace_and_budget.md)、[013源码与兼容核查](../../../../research/reports/013_comprehensive_upgrade_plan.md)、[015贡献评估](../../../../research/reports/015_industry_contribution_assessment.md)。冲突时以最新用户决定与本包标记的已确认项为准；未决推荐不能冒充确认。

016轮仅授权准备；017轮用户明确“请你开始代码实现”，已进入本项skills链路编码与软件测试。未进行实际数据库迁移、真实模型执行、生产部署或论文实验。具体实现覆盖和限制见IMPLEMENTATION，不能将本包规格都视作已实现。

准备开始时源码 Git 工作区干净。静态源码检查不能证明生产部署行为；任何未在本仓库实现的运行时接口都列作显式依赖。
