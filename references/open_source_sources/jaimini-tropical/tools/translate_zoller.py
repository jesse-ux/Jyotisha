"""
Robert Zoller - Medieval Astrology Foundation Course
Translation Pipeline (improved)

Key improvements over the previous Jyotish-Prasana pipeline:
1. Per-page translation (natural page boundaries, ~2000 chars/page)
2. Medieval/Classical astrology terminology system prompt
3. Page header/footer cleanup before API call
4. Footnote detection and inline placement
5. Progress saved every 5 pages (JSON resume)

Usage:
  python tools/translate_zoller.py
"""
import fitz
import os, sys, json, time, re
from pathlib import Path

import requests

# ---- Config ----
BASE_DIR = Path(r"D:/projects/micrograd_from_scratch")
PDF_PATH = BASE_DIR / "古典占星著作" / "Robert Zoller - Medieval Astrology Foundation Course.pdf"
OUTPUT_DIR = BASE_DIR / "output"
PROGRESS_DIR = BASE_DIR / "progress"
OUTPUT_NAME = "Zoller-Medieval-Astrology"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

# ---- System Prompt ----
SYSTEM_PROMPT = """你是一位中世纪/古典占星学（Medieval/Traditional Astrology）文献的专业翻译。你的任务是：

1. **翻译为中文**: 将英文授课文字稿翻译成流畅、准确的中文。注意：
   - 占星学术语保持专业和一致性：
     "sign" → "星座"、"house" → "宫位"、"planet" → "行星"
     "dignity" → "尊贵"、"debility" → "陷落"、"ruler" → "主宰星"
     "exaltation" → "擢升"、"triplicity" → "三分性"、"term" → "界"、"face/decan" → "面/十分度"
     "natal chart/figure" → "本命盘"、"horoscope" → "星盘"
     "delineation" → "解盘/解读"、"prediction" → "预测"
     " Arabic Parts/Lots" → "阿拉伯点/希腊点"
     "Hermetic" → "赫尔墨斯"、"Medieval" → "中世纪"
   - 保持作者 Robert Zoller 的口语授课风格（这是录音文字稿）
   - 列表、表格保持结构

2. **格式处理**:
   - 保留原文中的 [N] 引用标记
   - 用 --- 分隔明显的话题转换
   - 原文中的拉丁语/希腊语术语保留原文并附中文翻译

3. **页脚清理**: 忽略版权声明、URL、重复标题等页脚内容。

4. **只输出中文翻译，不加额外解释。**"""


def clean_page(text: str) -> str:
    """Remove page headers, footers, copyright notices from extracted text."""
    lines = text.split("\n")
    cleaned = []

    # Patterns to remove
    skip_patterns = [
        re.compile(r"^© Copyright.*All Rights Reserved$", re.IGNORECASE),
        re.compile(r"^http://", re.IGNORECASE),
        re.compile(r"^New Library Limited$", re.IGNORECASE),
        re.compile(r"^New Library Publication$", re.IGNORECASE),
        re.compile(r"^London WC1N 3XX$"),
        re.compile(r"^England$"),
        re.compile(r"^contact@new-library\.com$", re.IGNORECASE),
        re.compile(r"^All Rights Reserved\.?$", re.IGNORECASE),
        re.compile(r"^MEDIEVAL ASTROLOGY FOUNDATION COURSE$"),
        re.compile(r"^ORIENTATION$"),
        re.compile(r"^Robert Zoller\.?$"),
        re.compile(r"^\d+$"),  # standalone page numbers (but keep [N] references)
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        skip = False
        for pat in skip_patterns:
            if pat.match(stripped):
                skip = True
                break
        if not skip:
            cleaned.append(stripped)

    # Remove consecutive blank lines (keep at most 1)
    result = []
    prev_blank = False
    for line in cleaned:
        if line == "":
            if not prev_blank:
                result.append(line)
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False

    return "\n".join(result).strip()


def detect_footnotes(text: str) -> tuple[str, list[str]]:
    """Detect footnote markers and extract footnote content from end of page.
    Returns (body_text, footnote_list)."""
    lines = text.split("\n")
    # Look for footnote markers like [1], [2] etc. in body
    footnote_markers = re.findall(r"\[(\d+)\]", text)
    if not footnote_markers:
        return text, []

    # Check if last few lines look like footnotes (start with number)
    footnotes = []
    body_end = len(lines)
    for i in range(len(lines) - 1, max(0, len(lines) - 10), -1):
        line = lines[i].strip()
        if re.match(r"^\d+[\.\s]", line):
            footnotes.insert(0, line)
            body_end = i
        else:
            break

    body = "\n".join(lines[:body_end]).strip()
    return body, footnotes


def translate_page(text: str, page_num: int, prev_summary: str = "") -> str:
    """Translate cleaned page text via DeepSeek API."""
    body, footnotes = detect_footnotes(text)

    user_content = f"第 {page_num + 1} 页：\n\n{body}"
    if footnotes:
        user_content += f"\n\n本页脚注：\n" + "\n".join(footnotes)

    if prev_summary:
        user_content = f"上文摘要（第 {page_num} 页前的内容）：{prev_summary}\n\n{user_content}"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    for attempt in range(3):
        try:
            resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=180)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                print(f"  API error (attempt {attempt+1}): {resp.status_code} - {resp.text[:200]}")
                if resp.status_code == 429:
                    time.sleep(10 * (attempt + 1))
        except Exception as e:
            print(f"  API exception (attempt {attempt+1}): {e}")
            time.sleep(5 * (attempt + 1))

    return f"[翻译失败 - 第{page_num+1}页]\n\n{text[:1000]}"


def main():
    if not DEEPSEEK_API_KEY:
        print("ERROR: Set DEEPSEEK_API_KEY environment variable.")
        print("  CMD: set DEEPSEEK_API_KEY=sk-...")
        sys.exit(1)

    progress_file = PROGRESS_DIR / f"{OUTPUT_NAME}_progress.json"
    output_file = OUTPUT_DIR / f"{OUTPUT_NAME}.txt"

    # Load or init progress
    if progress_file.exists():
        progress = json.loads(progress_file.read_text(encoding="utf-8"))
        print(f"Resuming: {len(progress)} pages already translated")
    else:
        progress = {}

    doc = fitz.open(str(PDF_PATH))
    total = doc.page_count
    print(f"PDF: {PDF_PATH.name}")
    print(f"Pages: {total}")
    print(f"Output: {output_file}")
    print()

    # Open output for appending
    output_lines = []

    for pg in range(total):
        page_key = str(pg)
        if page_key in progress:
            continue

        page = doc[pg]
        raw_text = page.get_text("text")
        cleaned = clean_page(raw_text)

        if len(cleaned) < 30:
            # Nearly empty page (diagram or blank)
            progress[page_key] = "[本页为图表或空白页]"
            print(f"  Page {pg+1}/{total}: skipped (empty/diagram)")
            if pg % 5 == 0:
                progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
            continue

        # Get previous page summary for context
        prev_summary = ""
        if pg > 0 and str(pg - 1) in progress:
            prev_text = progress[str(pg - 1)]
            if len(prev_text) > 200:
                prev_summary = prev_text[:200]

        print(f"  Page {pg+1}/{total}: translating ({len(cleaned)} chars)...", end=" ", flush=True)
        translated = translate_page(cleaned, pg, prev_summary)
        progress[page_key] = translated
        print(f"→ {len(translated)} chars")

        # Save progress every 5 pages
        if pg % 5 == 0 or pg == total - 1:
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(1)  # brief pause to avoid rate limiting

        # Rate limit
        time.sleep(0.5)

    doc.close()

    # Build final output
    print(f"\nBuilding output file...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"============================================================\n")
        f.write(f"Robert Zoller - Medieval Astrology Foundation Course\n")
        f.write(f"中世纪占星学基础教程\n")
        f.write(f"翻译时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总页数: {total}\n")
        f.write(f"============================================================\n\n")

        for pg in range(total):
            page_key = str(pg)
            if page_key in progress:
                f.write(f"\n--- 第 {pg + 1} 页 ---\n\n")
                f.write(progress[page_key])
                f.write("\n")

    print(f"Saved: {output_file}")
    print(f"Progress saved: {progress_file}")


if __name__ == "__main__":
    main()
