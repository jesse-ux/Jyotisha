from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "kp_precision_timing_probe.py"


def test_kp_precision_timing_probe_outputs_star_sub_lord_and_significators() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["scope"] == "kp_star_sub_lord_significator_probe"
    assert report["claim_status"] == "probe_only_not_timing_truth"
    assert report["production_tuning_allowed"] is False
    assert report["raw_sha256"]

    assert "Sun" in report["kp_lords_by_planet"]
    sun_lords = report["kp_lords_by_planet"]["Sun"]
    assert {"rasi_lord", "nakshatra_lord", "sub_lord", "sub_sub_lord"} <= set(sun_lords)

    assert "Sun" in report["planet_significators"]
    assert {"A", "B", "C", "D"} <= set(report["planet_significators"]["Sun"])
    assert "10" in report["house_significators"]
    assert {"A", "B", "C", "D"} <= set(report["house_significators"]["10"])
    assert {"weekday_lord", "moon_sign_lord", "moon_star_lord", "asc_sign_lord", "asc_star_lord", "asc_sub_lord"} <= set(report["ruling_planets"])


def test_kp_precision_timing_probe_preserves_oracle_and_holdout_blockers() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["external_oracle_status"] == "partial_sublord_csv_only"
    assert report["negative_holdout_status"] == "missing"
    assert "cannot drive precise event timing" in report["claim_boundary"]
