from scripts.reference_transparency_contract import (
    build_reference_transparency_contract,
    select_similar_public_cases,
)
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _chart(ascendant: str, moon: str, domain_lord_sign: str) -> dict:
    return {
        "ascendant": {"sign": ascendant},
        "planets": {
            "Moon": {"sign": moon},
            "Saturn": {"sign": domain_lord_sign},
        },
        "houses": {"house_10": {"lord": "Saturn"}},
    }


def test_select_similar_cases_shares_only_high_similarity_same_domain() -> None:
    user_chart = _chart("Leo", "Pisces", "Libra")
    cases = [
        {
            "case_id": "matching_career_case",
            "subject": {"name": "Public Example"},
            "chart": _chart("Leo", "Pisces", "Libra"),
            "source": {"url": "https://example.com/birth", "source_grade": "primary"},
            "event_outcomes": [{
                "domain": "career", "event_type": "career_breakthrough", "event_date": "2007-01-09",
                "outcome": "Public career event", "source": {"url": "https://example.com/event", "source_grade": "primary"},
            }],
            "replay": {"outcome_replay_status": "replayed", "do_not_use_for_prediction": False},
        },
        {
            "case_id": "wrong_domain_case",
            "subject": {"name": "Different Example"},
            "chart": _chart("Aries", "Aries", "Aries"),
            "source": {"url": "https://example.com/birth-2", "source_grade": "primary"},
            "event_outcomes": [{
                "domain": "marriage", "event_type": "legal_marriage", "event_date": "2011-04-29",
                "outcome": "Public marriage event", "source": {"url": "https://example.com/event-2", "source_grade": "primary"},
            }],
            "replay": {"outcome_replay_status": "replayed", "do_not_use_for_prediction": False},
        },
    ]

    selected = select_similar_public_cases(user_chart, ["career"], cases=cases)

    assert selected["status"] == "high_similarity_public_references_available"
    assert [case["case_id"] for case in selected["cases"]] == ["matching_career_case"]
    assert selected["cases"][0]["similarity"]["score"] == 1.0
    assert selected["cases"][0]["event_source"]["url"] == "https://example.com/event"
    assert selected["does_not_predict_user_outcome"] is True


def test_reference_contract_preserves_dates_and_discloses_parallel_methods() -> None:
    contract = build_reference_transparency_contract(
        _chart("Leo", "Pisces", "Libra"),
        ["career"],
        timing={"candidate_windows": [{"start": "2026-08-12", "end": "2026-08-16"}]},
        cases=[],
    )

    assert contract["timing_display"]["exact_triggers"] == "display_as_technical_trigger_not_guarantee"
    assert contract["external_engine_observations"]["VedAstro hosted"]["deployment_identity"] == "not_publicly_proven"
    assert contract["method_variants"]["display"] == "show_parallel_methods_with_sources"
    assert contract["similar_public_cases"]["status"] == "no_high_similarity_public_reference"


def test_default_public_manifest_can_surface_a_matching_replayed_case() -> None:
    from scripts.domain_calculation_service import compute_chart

    jobs_chart = compute_chart({
        "year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15,
        "lat": 37.7833, "lon": -122.4167, "tz": -8.0,
        "ayanamsa": "lahiri", "node_mode": "mean",
    })

    selected = select_similar_public_cases(jobs_chart, ["career"])

    assert selected["status"] == "high_similarity_public_references_available"
    assert selected["cases"][0]["case_id"] == "jobs_iphone_2007"
    assert selected["cases"][0]["reference_only"] is True


def test_consultation_api_exposes_reference_transparency_contract() -> None:
    source = (ROOT / "scripts" / "jyotish_api_server.py").read_text(encoding="utf-8")
    assert "result['reference_transparency'] = build_reference_transparency_contract(" in source
