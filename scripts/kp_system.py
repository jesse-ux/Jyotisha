#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KP (Krishnamurti Paddhati) 占星系统模块
基于 diliprk/VedicAstro (MIT License) 核心算法适配

核心功能：
1. Sublord/Subsublord 计算（基于Vimshottari比例划分）
2. Planet Significator ABCD体系
3. House Significator ABCD体系
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]

# Vimshottari年限（KP系统使用相同比例划分sublord）
VIMSHOTTARI_DURATION = [7, 20, 6, 10, 7, 18, 16, 19, 17]
KP_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
STAR_LORDS = KP_LORDS * 3  # 27 Nakshatras = 3 cycles of 9 lords
VIMSHOTTARI_YEARS = dict(zip(KP_LORDS, VIMSHOTTARI_DURATION))

NAKSHATRA_SPAN = 360.0 / 27.0  # 13.333... degrees


def get_kp_lords(degree: float) -> Dict:
    """
    KP Sublord/Subsublord 计算核心（基于 diliprk/VedicAstro MIT 算法）。

    输入任意黄道经度，返回：
    - Rasi Lord: 星座主星
    - Nakshatra: 星宿名称
    - Nakshatra Lord: 星宿主星
    - Nakshatra Pada: 星宿四分之一
    - Sub Lord: 子主星（KP特有，按Vimshottari比例划分）
    - Sub Sub Lord: 次子主星（KP特有，进一步细分）

    Args:
        degree: 黄道经度（0-360）

    Returns:
        KP lords字典
    """
    deg = degree % 360

    # 1. Sign lord
    sign_index = int(deg // 30)

    # 2. Nakshatra
    nakshatra_index = int(deg // NAKSHATRA_SPAN) % 27
    nakshatra_deg = deg % NAKSHATRA_SPAN
    pada = int(nakshatra_deg // (NAKSHATRA_SPAN / 4)) + 1

    # 3. Sublord & SubSubLord（KP核心算法）
    # 将Vimshottari 120年周期按比例投影到度数上
    deg_remainder = deg - 120 * int(deg / 120)
    deg_cumulative = 0.0

    for i in range(9):
        deg_nl = NAKSHATRA_SPAN  # 13.333... degrees per nakshatra
        for j in range(i, i + 9):
            j_mod = j % 9
            deg_sl = deg_nl * VIMSHOTTARI_DURATION[j_mod] / 120.0
            for k in range(j_mod, j_mod + 9):
                k_mod = k % 9
                deg_ss = deg_sl * VIMSHOTTARI_DURATION[k_mod] / 120.0
                deg_cumulative += deg_ss
                if deg_cumulative >= deg_remainder:
                    return {
                        'rasi_lord': SIGN_LORDS.get(SIGNS[sign_index], ''),
                        'sign': SIGNS[sign_index],
                        'nakshatra': NAKSHATRAS[nakshatra_index],
                        'nakshatra_lord': STAR_LORDS[nakshatra_index],
                        'pada': pada,
                        'sub_lord': KP_LORDS[j_mod],
                        'sub_sub_lord': KP_LORDS[k_mod],
                    }

    # Fallback
    return {
        'rasi_lord': SIGN_LORDS.get(SIGNS[sign_index], ''),
        'sign': SIGNS[sign_index],
        'nakshatra': NAKSHATRAS[nakshatra_index],
        'nakshatra_lord': STAR_LORDS[nakshatra_index],
        'pada': pada,
        'sub_lord': 'Unknown',
        'sub_sub_lord': 'Unknown',
    }


def get_planet_significators(planet_positions: Dict, houses: List[Dict]) -> Dict:
    """
    Planet Significator ABCD（基于 diliprk/VedicAstro MIT 算法）。

    对每颗行星计算KP体系的A/B/C/D四个significator：
    - A: 星宿主星(Nakshatra Lord)所在的宫位
    - B: 行星自身所在的宫位
    - C: 星宿主星也是宫主星的那些宫位
    - D: 行星自身也是宫主星的那些宫位

    Args:
        planet_positions: {planet_name: {...包含kp_lords/house...}}
        houses: 12宫位列表 [{'house': 1, 'sign': 'Aries', 'rasi_lord': 'Mars'}, ...]

    Returns:
        Planet significators
    """
    # 构建辅助索引
    planet_kp_data = {}
    for pname, pdata in planet_positions.items():
        kp_lords = pdata.get('kp_lords', {})
        planet_kp_data[pname] = {
            'nakshatra_lord': kp_lords.get('nakshatra_lord', ''),
            'house': pdata.get('house', 1),
        }

    results = {}
    for pname, kp_data in planet_kp_data.items():
        nl = kp_data['nakshatra_lord']

        # A: 星宿主星所在的宫位
        A = None
        if nl in planet_kp_data:
            A = planet_kp_data[nl]['house']

        # B: 行星自身所在宫位
        B = kp_data['house']

        # C: 星宿主星是宫主星的那些宫位
        C = [h['house'] for h in houses if h.get('rasi_lord', '') == nl]

        # D: 行星自身是宫主星的那些宫位
        D = [h['house'] for h in houses if h.get('rasi_lord', '') == pname]

        results[pname] = {'A': A, 'B': B, 'C': C, 'D': D}

    return results


def get_house_significators(planet_positions: Dict, houses: List[Dict]) -> Dict:
    """
    House Significator ABCD（基于 diliprk/VedicAstro MIT 算法）。

    对每个宫位计算KP体系的A/B/C/D四个significator：
    - A: 在该宫位居住者的星宿中的行星
    - B: 该宫位中的行星
    - C: 在该宫位主星的星宿中的行星
    - D: 该宫位的主星

    Args:
        planet_positions: {planet_name: {...包含kp_lords/house...}}
        houses: 12宫位列表

    Returns:
        House significators
    """
    # 构建行星ID到星宿主星的映射
    planet_nl = {}
    for pname, pdata in planet_positions.items():
        kp_lords = pdata.get('kp_lords', {})
        planet_nl[pname] = kp_lords.get('nakshatra_lord', '')

    results = {}
    for h in houses:
        house_num = h['house']

        # A: 在该宫位居住者的星宿中的行星
        occupants = [pname for pname, pdata in planet_positions.items()
                     if pdata.get('house') == house_num]
        A = [pname for pname, nl in planet_nl.items() if nl in occupants]

        # B: 该宫位中的行星
        B = occupants

        # C: 在该宫位主星的星宿中的行星
        rasi_lord = h.get('rasi_lord', '')
        C = [pname for pname, nl in planet_nl.items() if nl == rasi_lord]

        # D: 该宫位的主星
        D = rasi_lord

        results[house_num] = {'A': A, 'B': B, 'C': C, 'D': D}

    return results


def calc_kp_analysis(planet_positions: Dict, asc_sign: str = 'Aries') -> Dict:
    """
    完整KP分析（基于 diliprk/VedicAstro MIT 算法）。

    Args:
        planet_positions: 行星位置 {planet: {'sign': str, 'degree': float, 'house': int}}
        asc_sign: 上升星座名称

    Returns:
        完整KP分析结果
    """
    asc_sign_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0

    # 1. 为每颗行星计算KP lords
    kp_planets = {}
    for pname, pdata in planet_positions.items():
        sign = pdata.get('sign', 'Aries')
        deg_in_sign = pdata.get('degree', 0) % 30
        if sign in SIGNS:
            sign_idx = SIGNS.index(sign)
            degree = sign_idx * 30 + deg_in_sign
        else:
            degree = deg_in_sign

        kp_lords = get_kp_lords(degree)
        kp_planets[pname] = {
            'sign': sign,
            'degree': degree,
            'house': pdata.get('house', 1),
            'kp_lords': kp_lords,
        }

    # 2. 构建宫位信息（含KP lords）
    houses = []
    for house_num in range(1, 13):
        sign_idx = (asc_sign_idx + house_num - 1) % 12
        sign_name = SIGNS[sign_idx]
        house_center_degree = sign_idx * 30 + 15.0  # 宫位中点
        kp_lords = get_kp_lords(house_center_degree)

        houses.append({
            'house': house_num,
            'sign': sign_name,
            'rasi_lord': SIGN_LORDS.get(sign_name, ''),
            'kp_lords': kp_lords,
        })

    # 3. 计算significators
    planet_sig = get_planet_significators(kp_planets, houses)
    house_sig = get_house_significators(kp_planets, houses)

    return {
        'method': 'KP (Krishnamurti Paddhati) 系统',
        'version': '1.0',
        'source': 'diliprk/VedicAstro MIT License',
        'planets': {pname: {'kp_lords': data['kp_lords'], 'significators': planet_sig.get(pname, {})}
                    for pname, data in kp_planets.items()},
        'houses': {h['house']: {'sign': h['sign'], 'kp_lords': h['kp_lords'], 'significators': house_sig.get(h['house'], {})}
                   for h in houses},
    }


def _kp_next_lords(start_lord: str) -> List[str]:
    idx = KP_LORDS.index(start_lord)
    return KP_LORDS[idx:] + KP_LORDS[:idx]


def _kp_years_to_days(years: float) -> float:
    return years * 365.2425


def _kp_birth_star_balance(moon_longitude: float) -> Tuple[str, float]:
    moon_longitude = moon_longitude % 360.0
    nak_idx = int(moon_longitude // NAKSHATRA_SPAN) % 27
    star_lord = STAR_LORDS[nak_idx]
    elapsed = (moon_longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    return star_lord, max(0.0, min(1.0, 1.0 - elapsed))


def _kp_period_score(lords: List[str], planet_house_significators: Optional[Dict[str, Dict]] = None) -> Dict:
    supportive_houses = {2, 5, 7, 11}
    blocking_houses = {1, 6, 8, 10, 12}
    supportive = 0
    blocking = 0
    details = {}
    for lord in lords:
        sig = (planet_house_significators or {}).get(lord, {})
        houses = set()
        for value in sig.values():
            if isinstance(value, int):
                houses.add(value)
            elif isinstance(value, list):
                houses.update(v for v in value if isinstance(v, int))
        support_hits = sorted(houses & supportive_houses)
        block_hits = sorted(houses & blocking_houses)
        supportive += len(support_hits)
        blocking += len(block_hits)
        details[lord] = {'supportive_houses': support_hits, 'blocking_houses': block_hits}
    score = supportive - blocking
    if score >= 2:
        judgement = 'supportive'
    elif score <= -2:
        judgement = 'blocking'
    else:
        judgement = 'mixed'
    return {
        'marriage_score': score,
        'supportive_hits': supportive,
        'blocking_hits': blocking,
        'judgement': judgement,
        'lord_details': details,
    }


def calc_kp_dba_timeline(
    birth_datetime: datetime,
    moon_longitude: float,
    target_start: datetime,
    target_end: datetime,
    planet_house_significators: Optional[Dict[str, Dict]] = None,
) -> Dict:
    """Build Vimshottari MD/AD/PD windows for KP-style marriage timing review."""
    birth_star_lord, balance = _kp_birth_star_balance(moon_longitude)
    periods = []
    md_start = birth_datetime
    for md_i, md_lord in enumerate(_kp_next_lords(birth_star_lord) * 3):
        md_years = VIMSHOTTARI_YEARS[md_lord] * (balance if md_i == 0 else 1.0)
        md_end = md_start + timedelta(days=_kp_years_to_days(md_years))
        ad_start = md_start
        for ad_lord in _kp_next_lords(md_lord):
            ad_years = md_years * VIMSHOTTARI_YEARS[ad_lord] / 120.0
            ad_end = ad_start + timedelta(days=_kp_years_to_days(ad_years))
            pd_start = ad_start
            for pd_lord in _kp_next_lords(ad_lord):
                pd_years = ad_years * VIMSHOTTARI_YEARS[pd_lord] / 120.0
                pd_end = pd_start + timedelta(days=_kp_years_to_days(pd_years))
                if pd_end >= target_start and pd_start <= target_end:
                    scored = _kp_period_score([md_lord, ad_lord, pd_lord], planet_house_significators)
                    periods.append({
                        'md_lord': md_lord,
                        'ad_lord': ad_lord,
                        'pd_lord': pd_lord,
                        'start': pd_start.isoformat(),
                        'end': pd_end.isoformat(),
                        **scored,
                    })
                pd_start = pd_end
            ad_start = ad_end
        md_start = md_end
        if md_start > target_end:
            break
    return {
        'method': 'KP DBA timeline (Vimshottari MD/AD/PD)',
        'birth_star_lord': birth_star_lord,
        'birth_star_balance_fraction': balance,
        'target_start': target_start.isoformat(),
        'target_end': target_end.isoformat(),
        'periods': periods,
    }
