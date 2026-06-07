#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orchestrator_bridge.py — 编排器桥接层
=====================================
打通 reading_orchestrator (技法执行层) 与 report_orchestrator (叙事生成层)。

职责：
1. 将 ReadingChapter 转换为 report_orchestrator 可消费的 TechniqueResult
2. 映射主题（ReadingTheme ↔ ThemeName）
3. 统一冲突裁决的表达方式
4. 提供端到端的一体化报告生成入口

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import dasha systems (handle relative imports)
try:
    from ashtottari_dasha import calculate_ashtottari_dasha
    from yogini_dasha import calculate_yogini_dasha
    from kalachakra_dasha import calculate_kalachakra_dasha
except ImportError:
    from scripts.ashtottari_dasha import calculate_ashtottari_dasha
    from scripts.yogini_dasha import calculate_yogini_dasha
    from scripts.kalachakra_dasha import calculate_kalachakra_dasha

# Import both orchestrators (handle relative imports)
try:
    from reading_orchestrator import (
        ReadingOrchestrator, ReadingTheme, ReadingChapter,
        TechniqueResult as ReadingTechniqueResult,
    )
except ImportError:
    from scripts.reading_orchestrator import (
        ReadingOrchestrator, ReadingTheme, ReadingChapter,
        TechniqueResult as ReadingTechniqueResult,
    )

try:
    from report_orchestrator import (
        ThematicReportOrchestrator as ReportOrchestrator,
        ThemeName, ThemeReport,
        TechniqueResult as ReportTechniqueResult,
        StrengthLevel, TimingAnchor,
    )
except ImportError:
    from scripts.report_orchestrator import (
        ThematicReportOrchestrator as ReportOrchestrator,
        ThemeName, ThemeReport,
        TechniqueResult as ReportTechniqueResult,
        StrengthLevel, TimingAnchor,
    )


# ═══════════════════════════════════════════════════════════════
# 主题映射
# ═══════════════════════════════════════════════════════════════

THEME_MAPPING: Dict[ReadingTheme, ThemeName] = {
    ReadingTheme.MARRIAGE: ThemeName.MARRIAGE,
    ReadingTheme.CAREER: ThemeName.CAREER,
    ReadingTheme.WEALTH: ThemeName.WEALTH,
    ReadingTheme.HEALTH: ThemeName.HEALTH,
    ReadingTheme.SPIRITUAL: ThemeName.SPIRITUALITY,
}

REVERSE_THEME_MAPPING: Dict[ThemeName, ReadingTheme] = {
    v: k for k, v in THEME_MAPPING.items()
}


# ═══════════════════════════════════════════════════════════════
# 桥接转换器
# ═══════════════════════════════════════════════════════════════

class OrchestratorBridge:
    """
    编排器桥接器

    将 reading_orchestrator 的输出（ReadingChapter）转换为
    report_orchestrator 的输入（TechniqueResult + ThemeReport）。
    """

    def __init__(
        self,
        reading_orchestrator: ReadingOrchestrator,
        report_orchestrator: ReportOrchestrator,
    ):
        self.ro = reading_orchestrator
        self.rpo = report_orchestrator

    # ── ReadingChapter → ReportTechniqueResult ──

    @staticmethod
    def chapter_to_technique_results(chapter: ReadingChapter) -> List[ReportTechniqueResult]:
        """
        将 ReadingChapter 拆解为 report_orchestrator 的 TechniqueResult 列表。

        策略：
        - findings → 每个 finding 对应一个 TechniqueResult
        - conflicts → 每个 conflict 也作为一个 TechniqueResult（sentiment=neutral，标注矛盾）
        - timing → 如果时间锚定存在，也生成一个 TechniqueResult
        """
        results: List[ReportTechniqueResult] = []

        # 1. Findings → positive/negative TechniqueResult
        for finding in chapter.findings:
            sentiment = _infer_sentiment(finding)
            strength = _infer_strength(finding, chapter.conflicts)
            results.append(ReportTechniqueResult(
                technique=f"finding_{len(results)}",
                chart="D1",  # default; can be refined
                conclusion=finding,
                sentiment=sentiment,
                strength=strength,
            ))

        # 2. Conflicts → neutral TechniqueResult with details
        for conflict in chapter.conflicts:
            results.append(ReportTechniqueResult(
                technique="conflict_resolution",
                chart="D1",
                conclusion=conflict.narrative,
                sentiment="neutral",
                strength=StrengthLevel.MODERATE,
                details={
                    "dimension": conflict.dimension,
                    "d1_finding": conflict.d1_finding,
                    "d9_finding": conflict.d9_finding,
                    "resolution": conflict.resolution,
                },
            ))

        # 3. Timing → TechniqueResult
        if chapter.timing:
            results.append(ReportTechniqueResult(
                technique="timing_anchor",
                chart="Dasha",
                conclusion=chapter.timing,
                sentiment="neutral",
                strength=StrengthLevel.MODERATE,
            ))

        return results

    # ── 推运系统注入 ──

    def inject_dasha_results(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算并注入 Ashtottari / Yogini / Kalachakra Dasha 结果。

        从 chart_data 提取 birth_info，调用三个推运模块，
        将当前推运周期转换为 TimingAnchor 注入 report_orchestrator。

        Returns:
            三个推运系统的原始计算结果，供后续使用。
        """
        # 从 chart_data 提取 birth_info
        birth_info = self._extract_birth_info(chart_data)
        if not birth_info:
            return {}

        results: Dict[str, Any] = {}

        # 1. Ashtottari Dasha (条件性推运)
        try:
            ash = calculate_ashtottari_dasha(birth_info)
            results["ashtottari"] = ash
            if ash.get("applicable") and ash.get("current"):
                self._add_dasha_timing_anchor(
                    system="Ashtottari",
                    current=ash["current"],
                    total_cycle=ash.get("total_cycle", 108),
                )
        except Exception:
            pass

        # 2. Yogini Dasha (普遍适用)
        try:
            yog = calculate_yogini_dasha(birth_info)
            results["yogini"] = yog
            if yog.get("current"):
                self._add_dasha_timing_anchor(
                    system="Yogini",
                    current=yog["current"],
                    total_cycle=yog.get("total_cycle", 36),
                )
        except Exception:
            pass

        # 3. Kalachakra Dasha (条件性推运)
        try:
            kal = calculate_kalachakra_dasha(birth_info)
            results["kalachakra"] = kal
            if kal.get("current"):
                self._add_dasha_timing_anchor(
                    system="Kalachakra",
                    current=kal["current"],
                    total_cycle=kal.get("total_cycle", 0),
                )
        except Exception:
            pass

        # 4. 将推运结果也作为 TechniqueResult 注入所有主题
        self._inject_dasha_technique_results(results)

        return results

    def _extract_birth_info(self, chart_data: Any) -> Optional[Dict[str, Any]]:
        """从 chart_data 提取推运计算所需的 birth_info。

        支持 dict 和 dataclass 对象（如 BirthChartData）。
        如果数据不足，返回 None（推运注入将静默跳过）。
        """
        import dataclasses

        # 统一转为 dict
        if hasattr(chart_data, "__dataclass_fields__"):
            data = dataclasses.asdict(chart_data)
        elif isinstance(chart_data, dict):
            data = chart_data
        else:
            return None

        info: Dict[str, Any] = {}

        # birth_datetime
        birth_dt = data.get("birth_datetime")
        if birth_dt is None:
            chart = data.get("chart") or data.get("natal_chart")
            if chart:
                birth_dt = chart.get("birth_datetime")
        if isinstance(birth_dt, str):
            birth_dt = datetime.fromisoformat(birth_dt.replace("Z", "+00:00"))
        info["birth_datetime"] = birth_dt

        # moon_nakshatra_index
        moon_nak = data.get("moon_nakshatra_index")
        if moon_nak is None:
            chart = data.get("chart") or data.get("natal_chart")
            if chart:
                nakshatras = chart.get("nakshatras") or chart.get("nakshatra")
                if nakshatras and "Moon" in nakshatras:
                    moon_nak = nakshatras["Moon"].get("index")
        if moon_nak is not None:
            info["moon_nakshatra_index"] = int(moon_nak)

        # is_shukla_paksha (从Tithi推断)
        tithi = data.get("tithi")
        if tithi is None:
            chart = data.get("chart") or data.get("natal_chart")
            if chart:
                tithi = chart.get("tithi")
        if tithi is not None:
            tithi_num = int(tithi) if isinstance(tithi, (int, float, str)) else 15
            info["is_shukla_paksha"] = 1 <= tithi_num <= 15

        # lagna_rashi_index
        lagna = data.get("ascendant") or data.get("lagna")
        if lagna is None:
            chart = data.get("chart") or data.get("natal_chart")
            if chart:
                lagna = chart.get("ascendant") or chart.get("lagna")
        if lagna is not None:
            if isinstance(lagna, str):
                sign_names = [
                    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
                ]
                if lagna in sign_names:
                    info["lagna_rashi_index"] = sign_names.index(lagna)
            elif isinstance(lagna, dict):
                sign = lagna.get("sign") or lagna.get("rashi")
                if sign:
                    sign_names = [
                        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
                    ]
                    if sign in sign_names:
                        info["lagna_rashi_index"] = sign_names.index(sign)
                degree = lagna.get("degree")
                if degree is not None:
                    info["lagna_rashi_index"] = int(degree / 30) % 12

        # moon_pada (for Kalachakra)
        moon_pada = data.get("moon_pada")
        if moon_pada is None:
            chart = data.get("chart") or data.get("natal_chart")
            if chart:
                nakshatras = chart.get("nakshatras") or chart.get("nakshatra")
                if nakshatras and "Moon" in nakshatras:
                    moon_pada = nakshatras["Moon"].get("pada")
        if moon_pada is not None:
            info["moon_pada"] = int(moon_pada)
        else:
            info["moon_pada"] = 1

        return info if info.get("birth_datetime") else None

    def _add_dasha_timing_anchor(
        self,
        system: str,
        current: Dict[str, Any],
        total_cycle: int,
    ) -> None:
        """将单个推运当前周期转换为 TimingAnchor 并注入 report_orchestrator。"""
        start_date = current.get("start_date", "")
        end_date = current.get("end_date", "")

        # 提取年份
        try:
            start_year = int(start_date[:4]) if isinstance(start_date, str) else datetime.now().year
            end_year = int(end_date[:4]) if isinstance(end_date, str) else (start_year + 5)
        except (ValueError, TypeError):
            start_year = datetime.now().year
            end_year = start_year + 5

        # 确定行星名称
        planet = current.get("planet") or current.get("yogini") or current.get("lord") or "Unknown"

        # 构建激活描述
        activation = f"{system}推运中，{planet}主运带来人生阶段的转换与业力展现"
        if system == "Yogini":
            activation = f"Yogini推运中，{planet}女神主导当前周期，影响心理与事件层面"
        elif system == "Kalachakra":
            rashi = current.get("rashi", "")
            mode = current.get("mode", "")
            activation = f"Kalachakra {mode}模式推运中，{planet}主宰{rashi}宫阶段"

        anchor = TimingAnchor(
            dasha_period=f"{system}-{planet}",
            start_year=start_year,
            end_year=end_year,
            activation_description=activation,
            is_current=True,
        )

        # 注入到所有5个主题
        for tn in ThemeName:
            self.rpo.add_timing(tn, anchor)

    def _inject_dasha_technique_results(self, dasha_results: Dict[str, Any]) -> None:
        """将推运结果作为 TechniqueResult 注入所有主题。"""
        for system, result in dasha_results.items():
            if not result:
                continue
            current = result.get("current")
            if not current:
                continue

            planet = current.get("planet") or current.get("yogini") or current.get("lord") or "Unknown"
            system_zh = {"ashtottari": "Ashtottari推运", "yogini": "Yogini推运", "kalachakra": "Kalachakra推运"}.get(system, system)

            conclusion = f"{system_zh}：当前处于{planet}主运周期"
            if system == "ashtottari" and result.get("applicable") is False:
                conclusion = f"{system_zh}：不适用（出生条件不符合）"

            tech_result = ReportTechniqueResult(
                technique=f"{system}_dasha",
                chart="Dasha",
                conclusion=conclusion,
                sentiment="neutral",
                strength=StrengthLevel.MODERATE,
                details={
                    "system": system,
                    "current_period": current,
                    "total_cycle": result.get("total_cycle"),
                    "applicable": result.get("applicable", True),
                },
            )

            for tn in ThemeName:
                self.rpo.add_technique(tn, tech_result)

    # ── 端到端报告生成 ──

    def generate_full_report(
        self,
        chart_data: Dict[str, Any],
        themes: Optional[List[ReadingTheme]] = None,
    ) -> Dict[str, Any]:
        """
        端到端报告生成：从星盘数据 → ReadingChapter → ThemeReport。

        Args:
            chart_data: 星盘完整数据
            themes: 要分析的主题列表，None=全部5大主题

        Returns:
            {
                "reading_chapters": Dict[ReadingTheme, List[ReadingChapter]],
                "theme_reports": Dict[ThemeName, ThemeReport],
                "unified_narrative": str,
                "dasha_results": Dict[str, Any],
            }
        """
        if themes is None:
            themes = [
                ReadingTheme.MARRIAGE,
                ReadingTheme.CAREER,
                ReadingTheme.WEALTH,
                ReadingTheme.HEALTH,
                ReadingTheme.SPIRITUAL,
            ]

        # Step 0: 注入推运结果（在所有主题分析之前）
        dasha_results = self.inject_dasha_results(chart_data)

        reading_chapters: Dict[str, List[ReadingChapter]] = {}
        theme_reports: Dict[str, Any] = {}

        for rt in themes:
            # Step 1: reading_orchestrator 执行技法
            chapters = self.ro.analyze(chart_data, rt)
            reading_chapters[rt.value] = chapters

            # Step 2: 映射到 ThemeName
            tn = THEME_MAPPING.get(rt)
            if not tn:
                continue

            # Step 3: 将 chapters 转换为 TechniqueResults 并喂给 report_orchestrator
            for ch in chapters:
                tech_results = self.chapter_to_technique_results(ch)
                for tr in tech_results:
                    self.rpo.add_technique(tn, tr)

            # Step 4: 生成 ThemeReport
            report = self.rpo.generate_report(tn)
            theme_reports[tn.value] = report.to_dict()

        # Step 5: 生成统一叙事
        unified = self._build_unified_narrative(theme_reports)

        return {
            "reading_chapters": {
                k: [self._chapter_to_dict(ch) for ch in v]
                for k, v in reading_chapters.items()
            },
            "theme_reports": theme_reports,
            "unified_narrative": unified,
            "dasha_results": dasha_results,
        }

    # ── 内部辅助 ──

    @staticmethod
    def _build_unified_narrative(theme_reports: Dict[str, Any]) -> str:
        """将多个 ThemeReport 拼接为统一的人生叙事。"""
        parts = []
        order = ["marriage", "career", "wealth", "health", "spirituality"]
        for theme_key in order:
            if theme_key in theme_reports:
                r = theme_reports[theme_key]
                parts.append(f"\n## {r.get('summary', theme_key)}")
                parts.append(r.get("narrative", ""))
                if r.get("recommendations"):
                    parts.append("\n**建议：**")
                    for rec in r["recommendations"]:
                        parts.append(f"- {rec}")
        return "\n".join(parts)

    @staticmethod
    def _chapter_to_dict(ch: ReadingChapter) -> Dict[str, Any]:
        return {
            "title": ch.title,
            "subtitle": ch.subtitle,
            "priority": ch.priority,
            "techniques_used": ch.techniques_used,
            "findings": ch.findings,
            "conflicts": [
                {
                    "dimension": c.dimension,
                    "d1_finding": c.d1_finding,
                    "d9_finding": c.d9_finding,
                    "resolution": c.resolution,
                    "narrative": c.narrative,
                }
                for c in ch.conflicts
            ],
            "narrative": ch.narrative,
            "actionable": ch.actionable,
            "timing": ch.timing,
        }


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _infer_sentiment(text: str) -> str:
    """从 finding 文本推断 sentiment。"""
    negative_keywords = [
        "阻碍", "困难", "挑战", "风险", "不利", "凶", "克", "弱", "陷",
        "冲突", "矛盾", "破坏", "损失", "障碍", "延迟", "问题",
    ]
    positive_keywords = [
        "有利", "吉", "旺", "强", "助力", "支持", "机遇", "突破",
        "成就", "成功", "和谐", "稳定", "增益", "提升",
    ]
    text_lower = text.lower()
    neg_score = sum(1 for w in negative_keywords if w in text_lower)
    pos_score = sum(1 for w in positive_keywords if w in text_lower)
    if neg_score > pos_score:
        return "negative"
    if pos_score > neg_score:
        return "positive"
    return "neutral"


def _infer_strength(text: str, conflicts: List[Any]) -> StrengthLevel:
    """从 finding 文本和冲突情况推断 strength。"""
    strong_keywords = ["非常", "极强", "显著", "明确", "主导", "绝对"]
    weak_keywords = ["轻微", "略有", "潜在", "可能", "模糊", "微弱"]
    text_lower = text.lower()
    if any(w in text_lower for w in strong_keywords):
        return StrengthLevel.STRONG
    if any(w in text_lower for w in weak_keywords):
        return StrengthLevel.WEAK
    if conflicts:
        return StrengthLevel.MODERATE
    return StrengthLevel.MODERATE


# ═══════════════════════════════════════════════════════════════
# CLI / 测试
# ═══════════════════════════════════════════════════════════════

def demo():
    """演示桥接功能（使用模拟数据）。"""
    from report_orchestrator import MockDataFactory

    # 创建模拟星盘数据
    chart_data = MockDataFactory.create_sample_chart()

    # 创建 orchestrators
    # NOTE: reading_orchestrator 需要 registry，这里用空 registry 演示
    class DummyRegistry:
        def get(self, name):
            return None

    ro = ReadingOrchestrator(DummyRegistry())
    rpo = ReportOrchestrator(chart_data)

    # 桥接
    bridge = OrchestratorBridge(ro, rpo)
    result = bridge.generate_full_report(chart_data)

    print("=" * 60)
    print("Orchestrator Bridge Demo")
    print("=" * 60)
    print(f"\n生成主题报告数: {len(result['theme_reports'])}")
    for theme, report in result["theme_reports"].items():
        print(f"\n  [{theme}]")
        print(f"    总结: {report.get('summary', 'N/A')}")
        print(f"    强度: {report.get('strength', 'N/A')}")
        print(f"    证据数: {len(report.get('evidence', []))}")

    print("\n" + "=" * 60)
    print("统一叙事（前500字）:")
    print("=" * 60)
    print(result["unified_narrative"][:500] + "...")


if __name__ == "__main__":
    demo()
