#!/usr/bin/env python3
"""Probe jyotishyamitra as an independent oracle without copying implementation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.xalen_oracle_comparison import RASHI


VERSION = "1.4.0"
COMMIT = "86f7eb610a66b06b3f0817d2c53355bec8b3bf8d"
LICENSE = "MIT"
RETURNVAL = "ASTRODATA_DICTIONARY"
SIGN_ALIASES = {"Saggitarius": "Sagittarius"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def wheel_metadata(wheel_path: Path) -> dict:
    with zipfile.ZipFile(wheel_path) as zf:
        metadata_name = next(name for name in zf.namelist() if name.endswith(".dist-info/METADATA"))
        wheel_name = next(name for name in zf.namelist() if name.endswith(".dist-info/WHEEL"))
        license_name = next((name for name in zf.namelist() if name.endswith(".dist-info/licenses/LICENSE")), None)
        metadata_text = zf.read(metadata_name).decode("utf-8", "replace")
        wheel_text = zf.read(wheel_name).decode("utf-8", "replace")
        license_text = zf.read(license_name).decode("utf-8", "replace") if license_name else ""
    fields = {}
    for line in metadata_text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            fields.setdefault(key, value)
    tags = [line.split(": ", 1)[1] for line in wheel_text.splitlines() if line.startswith("Tag: ")]
    return {
        "metadata_name": metadata_name,
        "wheel_name": wheel_name,
        "name": fields.get("Name"),
        "version": fields.get("Version"),
        "license": fields.get("License"),
        "license_file_name": license_name,
        "license_file_sha256": _sha256_bytes(license_text.encode("utf-8")) if license_text else None,
        "license_file_spdx_inferred": "MIT" if "MIT License" in license_text else None,
        "requires_python": fields.get("Requires-Python"),
        "summary": fields.get("Summary"),
        "wheel_tags": tags,
        "metadata_sha256": _sha256_bytes(metadata_text.encode("utf-8")),
        "wheel_record_sha256": _sha256_bytes(wheel_text.encode("utf-8")),
    }


def canonical_request(case: dict) -> dict:
    birth = case["birth"]
    return {
        "name": case.get("name", "public_case"),
        "gender": case.get("gender", "male"),
        "place": case.get("place", "unknown"),
        "longitude": case["longitude"],
        "latitude": case["latitude"],
        "timezone": case["timezone"],
        "birth": {
            "year": birth["year"],
            "month": birth["month"],
            "day": birth["day"],
            "hour": birth["hour"],
            "minute": birth["minute"],
            "second": birth.get("second", 0),
        },
        "ayanamsa": case.get("ayanamsa", "package_default"),
        "node_mode": case.get("node_mode", "package_default"),
        "returnval": RETURNVAL,
    }


def schema_fingerprint(raw: object) -> dict:
    paths = []

    def walk(value: object, prefix: str = "$") -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                walk(value[key], f"{prefix}.{key}")
        elif isinstance(value, list):
            paths.append(f"{prefix}[]")
            if value:
                walk(value[0], f"{prefix}[]")
        else:
            paths.append(f"{prefix}:{type(value).__name__}")

    walk(raw)
    joined = "\n".join(paths)
    return {"path_count": len(paths), "sha256": _sha256_bytes(joined.encode("utf-8")), "sample_paths": paths[:80]}


def normalize_raw(raw: object) -> object:
    data = copy.deepcopy(raw)
    try:
        data["Dashas"]["Vimshottari"]["current"]["date"] = "<volatile_run_time>"
    except (TypeError, KeyError):
        pass
    return data


def run_installed_jyotishyamitra(case: dict) -> object:
    import importlib

    jm = importlib.import_module("jyotishyamitra")
    request = canonical_request(case)
    birth = request["birth"]
    data = jm.input_birthdata(
        name=request["name"],
        gender=request["gender"],
        place=request["place"],
        longitude=str(request["longitude"]),
        lattitude=str(request["latitude"]),
        timezone=str(request["timezone"]),
        year=str(birth["year"]),
        month=str(birth["month"]),
        day=str(birth["day"]),
        hour=str(birth["hour"]),
        min=str(birth["minute"]),
        sec=str(birth.get("second", 0)),
    )
    validation = jm.validate_birthdata()
    if validation != "SUCCESS":
        return {"status": "INPUT_ERROR", "validation": validation, "input": data}
    return jm.generate_astrologicalData(jm.get_birthdata(), returnval=request["returnval"])


def run_isolated(wheel_path: Path, case: dict) -> dict:
    with TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "--target", tmp, str(wheel_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        code = (
            "import json,sys;"
            "sys.path.insert(0, sys.argv[1]);"
            "from scripts.jyotishyamitra_adapter_probe import run_installed_jyotishyamitra;"
            "case=json.loads(sys.stdin.read());"
            "print(json.dumps(run_installed_jyotishyamitra(case), ensure_ascii=False, sort_keys=True))"
        )
        env = {**os.environ, "PYTHONPATH": str(Path.cwd())}
        done = subprocess.run(
            [sys.executable, "-c", code, tmp],
            input=_stable_json(case),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=False,
        )
        raw = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip().startswith(("{", "[", '"')) else done.stdout.strip()
        return {
            "install_path": tmp,
            "returncode": done.returncode,
            "stderr": done.stderr.strip(),
            "raw": raw,
        }


def extract_fields(raw: dict) -> dict:
    keys = ("D1", "D2", "D4", "D9", "D10", "ashtakavarga", "shadbala", "vimshottari")
    lowered = {str(k).lower(): k for k in raw}
    out = {}
    for key in keys:
        source = lowered.get(key.lower())
        if source is not None:
            out[key] = raw[source]
    return out


def extract_varga_signs(raw: dict) -> dict:
    out = {}
    for chart in ("D1", "D2", "D4", "D9", "D10"):
        planets = (raw.get(chart) or {}).get("planets") or {}
        signs = {
            planet: SIGN_ALIASES.get(str(data["sign"]), str(data["sign"]))
            for planet, data in planets.items()
            if isinstance(data, dict) and isinstance(data.get("sign"), str) and data["sign"]
        }
        if signs:
            out[chart] = signs
    return out


def extract_local_varga_signs(raw: dict) -> dict:
    d1 = raw.get("planets") or {}
    varga = raw.get("varga") or {}
    surfaces = {"D1": d1, **varga}
    return {
        chart: {
            planet: data["sign"]
            for planet, data in planets.items()
            if isinstance(data, dict) and isinstance(data.get("sign"), str) and data["sign"]
        }
        for chart, planets in surfaces.items()
        if chart in {"D1", "D2", "D4", "D9", "D10"} and isinstance(planets, dict)
    }


def extract_xalen_varga_signs(raw: dict) -> dict:
    varga = raw.get("varga") or {}
    return {
        chart: {
            planet: RASHI.get(str(sign), str(sign))
            for planet, sign in planets.items()
            if isinstance(sign, str) and sign
        }
        for chart, planets in varga.items()
        if chart in {"D1", "D2", "D4", "D9", "D10"} and isinstance(planets, dict)
    }


def build_varga_comparison(jyotishyamitra_raw: dict, local_raw: dict, xalen_raw: dict) -> dict:
    return compare_with_existing_oracles(
        extract_varga_signs(jyotishyamitra_raw),
        extract_local_varga_signs(local_raw),
        extract_xalen_varga_signs(xalen_raw.get("raw", xalen_raw)),
    )


def compare_with_existing_oracles(jyotishyamitra: dict, local: dict, xalen: dict) -> dict:
    rows = []
    counts = {"local": 0, "xalen": 0}
    for section, fields in jyotishyamitra.items():
        if not isinstance(fields, dict):
            continue
        for field, value in fields.items():
            local_value = (local.get(section) or {}).get(field)
            xalen_value = (xalen.get(section) or {}).get(field)
            local_match = local_value is not None and value == local_value
            xalen_match = xalen_value is not None and value == xalen_value
            counts["local"] += int(local_match)
            counts["xalen"] += int(xalen_match)
            rows.append(
                {
                    "section": section,
                    "field": field,
                    "jyotishyamitra_value": value,
                    "local_value": local_value,
                    "xalen_value": xalen_value,
                    "local_status": "not_comparable" if local_value is None else ("match" if local_match else "mismatch"),
                    "xalen_status": "not_comparable" if xalen_value is None else ("match" if xalen_match else "mismatch"),
                }
            )
    return {
        "scope": "jyotishyamitra_field_comparison",
        "row_count": len(rows),
        "match_counts": counts,
        "promotion_allowed": False,
        "truth_policy": "independent_observation_not_truth",
        "rows": rows,
    }


def build_report(
    wheel_path: Path,
    commit: str = COMMIT,
    raw: dict | None = None,
    comparison: dict | None = None,
    request: dict | None = None,
    isolated_run: dict | None = None,
) -> dict:
    if not wheel_path.exists():
        return {
            "scope": "jyotishyamitra_pinned_adapter_probe",
            "oracle": "jyotishyamitra",
            "version": VERSION,
            "source_commit": commit,
            "license": LICENSE,
            "wheel_path": str(wheel_path),
            "status": "blocked",
            "blocked_reason": "fixture_missing",
            "truth_policy": "independent_observation_not_truth",
            "promotion_allowed": False,
            "boundary": "Wheel fixture is required; adapter must not download at test/runtime or use fake zip evidence.",
        }
    raw = raw or {}
    normalized = normalize_raw(raw)
    wheel_hash = _sha256_bytes(wheel_path.read_bytes()) if wheel_path.exists() else None
    meta = wheel_metadata(wheel_path) if wheel_path.exists() else {}
    return {
        "scope": "jyotishyamitra_pinned_adapter_probe",
        "oracle": "jyotishyamitra",
        "version": VERSION,
        "source_commit": commit,
        "source_url": f"https://github.com/VicharaVandana/jyotishyamitra/commit/{commit}",
        "package_url": "https://pypi.org/project/jyotishyamitra/1.4.0/",
        "license": LICENSE,
        "package_metadata": meta,
        "python_runtime": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "wheel_tags": meta.get("wheel_tags", []),
        },
        "canonical_request": request or {},
        "isolated_subprocess": {
            "used": isolated_run is not None,
            "returncode": None if isolated_run is None else isolated_run["returncode"],
            "temporary_install_path": None if isolated_run is None else isolated_run["install_path"],
            "stderr": None if isolated_run is None else isolated_run["stderr"],
        },
        "wheel_path": str(wheel_path),
        "wheel_sha256": wheel_hash,
        "raw_sha256": _sha256_bytes(_stable_json(raw).encode("utf-8")),
        "normalized_raw_sha256": _sha256_bytes(_stable_json(normalized).encode("utf-8")),
        "normalization": {
            "volatile_paths": ["$.Dashas.Vimshottari.current.date"],
            "purpose": "remove run timestamp before replay comparison",
        },
        "schema_fingerprint": schema_fingerprint(raw),
        "raw": raw,
        "comparison": comparison or {},
        "truth_policy": "independent_observation_not_truth",
        "promotion_allowed": False,
        "status": "stable_raw_ready_as_independent_observation" if raw and not (isinstance(raw, dict) and raw.get("status") == "INPUT_ERROR") else "metadata_only_or_input_blocked",
        "boundary": "Adapter calls the installed MIT package as an oracle; it does not copy implementation or promote conclusions.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, default=Path("/tmp/jyotishyamitra_probe/jyotishyamitra-1.4.0-py3-none-any.whl"))
    parser.add_argument("--case-json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = {}
    request = {}
    isolated = None
    if args.case_json:
        case = json.loads(args.case_json.read_text(encoding="utf-8"))
        request = canonical_request(case)
        isolated = run_isolated(args.wheel, case)
        raw = isolated["raw"]
    report = build_report(args.wheel, raw=raw, request=request, isolated_run=isolated)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
