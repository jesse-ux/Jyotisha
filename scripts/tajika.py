#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tajika/Varshaphala年运盘模块 v1.0
太阳返照盘分析系统

支持:
  - Muntha（年度上升点移动）
  - Varshaphala计算（太阳回到出生位置时的星盘）
  - Mudda Dasha（年度大运）
  - Tajika Yoga（年度特殊格局）
  - Tri-Pataka（三旗系统）
  -年度Lord（Year Lord）
"""
from typing import Dict, List, Optional
from datetime import datetime
import math
import json
import os

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
CLASSICAL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
BENEFICS = {'Moon', 'Mercury', 'Jupiter', 'Venus'}
MALEFICS = {'Sun', 'Mars', 'Saturn'}
EXALT_SIGN = {'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6}
DEBIL_SIGN = {'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0}
OWN_SIGNS = {'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
             'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]}

SAHAM_RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references', 'saham_rules.json')


def _load_saham_rules() -> Dict:
    with open(SAHAM_RULES_PATH, 'r', encoding='utf-8') as handle:
        return json.load(handle)


_SAHAM_RULES = _load_saham_rules()


def _resolve_saham_operand(operand: str, planet_lons: Dict[str, float], asc_lon: float, computed: Dict[str, float]) -> float:
    if operand == 'Ascendant':
        return float(asc_lon) % 360
    if operand in computed:
        return float(computed[operand]) % 360
    if operand in planet_lons:
        return float(planet_lons[operand]) % 360
    raise KeyError(f"Unsupported saham operand: {operand}")


def _calc_formula_saham(
    rule_name: str,
    planet_lons: Dict[str, float],
    asc_lon: float,
    is_day: bool,
    computed: Dict[str, float],
) -> float:
    rule = _SAHAM_RULES['sahams'][rule_name]
    formula = rule['formula_day'] if is_day else rule['formula_night']
    first = _resolve_saham_operand(formula[0], planet_lons, asc_lon, computed)
    second = _resolve_saham_operand(formula[1], planet_lons, asc_lon, computed)
    third = _resolve_saham_operand(formula[2], planet_lons, asc_lon, computed)
    return (third + (first - second)) % 360


def calc_muntha(birth_asc_idx: int, age: int) -> Dict:
    """
    Muntha计算：年度上升点
    从出生上升星座开始，每年前进一个星座
    
    参数:
        birth_asc_idx: 出生上升星座索引（0=Aries）
        age: 当前年龄（整数）
    """
    muntha_idx = (birth_asc_idx + age) % 12
    muntha_sign = SIGNS[muntha_idx]
    lord = SIGN_LORDS[muntha_sign]
    
    # Muntha落在的宫位（从本命盘上升算起）
    # 需要本命盘上升来计算
    
    return {
        'muntha_sign': muntha_sign,
        'muntha_sign_idx': muntha_idx,
        'muntha_lord': lord,
        'age': age,
        'interpretation': _muntha_interp(muntha_sign, lord),
    }


def calc_year_lord(birth_asc_idx: int, age: int) -> Dict:
    """
    Year Lord（年度守护星）
    基于Muntha位置确定该年的守护行星
    
    规则:
      - Muntha落在某星座→该星座守护星为Year Lord
      - Muntha的2/5/9/11宫的守护星为辅助
    """
    muntha_idx = (birth_asc_idx + age) % 12
    muntha_sign = SIGNS[muntha_idx]
    year_lord = SIGN_LORDS[muntha_sign]
    
    # 辅助星（2/5/9/11宫主）
    aux_houses = [2, 5, 9, 11]
    aux_lords = []
    for h in aux_houses:
        h_sign_idx = (muntha_idx + h - 1) % 12
        h_sign = SIGNS[h_sign_idx]
        aux_lords.append({'house': h, 'sign': h_sign, 'lord': SIGN_LORDS[h_sign]})
    
    return {
        'age': age,
        'year_lord': year_lord,
        'muntha_sign': muntha_sign,
        'auxiliary_lords': aux_lords,
        'year_theme': _year_theme(year_lord),
    }


def calc_varshaphala(birth_datetime: datetime, 
                     target_year: int,
                     birth_lon: float, birth_lat: float,
                     birth_tz: float) -> Dict:
    """
    Varshaphala（太阳返照盘）计算
    
    原理: 太阳回到出生时精确位置的时刻，重新起盘
    这个新的上升星座和行星配置代表该年的运势
    
    参数:
        birth_datetime: 出生时间
        target_year: 目标年份
        birth_lon/lat: 出生经纬度
        birth_tz: 出生时区
    """
    # 简化版：用Muntha + Year Lord + 基本Tajika规则
    # 完整版需要Swiss Ephemeris计算太阳精确返照时间
    
    # 出生上升（需要传入，这里用简化版）
    age = target_year - birth_datetime.year
    
    return {
        'target_year': target_year,
        'age': age,
        'note': 'Varshaphala完整计算需要Swiss Ephemeris精确返照时间',
        'components': {
            'muntha': calc_muntha(0, age),  # 需要实际出生上升
            'year_lord': calc_year_lord(0, age),
        }
    }


def calc_mudda_dasha(asc_sign_idx: int, 
                     varsha_lord: str,
                     birth_month: int) -> Dict:
    """
    Mudda Dasha（年度大运）
    基于Varshaphala上升的12个月大运系统
    
    规则: 从年度守护星开始，按Vimshottari顺序排列
    每个大运按比例分配12个月
    """
    DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
    DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}
    
    start_idx = DASHA_ORDER.index(varsha_lord) if varsha_lord in DASHA_ORDER else 0
    
    sequence = []
    remaining_months = 12.0
    
    for i in range(9):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        years = DASHA_YEARS[lord]
        months = years * 12.0 / 120.0  # 按比例分配
        
        if months > remaining_months:
            months = remaining_months
        remaining_months -= months
        
        sequence.append({
            'lord': lord,
            'months': round(months, 2),
            'order': i + 1,
        })
        
        if remaining_months <= 0:
            break
    
    return {
        'varsha_lord': varsha_lord,
        'dasha_sequence': sequence,
        'total_months': 12,
    }


def calc_tri_pataka(planet_lons: Dict[str, float], 
                    varsha_lord: str,
                    muntha_sign_idx: int) -> Dict:
    """
    Tri-Pataka（三旗系统）
    Tajika占星中判断年度吉凶的重要技法
    
    三旗:
      1. Dasha Lord（大运守护星）的强度
      2. Muntha Lord（Muntha守护星）的强度  
      3. Year Lord（年度守护星）的强度
    
    三者都强→大吉年；三者都弱→凶年
    """
    muntha_lord = SIGN_LORDS.get(SIGNS[muntha_sign_idx], '')
    
    # 评估各守护星强度（简化版）
    def _strength(planet, lons):
        if planet not in lons:
            return 'unknown'
        lon = lons[planet]
        si = int(lon / 30) % 12
        # 简化：在角宫(1/4/7/10)=强，三方(5/9)=中，其他=弱
        house_from_asc = ((si - muntha_sign_idx) % 12) + 1
        if house_from_asc in (1, 4, 7, 10): return 'strong'
        if house_from_asc in (5, 9): return 'moderate'
        return 'weak'
    
    dl_strength = _strength(varsha_lord, planet_lons)
    ml_strength = _strength(muntha_lord, planet_lons)
    yl_strength = _strength(varsha_lord, planet_lons)
    
    strong_count = sum(1 for s in [dl_strength, ml_strength, yl_strength] if s == 'strong')
    weak_count = sum(1 for s in [dl_strength, ml_strength, yl_strength] if s == 'weak')
    
    if strong_count >= 2: verdict = 'excellent'
    elif weak_count >= 2: verdict = 'challenging'
    else: verdict = 'mixed'
    
    return {
        'dasha_lord': {'planet': varsha_lord, 'strength': dl_strength},
        'muntha_lord': {'planet': muntha_lord, 'strength': ml_strength},
        'year_lord': {'planet': varsha_lord, 'strength': yl_strength},
        'verdict': verdict,
        'interpretation': {
            'excellent': '三旗中两旗以上强旺，年度运势极佳',
            'mixed': '三旗力量参差不齐，年度运势起伏',
            'challenging': '三旗中两旗以上衰弱，年度运势挑战较大',
        }.get(verdict, ''),
    }


def calc_tajika_strength_layers(
    planet_lons: Dict[str, float],
    asc_lon: float = 0.0,
    year_lord: Optional[str] = None,
) -> Dict:
    """
    计算 Varshaphala 用户端所需的 Harsha Bala 与 Panchavargiya Bala 摘要层。

    该函数优先服务产品解释链：保留每颗星的分项分、等级和下一步提示。
    Panchavargiya 使用 Rasi、Hora、Drekkana、Navamsa、Dwadashamsa 五层分盘尊贵度
    作为稳定代理；若分盘模块不可用，则使用本地经度推导，避免年度 API 断链。
    """
    normalized = {
        planet: float(planet_lons[planet]) % 360
        for planet in CLASSICAL_PLANETS
        if planet in planet_lons and _is_number(planet_lons[planet])
    }
    harsha_bala = {}
    panchavargiya_bala = {}
    combined_strength = {}

    for planet, lon in normalized.items():
        harsha = _calc_harsha_bala_for_planet(planet, lon, asc_lon, year_lord)
        panchavargiya = _calc_panchavargiya_bala_for_planet(planet, lon)
        total = round(harsha['score'] + panchavargiya['score'], 2)
        max_score = harsha['max_score'] + panchavargiya['max_score']
        grade = _strength_grade(total, max_score)
        harsha_bala[planet] = harsha
        panchavargiya_bala[planet] = panchavargiya
        combined_strength[planet] = {
            'score': total,
            'max_score': max_score,
            'grade': grade,
            'components': {
                'harsha_bala': harsha['score'],
                'panchavargiya_bala': panchavargiya['score'],
            },
            'interpretation': _strength_interpretation(planet, grade),
        }

    ranked = sorted(
        (
            {'planet': planet, **data}
            for planet, data in combined_strength.items()
        ),
        key=lambda item: item['score'],
        reverse=True,
    )

    return {
        'method': 'Tajika Harsha/Panchavargiya Bala',
        'source': '本地 Tajika 强度模型：Harsha Bala + Panchavargiya 五分盘尊贵度代理，用于年度盘证据链与用户端排序。',
        'available_planets': len(normalized),
        'year_lord': year_lord or '',
        'ascendant_longitude': round(float(asc_lon or 0) % 360, 4),
        'harsha_bala': harsha_bala,
        'panchavargiya_bala': panchavargiya_bala,
        'combined_strength': combined_strength,
        'summary': {
            'strongest_planets': ranked[:3],
            'weakest_planets': list(reversed(ranked[-3:])) if ranked else [],
            'headline': _strength_headline(ranked),
            'next_action': '用最强星解释年度可主动推进的主题，用最弱星标注需要 Dasha/Transit 二次确认的风险点。',
        },
    }


def _is_number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _sign_idx_from_lon(lon: float) -> int:
    return int((float(lon) % 360) / 30) % 12


def _house_from_asc(lon: float, asc_lon: float) -> int:
    return ((_sign_idx_from_lon(lon) - _sign_idx_from_lon(asc_lon)) % 12) + 1


def _dignity_points(planet: str, sign_idx: int) -> float:
    if EXALT_SIGN.get(planet) == sign_idx:
        return 5.0
    if sign_idx in OWN_SIGNS.get(planet, []):
        return 4.0
    if DEBIL_SIGN.get(planet) == sign_idx:
        return 0.5
    sign_lord = SIGN_LORDS.get(SIGNS[sign_idx])
    if sign_lord == planet:
        return 4.0
    return 2.5


def _strength_grade(score: float, max_score: float) -> str:
    if max_score <= 0:
        return 'unknown'
    ratio = score / max_score
    if ratio >= 0.78:
        return 'excellent'
    if ratio >= 0.62:
        return 'strong'
    if ratio >= 0.42:
        return 'moderate'
    return 'weak'


def _calc_harsha_bala_for_planet(planet: str, lon: float, asc_lon: float, year_lord: Optional[str]) -> Dict:
    house = _house_from_asc(lon, asc_lon)
    sign_idx = _sign_idx_from_lon(lon)
    house_joy = _harsha_house_points(planet, house)
    dignity = _dignity_points(planet, sign_idx)
    year_lord_bonus = 3.0 if year_lord == planet else 0.0
    angular_support = 2.0 if house in (1, 4, 7, 10) else 1.0 if house in (5, 9, 11) else 0.0
    score = round(house_joy + dignity + year_lord_bonus + angular_support, 2)
    max_score = 15.0
    return {
        'score': min(score, max_score),
        'max_score': max_score,
        'grade': _strength_grade(score, max_score),
        'components': {
            'house': house,
            'sign': SIGNS[sign_idx],
            'house_joy': house_joy,
            'dignity': dignity,
            'year_lord_bonus': year_lord_bonus,
            'angular_support': angular_support,
        },
    }


def _harsha_house_points(planet: str, house: int) -> float:
    if planet in MALEFICS:
        if house in (3, 6, 10, 11):
            return 5.0
        if house in (1, 4, 7):
            return 2.5
        return 1.0
    if planet in BENEFICS:
        if house in (1, 2, 4, 5, 7, 9, 10, 11):
            return 5.0
        if house in (3, 6):
            return 2.0
        return 1.0
    return 2.5


def _calc_panchavargiya_bala_for_planet(planet: str, lon: float) -> Dict:
    components = {
        'rasi': _varga_dignity_component(planet, lon, 1),
        'hora': _varga_dignity_component(planet, lon, 2),
        'drekkana': _varga_dignity_component(planet, lon, 3),
        'navamsa': _varga_dignity_component(planet, lon, 9),
        'dwadasamsa': _varga_dignity_component(planet, lon, 12),
    }
    score = round(sum(item['points'] for item in components.values()), 2)
    max_score = 25.0
    return {
        'score': score,
        'max_score': max_score,
        'grade': _strength_grade(score, max_score),
        'components': components,
    }


def _varga_dignity_component(planet: str, lon: float, div: int) -> Dict:
    if div == 1:
        sign_idx = _sign_idx_from_lon(lon)
    else:
        sign_idx = _calc_varga_sign_idx(lon, div)
    points = _dignity_points(planet, sign_idx)
    return {
        'division': f'D{div}',
        'sign': SIGNS[sign_idx],
        'points': points,
        'dignity': _dignity_label(planet, sign_idx),
    }


def _calc_varga_sign_idx(lon: float, div: int) -> int:
    try:
        from varga import calc_varga
        return int(calc_varga(lon, div).get('sign_idx', _fallback_varga_sign_idx(lon, div))) % 12
    except Exception:
        return _fallback_varga_sign_idx(lon, div)


def _fallback_varga_sign_idx(lon: float, div: int) -> int:
    sign_idx = _sign_idx_from_lon(lon)
    degree_in_sign = (float(lon) % 30)
    part_index = int(degree_in_sign / (30.0 / div))
    if div == 2:
        return 4 if part_index == 0 else 3
    if div == 3:
        return (sign_idx + part_index * 4) % 12
    if div == 9:
        start = sign_idx if sign_idx % 3 == 0 else (sign_idx + 4) % 12 if sign_idx % 3 == 1 else (sign_idx + 8) % 12
        return (start + part_index) % 12
    if div == 12:
        return (sign_idx + part_index) % 12
    return sign_idx


def _dignity_label(planet: str, sign_idx: int) -> str:
    if EXALT_SIGN.get(planet) == sign_idx:
        return 'exalted'
    if sign_idx in OWN_SIGNS.get(planet, []):
        return 'own'
    if DEBIL_SIGN.get(planet) == sign_idx:
        return 'debilitated'
    return 'neutral'


def _strength_interpretation(planet: str, grade: str) -> str:
    planet_topics = {
        'Sun': '权威、目标感、父亲/上级',
        'Moon': '情绪、安全感、公众反馈',
        'Mars': '行动、竞争、执行压力',
        'Mercury': '沟通、交易、学习',
        'Jupiter': '机会、导师、财富增长',
        'Venus': '关系、审美、享受资源',
        'Saturn': '责任、结构、长期压力',
    }
    topic = planet_topics.get(planet, planet)
    if grade in ('excellent', 'strong'):
        return f'{planet} 强，年度可主动使用“{topic}”作为推进点。'
    if grade == 'moderate':
        return f'{planet} 中等，“{topic}”需结合 Dasha/Transit 再确认。'
    return f'{planet} 偏弱，“{topic}”宜作为风险提醒和补救重点。'


def _strength_headline(ranked: List[Dict]) -> str:
    if not ranked:
        return '缺少可用行星经度，暂无法生成 Tajika 强度摘要。'
    top = ranked[0]
    bottom = ranked[-1]
    return f"年度最可用行星为 {top['planet']}（{top['grade']}），最需复核行星为 {bottom['planet']}（{bottom['grade']}）。"


def _muntha_interp(sign, lord):
    """Muntha在12星座的基本解读"""
    interps = {
        'Aries': '年度主题：新开始、冒险、独立行动',
        'Taurus': '年度主题：财务稳定、物质积累、感官享受',
        'Gemini': '年度主题：学习、沟通、多元发展',
        'Cancer': '年度主题：家庭、情感、内在安全感',
        'Leo': '年度主题：创造力、领导力、自我表达',
        'Virgo': '年度主题：健康、服务、细节完善',
        'Libra': '年度主题：关系、合作、美学追求',
        'Scorpio': '年度主题：转化、深层变革、隐藏事物',
        'Sagittarius': '年度主题：远方旅行、哲学、高等教育',
        'Capricorn': '年度主题：事业成就、社会地位、长期规划',
        'Aquarius': '年度主题：社交网络、创新、人道主义',
        'Pisces': '年度主题：灵性成长、隐退、创意灵感',
    }
    return interps.get(sign, '')


def _year_theme(lord):
    """年度守护星主题"""
    themes = {
        'Sun': '权威、政府、父亲、领导力',
        'Moon': '公众、母亲、情感、直觉',
        'Mars': '行动、竞争、房地产、手术',
        'Mercury': '沟通、商业、学习、旅行',
        'Jupiter': '智慧、子女、宗教、财富',
        'Venus': '爱情、艺术、奢侈品、婚姻',
        'Saturn': '纪律、长寿、建筑、责任',
    }
    return themes.get(lord, '')


# ============================================================================
# Tajika Yogas（年运盘特殊格局）—— v6.0.13 新增
# ============================================================================

def calc_tajika_yogas(planet_lons: Dict[str, float],
                       planet_lats: Optional[Dict[str, float]] = None,
                       chart_type: str = 'varsha') -> Dict:
    """
    计算 Tajika Yogas（年运盘特殊格局）。

    参数:
        planet_lons: 行星经度字典 {行星名: 经度(0-360)}
        planet_lats: 行星纬度字典（可选，用于部分Yoga）
        chart_type: 'varsha'（年运盘）或 'natal'（本命盘）

    返回:
        {
            'yogas': [...],          # 检测到的Yogas列表
            'ithasala': [...],      # Ithasala连接瑜伽
            'easarapha': [...],    # Easarapha分离瑜伽
            'nakta': None,          # Nakta夜间瑜伽
            'yamaya': [...],        # Yamaya双重瑜伽
            'manahoo': [...],       # Manahoo特殊组合
            'graha_yuddha': [...], # Graha Yuddha行星战争
            'summary': str,         # 总结
        }
    """
    if planet_lats is None:
        planet_lats = {}

    Planet_LIST = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    results = {
        'yogas': [],
        'ithasala': [],
        'easarapha': [],
        'nakta': None,
        'yamaya': [],
        'manahoo': [],
        'graha_yuddha': [],
        'summary': '',
    }

    # ── 1. Ithasala Yoga（连接瑜伽）──
    # 定义：两行星同星座，快行星追慢行星（apply），度数差<=3度
    for i, p1 in enumerate(Planet_LIST):
        if p1 not in planet_lons:
            continue
        for p2 in Planet_LIST[i+1:]:
            if p2 not in planet_lons:
                continue
            lon1, lon2 = planet_lons[p1], planet_lons[p2]
            sign1 = int(lon1 / 30) % 12
            sign2 = int(lon2 / 30) % 12
            if sign1 != sign2:
                continue  # 不同星座

            diff = (lon2 - lon1) % 360
            if diff > 180:
                diff = 360 - diff

            # 判断谁快谁慢（简化：按行星自然速度）
            speed_order = ['Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Sun']
            # Rahu/Ketu逆行，速度特殊
            fast = p1 if _is_faster(p1, p2) else p2
            slow = p2 if fast == p1 else p1

            fast_lon = planet_lons[fast]
            slow_lon = planet_lons[slow]
            fast_diff = (fast_lon - slow_lon) % 360
            if fast_diff > 180:
                fast_diff = 360 - fast_diff

            # Ithasala：快追慢，差<=3度
            if fast_diff <= 3.0:
                yoga = {
                    'type': 'Ithasala',
                    'fast_planet': fast,
                    'slow_planet': slow,
                    'degree_diff': round(fast_diff, 4),
                    'sign': SIGNS[sign1],
                    'strength': 'strong' if fast_diff <= 1.0 else 'moderate',
                    'interpretation': _ithasala_interp(fast, slow, fast_diff),
                }
                results['ithasala'].append(yoga)
                results['yogas'].append(yoga)

    # ── 2. Easarapha Yoga（分离瑜伽）──
    # 定义：两行星同星座，快行星已离开慢行星（separate），度数差<=3度
    for i, p1 in enumerate(Planet_LIST):
        if p1 not in planet_lons:
            continue
        for p2 in Planet_LIST[i+1:]:
            if p2 not in planet_lons:
                continue
            lon1, lon2 = planet_lons[p1], planet_lons[p2]
            sign1 = int(lon1 / 30) % 12
            sign2 = int(lon2 / 30) % 12
            if sign1 != sign2:
                continue

            fast = p1 if _is_faster(p1, p2) else p2
            slow = p2 if fast == p1 else p1

            fast_lon = planet_lons[fast]
            slow_lon = planet_lons[slow]
            # 分离：快行星已过慢行星（在慢行星"后面"）
            # 即慢行星度数 > 快行星度数（在同一圈内）
            slow_in_sign = slow_lon % 30
            fast_in_sign = fast_lon % 30
            if slow_in_sign > fast_in_sign:
                # 慢在前面，快在后面 → 分离状态
                diff = slow_in_sign - fast_in_sign
                if diff <= 3.0:
                    yoga = {
                        'type': 'Easarapha',
                        'fast_planet': fast,
                        'slow_planet': slow,
                        'degree_diff': round(diff, 4),
                        'sign': SIGNS[sign1],
                        'strength': 'strong' if diff <= 1.0 else 'moderate',
                        'interpretation': _easarapha_interp(fast, slow, diff),
                    }
                    results['easarapha'].append(yoga)
                    results['yogas'].append(yoga)

    # ── 3. Nakta Yoga（夜间瑜伽）──
    # 定义：太阳和月亮同星座（任何度数）
    if 'Sun' in planet_lons and 'Moon' in planet_lons:
        sun_sign = int(planet_lons['Sun'] / 30) % 12
        moon_sign = int(planet_lons['Moon'] / 30) % 12
        if sun_sign == moon_sign:
            results['nakta'] = {
                'type': 'Nakta',
                'sun_sign': SIGNS[sun_sign],
                'moon_sign': SIGNS[moon_sign],
                'interpretation': '太阳月亮同星座，Nakta瑜伽——意志与情感合一，但可能过于自我中心',
            }
            results['yogas'].append(results['nakta'])

    # ── 4. Yamaya Yoga（双重瑜伽）──
    # 定义：Ithasala的强化版，两行星度数差<=1度，且两行星都在强星座
    for item in results['ithasala']:
        if item['degree_diff'] <= 1.0:
            yamaya = {
                'type': 'Yamaya',
                'planet1': item['fast_planet'],
                'planet2': item['slow_planet'],
                'degree_diff': item['degree_diff'],
                'sign': item['sign'],
                'interpretation': f"Yamaya瑜伽——{item['fast_planet']}与{item['slow_planet']}极度接近（{item['degree_diff']}度），双重能量融合",
            }
            results['yamaya'].append(yamaya)
            results['yogas'].append(yamaya)

    # ── 5. Manahoo（特殊组合）──
    # 定义：三行星同星座，且形成特殊组合
    sign_groups = {}
    for p in Planet_LIST:
        if p not in planet_lons:
            continue
        sign_idx = int(planet_lons[p] / 30) % 12
        if sign_idx not in sign_groups:
            sign_groups[sign_idx] = []
        sign_groups[sign_idx].append(p)

    for sign_idx, planets in sign_groups.items():
        if len(planets) >= 3:
            manahoo = {
                'type': 'Manahoo',
                'sign': SIGNS[sign_idx],
                'planets': planets,
                'planet_count': len(planets),
                'interpretation': f"Manahoo组合——{len(planets)}颗行星在{SIGNS[sign_idx]}（{', '.join(planets)}），能量高度集中",
            }
            results['manahoo'].append(manahoo)
            results['yogas'].append(manahoo)

    # ── 6. Graha Yuddha（行星战争）──
    # 定义：两行星度数差<=1度（极近距离）
    for i, p1 in enumerate(Planet_LIST):
        if p1 not in planet_lons or p1 in ('Rahu', 'Ketu'):
            continue
        for p2 in Planet_LIST[i+1:]:
            if p2 not in planet_lons or p2 in ('Rahu', 'Ketu'):
                continue
            lon1, lon2 = planet_lons[p1], planet_lons[p2]
            diff = abs(lon1 - lon2) % 360
            if diff > 180:
                diff = 360 - diff
            if diff <= 1.0:
                winner = p1 if _is_faster(p1, p2) else p2
                loser = p2 if winner == p1 else p1
                yuddha = {
                    'type': 'Graha Yuddha',
                    'planet1': p1,
                    'planet2': p2,
                    'degree_diff': round(diff, 4),
                    'winner': winner,
                    'loser': loser,
                    'sign': SIGNS[int(lon1 / 30) % 12],
                    'interpretation': f"Graha Yuddha——{p1}与{p2}极近（{diff}度），{winner}胜，{loser}受损",
                }
                results['graha_yuddha'].append(yuddha)
                results['yogas'].append(yuddha)

    # ── 总结 ──
    total = len(results['yogas'])
    results['summary'] = (
        f"Tajika Yogas检测：共{total}个格局。"
        f"Ithasala（连接）{len(results['ithasala'])}个，"
        f"Easarapha（分离）{len(results['easarapha'])}个，"
        f"Nakta（日月同度）{'1个' if results['nakta'] else '无'}，"
        f"Yamaya（双重）{len(results['yamaya'])}个，"
        f"Manahoo（三行星集中）{len(results['manahoo'])}个，"
        f"Graha Yuddha（行星战争）{len(results['graha_yuddha'])}个。"
    )

    return results


def _is_faster(p1: str, p2: str) -> bool:
    """判断p1是否比p2快（按自然速度）"""
    speeds = {
        'Moon': 13.176, 'Mercury': 4.092, 'Venus': 1.602,
        'Mars': 0.524, 'Jupiter': 0.083, 'Saturn': 0.034,
        'Sun': 0.986, 'Rahu': -0.053, 'Ketu': -0.053,
    }
    return abs(speeds.get(p1, 0)) > abs(speeds.get(p2, 0))


def _ithasala_interp(fast: str, slow: str, diff: float) -> str:
    """Ithasala瑜伽解读"""
    templates = [
        f"{fast}与{slow}形成Ithasala（连接瑜伽），两星能量融合，事件将要发生（差{diff}度）",
        f"预示：两星所主管领域将有合作、连接、顺利推进之象",
    ]
    return '；'.join(templates)


def _easarapha_interp(fast: str, slow: str, diff: float) -> str:
    """Easarapha瑜伽解读"""
    templates = [
        f"{fast}与{slow}形成Easarapha（分离瑜伽），两星能量分离，事件已过或受阻（差{diff}度）",
        f"预示：两星所主管领域将有分离、结束、阻碍之象",
    ]
    return '；'.join(templates)


# ============================================================================
# Sahams（特殊点计算）—— v6.0.13 新增
# ============================================================================

def calc_sahams(birth_dt: datetime,
                 sun_lon: float, moon_lon: float,
                 asc_lon: float,
                 yoga_point: float) -> Dict:
    """
    计算各种Sahams（特殊点）。

    参数:
        birth_dt: 出生时间（datetime）
        sun_lon: 太阳经度（0-360）
        moon_lon: 月亮经度（0-360）
        asc_lon: 上升经度（0-360）
        yoga_point: Yoga Point经度（0-360）

    返回:
        {
            'punya_saham': {...},   # 福德点
            'karya_saham': {...},   # 事业点
            'vivah_saham': {...},   # 婚姻点
            'rajya_saham': {...},   # 王权点
            'shatru_saham': {...},  # 敌人点
            'labha_saham': {...},   # 收益点
            'parakrama_saham': {...}, # 勇气点
        }
    """
    results = {}

    # 通用Saham计算公式（Tajika系统）：
    # Saham Lon = Asc Lon + (Planet2 Lon - Planet1 Lon)
    # 如果结果>=360，减去360

    def _calc_saham(p1_lon: float, p2_lon: float, asc: float) -> float:
        """计算Saham经度"""
        return (asc + (p2_lon - p1_lon)) % 360

    # Punya Saham（福德点）：Sun - Moon + Asc
    punya_lon = _calc_saham(moon_lon, sun_lon, asc_lon)
    results['punya_saham'] = {
        'longitude': round(punya_lon, 4),
        'sign': SIGNS[int(punya_lon / 30) % 12],
        'degree_in_sign': round(punya_lon % 30, 4),
        'interpretation': 'Punya Saham（福德点）——指示人生福德、善业积累、精神成长领域',
    }

    # Karya Saham（事业点）：Moon - Mars + Asc（日间）或 Mars - Moon + Asc（夜间）
    is_daytime = _is_daytime(birth_dt, sun_lon, asc_lon)
    if is_daytime:
        karya_lon = _calc_saham(mars_lon:=0, moon_lon, asc_lon)  # 需要Mars经度
        # 暂时用0占位，实际需要从外部传入
        results['karya_saham'] = {'note': '需要Mars经度，请从外部传入'}
    else:
        results['karya_saham'] = {'note': '夜间盘，需要Mars-Moon，请从外部传入'}

    # 简化版：直接返回结构，具体计算由调用方完成
    results['_note'] = 'Saham计算需要完整的行星经度，请在jyotish_engine.py中调用calc_all_sahams()'

    return results


def _is_daytime(birth_dt: datetime, sun_lon: float, asc_lon: float) -> bool:
    """判断出生时是白天还是夜间（简化：太阳在1-6宫=白天）"""
    sun_house = (int(sun_lon / 30) - int(asc_lon / 30)) % 12 + 1
    return sun_house in (1, 2, 3, 4, 5, 6)


def calc_all_sahams(planet_lons: Dict[str, float],
                    asc_lon: float,
                    birth_dt: datetime,
                    chart_type: str = 'natal') -> Dict:
    """
    计算所有主要Sahams（完整版）。

    参数:
        planet_lons: 所有行星经度 {名: 经度}
        asc_lon: 上升经度
        birth_dt: 出生时间
        chart_type: 'natal'（本命）或 'varsha'（年运）

    返回:
        完整Sahams字典
    """
    sun_lon = planet_lons.get('Sun', 0)
    moon_lon = planet_lons.get('Moon', 0)
    mars_lon = planet_lons.get('Mars', 0)
    jupiter_lon = planet_lons.get('Jupiter', 0)
    venus_lon = planet_lons.get('Venus', 0)
    saturn_lon = planet_lons.get('Saturn', 0)

    def _saham(p1_lon, p2_lon):
        return (asc_lon + (p2_lon - p1_lon)) % 360

    is_day = _is_daytime(birth_dt, sun_lon, asc_lon)

    results = {}
    computed_formula_sahams: Dict[str, float] = {}

    # 1. Punya Saham（福德点）：Moon - Sun + Asc
    p_lon = _calc_formula_saham('Punya_Saham', planet_lons, asc_lon, is_day, computed_formula_sahams)
    computed_formula_sahams['Punya_Saham'] = p_lon
    results['punya_saham'] = _saham_dict(p_lon, 'Punya Saham', '福德点——善业、精神成长、父系福德')

    # 2. Karya Saham（事业点）：
    # 日间：Mars - Moon + Asc；夜间：Moon - Mars + Asc
    if is_day:
        k_lon = _saham(moon_lon, mars_lon)
    else:
        k_lon = _saham(mars_lon, moon_lon)
    results['karya_saham'] = _saham_dict(k_lon, 'Karya Saham', '事业点——行动、努力、工作成果')

    # 3. Vivah Saham（婚姻点）：
    # 日间：Venus - Mars + Asc（男性）或 Mars - Venus + Asc（女性）
    # 简化：用Venus - Mars
    v_lon = _saham(mars_lon, venus_lon)
    results['vivah_saham'] = _saham_dict(v_lon, 'Vivah Saham', '婚姻点——婚姻、伴侣、情感关系')

    # 4. Rajya Saham（王权点）：Sun - Jupiter + Asc
    r_lon = _saham(jupiter_lon, sun_lon)
    results['rajya_saham'] = _saham_dict(r_lon, 'Rajya Saham', '王权点——地位、权威、社会认可')

    # 5. Shatru Saham（敌人点）：Mars - Saturn + Asc
    sh_lon = _saham(saturn_lon, mars_lon)
    results['shatru_saham'] = _saham_dict(sh_lon, 'Shatru Saham', '敌人点——竞争对手、障碍、冲突来源')

    # 6. Labha Saham（收益点）：Jupiter - Moon + Asc
    l_lon = _saham(moon_lon, jupiter_lon)
    results['labha_saham'] = _saham_dict(l_lon, 'Labha Saham', '收益点——收获、增益、扩张')

    # 7. Parakrama Saham（勇气点）：Mars - Sun + Asc
    pa_lon = _saham(sun_lon, mars_lon)
    results['parakrama_saham'] = _saham_dict(pa_lon, 'Parakrama Saham', '勇气点——勇气、竞争力、克服困难')

    # 8-36. 扩展Sahams（Tajika系统36种）
    # 8. Putra Saham（子女点）：Jupiter - Moon + Asc
    putra_lon = _saham(moon_lon, jupiter_lon)
    results['putra_saham'] = _saham_dict(putra_lon, 'Putra Saham', '子女点——子女、后代、创造力')

    # 9. Jnana Saham（教育点）：Jupiter - Mercury + Asc
    mercury_lon = planet_lons.get('Mercury', 0)
    jnana_lon = _saham(mercury_lon, jupiter_lon)
    results['jnana_saham'] = _saham_dict(jnana_lon, 'Jnana Saham', '教育点——学习、知识、智慧')

    # 10. Raja Saham（王权）：Sun - Moon + Asc
    raja_lon = _saham(moon_lon, sun_lon)
    results['raja_saham'] = _saham_dict(raja_lon, 'Raja Saham', '王权点——领导力、权威')

    # 11. Yasha Saham（名声点）：Jupiter - Sun + Asc
    try:
        yasha_lon = _calc_formula_saham('Yashas_Saham', planet_lons, asc_lon, is_day, computed_formula_sahams)
        computed_formula_sahams['Yashas_Saham'] = yasha_lon
    except KeyError:
        yasha_lon = _saham(sun_lon, jupiter_lon)
    results['yasha_saham'] = _saham_dict(yasha_lon, 'Yasha Saham', '名声点——声誉、社会地位')

    # 12. Karma Saham（业力点）：Saturn - Mars + Asc
    try:
        karma_lon = _calc_formula_saham('Karma_Saham', planet_lons, asc_lon, is_day, computed_formula_sahams)
        computed_formula_sahams['Karma_Saham'] = karma_lon
    except KeyError:
        karma_lon = _saham(mars_lon, saturn_lon)
    results['karma_saham'] = _saham_dict(karma_lon, 'Karma Saham', '业力点——前世因果、责任')

    # 13. Bandhu Saham（兄弟点）：Mars - Mercury + Asc
    bandhu_lon = _saham(mercury_lon, mars_lon)
    results['bandhu_saham'] = _saham_dict(bandhu_lon, 'Bandhu Saham', '兄弟点——兄弟姐妹、同辈')

    # 14. Matri Saham（母亲点）：Moon - Venus + Asc
    matri_lon = _saham(venus_lon, moon_lon)
    results['matri_saham'] = _saham_dict(matri_lon, 'Matri Saham', '母亲点——母亲、养育、情感滋养')

    # 15. Pitri Saham（父亲点）：Sun - Saturn + Asc
    pitri_lon = _saham(saturn_lon, sun_lon)
    results['pitri_saham'] = _saham_dict(pitri_lon, 'Pitri Saham', '父亲点——父亲、权威、传承')

    # 16. Janma Saham（出生点）：出生时刻敏感点
    j_lon = _saham(sun_lon, asc_lon)  # Special: Asc based
    results['janma_saham'] = _saham_dict(j_lon, 'Janma Saham', '出生点——生命起点、先天禀赋')

    # 17. Mrityu Saham（死亡点）：Saturn出生 - 8宫主 + Asc
    m_lon = _saham(mars_lon, saturn_lon)  # 近似
    results['mrityu_saham'] = _saham_dict(m_lon, 'Mrityu Saham', '死亡点——寿命、终结、转变')

    # 18. Rogha Saham（疾病点）：Mercury - Saturn + Asc
    rogha_lon = _saham(saturn_lon, mercury_lon)
    results['rogha_saham'] = _saham_dict(rogha_lon, 'Rogha Saham', '疾病点——健康、疾病倾向')

    # 19. Aarogya Saham（健康点）：Jupiter - Saturn + Asc
    aarogya_lon = _saham(saturn_lon, jupiter_lon)
    results['aarogya_saham'] = _saham_dict(aarogya_lon, 'Aarogya Saham', '健康点——康复、旺盛精力')

    # 20. Bhraatri Saham（同辈点）：Mars - Moon + Asc
    bhratr_lon = _saham(moon_lon, mars_lon)
    results['bhraatri_saham'] = _saham_dict(bhratr_lon, 'Bhraatri Saham', '同辈点——手足、社交圈')

    # 21. Ghataka Saham（冲突点）：Rahu - Mars + Asc
    rahu_lon = planet_lons.get('Rahu', 0)
    ghataka_lon = _saham(mars_lon, rahu_lon)
    results['ghataka_saham'] = _saham_dict(ghataka_lon, 'Ghataka Saham', '冲突点——意外、冲击、突袭')

    # 22. Paradesa Saham（海外点）：Saturn - Moon + Asc
    paradesa_lon = _saham(moon_lon, saturn_lon)
    results['paradesa_saham'] = _saham_dict(paradesa_lon, 'Paradesa Saham', '海外点——出国、异域、远方')

    # 23. Parabharya Saham（配偶点）：Venus - Mars + Asc（女性盘）
    parab_lon = _saham(mars_lon, venus_lon)
    results['parabharya_saham'] = _saham_dict(parab_lon, 'Parabharya Saham', '配偶点——伴侣特质')

    # 24. Dhan Saham（财富点）：Jupiter - Venus + Asc
    dhan_lon = _saham(venus_lon, jupiter_lon)
    results['dhan_saham'] = _saham_dict(dhan_lon, 'Dhan Saham', '财富点——金钱、资产、物质')

    # 25. Maya Saham（幻象点）：Rahu - Ketu + Asc
    ketu_lon = planet_lons.get('Ketu', 0)
    maya_lon = _saham(ketu_lon, rahu_lon)
    results['maya_saham'] = _saham_dict(maya_lon, 'Maya Saham', '幻象点——迷惑、欺骗、直觉')

    # 26. Moksha Saham（解脱点）：Ketu - Jupiter + Asc
    moksha_lon = _saham(jupiter_lon, ketu_lon)
    results['moksha_saham'] = _saham_dict(moksha_lon, 'Moksha Saham', '解脱点——灵性、开悟、超越')

    # 27. Buddha Saham（智慧点）：Mercury - Jupiter + Asc
    buddha_lon = _saham(jupiter_lon, mercury_lon)
    results['buddha_saham'] = _saham_dict(buddha_lon, 'Buddha Saham', '智慧点——智力、逻辑、语言')

    # 28. Shastra Saham（武器点）：Mars - Ketu + Asc
    shastra_lon = _saham(ketu_lon, mars_lon)
    results['shastra_saham'] = _saham_dict(shastra_lon, 'Shastra Saham', '武器点——攻击性、防御、技术')

    # 29. Kala Saham（时间点）：Saturn - Sun + Asc
    kala_lon = _saham(sun_lon, saturn_lon)
    results['kala_saham'] = _saham_dict(kala_lon, 'Kala Saham', '时间点——时机、节奏、耐心')

    # 30. Shakti Saham（力量点）：Venus - Moon + Asc
    shakti_lon = _saham(moon_lon, venus_lon)
    results['shakti_saham'] = _saham_dict(shakti_lon, 'Shakti Saham', '力量点——女性力量、魅力、创造力')

    # 31. Bhrigu Saham（先知点）：Venus - Jupiter + Asc
    bhrigu_lon = _saham(jupiter_lon, venus_lon)
    results['bhrigu_saham'] = _saham_dict(bhrigu_lon, 'Bhrigu Saham', '先知点——直觉、预见、智慧传承')

    # 32. Sundara Saham（美点）：Venus - Mercury + Asc
    sundara_lon = _saham(mercury_lon, venus_lon)
    results['sundara_saham'] = _saham_dict(sundara_lon, 'Sundara Saham', '美点——艺术、美感、和谐')

    # 33. Jnati Saham（亲戚点）：Mars - Saturn + Asc
    jnati_lon = _saham(saturn_lon, mars_lon)
    results['jnati_saham'] = _saham_dict(jnati_lon, 'Jnati Saham', '亲戚点——宗族、家族关系')

    # 34. Artha Saham（财富点）：Sun - Venus + Asc
    artha_lon = _saham(venus_lon, sun_lon)
    results['artha_saham'] = _saham_dict(artha_lon, 'Artha Saham', '财富点——物质繁荣、经济')

    # 35. Dharma Saham（正法点）：Jupiter - Saturn + Asc
    dharma_lon = _saham(saturn_lon, jupiter_lon)
    results['dharma_saham'] = _saham_dict(dharma_lon, 'Dharma Saham', '正法点——正义、道德、人生使命')

    # 36. Sangrama Saham（战斗点）：Mars - Rahu + Asc
    sangrama_lon = _saham(rahu_lon, mars_lon)
    results['sangrama_saham'] = _saham_dict(sangrama_lon, 'Sangrama Saham', '战斗点——竞争、挑战、胜利')

    return results


def _saham_dict(lon: float, name: str, interp: str) -> Dict:
    """构建Saham字典"""
    return {
        'longitude': round(lon, 4),
        'sign': SIGNS[int(lon / 30) % 12],
        'sign_cn': SIGNS_CN.get(SIGNS[int(lon / 30) % 12], ''),
        'degree_in_sign': round(lon % 30, 4),
        'name': name,
        'interpretation': interp,
    }


# 补充SIGNS_CN（中文星座名）
SIGNS_CN = {
    'Aries': '白羊', 'Taurus': '金牛', 'Gemini': '双子',
    'Cancer': '巨蟹', 'Leo': '狮子', 'Virgo': '处女',
    'Libra': '天秤', 'Scorpio': '天蝎', 'Sagittarius': '射手',
    'Capricorn': '摩羯', 'Aquarius': '水瓶', 'Pisces': '双鱼',
}


# =============================================================================
# Tajika Yogas 完整检测（v7.0 complete）
# 基于 BPHS Tajika + PyJHora tajika/yogas.py 算法翻译
# 10种年度Yoga + 完整Vedha阻碍逻辑 + Tajika相位规则
# =============================================================================

# Tajika相位表（不同于Parashara！Tajika使用西方式7种相位）
# 行=相位类型，列=度数范围
TAJIKA_ASPECT_DEGREES = {0, 30, 60, 90, 120, 150, 180}

# Tajika 容许度（orb）—— 各行星的标准容许度
TAJIKA_ORBS = {
    'Sun': 15, 'Moon': 12, 'Mars': 8, 'Mercury': 7,
    'Jupiter': 9, 'Venus': 7, 'Saturn': 9,
}

# Vedha 阻碍点表（Tajika经典）
# 每对行星间有固定的Vedha敏感度数位置
# 格式: (planet1_deg, planet2_deg) → 如果第三方行星在这个度数，则形成Vedha
VEDHA_TABLE = {
    # 从Ithasala点出发的度数偏移
    1: 7, 2: 5, 3: 9, 4: 3, 5: 8, 6: 2, 7: 10, 8: 4, 9: 6, 10: 1,
    11: 9, 12: 3, 13: 7, 14: 5, 15: 2, 16: 8, 17: 4, 18: 6, 19: 1, 20: 10,
    21: 3, 22: 9, 23: 5, 24: 7, 25: 2, 26: 8, 27: 4, 28: 6, 29: 1, 30: 10,
}


def detect_tajika_yogas(varsha_planets: Dict, year_lord: str = None) -> List[Dict]:
    """
    检测Tajika Yogas（年度Yoga）—— 完整版 v7.0。

    10种Yoga分类：
    1. Itasala (Ithasala) — 连接瑜伽（快追慢，orb≤行星容许度）
    2. Ishkavala — 单向相位瑜伽（一星与多星形成Ithasala）
    3. Vasala — 无效相位瑜伽（落陷星形成Ithasala）
    4. Tambira — 阻碍瑜伽（凶星在Ithasala之间）
    5. Kambira — 双重阻碍瑜伽（两凶星同时阻碍）
    6. Dakshina — 右向瑜伽（快星在慢星右侧）
    7. Vama — 左向瑜伽（快星在慢星左侧）
    8. Ubhaya — 双向瑜伽（两对Ithasala互相支持）
    9. Vedha — 穿刺阻碍（第三方在Vedha敏感点）
    10. Kuta — 组合瑜伽（三行星聚集同星座）

    Args:
        varsha_planets: 年运盘行星位置 {planet: {'sign':str, 'degree':float, ...}}
                       或 {planet: longitude_float}
        year_lord: 年度主星

    Returns:
        检测到的Tajika Yoga列表
    """
    yogas = []
    SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    MALEFICS = {'Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu'}
    BENEFICS = {'Jupiter', 'Venus', 'Mercury', 'Moon'}

    # 落陷星座表
    DEBILITATION = {
        'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer',
        'Mercury': 'Pisces', 'Jupiter': 'Capricorn',
        'Venus': 'Virgo', 'Saturn': 'Aries',
    }

    def _get_longitude(pname):
        pd = varsha_planets.get(pname, {})
        if isinstance(pd, (int, float)):
            return float(pd)
        sign = pd.get('sign', '')
        deg = pd.get('degree', 0) % 30
        if sign in SIGNS:
            return SIGNS.index(sign) * 30 + deg
        return pd.get('longitude', pd.get('lon', 0))

    def _get_sign(pname):
        lon = _get_longitude(pname)
        return int(lon / 30) % 12

    def _degree_in_sign(pname):
        lon = _get_longitude(pname)
        return lon % 30

    def _is_debilitated(pname):
        sign_idx = _get_sign(pname)
        sign_name = SIGNS[sign_idx]
        return DEBILITATION.get(pname) == sign_name

    def _is_faster(p1, p2):
        speeds = {
            'Moon': 13.176, 'Mercury': 4.092, 'Venus': 1.602,
            'Sun': 0.986, 'Mars': 0.524, 'Jupiter': 0.083, 'Saturn': 0.034,
        }
        return speeds.get(p1, 0) > speeds.get(p2, 0)

    def _orb_between(p1, p2):
        d = abs(_get_longitude(p1) - _get_longitude(p2))
        return min(d, 360 - d)

    def _effective_orb(p1, p2):
        """计算两星间的有效容许度（取较小者）"""
        return min(TAJIKA_ORBS.get(p1, 7), TAJIKA_ORBS.get(p2, 7))

    # ── 1. Ithasala Yoga（连接瑜伽）完整版 ──
    # 条件：快星追赶慢星（applying），orb ≤ 有效容许度
    ithasala_pairs = []
    checked = set()
    for p1 in SEVEN:
        for p2 in SEVEN:
            if p1 >= p2:
                continue
            if (p1, p2) in checked:
                continue
            checked.add((p1, p2))

            l1 = _get_longitude(p1)
            l2 = _get_longitude(p2)
            orb = _orb_between(p1, p2)
            eff_orb = _effective_orb(p1, p2)

            if orb > eff_orb:
                continue

            fast = p1 if _is_faster(p1, p2) else p2
            slow = p2 if fast == p1 else p1
            fast_lon = _get_longitude(fast)
            slow_lon = _get_longitude(slow)

            # 判断是否applying（快追慢）
            # 快星度数 < 慢星度数（同一方向）= applying
            applying = (fast_lon % 30) < (slow_lon % 30)

            if applying or orb <= 3.0:  # 3°内视为紧密连接
                ithasala_pairs.append({
                    'fast': fast, 'slow': slow, 'orb': orb,
                    'fast_lon': fast_lon, 'slow_lon': slow_lon,
                })

    for pair in ithasala_pairs:
        yogas.append({
            'type': 'Itasala',
            'planets': [pair['fast'], pair['slow']],
            'orb': round(pair['orb'], 2),
            'direction': 'applying',
            'description': f"{pair['fast']}(快)追{pair['slow']}(慢)，orb={pair['orb']:.1f}°，形成Itasala连接瑜伽",
        })

    # ── 2. Ishkavala Yoga（单向相位瑜伽）──
    # 条件：一星与多星形成Ithasala，且该星不在其他Ithasala中作为慢星
    planet_ithasala_count = {}
    for pair in ithasala_pairs:
        for p in [pair['fast'], pair['slow']]:
            planet_ithasala_count[p] = planet_ithasala_count.get(p, 0) + 1

    for p, count in planet_ithasala_count.items():
        if count >= 2:
            partners = []
            for pair in ithasala_pairs:
                if p in (pair['fast'], pair['slow']):
                    partner = pair['slow'] if p == pair['fast'] else pair['fast']
                    partners.append(partner)
            yogas.append({
                'type': 'Ishkavala',
                'planets': [p] + partners,
                'description': f'{p}与{", ".join(partners)}形成多个Ithasala，Ishkavala单向相位瑜伽',
            })

    # ── 3. Vasala Yoga（无效相位瑜伽）──
    # 条件：落陷星形成Ithasala
    for pair in ithasala_pairs:
        for p in [pair['fast'], pair['slow']]:
            if _is_debilitated(p):
                yogas.append({
                    'type': 'Vasala',
                    'planets': [pair['fast'], pair['slow']],
                    'description': f'{p}落陷状态下与{pair["slow"] if p == pair["fast"] else pair["fast"]}形成Ithasala，Vasala无效相位瑜伽',
                })

    # ── 4. Tambira Yoga（阻碍瑜伽）──
    # 条件：凶星在Ithasala两星之间（度数上）
    for pair in ithasala_pairs:
        l1, l2 = pair['fast_lon'], pair['slow_lon']
        for p3 in SEVEN:
            if p3 in (pair['fast'], pair['slow']):
                continue
            if p3 not in MALEFICS:
                continue
            l3 = _get_longitude(p3)
            # 检查p3是否在l1和l2之间
            lo, hi = min(l1, l2), max(l1, l2)
            if hi - lo > 180:
                # 跨越0°的情况
                if l3 > hi or l3 < lo:
                    yogas.append({
                        'type': 'Tambira',
                        'planets': [pair['fast'], pair['slow'], p3],
                        'description': f'凶星{p3}在{pair["fast"]}-{pair["slow"]}之间阻碍，Tambira阻碍瑜伽',
                    })
                    break
            else:
                if lo < l3 < hi:
                    yogas.append({
                        'type': 'Tambira',
                        'planets': [pair['fast'], pair['slow'], p3],
                        'description': f'凶星{p3}在{pair["fast"]}-{pair["slow"]}之间阻碍，Tambira阻碍瑜伽',
                    })
                    break

    # ── 5. Kambira Yoga（双重阻碍瑜伽）──
    # 条件：两个凶星同时阻碍同一对Ithasala
    for pair in ithasala_pairs:
        l1, l2 = pair['fast_lon'], pair['slow_lon']
        blockers = []
        for p3 in SEVEN:
            if p3 in (pair['fast'], pair['slow']) or p3 not in MALEFICS:
                continue
            l3 = _get_longitude(p3)
            lo, hi = min(l1, l2), max(l1, l2)
            between = False
            if hi - lo > 180:
                between = (l3 > hi or l3 < lo)
            else:
                between = (lo < l3 < hi)
            if between:
                blockers.append(p3)
        if len(blockers) >= 2:
            yogas.append({
                'type': 'Kambira',
                'planets': [pair['fast'], pair['slow']] + blockers[:2],
                'description': f'双凶星{blockers[0]}和{blockers[1]}同时阻碍{pair["fast"]}-{pair["slow"]}，Kambira双重阻碍瑜伽',
            })

    # ── 6-7. Dakshina/Vama Yoga（右/左向瑜伽）──
    for pair in ithasala_pairs:
        fast_lon = pair['fast_lon']
        slow_lon = pair['slow_lon']
        # 右向（Dakshina）：快星在慢星顺时针方向
        diff = (slow_lon - fast_lon) % 360
        direction = 'Dakshina(右向)' if diff <= 180 else 'Vama(左向)'
        direction_type = 'Dakshina' if diff <= 180 else 'Vama'
        yogas.append({
            'type': direction_type,
            'planets': [pair['fast'], pair['slow']],
            'description': f'{pair["fast"]}追{pair["slow"]}方向={direction}，{direction_type}方向瑜伽',
        })

    # ── 8. Ubhaya Yoga（双向瑜伽）──
    # 条件：两对Ithasala互相支持（A追B，C追D，且B和C在同一星座）
    for i, pair1 in enumerate(ithasala_pairs):
        for pair2 in ithasala_pairs[i+1:]:
            shared = set()
            s1 = {pair1['fast'], pair1['slow']}
            s2 = {pair2['fast'], pair2['slow']}
            overlap = s1 & s2
            if overlap:
                shared = overlap
            # 也检查同星座
            elif _get_sign(pair1['slow']) == _get_sign(pair2['fast']):
                yogas.append({
                    'type': 'Ubhaya',
                    'planets': [pair1['fast'], pair1['slow'], pair2['fast'], pair2['slow']],
                    'description': f'{pair1["fast"]}→{pair1["slow"]}与{pair2["fast"]}→{pair2["slow"]}互相支持，Ubhaya双向瑜伽',
                })

    # ── 9. Vedha Yoga（穿刺阻碍）完整版 ──
    # 条件：第三方行星在Vedha敏感度数上
    for pair in ithasala_pairs:
        l1, l2 = pair['fast_lon'], pair['slow_lon']
        mid_point = (l1 + l2) / 2.0 % 360
        for p3 in SEVEN:
            if p3 in (pair['fast'], pair['slow']):
                continue
            l3 = _get_longitude(p3)
            # Vedha检查：p3在敏感距离内
            for offset in [7, 5, 9, 3, 8, 2]:  # 经典Vedha偏移度数
                for sign_mult in [1, -1]:
                    vedha_point = (mid_point + sign_mult * offset) % 360
                    vedha_orb = abs(l3 - vedha_point)
                    if vedha_orb > 180:
                        vedha_orb = 360 - vedha_orb
                    if vedha_orb <= 2.0:  # 2°容许度
                        yogas.append({
                            'type': 'Vedha',
                            'planets': [pair['fast'], pair['slow'], p3],
                            'vedha_offset': offset,
                            'description': f'{p3}在Vedha敏感点（偏移{offset}°）穿刺{pair["fast"]}-{pair["slow"]}，Vedha穿刺瑜伽',
                        })
                        break
                else:
                    continue
                break

    # ── 10. Kuta Yoga（组合瑜伽）──
    # 条件：三颗以上行星聚集同一星座
    sign_groups = {}
    for p in SEVEN:
        sign_idx = _get_sign(p)
        if sign_idx not in sign_groups:
            sign_groups[sign_idx] = []
        sign_groups[sign_idx].append(p)

    for sign_idx, planets in sign_groups.items():
        if len(planets) >= 3:
            yogas.append({
                'type': 'Kuta',
                'planets': planets,
                'description': f'{len(planets)}颗行星({", ".join(planets)})聚集在{SIGNS[sign_idx]}，Kuta组合瑜伽',
            })

    # ── 额外: Radda Yoga（废弃瑜伽）──
    # 条件：Ithasala被Vedha完全破坏
    for pair in ithasala_pairs:
        vedha_count = sum(1 for y in yogas
                         if y['type'] == 'Vedha'
                         and pair['fast'] in y['planets']
                         and pair['slow'] in y['planets'])
        if vedha_count >= 2:
            yogas.append({
                'type': 'Radda',
                'planets': [pair['fast'], pair['slow']],
                'description': f'{pair["fast"]}-{pair["slow"]}的Ithasala被多重Vedha破坏，Radda废弃瑜伽',
            })

    return yogas


def detect_vedha(varsha_planets: Dict) -> List[Dict]:
    """
    专门检测Vedha（穿刺阻碍）—— 完整版 v7.0

    基于经典Tajika Vedha表：每对行星有固定敏感度数位置，
    当第三方行星落入该位置时，破坏原有的Ithasala/Easarapha。

    Args:
        varsha_planets: 年运盘行星数据

    Returns:
        Vedha列表
    """
    vedhas = []
    SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    def _get_lon(pname):
        pd = varsha_planets.get(pname, {})
        if isinstance(pd, (int, float)):
            return float(pd)
        sign = pd.get('sign', '')
        deg = pd.get('degree', 0) % 30
        if sign in SIGNS:
            return SIGNS.index(sign) * 30 + deg
        return pd.get('longitude', pd.get('lon', 0))

    # Vedha敏感度数（经典Tajika规则）
    # 对于度数差N（1-30），Vedha在特定偏移处
    VEDHA_OFFSETS = {
        1: 7, 2: 5, 3: 9, 4: 3, 5: 8, 6: 2, 7: 10, 8: 4,
        9: 6, 10: 1, 11: 9, 12: 3, 13: 7, 14: 5, 15: 2,
    }

    for p1 in SEVEN:
        for p2 in SEVEN:
            if p1 >= p2:
                continue

            l1 = _get_lon(p1)
            l2 = _get_lon(p2)

            # 计算两星间度数差
            diff = abs(l1 - l2)
            if diff > 180:
                diff = 360 - diff

            if diff > 15:  # 超出Vedha表范围
                continue

            # 查找Vedha偏移
            diff_key = int(diff) + 1  # 1-based
            if diff_key not in VEDHA_OFFSETS:
                continue

            offset = VEDHA_OFFSETS[diff_key]

            # 计算Vedha敏感点
            mid = (l1 + l2) / 2.0 % 360
            for sign_mult in [1, -1]:
                vedha_point = (mid + sign_mult * offset) % 360

                # 检查是否有第三方行星在敏感点±2°内
                for p3 in SEVEN:
                    if p3 in (p1, p2):
                        continue
                    l3 = _get_lon(p3)
                    vedha_orb = abs(l3 - vedha_point)
                    if vedha_orb > 180:
                        vedha_orb = 360 - vedha_orb
                    if vedha_orb <= 2.0:
                        vedhas.append({
                            'planets': [p1, p2, p3],
                            'vedha_degree': round(vedha_point, 2),
                            'offset': offset,
                            'orb': round(vedha_orb, 2),
                            'description': f'{p3}在Vedha敏感点({offset}°偏移)穿刺{p1}-{p2}',
                        })

    return vedhas
