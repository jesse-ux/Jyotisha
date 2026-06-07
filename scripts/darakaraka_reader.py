#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
darakaraka_reader.py — Darakaraka深度解读引擎
===============================================
Jaimini系统核心：配偶征象星的多维度深度分析

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# DK行星特质库
PLANET_SPOUSE_TRAITS = {
    "Sun": {
        "core": "领导者型伴侣",
        "traits": ["天生权威感", "决断力强", "稳定可靠", "有远见", "自尊心强"],
        "attracted_to": ["有领导力的人", "有社会地位的人", "自信独立的人"],
        "challenges": ["可能过于自我中心", "需要被尊重", "控制欲强"],
        "positive": ["忠诚", "保护欲强", "有责任感", "能提供安全感"],
        "career_signs": ["政府", "管理", "领导岗位", "创业"],
    },
    "Moon": {
        "core": " nurturing型伴侣",
        "traits": ["情感丰富", "关怀体贴", "直觉敏锐", "温和敏感", "依恋家庭"],
        "attracted_to": ["温暖体贴的人", "能提供情感安全感的人", "重视家庭的人"],
        "challenges": ["情绪波动大", "过于依赖", "安全感需求高"],
        "positive": ["无条件的爱", "滋养力强", "善解人意", "母性/父性本能"],
        "career_signs": ["护理", "教育", "心理咨询", "艺术创作"],
    },
    "Mars": {
        "core": "行动派伴侣",
        "traits": ["充满活力", "勇敢果断", "竞争性强", "直率坦诚", "行动迅速"],
        "attracted_to": ["有活力的人", "敢于挑战的人", "独立自强的人"],
        "challenges": ["脾气暴躁", "冲动", "好胜心过强", "缺乏耐心"],
        "positive": ["保护欲极强", "勇敢无畏", "积极主动", "充满激情"],
        "career_signs": ["军事", "体育", "工程", "外科医生", "冒险行业"],
    },
    "Mercury": {
        "core": "智慧型伴侣",
        "traits": ["聪明机智", "沟通能力强", "好奇心重", "适应力强", "理性分析"],
        "attracted_to": ["聪明有趣的人", "善于交流的人", "有学识的人"],
        "challenges": ["可能过于理性", "善变", "分析过度", "不够深情"],
        "positive": ["善解人意", "幽默风趣", "知识渊博", "善于解决问题"],
        "career_signs": ["写作", "教学", "商业", "传媒", "IT"],
    },
    "Jupiter": {
        "core": "导师型伴侣",
        "traits": ["智慧博爱", "道德感强", "慷慨大方", "乐观积极", "精神追求"],
        "attracted_to": ["有智慧的人", "道德高尚的人", "有精神追求的人"],
        "challenges": ["可能过于理想化", "说教倾向", "过度乐观"],
        "positive": ["智慧引导", "慷慨支持", "精神伴侣", "道德榜样"],
        "career_signs": ["教育", "法律", "宗教", "咨询", "金融"],
    },
    "Venus": {
        "core": "浪漫型伴侣",
        "traits": ["优雅迷人", "重视美感", "浪漫多情", "社交能力强", "追求和谐"],
        "attracted_to": ["有品位的人", "浪漫体贴的人", "外表吸引的人"],
        "challenges": ["可能过于注重外表", "物质倾向", "优柔寡断"],
        "positive": ["浪漫体贴", "审美力强", "善于营造氛围", "关系和谐"],
        "career_signs": ["艺术", "设计", "时尚", "美容", "外交"],
    },
    "Saturn": {
        "core": "成熟型伴侣",
        "traits": ["成熟稳重", "责任心强", "务实踏实", "纪律性强", "晚成"],
        "attracted_to": ["成熟稳重的人", "有责任感的人", "事业稳定的人"],
        "challenges": ["可能过于严肃", "情感表达困难", "冷淡疏离", "延迟"],
        "positive": ["极度忠诚", "可靠稳重", "长期承诺", "共同成长"],
        "career_signs": ["管理", "工程", "建筑", "政府", "传统行业"],
    },
    "Rahu": {
        "core": "异域/非传统型伴侣",
        "traits": ["独特非凡", "打破常规", "野心勃勃", "异域风情", "颠覆性"],
        "attracted_to": ["与众不同的人", "有野心的人", "异域文化背景的人"],
        "challenges": ["可能不稳定", "非传统关系", "社会不认可", "欺骗风险"],
        "positive": ["带来全新体验", "突破局限", "独特魅力", "激发潜能"],
        "career_signs": ["科技", "新媒体", "跨国业务", "非主流行业"],
    },
}

# DK星座细化
SIGN_REFINEMENTS = {
    "Aries": {"intensifies": ["行动力", "独立性"], "softens": [], "adds": ["冲动", "直接"]},
    "Taurus": {"intensifies": ["稳定性", "感官享受"], "softens": ["急躁"], "adds": ["固执", "物质安全感"]},
    "Gemini": {"intensifies": ["沟通", "多变"], "softens": ["沉闷"], "adds": ["好奇心", "不专一风险"]},
    "Cancer": {"intensifies": ["情感", "保护欲"], "softens": ["冷漠"], "adds": ["情绪化", "依恋"]},
    "Leo": {"intensifies": ["自信", "表现力"], "softens": [], "adds": ["需要关注", "骄傲"]},
    "Virgo": {"intensifies": ["细致", "服务意识"], "softens": ["粗心"], "adds": ["挑剔", "焦虑"]},
    "Libra": {"intensifies": ["和谐", "美感"], "softens": ["粗鲁"], "adds": ["优柔寡断", "依赖关系"]},
    "Scorpio": {"intensifies": ["深度", "激情", "转化力"], "softens": [], "adds": ["控制欲", "嫉妒", "秘密"]},
    "Sagittarius": {"intensifies": ["自由", "哲学"], "softens": ["狭隘"], "adds": ["不安定", "过度乐观"]},
    "Capricorn": {"intensifies": ["野心", "责任感"], "softens": ["轻浮"], "adds": ["工作狂", "情感压抑"]},
    "Aquarius": {"intensifies": ["独立", "创新"], "softens": ["传统束缚"], "adds": ["疏离", "反传统"]},
    "Pisces": {"intensifies": ["同情", "灵性"], "softens": ["硬化"], "adds": ["模糊", "逃避", "牺牲"]},
}

# DK宫位解读
HOUSE_INTERPRETATIONS = {
    1: "伴侣对命主影响深远，婚姻关系是自我身份的核心部分。伴侣可能性格鲜明、有领导力。",
    2: "伴侣与家庭财富密切相关，可能带来财务支持或共同理财。伴侣重视家庭价值观。",
    3: "伴侣与沟通、 siblings 有关。可能通过兄弟姐妹介绍认识，或伴侣重视交流。",
    4: "伴侣与内心安全感、房产、家庭根基有关。伴侣提供情感庇护所。",
    5: "伴侣与子女、创造力、浪漫有关。可能通过子女结识，或关系充满浪漫。",
    6: "伴侣可能带来服务性质的关系，或伴侣从事服务/医疗行业。关系中需要克服困难。",
    7: "伴侣特质直接显现，婚姻关系是核心人生主题。伴侣公开、直接。",
    8: "深层转化型关系，伴侣可能带来重大人生变革。涉及共同资源、遗产、秘密。",
    9: "伴侣与远方、高等教育、灵性有关。可能异地或文化背景不同。伴侣有智慧。",
    10: "伴侣与社会地位、事业有关。伴侣可能有成就，或帮助命主事业发展。",
    11: "伴侣与社交网络、愿望实现有关。通过朋友介绍认识，或共同追求理想。",
    12: "隐秘或牺牲型关系，伴侣可能来自幕后或需要隐秘。灵性层面的连接。",
}

# 友好/敌对行星（影响DK）
FRIENDLY_PLANETS = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus": ["Mercury", "Saturn"],
    "Saturn": ["Mercury", "Venus"],
    "Rahu": ["Venus", "Saturn"],
}

ENEMY_PLANETS = {
    "Sun": ["Saturn", "Venus"],
    "Moon": [],
    "Mars": ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus": ["Sun", "Moon"],
    "Saturn": ["Sun", "Moon", "Mars"],
    "Rahu": ["Sun", "Moon", "Mars"],
}


@dataclass
class DKAnalysis:
    """DK分析结果"""
    # 基础信息
    dk_planet: str
    dk_sign: str
    dk_house: int
    dk_degree: float
    nakshatra: Optional[str] = None
    nakshatra_pada: Optional[int] = None
    
    # 状态
    is_retrograde: bool = False
    is_combust: bool = False
    dignity: str = ""  # exalted/own/friendly/neutral/enemy/debilitated
    
    # D9信息
    d9_sign: Optional[str] = None
    d9_house: Optional[int] = None
    d9_dignity: Optional[str] = None
    
    # 解读
    core_profile: str = ""           # 核心配偶原型
    personality_traits: List[str] = field(default_factory=list)
    attracted_to: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    positive_traits: List[str] = field(default_factory=list)
    career_signs: List[str] = field(default_factory=list)
    
    # 宫位解读
    house_meaning: str = ""
    house_themes: List[str] = field(default_factory=list)
    
    # 相位影响
    conjunctions: List[Dict] = field(default_factory=list)      # 合相
    aspects_friendly: List[str] = field(default_factory=list)   # 友好相位
    aspects_hostile: List[str] = field(default_factory=list)    # 敌对相位
    
    # 综合评估
    marriage_quality_score: float = 0.5   # 0-1
    timing_clues: List[str] = field(default_factory=list)
    remedies: List[str] = field(default_factory=list)
    
    # 叙事
    narrative: str = ""


class DarakarakaReader:
    """Darakaraka深度解读引擎"""
    
    def __init__(self):
        self.planet_traits = PLANET_SPOUSE_TRAITS
        self.sign_refinements = SIGN_REFINEMENTS
        self.house_interps = HOUSE_INTERPRETATIONS
    
    def analyze(self, chart_data: Dict, use_8_karaka: bool = True) -> DKAnalysis:
        """
        分析Darakaraka
        
        Args:
            chart_data: 标准星盘数据
            use_8_karaka: 使用8星系统（含Rahu）
        
        Returns:
            DKAnalysis对象
        """
        # Step 1: 计算DK
        dk_planet, dk_info = self._calculate_dk(chart_data, use_8_karaka)
        
        # Step 2: 提取位置信息
        dk_sign = dk_info.get("sign", "")
        dk_house = dk_info.get("house", 0)
        dk_degree = dk_info.get("degree_in_sign", 0)
        
        # Step 3: 构建分析结果
        analysis = DKAnalysis(
            dk_planet=dk_planet,
            dk_sign=dk_sign,
            dk_house=dk_house,
            dk_degree=dk_degree,
        )
        
        # Step 4: 填充行星特质
        self._fill_planet_traits(analysis)
        
        # Step 5: 星座细化
        self._refine_by_sign(analysis)
        
        # Step 6: 宫位解读
        self._interpret_house(analysis)
        
        # Step 7: 相位分析
        self._analyze_aspects(analysis, chart_data)
        
        # Step 8: D9分析
        self._analyze_d9(analysis, chart_data)
        
        # Step 9: 状态检测（逆行/燃烧）
        self._check_status(analysis, dk_info)
        
        # Step 10: 综合评估
        self._comprehensive_assessment(analysis)
        
        # Step 11: 生成叙事
        analysis.narrative = self._generate_narrative(analysis)
        
        return analysis
    
    def _calculate_dk(self, chart_data: Dict, use_8_karaka: bool = True) -> Tuple[str, Dict]:
        """计算Darakaraka行星"""
        planets = chart_data.get("planets", {})
        
        # 提取各行星星座内度数
        planet_degs = {}
        for pname, pdata in planets.items():
            if isinstance(pdata, dict) and "degree" in pdata:
                deg_in_sign = pdata.get("degree_in_sign", pdata["degree"] % 30)
                
                # Rahu逆行校正（8星系统）
                if pname == "Rahu" and use_8_karaka:
                    deg_in_sign = 30.0 - deg_in_sign
                
                planet_degs[pname] = deg_in_sign
        
        # 排序（降序）
        sorted_planets = sorted(planet_degs.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_planets:
            return "Unknown", {}
        
        if use_8_karaka and len(sorted_planets) >= 8:
            # 8星系统：第7高（第8颗被排除）
            dk = sorted_planets[6][0]  # 索引6 = 第7高
        else:
            # 7星系统：最低的
            dk = sorted_planets[-1][0]
        
        return dk, planets.get(dk, {})
    
    def _fill_planet_traits(self, analysis: DKAnalysis):
        """填充行星基础特质"""
        traits = self.planet_traits.get(analysis.dk_planet, {})
        
        analysis.core_profile = traits.get("core", "")
        analysis.personality_traits = traits.get("traits", [])
        analysis.attracted_to = traits.get("attracted_to", [])
        analysis.challenges = traits.get("challenges", [])
        analysis.positive_traits = traits.get("positive", [])
        analysis.career_signs = traits.get("career_signs", [])
    
    def _refine_by_sign(self, analysis: DKAnalysis):
        """按星座细化"""
        refinement = self.sign_refinements.get(analysis.dk_sign, {})
        
        # 强化某些特质
        for trait in refinement.get("intensifies", []):
            if trait not in analysis.personality_traits:
                analysis.personality_traits.append(f"**{trait}**")
        
        # 软化某些特质
        for trait in refinement.get("softens", []):
            if trait in analysis.challenges:
                analysis.challenges.remove(trait)
        
        # 新增特质
        for trait in refinement.get("adds", []):
            if trait not in analysis.personality_traits:
                analysis.personality_traits.append(trait)
    
    def _interpret_house(self, analysis: DKAnalysis):
        """解读DK宫位"""
        analysis.house_meaning = self.house_interps.get(
            analysis.dk_house, 
            f"DK位于第{analysis.dk_house}宫"
        )
        
        # 宫位主题
        house_themes = {
            1: ["自我认同", "伴侣影响", "个人成长"],
            2: ["家庭财富", "价值观", "语言能力"],
            3: ["沟通", "兄弟姐妹", "短途旅行"],
            4: ["情感安全", "房产", "母亲"],
            5: ["子女", "创造力", "浪漫"],
            6: ["服务", "健康", "克服困难"],
            7: ["婚姻", "合作", "公开关系"],
            8: ["转化", "共同资源", "秘密"],
            9: ["远方", "智慧", "灵性"],
            10: ["事业", "社会地位", "公众形象"],
            11: ["社交网络", "愿望", "收益"],
            12: ["隐秘", "牺牲", "灵性解脱"],
        }
        analysis.house_themes = house_themes.get(analysis.dk_house, [])
    
    def _analyze_aspects(self, analysis: DKAnalysis, chart_data: Dict):
        """分析DK的相位影响"""
        planets = chart_data.get("planets", {})
        dk_lon = None
        
        for pname, pdata in planets.items():
            if pname == analysis.dk_planet and isinstance(pdata, dict):
                dk_lon = pdata.get("degree")
                break
        
        if dk_lon is None:
            return
        
        # 检测合相（8度内）
        conjunctions = []
        for pname, pdata in planets.items():
            if pname == analysis.dk_planet:
                continue
            if isinstance(pdata, dict) and "degree" in pdata:
                diff = abs((pdata["degree"] - dk_lon + 180) % 360 - 180)
                if diff < 8:
                    conjunctions.append({
                        "planet": pname,
                        "orb": round(diff, 2),
                        "nature": "friendly" if pname in FRIENDLY_PLANETS.get(analysis.dk_planet, []) else "neutral"
                    })
        
        analysis.conjunctions = conjunctions
        
        # 分类友好/敌对影响
        for conj in conjunctions:
            if conj["nature"] == "friendly":
                analysis.aspects_friendly.append(conj["planet"])
            elif conj["planet"] in ENEMY_PLANETS.get(analysis.dk_planet, []):
                analysis.aspects_hostile.append(conj["planet"])
    
    def _analyze_d9(self, analysis: DKAnalysis, chart_data: Dict):
        """分析DK在D9中的位置"""
        # 简化实现：从chart_data的context中提取D9数据
        context = chart_data.get("context", {})
        d9_planets = context.get("navamsa_planets", {})
        
        if analysis.dk_planet in d9_planets:
            d9_data = d9_planets[analysis.dk_planet]
            analysis.d9_sign = d9_data.get("sign")
            analysis.d9_house = d9_data.get("house")
            analysis.d9_dignity = d9_data.get("dignity")
    
    def _check_status(self, analysis: DKAnalysis, dk_info: Dict):
        """检查DK状态"""
        analysis.is_retrograde = dk_info.get("retrograde", False)
        analysis.is_combust = dk_info.get("combust", False)
        analysis.dignity = dk_info.get("dignity", "")
    
    def _comprehensive_assessment(self, analysis: DKAnalysis):
        """综合评估婚姻质量"""
        score = 0.5
        
        # 正面因素
        if analysis.dignity in ["exalted", "own", "friendly"]:
            score += 0.15
        if len(analysis.aspects_friendly) > len(analysis.aspects_hostile):
            score += 0.1
        if analysis.dk_house in [1, 4, 7, 10]:
            score += 0.05
        if not analysis.is_combust:
            score += 0.1
        
        # 负面因素
        if analysis.dignity in ["debilitated", "enemy"]:
            score -= 0.15
        if analysis.is_combust:
            score -= 0.15
        if analysis.is_retrograde:
            score -= 0.05
        if len(analysis.aspects_hostile) > 0:
            score -= 0.05 * len(analysis.aspects_hostile)
        if analysis.dk_house in [6, 8, 12]:
            score -= 0.05
        
        analysis.marriage_quality_score = max(0, min(1, score))
        
        # 时间线索
        if analysis.is_retrograde:
            analysis.timing_clues.append("婚姻可能较晚或经历反复")
        if analysis.dk_house == 7:
            analysis.timing_clues.append("婚姻关系是核心人生主题")
        if analysis.dk_planet == "Saturn":
            analysis.timing_clues.append("婚姻可能在30岁后或更晚")
        
        # 补救措施
        if analysis.marriage_quality_score < 0.4:
            analysis.remedies.append("建议进行传统的婚姻祈福仪式")
        if analysis.is_combust:
            analysis.remedies.append("DK被燃烧，建议加强个人独立性")
        if analysis.dk_planet == "Saturn":
            analysis.remedies.append("耐心是关键，不要急于进入婚姻")
    
    def _generate_narrative(self, analysis: DKAnalysis) -> str:
        """生成DK解读叙事"""
        parts = []
        
        # 核心画像
        parts.append(f"### 伴侣核心画像：{analysis.core_profile}\n")
        parts.append(f"您的Darakaraka（配偶象征星）是 **{analysis.dk_planet}**，")
        parts.append(f"落在 **{analysis.dk_sign}** 的第 **{analysis.dk_house}** 宫。\n")
        
        # 性格特质
        if analysis.personality_traits:
            parts.append(f"\n伴侣的核心性格特质：{', '.join(analysis.personality_traits[:5])}。\n")
        
        # 宫位解读
        parts.append(f"\n{analysis.house_meaning}\n")
        
        # 吸引力
        if analysis.attracted_to:
            parts.append(f"\n您在伴侣身上寻找的品质：{', '.join(analysis.attracted_to[:3])}。\n")
        
        # 挑战
        if analysis.challenges:
            parts.append(f"\n需要注意的议题：{', '.join(analysis.challenges[:3])}。\n")
        
        # 正面
        if analysis.positive_traits:
            parts.append(f"\n伴侣带来的礼物：{', '.join(analysis.positive_traits[:3])}。\n")
        
        # 合相影响
        if analysis.conjunctions:
            parts.append(f"\n与DK合相的行星：")
            for conj in analysis.conjunctions:
                parts.append(f"  - {conj['planet']} (orb: {conj['orb']}°)")
            parts.append("")
        
        # D9
        if analysis.d9_sign:
            parts.append(f"\n在Navamsa (D9) 中，DK位于 **{analysis.d9_sign}**，")
            if analysis.d9_dignity:
                parts.append(f"状态为 **{analysis.d9_dignity}**。\n")
            parts.append("这揭示了灵魂层面对伴侣的深层需求。\n")
        
        # 综合评估
        quality_desc = "优秀" if analysis.marriage_quality_score > 0.7 else \
                      "良好" if analysis.marriage_quality_score > 0.5 else \
                      "需要努力" if analysis.marriage_quality_score > 0.3 else "有挑战"
        parts.append(f"\n**婚姻质量评估：{quality_desc}** ({analysis.marriage_quality_score:.0%})\n")
        
        # 时间线索
        if analysis.timing_clues:
            parts.append(f"\n时间线索：{'; '.join(analysis.timing_clues)}\n")
        
        # 补救
        if analysis.remedies:
            parts.append(f"\n建议：{'; '.join(analysis.remedies)}\n")
        
        return "\n".join(parts)
    
    def to_dict(self, analysis: DKAnalysis) -> Dict:
        """转换为字典（JSON可序列化）"""
        return {
            "dk_planet": analysis.dk_planet,
            "dk_sign": analysis.dk_sign,
            "dk_house": analysis.dk_house,
            "dk_degree": round(analysis.dk_degree, 2),
            "d9_sign": analysis.d9_sign,
            "d9_house": analysis.d9_house,
            "d9_dignity": analysis.d9_dignity,
            "is_retrograde": analysis.is_retrograde,
            "is_combust": analysis.is_combust,
            "dignity": analysis.dignity,
            "core_profile": analysis.core_profile,
            "personality_traits": analysis.personality_traits,
            "attracted_to": analysis.attracted_to,
            "challenges": analysis.challenges,
            "positive_traits": analysis.positive_traits,
            "career_signs": analysis.career_signs,
            "house_meaning": analysis.house_meaning,
            "house_themes": analysis.house_themes,
            "conjunctions": analysis.conjunctions,
            "aspects_friendly": analysis.aspects_friendly,
            "aspects_hostile": analysis.aspects_hostile,
            "marriage_quality_score": round(analysis.marriage_quality_score, 2),
            "timing_clues": analysis.timing_clues,
            "remedies": analysis.remedies,
            "narrative": analysis.narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_darakaraka(chart_data: Dict, use_8_karaka: bool = True) -> Dict:
    """便捷函数：分析Darakaraka"""
    reader = DarakarakaReader()
    analysis = reader.analyze(chart_data, use_8_karaka)
    return reader.to_dict(analysis)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    # 模拟测试数据
    mock_chart = {
        "planets": {
            "Sun": {"degree": 20.0, "degree_in_sign": 20.0, "sign": "Aries", "house": 1, "retrograde": False, "combust": False, "dignity": "exalted"},
            "Moon": {"degree": 50.0, "degree_in_sign": 20.0, "sign": "Taurus", "house": 2, "retrograde": False},
            "Mars": {"degree": 80.0, "degree_in_sign": 20.0, "sign": "Gemini", "house": 3, "retrograde": False},
            "Mercury": {"degree": 110.0, "degree_in_sign": 20.0, "sign": "Cancer", "house": 4, "retrograde": False},
            "Jupiter": {"degree": 140.0, "degree_in_sign": 20.0, "sign": "Leo", "house": 5, "retrograde": False},
            "Venus": {"degree": 170.0, "degree_in_sign": 20.0, "sign": "Virgo", "house": 6, "retrograde": False},
            "Saturn": {"degree": 200.0, "degree_in_sign": 20.0, "sign": "Libra", "house": 7, "retrograde": True},
            "Rahu": {"degree": 230.0, "degree_in_sign": 20.0, "sign": "Scorpio", "house": 8, "retrograde": False},
        },
        "context": {
            "navamsa_planets": {
                "Saturn": {"sign": "Capricorn", "house": 10, "dignity": "own"}
            }
        }
    }
    
    print("=" * 60)
    print("Darakaraka 深度解读引擎")
    print("=" * 60)
    
    result = analyze_darakaraka(mock_chart, use_8_karaka=True)
    
    print(f"\nDK行星: {result['dk_planet']}")
    print(f"DK星座: {result['dk_sign']}")
    print(f"DK宫位: {result['dk_house']}")
    print(f"\n核心画像: {result['core_profile']}")
    print(f"\n婚姻质量评分: {result['marriage_quality_score']}")
    
    print("\n" + "=" * 60)
    print("完整叙事")
    print("=" * 60)
    print(result['narrative'])
