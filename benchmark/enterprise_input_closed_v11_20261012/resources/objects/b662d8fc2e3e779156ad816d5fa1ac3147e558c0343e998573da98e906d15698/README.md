# Contract Review Skill · 合同审查

> 通用合同审查 Skill。系统化审查中国法域合同的 10 步流程，输出带 **Word 原生批注**的审阅版合同。

[![Skill Version](https://img.shields.io/badge/v2.0-10%20steps-blue)](#)
[![Coverage](https://img.shields.io/badge/contract_types-9-green)](#)
[![Output](https://img.shields.io/badge/output-Word%20%2B%20native%20comments-orange)](#)

---

## ✨ 核心特性

| 能力 | 说明 |
|---|---|
| **10 步工作流** | 类型识别 → 文本质量初审 → 条款初审 → 金额核算 → 冲突检测 → 风险分析 → 术语核对 → 合规审查 → 输出 |
| **7 类原生批注** | `risk_high` / `risk_medium` / `risk_low` / `amount_anomaly` / `clause_conflict` / `compliance_fail` / `text_quality` |
| **3 色视觉规范** | `#cf222e` 高风险 / `#9a6700` 中风险 / `#d0d7de` 低风险 |
| **10 项自检门禁** | 批注作者 / 风险分布 / 法条引用 / 检索时点 / 金额异常完整性 / 双向冲突 / 合规法条 / 文本瑕疵完整性 / 文本瑕疵隔离 |
| **纯法律视角** | 不评估商业合理性 / 议价空间 / 关系管理 —— 明确边界 |

---

## 📋 覆盖合同类型

| 类型 | 文档 | 专项清单 |
|---|---|---|
| 销售/买卖 | [sales-contract.md](references/contract-types/sales-contract.md) | 价格条款、交付验收 |
| 服务 | [service-contract.md](references/contract-types/service-contract.md) | 服务范围、SLA |
| 采购 | [purchase-contract.md](references/contract-types/purchase-contract.md) | 供应商管理、验收 |
| NDA | [nda.md](references/contract-types/nda.md) | 保密范围、例外情形 |
| 劳动 | [employment-contract.md](references/contract-types/employment-contract.md) | 工资、竞业、解除 |
| 股权/投融资 | [equity-investment.md](references/contract-types/equity-investment.md) | 对赌、回购、估值调整 |
| OEM 代工 | [oem-contract.md](references/contract-types/oem-contract.md) | 知识产权归属、包材责任 |
| 建筑工程 | [construction-contract.md](references/contract-types/construction-contract.md) | 工期、工程款、验收 |
| 租赁 | [lease-contract.md](references/contract-types/lease-contract.md) | 租金调整、维修责任 |
| 技术开发 | [tech-development-contract.md](references/contract-types/tech-development-contract.md) | 成果归属、背景 IP |
| 跨境贸易 | [cross-border-trade.md](references/contract-types/cross-border-trade.md) | 贸易术语、关税承担 |

---

## 🚀 快速开始

### 1. 安装（Installation）

**复制这段话给你的 AI 助手，它会自动帮你完成部署：**

> 请帮我安装 contract-review 合同审查技能：将 https://github.com/NOMOREKKK/contract-review-skill 克隆到本地，把其中 contract-review/ 目录（含 SKILL.md）安装到你的 skills 目录，完成后告诉我。

**或手动安装：**

```bash
git clone https://github.com/NOMOREKKK/contract-review-skill
cp -r contract-review/contract-review ~/.claude/skills/
```

**依赖**：Python 3.10+；Word 批注生成需要 officecli 工具（Windows）；可选 MCP 连接器：`fyopen-lawsearch`（法规检索）、`textin-xparse`（PDF/扫描件解析）。

### 2. 使用（Usage）

安装完成后，直接对你的 AI 助手说：

> "审查这份合同"
> "看看这份合同有什么问题"
> "帮我审一下这份合同"

并上传合同文件（PDF/Word/docx），Skill 会自动启动 10 步审查流程，交付带原生批注的 Word 文档。

**命令行调用**（适合自动化/批量场景）：

```bash
# 1. 插入 Word 批注
python scripts/annotate_docx.py \
  --input "原合同.docx" \
  --output "reviewed-原合同.docx" \
  --comments-json "审查意见.json"

# 2. 输出前自检
python scripts/validate.py --file "reviewed-原合同.docx"
```

---

## 📂 仓库结构

```
contract-review/
├── SKILL.md                              ← 主入口（Skill 加载）
├── README.md                             ← 本文件
├── .gitignore
├── assets/
│   └── contract-review-template.docx     ← 空白 Word 模板
├── references/                           ← 知识库（按需加载）
│   ├── clause-checklist.md               ← 通用条款初审清单
│   ├── financial-amounts.md              ← 🆕 9 类金额 + 10 项异常阈值
│   ├── clause-conflict-detection.md      ← 5 类通用冲突 + 9 类合同专项冲突
│   ├── compliance-checklist.md           ← 通用 + 8 类专项合规
│   ├── risk-matrix.md                    ← 风险等级判定标准
│   ├── terminology-glossary.md           ← 法律术语核对清单
│   ├── law-sources.md                    ← 中国法律法规索引
│   ├── output-format.md                  ← Word 批注输出规范
│   ├── contract-type-detection.md        ← 🆕 9 类合同自动识别规则
│   ├── text-quality-checklist.md         ← 🆕 4 维文本质量检查清单
│   └── contract-types/                   ← 11 类合同专项清单
└── scripts/                              ← 自动化工具
    ├── parse_contract.py                 ← 提取合同文本 + 段落定位
    ├── detect_contract_type.py           ← 🆕 自动识别合同类型
    ├── check_text_quality.py             ← 🆕 文本质量扫描
    ├── annotate_docx.py                  ← 批量插入 Word 原生批注（7 类）
    └── validate.py                       ← 输出前自检（10 项）
```

---

## 🔌 依赖

### 必需
- **Python 3.10+**
- **officecli** —— Word 批注生成

### 推荐 MCP 连接器
- `fyopen-lawsearch`（默认）—— 法规检索
- `pkulaw`（可选）—— 类案判决检索
- `textin-xparse`（可选）—— PDF / 扫描件解析

---

## 📝 审查意见 JSON 模板

```json
{
  "comments": [
    {
      "paragraph_index": 9,
      "type": "risk_high",
      "clause_no": "9",
      "title": "违约金比例过高",
      "essence": "违约金达合同总价 30%，超过合理范围",
      "law": "《民法典》第 585 条",
      "loss_estimate": "潜在损失约 300 万元",
      "suggestion": "建议降至 20%",
      "modify_text": "任一方违约的，应支付合同总价 20% 的违约金",
      "search_date": "2026-08-06"
    },
    {
      "paragraph_index": 5,
      "type": "amount_anomaly",
      "title": "付款比例累计错误",
      "anomaly_type": "计算错误（百分比累计）",
      "value": "30% + 40% + 20% = 90%",
      "threshold": "付款比例之和应为 100%",
      "law": "无",
      "suggestion": "建议修正为 30% + 50% + 20% = 100%"
    },
    {
      "paragraph_index": 7,
      "type": "clause_conflict",
      "title": "违约金 vs 免责冲突",
      "conflict_id": "CONF-001",
      "other_clause_no": "8",
      "conflict_type": "违约责任 vs 免责条款",
      "law": "《民法典》第 590 条",
      "suggestion": "明确免责范围仅限不可抗力"
    },
    {
      "paragraph_index": 11,
      "type": "compliance_fail",
      "title": "未约定个人信息处理授权",
      "compliance_domain": "数据合规（个人信息）",
      "severity": "高",
      "law": "《个人信息保护法》第 13、29 条",
      "suggestion": "增加个人信息处理授权条款"
    }
  ]
}
```

---

## 🛡️ 边界与免责

### ✅ 适用
- 中国大陆法域的合同、协议、法律文书
- 9 类常见商业合同 + 通用法律文书
- 纯法律视角的合规性、一致性审查

### ❌ 不适用
- 涉外合同（英美法 / 欧盟法 / 国际仲裁）
- 律师意见签署（无执业律师资质）
- 替代尽职调查（信息源仅为合同文本）
- 复杂股权架构设计（建议专业机构）
- **商业合理性评估**（议价空间、关系管理、市场分析）

---

## 📜 License

MIT License

---

## 🙏 致谢

基于资深律师的合同审查工作流设计。