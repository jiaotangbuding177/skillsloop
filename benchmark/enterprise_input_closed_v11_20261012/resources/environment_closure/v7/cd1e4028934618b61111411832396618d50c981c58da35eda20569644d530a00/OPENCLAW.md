# OpenClaw Installation and Use

## Skill

`evomind-paper-scan`

## Purpose

Use this skill to review academic papers with source data, supplementary tables, figure data, or PDF-extracted tables. It produces EvoMind-branded internal review reports with a concise data-audit component label.

## Install

Copy the whole `evomind-paper-scan` folder into OpenClaw's skills directory.

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

The report identifies the data-audit component as `paperconan v0.5.0`.

## Recommended OpenClaw Prompt

```text
Use evomind-paper-scan to review this paper.

Paper:
<paper path>

Source data folder:
<source data folder, optional>

First read the whole paper and complete the 29-dimension review. Then run the data numeric scan and interpret the findings against the paper text, tables, figures, captions, methods, and source-data availability.

Generate Chinese and English Markdown reports, auxiliary summaries, and EvoMind Word/PDF internal review reports.
```

## Direct Runnable Command

```powershell
python .\scripts\run_evomind_paper_scan.py --paper "<paper.pdf>" --source-data "<source data folder>" --out-dir ".\reports" --title "<paper title>" --docx --pdf
```

Without source data:

```powershell
python .\scripts\run_evomind_paper_scan.py --paper "<paper.pdf>" --out-dir ".\reports" --docx --pdf
```

## Outputs

```text
reports/
  <paper-title>/
    paper_data_scan_zh.md
    paper_data_scan_en.md
    auxiliary/
      numeric_scan_summary_zh.md
      numeric_scan_summary_en.md
      source_data_inventory_zh.md
      source_data_inventory_en.md
    audit/
      scan.json
      REPORT.md
      report.html
    EvoMind_内部审查报告.docx
    EvoMind_内部审查报告.pdf
```

## Required Branding

- Review process: `EvoMind Paper-Data-Scan v1.0（EvoMind 自研审查流程）`
- Institution: `EvoMind 学术质量审查实验室`
- Confidentiality: `内部资料`
- Header: `EvoMind 内部审查报告`
- Footer: `EvoMind 学术质量审查实验室 | 内部资料`
- Warning: `AI判断不能作为最终结果，需人工复核`

## Safety

This skill is for academic review support. It must not make final misconduct determinations. All AI-generated conclusions require human review.
