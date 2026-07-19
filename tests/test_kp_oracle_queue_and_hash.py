from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HASH_SCRIPT = ROOT / "scripts/kp_external_table_hash_manifest.py"
QUEUE = ROOT / "references/oracle/kp_cusp_worked_example_oracle_queue_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_kp_external_table_hash_manifest_reports_fixture_status() -> None:
    completed = subprocess.run(
        [sys.executable, str(HASH_SCRIPT)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["scope"] == "kp_external_table_hash_manifest"
    assert report["production_tuning_allowed"] is False
    assert report["table_id"] == "VedicAstro_KP_SL_Divisions"
    assert report["status"] in {"fixed_hash", "fixture_missing"}
    if report["status"] == "fixed_hash":
        assert len(report["sha256"]) == 64
    else:
        assert report["claim_status"] == "blocked_fixture_missing"


def test_kp_cusp_worked_example_oracle_queue_is_blocked_but_actionable() -> None:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert data["scope"] == "kp_cusp_worked_example_oracle_queue"
    assert data["status"] == "public_candidates_triaged"
    assert data["production_tuning_allowed"] is False
    assert data["claim_status"] == "blocked"
    required = {field["field"] for field in data["required_fields"]}
    assert {"cusp_longitude", "star_lord", "sub_lord", "sub_sub_lord", "source_url"}.issubset(required)
    assert len(data["queue"]) >= 4
    assert data["queue"][0]["candidate_strength"] == "strongest_current_candidate"
    assert all("oracle_ready" not in row["oracle_status"] for row in data["queue"])
    assert "raw/hash" in data["claim_boundary"]


def test_kp_hash_and_oracle_queue_are_indexed() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {packet["packet_id"]: packet for packet in data["packets"]}
    assert packets["kp_external_table_hash_manifest"]["path"] == "scripts/kp_external_table_hash_manifest.py"
    assert packets["kp_cusp_worked_example_oracle_queue"]["claim_status"] == "blocked"
