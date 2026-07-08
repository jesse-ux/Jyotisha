#!/usr/bin/env python3
"""Scan release files for private birth-data residues."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "scratch",
    "references/open_source_sources",
}

SKIP_FILES = {
    "scripts/public_release_privacy_scan.py",
    "tests/test_public_release_privacy_scan.py",
}

TEXT_SUFFIXES = {
    ".cfg",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

DENY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_exact_iso_birth_date", re.compile(r"REDACTED_DATE")),
    ("private_compact_birth_datetime", re.compile(r"REDACTED_DATE[_-]?REDACTED_TIME")),
    ("private_slug_birth_date", re.compile(r"REDACTED_YEAR[_-]04[_-]17")),
    ("private_birth_time_literal", re.compile(r"REDACTED_YEAR.{0,120}\bREDACTED_TIME\b|\bREDACTED_TIME\b.{0,120}REDACTED_YEAR|REDACTED_TIME")),
    ("private_place_han", re.compile(r"REDACTED_PLACE|REDACTED_PLACE|REDACTED_HOSPITAL")),
    ("private_case_slug", re.compile(r"user_REDACTED_YEAR|redacted_place", re.IGNORECASE)),
    (
        "private_birth_dict_tuple",
        re.compile(
            r"(?s)(?:year|--year|datetime\()\D*REDACTED_YEAR.{0,220}"
            r"(?:month|--month|,\s*)\D*4.{0,220}"
            r"(?:day|--day|,\s*)\D*17.{0,220}"
            r"(?:hour|--hour|,\s*)\D*14.{0,220}"
            r"(?:minute|--minute|,\s*)\D*49"
        ),
    ),
]


def _is_skipped(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel in SKIP_FILES:
        return True
    return any(rel == item or rel.startswith(f"{item}/") for item in SKIP_DIRS)


def iter_release_files(root: Path = ROOT) -> Iterable[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    for line in completed.stdout.splitlines():
        path = root / line
        if not path.is_file() or _is_skipped(path):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_text(path: Path, text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    try:
        display_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        display_path = path.as_posix()
    for rule_id, pattern in DENY_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                {
                    "rule_id": rule_id,
                    "path": display_path,
                    "line": line,
                }
            )
    return findings


def build_report(root: Path = ROOT) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in iter_release_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        findings.extend(scan_text(path, text))
    return {
        "scope": "public_release_privacy_scan",
        "scanned_files": scanned,
        "finding_count": len(findings),
        "findings": findings,
        "status": "pass" if not findings else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{report['status']}: {report['finding_count']} findings")
        for finding in report["findings"]:
            print(f"{finding['path']}:{finding['line']} {finding['rule_id']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
