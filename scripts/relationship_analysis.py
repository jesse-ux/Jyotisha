#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Love & Relationship Analysis（感情分析）引擎 v1.0
超越 vedic-astro-skills 的 AI prompt，实现结构化引擎级分析

核心分析链：
7宫+Venus → Navamsa(D9) → Upapada(UL) → Darakaraka → Synastry
"""

from typing import Dict, List, Any

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

VENUS_SIGN_EXPRESSIONS = {
    'Aries': '热情主动，追求挑战型伴侣，偏好独立自主的关系',
    'Taurus': '重视感官和稳定，寻求可靠持久的伴侣关系',
    'Gemini': '注重沟通和智力匹配，偏好灵活多变的关系',
    'Cancer': '情感细腻，重视家庭安全感，寻求呵护型关系',
    'Leo': '浪漫大方，需要欣赏和赞美，偏好光芒四射的伴侣',
    'Virgo': '谨慎务实，注重细节服务，偏好可靠稳重的伴侣',
    'Libra': '和谐至上，重视平等尊重，偏好优雅得体的伴侣',
    'Scorpio': '深刻激烈，追求灵魂共鸣，偏好深度连接的关系',
    'Sagittarius': '自由奔放，注重精神成长，偏好开阔视野的伴侣',
    'Capricorn': '务实理性，重视责任担当，偏好成熟稳重的伴侣',
    'Aquarius': '独特自由，重视友谊基础，偏好不拘一格的伴侣',
    'Pisces': '浪漫梦幻，追求灵魂伴侣，偏好温柔体贴的伴侣',
}

RELATIONSHIP_TIMING = {
    1: '年少时感情萌芽（15-22岁）',
    2: '通过家庭/社交圈认识（20-25岁）',
    3: '通过朋友/同事介绍（22-28岁）',
    4: '通过工作/事业认识（25-30岁）',
    5: '通过浪漫邂逅（20-28岁）',
    6: '通过挑战/竞争环境认识（25-32岁）',
    7: '通过公开社交/相亲（24-30岁）',
    8: '通过深层经历/转变认识（28-35岁）',
    9: '通过高等教育/旅行认识（22-30岁）',
    10: '通过事业成就期认识（28-35岁）',
    11: '通过社交网络/大型活动认识（22-32岁）',
    12: '通过隐秘/远程方式认识（25-35岁）',
}


def analyze_relationship(planets: Dict, asc_sign: str = 'Aries',
                         d9_positions: Dict = None, ul_sign: str = None,
                         darakaraka: str = None, dasha_info: Dict = None) -> Dict:
    """
    完整感情分析引擎。

    Args:
        planets: D1行星位置
        asc_sign: 上升星座
        d9_positions: D9分盘位置（可选）
        ul_sign: Upapada Lagna星座（可选）
        darakaraka: DK配偶指示星（可选）
        dasha_info: 大运信息（可选）

    Returns:
        结构化感情分析
    """
    analysis = {
        'partnership_style': [],
        'attraction_pattern': [],
        'timing': [],
        'strength': [],
        'challenges': [],
        'assessment': '',
    }

    # 1. Venus分析（关系核心指示星）
    venus = planets.get('Venus', {})
    venus_sign = venus.get('sign', 'Libra')
    venus_house = venus.get('house', 0)

    analysis['partnership_style'].append({
        'planet': 'Venus',
        'sign': venus_sign,
        'house': venus_house,
        'expression': VENUS_SIGN_EXPRESSIONS.get(venus_sign, ''),
        'note': f'Venus在{venus_house}宫 — 感情通过{RELATIONSHIP_TIMING.get(venus_house,"自然相遇")}',
    })

    # 2. 7宫分析
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    h7_sign = SIGNS[(asc_idx + 6) % 12]
    h7_lord = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
               'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
               'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}[h7_sign]

    h7_data = planets.get(h7_lord, {})
    h7_house = h7_data.get('house', 0)

    analysis['strength'].append({
        'indicator': '7宫主',
        'lord': h7_lord,
        'sign': h7_sign,
        'house': h7_house,
        'note': f'7宫主{h7_lord}在{h7_house}宫，关系质量与该宫主题紧密相关',
    })

    # 3. 7宫内行星
    h7_planets = []
    for pn, pd in planets.items():
        if pd.get('house') == 7 and pn not in ('Rahu','Ketu'):
            h7_planets.append(pn)
    if h7_planets:
        analysis['strength'].append({
            'indicator': '7宫内行星',
            'planets': h7_planets,
            'note': f'7宫有{", ".join(h7_planets)}，关系领域活跃，伴侣显著影响',
        })

    # 4. Darakaraka分析
    if darakaraka:
        dk_data = planets.get(darakaraka, {})
        analysis['attraction_pattern'].append({
            'type': 'DK配偶指示星',
            'planet': darakaraka,
            'note': f'DK={darakaraka}，伴侣具有{darakaraka}特质 — {PLANET_PARTNER.get(darakaraka, "")}',
        })

    # 5. D9 Navamsa
    if d9_positions:
        d9_venus = d9_positions.get('Venus', {})
        d9_h7 = d9_positions.get('7th_lord', {})
        analysis['strength'].append({
            'indicator': 'D9 Navamsa',
            'venus_sign': d9_venus.get('sign', ''),
            'note': f'D9 Venus在{d9_venus.get("sign","")} — 深层关系需求',
        })

    # 6. UL Upapada Lagna
    if ul_sign:
        analysis['attraction_pattern'].append({
            'type': 'UL配偶镜像',
            'sign': ul_sign,
            'note': f'UL={ul_sign} — 社会视角下的伴侣形象和婚姻质量',
        })

    # 7. 时间窗口
    if dasha_info:
        md = dasha_info.get('maha_dasha', '')
        relationship_planets = ['Venus', 'Jupiter', 'Moon']
        if md in relationship_planets:
            analysis['timing'].append({
                'dasha': md,
                'note': f'当前{md}大运期间，感情/关系相关领域活跃',
            })

    # 8. 综合评估
    venus_strength = 0
    if venus_house in (1, 4, 7, 10, 5, 9):
        venus_strength += 2
    if planets.get('Moon', {}).get('house') in (4, 7, 10):
        venus_strength += 1
    if h7_lord in planets and planets[h7_lord].get('dignity', '') in ('own','exalted','friendly'):
        venus_strength += 2

    if venus_strength >= 4:
        analysis['assessment'] = '感情配置强，关系发展顺利，伴侣质量高'
    elif venus_strength >= 2:
        analysis['assessment'] = '感情基础良好，需注意关系中的沟通和理解'
    else:
        analysis['assessment'] = '感情需要更多耐心和策略，建议关注自我成长后再建立关系'

    return analysis


PLANET_PARTNER = {
    'Sun': '伴侣有领导力、自信、独立自主',
    'Moon': '伴侣温柔体贴、情感丰富、关心家庭',
    'Mars': '伴侣有行动力、勇敢直接、活力充沛',
    'Mercury': '伴侣聪明机智、善于沟通、思维敏捷',
    'Jupiter': '伴侣有智慧慷慨、教育背景好、有信仰',
    'Venus': '伴侣有魅力、艺术气质、注重和谐',
    'Saturn': '伴侣成熟稳重、有责任心、事业有成',
}
