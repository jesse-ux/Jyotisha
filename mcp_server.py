#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jyotish MCP Server v1.0
Exposes Jyotish-Vedic-Astrology calculation engine as MCP tools.

Install:
  pip install mcp

Run:
  python3 mcp_server.py

Add to ~/.workbuddy/mcp.json:
  {
    "mcpServers": {
      "jyotish": {
        "command": "/Users/wuyongnaren/.workbuddy/binaries/python/versions/3.13.12/bin/python3",
        "args": ["/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology/mcp_server.py"],
        "env": {}
      }
    }
  }
"""

import sys
import os
import json
import subprocess
import asyncio
from typing import Dict, Any, Optional, List

# Add scripts dir to path so imports work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))

from mcp.server.fastmcp import FastMCP

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


def _derive_event_judgement(route: str, present: Dict[str, Any], missing: List[str]) -> Dict[str, Any]:
    if route == "relationship":
        score = 0
        score += 15 if present.get("d9_navamsa") else 0
        score += 15 if present.get("upapada_lagna") else 0
        score += 15 if present.get("darakaraka") else 0
        score += 10 if present.get("vivah_saham") else 0
        score += 10 if present.get("vimshottari_current") else 0
        score += 10 if present.get("narayana_current") else 0
        score += _convergence_score(present.get("marriage_convergence"))
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
        score += 20 if wealth_promise_level == "strong" else 10 if wealth_promise_level == "moderate" else 0
        score += 5 if wealth_promise_diversity >= 2 else 0
        score += max(
            _convergence_score(present.get("wealth_convergence")),
            _convergence_score(present.get("gains_convergence")),
            _convergence_score(present.get("career_convergence")),
        )
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


def _collect_strict_evidence(route: str, result: Dict[str, Any]) -> Dict[str, Any]:
    modules = result.get("modules", {}) if isinstance(result, dict) else {}
    domain_activations = _safe_get(modules, "dasa_convergence", "domain_activations") or {}

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
            "vimshottari_current": _safe_get(modules, "dasha", "current_dasha"),
            "narayana_current": _safe_get(modules, "narayana_dasha", "current_dasha"),
            "marriage_convergence": domain_activations.get("marriage_partnership"),
        }
        present["jaimini_timing_support"] = _safe_get(modules, "jaimini", "marriage_timing_support")
        present["jaimini_marriage_support"] = _derive_jaimini_marriage_support(present)
        missing = [
            key for key, value in present.items()
            if key not in {"jaimini_marriage_support", "jaimini_timing_support"}
            and value in (None, {}, [], "")
        ]
        convergence = present["marriage_convergence"] or {}
        confidence_cap = "medium"
        if missing:
            confidence_cap = "low"
        elif convergence.get("convergence_level") in {"L4", "L5"}:
            confidence_cap = "medium-high"
        elif convergence.get("convergence_level") == "L3":
            confidence_cap = "medium"
        else:
            confidence_cap = "medium-low"
        event_judgement = _derive_event_judgement(route, present, missing)
        return {
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
            "career_convergence": domain_activations.get("career_status"),
            "wealth_promise_strength": _derive_wealth_promise_strength(modules),
            "avayogi_risk": avayogi_risk,
        }
        missing = [key for key, value in present.items() if key not in {
            "gains_convergence", "career_convergence", "avayogi_risk"
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
        return {
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

    return {
        "question_type": route,
        "required_evidence": [],
        "present_evidence": {},
        "missing_evidence": [],
        "confidence_cap": "context-only",
        "blocked": False,
        "event_judgement": _derive_event_judgement(route, {}, []),
        "reason": "Route-specific strict evidence audit is currently implemented for relationship and finance timing.",
    }


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
    q = question.lower()
    if any(k in q for k in ("career", "job", "work", "promotion", "business", "profession", "事业", "工作", "升职", "生意")):
        route = "career"
        focus_techniques = ["D10", "Dasha", "Shadbala", "Transit", "Narayana Dasha"]
    elif any(k in q for k in ("marriage", "married", "wedding", "relationship", "love", "spouse", "partner", "divorce", "婚恋", "婚姻", "感情", "配偶", "恋爱", "结婚")):
        route = "relationship"
        focus_techniques = ["D9", "UL Upapada", "Dasha", "Nakshatra", "Vivah Saham"]
    elif any(k in q for k in ("money", "wealth", "finance", "investment", "property", "income", "财务", "财富", "投资", "房产", "收入")):
        route = "finance"
        focus_techniques = ["D2", "D11", "Dasha", "Shadbala", "Ashtakavarga"]
    elif any(k in q for k in ("when", "timing", "event", "prediction", "future", "应期", "预测", "何时", "将来")):
        route = "timing"
        focus_techniques = ["Dasha", "Transit", "Double Transit", "Gochara"]
    else:
        route = "general"
        focus_techniques = ["D1", "D9", "Dasha", "Yoga", "Shadbala", "Ashtakavarga"]

    result = _run_engine("full-reading", {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
        "age": age, "transit_date": transit_date,
        "node_mode": node_mode,
    })

    if isinstance(result, dict) and "error" not in result:
        strict_evidence = _collect_strict_evidence(route, result)
        result["routing"] = {
            "question_type": route,
            "focus_techniques": focus_techniques,
            "note": (
                f"Routed to '{route}' path. Focus on the listed techniques "
                f"for higher-confidence answers. Full reading included for context, "
                f"and strict evidence audit now reports confidence cap and missing links."
            ),
        }
        result["strict_workflow"] = strict_evidence
    return result


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
