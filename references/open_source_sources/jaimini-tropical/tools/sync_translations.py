"""
Sync edited translations from the Markdown file back to JSON and regenerate PDF.

Usage:
  python tools/sync_translations.py
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MD_FILE = PROJECT_ROOT / "progress" / "pages_editable" / "_ALL_PAGES_bilingual.md"
TRANSLATED_JSON = PROJECT_ROOT / "progress" / "Jyotish-Prasana_translated.json"


def parse_md(filepath: Path) -> dict[str, str]:
    """Parse the editable Markdown file, extract Chinese translations per page."""
    text = filepath.read_text(encoding="utf-8")
    # Split by page markers
    pattern = re.compile(
        r"={10}\s*第\s*(\d+)\s*页.*?={10}\s*\n"
        r".*?【英文原文】\n(.*?)\n\n"
        r"【中文翻译】.*?\n(.*?)(?:\n\n\n|$)",
        re.DOTALL,
    )
    translations = {}
    for match in pattern.finditer(text):
        page_num = int(match.group(1)) - 1
        en_block = match.group(1).strip()
        zh_block = match.group(2).strip()
        # Only update if Chinese translation has changed (non-empty)
        key = str(page_num)
        translations[key] = zh_block

    return translations


def main():
    if not MD_FILE.exists():
        print(f"ERROR: {MD_FILE} not found!")
        print("Run generate_bilingual_pdf.py first to create the editable file.")
        sys.exit(1)

    print(f"Parsing: {MD_FILE}")
    updates = parse_md(MD_FILE)
    print(f"  Found {len(updates)} translated pages")

    # Load existing translations
    with open(TRANSLATED_JSON, "r", encoding="utf-8") as f:
        existing = json.load(f)

    # Apply updates
    changed = 0
    for key, new_text in updates.items():
        if key in existing and existing[key] != new_text:
            existing[key] = new_text
            changed += 1

    if changed == 0:
        print("  No changes detected.")
    else:
        # Save updated JSON
        with open(TRANSLATED_JSON, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  Updated {changed} pages in {TRANSLATED_JSON}")

        # Regenerate PDF
        print("\nRegenerating PDF...")
        import subprocess

        python = sys.executable
        gen_script = PROJECT_ROOT / "tools" / "generate_bilingual_pdf.py"
        result = subprocess.run([python, str(gen_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            sys.exit(1)
        print("Done!")


if __name__ == "__main__":
    main()
