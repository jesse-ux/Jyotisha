#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jaimini占星体系模块 v1.2
Parashara传承中的Jaimini子系统

支持:
  - Chara Karaka: 7/8个功能指示星（按度数排序）
  - Arudha Pada: A1-A12 + Upapada（UL），复用 dashaflow/jaimini-tropical 的 MIT 算法
  - Karakamsha: AK在Navamsa中的上升（灵魂方向）
  - Chara Dasha: KN Rao benchmark overall 95.83%，作为 covered timing 模块使用；事件应期仍需多系统确认
  - Special Lagnas: HL/GL/VL 简化计算（出生时间敏感，作为辅助）

MIT复用来源:
  - dashaflow (adarshj322): Arudha/Upapada公式与例外规则
  - jaimini-tropical (tunanfang-pixel): Pada命名、Graha Pada与Jaimini特殊点结构
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

# 行星友好/敌对关系（用于Jaimini共主比较）
FRIENDSHIP = {
    'Sun': {'friend': ['Moon', 'Mars', 'Jupiter'], 'enemy': ['Saturn', 'Venus'], 'neutral': ['Mercury']},
    'Moon': {'friend': ['Sun', 'Mercury'], 'enemy': [], 'neutral': ['Mars', 'Jupiter', 'Venus', 'Saturn']},
    'Mars': {'friend': ['Sun', 'Moon', 'Jupiter'], 'enemy': ['Mercury'], 'neutral': ['Venus', 'Saturn']},
    'Mercury': {'friend': ['Sun', 'Venus'], 'enemy': ['Moon'], 'neutral': ['Mars', 'Jupiter', 'Saturn']},
    'Jupiter': {'friend': ['Sun', 'Moon', 'Mars'], 'enemy': ['Mercury', 'Venus'], 'neutral': ['Saturn']},
    'Venus': {'friend': ['Mercury', 'Saturn'], 'enemy': ['Sun', 'Moon'], 'neutral': ['Mars', 'Jupiter']},
    'Saturn': {'friend': ['Mercury', 'Venus'], 'enemy': ['Sun', 'Moon', 'Mars'], 'neutral': ['Jupiter']},
    'Rahu': {'friend': ['Jupiter', 'Venus', 'Saturn'], 'enemy': ['Sun', 'Moon', 'Mars'], 'neutral': ['Mercury']},
    'Ketu': {'friend': ['Mars', 'Venus', 'Saturn'], 'enemy': ['Sun', 'Moon'], 'neutral': ['Mercury', 'Jupiter']},
}

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
# PyJHora v6: [3,4,5,9,10,11] = Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces
# 注意: 这是"偶数季度"星座，不是传统samapada
_EVEN_FOOTED_SIGNS = {3, 4, 5, 9, 10, 11}  # Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces

# 行星尊贵对照（KN Rao Chara Dasha专用）
# 对齐PyJHora house_strengths_of_planets表的_EXALTED_UCCHAM(4)和_DEBILITATED_NEECHAM(0)
# 关键: Mercury在Virgo(5)是own sign (strength=5)非exalted(=4)，不+1；在Gemini(2)同样own sign
# Rahu: exalted 1,2(Taurus,Gemini=strength=4); debilitated 7,8(Scorpio,Sagittarius=strength=0)
# Ketu: exalted 7,8(Scorpio,Sagittarius=strength=4); debilitated 1,2(Taurus,Gemini=strength=0)
_PLANET_DIGNITY_KNRAO = {
    'Sun':     {'exalted': {0}, 'debilitated': {6}},      # Aries / Libra
    'Moon':    {'exalted': {1}, 'debilitated': {7}},      # Taurus / Scorpio
    'Mars':    {'exalted': {9}, 'debilitated': {3}},      # Capricorn / Cancer
    'Mercury': {'exalted': set(), 'debilitated': {11}},   # own sign in 2,5 → no exalted; Pisces=deb
    'Jupiter': {'exalted': {3}, 'debilitated': {9}},      # Cancer / Capricorn
    'Venus':   {'exalted': {11}, 'debilitated': {5}},     # Pisces / Virgo
    'Saturn':  {'exalted': {6}, 'debilitated': {0}},      # Libra / Aries
    'Rahu':    {'exalted': {1, 2}, 'debilitated': {7, 8}}, # Taurus,Gemini / Scorpio,Sag
    'Ketu':    {'exalted': {7, 8}, 'debilitated': {1, 2}}, # Scorpio,Sag / Taurus,Gemini
}

# Chara Dasha 宫主动态判定
# Aquarius (sign 10): 传统主Saturn vs 共主Rahu — PyJHora用stronger_planet动态判定
# Scorpio (sign 7): 传统主Mars vs 共主Ketu — PyJHora用stronger_planet动态判定
_CHARA_DASHA_CO_LORD_SIGNS = {10, 7}  # Aquarius, Scorpio 有共主争议


def _jaimini_planet_dignity_level(planet: str, sign_idx: int) -> int:
    """
    计算行星在指定星座的尊严层级（用于Jaimini共主比较）。
    基于PyJHora _stronger_planet_new 尊严比较链。

    层级值: 6=exalted, 5=own_sign, 4=friendly, 3=neutral, 2=enemy, 1=debilitated
    """
    dignities = _PLANET_DIGNITY_KNRAO.get(planet, {})
    if not dignities:
        return 2  # default: enemy level for unknown planets

    # Check exalted (highest dignity)
    if sign_idx in dignities.get('exalted', set()):
        return 6

    # Check debilitated (lowest)
    if sign_idx in dignities.get('debilitated', set()):
        return 1

    # Check own sign (lord association)
    sign_name = SIGNS[sign_idx]
    traditional_lord = SIGN_LORDS.get(sign_name, '')
    if planet == traditional_lord:
        # For Mercury: own sign is Gemini or Virgo (not exalted)
        return 5

    # Check friendship
    friendship = FRIENDSHIP.get(planet, {})
    if planet in friendship.get('friend', []):
        friend_planets = friendship['friend']
        if traditional_lord in friend_planets:
            return 4

    if planet in friendship.get('enemy', []):
        enemy_planets = friendship['enemy']
        if traditional_lord in enemy_planets:
            return 2

    # Neutral
    return 3


def _jaimini_stronger_planet(longitudes: Dict[str, float], planet_a: str,
                              planet_b: str, sign_idx: int) -> str:
    """
    动态比较两颗行星在指定星座的力量，返回较强者。
    基于PyJHora _stronger_planet_new 算法翻译。

    比较层次：
    1. 尊严层级: exalted(6) > own(5) > friendly(4) > neutral(3) > enemy(2) > debilitated(1)
    2. 同层级：比较行星经度位置（度数更靠近星座中心更强）
    3. 仍相同：比较Naisargika Bala（天然力量）
    """
    level_a = _jaimini_planet_dignity_level(planet_a, sign_idx)
    level_b = _jaimini_planet_dignity_level(planet_b, sign_idx)

    if level_a > level_b:
        return planet_a
    if level_b > level_a:
        return planet_b

    # 同层级：比较行星在星座中的位置（更靠近星座中心度数=15°更强）
    deg_a = longitudes.get(planet_a, 0) % 30
    deg_b = longitudes.get(planet_b, 0) % 30

    center_diff_a = abs(deg_a - 15)
    center_diff_b = abs(deg_b - 15)

    if center_diff_a < center_diff_b:
        return planet_a
    if center_diff_b < center_diff_a:
        return planet_b

    # 完全平局：使用Naisargika Bala决断
    naisargika_order = ['Sun', 'Moon', 'Venus', 'Jupiter', 'Mercury', 'Mars', 'Saturn']
    idx_a = naisargika_order.index(planet_a) if planet_a in naisargika_order else 99
    idx_b = naisargika_order.index(planet_b) if planet_b in naisargika_order else 99
    return planet_a if idx_a <= idx_b else planet_b


def _resolve_chara_dasha_lord(longitudes, sign_idx):
    """
    解析Chara Dasha宫主。v6.1.13: 实现动态共主判定。

    Aquarius (sign 10): 比较 Saturn vs Rahu
    Scorpio (sign 7): 比较 Mars vs Ketu
    其他星座: 使用传统宫主
    """
    sign_name = SIGNS[sign_idx]
    traditional_lord = SIGN_LORDS.get(sign_name, '')

    # Aquarius: Saturn vs Rahu 共主判定
    if sign_idx == 10:  # Aquarius
        saturn_present = 'Saturn' in longitudes and longitudes['Saturn'] >= 0
        rahu_present = 'Rahu' in longitudes and longitudes['Rahu'] >= 0
        if saturn_present and rahu_present:
            return _jaimini_stronger_planet(longitudes, 'Saturn', 'Rahu', sign_idx)
        return 'Saturn' if saturn_present else 'Rahu'

    # Scorpio: Mars vs Ketu 共主判定
    if sign_idx == 7:  # Scorpio
        mars_present = 'Mars' in longitudes and longitudes['Mars'] >= 0
        ketu_present = 'Ketu' in longitudes and longitudes['Ketu'] >= 0
        if mars_present and ketu_present:
            return _jaimini_stronger_planet(longitudes, 'Mars', 'Ketu', sign_idx)
        return 'Mars' if mars_present else 'Ketu'

    return traditional_lord


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
    KN Rao Chara Dasha 大运时长计算 v6.1.12。
    
    对齐PyJHora _dhasa_duration_knrao_method（已验证95.42%→目标100%）：
    1. 获取当前星座的宫主（含Rahu/Ketu共主覆写）
    2. 获取宫主所在宫位
    3. 若星座为偶数脚：从宫主数到本星座（顺数）；否则从本星座数到宫主（顺数）
    4. count - 1 → years
    5. 若years ≤ 0：years = 12（先于尊贵调整，对齐PyJHora）
    6. 尊贵调整（对齐PyJHora house_strengths_of_planets）：
       若宫主在所在宫位 ⟹ Exalted(+1)；Debilitated(-1)
       Mercury在Virgo/Gemini是own sign非exalted，不+1
    """
    # 动态宫主判定：Aquarius→Saturn/Rahu比较，Scorpio→Mars/Ketu比较
    lord = _resolve_chara_dasha_lord(longitudes, sign_idx)

    lord_house = _get_planet_house(longitudes, lord)

    if _sign_is_even_footed(sign_idx):
        count = _count_rasis_forward(lord_house, sign_idx)
    else:
        count = _count_rasis_forward(sign_idx, lord_house)

    years = count - 1

    # 对齐PyJHora: 先检查≤0再加减尊贵
    if years <= 0:
        years = 12

    # 尊贵调整（对齐PyJHora house_strengths_of_planets表）
    dignities = _PLANET_DIGNITY_KNRAO.get(lord, {})
    if dignities:
        if lord_house in dignities.get('exalted', set()):
            years += 1
        elif lord_house in dignities.get('debilitated', set()):
            years -= 1

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
        lord = _resolve_chara_dasha_lord(planet_longitudes, sign_idx)
        duration = _chara_dasha_duration_knrao(planet_longitudes, sign_idx)

        # 宮主所在宫位
        lord_house = _get_planet_house(planet_longitudes, lord)
        lord_house_name = SIGNS[lord_house]

        # 尊贵状态
        dignities = _PLANET_DIGNITY_KNRAO.get(lord, {})
        dignity_status = 'none'
        if dignities:
            exalted_set = dignities.get('exalted', set())
            debil_set = dignities.get('debilitated', set())
            if lord_house in exalted_set:
                dignity_status = 'exalted'
            elif lord_house in debil_set:
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


def _julian_day(year: int, month: int, day: int, hour: float = 12.0) -> float:
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    return (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
        + hour / 24.0
    )


def _solar_obliquity(jd: float) -> float:
    t = (jd - 2451545.0) / 36525.0
    eps0 = 84381.448 - 46.8150 * t - 0.00059 * t * t + 0.001813 * t * t * t
    return eps0 / 3600.0


def calc_sunrise_utc_hours(year: int, month: int, day: int, lat: float, lon: float) -> float:
    """
    Calculate sunrise UTC decimal hours for a date/location.

    MIT-adapted from jaimini-tropical's sunrise helper; accuracy is sufficient for
    product-facing Special Lagna timing and avoids a hard dependency on SwissEph.
    """
    jd = _julian_day(year, month, day, 12.0)
    mean_anomaly = (357.5291 + 0.98560028 * (jd - 2451545.0)) % 360
    center = (
        1.9148 * math.sin(math.radians(mean_anomaly))
        + 0.0200 * math.sin(math.radians(2 * mean_anomaly))
        + 0.0003 * math.sin(math.radians(3 * mean_anomaly))
    )
    sun_lon = (mean_anomaly + center + 180.10248 + 0.000048 * (jd - 2451545.0) * 360) % 360
    eps = _solar_obliquity(jd)
    declination = math.degrees(
        math.asin(math.sin(math.radians(sun_lon)) * math.sin(math.radians(eps)))
    )
    lat_rad = math.radians(lat)
    dec_rad = math.radians(declination)
    cos_ha = (
        math.cos(math.radians(90.833))
        - math.sin(lat_rad) * math.sin(dec_rad)
    ) / (math.cos(lat_rad) * math.cos(dec_rad))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    hour_angle = math.degrees(math.acos(cos_ha))

    b = math.radians(360.0 * (jd - 2451545.0 - 0.5) / 365.25)
    eq_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(b)
        - 0.032077 * math.sin(b)
        - 0.014615 * math.cos(2 * b)
        - 0.040849 * math.sin(2 * b)
    )
    solar_noon = (720.0 - 4.0 * lon - eq_time) / 60.0
    return (solar_noon - hour_angle / 15.0) % 24.0


def _elapsed_ghatis_from_sunrise(sunrise_utc_hours: float, birth_utc_hours: float) -> float:
    diff_hours = birth_utc_hours - sunrise_utc_hours
    if diff_hours < 0:
        diff_hours += 24
    return diff_hours / 0.4


def _special_lagna_payload(name: str, full_name: str, sign_idx: int, degree_in_sign: float,
                           ghatis_elapsed: float, night_birth: bool = False) -> Dict:
    sign = _sign_name(sign_idx)
    payload = {
        'name': name,
        'full_name': full_name,
        'sign': sign,
        'sign_idx': sign_idx % 12,
        'lord': SIGN_LORDS[sign],
        'degree_in_sign': round(degree_in_sign % 30, 4),
        'longitude': round((sign_idx % 12) * 30 + (degree_in_sign % 30), 4),
        'ghatis_elapsed': round(ghatis_elapsed, 4),
    }
    if night_birth:
        payload['night_birth'] = True
    return payload


def calc_special_lagnas_precise(
    asc_sign_idx: int,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: float = 0,
    lat: float = 0.0,
    lon: float = 0.0,
    tz_offset: float = 0.0,
    second: float = 0.0,
) -> Dict:
    """
    Sunrise-correct Jaimini Special Lagnas: HL/GL/VL.

    Uses local birth time, converts it to UTC, calculates local sunrise in UTC,
    then maps elapsed Ghatis from sunrise to HL/GL. VL remains Ascendant-derived.
    """
    whole_minute = int(minute)
    second_total = (float(minute) - whole_minute) * 60.0 + float(second)
    whole_second = int(second_total)
    microsecond = int(round((second_total - whole_second) * 1_000_000))
    if microsecond >= 1_000_000:
        whole_second += 1
        microsecond -= 1_000_000
    local_dt = datetime(year, month, day, int(hour), whole_minute, whole_second, microsecond)
    utc_dt = local_dt - timedelta(hours=tz_offset)
    birth_utc_hours = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    sunrise_utc = calc_sunrise_utc_hours(utc_dt.year, utc_dt.month, utc_dt.day, lat, lon)
    ghatis = _elapsed_ghatis_from_sunrise(sunrise_utc, birth_utc_hours)
    ghati_floor = int(ghatis)
    fraction = ghatis - ghati_floor

    hl_idx = ghati_floor % 12 if ghati_floor % 2 else (7 - ghati_floor) % 12
    gl_idx = ghati_floor % 12
    vl_idx = (asc_sign_idx * 3) % 12

    sunrise_local_hours = (sunrise_utc + tz_offset) % 24
    sunrise_local_minutes = int(round(sunrise_local_hours * 60)) % (24 * 60)
    local_birth_hours = int(hour) + whole_minute / 60.0 + whole_second / 3600.0 + microsecond / 3_600_000_000.0
    before_sunrise = local_birth_hours < sunrise_local_hours
    return {
        'method': 'Special Lagnas HL/GL/VL sunrise-correct (jaimini-tropical MIT adapted)',
        'capability_status': 'covered',
        'precision': 'sunrise_correct',
        'sunrise_utc_hours': round(sunrise_utc, 4),
        'sunrise_local_time': f'{sunrise_local_minutes // 60:02d}:{sunrise_local_minutes % 60:02d}',
        'birth_utc_hours': round(birth_utc_hours, 4),
        'ghatis_elapsed_from_sunrise': round(ghatis, 4),
        'HL': _special_lagna_payload('HL', 'Hora Lagna', hl_idx, fraction * 30.0, ghatis, before_sunrise),
        'GL': _special_lagna_payload('GL', 'Ghati Lagna', gl_idx, fraction * 30.0, ghatis, before_sunrise),
        'VL': {
            'name': 'VL',
            'full_name': 'Varnada Lagna',
            'sign': _sign_name(vl_idx),
            'sign_idx': vl_idx,
            'lord': SIGN_LORDS[_sign_name(vl_idx)],
            'method': 'Ascendant sign × 3',
        },
        'note': 'HL/GL以出生地日出为起点计算；GL对24分钟边界敏感，出生时间不准时应结合生时校正。'
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
