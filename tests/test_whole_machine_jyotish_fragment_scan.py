import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "references/oracle/whole_machine_jyotish_fragment_scan_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_whole_machine_fragment_scan_records_external_and_privacy_buckets():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert data["scope"] == "whole_machine_jyotish_fragment_scan_2026_07_21"
    assert summary["files_with_signals"] >= 2000
    assert summary["external_signal_files"] >= 1500
    assert summary["privacy_blocked_files"] >= 900
    assert summary["reviewable_external_files"] >= 700


def test_scan_keeps_old_workbuddy_out_of_truth_source():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    policy = data["decision_policy"]

    assert policy["workbuddy_fragment"] == "reference only; never truth source"
    assert policy["privacy_review_required"] == "forbidden until human privacy review"

    workbuddy_rows = [
        row for row in data["reviewable_external_candidates"]
        if row["category"] == "workbuddy_fragment"
    ]
    assert workbuddy_rows
    assert all(row["decision"] == "reference_only_candidate_not_truth_source" for row in workbuddy_rows)


def test_scan_records_reference_layers_that_exist_but_are_not_fully_called():
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    runtime = data["runtime_invocation_findings"]

    assert runtime["interpretation_source_runtime_coverage_status"] == "partial"
    assert "references/open_source_sources/jyotishganit" in runtime["not_fully_closed_reference_layers"]
    assert "references/open_source_sources/VedicAstro" in runtime["not_fully_closed_reference_layers"]
    assert runtime["inventory_gate_status"] == "pass"


def test_fragment_scan_is_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "whole_machine_jyotish_fragment_scan_2026_07_21"
    )

    assert entry["domain"] == "fragment_governance"
    assert entry["claim_status"] == "open_queue"
    assert "not truth source" in entry["claim_boundary"]
