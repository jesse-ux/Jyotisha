from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_commercial_privacy_scan_reuses_public_release_scanner() -> None:
    source = (ROOT / "scripts/commercial_privacy_artifact_scan.py").read_text()
    assert "from public_release_privacy_scan import build_report" in source
    assert "no_real_user_birth_data_private_cases_or_secret_values_in_public_artifacts" in source
    assert "hip_main.dat" in source


def test_commercial_privacy_scan_json_contract_passes_current_tree() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/commercial_privacy_artifact_scan.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    report = json.loads(completed.stdout)
    assert report["scope"] == "commercial_privacy_artifact_scan"
    assert report["scanner_reuse"] == "scripts/public_release_privacy_scan.py"
    assert report["status"] == "pass"
    assert report["finding_count"] == 0
    assert "hip_main.dat" in report["local_runtime_assets_not_committed"]
