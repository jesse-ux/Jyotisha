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


def _read(*parts: str) -> str:
    path = ROOT.joinpath(*parts)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _package_dependency(name: str) -> bool:
    package = _read("jyotish-app", "package.json")
    return f'"{name}"' in package or f"'{name}'" in package


def _package_license(*parts: str) -> str:
    text = _read(*parts)
    if not text:
        return "not_found"
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "unreadable"
    return str(data.get("license") or "unspecified")


def build_spike() -> Dict[str, Any]:
    swisseph_wasm_assets = [
        "jyotish-app/public/swisseph-wasm/wasm/swisseph.wasm",
        "jyotish-app/public/swisseph/swisseph.wasm",
        "jyotish-app/lib/swisseph-wasm/swisseph.js",
    ]
    swisseph_wasm_candidate = {
        "candidate_backend": "swisseph_wasm_candidate",
        "candidate_adapter_spike": "asset_detected_no_runtime_switch",
        "available": any(_exists(*path.split("/")) for path in swisseph_wasm_assets),
        "evidence": [path for path in swisseph_wasm_assets if _exists(*path.split("/"))],
        "dependencies": {
            "@swisseph/browser": _package_dependency("@swisseph/browser"),
            "swisseph-wasm": _package_dependency("swisseph-wasm"),
        },
        "package_license": {
            "@swisseph/browser": _package_license("jyotish-app", "node_modules", "@swisseph", "browser", "package.json"),
            "swisseph-wasm": _package_license("jyotish-app", "node_modules", "swisseph-wasm", "package.json"),
        },
        "license_gate": "Swiss Ephemeris WASM remains under Swiss Ephemeris licensing boundaries; verify commercial/GPL compatibility before distribution claims.",
        "distribution_gate": "AGPL-3.0 and GPL-3.0-or-later packages must not be treated as low-risk proprietary desktop/PWA dependencies.",
        "runtime_setting_exposure": "blocked_until_parity_gate_required",
        "parity_gate_required": "Must emit EphemerisAdapterContract rows and pass swisseph_python longitude_delta_arcsec thresholds.",
    }

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
            "swisseph_wasm_candidate": swisseph_wasm_candidate["license_gate"],
            "xalen_ephemeris_candidate": xalen_ephemeris_candidate["license_gate"],
            "vedastro_service_adapter_candidate": vedastro_service_adapter_candidate["license_gate"],
        },
        "package_license": swisseph_wasm_candidate["package_license"],
        "parity_gate_required": "Run scripts/ephemeris_adapter_contract.py with real candidate rows before settings exposure.",
        "candidate_backends": {
            "swisseph_wasm_candidate": swisseph_wasm_candidate,
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
