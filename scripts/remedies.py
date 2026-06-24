#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remedies（补救措施）系统 v1.0
基于BPHS（Brihat Parashara Hora Shastra）经典补救体系

五大类补救：
1. Ratna (宝石) — 行星弱点修饰
2. Mantra (咒语) — 声音振动疗愈
3. Dana (捐赠) — 因果净化
4. Vrata (斋戒) — 身体净化
5. Yantra (护符) — 几何能量图案

输入：行星力量分析结果（Shadbala/Dignity/Dasha）
输出：针对性的补救建议
"""

from typing import Dict, List, Optional

PLANET_GEMS = {
    'Sun': {'gem': '红宝石 (Ruby/Manikya)', 'metal': '金 (Gold)', 'finger': '无名指', 'day': '周日'},
    'Moon': {'gem': '珍珠 (Pearl/Moti)', 'metal': '银 (Silver)', 'finger': '小指', 'day': '周一'},
    'Mars': {'gem': '红珊瑚 (Red Coral/Moonga)', 'metal': '铜 (Copper)', 'finger': '无名指', 'day': '周二'},
    'Mercury': {'gem': '祖母绿 (Emerald/Panna)', 'metal': '金 (Gold)', 'finger': '小指', 'day': '周三'},
    'Jupiter': {'gem': '黄宝石 (Yellow Sapphire/Pukhraj)', 'metal': '金 (Gold)', 'finger': '食指', 'day': '周四'},
    'Venus': {'gem': '钻石 (Diamond/Heera)', 'metal': '银/白金 (Silver/Platinum)', 'finger': '中指', 'day': '周五'},
    'Saturn': {'gem': '蓝宝石 (Blue Sapphire/Neelam)', 'metal': '铁 (Iron)', 'finger': '中指', 'day': '周六'},
    'Rahu': {'gem': '天河石 (Hessonite/Gomed)', 'metal': '混合金属 (Mixed)', 'finger': '中指', 'day': '周六'},
    'Ketu': {'gem': '猫眼石 (Cat\'s Eye/Lahsuniya)', 'metal': '混合金属 (Mixed)', 'finger': '无名指', 'day': '周二'},
}

PLANET_MANTRAS = {
    'Sun': 'Om Suryaya Namaha',
    'Moon': 'Om Chandraya Namaha',
    'Mars': 'Om Mangalaya Namaha',
    'Mercury': 'Om Budhaya Namaha',
    'Jupiter': 'Om Brihaspataye Namaha',
    'Venus': 'Om Shukraya Namaha',
    'Saturn': 'Om Shanaishcharaya Namaha',
    'Rahu': 'Om Rahave Namaha',
    'Ketu': 'Om Ketave Namaha',
}

PLANET_DONATIONS = {
    'Sun': ['小麦(Wheat)', '红糖(Jaggery)', '红布', '铜器'],
    'Moon': ['大米(Rice)', '牛奶', '银器', '白糖'],
    'Mars': ['红扁豆(Masoor Dal)', '红布', '铜器', '珊瑚碎片'],
    'Mercury': ['绿豆(Moong Dal)', '青色布', '文具', '书本'],
    'Jupiter': ['鹰嘴豆(Chana Dal)', '黄布', '姜黄', '香蕉'],
    'Venus': ['白米', '白布', '酥油(Ghee)', '银器'],
    'Saturn': ['黑芝麻(Black Sesame)', '黑布', '铁器', '油灯'],
    'Rahu': ['黑芥末(Black Mustard)', '蓝布', '铁器', '蓝宝石替代品'],
    'Ketu': ['芝麻(Sesame)', '多色布', '灯笼', '猫眼石替代品'],
}

PLANET_FAST_DAYS = {
    'Sun': '周日 (Sunday)', 'Moon': '周一 (Monday)',
    'Mars': '周二 (Tuesday)', 'Mercury': '周三 (Wednesday)',
    'Jupiter': '周四 (Thursday)', 'Venus': '周五 (Friday)',
    'Saturn': '周六 (Saturday)', 'Rahu': '周六 (Saturday)',
    'Ketu': '周二 (Tuesday)',
}

PLANET_COLORS = {
    'Sun': '红/金/橙', 'Moon': '白/银/乳白', 'Mars': '红/珊瑚色',
    'Mercury': '绿/浅绿', 'Jupiter': '黄/金色',
    'Venus': '白/粉/彩虹', 'Saturn': '黑/深蓝/紫',
    'Rahu': '深蓝/烟灰', 'Ketu': '斑点/多色',
}

STRENGTH_THRESHOLDS = {
    'weak': 0.5,      # Rupa < 0.5 → 极度需要补救
    'moderate': 0.75,  # 0.5-0.75 → 轻���补救
}


def recommend_remedies(shadbala_results: Dict, planet_dignities: Dict = None,
                       active_dasha_lord: str = None, doshas: List[str] = None) -> Dict:
    """
    基于行星力量分析推荐补救措施。

    Args:
        shadbala_results: Shadbala结果 {planet: {'total_rupas': float, 'strength_level': str, ...}}
        planet_dignities: 行星尊严 {planet: dignity_level}
        active_dasha_lord: 当前大运主星
        doshas: 检测到的Dosha列表 ['Mangal Dosha', 'Kaal Sarp Dosha', ...]

    Returns:
        分类的补救建议
    """
    doshas = doshas or []
    recommendations = {
        'gems': [],
        'mantras': [],
        'donations': [],
        'fasting': [],
        'lifestyle': [],
        'dosha_remedies': [],
    }

    # 分析需要补救的行星
    weak_planets = []
    moderate_planets = []
    evidence_chain = []

    for planet, data in shadbala_results.items():
        rupas = data.get('total_rupas', data.get('rupas', 1.0))
        if rupas < STRENGTH_THRESHOLDS['weak']:
            weak_planets.append(planet)
            evidence_chain.append({
                'source': 'shadbala',
                'planet': planet,
                'severity': 'high',
                'value': round(rupas, 3) if isinstance(rupas, (int, float)) else rupas,
                'threshold': STRENGTH_THRESHOLDS['weak'],
                'reason': f'{planet} Shadbala低于极弱阈值',
            })
        elif rupas < STRENGTH_THRESHOLDS['moderate']:
            moderate_planets.append(planet)
            evidence_chain.append({
                'source': 'shadbala',
                'planet': planet,
                'severity': 'medium',
                'value': round(rupas, 3) if isinstance(rupas, (int, float)) else rupas,
                'threshold': STRENGTH_THRESHOLDS['moderate'],
                'reason': f'{planet} Shadbala低于偏弱阈值',
            })

    # 1. 宝石建议（仅对极弱行星）
    for planet in weak_planets:
        if planet in PLANET_GEMS:
            g = PLANET_GEMS[planet]
            recommendations['gems'].append({
                'planet': planet,
                'gem': g['gem'],
                'metal': g['metal'],
                'finger': g['finger'],
                'day': g['day'],
                'severity': 'high',
                'note': f'{planet}极度虚弱，建议佩戴{g["gem"]}镶嵌于{g["metal"]}，戴在{g["finger"]}上。首次佩戴应在{g["day"]}日出后。'
            })

    for planet in moderate_planets:
        if planet in PLANET_GEMS:
            g = PLANET_GEMS[planet]
            recommendations['gems'].append({
                'planet': planet,
                'gem': g['gem'],
                'metal': g['metal'],
                'severity': 'medium',
                'note': f'{planet}偏弱，可考虑佩戴{g["gem"]}作为辅助。'
            })

    # 2. 咒语建议
    for planet in weak_planets + moderate_planets:
        if planet in PLANET_MANTRAS:
            recs = 108 if planet in weak_planets else 27
            recommendations['mantras'].append({
                'planet': planet,
                'mantra': PLANET_MANTRAS[planet],
                'repetitions': recs,
                'note': f'每日念诵 {PLANET_MANTRAS[planet]} × {recs}遍',
            })

    # 3. 大运主星特别建议
    if active_dasha_lord and active_dasha_lord in PLANET_MANTRAS:
        recommendations['mantras'].append({
            'planet': active_dasha_lord,
            'mantra': PLANET_MANTRAS[active_dasha_lord],
            'repetitions': 108,
            'note': f'当前大运为{active_dasha_lord}期间，建议强化念诵 {PLANET_MANTRAS[active_dasha_lord]}',
            'priority': 'dasha_lord',
        })
        evidence_chain.append({
            'source': 'dasha',
            'planet': active_dasha_lord,
            'severity': 'context',
            'reason': f'当前大运主星为{active_dasha_lord}，补救优先级上调',
        })

    # 4. 捐赠建议
    for planet in weak_planets[:3]:  # Top 3 weakest
        if planet in PLANET_DONATIONS:
            items = ', '.join(PLANET_DONATIONS[planet][:2])
            recommendations['donations'].append({
                'planet': planet,
                'items': PLANET_DONATIONS[planet],
                'note': f'捐赠{planet}相关物品：{items}等。在{PLANET_FAST_DAYS.get(planet, "适当日子")}捐赠效果最佳。',
            })

    # 5. 斋戒建议
    for planet in weak_planets[:2]:
        recommendations['fasting'].append({
            'planet': planet,
            'day': PLANET_FAST_DAYS.get(planet, ''),
            'note': f'在{PLANET_FAST_DAYS.get(planet)}进行{planet}斋戒，从日出到日落。',
        })

    # 6. Dosha专项补救
    dosha_remedies_map = {
        'Mangal Dosha': {
            'actions': ['Kumbha Vivah (与无花果/香蕉树先"结婚"后再与人结婚)', 'Mangal Chandika Path', '周二火星斋戒'],
            'gem': '红珊瑚 (Red Coral)',
        },
        'Kaal Sarp Dosha': {
            'actions': ['Rahu-Ketu Shanti Puja', '那伽潘查米节祭拜蛇神', '参观12个Jyotirlinga'],
            'gem': '天河石+猫眼石组合',
        },
        'Nadi Dosha': {
            'actions': ['Nadi Shanti Puja', 'Mahamrityunjaya Mantra', '捐赠谷物'],
            'gem': None,
        },
        'Pitra Dosha': {
            'actions': ['Amavasya祖先祭拜', '捐赠黑芝麻和铁器', '供养婆罗门'],
            'gem': None,
        },
    }

    for dosha_name in doshas:
        if dosha_name in dosha_remedies_map:
            dr = dosha_remedies_map[dosha_name]
            recommendations['dosha_remedies'].append({
                'dosha': dosha_name,
                'actions': dr['actions'],
                'gem': dr.get('gem'),
                'note': f'{dosha_name}检测到。建议进行: {"; ".join(dr["actions"][:2])}',
            })
            evidence_chain.append({
                'source': 'dosha',
                'dosha': dosha_name,
                'severity': 'context',
                'reason': f'{dosha_name}命中，生成专项补救建议',
            })

    # 7. 生活建议
    colors = []
    for planet in weak_planets[:3]:
        if planet in PLANET_COLORS:
            colors.append(PLANET_COLORS[planet])
    if colors:
        recommendations['lifestyle'].append({
            'type': '色彩疗愈',
            'note': f'多使用{", ".join(colors)}色系的衣物和装饰物',
        })

    if 'Saturn' in weak_planets:
        recommendations['lifestyle'].append({
            'type': '土星平和',
            'note': '周六拜访Shani寺庙，提供芥末油灯。避免穿黑色。',
        })

    # 建议摘要
    total_recs = sum(len(v) for v in recommendations.values())
    summary = f'共{total_recs}条补救建议 — 重点关注: {", ".join(weak_planets[:3]) if weak_planets else "无极度虚弱行星"}'
    next_action = (
        '先执行咒语、捐赠、生活调整等低风险补救；宝石、斋戒和仪式类建议需结合体质、预算与专业意见二次确认。'
        if total_recs else
        '当前未发现必须补救的弱项，保持观察并等待Dasha/Transit触发再复核。'
    )

    return {
        'method': 'BPHS补救系统 v1.0',
        'weak_planets': weak_planets,
        'moderate_planets': moderate_planets,
        'recommendations': recommendations,
        'evidence_chain': evidence_chain,
        'next_action': next_action,
        'summary': summary,
    }


def quick_remedy(planet: str, severity: str = 'weak') -> Dict:
    """快速获取单行星补救建议"""
    result = {}
    if planet in PLANET_GEMS:
        g = PLANET_GEMS[planet]
        result['gem'] = f'{g["gem"]} 镶{g["metal"]} 戴{g["finger"]} ({g["day"]})'
    if planet in PLANET_MANTRAS:
        result['mantra'] = f'{PLANET_MANTRAS[planet]} × {"108" if severity == "weak" else "27"}'
    if planet in PLANET_FAST_DAYS:
        result['fast'] = f'{PLANET_FAST_DAYS[planet]} 斋戒'
    if planet in PLANET_DONATIONS:
        result['donate'] = ', '.join(PLANET_DONATIONS[planet][:2])
    return result
