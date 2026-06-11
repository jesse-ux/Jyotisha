#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sade Sati + Kantaka Shani 完整模块
基于BPHS标准算法，实现完整的土星压力周期分析。

Sade Sati 三阶段：
1. Rising Phase: 土星进入月亮前方星座（约2.5年）
2. Peak Phase: 土星在月亮星座（约2.5年）
3. Setting Phase: 土星进入月亮后方星座（约2.5年）

Kantaka Shani: 土星经过第1/4/8/10宫时的额外压力标记
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# 土星在每个星座停留的近似时间（约2.5年即30个月）
SATURN_TRANSIT_MONTHS = 30  # 近似值（实际约29.5个月）


def calc_sade_sati(moon_sign: str, transit_saturn_sign: str,
                   current_date: datetime = None) -> Dict:
    """
    计算Sade Sati三阶段状态。

    根据土星当前所在星座与月亮星座的相对位置，判断当前处于
    Rising/Peak/Setting哪个阶段，以及剩余时间。

    Args:
        moon_sign: 月亮星座名称
        transit_saturn_sign: 行运土星所在星座
        current_date: 当前日期（可选，用于计算剩余时间）

    Returns:
        Sade Sati分析结果
    """
    if moon_sign not in SIGNS or transit_saturn_sign not in SIGNS:
        return {'active': False, 'error': 'Invalid sign'}

    moon_idx = SIGNS.index(moon_sign)
    saturn_idx = SIGNS.index(transit_saturn_sign)

    # 计算土星相对于月亮的位置
    relative = (saturn_idx - moon_idx) % 12

    # 三阶段判定
    if relative == 11:  # 月亮前一个星座 = Rising
        phase = 'rising'
        phase_name = '上升期（Rising Phase）'
        phase_desc = '土星正进入月亮前方星座，压力开始累积。表现为新挑战、新责任、新环境适应。'
        intensity = '中等'
        progress = 0
    elif relative == 0:  # 月亮星座 = Peak
        phase = 'peak'
        phase_name = '高峰期（Peak Phase）'
        phase_desc = '土星正经过月亮星座，压力达到顶点。核心考验期，涉及身份、情感、安全感的全面检视。'
        intensity = '高潮'
        progress = 0
    elif relative == 1:  # 月亮后一个星座 = Setting
        phase = 'setting'
        phase_name = '消退期（Setting Phase）'
        phase_desc = '土星已离开月亮星座，进入后方星座。压力开始消退，收获教训、总结经验。'
        intensity = '递减'
        progress = 0
    else:
        return {
            'active': False,
            'phase': 'none',
            'phase_name': '非Sade Sati期间',
            'phase_desc': '土星不在月亮星座及其相邻星座范围内',
            'moon_sign': moon_sign,
            'saturn_sign': transit_saturn_sign,
            'intensity': '无',
            'next_phase': _predict_next_phase(moon_idx, saturn_idx),
        }

    return {
        'active': True,
        'phase': phase,
        'phase_name': phase_name,
        'phase_desc': phase_desc,
        'moon_sign': moon_sign,
        'saturn_sign': transit_saturn_sign,
        'intensity': intensity,
        'total_duration': '约7.5年',
        'current_phase_duration': '约2.5年',
    }


def _predict_next_phase(moon_idx: int, saturn_idx: int) -> str:
    """预测下一个Sade Sati阶段"""
    dist_to_moon = (moon_idx - saturn_idx) % 12
    if dist_to_moon <= 1:
        return '即将进入Rising期'
    elif dist_to_moon <= 4:
        return f'约{dist_to_moon * 2.5:.0f}年后进入Rising期'
    else:
        return f'约{dist_to_moon * 2.5:.0f}年后进入Rising期'


def calc_kantaka_shani(moon_sign: str, asc_sign: str,
                       transit_saturn_sign: str) -> Dict:
    """
    计算Kantaka Shani（土星尖刺压力）。

    土星在第1/4/8/10宫时触发额外的Kantaka Shani压力。
    这些位置代表人生核心领域受到土星的直接考验。

    Args:
        moon_sign: 月亮星座
        asc_sign: 上升星座
        transit_saturn_sign: 行运土星星座

    Returns:
        Kantaka Shani分析
    """
    if moon_sign not in SIGNS or asc_sign not in SIGNS or transit_saturn_sign not in SIGNS:
        return {'active': False}

    moon_idx = SIGNS.index(moon_sign)
    asc_idx = SIGNS.index(asc_sign)
    saturn_idx = SIGNS.index(transit_saturn_sign)

    triggers = []

    # 从月亮角度
    moon_house = (saturn_idx - moon_idx) % 12 + 1
    if moon_house == 1:
        triggers.append({'reference': '月亮', 'house': 1, 'area': '自我认同、情感安全'})
    if moon_house == 4:
        triggers.append({'reference': '月亮', 'house': 4, 'area': '家庭、内在安全感'})
    if moon_house == 8:
        triggers.append({'reference': '月亮', 'house': 8, 'area': '深层恐惧、转变'})
    if moon_house == 10:
        triggers.append({'reference': '月亮', 'house': 10, 'area': '公众形象、事业方向'})

    # 从上升角度
    asc_house = (saturn_idx - asc_idx) % 12 + 1
    if asc_house == 1:
        triggers.append({'reference': '上升', 'house': 1, 'area': '自我、身体、人生方向'})
    if asc_house == 4:
        triggers.append({'reference': '上升', 'house': 4, 'area': '家庭、根基、内在稳定'})
    if asc_house == 8:
        triggers.append({'reference': '上升', 'house': 8, 'area': '危机、变革、共享资源'})
    if asc_house == 10:
        triggers.append({'reference': '上升', 'house': 10, 'area': '事业、社会地位、成就'})

    return {
        'active': len(triggers) > 0,
        'triggers': triggers,
        'intensity': '高' if len(triggers) >= 3 else '中等' if len(triggers) >= 2 else '低' if triggers else '无',
        'advice': _kantaka_advice(triggers) if triggers else None,
    }


def _kantaka_advice(triggers: List[Dict]) -> str:
    """生成Kantaka Shani建议"""
    areas = [t['area'] for t in triggers]
    if '自我认同、情感安全' in areas or '自我、身体、人生方向' in areas:
        return '当前阶段需特别关注自我认知和身体健康，避免冲动决策。'
    if '事业、社会地位、成就' in areas or '公众形象、事业方向' in areas:
        return '事业领域面临考验，需稳健行事，避免冒进。长期规划优于短期投机。'
    if '家庭、根基、内在稳定' in areas or '家庭、内在安全感' in areas:
        return '家庭和内在安全感需要额外关注，适合沉淀和积累。'
    if '危机、变革、共享资源' in areas or '深层恐惧、转变' in areas:
        return '面临深层转变，适合心理探索和精神成长，避免财务冒进。'
    return '土星考验期间，保持耐心和纪律是度过难关的关键。'


def calc_sade_sati_complete(moon_degree: float, asc_degree: float,
                            transit_saturn_degree: float,
                            current_date: datetime = None) -> Dict:
    """
    完整的Sade Sati + Kantaka Shani综合分析。

    Args:
        moon_degree: 月亮黄道经度(0-360)
        asc_degree: 上升黄道经度(0-360)
        transit_saturn_degree: 行运土星黄道经度(0-360)
        current_date: 当前日期

    Returns:
        完整的Sade Sati分析
    """
    moon_sign = SIGNS[int(moon_degree / 30) % 12]
    asc_sign = SIGNS[int(asc_degree / 30) % 12]
    saturn_sign = SIGNS[int(transit_saturn_degree / 30) % 12]

    sade_sati = calc_sade_sati(moon_sign, saturn_sign, current_date)
    kantaka = calc_kantaka_shani(moon_sign, asc_sign, saturn_sign)

    # 综合强度评定
    if sade_sati['active'] and kantaka['active']:
        overall = '极高压力 — Sade Sati与Kantaka Shani同时活跃'
    elif sade_sati['active']:
        overall = f'Sade Sati {sade_sati["intensity"]}压力期间'
    elif kantaka['active']:
        overall = f'仅Kantaka Shani — 土星尖刺压力({kantaka["intensity"]})'
    else:
        overall = '无Sade Sati或Kantaka Shani压力'

    return {
        'method': 'Sade Sati + Kantaka Shani 完整分析v1.0',
        'moon_sign': moon_sign,
        'asc_sign': asc_sign,
        'saturn_sign': saturn_sign,
        'sade_sati': sade_sati,
        'kantaka_shani': kantaka,
        'overall_assessment': overall,
    }
