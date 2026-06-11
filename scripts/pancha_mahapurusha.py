#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pancha Mahapurusha Yoga（五王瑜伽）完整检测模块 v1.0
基于BPHS和dashaflow (MIT) detect_yogas核心算法

五种瑜伽：
- Ruchaka Yoga (Mars)
- Bhadra Yoga (Mercury)
- Hamsa Yoga (Jupiter)
- Malavya Yoga (Venus)
- Shasha Yoga (Saturn)

含完整的燃烧(Combustion)/逆行(Retrograde)/受克(Affliction)失效条件检测
"""

from typing import Dict, List, Optional

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

KENDRA_HOUSES = {1, 4, 7, 10}
MAHAPURUSHA_PLANETS = {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

MAHAPURUSHA_NAMES = {
    "Mars": "Ruchaka Yoga",
    "Mercury": "Bhadra Yoga",
    "Jupiter": "Hamsa Yoga",
    "Venus": "Malavya Yoga",
    "Saturn": "Shasha Yoga",
}

MAHAPURUSHA_EFFECTS = {
    "Ruchaka": "军事领袖、建筑大师、体魄强健、勇敢果断",
    "Bhadra": "演说家、学者、机智聪慧、商业头脑",
    "Hamsa": "精神导师、哲学家、富足慷慨、智慧卓越",
    "Malavya": "艺术家、享乐者、魅力超凡、审美敏锐",
    "Shasha": "政治家、长者、坚韧执着、权威地位",
}

EXALTATION = {'Sun':('Aries',10),'Moon':('Taurus',3),'Mars':('Capricorn',28),'Mercury':('Virgo',15),'Jupiter':('Cancer',5),'Venus':('Pisces',27),'Saturn':('Libra',20)}
OWN_SIGNS = {'Sun':{'Leo'},'Moon':{'Cancer'},'Mars':{'Aries','Scorpio'},'Mercury':{'Gemini','Virgo'},'Jupiter':{'Sagittarius','Pisces'},'Venus':{'Taurus','Libra'},'Saturn':{'Capricorn','Aquarius'}}

# Combustion orb (degrees from Sun)
COMBUSTION_ORB = {'Mars':17,'Mercury':12,'Jupiter':11,'Venus':10,'Saturn':15}

NATURAL_MALEFICS = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}


def _is_exalted_or_own(planet: str, sign: str) -> bool:
    if planet in EXALTATION and EXALTATION[planet][0] == sign:
        return True
    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return True
    return False


def _is_combust(planet: str, planet_degree: float, sun_degree: float) -> bool:
    """检查行星是否被太阳燃烧"""
    orb = COMBUSTION_ORB.get(planet, 10)
    diff = abs(planet_degree - sun_degree)
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def _has_malefic_aspect(planet_sign: str, all_planets: Dict) -> List[str]:
    """检查是否有凶星合相/相位该行星"""
    afflicting = []
    for pn, pd in all_planets.items():
        if pn == planet_sign or pn not in NATURAL_MALEFICS:
            continue
        # 简单合相检查
        if pd.get('sign') == planet_sign:
            afflicting.append(pn)
    return afflicting


def detect_pancha_mahapurusha(planets: Dict, sun_degree: float = None) -> List[Dict]:
    """
    检测所有Pancha Mahapurusha Yoga，含失效条件。

    Args:
        planets: {planet: {'sign': str, 'house': int, 'degree': float, ...}}
        sun_degree: 太阳黄道经度(用于燃烧检测)

    Returns:
        检测到的PMC Yoga列表
    """
    yogas = []
    sun_deg = sun_degree

    for planet in MAHAPURUSHA_PLANETS:
        pd = planets.get(planet)
        if not pd:
            continue

        sign = pd.get('sign', '')
        house = pd.get('house', 0)

        # 基本条件：在Kendra + own/exalted
        if house not in KENDRA_HOUSES:
            continue
        if not _is_exalted_or_own(planet, sign):
            continue

        yoga_name = MAHAPURUSHA_NAMES[planet]
        effect = MAHAPURUSHA_EFFECTS.get(yoga_name.replace(" Yoga", ""), "")

        # 检查失效条件
        cancellations = []
        is_valid = True

        # 1. 燃烧检测
        if sun_deg is not None:
            planet_deg = pd.get('degree', 0)
            if _is_combust(planet, planet_deg, sun_deg):
                cancellations.append(f"{planet}被太阳燃烧(orb < {COMBUSTION_ORB.get(planet,10)}°) — Yoga效力大减")
                is_valid = False

        # 2. 逆行检测
        if pd.get('retrograde', False):
            cancellations.append(f"{planet}逆行 — Yoga效力减弱")
            is_valid = False

        # 3. 凶星受克
        malefics = _has_malefic_aspect(sign, planets)
        if malefics:
            cancellations.append(f"{planet}受凶星合相: {', '.join(malefics)} — Yoga部分失效")
            is_valid = False

        # 4. Navamsa弱势（D9中落陷）
        navamsa_sign = pd.get('navamsa_sign', '')
        if navamsa_sign in OWN_SIGNS.get(planet, set()) or (planet in EXALTATION and EXALTATION[planet][0] == navamsa_sign):
            pass  # D9 also strong → yoga reinforced
        elif navamsa_sign:
            # Check if debilitated in D9
            deb_sign_idx = (SIGNS.index(EXALTATION[planet][0]) + 6) % 12 if planet in EXALTATION and planet != 'Rahu' and planet != 'Ketu' else -1
            if deb_sign_idx >= 0 and navamsa_sign == SIGNS[deb_sign_idx]:
                cancellations.append(f"{planet}在Navamsa落陷 — Yoga根基不稳")
                is_valid = False

        yogas.append({
            'name': yoga_name,
            'planet': planet,
            'sign': sign,
            'house': house,
            'is_valid': is_valid,
            'strength': '完整' if is_valid else '削弱',
            'effect': effect,
            'cancellations': cancellations,
        })

    return yogas


def assess_pmc_strength(planets: Dict, sun_degree: float = None) -> Dict:
    """
    评估Pancha Mahapurusha Yoga总体强度。

    Returns:
        PMC评估结果
    """
    yogas = detect_pancha_mahapurusha(planets, sun_degree)
    valid = [y for y in yogas if y['is_valid']]
    invalid = [y for y in yogas if not y['is_valid']]

    if len(valid) >= 2:
        assessment = "多重大王瑜伽 — 命主在不同领域均有杰出天赋"
    elif len(valid) == 1:
        assessment = f"{valid[0]['name']} — 命主在特定领域有卓越潜力"
    elif len(invalid) > 0:
        st = [y['planet'] for y in invalid]
        assessment = f"瑜伽潜质存在但因{', '.join(st)}受克而削弱"
    else:
        assessment = "无Pancha Mahapurusha Yoga"

    return {
        'method': 'Pancha Mahapurusha Yoga 完整检测 v1.0',
        'yogas': yogas,
        'valid_count': len(valid),
        'invalid_count': len(invalid),
        'assessment': assessment,
    }
