# 29-Dimension Paper Data Scan Checklist

Complete this matrix before deep source-data judgment. Use the user's exact categories and checks.

For every item, record:

- `rating`: strong | adequate | weak | unclear | not_applicable
- `severity`: critical | major | minor | note | none
- `paper evidence`: page, section, figure, table, equation, reference, or supplement
- `data evidence`: source-data file, sheet, table, cell/range, scanner finding, or missing file
- `reason`: concise explanation
- `recommended follow-up`: what to verify next

## Required 29 Items

| No. | Category | Check |
| --- | --- | --- |
| 1 | 创新性 | 创新点是否成立 |
| 2 | 创新性 | 是否只是工程组合 |
| 3 | 研究问题 | 问题是否真实 |
| 4 | 理论逻辑 | 前后是否矛盾 |
| 5 | 理论逻辑 | 推理是否成立 |
| 6 | 理论逻辑 | 公式是否正确 |
| 7 | 文献综述 | 是否漏引经典工作 |
| 8 | 文献综述 | 是否引用偏置 |
| 9 | 方法设计 | 方法是否合理 |
| 10 | 方法设计 | 是否可复现 |
| 11 | 实验设计 | Baseline是否充分 |
| 12 | 实验设计 | 数据集是否合理 |
| 13 | 实验设计 | 实验是否公平 |
| 14 | 实验设计 | 是否数据泄漏 |
| 15 | 结果分析 | 数据是否自洽 |
| 16 | 结果分析 | 是否统计显著 |
| 17 | 结果分析 | 是否过度结论 |
| 18 | 图片 | 图文是否一致 |
| 19 | 图片 | 图例是否正确 |
| 20 | 图片 | 分辨率是否达标 |
| 21 | 图片 | 是否存在造假 |
| 22 | 表格 | 数据是否正确 |
| 23 | 表格 | 表文是否一致 |
| 24 | 写作 | 语言是否规范 |
| 25 | 写作 | 术语是否统一 |
| 26 | 写作 | 是否大量重复 |
| 27 | 科研诚信 | 是否抄袭 |
| 28 | 科研诚信 | 是否AI幻觉引用 |
| 29 | 整体性 | 是否形成完整故事闭环 |

## How To Apply The Matrix

### Innovation

Check whether the claimed novelty is conceptually real and not only a routine assembly of known techniques, assays, datasets, or engineering components. Compare the abstract, introduction, related work, and claimed contributions against cited and missing prior work.

### Research Question

Check whether the problem is real, important, testable, and not invented only to fit available experiments or data. A real problem should have clear stakeholders, scientific uncertainty, or empirical consequences.

### Theory And Logic

Trace the paper's argument from assumptions to hypotheses to methods to results. Check internal contradictions, unsupported inference steps, and equations/formulas. If formulas are central, verify notation, dimensions, boundary conditions, and whether the derivation matches the implementation or experiment.

### Literature Review

Look for missing classic work, missing recent strong baselines, selective citation, self-citation bias, field mispositioning, and claims of novelty that ignore direct predecessors.

### Method Design

Evaluate whether methods are appropriate for the question, whether protocols or algorithms are reproducible, and whether the paper gives enough parameters, materials, software versions, preprocessing, and implementation details.

### Experimental Design

Check baselines, datasets, controls, fairness, leakage, sample overlap, repeated samples, train/test contamination, cohort leakage, batch effects, and whether comparisons answer the stated question.

### Result Analysis

Compare text claims, plots, tables, captions, statistical tests, source data, and scanner findings. Check self-consistency, statistical significance, effect sizes, uncertainty, correction for multiple comparisons, and whether conclusions exceed the evidence.

### Images

Check figure-text consistency, panel labels, legends, axes, units, scale bars, resolution, raw image availability, duplicated regions, splicing, reused panels, mirrored/cropped reuse, and whether schematic reuse is being confused with experimental image reuse.

### Tables

Check arithmetic, totals, percentages, units, labels, sample sizes, P values, and consistency between table text, paper text, supplementary tables, and source-data sheets.

### Writing

Check language quality, terminology consistency, repeated text, template artifacts, contradictory wording, and whether definitions remain stable across sections.

### Research Integrity

Check plagiarism signals, unverifiable references, hallucinated citations, source-data absence, unexplained anomalies, impossible values, and whether all integrity concerns are phrased as evidence-backed risks rather than allegations.

### Whole-Story Coherence

Judge whether the paper forms a coherent story: problem, hypothesis, method, evidence, result, limitation, and conclusion must align. A paper can have correct components but still fail if the chain does not close.

## Main Report Template

```markdown
# Paper Data Scan

## Paper Identity
- Title:
- DOI:
- Venue/year:
- Article type:
- Files reviewed:

## Whole-Paper Baseline
- Research question:
- Claimed innovation:
- Methods:
- Experimental/data system:
- Main claims:
- Main figures/tables:
- Statistical strategy:
- Source-data availability:

## 29-Dimension Matrix
| No. | Category | Check | Rating | Severity | Paper evidence | Data evidence | Reason | Recommended follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Figure/Table/Source-Data Inventory
| Item | Claim supported | Expected source data | Available source data | Scanner findings | Review priority |
| --- | --- | --- | --- | --- | --- |

## Numeric Scan Summary
- Scanner command:
- Output folder:
- Files scanned:
- High/medium/low finding counts:
- Cross-sheet/cross-file findings:
- Most important files/sheets:
- `report.html`:

## Integrated Findings
| Severity | Area | Paper location | Data location | Issue | Evidence | Interpretation | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Overall Verdict
- Overall quality:
- Strongest support:
- Weakest links:
- Highest-priority manual checks:
- Missing files needed:
```

