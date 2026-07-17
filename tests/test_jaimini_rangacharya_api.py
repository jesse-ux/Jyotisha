import os
import sys


SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from jyotish_api_server import JyotishAPIHandler  # noqa: E402


def _handler() -> JyotishAPIHandler:
    return JyotishAPIHandler.__new__(JyotishAPIHandler)


def _planets():
    return {
        "Sun": {"lon": 10.0},
        "Moon": {"lon": 45.0},
        "Mars": {"lon": 80.0},
        "Mercury": {"lon": 110.0},
        "Jupiter": {"lon": 145.0},
        "Venus": {"lon": 200.0},
        "Saturn": {"lon": 250.0},
        "Rahu": {"lon": 300.0},
        "Ketu": {"lon": 120.0},
    }


def test_jaimini_default_does_not_include_rangacharya():
    result = _handler()._compute_jaimini({
        "mode": "arudha",
        "ascendant": {"lon": 0.0},
        "planets": _planets(),
    })
    assert "rangacharya" not in result["result"]
    assert "rangacharya_diff" not in result["result"]


def test_jaimini_variant_all_includes_current_variant_and_diff():
    result = _handler()._compute_jaimini({
        "mode": "arudha",
        "variant": "all",
        "ascendant": {"lon": 0.0},
        "planets": _planets(),
    })
    assert result["result"]["rangacharya"]["adjudication_enabled"] is False
    assert result["result"]["rangacharya_diff"]["adjudication_enabled"] is False
    assert result["result"]["rangacharya"]["arudha_padas"]["AL"]["source_card_status"] == "transcribed"
    assert result["result"]["rangacharya"]["active_lagna"]["source_card_id"] == "active_effective_lagna"
