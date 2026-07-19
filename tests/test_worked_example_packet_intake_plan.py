import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references" / "oracle" / "worked_example_packet_intake_plan_2026_07_20.json"
INDEX = ROOT / "references" / "oracle" / "evidence_packet_index_2026_07_19.json"


def test_worked_example_packet_intake_plan_groups_candidates_by_domain():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/worked_example_packet_intake_plan.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "worked_example_packet_intake_plan"
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["candidate_count"] >= 5
    assert data["summary"]["oracle_ready_count"] == 0
    domains = {row["domain"] for row in data["domain_queues"]}
    assert {"kp_precision_timing", "shadbala_component_closure", "muhurta_factor_scoring"}.issubset(domains)


def test_worked_example_packet_intake_plan_preserves_blockers_and_next_actions():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    rows = {row["domain"]: row for row in data["domain_queues"]}
    kp = rows["kp_precision_timing"]
    assert kp["highest_status"] in {"runtime_only_public_oracle_missing", "reference_table_hash_needed"}
    assert "public_numeric_expected_values" in kp["blocking_fields"]
    assert kp["next_action_owner"] == "oracle_intake"
    assert all(item["upgrade_policy"] == "observation_only_until_numeric_packet" for row in data["domain_queues"] for item in row["items"])


def test_worked_example_packet_intake_plan_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["worked_example_packet_intake_plan_2026_07_20"]
    assert packet["domain"] == "worked_example_collection"
    assert packet["claim_status"] == "open_queue"
