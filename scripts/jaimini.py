#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jaimini占星体系模块 v1.1
Parashara传承中的Jaimini子系统

支持:
  - Chara Karaka: 7/8个功能指示星（按度数排序）
  - Karakamsha: AK在Navamsa中的上升（灵魂方向）
  - Chara Dasha: 当前为简化 timing 实现，v6.0.9 后标注为 partial，不得单独作为高置信度应期依据
  - Jaimini Sutras关键规则
"""
from typing import Dict, List, Tuple, Optional
import math

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

# Chara Karaka 定义（7星制，排除Rahu）
KARAKA_7 = {
    1: 'Atmakaraka',    # AK - 灵魂指示星（度数最高）
    2: 'Amatyakaraka',  # AmK - 事业/顾问
    3: 'Bhratrikaraka', # BK - 兄弟/勇气
    4: 'Matrikaraka',   # MK - 母亲
    5: 'Putrakaraka',   # PK - 子女
    6: 'Gnatikaraka',   # GK - 敌人/障碍
    7: 'Darakaraka',    # DK - 配偶（度数最低）
}

# 8星制（含Rahu，用绝对度数）
KARAKA_8 = {
    1: 'Atmakaraka', 2: 'Amatyakaraka', 3: 'Bhratrikaraka', 4: 'Matrikaraka',
    5: 'Putrakaraka', 6: 'Gnatikaraka', 7: 'Darakaraka', 8: 'Pitrukaraka',
}

KARAKA_CN = {
    'Atmakaraka': '灵魂星AK', 'Amatyakaraka': '事业星AmK',
    'Bhratrikaraka': '兄弟星BK', 'Matrikaraka': '母亲星MK',
    'Putrakaraka': '子女星PK', 'Gnatikaraka': '障碍星GK',
    'Darakaraka': '配偶星DK', 'Pitrukaraka': '父亲星PiK',
}

KARAKA_DOMAINS = {
    'Atmakaraka': '灵魂使命、核心自我、人生最高目标',
    'Amatyakaraka': '事业方向、主要谋士、权力代理',
    'Bhratrikaraka': '兄弟姐妹、勇气、冒险精神',
    'Matrikaraka': '母亲、家庭根基、情感安全感',
    'Putrakaraka': '子女、创造力、学生、智能成果',
    'Gnatikaraka': '竞争对手、疾病、障碍、转化力量',
    'Darakaraka': '配偶特质、伴侣关系、婚姻质量',
    'Pitrukaraka': '父亲、祖先业力、传统传承',
}


def calc_chara_karaka_7(planet_degrees: Dict[str, float]) -> Dict:
    """
    计算7星制Chara Karaka（度数最高→AK，最低→DK）
    
    参数: planet_degrees = {'Sun': 12.5, 'Moon': 8.3, ...}
          每个行星在星座内的度数（0-30）
    
    返回: {karaka_name: {'planet': str, 'degree': float, 'domain': str}}
    """
    # 排除Rahu和Ketu
    exclude = {'Rahu', 'Ketu'}
    planets = {k: v for k, v in planet_degrees.items() if k not in exclude}
    
    # 按度数降序排列（度数最高的=AK）
    sorted_planets = sorted(planets.items(), key=lambda x: x[1], reverse=True)
    
    results = {}
    for rank, (pname, deg) in enumerate(sorted_planets, 1):
        if rank > 7:
            break
        karaka = KARAKA_7[rank]
        results[karaka] = {
            'planet': pname,
            'degree_in_sign': round(deg, 4),
            'rank': rank,
            'domain': KARAKA_DOMAINS.get(karaka, ''),
            'cn_name': KARAKA_CN.get(karaka, karaka),
        }
    
    # 额外分析
    ak = results.get('Atmakaraka', {})
    dk = results.get('Darakaraka', {})
    
    return {
        'karaka_table': results,
        'summary': {
            'AK': f"{ak.get('planet','?')} ({ak.get('degree_in_sign',0):.1f}°)",
            'DK': f"{dk.get('planet','?')} ({dk.get('degree_in_sign',0):.1f}°)",
            'AK_domain': ak.get('domain', ''),
            'DK_domain': dk.get('domain', ''),
        }
    }


def calc_chara_karaka_8(planet_degrees: Dict[str, float]) -> Dict:
    """
    计算8星制Chara Karaka（含Rahu，使用30-度数来处理Rahu逆行）
    """
    planets = {}
    for pname, deg in planet_degrees.items():
        if pname == 'Ketu':
            continue
        if pname == 'Rahu':
            # Rahu直接使用星座内度数（与其它行星相同），不做取反
            planets[pname] = deg
        else:
            planets[pname] = deg
    
    sorted_planets = sorted(planets.items(), key=lambda x: x[1], reverse=True)
    
    results = {}
    for rank, (pname, deg) in enumerate(sorted_planets, 1):
        if rank > 8:
            break
        karaka = KARAKA_8[rank]
        results[karaka] = {
            'planet': pname,
            'degree_in_sign': round(deg, 4),
            'rank': rank,
            'domain': KARAKA_DOMAINS.get(karaka, ''),
            'cn_name': KARAKA_CN.get(karaka, karaka),
        }
    
    return {'karaka_table_8': results}


def calc_chara_dasha(asc_sign_idx: int, 
                     planet_longitudes: Dict[str, float],
                     birth_year: int, birth_month: int) -> Dict:
    """
    Chara Dasha计算（简化实现；v6.0.9 后能力状态为 partial）
    
    规则:
      - 从上升星座开始
      - 奇数星座（Aries, Gemini...）：正向顺序
      - 偶数星座（Taurus, Cancer...）：反向顺序
      - 每个大运长度 = 12 - 该星座内的行星数量（用特定规则）
      - 注意：该实现不是 KN Rao / PVN Rao / Iranganti 完整传统算法；只能作低权重辅助
    """
    # 确定顺序方向
    is_odd = asc_sign_idx % 2 == 0
    direction = 1 if is_odd else -1
    
    # 生成大运序列
    dasha_sequence = []
    current = asc_sign_idx
    
    # 简化 Chara Dasha: 按上升星座顺/逆排列；不等同于 KN Rao/PVN Rao/Iranganti 完整传统算法
    for i in range(12):
        sign_idx = (current + direction * i) % 12
        sign_name = SIGNS[sign_idx]
        lord = SIGN_LORDS[sign_name]
        
        # 大运长度计算（简化版：基于星座的默认年数）
        # 标准法：大运长度 = 基于该星座中行星的Karakamsa计算
        # 简化法：每个大运1年
        duration = _chara_dasha_duration(sign_idx, planet_longitudes)
        
        dasha_sequence.append({
            'sign': sign_name,
            'sign_idx': sign_idx,
            'lord': lord,
            'duration_years': duration,
            'order': i + 1,
        })
    
    # 计算日期
    total_years = sum(d['duration_years'] for d in dasha_sequence)
    current_year = birth_year
    current_month = birth_month
    
    for d in dasha_sequence:
        d['start_date'] = f"{current_year}-{current_month:02d}"
        end_month = current_month + int(d['duration_years'] * 12)
        end_year = current_year + end_month // 12
        end_month = end_month % 12
        if end_month == 0:
            end_month = 12
            end_year -= 1
        d['end_date'] = f"{end_year}-{end_month:02d}"
        current_year = end_year
        current_month = end_month + 1
        if current_month > 12:
            current_month = 1
            current_year += 1
    
    return {
        'ascendant': SIGNS[asc_sign_idx],
        'direction': 'forward' if is_odd else 'backward',
        'dasha_sequence': dasha_sequence,
        'total_years': total_years,
    }


def calc_chara_dasha_with_antardasha(asc_sign_idx: int,
                                      planet_longitudes: Dict[str, float],
                                      birth_year: int, birth_month: int) -> Dict:
    """
    Chara Dasha 计算含 Antardasha 子周期（简化 timing 实现，能力状态 partial）

    Antardasha 规则:
      - 在每个 Mahadasha 内，Antardasha 从 Mahadasha 星座开始
      - 方向与 Mahadasha 方向相同
      - 每个 Antardasha 时长 = (该子星座大运年数 / 总大运年数) * Mahadasha 年数
      - 生成 12 个 Antardasha
    """
    # 先算 Mahadasha
    base = calc_chara_dasha(asc_sign_idx, planet_longitudes, birth_year, birth_month)
    is_odd = asc_sign_idx % 2 == 0
    direction = 1 if is_odd else -1
    base_total = sum(_chara_dasha_duration((asc_sign_idx + direction * i) % 12, planet_longitudes) for i in range(12))

    # 为每个 Mahadasha 计算 Antardasha
    for md in base['dasha_sequence']:
        md_sign_idx = md['sign_idx']
        md_duration = md['duration_years']
        antardasha_list = []

        # Antardasha 也从该 Mahadasha 星座开始，同方向
        for j in range(12):
            ad_sign_idx = (md_sign_idx + direction * j) % 12
            ad_sign = SIGNS[ad_sign_idx]
            ad_lord = SIGN_LORDS[ad_sign]

            # 子周期时长 = (该星座独立年数 / 总年数) * Mahadasha 年数
            ad_independent_duration = _chara_dasha_duration(ad_sign_idx, planet_longitudes)
            ad_duration = round((ad_independent_duration / base_total) * md_duration, 2)
            if ad_duration < 0.01:
                ad_duration = 0.01  # 最小约4天

            antardasha_list.append({
                'sign': ad_sign,
                'sign_idx': ad_sign_idx,
                'lord': ad_lord,
                'duration_years': ad_duration,
                'order': j + 1,
            })

        # 计算 Antardasha 日期
        start_year, start_month = map(int, md['start_date'].split('-'))
        for ad in antardasha_list:
            ad['start_date'] = f"{start_year}-{start_month:02d}"
            total_months = round(ad['duration_years'] * 12)
            end_month = start_month + total_months
            end_year = start_year + (end_month - 1) // 12
            end_month = ((end_month - 1) % 12) + 1
            ad['end_date'] = f"{end_year}-{end_month:02d}"
            # 下一个 Antardasha 的开始
            if end_month < 12:
                start_year = end_year
                start_month = end_month + 1
            else:
                start_year = end_year + 1
                start_month = 1

        md['antardashas'] = antardasha_list

    base['has_antardasha'] = True
    return base


def _chara_dasha_duration(sign_idx, planet_lons):
    """计算Chara Dasha单个大运的年数"""
    # 标准方法：12 - 落入该星座的行星数量（最少1年，最多12年）
    count = 0
    for pname, lon in planet_lons.items():
        if pname in ('Rahu', 'Ketu'):
            continue
        p_sign = int(lon / 30) % 12
        if p_sign == sign_idx:
            count += 1
    return max(1, 12 - count)


def calc_karakamsha(ak_sign_in_d9: str, ak_degree_in_d9: float) -> Dict:
    """
    Karakamsha分析：AK（Atmakaraka，灵魂星）在D9中的位置作为"灵魂上升"
    这是Jaimini体系中判断人生终极方向的关键技法
    
    经典定义：Karakamsha = Atmakaraka在Navamsa(D9)中落入的星座
    从这个星座看12宫的布局，分析灵魂方向
    
    ⚠️ 2026-05-03修正：此前版本错误使用DK（配偶星），现已修正为AK（灵魂星）
    
    参数:
        ak_sign_in_d9: AK（灵魂星）在D9中的星座
        ak_degree_in_d9: AK在D9中的度数
    """
    sign_idx = SIGNS.index(ak_sign_in_d9) if ak_sign_in_d9 in SIGNS else 0
    lord = SIGN_LORDS.get(ak_sign_in_d9, '')
    
    # Karakamsha Lagna = AK（灵魂星）在D9中的位置
    # 从这个位置看12宫的布局，分析灵魂方向
    interpretations = _karakamsha_interpretations(ak_sign_in_d9, lord)
    
    return {
        'karakamsha_sign': ak_sign_in_d9,
        'karakamsha_degree': ak_degree_in_d9,
        'karakamsha_lord': lord,
        'soul_direction': interpretations,
    }


def _karakamsha_interpretations(sign, lord):
    """Karakamsha的灵魂方向解读"""
    directions = {
        'Aries': '灵魂追求独立、开拓、成为先驱',
        'Taurus': '灵魂追求稳定、物质安全感、感官和谐',
        'Gemini': '灵魂追求知识、沟通、多元体验',
        'Cancer': '灵魂追求情感连接、家庭、滋养他人',
        'Leo': '灵魂追求创造力、领导力、自我表达',
        'Virgo': '灵魂追求服务、完善、分析能力',
        'Libra': '灵魂追求平衡、关系和谐、美学',
        'Scorpio': '灵魂追求转化、深层真相、神秘学',
        'Sagittarius': '灵魂追求真理、哲学、智慧传播',
        'Capricorn': '灵魂追求成就、结构、社会贡献',
        'Aquarius': '灵魂追求革新、人道主义、群体觉醒',
        'Pisces': '灵魂追求灵性、超越、无条件的爱',
    }
    lord_meanings = {
        'Sun': '通过权威、创造力和自我实现达成',
        'Moon': '通过情感智慧、直觉和公众影响力达成',
        'Mars': '通过行动力、勇气和技术能力达成',
        'Mercury': '通过智慧、沟通和学习能力达成',
        'Jupiter': '通过智慧、教导和灵性成长达成',
        'Venus': '通过美学、关系和创造力达成',
        'Saturn': '通过耐力、自律和长期承诺达成',
    }
    return {
        'sign_direction': directions.get(sign, ''),
        'lord_method': lord_meanings.get(lord, ''),
    }


# ============================================================================
# Darakaraka (DK) 计算 —— v6.0.14 新增
# ============================================================================

def calc_darakaraka(planet_degrees: Dict[str, float],
                    use_8karaka: bool = False) -> Dict:
    """
    计算 Darakaraka (DK) —— Jaimini 体系中代表配偶/伴侣的行星。

    规则（7星制）：
      - 排除 Rahu/Ketu，剩余7颗行星按度数升序排列
      - 度数最低的行星 = Darakaraka (DK) —— 配偶特质星
      - 度数最高的行星 = Atmakaraka (AK) —— 灵魂星

    规则（8星制）：
      - 含 Rahu，8颗行星按度数升序排列
      - 度数最低的 = DK，度数最高的 = AK

    参数：
        planet_degrees: {行星名: 星座内度数(0-30)}
        use_8karaka: 是否使用8星制（含Rahu）

    返回：
        {
            'DK': {'planet': str, 'degree': float, 'rank': 7(7星制)或8(8星制)},
            'AK': {'planet': str, 'degree': float, 'rank': 1},
            'all_karaka': {rank: {'planet','degree','name'}},
            'dk_interpretation': str,
            'marriage_significator': str,
        }
    """
    if use_8karaka:
        planets = {k: v for k, v in planet_degrees.items() if k != 'Ketu'}
        karaka_def = KARAKA_8
        total = 8
    else:
        planets = {k: v for k, v in planet_degrees.items()
                   if k not in ('Rahu', 'Ketu')}
        karaka_def = KARAKA_7
        total = 7

    # 按度数升序排列（度数最低=DK）
    sorted_p = sorted(planets.items(), key=lambda x: x[1])

    all_karaka = {}
    dk_info = None
    ak_info = None

    for rank, (pname, deg) in enumerate(sorted_p[:total], 1):
        karaka_name = karaka_def[rank]
        entry = {
            'planet': pname,
            'degree_in_sign': round(deg, 4),
            'rank': rank,
            'name': karaka_name,
            'cn_name': KARAKA_CN.get(karaka_name, karaka_name),
            'domain': KARAKA_DOMAINS.get(karaka_name, ''),
        }
        all_karaka[rank] = entry
        if karaka_name == 'Darakaraka':
            dk_info = entry
        if karaka_name == 'Atmakaraka':
            ak_info = entry

    # 解读 DK
    dk_planet = dk_info['planet'] if dk_info else '?'
    dk_interp = _dk_interpretation(dk_planet)
    marriage_sig = _marriage_significator(dk_planet, ak_info['planet'] if ak_info else '?')

    return {
        'DK': dk_info,
        'AK': ak_info,
        'all_karaka': all_karaka,
        'dk_planet': dk_planet,
        'dk_degree': dk_info['degree_in_sign'] if dk_info else None,
        'dk_interpretation': dk_interp,
        'marriage_significator': marriage_sig,
        'use_8karaka': use_8karaka,
    }


def _dk_interpretation(dk_planet: str) -> str:
    """Darakaraka 行星的配偶特质解读"""
    interpretations = {
        'Sun': '配偶有权威感、领导力强，可能比命主年长或地位高；关系中需要尊重和认可',
        'Moon': '配偶情感丰富、重视家庭，情绪敏感；关系以情感连接为核心',
        'Mars': '配偶行动力强、有魄力，可能性格急躁；关系中需要空间和尊重',
        'Mercury': '配偶聪明、善于沟通，可能从事文书/教育/商业；关系以交流为基础',
        'Jupiter': '配偶有智慧、教导型人格，可能从事教育/法律/宗教；关系有成长导向',
        'Venus': '配偶有魅力、重视美学和享受，浪漫且物质条件好；关系充满爱和美好',
        'Saturn': '配偶成熟稳重、有责任感，可能年龄差距较大；关系需要时间和承诺',
        'Rahu': '配偶背景复杂、有野心，可能来自不同文化/阶层；关系有非常规色彩',
        'Ketu': '配偶有灵性倾向、可能疏离，关系有超脱/宿命感',
    }
    return interpretations.get(dk_planet, f'DK={dk_planet}，需结合全盘分析')


def _marriage_significator(dk: str, ak: str) -> str:
    """AK-DK 关系对婚姻的综合指示"""
    # AK=灵魂，DK=配偶，两者关系反映灵魂与伴侣的互动模式
    relations = {
        ('Sun', 'Moon'): '灵魂（Sun）与情感（Moon）结合，婚姻中有父性保护色彩',
        ('Moon', 'Sun'): '情感（Moon）与权威（Sun）结合，配偶可能是引导者/权威人物',
        ('Venus', 'Jupiter'): '爱（Venus）与智慧（Jupiter）结合，婚姻有成长和教育意义',
        ('Jupiter', 'Venus'): '智慧（Jupiter）与爱（Venus）结合，配偶带来美感和快乐',
    }
    key = (ak, dk)
    return relations.get(key, f'AK={ak}与DK={dk}的组合，需结合两者星座/宫位深入分析')


def calc_dk_marriage_analysis(dk_planet: str,
                              dk_sign: str,
                              dk_house: int,
                              ak_sign: str,
                              ak_house: int,
                              venus_sign: str,
                              venus_house: int,
                              seventh_lord: str,
                              seventh_lord_sign: str) -> Dict:
    """
    综合 DK 信息进行婚姻分析（v6.0.14 新增）

    参数：
        dk_planet: DK行星名
        dk_sign: DK所在星座
        dk_house: DK所在宫位（1-12）
        ak_sign: AK所在星座
        ak_house: AK所在宫位
        venus_sign: Venus所在星座
        venus_house: Venus所在宫位
        seventh_lord: 第七宫宫主星
        seventh_lord_sign: 第七宫宫主星所在星座

    返回：婚姻分析字典
    """
    # DK 在宫位的解读
    dk_house_meaning = _dk_house_meaning(dk_house)

    # Venus 与 DK 的关系
    venus_dk_relation = _venus_dk_relation(venus_sign, dk_sign, venus_house, dk_house)

    # 第七宫分析
    seventh_analysis = _seventh_house_analysis(seventh_lord, seventh_lord_sign)

    # 综合婚姻时机指示
    marriage_timing = _marriage_timing_indication(dk_planet, venus_sign, seventh_lord)

    return {
        'dk_planet': dk_planet,
        'dk_sign': dk_sign,
        'dk_house': dk_house,
        'dk_house_meaning': dk_house_meaning,
        'venus_dk_relation': venus_dk_relation,
        'seventh_analysis': seventh_analysis,
        'marriage_timing': marriage_timing,
        'summary': f"配偶星DK={dk_planet}在{dk_sign}第{dk_house}宫；{dk_house_meaning}",
    }


def _dk_house_meaning(house: int) -> str:
    """DK所在宫位对婚姻的意义"""
    meanings = {
        1: '配偶与命主高度相似，自我认同与伴侣融合',
        2: '配偶带来财富/家庭资源，可能通过婚姻改善经济状况',
        3: '配偶是命主的勇气来源，可能有兄弟姐妹牵线',
        4: '配偶带来情感安全感，家庭和谐，可能有房产',
        5: '配偶与子女/创造力有关，浪漫关系，可能有年龄差',
        6: '配偶可能是工作伙伴/竞争对手，关系中需注意健康/债务',
        7: '配偶是命主的直接伙伴，婚姻关系最直接',
        8: '配偶带来深层转化，可能涉及神秘事务/遗产/危机',
        9: '配偶有灵性/哲学导向，可能来自不同文化背景',
        10: '配偶与事业/社会地位有关，可能因工作相识',
        11: '配偶带来收益/社交网络，朋友变伴侣',
        12: '配偶涉及潜意识/海外/隐秘事务，可能是异地/外籍',
    }
    return meanings.get(house, '')


def _venus_dk_relation(venus_sign: str, dk_sign: str,
                        venus_house: int, dk_house: int) -> str:
    """Venus与DK的关系分析"""
    # 简化：看两者是否同一星座或相邻宫位
    venus_idx = SIGNS.index(venus_sign) if venus_sign in SIGNS else -1
    dk_idx = SIGNS.index(dk_sign) if dk_sign in SIGNS else -1

    if venus_idx >= 0 and dk_idx >= 0:
        diff = abs(venus_idx - dk_idx)
        if diff <= 1 or diff >= 11:
            return 'Venus与DK能量融合，爱与婚姻高度一致'
        elif diff <= 3:
            return 'Venus与DK有一定张力，爱情与婚姻选择可能有分歧'
        else:
            return 'Venus与DK度数较远，爱情观与婚姻现实有差距'

    return 'Venus/DK关系需结合全盘确定'


def _seventh_house_analysis(seventh_lord: str, seventh_lord_sign: str) -> str:
    """第七宫宫主星分析"""
    lord_meanings = {
        'Sun': '配偶有领导力，可能从事管理/政府工作',
        'Moon': '配偶情感丰富，可能从事护理/餐饮/海洋相关',
        'Mars': '配偶有行动力，可能从事技术/军事/体育',
        'Mercury': '配偶聪明善辩，可能从事教育/写作/商业',
        'Jupiter': '配偶有智慧，可能从事教育/法律/宗教',
        'Venus': '配偶有魅力，可能从事艺术/娱乐/美容',
        'Saturn': '配偶成熟稳重，可能从事结构/建筑/长期项目',
    }
    return lord_meanings.get(seventh_lord, f'第七宫主星={seventh_lord}，需结合全盘')


def _marriage_timing_indication(dk_planet: str, venus_sign: str,
                                seventh_lord: str) -> str:
    """婚姻时机的简化指示（需结合Dasha/Transit使用）"""
    return (f"婚姻窗口与DK={dk_planet}、Venus在{venus_sign}、"
            f"第七宫主星={seventh_lord}的Dasha/Transit高度相关；"
            f"具体应期需结合Vimshottari Dasha和Gochara（过境）确定")
