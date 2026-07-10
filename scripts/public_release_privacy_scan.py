#!/usr/bin/env python3
"""Scan release files for private birth-data residues."""

from __future__ import annotations

import argparse
import json
import os
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

LOCAL_DENY_PATTERN_FILE = Path("scratch/local/public_release_deny_patterns.txt")
ENV_DENY_PATTERNS = "PUBLIC_RELEASE_DENY_PATTERNS"


def _literal_patterns(values: Iterable[str], prefix: str) -> list[tuple[str, re.Pattern[str]]]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for index, value in enumerate(values, start=1):
        value = value.strip()
        if not value or value.startswith("#"):
            continue
        patterns.append((f"{prefix}_{index:02d}", re.compile(re.escape(value), re.IGNORECASE)))
    return patterns


def deny_patterns(root: Path = ROOT) -> list[tuple[str, re.Pattern[str]]]:
    patterns = _literal_patterns(os.environ.get(ENV_DENY_PATTERNS, "").splitlines(), "private_env_pattern")
    local_file = root / LOCAL_DENY_PATTERN_FILE
    if local_file.is_file():
        patterns.extend(
            _literal_patterns(
                local_file.read_text(encoding="utf-8", errors="ignore").splitlines(),
                "private_local_pattern",
            )
        )
    return patterns


def _is_skipped(path: Path, root: Path = ROOT) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    if rel in SKIP_FILES:
        return True
    return any(rel == item or rel.startswith(f"{item}/") for item in SKIP_DIRS)


def iter_release_files(root: Path = ROOT) -> Iterable[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        candidates = (root / line for line in completed.stdout.splitlines())
    else:
        candidates = (path for path in root.rglob("*") if path.is_file())
    for path in candidates:
        if not path.is_file() or _is_skipped(path, root):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def scan_text(
    path: Path,
    text: str,
    patterns: Iterable[tuple[str, re.Pattern[str]]] | None = None,
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    try:
        display_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        display_path = path.as_posix()
    for rule_id, pattern in (patterns if patterns is not None else deny_patterns()):
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
    patterns = deny_patterns(root)
    for path in iter_release_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        findings.extend(scan_text(path, text, patterns))
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
