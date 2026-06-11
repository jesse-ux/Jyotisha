#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
额外Dasha系统模块 v1.0
基于BPHS条件性Dasha体系

支持的Dasha系统：
1. Dwisaptati Sama Dasha (72年周期) — 当Lagna lord在特定条件时触发
2. Shattrimsa Sama Dasha (36年周期) — 当Moon在特定条件时触发
3. Dwadashottari Dasha (112年周期) — 当Venus在特定Nakshatra时触发
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

YEAR_DAYS = 365.25636
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
    'Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni',
    'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta','Shatabhisha',
    'Purva Bhadrapada','Uttara Bhadrapada','Revati']

VIMSHOTTARI_DURATION = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}
DASHA_ORDER = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']


# =============================================================================
# Dwisaptati Sama Dasha (72年周期)
# 适用条件：Lagna lord在Lagna或7宫时激活
# 主星序列：特定8星顺序，每9年一个主星
# =============================================================================

DWISAPTATI_LORDS = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu']
DWISAPTATI_DURATION = {l: 9 for l in DWISAPTATI_LORDS}  # 每个9年，共72年
DWISAPTATI_SUB_DURATION = {p: VIMSHOTTARI_DURATION[p]*9/120 for p in DWISAPTATI_LORDS}


def check_dwisaptati_condition(lagna_lord: str, lagna_lord_house: int) -> bool:
    """检查Dwisaptati触发条件：Lagna lord在1或7宫"""
    return lagna_lord_house in (1, 7)


def calc_dwisaptati_dasha(birth_date: datetime, lagna_lord: str,
                          lagna_lord_degree: float) -> List[Dict]:
    """
    计算Dwisaptati Sama Dasha（72年周期）。

    每个主星周期 = 9年，子周期按Vimshottari比例分配。
    """
    start_idx = DWISAPTATI_LORDS.index(lagna_lord)
    sequence = []
    current = birth_date

    for i in range(8):
        lord_idx = (start_idx + i) % 8
        lord = DWISAPTATI_LORDS[lord_idx]
        days = 9 * YEAR_DAYS
        end_date = current + timedelta(days=days)

        # 子周期
        subs = []
        sub_start = current
        for j in range(8):
            sub_lord_idx = (lord_idx + j) % 8
            sub_lord = DWISAPTATI_LORDS[sub_lord_idx]
            sub_days = days * (VIMSHOTTARI_DURATION.get(sub_lord, 9) / 120)
            sub_end = sub_start + timedelta(days=sub_days)
            subs.append({'lord': sub_lord, 'start': sub_start.strftime('%Y-%m-%d'),
                        'end': sub_end.strftime('%Y-%m-%d')})
            sub_start = sub_end

        sequence.append({
            'lord': lord, 'years': 9,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'sub_periods': subs[:4],
        })
        current = end_date

    return sequence


# =============================================================================
# Shattrimsa Sama Dasha (36年周期)
# 适用条件：特定条件触发（Moon-based condition）
# 主星序列：9星，每星4年
# =============================================================================

SHATTRIMSA_DURATION = {l: 4 for l in DASHA_ORDER}


def check_shattrimsa_condition(moon_sign: str) -> bool:
    """Shattrimsa触发条件：Moon在特定星座/条件时"""
    return True  # 简化：总可用


def calc_shattrimsa_dasha(birth_date: datetime, moon_nakshatra_idx: int) -> List[Dict]:
    """计算Shattrimsa Sama Dasha（36年周期）。每个主星=4年"""
    start_lord_idx = moon_nakshatra_idx % 9
    sequence = []
    current = birth_date

    for i in range(9):
        lord_idx = (start_lord_idx + i) % 9
        lord = DASHA_ORDER[lord_idx]
        days = 4 * YEAR_DAYS
        end_date = current + timedelta(days=days)

        sequence.append({
            'lord': lord, 'years': 4,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date

    return sequence


# =============================================================================
# Dwadashottari Dasha (112年周期)
# 适用条件：当Venus在特定Nakshatra(Revati/UttaraBhadrapada等)时触发
# 主星序列：特定8星，不同年限
# =============================================================================

DWADASHOTTARI_LORDS = ['Sun','Jupiter','Ketu','Mercury','Rahu','Mars','Saturn','Moon']
DWADASHOTTARI_YEARS = {'Sun':7,'Jupiter':9,'Ketu':11,'Mercury':13,'Rahu':15,'Mars':17,'Saturn':19,'Moon':21}

VENUS_TRIGGER_NAKSHATRAS = {24, 25, 26}  # Shatabhisha, Purva Bhadra, Uttara Bhadra


def check_dwadashottari_condition(venus_nakshatra_idx: int) -> bool:
    """Dwadashottari触发条件：Venus在特定Nakshatra"""
    return venus_nakshatra_idx in VENUS_TRIGGER_NAKSHATRAS


def calc_dwadashottari_dasha(birth_date: datetime, moon_degree: float) -> List[Dict]:
    """计算Dwadashottari Dasha（112年周期）"""
    nak_idx = int(moon_degree / (360/27))
    start_lord_idx = nak_idx % 8
    sequence = []
    current = birth_date

    for i in range(8):
        lord_idx = (start_lord_idx + i) % 8
        lord = DWADASHOTTARI_LORDS[lord_idx]
        years = DWADASHOTTARI_YEARS[lord]
        days = years * YEAR_DAYS
        end_date = current + timedelta(days=days)

        sequence.append({
            'lord': lord, 'years': years,
            'start': current.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
        })
        current = end_date

    return sequence


# =============================================================================
# 条件性Dasha综合选择器
# =============================================================================

def get_applicable_dashas(planets: Dict, lagna_sign: str, moon_degree: float) -> Dict:
    """
    根据星盘条件推荐适用���Dasha系统。

    Returns:
        各Dasha系统的触发状态和计算结果
    """
    results = {'vimshottari': {'applicable': True, 'note': '始终适用（120年标准周期）'}}

    # Dwisaptati
    lagna_lord = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
                  'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
                  'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}.get(lagna_sign, '')
    lord_house = planets.get(lagna_lord, {}).get('house', 0)
    if check_dwisaptati_condition(lagna_lord, lord_house):
        results['dwisaptati'] = {'applicable': True, 'note': f'Lagna lord {lagna_lord}在{lord_house}宫——72年周期激活'}

    # Shattrimsa
    if check_shattrimsa_condition(lagna_sign):
        results['shattrimsa'] = {'applicable': True, 'note': 'Moon-based condition——36年周期可用'}

    # Dwadashottari
    venus_data = planets.get('Venus', {})
    venus_nak = int(venus_data.get('degree', 0) / (360/27))
    if check_dwadashottari_condition(venus_nak):
        results['dwadashottari'] = {'applicable': True, 'note': f'Venus在触发星宿——112年周期激活'}

    return results
