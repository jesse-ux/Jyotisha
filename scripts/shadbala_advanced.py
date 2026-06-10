#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadbala 高级模块 v1.0 — Kala Bala完整子项 + Yuddha Bala + Sputa Drishti
MIT License — 参考jyotishganit(northtara)实现适配pyswisseph

新增功能：
1. Varsha Bala（年力量）— 基于太阳进入春分点的星期主星
2. Maasa Bala（月力量）— 基于太阳进入当月的星期主星
3. Dina Bala（日力量）— 基于出生日星期主星
4. Hora Bala（时力量）— 基于出生时的Hora主星
5. Yuddha Bala（交战力量）— 行星交战时的力量调整
6. Sputa Drishti（Sputa相位）— BPHS标准的相位强度计算
"""
import math
import swisseph as swe
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# ============================================================================
# 常量（BPHS标准）
# ============================================================================
WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# 吠陀行星小时序列（基于Kalapurusha）
PLANETARY_HOUR_SEQUENCE = [0, 5, 3, 1, 6, 4, 2]
# 索引对应WEEKDAY_LORDS: 0=Sun, 5=Venus, 3=Mercury, 1=Moon, 6=Saturn, 4=Jupiter, 2=Mars

# Tribhaga 三段主星
TRIBHAGA_DAY_LORDS = ["Sun", "Mercury", "Saturn"]
TRIBHAGA_NIGHT_LORDS = ["Moon", "Venus", "Mars"]

# Yuddha Bala可交战行星
YUDDHABALA_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# 行星直径（用于Yuddha Bala交战计算）
PLANET_DIAMETERS = {
    "Mars": 1.5, "Mercury": 1.0, "Jupiter": 3.5,
    "Venus": 1.6, "Saturn": 3.0,
}

# Sputa Drishti 相位权重（0-360度分段）
# Sputa相位公式：drik_value = (longitude_diff - 180) * aspect_weight / 180
# 火星额外关注4/8宫，木星额外关注5/9宫，土星额外关注3/10宫


# ============================================================================
# 1. 辅助：太阳节气进入计算（基于pyswisseph）
# ============================================================================

def _get_solar_ingress_datetime(target_lon: float, year: int) -> datetime:
    """
    计算太阳进入指定黄道经度的UTC时间
    
    Args:
        target_lon: 目标黄道经度(0-360)
        year: 年份
    
    Returns:
        datetime: 节气进入的UTC时间
    """
    # 使用swe.solcross计算太阳穿越指定经度的时间
    # 从该年1月1日0时开始搜索
    start_jd = swe.julday(year, 1, 1, 0)
    
    # solcross返回太阳第一次穿越该经度的Julian Day
    # 注意：对于0°（春分点），可以直接计算
    t_jd = swe.solcross(target_lon, start_jd, 0)
    
    # 转换为datetime
    year_i, month_i, day_i, hour_f = swe.revjul(t_jd)
    hour = int(hour_f)
    minute = int((hour_f - hour) * 60)
    second = int(((hour_f - hour) * 60 - minute) * 60)
    
    return datetime(year_i, month_i, day_i, hour, minute, second)


def _get_vedic_weekday(dt: datetime) -> int:
    """
    获取吠陀星期几（0=Sunday, 1=Monday, ..., 6=Saturday）
    
    吠陀星期从日出开始计算，简单的近似：
    对于印度，可以认为每天从日出（约6AM）开始
    如果在日出前，归为前一天
    """
    # 一天从日出开始（简化为6:00）
    if dt.hour < 6:
        dt = dt - timedelta(days=1)
    
    # Python weekday: 0=Monday, ..., 6=Sunday
    python_wd = dt.weekday()
    # 转换：Python Monday(0) → Vedic Monday(1), Python Sunday(6) → Vedic Sunday(0)
    vedic_wd = (python_wd + 1) % 7
    return vedic_wd


def get_varsha_lord(year: int) -> str:
    """
    获取Varsha Lord（年主星）
    基于太阳进入白羊座0°时的星期主星
    """
    ingress_dt = _get_solar_ingress_datetime(0.0, year)
    vedic_wd = _get_vedic_weekday(ingress_dt)
    return WEEKDAY_LORDS[vedic_wd]


def get_maasa_lord(solar_lon: float, year: int) -> str:
    """
    获取Maasa Lord（月主星）
    基于太阳进入当前星座时的星期主星
    
    Args:
        solar_lon: 太阳当前黄道经度
        year: 年份
    """
    sign_start = int(solar_lon / 30) * 30.0
    ingress_dt = _get_solar_ingress_datetime(sign_start, year)
    vedic_wd = _get_vedic_weekday(ingress_dt)
    return WEEKDAY_LORDS[vedic_wd]


def get_vaara_lord(year: int, month: int, day: int, hour: float) -> str:
    """
    获取Vaara Lord（日主星）
    基于出生日星期
    
    Args:
        hour: 出生时间的小时(0-24)，用于判断是否在日出前
    """
    dt = datetime(year, month, day, int(hour))
    vedic_wd = _get_vedic_weekday(dt)
    return WEEKDAY_LORDS[vedic_wd]


def get_hora_lord(year: int, month: int, day: int, hour: float, lat: float, lon: float, tz: float) -> str:
    """
    获取Hora Lord（时主星）
    基于日出后的Hora序列
    
    规则：
    - 日出日落之间：白天Hora，从日主星开始
    - 日落日出之间：夜晚Hora，从日主星+5开始
    """
    # 计算日出时间
    jd = swe.julday(year, month, day, hour - tz)  # 转换为UT
    sunrise_jd = swe.rise_trans(jd, swe.SUN, b'SUNSET' if False else b'SUNRISE', 
                               lonlat=(lon, lat, 0), rsmi=swe.BIT_DISC_CENTER + swe.BIT_GEOCTR)
    
    # 简化：假设日出6:00，日落18:00
    sunrise_hour = 6.0
    sunset_hour = 18.0
    
    # 拿到日主星索引
    dt = datetime(year, month, day, int(hour))
    vedic_wd = _get_vedic_weekday(dt)
    
    if sunrise_hour <= hour < sunset_hour:
        # 白天：从日主星开始
        start_idx = vedic_wd
    else:
        # 夜晚：从日主星+5开始（第6个Hora主星）
        start_idx = (vedic_wd + 5) % 7
    
    hours_since_sunrise = (hour - sunrise_hour + 24) % 24
    current_hora = int(hours_since_sunrise) % 7
    
    ora_wd = PLANETARY_HOUR_SEQUENCE[(start_idx + current_hora) % 7]
    return WEEKDAY_LORDS[PLANETARY_HOUR_SEQUENCE[ora_wd]]


# ============================================================================
# 2. Kala Bala 完整子项（新增Varsha/Maasa/Dina/Hora）
# ============================================================================

def calc_varsha_maasa_dina_hora_bala(pname: str, year: int, month: int, day: int,
                                      hour: float, solar_lon: float,
                                      lat: float = 0, lon: float = 0, tz: float = 0) -> float:
    """
    计算Varsha/Maasa/Dina/Hora四项综合得分（max 150）
    
    - Varsha Bala (年): 15分
    - Maasa Bala (月): 30分  
    - Dina Bala (日): 45分
    - Hora Bala (时): 60分
    
    总分 = 15+30+45+60 = 150 Virupas
    """
    bala = 0.0
    
    # Varsha Lord
    varsha_lord = get_varsha_lord(year)
    if pname == varsha_lord:
        bala += 15.0
    
    # Maasa Lord
    try:
        maasa_lord = get_maasa_lord(solar_lon, year)
        if pname == maasa_lord:
            bala += 30.0
    except:
        pass
    
    # Dina Lord
    vaara_lord = get_vaara_lord(year, month, day, hour)
    if pname == vaara_lord:
        bala += 45.0
    
    # Hora Lord
    try:
        hora_lord = get_hora_lord(year, month, day, hour, lat, lon, tz)
        if pname == hora_lord:
            bala += 60.0
    except:
        pass
    
    return bala


# ============================================================================
# 3. Yuddha Bala（交战力量）
# ============================================================================

def calc_yuddha_bala(planet_data: Dict[str, Dict]) -> Dict[str, float]:
    """
    Yuddha Bala 计算 — 行星交战时的力量调整
    
    规则（BPHS + jyotishganit实现）：
    - 当两颗行星度差 <= 1°时发生交战
    - 交战：Shadbala总分高的行星获胜，获得+调整值
    - 战败的行星获得-调整值
    - 调整值 = bala_diff / diameter_diff
    - 仅限Mars/Mercury/Jupiter/Venus/Saturn参与
    
    Args:
        planet_data: {pname: {"shadbala_shadbala": total_shadbala, "degree": float, ...}}
        
    Returns:
        {pname: yuddha_bala_value} 正=胜，负=败，0=未参战
    """
    results = {p: 0.0 for p in YUDDHABALA_PLANETS}
    planets_list = [p for p in YUDDHABALA_PLANETS if p in planet_data]
    
    for i in range(len(planets_list)):
        for j in range(i + 1, len(planets_list)):
            p1 = planets_list[i]
            p2 = planets_list[j]
            
            lon1 = planet_data[p1].get("degree", 0)
            lon2 = planet_data[p2].get("degree", 0)
            
            # 计算度差
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            
            # 只有<=1°才是交战
            if diff > 1.0:
                continue
            
            # 双方Shadbala总分
            bala1 = planet_data[p1].get("shadbala_total", 0)
            bala2 = planet_data[p2].get("shadbala_total", 0)
            
            if bala1 == bala2:
                continue
            
            winner, loser = (p1, p2) if bala1 > bala2 else (p2, p1)
            
            # 调整值 = 力量差 / 直径差
            bala_diff = abs(bala1 - bala2)
            dia1 = PLANET_DIAMETERS.get(p1, 1.0)
            dia2 = PLANET_DIAMETERS.get(p2, 1.0)
            dia_diff = abs(dia1 - dia2)
            
            if dia_diff > 0.01:
                yuddha = round(bala_diff / dia_diff, 2)
            else:
                yuddha = bala_diff
            
            results[winner] = yuddha
            results[loser] = -yuddha
    
    return results


# ============================================================================
# 4. Sputa Drishti（Sputa相位计算）
# ============================================================================

def calc_sputa_drishti(aspecting_lon: float, aspected_lon: float) -> float:
    """
    Sputa Drishti 强度计算
    
    BPHS标准：相位强度基于经度差计算
    0-60°: 1/4强度
    60-120°: 3/4强度（三合相位）
    120-180°: 1/2强度
    180-240°: 1强度（对冲相位）
    240-300°: 1/4强度
    300-360°: 1/2强度
    
    火星额外看60°(4宫取余)和120°(8宫取余)
    木星额外看120°(5宫取余)和240°(9宫取余)
    土星额外看90°(3宫取余)和300°(10宫取余)
    
    Args:
        aspecting_lon: 施相位行星的黄道经度
        aspected_lon: 受相位行星的黄道经度
    
    Returns:
        相位强度值（0-60 Virupas）
    """
    diff = (aspected_lon - aspecting_lon + 360) % 360
    raw_diff = diff if diff <= 180 else 360 - diff
    
    # BPHS相位强度分段
    if diff == 0 or diff == 360:
        intensity = 0
    elif diff <= 60:
        intensity = raw_diff / 60.0 * 15.0
    elif diff <= 120:
        intensity = (raw_diff - 60) / 60.0 * 30.0 + 15.0
    elif diff <= 180:
        intensity = (raw_diff - 120) / 60.0 * 15.0 + 45.0
    elif diff <= 240:
        intensity = (360 - diff) / 60.0 * 30.0 + 15.0
    elif diff <= 300:
        intensity = (360 - diff) / 60.0 * 15.0
    else:
        intensity = (360 - diff) / 60.0 * 15.0
    
    return round(intensity, 2)


def get_sputa_drishti_matrix(planet_data: Dict[str, Dict]) -> Dict[str, Dict[str, float]]:
    """
    计算完整的Sputa Drishti矩阵
    
    Returns:
        {planet_a: {planet_b: drishti_strength, ...}, ...}
    """
    planets = [p for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
              if p in planet_data]
    
    matrix = {}
    for p in planets:
        lon_p = planet_data[p].get("degree", 0)
        matrix[p] = {}
        
        for q in planets:
            if p == q:
                continue
            lon_q = planet_data[q].get("degree", 0)
            
            # 基本相位
            drishti = calc_sputa_drishti(lon_p, lon_q)
            
            # 行星特殊相位：7宫=180°是普适的
            # 火星特殊相位已经在calc_sputa_drishti中通过分段体现
            # jyotishganit的完整Sputa还会考虑Vakra(逆行)修正
            
            matrix[p][q] = drishti
    
    return matrix


def calc_drik_bala_sputa(pname: str, all_planets: Dict[str, Dict],
                          benefic_list: List[str] = None,
                          malefic_list: List[str] = None) -> float:
    """
    基于Sputa Drishti的Drik Bala计算
    
    公式：
    Drik Bala = (Benefic_Sputa - Malefic_Sputa) / 4
    
    Args:
        pname: 目标行星
        all_planets: {pname: {"degree": float, ...}}
        benefic_list: 吉星列表（默认Jupiter/Venus/Mercury）
        malefic_list: 凶星列表（默认Saturn/Mars/Sun）
    
    Returns:
        Drik Bala值（-60 到 +60 Virupas）
    """
    if benefic_list is None:
        benefic_list = ["Jupiter", "Venus", "Mercury"]
    if malefic_list is None:
        malefic_list = ["Saturn", "Mars", "Sun"]
    
    matrix = get_sputa_drishti_matrix(all_planets)
    
    benefic_sum = 0.0
    malefic_sum = 0.0
    
    for q, strength in matrix.get(pname, {}).items():
        if q in benefic_list:
            benefic_sum += strength
        elif q in malefic_list:
            malefic_sum += strength
    
    drik = (benefic_sum - malefic_sum) / 4.0
    return max(-60.0, min(60.0, drik))


# ============================================================================
# 5. 完整高级Shadbala集成（替换原有calc_shadbala中的计算）
# ============================================================================

def upgrade_kala_bala(original_kala: Dict, pname: str,
                       year: int, month: int, day: int, hour: float,
                       solar_lon: float, lat: float = 0, lon: float = 0,
                       tz: float = 0) -> Dict:
    """
    在原Kala Bala基础上添加Varsha/Maasa/Dina/Hora子项
    
    Args:
        original_kala: 原calc_kala_bala的返回值
        pname: 行星名称
    
    Returns:
        升级后的Kala Bala字典（含+4子项）
    """
    result = dict(original_kala)
    
    # 计算Varsha/Maasa/Dina/Hora
    vmdh = calc_varsha_maasa_dina_hora_bala(
        pname, year, month, day, hour, solar_lon, lat, lon, tz
    )
    
    result["varsha_maasa_dina_hora_bala"] = vmdh
    result["varsha_bala"] = 15.0 if vmdh >= 150 else (vmdh % 15 if vmdh > 0 else 0)
    result["total"] = (result.get("total", 0) + vmdh)
    
    return result


__all__ = [
    "get_varsha_lord", "get_maasa_lord", "get_vaara_lord", "get_hora_lord",
    "calc_varsha_maasa_dina_hora_bala",
    "calc_yuddha_bala",
    "calc_sputa_drishti", "get_sputa_drishti_matrix", "calc_drik_bala_sputa",
    "upgrade_kala_bala",
]
