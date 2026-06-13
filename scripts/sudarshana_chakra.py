#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sudarshana Chakra（苏达沙那轮）— 三参考点复合分析
====================================================
基于BPHS传统技法，将星盘分别以上升、月亮、太阳为第一宫，
生成三张参考盘并叠加分析。

三个参考点：
1. Ascendant Lagna (AL) → 自我、身体
2. Moon Lagna (ML) → 情感、心理
3. Sun Lagna (SL) → 灵魂、生命力

当三个参考点中同一宫位/行星配置一致时，事件确认度高。

版本: v2.0 | 2026-06-13  重构为完整分析器
"""

from typing import Dict, List, Optional, Tuple

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGNS_CN = {
    'Aries': '白羊座', 'Taurus': '金牛座', 'Gemini': '双子座',
    'Cancer': '巨蟹座', 'Leo': '狮子座', 'Virgo': '处女座',
    'Libra': '天秤座', 'Scorpio': '天蝎座', 'Sagittarius': '射手座',
    'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '双鱼座'
}

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

PLANETS_ALL = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']

# 吉宫: 1,2,3,4,5,7,9,10,11  凶宫: 6,8,12
FAVORABLE_HOUSES = {1, 2, 3, 4, 5, 7, 9, 10, 11}
UNFAVORABLE_HOUSES = {6, 8, 12}
# 中性宫: 无（传统分法中6,8,12为dusthana，其余吉）

HOUSE_MEANINGS = {
    1:  ('自我/健康', 'Self/Health'),
    2:  ('财富/家庭', 'Wealth/Family'),
    3:  ('勇气/兄弟姐妹', 'Courage/Siblings'),
    4:  ('幸福/母亲/住所', 'Happiness/Mother/Home'),
    5:  ('子女/智力/过去善业', 'Children/Intelligence/Poorvapunya'),
    6:  ('疾病/敌人/债务', 'Disease/Enemies/Debt'),
    7:  ('婚姻/伴侣/合作', 'Marriage/Partnership'),
    8:  ('寿命/变革/隐秘', 'Longevity/Transformation'),
    9:  ('幸运/导师/宗教', 'Fortune/Guru/Religion'),
    10: ('事业/地位/名声', 'Career/Status/Fame'),
    11: ('收益/愿望/朋友圈', 'Gains/Wishes/Circles'),
    12: ('损失/解脱/海外', 'Loss/Liberation/Foreign'),
}

# 宫主星飞入各宫的吉凶权重
LORD_PLACEMENT_WEIGHTS = {
    # 自身宫位 → 强
    'own_house': 1.0,
    # 吉宫
    'favorable': 0.8,
    # 凶宫
    'unfavorable': 0.2,
    # 角宫(kendra) 1,4,7,10
    'kendra': 0.7,
    # 三方宫(trikona) 1,5,9
    'trikona': 0.9,
}


class SudarshanaChakraAnalyzer:
    """Sudarshana Chakra — 三 Lagna 叠加分析器"""

    SIGNS = SIGNS
    SIGN_LORDS = SIGN_LORDS

    def __init__(self):
        self.seven_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _sign_idx(sign_or_idx) -> int:
        """将星座名或索引统一转为 0-11 索引"""
        if isinstance(sign_or_idx, int):
            return sign_or_idx % 12
        if isinstance(sign_or_idx, str) and sign_or_idx in SIGNS:
            return SIGNS.index(sign_or_idx)
        return 0

    @staticmethod
    def _house_from_refs(planet_sign_idx: int, reference_sign_idx: int) -> int:
        """计算行星在以 reference_sign_idx 为第一宫时的宫位 (1-12)"""
        return (planet_sign_idx - reference_sign_idx) % 12 + 1

    @staticmethod
    def _sign_idx_from_lon(lon: float) -> int:
        """从黄经获取星座索引 (0-11)"""
        return int(lon / 30) % 12

    def _planet_sign_idx(self, planet_lons: Dict, planet: str) -> int:
        """从 planet_lons 字典获取行星星座索引"""
        lon = planet_lons.get(planet)
        if lon is None:
            return 0
        return self._sign_idx_from_lon(lon)

    # ------------------------------------------------------------------
    # 核心方法
    # ------------------------------------------------------------------

    def generate_three_charts(self, planet_lons: Dict, asc_lon: float) -> Dict:
        """
        生成三参考点盘。

        Args:
            planet_lons: {planet_name: longitude_in_sidereal_0_360}
            asc_lon: 上升点黄经 (sidereal, 0-360)

        Returns:
            {
                'ascendant_lagna': {planet: {'sign': str, 'sign_idx': int, 'house': int, 'degree': float}},
                'moon_lagna':      {planet: {'sign': str, 'sign_idx': int, 'house': int, 'degree': float}},
                'sun_lagna':       {planet: {'sign': str, 'sign_idx': int, 'house': int, 'degree': float}},
            }
        """
        asc_idx = self._sign_idx_from_lon(asc_lon)
        moon_idx = self._planet_sign_idx(planet_lons, 'Moon')
        sun_idx = self._planet_sign_idx(planet_lons, 'Sun')

        refs = {
            'ascendant_lagna': asc_idx,
            'moon_lagna': moon_idx,
            'sun_lagna': sun_idx,
        }

        result = {}
        for chart_name, ref_idx in refs.items():
            chart = {}
            for planet, lon in planet_lons.items():
                p_sign_idx = self._sign_idx_from_lon(lon)
                house = self._house_from_refs(p_sign_idx, ref_idx)
                chart[planet] = {
                    'sign': SIGNS[p_sign_idx],
                    'sign_cn': SIGNS_CN[SIGNS[p_sign_idx]],
                    'sign_idx': p_sign_idx,
                    'house': house,
                    'degree': round(lon, 4),
                    'degree_in_sign': round(lon - p_sign_idx * 30, 4),
                }
            result[chart_name] = chart

        return result

    def composite_analysis(self, planet_lons: Dict, asc_lon: float) -> Dict:
        """
        分析每个行星在三张盘中的吉凶强度。

        对于每颗行星：
        - 统计三张盘中落入吉宫(1,2,3,4,5,7,9,10,11)的次数
        - 统计落入凶宫(6,8,12)的次数
        - 复合评分: favorable_count / 3 (0.0 ~ 1.0)

        Returns:
            {planet: {
                'asc_house': int, 'moon_house': int, 'sun_house': int,
                'favorable_count': int (0-3),
                'unfavorable_count': int (0-3),
                'composite_score': float (0.0-1.0),
                'interpretation': str
            }}
        """
        charts = self.generate_three_charts(planet_lons, asc_lon)

        result = {}
        for planet in planet_lons:
            if planet not in charts['ascendant_lagna']:
                continue

            asc_h = charts['ascendant_lagna'][planet]['house']
            moon_h = charts['moon_lagna'][planet]['house']
            sun_h = charts['sun_lagna'][planet]['house']

            houses = [asc_h, moon_h, sun_h]
            fav = sum(1 for h in houses if h in FAVORABLE_HOUSES)
            unfav = sum(1 for h in houses if h in UNFAVORABLE_HOUSES)
            score = fav / 3.0

            if fav == 3:
                interp = "三盘皆吉 — 该领域高度确认，力量极强"
            elif fav == 2 and unfav == 0:
                interp = "两盘吉、一中性 — 总体有利"
            elif fav == 2 and unfav == 1:
                interp = "两盘吉、一凶 — 有利但有隐患"
            elif fav == 1 and unfav == 2:
                interp = "一盘吉、两盘凶 — 矛盾信号，需结合大运判断"
            elif unfav == 3:
                interp = "三盘皆凶 — 该领域挑战极大"
            elif fav == 1 and unfav == 1:
                interp = "一吉一凶一中性 — 混合信号"
            elif unfav == 2:
                interp = "两盘凶 — 力量偏弱"
            else:
                interp = "中性 — 无明显吉凶偏向"

            result[planet] = {
                'asc_house': asc_h,
                'moon_house': moon_h,
                'sun_house': sun_h,
                'favorable_count': fav,
                'unfavorable_count': unfav,
                'composite_score': round(score, 3),
                'interpretation': interp,
            }

        return result

    def house_analysis(self, planet_lons: Dict, asc_lon: float, house_number: int) -> Dict:
        """
        分析指定宫位在三张盘中的情况。

        Returns:
            {
                'house': int,
                'meaning_cn': str,
                'meaning_en': str,
                'asc_lagna': {'planets': [...], 'lord': str, 'lord_house': int},
                'moon_lagna': {'planets': [...], 'lord': str, 'lord_house': int},
                'sun_lagna':  {'planets': [...], 'lord': str, 'lord_house': int},
                'composite_strength': float (0.0-1.0),
                'interpretation': str
            }
        """
        if not 1 <= house_number <= 12:
            return {'error': f'宫位号 {house_number} 超出范围(1-12)'}

        charts = self.generate_three_charts(planet_lons, asc_lon)

        def _analyze_house(chart: Dict, ref_sign_idx: int) -> Dict:
            """分析单个参考盘中某宫位"""
            # 该宫位对应的星座
            house_sign_idx = (ref_sign_idx + house_number - 1) % 12
            house_sign = SIGNS[house_sign_idx]
            lord = SIGN_LORDS[house_sign]

            # 该宫位中的行星
            planets_in_house = []
            for pname, pdata in chart.items():
                if pdata['house'] == house_number:
                    planets_in_house.append(pname)

            # 宫主星所在宫位
            lord_sign_idx = self._planet_sign_idx(planet_lons, lord) if lord in planet_lons else None
            lord_house = self._house_from_refs(lord_sign_idx, ref_sign_idx) if lord_sign_idx is not None else None

            return {
                'sign': house_sign,
                'sign_cn': SIGNS_CN[house_sign],
                'lord': lord,
                'lord_house': lord_house,
                'planets': planets_in_house,
            }

        asc_idx = self._sign_idx_from_lon(asc_lon)
        moon_idx = self._planet_sign_idx(planet_lons, 'Moon')
        sun_idx = self._planet_sign_idx(planet_lons, 'Sun')

        al = _analyze_house(charts['ascendant_lagna'], asc_idx)
        ml = _analyze_house(charts['moon_lagna'], moon_idx)
        sl = _analyze_house(charts['sun_lagna'], sun_idx)

        # 复合强度评分
        strength_components = []

        for ref_data in [al, ml, sl]:
            s = 0.0
            # 宫内有行星加分（尤其吉星）
            for p in ref_data['planets']:
                if p in ('Jupiter', 'Venus', 'Moon', 'Mercury'):
                    s += 0.2
                elif p in ('Saturn', 'Mars', 'Rahu', 'Ketu'):
                    s += 0.05
                else:
                    s += 0.1
            # 宫主星落入吉宫加分
            lh = ref_data.get('lord_house')
            if lh:
                if lh in FAVORABLE_HOUSES:
                    s += 0.3
                elif lh in UNFAVORABLE_HOUSES:
                    s += 0.05
                else:
                    s += 0.15
            strength_components.append(min(s, 1.0))

        composite_strength = round(sum(strength_components) / 3.0, 3)

        # 解读
        if composite_strength >= 0.7:
            interp = f"第{house_number}宫整体强势，三盘均支持该领域发展"
        elif composite_strength >= 0.4:
            interp = f"第{house_number}宫中等强度，部分参考盘有利，部分偏弱"
        else:
            interp = f"第{house_number}宫整体偏弱，该领域需更多努力与补救"

        meaning_cn, meaning_en = HOUSE_MEANINGS.get(house_number, ('未知', 'Unknown'))

        return {
            'house': house_number,
            'meaning_cn': meaning_cn,
            'meaning_en': meaning_en,
            'asc_lagna': al,
            'moon_lagna': ml,
            'sun_lagna': sl,
            'composite_strength': composite_strength,
            'interpretation': interp,
        }

    def life_area_analysis(self, planet_lons: Dict, asc_lon: float) -> Dict:
        """
        12个生活领域的综合分析。

        Returns:
            {area_name: {house: int, meaning_cn: str, composite_strength: float, details: dict, verdict: str}}
        """
        areas = {}
        for h in range(1, 13):
            ha = self.house_analysis(planet_lons, asc_lon, h)
            meaning_cn = ha.get('meaning_cn', f'第{h}宫')

            strength = ha['composite_strength']
            if strength >= 0.7:
                verdict = '强'
            elif strength >= 0.5:
                verdict = '中上'
            elif strength >= 0.35:
                verdict = '中'
            elif strength >= 0.2:
                verdict = '偏弱'
            else:
                verdict = '弱'

            areas[meaning_cn] = {
                'house': h,
                'meaning_cn': meaning_cn,
                'meaning_en': ha.get('meaning_en', ''),
                'composite_strength': strength,
                'asc_lagna': ha['asc_lagna'],
                'moon_lagna': ha['moon_lagna'],
                'sun_lagna': ha['sun_lagna'],
                'verdict': verdict,
            }

        return areas

    def generate_report(self, planet_lons: Dict, asc_lon: float, format: str = 'text') -> str:
        """
        生成人类可读的 Sudarshana Chakra 报告。

        Args:
            planet_lons: {planet: sidereal_longitude}
            asc_lon: sidereal ascendant longitude
            format: 'text' 或 'json'
        """
        charts = self.generate_three_charts(planet_lons, asc_lon)
        composite = self.composite_analysis(planet_lons, asc_lon)
        areas = self.life_area_analysis(planet_lons, asc_lon)

        if format == 'json':
            import json
            return json.dumps({
                'charts': charts,
                'composite_analysis': composite,
                'life_areas': areas,
            }, ensure_ascii=False, indent=2, default=str)

        # 文本报告
        asc_idx = self._sign_idx_from_lon(asc_lon)
        moon_idx = self._planet_sign_idx(planet_lons, 'Moon')
        sun_idx = self._planet_sign_idx(planet_lons, 'Sun')

        lines = []
        lines.append("=" * 60)
        lines.append("Sudarshana Chakra 三参考点盘分析")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"参考点:")
        lines.append(f"  上升 Lagna: {SIGNS[asc_idx]}({SIGNS_CN[SIGNS[asc_idx]]}) — 自我/身体")
        lines.append(f"  月亮 Lagna: {SIGNS[moon_idx]}({SIGNS_CN[SIGNS[moon_idx]]}) — 情感/心理")
        lines.append(f"  太阳 Lagna: {SIGNS[sun_idx]}({SIGNS_CN[SIGNS[sun_idx]]}) — 灵魂/生命力")
        lines.append("")

        # 三盘宫位一览
        lines.append("-" * 60)
        lines.append("行星在三盘中的宫位分布:")
        lines.append(f"{'行星':10s} {'上升盘':>6s} {'月亮盘':>6s} {'太阳盘':>6s} {'吉宫数':>6s} {'评分':>6s} {'解读'}")
        lines.append("-" * 60)
        for planet in planet_lons:
            if planet not in composite:
                continue
            c = composite[planet]
            lines.append(
                f"{planet:10s} {c['asc_house']:>6d} {c['moon_house']:>6d} {c['sun_house']:>6d} "
                f"{c['favorable_count']:>6d} {c['composite_score']:>6.2f} {c['interpretation']}"
            )
        lines.append("")

        # 12宫综合分析
        lines.append("-" * 60)
        lines.append("12宫生活领域综合评估:")
        lines.append(f"{'宫位':>4s} {'领域':18s} {'强度':>6s} {'判定':>6s} {'上升盘主星':>10s} {'月亮盘主星':>10s} {'太阳盘主星':>10s}")
        lines.append("-" * 60)
        for area_name, data in areas.items():
            h = data['house']
            al_lord = data['asc_lagna']['lord'] + f"(H{data['asc_lagna']['lord_house'] or '?'})"
            ml_lord = data['moon_lagna']['lord'] + f"(H{data['moon_lagna']['lord_house'] or '?'})"
            sl_lord = data['sun_lagna']['lord'] + f"(H{data['sun_lagna']['lord_house'] or '?'})"
            lines.append(
                f"{h:>4d} {area_name:18s} {data['composite_strength']:>6.2f} {data['verdict']:>6s} "
                f"{al_lord:>10s} {ml_lord:>10s} {sl_lord:>10s}"
            )
        lines.append("")

        # 收敛性分析
        lines.append("-" * 60)
        lines.append("三盘收敛性分析 (行星在至少两盘中落入同一宫位):")
        lines.append("-" * 60)
        convergences = self._find_convergences_text(charts)
        if convergences:
            for c in convergences:
                lines.append(f"  {c}")
        else:
            lines.append("  无显著收敛")
        lines.append("")

        # 总体评估
        scores = [c['composite_score'] for c in composite.values() if isinstance(c.get('composite_score'), (int, float))]
        avg_score = sum(scores) / len(scores) if scores else 0
        strong = sum(1 for s in scores if s >= 0.67)
        weak = sum(1 for s in scores if s <= 0.33)

        lines.append("=" * 60)
        lines.append("总体评估:")
        lines.append(f"  平均复合评分: {avg_score:.2f}")
        lines.append(f"  强势行星数(≥0.67): {strong}")
        lines.append(f"  弱势行星数(≤0.33): {weak}")
        if avg_score >= 0.6:
            lines.append("  总体判断: 盘面偏强，多数领域有支撑")
        elif avg_score >= 0.4:
            lines.append("  总体判断: 盘面中等，需结合大运看时机")
        else:
            lines.append("  总体判断: 盘面偏弱，需补救措施加强")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _find_convergences_text(self, charts: Dict) -> List[str]:
        """查找三盘收敛性，返回文本列表"""
        results = []
        for planet in self.seven_planets:
            if planet not in charts.get('ascendant_lagna', {}):
                continue
            al_h = charts['ascendant_lagna'][planet]['house']
            ml_h = charts['moon_lagna'][planet]['house']
            sl_h = charts['sun_lagna'][planet]['house']

            if al_h == ml_h == sl_h:
                results.append(f"{planet}: 三盘同宫(H{al_h}) ★★★ 强收敛")
            elif al_h == ml_h:
                results.append(f"{planet}: 上升盘=月亮盘(H{al_h}) ★★ 中收敛")
            elif al_h == sl_h:
                results.append(f"{planet}: 上升盘=太阳盘(H{al_h}) ★★ 中收敛")
            elif ml_h == sl_h:
                results.append(f"{planet}: 月亮盘=太阳盘(H{ml_h}) ★★ 中收敛")

        return results


# ============================================================================
# 便捷函数 — 供 jyotish_engine.py 调用
# ============================================================================

def calc_sudarshana_chakra(planet_lons: Dict, asc_lon: float,
                           house: int = None) -> Dict:
    """
    计算完整的 Sudarshana Chakra 分析。

    Args:
        planet_lons: {planet_name: sidereal_longitude_0_360}
        asc_lon: 上升点黄经 (sidereal, 0-360)
        house: 可选，指定分析某宫位 (1-12)

    Returns:
        完整分析结果字典
    """
    analyzer = SudarshanaChakraAnalyzer()

    charts = analyzer.generate_three_charts(planet_lons, asc_lon)
    composite = analyzer.composite_analysis(planet_lons, asc_lon)
    areas = analyzer.life_area_analysis(planet_lons, asc_lon)

    result = {
        'method': 'Sudarshana Chakra 三参考点盘 (BPHS标准)',
        'version': '2.0',
        'reference_points': {
            'ascendant_lagna': {
                'sign': SIGNS[analyzer._sign_idx_from_lon(asc_lon)],
                'sign_cn': SIGNS_CN[SIGNS[analyzer._sign_idx_from_lon(asc_lon)]],
                'role': '自我/身体',
            },
            'moon_lagna': {
                'sign': SIGNS[analyzer._planet_sign_idx(planet_lons, 'Moon')],
                'sign_cn': SIGNS_CN[SIGNS[analyzer._planet_sign_idx(planet_lons, 'Moon')]],
                'role': '情感/心理',
            },
            'sun_lagna': {
                'sign': SIGNS[analyzer._planet_sign_idx(planet_lons, 'Sun')],
                'sign_cn': SIGNS_CN[SIGNS[analyzer._planet_sign_idx(planet_lons, 'Sun')]],
                'role': '灵魂/生命力',
            },
        },
        'three_charts': charts,
        'composite_analysis': composite,
        'life_area_analysis': areas,
    }

    if house is not None:
        result['specific_house'] = analyzer.house_analysis(planet_lons, asc_lon, house)

    # 收敛性
    convergences = []
    for planet in analyzer.seven_planets:
        if planet not in charts.get('ascendant_lagna', {}):
            continue
        al_h = charts['ascendant_lagna'][planet]['house']
        ml_h = charts['moon_lagna'][planet]['house']
        sl_h = charts['sun_lagna'][planet]['house']
        if al_h == ml_h == sl_h:
            convergences.append({
                'planet': planet, 'house': al_h,
                'level': 'triple', 'significance': 'high',
            })
        elif al_h == ml_h or al_h == sl_h or ml_h == sl_h:
            match_h = al_h if al_h == ml_h or al_h == sl_h else ml_h
            convergences.append({
                'planet': planet, 'house': match_h,
                'level': 'double', 'significance': 'medium',
            })

    result['convergence'] = {
        'items': convergences,
        'high_confidence': [c for c in convergences if c['significance'] == 'high'],
        'medium_confidence': [c for c in convergences if c['significance'] == 'medium'],
    }

    # 总体评估
    scores = [c['composite_score'] for c in composite.values()]
    avg = sum(scores) / len(scores) if scores else 0
    strong = sum(1 for s in scores if s >= 0.67)
    weak = sum(1 for s in scores if s <= 0.33)

    if avg >= 0.6:
        overall = '盘面偏强，多数领域有支撑'
    elif avg >= 0.4:
        overall = '盘面中等，需结合大运看时机'
    else:
        overall = '盘面偏弱，需补救措施加强'

    result['overall_assessment'] = {
        'average_score': round(avg, 3),
        'strong_planets': strong,
        'weak_planets': weak,
        'judgment': overall,
    }

    return result


def generate_sudarshana_report(planet_lons: Dict, asc_lon: float) -> str:
    """生成文本报告"""
    analyzer = SudarshanaChakraAnalyzer()
    return analyzer.generate_report(planet_lons, asc_lon, format='text')
