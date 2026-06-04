#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yogas / Doshas / Special Lagnas 计算模块 v6.0.14

支持:
  - Raj Yogas: 王者瑜伽（主星互涉形成权力格局）
  - Dhana Yogas: 财富瑜伽（2/11宫主与吉星组合）
  - Pancha Mahapurusha Yogas: 五王瑜伽（吉星在角宫入庙）
  - Neecha Bhanga Raj Yoga: 落陷解除王者瑜伽
  - Mangal Dosha (Kuja Dosha): 火星煞（火星在1/2/4/7/8/12宫）
  - Kaal Sarp Dosha: 时间蛇煞（所有行星在Rahu-Ketu轴线一侧）
  - Pitra Dosha: 父辈煞（Sun与Rahu合相/受克）
  - Sade Sati: 土星七年（土星过Moon前后各1星座）
  - Arudha Lagna (AL): 镜像上升（从Lagna看Lagna主的落点）
  - Upapada Lagna (UL): 配偶镜像上升（从12宫看12宫主的落点）
"""

from typing import Dict, List, Tuple, Optional

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
          'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

# 吉星/凶星分类
NATURAL_BENEFICS = {'Jupiter', 'Venus', 'Mercury', 'Moon'}
NATURAL_MALEFICS = {'Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu'}


def calc_raj_yogas(planets_data: Dict, houses: Dict) -> Dict:
    """
    计算 Raj Yogas（王者瑜伽）——权力、地位、社会影响力格局

    经典 Raj Yoga 形成条件：
      1. 角宫主（1/4/7/10宫主）与三方宫主（5/9宫主）结合
      2. 角宫主与角宫主结合
      3. 三方宫主与三方宫主结合
      4. 以上组合发生在角宫/三方宫/11宫

    返回：检测到的 Raj Yogas 列表
    """
    results = {'yogas': [], 'summary': ''}

    # 提取宫主星信息
    house_lords = {}
    for h in range(1, 13):
        lord_key = f'H{h}_Lord'
        if lord_key in houses:
            house_lords[h] = houses[lord_key]

    # 检查每对宫主星的组合
    kendras = [1, 4, 7, 10]  # 角宫
    trikonas = [5, 9]  # 三方宫

    def _get_lord_sign_lord(house_num):
        """获取某宫宫主星及其所在宫位"""
        lkey = f'H{house_num}_Lord'
        if lkey not in houses:
            return None, None
        lord = houses[lkey]
        # 找lord在哪里（简化：返回lord所在宫位）
        for pname, pdata in planets_data.items():
            if pname == lord and isinstance(pdata, dict) and 'house' in pdata:
                return lord, pdata['house']
        return lord, None

    # 检查条件1：角宫主 × 三方宫主
    for k_house in kendras:
        for t_house in trikonas:
            k_lord, k_lord_house = _get_lord_sign_lord(k_house)
            t_lord, t_lord_house = _get_lord_sign_lord(t_house)
            if not k_lord or not t_lord:
                continue

            # 检查两主星是否在同一宫或互看对方宫
            # 简化：检查两主星所在宫位是否形成权力宫（角/三方/11）
            if k_lord_house and t_lord_house:
                power_houses = kendras + trikonas + [11]
                if k_lord_house in power_houses or t_lord_house in power_houses:
                    yoga = {
                        'type': 'Raj Yoga',
                        'combination': f'H{k_house}_Lord({k_lord}) + H{t_house}_Lord({t_lord})',
                        'formation_house': k_lord_house,
                        'strength': 'strong' if k_lord_house in kendras else 'moderate',
                        'interpretation': f'Raj Yoga——{k_lord}(H{k_house}主)与{t_lord}(H{t_house}主)结合，权力与地位格局',
                    }
                    results['yogas'].append(yoga)

    results['summary'] = f"Raj Yoga检测：共{len(results['yogas'])}个格局"
    return results


def calc_dhana_yogas(planets_data: Dict, houses: Dict) -> Dict:
    """
    计算 Dhana Yogas（财富瑜伽）——财富积累格局

    经典 Dhana Yoga 形成条件：
      1. 2宫主（财富宫主）与吉星/11宫主结合
      2. 11宫主（收益宫主）与吉星/2宫主结合
      3. 以上组合发生在2/11/角宫/三方宫

    返回：检测到的 Dhana Yogas 列表
    """
    results = {'yogas': [], 'summary': ''}

    # 2宫主和11宫主
    h2_lord = houses.get('H2_Lord', '')
    h11_lord = houses.get('H11_Lord', '')

    if not h2_lord or not h11_lord:
        results['summary'] = 'Dhana Yoga检测：缺少2/11宫主信息'
        return results

    # 检查2宫主和11宫主的组合
    # 找h2_lord和h11_lord的宫位
    h2_lord_house = None
    h11_lord_house = None
    for pname, pdata in planets_data.items():
        if pname == h2_lord and isinstance(pdata, dict) and 'house' in pdata:
            h2_lord_house = pdata['house']
        if pname == h11_lord and isinstance(pdata, dict) and 'house' in pdata:
            h11_lord_house = pdata['house']

    if h2_lord_house and h11_lord_house:
        wealth_houses = [2, 11, 1, 4, 7, 10, 5, 9]
        if h2_lord_house in wealth_houses or h11_lord_house in wealth_houses:
            yoga = {
                'type': 'Dhana Yoga',
                'combination': f'H2_Lord({h2_lord}) + H11_Lord({h11_lord})',
                'formation_house': h2_lord_house,
                'strength': 'strong' if h2_lord_house in [2, 11] else 'moderate',
                'interpretation': f'Dhana Yoga——{h2_lord}(H2主)与{h11_lord}(H11主)结合，财富积累格局',
            }
            results['yogas'].append(yoga)

    results['summary'] = f"Dhana Yoga检测：共{len(results['yogas'])}个格局"
    return results


def calc_pancha_mahapurusha_yoga(planets_data: Dict) -> Dict:
    """
    计算 Pancha Mahapurusha Yogas（五王瑜伽）

    条件：5颗吉星（Mars/Mercury/Jupiter/Venus/Saturn）在角宫（1/4/7/10）
          且入庙（在自家星座）或擢升（在擢升星座）

    5种瑜伽：
      - Ruchaka Yoga: Mars在角宫入庙/擢升
      - Bhadra Yoga: Mercury在角宫入庙/擢升
      - Hamsa Yoga: Jupiter在角宫入庙/擢升
      - Malavya Yoga: Venus在角宫入庙/擢升
      - Sasa Yoga: Saturn在角宫入庙/擢升
    """
    results = {'yogas': [], 'summary': ''}

    # 擢升星座表
    exaltation = {'Mars': 'Capricorn', 'Mercury': 'Virgo', 'Jupiter': 'Cancer',
                  'Venus': 'Pisces', 'Saturn': 'Libra'}
    # 入庙星座表
    own_sign = {'Mars': ['Aries', 'Scorpio'], 'Mercury': ['Gemini', 'Virgo'],
                'Jupiter': ['Sagittarius', 'Pisces'], 'Venus': ['Taurus', 'Libra'],
                'Saturn': ['Capricorn', 'Aquarius']}

    for pname in ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        pdata = planets_data.get(pname, {})
        if not isinstance(pdata, dict) or 'house' not in pdata:
            continue

        house = pdata['house']
        sign = pdata.get('sign', '')

        # 检查是否在角宫
        if house not in [1, 4, 7, 10]:
            continue

        # 检查是否入庙或擢升
        is_exalted = (sign == exaltation.get(pname, ''))
        is_own = (sign in own_sign.get(pname, []))

        if is_exalted or is_own:
            yoga_names = {
                'Mars': 'Ruchaka Yoga', 'Mercury': 'Bhadra Yoga',
                'Jupiter': 'Hamsa Yoga', 'Venus': 'Malavya Yoga',
                'Saturn': 'Sasa Yoga',
            }
            yoga = {
                'type': yoga_names[pname],
                'planet': pname,
                'house': house,
                'sign': sign,
                'status': 'exalted' if is_exalted else 'own_sign',
                'strength': 'very strong' if is_exalted else 'strong',
                'interpretation': f'{yoga_names[pname]}——{pname}在{house}宫{sign}（{"擢升" if is_exalted else "入庙"}），五王瑜伽之一',
            }
            results['yogas'].append(yoga)

    results['summary'] = f"Pancha Mahapurusha Yoga检测：共{len(results['yogas'])}个（最多5个）"
    return results


def calc_nicha_bhanga_raj_yoga(planets_data: Dict, houses: Dict) -> Dict:
    """
    计算 Neecha Bhanga Raj Yoga（落陷解除王者瑜伽）

    条件（需同时满足）：
      1. 某行星落陷（在落陷星座）
      2. 该行星的落陷星座主星在某个角宫/三方宫
      3. 或者：落陷星座主星与落陷行星形成互容

    经典：落陷+落陷解除 = 王者瑜伽（先抑后扬，大器晚成）
    """
    results = {'yogas': [], 'summary': ''}

    # 落陷星座表
    debilitation = {'Mars': 'Cancer', 'Mercury': 'Pisces', 'Jupiter': 'Capricorn',
                    'Venus': 'Virgo', 'Saturn': 'Aries', 'Sun': 'Libra',
                    'Moon': 'Scorpio'}

    for pname, deb_sign in debilitation.items():
        pdata = planets_data.get(pname, {})
        if not isinstance(pdata, dict) or 'sign' not in pdata:
            continue

        sign = pdata['sign']
        if sign != deb_sign:
            continue  # 没落陷

        # 检查落陷解除条件：
        # 条件A：落陷星座主星在角宫/三方宫
        deb_lord = SIGN_LORDS.get(deb_sign, '')
        deb_lord_data = planets_data.get(deb_lord, {})
        deb_lord_house = deb_lord_data.get('house') if isinstance(deb_lord_data, dict) else None

        condition_met = False
        if deb_lord_house and deb_lord_house in [1, 4, 7, 10, 5, 9]:
            condition_met = True

        # 条件B：落陷行星与落陷星座主星互容（在两星星座中）
        # 简化：检查两星是否在同一宫
        p_house = pdata.get('house')
        if deb_lord_house and p_house and deb_lord_house == p_house:
            condition_met = True

        if condition_met:
            yoga = {
                'type': 'Neecha Bhanga Raj Yoga',
                'planet': pname,
                'debilitated_sign': deb_sign,
                'debility_lord': deb_lord,
                'lord_house': deb_lord_house,
                'interpretation': f'Neecha Bhanga Raj Yoga——{pname}在{deb_sign}落陷但解除（{deb_lord}在{deb_lord_house}宫），先抑后扬大器晚成',
            }
            results['yogas'].append(yoga)

    results['summary'] = f"Neecha Bhanga Raj Yoga检测：共{len(results['yogas'])}个"
    return results


def calc_mangal_dosha(planets_data: Dict, mars_house: int) -> Dict:
    """
    计算 Mangal Dosha / Kuja Dosha（火星煞）

    规则：Mars在1/2/4/7/8/12宫 → Mangal Dosha
         影响：婚姻延迟/困难，配偶健康 issues

    缓和条件：
      - Mars在自身星座（Aries/Scorpio）→ 部分缓和
      - Mars擢升（Capricorn）→ 完全解除
      - 第七宫/第七宫主有吉星→ 部分缓和
      - 双鱼/巨蟹上升 → 更麻烦（Mars在这些星座更凶）
    """
    results = {'has_dosha': False, 'severity': 'none', 'remedies': []}

    bad_houses = [1, 2, 4, 7, 8, 12]
    if mars_house not in bad_houses:
        results['summary'] = '无Mangal Dosha（Mars不在煞宫）'
        return results

    results['has_dosha'] = True
    mars_data = planets_data.get('Mars', {})
    mars_sign = mars_data.get('sign', '') if isinstance(mars_data, dict) else ''

    # 判断严重程度
    if mars_house in [7, 8]:
        results['severity'] = 'high'  # 7/8宫最凶
    elif mars_house in [1, 2]:
        results['severity'] = 'moderate'
    else:
        results['severity'] = 'low'

    # 检查缓和条件
    remedies = []
    if mars_sign in ['Aries', 'Scorpio']:
        remedies.append('Mars在自身星座，部分缓和')
        results['severity'] = 'moderate' if results['severity'] == 'high' else 'low'
    if mars_sign == 'Capricorn':
        remedies.append('Mars擢升，完全解除')
        results['severity'] = 'none'
        results['has_dosha'] = False

    results['remedies'] = remedies
    results['mars_house'] = mars_house
    results['mars_sign'] = mars_sign
    results['summary'] = (f"{'无' if not results['has_dosha'] else '有'}Mangal Dosha——"
                           f"Mars在{mars_house}宫{mars_sign}，严重程度：{results['severity']}")
    return results


def calc_kaal_sarp_dosha(planets_data: Dict) -> Dict:
    """
    计算 Kaal Sarp Dosha（时间蛇煞）

    规则：所有行星（除Rahu/Ketu外）都在Rahu-Ketu轴线的同一侧
         形成"蛇吞"格局，带来阻碍、延迟、心理压力

    类型：
      - 完全Kaal Sarp：所有行星在Rahu-Ketu之间（单一侧）
      - 部分Kaal Sarp：大部分行星在Rahu-Ketu之间
    """
    results = {'has_dosha': False, 'type': 'none', 'affected_houses': []}

    rahu_data = planets_data.get('Rahu', {})
    ketu_data = planets_data.get('Ketu', {})

    if not isinstance(rahu_data, dict) or 'house' not in rahu_data:
        results['summary'] = 'Rahu位置未知，无法判断Kaal Sarp Dosha'
        return results

    rahu_house = rahu_data['house']
    ketu_house = ketu_data.get('house', 0) if isinstance(ketu_data, dict) else 0

    # 确定Rahu-Ketu轴线的"之间"范围
    # 简化处理：假设Rahu-Ketu在一条直线上（相差6宫）
    axis_houses = list(range(rahu_house, rahu_house + 6))
    axis_houses = [(h - 1) % 12 + 1 for h in axis_houses]  # 转为1-12

    # 统计在"之间"的行星数量
    planets_in_axis = []
    planets_outside = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        pdata = planets_data.get(pname, {})
        if not isinstance(pdata, dict) or 'house' not in pdata:
            continue
        p_house = pdata['house']
        if p_house in axis_houses:
            planets_in_axis.append(pname)
        else:
            planets_outside.append(pname)

    total_planets = len(planets_in_axis) + len(planets_outside)

    if len(planets_in_axis) == total_planets and total_planets >= 7:
        results['has_dosha'] = True
        results['type'] = 'full'
        results['summary'] = f'完全Kaal Sarp Dosha——所有{total_planets}颗行星在Rahu({rahu_house})—Ketu轴线之间'
    elif len(planets_in_axis) >= total_planets * 0.7:
        results['has_dosha'] = True
        results['type'] = 'partial'
        results['summary'] = f'部分Kaal Sarp Dosha——{len(planets_in_axis)}/{total_planets}颗行星在轴线之间'
    else:
        results['has_dosha'] = False
        results['type'] = 'none'
        results['summary'] = '无Kaal Sarp Dosha'

    results['planets_in_axis'] = planets_in_axis
    results['planets_outside'] = planets_outside
    results['rahu_house'] = rahu_house
    results['ketu_house'] = ketu_house
    return results


def calc_pitra_dosha(planets_data: Dict, sun_house: int) -> Dict:
    """
    计算 Pitra Dosha（父辈煞）

    规则：
      - Sun与Rahu合相（同宫或相邻宫）→ Pitra Dosha
      - Sun受土星/火星克 → 可能Pitra Dosha
      - 第9宫/第9宫主受克 → 父辈煞

    影响：父辈业力、祖先未解问题、子女健康/生育问题
    """
    results = {'has_dosha': False, 'indicators': []}

    sun_data = planets_data.get('Sun', {})
    rahu_data = planets_data.get('Rahu', {})

    if not isinstance(sun_data, dict) or 'house' not in sun_data:
        results['summary'] = 'Sun位置未知，无法判断Pitra Dosha'
        return results

    sun_house = sun_data['house']
    sun_sign = sun_data.get('sign', '')

    # 检查Sun-Rahu合相
    if isinstance(rahu_data, dict) and 'house' in rahu_data:
        rahu_house = rahu_data['house']
        if abs(sun_house - rahu_house) <= 1 or (sun_house == rahu_house):
            results['has_dosha'] = True
            results['indicators'].append(f'Sun({sun_house}宫)与Rahu({rahu_house}宫)合相/相邻')

    # 检查Sun受克（土星/火星在Sun宫或相邻宫）
    for malefic in ['Saturn', 'Mars']:
        mdata = planets_data.get(malefic, {})
        if isinstance(mdata, dict) and 'house' in mdata:
            m_house = mdata['house']
            if abs(sun_house - m_house) <= 1:
                results['has_dosha'] = True
                results['indicators'].append(f'{malefic}({m_house}宫)克Sun({sun_house}宫)')

    results['sun_house'] = sun_house
    results['sun_sign'] = sun_sign
    if not results['indicators']:
        results['summary'] = '无Pitra Dosha明显迹象'
    else:
        results['summary'] = f'有Pitra Dosha迹象：{"; ".join(results["indicators"][:2])}'
    return results


def calc_sade_sati(moon_sign: str, current_year: int = 2026) -> Dict:
    """
    计算 Sade Sati（土星七年）

    规则：土星过Moon所在星座及其前后各1星座，共约7.5年
         每个阶段影响不同：
         - 第一阶段（土星过前一星座）：心理压力开始
         - 第二阶段（土星过Moon星座）：最困难，健康/关系/事业挑战
         - 第三阶段（土星过后一星座）：压力缓解，但有收获

    参数：moon_sign（Moon星座），current_year（当前年份，用于判断是否在进行中）

    返回：Sade Sati阶段信息
    """
    results = {'is_active': False, 'phase': 'none', 'summary': ''}

    if not moon_sign or moon_sign not in SIGNS:
        results['summary'] = 'Moon星座未知，无法判断Sade Sati'
        return results

    moon_idx = SIGNS.index(moon_sign)

    # 简化：只判断当前年份Saturn是否在Moon前后1星座
    # 实际需要Saturn实时位置，这里只给框架
    results['moon_sign'] = moon_sign
    results['moon_idx'] = moon_idx
    results['phases'] = {
        'rising': SIGNS[(moon_idx - 1) % 12],  # 前一星座
        'peak': moon_sign,  # Moon星座（最困难）
        'setting': SIGNS[(moon_idx + 1) % 12],  # 后一星座
    }
    results['summary'] = (f'Sade Sati阶段框架：上升期={results["phases"]["rising"]}，'
                          f'高峰期={results["phases"]["peak"]}（最困难），'
                          f'下降期={results["phases"]["setting"]}；'
                          f'需结合Saturn实际位置判断是否在进行中')
    return results


def calc_arudha_lagna(asc_sign: str, asc_lord: str, planets_data: Dict) -> Dict:
    """
    计算 Arudha Lagna (AL) —— 镜像上升点

    规则：从Lagna（上升）看Lagna Lord（上升主星）的落点，
         再从该落点的"镜像位置"得到AL
         公式：AL = 从Asc看Lord的宫位数，再同样宫位数从Lord往外数

    例子：Asc=Leo, Lord=Sun在10宫 → 从Asc(1)看Sun(10) = 9宫远
         从Sun(10)再数9宫 = 10+9-1=18 → 18-12=6宫 → AL在6宫

    意义：AL代表"他人如何看待命主"，镜像自我认知
    """
    results = {'arudha_lagna': None, 'al_house': None, 'interpretation': ''}

    if not asc_sign or asc_sign not in SIGNS:
        results['summary'] = 'Asc星座未知，无法计算Arudha Lagna'
        return results

    asc_idx = SIGNS.index(asc_sign)

    # 找Asc Lord的宫位
    lord_data = planets_data.get(asc_lord, {})
    if not isinstance(lord_data, dict) or 'house' not in lord_data:
        results['summary'] = f'Asc Lord({asc_lord})宫位未知，无法计算AL'
        return results

    lord_house = lord_data['house']  # 1-12
    lord_idx = (lord_house - 1)  # 转为0-11

    # 计算镜像：从Asc到Lord的宫位数 = lord_idx - asc_idx (mod 12)
    distance = (lord_idx - asc_idx) % 12  # 0-11
    if distance == 0:
        distance = 12  # 同宫=12宫远

    # AL = 从Lord再数同样距离
    al_idx = (lord_idx + distance) % 12
    al_house = al_idx + 1  # 转回1-12

    al_sign = SIGNS[al_idx]

    results['arudha_lagna'] = al_sign
    results['al_house'] = al_house
    results['distance'] = distance
    results['lord_house'] = lord_house
    results['interpretation'] = (
        f'Arudha Lagna (AL) = {al_sign}（第{al_house}宫）——'
        f'他人眼中的你；Asc={asc_sign}, Lord={asc_lord}在{lord_house}宫，距离={distance}'
    )
    results['summary'] = results['interpretation']
    return results


def calc_upapada_lagna(asc_sign: str, house12_lord: str, planets_data: Dict) -> Dict:
    """
    计算 Upapada Lagna (UL) —— 配偶镜像上升点

    规则：从12宫（损失/海外/床事宫）看12宫主星的落点，
         镜像计算方式同Arudha Lagna
         公式：UL = 从12宫看12宫主星的宫位数，再从主星落点往外数同样宫位数

    意义：UL代表"配偶/婚姻伙伴"，是婚姻质量的关键指标
          UL受克/受损 → 婚姻困难
          UL有吉星 → 婚姻幸福
    """
    results = {'upapada': None, 'ul_house': None, 'interpretation': ''}

    if not asc_sign or asc_sign not in SIGNS:
        results['summary'] = 'Asc星座未知，无法计算Upapada'
        return results

    asc_idx = SIGNS.index(asc_sign)
    h12_idx = (asc_idx + 11) % 12  # 12宫 index (0-11)

    # 找12宫主星的宫位
    lord_data = planets_data.get(house12_lord, {})
    if not isinstance(lord_data, dict) or 'house' not in lord_data:
        results['summary'] = f'12宫主星({house12_lord})宫位未知，无法计算UL'
        return results

    lord_house = lord_data['house']  # 1-12
    lord_idx = (lord_house - 1)  # 0-11

    # 计算镜像：从12宫到12宫主星的宫位数
    distance = (lord_idx - h12_idx) % 12
    if distance == 0:
        distance = 12

    # UL = 从Lord再数同样距离
    ul_idx = (lord_idx + distance) % 12
    ul_house = ul_idx + 1

    ul_sign = SIGNS[ul_idx]

    results['upapada'] = ul_sign
    results['ul_house'] = ul_house
    results['distance'] = distance
    results['lord_house'] = lord_house
    results['interpretation'] = (
        f'Upapada Lagna (UL) = {ul_sign}（第{ul_house}宫）——'
        f'配偶/婚姻质量指标；12宫主星={house12_lord}在{lord_house}宫，距离={distance}'
    )
    results['summary'] = results['interpretation']
    return results


def calc_all_yogas_doshas(planets_data: Dict, houses: Dict,
                          asc_sign: str, asc_lord: str,
                          moon_sign: str, moon_house: int,
                          mars_house: int, sun_house: int,
                          house12_lord: str) -> Dict:
    """
    批量计算所有 Yogas + Doshas + Special Lagnas（v6.0.14 主入口）

    参数：
        planets_data: 行星数据字典
        houses: 宫位信息字典
        asc_sign: 上升星座
        asc_lord: 上升主星
        moon_sign: Moon星座
        moon_house: Moon宫位
        mars_house: Mars宫位
        sun_house: Sun宫位
        house12_lord: 12宫主星

    返回：完整结果字典
    """
    results = {}

    # Yogas
    results['raj_yogas'] = calc_raj_yogas(planets_data, houses)
    results['dhana_yogas'] = calc_dhana_yogas(planets_data, houses)
    results['pancha_mahapurusha'] = calc_pancha_mahapurusha_yoga(planets_data)
    results['nicha_bhanga_raj'] = calc_nicha_bhanga_raj_yoga(planets_data, houses)

    # Doshas
    results['mangal_dosha'] = calc_mangal_dosha(planets_data, mars_house)
    results['kaal_sarp_dosha'] = calc_kaal_sarp_dosha(planets_data)
    results['pitra_dosha'] = calc_pitra_dosha(planets_data, sun_house)
    results['sade_sati'] = calc_sade_sati(moon_sign)

    # Special Lagnas
    results['arudha_lagna'] = calc_arudha_lagna(asc_sign, asc_lord, planets_data)
    results['upapada_lagna'] = calc_upapada_lagna(asc_sign, house12_lord, planets_data)

    # 总结
    total_yogas_count = (len(results['raj_yogas']['yogas']) +
                         len(results['dhana_yogas']['yogas']) +
                         len(results['pancha_mahapurusha']['yogas']) +
                         len(results['nicha_bhanga_raj']['yogas']))
    has_dosha = any([
        results['mangal_dosha']['has_dosha'],
        results['kaal_sarp_dosha']['has_dosha'],
        results['pitra_dosha']['has_dosha'],
    ])

    results['summary'] = (
        f"Yogas共{total_yogas_count}个；"
        f"Doshas: Mangal={'有' if results['mangal_dosha']['has_dosha'] else '无'}"
        f"/Kaal Sarp={'有' if results['kaal_sarp_dosha']['has_dosha'] else '无'}"
        f"/Pitra={'有' if results['pitra_dosha']['has_dosha'] else '无'}"
    )

    return results
