#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
星宿大运推演系统 v1.0 — Nakshatra Dasha Engine

支持:
  - Ashtottari Dasha（108年星宿大运，条件性系统）
  - Vimshottari Nakshatra-level 详细拆解
  - Nakshatra Transit Overlay（过境星宿叠加大运）
  - Nakshatra-based 时间窗口推演
  - 综合星宿大运报告

设计原则:
  - Ashtottari 作为 Vimshottari 的补充系统（条件：Rahu 不在 Kendra 时适用）
  - Nakshatra-level 拆解提供当前大运的星宿层面的精细时间线
  - Transit Overlay 将过境星宿叠加上大运周期，提供精确时间窗口
"""
from typing import Dict, List, Optional, Tuple
import math
from datetime import datetime, timedelta

# 从 nakshatra_advanced 导入需要的数据
try:
    from nakshatra_advanced import (
        NAK_LIST, NAK_NAMES, NAK_LORDS, NAK_YEARS,
        find_nakshatra, calc_tara_bala,
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from nakshatra_advanced import (
        NAK_LIST, NAK_NAMES, NAK_LORDS, NAK_YEARS,
        find_nakshatra, calc_tara_bala,
    )

# ============================================================================
# Ashtottari Dasha 数据表
# ============================================================================

# Ashtottari 行星年数（108年制）
ASHTOTTARI_YEARS = {
    'Sun': 6, 'Moon': 15, 'Mars': 8, 'Mercury': 17,
    'Saturn': 10, 'Jupiter': 19, 'Rahu': 12, 'Venus': 21,
}
ASHTOTTARI_TOTAL = sum(ASHTOTTARI_YEARS.values())  # 108

# Ashtottari 大运顺序（固定循环）
ASHTOTTARI_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Saturn', 'Jupiter', 'Rahu', 'Venus']

# Nakshatra → Ashtottari 起始守护星映射
# 按 Vimshottari 星宿守护星对应 Ashtottari 起始点
# Ketu 星宿 → 不作为 Ashtottari 起点，回溯到上一个 Venus
NAK_TO_ASHTOTTARI_START = {
    'Ashwini': 'Venus',       # Ketu nakshatra → 上一周期末尾 Venus
    'Bharani': 'Venus',       # Venus
    'Krittika': 'Sun',        # Sun
    'Rohini': 'Moon',         # Moon
    'Mrigashira': 'Mars',     # Mars
    'Ardra': 'Rahu',          # Rahu
    'Punarvasu': 'Jupiter',   # Jupiter
    'Pushya': 'Saturn',       # Saturn
    'Ashlesha': 'Mercury',    # Mercury
    'Magha': 'Venus',         # Ketu → Venus
    'Purva Phalguni': 'Venus', # Venus
    'Uttara Phalguni': 'Sun', # Sun
    'Hasta': 'Moon',          # Moon
    'Chitra': 'Mars',         # Mars
    'Swati': 'Rahu',          # Rahu
    'Vishakha': 'Jupiter',    # Jupiter
    'Anuradha': 'Saturn',     # Saturn
    'Jyeshtha': 'Mercury',    # Mercury
    'Mula': 'Venus',          # Ketu → Venus
    'Purva Ashadha': 'Venus', # Venus
    'Uttara Ashadha': 'Sun',  # Sun
    'Shravana': 'Moon',       # Moon
    'Dhanishta': 'Mars',      # Mars
    'Shatabhisha': 'Rahu',    # Rahu
    'Purva Bhadrapada': 'Jupiter', # Jupiter
    'Uttara Bhadrapada': 'Saturn', # Saturn
    'Revati': 'Mercury',      # Mercury
}


# ============================================================================
# 核心计算函数
# ============================================================================

def is_ashtottari_applicable(rahu_house: int) -> bool:
    """
    判断 Ashtottari Dasha 是否适用

    传统规则：当 Rahu 不在 Kendra（1/4/7/10宫）时，Ashtottari 优先。
    若 Rahu 在 Kendra，则使用 Vimshottari。

    参数:
        rahu_house: Rahu 所在宫位 (1-12)

    返回:
        bool: True = Ashtottari 适用
    """
    kendras = {1, 4, 7, 10}
    return rahu_house not in kendras


def calc_ashtottari_dasha(
    moon_longitude: float,
    birth_date_str: str,
    rahu_house: int,
) -> Dict:
    """
    计算 Ashtottari Dasha 108年大运序列 — v1.0

    参数:
        moon_longitude: 月亮恒星黄道经度
        birth_date_str: 出生日期 YYYY-MM-DD
        rahu_house: Rahu 所在宫位 (1-12)

    返回:
        dict: {
            'applicable': bool,
            'reason': str,
            'starting_lord': str,
            'sequence': [...],
            'total_years': 108,
        }
    """
    applicable = is_ashtottari_applicable(rahu_house)

    # 月亮星宿信息
    nak_data = find_nakshatra(moon_longitude)
    moon_nak = nak_data['nakshatra']
    moon_nak_idx = nak_data['nakshatra_idx']

    # 起始守护星
    starting_lord = NAK_TO_ASHTOTTARI_START.get(moon_nak, 'Sun')

    # 计算起始点的已用/剩余比例
    nak_span = 360.0 / 27
    nak_start = moon_nak_idx * nak_span
    deg_in_nak = moon_longitude - nak_start
    used_ratio = deg_in_nak / nak_span
    remaining_ratio = 1 - used_ratio

    start_lord_years = ASHTOTTARI_YEARS.get(starting_lord, 6)
    first_remaining = start_lord_years * remaining_ratio

    # 构建大运序列
    start_idx = ASHTOTTARI_ORDER.index(starting_lord)
    sequence = []
    cumulative = 0.0

    # 首个大运的剩余部分
    sequence.append({
        'lord': starting_lord,
        'full_years': start_lord_years,
        'remaining_years': round(first_remaining, 4),
        'elapsed_years': round(start_lord_years - first_remaining, 4),
        'cumulative_from_birth': 0.0,
        'cumulative_to_birth': round(first_remaining, 4),
        'is_first': True,
    })
    cumulative += first_remaining

    # 后续完整大运循环
    idx = (start_idx + 1) % 8
    cycle_count = 1
    while cumulative < 120:  # 超出人生预期范围
        lord = ASHTOTTARI_ORDER[idx]
        years = ASHTOTTARI_YEARS[lord]
        sequence.append({
            'lord': lord,
            'full_years': years,
            'remaining_years': years,
            'elapsed_years': 0,
            'cumulative_from_birth': round(cumulative, 4),
            'cumulative_to_birth': round(cumulative + years, 4),
            'is_first': False,
        })
        cumulative += years
        idx = (idx + 1) % 8
        cycle_count += 1
        if cycle_count > 20:  # 安全上限
            break

    # 出生日期
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
    except:
        birth_date = datetime(2000, 1, 1)

    # 为大运添加日期范围
    for item in sequence:
        from_years = item['cumulative_from_birth']
        to_years = item['cumulative_to_birth']
        item['date_from'] = _add_years_to_date(birth_date, from_years)
        item['date_to'] = _add_years_to_date(birth_date, to_years)
        item['age_from'] = round(from_years, 2)
        item['age_to'] = round(to_years, 2)

    if applicable:
        reason = f"Rahu 在第{rahu_house}宫，不在 Kendra(1/4/7/10)，Ashtottari 适用"
    else:
        reason = f"Rahu 在第{rahu_house}宫，在 Kendra，建议使用 Vimshottari"

    return {
        'system': 'Ashtottari Dasha（108年星宿大运）',
        'applicable': applicable,
        'reason': reason,
        'rahu_house': rahu_house,
        'moon_nakshatra': moon_nak,
        'starting_lord': starting_lord,
        'total_years': ASHTOTTARI_TOTAL,
        'first_remaining_years': round(first_remaining, 4),
        'sequence': sequence,
        'note': ('Ashtottari 作为 Vimshottari 的补充系统，'
                 '当 Rahu 不在 Kendra 时提供替代视角。'
                 '两者各有侧重：Vimshottari 偏"心识"，Ashtottari 偏"命运安排"。'),
    }


def calc_current_ashtottari(
    ashtottari_data: Dict,
    age: float,
) -> Dict:
    """
    从 Ashtottari 序列中定位当前年龄的大运

    返回:
        dict: {lord, years_remaining, progress, sub_periods, ...}
    """
    if not ashtottari_data.get('applicable', False):
        return {'applicable': False, 'reason': ashtottari_data.get('reason', '')}

    sequence = ashtottari_data.get('sequence', [])
    current = None
    next_item = None

    for i, item in enumerate(sequence):
        if item['cumulative_from_birth'] <= age < item['cumulative_to_birth']:
            current = item
            if i + 1 < len(sequence):
                next_item = sequence[i + 1]
            break

    if current is None:
        return {'error': f'无法定位年龄 {age} 在 Ashtottari 序列中'}

    years_elapsed_in_md = age - current['cumulative_from_birth']
    years_remaining = current['cumulative_to_birth'] - age
    progress = years_elapsed_in_md / current['remaining_years'] if current['remaining_years'] > 0 else 0

    # 计算 Antardasha 子周期（简化：按比例分配）
    antardasha_sequence = _calc_ashtottari_antardasha(current['lord'], current['remaining_years'])

    # 定位当前 Antardasha
    ad_cumulative = 0
    current_ad = None
    for ad in antardasha_sequence:
        ad_end = ad_cumulative + ad['years']
        if ad_cumulative <= years_elapsed_in_md < ad_end:
            current_ad = {
                **ad,
                'progress_in_ad': (years_elapsed_in_md - ad_cumulative) / ad['years'] if ad['years'] > 0 else 0,
                'remaining_years': round(ad_end - years_elapsed_in_md, 4),
            }
            break
        ad_cumulative = ad_end

    return {
        'applicable': True,
        'current_mahadasha': current['lord'],
        'mahadasha_progress': round(progress, 4),
        'years_elapsed_in_md': round(years_elapsed_in_md, 4),
        'years_remaining_in_md': round(years_remaining, 4),
        'age_from': current['age_from'],
        'age_to': current['age_to'],
        'next_mahadasha': next_item['lord'] if next_item else None,
        'antardasha_sequence': antardasha_sequence,
        'current_antardasha': current_ad,
    }


def _calc_ashtottari_antardasha(md_lord: str, md_years: float) -> List[Dict]:
    """计算 Ashtottari Antardasha 子周期"""
    md_start_idx = ASHTOTTARI_ORDER.index(md_lord)
    total = sum(ASHTOTTARI_YEARS.values())

    result = []
    for i in range(8):
        ad_lord = ASHTOTTARI_ORDER[(md_start_idx + i) % 8]
        ad_years_total = ASHTOTTARI_YEARS[ad_lord]
        # 按比例缩放
        ad_years_in_md = md_years * ad_years_total / total
        result.append({
            'lord': ad_lord,
            'years': round(ad_years_in_md, 4),
            'months': round(ad_years_in_md * 12, 1),
        })

    return result


# ============================================================================
# Vimshottari Nakshatra-level 拆解
# ============================================================================

# Vimshottari Dasha 顺序（9星循环）
VIMSHOTTARI_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
VIMSHOTTARI_YEARS = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}


def calc_nakshatra_dasha_breakdown(
    moon_longitude: float,
    planet_lons: Dict[str, float],
    birth_date_str: str,
    age: float,
) -> Dict:
    """
    Vimshottari Nakshatra-level 详细拆解 — v1.0

    在当前 Vimshottari 大运/小运框架下，提供：
    1. 大运守护星的 Nakshatra 位置及其 Tara 关系
    2. 小运守护星的 Nakshatra 位置
    3. Nakshatra Pada 层面的时间窗口
    4. 月亮星宿到各大运/小运守护星星宿的 Tara Bala

    参数:
        moon_longitude: 月亮恒星黄道经度
        planet_lons: {行星名: 恒星经度}
        birth_date_str: 出生日期 YYYY-MM-DD
        age: 当前年龄（岁）

    返回:
        dict: 星宿层面的大运拆解
    """
    moon_nak_data = find_nakshatra(moon_longitude)
    moon_nak_idx = moon_nak_data['nakshatra_idx']

    # 计算 Vimshottari 起始
    nak = find_nakshatra(moon_longitude)
    nak_idx = nak['nakshatra_idx']
    nak_span = 360.0 / 27
    nak_start = nak_idx * nak_span
    deg_in_nak = moon_longitude - nak_start
    used_ratio = deg_in_nak / nak_span

    # 起始守护星和剩余年数
    start_lord = NAK_LORDS[nak_idx]
    start_total = VIMSHOTTARI_YEARS.get(start_lord, 7)
    first_remaining = start_total * (1 - used_ratio)

    # 构建大运序列
    start_idx = VIMSHOTTARI_ORDER.index(start_lord)
    sequence = []
    cumulative = 0.0

    # 首个（剩余）大运
    sequence.append({
        'lord': start_lord,
        'years': round(first_remaining, 4),
        'cumulative_from': 0.0,
        'is_first': True,
    })
    cumulative += first_remaining

    idx = (start_idx + 1) % 9
    for _ in range(15):  # 足够覆盖到120岁
        lord = VIMSHOTTARI_ORDER[idx]
        years = VIMSHOTTARI_YEARS[lord]
        sequence.append({
            'lord': lord,
            'years': round(years, 4),
            'cumulative_from': round(cumulative, 4),
            'is_first': False,
        })
        cumulative += years
        idx = (idx + 1) % 9
        if cumulative > 120:
            break

    # 定位当前大运
    current_md = None
    current_md_idx = -1
    for i, item in enumerate(sequence):
        if item['cumulative_from'] <= age < (item['cumulative_from'] + item['years']):
            current_md = item
            current_md_idx = i
            break

    if current_md is None:
        return {'error': f'无法定位年龄 {age} 在 Vimshottari 序列中'}

    md_lord = current_md['lord']
    md_years = current_md['years']
    md_start_age = current_md['cumulative_from']
    years_in_md = age - md_start_age

    # 大运守护星的 Nakshatra
    md_lord_nak = None
    if md_lord in planet_lons:
        md_lord_nak = find_nakshatra(planet_lons[md_lord])

    # 计算当前 Antardasha
    antardasas = _calc_vimshottari_antardasha_full(md_lord, md_years)

    # 定位当前 Antardasha
    ad_cumulative = 0.0
    current_ad = None
    for ad in antardasas:
        ad_end = ad_cumulative + ad['years']
        if ad_cumulative <= years_in_md < ad_end:
            current_ad = {
                'lord': ad['lord'],
                'years': ad['years'],
                'progress': (years_in_md - ad_cumulative) / ad['years'] if ad['years'] > 0 else 0,
                'remaining': round(ad_end - years_in_md, 4),
            }
            break
        ad_cumulative = ad_end

    # 当前 Antardasha 守护星的 Nakshatra
    ad_lord_nak = None
    if current_ad and current_ad['lord'] in planet_lons:
        ad_lord_nak = find_nakshatra(planet_lons[current_ad['lord']])

    # Nakshatra Tara 关系分析
    tara_analysis = {}
    if md_lord_nak:
        tara_analysis['mahadasha_lord'] = {
            'planet': md_lord,
            'nakshatra': md_lord_nak['nakshatra'],
            'pada': md_lord_nak['pada'],
            'tara_to_moon': calc_tara_bala(moon_nak_idx, md_lord_nak['nakshatra_idx']),
        }
    if ad_lord_nak and current_ad:
        tara_analysis['antardasha_lord'] = {
            'planet': current_ad['lord'],
            'nakshatra': ad_lord_nak['nakshatra'],
            'pada': ad_lord_nak['pada'],
            'tara_to_moon': calc_tara_bala(moon_nak_idx, ad_lord_nak['nakshatra_idx']),
        }

    # 星宿层面的时间窗口（Pada-level 细分）
    pada_windows = []
    if md_lord_nak and current_ad:
        nak_span_deg = 360.0 / 27
        pada_span_deg = nak_span_deg / 4
        md_years_per_nak = md_years / 9  # 每个 Antardasha 时长近似
        md_years_per_pada = md_years_per_nak / 4

        for ad in antardasas:
            if md_years_per_nak > 0:
                ad_nak = find_nakshatra(planet_lons.get(ad['lord'], 0))
                pada_windows.append({
                    'period': f"AD {ad['lord']}",
                    'nakshatra': ad_nak['nakshatra'],
                    'pada': ad_nak['pada'],
                    'years': round(ad['years'], 4),
                    'tara': calc_tara_bala(moon_nak_idx, ad_nak['nakshatra_idx']),
                })

    # 构建返回
    birth_date = None
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
    except:
        pass

    return {
        'system': 'Vimshottari Nakshatra-level Breakdown',
        'moon_nakshatra': moon_nak_data['nakshatra'],
        'moon_nakshatra_idx': moon_nak_idx,
        'moon_pada': moon_nak_data['pada'],
        'current_age': age,
        'mahadasha': {
            'lord': md_lord,
            'years_total': round(md_years, 4),
            'age_range': f"{round(md_start_age, 2)}-{round(md_start_age + md_years, 2)}",
            'years_elapsed': round(years_in_md, 4),
            'years_remaining': round(md_years - years_in_md, 4),
            'progress': round(years_in_md / md_years, 4) if md_years > 0 else 0,
            'nakshatra': md_lord_nak,
            'tara': tara_analysis.get('mahadasha_lord', {}),
        },
        'antardasha': current_ad,
        'tara_analysis': tara_analysis,
        'pada_windows': pada_windows,
    }


def _calc_vimshottari_antardasha_full(md_lord: str, md_years: float) -> List[Dict]:
    """计算完整的 Vimshottari Antardasha（9个周期）"""
    md_start_idx = VIMSHOTTARI_ORDER.index(md_lord)
    total_years = sum(VIMSHOTTARI_YEARS.values())  # 120

    result = []
    for i in range(9):
        ad_lord = VIMSHOTTARI_ORDER[(md_start_idx + i) % 9]
        ad_years_total = VIMSHOTTARI_YEARS[ad_lord]
        ad_years = md_years * ad_years_total / total_years
        result.append({
            'lord': ad_lord,
            'years': round(ad_years, 4),
            'months': round(ad_years * 12, 1),
        })

    return result


# ============================================================================
# Nakshatra Transit Overlay（过境星宿叠加大运）
# ============================================================================

def calc_nakshatra_transit_overlay(
    natal_planet_lons: Dict[str, float],
    transit_planet_lons: Dict[str, float],
    moon_nak_idx: int,
) -> Dict:
    """
    将过境星宿叠加在本命大运框架上 — v1.0

    分析每个过境行星当前所在的星宿，及其：
    1. 与本命月亮星宿的 Tara 关系
    2. 与本命行星的星宿距离
    3. 当前星宿的 Pada 位置
    4. 吉凶评估

    参数:
        natal_planet_lons: 本命行星经度
        transit_planet_lons: 过境行星经度
        moon_nak_idx: 本命月亮星宿索引

    返回:
        dict: 过境星宿叠加分析
    """
    results = {}

    for pname, t_lon in transit_planet_lons.items():
        t_nak = find_nakshatra(t_lon)
        tara = calc_tara_bala(moon_nak_idx, t_nak['nakshatra_idx'])

        # 过境星宿是否与某本命行星的星宿重叠
        same_nak_as_natal = []
        n_lon = natal_planet_lons.get(pname)
        if n_lon is not None:
            n_nak = find_nakshatra(n_lon)
            if n_nak['nakshatra_idx'] == t_nak['nakshatra_idx']:
                same_nak_as_natal.append('self')

        for np, nl in natal_planet_lons.items():
            if np == pname:
                continue
            n_nak = find_nakshatra(nl)
            if n_nak['nakshatra_idx'] == t_nak['nakshatra_idx']:
                same_nak_as_natal.append(np)

        # 评估
        if tara['is_auspicious']:
            transit_quality = 'favorable'
        elif tara['is_dangerous']:
            transit_quality = 'challenging'
        else:
            transit_quality = 'neutral'

        if same_nak_as_natal:
            transit_quality = transit_quality + '_nak_conjunction'
            note = f"过境星宿与本命{'/'.join(same_nak_as_natal)}同星宿，叠加效应增强"
        else:
            note = ''

        results[pname] = {
            'transit_nakshatra': t_nak['nakshatra'],
            'transit_nakshatra_lord': t_nak['nakshatra_lord'],
            'transit_pada': t_nak['pada'],
            'tara_to_natal_moon': tara,
            'same_nakshatra_as': same_nak_as_natal if same_nak_as_natal else None,
            'quality': transit_quality,
            'note': note,
            'gana': t_nak['gana'],
            'element': t_nak['element'],
        }

    return results


# ============================================================================
# 综合星宿大运报告
# ============================================================================

def nakshatra_dasha_full_report(
    chart_data: Dict,
    birth_date_str: str,
    age: float,
    transit_planet_lons: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    综合星宿大运完整报告 — v1.0

    包含:
    1. Ashtottari Dasha（条件性，Rahu 不在 Kendra 时计算）
    2. Vimshottari Nakshatra-level 拆解
    3. Nakshatra Transit Overlay（如提供过境数据）
    4. 综合时间窗口与 Tara 评估

    参数:
        chart_data: 星盘数据
        birth_date_str: 出生日期 YYYY-MM-DD
        age: 当前年龄
        transit_planet_lons: 过境行星经度（可选）

    返回:
        dict: 完整星宿大运报告
    """
    planets = chart_data.get('planets', {})
    planet_lons = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']

    if not planet_lons:
        return {'error': '无法获取行星经度数据'}

    moon_lon = planet_lons.get('Moon', 0)
    moon_nak = find_nakshatra(moon_lon)
    moon_nak_idx = moon_nak['nakshatra_idx']

    # 确定 Rahu 宫位
    asc_idx = chart_data.get('ascendant_index', 0)
    rahu_deg = None
    rahu_house = 1  # 默认
    if 'Rahu' in planet_lons:
        rahu_deg = planet_lons['Rahu']
        rahu_sign_idx = int(rahu_deg / 30) % 12
        rahu_house = ((rahu_sign_idx - asc_idx) % 12) + 1

    report = {}

    # 1. Ashtottari Dasha
    report['ashtottari'] = calc_ashtottari_dasha(moon_lon, birth_date_str, rahu_house)
    if report['ashtottari']['applicable']:
        report['ashtottari_current'] = calc_current_ashtottari(report['ashtottari'], age)

    # 2. Vimshottari Nakshatra-level
    report['vimshottari_nak_breakdown'] = calc_nakshatra_dasha_breakdown(
        moon_lon, planet_lons, birth_date_str, age)

    # 3. Nakshatra Transit Overlay
    if transit_planet_lons:
        report['transit_overlay'] = calc_nakshatra_transit_overlay(
            planet_lons, transit_planet_lons, moon_nak_idx)

    # 4. 汇总
    md_info = report['vimshottari_nak_breakdown'].get('mahadasha', {})
    ad_info = report['vimshottari_nak_breakdown'].get('antardasha', {})

    summary = {
        'moon_nakshatra': moon_nak['nakshatra'],
        'moon_nakshatra_lord': moon_nak['nakshatra_lord'],
        'moon_pada': moon_nak['pada'],
        'current_age': age,
        'vimshottari_md': md_info.get('lord', 'N/A'),
        'vimshottari_ad': ad_info.get('lord', 'N/A') if ad_info else 'N/A',
        'ashtottari_applicable': report['ashtottari']['applicable'],
    }

    if report['ashtottari']['applicable'] and 'ashtottari_current' in report:
        ac = report['ashtottari_current']
        summary['ashtottari_md'] = ac.get('current_mahadasha', 'N/A')
        if ac.get('current_antardasha'):
            summary['ashtottari_ad'] = ac['current_antardasha']['lord']

    # Dasha 系统的 Nakshatra Tara 评估
    tara_md = report['vimshottari_nak_breakdown'].get('tara_analysis', {}).get('mahadasha_lord', {})
    tara_ad = report['vimshottari_nak_breakdown'].get('tara_analysis', {}).get('antardasha_lord', {})

    summary['md_tara_to_moon'] = tara_md.get('tara_to_moon', {}).get('tara_cn', 'N/A') if tara_md else 'N/A'
    summary['ad_tara_to_moon'] = tara_ad.get('tara_to_moon', {}).get('tara_cn', 'N/A') if tara_ad else 'N/A'

    report['summary'] = summary

    return report


# ============================================================================
# 工具函数
# ============================================================================

def _add_years_to_date(dt: datetime, years: float) -> str:
    """日期 + 年数 → ISO 日期字符串"""
    total_days = years * 365.25
    new_dt = dt + timedelta(days=total_days)
    return new_dt.strftime('%Y-%m-%d')
