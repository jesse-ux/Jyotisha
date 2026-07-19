import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references/oracle/d1_d60_varga_mapping_registry_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_generator_outputs_all_d1_to_d60_rows():
    data = json.loads(
        subprocess.check_output(["python3", "scripts/d1_d60_varga_mapping_registry.py"], cwd=ROOT, text=True)
    )
    assert data["scope"] == "d1_d60_varga_mapping_registry"
    assert data["summary"]["total_rows"] == 60
    assert [row["number"] for row in data["rows"]] == list(range(1, 61))
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False


def test_registry_marks_formal_vs_generic_rows():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = {row["number"]: row for row in data["rows"]}
    assert rows[1]["formal_name"] == "Rashi"
    assert rows[9]["formal_name"] == "Navamsa"
    assert rows[10]["skill_invoked"] is True
    assert rows[60]["formal_name"] == "Shashtiamsa"
    assert rows[13]["formal_name_present"] is False
    assert rows[13]["local_basis"] == "generic_fallback_only_unvalidated"
    assert rows[13]["claim_status"] == "low_rigor_generic_only"
    assert "must not be advertised" in data["boundary"]


def test_registry_tracks_api_ui_skill_oracle_boundaries():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = {row["number"]: row for row in data["rows"]}
    assert rows[24]["api_entry"] is True
    assert rows[24]["ui_entry"] is True
    assert rows[27]["api_entry"] is True
    assert rows[27]["ui_entry"] is False
    assert rows[27]["external_oracle_status"] == "missing"
    assert data["summary"]["formal_name_count"] == 20
    assert data["summary"]["generic_only_count"] == 40


def test_evidence_index_registers_d1_d60_registry():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    packet = packets["d1_d60_varga_mapping_registry"]
    assert packet["path"] == "references/oracle/d1_d60_varga_mapping_registry_2026_07_19.json"
    assert packet["claim_status"] == "partial"
