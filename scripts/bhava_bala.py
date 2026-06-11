#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bhava Bala（宫位力量）计算模块
基于jyotishganit (MIT License) 核心算法适配

三组件：
1. Bhava Adhipathi Bala - 宫位主星的Shadbala总分
2. Bhava Dig Bala - 基于星座性质的方向力量
3. Bhava Drik Bala - 基于Sputa Drishti的行星对宫位中点相位
"""

from typing import Dict, List

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

# 星座性质分类（BPHS标准）
# nara=人类, chatushpada=四足, jalachara=水栖, keeta=虫类, vanaspati=植物
SIGN_NATURE = {
    'Aries': 'chatushpada', 'Taurus': 'chatushpada', 
    'Gemini': 'nara', 'Cancer': 'jalachara',
    'Leo': 'chatushpada', 'Virgo': 'nara',
    'Libra': 'nara', 'Scorpio': 'keeta',
    'Sagittarius': 'nara', 'Capricorn': 'jalachara',
    'Aquarius': 'nara', 'Pisces': 'jalachara',
}

# 宫位力量基于星座性质（BPHS标准，单位Virupas）
# 索引0-11对应第1-12宫
BHAVA_STRENGTH_FROM_SIGN_NATURE = {
    'nara':         [30, 20, 10, 20, 10, 20, 30, 20, 10, 20, 10, 20],
    'chatushpada':  [30, 20, 10, 20, 10, 20, 30, 20, 10, 20, 10, 20],
    'jalachara':    [20, 30, 10, 30, 10, 30, 20, 30, 10, 30, 10, 30],
    'keeta':        [10, 20, 30, 20, 30, 20, 10, 20, 30, 20, 30, 20],
    'vanaspati':    [20, 10, 20, 10, 20, 30, 20, 10, 20, 10, 20, 30],
}

# Sputa Drishti值表（基于角距离的连续相位力量）
def _get_sputa_drishti(angle_diff: float) -> float:
    """基于jxotishganit MIT算法，将精确角距离转换为Sputa Drishti值(0-60)"""
    ad = angle_diff % 360
    if ad > 180:
        ad = 360 - ad
    
    if ad <= 1.0: return 60.0
    if ad <= 3.0: return 57.0
    if ad <= 7.0: return 51.0
    if ad <= 10.0: return 45.0
    if ad <= 15.0: return 40.5
    if ad <= 20.0: return 30.0
    if ad <= 25.0: return 22.5
    if ad <= 30.0: return 15.0
    if ad <= 40.0: return 12.0
    if ad <= 50.0: return 9.0
    if ad <= 60.0: return 6.0
    if ad <= 75.0: return 4.5
    if ad <= 90.0: return 3.0
    if ad <= 120.0: return 2.25
    if ad <= 150.0: return 1.5
    return 0.0


def calc_bhava_adhipathi_bala(house_signs: List[str], planet_shadbala: Dict) -> List[float]:
    """
    Bhava Adhipathi Bala：宫位主星的Shadbala总分作为宫位力量基础。

    Args:
        house_signs: 12宫位的星座名称列表
        planet_shadbala: 行星Shadbala总分 dict（Virupas）

    Returns:
        12个宫位的adhipathi bala值
    """
    bala = []
    for sign_name in house_signs:
        lord = SIGN_LORDS.get(sign_name, '')
        bala.append(planet_shadbala.get(lord, 0))
    return bala


def calc_bhava_dig_bala(house_signs: List[str], house_degrees: List[float]) -> List[float]:
    """
    Bhava Dig Bala：基于星座性质的宫位方向力量。

    Args:
        house_signs: 12宫位的星座名称列表
        house_degrees: 12宫位的宫头度数列表

    Returns:
        12个宫位的dig bala值
    """
    bala = []
    for hno, sign_name in enumerate(house_signs):
        nature_key = sign_name
        deg = house_degrees[hno] if hno < len(house_degrees) else 15.0
        
        # Sagittarius和Capricorn的双重性质处理
        if sign_name == 'Sagittarius':
            nature_key = 'Sagittarius_first_half' if deg < 15.0 else 'Sagittarius_second_half'
        elif sign_name == 'Capricorn':
            nature_key = 'Capricorn_first_half' if deg < 15.0 else 'Capricorn_second_half'
        
        # 处理双性星座
        if 'first_half' in nature_key:
            # Sagittarius前半=nara, Capricorn前半=jalachara
            real_nature = 'nara' if 'Sagittarius' in nature_key else 'jalachara'
        elif 'second_half' in nature_key:
            real_nature = 'chatushpada' if 'Sagittarius' in nature_key else 'jalachara'
        else:
            real_nature = SIGN_NATURE.get(sign_name, 'nara')
        
        # 查找对应值
        strengths = BHAVA_STRENGTH_FROM_SIGN_NATURE.get(real_nature, BHAVA_STRENGTH_FROM_SIGN_NATURE['nara'])
        bala.append(float(strengths[hno] if hno < len(strengths) else 20))
    
    return bala


def calc_bhava_drik_bala(house_signs: List[str], house_degrees: List[float],
                         asc_sign: str, asc_degree: float,
                         planet_positions: Dict, planet_shadbala: Dict) -> List[float]:
    """
    Bhava Drik Bala：所有行星对宫位中点(Bhava Madhya)的Sputa Drishti相位。

    基于jyotishganit MIT算法：计算行星到宫位中点的精确角距离，
    使用Sputa Drishti将吉星相位减凶星相位后除以4。

    Args:
        house_signs: 12宫位的星座名称
        house_degrees: 12宫位的宫头度数
        asc_sign: 上升星座名称
        asc_degree: 上升度数(0-30)
        planet_positions: 行星位置 dict {planet: {'sign': str, 'degree': float}}
        planet_shadbala: 行星Shadbala dict

    Returns:
        12个宫位的drik bala值
    """
    BENEFICS = ['Jupiter', 'Venus', 'Mercury']
    MALEFICS = ['Saturn', 'Mars', 'Sun']
    
    asc_sign_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    asc_long = asc_sign_idx * 30 + asc_degree
    
    bala = []
    for house_idx in range(12):
        # 计算宫位中点（Equal House系统中，宫头 + 15°）
        house_cusp = (asc_long + house_idx * 30) % 360
        house_midpoint = (house_cusp + 15) % 360
        
        benefic_sputa = 0.0
        malefic_sputa = 0.0
        
        for planet_name, planet_data in planet_positions.items():
            if planet_name not in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                continue
            
            p_sign = planet_data.get('sign', '')
            p_deg = planet_data.get('degree', 0)
            if p_sign not in SIGNS:
                continue
            
            p_sign_idx = SIGNS.index(p_sign)
            p_long = p_sign_idx * 30 + (p_deg % 30)
            
            # 角距离
            diff = (p_long - house_midpoint + 180) % 360 - 180  # -180 to +180
            dist_deg = abs(diff)
            
            # Sputa Drishti值
            sputa = _get_sputa_drishti(dist_deg)
            
            if planet_name in BENEFICS:
                benefic_sputa += sputa
            elif planet_name in MALEFICS:
                malefic_sputa += sputa
        
        drishtipinda = benefic_sputa - malefic_sputa
        house_drikbala = min(drishtipinda / 4.0, 20.0)
        bala.append(round(house_drikbala, 3))
    
    return bala


def calc_bhava_bala(house_signs: List[str], house_degrees: List[float],
                    asc_sign: str, asc_degree: float,
                    planet_positions: Dict, planet_shadbala: Dict) -> Dict:
    """
    计算完整Bhava Bala（宫位三元力量）。

    Args:
        house_signs: 12宫位的星座名称
        house_degrees: 12宫位的宫头度数
        asc_sign: 上升星座名称
        asc_degree: 上升度数
        planet_positions: 行星位置
        planet_shadbala: 行星Shadbala总分

    Returns:
        完整的Bhava Bala计算结果
    """
    adhipathi = calc_bhava_adhipathi_bala(house_signs, planet_shadbala)
    dig_bala = calc_bhava_dig_bala(house_signs, house_degrees)
    drik_bala = calc_bhava_drik_bala(house_signs, house_degrees, asc_sign, asc_degree,
                                      planet_positions, planet_shadbala)
    
    houses = []
    for i in range(12):
        total = adhipathi[i] + dig_bala[i] + drik_bala[i]
        if total >= 60:
            level = "极强"
        elif total >= 50:
            level = "强"
        elif total >= 40:
            level = "中强"
        elif total >= 30:
            level = "中等"
        elif total >= 20:
            level = "弱"
        else:
            level = "极弱"
        
        houses.append({
            'house': i + 1,
            'sign': house_signs[i] if i < len(house_signs) else SIGNS[i],
            'adhipathi_bala': round(adhipathi[i], 2),
            'dig_bala': round(dig_bala[i], 2),
            'drik_bala': round(drik_bala[i], 2),
            'total': round(total, 2),
            'level': level,
        })
    
    return {
        'method': 'Bhava Bala三元力量（基于jyotishganit MIT算法）',
        'version': '1.0',
        'houses': houses,
        'strongest_house': max(houses, key=lambda h: h['total'])['house'],
        'weakest_house': min(houses, key=lambda h: h['total'])['house'],
    }
