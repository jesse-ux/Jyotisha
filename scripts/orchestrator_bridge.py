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

    # ── full-reading.modules → ReportTechniqueResult ──

    def inject_full_reading_modules(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 `jyotish_engine.py full-reading` 的真实模块输出注入主题化报告。

        v6.1.8 之前，桥接层主要依赖 reading_orchestrator 的 registry；当 registry
        未注册真实执行函数时，主题报告容易退化为少量模拟/占位信息。本方法直接消费
        full-reading.modules 中已经计算完成的模块，把 Yoga、分盘、Ashtakavarga、
        Shadbala、特殊上升点、Vivah Saham、Transit、多系统 Dasha Convergence 等
        转成 report_orchestrator 可叙事的 TechniqueResult。
        """
        modules = _extract_modules(chart_data)
        if not modules:
            return {"injected": False, "reason": "no full-reading modules found", "counts": {}}

        counts = {theme.value: 0 for theme in ThemeName}

        def add(theme: ThemeName, result: ReportTechniqueResult) -> None:
            self.rpo.add_technique(theme, result)
            counts[theme.value] += 1

        self._inject_yoga_module(modules, add)
        self._inject_varga_modules(modules, add)
        self._inject_strength_modules(modules, add)
        self._inject_special_points(modules, add)
        self._inject_dasa_convergence_module(modules, add)
        self._inject_transit_module(modules, add)

        return {
            "injected": True,
            "source": "full-reading.modules",
            "counts": counts,
            "source_modules": sorted(k for k in modules.keys() if k in {
                "yoga", "varga_full", "d9_navamsa_expanded", "ashtakavarga", "shadbala",
                "special_lagnas", "vivah_saham", "dasa_convergence", "transit_multi_reference",
                "dasha", "yogini_dasha", "ashtottari_dasha", "kalachakra_dasha",
            }),
        }

    def _inject_yoga_module(self, modules: Dict[str, Any], add) -> None:
        yoga = modules.get("yoga") or {}
        yogas = yoga.get("yogas") or yoga.get("detected_yogas") or []
        if not isinstance(yogas, list):
            return

        added_per_theme = {theme: 0 for theme in ThemeName}
        for y in yogas:
            if not isinstance(y, dict):
                continue
            themes = _themes_for_yoga(y)
            if not themes:
                continue
            strength = _strength_from_text(y.get("strength"), default=StrengthLevel.MODERATE)
            sentiment = _sentiment_from_yoga(y)
            effects = y.get("effects") or []
            if isinstance(effects, list):
                effect_text = "、".join(str(e) for e in effects[:4])
            else:
                effect_text = str(effects)
            conclusion = f"{y.get('name_cn') or y.get('name') or 'Yoga'}：{y.get('combination', '检测到相关组合')}"
            if effect_text:
                conclusion += f"；传统效应：{effect_text}"

            for theme in themes:
                if added_per_theme[theme] >= 8:
                    continue
                add(theme, ReportTechniqueResult(
                    technique=f"yoga:{y.get('rule_id') or y.get('name') or 'unknown'}",
                    chart="D1",
                    conclusion=conclusion,
                    sentiment=sentiment,
                    strength=strength,
                    details={"source_module": "yoga", "raw": y},
                ))
                added_per_theme[theme] += 1

    def _inject_varga_modules(self, modules: Dict[str, Any], add) -> None:
        d9 = modules.get("d9_navamsa_expanded") or {}
        if isinstance(d9, dict) and d9:
            asc = d9.get("Ascendant") or {}
            venus = d9.get("Venus") or {}
            jupiter = d9.get("Jupiter") or {}
            parts = []
            if asc:
                parts.append(f"D9上升落{asc.get('sign_cn') or asc.get('sign')}，主星{asc.get('lord', '未知')}")
            if venus:
                parts.append(f"Venus在D9落{venus.get('sign_cn') or venus.get('sign')}，尊严={venus.get('dignity', '未知')}")
            if jupiter:
                parts.append(f"Jupiter在D9落{jupiter.get('sign_cn') or jupiter.get('sign')}，尊严={jupiter.get('dignity', '未知')}")
            add(ThemeName.MARRIAGE, ReportTechniqueResult(
                technique="d9_navamsa_expanded",
                chart="D9",
                conclusion="；".join(parts[:3]) or "D9 Navamsa 已完成展开",
                sentiment=_sentiment_from_dignities([venus.get("dignity"), jupiter.get("dignity")]),
                strength=StrengthLevel.STRONG,
                details={"source_module": "d9_navamsa_expanded", "ascendant": asc, "venus": venus, "jupiter": jupiter},
            ))

        varga = modules.get("varga_full") or {}
        if not isinstance(varga, dict):
            return
        mapping = [
            ("D2_Hora", ThemeName.WEALTH, "D2", "Hora财富分盘"),
            ("D10_Dasamsa", ThemeName.CAREER, "D10", "Dashamsha事业分盘"),
            ("D20_Vimsamsa", ThemeName.SPIRITUALITY, "D20", "Vimsamsa灵性分盘"),
            ("D30_Trimsamsa", ThemeName.HEALTH, "D30", "Trimsamsa健康/灾厄分盘"),
            ("D60_Shashtyamsa", ThemeName.SPIRITUALITY, "D60", "Shashtyamsha业力分盘"),
        ]
        for key, theme, chart, label in mapping:
            data = varga.get(key) or {}
            if not isinstance(data, dict) or not data:
                continue
            asc = data.get("Ascendant") or {}
            dignity = data.get("_dignity") or {}
            strong = [p for p, d in dignity.items() if str(d).lower() in {"exalted", "own sign", "moolatrikona"}]
            weak = [p for p, d in dignity.items() if "debil" in str(d).lower()]
            conclusion = f"{label}：上升落{asc.get('sign', '未知')}；强势行星{strong[:3] or '未突出'}；需留意行星{weak[:3] or '无明显落陷'}"
            add(theme, ReportTechniqueResult(
                technique=f"varga_full:{key}",
                chart=chart,
                conclusion=conclusion,
                sentiment="positive" if len(strong) > len(weak) else ("negative" if weak else "neutral"),
                strength=StrengthLevel.STRONG,
                details={"source_module": "varga_full", "varga": key, "ascendant": asc, "dignity": dignity},
            ))

    def _inject_strength_modules(self, modules: Dict[str, Any], add) -> None:
        shadbala = modules.get("shadbala") or {}
        if isinstance(shadbala, dict) and shadbala:
            strongest = shadbala.get("strongest") or []
            weakest = shadbala.get("weakest") or []
            conclusion = f"Shadbala相对力量：最强={strongest}；最弱={weakest}。该模块当前用于相对强弱排序。"
            result = ReportTechniqueResult(
                technique="shadbala_relative_strength",
                chart="D1",
                conclusion=conclusion,
                sentiment="neutral",
                strength=StrengthLevel.MODERATE,
                details={"source_module": "shadbala", "strongest": strongest, "weakest": weakest, "status": shadbala.get("status")},
            )
            for theme in [ThemeName.CAREER, ThemeName.HEALTH, ThemeName.SPIRITUALITY]:
                add(theme, result)

        av = modules.get("ashtakavarga") or {}
        if isinstance(av, dict) and av:
            house_scores = av.get("house_scores") or av.get("house_scores_full") or {}
            wealth_scores = _pick_house_scores(house_scores, [2, 11])
            health_scores = _pick_house_scores(house_scores, [6, 8, 12])
            career_scores = _pick_house_scores(house_scores, [10])
            for theme, houses, label in [
                (ThemeName.WEALTH, wealth_scores, "2/11宫财富"),
                (ThemeName.HEALTH, health_scores, "6/8/12宫健康压力"),
                (ThemeName.CAREER, career_scores, "10宫事业"),
            ]:
                if not houses:
                    continue
                avg = sum(houses.values()) / len(houses)
                add(theme, ReportTechniqueResult(
                    technique=f"ashtakavarga:{label}",
                    chart="AV",
                    conclusion=f"Ashtakavarga {label}分值：{houses}，均值约{avg:.1f}",
                    sentiment="positive" if avg >= 28 else ("negative" if avg <= 24 else "neutral"),
                    strength=StrengthLevel.MODERATE,
                    details={"source_module": "ashtakavarga", "scores": houses},
                ))

    def _inject_special_points(self, modules: Dict[str, Any], add) -> None:
        special = modules.get("special_lagnas") or {}
        if isinstance(special, dict):
            upapada = special.get("Upapada_Lagna") or {}
            a10 = special.get("A10_Karma_Pada") or {}
            arudha = special.get("Arudha_Lagna") or {}
            if upapada:
                add(ThemeName.MARRIAGE, ReportTechniqueResult(
                    technique="special_lagnas:upapada_lagna",
                    chart="D1",
                    conclusion=f"Upapada Lagna落{upapada.get('sign', '未知')}第{upapada.get('house', '?')}宫，提示婚姻的社会呈现与伴侣形象。",
                    sentiment="neutral",
                    strength=StrengthLevel.STRONG,
                    details={"source_module": "special_lagnas", "upapada_lagna": upapada},
                ))
            if a10:
                add(ThemeName.CAREER, ReportTechniqueResult(
                    technique="special_lagnas:a10_karma_pada",
                    chart="D1",
                    conclusion=f"A10/Karma Pada落{a10.get('sign', '未知')}第{a10.get('house', '?')}宫，用于观察事业名声与业力方向。",
                    sentiment="neutral",
                    strength=StrengthLevel.STRONG,
                    details={"source_module": "special_lagnas", "a10_karma_pada": a10},
                ))
            if arudha:
                add(ThemeName.CAREER, ReportTechniqueResult(
                    technique="special_lagnas:arudha_lagna",
                    chart="D1",
                    conclusion=f"Arudha Lagna落{arudha.get('sign', '未知')}第{arudha.get('house', '?')}宫，显示公众形象与外界评价。",
                    sentiment="neutral",
                    strength=StrengthLevel.MODERATE,
                    details={"source_module": "special_lagnas", "arudha_lagna": arudha},
                ))

        vivah = modules.get("vivah_saham") or {}
        if isinstance(vivah, dict) and vivah:
            point = vivah.get("vivah_saham") or vivah
            add(ThemeName.MARRIAGE, ReportTechniqueResult(
                technique="vivah_saham",
                chart="Tajika",
                conclusion=f"Vivah Saham婚姻敏感点落{point.get('sign', vivah.get('saham_sign', '未知'))}第{point.get('house', vivah.get('saham_house', '?'))}宫；适合与Transit触发联合判断婚恋窗口。",
                sentiment="neutral",
                strength=StrengthLevel.MODERATE,
                details={"source_module": "vivah_saham", "raw": vivah},
            ))

    def _inject_dasa_convergence_module(self, modules: Dict[str, Any], add) -> None:
        convergence = modules.get("dasa_convergence") or {}
        if not isinstance(convergence, dict) or not convergence:
            return

        # 从 full-reading 的 Vimshottari current antar 注入真实时间锚，避免报告退回模拟 TimingAnchorBuilder。
        systems_summary = convergence.get("systems_summary") or {}
        vim = systems_summary.get("vimshottari") or {}
        antar = vim.get("antar") or {}
        if isinstance(antar, dict):
            start_year = _year_from_date(antar.get("start"), datetime.now().year)
            end_year = _year_from_date(antar.get("end"), start_year + 3)
            maha = vim.get("maha") or "Unknown"
            antar_lord = antar.get("lord") or "Unknown"
            anchor = TimingAnchor(
                dasha_period=f"Vimshottari-{maha}-{antar_lord}",
                start_year=start_year,
                end_year=end_year,
                activation_description="full-reading 五系统 Dasa Convergence 已完成，当前 Vimshottari 主/副运作为主题报告时间锚。",
                is_current=bool(antar.get("is_current", True)),
            )
            for tn in ThemeName:
                self.rpo.add_timing(tn, anchor)

        domain_map = {
            "marriage_partnership": ThemeName.MARRIAGE,
            "career_status": ThemeName.CAREER,
            "wealth_family": ThemeName.WEALTH,
            "health_service": ThemeName.HEALTH,
            "fortune_dharma": ThemeName.SPIRITUALITY,
            "transformation": ThemeName.SPIRITUALITY,
        }
        domains = convergence.get("domain_activations") or {}
        for domain, data in domains.items():
            theme = domain_map.get(domain)
            if not theme or not isinstance(data, dict):
                continue
            activations = data.get("activations") or []
            systems = sorted({a.get("system") for a in activations if isinstance(a, dict) and a.get("system")})
            conclusion = f"Dasa Convergence：{domain} 获得{data.get('system_count', len(systems))}个系统激活（{', '.join(systems) or '未列出'}），收敛等级{data.get('convergence_level', '未知')}，概率{data.get('probability', '未标注')}。"
            add(theme, ReportTechniqueResult(
                technique=f"dasa_convergence:{domain}",
                chart="Dasha",
                conclusion=conclusion,
                sentiment="positive" if data.get("system_count", 0) >= 2 else "neutral",
                strength=StrengthLevel.STRONG if data.get("system_count", 0) >= 3 else StrengthLevel.MODERATE,
                details={"source_module": "dasa_convergence", "domain": domain, "raw": data},
            ))

    def _inject_transit_module(self, modules: Dict[str, Any], add) -> None:
        transit = modules.get("transit_multi_reference") or {}
        if not isinstance(transit, dict) or not transit:
            return
        target_date = transit.get("target_date")
        analysis = transit.get("transit_analysis") or {}
        for planet in ["Jupiter", "Saturn", "Rahu", "Ketu"]:
            pdata = analysis.get(planet)
            if not isinstance(pdata, dict):
                continue
            house_map = pdata.get("house_from_ref") or {}
            lagna_house = (house_map.get("Lagna") or {}).get("house")
            if not lagna_house:
                continue
            themes = _themes_for_transit_house(int(lagna_house))
            for theme in themes:
                add(theme, ReportTechniqueResult(
                    technique=f"transit_multi_reference:{planet}",
                    chart="Transit",
                    conclusion=f"{target_date or '当前'}真实过境：{planet}从Lagna参考点落第{lagna_house}宫，并需结合Chandra/Arudha/Navamsa多参考点校验。",
                    sentiment="positive" if planet == "Jupiter" and lagna_house in [2, 5, 7, 9, 10, 11] else ("negative" if planet in ["Saturn", "Rahu", "Ketu"] and lagna_house in [6, 8, 12] else "neutral"),
                    strength=StrengthLevel.MODERATE,
                    details={"source_module": "transit_multi_reference", "planet": planet, "raw": pdata},
                ))

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

        # Step 0: 注入推运结果与 full-reading 真实模块（在所有主题分析之前）
        dasha_results = self.inject_dasha_results(chart_data)
        full_reading_injection = self.inject_full_reading_modules(chart_data)

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
            "full_reading_injection": full_reading_injection,
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

def _extract_modules(chart_data: Any) -> Dict[str, Any]:
    """Return full-reading modules from either a full report dict or a modules dict."""
    if not isinstance(chart_data, dict):
        return {}
    modules = chart_data.get("modules")
    if isinstance(modules, dict):
        return modules
    # Allow passing modules directly in tests.
    known = {
        "yoga", "varga_full", "d9_navamsa_expanded", "ashtakavarga", "shadbala",
        "special_lagnas", "vivah_saham", "dasa_convergence", "transit_multi_reference",
        "dasha", "yogini_dasha", "ashtottari_dasha", "kalachakra_dasha",
    }
    if any(k in chart_data for k in known):
        return chart_data
    return {}


def _strength_from_text(value: Any, default: StrengthLevel = StrengthLevel.MODERATE) -> StrengthLevel:
    text = str(value or "").lower()
    if any(x in text for x in ["强", "strong", "high", "极"]):
        return StrengthLevel.STRONG
    if any(x in text for x in ["弱", "weak", "low"]):
        return StrengthLevel.WEAK
    return default


def _sentiment_from_yoga(yoga: Dict[str, Any]) -> str:
    category = str(yoga.get("category") or yoga.get("name") or yoga.get("name_cn") or "").lower()
    negative_tokens = ["darid", "dharidhra", "kapata", "arista", "dosha", "curse", "poverty", "roga", "mrityu", "凶", "贫", "病", "灾", "欺"]
    positive_tokens = ["raja", "dhana", "lakshmi", "gaja", "kesari", "amala", "yoga", "财富", "王", "吉", "成就"]
    if any(t in category for t in negative_tokens):
        return "negative"
    if any(t in category for t in positive_tokens):
        return "positive"
    return "neutral"


def _themes_for_yoga(yoga: Dict[str, Any]) -> List[ThemeName]:
    text = " ".join(str(yoga.get(k, "")) for k in ["name", "name_cn", "category", "rule_id", "combination"])
    effects = yoga.get("effects") or []
    if isinstance(effects, list):
        text += " " + " ".join(str(e) for e in effects)
    lower = text.lower()
    themes: List[ThemeName] = []
    keyword_map = [
        (ThemeName.WEALTH, ["dhana", "lakshmi", "wealth", "money", "income", "财富", "财", "收入", "资源"]),
        (ThemeName.CAREER, ["raja", "career", "profession", "status", "authority", "power", "事业", "权力", "地位", "名声", "成就"]),
        (ThemeName.MARRIAGE, ["marriage", "spouse", "venus", "vivah", "partner", "婚", "配偶", "伴侣", "金星"]),
        (ThemeName.HEALTH, ["arista", "roga", "disease", "health", "illness", "saturn-mars", "病", "健康", "灾", "凶"]),
        (ThemeName.SPIRITUALITY, ["moksha", "jupiter", "ketu", "spiritual", "dharma", "智慧", "灵性", "木星", "解脱"]),
    ]
    for theme, keywords in keyword_map:
        if any(k in lower or k in text for k in keywords):
            themes.append(theme)
    if not themes and yoga.get("category") in ["raja", "bvr"]:
        themes.append(ThemeName.CAREER)
    return themes[:3]


def _sentiment_from_dignities(values: List[Any]) -> str:
    text = " ".join(str(v or "").lower() for v in values)
    if any(k in text for k in ["exalted", "own", "moola", "friend"]):
        return "positive"
    if any(k in text for k in ["debil", "enemy"]):
        return "negative"
    return "neutral"


def _pick_house_scores(house_scores: Any, houses: List[int]) -> Dict[int, float]:
    if not isinstance(house_scores, dict):
        return {}
    picked: Dict[int, float] = {}
    for house in houses:
        value = None
        for key in [house, str(house), f"house_{house}", f"H{house}"]:
            if key in house_scores:
                value = house_scores[key]
                break
        if isinstance(value, dict):
            value = value.get("score") or value.get("bindus") or value.get("sav")
        if isinstance(value, (int, float)):
            picked[house] = float(value)
    return picked


def _year_from_date(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and len(value) >= 4:
        try:
            return int(value[:4])
        except ValueError:
            return default
    return default


def _themes_for_transit_house(house: int) -> List[ThemeName]:
    mapping = {
        1: [ThemeName.HEALTH],
        2: [ThemeName.WEALTH],
        5: [ThemeName.WEALTH, ThemeName.SPIRITUALITY],
        6: [ThemeName.HEALTH, ThemeName.CAREER],
        7: [ThemeName.MARRIAGE],
        8: [ThemeName.HEALTH, ThemeName.SPIRITUALITY],
        9: [ThemeName.SPIRITUALITY, ThemeName.CAREER],
        10: [ThemeName.CAREER],
        11: [ThemeName.WEALTH, ThemeName.CAREER],
        12: [ThemeName.HEALTH, ThemeName.SPIRITUALITY],
    }
    return mapping.get(house, [])


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
    """演示桥接功能。

    默认使用 MockDataFactory；如果传入一个 full-reading JSON 路径，则直接消费
    `modules` 真实结果，验证 v6.1.8 的真实模块接线。
    """
    import sys
    from report_orchestrator import MockDataFactory

    # 创建星盘数据：优先使用 full-reading JSON，否则使用模拟数据
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            chart_data = json.load(f)
    else:
        chart_data = MockDataFactory.create_sample_chart()

    # 创建 orchestrators
    # NOTE: reading_orchestrator 需要 registry，这里用空 registry 演示；真实证据由 full-reading 注入层提供
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
