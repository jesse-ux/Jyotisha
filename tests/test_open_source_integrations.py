#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开源项目集成 smoke test

验证已从 MIT 开源项目适配进来的模块能在本 skill 中独立运行：
- dashaflow / jaimini-tropical: Jaimini Arudha A1-A12、Graha Pada、Special Lagnas
- jaimini-tropical: Argala + Virodhargala + Rajayoga classification
- dashaflow: Synastry additional kutas (Mahendra/StreeDeergha/Vedha/Rajju/BadConstellations)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

from jaimini import calc_arudha_padas, calc_graha_padas, calc_special_lagnas
from argala import calc_argala
from synastry import calc_synastry


def sample_planet_longitudes():
    return {
        "Sun": 3.5055,
        "Moon": 311.7759,
        "Mars": 91.3161,
        "Mercury": 338.5287,
        "Jupiter": 163.8233,
        "Venus": 340.5447,
        "Saturn": 304.2874,
        "Rahu": 231.0339,
        "Ketu": 51.0339,
    }


def test_jaimini_arudha_modules():
    asc_idx = 4  # Leo
    lons = sample_planet_longitudes()
    padas = calc_arudha_padas(asc_idx, lons)
    assert padas["method"].startswith("Arudha Pada")
    assert "A1" in padas["padas"]
    assert "UL" in padas["padas"]
    assert padas["padas"]["A10"]["name"] == "Karma Pada (A10)"

    graha = calc_graha_padas(lons)
    assert "Sun" in graha["graha_padas"]
    assert "graha_pada_sign" in graha["graha_padas"]["Sun"]

    special = calc_special_lagnas(asc_idx, 14, 45)
    assert special["capability_status"] == "auxiliary_partial"
    assert all(k in special for k in ("HL", "GL", "VL"))


def test_argala_enhanced_module():
    asc_idx = 4
    signs = {p: int(lon / 30) % 12 for p, lon in sample_planet_longitudes().items()}
    result = calc_argala(signs, asc_idx)
    assert result["version"] == "1.1"
    assert "house_1" in result["houses"]
    assert "rajayoga_classification" in result["houses"]["house_1"]
    assert "summary" in result


def test_synastry_dashaflow_additional_kutas():
    result = calc_synastry(
        {"moon_lon": 210.5, "mars_lon": 130.1, "asc_lon": 120.0, "gender": "M"},
        {"moon_lon": 45.2, "mars_lon": 15.0, "asc_lon": 60.0, "gender": "F"},
    )
    assert result["version"] == "3.8-dashaflow-mit-adapted"
    assert "additional_kutas" in result
    for key in ("Mahendra", "StreeDeergha", "Vedha", "Rajju", "BadConstellations"):
        assert key in result["additional_kutas"]


def main():
    test_jaimini_arudha_modules()
    test_argala_enhanced_module()
    test_synastry_dashaflow_additional_kutas()
    print(json.dumps({"status": "passed", "tests": 3}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
