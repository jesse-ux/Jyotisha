import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/muhurta_factor_scoring_readiness_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_muhurta_readiness_script_outputs_supporting_only_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/muhurta_factor_scoring_readiness.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "muhurta_factor_scoring_readiness"
    assert data["claim_status"] == "partial"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["factor_count"] == 6
    assert data["summary"]["scored_verdict_ready_count"] == 0


def test_muhurta_readiness_artifact_blocks_final_scored_verdict():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["summary"]["supporting_context_only_count"] == 6
    assert all(row["allowed_product_use"] == "supporting_context_only" for row in data["rows"])
    assert {row["factor"] for row in data["rows"]} == {
        "panchanga_suddhi",
        "activity_specific_rules",
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "abhijit",
    }
    assert "No final scored Muhurta verdict is ready" in data["boundary"]


def test_evidence_index_registers_muhurta_readiness():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["muhurta_factor_scoring_readiness"]["claim_status"] == "partial"
