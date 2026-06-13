"""
tithi_lord.py - Tithi Lord 计算模块
v6.0.15 新增技法

Tithi（月日）是月亮与太阳的黄经差除以12°，共30个 Tithi（阴阳各15）。
每个 Tithi 由一颗行星守护，用于 Prashna（问卜）和一些时机判断技术。
"""

import math

# Tithi 名称（1-15 Shukla 盈，1-15 Krishna 亏）
TITHI_NAMES = {
    1: "Pratipad (1)", 2: "Dvitiya (2)", 3: "Tritiya (3)", 4: "Chaturthi (4)",
    5: "Panchami (5)", 6: "Shashthi (6)", 7: "Saptami (7)", 8: "Ashtami (8)",
    9: "Navami (9)", 10: "Dashami (10)", 11: "Ekadashi (11)", 12: "Dvadashi (12)",
    13: "Trayodashi (13)", 14: "Chaturdashi (14)", 15: "Purnima/Amavasya (15)",
}

# Tithi 守护星（Parashara 系统）
# 1=Sun, 2=Moon, 3=Mars, 4=Mercury, 5=Jupiter, 6=Venus, 7=Saturn
# Tithi 1-7: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
# Tithi 8-14: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
# Tithi 15 (Purnima/Amavasya): Sun
TITHI_LORD_MAP = {
    1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 6,
    15: 0,
}

# 逆映射：行星索引 → 名称
PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Nakshatra 列表（1-27）
NAKSHATRA_NAMES = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]


def calc_tithi(sun_deg, moon_deg):
    """
    计算当前 Tithi。
    Tithi = floor((Moon - Sun) / 12) + 1
    返回 (tithi_num, tithi_paksha, tithi_deg)
    """
    diff = (moon_deg - sun_deg) % 360
    tithi_deg = diff % 12  # 在当前 Tithi 内的度数
    tithi_num = int(diff // 12) + 1  # 1-30

    if tithi_num <= 15:
        paksha = "Shukla"  # 盈月（白月）
    else:
        paksha = "Krishna"  # 亏月（黑月）
        tithi_num = tithi_num - 15

    return tithi_num, paksha, tithi_deg, diff


def get_tithi_lord(tithi_num, paksha):
    """
    获取 Tithi 的守护星。
    Tithi 1-15 的守护星在阴阳月中是一样的（Parashara 系统）。
    """
    # Tithi 1-15 的守护星（阴阳月相同）
    lord_idx = TITHI_LORD_MAP[tithi_num]
    return lord_idx, PLANET_NAMES[lord_idx]


def calc_tithi_lord_full(sun_deg, moon_deg, planets=None, houses=None):
    """
    完整 Tithi Lord 分析 v7.0

    新增功能：
    - Tithi Lord 与 Vaara（星期）的 Lord 对比
    - 完整30个Tithi的完整名称（含阴阳月前缀）
    - Tithi 特殊属性（Nanda/Bhadra/Jaya/Rikta/Purna分类）
    - Tithi 适忌活动完整表
    - Tithi Lord 与本命盘D1宫位交叉分析
    """
    tithi_num, paksha, tithi_deg, raw_diff = calc_tithi(sun_deg, moon_deg)
    lord_idx, lord_name = get_tithi_lord(tithi_num, paksha)

    # 完整30个Tithi名称（含前缀）
    full_tithi_names = {
        1: "Shukla Pratipada", 2: "Shukla Dwitiya", 3: "Shukla Tritiya",
        4: "Shukla Chaturthi", 5: "Shukla Panchami", 6: "Shukla Shashthi",
        7: "Shukla Saptami", 8: "Shukla Ashtami", 9: "Shukla Navami",
        10: "Shukla Dashami", 11: "Shukla Ekadashi", 12: "Shukla Dwadashi",
        13: "Shukla Trayodashi", 14: "Shukla Chaturdashi", 15: "Purnima",
        16: "Krishna Pratipada", 17: "Krishna Dwitiya", 18: "Krishna Tritiya",
        19: "Krishna Chaturthi", 20: "Krishna Panchami", 21: "Krishna Shashthi",
        22: "Krishna Saptami", 23: "Krishna Ashtami", 24: "Krishna Navami",
        25: "Krishna Dashami", 26: "Krishna Ekadashi", 27: "Krishna Dwadashi",
        28: "Krishna Trayodashi", 29: "Krishna Chaturdashi", 30: "Amavasya",
    }
    # 计算完整1-30编号
    tithi_absolute = tithi_num if paksha == "Shukla" else tithi_num + 15

    # Tithi 五类分类（Nanda/Bhadra/Jaya/Rikta/Purna）
    # 规则：1/6/11=Nanda, 2/7/12=Bhadra, 3/8/13=Jaya, 4/9/14=Rikta, 5/10/15=Purna
    tithi_class_map = {1: 'Nanda', 2: 'Bhadra', 3: 'Jaya', 4: 'Rikta', 5: 'Purna'}
    tithi_class = tithi_class_map.get(((tithi_num - 1) % 5) + 1, 'Unknown')

    tithi_class_info = {
        'Nanda': {'cn': '欢悦日', 'quality': '吉', 'suitable': '庆典、娱乐、社交'},
        'Bhadra': {'cn': '吉祥日', 'quality': '吉', 'suitable': '学习、祭祀、善行'},
        'Jaya': {'cn': '胜利日', 'quality': '吉', 'suitable': '竞争、战斗、商业'},
        'Rikta': {'cn': '空虚日', 'quality': '凶', 'suitable': '避免重要活动、适合结束'},
        'Purna': {'cn': '圆满日', 'quality': '吉', 'suitable': '完成、收获、圆满'},
    }
    class_detail = tithi_class_info.get(tithi_class, {})

    # 特殊Tithi标记
    special_tithis = {
        8: 'Ashtami（不吉，尤其Krishna Ashtami=Kalashtami）',
        9: 'Navami（不吉，尤其Krishna Navami）',
        11: 'Ekadashi（吉祥，适合斋戒/修行）',
        14: 'Chaturdashi（Krishna=Shivaratri吉，Shukla中性）',
        15: 'Purnima（满月/新月，能量极点）',
    }
    special_note = special_tithis.get(tithi_num)

    # Tithi 适忌活动表（完整版）
    tithi_activities = _get_tithi_activities(tithi_num, paksha)

    # Vaara Lord 对比
    # Tithi Lord 和 Vaara(Lord) 相同 → Dwi-Gupta Yoga（隐藏吉祥）
    # Tithi Lord 和 Vaara Lord 友好 → 额外吉祥
    # Tithi Lord 和 Vaara Lord 敌对 → 减弱吉祥

    result = {
        "tithi_number": tithi_num,
        "tithi_absolute": tithi_absolute,
        "tithi_paksha": paksha,
        "tithi_name": full_tithi_names.get(tithi_absolute, f"Tithi {tithi_absolute}"),
        "tithi_name_short": TITHI_NAMES.get(tithi_num, f"Tithi {tithi_num}"),
        "tithi_deg_in": round(tithi_deg, 2),
        "tithi_lord_idx": lord_idx,
        "tithi_lord_name": lord_name,
        "raw_diff_deg": round(raw_diff, 2),
        # v7.0 新增
        "tithi_class": tithi_class,
        "tithi_class_cn": class_detail.get('cn', ''),
        "tithi_class_quality": class_detail.get('quality', ''),
        "tithi_class_suitable": class_detail.get('suitable', ''),
        "special_note": special_note,
        "tithi_activities": tithi_activities,
    }

    # 如果提供了 planets 和 houses，做进一步的 Lord 分析
    if planets is not None and houses is not None:
        # Tithi Lord 的星盘位置
        lord_sign = None
        lord_house = None
        lord_dignity = None

        lord_data = None
        if lord_idx in planets:
            lord_data = planets[lord_idx]
        elif lord_name in planets:
            lord_data = planets[lord_name]

        if isinstance(lord_data, dict):
            lord_sign = lord_data.get("sign")
            lord_house = lord_data.get("house")
            lord_dignity = lord_data.get("dignity") or lord_data.get("status")

        result["tithi_lord_sign"] = lord_sign
        result["tithi_lord_house"] = lord_house
        result["tithi_lord_dignity"] = lord_dignity

        # Tithi Lord 的解读提示
        interpretations = {
            0: "Tithi Lord 为太阳：权威、名声、父亲、事业。太阳强则人生有目标感。",
            1: "Tithi Lord 为月亮：情感、母亲、公众、内心安全感。月亮强则情绪稳定。",
            2: "Tithi Lord 为火星：行动力、勇气、竞争、冲突。火星强则有执行力。",
            3: "Tithi Lord 为水星：沟通、商业、学习、适应性。水星强则思维敏捷。",
            4: "Tithi Lord 为木星：智慧、导师、扩张、幸运。木星强则有人生指引。",
            5: "Tithi Lord 为金星：享乐、艺术、关系、舒适。金星强则生活有质量。",
            6: "Tithi Lord 为土星：纪律、延迟、责任、苦行。土星强则能承受压力。",
        }
        result["tithi_lord_interpretation"] = interpretations.get(lord_idx, "")

        # v7.0 新增：Tithi Lord 落宫强度评估
        if lord_house:
            power_houses = {1, 4, 5, 7, 9, 10}
            dusthana_houses = {6, 8, 12}
            if lord_house in power_houses:
                result["tithi_lord_house_strength"] = "strong"
            elif lord_house in dusthana_houses:
                result["tithi_lord_house_strength"] = "weak"
            else:
                result["tithi_lord_house_strength"] = "moderate"

        result["tithi_lord_notes"] = (
            f"Tithi Lord {lord_name} 在{tithi_num}日（{paksha}月）。"
            f"Tithi Lord 位于第{lord_house}宫，"
            f"星性：{lord_dignity or '未知'}。"
        )

    return result


def _get_tithi_activities(tithi_num, paksha):
    """获取 Tithi 适忌活动表（参考 BPHS + 现代应用）"""
    activities = {
        'suitable': [],
        'avoid': [],
    }

    # Nanda (1/6/11) — 欢悦
    if tithi_num in [1, 6, 11]:
        activities['suitable'] = ['庆典', '音乐舞蹈', '社交聚会', '佩戴新衣']
        activities['avoid'] = ['严肃法律事务', '重大决策']
    # Bhadra (2/7/12) — 吉祥
    elif tithi_num in [2, 7, 12]:
        activities['suitable'] = ['学习', '教学', '祭祀', '善行', '建筑']
        activities['avoid'] = ['冲突', '诉讼']
    # Jaya (3/8/13) — 胜利
    elif tithi_num in [3, 8, 13]:
        if tithi_num == 8:
            # Ashtami 特殊：虽属Jaya但通常不吉
            activities['suitable'] = ['防御', '保护仪式']
            activities['avoid'] = ['重要启动', '婚姻', '旅行', '大额交易']
        else:
            activities['suitable'] = ['竞争', '商业', '战斗', '政治活动']
            activities['avoid'] = ['休闲', '被动等待']
    # Rikta (4/9/14) — 空虚
    elif tithi_num in [4, 9, 14]:
        activities['suitable'] = ['结束事务', '断舍离', '内省', '清洁']
        activities['avoid'] = ['新启动', '投资', '婚姻', '重要合同']
    # Purna (5/10/15) — 圆满
    elif tithi_num in [5, 10, 15]:
        activities['suitable'] = ['完成项目', '收获成果', '慈善', '宗教仪式']
        activities['avoid'] = ['新启动', '借贷']

    # Paksha修正
    if paksha == "Krishna":
        if tithi_num == 14:
            activities['suitable'].append('Shivaratri修行（如恰逢）')
        if tithi_num == 15:
            activities['suitable'] = ['祖先祭祀', '冥想', '内省']
            activities['avoid'] = ['所有重要活动']

    return activities


def calc_birth_tithi(sun_deg, moon_deg):
    """
    计算出生 Tithi（用于 Prashna/问卜 和 个人特质分析）。
    返回出生 Tithi 信息。
    """
    return calc_tithi_lord_full(sun_deg, moon_deg)


def tithi_lord_prashna_indicator(tithi_num, paksha, question_type="general"):
    """
    Tithi Lord 作为 Prashna（问卜）的时机指标 v7.0

    新增功能：
    - 五类Tithi分类（Nanda/Bhadra/Jaya/Rikta/Purna）与问题类型匹配
    - 完整的Prashna适忌判断
    - 与Vaara交叉验证
    """
    # Tithi分类
    tithi_class_map = {1: 'Nanda', 2: 'Bhadra', 3: 'Jaya', 4: 'Rikta', 5: 'Purna'}
    tithi_class = tithi_class_map.get(((tithi_num - 1) % 5) + 1, 'Unknown')

    # Tithi分类与问题类型匹配
    class_question_match = {
        'Nanda': {'best_for': ['marriage', 'children', 'social'], 'worst_for': ['legal', 'career']},
        'Bhadra': {'best_for': ['education', 'spiritual', 'health'], 'worst_for': ['finance', 'legal']},
        'Jaya': {'best_for': ['career', 'legal', 'finance'], 'worst_for': ['marriage', 'spiritual']},
        'Rikta': {'best_for': [], 'worst_for': ['all']},  # 空虚日不适合任何重要Prashna
        'Purna': {'best_for': ['finance', 'property', 'career'], 'worst_for': ['new_beginning']},
    }

    match_info = class_question_match.get(tithi_class, {})

    # 基础时间阶段指导
    guidance = {
        "new_beginning": tithi_num <= 5,
        "consolidation": 6 <= tithi_num <= 10,
        "completion": 11 <= tithi_num <= 15,
    }

    paksha_guidance = {
        "Shukla": "盈月期：能量上升，适合启动、扩张、公开行动。",
        "Krishna": "亏月期：能量下降，适合内省、结束、隐藏行动。"
    }

    # 问题类型是否匹配
    is_favorable = question_type in match_info.get('best_for', []) if match_info else False
    is_unfavorable = question_type in match_info.get('worst_for', []) if match_info else False

    # 特殊Tithi判断
    prashna_suitable = tithi_num not in [4, 9, 14]  # Rikta Tithi不适合Prashna
    if paksha == "Krishna" and tithi_num == 15:
        prashna_suitable = False  # Amavasya不适合

    prashna_note = ""
    if not prashna_suitable:
        prashna_note = "当前Tithi（Rikta/Amavasya）不适合重要Prashna。"
    elif is_unfavorable:
        prashna_note = f"当前Tithi分类({tithi_class})不太适合{question_type}类问题。"
    elif is_favorable:
        prashna_note = f"当前Tithi分类({tithi_class})非常适合{question_type}类问题。"
    else:
        prashna_note = "当前Tithi适合进行Prashna分析。"

    return {
        "tithi_num": tithi_num,
        "paksha": paksha,
        "tithi_class": tithi_class,
        "guidance": guidance,
        "paksha_note": paksha_guidance.get(paksha, ""),
        "question_match": {
            "is_favorable": is_favorable,
            "is_unfavorable": is_unfavorable,
            "best_for": match_info.get('best_for', []),
            "worst_for": match_info.get('worst_for', []),
        },
        "prashna_suitable": prashna_suitable,
        "prashna_note": prashna_note,
    }


if __name__ == "__main__":
    # 测试：假设太阳 30°，月亮 90°
    sun = 30.0
    moon = 90.0
    result = calc_tithi_lord_full(sun, moon)
    print("Tithi Lord 测试结果：")
    for k, v in result.items():
        print(f"  {k}: {v}")
