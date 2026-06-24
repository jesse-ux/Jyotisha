#!/usr/bin/env python3
"""Deep Varga + Avastha interpretation layer for user-facing reports."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from avastha_calculator import AvasthaCalculator
from divisional_charts_extended import DivisionalChartsCalculator, VargaType
from trimshamsa_d30 import calc_d30_chart


SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
CLASSICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
KEY_PLANETS = {
    "D24": ["Mercury", "Jupiter", "Moon", "Sun"],
    "D30": ["Mars", "Saturn", "Rahu", "Ketu", "Venus"],
    "D60": ["Sun", "Moon", "Jupiter", "Saturn", "Ketu"],
}
TRIK_HOUSES = {6, 8, 12}
KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}


def build_deep_varga_avastha_report(planet_lons: Dict[str, float], asc_lon: float = 0.0) -> Dict:
    """Build Sayanadi/Shayanadi avastha and D24/D30/D60 interpretive templates."""
    normalized_lons = {
        planet: float(lon) % 360
        for planet, lon in planet_lons.items()
        if _is_number(lon)
    }
    if not normalized_lons:
        raise ValueError("planet_lons must include longitude data")

    avastha_summary = _build_avastha_summary(normalized_lons, asc_lon)
    deep_templates = _build_deep_varga_templates(normalized_lons, asc_lon)
    priority_cards = _priority_cards(avastha_summary, deep_templates)
    return {
        "method": "Sayanadi/Shayanadi Avastha + D24/D30/D60 Deep Templates",
        "source": "avastha_calculator.py + divisional_charts_extended.py + trimshamsa_d30.py",
        "summary": {
            "headline": _headline(avastha_summary, deep_templates),
            "priority_cards": priority_cards,
            "next_action": "把 D24 用于学习与证书，D30 用于风险压力，D60 用于根层业力；必须与 D1、Dasha、Transit 同读。",
        },
        "avastha_summary": avastha_summary,
        "deep_varga_templates": deep_templates,
    }


def _build_avastha_summary(planet_lons: Dict[str, float], asc_lon: float) -> Dict:
    calculator = AvasthaCalculator()
    planet_states = {}
    state_counter: Counter[str] = Counter()
    weak_planets = []
    strong_planets = []
    asc_sign_idx = _sign_idx(asc_lon)
    for planet in CLASSICAL_PLANETS:
        lon = planet_lons.get(planet)
        if lon is None:
            continue
        sign_idx = _sign_idx(lon)
        degree = lon % 30
        house = ((sign_idx - asc_sign_idx) % 12) + 1
        result = calculator.calculate_all_avasthas(
            planet,
            SIGNS[sign_idx],
            degree,
            house,
            conjunctions=_conjunctions_for(planet, planet_lons),
            aspects=[],
            is_combust=False,
            is_retrograde=False,
        )
        avasthas = result.get("avasthas", {})
        shayanadi = avasthas.get("Shayanadi", {})
        bala = avasthas.get("Bala", {})
        state_counter[shayanadi.get("state", "unknown")] += 1
        strength = float(bala.get("strength") or 0)
        row = {
            "planet": planet,
            "sign": SIGNS[sign_idx],
            "house": house,
            "Bala": bala,
            "Jagrat": avasthas.get("Jagrat", {}),
            "Deeptadi": avasthas.get("Deeptadi", {}),
            "Lajjitadi": avasthas.get("Lajjitadi", {}),
            "Shayanadi": shayanadi,
            "interpretation": result.get("interpretation", ""),
            "remedies": result.get("remedies", []),
        }
        planet_states[planet] = row
        if strength >= 0.7:
            strong_planets.append({"planet": planet, "strength": strength, "state": bala.get("state")})
        elif strength <= 0.5:
            weak_planets.append({"planet": planet, "strength": strength, "state": bala.get("state")})
    return {
        "dominant_states": [{"state": state, "count": count} for state, count in state_counter.most_common()],
        "strong_planets": strong_planets,
        "weak_planets": weak_planets,
        "planet_states": planet_states,
        "next_action": "优先复核弱 Bala 或 Nidra/Shayana 行星对应的 Dasha；强 Bala 行星可作为可用资源。",
    }


def _build_deep_varga_templates(planet_lons: Dict[str, float], asc_lon: float) -> Dict:
    calc = DivisionalChartsCalculator()
    selected = {
        "D24": VargaType.D24,
        "D30": VargaType.D30,
        "D60": VargaType.D60,
    }
    templates = {}
    for key, varga_type in selected.items():
        chart = calc._calculate_single_varga(varga_type, planet_lons, asc_lon)
        if key == "D24":
            templates[key] = _d24_template(chart)
        elif key == "D30":
            d30_chart = calc_d30_chart(planet_lons, asc_lon)
            templates[key] = _d30_template(chart, d30_chart)
        else:
            templates[key] = _d60_template(chart)
    return templates


def _d24_template(chart: Dict) -> Dict:
    cards = _key_planet_cards(chart, "D24")
    support = [card for card in cards if card["house"] in KENDRA_TRIKONA]
    pressure = [card for card in cards if card["house"] in TRIK_HOUSES]
    return {
        "division": "D24",
        "theme": "education_learning",
        "title": "D24 Chaturvimsamsa 学习/证书模板",
        "template_cards": cards,
        "support_factors": support,
        "risk_flags": [{"planet": card["planet"], "reason": "D24 trika house pressure"} for card in pressure],
        "next_action": "用 Mercury/Jupiter/Moon 判断学习方式、考试状态和导师资源；再与 Dasha 的教育触发交叉。",
    }


def _d30_template(chart: Dict, d30_chart: Dict) -> Dict:
    cards = _key_planet_cards(chart, "D30")
    risk_flags = []
    concentration = d30_chart.get("malefic_concentration") or {}
    if concentration.get("risk_level"):
        risk_flags.append({"type": "malefic_concentration", "reason": concentration.get("risk_level")})
    for card in cards:
        if card["house"] in TRIK_HOUSES:
            risk_flags.append({"planet": card["planet"], "reason": f"D30 house {card['house']} pressure"})
    return {
        "division": "D30",
        "theme": "risk_crisis",
        "title": "D30 Trimsamsa 压力/危机模板",
        "template_cards": cards,
        "risk_flags": risk_flags,
        "planet_states": d30_chart.get("planet_states", {}),
        "malefic_concentration": concentration,
        "next_action": "D30 只用于风险侧证；健康、法律、事故等主题必须分开现实建议与占星提示。",
    }


def _d60_template(chart: Dict) -> Dict:
    cards = _key_planet_cards(chart, "D60")
    rooted = [card for card in cards if card["house"] in KENDRA_TRIKONA]
    lessons = [card for card in cards if card["house"] in TRIK_HOUSES]
    return {
        "division": "D60",
        "theme": "karma_root",
        "title": "D60 Shashtiamsa 根层业力模板",
        "template_cards": cards,
        "support_factors": rooted,
        "risk_flags": [{"planet": card["planet"], "reason": "D60 trika karmic lesson"} for card in lessons],
        "next_action": "D60 对出生时间极敏感；若出生时间未精确校正，只把它作为背景主题，不作为事件承诺。",
    }


def _key_planet_cards(chart: Dict, division: str) -> List[Dict]:
    planets = chart.get("planets", {})
    cards = []
    for planet in KEY_PLANETS.get(division, CLASSICAL_PLANETS):
        item = planets.get(planet)
        if not item:
            continue
        house = int(item.get("house") or 0)
        cards.append({
            "planet": planet,
            "sign": item.get("sign"),
            "house": house,
            "degree": item.get("degree"),
            "role": _planet_role(division, planet),
            "reading": _varga_reading(division, planet, house),
        })
    return cards


def _priority_cards(avastha_summary: Dict, templates: Dict) -> List[Dict]:
    cards = []
    weak = avastha_summary.get("weak_planets") or []
    if weak:
        cards.append({
            "title": "Avastha 需补强",
            "value": ", ".join(item["planet"] for item in weak[:3]),
            "note": "弱 Bala / 不活跃状态会降低对应 Dasha 兑现质量。",
        })
    for division in ("D24", "D30", "D60"):
        template = templates.get(division, {})
        flags = template.get("risk_flags") or []
        cards.append({
            "title": division,
            "value": template.get("title", division),
            "note": f"{len(flags)} 个风险/压力标记；{len(template.get('template_cards') or [])} 个关键行星。",
        })
    return cards


def _headline(avastha_summary: Dict, templates: Dict) -> str:
    states = avastha_summary.get("dominant_states") or []
    top_state = states[0]["state"] if states else "unknown"
    d30_flags = len((templates.get("D30") or {}).get("risk_flags") or [])
    return f"主导 Shayanadi 状态为 {top_state}；D30 发现 {d30_flags} 个压力标记。"


def _planet_role(division: str, planet: str) -> str:
    roles = {
        "D24": {"Mercury": "学习方法", "Jupiter": "导师/高等教育", "Moon": "记忆与适应", "Sun": "证书与权威"},
        "D30": {"Mars": "冲突/急性风险", "Saturn": "慢性压力", "Rahu": "异常风险", "Ketu": "切断/损失", "Venus": "关系压力"},
        "D60": {"Sun": "根层使命", "Moon": "潜意识模式", "Jupiter": "福德", "Saturn": "业力课题", "Ketu": "前缘/释放"},
    }
    return roles.get(division, {}).get(planet, "key planet")


def _varga_reading(division: str, planet: str, house: int) -> str:
    if house in KENDRA_TRIKONA:
        return f"{planet} 在 {division} 的 {house} 宫，作为该主题的可用支撑。"
    if house in TRIK_HOUSES:
        return f"{planet} 在 {division} 的 {house} 宫，提示该主题需要谨慎与现实复核。"
    return f"{planet} 在 {division} 的 {house} 宫，作为中性背景证据。"


def _conjunctions_for(target: str, planet_lons: Dict[str, float], orb: float = 8.0) -> List[str]:
    target_lon = planet_lons.get(target)
    if target_lon is None:
        return []
    result = []
    for planet, lon in planet_lons.items():
        if planet == target:
            continue
        if abs(((lon - target_lon + 180) % 360) - 180) <= orb:
            result.append(planet)
    return result


def _sign_idx(lon: float) -> int:
    return int((float(lon) % 360) / 30) % 12


def _is_number(value: object) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False
