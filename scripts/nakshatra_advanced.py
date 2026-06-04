#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级星宿分析模块 v2.0
Nakshatra深度分析系统

支持:
  - Tara Bala（星宿力量匹配 — Navatara 9星宿循环）
  - Chandra Bala（月座力量 — 12宫循环）
  - Sub-Lord体系（KP占星）
  - 精确Vimshottari起始点计算
  - Nakshatra兼容性分析
  - Navatara（9星宿组）分类
  - 综合星宿力量报告
"""
from typing import Dict, List, Tuple, Optional
import math
from datetime import datetime, timedelta

NAK_LIST = [
    ("Ashwini","Ketu",7),("Bharani","Venus",20),("Krittika","Sun",6),
    ("Rohini","Moon",10),("Mrigashira","Mars",7),("Ardra","Rahu",18),
    ("Punarvasu","Jupiter",16),("Pushya","Saturn",19),("Ashlesha","Mercury",17),
    ("Magha","Ketu",7),("Purva Phalguni","Venus",20),("Uttara Phalguni","Sun",6),
    ("Hasta","Moon",10),("Chitra","Mars",7),("Swati","Rahu",18),
    ("Vishakha","Jupiter",16),("Anuradha","Saturn",19),("Jyeshtha","Mercury",17),
    ("Mula","Ketu",7),("Purva Ashadha","Venus",20),("Uttara Ashadha","Sun",6),
    ("Shravana","Moon",10),("Dhanishta","Mars",7),("Shatabhisha","Rahu",18),
    ("Purva Bhadrapada","Jupiter",16),("Uttara Bhadrapada","Saturn",19),("Revati","Mercury",17),
]
NAK_NAMES = [n[0] for n in NAK_LIST]
NAK_LORDS = [n[1] for n in NAK_LIST]
NAK_YEARS = [n[2] for n in NAK_LIST]

# Navatara分组（从月亮星宿开始的9个星宿循环）
TARA_NAMES = ['Janma(生命)','Sampat(财富)','Vipat(危险)','Kshema(安全)',
    'Pratyak(障碍)','Sadhana(成就)','Vadha(毁灭)','Mitra(友好)','ParamaMitra(至友)']
TARA_CN = {0:'生命Tara',1:'财富Tara',2:'危险Tara',3:'安全Tara',
    4:'障碍Tara',5:'成就Tara',6:'毁灭Tara',7:'友好Tara',8:'至友Tara'}

# Nakshatra元素和属性
NAK_GANA = {  # 气质类型
    0:'Dev(神圣)',1:'Manushya(人类)',2:'Rakshasa(罗刹)',
    3:'Dev',4:'Dev',5:'Manushya',6:'Dev',7:'Dev',8:'Rakshasa',
    9:'Rakshasa',10:'Manushya',11:'Manushya',12:'Dev',13:'Rakshasa',14:'Dev',
    15:'Rakshasa',16:'Dev',17:'Rakshasa',18:'Rakshasa',19:'Manushya',20:'Manushya',
    21:'Dev',22:'Rakshasa',23:'Rakshasa',24:'Manushya',25:'Manushya',26:'Dev',
}
NAK_ELEMENT = {
    0:'火',1:'土',2:'火',3:'土',4:'土',5:'风',6:'风',7:'水',8:'水',
    9:'火',10:'土',11:'火',12:'土',13:'火',14:'风',15:'火',16:'水',17:'风',
    18:'火',19:'水',20:'土',21:'土',22:'风',23:'风',24:'水',25:'火',26:'水',
}


def find_nakshatra(longitude: float) -> Dict:
    """从恒星黄道经度精确计算Nakshatra"""
    nak_span = 360.0 / 27  # 每个星宿13.333...°
    nak_idx = int(longitude / nak_span) % 27
    nak_start = nak_idx * nak_span
    deg_in_nak = longitude - nak_start
    pada_span = nak_span / 4  # 每个Pada 3.333...°
    pada = int(deg_in_nak / pada_span) + 1
    deg_in_pada = deg_in_nak - (pada - 1) * pada_span

    return {
        'nakshatra': NAK_NAMES[nak_idx],
        'nakshatra_idx': nak_idx,
        'nakshatra_lord': NAK_LORDS[nak_idx],
        'dasha_years': NAK_YEARS[nak_idx],
        'pada': pada,
        'degree_in_nakshatra': round(deg_in_nak, 4),
        'degree_in_pada': round(deg_in_pada, 4),
        'gana': NAK_GANA.get(nak_idx, ''),
        'element': NAK_ELEMENT.get(nak_idx, ''),
    }


def calc_tara_bala(moon_nak_idx: int, target_nak_idx: int) -> Dict:
    """
    Tara Bala计算：月亮星宿到目标星宿的9星宿循环关系

    用于判断某个行星/事件星宿与月亮星宿的关系
    0=Janma(中性), 1=Sampat(吉), 2=Vipat(凶), 3=Kshema(吉),
    4=Pratyak(凶), 5=Sadhana(吉), 6=Vadha(凶), 7=Mitra(吉), 8=ParamaMitra(大吉)
    """
    distance = (target_nak_idx - moon_nak_idx) % 9
    tara_name = TARA_NAMES[distance]
    tara_cn = TARA_CN[distance]

    is_auspicious = distance in (1, 3, 5, 7, 8)
    is_dangerous = distance in (2, 4, 6)

    return {
        'tara_index': distance,
        'tara_name': tara_name,
        'tara_cn': tara_cn,
        'is_auspicious': is_auspicious,
        'is_dangerous': is_dangerous,
        'quality': 'auspicious' if is_auspicious else 'dangerous' if is_dangerous else 'neutral',
        'interpretation': _tara_interp(distance),
    }


def calc_all_tara_balas(moon_nak_idx: int, planet_lons: Dict[str, float]) -> Dict:
    """计算所有行星相对于月亮的Tara Bala"""
    results = {}
    for pname, lon in planet_lons.items():
        p_nak = find_nakshatra(lon)
        tara = calc_tara_bala(moon_nak_idx, p_nak['nakshatra_idx'])
        results[pname] = {
            'nakshatra': p_nak['nakshatra'],
            'tara': tara,
        }
    return results


def calc_vimshottari_start(moon_longitude: float) -> Dict:
    """
    精确计算Vimshottari Dasha的起始点

    返回月亮所在星宿的守护星、已用度数比例、剩余年数
    """
    nak = find_nakshatra(moon_longitude)
    nak_idx = nak['nakshatra_idx']
    nak_lord = NAK_LORDS[nak_idx]
    total_years = NAK_YEARS[nak_idx]

    # 已用比例
    nak_span = 360.0 / 27
    nak_start = nak_idx * nak_span
    deg_in_nak = moon_longitude - nak_start
    used_ratio = deg_in_nak / nak_span
    remaining_ratio = 1 - used_ratio

    # 第一个Mahadasha的剩余年数
    first_mahadasha_remaining = total_years * remaining_ratio
    first_mahadasha_elapsed = total_years * used_ratio

    return {
        'moon_nakshatra': nak['nakshatra'],
        'moon_nakshatra_lord': nak_lord,
        'moon_pada': nak['pada'],
        'total_dasha_years': total_years,
        'used_ratio': round(used_ratio, 6),
        'remaining_ratio': round(remaining_ratio, 6),
        'first_mahadasha_remaining_years': round(first_mahadasha_remaining, 4),
        'first_mahadasha_elapsed_years': round(first_mahadasha_elapsed, 4),
        'first_mahadasha_lord': nak_lord,
    }


def calc_sub_lord(longitude: float, division: int = 9) -> Dict:
    """
    Sub-Lord计算（KP占星体系）
    将星宿进一步细分为Sub-Lord和Sub-Sub-Lord

    参数:
        longitude: 恒星黄道经度
        division: 细分层级（9=Sub-Lord, 81=Sub-Sub-Lord）
    """
    # 主星宿
    nak = find_nakshatra(longitude)
    nak_span = 360.0 / 27

    # Sub-Lord: 当前版本为简化版，直接按9等分。
    # 完整 KP 体系应按 Vimshottari 年数比例不等分，后续需单独对标。
    nak_lord = NAK_LORDS[nak['nakshatra_idx']]
    deg_in_nak = nak['degree_in_nakshatra']

    # 简化版：直接按9等分
    sub_span = nak_span / 9
    sub_idx = int(deg_in_nak / sub_span) % 9

    # Sub-Lord是第sub_idx个行星（从星宿守护星开始的大运顺序）
    DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    nak_lord_idx = DASHA_ORDER.index(NAK_LORDS[nak['nakshatra_idx']])
    sub_lord = DASHA_ORDER[(nak_lord_idx + sub_idx) % 9]

    return {
        'nakshatra': nak['nakshatra'],
        'nakshatra_lord': nak_lord,
        'sub_lord': sub_lord,
        'sub_index': sub_idx,
        'pada': nak['pada'],
        'degree_in_nakshatra': round(deg_in_nak, 4),
    }


def nakshatra_compatibility(nak1_idx: int, nak2_idx: int) -> Dict:
    """
    Nakshatra兼容性分析（Koota系统中的星宿匹配部分）
    基于Tara Bala和Nakshatra元素匹配
    """
    # Tara匹配
    tara = calc_tara_bala(nak1_idx, nak2_idx)
    tara_score = 3 if tara['is_auspicious'] else 0 if tara['is_dangerous'] else 1.5

    # 元素匹配
    el1 = NAK_ELEMENT.get(nak1_idx, '')
    el2 = NAK_ELEMENT.get(nak2_idx, '')
    el_compatible = el1 == el2 or (el1 in ('火','风') and el2 in ('火','风')) or (el1 in ('土','水') and el2 in ('土','水'))

    # Gana匹配
    g1 = NAK_GANA.get(nak1_idx, '')
    g2 = NAK_GANA.get(nak2_idx, '')
    gana_score = 6 if g1 == g2 else 3 if ('Dev' in g1 and 'Manushya' in g2) or ('Manushya' in g1 and 'Dev' in g2) else 0

    return {
        'nak1': NAK_NAMES[nak1_idx],
        'nak2': NAK_NAMES[nak2_idx],
        'tara_bala': tara,
        'tara_score': tara_score,
        'element_match': {'e1': el1, 'e2': el2, 'compatible': el_compatible},
        'gana_match': {'g1': g1, 'g2': g2, 'score': gana_score},
        'overall': 'compatible' if tara_score >= 1.5 and el_compatible else 'challenging' if tara['is_dangerous'] else 'moderate',
    }


def _tara_interp(idx):
    interps = {
        0: '生命Tara—中性，代表自我，不吉不凶',
        1: '财富Tara—吉，带来物质和精神增长',
        2: '危险Tara—凶，需要谨慎，可能带来损失',
        3: '安全Tara—吉，提供保护和稳定',
        4: '障碍Tara—凶，可能面临困难和延误',
        5: '成就Tara—吉，有利于实现目标',
        6: '毁灭Tara—凶，最大凶Tara，需特别注意',
        7: '友好Tara—吉，提供支持和帮助',
        8: '至友Tara—大吉，最强吉Tara',
    }
    return interps.get(idx, '')


# ============================================================================
# Chandra Bala（月座力量）— v2.0 新增
# ============================================================================

# 12宫 Chandra Bala 名称（从月亮星座起算）
CHANDRA_NAMES = [
    'Janma(生命)', 'Sampat(财富)', 'Vipat(危险)', 'Kshema(安全)',
    'Pratyak(障碍)', 'Sadhana(成就)', 'Vadha(毁灭)', 'Mitra(友好)',
    'ParamaMitra(至友)', 'Karma(业力)', 'Labha(收益)', 'Vyaya(消耗)',
]
CHANDRA_CN = {
    0: '生命位', 1: '财富位', 2: '危险位', 3: '安全位',
    4: '障碍位', 5: '成就位', 6: '毁灭位', 7: '友好位',
    8: '至友位', 9: '业力位', 10: '收益位', 11: '消耗位',
}


def calc_chandra_bala(natal_moon_sign_idx: int, transit_moon_sign_idx: int) -> Dict:
    """
    Chandra Bala（月座力量）计算 — v2.0 新增

    基于月亮所在宫位（Rashi/Sign）的相对位置评估力量。
    从本命月亮星座起算到当前（过境）月亮星座的12宫循环。

    与 Tara Bala（星宿/Nakshatra 层面）互补，提供 Rashi/Sign 层面的力量评估。
    常用于 Muhurta 择时和 Transit 过境分析。

    参数:
        natal_moon_sign_idx: 本命月亮星座索引 (0=Aries ~ 11=Pisces)
        transit_moon_sign_idx: 过境月亮星座索引 (0=Aries ~ 11=Pisces)

    返回:
        dict: {
            'rashi_from_moon': 0-11,
            'chandra_name': 'Janma/Sampat/...',
            'chandra_cn': '生命位/财富位/...',
            'is_auspicious': bool,
            'is_dangerous': bool,
            'quality': 'auspicious'/'dangerous'/'neutral',
            'interpretation': str,
        }
    """
    # 从本命月亮星座到过境月亮星座的步数（0-based, 12宫循环）
    distance = (transit_moon_sign_idx - natal_moon_sign_idx) % 12

    name = CHANDRA_NAMES[distance]
    cn = CHANDRA_CN[distance]

    # 吉位：Sampat(1), Kshema(3), Sadhana(5), Mitra(7), ParamaMitra(8), Labha(10)
    # 凶位：Vipat(2), Pratyak(4), Vadha(6), Karma(9)
    # 中性：Janma(0), Vyaya(11)
    is_auspicious = distance in (1, 3, 5, 7, 8, 10)
    is_dangerous = distance in (2, 4, 6, 9)

    if is_auspicious:
        quality = 'auspicious'
    elif is_dangerous:
        quality = 'dangerous'
    else:
        quality = 'neutral'

    return {
        'rashi_from_moon': distance,
        'chandra_name': name,
        'chandra_cn': cn,
        'is_auspicious': is_auspicious,
        'is_dangerous': is_dangerous,
        'quality': quality,
        'interpretation': _chandra_interp(distance),
    }


def _chandra_interp(idx: int) -> str:
    """Chandra Bala 解释"""
    interps = {
        0: '生命位—代表身体和自我状态，中性',
        1: '财富位—吉，有利于财务和资源获取',
        2: '危险位—凶，可能遭遇损失和挑战',
        3: '安全位—吉，提供保护和稳定感',
        4: '障碍位—凶，面临困难和拖延',
        5: '成就位—吉，有利于达成目标和获得成功',
        6: '毁灭位—凶，需警惕冲突和破坏',
        7: '友好位—吉，获得他人的支持和帮助',
        8: '至友位—大吉，最强吉位，全面有利',
        9: '业力位—凶，涉及过往业力的清算',
        10: '收益位—吉，有利于收入和事业增长',
        11: '消耗位—中性偏凶，可能消耗能量和资源',
    }
    return interps.get(idx, '')


def calc_tara_chandra_combined(
    natal_moon_nak_idx: int,
    natal_moon_sign_idx: int,
    planet_lons: Dict[str, float],
    transit_moon_lon: Optional[float] = None,
    transit_moon_sign_idx: Optional[int] = None,
) -> Dict:
    """
    Tara Bala + Chandra Bala 双维度综合行星力量分析 — v2.0 新增

    同时评估：
    1. Tara Bala（Star层面）：月亮星宿到行星星宿的9星宿循环
    2. Chandra Bala（Sign层面）：月亮星座到行星星座的12宫循环

    双吉 = 最强力，双凶 = 最弱力，一吉一凶 = 混合力量

    参数:
        natal_moon_nak_idx: 本命月亮星宿索引 (0-26)
        natal_moon_sign_idx: 本命月亮星座索引 (0-11)
        planet_lons: {行星名: 恒星黄道经度}
        transit_moon_lon: 过境月亮经度（可选，用于过境分析）
        transit_moon_sign_idx: 过境月亮星座索引（可选，用于过境分析）

    返回:
        dict: {planet: {tara, chandra, combined_score, interpretation}}
    """
    results = {}

    for pname, lon in planet_lons.items():
        # Tara Bala（Nakshatra层面）
        p_nak = find_nakshatra(lon)
        tara = calc_tara_bala(natal_moon_nak_idx, p_nak['nakshatra_idx'])

        # Chandra Bala（Rashi层面）
        p_sign_idx = int(lon / 30) % 12
        chandra = calc_chandra_bala(natal_moon_sign_idx, p_sign_idx)

        # 综合评分
        combined_score = _combined_score(tara, chandra)

        results[pname] = {
            'nakshatra': p_nak['nakshatra'],
            'sign_idx': p_sign_idx,
            'tara': tara,
            'chandra': chandra,
            'combined_score': combined_score,
            'assessment': _combined_assessment(combined_score),
        }

    return results


def _combined_score(tara: Dict, chandra: Dict) -> str:
    """综合 Tara + Chandra 评分"""
    t_good = tara['is_auspicious']
    c_good = chandra['is_auspicious']
    t_bad = tara['is_dangerous']
    c_bad = chandra['is_dangerous']

    if t_good and c_good:
        return 'double_auspicious'
    elif t_bad and c_bad:
        return 'double_dangerous'
    elif t_good and c_bad:
        return 'tara_good_chandra_bad'
    elif t_bad and c_good:
        return 'tara_bad_chandra_good'
    else:
        # 至少有一方中性
        if t_good or c_good:
            return 'mixed_favorable'
        elif t_bad or c_bad:
            return 'mixed_unfavorable'
        else:
            return 'neutral'


def _combined_assessment(score: str) -> str:
    """综合评估说明"""
    assessments = {
        'double_auspicious': '双吉—Star与Sign层面均有利，最强力支持',
        'double_dangerous': '双凶—Star与Sign层面均不利，需格外谨慎',
        'tara_good_chandra_bad': '星吉宫凶—Nakshatra有利但Rashi层面受阻，可能好事多磨',
        'tara_bad_chandra_good': '星凶宫吉—Nakshatra不利但Rashi层面有保护，或许有惊无险',
        'mixed_favorable': '偏吉—至少一方有利，方向积极',
        'mixed_unfavorable': '偏凶—至少一方不利，需注意',
        'neutral': '中性—无明确吉凶指向',
    }
    return assessments.get(score, '')


def calc_nakshatra_transits_natal(
    planet_lons: Dict[str, float],
) -> Dict:
    """
    计算所有行星在星盘中的 Nakshatra 分布 — v2.0 新增

    用于快速查看每个行星落在哪个星宿、Pada、守护星等信息。

    返回:
        dict: {planet: {nakshatra, pada, lord, gana, element, degree_in_nak}}
    """
    results = {}
    for pname, lon in planet_lons.items():
        nak = find_nakshatra(lon)
        results[pname] = {
            'nakshatra': nak['nakshatra'],
            'nakshatra_idx': nak['nakshatra_idx'],
            'nakshatra_lord': nak['nakshatra_lord'],
            'pada': nak['pada'],
            'gana': nak['gana'],
            'element': nak['element'],
            'degree_in_nakshatra': nak['degree_in_nakshatra'],
            'dasha_years': nak['dasha_years'],
        }
    return results


def nakshatra_full_report(
    chart_data: Dict,
    age: Optional[float] = None,
    transit_date: Optional[str] = None,
) -> Dict:
    """
    综合星宿力量完整报告 — v2.0 新增

    包含:
    1. 本命 Nakshatra 分布（所有行星）
    2. Tara Bala 全部分析（以月亮星宿为基准）
    3. Chandra Bala 全部分析（以月亮星座为基准）
    4. Tara+Chandra 双维度综合评分
    5. Nakshatra 兼容性（行星间的星宿关系）
    6. Vimshottari 起始点信息
    7. Sub-Lord KP 分析

    参数:
        chart_data: 星盘数据 (from jyotish_engine chart command)
        age: 当前年龄（可选）
        transit_date: 过境日期 YYYY-MM-DD（可选）

    返回:
        dict: 完整星宿报告
    """
    planets = chart_data.get('planets', {})
    planet_lons = {}
    planet_signs = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']
            planet_signs[pn] = int(pd['degree'] / 30) % 12

    if not planet_lons:
        return {'error': '无法获取行星经度数据'}

    moon_lon = planet_lons.get('Moon', 0)
    moon_nak_idx = int(moon_lon / (360/27)) % 27
    moon_sign_idx = int(moon_lon / 30) % 12

    report = {}

    # 1. 本命星宿分布
    report['natal_nakshatras'] = calc_nakshatra_transits_natal(planet_lons)

    # 2. Tara Bala
    report['tara_bala'] = calc_all_tara_balas(moon_nak_idx, planet_lons)

    # 3. Chandra Bala
    chandra_bala = {}
    for pn, lon in planet_lons.items():
        p_sign = int(lon / 30) % 12
        chandra_bala[pn] = {
            'planet_sign': p_sign,
            'chandra': calc_chandra_bala(moon_sign_idx, p_sign),
        }
    report['chandra_bala'] = chandra_bala

    # 4. Tara + Chandra 双维综合
    report['tara_chandra_combined'] = calc_tara_chandra_combined(
        moon_nak_idx, moon_sign_idx, planet_lons)

    # 5. Sub-Lords
    report['sub_lords'] = {pn: calc_sub_lord(lon) for pn, lon in planet_lons.items()}

    # 6. Vimshottari 起始点
    report['vimshottari_start'] = calc_vimshottari_start(moon_lon)

    # 7. 星宿力量排序
    power_ranking = []
    for pn, combined in report['tara_chandra_combined'].items():
        score_val = _score_value(combined['combined_score'])
        power_ranking.append({
            'planet': pn,
            'nakshatra': combined['nakshatra'],
            'tara_name': combined['tara']['tara_cn'],
            'tara_quality': combined['tara']['quality'],
            'chandra_name': combined['chandra']['chandra_cn'],
            'chandra_quality': combined['chandra']['quality'],
            'combined': combined['combined_score'],
            'score': score_val,
            'assessment': combined['assessment'],
        })
    power_ranking.sort(key=lambda x: x['score'], reverse=True)
    report['power_ranking'] = power_ranking

    # 8. 汇总
    double_auspicious = [p['planet'] for p in power_ranking if p['combined'] == 'double_auspicious']
    double_dangerous = [p['planet'] for p in power_ranking if p['combined'] == 'double_dangerous']
    report['summary'] = {
        'moon_nakshatra': NAK_NAMES[moon_nak_idx],
        'moon_nakshatra_lord': NAK_LORDS[moon_nak_idx],
        'moon_sign_idx': moon_sign_idx,
        'strongest_planets': [p['planet'] for p in power_ranking[:3]],
        'weakest_planets': [p['planet'] for p in power_ranking[-3:]],
        'double_auspicious_planets': double_auspicious,
        'double_dangerous_planets': double_dangerous,
        'tara_auspicious_count': sum(1 for p in power_ranking if p['tara_quality'] == 'auspicious'),
        'chandra_auspicious_count': sum(1 for p in power_ranking if p['chandra_quality'] == 'auspicious'),
    }

    return report


def _score_value(combined: str) -> int:
    """将组合评分转为数值"""
    scores = {
        'double_auspicious': 100,
        'tara_good_chandra_bad': 60,
        'tara_bad_chandra_good': 60,
        'mixed_favorable': 55,
        'neutral': 50,
        'mixed_unfavorable': 45,
        'double_dangerous': 0,
    }
    return scores.get(combined, 50)
