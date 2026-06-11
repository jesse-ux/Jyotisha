#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展Dasha系统 v2.0 — 冲刺全球第一
新增：Kalachakra, Narayana, Yogini, Shasti-Hayani, Navamsa, Kendradi, Tara, Shoola

Dasha总数：10 → 18
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

YEAR_DAYS = 365.25636
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
DASHA_ORDER = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
    'Punarvasu','Pushya','Ashlesha','Magha','PurvaPhalguni','UttaraPhalguni',
    'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','PurvaAshadha','UttaraAshadha','Shravana','Dhanishta','Shatabhisha',
    'PurvaBhadrapada','UttaraBhadrapada','Revati']


# =============================================================================
# 1. Kalachakra Dasha（时轮大运）
# =============================================================================

KALACHAKRA_NAVAMSHA_MAP = {}
KALACHAKRA_SAVYA = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius']
KALACHAKRA_APASAVYA = ['Scorpio','Libra','Virgo','Cancer','Leo','Gemini','Taurus','Aries','Sagittarius']
KALACHAKRA_YEARS = {'Aries':10,'Taurus':16,'Gemini':18,'Cancer':24,'Leo':20,'Virgo':22,'Libra':12,'Scorpio':14,'Sagittarius':8,'Capricorn':7,'Aquarius':9,'Pisces':11}

def calc_kalachakra_dasha(birth_date: datetime, moon_nak_idx: int,
                          moon_pada: int) -> List[Dict]:
    """Kalachakra Dasha（时轮大运）"""
    # 判定savya/apasavya序列
    savya_naks = {0,1,2,3,4,5,10,11,12,13,14,15,22,23,24,25,26}
    is_savya = moon_nak_idx in savya_naks
    sequence = KALACHAKRA_SAVYA if is_savya else KALACHAKRA_APASAVYA

    # 起始点
    pada_map = {1:0, 2:3, 3:6, 4:0}  # 简化映射
    start_offset = pada_map.get(moon_pada, 0)
    start_idx = (moon_nak_idx % 9 + start_offset) % 9

    results = []
    current = birth_date
    for i in range(9):
        sign_idx = (start_idx + i) % 9
        sign = sequence[sign_idx]
        years = KALACHAKRA_YEARS.get(sign, 10)
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': sign, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 2. Narayana Dasha（那罗延大运）
# =============================================================================

NARAYANA_ORDER = ['Aries','Scorpio','Sagittarius','Pisces','Capricorn','Aquarius','Taurus','Virgo','Leo','Cancer','Gemini','Libra']

def calc_narayana_dasha(birth_date: datetime, asc_sign_idx: int) -> List[Dict]:
    """Narayana Dasha — 基于星座的推运系统"""
    start_idx = NARAYANA_ORDER.index(SIGNS[asc_sign_idx])
    results = []
    current = birth_date
    for i in range(12):
        idx = (start_idx + i) % 12
        sign = NARAYANA_ORDER[idx]
        years = (idx % 3 + 1) * 3  # movable=3, fixed=6, dual=9
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': sign, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 3. Yogini Dasha（瑜伽女神大运）— 36年周期
# =============================================================================

YOGINI_LORDS = ['Mangala','Pingala','Dhanya','Bhramari','Bhadrika','Ulka','Siddha','Sankata']
YOGINI_YEARS = [1,2,3,4,5,6,7,8]  # 总和=36

def calc_yogini_dasha(birth_date: datetime, moon_nak_idx: int) -> List[Dict]:
    """Yogini Dasha — 36年女神周期"""
    start_idx = moon_nak_idx % 8
    results = []
    current = birth_date
    for i in range(8):
        idx = (start_idx + i) % 8
        lord = YOGINI_LORDS[idx]
        years = YOGINI_YEARS[idx]
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': lord, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 4. Shasti-Hayani Dasha（六十哈亚尼大运）
# =============================================================================

SHASTI_LORDS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
SHASTI_YEARS = [6,8,10,12,14,16,18]

def calc_shasti_hayani_dasha(birth_date: datetime, sun_sign_idx: int) -> List[Dict]:
    """Shasti-Hayani Dasha — 基于太阳位置的60年推运"""
    start_idx = sun_sign_idx % 7
    results = []
    current = birth_date
    for i in range(7):
        idx = (start_idx + i) % 7
        lord = SHASTI_LORDS[idx]
        years = SHASTI_YEARS[idx]
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': lord, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 5. Navamsa Dasha（九分盘大运）
# =============================================================================

def calc_navamsa_dasha(birth_date: datetime, d9_asc_sign_idx: int) -> List[Dict]:
    """Navamsa Dasha — 基于D9上升的星座推运"""
    results = []
    current = birth_date
    for i in range(12):
        sign_idx = (d9_asc_sign_idx + i) % 12
        sign = SIGNS[sign_idx]
        years = (i % 3 + 1) * 3
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': sign, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 6. Kendradi Dasha（角宫推运）
# =============================================================================

KENDRADI_ORDER = [1,4,7,10,2,5,8,11,3,6,9,12]

def calc_kendradi_dasha(birth_date: datetime, asc_sign_idx: int) -> List[Dict]:
    """Kendradi Dasha — 从角宫开始的宫位推运"""
    results = []
    current = birth_date
    for i, house_num in enumerate(KENDRADI_ORDER):
        sign_idx = (asc_sign_idx + house_num - 1) % 12
        sign = SIGNS[sign_idx]
        years = 5 if i < 4 else 3  # 角宫5年，其他3年
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': f'House {house_num} ({sign})', 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 7. Tara Dasha（星宿推运）
# =============================================================================

def calc_tara_dasha(birth_date: datetime, moon_nak_idx: int) -> List[Dict]:
    """Tara Dasha — 从出生星宿开始的推运"""
    results = []
    current = birth_date
    for i in range(27):
        nak_idx = (moon_nak_idx + i) % 27
        nak = NAKSHATRAS[nak_idx]
        years = 3
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': nak, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# 8. Shoola Dasha（尖刺推运）
# =============================================================================

def calc_shoola_dasha(birth_date: datetime, moon_sign_idx: int) -> List[Dict]:
    """Shoola Dasha — 基于月亮星座的9年周期"""
    results = []
    current = birth_date
    for i in range(9):
        sign_idx = (moon_sign_idx + i) % 12
        sign = SIGNS[sign_idx]
        years = 9 - i if i < 9 else 1
        end_date = current + timedelta(days=years * YEAR_DAYS)
        results.append({
            'lord': sign, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date
    return results


# =============================================================================
# Dasha注册表
# =============================================================================

DASHA_REGISTRY = {
    'vimshottari': {'name': 'Vimshottari', 'years': 120, 'type': 'nakshatra'},
    'chara': {'name': 'Chara (Jaimini)', 'years': 36, 'type': 'rasi'},
    'ashtottari': {'name': 'Ashtottari', 'years': 108, 'type': 'conditional'},
    'kalachakra': {'name': 'Kalachakra', 'years': 94, 'type': 'nakshatra'},
    'dwisaptati': {'name': 'Dwisaptati Sama', 'years': 72, 'type': 'conditional'},
    'shattrimsa': {'name': 'Shattrimsa Sama', 'years': 36, 'type': 'conditional'},
    'dwadashottari': {'name': 'Dwadashottari', 'years': 112, 'type': 'conditional'},
    'narayana': {'name': 'Narayana', 'years': 36, 'type': 'rasi'},
    'yogini': {'name': 'Yogini', 'years': 36, 'type': 'nakshatra'},
    'shasti_hayani': {'name': 'Shasti-Hayani', 'years': 60, 'type': 'conditional'},
    'navamsa': {'name': 'Navamsa Dasha', 'years': 36, 'type': 'varga'},
    'kendradi': {'name': 'Kendradi', 'years': 38, 'type': 'bhav'},
    'tara': {'name': 'Tara Dasha', 'years': 81, 'type': 'nakshatra'},
    'shoola': {'name': 'Shoola Dasha', 'years': 9, 'type': 'rasi'},
}

def get_available_dashas() -> List[str]:
    """获取所有可用Dasha系统"""
    return list(DASHA_REGISTRY.keys())

def get_dasha_info(name: str) -> Dict:
    """获取Dasha系统信息"""
    return DASHA_REGISTRY.get(name, {})
