from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import domain_calculation_service as calculation_service  # noqa: E402
import jyotish_api_server  # noqa: E402
from jyotish_api_server import JyotishAPIHandler  # noqa: E402


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
}


def test_domain_chart_exposes_effective_params_and_result_hash() -> None:
    mean = calculation_service.compute_chart({**BIRTH, "node_mode": "mean"})
    true = calculation_service.compute_chart({**BIRTH, "node_mode": "true"})

    assert mean["calculation_contract"]["effective"]["ayanamsa"] == "lahiri"
    assert true["calculation_contract"]["effective"]["node_mode"] == "true"
    assert mean["planets"]["Rahu"]["lon"] != pytest.approx(true["planets"]["Rahu"]["lon"], abs=1e-8)
    assert mean["result_hash"] != true["result_hash"]


def test_api_chart_response_uses_domain_contract_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )
    expected = calculation_service.compute_chart({**BIRTH, "node_mode": "true"})

    rest = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(
        {**BIRTH, "node_mode": "true", "transit_date": "2026-07-11"}
    )

    assert rest["result_hash"] == expected["result_hash"]
    assert rest["birth"]["node_mode"] == "true"
    assert rest["calculation_contract"]["effective"]["node_mode"] == "true"


def test_api_visible_chart_values_come_from_domain_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )
    request = {**BIRTH, "node_mode": "true", "transit_date": "2026-07-11"}
    expected = calculation_service.compute_chart(request)

    rest = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(request)

    assert rest["ascendant"]["lon"] == pytest.approx(expected["ascendant"]["lon"], abs=1e-8)
    for planet in ("Sun", "Moon", "Rahu", "Ketu"):
        assert rest["planets"][planet]["sign"] == expected["planets"][planet]["sign"]
        assert rest["planets"][planet]["lon"] == pytest.approx(
            expected["planets"][planet]["lon"], abs=1e-8
        )
