#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Career Analysis（事业分析）引擎 v1.0
超越 vedic-astro-skills 的 AI prompt，实现结构化引擎级分析

核心分析链：
D10(Dashamsa)事业盘 → 10宫主状态 → Saturn/Jupiter角色 → Dasha事业窗口 → Yogas
"""

from typing import Dict, List, Any

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

CAREER_SIGN_INDICATORS = {
    'Aries': ['军事/执法','工程/技术','创业/先驱','外科医学'],
    'Taurus': ['金融/银行','艺术/设计','餐饮/食品','奢侈品'],
    'Gemini': ['媒体/传播','教育/培训','销售/贸易','IT/编程'],
    'Cancer': ['医疗/护理','房地产','酒店/旅游','心理学/咨询'],
    'Leo': ['管理/领导','娱乐/表演','政府/政治','教育/学术'],
    'Virgo': ['数据分析','会计/审计','编辑/校对','医疗技术'],
    'Libra': ['法律/司法','艺术/美学','公共关系','人力资源'],
    'Scorpio': ['投资/风控','研究/侦探','心理学/精神分析','保险/精算'],
    'Sagittarius': ['国际商务','教育/哲学','法律/宗教','出版/写作'],
    'Capricorn': ['管理/行政','土木工程','政府/政策','传统行业'],
    'Aquarius': ['科技/创新','NGO/公益','科学/研究','网络/电商'],
    'Pisces': ['艺术/影视','医疗/康复','慈善/NGO','创意/设计'],
}

PLANET_CAREER_ROLES = {
    'Sun': {'domain': '领导/管理','strength': '威权、决策、独立执业'},
    'Moon': {'domain': '公众/服务','strength': '人际、关怀、变动适应'},
    'Mars': {'domain': '执行/技术','strength': '行动力、工程、军事'},
    'Mercury': {'domain': '信息/沟通','strength': '智力、商业、IT'},
    'Jupiter': {'domain': '指导/教育','strength': '教导、咨询、法律'},
    'Venus': {'domain': '艺术/财富','strength': '审美、金融、奢侈'},
    'Saturn': {'domain': '管理/组织','strength': '纪律、行政、工业'},
    'Rahu': {'domain': '创新/涉外','strength': '科技、外企、非传统'},
    'Ketu': {'domain': '研究/灵性','strength': '分析、玄学、幕后'},
}

D10_HOUSE_MEANINGS = {
    1: '事业身份/职业形象', 2: '事业财富/收入来源', 3: '事业沟通/技能',
    4: '事业根基/安稳度', 5: '事业创意/子女相关', 6: '事业竞争/服务',
    7: '事业合作/客户', 8: '事业变革/危机管理', 9: '事业远见/高等教育',
    10: '事业成就/社会地位', 11: '事业收益/人脉', 12: '事业幕后/海外',
}


def analyze_career(planets: Dict, asc_sign: str = 'Aries',
                   d10_positions: Dict = None, dasha_info: Dict = None,
                   shadbala: Dict = None) -> Dict:
    """
    完整事业分析引擎。

    Args:
        planets: D1行星位置 {planet: {'sign','house','degree',...}}
        asc_sign: 上升星座
        d10_positions: D10分盘行星位置（可选，提升精度）
        dasha_info: 当前大运/小运信息（可选）
        shadbala: Shadbala结果（可选）

    Returns:
        结构化事业分析
    """
    analysis = {'indicators': [], 'strengths': [], 'challenges': [], 'timing': [], 'fields': []}

    # 1. 10宫分析
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    h10_sign = SIGNS[(asc_idx + 9) % 12]
    h10_lord = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
                'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
                'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}[h10_sign]

    # 10宫主状态
    h10_data = planets.get(h10_lord, {})
    h10_house = h10_data.get('house', 0)
    h10_dignity = h10_data.get('dignity', 'neutral')

    analysis['indicators'].append({
        'type': '10宫主分析',
        'lord': h10_lord,
        'sign': h10_sign,
        'house': h10_house,
        'dignity': h10_dignity,
        'potential_fields': CAREER_SIGN_INDICATORS.get(h10_sign, []),
    })

    # 2. 行星角色分配
    for planet in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']:
        pd = planets.get(planet, {})
        if not pd:
            continue
        house = pd.get('house', 0)
        if house in (1, 4, 7, 10):
            analysis['strengths'].append({
                'planet': planet,
                'role': PLANET_CAREER_ROLES.get(planet, {}).get('domain', ''),
                'detail': PLANET_CAREER_ROLES.get(planet, {}).get('strength', ''),
                'house': house,
                'note': f'{planet}在角宫({house}) — 事业核心驱动力',
            })

    # 3. Saturn角色（事业核心指示星）
    saturn = planets.get('Saturn', {})
    saturn_house = saturn.get('house', 0)
    if saturn_house in (10, 6):
        analysis['strengths'].append({'planet':'Saturn','role':'事业纪律','detail':'Saturn在事业/服务宫，职业路径明确且循序渐进'})
    if saturn_house in (8, 12):
        analysis['challenges'].append({'planet':'Saturn','issue':'事业迟发','detail':f'Saturn在{saturn_house}宫，事业成熟较晚但后劲充足'})

    # 4. 事业领域推荐
    scored_fields = {}
    # 10宫星座
    for field in CAREER_SIGN_INDICATORS.get(h10_sign, []):
        scored_fields[field] = scored_fields.get(field, 0) + 3
    # 10宫主
    if h10_lord in PLANET_CAREER_ROLES:
        scored_fields[PLANET_CAREER_ROLES[h10_lord]['domain']] = scored_fields.get(PLANET_CAREER_ROLES[h10_lord]['domain'], 0) + 2
    # D10分析（如果有）
    if d10_positions:
        d10_h10_sign = SIGNS[((asc_idx + d10_positions.get('asc_offset', 0)) % 12)]
        for field in CAREER_SIGN_INDICATORS.get(d10_h10_sign, []):
            scored_fields[field] = scored_fields.get(field, 0) + 1

    top_fields = sorted(scored_fields.items(), key=lambda x: x[1], reverse=True)[:5]
    analysis['fields'] = [{'field': f, 'score': s} for f, s in top_fields]

    # 5. 时间窗口
    if dasha_info:
        md = dasha_info.get('maha_dasha', '')
        ad = dasha_info.get('antar_dasha', '')
        analysis['timing'].append({
            'current': f'{md}-{ad}',
            'note': f'当前{md}大运{ad}小运期间，{PLANET_CAREER_ROLES.get(md,{}).get("domain","")}领域活跃',
        })

    # 6. 综合评估
    if shadbala:
        h10_strength = shadbala.get(h10_lord, {}).get('total_rupas', 3)
        if h10_strength > 5:
            level = '事业驱动力强，职业路径明确'
        elif h10_strength > 3:
            level = '事业基础稳固，需策略性发展'
        else:
            level = '事业需要额外努力和策略规划'
    else:
        level = '基于10宫主状态，事业潜力为中等偏上'

    analysis['assessment'] = level

    return analysis
