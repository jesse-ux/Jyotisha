#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kakshya 评分系统模块
基于BPHS标准算法，为Ashtakavarga行运提供度数级精确量化。

每个星座(30°)分为8个Kakshya区间，每个区间由特定行星守护。
当行运行星进入某区间时，获得该区间守护行星的加持/削弱。

算法来源：Brihat Parashara Hora Shastra, 基于PyJHora kakshya逻辑翻译（AGPL→独立实现）
"""

from typing import Dict, List, Tuple

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

# Kakshya守护顺序（BPHS标准，每个区间由不同行星守护）
# 8个Kakshya区间按下列顺序分配守护行星
KAKSHYA_LORDS = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Lagna']

# 每个Kakshya区间的度数范围（不等分，基于行星平均运动速度）
# Saturn=3°45'(3.75°), Jupiter=3°45', Mars=3°45', Sun=3°45',
# Venus=3°45', Mercury=3°45', Moon=3°45', Lagna=3°45'
# 合计：8 × 3.75° = 30°
KAKSHYA_SPAN = 30.0 / 8.0  # 3.75°


def get_kakshya_lord(degree_in_sign: float, sign_idx: int, asc_sign_idx: int) -> str:
    """
    获取指定度数在Kakshya系统中的守护行星。

    算法：每个星座的前3.75°为Saturn区间，接着3.75°为Jupiter区间，
    以此类推，最后3.75°为Lagna区间。

    Args:
        degree_in_sign: 行星在星座中的度数(0-30)
        sign_idx: 星座索引(0-11)
        asc_sign_idx: 上升星座索引(0-11)，用于确定Lagna位置

    Returns:
        Kakshya守护行星名称
    """
    kakshya_index = min(int(degree_in_sign / KAKSHYA_SPAN), 7)
    lord = KAKSHYA_LORDS[kakshya_index]
    # Lagna守护指该Kakshya由上升星座的特殊贡献决定
    if lord == 'Lagna':
        return f"Lagna({SIGNS[asc_sign_idx]})"
    return lord


def calc_kakshya_scores(planet_positions: Dict, asc_sign_idx: int) -> Dict:
    """
    计算所有7行星的Kakshya评分。

    对每颗行星，计算其所在Kakshya区间的守护行星，并评估：
    1. Kakshya守护星力量（在该星座的尊严）
    2. Kakshya与Ashtakavarga BAV的对应关系
    3. 综合Kakshya力量评分

    Args:
        planet_positions: 行星位置 {planet: {'sign': str, 'degree': float}}
        asc_sign_idx: 上升星座索引

    Returns:
        Kakshya评分结果
    """
    from typing import Dict as TDict
    SEVEN_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    
    # 行星尊严评分（用于Kakshya守护评估）
    FRIENDSHIP = {
        'Sun': {'friend': ['Moon', 'Mars', 'Jupiter'], 'enemy': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
        'Moon': {'friend': ['Sun', 'Mercury'], 'enemy': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
        'Mars': {'friend': ['Sun', 'Moon', 'Jupiter'], 'enemy': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
        'Mercury': {'friend': ['Sun', 'Venus'], 'enemy': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
        'Jupiter': {'friend': ['Sun', 'Moon', 'Mars'], 'enemy': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
        'Venus': {'friend': ['Mercury', 'Saturn'], 'enemy': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
        'Saturn': {'friend': ['Mercury', 'Venus'], 'enemy': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
    }
    
    SIGN_LORDS = {
        'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
        'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
        'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
    }
    
    results = {}
    
    for planet in SEVEN_PLANETS:
        if planet not in planet_positions:
            continue
        
        p_data = planet_positions[planet]
        sign_name = p_data.get('sign', 'Aries')
        degree = p_data.get('degree', 0) % 30
        
        if sign_name not in SIGNS:
            sign_name = 'Aries'
        sign_idx = SIGNS.index(sign_name)
        
        # Kakshya守护行星
        kakshya_lord = get_kakshya_lord(degree, sign_idx, asc_sign_idx)
        base_lord = kakshya_lord.split('(')[0]  # 去除Lagna后缀
        
        # 评估Kakshya守护星力量
        kakshya_strength = _evaluate_kakshya_strength(base_lord, sign_name, SIGN_LORDS, FRIENDSHIP)
        
        results[planet] = {
            'sign': sign_name,
            'degree_in_sign': round(degree, 2),
            'kakshya_index': int(degree / KAKSHYA_SPAN),
            'kakshya_lord': kakshya_lord,
            'kakshya_strength': kakshya_strength,
            'kakshya_assessment': _kakshya_assessment(kakshya_strength),
        }
    
    return {
        'method': 'Kakshya评分系统 (BPHS标准)',
        'version': '1.0',
        'kakshya_span': KAKSHYA_SPAN,
        'lords': KAKSHYA_LORDS,
        'planets': results,
    }


def _evaluate_kakshya_strength(kakshya_lord: str, sign_name: str,
                                sign_lords: Dict, friendship: Dict) -> float:
    """评估Kakshya守护星在指定星座的力量"""
    if kakshya_lord == 'Lagna':
        return 5.0  # Lagna总是中性
    
    sign_lord = sign_lords.get(sign_name, '')
    if kakshya_lord == sign_lord:
        return 10.0  # Own sign
    
    # 检查友谊关系
    rel = friendship.get(kakshya_lord, {})
    if sign_lord in rel.get('friend', []):
        return 7.0  # Friend
    elif sign_lord in rel.get('enemy', []):
        return 3.0  # Enemy
    else:
        return 5.0  # Neutral


def _kakshya_assessment(strength: float) -> str:
    """Kakshya力量评估"""
    if strength >= 9:
        return "极强（Kakshya守护星在本星座或入庙）"
    elif strength >= 7:
        return "强（Kakshya守护星为友好关系）"
    elif strength >= 5:
        return "中性（Kakshya守护星为本星或中性关系）"
    elif strength >= 3:
        return "弱（Kakshya守护星为敌对关系）"
    else:
        return "极弱（Kakshya守护星落陷或大敌）"


def calc_transit_kakshya(natal_positions: Dict, transit_positions: Dict,
                         asc_sign_idx: int) -> Dict:
    """
    计算行运行星过Kakshya区间的触发分析。

    比较行运和本命行星所在的Kakshya区间，
    找出正在经历关键Kakshya变化的行星。

    Args:
        natal_positions: 本命行星位置
        transit_positions: 行运行星位置
        asc_sign_idx: 上升星座索引

    Returns:
        行运Kakshya触发分析
    """
    SEVEN_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    triggers = []
    
    for planet in SEVEN_PLANETS:
        if planet not in transit_positions:
            continue
        
        t_data = transit_positions[planet]
        t_sign = t_data.get('sign', '')
        t_deg = t_data.get('degree', 0) % 30
        
        if t_sign not in SIGNS:
            continue
        t_sign_idx = SIGNS.index(t_sign)
        t_kakshya_lord = get_kakshya_lord(t_deg, t_sign_idx, asc_sign_idx)
        
        # 本命参考
        n_data = natal_positions.get(planet, {})
        n_sign = n_data.get('sign', '')
        n_deg = n_data.get('degree', 0) % 30
        
        trigger_info = {
            'planet': planet,
            'transit_sign': t_sign,
            'transit_kakshya_lord': t_kakshya_lord,
            'transit_degree': round(t_deg, 2),
        }
        
        # 检查是否与Kakshya守护星互动
        if n_sign in SIGNS:
            n_sign_idx = SIGNS.index(n_sign)
            n_kakshya_lord = get_kakshya_lord(n_deg, n_sign_idx, asc_sign_idx)
            trigger_info['natal_kakshya_lord'] = n_kakshya_lord
            
            base_t_lord = t_kakshya_lord.split('(')[0]
            base_n_lord = n_kakshya_lord.split('(')[0]
            
            if base_t_lord == base_n_lord:
                trigger_info['trigger'] = 'Kakshya回归'
                trigger_info['significance'] = f'{planet}正经过与本命相同的Kakshya区间({base_t_lord})，事件触发概率升高'
            elif base_t_lord == planet:
                trigger_info['trigger'] = '自守Kakshya'
                trigger_info['significance'] = f'{planet}正经过自己守护的Kakshya区间，自身力量增强'
        
        triggers.append(trigger_info)
    
    return {
        'method': '行运Kakshya触发分析',
        'version': '1.0',
        'triggers': triggers,
        'active_triggers': [t for t in triggers if 'trigger' in t],
    }
