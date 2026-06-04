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
    完整 Tithi Lord 分析。
    输入：太阳度数、月亮度数、行星列表（可选）、宫位列表（可选）
    输出：Tithi 信息 + Lord 分析
    """
    tithi_num, paksha, tithi_deg, raw_diff = calc_tithi(sun_deg, moon_deg)
    lord_idx, lord_name = get_tithi_lord(tithi_num, paksha)

    result = {
        "tithi_number": tithi_num,
        "tithi_paksha": paksha,
        "tithi_name": TITHI_NAMES.get(tithi_num, f"Tithi {tithi_num}"),
        "tithi_deg_in": round(tithi_deg, 2),
        "tithi_lord_idx": lord_idx,
        "tithi_lord_name": lord_name,
        "raw_diff_deg": round(raw_diff, 2),
    }

    # 如果提供了 planets 和 houses，做进一步的 Lord 分析
    if planets is not None and houses is not None:
        # Tithi Lord 的星盘位置
        lord_sign = None
        lord_house = None
        lord_dignity = None

        # 从 planets 字典里找 Tithi Lord 的数据。
        # 兼容两种格式：{0: {...}, 1: {...}} 或 {'Sun': {...}, 'Moon': {...}}
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

        # Tithi Lord 与主要行星的相位关系（如果有 aspects 数据）
        # 这里只做简单标注
        result["tithi_lord_notes"] = (
            f"Tithi Lord {lord_name} 在{tithi_num}日（{paksha}月）。"
            f"Tithi Lord 位于第{lord_house}宫，"
            f"星性：{lord_dignity or '未知'}。"
        )

    return result


def calc_birth_tithi(sun_deg, moon_deg):
    """
    计算出生 Tithi（用于 Prashna/问卜 和 个人特质分析）。
    返回出生 Tithi 信息。
    """
    return calc_tithi_lord_full(sun_deg, moon_deg)


def tithi_lord_prashna_indicator(tithi_num, paksha, question_type="general"):
    """
    Tithi Lord 作为 Prashna（问卜）的时机指标。
    不同 Tithi 适合不同类型的问题。
    """
    # Tithi 1-5: 新开始，适合启动项目
    # Tithi 6-10: 稳定期，适合巩固
    # Tithi 11-15: 完成期，适合结束/收获

    guidance = {
        "new_beginning": tithi_num <= 5,
        "consolidation": 6 <= tithi_num <= 10,
        "completion": 11 <= tithi_num <= 15,
    }

    paksha_guidance = {
        "Shukla": "盈月期：能量上升，适合启动、扩张、公开行动。",
        "Krishna": "亏月期：能量下降，适合内省、结束、隐藏行动。"
    }

    return {
        "tithi_num": tithi_num,
        "paksha": paksha,
        "guidance": guidance,
        "paksha_note": paksha_guidance.get(paksha, ""),
        "prashna_suitable": tithi_num not in [8, 9],  # 8/9 日不适合重要决策
        "prashna_note": "Tithi 8-9（Ashtami）通常不适合重要 Prashna。"
        if tithi_num in [8, 9] else "当前 Tithi 适合进行 Prashna 分析。"
    }


if __name__ == "__main__":
    # 测试：假设太阳 30°，月亮 90°
    sun = 30.0
    moon = 90.0
    result = calc_tithi_lord_full(sun, moon)
    print("Tithi Lord 测试结果：")
    for k, v in result.items():
        print(f"  {k}: {v}")
