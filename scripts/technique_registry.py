#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
technique_registry.py — 印度占星技法注册中心
================================================
让所有技法模块可独立开发、独立注册、独立验证。
支持并行推进：路线A(6模块) + 路线B(全覆盖) + 路线C(Yoga精度)

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import inspect


class TechniqueLevel(Enum):
    """技法层级"""
    L1_COMPUTE = "L1"      # 基础计算
    L2_STANDARD = "L2"     # 标准技法
    L3_ADVANCED = "L3"     # 高级技法
    L4_ESOTERIC = "L4"     # 秘传技法


class TechniqueCategory(Enum):
    """技法分类"""
    NATAL = "natal"                    # 本命分析
    DASHA = "dasha"                    # 推运系统
    TRANSIT = "transit"                # 流年系统
    MUHURTA = "muhurta"                # 择时系统
    PRASHNA = "prashna"                # 问事系统
    SYNASTRY = "synastry"              # 合盘系统
    TAJIKA = "tajika"                  # Tajika年运
    READING = "reading"                # 报告解读


class TechniqueStatus(Enum):
    """技法状态"""
    PLANNED = "planned"                # 计划中
    WIP = "wip"                        # 开发中
    ALPHA = "alpha"                    # 内测
    BETA = "beta"                      # 公测
    STABLE = "stable"                  # 稳定
    DEPRECATED = "deprecated"          # 废弃


@dataclass
class TechniqueSpec:
    """技法规格定义"""
    # 基础信息
    name: str                          # 英文名称
    name_cn: str                       # 中文名称
    category: TechniqueCategory        # 分类
    level: TechniqueLevel              # 层级
    status: TechniqueStatus            # 状态
    
    # 依赖关系
    depends_on: List[str] = field(default_factory=list)  # 依赖的其他技法名
    requires_varga: List[int] = field(default_factory=list)  # 需要的分盘
    
    # 接口定义
    input_schema: Dict[str, Any] = field(default_factory=dict)   # 输入参数定义
    output_schema: Dict[str, Any] = field(default_factory=dict)  # 输出结构定义
    
    # 实现信息
    module_path: str = ""              # 实现模块路径
    compute_func: Optional[str] = None # 计算函数名
    interpret_func: Optional[str] = None # 解读函数名
    
    # 验证信息
    validation_cases: List[Dict] = field(default_factory=list)   # 验证用例
    precision_target: Optional[float] = None  # 精度目标(如F1)
    
    # 元数据
    description: str = ""              # 描述
    references: List[str] = field(default_factory=list)  # 参考文档
    author: str = ""                   # 作者
    version: str = "0.1.0"             # 版本


class TechniqueRegistry:
    """技法注册中心 — 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._techniques: Dict[str, TechniqueSpec] = {}
            cls._instance._compute_funcs: Dict[str, Callable] = {}
            cls._instance._interpret_funcs: Dict[str, Callable] = {}
        return cls._instance
    
    def register(self, spec: TechniqueSpec, 
                 compute_func: Optional[Callable] = None,
                 interpret_func: Optional[Callable] = None) -> bool:
        """
        注册一个技法
        
        Args:
            spec: 技法规格
            compute_func: 计算函数 (chart_data -> result)
            interpret_func: 解读函数 (result -> interpretation)
        
        Returns:
            bool: 是否注册成功
        """
        name = spec.name
        
        # 检查依赖是否满足
        for dep in spec.depends_on:
            if dep not in self._techniques:
                print(f"[WARN] 技法 '{name}' 的依赖 '{dep}' 尚未注册")
        
        self._techniques[name] = spec
        
        if compute_func:
            self._compute_funcs[name] = compute_func
        if interpret_func:
            self._interpret_funcs[name] = interpret_func
        
        print(f"[REG] 已注册: {name} ({spec.name_cn}) [{spec.status.value}]")
        return True
    
    def get(self, name: str) -> Optional[TechniqueSpec]:
        """获取技法规格"""
        return self._techniques.get(name)
    
    def compute(self, name: str, chart_data: Dict, **kwargs) -> Optional[Dict]:
        """
        执行技法计算
        
        Args:
            name: 技法名称
            chart_data: 星盘数据 (标准格式)
            **kwargs: 额外参数
        
        Returns:
            计算结果，或None（未找到/未实现）
        """
        spec = self._techniques.get(name)
        if not spec:
            print(f"[ERR] 技法 '{name}' 未注册")
            return None
        
        func = self._compute_funcs.get(name)
        if not func:
            print(f"[ERR] 技法 '{name}' 的计算函数未注册")
            return None
        
        try:
            # 自动注入chart_data
            sig = inspect.signature(func)
            if 'chart_data' in sig.parameters:
                return func(chart_data=chart_data, **kwargs)
            else:
                return func(**kwargs)
        except Exception as e:
            print(f"[ERR] 技法 '{name}' 计算失败: {e}")
            return {"error": str(e), "technique": name}
    
    def interpret(self, name: str, result: Dict, **kwargs) -> Optional[str]:
        """执行技法解读"""
        func = self._interpret_funcs.get(name)
        if not func:
            return None
        
        try:
            return func(result=result, **kwargs)
        except Exception as e:
            print(f"[ERR] 技法 '{name}' 解读失败: {e}")
            return None
    
    def list_all(self, category: Optional[TechniqueCategory] = None,
                 level: Optional[TechniqueLevel] = None,
                 status: Optional[TechniqueStatus] = None) -> List[TechniqueSpec]:
        """列出技法，支持过滤"""
        results = []
        for spec in self._techniques.values():
            if category and spec.category != category:
                continue
            if level and spec.level != level:
                continue
            if status and spec.status != status:
                continue
            results.append(spec)
        return sorted(results, key=lambda x: (x.category.value, x.level.value, x.name))
    
    def get_coverage_stats(self) -> Dict:
        """获取覆盖度统计"""
        stats = {
            "total": len(self._techniques),
            "by_category": {},
            "by_level": {},
            "by_status": {},
            "coverage_pct": {}
        }
        
        for spec in self._techniques.values():
            cat = spec.category.value
            lvl = spec.level.value
            st = spec.status.value
            
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            stats["by_level"][lvl] = stats["by_level"].get(lvl, 0) + 1
            stats["by_status"][st] = stats["by_status"].get(st, 0) + 1
        
        # 计算各分类的stable覆盖率
        for cat in stats["by_category"]:
            total = stats["by_category"][cat]
            stable = sum(1 for s in self._techniques.values() 
                        if s.category.value == cat and s.status == TechniqueStatus.STABLE)
            stats["coverage_pct"][cat] = round(stable / total * 100, 1) if total > 0 else 0
        
        return stats
    
    def get_reading_chain(self, theme: str) -> List[str]:
        """
        获取主题解读链 — 用于主题化报告
        
        Args:
            theme: 主题名称 (marriage/career/health/spiritual/wealth)
        
        Returns:
            按优先级排序的技法名称列表
        """
        chains = {
            "marriage": [
                "darakaraka",           # DK配偶解读
                "spouse_status_yoga",   # 高地位配偶
                "navamsa_analysis",     # D9分析
                "rtn_mapping",          # RTN映射
                "vivah_saham",          # 婚姻Saham
                "tithi_lord",           # Tithi主星
                "mangal_dosha",         # 火星凶星
                "synastry",             # 合盘
                "upapada_lagna",        # 婚姻上升
            ],
            "career": [
                "amatyakaraka",         # 事业象征
                "dashamsa_analysis",    # D10分析
                "d10_yoga",             # D10 Yoga
                "shadbala",             # 力量评估
                "ashtakavarga",         # 八点分
                "tajika_varshaphala",   # 年运
                "dasha_career",         # 事业推运
            ],
            "health": [
                "curse_yoga",           # 凶星合相
                "trimshamsa",           # D30
                "shadbala",             # 力量
                "avastha",              # 行星状态
                "drekkena",             # D3
                "dasha_health",         # 健康推运
            ],
            "wealth": [
                "dhana_yoga",           # 财组合
                "hora_analysis",        # D2
                "dhanakaraka",          # 财富象征
                "vasihikamsa",          # 特殊分
                "ashtakavarga",         # 八点分
            ],
            "spiritual": [
                "atmakaraka",           # 灵魂象征
                "karakamsha",           # AK星座
                "vimsamsa",             # D20
                "chara_dasha",          # Jaimini推运
                "nakshatra_deity",      # 星宿神祇
            ],
        }
        return chains.get(theme, [])


# ============================================================================
# 全局注册实例
# ============================================================================

registry = TechniqueRegistry()


# ============================================================================
# 便捷注册装饰器
# ============================================================================

def technique(spec: TechniqueSpec):
    """技法注册装饰器
    
    用法:
        @technique(TechniqueSpec(
            name="darakaraka",
            name_cn="配偶象征星解读",
            category=TechniqueCategory.NATAL,
            level=TechniqueLevel.L3_ADVANCED,
            status=TechniqueStatus.WIP,
            description="Darakaraka深度解读",
        ))
        def compute_darakaraka(chart_data, **kwargs):
            ...
    """
    def decorator(func):
        # 判断是计算函数还是解读函数
        if spec.compute_func is None:
            spec.compute_func = func.__name__
            registry.register(spec, compute_func=func)
        else:
            registry.register(spec, interpret_func=func)
        return func
    return decorator


# ============================================================================
# 现有技法批量注册（已有模块）
# ============================================================================

def _register_existing_techniques():
    """注册引擎中已实现的技法"""
    
    existing = [
        # L1 基础计算
        TechniqueSpec("chart", "本命星盘", TechniqueCategory.NATAL, 
                     TechniqueLevel.L1_COMPUTE, TechniqueStatus.STABLE,
                     module_path="jyotish_engine.py", compute_func="cmd_chart"),
        TechniqueSpec("varga", "分盘计算", TechniqueCategory.NATAL,
                     TechniqueLevel.L1_COMPUTE, TechniqueStatus.STABLE,
                     module_path="varga.py", compute_func="calc_all_vargas"),
        TechniqueSpec("dasha", "Vimshottari推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L1_COMPUTE, TechniqueStatus.STABLE,
                     module_path="dasha_calculator.py", compute_func="calculate_mahadasha"),
        
        # L2 标准技法
        TechniqueSpec("yoga", "Yoga组合检测", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.BETA,
                     module_path="yoga_engine.py", compute_func="cmd_yoga",
                     precision_target=0.95),
        TechniqueSpec("shadbala", "六重力量", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="shadbala.py", compute_func="calc_shadbala"),
        TechniqueSpec("ashtakavarga", "八点分", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="ashtakavarga.py", compute_func="calc_ashtakavarga"),
        TechniqueSpec("aspects", "相位系统", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="aspects.py", compute_func="calc_all_aspects"),
        TechniqueSpec("argala", "Argala阻碍", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="argala.py", compute_func="calc_argala"),
        TechniqueSpec("karaka", "象征星计算", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="karaka_calculator.py", compute_func="calculate_karaka"),
        TechniqueSpec("nakshatra", "星宿系统", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="nakshatra_advanced.py", compute_func="find_nakshatra"),
        TechniqueSpec("avastha", "行星状态", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="avastha_calculator.py"),
        TechniqueSpec("jaimini", "Jaimini系统", TechniqueCategory.NATAL,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.BETA,
                     module_path="jaimini.py", compute_func="calc_chara_karaka_7"),
        TechniqueSpec("tajika", "Tajika年运", TechniqueCategory.TAJIKA,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.BETA,
                     module_path="tajika.py", compute_func="calc_varshaphala"),
        TechniqueSpec("transit", "流年推运", TechniqueCategory.TRANSIT,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="transit.py", compute_func="computeTransit"),
        TechniqueSpec("synastry", "合盘系统", TechniqueCategory.SYNASTRY,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.STABLE,
                     module_path="synastry.py", compute_func="calc_synastry"),
        TechniqueSpec("prashna", "问事系统", TechniqueCategory.PRASHNA,
                     TechniqueLevel.L2_STANDARD, TechniqueStatus.BETA,
                     module_path="prashna.py", compute_func="cast_prashna"),
        
        # L3 高级技法（部分已有）
        TechniqueSpec("vimsopaka", "20分力量", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.STABLE,
                     module_path="vimsopaka_calculator.py"),
        TechniqueSpec("special_lagnas", "特殊上升", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.BETA,
                     module_path="special_lagnas.py"),
        TechniqueSpec("event_prediction", "事件预测", TechniqueCategory.READING,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="event_prediction_model.py"),
    ]
    
    for spec in existing:
        registry.register(spec)
    
    # 注册新开发模块（v6.1.0 — 6大缺失模块）
    new_modules = [
        TechniqueSpec("darakaraka", "配偶象征星深度解读", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="darakaraka_reader.py", compute_func="analyze_darakaraka",
                     depends_on=["karaka", "navamsa"]),
        TechniqueSpec("rtn_mapping", "RTN映射", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="rashi_tulya_navamsa.py", compute_func="analyze_rtn",
                     depends_on=["varga"], requires_varga=[9]),
        TechniqueSpec("curse_yoga", "凶星合相命名", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="curse_yoga_detector.py", compute_func="detect_curse_yogas",
                     depends_on=["yoga", "aspects"]),
        TechniqueSpec("spouse_status_yoga", "高地位配偶Yoga", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="spouse_status_yoga.py", compute_func="analyze_spouse_status",
                     depends_on=["navamsa", "shadbala"]),
        TechniqueSpec("pancha_pakshi", "五鸟择时", TechniqueCategory.MUHURTA,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="pancha_pakshi.py", compute_func="get_pancha_pakshi_schedule",
                     depends_on=["nakshatra"]),
        TechniqueSpec("tithi_lord", "Tithi主星", TechniqueCategory.NATAL,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.ALPHA,
                     module_path="tithi_analyzer.py", compute_func="analyze_tithi",
                     depends_on=["chart"]),
        
        # 更多计划中的技法（路线B）
        TechniqueSpec("chara_dasha", "Jaimini Chara推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.PLANNED,
                     depends_on=["jaimini"]),
        TechniqueSpec("ashtottari_dasha", "Ashtottari推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.PLANNED),
        TechniqueSpec("yogini_dasha", "Yogini推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L3_ADVANCED, TechniqueStatus.PLANNED),
        TechniqueSpec("kalachakra_dasha", "Kalachakra推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L4_ESOTERIC, TechniqueStatus.PLANNED),
        TechniqueSpec("narayana_dasha", "Narayana推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L4_ESOTERIC, TechniqueStatus.PLANNED),
        TechniqueSpec("moola_dasha", "Moola推运", TechniqueCategory.DASHA,
                     TechniqueLevel.L4_ESOTERIC, TechniqueStatus.PLANNED),
    ]
    
    for spec in new_modules:
        registry.register(spec)
    
    print(f"\n[REGISTRY] 总计注册技法: {len(registry._techniques)} 个")
    print(f"[REGISTRY] 其中 STABLE: {sum(1 for s in registry._techniques.values() if s.status == TechniqueStatus.STABLE)} 个")
    print(f"[REGISTRY] 其中 PLANNED: {sum(1 for s in registry._techniques.values() if s.status == TechniqueStatus.PLANNED)} 个")


# 启动时自动注册
_register_existing_techniques()


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("印度占星技法注册中心")
    print("=" * 60)
    
    stats = registry.get_coverage_stats()
    print(f"\n总技法数: {stats['total']}")
    print(f"\n按分类:")
    for cat, count in sorted(stats['by_category'].items()):
        pct = stats['coverage_pct'].get(cat, 0)
        print(f"  {cat:12s}: {count:3d} 个 (stable覆盖率: {pct}%)")
    
    print(f"\n按层级:")
    for lvl, count in sorted(stats['by_level'].items()):
        print(f"  {lvl}: {count:3d} 个")
    
    print(f"\n按状态:")
    for st, count in sorted(stats['by_status'].items()):
        print(f"  {st:12s}: {count:3d} 个")
    
    print("\n" + "=" * 60)
    print("婚姻主题解读链:")
    for i, t in enumerate(registry.get_reading_chain("marriage"), 1):
        spec = registry.get(t)
        status = spec.status.value if spec else "?"
        print(f"  {i}. {t:25s} [{status}]")
