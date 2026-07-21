import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path("/tmp/vedicastro_sidereal_flatlib_probe.Nt8ANZ")
ARTIFACT = ROOT / "references/oracle/vedicastro_kp_house_cusp_probe_steve_jobs_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_vedicastro_kp_house_cusp_artifact_has_12_cusps_and_hash():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["scope"] == "vedicastro_kp_house_cusp_probe"
    assert data["claim_status"] == "observation_only"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert data["raw_hash"]
    assert data["schema_fingerprint"]["house_count"] == 12
    fields = set(data["schema_fingerprint"]["fields"])
    assert {"LonDecDeg", "NakshatraLord", "SubLord", "SubSubLord"} <= fields
    assert data["raw"]["houses"][0]["Object"] == "I"


def test_vedicastro_kp_house_cusp_probe_runtime_when_temp_env_exists():
    if not RUNTIME.exists():
        return
    env = {
        **os.environ,
        "PYTHONPATH": f"{RUNTIME}:{ROOT / 'references/open_source_sources/VedicAstro'}",
    }
    out = subprocess.check_output(
        [sys.executable, "scripts/vedicastro_kp_house_cusp_probe.py"],
        cwd=ROOT,
        text=True,
        env=env,
    )
    data = json.loads(out)
    assert data["schema_fingerprint"]["house_count"] == 12
    assert data["raw"]["houses"][0]["SubLord"]
    assert data["dependency_identity"]["observed_pinned_flatlib_commit"] == "2618c348ce1ab2588548f935ff65f031630b4872"


def test_evidence_index_registers_house_cusp_probe():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    assert packets["vedicastro_kp_house_cusp_probe"]["claim_status"] == "observation_only"
