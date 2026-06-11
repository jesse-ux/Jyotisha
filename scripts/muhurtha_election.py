#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Muhurtha（择时占星）完整模块 v1.0
基于 dashaflow (MIT License) muhurtha.py 核心算法适配

支持6类活动的吉祥择时：
- marriage 婚姻
- travel 出行
- business 商业
- education 学业
- house_entry 入宅
- medical 医疗

包含：Panchanga Suddhi五清 + 活动专项规则 + Dosha检测 + 评分
"""

from typing import Dict, List, Optional

# =============================================================================
# 数据表（来自 dashaflow MIT License）
# =============================================================================

# 不吉Panchang Yoga（0-indexed）
BAD_YOGAS = {0, 5, 8, 9, 12, 14, 16, 18, 26}

# 普遍避开的日子
BAD_TITHIS = {4, 6, 8, 12, 14, 30}

# 普遍避开的星宿
BAD_NAKSHATRAS = {"Bharani", "Krittika"}

# 婚姻规则
MARRIAGE_RULES = {
    "good_nakshatras": {"Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta",
                        "Swati", "Anuradha", "Moola", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Taurus", "Gemini", "Cancer", "Virgo", "Libra", "Sagittarius"},
}

# 出行规则
TRAVEL_RULES = {
    "good_nakshatras": {"Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta",
                        "Anuradha", "Shravana", "Dhanishta", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Aries", "Taurus", "Cancer", "Leo", "Libra", "Sagittarius"},
}

# 商业规则
BUSINESS_RULES = {
    "good_nakshatras": {"Ashwini", "Rohini", "Punarvasu", "Pushya", "Uttara Phalguni",
                        "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Monday", "Wednesday", "Thursday", "Friday"},
    "good_moon_signs": {"Taurus", "Cancer", "Virgo", "Libra", "Sagittarius", "Pisces"},
}

# 学业规则
EDUCATION_RULES = {
    "good_nakshatras": {"Ashwini", "Punarvasu", "Pushya", "Hasta", "Chitra",
                        "Swati", "Shravana", "Dhanishta", "Shatabhisha", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_lagnas": {"Gemini", "Virgo", "Sagittarius", "Pisces"},
}

# 入宅规则
HOUSE_ENTRY_RULES = {
    "good_nakshatras": {"Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada",
                        "Shravana", "Dhanishta", "Revati", "Ashwini", "Mrigashira"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Monday", "Wednesday", "Thursday", "Friday"},
}

# 医疗规则
MEDICAL_RULES = {
    "good_nakshatras": {"Ashwini", "Rohini", "Mrigashira", "Pushya", "Hasta",
                        "Chitra", "Swati", "Anuradha", "Shravana", "Revati"},
    "good_tithis": {2, 3, 5, 7, 10, 11, 13},
    "good_weekdays": {"Saturday", "Monday"},
}

ACTIVITY_RULES = {
    "marriage": MARRIAGE_RULES,
    "travel": TRAVEL_RULES,
    "business": BUSINESS_RULES,
    "education": EDUCATION_RULES,
    "house_entry": HOUSE_ENTRY_RULES,
    "medical": MEDICAL_RULES,
}


def check_panchanga_suddhi(tithi_num: int, nakshatra_name: str, yoga_index: int) -> List[str]:
    """检查Panchanga五清（Tithi/Nakshatra/Yoga纯度）"""
    issues = []
    if tithi_num in BAD_TITHIS:
        issues.append(f"不吉日: Tithi #{tithi_num}")
    if nakshatra_name in BAD_NAKSHATRAS:
        issues.append(f"不吉星宿: {nakshatra_name}")
    if yoga_index in BAD_YOGAS:
        issues.append(f"不吉Yoga: #{yoga_index}")
    return issues


def check_marriage_doshas(planets: Dict) -> List[str]:
    """婚姻专项Dosha检测"""
    doshas = []
    moon = planets.get("Moon", {})
    moon_sign = moon.get("sign", "")

    # Sagraha Dosha: Moon conjunct any planet
    for p_name, pd in planets.items():
        if p_name != "Moon" and pd.get("sign") == moon_sign:
            doshas.append(f"Sagraha Dosha: Moon合{p_name}在{moon_sign}")
            break

    # Moon in 6/8/12
    moon_house = moon.get("house", 0)
    if moon_house in (6, 8, 12):
        doshas.append(f"Shashtashta Dosha: Moon在{moon_house}宫")

    # Venus in 6th
    if planets.get("Venus", {}).get("house") == 6:
        doshas.append("Bhrigupta Shatka: Venus在6宫")

    # Mars in 8th
    if planets.get("Mars", {}).get("house") == 8:
        doshas.append("Kujaasthama: Mars在8宫")

    return doshas


def evaluate_muhurtha(activity: str, tithi_num: int, nakshatra_name: str,
                      yoga_index: int, weekday: str = "", lagna_sign: str = "",
                      planets: Optional[Dict] = None) -> Dict:
    """
    评估特定活动的择时吉凶。

    Args:
        activity: 'marriage'|'travel'|'business'|'education'|'house_entry'|'medical'
        tithi_num: 阴历日编号(1-30)
        nakshatra_name: 星宿名称
        yoga_index: Panchang Yoga索引
        weekday: 星期几
        lagna_sign: 上升星座
        planets: 行星位置(用于dosha检测)

    Returns:
        吉凶评估结果
    """
    rules = ACTIVITY_RULES.get(activity)
    if not rules:
        return {"verdict": "error", "reason": f"未知活动: {activity}",
                "activities": list(ACTIVITY_RULES.keys())}

    positive, negative = [], []

    # 1. Panchanga Suddhi
    issues = check_panchanga_suddhi(tithi_num, nakshatra_name, yoga_index)
    negative.extend(issues)

    # 2. Nakshatra
    good_naks = rules.get("good_nakshatras", set())
    if nakshatra_name in good_naks:
        positive.append(f"吉祥星宿: {nakshatra_name}")
    elif nakshatra_name and nakshatra_name not in BAD_NAKSHATRAS:
        negative.append(f"星宿{nakshatra_name}非最佳")

    # 3. Tithi
    good_tithis = rules.get("good_tithis", set())
    if tithi_num in good_tithis:
        positive.append(f"吉祥日: Tithi #{tithi_num}")

    # 4. Weekday
    good_wds = rules.get("good_weekdays")
    if good_wds and weekday:
        if weekday in good_wds:
            positive.append(f"吉祥曜日: {weekday}")
        else:
            negative.append(f"曜日{weekday}非最佳")

    # 5. Lagna
    good_lagnas = rules.get("good_lagnas")
    if good_lagnas and lagna_sign:
        if lagna_sign in good_lagnas:
            positive.append(f"吉祥上升: {lagna_sign}")
        else:
            negative.append(f"上升{lagna_sign}非最佳")

    # 6. Moon sign (business)
    good_moon = rules.get("good_moon_signs")
    if good_moon and planets:
        ms = planets.get("Moon", {}).get("sign", "")
        if ms in good_moon:
            positive.append(f"月亮在吉位: {ms}")
        else:
            negative.append(f"月亮{ms}非最佳")

    # 7. Marriage doshas
    if activity == "marriage" and planets:
        for d in check_marriage_doshas(planets):
            negative.append(f"DOSHA: {d}")

    # 8. 8th house check
    if activity in ("marriage", "medical", "house_entry") and planets:
        for pn, pd in planets.items():
            if pn not in ("Rahu", "Ketu") and pd.get("house") == 8:
                negative.append(f"行星在8宫: {pn}")
                break

    # Scoring
    score = len(positive) * 10 - len(negative) * 15
    has_hard_reject = any("DOSHA:" in n for n in negative)

    if has_hard_reject:
        verdict = "不吉"
    elif len(negative) == 0 and len(positive) >= 2:
        verdict = "大吉"
    elif len(positive) > len(negative):
        verdict = "尚可"
    elif len(negative) > len(positive):
        verdict = "不吉"
    else:
        verdict = "中性"

    return {
        "activity": activity,
        "verdict": verdict,
        "score": max(0, score),
        "positive": positive,
        "negative": negative,
    }
