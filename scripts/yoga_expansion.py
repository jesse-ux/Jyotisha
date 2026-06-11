#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yoga规则扩展模块 v1.0
基于 dashaflow (MIT) yoga.py 补充检测规则，用于提升F1

新增检测:
- Kemadruma Yoga (孤月)
- Adhi Yoga (吉星护卫)
- Amala Yoga (10宫吉星)
- Saraswati Yoga (智慧三杰)
- Lakshmi Yoga (财富女神)
- Graha Yuddha (行星战争)
- Gandanta (业力节点)
"""

from typing import Dict, List

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

KENDRA = {1,4,7,10}
TRIKONA = {1,5,9}
DUSTHANA = {6,8,12}
BENEFICS = {"Jupiter","Venus","Mercury"}
MALEFICS = {"Saturn","Mars","Sun","Rahu","Ketu"}

GANDANTA_JUNCTIONS = [(3,4),(7,8),(11,0)]  # Cancer→Leo, Scorpio→Sag, Pisces→Aries
GANDANTA_ORB = 3.3333


def detect_kemadruma(planets: Dict) -> Dict:
    """Kemadruma Yoga: Moon孤立，无行星在2宫或12宫"""
    moon = planets.get('Moon', {})
    moon_sign = moon.get('sign', '')
    if moon_sign not in SIGNS:
        return {'present': False}
    
    moon_idx = SIGNS.index(moon_sign)
    sign_2nd = (moon_idx + 1) % 12
    sign_12th = (moon_idx - 1) % 12
    
    has_support = False
    for pn, pd in planets.items():
        if pn in ('Sun','Moon','Rahu','Ketu'):
            continue
        p_sign = pd.get('sign', '')
        p_idx = SIGNS.index(p_sign) if p_sign in SIGNS else -1
        if p_idx in (sign_2nd, sign_12th):
            has_support = True
            break
    
    return {
        'present': not has_support,
        'name': 'Kemadruma Yoga',
        'description': 'Moon孤立无援—人生孤独感强、自我依赖' if not has_support else 'Kemadruma已解除',
        'planets': ['Moon'],
    }


def detect_adhi_yoga(planets: Dict) -> List[Dict]:
    """Adhi Yoga: 吉星在6/7/8宫从月亮"""
    moon = planets.get('Moon', {})
    moon_sign = moon.get('sign', '')
    if moon_sign not in SIGNS:
        return []
    
    moon_idx = SIGNS.index(moon_sign)
    adhi_planets = []
    target = {6,7,8}
    for pn in BENEFICS:
        pd = planets.get(pn)
        if not pd:
            continue
        p_sign = pd.get('sign', '')
        p_idx = SIGNS.index(p_sign) if p_sign in SIGNS else -1
        house_from_moon = ((p_idx - moon_idx) % 12) + 1
        if house_from_moon in target:
            adhi_planets.append(pn)
    
    if len(adhi_planets) >= 2:
        return [{'name': 'Adhi Yoga', 'planets': adhi_planets,
                 'description': f'吉星{",".join(adhi_planets)}在6/7/8宫—宿命式成功'}]
    return []


def detect_amala_yoga(planets: Dict, asc_sign: str) -> List[Dict]:
    """Amala Yoga: 天然吉星在10宫"""
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    yogas = []
    for pn in BENEFICS:
        pd = planets.get(pn)
        if not pd:
            continue
        p_sign = pd.get('sign', '')
        p_idx = SIGNS.index(p_sign) if p_sign in SIGNS else -1
        house = ((p_idx - asc_idx) % 12) + 1
        if house == 10:
            yogas.append({'name': 'Amala Yoga', 'planet': pn,
                          'description': f'{pn}在10宫—善行得声望、晚年福报'})
    return yogas


def detect_saraswati_yoga(planets: Dict, asc_sign: str) -> Dict:
    """Saraswati Yoga: Jupiter+Venus+Mercury在kendra/trikona/2宫 + Jupiter强"""
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    good_houses = KENDRA | TRIKONA | {2}
    
    ok = []
    for pn in ("Jupiter","Venus","Mercury"):
        pd = planets.get(pn)
        if not pd:
            continue
        p_sign = pd.get('sign', '')
        p_idx = SIGNS.index(p_sign) if p_sign in SIGNS else -1
        house = ((p_idx - asc_idx) % 12) + 1
        if house in good_houses:
            ok.append(pn)
    
    if len(ok) == 3:
        jup = planets.get('Jupiter', {})
        jup_strong = jup.get('dignity', '') in ('own','exalted') or jup.get('house') in KENDRA
        if jup_strong:
            return {'present': True, 'name': 'Saraswati Yoga', 'planets': ok,
                    'description': '智慧三杰聚吉宫—博学多才、表达能力卓越'}
    return {'present': False}


def detect_lakshmi_yoga(planets: Dict, asc_sign: str) -> Dict:
    """Lakshmi Yoga: 9宫主在own/exalted + Venus在own/exalted kendra"""
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    sign_lords = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
                  'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
                  'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
    
    # 9宫主
    h9_sign = SIGNS[(asc_idx + 8) % 12]
    h9_lord = sign_lords[h9_sign]
    h9_data = planets.get(h9_lord, {})
    h9_strong = h9_data.get('dignity', '') in ('own','exalted')
    
    # Venus
    venus = planets.get('Venus', {})
    venus_house = venus.get('house', 0)
    venus_strong = venus_house in KENDRA and venus.get('dignity', '') in ('own','exalted')
    
    if h9_strong and venus_strong:
        return {'present': True, 'name': 'Lakshmi Yoga', 'planets': [h9_lord, 'Venus'],
                'description': '9宫主吉+Venus强—巨大财富与繁荣'}
    return {'present': False}


def detect_graha_yuddha(planets: Dict) -> List[Dict]:
    """Graha Yuddha: 两颗行星相距<1°"""
    war_planets = ['Mars','Mercury','Jupiter','Venus','Saturn']
    wars = []
    for i in range(len(war_planets)):
        for j in range(i+1, len(war_planets)):
            p1, p2 = war_planets[i], war_planets[j]
            d1, d2 = planets.get(p1,{}), planets.get(p2,{})
            if not d1 or not d2:
                continue
            lon1 = d1.get('degree', 0) % 360
            lon2 = d2.get('degree', 0) % 360
            diff = abs(lon1 - lon2) % 360
            if diff > 180:
                diff = 360 - diff
            if diff <= 1.0:
                winner = p1 if lon1 > lon2 else p2
                loser = p2 if winner == p1 else p1
                wars.append({
                    'name': 'Graha Yuddha', 'planet1': p1, 'planet2': p2,
                    'separation': round(diff, 3), 'winner': winner, 'loser': loser,
                    'description': f'{p1}-{p2}行星战争({diff:.2f}°)—{loser}被削弱',
                })
    return wars


def detect_gandanta(planets: Dict) -> List[Dict]:
    """Gandanta: 行星在水火交界3°20'范围内"""
    points = []
    for pn, pd in planets.items():
        lon = pd.get('degree', 0) % 360
        sign_idx = int(lon / 30) % 12
        deg = lon % 30
        for water_idx, fire_idx in GANDANTA_JUNCTIONS:
            if sign_idx == water_idx and deg >= (30 - GANDANTA_ORB):
                points.append({'name': 'Gandanta', 'planet': pn, 'sign': SIGNS[sign_idx],
                    'degree': round(deg, 1), 'junction': f'{SIGNS[water_idx]}-{SIGNS[fire_idx]}',
                    'description': f'{pn}在水火交界—业力节点、灵性转化'})
            if sign_idx == fire_idx and deg <= GANDANTA_ORB:
                points.append({'name': 'Gandanta', 'planet': pn, 'sign': SIGNS[sign_idx],
                    'degree': round(deg, 1), 'junction': f'{SIGNS[water_idx]}-{SIGNS[fire_idx]}',
                    'description': f'{pn}在水火交界—业力节点、灵性转化'})
    return points


def detect_all_yogas(planets: Dict, asc_sign: str = 'Aries') -> List[Dict]:
    """检测所有扩展Yoga"""
    results = []
    
    r = detect_kemadruma(planets)
    if r.get('present'):
        results.append(r)
    
    results.extend(detect_adhi_yoga(planets))
    results.extend(detect_amala_yoga(planets, asc_sign))
    
    r = detect_saraswati_yoga(planets, asc_sign)
    if r.get('present'):
        results.append(r)
    
    r = detect_lakshmi_yoga(planets, asc_sign)
    if r.get('present'):
        results.append(r)
    
    results.extend(detect_graha_yuddha(planets))
    results.extend(detect_gandanta(planets))
    
    return results
