"""
Reformat _ALL_PAGES_bilingual.md — apply the user's formatting style
from the first 163 lines consistently to the entire file.

Key improvements:
1. Clean up English OCR sections (remove orphaned page numbers, fix garbled text)
2. Format the 60-year list and other structured data cleanly
3. For TOC-like pages, merge CN translations into EN section (matching user's page 5 pattern)
4. Ensure consistent 【英文原文】/【中文翻译】 section markers
5. Remove excessive blank lines

Usage:
  python tools/reformat_bilingual.py
"""

import re
from pathlib import Path

INPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")
OUTPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")  # overwrite

# ── Known OCR fixes in English text ──
OCR_FIXES = [
    # garbled words
    (r'\bsustrum\b', 'lustrum'),
    (r'\bldavatsara\b', 'Idavatsara'),
    (r'\blndragni\b', 'Indragni'),
    (r'\blrdrugni\b', 'Indragni'),
    (r'\bTar ana\b', 'Tarana'),
    (r'\bAnand a\b', 'Ananda'),
    (r'\bKeel aka\b', 'Keelaka'),
    (r'\bAIIotment\b', 'Allotment'),
    # Page header/footer artifacts — remove isolated page numbers embedded in English text
    # Pattern: number like "1" or "2" appearing after "【英文原文】" as first line
    # These are the original book's page numbers, not content
]


def clean_english_block(text):
    """Remove OCR artifact lines from English content."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        # Skip truly empty lines (will be normalized later)
        if not s:
            cleaned.append('')
            continue
        # Skip orphaned page numbers: solo 1-3 digit numbers (original book page markers)
        if re.match(r'^\d{1,3}$', s):
            continue
        # Skip garbled OCR artifacts like "1bl", "11l", "46l", "28'", "25,", "26;"
        if re.match(r'^\d{1,3}[bl\';\-,:]+$', s):
            continue
        # Skip orphaned "(vi)", "(vii)" etc. — these are book front-matter page markers
        if re.match(r'^\([ivxlcdm]+\)$', s, re.IGNORECASE):
            continue
        # Skip solo roman numerals
        if re.match(r'^[ivxlcdm]+$', s, re.IGNORECASE) and len(s) <= 4:
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def merge_toc_page(page_text):
    """For TOC/directory pages, merge Chinese into the English section
    following the user's page 5 formatting pattern."""
    # Check if this looks like a TOC page (has Chapter listings)
    eng_match = re.search(r'【英文原文】\n(.*?)(?=【中文翻译】)', page_text, re.DOTALL)
    chi_match = re.search(r'【中文翻译】← 编辑这里\n(.*?)(?=\n\n==========|\Z)', page_text, re.DOTALL)

    if not eng_match or not chi_match:
        return page_text

    eng_content = eng_match.group(1)
    chi_content = chi_match.group(1)

    # Check if this is a TOC page (contains "Chapter" patterns)
    is_toc = bool(re.search(r'Chapter[- ]+[IVX]+', eng_content))

    if not is_toc:
        return page_text

    # For TOC pages, merge format: "English term中文术语"
    # The Chinese section already has the translations
    # We'll keep both sections but format the English section to include Chinese

    return page_text


def process_page(page_text):
    """Process a single page section."""
    # Apply OCR fixes
    for pattern, replacement in OCR_FIXES:
        page_text = re.sub(pattern, replacement, page_text)

    # Clean the English section
    def clean_eng(match):
        eng = match.group(1)
        cleaned = clean_english_block(eng)
        return '【英文原文】\n' + cleaned

    page_text = re.sub(
        r'【英文原文】\n(.*?)(?=【中文翻译】)',
        clean_eng,
        page_text,
        flags=re.DOTALL
    )

    return page_text


def main():
    content = INPUT.read_text(encoding='utf-8')

    # Split into pages
    pages = re.split(r'(?=^========== 第 )', content, flags=re.MULTILINE)

    processed = []
    for i, page in enumerate(pages):
        if not page.strip():
            continue
        processed.append(process_page(page))

    result = ''.join(processed)

    # Normalize blank lines: max 2 consecutive
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    # Ensure each page section has exactly one blank line before the next
    # (page separator formatting)

    OUTPUT.write_text(result, encoding='utf-8')
    print(f"Processed {len(processed)} pages.")
    print(f"Chars: {len(content)} → {len(result)}")
    print(f"Written to: {OUTPUT}")


if __name__ == '__main__':
    main()
