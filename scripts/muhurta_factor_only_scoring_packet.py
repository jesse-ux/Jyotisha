#!/usr/bin/env python3
"""Capture a Muhurta factor-only scoring observation packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from muhurta_factor_probe import build_probe


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "references/oracle/muhurta_factor_only_scoring_packet_2026_07_23.json"


def _stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def build() -> dict[str, Any]:
    raw = build_probe("2026-07-19", birth_moon_nakshatra_index=4, birth_moon_sign_index=1)
    factor_keys = [
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "yamaganda",
        "gulika_kalam",
        "abhijit_muhurta",
        "panchaka",
        "sankranti",
        "vyatipata",
        "vaidhriti",
    ]
    packet = {
        "scope": "muhurta_factor_only_scoring_packet",
        "created_at": "2026-07-23",
        "claim_status": "observation_only",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "verified_muhurta_verdict": False,
        "final_muhurta_verdict_status": "blocked_until_oracle",
        "observed_factor_keys": factor_keys,
        "canonical_request": {
            "date": "2026-07-19",
            "birth_moon_nakshatra_index": 4,
            "birth_moon_sign_index": 1,
        },
        "factor_scorecard": raw["factor_scorecard"],
        "factor_status": {
            key: (
                raw["factors"][key].get("status")
                if isinstance(raw["factors"].get(key), dict)
                else "present"
            )
            for key in factor_keys
        },
        "raw_sha256": hashlib.sha256(_stable_json(raw).encode("utf-8")).hexdigest(),
        "raw_observation": raw,
        "boundary": "Muhurta factor-only scoring is available for comparison; no final Muhurta verdict or electional promise is allowed until public worked examples close.",
    }
    return packet


def main() -> int:
    packet = build()
    OUTPUT.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
