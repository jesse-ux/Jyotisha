from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ocr_extract  # noqa: E402


def test_manual_transcript_backend_writes_jsonl(tmp_path: Path) -> None:
    image = tmp_path / "IMG_3502.PNG"
    image.write_bytes(b"not-a-real-image")
    transcript = tmp_path / "IMG_3502.txt"
    transcript.write_text("Arudha Lagna\nUpapada\n", encoding="utf-8")
    output = tmp_path / "ocr.jsonl"

    report = ocr_extract.extract_many([image], output=output, transcript_dir=tmp_path, backend="manual")

    assert report["status"] == "ok"
    assert report["items"][0]["backend"] == "manual"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows == [
        {
            "image_path": str(image),
            "text": "Arudha Lagna\nUpapada\n",
            "backend": "manual",
            "status": "ok",
        }
    ]


def test_missing_manual_transcript_is_blocked(tmp_path: Path) -> None:
    image = tmp_path / "IMG_3503.PNG"
    image.write_bytes(b"not-a-real-image")

    report = ocr_extract.extract_many([image], transcript_dir=tmp_path, backend="manual")

    assert report["status"] == "blocked"
    assert report["items"][0]["reason"] == "manual_transcript_missing"


def test_backend_auto_prefers_shortcuts_before_tesseract(monkeypatch) -> None:
    monkeypatch.setattr(ocr_extract.shutil, "which", lambda name: f"/usr/bin/{name}" if name in {"shortcuts", "tesseract"} else None)

    assert ocr_extract.choose_backend("auto") == "shortcuts"
