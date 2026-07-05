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
import calendar
import math

from ayanamsa_utils import sidereal_flags

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

RAHU_KALA_SEGMENTS = {
    0: 8,  # Sunday
    1: 2,  # Monday
    2: 7,  # Tuesday
    3: 5,  # Wednesday
    4: 6,  # Thursday
    5: 4,  # Friday
    6: 3,  # Saturday
}
YAMAGANDA_SEGMENTS = {
    0: 5,
    1: 4,
    2: 3,
    3: 2,
    4: 1,
    5: 7,
    6: 6,
}
GULIKA_SEGMENTS = {
    0: 7,
    1: 6,
    2: 5,
    3: 4,
    4: 3,
    5: 2,
    6: 1,
}

TITHI_BOUNDARY_DEGREES = 12.0
NAKSHATRA_BOUNDARY_DEGREES = 360.0 / 27.0
YOGA_BOUNDARY_DEGREES = 360.0 / 27.0

CHOGHADIYA_DAY_SEQUENCE = {
    0: ['Udveg', 'Chal', 'Labh', 'Amrit', 'Kal', 'Shubh', 'Rog', 'Udveg'],
    1: ['Amrit', 'Kal', 'Shubh', 'Rog', 'Udveg', 'Chal', 'Labh', 'Amrit'],
    2: ['Rog', 'Udveg', 'Chal', 'Labh', 'Amrit', 'Kal', 'Shubh', 'Rog'],
    3: ['Labh', 'Amrit', 'Kal', 'Shubh', 'Rog', 'Udveg', 'Chal', 'Labh'],
    4: ['Shubh', 'Rog', 'Udveg', 'Chal', 'Labh', 'Amrit', 'Kal', 'Shubh'],
    5: ['Chal', 'Labh', 'Amrit', 'Kal', 'Shubh', 'Rog', 'Udveg', 'Chal'],
    6: ['Kal', 'Shubh', 'Rog', 'Udveg', 'Chal', 'Labh', 'Amrit', 'Kal'],
}
CHOGHADIYA_NIGHT_SEQUENCE = {
    0: ['Shubh', 'Amrit', 'Chal', 'Rog', 'Kal', 'Labh', 'Udveg', 'Shubh'],
    1: ['Chal', 'Rog', 'Kal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Chal'],
    2: ['Kal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Chal', 'Rog', 'Kal'],
    3: ['Udveg', 'Shubh', 'Amrit', 'Chal', 'Rog', 'Kal', 'Labh', 'Udveg'],
    4: ['Amrit', 'Chal', 'Rog', 'Kal', 'Labh', 'Udveg', 'Shubh', 'Amrit'],
    5: ['Rog', 'Kal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Chal', 'Rog'],
    6: ['Labh', 'Udveg', 'Shubh', 'Amrit', 'Chal', 'Rog', 'Kal', 'Labh'],
}
CHOGHADIYA_QUALITY = {
    'Amrit': 'auspicious',
    'Shubh': 'auspicious',
    'Labh': 'auspicious',
    'Chal': 'usable',
    'Udveg': 'inauspicious',
    'Kal': 'inauspicious',
    'Rog': 'inauspicious',
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


def _parse_hhmm(value: str, default: str) -> Tuple[int, int]:
    if not value:
        value = default
    try:
        hour_str, minute_str = value.split(':', 1)
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError) as exc:
        raise ValueError('time must be HH:MM') from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError('time must be HH:MM')
    return hour, minute


def _minutes_to_hhmm(minutes: float) -> str:
    total = int(round(minutes)) % (24 * 60)
    return f'{total // 60:02d}:{total % 60:02d}'


def _segment_window(segment: int, sunrise_min: int, sunset_min: int) -> Dict:
    day_duration = sunset_min - sunrise_min
    if day_duration <= 0:
        day_duration += 24 * 60
    segment_len = day_duration / 8.0
    start = sunrise_min + (segment - 1) * segment_len
    end = start + segment_len
    return {
        'segment': segment,
        'start': _minutes_to_hhmm(start),
        'end': _minutes_to_hhmm(end),
        'duration_minutes': round(segment_len, 1),
    }


def _clock_minutes(value: str, default: str) -> int:
    hour, minute = _parse_hhmm(value, default)
    return hour * 60 + minute


def _window_from_minutes(start_min: float, end_min: float) -> Dict:
    return {
        'start': _minutes_to_hhmm(start_min),
        'end': _minutes_to_hhmm(end_min),
        'duration_minutes': round(end_min - start_min, 1),
    }


def _split_window(start_min: float, end_min: float, parts: int) -> List[Tuple[float, float]]:
    duration = end_min - start_min
    if duration <= 0:
        duration += 24 * 60
    step = duration / parts
    return [(start_min + idx * step, start_min + (idx + 1) * step) for idx in range(parts)]


def _solar_event_utc_hours(year: int, month: int, day: int, lat: float, lon: float, event: str) -> float:
    """Approximate sunrise/sunset UTC decimal hours using the Jaimini helper model."""
    jd = 367 * year - int(7 * (year + int((month + 9) / 12)) / 4) + int(275 * month / 9) + day + 1721013.5
    d = jd - 2451545.0
    mean_anomaly = (357.5291 + 0.98560028 * d) % 360
    center = (
        1.9148 * math.sin(math.radians(mean_anomaly))
        + 0.0200 * math.sin(math.radians(2 * mean_anomaly))
        + 0.0003 * math.sin(math.radians(3 * mean_anomaly))
    )
    sun_lon = (mean_anomaly + center + 180.10248 + 0.000048 * d * 360) % 360
    t = d / 36525.0
    eps0 = 84381.448 - 46.8150 * t - 0.00059 * t * t + 0.001813 * t * t * t
    eps = eps0 / 3600.0
    declination = math.degrees(
        math.asin(math.sin(math.radians(sun_lon)) * math.sin(math.radians(eps)))
    )
    lat_rad = math.radians(lat)
    dec_rad = math.radians(declination)
    denom = math.cos(lat_rad) * math.cos(dec_rad)
    if abs(denom) < 1e-9:
        raise ValueError('sunrise/sunset undefined near pole for this date')
    cos_ha = (
        math.cos(math.radians(90.833))
        - math.sin(lat_rad) * math.sin(dec_rad)
    ) / denom
    cos_ha = max(-1.0, min(1.0, cos_ha))
    hour_angle = math.degrees(math.acos(cos_ha))
    b = math.radians(360.0 * (d - 0.5) / 365.25)
    eq_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(b)
        - 0.032077 * math.sin(b)
        - 0.014615 * math.cos(2 * b)
        - 0.040849 * math.sin(2 * b)
    )
    solar_noon = (720.0 - 4.0 * lon - eq_time) / 60.0
    if event == 'sunrise':
        return (solar_noon - hour_angle / 15.0) % 24.0
    if event == 'sunset':
        return (solar_noon + hour_angle / 15.0) % 24.0
    raise ValueError('event must be sunrise or sunset')


def _local_hours_from_jd(event_jd: float, local_midnight_jd: float) -> float:
    return (event_jd - local_midnight_jd) * 24.0


def _swisseph_solar_times_local(
    year: int,
    month: int,
    day: int,
    lat: float,
    lon: float,
    tz: float,
) -> Optional[Dict]:
    """Return precise local sunrise/sunset via pyswisseph when available."""
    try:
        import swisseph as swe
    except Exception:
        return None

    try:
        local_midnight_jd = swe.julday(year, month, day, -tz)
        geopos = (lon, lat, 0.0)
        flags = getattr(swe, 'FLG_SWIEPH', 2)
        rise_res, rise_tret = swe.rise_trans(local_midnight_jd, swe.SUN, swe.CALC_RISE, geopos, flags=flags)
        set_res, set_tret = swe.rise_trans(local_midnight_jd, swe.SUN, swe.CALC_SET, geopos, flags=flags)
    except Exception:
        return None

    if rise_res != 0 or set_res != 0:
        return None

    sunrise_local = _local_hours_from_jd(rise_tret[0], local_midnight_jd)
    sunset_local = _local_hours_from_jd(set_tret[0], local_midnight_jd)
    if not (0.0 <= sunrise_local < 24.0 and 0.0 <= sunset_local < 24.0):
        return None
    sunrise_utc = (sunrise_local - tz) % 24.0
    sunset_utc = (sunset_local - tz) % 24.0
    return {
        'policy': 'swisseph_rise_trans',
        'lat': round(lat, 5),
        'lon': round(lon, 5),
        'tz': tz,
        'sunrise': _minutes_to_hhmm(sunrise_local * 60),
        'sunset': _minutes_to_hhmm(sunset_local * 60),
        'sunrise_local_hours': round(sunrise_local, 4),
        'sunset_local_hours': round(sunset_local, 4),
        'sunrise_utc_hours': round(sunrise_utc, 4),
        'sunset_utc_hours': round(sunset_utc, 4),
    }


def calc_sunrise_sunset_local(
    year: int,
    month: int,
    day: int,
    lat: float,
    lon: float,
    tz: float,
) -> Dict:
    """Local sunrise/sunset HH:MM for a date and location, precise when SwissEph is available."""
    swisseph_result = _swisseph_solar_times_local(year, month, day, lat, lon, tz)
    if swisseph_result:
        return swisseph_result

    sunrise_utc = _solar_event_utc_hours(year, month, day, lat, lon, 'sunrise')
    sunset_utc = _solar_event_utc_hours(year, month, day, lat, lon, 'sunset')
    sunrise_local = (sunrise_utc + tz) % 24.0
    sunset_local = (sunset_utc + tz) % 24.0
    return {
        'policy': 'location_aware_solar_event_approximation',
        'lat': round(lat, 5),
        'lon': round(lon, 5),
        'tz': tz,
        'sunrise': _minutes_to_hhmm(sunrise_local * 60),
        'sunset': _minutes_to_hhmm(sunset_local * 60),
        'sunrise_utc_hours': round(sunrise_utc, 4),
        'sunset_utc_hours': round(sunset_utc, 4),
    }


def calc_choghadiya_windows(
    weekday: int,
    sunrise: str = '06:00',
    sunset: str = '18:00',
) -> Dict:
    """Calculate day and night Choghadiya windows from sunrise/sunset."""
    sunrise_min = _clock_minutes(sunrise, '06:00')
    sunset_min = _clock_minutes(sunset, '18:00')
    next_sunrise_min = sunrise_min + 24 * 60
    day_sequence = CHOGHADIYA_DAY_SEQUENCE[weekday % 7]
    night_sequence = CHOGHADIYA_NIGHT_SEQUENCE[weekday % 7]

    def build_rows(sequence: List[str], windows: List[Tuple[float, float]]) -> List[Dict]:
        return [
            {
                'index': idx + 1,
                'name': name,
                'quality': CHOGHADIYA_QUALITY.get(name, 'mixed'),
                **_window_from_minutes(start, end),
            }
            for idx, (name, (start, end)) in enumerate(zip(sequence, windows))
        ]

    return {
        'policy': 'traditional_day_night_8_choghadiya_segments',
        'day': build_rows(day_sequence, _split_window(sunrise_min, sunset_min, 8)),
        'night': build_rows(night_sequence, _split_window(sunset_min, next_sunrise_min, 8)),
    }


def calc_hora_windows(
    weekday: int,
    sunrise: str = '06:00',
    sunset: str = '18:00',
) -> Dict:
    """Calculate planetary Hora windows for daytime and nighttime."""
    sunrise_min = _clock_minutes(sunrise, '06:00')
    sunset_min = _clock_minutes(sunset, '18:00')
    next_sunrise_min = sunrise_min + 24 * 60
    vara_lord = VARA_LORDS[weekday % 7][1]
    start_idx = VARA_START_IDX.get(vara_lord, 0)

    def lord_for(offset: int) -> str:
        return HORA_ORDER[(start_idx + offset) % len(HORA_ORDER)]

    return {
        'policy': 'planetary_hora_day_night_12_segments',
        'day': [
            {'index': idx + 1, 'lord': lord_for(idx), **_window_from_minutes(start, end)}
            for idx, (start, end) in enumerate(_split_window(sunrise_min, sunset_min, 12))
        ],
        'night': [
            {'index': idx + 13, 'lord': lord_for(idx + 12), **_window_from_minutes(start, end)}
            for idx, (start, end) in enumerate(_split_window(sunset_min, next_sunrise_min, 12))
        ],
    }


def _jd_for_local_time(year: int, month: int, day: int, local_hours: float, tz: float) -> Optional[float]:
    try:
        import swisseph as swe
        return swe.julday(year, month, day, local_hours - tz)
    except Exception:
        return None


def _local_time_from_jd(jd: float, tz: float) -> str:
    local_dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451544.5, hours=tz)
    return local_dt.strftime('%Y-%m-%d %H:%M')


def _swisseph_sun_moon_lon(jd: float, ayanamsa_name: str = 'lahiri') -> Optional[Tuple[float, float]]:
    try:
        import swisseph as swe
        flags = sidereal_flags(swe, ayanamsa_name)
        sun = swe.calc_ut(jd, swe.SUN, flags)[0][0] % 360
        moon = swe.calc_ut(jd, swe.MOON, flags)[0][0] % 360
        return sun, moon
    except Exception:
        return None


def _find_next_boundary(
    jd_start: float,
    value_func,
    boundary_size: float,
    max_days: float,
    samples: int = 96,
) -> Optional[float]:
    start_value = value_func(jd_start)
    if start_value is None:
        return None
    current_slot = int(start_value / boundary_size)
    previous_jd = jd_start
    previous_value = start_value
    step = max_days / samples
    for idx in range(1, samples + 1):
        candidate_jd = jd_start + step * idx
        candidate_value = value_func(candidate_jd)
        if candidate_value is None:
            return None
        if int(candidate_value / boundary_size) != current_slot or candidate_value < previous_value:
            low = previous_jd
            high = candidate_jd
            for _ in range(32):
                mid = (low + high) / 2
                mid_value = value_func(mid)
                if mid_value is None:
                    return None
                if int(mid_value / boundary_size) == current_slot and mid_value >= start_value:
                    low = mid
                else:
                    high = mid
            return high
        previous_jd = candidate_jd
        previous_value = candidate_value
    return None


def calc_panchanga_end_times(
    year: int,
    month: int,
    day: int,
    tz: float,
    local_hours: float,
    ayanamsa_name: str = 'lahiri',
) -> Optional[Dict]:
    """Calculate current Tithi/Nakshatra/Yoga end times from SwissEph positions."""
    jd_start = _jd_for_local_time(year, month, day, local_hours, tz)
    if jd_start is None:
        return None

    def tithi_value(jd: float) -> Optional[float]:
        positions = _swisseph_sun_moon_lon(jd, ayanamsa_name=ayanamsa_name)
        if not positions:
            return None
        sun, moon = positions
        return (moon - sun) % 360

    def nakshatra_value(jd: float) -> Optional[float]:
        positions = _swisseph_sun_moon_lon(jd, ayanamsa_name=ayanamsa_name)
        if not positions:
            return None
        return positions[1] % 360

    def yoga_value(jd: float) -> Optional[float]:
        positions = _swisseph_sun_moon_lon(jd, ayanamsa_name=ayanamsa_name)
        if not positions:
            return None
        sun, moon = positions
        return (sun + moon) % 360

    boundaries = {
        'tithi': _find_next_boundary(jd_start, tithi_value, TITHI_BOUNDARY_DEGREES, 1.6),
        'nakshatra': _find_next_boundary(jd_start, nakshatra_value, NAKSHATRA_BOUNDARY_DEGREES, 1.4),
        'yoga': _find_next_boundary(jd_start, yoga_value, YOGA_BOUNDARY_DEGREES, 1.4),
    }
    result = {'policy': 'swisseph_boundary_bisection', 'reference_local_time': _local_time_from_jd(jd_start, tz)}
    for key, boundary_jd in boundaries.items():
        if boundary_jd is None:
            continue
        result[key] = {
            'ends_at': _local_time_from_jd(boundary_jd, tz),
            'hours_from_reference': round((boundary_jd - jd_start) * 24.0, 2),
        }
    return result


def _normalize_name(value: object) -> str:
    return str(value or '').strip()


def _push_tag(tags: List[Dict], key: str, label: str, tag_type: str, guidance: str) -> None:
    if any(tag.get('key') == key for tag in tags):
        return
    tags.append({
        'key': key,
        'label': label,
        'type': tag_type,
        'guidance': guidance,
    })


def classify_vrata_tags(
    tithi: Dict,
    nakshatra: Optional[Dict] = None,
    vara: Optional[Dict] = None,
) -> List[Dict]:
    """Classify conservative vrata/festival observance tags from Panchanga limbs.

    Precise named festivals often require lunar month/masa and local sunrise rules.
    Tags that cannot be confirmed from the current data are explicitly marked as
    candidates so the UI can guide users without overstating precision.
    """
    tithi_num = int(tithi.get('tithi_num') or 0)
    paksha = _normalize_name(tithi.get('paksha'))
    name = _normalize_name(tithi.get('name'))
    nak_name = _normalize_name((nakshatra or {}).get('nakshatra') or (nakshatra or {}).get('name'))
    vara_name = _normalize_name((vara or {}).get('vara') or (vara or {}).get('name'))
    tags = []
    if tithi_num in (11, 26):
        _push_tag(
            tags,
            'ekadashi',
            f'{paksha} Ekadashi'.strip(),
            'fasting',
            'Commonly observed as a fasting and spiritual practice day.',
        )
    if tithi_num in (13, 28):
        pradosham_label = f'{paksha} Pradosham'.strip()
        if vara_name == 'Monday':
            pradosham_label = f'Soma {pradosham_label}'
        elif vara_name == 'Saturday':
            pradosham_label = f'Shani {pradosham_label}'
        _push_tag(
            tags,
            'pradosham',
            pradosham_label,
            'observance',
            'Pradosham is traditionally associated with Shiva worship near dusk.',
        )
    if tithi_num == 15 or name == 'Purnima':
        _push_tag(
            tags,
            'purnima',
            'Purnima',
            'lunar',
            'Full moon observance; often used for vrata, puja and spiritual practices.',
        )
    if tithi_num == 30 or name == 'Amavasya':
        _push_tag(
            tags,
            'amavasya',
            'Amavasya',
            'lunar',
            'New moon observance; often used for ancestral rites and inward practice.',
        )
    if tithi_num in (4, 19):
        _push_tag(
            tags,
            'chaturthi_vrata',
            f'{paksha} Chaturthi'.strip(),
            'vrata',
            'Chaturthi is commonly associated with Ganapati observances; confirm local sunrise rule for exact vrata.',
        )
    if tithi_num in (6, 21):
        _push_tag(
            tags,
            'shashthi_vrata',
            f'{paksha} Shashthi'.strip(),
            'vrata',
            'Shashthi is used for Skanda/Subrahmanya observances in many Panchanga traditions.',
        )
    if tithi_num in (8, 23):
        _push_tag(
            tags,
            'ashtami_vrata',
            f'{paksha} Ashtami'.strip(),
            'vrata',
            'Ashtami is a common vrata and Devi/Krishna observance marker; festival name depends on lunar month.',
        )
    if tithi_num in (9, 24):
        _push_tag(
            tags,
            'navami_observance',
            f'{paksha} Navami'.strip(),
            'observance',
            'Navami can become a major festival marker in the right lunar month; treat as a condition for deeper lookup.',
        )
    if tithi_num == 3 and paksha == 'Shukla':
        _push_tag(
            tags,
            'akshaya_tritiya_candidate',
            'Shukla Tritiya festival candidate',
            'festival_candidate',
            'May indicate Akshaya Tritiya only when the lunar month is Vaishakha; confirm masa before final reporting.',
        )
    if tithi_num == 29 and paksha == 'Krishna':
        _push_tag(
            tags,
            'shivaratri_candidate',
            'Krishna Chaturdashi/Shivaratri candidate',
            'festival_candidate',
            'Monthly Shivaratri marker; Maha Shivaratri requires Phalguna/Magha month confirmation by tradition.',
        )
    if nak_name == 'Pushya':
        _push_tag(
            tags,
            'pushya_nakshatra',
            'Pushya Nakshatra',
            'nakshatra',
            'Pushya is widely treated as a strong auspicious nakshatra for learning, purchases and counsel.',
        )
        if vara_name == 'Thursday':
            _push_tag(
                tags,
                'guru_pushya',
                'Guru Pushya Yoga',
                'festival_window',
                'Thursday plus Pushya is treated as a highly auspicious purchase/initiation window.',
            )
        if vara_name == 'Sunday':
            _push_tag(
                tags,
                'ravi_pushya',
                'Ravi Pushya Yoga',
                'festival_window',
                'Sunday plus Pushya is a favored window for acquisition and auspicious beginnings.',
            )
    if nak_name == 'Rohini':
        _push_tag(
            tags,
            'rohini_nakshatra',
            'Rohini Nakshatra',
            'nakshatra',
            'Rohini is a fixed, growth-oriented nakshatra often used for stable starts.',
        )
    return tags


def classify_panchanga_condition_tags(report: Dict, activity: Optional[str] = None) -> List[Dict]:
    """Return searchable product tags for Panchanga calendar rows."""
    panchanga = report.get('panchanga') or {}
    summary = report.get('summary') or {}
    warnings = summary.get('warnings') or panchanga.get('warnings') or []
    vrata_tags = report.get('vrata_tags') or []
    checks = report.get('activity_checks') or {}
    choghadiya = report.get('choghadiya') or {}
    tags: List[Dict] = []

    def add(key: str, label: str, guidance: str = '') -> None:
        _push_tag(tags, key, label, 'condition', guidance)

    if vrata_tags:
        add('has_vrata', 'Vrata/observance day', 'At least one vrata, lunar observance or festival-candidate tag is present.')
    if any(tag.get('type') == 'festival_candidate' for tag in vrata_tags):
        add('festival_candidate', 'Festival candidate', 'Needs lunar month or tradition-specific confirmation before final naming.')
    if any(tag.get('type') in {'fasting', 'observance', 'lunar', 'vrata'} for tag in vrata_tags):
        add('spiritual_practice', 'Spiritual practice day', 'Useful for fasting, puja, mantra, vrata or inward observance.')
    if summary.get('best_activities'):
        add('auspicious_activity', 'Auspicious for selected/common activity', 'At least one activity check is favorable.')
    if summary.get('avoid_activities') or warnings:
        add('avoid_new_start', 'Avoid important new starts', 'One or more Panchanga factors or activity checks advise caution.')
    if any(item.get('quality') == 'auspicious' for segment in ('day', 'night') for item in choghadiya.get(segment, []) or []):
        add('good_choghadiya', 'Has auspicious Choghadiya window', 'At least one Amrit/Shubh/Labh Choghadiya window is available.')
    if activity and activity in checks:
        verdict = checks[activity].get('verdict', '')
        if '不宜' in verdict or 'Avoid' in verdict:
            add('selected_activity_avoid', 'Selected activity should be avoided', 'The chosen activity has a negative Panchanga verdict.')
        elif '吉' in verdict or 'Good' in verdict or 'Excellent' in verdict:
            add('selected_activity_good', 'Selected activity is favorable', 'The chosen activity has a favorable Panchanga verdict.')
    return tags


def build_festival_details(report: Dict) -> List[Dict]:
    """Build user-facing explanations for vrata and festival candidate tags."""
    panchanga = report.get('panchanga') or {}
    tithi = panchanga.get('tithi') or {}
    nakshatra = panchanga.get('nakshatra') or {}
    vara = panchanga.get('vara') or {}
    details = []
    for tag in report.get('vrata_tags') or []:
        detail_type = tag.get('type') or 'observance'
        requires_confirmation = detail_type == 'festival_candidate'
        details.append({
            'key': tag.get('key'),
            'label': tag.get('label') or tag.get('key'),
            'type': detail_type,
            'guidance': tag.get('guidance') or '',
            'basis': [
                f"Tithi: {tithi.get('full_name') or tithi.get('name') or '-'}",
                f"Nakshatra: {nakshatra.get('nakshatra') or nakshatra.get('name') or '-'}",
                f"Vara: {vara.get('vara') or vara.get('name') or '-'}",
            ],
            'requires_confirmation': requires_confirmation,
            'confirmation_note': (
                'Needs lunar masa, local sunrise observance rule and tradition-specific calendar confirmation.'
                if requires_confirmation else
                'Conservative Panchanga tag derived from tithi/nakshatra/vara; confirm local tradition for formal observance.'
            ),
        })
    return details


def build_panchanga_search_summary(rows: List[Dict], activity: Optional[str] = None) -> Dict:
    """Summarize searchable Panchanga conditions for same-category calendar UX."""
    condition_counts: Dict[str, int] = {}
    festival_candidates = []
    spiritual_days = []
    good_activity_days = []
    caution_days = []
    for row in rows:
        date = row.get('query_date')
        for tag in row.get('condition_tags') or []:
            key = tag.get('key')
            if key:
                condition_counts[key] = condition_counts.get(key, 0) + 1
        if any(tag.get('type') == 'festival_candidate' for tag in row.get('vrata_tags') or []):
            festival_candidates.append(date)
        if any(tag.get('key') == 'spiritual_practice' for tag in row.get('condition_tags') or []):
            spiritual_days.append(date)
        if any(tag.get('key') in {'auspicious_activity', 'selected_activity_good'} for tag in row.get('condition_tags') or []):
            good_activity_days.append(date)
        if any(tag.get('key') in {'avoid_new_start', 'selected_activity_avoid'} for tag in row.get('condition_tags') or []):
            caution_days.append(date)
    return {
        'mode': 'range_condition_index',
        'activity': activity or 'all',
        'condition_counts': condition_counts,
        'festival_candidate_dates': festival_candidates,
        'spiritual_practice_dates': spiritual_days,
        'auspicious_activity_dates': good_activity_days,
        'avoid_new_start_dates': caution_days,
        'query_examples': [
            'festival_candidate + spiritual_practice',
            'auspicious_activity + good_choghadiya',
            'avoid_new_start',
        ],
    }


def build_panchanga_month_grid(rows: List[Dict], start_dt: datetime, end_dt: datetime) -> List[List[Optional[Dict]]]:
    """Build calendar-week rows for single-month ranges, leaving blanks outside the selected month."""
    if start_dt.year != end_dt.year or start_dt.month != end_dt.month:
        return []

    by_date = {row.get('query_date'): row for row in rows}
    weeks = []
    for week in calendar.Calendar(firstweekday=6).monthdatescalendar(start_dt.year, start_dt.month):
        week_cells = []
        for current in week:
            if current.month != start_dt.month:
                week_cells.append(None)
                continue
            row = by_date.get(current.strftime('%Y-%m-%d'))
            if not row:
                week_cells.append(None)
                continue
            panchanga = row.get('panchanga') or {}
            periods = row.get('inauspicious_periods') or {}
            end_times = row.get('end_times') or {}
            week_cells.append({
                'date': row.get('query_date'),
                'day': current.day,
                'quality': (row.get('summary') or {}).get('overall_quality') or panchanga.get('overall_quality'),
                'score': (row.get('summary') or {}).get('overall_score', panchanga.get('overall_score')),
                'tithi': (panchanga.get('tithi') or {}).get('full_name') or (panchanga.get('tithi') or {}).get('name'),
                'nakshatra': (panchanga.get('nakshatra') or {}).get('nakshatra') or (panchanga.get('nakshatra') or {}).get('name'),
                'yoga': (panchanga.get('yoga') or {}).get('yoga') or (panchanga.get('yoga') or {}).get('name'),
                'best_activities': (row.get('summary') or {}).get('best_activities') or [],
                'avoid_activities': (row.get('summary') or {}).get('avoid_activities') or [],
                'vrata_tags': row.get('vrata_tags') or [],
                'condition_tags': row.get('condition_tags') or [],
                'tithi_ends_at': (end_times.get('tithi') or {}).get('ends_at'),
                'nakshatra_ends_at': (end_times.get('nakshatra') or {}).get('ends_at'),
                'best_choghadiya': [
                    item for item in ((row.get('choghadiya') or {}).get('day') or [])
                    if item.get('quality') == 'auspicious'
                ][:2],
                'sunrise': periods.get('sunrise'),
                'sunset': periods.get('sunset'),
            })
        weeks.append(week_cells)
    return weeks


def calc_daytime_inauspicious_periods(
    weekday: int,
    sunrise: str = '06:00',
    sunset: str = '18:00',
) -> Dict:
    """
    Calculate daytime Rahu Kala, Yamaganda and Gulika using the traditional
    eight-part daytime division. Times are local clock HH:MM values.
    """
    sunrise_h, sunrise_m = _parse_hhmm(sunrise, '06:00')
    sunset_h, sunset_m = _parse_hhmm(sunset, '18:00')
    sunrise_min = sunrise_h * 60 + sunrise_m
    sunset_min = sunset_h * 60 + sunset_m
    weekday = weekday % 7
    return {
        'policy': 'daytime_8_segments_local_clock',
        'sunrise': f'{sunrise_h:02d}:{sunrise_m:02d}',
        'sunset': f'{sunset_h:02d}:{sunset_m:02d}',
        'rahu_kala': {
            **_segment_window(RAHU_KALA_SEGMENTS[weekday], sunrise_min, sunset_min),
            'label': 'Rahu Kala',
            'guidance': 'Avoid important beginnings and commitments.',
        },
        'yamaganda': {
            **_segment_window(YAMAGANDA_SEGMENTS[weekday], sunrise_min, sunset_min),
            'label': 'Yamaganda',
            'guidance': 'Avoid travel starts and high-stakes launches.',
        },
        'gulika': {
            **_segment_window(GULIKA_SEGMENTS[weekday], sunrise_min, sunset_min),
            'label': 'Gulika',
            'guidance': 'Use caution; traditionally treated as Saturnine.',
        },
    }


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


def panchanga_range_report(
    start_date: str,
    end_date: str,
    hour_from_sunrise: float = 6.0,
    sunrise: str = '06:00',
    sunset: str = '18:00',
    activity: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz: Optional[float] = None,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """Build a date-range Panchanga calendar with daytime inauspicious windows."""
    start_dt = datetime.strptime(start_date[:10], '%Y-%m-%d')
    end_dt = datetime.strptime(end_date[:10], '%Y-%m-%d')
    if end_dt < start_dt:
        raise ValueError('end_date must be on or after start_date')
    days = (end_dt - start_dt).days + 1
    rows = []
    solar_policies = set()
    panchanga_policies = set()
    for offset in range(days):
        current = start_dt + timedelta(days=offset)
        date_str = current.strftime('%Y-%m-%d')
        weekday = (current.weekday() + 1) % 7
        sun_lon, moon_lon = _approx_sun_moon_lon(current.year, current.month, current.day)
        panchanga_policy = 'approximate Sun/Moon sidereal longitudes from local muhurta kernel'
        solar_times = None
        end_times = None
        day_sunrise = sunrise
        day_sunset = sunset
        if lat is not None and lon is not None and tz is not None:
            solar_times = calc_sunrise_sunset_local(current.year, current.month, current.day, lat, lon, tz)
            solar_policies.add(solar_times.get('policy', 'unknown'))
            day_sunrise = solar_times['sunrise']
            day_sunset = solar_times['sunset']
            sunrise_local_hours = solar_times.get('sunrise_local_hours')
            if sunrise_local_hours is None:
                sunrise_h, sunrise_m = _parse_hhmm(day_sunrise, '06:00')
                sunrise_local_hours = sunrise_h + sunrise_m / 60.0
            reference_local_hours = float(sunrise_local_hours) + hour_from_sunrise
            reference_jd = _jd_for_local_time(current.year, current.month, current.day, reference_local_hours, tz)
            positions = _swisseph_sun_moon_lon(reference_jd, ayanamsa_name=ayanamsa_name) if reference_jd is not None else None
            if positions:
                sun_lon, moon_lon = positions
                panchanga_policy = 'SwissEph Lahiri at sunrise-relative reference time'
                end_times = calc_panchanga_end_times(
                    current.year,
                    current.month,
                    current.day,
                    tz,
                    reference_local_hours,
                    ayanamsa_name=ayanamsa_name,
                )
        panchanga_policies.add(panchanga_policy)
        report = muhurta_full_report(
            sun_lon,
            moon_lon,
            weekday,
            hour_from_sunrise=hour_from_sunrise,
            query_date_str=date_str,
            activities=[activity] if activity else None,
        )
        report['inauspicious_periods'] = calc_daytime_inauspicious_periods(weekday, day_sunrise, day_sunset)
        report['choghadiya'] = calc_choghadiya_windows(weekday, day_sunrise, day_sunset)
        report['hora_windows'] = calc_hora_windows(weekday, day_sunrise, day_sunset)
        panchanga = report['panchanga']
        report['vrata_tags'] = classify_vrata_tags(
            panchanga['tithi'],
            panchanga.get('nakshatra'),
            panchanga.get('vara'),
        )
        report['condition_tags'] = classify_panchanga_condition_tags(report, activity=activity)
        report['festival_details'] = build_festival_details(report)
        if solar_times:
            report['solar_times'] = solar_times
        if end_times:
            report['end_times'] = end_times
        rows.append(report)

    location_supplied = lat is not None and lon is not None and tz is not None
    sunrise_sunset_policy = 'manual fixed sunrise/sunset inputs'
    next_precision_step = 'allow city lookup and daylight-saving timezone resolution'
    if location_supplied:
        if solar_policies == {'swisseph_rise_trans'}:
            sunrise_sunset_policy = 'SwissEph rise_trans'
            next_precision_step = 'add Tithi/Nakshatra end times and festival/vrata rules'
        elif 'swisseph_rise_trans' in solar_policies:
            sunrise_sunset_policy = 'mixed SwissEph rise_trans with approximation fallback'
            next_precision_step = 'investigate dates/locations that required approximation fallback'
        else:
            sunrise_sunset_policy = 'location-aware solar approximation'
            next_precision_step = 'replace approximation with SwissEph rise_trans or vetted Panchanga library'

    return {
        'start_date': start_dt.strftime('%Y-%m-%d'),
        'end_date': end_dt.strftime('%Y-%m-%d'),
        'day_count': len(rows),
        'sunrise': sunrise,
        'sunset': sunset,
        'location': (
            {'lat': round(lat, 5), 'lon': round(lon, 5), 'tz': tz}
            if lat is not None and lon is not None and tz is not None else None
        ),
        'hour_from_sunrise': hour_from_sunrise,
        'calculation_policy': {
            'panchanga': (
                'SwissEph Lahiri at sunrise-relative reference time'
                if panchanga_policies == {'SwissEph Lahiri at sunrise-relative reference time'}
                else 'mixed SwissEph/approximate Panchanga positions'
                if 'SwissEph Lahiri at sunrise-relative reference time' in panchanga_policies
                else 'approximate Sun/Moon sidereal longitudes from local muhurta kernel'
            ),
            'inauspicious_periods': 'traditional daytime eight-segment rule; local clock times',
            'sunrise_sunset': sunrise_sunset_policy,
            'end_times': 'SwissEph boundary bisection when location/timezone are available',
            'sub_day_windows': 'traditional Choghadiya and planetary Hora segmented by local sunrise/sunset',
            'festival_rules': 'conservative tithi/nakshatra/vara vrata rules; masa-dependent festivals marked as candidates',
            'condition_tags': 'searchable row tags derived from vrata, activity verdicts, warnings and sub-day windows',
            'next_precision_step': next_precision_step,
        },
        'search_summary': build_panchanga_search_summary(rows, activity=activity),
        'month_grid': build_panchanga_month_grid(rows, start_dt, end_dt),
        'days': rows,
    }


def muhurta_range_search(
    start_date: str,
    end_date: str,
    activity: str = 'business',
    limit: int = 5,
    hour_from_sunrise: float = 6.0,
    sunrise: str = '06:00',
    sunset: str = '18:00',
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz: Optional[float] = None,
    avoid_inauspicious_periods: bool = True,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """Search a date range for ranked Muhurta candidates for a selected activity."""
    limit = max(1, min(int(limit or 5), 20))
    activity = activity if activity in ACTIVITY_RULES else 'business'
    calendar_report = panchanga_range_report(
        start_date,
        end_date,
        hour_from_sunrise=hour_from_sunrise,
        sunrise=sunrise,
        sunset=sunset,
        activity=activity,
        lat=lat,
        lon=lon,
        tz=tz,
        ayanamsa_name=ayanamsa_name,
    )
    candidates = []
    rejected_dates = []
    for row in calendar_report.get('days', []):
        candidate = _build_muhurta_candidate(row, activity, avoid_inauspicious_periods)
        if candidate['score'] >= 0.45 and candidate['recommended_windows']:
            candidates.append(candidate)
        else:
            rejected_dates.append({
                'date': candidate['date'],
                'score': candidate['score'],
                'reason': candidate['rejection_reason'],
                'activity_verdict': candidate['activity_verdict'],
            })

    candidates.sort(key=lambda item: (item['score'], len(item['recommended_windows'])), reverse=True)
    for item in candidates[limit:]:
        rejected_dates.append({
            'date': item['date'],
            'score': item['score'],
            'reason': 'ranked below selected candidate limit',
            'activity_verdict': item['activity_verdict'],
        })
    best_windows = candidates[:limit]
    return {
        'mode': 'muhurta_date_range_solver',
        'activity': activity,
        'activity_label': ACTIVITY_RULES[activity]['name'],
        'date_range': {
            'start': calendar_report['start_date'],
            'end': calendar_report['end_date'],
        },
        'candidate_count': len(best_windows),
        'scanned_days': calendar_report['day_count'],
        'constraints': {
            'limit': limit,
            'hour_from_sunrise': hour_from_sunrise,
            'avoid_inauspicious_periods': bool(avoid_inauspicious_periods),
            'sunrise': sunrise,
            'sunset': sunset,
            'location': calendar_report.get('location'),
        },
        'best_windows': best_windows,
        'rejected_dates': rejected_dates,
        'calculation_policy': calendar_report.get('calculation_policy', {}),
        'next_action': '把候选日期作为初筛；婚礼、手术、签约等高风险活动仍需结合本命盘、Dasha/Transit 和当地传统规则复核。',
    }


def build_muhurta_sidecar(
    *,
    date_str: str,
    activity: str = 'business',
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz: Optional[float] = None,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """Compact Muhurta/Panchanga packet for unified workflow consumers."""
    activity = activity if activity in ACTIVITY_RULES else 'business'
    search = muhurta_range_search(
        date_str,
        date_str,
        activity=activity,
        limit=3,
        lat=lat,
        lon=lon,
        tz=tz,
        ayanamsa_name=ayanamsa_name,
    )
    calendar = panchanga_range_report(
        date_str,
        date_str,
        activity=activity,
        lat=lat,
        lon=lon,
        tz=tz,
        ayanamsa_name=ayanamsa_name,
    )
    days = calendar.get('days') or []
    first_day = days[0] if days else {}
    return {
        'status': 'ok',
        'source': 'local_muhurta.py',
        'date': date_str,
        'activity': activity,
        'activity_label': ACTIVITY_RULES[activity]['name'],
        'report_mode': search.get('mode', 'muhurta_date_range_solver'),
        'panchanga': {
            'query_date': first_day.get('query_date', date_str),
            'summary': first_day.get('summary') or {},
            'panchanga': first_day.get('panchanga') or {},
            'inauspicious_periods': first_day.get('inauspicious_periods') or [],
            'choghadiya': first_day.get('choghadiya') or [],
            'hora_windows': first_day.get('hora_windows') or [],
            'condition_tags': first_day.get('condition_tags') or [],
        },
        'best_windows': search.get('best_windows') or [],
        'calculation_policy': calendar.get('calculation_policy') or search.get('calculation_policy') or {},
        'next_action': search.get('next_action') or 'Use as timing sidecar only; final judgement still needs chart-based workflow.',
    }


def _build_muhurta_candidate(row: Dict, activity: str, avoid_inauspicious_periods: bool) -> Dict:
    summary = row.get('summary') or {}
    panchanga = row.get('panchanga') or {}
    activity_check = (row.get('activity_checks') or {}).get(activity, {})
    recommended_windows = _select_recommended_windows(row, avoid_inauspicious_periods)
    score = _score_muhurta_candidate(summary, activity_check, recommended_windows)
    quality = _candidate_quality(score, activity_check)
    rejection_reason = _candidate_rejection_reason(row, activity_check, recommended_windows)
    return {
        'date': row.get('query_date'),
        'score': round(score, 3),
        'quality': quality,
        'activity_verdict': activity_check.get('verdict', ''),
        'recommended_windows': recommended_windows,
        'avoid_flags': _build_muhurta_avoid_flags(row, activity_check),
        'rejection_reason': rejection_reason,
        'evidence': {
            'panchanga': {
                'tithi': (panchanga.get('tithi') or {}).get('full_name') or (panchanga.get('tithi') or {}).get('name'),
                'nakshatra': (panchanga.get('nakshatra') or {}).get('nakshatra'),
                'yoga': (panchanga.get('yoga') or {}).get('yoga'),
                'vara': (panchanga.get('vara') or {}).get('vara'),
                'overall_quality': summary.get('overall_quality') or panchanga.get('overall_quality'),
                'overall_score': summary.get('overall_score', panchanga.get('overall_score')),
            },
            'activity_notes': activity_check.get('notes', []),
            'condition_tags': row.get('condition_tags') or [],
        },
    }


def _score_muhurta_candidate(summary: Dict, activity_check: Dict, windows: List[Dict]) -> float:
    score = float(summary.get('overall_score') or 0)
    verdict = activity_check.get('verdict', '')
    if 'Excellent' in verdict or '大吉' in verdict:
        score += 0.22
    elif 'Good' in verdict or '吉' in verdict:
        score += 0.16
    elif 'Fair' in verdict or '一般' in verdict:
        score += 0.06
    elif 'Avoid' in verdict or '不宜' in verdict:
        score -= 0.28
    score += min(len(windows), 3) * 0.04
    if summary.get('warnings'):
        score -= min(len(summary.get('warnings') or []), 3) * 0.04
    return max(0.0, min(1.0, score))


def _candidate_quality(score: float, activity_check: Dict) -> str:
    verdict = activity_check.get('verdict', '')
    if 'Avoid' in verdict or '不宜' in verdict:
        return 'avoid'
    if score >= 0.78:
        return 'excellent'
    if score >= 0.62:
        return 'strong'
    if score >= 0.45:
        return 'usable'
    return 'weak'


def _select_recommended_windows(row: Dict, avoid_inauspicious_periods: bool) -> List[Dict]:
    blocked = _blocked_windows(row) if avoid_inauspicious_periods else []
    selected = []
    for item in (row.get('choghadiya') or {}).get('day') or []:
        if item.get('quality') not in {'auspicious', 'usable'}:
            continue
        if _window_overlaps_any(item, blocked):
            continue
        selected.append({
            'type': 'choghadiya',
            'name': item.get('name'),
            'quality': item.get('quality'),
            'start': item.get('start'),
            'end': item.get('end'),
            'guidance': '优先选择 Amrit/Shubh/Labh；Chal 可作为普通事务备用。',
        })
        if len(selected) >= 3:
            break
    if len(selected) < 3:
        for item in (row.get('hora_windows') or {}).get('day') or []:
            if item.get('lord') not in {'Jupiter', 'Venus', 'Mercury', 'Moon'}:
                continue
            if _window_overlaps_any(item, blocked):
                continue
            selected.append({
                'type': 'hora',
                'name': f"{item.get('lord')} Hora",
                'quality': 'supportive',
                'start': item.get('start'),
                'end': item.get('end'),
                'guidance': '吉星 Hora 可作为活动执行窗口的辅助条件。',
            })
            if len(selected) >= 3:
                break
    return selected


def _blocked_windows(row: Dict) -> List[Dict]:
    periods = row.get('inauspicious_periods') or {}
    return [
        periods[key]
        for key in ('rahu_kala', 'yamaganda', 'gulika')
        if isinstance(periods.get(key), dict)
    ]


def _build_muhurta_avoid_flags(row: Dict, activity_check: Dict) -> List[str]:
    flags = []
    if 'Avoid' in activity_check.get('verdict', '') or '不宜' in activity_check.get('verdict', ''):
        flags.append('selected_activity_avoid')
    if (row.get('summary') or {}).get('warnings'):
        flags.append('panchanga_warning')
    if not _select_recommended_windows(row, True):
        flags.append('no_clean_daytime_window')
    return flags


def _candidate_rejection_reason(row: Dict, activity_check: Dict, windows: List[Dict]) -> str:
    if 'Avoid' in activity_check.get('verdict', '') or '不宜' in activity_check.get('verdict', ''):
        return 'selected activity verdict is avoid'
    if not windows:
        return 'no clean daytime Choghadiya/Hora window outside Rahu Kala/Yamaganda/Gulika'
    if (row.get('summary') or {}).get('warnings'):
        return 'panchanga warnings reduce confidence'
    return 'score below solver threshold'


def _window_overlaps_any(window: Dict, blocked: List[Dict]) -> bool:
    start = _clock_minutes(str(window.get('start') or '00:00'), '00:00')
    end = _clock_minutes(str(window.get('end') or '00:00'), '00:00')
    for item in blocked:
        blocked_start = _clock_minutes(str(item.get('start') or '00:00'), '00:00')
        blocked_end = _clock_minutes(str(item.get('end') or '00:00'), '00:00')
        if start < blocked_end and blocked_start < end:
            return True
    return False


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
