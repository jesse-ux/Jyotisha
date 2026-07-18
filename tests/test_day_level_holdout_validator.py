from pathlib import Path
import json
from scripts.day_level_holdout_validator import validate

ROOT=Path(__file__).resolve().parents[1]

def test_empty_preregistered_holdout_remains_honestly_blocked() -> None:
    report=validate(ROOT/"references/real_case_calibration/day_level_holdout_v3_preregistration.json")
    assert report["status"] == "awaiting_independent_labels"
    assert report["annotation_count"] == 0
    assert report["production_tuning_allowed"] is False


def test_raman_source_candidates_are_not_holdout_labels() -> None:
    payload = json.loads((ROOT / "references/real_case_calibration/raman_vol1_holdout_source_candidates_2026_07_18.json").read_text())
    assert payload["candidate_count"] >= 20
    assert all(row["status"] == "needs_independent_normalization" for row in payload["candidates"])
    assert all("day_level_label" in row["prohibited_uses"] for row in payload["candidates"])
