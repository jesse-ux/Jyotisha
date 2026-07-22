from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import domain_calculation_service as calculation_service  # noqa: E402
import jyotish_api_server  # noqa: E402
from jyotish_api_server import JyotishAPIHandler  # noqa: E402
from jyotish_engine import _compute_chart_from_args  # noqa: E402

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


def test_true_node_changes_effective_rahu_and_contract() -> None:
    mean = calculation_service.compute_chart({**BIRTH, "node_mode": "mean"})
    true = calculation_service.compute_chart({**BIRTH, "node_mode": "true"})

    assert mean["planets"]["Rahu"]["lon"] != pytest.approx(
        true["planets"]["Rahu"]["lon"], abs=1e-8
    )
    assert mean["calculation_contract"]["effective"]["node_mode"] == "mean"
    assert true["calculation_contract"]["effective"]["node_mode"] == "true"
    assert mean["result_hash"] != true["result_hash"]


def test_vimshottari_uses_birth_balance_as_canonical_timeline() -> None:
    birth_dt = datetime(1990, 1, 1, 12, 0)
    result = calculation_service.compute_vimshottari_timeline(
        birth_dt=birth_dt,
        moon_lon=100.0,
        current_date=birth_dt,
    )

    first = result["periods"][0]
    assert first["lord"] == "Saturn"
    assert first["start"] == "1980-07-02"
    assert first["end"] == "1999-07-02"
    assert result["birth_balance"]["remaining_years"] == pytest.approx(9.5)
    assert result["calculation_contract"]["algorithm"] == "vimshottari_birth_balance"


def test_sade_sati_uses_real_saturn_transit_for_reference_date() -> None:
    result = calculation_service.compute_sade_sati(
        moon_degree=300.0,
        asc_degree=330.0,
        reference_date="2026-07-11",
        tz=5.5,
        ayanamsa="lahiri",
    )
    oracle = calculation_service.compute_transit_longitude(
        planet="Saturn",
        reference_date="2026-07-11",
        tz=5.5,
        ayanamsa="lahiri",
    )

    assert result["transit_saturn_lon"] == pytest.approx(oracle["longitude"], abs=1e-8)
    assert result["provenance"]["data_layer"] == "true_transit_positions"
    assert result["provenance"]["reference_date"] == "2026-07-11"


def test_jupiter_transit_uses_the_canonical_transit_contract() -> None:
    result = calculation_service.compute_transit_longitude(
        planet="Jupiter",
        reference_date="2026-07-11",
        tz=5.5,
        ayanamsa="lahiri",
    )

    assert result["planet"] == "Jupiter"
    assert 0 <= result["longitude"] < 360
    assert result["data_layer"] == "true_transit_positions"
    assert result["ayanamsa"] == "lahiri"


def test_timezone_inference_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        calculation_service,
        "_lookup_timezone_name",
        lambda _lat, _lon: None,
    )

    with pytest.raises(calculation_service.TimezoneInferenceError, match="timezone inference"):
        calculation_service.infer_timezone_offset(
            lat=0.0,
            lon=0.0,
            local_datetime=datetime(1990, 1, 1, 12, 0),
        )


def test_chart_hash_matches_domain_cli_and_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JYOTISH_API_CHART_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "0")
    monkeypatch.setattr(
        jyotish_api_server,
        "_attach_vedastro_main_entry_overview",
        lambda result, _birth: result,
    )
    expected = calculation_service.compute_chart({**BIRTH, "node_mode": "true"})
    cli, _asc_idx, _jd, _ayanamsa = _compute_chart_from_args(
        SimpleNamespace(**BIRTH, node_mode="true")
    )
    rest = JyotishAPIHandler.__new__(JyotishAPIHandler)._compute_chart_sync(
        {**BIRTH, "node_mode": "true", "transit_date": "2026-07-11"}
    )

    assert cli["result_hash"] == expected["result_hash"]
    assert rest["result_hash"] == expected["result_hash"]
    assert rest["birth"]["node_mode"] == "true"
    assert rest["calculation_contract"]["effective"]["node_mode"] == "true"
