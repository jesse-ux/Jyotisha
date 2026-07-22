import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "references/oracle/source_runtime_closure_queue_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"
KP_RAW = ROOT / "references/oracle/vedicastro_kp_house_cusp_raw_2026_07_21.json"
KP_ENV = ROOT / "references/oracle/vedicastro_kp_tmp_env_identity_2026_07_21.json"


def test_queue_prioritizes_jyotishganit_and_vedicastro_without_truth_upgrade():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in data["rows"]}

    assert data["scope"] == "source_runtime_closure_queue"
    assert data["claim_status"] == "open_queue"
    assert data["truth_matrix_allowed"] is False
    assert rows["jyotishganit_field_closure"]["current_status"] == "probe_runs_observation_only"
    assert rows["vedicastro_kp_house_cusp_closure"]["current_status"] == "raw_ready_observation_only"
    assert rows["vedicastro_kp_house_cusp_closure"]["latest_observed_raw_hash"] == "2e7a6b17eb2965a60846f625f6bd8bc03555216d6225983647bcbfa23d0e345b"
    assert rows["vedicastro_kp_house_cusp_closure"]["coverage"]["sub_sub_lord"] is True


def test_queue_marks_existing_assets_as_not_fully_invoked():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    not_closed = data["not_fully_closed_reference_layers"]

    assert "references/open_source_sources/jyotishganit" in not_closed
    assert "references/open_source_sources/VedicAstro" in not_closed
    assert "references/open_source_sources/rishi-ai-mcp" in not_closed
    assert "references/open_source_sources/vedic-astro-skills" in not_closed
    assert data["boundary"] == "queue_only_no_adapter_or_truth_upgrade"


def test_queue_is_registered_in_evidence_index():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    entry = next(
        row for row in index["packets"]
        if row["packet_id"] == "source_runtime_closure_queue_2026_07_21"
    )

    assert entry["domain"] == "source_runtime_closure"
    assert entry["claim_status"] == "open_queue"


def test_vedicastro_kp_raw_and_tmp_env_are_observation_only_packets():
    raw = json.loads(KP_RAW.read_text(encoding="utf-8"))
    env = json.loads(KP_ENV.read_text(encoding="utf-8"))

    assert raw["scope"] == "vedicastro_kp_house_cusp_probe"
    assert raw["status"] == "complete"
    assert raw["claim_status"] == "observation_only"
    assert raw["truth_matrix_allowed"] is False
    assert raw["raw_hash"] == "2e7a6b17eb2965a60846f625f6bd8bc03555216d6225983647bcbfa23d0e345b"
    assert raw["schema_fingerprint"]["house_count"] == 12
    assert "SubLord" in raw["schema_fingerprint"]["fields"]
    assert "SubSubLord" in raw["schema_fingerprint"]["fields"]
    assert env["claim_status"] == "runtime_dependency_ready"
    assert env["project_dependency_mutation_allowed"] is False
