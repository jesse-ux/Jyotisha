"""
rashi_tulya_navamsa.py - Rashi Tulya Navamsa（本命对分盘九分仪）分析模块
v6.0.15 新增技法

Rashi Tulya Navamsa：将 D9（Navamsa）分盘的每一宫与 D1（Rashi）的同一宫对比，
揭示该生活领域的"内在真相"和"潜在动力"。
核心思路：D1 是外在表现，D9 是内在潜力/真实状态。
"""

# 宫位名称（1-12）
HOUSE_NAMES = [
    "第1宫（自我/身体）", "第2宫（财富/家庭）", "第3宫（兄弟/勇气）",
    "第4宫（母亲/情绪）", "第5宫（子女/智慧）", "第6宫（疾病/敌人）",
    "第7宫（配偶/合伙）", "第8宫（隐藏/转变）", "第9宫（命运/父亲）",
    "第10宫（事业/名声）", "第11宫（收益/朋友）", "第12宫（损失/解脱）"
]

# 行星名称
PLANET_NAMES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# 宫位领域关键词
HOUSE_KEYWORDS = [
    "自我身份、外貌、性格、生命力",
    "财富积累、语言能力、早期教育、家庭经济",
    "兄弟姐妹、沟通勇气、短途旅行、动手能力",
    "母亲、家庭、内心安全感、不动产、车辆",
    "子女、创造性智慧、投资项目、恋爱前期",
    "日常工作、健康问题、竞争对手、债务",
    "婚姻关系、商业合伙、公开的敌人、异地",
    "深层转变、神秘学、性传播、意外收入",
    "人生大方向、高等教育、哲学信仰、父亲",
    "社会身份、事业成就、公众形象、权威",
    "长期收益、朋友圈、团体归属、愿景实现",
    "潜意识、海外事务、精神解脱、隐秘支出"
]


def analyze_rashi_tulya_navamsa(d1_planets, d1_houses, d9_planets, d9_houses):
    """
    Rashi Tulya Navamsa 核心分析。
    输入：
      d1_planets: D1 行星数据 {planet_idx: {sign, house, dignity,...}}
      d1_houses: D1 宫位数据 {house_num: {sign, lord, planets}}
      d9_planets: D9 行星数据 {planet_idx: {sign, house, dignity,...}}
      d9_houses: D9 宫位数据 {house_num: {sign, lord, planets}}
    输出：
      每宫的 D1→D9 对比分析
    """
    results = []

    for house_num in range(1, 13):  # 1-12 宫
        d1_house_data = d1_houses.get(house_num, {})
        d9_house_data = d9_houses.get(house_num, {})

        # D1 该宫的信息
        d1_sign = d1_house_data.get("sign", "Unknown")
        d1_lord = d1_house_data.get("lord", "Unknown")
        d1_planets_in = d1_house_data.get("planets", [])
        d1_house_strength = d1_house_data.get("strength", "Unknown")

        # D9 该宫的信息
        d9_sign = d9_house_data.get("sign", "Unknown")
        d9_lord = d9_house_data.get("lord", "Unknown")
        d9_planets_in = d9_house_data.get("planets", [])
        d9_house_strength = d9_house_data.get("strength", "Unknown")

        # 核心对比分析
        comparison = _compare_d1_d9_house(
            house_num, d1_sign, d1_lord, d1_planets_in, d1_house_strength,
            d9_sign, d9_lord, d9_planets_in, d9_house_strength
        )

        results.append({
            "house_num": house_num,
            "house_name": HOUSE_NAMES[house_num - 1],
            "house_keywords": HOUSE_KEYWORDS[house_num - 1],
            "d1_sign": d1_sign,
            "d1_lord": d1_lord,
            "d1_planets_in": d1_planets_in,
            "d1_strength": d1_house_strength,
            "d9_sign": d9_sign,
            "d9_lord": d9_lord,
            "d9_planets_in": d9_planets_in,
            "d9_strength": d9_house_strength,
            "comparison": comparison,
        })

    return results


def _compare_d1_d9_house(house_num, d1_sign, d1_lord, d1_pl, d1_str, d9_sign, d9_lord, d9_pl, d9_str):
    """
    对比 D1 和 D9 同一宫位的详细分析。
    """
    analysis = []

    # 1. 宫主星对比
    if d1_lord == d9_lord:
        analysis.append(f"宫主星一致（{d1_lord}），该领域内外表现统一，潜力与表现匹配。")
    else:
        analysis.append(f"宫主星不同：D1={d1_lord}，D9={d9_lord}。外在表现（{d1_lord}）"
                       f"与内在潜力（{d9_lord}）有差异，需要调和。")

    # 2. 行星入驻对比
    d1_pl_names = [PLANET_NAMES[p] if isinstance(p, int) else p for p in d1_pl]
    d9_pl_names = [PLANET_NAMES[p] if isinstance(p, int) else p for p in d9_pl]

    if d1_pl_names:
        analysis.append(f"D1 入驻行星：{', '.join(map(str, d1_pl_names))}（外在影响）")
    else:
        analysis.append("D1 无行星入驻（该领域外在平静）")

    if d9_pl_names:
        analysis.append(f"D9 入驻行星：{', '.join(map(str, d9_pl_names))}（内在动力）")
    else:
        analysis.append("D9 无行星入驻（该领域内在潜力未被激活）")

    # 3. 力量对比
    analysis.append(f"D1 宫力量：{d1_str} | D9 宫力量：{d9_str}")
    if d1_str == "Strong" and d9_str == "Strong":
        analysis.append("→ D1、D9 均强：该领域内外兼强，潜力完全发挥。")
    elif d1_str == "Weak" and d9_str == "Weak":
        analysis.append("→ D1、D9 均弱：该领域内外兼弱，需要努力克服。")
    elif d1_str == "Strong" and d9_str == "Weak":
        analysis.append("→ D1 强 D9 弱：外在表现好，但内在支持不足，可能表面风光。")
    elif d1_str == "Weak" and d9_str == "Strong":
        analysis.append("→ D1 弱 D9 强：外在表现弱，但内在潜力强，大器晚成之象。")

    # 4. 关键解读（按宫位）
    key_interp = _get_house_key_interpretation(house_num, d1_pl, d9_pl, d1_lord, d9_lord)
    if key_interp:
        analysis.append(f"关键解读：{key_interp}")

    return analysis


def _get_house_key_interpretation(house_num, d1_pl, d9_pl, d1_lord, d9_lord):
    """
    按宫位给出关键解读。
    """
    interpretations = {
        1: "第1宫：自我认知。D9 强则内在自信，D1 强则外在魅力。",
        2: "第2宫：财富积累。D9 有金星/木星则财富潜力大，D1 有恶星则财务波折。",
        3: "第3宫：勇气行动。D9 有火星则内在勇敢，D1 有水星则沟通力强。",
        4: "第4宫：内心安全。D9 有月亮/金星则内心满足，D1 有土星则情感压抑。",
        5: "第5宫：创造智慧。D9 有木星则智慧天赋高，D1 有火星则创造冲动强。",
        6: "第6宫：竞争健康。D9 有土星/火星则抗压能力强，D1 有木星则能化解敌意。",
        7: "第7宫：婚姻关系。D9 是婚姻内在，D1 是婚姻表现。D9 强则婚姻内在和谐。",
        8: "第8宫：深层转变。D9 有木星/金星则危机中有贵人，D1 有恶星则有突发事件。",
        9: "第9宫：命运方向。D9 有木星/太阳则命运护佑强，D1 有恶星则需要努力。",
        10: "第10宫：事业成就。D9 是事业潜力，D1 是事业表现。D9 强则事业基础稳。",
        11: "第11宫：收益朋友。D9 有木星/金星则收益潜力大，D1 有土星则收益延迟。",
        12: "第12宫：解脱潜意识。D9 有木星/金星则精神解脱能力强，D1 有恶星则有隐秘损失。",
    }
    return interpretations.get(house_num, "")


def rashi_tulya_navamsa_summary(rashi_tulya_results):
    """
    生成 Rashi Tulya Navamsa 的总结报告。
    """
    summary = {
        "total_houses_analyzed": len(rashi_tulya_results),
        "houses_d1_d9_both_strong": [],
        "houses_d1_weak_d9_strong": [],
        "houses_d1_strong_d9_weak": [],
        "houses_d1_d9_both_weak": [],
        "key_insights": [],
    }

    for house_data in rashi_tulya_results:
        h = house_data["house_num"]
        d1_s = house_data["d1_strength"]
        d9_s = house_data["d9_strength"]

        if d1_s == "Strong" and d9_s == "Strong":
            summary["houses_d1_d9_both_strong"].append(h)
        elif d1_s == "Weak" and d9_s == "Strong":
            summary["houses_d1_weak_d9_strong"].append(h)
        elif d1_s == "Strong" and d9_s == "Weak":
            summary["houses_d1_strong_d9_weak"].append(h)
        elif d1_s == "Weak" and d9_s == "Weak":
            summary["houses_d1_d9_both_weak"].append(h)

    # 关键洞察
    if summary["houses_d1_weak_d9_strong"]:
        summary["key_insights"].append(
            f"大器晚成宫位：{summary['houses_d1_weak_d9_strong']}"
            f"（这些领域内在潜力强，但需要时间/努力才能显现）"
        )
    if summary["houses_d1_strong_d9_weak"]:
        summary["key_insights"].append(
            f"表面风光宫位：{summary['houses_d1_strong_d9_weak']}"
            f"（这些领域外在表现好，但内在支持不足，需要警惕）"
        )
    if summary["houses_d1_d9_both_strong"]:
        summary["key_insights"].append(
            f"内外兼强宫位：{summary['houses_d1_d9_both_strong']}"
            f"（这些领域实力雄厚，可以重点发展）"
        )
    if summary["houses_d1_d9_both_weak"]:
        summary["key_insights"].append(
            f"需要努力宫位：{summary['houses_d1_d9_both_weak']}"
            f"（这些领域内外都弱，需要特别努力或寻求帮助）"
        )

    return summary


def rashi_tulya_navamsa_marriage_focus(rashi_tulya_results):
    """
    专门针对婚姻（第7宫）的 Rashi Tulya Navamsa 分析。
    """
    # 找到第7宫的数据
    house_7_data = None
    for h_data in rashi_tulya_results:
        if h_data["house_num"] == 7:
            house_7_data = h_data
            break

    if not house_7_data:
        return {"error": "未找到第7宫数据"}

    d1_7 = house_7_data["d1_sign"]
    d9_7 = house_7_data["d9_sign"]
    d1_pl_7 = house_7_data["d1_planets_in"]
    d9_pl_7 = house_7_data["d9_planets_in"]
    d1_str_7 = house_7_data["d1_strength"]
    d9_str_7 = house_7_data["d9_strength"]

    marriage_analysis = {
        "house_7_d1_sign": d1_7,
        "house_7_d9_sign": d9_7,
        "house_7_d1_planets": d1_pl_7,
        "house_7_d9_planets": d9_pl_7,
        "house_7_d1_strength": d1_str_7,
        "house_7_d9_strength": d9_str_7,
        "marriage_outer_expression": f"外在婚姻表现受 {d1_7} 影响",
        "marriage_inner_potential": f"内在婚姻潜力在 {d9_7}",
        "assessment": "",
    }

    # 评估
    if d1_str_7 == "Strong" and d9_str_7 == "Strong":
        marriage_analysis["assessment"] = "婚姻内外兼强，配偶优秀，关系和谐。"
    elif d1_str_7 == "Weak" and d9_str_7 == "Strong":
        marriage_analysis["assessment"] = "婚姻内在潜力强（D9强），但外在表现弱（D1弱），可能晚婚或婚姻经历波折后好转。"
    elif d1_str_7 == "Strong" and d9_str_7 == "Weak":
        marriage_analysis["assessment"] = "婚姻外在表现好（D1强），但内在不稳定（D9弱），需要注意关系维护。"
    else:
        marriage_analysis["assessment"] = "婚姻内外都弱，需要努力经营，也可能配偶条件一般。"

    return marriage_analysis


if __name__ == "__main__":
    # 简单测试（需要实际数据）
    print("Rashi Tulya Navamsa 模块已加载")
    print("需要 D1 和 D9 的行星/宫位数据作为输入")
