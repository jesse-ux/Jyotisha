"""
muhurta.py  v6.0.21 — Muhurta（择时占星）核心计算模块

Muhurta 是印度占星的择时系统，核心是 Panchanga 五要素：
  1. Tithi（月相日）  — 月亮与太阳之间的角度 / 12°
  2. Vara（周日）     — 星期对应的行星守护
  3. Nakshatra（星宿）— 月亮所在星宿
  4. Yoga（瑜伽）     — 太阳 + 月亮黄经之和 / (360/27)
  5. Karana（半日）   — 每半个 Tithi 为一 Karana

每个元素都有吉（Subha）/ 凶（Asubha）/ 中性（Mixed）属性，
组合评分决定特定时间段是否适合某类活动。
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

# ── Vara（周日行星）──────────────────────────────────────────────────
VARA_LORDS = {
    0: ('Sunday',    'Sun',     'asubha'),  # 周日
    1: ('Monday',    'Moon',    'subha'),
    2: ('Tuesday',   'Mars',    'asubha'),
    3: ('Wednesday', 'Mercury', 'mixed'),
    4: ('Thursday',  'Jupiter', 'subha'),
    5: ('Friday',    'Venus',   'subha'),
    6: ('Saturday',  'Saturn',  'asubha'),
}

# Hora（每小时行星）— 从日出起每小时依次排列
# 顺序: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars
HORA_ORDER = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
# 每日起始 Hora = Vara Lord 在 HORA_ORDER 中的位置
VARA_START_IDX = {
    'Sun': 0, 'Venus': 1, 'Mercury': 2, 'Moon': 3,
    'Saturn': 4, 'Jupiter': 5, 'Mars': 6
}

# ── Tithi（月相日）────────────────────────────────────────────────────
# 1-15 = Shukla Paksha, 16-30 = Krishna Paksha
TITHI_NAMES = [
    '', 'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima/Amavasya'
]
# 吉凶：1=subha, 0=asubha, 0.5=mixed
TITHI_QUALITY = {
    1: 'subha', 2: 'subha', 3: 'subha', 4: 'asubha', 5: 'subha',
    6: 'mixed', 7: 'subha', 8: 'asubha', 9: 'mixed', 10: 'subha',
    11: 'subha', 12: 'subha', 13: 'asubha', 14: 'asubha',
    15: 'subha',  # Purnima = Shukla 15（满月）
    16: 'subha',  # Pratipada Krishna
    17: 'subha', 18: 'subha', 19: 'asubha', 20: 'subha',
    21: 'mixed', 22: 'subha', 23: 'asubha', 24: 'mixed', 25: 'subha',
    26: 'subha', 27: 'subha', 28: 'asubha', 29: 'asubha',
    30: 'asubha'  # Amavasya（新月）
}

# ── Nakshatra（27 星宿）──────────────────────────────────────────────
NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha',
    'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]
# Nakshatra 吉凶分类（Muhurta 视角）
NAKSHATRA_TYPE = {
    'Ashwini': 'laghu',      # 轻快 → 手术、旅行
    'Bharani': 'ugra',       # 凶猛 → 不利开始
    'Krittika': 'mixed',     # 混合
    'Rohini': 'sthira',      # 固定/吉 → 种植、建筑
    'Mrigashira': 'mridu',   # 柔和 → 艺术、爱情
    'Ardra': 'tikshna',      # 尖锐 → 不宜重要事
    'Punarvasu': 'chara',    # 动态 → 旅行
    'Pushya': 'laghu',       # 最吉 → 几乎万能
    'Ashlesha': 'tikshna',   # 蛇宿 → 不宜
    'Magha': 'ugra',         # 凶 → 不宜
    'Purva Phalguni': 'ugra',# 凶
    'Uttara Phalguni': 'sthira',  # 吉
    'Hasta': 'laghu',        # 轻快/吉
    'Chitra': 'mridu',       # 柔和
    'Swati': 'chara',        # 动态
    'Vishakha': 'mixed',     # 混合
    'Anuradha': 'mridu',     # 柔和
    'Jyeshtha': 'tikshna',   # 尖锐
    'Mula': 'tikshna',       # 最凶 → 不宜开始
    'Purva Ashadha': 'ugra', # 凶
    'Uttara Ashadha': 'sthira',   # 吉
    'Shravana': 'mridu',     # 柔和/吉
    'Dhanishtha': 'chara',   # 动态
    'Shatabhisha': 'chara',  # 动态
    'Purva Bhadrapada': 'ugra',   # 凶
    'Uttara Bhadrapada': 'sthira',# 吉
    'Revati': 'mridu',       # 柔和
}
NAKSHATRA_QUALITY = {
    'laghu': 'subha', 'sthira': 'subha', 'mridu': 'subha', 'chara': 'mixed',
    'mixed': 'mixed', 'ugra': 'asubha', 'tikshna': 'asubha'
}

# ── Yoga（27 瑜伽）────────────────────────────────────────────────────
YOGA_NAMES = [
    'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
    'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
    'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra',
    'Siddhi', 'Vyatipata', 'Variyana', 'Parigha', 'Shiva',
    'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
    'Aindra', 'Vaidhriti'
]
YOGA_QUALITY = {
    'Vishkambha': 'asubha', 'Priti': 'subha', 'Ayushman': 'subha',
    'Saubhagya': 'subha', 'Shobhana': 'subha', 'Atiganda': 'asubha',
    'Sukarma': 'subha', 'Dhriti': 'subha', 'Shula': 'asubha',
    'Ganda': 'asubha', 'Vriddhi': 'subha', 'Dhruva': 'subha',
    'Vyaghata': 'asubha', 'Harshana': 'subha', 'Vajra': 'asubha',
    'Siddhi': 'subha', 'Vyatipata': 'asubha', 'Variyana': 'subha',
    'Parigha': 'asubha', 'Shiva': 'subha', 'Siddha': 'subha',
    'Sadhya': 'subha', 'Shubha': 'subha', 'Shukla': 'subha',
    'Brahma': 'subha', 'Aindra': 'subha', 'Vaidhriti': 'asubha'
}

# ── Karana（11 迦那）────────────────────────────────────────────────
# 7 个 movable + 4 个 fixed
KARANA_NAMES = [
    'Bava', 'Balava', 'Kaulava', 'Taitila', 'Garija',
    'Vanija', 'Vishti',  # 7 movable（循环8次）
    'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna'  # 4 fixed
]
KARANA_QUALITY = {
    'Bava': 'subha', 'Balava': 'subha', 'Kaulava': 'subha',
    'Taitila': 'subha', 'Garija': 'subha', 'Vanija': 'subha',
    'Vishti': 'asubha',  # Bhadra（Vishti）最凶
    'Shakuni': 'mixed', 'Chatushpada': 'mixed',
    'Naga': 'asubha', 'Kimstughna': 'subha'
}


# ── 核心计算函数 ─────────────────────────────────────────────────────

def calc_tithi(sun_lon: float, moon_lon: float) -> Dict:
    """计算 Tithi（月相日）。
    
    sun_lon, moon_lon: 恒星黄经（Lahiri，0-360）
    返回: tithi_num(1-30), paksha, name, quality
    """
    diff = (moon_lon - sun_lon) % 360
    tithi_num = int(diff / 12) + 1  # 1-30
    if tithi_num > 30:
        tithi_num = 30

    paksha = 'Shukla' if tithi_num <= 15 else 'Krishna'
    tithi_in_paksha = tithi_num if tithi_num <= 15 else tithi_num - 15

    name = TITHI_NAMES[min(tithi_in_paksha, 15)]
    if tithi_num == 15:
        name = 'Purnima'
    elif tithi_num == 30:
        name = 'Amavasya'

    quality = TITHI_QUALITY.get(tithi_num, 'mixed')
    return {
        'tithi_num': tithi_num,
        'paksha': paksha,
        'tithi_in_paksha': tithi_in_paksha,
        'name': name,
        'full_name': f'{paksha} {name}',
        'quality': quality,
        'moon_sun_diff': round(diff, 2)
    }


def calc_nakshatra_from_lon(lon: float) -> Dict:
    """从黄经计算星宿。"""
    lon = lon % 360
    idx = int(lon / (360 / 27))
    pada = int((lon % (360 / 27)) / (360 / 108)) + 1
    name = NAKSHATRAS[idx]
    ntype = NAKSHATRA_TYPE.get(name, 'mixed')
    quality = NAKSHATRA_QUALITY.get(ntype, 'mixed')
    return {
        'nakshatra': name,
        'nakshatra_idx': idx,
        'pada': pada,
        'type': ntype,
        'quality': quality,
        'moon_lon': round(lon, 2)
    }


def calc_yoga(sun_lon: float, moon_lon: float) -> Dict:
    """计算 Yoga（日月之和的 27 分之一）。"""
    total = (sun_lon + moon_lon) % 360
    idx = int(total / (360 / 27))
    if idx >= 27:
        idx = 26
    name = YOGA_NAMES[idx]
    quality = YOGA_QUALITY.get(name, 'mixed')
    return {
        'yoga': name,
        'yoga_idx': idx,
        'quality': quality,
        'sun_moon_sum': round(total, 2)
    }


def calc_karana(sun_lon: float, moon_lon: float) -> Dict:
    """计算 Karana（半 Tithi）。
    
    Karana 序列：
    - Kimstughna（fixed, 只在 Krishna 30 Tithi 前半）
    - 7 movable karanas × 8 = 56
    - Shakuni/Chatushpada/Naga/Kimstughna（fixed, 只在最后）
    共 60 个 half-tithis
    """
    diff = (moon_lon - sun_lon) % 360
    half_tithi = diff / 6  # 0-60
    
    # Karana 编号（0-59）
    k_num = int(half_tithi)
    
    if k_num == 0:
        name = 'Kimstughna'  # Fixed, first half of Shukla 1
    elif 1 <= k_num <= 56:
        idx = (k_num - 1) % 7
        name = KARANA_NAMES[idx]
    elif k_num == 57:
        name = 'Shakuni'
    elif k_num == 58:
        name = 'Chatushpada'
    elif k_num == 59:
        name = 'Naga'
    else:
        name = 'Kimstughna'

    quality = KARANA_QUALITY.get(name, 'mixed')
    return {
        'karana': name,
        'karana_num': k_num,
        'quality': quality,
        'is_vishti': name == 'Vishti'  # Vishti = Bhadra，最凶
    }


def calc_vara(weekday: int) -> Dict:
    """计算 Vara（weekday: 0=Sun, 1=Mon, ..., 6=Sat）。"""
    info = VARA_LORDS.get(weekday % 7, ('Unknown', 'Unknown', 'mixed'))
    return {
        'vara': info[0],
        'vara_lord': info[1],
        'quality': info[2],
        'weekday_idx': weekday % 7
    }


def calc_hora(weekday: int, hour_from_sunrise: float) -> Dict:
    """计算当前 Hora（日出后的小时序号）。
    
    weekday: 0=Sun, ..., 6=Sat
    hour_from_sunrise: 从日出起算的小时数（浮点）
    """
    vara_lord = VARA_LORDS[weekday % 7][1]
    start_idx = VARA_START_IDX.get(vara_lord, 0)
    hora_offset = int(hour_from_sunrise) % 24
    hora_lord = HORA_ORDER[(start_idx + hora_offset) % 7]
    hora_quality = 'subha' if hora_lord in ('Jupiter', 'Venus', 'Mercury') else \
                   'mixed' if hora_lord == 'Moon' else 'asubha'
    return {
        'hora_lord': hora_lord,
        'hora_num': hora_offset + 1,
        'quality': hora_quality,
        'hora_from_sunrise': round(hour_from_sunrise, 2)
    }


def calc_abhijit_muhurta(sunrise_ut: Optional[float] = None,
                          sunset_ut: Optional[float] = None) -> Dict:
    """
    计算 Abhijit Muhurta（最吉祥的时刻，正午±24分钟）。
    
    Abhijit = 8/15 * daytime（从日出到日落的 8/15 处），持续约 48 分钟。
    注意：周三（Wednesday）Abhijit 不吉，应避免使用。
    
    参数为 JD UT（可选），缺省时给出相对说明。
    """
    result = {
        'description': 'Abhijit Muhurta 是一天中最吉祥的时段（正午前后各24分钟）',
        'rule': '日升到日落共15个 muhurta，第8个（中间）即 Abhijit',
        'duration_minutes': 48,
        'warning': '周三（Wednesday/Budha Vara）不宜使用 Abhijit',
    }
    if sunrise_ut is not None and sunset_ut is not None:
        day_dur = sunset_ut - sunrise_ut  # in JD (days)
        abhijit_start_jd = sunrise_ut + day_dur * (7 / 15)
        abhijit_end_jd = sunrise_ut + day_dur * (8 / 15)
        result['abhijit_start_jd'] = round(abhijit_start_jd, 6)
        result['abhijit_end_jd'] = round(abhijit_end_jd, 6)
        result['abhijit_start_offset_min'] = round(day_dur * (7 / 15) * 24 * 60, 1)
        result['abhijit_end_offset_min'] = round(day_dur * (8 / 15) * 24 * 60, 1)
    return result


def calc_panchanga(sun_lon: float, moon_lon: float, weekday: int,
                   hour_from_sunrise: float = 6.0) -> Dict:
    """
    计算 Panchanga 五要素（所有输入均为恒星坐标 Lahiri）。
    
    参数：
        sun_lon: 太阳恒星黄经
        moon_lon: 月亮恒星黄经
        weekday: 0=Sun, ..., 6=Sat
        hour_from_sunrise: 从日出起算的小时数（默认 6h，约正午）
    """
    tithi = calc_tithi(sun_lon, moon_lon)
    nakshatra = calc_nakshatra_from_lon(moon_lon)
    yoga = calc_yoga(sun_lon, moon_lon)
    karana = calc_karana(sun_lon, moon_lon)
    vara = calc_vara(weekday)
    hora = calc_hora(weekday, hour_from_sunrise)

    # 综合吉凶评分
    elements = [
        ('Tithi', tithi['quality']),
        ('Vara', vara['quality']),
        ('Nakshatra', nakshatra['quality']),
        ('Yoga', yoga['quality']),
        ('Karana', karana['quality']),
        ('Hora', hora['quality']),
    ]
    score_map = {'subha': 1.0, 'mixed': 0.5, 'asubha': 0.0}
    total_score = sum(score_map[q] for _, q in elements)
    max_score = len(elements)
    score_pct = total_score / max_score

    if score_pct >= 0.75:
        overall = '吉（Subha）'
    elif score_pct >= 0.5:
        overall = '中（Mixed）'
    else:
        overall = '凶（Asubha）'

    # 特殊凶时段检查
    warnings = []
    if karana['is_vishti']:
        warnings.append('⚠️ Vishti（Bhadra）时段——最凶，避免重要开始')
    if tithi['name'] == 'Amavasya':
        warnings.append('⚠️ Amavasya（新月）——不宜开始新事')
    if nakshatra['type'] == 'tikshna':
        warnings.append(f'⚠️ {nakshatra["nakshatra"]} 为 Tikshna（尖锐）星宿——不宜立约、开业')
    if yoga['quality'] == 'asubha':
        warnings.append(f'⚠️ {yoga["yoga"]} Yoga——不利时段')

    return {
        'tithi': tithi,
        'nakshatra': nakshatra,
        'yoga': yoga,
        'karana': karana,
        'vara': vara,
        'hora': hora,
        'overall_score': round(score_pct, 2),
        'overall_quality': overall,
        'warnings': warnings,
        'auspicious_count': sum(1 for _, q in elements if q == 'subha'),
        'total_elements': len(elements),
    }


# ── 活动适宜性规则库 ──────────────────────────────────────────────────

ACTIVITY_RULES = {
    'marriage': {
        'name': '婚礼（Vivaha）',
        'good_tithis': [2, 3, 5, 7, 10, 11, 12, 13, 15],  # 吉 Tithi
        'bad_tithis': [4, 8, 9, 14, 29, 30],
        'good_nakshatras': ['Rohini', 'Mrigashira', 'Magha', 'Uttara Phalguni',
                            'Hasta', 'Swati', 'Anuradha', 'Mula', 'Uttara Ashadha',
                            'Uttara Bhadrapada', 'Revati'],
        'bad_nakshatras': ['Bharani', 'Ardra', 'Ashlesha', 'Jyeshtha'],
        'good_varas': ['Monday', 'Wednesday', 'Friday', 'Thursday'],
        'bad_varas': ['Tuesday', 'Saturday'],
    },
    'business': {
        'name': '开业/签约（Vyapar）',
        'good_tithis': [2, 3, 5, 7, 10, 11, 12],
        'bad_tithis': [4, 8, 9, 14, 29, 30],
        'good_nakshatras': ['Ashwini', 'Rohini', 'Mrigashira', 'Punarvasu',
                            'Pushya', 'Hasta', 'Chitra', 'Swati', 'Anuradha',
                            'Shravana', 'Dhanishtha', 'Revati'],
        'bad_nakshatras': ['Bharani', 'Ardra', 'Ashlesha', 'Magha', 'Mula',
                           'Purva Ashadha', 'Purva Phalguni', 'Purva Bhadrapada'],
        'good_varas': ['Monday', 'Wednesday', 'Thursday', 'Friday'],
        'bad_varas': ['Tuesday', 'Saturday', 'Sunday'],
    },
    'travel': {
        'name': '出行（Yatra）',
        'good_tithis': [2, 3, 5, 7, 10, 12],
        'bad_tithis': [4, 8, 9, 14, 30],
        'good_nakshatras': ['Ashwini', 'Mrigashira', 'Punarvasu', 'Pushya',
                            'Hasta', 'Chitra', 'Swati', 'Shravana', 'Revati'],
        'bad_nakshatras': ['Bharani', 'Ardra', 'Ashlesha', 'Jyeshtha', 'Mula'],
        'good_varas': ['Monday', 'Wednesday', 'Thursday', 'Friday'],
        'bad_varas': ['Tuesday', 'Saturday'],
    },
    'medical': {
        'name': '手术/医疗（Chikitsa）',
        'good_tithis': [1, 2, 3, 5, 6, 7, 10, 11, 12],
        'bad_tithis': [8, 9, 13, 14, 30],
        'good_nakshatras': ['Ashwini', 'Mrigashira', 'Pushya', 'Hasta', 'Anuradha'],
        'bad_nakshatras': ['Ardra', 'Ashlesha', 'Jyeshtha', 'Mula', 'Vishakha'],
        'good_varas': ['Monday', 'Wednesday', 'Thursday'],
        'bad_varas': ['Tuesday', 'Saturday', 'Sunday'],
    },
    'education': {
        'name': '学习/入学（Vidyarambha）',
        'good_tithis': [2, 3, 5, 7, 10, 11, 12],
        'bad_tithis': [4, 6, 8, 9, 14, 29, 30],
        'good_nakshatras': ['Ashwini', 'Mrigashira', 'Punarvasu', 'Pushya',
                            'Hasta', 'Chitra', 'Swati', 'Shravana', 'Revati'],
        'bad_nakshatras': ['Bharani', 'Ardra', 'Ashlesha', 'Magha', 'Mula'],
        'good_varas': ['Monday', 'Wednesday', 'Thursday', 'Friday'],
        'bad_varas': ['Tuesday', 'Saturday'],
    }
}


def check_activity_muhurta(panchanga: Dict, activity: str) -> Dict:
    """
    检查给定 Panchanga 是否适合特定活动。
    
    activity: 'marriage', 'business', 'travel', 'medical', 'education'
    """
    rules = ACTIVITY_RULES.get(activity)
    if not rules:
        return {'error': f'未知活动类型: {activity}。支持: {list(ACTIVITY_RULES.keys())}'}

    tithi_num = panchanga['tithi']['tithi_num']
    nakshatra = panchanga['nakshatra']['nakshatra']
    vara = panchanga['vara']['vara']
    
    # Tithi 评估
    if tithi_num in rules['good_tithis']:
        tithi_score = 'good'
    elif tithi_num in rules['bad_tithis']:
        tithi_score = 'bad'
    else:
        tithi_score = 'neutral'

    # Nakshatra 评估
    if nakshatra in rules['good_nakshatras']:
        nakshatra_score = 'good'
    elif nakshatra in rules['bad_nakshatras']:
        nakshatra_score = 'bad'
    else:
        nakshatra_score = 'neutral'

    # Vara 评估
    if vara in rules['good_varas']:
        vara_score = 'good'
    elif vara in rules['bad_varas']:
        vara_score = 'bad'
    else:
        vara_score = 'neutral'

    scores = [tithi_score, nakshatra_score, vara_score]
    good_count = scores.count('good')
    bad_count = scores.count('bad')

    if bad_count >= 2:
        verdict = '不宜（Avoid）'
    elif good_count >= 2 and bad_count == 0:
        verdict = '大吉（Excellent）'
    elif good_count >= 1 and bad_count == 0:
        verdict = '吉（Good）'
    elif bad_count == 1 and good_count >= 1:
        verdict = '一般（Fair）'
    else:
        verdict = '中（Neutral）'

    return {
        'activity': rules['name'],
        'tithi_eval': tithi_score,
        'nakshatra_eval': nakshatra_score,
        'vara_eval': vara_score,
        'verdict': verdict,
        'good_count': good_count,
        'bad_count': bad_count,
        'notes': _get_activity_notes(rules, tithi_num, nakshatra, vara)
    }


def _get_activity_notes(rules: Dict, tithi_num: int,
                        nakshatra: str, vara: str) -> List[str]:
    notes = []
    if tithi_num in rules['bad_tithis']:
        notes.append(f'Tithi {tithi_num} 不宜此类活动')
    if nakshatra in rules['bad_nakshatras']:
        notes.append(f'{nakshatra} 星宿不利此类活动')
    if vara in rules['bad_varas']:
        notes.append(f'{vara} 不利此类活动')
    if tithi_num in rules['good_tithis']:
        notes.append(f'Tithi {tithi_num} 有利此类活动')
    if nakshatra in rules['good_nakshatras']:
        notes.append(f'{nakshatra} 星宿适合此类活动')
    if vara in rules['good_varas']:
        notes.append(f'{vara} 有利此类活动')
    return notes


# ── 完整报告函数 ──────────────────────────────────────────────────────

def muhurta_full_report(
    sun_lon: float,
    moon_lon: float,
    weekday: int,
    hour_from_sunrise: float = 6.0,
    query_date_str: Optional[str] = None,
    activities: Optional[List[str]] = None,
) -> Dict:
    """
    生成完整 Muhurta 报告。
    
    参数：
        sun_lon: 太阳恒星黄经（Lahiri，0-360）
        moon_lon: 月亮恒星黄经（Lahiri，0-360）
        weekday: 0=Sun, ..., 6=Sat
        hour_from_sunrise: 从日出起算的小时（默认 6h = 约正午）
        query_date_str: 查询日期字符串（用于展示）
        activities: 要检查的活动列表（默认检查所有）
    """
    panchanga = calc_panchanga(sun_lon, moon_lon, weekday, hour_from_sunrise)
    abhijit = calc_abhijit_muhurta()

    if activities is None:
        activities = list(ACTIVITY_RULES.keys())

    activity_checks = {}
    for act in activities:
        activity_checks[act] = check_activity_muhurta(panchanga, act)

    return {
        'query_date': query_date_str or 'unknown',
        'panchanga': panchanga,
        'abhijit_muhurta': abhijit,
        'activity_checks': activity_checks,
        'summary': {
            'overall_quality': panchanga['overall_quality'],
            'overall_score': panchanga['overall_score'],
            'auspicious_elements': panchanga['auspicious_count'],
            'warnings': panchanga['warnings'],
            'best_activities': [
                act for act, chk in activity_checks.items()
                if '吉' in chk.get('verdict', '') or 'Good' in chk.get('verdict', '')
            ],
            'avoid_activities': [
                act for act, chk in activity_checks.items()
                if '不宜' in chk.get('verdict', '') or 'Avoid' in chk.get('verdict', '')
            ]
        }
    }


# ── 近似测试函数 ──────────────────────────────────────────────────────

def _approx_sun_moon_lon(year: int, month: int, day: int) -> Tuple[float, float]:
    """
    近似计算太阳/月亮恒星黄经（无 swisseph，精度约 ±2°）。
    仅用于测试和展示，不用于精确解盘。
    Lahiri Ayanamsa ≈ 23.85°（2026年）
    """
    # J2000.0 起的天数
    import math
    jd = 367 * year - int(7 * (year + int((month + 9) / 12)) / 4) + int(275 * month / 9) + day + 1721013.5
    d = jd - 2451545.0  # days since J2000.0

    # 太阳黄经（热带）
    M_sun = math.radians(357.5291 + 0.98560028 * d)
    L_sun = 280.4665 + 0.98564736 * d + 1.9146 * math.sin(M_sun)
    L_sun = L_sun % 360

    # 月亮黄经（热带，简化）
    L_moon = (218.3165 + 13.175396 * d) % 360
    M_moon = math.radians(134.9634 + 13.064993 * d)
    L_moon = (L_moon + 6.2886 * math.sin(M_moon)) % 360

    # 转为恒星（减去 Lahiri Ayanamsa ≈ 23.85°，2026年）
    ayanamsa = 23.85
    sun_sid = (L_sun - ayanamsa) % 360
    moon_sid = (L_moon - ayanamsa) % 360

    return sun_sid, moon_sid


if __name__ == '__main__':
    import json
    # 测试：2026-06-04 (Wednesday)
    y, m, d = 2026, 6, 4
    sun_lon, moon_lon = _approx_sun_moon_lon(y, m, d)
    wd = datetime(y, m, d).weekday()  # 0=Mon in Python → convert
    # Python weekday: 0=Mon, but our VARA_LORDS: 0=Sun
    # June 4 2026 = Wednesday = Python 2
    vara_idx = (wd + 1) % 7  # convert Python weekday to Vara (Sun=0)

    print(f"=== Muhurta 测试 {y}-{m:02d}-{d:02d} ===")
    print(f"Sun lon (approx): {sun_lon:.2f}°  Moon lon (approx): {moon_lon:.2f}°")
    print(f"Vara index: {vara_idx} ({VARA_LORDS[vara_idx][0]})")
    print()

    result = muhurta_full_report(
        sun_lon, moon_lon, vara_idx,
        hour_from_sunrise=6.0,
        query_date_str=f'{y}-{m:02d}-{d:02d}',
    )

    p = result['panchanga']
    print(f"Tithi: {p['tithi']['full_name']} ({p['tithi']['quality']})")
    print(f"Nakshatra: {p['nakshatra']['nakshatra']} ({p['nakshatra']['quality']})")
    print(f"Yoga: {p['yoga']['yoga']} ({p['yoga']['quality']})")
    print(f"Karana: {p['karana']['karana']} ({p['karana']['quality']})")
    print(f"Vara: {p['vara']['vara']} ({p['vara']['quality']})")
    print(f"Hora: {p['hora']['hora_lord']} ({p['hora']['quality']})")
    print()
    print(f"综合评分: {result['summary']['overall_quality']} ({result['summary']['overall_score']:.0%})")
    print(f"警告: {result['summary']['warnings']}")
    print()
    print("活动适宜性:")
    for act, chk in result['activity_checks'].items():
        print(f"  {act}: {chk['verdict']}")
