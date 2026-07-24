from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _birth_case() -> dict[str, object]:
    return {
        "year": 1992,
        "month": 8,
        "day": 17,
        "hour": 14,
        "minute": 30,
        "lat": 23.1291,
        "lon": 113.2644,
        "tz": 8,
        "reference_date": "2026-07-14",
    }


def test_vedastro_child_process_defaults_to_active_interpreter(monkeypatch) -> None:
    from scripts import vedastro_service_adapter

    monkeypatch.delenv("VEDASTRO_PYTHON_BIN", raising=False)
    monkeypatch.delenv("PYTHON_BIN", raising=False)

    assert vedastro_service_adapter._vedastro_python_bin() == sys.executable


def test_fast_snapshot_executes_only_five_scalar_methods(monkeypatch) -> None:
    from scripts import vedastro_official_capability_runner as runner

    calls: list[str] = []

    def fake_call(method: str, _payload: dict[str, object]) -> dict[str, object]:
        calls.append(method)
        return {"available": True, "status": "ok", "result": {"method": method}}

    monkeypatch.setattr(runner, "SNAPSHOT_FANOUT_ENABLED", False)
    monkeypatch.setattr(runner, "_call_bridge", fake_call)

    result = runner.run_snapshot_bundle("official_full_snapshot", _birth_case())

    assert calls == [
        "DasaAtRange",
        "DasaAtTime",
        "GetCharaDasaAtTime",
        "AllPlanetStrength",
        "AshtakvargaLifeMap",
    ]
    assert result["available"] is True
    assert result["summary"]["requested_method_count"] == 5
    assert result["summary"]["fanout_enabled"] is False
    assert set(result["result"]["snapshot_sections"]) == {
        "dasha_all",
        "vimshottari_now",
        "chara_dasha_now",
        "shadbala",
        "ashtakavarga",
    }


def test_rectification_range_scan_cannot_be_disabled_separately_from_official_network(monkeypatch) -> None:
    from scripts import vedastro_service_adapter

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_RANGE_SCAN_NETWORK_ENABLED", "0")
    calls: list[dict[str, object]] = []

    def fake_post(_endpoint: str, request_preview: dict[str, object]):
        calls.append(request_preview)
        return {"Status": "Pass", "Payload": []}, 1, []

    monkeypatch.setattr(vedastro_service_adapter, "_post_json_with_retry", fake_post)

    result = vedastro_service_adapter.run_range_scan_for_case(
        _birth_case(),
        "career",
        "2026-07-14",
        "2026-07-14",
    )

    assert len(calls) == 1
    assert result["status"] == "ok"


def test_official_env_example_enables_official_gateway_and_range_scan() -> None:
    example = (ROOT / ".env.official.example").read_text(encoding="utf-8")

    assert "VEDASTRO_GATEWAY_MODE=official_first" in example
    assert "VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api" in example
    assert "VEDASTRO_ENABLE_NETWORK=1" in example
    assert "VEDASTRO_RANGE_SCAN_NETWORK_ENABLED=1" in example
