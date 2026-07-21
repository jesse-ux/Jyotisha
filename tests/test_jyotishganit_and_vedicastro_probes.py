import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_jyotishganit_field_probe_outputs_raw_hash_and_required_sections():
    out = subprocess.check_output(["python3", "scripts/jyotishganit_field_probe.py"], cwd=ROOT, text=True)
    data = json.loads(out)
    assert data["scope"] == "jyotishganit_field_probe"
    assert data["claim_status"] == "observation_only"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["raw_hash"]
    assert data["selected_hash"]
    for key in ["panchanga", "D2", "D4", "D9", "D10", "BAV_SAV", "Shadbala"]:
        assert key in data["coverage"]
    assert data["coverage"]["D2"] is True
    assert data["coverage"]["D4"] is True
    assert data["coverage"]["D9"] is True
    assert data["coverage"]["D10"] is True
    assert data["coverage"]["panchanga"] is True
    assert data["coverage"]["BAV_SAV"] is True
    assert data["coverage"]["Shadbala"] is False


def test_vedicastro_kp_api_probe_is_observation_only_even_when_import_blocks():
    out = subprocess.check_output(["python3", "scripts/vedicastro_kp_api_probe.py"], cwd=ROOT, text=True)
    data = json.loads(out)
    assert data["scope"] == "vedicastro_kp_api_probe"
    assert data["claim_status"] == "observation_only"
    assert data["source_sha256"]
    assert "get_rl_nl_sl_data" in data["api_surface"]["methods"]
    assert data["runtime_probe"]["attempted"] is True


def test_public_worked_example_queue_keeps_sources_unverified():
    data = json.loads((ROOT / "references/oracle/public_worked_example_queue_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["claim_status"] == "open_queue"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    topics = {row["topic"] for row in data["queues"]}
    assert "KP exact cusp star/sub/sub-sub lord" in topics
    assert "Muhurta Tarabala/Chandrabala/Rahu Kalam/Abhijit" in topics
    assert "Shadbala Virupa and Ashtakavarga component" in topics


def test_evidence_index_registers_new_probes():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    for packet_id in ["jyotishganit_field_probe", "vedicastro_kp_api_probe", "public_worked_example_queue"]:
        assert packet_id in packets
        assert packets[packet_id]["claim_status"] in {"observation_only", "open_queue"}
