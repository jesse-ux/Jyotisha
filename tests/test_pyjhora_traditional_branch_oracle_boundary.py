import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/pyjhora_traditional_branch_oracle_boundary_2026_07_23.json"


def test_pyjhora_traditional_boundary_is_matrix_only_not_runtime_copy() -> None:
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/pyjhora_traditional_branch_oracle_boundary.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["claim_status"] == "observation_boundary_matrix"
    assert data["consumer_policy"] == "sync_matrix_only_do_not_vendor_agpl_implementation"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["commercial_final_truth_allowed_count"] == 0


def test_pyjhora_traditional_boundary_covers_tajika_kp_and_advanced_av_fields() -> None:
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert set(data["matrices"]) == {"tajika", "kp_exact_cusp", "advanced_ashtakavarga"}
    for rows in data["matrices"].values():
        for row in rows:
            assert {
                "field",
                "local_repo_can_calculate",
                "pyjhora_can_observe",
                "jyotishganit_or_vedicastro_can_reference",
                "public_worked_example_status",
                "commercial_output_allowed",
            } <= set(row)
    assert data["matrices"]["kp_exact_cusp"][0]["commercial_output_allowed"] == "boundary_only"
    assert data["matrices"]["advanced_ashtakavarga"][-1]["commercial_output_allowed"] == "blocked_as_precise_timing_truth"
