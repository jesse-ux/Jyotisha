from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "research" / "shadbala_av_normative_benchmark_plan_2026_07_19.md"


def test_shadbala_av_plan_keeps_current_closure_separate_from_global_truth() -> None:
    text = PLAN.read_text(encoding="utf-8")

    for token in [
        "current target set: `external_verified`",
        "`can_claim_shadbala_absolute_closure = true`",
        "`production_tuning_allowed = false`",
        "must not claim universal Shadbala or AV truth",
        "60 mismatches, 60 classified, 0 unclassified",
        "no majority vote",
    ]:
        assert token in text


def test_shadbala_av_plan_requires_component_units_and_license_boundaries() -> None:
    text = PLAN.read_text(encoding="utf-8")

    for token in [
        "VP Jain",
        "Xalen",
        "PyJHora/JHora",
        "jyotishganit",
        "Virupa vs Rupa must be explicit",
        "`sthana`",
        "`dig`",
        "`kala`",
        "`chesta`",
        "`naisargika`",
        "`drik`",
        "`total_rupa`",
        "AGPL implementation code",
        "Independent ephemeris mode",
    ]:
        assert token in text
