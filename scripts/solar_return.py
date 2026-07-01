#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solar Return (太阳返照盘 / Varshaphala) 计算模块
Jyotish Vedic Astrology Skill — v6.0.18

功能:
  1. find_solar_return_ut() — 计算太阳返照精确 UT 时刻
  2. calc_solar_return_chart() — 生成完整的太阳返照盘（调用 engine 的 compute_chart_data）
  3. solar_return_full_report() — 太阳返照盘完整报告（整合 Muntha / Year Lord / Tajika Yogas）

依赖:
  - swisseph（高精度天文计算，可选）
  - 若 swisseph 不可用，使用近似算法（误差 ±1 天以内）
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import math
import sys
import os

from ayanamsa_utils import sidereal_flags

# ── swisseph 可用性检测 ─────────────────────────────────────────────
try:
    import swisseph as swe
    HAS_SWE = True
except ImportError:
    HAS_SWE = False


def _gregorian_calendar_flag() -> int:
    """Return the Gregorian calendar flag across swisseph builds."""
    return int(getattr(swe, 'GREG_FLAG', 1)) if HAS_SWE else 1

# ── 常量 ──────────────────────────────────────────────────────────
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

# Sun sign lookup table (approximate, valid ~1950-2100, Lahiri ayanamsa)
# Maps (month, day_range) → sidereal sign index
_SUN_SIGN_LOOKUP = {
    1: [(1, 14, 9), (15, 31, 10)],    # Jan: Sagittarius → Capricorn
    2: [(1, 12, 10), (13, 29, 11)],   # Feb: Capricorn → Aquarius
    3: [(1, 14, 11), (15, 31, 0)],    # Mar: Aquarius → Pisces
    4: [(1, 13, 0), (14, 30, 1)],     # Apr: Pisces → Aries
    5: [(1, 14, 1), (15, 31, 2)],     # May: Aries → Taurus
    6: [(1, 15, 2), (16, 30, 3)],     # Jun: Taurus → Gemini
    7: [(1, 16, 3), (17, 31, 4)],     # Jul: Gemini → Cancer
    8: [(1, 16, 4), (17, 31, 5)],     # Aug: Cancer → Leo
    9: [(1, 16, 5), (17, 30, 6)],     # Sep: Leo → Virgo
    10: [(1, 17, 6), (18, 31, 7)],    # Oct: Virgo → Libra
    11: [(1, 16, 7), (17, 30, 8)],    # Nov: Libra → Scorpio
    12: [(1, 15, 8), (16, 31, 9)],    # Dec: Scorpio → Sagittarius
}


def _estimate_sun_sign(birth_month: int, birth_day: int) -> int:
    """从出生月日估算出生太阳星座（查表法，用于无 swisseph 时的近似计算）。
    精度 ±1 星座，对 Muntha 计算足够（Muntha 只关心12年周期）。
    返回 sign index 0-11。"""
    entries = _SUN_SIGN_LOOKUP.get(birth_month, [(1, 31, 0)])
    for day_start, day_end, sign_idx in entries:
        if day_start <= birth_day <= day_end:
            return sign_idx
    return 0  # fallback


# =========================================================================
# 工具函数
# =========================================================================

def _jd_to_datetime(jd_ut: float) -> datetime:
    """Julian Day (UT) → datetime (UTC)"""
    # 使用 swisseph 的辅助函数，或手动转换
    if HAS_SWE:
        # swe.revjul 返回 (year, month, day, hour, minute, second)
        rev = swe.revjul(jd_ut, _gregorian_calendar_flag())
        if len(rev) == 4:
            y, m, d, hour_decimal = rev
            h = int(hour_decimal)
            minute_decimal = (hour_decimal - h) * 60.0
            mn = int(minute_decimal)
            s = int(round((minute_decimal - mn) * 60.0))
            if s >= 60:
                s -= 60
                mn += 1
            if mn >= 60:
                mn -= 60
                h += 1
        else:
            y, m, d, h, mn, s = rev
        return datetime(y, m, d, int(h), int(mn), int(s))
    else:
        # 近似：JD 2440587.5 = 1970-01-01 00:00:00 UT
        jd_unix = jd_ut - 2440587.5
        ts = int(jd_unix * 86400)
        return datetime(1970, 1, 1) + timedelta(seconds=ts)


def _datetime_to_jd_ut(dt: datetime) -> float:
    """datetime (UTC) → Julian Day (UT)"""
    if HAS_SWE:
        return swe.julday(dt.year, dt.month, dt.day,
                         dt.hour + dt.minute/60.0 + dt.second/3600.0,
                         _gregorian_calendar_flag())
    else:
        # 近似
        unix_sec = int((dt - datetime(1970, 1, 1)).total_seconds())
        return 2440587.5 + unix_sec / 86400.0


def _get_sun_lon_jd(jd_ut: float, ayanamsa_name: str = 'lahiri') -> Optional[float]:
    """计算给定 JD (UT) 的太阳恒星黄经（Lahiri）"""
    if not HAS_SWE:
        return None
    try:
        res = swe.calc_ut(jd_ut, swe.SUN, sidereal_flags(swe, ayanamsa_name))
        return float(res[0][0] % 360.0)
    except Exception:
        return None


# =========================================================================
# 核心：计算太阳返照精确时刻
# =========================================================================

def find_solar_return_ut(
    birth_jd_ut: float,
    birth_sun_lon: float,
    target_year: int,
    lat: float = 0.0,
    lon: float = 0.0,
    tz: float = 0.0,
    max_iter: int = 30,
    tol_deg: float = 0.0003,  # ~1 arcsec
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """
    计算太阳返照（Solar Return）精确 UT 时刻。

    参数:
        birth_jd_ut: 出生时刻 JD (UT)
        birth_sun_lon: 出生太阳恒星黄经 (0-360)
        target_year: 目标年份（计算该年的太阳返照）
        lat, lon, tz: 出生地点（仅用于近似计算，精确计算不需要）
        max_iter: 最大迭代次数
        tol_deg: 收敛精度（度）

    返回:
        dict: {
            'jd_ut': float,           # 太阳返照时刻 JD (UT)
            'dt_ut': datetime,         # 太阳返照 UTC 时间
            'dt_local': datetime,      # 太阳返照本地时间（近似）
            'sun_lon': float,         # 返照时太阳经度（应≈birth_sun_lon）
            'error_deg': float,       # 太阳经度误差（度）
            'iterations': int,         # 实际迭代次数
            'method': str,            # 'swisseph' or 'approximation'
            'note': str,
        }
    """
    if HAS_SWE:
        return _find_solar_return_swe(birth_jd_ut, birth_sun_lon, target_year,
                                      max_iter, tol_deg, ayanamsa_name)
    else:
        return _find_solar_return_approx(birth_jd_ut, birth_sun_lon, target_year, tz)


def _find_solar_return_swe(
    birth_jd_ut: float,
    birth_sun_lon: float,
    target_year: int,
    max_iter: int,
    tol_deg: float,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """使用 swisseph 精确计算太阳返照时刻（Newton 迭代法）"""
    # 近似起始点：出生日期在目标年份的同一天
    birth_dt = _jd_to_datetime(birth_jd_ut)
    try:
        approx_dt = datetime(target_year, birth_dt.month, birth_dt.day, 12, 0, 0)
    except ValueError:
        # 出生是 2月29日 等特殊情况
        approx_dt = datetime(target_year, birth_dt.month, 1, 12, 0, 0)
    jd_guess = _datetime_to_jd_ut(approx_dt)

    prev_diff = None
    for i in range(max_iter):
        sun_lon = _get_sun_lon_jd(jd_guess, ayanamsa_name=ayanamsa_name)
        if sun_lon is None:
            return {'error': 'swisseph calc_ut failed', 'method': 'swisseph_failed'}
        diff = (sun_lon - birth_sun_lon + 180.0) % 360.0 - 180.0  # -180..180
        if abs(diff) < tol_deg:
            # 收敛
            dt_ut = _jd_to_datetime(jd_guess)
            return {
                'jd_ut': jd_guess,
                'dt_ut': dt_ut,
                'dt_local': dt_ut,  # 调用方另行加 tz
                'sun_lon': sun_lon,
                'error_deg': abs(diff),
                'iterations': i + 1,
                'method': 'swisseph_newton',
                'note': f'Newton迭代 {i+1} 步收敛，误差 {abs(diff)*3600:.1f}"',
            }
        # Newton 步：sun 速度 ~1°/天，步长 = -diff（天）
        # 更精确：用瞬时速度（下一小时的速度）
        jd_next = jd_guess + 1.0 / 24.0
        sun_lon_next = _get_sun_lon_jd(jd_next, ayanamsa_name=ayanamsa_name)
        if sun_lon_next is not None:
            speed = (sun_lon_next - sun_lon) * 24.0  # °/day
            if abs(speed) > 0.01:
                step = -diff / speed  # days
            else:
                step = -diff  # fallback
        else:
            step = -diff
        jd_guess += step
        prev_diff = diff

    # 未收敛：返回当前最佳估计
    dt_ut = _jd_to_datetime(jd_guess)
    sun_lon = _get_sun_lon_jd(jd_guess, ayanamsa_name=ayanamsa_name)
    return {
        'jd_ut': jd_guess,
        'dt_ut': dt_ut,
        'dt_local': dt_ut,
        'sun_lon': sun_lon,
        'error_deg': abs((sun_lon - birth_sun_lon + 180) % 360 - 180) if sun_lon else None,
        'iterations': max_iter,
        'method': 'swisseph_newton_not_converged',
        'note': f'Newton迭代 {max_iter} 步未完全收敛，误差较大，请检查',
        'warning': True,
    }


def _find_solar_return_approx(
    birth_jd_ut: float,
    birth_sun_lon: float,
    target_year: int,
    tz: float,
) -> Dict:
    """
    近似计算太阳返照时间（不使用 swisseph）。
    误差：±1 天以内（太阳黄经误差 < 1°）。
    """
    birth_dt = _jd_to_datetime(birth_jd_ut)
    try:
        approx_dt_utc = datetime(target_year, birth_dt.month, birth_dt.day, 12, 0, 0)
    except ValueError:
        approx_dt_utc = datetime(target_year, birth_dt.month, 1, 12, 0, 0)

    dt_local = approx_dt_utc + timedelta(hours=tz)

    return {
        'jd_ut': _datetime_to_jd_ut(approx_dt_utc),
        'dt_ut': approx_dt_utc,
        'dt_local': dt_local,
        'sun_lon': None,   # 未知（没有 swisseph）
        'error_deg': None,
        'iterations': 0,
        'method': 'approximation_no_swe',
        'note': '近似算法（无swisseph），太阳返照时间误差约±1天，太阳经度未知；建议安装swisseph以获精确结果',
        'warning': True,
    }


# =========================================================================
# 生成完整太阳返照盘
# =========================================================================

def calc_solar_return_chart(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    birth_lat: float, birth_lon: float, birth_tz: float,
    target_year: int,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """
    计算太阳返照盘（Varshaphala）。

    工作流程:
      1. 计算精确太阳返照时刻（find_solar_return_ut）
      2. 以返照时刻调用 compute_chart_data() 生成星盘
      3. 返回返照盘数据（planet_lons, houses, ascendant 等）

    参数:
        birth_*: 出生信息
        target_year: 目标年份（计算该年太阳返照）

    返回:
        dict: {
            'solar_return': {...},      # find_solar_return_ut 的结果
            'chart': {...},             # compute_chart_data 的返回值
            'planet_lons': dict,        # 返照盘行星经度
            'houses': dict,             # 返照盘宫位
            'ascendant': dict,           # 返照盘上升
            'note': str,
        }
    """
    # Step 1: 获取出生太阳经度（需要先计算出生盘）
    # 但 compute_chart_data 需要 swisseph，这里假设调用方已算好 birth_sun_lon
    # → 改为由调用方传入 birth_sun_lon，或从出生盘数据里取
    # 这里我们先做：调用 engine 的 compute_chart_data 算出生盘
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from jyotish_engine import compute_chart_data, HAS_SWE as ENGINE_HAS_SWE

        if not ENGINE_HAS_SWE:
            return {
                'error': 'swisseph未安装，无法计算星盘',
                'hint': '安装swisseph: pip install swisseph',
                'solar_return_approx': _find_solar_return_approx(
                    _datetime_to_jd_ut(datetime(birth_year, birth_month, birth_day,
                                            birth_hour, birth_minute, 0)),
                    0,  # birth_sun_lon unknown
                    target_year,
                    birth_tz
                ),
            }

        # 算出出生盘的太阳经度
        birth_chart, birth_asc_idx, birth_jd, _ = compute_chart_data(
            birth_year, birth_month, birth_day,
            birth_hour, birth_minute,
            birth_lat, birth_lon, birth_tz,
            'mean',
            ayanamsa_name=ayanamsa_name,
        )
        if birth_chart is None:
            return {'error': '出生盘计算失败（swisseph问题）'}

        sun_data = birth_chart.get('planets', {}).get('Sun', {})
        birth_sun_lon = sun_data.get('degree_raw', sun_data.get('degree', 0))
        birth_jd_ut = birth_jd

        # Step 2: 计算太阳返照精确时刻
        sr_result = find_solar_return_ut(
            birth_jd_ut, birth_sun_lon, target_year,
            birth_lat, birth_lon, birth_tz,
            ayanamsa_name=ayanamsa_name,
        )
        if 'error' in sr_result:
            return {'error': sr_result['error'], 'solar_return': sr_result}

        sr_jd_ut = sr_result['jd_ut']
        sr_dt_ut = sr_result['dt_ut']

        # Step 3: 以返照时刻计算星盘
        # compute_chart_data 接受 year/month/day/hour/minute
        sr_year, sr_month, sr_day = sr_dt_ut.year, sr_dt_ut.month, sr_dt_ut.day
        sr_hour = sr_dt_ut.hour + sr_dt_ut.minute / 60.0 + sr_dt_ut.second / 3600.0
        sr_hour_int = int(sr_hour)
        sr_minute_int = int((sr_hour - sr_hour_int) * 60)

        sr_chart, sr_asc_idx, sr_jd, sr_ayanamsa = compute_chart_data(
            sr_year, sr_month, sr_day,
            sr_hour_int, sr_minute_int,
            birth_lat, birth_lon, 0,  # UT 时间，时区=0
            'mean',
            ayanamsa_name=ayanamsa_name,
        )
        if sr_chart is None:
            return {'error': '返照盘计算失败', 'solar_return': sr_result}

        # 提取行星经度
        planet_lons = {}
        for pn, pd in sr_chart.get('planets', {}).items():
            if isinstance(pd, dict) and 'degree' in pd:
                planet_lons[pn] = pd['degree']

        houses = sr_chart.get('houses', {})
        ascendant = sr_chart.get('ascendant', {})

        return {
            'solar_return': sr_result,
            'chart': sr_chart,
            'planet_lons': planet_lons,
            'houses': houses,
            'ascendant': ascendant,
            'asc_sign_idx': sr_asc_idx,
            'target_year': target_year,
            'birth_year': birth_year,
            'age': target_year - birth_year,
            'note': f'太阳返照盘 {target_year} 年（年龄 {target_year-birth_year} 岁）',
        }

    except Exception as e:
        return {'error': f'calc_solar_return_chart异常: {e}'}


# =========================================================================
# 完整报告：太阳返照盘 + Muntha + Year Lord + Tajika Yogas
# =========================================================================

def solar_return_full_report(
    birth_year: int, birth_month: int, birth_day: int,
    birth_hour: int, birth_minute: int,
    birth_lat: float, birth_lon: float, birth_tz: float,
    target_year: int,
    ayanamsa_name: str = 'lahiri',
) -> Dict:
    """
    太阳返照盘完整报告（Varshaphala 年运分析）。

    整合:
      - 太阳返照盘计算
      - Muntha（年度主星）
      - Year Lord（年守护星）
      - Tajika Yogas（Ithasala/Easarapha 等）
      - Sahams（特殊点）
      - Tri-Pataka（三旗评估）
      - Mudda Dasha（年内大运）

    v6.0.19 修复：swisseph 不可用时不再提前退出，
    而是用查表法估算太阳星座，继续计算 Muntha 和 Year Lord。
    """
    result = {'target_year': target_year}
    age = target_year - birth_year
    degraded = False  # True when swisseph unavailable

    # 1. 计算太阳返照盘
    sr = calc_solar_return_chart(
        birth_year, birth_month, birth_day,
        birth_hour, birth_minute,
        birth_lat, birth_lon, birth_tz,
        target_year,
        ayanamsa_name=ayanamsa_name,
    )

    if 'error' in sr:
        degraded = True
        result['error'] = sr['error']
        # Extract approximate solar return data if available
        sr_approx = sr.get('solar_return_approx', {})
        result['solar_return'] = sr_approx if sr_approx else sr
        # Estimate sun sign from birth date for Muntha calculation
        approx_sun_sign = _estimate_sun_sign(birth_month, birth_day)
        planet_lons = {'Sun': approx_sun_sign * 30 + 15}  # mid-sign for computations
        asc_sign_idx = None
        result['sr_chart_info'] = {
            'asc_sign': '未知（无swisseph）',
            'asc_sign_idx': None,
            'age': age,
            'note': 'swisseph未安装，Muntha使用近似太阳星座（查表法，±1星座）',
        }
    else:
        result['solar_return'] = sr['solar_return']
        result['sr_chart_info'] = {
            'asc_sign': SIGNS[sr['asc_sign_idx']],
            'asc_sign_idx': sr['asc_sign_idx'],
            'age': sr['age'],
        }
        planet_lons = sr['planet_lons']
        asc_sign_idx = sr['asc_sign_idx']

    # 2. Muntha（正确算法：从返照盘太阳星座开始数）
    try:
        # Solar return sun sign = birth sun sign (by definition of solar return)
        sr_sun_sign = int(planet_lons.get('Sun', 0) / 30) % 12
        muntha_sign = (sr_sun_sign + age) % 12
        muntha_note = ''
        if degraded:
            muntha_note = '（基于查表法估算太阳星座，实际Muntha可能偏差±1星座）'
        result['muntha'] = {
            'muntha_sign_idx': muntha_sign,
            'muntha_sign': SIGNS[muntha_sign],
            'muntha_lord': SIGN_LORDS[SIGNS[muntha_sign]],
            'sr_sun_sign_idx': sr_sun_sign,
            'sr_sun_sign': SIGNS[sr_sun_sign],
            'age': age,
            'formula': f'(返照盘太阳星座{sr_sun_sign} + 年龄{age}) mod 12 = {muntha_sign}',
            'interpretation': _interpret_muntha_sign(muntha_sign),
            'note': muntha_note,
        }
    except Exception as e:
        result['muntha'] = {'error': str(e)}

    # 3. Year Lord（= Muntha 守护星）
    try:
        muntha_data = result.get('muntha', {})
        muntha_sign_val = muntha_data.get('muntha_sign_idx', muntha_sign if 'muntha_sign' in dir() else 0)
        year_lord_sign = muntha_sign_val
        year_lord = SIGN_LORDS[SIGNS[year_lord_sign]]
        result['year_lord'] = {
            'year_lord': year_lord,
            'year_lord_sign_idx': year_lord_sign,
            'year_lord_sign': SIGNS[year_lord_sign],
        }
    except Exception as e:
        result['year_lord'] = {'error': str(e)}

    # 4. Tajika Yogas（需完整星盘，降级模式跳过）
    if degraded:
        result['tajika_yogas'] = {'error': 'swisseph未安装，无法计算Tajika Yogas（需完整星盘）'}
    else:
        try:
            from tajika import calc_tajika_yogas
            yogas = calc_tajika_yogas(planet_lons, chart_type='varsha')
            result['tajika_yogas'] = yogas
        except Exception as e:
            result['tajika_yogas'] = {'error': str(e)}

    # 5. Sahams（需完整星盘，降级模式跳过）
    if degraded:
        result['sahams'] = {'error': 'swisseph未安装，无法计算Sahams（需完整星盘）'}
    else:
        try:
            from tajika import calc_all_sahams
            asc_lon = sr['ascendant'].get('lon', sr['ascendant'].get('degree', 0))
            sr_dt_ut = sr['solar_return']['dt_ut']
            sahams = calc_all_sahams(planet_lons, asc_lon, sr_dt_ut, chart_type='varsha')
            result['sahams'] = sahams
        except Exception as e:
            result['sahams'] = {'error': str(e)}

    # 6. Tri-Pataka（需完整星盘 + year_lord + muntha，降级模式跳过）
    if degraded:
        result['tri_pataka'] = {'error': 'swisseph未安装，无法计算Tri-Pataka（需完整星盘）'}
    else:
        try:
            from tajika import calc_tri_pataka
            yl_data = result.get('year_lord', {})
            yl = yl_data.get('year_lord', '')
            muntha_data = result.get('muntha', {})
            ms = muntha_data.get('muntha_sign_idx', 0)
            tri = calc_tri_pataka(planet_lons, yl, ms)
            result['tri_pataka'] = tri
        except Exception as e:
            result['tri_pataka'] = {'error': str(e)}

    # 7. Mudda Dasha（需 asc_sign_idx + year_lord，降级模式跳过）
    if degraded:
        result['mudda_dasha'] = {'error': 'swisseph未安装，无法计算Mudda Dasha（需完整星盘）'}
    else:
        try:
            from tajika import calc_mudda_dasha
            yl_data = result.get('year_lord', {})
            yl = yl_data.get('year_lord', '')
            mudda = calc_mudda_dasha(asc_sign_idx, yl, birth_month or 1)
            result['mudda_dasha'] = mudda
        except Exception as e:
            result['mudda_dasha'] = {'error': str(e)}

    # 8. Harsha / Panchavargiya Bala（年度强度层）
    try:
        from tajika import calc_tajika_strength_layers
        yl_data = result.get('year_lord', {})
        yl = yl_data.get('year_lord', '')
        if degraded:
            asc_lon = float((asc_sign_idx or 0) * 30)
        else:
            asc = sr.get('ascendant', {})
            asc_lon = asc.get('lon', asc.get('degree', float((asc_sign_idx or 0) * 30)))
        result['tajika_strength'] = calc_tajika_strength_layers(
            planet_lons,
            asc_lon=asc_lon,
            year_lord=yl,
        )
    except Exception as e:
        result['tajika_strength'] = {'error': str(e)}

    # 9. 综合总结
    result['summary'] = _make_sr_summary(result)

    return result

def _interpret_muntha_sign(sign_idx: int) -> str:
    """Muntha 在12星座的解读"""
    interp = {
        0: "年度主题：新开始、冒险、独立行动。适合启动项目。",
        1: "年度主题：财务稳定、物质积累。投资、储蓄、巩固基础。",
        2: "年度主题：学习、沟通、短途旅行。信息处理量大，社交活跃。",
        3: "年度主题：家庭、情感、安全感。家庭事务重要，内心探索。",
        4: "年度主题：创造力、自我表达、子女。创作项目，娱乐活动。",
        5: "年度主题：健康、服务、日常工作。细节管理，身心调整。",
        6: "年度主题：关系、合作、伴侣。婚姻/合伙事务活跃。",
        7: "年度主题：深入转型、危机处理。可能涉及共享财务、心理探索。",
        8: "年度主题：高等学习、长途旅行、哲学。出国、深造、信念探索。",
        9: "年度主题：事业成就、社会地位。职业晋升，长期规划结果。",
        10: "年度主题：社交网络、创新、团体。朋友活跃，科技相关。",
        11: "年度主题：灵性、慈悲服务、潜意识。修心养性，幕后工作。",
    }
    return interp.get(sign_idx, '')


def _make_sr_summary(result: Dict) -> str:
    """生成太阳返照盘综合总结"""
    lines = ["【太阳返照盘综合总结】"]
    target = result.get('target_year', '?')
    age = result.get('sr_chart_info', {}).get('age', '?')
    lines.append(f"  目标年份：{target} 年（年龄 {age} 岁）")

    sr = result.get('solar_return', {})
    if 'dt_ut' in sr:
        lines.append(f"  太阳返照时刻（UT）：{sr['dt_ut']}")
    if sr.get('method', '').startswith('approx'):
        lines.append("  ⚠ 注意：太阳返照时间为近似值，建议安装swisseph获精确时刻")

    muntha = result.get('muntha', {})
    if 'muntha_sign' in muntha:
        lines.append(f"  Muntha：{muntha['muntha_sign']}（守护星 {muntha['muntha_lord']}）")
        lines.append(f"  → {muntha.get('interpretation','')[:60]}")

    yl = result.get('year_lord', {})
    if 'year_lord' in yl:
        lines.append(f"  Year Lord：{yl['year_lord']}")

    tp = result.get('tri_pataka', {})
    if 'verdict' in tp:
        lines.append(f"  Tri-Pataka：{tp['verdict']} — {tp.get('interpretation','')[:50]}")

    yogas = result.get('tajika_yogas', {})
    if 'summary' in yogas:
        lines.append(f"  Tajika Yogas：{yogas['summary'][:100]}")

    return '\n'.join(lines)


# =========================================================================
# CLI 测试入口
# =========================================================================

if __name__ == '__main__':
    print("Solar Return (太阳返照盘) 模块")
    print(f"  swisseph可用: {HAS_SWE}")
    print()

    # 测试：REDACTED_DATE 14:45 +8 的出生盘，计算 2026 年太阳返照
    test_birth_year, test_birth_month, test_birth_day = REDACTED_YEAR, 4, 17
    test_birth_hour, test_birth_minute = 14, 45
    test_lat, test_lon, test_tz = 36.4667, 114.2, 8.0
    test_target_year = 2026

    print(f"测试：出生 {test_birth_year}-{test_birth_month:02d}-{test_birth_day:02d} "
          f"{test_birth_hour:02d}:{test_birth_minute:02d} (tz+{test_tz})")
    print(f"      目标年份：{test_target_year}")
    print()

    result = solar_return_full_report(
        test_birth_year, test_birth_month, test_birth_day,
        test_birth_hour, test_birth_minute,
        test_lat, test_lon, test_tz,
        test_target_year
    )

    print("结果：")
    for k, v in result.items():
        if k in ('tajika_yogas', 'sahams', 'mudda_dasha'):
            print(f"  {k}: (见详细输出）")
        elif k == 'sr_chart_info':
            print(f"  {k}: {v}")
        elif k == 'solar_return':
            sr = v
            print(f"  solar_return:")
            print(f"    method: {sr.get('method', '?')}")
            print(f"    dt_ut: {sr.get('dt_ut', '?')}")
            print(f"    sun_lon: {sr.get('sun_lon', '?')}")
            print(f"    error_deg: {sr.get('error_deg', '?')}")
        elif k == 'summary':
            print(f"  summary:\n{v}")
        else:
            print(f"  {k}: {v}")
