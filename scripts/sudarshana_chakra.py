#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sudarshana Chakra（三轮盘同参） v1.0
参考：PyJHora sudharsana_chakra.py 算法思路 + BPHS标准
License: MIT

Sudarshana Chakra 是结合三个"盘"的综合分析：
  内圈 = 本命盘（以Lagna为第1宫）
  中圈 = 月亮盘（以Moon星座为第1宫）  
  外圈 = 太阳盘（以Sun星座为第1宫）

核心分析：三环汇聚 — 同一宫位编号在三圈中有相同行星或主题
"""
from typing import Dict, List, Tuple


def build_rotated_chart(raw_planets: Dict, anchor_sign_idx: int) -> Dict:
    """
    以指定星座为第1宫，构建旋转后的12宫宫位映射
    
    Args:
        raw_planets: {planet_name: {"sign_idx": int, "degree": float, ...}}
        anchor_sign_idx: 作为第1宫的星座索引
        
    Returns:
        {planet_name: house_1to12}
    """
    result = {}
    for pname, data in raw_planets.items():
        sign_idx = data.get("sign_idx", 0)
        house = ((sign_idx - anchor_sign_idx) % 12) + 1
        result[pname] = house
    return result


def calculate_sudarshana_chakra(raw_planets: Dict, lagna_sign_idx: int,
                                 moon_sign_idx: int, sun_sign_idx: int) -> Dict:
    """
    Sudarshana Chakra 三轮盘同参计算
    
    Args:
        raw_planets: 行星数据 {name: {sign_idx, degree, ...}}
        lagna_sign_idx: Lagna所在星座索引
        moon_sign_idx: 月亮所在星座索引
        sun_sign_idx: 太阳所在星座索引
    
    Returns:
        {
            "charts": {
                "lagna_chart": {planet: house},  # 内圈
                "moon_chart": {planet: house},   # 中圈
                "sun_chart": {planet: house},    # 外圈
            },
            "convergences": {house_index: {"planets": [names], "circles": int}},
            "triple_convergences": [house_indices],  # 三环汇聚
            "dual_convergences": [house_indices],    # 双环汇聚
        }
    """
    # 构建三个圈
    lagna_chart = build_rotated_chart(raw_planets, lagna_sign_idx)
    moon_chart = build_rotated_chart(raw_planets, moon_sign_idx)
    sun_chart = build_rotated_chart(raw_planets, sun_sign_idx)
    
    # 分析每宫的汇聚情况
    convergences = {}
    for house_num in range(1, 13):
        # 找出三个圈中落入该宫的行星
        planets_in = {}
        for pname in raw_planets:
            if pname in ('Rahu', 'Ketu'):
                continue
            houses = (
                lagna_chart.get(pname, 0),
                moon_chart.get(pname, 0),
                sun_chart.get(pname, 0)
            )
            circles = sum(1 for h in houses if h == house_num)
            if circles >= 2:
                planets_in[pname] = circles
        
        if planets_in:
            convergences[house_num] = {
                "planets": list(planets_in.keys()),
                "max_circles": max(planets_in.values()),
                "details": planets_in,
            }
    
    # 三环汇聚（最强）
    triple = [h for h, data in convergences.items() 
              if data["max_circles"] == 3]
    
    # 双环汇聚
    dual = [h for h, data in convergences.items()
            if data["max_circles"] == 2]
    
    return {
        "charts": {
            "lagna_chart": lagna_chart,
            "moon_chart": moon_chart,
            "sun_chart": sun_chart,
        },
        "convergences": convergences,
        "triple_convergences": triple,
        "dual_convergences": dual,
        "triple_count": len(triple),
        "dual_count": len(dual),
        "summary": _generate_summary(triple, dual, lagna_chart, moon_chart, sun_chart),
    }


def calculate_sd_chakra_with_vargas(raw_planets: Dict,
                                     chart_d1: Dict,
                                     chart_d9: Dict,
                                     chart_d10: Dict,
                                     lagna_d1: int,
                                     lagna_d9: int,
                                     lagna_d10: int) -> Dict:
    """
    Sudarshana Chakra 现代变体：D1 × D9 × D10 三角形分析
    
    Args:
        chart_d1/d9/d10: 各盘的行星宫位数据
        lagna_d1/d9/d10: 各盘的Lagna宫位索引
    
    Returns:
        三盘跨盘分析结果
    """
    # 对各盘以各自Lagna为第1宫旋转
    d1_rotated = build_rotated_chart(chart_d1, lagna_d1)
    d9_rotated = build_rotated_chart(chart_d9, lagna_d9)
    d10_rotated = build_rotated_chart(chart_d10, lagna_d10)
    
    cross_analysis = {}
    for house_num in range(1, 13):
        planets_d1 = {p for p, h in d1_rotated.items() if h == house_num and p not in ('Rahu','Ketu')}
        planets_d9 = {p for p, h in d9_rotated.items() if h == house_num and p not in ('Rahu','Ketu')}
        planets_d10 = {p for p, h in d10_rotated.items() if h == house_num and p not in ('Rahu','Ketu')}
        
        # 跨盘一致的行星
        cross_all = planets_d1 & planets_d9 & planets_d10
        cross_any = planets_d1 | planets_d9 | planets_d10
        
        cross_analysis[house_num] = {
            "d1": sorted(planets_d1),
            "d9": sorted(planets_d9),
            "d10": sorted(planets_d10),
            "triple_cross": sorted(cross_all),
            "total_planets": len(cross_any),
            "unique_planets": len(planets_d1) + len(planets_d9) + len(planets_d10),
        }
    
    return {
        "method": "Sudarshana Chakra (D1×D9×D10 三角形分析)",
        "cross_analysis": cross_analysis,
        "strongest_houses": sorted(
            [h for h, data in cross_analysis.items() if data["triple_cross"]],
            key=lambda h: len(cross_analysis[h]["triple_cross"]),
            reverse=True,
        ),
    }


def calculate_sd_chakra_dasha(lagna_sign_idx: int, moon_sign_idx: int,
                                sun_sign_idx: int, years: int = 108) -> List[Dict]:
    """
    Sudarshana Chakra 12年周期大运（SD Cakra Dasha）
    
    每年 = 三个圈同时向前推进1宫
    第1年 = (L+0, M+0, S+0)
    第2年 = (L+1, M+1, S+1)
    ...
    通常推9周期 = 108年
    
    Args:
        lagna_sign_idx: Lagna星座索引
        moon_sign_idx: 月亮星座索引
        sun_sign_idx: 太阳星座索引
        years: 预测年数（默认108年，9个周期）
    
    Returns:
        [{year: int, period: int, lagna_house, moon_house, sun_house, description}]
    """
    result = []
    for year in range(1, years + 1):
        period = (year - 1) // 12 + 1  # 1-9
        offset = (year - 1) % 12
        
        lh = ((lagna_sign_idx + offset) % 12) + 1
        mh = ((moon_sign_idx + offset) % 12) + 1
        sh = ((sun_sign_idx + offset) % 12) + 1
        
        # 判断该年的主要主题
        circles = len({lh, mh, sh})
        same_house = lh == mh == sh
        
        desc = f"第{period}周期·第{year}年 "
        if same_house:
            desc += f"三圈同聚第{lh}宫 ★"
        elif circles == 2:
            desc += f"内圈{lh}/中圈{mh}/外圈{sh}（双圈一致）"
        else:
            desc += f"内圈{lh}/中圈{mh}/外圈{sh}"
        
        result.append({
            "year": year,
            "period": period,
            "year_in_period": offset + 1,
            "lagna_house": lh,
            "moon_house": mh,
            "sun_house": sh,
            "circles": circles,
            "all_same": same_house,
            "description": desc,
        })
    
    return result


def _generate_summary(triple: List, dual: List,
                       lagna_chart: Dict, moon_chart: Dict,
                       sun_chart: Dict) -> str:
    """生成文本摘要"""
    lines = []
    if triple:
        lines.append(f"三环汇聚（最强）: 第{'/'.join(map(str, triple))}宫")
    if dual:
        lines.append(f"双环汇聚: 第{'/'.join(map(str, dual))}宫")
    if not triple and not dual:
        lines.append("本次无三环或双环汇聚")
    return " | ".join(lines) if lines else "无汇聚"


def sudarshana_full_analysis(raw_planets: Dict, lagna_sign_idx: int,
                               moon_sign_idx: int, sun_sign_idx: int,
                               chart_d1: Dict = None, chart_d9: Dict = None,
                               chart_d10: Dict = None,
                               lagna_d9: int = None, lagna_d10: int = None) -> Dict:
    """
    完整Sudarshana Chakra分析：三轮盘 + D1×D9×D10三角分析 + 12年周期大运
    
    Returns: 综合报告
    """
    # 三轮盘分析
    three_ring = calculate_sudarshana_chakra(
        raw_planets, lagna_sign_idx, moon_sign_idx, sun_sign_idx
    )
    
    # 12年周期大运
    dasha = calculate_sd_chakra_dasha(lagna_sign_idx, moon_sign_idx, sun_sign_idx)
    
    # D1×D9×D10 三角分析（如果有数据）
    triangle = None
    if chart_d1 and chart_d9 and chart_d10 and lagna_d9 is not None and lagna_d10 is not None:
        triangle = calculate_sd_chakra_with_vargas(
            raw_planets, chart_d1, chart_d9, chart_d10,
            lagna_sign_idx, lagna_d9, lagna_d10
        )
    
    return {
        "method": "Sudarshana Chakra 完整分析（三轮盘 + 三角盘 + 12年周期大运）",
        "three_ring_convergences": three_ring,
        "d1_d9_d10_triangle": triangle,
        "chakra_dasha_12_year_cycle": {
            "total_years": len(dasha),
            "cycles": 9,
            "current_period": dasha[0:12],  # 最近12年
        },
    }
