"""
Marriage Counting Method (婚姻计数法) —— Bhrigu 体系 v7.0
Jyotish Vedic Astrology Skill

来源：bhrigu-pada-dasha-marriage-counting.md
算法：D1 第7宫主在 D1 的星座(A) → D9 的星座(B) → 从A数到B = 婚姻次数

v7.0 新增：
- Parivartana自动重算（原为TODO）
- D9 Venus/Mars/7宫主完整状态评估
- Upapada Loga整合
- 每段关系的质量预测
"""
from typing import Dict, Optional, List


# 星座名称
SIGN_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']


def sign_of(lon: float) -> int:
    """从黄道经度计算星座序号 (0-11)"""
    return int((lon % 360) / 30)


def marriage_counting_method(
    d1_house7_lord: str,
    d1_planet_lons: Dict[str, float],
    d9_planet_lons: Dict[str, float],
    d1_houses: Optional[Dict] = None,
    d9_houses: Optional[Dict] = None,
    parivartana_check: bool = True
) -> Dict:
    """
    婚姻计数法 (Marriage Counting Method)
    
    参数:
        d1_house7_lord: D1 第7宫主星名称 (如 'Venus')
        d1_planet_lons: D1 行星经度字典
        d9_planet_lons: D9 行星经度字典
        d1_houses: D1 宫位数据 (可选，用于 Parivartana 检查)
        d9_houses: D9 宫位数据 (可选)
        parivartana_check: 是否检查 Parivartana (默认 True)
    
    返回:
        dict: {
            'method': 'Marriage Counting Method',
            'd1_7th_lord': str,
            'point_A': {'sign': int, 'sign_cn': str},  # D1 中7宫主星座
            'point_B': {'sign': int, 'sign_cn': str},  # D9 中7宫主星座
            'distance': int,  # 从A数到B (包含A和B)
            'marriage_count': int,  # 婚姻/认真关系数量
            'interpretation': str,  # 解读
            'parivartana': dict or None,  # Parivartana 检查结果
            'warnings': list,
        }
    """
    warnings = []
    
    # Step 1: 找到 D1 第7宫主
    if not d1_house7_lord:
        return {'error': '未提供 D1 第7宫主', 'method': 'Marriage Counting Method'}
    
    # Step 2: 找到 7宫主在 D1 中的星座 (A)
    if d1_house7_lord not in d1_planet_lons:
        warnings.append(f"D1 中未找到 {d1_house7_lord} 的位置")
        return {'error': f"D1 中未找到 {d1_house7_lord}", 'method': 'Marriage Counting Method'}
    
    d1_lon = d1_planet_lons[d1_house7_lord]
    point_A = sign_of(d1_lon)
    
    # Step 3: 找到 7宫主在 D9 中的星座 (B)
    if d1_house7_lord not in d9_planet_lons:
        warnings.append(f"D9 中未找到 {d1_house7_lord} 的位置")
        return {'error': f"D9 中未找到 {d1_house7_lord}", 'method': 'Marriage Counting Method'}
    
    d9_lon = d9_planet_lons[d1_house7_lord]
    point_B = sign_of(d9_lon)
    
    # Parivartana 检查
    parivartana = None
    if parivartana_check and d1_houses:
        parivartana = _check_parivartana(
            d1_house7_lord, point_A, d1_houses, d1_planet_lons
        )
        if parivartana and parivartana.get('has_parivartana'):
            # v7.0: 实现 Parivartana 后的自动重算
            # Parivartana = 两星交换星座，需用交换后的位置重新计算
            swapped_lord = parivartana['planet2']  # 7宫主的交换对象
            swapped_sign = parivartana.get('planet2_sign', point_A)

            # 用交换后的星座作为新的 Point A
            point_A_swapped = swapped_sign

            # 重新计算距离
            if point_B >= point_A_swapped:
                distance_swapped = point_B - point_A_swapped + 1
            else:
                distance_swapped = (11 - point_A_swapped + 1) + (point_B + 1)

            warnings.append(
                f"Parivartana（行星交换）！{d1_house7_lord} 与 {swapped_lord} 交换。"
                f" 原计数={distance}，交换后计数={distance_swapped}。"
                f" 以交换后计数为准。"
            )
            # 使用交换后的结果
            distance = distance_swapped
    
    # Step 4: 计数 (从 A 到 B，包含 A 和 B)
    if point_B >= point_A:
        distance = point_B - point_A + 1
    else:
        # 跨越白羊座0°: 从 A 到双鱼座(11) + 从白羊座(0) 到 B
        distance = (11 - point_A + 1) + (point_B + 1)
    
    marriage_count = distance
    
    # 解读
    interpretation = _interpret_marriage_count(marriage_count, point_A, point_B)
    
    return {
        'method': 'Marriage Counting Method (Bhrigu)',
        'd1_7th_lord': d1_house7_lord,
        'point_A': {
            'sign': point_A,
            'sign_cn': SIGN_CN[point_A],
            'degree': d1_lon,
        },
        'point_B': {
            'sign': point_B,
            'sign_cn': SIGN_CN[point_B],
            'degree': d9_lon,
        },
        'distance': distance,
        'marriage_count': marriage_count,
        'interpretation': interpretation,
        'parivartana': parivartana,
        'warnings': warnings,
    }


def _check_parivartana(
    lord: str,
    lord_sign: int,
    d1_houses: Dict,
    d1_planet_lons: Dict[str, float]
) -> Dict:
    """
    检查 7宫主是否与其落入星座的主星有 Parivartana（行星交换）
    
    返回: {'has_parivartana': bool, 'planet1': str, 'planet2': str, ...}
    """
    # 找到 lord 落入星座的主星
    SIGN_LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
                   'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']
    host = SIGN_LORDS[lord_sign]  # lord 落入星座的主星

    # 落在自己掌管的星座不是 Parivartana（行星交换），只是 own-sign 状态。
    if host == lord:
        return {'has_parivartana': False, 'reason': f'{lord} 位于自己掌管的星座，不构成 Parivartana'}

    if host not in d1_planet_lons:
        return {'has_parivartana': False, 'reason': f'{host} 位置未知'}
    
    host_sign = sign_of(d1_planet_lons[host])
    lord_own_sign = sign_of(d1_planet_lons.get(lord, 0))
    
    # Parivartana: lord 在 host 的星座里，host 在 lord 的星座里
    if host_sign == lord_own_sign and lord_sign == sign_of(d1_planet_lons.get(host, 0)):
        return {
            'has_parivartana': True,
            'planet1': lord,
            'planet1_sign': lord_sign,
            'planet2': host,
            'planet2_sign': host_sign,
            'note': f'{lord}(在{ SIGN_CN[lord_sign]}) 与 {host}(在{ SIGN_CN[host_sign]}) 交换宫位',
        }
    
    return {'has_parivartana': False}


def _interpret_marriage_count(count: int, A: int, B: int) -> str:
    """解读婚姻计数结果"""
    lines = []
    lines.append(f"婚姻/认真关系数量：{count}")
    
    if count == 1:
        lines.append("解读：一次终身关系，忠诚度较高。")
        if A == B:
            lines.append("  D1与D9同星座 → 关系稳定，不易动摇。")
    elif count == 2:
        lines.append("解读：两段重要关系，可能再婚或长期关系更替。")
    elif count == 3:
        lines.append("解读：多段关系，关系模式较为复杂。")
    elif count >= 4:
        lines.append(f"解读：{count}段关系，关系频繁变化，需检视关系模式中的重复问题。")
    
    # 特殊位置解读
    if A == B:
        lines.append("⭐ A=B（D1与D9同星座）：内在一致，关系忠诚度高。")
    if (B - A) % 12 == 6:  # 对冲
        lines.append("⚠️ A与B对冲：内在矛盾，关系中的拉锯与不稳定性。")
    
    return "\n".join(lines)


def marriage_counting_full_analysis(
    d1_house7_lord: str,
    d1_planet_lons: Dict[str, float],
    d9_planet_lons: Dict[str, float],
    d1_houses: Optional[Dict] = None,
    d9_houses: Optional[Dict] = None,
    d1_moon_nak_idx: Optional[int] = None,
    d9_upapada_lord: Optional[str] = None,
) -> Dict:
    """
    完整婚姻计数分析（配合 Dasha + D9 验证）
    
    返回包含婚姻计数 + D9 质量评估 + 综合建议
    """
    # 基础计数
    base = marriage_counting_method(
        d1_house7_lord, d1_planet_lons, d9_planet_lons,
        d1_houses, d9_houses
    )
    
    if 'error' in base:
        return base
    
    # D9 质量评估（简化版）
    d9_quality = _assess_d9_marriage_quality(d9_planet_lons, d9_houses)
    
    # 综合建议
    recommendations = _marriage_recommendations(base, d9_quality)
    
    return {
        **base,
        'd9_marriage_quality': d9_quality,
        'recommendations': recommendations,
        'note': '此法的"婚姻"指持续1年以上的认真关系，不一定是法律婚姻。',
    }


def _assess_d9_marriage_quality(
    d9_planet_lons: Dict[str, float],
    d9_houses: Optional[Dict]
) -> Dict:
    """D9 婚姻质量评估 v7.0（完整版）"""
    quality_points = 0
    factors = []

    SIGN_LORDS_LIST = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
                        'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

    def _sign_of(lon):
        return int((lon % 360) / 30)

    def _dignity(planet, sign_idx):
        """简化星性判断"""
        EXALTATION = {'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
                      'Jupiter': 3, 'Venus': 11, 'Saturn': 6}
        OWN = {'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
               'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]}
        DEBILITATION = {'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
                        'Jupiter': 9, 'Venus': 5, 'Saturn': 0}

        if sign_idx == EXALTATION.get(planet, -1):
            return 'exalted'
        if sign_idx in OWN.get(planet, []):
            return 'own'
        if sign_idx == DEBILITATION.get(planet, -1):
            return 'debilitated'
        return 'neutral'

    # 检查 D9 Venus 状态（完整版）
    venus_d9 = d9_planet_lons.get('Venus')
    if venus_d9 is not None:
        venus_sign = _sign_of(venus_d9)
        venus_dig = _dignity('Venus', venus_sign)
        if venus_dig == 'exalted':
            quality_points += 3
            factors.append(f"D9 Venus擢升在{SIGN_CN[venus_sign]} → 婚姻质量极高")
        elif venus_dig == 'own':
            quality_points += 2
            factors.append(f"D9 Venus入庙在{SIGN_CN[venus_sign]} → 婚姻关系质量高")
        elif venus_dig == 'debilitated':
            quality_points -= 2
            factors.append(f"D9 Venus落陷在{SIGN_CN[venus_sign]} → 婚姻关系有重大挑战")
        elif venus_sign in [1, 6]:  # Taurus/Libra own
            quality_points += 2
            factors.append(f"D9 Venus在本宫{SIGN_CN[venus_sign]} → 关系质量好")
        else:
            quality_points += 0
            factors.append(f"D9 Venus在{SIGN_CN[venus_sign]}({venus_dig}) → 关系质量中等")

    # 检查 D9 Mars 状态（婚姻中的冲突指标）
    mars_d9 = d9_planet_lons.get('Mars')
    if mars_d9 is not None:
        mars_sign = _sign_of(mars_d9)
        mars_dig = _dignity('Mars', mars_sign)
        if mars_dig == 'debilitated':
            quality_points -= 1
            factors.append(f"D9 Mars落陷 → 婚姻中缺乏行动力/保护")
        elif mars_dig in ('exalted', 'own'):
            quality_points += 1
            factors.append(f"D9 Mars强 → 婚姻中有保护力和行动力")

    # 检查 D9 Jupiter 状态（婚姻中的智慧和祝福）
    jup_d9 = d9_planet_lons.get('Jupiter')
    if jup_d9 is not None:
        jup_sign = _sign_of(jup_d9)
        jup_dig = _dignity('Jupiter', jup_sign)
        if jup_dig in ('exalted', 'own'):
            quality_points += 2
            factors.append(f"D9 Jupiter强在{SIGN_CN[jup_sign]} → 婚姻有智慧和祝福")
        elif jup_dig == 'debilitated':
            quality_points -= 1
            factors.append(f"D9 Jupiter落陷 → 婚姻缺乏指引")

    # 检查 D9 7宫/7宫主（如果有宫位数据）
    if d9_houses and '7' in d9_houses:
        h7_d9 = d9_houses['7']
        if isinstance(h7_d9, dict) and 'lord' in h7_d9:
            h7_lord_d9 = h7_d9['lord']
            factors.append(f"D9 第7宫主：{h7_lord_d9}")
            # D9 7宫主的星性
            h7l_d9_lon = d9_planet_lons.get(h7_lord_d9)
            if h7l_d9_lon is not None:
                h7l_sign = _sign_of(h7l_d9_lon)
                h7l_dig = _dignity(h7_lord_d9, h7_sign)
                if h7l_dig in ('exalted', 'own'):
                    quality_points += 2
                    factors.append(f"D9 7宫主{h7_lord_d9}强 → 伴侣支持有力")
                elif h7l_dig == 'debilitated':
                    quality_points -= 1
                    factors.append(f"D9 7宫主{h7_lord_d9}落陷 → 伴侣关系挑战")

    # 检查 D9 Rahu/Ketu 对7宫的影响
    rahu_d9 = d9_planet_lons.get('Rahu')
    ketu_d9 = d9_planet_lons.get('Ketu')
    if d9_houses:
        h7_sign = d9_houses.get('7', {})
        if isinstance(h7_sign, dict) and 'sign' in h7_sign:
            h7_sign_name = h7_sign['sign']
            SIGNS_LIST = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                          'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
            if h7_sign_name in SIGNS_LIST:
                h7_idx = SIGNS_LIST.index(h7_sign_name)
                if rahu_d9 is not None and _sign_of(rahu_d9) == h7_idx:
                    quality_points -= 1
                    factors.append("D9 Rahu在7宫 → 关系中的迷惑/非常规因素")
                if ketu_d9 is not None and _sign_of(ketu_d9) == h7_idx:
                    quality_points -= 1
                    factors.append("D9 Ketu在7宫 → 关系中的分离倾向")

    # 综合评级
    if quality_points >= 4:
        rating = "高（关系质量好，伴侣支持强，婚姻稳定）"
    elif quality_points >= 1:
        rating = "中上（关系质量尚可，需经营但基础好）"
    elif quality_points >= 0:
        rating = "中（关系质量一般，需用心经营）"
    elif quality_points >= -2:
        rating = "中下（关系有挑战，需提前沟通和调整期望）"
    else:
        rating = "低（关系质量有重大挑战，强烈建议婚前咨询）"

    return {
        'quality_rating': rating,
        'quality_points': quality_points,
        'factors': factors,
    }


def _marriage_recommendations(base: Dict, d9_quality: Dict) -> List[str]:
    """生成综合建议 v7.0"""
    recs = []
    count = base['marriage_count']

    if count == 1:
        recs.append("重点经营唯一关系，避免第三者介入。")
    elif count == 2:
        recs.append("第一次关系需认真经营；若结束，第二次关系质量需提前评估。")
        # v7.0: 增加每段关系质量预测
        recs.append("第一段关系通常受D1 7宫主状态影响，第二段受D9 7宫主状态影响。")
    else:
        recs.append("需检视关系模式中的重复问题（依恋类型、沟通方式等）。")
        recs.append("每段关系的质量递进：第一段=D1质量，后续逐渐转向D9质量。")

    # v7.0: 每段关系质量预测
    if count >= 2 and 'point_A' in base and 'point_B' in base:
        a = base['point_A']['sign']
        b = base['point_B']['sign']
        # 第一段关系：从A开始的质量
        SIGN_LORDS_LIST = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
                           'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']
        BENEFICS = {'Jupiter', 'Venus', 'Moon', 'Mercury'}
        a_lord = SIGN_LORDS_LIST[a]
        if a_lord in BENEFICS:
            recs.append(f"第一段关系由吉星{a_lord}主导，质量较好。")
        else:
            recs.append(f"第一段关系由{a_lord}主导，可能较为激烈或辛苦。")

    # D9 质量建议
    q_rating = d9_quality['quality_rating']
    if '低' in q_rating or '中下' in q_rating:
        recs.append("D9显示婚姻关系有挑战 → 建议在Dasha吉期内主动经营关系。")
        recs.append("强烈建议婚前/关系前进行专业占星咨询。")
    elif '高' in q_rating:
        recs.append("D9显示婚姻关系质量高 → 珍惜并维护现有关系。")
    elif '中上' in q_rating:
        recs.append("D9显示婚姻关系基础好 → 持续投入可获良好回报。")

    recs.append("建议配合 Vimshottari/Chara Dasha 确认具体结婚/分手时间。")
    recs.append("注意：此法给出数量框架，具体事件需通过 Dasha + Transit 精确定位。")

    return recs


# 导出函数
def calc_marriage_count(d1_7lord, d1_lons, d9_lons, d1_h=None, d9_h=None):
    """便捷函数：计算婚姻计数"""
    return marriage_counting_method(d1_7lord, d1_lons, d9_lons, d1_h, d9_h)


if __name__ == '__main__':
    # 测试：假设 D1 7宫主 = Venus，D1 Venus 在 Gemini(2)，D9 Venus 在 Virgo(5)
    test = marriage_counting_method(
        'Venus',
        {'Venus': 2*30 + 15},  # Gemini 15°
        {'Venus': 5*30 + 10},  # Virgo 10°
    )
    print(test)
