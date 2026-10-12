#!/usr/bin/env python3
"""
Document Extractor for OpenClaw Karpathy Wiki

Extracts text content from various document files.
Outputs markdown-formatted text to stdout for LLM ingestion.

Usage:
    python doc_extractor.py <filepath>
    python doc_extractor.py <filepath> --max-pages 50
    python doc_extractor.py <filepath> --max-rows 10000

Supports:
    - PDF (.pdf) via PyMuPDF (pymupdf)
    - Excel (.xlsx) via openpyxl
    - Excel (.xls) via xlrd
    - Word (.docx) via python-docx
    - PowerPoint (.pptx) via python-pptx
    - RTF (.rtf) via striprtf
    - EPUB (.epub) via ebooklib + BeautifulSoup
    - OpenDocument (.odt/.ods/.odp) via odfdo
    - Images (.png/.jpg/.jpeg/.gif/.webp/.bmp) via EasyOCR (CJK+EN)
    - SVG (.svg) via inline text extraction, fallback to rasterization + OCR
"""

import argparse
import sys
import os
from pathlib import Path

# Global EasyOCR instance (singleton to avoid slow re-initialization)
_OCR_INSTANCE = None


def _get_ocr_instance():
    """Get or create a singleton EasyOCR instance. Initialization is expensive (~30s on first call)."""
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        try:
            import easyocr
            _OCR_INSTANCE = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        except ImportError:
            return None
    return _OCR_INSTANCE


def extract_image_ocr(filepath: str, confidence_threshold: float = 0.3) -> str:
    """Extract text from images using EasyOCR. Supports Chinese+English mixed content."""
    ocr = _get_ocr_instance()
    if ocr is None:
        return "[ERROR] EasyOCR not installed. Run: pip install easyocr"

    try:
        result = ocr.readtext(filepath, paragraph=False)
    except Exception as e:
        return f"[ERROR] OCR failed: {e}"

    if not result:
        return f"# {Path(filepath).name}\n\n- **Type**: Image (no text detected)\n\n---\n\n*(No recognizable text found in this image.)*"

    # result is a list of [bbox, text, confidence] tuples
    texts = []
    for detection in result:
        bbox, text, confidence = detection
        if confidence >= confidence_threshold:
            texts.append(text)

    if not texts:
        return f"# {Path(filepath).name}\n\n- **Type**: Image (text below confidence threshold {confidence_threshold})\n\n---\n\n*(No text met confidence threshold of {confidence_threshold}.)*"

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: Image (OCR)\n"
    header += f"- **Text lines**: {len(texts)}\n"
    header += f"- **Confidence threshold**: {confidence_threshold}\n\n---\n\n"

    return header + "\n".join(texts)


def extract_pdf(filepath: str, max_pages: int = 0) -> str:
    """Extract text from PDF using PyMuPDF with sort=True for reading order."""
    try:
        import pymupdf
    except ImportError:
        return "[ERROR] PyMuPDF not installed. Run: pip install PyMuPDF"

    doc = pymupdf.open(filepath)

    if doc.is_encrypted:
        doc.close()
        return "[ERROR] PDF is encrypted and cannot be read"

    pages_to_read = doc.page_count if max_pages == 0 else min(max_pages, doc.page_count)
    parts = []

    for i in range(pages_to_read):
        page = doc[i]
        text = page.get_text("text", sort=True)
        if text.strip():
            parts.append(f"## Page {i + 1}\n\n{text.strip()}")

    total_pages = doc.page_count
    doc.close()

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: PDF\n"
    header += f"- **Pages**: {total_pages}"
    if pages_to_read < total_pages:
        header += f" (extracted first {pages_to_read})"
    header += "\n\n---\n\n"

    return header + "\n\n".join(parts)


def extract_xlsx(filepath: str, max_rows: int = 0) -> str:
    """Extract data from .xlsx using openpyxl in read-only mode."""
    try:
        from openpyxl import load_workbook
    except ImportError:
        return "[ERROR] openpyxl not installed. Run: pip install openpyxl"

    wb = load_workbook(filepath, read_only=True, data_only=True)
    parts = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows_data = []
        row_count = 0

        for row in ws.iter_rows(values_only=True):
            if max_rows > 0 and row_count >= max_rows:
                break
            # Convert all cells to strings, handle None
            cells = [str(cell) if cell is not None else "" for cell in row]
            if any(cells):  # Skip completely empty rows
                rows_data.append("| " + " | ".join(cells) + " |")
                row_count += 1

        if rows_data:
            # Add markdown table header if we have data
            col_count = len(rows_data[0].split("|")) - 2  # Remove padding pipes
            separator = "| " + " | ".join(["---"] * col_count) + " |"
            parts.append(f"## Sheet: {sheet_name}\n\n{rows_data[0]}\n{separator}")
            parts.extend(rows_data[1:])

    wb.close()

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: Excel (.xlsx)\n"
    header += f"- **Sheets**: {', '.join(wb.sheetnames)}\n\n---\n\n"

    return header + "\n\n".join(parts)


def extract_xls(filepath: str, max_rows: int = 0) -> str:
    """Extract data from legacy .xls using xlrd."""
    try:
        import xlrd
    except ImportError:
        return "[ERROR] xlrd not installed. Run: pip install xlrd"

    wb = xlrd.open_workbook(filepath)
    parts = []

    for sheet_idx in range(wb.nsheets):
        sheet = wb.sheet_by_index(sheet_idx)
        rows_data = []

        for row_idx in range(sheet.nrows):
            if max_rows > 0 and row_idx >= max_rows:
                break
            cells = [str(sheet.cell_value(row_idx, col_idx)) for col_idx in range(sheet.ncols)]
            if any(c.strip() for c in cells):
                rows_data.append("| " + " | ".join(cells) + " |")

        if rows_data:
            col_count = sheet.ncols
            separator = "| " + " | ".join(["---"] * col_count) + " |"
            parts.append(f"## Sheet: {sheet.name}\n\n{rows_data[0]}\n{separator}")
            parts.extend(rows_data[1:])

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: Excel (.xls)\n"
    header += f"- **Sheets**: {', '.join(wb.sheet_names())}\n\n---\n\n"

    return header + "\n\n".join(parts)


def extract_docx(filepath: str) -> str:
    """Extract text from .docx using python-docx."""
    try:
        from docx import Document
    except ImportError:
        return "[ERROR] python-docx not installed. Run: pip install python-docx"

    doc = Document(filepath)
    parts = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            # Preserve heading levels
            style_name = para.style.name.lower() if para.style else ""
            if "heading 1" in style_name:
                parts.append(f"# {text}")
            elif "heading 2" in style_name:
                parts.append(f"## {text}")
            elif "heading 3" in style_name:
                parts.append(f"### {text}")
            else:
                parts.append(text)

    # Extract tables
    for i, table in enumerate(doc.tables):
        table_parts = []
        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]
            table_parts.append("| " + " | ".join(cells) + " |")
            if row_idx == 0:
                col_count = len(cells)
                table_parts.append("| " + " | ".join(["---"] * col_count) + " |")

        if table_parts:
            parts.append(f"\n## Table {i + 1}\n\n" + "\n".join(table_parts))

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: Word (.docx)\n"
    header += f"- **Paragraphs**: {len(doc.paragraphs)}\n\n---\n\n"

    return header + "\n\n".join(parts)


def extract_pptx(filepath: str) -> str:
    """Extract text from PowerPoint (.pptx) including slides, tables, and speaker notes."""
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        return "[ERROR] python-pptx not installed. Run: pip install python-pptx"

    prs = Presentation(filepath)
    parts = []

    def _extract_shape_text(shape) -> list:
        """Recursively extract text from shapes, including nested groups."""
        texts = []
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                texts.extend(_extract_shape_text(child))
            return texts
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if text:
                texts.append(text)
        return texts

    for slide_idx, slide in enumerate(prs.slides):
        slide_parts = []

        # Extract text from shapes (handles groups recursively)
        for shape in slide.shapes:
            shape_texts = _extract_shape_text(shape)
            if shape_texts:
                slide_parts.extend(shape_texts)

            # Extract tables
            if shape.has_table:
                table = shape.table
                table_rows = []
                for row_idx, row in enumerate(table.rows):
                    cells = [cell.text_frame.text.strip() for cell in row.cells]
                    table_rows.append("| " + " | ".join(cells) + " |")
                    if row_idx == 0:
                        col_count = len(cells)
                        table_rows.append("| " + " | ".join(["---"] * col_count) + " |")
                if table_rows:
                    slide_parts.append("\n" + "\n".join(table_rows))

        # Extract speaker notes
        if slide.has_notes_slide:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                slide_parts.append(f"\n**Speaker Notes**: {notes_text}")

        if slide_parts:
            parts.append(f"## Slide {slide_idx + 1}\n\n" + "\n\n".join(slide_parts))

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: PowerPoint (.pptx)\n"
    header += f"- **Slides**: {len(prs.slides)}\n\n---\n\n"

    return header + "\n\n".join(parts)


def extract_rtf(filepath: str) -> str:
    """Extract text from RTF (.rtf) using striprtf."""
    try:
        from striprtf.striprtf import rtf_to_text
    except ImportError:
        return "[ERROR] striprtf not installed. Run: pip install striprtf"

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            rtf_content = f.read()
        text = rtf_to_text(rtf_content, errors='ignore')
    except UnicodeDecodeError:
        # Fallback to cp1252 (common Windows RTF encoding)
        with open(filepath, 'r', encoding='cp1252', errors='replace') as f:
            rtf_content = f.read()
        text = rtf_to_text(rtf_content, errors='ignore')

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: RTF (.rtf)\n\n---\n\n"

    return header + text.strip()


def extract_epub(filepath: str) -> str:
    """Extract text from EPUB (.epub) using ebooklib + BeautifulSoup."""
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        return "[ERROR] ebooklib not installed. Run: pip install ebooklib"

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return "[ERROR] beautifulsoup4 not installed. Run: pip install beautifulsoup4"

    book = epub.read_epub(filepath)
    chapters = []

    # Iterate spine items (reading order, not filesystem order)
    for item in book.spine:
        # item is ('idref_string',) tuple from spine
        if isinstance(item, tuple):
            item_id = item[0]
        else:
            item_id = item
        chapter = book.get_item_with_id(item_id)
        if chapter and chapter.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(chapter.get_content(), 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            if text:
                chapters.append(text)

    # Fallback: if spine iteration yields nothing, try all document items
    if not chapters:
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            if text:
                chapters.append(text)

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: EPUB (.epub)\n"
    header += f"- **Chapters**: {len(chapters)}\n\n---\n\n"

    return header + "\n\n".join(chapters)


def extract_odf(filepath: str) -> str:
    """Extract text from OpenDocument formats (.odt/.ods/.odp) using odfdo."""
    try:
        from odfdo import Document
    except ImportError:
        return "[ERROR] odfdo not installed. Run: pip install odfdo"

    ext = Path(filepath).suffix.lower()
    doc = Document.open(filepath)
    parts = []

    if ext == '.odt':
        # Text document: extract paragraphs
        for paragraph in doc.body.paragraphs:
            text = paragraph.text.strip() if hasattr(paragraph, 'text') else str(paragraph).strip()
            if text:
                parts.append(text)

    elif ext == '.ods':
        # Spreadsheet: extract tables
        for table in doc.body.tables:
            table_rows = []
            for row_idx, row in enumerate(table.rows):
                cells = [(cell.text or '').strip() for cell in row.cells]
                table_rows.append("| " + " | ".join(cells) + " |")
                if row_idx == 0:
                    col_count = len(cells)
                    table_rows.append("| " + " | ".join(["---"] * col_count) + " |")
            if table_rows:
                parts.append(f"## Table: {table.name}\n\n" + "\n".join(table_rows))

    elif ext == '.odp':
        # Presentation: extract text from draw pages
        for page_idx, page in enumerate(doc.body.draw_pages):
            page_texts = []
            for frame in page.frames:
                if hasattr(frame, 'text_content'):
                    text = frame.text_content.strip()
                    if text:
                        page_texts.append(text)
            if page_texts:
                parts.append(f"## Slide {page_idx + 1}\n\n" + "\n\n".join(page_texts))

    else:
        # Generic fallback: try body text
        body_text = doc.body.text if hasattr(doc.body, 'text') else str(doc.body)
        if body_text:
            parts.append(body_text)

    # Try markdown conversion as fallback for ODT
    if not parts and ext == '.odt':
        try:
            from odfdo.document_to_markdown import document_to_markdown
            md = document_to_markdown(doc)
            if md and md.strip():
                return f"# {Path(filepath).name}\n\n- **Type**: OpenDocument (.odt)\n\n---\n\n{md}"
        except (ImportError, Exception):
            pass

    type_label = {"odt": "OpenDocument Text", "ods": "OpenDocument Spreadsheet", "odp": "OpenDocument Presentation"}.get(ext.lstrip('.'), "OpenDocument")

    header = f"# {Path(filepath).name}\n\n"
    header += f"- **Type**: {type_label} ({ext})\n\n---\n\n"

    return header + "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Extract text from documents for LLM ingestion")
    parser.add_argument("filepath", help="Path to the document file")
    parser.add_argument("--max-pages", type=int, default=0, help="Max PDF pages to extract (0=all)")
    parser.add_argument("--max-rows", type=int, default=0, help="Max Excel rows per sheet (0=all)")

    args = parser.parse_args()

    filepath = args.filepath
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    ext = Path(filepath).suffix.lower()

    extractors = {
        ".pdf": lambda: extract_pdf(filepath, args.max_pages),
        ".xlsx": lambda: extract_xlsx(filepath, args.max_rows),
        ".xls": lambda: extract_xls(filepath, args.max_rows),
        ".docx": lambda: extract_docx(filepath),
        ".pptx": lambda: extract_pptx(filepath),
        ".rtf": lambda: extract_rtf(filepath),
        ".epub": lambda: extract_epub(filepath),
        ".odt": lambda: extract_odf(filepath),
        ".ods": lambda: extract_odf(filepath),
        ".odp": lambda: extract_odf(filepath),
        # Image formats (OCR)
        ".png": lambda: extract_image_ocr(filepath),
        ".jpg": lambda: extract_image_ocr(filepath),
        ".jpeg": lambda: extract_image_ocr(filepath),
        ".gif": lambda: extract_image_ocr(filepath),
        ".webp": lambda: extract_image_ocr(filepath),
        ".bmp": lambda: extract_image_ocr(filepath),
        # SVG (inline text or rasterize + OCR fallback)
        ".svg": lambda: extract_svg(filepath),
    }

    extractor = extractors.get(ext)
    if extractor is None:
        print(f"[ERROR] Unsupported file type: {ext}. Supported: {', '.join(extractors.keys())}", file=sys.stderr)
        sys.exit(1)

    try:
        result = extractor()
        print(result)
    except Exception as e:
        print(f"[ERROR] Failed to extract {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
