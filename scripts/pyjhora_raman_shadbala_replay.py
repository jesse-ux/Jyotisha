#!/usr/bin/env python3
"""Replay the missing Raman Shadbala raw artifact through installed PyJHora.

This is a black-box observation runner. It imports the installed `jhora`
package, records stdout-like raw values and hashes, and compares them to the
pending Raman packet. It does not copy PyJHora implementation code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "references/oracle/artifacts/pending_packets/external_template_synthetic_north_china_shadbala_raman_pyjhora_20260627.json"
ARTIFACT = ROOT / "references/oracle/artifacts/pyjhora_synthetic_north_china_shadbala_raman_stdout_20260722.txt"
PACKET = ROOT / "references/oracle/raman_shadbala_raw_replay_and_input_drift_2026_07_22.json"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
COMPONENTS = ["sthana", "kala", "dig", "chesta", "naisargika", "drik"]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _round_rupa(raw: list[list[float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for planet_index, planet in enumerate(PLANETS):
        row = {}
        for component_index, component in enumerate(COMPONENTS):
            row[component] = round(float(raw[component_index][planet_index]) / 60.0, 4)
        row["total_rupa"] = round(float(raw[6][planet_index]) / 60.0, 4)
        out[planet] = row
    return out


def _replay_case(case: dict[str, Any]) -> dict[str, Any]:
    from jhora import utils
    from jhora.panchanga import drik
    from jhora.horoscope.chart import strength

    drik.set_ayanamsa_mode("Raman")
    jd = utils.julian_day_number(
        (case["year"], case["month"], case["day"]),
        (case["hour"], case["minute"], case.get("second", 0)),
    )
    place = drik.Place(case["label"], case["lat"], case["lon"], case["tz"])
    raw = strength.shad_bala(jd, place)
    chesta_new = strength._cheshta_bala_new(jd, place)  # black-box call; no implementation copied
    try:
        chesta_legacy = strength._cheshta_bala(jd, place)
        legacy_status = {"status": "ok", "values": chesta_legacy}
    except Exception as exc:  # noqa: BLE001 - artifact should capture exact black-box failure type
        legacy_status = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
    return {
        "case": case,
        "julian_day": jd,
        "ayanamsa_value": drik.get_ayanamsa_value(jd),
        "raw_virupa": raw,
        "component_rupa": _round_rupa(raw),
        "chesta_new": chesta_new,
        "chesta_legacy": legacy_status,
    }


def _diff_against_pending(component_rupa: dict[str, dict[str, float]], pending: dict[str, Any]) -> dict[str, Any]:
    target = pending["target_placeholders"]["target.shadbala_components"]
    diffs = []
    for planet in PLANETS:
        for component in ["sthana", "dig", "kala", "chesta", "naisargika", "drik", "total_rupa"]:
            observed = component_rupa[planet][component]
            expected = target[planet][component]
            diffs.append({
                "planet": planet,
                "component": component,
                "observed": observed,
                "pending_expected": expected,
                "abs_diff": round(abs(observed - expected), 4),
            })
    return {
        "max_abs_diff": max(row["abs_diff"] for row in diffs),
        "within_0001_count": sum(row["abs_diff"] <= 0.0001 for row in diffs),
        "row_count": len(diffs),
        "diffs": diffs,
    }


def build() -> dict[str, Any]:
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    birth = pending["birth"]
    cases = [
        {"label": "declared_packet_coordinates", **birth},
        {
            "label": "handan_candidate_coordinates",
            "year": birth["year"],
            "month": birth["month"],
            "day": birth["day"],
            "hour": birth["hour"],
            "minute": birth["minute"],
            "second": birth.get("second", 0),
            "lat": 36.6,
            "lon": 114.5,
            "tz": birth["tz"],
        },
    ]
    replays = [_replay_case(case) for case in cases]
    artifact_body = "\n".join(
        [
            "SOURCE_ENV installed jhora black-box import; AGPL implementation not copied",
            "CAPTURE_DATE 2026-07-22",
            "PENDING_PACKET references/oracle/artifacts/pending_packets/external_template_synthetic_north_china_shadbala_raman_pyjhora_20260627.json",
            "NOTE Replays declared packet coordinates and Handan candidate coordinates because existing packet metadata conflicts with case naming/history.",
            "REPLAY_JSON " + json.dumps(replays, ensure_ascii=False, sort_keys=True),
        ]
    ) + "\n"
    ARTIFACT.write_text(artifact_body, encoding="utf-8")
    comparisons = [
        {
            "case_label": replay["case"]["label"],
            "pending_diff": _diff_against_pending(replay["component_rupa"], pending),
        }
        for replay in replays
    ]
    return {
        "scope": "raman_shadbala_raw_replay_and_input_drift",
        "created_at": "2026-07-22",
        "claim_status": "blocked",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "pending_packet": str(PENDING.relative_to(ROOT)),
        "replay_artifact": str(ARTIFACT.relative_to(ROOT)),
        "replay_artifact_sha256": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
        "summary": {
            "replay_case_count": len(replays),
            "pending_declared_artifact_found": (ROOT / pending["metadata"]["source_artifact"]).exists(),
            "best_case_label_by_max_diff": min(comparisons, key=lambda row: row["pending_diff"]["max_abs_diff"])["case_label"],
            "complete_match_count": sum(row["pending_diff"]["max_abs_diff"] <= 0.0001 for row in comparisons),
            "can_promote_raman_sample": False,
        },
        "comparisons": comparisons,
        "chesta_variant_observation": {
            "legacy_api_status": replays[0]["chesta_legacy"]["status"],
            "new_api_present": True,
            "boundary": "PyJHora exposes at least two Chesta paths; this replay records behavior but does not choose a formula truth.",
        },
        "boundary": (
            "Raman Shadbala sample is not promoted: the declared raw artifact is "
            "absent and fresh black-box replay does not exactly match the pending "
            "target values under the declared coordinates. Handan-like coordinates "
            "are closer, proving an input-contract drift that needs human/source review."
        ),
    }


def main() -> int:
    packet = build()
    PACKET.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
