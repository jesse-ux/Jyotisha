"""
Trimshamsa D30 分盘计算模块
Jyotish Vedic Astrology Skill

D30 (Trimsamsa，三十分盘）：
- 每个星座(30°)分为30等份（每份1°）
- 第1份(0-1°)→起始星座，第2份(1-2°)→下一星座，... 循环
- 用于分析灾难、苦难、重大危机事件

来源：Parashara Hora Shastra + 现代应用指南
"""
from typing import Dict, List, Optional


SIGN_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']

# D30 每个星座的起始映射（Parashara 规则）
# 白羊座30°÷30=1°/份，依次分配给12星座循环
# 份0(0-1°)→白羊，份1(1-2°)→金牛，...份11(11-12°)→双鱼，份12(12-13°)→白羊...
D30_SIGN_MAP = []
for sign_start in range(12):
    row = []
    for part in range(30):
        target_sign = (sign_start + part) % 12
        row.append(target_sign)
    D30_SIGN_MAP.append(row)


def calc_d30_sign(longitude: float) -> int:
    """
    计算 D30 分盘中的星座
    
    参数:
        longitude: 行星黄道经度 (0-360)
    返回:
        D30 中的星座序号 (0-11)
    """
    sign = int(longitude // 30)  # 本命星座 0-11
    deg_in_sign = longitude % 30      # 在星座内的度数 0-29.999
    part = int(deg_in_sign)           # 第几份 0-29
    
    d30_sign = D30_SIGN_MAP[sign][part]
    return d30_sign


def calc_d30_chart(planet_lons: Dict[str, float]) -> Dict:
    """
    计算完整 D30 分盘
    
    参数:
        planet_lons: 本命行星经度字典 {'Sun': lon, 'Moon': lon, ...}
    返回:
        dict: {'planets': {planet: {'d30_sign': int, 'd30_sign_cn': str}},
              'houses': {...}}  # 简化版暂不计算宫位
    """
    d30_planets = {}
    for pname, lon in planet_lons.items():
        d30_s = calc_d30_sign(lon)
        d30_planets[pname] = {
            'd30_longitude': d30_s * 30 + (lon % 30),  # 简化经度
            'd30_sign': d30_s,
            'd30_sign_cn': SIGN_CN[d30_s],
        }
    
    # 简化：不计算 D30 宫位（需要 D30 上升度）
    return {
        'chart': 'D30_Trimshamsa',
        'meaning': '灾难、苦难、重大危机、深层业力',
        'planets': d30_planets,
        'note': 'D30 宫位计算需要 D30 上升度（基于出生时间和地点），当前仅提供行星 D30 星座',
    }


def analyze_d30_marriage_crisis(d30_planets: Dict) -> Dict:
    """
    D30 婚姻危机分析（简化版）
    
    D30 中第7宫（伴侣）/第8宫（危机）/第12宫（损失）的行星状态
    用于判断婚姻中的深层危机模式
    """
    # 简化：检查金星、7宫主、12宫主在 D30 中的状态
    crisis_factors = []
    
    venus_d30 = d30_planets.get('Venus', {}).get('d30_sign')
    if venus_d30 is not None:
        crisis_factors.append(f"D30 金星在 {SIGN_CN[venus_d30]}")
    
    return {
        'd30_marriage_crisis': crisis_factors,
        'note': 'D30 完整分析需要 D30 宫位数据，建议使用专业软件（如 Jagannatha Hora）',
    }


def d30_full_report(birth_planet_lons: Dict[str, float]) -> Dict:
    """
    D30 完整报告（简化版）
    """
    d30 = calc_d30_chart(birth_planet_lons)
    crisis = analyze_d30_marriage_crisis(d30['planets'])
    
    return {
        'd30_chart': d30,
        'marriage_crisis': crisis,
        'interpretation': _d30_basic_interpretation(d30['planets']),
        'method': 'D30 Trimshamsa (Parashara)',
        'limitation': 'D30 是高级分盘，精确解读需配合 D30 宫位和其他分盘交叉验证',
    }


def _d30_basic_interpretation(d30_planets: Dict) -> str:
    """D30 基础解读"""
    lines = ["【D30 Trimshamsa 三十分盘分析】", ""]
    lines.append("D30 用于分析灾难、苦难、重大危机和深层业力模式。")
    lines.append("")
    
    # 重点行星
    key_planets = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
    for p in key_planets:
        p_data = d30_planets.get(p)
        if p_data:
            lines.append(f"{p} 在 D30：{p_data['d30_sign_cn']}")
    
    lines.append("")
    lines.append("⚠️ D30 解读需要高级技巧，建议：")
    lines.append("  1. 检查 D30 中凶星（火星/土星/罗睺/计都）是否集中在特定宫位")
    lines.append("  2. 与 D1/D9 交叉验证危机事件的时间线")
    lines.append("  3. 使用 Vimshottari Dasha 定位具体危机发生时期")
    
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
