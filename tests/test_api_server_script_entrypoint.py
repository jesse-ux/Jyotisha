"""Regression coverage for starting the API server as a script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_SERVER = ROOT / "scripts" / "jyotish_api_server.py"


def test_script_entrypoint_can_lazy_import_scripts_package_from_another_cwd() -> None:
    """The documented script command must retain repository-root package imports."""
    program = f"""
import runpy
import sys
from pathlib import Path

root = Path({str(ROOT)!r})
sys.path[:] = [entry for entry in sys.path if Path(entry or '.').resolve() != root]
namespace = runpy.run_path({str(API_SERVER)!r}, run_name='jyotish_api_server_script_entrypoint')
handler = namespace['JyotishAPIHandler'].__new__(namespace['JyotishAPIHandler'])
result = handler._compute_vedastro_gateway_archives()
assert isinstance(result, dict)
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr
