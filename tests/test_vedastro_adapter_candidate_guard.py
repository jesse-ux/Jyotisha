from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backend_probe_tracks_vedastro_as_service_adapter_candidate() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/ephemeris_backend_probe.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    vedastro = report["candidate_backends"]["vedastro"]

    assert set(report["candidate_backends"]) == {
        "external_benchmark_benchmark",
        "swisseph_python",
        "vedastro",
        "xalen_ephemeris",
    }
    assert set(report["replacement_readiness"]) == {
        "benchmark_only",
        "primary",
        "service_adapter_candidate",
        "spike_only",
    }
    assert vedastro["available"] is True
    assert vedastro["replacement_readiness"] == "service_adapter_candidate"
    assert "service/API boundary" in vedastro["license_posture"]
    assert "adapter contract" in vedastro["next_step"]


def test_candidate_spike_keeps_vedastro_gated_until_parity_and_timeout_checks() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/ephemeris_candidate_adapter_spike.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    vedastro = report["candidate_backends"]["vedastro_service_adapter_candidate"]

    assert set(report["candidate_backends"]) == {
        "vedastro_service_adapter_candidate",
        "xalen_ephemeris_candidate",
    }
    assert vedastro["candidate_backend"] == "vedastro_service_adapter_candidate"
    assert vedastro["candidate_adapter_spike"] == "service_boundary_not_yet_executable"
    assert vedastro["runtime_setting_exposure"] == "blocked_until_parity_timeout_and_license_gates"
    assert "service boundary" in vedastro["license_gate"]
    assert "timeout" in vedastro["parity_gate_required"]
