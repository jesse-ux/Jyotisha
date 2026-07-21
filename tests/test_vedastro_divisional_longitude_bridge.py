from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import varga  # noqa: E402


def test_vedastro_bridge_divisional_longitudes_match_local_degree_mapping() -> None:
    for division in (2, 4, 9, 10):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "vedastro_python_bridge.py"),
                "--method",
                "DivisionalLongitude",
                "--params-json",
                json.dumps({"args": [3.5, division]}),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["status"] == "ok"
        assert float(payload["result"]["TotalDegrees"]) == varga.calc_varga(
            3.5, division
        )["degree_in_sign"]
