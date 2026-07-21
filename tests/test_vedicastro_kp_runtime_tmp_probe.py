import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_DEPS = Path("/tmp/vedicastro_flatlib_probe")


def test_vedicastro_probe_reports_dependency_chain_without_truth_upgrade():
    env = {"PYTHONPATH": f"{TMP_DEPS}:{ROOT / 'references/open_source_sources/VedicAstro'}"}
    out = subprocess.check_output(
        [sys.executable, "scripts/vedicastro_kp_api_probe.py"],
        cwd=ROOT,
        text=True,
        env={**__import__("os").environ, **env},
    )
    data = json.loads(out)
    assert data["scope"] == "vedicastro_kp_api_probe"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["dependency_identity"]["required_flatlib_source"] == "git+https://github.com/diliprk/flatlib.git@sidereal"
    assert data["runtime_probe"]["attempted"] is True
    if data["runtime_probe"].get("import_status") == "success":
        assert data["runtime_probe"]["method_present"] is True
        assert "SubLord" in data["runtime_probe"]["sample_rl_nl_sl"]
        assert "AY_KRISHNAMURTI" in data["runtime_probe"]["sidereal_ayanamsa_constants_present"]
        assert data["dependency_identity"]["observed_pinned_flatlib_commit"] == "2618c348ce1ab2588548f935ff65f031630b4872"
    else:
        assert data["status"] == "blocked_runtime_import"
