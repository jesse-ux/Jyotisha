#!/usr/bin/env python3
"""Audit VedAstro identity evidence without upgrading hosted truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _field(name: str, value, source: str, blocker: str = "") -> dict:
    ok = value not in (None, "", [], {})
    return {
        "field": name,
        "status": "complete" if ok else "blocked",
        "value": value if ok else None,
        "source": source,
        "blocker": "" if ok else blocker,
    }


def build_audit(archive_path: Path, runtime_path: Path) -> dict:
    archive = _load(archive_path)
    runtime = _load(runtime_path)
    evidence = [
        _field("package_sha256", runtime.get("package_sha256") or archive.get("package_hash"), str(runtime_path)),
        _field("library_dll_sha256", runtime.get("library_dll_sha256"), str(runtime_path)),
        _field("assembly_version", runtime.get("assembly_version"), str(runtime_path)),
        _field("assembly_informational_version", runtime.get("assembly_informational_version"), str(runtime_path)),
        _field("public_method_contracts", runtime.get("public_method_contracts"), str(runtime_path)),
        _field("runtime_image_digest", runtime.get("runtime_image_digest"), str(runtime_path)),
        _field(
            "source_commit",
            archive.get("source_commit") or runtime.get("source_commit"),
            str(archive_path),
            "source commit not present in NuGet catalog/runtime contract; hosted API identity still needs upstream metadata or pinned source checkout.",
        ),
    ]
    complete = sum(row["status"] == "complete" for row in evidence)
    blocked = sum(row["status"] == "blocked" for row in evidence)
    return {
        "scope": "vedastro_identity_evidence_audit",
        "package": runtime["package"],
        "version": runtime["version"],
        "license": runtime["license"],
        "archive": str(archive_path),
        "runtime_contract": str(runtime_path),
        "runtime_candidate_status": "complete" if blocked <= 1 else "partial",
        "hosted_identity_status": archive["hosted_api_status"],
        "truth_upgrade_allowed": False,
        "production_tuning_allowed": False,
        "boundary": "NuGet/runtime identity can be pinned locally; hosted api.vedastro.org remains blocked without upstream build/method metadata.",
        "summary": {
            "required_field_count": len(evidence),
            "complete_count": complete,
            "blocked_count": blocked,
            "method_contract_count": len(runtime.get("public_method_contracts") or []),
        },
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("references/oracle/vedastro_identity_archive_2026_07_19.json"),
    )
    parser.add_argument(
        "--runtime",
        type=Path,
        default=Path("references/oracle/artifacts/vedastro_nuget_1_2_0_runtime_contract.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = build_audit(args.archive, args.runtime)
    text = json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
