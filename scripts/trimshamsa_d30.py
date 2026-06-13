"""
Trimshamsa D30 分盘计算模块 v7.0
Jyotish Vedic Astrology Skill

D30 (Trimsamsa，三十分盘）：
- 基于Parashara经典规则（非简单线性循环）
- 奇数星座和偶数星座有不同的度数分配表
- 用于分析灾难、苦难、重大危机事件

来源：Parashara Hora Shastra + jyotishganit divisional_charts.py (MIT)

v7.0 修正：
- 修正D30计算：使用Parashara奇偶星座规则（而非简单30等分循环）
- 添加完整行星状态分析（入庙/落陷/友宫/敌宫）
- 添加D30宫位推算
- 添加D30凶星集中度分析
"""
from typing import Dict, List, Optional


SIGN_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']

SIGN_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

SIGN_LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
              'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

# D30 Parashara 规则（参考jyotishganit trimsamsa_from_long）
# 奇数星座(Odd signs: Aries,Gemini,Leo,Libra,Sagittarius,Aquarius):
#   0-5°  → Aries(0), 5-10° → Aquarius(10), 10-18° → Sagittarius(8),
#   18-25° → Gemini(2), 25-30° → Libra(6)
# 偶数星座(Even signs: Taurus,Cancer,Virgo,Scorpio,Capricorn,Pisces):
#   0-5°  → Taurus(1), 5-12° → Virgo(5), 12-19° → Capricorn(9),
#   19-24° → Pisces(11), 24-30° → Scorpio(7)

D30_ODD_RANGES = [
    (0, 5, 0),     # 0-5°  → Aries
    (5, 10, 10),   # 5-10° → Aquarius
    (10, 18, 8),   # 10-18° → Sagittarius
    (18, 25, 2),   # 18-25° → Gemini
    (25, 30, 6),   # 25-30° → Libra
]

D30_EVEN_RANGES = [
    (0, 5, 1),     # 0-5°  → Taurus
    (5, 12, 5),    # 5-12° → Virgo
    (12, 19, 9),   # 12-19° → Capricorn
    (19, 24, 11),  # 19-24° → Pisces
    (24, 30, 7),   # 24-30° → Scorpio
]


def calc_d30_sign(longitude: float) -> int:
    """
    计算 D30 分盘中的星座 v7.0（Parashara 规则）

    参数:
        longitude: 行星黄道经度 (0-360)
    返回:
        D30 中的星座序号 (0-11)
    """
    sign = int(longitude // 30)  # 本命星座 0-11
    deg_in_sign = longitude % 30  # 在星座内的度数 0-29.999

    is_odd = (sign % 2 == 0)  # 0-based: Aries(0)=odd, Taurus(1)=even...

    if is_odd:
        # 奇数星座规则
        for start, end, target in D30_ODD_RANGES:
            if start <= deg_in_sign < end:
                return target
    else:
        # 偶数星座规则
        for start, end, target in D30_EVEN_RANGES:
            if start <= deg_in_sign < end:
                return target

    # 回退（不应到达）
    return sign


def calc_d30_chart(planet_lons: Dict[str, float], asc_lon: float = None) -> Dict:
    """
    计算完整 D30 分盘 v7.0

    参数:
        planet_lons: 本命行星经度字典 {'Sun': lon, 'Moon': lon, ...}
        asc_lon: D1上升经度(可选，用于推算D30宫位)
    返回:
        dict: 完整D30数据（含宫位推算和行星状态分析）
    """
    d30_planets = {}
    for pname, lon in planet_lons.items():
        d30_s = calc_d30_sign(lon)
        # 计算D30中的经度（保留原始度数在D30星座内的映射）
        deg_in_d1_sign = lon % 30
        d30_planets[pname] = {
            'd30_sign': d30_s,
            'd30_sign_name': SIGN_NAMES[d30_s],
            'd30_sign_cn': SIGN_CN[d30_s],
            'd30_lord': SIGN_LORDS[d30_s],
            'd1_degree_in_sign': round(deg_in_d1_sign, 2),
        }

    # 推算D30上升和宫位
    d30_asc = None
    d30_houses = {}
    if asc_lon is not None:
        d30_asc = calc_d30_sign(asc_lon)
        d30_asc_name = SIGN_NAMES[d30_asc]
        for h in range(1, 13):
            sign_idx = (d30_asc + h - 1) % 12
            d30_houses[h] = {
                'sign': SIGN_NAMES[sign_idx],
                'sign_cn': SIGN_CN[sign_idx],
                'lord': SIGN_LORDS[sign_idx],
            }
        # 映射行星到D30宫位
        for pname, pdata in d30_planets.items():
            p_sign = pdata['d30_sign']
            house = ((p_sign - d30_asc) % 12) + 1
            pdata['d30_house'] = house

    # 行星状态分析
    planet_states = _analyze_d30_planet_states(d30_planets)

    # 凶星集中度分析
    malefic_concentration = _analyze_malefic_concentration(d30_planets, d30_houses)

    return {
        'chart': 'D30_Trimshamsa',
        'meaning': '灾难、苦难、重大危机、深层业力',
        'method': 'Parashara经典规则（奇偶星座分区法）',
        'planets': d30_planets,
        'd30_ascendant': {
            'sign': SIGN_NAMES[d30_asc] if d30_asc is not None else None,
            'sign_cn': SIGN_CN[d30_asc] if d30_asc is not None else None,
        } if d30_asc is not None else None,
        'd30_houses': d30_houses if d30_houses else None,
        'planet_states': planet_states,
        'malefic_concentration': malefic_concentration,
    }


def analyze_d30_marriage_crisis(d30_planets: Dict, d30_houses: Dict = None) -> Dict:
    """
    D30 婚姻危机分析 v7.0

    D30 中第7宫（伴侣）/第8宫（危机）/第12宫（损失）的行星状态
    用于判断婚姻中的深层危机模式
    """
    crisis_factors = []
    crisis_score = 0

    # Venus在D30的状态
    venus_d30 = d30_planets.get('Venus', {})
    if venus_d30:
        v_sign = venus_d30.get('d30_sign')
        v_house = venus_d30.get('d30_house')
        crisis_factors.append(f"D30 Venus在{SIGN_CN[v_sign]}")
        if v_house and v_house in [6, 8, 12]:
            crisis_score += 2
            crisis_factors.append(f"  Venus在D30第{v_house}宫 → 婚姻受克")
        elif v_house and v_house in [1, 4, 7, 10]:
            crisis_score -= 1
            crisis_factors.append(f"  Venus在D30第{v_house}宫(角宫) → 婚姻较稳")

    # Mars在D30的状态
    mars_d30 = d30_planets.get('Mars', {})
    if mars_d30:
        m_sign = mars_d30.get('d30_sign')
        m_house = mars_d30.get('d30_house')
        if m_house and m_house == 7:
            crisis_score += 2
            crisis_factors.append(f"  Mars在D30第7宫 → 伴侣冲突/暴力风险")
        elif m_house and m_house == 8:
            crisis_score += 1
            crisis_factors.append(f"  Mars在D30第8宫 → 婚姻中突发危机")

    # Saturn在D30的状态
    sat_d30 = d30_planets.get('Saturn', {})
    if sat_d30:
        s_house = sat_d30.get('d30_house')
        if s_house and s_house == 7:
            crisis_score += 1
            crisis_factors.append(f"  Saturn在D30第7宫 → 婚姻延迟/冷漠")

    # D30 8宫检查
    if d30_houses:
        h8_lord = d30_houses.get(8, {}).get('lord')
        if h8_lord:
            crisis_factors.append(f"D30 第8宫主：{h8_lord}")

    # 综合评估
    if crisis_score >= 4:
        severity = "严重（婚姻危机风险高，需专业咨询）"
    elif crisis_score >= 2:
        severity = "中等（婚姻中有挑战，需主动经营）"
    elif crisis_score >= 0:
        severity = "轻微（婚姻危机风险低）"
    else:
        severity = "极低（婚姻较稳定）"

    return {
        'd30_marriage_crisis': crisis_factors,
        'crisis_score': crisis_score,
        'severity': severity,
    }


def _analyze_d30_planet_states(d30_planets: Dict) -> Dict:
    """D30 行星状态分析"""
    states = {}
    # 擢升/落陷星座表
    EXALTATION = {'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
                  'Jupiter': 3, 'Venus': 11, 'Saturn': 6}
    DEBILITATION = {'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
                    'Jupiter': 9, 'Venus': 5, 'Saturn': 0}
    OWN = {'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
           'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]}

    for pname, pdata in d30_planets.items():
        d30_sign = pdata.get('d30_sign')
        if d30_sign is None or pname not in EXALTATION:
            continue

        state = 'neutral'
        if d30_sign == EXALTATION.get(pname, -1):
            state = 'exalted'
        elif d30_sign == DEBILITATION.get(pname, -1):
            state = 'debilitated'
        elif d30_sign in OWN.get(pname, []):
            state = 'own'

        states[pname] = {
            'd30_sign': SIGN_NAMES[d30_sign],
            'state': state,
            'significance': _d30_state_significance(pname, state),
        }

    return states


def _d30_state_significance(planet: str, state: str) -> str:
    """D30中行星状态的解读"""
    if state == 'exalted':
        return f'{planet}在D30擢升 → 该行星能量在危机中表现为正面转化力'
    elif state == 'debilitated':
        return f'{planet}在D30落陷 → 该行星能量在危机中表现为负面放大'
    elif state == 'own':
        return f'{planet}在D30入庙 → 该行星能量在危机中表现稳定'
    return f'{planet}在D30中性 → 危机中表现取决于其他因素'


def _analyze_malefic_concentration(d30_planets: Dict, d30_houses: Dict) -> Dict:
    """D30 凶星集中度分析"""
    MALEFICS = {'Mars', 'Saturn', 'Rahu', 'Ketu', 'Sun'}
    concentration = {}

    # 按星座统计凶星
    sign_malefics = {}
    for pname in MALEFICS:
        pdata = d30_planets.get(pname)
        if pdata:
            s = pdata.get('d30_sign')
            if s is not None:
                sign_malefics.setdefault(s, []).append(pname)

    # 找出凶星集中度最高的星座
    for sign_idx, planets in sign_malefics.items():
        if len(planets) >= 2:
            concentration[SIGN_NAMES[sign_idx]] = {
                'malefics': planets,
                'count': len(planets),
                'severity': 'high' if len(planets) >= 3 else 'moderate',
            }

    # 按宫位统计（如果有宫位数据）
    if d30_houses:
        house_malefics = {}
        for pname in MALEFICS:
            pdata = d30_planets.get(pname)
            if pdata:
                h = pdata.get('d30_house')
                if h:
                    house_malefics.setdefault(h, []).append(pname)
        for house, planets in house_malefics.items():
            if len(planets) >= 2:
                concentration[f'House_{house}'] = {
                    'malefics': planets,
                    'count': len(planets),
                    'severity': 'high' if house in [6, 8, 12] else 'moderate',
                }

    return concentration


def d30_full_report(birth_planet_lons: Dict[str, float], asc_lon: float = None) -> Dict:
    """
    D30 完整报告 v7.0
    """
    d30 = calc_d30_chart(birth_planet_lons, asc_lon)
    crisis = analyze_d30_marriage_crisis(
        d30['planets'],
        d30.get('d30_houses')
    )

    return {
        'd30_chart': d30,
        'marriage_crisis': crisis,
        'interpretation': _d30_full_interpretation(d30, crisis),
        'method': 'D30 Trimshamsa (Parashara经典规则)',
    }


def _d30_full_interpretation(d30_data: Dict, crisis_data: Dict) -> str:
    """D30 完整解读 v7.0"""
    lines = ["【D30 Trimshamsa 三十分盘分析】", ""]
    lines.append("D30 用于分析灾难、苦难、重大危机和深层业力模式。")
    lines.append(f"计算方法：Parashara经典规则（奇偶星座分区法）")
    lines.append("")

    # 上升信息
    asc = d30_data.get('d30_ascendant')
    if asc and asc.get('sign_cn'):
        lines.append(f"D30 上升：{asc['sign_cn']} ({asc['sign']})")
        lines.append("")

    # 行星状态
    states = d30_data.get('planet_states', {})
    lines.append("#### 行星在D30中的状态")
    for pname, sdata in states.items():
        state_cn = {'exalted': '擢升', 'debilitated': '落陷', 'own': '入庙', 'neutral': '中性'}
        lines.append(f"  {pname}: {sdata['d30_sign']} ({state_cn.get(sdata['state'], sdata['state'])})")
    lines.append("")

    # 凶星集中度
    concentration = d30_data.get('malefic_concentration', {})
    if concentration:
        lines.append("#### 凶星集中度")
        for area, data in concentration.items():
            lines.append(f"  {area}: {data['malefics']} (集中度={data['severity']})")
        lines.append("")

    # 婚姻危机
    if crisis_data.get('crisis_factors'):
        lines.append(f"#### 婚姻危机评估: {crisis_data.get('severity', '未知')}")
        for f in crisis_data['crisis_factors']:
            lines.append(f"  {f}")
        lines.append("")

    lines.append("注意：")
    lines.append("  1. D30中凶星集中 = 危机高发领域")
    lines.append("  2. 与D1/D9交叉验证危机事件的时间线")
    lines.append("  3. 使用Vimshottari Dasha定位具体危机发生时期")

    return "\n".join(lines)


# 便捷函数
def get_d30_sign(lon: float) -> int:
    """便捷函数：获取 D30 星座"""
    return calc_d30_sign(lon)


if __name__ == '__main__':
    # 测试
    test_lons = {'Sun': 28.5, 'Moon': 65.2, 'Mars': 120.8, 
                 'Mercury': 29.9, 'Jupiter': 185.3, 'Venus': 210.7, 
                 'Saturn': 300.1, 'Rahu': 88.4, 'Ketu': 268.4}
    report = d30_full_report(test_lons)
    print(report['interpretation'])
