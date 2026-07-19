import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "references/oracle/high_rigor_closure_gate_snapshot_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_high_rigor_closure_snapshot_generator_writes_blocked_snapshot():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/high_rigor_closure_snapshot.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "high_rigor_closure_gate_snapshot"
    assert data["created_at"] == "2026-07-20"
    assert data["source_scope"] == "high_rigor_closure_gate"
    assert data["overall_status"] == "blocked"
    assert data["production_tuning_allowed"] is False
    assert data["snapshot_hash"]


def test_high_rigor_closure_snapshot_artifact_and_index_are_present():
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert data["overall_status"] == "blocked"
    gate_ids = {gate["gate_id"] for gate in data["gates"]}
    assert {"external_numeric_oracle", "independent_negative_holdout", "kp_exact_cusp", "full_scoring_contracts"} <= gate_ids

    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["high_rigor_closure_gate_snapshot_2026_07_20"]["claim_status"] == "blocked"
