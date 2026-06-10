"""
Clean up _ALL_PAGES_bilingual.md:
1. Remove orphaned page numbers (OCR artifacts) from English sections
2. Fix known OCR error patterns
3. Normalize section markers
4. Clean up excessive blank lines

Usage: python tools/cleanup_bilingual_md.py
"""

import re
from pathlib import Path

INPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")
OUTPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual_cleaned.md")

# Known OCR fixes: (pattern, replacement)
OCR_FIXES = [
    # Common English OCR errors
    (r'\bldavatsara\b', 'Idavatsara'),
    (r'\blndragni\b', 'Indragni'),
    (r'\blrdrugni\b', 'Indragni'),
    (r'\bsustrum\b', 'lustrum'),
    (r'\bTar ana\b', 'Tarana'),
    (r'\bAnand a\b', 'Ananda'),
    (r'\bKeel aka\b', 'Keelaka'),
    (r'\bAIIotment\b', 'Allotment'),
    (r'\besseential\b', 'essentials'),
    (r'\bSpearing\b', 'Spearing'),  # keep — it's in the original
    # OCR artifacts — garbled number patterns
    (r'^1bl$', ''),   # OCR garbled "10)"
    (r'^11l$', ''),   # OCR garbled "11)"
    # Fix inconsistent Sanskrit transliteration (common patterns)
    (r'\bAswini\b', 'Aswini'),   # keep standardized form
]

def clean_english_section(text):
    """Remove orphaned single-digit/OCR-artifact numbers from English text."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Remove truly orphaned numbers (page number artifacts from OCR)
        # These appear as solo numbers like "1", "2", "12" etc. on their own line
        # in the English sections between paragraphs
        if re.match(r'^\d{1,3}$', stripped):
            continue  # skip orphaned page numbers
        # Remove garbled OCR artifacts like "1bl", "11l", "46l", "28'"
        if re.match(r'^\d+[bl\';:,\s]*\d*$', stripped) and len(stripped) <= 4:
            continue
        # Remove lines that are just a single garbled char like "~"
        if stripped in ('~',):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def process_file():
    content = INPUT.read_text(encoding='utf-8')

    # Split into page sections
    # Each page starts with "========== 第 X 页 (page Y) =========="
    pages = re.split(r'(?=^========== 第 )', content, flags=re.MULTILINE)

    processed_pages = []

    for page in pages:
        if not page.strip():
            continue

        # Apply OCR fixes
        for pattern, replacement in OCR_FIXES:
            page = re.sub(pattern, replacement, page)

        # Split into English and Chinese sections
        # Find 【英文原文】 and 【中文翻译】 markers
        eng_match = re.search(r'【英文原文】\n(.*?)(?=【中文翻译】|\Z)', page, re.DOTALL)
        chi_match = re.search(r'【中文翻译】.*?\n(.*?)(?=\n========== |\Z)', page, re.DOTALL)

        if eng_match:
            eng_content = eng_match.group(1)
            cleaned_eng = clean_english_section(eng_content)
            page = page.replace(eng_content, cleaned_eng)

        processed_pages.append(page)

    result = ''.join(processed_pages)

    # Clean up excessive blank lines (more than 2 consecutive)
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    # Write output
    OUTPUT.write_text(result, encoding='utf-8')
    print(f"Cleaned file written to: {OUTPUT}")
    print(f"Original size: {len(content)} chars, Cleaned size: {len(result)} chars")


if __name__ == '__main__':
    process_file()
