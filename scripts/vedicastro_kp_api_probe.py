#!/usr/bin/env python3
"""Probe local VedicAstro KP API surface in isolation.

Does not require dependencies to be present. If import/runtime is unavailable,
returns a blocked observation artifact with source hashes.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/open_source_sources/VedicAstro"
API = SRC / "vedicastro/VedicAstro.py"


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    payload: dict[str, Any] = {
        "scope": "vedicastro_kp_api_probe",
        "created_at": "2026-07-19",
        "status": "blocked_or_partial",
        "claim_status": "observation_only",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "source_path": str(API.relative_to(ROOT)),
        "source_sha256": sha256(API),
        "api_surface": {
            "class": "VedicHoroscopeData",
            "methods": [
                "get_rl_nl_sl_data",
                "get_planets_data_from_chart",
                "get_houses_data_from_chart",
                "generate_chart",
            ],
            "fields": [
                "Nakshatra",
                "NakshatraLord",
                "SubLord",
                "SubSubLord",
                "house_sub_lord",
                "house_ss_lord",
            ],
        },
        "dependency_identity": {
            "flatlib": {"version": _package_version("flatlib")},
            "polars": {"version": _package_version("polars")},
            "timezonefinder": {"version": _package_version("timezonefinder")},
            "required_flatlib_source": "git+https://github.com/diliprk/flatlib.git@sidereal",
            "observed_pinned_flatlib_commit": "2618c348ce1ab2588548f935ff65f031630b4872",
        },
        "runtime_probe": {"attempted": True},
        "boundary": "Source/API surface hash only unless runtime dependencies and public numeric KP worked examples are both available.",
    }
    try:
        sys.path.insert(0, str(SRC))
        from flatlib import const as flatlib_const  # type: ignore
        from vedicastro.VedicAstro import VedicHoroscopeData  # type: ignore

        cls = VedicHoroscopeData
        ayanamsa_constants = [
            name for name in ("AY_LAHIRI", "AY_KRISHNAMURTI") if hasattr(flatlib_const, name)
        ]
        sample = cls(
            1955,
            2,
            24,
            19,
            15,
            0,
            37.3382,
            -122.0383,
            tz="America/Los_Angeles",
            ayanamsa="Krishnamurti",
            house_system="Placidus",
        ).get_rl_nl_sl_data(0.0)
        payload["runtime_probe"] = {
            "attempted": True,
            "import_status": "success",
            "class_present": cls is not None,
            "method_present": bool(cls and hasattr(cls, "get_rl_nl_sl_data")),
            "sidereal_ayanamsa_constants_present": ayanamsa_constants,
            "sample_degree": 0.0,
            "sample_rl_nl_sl": sample,
        }
        payload["status"] = "partial_runtime_surface_available"
        payload[
            "boundary"
        ] = "KP Rashi/Nakshatra/Sub/SubSub API surface is callable in an isolated dependency path; this is still observation_only until public numeric KP worked examples and replay hashes are archived."
    except Exception as exc:  # dependency/import errors are expected in clean envs
        payload["runtime_probe"] = {
            "attempted": True,
            "import_status": "blocked",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        payload["status"] = "blocked_runtime_import"
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
