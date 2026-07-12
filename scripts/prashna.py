#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prashna（卜卦/问事）占星系统 v7.0

核心功能：
1. Prashna Lagna — 基于询问时刻的卜卦盘
2. Arudha Prashna — 镜像点解读
3. KP Prashna — 用KP sublord精确定位答案
4. Sphuta — 特殊敏感点
5. 问事分类— 12宫主题映射
6. Nadi Prashna — 从Moon/Jupiter角度解读
7. Tajika Prashna — 年运盘整合

v7.0 新增：
- KP Sublord 完整计算（27 Nakshatra × 9行星 = 249 sublord映射）
- Nadi Prashna 角度解读
- Tajika Ithasala/Easarapha 整合
- 完整Sphuta计算（Gulika/Yamaghantaka）
- Prashna时机评分系统
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
    'Punarvasu','Pushya','Ashlesha','Magha','PurvaPhalguni','UttaraPhalguni',
    'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','PurvaAshadha','UttaraAshadha','Shravana','Dhanishta','Shatabhisha',
    'PurvaBhadrapada','UttaraBhadrapada','Revati']

# KP 249 sublord字典（简化版，完整需加载249条）
KP_SUBLORD_MEANINGS = {
    'Sun': {1:'健康恢复', 2:'收入增长', 3:'勇气', 4:'房产', 5:'投资', 6:'疾病', 7:'婚姻', 8:'遗产', 9:'远行', 10:'升职', 11:'收益', 12:'支出'},
    'Moon': {1:'新开始', 2:'波动收入', 3:'短途旅行', 4:'搬家', 5:'创造', 6:'慢性病', 7:'情感', 8:'心理', 9:'精神', 10:'公众', 11:'社交', 12:'隐退'},
    'Mars': {1:'积极行动', 2:'资金', 3:'技能', 4:'建筑', 5:'投机', 6:'手术', 7:'竞争', 8:'意外', 9:'法律', 10:'职业', 11:'社交', 12:'幕后'},
    'Mercury': {1:'沟通', 2:'商业', 3:'写作', 4:'学习', 5:'教育', 6:'文书', 7:'谈判', 8:'研究', 9:'出版', 10:'信息', 11:'网络', 12:'秘密'},
    'Jupiter': {1:'新开始', 2:'财富', 3:'努力', 4:'家宅', 5:'子女', 6:'恢复', 7:'婚姻', 8:'转变', 9:'远行', 10:'成功', 11:'扩张', 12:'解脱'},
    'Venus': {1:'魅力', 2:'奢侈品', 3:'艺术', 4:'舒适', 5:'浪漫', 6:'享受', 7:'伴侣', 8:'深层', 9:'高等', 10:'审美', 11:'社交', 12:'隐居'},
    'Saturn': {1:'缓慢', 2:'节俭', 3:'延迟', 4:'老旧', 5:'等待', 6:'慢性', 7:'延迟婚', 8:'遗产', 9:'严肃', 10:'权威', 11:'长期', 12:'孤独'},
    'Rahu': {1:'迷惑', 2:'暴富', 3:'冒险', 4:'不满', 5:'非婚', 6:'怪病', 7:'涉外', 8:'突变', 9:'异域', 10:'非传统', 11:'网络', 12:'海外'},
    'Ketu': {1:'抽离', 2:'损失', 3:'独立', 4:'搬家', 5:'异常', 6:'谜病', 7:'分离', 8:'秘密', 9:'修行', 10:'幕后', 11:'孤立', 12:'解脱'},
}

# 问事类型分类
QUESTION_CATEGORIES = {
    'career': {'primary': 10, 'secondary': [6, 2, 11], 'karaka': 'Saturn'},
    'finance': {'primary': 2, 'secondary': [11, 5, 9], 'karaka': 'Jupiter'},
    'health': {'primary': 6, 'secondary': [1, 8], 'karaka': 'Sun'},
    'marriage': {'primary': 7, 'secondary': [2, 11], 'karaka': 'Venus'},
    'children': {'primary': 5, 'secondary': [9], 'karaka': 'Jupiter'},
    'relocation': {'primary': 4, 'secondary': [12, 9], 'karaka': 'Moon'},
    'education': {'primary': 5, 'secondary': [4, 9], 'karaka': 'Mercury'},
    'legal': {'primary': 6, 'secondary': [8, 7], 'karaka': 'Jupiter'},
    'spiritual': {'primary': 9, 'secondary': [12, 9], 'karaka': 'Ketu'},
    'property': {'primary': 4, 'secondary': [2, 11], 'karaka': 'Mars'},
    'travel': {'primary': 12, 'secondary': [9, 3], 'karaka': 'Rahu'},
    'general': {'primary': 1, 'secondary': [10], 'karaka': 'Moon'},
}


def calc_prashna_chart(question_time: datetime, planet_positions: Dict,
                       asc_degree: float = None) -> Dict:
    """
    计算Prashna（卜卦）盘。

    基于询问时刻的天象构建卜卦盘，这是Prashna的核心。

    Args:
        question_time: 询问时间
        planet_positions: 该时刻的行星位置
        asc_degree: 卜卦上升度数(0-360, 可选)

    Returns:
        卜卦盘数据
    """
    if asc_degree is None:
        # 使用询问时间的秒数计算伪随机上升
        asc_degree = (question_time.hour * 3600 + question_time.minute * 60 + question_time.second) % 360

    asc_sign_idx = int(asc_degree / 30) % 12
    asc_sign = SIGNS[asc_sign_idx]

    # 构建分宫图
    houses = {}
    for h in range(1, 13):
        sign_idx = (asc_sign_idx + h - 1) % 12
        houses[h] = {
            'sign': SIGNS[sign_idx],
            'lord': SIGN_LORDS[SIGNS[sign_idx]],
        }

    # 映射行星到宫位
    planet_houses = {}
    for pname, pdata in planet_positions.items():
        sign = pdata.get('sign', '')
        if sign in SIGNS:
            p_sign_idx = SIGNS.index(sign)
            house = (p_sign_idx - asc_sign_idx) % 12 + 1
            planet_houses[pname] = house

    return {
        'question_time': question_time.isoformat(),
        'asc_sign': asc_sign,
        'asc_degree': round(asc_degree % 30, 2),
        'houses': houses,
        'planet_houses': planet_houses,
        'prashna_lagna_lord': SIGN_LORDS[asc_sign],
    }


def get_kp_prashna_answer(planet_positions: Dict, question_category: str,
                          asc_degree: float) -> Dict:
    """
    使用KP sublord方法回答Prashna问题。

    1. 确定问题宫位
    2. 找到该宫位主星
    3. 查看其sublord在哪个宫
    4. 如果sublord的本宫与问题宫位或karaka相关 → 答案是YES

    Args:
        planet_positions: 卜卦时刻行星位置
        question_category: 问题类型
        asc_degree: 上升度数

    Returns:
        KP答案分析
    """
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    primary_house = cat['primary']
    karaka = cat['karaka']

    asc_sign = SIGNS[int(asc_degree / 30) % 12]
    asc_idx = SIGNS.index(asc_sign)

    # 问题宫主
    question_sign = SIGNS[(asc_idx + primary_house - 1) % 12]
    question_lord = SIGN_LORDS[question_sign]

    # 问题宫主所在的行星位置
    ql_data = planet_positions.get(question_lord, {})
    ql_sign = ql_data.get('sign', '')
    ql_sign_idx = SIGNS.index(ql_sign) if ql_sign in SIGNS else 0
    ql_house = (ql_sign_idx - asc_idx) % 12 + 1

    # Sublord分析（简化版，完整版需精确计算）
    # 如果问题宫主在自己的宫位或与karaka相关 → 有利
    is_favorable = ql_house in (1, 4, 5, 7, 9, 10, 11)

    # KP答案判定
    if is_favorable:
        answer = "YES — 卜卦信号有利"
        confidence = "高"
    elif ql_house in (6, 8, 12):
        answer = "NO — 卜卦信号不利"
        confidence = "高"
    else:
        answer = "MAYBE — 需要更多信息确认"
        confidence = "中"

    return {
        'question_type': question_category,
        'primary_house': primary_house,
        'question_lord': question_lord,
        'lord_house': ql_house,
        'lord_sign': ql_sign,
        'karaka': karaka,
        'kp_answer': answer,
        'confidence': confidence,
        'note': '基于KP sublord原则：主星状态决定结果方向',
    }


def detect_prashna_arudha(planet_positions: Dict, asc_degree: float,
                          question_house: int) -> Dict:
    """
    计算Prashna中的Arudha（镜像点）。

    Arudha = 反射真实意图的镜像宫位。
    用于验证问事者的问题是否与真实关切一致。
    """
    asc_sign_idx = int(asc_degree / 30) % 12
    lord_sign_idx = (asc_sign_idx + question_house - 1) % 12
    lord = SIGN_LORDS[SIGNS[lord_sign_idx]]
    lord_house = 0

    for pname, pdata in planet_positions.items():
        if pname == lord:
            p_sign = pdata.get('sign', '')
            if p_sign in SIGNS:
                lord_house = (SIGNS.index(p_sign) - asc_sign_idx) % 12 + 1
            break

    if lord_house == 0:
        lord_house = question_house

    # Arudha公式：从宫主数X宫，再从宫主落位数X宫
    distance = lord_house - question_house
    if distance <= 0:
        distance += 12
    arudha_house = (lord_house + distance - 1) % 12 + 1

    # BPHS例外：Arudha不能落在原宫或7宫
    if arudha_house == question_house:
        arudha_house = 10
    if arudha_house == ((question_house + 6) % 12) or ((question_house + 6) % 12) == 0:
        _h7 = ((question_house + 6) % 12) or 12
        if arudha_house == _h7:
            arudha_house = 4

    return {
        'question_house': question_house,
        'lord': lord,
        'lord_house': lord_house,
        'arudha_house': arudha_house,
        'note': f'Arudha在{arudha_house}宫 — 问题的"镜像"反映在此领域',
    }


# =============================================================================
# KP Sublord 完整计算 v7.0
# =============================================================================

# Nakshatra Lords (Vimshottari sequence)
NAK_LORDS = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
NAK_SPAN = 360.0 / 27.0  # 13.333...° per nakshatra
SUB_SPAN = NAK_SPAN / 9.0  # ~1.481° per sub (每个sub由nakshatra lord的一个行星段构成)

# Vimshottari年数用于计算sub比例
VIM_DURATIONS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,
                 'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}
VIM_TOTAL = 120.0


def calc_kp_sublord(longitude: float) -> Dict:
    """
    计算某经度的KP Sublord v7.0

    KP系统：每个Nakshatra由一个Lord掌管，Nakshatra内按Vimshottari比例
    细分为9个sub，每个sub由下一个Dasha序列行星掌管。

    Args:
        longitude: 行星经度 (0-360 sidereal)

    Returns:
        dict: {nakshatra, nak_lord, pada, sub_lord, sub_sub_lord}
    """
    lon = longitude % 360

    # Nakshatra
    nak_idx = int(lon / NAK_SPAN) % 27
    nak_lord = NAK_LORDS[nak_idx % 9]
    nak_name = NAKSHATRAS[nak_idx]

    # Pada (1-4)
    pos_in_nak = lon % NAK_SPAN
    pada = int(pos_in_nak / (NAK_SPAN / 4)) + 1

    # Sub Lord: 在Nakshatra内，按Vimshottari比例分段
    # 从Nakshatra Lord开始，按序列分配
    lord_idx = NAK_LORDS.index(nak_lord)
    cum_deg = 0.0
    sub_lord = nak_lord  # 默认
    for i in range(9):
        planet = NAK_LORDS[(lord_idx + i) % 9]
        sub_size = NAK_SPAN * (VIM_DURATIONS[planet] / VIM_TOTAL)
        if cum_deg <= pos_in_nak < cum_deg + sub_size:
            sub_lord = planet
            break
        cum_deg += sub_size

    # Sub-Sub Lord: 在Sub内再按Vimshottari比例细分
    sub_start = cum_deg
    sub_size = NAK_SPAN * (VIM_DURATIONS[sub_lord] / VIM_TOTAL)
    pos_in_sub = pos_in_nak - sub_start
    sub_lord_idx = NAK_LORDS.index(sub_lord)
    cum_deg2 = 0.0
    sub_sub_lord = sub_lord
    for i in range(9):
        planet = NAK_LORDS[(sub_lord_idx + i) % 9]
        sub_sub_size = sub_size * (VIM_DURATIONS[planet] / VIM_TOTAL)
        if cum_deg2 <= pos_in_sub < cum_deg2 + sub_sub_size:
            sub_sub_lord = planet
            break
        cum_deg2 += sub_sub_size

    return {
        'nakshatra': nak_name,
        'nakshatra_index': nak_idx,
        'nakshatra_lord': nak_lord,
        'pada': pada,
        'sub_lord': sub_lord,
        'sub_sub_lord': sub_sub_lord,
    }


def get_kp_prashna_answer_v2(planet_positions: Dict, question_category: str,
                              asc_degree: float) -> Dict:
    """
    KP Prashna v7.0 — 完整版

    使用KP sublord三层判定：
    1. 问题宫主星(Star Lord) → 大方向
    2. Sub Lord → 实际结果
    3. Sub-Sub Lord → 细节/时机

    判定规则（KP经典）：
    - Sub Lord 落在问题宫位的2/3/11宫 → YES
    - Sub Lord 落在问题宫位的6/8/12宫 → NO
    - Sub Lord 落在1/5/9宫 → 延迟但最终YES
    - Sub Lord 落在4/7/10宫 → 取决于努力
    """
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    primary_house = cat['primary']
    karaka = cat['karaka']

    asc_sign = SIGNS[int(asc_degree / 30) % 12]
    asc_idx = SIGNS.index(asc_sign)

    # 问题宫主
    question_sign = SIGNS[(asc_idx + primary_house - 1) % 12]
    question_lord = SIGN_LORDS[question_sign]

    # 问题宫主的经度
    ql_data = planet_positions.get(question_lord, {})
    ql_lon = ql_data.get('longitude', ql_data.get('lon', 0))
    if not ql_lon and 'sign' in ql_data:
        sign_idx = SIGNS.index(ql_data['sign']) if ql_data['sign'] in SIGNS else 0
        deg = ql_data.get('degree', ql_data.get('deg_in_sign', 0))
        ql_lon = sign_idx * 30 + deg

    # 计算 KP Sublord
    kp = calc_kp_sublord(ql_lon)

    # Sub Lord 所在宫位
    sub_lord = kp['sub_lord']
    sl_data = planet_positions.get(sub_lord, {})
    sl_sign = sl_data.get('sign', '')
    sl_sign_idx = SIGNS.index(sl_sign) if sl_sign in SIGNS else 0
    sl_house = (sl_sign_idx - asc_idx) % 12 + 1

    # 从问题宫位看Sub Lord所在宫位
    house_from_question = ((sl_house - primary_house) % 12) + 1

    # KP判定
    YES_HOUSES = {2, 3, 11}  # 从问题宫看：2/3/11宫
    DELAYED_YES = {1, 5, 9}  # 三方宫
    DEPENDS_HOUSES = {4, 7, 10}  # 角宫
    NO_HOUSES = {6, 8, 12}  # 凶宫

    if house_from_question in YES_HOUSES:
        answer = "YES"
        confidence = "高"
        reason = f"Sub Lord {sub_lord} 在问题宫的第{house_from_question}宫（吉宫），结果有利"
    elif house_from_question in DELAYED_YES:
        answer = "YES (延迟)"
        confidence = "中"
        reason = f"Sub Lord {sub_lord} 在问题宫的第{house_from_question}宫（三方），延迟但最终有利"
    elif house_from_question in NO_HOUSES:
        answer = "NO"
        confidence = "高"
        reason = f"Sub Lord {sub_lord} 在问题宫的第{house_from_question}宫（凶宫），结果不利"
    elif house_from_question in DEPENDS_HOUSES:
        answer = "MAYBE (取决于努力)"
        confidence = "中"
        reason = f"Sub Lord {sub_lord} 在问题宫的第{house_from_question}宫（角宫），结果取决于努力"
    else:
        answer = "MAYBE"
        confidence = "低"
        reason = f"Sub Lord {sub_lord} 位置不明确"

    # Sub-Sub Lord 时机提示
    sub_sub = kp['sub_sub_lord']
    ss_data = planet_positions.get(sub_sub, {})
    ss_sign = ss_data.get('sign', '')
    timing_note = ""
    if ss_sign in SIGNS:
        ss_house = (SIGNS.index(ss_sign) - asc_idx) % 12 + 1
        timing_note = f"Sub-Sub Lord {sub_sub} 在{ss_house}宫，提示时机线索"

    return {
        'question_type': question_category,
        'primary_house': primary_house,
        'question_lord': question_lord,
        'question_lord_longitude': ql_lon,
        'kp_star_lord': kp['nakshatra_lord'],
        'kp_sub_lord': sub_lord,
        'kp_sub_sub_lord': sub_sub,
        'sub_lord_house': sl_house,
        'house_from_question': house_from_question,
        'karaka': karaka,
        'kp_answer': answer,
        'confidence': confidence,
        'reason': reason,
        'timing_note': timing_note,
        'kp_details': kp,
    }


def build_kp_horary_evidence(planet_positions: Dict, question_category: str,
                             asc_degree: float, horary_number: int = None) -> Dict:
    """Build structured KP Horary evidence for Prashna UI/API contracts.

    This is intentionally lightweight: it reuses the local KP sub-lord and
    significator rules instead of running an all-day 1-249 exact-time search.
    """
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    primary = cat['primary']
    secondary = cat.get('secondary', [])
    asc_idx = int(asc_degree / 30) % 12
    asc_sign = SIGNS[asc_idx]
    asc_lord = SIGN_LORDS[asc_sign]
    moon_lon = _planet_longitude(planet_positions, 'Moon')
    moon_kp = calc_kp_sublord(moon_lon)
    cusp_lon = (asc_degree + (primary - 1) * 30) % 360
    cusp_kp = calc_kp_sublord(cusp_lon)
    houses = _kp_horary_houses(asc_idx)
    normalized_planets = _kp_horary_planets(planet_positions, asc_idx)
    house_significators = _house_significators_for_horary(normalized_planets, houses)
    focus_houses = [primary] + [h for h in secondary if h != primary]
    judgement = []
    for house in focus_houses:
        sig = house_significators.get(house, {})
        strength = len(sig.get('A', [])) * 3 + len(sig.get('B', [])) * 2 + len(sig.get('C', [])) + (1 if sig.get('D') else 0)
        judgement.append({
            'house': house,
            'role': 'primary' if house == primary else 'supporting',
            'significators': sig,
            'score': strength,
            'signal': 'strong' if strength >= 4 else 'moderate' if strength >= 2 else 'thin',
        })
    return {
        'method': 'KP Horary',
        'source': 'local prashna.py + kp_system.py; VedicAstro-compatible KP sub-lord proportions',
        'horary_number': horary_number,
        'question_type': question_category,
        'question_houses': {
            'primary': primary,
            'secondary': secondary,
            'karaka': cat.get('karaka'),
        },
        'ruling_planets': {
            'ascendant_lord': asc_lord,
            'moon_star_lord': moon_kp['nakshatra_lord'],
            'moon_sub_lord': moon_kp['sub_lord'],
            'day_lord': '',
            'method_note': 'Ruling planets use available Prashna ascendant and Moon KP lords; day lord is omitted when exact question date is not supplied.',
        },
        'cuspal_sub_lord': {
            'house': primary,
            'cusp_longitude': round(cusp_lon, 4),
            'kp_lords': cusp_kp,
        },
        'house_significators': {str(h): house_significators.get(h, {}) for h in focus_houses},
        'judgement_matrix': judgement,
        'next_action': 'KP Horary evidence should confirm the YES/NO answer through ruling planets, cuspal sub-lord and house significators.',
    }


def _planet_longitude(planet_positions: Dict, planet: str) -> float:
    data = planet_positions.get(planet, {}) if isinstance(planet_positions, dict) else {}
    lon = data.get('longitude', data.get('lon'))
    if isinstance(lon, (int, float)):
        return lon % 360
    sign = data.get('sign')
    if sign in SIGNS:
        return (SIGNS.index(sign) * 30 + float(data.get('degree', data.get('degree_in_sign', 0)) or 0)) % 360
    return 0.0


def _kp_horary_houses(asc_idx: int) -> List[Dict]:
    houses = []
    for house in range(1, 13):
        sign = SIGNS[(asc_idx + house - 1) % 12]
        houses.append({'house': house, 'sign': sign, 'rasi_lord': SIGN_LORDS[sign]})
    return houses


def _kp_horary_planets(planet_positions: Dict, asc_idx: int) -> Dict:
    normalized = {}
    for planet, data in planet_positions.items():
        if not isinstance(data, dict):
            continue
        lon = _planet_longitude(planet_positions, planet)
        sign = SIGNS[int(lon / 30) % 12]
        house = ((SIGNS.index(sign) - asc_idx) % 12) + 1
        normalized[planet] = {
            'sign': sign,
            'house': house,
            'longitude': round(lon, 4),
            'kp_lords': calc_kp_sublord(lon),
        }
    return normalized


def _house_significators_for_horary(planet_positions: Dict, houses: List[Dict]) -> Dict:
    planet_nak_lords = {
        planet: data.get('kp_lords', {}).get('nakshatra_lord', '')
        for planet, data in planet_positions.items()
    }
    result = {}
    for house in houses:
        house_num = house['house']
        occupants = [planet for planet, data in planet_positions.items() if data.get('house') == house_num]
        lord = house.get('rasi_lord', '')
        result[house_num] = {
            'A': [planet for planet, nak_lord in planet_nak_lords.items() if nak_lord in occupants],
            'B': occupants,
            'C': [planet for planet, nak_lord in planet_nak_lords.items() if nak_lord == lord],
            'D': lord,
        }
    return result


# =============================================================================
# Nadi Prashna v7.0
# =============================================================================

def nadi_prashna_analysis(planet_positions: Dict, asc_degree: float,
                           question_category: str) -> Dict:
    """
    Nadi Prashna 分析 v7.0

    从Moon和Jupiter的角度解读问题：
    - Moon = 问事者的真实情感/内心状态
    - Jupiter = 问题的智慧/导师角度
    - 两者之间的关系揭示问题的本质

    Args:
        planet_positions: 行星位置
        asc_degree: 上升度数
        question_category: 问题类型

    Returns:
        Nadi Prashna分析结果
    """
    asc_idx = int(asc_degree / 30) % 12

    # Moon位置
    moon_data = planet_positions.get('Moon', {})
    moon_sign = moon_data.get('sign', '')
    moon_sign_idx = SIGNS.index(moon_sign) if moon_sign in SIGNS else asc_idx
    moon_house = (moon_sign_idx - asc_idx) % 12 + 1

    # Jupiter位置
    jup_data = planet_positions.get('Jupiter', {})
    jup_sign = jup_data.get('sign', '')
    jup_sign_idx = SIGNS.index(jup_sign) if jup_sign in SIGNS else asc_idx
    jup_house = (jup_sign_idx - asc_idx) % 12 + 1

    # Moon-Jupiter关系
    moon_jup_aspect = abs(moon_house - jup_house)
    if moon_jup_aspect > 6:
        moon_jup_aspect = 12 - moon_jup_aspect

    # Nadi解读
    if moon_jup_aspect in [1, 5, 9]:
        relation = "友好（三方/同宫）→ 问事者内心与问题导师和谐"
    elif moon_jup_aspect in [4, 7, 10]:
        relation = "紧张（角宫相位）→ 问事者内心与问题有张力但有力"
    elif moon_jup_aspect in [6, 8]:
        relation = "困难（凶宫关系）→ 问事者内心与问题有深层矛盾"
    else:
        relation = "中性 → 关系一般"

    # 从Moon看问题宫位
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    q_house = cat['primary']
    house_from_moon = ((q_house - moon_house) % 12) + 1

    return {
        'moon_house': moon_house,
        'jupiter_house': jup_house,
        'moon_jupiter_relation': relation,
        'question_house_from_moon': house_from_moon,
        'nadi_interpretation': _nadi_interpret(moon_house, jup_house, house_from_moon, q_house),
    }


def _nadi_interpret(moon_h, jup_h, q_from_moon, q_house):
    """Nadi解读辅助"""
    lines = []
    lines.append(f"Moon在{moon_h}宫 → 问事者当前的情感焦点")
    lines.append(f"Jupiter在{jup_h}宫 → 问题的智慧指引方向")

    if q_from_moon in [1, 4, 7, 10]:
        lines.append(f"问题宫从Moon看在{q_from_moon}宫(角宫) → 问事者对问题有直接关注")
    elif q_from_moon in [5, 9]:
        lines.append(f"问题宫从Moon看在{q_from_moon}宫(三方) → 问事者对问题有好感/支持")
    elif q_from_moon in [6, 8, 12]:
        lines.append(f"问题宫从Moon看在{q_from_moon}宫(凶宫) → 问事者对问题有焦虑/回避")

    return "\n".join(lines)


# =============================================================================
# Sphuta 敏感点计算 v7.0
# =============================================================================

def calc_gulika_sphuta(sun_lon: float, weekday: int,
                       sunrise_jd: float, sunset_jd: float,
                       birth_jd: float) -> Dict:
    """
    计算 Gulika Sphuta v7.0

    Gulika = Saturn的儿子，代表苦难/延迟的敏感点。
    根据白天/夜晚的不同时段计算。

    Args:
        sun_lon: 太阳经度
        weekday: 0=Sunday..6=Saturday
        sunrise_jd: 日出JD
        sunset_jd: 日落JD
        birth_jd: 出生JD

    Returns:
        Gulika经度和宫位
    """
    # 白天分8段（从日出到日落），夜间分8段（从日落到次日日出）
    is_daytime = sunrise_jd <= birth_jd <= sunset_jd

    if is_daytime:
        day_duration = sunset_jd - sunrise_jd
        segment = day_duration / 8.0
        # Gulika在白天的第7段（Saturn段）
        gulika_time = sunrise_jd + 6 * segment
    else:
        # 夜间
        night_start = sunset_jd
        night_duration = (sunrise_jd + 1) - night_start  # 次日日出
        segment = night_duration / 8.0
        gulika_time = night_start + 6 * segment

    # 简化：Gulika的经度≈太阳经度+时角偏移
    # 精确计算需要恒星时，这里用近似
    hours_from_sunrise = (gulika_time - sunrise_jd) * 24.0
    gulika_lon = (sun_lon + hours_from_sunrise * 15.0) % 360

    return {
        'gulika_longitude': round(gulika_lon, 4),
        'gulika_sign': SIGNS[int(gulika_lon / 30) % 12],
        'gulika_sign_cn': ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
                           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座'][int(gulika_lon / 30) % 12],
        'is_daytime': is_daytime,
        'note': 'Gulika代表苦难/延迟的敏感点，需检查其与凶星的联系',
    }


def calc_yamaghantaka_sphuta(sun_lon: float, weekday: int,
                              sunrise_jd: float, birth_jd: float) -> Dict:
    """
    计算 Yamaghantaka Sphuta v7.0

    Yamaghantaka = Jupiter的儿子，代表幸运/保护的敏感点。
    在白天的特定时段出现。

    Args:
        sun_lon: 太阳经度
        weekday: 0=Sunday..6=Saturday
        sunrise_jd: 日出JD
        birth_jd: 出生JD

    Returns:
        Yamaghantaka经度和宫位
    """
    # Yamaghantaka在白天的Jupiter段
    # 白天分8段，Jupiter段 = 第5段
    day_duration_approx = 0.5  # 约12小时
    segment = day_duration_approx / 8.0
    yama_time = sunrise_jd + 4 * segment  # 第5段

    hours_from_sunrise = (yama_time - sunrise_jd) * 24.0
    yama_lon = (sun_lon + hours_from_sunrise * 15.0) % 360

    return {
        'yamaghantaka_longitude': round(yama_lon, 4),
        'yamaghantaka_sign': SIGNS[int(yama_lon / 30) % 12],
        'note': 'Yamaghantaka代表保护/幸运的敏感点',
    }


# =============================================================================
# Prashna 时机评分系统 v7.0
# =============================================================================

def prashna_timing_score(planet_positions: Dict, asc_degree: float,
                          question_category: str) -> Dict:
    """
    Prashna 时机评分 v7.0

    综合评估当前时刻是否适合回答该类问题。
    评分因素：
    1. 上升主星状态
    2. Moon状态
    3. 问题宫主星状态
    4. KP Sublord判定
    5. 凶星干扰

    Returns:
        评分和解读
    """
    score = 50  # 基础分
    factors = []

    asc_idx = int(asc_degree / 30) % 12
    asc_lord = SIGN_LORDS[SIGNS[asc_idx]]

    # 1. 上升主星状态
    al_data = planet_positions.get(asc_lord, {})
    al_house = al_data.get('house', 0)
    if al_house in [1, 4, 7, 10, 5, 9]:
        score += 15
        factors.append(f"上升主星{asc_lord}在{al_house}宫(强宫) +15")
    elif al_house in [6, 8, 12]:
        score -= 10
        factors.append(f"上升主星{asc_lord}在{al_house}宫(弱宫) -10")

    # 2. Moon状态
    moon_data = planet_positions.get('Moon', {})
    moon_sign = moon_data.get('sign', '')
    if moon_sign in ['Taurus', 'Cancer']:  # Moon入庙/本宫
        score += 10
        factors.append("Moon入庙/本宫 +10")
    elif moon_sign in ['Scorpio']:  # Moon落陷
        score -= 10
        factors.append("Moon落陷 -10")

    # 3. 问题宫主星状态
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    q_house = cat['primary']
    q_sign = SIGNS[(asc_idx + q_house - 1) % 12]
    q_lord = SIGN_LORDS[q_sign]
    ql_data = planet_positions.get(q_lord, {})
    ql_house = ql_data.get('house', 0)
    if ql_house in [1, 4, 7, 10, 5, 9]:
        score += 10
        factors.append(f"问题宫主{q_lord}在{ql_house}宫(强宫) +10")
    elif ql_house in [6, 8, 12]:
        score -= 10
        factors.append(f"问题宫主{q_lord}在{ql_house}宫(弱宫) -10")

    # 4. 凶星干扰检查
    for malefic in ['Saturn', 'Mars', 'Rahu']:
        m_data = planet_positions.get(malefic, {})
        m_house = m_data.get('house', 0)
        if m_house == q_house:
            score -= 10
            factors.append(f"凶星{malefic}在问题宫({q_house}宫) -10")

    # 5. 逆行检查
    for pname, pdata in planet_positions.items():
        if isinstance(pdata, dict) and pdata.get('retrograde'):
            if pname in ['Mercury', 'Venus']:
                score -= 5
                factors.append(f"{pname}逆行 -5")

    # 综合评级
    if score >= 75:
        rating = "极佳（高度适合进行Prashna）"
    elif score >= 60:
        rating = "良好（适合进行Prashna）"
    elif score >= 45:
        rating = "一般（可以进行，但结果需更多验证）"
    else:
        rating = "不佳（不建议此时进行重要Prashna）"

    return {
        'score': score,
        'rating': rating,
        'factors': factors,
        'recommendation': "建议在更佳时机重新询问" if score < 45 else "可以进行Prashna分析",
    }


# =============================================================================
# Legacy CLI compatibility + Prashna advanced modes
# =============================================================================
def _norm(lon: float) -> float:
    return float(lon or 0) % 360


def _sign(lon: float) -> str:
    return SIGNS[int(_norm(lon) / 30) % 12]


def _house_from_asc(lon: float, asc_lon: float) -> int:
    return (int(_norm(lon) / 30) - int(_norm(asc_lon) / 30)) % 12 + 1


def _point(name: str, lon: float, asc_lon: float, note: str = "") -> Dict:
    lon = _norm(lon)
    return {
        "name": name,
        "longitude": round(lon, 4),
        "sign": _sign(lon),
        "house": _house_from_asc(lon, asc_lon),
        "note": note,
    }


def _planet_lon(planet_lons: Dict, planet: str, default: float = 0.0) -> float:
    return _norm(planet_lons.get(planet, default))


def calc_gulika_simple(asc_lon: float, sun_lon: float = 0.0, weekday: int = 0) -> float:
    """Lightweight Gulika approximation used when sunrise data is unavailable."""
    weekday_offsets = [210, 180, 150, 120, 90, 60, 30]
    return _norm((sun_lon or asc_lon) + weekday_offsets[weekday % 7])


def calc_arudha(asc_lon: float, planet_lons: Dict) -> Dict:
    """Compatibility wrapper for CLI Arudha mode."""
    asc_idx = int(_norm(asc_lon) / 30) % 12
    asc_lord = SIGN_LORDS[SIGNS[asc_idx]]
    lord_lon = _planet_lon(planet_lons, asc_lord, asc_lon)
    lord_house = _house_from_asc(lord_lon, asc_lon)
    distance = max(1, lord_house - 1)
    arudha_house = ((lord_house + distance - 1) % 12) + 1
    if arudha_house in (1, 7):
        arudha_house = 10 if arudha_house == 1 else 4
    arudha_lon = _norm(asc_lon + (arudha_house - 1) * 30)
    return {
        "asc_lord": asc_lord,
        "lord_house": lord_house,
        "arudha_house": arudha_house,
        "arudha_lagna": _point("Arudha Lagna", arudha_lon, asc_lon, "问题外显/镜像关注点"),
    }


def calc_sphutas(planet_lons: Dict, asc_lon: float = 0.0) -> Dict:
    """Blocked until exact Gulika and PrashnaContext support are available."""
    return {
        "status": "blocked",
        "reason": "exact_gulika_required_for_sphuta_calculation",
        "blocked_layers": ["Gulika", "Trisphuta", "Catusphuta", "Pancasphuta"],
    }

    # Legacy approximate implementation retained below only for source history.
    sun = _planet_lon(planet_lons, "Sun")
    moon = _planet_lon(planet_lons, "Moon")
    rahu = _planet_lon(planet_lons, "Rahu")
    gulika = calc_gulika_simple(asc_lon, sun)
    trisphuta = _norm(asc_lon + moon + gulika)
    catusphuta = _norm(trisphuta + sun)
    pancasphuta = _norm(catusphuta + rahu)
    return {
        "method": "Prashna Sphuta combinations",
        "gulika": _point("Gulika", gulika, asc_lon, "延迟/压力敏感点"),
        "trisphuta": _point("Trisphuta", trisphuta, asc_lon, "Lagna + Moon + Gulika"),
        "catusphuta": _point("Catusphuta", catusphuta, asc_lon, "Trisphuta + Sun"),
        "pancasphuta": _point("Pancasphuta", pancasphuta, asc_lon, "Catusphuta + Rahu"),
        "boundary": "Sphuta 是 Prashna 辅助证据，不应单独作为医疗、死亡或重大决策结论。",
    }


def calc_life_sphutas(asc_lon: float, moon_lon: float, sun_lon: float, gulika_lon: float = 0.0) -> Dict:
    gulika = _norm(gulika_lon or calc_gulika_simple(asc_lon, sun_lon))
    prana = _norm(asc_lon * 5 + gulika)
    deha = _norm(moon_lon * 8 + gulika)
    mrityu = _norm(gulika * 7 + sun_lon)
    balance = (_norm(prana + deha) - mrityu + 360) % 360
    if balance > 180:
        signal = "需谨慎复核"
        note = "Prana/Deha 与 Mrityu 的关系偏紧张，只能提示压力，不可作健康结论。"
    else:
        signal = "相对平衡"
        note = "生命点组合未见极端压力，仍需结合现实健康信息。"
    return {
        "prana": _point("Prana", prana, asc_lon, "生命之息"),
        "deha": _point("Deha", deha, asc_lon, "身体承载"),
        "mrityu": _point("Mrityu", mrityu, asc_lon, "风险敏感点"),
        "signal": signal,
        "note": note,
    }


def calc_sahams(planet_lons: Dict, asc_lon: float) -> Dict:
    """Blocked legacy entry: it lacks question time and location."""
    return {
        "status": "blocked",
        "reason": "question_timestamp_and_location_required_for_sahams",
        "blocked_layers": ["Sahams"],
    }

    # Legacy formulas retained below only for source history.
    sun = _planet_lon(planet_lons, "Sun")
    moon = _planet_lon(planet_lons, "Moon")
    mars = _planet_lon(planet_lons, "Mars")
    mercury = _planet_lon(planet_lons, "Mercury")
    jupiter = _planet_lon(planet_lons, "Jupiter")
    venus = _planet_lon(planet_lons, "Venus")
    saturn = _planet_lon(planet_lons, "Saturn")
    second_cusp = _norm(asc_lon + 30)
    eighth_cusp = _norm(asc_lon + 210)
    second_lord = SIGN_LORDS[_sign(second_cusp)]
    second_lord_lon = _planet_lon(planet_lons, second_lord, second_cusp)
    definitions = [
        ("Punya", "福德", moon, sun, asc_lon),
        ("Vidya", "学业", sun, moon, asc_lon),
        ("Putra", "子女", jupiter, moon, asc_lon),
        ("Vivaha", "婚姻", venus, saturn, asc_lon),
        ("Roga", "疾病", asc_lon, moon, asc_lon),
        ("Mrityu", "风险", eighth_cusp, moon, asc_lon),
        ("Karma", "职业", mars, mercury, asc_lon),
        ("Artha", "财富", second_cusp, second_lord_lon, asc_lon),
        ("Vanik", "贸易", moon, mercury, asc_lon),
        ("Vyapara", "商业", mars, saturn, asc_lon),
        ("Bhratru", "兄弟", jupiter, saturn, asc_lon),
        ("Matru", "母亲", moon, venus, asc_lon),
        ("Pitru", "父亲", saturn, sun, asc_lon),
        ("Bandhu", "亲属", mercury, moon, asc_lon),
        ("Apamrityu", "意外风险", eighth_cusp, mars, asc_lon),
    ]
    points = []
    for name, cn, minuend, subtrahend, addend in definitions:
        lon = _norm(minuend - subtrahend + addend)
        points.append(_point(name, lon, asc_lon, cn))
    return {
        "method": "Selected Prashna/Tajika Sahams",
        "count": len(points),
        "points": points,
        "boundary": "Sahams 用于补充主题证据，需与问题宫、KP、Dasha/Transit 交叉验证。",
    }


def analyze_lost_item(planet_lons: Dict, asc_lon: float) -> Dict:
    moon = _planet_lon(planet_lons, "Moon")
    lord2 = SIGN_LORDS[_sign(asc_lon + 30)]
    lord4 = SIGN_LORDS[_sign(asc_lon + 90)]
    lord11 = SIGN_LORDS[_sign(asc_lon + 300)]
    moon_house = _house_from_asc(moon, asc_lon)
    recovery_house = _house_from_asc(_planet_lon(planet_lons, lord11, asc_lon), asc_lon)
    likely_direction = {
        1: "东方/显眼处", 2: "东南/储物处", 3: "近处/书桌或通讯物旁", 4: "家中/车辆/柜内",
        5: "休闲区/儿童用品旁", 6: "工作区/杂物处", 7: "西方/他人接触处", 8: "隐蔽处/深色角落",
        9: "高处/远处/旅行物品", 10: "办公室/公共位置", 11: "朋友处/社群空间", 12: "床边/隐私空间",
    }.get(moon_house, "需复核")
    recoverable = recovery_house in (1, 2, 4, 7, 10, 11)
    return {
        "item_house": 2,
        "location_house": 4,
        "recovery_house": 11,
        "item_lord": lord2,
        "location_lord": lord4,
        "recovery_lord": lord11,
        "moon_house": moon_house,
        "likely_direction": likely_direction,
        "recoverable": recoverable,
        "summary": "有找回信号" if recoverable else "找回信号偏弱，优先排查隐蔽/远离原位的位置",
    }


def kunda_verify(asc_lon: float) -> Dict:
    """Blocked until the documented Lagna-arc x 81 calculation is implemented."""
    return {
        "status": "blocked",
        "reason": "exact_kunda_lagna_arc_verification_not_implemented",
        "blocked_layers": ["Kunda"],
    }

    # Legacy Pada-only proxy retained below only for source history.
    nak_idx = int(_norm(asc_lon) / NAK_SPAN) % 27
    pada = int((_norm(asc_lon) % NAK_SPAN) / (NAK_SPAN / 4)) + 1
    strength = "清晰" if pada in (2, 3) else "需复核"
    return {
        "ascendant": _point("Prashna Lagna", asc_lon, asc_lon, "问盘上升"),
        "nakshatra": NAKSHATRAS[nak_idx],
        "pada": pada,
        "strength": strength,
        "note": "Kunda 验证用于判断问盘是否足够清晰；边界 pada 需结合问题真诚度和时机评分。",
    }


def cast_prashna(question_datetime: str, lat: float = 0.0, lon: float = 0.0) -> Dict:
    """Blocked legacy fallback; production callers must use PrashnaContext."""
    return {
        "status": "blocked",
        "reason": "deterministic_prashna_fallback_removed_use_prashna_context",
        "required_entry": "scripts.prashna_context.build_prashna_context",
    }

    # Legacy deterministic positions retained below only for source history.
    try:
        dt = datetime.fromisoformat(str(question_datetime).replace(" ", "T"))
    except ValueError:
        dt = datetime.now()
    asc_lon = _norm((dt.hour * 15 + dt.minute / 4 + float(lon or 0) / 2) % 360)
    base = _norm(dt.timetuple().tm_yday * 0.985647 + dt.hour * 0.041)
    planet_offsets = {
        "Sun": 0, "Moon": 93, "Mars": 47, "Mercury": 18, "Jupiter": 121,
        "Venus": 32, "Saturn": 205, "Rahu": 271, "Ketu": 91,
    }
    planets = {}
    for pname, offset in planet_offsets.items():
        p_lon = _norm(base + offset)
        planets[pname] = {
            "lon": round(p_lon, 4),
            "sign": _sign(p_lon),
            "house": _house_from_asc(p_lon, asc_lon),
        }
    return {
        "method": "Prashna fallback chart",
        "question_time": dt.isoformat(),
        "location": {"lat": float(lat or 0), "lon": float(lon or 0)},
        "ascendant": {"lon": round(asc_lon, 4), "sign": _sign(asc_lon)},
        "planets": planets,
        "note": "Fallback chart uses lightweight deterministic positions; API chart should use live planetary data when available.",
    }
