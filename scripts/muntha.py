"""
Muntha (Varshaphala 年运盘核心指标) 计算模块
Jyotish Vedic Astrology Skill

Muntha 是 Tajika 年运盘（Varshaphala）中的核心指标，
代表该年度的"年度之主"，用于判断年度主旋律。

计算原理：
1. 计算太阳返照时间（Solar Return）——太阳回到出生太阳精确位置的时刻
2. 以太阳返照时刻排盘，得到 Varshaphala 年运盘
3. Muntha = 从年运盘太阳星座开始，向前数（当前年龄-1）mod 12 + 1 个星座
   Muntha 所在星座 = (Solar Return Sun sign + (age - 1) mod 12)
   如果结果 >= 12，则减 12

注意：不同流派对 Muntha 计算公式有微小差异。
本实现采用最广泛接受的方法。
"""
from typing import Dict, Optional
from datetime import datetime, timedelta


# 星座名称
SIGN_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']

# 星座守护星（用于判断 Muntha 守护星）
SIGN_LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
               'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']


def calc_muntha(solar_return_dt: datetime, birth_year: int, 
                age: Optional[int] = None) -> Dict:
    """
    计算 Muntha（年度之主）
    
    参数:
        solar_return_dt: 太阳返照时间（datetime）
        birth_year: 出生年份
        age: 当前年龄（可选，不提供则自动计算）
    
    返回:
        dict: {
            'muntha_sign': int,  # 0-11
            'muntha_sign_cn': str,
            'muntha_lord': str,  # 守护星
            'muntha_lord_cn': str,
            'solar_return_dt': str,  # 太阳返照时间
            'age_at_return': int,  # 返照时的年龄
            'calculation_note': str,
        }
    """
    if age is None:
        age = solar_return_dt.year - birth_year
    
    # 太阳返照盘中的太阳星座
    # 简化：假设 solar_return_dt 时刻的太阳黄道经度已计算好
    # 实际使用中，需要从 Varshaphala 盘数据获取太阳经度
    # 这里提供一个接口，接受太阳经度作为参数更合理
    
    return {
        'note': 'calc_muntha 需要 Varshaphala 盘的太阳经度，请使用 calc_muntha_from_sun_sign',
        'solar_return_dt': solar_return_dt.isoformat() if solar_return_dt else None,
    }


def calc_muntha_from_sun_sign(sun_sign_vp: int, age: int) -> Dict:
    """
    从 Varshaphala 盘太阳星座计算 Muntha
    
    参数:
        sun_sign_vp: Varshaphala 盘中太阳所在星座 (0-11)
        age: 该年度的年龄（年运盘对应的年龄）
    
    返回:
        dict: Muntha 信息
    """
    # Muntha 公式：(sun_sign_vp + (age - 1)) mod 12
    muntha_sign = (sun_sign_vp + (age - 1)) % 12
    muntha_lord = SIGN_LORDS[muntha_sign]
    muntha_lord_cn = {'Sun':'太阳','Moon':'月亮','Mars':'火星','Mercury':'水星',
                       'Jupiter':'木星','Venus':'金星','Saturn':'土星'}.get(muntha_lord, muntha_lord)
    
    return {
        'muntha_sign': muntha_sign,
        'muntha_sign_cn': SIGN_CN[muntha_sign],
        'muntha_lord': muntha_lord,
        'muntha_lord_cn': muntha_lord_cn,
        'age': age,
        'formula': f'(太阳星座{sun_sign_vp} + 年龄{age}-1) mod 12 = {muntha_sign}',
        'interpretation': _interpret_muntha(muntha_sign, muntha_lord),
    }


def _interpret_muntha(sign: int, lord: str) -> str:
    """Muntha 基础解读"""
    interpretations = {
        0: "Muntha 在白羊座：该年度精力充沛，主动开启新项目，可能有新的开始。",
        1: "Muntha 在金牛座：该年度注重财务和物质稳定，适合投资和积累。",
        2: "Muntha 在双子座：该年度沟通、学习、短途旅行活跃，信息处理量大。",
        3: "Muntha 在巨蟹座：该年度注重家庭、情感和安全感，家庭事务重要。",
        4: "Muntha 在狮子座：该年度创造力强，关注自我表达和子女，可能有创作项目。",
        5: "Muntha 在处女座：该年度注重健康、服务和日常工作，细节管理重要。",
        6: "Muntha 在天秤座：该年度注重关系、合作和伴侣，婚姻/合伙事务活跃。",
        7: "Muntha 在天蝎座：该年度深入转型，可能涉及财务共享、心理探索或危机处理。",
        8: "Muntha 在射手座：该年度注重高等学习、长途旅行、哲学/宗教事务。",
        9: "Muntha 在摩羯座：该年度注重事业、社会地位和长期规划，职业上有重要进展。",
        10: "Muntha 在水瓶座：该年度注重社交网络、团体活动和创新思维。",
        11: "Muntha 在双鱼座：该年度注重灵性、慈悲服务和潜意识探索。",
    }
    return interpretations.get(sign, f"Muntha 在 {SIGN_CN[sign]}")


def calc_yoga_from_muntha(muntha_sign: int, planet_lons_vp: Dict[str, float], 
                          house_data_vp: Dict) -> Dict:
    """
    基于 Muntha 的 Tajika Yoga 分析（Varshaphala 年运盘）
    
    分析 Muntha 与其他行星的 Tajika Yoga 关系（Ithasala/Easarapha 等）
    """
    from .tajika import calc_tajika_yogas  # 复用已有 Tajika Yoga 计算
    
    # 将 Muntha 视为一颗"虚拟行星"参与 Tajika Yoga 计算
    muntha_lon = muntha_sign * 30 + 15  # 取星座中点
    all_lons = dict(planet_lons_vp)
    all_lons['Muntha'] = muntha_lon
    
    yogas = calc_tajika_yogas(all_lons)
    
    # 筛选涉及 Muntha 的 Yoga
    muntha_yogas = []
    for y in yogas.get('yogas', []):
        if 'Muntha' in y.get('involved', []):
            muntha_yogas.append(y)
    
    return {
        'muntha_sign': muntha_sign,
        'muntha_lon': muntha_lon,
        'muntha_yogas': muntha_yogas,
        'all_yogas': yogas,
        'interpretation': _interpret_muntha_yogas(muntha_yogas),
    }


def _interpret_muntha_yogas(yogas: List[Dict]) -> str:
    """解读涉及 Muntha 的 Tajika Yoga"""
    if not yogas:
        return "Muntha 未形成显著的 Tajika Yoga，该年度主旋律较平稳。"
    
    lines = ["涉及 Muntha 的 Tajika Yoga："]
    for y in yogas:
        y_type = y.get('type', 'unknown')
        involved = y.get('involved', [])
        lines.append(f"  - {y_type}: {involved} → {y.get('interpretation', '')[:60]}")
    
    return "\n".join(lines)


# Varshaphala（太阳返照盘）辅助函数

def estimate_solar_return_ut(birth_sun_lon: float, target_year: int, 
                            tz_offset: float = 0) -> Dict:
    """
    估算太阳返照 UTC 时间（简化版）
    
    参数:
        birth_sun_lon: 出生太阳黄道经度
        target_year: 目标年份（计算该年的太阳返照）
        tz_offset: 时区偏移（小时），用于转换到本地时间
    
    返回:
        dict: {'utc_dt': datetime, 'local_dt': datetime, 'note': str}
    
    注意：这是估算值，精确计算需要天文算法（pyswisseph）。
    """
    # 简化：假设太阳每天移动 ~1°，找到太阳经度 = birth_sun_lon 的日期
    # 实际应使用 pyswisseph 的 swe_calc_ut 进行精确计算
    return {
        'note': '精确太阳返照时间计算需要 pyswisseph 支持，当前为估算值',
        'suggest': '使用 pyswisseph.swe_calc_ut 计算太阳精确位置，然后二分搜索',
    }


def muntha_full_analysis(vp_sun_sign: int, vp_age: int, 
                       vp_planet_lons: Dict[str, float], 
                       vp_houses: Dict) -> Dict:
    """
    Muntha 完整分析（Varshaphala 年运盘）
    
    参数:
        vp_sun_sign: Varshaphala 盘太阳星座 (0-11)
        vp_age: 年运盘对应年龄
        vp_planet_lons: Varshaphala 盘行星经度
        vp_houses: Varshaphala 盘宫位数据
    """
    # 1. 计算 Muntha
    muntha = calc_muntha_from_sun_sign(vp_sun_sign, vp_age)
    
    # 2. Muntha 在 Varshaphala 盘中的位置
    muntha_sign = muntha['muntha_sign']
    vp_house_of_muntha = None
    for h_num, h_data in vp_houses.items():
        if isinstance(h_data, dict) and h_data.get('sign') == muntha_sign:
            vp_house_of_muntha = int(h_num)
            break
        elif isinstance(h_data, int) and h_data == muntha_sign:
            vp_house_of_muntha = int(h_num)
            break
    
    # 3. Muntha Tajika Yoga 分析
    yoga_analysis = calc_yoga_from_muntha(muntha_sign, vp_planet_lons, vp_houses)
    
    # 4. 综合解读
    synthesis = _synthesize_muntha_analysis(
        muntha, vp_house_of_muntha, yoga_analysis
    )
    
    return {
        'muntha': muntha,
        'vp_house_of_muntha': vp_house_of_muntha,
        'yoga_analysis': yoga_analysis,
        'synthesis': synthesis,
        'method': 'Muntha (Tajika Varshaphala)',
        'note': 'Varshaphala 精确排盘需太阳返照时刻，建议配合 pyswisseph 使用',
    }


def _synthesize_muntha_analysis(muntha: Dict, vp_house: Optional[int], 
                                yoga: Dict) -> str:
    """综合解读 Muntha 分析"""
    lines = []
    m_sign_cn = muntha['muntha_sign_cn']
    m_lord_cn = muntha['muntha_lord_cn']
    
    lines.append(f"【Muntha 分析】")
    lines.append(f"  Muntha在 {m_sign_cn}，守护星 {m_lord_cn}")
    lines.append(f"  {muntha['interpretation']}")
    
    if vp_house:
        lines.append(f"  Varshaphala 盘中 Muntha 在第 {vp_house} 宫")
        if vp_house in [1,4,7,10]:
            lines.append(f"  → Muntha在角宫：该年度事件主导性强，主动权在握")
        elif vp_house in [2,5,8,11]:
            lines.append(f"  → Muntha在固定宫：该年度稳步积累，成果可持续")
        else:
            lines.append(f"  → Muntha在双体宫：该年度变化多，需灵活应对")
    
    lines.append(f"\n【Muntha Tajika Yoga】")
    lines.append(yoga['interpretation'])
    
    return "\n".join(lines)


if __name__ == '__main__':
    # 测试
    m = calc_muntha_from_sun_sign(0, 33)  # 太阳在白羊座，年龄33岁
    print("Muntha 测试：")
    print(m)
    print()
    a = muntha_full_analysis(0, 33, {'Sun': 15, 'Moon': 45, 'Jupiter': 90}, {1:0, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:9, 11:10, 12:11})
    print(a['synthesis'])
