import json
from copy import deepcopy
from pathlib import Path

from scripts.minute_rectification_development_validator import DEFAULT_MANIFEST, validate
from scripts.minute_rectification_development_eval import run


def test_public_development_case_is_valid_but_cannot_enter_holdout() -> None:
    report = validate()

    assert report["status"] == "ready_for_development"
    assert report["valid_development_cases"] == 3
    assert report["excluded_from_holdout"] is True
    assert report["may_open_release_gate"] is False


def test_development_case_must_be_permanently_excluded_from_holdout(tmp_path: Path) -> None:
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    changed = deepcopy(manifest)
    changed["cases"][0]["excluded_from_holdout"] = False
    path = tmp_path / "invalid-development.json"
    path.write_text(json.dumps(changed), encoding="utf-8")

    report = validate(path)

    assert report["status"] == "blocked"
    assert "case_not_excluded_from_holdout" in report["invalid_cases"][0]["errors"]


def test_v3_development_result_stays_shadow_only() -> None:
    report = run()

    assert report["case_count"] == 3
    assert report["summary"]["v3_shadow_only"] is True
    assert report["summary"]["v3_may_replace_production"] is False
    assert report["summary"]["decision"] == "reject_v3_production_promotion"
    assert report["summary"]["v4_shadow_only"] is True
    assert report["summary"]["v4_may_replace_production"] is False
    assert report["summary"]["v4_decision"] == "requires_independent_frozen_holdout"
    assert report["summary"]["v3_improved_case_count"] == 0
    assert report["summary"]["indistinguishable_adjacent_pair_ratio"] == 0.7
    assert report["summary"]["p6_fact_indistinguishable_adjacent_pair_ratio"] == 0.6333
    assert report["summary"]["p6_fact_difference_opportunity_count"] == 11
    assert report["summary"]["p6_question_ready_opportunity_count"] == 9
    assert report["summary"]["p6_fact_atoms_may_affect_score"] is False
    assert all(case["production_confirmation_allowed"] is False for case in report["cases"])
