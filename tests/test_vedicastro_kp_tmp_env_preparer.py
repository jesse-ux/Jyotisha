import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_vedicastro_kp_tmp_env.py"


def test_preparer_supports_report_only_mode_without_project_install():
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), "--report-only"],
        cwd=ROOT,
        text=True,
    )
    data = json.loads(out)

    assert data["scope"] == "vedicastro_kp_tmp_env_preparer"
    assert data["target"] == "/tmp/vedicastro_flatlib_probe"
    assert data["project_dependency_mutation_allowed"] is False
    assert data["required_packages"]["flatlib"].startswith("git+https://github.com/diliprk/flatlib.git@sidereal")
    assert data["claim_status"] in {"blocked_runtime_dependency", "runtime_dependency_ready"}


def test_preparer_result_never_claims_oracle_truth():
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), "--report-only"],
        cwd=ROOT,
        text=True,
    )
    data = json.loads(out)

    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["boundary"] == "dependency_preparation_only_no_kp_oracle_truth"
