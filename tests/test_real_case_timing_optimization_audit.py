from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "research" / "real_case_timing_optimization_audit_2026_07_19.md"


def test_real_case_timing_audit_separates_positive_replay_from_specificity() -> None:
    text = DOC.read_text(encoding="utf-8")

    for token in [
        "Positive-event replay is healthy",
        "known positive events only",
        "does not verify day/month predictive specificity",
        "Day-level negative holdout remains empty",
        "status = awaiting_independent_labels",
        "day_level_holdout_v3_pilot_source_queue_2026_07_19.json",
        "not a holdout manifest",
        "production_tuning_allowed = false",
        "claim_status = exploratory_unvalidated",
        "Forbidden UX: packaging candidate dates as verified event promises",
    ]:
        assert token in text
