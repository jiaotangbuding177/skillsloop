#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate an EvoMind branded internal review PDF from Markdown."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DEFAULT_TOOL = "EvoMind Paper-Data-Scan v1.0（EvoMind 自研审查流程）"
DEFAULT_DATA_AUDIT_TOOL = "paperconan v0.5.0"
DEFAULT_INSTITUTION = "EvoMind 学术质量审查实验室"
DEFAULT_DOC_NO = "EM-REP-20260602-001"
DEFAULT_CONFIDENTIALITY = "内部资料"
DEFAULT_HEADER = "EvoMind 内部审查报告"
DEFAULT_WARNING = "AI判断不能作为最终结果，需人工复核"


def register_font() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for font_path in candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("EvoMindCJK", str(font_path)))
            return "EvoMindCJK"
    return "Helvetica"


def markdown_text(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells if cell.strip())


def infer_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return title[:140]
    return fallback


def build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "EvoTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=20,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle("H1", parent=styles["Heading1"], fontName=font_name, fontSize=15, leading=20, spaceBefore=12),
        "h2": ParagraphStyle("H2", parent=styles["Heading2"], fontName=font_name, fontSize=13, leading=18, spaceBefore=10),
        "h3": ParagraphStyle("H3", parent=styles["Heading3"], fontName=font_name, fontSize=11.5, leading=16, spaceBefore=8),
        "body": ParagraphStyle("Body", parent=styles["BodyText"], fontName=font_name, fontSize=9.5, leading=14, alignment=TA_LEFT),
        "small": ParagraphStyle("Small", parent=styles["BodyText"], fontName=font_name, fontSize=8, leading=11),
        "warning": ParagraphStyle(
            "Warning",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#C00000"),
            spaceAfter=16,
        ),
    }


def header_footer(canvas, doc, font_name: str, institution: str, confidentiality: str) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFont(font_name, 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawCentredString(width / 2, height - 1.15 * cm, DEFAULT_HEADER)
    canvas.drawCentredString(width / 2, 0.8 * cm, f"{institution} | {confidentiality}")
    canvas.restoreState()


def add_cover(story: list, styles: dict[str, ParagraphStyle], args: argparse.Namespace, title: str) -> None:
    story.append(Spacer(1, 1.8 * cm))
    story.append(Paragraph("EvoMind 内部审查报告", styles["title"]))
    story.append(Paragraph(markdown_text(title), styles["title"]))
    story.append(Spacer(1, 0.6 * cm))
    rows = [
        ["审查工具", args.tool_name],
        ["数据审核组件", args.data_audit_tool],
        ["审查机构", args.institution],
        ["文档编号", args.doc_no],
        ["密级", args.confidentiality],
        ["生成日期", dt.date.today().isoformat()],
    ]
    data = [[Paragraph(markdown_text(str(cell)), styles["body"]) for cell in row] for row in rows]
    table = Table(data, colWidths=[4.0 * cm, 11.2 * cm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EDEDED")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(PageBreak())


def add_signoff(story: list, styles: dict[str, ParagraphStyle], institution: str) -> None:
    story.append(Paragraph("签核页", styles["title"]))
    story.append(Paragraph(DEFAULT_WARNING, styles["warning"]))
    data = [["签核角色", "姓名", "日期", "意见/签名"], ["初审", "", "", ""], ["复核", "", "", ""], ["批准", "", "", ""]]
    table = Table([[Paragraph(markdown_text(cell), styles["body"]) for cell in row] for row in data], colWidths=[3 * cm, 3 * cm, 3 * cm, 6 * cm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWHEIGHT", (0, 1), (-1, -1), 1.1 * cm),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"本报告由 {institution} 形成，仅作内部审查参考。", styles["body"]))
    story.append(PageBreak())


def add_markdown_table(story: list, rows: list[list[str]], styles: dict[str, ParagraphStyle]) -> None:
    if not rows:
        return
    max_cols = max(len(row) for row in rows)
    data = []
    for row in rows:
        data.append([Paragraph(markdown_text(row[i] if i < len(row) else ""), styles["small"]) for i in range(max_cols)])
    available_width = A4[0] - 4.4 * cm
    col_widths = [available_width / max_cols] * max_cols
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8B8B8")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.18 * cm))


def add_markdown(story: list, markdown: str, styles: dict[str, ParagraphStyle]) -> None:
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_table_row(lines[i])
                if not is_separator_row(cells):
                    rows.append(cells)
                i += 1
            add_markdown_table(story, rows, styles)
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            story.append(Paragraph(markdown_text(text), styles["h1" if level == 1 else "h2" if level == 2 else "h3"]))
        elif stripped.startswith(("- ", "* ")):
            story.append(ListFlowable([ListItem(Paragraph(markdown_text(stripped[2:].strip()), styles["body"]))], bulletType="bullet"))
        elif re.match(r"^\d+\.\s+", stripped):
            story.append(ListFlowable([ListItem(Paragraph(markdown_text(re.sub(r'^\d+\.\s+', '', stripped)), styles["body"]))], bulletType="1"))
        else:
            story.append(Paragraph(markdown_text(stripped), styles["body"]))
        i += 1


def generate_pdf(args: argparse.Namespace) -> Path:
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    markdown = source.read_text(encoding="utf-8")
    title = args.title or infer_title(markdown, "学术质量审查报告")
    font_name = register_font()
    styles = build_styles(font_name)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.6 * cm,
        title=title,
        author=args.institution,
    )
    story: list = []
    add_cover(story, styles, args, title)
    add_signoff(story, styles, args.institution)
    add_markdown(story, markdown, styles)
    doc.build(
        story,
        onFirstPage=lambda canvas, doc_: header_footer(canvas, doc_, font_name, args.institution, args.confidentiality),
        onLaterPages=lambda canvas, doc_: header_footer(canvas, doc_, font_name, args.institution, args.confidentiality),
    )
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input Markdown report path")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--title", default="", help="Optional report title")
    parser.add_argument("--tool-name", default=DEFAULT_TOOL)
    parser.add_argument("--data-audit-tool", default=DEFAULT_DATA_AUDIT_TOOL)
    parser.add_argument("--institution", default=DEFAULT_INSTITUTION)
    parser.add_argument("--doc-no", default=DEFAULT_DOC_NO)
    parser.add_argument("--confidentiality", default=DEFAULT_CONFIDENTIALITY)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(generate_pdf(args))


if __name__ == "__main__":
    main()
