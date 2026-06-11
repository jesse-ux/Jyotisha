"""
RishiAI MCP Server — Vedic astrology tools via the Model Context Protocol.

Thin wrapper around the DashaFlow library. Exposes 5 tools:
  cast_vedic_chart, cast_transit_chart, calculate_compatibility_tool,
  check_muhurtha_tool, analyze_career_chart.

Install:  pip install rishi-ai-mcp
Run:      rishi-ai-mcp            (console entry-point)
  or:     python rishi_ai_mcp.py  (direct)
"""

__version__ = "1.1.0"

import json
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from dashaflow import (
    cast_chart,
    cast_transit,
    calculate_compatibility,
    check_muhurtha,
    analyze_career,
)

mcp = FastMCP(
    "vedic-astrology",
    instructions="Vedic Astrology chart calculator using Swiss Ephemeris (Sidereal Lahiri)",
)


@mcp.tool()
def cast_vedic_chart(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
    query_date: str = "",
) -> Dict[str, Any]:
    """
    Calculate a complete Vedic birth chart (Sidereal Lahiri ayanamsha).

    Returns (JSON):
    - `metadata`: DOB, time, coordinates, ayanamsha (Lahiri), ayanamsha degrees, query date.
    - `panchang`: Tithi (number, name, paksha), Vara (weekday + lord), Nakshatra (Moon's), Yoga, Karana.
    - `lagna`: sign, degree, nakshatra, pada, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D60 signs.
    - `planets`: For each of Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu:
      - `sign`, `degree`, `house` (whole-sign from Lagna), `nakshatra`, `pada`, `nakshatra_lord`
      - `is_retrograde`, `is_combust`, `has_digbala`
      - `dignity`: "exalted" / "mooltrikona" / "own_sign" / "friend" / "neutral" / "enemy" / "debilitated"
      - `d2_sign`, `d9_sign`, `d10_sign`, `d16_sign`, `d20_sign`, `d24_sign`, `d27_sign`, `d30_sign`, `d40_sign`, `d60_sign`
      - `aspects`: signs aspected (BPHS special aspects for Mars, Jupiter, Saturn; 7th for all others)
    - `dashas`:
      - `maha`: current Mahadasha (planet, start, end)
      - `antar`: current Antardasha (planet, start, end)
      - `pratyantar`: current Pratyantardasha (planet, start, end)
      - `sukshma`: current Sukshma dasha (planet, start, end)
      - `prana`: current Prana dasha (planet, start, end)
      - `timeline`: full Mahadasha sequence (~120 years from birth)
    - `yogas`: array of `{ name, formed_by, description }`. Detected (24 types): Pancha Mahapurusha (5), Gajakesari, Budhaditya, Chandra-Mangal, Kemadruma, Adhi Yoga, Raj Yoga (dual lordship + conjunction), Viparita Raj Yoga, Neecha Bhanga Raja Yoga, Parivartana Yoga (Maha/Khala/Dainya), Dhana Yoga, Sunapha/Anapha/Durudhura, Amala Yoga, Saraswati Yoga, Lakshmi Yoga, Veshi/Voshi/Ubhayachari Yoga.
    - `ashtakavarga`: SAV (Sarvashtakavarga), BAV (Bhinnashtakavarga), Prashtara Ashtakavarga (source-level bindu contributions), and total bindus (337).
    - `jaimini_karakas`: 7 Karakas by degree — Atmakaraka, Amatyakaraka, Bhratrukaraka, etc.
    - `shadbala`: six-fold strength in Rupas and Percentage of required strength per planet, plus `ishta_kashta_phala` (Ishta Phala = auspicious capacity, Kashta Phala = suffering potential).
    - `bhava_chalit`: Equal-house Bhava Chalit chart (cusps calculated from Lagna midpoint). Lists each house's start/end degree and which planets actually fall in each bhava. Use when a planet near a house cusp may functionally belong to the adjacent house.
    - `avasthas`: Planetary age-states per BPHS — Bala (infant), Kumara (youth), Yuva (adult), Vriddha (old), Mrita (dead). Odd signs: 0–6° Bala … 24–30° Mrita; even signs reversed. Yuva = full delivery, Bala/Mrita = weak delivery.
    - `kaal_sarpa`: Kaal Sarpa Dosha detection — `active` boolean, `type` (ascending/descending), `is_partial` (true if any planet shares Rahu/Ketu sign), and `axis` (e.g. "Rahu in Aries / Ketu in Libra").
    - `graha_yuddha`: Planetary War detection — pairs of true planets (Mars–Saturn) within 1° longitude. Reports `winner` (higher longitude), `loser`, `separation` degrees, and `planets` list.
    - `gandanta`: Gandanta junction detection — planets or Lagna within 3°20' of water-fire sign boundaries (Cancer→Leo, Scorpio→Sagittarius, Pisces→Aries). Reports affected planet, `degree`, `junction`, and `gap` from boundary.
    - `arudha_padas`: All 12 Arudha Padas (A1–A12) with sign placements. Includes the BPHS exception rule (same-sign/7th → 10th from house). Key padas: A1 (Arudha Lagna — worldly image), A7 (Dara Pada — spouse perception), A10 (Karma Pada — career reputation).
    - `upapada`: Upapada Lagna (A12) — sign, its lord (planet + sign), and the 2nd house from UL (sustenance of marriage).
    - `karakamsha`: Karakamsha analysis — Atmakaraka's Navamsha sign, house from D1 Lagna, Ishta Devata (planet ruling 12th from Karakamsha), and planets placed in the Karakamsha sign.

    Parameters:
        dob: Date of birth as "YYYY-MM-DD" (e.g. "1990-04-15")
        time: Time of birth as "HH:MM" in 24-hour format (e.g. "14:30")
        lat: Birth latitude as decimal degrees (e.g. 28.6139 for New Delhi)
        lon: Birth longitude as decimal degrees (e.g. 77.2090 for New Delhi)
        timezone: IANA timezone string (e.g. "Asia/Kolkata", "America/New_York")
        query_date: Optional date for Dasha lookup as "YYYY-MM-DD". Defaults to today.
    """
    try:
        return cast_chart(dob, time, lat, lon, timezone, query_date or None)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def cast_transit_chart(
    transit_date: str,
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str = "Asia/Kolkata",
) -> Dict[str, Any]:
    """
    Calculate planetary transits for a given date overlaid on a natal chart.

    Returns (JSON):
    - `planets`: For each transit planet:
      - `sign`, `degree`, `is_retrograde`, `nakshatra`
      - `sav_points`: Ashtakavarga points in the transiting sign
      - `house_from_lagna`, `house_from_moon`
    - `sade_sati`: `{ active, phase, saturn_transit_sign, natal_moon_sign }`
    - `rahu_ketu_axis`: `{ rahu_house_from_lagna, ketu_house_from_lagna, rahu_sign, ketu_sign }`

    Parameters:
        transit_date: The date to compute transits for as "YYYY-MM-DD" (e.g. "2026-02-28")
        dob: Date of birth as "YYYY-MM-DD"
        time: Time of birth as "HH:MM" in 24-hour format
        lat: Birth latitude as decimal degrees
        lon: Birth longitude as decimal degrees
        timezone: IANA timezone string (defaults to "Asia/Kolkata")
    """
    try:
        return cast_transit(transit_date, dob, time, lat, lon, timezone)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def calculate_compatibility_tool(
    dob1: str, time1: str, lat1: float, lon1: float, tz1: str,
    dob2: str, time2: str, lat2: float, lon2: float, tz2: str,
) -> Dict[str, Any]:
    """
    Calculates traditional 36-point Ashtakoot relationship compatibility between two people.
    By tradition, Person 1 (dob1) should be Male and Person 2 (dob2) should be Female for accurate points.

    Returns (JSON):
    - 8 Ashtakoot kutas (total 36 pts): Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi
    - Additional kutas: Mahendra, Stree Deergha, Vedha, Rajju (5-group nakshatra durability), BadConstellations, LagnaHouse7, SexEnergy
    - Exception logic: Nadi mitigated by Bhakoot+Rajju, Rajju mitigated by GrahaMaitri+Bhakoot+Tara+Mahendra
    - Kuja Dosha: per-person Mars/Saturn/Rahu/Ketu/Sun analysis in houses 2,4,7,8,12 with dignity-based scoring and compatibility verdict

    Parameters:
        dob1, time1, lat1, lon1, tz1: Birth details for Person 1 (e.g. "1990-04-15", "14:30")
        dob2, time2, lat2, lon2, tz2: Birth details for Person 2
    """
    try:
        return calculate_compatibility(
            dob1, time1, lat1, lon1, tz1,
            dob2, time2, lat2, lon2, tz2,
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def check_muhurtha_tool(
    activity: str,
    date: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> Dict[str, Any]:
    """
    Check if a date/time is auspicious for a specific activity (electional astrology).

    Evaluates Panchang purity, nakshatra suitability, tithi, weekday, Lagna, and
    activity-specific doshas to determine muhurtha quality. 

    Returns (JSON):
    - `verdict`: "auspicious" / "mixed_favorable" / "mixed" / "inauspicious"
    - `score`: numeric score (positive*10 - negative*15)
    - `positive_factors`, `negative_factors`: specific reasons
    - `panchang_suddhi`: tithi/vara/nakshatra/yoga/karana assessment
    - `marriage_doshas` (marriage only): Sagraha, Shashtashta, Bhrigupta Shatka, Kujaasthama

    Parameters:
        activity: Type of activity — one of 'marriage', 'travel', 'business', 'education', 'house_entry', 'medical'
        date: Date to evaluate as "YYYY-MM-DD"
        time: Time to evaluate as "HH:MM" (24h format)
        lat: Location latitude
        lon: Location longitude
        timezone: IANA timezone string
    """
    try:
        return check_muhurtha(activity, date, time, lat, lon, timezone)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def analyze_career_chart(
    dob: str,
    time: str,
    lat: float,
    lon: float,
    timezone: str,
) -> Dict[str, Any]:
    """
    Analyze career potential using the 10th house, D10 Dashamsha, and planetary significations.

    Returns (JSON):
    - `tenth_house`: lord, sign, occupants, dignity, D10 sign
    - `d10_indicators`: planet-by-planet D10 placements with career domain significations
    - `career_themes`: ranked career domains derived from planetary + sign analysis
    - `strength_factors`: supporting indicators (6th/7th lord connections, etc.)

    Parameters:
        dob: Date of birth as "YYYY-MM-DD"
        time: Time of birth as "HH:MM" (24h)
        lat: Birth latitude
        lon: Birth longitude
        timezone: IANA timezone string
    """
    try:
        return analyze_career(dob, time, lat, lon, timezone)
    except Exception as e:
        return {"error": str(e)}


def main():
    """Console entry point for `rishi-ai-mcp` command."""
    mcp.run()


if __name__ == "__main__":
    main()
