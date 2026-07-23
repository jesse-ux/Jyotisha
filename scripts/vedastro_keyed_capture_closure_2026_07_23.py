#!/usr/bin/env python3
"""Summarise keyed VedAstro captures without persisting secrets.

This packet is intentionally a governance artifact.  It records what the
newly-configured API key lets us observe, and what remains blocked because
hosted build identity or public numeric oracle contracts are still missing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "references/oracle/vedastro_keyed_capture_closure_2026_07_23.json"
CONTRACT_PROBE = ROOT / "references/oracle/artifacts/vedastro_steve_jobs_contract_probe_keyed_2026_07_23.json"
PARITY_RAW = ROOT / "references/oracle/artifacts/vedastro_official_parity_raw_keyed_2026_07_23.json"
METHOD_CATALOG = ROOT / "references/oracle/vedastro_method_catalog_keyed_2026_07_23.json"
SELECTED_METHODS = ROOT / "references/oracle/artifacts/vedastro_keyed_gulika_tajika_methods_2026_07_23.json"


TERMS = (
    "KP",
    "Cusp",
    "Prashna",
    "Tajika",
    "Saham",
    "Gulika",
    "Mandi",
    "Sphuta",
    "Panchanga",
    "Hora",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_hits(catalog: dict[str, Any]) -> dict[str, list[str]]:
    capabilities = catalog.get("python_capabilities", [])
    hits: dict[str, list[str]] = {}
    for term in TERMS:
        term_hits = []
        for capability in capabilities:
            method = str(capability.get("method", ""))
            if term.lower() in method.lower():
                term_hits.append(method)
        hits[term] = sorted(set(term_hits))
    return hits


def build_packet() -> dict[str, Any]:
    contract = _load(CONTRACT_PROBE)
    parity = _load(PARITY_RAW)
    catalog = _load(METHOD_CATALOG)
    selected = _load(SELECTED_METHODS)

    hits = _catalog_hits(catalog)
    selected_results = selected.get("results", {})
    selected_status = {
        method: {
            "available": result.get("available"),
            "status": result.get("status"),
        }
        for method, result in selected_results.items()
    }

    return {
        "packet_id": "vedastro_keyed_capture_closure_2026_07_23",
        "scope": "vedastro_keyed_capture_closure",
        "created_at": "2026-07-23",
        "claim_status": "keyed_observation_partial",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "api_key_policy": {
            "configured_by_user": True,
            "persisted_in_artifact": False,
            "secret_material_allowed_in_git": False,
        },
        "source_artifacts": {
            "contract_probe": {
                "path": str(CONTRACT_PROBE.relative_to(ROOT)),
                "sha256": _sha256_file(CONTRACT_PROBE),
                "contract_status": contract.get("contract_status"),
                "method_contract_status": contract.get("method_contract", {}).get("status"),
                "api_version_contract_status": contract.get("api_version_contract", {}).get("status"),
                "server_identity_contract_status": contract.get("server_identity_contract", {}).get("status"),
            },
            "official_parity_raw": {
                "path": str(PARITY_RAW.relative_to(ROOT)),
                "sha256": _sha256_file(PARITY_RAW),
                "status": parity.get("status"),
                "response_hash": parity.get("response_hash"),
                "fanout_statuses": parity.get("fanout_statuses", {}),
            },
            "method_catalog": {
                "path": str(METHOD_CATALOG.relative_to(ROOT)),
                "sha256": _sha256_file(METHOD_CATALOG),
                "summary": catalog.get("summary", {}),
            },
            "selected_methods": {
                "path": str(SELECTED_METHODS.relative_to(ROOT)),
                "sha256": _sha256_file(SELECTED_METHODS),
                "summary": selected.get("summary", {}),
                "statuses": selected_status,
            },
        },
        "method_catalog_hits": hits,
        "closure_findings": [
            {
                "gap": "hosted_identity",
                "status": "blocked",
                "reason": "Hosted API returned no explicit build metadata, source commit, assembly version, DLL hash, or image digest.",
            },
            {
                "gap": "longitude_method_semantics",
                "status": "observation_resolved_for_probe_case",
                "reason": "Keyed replay reports AllPlanetData/AllPlanetLongitude matching Nirayana for the Steve Jobs contract probe within the probe contract.",
            },
            {
                "gap": "kp_exact_12_cusp",
                "status": "blocked",
                "reason": "Catalog exposes IsPlanetInHouseKP only; no complete 12-cusp exact longitude/star/sub/sub-sub endpoint was found.",
            },
            {
                "gap": "gulika_tajika_selected_methods",
                "status": "blocked_pending_payload_contract",
                "reason": "Relevant methods exist, but selected runner classified them as unsupported_signature for the current generic payload strategy.",
            },
            {
                "gap": "prashna_saham_sphuta",
                "status": "blocked",
                "reason": "No Prashna, Saham, or Sphuta method names were found in the keyed catalog capture.",
            },
        ],
        "claim_boundary": (
            "The key enables pinned raw observation and method catalog capture. "
            "It does not by itself provide hosted build identity, KP 12-cusp oracle, "
            "Prashna/Saham/Sphuta numeric packets, selected Gulika/Tajika payload contracts, "
            "or timing/birth-rectification holdout labels."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    packet = build_packet()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
