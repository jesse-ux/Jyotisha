#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rashi_tulya_navamsa.py — Rashi Tulya Navamsa (RTN) 映射引擎
===========================================================
将D9行星位置映射到D1，揭示隐藏的力量结构

来源: 《Dhruva Nadi》《Deva Keralam》
版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# RTN宫位名称
RTN_HOUSE_NAMES = {
    1: "Lagnamsa",       # 性格和本质
    2: "Dhanamsa",       # 财富和积累
    3: "Vikramsa",       # 勇气、努力和兄弟
    4: "Sukhamsa",       # 家庭幸福、母亲
    5: "Putramsa",       # 子女、智力
    6: "Ariamsa",        # 敌人、障碍、健康
    7: "Kalatramsa",     # 婚姻、配偶、合伙
    8: "Randhramsa",     # 突变、意外、转变
    9: "Bhagyamsa",      # 命运、宗教、好运
    10: "Karmamsa",      # 事业、成就、公共生活
    11: "Labhamsa",      # 收益、朋友、社交圈
    12: "Vyayamsa",      # 支出、隐秘、精神追求
}

# Gunas分类
GUNAS = {
    "Rajas": ["Venus", "Mercury"],           # 创造
    "Sattva": ["Jupiter", "Sun", "Moon"],    # 维持
    "Tamas": ["Saturn", "Mars", "Rahu", "Ketu"],  # 毁灭
}

# 凶星合相命名
CURSE_YOGAS = {
    ("Mars", "Saturn"): {
        "name": "Yama Yoga",
        "name_cn": "阎魔瑜伽",
        "meaning": "死亡之神 sitting，等待被激活。激活Dasha/Transit可触发危险疾病或事故。",
        "remedy": "需要上师保护，唱诵Guru Vandana",
        "severity": "critical",
    },
    ("Saturn", "Rahu"): {
        "name": "Preta Yoga",
        "name_cn": "亡灵瑜伽",
        "meaning": "过早死亡的风险，慢性疾病，可能来自祖先未解决的业力。",
        "remedy": "湿婆能量，唱诵湿婆咒语",
        "severity": "critical",
    },
    ("Saturn", "Ketu"): {
        "name": "Preta Yoga",
        "name_cn": "亡灵瑜伽",
        "meaning": "过早死亡的风险，慢性疾病，可能来自祖先未解决的业力。",
        "remedy": "湿婆能量，唱诵湿婆咒语",
        "severity": "critical",
    },
    ("Mars", "Rahu"): {
        "name": "Rakshasa Yoga",
        "name_cn": "恶魔瑜伽",
        "meaning": "暴力事件，粗俗或微妙的攻击，神经系统受损。",
        "remedy": "杜尔迦女神，唱诵Durga咒语",
        "severity": "high",
    },
    ("Mars", "Ketu"): {
        "name": "Pisacha Yoga",
        "name_cn": "鬼魅瑜伽",
        "meaning": "与有毒的人接触，被鬼魂困扰，天蝎座凶星激发。",
        "remedy": "毗湿奴，唱诵Vishnu咒语",
        "severity": "high",
    },
}


@dataclass
class RTNPlanet:
    """RTN中的行星"""
    planet: str
    d9_sign: str
    d9_house: int
    d1_sign: str           # 映射到D1的星座
    d1_house: int          # 映射到D1的宫位
    rtn_house_name: str    # RTN宫位名称
    dignity_d9: str        # D9中的庙旺状态
    dignity_d1: str        # D1中的庙旺状态
    
    # 与D1行星的合相
    d1_conjunctions: List[str] = field(default_factory=list)
    d1_aspects: List[str] = field(default_factory=list)
    
    # Gunas
    guna: str = ""
    
    # 解读
    narrative: str = ""


@dataclass
class RTNAnalysis:
    """RTN分析结果"""
    # 基础信息
    lagna_sign: str
    planets: List[RTNPlanet] = field(default_factory=list)
    
    # 宫位映射
    house_mapping: Dict[int, List[str]] = field(default_factory=dict)
    
    # 关键发现
    exalted_cancelled: List[str] = field(default_factory=list)   # 耀升被取消
    debilitated_cancelled: List[str] = field(default_factory=list)  # 落陷被取消
    
    # 凶星合相
    curse_yogas: List[Dict] = field(default_factory=list)
    
    # Gunas分析
    guna_balance: Dict[str, int] = field(default_factory=dict)
    guna_narrative: str = ""
    
    # 综合评估
    strength_score: float = 0.5
    weakness_score: float = 0.5
    
    # 叙事
    full_narrative: str = ""


class RashiTulyaNavamsa:
    """RTN映射引擎"""
    
    def __init__(self):
        self.house_names = RTN_HOUSE_NAMES
        self.gunas = GUNAS
        self.curse_yogas = CURSE_YOGAS
    
    def analyze(self, chart_data: Dict) -> RTNAnalysis:
        """
        执行RTN分析
        
        Args:
            chart_data: 标准星盘数据（含context.navamsa_planets）
        
        Returns:
            RTNAnalysis对象
        """
        # Step 1: 获取D9行星位置
        d9_planets = self._get_d9_planets(chart_data)
        
        # Step 2: 获取D1信息
        d1_planets = chart_data.get("planets", {})
        asc_sign = chart_data.get("ascendant", {}).get("sign", "Aries")
        asc_house = 1  # 上升永远在第1宫
        
        # Step 3: 创建RTN分析对象
        analysis = RTNAnalysis(lagna_sign=asc_sign)
        
        # Step 4: 映射每个D9行星到D1
        for planet_name, d9_data in d9_planets.items():
            if planet_name in ["Ascendant", "Lagna"]:
                continue
            
            rtn_planet = self._map_planet(
                planet_name, d9_data, d1_planets, asc_sign
            )
            analysis.planets.append(rtn_planet)
            
            # 记录宫位映射
            house = rtn_planet.d1_house
            if house not in analysis.house_mapping:
                analysis.house_mapping[house] = []
            analysis.house_mapping[house].append(planet_name)
        
        # Step 5: 检测耀升/落陷取消
        self._check_dignity_cancellation(analysis)
        
        # Step 6: 检测凶星合相
        self._detect_curse_yogas(analysis)
        
        # Step 7: Gunas分析
        self._analyze_gunas(analysis)
        
        # Step 8: 综合评估
        self._comprehensive_assessment(analysis)
        
        # Step 9: 生成叙事
        analysis.full_narrative = self._generate_narrative(analysis)
        
        return analysis
    
    def _get_d9_planets(self, chart_data: Dict) -> Dict:
        """从chart_data中提取D9行星位置"""
        context = chart_data.get("context", {})
        
        # 优先从context获取
        if "navamsa_planets" in context:
            return context["navamsa_planets"]
        
        # 否则尝试从varga计算
        # 简化：返回空
        return {}
    
    def _map_planet(self, planet_name: str, d9_data: Dict,
                    d1_planets: Dict, asc_sign: str) -> RTNPlanet:
        """将单个D9行星映射到D1"""
        d9_sign = d9_data.get("sign", "")
        d9_house = d9_data.get("house", 0)
        
        # 在D1中找到相同的星座
        d1_sign = d9_sign
        d1_house = self._sign_to_house(d9_sign, asc_sign)
        
        # RTN宫位名称
        rtn_name = self.house_names.get(d1_house, f"House_{d1_house}")
        
        # 检测D1中的庙旺状态
        d1_dignity = self._check_dignity_in_chart(planet_name, d9_sign, d1_planets)
        d9_dignity = d9_data.get("dignity", "")
        
        # 检测与D1行星的合相
        d1_conjs = self._find_d1_conjunctions(planet_name, d1_sign, d1_planets)
        
        # Gunas
        guna = self._get_guna(planet_name)
        
        return RTNPlanet(
            planet=planet_name,
            d9_sign=d9_sign,
            d9_house=d9_house,
            d1_sign=d1_sign,
            d1_house=d1_house,
            rtn_house_name=rtn_name,
            dignity_d9=d9_dignity,
            dignity_d1=d1_dignity,
            d1_conjunctions=d1_conjs,
            guna=guna,
        )
    
    def _sign_to_house(self, sign: str, asc_sign: str) -> int:
        """根据上升星座计算某星座是第几宫"""
        SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        try:
            asc_idx = SIGNS.index(asc_sign)
            sign_idx = SIGNS.index(sign)
            house = ((sign_idx - asc_idx) % 12) + 1
            return house
        except ValueError:
            return 1
    
    def _check_dignity_in_chart(self, planet: str, sign: str, 
                                 d1_planets: Dict) -> str:
        """检查行星在某星座的庙旺状态"""
        # 简化实现
        EXALTATION = {
            "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
            "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
            "Saturn": "Libra",
        }
        DEBILITATION = {
            "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
            "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
            "Saturn": "Aries",
        }
        OWN_SIGN = {
            "Sun": "Leo", "Moon": "Cancer", "Mars": ["Aries", "Scorpio"],
            "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
            "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
        }
        
        if EXALTATION.get(planet) == sign:
            return "exalted"
        elif DEBILITATION.get(planet) == sign:
            return "debilitated"
        elif sign in (OWN_SIGN.get(planet) or []):
            return "own"
        return "neutral"
    
    def _find_d1_conjunctions(self, planet_name: str, sign: str,
                               d1_planets: Dict) -> List[str]:
        """找到D1中同星座的其他行星"""
        conjs = []
        for pname, pdata in d1_planets.items():
            if pname == planet_name:
                continue
            if isinstance(pdata, dict) and pdata.get("sign") == sign:
                conjs.append(pname)
        return conjs
    
    def _get_guna(self, planet: str) -> str:
        """获取行星的Gunas"""
        for guna, planets in self.gunas.items():
            if planet in planets:
                return guna
        return "Tamas"  # Rahu/Ketu默认Tamas
    
    def _check_dignity_cancellation(self, analysis: RTNAnalysis):
        """检测耀升/落陷取消"""
        for p in analysis.planets:
            # 如果在D1中耀升但D9映射后落在凶星星座/宫位
            if p.dignity_d1 == "exalted" and p.d1_conjunctions:
                malefics = ["Saturn", "Mars", "Rahu", "Ketu"]
                if any(m in p.d1_conjunctions for m in malefics):
                    analysis.exalted_cancelled.append(p.planet)
            
            # 如果在D1中落陷但D9映射后与吉星合相
            if p.dignity_d1 == "debilitated" and p.d1_conjunctions:
                benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
                if any(b in p.d1_conjunctions for b in benefics):
                    analysis.debilitated_cancelled.append(p.planet)
    
    def _detect_curse_yogas(self, analysis: RTNAnalysis):
        """检测凶星合相命名"""
        # 按宫位检查
        for house, planets in analysis.house_mapping.items():
            if len(planets) < 2:
                continue
            
            # 检查所有行星对
            for i, p1 in enumerate(planets):
                for p2 in planets[i+1:]:
                    # 标准化顺序
                    pair = tuple(sorted([p1, p2]))
                    
                    if pair in self.curse_yogas:
                        curse = self.curse_yogas[pair].copy()
                        curse["house"] = house
                        curse["house_name"] = self.house_names.get(house, "")
                        curse["planets"] = list(pair)
                        analysis.curse_yogas.append(curse)
    
    def _analyze_gunas(self, analysis: RTNAnalysis):
        """分析Gunas平衡"""
        counts = {"Rajas": 0, "Sattva": 0, "Tamas": 0}
        
        for p in analysis.planets:
            if p.guna in counts:
                counts[p.guna] += 1
        
        analysis.guna_balance = counts
        
        # 生成叙事
        total = sum(counts.values())
        if total == 0:
            return
        
        dominant = max(counts, key=counts.get)
        ratio = counts[dominant] / total
        
        if ratio > 0.5:
            if dominant == "Sattva":
                analysis.guna_narrative = "Gunas以Sattva（纯善）为主导，吉星力量较强，灵性倾向明显。"
            elif dominant == "Rajas":
                analysis.guna_narrative = "Gunas以Rajas（活动）为主导，创造性能量活跃，追求成就。"
            else:
                analysis.guna_narrative = "Gunas以Tamas（惯性）为主导，毁灭力量较强，需要特别注意凶星影响。"
        else:
            analysis.guna_narrative = "Gunas相对平衡，三种力量相互制衡。"
    
    def _comprehensive_assessment(self, analysis: RTNAnalysis):
        """综合评估"""
        # 计算力量得分
        strength = 0
        weakness = 0
        
        for p in analysis.planets:
            if p.dignity_d1 in ["exalted", "own"]:
                strength += 1
            elif p.dignity_d1 == "debilitated":
                weakness += 1
            
            # 凶星合相增加弱点
            if p.planet in ["Saturn", "Mars", "Rahu", "Ketu"] and p.d1_conjunctions:
                weakness += 0.5
        
        total = len(analysis.planets) or 1
        analysis.strength_score = min(strength / total, 1.0)
        analysis.weakness_score = min(weakness / total, 1.0)
    
    def _generate_narrative(self, analysis: RTNAnalysis) -> str:
        """生成RTN解读叙事"""
        parts = []
        
        parts.append("### Rashi Tulya Navamsa (RTN) 深度分析\n")
        parts.append("将Navamsa (D9) 行星映射到本命盘 (D1)，揭示隐藏的力量结构。\n")
        
        # 宫位映射概览
        parts.append("\n#### RTN宫位映射概览\n")
        for house in sorted(analysis.house_mapping.keys()):
            planets = analysis.house_mapping[house]
            name = self.house_names.get(house, "")
            parts.append(f"**{name}** (第{house}宫): {', '.join(planets)}\n")
        
        # 关键发现
        if analysis.exalted_cancelled:
            parts.append(f"\n⚠️ **耀升被取消**: {', '.join(analysis.exalted_cancelled)}")
            parts.append("这些行星表面强大但根基不稳，效果被削弱。\n")
        
        if analysis.debilitated_cancelled:
            parts.append(f"\n✨ **落陷被取消**: {', '.join(analysis.debilitated_cancelled)}")
            parts.append("这些行星表面弱势但有隐藏支持，效果被增强。\n")
        
        # 凶星合相
        if analysis.curse_yogas:
            parts.append("\n#### 凶星合相警示\n")
            for curse in analysis.curse_yogas:
                parts.append(f"\n🔥 **{curse['name']} ({curse['name_cn']})**")
                parts.append(f"   行星: {', '.join(curse['planets'])}")
                parts.append(f"   宫位: 第{curse['house']}宫 ({curse['house_name']})")
                parts.append(f"   含义: {curse['meaning']}")
                parts.append(f"   补救: {curse['remedy']}\n")
        
        # Gunas
        if analysis.guna_narrative:
            parts.append(f"\n#### Gunas能量分析\n")
            parts.append(f"{analysis.guna_narrative}\n")
            parts.append(f"Rajas: {analysis.guna_balance.get('Rajas', 0)} | ")
            parts.append(f"Sattva: {analysis.guna_balance.get('Sattva', 0)} | ")
            parts.append(f"Tamas: {analysis.guna_balance.get('Tamas', 0)}\n")
        
        # 综合评估
        parts.append(f"\n#### 综合评估\n")
        parts.append(f"力量指数: {analysis.strength_score:.0%}\n")
        parts.append(f"弱点指数: {analysis.weakness_score:.0%}\n")
        
        if analysis.strength_score > analysis.weakness_score:
            parts.append("\n总体评估：吉星力量占优，积极因素可以克服挑战。\n")
        else:
            parts.append("\n总体评估：凶星影响较强，需要特别注意相关领域。\n")
        
        return "\n".join(parts)
    
    def to_dict(self, analysis: RTNAnalysis) -> Dict:
        """转换为字典"""
        return {
            "lagna_sign": analysis.lagna_sign,
            "planets": [
                {
                    "planet": p.planet,
                    "d9_sign": p.d9_sign,
                    "d1_house": p.d1_house,
                    "rtn_house_name": p.rtn_house_name,
                    "dignity_d9": p.dignity_d9,
                    "dignity_d1": p.dignity_d1,
                    "d1_conjunctions": p.d1_conjunctions,
                    "guna": p.guna,
                }
                for p in analysis.planets
            ],
            "house_mapping": analysis.house_mapping,
            "exalted_cancelled": analysis.exalted_cancelled,
            "debilitated_cancelled": analysis.debilitated_cancelled,
            "curse_yogas": analysis.curse_yogas,
            "guna_balance": analysis.guna_balance,
            "guna_narrative": analysis.guna_narrative,
            "strength_score": round(analysis.strength_score, 2),
            "weakness_score": round(analysis.weakness_score, 2),
            "narrative": analysis.full_narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_rtn(chart_data: Dict) -> Dict:
    """便捷函数：RTN分析"""
    engine = RashiTulyaNavamsa()
    analysis = engine.analyze(chart_data)
    return engine.to_dict(analysis)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    mock_chart = {
        "ascendant": {"sign": "Capricorn"},
        "planets": {
            "Moon": {"sign": "Aquarius", "house": 2},
            "Saturn": {"sign": "Aquarius", "house": 2},
            "Mars": {"sign": "Aquarius", "house": 2},
            "Rahu": {"sign": "Aquarius", "house": 2},
            "Jupiter": {"sign": "Leo", "house": 8},
        },
        "context": {
            "navamsa_planets": {
                "Moon": {"sign": "Scorpio", "house": 10, "dignity": "debilitated"},
                "Saturn": {"sign": "Scorpio", "house": 10, "dignity": "neutral"},
                "Mars": {"sign": "Scorpio", "house": 10, "dignity": "own"},
                "Rahu": {"sign": "Scorpio", "house": 10, "dignity": "neutral"},
                "Jupiter": {"sign": "Cancer", "house": 7, "dignity": "exalted"},
            }
        }
    }
    
    print("=" * 60)
    print("Rashi Tulya Navamsa (RTN) 映射引擎")
    print("=" * 60)
    
    result = analyze_rtn(mock_chart)
    print(result["narrative"])
