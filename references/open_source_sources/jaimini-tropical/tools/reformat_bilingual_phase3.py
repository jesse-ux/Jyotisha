"""
Phase 3 — Comprehensive English OCR cleanup for _ALL_PAGES_bilingual.md

This handles remaining English OCR artifacts more aggressively:
1. Remove orphaned list numbers (where numbers and content got separated by OCR)
2. Fix garbled punctuation patterns
3. Clean up random line-breaks in English that break sentences
4. Normalize spacing

Usage: python tools/reformat_bilingual_phase3.py
"""

import re
from pathlib import Path

INPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")
OUTPUT = Path("progress/pages_editable/_ALL_PAGES_bilingual.md")

# Extensive OCR fixes — (pattern, replacement) using word boundaries
OCR_PATTERNS = [
    # Garbled words (space-inserted)
    (r'\bO ghatis\b', '10 ghatis'),
    (r'\bO vig\b', '10 vig'),
    (r'\bO gh\b', '10 gh'),
    (r'\b1 Ogh\b', '10 gh'),
    (r'\b1 Ovi\b', '10 vi'),
    (r'\b1 oa day\b', '1° a day'),
    (r'\b1 st\b', '1st'),
    (r'\b2B to 108\b', '28 to 108'),
    (r'\ba11d\b', 'and'),
    (r'\bshold\b', 'should'),
    (r'\bmedicare\b', 'mediocre'),
    (r'\bofvaisakha\b', 'of Vaisakha'),
    (r'\bEvii\b', 'evil'),
    # Fix common OCR misreads
    ('ldavatsara', 'Idavatsara'),
    ('lndragni', 'Indragni'),
    ('lrdrugni', 'Indragni'),
    ('AIIotment', 'Allotment'),
    ('Amave..sya', 'Amavasya'),
    ('Amave.sya', 'Amavasya'),
    ('fortnignt', 'fortnight'),
    ('Ksliayamasa', 'Kshayamasa'),
    ('Lunarasterisms', 'Lunar asterisms'),
    ('yejurvedic', 'Yajurvedic'),
    ('Satapadhabrahmana', 'Satapadhabrahmana'),
    ('Pancheshttika', 'Pancheshttika'),
    ('sinequanon', 'sine qua non'),
    ('Zodaic', 'Zodiac'),
    # Fix garbled number patterns in the 60-year list
    ('21; Sarvajit', '21) Sarvajit'),
    ('22: Sarvadhari', '22) Sarvadhari'),
    ('25, Khara', '25) Khara'),
    ('26; Nandana', '26) Nandana'),
    ('27, Vijaya', '27) Vijaya'),
    ("28' Jaya", '28) Jaya'),
    ('29: Manmadha', '29) Manmadha'),
    ('sustrum', 'lustrum'),
    # More common errors
    ('Tar ana', 'Tarana'),
    ('Anand a', 'Ananda'),
    ('Keel aka', 'Keelaka'),
    ('nityha', 'nitya'),
    ('thatthe', 'that the'),
    ('overthe', 'over the'),
    ('evii', 'evil'),
    ('a11d', 'and'),
]


def deep_clean_english(text):
    """Deep clean English text content."""
    for pattern, replacement in OCR_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def clean_orphaned_nums_in_list(line):
    """Check if a line is just an orphaned list number like '41)', '42:', '43:', '44:', '45:' etc."""
    s = line.strip()
    if re.match(r'^\d{1,3}[);:,\.\']+\s*$', s):
        return True
    return False


def process_english_section(text):
    """Process English section text, removing orphaned list numbers."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append('')
            continue
        # Skip orphaned list markers that got separated from their content by OCR
        # Pattern: solo "41)", "42:", "43:", etc. with no content following on same line
        # But keep them if the next line doesn't look like a year name
        if clean_orphaned_nums_in_list(line):
            continue
        # Skip garbled page marker artifacts
        if re.match(r'^\d{1,3}[bl\']+$', s):
            continue
        cleaned.append(line)
    # Remove consecutive empty lines (keep max 1)
    result = []
    prev_empty = False
    for line in cleaned:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        result.append(line)
        prev_empty = is_empty
    return '\n'.join(result)


def main():
    content = INPUT.read_text(encoding='utf-8')

    # Apply deep OCR fixes to the whole file
    content = deep_clean_english(content)

    # Split into pages and clean English sections
    pages = re.split(r'(?=^========== 第 )', content, flags=re.MULTILINE)

    processed = []
    for page in pages:
        if not page.strip():
            continue

        # Find and clean the English section
        def replace_eng(m):
            eng = m.group(1)
            cleaned = process_english_section(eng)
            return '【英文原文】\n' + cleaned

        page = re.sub(
            r'【英文原文】\n(.*?)(?=【中文翻译】)',
            replace_eng,
            page,
            flags=re.DOTALL
        )

        processed.append(page)

    result = ''.join(processed)

    # Normalize blank lines
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    OUTPUT.write_text(result, encoding='utf-8')
    print(f"Phase 3 complete. Processed {len(processed)} pages.")


if __name__ == '__main__':
    main()
