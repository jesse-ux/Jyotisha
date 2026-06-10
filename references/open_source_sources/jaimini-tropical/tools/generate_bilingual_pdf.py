"""
Generate a bilingual (English + Chinese) paragraph-interleaved PDF for Jyotish-Prasana.

Input:
  - progress/Jyotish-Prasana_pages.json       (original English, 190 pages)
  - progress/Jyotish-Prasana_translated.json  (DeepSeek Chinese translation, 190 pages)

Output:
  - output/Jyotish-Prasana_bilingual.pdf

Layout: EN paragraph → ZH paragraph → separator → repeat.
Headings auto-detected and rendered in dark blue.

Usage:
  python tools/generate_bilingual_pdf.py
"""

import json
import re
import sys
from pathlib import Path

from fpdf import FPDF

# ---- Config ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGLISH_JSON = PROJECT_ROOT / "progress" / "Jyotish-Prasana_pages.json"
CHINESE_JSON = PROJECT_ROOT / "progress" / "Jyotish-Prasana_translated.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "Jyotish-Prasana_bilingual.pdf"

FONT_YAHEI = "C:/Windows/Fonts/msyh.ttc"
FONT_YAHEI_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_TNR = "C:/Windows/Fonts/times.ttf"
FONT_TNR_I = "C:/Windows/Fonts/timesi.ttf"

# Page layout
PAGE_W = 210
PAGE_H = 297
MARGIN_TOP = 18
MARGIN_BOTTOM = 18
MARGIN_SIDE = 20
BODY_W = PAGE_W - 2 * MARGIN_SIDE  # 170mm
# Colors
COLOR_HEADING = (26, 82, 118)    # dark blue
COLOR_EN_BODY = (50, 50, 50)     # dark gray
COLOR_ZH_BODY = (0, 0, 0)        # black
COLOR_SEP = (180, 180, 180)      # light gray

# Font sizes
SIZE_EN_BODY = 10.5
SIZE_ZH_BODY = 10
SIZE_HEADING_EN = 11.5
SIZE_HEADING_ZH = 11
LINE_H = 5.8

# ---- Character filtering ----

def strip_unsupported(text: str) -> str:
    """Keep only chars supported by YaHei/TNR: ASCII, Latin Ext (IAST), CJK, punctuation."""
    result = []
    for ch in text:
        cp = ord(ch)
        if (
            cp < 0x7F
            or 0xA0 <= cp <= 0x24F
            or 0x2000 <= cp <= 0x206F
            or 0x2E00 <= cp <= 0x2E7F
            or 0x3000 <= cp <= 0x303F
            or 0x3400 <= cp <= 0x4DBF
            or 0x4E00 <= cp <= 0x9FFF
            or 0xFF00 <= cp <= 0xFFEF
        ):
            result.append(ch)
    return "".join(result)


IAST_MAP = str.maketrans({
    "Ā": "A", "ā": "a", "Ī": "I", "ī": "i", "Ū": "U", "ū": "u",
    "Ṛ": "R", "ṛ": "r", "Ṣ": "S", "ṣ": "s", "Ṭ": "T", "ṭ": "t",
    "Ḍ": "D", "ḍ": "d", "Ṇ": "N", "ṇ": "n", "Ṅ": "N", "ṅ": "n",
    "Ḷ": "L", "ḷ": "l", "Ḥ": "H", "ḥ": "h", "Ṃ": "M", "ṃ": "m",
    "Ś": "S", "ś": "s", "Ñ": "N", "ñ": "n",
})

# ---- Text Cleaning ----

RE_IMG = re.compile(r"^\[(?:嵌入图片|插图)[^\]]*\]")
RE_ROMAN = re.compile(r"^\([ivxlcdm]+\)\s*$", re.IGNORECASE)
RE_HLINE = re.compile(r"^[\s\-_~=]+$")
RE_HEADING_EN = re.compile(
    r"^(?:Chapter|CHAPTER)\s*-?\s*[IVXLCDM\d]+\b|"
    r"^(?:[IVXLCDM]+\.?\s+[A-Z])|"
    r"^[A-Z]{2,}(?:\s+[A-Z]+){0,4}\s*:?$|"
    r"^\d+\.\s+[A-Z][a-z]"
)
RE_HEADING_ZH = re.compile(
    r"^第[一二三四五六七八九十百千\d]+[章节卷]|"
    r"^[一二三四五六七八九十]+[、．、]\s*\S|"
    r"^（[一二三四五六七八九十\d]+）"
)


def is_heading_en(line: str) -> bool:
    """Detect if an English line is a heading/title."""
    s = line.strip()
    if not s or len(s) > 80:
        return False
    if s.isupper() and len(s) > 3:
        return True
    if RE_HEADING_EN.match(s):
        return True
    return False


def is_heading_zh(line: str) -> bool:
    """Detect if a Chinese line is a heading/title."""
    s = line.strip()
    if not s or len(s) > 60:
        return False
    if RE_HEADING_ZH.match(s):
        return True
    # Line ending with ：that contains CJK chars (section heading)
    if s.endswith("：") and re.search(r"[一-鿿]", s):
        return True
    # Short line with Chinese + English in parens (e.g. "太阴年（Lunar Years）：")
    if re.match(r"^[一-鿿]{2,30}（[A-Za-z\s]+）[：:]?$", s):
        return True
    return False


def clean_english(text: str) -> str:
    """Remove artifacts from English OCR text."""
    lines = text.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if RE_IMG.match(stripped):
            continue
        if RE_HLINE.match(stripped):
            continue
        if len(stripped) > 5:
            printable = sum(1 for c in stripped if 32 <= ord(c) <= 126)
            if printable / max(len(stripped), 1) < 0.4:
                continue
            # Detect garbled OCR: count actual English-like words (3+ alpha chars)
            words = re.findall(r"[A-Za-z]{3,}", stripped)
            word_chars = sum(len(w) for w in words)
            alpha_chars = sum(1 for c in stripped if c.isalpha())
            if alpha_chars > 10 and word_chars / max(alpha_chars, 1) < 0.3:
                continue  # mostly non-word garbage
        line = line.replace("~", "")
        line = strip_unsupported(line)
        # Clean up empty parenthetical left after Devanagari removal: "( / ... →" → "(..."
        line = re.sub(r"\(\s*/\s*", "(", line)
        out.append(line)
    return "\n".join(out)


def clean_chinese(text: str) -> str:
    """Remove artifacts from Chinese translated text."""
    lines = text.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if RE_IMG.match(stripped):
            continue
        if "梵文诗句，内容待确认" in stripped:
            continue
        if RE_ROMAN.match(stripped):
            continue
        if RE_HLINE.match(stripped):
            continue
        line = line.replace("**", "")
        line = line.replace("~", "")
        line = strip_unsupported(line)
        line = re.sub(r"\(\s*/\s*", "(", line)
        out.append(line)
    return "\n".join(out)


# ---- PDF Class ----


class BilingualPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.set_auto_page_break(auto=True, margin=MARGIN_BOTTOM)
        self.add_font("YaHei", "", FONT_YAHEI)
        self.add_font("YaHei", "B", FONT_YAHEI_BOLD)
        self.add_font("TNR", "", FONT_TNR)
        self.add_font("TNR", "I", FONT_TNR_I)
        self._cover_done = False

    def footer(self):
        if not self._cover_done:
            return
        self.set_y(-12)
        self.set_font("TNR", "", 8)
        self.set_text_color(*COLOR_SEP)
        self.cell(0, 8, f"- {self.page_no()} -", align="C")

    def add_cover_page(self):
        """Bilingual cover page."""
        self.add_page()
        self.ln(45)

        self.set_font("YaHei", "B", 28)
        self.set_text_color(*COLOR_HEADING)
        self.cell(0, 14, "MUHURTHA SINDHU", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font("YaHei", "B", 20)
        self.cell(0, 12, "择时宝鉴", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        self.set_font("TNR", "I", 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, "A Manual of Electional Astrology", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("YaHei", "", 12)
        self.cell(0, 10, "选举占星学手册", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        self.set_font("YaHei", "", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, "作者：Iranganti Rangacharya", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("YaHei", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, "英汉对照版  |  Bilingual Edition", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, "Chinese translation by DeepSeek AI  |  Typeset with fpdf2", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(14)

        # Rule
        self.set_draw_color(*COLOR_SEP)
        self.set_line_width(0.3)
        self.line(MARGIN_SIDE + 10, self.get_y(), PAGE_W - MARGIN_SIDE - 10, self.get_y())
        self.ln(8)

        self.set_font("YaHei", "", 8.5)
        self.set_text_color(100, 100, 100)
        desc = (
            "本书为 Iranganti Rangacharya 所著《Muhurtha Sindhu》的英汉对照版。"
            "英文原文通过 PDF 提取，中文翻译由 DeepSeek AI 完成。"
            "全书共 190 页，涵盖择时占星学的完整体系。"
        )
        self.multi_cell(w=BODY_W, h=5, text=desc, align="C")

        self._cover_done = True


# ---- Rendering ----


def write_styled_block(pdf: BilingualPDF, text: str, lang: str):
    """Write a text block with heading detection. Lines detected as headings
    are rendered in dark blue bold; body text in default color."""
    lines = text.split("\n")
    # Normalize: merge consecutive non-heading lines for better wrapping
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        heading = (is_heading_en(line) if lang == "en" else is_heading_zh(line))
        if heading:
            # Render heading
            pdf.ln(1.5)
            if lang == "en":
                pdf.set_font("TNR", "I", SIZE_HEADING_EN)
            else:
                pdf.set_font("YaHei", "B", SIZE_HEADING_ZH)
            pdf.set_text_color(*COLOR_HEADING)
            pdf.multi_cell(w=BODY_W, h=LINE_H + 1, text=line, align="L")
            pdf.ln(0.5)
            i += 1
        else:
            # Collect consecutive body lines
            body_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    i += 1
                    continue
                if is_heading_en(s) if lang == "en" else is_heading_zh(s):
                    break
                body_lines.append(s)
                i += 1
            if body_lines:
                body_text = " ".join(body_lines)
                if lang == "en":
                    pdf.set_font("TNR", "", SIZE_EN_BODY)
                    pdf.set_text_color(*COLOR_EN_BODY)
                else:
                    pdf.set_font("YaHei", "", SIZE_ZH_BODY)
                    pdf.set_text_color(*COLOR_ZH_BODY)
                pdf.multi_cell(w=BODY_W, h=LINE_H, text=body_text, align="L")
                pdf.ln(1)

        # Check for page overflow after each element
        if pdf.get_y() > PAGE_H - MARGIN_BOTTOM - 20:
            break


def write_lang_separator(pdf: BilingualPDF):
    """Bold separator marking the language switch."""
    pdf.ln(3)
    pdf.set_draw_color(*COLOR_HEADING)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(MARGIN_SIDE + 30, y, PAGE_W - MARGIN_SIDE - 30, y)
    pdf.ln(2)
    pdf.set_font("YaHei", "B", 8)
    pdf.set_text_color(*COLOR_HEADING)
    pdf.cell(BODY_W, 4, "▼  中文翻译  ▼", align="C")
    pdf.ln(6)


def render_page_pair(pdf: BilingualPDF, en_text: str, cn_text: str, page_num: int):
    """Render one source page: English block → separator → Chinese block."""
    # Page badge
    pdf.set_font("TNR", "I", 7)
    pdf.set_text_color(*COLOR_SEP)
    pdf.cell(BODY_W, 3, f"p. {page_num + 1}", align="R")
    pdf.ln(5)

    if not en_text.strip() and not cn_text.strip():
        return

    # English block
    if en_text.strip():
        write_styled_block(pdf, en_text, "en")

    # Language separator
    if en_text.strip() and cn_text.strip():
        write_lang_separator(pdf)

    # Chinese block
    if cn_text.strip():
        write_styled_block(pdf, cn_text, "zh")


# ---- Main ----


def main():
    print("Loading JSON files...")
    with open(ENGLISH_JSON, "r", encoding="utf-8") as f:
        pages_en = json.load(f)
    with open(CHINESE_JSON, "r", encoding="utf-8") as f:
        pages_cn = json.load(f)

    total = len(pages_en)
    print(f"  Source pages: {total}")
    print(f"  Output: {OUTPUT_FILE}")

    pdf = BilingualPDF()
    pdf.set_left_margin(MARGIN_SIDE)
    pdf.set_right_margin(MARGIN_SIDE)
    pdf.set_top_margin(MARGIN_TOP)
    pdf.set_auto_page_break(auto=True, margin=MARGIN_BOTTOM)

    pdf.add_cover_page()

    for pg in range(total):
        key = str(pg)
        en_raw = pages_en.get(key, "")
        cn_raw = pages_cn.get(key, "")

        en_text = clean_english(en_raw)
        cn_text = clean_chinese(cn_raw)
        # IAST → ASCII for Chinese only (YaHei lacks extended Latin)
        cn_text = cn_text.translate(IAST_MAP)

        if not en_text.strip() and not cn_text.strip():
            continue

        pdf.add_page()
        render_page_pair(pdf, en_text, cn_text, pg)

        if (pg + 1) % 20 == 0:
            print(f"  Processed {pg + 1}/{total} pages...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT_FILE))
    print(f"\nDone: {OUTPUT_FILE}")
    print(f"  PDF pages: {pdf.pages_count}")
    print(f"  Content pages: {total}")


if __name__ == "__main__":
    main()
