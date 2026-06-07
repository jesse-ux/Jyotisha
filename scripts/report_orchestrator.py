#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jyotish Thematic Report Orchestrator
=====================================
主题化解盘编排器 —— 将多种印度占星技法整合为主题化叙事报告。

架构设计：
- 主题定义层 (Theme Definitions)：5 大人生主题的技法映射
- 交叉验证引擎 (Cross-Validation Engine)：多源证据聚合与矛盾裁决
- 叙事生成器 (Narrative Generator)：将技法结论转译为连贯段落
- 时间锚定器 (Timing Anchor)：将静态格局与动态 Dasha 周期关联

作者：Architect
日期：2026-06-07
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 核心枚举与常量
# ═══════════════════════════════════════════════════════════════

class StrengthLevel(str, Enum):
    """结论强度分级"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class ThemeName(str, Enum):
    """五大分析主题"""
    MARRIAGE = "marriage"
    CAREER = "career"
    WEALTH = "wealth"
    HEALTH = "health"
    SPIRITUALITY = "spirituality"


# 经典矛盾裁决优先级：D9 > D1（婚姻），D10 > D1（事业），D30 > D1（健康）
# 数值越大优先级越高
CHART_PRIORITY = {
    "D1": 1,
    "D2": 2,
    "D7": 3,
    "D9": 5,    # 婚姻分盘最高优先级
    "D10": 5,   # 事业分盘最高优先级
    "D20": 4,
    "D30": 5,   # 健康分盘最高优先级
    "D60": 4,
    "Rashi": 1,
    "Navamsa": 5,
    "Dashamsha": 5,
    "Trimsamsa": 5,
}


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class TechniqueResult:
    """单一技法分析结果"""
    technique: str              # 技法名称，如 "D1-7th-house", "Venus-strength"
    chart: str                  # 所属分盘，如 "D1", "D9", "D10"
    conclusion: str             # 结论描述
    sentiment: str              # 情感倾向: "positive" | "negative" | "neutral"
    strength: StrengthLevel     # 该技法本身的证据强度
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictResolution:
    """矛盾裁决记录"""
    technique_a: str
    conclusion_a: str
    technique_b: str
    conclusion_b: str
    resolution: str             # 裁决结果
    reasoning: str              # 裁决依据
    winner: str                 # 采纳哪方结论


@dataclass
class TimingAnchor:
    """时间锚定信息"""
    dasha_period: str           # 如 "Jupiter-Mercury"
    start_year: int
    end_year: int
    activation_description: str # 激活描述
    is_current: bool = False


@dataclass
class ThemeReport:
    """单一主题完整报告"""
    theme: ThemeName
    summary: str                # 一句话总结
    narrative: str              # 详细叙事段落
    evidence: List[Dict[str, Any]]
    strength: StrengthLevel
    timing: Optional[TimingAnchor]
    conflicts: List[ConflictResolution]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["theme"] = self.theme.value
        d["strength"] = self.strength.value
        return d

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)


@dataclass
class BirthChartData:
    """模拟本命盘数据结构（实际项目应由排盘引擎提供）"""
    d1_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d9_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d10_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d2_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d20_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d30_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    d60_houses: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    planets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_dasha: str = ""
    dasha_timeline: List[Dict[str, Any]] = field(default_factory=list)
    yogas: List[Dict[str, Any]] = field(default_factory=list)
    ashtakavarga: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# 主题定义与技法映射
# ═══════════════════════════════════════════════════════════════

THEME_TECHNIQUE_MAP: Dict[ThemeName, Dict[str, Any]] = {
    ThemeName.MARRIAGE: {
        "name_zh": "婚姻",
        "techniques": [
            ("D1-7th-house", "D1", "第7宫主星及宫内星分析"),
            ("D9-lagna", "D9", "Navamsa 上升及主星状态"),
            ("DK-position", "D1", "Dara Karaka 所在宫位与星座"),
            ("Upapada-lagna", "D1", "Upapada Lagna 及主星"),
            ("RTN-analysis", "D1", "Navamsa Tulya Rashi 分析"),
            ("Venus-strength", "D1", "Venus 庙旺落陷及相位"),
            ("Tithi-lord", "D1", "出生 Tithi 主星状态"),
        ],
        "primary_chart": "D9",
        "conflict_rule": "婚姻议题以 D9 (Navamsa) 为最终裁决依据",
    },
    ThemeName.CAREER: {
        "name_zh": "事业",
        "techniques": [
            ("D1-10th-house", "D1", "第10宫主星、宫内星及相位"),
            ("D10-lagna", "D10", "Dashamsha 上升及主星"),
            ("Karaka-position", "D1", "Amatyakaraka 所在宫位"),
            ("Amatyakaraka-dignity", "D1", "Amatyakaraka 庙旺状态"),
            ("Dasha-career-link", "Dasha", "大运与10宫主关联"),
            ("Raja-Yoga-10th", "D1", "10宫相关 Raja Yoga"),
        ],
        "primary_chart": "D10",
        "conflict_rule": "事业议题以 D10 (Dashamsha) 为最终裁决依据",
    },
    ThemeName.WEALTH: {
        "name_zh": "财富",
        "techniques": [
            ("D2-analysis", "D2", "Hora 分盘日月属性分布"),
            ("Dhana-Yoga", "D1", "Dhana Yoga 组合识别"),
            ("2nd-lord", "D1", "第2宫主星状态"),
            ("11th-lord", "D1", "第11宫主星状态"),
            ("Ashtakavarga-wealth", "AV", "2/11宫 Ashtakavarga 分值"),
            ("Lakshmi-Yoga", "D1", "Lakshmi Yoga 检测"),
        ],
        "primary_chart": "D2",
        "conflict_rule": "财富议题综合 D2 与 Ashtakavarga，Dhana Yoga 为辅助验证",
    },
    ThemeName.HEALTH: {
        "name_zh": "健康",
        "techniques": [
            ("D1-6th-house", "D1", "第6宫疾病宫位分析"),
            ("D1-8th-house", "D1", "第8宫长寿/意外宫位"),
            ("D1-12th-house", "D1", "第12宫住院/虚弱宫位"),
            ("D30-analysis", "D30", "Trimsamsa 健康分盘"),
            ("Arista-Yoga", "D1", "Arista Yoga 凶星组合"),
            ("Malefic-conjunction", "D1", "凶星合相第1宫或日月"),
            ("Saturn-Mars", "D1", "Saturn-Mars 合相/对冲"),
        ],
        "primary_chart": "D30",
        "conflict_rule": "健康议题以 D30 (Trimsamsa) 为最终裁决依据",
    },
    ThemeName.SPIRITUALITY: {
        "name_zh": "灵性",
        "techniques": [
            ("D20-analysis", "D20", "Vimsamsa 灵性分盘"),
            ("D60-analysis", "D60", "Shashtyamsha 业力分盘"),
            ("Karakamsha", "D1", "Karakamsha 宫位及主星"),
            ("Jupiter-dignity", "D1", "Jupiter 庙旺状态及宫位"),
            ("12th-house-spirit", "D1", "第12宫解脱/出离宫位"),
            ("Moksha-trikena", "D1", "4/8/12宫 Moksha 三角分析"),
            ("Ishta-Devata", "D1", "Ishta Devata 守护 deity"),
        ],
        "primary_chart": "D20",
        "conflict_rule": "灵性议题以 D20 (Vimsamsa) 为核心，D60 验证深层业力",
    },
}


# ═══════════════════════════════════════════════════════════════
# 交叉验证引擎
# ═══════════════════════════════════════════════════════════════

class CrossValidationEngine:
    """
    交叉验证引擎

    职责：
    1. 收集同一主题下多个技法的结论
    2. 检测正面/负面结论之间的矛盾
    3. 依据经典规则裁决矛盾（如 D9 > D1）
    4. 综合评定整体强度等级
    """

    def __init__(self, theme: ThemeName):
        self.theme = theme
        self.techniques: List[TechniqueResult] = []
        self.resolutions: List[ConflictResolution] = []

    def add_technique(self, result: TechniqueResult) -> None:
        self.techniques.append(result)

    def detect_conflicts(self) -> List[ConflictResolution]:
        """
        检测矛盾：同一主题下 sentiment 相反的结论构成矛盾对。
        采用 O(n^2) 配对检测，实际应用中可按 chart 类型分组优化。
        """
        conflicts = []
        n = len(self.techniques)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = self.techniques[i], self.techniques[j]
                # 仅当 sentiment 相反且均非 neutral 时视为矛盾
                if self._is_opposite(a.sentiment, b.sentiment):
                    resolution = self._adjudicate(a, b)
                    conflicts.append(resolution)
        self.resolutions = conflicts
        return conflicts

    @staticmethod
    def _is_opposite(s1: str, s2: str) -> bool:
        opposite_pairs = {("positive", "negative"), ("negative", "positive")}
        return (s1, s2) in opposite_pairs

    def _adjudicate(self, a: TechniqueResult, b: TechniqueResult) -> ConflictResolution:
        """
        矛盾裁决核心逻辑。
        优先级：1) 分盘优先级（CHART_PRIORITY） 2) 证据强度 3) 主题主盘
        """
        pri_a = CHART_PRIORITY.get(a.chart, 1)
        pri_b = CHART_PRIORITY.get(b.chart, 1)
        theme_info = THEME_TECHNIQUE_MAP[self.theme]
        primary = theme_info["primary_chart"]

        # 规则1：若一方来自主题主盘，优先采纳
        if a.chart == primary and b.chart != primary:
            winner, reasoning = a.technique, f"{a.chart} 是本主题主盘，优先采纳"
        elif b.chart == primary and a.chart != primary:
            winner, reasoning = b.technique, f"{b.chart} 是本主题主盘，优先采纳"
        # 规则2：比较分盘优先级
        elif pri_a > pri_b:
            winner, reasoning = a.technique, f"{a.chart} 优先级({pri_a})高于{b.chart}({pri_b})"
        elif pri_b > pri_a:
            winner, reasoning = b.technique, f"{b.chart} 优先级({pri_b})高于{a.chart}({pri_a})"
        # 规则3：优先级相同，比较证据强度
        else:
            strength_order = {StrengthLevel.STRONG: 3, StrengthLevel.MODERATE: 2, StrengthLevel.WEAK: 1}
            sa, sb = strength_order.get(a.strength, 0), strength_order.get(b.strength, 0)
            if sa > sb:
                winner, reasoning = a.technique, "同等分盘下，证据强度更高"
            elif sb > sa:
                winner, reasoning = b.technique, "同等分盘下，证据强度更高"
            else:
                winner, reasoning = a.technique, "势均力敌，保守采纳先出现的结论"

        return ConflictResolution(
            technique_a=a.technique,
            conclusion_a=a.conclusion,
            technique_b=b.technique,
            conclusion_b=b.conclusion,
            resolution=f"采纳 [{winner}] 的结论",
            reasoning=reasoning,
            winner=winner,
        )

    def compute_overall_strength(self) -> StrengthLevel:
        """
        综合强度评定算法：
        - 统计所有技法 sentiment
        - positive 占多数 → strong
        - mixed 或 moderate 占多数 → moderate
        - negative 占多数且无 strong positive 抵消 → weak
        """
        sentiments = [t.sentiment for t in self.techniques]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        neu = sentiments.count("neutral")
        total = len(sentiments) or 1

        # 考虑已裁决的冲突：被裁决为 winner 的负面结论需要加权
        for res in self.resolutions:
            # 若 winner 是负面结论，降低整体强度
            winner_tech = res.winner
            for t in self.techniques:
                if t.technique == winner_tech and t.sentiment == "negative":
                    neg += 0.5

        if pos / total >= 0.6 and neg == 0:
            return StrengthLevel.STRONG
        elif pos >= neg:
            return StrengthLevel.MODERATE
        else:
            return StrengthLevel.WEAK

    def get_dominant_sentiment(self) -> str:
        """获取裁决后的主导 sentiment"""
        # 应用裁决结果：loser 的 sentiment 被覆盖
        suppressed = set()
        for res in self.resolutions:
            loser = res.technique_b if res.winner == res.technique_a else res.technique_a
            suppressed.add(loser)

        valid = [t for t in self.techniques if t.technique not in suppressed]
        if not valid:
            valid = self.techniques

        sentiments = [t.sentiment for t in valid]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"


# ═══════════════════════════════════════════════════════════════
# 叙事生成器
# ═══════════════════════════════════════════════════════════════

class NarrativeGenerator:
    """
    叙事生成器

    将离散的技法结论编织为连贯段落，避免罗列式输出。
    采用模板引擎 + 语境缝合策略。
    """

    # 主题级叙事模板
    TEMPLATES: Dict[ThemeName, List[str]] = {
        ThemeName.MARRIAGE: [
            "你的婚姻格局中，{d1_summary}，而 {d9_summary}。{cross_verification}。{timing_sentence}",
            "从 D1 本命盘来看，{d1_detail}；Navamsa (D9) 则进一步揭示 {d9_detail}。{conclusion}。",
        ],
        ThemeName.CAREER: [
            "事业维度上，{d1_summary}；深入 Dashamsha (D10) 分盘，{d10_summary}。{cross_verification}。{timing_sentence}",
            "本命盘第10宫显示 {d1_detail}，而 D10 分盘则精细刻画了 {d10_detail}。{conclusion}。",
        ],
        ThemeName.WEALTH: [
            "财富格局呈现出 {overall_tone} 态势：{d1_summary}，Hora 分盘 (D2) 则 {d2_summary}。{av_sentence} {timing_sentence}",
            "从 Dhana Yoga 检测来看，{yoga_detail}；2宫主与11宫主的联动表明 {lord_detail}。{conclusion}。",
        ],
        ThemeName.HEALTH: [
            "健康层面，本命盘的 6/8/12 宫格局显示 {d1_summary}；Trimsamsa (D30) 分盘则 {d30_summary}。{cross_verification}。{timing_sentence}",
            "需要关注的是，{arista_detail}；不过 {positive_offset}。{recommendation_preview}",
        ],
        ThemeName.SPIRITUALITY: [
            "灵性成长路径上，{d20_summary}；Shashtyamsha (D60) 则 {d60_summary}。{karakamsha_detail}。{timing_sentence}",
            "Jupiter 作为灵性能量核心，{jupiter_detail}；第12宫的配置暗示 {twelfth_detail}。{conclusion}。",
        ],
    }

    def __init__(self, theme: ThemeName):
        self.theme = theme
        self.theme_zh = THEME_TECHNIQUE_MAP[theme]["name_zh"]

    def generate(
        self,
        techniques: List[TechniqueResult],
        resolutions: List[ConflictResolution],
        timing: Optional[TimingAnchor],
        strength: StrengthLevel,
    ) -> str:
        """生成连贯叙事段落"""
        # 1. 按 chart 分组提取关键结论
        by_chart: Dict[str, List[TechniqueResult]] = {}
        for t in techniques:
            by_chart.setdefault(t.chart, []).append(t)

        # 2. 构建模板变量
        ctx = self._build_context(by_chart, resolutions, timing, strength)

        # 3. 选择并渲染模板
        templates = self.TEMPLATES.get(self.theme, ["{overall_tone}格局。{cross_verification}。"])
        template = templates[0] if strength != StrengthLevel.WEAK else templates[-1]

        try:
            narrative = template.format(**ctx)
        except KeyError:
            # 降级：直接拼接关键句
            narrative = self._fallback_narrative(ctx, strength)

        return narrative

    def _build_context(
        self,
        by_chart: Dict[str, List[TechniqueResult]],
        resolutions: List[ConflictResolution],
        timing: Optional[TimingAnchor],
        strength: StrengthLevel,
    ) -> Dict[str, str]:
        """构建模板渲染上下文"""
        # 提取各分盘摘要
        d1_items = by_chart.get("D1", [])
        d9_items = by_chart.get("D9", [])
        d10_items = by_chart.get("D10", [])
        d2_items = by_chart.get("D2", [])
        d20_items = by_chart.get("D20", [])
        d30_items = by_chart.get("D30", [])
        d60_items = by_chart.get("D60", [])

        ctx = {
            "d1_summary": self._summarize_group(d1_items, "本命盘"),
            "d9_summary": self._summarize_group(d9_items, "Navamsa"),
            "d10_summary": self._summarize_group(d10_items, "Dashamsha"),
            "d2_summary": self._summarize_group(d2_items, "Hora"),
            "d20_summary": self._summarize_group(d20_items, "Vimsamsa"),
            "d30_summary": self._summarize_group(d30_items, "Trimsamsa"),
            "d60_summary": self._summarize_group(d60_items, "Shashtyamsha"),
            "d1_detail": self._detail_group(d1_items),
            "d9_detail": self._detail_group(d9_items),
            "d10_detail": self._detail_group(d10_items),
            "overall_tone": self._tone_description(strength),
            "cross_verification": self._cross_verification_sentence(resolutions),
            "timing_sentence": self._timing_sentence(timing),
            "conclusion": self._conclusion_sentence(strength, resolutions),
            "yoga_detail": self._extract_by_keyword(d1_items, "Yoga"),
            "lord_detail": self._extract_by_keyword(d1_items, "主星"),
            "av_sentence": self._extract_by_keyword(d1_items + d2_items, "Ashtakavarga"),
            "arista_detail": self._extract_by_keyword(d1_items, "Arista"),
            "positive_offset": self._extract_positive(d1_items),
            "recommendation_preview": self._recommendation_preview(strength),
            "jupiter_detail": self._extract_by_keyword(d1_items, "Jupiter"),
            "twelfth_detail": self._extract_by_keyword(d1_items, "12th"),
            "karakamsha_detail": self._extract_by_keyword(d1_items, "Karakamsha"),
        }
        return ctx

    @staticmethod
    def _summarize_group(items: List[TechniqueResult], chart_name: str) -> str:
        if not items:
            return f"{chart_name} 未提供显著信息"
        pos = [t for t in items if t.sentiment == "positive"]
        neg = [t for t in items if t.sentiment == "negative"]
        if len(pos) > len(neg):
            return f"{chart_name} 呈现积极信号"
        elif len(neg) > len(pos):
            return f"{chart_name} 存在挑战因素"
        return f"{chart_name} 呈现混合格局"

    @staticmethod
    def _detail_group(items: List[TechniqueResult]) -> str:
        if not items:
            return "信息有限"
        return "；".join(t.conclusion for t in items[:2])

    @staticmethod
    def _tone_description(strength: StrengthLevel) -> str:
        mapping = {
            StrengthLevel.STRONG: "整体积极的",
            StrengthLevel.MODERATE: "机遇与挑战并存的",
            StrengthLevel.WEAK: "需要谨慎经营的",
        }
        return mapping.get(strength, "复杂的")

    @staticmethod
    def _cross_verification_sentence(resolutions: List[ConflictResolution]) -> str:
        if not resolutions:
            return "各技法结论相互印证，未检测到显著矛盾"
        main = resolutions[0]
        return (
            f"交叉验证发现 '{main.technique_a}' 与 '{main.technique_b}' 存在分歧，"
            f"经裁决：{main.reasoning}，{main.resolution}"
        )

    @staticmethod
    def _timing_sentence(timing: Optional[TimingAnchor]) -> str:
        if not timing:
            return "当前大运周期未提供明确激活信号。"
        period = f"{timing.start_year}-{timing.end_year}年"
        return f"在{period}的{timing.dasha_period}大运期间，{timing.activation_description}"

    @staticmethod
    def _conclusion_sentence(strength: StrengthLevel, resolutions: List[ConflictResolution]) -> str:
        if strength == StrengthLevel.STRONG:
            return "综合来看，格局支持力度较强"
        elif strength == StrengthLevel.MODERATE:
            return "综合来看，需要把握关键窗口期"
        return "综合来看，建议采取审慎策略并积极化解"

    @staticmethod
    def _extract_by_keyword(items: List[TechniqueResult], keyword: str) -> str:
        for t in items:
            if keyword in t.technique or keyword in t.conclusion:
                return t.conclusion
        return "相关信息待补充"

    @staticmethod
    def _extract_positive(items: List[TechniqueResult]) -> str:
        for t in items:
            if t.sentiment == "positive":
                return t.conclusion
        return "整体格局仍有调和空间"

    @staticmethod
    def _recommendation_preview(strength: StrengthLevel) -> str:
        if strength == StrengthLevel.WEAK:
            return "建议关注预防性措施"
        return "维持良好状态即可"

    def _fallback_narrative(self, ctx: Dict[str, str], strength: StrengthLevel) -> str:
        """模板渲染失败时的降级叙事"""
        parts = [
            f"你的{self.theme_zh}格局呈现{ctx.get('overall_tone', '复杂')}态势。",
            ctx.get("d1_summary", ""),
            ctx.get("cross_verification", ""),
            ctx.get("timing_sentence", ""),
        ]
        return " ".join(p for p in parts if p)


# ═══════════════════════════════════════════════════════════════
# 时间锚定器
# ═══════════════════════════════════════════════════════════════

class TimingAnchorBuilder:
    """
    时间锚定器

    将主题相关的 Yoga / 宫位激活与当前及未来 Dasha 周期关联。
    """

    def __init__(self, chart_data: BirthChartData):
        self.chart = chart_data

    def build_for_theme(self, theme: ThemeName) -> Optional[TimingAnchor]:
        """
        为主题构建时间锚定。
        实际项目中应由 Dasha 计算引擎精确推算，此处提供模拟逻辑。
        """
        if not self.chart.dasha_timeline:
            return None

        # 找到当前或即将开始的大运周期
        current = None
        now = datetime.now().year
        for period in self.chart.dasha_timeline:
            if period.get("start", 0) <= now <= period.get("end", 0):
                current = period
                break
        if not current:
            current = self.chart.dasha_timeline[0]

        # 根据主题生成激活描述
        activation = self._activation_text(theme, current)

        return TimingAnchor(
            dasha_period=current.get("mahadasha", "Unknown") + "-" + current.get("antardasha", "Unknown"),
            start_year=current.get("start", now),
            end_year=current.get("end", now + 3),
            activation_description=activation,
            is_current=True,
        )

    def _activation_text(self, theme: ThemeName, period: Dict[str, Any]) -> str:
        md = period.get("mahadasha", "")
        ad = period.get("antardasha", "")
        theme_desc = {
            ThemeName.MARRIAGE: "婚姻相关宫位与 karaka 将被激活，是缔结或调整伴侣关系的关键期",
            ThemeName.CAREER: "事业宫位能量被引动，可能出现职位变动、项目突破或行业转换的契机",
            ThemeName.WEALTH: "财富宫位与 Dhana Yoga 被触发，收入结构可能发生变化",
            ThemeName.HEALTH: "健康宫位能量显现，是关注身体信号、调整作息的重要时期",
            ThemeName.SPIRITUALITY: "灵性宫位被激活，内省、修行或精神探索将获得深层进展",
        }
        return f"{md} 主运配合 {ad} 副运，{theme_desc.get(theme, '相关能量将被激活')}"


# ═══════════════════════════════════════════════════════════════
# 主题化解盘编排器（主控类）
# ═══════════════════════════════════════════════════════════════

class ThematicReportOrchestrator:
    """
    主题化解盘编排器 —— 主控类

    使用流程：
        1. 初始化 orchestrator = ThematicReportOrchestrator(chart_data)
        2. 添加技法结果 orchestrator.add_technique(theme, TechniqueResult(...))
        3. 生成报告 report = orchestrator.generate_report(theme)
        4. 或批量生成 all_reports = orchestrator.generate_all_reports()
    """

    def __init__(self, chart_data: BirthChartData):
        self.chart = chart_data
        self._data: Dict[ThemeName, List[TechniqueResult]] = {
            t: [] for t in ThemeName
        }
        self._validators: Dict[ThemeName, CrossValidationEngine] = {
            t: CrossValidationEngine(t) for t in ThemeName
        }
        self._narrators: Dict[ThemeName, NarrativeGenerator] = {
            t: NarrativeGenerator(t) for t in ThemeName
        }
        self._timing_builder = TimingAnchorBuilder(chart_data)

    def add_technique(self, theme: ThemeName, result: TechniqueResult) -> None:
        """向指定主题添加一个技法分析结果"""
        self._data[theme].append(result)
        self._validators[theme].add_technique(result)

    def add_techniques(self, theme: ThemeName, results: List[TechniqueResult]) -> None:
        """批量添加技法结果"""
        for r in results:
            self.add_technique(theme, r)

    def generate_report(self, theme: ThemeName) -> ThemeReport:
        """生成单一主题完整报告"""
        validator = self._validators[theme]
        techniques = self._data[theme]

        # 1. 交叉验证
        conflicts = validator.detect_conflicts()
        strength = validator.compute_overall_strength()
        dominant = validator.get_dominant_sentiment()

        # 2. 时间锚定
        timing = self._timing_builder.build_for_theme(theme)

        # 3. 叙事生成
        narrator = self._narrators[theme]
        narrative = narrator.generate(techniques, conflicts, timing, strength)

        # 4. 一句话总结
        summary = self._one_liner_summary(theme, dominant, strength, timing)

        # 5. 证据列表
        evidence = [self._technique_to_dict(t) for t in techniques]

        # 6. 建议生成
        recommendations = self._generate_recommendations(theme, strength, conflicts)

        return ThemeReport(
            theme=theme,
            summary=summary,
            narrative=narrative,
            evidence=evidence,
            strength=strength,
            timing=timing,
            conflicts=conflicts,
            recommendations=recommendations,
        )

    def generate_all_reports(self) -> Dict[ThemeName, ThemeReport]:
        """批量生成全部五大主题报告"""
        return {theme: self.generate_report(theme) for theme in ThemeName}

    @staticmethod
    def _technique_to_dict(t: TechniqueResult) -> Dict[str, Any]:
        return {
            "technique": t.technique,
            "chart": t.chart,
            "conclusion": t.conclusion,
            "sentiment": t.sentiment,
            "strength": t.strength.value,
            "details": t.details,
        }

    def _one_liner_summary(
        self,
        theme: ThemeName,
        dominant: str,
        strength: StrengthLevel,
        timing: Optional[TimingAnchor],
    ) -> str:
        zh = THEME_TECHNIQUE_MAP[theme]["name_zh"]
        sentiment_word = {
            "positive": "积极向好",
            "negative": "面临挑战",
            "neutral": "趋于平稳",
        }.get(dominant, "格局复杂")

        strength_word = {
            StrengthLevel.STRONG: "且信号明确",
            StrengthLevel.MODERATE: "但需把握时机",
            StrengthLevel.WEAK: "需谨慎应对",
        }.get(strength, "")

        timing_hint = ""
        if timing:
            timing_hint = f"，关键窗口在 {timing.start_year}-{timing.end_year} 年"

        return f"{zh}格局整体{sentiment_word}{strength_word}{timing_hint}。"

    @staticmethod
    def _generate_recommendations(
        theme: ThemeName,
        strength: StrengthLevel,
        conflicts: List[ConflictResolution],
    ) -> List[str]:
        """基于主题、强度和矛盾生成建议"""
        recs = []
        zh = THEME_TECHNIQUE_MAP[theme]["name_zh"]

        if strength == StrengthLevel.WEAK:
            recs.append(f"{zh}领域存在较多阻碍信号，建议采取保守策略，优先化解不利因素。")
        elif strength == StrengthLevel.MODERATE:
            recs.append(f"{zh}领域机遇与风险并存，建议聚焦关键窗口期主动出击。")
        else:
            recs.append(f"{zh}领域格局有利，建议顺势而为，巩固已有优势。")

        if conflicts:
            recs.append(
                f"检测到技法分歧：{conflicts[0].reasoning}。"
                f"建议以 {conflicts[0].winner} 的视角为主要参考。"
            )

        # 主题专属建议
        extra = {
            ThemeName.MARRIAGE: [
                "在做出重大婚姻决策前，建议结合 D9 分盘确认伴侣匹配度。",
                "Venus 行运期间是推进关系的适宜时机。",
            ],
            ThemeName.CAREER: [
                "关注 Amatyakaraka 所在宫位的行运触发。",
                "D10 分盘中的 Raja Yoga 行运期是事业突破的关键。",
            ],
            ThemeName.WEALTH: [
                "Dhana Yoga 激活期间可考虑资产配置，但需避开 Arista 叠加期。",
                "Ashtakavarga 高分宫位对应的行运期是财富增长的助力。",
            ],
            ThemeName.HEALTH: [
                "6/8/12 宫主星受克期间需加强体检与预防。",
                "D30 分盘中的凶星配置建议通过生活方式调整来调和。",
            ],
            ThemeName.SPIRITUALITY: [
                "Jupiter 大运期间适合深入修习与导师结缘。",
                "Karakamsha 所在宫位提示了最适合的灵性实践方向。",
            ],
        }
        recs.extend(extra.get(theme, []))
        return recs


# ═══════════════════════════════════════════════════════════════
# 模拟数据工厂（用于测试与示例）
# ═══════════════════════════════════════════════════════════════

class MockDataFactory:
    """生成模拟本命盘数据与技法结果，用于演示和单元测试。"""

    @staticmethod
    def create_sample_chart() -> BirthChartData:
        """创建一个丰富的模拟本命盘"""
        return BirthChartData(
            d1_houses={
                1: {"sign": "Cancer", "lord": "Moon", "planets": ["Moon", "Jupiter"]},
                7: {"sign": "Capricorn", "lord": "Saturn", "planets": ["Venus"]},
                10: {"sign": "Aries", "lord": "Mars", "planets": ["Sun", "Mercury"]},
                2: {"sign": "Leo", "lord": "Sun", "planets": []},
                11: {"sign": "Taurus", "lord": "Venus", "planets": ["Rahu"]},
                6: {"sign": "Sagittarius", "lord": "Jupiter", "planets": ["Saturn"]},
                8: {"sign": "Aquarius", "lord": "Saturn", "planets": ["Ketu"]},
                12: {"sign": "Gemini", "lord": "Mercury", "planets": ["Mars"]},
            },
            d9_houses={
                1: {"sign": "Pisces", "lord": "Jupiter", "planets": ["Jupiter"]},
                7: {"sign": "Virgo", "lord": "Mercury", "planets": ["Saturn", "Mars"]},
            },
            d10_houses={
                1: {"sign": "Libra", "lord": "Venus", "planets": ["Venus", "Mercury"]},
                10: {"sign": "Cancer", "lord": "Moon", "planets": ["Sun"]},
            },
            planets={
                "Jupiter": {"sign": "Cancer", "house": 1, "dignity": "exalted", "degree": 5.2},
                "Venus": {"sign": "Capricorn", "house": 7, "dignity": "neutral", "degree": 18.5},
                "Saturn": {"sign": "Sagittarius", "house": 6, "dignity": "neutral", "degree": 22.1},
                "Moon": {"sign": "Cancer", "house": 1, "dignity": "own", "degree": 12.0},
                "Sun": {"sign": "Aries", "house": 10, "dignity": "exalted", "degree": 8.7},
                "Mars": {"sign": "Gemini", "house": 12, "dignity": "neutral", "degree": 15.3},
                "Mercury": {"sign": "Aries", "house": 10, "dignity": "neutral", "degree": 3.1},
                "Rahu": {"sign": "Taurus", "house": 11, "dignity": "neutral", "degree": 28.0},
                "Ketu": {"sign": "Scorpio", "house": 5, "dignity": "neutral", "degree": 28.0},
            },
            current_dasha="Jupiter-Mercury",
            dasha_timeline=[
                {"mahadasha": "Jupiter", "antardasha": "Mercury", "start": 2025, "end": 2028},
                {"mahadasha": "Jupiter", "antardasha": "Ketu", "start": 2028, "end": 2029},
                {"mahadasha": "Jupiter", "antardasha": "Venus", "start": 2029, "end": 2032},
            ],
            yogas=[
                {"name": "Gajakesari Yoga", "planets": ["Moon", "Jupiter"], "house": 1, "type": "benefic"},
                {"name": "Viparita Raja Yoga", "planets": ["Saturn", "Ketu"], "house": 6, "type": "mixed"},
            ],
            ashtakavarga={
                "total_points": 128,
                "2nd_house": 28,
                "11th_house": 32,
                "bindus": {"Jupiter": 5, "Venus": 4, "Saturn": 3, "Sun": 5, "Moon": 5},
            },
        )

    @classmethod
    def create_marriage_techniques(cls) -> List[TechniqueResult]:
        """生成婚姻主题模拟技法结果（含矛盾以演示裁决）"""
        return [
            TechniqueResult(
                technique="D1-7th-house",
                chart="D1",
                conclusion="第7宫主 Saturn 落入第6宫，与疾病宫关联，婚姻宫位受克",
                sentiment="negative",
                strength=StrengthLevel.MODERATE,
                details={"lord": "Saturn", "house": 6, "aspect": "Mars aspects 7th"},
            ),
            TechniqueResult(
                technique="D9-lagna",
                chart="D9",
                conclusion="Navamsa 上升落入双鱼座，主星 Jupiter 庙旺，婚姻基础稳固",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"navamsa_lagna": "Pisces", "lagna_lord": "Jupiter", "dignity": "exalted"},
            ),
            TechniqueResult(
                technique="DK-position",
                chart="D1",
                conclusion="Dara Karaka Venus 落入第7宫本宫，配偶特质明显",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"dk_planet": "Venus", "house": 7},
            ),
            TechniqueResult(
                technique="Venus-strength",
                chart="D1",
                conclusion="Venus 落入摩羯座，处于中性状态，无庙旺也无落陷",
                sentiment="neutral",
                strength=StrengthLevel.WEAK,
                details={"sign": "Capricorn", "dignity": "neutral"},
            ),
            TechniqueResult(
                technique="Upapada-lagna",
                chart="D1",
                conclusion="Upapada 落入狮子座，主星 Sun 入庙于第10宫，配偶社会地位良好",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"upapada_sign": "Leo", "lord": "Sun", "lord_house": 10},
            ),
        ]

    @classmethod
    def create_career_techniques(cls) -> List[TechniqueResult]:
        return [
            TechniqueResult(
                technique="D1-10th-house",
                chart="D1",
                conclusion="第10宫主 Mars 落入第12宫，事业能量外泄，可能涉及海外或幕后工作",
                sentiment="negative",
                strength=StrengthLevel.MODERATE,
                details={"lord": "Mars", "house": 12},
            ),
            TechniqueResult(
                technique="D10-lagna",
                chart="D10",
                conclusion="Dashamsha 上升天秤，主星 Venus 与 Mercury 合相，事业偏向沟通协调",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"d10_lagna": "Libra", "planets": ["Venus", "Mercury"]},
            ),
            TechniqueResult(
                technique="Amatyakaraka-dignity",
                chart="D1",
                conclusion="Amatyakaraka Mercury 落入第10宫白羊，与 Sun 同宫，具备管理才能",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"amk": "Mercury", "house": 10, "conjunct": ["Sun"]},
            ),
            TechniqueResult(
                technique="Raja-Yoga-10th",
                chart="D1",
                conclusion="第10宫形成 Raja Yoga，Sun 与 Mercury 合相（Budha-Aditya Yoga）",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"yoga": "Budha-Aditya", "house": 10},
            ),
        ]

    @classmethod
    def create_wealth_techniques(cls) -> List[TechniqueResult]:
        return [
            TechniqueResult(
                technique="Dhana-Yoga",
                chart="D1",
                conclusion="第2宫主 Sun 与第11宫主 Venus 无直接关联，Dhana Yoga 基础较弱",
                sentiment="negative",
                strength=StrengthLevel.WEAK,
                details={"2nd_lord": "Sun", "11th_lord": "Venus", "aspect": "none"},
            ),
            TechniqueResult(
                technique="Ashtakavarga-wealth",
                chart="AV",
                conclusion="第11宫 Ashtakavarga 分值高达32，远超平均值，财富获取渠道多元",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"11th_house_points": 32, "average": 25},
            ),
            TechniqueResult(
                technique="2nd-lord",
                chart="D1",
                conclusion="第2宫主 Sun 入庙第10宫，正财与事业声誉挂钩",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"lord": "Sun", "dignity": "exalted", "house": 10},
            ),
        ]

    @classmethod
    def create_health_techniques(cls) -> List[TechniqueResult]:
        return [
            TechniqueResult(
                technique="D1-6th-house",
                chart="D1",
                conclusion="第6宫主 Jupiter 入庙第1宫，疾病抵抗力强",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"lord": "Jupiter", "dignity": "exalted", "house": 1},
            ),
            TechniqueResult(
                technique="D1-8th-house",
                chart="D1",
                conclusion="第8宫主 Saturn 落入第6宫，形成 Viparita Raja Yoga，化险为夷",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"lord": "Saturn", "house": 6, "yoga": "Viparita Raja"},
            ),
            TechniqueResult(
                technique="Arista-Yoga",
                chart="D1",
                conclusion="Mars 落入第12宫与第1宫 Moon-Jupiter 无直接相位，Arista 信号较弱",
                sentiment="positive",
                strength=StrengthLevel.WEAK,
                details={"malefic": "Mars", "affected": "none"},
            ),
            TechniqueResult(
                technique="D30-analysis",
                chart="D30",
                conclusion="Trimsamsa 第1宫受土星影响，需注意骨骼与关节保养",
                sentiment="negative",
                strength=StrengthLevel.MODERATE,
                details={"d30_lagna_affected": "Saturn", "area": "bones"},
            ),
        ]

    @classmethod
    def create_spirituality_techniques(cls) -> List[TechniqueResult]:
        return [
            TechniqueResult(
                technique="Jupiter-dignity",
                chart="D1",
                conclusion="Jupiter 在第1宫巨蟹座庙旺，灵性根基深厚，天然具备信仰倾向",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"planet": "Jupiter", "dignity": "exalted", "house": 1},
            ),
            TechniqueResult(
                technique="12th-house-spirit",
                chart="D1",
                conclusion="第12宫主 Mercury 落入第10宫，灵性追求与世俗事业产生张力",
                sentiment="negative",
                strength=StrengthLevel.MODERATE,
                details={"lord": "Mercury", "house": 10, "tension": "material vs spiritual"},
            ),
            TechniqueResult(
                technique="D20-analysis",
                chart="D20",
                conclusion="Vimsamsa 第5宫有 Jupiter 加持，具备教学与传承灵性知识的禀赋",
                sentiment="positive",
                strength=StrengthLevel.STRONG,
                details={"d20_5th": "Jupiter", "ability": "teaching"},
            ),
            TechniqueResult(
                technique="Karakamsha",
                chart="D1",
                conclusion="Karakamsha 落入第9宫，人生深层使命与 Dharma/哲学探索相关",
                sentiment="positive",
                strength=StrengthLevel.MODERATE,
                details={"karakamsha_house": 9},
            ),
        ]


# ═══════════════════════════════════════════════════════════════
# 演示与测试入口
# ═══════════════════════════════════════════════════════════════

def demo():
    """
    完整演示：从模拟数据到主题化报告的端到端流程。
    """
    print("=" * 70)
    print("Jyotish 主题化解盘编排器 —— 演示运行")
    print("=" * 70)

    # 1. 准备模拟本命盘
    chart = MockDataFactory.create_sample_chart()
    print(f"\n[1] 已加载模拟本命盘")
    print(f"    当前大运: {chart.current_dasha}")
    print(f"    行星数量: {len(chart.planets)}")

    # 2. 初始化编排器
    orchestrator = ThematicReportOrchestrator(chart)

    # 3. 注入各主题技法结果
    factory = MockDataFactory()
    orchestrator.add_techniques(ThemeName.MARRIAGE, factory.create_marriage_techniques())
    orchestrator.add_techniques(ThemeName.CAREER, factory.create_career_techniques())
    orchestrator.add_techniques(ThemeName.WEALTH, factory.create_wealth_techniques())
    orchestrator.add_techniques(ThemeName.HEALTH, factory.create_health_techniques())
    orchestrator.add_techniques(ThemeName.SPIRITUALITY, factory.create_spirituality_techniques())

    print(f"\n[2] 已注入技法结果:")
    for theme in ThemeName:
        count = len(orchestrator._data[theme])
        print(f"    - {theme.value:15s} ({THEME_TECHNIQUE_MAP[theme]['name_zh']}) : {count} 条")

    # 4. 批量生成报告
    print(f"\n[3] 生成分主题报告...")
    reports = orchestrator.generate_all_reports()

    # 5. 逐主题展示
    for theme, report in reports.items():
        print(f"\n{'─' * 70}")
        print(f"主题: {report.theme.value.upper()} ({THEME_TECHNIQUE_MAP[theme]['name_zh']})")
        print(f"{'─' * 70}")
        print(f"【一句话总结】\n  {report.summary}")
        print(f"\n【整体强度】\n  {report.strength.value}")
        print(f"\n【叙事段落】\n  {report.narrative}")

        if report.timing:
            t = report.timing
            print(f"\n【时间锚定】")
            print(f"  大运周期: {t.dasha_period}")
            print(f"  时间范围: {t.start_year}-{t.end_year}")
            print(f"  激活描述: {t.activation_description}")

        if report.conflicts:
            print(f"\n【矛盾裁决】")
            for idx, c in enumerate(report.conflicts, 1):
                print(f"  [{idx}] {c.technique_a} vs {c.technique_b}")
                print(f"      裁决: {c.resolution}")
                print(f"      依据: {c.reasoning}")

        print(f"\n【建议】")
        for idx, rec in enumerate(report.recommendations, 1):
            print(f"  {idx}. {rec}")

        print(f"\n【证据链 ({len(report.evidence)} 条)】")
        for ev in report.evidence:
            icon = {"positive": "+", "negative": "-", "neutral": "o"}.get(ev["sentiment"], "?")
            print(f"  [{icon}] [{ev['chart']:4s}] {ev['technique']:20s} — {ev['conclusion']}")

    # 6. 输出完整 JSON（以婚姻为例）
    print(f"\n{'=' * 70}")
    print("[4] 结构化 JSON 输出示例（婚姻主题）")
    print(f"{'=' * 70}")
    marriage_json = reports[ThemeName.MARRIAGE].to_json(indent=2, ensure_ascii=False)
    print(marriage_json)

    print(f"\n{'=' * 70}")
    print("演示完成。")
    print(f"{'=' * 70}")

    return reports


def unit_test():
    """
    简单的断言测试，验证核心引擎逻辑。
    """
    print("\n运行单元测试...")

    # 测试1: 矛盾裁决 —— D9 应优先于 D1
    engine = CrossValidationEngine(ThemeName.MARRIAGE)
    engine.add_technique(TechniqueResult(
        technique="D1-test", chart="D1", conclusion="D1 says bad",
        sentiment="negative", strength=StrengthLevel.STRONG,
    ))
    engine.add_technique(TechniqueResult(
        technique="D9-test", chart="D9", conclusion="D9 says good",
        sentiment="positive", strength=StrengthLevel.STRONG,
    ))
    conflicts = engine.detect_conflicts()
    assert len(conflicts) == 1, "应检测到 1 条矛盾"
    assert conflicts[0].winner == "D9-test", "D9 应获胜"
    print("  [PASS] 矛盾裁决: D9 > D1")

    # 测试2: 强度计算
    engine2 = CrossValidationEngine(ThemeName.CAREER)
    engine2.add_technique(TechniqueResult(
        technique="t1", chart="D1", conclusion="good",
        sentiment="positive", strength=StrengthLevel.STRONG,
    ))
    engine2.add_technique(TechniqueResult(
        technique="t2", chart="D1", conclusion="good2",
        sentiment="positive", strength=StrengthLevel.STRONG,
    ))
    engine2.add_technique(TechniqueResult(
        technique="t3", chart="D1", conclusion="bad",
        sentiment="negative", strength=StrengthLevel.WEAK,
    ))
    strength = engine2.compute_overall_strength()
    assert strength == StrengthLevel.MODERATE, f"期望 moderate，得到 {strength}"
    print("  [PASS] 强度计算: 多数 positive → moderate（因存在 negative）")

    # 测试3: 叙事生成非空
    gen = NarrativeGenerator(ThemeName.MARRIAGE)
    narrative = gen.generate(
        techniques=[
            TechniqueResult("D1-7th", "D1", "7th lord ok", "neutral", StrengthLevel.MODERATE),
            TechniqueResult("D9-lag", "D9", "D9 good", "positive", StrengthLevel.STRONG),
        ],
        resolutions=[],
        timing=TimingAnchor("Jupiter-Venus", 2027, 2030, "test", True),
        strength=StrengthLevel.STRONG,
    )
    assert len(narrative) > 20, "叙事段落应有一定长度"
    print("  [PASS] 叙事生成: 段落非空")

    print("所有单元测试通过。")


if __name__ == "__main__":
    reports = demo()
    unit_test()
