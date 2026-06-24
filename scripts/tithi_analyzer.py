#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tithi_analyzer.py — Tithi主星分析引擎
======================================
分析Tithi（太阴日）及其主星对情感模式和关系的影响

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TithiType(Enum):
    """Tithi类型"""
    NANDA = "Nanda"         # 1, 6, 11, 16, 21, 26 — 幸福
    BHADRA = "Bhadra"       # 2, 7, 12, 17, 22, 27 — 吉祥
    JAYA = "Jaya"           # 3, 8, 13, 18, 23, 28 — 胜利
    RIKTA = "Rikta"         # 4, 9, 14, 19, 24, 29 — 空虚
    PURNA = "Purna"         # 5, 10, 15, 20, 25, 30 — 圆满


# 30个Tithi及其主星
TITHI_LORDS = {
    # Shukla Paksha (亮月期)
    1: {"name": "Pratipada", "lord": "Sun", "type": TithiType.NANDA},
    2: {"name": "Dwitiya", "lord": "Moon", "type": TithiType.BHADRA},
    3: {"name": "Tritiya", "lord": "Mars", "type": TithiType.JAYA},
    4: {"name": "Chaturthi", "lord": "Mercury", "type": TithiType.RIKTA},
    5: {"name": "Panchami", "lord": "Jupiter", "type": TithiType.PURNA},
    6: {"name": "Shashthi", "lord": "Venus", "type": TithiType.NANDA},
    7: {"name": "Saptami", "lord": "Saturn", "type": TithiType.BHADRA},
    8: {"name": "Ashtami", "lord": "Rahu", "type": TithiType.JAYA},
    9: {"name": "Navami", "lord": "Sun", "type": TithiType.RIKTA},
    10: {"name": "Dashami", "lord": "Moon", "type": TithiType.PURNA},
    11: {"name": "Ekadashi", "lord": "Mars", "type": TithiType.NANDA},
    12: {"name": "Dwadashi", "lord": "Mercury", "type": TithiType.BHADRA},
    13: {"name": "Trayodashi", "lord": "Jupiter", "type": TithiType.JAYA},
    14: {"name": "Chaturdashi", "lord": "Venus", "type": TithiType.RIKTA},
    15: {"name": "Purnima", "lord": "Saturn/Rahu", "type": TithiType.PURNA},
    
    # Krishna Paksha (暗月期)
    16: {"name": "Pratipada", "lord": "Sun", "type": TithiType.NANDA},
    17: {"name": "Dwitiya", "lord": "Moon", "type": TithiType.BHADRA},
    18: {"name": "Tritiya", "lord": "Mars", "type": TithiType.JAYA},
    19: {"name": "Chaturthi", "lord": "Mercury", "type": TithiType.RIKTA},
    20: {"name": "Panchami", "lord": "Jupiter", "type": TithiType.PURNA},
    21: {"name": "Shashthi", "lord": "Venus", "type": TithiType.NANDA},
    22: {"name": "Saptami", "lord": "Saturn", "type": TithiType.BHADRA},
    23: {"name": "Ashtami", "lord": "Rahu", "type": TithiType.JAYA},
    24: {"name": "Navami", "lord": "Sun", "type": TithiType.RIKTA},
    25: {"name": "Dashami", "lord": "Moon", "type": TithiType.PURNA},
    26: {"name": "Ekadashi", "lord": "Mars", "type": TithiType.NANDA},
    27: {"name": "Dwadashi", "lord": "Mercury", "type": TithiType.BHADRA},
    28: {"name": "Trayodashi", "lord": "Jupiter", "type": TithiType.JAYA},
    29: {"name": "Chaturdashi", "lord": "Venus", "type": TithiType.RIKTA},
    30: {"name": "Amavasya", "lord": "Saturn/Rahu", "type": TithiType.PURNA},
}

# 主星星座解读（按四元素）
LORD_SIGN_ELEMENT = {
    "Sun": "Fire", "Moon": "Water", "Mars": "Fire",
    "Mercury": "Earth", "Jupiter": "Ether", "Venus": "Water",
    "Saturn": "Air", "Rahu": "Air", "Ketu": "Fire",
}

ELEMENT_MEANINGS = {
    "Fire": "热情、积极、直接、有领导力。情感表达热烈但可能冲动。",
    "Water": "情感丰富、直觉敏锐、关怀体贴。情感深沉但可能依赖。",
    "Earth": "务实、稳定、理性。情感表达谨慎但可靠。",
    "Air": "理性、沟通、社交。情感需要智识连接。",
    "Ether": "灵性、智慧、扩张。情感带有精神层面。",
}

# 主星宫位解读（对情感/关系的影响）
LORD_HOUSE_MEANINGS = {
    1: "情感模式强烈影响自我认同，关系中需要被看见和认可。",
    2: "情感与家庭财富/价值观绑定，重视物质安全感。",
    3: "通过沟通和 siblings 表达情感，喜欢智力交流。",
    4: "情感根植于家庭和内心安全感，需要情感庇护。",
    5: "浪漫多情，通过创造力和子女表达爱，喜欢恋爱。",
    6: "情感表达带有服务性质，可能在关系中过度付出。",
    7: "关系是核心主题，伴侣影响情感模式深远。",
    8: "深层转化型情感，可能经历激烈的情绪变化。",
    9: "情感带有哲学/灵性维度，可能被远方的人吸引。",
    10: "情感与事业/社会地位相关，可能选择有成就的伴侣。",
    11: "通过社交网络表达情感，朋友可能发展为伴侣。",
    12: "隐秘的情感模式，可能在关系中牺牲或逃避。",
}

# Tithi瑕疵（Tithi Dosh）
TITHI_DOSHA = {
    # 主星在火象星座且受克
    "fire_debilitated": {
        "condition": "主星在火象星座且被凶星相位",
        "effect": "情感模式有缺陷，关系中容易冲突",
        "remedy": "加强水元素平衡，冥想",
    },
    # Rikta Tithi
    "rikta": {
        "condition": "出生在Rikta Tithi (4/9/14/19/24/29)",
        "effect": "Tithi空虚，某些领域可能缺乏支持",
        "remedy": " charity，捐赠，灵性练习",
    },
    # 主星逆行
    "retrograde_lord": {
        "condition": "Tithi主星逆行",
        "effect": "情感表达有延迟或反复",
        "remedy": "耐心，给予关系更多时间",
    },
}


@dataclass
class TithiAnalysis:
    """Tithi分析结果"""
    # 基础信息
    tithi_number: int
    tithi_name: str
    tithi_type: str
    tithi_type_cn: str
    paksha: str              # shukla/krishna
    
    # 主星信息
    tithi_lord: str
    lord_sign: str
    lord_house: int
    lord_element: str
    lord_dignity: str
    lord_retrograde: bool
    
    # 解读
    emotional_pattern: str = ""
    relationship_style: str = ""
    attracted_to: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    
    # 瑕疵
    doshas: List[Dict] = field(default_factory=list)
    
    # 综合
    tithi_score: float = 0.5   # 0-1
    narrative: str = ""


class TithiAnalyzer:
    """Tithi主星分析引擎"""
    
    def __init__(self):
        self.tithi_lords = TITHI_LORDS
        self.element_meanings = ELEMENT_MEANINGS
        self.house_meanings = LORD_HOUSE_MEANINGS
        self.dosha_defs = TITHI_DOSHA
    
    def analyze(self, chart_data: Dict) -> TithiAnalysis:
        """
        分析Tithi
        
        Args:
            chart_data: 标准星盘数据（需包含tithi信息或计算）
        
        Returns:
            TithiAnalysis对象
        """
        # Step 1: 计算Tithi
        tithi_num, paksha = self._calculate_tithi(chart_data)
        
        # Step 2: 获取Tithi信息
        tithi_info = self.tithi_lords.get(tithi_num, {})
        tithi_name = tithi_info.get("name", "")
        tithi_type = tithi_info.get("type", TithiType.NANDA)
        tithi_lord = tithi_info.get("lord", "Sun")
        
        # Step 3: 获取主星在星盘中的位置
        planets = chart_data.get("planets", {})
        lord_data = planets.get(tithi_lord, {}) if tithi_lord not in ["Saturn/Rahu"] else planets.get("Saturn", {})
        
        if not isinstance(lord_data, dict):
            lord_data = {}
        
        lord_sign = lord_data.get("sign", "")
        lord_house = lord_data.get("house", 0)
        lord_dignity = lord_data.get("dignity", "")
        lord_retrograde = lord_data.get("retrograde", False)
        
        # Step 4: 创建分析对象
        analysis = TithiAnalysis(
            tithi_number=tithi_num,
            tithi_name=tithi_name,
            tithi_type=tithi_type.value,
            tithi_type_cn=self._tithi_type_to_chinese(tithi_type),
            paksha=paksha,
            tithi_lord=tithi_lord,
            lord_sign=lord_sign,
            lord_house=lord_house,
            lord_element=LORD_SIGN_ELEMENT.get(tithi_lord, "Fire"),
            lord_dignity=lord_dignity,
            lord_retrograde=lord_retrograde,
        )
        
        # Step 5: 生成解读
        self._generate_interpretation(analysis)
        
        # Step 6: 检测瑕疵
        self._detect_dosha(analysis)
        
        # Step 7: 综合评估
        self._comprehensive_assessment(analysis)
        
        # Step 8: 生成叙事
        analysis.narrative = self._generate_narrative(analysis)
        
        return analysis
    
    def _calculate_tithi(self, chart_data: Dict) -> Tuple[int, str]:
        """计算Tithi（简化版）"""
        # 从chart_data中提取日月经度
        planets = chart_data.get("planets", {})
        
        sun_data = planets.get("Sun", {})
        moon_data = planets.get("Moon", {})
        
        if not isinstance(sun_data, dict) or not isinstance(moon_data, dict):
            return 1, "shukla"
        
        sun_lon = sun_data.get("lon", sun_data.get("degree", 0))
        moon_lon = moon_data.get("lon", moon_data.get("degree", 0))
        
        # Tithi = (Moon - Sun) / 12
        diff = (moon_lon - sun_lon) % 360
        tithi = int(diff / 12) + 1
        
        # Paksha
        paksha = "shukla" if diff < 180 else "krishna"
        
        # 调整Krishna Paksha的Tithi编号
        if paksha == "krishna":
            tithi = tithi - 15 if tithi > 15 else tithi + 15
        
        return min(tithi, 30), paksha
    
    def _tithi_type_to_chinese(self, tithi_type: TithiType) -> str:
        """Tithi类型转中文"""
        names = {
            TithiType.NANDA: "幸福",
            TithiType.BHADRA: "吉祥",
            TithiType.JAYA: "胜利",
            TithiType.RIKTA: "空虚",
            TithiType.PURNA: "圆满",
        }
        return names.get(tithi_type, "未知")
    
    def _generate_interpretation(self, analysis: TithiAnalysis):
        """生成解读"""
        # 情感模式（基于主星）
        lord_traits = {
            "Sun": "热情、自信、需要被尊重。在关系中寻求平等的伙伴关系。",
            "Moon": "情感丰富、 nurturing、需要安全感。在关系中非常体贴。",
            "Mars": "直接、热情、有行动力。在关系中主动追求。",
            "Mercury": "理性、沟通导向、喜欢智力交流。在关系中需要思想契合。",
            "Jupiter": "慷慨、智慧、有道德感。在关系中提供指导和支持。",
            "Venus": "浪漫、注重美感、追求和谐。在关系中非常重视爱情。",
            "Saturn": "严肃、忠诚、需要时间建立信任。在关系中非常专一。",
            "Rahu": "强烈、非传统、渴望新奇。在关系中追求独特体验。",
        }
        
        analysis.emotional_pattern = lord_traits.get(analysis.tithi_lord, "独特的情感模式")
        
        # 关系风格（基于元素）
        element_style = {
            "Fire": "热情直接，喜欢主动追求，关系中需要激情和冒险。",
            "Water": "情感深沉，重视连接和亲密，关系中需要情感安全感。",
            "Earth": "务实稳定，重视承诺和责任，关系中需要物质基础。",
            "Air": "理性沟通，重视思想和交流，关系中需要智力刺激。",
            "Ether": "灵性导向，重视精神成长，关系中需要共同的精神追求。",
        }
        
        analysis.relationship_style = element_style.get(analysis.lord_element, "平衡的关系风格")
        
        # 吸引力
        analysis.attracted_to = self._get_attracted_to(analysis.tithi_lord)
        
        # 挑战
        analysis.challenges = self._get_challenges(analysis.tithi_lord)
        
        # 优势
        analysis.strengths = self._get_strengths(analysis.tithi_lord)
    
    def _get_attracted_to(self, lord: str) -> List[str]:
        """获取吸引力方向"""
        mapping = {
            "Sun": ["有领导力的人", "自信的人", "有创造力的人"],
            "Moon": ["温暖体贴的人", "重视家庭的人", "情感丰富的人"],
            "Mars": ["有活力的人", "独立自强的人", "敢于冒险的人"],
            "Mercury": ["聪明有趣的人", "善于沟通的人", "有学识的人"],
            "Jupiter": ["有智慧的人", "道德高尚的人", "慷慨的人"],
            "Venus": ["有品位的人", "浪漫的人", "外表吸引的人"],
            "Saturn": ["成熟稳重的人", "有责任感的人", "事业稳定的人"],
            "Rahu": ["与众不同的人", "有野心的人", "异域文化背景的人"],
        }
        return mapping.get(lord, ["有独特魅力的人"])
    
    def _get_challenges(self, lord: str) -> List[str]:
        """获取挑战"""
        mapping = {
            "Sun": ["自尊心过强", "控制欲", "需要被认可"],
            "Moon": ["情绪波动", "过度依赖", "安全感需求高"],
            "Mars": ["脾气暴躁", "冲动", "好胜心强"],
            "Mercury": ["过于理性", "善变", "分析过度"],
            "Jupiter": ["过度理想化", "说教倾向", "过度乐观"],
            "Venus": ["注重外表", "物质倾向", "优柔寡断"],
            "Saturn": ["情感压抑", "冷淡疏离", "悲观"],
            "Rahu": ["非传统关系", "不稳定", "欺骗风险"],
        }
        return mapping.get(lord, ["需要自我觉察"])
    
    def _get_strengths(self, lord: str) -> List[str]:
        """获取优势"""
        mapping = {
            "Sun": ["忠诚", "保护欲强", "有责任感"],
            "Moon": ["无条件的爱", "善解人意", " nurturing"],
            "Mars": ["积极主动", "勇敢", "激情"],
            "Mercury": ["沟通顺畅", "幽默", "解决问题能力强"],
            "Jupiter": ["智慧引导", "慷慨", "精神伴侣"],
            "Venus": ["浪漫", "和谐", "审美力强"],
            "Saturn": ["极度忠诚", "可靠", "长期承诺"],
            "Rahu": ["独特体验", "突破局限", "激发潜能"],
        }
        return mapping.get(lord, ["独特的魅力"])
    
    def _detect_dosha(self, analysis: TithiAnalysis):
        """检测Tithi瑕疵"""
        doshas = []
        
        # Rikta Tithi
        if analysis.tithi_type == "Rikta":
            doshas.append({
                "type": "rikta",
                "name": "Rikta Tithi Dosh",
                "description": "出生在空虚Tithi，某些领域可能缺乏支持",
                "remedy": "多做慈善和捐赠，加强灵性练习",
            })
        
        # 主星逆行
        if analysis.lord_retrograde:
            doshas.append({
                "type": "retrograde_lord",
                "name": "Retrograde Lord Dosh",
                "description": "Tithi主星逆行，情感表达可能有延迟或反复",
                "remedy": "给予关系更多时间和耐心",
            })
        
        # 主星落陷
        if analysis.lord_dignity == "debilitated":
            doshas.append({
                "type": "debilitated_lord",
                "name": "Debilitated Lord Dosh",
                "description": "Tithi主星落陷，情感模式有根本缺陷",
                "remedy": "通过灵性成长弥补，寻找互补的伴侣",
            })
        
        analysis.doshas = doshas
    
    def _comprehensive_assessment(self, analysis: TithiAnalysis):
        """综合评估"""
        score = 0.5
        
        # 正面因素
        if analysis.tithi_type in ["Nanda", "Bhadra", "Jaya", "Purna"]:
            score += 0.15
        if analysis.lord_dignity in ["exalted", "own", "friendly"]:
            score += 0.15
        if not analysis.lord_retrograde:
            score += 0.1
        
        # 负面因素
        if analysis.tithi_type == "Rikta":
            score -= 0.1
        if analysis.lord_dignity == "debilitated":
            score -= 0.15
        if analysis.lord_retrograde:
            score -= 0.05
        if analysis.doshas:
            score -= 0.05 * len(analysis.doshas)
        
        analysis.tithi_score = max(0, min(1, score))
    
    def _generate_narrative(self, analysis: TithiAnalysis) -> str:
        """生成叙事"""
        parts = []
        
        parts.append("### Tithi主星分析 — 情感模式深度解读\n")
        parts.append(f"您的出生Tithi: **{analysis.tithi_name}** (第{analysis.tithi_number}个Tithi)\n")
        parts.append(f"Tithi类型: **{analysis.tithi_type_cn}** ({analysis.tithi_type})\n")
        parts.append(f"月相: **{'亮月期 (Shukla Paksha)' if analysis.paksha == 'shukla' else '暗月期 (Krishna Paksha)'}**\n")
        parts.append(f"Tithi主星: **{analysis.tithi_lord}**\n")
        
        # 主星位置
        if analysis.lord_sign:
            parts.append(f"主星位置: {analysis.lord_sign} 第{analysis.lord_house}宫\n")
        
        parts.append(f"\n#### 情感模式\n")
        parts.append(f"{analysis.emotional_pattern}\n")
        
        parts.append(f"\n#### 关系风格\n")
        parts.append(f"{analysis.relationship_style}\n")
        
        # 吸引力
        if analysis.attracted_to:
            parts.append(f"\n#### 您被什么样的人吸引\n")
            for item in analysis.attracted_to:
                parts.append(f"- {item}\n")
        
        # 挑战
        if analysis.challenges:
            parts.append(f"\n#### 需要注意的议题\n")
            for item in analysis.challenges:
                parts.append(f"- {item}\n")
        
        # 优势
        if analysis.strengths:
            parts.append(f"\n#### 您的情感优势\n")
            for item in analysis.strengths:
                parts.append(f"- {item}\n")
        
        # 宫位解读
        if analysis.lord_house > 0:
            house_meaning = self.house_meanings.get(analysis.lord_house, "")
            if house_meaning:
                parts.append(f"\n#### 主星宫位解读\n")
                parts.append(f"{house_meaning}\n")
        
        # 瑕疵
        if analysis.doshas:
            parts.append(f"\n#### Tithi瑕疵检测\n")
            for d in analysis.doshas:
                parts.append(f"⚠️ **{d['name']}**: {d['description']}\n")
                parts.append(f"   补救: {d['remedy']}\n")
        
        # 综合评估
        quality = "优秀" if analysis.tithi_score > 0.7 else \
                 "良好" if analysis.tithi_score > 0.5 else \
                 "需要努力" if analysis.tithi_score > 0.3 else "有挑战"
        parts.append(f"\n#### 综合评估\n")
        parts.append(f"Tithi质量: **{quality}** ({analysis.tithi_score:.0%})\n")
        
        return "\n".join(parts)
    
    def to_dict(self, analysis: TithiAnalysis) -> Dict:
        """转换为字典"""
        return {
            "tithi_number": analysis.tithi_number,
            "tithi_name": analysis.tithi_name,
            "tithi_type": analysis.tithi_type,
            "tithi_type_cn": analysis.tithi_type_cn,
            "paksha": analysis.paksha,
            "tithi_lord": analysis.tithi_lord,
            "lord_sign": analysis.lord_sign,
            "lord_house": analysis.lord_house,
            "lord_element": analysis.lord_element,
            "lord_dignity": analysis.lord_dignity,
            "lord_retrograde": analysis.lord_retrograde,
            "emotional_pattern": analysis.emotional_pattern,
            "relationship_style": analysis.relationship_style,
            "attracted_to": analysis.attracted_to,
            "challenges": analysis.challenges,
            "strengths": analysis.strengths,
            "doshas": analysis.doshas,
            "tithi_score": round(analysis.tithi_score, 2),
            "narrative": analysis.narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_tithi(chart_data: Dict) -> Dict:
    """便捷函数"""
    analyzer = TithiAnalyzer()
    analysis = analyzer.analyze(chart_data)
    return analyzer.to_dict(analysis)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    mock_chart = {
        "planets": {
            "Sun": {"degree": 20.0},
            "Moon": {"degree": 65.0, "sign": "Taurus", "house": 2, "dignity": "own"},
        },
    }
    
    print("=" * 60)
    print("Tithi主星分析引擎")
    print("=" * 60)
    
    result = analyze_tithi(mock_chart)
    print(result["narrative"])
    print(f"\nTithi得分: {result['tithi_score']}")
