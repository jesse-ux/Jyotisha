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
    计算 Raj Yogas（王者瑜伽）——权力、地位、社会影响力格局 v7.0

    经典 Raj Yoga 形成条件：
      1. 角宫主（1/4/7/10宫主）与三方宫主（5/9宫主）同宫（conjunction）
      2. 角宫主与三方宫主互看（mutual aspect）
      3. 角宫主与三方宫主互容（parivartana）
      4. 同一星同时掌管角宫和三方宫（dual lordship）
      5. Viparita Raja Yoga：凶宫主（6/8/12宫主）落入另一个凶宫

    参考：dashaflow yoga.py (MIT)

    返回：检测到的 Raj Yogas 列表
    """
    results = {'yogas': [], 'summary': ''}

    SIGNS_LIST = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

    # 提取宫主星信息
    def _lord_of_house(house_num):
        """获取某宫的宫主星"""
        lkey = f'H{house_num}_Lord'
        if lkey in houses:
            return houses[lkey]
        # 从行星数据推断
        asc_sign = houses.get('asc_sign', '')
        if asc_sign and asc_sign in SIGN_LORDS:
            asc_idx = SIGNS_LIST.index(asc_sign) if asc_sign in SIGNS_LIST else 0
            sign_idx = (asc_idx + house_num - 1) % 12
            return SIGN_LORDS[SIGNS_LIST[sign_idx]]
        return None

    def _get_planet_sign_idx(pname):
        """获取行星所在星座索引"""
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'sign' in pdata:
            sign = pdata['sign']
            if sign in SIGNS_LIST:
                return SIGNS_LIST.index(sign)
        # 从经度推断
        if isinstance(pdata, dict) and 'longitude' in pdata:
            return int(pdata['longitude'] / 30) % 12
        return None

    def _get_planet_house(pname):
        """获取行星所在宫位"""
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'house' in pdata:
            return pdata['house']
        return None

    # 检查每对宫主星的组合
    kendras = [1, 4, 7, 10]  # 角宫
    trikonas = [1, 5, 9]  # 三方宫（含1宫）
    dusthanas = [6, 8, 12]  # 凶宫

    # ── 条件4: 双重宫主星（同一星掌管角宫+三方宫）──
    kendra_lords = {}
    trikona_lords = {}
    for h in kendras:
        lord = _lord_of_house(h)
        if lord:
            kendra_lords.setdefault(lord, []).append(h)
    for h in trikonas:
        lord = _lord_of_house(h)
        if lord:
            trikona_lords.setdefault(lord, []).append(h)

    dual_lords = set(kendra_lords.keys()) & set(trikona_lords.keys())
    for lord in dual_lords:
        k_houses = kendra_lords[lord]
        t_houses = trikona_lords[lord]
        lord_house = _get_planet_house(lord)
        if lord_house and lord_house in kendras + trikonas:
            yoga = {
                'type': 'Raj Yoga',
                'subtype': 'dual_lordship',
                'combination': f'{lord}(H{k_houses}主+H{t_houses}主)',
                'formation_house': lord_house,
                'strength': 'strong' if lord_house in kendras else 'moderate',
                'interpretation': f'Raj Yoga——{lord}同时掌管角宫{k_houses}和三方宫{t_houses}，且在{lord_house}宫，双重权力格局',
            }
            results['yogas'].append(yoga)

    # ── 条件1+2+3: 角宫主 × 三方宫主 的组合检测 ──
    pure_kendra_lords = set(kendra_lords.keys()) - dual_lords
    pure_trikona_lords = set(trikona_lords.keys()) - dual_lords

    for kl in pure_kendra_lords:
        for tl in pure_trikona_lords:
            kl_sign = _get_planet_sign_idx(kl)
            tl_sign = _get_planet_sign_idx(tl)

            if kl_sign is None or tl_sign is None:
                continue

            # 条件1: 同宫（conjunction）
            if kl_sign == tl_sign:
                house_from_asc = (kl_sign - (SIGNS_LIST.index(houses.get('asc_sign', 'Aries')) if houses.get('asc_sign') in SIGNS_LIST else 0)) % 12 + 1
                yoga = {
                    'type': 'Raj Yoga',
                    'subtype': 'conjunction',
                    'combination': f'{kl}(角宫主) + {tl}(三方宫主)',
                    'formation_house': house_from_asc,
                    'strength': 'strong' if house_from_asc in kendras else 'moderate',
                    'interpretation': f'Raj Yoga——{kl}(角宫主)与{tl}(三方宫主)同宫在{SIGNS_LIST[kl_sign]}，权力格局',
                }
                results['yogas'].append(yoga)

            # 条件2: 互看（mutual aspect: 7宫关系）
            elif abs(kl_sign - tl_sign) == 6 or abs(kl_sign - tl_sign) == 6 + 12:
                yoga = {
                    'type': 'Raj Yoga',
                    'subtype': 'mutual_aspect',
                    'combination': f'{kl}(角宫主) ↔ {tl}(三方宫主)',
                    'interpretation': f'Raj Yoga——{kl}(角宫主)与{tl}(三方宫主)互看（对宫相位），权力格局',
                }
                results['yogas'].append(yoga)

            # 条件3: 互容（parivartana）
            else:
                # 检查kl是否在tl掌管的星座，且tl是否在kl掌管的星座
                kl_lord_signs = []  # kl掌管的星座
                tl_lord_signs = []  # tl掌管的星座
                for s_idx, s_name in enumerate(SIGNS_LIST):
                    if SIGN_LORDS[s_name] == kl:
                        kl_lord_signs.append(s_idx)
                    if SIGN_LORDS[s_name] == tl:
                        tl_lord_signs.append(s_idx)

                if tl_sign in kl_lord_signs and kl_sign in tl_lord_signs:
                    yoga = {
                        'type': 'Raj Yoga',
                        'subtype': 'parivartana',
                        'combination': f'{kl}(角宫主) ⇄ {tl}(三方宫主)',
                        'interpretation': f'Raj Yoga——{kl}(角宫主)与{tl}(三方宫主)互容交换，权力格局强化',
                    }
                    results['yogas'].append(yoga)

    # ── 条件5: Viparita Raja Yoga ──
    # 6/8/12宫主落入另一个凶宫（凶中凶=逆转大吉）
    dusthana_lords = {}
    for h in dusthanas:
        lord = _lord_of_house(h)
        if lord:
            dusthana_lords[h] = lord

    for h, lord in dusthana_lords.items():
        lord_house = _get_planet_house(lord)
        if lord_house and lord_house in dusthanas and lord_house != h:
            yoga = {
                'type': 'Viparita Raja Yoga',
                'subtype': 'dusthana_in_dusthana',
                'combination': f'H{h}_Lord({lord}) in H{lord_house}',
                'interpretation': f'Viparita Raja Yoga——{h}宫主{lord}落入{lord_house}宫（凶中凶），先苦后甜逆转格局',
            }
            results['yogas'].append(yoga)

    results['summary'] = f"Raj Yoga检测：共{len(results['yogas'])}个格局"
    return results


def calc_dhana_yogas(planets_data: Dict, houses: Dict) -> Dict:
    """
    计算 Dhana Yogas（财富瑜伽）——财富积累格局 v7.0

    经典 Dhana Yoga 形成条件（参考dashaflow yoga.py MIT）：
      1. 2宫主+11宫主同在角宫/三方宫
      2. 5宫主+9宫主同宫或互看
      3. 2宫主+9宫主（财富+幸运）同宫/互看
      4. 11宫主+9宫主（收益+幸运）同宫/互看
      5. 2/11宫主与吉星（Jupiter/Venus）同宫

    返回：检测到的 Dhana Yogas 列表
    """
    results = {'yogas': [], 'summary': ''}

    SIGNS_LIST = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
    KENDRA = {1, 4, 7, 10}
    TRIKONA = {1, 5, 9}
    GOOD_HOUSES = KENDRA | TRIKONA | {2, 11}
    BENEFICS = {'Jupiter', 'Venus'}

    def _lord_of_house(house_num):
        lkey = f'H{house_num}_Lord'
        if lkey in houses:
            return houses[lkey]
        asc_sign = houses.get('asc_sign', '')
        if asc_sign and asc_sign in SIGN_LORDS:
            asc_idx = SIGNS_LIST.index(asc_sign) if asc_sign in SIGNS_LIST else 0
            sign_idx = (asc_idx + house_num - 1) % 12
            return SIGN_LORDS[SIGNS_LIST[sign_idx]]
        return None

    def _get_planet_house(pname):
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'house' in pdata:
            return pdata['house']
        return None

    def _get_planet_sign(pname):
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'sign' in pdata:
            return pdata['sign']
        return None

    def _same_sign(p1, p2):
        s1 = _get_planet_sign(p1)
        s2 = _get_planet_sign(p2)
        return s1 and s2 and s1 == s2

    # ── 条件1: 2宫主+11宫主同在角宫/三方宫 ──
    lord_2 = _lord_of_house(2)
    lord_11 = _lord_of_house(11)
    if lord_2 and lord_11:
        h2 = _get_planet_house(lord_2)
        h11 = _get_planet_house(lord_11)
        if h2 and h11 and h2 in GOOD_HOUSES and h11 in GOOD_HOUSES:
            results['yogas'].append({
                'type': 'Dhana Yoga',
                'subtype': '2nd_11th_lords_strong',
                'combination': f'H2_Lord({lord_2}) in H{h2} + H11_Lord({lord_11}) in H{h11}',
                'strength': 'strong' if h2 in KENDRA and h11 in KENDRA else 'moderate',
                'interpretation': f'Dhana Yoga——2宫主{lord_2}(H{h2})与11宫主{lord_11}(H{h11})均落强宫，财富积累格局',
            })

    # ── 条件2: 5宫主+9宫主同宫/互看 ──
    lord_5 = _lord_of_house(5)
    lord_9 = _lord_of_house(9)
    if lord_5 and lord_9:
        if _same_sign(lord_5, lord_9):
            s = _get_planet_sign(lord_5)
            results['yogas'].append({
                'type': 'Dhana Yoga',
                'subtype': '5th_9th_conjunction',
                'combination': f'H5_Lord({lord_5}) + H9_Lord({lord_9})',
                'strength': 'strong',
                'interpretation': f'Dhana Yoga——5宫主{lord_5}与9宫主{lord_9}同宫在{s}，财富+幸运格局',
            })
        else:
            h5 = _get_planet_house(lord_5)
            h9 = _get_planet_house(lord_9)
            if h5 and h9:
                # 互看: 7宫关系
                if abs(h5 - h9) == 6:
                    results['yogas'].append({
                        'type': 'Dhana Yoga',
                        'subtype': '5th_9th_mutual_aspect',
                        'combination': f'H5_Lord({lord_5}) ↔ H9_Lord({lord_9})',
                        'strength': 'moderate',
                        'interpretation': f'Dhana Yoga——5宫主{lord_5}(H{h5})与9宫主{lord_9}(H{h9})互看，财富格局',
                    })
                # 同在角宫/三方宫
                elif h5 in GOOD_HOUSES and h9 in GOOD_HOUSES:
                    results['yogas'].append({
                        'type': 'Dhana Yoga',
                        'subtype': '5th_9th_strong_houses',
                        'combination': f'H5_Lord({lord_5}) in H{h5} + H9_Lord({lord_9}) in H{h9}',
                        'strength': 'moderate',
                        'interpretation': f'Dhana Yoga——5宫主{lord_5}与9宫主{lord_9}均落强宫，财富格局',
                    })

    # ── 条件3: 2宫主+9宫主同宫/互看 ──
    if lord_2 and lord_9:
        if _same_sign(lord_2, lord_9):
            s = _get_planet_sign(lord_2)
            results['yogas'].append({
                'type': 'Dhana Yoga',
                'subtype': '2nd_9th_conjunction',
                'combination': f'H2_Lord({lord_2}) + H9_Lord({lord_9})',
                'strength': 'strong',
                'interpretation': f'Dhana Yoga——2宫主{lord_2}与9宫主{lord_9}同宫在{s}，财富+幸运组合',
            })

    # ── 条件4: 11宫主+9宫主同宫/互看 ──
    if lord_11 and lord_9:
        if _same_sign(lord_11, lord_9):
            s = _get_planet_sign(lord_11)
            results['yogas'].append({
                'type': 'Dhana Yoga',
                'subtype': '11th_9th_conjunction',
                'combination': f'H11_Lord({lord_11}) + H9_Lord({lord_9})',
                'strength': 'strong',
                'interpretation': f'Dhana Yoga——11宫主{lord_11}与9宫主{lord_9}同宫在{s}，收益+幸运组合',
            })

    # ── 条件5: 2/11宫主与吉星同宫 ──
    for wealth_lord, w_house in [(lord_2, 2), (lord_11, 11)]:
        if not wealth_lord:
            continue
        for benefic in BENEFICS:
            if _same_sign(wealth_lord, benefic):
                s = _get_planet_sign(wealth_lord)
                results['yogas'].append({
                    'type': 'Dhana Yoga',
                    'subtype': f'{w_house}th_lord_benefic_conjunction',
                    'combination': f'H{w_house}_Lord({wealth_lord}) + {benefic}',
                    'strength': 'moderate',
                    'interpretation': f'Dhana Yoga——{w_house}宫主{wealth_lord}与吉星{benefic}同宫在{s}，财富助力格局',
                })

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
    计算 Neecha Bhanga Raj Yoga（落陷解除王者瑜伽）v7.0

    条件（需满足落陷 + 解除，参考dashaflow yoga.py MIT）：
      1. 某行星落陷（在落陷星座）
      解除条件（满足任一即可）：
      A. 落陷星座主星（dispositor）在Lagna角宫(1/4/7/10)
      B. 落陷星座主星在Moon角宫
      C. 擢升星座主星在Lagna角宫
      D. 擢升星座主星在Moon角宫
      E. 落陷星与落陷星座主星互容（parivartana）
      F. 落陷星在Navamsa中入庙/擢升（vargottama缓解）

    经典：落陷+落陷解除 = 王者瑜伽（先抑后扬，大器晚成）
    """
    results = {'yogas': [], 'summary': ''}

    SIGNS_LIST = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
                  'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

    # 落陷星座表
    debilitation = {'Mars': 'Cancer', 'Mercury': 'Pisces', 'Jupiter': 'Capricorn',
                    'Venus': 'Virgo', 'Saturn': 'Aries', 'Sun': 'Libra',
                    'Moon': 'Scorpio'}

    # 擢升星座表
    exaltation = {'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn',
                  'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces',
                  'Saturn': 'Libra'}

    KENDRA = {1, 4, 7, 10}

    def _get_planet_house(pname):
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'house' in pdata:
            return pdata['house']
        return None

    def _get_planet_sign(pname):
        pdata = planets_data.get(pname, {})
        if isinstance(pdata, dict) and 'sign' in pdata:
            return pdata['sign']
        return None

    def _get_planet_sign_idx(pname):
        s = _get_planet_sign(pname)
        if s and s in SIGNS_LIST:
            return SIGNS_LIST.index(s)
        return None

    def _get_moon_house():
        return _get_planet_house('Moon')

    def _house_from_moon(planet_name):
        """计算从Moon看某行星在第几宫"""
        moon_idx = _get_planet_sign_idx('Moon')
        p_idx = _get_planet_sign_idx(planet_name)
        if moon_idx is not None and p_idx is not None:
            return ((p_idx - moon_idx) % 12) + 1
        return None

    for pname, deb_sign in debilitation.items():
        pdata = planets_data.get(pname, {})
        if not isinstance(pdata, dict) or 'sign' not in pdata:
            continue

        sign = pdata['sign']
        if sign != deb_sign:
            continue  # 没落陷

        cancellation = False
        cancel_reasons = []

        # 条件A: 落陷星座主星(dispositor)在Lagna角宫
        deb_lord = SIGN_LORDS.get(deb_sign, '')
        deb_lord_house = _get_planet_house(deb_lord)
        if deb_lord_house and deb_lord_house in KENDRA:
            cancellation = True
            cancel_reasons.append(f'定位星{deb_lord}在Lagna第{deb_lord_house}宫(角宫)')

        # 条件B: 落陷星座主星在Moon角宫
        if deb_lord:
            hfm = _house_from_moon(deb_lord)
            if hfm and hfm in KENDRA:
                cancellation = True
                cancel_reasons.append(f'定位星{deb_lord}在Moon第{hfm}宫(角宫)')

        # 条件C: 擢升星座主星在Lagna角宫
        exalt_sign = exaltation.get(pname, '')
        exalt_lord = SIGN_LORDS.get(exalt_sign, '')
        if exalt_lord:
            exalt_lord_house = _get_planet_house(exalt_lord)
            if exalt_lord_house and exalt_lord_house in KENDRA:
                cancellation = True
                cancel_reasons.append(f'擢升星主{exalt_lord}在Lagna第{exalt_lord_house}宫(角宫)')

        # 条件D: 擢升星座主星在Moon角宫
        if exalt_lord:
            hfm = _house_from_moon(exalt_lord)
            if hfm and hfm in KENDRA:
                cancellation = True
                cancel_reasons.append(f'擢升星主{exalt_lord}在Moon第{hfm}宫(角宫)')

        # 条件E: 落陷星与定位星互容（parivartana）
        if deb_lord and deb_lord != pname:
            p_sign = _get_planet_sign(pname)
            lord_sign = _get_planet_sign(deb_lord)
            if p_sign and lord_sign:
                # pname在deb_sign(由deb_lord掌管), deb_lord是否在pname掌管的星座?
                pname_own_signs = [s for s, l in SIGN_LORDS.items() if l == pname]
                if lord_sign in pname_own_signs:
                    cancellation = True
                    cancel_reasons.append(f'{pname}与{deb_lord}互容(Parivartana)')

        # 条件F: Navamsa入庙/擢升缓解（如果有navamsa数据）
        navamsa_sign = pdata.get('navamsa_sign')
        if navamsa_sign:
            own_signs = [s for s, l in SIGN_LORDS.items() if l == pname]
            if navamsa_sign in own_signs or navamsa_sign == exaltation.get(pname, ''):
                cancellation = True
                cancel_reasons.append(f'{pname}在Navamsa中入庙/擢升({navamsa_sign})')

        if cancellation:
            # 量化解除程度
            cancel_count = len(cancel_reasons)
            strength = 'very strong' if cancel_count >= 3 else 'strong' if cancel_count >= 2 else 'moderate'

            yoga = {
                'type': 'Neecha Bhanga Raj Yoga',
                'planet': pname,
                'debilitated_sign': deb_sign,
                'debility_lord': deb_lord,
                'lord_house': deb_lord_house,
                'exaltation_sign': exalt_sign,
                'exaltation_lord': exalt_lord,
                'cancellation_reasons': cancel_reasons,
                'cancellation_count': cancel_count,
                'strength': strength,
                'interpretation': f'Neecha Bhanga Raj Yoga——{pname}在{deb_sign}落陷但解除（{"; ".join(cancel_reasons)}），先抑后扬大器晚成',
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
