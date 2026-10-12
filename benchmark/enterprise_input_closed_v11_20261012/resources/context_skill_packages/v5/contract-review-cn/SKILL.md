---
name: contract-review-cn
description: 对中文合同按用户立场逐条审查，生成有原文定位、实质修订及理由的三栏对照 Word；使用同名公共包与独立文档适配，避免上游占位分析。
---

# 中文合同审查

已取得 ClawHub `lingmoon96-dev/contract-review-cn` 1.0.1 同名公开包。原包全文件保留在 `/workspace/reference_support/contract-review-cn-upstream/`。原始 `SKILL.md` 没有 frontmatter、安装指向未附的 requirements/template，原 analyzer 的修订原文和内容为占位。本入口为明确的公共包运行适配，不认证历史 EvoMind 包同字节，不把原 analyzer 的占位输出当真实审查。

1. 确定用户立场、当前合同和可见附件；用户未指定立场则按中立范围说明，不把另一来源的甲方/乙方立场带入。保持整份原合同上下文。
2. 执行 `python scripts/artifact_tools.py extract 合同.docx --out 条款.json`。支持 DOCX、PDF、TXT；旧 DOC 先用 LibreOffice 转换，扫描 PDF 先 OCR。抽取定位和 SHA，随后由当前 actor 根据真实条款审查价款、交付验收、权责、违约、知识产权、保密、解除及争议处理等适用事项。
3. 所有风险判断须有具体原文和依据；查法律时用官方文本、说明版本及适用条件。不得把无匹配条款或缺材料说成“低风险”。
4. 填写 JSON：`contract`（实际文件路径）、`standpoint`、`scope`、`unknowns`、`conclusion`，`findings` 每项含 `locator`、`original`（真实摘录）、`replacement`（具体新条文）、`reason`、`level`、`basis`。执行 `python scripts/artifact_tools.py review 审查.json --out /workspace/outputs/合同审查.docx`。脚本核对每条摘录并产生三栏表及 Markdown，不自动生成法律判断。
5. 用户需要把补充文字写进原合同时，另外准备 `patches`（`locator`、完整 `original`、`replacement`、`reason`、可选 `bold`）与 `append_clauses`（`text`、`reason`）。执行 `revise 原合同.docx 修改.json --out 修订合同.docx`。未改段落与表格 XML 应全部保留；新补条款加粗黑色。核实 `.preservation.json`，交付实际文件。

本适配复用当前 actor 的模型能力，不另外要求创建一个合同审查 API key。原包的公开示例只能作接口参考，不能作企业轨迹答案。
