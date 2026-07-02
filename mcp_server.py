#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jyotish MCP Server v1.0
Exposes Jyotish-Vedic-Astrology calculation engine as MCP tools.

Install:
  pip install mcp

Run:
  python3 mcp_server.py

MCP client config should point at this repository path, for example:
  {
    "mcpServers": {
      "jyotish": {
        "command": "python3",
        "args": ["/Users/wuyongnaren/Documents/印度占星/mcp_server.py"],
        "env": {}
      }
    }
  }

The `.workbuddy` copy is a distribution mirror / historical reference only;
it is not the runtime source of truth for this server.
"""

import sys
import os
import json
import subprocess
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Any, Optional, List

# Add scripts dir to path so imports work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))

from local_env import load_local_env

from mcp.server.fastmcp import FastMCP
from functional_benefics import derive_functional_benefic_malefic
from vedastro_priority import official_snapshot_evidence
from unified_consultation_orchestrator import UnifiedConsultationOrchestrator

load_local_env(SCRIPT_DIR)

# ============================================================================
# MCP Server
# ============================================================================
mcp = FastMCP(
    "jyotish-vedic-astrology",
    instructions=(
        "Jyotish (Vedic Astrology) calculation engine. "
        "Provides chart calculation, Vimshottari Dasha, Shadbala, "
        "Ashtakavarga, Nakshatra analysis, and full-reading synthesis. "
        "All calculations use Swiss Ephemeris (Lahiri ayanamsa). "
        "IMPORTANT: partial techniques (marked in audit) are approximate "
        "and should NOT be used as sole evidence for high-stakes predictions."
    ),
)

_UNIFIED_CONSULTATION_ORCHESTRATOR = UnifiedConsultationOrchestrator()

# ============================================================================
# Helpers
# ============================================================================

def _run_engine(subcommand: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run jyotish_engine.py subcommand and return parsed JSON output."""
    engine = os.path.join(SCRIPT_DIR, "scripts", "jyotish_engine.py")
    cmd = [sys.executable, engine, subcommand]
    for k, v in args.items():
        if v is None:
            continue
        flag = "--" + k.replace("_", "-")
        if isinstance(v, bool):
            if v:
                cmd.append(flag)
        else:
            cmd.extend([flag, str(v)])
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120, cwd=SCRIPT_DIR
    )
    if result.returncode != 0:
        return {"error": True, "stderr": result.stderr, "stdout": result.stdout}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_output": result.stdout}


def _audit_status() -> Dict[str, Any]:
    """Run audit and return structured status."""
    audit = os.path.join(SCRIPT_DIR, "scripts", "audit_capabilities.py")
    result = subprocess.run(
        [sys.executable, audit, "--mode", "validate"],
        capture_output=True, text=True, timeout=30, cwd=SCRIPT_DIR
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"valid": False, "raw": result.stdout}


def _repo_relative_exists(path: str) -> bool:
    return os.path.exists(os.path.join(SCRIPT_DIR, path))


def _load_json_file(path: str) -> Dict[str, Any]:
    with open(os.path.join(SCRIPT_DIR, path), "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _existing_paths(paths: List[str]) -> List[str]:
    return [path for path in paths if _repo_relative_exists(path)]


CORE_RULE_SOURCE_REFS = [
    "references/prediction-boundary-protocol.md",
    "references/event_judgment_skeleton.md",
    "references/planetary-dignity-complete-reference.md",
    "references/retrograde-combustion-war-guide.md",
    "references/transit-multi-reference-guide.md",
]


def _build_interpretation_source_inventory(source_refs: List[str]) -> Dict[str, Any]:
    primary_truth = [
        "references/interpretation_template_registry.json",
        "references/raman-house-judgment-methodology.md",
        "references/bphs-ch48-narayana-dasha.md",
        "references/mandatory-verification-gate-protocol.md",
        "references/real-reading-quality-checklist.md",
    ]
    frontend_interpretation = [
        "jyotish-app/interpretation.js",
        "jyotish-app/analysis-deep.js",
        "jyotish-app/planet-house-details-a.js",
        "jyotish-app/planet-house-details-b.js",
        "jyotish-app/planet-house-details-c.js",
    ]
    qa_governance = [
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md",
    ]
    reader_validation = [
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/chart_reading_rules.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md",
    ]
    yoga_rules = [
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/yogas.md",
        "references/yoga_rules.json",
        "jyotish-app/yoga-details-a.js",
        "jyotish-app/yoga-details-b.js",
        "jyotish-app/yoga-extended.js",
        "jyotish-app/yoga-extended-b.js",
    ]
    saham_rules = [
        "references/saham_rules.json",
    ]
    reference_layer = [
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md",
        "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md",
        *CORE_RULE_SOURCE_REFS,
        *frontend_interpretation,
        *qa_governance,
        *reader_validation,
        *yoga_rules,
        *saham_rules,
    ]
    quarantined_drafts = [
        "docs/research/local_drafts/2026-06/skill_fragment_map_and_source_of_truth_2026_06_26.md",
        "docs/research/local_drafts/2026-06/dasha_accuracy_closure_status_2026_06_26.md",
        "docs/research/local_drafts/2026-06/dasha_code_only_priority_rerank_2026_06_26.md",
    ]

    layers = {
        "primary_truth": {
            "status": "available",
            "promotion_status": "primary_truth",
            "source_refs": _existing_paths(primary_truth),
            "missing_refs": [path for path in primary_truth if not _repo_relative_exists(path)],
        },
        "frontend_interpretation": {
            "status": "available",
            "promotion_status": "reference_layer",
            "source_refs": _existing_paths(frontend_interpretation),
            "missing_refs": [path for path in frontend_interpretation if not _repo_relative_exists(path)],
        },
        "qa_governance": {
            "status": "available",
            "promotion_status": "reference_layer",
            "source_refs": _existing_paths(qa_governance),
            "missing_refs": [path for path in qa_governance if not _repo_relative_exists(path)],
        },
        "reader_validation": {
            "status": "available",
            "promotion_status": "reference_layer",
            "source_refs": _existing_paths(reader_validation),
            "missing_refs": [path for path in reader_validation if not _repo_relative_exists(path)],
        },
        "yoga_rules": {
            "status": "available",
            "promotion_status": "reference_layer",
            "source_refs": _existing_paths(yoga_rules),
            "missing_refs": [path for path in yoga_rules if not _repo_relative_exists(path)],
        },
        "saham_rules": {
            "status": "available",
            "promotion_status": "reference_layer",
            "source_refs": _existing_paths(saham_rules),
            "missing_refs": [path for path in saham_rules if not _repo_relative_exists(path)],
        },
        "core_rule_sources": {
            "status": "available",
            "promotion_status": "primary_truth_candidate",
            "promotion_batch": "priority1_batch1_core5",
            "source_refs": _existing_paths(CORE_RULE_SOURCE_REFS),
            "missing_refs": [path for path in CORE_RULE_SOURCE_REFS if not _repo_relative_exists(path)],
            "boundary": "First promoted core references; visible to strict workflows but still subject to conflict arbitration.",
        },
        "quarantined_drafts": {
            "status": "quarantined",
            "promotion_status": "not_truth_source",
            "source_refs": _existing_paths(quarantined_drafts),
            "missing_refs": [path for path in quarantined_drafts if not _repo_relative_exists(path)],
            "boundary": "Listed for awareness only; drafts are not promoted into runtime source_refs.",
        },
    }
    missing_refs = [path for layer in layers.values() for path in layer["missing_refs"]]
    quarantined_refs = set(layers["quarantined_drafts"]["source_refs"])
    promoted_quarantined = sorted(quarantined_refs.intersection(source_refs))
    status = "used" if not missing_refs and not promoted_quarantined else "partial"
    return {
        "status": status,
        "source": "repo_interpretation_source_inventory_v1",
        "layers": layers,
        "summary": {
            "primary_truth_count": len(layers["primary_truth"]["source_refs"]),
            "reference_layer_count": len(_existing_paths(reference_layer)),
            "quarantined_draft_count": len(layers["quarantined_drafts"]["source_refs"]),
            "missing_ref_count": len(missing_refs),
            "promoted_quarantined_count": len(promoted_quarantined),
        },
        "missing_refs": missing_refs,
        "promoted_quarantined_refs": promoted_quarantined,
        "boundary": "Inventory is explicit and conservative; local drafts are indexed but not treated as truth sources.",
    }


@lru_cache(maxsize=1)
def _existing_interpretation_source_pack() -> Dict[str, Any]:
    """Return the existing repo interpretation/source layers as an explicit evidence pack."""
    template_path = "references/interpretation_template_registry.json"
    p1_p12_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md"
    house_framework_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md"
    qa_rules_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/qa_rules.md"
    core_yogas_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/yogas.md"
    reader_chart_rules_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/chart_reading_rules.md"
    reader_validation_rules_path = "references/open_source_sources/vedic-astro-skills/codex/skills/vedic-reader/resources/validation_rules.md"
    raman_path = "references/raman-house-judgment-methodology.md"
    bphs_narayana_path = "references/bphs-ch48-narayana-dasha.md"
    mevg_path = "references/mandatory-verification-gate-protocol.md"
    real_case_checklist_path = "references/real-reading-quality-checklist.md"
    core_rule_paths = CORE_RULE_SOURCE_REFS
    frontend_interpretation_paths = [
        "jyotish-app/interpretation.js",
        "jyotish-app/analysis-deep.js",
    ]
    planet_house_paths = [
        "jyotish-app/planet-house-details-a.js",
        "jyotish-app/planet-house-details-b.js",
        "jyotish-app/planet-house-details-c.js",
    ]
    yoga_rule_paths = [
        core_yogas_path,
        "references/yoga_rules.json",
        "jyotish-app/yoga-details-a.js",
        "jyotish-app/yoga-details-b.js",
        "jyotish-app/yoga-extended.js",
        "jyotish-app/yoga-extended-b.js",
    ]
    saham_rule_paths = [
        "references/saham_rules.json",
    ]

    template_ids: List[str] = []
    template_count = 0
    try:
        registry = _load_json_file(template_path)
        templates = registry.get("templates") if isinstance(registry.get("templates"), dict) else {}
        template_ids = sorted(templates.keys())
        template_count = len(template_ids)
    except Exception:
        template_ids = []
        template_count = 0

    source_refs = [
        template_path,
        p1_p12_path,
        house_framework_path,
        raman_path,
        bphs_narayana_path,
        mevg_path,
        real_case_checklist_path,
        *core_rule_paths,
        *frontend_interpretation_paths,
        *planet_house_paths,
        qa_rules_path,
        reader_chart_rules_path,
        reader_validation_rules_path,
        *yoga_rule_paths,
        *saham_rule_paths,
    ]
    missing_refs = [path for path in source_refs if not _repo_relative_exists(path)]
    inventory = _build_interpretation_source_inventory(source_refs)
    return {
        "status": "used" if not missing_refs and inventory.get("status") == "used" else "partial",
        "source": "repo_existing_interpretation_sources",
        "source_refs": source_refs,
        "missing_refs": missing_refs,
        "interpretation_source_inventory": inventory,
        "template_registry": {
            "path": template_path,
            "template_count": template_count,
            "template_ids": template_ids,
        },
        "frameworks": [
            "p1_p12",
            "house_framework",
            "raman_functional_house_judgment",
            "bphs_narayana_dasha",
            "mevg_mandatory_external_verification",
            "real_case_quality_checklist",
            "priority1_batch1_core_rule_sources",
            "qa_governance_rules",
            "reader_validation_rules",
            "frontend_interpretation_layer",
            "yoga_rule_layer",
            "saham_rule_layer",
        ],
        "bphs_raman_layer": {
            "status": "available" if _repo_relative_exists(raman_path) and _repo_relative_exists(bphs_narayana_path) else "partial",
            "source_refs": [raman_path, bphs_narayana_path],
        },
        "core_rule_source_layer": {
            "status": "available" if all(_repo_relative_exists(path) for path in core_rule_paths) else "partial",
            "source_refs": core_rule_paths,
            "promotion_status": "primary_truth_candidate",
            "promotion_batch": "priority1_batch1_core5",
            "boundary": "Audit-promoted core references; use as visible rule sources with conflict arbitration.",
        },
        "frontend_interpretation_layer": {
            "status": "available" if all(_repo_relative_exists(path) for path in frontend_interpretation_paths) else "partial",
            "source_refs": frontend_interpretation_paths,
            "promotion_status": "reference_layer",
        },
        "frontend_planet_house_details": {
            "status": "available" if all(_repo_relative_exists(path) for path in planet_house_paths) else "partial",
            "coverage": "9_planets_x_12_houses",
            "planet_count": 9,
            "house_count": 12,
            "source_refs": planet_house_paths,
        },
        "qa_governance_layer": {
            "status": "available" if _repo_relative_exists(qa_rules_path) else "partial",
            "source_refs": [qa_rules_path],
            "promotion_status": "reference_layer",
        },
        "reader_validation_layer": {
            "status": "available" if all(_repo_relative_exists(path) for path in [reader_chart_rules_path, reader_validation_rules_path]) else "partial",
            "source_refs": [reader_chart_rules_path, reader_validation_rules_path],
            "promotion_status": "reference_layer",
        },
        "yoga_rule_layer": {
            "status": "available" if all(_repo_relative_exists(path) for path in yoga_rule_paths) else "partial",
            "source_refs": yoga_rule_paths,
            "promotion_status": "reference_layer",
        },
        "saham_rule_layer": {
            "status": "available" if all(_repo_relative_exists(path) for path in saham_rule_paths) else "partial",
            "source_refs": saham_rule_paths,
            "promotion_status": "reference_layer",
        },
        "mevg_gate": {
            "status": "blocked",
            "required": True,
            "source_ref": mevg_path,
            "effect_on_confidence": "blocks_or_downgrades_interpretive_claims_until_completed",
        },
        "real_case_calibration": {
            "status": "blocked",
            "required": True,
            "source_ref": real_case_checklist_path,
            "effect_on_confidence": "caps_confidence_without_matching_cases",
        },
        "boundary": (
            "This pack exposes existing local interpretation sources. It does not replace live MEVG web "
            "collection, real-case calibration, chart calculation, or oracle closure."
        ),
    }


def _execute_mcp_consultation_workflow(
    *,
    question: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    transit_date: str,
    node_mode: str,
    entry_mode: str = "direct_chart",
    theme: list[str] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    from jyotish_api_server import JyotishAPIHandler, execute_consultation_workflow

    handler = JyotishAPIHandler.__new__(JyotishAPIHandler)
    return execute_consultation_workflow(
        handler,
        body={
            "question": question,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "lat": lat,
            "lon": lon,
            "tz": tz,
            "transit_date": transit_date,
            "node_mode": node_mode,
            "entry_mode": entry_mode,
            "theme": theme or [],
            "events": events or [],
        },
        surface="skill_mcp",
    )


def _safe_get(data: Dict[str, Any], *path: str) -> Any:
    cur: Any = data
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _convergence_score(convergence: Any) -> int:
    if not isinstance(convergence, dict):
        return 0
    level = convergence.get("convergence_level")
    mapping = {"L1": 20, "L2": 40, "L3": 60, "L4": 80, "L5": 95}
    return mapping.get(level, 0)


_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_TO_INDEX = {name: idx for idx, name in enumerate(_SIGNS)}
_SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
_NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]
_NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]
_WEALTH_HOUSES = {2, 5, 9, 10, 11}
_NAKSHATRA_SPAN = 360.0 / 27.0
_SHADBALA_REQUIRED_COMPONENTS = ["sthana", "dig", "kala", "chesta", "naisargika", "drik"]
_VEDASTRO_ROUTE_DOMAIN = {
    "career": "career",
    "relationship": "marriage",
    "finance": "wealth",
}


def _normalize_longitude(value: Any) -> Optional[float]:
    try:
        return float(value) % 360.0
    except (TypeError, ValueError):
        return None


def _circular_distance_deg(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _sign_from_longitude(lon: float) -> str:
    return _SIGNS[int(lon // 30.0) % 12]


def _house_from_longitude(lon: float, asc_sign: Optional[str]) -> Optional[int]:
    asc_idx = _SIGN_TO_INDEX.get(asc_sign) if asc_sign else None
    if asc_idx is None:
        return None
    return ((int(lon // 30.0) - asc_idx) % 12) + 1


def _wealth_lord_for_house(asc_sign: Optional[str], house_num: int) -> Optional[str]:
    asc_idx = _SIGN_TO_INDEX.get(asc_sign) if asc_sign else None
    if asc_idx is None:
        return None
    house_sign = _SIGNS[(asc_idx + house_num - 1) % 12]
    return _SIGN_LORDS.get(house_sign)


def _planet_snapshot(planets: Dict[str, Any], name: str, asc_sign: Optional[str]) -> Dict[str, Any]:
    raw = planets.get(name) if isinstance(planets, dict) else None
    data = dict(raw) if isinstance(raw, dict) else {}
    lon = _normalize_longitude(data.get("degree_raw", data.get("degree")))
    if lon is not None:
        data.setdefault("degree_raw", lon)
        data.setdefault("sign", _sign_from_longitude(lon))
        if data.get("house") is None:
            house = _house_from_longitude(lon, asc_sign)
            if house is not None:
                data["house"] = house
    return data


def _derive_yogi_wealth_support(modules: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(modules, dict):
        return None
    chart = modules.get("chart")
    if not isinstance(chart, dict):
        return None

    ascendant = chart.get("ascendant") if isinstance(chart.get("ascendant"), dict) else {}
    asc_lon = _normalize_longitude(ascendant.get("degree_raw", ascendant.get("lon", ascendant.get("degree"))))
    asc_sign = ascendant.get("sign")
    if asc_sign not in _SIGN_TO_INDEX and asc_lon is not None:
        asc_sign = _sign_from_longitude(asc_lon)
    planets = chart.get("planets") if isinstance(chart.get("planets"), dict) else {}

    sun_lon = _normalize_longitude(_safe_get(planets, "Sun", "degree_raw") or _safe_get(planets, "Sun", "degree"))
    moon_lon = _normalize_longitude(_safe_get(planets, "Moon", "degree_raw") or _safe_get(planets, "Moon", "degree"))
    if sun_lon is None or moon_lon is None:
        return None

    yogi_point_lon = (sun_lon + moon_lon) % 360.0
    yogi_nak_idx = int(yogi_point_lon // _NAKSHATRA_SPAN) % 27
    yogi_point_nakshatra = _NAKSHATRA_NAMES[yogi_nak_idx]
    yogi_planet = _NAKSHATRA_LORDS[yogi_nak_idx]
    duplicate_yogi = _SIGN_LORDS[_sign_from_longitude(yogi_point_lon)]
    avayogi = _NAKSHATRA_LORDS[(yogi_nak_idx + 6) % 27]
    yogi_point_house = _house_from_longitude(yogi_point_lon, asc_sign)

    yogi_data = _planet_snapshot(planets, yogi_planet, asc_sign)
    avayogi_data = _planet_snapshot(planets, avayogi, asc_sign)

    signals: List[str] = []
    wealth_lord_links: List[str] = []
    tight_orb_hits: List[str] = []
    risk_flags: List[str] = []

    yogi_house = yogi_data.get("house")
    if yogi_house in _WEALTH_HOUSES:
        signals.append("yogi_planet_in_wealth_house")

    second_lord = _wealth_lord_for_house(asc_sign, 2)
    eleventh_lord = _wealth_lord_for_house(asc_sign, 11)
    if yogi_planet == second_lord:
        wealth_lord_links.append("yogi_planet_is_2l")
        signals.append("yogi_planet_is_2l")
    if yogi_planet == eleventh_lord:
        wealth_lord_links.append("yogi_planet_is_11l")
        signals.append("yogi_planet_is_11l")

    lagna_yogi_distance = None
    if asc_lon is not None:
        lagna_yogi_distance = round(_circular_distance_deg(asc_lon, yogi_point_lon), 4)
        if lagna_yogi_distance <= 1.0:
            tight_orb_hits.append("lagna_yogi_tight_orb")
            signals.append("lagna_yogi_tight_orb")

    avayogi_house = avayogi_data.get("house")
    if avayogi_house in _WEALTH_HOUSES:
        risk_flags.append("avayogi_in_wealth_house")

    if len(signals) >= 3 and not risk_flags:
        level = "strong"
    elif len(signals) >= 2:
        level = "moderate"
    else:
        level = "weak"

    return {
        "level": level,
        "source": "yogi_asc_tight_orb_wealth",
        "yogi_planet": yogi_planet,
        "duplicate_yogi": duplicate_yogi,
        "avayogi": avayogi,
        "yogi_point_longitude": round(yogi_point_lon, 4),
        "yogi_point_nakshatra": yogi_point_nakshatra,
        "yogi_point_house": yogi_point_house,
        "lagna_yogi_distance_deg": lagna_yogi_distance,
        "tight_orb_hits": tight_orb_hits,
        "wealth_lord_links": wealth_lord_links,
        "signals": signals,
        "risk_flags": risk_flags,
    }


def _derive_wealth_promise_strength(modules: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    yogi_support = _derive_yogi_wealth_support(modules)
    yogas_doshas = modules.get("yogas_doshas") if isinstance(modules, dict) else {}
    dhana = yogas_doshas.get("dhana_yogas") if isinstance(yogas_doshas, dict) else {}
    yogas = dhana.get("yogas") if isinstance(dhana, dict) else None

    has_dhana = False
    has_lakshmi = False
    dhana_level = "weak"
    lakshmi_level = "weak"

    sources = set()
    if isinstance(yogas, list) and yogas:
        for row in yogas:
            if not isinstance(row, dict):
                continue
            lvl = str(row.get("strength", "")).lower()
            row_type = str(row.get("type", "")).lower()
            if "lakshmi" in row_type:
                sources.add("lakshmi")
                has_lakshmi = True
                if lvl == "strong" or (lvl == "moderate" and lakshmi_level == "weak"):
                    lakshmi_level = lvl
            elif "dhana" in row_type:
                sources.add("dhana")
                has_dhana = True
                if lvl == "strong" or (lvl == "moderate" and dhana_level == "weak"):
                    dhana_level = lvl

    if not has_dhana and not has_lakshmi:
        return None

    yogi_level = yogi_support.get("level") if isinstance(yogi_support, dict) else None
    if yogi_level in {"moderate", "strong"}:
        sources.add("yogi")
    supporting_sources = sorted(sources)

    if has_dhana and has_lakshmi and "yogi" in sources:
        primary_source = "dhana_lakshmi_yogi_hooks"
    elif has_dhana and "yogi" in sources:
        primary_source = "dhana_yogi_hooks"
    elif has_dhana and has_lakshmi:
        primary_source = "dhana_lakshmi_hooks"
    elif has_dhana:
        primary_source = "dhana_yogas"
    else:
        primary_source = "lakshmi_hooks"

    if dhana_level == "strong" or lakshmi_level == "strong":
        final_level = "strong"
    elif dhana_level == "moderate" or lakshmi_level == "moderate":
        final_level = "moderate"
    else:
        final_level = "weak"

    return {
        "level": final_level,
        "primary_source": primary_source,
        "supporting_sources": supporting_sources,
        "count": len(yogas) if isinstance(yogas, list) else 0,
        "source_diversity": len(supporting_sources),
        "yogi_support": yogi_support if yogi_level in {"moderate", "strong"} else None,
    }


def _check_external_avayogi_risk(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    external_truth = result.get("external_truth") if isinstance(result, dict) else {}
    avayogi_planet = external_truth.get("avayogi_planet") if isinstance(external_truth, dict) else None
    if not avayogi_planet:
        return None

    modules = result.get("modules", {}) if isinstance(result, dict) else {}
    chart = modules.get("chart") if isinstance(modules, dict) else {}
    planets = chart.get("planets") if isinstance(chart, dict) else {}
    planet_data = planets.get(avayogi_planet) if isinstance(planets, dict) else None
    if not isinstance(planet_data, dict):
        return None

    house = planet_data.get("house")
    status = str(planet_data.get("status", ""))
    if "Own Sign" in status or "Moolatrikona" in status or "Exalted" in status:
        return None

    signals: List[str] = []
    if house in {1, 2, 5, 9, 10, 11}:
        signals.append("avayogi_in_wealth_house")

    if not signals:
        return None

    return {
        "planet": avayogi_planet,
        "house": house,
        "status": status,
        "source": "external_avayogi_planet",
        "risk_level": "moderate",
        "signals": signals,
    }


def _derive_jaimini_marriage_support(present: Dict[str, Any]) -> Dict[str, Any]:
    signals: List[str] = []
    darakaraka = present.get("darakaraka")
    upapada_lagna = present.get("upapada_lagna")

    if darakaraka:
        signals.append("darakaraka_active")

    if isinstance(darakaraka, dict):
        if darakaraka.get("house") == 7 or darakaraka.get("house_from_lagna") == 7:
            signals.append("dk_7h_link")
        if darakaraka.get("ul_link") or darakaraka.get("linked_to_ul"):
            signals.append("dk_ul_link")

    if isinstance(upapada_lagna, dict) and isinstance(darakaraka, dict):
        dk_sign = darakaraka.get("sign")
        ul_sign = upapada_lagna.get("sign")
        if dk_sign and ul_sign and dk_sign == ul_sign and "dk_ul_link" not in signals:
            signals.append("dk_ul_link")

    if present.get("jaimini_timing_support"):
        signals.append("jaimini_dasha_support")

    if not signals:
        level = "none"
    elif len(signals) == 1:
        level = "weak"
    elif "darakaraka_active" in signals:
        level = "moderate"
    else:
        level = "weak"

    return {
        "level": level,
        "signals": signals,
        "source": "jaimini_bridge_v1",
    }


def _external_activation_ledger(modules: Dict[str, Any]) -> tuple[Any, Dict[str, Any]]:
    ledger = _safe_get(modules, "external_activation", "evidence_ledger")
    if isinstance(ledger, list):
        activation = modules.get("external_activation") if isinstance(modules, dict) else {}
        metadata = activation.get("source_metadata") if isinstance(activation, dict) else {}
        return ledger, metadata if isinstance(metadata, dict) else {}
    adapter_result = modules.get("vedastro_range_scan_result") if isinstance(modules, dict) else {}
    if isinstance(adapter_result, dict) and adapter_result.get("backend") == "vedastro_service_adapter_candidate":
        ledger = adapter_result.get("evidence_ledger")
        metadata = adapter_result.get("source_metadata")
        return ledger, metadata if isinstance(metadata, dict) else {}
    return None, {}


def _derive_external_activation_support(modules: Dict[str, Any], domain: str) -> Dict[str, Any]:
    ledger, provenance = _external_activation_ledger(modules)
    adapter_result = modules.get("vedastro_range_scan_result") if isinstance(modules, dict) else {}
    if not isinstance(adapter_result, dict):
        adapter_result = {}
    daily_windows = adapter_result.get("daily_windows") if isinstance(adapter_result.get("daily_windows"), list) else []
    top_daily_window = adapter_result.get("top_daily_window") if isinstance(adapter_result.get("top_daily_window"), dict) else None
    official_day_signals = _derive_official_day_signals(domain, daily_windows)
    if not isinstance(ledger, list):
        return {
            "level": "missing_required_external_radar",
            "source": "vedastro_service_adapter_candidate",
            "signals": [],
            "events": [],
            "daily_windows": daily_windows,
            "top_daily_window": top_daily_window,
            "official_day_signals": official_day_signals,
            "required": True,
            "operation": "range_scan",
            "external_calculation_coverage": "VedAstro 596+/600+ calculation nodes",
            "provenance": provenance,
            "reason": (
                "VedAstro EventsAtRange / FindLifeEvents-style high-frequency radar "
                "was not provided; keep timing confidence bounded."
            ),
        }

    events: List[Dict[str, Any]] = []
    for event in ledger:
        if not isinstance(event, dict):
            continue
        if event.get("operation") != "range_scan":
            continue
        if event.get("domain") != domain:
            continue
        if event.get("source") != "vedastro_service_adapter_candidate":
            continue
        events.append(event)

    if not events:
        if official_day_signals:
            top_signal = official_day_signals[0]
            level = "moderate" if top_signal.get("confidence") == "high" else "weak"
        else:
            level = "none"
    elif any((event.get("score") or 0) >= 70 for event in events):
        level = "moderate"
    else:
        level = "weak"

    return {
        "level": level,
        "source": "vedastro_service_adapter_candidate" if events or official_day_signals else None,
        "signals": ["vedastro_range_scan"] if events or official_day_signals else [],
        "events": events,
        "daily_windows": daily_windows,
        "top_daily_window": top_daily_window,
        "official_day_signals": official_day_signals,
        "required": True,
        "operation": "range_scan",
        "external_calculation_coverage": "VedAstro 596+/600+ calculation nodes",
        "provenance": provenance,
    }


def _derive_official_day_signals(domain: str, daily_windows: Any) -> List[Dict[str, Any]]:
    if not isinstance(daily_windows, list):
        return []
    positive_families = {
        "career": {"career_trigger"},
        "marriage": {"marriage_trigger"},
        "wealth": {"wealth_trigger", "gains_trigger"},
    }
    negative_families = {
        "career": {"career_pressure"},
        "marriage": {"relationship_pressure"},
        "wealth": {"wealth_pressure"},
    }
    label_map = {
        "career": {
            "opportunity_entry": ("opportunity_entry", "事业机会进入日"),
            "pressure_opportunity": ("pressure_opportunity", "事业压力机会日"),
            "relocation_motion": ("relocation_motion", "事业迁移动作日"),
            "closure_risk": ("closure_risk", "事业真正收尾风险日"),
            "mixed": ("mixed", "事业混合日"),
        },
        "marriage": {
            "positive": ("progress", "婚恋推进日"),
            "negative": ("risk", "婚恋风险日"),
            "mixed": ("mixed", "婚恋混合日"),
        },
        "wealth": {
            "positive": ("opportunity", "财富机会日"),
            "negative": ("risk", "财富风险日"),
            "mixed": ("mixed", "财富混合日"),
        },
    }
    positive_tokens = ("good", "support", "expansion", "gain", "auspicious", "lending", "borrowing")
    negative_tokens = ("bad", "pressure", "dosha", "obstruction", "affliction", "risk")
    route_labels = label_map.get(domain, label_map["career"])
    signals: List[Dict[str, Any]] = []
    for window in daily_windows:
        if not isinstance(window, dict):
            continue
        families = {
            str(item)
            for item in (window.get("signal_families") or [])
            if isinstance(item, str) and item
        }
        label_text = str(window.get("top_signal_label") or "").lower()
        event_ids = list(window.get("event_ids") or [])
        combined_text = " ".join(
            [label_text] + [str(item).lower() for item in event_ids if isinstance(item, str)]
        )
        positive = bool(families.intersection(positive_families.get(domain, set()))) or any(token in combined_text for token in positive_tokens)
        negative = bool(families.intersection(negative_families.get(domain, set()))) or any(token in combined_text for token in negative_tokens)
        if domain == "career":
            travel_hit = "travel" in combined_text
            building_hit = "building" in combined_text
            selling_hit = "selling" in combined_text or "sell" in combined_text
            saturn_hit = "saturn" in combined_text
            if positive and travel_hit and not negative:
                day_type, summary = route_labels["relocation_motion"]
            elif positive and not negative:
                day_type, summary = route_labels["opportunity_entry"]
            elif negative and (positive or saturn_hit or building_hit or travel_hit) and not selling_hit:
                day_type, summary = route_labels["pressure_opportunity"]
            elif negative and not positive:
                day_type, summary = route_labels["closure_risk"]
            else:
                day_type, summary = route_labels["mixed"]
        elif positive and not negative:
            day_type, summary = route_labels["positive"]
        elif negative and not positive:
            day_type, summary = route_labels["negative"]
        else:
            day_type, summary = route_labels["mixed"]
        signals.append(
            {
                "date": window.get("date"),
                "domain": window.get("domain") or domain,
                "day_type": day_type,
                "summary": summary,
                "confidence": window.get("confidence"),
                "score": window.get("score"),
                "event_count": window.get("event_count"),
                "top_signal_label": window.get("top_signal_label"),
                "signal_families": list(window.get("signal_families") or []),
                "event_ids": event_ids,
                "source": "vedastro_official_day_windows",
            }
        )
    return signals


def _external_activation_audit(external_activation: Any) -> List[Dict[str, Any]]:
    if not isinstance(external_activation, dict):
        return []
    if external_activation.get("level") == "missing_required_external_radar":
        return [
            {
                "technique": "VedAstro EventsAtRange / 596+ Calculator Radar",
                "status": "blocked",
                "role": "required_external_timing_radar",
                "effect": "confidence_boundary_only_no_score_or_label_lift",
            }
        ]
    if external_activation.get("source") == "vedastro_service_adapter_candidate":
        events = external_activation.get("events") or []
        official_day_signals = external_activation.get("official_day_signals") or []
        if (isinstance(events, list) and events) or (isinstance(official_day_signals, list) and official_day_signals):
            return [
                {
                    "technique": "VedAstro EventsAtRange / 596+ Calculator Radar",
                    "status": "used",
                    "role": "external_timing_evidence",
                    "event_count": len(events),
                    "day_signal_count": len(official_day_signals) if isinstance(official_day_signals, list) else 0,
                    "effect": "activation_context_only_guarded_score_bump",
                }
            ]
    return []


def _build_official_day_signal_summary(external_activation: Any) -> Dict[str, Any]:
    if not isinstance(external_activation, dict):
        return {"available": False, "signal_count": 0, "top_day": None, "days": []}
    signals = external_activation.get("official_day_signals")
    if not isinstance(signals, list) or not signals:
        return {"available": False, "signal_count": 0, "top_day": None, "days": []}
    return {
        "available": True,
        "signal_count": len(signals),
        "top_day": signals[0] if isinstance(signals[0], dict) else None,
        "days": [item for item in signals[:3] if isinstance(item, dict)],
        "source": "present_evidence.external_activation.official_day_signals",
    }


def _official_day_signal_rows(external_activation: Any) -> List[Dict[str, Any]]:
    if not isinstance(external_activation, dict):
        return []
    signals = external_activation.get("official_day_signals")
    if not isinstance(signals, list):
        return []
    return [item for item in signals if isinstance(item, dict)]


def _supporting_day_rows(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in signals[:3]:
        rows.append(
            {
                "date": item.get("date"),
                "summary": item.get("summary"),
                "confidence": item.get("confidence"),
                "day_type": item.get("day_type"),
                "source": item.get("source") or "vedastro_official_day_windows",
            }
        )
    return rows


def _signal_day_types(signals: List[Dict[str, Any]]) -> set[str]:
    return {
        str(item.get("day_type"))
        for item in signals
        if isinstance(item, dict) and item.get("day_type")
    }


def _signal_text_has(signals: List[Dict[str, Any]], *tokens: str) -> bool:
    normalized = tuple(str(token).lower() for token in tokens if token)
    for item in signals:
        if not isinstance(item, dict):
            continue
        parts = [str(item.get("summary") or "").lower(), str(item.get("top_signal_label") or "").lower()]
        parts.extend(str(value).lower() for value in (item.get("event_ids") or []) if isinstance(value, str))
        combined = " ".join(parts)
        if any(token in combined for token in normalized):
            return True
    return False


def _monthly_state_for_route(route: str, strict: Dict[str, Any], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    event_judgement = strict.get("event_judgement") if isinstance(strict.get("event_judgement"), dict) else {}
    stages = strict.get("adjudication_stages") if isinstance(strict.get("adjudication_stages"), dict) else {}
    secondary_context = set(event_judgement.get("secondary_context") or [])
    dominant_label = event_judgement.get("dominant_label")
    day_types = _signal_day_types(signals)
    activation_status = _safe_get(stages, "activation", "status")
    promise_status = _safe_get(stages, "promise", "status")

    if route == "career":
        if "closure_risk" in day_types and not day_types.intersection({"opportunity_entry", "relocation_motion"}):
            return {"value": "收束", "reason_codes": ["closure_risk_day_cluster"], "source": "official_day_signals"}
        if day_types.intersection({"pressure_opportunity"}) or secondary_context.intersection({"dignity_conflict", "dignity_high_friction"}):
            return {"value": "重组", "reason_codes": ["pressure_opportunity_or_dignity_friction"], "source": "strict_adjudication"}
        if day_types.intersection({"opportunity_entry", "relocation_motion"}) or dominant_label == "career_status":
            return {"value": "推进", "reason_codes": ["career_activation_with_manifestation"], "source": "strict_adjudication"}
        if promise_status == "present" and activation_status == "present":
            return {"value": "启动", "reason_codes": ["promise_and_activation_present"], "source": "strict_adjudication"}
        return {"value": "观察", "reason_codes": ["insufficient_monthly_activation"], "source": "strict_adjudication"}

    if route == "relationship":
        if "risk" in day_types and "progress" not in day_types and not dominant_label:
            return {"value": "收束", "reason_codes": ["risk_without_progress"], "source": "official_day_signals"}
        if dominant_label == "legal_marriage":
            return {"value": "推进", "reason_codes": ["legal_marriage_label_present"], "source": "strict_adjudication"}
        if "public_formalization_candidate" in secondary_context:
            return {"value": "筛选", "reason_codes": ["public_formalization_without_marriage_label"], "source": "strict_adjudication"}
        if "progress" in day_types and activation_status == "present":
            return {"value": "推进", "reason_codes": ["relationship_progress_day_supported"], "source": "official_day_signals"}
        if promise_status == "present" and activation_status == "present":
            return {"value": "启动", "reason_codes": ["relationship_promise_and_activation_present"], "source": "strict_adjudication"}
        return {"value": "观察", "reason_codes": ["insufficient_relationship_activation"], "source": "strict_adjudication"}

    if route == "finance":
        if "risk" in day_types and "opportunity" not in day_types and not dominant_label:
            return {"value": "收束", "reason_codes": ["risk_without_finance_support"], "source": "official_day_signals"}
        if dominant_label in {"income_growth", "public_wealth_status"} and "opportunity" in day_types:
            return {"value": "推进", "reason_codes": ["finance_label_plus_positive_day"], "source": "strict_adjudication"}
        if secondary_context.intersection({"avayogi_active", "ashtakavarga_wealth_friction", "sodhita_wealth_friction"}):
            return {"value": "整固", "reason_codes": ["finance_friction_requires_consolidation"], "source": "strict_adjudication"}
        if promise_status == "present" and activation_status == "present":
            return {"value": "启动", "reason_codes": ["finance_promise_and_activation_present"], "source": "strict_adjudication"}
        return {"value": "观察", "reason_codes": ["insufficient_finance_activation"], "source": "strict_adjudication"}

    return {"value": "观察", "reason_codes": ["route_not_supported"], "source": "strict_adjudication"}


def _monthly_manifestation_for_route(route: str, strict: Dict[str, Any], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    event_judgement = strict.get("event_judgement") if isinstance(strict.get("event_judgement"), dict) else {}
    secondary_context = set(event_judgement.get("secondary_context") or [])
    dominant_label = event_judgement.get("dominant_label")
    day_types = _signal_day_types(signals)

    if route == "career":
        if "relocation_motion" in day_types or _signal_text_has(signals, "travel"):
            return {"value": "迁移/异地/差旅动作", "reason_codes": ["relocation_motion_day"], "source": "official_day_signals"}
        if "opportunity_entry" in day_types:
            if secondary_context.intersection({"a10_active", "amk_active"}):
                return {"value": "项目/合作推进", "reason_codes": ["a10_or_amk_with_positive_day"], "source": "strict_adjudication"}
            return {"value": "职责/职位推进", "reason_codes": ["career_positive_day"], "source": "official_day_signals"}
        if "pressure_opportunity" in day_types:
            return {"value": "岗位/项目重组", "reason_codes": ["pressure_opportunity_day"], "source": "official_day_signals"}
        if dominant_label == "career_status":
            return {"value": "职业定位推进", "reason_codes": ["career_status_label"], "source": "strict_adjudication"}
        return {"value": "职业观察窗口", "reason_codes": ["no_manifestation_lift"], "source": "strict_adjudication"}

    if route == "relationship":
        if dominant_label == "legal_marriage":
            return {"value": "长期关系/承诺推进", "reason_codes": ["legal_marriage_label"], "source": "strict_adjudication"}
        if "public_formalization_candidate" in secondary_context:
            return {"value": "关系公开化/可见度提升", "reason_codes": ["public_formalization_candidate"], "source": "strict_adjudication"}
        if "progress" in day_types:
            return {"value": "认识/互动推进", "reason_codes": ["progress_day"], "source": "official_day_signals"}
        if "risk" in day_types:
            return {"value": "关系现实面测试", "reason_codes": ["risk_day"], "source": "official_day_signals"}
        return {"value": "关系观察/筛选", "reason_codes": ["no_manifestation_lift"], "source": "strict_adjudication"}

    if route == "finance":
        if dominant_label == "income_growth":
            return {"value": "收入增长/入账机会", "reason_codes": ["income_growth_label"], "source": "strict_adjudication"}
        if dominant_label == "public_wealth_status":
            return {"value": "项目回款/对外收入状态", "reason_codes": ["public_wealth_status_label"], "source": "strict_adjudication"}
        if _signal_text_has(signals, "borrowing", "lending", "business"):
            return {"value": "资金调度/合作现金流", "reason_codes": ["wealth_signal_text_cashflow"], "source": "official_day_signals"}
        if "risk" in day_types:
            return {"value": "支出/交易收口", "reason_codes": ["risk_day"], "source": "official_day_signals"}
        return {"value": "现金流结构观察", "reason_codes": ["no_manifestation_lift"], "source": "strict_adjudication"}

    return {"value": "观察", "reason_codes": ["route_not_supported"], "source": "strict_adjudication"}


def _monthly_friction_for_route(route: str, strict: Dict[str, Any], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    event_judgement = strict.get("event_judgement") if isinstance(strict.get("event_judgement"), dict) else {}
    secondary_context = set(event_judgement.get("secondary_context") or [])
    blocked_items = strict.get("blocked_items") if isinstance(strict.get("blocked_items"), list) else []
    day_types = _signal_day_types(signals)

    if route == "career":
        if secondary_context.intersection({"dignity_conflict", "dignity_high_friction"}):
            return {"value": "权责与结构摩擦", "reason_codes": ["dignity_conflict"], "source": "strict_adjudication"}
        if secondary_context.intersection({"virodhargala_obstruction", "kakshya_career_friction"}) or "pressure_opportunity" in day_types:
            return {"value": "执行压力伴随机会", "reason_codes": ["argala_or_kakshya_friction"], "source": "strict_adjudication"}
        if blocked_items or "vedastro_range_scan_missing" in secondary_context:
            return {"value": "时间证据不足", "reason_codes": ["external_timing_gap"], "source": "strict_adjudication"}
        return {"value": "可控结构压力", "reason_codes": ["default_career_friction"], "source": "strict_adjudication"}

    if route == "relationship":
        if secondary_context.intersection({"dignity_conflict", "dignity_high_friction"}) or "risk" in day_types:
            return {"value": "现实条件与节奏压力", "reason_codes": ["relationship_risk_or_dignity"], "source": "strict_adjudication"}
        if "virodhargala_obstruction" in secondary_context:
            return {"value": "关系推进阻力", "reason_codes": ["argala_obstruction"], "source": "strict_adjudication"}
        if "public_formalization_candidate" in secondary_context:
            return {"value": "公开化快于承诺", "reason_codes": ["public_formalization_mismatch"], "source": "strict_adjudication"}
        if blocked_items or "vedastro_range_scan_missing" in secondary_context:
            return {"value": "时间证据不足", "reason_codes": ["external_timing_gap"], "source": "strict_adjudication"}
        return {"value": "筛选与磨合成本", "reason_codes": ["default_relationship_friction"], "source": "strict_adjudication"}

    if route == "finance":
        if secondary_context.intersection({"avayogi_active", "ashtakavarga_wealth_friction", "sodhita_wealth_friction"}):
            return {"value": "现金流波动/错误决策风险", "reason_codes": ["finance_friction_signals"], "source": "strict_adjudication"}
        if "risk" in day_types:
            return {"value": "交易/回款节奏压力", "reason_codes": ["finance_risk_day"], "source": "official_day_signals"}
        if blocked_items or "vedastro_range_scan_missing" in secondary_context:
            return {"value": "时间证据不足", "reason_codes": ["external_timing_gap"], "source": "strict_adjudication"}
        return {"value": "兑现节奏与支出管理", "reason_codes": ["default_finance_friction"], "source": "strict_adjudication"}

    return {"value": "证据不足", "reason_codes": ["route_not_supported"], "source": "strict_adjudication"}


def _monthly_time_confidence(strict: Dict[str, Any], signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    stages = strict.get("adjudication_stages") if isinstance(strict.get("adjudication_stages"), dict) else {}
    promise_status = _safe_get(stages, "promise", "status")
    activation_status = _safe_get(stages, "activation", "status")
    if signals and activation_status == "present":
        return {"value": "day_supported", "reason_codes": ["official_day_signal_plus_dual_dasha"], "source": "strict_adjudication"}
    if activation_status == "present":
        return {"value": "month_supported", "reason_codes": ["dual_dasha_without_day_signal"], "source": "strict_adjudication"}
    if promise_status == "present":
        return {"value": "month_only", "reason_codes": ["promise_without_activation"], "source": "strict_adjudication"}
    return {"value": "blocked", "reason_codes": ["missing_promise_and_activation"], "source": "strict_adjudication"}


def _build_monthly_adjudication_summary(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    present = strict.get("present_evidence") if isinstance(strict, dict) else {}
    if not isinstance(present, dict):
        present = {}
    external_activation = present.get("external_activation")
    signals = _official_day_signal_rows(external_activation)
    return {
        "route": route,
        "primary_state": _monthly_state_for_route(route, strict, signals),
        "manifestation_mode": _monthly_manifestation_for_route(route, strict, signals),
        "friction_source": _monthly_friction_for_route(route, strict, signals),
        "time_confidence": _monthly_time_confidence(strict, signals),
        "supporting_days": _supporting_day_rows(signals),
        "confidence_cap": strict.get("confidence_cap"),
        "blocked_items": strict.get("blocked_items") or [],
        "conflicts": strict.get("conflicts") or [],
        "source": "strict_workflow_monthly_adjudication_v1",
    }


def _official_snapshot_audit(official_snapshot: Any) -> List[Dict[str, Any]]:
    if not isinstance(official_snapshot, dict):
        return []
    if official_snapshot.get("level") == "primary":
        return [
            {
                "technique": "VedAstro Official Full Snapshot",
                "status": "used",
                "role": "primary_raw_evidence",
                "effect": "chart_and_varga_values_take_priority_over_local_engine",
            }
        ]
    return [
        {
            "technique": "VedAstro Official Full Snapshot",
            "status": "blocked",
            "role": "primary_raw_evidence",
            "effect": "local_engine_fallback_only_with_boundary",
            "reason": official_snapshot.get("reason") or official_snapshot.get("status"),
        }
    ]


def _evidence_present(value: Any) -> bool:
    if value in (None, {}, [], ""):
        return False
    if isinstance(value, dict):
        if value.get("status") in {"blocked", "missing", "none"}:
            return False
        if value.get("level") in {"blocked", "missing", "none"}:
            return False
    return True


def _official_section_status(snapshot: Dict[str, Any], *keys: str) -> str:
    if not isinstance(snapshot, dict):
        return "blocked"
    statuses = snapshot.get("section_statuses") if isinstance(snapshot.get("section_statuses"), dict) else {}
    for key in keys:
        value = statuses.get(key)
        if value:
            return str(value)
    if snapshot.get("level") == "primary":
        return "unknown"
    return str(snapshot.get("status") or "blocked")


def _build_official_primary_evidence(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = present.get("vedastro_official_snapshot") if isinstance(present, dict) else {}
    event_status = _official_section_status(snapshot, "events_overview")
    external_activation = present.get("external_activation") if isinstance(present, dict) else {}
    if isinstance(external_activation, dict) and external_activation.get("level") == "moderate":
        event_status = "ok"

    evidence = {
        "chart_core": {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": _official_section_status(snapshot, "chart_core"),
        },
        "dasha": {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": _official_section_status(snapshot, "dasha_all"),
        },
        "event_radar": {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": event_status,
        },
    }
    if route == "relationship":
        evidence["d9"] = {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": _official_section_status(snapshot, "varga_d9", "varga_all"),
        }
    elif route == "career":
        evidence["d10"] = {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": _official_section_status(snapshot, "varga_d10", "varga_all"),
        }
    elif route == "finance":
        evidence["d2_d11"] = {
            "source": "vedastro_official",
            "role": "official_primary",
            "status": _official_section_status(snapshot, "varga_d2_d11", "varga_all"),
        }
    return evidence


def _build_local_supplemental_evidence(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "relationship":
        keys = ("upapada_lagna", "darakaraka", "narayana_current", "functional_benefic_malefic")
    elif route == "career":
        keys = ("a10_karma_pada", "amatyakaraka", "karakamsha", "narayana_current", "functional_benefic_malefic")
    elif route == "finance":
        keys = ("wealth_promise_strength", "narayana_current", "functional_benefic_malefic")
    else:
        keys = ()
    return {
        key: {
            "source": "local_module",
            "role": "required_local_supplement",
            "present": _evidence_present(present.get(key)),
        }
        for key in keys
    }


def _dedupe_ordered(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _build_fallback_and_blocked(
    route: str,
    present: Dict[str, Any],
    missing: List[str],
    official_primary_evidence: Dict[str, Any],
) -> tuple[List[str], List[str]]:
    fallback_used: List[str] = []
    blocked_items: List[str] = []
    snapshot = present.get("vedastro_official_snapshot") if isinstance(present, dict) else {}
    source_priority = present.get("source_priority") if isinstance(present, dict) else {}

    if not isinstance(snapshot, dict) or snapshot.get("level") != "primary":
        blocked_items.append("official_primary_chart_blocked")
        fallback_used.append("local_chart_fallback")
    if isinstance(source_priority, dict) and source_priority.get("mode") == "local_fallback_official_blocked":
        fallback_used.append("source_priority_local_fallback")

    event_status = ((official_primary_evidence.get("event_radar") or {}).get("status"))
    if event_status == "partial":
        blocked_items.append("official_event_radar_partial")
    elif event_status in {"blocked", "missing", "service_endpoint_not_configured", "network_execution_disabled"}:
        blocked_items.append("official_event_radar_blocked")

    for key in missing:
        blocked_items.append(f"missing_required_{key}")

    return _dedupe_ordered(fallback_used), _dedupe_ordered(blocked_items)


def _build_conflicts(route: str, present: Dict[str, Any], official_primary_evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    dignity_guardrail = present.get("dignity_guardrail") if isinstance(present, dict) else {}
    if isinstance(dignity_guardrail, dict) and dignity_guardrail.get("status") == "conflict":
        conflicts.append(
            {
                "type": "official_local_divisional_conflict",
                "primary_source": "vedastro_official",
                "supplemental_source": "local_module",
                "impact": "interpretation",
                "resolution": "keep_official_primary_and_downgrade_confidence",
                "details": {"dignity_guardrail": dignity_guardrail},
            }
        )

    event_status = ((official_primary_evidence.get("event_radar") or {}).get("status"))
    if event_status == "partial":
        conflicts.append(
            {
                "type": "official_event_radar_missing_or_partial",
                "primary_source": "vedastro_official",
                "supplemental_source": "local_module",
                "impact": "timing",
                "resolution": "keep_official_primary_and_downgrade_confidence",
                "details": {"event_radar_status": event_status, "route": route},
            }
        )

    return conflicts


def _derive_external_technique_evidence(modules: Dict[str, Any], domain: str) -> Dict[str, Any]:
    ledger = _safe_get(modules, "external_technique_evidence", "evidence_ledger")
    if not isinstance(ledger, list):
        return {
            "level": "none",
            "source": None,
            "signals": [],
            "methods": [],
            "evidence": [],
            "policy": {
                "can_change_score": False,
                "can_set_dominant_label": False,
                "can_set_payout_label": False,
            },
        }

    evidence: List[Dict[str, Any]] = []
    methods: List[str] = []
    for item in ledger:
        if not isinstance(item, dict):
            continue
        if item.get("source") != "vedastro_service_adapter_candidate":
            continue
        if item.get("operation") != "calculation_method":
            continue
        if item.get("role") != "external_technique_evidence":
            continue
        item_domain = item.get("domain") or "general"
        if item_domain not in {domain, "general"}:
            continue
        evidence.append(item)
        method = item.get("method")
        if isinstance(method, str) and method and method not in methods:
            methods.append(method)

    return {
        "level": "context_only" if evidence else "none",
        "source": "vedastro_service_adapter_candidate" if evidence else None,
        "signals": ["vedastro_external_calculation_method"] if evidence else [],
        "methods": methods,
        "evidence": evidence,
        "policy": {
            "can_change_score": False,
            "can_set_dominant_label": False,
            "can_set_payout_label": False,
        },
    }


def _external_technique_audit(external_technique: Any) -> List[Dict[str, Any]]:
    if not isinstance(external_technique, dict) or external_technique.get("level") != "context_only":
        return []
    return [
        {
            "technique": "VedAstro External Technique Evidence",
            "status": "used",
            "role": "external_evidence_only",
            "methods": external_technique.get("methods") or [],
            "effect": "secondary_context_only_no_score_or_label_lift",
        }
    ]


def _derive_functional_benefic_malefic(modules: Dict[str, Any]) -> Dict[str, Any]:
    chart = _safe_get(modules, "chart")
    ascendant = _safe_get(chart, "ascendant") if isinstance(chart, dict) else None
    if not isinstance(ascendant, dict):
        return {
            "status": "blocked",
            "ascendant": ascendant.get("sign") if isinstance(ascendant, dict) else None,
            "functional_benefics": [],
            "functional_malefics": [],
            "functional_neutrals": [],
            "yogakarakas": [],
            "owned_houses": {},
            "effect_on_confidence": "Missing chart.ascendant; functional layer blocked.",
            "source": "strict_functional_benefic_malefic_v1",
        }
    return derive_functional_benefic_malefic(ascendant.get("sign"))


def _derive_synastry_relationship_support(modules: Dict[str, Any]) -> Dict[str, Any]:
    synastry = _safe_get(modules, "synastry")
    base = {
        "level": "none",
        "source": "synastry_relationship_bridge_v1",
        "signals": [],
        "total_score": None,
        "approved": False,
    }
    if not isinstance(synastry, dict):
        return base

    try:
        total_score = float(synastry.get("total_score"))
    except (TypeError, ValueError):
        total_score = None

    approved = bool(
        synastry.get("is_approved")
        or synastry.get("is_match_approved")
    )
    signals: List[str] = []
    if approved:
        signals.append("ashtakoot_approved")
    if total_score is not None and total_score >= 27:
        signals.append("ashtakoot_high_score")
    exceptions = synastry.get("exceptions")
    if isinstance(exceptions, list):
        exception_text = " ".join(str(item).lower() for item in exceptions)
        if "mitigat" in exception_text or "exception" in exception_text:
            signals.append("exception_mitigated_match")
    additional_kutas = synastry.get("additional_kutas")
    if isinstance(additional_kutas, dict):
        def _kuta_result(value: Any) -> str | None:
            if isinstance(value, dict):
                result = value.get("result")
                return str(result).lower() if result is not None else None
            return str(value).lower() if value is not None else None

        if _kuta_result(additional_kutas.get("Mahendra")) == "good":
            signals.append("mahendra_support")
        if _kuta_result(additional_kutas.get("StreeDeergha")) == "good":
            signals.append("stree_deergha_support")
        vedha_good = _kuta_result(additional_kutas.get("Vedha")) == "good"
        bad_constellations_good = _kuta_result(additional_kutas.get("BadConstellations")) == "good"
        rajju = additional_kutas.get("Rajju")
        rajju_good = isinstance(rajju, dict) and rajju.get("result") == "good"
        if vedha_good:
            signals.append("vedha_clean")
        if rajju_good:
            signals.append("rajju_clean")
        if bad_constellations_good:
            signals.append("bad_constellations_clean")
        if vedha_good and bad_constellations_good and rajju_good:
            signals.append("kuta_exception_clean")

    if approved and total_score is not None and total_score >= 27:
        level = "supportive"
    elif approved or (total_score is not None and total_score >= 24):
        level = "moderate"
    else:
        level = "none"

    base.update(
        {
            "level": level,
            "signals": signals,
            "total_score": total_score,
            "approved": approved,
        }
    )
    return base


def _derive_argala_support(modules: Dict[str, Any], target_house: int) -> Dict[str, Any]:
    house_data = _safe_get(modules, "argala", "houses", f"house_{target_house}")
    if not isinstance(house_data, dict):
        return {
            "level": "none",
            "target_house": target_house,
            "source": "argala_house_bridge_v1",
            "signals": [],
            "raw": None,
        }

    net_result = house_data.get("net_result")
    if net_result == "supported":
        level = "supportive"
        signals = ["argala_support"]
    elif net_result == "obstructed":
        level = "obstructive"
        signals = ["virodhargala_obstruction"]
    else:
        level = "none"
        signals = []

    return {
        "level": level,
        "target_house": target_house,
        "source": "argala_house_bridge_v1",
        "signals": signals,
        "raw": {
            "net_result": net_result,
            "argala_count": house_data.get("argala_count"),
            "virodhargala_count": house_data.get("virodhargala_count"),
        },
    }


def _extract_house_score_value(score: Any) -> Optional[float]:
    if isinstance(score, dict):
        for key in ("sav", "score", "total", "bindus"):
            if key in score:
                try:
                    return float(score[key])
                except (TypeError, ValueError):
                    return None
        return None
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _derive_ashtakavarga_finance_support(house_scores: Any) -> Dict[str, Any]:
    if not isinstance(house_scores, dict):
        return {
            "level": "none",
            "source": "ashtakavarga_house_scores_bridge_v1",
            "target_houses": [2, 11],
            "signals": [],
            "raw_scores": {},
        }

    raw_scores: Dict[str, Any] = {}
    numeric_scores: Dict[str, float] = {}
    for house in ("2", "11"):
        value = house_scores.get(house) or house_scores.get(f"house_{house}")
        score = _extract_house_score_value(value)
        if score is None:
            continue
        numeric_scores[house] = score
        raw_scores[house] = int(score) if score.is_integer() else score

    if len(numeric_scores) < 2:
        level = "none"
        signals: List[str] = []
    elif min(numeric_scores.values()) >= 32:
        level = "supportive"
        signals = ["wealth_sav_support"]
    elif max(numeric_scores.values()) <= 24:
        level = "obstructive"
        signals = ["wealth_sav_low"]
    else:
        level = "none"
        signals = []

    return {
        "level": level,
        "source": "ashtakavarga_house_scores_bridge_v1",
        "target_houses": [2, 11],
        "signals": signals,
        "raw_scores": raw_scores,
    }


def _derive_shadbala_component_audit(planets: Any) -> Dict[str, Any]:
    audit = {
        "status": "blocked",
        "source": "shadbala.planets",
        "required_components": _SHADBALA_REQUIRED_COMPONENTS,
        "missing": {},
    }
    if not isinstance(planets, dict) or not planets:
        return audit

    missing: Dict[str, List[str]] = {}
    for planet, pdata in planets.items():
        if not isinstance(pdata, dict):
            missing[str(planet)] = list(_SHADBALA_REQUIRED_COMPONENTS)
            continue
        components = pdata.get("components") if isinstance(pdata.get("components"), dict) else pdata
        planet_missing = [
            component for component in _SHADBALA_REQUIRED_COMPONENTS
            if components.get(component) in (None, "", [], {})
        ]
        if planet_missing:
            missing[str(planet)] = planet_missing

    audit["missing"] = missing
    audit["status"] = "complete" if not missing else "incomplete"
    return audit


def _derive_pav_finance_support(ashtakavarga: Any) -> Dict[str, Any]:
    base = {
        "level": "none",
        "source": "ashtakavarga_pav_bridge_v1",
        "signals": [],
        "top_planets": [],
    }
    pav_summary = _safe_get(ashtakavarga, "pav", "pav_summary")
    if not isinstance(pav_summary, dict):
        return base

    top_planets: List[str] = []
    for planet, source_scores in pav_summary.items():
        if not isinstance(source_scores, dict):
            continue
        high_sources = [
            source for source, bindus in source_scores.items()
            if isinstance(bindus, (int, float)) and bindus >= 5
        ]
        if high_sources:
            top_planets.append(str(planet))

    if top_planets:
        base["level"] = "supportive"
        base["signals"] = ["pav_finance_support"]
        base["top_planets"] = sorted(top_planets)
    return base


def _derive_sodhita_finance_support(ashtakavarga: Any, asc_sign: Optional[str]) -> Dict[str, Any]:
    base = {
        "level": "none",
        "source": "ashtakavarga_sodhita_bridge_v1",
        "signals": [],
        "target_houses": [2, 11],
        "raw_scores": {},
    }
    assessment = _safe_get(ashtakavarga, "sodhita", "sodhita_sav", "assessment")
    asc_idx = _SIGN_TO_INDEX.get(asc_sign) if asc_sign else None
    if not isinstance(assessment, list) or asc_idx is None:
        return base

    sign_to_score: Dict[str, float] = {}
    for row in assessment:
        if not isinstance(row, dict):
            continue
        sign = row.get("sign")
        score = row.get("score")
        if sign in _SIGN_TO_INDEX and isinstance(score, (int, float)):
            sign_to_score[str(sign)] = float(score)

    raw_scores: Dict[str, Any] = {}
    numeric_scores: Dict[int, float] = {}
    for house in (2, 11):
        sign = _SIGNS[(asc_idx + house - 1) % 12]
        if sign in sign_to_score:
            numeric_scores[house] = sign_to_score[sign]
            value = sign_to_score[sign]
            raw_scores[str(house)] = int(value) if value.is_integer() else value

    base["raw_scores"] = raw_scores
    if len(numeric_scores) == 2 and max(numeric_scores.values()) <= 19:
        base["level"] = "obstructive"
        base["signals"] = ["sodhita_wealth_friction"]
    return base


def _derive_kakshya_finance_support(kakshya: Any) -> Dict[str, Any]:
    base = {
        "level": "none",
        "source": "kakshya_finance_bridge_v1",
        "signals": [],
        "average_strength": None,
    }
    avg = _safe_get(kakshya, "summary", "average_strength")
    if not isinstance(avg, (int, float)):
        return base
    base["average_strength"] = float(avg)
    if avg >= 6.5:
        base["level"] = "supportive"
        base["signals"] = ["kakshya_finance_support"]
    elif avg <= 4.5:
        base["level"] = "obstructive"
        base["signals"] = ["kakshya_finance_friction"]
    return base


def _derive_kakshya_career_support(kakshya: Any) -> Dict[str, Any]:
    base = {
        "level": "none",
        "source": "kakshya_career_bridge_v1",
        "signals": [],
        "average_strength": None,
    }
    avg = _safe_get(kakshya, "summary", "average_strength")
    if not isinstance(avg, (int, float)):
        return base
    base["average_strength"] = float(avg)
    if avg >= 6.5:
        base["level"] = "supportive"
        base["signals"] = ["kakshya_career_support"]
    elif avg <= 4.5:
        base["level"] = "obstructive"
        base["signals"] = ["kakshya_career_friction"]
    return base


def _sign_to_index(sign: str) -> Optional[int]:
    try:
        return _SIGNS.index(sign)
    except ValueError:
        return None


def _lord_for_house_from_lagna(asc_sign: Optional[str], house_num: int) -> Optional[str]:
    asc_idx = _sign_to_index(asc_sign) if asc_sign else None
    if asc_idx is None:
        return None
    sign = _SIGNS[(asc_idx + house_num - 1) % 12]
    return _SIGN_LORDS.get(sign)


def _extract_dignity_code(status: str) -> Optional[str]:
    if "Neecha Bhanga" in status or "落陷取消" in status:
        return "NEECHA_BHANGA"
    if "Great Friend" in status or "极友" in status:
        return "GREAT_FRIEND"
    if "Great Enemy" in status or "极敌" in status:
        return "GREAT_ENEMY"
    return None


def _derive_dignity_guardrail(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    base = {
        "route": route,
        "status": "blocked",
        "score_delta": 0,
        "source": "chart.planets.status",
        "relevant_planets": [],
        "ignored_planets": [],
        "conflict_flags": [],
        "notes": ["Only domain-relevant planets are allowed to affect score."],
    }

    chart = present.get("chart") if isinstance(present.get("chart"), dict) else {}
    ascendant = chart.get("ascendant") if isinstance(chart.get("ascendant"), dict) else {}
    planets = chart.get("planets") if isinstance(chart.get("planets"), dict) else {}
    asc_sign = ascendant.get("sign")

    if not asc_sign or not isinstance(planets, dict) or not planets:
        return base

    relevant_roles: Dict[str, str] = {}

    if route == "relationship":
        lord_7 = _lord_for_house_from_lagna(asc_sign, 7)
        if not lord_7:
            return base
        relevant_roles[lord_7] = "7l"
        relevant_roles["Venus"] = "relationship_karaka"
        relevant_roles["Jupiter"] = "relationship_support"
        darakaraka = present.get("darakaraka")
        if isinstance(darakaraka, dict) and darakaraka.get("planet"):
            relevant_roles[darakaraka["planet"]] = "darakaraka"
    elif route == "career":
        lord_10 = _lord_for_house_from_lagna(asc_sign, 10)
        if not lord_10:
            return base
        relevant_roles[lord_10] = "10l"
        a10 = present.get("a10_karma_pada")
        if isinstance(a10, dict) and a10.get("lord"):
            relevant_roles[str(a10["lord"])] = "a10_lord"
        amatyakaraka = present.get("amatyakaraka")
        if isinstance(amatyakaraka, dict) and amatyakaraka.get("planet"):
            relevant_roles[str(amatyakaraka["planet"])] = "amatyakaraka"
        karakamsha = present.get("karakamsha")
        if isinstance(karakamsha, dict) and karakamsha.get("karakamsha_lord"):
            relevant_roles[str(karakamsha["karakamsha_lord"])] = "karakamsha_lord"
        vimshottari = present.get("vimshottari_current")
        if isinstance(vimshottari, dict):
            if vimshottari.get("mahadasha"):
                relevant_roles[str(vimshottari["mahadasha"])] = "mahadasha_lord"
            antardasha = vimshottari.get("antardasha")
            if isinstance(antardasha, dict) and antardasha.get("lord"):
                relevant_roles[str(antardasha["lord"])] = "antardasha_lord"
            elif isinstance(antardasha, str) and antardasha:
                relevant_roles[antardasha] = "antardasha_lord"
            elif vimshottari.get("lord"):
                relevant_roles[str(vimshottari["lord"])] = "mahadasha_lord"
        narayana = present.get("narayana_current")
        if isinstance(narayana, dict) and narayana.get("lord"):
            relevant_roles[str(narayana["lord"])] = "narayana_lord"
    elif route == "finance":
        lord_2 = _lord_for_house_from_lagna(asc_sign, 2)
        lord_11 = _lord_for_house_from_lagna(asc_sign, 11)
        if not lord_2 or not lord_11:
            return base
        relevant_roles[lord_2] = "2l"
        relevant_roles[lord_11] = "11l"
        relevant_roles["Venus"] = "finance_karaka"
        relevant_roles["Jupiter"] = "finance_support"
        if present.get("career_convergence"):
            lord_10 = _lord_for_house_from_lagna(asc_sign, 10)
            if lord_10:
                relevant_roles[lord_10] = "10l_career_monetization"
    else:
        base["status"] = "ok"
        return base

    supportive_hits: List[str] = []
    supportive_friend_hits: List[str] = []
    friction_hits: List[str] = []

    for planet_name, pdata in planets.items():
        if planet_name not in relevant_roles:
            base["ignored_planets"].append({
                "planet": planet_name,
                "reason": "not_domain_relevant",
            })
            continue
        if not isinstance(pdata, dict):
            return base
        status = str(pdata.get("status", ""))
        if not status:
            return base
        dignity_code = _extract_dignity_code(status)
        effect = (
            "supportive_recovery" if dignity_code == "NEECHA_BHANGA"
            else "supportive_friendship" if dignity_code == "GREAT_FRIEND"
            else "high_friction" if dignity_code == "GREAT_ENEMY"
            else "none"
        )
        base["relevant_planets"].append({
            "planet": planet_name,
            "role": relevant_roles[planet_name],
            "status": status,
            "dignity_code": dignity_code,
            "effect": effect,
        })
        if dignity_code == "NEECHA_BHANGA":
            supportive_hits.append(planet_name)
        elif dignity_code == "GREAT_FRIEND":
            supportive_friend_hits.append(planet_name)
        elif dignity_code == "GREAT_ENEMY":
            friction_hits.append(planet_name)

    if supportive_hits and friction_hits:
        base["status"] = "conflict"
        base["conflict_flags"] = [
            "neecha_bhanga_on_key_significator",
            "great_enemy_on_key_significator",
        ]
        base["score_delta"] = 0
    elif supportive_hits:
        base["status"] = "caution"
        base["score_delta"] = 5
    elif supportive_friend_hits and friction_hits:
        base["status"] = "conflict"
        base["conflict_flags"] = [
            "great_friend_on_key_significator",
            "great_enemy_on_key_significator",
        ]
        base["score_delta"] = 0
    elif supportive_friend_hits:
        base["status"] = "caution"
        base["score_delta"] = 3
    elif friction_hits:
        base["status"] = "caution"
        base["score_delta"] = -5
    else:
        base["status"] = "ok"
        base["score_delta"] = 0

    return base


def _derive_event_judgement(route: str, present: Dict[str, Any], missing: List[str]) -> Dict[str, Any]:
    if route == "career":
        score = 0
        score += 20 if present.get("d10_dasamsa") else 0
        score += 15 if present.get("a10_karma_pada") else 0
        score += 15 if present.get("amatyakaraka") else 0
        score += 10 if present.get("karakamsha") else 0
        score += 10 if present.get("vimshottari_current") else 0
        score += 10 if present.get("narayana_current") else 0
        score += _convergence_score(present.get("career_convergence"))
        dignity_guardrail = present.get("dignity_guardrail") or {}
        score += dignity_guardrail.get("score_delta", 0)
        kakshya_career_support = present.get("kakshya_career_support") or {}
        if kakshya_career_support.get("level") == "supportive":
            score += 2
        elif kakshya_career_support.get("level") == "obstructive":
            score -= 2
        argala_support = present.get("argala_support") or {}
        if argala_support.get("level") == "supportive":
            score += 5
        elif argala_support.get("level") == "obstructive":
            score -= 5
        external_activation = present.get("external_activation") or {}
        if external_activation.get("level") == "moderate":
            score += 5
        if missing:
            score = min(score, 35)
        score = min(score, 100)

        if missing:
            verdict = "insufficient_evidence"
        elif score >= 80:
            verdict = "high_probability_window"
        elif score >= 60:
            verdict = "moderate_probability_window"
        elif score >= 40:
            verdict = "weak_window_needs_confirmation"
        else:
            verdict = "insufficient_evidence"

        secondary_context: List[str] = []
        if present.get("a10_karma_pada"):
            secondary_context.append("a10_active")
        if present.get("amatyakaraka"):
            secondary_context.append("amk_active")
        if present.get("karakamsha"):
            secondary_context.append("karakamsha_context")
        shadbala_component_audit = present.get("shadbala_component_audit") or {}
        if shadbala_component_audit.get("status") in {"blocked", "incomplete"}:
            secondary_context.append("shadbala_component_gap")
        functional_layer = present.get("functional_benefic_malefic") or {}
        if functional_layer.get("status") == "used":
            secondary_context.append("functional_benefic_malefic_used")
        if kakshya_career_support.get("level") == "supportive":
            secondary_context.append("kakshya_career_support")
        elif kakshya_career_support.get("level") == "obstructive":
            secondary_context.append("kakshya_career_friction")
        if argala_support.get("level") == "supportive":
            secondary_context.append("argala_support")
        elif argala_support.get("level") == "obstructive":
            secondary_context.append("virodhargala_obstruction")
        if external_activation.get("level") == "moderate":
            secondary_context.append("external_activation_support")
        elif external_activation.get("level") == "missing_required_external_radar":
            secondary_context.append("vedastro_range_scan_missing")
        external_technique = present.get("external_technique_evidence") or {}
        if external_technique.get("level") == "context_only":
            secondary_context.append("external_technique_evidence")
        if dignity_guardrail.get("status") == "conflict":
            secondary_context.append("dignity_conflict")
        elif dignity_guardrail.get("score_delta") == 5:
            secondary_context.append("dignity_supportive_recovery")
        elif dignity_guardrail.get("score_delta") == 3:
            secondary_context.append("dignity_supportive_friendship")
        elif dignity_guardrail.get("score_delta") == -5:
            secondary_context.append("dignity_high_friction")

        hard_gate_missing = any(
            key in missing for key in (
                "d10_dasamsa",
                "a10_karma_pada",
                "vimshottari_current",
                "narayana_current",
            )
        )
        dominant_label = None
        if not hard_gate_missing and present.get("career_convergence") and score >= 60:
            dominant_label = "career_status"

        return {
            "event_family": "career",
            "score": score,
            "verdict": verdict,
            "dominant_label": dominant_label,
            "secondary_context": secondary_context,
            "primary_drivers": [
                key for key in (
                    "career_convergence",
                    "vimshottari_current",
                    "narayana_current",
                    "a10_karma_pada",
                    "amatyakaraka",
                    "karakamsha",
                    "argala_support",
                )
                if present.get(key)
            ],
        }

    if route == "relationship":
        score = 0
        score += 15 if present.get("d9_navamsa") else 0
        score += 15 if present.get("upapada_lagna") else 0
        score += 15 if present.get("darakaraka") else 0
        score += 10 if present.get("vivah_saham") else 0
        score += 10 if present.get("vimshottari_current") else 0
        score += 10 if present.get("narayana_current") else 0
        score += _convergence_score(present.get("marriage_convergence"))
        dignity_guardrail = present.get("dignity_guardrail") or {}
        score += dignity_guardrail.get("score_delta", 0)
        synastry_support = present.get("synastry_relationship_support") or {}
        if synastry_support.get("level") == "supportive":
            score += 5
        argala_support = present.get("argala_support") or {}
        if argala_support.get("level") == "supportive":
            score += 5
        elif argala_support.get("level") == "obstructive":
            score -= 5
        if missing:
            score = min(score, 35)
        score = min(score, 100)
        if missing:
            verdict = "insufficient_evidence"
        elif score >= 80:
            verdict = "high_probability_window"
        elif score >= 60:
            verdict = "moderate_probability_window"
        elif score >= 40:
            verdict = "weak_window_needs_confirmation"
        else:
            verdict = "insufficient_evidence"
        jaimini_support = present.get("jaimini_marriage_support") or {}
        secondary_context: List[str] = []
        if present.get("darakaraka"):
            secondary_context.append("darakaraka_active")
        if jaimini_support.get("level") == "moderate":
            secondary_context.append("jaimini_support")
        if present.get("upapada_lagna"):
            secondary_context.append("ul_support")
        synastry_level = synastry_support.get("level")
        if synastry_level in {"supportive", "moderate"}:
            secondary_context.append("synastry_support")
        synastry_signals = synastry_support.get("signals") or []
        if synastry_level in {"supportive", "moderate"} and any(
            signal in synastry_signals for signal in ("mahendra_support", "stree_deergha_support")
        ):
            secondary_context.append("synastry_compatibility_support")
        if synastry_level in {"supportive", "moderate"} and any(
            signal in synastry_signals for signal in ("vedha_clean", "rajju_clean", "bad_constellations_clean")
        ):
            secondary_context.append("synastry_protective_kuta_support")
        if synastry_level in {"supportive", "moderate"} and "exception_mitigated_match" in synastry_signals:
            secondary_context.append("synastry_exception_mitigated")
        if synastry_level in {"supportive", "moderate"} and "kuta_exception_clean" in synastry_signals:
            secondary_context.append("synastry_kuta_exception_clean")
        if synastry_level in {"supportive", "moderate"} and "mahendra_support" in synastry_signals:
            secondary_context.append("mahendra_support")
        if synastry_level in {"supportive", "moderate"} and "stree_deergha_support" in synastry_signals:
            secondary_context.append("stree_deergha_support")
        if synastry_level in {"supportive", "moderate"} and "vedha_clean" in synastry_signals:
            secondary_context.append("vedha_clean")
        if synastry_level in {"supportive", "moderate"} and "rajju_clean" in synastry_signals:
            secondary_context.append("rajju_clean")
        if synastry_level in {"supportive", "moderate"} and "bad_constellations_clean" in synastry_signals:
            secondary_context.append("bad_constellations_clean")
        shadbala_component_audit = present.get("shadbala_component_audit") or {}
        if shadbala_component_audit.get("status") in {"blocked", "incomplete"}:
            secondary_context.append("shadbala_component_gap")
        functional_layer = present.get("functional_benefic_malefic") or {}
        if functional_layer.get("status") == "used":
            secondary_context.append("functional_benefic_malefic_used")
        if argala_support.get("level") == "supportive":
            secondary_context.append("argala_support")
        elif argala_support.get("level") == "obstructive":
            secondary_context.append("virodhargala_obstruction")
        external_activation = present.get("external_activation") or {}
        if external_activation.get("level") == "moderate":
            secondary_context.append("external_activation_support")
        elif external_activation.get("level") == "missing_required_external_radar":
            secondary_context.append("vedastro_range_scan_missing")
        external_technique = present.get("external_technique_evidence") or {}
        if external_technique.get("level") == "context_only":
            secondary_context.append("external_technique_evidence")
        if dignity_guardrail.get("status") == "conflict":
            secondary_context.append("dignity_conflict")
        elif dignity_guardrail.get("score_delta") == 5:
            secondary_context.append("dignity_supportive_recovery")
        elif dignity_guardrail.get("score_delta") == 3:
            secondary_context.append("dignity_supportive_friendship")
        elif dignity_guardrail.get("score_delta") == -5:
            secondary_context.append("dignity_high_friction")

        hard_gate_missing = any(
            key in missing for key in (
                "d9_navamsa",
                "upapada_lagna",
                "vimshottari_current",
                "narayana_current",
            )
        )
        label_support_present = bool(present.get("vivah_saham") or present.get("marriage_convergence"))
        dominant_label = None
        if (
            not hard_gate_missing
            and label_support_present
            and jaimini_support.get("level") == "moderate"
        ):
            dominant_label = "legal_marriage"
        elif (
            not hard_gate_missing
            and not label_support_present
            and jaimini_support.get("level") == "moderate"
            and external_activation.get("level") == "moderate"
        ):
            secondary_context.append("public_formalization_candidate")
        return {
            "event_family": "relationship",
            "score": score,
            "verdict": verdict,
            "dominant_label": dominant_label,
            "secondary_context": secondary_context,
            "primary_drivers": [
                key for key in (
                    "marriage_convergence",
                    "vimshottari_current",
                    "narayana_current",
                    "darakaraka",
                    "upapada_lagna",
                    "synastry_relationship_support",
                    "argala_support",
                )
                if present.get(key)
            ],
        }

    if route == "finance":
        score = 0
        wealth_promise = present.get("wealth_promise_strength")
        wealth_promise_level = wealth_promise.get("level") if isinstance(wealth_promise, dict) else None
        wealth_promise_diversity = wealth_promise.get("source_diversity", 0) if isinstance(wealth_promise, dict) else 0
        avayogi_risk = present.get("avayogi_risk")
        score += 15 if present.get("d2_hora") else 0
        score += 10 if present.get("d10_dasamsa") else 0
        score += 10 if present.get("shadbala") else 0
        score += 10 if present.get("ashtakavarga_house_scores") else 0
        score += 10 if present.get("vimshottari_current") else 0
        score += 10 if present.get("narayana_current") else 0
        ashtakavarga_finance = present.get("ashtakavarga_finance_support") or {}
        if ashtakavarga_finance.get("level") == "supportive":
            score += 5
        elif ashtakavarga_finance.get("level") == "obstructive":
            score -= 5
        pav_finance_support = present.get("pav_finance_support") or {}
        if pav_finance_support.get("level") == "supportive":
            score += 2
        sodhita_finance_support = present.get("sodhita_finance_support") or {}
        if sodhita_finance_support.get("level") == "obstructive":
            score -= 2
        kakshya_finance_support = present.get("kakshya_finance_support") or {}
        if kakshya_finance_support.get("level") == "supportive":
            score += 2
        elif kakshya_finance_support.get("level") == "obstructive":
            score -= 2
        score += 20 if wealth_promise_level == "strong" else 10 if wealth_promise_level == "moderate" else 0
        score += 5 if wealth_promise_diversity >= 2 else 0
        score += max(
            _convergence_score(present.get("wealth_convergence")),
            _convergence_score(present.get("gains_convergence")),
            _convergence_score(present.get("career_convergence")),
        )
        dignity_guardrail = present.get("dignity_guardrail") or {}
        score += dignity_guardrail.get("score_delta", 0)
        score -= 5 if isinstance(avayogi_risk, dict) and avayogi_risk.get("risk_level") == "moderate" else 0
        public_wealth_lift = (
            not missing
            and bool(present.get("wealth_convergence"))
            and (
                bool(present.get("gains_convergence"))
                or bool(present.get("career_convergence"))
            )
            and bool(present.get("vimshottari_current"))
            and bool(present.get("narayana_current"))
        )
        if missing:
            score = min(score, 35)
        score = min(score, 100)
        if missing:
            verdict = "insufficient_evidence"
        elif public_wealth_lift and score >= 60:
            verdict = "moderate_probability_window"
        elif score >= 80:
            verdict = "high_probability_window"
        elif score >= 60:
            verdict = "moderate_probability_window"
        elif score >= 40:
            verdict = "weak_window_needs_confirmation"
        else:
            verdict = "insufficient_evidence"
        payout_label = None
        dominant_label = None
        secondary_context: List[str] = []
        gains_score = _convergence_score(present.get("gains_convergence"))
        wealth_score = _convergence_score(present.get("wealth_convergence"))
        career_score = _convergence_score(present.get("career_convergence"))
        if gains_score >= 60 and wealth_score < 40 and career_score < 40:
            payout_label = "income_growth"
            dominant_label = "income_growth"
            secondary_context = ["wealth_family"] if present.get("wealth_convergence") else []
        elif public_wealth_lift and score >= 60:
            payout_label = "public_wealth_status"
            dominant_label = "public_wealth_status"
            if present.get("career_convergence"):
                secondary_context.append("career_status")
            if present.get("gains_convergence"):
                secondary_context.append("gains_wishes")
        if isinstance(avayogi_risk, dict) and avayogi_risk.get("risk_level") == "moderate":
            secondary_context.append("avayogi_active")
        shadbala_component_audit = present.get("shadbala_component_audit") or {}
        if shadbala_component_audit.get("status") in {"blocked", "incomplete"}:
            secondary_context.append("shadbala_component_gap")
        functional_layer = present.get("functional_benefic_malefic") or {}
        if functional_layer.get("status") == "used":
            secondary_context.append("functional_benefic_malefic_used")
        if pav_finance_support.get("level") == "supportive":
            secondary_context.append("pav_finance_support")
        if sodhita_finance_support.get("level") == "obstructive":
            secondary_context.append("sodhita_wealth_friction")
        if kakshya_finance_support.get("level") == "supportive":
            secondary_context.append("kakshya_finance_support")
        elif kakshya_finance_support.get("level") == "obstructive":
            secondary_context.append("kakshya_finance_friction")
        if ashtakavarga_finance.get("level") == "supportive":
            secondary_context.append("ashtakavarga_wealth_support")
        elif ashtakavarga_finance.get("level") == "obstructive":
            secondary_context.append("ashtakavarga_wealth_friction")
        external_activation = present.get("external_activation") or {}
        if external_activation.get("level") == "moderate":
            secondary_context.append("external_activation_support")
        elif external_activation.get("level") == "missing_required_external_radar":
            secondary_context.append("vedastro_range_scan_missing")
        external_technique = present.get("external_technique_evidence") or {}
        if external_technique.get("level") == "context_only":
            secondary_context.append("external_technique_evidence")
        if dignity_guardrail.get("status") == "conflict":
            secondary_context.append("dignity_conflict")
        elif dignity_guardrail.get("score_delta") == 5:
            secondary_context.append("dignity_supportive_recovery")
        elif dignity_guardrail.get("score_delta") == 3:
            secondary_context.append("dignity_supportive_friendship")
        elif dignity_guardrail.get("score_delta") == -5:
            secondary_context.append("dignity_high_friction")
        return {
            "event_family": "finance",
            "score": score,
            "verdict": verdict,
            "payout_label": payout_label,
            "dominant_label": dominant_label,
            "secondary_context": secondary_context,
            "primary_drivers": [
                key for key in (
                    "wealth_convergence",
                    "gains_convergence",
                    "career_convergence",
                    "vimshottari_current",
                    "narayana_current",
                )
                if present.get(key)
            ],
        }

    return {
        "event_family": route,
        "score": 0,
        "verdict": "context_only",
        "primary_drivers": [],
    }


def _has_promise_evidence(route: str, present: Dict[str, Any]) -> bool:
    if route == "career":
        return bool(
            present.get("d10_dasamsa")
            or present.get("a10_karma_pada")
            or present.get("amatyakaraka")
            or present.get("karakamsha")
        )
    if route == "relationship":
        return bool(
            present.get("d9_navamsa")
            or present.get("upapada_lagna")
            or present.get("darakaraka")
            or present.get("vivah_saham")
        )
    if route == "finance":
        return bool(
            present.get("d2_hora")
            or present.get("d10_dasamsa")
            or present.get("wealth_promise_strength")
            or present.get("ashtakavarga_house_scores")
        )
    return False


def _has_activation_evidence(route: str, present: Dict[str, Any]) -> bool:
    if route == "career":
        return bool(
            present.get("vimshottari_current")
            and present.get("narayana_current")
            and present.get("career_convergence")
        )
    if route == "relationship":
        return bool(
            present.get("vimshottari_current")
            and present.get("narayana_current")
            and (
                present.get("marriage_convergence")
                or (present.get("external_activation") or {}).get("level") == "moderate"
            )
        )
    if route == "finance":
        return bool(
            present.get("vimshottari_current")
            and present.get("narayana_current")
            and (
                present.get("wealth_convergence")
                or present.get("gains_convergence")
                or present.get("career_convergence")
            )
        )
    return False


def _promise_drivers(route: str, present: Dict[str, Any]) -> List[str]:
    by_route = {
        "career": ("d10_dasamsa", "a10_karma_pada", "amatyakaraka", "karakamsha"),
        "relationship": ("d9_navamsa", "upapada_lagna", "darakaraka", "vivah_saham"),
        "finance": ("d2_hora", "d10_dasamsa", "wealth_promise_strength", "ashtakavarga_house_scores"),
    }
    return [key for key in by_route.get(route, ()) if present.get(key)]


def _activation_drivers(route: str, present: Dict[str, Any]) -> List[str]:
    by_route = {
        "career": ("vimshottari_current", "narayana_current", "career_convergence", "external_activation"),
        "relationship": ("vimshottari_current", "narayana_current", "marriage_convergence", "external_activation"),
        "finance": ("vimshottari_current", "narayana_current", "wealth_convergence", "gains_convergence", "career_convergence", "external_activation"),
    }
    return [key for key in by_route.get(route, ()) if present.get(key)]


def _summary_root_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "career":
        return {
            "promise_drivers": [key for key in ("a10_karma_pada", "amatyakaraka", "karakamsha") if present.get(key)],
        }
    if route == "relationship":
        return {
            "promise_drivers": [key for key in ("upapada_lagna", "darakaraka", "vivah_saham") if present.get(key)],
        }
    if route == "finance":
        return {
            "promise_drivers": [key for key in ("wealth_promise_strength", "d2_hora", "ashtakavarga_house_scores") if present.get(key)],
        }
    return {}


def _summary_divisional_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "career":
        return {"d10_dasamsa": present.get("d10_dasamsa")}
    if route == "relationship":
        return {"d9_navamsa": present.get("d9_navamsa")}
    if route == "finance":
        return {
            "d2_hora": present.get("d2_hora"),
            "d10_dasamsa": present.get("d10_dasamsa"),
        }
    return {}


def _summary_visibility_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "career":
        return {"a10_karma_pada": present.get("a10_karma_pada")}
    if route == "relationship":
        return {"upapada_lagna": present.get("upapada_lagna")}
    if route == "finance":
        return {"wealth_promise_strength": present.get("wealth_promise_strength")}
    return {}


def _summary_karaka_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    if route == "career":
        return {
            "amatyakaraka": present.get("amatyakaraka"),
            "karakamsha": present.get("karakamsha"),
        }
    if route == "relationship":
        return {
            "darakaraka": present.get("darakaraka"),
        }
    return {}


def _summary_timing_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    frame = {
        "vimshottari_current": present.get("vimshottari_current"),
        "narayana_current": present.get("narayana_current"),
    }
    if route == "career":
        frame["domain_convergence"] = present.get("career_convergence")
    elif route == "relationship":
        frame["domain_convergence"] = present.get("marriage_convergence")
    elif route == "finance":
        frame["domain_convergence"] = {
            "wealth_convergence": present.get("wealth_convergence"),
            "gains_convergence": present.get("gains_convergence"),
            "career_convergence": present.get("career_convergence"),
        }
    if present.get("external_activation"):
        frame["external_activation"] = present.get("external_activation")
    return frame


def _summary_modifier_frame(route: str, present: Dict[str, Any]) -> Dict[str, Any]:
    frame: Dict[str, Any] = {
        "functional_benefic_malefic": present.get("functional_benefic_malefic"),
        "shadbala_component_audit": present.get("shadbala_component_audit"),
        "argala_support": present.get("argala_support"),
    }
    if route == "career":
        frame["kakshya_career_support"] = present.get("kakshya_career_support")
    elif route == "relationship":
        frame["manifestation_split"] = {
            "role": "modifier_only",
            "signals": [
                "relationship_formation",
                "legal_marriage",
                "public_formalization",
            ],
        }
        frame["synastry_relationship_support"] = present.get("synastry_relationship_support")
        frame["dignity_guardrail"] = present.get("dignity_guardrail")
    elif route == "finance":
        frame["ashtakavarga_finance_support"] = present.get("ashtakavarga_finance_support")
        frame["pav_finance_support"] = present.get("pav_finance_support")
        frame["sodhita_finance_support"] = present.get("sodhita_finance_support")
        frame["kakshya_finance_support"] = present.get("kakshya_finance_support")
        frame["yogi_support"] = {
            "role": "modifier_only",
            "value": present.get("wealth_promise_strength"),
        }
        frame["dignity_guardrail"] = present.get("dignity_guardrail")
    return frame


def _route_varga_gate_keys(route: str) -> List[str]:
    if route == "career":
        return ["d10_dasamsa", "a10_karma_pada", "amatyakaraka", "karakamsha"]
    if route == "relationship":
        return ["d9_navamsa", "upapada_lagna", "darakaraka", "vivah_saham"]
    if route == "finance":
        return ["d2_hora", "d10_dasamsa", "shadbala", "ashtakavarga_house_scores"]
    return []


def _build_technique_audit_summary(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    present = strict.get("present_evidence") if isinstance(strict, dict) else {}
    official = strict.get("official_primary_evidence") if isinstance(strict, dict) else {}
    local = strict.get("local_supplemental_evidence") if isinstance(strict, dict) else {}
    fallback_used = strict.get("fallback_used") if isinstance(strict, dict) else []
    blocked_items = strict.get("blocked_items") if isinstance(strict, dict) else []
    conflicts = strict.get("conflicts") if isinstance(strict, dict) else []
    if not isinstance(present, dict):
        present = {}
    if not isinstance(official, dict):
        official = {}
    if not isinstance(local, dict):
        local = {}
    if not isinstance(fallback_used, list):
        fallback_used = []
    if not isinstance(blocked_items, list):
        blocked_items = []
    if not isinstance(conflicts, list):
        conflicts = []

    varga_keys = _route_varga_gate_keys(route)
    functional_layer = present.get("functional_benefic_malefic")
    interpretation_source_pack = present.get("interpretation_source_pack")
    if not isinstance(interpretation_source_pack, dict):
        interpretation_source_pack = {}
    mevg_gate = interpretation_source_pack.get("mevg_gate") if isinstance(interpretation_source_pack.get("mevg_gate"), dict) else {}
    real_case_calibration = (
        interpretation_source_pack.get("real_case_calibration")
        if isinstance(interpretation_source_pack.get("real_case_calibration"), dict)
        else {}
    )
    return {
        "functional_benefic_malefic": {
            "gate": "hard",
            "used": bool(isinstance(functional_layer, dict) and functional_layer.get("status") == "used"),
            "status": functional_layer.get("status") if isinstance(functional_layer, dict) else "blocked",
            "note": (
                functional_layer.get("effect_on_confidence")
                if isinstance(functional_layer, dict)
                else "Functional benefic/malefic layer unavailable."
            ),
        },
        "interpretation_source_pack": {
            "gate": "hard",
            "used": bool(interpretation_source_pack.get("status") in {"used", "partial"}),
            "status": interpretation_source_pack.get("status") or "blocked",
            "source": interpretation_source_pack.get("source") or "repo_existing_interpretation_sources",
            "source_refs": interpretation_source_pack.get("source_refs") or [],
            "core_rule_source_refs": (
                interpretation_source_pack.get("core_rule_source_layer", {}).get("source_refs")
                if isinstance(interpretation_source_pack.get("core_rule_source_layer"), dict)
                else []
            ),
            "missing_refs": interpretation_source_pack.get("missing_refs") or [],
            "effect_on_confidence": (
                "uses existing BPHS/Raman/frontend/template source layers; missing refs lower confidence"
            ),
        },
        "mevg_global_web_evidence": {
            "gate": "hard",
            "required": True,
            "status": mevg_gate.get("status") or "blocked",
            "source_ref": mevg_gate.get("source_ref") or "references/mandatory-verification-gate-protocol.md",
            "effect_on_confidence": (
                mevg_gate.get("effect_on_confidence")
                or "blocks_or_downgrades_interpretive_claims_until_completed"
            ),
        },
        "real_case_calibration": {
            "gate": "hard",
            "required": True,
            "status": real_case_calibration.get("status") or "blocked",
            "source_ref": real_case_calibration.get("source_ref") or "references/real-reading-quality-checklist.md",
            "effect_on_confidence": (
                real_case_calibration.get("effect_on_confidence")
                or "caps_confidence_without_matching_cases"
            ),
        },
        "relevant_vargas": {
            "gate": "hard",
            "required_keys": varga_keys,
            "present_keys": [key for key in varga_keys if present.get(key)],
        },
        "vimshottari_narayana_crosscheck": {
            "gate": "hard",
            "used": bool(present.get("vimshottari_current")) and bool(present.get("narayana_current")),
            "required_timing_systems": ["Vimshottari", "Narayana"],
        },
        "source_priority_boundary": {
            "gate": "boundary",
            "official": official,
            "local": local,
            "fallback_used": fallback_used,
            "blocked_items": blocked_items,
            "conflicts": conflicts,
        },
    }


def _build_adjudication_stages(route: str, present: Dict[str, Any], event_judgement: Dict[str, Any]) -> Dict[str, Any]:
    dominant_label = event_judgement.get("dominant_label")
    manifestation_drivers = list(event_judgement.get("secondary_context") or [])
    if route == "finance":
        manifestation_bridge_modifiers = [
            key
            for key in (
                "ashtakavarga_finance_support",
                "pav_finance_support",
                "sodhita_finance_support",
                "kakshya_finance_support",
            )
            if present.get(key)
        ]
    elif route == "relationship":
        manifestation_bridge_modifiers = [
            key
            for key in ("synastry_relationship_support", "jaimini_marriage_support", "argala_support")
            if present.get(key)
        ]
    else:
        manifestation_bridge_modifiers = [
            key for key in ("argala_support", "kakshya_career_support", "external_activation") if present.get(key)
        ]
    return {
        "promise": {
            "status": "present" if _has_promise_evidence(route, present) else "weak",
            "drivers": _promise_drivers(route, present),
        },
        "activation": {
            "status": "present" if _has_activation_evidence(route, present) else "weak",
            "required_timing_systems": ["Vimshottari", "Narayana"],
            "drivers": _activation_drivers(route, present),
        },
        "manifestation": {
            "status": "present" if dominant_label else "weak",
            "drivers": manifestation_drivers,
            "bridge_modifiers": manifestation_bridge_modifiers,
        },
        "label": {
            "status": "present" if dominant_label else "missing",
            "value": dominant_label,
            "verdict": event_judgement.get("verdict"),
        },
    }


def _build_multi_reference_reading_summary(route: str, present: Dict[str, Any], strict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "root_frame": _summary_root_frame(route, present),
        "divisional_frame": _summary_divisional_frame(route, present),
        "visibility_frame": _summary_visibility_frame(route, present),
        "karaka_frame": _summary_karaka_frame(route, present),
        "timing_frame": _summary_timing_frame(route, present),
        "modifier_frame": _summary_modifier_frame(route, present),
        "audit_gate_frame": strict.get("technique_audit_summary") or {},
        "conflict_frame": {
            "conflicts": strict.get("conflicts") or [],
            "confidence_cap": strict.get("confidence_cap"),
        },
    }


def _attach_top_reader_contract(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    present = strict.get("present_evidence") if isinstance(strict, dict) else {}
    event_judgement = strict.get("event_judgement") if isinstance(strict, dict) else {}
    if not isinstance(present, dict):
        present = {}
    if not isinstance(event_judgement, dict):
        event_judgement = {}
    strict["technique_audit_summary"] = _build_technique_audit_summary(route, strict)
    strict["adjudication_stages"] = _build_adjudication_stages(route, present, event_judgement)
    strict["multi_reference_reading_summary"] = _build_multi_reference_reading_summary(route, present, strict)
    strict["official_day_signal_summary"] = _build_official_day_signal_summary(present.get("external_activation"))
    strict["monthly_adjudication_summary"] = _build_monthly_adjudication_summary(route, strict)
    strict["verdict"] = event_judgement.get("verdict")
    strict["dominant_label"] = event_judgement.get("dominant_label")
    strict["main_conflicts"] = strict.get("conflicts") or []
    return strict


def _build_life_event_graph(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    event_judgement = strict.get("event_judgement") if isinstance(strict, dict) else {}
    present = strict.get("present_evidence") if isinstance(strict, dict) else {}
    if not isinstance(event_judgement, dict):
        event_judgement = {}
    if not isinstance(present, dict):
        present = {}

    nodes: List[Dict[str, Any]] = []
    nodes.append(
        {
            "kind": "judgement",
            "label": event_judgement.get("dominant_label") or event_judgement.get("event_family") or route,
            "verdict": event_judgement.get("verdict"),
            "score": event_judgement.get("score"),
            "source": "strict_workflow",
        }
    )

    vim = present.get("vimshottari_current")
    if isinstance(vim, dict):
        md = vim.get("mahadasha")
        ad = vim.get("antardasha")
        if isinstance(md, dict):
            md = md.get("lord") or md.get("mahadasha")
        if isinstance(ad, dict):
            ad = ad.get("lord") or ad.get("antardasha")
        label = "/".join([part for part in (md, ad) if part])
        if label:
            nodes.append(
                {
                    "kind": "dasha_window",
                    "label": label,
                    "source": "vimshottari_current",
                }
            )

    narayana = present.get("narayana_current")
    if isinstance(narayana, dict):
        sign = narayana.get("sign")
        lord = narayana.get("lord")
        label = "/".join([part for part in (sign, lord) if part])
        if label:
            nodes.append(
                {
                    "kind": "dasha_window",
                    "label": label,
                    "source": "narayana_current",
                }
            )

    convergence_keys = (
        "marriage_convergence",
        "career_convergence",
        "wealth_convergence",
        "gains_convergence",
    )
    for key in convergence_keys:
        convergence = present.get(key)
        if not isinstance(convergence, dict) or not convergence:
            continue
        nodes.append(
            {
                "kind": "convergence",
                "label": key,
                "level": convergence.get("convergence_level"),
                "probability": convergence.get("probability"),
                "source": "dasa_convergence",
            }
        )

    external_activation = present.get("external_activation")
    if isinstance(external_activation, dict):
        provenance = external_activation.get("provenance")
        if isinstance(provenance, dict) and provenance.get("ingestion_profile") == "main_entry_overview":
            nodes.append(
                {
                    "kind": "external_overview",
                    "label": "VedAstro main-entry overview",
                    "ingestion_profile": provenance.get("ingestion_profile"),
                    "search_scope": provenance.get("search_scope"),
                    "reference_date": provenance.get("reference_date"),
                    "source": external_activation.get("source"),
                }
            )
        for event in external_activation.get("events") or []:
            if not isinstance(event, dict):
                continue
            nodes.append(
                {
                    "kind": "external_window",
                    "label": event.get("signal_label") or event.get("event_id"),
                    "event_id": event.get("event_id"),
                    "signal_key": event.get("signal_key"),
                    "signal_family": event.get("signal_family"),
                    "score": event.get("score"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "tags": event.get("tags") or [],
                    "source": event.get("source") or external_activation.get("source"),
                }
            )
        for window in external_activation.get("daily_windows") or []:
            if not isinstance(window, dict):
                continue
            nodes.append(
                {
                    "kind": "official_day_window",
                    "date": window.get("date"),
                    "domain": window.get("domain"),
                    "score": window.get("score"),
                    "confidence": window.get("confidence"),
                    "event_count": window.get("event_count"),
                    "top_signal_label": window.get("top_signal_label"),
                    "signal_families": window.get("signal_families") or [],
                    "event_ids": window.get("event_ids") or [],
                    "source": external_activation.get("source"),
                }
            )

    for label in event_judgement.get("secondary_context") or []:
        if not isinstance(label, str):
            continue
        if label.startswith("synastry_"):
            nodes.append(
                {
                    "kind": "context",
                    "label": label,
                    "source": "event_judgement.secondary_context",
                }
            )

    return {
        "version": "life_event_graph_v1",
        "route": route,
        "dominant_label": event_judgement.get("dominant_label"),
        "verdict": event_judgement.get("verdict"),
        "confidence_cap": strict.get("confidence_cap"),
        "blocked": bool(strict.get("blocked")),
        "missing_evidence": strict.get("missing_evidence") or [],
        "event_nodes": nodes,
        "secondary_context": event_judgement.get("secondary_context") or [],
        "primary_drivers": event_judgement.get("primary_drivers") or [],
    }


def _with_life_event_graph(route: str, strict: Dict[str, Any]) -> Dict[str, Any]:
    strict["life_event_graph"] = _build_life_event_graph(route, strict)
    return strict


def _collect_strict_evidence(route: str, result: Dict[str, Any]) -> Dict[str, Any]:
    modules = result.get("modules", {}) if isinstance(result, dict) else {}
    domain_activations = _safe_get(modules, "dasa_convergence", "domain_activations") or {}

    if route == "career":
        required = [
            "varga_full.D10_Dasamsa",
            "special_lagnas.A10_Karma_Pada",
            "jaimini.karakas.Amatyakaraka",
            "jaimini.karakamsha",
            "dasha.current_dasha",
            "narayana_dasha.current_dasha",
            "dasa_convergence.domain_activations.career_status",
        ]
        present = {
            "d10_dasamsa": _safe_get(modules, "varga_full", "D10_Dasamsa"),
            "a10_karma_pada": _safe_get(modules, "special_lagnas", "A10_Karma_Pada"),
            "amatyakaraka": (
                _safe_get(modules, "jaimini", "chara_karaka_7", "karaka_table", "Amatyakaraka")
                or _safe_get(modules, "jaimini", "karakas", "Amatyakaraka")
            ),
            "karakamsha": _safe_get(modules, "jaimini", "karakamsha"),
            "vimshottari_current": _safe_get(modules, "dasha", "current_dasha"),
            "narayana_current": _safe_get(modules, "narayana_dasha", "current_dasha"),
            "career_convergence": domain_activations.get("career_status"),
        }
        present["shadbala"] = _safe_get(modules, "shadbala", "planets")
        present["shadbala_component_audit"] = _derive_shadbala_component_audit(present["shadbala"]) if present["shadbala"] else None
        present["kakshya_career_support"] = _derive_kakshya_career_support(_safe_get(modules, "kakshya"))
        present["argala_support"] = _derive_argala_support(modules, 10)
        present["external_activation"] = _derive_external_activation_support(modules, "career")
        present["external_technique_evidence"] = _derive_external_technique_evidence(modules, "career")
        present["vedastro_official_snapshot"] = official_snapshot_evidence(modules)
        present["source_priority"] = modules.get("source_priority") if isinstance(modules.get("source_priority"), dict) else {}
        present["chart"] = _safe_get(modules, "chart")
        present["dignity_guardrail"] = _derive_dignity_guardrail(route, present)
        present["functional_benefic_malefic"] = _derive_functional_benefic_malefic(modules)
        present["interpretation_source_pack"] = _existing_interpretation_source_pack()
        missing = [key for key, value in present.items() if key not in {
            "chart", "external_activation", "external_technique_evidence", "vedastro_official_snapshot", "source_priority", "dignity_guardrail", "argala_support", "shadbala", "shadbala_component_audit", "kakshya_career_support", "functional_benefic_malefic", "interpretation_source_pack"
        } and value in (None, {}, [], "")]
        convergence = present["career_convergence"] or {}
        confidence_cap = "medium"
        if missing:
            confidence_cap = "low"
        elif present["dignity_guardrail"].get("status") == "conflict":
            confidence_cap = "low"
        elif (present.get("shadbala_component_audit") or {}).get("status") in {"blocked", "incomplete"}:
            confidence_cap = "low"
        elif convergence.get("convergence_level") in {"L4", "L5"}:
            confidence_cap = "medium-high"
        elif convergence.get("convergence_level") == "L3":
            confidence_cap = "medium"
        else:
            confidence_cap = "medium-low"
        event_judgement = _derive_event_judgement(route, present, missing)
        strict = {
            "question_type": route,
            "required_evidence": required,
            "present_evidence": present,
            "missing_evidence": missing,
            "confidence_cap": confidence_cap,
            "blocked": bool(missing),
            "event_judgement": event_judgement,
            "reason": (
                "Career timing requires D10 + A10/Karma Pada + AmK/Karakamsha "
                "plus dual dasha and career convergence support."
            ),
        }
        strict["official_primary_evidence"] = _build_official_primary_evidence(route, present)
        strict["local_supplemental_evidence"] = _build_local_supplemental_evidence(route, present)
        strict["fallback_used"], strict["blocked_items"] = _build_fallback_and_blocked(
            route,
            present,
            missing,
            strict["official_primary_evidence"],
        )
        strict["conflicts"] = _build_conflicts(route, present, strict["official_primary_evidence"])
        audit = (
            _official_snapshot_audit(present.get("vedastro_official_snapshot"))
            + _external_activation_audit(present.get("external_activation"))
            + _external_technique_audit(present.get("external_technique_evidence"))
        )
        if audit:
            strict["technique_audit"] = audit
        strict = _attach_top_reader_contract(route, strict)
        return _with_life_event_graph(route, strict)

    if route == "relationship":
        required = [
            "varga_full.D9_Navamsa",
            "special_lagnas.Upapada_Lagna",
            "jaimini.darakaraka",
            "vivah_saham",
            "dasha.current_dasha",
            "narayana_dasha.current_dasha",
            "dasa_convergence.domain_activations.marriage_partnership",
        ]
        present = {
            "d9_navamsa": _safe_get(modules, "varga_full", "D9_Navamsa"),
            "upapada_lagna": _safe_get(modules, "special_lagnas", "Upapada_Lagna"),
            "darakaraka": _safe_get(modules, "jaimini", "darakaraka"),
            "vivah_saham": _safe_get(modules, "vivah_saham"),
            "chart": _safe_get(modules, "chart"),
            "vimshottari_current": _safe_get(modules, "dasha", "current_dasha"),
            "narayana_current": _safe_get(modules, "narayana_dasha", "current_dasha"),
            "marriage_convergence": domain_activations.get("marriage_partnership"),
        }
        present["shadbala"] = _safe_get(modules, "shadbala", "planets")
        present["shadbala_component_audit"] = _derive_shadbala_component_audit(present["shadbala"]) if present["shadbala"] else None
        present["jaimini_timing_support"] = _safe_get(modules, "jaimini", "marriage_timing_support")
        present["jaimini_marriage_support"] = _derive_jaimini_marriage_support(present)
        present["synastry_relationship_support"] = _derive_synastry_relationship_support(modules)
        present["argala_support"] = _derive_argala_support(modules, 7)
        present["external_activation"] = _derive_external_activation_support(modules, "marriage")
        present["external_technique_evidence"] = _derive_external_technique_evidence(modules, "marriage")
        present["vedastro_official_snapshot"] = official_snapshot_evidence(modules)
        present["source_priority"] = modules.get("source_priority") if isinstance(modules.get("source_priority"), dict) else {}
        present["dignity_guardrail"] = _derive_dignity_guardrail(route, present)
        present["functional_benefic_malefic"] = _derive_functional_benefic_malefic(modules)
        present["interpretation_source_pack"] = _existing_interpretation_source_pack()
        missing = [
            key for key, value in present.items()
            if key not in {"chart", "external_activation", "external_technique_evidence", "vedastro_official_snapshot", "source_priority", "dignity_guardrail", "jaimini_marriage_support", "jaimini_timing_support", "synastry_relationship_support", "argala_support", "shadbala", "shadbala_component_audit", "functional_benefic_malefic", "interpretation_source_pack"}
            and value in (None, {}, [], "")
        ]
        convergence = present["marriage_convergence"] or {}
        confidence_cap = "medium"
        if missing:
            confidence_cap = "low"
        elif present["dignity_guardrail"].get("status") == "conflict":
            confidence_cap = "low"
        elif (present.get("shadbala_component_audit") or {}).get("status") in {"blocked", "incomplete"}:
            confidence_cap = "low"
        elif convergence.get("convergence_level") in {"L4", "L5"}:
            confidence_cap = "medium-high"
        elif convergence.get("convergence_level") == "L3":
            confidence_cap = "medium"
        else:
            confidence_cap = "medium-low"
        event_judgement = _derive_event_judgement(route, present, missing)
        strict = {
            "question_type": route,
            "required_evidence": required,
            "present_evidence": present,
            "missing_evidence": missing,
            "confidence_cap": confidence_cap,
            "blocked": bool(missing),
            "event_judgement": event_judgement,
            "reason": (
                "Marriage timing requires D9 + UL + DK + dual dasha + Vivah Saham "
                "and convergence support; missing links cap confidence."
            ),
        }
        strict["official_primary_evidence"] = _build_official_primary_evidence(route, present)
        strict["local_supplemental_evidence"] = _build_local_supplemental_evidence(route, present)
        strict["fallback_used"], strict["blocked_items"] = _build_fallback_and_blocked(
            route,
            present,
            missing,
            strict["official_primary_evidence"],
        )
        strict["conflicts"] = _build_conflicts(route, present, strict["official_primary_evidence"])
        audit = (
            _official_snapshot_audit(present.get("vedastro_official_snapshot"))
            + _external_activation_audit(present.get("external_activation"))
            + _external_technique_audit(present.get("external_technique_evidence"))
        )
        if audit:
            strict["technique_audit"] = audit
        strict = _attach_top_reader_contract(route, strict)
        return _with_life_event_graph(route, strict)

    if route == "finance":
        avayogi_risk = _check_external_avayogi_risk(result)
        required = [
            "varga_full.D2_Hora",
            "varga_full.D10_Dasamsa",
            "shadbala.planets",
            "ashtakavarga.house_scores",
            "dasha.current_dasha",
            "narayana_dasha.current_dasha",
            "dasa_convergence.domain_activations.wealth_family",
        ]
        present = {
            "d2_hora": _safe_get(modules, "varga_full", "D2_Hora"),
            "d10_dasamsa": _safe_get(modules, "varga_full", "D10_Dasamsa"),
            "shadbala": _safe_get(modules, "shadbala", "planets"),
            "ashtakavarga_house_scores": _safe_get(modules, "ashtakavarga", "house_scores"),
            "vimshottari_current": _safe_get(modules, "dasha", "current_dasha"),
            "narayana_current": _safe_get(modules, "narayana_dasha", "current_dasha"),
            "wealth_convergence": domain_activations.get("wealth_family"),
            "gains_convergence": domain_activations.get("gains_wishes"),
            "chart": _safe_get(modules, "chart"),
            "career_convergence": domain_activations.get("career_status"),
            "wealth_promise_strength": _derive_wealth_promise_strength(modules),
            "avayogi_risk": avayogi_risk,
        }
        present["asc_sign"] = _safe_get(modules, "chart", "ascendant", "sign")
        present["shadbala_component_audit"] = _derive_shadbala_component_audit(present["shadbala"])
        present["ashtakavarga_finance_support"] = _derive_ashtakavarga_finance_support(
            present["ashtakavarga_house_scores"]
        )
        present["pav_finance_support"] = _derive_pav_finance_support(_safe_get(modules, "ashtakavarga"))
        present["sodhita_finance_support"] = _derive_sodhita_finance_support(
            _safe_get(modules, "ashtakavarga"),
            present["asc_sign"],
        )
        present["kakshya_finance_support"] = _derive_kakshya_finance_support(_safe_get(modules, "kakshya"))
        present["external_activation"] = _derive_external_activation_support(modules, "wealth")
        present["external_technique_evidence"] = _derive_external_technique_evidence(modules, "wealth")
        present["vedastro_official_snapshot"] = official_snapshot_evidence(modules)
        present["source_priority"] = modules.get("source_priority") if isinstance(modules.get("source_priority"), dict) else {}
        present["dignity_guardrail"] = _derive_dignity_guardrail(route, present)
        present["functional_benefic_malefic"] = _derive_functional_benefic_malefic(modules)
        present["interpretation_source_pack"] = _existing_interpretation_source_pack()
        missing = [key for key, value in present.items() if key not in {
            "chart", "external_activation", "external_technique_evidence", "vedastro_official_snapshot", "source_priority", "dignity_guardrail", "gains_convergence", "career_convergence", "avayogi_risk", "ashtakavarga_finance_support", "shadbala_component_audit", "asc_sign", "pav_finance_support", "sodhita_finance_support", "kakshya_finance_support", "functional_benefic_malefic", "interpretation_source_pack"
        } and value in (None, {}, [], "")]
        convergence_hits: List[Dict[str, Any]] = [
            item for item in [
                present["wealth_convergence"],
                present["gains_convergence"],
                present["career_convergence"],
            ]
            if isinstance(item, dict) and item
        ]
        confidence_cap = "medium"
        if missing:
            confidence_cap = "low"
        elif present["dignity_guardrail"].get("status") == "conflict":
            confidence_cap = "low"
        elif present["shadbala_component_audit"].get("status") in {"blocked", "incomplete"}:
            confidence_cap = "low"
        elif any(hit.get("convergence_level") in {"L4", "L5"} for hit in convergence_hits):
            confidence_cap = "medium-high"
        elif convergence_hits:
            confidence_cap = "medium"
        else:
            confidence_cap = "medium-low"
        event_judgement = _derive_event_judgement(route, present, missing)
        promise = present.get("wealth_promise_strength") or {}
        if "yogi" in promise.get("supporting_sources", []) and event_judgement.get("dominant_label") and "yogi_active" not in event_judgement.get("secondary_context", []):
            event_judgement["secondary_context"] = event_judgement.get("secondary_context", []) + ["yogi_active"]
        strict = {
            "question_type": route,
            "required_evidence": required,
            "present_evidence": present,
            "missing_evidence": missing,
            "confidence_cap": confidence_cap,
            "blocked": bool(missing),
            "event_judgement": event_judgement,
            "reason": (
                "Finance timing requires D2/D10 + strength + SAV + dual dasha "
                "plus at least one wealth-related convergence domain."
            ),
        }
        strict["official_primary_evidence"] = _build_official_primary_evidence(route, present)
        strict["local_supplemental_evidence"] = _build_local_supplemental_evidence(route, present)
        strict["fallback_used"], strict["blocked_items"] = _build_fallback_and_blocked(
            route,
            present,
            missing,
            strict["official_primary_evidence"],
        )
        strict["conflicts"] = _build_conflicts(route, present, strict["official_primary_evidence"])
        audit = (
            _official_snapshot_audit(present.get("vedastro_official_snapshot"))
            + _external_activation_audit(present.get("external_activation"))
            + _external_technique_audit(present.get("external_technique_evidence"))
        )
        if audit:
            strict["technique_audit"] = audit
        strict = _attach_top_reader_contract(route, strict)
        return _with_life_event_graph(route, strict)

    strict = {
        "question_type": route,
        "required_evidence": [],
        "present_evidence": {},
        "missing_evidence": [],
        "confidence_cap": "context-only",
        "blocked": False,
        "event_judgement": _derive_event_judgement(route, {}, []),
        "reason": "Route-specific strict evidence audit is currently implemented for relationship and finance timing.",
    }
    strict = _attach_top_reader_contract(route, strict)
    return _with_life_event_graph(route, strict)


def _default_vedastro_scan_window(transit_date: str) -> tuple[str, str]:
    try:
        start = datetime.strptime(str(transit_date), "%Y-%m-%d").date()
    except ValueError:
        return str(transit_date), str(transit_date)
    end = start + timedelta(days=180)
    return start.isoformat(), end.isoformat()


def _maybe_attach_vedastro_evidence(
    route: str,
    result: Dict[str, Any],
    *,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    transit_date: str,
    node_mode: str,
) -> Dict[str, Any]:
    if not isinstance(result, dict) or result.get("error"):
        return result

    modules = result.get("modules")
    if not isinstance(modules, dict):
        return result

    vedastro_domain = _VEDASTRO_ROUTE_DOMAIN.get(route)
    if not vedastro_domain:
        return result

    if modules.get("vedastro_range_scan_result") or _safe_get(modules, "external_activation", "evidence_ledger"):
        return result

    try:
        from vedastro_evidence_orchestrator import orchestrate_vedastro_evidence
    except Exception:
        return result

    start_date, end_date = _default_vedastro_scan_window(transit_date)
    scan_result = orchestrate_vedastro_evidence(
        {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": 0,
            "lat": lat,
            "lon": lon,
            "tz": tz,
            "ayanamsa_policy": (
                _safe_get(result, "meta", "ayanamsa")
                or _safe_get(result, "chart", "ayanamsa")
                or "lahiri"
            ),
            "node_policy": node_mode or "mean",
        },
        route=route,
        start_date=start_date,
        end_date=end_date,
        case_id=f"strict_workflow_{route}",
    )
    if not isinstance(scan_result, dict):
        return result

    attached_scan = deepcopy(scan_result)
    metadata = attached_scan.get("source_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.setdefault("auto_ingested_by", "strict_workflow")
    metadata.setdefault("strict_route", route)
    metadata.setdefault("scan_window", {"start_date": start_date, "end_date": end_date})
    metadata.setdefault("adapter_status", attached_scan.get("status"))
    if attached_scan.get("reason"):
        metadata.setdefault("adapter_reason", attached_scan.get("reason"))
    attached_scan["source_metadata"] = metadata

    enriched = dict(result)
    enriched["modules"] = dict(modules)
    enriched["modules"]["vedastro_range_scan_result"] = attached_scan
    official_snapshot = attached_scan.get("official_full_snapshot")
    if isinstance(official_snapshot, dict):
        try:
            from vedastro_priority import apply_vedastro_source_priority

            apply_vedastro_source_priority(enriched, official_snapshot=official_snapshot)
        except Exception:
            enriched["modules"]["vedastro_official_full_snapshot"] = official_snapshot
    return enriched


# ============================================================================
# Tools
# ============================================================================

@mcp.tool()
def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate a complete Vedic birth chart (D1 Rashi).

    Returns: planets with sidereal longitudes, houses (whole-sign),
    Nakshatra placements, dignity levels, and combustion status.
    Uses Swiss Ephemeris with Lahiri ayanamsa.

    Args:
        year: Birth year (e.g. 1990)
        month: Birth month (1-12)
        day: Birth day (1-31)
        hour: Birth hour (0-23)
        minute: Birth minute (0-59)
        lat: Latitude in decimal degrees (north positive, e.g. 28.61)
        lon: Longitude in decimal degrees (east positive, e.g. 77.20)
        tz: Timezone offset from UTC in hours (e.g. 5.5 for IST, 8.0 for CST)
        node_mode: 'mean' (default) or 'true' for lunar node calculation

    Returns:
        JSON with planets, houses, ascendant, Nakshatras, dignities
    """
    return _run_engine("chart", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_dasha(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    start_date: Optional[str] = None,
    years: int = 10,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate Vimshottari Dasha (planetary period) timeline.

    Returns the hierarchical Dasha timeline (Maha Dasha → Antar Dasha → Pratyantar)
    from birth or from a specified start_date.

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        start_date: Optional start date (YYYY-MM-DD) for Dasha from a specific date
        years: Number of years to calculate from birth (default 10)
        node_mode: 'mean' or 'true'

    Returns:
        JSON with Dasha periods, start/end dates, and current Dasha at birth
    """
    args = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "years": years, "node_mode": node_mode,
    }
    if start_date:
        args["start_date"] = start_date
    return _run_engine("dasha", args)


@mcp.tool()
def calculate_shadbala(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate Shadbala (six-fold planetary strength).

    Returns the six components of planetary strength:
    Sthana Bala (positional), Dig Bala (directional), Kala Bala (temporal),
    Chesta Bala (motional), Naisargika Bala (natural), Drik Bala (aspectual).

    NOTE: This is currently a PARTIAL implementation (v6.0.11).
    Internal invariants pass (1200/1200) but external absolute calibration
    against JHora/PyJHora/BV Raman is NOT yet complete.
    Use for relative strength comparison only, NOT for absolute assertions.

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        node_mode: 'mean' or 'true'

    Returns:
        JSON with Shadbala components and total scores per planet
    """
    return _run_engine("shadbala", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_ashtakavarga(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate Ashtakavarga (eight-fold strength matrix).

    Returns the Ashtakavarga table (bindus contributed by each planet to each house)
    and the Sarva Ashtakavarga (SAV) total for each house.
    Uses BPHS complete table (SAV=337 total).

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        node_mode: 'mean' or 'true'

    Returns:
        JSON with per-planet Ashtakavarga tables and SAV totals
    """
    return _run_engine("ashtakavarga", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_varga(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    varga: str = "D9",
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate a specific Varga (divisional chart).

    Supported vargas: D9 (Navamsa), D10 (Dasamsa), D12 (Dwadasamsa),
    D16 (Shodasamsa), D20 (Vimsamsa), D24 (Chaturvimsamsa),
    D30 (Trimshamsa), D40 (Khavedamsa), D45 (Akshavedamsa), D60 (Shastiamsa).

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        varga: Varga code (default 'D9' for Navamsa)
        node_mode: 'mean' or 'true'

    Returns:
        JSON with varga chart planets and house placements
    """
    return _run_engine("varga", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "varga": varga,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_varga_full(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate ALL Vargas (D2 through D60) in one call.

    Returns the complete BPHS sixteen-varga system.
    D2=Hora, D3=Drekkana, D4=Chaturthamsa, D7=Saptamsa,
    D9=Navamsa, D10=Dasamsa, D12=Dwadasamsa, D16=Shodasamsa,
    D20=Vimsamsa, D24=Chaturvimsamsa, D30=Trimshamsa,
    D40=Khavedamsa, D45=Akshavedamsa, D60=Shastiamsa.

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        node_mode: 'mean' or 'true'

    Returns:
        JSON with all varga charts
    """
    return _run_engine("varga-full", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "node_mode": node_mode,
    })


@mcp.tool()
def analyze_nakshatra(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    mode: str = "full",
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Advanced Nakshatra analysis (Chandra Bala, Tara Bala, combined score).

    Modes:
    - 'chandra': Chandra Bala only (Moon's strength in Nakshatras)
    - 'tara': Tara Bala only (constellation-based fortune timing)
    - 'combined': Both Chandra + Tara with combined score
    - 'full': Full Nakshatra report with Dasha overlay

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        mode: 'chandra' | 'tara' | 'combined' | 'full' (default 'full')
        node_mode: 'mean' or 'true'

    Returns:
        JSON with Nakshatra analysis results
    """
    return _run_engine("nakshatra-adv", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "mode": mode,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_yogas(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Detect Yogas (planetary combinations) in the birth chart.

    Detects:
    - Raja Yogas (power/combin status)
    - Dhana Yogas (wealth combinations)
    - Pancha Mahapurusha Yogas (great person combinations)
    - Neecha Bhanga Raja Yoga (cancellation of debility)
    - Many more from classical texts

    NOTE: Partial implementation. Not all 284 yoga variants from PyJHora
    are covered. Use as辅助参考, not sole evidence.

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        node_mode: 'mean' or 'true'

    Returns:
        JSON with detected yogas and their strengths
    """
    return _run_engine("yoga", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "node_mode": node_mode,
    })


@mcp.tool()
def calculate_transit(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    transit_date: str,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Calculate planetary transits for a specific date.

    Returns true sidereal positions of all planets for the transit date,
    plus double-transit analysis (Saturn + Jupiter) for event timing.

    Args:
        year, month, day, hour, minute: Birth datetime (for natal reference)
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        transit_date: Transit date to analyze (YYYY-MM-DD format)
        node_mode: 'mean' or 'true'

    Returns:
        JSON with transit positions and double-transit analysis
    """
    return _run_engine("transit", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "transit_date": transit_date,
        "node_mode": node_mode,
    })


@mcp.tool()
def full_reading(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    age: int,
    transit_date: str,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Full Jyotish reading: all techniques in one synthesized report.

    This is the flagship command. It runs the complete analysis pipeline:
    D1 chart → D9 Navamsa → D10 Dasamsa → Vimshottari Dasha →
    Dasha Sandhi → Narayana Dasha → Solar Return → Nakshatra Advanced →
    Shadbala → Ashtakavarga → Transit → Argala → A10 Karma Pada →
    UL Upapada → Vargottama → Pushkara → Yogas/Doshas → and more.

    The output includes a Technique Audit Table showing which techniques
    are covered (verified) vs partial (approximate).

    Args:
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        age: Current age of the person (used for age-appropriate analysis)
        transit_date: Transit date for prediction (YYYY-MM-DD)
        node_mode: 'mean' or 'true'

    Returns:
        JSON with complete reading: all modules, synthesis, audit table
    """
    return _run_engine("full-reading", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "age": age,
        "transit_date": transit_date,
        "node_mode": node_mode,
    })


@mcp.tool()
def get_audit_status() -> Dict[str, Any]:
    """
    Get the technique registry audit status.

    Returns which of the 44 techniques are covered (verified against
    authoritative sources), partial (implemented but not fully benchmarked),
    or missing. Also returns any warnings or problems.

    Use this before making predictions to know which techniques are reliable.

    Returns:
        JSON with technique_count, covered/partial/missing counts,
        warnings, and the full technique registry
    """
    return _audit_status()


@mcp.tool()
def strict_workflow(
    question: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    age: int,
    transit_date: str,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Strict workflow router: routes question to the correct analysis path.

    Instead of running all techniques, this selects the optimal technique
    combination based on the question type:
    - Career questions → D10 + Dasha + Shadbala + Transit
    - Relationship questions → D9 + UL + Dasha + Nakshatra
    - Financial questions → D2 + D11 + Dasha + Shadbala
    - Event timing → Dasha + Transit + Gochara

    This produces higher-confidence results than full-reading for specific questions.

    Args:
        question: The user's question in natural language
                  (e.g. 'When will I get married?', 'Career change?')
        year, month, day, hour, minute: Birth datetime
        lat, lon: Birth place coordinates
        tz: Timezone offset from UTC
        age: Current age
        transit_date: Transit date for prediction (YYYY-MM-DD)
        node_mode: 'mean' or 'true'

    Returns:
        JSON with routed analysis and confidence level
    """
    route_packet = _UNIFIED_CONSULTATION_ORCHESTRATOR.resolve_route(question, None)
    normalized_themes = _UNIFIED_CONSULTATION_ORCHESTRATOR.normalize_themes(route_packet["primary_theme"])

    result = _execute_mcp_consultation_workflow(
        question=question,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lon=lon,
        tz=tz,
        transit_date=transit_date,
        node_mode=node_mode,
        entry_mode="direct_chart",
        theme=normalized_themes,
    )
    chart = result.get("chart") if isinstance(result, dict) else {}
    route = _safe_get(result, "routing", "question_type") or route_packet["question_type"] or "general"
    if isinstance(chart, dict) and "error" not in chart:
        chart = _maybe_attach_vedastro_evidence(
            route,
            chart,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            lat=lat,
            lon=lon,
            tz=tz,
            transit_date=transit_date,
            node_mode=node_mode,
        )
        result["chart"] = chart
        result["strict_workflow"] = _collect_strict_evidence(route, chart)
    return result


@mcp.tool()
def life_event_graph(
    question: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    age: int,
    transit_date: str,
    node_mode: str = "mean",
) -> Dict[str, Any]:
    """
    Build a graph-friendly event timeline from strict workflow evidence.

    This tool reuses the local full-reading pipeline plus strict adjudicator
    evidence and optional VedAstro range-scan windows already present in the
    evidence ledger. It does not claim external oracle closure by itself.
    """
    result = strict_workflow(
        question=question,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lon=lon,
        tz=tz,
        age=age,
        transit_date=transit_date,
        node_mode=node_mode,
    )
    route = _safe_get(result, "routing", "question_type") or "general"
    strict = result.get("strict_workflow") if isinstance(result, dict) else {}
    return {
        "question": question,
        "route": route,
        "life_event_graph": _build_life_event_graph(route, strict if isinstance(strict, dict) else {}),
        "strict_workflow": strict,
    }


# ============================================================================
# Resources
# ============================================================================

@mcp.resource("jyotish://technique-registry")
def technique_registry_resource() -> str:
    """Full technique registry as JSON."""
    registry_path = os.path.join(SCRIPT_DIR, "references", "technique_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("jyotish://quick-reference")
def quick_reference_resource() -> str:
    """Quick reference guide for Jyotish concepts."""
    qr_path = os.path.join(SCRIPT_DIR, "references", "quick-reference-guide.md")
    with open(qr_path, "r", encoding="utf-8") as f:
        return f.read()


@mcp.resource("jyotish://audit-status")
def audit_status_resource() -> str:
    """Current audit status as JSON."""
    status = _audit_status()
    return json.dumps(status, indent=2, ensure_ascii=False)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    mcp.run()
