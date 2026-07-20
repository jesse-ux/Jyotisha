import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/prashna_sphuta_oss_case_probe_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_prashna_sphuta_oss_case_probe_runs_pyjhora_case_in_isolation():
    data = json.loads(subprocess.check_output(["python3", "scripts/prashna_sphuta_oss_case_probe.py", "--date", "2026-07-20"], cwd=ROOT, text=True))
    assert data["scope"] == "prashna_sphuta_oss_case_probe"
    assert data["claim_status"] == "tooling_observation_only"
    assert data["license_boundary"] == "agpl_observation_only_do_not_vendor"
    assert data["case"]["source"] == "jhora.tests.pvr_tests.sphuta_tests"
    assert {r["field"] for r in data["rows"]} >= {"tri_sphuta", "chatur_sphuta", "pancha_sphuta"}
    assert data["raw_hash"]


def test_prashna_sphuta_oss_case_probe_does_not_upgrade_oracle_truth():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["oracle_ready"] is False
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert all(row["status"] in {"observed", "runtime_error"} for row in data["rows"])


def test_prashna_sphuta_oss_case_probe_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["prashna_sphuta_oss_case_probe_2026_07_20"]["claim_status"] == "tooling_observation_only"
