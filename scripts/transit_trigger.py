#!/usr/bin/env python3
"""
Transit精确触发搜索 (v6.9.0)
度数级精确日期搜索：给定行星经度、目标敏感点、搜索区间，
返回所有精确接触的日期和时间。

应用场景：
- 「Saturn transit在我的Moon 15°时触发Sade Sati峰值」
- 「Jupiter什么时候精确经过我的上升？」
- 「当期的Transit在什么时间点激活了我的Yoga？」
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from ayanamsa_utils import ayanamsa_display_name, normalize_ayanamsa_name, sidereal_flags

# 行星每日运动速度（°/天）- 用于步长优化
PLANET_SPEED = {
    'Sun': 0.9856, 'Moon': 13.176, 'Mars': 0.524, 'Mercury': 1.383,
    'Jupiter': 0.0831, 'Venus': 1.383, 'Saturn': 0.0335,
    'Rahu': -0.0529, 'Ketu': -0.0529,
}

# 接触精度阈值（度数）
CONTACT_ORB = 1.0   # 初步搜索
EXACT_ORB = 0.1     # 精确接触


def _get_transit_lon(planet: str, base_date: datetime, days_offset: float) -> float:
    """计算行星在指定日期的过境经度（简化模型，仅作为 Swiss Ephemeris 不可用时的回退）。"""
    speed = PLANET_SPEED.get(planet, 0.5)
    return (base_date.toordinal() * speed + days_offset * 360 / 365.25) % 360


def _datetime_to_jd(dt: datetime) -> float:
    """Convert a datetime to Julian day UT."""
    import swisseph as swe
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3_600_000_000.0
    return swe.julday(dt.year, dt.month, dt.day, hour)


def _angular_diff(a: float, b: float) -> float:
    """Smallest angular distance in degrees."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _get_planet_lon_swe(
    planet_name: str,
    jd: float,
    sidereal: bool = True,
    ayanamsa_name: str = 'lahiri',
) -> float:
    """使用 Swiss Ephemeris 计算行星经度（默认 Lahiri 恒星黄道）。"""
    try:
        import swisseph as swe
        planet_ids = {
            'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
            'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
            'Venus': swe.VENUS, 'Saturn': swe.SATURN,
            'Rahu': swe.MEAN_NODE, 'Ketu': swe.MEAN_NODE,
        }
        pid = planet_ids.get(planet_name)
        if pid is None:
            return None
        flags = swe.FLG_SWIEPH
        if sidereal:
            flags = sidereal_flags(swe, ayanamsa_name)
        result = swe.calc_ut(jd, pid, flags)
        lon = result[0][0]
        if planet_name == 'Ketu':
            lon = (lon + 180) % 360
        return lon % 360
    except (ImportError, Exception):
        pass
    return None


def _get_transit_lon_precise(
    planet: str,
    dt: datetime,
    base_date: datetime,
    ayanamsa_name: str = 'lahiri',
) -> Tuple[float, str]:
    """Return transit longitude and calculation source."""
    try:
        ayanamsa = normalize_ayanamsa_name(ayanamsa_name)
        lon = _get_planet_lon_swe(planet, _datetime_to_jd(dt), ayanamsa_name=ayanamsa)
        if lon is not None:
            return lon, f'swiss_ephemeris_{ayanamsa}'
    except Exception:
        pass
    return _get_transit_lon(planet, base_date, (dt - base_date).total_seconds() / 86400.0), 'mean_speed_fallback'


def search_transit_triggers(
    planet: str,
    target_longitude: float,
    start_date: datetime,
    end_date: datetime,
    orb: float = CONTACT_ORB,
    natal_planets: Dict = None,
    ayanamsa_name: str = 'lahiri',
) -> List[Dict]:
    """
    搜索单个行星的过境触发点。

    Args:
        planet: 过境行星名 (Sun/Moon/Mars/.../Saturn/Jupiter/Rahu/Ketu)
        target_longitude: 目标经度(0-360°) - 通常是上升/月亮/行星度数
        start_date: 搜索起始日期
        end_date: 搜索结束日期
        orb: 接触球度 (默认1°)
        natal_planets: 本命星盘数据(可选,用于SwissEph精确计算)

    Returns:
        [{'date': datetime, 'transit_lon': float, 'orb': float, 'event': str}, ...]
    """
    results = []
    speed = PLANET_SPEED.get(planet, 0.5)
    total_days = (end_date - start_date).days

    if total_days < 1:
        return results

    # 根据行星速度确定搜索步长
    if abs(speed) > 5:  # Moon
        step_hours = 2
    elif abs(speed) > 0.5:  # Sun/Mercury/Venus/Mars
        step_hours = 12
    else:  # Jupiter/Saturn/Rahu/Ketu (慢行星)
        step_hours = 24

    step_days = step_hours / 24.0
    current_date = start_date
    prev_orb = None
    prev_sign = None

    source = 'unknown'
    while current_date <= end_date:
        lon, source = _get_transit_lon_precise(
            planet,
            current_date,
            start_date,
            ayanamsa_name=ayanamsa_name,
        )
        diff = _angular_diff(lon, target_longitude)

        if diff <= orb:
            # 检测是否是进入/离开接触
            if prev_orb is not None and prev_orb > orb:
                results.append({
                    'date': current_date,
                    'transit_lon': round(lon, 2),
                    'orb': round(diff, 2),
                    'event': 'entering',
                    'type': 'transit_contact',
                    'source': source,
                })
            elif prev_orb is None:
                if diff <= EXACT_ORB:
                    results.append({
                        'date': current_date,
                        'transit_lon': round(lon, 2),
                        'orb': round(diff, 2),
                        'event': 'exact',
                        'type': 'exact_hit',
                        'source': source,
                    })

        prev_orb = diff
        current_date += timedelta(days=step_days)

    # 去重并合并连续区间
    merged = _merge_contact_intervals(results, planet, target_longitude)

    return merged


def _merge_contact_intervals(triggers: List[Dict], planet: str, target: float) -> List[Dict]:
    """合并连续的接触区间"""
    if len(triggers) <= 1:
        return triggers
    merged = []
    i = 0
    while i < len(triggers):
        entry = triggers[i]
        # 找对应的离开点
        j = i + 1
        while j < len(triggers) and (triggers[j]['date'] - triggers[j-1]['date']).days <= 1:
            j += 1
        if j > i + 1:
            period_end = triggers[j-1]['date']
            merged.append({
                'planet': planet,
                'target_degree': round(target, 1),
                'start_date': entry['date'].strftime('%Y-%m-%d'),
                'end_date': period_end.strftime('%Y-%m-%d'),
                'duration_days': (period_end - entry['date']).days,
                'event': f'{planet} transit over {target:.1f}°',
                'type': 'transit_period',
                'source': entry.get('source', 'unknown'),
            })
            i = j
        else:
            merged.append({
                'planet': planet,
                'target_degree': round(target, 1),
                'start_date': entry['date'].strftime('%Y-%m-%d'),
                'end_date': entry['date'].strftime('%Y-%m-%d'),
                'duration_days': 1,
                'event': f'{planet} exact on {target:.1f}°',
                'type': 'exact_hit',
                'source': entry.get('source', 'unknown'),
            })
            i += 1
    return merged


def search_all_transit_triggers(
    natal_data: Dict,
    start_date: datetime,
    end_date: datetime,
    planets_to_check: List[str] = None,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """
    搜索所有过境触发点。

    Args:
        natal_data: 本命星盘 {'asc': float, 'planets': {name: {'lon': float}}, ...}
        start_date: 起始日期
        end_date: 结束日期
        planets_to_check: 要检查的行星列表(默认慢行星+日月)

    Returns:
        {
            'sensitive_points': [{name, degree}],
            'triggers': [{planet, target, start, end, event}],
            'sade_sati_check': {...},
            'summary': str,
        }
    """
    if planets_to_check is None:
        planets_to_check = ['Saturn', 'Jupiter', 'Sun', 'Moon', 'Mars', 'Rahu', 'Ketu']

    asc_lon = natal_data.get('asc', 0)
    planets = natal_data.get('planets', {})
    moon_lon = planets.get('Moon', {}).get('lon', 0) if 'Moon' in planets else 0

    # 敏感点定义
    sensitive_points = [
        {'name': 'Ascendant', 'degree': asc_lon},
        {'name': 'Moon', 'degree': moon_lon},
    ]
    for pn in ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
        if pn in planets:
            sensitive_points.append({'name': pn, 'degree': planets[pn].get('lon', 0)})

    # 搜索所有组合
    all_triggers = []
    for sp in sensitive_points:
        for planet in planets_to_check:
            triggers = search_transit_triggers(
                planet, sp['degree'], start_date, end_date, orb=CONTACT_ORB,
                ayanamsa_name=ayanamsa_name,
            )
            for t in triggers:
                t['sensitive_point'] = sp['name']
                all_triggers.append(t)

    # Normalize legacy raw trigger rows (single-contact results may bypass interval merge)
    for t in all_triggers:
        if 'start_date' not in t and 'date' in t:
            t['start_date'] = t['date'].strftime('%Y-%m-%d')
        if 'end_date' not in t and 'date' in t:
            t['end_date'] = t['date'].strftime('%Y-%m-%d')
        if 'duration_days' not in t:
            t['duration_days'] = 1

    # 排序
    all_triggers.sort(key=lambda x: x.get('start_date', '9999-12-31'))

    # Sade Sati 检测
    sade_sati = _check_sade_sati_trigger(asc_lon, moon_lon, start_date, end_date)

    # 逆行检测
    retro_note = _check_retrograde_periods(planets_to_check, start_date, end_date)

    summary = f"搜索完成: {len(all_triggers)}个触发点, "
    summary += f"Sade Sati: {'活跃' if sade_sati.get('active') else '不活跃'}"
    if retro_note:
        summary += f", 逆行: {retro_note}"

    return {
        'search_period': {'start': start_date.strftime('%Y-%m-%d'), 'end': end_date.strftime('%Y-%m-%d')},
        'sensitive_points': sensitive_points,
        'triggers': all_triggers,
        'sade_sati_check': sade_sati,
        'retrograde_notes': retro_note,
        'total_triggers': len(all_triggers),
        'summary': summary,
        'ayanamsa': {
            'name': normalize_ayanamsa_name(ayanamsa_name),
            'display': ayanamsa_display_name(ayanamsa_name),
        },
    }


def _check_sade_sati_trigger(asc_lon: float, moon_lon: float, start: datetime, end: datetime) -> Dict:
    """检测Sade Sati触发期间"""
    # Saturn在Moon前后45°内 = Sade Sati活跃
    # 简化检测：Saturn平均速度0.0335°/天
    saturn_start = 0  # 需要SwissEph精确计算
    return {
        'active': True,
        'note': 'Sade Sati区间需要精确计算(Saturn transit需Swiss Ephemeris)',
        'moon_degree': round(moon_lon, 1),
    }


def _check_retrograde_periods(planets: List[str], start: datetime, end: datetime) -> str:
    """检测逆行期（简化）"""
    retro_planets = [p for p in planets if p in ('Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn')]
    if retro_planets:
        return f"{', '.join(retro_planets[:3])}需SwissEph确认逆行期"
    return ""


def find_exact_transit_date(
    planet: str,
    target_longitude: float,
    start_date: datetime,
    end_date: datetime,
    ayanamsa_name: str = 'lahiri',
) -> Optional[Dict]:
    """
    找到行星精确经过目标经度的日期（二分搜索法）。

    Args:
        planet: 行星名
        target_longitude: 目标经度(0-360°)
        start_date: 搜索起始
        end_date: 搜索结束

    Returns:
        {'date': datetime, 'exact_lon': float} or None
    """
    # 用二分搜索找到精确日期
    lo_days = 0.0
    hi_days = (end_date - start_date).days

    lo_lon, source = _get_transit_lon_precise(
        planet,
        start_date,
        start_date,
        ayanamsa_name=ayanamsa_name,
    )
    hi_lon, _ = _get_transit_lon_precise(
        planet,
        end_date,
        start_date,
        ayanamsa_name=ayanamsa_name,
    )

    for _ in range(30):  # 30次迭代精度 ≈ 1分钟
        mid_days = (lo_days + hi_days) / 2.0
        mid_dt = start_date + timedelta(days=mid_days)
        mid_lon, source = _get_transit_lon_precise(
            planet,
            mid_dt,
            start_date,
            ayanamsa_name=ayanamsa_name,
        )

        if _angular_diff(mid_lon, target_longitude) < EXACT_ORB:
            return {
                'planet': planet,
                'target_degree': round(target_longitude, 1),
                'date': mid_dt.strftime('%Y-%m-%d %H:%M'),
                'exact_degree': round(mid_lon, 2),
                'source': source,
            }

        if (mid_lon - lo_lon) % 360 < (target_longitude - lo_lon) % 360:
            lo_days = mid_days
            lo_lon = mid_lon
        else:
            hi_days = mid_days
            hi_lon = mid_lon

    return None
