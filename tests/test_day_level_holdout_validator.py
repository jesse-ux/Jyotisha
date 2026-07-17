from pathlib import Path
from scripts.day_level_holdout_validator import validate

ROOT=Path(__file__).resolve().parents[1]

def test_empty_preregistered_holdout_remains_honestly_blocked() -> None:
    report=validate(ROOT/"references/real_case_calibration/day_level_holdout_v3_preregistration.json")
    assert report["status"] == "awaiting_independent_labels"
    assert report["annotation_count"] == 0
    assert report["production_tuning_allowed"] is False
