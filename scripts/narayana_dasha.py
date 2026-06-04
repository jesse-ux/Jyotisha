#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narayana Dasha（Rishi Dasha / Padakrama Dasha）计算模块
Jyotish Vedic Astrology Skill — v6.0.20

Narayana Dasha 是 Parashara 传授的 Rishi-based 大运系统，与 Vimshottari 互补：
  - Vimshottari: Nakshatra-based, 120年固定周期
  - Narayana: Rashi-based, 从 Lagna 起按黄道序推进，周期可变

算法（Lagna-based variant, BPHS Chapter 48）:
  1. 从 Lagna 星座开始
  2. 每个星座的大运年数 = 从该星座数到其守护星所在星座的步数（含起点，不含终点）
  3. 若守护星在本星座 → 12年
  4. 按黄道顺序推进 12 星座，然后循环
  5. Antardasha 按各星座年数比例分配

依赖: 需要 planet_lons 和 houses 数据（可从引擎传入）
"""

from typing import Dict, List, Optional, Tuple
import math

# ── 常量 ──────────────────────────────────────────────────────────
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {
    'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter',
}
SIGN_INDEX = {s:i for i,s in enumerate(SIGNS)}

# Planet name → sign index lookup
PLANET_SIGN_INDEX = {
    'Sun': 4, 'Moon': 3, 'Mars': (0,7), 'Mercury': (2,5),
    'Jupiter': (8,11), 'Venus': (1,6), 'Saturn': (9,10),
    'Rahu': 10, 'Ketu': 7,  # traditional assignments
}


# =========================================================================
# 核心计算
# =========================================================================

def _get_planet_sign(planet_name: str, planet_lons: Dict[str, float]) -> Optional[int]:
    """获取行星所在星座索引"""
    lon = planet_lons.get(planet_name)
    if lon is None:
        return None
    return int(lon / 30) % 12


def _count_signs_forward(src_idx: int, dest_idx: int) -> int:
    """从 src 数到 dest（含起点，不含终点），顺黄道方向。
    若 src == dest → 12 年（守护星在本星座）"""
    if src_idx == dest_idx:
        return 12
    count = (dest_idx - src_idx + 12) % 12
    return count  # 已含起点


def calc_narayana_mahadasha(
    lagna_sign_idx: int,
    planet_lons: Dict[str, float],
    start_year: float = 0.0,
) -> List[Dict]:
    """
    计算 Narayana Dasha 大运序列（第1周期）。

    参数:
        lagna_sign_idx: Lagna 星座索引 (0-11)
        planet_lons: 行星经度字典 {planet_name: longitude_deg}
        start_year: 起始年份偏移（默认 0 = 出生时）

    返回:
        list of dasha periods, each: {
            'sign': str, 'sign_idx': int, 'lord': str,
            'years': int, 'start_age': float, 'end_age': float,
        }
    """
    periods = []
    cum_years = start_year

    for i in range(12):
        sign_idx = (lagna_sign_idx + i) % 12
        sign = SIGNS[sign_idx]
        lord = SIGN_LORDS[sign]

        # 获取 lord 所在的星座
        lord_sign_idx = _get_planet_sign(lord, planet_lons)
        if lord_sign_idx is None:
            # fallback: 如果找不到 lord 位置，用 lord 的 Moolatrikona 或自身星座
            lord_sign_idx = sign_idx  # 保守假设：lord 在自己星座

        years = _count_signs_forward(sign_idx, lord_sign_idx)

        periods.append({
            'sign': sign,
            'sign_idx': sign_idx,
            'lord': lord,
            'lord_in_sign': SIGNS[lord_sign_idx],
            'lord_sign_idx': lord_sign_idx,
            'years': years,
            'count_from_to': f'{sign}({sign_idx})→{SIGNS[lord_sign_idx]}({lord_sign_idx})',
            'start_age': round(cum_years, 2),
            'end_age': round(cum_years + years, 2),
        })
        cum_years += years

    return periods


def calc_narayana_antardasha(
    mahadasha_periods: List[Dict],
    md_sign_idx: int,
) -> List[Dict]:
    """
    计算给定 Mahadasha 的 Antardasha 子周期。

    参数:
        mahadasha_periods: calc_narayana_mahadasha 的返回值
        md_sign_idx: Mahadasha 星座索引

    返回:
        list of antardasha periods
    """
    # 找到对应的大运
    md = None
    for p in mahadasha_periods:
        if p['sign_idx'] == md_sign_idx:
            md = p
            break
    if md is None:
        return []

    total_years = md['years']
    sub_periods = []
    cum = md['start_age']

    # Antardasha 从 MD 星座开始，按黄道序推进
    for i in range(12):
        sign_idx = (md_sign_idx + i) % 12
        lord_sign = mahadasha_periods[0]['lord_in_sign']  # placeholder
        sub_years_ratio = mahadasha_periods[i]['years'] / sum(p['years'] for p in mahadasha_periods)
        sub_years = round(total_years * sub_years_ratio, 2)

        sub_periods.append({
            'sign': SIGNS[sign_idx],
            'sign_idx': sign_idx,
            'lord': SIGN_LORDS[SIGNS[sign_idx]],
            'years': sub_years,
            'start_age': round(cum, 2),
            'end_age': round(cum + sub_years, 2),
            'parent_md': SIGNS[md_sign_idx],
        })
        cum += sub_years

    return sub_periods


def get_current_narayana_dasha(
    mahadasha_periods: List[Dict],
    current_age: float,
) -> Dict:
    """
    获取当前年龄对应的 Narayana Dasha 周期（Mahadasha + Antardasha）。

    返回:
        {
            'md': {...},   # 当前大运
            'ad': {...},   # 当前小运
            'pd': {...},   # 当前节运（Pratyantara，简化）
            'remaining_years': float,
        }
    """
    result = {'md': None, 'ad': None, 'pd': None, 'remaining_years': 0}

    # 处理多年期（可能跨多个周期）
    total_cycle = sum(p['years'] for p in mahadasha_periods)
    if total_cycle == 0:
        return result

    age_in_cycle = current_age % total_cycle

    # 找当前 MD
    for p in mahadasha_periods:
        if p['start_age'] <= age_in_cycle < p['end_age']:
            result['md'] = {
                'sign': p['sign'],
                'sign_idx': p['sign_idx'],
                'lord': p['lord'],
                'years': p['years'],
                'start_age': p['start_age'],
                'end_age': p['end_age'],
            }
            result['remaining_years'] = round(p['end_age'] - age_in_cycle, 2)

            # 计算 AD
            ads = calc_narayana_antardasha(mahadasha_periods, p['sign_idx'])
            elapsed_in_md = age_in_cycle - p['start_age']
            for ad in ads:
                if ad['start_age'] <= elapsed_in_md < ad['end_age']:
                    result['ad'] = {
                        'sign': ad['sign'],
                        'sign_idx': ad['sign_idx'],
                        'lord': ad['lord'],
                        'years': ad['years'],
                        'start_age': round(p['start_age'] + ad['start_age'], 2),
                        'end_age': round(p['start_age'] + ad['end_age'], 2),
                    }
                    break
            break

    return result


def narayana_dasha_full_report(
    lagna_sign_idx: int,
    planet_lons: Dict[str, float],
    current_age: float = 0,
    birth_year: int = 0,
) -> Dict:
    """
    Narayana Dasha 完整报告。

    参数:
        lagna_sign_idx: Lagna 星座索引 (0-11)
        planet_lons: 行星经度字典
        current_age: 当前年龄
        birth_year: 出生年份

    返回:
        dict with mahadasha_sequence, current_dasha, total_cycle_years
    """
    result = {}

    # 1. 完整大运序列
    mahadasha = calc_narayana_mahadasha(lagna_sign_idx, planet_lons)
    total_cycle = sum(p['years'] for p in mahadasha)
    result['mahadasha_sequence'] = mahadasha
    result['total_cycle_years'] = total_cycle
    result['lagna_sign'] = SIGNS[lagna_sign_idx]
    result['lagna_sign_idx'] = lagna_sign_idx

    # 2. 当前大运
    if current_age > 0:
        curr = get_current_narayana_dasha(mahadasha, current_age)
        result['current_dasha'] = curr

        # 当前日期（如果有出生年份）
        if birth_year > 0:
            curr_year = birth_year + int(current_age)
            result['current_year'] = curr_year
            result['current_age'] = current_age

    # 3. 简要解读
    result['interpretation'] = _interpret_narayana(result, current_age)

    return result


def _interpret_narayana(result: Dict, current_age: float) -> List[str]:
    """Narayana Dasha 简要解读"""
    lines = []

    md_seq = result.get('mahadasha_sequence', [])
    if md_seq:
        total = sum(p['years'] for p in md_seq)
        lines.append(f"Narayana Dasha 完整周期: {total} 年（12 星座 × 可变年数）")
        lines.append(f"起运星座: {result.get('lagna_sign', '?')}（Lagna）")

    curr = result.get('current_dasha', {})
    md = curr.get('md')
    if md:
        lord_cond = _check_lord_condition(md['sign_idx'], result.get('lagna_sign_idx', 0))
        lines.append(f"当前 Narayana Mahadasha: {md['sign']}（守护星 {md['lord']}，{md['years']}年）")
        lines.append(f"  剩余: {curr.get('remaining_years', 0):.1f}年")
        lines.append(f"  {lord_cond}")

    ad = curr.get('ad')
    if ad:
        lines.append(f"当前 Antardasha: {ad['sign']}（守护星 {ad['lord']}，{ad['years']}年）")

    # 与 Vimshottari 互补提示
    lines.append("")
    lines.append("【与 Vimshottari 互补解读提示】")
    lines.append("Narayana Dasha 的星座主题与 Vimshottari 的行星主题形成互补。")
    lines.append("两者一致 → 事件确定性高；两者矛盾 → 混合影响，需看具体宫位。")

    return lines


def _check_lord_condition(sign_idx: int, lagna_idx: int) -> str:
    """检查当前星座守护星与 Lagna 的关系"""
    house_from_lagna = (sign_idx - lagna_idx + 12) % 12 + 1
    house_labels = {
        1: 'Lagna（自我/身体）', 2: '2宫（财富/家庭）', 3: '3宫（兄弟/努力）',
        4: '4宫（家庭/房产）', 5: '5宫（子女/创意）', 6: '6宫（健康/竞争）',
        7: '7宫（婚姻/合作）', 8: '8宫（转型/遗产）', 9: '9宫（信仰/长途）',
        10: '10宫（事业/地位）', 11: '11宫（收益/社交）', 12: '12宫（支出/灵性）',
    }
    return f"  从 Lagna 算 = {house_from_lagna}宫 {house_labels.get(house_from_lagna, '')}"


# =========================================================================
# CLI 测试入口
# =========================================================================

if __name__ == '__main__':
    print("Narayana Dasha（Rishi Dasha）模块 v6.0.20")
    print()

    # 测试数据：用户星盘 Le Asc, Saturn MD
    test_lagna = 4  # Leo
    test_planets = {
        'Sun': 19.07, 'Moon': 325.64, 'Mars': 98.12, 'Mercury': 32.56,
        'Jupiter': 97.08, 'Venus': 55.01, 'Saturn': 306.96,
        'Rahu': 342.27, 'Ketu': 162.27,
    }
    test_age = 33.13  # 2026-06-04 年龄

    print(f"测试: Leo Asc, age={test_age}")
    print(f"行星经度: { {k: f'{v:.1f}' for k,v in test_planets.items()} }")
    print()

    result = narayana_dasha_full_report(test_lagna, test_planets, test_age, REDACTED_YEAR)

    print("=== 大运序列 ===")
    for p in result['mahadasha_sequence']:
        print(f"  {p['sign']:>12s} ({p['lord']:>7s} in {p['lord_in_sign']:>12s}): "
              f"{p['years']:2d}年  [{p['start_age']:5.1f}→{p['end_age']:5.1f}]  "
              f"{p['count_from_to']}")

    print(f"\n总周期: {result['total_cycle_years']} 年")

    print("\n=== 当前 Dasha ===")
    curr = result.get('current_dasha', {})
    md = curr.get('md')
    if md:
        print(f"  MD: {md['sign']} ({md['lord']}) {md['years']}年")
        print(f"  剩余: {curr['remaining_years']}年")
    ad = curr.get('ad')
    if ad:
        print(f"  AD: {ad['sign']} ({ad['lord']}) {ad['years']}年")

    print("\n=== 解读 ===")
    for line in result.get('interpretation', []):
        print(line)
