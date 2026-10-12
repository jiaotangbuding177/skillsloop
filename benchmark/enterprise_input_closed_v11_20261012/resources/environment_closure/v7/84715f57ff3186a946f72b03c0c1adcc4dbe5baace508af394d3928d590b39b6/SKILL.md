---
name: legal-risk-context-reconstructed
description: 对合同、付款、劳动关系和企业权属等当前材料做证据索引与法律风险报告，给出有来源的问题分析及待核实事项；用于原名被遮蔽的法务技能环境替代。
---

# 证据与法律风险材料

原导出仅保留 `legal-ri***KEY***`，没有可确认的完整名称或原包。本包是明确命名的上下文重建替代，不能声称恢复原 `legal-risk-assessment`，也不能拿历史 AI 结论充当评测答案。

1. 确定当轮问题、用户立场、司法辖区与可见文件。按原文定位区分事实、主张、缺失证据和法律判断。用 `python scripts/artifact_tools.py extract 资料 --out 定位.json` 抽取段落、表格或 PDF 页。
2. 整理时间线、合同义务与履行证据。只有已提供证据才能认定事实；材料缺失时保留未知项。引用现行法律规则时查询官方法律文本并记录条文、版本与适用条件，不虚构司法记录或固定风险等级。
3. 报告 JSON 含 `title`、`standpoint`、`scope`、`unknowns`，`evidence` 每项含 `id`、`path`、`locator`、`quote`；`issues` 每项含 `issue`、`evidence_ids`、`analysis`、`action`。分析必须引用真实证据及所用法律依据，明确推断限度。
4. 执行 `python scripts/artifact_tools.py risk 分析.json --out /workspace/outputs/风险报告.docx`。脚本核对引用原文与实际文件，生成证据表、问题表和 Markdown；它不自动判定法律结论。若需改合同，另用 `revise`，按确切定位改动并核验未改条款 XML。
5. 核对文档实质内容，按用户格式交付。不得把“文件可打开”“证据引用匹配”表述成所有法律事实已核验。
