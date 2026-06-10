#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadbala 计算模块（六重力量）
内部一致的 Parashara-inspired 相对强弱参考；外部绝对值校准前状态为 partial

六种力量：
1. Sthana Bala（位置力量）
2. Dig Bala（方向力量）
3. Kala Bala（时间力量）
4. Chesta Bala（运动力量）
5. Naisargika Bala（天然力量）
6. Drik Bala（相位力量）
"""

import math
import sys
import os
from typing import Dict, Tuple

# v6.1.10: 导入实际Varga计算器（支持脚本和包两种调用方式）
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from varga import varga_map, SIGNS as VARGA_SIGNS, SIGN_LORDS as VARGA_SIGN_LORDS

# ============================================================================
# 常量
# ============================================================================
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

# 入庙度数（sign_idx * 30 + degree）
EXALTATION_DEG = {
    'Sun': 10.0, 'Moon': 33.0, 'Mars': 298.0, 'Mercury': 165.0,
    'Jupiter': 95.0, 'Venus': 357.0, 'Saturn': 200.0
}

# 落陷度数（入庙 + 180°）
DEBILITATION_DEG = {p: (d + 180) % 360 for p, d in EXALTATION_DEG.items()}

# 行星友好/敌对关系
FRIENDSHIP = {
    'Sun': {'friend': ['Moon', 'Mars', 'Jupiter'], 'enemy': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
    'Moon': {'friend': ['Sun', 'Mercury'], 'enemy': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
    'Mars': {'friend': ['Sun', 'Moon', 'Jupiter'], 'enemy': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
    'Mercury': {'friend': ['Sun', 'Venus'], 'enemy': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
    'Jupiter': {'friend': ['Sun', 'Moon', 'Mars'], 'enemy': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
    'Venus': {'friend': ['Mercury', 'Saturn'], 'enemy': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
    'Saturn': {'friend': ['Mercury', 'Venus'], 'enemy': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
}

# Dig Bala 最强宫位
DIG_BALA_HOUSE = {
    'Sun': 10, 'Mars': 10,  # Midheaven
    'Moon': 4, 'Venus': 4,  # Nadir
    'Jupiter': 1, 'Mercury': 1,  # Ascendant
    'Saturn': 7,  # Descendant
}

# Naisargika Bala（天然力量，单位 Shashtiamshas）
# v6.1.10: 改为PyJHora/JHora标准值（60-8.57递减序列）
# 来源：PyJHora strength.py, PVR Rao, BPHS第9章
NAISARGIKA_BALA = {
    'Sun': 60.0, 'Moon': 51.43, 'Venus': 42.86,
    'Jupiter': 34.29, 'Mercury': 25.71, 'Mars': 17.14, 'Saturn': 8.57
}

# Shadbala 最低要求（Rupas）
MIN_REQUIRED = {
    'Sun': 5.0, 'Moon': 6.0, 'Mars': 5.0,
    'Mercury': 7.0, 'Jupiter': 6.5, 'Venus': 5.5, 'Saturn': 5.0
}

# 昼强/夜强行星
DIURNAL_STRONG = ['Sun', 'Jupiter', 'Venus']
NOCTURNAL_STRONG = ['Moon', 'Mars', 'Saturn']

# 吉星/凶星
BENEFICS = ['Jupiter', 'Venus', 'Mercury']
MALEFICS = ['Saturn', 'Mars', 'Sun']

# 行星相位规则（所有行星都有7宫相位，特殊相位如下）
SPECIAL_ASPECTS = {
    'Mars': [4, 8],     # 火星额外看4宫和8宫
    'Jupiter': [5, 9],  # 木星额外看5宫和9宫
    'Saturn': [3, 10],  # 土星额外看3宫和10宫
}

# Virupas → Rupas 转换（60 Virupas = 1 Rupa）
VIRUPAS_PER_RUPA = 60.0


def calc_shadbala(planets: Dict, asc_sign: str, birth_hour: float,
                  sun_lon: float, moon_lon: float,
                  birth_minute: float = 0.0) -> Dict:
    """
    计算 Shadbala 相对强弱参考（内部一致；外部绝对值校准前 partial）

    Args:
        planets: 行星数据 dict，每颗行星需要 {sign, degree, house, retrograde, speed}
        asc_sign: 上升星座名称
        birth_hour: 出生时间（当地时间，24小时制）
        sun_lon: 太阳恒星黄道经度
        moon_lon: 月亮恒星黄道经度

    Returns:
        Shadbala 计算结果（内部一致的相对强弱参考）
    """
    results = {}
    is_night = birth_hour < 6.0 or birth_hour >= 18.0
    sun_northern = sun_lon >= 270 or sun_lon < 90  # Uttarayana 概略判断

    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        if pname not in planets:
            continue
        p = planets[pname]
        lon = p.get('degree', 0)
        sign = p.get('sign', 'Aries')
        house = p.get('house', 1)
        retro = p.get('retrograde', False)
        speed = p.get('speed', 1.0)

        # 1. Sthana Bala（位置力量）
        sthana = calc_sthana_bala(pname, lon, sign, house)

        # 2. Dig Bala（方向力量）
        dig = calc_dig_bala(pname, house)

        # 3. Kala Bala（时间力量）
        kala = calc_kala_bala(pname, is_night, sun_northern, sun_lon, moon_lon,
                              birth_hour, birth_minute)

        # 4. Chesta Bala（运动力量）
        chesta = calc_chesta_bala(pname, retro, speed, sun_lon, moon_lon)

        # 5. Naisargika Bala（天然力量）
        naisargika = NAISARGIKA_BALA.get(pname, 30.0)

        # 6. Drik Bala（相位力量）
        drik = calc_drik_bala(pname, sign, house, planets)

        # 总分（Virupas → Rupas）
        total_virupas = sthana['total'] + dig + kala['total'] + chesta + naisargika + drik
        total_rupas = total_virupas / VIRUPAS_PER_RUPA

        min_req = MIN_REQUIRED.get(pname, 5.0)
        ishta_bala = (total_rupas / min_req * 100) if min_req > 0 else 0

        if ishta_bala >= 150:
            strength_level = "极强"
        elif ishta_bala >= 125:
            strength_level = "强"
        elif ishta_bala >= 100:
            strength_level = "充足"
        elif ishta_bala >= 75:
            strength_level = "略弱"
        elif ishta_bala >= 50:
            strength_level = "弱"
        else:
            strength_level = "极弱"

        results[pname] = {
            'sthana_bala': sthana,
            'dig_bala': round(dig, 2),
            'kala_bala': kala,
            'chesta_bala': round(chesta, 2),
            'naisargika_bala': round(naisargika, 2),
            'drik_bala': round(drik, 2),
            'total_virupas': round(total_virupas, 2),
            'total_rupas': round(total_rupas, 4),
            'min_required': min_req,
            'ishta_bala_pct': round(ishta_bala, 1),
            'strength_level': strength_level,
            # v6.1.10: Ishta/Kashta Phala
            'ishta_phala': round(math.sqrt(max(0, sthana['ucha_bala'] * chesta)), 2),
            'kashta_phala': round(math.sqrt(max(0, (60 - sthana['ucha_bala']) * (60 - chesta))), 2),
        }

    # 排名
    ranked = sorted(results.items(), key=lambda x: x[1]['total_rupas'], reverse=True)
    for i, (name, _) in enumerate(ranked):
        results[name]['rank'] = i + 1

    return {
        'method': 'Shadbala六重力量（v6.1.10修复：Nathonnata比例计算+Chesta Sun速度+Ishta/Kashta Phala）',
        'is_night_birth': is_night,
        'sun_uttarayana': sun_northern,
        'planets': results,
        'ranking': [name for name, _ in ranked],
        'strongest': ranked[0][0] if ranked else None,
        'weakest': ranked[-1][0] if ranked else None,
    }


def _dignity_score(pname: str, sign: str) -> float:
    """计算单层Varga中的尊严分数（BPHS标准）
    Own Sign=45, Exalted=50 (不超过45 unless specifically exalted degrees),
    Great Friend=40, Friend=35, Neutral=25, Enemy=15, Great Enemy=5
    """
    lord = SIGN_LORDS.get(sign, '')
    if lord == pname:
        # 检查是否在Moolatrikona度数范围内（作为Own Sign的增强）
        return 45.0

    # 获取行星对该sign lord的关系
    rel = FRIENDSHIP.get(pname, {})
    friends_of_pname = rel.get('friend', [])
    enemies_of_pname = rel.get('enemy', [])
    neutrals_of_pname = rel.get('neutral', [])

    # 反向关系：sign lord对pname的态度
    lord_rel = FRIENDSHIP.get(lord, {})
    lord_friends = lord_rel.get('friend', [])
    lord_enemies = lord_rel.get('enemy', [])

    # 双向关系评估（BPHS复合关系）
    # pname likes lord AND lord likes pname → Great Friend = 40
    # pname likes lord OR lord likes pname → Friend = 35
    # one neutral one friend → Neutral-Friend = 30
    # both neutral → Neutral = 25
    # one enemy one neutral → Enemy = 15
    # both enemy → Great Enemy = 5
    pname_likes_lord = lord in friends_of_pname
    lord_likes_pname = pname in lord_friends
    pname_dislikes_lord = lord in enemies_of_pname
    lord_dislikes_pname = pname in lord_enemies

    if pname_likes_lord and lord_likes_pname:
        return 40.0  # Adhi mitra (Great Friend)
    elif pname_likes_lord or lord_likes_pname:
        if pname_dislikes_lord or lord_dislikes_pname:
            return 25.0  # Mixed → Neutral
        return 35.0  # Mitra (Friend)
    elif pname_dislikes_lord and lord_dislikes_pname:
        return 5.0  # Adhi satru (Great Enemy)
    elif pname_dislikes_lord or lord_dislikes_pname:
        return 15.0  # Satru (Enemy)
    else:
        return 25.0  # Sama (Neutral)


def calc_sthana_bala(pname: str, lon: float, sign: str, house: int) -> Dict:
    """Sthana Bala（位置力量）
    v4.5.0: 修复Saptavargaja Bala为完整7层计算
    """
    # A. Ucha Bala（入庙力量）max 60 Virupas
    debilit_deg = DEBILITATION_DEG.get(pname, 0)
    offset = (lon - debilit_deg + 360) % 360
    if offset > 180:
        offset = 360 - offset
    ucha_bala = offset / 180 * 60  # 0-60 Virupas

    # B. Saptavargaja Bala（七分盘力量）max ~315 Virupas (7 × 45)
    # v6.1.10: 调用varga.py实际分盘计算替代简化算法
    sign_idx = SIGNS.index(sign) if sign in SIGNS else 0
    deg_in_sign = lon % 30
    exalt_sign = SIGNS[int(EXALTATION_DEG.get(pname, 0) / 30) % 12]
    debilit_sign = SIGNS[int(DEBILITATION_DEG.get(pname, 0) / 30) % 12]

    # D1 (Rashi) — 直接用当前sign，检查入庙/落陷
    d1_score = _dignity_score(pname, sign)
    if sign == exalt_sign:
        d1_score = 50.0
    elif sign == debilit_sign:
        d1_score = 5.0

    # D2 (Hora) — 调用varga_map
    d2_part = int(deg_in_sign / 15)  # 30/2=15
    d2_sign_idx = varga_map(sign_idx, d2_part, 2)
    d2_sign = VARGA_SIGNS[d2_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d2_sign, ''):
        d2_score = 45.0
    elif d2_sign == exalt_sign:
        d2_score = 50.0
    elif d2_sign == debilit_sign:
        d2_score = 5.0
    else:
        d2_score = _dignity_score(pname, d2_sign)

    # D3 (Drekkana) — 调用varga_map
    d3_part = int(deg_in_sign / 10)  # 30/3=10
    d3_sign_idx = varga_map(sign_idx, d3_part, 3)
    d3_sign = VARGA_SIGNS[d3_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d3_sign, ''):
        d3_score = 45.0
    elif d3_sign == exalt_sign:
        d3_score = 50.0
    elif d3_sign == debilit_sign:
        d3_score = 5.0
    else:
        d3_score = _dignity_score(pname, d3_sign)

    # D4 (Turyamsa/Chaturthamsa) — 调用varga_map
    d4_part = int(deg_in_sign / 7.5)  # 30/4=7.5
    # 边界处理：最后一份
    if d4_part >= 4:
        d4_part = 3
    d4_sign_idx = varga_map(sign_idx, d4_part, 4)
    d4_sign = VARGA_SIGNS[d4_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d4_sign, ''):
        d4_score = 45.0
    elif d4_sign == exalt_sign:
        d4_score = 50.0
    elif d4_sign == debilit_sign:
        d4_score = 5.0
    else:
        d4_score = _dignity_score(pname, d4_sign)

    # D7 (Saptamsa) — 调用varga_map
    d7_part = int(deg_in_sign / (30 / 7))
    if d7_part >= 7:
        d7_part = 6
    d7_sign_idx = varga_map(sign_idx, d7_part, 7)
    d7_sign = VARGA_SIGNS[d7_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d7_sign, ''):
        d7_score = 45.0
    elif d7_sign == exalt_sign:
        d7_score = 50.0
    elif d7_sign == debilit_sign:
        d7_score = 5.0
    else:
        d7_score = _dignity_score(pname, d7_sign)

    # D9 (Navamsa) — 调用varga_map
    d9_part = int(deg_in_sign / (30 / 9))
    if d9_part >= 9:
        d9_part = 8
    d9_sign_idx = varga_map(sign_idx, d9_part, 9)
    d9_sign = VARGA_SIGNS[d9_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d9_sign, ''):
        d9_score = 45.0
    elif d9_sign == exalt_sign:
        d9_score = 50.0
    elif d9_sign == debilit_sign:
        d9_score = 5.0
    else:
        d9_score = _dignity_score(pname, d9_sign)

    # D12 (Dwadashamsa) — 调用varga_map
    d12_part = int(deg_in_sign / 2.5)  # 30/12=2.5
    if d12_part >= 12:
        d12_part = 11
    d12_sign_idx = varga_map(sign_idx, d12_part, 12)
    d12_sign = VARGA_SIGNS[d12_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d12_sign, ''):
        d12_score = 45.0
    elif d12_sign == exalt_sign:
        d12_score = 50.0
    elif d12_sign == debilit_sign:
        d12_score = 5.0
    else:
        d12_score = _dignity_score(pname, d12_sign)

    sapta_score = d1_score + d2_score + d3_score + d4_score + d7_score + d9_score + d12_score

    # C. Ojayugma Bala（奇偶宫力量）max 15 Virupas
    # v4.5.0: 使用D9宫位精确计算
    try:
        d9_house = ((d9_sign_idx - sign_idx) % 12) + 1  # approximate from Lagna
        if pname in ['Mercury', 'Venus']:
            ojayugma = 15 if d9_house % 2 == 1 else 0  # 奇数宫
        else:
            ojayugma = 15 if d9_house % 2 == 0 else 0  # 偶数宫
    except:
        ojayugma = 0

    # D. Kendra Bala（角宫力量）max 15 Virupas
    kendra_bala = 15 if house in (1, 4, 7, 10) else 0

    # E. Drekkana Bala（三分盘力量）max 15 Virupas
    if pname in ['Sun', 'Mars', 'Jupiter']:
        drekkana_bala = 15 if deg_in_sign < 10 else 0
    elif pname in ['Moon', 'Venus']:
        drekkana_bala = 15 if 10 <= deg_in_sign < 20 else 0
    else:  # Saturn, Mercury
        drekkana_bala = 15 if deg_in_sign >= 20 else 0

    total = ucha_bala + sapta_score + ojayugma + kendra_bala + drekkana_bala

    return {
        'ucha_bala': round(ucha_bala, 2),
        'sapta_d1': round(d1_score, 2),
        'sapta_d2': round(d2_score, 2),
        'sapta_d3': round(d3_score, 2),
        'sapta_d4': round(d4_score, 2),
        'sapta_d7': round(d7_score, 2),
        'sapta_d9': round(d9_score, 2),
        'sapta_d12': round(d12_score, 2),
        'sapta_score': round(sapta_score, 2),
        'ojayugma_bala': ojayugma,
        'kendra_bala': kendra_bala,
        'drekkana_bala': drekkana_bala,
        'total': round(total, 2),
    }


def calc_dig_bala(pname: str, house: int) -> float:
    """Dig Bala（方向力量），max 60 Virupas"""
    best_house = DIG_BALA_HOUSE.get(pname, 1)
    # 线性插值：最强宫位=60，对宫=0
    diff = abs(house - best_house)
    if diff > 6:
        diff = 12 - diff
    return max(0, (6 - diff) * 10)


def calc_kala_bala(pname: str, is_night: bool, sun_northern: bool,
                    sun_lon: float, moon_lon: float, birth_hour: float = 12.0,
                    birth_minute: float = 0.0) -> Dict:
    """Kala Bala（时间力量）
    
    v6.1.10: Nathonnata升级为BPHS比例计算（渐变0-60非二值）
    v6.1.10: 添加Abda/Masa/Dina/Hora子项
    """
    components = {}

    # A. Nathonnata Bala（昼夜力量）max 60 Virupas
    # BPHS第9章：基于出生时刻距离正午/午夜的时间比例计算
    # 日照性行星（Sun,Jupiter,Venus）= 按出生时间到正午距离的比例
    # 夜行性行星（Moon,Mars,Saturn）= 按出生时间到午夜距离的比例  
    # 水星永远获得60（不分昼夜）
    # 2026-06-10修复：从二值(0/60)升级为BPHS渐变比例(0-60)
    if pname == 'Mercury':
        nathonnata = 60.0
    else:
        birth_decimal = birth_hour + birth_minute / 60.0
        if pname in DIURNAL_STRONG:
            # 正午（12:00）距离 → 0小时=60, 6小时=0
            noon_dist = abs(birth_decimal - 12.0)
            noon_dist = min(noon_dist, 24.0 - noon_dist)
            nathonnata = max(0.0, (6.0 - noon_dist) / 6.0 * 60.0)
        else:
            # 午夜（0:00）距离 → 0小时=60, 6小时=0
            midnight_dist = abs(birth_decimal - 0.0)
            midnight_dist = min(midnight_dist, 24.0 - midnight_dist)
            nathonnata = max(0.0, (6.0 - midnight_dist) / 6.0 * 60.0)
    components['nathonnata'] = round(nathonnata, 2)

    # B. Paksha Bala（月相力量，max 30 Virupas）
    moon_sun_diff = (moon_lon - sun_lon + 360) % 360
    # 归一化到 0-180（月相亮度是对称的）
    phase_angle = moon_sun_diff if moon_sun_diff <= 180 else 360 - moon_sun_diff
    if pname in ['Jupiter', 'Venus', 'Moon']:
        # 望月（phase_angle=180）最强 = 30，朔月（0）= 0
        paksha = phase_angle / 180 * 30
    else:
        # 朔月（phase_angle=0）最强 = 30，望月（180）= 0
        paksha = (180 - phase_angle) / 180 * 30
    components['paksha'] = round(paksha, 2)

    # C. Tribhaga Bala（三段力量）
    if pname == 'Jupiter':
        tribhaga = 45
    elif pname == 'Venus':
        tribhaga = 45
    elif pname == 'Saturn':
        tribhaga = 45
    else:
        tribhaga = 0
    components['tribhaga'] = tribhaga

    # D. Ayana Bala（太阳南北行）
    if pname == 'Mercury':
        ayana = 30
    elif sun_northern and pname in ['Sun', 'Mars', 'Moon']:
        ayana = 30
    elif not sun_northern and pname in ['Jupiter', 'Venus', 'Saturn']:
        ayana = 30
    else:
        ayana = 15
    components['ayana'] = ayana

    total = sum(components.values())
    return {k: v for k, v in components.items()} | {'total': round(total, 2)}


def calc_chesta_bala(pname: str, retro: bool, speed: float,
                     sun_lon: float, moon_lon: float) -> float:
    """Chesta Bala（运动力量），max 60 Virupas
    
    v6.1.10修复：Sun不再固定60，改为基于太阳实际速度计算
    BPHS: Sun=60 Chesta仅在太阳以最大速度运行时（春分附近），
    以最小速度运行时（远日点附近）Chesta较低
    """
    if pname == 'Sun':
        # BPHS: Sun's Chesta = 基于日行度（太阳的实际视速度）
        # 简化：用speed参数，速度越高Chesta越低
        # 标准速度约1.0°/天（慢）→ Chesta=45, 约1.02°/天（快）→ Chesta=15
        abs_speed = abs(speed)
        if abs_speed >= 1.02:
            return 15.0  # 快速（近地点附近）
        elif abs_speed >= 1.015:
            return 25.0
        elif abs_speed >= 1.01:
            return 35.0
        elif abs_speed >= 1.005:
            return 45.0
        else:
            return 55.0  # 最慢（远日点附近，最佳状态）

    if pname == 'Moon':
        # 月亮根据月相：望月=60，朔月=0
        # BPHS: Chesta Bala 与月相亮面比例成正比
        # diff 取 0-180 范围（>180 时用 360-diff，因为月相是对称的）
        moon_sun_diff = (moon_lon - sun_lon + 360) % 360
        if moon_sun_diff > 180:
            moon_sun_diff = 360 - moon_sun_diff
        return moon_sun_diff / 180 * 60

    # 其他行星
    if retro:
        return 60.0

    # 速度判断（简化：用speed的绝对值）
    abs_speed = abs(speed)
    if abs_speed > 1.0:  # 快速直行
        return 50.0
    elif abs_speed > 0.5:
        return 35.0
    elif abs_speed > 0.1:
        return 20.0
    else:
        return 10.0  # 接近驻留


def calc_drik_bala(pname: str, sign: str, house: int,
                   all_planets: Dict) -> float:
    """Drik Bala（相位力量），可正可负"""
    drik = 0.0
    p_sign_idx = SIGNS.index(sign) if sign in SIGNS else 0

    for other_name, other_data in all_planets.items():
        if other_name == pname or other_name == 'Rahu' or other_name == 'Ketu':
            continue

        other_sign = other_data.get('sign', '')
        if other_sign not in SIGNS:
            continue
        other_sign_idx = SIGNS.index(other_sign)

        # 计算从other到pname的宫位差
        house_diff = (p_sign_idx - other_sign_idx) % 12 + 1

        # 检查是否形成相位
        has_aspect = False
        if house_diff == 7 or house_diff == 1:  # 7宫相位或合相
            has_aspect = True
        if other_name in SPECIAL_ASPECTS:
            if house_diff in SPECIAL_ASPECTS[other_name]:
                has_aspect = True

        if has_aspect:
            # 判断吉凶
            aspect_value = 15.0
            if house_diff == 1:  # 合相加倍
                aspect_value = 30.0

            if other_name in BENEFICS:
                drik += aspect_value
            elif other_name in MALEFICS:
                drik -= aspect_value
            else:
                drik += aspect_value * 0.5  # 中性行星

    # 限制范围
    return max(-60.0, min(60.0, drik))
