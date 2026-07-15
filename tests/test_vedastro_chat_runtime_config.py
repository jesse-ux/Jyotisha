from __future__ import annotations

import sys


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


def test_disabled_range_scan_never_calls_network(monkeypatch) -> None:
    from scripts import vedastro_service_adapter

    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_ENABLE_NETWORK", "1")
    monkeypatch.setenv("VEDASTRO_RANGE_SCAN_NETWORK_ENABLED", "0")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("range scan network request should not run in chat mode")

    monkeypatch.setattr(vedastro_service_adapter, "_post_json_with_retry", fail_if_called)

    result = vedastro_service_adapter.run_range_scan_for_case(
        _birth_case(),
        "career",
        "2026-07-14",
        "2026-08-14",
    )

    assert result["status"] == "network_execution_disabled"
    assert "interactive chat path" in result["reason"]
