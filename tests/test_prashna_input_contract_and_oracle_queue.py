import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references/oracle/prashna_input_contract_2026_07_20.json"
QUEUE = ROOT / "references/oracle/prashna_numeric_oracle_packet_queue_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_contract_requires_time_place_timezone_ayanamsa_node():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_oracle_queue.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    contract = data["contract"]
    assert contract["scope"] == "prashna_input_contract"
    required = {row["field"] for row in contract["required_fields"]}
    assert {"question_datetime_local", "location", "timezone", "ayanamsa", "node_mode"}.issubset(required)
    assert contract["claim_status"] == "ready_contract"


def test_prashna_queue_keeps_public_numeric_examples_candidate_only():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert queue["scope"] == "prashna_numeric_oracle_packet_queue"
    assert queue["claim_status"] == "open_queue"
    assert queue["summary"]["numeric_candidate_count"] >= 1
    assert queue["summary"]["oracle_ready_count"] == 0
    example = next(row for row in queue["rows"] if row["source_id"] == "vedastro_prasna_marga_ch5_sphuta_example")
    assert example["numeric_fields_present"] is True
    assert "trisphuta" in example["expected_values"]
    assert "complete_prashna_input" in example["missing_for_oracle"]
    assert example["upgrade_status"] == "candidate_not_oracle"


def test_prashna_contract_and_queue_are_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_input_contract_2026_07_20"]["claim_status"] == "ready_contract"
    assert packets["prashna_numeric_oracle_packet_queue_2026_07_20"]["claim_status"] == "open_queue"
