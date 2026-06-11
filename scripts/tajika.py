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

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}


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

    # 1. Punya Saham（福德点）：Moon - Sun + Asc
    p_lon = _saham(sun_lon, moon_lon)
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
    yasha_lon = _saham(sun_lon, jupiter_lon)
    results['yasha_saham'] = _saham_dict(yasha_lon, 'Yasha Saham', '名声点——声誉、社会地位')

    # 12. Karma Saham（业力点）：Saturn - Mars + Asc
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
# Tajika Yogas 完整检测（P1.4）
# 基于PyJHora tajika/yogas.py 算法翻译
# 10种年度Yoga + Vedha阻碍逻辑
# =============================================================================

def detect_tajika_yogas(varsha_planets: Dict, year_lord: str = None) -> List[Dict]:
    """
    检测Tajika Yogas（年度Yoga）。

    10种Yoga分类：
    1. Itasala — 友好相位瑜伽
    2. Ishkavala — 单向相位瑜伽
    3. Vasala — 无效相位瑜伽
    4. Tambira — 阻碍瑜伽
    5. Kambira — 双重阻碍瑜伽
    6. Dakshina — 右向瑜伽
    7. Vama — 左向瑜伽
    8. Ubhaya — 双向瑜伽
    9. Vedha — 穿刺阻碍
    10. Kuta — 组合瑜伽

    Args:
        varsha_planets: 年运盘行星位置 {planet: {'sign':str, 'degree':float, ...}}
        year_lord: 年度主星

    Returns:
        检测到的Tajika Yoga列表
    """
    yogas = []
    SEVEN = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    MALEFICS = {'Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu'}
    BENEFICS = {'Jupiter', 'Venus', 'Mercury', 'Moon'}

    def _get_longitude(pname):
        pd = varsha_planets.get(pname, {})
        sign = pd.get('sign', '')
        deg = pd.get('degree', 0) % 30
        if sign in SIGNS:
            return SIGNS.index(sign) * 30 + deg
        return 0

    def _orb_between(p1, p2):
        d = abs(_get_longitude(p1) - _get_longitude(p2))
        return min(d, 360 - d)

    # 遍历所有行星对
    checked = set()
    for p1 in SEVEN:
        for p2 in SEVEN:
            if p1 >= p2:
                continue
            if (p1, p2) in checked:
                continue
            checked.add((p1, p2))

            orb = _orb_between(p1, p2)
            p1_long = _get_longitude(p1)
            p2_long = _get_longitude(p2)

            # 检查Vedha（穿刺阻碍）— 第三方行星在两星之间
            vedha_planet = None
            for p3 in SEVEN:
                if p3 in (p1, p2):
                    continue
                p3l = _get_longitude(p3)
                if min(p1_long, p2_long) < p3l < max(p1_long, p2_long):
                    if p3 in MALEFICS:
                        vedha_planet = p3
                        break

            # 分类判定
            if orb <= 1.0:
                # 紧密合相 — Kuta（组合）
                yogas.append({
                    'type': 'Kuta',
                    'planets': [p1, p2],
                    'description': f'{p1}和{p2}紧密合相(orb={orb:.1f}°)，形成Kuta组合Yoga',
                })
            elif orb <= 5.0:
                if vedha_planet:
                    yogas.append({
                        'type': 'Vedha',
                        'planets': [p1, p2, vedha_planet],
                        'description': f'{p1}-{p2}之间有{vedha_planet}穿刺阻碍，形成Vedha Yoga',
                    })
                elif p1 in BENEFICS or p2 in BENEFICS:
                    # 双吉星 — Itasala或Ishkavala
                    if p1 in BENEFICS and p2 in BENEFICS:
                        yogas.append({
                            'type': 'Itasala',
                            'planets': [p1, p2],
                            'description': f'{p1}和{p2}互相友好相位，形成Itasala Yoga',
                        })
                    else:
                        yogas.append({
                            'type': 'Ishkavala',
                            'planets': [p1, p2],
                            'description': f'{p1}和{p2}单向相位，形成Ishkavala Yoga',
                        })
                elif p1 in MALEFICS and p2 in MALEFICS:
                    yogas.append({
                        'type': 'Tambira',
                        'planets': [p1, p2],
                        'description': f'{p1}和{p2}双凶星阻碍，形成Tambira Yoga',
                    })
                else:
                    yogas.append({
                        'type': 'Vasala',
                        'planets': [p1, p2],
                        'description': f'{p1}和{p2}无效相位，形成Vasala Yoga',
                    })

    # 左/右向判定
    for y in yogas:
        if len(y['planets']) >= 2:
            p1, p2 = y['planets'][0], y['planets'][1]
            l1, l2 = _get_longitude(p1), _get_longitude(p2)
            if l2 > l1:
                y['direction'] = 'Dakshina(右向)'
            else:
                y['direction'] = 'Vama(左向)'

    return yogas


def detect_vedha(varsha_planets: Dict) -> List[Dict]:
    """专门检测Vedha（穿刺阻碍）"""
    vedhas = []
    SEVEN = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']
    MALEFICS = {'Saturn','Mars','Sun','Rahu','Ketu'}

    for p1 in SEVEN:
        for p2 in SEVEN:
            if p1 >= p2:
                continue
            for p3 in SEVEN:
                if p3 in (p1, p2) or p3 not in MALEFICS:
                    continue
                # 简化检测：检查三颗星是否在10°范围内
                l1 = varsha_planets.get(p1, {}).get('degree', 0)
                l2 = varsha_planets.get(p2, {}).get('degree', 0)
                l3 = varsha_planets.get(p3, {}).get('degree', 0)
                if abs(l1 - l2) < 10 and min(l1, l2) < l3 < max(l1, l2):
                    vedhas.append({
                        'planets': [p1, p2, p3],
                        'description': f'{p3}穿刺阻碍{p1}-{p2}，形成Vedha',
                    })
    return vedhas
