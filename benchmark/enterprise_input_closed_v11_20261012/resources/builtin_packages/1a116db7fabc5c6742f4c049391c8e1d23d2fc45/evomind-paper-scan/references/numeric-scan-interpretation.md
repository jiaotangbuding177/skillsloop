# Numeric Scan Interpretation

Numeric scanner output is a statistical anomaly signal, not a misconduct conclusion.

## Scanner Artifacts

Typical outputs:

- `scan.json`: structured findings for the agent to parse.
- `report.html`: user-facing highlighted evidence tables.
- `REPORT.md`: optional Markdown summary.

Always link these outputs in the final report when they exist.

## What To Surface First

1. Cross-sheet or cross-file same-position numeric overlap.
2. Cross-sheet value overlap across supposedly independent sheets/files.
3. Identical columns or many equal pairs within a data block.
4. Constant ratio, constant offset, exact linear relation, or suspicious derived values.
5. Within-column value duplication, repeated decimal endings, or missing last digits.
6. Sheet-level digit distribution anomalies.

Group findings by file, sheet, figure/table panel, and severity.

## Benign Explanations To Check

Before escalating a scanner finding, check the paper and source data for:

- Shared controls reused across panels.
- Combined panel and per-replicate breakdown of the same data.
- Normalization to a common baseline.
- Dose/time/index columns.
- Genomic coordinates, ranking, or count tables.
- Detection-limit censoring, zeros, or thresholded values.
- Formula-derived columns, unit conversion, or percentage complements.
- Correlation matrices, distance matrices, or dense derived tables.
- Repeated labels from multi-row headers or grouped table layout.

## Integrated Severity Guidance

Scanner severity is not final report severity.

- Scanner `high` + central claim + no benign explanation = likely `major` or `critical`.
- Scanner `high` + clear shared-control/derived-value explanation = `minor` or `note`.
- Scanner `medium` + paper-data contradiction = `major`.
- Scanner `low` usually stays hidden unless it supports a stronger finding.

## Required Wording

Use:

- "统计异常信号"
- "possible fabrication-risk signal"
- "requires manual verification against figure legend and Methods"
- "cannot determine intent from this evidence alone"

Avoid:

- "造假了"
- "fake/fraudulent paper"
- "作者编造数据"
- "实锤"
- public accusation language

## User-Facing Summary Pattern

```markdown
扫描了 N 个 source-data 文件，发现 K 条 high、M 条 medium、L 条 low 数值异常信号。这些是统计异常信号，不是造假结论。最需要优先人工核对的是：

1. `<file> :: <sheet/panel>`: <rule>. 论文对应位置：<figure/table/caption>. 可能解释：<benign explanation or missing>.
2. ...

下一步：打开 `report.html` 查看高亮单元格；回到论文 figure legend / Methods 核对共享对照、归一化、样本量和统计方法；必要时复算关键统计量。
```

