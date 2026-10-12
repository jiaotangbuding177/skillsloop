#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run the EvoMind paper scan scaffold and optional paperconan numeric scan."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


TOOL_NAME = "EvoMind Paper-Data-Scan v1.0（EvoMind 自研审查流程）"
INSTITUTION = "EvoMind 学术质量审查实验室"
DOC_NO = "EM-REP-20260602-001"
CONFIDENTIALITY = "内部资料"
WARNING = "AI判断不能作为最终结果，需人工复核"
DATA_AUDIT_COMPONENT = "paperconan v0.5.0"


def sanitize_title(title: str) -> str:
    ascii_text = title.encode("ascii", errors="ignore").decode("ascii")
    ascii_text = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_text).strip("-._")
    digest = hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()[:8]
    if ascii_text:
        return f"{ascii_text[:80]}-{digest}"
    return f"paper-scan-{digest}"


def infer_title_from_pdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        metadata_title = ""
        if reader.metadata:
            metadata_title = (reader.metadata.title or "").strip()
        if metadata_title:
            return metadata_title
        first_text = (reader.pages[0].extract_text() or "").splitlines()
        for line in first_text[:12]:
            line = line.strip()
            if 6 <= len(line) <= 120 and not line.lower().startswith("abstract"):
                return line
    except Exception:
        pass
    return pdf_path.stem


def run_paperconan(scan_input: Path, title: str) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "paperconan", str(scan_input), "--md", "--title", title]
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        return False, f"Failed to run paperconan: {exc}"
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip()


def load_scan_summary(scan_json: Path) -> dict:
    if not scan_json.exists():
        return {
            "n_files": 0,
            "n_blocks_with_findings": 0,
            "severity": {},
            "kinds": [],
            "cross_sheet_count": 0,
            "digit_distribution_count": 0,
            "digit_fdr_significant": 0,
        }
    data = json.loads(scan_json.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    relations_blocks = data.get("relations_blocks", [])
    decimal_endings = data.get("decimal_endings", [])
    digit_distribution = data.get("digit_distribution", [])
    severity: dict[str, int] = {}
    kinds: dict[str, int] = {}
    bysheet: dict[str, dict[str, int]] = {}
    for finding in findings:
        sev = finding.get("severity", "unknown")
        kind = finding.get("kind", "unknown")
        sheet = finding.get("sheet", "unknown")
        severity[sev] = severity.get(sev, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1
        bysheet.setdefault(sheet, {})
        bysheet[sheet][sev] = bysheet[sheet].get(sev, 0) + 1
    for block in relations_blocks:
        sheet = block.get("sheet", "unknown")
        for item in block.get("identical_after_rounding", []):
            sev = item.get("severity", "unknown")
            kind = item.get("kind", "identical_after_rounding")
            severity[sev] = severity.get(sev, 0) + 1
            kinds[kind] = kinds.get(kind, 0) + 1
            bysheet.setdefault(sheet, {})
            bysheet[sheet][sev] = bysheet[sheet].get(sev, 0) + 1
    for item in decimal_endings:
        kind = "decimal_endings"
        sev = item.get("severity", "medium")
        severity[sev] = severity.get(sev, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1
    for item in digit_distribution:
        kind = "digit_distribution"
        sev = item.get("severity", "medium")
        severity[sev] = severity.get(sev, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "tool_version": data.get("tool_version") or data.get("version") or "unknown",
        "n_files": len(data.get("files", [])) if isinstance(data.get("files"), list) else data.get("n_files", 0),
        "n_blocks_with_findings": data.get("n_blocks_with_findings", len(bysheet)),
        "severity": severity,
        "kinds": sorted(kinds.items(), key=lambda item: (-item[1], item[0])),
        "cross_sheet_count": kinds.get("cross_sheet_duplicate", 0) + kinds.get("cross_sheet", 0),
        "digit_distribution_count": len(digit_distribution),
        "digit_fdr_significant": sum(1 for item in digit_distribution if item.get("fdr_significant") or item.get("q_value", 1) <= 0.05),
        "bysheet": bysheet,
    }


def copy_audit_outputs(scan_input: Path, report_dir: Path) -> Path:
    source_audit = scan_input / "audit"
    target_audit = report_dir / "audit"
    target_audit.mkdir(parents=True, exist_ok=True)
    if source_audit.exists():
        for item in source_audit.iterdir():
            if item.is_file():
                shutil.copy2(item, target_audit / item.name)
    return target_audit


def markdown_table_from_dict(values: dict[str, int]) -> str:
    if not values:
        return "| 项目 | 数值 |\n|---|---:|\n| 无 | 0 |"
    lines = ["| 项目 | 数值 |", "|---|---:|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def write_reports(
    report_dir: Path,
    title: str,
    paper: Path,
    source_data: Path | None,
    scan_summary: dict,
    paperconan_ok: bool,
    paperconan_log: str,
) -> None:
    auxiliary = report_dir / "auxiliary"
    auxiliary.mkdir(parents=True, exist_ok=True)
    generated = dt.date.today().isoformat()
    source_status = str(source_data) if source_data else "未提供独立源数据；仅扫描论文 PDF 可抽取表格。"
    severity_table = markdown_table_from_dict(scan_summary.get("severity", {}))
    kinds = scan_summary.get("kinds", [])
    kind_lines = ["| 类型 | 数量 |", "|---|---:|"] + [f"| {kind} | {count} |" for kind, count in kinds]
    kind_table = "\n".join(kind_lines) if kinds else "| 类型 | 数量 |\n|---|---:|\n| 无 | 0 |"

    zh = f"""# 《{title}》EvoMind 内部审查报告

生成日期：{generated}

| 字段 | 内容 |
|---|---|
| 审查工具 | {TOOL_NAME} |
| 数据审核组件 | {DATA_AUDIT_COMPONENT} |
| 审查机构 | {INSTITUTION} |
| 文档编号 | {DOC_NO} |
| 密级 | {CONFIDENTIALITY} |
| 论文文件 | `{paper}` |
| 源数据 | `{source_status}` |

**签核警示：{WARNING}**

## 一、整体结论

此文件为 OpenClaw 可运行脚本生成的审查骨架。OpenClaw agent 应在阅读全文后补充完整的论文基线、29 维审查矩阵、图表/源数据映射和综合判断。

当前脚本已完成本地文件预检、数据审核组件扫描尝试、辅助摘要和 Word 报告生成准备。

## 二、论文内容基线

待 OpenClaw agent 阅读全文后填写：题名、作者、年份、研究问题、方法、数据来源、核心结论、图表清单和主张链条。

## 三、29 维审查矩阵

| 类别 | 检查项 | 判断 | 说明 |
|---|---|---:|---|
| 创新性 | 创新点是否成立 | 待审查 | 需阅读全文后判断。 |
| 创新性 | 是否只是工程组合 | 待审查 | 需阅读全文后判断。 |
| 研究问题 | 问题是否真实 | 待审查 | 需阅读全文后判断。 |
| 理论逻辑 | 前后是否矛盾 | 待审查 | 需阅读全文后判断。 |
| 理论逻辑 | 推理是否成立 | 待审查 | 需阅读全文后判断。 |
| 理论逻辑 | 公式是否正确 | 待审查 | 需阅读全文后判断。 |
| 文献综述 | 是否漏引经典工作 | 待审查 | 需外部文献或全文判断。 |
| 文献综述 | 是否引用偏置 | 待审查 | 需外部文献或全文判断。 |
| 方法设计 | 方法是否合理 | 待审查 | 需阅读全文后判断。 |
| 方法设计 | 是否可复现 | 待审查 | 需结合源数据和方法描述判断。 |
| 实验设计 | Baseline是否充分 | 待审查 | 按论文类型判断。 |
| 实验设计 | 数据集是否合理 | 待审查 | 需结合数据来源判断。 |
| 实验设计 | 实验是否公平 | 待审查 | 需结合方法和分组判断。 |
| 实验设计 | 是否数据泄漏 | 待审查 | 按论文类型判断。 |
| 结果分析 | 数据是否自洽 | 待审查 | 需结合表格、图和源数据。 |
| 结果分析 | 是否统计显著 | 待审查 | 需复核统计输出。 |
| 结果分析 | 是否过度结论 | 待审查 | 需核对主张强度。 |
| 图片 | 图文是否一致 | 待审查 | 需检查图、图注和正文。 |
| 图片 | 图例是否正确 | 待审查 | 需检查图例、单位和标注。 |
| 图片 | 分辨率是否达标 | 待审查 | 需检查图像文件。 |
| 图片 | 是否存在造假 | 待审查 | 不得仅凭扫描器下结论。 |
| 表格 | 数据是否正确 | 待审查 | 需结合源数据复算。 |
| 表格 | 表文是否一致 | 待审查 | 需核对正文和表格。 |
| 写作 | 语言是否规范 | 待审查 | 需阅读全文后判断。 |
| 写作 | 术语是否统一 | 待审查 | 需阅读全文后判断。 |
| 写作 | 是否大量重复 | 待审查 | 需阅读全文后判断。 |
| 科研诚信 | 是否抄袭 | 未检测 | 需查重系统或外部数据库。 |
| 科研诚信 | 是否AI幻觉引用 | 待审查 | 需核查引用真实性。 |
| 整体性 | 是否形成完整故事闭环 | 待审查 | 需阅读全文后判断。 |

## 四、数据审核组件扫描摘要

扫描状态：{"成功" if paperconan_ok else "失败或未完成"}

| 指标 | 数值 |
|---|---:|
| 扫描文件数 | {scan_summary.get("n_files", 0)} |
| 有发现的表格块 | {scan_summary.get("n_blocks_with_findings", 0)} |
| cross_sheet_count | {scan_summary.get("cross_sheet_count", 0)} |
| digit_distribution_count | {scan_summary.get("digit_distribution_count", 0)} |
| digit_fdr_significant | {scan_summary.get("digit_fdr_significant", 0)} |

### 严重度统计

{severity_table}

### 发现类型统计

{kind_table}

### 运行日志

```text
{paperconan_log or "无"}
```

## 五、源数据与复现

源数据状态：{source_status}

若源数据缺失，不能据此直接判断论文造假，但应标记为可复现性限制。若源数据存在，OpenClaw agent 应把扫描发现映射到具体图、表、面板、统计方法和论文主张。

## 六、人工复核要求

{WARNING}
"""

    en = f"""# EvoMind Internal Review Report: {title}

Date: {generated}

| Field | Content |
|---|---|
| Review process | {TOOL_NAME} |
| Data audit component | {DATA_AUDIT_COMPONENT} |
| Institution | {INSTITUTION} |
| Document number | {DOC_NO} |
| Confidentiality | {CONFIDENTIALITY} |
| Paper file | `{paper}` |
| Source data | `{source_status}` |

**Sign-off warning: {WARNING}**

## Overall Note

This is a runnable scaffold generated by the OpenClaw-compatible package. The OpenClaw agent should read the full paper and complete the semantic baseline, 29-dimension matrix, source-data mapping, and integrated judgment.

## Data Audit Component Scan Summary

Status: {"success" if paperconan_ok else "failed or incomplete"}

| Metric | Value |
|---|---:|
| Files scanned | {scan_summary.get("n_files", 0)} |
| Blocks with findings | {scan_summary.get("n_blocks_with_findings", 0)} |
| cross_sheet_count | {scan_summary.get("cross_sheet_count", 0)} |
| digit_distribution_count | {scan_summary.get("digit_distribution_count", 0)} |
| digit_fdr_significant | {scan_summary.get("digit_fdr_significant", 0)} |

### Severity

{severity_table}

### Finding Types

{kind_table}

## Reproducibility

Source data status: {source_status}

Missing source data limits reproducibility but is not evidence of fabrication by itself. Scanner findings must be interpreted against the paper's methods, captions, tables, figures, and plausible benign explanations.

## Human Review Required

{WARNING}
"""

    (report_dir / "paper_data_scan_zh.md").write_text(zh, encoding="utf-8")
    (report_dir / "paper_data_scan_en.md").write_text(en, encoding="utf-8")

    numeric_zh = f"""# 数字扫描辅助摘要

数据审核组件：paperconan v0.5.0

扫描状态：{"成功" if paperconan_ok else "失败或未完成"}

{severity_table}

{kind_table}
"""
    numeric_en = f"""# Numeric Scan Auxiliary Summary

Data audit component: paperconan v0.5.0

Status: {"success" if paperconan_ok else "failed or incomplete"}

{severity_table}

{kind_table}
"""
    source_zh = f"""# 源数据清单

| 项目 | 状态 |
|---|---|
| 论文 | `{paper}` |
| 源数据 | `{source_status}` |
| paperconan 扫描 | {"成功" if paperconan_ok else "失败或未完成"} |

说明：缺少源数据时，应标记为可复现性限制，不应直接推断科研不端。
"""
    source_en = f"""# Source Data Inventory

| Item | Status |
|---|---|
| Paper | `{paper}` |
| Source data | `{source_status}` |
| paperconan scan | {"success" if paperconan_ok else "failed or incomplete"} |

Missing source data is a reproducibility limitation, not direct evidence of misconduct.
"""
    (auxiliary / "numeric_scan_summary_zh.md").write_text(numeric_zh, encoding="utf-8")
    (auxiliary / "numeric_scan_summary_en.md").write_text(numeric_en, encoding="utf-8")
    (auxiliary / "source_data_inventory_zh.md").write_text(source_zh, encoding="utf-8")
    (auxiliary / "source_data_inventory_en.md").write_text(source_en, encoding="utf-8")


def generate_docx(report_dir: Path) -> None:
    script_path = Path(__file__).resolve().parent / "generate_evomind_word_report.py"
    input_md = report_dir / "paper_data_scan_zh.md"
    output_docx = report_dir / "EvoMind_内部审查报告.docx"
    subprocess.run(
        [sys.executable, str(script_path), "--input", str(input_md), "--output", str(output_docx)],
        check=True,
    )


def generate_pdf(report_dir: Path) -> None:
    script_path = Path(__file__).resolve().parent / "generate_evomind_pdf_report.py"
    input_md = report_dir / "paper_data_scan_zh.md"
    output_pdf = report_dir / "EvoMind_内部审查报告.pdf"
    subprocess.run(
        [sys.executable, str(script_path), "--input", str(input_md), "--output", str(output_pdf)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True, help="Paper PDF/DOCX path")
    parser.add_argument("--source-data", default="", help="Optional source data or supplementary folder")
    parser.add_argument("--out-dir", default="reports", help="Output reports directory")
    parser.add_argument("--title", default="", help="Paper title, defaults to inferred PDF title or filename")
    parser.add_argument("--docx", action="store_true", help="Generate EvoMind DOCX report")
    parser.add_argument("--pdf", action="store_true", help="Generate EvoMind PDF report")
    args = parser.parse_args()

    paper = Path(args.paper).resolve()
    if not paper.exists():
        raise SystemExit(f"Paper file not found: {paper}")

    source_data = Path(args.source_data).resolve() if args.source_data else None
    if source_data and not source_data.exists():
        raise SystemExit(f"Source data folder not found: {source_data}")

    title = args.title.strip() or infer_title_from_pdf(paper)
    report_dir = Path(args.out_dir).resolve() / sanitize_title(title)
    report_dir.mkdir(parents=True, exist_ok=True)

    if source_data:
        scan_input = source_data
    else:
        scan_input = report_dir / "tmp_scan_input"
        scan_input.mkdir(parents=True, exist_ok=True)
        scan_ext = paper.suffix.lower() if paper.suffix else ".pdf"
        scan_name = f"article{scan_ext}"
        shutil.copy2(paper, scan_input / scan_name)

    ok, log = run_paperconan(scan_input, title)
    audit_dir = copy_audit_outputs(scan_input, report_dir)
    scan_summary = load_scan_summary(audit_dir / "scan.json")
    write_reports(report_dir, title, paper, source_data, scan_summary, ok, log)

    if args.docx:
        generate_docx(report_dir)
    if args.pdf:
        generate_pdf(report_dir)

    print(report_dir)


if __name__ == "__main__":
    main()
