from __future__ import annotations

import json
from pathlib import Path

from scripts.public_real_case_benchmark import (
    _engine_json,
    ashtakavarga_audit,
    clear_engine_cache,
    combine_reports,
    compare_reports,
    node_dispositor_bonus,
    promotion_decision,
    score_active_dasha_lords,
    summarize_results,
    varga_and_karaka_bonus,
)


ROOT = Path(__file__).resolve().parents[1]


def test_summary_reports_positive_recall_without_inventing_specificity() -> None:
    summary = summarize_results(
        [
            {"result_class": "strong_hit", "matched_expected_label": True, "blocked": False},
            {"result_class": "weak_hit", "matched_expected_label": False, "blocked": False},
            {"result_class": "miss", "matched_expected_label": False, "blocked": False},
            {"result_class": "blocked", "matched_expected_label": False, "blocked": True},
        ]
    )
    assert summary["positive_event_recall"] == 2 / 3
    assert summary["exact_label_rate"] == 1 / 3
    assert summary["blocked_rate"] == 1 / 4
    assert summary["balanced_accuracy"] is None
    assert summary["balanced_accuracy_blocked_reason"] == "no_verified_negative_control_dates"
    assert summary["known_event_activation_rate"] == 2 / 3
    assert summary["strong_activation_rate"] == 1 / 3
    assert summary["positive_event_recall_deprecated"] is True
    assert summary["exact_label_rate_deprecated"] is True


def test_v21_deduplicates_same_md_ad_lord() -> None:
    chart = {"planets": {"Jupiter": {"house": 10}}}
    roles = {"owned_houses": {"Jupiter": [9, 11]}}

    score, signals = score_active_dasha_lords(
        ["Jupiter", "Jupiter"], {6, 9, 10, 11}, chart, roles, {"Sun", "Saturn", "Mercury"}
    )

    assert score == 3
    assert signals.count("Jupiter_owns_event_houses:[9, 11]") == 1
    assert signals.count("Jupiter_occupies_event_house:10") == 1


def test_ashtakavarga_audit_reports_event_houses_and_transit_bav_without_scoring() -> None:
    audit = ashtakavarga_audit(
        "marriage",
        {
            "method": "Ashtakavarga",
            "version": "2.1",
            "sav": {"total": 337, "valid": True, "scores": {"Libra": 30, "Sagittarius": 27}},
            "all_bav_valid": True,
            "house_scores": {
                "house_2": {"sign": "Leo", "sav_score": 24},
                "house_5": {"sign": "Scorpio", "sav_score": 29},
                "house_7": {"sign": "Capricorn", "sav_score": 31},
                "house_11": {"sign": "Taurus", "sav_score": 32},
            },
            "bav": {
                "Jupiter": {"bindus": [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0], "total": 56, "valid": True},
                "Saturn": {"bindus": [0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0], "total": 39, "valid": True},
            },
        },
        {
            "ayanamsa": 24.1,
            "node_mode": "mean",
            "planets": {"Jupiter": {"sign": "Libra"}, "Saturn": {"sign": "Sagittarius"}},
        },
    )

    assert audit["status"] == "used_non_scoring"
    assert audit["sav_total"] == 337
    assert audit["event_house_sav"]["7"]["sav_score"] == 31
    assert audit["transit_support"]["Jupiter"] == {"sign": "Libra", "sav": 30, "bav": 5}
    assert audit["transit_support"]["Saturn"] == {"sign": "Sagittarius", "sav": 27, "bav": 4}


def test_engine_json_cache_reuses_identical_subject_command(monkeypatch) -> None:
    calls = []

    class Completed:
        stdout = '{"ok": true}'

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return Completed()

    clear_engine_cache()
    monkeypatch.setattr("scripts.public_real_case_benchmark.subprocess.run", fake_run)
    subject = {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 0, "lat": 0, "lon": 0, "tz": 0}

    assert _engine_json("chart", subject) == {"ok": True}
    assert _engine_json("chart", subject) == {"ok": True}
    assert len(calls) == 1
    clear_engine_cache()


def test_committed_report_matches_the_ten_case_manifest() -> None:
    manifest = json.loads((ROOT / "references/real_case_calibration/replay_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "docs/benchmark/public_real_case_benchmark_2026_07_11.json").read_text(encoding="utf-8"))
    assert {case["case_id"] for case in manifest["cases"]} == {case["case_id"] for case in report["cases"]}
    assert report["summary"]["total_events"] == 10
    assert report["summary"]["positive_event_recall"] == 0.8
    assert report["summary"]["balanced_accuracy"] is None


def test_v2_node_dispositor_adds_general_event_house_support() -> None:
    chart = {
        "planets": {
            "Rahu": {"sign": "Taurus", "house": 3},
            "Venus": {"sign": "Capricorn", "house": 10},
        }
    }
    roles = {"owned_houses": {"Venus": [3, 10]}}
    score, signals = node_dispositor_bonus({"Rahu"}, "career", chart, roles)
    assert score == 2
    assert "Rahu_dispositor_Venus_owns_event_house" in signals
    assert "Rahu_dispositor_Venus_occupies_event_house:10" in signals


def test_v2_varga_and_chara_karaka_support_is_domain_specific() -> None:
    varga = {
        "divisional_charts": {
            "D10_Dasamsa": {
                "ascendant": "Taurus",
                "Saturn": {"sign": "Aquarius"},
            }
        }
    }
    jaimini = {
        "chara_karaka_7": {
            "karaka_table": {"Amatyakaraka": {"planet": "Saturn"}}
        }
    }
    score, signals = varga_and_karaka_bonus({"Saturn"}, "career", varga, jaimini)
    assert score == 3
    assert "active_dasha_matches_D10_10L:Saturn" in signals
    assert "active_dasha_occupies_D10_house_10:Saturn" in signals
    assert "active_dasha_matches_Amatyakaraka:Saturn" in signals


def test_v2_promotion_requires_holdout_improvement_without_more_blocking() -> None:
    promoted = promotion_decision(
        {"positive_event_recall": 0.6, "exact_label_rate": 0.2, "blocked_events": 0},
        {"positive_event_recall": 0.8, "exact_label_rate": 0.4, "blocked_events": 0},
    )
    assert promoted["promote"] is True
    blocked = promotion_decision(
        {"positive_event_recall": 0.6, "exact_label_rate": 0.2, "blocked_events": 0},
        {"positive_event_recall": 0.8, "exact_label_rate": 0.4, "blocked_events": 1},
    )
    assert blocked["promote"] is False
    assert blocked["reason"] == "v2_increased_blocked_events"


def test_compare_reports_keeps_case_level_deltas_auditable() -> None:
    v1 = {
        "rule_version": "v1",
        "summary": {"positive_event_recall": 0.5, "exact_label_rate": 0.0, "blocked_events": 0},
        "cases": [{"case_id": "case-a", "score": 3, "result_class": "miss", "signals": ["base"]}],
    }
    v2 = {
        "rule_version": "v2",
        "summary": {"positive_event_recall": 1.0, "exact_label_rate": 1.0, "blocked_events": 0},
        "cases": [{"case_id": "case-a", "score": 7, "result_class": "strong_hit", "signals": ["base", "new"]}],
    }

    comparison = compare_reports(v1, v2)

    assert comparison["promotion"]["promote"] is True
    assert comparison["case_deltas"] == [
        {
            "case_id": "case-a",
            "v1_score": 3,
            "v2_score": 7,
            "score_delta": 4,
            "v1_result_class": "miss",
            "v2_result_class": "strong_hit",
            "added_signals": ["new"],
        }
    ]


def test_combine_reports_recomputes_twenty_case_summary() -> None:
    batch1 = {"cases": [{"case_id": "a", "result_class": "strong_hit", "matched_expected_label": True, "blocked": False}]}
    holdout = {"cases": [{"case_id": "b", "result_class": "miss", "matched_expected_label": False, "blocked": False}]}

    combined = combine_reports([batch1, holdout], {"promote": True, "reason": "holdout_metrics_improved"})

    assert combined["summary"]["total_events"] == 2
    assert combined["summary"]["positive_event_recall"] == 0.5
    assert combined["holdout_promotion"]["promote"] is True
    assert [row["case_id"] for row in combined["cases"]] == ["a", "b"]
