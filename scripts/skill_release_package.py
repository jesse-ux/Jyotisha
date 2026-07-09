#!/usr/bin/env python3
"""Dry-run or build a cleaned skill release zip."""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

try:
    from scripts.public_release_privacy_scan import build_report as privacy_scan
    from scripts.skill_release_manifest import build_report as release_manifest
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from public_release_privacy_scan import build_report as privacy_scan
    from skill_release_manifest import build_report as release_manifest


ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = ("scratch/", "references/open_source_sources/", ".git/", "__pycache__/")
SKIP_NAMES = {".env", ".env.local"}
GENERATED_DOCS = {
    "INSTALL.md": """# Jyotish Skill Install

1. Unzip this package into a local folder.
2. Run `python3 scripts/public_release_privacy_scan.py`.
3. Run `python3 scripts/user_invocation_acceptance_check.py`.
4. If the check passes, load this folder as a Codex skill/plugin or call `mcp_server.py`.
5. VedAstro cloud evidence is optional. Without `official_raw_response`, reports must say `official_blocked` or `local_fallback`.

Do not add private birth data, API keys, or desktop oracle screenshots to this package.
""",
    "USER_PROMPTS.md": """# User Prompts

## User Has No Question

请根据我的出生信息先运行统一主链，生成 evidence_packet、guided_topics 和 Technique Audit Table。
不要反问我想看什么；请先给出 3-5 个最值得继续看的方向，并附可直接复制的问题。

## High-Rigor Reading

请使用 strict_workflow，并在输出中标明 VedAstro / PyJHora-JHora / jyotishganit / Real Case Calibration 的状态。
如果没有 VedAstro official_raw_response，请标记 official_blocked 或 local_fallback。

## Birth-Time Rectification

请使用主动问询式校时：先生成候选时间扫描和选择题，我只回答 A/B/C/D。
""",
}


def _git_files() -> list[str]:
    completed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return sorted(item.decode("utf-8") for item in completed.stdout.split(b"\0") if item)


def _allowed(path: str) -> bool:
    if Path(path).name in SKIP_NAMES:
        return False
    lowered = path.lower()
    if "private" in lowered or any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    return True


def _edition_files(edition: str) -> list[str]:
    manifest = release_manifest()
    if edition not in manifest["editions"]:
        raise ValueError(f"unknown edition: {edition}")
    files = _git_files()
    if edition == "basic_git":
        keep = ("SKILL.md", "README.md", "mcp_server.py", ".codex-plugin/", "scripts/", "tests/")
        files = [path for path in files if path in keep or any(path.startswith(prefix) for prefix in keep if prefix.endswith("/"))]
    return [path for path in files if _allowed(path)]


def build_package_plan(edition: str = "premium_cloud_drive") -> dict[str, Any]:
    privacy = privacy_scan()
    files = _edition_files(edition)
    return {
        "scope": "skill_release_package",
        "schema_version": 1,
        "edition": edition,
        "mode": "dry_run",
        "privacy_scan_status": privacy["status"],
        "file_count": len(files),
        "files": files,
        "generated_files": sorted(GENERATED_DOCS),
        "boundary": "Dry-run plan only; use --write-zip to create a local zip, then upload manually if desired.",
    }


def write_zip(edition: str, output: Path) -> dict[str, Any]:
    plan = build_package_plan(edition)
    if plan["privacy_scan_status"] != "pass":
        raise RuntimeError("privacy scan failed; refusing to write release zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in plan["files"]:
            archive.write(ROOT / rel, rel)
        for rel, text in GENERATED_DOCS.items():
            archive.writestr(rel, text)
    return {**plan, "mode": "write_zip", "zip_path": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", choices=["basic_git", "premium_cloud_drive"], default="premium_cloud_drive")
    parser.add_argument("--write-zip", type=Path)
    args = parser.parse_args()
    report = write_zip(args.edition, args.write_zip) if args.write_zip else build_package_plan(args.edition)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
