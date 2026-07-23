from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts/muhurta_factor_probe.py"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_muhurta_factor_probe_outputs_observation_not_verdict() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROBE), "--date", "2026-07-19", "--birth-moon-nakshatra-index", "4"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["scope"] == "muhurta_factor_probe"
    assert report["claim_status"] == "exploratory_muhurta_candidate"
    assert report["verified_muhurta_verdict"] is False
    assert report["production_tuning_allowed"] is False
    factors = report["factors"]
    assert {"tarabala", "chandrabala", "rahu_kalam", "abhijit_muhurta"} <= set(factors)
    assert report["candidate_windows"]
    assert report["candidate_windows"][0]["confidence_cap"] == "low"


def test_muhurta_factor_probe_outputs_full_factor_only_scoring_set() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(PROBE),
            "--date",
            "2026-07-19",
            "--birth-moon-nakshatra-index",
            "4",
            "--birth-moon-sign-index",
            "1",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)

    assert report["verified_muhurta_verdict"] is False
    assert report["full_scoring_status"] == "factor_only_scoring_observation"
    required = {
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "yamaganda",
        "gulika_kalam",
        "abhijit_muhurta",
        "panchaka",
        "sankranti",
        "vyatipata",
        "vaidhriti",
    }
    assert required <= set(report["factors"])
    assert report["factor_scorecard"]["claim_status"] == "factor_only_not_final_muhurta_verdict"
    assert report["factor_scorecard"]["score_cap"] == "low"


def test_muhurta_factor_probe_keeps_full_scoring_blocked() -> None:
    completed = subprocess.run(
        [sys.executable, str(PROBE), "--date", "2026-07-19"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["full_scoring_status"] == "factor_only_scoring_observation"
    assert report["final_muhurta_verdict_status"] == "blocked_until_oracle"
    assert "不能作为确定择日承诺" in report["boundary"]


def test_muhurta_factor_probe_is_indexed() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {packet["packet_id"]: packet for packet in data["packets"]}
    assert packets["muhurta_factor_probe"]["path"] == "scripts/muhurta_factor_probe.py"
    assert packets["muhurta_factor_probe"]["claim_status"] == "partial"
