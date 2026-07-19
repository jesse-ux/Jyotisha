import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path("/tmp/vedicastro_sidereal_flatlib_probe.Nt8ANZ")
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_jyotishganit_shadbala_surface_artifact_has_six_strengths():
    data = json.loads((ROOT / "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["scope"] == "jyotishganit_shadbala_surface_probe"
    assert data["claim_status"] == "observation_only"
    assert data["raw_hash"]
    sun = data["raw"]["shadbala"]["Sun"]
    for key in ["Sthanabala", "Digbala", "Kaalabala", "Cheshtabala", "Naisargikabala", "Drikbala", "Shadbala"]:
        assert key in sun


def test_vedicastro_batch_cusp_probe_artifact_has_public_cases():
    data = json.loads((ROOT / "references/oracle/vedicastro_kp_cusp_batch_probe_2026_07_19.json").read_text(encoding="utf-8"))
    assert data["scope"] == "vedicastro_kp_cusp_batch_probe"
    assert data["claim_status"] == "observation_only"
    assert data["summary"]["case_count"] >= 3
    assert data["summary"]["complete_count"] >= 1
    for row in data["cases"]:
        if row["status"] == "complete":
            assert row["house_count"] == 12
            assert row["raw_hash"]


def test_vedicastro_batch_runtime_when_temp_env_exists():
    if not RUNTIME.exists():
        return
    env = {**os.environ, "PYTHONPATH": f"{RUNTIME}:{ROOT / 'references/open_source_sources/VedicAstro'}"}
    out = subprocess.check_output([sys.executable, "scripts/vedicastro_kp_cusp_batch_probe.py", "--limit", "1"], cwd=ROOT, text=True, env=env)
    data = json.loads(out)
    assert data["summary"]["case_count"] == 1
    assert data["claim_status"] == "observation_only"


def test_remaining_queues_are_not_truth_upgrades():
    for rel in [
        "references/oracle/d1_d60_public_source_candidate_queue_2026_07_19.json",
        "references/oracle/muhurta_oss_factor_scoring_queue_2026_07_19.json",
        "references/oracle/four_engine_comparison_queue_2026_07_19.json",
    ]:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        assert data["production_tuning_allowed"] is False
        assert data["truth_matrix_allowed"] is False


def test_evidence_index_registers_ordered_remaining_packets():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    for packet_id in [
        "jyotishganit_shadbala_surface_probe",
        "vedicastro_kp_cusp_batch_probe",
        "d1_d60_public_source_candidate_queue",
        "muhurta_oss_factor_scoring_queue",
        "four_engine_comparison_queue",
    ]:
        assert packet_id in packets
