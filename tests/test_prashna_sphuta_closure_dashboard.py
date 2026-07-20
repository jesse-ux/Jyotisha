import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_closure_dashboard_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_closure_dashboard_summarizes_chain_and_blockers():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_closure_dashboard.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_closure_dashboard"
    assert data["claim_status"] == "blocked_until_human_labels"
    assert data["summary"]["packet_chain_count"] >= 9
    assert data["summary"]["truth_upgrade_count"] == 0
    assert data["summary"]["blocked_gate_count"] >= 2
    gates = {gate["gate_id"]: gate for gate in data["gates"]}
    assert gates["human_line_review"]["status"] == "blocked"
    assert gates["complete_prashna_input"]["status"] == "blocked"


def test_prashna_sphuta_closure_dashboard_preserves_commercial_boundary():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["commercial_sync_status"] == "research_observation_only"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert "do_not_use_for_deterministic_prashna_verdict" in data["forbidden_uses"]


def test_prashna_sphuta_closure_dashboard_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_closure_dashboard_2026_07_20"]["claim_status"] == "blocked_until_human_labels"
