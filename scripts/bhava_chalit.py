#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bhava Chalit 宫位系统 v1.0
MIT License — 基于 dashaflow (adarshj322) 的等宫制实现

Bhava Chalit = 等分宫制，从上升中点(Lagna - 15°)开始，每宫30度
与整宫制(Whole Sign)的区别：靠近星座边界的行星可能跨宫
"""
from typing import Dict, List, Tuple

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']


def calculate_bhava_chalit(asc_lon: float, raw_planets: Dict) -> Dict:
    """
    Bhava Chalit 计算（等宫制从上升中点划分）
    
    规则：
      - 第1宫中点(Bhava Madhya) = Lagna 经度
      - 第1宫起点 = Lagna - 15°
      - 每宫跨度 = 30°
      - 行星的Bhava宫位可能与其Rashi(整宫)宫位不同
    
    Args:
        asc_lon: 上升点黄道经度 (0-360)
        raw_planets: {planet_name: {"lon": float, ...}} 
                     每颗行星需要lon（黄道经度）和sign_idx（星座索引）
    
    Returns:
        dict: {planet_name: {"bhava_house": int, "rashi_house": int, "shifted": bool}}
    """
    cusp_start = (asc_lon - 15.0) % 360.0
    asc_sign_idx = int(asc_lon / 30) % 12

    result = {}
    for name, rp in raw_planets.items():
        planet_lon = rp.get("lon", 0)
        
        # 整宫制
        sign_idx = rp.get("sign_idx", int(planet_lon / 30) % 12)
        rashi_house = ((sign_idx - asc_sign_idx) % 12) + 1
        
        # Bhava 宫位（等宫制）
        diff = (planet_lon - cusp_start) % 360.0
        bhava_house = int(diff / 30.0) + 1
        if bhava_house > 12:
            bhava_house = 12

        result[name] = {
            "bhava_house": bhava_house,
            "rashi_house": rashi_house,
            "shifted": bhava_house != rashi_house,
        }

    return result


def get_bhava_cusps(asc_lon: float) -> List[float]:
    """
    获取所有12宫的Bhava Cusp（宫头）经度
    
    Returns:
        12个float，第1宫到第12宫的Cusp经度
    """
    cusp_start = (asc_lon - 15.0) % 360.0
    return [(cusp_start + i * 30.0) % 360.0 for i in range(12)]


def get_bhava_madhyas(asc_lon: float) -> List[float]:
    """
    获取所有12宫的Bhava Madhya（宫中点）经度
    
    Returns:
        12个float，第1宫到第12宫的中点经度
    """
    return [(asc_lon + i * 30.0) % 360.0 for i in range(12)]


def get_bhava_ranges(asc_lon: float) -> List[Tuple[float, float]]:
    """
    获取每个宫位的起止范围
    
    Returns:
        12个tuple (start, end)，第1宫到第12宫的经度范围
    """
    cusps = get_bhava_cusps(asc_lon)
    ranges = []
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if end <= start:
            end += 360
        ranges.append((start, end))
    return ranges


def planet_in_which_bhava(planet_lon: float, asc_lon: float) -> int:
    """
    判断行星经度落在哪个Bhava宫（1-12）
    """
    cusps = get_bhava_cusps(asc_lon)
    for i in range(12):
        start = cusps[i]
        end = cusps[(i + 1) % 12]
        if end <= start:
            end += 360
        plon = planet_lon if planet_lon >= start else planet_lon + 360
        if start <= plon < end:
            return i + 1
    return 12


def cross_house_check(asc_lon: float, planet_name: str, planet_lon: float,
                      planet_sign_idx: int) -> Dict:
    """
    跨宫检查：判断行星是否因Bhava Chalit而换宫
    
    Returns:
        {"planet": str, "rashi_house": int, "bhava_house": int, 
         "shifted": bool, "delta_degrees": float}
    """
    asc_sign_idx = int(asc_lon / 30) % 12
    rashi_house = ((planet_sign_idx - asc_sign_idx) % 12) + 1
    bhava_house = planet_in_which_bhava(planet_lon, asc_lon)
    
    delta = abs(bhava_house - rashi_house)
    if delta > 6:
        delta = 12 - delta
    
    return {
        "planet": planet_name,
        "rashi_house": rashi_house,
        "bhava_house": bhava_house,
        "shifted": bhava_house != rashi_house,
        "delta_houses": delta,
    }
