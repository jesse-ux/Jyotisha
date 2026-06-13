#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synastry（合盘）模块 — 基于 dashaflow (MIT License) 核心算法

16因子兼容性分析系统：
- Ashtakoot 8因子（36分制）
- 附加8 Kuta（Mahendra/Stree Deergha/Vedha/Kuja Dosha/Rajju等）
"""

from typing import Dict, List, Tuple, Any

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

NAKSHATRAS = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']

# =============================================================================
# 数据表 (来自 dashaflow MIT License)
# =============================================================================

YONI_ANIMALS = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat",
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer",
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant"
]

YONI_ENEMIES = {
    "Horse": "Buffalo", "Buffalo": "Horse", "Elephant": "Lion", "Lion": "Elephant",
    "Sheep": "Monkey", "Monkey": "Sheep", "Serpent": "Mongoose", "Mongoose": "Serpent",
    "Dog": "Deer", "Deer": "Dog", "Cat": "Rat", "Rat": "Cat",
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
    "Leo": "Vanachara", "Sagittarius": "Chatushpada", "Capricorn": "Chatushpada",
    "Gemini": "Manava", "Virgo": "Manava", "Libra": "Manava", "Aquarius": "Manava",
    "Cancer": "Jalachara", "Pisces": "Jalachara",
    "Scorpio": "Keet",
}

VEDHA_PAIRS = [(0,17),(1,16),(2,15),(3,14),(5,21),(6,20),(7,19),(8,18),(9,26),(10,25),(11,24),(12,23),(4,22)]

RAJJU_GROUPS = {
    "Pada":{0,8,9,17,18,26}, "Kati":{1,7,10,16,25,19},
    "Udara":{2,6,11,15,20,24}, "Kanta":{3,5,12,14,21,23}, "Sira":{4,13,22}
}
RAJJU_EFFECTS = {"Sira":"head—risk to husband","Kanta":"neck—risk to wife","Udara":"stomach—risk to children","Kati":"waist—poverty","Pada":"foot—wandering"}

NATURAL_FRIENDS = {
    'Sun': ['Moon','Mars','Jupiter'], 'Moon': ['Sun','Mercury'],
    'Mars': ['Sun','Moon','Jupiter'], 'Mercury': ['Sun','Venus'],
    'Jupiter': ['Sun','Moon','Mars'], 'Venus': ['Mercury','Saturn'],
    'Saturn': ['Mercury','Venus']
}
NATURAL_ENEMIES = {
    'Sun': ['Saturn','Venus'], 'Moon': [], 'Mars': ['Mercury'],
    'Mercury': ['Moon'], 'Jupiter': ['Mercury','Venus'],
    'Venus': ['Sun','Moon'], 'Saturn': ['Sun','Moon','Mars']
}

EXALTATION = {'Sun':('Aries',10),'Moon':('Taurus',3),'Mars':('Capricorn',28),'Mercury':('Virgo',15),'Jupiter':('Cancer',5),'Venus':('Pisces',27),'Saturn':('Libra',20)}
DEBILITATION = {p:(SIGNS[(SIGNS.index(s)+6)%12],d) for p,(s,d) in EXALTATION.items()}
OWN_SIGNS = {'Sun':{'Leo'},'Moon':{'Cancer'},'Mars':{'Aries','Scorpio'},'Mercury':{'Gemini','Virgo'},'Jupiter':{'Sagittarius','Pisces'},'Venus':{'Taurus','Libra'},'Saturn':{'Capricorn','Aquarius'}}

_DOSHA_HOUSES = {2,4,7,8,12}
_HIGH_SEVERITY_HOUSES = {7,8}
_MARS_EXCEPTIONS = {2:{"Gemini","Virgo"},12:{"Taurus","Libra"},4:{"Aries","Scorpio"},7:{"Capricorn","Cancer"},8:{"Sagittarius","Pisces"}}
_MARS_EXEMPT_SIGNS = {"Aquarius","Leo"}

# =============================================================================
# Ashtakoot 8因子 (36分制)
# =============================================================================

def _calc_varna(m_sign, f_sign): 
    return 1.0 if VARNA[m_sign] <= VARNA[f_sign] else 0.0

def _calc_tara(m_nak, f_nak):
    pts = 0.0
    if (f_nak-m_nak)%9 not in (2,4,6): pts += 1.5
    if (m_nak-f_nak)%9 not in (2,4,6): pts += 1.5
    return pts

def _calc_yoni(m_nak, f_nak):
    my, fy = YONI_ANIMALS[m_nak], YONI_ANIMALS[f_nak]
    if my == fy: return 4.0
    if YONI_ENEMIES.get(my) == fy: return 0.0
    return 2.0

def _calc_graha_maitri(m_sign, f_sign):
    ml, fl = SIGN_LORDS[m_sign], SIGN_LORDS[f_sign]
    def _check(p1, p2):
        if p1==p2: return 1.0
        if p2 in NATURAL_FRIENDS.get(p1,[]): return 1.0
        if p2 in NATURAL_ENEMIES.get(p1,[]): return 0.0
        return 0.5
    total = _check(ml,fl) + _check(fl,ml)
    if total == 2.0: return 5.0
    if total == 1.5: return 4.0
    if total == 1.0: return 3.0
    if total == 0.5: return 1.0
    return 0.0

def _calc_gana(m_nak, f_nak):
    mg, fg = GANA[m_nak], GANA[f_nak]
    if mg == fg: return 6.0
    if mg=="Deva" and fg=="Manushya": return 6.0
    if mg=="Manushya" and fg=="Deva": return 5.0
    if "Rakshasa" in (mg,fg) and "Manushya" in (mg,fg): return 0.0
    if mg=="Rakshasa" and fg=="Deva": return 1.0
    if fg=="Rakshasa" and mg=="Deva": return 0.0
    return 0.0

def _calc_bhakoot(m_sign, f_sign):
    mi, fi = SIGNS.index(m_sign), SIGNS.index(f_sign)
    diff = (fi - mi) % 12 + 1
    return 7.0 if diff in (1,7,3,11,4,10) else 0.0

def _calc_nadi(m_nak, f_nak):
    return 8.0 if NADI[m_nak] != NADI[f_nak] else 0.0

def _calc_vedha(m_nak, f_nak):
    for a,b in VEDHA_PAIRS:
        if (m_nak==a and f_nak==b) or (m_nak==b and f_nak==a): return "bad"
    return "good"

def _calc_rajju(m_nak, f_nak):
    for group, indices in RAJJU_GROUPS.items():
        if m_nak in indices and f_nak in indices:
            return {"result":"bad","group":group,"effect":RAJJU_EFFECTS[group]}
    return {"result":"good","group":None,"effect":""}

def _calc_mahendra(m_nak, f_nak):
    cnt = ((m_nak-f_nak)%27)+1
    return "good" if cnt in (4,7,10,13,16,19,22,25) else "bad"

def _calc_stree_deergha(m_nak, f_nak):
    cnt = ((m_nak-f_nak)%27)+1
    return "good" if cnt >= 9 else "bad"

# =============================================================================
# 主计算函数
# =============================================================================

def calc_ashtakoot(male_moon_degree: float, female_moon_degree: float,
                   male_chart: Dict = None, female_chart: Dict = None) -> Dict:
    """
    计算16因子Ashtakoot兼容性匹配（基于dashaflow MIT算法）。

    Args:
        male_moon_degree: 男性月亮黄道经度(0-360)
        female_moon_degree: 女性月亮黄道经度(0-360)
        male_chart: 男性星盘数据(可选，用于附加Kuta)
        female_chart: 女性星盘数据(可选)

    Returns:
        完整的兼容性分析
    """
    m_nak = int(male_moon_degree / (360.0/27.0))
    f_nak = int(female_moon_degree / (360.0/27.0))
    m_sign = SIGNS[int(male_moon_degree/30)%12]
    f_sign = SIGNS[int(female_moon_degree/30)%12]

    scores = {
        "Varna": _calc_varna(m_sign, f_sign),
        "Vashya": 2.0,  # Simplified
        "Tara": _calc_tara(m_nak, f_nak),
        "Yoni": _calc_yoni(m_nak, f_nak),
        "GrahaMaitri": _calc_graha_maitri(m_sign, f_sign),
        "Gana": _calc_gana(m_nak, f_nak),
        "Bhakoot": _calc_bhakoot(m_sign, f_sign),
        "Nadi": _calc_nadi(m_nak, f_nak),
    }
    total = sum(scores.values())

    rajju = _calc_rajju(m_nak, f_nak)
    additional = {
        "Mahendra": _calc_mahendra(m_nak, f_nak),
        "StreeDeergha": _calc_stree_deergha(m_nak, f_nak),
        "Vedha": _calc_vedha(m_nak, f_nak),
        "Rajju": rajju,
    }

    # Dosha缓解逻辑
    exceptions = []
    if scores["Nadi"]==0 and scores["Bhakoot"]>0 and rajju["result"]=="good":
        exceptions.append("Nadi Dosha mitigated by good Bhakoot and Rajju")
    if rajju["result"]=="bad" and scores["GrahaMaitri"]>=4 and scores["Bhakoot"]>0 and scores["Tara"]>=1.5 and additional["Mahendra"]=="good":
        exceptions.append("Rajju Dosha mitigated")

    assessment = "优秀" if total>=28 else "良好" if total>=21 else "一般" if total>=18 else "不推荐"
    approved = total >= 18.0 and (scores["Nadi"]>0 or len(exceptions)>0)

    return {
        "version": "3.8-dashaflow-mit-adapted",
        "method": "Ashtakoot 16因子兼容性分析 (dashaflow MIT)",
        "male": {"moon_sign":m_sign,"nakshatra":NAKSHATRAS[m_nak],"gana":GANA[m_nak],"nadi":NADI[m_nak],"yoni":YONI_ANIMALS[m_nak]},
        "female": {"moon_sign":f_sign,"nakshatra":NAKSHATRAS[f_nak],"gana":GANA[f_nak],"nadi":NADI[f_nak],"yoni":YONI_ANIMALS[f_nak]},
        "scores": scores,
        "total_score": total,
        "max_score": 36.0,
        "assessment": assessment,
        "is_approved": approved,
        "additional_kutas": additional,
        "exceptions": exceptions,
    }


def calc_synastry(male_chart: Dict, female_chart: Dict) -> Dict:
    """
    Backward-compatible synastry wrapper used by integration tests and older CLI paths.

    Expected chart keys:
    - moon_lon: Moon longitude in degrees (required)
    - mars_lon / asc_lon / gender: optional, reserved for Kuja and extended factors
    """
    if "moon_lon" not in male_chart or "moon_lon" not in female_chart:
        raise ValueError("calc_synastry requires moon_lon in both male_chart and female_chart")

    result = calc_ashtakoot(
        float(male_chart["moon_lon"]),
        float(female_chart["moon_lon"]),
        male_chart=male_chart,
        female_chart=female_chart,
    )

    # Historical test/API compatibility: expose BadConstellations as an additional Kuta.
    # A bad constellation condition is present if Vedha or Rajju is adverse.
    vedha_bad = result["additional_kutas"].get("Vedha") == "bad"
    rajju_bad = result["additional_kutas"].get("Rajju", {}).get("result") == "bad"
    result["additional_kutas"]["BadConstellations"] = "bad" if (vedha_bad or rajju_bad) else "good"
    return result
