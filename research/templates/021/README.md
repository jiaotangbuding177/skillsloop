# 首批数据与评估交接模板

配套[交接说明](../../reports/021_data_handoff.md)与[执行计划](../../reports/021_execution_plan.md)。这些是模板，不是已采集数据。可直接提供原始表导出，由我负责映射；不用为了交接先填完全部模板。

- `handoff.yaml`：首先补数据库路径、范围与可用条件；不填写密码。
- `task_catalog.csv`：每行一种实际任务；importance_basis填写业务理由，不用AI自评分。
- `evaluation_cases.csv`：每行一个独立测试任务；参考答案路径必须与agent输入路径隔离。
- `annotations.csv`：业务评审独立填写；unknown可以保留，不能把无反馈当成功。

CSV中包含逗号/换行的值需标准双引号转义。原始企业文本和附件留在受控数据目录，通过相对引用关联；这些空模板可留在项目中，填入敏感内容后的副本不要加入公开论文材料。
