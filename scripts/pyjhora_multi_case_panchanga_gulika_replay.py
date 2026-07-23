#!/usr/bin/env python3
"""Compare fixed public/synthetic PyJHora Panchanga and Gulika observations."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gulika import calculate_gulika
from muhurta import _swisseph_sun_moon_lon, calc_panchanga

CASES = (
    {"case_id": "synthetic_beijing_1990", "date": (1990, 1, 1), "time": (12, 0, 0), "place": ("Beijing", 39.9042, 116.4074, 8.0)},
    {"case_id": "public_smoke_chennai_1996", "date": (1996, 12, 7), "time": (10, 34, 0), "place": ("Chennai", 13.0878, 80.2785, 5.5)},
    {"case_id": "synthetic_london_2000", "date": (2000, 6, 21), "time": (6, 30, 0), "place": ("London", 51.5074, -0.1278, 1.0)},
)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def build_report() -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from jhora import utils
        from jhora.panchanga import drik
        drik.set_ayanamsa_mode("LAHIRI")
        rows = []
        try:
            for item in CASES:
                y, m, d = item["date"]
                hh, mm, ss = item["time"]
                name, lat, lon, tz = item["place"]
                dob, tob, place = drik.Date(y, m, d), (hh, mm, ss), drik.Place(name, lat, lon, tz)
                local_jd = utils.julian_day_number(dob, tob)
                raw = {
                    "gulika": drik.gulika_longitude(dob, tob, place),
                    "maandi": drik.maandi_longitude(dob, tob, place),
                    "tithi": drik.tithi(local_jd, place),
                    "nakshatra": drik.nakshatra(local_jd, place),
                    "yogam": drik.yogam(local_jd, place),
                    "karana": drik.karana(local_jd, place),
                    "raahu_kaalam": drik.raahu_kaalam(local_jd, place),
                    "yamaganda_kaalam": drik.yamaganda_kaalam(local_jd, place),
                    "durmuhurtam": drik.durmuhurtam(local_jd, place),
                    "abhijit_muhurta": drik.abhijit_muhurta(local_jd, place),
                }
                utc_jd = local_jd - tz / 24
                sun_moon = _swisseph_sun_moon_lon(utc_jd, "lahiri")
                local = calc_panchanga(*sun_moon, weekday=(datetime(y, m, d).weekday() + 1) % 7)
                local_gulika = calculate_gulika(datetime(y, m, d, hh, mm, ss), lat=lat, lon=lon, tz=tz)
                py_gulika_deg = raw["gulika"][0] * 30 + raw["gulika"][1]
                field_comparison = {
                    "tithi": {"local": local["tithi"]["tithi_num"], "pyjhora": raw["tithi"][0], "status": "match" if local["tithi"]["tithi_num"] == raw["tithi"][0] else "mismatch"},
                    "nakshatra": {"local": local["nakshatra"]["nakshatra_idx"] + 1, "pyjhora": raw["nakshatra"][0], "status": "match" if local["nakshatra"]["nakshatra_idx"] + 1 == raw["nakshatra"][0] else "mismatch"},
                    "yogam": {"local": local["yoga"]["yoga_idx"] + 1, "pyjhora": raw["yogam"][0], "status": "match" if local["yoga"]["yoga_idx"] + 1 == raw["yogam"][0] else "mismatch"},
                    "gulika": {"local_degrees": local_gulika["longitude"], "pyjhora_degrees": py_gulika_deg, "delta_degrees": abs(((local_gulika["longitude"] - py_gulika_deg + 180) % 360) - 180), "status": "observed_formula_comparison"},
                }
                rows.append({"case_id": item["case_id"], "input": {"date": f"{y:04d}-{m:02d}-{d:02d}", "time": f"{hh:02d}:{mm:02d}:{ss:02d}", "place": name, "latitude": lat, "longitude": lon, "timezone": f"{tz:+03.1f}", "ayanamsa": "Lahiri"}, "pyjhora_raw": raw, "field_comparison": field_comparison, "raw_sha256": _hash(raw)})
        finally:
            drik.reset_ayanamsa_mode()
    return {"scope": "pyjhora_multi_case_panchanga_gulika_replay", "claim_status": "observation_only", "consumer_policy": "research_observation_only", "production_tuning_allowed": False, "truth_matrix_allowed": False, "license_boundary": "agpl_observation_only_do_not_vendor", "cases": rows, "boundary": "Three fixed public/synthetic cases compare field observations only. Maandi and Muhurta windows remain raw observations; no automatic election, prediction, or truth upgrade is allowed."}


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, default=str))
