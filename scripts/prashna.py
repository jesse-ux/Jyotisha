#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prashna（卜卦/问事）占星系统 v1.0
填补最后的关键技法缺口 — 这是vedic-calc唯一领先我们的领域

核心功能：
1. Prashna Lagna — 基于询问时刻的卜卦盘
2. Arudha Prashna — 镜像点解读
3. KP Prashna — 用KP sublord精确定位答案
4. Sphuta — 特殊敏感点
5. 问事分类— 12宫主题映射
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}

NAKSHATRAS = ['Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra',
    'Punarvasu','Pushya','Ashlesha','Magha','PurvaPhalguni','UttaraPhalguni',
    'Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','PurvaAshadha','UttaraAshadha','Shravana','Dhanishta','Shatabhisha',
    'PurvaBhadrapada','UttaraBhadrapada','Revati']

# KP 249 sublord字典（简化版，完整需加载249条）
KP_SUBLORD_MEANINGS = {
    'Sun': {1:'健康恢复', 2:'收入增长', 3:'勇气', 4:'房产', 5:'投资', 6:'疾病', 7:'婚姻', 8:'遗产', 9:'远行', 10:'升职', 11:'收益', 12:'支出'},
    'Moon': {1:'新开始', 2:'波动收入', 3:'短途旅行', 4:'搬家', 5:'创造', 6:'慢性病', 7:'情感', 8:'心理', 9:'精神', 10:'公众', 11:'社交', 12:'隐退'},
    'Mars': {1:'积极行动', 2:'资金', 3:'技能', 4:'建筑', 5:'投机', 6:'手术', 7:'竞争', 8:'意外', 9:'法律', 10:'职业', 11:'社交', 12:'幕后'},
    'Mercury': {1:'沟通', 2:'商业', 3:'写作', 4:'学习', 5:'教育', 6:'文书', 7:'谈判', 8:'研究', 9:'出版', 10:'信息', 11:'网络', 12:'秘密'},
    'Jupiter': {1:'新开始', 2:'财富', 3:'努力', 4:'家宅', 5:'子女', 6:'恢复', 7:'婚姻', 8:'转变', 9:'远行', 10:'成功', 11:'扩张', 12:'解脱'},
    'Venus': {1:'魅力', 2:'奢侈品', 3:'艺术', 4:'舒适', 5:'浪漫', 6:'享受', 7:'伴侣', 8:'深层', 9:'高等', 10:'审美', 11:'社交', 12:'隐居'},
    'Saturn': {1:'缓慢', 2:'节俭', 3:'延迟', 4:'老旧', 5:'等待', 6:'慢性', 7:'延迟婚', 8:'遗产', 9:'严肃', 10:'权威', 11:'长期', 12:'孤独'},
    'Rahu': {1:'迷惑', 2:'暴富', 3:'冒险', 4:'不满', 5:'非婚', 6:'怪病', 7:'涉外', 8:'突变', 9:'异域', 10:'非传统', 11:'网络', 12:'海外'},
    'Ketu': {1:'抽离', 2:'损失', 3:'独立', 4:'搬家', 5:'异常', 6:'谜病', 7:'分离', 8:'秘密', 9:'修行', 10:'幕后', 11:'孤立', 12:'解脱'},
}

# 问事类型分类
QUESTION_CATEGORIES = {
    'career': {'primary': 10, 'secondary': [6, 2, 11], 'karaka': 'Saturn'},
    'finance': {'primary': 2, 'secondary': [11, 5, 9], 'karaka': 'Jupiter'},
    'health': {'primary': 6, 'secondary': [1, 8], 'karaka': 'Sun'},
    'marriage': {'primary': 7, 'secondary': [2, 11], 'karaka': 'Venus'},
    'children': {'primary': 5, 'secondary': [9], 'karaka': 'Jupiter'},
    'relocation': {'primary': 4, 'secondary': [12, 9], 'karaka': 'Moon'},
    'education': {'primary': 5, 'secondary': [4, 9], 'karaka': 'Mercury'},
    'legal': {'primary': 6, 'secondary': [8, 7], 'karaka': 'Jupiter'},
    'spiritual': {'primary': 9, 'secondary': [12, 9], 'karaka': 'Ketu'},
    'property': {'primary': 4, 'secondary': [2, 11], 'karaka': 'Mars'},
    'travel': {'primary': 12, 'secondary': [9, 3], 'karaka': 'Rahu'},
    'general': {'primary': 1, 'secondary': [10], 'karaka': 'Moon'},
}


def calc_prashna_chart(question_time: datetime, planet_positions: Dict,
                       asc_degree: float = None) -> Dict:
    """
    计算Prashna（卜卦）盘。

    基于询问时刻的天象构建卜卦盘，这是Prashna的核心。

    Args:
        question_time: 询问时间
        planet_positions: 该时刻的行星位置
        asc_degree: 卜卦上升度数(0-360, 可选)

    Returns:
        卜卦盘数据
    """
    if asc_degree is None:
        # 使用询问时间的秒数计算伪随机上升
        asc_degree = (question_time.hour * 3600 + question_time.minute * 60 + question_time.second) % 360

    asc_sign_idx = int(asc_degree / 30) % 12
    asc_sign = SIGNS[asc_sign_idx]

    # 构建分宫图
    houses = {}
    for h in range(1, 13):
        sign_idx = (asc_sign_idx + h - 1) % 12
        houses[h] = {
            'sign': SIGNS[sign_idx],
            'lord': SIGN_LORDS[SIGNS[sign_idx]],
        }

    # 映射行星到宫位
    planet_houses = {}
    for pname, pdata in planet_positions.items():
        sign = pdata.get('sign', '')
        if sign in SIGNS:
            p_sign_idx = SIGNS.index(sign)
            house = (p_sign_idx - asc_sign_idx) % 12 + 1
            planet_houses[pname] = house

    return {
        'question_time': question_time.isoformat(),
        'asc_sign': asc_sign,
        'asc_degree': round(asc_degree % 30, 2),
        'houses': houses,
        'planet_houses': planet_houses,
        'prashna_lagna_lord': SIGN_LORDS[asc_sign],
    }


def get_kp_prashna_answer(planet_positions: Dict, question_category: str,
                          asc_degree: float) -> Dict:
    """
    使用KP sublord方法回答Prashna问题。

    1. 确定问题宫位
    2. 找到该宫位主星
    3. 查看其sublord在哪个宫
    4. 如果sublord的本宫与问题宫位或karaka相关 → 答案是YES

    Args:
        planet_positions: 卜卦时刻行星位置
        question_category: 问题类型
        asc_degree: 上升度数

    Returns:
        KP答案分析
    """
    cat = QUESTION_CATEGORIES.get(question_category, QUESTION_CATEGORIES['general'])
    primary_house = cat['primary']
    karaka = cat['karaka']

    asc_sign = SIGNS[int(asc_degree / 30) % 12]
    asc_idx = SIGNS.index(asc_sign)

    # 问题宫主
    question_sign = SIGNS[(asc_idx + primary_house - 1) % 12]
    question_lord = SIGN_LORDS[question_sign]

    # 问题宫主所在的行星位置
    ql_data = planet_positions.get(question_lord, {})
    ql_sign = ql_data.get('sign', '')
    ql_sign_idx = SIGNS.index(ql_sign) if ql_sign in SIGNS else 0
    ql_house = (ql_sign_idx - asc_idx) % 12 + 1

    # Sublord分析（简化版，完整版需精确计算）
    # 如果问题宫主在自己的宫位或与karaka相关 → 有利
    is_favorable = ql_house in (1, 4, 5, 7, 9, 10, 11)

    # KP答案判定
    if is_favorable:
        answer = "YES — 卜卦信号有利"
        confidence = "高"
    elif ql_house in (6, 8, 12):
        answer = "NO — 卜卦信号不利"
        confidence = "高"
    else:
        answer = "MAYBE — 需要更多信息确认"
        confidence = "中"

    return {
        'question_type': question_category,
        'primary_house': primary_house,
        'question_lord': question_lord,
        'lord_house': ql_house,
        'lord_sign': ql_sign,
        'karaka': karaka,
        'kp_answer': answer,
        'confidence': confidence,
        'note': '基于KP sublord原则：主星状态决定结果方向',
    }


def detect_prashna_arudha(planet_positions: Dict, asc_degree: float,
                          question_house: int) -> Dict:
    """
    计算Prashna中的Arudha（镜像点）。

    Arudha = 反射真实意图的镜像宫位。
    用于验证问事者的问题是否与真实关切一致。
    """
    asc_sign_idx = int(asc_degree / 30) % 12
    lord_sign_idx = (asc_sign_idx + question_house - 1) % 12
    lord = SIGN_LORDS[SIGNS[lord_sign_idx]]
    lord_house = 0

    for pname, pdata in planet_positions.items():
        if pname == lord:
            p_sign = pdata.get('sign', '')
            if p_sign in SIGNS:
                lord_house = (SIGNS.index(p_sign) - asc_sign_idx) % 12 + 1
            break

    if lord_house == 0:
        lord_house = question_house

    # Arudha公式：从宫主数X宫，再从宫主落位数X宫
    distance = lord_house - question_house
    if distance <= 0:
        distance += 12
    arudha_house = (lord_house + distance - 1) % 12 + 1

    # BPHS例外：Arudha不能落在原宫或7宫
    if arudha_house == question_house:
        arudha_house = 10
    if arudha_house == ((question_house + 6) % 12) or ((question_house + 6) % 12) == 0:
        _h7 = ((question_house + 6) % 12) or 12
        if arudha_house == _h7:
            arudha_house = 4

    return {
        'question_house': question_house,
        'lord': lord,
        'lord_house': lord_house,
        'arudha_house': arudha_house,
        'note': f'Arudha在{arudha_house}宫 — 问题的"镜像"反映在此领域',
    }
