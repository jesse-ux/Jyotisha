"""
pancha_pakshi.py - Pancha Pakshi（五鸟）系统计算模块
v6.0.15 新增技法

Pancha Pakshi 是泰米尔占星系统，将 27 Nakshatra 分配给 5 只"鸟"
（代表生命力的 5 种状态：统治、进食、行走、睡眠、死亡）。
每个人根据出生 Nakshatra 和当前时日，处于某种 Pakshi 状态。
"""

# 五鸟名称与状态
PAKSHI_NAMES = {
    0: "Vulture / Rule (统治)",
    1: "Crow / Eat (进食)",
    2: "Crane / Walk (行走)",
    3: "Owl / Sleep (睡眠)",
    4: "Bat / Die (死亡)",
}

# 27 Nakshatra 对应的 Pakshi 分配（按泰米尔传统）
# 来源：泰米尔占星文献
# 分配方式：每个 Pakshi 掌管 5-6 个 Nakshatra
NAKSHATRA_PAKSHI = {
    # Vulture / Rule (0)
    1: 0, 2: 0, 3: 0, 4: 0, 5: 0,
    # Crow / Eat (1)
    6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    # Crane / Walk (2)
    11: 2, 12: 2, 13: 2, 14: 2, 15: 2,
    # Owl / Sleep (3)
    16: 3, 17: 3, 18: 3, 19: 3, 20: 3,
    # Bat / Die (4)
    21: 4, 22: 4, 23: 4, 24: 4, 25: 4, 26: 4, 27: 4,
}

# Nakshatra 名称列表
NAKSHATRA_NAMES = [
    "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# 五状态顺序（统治 → 进食 → 行走 → 睡眠 → 死亡 → 统治...）
PAKSHI_CYCLE = [0, 1, 2, 3, 4]  # Rule, Eat, Walk, Sleep, Die

# 星期对应的 Pakshi 起始偏移（0=周日，1=周一...6=周六）
# 每个星期开始时的 Pakshi 偏移量
WEEKDAY_PAKSHI_OFFSET = {
    0: 0,  # 周日：从 Rule 开始
    1: 2,  # 周一：从 Walk 开始
    2: 4,  # 周二：从 Die 开始
    3: 1,  # 周三：从 Eat 开始
    4: 3,  # 周四：从 Sleep 开始
    5: 0,  # 周五：从 Rule 开始
    6: 2,  # 周六：从 Walk 开始
}


def get_birth_pakshi(nakshatra_num):
    """
    根据出生 Nakshatra 获取所属 Pakshi。
    """
    if nakshatra_num < 1 or nakshatra_num > 27:
        return None, f"Nakshatra 编号 {nakshatra_num} 超出范围（1-27）"

    pakshi_idx = NAKSHATRA_PAKSHI.get(nakshatra_num)
    if pakshi_idx is None:
        return None, f"Nakshatra {nakshatra_num} 未找到 Pakshi 映射"

    return pakshi_idx, PAKSHI_NAMES[pakshi_idx]


def calc_pakshi_day_state(birth_nakshatra, weekday, period_of_day=0):
    """
    计算指定日期的 Pakshi 状态。
    birth_nakshatra: 出生 Nakshatra 编号（1-27）
    weekday: 星期（0=周日，1=周一...6=周六）
    period_of_day: 一天中的时段（0-4，对应五个 Pakshi 时段）
    """
    birth_pakshi, _ = get_birth_pakshi(birth_nakshatra)
    if birth_pakshi is None:
        return None, f"出生 Nakshatra {birth_nakshatra} 无效"

    # 星期起始偏移
    offset = WEEKDAY_PAKSHI_OFFSET.get(weekday, 0)

    # 当日当前时段的 Pakshi = (出生 Pakshi + 星期偏移 + 时段) % 5
    current_pakshi = (birth_pakshi + offset + period_of_day) % 5

    return current_pakshi, PAKSHI_NAMES[current_pakshi]


def calc_pakshi_full_analysis(birth_nakshatra, birth_weekday=None, target_weekday=None, target_period=0):
    """
    完整 Pancha Pakshi 分析。
    birth_nakshatra: 出生 Nakshatra（1-27）
    birth_weekday: 出生星期（可选，用于更精确分析）
    target_weekday: 目标日期星期（用于预测，0-6）
    target_period: 目标时段（0-4）
    """
    birth_pakshi_idx, birth_pakshi_name = get_birth_pakshi(birth_nakshatra)
    if birth_pakshi_idx is None:
        return {"error": birth_pakshi_name}

    result = {
        "birth_nakshatra": birth_nakshatra,
        "birth_nakshatra_name": NAKSHATRA_NAMES[birth_nakshatra - 1] if 1 <= birth_nakshatra <= 27 else "Unknown",
        "birth_pakshi_idx": birth_pakshi_idx,
        "birth_pakshi_name": birth_pakshi_name,
    }

    # 出生时的 Pakshi 状态解释
    pakshi_interpretations = {
        0: "统治鸟（Vulture）：出生时有领导力，能掌控局面，适合开始重要项目。",
        1: "进食鸟（Crow）：出生时需要滋养，关注物质获取，适合积累资源。",
        2: "行走鸟（Crane）：出生时处于行动状态，适合旅行、移动、沟通。",
        3: "睡眠鸟（Owl）：出生时休息状态，适合内省、规划、潜伏等待。",
        4: "死亡鸟（Bat）：出生时转化状态，适合结束、释放、深度改变。",
    }
    result["birth_pakshi_interpretation"] = pakshi_interpretations.get(birth_pakshi_idx, "")

    # 如果提供了目标日期，计算那时的 Pakshi 状态
    if target_weekday is not None:
        target_pakshi_idx, target_pakshi_name = calc_pakshi_day_state(
            birth_nakshatra, target_weekday, target_period
        )
        result["target_weekday"] = target_weekday
        result["target_period"] = target_period
        result["target_pakshi_idx"] = target_pakshi_idx
        result["target_pakshi_name"] = target_pakshi_name

        # 目标状态的解读
        target_interpretations = {
            0: "统治时段：适合开始新项目、领导、决策、公开行动。能量最强。",
            1: "进食时段：适合积累、学习、获取资源、建立联系。能量恢复中。",
            2: "行走时段：适合旅行、移动、沟通、短途出行。能量流动。",
            3: "睡眠时段：适合休息、规划、内省、等待。能量最低，不宜重要决策。",
            4: "死亡时段：适合结束、释放、深度转化、灵性实践。能量转化中。",
        }
        result["target_pakshi_interpretation"] = target_interpretations.get(target_pakshi_idx, "")

    # Pakshi 周期完整列表（一天五个时段）
    day_periods = []
    for period in range(5):
        p_idx, p_name = calc_pakshi_day_state(birth_nakshatra, target_weekday or 0, period)
        day_periods.append({
            "period": period,
            "pakshi_idx": p_idx,
            "pakshi_name": p_name,
        })
    result["day_periods"] = day_periods

    return result


def pancha_pakshi_prashna_guide(birth_nakshatra, question_type="general"):
    """
    Pancha Pakshi 用于 Prashna（问卜）的指导。
    根据出生 Pakshi 和当前时段判断问题是否适合提问。
    """
    birth_pakshi_idx, _ = get_birth_pakshi(birth_nakshatra)

    # 不同时段适合的问题类型
    suitable_for = {
        0: ["new_beginning", "leadership", "decision"],  # 统治：新开始、领导、决策
        1: ["resource", "learning", "relationship"],  # 进食：资源、学习、关系
        2: ["travel", "communication", "short_term"],  # 行走：旅行、沟通、短期
        3: ["rest", "planning", "inner_work"],  # 睡眠：休息、规划、内在工作
        4: ["ending", "transformation", "spiritual"],  # 死亡：结束、转化、灵性
    }

    guidance = {
        "current_pakshi": birth_pakshi_idx,
        "current_pakshi_name": PAKSHI_NAMES[birth_pakshi_idx],
        "suitable_question_types": suitable_for.get(birth_pakshi_idx, []),
        "prashna_advice": (
            "当前为统治时段，问题关于新开始或领导最适合。"
            if birth_pakshi_idx == 0 else
            "当前为进食时段，问题关于资源或学习最适合。"
            if birth_pakshi_idx == 1 else
            "当前为行走时段，问题关于旅行或沟通最适合。"
            if birth_pakshi_idx == 2 else
            "当前为睡眠时段，问题关于休息或规划最适合，不宜重要决策。"
            if birth_pakshi_idx == 3 else
            "当前为死亡时段，问题关于结束或转化最适合。"
        ),
    }

    return guidance


if __name__ == "__main__":
    # 测试：出生 Nakshatra 10（Magha），目标周三（weekday=3），时段 0
    result = calc_pakshi_full_analysis(10, target_weekday=3, target_period=0)
    print("Pancha Pakshi 测试结果：")
    for k, v in result.items():
        if k != "day_periods":
            print(f"  {k}: {v}")
    print("  时段列表：")
    for p in result.get("day_periods", []):
        print(f"    {p}")
