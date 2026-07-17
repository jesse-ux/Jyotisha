from __future__ import annotations

import json

from scripts import collect_vedastro_official_parity_raw as collector


def test_collect_chart_core_writes_secret_free_hashed_packet(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VEDASTRO_API_ENDPOINT", "https://api.vedastro.org/api")
    monkeypatch.setenv("VEDASTRO_API_KEY", "must-not-leak")

    def fake_post(endpoint, request_item):
        if request_item["section"] == "shadbala_chesta":
            return {"Status": "Pass", "Payload": {"PlanetChestaBala": "12.5"}}, 1, []
        if request_item["section"] == "shadbala":
            return {"Status": "Pass", "Payload": {"AllPlanetStrength": "(400, Sun)"}}, 1, []
        if request_item["section"] == "ashtakavarga_sav":
            return {"Status": "Pass", "Payload": {"AshtakvargaLifeMap": {"TotalBindus": 337}}}, 1, []
        if request_item["section"] == "ashtakavarga_bav":
            return {"Status": "Pass", "Payload": {"BhinnashtakavargaChart": {"Sun": {"Rows": [1] * 12}}}}, 1, []
        if request_item["section"] == "ashtakavarga_sav_chart":
            return {"Status": "Pass", "Payload": {"SarvashtakavargaChart": {"Sarvashtakavarga": {"Rows": [28] * 12}}}}, 1, []
        planet = request_item["fanout_value"]
        return {
            "Status": "Pass",
            "Payload": {
                "AllPlanetData": {
                    "PlanetHoraD2Signs": {"Name": f"{planet}-D2"},
                    "PlanetChaturthamshaD4Sign": {"Name": f"{planet}-D4"},
                    "PlanetNavamshaD9Sign": {"Name": f"{planet}-D9"},
                    "PlanetDashamamshaD10Sign": {"Name": f"{planet}-D10"},
                }
            },
        }, 1, []

    monkeypatch.setattr(collector.adapter, "_post_official_snapshot_section", fake_post)
    output = tmp_path / "packet.json"
    report = collector.collect_chart_core(
        collector.adapter.PARITY_CASES["beijing_first_use_demo"],
        case_id="beijing_first_use_demo",
        planets=["Sun", "Moon"],
        output_path=output,
    )

    stored = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert stored["coverage"]["sections"] == [
        "D2", "D4", "D9", "D10", "shadbala_total", "shadbala_components", "ashtakavarga_bav", "ashtakavarga_sav"
    ]
    assert stored["fanout_statuses"] == {"Moon": "ok", "Sun": "ok"}
    assert stored["scalar_statuses"] == {
        "ashtakavarga_bav": "ok",
        "ashtakavarga_sav": "ok",
        "ashtakavarga_sav_chart": "ok",
        "shadbala": "ok",
    }
    assert stored["component_statuses"] == {"Moon.chesta": "ok", "Sun.chesta": "ok"}
    assert len(stored["response_hash"]) == 64
    assert "must-not-leak" not in output.read_text(encoding="utf-8")
