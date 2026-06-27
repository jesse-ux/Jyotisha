from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pyjhora_oracle_artifact_manifest_reports_current_blackbox_assets() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/generate_pyjhora_oracle_artifact_manifest.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "pyjhora_oracle_artifact_manifest"
    assert report["artifact_count"] >= 5
    assert report["packet_count"] >= 4
    assert report["fronts"]["dasha"]["artifact_count"] >= 2
    assert report["fronts"]["shadbala"]["artifact_count"] >= 2
    assert report["fronts"]["tajika_sahams"]["artifact_count"] >= 1
    assert report["files"]["manifest"].endswith("references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json")

    manifest = ROOT / "references" / "oracle" / "artifacts" / "pyjhora_oracle_artifact_manifest.json"
    assert manifest.exists()
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["scope"] == "pyjhora_oracle_artifact_manifest"
    assert "pyjhora_steve_jobs_dasha_stdout_20260627.txt" in manifest_data["artifacts"]
    assert "external_template_steve_jobs_dasha_lahiri_pyjhora_20260627.json" in manifest_data["pending_packets"]
