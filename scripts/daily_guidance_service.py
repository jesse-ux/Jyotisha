#!/usr/bin/env python3
"""Positive daily guidance built from auditable chart evidence."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import swisseph as swe
    from ayanamsa_utils import apply_ayanamsa, normalize_ayanamsa_name
    from domain_calculation_service import compute_chart, compute_vimshottari_timeline
except ModuleNotFoundError:
    import swisseph as swe
    from scripts.ayanamsa_utils import apply_ayanamsa, normalize_ayanamsa_name
    from scripts.domain_calculation_service import compute_chart, compute_vimshottari_timeline

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

HOUSE_THEMES = {
    1: ("自我", "整理状态、重启节奏"),
    2: ("财务", "记账、定价、整理资源"),
    3: ("沟通", "发消息、写计划、更新作品"),
    4: ("家庭", "整理空间、处理家宅事务"),
    5: ("创意", "创作、表达、轻松社交"),
    6: ("执行", "清单推进、修正细节"),
    7: ("合作", "谈合作、修复关系、主动连接"),
    8: ("深度", "复盘、研究、清理旧问题"),
    9: ("学习", "学习、发布观点、远程联络"),
    10: ("事业", "推进项目、展示成果、联系上级"),
    11: ("人脉", "社群互动、资源交换"),
    12: ("休整", "休息、收尾、安静准备"),
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _house_from_sign(asc_sign: str | None, transit_sign: str | None) -> int | None:
    if asc_sign not in SIGNS or transit_sign not in SIGNS:
        return None
    return (SIGNS.index(transit_sign) - SIGNS.index(asc_sign)) % 12 + 1


def _chart_from_body(body: dict[str, Any]) -> dict[str, Any]:
    chart = body.get("chart_data") or body.get("chart")
    if isinstance(chart, dict) and chart.get("ascendant") and chart.get("planets"):
        return chart
    return compute_chart(body)


def _moon_transit(reference_date: str, tz: float, ayanamsa: str) -> dict[str, Any]:
    local_dt = datetime.strptime(reference_date[:10], "%Y-%m-%d").replace(hour=12)
    apply_ayanamsa(normalize_ayanamsa_name(ayanamsa), swe)
    jd = swe.julday(local_dt.year, local_dt.month, local_dt.day, 12.0 - float(tz))
    ayanamsa_value = swe.get_ayanamsa(jd)
    position, _flags = swe.calc_ut(jd, swe.MOON)
    longitude = (position[0] - ayanamsa_value) % 360
    sign_index = int(longitude // 30)
    return {
        "planet": "Moon",
        "date": reference_date,
        "longitude": longitude,
        "sign": SIGNS[sign_index],
        "degree_in_sign": longitude % 30,
    }


def _current_dasha(chart: dict[str, Any], reference_date: str) -> dict[str, Any]:
    birth = chart.get("birth_info") or {}
    moon = (chart.get("planets") or {}).get("Moon") or {}
    moon_lon = moon.get("lon", moon.get("degree_raw", moon.get("degree")))
    try:
        birth_dt = datetime(
            _safe_int(birth.get("year")),
            _safe_int(birth.get("month"), 1),
            _safe_int(birth.get("day"), 1),
            _safe_int(birth.get("hour")),
            _safe_int(birth.get("minute")),
            _safe_int(birth.get("second")),
        )
        return compute_vimshottari_timeline(
            birth_dt=birth_dt,
            moon_lon=float(moon_lon),
            current_date=datetime.strptime(reference_date[:10], "%Y-%m-%d"),
        ).get("current_dasha") or {}
    except Exception as exc:
        return {"status": "blocked", "reason": str(exc)}


def build_daily_guidance(body: dict[str, Any]) -> dict[str, Any]:
    reference_date = str(body.get("date") or body.get("reference_date") or datetime.now().strftime("%Y-%m-%d"))[:10]
    chart = _chart_from_body(body)
    birth = chart.get("birth_info") or {}
    tz = float(body.get("tz", birth.get("tz", 0) or 0))
    ayanamsa = str(body.get("ayanamsa") or birth.get("ayanamsa_name") or "lahiri")
    asc_sign = (chart.get("ascendant") or {}).get("sign")
    moon_transit = _moon_transit(reference_date, tz, ayanamsa)
    moon_house = _house_from_sign(asc_sign, moon_transit.get("sign"))
    theme, action = HOUSE_THEMES.get(moon_house or 0, ("今日", "整理计划、稳步推进"))
    dasha = _current_dasha(chart, reference_date)
    dasha_lord = dasha.get("mahadasha_lord") or dasha.get("lord") or dasha.get("md_lord")
    evidence = [
        {
            "layer": "D1",
            "finding": f"本命上升 {asc_sign or 'unknown'}；今日月亮过境第{moon_house or '?'}宫",
            "status": "used" if moon_house else "partial",
        },
        {
            "layer": "Vimshottari",
            "finding": f"当前大运主星 {dasha_lord}" if dasha_lord else "当前大运未能稳定提取",
            "status": "used" if dasha_lord else "blocked",
        },
        {
            "layer": "Daily Transit",
            "finding": f"Moon in {moon_transit.get('sign')} on {reference_date}",
            "status": "used",
        },
    ]
    text = f"今日星语：今日月亮触发你的{theme}主题，当前大运作背景支持把精力放在可推进的小事上。适合{action}；好运来自清楚表达、稳步行动。"
    if len(text) > 100:
        text = f"今日星语：今日月亮触发{theme}主题，适合{action}。把话说清、把事做小，好运来自主动连接与稳步推进。"
    return {
        "success": True,
        "endpoint": "daily_guidance",
        "date": reference_date,
        "daily_star_words": text,
        "word_count": len(text),
        "suggested_actions": [item.strip() for item in action.split("、")],
        "evidence": evidence,
        "audit": {
            "mode": "positive_daily_guidance",
            "not_a_prediction": True,
            "required_layers": ["D1", "Vimshottari", "Daily Transit"],
            "partial_layers": ["D9", "D10", "D2", "Narayana", "Panchanga", "Ashtakavarga"],
        },
    }
