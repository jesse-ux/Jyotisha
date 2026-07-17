#!/usr/bin/env python3
"""Extract text from screenshots without requiring Homebrew-installed Tesseract."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_SHORTCUT_NAME = "Extract Text from Image"
VALID_BACKENDS = {"auto", "manual", "shortcuts", "tesseract"}


def choose_backend(requested: str = "auto") -> str:
    if requested != "auto":
        if requested not in VALID_BACKENDS:
            raise ValueError(f"unsupported backend: {requested}")
        return requested
    if shutil.which("shortcuts"):
        return "shortcuts"
    if shutil.which("tesseract"):
        return "tesseract"
    return "manual"


def _manual_transcript_path(image: Path, transcript_dir: Path | None) -> Path:
    base = transcript_dir or image.parent
    return base / f"{image.stem}.txt"


def _extract_manual(image: Path, transcript_dir: Path | None) -> dict[str, Any]:
    transcript = _manual_transcript_path(image, transcript_dir)
    if not transcript.is_file():
        return {
            "image_path": str(image),
            "text": "",
            "backend": "manual",
            "status": "blocked",
            "reason": "manual_transcript_missing",
            "expected_transcript_path": str(transcript),
        }
    return {
        "image_path": str(image),
        "text": transcript.read_text(encoding="utf-8"),
        "backend": "manual",
        "status": "ok",
    }


def _extract_shortcuts(image: Path, shortcut_name: str) -> dict[str, Any]:
    if not shutil.which("shortcuts"):
        return {"image_path": str(image), "text": "", "backend": "shortcuts", "status": "blocked", "reason": "shortcuts_cli_missing"}
    completed = subprocess.run(
        ["shortcuts", "run", shortcut_name, "-i", str(image)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    text = completed.stdout
    if completed.returncode != 0:
        return {
            "image_path": str(image),
            "text": text,
            "backend": "shortcuts",
            "status": "blocked",
            "reason": "shortcuts_run_failed",
            "stderr": completed.stderr.strip(),
            "shortcut_name": shortcut_name,
        }
    return {"image_path": str(image), "text": text, "backend": "shortcuts", "status": "ok"}


def _extract_tesseract(image: Path) -> dict[str, Any]:
    if not shutil.which("tesseract"):
        return {"image_path": str(image), "text": "", "backend": "tesseract", "status": "blocked", "reason": "tesseract_missing"}
    completed = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", "eng+chi_sim"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        return {
            "image_path": str(image),
            "text": completed.stdout,
            "backend": "tesseract",
            "status": "blocked",
            "reason": "tesseract_run_failed",
            "stderr": completed.stderr.strip(),
        }
    return {"image_path": str(image), "text": completed.stdout, "backend": "tesseract", "status": "ok"}


def extract_one(image: Path, *, backend: str = "auto", transcript_dir: Path | None = None, shortcut_name: str = DEFAULT_SHORTCUT_NAME) -> dict[str, Any]:
    selected = choose_backend(backend)
    if selected == "manual":
        return _extract_manual(image, transcript_dir)
    if selected == "shortcuts":
        return _extract_shortcuts(image, shortcut_name)
    if selected == "tesseract":
        return _extract_tesseract(image)
    raise ValueError(f"unsupported backend: {selected}")


def extract_many(
    images: list[Path],
    *,
    output: Path | None = None,
    backend: str = "auto",
    transcript_dir: Path | None = None,
    shortcut_name: str = DEFAULT_SHORTCUT_NAME,
) -> dict[str, Any]:
    items = [extract_one(image, backend=backend, transcript_dir=transcript_dir, shortcut_name=shortcut_name) for image in images]
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in items) + "\n", encoding="utf-8")
    return {
        "status": "ok" if items and all(item["status"] == "ok" for item in items) else "blocked",
        "backend": choose_backend(backend),
        "items": items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--backend", choices=sorted(VALID_BACKENDS), default="auto")
    parser.add_argument("--transcript-dir", type=Path)
    parser.add_argument("--shortcut-name", default=DEFAULT_SHORTCUT_NAME)
    parser.add_argument("--output", type=Path, default=Path("scratch/local/ocr_extract/ocr.jsonl"))
    args = parser.parse_args(argv)
    report = extract_many(
        args.images,
        output=args.output,
        backend=args.backend,
        transcript_dir=args.transcript_dir,
        shortcut_name=args.shortcut_name,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
