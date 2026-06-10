"""
Generate bilingual PDF directly from the cleaned _ALL_PAGES_bilingual.md

Usage:
  python tools/generate_bilingual_pdf_from_md.py
"""

import re
from pathlib import Path

from fpdf import FPDF

# ── Config ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MD_FILE = PROJECT_ROOT / "progress" / "pages_editable" / "_ALL_PAGES_bilingual.md"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "Jyotish-Prasana_bilingual_v2.pdf"

FONT_YAHEI = "C:/Windows/Fonts/msyh.ttc"
FONT_YAHEI_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_TNR = "C:/Windows/Fonts/times.ttf"
FONT_TNR_I = "C:/Windows/Fonts/timesi.ttf"

PAGE_W = 210
PAGE_H = 297
MARGIN_TOP = 18
MARGIN_BOTTOM = 18
MARGIN_SIDE = 20
BODY_W = PAGE_W - 2 * MARGIN_SIDE

COLOR_HEADING = (26, 82, 118)
COLOR_EN_BODY = (50, 50, 50)
COLOR_ZH_BODY = (0, 0, 0)
COLOR_SEP = (180, 180, 180)

SIZE_EN_BODY = 10.5
SIZE_ZH_BODY = 10
SIZE_HEADING_EN = 11.5
SIZE_HEADING_ZH = 11
LINE_H = 5.8

# ── IAST → ASCII for Chinese font (YaHei lacks extended Latin) ──
IAST_MAP = str.maketrans({
    "Ā": "A", "ā": "a", "Ī": "I", "ī": "i", "Ū": "U", "ū": "u",
    "Ṛ": "R", "ṛ": "r", "Ṣ": "S", "ṣ": "s", "Ṭ": "T", "ṭ": "t",
    "Ḍ": "D", "ḍ": "d", "Ṇ": "N", "ṇ": "n", "Ṅ": "N", "ṅ": "n",
    "Ḷ": "L", "ḷ": "l", "Ḥ": "H", "ḥ": "h", "Ṃ": "M", "ṃ": "m",
    "Ś": "S", "ś": "s", "Ñ": "N", "ñ": "n",
})


def strip_unsupported(text: str) -> str:
    """Keep only chars supported by YaHei/TNR."""
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


# ── Heading detection (same as original) ──
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
    s = line.strip()
    if not s or len(s) > 80:
        return False
    if s.isupper() and len(s) > 3:
        return True
    if RE_HEADING_EN.match(s):
        return True
    return False


def is_heading_zh(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 60:
        return False
    if RE_HEADING_ZH.match(s):
        return True
    if s.endswith("：") and re.search(r"[一-鿿]", s):
        return True
    if re.match(r"^[一-鿿]{2,30}（[A-Za-z\s]+）[：:]?$", s):
        return True
    return False


# ── Parse md file ──
RE_PAGE = re.compile(r"^========== 第 \d+ 页 \(page (\d+)\) ==========$", re.MULTILINE)
RE_IMG = re.compile(r"^\[(?:嵌入图片|插图)[^\]]*\]")
RE_HLINE = re.compile(r"^[\s\-_~=]+$")


def parse_markdown(filepath):
    """Parse the bilingual markdown file into a list of {en, cn, page_num} dicts."""
    text = filepath.read_text(encoding="utf-8")

    # Split by page markers
    # Find all page starts
    page_starts = list(RE_PAGE.finditer(text))

    pages = []
    for i, m in enumerate(page_starts):
        page_num = int(m.group(1))
        start = m.end()
        end = page_starts[i + 1].start() if i + 1 < len(page_starts) else len(text)
        page_content = text[start:end]

        # Extract English and Chinese sections
        en_match = re.search(r"【英文原文】\n(.*?)(?=【中文翻译】)", page_content, re.DOTALL)
        cn_match = re.search(r"【中文翻译】← 编辑这里\n(.*?)(?=\n\n==========|\Z)", page_content, re.DOTALL)

        en_text = en_match.group(1).strip() if en_match else ""
        cn_text = cn_match.group(1).strip() if cn_match else ""

        # Check for merged format (content has inline CN, no separate section needed)
        if cn_text.startswith("（英文原文中已逐条附中文翻译，此处不再重复。）"):
            cn_text = ""  # TOC pages with merged format

        # Clean image references and horizontal lines
        en_lines = []
        for line in en_text.split('\n'):
            s = line.strip()
            if RE_IMG.match(s) or RE_HLINE.match(s):
                continue
            en_lines.append(line)
        en_text = '\n'.join(en_lines)

        cn_lines = []
        for line in cn_text.split('\n'):
            s = line.strip()
            if RE_IMG.match(s) or RE_HLINE.match(s):
                continue
            cn_lines.append(line)
        cn_text = '\n'.join(cn_lines)

        # Skip truly empty pages
        if not en_text.strip() and not cn_text.strip():
            continue

        pages.append({
            "en": en_text,
            "cn": cn_text,
            "page_num": page_num,
        })

    return pages


# ── PDF Class ──
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

        self.set_draw_color(*COLOR_SEP)
        self.set_line_width(0.3)
        self.line(MARGIN_SIDE + 10, self.get_y(), PAGE_W - MARGIN_SIDE - 10, self.get_y())
        self.ln(8)

        self.set_font("YaHei", "", 8.5)
        self.set_text_color(100, 100, 100)
        desc = (
            "本书为 Iranganti Rangacharya 所著《Muhurtha Sindhu》的英汉对照版。"
            "英文原文通过 PDF 提取，中文翻译由 DeepSeek AI 完成。"
            "全书涵盖择时占星学的完整体系。"
        )
        self.multi_cell(w=BODY_W, h=5, text=desc, align="C")
        self._cover_done = True


# ── Rendering ──
def write_body_block(pdf, text, lang):
    """Write body text with heading detection."""
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        heading = (is_heading_en(line) if lang == "en" else is_heading_zh(line))
        if heading:
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


def render_page(pdf, en_text, cn_text, page_num):
    """Render one page: English → separator → Chinese."""
    # Page badge
    pdf.set_font("TNR", "I", 7)
    pdf.set_text_color(*COLOR_SEP)
    pdf.cell(BODY_W, 3, f"p. {page_num + 1}", align="R")
    pdf.ln(5)

    # English block
    if en_text.strip():
        write_body_block(pdf, en_text, "en")

    # Separator
    if en_text.strip() and cn_text.strip():
        pdf.ln(2)
        pdf.set_draw_color(*COLOR_HEADING)
        pdf.set_line_width(0.5)
        y = pdf.get_y()
        pdf.line(MARGIN_SIDE + 30, y, PAGE_W - MARGIN_SIDE - 30, y)
        pdf.ln(2)
        pdf.set_font("YaHei", "B", 8)
        pdf.set_text_color(*COLOR_HEADING)
        pdf.cell(BODY_W, 4, "▼  中文翻译  ▼", align="C")
        pdf.ln(5)

    # Chinese block
    if cn_text.strip():
        write_body_block(pdf, cn_text, "zh")


# ── Main ──
def main():
    print(f"Parsing: {MD_FILE}")
    pages = parse_markdown(MD_FILE)
    print(f"  Found {len(pages)} content pages")

    pdf = BilingualPDF()
    pdf.set_left_margin(MARGIN_SIDE)
    pdf.set_right_margin(MARGIN_SIDE)
    pdf.set_top_margin(MARGIN_TOP)
    pdf.set_auto_page_break(auto=True, margin=MARGIN_BOTTOM)

    pdf.add_cover_page()

    for pg_data in pages:
        en_text = strip_unsupported(pg_data["en"])
        cn_text = strip_unsupported(pg_data["cn"])
        # IAST → ASCII for Chinese (YaHei can't render extended Latin)
        cn_text = cn_text.translate(IAST_MAP)

        if not en_text.strip() and not cn_text.strip():
            continue

        pdf.add_page()
        render_page(pdf, en_text, cn_text, pg_data["page_num"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT_FILE))
    print(f"\nDone: {OUTPUT_FILE}")
    print(f"  PDF pages: {pdf.pages_count}")


if __name__ == "__main__":
    main()
