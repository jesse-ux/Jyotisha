#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bhava Chalit (不等宫边界调整) 计算模块 v1.0

Bhava Chalit 是 JHora 和 PyJHora 的标准功能。它根据实际宫位边界
（非等宫30°）调整行星的宫位归属。

核心概念:
  - Bhava Madhya: 宫位中点（宫头/cusp）
  - Bhava Sandhi: 宫位边界（相邻两宫头的中点）
  - 行星根据落在哪两个 Sandhi 边界之间来确定 Bhava 宫位
  - Bhava 宫位可能与 Rashi（星座/整宫）宫位不同

支持的宫位制:
  - equal:      等宫制（每宫30°，从上升点起算）
  - whole_sign: 整宫制（星座=宫位）
  - sripati:    Sripati（Porphyry 变体，吠陀标准）
  - porphyry:   Porphyry（四象限三等分）
  - placidus:   Placidus（时间等分，西方最常用）
  - koch:       Koch（时间等分，西方流行）
"""

from typing import Dict, List, Optional

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGNS_CN = {'Aries': '白羊座', 'Taurus': '金牛座', 'Gemini': '双子座',
            'Cancer': '巨蟹座', 'Leo': '狮子座', 'Virgo': '处女座',
            'Libra': '天秤座', 'Scorpio': '天蝎座', 'Sagittarius': '射手座',
            'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '双鱼座'}


def _norm(lon: float) -> float:
    """归一化到 [0, 360)"""
    return lon % 360.0


def _sign_idx(lon: float) -> int:
    """黄经对应的星座索引 (0-11)"""
    return int(_norm(lon) / 30) % 12


def _angular_dist(a: float, b: float) -> float:
    """从 a 到 b 的正向角距离 [0, 360)"""
    return _norm(b - a)


class BhavaChalitCalculator:
    """Bhava Chalit (不等宫边界调整) 计算器。"""

    HOUSE_SYSTEMS = {
        'equal': 'Equal house (30° each)',
        'placidus': 'Placidus (time-based, most common Western)',
        'porphyry': 'Porphyry (quadrant trisection)',
        'sripati': 'Sripati (Vedic standard, Porphyry variant)',
        'whole_sign': 'Whole Sign (Rashi = House)',
        'koch': 'Koch (time-based, popular in Western)',
    }

    # swisseph house system codes
    _SWE_HSYS = {
        'placidus': b'P',
        'koch': b'K',
        'porphyry': b'O',
        'sripati': b'R',  # Sripati uses Regiomontanus approximation in swe
    }

    def __init__(self):
        self._has_swe = False
        try:
            import swisseph as swe
            self._has_swe = True
            self._swe = swe
        except ImportError:
            pass

    # ------------------------------------------------------------------
    # 核心算法: 宫头计算
    # ------------------------------------------------------------------

    def calculate_cusps(self, asc_lon: float, mc_lon: float,
                        house_system: str = 'sripati',
                        jd: float = None, lat: float = None,
                        lon: float = None) -> List[float]:
        """计算12个宫头（Bhava Madhya）。

        Parameters
        ----------
        asc_lon : float  上升点黄经 (sidereal)
        mc_lon  : float  天顶黄经 (sidereal), 仅 sripati/porphyry 需要
        house_system : str  宫位制
        jd      : float  儒略日, swisseph 宫位制需要
        lat     : float  纬度, swisseph 宫位制需要
        lon     : float  经度, swisseph 宫位制需要

        Returns
        -------
        list[float]  12个宫头黄经, 索引0=第1宫, 索引1=第2宫, ...
        """
        hs = house_system.lower()
        if hs not in self.HOUSE_SYSTEMS:
            raise ValueError(f"不支持的宫位制: {house_system}。"
                             f"可选: {list(self.HOUSE_SYSTEMS.keys())}")

        if hs == 'equal':
            return self._cusps_equal(asc_lon)
        elif hs == 'whole_sign':
            return self._cusps_whole_sign(asc_lon)
        elif hs == 'sripati':
            return self._cusps_sripati(asc_lon, mc_lon)
        elif hs == 'porphyry':
            return self._cusps_porphyry(asc_lon, mc_lon)
        elif hs in ('placidus', 'koch'):
            return self._cusps_swe(asc_lon, hs, jd, lat, lon)
        else:
            return self._cusps_equal(asc_lon)

    def _cusps_equal(self, asc_lon: float) -> List[float]:
        """等宫制: 每宫30°, 从上升点起算。"""
        return [_norm(asc_lon + i * 30) for i in range(12)]

    def _cusps_whole_sign(self, asc_lon: float) -> List[float]:
        """整宫制: 每宫=一个星座, 宫头在星座中点 (Bhava Madhya)。

        在 Jyotish 中, 宫头 (cusp) 是 Bhava Madhya (宫位中点)。
        Whole Sign 下, 中点在 15° of each sign。
        Sandhi (边界) 在星座0°, 确保不会出现 Rashi/Bhava 偏移。
        """
        asc_sign_start = int(asc_lon / 30) * 30
        # cusp = midpoint of each sign = sign_start + 15°
        return [_norm(asc_sign_start + i * 30 + 15) for i in range(12)]

    def _cusps_porphyry(self, asc_lon: float, mc_lon: float) -> List[float]:
        """Porphyry: 四象限三等分。

        四个象限:
          Q1: Asc → MC  (顺时针, 即 MC 在 Asc 之前/之上)
          Q2: MC → Desc (7宫 = Asc+180°)
          Q3: Desc → IC (4宫 = MC+180°)
          Q4: IC → Asc
        每个象限三等分 → 每象限3个宫。
        """
        desc_lon = _norm(asc_lon + 180)
        ic_lon = _norm(mc_lon + 180)
        cusps = [0.0] * 12

        # 1宫 = Asc, 10宫 = MC, 7宫 = Desc, 4宫 = IC
        cusps[0] = _norm(asc_lon)
        cusps[9] = _norm(mc_lon)
        cusps[6] = _norm(desc_lon)
        cusps[3] = _norm(ic_lon)

        # Q1: Asc → MC (houses 12, 11, 10-cusp)
        # 在黄道上, MC 通常在 Asc 的顺时针方向 (数值上 MC < Asc 或绕过360)
        # 行星沿黄道逆时针运行, 但宫位顺时针排列
        # Q1 从 MC 到 Asc (顺时针) 包含 house 11, 12
        # 但实际上 Porphyry 的象限划分是:
        #   Q1 (houses 10,11,12): MC → Asc
        #   Q2 (houses 7,8,9):   Desc → MC
        #   Q3 (houses 4,5,6):   IC → Desc
        #   Q4 (houses 1,2,3):   Asc → IC
        # 注意: 在印度占星中, 宫位顺时针, 2宫在1宫之后

        # 正确的象限划分 (JHora/Porphyry 标准):
        # Q1: Asc → IC   (houses 2, 3)  — 1宫和4宫之间
        # Q2: IC → Desc  (houses 5, 6)  — 4宫和7宫之间
        # Q3: Desc → MC  (houses 8, 9)  — 7宫和10宫之间
        # Q4: MC → Asc   (houses 11, 12) — 10宫和1宫之间

        self._trisect_quadrant(cusps, 0, 3, 1, 2)    # Asc → IC: houses 2,3
        self._trisect_quadrant(cusps, 3, 6, 4, 5)    # IC → Desc: houses 5,6
        self._trisect_quadrant(cusps, 6, 9, 7, 8)    # Desc → MC: houses 8,9
        self._trisect_quadrant(cusps, 9, 0, 10, 11)  # MC → Asc: houses 11,12

        return cusps

    def _cusps_sripati(self, asc_lon: float, mc_lon: float) -> List[float]:
        """Sripati: Porphyry 变体, 吠陀标准。

        与 Porphyry 相同的四象限三等分法。
        Sripati 的特点是: 先用 Porphyry 算出宫头,
        然后每个宫的中点 (midpoint between cusps) 才是真正的 Bhava Madhya。
        但在 JHora 的实现中, Sripati 宫头就是 Porphyry 宫头,
        差异仅在于 Sandhi (边界) 的计算方式。

        这里采用与 JHora 一致的 Sripati 算法:
        即 Porphyry 宫头 + Sandhi 在相邻 Porphyry 宫头中点。
        """
        return self._cusps_porphyry(asc_lon, mc_lon)

    def _trisect_quadrant(self, cusps: List[float],
                          start_idx: int, end_idx: int,
                          inner1: int, inner2: int):
        """将象限三等分, 填入两个内部宫头。

        从 cusps[start_idx] 到 cusps[end_idx], 顺时针方向。
        """
        start_lon = cusps[start_idx]
        end_lon = cusps[end_idx]
        arc = _angular_dist(start_lon, end_lon)
        third = arc / 3.0
        cusps[inner1] = _norm(start_lon + third)
        cusps[inner2] = _norm(start_lon + 2 * third)

    def _cusps_swe(self, asc_lon: float, house_system: str,
                   jd: float, lat: float, lon: float) -> List[float]:
        """使用 swisseph 计算宫头 (Placidus/Koch 等)。

        swisseph houses/houses_ex 返回12个值 (0-indexed):
          cusps[0]=H1, cusps[1]=H2, ..., cusps[11]=H12
        这些是 tropical 度数, 需要减去 ayanamsa 转为 sidereal。
        """
        if not self._has_swe:
            raise RuntimeError(f"swisseph 未安装, 无法使用 {house_system} 宫位制")
        if jd is None or lat is None or lon is None:
            raise ValueError(f"{house_system} 需要 jd, lat, lon 参数")

        hsys = self._SWE_HSYS.get(house_system, b'P')
        cusps_swe, ascmc = self._swe.houses(jd, lat, lon, hsys)

        ayanamsa = self._swe.get_ayanamsa(jd)
        result = []
        for i in range(12):
            result.append(_norm(cusps_swe[i] - ayanamsa))
        return result

    # ------------------------------------------------------------------
    # 核心: Bhava Sandhi (宫位边界)
    # ------------------------------------------------------------------

    def calculate_sandhis(self, cusps: List[float]) -> List[float]:
        """计算12个 Bhava Sandhi (宫位边界)。

        Sandhi[i] = 宫i的起始边界 = 从 cusp[i-1] 到 cusp[i] 的中点
        即相邻两宫头的中点 (沿黄道正向)。

        Returns
        -------
        list[float]  12个Sandhi, sandhi[0]=第1宫起始边界, ...
        """
        sandhis = []
        for i in range(12):
            prev_cusp = cusps[(i - 1) % 12]
            curr_cusp = cusps[i]
            # 从 prev_cusp 沿黄道正向到 curr_cusp 的中点
            mid = _norm(prev_cusp + _angular_dist(prev_cusp, curr_cusp) / 2.0)
            sandhis.append(mid)
        return sandhis

    # ------------------------------------------------------------------
    # 核心: 行星 Bhava 归属
    # ------------------------------------------------------------------

    def _planet_bhava(self, planet_lon: float, sandhis: List[float]) -> int:
        """确定行星落在哪个 Bhava。

        行星落在 sandhi[i] 和 sandhi[(i+1)%12] 之间 → 第(i+1)宫。

        Returns
        -------
        int  宫位 (1-12)
        """
        for i in range(12):
            start = sandhis[i]
            end = sandhis[(i + 1) % 12]
            arc = _angular_dist(start, end)
            pos = _angular_dist(start, planet_lon)
            if pos < arc:
                return i + 1
        # fallback: 最近的宫
        return 1

    def _planet_rashi_house(self, planet_lon: float, asc_lon: float) -> int:
        """整宫制宫位 (Rashi house)。"""
        p_si = _sign_idx(planet_lon)
        a_si = _sign_idx(asc_lon)
        return ((p_si - a_si) % 12) + 1

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def calculate_bhava_boundaries(self, asc_lon: float, mc_lon: float,
                                   house_system: str = 'sripati',
                                   jd: float = None, lat: float = None,
                                   lon: float = None) -> Dict:
        """计算完整的宫位边界信息。

        Returns
        -------
        dict with keys:
            house_system, cusps, sandhis, houses_detail
        """
        cusps = self.calculate_cusps(asc_lon, mc_lon, house_system,
                                     jd, lat, lon)
        sandhis = self.calculate_sandhis(cusps)

        houses_detail = []
        for i in range(12):
            start = sandhis[i]
            end = sandhis[(i + 1) % 12]
            span = _angular_dist(start, end)
            mid = cusps[i]
            mid_sign = SIGNS[_sign_idx(mid)]
            detail = {
                'house': i + 1,
                'cusp_lon': round(mid, 4),
                'cusp_sign': mid_sign,
                'cusp_sign_cn': SIGNS_CN[mid_sign],
                'cusp_degree_in_sign': round(mid - _sign_idx(mid) * 30, 4),
                'sandhi_start_lon': round(start, 4),
                'sandhi_end_lon': round(end, 4),
                'span_degrees': round(span, 4),
            }
            houses_detail.append(detail)

        return {
            'house_system': house_system,
            'house_system_desc': self.HOUSE_SYSTEMS.get(house_system, ''),
            'ascendant_lon': round(asc_lon, 4),
            'mc_lon': round(mc_lon, 4),
            'cusps': [round(c, 4) for c in cusps],
            'sandhis': [round(s, 4) for s in sandhis],
            'houses': houses_detail,
        }

    def get_bhava_chalit_chart(self, planet_lons: Dict[str, float],
                               asc_lon: float, mc_lon: float,
                               house_system: str = 'sripati',
                               jd: float = None, lat: float = None,
                               lon: float = None) -> Dict:
        """根据 Bhava 边界重新分配行星宫位。

        Parameters
        ----------
        planet_lons : dict  {行星名: sidereal黄经}
        asc_lon     : float  上升点黄经
        mc_lon      : float  天顶黄经
        house_system: str   宫位制
        jd, lat, lon       swisseph 宫位制所需参数

        Returns
        -------
        dict with keys:
            house_system, boundaries, planets
        """
        cusps = self.calculate_cusps(asc_lon, mc_lon, house_system,
                                     jd, lat, lon)
        sandhis = self.calculate_sandhis(cusps)

        planets = {}
        for pname, plon in planet_lons.items():
            bhava = self._planet_bhava(plon, sandhis)
            rashi = self._planet_rashi_house(plon, asc_lon)
            si = _sign_idx(plon)
            deg_in_sign = plon - si * 30

            planets[pname] = {
                'longitude': round(plon, 4),
                'sign': SIGNS[si],
                'sign_cn': SIGNS_CN[SIGNS[si]],
                'degree_in_sign': round(deg_in_sign, 4),
                'rashi_house': rashi,
                'bhava_house': bhava,
                'shifted': bhava != rashi,
                'shift_direction': 'forward' if bhava > rashi or (bhava == 1 and rashi == 12)
                                   else 'backward' if bhava != rashi
                                   else 'none',
            }
            # 修正 shift_direction: 考虑环绕
            if bhava != rashi:
                diff = ((bhava - rashi) % 12)
                if diff <= 6:
                    planets[pname]['shift_direction'] = 'forward'
                else:
                    planets[pname]['shift_direction'] = 'backward'

        return {
            'house_system': house_system,
            'house_system_desc': self.HOUSE_SYSTEMS.get(house_system, ''),
            'ascendant_lon': round(asc_lon, 4),
            'mc_lon': round(mc_lon, 4),
            'planets': planets,
            'shifted_planets': [p for p, d in planets.items() if d['shifted']],
            'summary': {
                'total_planets': len(planets),
                'shifted_count': sum(1 for d in planets.values() if d['shifted']),
                'shifted_names': [p for p, d in planets.items() if d['shifted']],
            }
        }

    def compare_rashi_vs_bhava(self, planet_lons: Dict[str, float],
                               asc_lon: float, mc_lon: float,
                               house_system: str = 'sripati',
                               jd: float = None, lat: float = None,
                               lon: float = None) -> Dict:
        """对比 Rashi (整宫) vs Bhava Chalit 宫位, 显示偏移。

        Returns
        -------
        dict with keys:
            house_system, rashi_chart, bhava_chart, shifts, boundaries
        """
        # Rashi chart (whole sign)
        rashi_chart = {}
        asc_si = _sign_idx(asc_lon)
        for pname, plon in planet_lons.items():
            si = _sign_idx(plon)
            house = ((si - asc_si) % 12) + 1
            rashi_chart[pname] = {
                'sign': SIGNS[si],
                'house': house,
                'degree_in_sign': round(plon - si * 30, 4),
            }

        # Bhava Chalit chart
        bhava_result = self.get_bhava_chalit_chart(
            planet_lons, asc_lon, mc_lon, house_system, jd, lat, lon)

        # Shifts
        shifts = []
        for pname in planet_lons:
            rh = rashi_chart[pname]['house']
            bh = bhava_result['planets'][pname]['bhava_house']
            if rh != bh:
                diff = ((bh - rh) % 12)
                direction = 'forward' if diff <= 6 else 'backward'
                magnitude = min(diff, 12 - diff)
                shifts.append({
                    'planet': pname,
                    'sign': rashi_chart[pname]['sign'],
                    'degree_in_sign': rashi_chart[pname]['degree_in_sign'],
                    'rashi_house': rh,
                    'bhava_house': bh,
                    'shift_direction': direction,
                    'shift_magnitude': magnitude,
                    'note': f"{pname} 从第{rh}宫偏移到第{bh}宫 ({direction})"
                })

        # Boundaries
        boundaries = self.calculate_bhava_boundaries(
            asc_lon, mc_lon, house_system, jd, lat, lon)

        return {
            'house_system': house_system,
            'house_system_desc': self.HOUSE_SYSTEMS.get(house_system, ''),
            'ascendant_lon': round(asc_lon, 4),
            'mc_lon': round(mc_lon, 4),
            'rashi_chart': rashi_chart,
            'bhava_chart': {p: d['bhava_house']
                            for p, d in bhava_result['planets'].items()},
            'shifts': shifts,
            'shifted_count': len(shifts),
            'boundaries': boundaries,
        }


# ======================================================================
# CLI 入口
# ======================================================================

def cmd_bhava_chalit(args):
    """bhava-chalit 子命令处理函数。"""
    import json
    import sys
    import os

    # 延迟导入, 避免循环依赖
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from jyotish_engine import compute_chart_data, HAS_SWE, output_json

    if not HAS_SWE:
        return {"error": "swisseph 未安装, 无法计算"}

    chart, asc_idx, jd, ayanamsa = compute_chart_data(
        args.year, args.month, args.day, args.hour, args.minute,
        args.lat, args.lon, args.tz, getattr(args, 'node_mode', 'mean'))

    if chart is None:
        return {"error": "星盘计算失败"}

    # 提取行星黄经
    planet_lons = {}
    for pname, pdata in chart.get('planets', {}).items():
        if 'degree_raw' in pdata:
            planet_lons[pname] = pdata['degree_raw']

    # 上升点和MC黄经
    asc_lon = chart['ascendant']['degree_raw']
    # MC: 从 swisseph 重新获取
    import swisseph as swe
    hour_decimal = args.hour + args.minute / 60.0 - args.tz
    jd_val = swe.julday(args.year, args.month, args.day, hour_decimal)
    cusps_raw, ascmc = swe.houses(jd_val, args.lat, args.lon, b'A')
    mc_tropical = ascmc[1]  # MC
    mc_lon = (mc_tropical - ayanamsa) % 360

    house_system = getattr(args, 'house_system', 'sripati')
    calc = BhavaChalitCalculator()

    mode = getattr(args, 'mode', 'compare')

    if mode == 'boundaries':
        return calc.calculate_bhava_boundaries(
            asc_lon, mc_lon, house_system, jd_val, args.lat, args.lon)
    elif mode == 'chart':
        return calc.get_bhava_chalit_chart(
            planet_lons, asc_lon, mc_lon, house_system,
            jd_val, args.lat, args.lon)
    else:  # compare
        return calc.compare_rashi_vs_bhava(
            planet_lons, asc_lon, mc_lon, house_system,
            jd_val, args.lat, args.lon)
