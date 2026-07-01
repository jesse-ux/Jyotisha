#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narayana Dasha 子命令
Jyotish Vedic Astrology Skill — v6.0.20
"""

import json


def cmd_narayana_dasha(args, chart_data):
    """
    narayana-dasha 子命令：计算并报告 Narayana Dasha（Rishi Dasha）。

    用法:
      python jyotish_engine.py narayana-dasha --year REDACTED_YEAR --month 4 --day 17 \\
          --hour 14 --minute 45 --lat 36.47 --lon 114.2 --tz 8 --age 33
    """
    if chart_data is None:
        return "\n".join([
            "╔══════════════════════════════════════════╗",
            "║  Narayana Dasha（Rishi Dasha）         ║",
            "╚══════════════════════════════════════════╝",
            "",
            "错误：图表数据未生成（swisseph 可能未安装）。",
            "Narayana Dasha 需要完整的行星经度数据。",
        ])

    from narayana_dasha import narayana_dasha_full_report

    planet_lons = {}
    for pn, pd in chart_data.get('planets', {}).items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']

    asc_idx = chart_data.get('ascendant_index')
    if asc_idx is None:
        asc_info = chart_data.get('ascendant', {}) if isinstance(chart_data, dict) else {}
        asc_idx = asc_info.get('sign_idx', 0)
        if asc_idx == 0 and isinstance(asc_info, dict):
            # compute_chart_data 输出 ascendant.sign，但不一定输出 sign_idx；兼容旧结构
            sign_name = asc_info.get('sign')
            signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
            if sign_name in signs:
                asc_idx = signs.index(sign_name)
    if isinstance(asc_idx, str):
        asc_idx = int(asc_idx)

    current_age = float(getattr(args, 'age', 0) or 0)
    birth_year = getattr(args, 'year', 0) or 0

    result = narayana_dasha_full_report(
        lagna_sign_idx=asc_idx,
        planet_lons=planet_lons,
        current_age=current_age,
        birth_year=birth_year,
    )

    # 格式化输出
    lines = [
        "╔══════════════════════════════════════════╗",
        "║  Narayana Dasha（Rishi Dasha）         ║",
        "╚══════════════════════════════════════════╝",
        "",
        f"Lagna: {result['lagna_sign']}（{result['lagna_sign_idx']}）",
        f"总周期: {result['total_cycle_years']} 年",
        "",
        "── 大运序列 ──",
    ]

    for p in result['mahadasha_sequence']:
        lines.append(
            f"  {p['sign']:>12s} ({p['lord']:>7s} in {p['lord_in_sign']:>12s}): "
            f"{p['years']:2d}年  [{p['start_age']:5.1f}→{p['end_age']:5.1f}]"
        )

    curr = result.get('current_dasha', {})
    md = curr.get('md')
    if md:
        lines.append("")
        lines.append(f"── 当前大运（age={current_age:.1f}）──")
        lines.append(f"  Mahadasha: {md['sign']}（{md['lord']}）{md['years']}年")
        lines.append(f"  剩余: {curr.get('remaining_years', 0):.1f}年")

    ad = curr.get('ad')
    if ad:
        lines.append(f"  Antardasha: {ad['sign']}（{ad['lord']}）{ad['years']}年")

    pd = curr.get('pd')
    if pd:
        lines.append(f"  Pratyantardasha: {pd['sign']}（{pd['lord']}）{pd['years']}年")

    lines.append("")
    for line in result.get('interpretation', []):
        lines.append(f"  {line}")

    return "\n".join(lines)
