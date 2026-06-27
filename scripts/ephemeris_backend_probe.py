#!/usr/bin/env python3
"""Probe Jyotish ephemeris backend readiness without network access.

This script is intentionally read-only. It turns the ephemeris roadmap into a
repeatable check: what is available now, what is only a benchmark, and what is
not ready to replace the current Swiss Ephemeris path.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _exists(*parts: str) -> bool:
    return (ROOT.joinpath(*parts)).exists()


def _read_text(*parts: str) -> str:
    path = ROOT.joinpath(*parts)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _python_module_status(module_name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(module_name)
    return {
        "module": module_name,
        "available": spec is not None,
        "origin": getattr(spec, "origin", None) if spec else None,
    }


def _package_has_dependency(package_text: str, dependency: str) -> bool:
    return f'"{dependency}"' in package_text or f"'{dependency}'" in package_text


def build_probe() -> dict[str, Any]:
    package_json = _read_text("jyotish-app", "package.json")
    product_gap = _read_text("docs", "research", "product_gap_matrix_2026_06_22.md")
    open_source_scan = _read_text("docs", "research", "open_source_scan_2026_06_22.md")

    swisseph_python_module = _python_module_status("swisseph")
    swisseph_python_available = swisseph_python_module["available"] and "import swisseph as swe" in _read_text(
        "scripts", "jyotish_api_server.py"
    )
    swisseph_wasm_files = [
        "jyotish-app/lib/swisseph-wasm/swisseph.js",
        "jyotish-app/public/swisseph/swisseph.js",
    ]
    swisseph_wasm_available = any(_exists(*path.split("/")) for path in swisseph_wasm_files)

    vedastro_local = _exists("references", "open_source_sources", "VedicAstro")
    vedastro_scan = "VedAstro/VedAstro" in open_source_scan or "VedAstro/VedAstro" in product_gap
    external_benchmark_scan = "naturalstupid/PyJHora" in open_source_scan or "PyJHora" in product_gap
    xalen_scan = "xalen-ephemeris" in product_gap

    candidate_backends: dict[str, dict[str, Any]] = {
        "swisseph_python": {
            "available": bool(swisseph_python_available),
            "replacement_readiness": "primary",
            "license_posture": "current production path; keep Swiss Ephemeris license/data boundary explicit",
            "evidence": [
                "scripts/jyotish_api_server.py imports swisseph",
                swisseph_python_module,
            ],
            "next_step": "keep as canonical longitude source until another backend passes parity cases",
        },
        "swisseph_wasm": {
            "available": bool(swisseph_wasm_available),
            "replacement_readiness": "fallback",
            "license_posture": "browser fallback using Swiss Ephemeris WASM assets; same boundary as Swiss Ephemeris",
            "evidence": [
                path for path in swisseph_wasm_files if _exists(*path.split("/"))
            ]
            + [
                {
                    "@swisseph/browser": _package_has_dependency(package_json, "@swisseph/browser"),
                    "swisseph-wasm": _package_has_dependency(package_json, "swisseph-wasm"),
                }
            ],
            "next_step": "keep for local-first browser degradation, not as a separate accuracy baseline",
        },
        "xalen_ephemeris": {
            "available": False,
            "replacement_readiness": "spike_only",
            "license_posture": "Apache-2.0 candidate from vedika-io/xalen-ephemeris; no local adapter yet",
            "evidence": [
                "tracked in product gap matrix" if xalen_scan else "not found in local docs",
                "no local references/open_source_sources/xalen mirror detected",
            ],
            "next_step": "add an isolated Rust/CLI parity spike before exposing as selectable runtime backend",
        },
        "vedastro": {
            "available": bool(vedastro_local or vedastro_scan),
            "replacement_readiness": "service_adapter_candidate",
            "license_posture": "MIT product/API benchmark; C# stack must stay behind a service/API boundary if reused",
            "evidence": [
                "references/open_source_sources/VedicAstro" if vedastro_local else "no local mirror detected by probe",
                "tracked in open-source scan" if vedastro_scan else "not tracked in current scan",
            ],
            "next_step": "reuse API/OpenAPI/product lessons; implement a service-boundary adapter contract before any runtime exposure",
        },
        "external_benchmark_benchmark": {
            "available": bool(external_benchmark_scan or _python_module_status("jhora")["available"]),
            "replacement_readiness": "benchmark_only",
            "license_posture": "AGPL benchmark/oracle only unless downstream license posture changes",
            "evidence": [
                "tracked as naturalstupid/PyJHora in open-source scan" if external_benchmark_scan else "not tracked in current scan",
                _python_module_status("jhora"),
            ],
            "next_step": "use public examples and expected outputs for parity tests; do not copy AGPL implementation code",
        },
    }

    valid = candidate_backends["swisseph_python"]["available"] or candidate_backends["swisseph_wasm"]["available"]
    return {
        "valid": bool(valid),
        "candidate_backends": candidate_backends,
        "license_posture": {
            "direct_reuse": ["MIT", "Apache-2.0"],
            "benchmark_only": ["AGPL", "GPL", "unknown/no-license"],
            "current_boundary": "Swiss Ephemeris remains the production ephemeris source until parity and license checks pass.",
        },
        "replacement_readiness": {
            "primary": ["swisseph_python"],
            "fallback": ["swisseph_wasm"],
            "spike_only": ["xalen_ephemeris"],
            "service_adapter_candidate": ["vedastro"],
            "benchmark_only": ["external_benchmark_benchmark"],
        },
        "recommendation": [
            "Do not replace SwissEph in core calculations yet.",
            "Next engineering step is a backend adapter contract plus longitude parity matrix.",
            "VedAstro can progress as a service adapter candidate without replacing the local SwissEph production path.",
            "Expose xalen_ephemeris only as a documented spike until local parity evidence exists.",
        ],
    }


def main() -> int:
    result = build_probe()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
