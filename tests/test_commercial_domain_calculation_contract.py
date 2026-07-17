from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


BIRTH = {
    "year": 1990,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "second": 0,
    "lat": 28.6139,
    "lon": 77.2090,
    "tz": 5.5,
    "ayanamsa": "lahiri",
    "node_mode": "true",
}


def test_domain_chart_exposes_effective_parameters_and_result_hash() -> None:
    from domain_calculation_service import compute_chart

    result = compute_chart(BIRTH)

    assert result["calculation_contract"]["effective"]["node_mode"] == "true"
    assert result["calculation_contract"]["effective"]["ayanamsa"] == "lahiri"
    assert result["result_hash"]


def test_api_chart_uses_same_domain_contract_and_preserves_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import domain_calculation_service
    import jyotish_api_server
    from jyotish_api_server import JyotishAPIHandler

    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )

    expected = domain_calculation_service.compute_chart(BIRTH)
    result = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(
        {**BIRTH, "transit_date": "2026-07-11"}
    )

    assert result["result_hash"] == expected["result_hash"]
    assert result["calculation_contract"] == expected["calculation_contract"]
    assert result["birth"]["node_mode"] == "true"
    assert result["planets"]
    assert result["ascendant"]
    assert "houses" in result
