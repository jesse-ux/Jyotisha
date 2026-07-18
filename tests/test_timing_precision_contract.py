from scripts.timing_precision_contract import build_timing_precision_contract
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_timing_contract_preserves_dates_but_caps_claim_status() -> None:
    contract = build_timing_precision_contract({
        "verified_window": "2026-08 to 2026-10",
        "candidate_windows": [{
            "start": "2026-08-12", "end": "2026-08-16", "rank": 1,
            "signals": ["Vimshottari", "Narayana", "D10", "transit"],
            "confidence_cap": "low",
        }],
        "exact_triggers": [{"at": "2026-08-14T09:30:00Z", "technique": "exact_transit"}],
    })

    assert contract["timing_precision"] == "candidate_day_window"
    assert contract["claim_status"] == "exploratory_unvalidated"
    assert contract["verified_window"] == "2026-08 to 2026-10"
    assert contract["candidate_windows"][0]["start"] == "2026-08-12"
    assert contract["exact_triggers"][0]["at"] == "2026-08-14T09:30:00Z"
    assert contract["promotion_gate"]["status"] == "blocked"


def test_empty_timing_contract_still_exposes_boundary() -> None:
    contract = build_timing_precision_contract()
    assert contract["timing_precision"] == "broad_window_only"
    assert contract["candidate_windows"] == []
    assert "不能作为确定事件承诺" in contract["boundary"]


def test_predict_cli_exposes_exploratory_timing_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/jyotish_engine.py", "predict", "--chart", '{"planets":{}}',
         "--lat", "0", "--lon", "0", "--tz", "0"],
        cwd=ROOT, text=True, capture_output=True, timeout=30, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    contract = json.loads(completed.stdout)["timing_precision_contract"]
    assert contract["claim_status"] == "exploratory_unvalidated"
    assert contract["promotion_gate"]["current_negative_controls_reusable_for_tuning"] is False


def test_consultation_api_attaches_same_contract() -> None:
    source = (ROOT / "scripts/jyotish_api_server.py").read_text(encoding="utf-8")
    assert source.count("result['timing_precision_contract'] = build_timing_precision_contract") == 2
