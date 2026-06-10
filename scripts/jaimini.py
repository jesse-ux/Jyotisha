#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jaimini占星体系模块 v1.2
Parashara传承中的Jaimini子系统

支持:
  - Chara Karaka: 7/8个功能指示星（按度数排序）
  - Arudha Pada: A1-A12 + Upapada（UL），复用 dashaflow/jaimini-tropical 的 MIT 算法
  - Karakamsha: AK在Navamsa中的上升（灵魂方向）
  - Chara Dasha: 当前为简化 timing 实现，v6.0.9 后标注为 partial，不得单独作为高置信度应期依据
  - Special Lagnas: HL/GL/VL 简化计算（出生时间敏感，作为辅助）

MIT复用来源:
  - dashaflow (adarshj322): Arudha/Upapada公式与例外规则
  - jaimini-tropical (tunanfang-pixel): Pada命名、Graha Pada与Jaimini特殊点结构
"""
from typing import Dict, List, Tuple, Optional
import math

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

# Chara Karaka 定义（7星制，排除Rahu）
KARAKA_7 = {
    1: 'Atmakaraka',    # AK - 灵魂指示星（度数最高）
    2: 'Amatyakaraka',  # AmK - 事业/顾问
    3: 'Bhratrikaraka', # BK - 兄弟/勇气
    4: 'Matrikaraka',   # MK - 母亲
    5: 'Putrakaraka',   # PK - 子女
    6: 'Gnatikaraka',   # GK - 敌人/障碍
    7: 'Darakaraka',    # DK - 配偶（度数最低）
}

# 8星制（含Rahu，用绝对度数）
KARAKA_8 = {
    1: 'Atmakaraka', 2: 'Amatyakaraka', 3: 'Bhratrikaraka', 4: 'Matrikaraka',
    5: 'Putrakaraka', 6: 'Gnatikaraka', 7: 'Darakaraka', 8: 'Pitrukaraka',
}

KARAKA_CN = {
    'Atmakaraka': '灵魂星AK', 'Amatyakaraka': '事业星AmK',
    'Bhratrikaraka': '兄弟星BK', 'Matrikaraka': '母亲星MK',
    'Putrakaraka': '子女星PK', 'Gnatikaraka': '障碍星GK',
    'Darakaraka': '配偶星DK', 'Pitrukaraka': '父亲星PiK',
}

KARAKA_DOMAINS = {
    'Atmakaraka': '灵魂使命、核心自我、人生最高目标',
    'Amatyakaraka': '事业方向、主要谋士、权力代理',
    'Bhratrikaraka': '兄弟姐妹、勇气、冒险精神',
    'Matrikaraka': '母亲、家庭根基、情感安全感',
    'Putrakaraka': '子女、创造力、学生、智能成果',
    'Gnatikaraka': '竞争对手、疾病、障碍、转化力量',
    'Darakaraka': '配偶特质、伴侣关系、婚姻质量',
    'Pitrukaraka': '父亲、祖先业力、传统传承',
}

ARUDHA_NAMES = {
    1: 'Arudha Lagna (AL)', 2: 'Dhana Pada (A2)', 3: 'Vikrama Pada (A3)',
    4: 'Sukha Pada (A4)', 5: 'Mantra Pada (A5)', 6: 'Roga Pada (A6)',
    7: 'Dara Pada (A7)', 8: 'Mrityu Pada (A8)', 9: 'Dharma Pada (A9)',
    10: 'Karma Pada (A10)', 11: 'Labha Pada (A11)', 12: 'Upapada (UL)',
}


def _sign_idx(sign_name: str) -> int:
    return SIGNS.index(sign_name) if sign_name in SIGNS else 0


def _sign_name(sign_idx: int) -> str:
    return SIGNS[sign_idx % 12]


def _house_count(from_idx: int, to_idx: int) -> int:
    """从A星座顺数到B星座，含起点，返回1-12。"""
    return ((to_idx - from_idx) % 12) + 1


def calc_chara_karaka_7(planet_degrees: Dict[str, float]) -> Dict:
    """
    计算7星制Chara Karaka（度数最高→AK，最低→DK）
    
    参数: planet_degrees = {'Sun': 12.5, 'Moon': 8.3, ...}
          每个行星在星座内的度数（0-30）
    
    返回: {karaka_name: {'planet': str, 'degree': float, 'domain': str}}
    """
    exclude = {'Rahu', 'Ketu'}
    planets = {k: v for k, v in planet_degrees.items() if k not in exclude}
    sorted_planets = sorted(planets.items(), key=lambda x: x[1], reverse=True)
    results = {}
    for rank, (pname, deg) in enumerate(sorted_planets, 1):
        if rank > 7:
            break
        karaka = KARAKA_7[rank]
        results[karaka] = {
            'planet': pname,
            'degree_in_sign': round(deg, 4),
            'rank': rank,
            'domain': KARAKA_DOMAINS.get(karaka, ''),
            'cn_name': KARAKA_CN.get(karaka, karaka),
        }
    ak = results.get('Atmakaraka', {})
    dk = results.get('Darakaraka', {})
    return {
        'karaka_table': results,
        'summary': {
            'AK': f"{ak.get('planet','?')} ({ak.get('degree_in_sign',0):.1f}°)",
            'DK': f"{dk.get('planet','?')} ({dk.get('degree_in_sign',0):.1f}°)",
            'AK_domain': ak.get('domain', ''),
            'DK_domain': dk.get('domain', ''),
        }
    }


def calc_chara_karaka_8(planet_degrees: Dict[str, float]) -> Dict:
    """计算8星制Chara Karaka（含Rahu，Ketu排除）。"""
    planets = {}
    for pname, deg in planet_degrees.items():
        if pname == 'Ketu':
            continue
        planets[pname] = deg
    sorted_planets = sorted(planets.items(), key=lambda x: x[1], reverse=True)
    results = {}
    for rank, (pname, deg) in enumerate(sorted_planets, 1):
        if rank > 8:
            break
        karaka = KARAKA_8[rank]
        results[karaka] = {
            'planet': pname,
            'degree_in_sign': round(deg, 4),
            'rank': rank,
            'domain': KARAKA_DOMAINS.get(karaka, ''),
            'cn_name': KARAKA_CN.get(karaka, karaka),
        }
    return {'karaka_table_8': results}


def calc_arudha_pada_for_house(house_sign_idx: int, planet_longitudes: Dict[str, float]) -> Optional[Dict]:
    """
    计算单宫Arudha Pada。

    公式复用 dashaflow / jaimini-tropical MIT 实现：
    1. 从目标宫星座数到宫主所在星座；
    2. 从宫主所在星座再数同样距离；
    3. 若落回本宫或本宫第七，则改取本宫第十。
    """
    house_sign = _sign_name(house_sign_idx)
    lord = SIGN_LORDS[house_sign]
    if lord not in planet_longitudes:
        return None
    lord_sign_idx = int(planet_longitudes[lord] / 30) % 12
    distance = _house_count(house_sign_idx, lord_sign_idx)
    pada_idx = (lord_sign_idx + distance - 1) % 12
    exception_triggered = False
    if pada_idx == house_sign_idx or pada_idx == (house_sign_idx + 6) % 12:
        pada_idx = (house_sign_idx + 9) % 12
        exception_triggered = True
    return {
        'sign': _sign_name(pada_idx),
        'sign_idx': pada_idx,
        'lord': SIGN_LORDS[_sign_name(pada_idx)],
        'source_house_sign': house_sign,
        'source_house_lord': lord,
        'lord_sign': _sign_name(lord_sign_idx),
        'distance': distance,
        'exception_triggered': exception_triggered,
    }


def calc_arudha_padas(asc_sign_idx: int, planet_longitudes: Dict[str, float]) -> Dict:
    """计算A1-A12全部Arudha Padas，含Upapada/UL。"""
    padas = {}
    for house_num in range(1, 13):
        house_sign_idx = (asc_sign_idx + house_num - 1) % 12
        pada = calc_arudha_pada_for_house(house_sign_idx, planet_longitudes)
        if pada:
            pada.update({
                'house_num': house_num,
                'name': ARUDHA_NAMES.get(house_num, f'A{house_num}'),
            })
            padas[f'A{house_num}' if house_num != 12 else 'UL'] = pada
    return {
        'method': 'Arudha Pada A1-A12 (dashaflow/jaimini-tropical MIT adapted)',
        'ascendant': _sign_name(asc_sign_idx),
        'padas': padas,
        'arudha_lagna': padas.get('A1'),
        'upapada': padas.get('UL'),
    }


def calc_upapada(asc_sign_idx: int, planet_longitudes: Dict[str, float]) -> Optional[Dict]:
    """计算Upapada Lagna（第12宫Arudha）。"""
    result = calc_arudha_padas(asc_sign_idx, planet_longitudes).get('upapada')
    if result:
        second_idx = (result['sign_idx'] + 1) % 12
        result = dict(result)
        result['second_from_ul'] = _sign_name(second_idx)
        result['description'] = f"Upapada在{result['sign']}，第二宫为{result['second_from_ul']}，用于婚姻持续性与配偶外显画像。"
    return result


def calc_graha_padas(planet_longitudes: Dict[str, float]) -> Dict:
    """计算行星Graha Pada：行星位置通过其宫主映射出的外显影像。"""
    results = {}
    for planet, lon in planet_longitudes.items():
        if planet in ('Rahu', 'Ketu'):
            continue
        planet_sign_idx = int(lon / 30) % 12
        planet_sign = _sign_name(planet_sign_idx)
        lord = SIGN_LORDS[planet_sign]
        if lord not in planet_longitudes:
            continue
        lord_sign_idx = int(planet_longitudes[lord] / 30) % 12
        distance = _house_count(planet_sign_idx, lord_sign_idx)
        pada_idx = (lord_sign_idx + distance - 1) % 12
        results[planet] = {
            'planet_sign': planet_sign,
            'lord': lord,
            'lord_sign': _sign_name(lord_sign_idx),
            'graha_pada_sign': _sign_name(pada_idx),
            'graha_pada_sign_idx': pada_idx,
            'distance': distance,
        }
    return {'method': 'Graha Pada (jaimini-tropical MIT adapted)', 'graha_padas': results}


# ───────────────────────────────────────────────
# Chara Dasha 重写：KN Rao Method (v6.1.11)
# 来源: PyJHora KN Rao 算法，MIT适配实现
# 核心差异：Dasha 时长基于宫主所在宫位而非星座内行星计数
# ───────────────────────────────────────────────

# 偶数脚星座（由PyJHora const.even_footed_signs定义）
_EVEN_FOOTED_SIGNS = {1, 3, 5, 7, 9, 11}  # Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces

# 行星尊贵对照：exalted_sign_idx / debilitated_sign_idx
_PLANET_DIGNITY = {
    'Sun':     {'exalted': 0, 'debilitated': 6},    # Aries / Libra
    'Moon':    {'exalted': 1, 'debilitated': 7},    # Taurus / Scorpio
    'Mars':    {'exalted': 9, 'debilitated': 3},    # Capricorn / Cancer
    'Mercury': {'exalted': 5, 'debilitated': 11},   # Virgo / Pisces
    'Jupiter': {'exalted': 3, 'debilitated': 9},    # Cancer / Capricorn
    'Venus':   {'exalted': 11, 'debilitated': 5},   # Pisces / Virgo
    'Saturn':  {'exalted': 6, 'debilitated': 0},    # Libra / Aries
}


def _sign_is_even_footed(sign_idx: int) -> bool:
    """判断星座是否为偶数脚星座（用于KN Rao方向判定）。"""
    return sign_idx in _EVEN_FOOTED_SIGNS


def _count_rasis_forward(from_idx: int, to_idx: int) -> int:
    """从from_idx顺数到to_idx的星座数（含from_idx，1-12）。"""
    return ((to_idx - from_idx) % 12) + 1


def _count_rasis_backward(from_idx: int, to_idx: int) -> int:
    """从from_idx倒数到to_idx的星座数（含from_idx，1-12）。"""
    return ((from_idx - to_idx) % 12) + 1


def _get_planet_house(longitudes: Dict[str, float], planet: str) -> int:
    """根据行星经度获取所在宫位（0-11）。"""
    return int(longitudes.get(planet, 0) / 30) % 12


def _get_sign_lord_house(longitudes: Dict[str, float], sign_idx: int) -> int:
    """获取指定星座宫主所在宫位。"""
    sign_name = SIGNS[sign_idx]
    lord = SIGN_LORDS[sign_name]
    return _get_planet_house(longitudes, lord)


def _chara_dasha_duration_knrao(longitudes: Dict[str, float], sign_idx: int) -> int:
    """
    KN Rao Chara Dasha 大运时长计算。
    
    算法（对齐PyJHora _dhasa_duration_knrao_method）：
    1. 获取当前星座的宫主
    2. 获取宫主所在宫位
    3. 若星座为偶数脚(Taurus/Cancer/Virgo/Scorpio/Capricorn/Pisces)：
       从宫主宫位数到本星座（顺数）
    4. 若为奇数脚：从本星座数到宫主宫位（顺数）
    5. 结果减1
    6. 若宫主在所在宫位受尊(Exalted)：+1；若落陷(Debilitated)：-1
    7. 若≤0则设为12
    """
    lord = SIGN_LORDS[SIGNS[sign_idx]]
    lord_house = _get_planet_house(longitudes, lord)

    if _sign_is_even_footed(sign_idx):
        count = _count_rasis_forward(lord_house, sign_idx)
    else:
        count = _count_rasis_forward(sign_idx, lord_house)

    years = count - 1

    # 尊贵调整
    dignities = _PLANET_DIGNITY.get(lord, {})
    if dignities:
        if lord_house == dignities.get('exalted'):
            years += 1
        elif lord_house == dignities.get('debilitated'):
            years -= 1

    if years <= 0:
        years = 12
    return years


def _chara_progression_knrao(asc_sign_idx: int, longitudes: Dict[str, float]) -> list:
    """
    KN Rao Chara Dasha 星座序列生成。
    
    算法（对齐PyJHora _dhasa_progression_knrao_method）：
    1. 起始 = 上升星座
    2. 检查第9宫：若为偶数脚 → 逆向，否则正向
    3. 生成12个星座的顺序
    """
    ninth_idx = (asc_sign_idx + 8) % 12
    if _sign_is_even_footed(ninth_idx):
        return [(asc_sign_idx + 12 - i) % 12 for i in range(12)]
    else:
        return [(asc_sign_idx + i) % 12 for i in range(12)]


def _jd_to_date_tuple(jd: float):
    """将Julian Day转换为(year, month, day)元组。使用简化算法。"""
    try:
        import datetime
        import math
        # 简化转换：约化儒略日
        jd_i = int(jd + 0.5)
        f = (jd + 0.5) - jd_i
        if jd_i >= 2299161:
            a = (jd_i - 1867216.25) / 36524.25
            jd_i += 1 + int(a - int(a) / 4)
        b = jd_i + 1524
        c = (b - 122.1) / 365.25
        d = int(365.25 * c)
        e = (b - d) / 30.6001
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        return (int(year), int(month), int(day))
    except Exception:
        return (2000, 1, 1)


def calc_chara_dasha(asc_sign_idx: int,
                     planet_longitudes: Dict[str, float],
                     birth_year: int, birth_month: int,
                     birth_day: int = 1) -> Dict:
    """
    Chara Dasha计算（v6.1.11重写：KN Rao Method）
    
    来源：PyJHora chara.py KN Rao方法（AGPL算法 -> MIT独立实现）
    对齐目标：与PyJHora KN Rao method ≥95%匹配
    
    规则:
      - 序列：自上升起，第9宫决定顺逆
      - 时长：基于宫主所在宫位而非行星计数
      - 尊贵：Exalted +1年 / Debilitated -1年
    """
    progression = _chara_progression_knrao(asc_sign_idx, planet_longitudes)

    dasha_sequence = []
    for i, sign_idx in enumerate(progression):
        sign_name = SIGNS[sign_idx]
        lord = SIGN_LORDS[sign_name]
        duration = _chara_dasha_duration_knrao(planet_longitudes, sign_idx)

        # 宮主所在宫位
        lord_house = _get_planet_house(planet_longitudes, lord)
        lord_house_name = SIGNS[lord_house]

        # 尊贵状态
        dignities = _PLANET_DIGNITY.get(lord, {})
        dignity_status = 'none'
        if dignities:
            if lord_house == dignities.get('exalted'):
                dignity_status = 'exalted'
            elif lord_house == dignities.get('debilitated'):
                dignity_status = 'debilitated'

        dasha_sequence.append({
            'sign': sign_name,
            'sign_idx': sign_idx,
            'lord': lord,
            'lord_in_sign': lord_house_name,
            'lord_in_sign_idx': lord_house,
            'duration_years': duration,
            'dignity_adjustment': dignity_status,
            'order': i + 1,
        })

    total_years = sum(d['duration_years'] for d in dasha_sequence)

    return {
        'method': 'Chara Dasha (KN Rao Method, v6.1.11, PyJHora-aligned)',
        'ascendant': SIGNS[asc_sign_idx],
        'ascendant_idx': asc_sign_idx,
        'progression_source': '9th_house_direction',
        'dasha_sequence': dasha_sequence,
        'total_cycle_years': total_years,
        'capability_status': 'covered',
    }


def calc_chara_dasha_with_antardasha(asc_sign_idx: int,
                                      planet_longitudes: Dict[str, float],
                                      birth_year: int, birth_month: int,
                                      birth_day: int = 1) -> Dict:
    """
    Chara Dasha 完整3层计算（MD → AD → PD）
    
    使用KN Rao方法（v6.1.11重写）。
    Antardasha：等分法（parent/12），序列为Maha序列偏移1位。
    """
    base = calc_chara_dasha(asc_sign_idx, planet_longitudes, birth_year, birth_month, birth_day)
    progression = _chara_progression_knrao(asc_sign_idx, planet_longitudes)

    # Antardasha序列：Mahadasha序列偏移1（PyJHora method=2）
    antar_sequence = progression[1:] + progression[:1]

    for md in base['dasha_sequence']:
        md_sign_idx = md['sign_idx']
        md_duration_years = md['duration_years']

        antardasha_list = []
        for j, ad_sign_idx in enumerate(antar_sequence):
            ad_sign = SIGNS[ad_sign_idx]
            ad_lord = SIGN_LORDS[ad_sign]
            ad_duration = round(md_duration_years / 12.0, 3)

            # Pratyantar (第三层)：等分
            pratyantar_list = []
            for k, pd_sign_idx in enumerate(antar_sequence):
                pd_sign = SIGNS[pd_sign_idx]
                pd_lord = SIGN_LORDS[pd_sign]
                pd_duration = round(ad_duration / 12.0, 4)
                pratyantar_list.append({
                    'sign': pd_sign,
                    'sign_idx': pd_sign_idx,
                    'lord': pd_lord,
                    'duration_years': pd_duration,
                    'order': k + 1,
                })

            antardasha_list.append({
                'sign': ad_sign,
                'sign_idx': ad_sign_idx,
                'lord': ad_lord,
                'duration_years': ad_duration,
                'order': j + 1,
                'pratyantar_dashas': pratyantar_list,
            })

        md['antardashas'] = antardasha_list

    base['has_antardasha'] = True
    base['has_pratyantar'] = True
    base['antardasha_method'] = 'equal_division_12 (PyJHora method=2)'
    return base


def calc_karakamsha(ak_sign_in_d9: str, ak_degree_in_d9: float) -> Dict:
    """Karakamsha分析：AK在D9中的位置作为灵魂上升。"""
    lord = SIGN_LORDS.get(ak_sign_in_d9, '')
    interpretations = _karakamsha_interpretations(ak_sign_in_d9, lord)
    return {
        'karakamsha_sign': ak_sign_in_d9,
        'karakamsha_degree': ak_degree_in_d9,
        'karakamsha_lord': lord,
        'soul_direction': interpretations,
    }


def _karakamsha_interpretations(sign, lord):
    """Karakamsha的灵魂方向解读。"""
    directions = {
        'Aries': '灵魂追求独立、开拓、成为先驱',
        'Taurus': '灵魂追求稳定、物质安全感、感官和谐',
        'Gemini': '灵魂追求知识、沟通、多元体验',
        'Cancer': '灵魂追求情感连接、家庭、滋养他人',
        'Leo': '灵魂追求创造力、领导力、自我表达',
        'Virgo': '灵魂追求服务、完善、分析能力',
        'Libra': '灵魂追求平衡、关系和谐、美学',
        'Scorpio': '灵魂追求转化、深层真相、神秘学',
        'Sagittarius': '灵魂追求真理、哲学、智慧传播',
        'Capricorn': '灵魂追求成就、结构、社会贡献',
        'Aquarius': '灵魂追求革新、人道主义、群体觉醒',
        'Pisces': '灵魂追求灵性、超越、无条件的爱',
    }
    lord_meanings = {
        'Sun': '通过权威、创造力和自我实现达成',
        'Moon': '通过情感智慧、直觉和公众影响力达成',
        'Mars': '通过行动力、勇气和技术能力达成',
        'Mercury': '通过智慧、沟通和学习能力达成',
        'Jupiter': '通过智慧、教导和灵性成长达成',
        'Venus': '通过美学、关系和创造力达成',
        'Saturn': '通过耐力、自律和长期承诺达成',
    }
    return {
        'sign_direction': directions.get(sign, ''),
        'lord_method': lord_meanings.get(lord, ''),
    }


def calc_special_lagnas(asc_sign_idx: int, hour: int, minute: int = 0) -> Dict:
    """
    Jaimini特殊上升点简化版：HL/GL/VL。

    注：jaimini-tropical原版基于日出时间计算；这里在无日出依赖的CLI层提供
    可运行的近似辅助值，精确断语仍应优先使用出生地日出校正版本。
    """
    local_hours = hour + minute / 60.0
    ghatis = (local_hours / 24.0) * 60.0
    ghati_floor = int(ghatis)
    hl_idx = ghati_floor % 12 if ghati_floor % 2 else (7 - ghati_floor) % 12
    gl_idx = ghati_floor % 12
    vl_idx = (asc_sign_idx * 3) % 12
    return {
        'method': 'Special Lagnas HL/GL/VL simplified (jaimini-tropical MIT adapted; sunrise-sensitive)',
        'capability_status': 'auxiliary_partial',
        'ghatis_elapsed_from_midnight': round(ghatis, 4),
        'HL': {'sign': _sign_name(hl_idx), 'sign_idx': hl_idx, 'lord': SIGN_LORDS[_sign_name(hl_idx)]},
        'GL': {'sign': _sign_name(gl_idx), 'sign_idx': gl_idx, 'lord': SIGN_LORDS[_sign_name(gl_idx)]},
        'VL': {'sign': _sign_name(vl_idx), 'sign_idx': vl_idx, 'lord': SIGN_LORDS[_sign_name(vl_idx)]},
        'note': 'HL/GL/VL对日出非常敏感；本函数用于结构化补齐，精确版本需接入当地日出。'
    }
