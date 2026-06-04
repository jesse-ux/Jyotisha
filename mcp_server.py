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
from typing import Dict, Any, Optional

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
    elif any(k in q for k in ("marriage", "relationship", "love", "spouse", "partner", "divorce", "婚恋", "婚姻", "感情", "配偶", "恋爱")):
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
        result["routing"] = {
            "question_type": route,
            "focus_techniques": focus_techniques,
            "note": (
                f"Routed to '{route}' path. Focus on the listed techniques "
                f"for higher-confidence answers. Full reading included for context."
            ),
        }
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
