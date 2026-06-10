#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Argala（门闩）行星干预模块 v1.1

从旧版“逐行星Argala”升级为“逐参考点/逐宫完整Argala”：
- 主Argala: 2/4/11宫
- Virodhargala: 12/10/3宫分别阻挡2/4/11宫
- 特殊Argala: 第3宫有2颗以上凶星
- 次级Argala: 5/9宫
- Argala Rajayoga分类: Poornargala / Tripadargala / Ardhargala / Padargala

MIT复用来源：
- jaimini-tropical/jaimini/core/argala.py (tunanfang-pixel, MIT)
适配：使用本项目 chart 输出的英文行星名与恒星黄道星座索引。
"""
from typing import Dict, List

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

NATURAL_MALEFICS = {'Sun', 'Mars', 'Saturn'}
NATURAL_BENEFICS = {'Moon', 'Mercury', 'Jupiter', 'Venus'}
NODES = {'Rahu', 'Ketu'}

PRIMARY_ARGALA = {2, 4, 11}
VIRODHARGALA_MAP = {2: 12, 4: 10, 11: 3}
SECONDARY_ARGALA = {5, 9}


def _house_from(ref_sign_idx: int, offset: int) -> int:
    """从参考星座起算第offset宫对应的星座索引。"""
    return (ref_sign_idx + offset - 1) % 12


def _planets_in_sign(sign_idx: int, planet_sign_indices: Dict[str, int], include_nodes: bool = False) -> List[str]:
    planets = []
    for pname, psi in planet_sign_indices.items():
        if not include_nodes and pname in NODES:
            continue
        if psi % 12 == sign_idx % 12:
            planets.append(pname)
    return planets


def classify_argala_rajayoga(argala_result: Dict) -> Dict:
    """按主Argala占据数量分类Rajayoga强度。"""
    primary = argala_result.get('primary', {})
    occupied = sum(1 for h in ['H2', 'H4', 'H11'] if primary.get(h, {}).get('planets'))
    blocked = sum(1 for h in ['H2', 'H4', 'H11'] if primary.get(h, {}).get('blockers'))
    if occupied == 3:
        return {'type': 'Poornargala', 'level': 4, 'cn': '完整Argala，最强支持'}
    if occupied == 2:
        return {'type': 'Tripadargala', 'level': 3, 'cn': '三足Argala，强支持'}
    if occupied == 1:
        return {'type': 'Ardhargala', 'level': 2, 'cn': '半Argala，中等支持'}
    if blocked:
        return {'type': 'Padargala', 'level': 1, 'cn': '弱Argala且受阻'}
    return {'type': 'None', 'level': 0, 'cn': '无明显Argala'}


def calc_argala_for_reference(ref_sign_idx: int, planet_sign_indices: Dict[str, int], include_nodes: bool = False) -> Dict:
    """计算单一参考点的完整Argala。"""
    result = {
        'ref_sign': SIGNS[ref_sign_idx],
        'ref_sign_idx': ref_sign_idx,
        'primary': {},
        'specific': None,
        'secondary': {},
        'argala_count': 0,
        'virodhargala_count': 0,
        'net_result': 'neutral',
    }

    for h in sorted(PRIMARY_ARGALA):
        argala_sign = _house_from(ref_sign_idx, h)
        planets = _planets_in_sign(argala_sign, planet_sign_indices, include_nodes)
        block_h = VIRODHARGALA_MAP[h]
        block_sign = _house_from(ref_sign_idx, block_h)
        blockers = _planets_in_sign(block_sign, planet_sign_indices, include_nodes)
        effective = len(planets) > len(blockers)
        result['primary'][f'H{h}'] = {
            'house_from_reference': h,
            'sign': SIGNS[argala_sign],
            'sign_idx': argala_sign,
            'planets': planets,
            'blocked_by_house': block_h,
            'blocked_by_sign': SIGNS[block_sign],
            'blockers': blockers,
            'effective': effective,
            'effect': _argala_effect(h, planets, blockers),
        }
        if planets:
            result['argala_count'] += 1
        if blockers:
            result['virodhargala_count'] += 1

    h3_sign = _house_from(ref_sign_idx, 3)
    h3_planets = _planets_in_sign(h3_sign, planet_sign_indices, include_nodes)
    h3_malefics = [p for p in h3_planets if p in NATURAL_MALEFICS]
    result['specific'] = {
        'house': 3,
        'sign': SIGNS[h3_sign],
        'sign_idx': h3_sign,
        'planets': h3_planets,
        'malefics': h3_malefics,
        'effective': len(h3_malefics) >= 2,
        'rule': '第3宫有2颗以上天然凶星形成特殊Argala',
    }
    if result['specific']['effective']:
        result['argala_count'] += 1

    for h in sorted(SECONDARY_ARGALA):
        sign_idx = _house_from(ref_sign_idx, h)
        planets = _planets_in_sign(sign_idx, planet_sign_indices, include_nodes)
        result['secondary'][f'H{h}'] = {
            'house_from_reference': h,
            'sign': SIGNS[sign_idx],
            'sign_idx': sign_idx,
            'planets': planets,
        }

    if result['argala_count'] > result['virodhargala_count']:
        result['net_result'] = 'supported'
    elif result['argala_count'] < result['virodhargala_count']:
        result['net_result'] = 'obstructed'
    result['rajayoga_classification'] = classify_argala_rajayoga(result)
    return result


def calc_argala(planet_sign_indices: Dict[str, int], asc_sign_idx: int, include_nodes: bool = False) -> Dict:
    """
    计算全盘Argala。

    Args:
        planet_sign_indices: {'Sun': 0, 'Moon': 3, ...}
        asc_sign_idx: 上升星座索引
        include_nodes: 是否把Rahu/Ketu纳入占位阻挡统计（默认False，遵循Jaimini七行星口径）
    """
    houses = {}
    for house_num in range(1, 13):
        ref_sign_idx = (asc_sign_idx + house_num - 1) % 12
        houses[f'house_{house_num}'] = calc_argala_for_reference(ref_sign_idx, planet_sign_indices, include_nodes)

    planet_refs = {}
    for pname, sign_idx in planet_sign_indices.items():
        if pname in NODES and not include_nodes:
            continue
        planet_refs[pname] = calc_argala_for_reference(sign_idx, planet_sign_indices, include_nodes)

    summary = _summarize_argala(houses)
    return {
        'method': 'Jaimini Argala + Virodhargala (jaimini-tropical MIT adapted)',
        'version': '1.1',
        'include_nodes': include_nodes,
        'ascendant': SIGNS[asc_sign_idx],
        'houses': houses,
        'planets': planet_refs,
        'summary': summary,
    }


def _summarize_argala(houses: Dict) -> Dict:
    supported = []
    obstructed = []
    strongest = []
    for house_key, data in houses.items():
        if data['net_result'] == 'supported':
            supported.append(house_key)
        elif data['net_result'] == 'obstructed':
            obstructed.append(house_key)
        level = data.get('rajayoga_classification', {}).get('level', 0)
        strongest.append((house_key, level, data.get('rajayoga_classification', {}).get('type')))
    strongest.sort(key=lambda x: x[1], reverse=True)
    return {
        'supported_houses': supported,
        'obstructed_houses': obstructed,
        'top_argala_houses': [{'house': h, 'level': lvl, 'type': typ} for h, lvl, typ in strongest[:5] if lvl > 0],
        'supported_count': len(supported),
        'obstructed_count': len(obstructed),
    }


def _argala_effect(house: int, planets: List[str], blockers: List[str]) -> str:
    if not planets:
        return '无行星形成此类Argala'
    base = {
        2: '资源、语言、家族与财务支持',
        4: '内在稳定、住所、母亲、教育与幸福感支持',
        11: '收益、人脉、愿望实现与社会网络支持',
    }.get(house, '一般支持')
    if blockers and len(blockers) >= len(planets):
        return f'{base}，但被{len(blockers)}个Virodhargala阻挡'
    if blockers:
        return f'{base}，有轻度阻挡但仍可能有效'
    return f'{base}，未见对应阻挡'
