#!/usr/bin/env python3
"""Read-only spike status for future ephemeris candidate adapters.

The script does not load alternate calculation engines. It records whether a
candidate_backend is executable enough to enter the parity gate defined by
scripts/ephemeris_adapter_contract.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]


def _exists(*parts: str) -> bool:
    return ROOT.joinpath(*parts).exists()


def build_spike() -> Dict[str, Any]:
    xalen_local_paths = [
        "references/open_source_sources/xalen-ephemeris",
        "references/open_source_sources/xalen",
    ]
    xalen_ephemeris_candidate = {
        "candidate_backend": "xalen_ephemeris_candidate",
        "candidate_adapter_spike": "documented_no_local_executable",
        "available": any(_exists(*path.split("/")) for path in xalen_local_paths),
        "evidence": [path for path in xalen_local_paths if _exists(*path.split("/"))] or ["no local xalen mirror detected"],
        "license_gate": "Apache-2.0 candidate from vedika-io/xalen-ephemeris; fetch/build/review before any adapter code is added.",
        "runtime_setting_exposure": "blocked_until_parity_gate_required",
        "parity_gate_required": "Must produce Sun/Moon/Asc/Rahu/Ketu rows compatible with EphemerisAdapterContract.",
    }

    vedastro_service_adapter_candidate = {
        "candidate_backend": "vedastro_service_adapter_candidate",
        "candidate_adapter_spike": "service_boundary_not_yet_executable",
        "available": True,
        "evidence": [
            "VedAstro/VedAstro tracked in local open-source scans",
            "MIT posture already recorded in research docs",
            "adapter execution is still missing from this Python workspace",
        ],
        "license_gate": "VedAstro is MIT, but the C# core must stay behind a reviewed service boundary rather than being mixed into the Python runtime path.",
        "runtime_setting_exposure": "blocked_until_parity_timeout_and_license_gates",
        "parity_gate_required": "Must emit EphemerisAdapterContract rows, enforce timeout handling, and pass longitude parity thresholds before any runtime setting exposure.",
        "service_gate": "Need a documented request schema, response normalization layer, retry/timeout policy, and provenance fields before wiring a real adapter.",
    }

    return {
        "valid": True,
        "candidate_adapter_spike": True,
        "runtime_setting_exposure": "do_not_expose_non_swisseph_backend_yet",
        "license_gate": {
            "xalen_ephemeris_candidate": xalen_ephemeris_candidate["license_gate"],
            "vedastro_service_adapter_candidate": vedastro_service_adapter_candidate["license_gate"],
        },
        "parity_gate_required": "Run scripts/ephemeris_adapter_contract.py with real candidate rows before settings exposure.",
        "candidate_backends": {
            "xalen_ephemeris_candidate": xalen_ephemeris_candidate,
            "vedastro_service_adapter_candidate": vedastro_service_adapter_candidate,
        },
        "next_step": "Implement an isolated candidate adapter only after local executable assets or a reviewed external service boundary are present.",
    }


def main() -> int:
    print(json.dumps(build_spike(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
