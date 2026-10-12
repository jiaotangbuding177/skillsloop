#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate a branded EvoMind internal review report DOCX from Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


DEFAULT_TOOL = "EvoMind Paper-Data-Scan v1.0（EvoMind 自研审查流程）"
DEFAULT_DATA_AUDIT_TOOL = "paperconan v0.5.0"
DEFAULT_INSTITUTION = "EvoMind 学术质量审查实验室"
DEFAULT_DOC_NO = "EM-REP-20260602-001"
DEFAULT_CONFIDENTIALITY = "内部资料"
DEFAULT_HEADER = "EvoMind 内部审查报告"
DEFAULT_WARNING = "AI判断不能作为最终结果，需人工复核"


TOOL_NAME_PATTERNS = [
    r"\bpaper-data-scan\b",
    r"\bevomind-paper-data-scan\b",
    r"\bPaper-Data-Scan\b",
    r"\bEvoMind Paper-Data-Scan\b(?! v1\.0)",
]


def normalize_tool_names(text: str, tool_name: str) -> str:
    for pattern in TOOL_NAME_PATTERNS:
        text = re.sub(pattern, tool_name, text, flags=re.IGNORECASE)
    return text


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text: str, bold: bool = False, color: RGBColor | None = None) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(10.5)
    if color:
        run.font.color.rgb = color
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def set_margins(section) -> None:
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)
    section.header_distance = Cm(1.1)
    section.footer_distance = Cm(1.1)


def style_document(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)

    for style_name, size, bold in [
        ("Title", 22, True),
        ("Heading 1", 16, True),
        ("Heading 2", 13, True),
        ("Heading 3", 11.5, True),
    ]:
        style = doc.styles[style_name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = bold


def apply_header_footer(doc: Document, institution: str, confidentiality: str) -> None:
    footer_text = f"{institution} | {confidentiality}"
    for section in doc.sections:
        set_margins(section)
        header_para = section.header.paragraphs[0]
        header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_para.text = DEFAULT_HEADER
        header_para.runs[0].font.name = "Microsoft YaHei"
        header_para.runs[0]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        header_para.runs[0].font.size = Pt(9)
        header_para.runs[0].font.color.rgb = RGBColor(95, 95, 95)

        footer_para = section.footer.paragraphs[0]
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_para.text = footer_text
        footer_para.runs[0].font.name = "Microsoft YaHei"
        footer_para.runs[0]._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        footer_para.runs[0].font.size = Pt(9)
        footer_para.runs[0].font.color.rgb = RGBColor(95, 95, 95)


def add_cover(
    doc: Document,
    title: str,
    tool_name: str,
    data_audit_tool: str,
    institution: str,
    doc_no: str,
    confidentiality: str,
) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("EvoMind 内部审查报告")
    r.bold = True
    r.font.size = Pt(24)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.size = Pt(18)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    doc.add_paragraph("")
    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    rows = [
        ("审查工具", tool_name),
        ("数据审核组件", data_audit_tool),
        ("审查机构", institution),
        ("文档编号", doc_no),
        ("密级", confidentiality),
        ("生成日期", dt.date.today().isoformat()),
    ]
    for i, (key, value) in enumerate(rows):
        set_cell_text(table.cell(i, 0), key, bold=True)
        set_cell_shading(table.cell(i, 0), "EDEDED")
        set_cell_text(table.cell(i, 1), value)

    doc.add_page_break()


def add_signoff_page(doc: Document, institution: str) -> None:
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run("签核页")
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    warning = doc.add_paragraph()
    warning.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = warning.add_run(DEFAULT_WARNING)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(192, 0, 0)
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    doc.add_paragraph("")
    table = doc.add_table(rows=4, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    headers = ["签核角色", "姓名", "日期", "意见/签名"]
    for idx, header in enumerate(headers):
        set_cell_text(table.cell(0, idx), header, bold=True)
        set_cell_shading(table.cell(0, idx), "EDEDED")
    for row_idx, role in enumerate(["初审", "复核", "批准"], start=1):
        set_cell_text(table.cell(row_idx, 0), role)
        for col_idx in range(1, 4):
            set_cell_text(table.cell(row_idx, col_idx), "")

    note = doc.add_paragraph()
    note.add_run(f"本报告由 {institution} 形成，仅作内部审查参考。").bold = True
    doc.add_page_break()


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells if cell.strip())


def add_markdown_table(doc: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    max_cols = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=max_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(rows):
        for c_idx in range(max_cols):
            text = row[c_idx] if c_idx < len(row) else ""
            set_cell_text(table.cell(r_idx, c_idx), text, bold=(r_idx == 0))
            if r_idx == 0:
                set_cell_shading(table.cell(r_idx, c_idx), "EDEDED")
    doc.add_paragraph("")


def add_paragraph_with_inline_code(doc: Document, text: str, style: str | None = None) -> None:
    paragraph = doc.add_paragraph(style=style)
    parts = re.split(r"(`[^`]+`)", text)
    for part in parts:
        if not part:
            continue
        run_text = part[1:-1] if part.startswith("`") and part.endswith("`") else part
        run = paragraph.add_run(run_text)
        run.font.name = "Microsoft YaHei"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        if part.startswith("`") and part.endswith("`"):
            run.font.name = "Consolas"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
            run.font.size = Pt(9)


def add_markdown_content(doc: Document, markdown: str, tool_name: str) -> None:
    markdown = normalize_tool_names(markdown, tool_name)
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith("|") and "|" in stripped[1:]:
            raw_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_table_row(lines[i])
                if not is_separator_row(cells):
                    raw_rows.append(cells)
                i += 1
            add_markdown_table(doc, raw_rows)
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            if level == 1:
                doc.add_heading(text, level=1)
            elif level == 2:
                doc.add_heading(text, level=2)
            else:
                doc.add_heading(text, level=3)
            i += 1
            continue

        if stripped.startswith(("- ", "* ")):
            add_paragraph_with_inline_code(doc, stripped[2:].strip(), style="List Bullet")
            i += 1
            continue

        numbered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered:
            add_paragraph_with_inline_code(doc, numbered.group(1), style="List Number")
            i += 1
            continue

        add_paragraph_with_inline_code(doc, stripped)
        i += 1


def infer_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            title = re.sub(r"^《(.+?)》.*$", r"《\1》审查报告", title)
            return title
    return fallback


def generate_docx(args: argparse.Namespace) -> Path:
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    markdown = source.read_text(encoding="utf-8")
    title = args.title or infer_title(markdown, "学术质量审查报告")

    doc = Document()
    style_document(doc)
    set_margins(doc.sections[0])
    apply_header_footer(doc, args.institution, args.confidentiality)

    add_cover(
        doc,
        title=title,
        tool_name=args.tool_name,
        data_audit_tool=args.data_audit_tool,
        institution=args.institution,
        doc_no=args.doc_no,
        confidentiality=args.confidentiality,
    )
    add_signoff_page(doc, args.institution)
    add_markdown_content(doc, markdown, args.tool_name)

    # Ensure sections created by page breaks keep the required header/footer.
    doc.add_section(WD_SECTION.CONTINUOUS)
    apply_header_footer(doc, args.institution, args.confidentiality)

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input Markdown report path")
    parser.add_argument("--output", required=True, help="Output DOCX path")
    parser.add_argument("--title", default="", help="Optional report title")
    parser.add_argument("--tool-name", default=DEFAULT_TOOL)
    parser.add_argument("--data-audit-tool", default=DEFAULT_DATA_AUDIT_TOOL)
    parser.add_argument("--institution", default=DEFAULT_INSTITUTION)
    parser.add_argument("--doc-no", default=DEFAULT_DOC_NO)
    parser.add_argument("--confidentiality", default=DEFAULT_CONFIDENTIALITY)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output = generate_docx(args)
    print(output)


if __name__ == "__main__":
    main()
