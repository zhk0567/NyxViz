"""Shared Chinese docx typography helpers."""
from __future__ import annotations

import re

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt


def normalize_cn(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+([，。；：、）】])", r"\1", text)
    text = re.sub(r"([（【])\s+", r"\1", text)
    text = re.sub(r"\s+→\s+", "→", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def parse_bold_runs(text: str) -> list[tuple[str, bool]]:
    """Split text into (segment, bold) preserving **markdown** markers."""
    parts: list[tuple[str, bool]] = []
    pos = 0
    for match in re.finditer(r"\*\*(.+?)\*\*", text):
        if match.start() > pos:
            parts.append((text[pos : match.start()], False))
        parts.append((match.group(1), True))
        pos = match.end()
    if pos < len(text):
        parts.append((text[pos:], False))
    if not parts:
        parts.append((text, False))
    cleaned: list[tuple[str, bool]] = []
    for segment, bold in parts:
        segment = normalize_cn(segment) if not bold else re.sub(
            r"`([^`]+)`", r"\1", segment
        ).strip()
        if segment:
            cleaned.append((segment, bold))
    return cleaned


def set_run_font(run, name: str = "宋体", size_pt: float = 10.5, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    r = run._element.get_or_add_rPr()
    r.rFonts.set(qn("w:eastAsia"), name)


def format_body_paragraph(paragraph, *, indent: bool = True, align=WD_ALIGN_PARAGRAPH.JUSTIFY) -> None:
    fmt = paragraph.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)
    fmt.alignment = align
    fmt.first_line_indent = Pt(21) if indent else Pt(0)


def style_table_cell(cell, *, bold: bool = False, size: float = 10.5) -> None:
    for para in cell.paragraphs:
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in para.runs:
            set_run_font(run, "宋体", size, bold=bold)


def count_text_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", normalize_cn(text)))
