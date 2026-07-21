import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/real_case_calibration/real_case_website_e2e_eval_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_real_case_website_e2e_eval_builds_twenty_case_contract():
    data = json.loads(subprocess.check_output(["python3", "scripts/real_case_website_e2e_eval.py"], cwd=ROOT, text=True))
    assert data["scope"] == "real_case_website_e2e_eval"
    assert data["case_count"] == 20
    assert data["claim_status"] == "ready_contract"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False


def test_real_case_website_e2e_eval_requires_core_runtime_context():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    required = {"D1", "Dasha", "functional_benefic_malefic", "claim_boundary", "similar_case_reference_allowed"}
    assert all(required <= set(case["expected_runtime_context"]) for case in data["cases"])
    domains = {domain for case in data["cases"] for domain in case["domains"]}
    assert {"career", "wealth", "marriage", "health", "migration", "family", "education", "timing", "annual"} <= domains


def test_real_case_website_e2e_eval_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    packet = packets["real_case_website_e2e_eval_2026_07_20"]
    assert packet["claim_status"] == "ready_contract"
    assert "not an accuracy benchmark" in packet["claim_boundary"]
