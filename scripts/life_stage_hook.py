#!/usr/bin/env python3
"""
Dynamic Life-Stage Hook Engine
Generates context-aware prompt suggestions based on the user's current Dasha and Transits.
"""

from typing import Any, Dict, List

# Core mapping for planets/houses to life themes
PLANET_THEMES = {
    "Sun": ["career", "status", "authority", "father"],
    "Moon": ["mind", "mother", "property", "emotional well-being"],
    "Mars": ["property", "energy", "courage", "siblings", "conflicts"],
    "Mercury": ["business", "communication", "intellect", "skills"],
    "Jupiter": ["wealth", "children", "expansion", "luck", "wisdom"],
    "Venus": ["marriage", "relationships", "luxury", "comfort"],
    "Saturn": ["career", "delays", "discipline", "hard work", "karma"],
    "Rahu": ["foreign affairs", "sudden events", "technology", "obsession"],
    "Ketu": ["spirituality", "losses", "detachment", "isolation"]
}

HOUSE_THEMES = {
    1: ["health", "self-development", "life path"],
    2: ["wealth", "savings", "family"],
    3: ["courage", "short trips", "communication"],
    4: ["property", "mother", "home", "peace"],
    5: ["investments", "children", "creativity"],
    6: ["health issues", "debts", "enemies", "daily work"],
    7: ["marriage", "business partnerships", "public relations"],
    8: ["hidden matters", "sudden gains/losses", "research", "crises"],
    9: ["fortune", "higher education", "long travel", "spirituality"],
    10: ["career advancement", "public status", "leadership"],
    11: ["gains", "networks", "profits", "elder siblings"],
    12: ["foreign lands", "expenses", "isolation", "spirituality"]
}

def _get_lord_houses(planet: str, asc_idx: int) -> List[int]:
    """Return the houses owned by the given planet for the given ascendant index."""
    SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    SIGN_LORDS = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
        "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
        "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    owned = []
    for h in range(1, 13):
        sign = SIGNS[(asc_idx + h - 1) % 12]
        if SIGN_LORDS.get(sign) == planet:
            owned.append(h)
    return owned

def generate_life_stage_hooks(
    planets: Dict[str, Any],
    asc_sign: str,
    asc_idx: int,
    current_dasha: Dict[str, Any],
    narayana_dasha: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Generate top 3 prompt hooks based on the current life stage.
    """
    hooks = []

    # 1. Antardasha (Sub-period) Hook
    ad_lord = None
    if isinstance(current_dasha, dict) and "antardasha" in current_dasha:
        ad = current_dasha.get("antardasha")
        if isinstance(ad, dict):
            ad_lord = ad.get("lord")
    elif isinstance(current_dasha, dict):
        ad_lord = current_dasha.get("lord")  # Fallback to MD lord

    if ad_lord:
        owned_houses = _get_lord_houses(ad_lord, asc_idx)
        core_themes = []
        for h in owned_houses:
            core_themes.extend(HOUSE_THEMES.get(h, []))

        if not core_themes:
            core_themes = PLANET_THEMES.get(ad_lord, [])

        if "career advancement" in core_themes or "wealth" in core_themes or ad_lord in ["Sun", "Jupiter"]:
            hooks.append({
                "type": "career_wealth",
                "trigger": f"Current Antardasha Lord ({ad_lord})",
                "question": f"🔮 测一测我在当前「{ad_lord}运」期间，是否有实质性的财务跃迁或事业升职机会？",
                "rationale": f"系统检测到你正处于 {ad_lord} 主导的运势周期，该星体掌管你的核心资源/事业宫位，近期极易触发财务或职级变动。"
            })
        elif "marriage" in core_themes or "business partnerships" in core_themes or ad_lord in ["Venus", "Moon"]:
            hooks.append({
                "type": "relationship",
                "trigger": f"Current Antardasha Lord ({ad_lord})",
                "question": f"🔮 我的正缘大概会在什么时间点出现？当前运势对我的婚恋/合伙关系有什么影响？",
                "rationale": f"系统检测到你正处于 {ad_lord} 运势周期，极易触发亲密关系或重要合伙人的变动，建议深度扫描婚恋应期。"
            })
        elif "foreign lands" in core_themes or "hidden matters" in core_themes or "health issues" in core_themes or ad_lord in ["Ketu", "Rahu"]:
            hooks.append({
                "type": "transition_healing",
                "trigger": f"Current Antardasha Lord ({ad_lord})",
                "question": f"🔮 我近期感到强烈的内耗/变动倾向，是否适合出国、换环境或进行重大人生断舍离？",
                "rationale": f"当前 {ad_lord} 运势激活了隐秘/变动宫位，容易带来精神内耗或海外发展的契机，需要诊断当前的卡点。"
            })
        else:
            # Fallback hook for Antardasha
            hooks.append({
                "type": "general_ad",
                "trigger": f"Current Antardasha Lord ({ad_lord})",
                "question": f"🔮 当前「{ad_lord}运」对我接下来的 1-2 年有什么本质性的影响？",
                "rationale": f"你目前处于 {ad_lord} 掌管的次级运势中，深度解读该星体能帮你把握近期的核心节奏。"
            })

    # 2. Narayana Dasha Hook
    if isinstance(narayana_dasha, dict):
        nd_obj = narayana_dasha.get("current_dasha")
        nd_sign = None
        if isinstance(nd_obj, dict):
            nd_sign = nd_obj.get("md", {}).get("sign")
        elif isinstance(nd_obj, str):
            nd_sign = nd_obj

        if nd_sign:
            hooks.append({
                "type": "macro_trend",
                "trigger": f"Narayana Dasha ({nd_sign})",
                "question": f"🔮 我在当前的「{nd_sign}星座大运」中，最应该把精力聚焦在哪个领域才能利益最大化？",
                "rationale": f"Jaimini 系统的 {nd_sign} 大运主轴已确认。顺应星座大运的能量流动，能帮你找到未来几年的阻力最小路径。"
            })

    # 3. Upcoming Transit (Gochar) Mock Hook (Requires actual ephemeris in full implementation)
    # For now, we inject a generic but highly actionable transit hook.
    hooks.append({
        "type": "transit_alert",
        "trigger": "Upcoming Major Transit",
        "question": "🔮 未来半年内，木星或土星的换座/过宫，会给我带来哪些具体的机遇或危机？",
        "rationale": "流年大星（木/土）的轨迹往往是触发本命盘事件的最后一把钥匙，提前观测能帮你避坑或抓红利。"
    })

    # Ensure we return exactly 3 top hooks
    # Remove duplicates by type
    seen_types = set()
    unique_hooks = []
    for h in hooks:
        if h["type"] not in seen_types:
            unique_hooks.append(h)
            seen_types.add(h["type"])

    # Always provide a fallback general reading option
    unique_hooks.append({
        "type": "general_reading",
        "trigger": "User Preference",
        "question": "🔮 跳过引导，我想查看完整的十年人生起伏与本命深度体检图谱。",
        "rationale": "生成最全面的静态命运基调与大运概览。"
    })

    return unique_hooks[:3]
