#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reading_orchestrator.py — 主题化解读编排器
===========================================
从"模块罗列"升级为"主题叙事"

核心能力：
1. 主题路由 — 根据用户问题选择分析主题
2. 技法编排 — 按优先级调用相关技法
3. 交叉验证 — 多维度矛盾裁决
4. 叙事生成 — 从数据生成连贯的人生故事

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ReadingTheme(Enum):
    """解读主题"""
    OVERVIEW = "overview"           # 生命概览
    MARRIAGE = "marriage"           # 婚姻情感
    CAREER = "career"               # 事业财富
    HEALTH = "health"               # 健康危机
    SPIRITUAL = "spiritual"         # 灵性成长
    WEALTH = "wealth"               # 财富积累
    TIMING = "timing"               # 时间预测
    RELATIONSHIP = "relationship"   # 人际关系
    EDUCATION = "education"         # 教育学习
    FAMILY = "family"               # 家庭父母


class ConflictResolution(Enum):
    """矛盾裁决策略"""
    D9_OVERRIDES = "d9_overrides"      # D9优先（婚姻/灵性）
    D1_OVERRIDES = "d1_overrides"      # D1优先（世俗事务）
    STRONGEST_WINS = "strongest_wins"  # 最强力量优先
    CONTEXTUAL = "contextual"          # 上下文叙事（推荐）
    ALL_VALID = "all_valid"            # 全部保留，标注差异


@dataclass
class ThemeConfig:
    """主题配置"""
    theme: ReadingTheme
    title: str                          # 主题标题
    description: str                    # 主题描述
    technique_chain: List[str]          # 技法调用链
    primary_varga: List[int]            # 主要分盘
    conflict_strategy: ConflictResolution  # 矛盾裁决策略
    narrative_template: str             # 叙事模板


@dataclass
class TechniqueResult:
    """技法计算结果包装"""
    technique_name: str
    technique_name_cn: str
    status: str                         # success / warning / error
    result: Dict[str, Any]
    interpretation: Optional[str] = None
    confidence: float = 0.5             # 置信度 0-1
    weight: float = 1.0                 # 在主题中的权重


@dataclass
class ConflictItem:
    """矛盾项"""
    dimension: str                      # 维度（如"婚姻质量"）
    d1_finding: str                     # D1发现
    d9_finding: str                     # D9发现
    other_findings: Dict[str, str]      # 其他分盘发现
    resolution: str                     # 裁决结果
    narrative: str                      # 叙事表达


@dataclass
class ReadingChapter:
    """报告章节"""
    title: str
    subtitle: str
    priority: int                       # 优先级（1最高）
    techniques_used: List[str]          # 使用的技法
    findings: List[str]                 # 核心发现
    conflicts: List[ConflictItem]       # 矛盾与裁决
    narrative: str                      # 叙事文本
    actionable: List[str]               # 行动建议
    timing: Optional[str] = None        # 时间锚定


class ReadingOrchestrator:
    """解读编排器"""
    
    def __init__(self, registry):
        self.registry = registry
        self._themes: Dict[ReadingTheme, ThemeConfig] = self._init_themes()
    
    def _init_themes(self) -> Dict[ReadingTheme, ThemeConfig]:
        """初始化主题配置"""
        return {
            ReadingTheme.OVERVIEW: ThemeConfig(
                theme=ReadingTheme.OVERVIEW,
                title="生命蓝图概览",
                description="从全局视角解读先天格局",
                technique_chain=[
                    "chart", "shadbala", "yoga", "karaka",
                    "nakshatra", "vimsopaka", "avastha"
                ],
                primary_varga=[1],
                conflict_strategy=ConflictResolution.ALL_VALID,
                narrative_template="overview"
            ),
            
            ReadingTheme.MARRIAGE: ThemeConfig(
                theme=ReadingTheme.MARRIAGE,
                title="婚姻与情感深度解析",
                description="从D1、D9、DK、Upapada多维度解读婚姻质量",
                technique_chain=[
                    "darakaraka",
                    "spouse_status_yoga",
                    "navamsa_analysis",
                    "rtn_mapping",
                    "vivah_saham",
                    "tithi_lord",
                    "mangal_dosha",
                    "synastry",
                    "upapada_lagna",
                    "dasha_marriage",
                    "transit_marriage"
                ],
                primary_varga=[1, 9],
                conflict_strategy=ConflictResolution.D9_OVERRIDES,
                narrative_template="marriage"
            ),
            
            ReadingTheme.CAREER: ThemeConfig(
                theme=ReadingTheme.CAREER,
                title="事业与社会成就",
                description="从D1、D10、AmK多维度解读事业轨迹",
                technique_chain=[
                    "amatyakaraka",
                    "dashamsa_analysis",
                    "d10_yoga",
                    "shadbala",
                    "ashtakavarga",
                    "tajika_varshaphala",
                    "dasha_career",
                    "transit_career"
                ],
                primary_varga=[1, 10],
                conflict_strategy=ConflictResolution.D1_OVERRIDES,
                narrative_template="career"
            ),
            
            ReadingTheme.HEALTH: ThemeConfig(
                theme=ReadingTheme.HEALTH,
                title="健康与生命危机",
                description="从D1、D30、凶星合相检测健康风险",
                technique_chain=[
                    "curse_yoga",
                    "trimshamsa",
                    "shadbala",
                    "avastha",
                    "drekkena",
                    "dasha_health",
                    "transit_health"
                ],
                primary_varga=[1, 30],
                conflict_strategy=ConflictResolution.STRONGEST_WINS,
                narrative_template="health"
            ),
            
            ReadingTheme.WEALTH: ThemeConfig(
                theme=ReadingTheme.WEALTH,
                title="财富与资源",
                description="从D1、D2、Dhana Yoga解读财富格局",
                technique_chain=[
                    "dhana_yoga",
                    "hora_analysis",
                    "dhanakaraka",
                    "vasihikamsa",
                    "ashtakavarga",
                    "dasha_wealth"
                ],
                primary_varga=[1, 2],
                conflict_strategy=ConflictResolution.D1_OVERRIDES,
                narrative_template="wealth"
            ),
            
            ReadingTheme.SPIRITUAL: ThemeConfig(
                theme=ReadingTheme.SPIRITUAL,
                title="灵性与灵魂成长",
                description="从AK、D20、Karakamsha解读灵性道路",
                technique_chain=[
                    "atmakaraka",
                    "karakamsha",
                    "vimsamsa",
                    "chara_dasha",
                    "nakshatra_deity",
                    "dasha_spiritual"
                ],
                primary_varga=[1, 9, 20],
                conflict_strategy=ConflictResolution.D9_OVERRIDES,
                narrative_template="spiritual"
            ),
            
            ReadingTheme.TIMING: ThemeConfig(
                theme=ReadingTheme.TIMING,
                title="时间预测",
                description="Dasha + Transit精准时间锚定",
                technique_chain=[
                    "dasha",
                    "transit",
                    "double_transit",
                    "tajika",
                    "gochara"
                ],
                primary_varga=[1],
                conflict_strategy=ConflictResolution.CONTEXTUAL,
                narrative_template="timing"
            ),
        }
    
    def analyze(self, chart_data: Dict, theme: ReadingTheme,
                question: Optional[str] = None) -> List[ReadingChapter]:
        """
        执行主题化分析
        
        Args:
            chart_data: 星盘数据
            theme: 分析主题
            question: 用户具体问题（可选）
        
        Returns:
            章节列表
        """
        config = self._themes.get(theme)
        if not config:
            return []
        
        chapters = []
        
        # Step 1: 执行技法链
        technique_results = []
        for tech_name in config.technique_chain:
            result = self._execute_technique(tech_name, chart_data)
            if result:
                technique_results.append(result)
        
        # Step 2: 生成核心发现
        findings = self._extract_findings(technique_results, config)
        
        # Step 3: 检测矛盾
        conflicts = self._detect_conflicts(technique_results, config)
        
        # Step 4: 裁决矛盾
        resolved_conflicts = self._resolve_conflicts(conflicts, config)
        
        # Step 5: 生成叙事
        narrative = self._generate_narrative(findings, resolved_conflicts, config, question)
        
        # Step 6: 生成行动建议
        actionable = self._generate_actionable(findings, resolved_conflicts, config)
        
        # Step 7: 时间锚定
        timing = self._generate_timing(technique_results, config)
        
        # 组装章节
        chapter = ReadingChapter(
            title=config.title,
            subtitle=config.description,
            priority=1,
            techniques_used=[r.technique_name for r in technique_results if r.status == "success"],
            findings=findings,
            conflicts=resolved_conflicts,
            narrative=narrative,
            actionable=actionable,
            timing=timing
        )
        chapters.append(chapter)
        
        return chapters
    
    def _execute_technique(self, name: str, chart_data: Dict) -> Optional[TechniqueResult]:
        """执行单个技法"""
        spec = self.registry.get(name)
        if not spec:
            return None
        
        # 如果技法状态是PLANNED，返回占位
        if spec.status.value == "planned":
            return TechniqueResult(
                technique_name=name,
                technique_name_cn=spec.name_cn,
                status="planned",
                result={},
                interpretation=f"[{spec.name_cn}] 技法开发中，将在后续版本中提供。",
                confidence=0.0
            )
        
        # 执行计算
        try:
            result = self.registry.compute(name, chart_data)
            if result is None:
                return None
            
            # 获取解读
            interpretation = self.registry.interpret(name, result)
            
            # 评估置信度
            confidence = self._assess_confidence(result, spec)
            
            return TechniqueResult(
                technique_name=name,
                technique_name_cn=spec.name_cn,
                status="success",
                result=result,
                interpretation=interpretation,
                confidence=confidence
            )
        except Exception as e:
            return TechniqueResult(
                technique_name=name,
                technique_name_cn=spec.name_cn if spec else name,
                status="error",
                result={"error": str(e)},
                confidence=0.0
            )
    
    def _assess_confidence(self, result: Dict, spec) -> float:
        """评估结果置信度"""
        # 基础置信度
        confidence = 0.5
        
        # 如果有明确检测结果，提高置信度
        if result.get("detected") or result.get("present"):
            confidence += 0.2
        
        # 如果有多个支持证据
        evidence_count = len(result.get("evidence", []))
        confidence += min(evidence_count * 0.05, 0.2)
        
        # 如果技法是STABLE状态
        if spec and spec.status.value == "stable":
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_findings(self, results: List[TechniqueResult], 
                         config: ThemeConfig) -> List[str]:
        """提取核心发现"""
        findings = []
        
        for r in results:
            if r.status != "success":
                continue
            
            # 从结果中提取关键发现
            result = r.result
            
            # Yoga检测类
            if "yogas" in result:
                yogas = result["yogas"]
                if yogas:
                    findings.append(f"检测到 {len(yogas)} 个相关Yoga: {', '.join([y.get('name','') for y in yogas[:3]])}")
            
            # 力量评估类
            if "score" in result:
                score = result["score"]
                if isinstance(score, (int, float)) and score > 0.7:
                    findings.append(f"{r.technique_name_cn}得分较高 ({score:.2f})，显示此领域有显著影响")
            
            # 相位/合相类
            if "conjunctions" in result:
                conj = result["conjunctions"]
                if conj:
                    findings.append(f"发现关键合相: {', '.join([str(c) for c in conj[:2]])}")
            
            # 解读文本
            if r.interpretation:
                findings.append(r.interpretation)
        
        # 去重并排序（按置信度）
        seen = set()
        unique = []
        for f in findings:
            if f and f not in seen:
                seen.add(f)
                unique.append(f)
        
        return unique[:7]  # 最多7条核心发现
    
    def _detect_conflicts(self, results: List[TechniqueResult],
                         config: ThemeConfig) -> List[ConflictItem]:
        """检测多维度矛盾"""
        conflicts = []
        
        # 按分盘分组
        d1_results = [r for r in results if "d1" in r.technique_name or r.technique_name in ["chart", "yoga"]]
        d9_results = [r for r in results if "navamsa" in r.technique_name or r.technique_name == "rtn_mapping"]
        
        # 简单示例：D1和D9的婚姻判断矛盾
        d1_marriage = self._extract_marriage_signal(d1_results)
        d9_marriage = self._extract_marriage_signal(d9_results)
        
        if d1_marriage and d9_marriage and d1_marriage != d9_marriage:
            conflicts.append(ConflictItem(
                dimension="婚姻质量",
                d1_finding=d1_marriage,
                d9_finding=d9_marriage,
                other_findings={},
                resolution="待裁决",
                narrative=""
            ))
        
        return conflicts
    
    def _extract_marriage_signal(self, results: List[TechniqueResult]) -> str:
        """从结果中提取婚姻信号"""
        # 简化实现
        positive = sum(1 for r in results if r.confidence > 0.6)
        negative = sum(1 for r in results if r.confidence < 0.4)
        
        if positive > negative:
            return "有利"
        elif negative > positive:
            return "有挑战"
        return "中性"
    
    def _resolve_conflicts(self, conflicts: List[ConflictItem],
                          config: ThemeConfig) -> List[ConflictItem]:
        """裁决矛盾"""
        resolved = []
        
        for c in conflicts:
            strategy = config.conflict_strategy
            
            if strategy == ConflictResolution.D9_OVERRIDES:
                winner = c.d9_finding
                reason = "Navamsa (D9) 在婚姻分析中具有最高权威"
            elif strategy == ConflictResolution.D1_OVERRIDES:
                winner = c.d1_finding
                reason = "本命盘 (D1) 在世俗事务中具有最高权威"
            elif strategy == ConflictResolution.STRONGEST_WINS:
                # 这里简化处理，实际应比较力量
                winner = c.d9_finding if len(c.d9_finding) > len(c.d1_finding) else c.d1_finding
                reason = "基于力量评估的综合判断"
            elif strategy == ConflictResolution.CONTEXTUAL:
                winner = f"表面{c.d1_finding}，但深层{c.d9_finding}"
                reason = "需要结合具体情境综合判断"
            else:
                winner = f"D1: {c.d1_finding}, D9: {c.d9_finding}"
                reason = "两种可能性并存"
            
            c.resolution = winner
            c.narrative = self._conflict_to_narrative(c, reason)
            resolved.append(c)
        
        return resolved
    
    def _conflict_to_narrative(self, conflict: ConflictItem, reason: str) -> str:
        """将矛盾转换为叙事"""
        if conflict.dimension == "婚姻质量":
            if "有利" in conflict.resolution and "挑战" in conflict.resolution:
                return f"婚姻表面看起来顺利，但深层存在需要关注的议题。{reason}。"
            return f"{conflict.resolution}。{reason}。"
        return f"{conflict.resolution}。{reason}。"
    
    def _generate_narrative(self, findings: List[str], 
                           conflicts: List[ConflictItem],
                           config: ThemeConfig,
                           question: Optional[str]) -> str:
        """生成主题叙事文本"""
        parts = []
        
        # 开场
        parts.append(f"## {config.title}\n")
        parts.append(f"{config.description}\n")
        
        # 核心发现
        if findings:
            parts.append("### 核心发现\n")
            for i, f in enumerate(findings, 1):
                parts.append(f"{i}. {f}\n")
        
        # 矛盾与裁决
        if conflicts:
            parts.append("\n### 深层洞察\n")
            for c in conflicts:
                parts.append(f"\n{c.narrative}\n")
        
        # 回应问题
        if question:
            parts.append(f"\n### 关于您的问题\n")
            parts.append(f"针对「{question}」，综合以上分析：\n")
            # 这里可以接入AI生成更具体的回答
        
        return "\n".join(parts)
    
    def _generate_actionable(self, findings: List[str],
                            conflicts: List[ConflictItem],
                            config: ThemeConfig) -> List[str]:
        """生成行动建议"""
        actionable = []
        
        if config.theme == ReadingTheme.MARRIAGE:
            actionable.extend([
                "关注Navamsa中7宫主星的状态，这是婚姻质量的核心指标",
                "在DK激活的Dasha周期特别注意关系维护",
                "如果Mangal Dosha存在，考虑传统补救措施"
            ])
        elif config.theme == ReadingTheme.CAREER:
            actionable.extend([
                "在AmK相关的Dasha周期积极寻求事业突破",
                "关注D10中10宫主星与Lagna的相位",
                "利用Double Transit激活期推进重要项目"
            ])
        elif config.theme == ReadingTheme.HEALTH:
            actionable.extend([
                "定期进行健康检查，特别是6宫和8宫相关的身体部位",
                "在凶星Dasha周期特别注意安全",
                "考虑传统 Ayurveda 调理"
            ])
        
        return actionable
    
    def _generate_timing(self, results: List[TechniqueResult],
                        config: ThemeConfig) -> Optional[str]:
        """生成时间锚定"""
        # 从Dasha和Transit结果中提取时间信息
        timing_parts = []
        
        for r in results:
            if "dasha" in r.technique_name and r.result:
                current = r.result.get("current", {})
                if current:
                    timing_parts.append(f"当前处于 {current.get('lord', '?')} 大运")
        
        if timing_parts:
            return "; ".join(timing_parts)
        return None
    
    def generate_full_report(self, chart_data: Dict, 
                            themes: Optional[List[ReadingTheme]] = None) -> Dict:
        """
        生成完整报告
        
        Args:
            chart_data: 星盘数据
            themes: 要分析的主题列表（None=全部）
        
        Returns:
            结构化报告
        """
        if themes is None:
            themes = [ReadingTheme.OVERVIEW, ReadingTheme.MARRIAGE, 
                     ReadingTheme.CAREER, ReadingTheme.HEALTH]
        
        report = {
            "version": "2.0-theme-based",
            "themes_analyzed": [],
            "chapters": [],
            "summary": "",
            "missing_techniques": []
        }
        
        for theme in themes:
            chapters = self.analyze(chart_data, theme)
            report["chapters"].extend(chapters)
            report["themes_analyzed"].append(theme.value)
            
            # 记录缺失的技法
            config = self._themes.get(theme)
            if config:
                for tech_name in config.technique_chain:
                    spec = self.registry.get(tech_name)
                    if spec and spec.status.value == "planned":
                        report["missing_techniques"].append({
                            "name": tech_name,
                            "name_cn": spec.name_cn,
                            "theme": theme.value
                        })
        
        # 去重缺失技法
        seen = set()
        unique_missing = []
        for m in report["missing_techniques"]:
            if m["name"] not in seen:
                seen.add(m["name"])
                unique_missing.append(m)
        report["missing_techniques"] = unique_missing
        
        # 生成总摘要
        report["summary"] = self._generate_summary(report["chapters"])
        
        return report
    
    def _generate_summary(self, chapters: List[ReadingChapter]) -> str:
        """生成报告总摘要"""
        parts = ["# 印度占星综合解读报告\n"]
        
        for ch in chapters:
            parts.append(f"\n## {ch.title}\n")
            if ch.findings:
                parts.append("关键发现: " + "; ".join(ch.findings[:3]) + "\n")
            if ch.timing:
                parts.append(f"时间锚定: {ch.timing}\n")
        
        return "\n".join(parts)


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    from technique_registry import registry
    
    print("=" * 60)
    print("主题化解读编排器")
    print("=" * 60)
    
    orchestrator = ReadingOrchestrator(registry)
    
    # 模拟星盘数据
    mock_chart = {
        "ascendant": {"sign": "Aries", "degree": 15.5},
        "planets": {
            "Sun": {"sign": "Aries", "degree": 20.0, "house": 1},
            "Moon": {"sign": "Taurus", "degree": 10.0, "house": 2},
        }
    }
    
    # 生成婚姻主题报告
    print("\n--- 婚姻主题分析 ---\n")
    chapters = orchestrator.analyze(mock_chart, ReadingTheme.MARRIAGE)
    for ch in chapters:
        print(ch.narrative)
        print(f"\n使用技法: {', '.join(ch.techniques_used)}")
        print(f"行动建议: {ch.actionable}")
    
    # 生成完整报告
    print("\n" + "=" * 60)
    print("完整报告预览")
    print("=" * 60)
    
    report = orchestrator.generate_full_report(mock_chart)
    print(f"\n分析主题: {report['themes_analyzed']}")
    print(f"章节数: {len(report['chapters'])}")
    print(f"\n待开发技法:")
    for m in report['missing_techniques'][:10]:
        print(f"  - {m['name_cn']} ({m['name']})")
