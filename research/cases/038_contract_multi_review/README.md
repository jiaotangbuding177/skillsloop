# P0-1 合同／协议多立场审查：真实案例材料

本案例包用于研究准备。来源是用户提供的两份本地企业导出；没有调用外部模型，没有生成或注册技能。解释和预检结果见[038报告](../../reports/038_contract_multi_review_case_preparation.md)。

| 文件 | 用途 |
| --- | --- |
| `package_manifest.json` | 来源、划分、数量和证据边界 |
| `source_index.json` | 每条原始消息ID、原导出行号、角色、哈希及用户时间来源 |
| `cohort_index.json` | 排除技能请求后的P0-1关键词命中会话、消息ID与统计口径 |
| `recovered_trajectories.json` | 三会话的回合顺序、任务边界、助手消息组和证据状态 |
| `holdout_request.json` | 较晚受托方会话的首条真实请求；后续助手回复留在私有原文中 |
| `preflight.json` | 当前Demo无模型预检的识别与聚类结果 |
| `prepare_case.py` | 从两份来源重新抽取本案例包的脚本 |
| `private/raw_messages.jsonl` | 70条选定的原始导出行，正文未改 |
| `private/user_messages_with_dates.jsonl` | 新包中对应的14条用户消息与时间 |
| `private/eligible_contract_user_messages.jsonl` | P0-1桶排除技能请求会话后的227条用户原始消息；仍是关键词命中，未逐条确认为任务 |
| `private/demo_generation_import.jsonl` | 8回合原句导入视图，助手连续片段并入相应用户回合 |
| `private/demo_generation_import_compat.jsonl` | 仅诊断接口：委托方首句前加“请”，不可视为原文 |

`private/` 含企业会话正文，只在本地使用。原始合同DOCX和历史输出文件不在导出中；文件名和助手陈述不是文件内容或完成证明。模型测试时只能传入指定的生成视图，不得把留出会话的历史助手回答一并给生成器。

从用户原始目录重建：

```powershell
python research/cases/038_contract_multi_review/prepare_case.py --mining C:\Users\39835\Downloads\zkys-skill-mining-20260925 --raw C:\Users\39835\Downloads\zkys-raw-export-20260925 --out research/cases/038_contract_multi_review
```

同一成员的生成材料依时间先后为供应商质量协议（9月7日）和委托方危废处置协议（9月21日）；9月23日受托方委托生产协议是较晚留出案例。时间仅是新包用户消息的时间，旧包助手时间仍不可用。
