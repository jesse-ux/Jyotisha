import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/muhurta_factor_only_scoring_packet_2026_07_23.json"


def test_muhurta_factor_only_packet_generator_captures_ten_factors():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/muhurta_factor_only_scoring_packet.py"],
            cwd=ROOT,
            text=True,
        )
    )

    assert data["scope"] == "muhurta_factor_only_scoring_packet"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["production_tuning_allowed"] is False
    assert data["verified_muhurta_verdict"] is False
    assert data["final_muhurta_verdict_status"] == "blocked_until_oracle"
    assert data["observed_factor_keys"] == [
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
    ]


def test_muhurta_factor_only_packet_keeps_scorecard_low_confidence():
    data = json.loads(PACKET.read_text(encoding="utf-8"))

    assert len(data["raw_sha256"]) == 64
    assert data["factor_scorecard"]["claim_status"] == "factor_only_not_final_muhurta_verdict"
    assert data["factor_scorecard"]["score_cap"] == "low"
    assert "no final Muhurta verdict" in data["boundary"]
