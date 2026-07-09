#!/usr/bin/env python3
"""Build the public/basic vs premium/cloud skill release manifest."""

from __future__ import annotations

import json
from typing import Any

try:
    from scripts.diagnose_external_engine_adapters import build_report as external_engine_report
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from diagnose_external_engine_adapters import build_report as external_engine_report


REPO_URL = "https://github.com/732642856/yinduzhanxing"


def _external_boundary() -> dict[str, Any]:
    diagnostics = external_engine_report()
    engines = diagnostics.get("engines", {})
    return {
        "VedAstro": {
            "status": engines.get("VedAstro", {}).get("status"),
            "runtime_dependency": False,
            "completion_gate": "official_raw_response required before claiming official cloud closure",
        },
        "PyJHora/JHora": {
            "status": engines.get("PyJHora/JHora", {}).get("status"),
            "runtime_dependency": False,
            "license_boundary": engines.get("PyJHora/JHora", {}).get("license_boundary"),
        },
        "JHora desktop": {
            "status": "manual_oracle_only",
            "runtime_dependency": False,
            "boundary": "Desktop screenshots/exports can be used as external oracle evidence; do not vendor JHora.",
        },
        "jyotishganit": {
            "status": engines.get("jyotishganit", {}).get("status"),
            "runtime_dependency": False,
            "license": engines.get("jyotishganit", {}).get("license"),
        },
    }


def build_report() -> dict[str, Any]:
    return {
        "scope": "skill_release_manifest",
        "schema_version": 1,
        "editions": {
            "basic_git": {
                "distribution": "public_git_repository",
                "source": REPO_URL,
                "included": [
                    "SKILL.md",
                    ".codex-plugin/plugin.json",
                    "mcp_server.py",
                    "scripts/",
                    "tests/",
                    "README.md",
                ],
                "excluded": ["private local reports", "cloud-drive premium notes", "manual oracle screenshots"],
            },
            "premium_cloud_drive": {
                "distribution": "cloud_drive_zip",
                "source": "operator-built package from the same cleaned repo revision",
                "included": [
                    "basic_git contents",
                    "guided user prompts",
                    "release checklist",
                    "offline install notes",
                    "optional .env.example templates",
                ],
                "excluded": ["personal birth data", "private PDFs", "API keys", "JHora/PyJHora binaries"],
            },
        },
        "privacy_boundary": {
            "private_birth_data_allowed": False,
            "excluded_material": [
                "personal_case_reports",
                "private_birth_records",
                "private_pdf_exports",
                "api_keys_or_env_local",
                "manual_oracle_screenshots_with_identity",
            ],
        },
        "external_engine_boundary": _external_boundary(),
        "acceptance_commands": [
            "python3 scripts/public_release_privacy_scan.py",
            "python3 scripts/user_invocation_acceptance_check.py",
            "python3 scripts/diagnose_external_engine_adapters.py --json",
            "python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45",
        ],
        "boundary": "This manifest defines package contents and guards; it does not build or upload a zip.",
    }


def main() -> int:
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
