#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sudarshana Chakra（苏达沙那轮）模块
基于BPHS传统三参考点盘系统

三个参考点：
1. Lagna (上升) → 自我、身体
2. Chandra (月亮) → 情感、心理
3. Surya (太阳) → 灵魂、生命力

当三个参考点中同一宫位/行星配置一致时，事件确认度高。
"""

from typing import Dict, List

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}


def _build_reference_chart(planet_positions: Dict, reference_sign_idx: int) -> Dict:
    """
    基于指定参考点构建重新排列的星盘。

    以reference_sign_idx为第1宫，重新计算所有行星的宫位。

    Args:
        planet_positions: {planet: {'sign_idx': int, 'degree': float}}
        reference_sign_idx: 参考星座索引（作为第1宫）

    Returns:
        重新排列的星盘 {planet: {'house': int, 'sign': str, ...}}
    """
    chart = {
        'reference_sign': SIGNS[reference_sign_idx],
        'houses': {},
        'planets': {},
    }

    # 计算每个宫位对应的星座
    for house_num in range(1, 13):
        sign_idx = (reference_sign_idx + house_num - 1) % 12
        chart['houses'][house_num] = {
            'sign': SIGNS[sign_idx],
            'rasi_lord': SIGN_LORDS[SIGNS[sign_idx]],
        }

    # 重新计算行星宫位
    for planet, data in planet_positions.items():
        sign_idx = data.get('sign_idx', data.get('sign', 0))
        if isinstance(sign_idx, str):
            sign_idx = SIGNS.index(sign_idx) if sign_idx in SIGNS else 0

        house = (sign_idx - reference_sign_idx) % 12 + 1
        chart['planets'][planet] = {
            'sign': SIGNS[sign_idx],
            'house': house,
            'degree': data.get('degree', 0),
        }

    return chart


def _find_convergences(lagna_chart: Dict, chandra_chart: Dict, surya_chart: Dict) -> Dict:
    """
    寻找三个参考点盘中的一致性（Convergence）。

    当同一宫位在至少两个参考点中有重要配置时，标记为收敛点。

    Returns:
        收敛分析结果
    """
    convergences = []
    SEVEN_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    for house_num in range(1, 13):
        lagna_planets = [p for p in SEVEN_PLANETS
                         if p in lagna_chart.get('planets', {})
                         and lagna_chart['planets'][p].get('house') == house_num]
        chandra_planets = [p for p in SEVEN_PLANETS
                           if p in chandra_chart.get('planets', {})
                           and chandra_chart['planets'][p].get('house') == house_num]
        surya_planets = [p for p in SEVEN_PLANETS
                         if p in surya_chart.get('planets', {})
                         and surya_chart['planets'][p].get('house') == house_num]

        # 寻找至少两个参考点中共有的行星
        all_in_house = set(lagna_planets + chandra_planets + surya_planets)
        for planet in all_in_house:
            count = (1 if planet in lagna_planets else 0) + \
                    (1 if planet in chandra_planets else 0) + \
                    (1 if planet in surya_planets else 0)
            if count >= 2:
                convergences.append({
                    'house': house_num,
                    'planet': planet,
                    'references': count,
                    'significance': 'high' if count == 3 else 'medium',
                })

    # 去重：同宫位多行星收敛
    house_convergences = {}
    for c in convergences:
        h = c['house']
        if h not in house_convergences:
            house_convergences[h] = []
        house_convergences[h].append(c)

    return {
        'total_convergences': len(convergences),
        'high_confidence': [c for c in convergences if c['significance'] == 'high'],
        'house_analysis': house_convergences,
    }


def calc_sudarshana_chakra(planet_positions: Dict,
                           asc_sign: str = None,
                           asc_sign_idx: int = None,
                           moon_degree: float = None,
                           sun_degree: float = None) -> Dict:
    """
    计算Sudarshana Chakra（三参考点盘）。

    Args:
        planet_positions: {planet: {'sign': str 或 'sign_idx': int, 'degree': float}}
        asc_sign: 上升星座名称（优先）
        asc_sign_idx: 上升星座索引
        moon_degree: 月亮黄道经度(0-360，用于确定月亮星座)
        sun_degree: 太阳黄道经度(0-360，用于确定太阳星座)

    Returns:
        完整的Sudarshana Chakra分析
    """
    # 确定三个参考点星座索引
    if asc_sign and asc_sign in SIGNS:
        lagna_ref = SIGNS.index(asc_sign)
    elif asc_sign_idx is not None:
        lagna_ref = asc_sign_idx % 12
    else:
        lagna_ref = 0

    if moon_degree is not None:
        chandra_ref = int(moon_degree / 30) % 12
    else:
        # 尝试从行星位置中获取
        moon_data = planet_positions.get('Moon', {})
        chandra_ref = moon_data.get('sign_idx', 0)
        if isinstance(chandra_ref, str):
            chandra_ref = SIGNS.index(chandra_ref) if chandra_ref in SIGNS else 3

    if sun_degree is not None:
        surya_ref = int(sun_degree / 30) % 12
    else:
        sun_data = planet_positions.get('Sun', {})
        surya_ref = sun_data.get('sign_idx', 0)
        if isinstance(surya_ref, str):
            surya_ref = SIGNS.index(surya_ref) if surya_ref in SIGNS else 4

    # 构建三个参考点盘
    lagna_chart = _build_reference_chart(planet_positions, lagna_ref)
    chandra_chart = _build_reference_chart(planet_positions, chandra_ref)
    surya_chart = _build_reference_chart(planet_positions, surya_ref)

    # 寻找收敛
    convergence = _find_convergences(lagna_chart, chandra_chart, surya_chart)

    return {
        'method': 'Sudarshana Chakra 三参考点盘 (BPHS标准)',
        'version': '1.0',
        'references': {
            'lagna': {'sign': SIGNS[lagna_ref], 'role': '自我/身体'},
            'chandra': {'sign': SIGNS[chandra_ref], 'role': '情感/心理'},
            'surya': {'sign': SIGNS[surya_ref], 'role': '灵魂/生命力'},
        },
        'charts': {
            'lagna_based': lagna_chart,
            'chandra_based': chandra_chart,
            'surya_based': surya_chart,
        },
        'convergence': convergence,
        'assessment': _assess_chakra(convergence),
    }


def _assess_chakra(convergence: Dict) -> str:
    """评估Sudarshana Chakra的总体结构"""
    high = len(convergence.get('high_confidence', []))
    total = convergence.get('total_convergences', 0)

    if high >= 3:
        return '强烈收敛 — 三个参考点高度一致，事件确认度极高'
    elif high >= 1 or total >= 5:
        return '中等收敛 — 部分领域一致性较强'
    elif total >= 1:
        return '弱收敛 — 少数领域有一致性'
    else:
        return '无收敛 — 三个参考点分散，需从多角度分别分析'
