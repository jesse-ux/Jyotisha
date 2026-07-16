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

Basic Git version: https://github.com/732642856/yinduzhanxing

1. Unzip this package into a local folder.
2. Run `python3 scripts/public_release_privacy_scan.py`.
3. Run `python3 scripts/user_invocation_acceptance_check.py`.
4. Run `python3 scripts/skill_release_package.py --edition premium_cloud_drive`.
5. If the checks pass, load this folder as a Codex skill/plugin or call `mcp_server.py`.
6. VedAstro cloud evidence is optional. Without `official_raw_response`, reports must say `official_blocked` or `local_fallback`.

Do not add private birth data, API keys, or desktop oracle screenshots to this package.
""",
    "USER_PROMPTS.md": """# User Prompts

## User Has No Question

请根据我的出生信息先运行统一主链，生成 evidence_packet、guided_topics 和 Technique Audit Table。
不要反问我想看什么；请先给出 3-5 个最值得继续看的方向，并附可直接复制的问题。

## High-Rigor Reading

请使用 strict_workflow，并在输出中标明 VedAstro / PyJHora-JHora / jyotishganit / Real Case Calibration 的状态。
如果没有 VedAstro official_raw_response，请标记 official_blocked 或 local_fallback。
如果我提供西方占星导出，请作为 western_oracle_payload 进入统一主链，不要把单边西占信号说成双系统互证。

## Highest Quality Mode

请走高级版最高品质流程：direct_chart 或 rectification 入口 → evidence_packet → Technique Audit Table → VedAstro 三态 → 三引擎 parity replay 状态 → Real Case outcome replay 状态 → guided_topics。

## Birth-Time Rectification

请使用主动问询式校时：先生成候选时间扫描和选择题，我只回答 A/B/C/D。
""",
    "SALES_PACKAGE.md": """# Premium Skill Sales Package

Edition: premium_cloud_drive

## What This Package Includes

- Unified Jyotish runtime entrypoints for skill, MCP, API, and local scripts.
- Evidence packet workflow for D1/D9/D10/D2/D4, dasha boundaries, audit rows, and external oracle status.
- Guided topic entrypoint for users who do not know what to ask.
- Strict workflow prompts for high-rigor readings.
- Release hygiene checks for privacy, clean unzip usage, and user invocation acceptance.

## What This Package Does Not Include

- Private birth data, private case reports, API keys, or desktop oracle screenshots.
- Guaranteed VedAstro cloud closure without `official_raw_response`.
- Completed PyJHora/JHora parity rows unless the operator imports external raw oracle outputs.
- Completed real case replay unless structured case outcomes are imported.

Do not include private birth data in this package. Users provide their own birth data at runtime.
""",
    "GUIDED_ENTRYPOINT.md": """# Guided Entrypoint

Use this when the user loads the skill but does not know how to ask.

## Default Flow

1. Ask for birth date, exact or approximate birth time, birthplace, and question language.
2. Run `direct_chart` when birth time is reliable; run `rectification` when birth time is uncertain.
3. Generate `evidence_packet`, `guided_topics`, and `Technique Audit Table` before interpretation.
4. Use `blind=true` when prior personal feedback must not influence the reading.
5. Mark VedAstro as `official_verified`, `official_blocked`, or `local_fallback`.
6. Mark PyJHora/JHora, jyotishganit, Western oracle, and Real Case Calibration as `used`, `partial`, or `blocked`.

## User-Facing Starter

请提供出生日期、出生时间、出生地点和想看的语言。
如果你不知道该问什么，我会先运行 evidence packet，然后给出 3-5 个最值得继续看的主题。

## Output Requirements

- Start from evidence, not story.
- Show blocked or partial techniques.
- Never claim official cloud evidence without raw official evidence.
- Keep `guided_topics` available for the next turn.
""",
}

REQUIRED_CONTRACTS = [
    "references/real_case_calibration/replay_manifest.json",
    "references/oracle/three_engine_parity_replay_manifest.json",
    "references/oracle/western_oracle_adapter_contract.md",
    "scripts/user_invocation_acceptance_check.py",
    "scripts/diagnose_external_engine_adapters.py",
    "scripts/western_chart_engine.py",
    "scripts/western_timing_engine.py",
]


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
    files = sorted(set(files) | {path for path in REQUIRED_CONTRACTS if (ROOT / path).is_file()})
    if edition == "basic_git":
        keep = ("SKILL.md", "README.md", "mcp_server.py", ".codex-plugin/", "scripts/", "tests/")
        files = [path for path in files if path in keep or any(path.startswith(prefix) for prefix in keep if prefix.endswith("/"))]
    return [path for path in files if _allowed(path)]


def _required_contracts() -> dict[str, bool]:
    return {path: (ROOT / path).is_file() for path in REQUIRED_CONTRACTS}


def _package_acceptance(edition: str, privacy: dict[str, Any], files: list[str]) -> dict[str, Any]:
    contracts = _required_contracts()
    return {
        "scope": "skill_release_package_acceptance",
        "schema_version": 1,
        "edition": edition,
        "status": "pass" if privacy["status"] == "pass" and all(contracts.values()) else "blocked",
        "privacy_scan_status": privacy["status"],
        "file_count": len(files),
        "required_contracts": contracts,
        "acceptance_commands": release_manifest()["acceptance_commands"],
        "boundary": (
            "Package acceptance proves release hygiene and contracts only; it does not prove external oracle raw "
            "closure or same-chart parity until replay manifests contain imported rows."
        ),
    }


def _generated_docs(edition: str, privacy: dict[str, Any], files: list[str]) -> dict[str, str]:
    manifest = release_manifest()
    acceptance = _package_acceptance(edition, privacy, files)
    docs = dict(GENERATED_DOCS)
    docs["RELEASE_MANIFEST.json"] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    docs["PACKAGE_ACCEPTANCE.json"] = json.dumps(acceptance, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return docs


def build_package_plan(edition: str = "premium_cloud_drive") -> dict[str, Any]:
    privacy = privacy_scan()
    files = _edition_files(edition)
    generated_docs = _generated_docs(edition, privacy, files)
    acceptance = _package_acceptance(edition, privacy, files)
    return {
        "scope": "skill_release_package",
        "schema_version": 1,
        "edition": edition,
        "mode": "dry_run",
        "privacy_scan_status": privacy["status"],
        "file_count": len(files),
        "files": files,
        "generated_files": sorted(generated_docs),
        "required_contracts": acceptance["required_contracts"],
        "package_acceptance_status": acceptance["status"],
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
        privacy = privacy_scan()
        for rel, text in _generated_docs(edition, privacy, plan["files"]).items():
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
