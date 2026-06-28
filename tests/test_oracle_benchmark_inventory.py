#!/usr/bin/env python3
"""Tests for the oracle/benchmark single-truth inventory."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_inventory(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/oracle_benchmark_inventory.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )


def test_oracle_benchmark_inventory_maps_high_value_assets() -> None:
    completed = run_inventory("--format", "json")

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["scope"] == "oracle_benchmark_single_truth_inventory"
    assert report["schema_version"] == 1
    assert report["summary"]["oracle_registry_count"] >= 3
    assert report["summary"]["oracle_case_count"] >= 9
    assert report["summary"]["pending_packet_count"] >= 18
    assert report["summary"]["pyjhora_artifact_count"] >= 8
    assert report["files"]["pyjhora_manifest"]["path"].endswith(
        "references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json"
    )

    registry_paths = {entry["path"] for entry in report["files"]["oracle_registries"]}
    assert "references/oracle/dasha_shadbala_oracle_cases.json" in registry_paths
    assert "references/oracle/tajika_annual_oracle_cases.json" in registry_paths

    case_paths = {entry["path"] for entry in report["files"]["oracle_cases"]}
    assert "references/oracle/cases/steve_jobs.json" in case_paths
    assert "references/oracle/cases/marilyn_monroe.json" in case_paths

    pending_paths = {entry["path"] for entry in report["files"]["pending_packets"]}
    assert (
        "references/oracle/artifacts/pending_packets/"
        "external_template_steve_jobs_varshaphala_1984_lahiri.json"
    ) in pending_paths
    assert (
        "references/oracle/artifacts/pending_packets/"
        "external_template_historical_dst_london_varshaphala_1943_lahiri.json"
    ) in pending_paths

    assert report["fronts"]["dasha"]["pending_packet_count"] >= 3
    assert report["fronts"]["shadbala"]["pending_packet_count"] >= 4
    assert report["fronts"]["tajika_sahams"]["pending_packet_count"] >= 5
    assert "external oracle evidence only" in report["boundary"]


def test_oracle_benchmark_inventory_outputs_markdown_and_can_write_file(tmp_path: Path) -> None:
    output = tmp_path / "oracle_benchmark_inventory.md"
    completed = run_inventory("--format", "markdown", "--output", str(output))

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output.exists()
    markdown = output.read_text(encoding="utf-8")
    assert "# Oracle Benchmark Single-Truth Inventory" in markdown
    assert "Oracle Registries" in markdown
    assert "Pending Evidence Packets" in markdown
    assert "PyJHora Black-Box Assets" in markdown
    assert "Next Actions" in markdown
