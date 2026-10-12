---
name: qcc-company-connection
description: 依据当前公司资料、公开披露证据或实验fixture制作公司核查报告；明确原企查查付费数据与接口是否实际恢复。
metadata:
  provenance: context_reconstruction
---

# 公司资料核查

这是原具名技能的授权重建版，原包正文、QCC凭据和原付费记录未恢复。本环境可执行公开证据核查和本地实验材料核查；不能把此能力称为企查查实时工商/司法数据连接。

核准当轮用户要查的公司全称与范围，区分同名公司、曾用名、集团/子公司。优先核查已有输入；需要公开信息时用当前网页/浏览器工具查公司官方资料、登记机关、法院、监管或交易所披露，保存链接、查询时间、原文位置和来源单位。对工商登记、股权关联、融资、诉讼与处罚分别记录实际覆盖。不把搜索无结果解释为无诉讼、无风险；查不到的字段写未知。不将历史AI判断写入本轮事实。

将取得的证据和字段填入JSON后使用 `scripts/company_check.py` 输出报告：

```bash
python scripts/company_check.py --input company_evidence.json --output-dir /workspace/output/company
```

输入：`company_name`；`source_kind` 为 `public_evidence` 或 `reconstructed_fixture`；`evidence` 列表每条包含 `id`、`subject_name`、`url`、`captured_at`、`text`；`fields` 列表每条包含 `name`、`value`、`status`（`supported`/`unknown`）、`evidence_ids`。公开模式要求实际HTTP来源；fixture模式是明示的实验资料。字段获支持必须引用同一公司证据，脚本检查并分离未知字段，输出MD与JSON和SHA清单。脚本不联网获取、推断或认证字段真实性。

阅读报告确认来源对象一致，逐字段复核原文支持力度；把司法/财务未覆盖项留在未知清单。用户后续要求尽调或估值时，继续用本次真实材料完成相应分析，不以固定分数/固定结论代替。
