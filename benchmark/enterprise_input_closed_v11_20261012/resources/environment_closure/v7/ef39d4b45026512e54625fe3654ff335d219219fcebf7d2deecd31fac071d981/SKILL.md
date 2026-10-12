---
name: evomind-paper-scan
description: OpenClaw-compatible EvoMind skill for academic paper quality review, 29-dimension paper audit, source-data/table numeric scanning, bilingual reporting, and professional Word DOCX internal review reports.
---

# EvoMind Paper Scan

`evomind-paper-scan` is an OpenClaw-compatible academic review skill. It combines:

- whole-paper 29-dimension quality review;
- paper/source-data/table consistency review;
- numeric anomaly scanning for data tables using `paperconan`;
- cautious research-integrity risk language;
- EvoMind-branded Markdown and Word internal reports.

## Branding

Use these exact defaults unless the user overrides them:

- Overall review process: `EvoMind Paper-Data-Scan v1.0（EvoMind 自研审查流程）`
- Review institution: `EvoMind 学术质量审查实验室`
- Document number: `EM-REP-20260602-001`
- Confidentiality: `内部资料`
- Header: `EvoMind 内部审查报告`
- Footer: `EvoMind 学术质量审查实验室 | 内部资料`
- Sign-off warning: `AI判断不能作为最终结果，需人工复核`

Use a concise component label in professional reports:

- Data audit component: `paperconan v0.5.0`

## Required Review Order

1. Confirm inputs: paper PDF/DOCX, source-data folder, supplementary files, desired language, and output folder.
2. Read the whole paper first. Identify title, author/year, field, research question, methods, tables, figures, claims, datasets, and source-data availability.
3. Complete the 29-dimension review using `references/29-dimension-checklist.md`.
4. Build a figure/table/source-data review queue.
5. Run numeric scan on source-data/supplementary tables when available.
6. Interpret numeric findings only through paper text, captions, methods, sample structure, and plausible benign explanations. Never treat scanner severity as final judgment.
7. Produce Markdown reports, auxiliary summaries, and DOCX/PDF internal reports if requested.

## Direct Script Usage

From the skill folder:

```powershell
python .\scripts\run_evomind_paper_scan.py --paper "<paper.pdf>" --source-data "<source data folder>" --out-dir ".\reports" --title "<paper title>" --docx --pdf
```

If no source-data folder exists, omit `--source-data`; the script will scan the PDF table extraction where possible and mark source data as missing.

The script creates:

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

## Output Rules

The main report must include:

- report metadata and EvoMind branding;
- paper identity and reviewed files;
- whole-paper baseline;
- 29-dimension quality matrix;
- source-data inventory;
- numeric scan summary;
- integrated findings comparing paper text, tables, figures, source data, and scanner output;
- limitations and next manual checks;
- red sign-off warning in DOCX.

## Integrity Language

Never conclude misconduct, fraud, fabrication, plagiarism, or author intent from scanner output alone. Use language such as:

- `possible fabrication risk`;
- `requires raw data confirmation`;
- `confirmed inconsistency`;
- `scanner finding with plausible benign explanation`;
- `source data unavailable, reproducibility limited`.

## Related Files

- `OPENCLAW.md`: OpenClaw installation and usage guide.
- `skill.yaml`: OpenClaw package metadata.
- `security.json`: local-only permissions and data-handling policy.
- `scripts/run_evomind_paper_scan.py`: direct runnable pipeline.
- `scripts/generate_evomind_word_report.py`: DOCX generator.
- `scripts/generate_evomind_pdf_report.py`: PDF generator.
- `references/29-dimension-checklist.md`: required review matrix.
- `references/numeric-scan-interpretation.md`: scanner interpretation guardrails.
