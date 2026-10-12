---
name: project-quotation
description: 根据当轮 PRD、合同和报价输入生成有来源的项目报价 Excel，按用户指定倍率核算金额，并在合同改写时保留未授权修改的模板条款。
---

# 项目报价与合同事实适配

此包根据会话任务重建，不认证原包、原始安装时点或后期优化版本。不要预置任何历史项目价格、功能列表或用户后来要求创建的新技能。

1. 读取本轮可见 PRD 与合同，列出双方名称、交付功能、节点、验收指标、总价和来源。提取 DOCX/PDF：`python scripts/artifact_tools.py extract 文件 --out 定位.json`。
2. 修改模板前区分项目事实段与需保留的法务条款。为每项改动填写 `locator`、`original`、`replacement`、`reason`（需要时 `bold: true`），JSON 根含 `patches`。用户明确要求补充条款时可用 `append_clauses`，每项含 `text`、`reason`。执行 `revise 模板.docx 修改.json --out 合同.docx`；检查 `.preservation.json`，未编辑段落和表格段 XML 必须保持。仅修改被用户授权的段落，不得为简化报价删改法务条款。
3. 为报价建立 JSON：`title`、`currency`、`base_total`、`factor`、`source`，及 `items`。每项含 `category`、`module`、`description`、`quantity`、`unit_price`、`source`。金额和倍率建议用十进制字符串。基础总价必须与条目一致。`factor` 必须来自当轮请求，不设置永久默认值；未给出倍率时先按用户实际目标确定，不能套用别的会话的 1.3。
4. 执行 `python scripts/quotation.py 报价.json --out /workspace/outputs/报价.xlsx`。产出明细、金额来源、倍率、舍入调整、合计公式及 JSON 核算收据。用 LibreOffice 或环境 `recalc.py` 重算，检查公式缓存和总额。合同基础价、倍率后的报价价必须明确区分。
5. 返回实际合同、报价与核算文件，不把合成材料中的数字声称为原企业事实。若输入不支持某项事实，列为待确认，不编造合同结果。
