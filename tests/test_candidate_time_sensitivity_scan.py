from scripts import candidate_time_sensitivity_scan as scanner


def test_scanner_reports_real_divisional_transitions(monkeypatch):
    def fake_engine(command, payload, timeout=20):
        minute = payload["minute"]
        if command == "chart":
            return {"ascendant": {"sign": "Leo", "degree_in_sign": 10 + minute / 100}}
        ascendant = "Aries" if minute % 2 else "Taurus"
        return {
            "D4_Turyamsa": {"Ascendant": {"sign": ascendant}},
            "D9_Navamsa": {"Ascendant": {"sign": ascendant}},
            "D10_Dasamsa": {"Ascendant": {"sign": ascendant}},
            "D24_Siddhamsa": {"Ascendant": {"sign": ascendant}},
            "D30_Trimsamsa": {"Ascendant": {"sign": ascendant}},
        }

    monkeypatch.setattr(scanner, "_engine_json", fake_engine)
    report = scanner.scan_candidate_times(
        {"year": 2000, "month": 1, "day": 1, "hour": 12, "minute": 1, "lat": 1, "lon": 1, "tz": 0},
        uncertainty_minutes=1,
    )

    assert report["candidate_count"] == 3
    assert report["transitions"]
    assert report["pending_layers"] == ["UL", "A7", "A10", "KP_cusp"]
    assert report["rows"][0]["divisional_ascendants"]["D9"] in {"Aries", "Taurus"}
    assert report["input_contract"]["settings"]["node_mode"] == "mean"
    assert report["rows"][0]["input_fingerprint"] != report["rows"][1]["input_fingerprint"]
    assert report["stability_contract"]["minute_confirmation_allowed"] is False
