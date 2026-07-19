import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/shadbala_same_unit_normalizer_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_normalizer_outputs_42_same_unit_rows():
    data = json.loads(subprocess.check_output(["python3", "scripts/shadbala_same_unit_normalizer.py"], cwd=ROOT, text=True))
    assert data["scope"] == "shadbala_same_unit_normalizer"
    assert data["summary"]["row_count"] == 42
    assert data["claim_status"] == "partial"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["matrix_hash"]


def test_normalizer_artifact_has_virupa_and_rupa_fields():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    first = data["rows"][0]
    assert first["normalization_unit"] == "Virupa"
    assert "jyotishganit_virupa" in first
    assert "jyotishganit_rupa" in first
    assert "vp_jain_published_virupa" in first
    assert first["classification"] in {
        "within_1_virupa_observation",
        "method_variant",
        "formula_or_unit_mismatch",
        "insufficient_numeric_sources",
    }


def test_normalizer_classifies_all_rows_without_truth_upgrade():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    total = (
        data["summary"]["within_1_virupa_observation_count"]
        + data["summary"]["method_variant_count"]
        + data["summary"]["formula_or_unit_mismatch_count"]
        + data["summary"]["insufficient_numeric_sources_count"]
    )
    assert total == 42
    assert data["summary"]["formula_or_unit_mismatch_count"] >= 1
    assert "not absolute parity closure" in data["boundary"]


def test_evidence_index_registers_same_unit_normalizer():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["shadbala_same_unit_normalizer"]["claim_status"] == "partial"
