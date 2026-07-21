from __future__ import annotations

from scripts import vedastro_divisional_contract_probe as probe


def test_probe_marks_degree_mapping_only_when_official_values_match(monkeypatch) -> None:
    def fake_post(calculator, body, _timeout):
        division = body["divisionalNo"]
        return {
            "calculator": calculator,
            "status": "Pass",
            "payload": {
                "DivisionalLongitude": {"TotalDegrees": str(3.5 * division % 30)}
            },
        }

    monkeypatch.setattr(probe, "_post", fake_post)
    result = probe.probe(total_degrees=3.5, timeout=1)

    assert result["contract_status"] == "degree_mapping_verified"
    assert result["chart_sign_contract"] == "blocked"
    assert result["rows"]["D9"]["matches_local"] is True
