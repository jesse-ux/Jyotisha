#!/usr/bin/env python3
"""Export the chart research book root to a simple readable PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


FONT_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
    ("/Library/Fonts/Arial Unicode.ttf", 0),
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export chart research book root to PDF")
    parser.add_argument(
        "--report-root",
        default="docs/reports/chart_research_REDACTED_DATE_REDACTED_TIME",
        help="Path to the chart research report root",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output PDF path; defaults to <report-root>/exports/chart_research_REDACTED_DATE_REDACTED_TIME.pdf",
    )
    return parser.parse_args()


def _load_order(book_path: Path) -> list[Path]:
    text = book_path.read_text(encoding="utf-8")
    links = re.findall(r"\]\(\./([^)]+\.md)\)", text)
    return [book_path.parent / link for link in links]


def _clean_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("`", "")
    text = text.replace("**", "")
    text = text.replace("*", "")
    return text.strip()


def _register_book_font() -> str:
    font_name = "ChartResearchBookFont"
    for font_path, subfont_index in FONT_CANDIDATES:
        path = Path(font_path)
        if not path.exists():
            continue
        registerFont(TTFont(font_name, str(path), subfontIndex=subfont_index))
        return font_name
    raise RuntimeError(
        "No renderable CJK font found for PDF export. Tried: "
        + ", ".join(path for path, _ in FONT_CANDIDATES)
    )


def _styles():
    font_name = _register_book_font()
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "BookTitle",
        parent=base["Title"],
        fontName=font_name,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=HexColor("#2c241c"),
        spaceAfter=18,
    )
    h1 = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=HexColor("#2f2a24"),
        spaceBefore=10,
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=20,
        textColor=HexColor("#3d352c"),
        spaceBefore=8,
        spaceAfter=6,
    )
    h3 = ParagraphStyle(
        "H3",
        parent=base["Heading3"],
        fontName=font_name,
        fontSize=12,
        leading=17,
        textColor=HexColor("#4a4036"),
        spaceBefore=6,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=16,
        textColor=HexColor("#332b24"),
        spaceAfter=4,
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=body,
        leftIndent=10,
        firstLineIndent=0,
    )
    mono = ParagraphStyle(
        "Mono",
        parent=body,
        fontName=font_name,
        fontSize=8.8,
        leading=12,
    )
    return {"title": title, "h1": h1, "h2": h2, "h3": h3, "body": body, "bullet": bullet, "mono": mono}


def _render_markdown(md_path: Path, styles: dict[str, ParagraphStyle]) -> list:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    flow = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flow.append(Spacer(1, 4))
            i += 1
            continue

        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].rstrip())
                i += 1
            flow.append(Preformatted("\n".join(block), styles["mono"]))
            flow.append(Spacer(1, 5))
            continue

        if stripped.startswith("# "):
            flow.append(Paragraph(_clean_inline(stripped[2:]), styles["h1"]))
            i += 1
            continue

        if stripped.startswith("## "):
            flow.append(Paragraph(_clean_inline(stripped[3:]), styles["h2"]))
            i += 1
            continue

        if stripped.startswith("### "):
            flow.append(Paragraph(_clean_inline(stripped[4:]), styles["h3"]))
            i += 1
            continue

        if stripped.startswith("> "):
            flow.append(Paragraph(_clean_inline(stripped[2:]), styles["body"]))
            i += 1
            continue

        if stripped.startswith("- "):
            flow.append(Paragraph("• " + _clean_inline(stripped[2:]), styles["bullet"]))
            i += 1
            continue

        if re.match(r"^\d+\.\s", stripped):
            flow.append(Paragraph(_clean_inline(stripped), styles["bullet"]))
            i += 1
            continue

        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "|", "-", ">")) or re.match(r"^\d+\.\s", nxt):
                break
            para.append(nxt)
            i += 1
        flow.append(Paragraph(_clean_inline(" ".join(para)), styles["body"]))

    return flow


def build_pdf(report_root: Path, output_pdf: Path) -> Path:
    styles = _styles()
    md_files = _load_order(report_root / "book.md")

    story = [
        Spacer(1, 25 * mm),
        Paragraph("B.V. Raman / Parashara / Jaimini Comprehensive Chart Research", styles["title"]),
        Paragraph("REDACTED_DATE REDACTED_TIME UTC+8 | REDACTED_PLACE Fengfeng, Hebei | Raman ayanamsa | Mean Node", styles["body"]),
        Spacer(1, 12 * mm),
        Paragraph("Markdown-first export generated from the report book root.", styles["body"]),
        PageBreak(),
    ]

    for idx, md_path in enumerate(md_files):
        if idx > 0:
            story.append(PageBreak())
        story.extend(_render_markdown(md_path, styles))

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="B.V. Raman / Parashara / Jaimini Comprehensive Chart Research",
        author="Codex + repo runtime outputs",
    )
    doc.build(story)
    return output_pdf


def main() -> int:
    args = _parse_args()
    report_root = Path(args.report_root).resolve()
    output_pdf = (
        Path(args.output).resolve()
        if args.output
        else report_root / "exports" / "chart_research_REDACTED_DATE_REDACTED_TIME.pdf"
    )
    build_pdf(report_root, output_pdf)
    print(output_pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
