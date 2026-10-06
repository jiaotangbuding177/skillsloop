# 真实企业历史上的 Trace2Skill 生成侧试跑

本轮用6条完整企业会话及相关工具原记录，比较直接学习和恢复任务关系后学习。使用官方补丁提议、合并和程序应用；企业未知结果入口与事件袋适配另有明确版本。没有执行历史工具命令、补造附件或开展新任务消费。

- [v1冻结协议](PROTOCOL.md)：输入、提示、官方commit、模型、预算与失败规则。
- [v2窄修复协议](PROTOCOL_V2.md)：只补模型遗漏的冗余端点索引，保留v1失败，原响应按请求SHA复用。
- [v3传输协议](PROTOCOL_V3.md)：仅延长等待并明确重发1次超时请求，保留未知用量，之后失败即停止。
- [总实验报告](../../reports/2026-10-06_trace2skill_ecnu_total_experiment_report.md)：结果、问题、实际用量与生成物。
- [最终分阶段用量](private/run_v3/generation_costs.csv)：API返回的token；另1次超时实耗未知。

## 当前交付

本批已结束：A直接学习生成1个待审技能包；B在v1第二条漏来源索引、v2第三条接口超时后，v3第四条恢复关系方向契约失败停止。没有B最终技能，不再重跑。19实际请求、265639已报告tokens，另1次超时用量未知；114592只为预算预留。各版本失败和原始结果保留。

本地查看：

- [统一交付入口](deliverables/README.md)
- [A技能正文](deliverables/A/spreadsheet-generation-audit/SKILL.md)
- [A技能包](deliverables/A/spreadsheet-generation-audit.skill)
- [实际请求及状态](private/run_v3/requests_ledger.json)
- [来源优先的最终审阅](private/independent_audit_v3.md)
- [运行与交付审计](private/run_v3/runtime_audit.json)

技能格式及打包通过，仍存在范围泛化和Markdown结构问题。未注册个人/组织库，未证明实际任务收益；这是一轮生成探索，不是论文正式效果实验。

## 复现边界

正文、原始响应和工具载荷位于private，不进入公开研究记忆。输入及代码SHA已冻结，官方源码commit为`3d0b52a140f002a512930252b613c49048f7d5ac`。模型请求名为`ecnu-plus`，响应model字段为`qwen3.8-flash`；此为接口所报标识，不能独立认证后端权重。temperature=0且未发送seed，不承诺API重复运行得到完全相同输出。

离线审计和已保存响应重放无需密钥。新模型请求需临时进程环境`ECNU_API_KEY`；不提供包含密钥的命令、不持久化凭据。已有run拒绝覆盖，不能把重放当新独立重复。v3已继承所有旧调用和未知预算；本批停止，不能直接继续追加付费请求。
