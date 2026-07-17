from __future__ import annotations

import sys
from datetime import datetime
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


def test_api_sade_sati_uses_domain_true_saturn_transit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )
    request = {**BIRTH, "node_mode": "true", "transit_date": "2026-07-11"}
    chart = calculation_service.compute_chart(request)
    expected = calculation_service.compute_sade_sati(
        moon_degree=chart["planets"]["Moon"]["lon"],
        asc_degree=chart["ascendant"]["lon"],
        reference_date="2026-07-11",
        tz=BIRTH["tz"],
        ayanamsa=BIRTH["ayanamsa"],
    )

    rest = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(request)

    assert rest["sade_sati"]["transit_saturn_lon"] == pytest.approx(
        expected["transit_saturn_lon"], abs=1e-8
    )
    assert rest["sade_sati"]["provenance"]["data_layer"] == "true_transit_positions"
    assert rest["sade_sati"]["calculation_contract"]["algorithm"] == "sade_sati_true_saturn_transit"


def test_api_dasha_boundary_comes_from_domain_service(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )
    request = {**BIRTH, "node_mode": "true", "transit_date": "2026-07-11"}
    chart = calculation_service.compute_chart(request)
    expected = calculation_service.compute_vimshottari_timeline(
        birth_dt=datetime(1990, 1, 1, 12, 0),
        moon_lon=chart["planets"]["Moon"]["lon"],
    )

    rest = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(request)

    assert rest["dasha"]["current_md"] == expected["birth_balance"]["lord"]
    assert rest["dasha"]["remaining_years"] == pytest.approx(
        expected["birth_balance"]["remaining_years"], abs=1e-8
    )
    assert rest["dasha"]["start_date"] == expected["periods"][0]["start"]
    assert rest["dasha"]["result_hash"] == expected["result_hash"]
