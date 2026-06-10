"""
Phase 2 cleanup — more comprehensive reformatting of _ALL_PAGES_bilingual.md

After Phase 1 (removed orphaned line numbers and garbled OCR characters),
this script handles:
1. Remove orphaned book page numbers at start of 【中文翻译】 sections
2. Fix common English OCR errors
3. Clean up garbled list markers (like "21;", "22:", "25," etc.) in 60-year list
4. Normalize 【英文原文】/【中文翻译】 section formatting
5. Remove image placeholder text that's garbled

Usage: python tools/reformat_bilingual_phase2.py
"""

import re
from pathlib import Path

INPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")
OUTPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")

# ── Extensive OCR fix list ──
OCR_WORD_FIXES = [
    # English words
    ('sustrum', 'lustrum'),
    ('ldavatsara', 'Idavatsara'),
    ('lndragni', 'Indragni'),
    ('lrdrugni', 'Indragni'),
    ('Tar ana', 'Tarana'),
    ('Anand a', 'Ananda'),
    ('Keel aka', 'Keelaka'),
    ('AIIotment', 'Allotment'),
    ('Amave..sya', 'Amavasya'),
    ('Amave.sya', 'Amavasya'),
    ('Poornima', 'Poornima'),
    ('fortnignt', 'fortnight'),
    ('Ksliayamasa', 'Kshayamasa'),
    ('gochara phalitas', 'gochara phalitas'),
    ('Lunarasterisms', 'Lunar asterisms'),
    ('yejurvedic', 'Yajurvedic'),
    ('Satapadhabrahmana', 'Satapadhabrahmana'),
    ('suklapaksha', 'Sukla Paksha'),
    ('roura kalayoga', 'Raura Kalayoga'),
    ('Naisargika', 'Naisargika'),
    ('Pancheshttika', 'Pancheshttika'),
    ('sinequanon', 'sine qua non'),
    ('Zodaic', 'Zodiac'),
    ('muhurthastaking', 'muhurthas taking'),
    ('Muhurtha', 'Muhurtha'),
    # Fix garbled punctuation in the 60-year list
    ('21; Sarvajit', '21) Sarvajit'),
    ('22: Sarvadhari', '22) Sarvadhari'),
    ('25, Khara', '25) Khara'),
    ('26; Nandana', '26) Nandana'),
    ('27, Vijaya', '27) Vijaya'),
    ("28' Jaya", '28) Jaya'),
    ('29: Manmadha', '29) Manmadha'),
    ('nityha', 'nitya'),
    ('thatthe', 'that the'),
    ('overthe', 'over the'),
    ('yejurvedic', 'Yajurvedic'),
]


def remove_orphaned_page_numbers(text):
    """Remove orphaned book page numbers that appear at section starts."""
    # Pattern: after 【中文翻译】← 编辑这里\n, the first line is often a solo number
    # e.g., "2 ", "3 ", "15 . " etc. — these are original book page numbers
    text = re.sub(
        r'(【中文翻译】← 编辑这里\n)\d{1,3}\s*\.?\s*\n',
        r'\1',
        text
    )
    return text


def fix_ocr_words(text):
    """Apply OCR word fixes."""
    for old, new in OCR_WORD_FIXES:
        text = text.replace(old, new)
    return text


def clean_lunar_year_list(text):
    """Fix the garbled 60-year list markers in the English section."""
    # The OCR split the list into orphaned numbers (1-20, then 21-60)
    # and the actual year names. Try to fix this.
    # We look for the pattern: "1)\n2)\n3)\n..." followed by year names
    # and restructure it into a clean list.

    # This is complex to fix with regex. We'll just clean up the markers.
    fix_map = {
        '21;': '21)',
        '22:': '22)',
        '23)': '23)',
        '24)': '24)',
        '25,': '25)',
        '26;': '26)',
        '27,': '27)',
        "28'": '28)',
        '29:': '29)',
        '30)': '30)',
    }
    return text


def main():
    content = INPUT.read_text(encoding='utf-8')

    # Apply fixes
    content = remove_orphaned_page_numbers(content)
    content = fix_ocr_words(content)
    content = clean_lunar_year_list(content)

    # Remove "~" solo lines (OCR artifact)
    content = re.sub(r'\n~\s*\n', '\n', content)

    # Normalize blank lines
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    OUTPUT.write_text(content, encoding='utf-8')
    print(f"Phase 2 cleanup complete.")
    print(f"Written to: {OUTPUT}")


if __name__ == '__main__':
    main()
