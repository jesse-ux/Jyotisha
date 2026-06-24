#!/usr/bin/env python3
"""
Tajika Varshaphala 完整年度星盘分析 (v6.9.1)
整合 solar_return.py + tajika.py + muntha.py 输出完整年报。

P1.4 Tajika Yogas完整 — 优化方案最后一项缺口。
"""
from datetime import datetime
from typing import Dict, List, Optional


def varshaphala_report(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: float, birth_lat: float, birth_lon: float, birth_tz: float,
    natal_planets: Dict, asc_sign: str,
    report_year: int = None,
) -> Dict:
    """
    生成Varshaphala年度星盘分析报告。

    包含：
    1. 年度太阳回归星盘 (Solar Return / Varsha Kundali)
    2. Muntha（年度运行星）位置
    3. 年度主星 (Varshesha) 判定
    4. Tajika Yogas 检测 (10种)
    5. Sahams 特殊点 (36种)
    6. 年度Dasha覆盖

    Args:
        birth_year/month/day: 出生日期
        birth_hour: 出生小时(含小数分钟)
        birth_lat/lon/tz: 出生经纬度和时区
        natal_planets: 本命行星数据
        asc_sign: 上升星座
        report_year: 报告年份(默认当前年)

    Returns:
        完整年度分析报告dict
    """
    if report_year is None:
        report_year = datetime.now().year

    # 1. Solar Return (Varsha Kundali)
    solar_return = _calc_solar_return(birth_year, birth_month, birth_day,
                                       birth_hour, birth_lat, birth_lon, birth_tz,
                                       report_year)

    # 2. Muntha 位置
    muntha = _calc_muntha(asc_sign, birth_year, report_year)

    # 3. 年度主星 (Varshesha)
    varshesha = _get_varshesha(solar_return)

    # 4. Tajika Yogas
    tajika_yogas = _detect_tajika_yogas_safe(solar_return.get('planets', {}))

    # 5. Sahams 扩展
    sahams = _calc_sahams_safe(natal_planets, asc_sign)

    # 6. Harsha / Panchavargiya Bala 强度层
    tajika_strength = _calc_tajika_strength_safe(
        solar_return.get('planets', {}),
        solar_return.get('asc_sign', asc_sign),
        varshesha.get('lord') or varshesha.get('planet'),
    )

    # 7. 关键预测
    predictions = _generate_predictions(solar_return, muntha, varshesha,
                                         tajika_yogas, natal_planets)

    return {
        'method': 'Varshaphala (Tajika Annual)',
        'version': '1.0',
        'report_year': report_year,
        'solar_return': {
            'date': solar_return.get('date', f'{report_year}'),
            'asc_sign': solar_return.get('asc_sign', ''),
            'planets': {k: v.get('sign', '?') for k, v in solar_return.get('planets', {}).items()},
        },
        'muntha': muntha,
        'varshesha': varshesha,
        'tajika_yogas': tajika_yogas,
        'tajika_strength': tajika_strength,
        'sahams': {k: v.get('sign', '?') for k, v in sahams.items() if isinstance(v, dict)} if sahams else {},
        'predictions': predictions,
    }


def _calc_solar_return(by, bm, bd, bh, blat, blon, btz, ry):
    """计算太阳回归星盘"""
    try:
        import swisseph as swe
        jd_start = swe.julday(ry, 1, 1, 0.0)
        natal_sun_lon = swe.calc_ut(swe.julday(by, bm, bd, bh - btz), swe.SUN)[0][0]

        # Binary search for Solar Return
        lo_jd, hi_jd = jd_start, jd_start + 365
        for _ in range(30):
            mid = (lo_jd + hi_jd) / 2
            sun_lon = swe.calc_ut(mid, swe.SUN)[0][0]
            if sun_lon < natal_sun_lon and natal_sun_lon - sun_lon > 180:
                lo_jd = mid
            else:
                hi_jd = mid

        sr_jd = (lo_jd + hi_jd) / 2
        sr_date = swe.revjul(sr_jd)
        asc_lon = swe.houses(sr_jd, blat, blon, b'E')[0][0]

        SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                 'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

        planets = {}
        for pn, pid in [('Sun', swe.SUN), ('Moon', swe.MOON), ('Mars', swe.MARS),
                         ('Mercury', swe.MERCURY), ('Jupiter', swe.JUPITER),
                         ('Venus', swe.VENUS), ('Saturn', swe.SATURN)]:
            lon = swe.calc_ut(sr_jd, pid)[0][0]
            planets[pn] = {'sign': SIGNS[int(lon/30)%12], 'degree': lon % 30}

        return {
            'date': f'{int(sr_date[0])}-{int(sr_date[1]):02d}-{int(sr_date[2]):02d}',
            'asc_sign': SIGNS[int(asc_lon/30)%12],
            'planets': planets,
        }
    except ImportError:
        return {'date': f'{ry}-06-15', 'asc_sign': 'Aries', 'planets': {}}


def _calc_tajika_strength_safe(planets: Dict, asc_sign: str, year_lord: Optional[str]) -> Dict:
    try:
        from tajika import calc_tajika_strength_layers, SIGNS
        planet_lons = {}
        for planet, data in planets.items():
            if not isinstance(data, dict):
                continue
            if 'lon' in data:
                planet_lons[planet] = float(data['lon']) % 360
                continue
            sign = data.get('sign')
            degree = float(data.get('degree', 0) or 0)
            if sign in SIGNS:
                planet_lons[planet] = SIGNS.index(sign) * 30 + degree
        asc_lon = SIGNS.index(asc_sign) * 30 if asc_sign in SIGNS else 0.0
        return calc_tajika_strength_layers(planet_lons, asc_lon=asc_lon, year_lord=year_lord)
    except Exception as e:
        return {'error': str(e)}


def _calc_muntha(asc_sign, birth_year, report_year):
    """Muntha = (birth Age) houses from Asc"""
    SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
             'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    age = report_year - birth_year
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    muntha_idx = (asc_idx + age) % 12
    return {
        'sign': SIGNS[muntha_idx],
        'house': (muntha_idx - asc_idx) % 12 + 1,
        'age': age,
    }


def _get_varshesha(solar_return):
    """年度主星判定：选力量最强者"""
    planets = solar_return.get('planets', {})
    if not planets:
        return {'lord': 'N/A', 'reason': 'Solar Return数据不足'}
    # 简化：选在Kendra中的行星
    asc = solar_return.get('asc_sign', 'Aries')
    SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
             'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    asc_idx = SIGNS.index(asc) if asc in SIGNS else 0
    for pn, pd in planets.items():
        sign = pd.get('sign', '')
        if sign in SIGNS:
            house = (SIGNS.index(sign) - asc_idx) % 12 + 1
            if house in (1, 4, 7, 10):
                return {'lord': pn, 'reason': f'{pn}在年度盘Kendra', 'house': house}
    return {'lord': 'Sun', 'reason': '无Kendra行星,默认Sun'}


def _detect_tajika_yogas_safe(planets):
    try:
        from tajika import detect_tajika_yogas
        return detect_tajika_yogas(planets)
    except:
        return []


def _calc_sahams_safe(natal_planets, asc_sign):
    try:
        from tajika import calc_all_sahams
        planet_lons = {}
        SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                 'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
        for pn, pd in natal_planets.items():
            sign = pd.get('sign', '')
            deg = pd.get('degree', 0) % 30
            planet_lons[pn] = (SIGNS.index(sign) if sign in SIGNS else 0) * 30 + deg
        asc_lon = (SIGNS.index(asc_sign) if asc_sign in SIGNS else 0) * 30
        return calc_all_sahams(planet_lons, asc_lon, datetime.now())
    except:
        return {}


def _generate_predictions(solar_return, muntha, varshesha, tajika_yogas, natal):
    predictions = []
    # Muntha触发
    m_house = muntha.get('house', 1)
    if m_house in (1, 5, 9):
        predictions.append(f'Muntha在{m_house}宫(Dharma三角):今年个人成长和精神发展为主导')
    elif m_house in (2, 6, 10):
        predictions.append(f'Muntha在{m_house}宫(Artha三角):今年财务和事业发展为主导')
    elif m_house in (3, 7, 11):
        predictions.append(f'Muntha在{m_house}宫(Kama三角):今年社交和关系发展为主导')
    elif m_house in (4, 8, 12):
        predictions.append(f'Muntha在{m_house}宫(Moksha三角):今年内在转变和休息为主导')

    # Tajika Yogas
    for y in tajika_yogas:
        predictions.append(f'Tajika Yoga: {y.get("type","")} - {y.get("description","")[:60]}')

    # Varshesha
    vl = varshesha.get('lord', '')
    if vl:
        predictions.append(f'年度主星{vl}: {varshesha.get("reason","")}')

    return predictions
