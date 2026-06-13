#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ashtakoot 合婚（36点匹配）+ Kuja Dosha + 附加 Kuta
基于 dashaflow/matchmaking.py (MIT License) 适配

8 个标准 Kuta (36点):
1. Varna (1) — 社会阶层兼容性
2. Vashya (2) — 控制力兼容性
3. Tara (3) — 星宿距离吉凶
4. Yoni (4) — 性格/本能兼容性
5. Graha Maitri (5) — 行星友谊
6. Gana (6) — 气质类型
7. Bhakoot (7) — 星座相对位置
8. Nadi (8) — 生理体质

附加 Kuta:
9. Mahendra — 长寿/子嗣
10. Stree Deergha — 丈夫长寿
11. Vedha — 障碍对
12. Rajju — 婚姻寿命
13. Bad Constellations — 凶宿
14. Lagna House7 — 上升/7宫交叉
15. Sex Energy — 性能量匹配
16. Kuja Dosha — 火星凶相分析
"""

import math
from typing import Dict, Optional

# ============================================================================
# 常量
# ============================================================================
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

# 27 宿数据
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
    "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury"
]

YONI_ANIMALS = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat",
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer",
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant"
]

YONI_ENEMIES = {
    "Horse": "Buffalo", "Buffalo": "Horse",
    "Elephant": "Lion", "Lion": "Elephant",
    "Sheep": "Monkey", "Monkey": "Sheep",
    "Serpent": "Mongoose", "Mongoose": "Serpent",
    "Dog": "Deer", "Deer": "Dog",
    "Cat": "Rat", "Rat": "Cat",
    "Cow": "Tiger", "Tiger": "Cow"
}

GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"
]

NADI = [
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya",
    "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi",
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya"
]

VARNA = {
    "Cancer": 1, "Scorpio": 1, "Pisces": 1,
    "Aries": 2, "Leo": 2, "Sagittarius": 2,
    "Taurus": 3, "Virgo": 3, "Capricorn": 3,
    "Gemini": 4, "Libra": 4, "Aquarius": 4
}

VASHYA_TYPE = {
    "Aries": "Chatushpada", "Taurus": "Chatushpada",
    "Leo": "Vanachara", "Sagittarius": "Chatushpada",
    "Capricorn": "Chatushpada",
    "Gemini": "Manava", "Virgo": "Manava", "Libra": "Manava",
    "Aquarius": "Manava",
    "Cancer": "Jalachara", "Pisces": "Jalachara",
    "Scorpio": "Keet",
}

VASHYA_MATRIX = {
    ("Chatushpada", "Chatushpada"): 2.0, ("Manava", "Manava"): 2.0,
    ("Jalachara", "Jalachara"): 2.0, ("Vanachara", "Vanachara"): 2.0,
    ("Keet", "Keet"): 2.0,
    ("Chatushpada", "Manava"): 0.5, ("Manava", "Chatushpada"): 0.5,
    ("Manava", "Jalachara"): 1.0, ("Jalachara", "Manava"): 1.0,
    ("Chatushpada", "Jalachara"): 0.5, ("Jalachara", "Chatushpada"): 0.5,
    ("Vanachara", "Chatushpada"): 0.0, ("Chatushpada", "Vanachara"): 0.0,
    ("Keet", "Chatushpada"): 0.0, ("Chatushpada", "Keet"): 0.0,
    ("Vanachara", "Manava"): 0.5, ("Manava", "Vanachara"): 0.5,
    ("Keet", "Manava"): 0.5, ("Manava", "Keet"): 0.5,
    ("Vanachara", "Jalachara"): 0.5, ("Jalachara", "Vanachara"): 0.5,
    ("Keet", "Jalachara"): 1.0, ("Jalachara", "Keet"): 1.0,
    ("Vanachara", "Keet"): 1.0, ("Keet", "Vanachara"): 1.0,
}

FRIENDSHIP = {
    'Sun': {'friend': ['Moon', 'Mars', 'Jupiter'], 'enemy': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
    'Moon': {'friend': ['Sun', 'Mercury'], 'enemy': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
    'Mars': {'friend': ['Sun', 'Moon', 'Jupiter'], 'enemy': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
    'Mercury': {'friend': ['Sun', 'Venus'], 'enemy': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
    'Jupiter': {'friend': ['Sun', 'Moon', 'Mars'], 'enemy': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
    'Venus': {'friend': ['Mercury', 'Saturn'], 'enemy': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
    'Saturn': {'friend': ['Mercury', 'Venus'], 'enemy': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
}

VEDHA_PAIRS = [
    (0, 17), (1, 16), (2, 15), (3, 14), (5, 21), (6, 20),
    (7, 19), (8, 18), (9, 26), (10, 25), (11, 24), (12, 23), (4, 22),
]

RAJJU_GROUPS = {
    "Pada":  {0, 8, 9, 17, 18, 26},
    "Kati":  {1, 7, 10, 16, 25, 19},
    "Udara": {2, 6, 11, 15, 20, 24},
    "Kanta": {3, 5, 12, 14, 21, 23},
    "Sira":  {4, 13, 22},
}

RAJJU_EFFECTS = {
    "Sira": "head — risk to husband's longevity",
    "Kanta": "neck — risk to wife's longevity",
    "Udara": "stomach — risk to children",
    "Kati": "waist — poverty may ensue",
    "Pada": "foot — couple may be always wandering",
}

# Kuja Dosha
DOSHA_HOUSES = {2, 4, 7, 8, 12}
HIGH_SEVERITY_HOUSES = {7, 8}
MARS_EXCEPTIONS = {
    2: {"Gemini", "Virgo"}, 12: {"Taurus", "Libra"},
    4: {"Aries", "Scorpio"}, 7: {"Capricorn", "Cancer"},
    8: {"Sagittarius", "Pisces"},
}
MARS_EXEMPT_SIGNS = {"Aquarius", "Leo"}

EXALTATION_DEG = {
    'Sun': 10.0, 'Moon': 33.0, 'Mars': 298.0, 'Mercury': 165.0,
    'Jupiter': 95.0, 'Venus': 357.0, 'Saturn': 200.0
}

OWN_SIGNS = {
    'Sun': {'Leo'}, 'Moon': {'Cancer'}, 'Mars': {'Aries', 'Scorpio'},
    'Mercury': {'Gemini', 'Virgo'}, 'Jupiter': {'Sagittarius', 'Pisces'},
    'Venus': {'Taurus', 'Libra'}, 'Saturn': {'Capricorn', 'Aquarius'}
}


# ============================================================================
# 辅助函数
# ============================================================================
def get_nakshatra(moon_lon: float) -> Dict:
    """从月亮经度计算星宿索引、名称和 pada"""
    nak_span = 360.0 / 27  # 13.333°
    nak_idx = int(moon_lon / nak_span) % 27
    pada = int(((moon_lon % nak_span) / nak_span) * 4) + 1
    return {
        "index": nak_idx,
        "name": NAKSHATRA_NAMES[nak_idx],
        "lord": NAKSHATRA_LORDS[nak_idx],
        "pada": pada,
    }


# ============================================================================
# 8 个标准 Kuta
# ============================================================================
def calc_varna(m_sign: str, f_sign: str) -> float:
    m_varna = VARNA.get(m_sign, 4)
    f_varna = VARNA.get(f_sign, 4)
    return 1.0 if m_varna <= f_varna else 0.0


def calc_vashya(m_sign: str, f_sign: str) -> float:
    if m_sign == f_sign:
        return 2.0
    m_type = VASHYA_TYPE.get(m_sign, "Manava")
    f_type = VASHYA_TYPE.get(f_sign, "Manava")
    return VASHYA_MATRIX.get((m_type, f_type), 1.0)


def calc_tara(m_nak_idx: int, f_nak_idx: int) -> float:
    m_to_f = (f_nak_idx - m_nak_idx) % 9
    f_to_m = (m_nak_idx - f_nak_idx) % 9
    pts = 0.0
    if m_to_f not in (2, 4, 6): pts += 1.5
    if f_to_m not in (2, 4, 6): pts += 1.5
    return pts


def calc_yoni(m_nak_idx: int, f_nak_idx: int) -> float:
    m_yoni = YONI_ANIMALS[m_nak_idx]
    f_yoni = YONI_ANIMALS[f_nak_idx]
    if m_yoni == f_yoni:
        return 4.0
    if YONI_ENEMIES.get(m_yoni) == f_yoni:
        return 0.0
    return 2.0


def calc_graha_maitri(m_sign: str, f_sign: str) -> float:
    m_lord = SIGN_LORDS.get(m_sign, '')
    f_lord = SIGN_LORDS.get(f_sign, '')

    def _friendship(p1, p2):
        if p1 == p2:
            return 1.0
        rel = FRIENDSHIP.get(p1, {})
        if p2 in rel.get('friend', []):
            return 1.0
        if p2 in rel.get('enemy', []):
            return 0.0
        return 0.5

    m_to_f = _friendship(m_lord, f_lord)
    f_to_m = _friendship(f_lord, m_lord)
    total = m_to_f + f_to_m
    if total == 2.0: return 5.0
    if total == 1.5: return 4.0
    if total == 1.0: return 3.0
    if total == 0.5: return 1.0
    return 0.0


def calc_gana(m_nak_idx: int, f_nak_idx: int) -> float:
    m_gana = GANA[m_nak_idx]
    f_gana = GANA[f_nak_idx]
    if m_gana == f_gana: return 6.0
    if m_gana == "Deva" and f_gana == "Manushya": return 6.0
    if m_gana == "Manushya" and f_gana == "Deva": return 5.0
    if m_gana == "Rakshasa" and f_gana == "Manushya": return 0.0
    if f_gana == "Rakshasa" and m_gana == "Manushya": return 0.0
    if m_gana == "Rakshasa" and f_gana == "Deva": return 1.0
    if f_gana == "Rakshasa" and m_gana == "Deva": return 0.0
    return 0.0


def calc_bhakoot(m_sign: str, f_sign: str) -> float:
    m_idx = SIGNS.index(m_sign) if m_sign in SIGNS else 0
    f_idx = SIGNS.index(f_sign) if f_sign in SIGNS else 0
    diff = (f_idx - m_idx) % 12 + 1
    if diff in (1, 7, 3, 11, 4, 10):
        return 7.0
    return 0.0


def calc_nadi(m_nak_idx: int, f_nak_idx: int) -> float:
    m_nadi = NADI[m_nak_idx]
    f_nadi = NADI[f_nak_idx]
    return 8.0 if m_nadi != f_nadi else 0.0


# ============================================================================
# 附加 Kuta
# ============================================================================
def calc_mahendra(m_nak_idx: int, f_nak_idx: int) -> str:
    count = ((m_nak_idx - f_nak_idx) % 27) + 1
    return "good" if count in (4, 7, 10, 13, 16, 19, 22, 25) else "bad"


def calc_stree_deergha(m_nak_idx: int, f_nak_idx: int) -> str:
    count = ((m_nak_idx - f_nak_idx) % 27) + 1
    return "good" if count >= 9 else "bad"


def calc_vedha(m_nak_idx: int, f_nak_idx: int) -> str:
    for a, b in VEDHA_PAIRS:
        if (m_nak_idx == a and f_nak_idx == b) or (m_nak_idx == b and f_nak_idx == a):
            return "bad"
    return "good"


def calc_rajju(m_nak_idx: int, f_nak_idx: int) -> Dict:
    def _group(idx):
        for g, indices in RAJJU_GROUPS.items():
            if idx in indices:
                return g
        return None
    m_group = _group(m_nak_idx)
    f_group = _group(f_nak_idx)
    if m_group and f_group and m_group == f_group:
        return {"result": "bad", "group": m_group, "effect": RAJJU_EFFECTS.get(m_group, "")}
    return {"result": "good", "group": None, "effect": ""}


def calc_bad_constellations(m_nak_idx: int, m_pada: int, f_nak_idx: int, f_pada: int) -> Dict:
    issues = []
    if m_nak_idx == 18 and m_pada == 1:
        issues.append("Male born in Moola 1st pada — risk to father-in-law.")
    if f_nak_idx == 18 and f_pada == 1:
        issues.append("Female born in Moola 1st pada — risk to father-in-law.")
    if f_nak_idx == 8 and f_pada == 1:
        issues.append("Female born in Ashlesha 1st pada — risk to husband's mother.")
    if f_nak_idx == 17 and f_pada == 1:
        issues.append("Female born in Jyeshtha 1st pada — risk to husband's elder brother.")
    if f_nak_idx == 15 and f_pada == 4:
        issues.append("Female born in Vishakha 4th pada — risk to husband's younger brother.")
    return {"result": "bad" if issues else "good", "issues": issues}


def calc_lagna_house7(chart1: Dict, chart2: Dict) -> Dict:
    m_lagna = chart1.get("lagna", {}).get("sign")
    f_lagna = chart2.get("lagna", {}).get("sign")
    m_moon = chart1.get("planets", {}).get("Moon", {}).get("sign")
    f_moon = chart2.get("planets", {}).get("Moon", {}).get("sign")

    if (f_moon and m_lagna and f_moon == m_lagna) or (m_moon and f_lagna and m_moon == f_lagna):
        return {"result": "good", "description": "Moon-Lagna cross match — mutual understanding."}

    if m_lagna and f_lagna:
        m_idx = SIGNS.index(m_lagna) if m_lagna in SIGNS else 0
        f_idx = SIGNS.index(f_lagna) if f_lagna in SIGNS else 0
        m_7th = SIGNS[(m_idx + 6) % 12]
        f_7th = SIGNS[(f_idx + 6) % 12]
        m_7lord = SIGN_LORDS[m_7th]
        f_7lord = SIGN_LORDS[f_7th]
        m_7lord_sign = chart1.get("planets", {}).get(m_7lord, {}).get("sign")
        f_7lord_sign = chart2.get("planets", {}).get(f_7lord, {}).get("sign")
        if m_7lord_sign == f_lagna or f_7lord_sign == m_lagna:
            return {"result": "good", "description": "7th house lord cross-placement — marriage stability."}

    return {"result": "neutral", "description": "No special Lagna-7th connection."}


# ============================================================================
# Kuja Dosha (Manglik 分析)
# ============================================================================
def _planet_dignity_level(planet_name: str, sign: str) -> str:
    exalt_sign = SIGNS[int(EXALTATION_DEG.get(planet_name, 999) / 30) % 12]
    debil_sign = SIGNS[int((EXALTATION_DEG.get(planet_name, 0) + 180) / 30) % 12]
    if sign == exalt_sign: return "exalted"
    if planet_name in OWN_SIGNS and sign in OWN_SIGNS[planet_name]: return "own"
    lord = SIGN_LORDS.get(sign, '')
    rel = FRIENDSHIP.get(planet_name, {})
    if lord in rel.get('friend', []): return "friendly"
    if lord in rel.get('enemy', []): return "enemy"
    if sign == debil_sign: return "debilitated"
    return "neutral"


def calc_kuja_dosha(chart: Dict) -> Dict:
    """计算完整的 Kuja Dosha（火星凶相分析）"""
    planets = chart.get("planets", {})

    dosha_scores_high = {
        "Mars": {"debilitated": 100, "enemy": 90, "neutral": 80, "friendly": 70, "own": 60, "exalted": 50},
        "Saturn": {"debilitated": 75, "enemy": 67.5, "neutral": 60, "friendly": 52.5, "own": 45, "exalted": 37.5},
        "Sun": {"debilitated": 50, "enemy": 45, "neutral": 40, "friendly": 35, "own": 30, "exalted": 25},
    }
    dosha_scores_low = {
        "Mars": {"debilitated": 50, "enemy": 45, "neutral": 40, "friendly": 35, "own": 30, "exalted": 25},
        "Saturn": {"debilitated": 37.5, "enemy": 33.75, "neutral": 30, "friendly": 26.25, "own": 22.5, "exalted": 18.75},
        "Sun": {"debilitated": 25, "enemy": 22.5, "neutral": 20, "friendly": 17.5, "own": 15, "exalted": 12.5},
    }

    total = 0.0
    breakdown = {}
    for p_name in ("Mars", "Saturn", "Rahu", "Ketu", "Sun"):
        pd = planets.get(p_name)
        if not pd:
            continue
        house = pd.get("house", 0)
        sign = pd.get("sign", "")
        if house not in DOSHA_HOUSES:
            continue

        # Mars exceptions
        if p_name == "Mars":
            if sign in MARS_EXEMPT_SIGNS:
                continue
            if house in MARS_EXCEPTIONS and sign in MARS_EXCEPTIONS[house]:
                continue

        dig = _planet_dignity_level(p_name, sign)
        score_table = dosha_scores_high if house in HIGH_SEVERITY_HOUSES else dosha_scores_low
        table = score_table.get(p_name, score_table.get("Saturn", {}))
        score = table.get(dig, 60 if house in HIGH_SEVERITY_HOUSES else 30)
        if score > 0:
            breakdown[p_name] = {"house": house, "sign": sign, "dignity": dig, "score": score}
        total += score

    return {"total_score": round(total, 2), "breakdown": breakdown, "is_manglik": total > 0}


def match_kuja_dosha(male_score: float, female_score: float) -> Dict:
    diff = male_score - female_score
    if abs(diff) <= 5:
        return {"result": "good", "description": "Kuja Dosha balanced."}
    if diff < -5:
        return {"result": "bad", "description": "Female has significantly more Kuja Dosha."}
    if female_score > 0 and diff < female_score * 0.25:
        return {"result": "acceptable", "description": "Male has more Kuja Dosha but within tolerance."}
    return {"result": "bad", "description": "Male has significantly more Kuja Dosha."}


# ============================================================================
# 主函数
# ============================================================================
def calculate_ashtakoot(male_moon_lon: float, female_moon_lon: float,
                        male_chart: Optional[Dict] = None,
                        female_chart: Optional[Dict] = None) -> Dict:
    """
    完整的 Ashtakoot 36点合婚 + 附加 Kuta + Kuja Dosha
    
    Args:
        male_moon_lon: 男方月亮恒星黄道经度
        female_moon_lon: 女方月亮恒星黄道经度
        male_chart: 男方完整星盘（可选，用于附加 Kuta）
        female_chart: 女方完整星盘（可选，用于附加 Kuta）
    """
    m_nak = get_nakshatra(male_moon_lon)
    f_nak = get_nakshatra(female_moon_lon)
    m_nak_idx = m_nak["index"]
    f_nak_idx = f_nak["index"]

    m_sign_idx = int((male_moon_lon % 360) / 30)
    f_sign_idx = int((female_moon_lon % 360) / 30)
    m_sign = SIGNS[m_sign_idx]
    f_sign = SIGNS[f_sign_idx]

    # 8 标准 Kuta
    scores = {
        "Varna": calc_varna(m_sign, f_sign),
        "Vashya": calc_vashya(m_sign, f_sign),
        "Tara": calc_tara(m_nak_idx, f_nak_idx),
        "Yoni": calc_yoni(m_nak_idx, f_nak_idx),
        "GrahaMaitri": calc_graha_maitri(m_sign, f_sign),
        "Gana": calc_gana(m_nak_idx, f_nak_idx),
        "Bhakoot": calc_bhakoot(m_sign, f_sign),
        "Nadi": calc_nadi(m_nak_idx, f_nak_idx),
    }
    total_score = sum(scores.values())

    # 附加 Kuta
    rajju_result = calc_rajju(m_nak_idx, f_nak_idx)
    additional_kutas = {
        "Mahendra": calc_mahendra(m_nak_idx, f_nak_idx),
        "StreeDeergha": calc_stree_deergha(m_nak_idx, f_nak_idx),
        "Vedha": calc_vedha(m_nak_idx, f_nak_idx),
        "Rajju": rajju_result,
        "BadConstellations": calc_bad_constellations(
            m_nak_idx, m_nak.get("pada", 0), f_nak_idx, f_nak.get("pada", 0)),
    }

    # 星盘依赖的 Kuta
    kuja_male = None
    kuja_female = None
    kuja_match = None
    if male_chart and female_chart:
        additional_kutas["LagnaHouse7"] = calc_lagna_house7(male_chart, female_chart)
        kuja_male = calc_kuja_dosha(male_chart)
        kuja_female = calc_kuja_dosha(female_chart)
        kuja_match = match_kuja_dosha(
            kuja_male.get("total_score", 0), kuja_female.get("total_score", 0))

    # 例外逻辑
    exceptions = []
    if scores["Nadi"] == 0:
        if scores["Bhakoot"] > 0 and rajju_result["result"] == "good":
            exceptions.append("Nadi Dosha mitigated by good Bhakoot and Rajju.")
    if rajju_result["result"] == "bad":
        if (scores["GrahaMaitri"] >= 4.0 and scores["Bhakoot"] > 0 and
                scores["Tara"] >= 1.5 and additional_kutas["Mahendra"] == "good"):
            exceptions.append("Rajju Dosha mitigated by good Graha Maitri, Bhakoot, Tara, and Mahendra.")
    if additional_kutas["StreeDeergha"] == "bad":
        if scores["Bhakoot"] > 0 and scores["GrahaMaitri"] >= 4.0:
            exceptions.append("Stree Deergha Dosha mitigated by good Bhakoot and Graha Maitri.")

    # 综合判定
    is_match = total_score >= 18.0 and (scores["Nadi"] > 0 or len(exceptions) > 0)

    return {
        "method": "Ashtakoot 36-point Matching + Additional Kutas (v6.9.12, MIT: dashaflow)",
        "male_details": {
            "moon_sign": m_sign,
            "nakshatra": m_nak["name"],
            "nakshatra_pada": m_nak["pada"],
            "gana": GANA[m_nak_idx],
            "nadi": NADI[m_nak_idx],
            "yoni": YONI_ANIMALS[m_nak_idx],
        },
        "female_details": {
            "moon_sign": f_sign,
            "nakshatra": f_nak["name"],
            "nakshatra_pada": f_nak["pada"],
            "gana": GANA[f_nak_idx],
            "nadi": NADI[f_nak_idx],
            "yoni": YONI_ANIMALS[f_nak_idx],
        },
        "scores": scores,
        "total_score": total_score,
        "max_score": 36.0,
        "match_percentage": round(total_score / 36.0 * 100, 1),
        "additional_kutas": additional_kutas,
        "exceptions": exceptions,
        "kuja_dosha_male": kuja_male,
        "kuja_dosha_female": kuja_female,
        "kuja_dosha_match": kuja_match,
        "is_match_approved": is_match,
    }
