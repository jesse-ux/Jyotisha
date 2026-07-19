import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/d1_d60_source_use_readiness_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_d1_d60_source_readiness_script_keeps_scope_narrow():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/d1_d60_source_use_readiness.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "d1_d60_source_use_readiness"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["candidate_source_count"] >= 3
    assert data["summary"]["numeric_oracle_ready_count"] == 0


def test_d1_d60_source_readiness_allows_only_names_and_use_notes():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["summary"]["allowed_scope"] == "names_and_use_notes_only"
    assert all(row["allowed_update"] == "names_and_use_notes_only" for row in data["sources"])
    assert all("numeric_formula" in row["blocked_update"] for row in data["sources"])
    assert "Generic-only divisions stay hidden" in data["boundary"]


def test_evidence_index_registers_d1_d60_source_readiness():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["d1_d60_source_use_readiness"]["claim_status"] == "partial"
