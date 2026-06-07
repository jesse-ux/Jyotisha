#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spouse_status_yoga.py — 高地位配偶与婚后成长Yoga检测引擎
==========================================================
检测配偶社会地位高于命主、婚后命运积极转变的占星组合

来源: 文章7 + 传统BPHS/BVR技法
版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# 上升星座对应的7宫星座
HOUSE7_SIGNS = {
    "Aries": "Libra", "Taurus": "Scorpio", "Gemini": "Sagittarius",
    "Cancer": "Capricorn", "Leo": "Aquarius", "Virgo": "Pisces",
    "Libra": "Aries", "Scorpio": "Taurus", "Sagittarius": "Gemini",
    "Capricorn": "Cancer", "Aquarius": "Leo", "Pisces": "Virgo",
}

# 星座守护星
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Upachaya宫（成长宫）— 从任何宫位起算的3/6/10/11
UPACHAYA_OFFSETS = [2, 5, 9, 10]  # 从当前宫起算的偏移（3=+2, 6=+5, 10=+9, 11=+10）


@dataclass
class SpouseStatusIndicator:
    """单个指标"""
    indicator_type: str              # 指标类型
    description: str                  # 描述
    present: bool                     # 是否存在
    strength: float                   # 强度 0-1
    evidence: List[str] = field(default_factory=list)


@dataclass
class SpouseStatusAnalysis:
    """高地位配偶分析结果"""
    # 四大核心原则
    principle1: SpouseStatusIndicator  # 7宫强于Lagna
    principle2: SpouseStatusIndicator  # D9中7主星有Rajyoga
    principle3: SpouseStatusIndicator  # 7主星在Upachaya
    principle4: SpouseStatusIndicator  # 从7宫起算的Upachaya被占据
    
    # 综合评估
    overall_score: float = 0.0         # 0-1
    verdict: str = ""                   # 结论
    spouse_status: str = ""             # 配偶地位评估
    post_marriage_growth: str = ""      # 婚后成长评估
    
    # 详细发现
    all_indicators: List[SpouseStatusIndicator] = field(default_factory=list)
    
    # 案例参考
    case_study: str = ""
    
    # 叙事
    narrative: str = ""


class SpouseStatusYogaDetector:
    """高地位配偶Yoga检测引擎"""
    
    def __init__(self):
        self.sign_lords = SIGN_LORDS
        self.house7_signs = HOUSE7_SIGNS
    
    def analyze(self, chart_data: Dict, d9_data: Optional[Dict] = None) -> SpouseStatusAnalysis:
        """
        分析高地位配偶Yoga
        
        Args:
            chart_data: D1星盘数据
            d9_data: D9星盘数据（可选）
        
        Returns:
            SpouseStatusAnalysis对象
        """
        planets = chart_data.get("planets", {})
        asc_sign = chart_data.get("ascendant", {}).get("sign", "")
        
        # Step 1: 原则1 — 7宫 vs Lagna力量比较
        p1 = self._check_principle1(planets, asc_sign)
        
        # Step 2: 原则2 — D9中7主星Rajyoga
        p2 = self._check_principle2(d9_data, asc_sign)
        
        # Step 3: 原则3 — 7主星在Upachaya
        p3 = self._check_principle3(planets, asc_sign)
        
        # Step 4: 原则4 — 从7宫起算的Upachaya被占据
        p4 = self._check_principle4(planets, asc_sign)
        
        # 创建分析对象
        analysis = SpouseStatusAnalysis(
            principle1=p1,
            principle2=p2,
            principle3=p3,
            principle4=p4,
        )
        
        analysis.all_indicators = [p1, p2, p3, p4]
        
        # Step 5: 综合评估
        self._comprehensive_assessment(analysis)
        
        # Step 6: 生成叙事
        analysis.narrative = self._generate_narrative(analysis, asc_sign)
        
        return analysis
    
    def _check_principle1(self, planets: Dict, asc_sign: str) -> SpouseStatusIndicator:
        """
        原则1: 7宫和7主星必须比Lagna和Lagna主星更强
        """
        indicator = SpouseStatusIndicator(
            indicator_type="principle1",
            description="7宫和7主星强于Lagna和Lagna主星",
            present=False,
            strength=0.0,
        )
        
        # 获取Lagna主星
        lagna_lord = self.sign_lords.get(asc_sign, "")
        lagna_lord_data = planets.get(lagna_lord, {})
        
        # 获取7宫星座和主星
        house7_sign = self.house7_signs.get(asc_sign, "")
        house7_lord = self.sign_lords.get(house7_sign, "")
        house7_lord_data = planets.get(house7_lord, {})
        
        if not isinstance(lagna_lord_data, dict) or not isinstance(house7_lord_data, dict):
            indicator.evidence.append("缺少行星数据")
            return indicator
        
        # 比较力量（简化：比较庙旺状态）
        lagna_dignity = lagna_lord_data.get("dignity", "")
        house7_dignity = house7_lord_data.get("dignity", "")
        
        dignity_scores = {
            "exalted": 4, "own": 3, "friendly": 2,
            "neutral": 1, "enemy": 0, "debilitated": -1,
        }
        
        lagna_score = dignity_scores.get(lagna_dignity, 0)
        house7_score = dignity_scores.get(house7_dignity, 0)
        
        # 7主星位置
        house7_lord_house = house7_lord_data.get("house", 0)
        
        # 如果7主星在角宫或三方宫，增强力量
        if house7_lord_house in [1, 4, 7, 10, 5, 9]:
            house7_score += 1
        
        # 如果7主星受Yogakaraka相位
        # 简化：检查是否有吉星相位
        # ...
        
        indicator.present = house7_score > lagna_score
        indicator.strength = min(max((house7_score - lagna_score + 2) / 6, 0), 1)
        
        if indicator.present:
            indicator.evidence.append(f"7主星{house7_lord}力量({house7_score}) > Lagna主星{lagna_lord}力量({lagna_score})")
            if house7_dignity in ["exalted", "own"]:
                indicator.evidence.append(f"7主星处于{house7_dignity}状态")
        else:
            indicator.evidence.append(f"7主星力量({house7_score}) 未超过 Lagna主星({lagna_score})")
        
        return indicator
    
    def _check_principle2(self, d9_data: Optional[Dict], asc_sign: str) -> SpouseStatusIndicator:
        """
        原则2: D9中7主星存在Rajyoga
        """
        indicator = SpouseStatusIndicator(
            indicator_type="principle2",
            description="Navamsa (D9) 中7主星存在Rajyoga",
            present=False,
            strength=0.0,
        )
        
        if not d9_data:
            indicator.evidence.append("缺少D9数据")
            return indicator
        
        d9_planets = d9_data.get("planets", {})
        d9_asc = d9_data.get("ascendant", {}).get("sign", asc_sign)
        
        # D9的7宫
        d9_house7_sign = self.house7_signs.get(d9_asc, "")
        d9_house7_lord = self.sign_lords.get(d9_house7_sign, "")
        d9_7lord_data = d9_planets.get(d9_house7_lord, {})
        
        if not isinstance(d9_7lord_data, dict):
            indicator.evidence.append("D9中7主星数据缺失")
            return indicator
        
        # 简化Rajyoga检测：检查7主星是否在Kendra/Kona
        d9_7lord_house = d9_7lord_data.get("house", 0)
        
        if d9_7lord_house in [1, 4, 7, 10, 5, 9]:
            indicator.present = True
            indicator.strength = 0.7
            indicator.evidence.append(f"D9中7主星{d9_house7_lord}位于{d9_7lord_house}宫（角宫/三方宫）")
        
        # 检查是否有吉星合相或相位
        # ...
        
        return indicator
    
    def _check_principle3(self, planets: Dict, asc_sign: str) -> SpouseStatusIndicator:
        """
        原则3: 7主星位于Upachaya宫（成长宫）
        """
        indicator = SpouseStatusIndicator(
            indicator_type="principle3",
            description="7主星位于Upachaya宫（成长宫）",
            present=False,
            strength=0.0,
        )
        
        house7_sign = self.house7_signs.get(asc_sign, "")
        house7_lord = self.sign_lords.get(house7_sign, "")
        house7_lord_data = planets.get(house7_lord, {})
        
        if not isinstance(house7_lord_data, dict):
            return indicator
        
        lord_house = house7_lord_data.get("house", 0)
        
        # Upachaya宫: 3, 6, 10, 11
        if lord_house in [3, 6, 10, 11]:
            indicator.present = True
            indicator.strength = 0.8
            indicator.evidence.append(f"7主星{house7_lord}位于Upachaya宫第{lord_house}宫")
        else:
            indicator.evidence.append(f"7主星位于第{lord_house}宫，非Upachaya宫")
        
        return indicator
    
    def _check_principle4(self, planets: Dict, asc_sign: str) -> SpouseStatusIndicator:
        """
        原则4: 从7宫起算的Upachaya宫被行星占据
        """
        indicator = SpouseStatusIndicator(
            indicator_type="principle4",
            description="从7宫起算的Upachaya宫被行星占据",
            present=False,
            strength=0.0,
        )
        
        # 从7宫起算的Upachaya: 7+2=9, 7+5=12, 7+9=16->4, 7+10=17->5
        # 即: 从7宫起算的3宫=9宫, 6宫=12宫, 10宫=4宫, 11宫=5宫
        # 等等，Upachaya是3/6/10/11，从7宫起算:
        # 3rd from 7 = 9th house
        # 6th from 7 = 12th house  
        # 10th from 7 = 4th house
        # 11th from 7 = 5th house
        upachaya_from_7 = [9, 12, 4, 5]
        
        occupied_count = 0
        total_strength = 0
        
        for house in upachaya_from_7:
            # 找到在这个宫位的行星
            house_planets = []
            for pname, pdata in planets.items():
                if isinstance(pdata, dict) and pdata.get("house") == house:
                    house_planets.append(pname)
            
            if house_planets:
                occupied_count += 1
                # 评估占据行星的力量
                for p in house_planets:
                    pdata = planets.get(p, {})
                    if isinstance(pdata, dict):
                        dignity = pdata.get("dignity", "")
                        if dignity in ["exalted", "own"]:
                            total_strength += 0.3
                        elif dignity in ["friendly"]:
                            total_strength += 0.2
                        else:
                            total_strength += 0.1
                        
                        indicator.evidence.append(f"第{house}宫被{p}占据 ({dignity})")
        
        if occupied_count > 0:
            indicator.present = True
            indicator.strength = min(total_strength + occupied_count * 0.15, 1.0)
        
        return indicator
    
    def _comprehensive_assessment(self, analysis: SpouseStatusAnalysis):
        """综合评估"""
        # 计算总分
        total_strength = sum(i.strength for i in analysis.all_indicators if i.present)
        present_count = sum(1 for i in analysis.all_indicators if i.present)
        
        analysis.overall_score = min(total_strength / 2, 1.0)  # 归一化
        
        # 结论
        if present_count >= 3:
            analysis.verdict = "极强的『嫁给高地位配偶』Yoga"
            analysis.spouse_status = "配偶社会地位显著高于命主"
            analysis.post_marriage_growth = "婚后命运将发生巨大跃迁，获得权力和地位"
        elif present_count == 2:
            analysis.verdict = "较强的婚后提升潜力"
            analysis.spouse_status = "配偶有一定社会地位或增长潜力"
            analysis.post_marriage_growth = "婚后有显著成长和进步"
        elif present_count == 1:
            analysis.verdict = "有婚后成长的迹象"
            analysis.spouse_status = "配偶背景尚可"
            analysis.post_marriage_growth = "婚后有一定改善"
        else:
            analysis.verdict = "无明显高地位配偶Yoga"
            analysis.spouse_status = "配偶背景与命主相当"
            analysis.post_marriage_growth = "婚后变化不显著"
        
        # 案例
        analysis.case_study = "索尼娅·甘地案例：巨蟹座上升，土星7主受Yogakaraka火星相位，形成Rajyoga。婚后从普通意大利女性跃升为印度最有权势的女性之一。"
    
    def _generate_narrative(self, analysis: SpouseStatusAnalysis, asc_sign: str) -> str:
        """生成叙事"""
        parts = []
        
        parts.append("### 高地位配偶与婚后命运转变分析\n")
        parts.append(f"基于四大核心原则的综合评估。\n")
        
        # 四大原则
        parts.append("\n#### 四大核心原则检测\n")
        for i, ind in enumerate(analysis.all_indicators, 1):
            status = "✅" if ind.present else "❌"
            parts.append(f"{status} **原则{i}**: {ind.description}")
            if ind.evidence:
                parts.append(f"   证据: {'; '.join(ind.evidence[:2])}")
            parts.append("")
        
        # 结论
        parts.append(f"\n#### 综合结论\n")
        parts.append(f"**{analysis.verdict}**\n")
        parts.append(f"\n配偶地位评估: {analysis.spouse_status}\n")
        parts.append(f"婚后成长评估: {analysis.post_marriage_growth}\n")
        parts.append(f"综合得分: {analysis.overall_score:.0%}\n")
        
        # 案例
        if analysis.case_study:
            parts.append(f"\n#### 参考案例\n")
            parts.append(f"{analysis.case_study}\n")
        
        # 注意事项
        parts.append(f"\n#### 重要提醒\n")
        parts.append("- 第七宫强大仅代表配偶出生背景好，不代表对方个人能力出众\n")
        parts.append("- 宫主星代表后天潜质和个人能力\n")
        parts.append("- 对方家庭好不代表夫妻关系顺利或你能获得幸福\n")
        parts.append("- 以上方法仅用于查看婚姻中物质繁荣的情况\n")
        
        return "\n".join(parts)
    
    def to_dict(self, analysis: SpouseStatusAnalysis) -> Dict:
        """转换为字典"""
        return {
            "principles": [
                {
                    "type": i.indicator_type,
                    "description": i.description,
                    "present": i.present,
                    "strength": round(i.strength, 2),
                    "evidence": i.evidence,
                }
                for i in analysis.all_indicators
            ],
            "overall_score": round(analysis.overall_score, 2),
            "verdict": analysis.verdict,
            "spouse_status": analysis.spouse_status,
            "post_marriage_growth": analysis.post_marriage_growth,
            "case_study": analysis.case_study,
            "narrative": analysis.narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_spouse_status(chart_data: Dict, d9_data: Optional[Dict] = None) -> Dict:
    """便捷函数"""
    detector = SpouseStatusYogaDetector()
    analysis = detector.analyze(chart_data, d9_data)
    return detector.to_dict(analysis)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    # 索尼娅·甘地模拟数据（简化）
    mock_chart = {
        "ascendant": {"sign": "Cancer"},
        "planets": {
            "Moon": {"sign": "Cancer", "house": 1, "dignity": "own"},  # Lagna主星
            "Saturn": {"sign": "Capricorn", "house": 7, "dignity": "own"},  # 7主星
            "Mars": {"sign": "Sagittarius", "house": 6, "dignity": "friendly"},  # Yogakaraka
        },
    }
    
    mock_d9 = {
        "ascendant": {"sign": "Aquarius"},
        "planets": {
            "Sun": {"sign": "Aquarius", "house": 1, "dignity": "neutral"},
            "Saturn": {"sign": "Scorpio", "house": 10, "dignity": "neutral"},
        },
    }
    
    print("=" * 60)
    print("高地位配偶与婚后成长Yoga检测")
    print("=" * 60)
    
    result = analyze_spouse_status(mock_chart, mock_d9)
    print(result["narrative"])
    print(f"\n综合得分: {result['overall_score']}")
