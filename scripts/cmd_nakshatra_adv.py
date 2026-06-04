#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cmd_nakshatra_adv: Nakshatra Advanced CLI 子命令
Jyotish Vedic Astrology Skill — v6.0.22

子命令:
  nakshatra-adv:  高级Nakshatra分析（Tara Bala / Chandra Bala / Sub-Lord / 综合报告）
  nakshatra-dasha: 星宿大运推演（Ashtottari / Vimshottari Nakshatra-level / Transit Overlay）
  nakshatra-full:  综合星宿完整报告（本命 + 大运 + 过境）
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime


def _compute_chart_from_args(args: Any) -> tuple:
    """
    从 args 计算星盘数据。
    返回 (chart, asc_idx, jd, ayanamsa, planet_lons, moon_lon, moon_nak_idx, asc_sign_idx)
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from jyotish_engine import compute_chart_data

    chart, asc_idx, jd, ayanamsa = compute_chart_data(
        args.year, args.month, args.day, args.hour, args.minute,
        args.lat, args.lon, args.tz, getattr(args, 'node_mode', 'mean'))

    if chart is None:
        return None, None, None, None, {}, 0, 0, 0

    planets = chart.get('planets', {})
    planet_lons = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']

    if not planet_lons:
        return chart, asc_idx, jd, ayanamsa, {}, 0, 0, 0

    moon_lon = planet_lons.get('Moon', 0)
    moon_nak_idx = int(moon_lon / (360.0 / 27)) % 27
    asc_sign_idx = asc_idx if asc_idx is not None else 0

    return chart, asc_idx, jd, ayanamsa, planet_lons, moon_lon, moon_nak_idx, asc_sign_idx


def cmd_nakshatra_adv(args: Any) -> Dict[str, Any]:
    """
    nakshatra-adv 子命令：高级Nakshatra分析（v3.7 → v6.0.22 升级）

    支持 mode:
        all      — 全部（detail + tara + chandra + sublord + full）
        detail   — Nakshatra详情
        tara     — Tara Bala
        chandra  — Chandra Bala (v6.0.22 新增)
        combined — Tara + Chandra 双维综合 (v6.0.22 新增)
        sublord  — Sub-Lord KP
        full     — 综合星宿报告 (v6.0.22 新增)
    """
    result = _compute_chart_from_args(args)
    chart, asc_idx, jd, ayanamsa, planet_lons, moon_lon, moon_nak_idx, asc_sign_idx = result

    if chart is None:
        return {"error": "swisseph未安装"}

    try:
        from nakshatra_advanced import (
            find_nakshatra, calc_all_tara_balas, calc_sub_lord,
            calc_chandra_bala, calc_tara_chandra_combined,
            calc_nakshatra_transits_natal, nakshatra_full_report,
            nakshatra_compatibility,
        )
    except ImportError as e:
        return {"error": f"nakshatra_advanced模块导入失败: {e}"}

    mode = getattr(args, 'mode', 'all') or 'all'

    # === mode: 'detail' ===
    if mode in ('all', 'detail'):
        detail = {}
        for pn, lon in planet_lons.items():
            detail[pn] = find_nakshatra(lon)
        result_dict = {'planets': detail}
        if mode == 'detail':
            return result_dict
    else:
        result_dict = {}

    # === mode: 'tara' ===
    if mode in ('all', 'tara'):
        tara = calc_all_tara_balas(moon_nak_idx, planet_lons)
        if mode == 'tara':
            return {'tara_bala': tara, 'moon_nakshatra_idx': moon_nak_idx}
        result_dict['tara_bala'] = tara

    # === mode: 'chandra' (v6.0.22 新增) ===
    if mode in ('all', 'chandra'):
        moon_sign_idx = int(moon_lon / 30) % 12
        chandra = {}
        for pn, lon in planet_lons.items():
            p_sign = int(lon / 30) % 12
            chandra[pn] = {
                'planet_sign': p_sign,
                'chandra': calc_chandra_bala(moon_sign_idx, p_sign),
            }
        if mode == 'chandra':
            return {'chandra_bala': chandra, 'moon_sign_idx': moon_sign_idx}
        result_dict['chandra_bala'] = chandra

    # === mode: 'combined' (v6.0.22 新增) ===
    if mode in ('all', 'combined'):
        moon_sign_idx = int(moon_lon / 30) % 12
        combined = calc_tara_chandra_combined(moon_nak_idx, moon_sign_idx, planet_lons)
        if mode == 'combined':
            return {'tara_chandra_combined': combined}
        result_dict['tara_chandra_combined'] = combined

    # === mode: 'sublord' ===
    if mode in ('all', 'sublord'):
        sublords = {pn: calc_sub_lord(lon) for pn, lon in planet_lons.items()}
        if mode == 'sublord':
            return {'sub_lords': sublords}
        result_dict['sub_lords'] = sublords

    # === mode: 'all' / 'full' — 综合报告 ===
    if mode in ('all', 'full'):
        full = nakshatra_full_report(chart)
        result_dict.update(full)

    return result_dict


def cmd_nakshatra_dasha(args: Any) -> Dict[str, Any]:
    """
    nakshatra-dasha 子命令：星宿大运推演（v6.0.22 新增）

    支持 mode:
        ashtottari  — 仅 Ashtottari Dasha
        vimshottari — 仅 Vimshottari Nakshatra-level 拆解
        overlay     — 仅 Nakshatra Transit Overlay
        all         — 全部（默认）
    """
    result = _compute_chart_from_args(args)
    chart, asc_idx, jd, ayanamsa, planet_lons, moon_lon, moon_nak_idx, asc_sign_idx = result

    if chart is None:
        return {"error": "swisseph未安装"}

    try:
        from nakshatra_dasha import (
            calc_ashtottari_dasha, calc_current_ashtottari,
            calc_nakshatra_dasha_breakdown,
            calc_nakshatra_transit_overlay,
            nakshatra_dasha_full_report,
        )
    except ImportError as e:
        return {"error": f"nakshatra_dasha模块导入失败: {e}"}

    # 构建 birth_date_str
    birth_date_str = f"{args.year}-{args.month:02d}-{args.day:02d}"

    # 年龄
    age = getattr(args, 'age', None)
    if age is None:
        try:
            birth_date = datetime(args.year, args.month, args.day)
            age = (datetime.now() - birth_date).days / 365.25
        except:
            age = 30.0

    mode = getattr(args, 'mode', 'all') or 'all'

    # 确定 Rahu 宫位
    rahu_deg = planet_lons.get('Rahu', 0)
    rahu_sign_idx = int(rahu_deg / 30) % 12
    rahu_house = ((rahu_sign_idx - asc_sign_idx) % 12) + 1

    if mode == 'ashtottari':
        asht = calc_ashtottari_dasha(moon_lon, birth_date_str, rahu_house)
        if asht['applicable']:
            asht['current'] = calc_current_ashtottari(asht, age)
        return asht

    if mode == 'vimshottari':
        return calc_nakshatra_dasha_breakdown(moon_lon, planet_lons, birth_date_str, age)

    if mode == 'overlay':
        # 需要过境数据：获取当前日期或 --transit-date
        transit_date_str = getattr(args, 'transit_date', None) or datetime.now().strftime('%Y-%m-%d')
        from jyotish_engine import _calc_sidereal_planets_for_jd
        try:
            import swisseph as swe
            ty, tm, td = map(int, transit_date_str.split('-'))
            transit_jd = swe.julday(ty, tm, td, 12.0 - args.tz)
            transit_planets, transit_ayanamsa = _calc_sidereal_planets_for_jd(
                transit_jd, node_mode=getattr(args, 'node_mode', 'mean'), include_ketu=True)
            transit_lons = {}
            for pn, pd in transit_planets.items():
                if isinstance(pd, dict) and 'degree' in pd:
                    transit_lons[pn] = pd['degree']
            overlay = calc_nakshatra_transit_overlay(planet_lons, transit_lons, moon_nak_idx)
            overlay['transit_date'] = transit_date_str
            return overlay
        except ImportError:
            return {"error": "swisseph 未安装，无法计算过境星宿"}

    # mode == 'all': 综合报告
    # 尝试获取过境数据
    transit_lons = None
    try:
        import swisseph as swe
        transit_date_str = getattr(args, 'transit_date', None) or datetime.now().strftime('%Y-%m-%d')
        from jyotish_engine import _calc_sidereal_planets_for_jd
        ty, tm, td = map(int, transit_date_str.split('-'))
        transit_jd = swe.julday(ty, tm, td, 12.0 - args.tz)
        transit_planets, _ = _calc_sidereal_planets_for_jd(
            transit_jd, node_mode=getattr(args, 'node_mode', 'mean'), include_ketu=True)
        transit_lons = {}
        for pn, pd in transit_planets.items():
            if isinstance(pd, dict) and 'degree' in pd:
                transit_lons[pn] = pd['degree']
    except:
        pass

    return nakshatra_dasha_full_report(chart, birth_date_str, age, transit_lons)


def cmd_nakshatra_full(args: Any) -> Dict[str, Any]:
    """
    nakshatra-full 子命令：综合星宿完整报告（本命 + 大运 + 过境）— v6.0.22 新增

    整合三个维度：
    1. 本命 Nakshatra 分析（Tara/Chandra/Sub-Lord/兼容性）
    2. Nakshatra Dasha 推演（Ashtottari + Vimshottari Nakshatra-level）
    3. Nakshatra Transit Overlay（当前过境星宿）
    """
    adv_result = cmd_nakshatra_adv(args)
    dasha_result = cmd_nakshatra_dasha(args)

    return {
        'system': 'Nakshatra Comprehensive Report（星宿综合报告）',
        'version': 'v6.0.22',
        'timestamp': datetime.now().isoformat(),
        'nakshatra_advanced': adv_result,
        'nakshatra_dasha': dasha_result,
    }
