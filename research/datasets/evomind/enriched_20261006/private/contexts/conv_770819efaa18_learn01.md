# 论文复现材料可得性盘点

会话：conv_770819efaa18；候选：conv_770819efaa18:learn01

这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。

可学习线索：区分补充PDF/视频与原训练数据和程序，明确官方未提供何种材料，按DOI和具体需要请求作者

边界：关联为现有语义标注，不认证原始时间顺序；附件或实际交付与执行成效未核验；学习片段不等同已验证技能；领域规则和助手专业判断仍需独立核验

## 原筛选种子 · 用户

u_4074743bb831bfc9ad

请对【论文 / 稿件】进行 EvoMind 数据智审，重点检查【29 维质量评估 / 源数据一致性 / 表格数值 / 科研诚信风险】，输出word格式的 EvoMind 内部审查报告。

## 原筛选种子 · 用户

u_2f63d5c303e3499fb0

我在哪里可以查到并下载那些原始数据？

## 原筛选种子 · 用户

u_e8d38201068b8ec052

补充这些有用么？

## 原筛选种子 · AI

a_57434c8bea5b394d30

审查完成。以下是审查报告摘要和交付物清单：

---

## ✅ EvoMind 数据智审完成

**论文**: *Integrated sensing and communication based on space-time-coding metasurfaces* — Nature Communications 2025, 16:1836  
**DOI**: 10.1038/s41467-025-57137-6

### 审查结果概览

| 维度 | 评价 |
|------|------|
| 🟢 **strong** ×7 | 研究问题真实、方法设计合理、无数据泄漏、图文一致、写作规范、故事闭环完整 |
| 🟡 **adequate** ×15 | 创新性认可、理论逻辑成立、文献综述均衡、实验公平 |
| 🔴 **weak** ×4 | 创新边界不够清晰（工程组合）、**可复现性不足**、**Baseline 对比不足**、**缺乏统计显著分析** |
| ⚪ **unclear** ×1 | 图片造假可能性：无原始数据无法验证 |

### 4 个 Major 发现

1. **🔴 可复现性危机** — ANN 训练超参数未公开、FPGA 代码未提供、LabVIEW 程序未共享
2. **🔴 统计证据薄弱** — EVM/BER/DOA 估计均无误差条、无重复测量、无统计检验
3. **🔴 Baseline 不足** — 仅与 STCM 关闭对比，缺乏与传统 phased array / RIS-aided ISAC 的定量比较
4. **🔴 源数据完全图形化** — 全部 6 个主图仅以图形呈现，无原始数值表，无法独立验证

### 科研诚信
- ✅ 无抄袭或 AI 幻觉引用风险
- ⚠️ 与前作 (ref.63) 在 ANN+STCM DOA 估计上有方法重叠，需人工确认增量贡献边界

### 交付文件

报告位于成果文件夹：
```
EvoMind_内部审查报告.docx  ← Word 格式（47KB，含封面/签核页/29维矩阵/综合评估）
paper_data_scan_zh.md      ← 原始 Markdown 报告
audit/REPORT.md            ← 审计日志摘要
```

> **⚠️ 重要提示**: AI 判断不能作为最终结果，需人工复核。所有风险信号需结合原始数据进一步核实，本报告不构成对研究诚信的指控或背书。

## 原筛选种子 · AI

a_83f5df2ad156094301

查到了。情况很直接：

**论文没有公开的原始数据仓库。** 从 Nature Communications 官方页面看：

### 可以下载的内容（补充辅助材料）

| 文件 | 链接 |
|------|------|
| Supplementary Information (PDF) | ✅ 论文页面可下载 — 含 Supplementary Notes、补充图、补充表 |
| Supplementary Movie 1 (MP4) | ✅ 实验演示视频 |
| Transparent Peer Review file (PDF) | ✅ 审稿记录 |
| Description of Additional Supplementary Files (DOCX) | ✅ 补充文件说明 |

这些都在论文页面上：
> **https://www.nature.com/articles/s41467-025-57137-6**
>
> 页面右侧的 "Supplementary Information" 部分

### ⛔ 无法下载的

**原始测量数据、ANN 训练集、FPGA 代码、LabVIEW 程序** 均未公开。论文的 Data availability 声明原文：

> *"The data supporting the findings of this study are presented in the paper and in the Supplementary information **or can be made available upon request** by contacting the corresponding authors."*

Code availability 也是类似措辞。没有 Zenodo、Figshare、GitHub 等任何公开仓库。

### 要获取原始数据，需要

直接联系通讯作者发邮件索取：

| 作者 | 邮箱 |
|------|------|
| Lei Zhang (张磊) | ***@*** |
| Tie Jun Cui (崔铁军) | ***@*** |
| Marco Di Renzo | ***@*** |
| Vincenzo Galdi | ***@*** |

建议主联系 **张磊** 或 **崔铁军**（东南大学），附带论文 DOI 和具体需求（ANN 训练数据、暗室测量原始数据、FPGA 配置文件），说明用于学术验证目的。
