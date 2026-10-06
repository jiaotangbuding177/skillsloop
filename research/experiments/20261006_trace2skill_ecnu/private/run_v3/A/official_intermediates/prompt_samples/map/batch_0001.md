===== PROMPT SAMPLE START =====

PHASE: map

LABEL: batch_0001



===== SYSTEM MESSAGE 1 START =====

你是Trace2Skill的局部补丁提议者。基于输入的历史经验记录，对同一个初始表格技能目录提出少量最小修改；不是为每条经验生成一个技能。
企业历史适配边界：这些记录不是统一的失败日志或成功日志。保留明确用户要求、未验证参考方法、局部错误/修订及UNKNOWN整体结果；不把候选经验升级为已验证成功。不同任务条件/用户范围不混用，不把实例数值固定为普遍规范；遇到矛盾保留条件和未知。输出中文技能正文，可操作且有适用范围；不凭skill名称编造其内部实现，不链接不存在的历史文件、工具脚本或KM路径。依赖能力须说明。来源ID作为依据说明保留，但不要复制整段企业正文。
只针对当前SKILL.md中实际存在的标题/文本提补丁，修改总量克制。可使用SKILL.md或references下的直接.md文件，禁止脚本、外部绝对路径。references新文件须同时补上正文链接。不修改YAML名称/描述和基础定位，不删除整体未知边界。允许无适合改进时edits=[]。
## Output Format

Respond with JSON in a fenced `json` block:

```json
{"reasoning":"2-3 sentences: what grounded experiences you see and what bounded changes they support","edits":[{"file":"SKILL.md","op":"append_to_section","target_section":"## Section Name","content":"new content to add"}],"changelog_entries":["Brief description of change"]}
```

Supported operations:
- "insert_after": insert content after target_text within target_section
- "insert_before": insert content before target_text within target_section
- "append_to_section": append content at end of target_section
- "replace_in_section": replace old_text with content within target_section
- "add_section": add new section (use after_section for placement)
- "delete_section": remove target_section entirely
- "create": create a new file (file + content)
- "delete_file": delete a file

CRITICAL: Propose MINIMAL, TARGETED edits. Each edit should be a few lines of content, not entire sections. Multiple small edits > one large rewrite.

IMPORTANT — file creation rule: if you propose a "create" op for a new references/*.md file, you MUST also include an edit to SKILL.md (or the relevant parent file) that adds a link and a brief description of when to read the new file. Likewise, a "delete_file" op MUST be paired with an edit that removes the corresponding link from SKILL.md.


===== SYSTEM MESSAGE 1 END =====



===== USER MESSAGE 1 START =====

{"batch_count":3,"batch_index":1,"initial_skill_files":{"SKILL.md":"---\nname: spreadsheet-generation-audit\ndescription: 根据用户明确要求处理与核验表格，整理可参考的操作方法及其适用边界。\n---\n\n# 表格生成与核验\n\n## 适用范围\n用于用户提供表格或明确数据结构后的表格处理；具体数据、映射和验收要求由本次任务给出。\n\n## 工作流程\n1. 阅读用户目标、输入结构和交付要求。\n2. 根据本次任务处理表格。\n3. 对照用户要求检查并保存结果。\n\n## 证据与边界\n历史经验是参考材料，不代表本次任务必然成功。不可见的文件内容、技能内部实现和业务结果保持未知。\n\n## 依赖\n实际执行时需要可用的表格读写工具；生成此技能不等于已经安装这些工具。\n\n"},"max_skill_lines":500,"records":[{"instance_id":"conv_9b78a49bd169","items":[{"conditions":["源文件与目标模板采用不同的会计准则或报表格式","任务要求数据正确填入特定模板"],"content":"当源报表（如小企业会计准则）与目标模板（如财会〔2019〕6号）格式不一致时，需先建立详细的科目映射表（如货币资金、实收资本、管理费用等），明确哪些科目直接对应、哪些需要整合，避免机械照搬。此方法在本次任务中被明确执行。","evidence_status":"VISIBLE_METHOD_UNVERIFIED","limitations":["具体映射规则的正确性依赖助手专业知识，未经独立第三方验证"],"source_ids":["m005","m007","m013"],"title":"财务报表跨准则映射需先理清差异"},{"conditions":["目标文件是包含公式计算的Excel模板","要求保留模板原始结构和计算逻辑"],"content":"在填入数据前，必须检查目标模板是否包含自动汇总公式、合并单元格或灰色锁定区域。策略是仅填入叶子节点（明细行）数据，保留模板自带的合计、小计公式及格式，防止破坏公式逻辑或样式。","evidence_status":"VISIBLE_METHOD_UNVERIFIED","limitations":["需确保openpyxl等库能正确读取公式结构而不破坏它，实际保存效果依赖于工具链"],"source_ids":["m005","m006","m011"],"title":"识别模板公式与合并单元格结构"},{"conditions":["生成的表格包含需要计算的公式（如合计行）","环境可用LibreOffice或等效的无头电子表格引擎"],"content":"生成Excel文件后，不直接信任Python库保存后的值，而是使用LibreOffice等外部引擎重新计算文件，读取回缓存值或最终结果。这一步用于验证填入数据后公式是否正确计算，以及格式是否兼容。","evidence_status":"VISIBLE_METHOD_UNVERIFIED","limitations":["未验证具体重算脚本的代码实现，仅观察到操作意图和后续状态更新"],"source_ids":["m007","m008","m011"],"title":"使用LibreOffice重算验证公式结果"},{"conditions":["任务要求确保数据正确且通过勾稽关系检查","涉及资产负债表、利润表、现金流量表的联动"],"content":"在交付前，编写脚本独立验证财务报表的内部逻辑一致性。关键勾稽关系包括：资产负债表平衡（资产=负债+所有者权益）、资产负债表期末现金与现金流量表期末现金一致、未分配利润变动与净利润匹配、实收资本变动与筹资现金流匹配等。","evidence_status":"OBSERVED_LOCAL_FAILURE","limitations":["助手曾出现列映射错误（误将2024年末当作2026H1期初），表明自动化校验脚本对时间维度的定义需高度精确"],"source_ids":["m009","m010","m013"],"title":"三表勾稽关系的程序化校验"},{"conditions":["模板要求覆盖多个财政年度","目标主体在部分覆盖年度尚未成立"],"content":"若填报须知要求填报连续多年数据，但公司注册时间晚于起始年份，需将注册前的年份数据置为0或初始值，而非留空或报错。本任务中，合生纪康成立于2025年，因此2023-2024年数据被强制填为0。","evidence_status":"USER_REQUIREMENT","limitations":["具体置零还是留空取决于具体填报须知，此处依据助手对“填报须知”的解读"],"source_ids":["m001","m013"],"title":"根据注册时间处理空年份数据"}],"task_outcome":"UNKNOWN","uncertainties":["助手是否真正通过LibreOffice成功执行了重算脚本（工具日志中未直接展示LibreOffice命令的执行细节，仅在助手叙述中提及）","勾稽关系校验脚本的具体代码逻辑及修正后的最终运行输出未展示","最终生成的Excel文件中的具体数值和公式状态无法直接通过提供的文本日志完全验证"]},{"instance_id":"conv_7f5a1845d742","items":[{"conditions":["生成包含计算逻辑的Excel表格","需要确保公式结果准确且无引用错误"],"content":"在生成含公式的评分表时，需确保数据起始行与公式引用行严格一致（如数据从第4行开始则公式不能引用第5行），并在交付前使用LibreOffice进行重算以覆盖文件并验证零错误。此方法为助手内部执行过程描述，未通过工具日志直接证实具体命令行参数，但作为表格核验的标准流程具有参考价值。","evidence_status":"VISIBLE_METHOD_UNVERIFIED","limitations":["未展示具体的LibreOffice命令行调用细节","未提供修正前后的代码对比证据"],"source_ids":["m002"],"title":"Excel公式行号对齐与LibreOffice重算验证"},{"conditions":["设计包含权重和原始得分的计算表格","最终输出需符合特定的分数范围（如0-100）"],"content":"在构建多维度加权评分模型时，明确将总分口径统一为百分制（权重×得分×10），以避免因小数点或百分比格式导致的理解偏差。这是针对特定业务场景（展会评估）的表格结构设计经验。","evidence_status":"OBSERVED_LOCAL_FAILURE","limitations":["仅观察到助手声称修正了口径，未看到修正前的错误状态及具体代码实现"],"source_ids":["m002"],"title":"加权评分表的百分制统一口径"},{"conditions":["环境中预装Python库不可用或版本混乱","需要读取.docx/.xlsx等非纯文本文件内容"],"content":"当遇到pip与python版本不匹配导致库安装失败或导入异常时（如ModuleNotFoundError: No module named 'docx'），应首先诊断系统默认python3版本与pip关联的版本是否一致，若无法快速修复，可考虑改用Node.js生态（如exceljs/docx）或直接解析底层XML/JSON结构作为替代读取方案。","evidence_status":"OBSERVED_LOCAL_FAILURE","limitations":["工具记录显示安装尝试失败，后续成功读取的具体技术路径未在工具日志中完全展开，仅见于助手叙述"],"source_ids":["tool001","m002"],"title":"Python环境依赖冲突的诊断与替代方案"}],"task_outcome":"UNKNOWN","uncertainties":["工具日志仅记录了首次python-docx安装失败的报错，未记录后续成功提取邀请函内容、生成Excel表格及LibreOffice重算的具体命令执行过程，因此‘表格生成与核验’的核心成功步骤缺乏直接的工具级证据支持。","助手提到的‘run_manifest.json’审计机制及‘部门共享工作区草稿目录’的文件复制操作，在提供的工具记录中未见对应文件系统操作的快照。"]}]}


===== USER MESSAGE 1 END =====



===== ASSISTANT MESSAGE 1 START =====

```json
{
  "reasoning": "历史经验强调了在生成含公式的Excel表格时，需特别注意公式引用行的对齐、模板结构的保留（不破坏合并单元格/锁定区域）以及使用外部引擎（如LibreOffice）进行重算验证以捕捉潜在错误。同时，跨准则映射和空数据处理提供了具体的填充策略参考。现有技能较为通用，建议增加针对‘模板结构保留’、‘公式重算验证’及‘数据填充规范’的操作细节，但不改变其基础定位。",
  "edits": [
    {
      "file": "SKILL.md",
      "op": "append_to_section",
      "target_section": "## 工作流程",
      "content": "   - **模板结构检查**：若使用现有模板，需识别合并单元格、锁定区域及自动汇总公式。仅向明细行（叶子节点）填入数据，避免覆盖公式或破坏格式。\n   - **数据填充规范**：对于时间序列数据，若填报主体在部分年份不存在，根据填报须知明确是置为0/初始值还是留空；跨格式/准则填报时，需先建立科目映射表，避免机械照搬。\n   - **公式与重算验证**：对于含公式的表格，确保数据起始行与公式引用行严格一致。生成后，若环境允许，建议使用LibreOffice等外部引擎重算文件并读取结果，以验证公式计算逻辑及兼容性。"
    }
  ],
  "changelog_entries": [
    "在工作流程中补充了模板结构检查（保留公式/合并单元格）、数据填充规范（空年份处理/映射表）及公式重算验证的具体操作建议。"
  ]
}
```


===== ASSISTANT MESSAGE 1 END =====



===== PROMPT SAMPLE END =====
