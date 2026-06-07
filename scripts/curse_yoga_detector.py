#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
curse_yoga_detector.py — 凶星合相命名与检测引擎
================================================
检测并命名危险的行星合相，提供预警和补救建议

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# 凶星合相定义
CURSE_DEFINITIONS = {
    "yama_yoga": {
        "name": "Yama Yoga",
        "name_cn": "阎魔瑜伽",
        "planets": ["Mars", "Saturn"],
        "houses_critical": [1, 2, 7, 8, 12],  # 在这些宫位更危险
        "meaning": "死亡之神 sitting，等待激活。可能造成危险疾病、事故、家族血脉中断。",
        "activation": ["Mars或Saturn的Dasha", "Mars或Saturn的Transit", "Mula Dasha激活"],
        "severity": 5,  # 1-5
        "remedy": "需要上师保护，唱诵Guru Vandana，侍奉上师",
        "deity": "上师/Guru",
        "body_parts": ["血液", "骨骼", "神经系统"],
        "family_effect": "家族血脉可能中断，无子女或子女早夭",
    },
    "preta_yoga_saturn_rahu": {
        "name": "Preta Yoga",
        "name_cn": "亡灵瑜伽（土星+罗喉）",
        "planets": ["Saturn", "Rahu"],
        "houses_critical": [8, 11, 6],  # 8宫=死亡，11宫=Badhaka，6宫=疾病
        "meaning": "过早死亡风险，慢性疾病，可能来自祖先未解决的业力（未得葬礼的祖先鬼魂）。",
        "activation": ["Saturn或Rahu的Dasha", "Badhaka宫被激活", "水瓶座相关事件"],
        "severity": 5,
        "remedy": "湿婆能量，唱诵Mahamrityunjaya Mantra，进行祖先祭祀",
        "deity": "湿婆/Shiva",
        "body_parts": ["慢性疾病部位", "骨骼", "神经系统退化"],
        "family_effect": "家族血脉停止，女性不婚或无子女，男性只有女儿",
    },
    "preta_yoga_saturn_ketu": {
        "name": "Preta Yoga",
        "name_cn": "亡灵瑜伽（土星+计都）",
        "planets": ["Saturn", "Ketu"],
        "houses_critical": [8, 11, 6],
        "meaning": "过早死亡风险，慢性疾病，灵性干扰，可能来自祖先业力。",
        "activation": ["Saturn或Ketu的Dasha", "灵性敏感期"],
        "severity": 5,
        "remedy": "湿婆能量，唱诵Mahamrityunjaya Mantra，火供",
        "deity": "湿婆/Shiva",
        "body_parts": ["慢性疾病", "灵性困扰", "睡眠障碍"],
        "family_effect": "家族业力传递，后代受影响",
    },
    "rakshasa_yoga": {
        "name": "Rakshasa Yoga",
        "name_cn": "恶魔瑜伽",
        "planets": ["Mars", "Rahu"],
        "houses_critical": [6, 8],  # 6宫=暴力/疾病，8宫=突变/死亡
        "meaning": "暴力事件，外部攻击，神经系统受损，可能被粗俗或微妙的恶魔力量攻击。",
        "activation": ["Mars或Rahu的Dasha", "6宫或8宫被Transit激活"],
        "severity": 4,
        "remedy": "杜尔迦女神，唱诵Durga Saptashati，建立界限",
        "deity": "杜尔迦/Durga",
        "body_parts": ["神经系统", "肌肉", "免疫系统"],
        "family_effect": "家族成员可能遭受暴力或事故",
    },
    "pisacha_yoga": {
        "name": "Pisacha Yoga",
        "name_cn": "鬼魅瑜伽",
        "planets": ["Mars", "Ketu"],
        "houses_critical": [8, 1, 6],  # 8宫=死亡，1宫=身体，6宫=疾病
        "meaning": "与有毒的人接触，被充满愤怒仇恨的鬼魂困扰，可能遭遇事故前感到被推动。",
        "activation": ["Mars或Ketu的Dasha", "天蝎座相关事件", "8宫被激活"],
        "severity": 4,
        "remedy": "毗湿奴，唱诵Vishnu Sahasranama，去除毒素",
        "deity": "毗湿奴/Vishnu",
        "body_parts": ["血液", "毒素", "生殖系统"],
        "family_effect": "与有毒人物的关系，婚姻中毒性伴侣",
    },
}

# 宫位拟人化（哪个身体部位/生活领域受影响）
HOUSE_PERSONIFICATION = {
    1: "自身/身体/个性",
    2: "家庭/财富/语言能力",
    3: "兄弟姐妹/勇气/沟通",
    4: "母亲/房产/内心",
    5: "子女/创造力/投机",
    6: "疾病/敌人/服务",
    7: "配偶/合作/公开对手",
    8: "死亡/突变/遗产/灵性",
    9: "父亲/长途旅行/高等教育",
    10: "事业/社会地位/母亲",
    11: "收益/愿望/社交网络",
    12: "损失/隐秘/灵性/海外",
}

# 行星拟人化（如果某行星在此位置，代表谁变得有毒/危险）
PLANET_PERSONIFICATION = {
    "Sun": "父亲/权威人物",
    "Moon": "母亲/情感滋养者",
    "Mars": "兄弟/竞争对手/行动者",
    "Mercury": "兄弟姐妹/年轻亲戚/商人",
    "Jupiter": "导师/子女/丈夫(女性)",
    "Venus": "配偶/妻子(男性)/艺术家",
    "Saturn": "长辈/仆人/苦行者",
    "Rahu": "外国人/非传统人物/野心家",
    "Ketu": "灵性导师/分离者/神秘人物",
}


@dataclass
class CurseDetection:
    """单个诅咒检测结果"""
    curse_type: str                    # yama/preta/rakshasa/pisacha
    curse_name: str
    curse_name_cn: str
    planets: List[str]
    house: int
    house_meaning: str
    sign: str
    
    # 严重程度
    severity: int                      # 1-5
    severity_label: str                # critical/high/medium/low
    
    # 影响范围
    affected_area: str                 # 影响的宫位主题
    affected_person: str               # 可能受影响的人（拟人化）
    body_parts: List[str]
    family_effect: str
    
    # 激活条件
    activation_triggers: List[str]
    current_dasha_relevant: bool       # 当前Dasha是否相关
    transit_relevant: bool             # 当前Transit是否相关
    
    # 补救
    remedy: str
    deity: str
    mantras: List[str]
    
    # 叙事
    narrative: str = ""


@dataclass
class CurseAnalysis:
    """诅咒分析结果"""
    curses_detected: List[CurseDetection] = field(default_factory=list)
    overall_risk: str = "low"          # low/medium/high/critical
    risk_score: float = 0.0            # 0-1
    
    # 综合建议
    general_remedies: List[str] = field(default_factory=list)
    general_mantras: List[str] = field(default_factory=list)
    lifestyle_advice: List[str] = field(default_factory=list)
    
    # 时间预警
    upcoming_danger_periods: List[Dict] = field(default_factory=list)
    
    narrative: str = ""


class CurseYogaDetector:
    """凶星合相命名与检测引擎"""
    
    def __init__(self):
        self.definitions = CURSE_DEFINITIONS
        self.house_person = HOUSE_PERSONIFICATION
        self.planet_person = PLANET_PERSONIFICATION
    
    def analyze(self, chart_data: Dict, current_dasha: Optional[str] = None,
                transit_data: Optional[Dict] = None) -> CurseAnalysis:
        """
        检测凶星合相
        
        Args:
            chart_data: 标准星盘数据
            current_dasha: 当前Dasha主星（可选）
            transit_data: 当前Transit数据（可选）
        
        Returns:
            CurseAnalysis对象
        """
        planets = chart_data.get("planets", {})
        asc_sign = chart_data.get("ascendant", {}).get("sign", "")
        
        analysis = CurseAnalysis()
        
        # Step 1: 在D1中检测
        d1_curses = self._detect_in_chart(planets, "D1")
        analysis.curses_detected.extend(d1_curses)
        
        # Step 2: 在D9中检测（如果有）
        context = chart_data.get("context", {})
        d9_planets = context.get("navamsa_planets", {})
        if d9_planets:
            d9_curses = self._detect_in_chart(d9_planets, "D9")
            for c in d9_curses:
                c.narrative = f"[Navamsa] {c.narrative}"
            analysis.curses_detected.extend(d9_curses)
        
        # Step 3: 评估与当前Dasha/Transit的关联
        if current_dasha:
            self._assess_dasha_relevance(analysis, current_dasha)
        
        # Step 4: 综合评估
        self._comprehensive_assessment(analysis)
        
        # Step 5: 生成建议
        self._generate_remedies(analysis)
        
        # Step 6: 生成叙事
        analysis.narrative = self._generate_narrative(analysis)
        
        return analysis
    
    def _detect_in_chart(self, planets: Dict, chart_name: str) -> List[CurseDetection]:
        """在单个星盘中检测诅咒Yoga"""
        detected = []
        
        # 将行星按宫位分组
        house_planets = {}
        for pname, pdata in planets.items():
            if not isinstance(pdata, dict):
                continue
            house = pdata.get("house", 0)
            if house not in house_planets:
                house_planets[house] = []
            house_planets[house].append((pname, pdata))
        
        # 在每个宫位检查诅咒合相
        for house, plists in house_planets.items():
            if len(plists) < 2:
                continue
            
            planet_names = [p[0] for p in plists]
            sign = plists[0][1].get("sign", "")
            
            # 检查所有行星对
            for i, (p1, data1) in enumerate(plists):
                for p2, data2 in plists[i+1:]:
                    pair = tuple(sorted([p1, p2]))
                    
                    # 匹配诅咒定义
                    for curse_id, definition in self.definitions.items():
                        def_planets = definition["planets"]
                        if set(pair) == set(def_planets):
                            detection = self._create_detection(
                                curse_id, definition, pair, house, sign, chart_name
                            )
                            detected.append(detection)
        
        return detected
    
    def _create_detection(self, curse_id: str, definition: Dict,
                         planets: Tuple[str, ...], house: int,
                         sign: str, chart_name: str) -> CurseDetection:
        """创建单个检测结果"""
        severity = definition["severity"]
        severity_label = "critical" if severity >= 5 else "high" if severity >= 4 else "medium"
        
        # 如果在危险宫位，提高严重程度
        if house in definition.get("houses_critical", []):
            severity = min(severity + 1, 5)
            severity_label = "critical"
        
        # 确定受影响的人
        affected_person = ""
        for p in planets:
            if p in self.planet_person:
                affected_person = self.planet_person[p]
                break
        
        return CurseDetection(
            curse_type=curse_id,
            curse_name=definition["name"],
            curse_name_cn=definition["name_cn"],
            planets=list(planets),
            house=house,
            house_meaning=self.house_person.get(house, ""),
            sign=sign,
            severity=severity,
            severity_label=severity_label,
            affected_area=self.house_person.get(house, ""),
            affected_person=affected_person,
            body_parts=definition.get("body_parts", []),
            family_effect=definition.get("family_effect", ""),
            activation_triggers=definition.get("activation", []),
            current_dasha_relevant=False,
            transit_relevant=False,
            remedy=definition.get("remedy", ""),
            deity=definition.get("deity", ""),
            mantras=self._get_mantras(definition.get("deity", "")),
            narrative=f"[{chart_name}] 在{sign}第{house}宫发现 {definition['name']} ({definition['name_cn']})",
        )
    
    def _get_mantras(self, deity: str) -> List[str]:
        """获取对应神祇的咒语"""
        mantras = {
            "上师/Guru": ["Om Guruve Namah", "Guru Vandana"],
            "湿婆/Shiva": ["Om Namah Shivaya", "Mahamrityunjaya Mantra"],
            "杜尔迦/Durga": ["Om Dum Durgayei Namah", "Durga Saptashati"],
            "毗湿奴/Vishnu": ["Om Namo Bhagavate Vasudevaya", "Vishnu Sahasranama"],
        }
        return mantras.get(deity, ["Om Shanti Shanti Shanti"])
    
    def _assess_dasha_relevance(self, analysis: CurseAnalysis, current_dasha: str):
        """评估与当前Dasha的关联"""
        for curse in analysis.curses_detected:
            # 如果当前Dasha主星是诅咒行星之一
            if current_dasha in curse.planets:
                curse.current_dasha_relevant = True
    
    def _comprehensive_assessment(self, analysis: CurseAnalysis):
        """综合风险评估"""
        if not analysis.curses_detected:
            analysis.overall_risk = "low"
            analysis.risk_score = 0.0
            return
        
        # 计算风险分数
        max_severity = max(c.severity for c in analysis.curses_detected)
        count = len(analysis.curses_detected)
        dasha_active = sum(1 for c in analysis.curses_detected if c.current_dasha_relevant)
        
        score = (max_severity / 5.0) * 0.4 + (min(count / 3.0, 1.0)) * 0.3 + (dasha_active / max(count, 1)) * 0.3
        analysis.risk_score = min(score, 1.0)
        
        if analysis.risk_score >= 0.8:
            analysis.overall_risk = "critical"
        elif analysis.risk_score >= 0.6:
            analysis.overall_risk = "high"
        elif analysis.risk_score >= 0.3:
            analysis.overall_risk = "medium"
        else:
            analysis.overall_risk = "low"
    
    def _generate_remedies(self, analysis: CurseAnalysis):
        """生成补救建议"""
        # 收集所有涉及的神祇
        deities = set(c.deity for c in analysis.curses_detected)
        
        analysis.general_remedies = [
            "定期进行冥想和灵性练习",
            "保持Sattvic（纯善）的生活方式",
            "避免Tamas（惰性）的活动和食物",
            "佩戴适合的宝石（需咨询专业占星师）",
        ]
        
        for deity in deities:
            if "湿婆" in deity:
                analysis.general_remedies.append("每周一进行湿婆礼拜")
            elif "毗湿奴" in deity:
                analysis.general_remedies.append("每周三/六进行毗湿奴礼拜")
            elif "杜尔迦" in deity:
                analysis.general_remedies.append("每周二/五进行杜尔迦礼拜")
        
        analysis.lifestyle_advice = [
            "避免与有毒的人接触",
            "定期进行健康检查",
            "在危险Dasha周期特别注意安全",
            "保持规律的作息和饮食",
            "参与慈善和志愿服务",
        ]
    
    def _generate_narrative(self, analysis: CurseAnalysis) -> str:
        """生成叙事"""
        parts = []
        
        parts.append("### 凶星合相命名与危机预警\n")
        
        if not analysis.curses_detected:
            parts.append("✅ 未发现显著的凶星合相诅咒。\n")
            parts.append("您的星盘在凶星合相方面相对安全。\n")
            return "\n".join(parts)
        
        # 风险等级
        risk_labels = {
            "critical": "🔴 严重",
            "high": "🟠 高",
            "medium": "🟡 中等",
            "low": "🟢 低",
        }
        parts.append(f"\n**总体风险等级: {risk_labels.get(analysis.overall_risk, analysis.overall_risk)}** ({analysis.risk_score:.0%})\n")
        
        # 逐个列出
        for curse in analysis.curses_detected:
            parts.append(f"\n---\n")
            parts.append(f"#### {curse.curse_name} ({curse.curse_name_cn})\n")
            parts.append(f"**涉及行星**: {', '.join(curse.planets)}\n")
            parts.append(f"**位置**: {curse.sign} 第{curse.house}宫 ({curse.house_meaning})\n")
            parts.append(f"**严重程度**: {'⭐' * curse.severity}\n")
            parts.append(f"**含义**: {self.definitions.get(curse.curse_type, {}).get('meaning', '')}\n")
            
            if curse.current_dasha_relevant:
                parts.append(f"⚠️ **当前Dasha与此诅咒相关，需特别注意！**\n")
            
            if curse.affected_person:
                parts.append(f"**可能影响的人**: {curse.affected_person}\n")
            
            if curse.body_parts:
                parts.append(f"**相关身体部位**: {', '.join(curse.body_parts)}\n")
            
            if curse.family_effect:
                parts.append(f"**家族影响**: {curse.family_effect}\n")
            
            parts.append(f"**激活条件**: {'; '.join(curse.activation_triggers)}\n")
            parts.append(f"**补救措施**: {curse.remedy}\n")
            parts.append(f"**守护神祇**: {curse.deity}\n")
            if curse.mantras:
                parts.append(f"**推荐咒语**: {'; '.join(curse.mantras)}\n")
        
        # 综合建议
        if analysis.general_remedies:
            parts.append(f"\n#### 综合补救建议\n")
            for r in analysis.general_remedies:
                parts.append(f"- {r}\n")
        
        if analysis.lifestyle_advice:
            parts.append(f"\n#### 生活方式建议\n")
            for a in analysis.lifestyle_advice:
                parts.append(f"- {a}\n")
        
        return "\n".join(parts)
    
    def to_dict(self, analysis: CurseAnalysis) -> Dict:
        """转换为字典"""
        return {
            "curses_detected": [
                {
                    "type": c.curse_type,
                    "name": c.curse_name,
                    "name_cn": c.curse_name_cn,
                    "planets": c.planets,
                    "house": c.house,
                    "sign": c.sign,
                    "severity": c.severity,
                    "severity_label": c.severity_label,
                    "affected_area": c.affected_area,
                    "remedy": c.remedy,
                    "deity": c.deity,
                }
                for c in analysis.curses_detected
            ],
            "overall_risk": analysis.overall_risk,
            "risk_score": round(analysis.risk_score, 2),
            "general_remedies": analysis.general_remedies,
            "lifestyle_advice": analysis.lifestyle_advice,
            "narrative": analysis.narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def detect_curse_yogas(chart_data: Dict, current_dasha: Optional[str] = None) -> Dict:
    """便捷函数：检测凶星合相"""
    detector = CurseYogaDetector()
    analysis = detector.analyze(chart_data, current_dasha)
    return detector.to_dict(analysis)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    mock_chart = {
        "ascendant": {"sign": "Capricorn"},
        "planets": {
            "Mars": {"sign": "Aquarius", "house": 2, "degree": 320},
            "Saturn": {"sign": "Aquarius", "house": 2, "degree": 322},
            "Rahu": {"sign": "Scorpio", "house": 11, "degree": 230},
            "Ketu": {"sign": "Scorpio", "house": 11, "degree": 50},
        },
    }
    
    print("=" * 60)
    print("凶星合相命名与检测引擎")
    print("=" * 60)
    
    result = detect_curse_yogas(mock_chart, current_dasha="Saturn")
    print(result["narrative"])
    print(f"\n总体风险: {result['overall_risk']} ({result['risk_score']})")
