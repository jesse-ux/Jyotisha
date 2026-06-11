#!/usr/bin/env python3
"""
分盘Yoga识别引擎 (v6.9.0)
在D9(Navamsa)、D10(Dasamsa)等分盘中运行Yoga检测。
分盘中的Yoga可以提供更精细的解读维度。

基于BPHS标准：Yoga在分盘中成立条件更严格，
因为分盘本身就是主盘的细化。
"""
from typing import Dict, List
import sys, os

# 星座常量
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}


def _calc_navamsa_position(planet_lon: float) -> tuple:
    """计算行星在D9(Navamsa)中的位置"""
    sign_idx = int(planet_lon / 30) % 12
    deg_in_sign = planet_lon % 30
    navamsa_size = 30.0 / 9  # 3°20'
    navamsa_idx = int(deg_in_sign / navamsa_size)
    # D9中星座映射（基于sign_index和navamsa_idx的BPHS规则）
    if sign_idx in (0, 4, 8):  # Fire: Aries, Leo, Sagittarius
        d9_sign = (0 + navamsa_idx) % 12
    elif sign_idx in (1, 5, 9):  # Earth: Taurus, Virgo, Capricorn
        d9_sign = (9 + navamsa_idx) % 12
    elif sign_idx in (2, 6, 10):  # Air: Gemini, Libra, Aquarius
        d9_sign = (6 + navamsa_idx) % 12
    else:  # Water: Cancer, Scorpio, Pisces
        d9_sign = (3 + navamsa_idx) % 12
    return d9_sign, (deg_in_sign % navamsa_size) * 9


def _calc_dasamsa_position(planet_lon: float) -> tuple:
    """计算行星在D10(Dasamsa)中的位置"""
    sign_idx = int(planet_lon / 30) % 12
    deg_in_sign = planet_lon % 30
    dasamsa_size = 30.0 / 10  # 3°
    dasamsa_idx = int(deg_in_sign / dasamsa_size)
    if sign_idx % 2 == 0:  # Odd signs
        d10_sign = (sign_idx + dasamsa_idx) % 12
    else:
        d10_sign = (sign_idx + 9 + dasamsa_idx) % 12
    return d10_sign, (deg_in_sign % dasamsa_size) * 10


def _calc_dvadasamsa_position(planet_lon: float) -> tuple:
    """计算行星在D12(Dvadasamsa)中的位置"""
    sign_idx = int(planet_lon / 30) % 12
    deg_in_sign = planet_lon % 30
    d12_size = 30.0 / 12  # 2°30'
    d12_idx = int(deg_in_sign / d12_size)
    d12_sign = (sign_idx * 12 + d12_idx) % 12
    return d12_sign, (deg_in_sign % d12_size) * 12


def convert_to_varga(planets: Dict, varga: str = 'D9') -> Dict:
    """
    将行星位置转换到分盘中。

    Args:
        planets: {planet_name: {'lon': float, 'sign': str}} 或 {planet_name: float}
        varga: 'D9' | 'D10' | 'D12' | 'D16' | 'D20' | 'D24' | 'D27' | 'D30'

    Returns:
        {planet_name: {'sign': str, 'sign_idx': int, 'degree': float, 'house': int}}
    """
    calc_fn = {
        'D9': _calc_navamsa_position,
        'D10': _calc_dasamsa_position,
        'D12': _calc_dvadasamsa_position,
    }.get(varga, _calc_navamsa_position)

    result = {}
    for pname, pdata in planets.items():
        if isinstance(pdata, dict):
            lon = pdata.get('lon', pdata.get('degree', 0))
        else:
            lon = float(pdata)

        sign_idx, degree = calc_fn(lon % 360)
        sign = SIGNS[sign_idx]
        result[pname] = {'sign': sign, 'sign_idx': sign_idx, 'degree': round(degree, 2)}

    return result


def detect_varga_yogas(planets: Dict, varga: str = 'D9', asc_sign: str = None) -> List[Dict]:
    """
    在指定分盘中检测Yoga。

    检测规则（适用于分盘）：
    1. Mahapurusha检测：行星在分盘中的Kendra并位于own/exalted sign
    2. Raja Yoga：Kendra-Kona lord conjunction
    3. Dhana Yoga：2H-11H lord connection
    4. Moon Yogas：基于分盘Moon位置

    Args:
        planets: 原始行星数据(含经度)
        varga: 分盘名称
        asc_sign: 分盘上升星座(可选)

    Returns:
        [{'name': str, 'type': str, 'planets': list, 'strength': str, 'description': str}]
    """
    varga_planets = convert_to_varga(planets, varga)
    yogas = []

    # 1. 检测分盘中的PMC
    pmc = _detect_pmc_in_varga(varga_planets)
    yogas.extend(pmc)

    # 2. 检测分盘中的Kendra-Kona连接
    raja = _detect_raja_in_varga(varga_planets)
    yogas.extend(raja)

    # 3. 检测分盘中的Dhana
    dhana = _detect_dhana_in_varga(varga_planets)
    yogas.extend(dhana)

    # 4. 检测分盘中的Moon相关Yoga
    moon = _detect_moon_varga_yogas(varga_planets)
    yogas.extend(moon)

    # 5. 检测Exchange (Parivartana)
    exchange = _detect_exchange_in_varga(varga_planets)
    yogas.extend(exchange)

    return yogas


def _get_varga_lords(planets: Dict) -> Dict[str, str]:
    """获取分盘中每颗行星的主星"""
    lords = {}
    for pname, pdata in planets.items():
        sign = pdata.get('sign', '')
        lords[pname] = SIGN_LORDS.get(sign, '')
    return lords


def _detect_pmc_in_varga(varga_planets: Dict) -> List[Dict]:
    """分盘中的PMC检测（简化）"""
    yogas = []
    pmc_configs = {
        'Mars': {'sign': 'Capricorn', 'name': 'Ruchaka', 'house_need': (1, 4, 7, 10)},
        'Mercury': {'sign': 'Virgo', 'name': 'Bhadra', 'house_need': (1, 4, 7, 10)},
        'Jupiter': {'sign': 'Cancer', 'name': 'Hamsa', 'house_need': (1, 4, 7, 10)},
        'Venus': {'sign': 'Pisces', 'name': 'Malavya', 'house_need': (1, 4, 7, 10)},
        'Saturn': {'sign': 'Aquarius', 'name': 'Shasha', 'house_need': (1, 4, 7, 10)},
    }
    for planet, config in pmc_configs.items():
        if planet in varga_planets:
            pd = varga_planets[planet]
            if pd.get('sign') in (config['sign'], SIGN_LORDS.get(config['sign'], '')):
                yogas.append({
                    'name': f'{config["name"]} (在分盘中)',
                    'type': 'PMC_varga',
                    'planets': [planet],
                    'strength': '中等（分盘中成立）',
                    'description': f'{planet}在分盘中位于{config["sign"]}形成{config["name"]} Yoga',
                })
    return yogas


def _detect_raja_in_varga(varga_planets: Dict) -> List[Dict]:
    """分盘中的Raja Yoga检测"""
    yogas = []
    lords = _get_varga_lords(varga_planets)

    # Kendra (1,4,7,10) lord + Kona (1,5,9) lord 在同一宫
    kendra_lords = set()
    kona_lords = set()
    for pn, pd in varga_planets.items():
        h = pd.get('house', 0)
        if h in (1, 4, 7, 10):
            kendra_lords.add(pn)
        if h in (1, 5, 9):
            kona_lords.add(pn)

    # Kendra lord 和 Kona lord 形成关联
    for kl in kendra_lords:
        for kn in kona_lords:
            if kl != kn:
                kl_sign = varga_planets.get(kl, {}).get('sign', '')
                kn_sign = varga_planets.get(kn, {}).get('sign', '')
                if kl_sign and kl_sign == kn_sign:
                    yogas.append({
                        'name': 'Raja Yoga (分盘)',
                        'type': 'raja_varga',
                        'planets': [kl, kn],
                        'strength': '强（分盘中Kendra-Kona lord合相）',
                        'description': f'{kl}(Kendra主)和{kn}(Kona主)在分盘中合相于{kl_sign}',
                    })
    return yogas


def _detect_dhana_in_varga(varga_planets: Dict) -> List[Dict]:
    """分盘中的Dhana Yoga"""
    yogas = []
    lords = _get_varga_lords(varga_planets)

    # 2H lord 和 11H lord 的连接
    h2_lord = h11_lord = None
    for pn, pd in varga_planets.items():
        h = pd.get('house', 0)
        if h == 2:
            h2_lord = pn
        if h == 11:
            h11_lord = pn

    if h2_lord and h11_lord:
        h2_sign = varga_planets[h2_lord].get('sign', '')
        h11_sign = varga_planets[h11_lord].get('sign', '')
        if h2_sign == h11_sign:
            yogas.append({
                'name': 'Dhana Yoga (分盘)',
                'type': 'dhana_varga',
                'planets': [h2_lord, h11_lord],
                'strength': '强（2H-11H lord连接）',
                'description': f'分盘中2H主{h2_lord}和11H主{h11_lord}形成Dhana Yoga',
            })
    return yogas


def _detect_moon_varga_yogas(varga_planets: Dict) -> List[Dict]:
    """分盘中Moon的Yoga"""
    yogas = []
    if 'Moon' not in varga_planets:
        return yogas

    moon = varga_planets['Moon']
    moon_sign = moon.get('sign', '')

    # Kemadruma检查
    has_neighbor = False
    for pn in ['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']:
        if pn in varga_planets:
            ps = varga_planets[pn]
            if ps.get('house', 0) in (moon.get('house', 0) - 1, moon.get('house', 0) + 1):
                has_neighbor = True
                break
    if not has_neighbor:
        yogas.append({
            'name': 'Kemadruma (分盘)',
            'type': 'moon_varga',
            'planets': ['Moon'],
            'strength': '挑战（分盘月独）',
            'description': f'分盘Moon在{moon_sign}无邻星，形成Kemadruma',
        })

    return yogas


def _detect_exchange_in_varga(varga_planets: Dict) -> List[Dict]:
    """分盘中的星座交换（Parivartana）"""
    yogas = []
    lords = _get_varga_lords(varga_planets)
    checked = set()

    for p1 in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        for p2 in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
            if p1 >= p2:
                continue
            if p1 not in varga_planets or p2 not in varga_planets:
                continue
            if (p1, p2) in checked:
                continue
            checked.add((p1, p2))

            s1 = varga_planets[p1].get('sign', '')
            s2 = varga_planets[p2].get('sign', '')
            if SIGN_LORDS.get(s1, '') == p2 and SIGN_LORDS.get(s2, '') == p1:
                yogas.append({
                    'name': 'Parivartana (分盘)',
                    'type': 'exchange_varga',
                    'planets': [p1, p2],
                    'strength': '强（星座交换）',
                    'description': f'{p1}({s1})和{p2}({s2})在分盘中形成Parivartana Yoga',
                })

    return yogas


def varga_yoga_report(planets: Dict, vargas: List[str] = None) -> Dict:
    """
    生成多分盘Yoga综合报告。

    Args:
        planets: 原始行星数据
        vargas: 要检查的分盘列表

    Returns:
        {'D9': [yoga_list], 'D10': [yoga_list], 'summary': str}
    """
    if vargas is None:
        vargas = ['D9', 'D10']

    report = {}
    total = 0
    for v in vargas:
        yogas = detect_varga_yogas(planets, v)
        report[v] = yogas
        total += len(yogas)

    report['total_varga_yogas'] = total
    report['vargas_checked'] = vargas
    report['summary'] = f"在{len(vargas)}个分盘中发现{total}个Yoga"
    return report
