import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/shadbala_component_closure_batch2_2026_07_23.json"


def test_batch2_generator_outputs_sthana_kala_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/shadbala_component_closure_batch2.py"],
            cwd=ROOT,
            text=True,
        )
    )

    assert data["scope"] == "shadbala_component_closure_batch2"
    assert data["claim_status"] == "component_explanatory_partial"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["summary"]["row_count"] == 14
    assert data["summary"]["component_counts"] == {"kala": 7, "sthana": 7}
    assert data["summary"]["absolute_truth_upgrade_count"] == 0
    assert data["summary"]["blocked_or_unresolved_row_count"] == 14


def test_batch2_rows_expose_subcomponent_formula_queues():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    rows = data["rows"]

    sthana = [row for row in rows if row["component"] == "sthana"]
    kala = [row for row in rows if row["component"] == "kala"]

    assert len(sthana) == 7
    assert len(kala) == 7
    assert all("moolatrikona_degree_range" in row["subcomponent_queue"] for row in sthana)
    assert all("sunrise/sunset and local apparent time contract" in row["subcomponent_queue"] for row in kala)


def test_batch2_does_not_promote_formula_truth():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    statuses = data["summary"]["closure_status_counts"]

    assert statuses["formula_mismatch_kala_subcomponent_unresolved"] == 7
    assert (
        statuses["formula_mismatch_sthana_subcomponent_unresolved"]
        + statuses["method_variant_dignity_policy_unresolved"]
        == 7
    )
    for row in data["rows"]:
        assert row["claim_upgrade"] == "none"
        assert row["source_formula"].startswith("shadbala_")
        assert row["unit_contract"]
        assert row["source_evidence"]
        assert row["blocked_reason"]
        assert row["truth_matrix_allowed"] is False
        assert row["production_tuning_allowed"] is False
