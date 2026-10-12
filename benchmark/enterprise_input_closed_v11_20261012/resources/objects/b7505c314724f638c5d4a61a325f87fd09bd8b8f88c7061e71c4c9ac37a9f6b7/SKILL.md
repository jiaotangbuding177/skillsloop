---
name: contract-review
description: 系统化审查中国法域合同/协议/法律文书的纯法律视角流程（立场询问 → 合同类型识别 → 文本质量初审 → 条款初审 → 金额核算 → 条款冲突检测 → 风险分析 → 术语核对 → 合规审查 → Word 批注输出）。当用户说"审查/审阅/检查这份合同"或上传合同 PDF/Word/docx 文件请求审阅时触发。自动识别 9 类合同（采购/OEM代工/服务/建筑工程/NDA/技术开发/租赁/股权转让/跨境贸易），5 大专项自动化能力（合同类型识别、文本质量扫描、金额异常检测、条款冲突检测、合规清单审查），输出带原生批注的 Word 文档。
---

# Contract Review Skill · 合同审查

> **设计哲学**：把资深律师的合同审查工作流拆解为 7 个可复用的标准化阶段，每阶段对应独立的 references/ 知识库与产出物，最终交付一份**带 Word 原生批注**的审阅版合同。
>
> **核心边界**：**纯法律视角分析，不涉及商业层面的考量**。本 Skill 只评估条款的合法性、合规性、逻辑一致性，不评估商业合理性、议价空间、关系管理。

---

## 何时使用

**适用场景**：
- 用户说"审查这份合同"/"看看这份合同有什么问题"/"帮我审一下合同"
- 用户上传合同文件（PDF/Word/docx）并要求审阅
- 用户给出合同文本要求逐条分析
- **新增**：用户要求"算一下合同金额"/"查条款冲突"/"做合规审查"

**不适用场景**（明确告知边界）：
- 涉外合同（英美法 / 欧盟法 / 国际仲裁）→ 仅适用中国法域
- 律师意见签署 → 本 Skill 不具备执业律师资质
- 复杂股权架构 / 并购对赌设计 → 建议专业机构
- 信息源仅为合同文本本身（不做尽调）
- **新增**：商业合理性评估（不在 Skill 范围）

---

## 工作流（10 步）

### Step 0 · 澄清 + 解析

1. **确认文件类型**：合同 / 协议 / 规章 / 法律文书（Skill 适用全部 4 类，但默认聚焦合同）
2. **🆕 强制确认审查立场**：用 `AskUserQuestion` 调用，4 选 1（甲方 / 乙方 / 共同委托方法律顾问 / 中立第三方），**不得推断**——历史上曾因仅凭文件路径推断立场（如把 `D:\合同归档\某公司\` 当作"乙方视角"）导致审查方向偏差，必须强制询问
3. **🆕 自动识别合同类型**：调用 `scripts/detect_contract_type.py`，从合同标题、第一条、关键术语自动识别（9 类：采购/OEM代工/服务/建筑工程/NDA/技术开发/租赁/股权转让/跨境贸易）；未识别时仅跑通用规则
4. **解析文件**：
   - docx 文件 → 用 `officecli view text` 提取文本 + 段落定位
   - PDF/扫描件 → 调用 `textin-xparse` 解析
   - 纯文本粘贴 → 直接进入 Step 1

### Step 0.5 · 🆕 文本质量初审

- **加载**：`references/text-quality-checklist.md`
- **调用**：`scripts/check_text_quality.py` 自动扫描
- **4 大检查维度**：
  1. **标点符号**：中英文混用、引号一致性、顿号 vs 逗号、句末标点缺失
  2. **排版格式**：编号层级混乱（1/(1)/a 混用）、字体字号不统一（已发现合同宋体 10.5/11/12pt + Arial 混用）、Tab/空格冗余
  3. **错别字**：同音字、形近字、主谓不一致（已发现"甲方已支付的甲方货款"）、量词错误
  4. **语义歧义**：量词模糊（"相关/必要/合理"）、范围模糊（"等/包括但不限于"）、条件模糊（"如/视情况"）、主体指代不明
- **输出**：文本质量问题清单（定位 + 原文 + 类型 + 建议），独立于法律风险，作为合同可读性 / 严谨性评估
- **重要边界**：本步骤仅识别文本本身的问题，**不评价法律含义**——具体法律评价仍由 Step 1+ 处理

### Step 1 · 条款初审

- **加载**：`references/clause-checklist.md`（通用）+ `references/contract-types/{type}.md`（专项）
- **逐条扫描**：识别对审查立场明显不利的条款
- **输出问题清单**：每条含 ① 条款编号 ② 原文摘录 ③ 问题本质 ④ 修改建议

### Step 2 · 金额核算（🆕 专项自动化）

- **加载**：`references/financial-amounts.md`
- **识别 9 类金额**：合同总价 / 付款节点 / 违约金 / 赔偿金 / 逾期利息 / 税费 / 保证金 / 担保 / 费用调整
- **执行 10 项异常检测**：违约金 > 30% / 利息 > LPR 4 倍 / 保证金 > 20% 等
- **执行计算错误识别**：百分比累计 ≠ 100% / 加减错误 / 费率引用错误
- **输出**：
  - 金额汇总表（按类型/阶段/主体/风险 4 个维度）
  - 异常清单（Word 末尾表格）
  - 现金流时间线（按付款节点）

### Step 3 · 条款冲突检测（🆕 专项自动化 + 自适应）

- **加载**：`references/clause-conflict-detection.md` + `references/contract-type-detection.md`（合同类型专项规则库）
- **通用 5 大类冲突**（所有合同必跑）：
  1. **主体矛盾**：付款方与收款方主体错位（如"甲方向甲方付款"）、权责主体冲突、违约责任主体不一致
  2. **金额矛盾**：同一事项在不同条款中出现不同金额、比例、计算方式（如违约金 0.3%/日 vs 万分之三/日，差异 10 倍）
  3. **时间矛盾**：履行期限、有效期、起止日期前后不一致
  4. **权责矛盾**：同一事项在不同条款中既约定又否定、或归责主体相互冲突
  5. **术语矛盾**：同一概念在不同条款中使用不同定义或指代（如"产品"与"成品"混用）
- **🆕 合同类型专项冲突**（按 Step 0 识别结果动态加载）：
  - 采购：货权转移与结算节点冲突、验收标准前后矛盾
  - OEM 代工：知识产权归属与质量责任冲突、原材料/包材责任交叉冲突
  - 服务类：服务范围与 SLA 冲突、成果验收与付款节点冲突
  - 建筑工程：工程款支付节点与工期冲突、验收标准与违约金冲突
  - NDA：保密范围与例外条款冲突、保密期限与违约责任冲突
  - 技术开发：成果归属与背景 IP 冲突、技术指标与验收标准冲突
  - 租赁：租金调整机制与租期冲突、维修责任主体冲突
  - 股权转让：付款节点与交割条件冲突、估值调整条款冲突
  - 跨境贸易：贸易术语与风险转移冲突、关税承担与支付条款冲突
- **合同类型未识别时**：仅跑通用 5 大类，不强行套用专项规则，**必须在输出中标注"合同类型识别置信度低"**
- **输出**：
  - 冲突清单 JSON（含双侧条款定位 + 通用/专项分类）
  - 双向批注（每个冲突的 2 个条款处都插入引用对方的批注）
  - 冲突风险等级矩阵

### Step 4 · 风险分析

- **加载**：`references/risk-matrix.md`（高/中/低 等级标准）+ `references/law-sources.md`（法条索引）
- **检索法条**：调用 `fyopen-lawsearch` 检索相关法规与司法解释
- **每个风险点必标**：
  - 风险等级（高/中/低）
  - 法条引用（《民法典 §XXX》、《合同法司法解释一 §XX》等）
  - 应对方案（接受 / 谈判 / 拒绝）

### Step 5 · 术语核对

- **加载**：`references/terminology-glossary.md`
- **审查定义条款**：定义边界清晰性、无歧义、不存在被对方利用的解释空间
- **重点防范**：定义范围过宽 / 过窄导致的权利失衡

### Step 6 · 合规清单审查（🆕 强化深度）

- **加载**：`references/compliance-checklist.md`
- **检查维度**：
  - 通用合规（8 项必查）
  - 反垄断（经营者集中 + 横向协议 + 纵向限制）
  - 反不正当竞争（商业贿赂 + 商业秘密 + 搭售）
  - 数据合规（个保法 + 数据安全法 + AI 训练数据）
  - 反商业贿赂
  - 行业资质（工程/食品/医疗器械/药品/IP/跨境贸易）
  - 劳动用工专项
  - 关联交易（涉及上市公司）
  - 司法实践高频争议（阴阳合同 / 表见代理 / 格式条款等）
- **输出**：合规清单 JSON + Word 批注 + 末尾附录表格

### Step 7 · 输出 Word 批注

- **加载**：`references/output-format.md`（批注样式/作者/颜色规范）
- **执行脚本**：
  ```bash
  python "scripts/annotate_docx.py" \
    --input "{原合同.docx}" \
    --output "reviewed-{filename}.docx" \
    --comments-json "{审查意见 JSON}"
  ```
- **脚本内部**：封装 officecli `add comment`，用 `batch` 保证原子性
- **支持 7 类批注类型**（详见 output-format.md）：
  - `risk_high` / `risk_medium` / `risk_low`
  - `amount_anomaly`（🆕 金额异常）
  - `clause_conflict`（🆕 条款冲突）
  - `compliance_fail`（🆕 合规问题）
- **自检**：
  ```bash
  python "scripts/validate.py" --file "reviewed-{filename}.docx"
  ```
- **交付**：带原生批注的 Word 文档

---

## 硬规则（违反任何一条都视为不合格）

1. **每条审查意见必带四要素**：条款定位 + 原文摘录 + 风险等级 + 修改建议
2. **高风险条款必带三要素**：法条引用 + 量化损失预估 + 必标颜色 `#cf222e`
3. **金额异常批注必带**：异常类型 + 触发阈值 + 法条依据 + 修改建议
4. **条款冲突批注必带**：冲突 ID + 对方条款定位 + 冲突类型 + 法条依据
5. **不替代律师尽调**：明确告知用户边界，建议重大合同咨询执业律师
6. **风险等级判定严格遵循** `references/risk-matrix.md` 的量化标准
7. **数据来源必标**：法条引用 + 检索时点（调用 fyopen-lawsearch 后必带时间戳）
8. **纯法律视角**：不评价商业合理性、议价空间、关系管理

---

## 风险等级视觉规范

| 等级 | 颜色 | 批注开头标识 | 触发场景 |
|---|---|---|---|
| 🔴 高 | `#cf222e` | `【高风险】` | 可能导致 ≥10% 合同金额损失 / 重大违约 / 主体瑕疵 |
| 🟡 中 | `#9a6700` | `【中风险】` | 权利义务不对等 / 违约金偏离行业 20%+/ 管辖不利 |
| ⚪ 低 | `#d0d7de` | `【低风险】` | 表述瑕疵 / 格式问题 / 非关键优化 |
| 💰 金额异常 | `#bf8700` | `【金额异常】` | 9 类金额 + 10 项阈值检测（详见 financial-amounts.md） |
| ⚔️ 条款冲突 | `#8250df` | `【条款冲突】` | 5 大通用类 + N 类专项（详见 clause-conflict-detection.md） |
| ⚠️ 合规问题 | `#cf222e` | `【合规】` | 违反强制性规定 / 反垄断 / 数据合规等 |
| 📝 文本瑕疵 | `#8c959f` | `【文本瑕疵】` | 🆕 标点/排版/错别字/语义歧义（详见 text-quality-checklist.md） |

---

## 加载顺序（references/）

主 agent 必须按以下顺序读取：

1. `SKILL.md`（本文件）
2. `references/contract-type-detection.md` 🆕（合同类型自动识别规则库，Step 0 调用）
3. `references/text-quality-checklist.md` 🆕（4 维文本质量检查清单，Step 0.5 调用）
4. `references/contract-types/{type}.md` ← 按 Step 0 识别结果加载（采购/OEM代工/服务/建筑工程/NDA/技术开发/租赁/股权转让/跨境贸易）
5. `references/clause-checklist.md`（通用条款初审清单）
6. `references/financial-amounts.md`（金额核算规则）
7. `references/clause-conflict-detection.md`（🆕 含通用 5 类 + 按合同类型加载专项规则）
8. `references/risk-matrix.md`（风险等级判定标准）
9. `references/law-sources.md`（法条索引 + 调用 fyopen-lawsearch）
10. `references/terminology-glossary.md`（法律术语核对清单）
11. `references/compliance-checklist.md`（合规清单）
12. `references/output-format.md`（Word 批注输出规范）

---

## 与现有 Skill / 工具的协同

| Skill / 工具 | 用途 | 调用时机 |
|---|---|---|
| **officecli** | Word 批注生成、模板合并 | Step 7 输出 |
| **fyopen-lawsearch** | 法规 / 司法解释检索 | Step 2、4、6 法条引用 |
| **pkulaw**（如已连接） | 类案判决检索 | Step 4 修改建议增强 |
| **textin-xparse** | PDF / 扫描件解析 | Step 0 输入 |
| **browser-skill** | 未集成数据库的临时查询 | 兜底 |
| **calculate.exe / python** | 金额核算 + 异常检测 | Step 2 计算 |
| **westock-data** | 上市公司关联方识别 | Step 6 关联交易 |

**工具启用原则**：
- `fyopen-lawsearch`：默认集成（已有连接器）
- `pkulaw`：如未启用连接器，在 SKILL.md 提示用户启用
- 工具调用失败时，**降级方案** = 仅基于主模型常识 + `references/law-sources.md` 中预录的法条

---

## 边界

### Skill 能力边界

✅ 通用商业合同 / 协议 / 法律文书审查（9 类合同 + 通用法律文书）  
✅ 中国大陆法域  
✅ **5 大专项自动化能力**：合同类型识别（🆕）、文本质量扫描（🆕）、金额异常检测、条款冲突检测、合规清单审查  
✅ 输出 AI 辅助审查意见 + 修改建议  
✅ 纯法律视角（合法性、合规性、逻辑一致性、文本严谨性）

❌ 涉外合同（英美法 / 欧盟法 / 国际仲裁）  
❌ 律师意见签署（无执业律师资质）  
❌ 替代尽职调查（信息源仅为合同文本）  
❌ 复杂股权架构设计（建议专业机构）  
❌ **商业合理性评估**（议价空间、关系管理、市场分析）—— 不在 Skill 范围  

---

## 资源文件导览

```
contract-review/
├── SKILL.md                                ← 你正在读
├── assets/
│   └── contract-review-template.docx       ← 空白 Word 模板（含样式定义）
├── references/
│   ├── clause-checklist.md                 ← 12 类常见问题条款通用清单
│   ├── financial-amounts.md                ← 9 类金额 + 10 项异常阈值
│   ├── clause-conflict-detection.md        ← 5 类通用冲突 + 9 类合同专项冲突
│   ├── compliance-checklist.md             ← 通用+8 类专项合规清单
│   ├── risk-matrix.md                      ← 高/中/低 风险等级判定标准
│   ├── terminology-glossary.md             ← 20+ 法律术语核对清单
│   ├── law-sources.md                      ← 中国法律法规索引（民法典/司法解释）
│   ├── output-format.md                    ← Word 批注输出规范（含 7 类批注）
│   ├── contract-type-detection.md          ← 🆕 9 类合同自动识别规则 + 关键词库
│   ├── text-quality-checklist.md           ← 🆕 4 维文本质量检查清单
│   └── contract-types/                     ← 9 类合同专项清单
│       ├── sales-contract.md               ← 销售/买卖合同
│       ├── service-contract.md             ← 服务合同
│       ├── purchase-contract.md            ← 采购合同
│       ├── nda.md                          ← 保密协议
│       ├── employment-contract.md          ← 劳动合同
│       ├── equity-investment.md            ← 股权/投融资类合同
│       ├── oem-contract.md                 ← 🆕 OEM 代工合同
│       ├── construction-contract.md        ← 🆕 建筑工程合同
│       ├── lease-contract.md               ← 🆕 租赁合同
│       ├── tech-development-contract.md    ← 🆕 技术开发合同
│       └── cross-border-trade.md           ← 🆕 跨境贸易合同
└── scripts/
    ├── parse_contract.py                   ← 提取合同文本 + 段落定位
    ├── detect_contract_type.py             ← 🆕 自动识别合同类型（独立可调）
    ├── check_text_quality.py               ← 🆕 文本质量扫描（独立可调）
    ├── annotate_docx.py                    ← 批量插入 Word 原生批注（含 7 类批注模板）
    └── validate.py                         ← 输出前自检脚本
```

---

## 已知陷阱

1. **officecli 批注路径引用**：段落路径必须用 `/body/p[N]` 形式（1-based），N 为段落序号
2. **路径引号**：`/body/p[N]` 中的 `[N]` 在 bash 中需加引号 `'/body/p[3]'`
3. **fyopen-lawsearch 调用失败**：如连接器未启用，回退到 `references/law-sources.md` 预录法条
4. **Word 批注作者字段**：必须填 `"admin"`，否则 `validate.py` 校验失败
5. **大文档性能**：>100 页的合同建议分批批注，每批 ≤20 条
6. **PDF 扫描件**：必须先用 textin-xparse OCR，纯图片合同审查准确率会下降
7. **🆕 金额异常检测**：阈值是参考值，特殊行业（如建筑工程）需在合同类型清单中查阅
8. **🆕 条款冲突检测**：自动检测只覆盖"硬冲突"，"软冲突"（边界模糊）需人工复审
9. **🆕 合规清单**：涉及上市关联交易的，必须用 westock-data 验证关联方身份