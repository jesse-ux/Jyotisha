from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "references" / "cross_project_contract" / "cross_repo_strategy_diff_audit_2026_07_19.json"


def test_strategy_diff_audit_blocks_blind_overwrite() -> None:
    data = json.loads(AUDIT.read_text(encoding="utf-8"))

    assert data["scope"] == "cross_repo_strategy_diff_audit"
    assert data["status"] == "do_not_blind_overwrite"
    assert data["summary"]["diff_count"] == 7


def test_strategy_diff_audit_tracks_vedastro_and_holdout_policy_diffs() -> None:
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    items = {item["path"]: item for item in data["items"]}

    assert "scripts/day_level_holdout_validator.py" in items
    assert "commercial_retains_observational_validation_mode_for_product_intake" in items[
        "scripts/day_level_holdout_validator.py"
    ]["notes"]
    assert "scripts/vedastro_identity_archive.py" in items
    assert "research_has_stricter_self_host_truth_upgrade_gate" in items[
        "scripts/vedastro_identity_archive.py"
    ]["notes"]
