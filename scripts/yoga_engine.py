#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yoga 规则引擎 v1.0 (数据驱动架构)
从 JSON 规则配置中读取 Yoga 定义，通用条件解释器执行检测。

设计原则:
- 规则完全数据驱动，加新 Yoga 只需改 JSON
- 条件类型可扩展，覆盖 BPHS/PyJHora 主流 Yoga 模式
- 与原 cmd_yoga() API 兼容
"""

import ast
import json
import os
from typing import Dict, List, Any, Optional

# ============================================================================
# 基础常量（自包含，避免循环导入）
# ============================================================================
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}
EXALTATION = {
    'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn', 'Mercury': 'Virgo',
    'Jupiter': 'Cancer', 'Venus': 'Pisces', 'Saturn': 'Libra'
}
DEBILITATION = {
    'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer', 'Mercury': 'Pisces',
    'Jupiter': 'Capricorn', 'Venus': 'Virgo', 'Saturn': 'Aries'
}
MOOLATRIKONA_SIGN = {
    'Sun': 'Leo', 'Moon': 'Taurus', 'Mars': 'Aries', 'Mercury': 'Virgo',
    'Jupiter': 'Sagittarius', 'Venus': 'Libra', 'Saturn': 'Aquarius'
}
# PyJHora const.friendly_planets mapped from planet ids to names.
FRIENDLY_PLANETS = {
    'Sun': ['Moon', 'Mars', 'Jupiter'],
    'Moon': ['Sun', 'Mercury'],
    'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'],
    'Jupiter': ['Sun', 'Moon', 'Mars'],
    'Venus': ['Mercury', 'Saturn', 'Rahu'],
    'Saturn': ['Mercury', 'Venus', 'Rahu'],
    'Rahu': ['Venus', 'Saturn'],
    'Ketu': ['Sun', 'Mars'],
}
PLANET_CN = {
    "Ketu": "南交点Ketu", "Venus": "金星Venus", "Sun": "太阳Sun",
    "Moon": "月亮Moon", "Mars": "火星Mars", "Rahu": "北交点Rahu",
    "Jupiter": "木星Jupiter", "Saturn": "土星Saturn", "Mercury": "水星Mercury"
}
BENEFICS = ['Jupiter', 'Venus', 'Mercury', 'Moon']
MALEFICS = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu']
MOVABLE_SIGNS = ['Aries', 'Cancer', 'Libra', 'Capricorn']
FIXED_SIGNS = ['Taurus', 'Leo', 'Scorpio', 'Aquarius']
DUAL_SIGNS = ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
ALL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
PLANET_INDEX = {planet: idx for idx, planet in enumerate(ALL_PLANETS)}
RAHU_KETU_OWNED_SIGN_INDEX = {'Rahu': 10, 'Ketu': 7}
# PyJHora const.house_strengths_of_planets, copied to make Yoga rule alignment deterministic.
# Strength scale: 5 own/lord, 4 exalted, 3 friend, 2 neutral, 1 enemy, 0 debilitated.
HOUSE_STRENGTHS = {
    'Sun':     [4, 1, 2, 2, 5, 2, 0, 3, 3, 1, 1, 3],
    'Moon':    [2, 4, 3, 5, 3, 3, 2, 0, 2, 2, 2, 2],
    'Mars':    [5, 2, 1, 0, 3, 1, 2, 5, 3, 4, 2, 3],
    'Mercury': [2, 3, 5, 1, 3, 5, 3, 2, 2, 2, 2, 0],
    'Jupiter': [3, 1, 1, 4, 3, 3, 1, 3, 5, 0, 2, 5],
    'Venus':   [2, 5, 3, 1, 1, 0, 5, 2, 3, 3, 3, 4],
    'Saturn':  [0, 3, 3, 1, 1, 3, 4, 1, 2, 5, 5, 2],
    'Rahu':    [1, 4, 4, 1, 1, 3, 3, 0, 0, 3, 1, 3],
    'Ketu':    [1, 0, 0, 1, 1, 3, 3, 4, 4, 3, 1, 3],
}


def _get_dignity_level(planet: str, sign: str) -> str:
    """判断行星在某星座的尊严等级"""
    if EXALTATION.get(planet) == sign:
        return 'EXALTED'
    if SIGN_LORDS.get(sign) == planet:
        return 'OWN_SIGN'
    if MOOLATRIKONA_SIGN.get(planet) == sign:
        return 'MOOLATRIKONA'
    if DEBILITATION.get(planet) == sign:
        return 'DEBILITATED'
    return 'NEUTRAL'


# ============================================================================
# YogaContext: 封装星盘数据，提供查询接口
# ============================================================================
class YogaContext:
    """Yoga 检测上下文。封装行星数据并提供各类查询方法。"""

    def __init__(self, planets: Dict[str, Dict], ascendant: str, context: Optional[Dict] = None):
        self.planets = planets  # name -> {sign, house, degree, ...}
        self.ascendant = ascendant
        self.asc_idx = SIGNS.index(ascendant) if ascendant in SIGNS else 0
        self.context = context or {}
        self.d9 = self.context.get("d9", {}) if isinstance(self.context, dict) else {}
        self.panchanga = self.context.get("panchanga", {}) if isinstance(self.context, dict) else {}
        self.upagraha = self.context.get("upagraha", {}) if isinstance(self.context, dict) else {}

        # 预计算 D1 宫主星。v6.0.39: Scorpio/Aquarius follow PyJHora's dynamic co-lord resolver
        # (Scorpio: stronger of Mars/Ketu; Aquarius: stronger of Saturn/Rahu), while SIGN_LORDS stays
        # as the classical fixed fallback for dignity tables and non-Jaimini contexts.
        self._house_lords: Dict[int, str] = {}
        for h in range(1, 13):
            sign = SIGNS[(self.asc_idx + h - 1) % 12]
            self._house_lords[h] = self._resolve_sign_lord(sign)

        # 预计算 D9 宫主星（用于依赖 Navamsa 的 B.V. Raman Yoga）
        d9_asc = self.d9.get("ascendant")
        d9_asc_idx = SIGNS.index(d9_asc) if d9_asc in SIGNS else None
        self._d9_house_lords: Dict[int, str] = {}
        if d9_asc_idx is not None:
            for h in range(1, 13):
                sign = SIGNS[(d9_asc_idx + h - 1) % 12]
                self._d9_house_lords[h] = self._resolve_sign_lord(sign)

    def _sign_index_of_planet(self, planet: str) -> Optional[int]:
        sign = self.sign_of(planet)
        return SIGNS.index(sign) if sign in SIGNS else None

    def _rasi_drishti_sign_indices_from(self, sign_idx: int) -> List[int]:
        sign_name = SIGNS[sign_idx]
        if sign_name in MOVABLE_SIGNS:
            return [i for i in [1, 4, 7, 10] if i not in ((sign_idx + 1) % 12, (sign_idx - 1) % 12)]
        if sign_name in FIXED_SIGNS:
            return [i for i in [0, 3, 6, 9] if i not in ((sign_idx + 1) % 12, (sign_idx - 1) % 12)]
        return [SIGNS.index(s) for s in DUAL_SIGNS if SIGNS.index(s) != sign_idx]

    def _stronger_co_lord(self, planet1: str, planet2: str) -> str:
        """Approximate PyJHora stronger_planet_from_planet_positions() for Sc/Aq co-lords."""
        h1 = self._sign_index_of_planet(planet1)
        h2 = self._sign_index_of_planet(planet2)
        if h1 is None:
            return planet2
        if h2 is None:
            return planet1

        node_owned_sign = RAHU_KETU_OWNED_SIGN_INDEX.get(planet1) or RAHU_KETU_OWNED_SIGN_INDEX.get(planet2)
        if node_owned_sign is not None:
            if h1 == node_owned_sign and h2 != node_owned_sign:
                return planet2
            if h2 == node_owned_sign and h1 != node_owned_sign:
                return planet1

        planet1_co_count = sum(1 for p in self.planets if self._sign_index_of_planet(p) == h1) - 1
        planet2_co_count = sum(1 for p in self.planets if self._sign_index_of_planet(p) == h2) - 1
        if planet1_co_count > planet2_co_count:
            return planet1
        if planet2_co_count > planet1_co_count:
            return planet2

        dispositor1 = self._resolve_sign_lord(SIGNS[h1], dynamic_co_lords=False)
        dispositor2 = self._resolve_sign_lord(SIGNS[h2], dynamic_co_lords=False)
        support1 = sum(
            self._sign_index_of_planet(p) == h1
            for p in ['Mercury', 'Jupiter', dispositor1]
            if p in self.planets
        )
        support1 += sum(
            p in self.planets and self._sign_index_of_planet(p) in self._rasi_drishti_sign_indices_from(h1)
            for p in ['Mercury', 'Jupiter', dispositor1]
        )
        support2 = sum(
            self._sign_index_of_planet(p) == h2
            for p in ['Mercury', 'Jupiter', dispositor2]
            if p in self.planets
        )
        support2 += sum(
            p in self.planets and self._sign_index_of_planet(p) in self._rasi_drishti_sign_indices_from(h2)
            for p in ['Mercury', 'Jupiter', dispositor2]
        )
        if support1 > support2:
            return planet1
        if support2 > support1:
            return planet2

        strength1 = HOUSE_STRENGTHS.get(planet1, [None] * 12)[h1]
        strength2 = HOUSE_STRENGTHS.get(planet2, [None] * 12)[h2]
        if strength1 == 4 and strength2 is not None and strength1 > strength2:
            return planet1
        if strength2 == 4 and strength1 is not None and strength2 > strength1:
            return planet2

        def modality_rank(sign_idx: int) -> int:
            sign_name = SIGNS[sign_idx]
            if sign_name in DUAL_SIGNS:
                return 3
            if sign_name in FIXED_SIGNS:
                return 2
            return 1

        rank1 = modality_rank(h1)
        rank2 = modality_rank(h2)
        if rank1 > rank2:
            return planet1
        if rank2 > rank1:
            return planet2

        degree1 = self.degree_of(planet1)
        degree2 = self.degree_of(planet2)
        if degree1 is not None and degree2 is not None:
            return planet1 if degree1 > degree2 else planet2
        return planet1

    def _resolve_sign_lord(self, sign: str, dynamic_co_lords: bool = True) -> Optional[str]:
        if not dynamic_co_lords:
            return SIGN_LORDS.get(sign)
        if sign == 'Scorpio':
            return self._stronger_co_lord('Mars', 'Ketu')
        if sign == 'Aquarius':
            return self._stronger_co_lord('Saturn', 'Rahu')
        return SIGN_LORDS.get(sign)

    # --- 基础查询 ---
    def house_of(self, planet: str) -> Optional[int]:
        return self.planets.get(planet, {}).get("house")

    def sign_of(self, planet: str) -> Optional[str]:
        return self.planets.get(planet, {}).get("sign")

    def degree_of(self, planet: str) -> Optional[float]:
        return self.planets.get(planet, {}).get("degree")

    def lord_of_house(self, house: int) -> Optional[str]:
        return self._house_lords.get(house)

    def planets_in_house(self, house: int) -> List[str]:
        return [p for p, info in self.planets.items() if info.get("house") == house]

    # --- D9 / Panchanga / Upagraha 扩展上下文 ---
    def d9_house_of(self, planet: str) -> Optional[int]:
        return self.d9.get("planets", {}).get(planet, {}).get("house")

    def d9_sign_of(self, planet: str) -> Optional[str]:
        return self.d9.get("planets", {}).get(planet, {}).get("sign")

    def d9_lord_of_house(self, house: int) -> Optional[str]:
        return self._d9_house_lords.get(house)

    def navamsa_dispositor(self, planet: str) -> Optional[str]:
        sign = self.d9_sign_of(planet)
        return self._resolve_sign_lord(sign) if sign else None

    def tithi(self) -> Optional[int]:
        return self.panchanga.get("tithi")

    def is_waning_moon(self) -> bool:
        return bool(self.panchanga.get("is_waning_moon"))

    def upagraha_house(self, name: str) -> Optional[int]:
        payload = self.upagraha.get(str(name).lower(), {})
        return payload.get("house")

    def upagraha_sign(self, name: str) -> Optional[str]:
        payload = self.upagraha.get(str(name).lower(), {})
        return payload.get("sign")

    # --- 尊严 ---
    def is_exalted(self, planet: str) -> bool:
        s = self.sign_of(planet)
        return s is not None and EXALTATION.get(planet) == s

    def is_own_sign(self, planet: str) -> bool:
        s = self.sign_of(planet)
        return s is not None and self._resolve_sign_lord(s) == planet

    def is_moolatrikona(self, planet: str) -> bool:
        s = self.sign_of(planet)
        return s is not None and MOOLATRIKONA_SIGN.get(planet) == s

    def is_debilitated(self, planet: str) -> bool:
        s = self.sign_of(planet)
        return s is not None and DEBILITATION.get(planet) == s

    def dignity(self, planet: str) -> str:
        s = self.sign_of(planet)
        return _get_dignity_level(planet, s) if s else 'NEUTRAL'

    # --- 宫位性质 ---
    def is_kendra(self, house: int) -> bool:
        return house in [1, 4, 7, 10]

    def is_trikona(self, house: int) -> bool:
        return house in [1, 5, 9]

    def is_dusthana(self, house: int) -> bool:
        return house in [6, 8, 12]

    def is_upachaya(self, house: int) -> bool:
        return house in [3, 6, 10, 11]

    def is_maraka(self, house: int) -> bool:
        return house in [2, 7]

    def is_badhaka(self, house: int) -> bool:
        """Badhaka 宫：基本盘7宫，固定盘9宫，变动盘11宫"""
        asc = self.ascendant
        if asc in ['Aries', 'Cancer', 'Libra', 'Capricorn']:
            return house == 11
        if asc in ['Taurus', 'Leo', 'Scorpio', 'Aquarius']:
            return house == 9
        return house == 7

    # --- 相对宫位关系 ---
    def house_offset(self, from_house: int, to_house: int) -> int:
        """从 from_house 到 to_house 的宫位偏移 (0=同宫, 1=下一宫, ...)"""
        return (to_house - from_house) % 12

    def is_kendra_from(self, planet: str, from_planet: str) -> bool:
        h1 = self.house_of(from_planet)
        h2 = self.house_of(planet)
        if h1 is None or h2 is None:
            return False
        return self.house_offset(h1, h2) in [0, 3, 6, 9]

    def is_trikona_from(self, planet: str, from_planet: str) -> bool:
        h1 = self.house_of(from_planet)
        h2 = self.house_of(planet)
        if h1 is None or h2 is None:
            return False
        return self.house_offset(h1, h2) in [0, 4, 8]

    def is_2nd_or_12th_from(self, planet: str, from_planet: str) -> bool:
        h1 = self.house_of(from_planet)
        h2 = self.house_of(planet)
        if h1 is None or h2 is None:
            return False
        return self.house_offset(h1, h2) in [1, 11]

    # --- 角色解析 ---
    def resolve(self, ref: Any) -> List[str]:
        """
        解析行星引用为具体行星名称列表。
        支持: 字符串行星名、角色对象、角色字符串。
        """
        if isinstance(ref, str):
            if ref in self.planets:
                return [ref]
            if ref == "benefics":
                return [p for p in BENEFICS if p in self.planets]
            if ref == "malefics":
                return [p for p in MALEFICS if p in self.planets]
            if ref == "all":
                return list(self.planets.keys())
            if ref in ("visible", "sun_to_saturn"):
                return [p for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] if p in self.planets]
            if ref == "kendra_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [1, 4, 7, 10]]))
            if ref == "trikona_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [1, 5, 9]]))
            if ref == "dusthana_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [6, 8, 12]]))
            if ref == "upachaya_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [3, 6, 10, 11]]))
            if ref.startswith("lord:"):
                house = int(ref.split(":")[1])
                lord = self._house_lords.get(house)
                return [lord] if lord else []
            return []

        if isinstance(ref, dict):
            role = ref.get("role")
            if role == "lord":
                house = ref.get("house")
                lord = self._house_lords.get(house)
                return [lord] if lord else []
            if role == "kendra_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [1, 4, 7, 10]]))
            if role == "trikona_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [1, 5, 9]]))
            if role == "dusthana_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [6, 8, 12]]))
            if role == "upachaya_lords":
                return list(dict.fromkeys([self._house_lords[h] for h in [3, 6, 10, 11]]))
            if role == "benefics":
                return [p for p in BENEFICS if p in self.planets]
            if role == "malefics":
                return [p for p in MALEFICS if p in self.planets]
            if role == "all":
                return list(self.planets.keys())
            if role in ("visible", "sun_to_saturn"):
                return [p for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] if p in self.planets]
            if role == "set":
                return [p for p in ref.get("planets", []) if p in self.planets]
        return []

    def resolve_single(self, ref: Any) -> Optional[str]:
        """解析为单个行星，返回 None 或行星名"""
        lst = self.resolve(ref)
        return lst[0] if lst else None


# ============================================================================
# YogaEngine: 规则加载与检测
# ============================================================================
class YogaEngine:
    """Yoga 检测引擎。从 JSON 加载规则，对星盘执行条件匹配。"""

    def __init__(self, rules_path: str):
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.schema_version = data.get("schema_version", "1.0")
        self.rules = [r for r in data.get("rules", []) if r.get("enabled", True)]

    def detect(self, planets: Dict[str, Dict], ascendant: str, context: Optional[Dict] = None) -> List[Dict]:
        """
        检测 Yoga。
        返回: [{name, name_cn, combination, effects, strength, source, bvr_id, category}, ...]
        """
        ctx = YogaContext(planets, ascendant, context=context)
        results = []
        seen_dedup = set()

        for rule in self.rules:
            matches = self._eval_rule(rule, ctx)
            for m in matches:
                entry = {
                    "name": rule["name"],
                    "name_cn": rule["name_cn"],
                    "combination": m.get("combination", ""),
                    "effects": rule.get("effects", []),
                    "strength": m.get("strength", rule.get("strength", "中")),
                    "source": rule.get("source", ""),
                    "bvr_id": rule.get("bvr_id"),
                    "category": rule.get("category", ""),
                    "rule_id": rule.get("id", ""),
                }
                # 去重：基于 dedup_key 或 name + combination
                dedup_key = rule.get("dedup_key") or rule["name"]
                dedup_val = f"{dedup_key}:{m.get('combination', '')}"
                if dedup_val in seen_dedup:
                    continue
                seen_dedup.add(dedup_val)
                results.append(entry)
        return results

    # ------------------------------------------------------------------------
    # 规则级评估
    # ------------------------------------------------------------------------
    def _eval_rule(self, rule: Dict, ctx: YogaContext) -> List[Dict]:
        """评估单条规则，返回匹配列表（空表示无匹配）"""
        logic = rule.get("logic", {})
        return self._eval_condition(logic, ctx, rule, {})

    def _eval_condition(self, cond: Dict, ctx: YogaContext, rule: Dict,
                        bindings: Dict) -> List[Dict]:
        """评估条件节点，返回匹配列表"""
        # v6.0.31: 兼容历史规则中的 "op" 字段。
        # 早期批量扩展脚本误用 op 而不是 type；如果只读 type，会导致这些规则静默失效。
        ctype = cond.get("type") or cond.get("op")
        # v6.0.32: 兼容批量生成规则使用的 compound_conditions/compound 结构。
        if ctype == "compound_conditions":
            cond = {**cond, "type": "and"}
            return self._eval_and(cond, ctx, rule, bindings)
        if ctype == "compound":
            operator = str(cond.get("operator", "AND")).lower()
            cond = {**cond, "type": "or" if operator == "or" else "and"}
            return self._eval_condition(cond, ctx, rule, bindings)

        handler = getattr(self, f"_eval_{ctype}", None)
        if handler:
            return handler(cond, ctx, rule, bindings)

        # v6.0.32: 兼容 PyJHora/BVR 批量规则中的语义型 condition type，
        # 避免未知类型静默导致整条 compound rule 永远失效。
        if ctype:
            return self._eval_semantic_condition(ctype, cond, ctx, rule, bindings)
        return []

    # ------------------------------------------------------------------------
    # 复合条件
    # ------------------------------------------------------------------------
    def _eval_and(self, cond, ctx, rule, bindings):
        """AND: 所有子条件必须同时满足"""
        subs = cond.get("conditions", [])
        if not subs:
            return [{"combination": "", "strength": rule.get("strength", "中")}]

        results = self._eval_condition(subs[0], ctx, rule, bindings)
        if not results:
            return []

        for sub in subs[1:]:
            new_results = []
            for match in results:
                b = {**bindings, **match.get("bindings", {})}
                sub_matches = self._eval_condition(sub, ctx, rule, b)
                for sm in sub_matches:
                    combo = match.get("combination", "")
                    sm_combo = sm.get("combination", "")
                    merged_combo = "; ".join(filter(None, [combo, sm_combo]))
                    new_results.append({
                        "combination": merged_combo,
                        "strength": sm.get("strength", match.get("strength")),
                        "bindings": {**match.get("bindings", {}), **sm.get("bindings", {})}
                    })
            results = new_results
            if not results:
                return []
        return results

    def _eval_or(self, cond, ctx, rule, bindings):
        """OR: 任一子条件满足即可"""
        all_results = []
        for sub in cond.get("conditions", []):
            matches = self._eval_condition(sub, ctx, rule, bindings)
            all_results.extend(matches)
        return all_results

    def _eval_not(self, cond, ctx, rule, bindings):
        """NOT: 子条件不满足时返回一个空匹配"""
        matches = self._eval_condition(cond.get("condition", {}), ctx, rule, bindings)
        return [] if matches else [{"combination": "", "strength": rule.get("strength", "中")}]

    # ------------------------------------------------------------------------
    # 单条件类型
    # ------------------------------------------------------------------------
    def _eval_same_house(self, cond, ctx, rule, bindings):
        """两颗行星同宫"""
        # 支持两种写法：
        # 1) {"a": ..., "b": ...}
        # 2) {"planets": ["Sun", "Mercury", ...]}：任意两颗同宫即满足
        if "planets" in cond and "a" not in cond and "b" not in cond:
            planets = cond.get("planets", [])
            pa = self._resolve_binding({"role": "set", "planets": planets}, ctx, bindings)
            pb = pa
        else:
            pa = self._resolve_binding(cond.get("a"), ctx, bindings)
            pb = self._resolve_binding(cond.get("b"), ctx, bindings)
        results = []
        for a in pa:
            for b in pb:
                if a == b:
                    continue
                h1 = ctx.house_of(a)
                h2 = ctx.house_of(b)
                if h1 is not None and h1 == h2:
                    tmpl = cond.get("combo_template", "{a}与{b}同在第{h}宫")
                    combo = tmpl.format(a=PLANET_CN.get(a, a), b=PLANET_CN.get(b, b), h=h1, a_raw=a, b_raw=b)
                    results.append({"combination": combo, "strength": rule.get("strength", "中"),
                                    "bindings": {"a": a, "b": b, "house": h1}})
        return results

    def _eval_in_houses(self, cond, ctx, rule, bindings):
        """行星在指定宫位列表中"""
        refs = self._resolve_binding(cond.get("planet", "$planet"), ctx, bindings)
        houses = cond.get("houses", [])
        exclude = cond.get("exclude", [])
        results = []
        for p in refs:
            if p in exclude:
                continue
            h = ctx.house_of(p)
            if h is not None and h in houses:
                tmpl = cond.get("combo_template", "{p}在第{h}宫")
                combo = tmpl.format(p=PLANET_CN.get(p, p), h=h, p_raw=p)
                results.append({"combination": combo, "strength": rule.get("strength", "中"),
                                "bindings": {"planet": p, "house": h}})
        return results

    def _eval_not_in_houses(self, cond, ctx, rule, bindings):
        """行星不在指定宫位列表中"""
        refs = self._resolve_binding(cond.get("planet"), ctx, bindings)
        houses = cond.get("houses", [])
        results = []
        for p in refs:
            h = ctx.house_of(p)
            if h is not None and h not in houses:
                results.append({"combination": "", "strength": rule.get("strength", "中"),
                                "bindings": {"planet": p, "house": h}})
        return results

    def _eval_in_houses_from(self, cond, ctx, rule, bindings):
        """行星在指定行星/基准的相对宫位关系中"""
        refs = self._resolve_binding(cond.get("planet"), ctx, bindings)
        from_ref = cond.get("from")
        relations = cond.get("relations", [])
        results = []

        # 解析 relations（支持字符串别名和整数偏移）
        valid_offsets = set()
        for r in relations:
            if r == "kendra":
                valid_offsets.update([0, 3, 6, 9])
            elif r == "trikona":
                valid_offsets.update([0, 4, 8])
            elif r == "2nd_12th":
                valid_offsets.update([1, 11])
            elif r == "3rd_11th":
                valid_offsets.update([2, 10])
            elif r == "same":
                valid_offsets.add(0)
            elif isinstance(r, int):
                valid_offsets.add(r)

        for p in refs:
            h1 = ctx.house_of(p)
            if h1 is None:
                continue
            # from 可以是行星或固定宫位
            if isinstance(from_ref, int):
                h_base = from_ref
            else:
                from_planets = self._resolve_binding(from_ref, ctx, bindings)
                for fp in from_planets:
                    h_base = ctx.house_of(fp)
                    if h_base is None:
                        continue
                    off = ctx.house_offset(h_base, h1)
                    if off in valid_offsets:
                        tmpl = cond.get("combo_template", "{p}在第{h}宫（从{fp}的{rel}）")
                        rel_name = self._offset_name(off)
                        combo = tmpl.format(p=PLANET_CN.get(p, p), h=h1, fp=PLANET_CN.get(fp, fp),
                                           rel=rel_name, off=off, p_raw=p, fp_raw=fp)
                        results.append({"combination": combo, "strength": rule.get("strength", "中"),
                                        "bindings": {"planet": p, "from": fp, "house": h1}})
        return results

    def _eval_dignity(self, cond, ctx, rule, bindings):
        """行星尊严检查"""
        refs = self._resolve_binding(cond.get("planet"), ctx, bindings)
        dignity_type = cond.get("dignity")  # exalted, own, moolatrikona, debilitated
        results = []
        for p in refs:
            ok = False
            if dignity_type == "exalted":
                ok = ctx.is_exalted(p)
            elif dignity_type == "own":
                ok = ctx.is_own_sign(p)
            elif dignity_type == "moolatrikona":
                ok = ctx.is_moolatrikona(p)
            elif dignity_type == "debilitated":
                ok = ctx.is_debilitated(p)
            elif dignity_type == "strong":
                ok = ctx.is_exalted(p) or ctx.is_own_sign(p) or ctx.is_moolatrikona(p)
            elif dignity_type == "not_debilitated":
                ok = not ctx.is_debilitated(p)
            elif dignity_type == "not_enemy":
                ok = True  # placeholder, not used in current rules

            # v6.0.31: 兼容历史规则中的 status 字段。
            # 批量规则曾使用 {"op":"dignity", "status":"exalted"}，而引擎原本只读取 dignity。
            if dignity_type is None:
                status = cond.get("status")
                if status == "exalted":
                    ok = ctx.is_exalted(p)
                    dignity_type = status
                elif status == "own":
                    ok = ctx.is_own_sign(p)
                    dignity_type = status
                elif status == "moolatrikona":
                    ok = ctx.is_moolatrikona(p)
                    dignity_type = status
                elif status == "debilitated":
                    ok = ctx.is_debilitated(p)
                    dignity_type = status
                elif status == "strong":
                    ok = ctx.is_exalted(p) or ctx.is_own_sign(p) or ctx.is_moolatrikona(p)
                    dignity_type = status
            if ok:
                sign = ctx.sign_of(p)
                tmpl = cond.get("combo_template", "{p}{dignity}在{sign}")
                combo = tmpl.format(p=PLANET_CN.get(p, p), dignity=dignity_type, sign=sign or "", p_raw=p)
                results.append({"combination": combo, "strength": rule.get("strength", "中"),
                                "bindings": {"planet": p, "sign": sign}})
        return results

    def _eval_count(self, cond, ctx, rule, bindings):
        """统计满足条件的行星数量"""
        refs = self._resolve_binding(cond.get("items", cond.get("planets")), ctx, bindings)
        sub_cond = cond.get("condition", {})
        min_count = cond.get("min", 1)
        max_count = cond.get("max")

        matched = []
        for p in refs:
            # 临时把 planet 绑定为 p，评估子条件
            sub_bindings = {**bindings, "planet": p}
            matches = self._eval_condition(sub_cond, ctx, rule, sub_bindings)
            if matches:
                matched.append(p)

        count = len(matched)
        ok = count >= min_count
        if max_count is not None:
            ok = ok and count <= max_count

        if ok:
            tmpl = cond.get("combo_template", "{count}颗行星满足条件")
            combo = tmpl.format(count=count, planets="、".join(PLANET_CN.get(p, p) for p in matched))
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"count": count, "matched": matched}}]
        return []

    def _eval_houses_occupied(self, cond, ctx, rule, bindings):
        """行星占据的宫位数量"""
        refs = self._resolve_binding(cond.get("planets", "all"), ctx, bindings)
        occupied = set()
        for p in refs:
            h = ctx.house_of(p)
            if h is not None:
                occupied.add(h)
        count = len(occupied)
        target = cond.get("count")
        min_count = cond.get("min")
        max_count = cond.get("max")

        ok = False
        if target is not None:
            ok = count == target
        else:
            ok = True
            if min_count is not None:
                ok = ok and count >= min_count
            if max_count is not None:
                ok = ok and count <= max_count

        if ok:
            tmpl = cond.get("combo_template", "行星分布在{count}个宫位")
            combo = tmpl.format(count=count)
            return [{"combination": combo, "strength": rule.get("strength", "中")}]
        return []

    def _eval_adjacent_houses(self, cond, ctx, rule, bindings):
        """目标宫位的前/后宫位有指定行星"""
        target = cond.get("house")
        sides = cond.get("sides", ["prev", "next"])
        refs = self._resolve_binding(cond.get("planets"), ctx, bindings)
        require_both = cond.get("both", False)

        prev_h = ((target - 2) % 12) + 1
        next_h = (target % 12) + 1

        prev_ok = any(ctx.house_of(p) == prev_h for p in refs) if "prev" in sides else True
        next_ok = any(ctx.house_of(p) == next_h for p in refs) if "next" in sides else True

        if require_both:
            ok = prev_ok and next_ok
        else:
            ok = prev_ok or next_ok

        if ok:
            tmpl = cond.get("combo_template", "第{target}宫被夹击")
            combo = tmpl.format(target=target, prev=prev_h, next=next_h)
            return [{"combination": combo, "strength": rule.get("strength", "中")}]
        return []

    def _eval_all_in_houses(self, cond, ctx, rule, bindings):
        """所有指定行星都在给定宫位集合中。"""
        refs = self._resolve_binding(cond.get("planets", "visible"), ctx, bindings)
        houses = set(cond.get("houses", []))
        if not refs or not houses:
            return []
        occupied = [ctx.house_of(p) for p in refs]
        ok = all(h in houses for h in occupied if h is not None) and len(occupied) == len(refs)
        if ok:
            tmpl = cond.get("combo_template", "所有指定行星均落入{houses}")
            combo = tmpl.format(houses="/".join(str(h) for h in sorted(houses)), planets="、".join(PLANET_CN.get(p, p) for p in refs))
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"planets": refs, "houses": sorted(houses)}}]
        return []

    def _eval_all_in_house_sets(self, cond, ctx, rule, bindings):
        """所有指定行星都在多个候选宫位集合之一中。"""
        refs = self._resolve_binding(cond.get("planets", "visible"), ctx, bindings)
        house_sets = cond.get("house_sets", [])
        if not refs or not house_sets:
            return []
        for houses in house_sets:
            houses_set = set(houses)
            occupied = [ctx.house_of(p) for p in refs]
            ok = all(h in houses_set for h in occupied if h is not None) and len(occupied) == len(refs)
            if ok:
                tmpl = cond.get("combo_template", "所有指定行星均落入候选宫位集合{houses}")
                combo = tmpl.format(houses="/".join(str(h) for h in sorted(houses_set)), planets="、".join(PLANET_CN.get(p, p) for p in refs))
                return [{"combination": combo, "strength": rule.get("strength", "中"),
                         "bindings": {"planets": refs, "houses": sorted(houses_set)}}]
        return []

    def _eval_occupied_houses_exact(self, cond, ctx, rule, bindings):
        """指定行星实际占据的宫位集合与目标集合完全一致。"""
        refs = self._resolve_binding(cond.get("planets", "visible"), ctx, bindings)
        houses = set(cond.get("houses", []))
        occupied = {ctx.house_of(p) for p in refs if ctx.house_of(p) is not None}
        if refs and occupied == houses:
            tmpl = cond.get("combo_template", "指定行星只占据{houses}")
            combo = tmpl.format(houses="/".join(str(h) for h in sorted(houses)), planets="、".join(PLANET_CN.get(p, p) for p in refs))
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"planets": refs, "houses": sorted(houses)}}]
        return []

    def _eval_occupied_houses_exact_sets(self, cond, ctx, rule, bindings):
        """指定行星实际占据的宫位集合等于候选集合之一。"""
        refs = self._resolve_binding(cond.get("planets", "visible"), ctx, bindings)
        house_sets = cond.get("house_sets", [])
        occupied = {ctx.house_of(p) for p in refs if ctx.house_of(p) is not None}
        for houses in house_sets:
            houses_set = set(houses)
            if refs and occupied == houses_set:
                tmpl = cond.get("combo_template", "指定行星只占据候选宫位集合{houses}")
                combo = tmpl.format(houses="/".join(str(h) for h in sorted(houses_set)), planets="、".join(PLANET_CN.get(p, p) for p in refs))
                return [{"combination": combo, "strength": rule.get("strength", "中"),
                         "bindings": {"planets": refs, "houses": sorted(houses_set)}}]
        return []

    def _eval_has_planet_in_house(self, cond, ctx, rule, bindings):
        """指定行星集合中至少一颗在某宫。"""
        refs = self._resolve_binding(cond.get("planets", "all"), ctx, bindings)
        house = cond.get("house")
        matched = [p for p in refs if ctx.house_of(p) == house]
        if matched:
            tmpl = cond.get("combo_template", "第{house}宫有{planets}")
            combo = tmpl.format(house=house, planets="、".join(PLANET_CN.get(p, p) for p in matched))
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"matched": matched, "house": house}}]
        return []

    def _eval_has_planet_in_house_from(self, cond, ctx, rule, bindings):
        """指定行星集合中至少一颗在某参考行星的相对宫位。houses 使用传统 1-12 口径。"""
        refs = self._resolve_binding(cond.get("planets", "all"), ctx, bindings)
        from_planet = cond.get("from") or cond.get("from_planet")
        from_list = self._resolve_binding(from_planet, ctx, bindings)
        houses = cond.get("houses", [])
        exclude = set(cond.get("exclude", []))
        results = []
        for fp in from_list:
            base = ctx.house_of(fp)
            if base is None:
                continue
            for rel_house in houses:
                target = ((base + rel_house - 2) % 12) + 1
                matched = [p for p in refs if p not in exclude and p != fp and ctx.house_of(p) == target]
                if matched:
                    tmpl = cond.get("combo_template", "{planets}在{fp}的第{rel}宫")
                    combo = tmpl.format(
                        planets="、".join(PLANET_CN.get(p, p) for p in matched),
                        fp=PLANET_CN.get(fp, fp),
                        rel=rel_house,
                        target=target,
                    )
                    results.append({"combination": combo, "strength": rule.get("strength", "中"),
                                    "bindings": {"matched": matched, "from": fp, "rel_house": rel_house, "house": target}})
        return results

    def _eval_houses_with_planets_count(self, cond, ctx, rule, bindings):
        """在指定宫位集合中，有多少个宫位至少包含一颗指定集合行星。"""
        refs = self._resolve_binding(cond.get("planets", "all"), ctx, bindings)
        houses = cond.get("houses", [])
        min_count = cond.get("min", 1)
        max_count = cond.get("max")
        occupied = []
        for h in houses:
            matched = [p for p in refs if ctx.house_of(p) == h]
            if matched:
                occupied.append((h, matched))
        count = len(occupied)
        ok = count >= min_count
        if max_count is not None:
            ok = ok and count <= max_count
        if ok:
            tmpl = cond.get("combo_template", "{count}个目标宫位有指定行星")
            detail = "; ".join(f"第{h}宫:" + "、".join(PLANET_CN.get(p, p) for p in ps)
                            for h, ps in occupied)
            combo = tmpl.format(count=count, detail=detail,
                               houses="/".join(str(h) for h, _ in occupied))
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"occupied": occupied, "count": count}}]
        return []

    def _eval_degree_gap(self, cond, ctx, rule, bindings):
        """同星座内两颗行星度数差小于阈值"""
        pa = self._resolve_binding(cond.get("a"), ctx, bindings)
        pb = self._resolve_binding(cond.get("b"), ctx, bindings)
        max_gap = cond.get("max_gap", 1.0)
        results = []
        for a in pa:
            for b in pb:
                if a == b:
                    continue
                s1 = ctx.sign_of(a)
                s2 = ctx.sign_of(b)
                if s1 is None or s1 != s2:
                    continue
                d1 = ctx.degree_of(a)
                d2 = ctx.degree_of(b)
                if d1 is None or d2 is None:
                    continue
                if abs(d1 - d2) < max_gap:
                    tmpl = cond.get("combo_template", "{a}与{b}在{sign}内相距{gap:.2f}°")
                    combo = tmpl.format(a=PLANET_CN.get(a, a), b=PLANET_CN.get(b, b), sign=s1,
                                       gap=abs(d1 - d2))
                    results.append({"combination": combo, "strength": rule.get("strength", "中")})
        return results

    def _eval_parivartana(self, cond, ctx, rule, bindings):
        """两颗宫主星互换星座（Parivartana/互落）"""
        la = ctx.resolve_single(cond.get("lord_a"))
        lb = ctx.resolve_single(cond.get("lord_b"))
        if la is None or lb is None or la == lb:
            return []
        sa = ctx.sign_of(la)
        sb = ctx.sign_of(lb)
        if sa is None or sb is None:
            return []
        lord_of_sa = SIGN_LORDS.get(sa)
        lord_of_sb = SIGN_LORDS.get(sb)
        if lord_of_sa == lb and lord_of_sb == la:
            tmpl = cond.get("combo_template", "{la}与{lb}互换星座")
            combo = tmpl.format(la=PLANET_CN.get(la, la), lb=PLANET_CN.get(lb, lb))
            return [{"combination": combo, "strength": rule.get("strength", "强")}]
        return []

    def _eval_any_pair(self, cond, ctx, rule, bindings):
        """从集合 A 和集合 B 中各取一个元素，配对满足条件"""
        if "planets" in cond and "from" not in cond and "to" not in cond:
            set_a = self._resolve_binding({"role": "set", "planets": cond.get("planets", [])}, ctx, bindings)
            set_b = set_a
            exclude_self = True
        else:
            set_a = self._resolve_binding(cond.get("from"), ctx, bindings)
            set_b = self._resolve_binding(cond.get("to"), ctx, bindings)
            exclude_self = cond.get("exclude_self", False)
        sub_cond = cond.get("condition", {})

        results = []
        for a in set_a:
            for b in set_b:
                if exclude_self and a == b:
                    continue
                pair_bindings = {**bindings, "a": a, "b": b}
                matches = self._eval_condition(sub_cond, ctx, rule, pair_bindings)
                for m in matches:
                    m["bindings"] = {**m.get("bindings", {}), "a": a, "b": b}
                results.extend(matches)
        return results

    def _eval_all_planets(self, cond, ctx, rule, bindings):
        """所有指定行星都满足某个条件"""
        refs = self._resolve_binding(cond.get("planets", "all"), ctx, bindings)
        sub_cond = cond.get("condition", {})
        all_match = True
        matched_combo_parts = []
        for p in refs:
            b = {**bindings, "planet": p}
            matches = self._eval_condition(sub_cond, ctx, rule, b)
            if not matches:
                all_match = False
                break
            matched_combo_parts.append(matches[0].get("combination", ""))
        if all_match and refs:
            combo = "; ".join(filter(None, matched_combo_parts))
            return [{"combination": combo, "strength": rule.get("strength", "中")}]
        return []

    def _eval_any_planet(self, cond, ctx, rule, bindings):
        """任一指定行星满足条件"""
        refs = self._resolve_binding(cond.get("planets"), ctx, bindings)
        sub_cond = cond.get("condition", {})
        for p in refs:
            b = {**bindings, "planet": p}
            matches = self._eval_condition(sub_cond, ctx, rule, b)
            if matches:
                return matches
        return []

    def _eval_exists(self, cond, ctx, rule, bindings):
        """存在至少一个行星满足条件"""
        refs = self._resolve_binding(cond.get("planets"), ctx, bindings)
        sub_cond = cond.get("condition", {})
        for p in refs:
            b = {**bindings, "planet": p}
            matches = self._eval_condition(sub_cond, ctx, rule, b)
            if matches:
                return matches
        return []

    def _eval_lord_in_house(self, cond, ctx, rule, bindings):
        """某宫主星在指定宫位"""
        house = cond.get("house")
        target_houses = cond.get("target_houses", [])
        lord = ctx.lord_of_house(house)
        if lord is None or lord not in ctx.planets:
            return []
        lh = ctx.house_of(lord)
        if lh is not None and lh in target_houses:
            tmpl = cond.get("combo_template", "{house}宫主{lord}在第{lh}宫")
            combo = tmpl.format(house=house, lord=PLANET_CN.get(lord, lord), lh=lh)
            return [{"combination": combo, "strength": rule.get("strength", "中"),
                     "bindings": {"lord": lord, "house": lh}}]
        return []

    def _eval_lords_relation(self, cond, ctx, rule, bindings):
        """两个宫主星之间的特定关系（同宫/互落等）"""
        lord_a = ctx.resolve_single(cond.get("lord_a"))
        lord_b = ctx.resolve_single(cond.get("lord_b"))
        if lord_a is None or lord_b is None:
            return []
        relation = cond.get("relation", "same_house")
        if relation == "same_house":
            ha = ctx.house_of(lord_a)
            hb = ctx.house_of(lord_b)
            if ha is not None and ha == hb:
                tmpl = cond.get("combo_template", "{la}与{lb}同在第{h}宫")
                combo = tmpl.format(la=PLANET_CN.get(lord_a, lord_a), lb=PLANET_CN.get(lord_b, lord_b), h=ha)
                return [{"combination": combo, "strength": rule.get("strength", "中")}]
        return []

    def _eval_custom(self, cond, ctx, rule, bindings):
        """自定义 Python 表达式（用于复杂规则）"""
        expr = cond.get("expr", "")
        if not expr:
            return []

        def house_of(p): return ctx.house_of(p)
        def sign_of(p): return ctx.sign_of(p)
        def deg_of(p): return ctx.degree_of(p)
        def lord(h): return ctx.lord_of_house(h)
        def in_houses(p, hs): h = house_of(p); return h is not None and h in hs
        def dignity(p): return ctx.dignity(p)
        def exalted(p): return ctx.is_exalted(p)
        def own(p): return ctx.is_own_sign(p)
        def debil(p): return ctx.is_debilitated(p)
        def moola(p): return ctx.is_moolatrikona(p)
        def kendra(h): return ctx.is_kendra(h)
        def trikona(h): return ctx.is_trikona(h)
        def dusthana(h): return ctx.is_dusthana(h)
        def upachaya(h): return ctx.is_upachaya(h)
        def kendra_from(p, fp): return ctx.is_kendra_from(p, fp)
        def trikona_from(p, fp): return ctx.is_trikona_from(p, fp)
        def offset(fh, th): return ctx.house_offset(fh, th)
        def planets_in(h): return ctx.planets_in_house(h)
        def resolve(ref): return ctx.resolve(ref)

        # v6.0.32: 修复 custom 规则中常用的缺失辅助函数
        def same_house(a, b):
            """两颗行星是否同宫"""
            if a == b:
                return False
            ha = ctx.house_of(a)
            hb = ctx.house_of(b)
            return ha is not None and ha == hb

        def aspect(a, b):
            """行星a是否aspect行星b（7th aspect + Mars/Jupiter/Saturn的特殊aspect）"""
            if a == b:
                return False
            ha = ctx.house_of(a)
            hb = ctx.house_of(b)
            if ha is None or hb is None:
                return False
            off = ctx.house_offset(ha, hb)
            # 7th aspect for all planets
            if off == 6:
                return True
            # Mars: 4th, 8th aspects
            if a == 'Mars' and off in (3, 7):
                return True
            # Jupiter: 5th, 9th aspects
            if a == 'Jupiter' and off in (4, 8):
                return True
            # Saturn: 3rd, 10th aspects
            if a == 'Saturn' and off in (2, 9):
                return True
            return False

        def aspects_house(p, h):
            if p not in ctx.planets or h is None:
                return False
            return h == ctx.house_of(p) or offset(ctx.house_of(p), h) in (6, 3 if p == 'Mars' else -1, 7 if p == 'Mars' else -1, 4 if p == 'Jupiter' else -1, 8 if p == 'Jupiter' else -1, 2 if p == 'Saturn' else -1, 9 if p == 'Saturn' else -1)

        def graha_aspects_house(p, h):
            if p not in ctx.planets or h is None:
                return False
            return offset(ctx.house_of(p), h) in (6, 3 if p == 'Mars' else -1, 7 if p == 'Mars' else -1, 4 if p == 'Jupiter' else -1, 8 if p == 'Jupiter' else -1, 2 if p == 'Saturn' else -1, 9 if p == 'Saturn' else -1)

        def pyjhora_planets_aspecting_raasi(p, h):
            """Replicate PyJHora house.planets_aspecting_the_raasi() behavior for source parity."""
            if p not in ctx.planets or h is None:
                return False
            sign_name = ctx.sign_of(p)
            if sign_name not in SIGNS:
                return False
            target_rasi_idx = (ctx.asc_idx + h - 1) % 12
            aspected_signs = rasi_drishti_signs_from(sign_name)
            planet_ids_in_aspected_signs = [
                PLANET_INDEX[q]
                for q in ctx.planets
                if q in PLANET_INDEX and ctx.sign_of(q) in aspected_signs
            ]
            return target_rasi_idx in planet_ids_in_aspected_signs

        def pyjhora_aspected_planets_of_raasi(h):
            """Replicate PyJHora house.aspected_planets_of_the_raasi(): planets whose rasi drishti hits a target house."""
            if h is None:
                return []
            target_sign = house_sign(h)
            return [
                p for p in ctx.planets
                if p in PLANET_INDEX and target_sign in rasi_drishti_signs_from(ctx.sign_of(p))
            ]

        def rasi_drishti_signs_from(sign_name):
            if sign_name not in SIGNS:
                return []
            sign_idx = SIGNS.index(sign_name)
            if sign_name in MOVABLE_SIGNS:
                return [SIGNS[i] for i in [1, 4, 7, 10] if i not in ((sign_idx + 1) % 12, (sign_idx - 1) % 12)]
            if sign_name in FIXED_SIGNS:
                return [SIGNS[i] for i in [0, 3, 6, 9] if i not in ((sign_idx + 1) % 12, (sign_idx - 1) % 12)]
            return [s for s in DUAL_SIGNS if s != sign_name]

        def rasi_aspects_house(p, h):
            if p not in ctx.planets or h is None:
                return False
            return house_sign(h) in rasi_drishti_signs_from(ctx.sign_of(p))

        def rasi_aspects(a, b):
            return a in ctx.planets and b in ctx.planets and rasi_aspects_house(a, ctx.house_of(b))

        def rasi_aspected_by_planets(h):
            return [p for p in ctx.planets if rasi_aspects_house(p, h)]

        def sign_index_of_planet(p):
            sign_name = ctx.sign_of(p)
            return SIGNS.index(sign_name) if sign_name in SIGNS else None

        def house_strength(p):
            sign_idx = sign_index_of_planet(p)
            if sign_idx is None or p not in HOUSE_STRENGTHS:
                return None
            strength = HOUSE_STRENGTHS[p][sign_idx]
            sign_name = SIGNS[sign_idx]
            # v6.0.39: PyJHora dynamic co-lord owner strength for Scorpio/Aquarius.
            # Without this, Ketu/Rahu can become house lords but still look non-owner in strength checks.
            if sign_name in ('Scorpio', 'Aquarius') and ctx._resolve_sign_lord(sign_name) == p:
                return max(strength, 5)
            return strength

        def strong(p, include_neutral=False):
            strength = house_strength(p)
            if strength is None:
                return False
            return strength >= (2 if include_neutral else 3)

        def weak(p):
            strength = house_strength(p)
            return strength is not None and strength <= 2

        def associated(a, b):
            return a in ctx.planets and b in ctx.planets and (same_house(a, b) or aspect(a, b) or aspect(b, a))

        def temporal_friend(a, b):
            if a not in ctx.planets or b not in ctx.planets or a == b:
                return False
            # PyJHora temporary friends: 2/3/4/10/11/12 from a planet.
            return offset(ctx.house_of(a), ctx.house_of(b)) in [1, 2, 3, 9, 10, 11]

        def natural_friend(a, b):
            return a in FRIENDLY_PLANETS.get(b, []) and b in FRIENDLY_PLANETS.get(a, [])

        def occupants(h):
            return ctx.planets_in_house(h) if h is not None else []

        def only_benefics_in_house(h):
            ps = occupants(h)
            return bool(ps) and all(p in BENEFICS for p in ps)

        def only_malefics_in_house(h):
            ps = occupants(h)
            return bool(ps) and all(p in MALEFICS for p in ps)

        def house_has_benefic(h):
            return any(p in BENEFICS for p in occupants(h))

        def house_has_malefic(h):
            return any(p in MALEFICS for p in occupants(h))

        def house_sign(h):
            if h is None:
                return None
            return SIGNS[(ctx.asc_idx + h - 1) % 12]

        def movable_house(h):
            return house_sign(h) in MOVABLE_SIGNS

        def d9_house_of(p): return ctx.d9_house_of(p)
        def d9_sign_of(p): return ctx.d9_sign_of(p)
        def d9_lord_of_house(h): return ctx.d9_lord_of_house(h)
        def navamsa_dispositor(p): return ctx.navamsa_dispositor(p)
        def tithi(): return ctx.tithi()
        def is_waning_moon(): return ctx.is_waning_moon()
        def upagraha_house(name): return ctx.upagraha_house(name)
        def upagraha_sign(name): return ctx.upagraha_sign(name)
        def gulika_house(): return ctx.upagraha_house("gulika")
        def maandi_house(): return ctx.upagraha_house("maandi")
        def gulika_sign(): return ctx.upagraha_sign("gulika")
        def maandi_sign(): return ctx.upagraha_sign("maandi")

        def exal(p): return ctx.is_exalted(p)
        def lord_of_house(h): return ctx.lord_of_house(h)
        def sign(p): return ctx.sign_of(p)

        def check_amala_from(base_house):
            """Amala: 第10宫仅有吉星，支持从Lagna/Moon等基准宫位计算。"""
            target = ((base_house - 1 + 9) % 12) + 1
            occupants = ctx.planets_in_house(target)
            return bool(occupants) and all(p in BENEFICS for p in occupants)

        def pyjhora_natural_benefics():
            """Replicate PyJHora yoga._get_natural_benefics(): Jupiter, Venus, plus benefic Mercury."""
            benefics = [p for p in ["Jupiter", "Venus"] if p in ctx.planets]
            mercury_house = ctx.house_of("Mercury")
            if mercury_house is not None:
                mercury_alone = len(ctx.planets_in_house(mercury_house)) == 1
                mercury_with_jupiter_or_venus = any(ctx.house_of(p) == mercury_house for p in ["Jupiter", "Venus"] if p in ctx.planets)
                if mercury_alone or mercury_with_jupiter_or_venus:
                    benefics.append("Mercury")
            return benefics

        # 辅助：获取星盘所有行星名列表
        def _planets_list():
            return list(ctx.planets.keys())
        # 辅助：获取所有宫主星（1-12宫）
        def _all_lords():
            return [ctx.lord_of_house(h) for h in range(1, 13)]
        # 辅助：获取角宫主星列表
        def _kendra_lords_list():
            ai = SIGNS.index(ctx.ascendant) if ctx.ascendant in SIGNS else 0
            return list(set([SIGN_LORDS[SIGNS[(ai + h - 1) % 12]] for h in [1, 4, 7, 10]]))
        # 辅助：获取三方宫主星列表
        def _trikona_lords_list():
            ai = SIGNS.index(ctx.ascendant) if ctx.ascendant in SIGNS else 0
            return list(set([SIGN_LORDS[SIGNS[(ai + h - 1) % 12]] for h in [1, 5, 9]]))

        safe_globals = {
            # 安全内置函数：只开放规则表达式需要的纯函数，避免 custom 规则因 all/any/len/set 缺失而静默失效。
            "all": all, "any": any, "len": len, "set": set, "tuple": tuple, "sorted": sorted,
            "abs": abs, "min": min, "max": max, "sum": sum, "range": range,
            "list": list, "bool": bool,
            "ctx": ctx, "bindings": bindings, "rule": rule,
            "SIGNS": SIGNS, "SIGN_LORDS": SIGN_LORDS,
            "FRIENDLY_PLANETS": FRIENDLY_PLANETS,
            "RAHU_KETU_OWNED_SIGN_INDEX": RAHU_KETU_OWNED_SIGN_INDEX,
            "EXALTATION": EXALTATION, "DEBILITATION": DEBILITATION,
            "PLANET_CN": PLANET_CN, "BENEFICS": BENEFICS, "MALEFICS": MALEFICS,
            "MOVABLE_SIGNS": MOVABLE_SIGNS, "FIXED_SIGNS": FIXED_SIGNS, "DUAL_SIGNS": DUAL_SIGNS,
            "PLANET_INDEX": PLANET_INDEX, "HOUSE_STRENGTHS": HOUSE_STRENGTHS,
            "ALL_PLANETS": ALL_PLANETS, "MOOLATRIKONA_SIGN": MOOLATRIKONA_SIGN,
            # 基础查询
            "house_of": house_of, "sign_of": sign_of, "deg_of": deg_of,
            "get_sign_of": sign_of,  # 别名
            "lord": lord, "lords_of": lord,  # 别名（接受宫位数）
            # 尊严检查
            "dignity": dignity,
            "exalted": exalted, "is_exalted": exalted,
            "own": own, "is_own_sign": own,
            "debil": debil, "is_debilitated": debil,
            "moola": moola, "is_moolatrikona": moola,
            # 宫位类型
            "in_houses": in_houses, "planets_in": planets_in,
            "kendra": kendra, "is_kendra": kendra,
            "trikona": trikona, "is_trikona": trikona,
            "dusthana": dusthana, "is_dusthana": dusthana,
            "upachaya": upachaya, "is_upachaya": upachaya,
            "kendra_from": kendra_from, "trikona_from": trikona_from,
            "offset": offset,
            # v6.0.32: 同宫与相位检查（custom规则常用）
            "same_house": same_house, "aspect": aspect, "aspects_house": aspects_house,
            "graha_aspects_house": graha_aspects_house,
            "pyjhora_planets_aspecting_raasi": pyjhora_planets_aspecting_raasi,
            "pyjhora_aspected_planets_of_raasi": pyjhora_aspected_planets_of_raasi,
            "rasi_drishti_signs_from": rasi_drishti_signs_from,
            "rasi_aspects_house": rasi_aspects_house, "rasi_aspects": rasi_aspects,
            "rasi_aspected_by_planets": rasi_aspected_by_planets,
            "house_strength": house_strength, "strong": strong, "weak": weak,
            "associated": associated, "temporal_friend": temporal_friend, "natural_friend": natural_friend,
            "occupants": occupants, "only_benefics_in_house": only_benefics_in_house,
            "only_malefics_in_house": only_malefics_in_house,
            "house_has_benefic": house_has_benefic, "house_has_malefic": house_has_malefic,
            "house_sign": house_sign, "movable_house": movable_house,
            "pyjhora_natural_benefics": pyjhora_natural_benefics,
            "d9_house_of": d9_house_of, "d9_sign_of": d9_sign_of,
            "d9_lord_of_house": d9_lord_of_house, "navamsa_dispositor": navamsa_dispositor,
            "tithi": tithi, "is_waning_moon": is_waning_moon,
            "upagraha_house": upagraha_house, "upagraha_sign": upagraha_sign,
            "gulika_house": gulika_house, "maandi_house": maandi_house,
            "gulika_sign": gulika_sign, "maandi_sign": maandi_sign,
            "exal": exal, "lord_of_house": lord_of_house, "sign": sign,
            "check_amala_from": check_amala_from,
            "Benefics": BENEFICS, "Malefics": MALEFICS,
            "planets": ctx.planets,
            # 解析
            "resolve": resolve,
            # 列表辅助
            "planets_list": _planets_list,
            "all_lords": _all_lords,
            "kendra_lords_list": _kendra_lords_list,
            "trikona_lords_list": _trikona_lords_list,
        }
        # v6.0.32: 支持多行语句（if/else/for等）+ 末尾表达式求值模式。
        # 不能简单 split 最后一行：多行 if/else 的最后一行经常只是 else 分支内部表达式，
        # 直接 exec 前半段会产生缩进不完整。这里用 AST 捕获“实际执行分支”的末尾表达式。
        result = None
        exec_globals = {"__builtins__": {}, **safe_globals}

        def _capture_tail_expr(block):
            """把代码块末尾表达式改写为 __result__ = <expr>；递归处理 if/for/while 分支。"""
            if not block:
                return block
            last = block[-1]
            if isinstance(last, ast.Expr):
                block[-1] = ast.Assign(targets=[ast.Name(id="__result__", ctx=ast.Store())], value=last.value)
            elif isinstance(last, ast.If):
                last.body = _capture_tail_expr(last.body)
                last.orelse = _capture_tail_expr(last.orelse)
            elif isinstance(last, (ast.For, ast.While)):
                last.body = _capture_tail_expr(last.body)
                last.orelse = _capture_tail_expr(last.orelse)
            elif isinstance(last, ast.Try):
                last.body = _capture_tail_expr(last.body)
                last.orelse = _capture_tail_expr(last.orelse)
                last.finalbody = _capture_tail_expr(last.finalbody)
                for handler in last.handlers:
                    handler.body = _capture_tail_expr(handler.body)
            return block

        try:
            # 同一命名空间同时作为 globals/locals，保证 list/dict comprehension 能访问 BENEFICS 等名称。
            result = eval(expr, exec_globals, exec_globals)
        except SyntaxError:
            try:
                tree = ast.parse(expr.strip(), mode="exec")
                tree.body = _capture_tail_expr(tree.body)
                ast.fix_missing_locations(tree)
                exec(compile(tree, "<yoga_custom>", "exec"), exec_globals, exec_globals)
                result = exec_globals.get("__result__")
            except Exception:
                pass
        except Exception:
            pass

        if result:
            combo = cond.get("combo_template", "自定义条件满足")
            if callable(combo):
                combo = combo(ctx, bindings)
            strength = cond.get("strength", rule.get("strength", "中"))
            if callable(strength):
                strength = strength(ctx, bindings)
            return [{"combination": combo, "strength": strength}]
        return []

    def _eval_semantic_condition(self, ctype, cond, ctx, rule, bindings):
        """兼容批量抽取规则中的语义型条件。返回保守布尔匹配。"""
        def success(combo=None):
            return [{"combination": combo or cond.get("note", ctype), "strength": rule.get("strength", "中")}]

        def house(ref):
            if isinstance(ref, int):
                return ref
            if isinstance(ref, str):
                if ref in ctx.planets:
                    return ctx.house_of(ref)
                low = ref.lower()
                if low in ("lagna", "asc", "ascendant"):
                    return 1
                if low == "moon":
                    return ctx.house_of("Moon")
            return None

        def planet_list(default=None):
            ps = cond.get("planets", default or [])
            if ps == "all":
                return [p for p in ALL_PLANETS if p in ctx.planets]
            if isinstance(ps, str):
                return [ps] if ps in ctx.planets else []
            return [p for p in ps if p in ctx.planets]

        def aspects(a, b):
            # b 可为行星名或宫位整数；支持检查行星对宫位/行星的传统相位。
            ha = ctx.house_of(a)
            hb = ctx.house_of(b) if isinstance(b, str) else b
            if ha is None or hb is None or a == b:
                return False
            off = ctx.house_offset(ha, hb)
            return off == 6 or (a == "Mars" and off in (3, 7)) or (a == "Jupiter" and off in (4, 8)) or (a == "Saturn" and off in (2, 9))

        def related(a, b):
            return a in ctx.planets and b in ctx.planets and (ctx.house_of(a) == ctx.house_of(b) or aspects(a, b) or aspects(b, a))

        def house_lord(h):
            return ctx.lord_of_house(h) if isinstance(h, int) else None

        def is_benefic(p):
            return p in BENEFICS

        def is_malefic(p):
            return p in MALEFICS

        def is_strong(p):
            return p in ctx.planets and (ctx.is_exalted(p) or ctx.is_own_sign(p) or ctx.is_moolatrikona(p) or ctx.is_kendra(ctx.house_of(p)) or ctx.is_trikona(ctx.house_of(p)))

        def rel_house(base, offset0):
            return ((base - 1 + offset0) % 12) + 1 if base else None

        if ctype == "placeholder":
            return []
        if ctype == "planet_in_lagna":
            p = cond.get("planet")
            return success() if p in ctx.planets and ctx.house_of(p) == 1 else []
        if ctype == "planet_in_house":
            p = cond.get("planet")
            h = cond.get("house")
            return success() if p in ctx.planets and ctx.house_of(p) == h else []
        if ctype == "venus_in_house":
            h = cond.get("house")
            return success() if "Venus" in ctx.planets and ctx.house_of("Venus") == h else []
        if ctype == "benefic_in_house":
            h = cond.get("house")
            return success() if any(ctx.house_of(p) == h for p in BENEFICS if p in ctx.planets) else []
        if ctype == "planets_in_house":
            h = cond.get("house")
            ps = planet_list()
            return success() if h and ps and all(ctx.house_of(p) == h for p in ps) else []
        if ctype == "planets_conjunct_in_same_house":
            ps = planet_list()
            return success() if len(ps) >= 2 and len({ctx.house_of(p) for p in ps}) == 1 else []
        if ctype == "planets_in_exactly_n_signs":
            ps = planet_list(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'])
            n = cond.get("n")
            return success() if n and len({ctx.sign_of(p) for p in ps if p in ctx.planets}) == n else []
        if ctype == "planets_in_kendras":
            ps = planet_list()
            return success() if ps and all(ctx.is_kendra(ctx.house_of(p)) for p in ps) else []
        if ctype == "planets_in_trines":
            ps = planet_list()
            return success() if ps and all(ctx.is_trikona(ctx.house_of(p)) for p in ps) else []
        if ctype == "malefics_in_kendras_and_trines":
            ps = [p for p in MALEFICS if p in ctx.planets]
            return success() if any(ctx.is_kendra(ctx.house_of(p)) for p in ps) and any(ctx.is_trikona(ctx.house_of(p)) for p in ps) else []
        if ctype == "malefics_in_lagna":
            return success() if any(ctx.house_of(p) == 1 for p in MALEFICS if p in ctx.planets) else []
        if ctype == "malefics_in_trines":
            return success() if any(ctx.is_trikona(ctx.house_of(p)) for p in MALEFICS if p in ctx.planets) else []
        if ctype == "planet_exalted_in_kendra":
            p = cond.get("planet")
            return success() if p in ctx.planets and ctx.is_exalted(p) and ctx.is_kendra(ctx.house_of(p)) else []
        if ctype == "lord_exalted":
            p = house_lord(cond.get("lord_of") or cond.get("house"))
            return success() if p and ctx.is_exalted(p) else []
        if ctype == "lord_in_kendra":
            p = house_lord(cond.get("lord_of") or cond.get("house"))
            return success() if p and ctx.is_kendra(ctx.house_of(p)) else []
        if ctype == "lord_in_exaltation_own_or_mool_trikona":
            p = house_lord(cond.get("lord_of") or cond.get("house"))
            return success() if p and (ctx.is_exalted(p) or ctx.is_own_sign(p) or ctx.is_moolatrikona(p)) else []
        if ctype == "mercury_strong_in_kendra_or_trikona":
            return success() if "Mercury" in ctx.planets and is_strong("Mercury") and (ctx.is_kendra(ctx.house_of("Mercury")) or ctx.is_trikona(ctx.house_of("Mercury"))) else []
        if ctype == "moon_strong":
            return success() if "Moon" in ctx.planets and is_strong("Moon") else []
        if ctype == "planet_in_own_or_exalted_sign":
            p = cond.get("planet")
            return success() if p in ctx.planets and (ctx.is_own_sign(p) or ctx.is_exalted(p)) else []
        if ctype == "planet_aspected_by_planet":
            p = cond.get("planet") or cond.get("to")
            by = cond.get("by") or cond.get("from")
            return success() if p in ctx.planets and by in ctx.planets and aspects(by, p) else []
        if ctype == "navamsa_lord_of_2_5_11_exalted_joins_9th_lord":
            l9 = house_lord(9)
            for h in (2, 5, 11):
                lord_h = house_lord(h)
                disp = ctx.navamsa_dispositor(lord_h) if lord_h else None
                if disp and l9 and disp in ctx.planets and ctx.is_exalted(disp) and related(disp, l9):
                    return success()
            return []
        if ctype == "navamsa_lord_of_moon_exalted_in_rasi":
            disp = ctx.navamsa_dispositor("Moon")
            return success() if disp and disp in ctx.planets and ctx.is_exalted(disp) else []
        if ctype == "navamsa_dispositor_exalted_in_10th_with_lagna_lord":
            ref = cond.get("reference_planet")
            if ref == "10th_lord":
                ref_planet = house_lord(10)
            else:
                ref_planet = ref if ref in ctx.planets else None
            disp = ctx.navamsa_dispositor(ref_planet) if ref_planet else None
            l1 = house_lord(1)
            return success() if disp and l1 and disp in ctx.planets and ctx.is_exalted(disp) and ctx.house_of(disp) == 10 and related(disp, l1) else []
        if ctype == "navamsa_lord_of_4th_lord_in_12th":
            l4 = house_lord(4)
            disp = ctx.navamsa_dispositor(l4) if l4 else None
            return success() if disp and disp in ctx.planets and ctx.house_of(disp) == 12 else []
        if ctype == "moon_with_malefics_in_navamsa_cancer_scorpio":
            moon_sign = ctx.d9_sign_of("Moon")
            moon_house = ctx.d9_house_of("Moon")
            return success() if moon_sign in {"Cancer", "Scorpio"} and moon_house and any(ctx.d9_house_of(p) == moon_house for p in MALEFICS if p in ctx.planets and p != "Moon") else []
        if ctype == "sun_and_mandi_in_house":
            target = cond.get("house") or cond.get("in_house")
            if target is None and cond.get("house_offset") is not None:
                target = int(cond.get("house_offset")) + 1
            return success() if target and ctx.house_of("Sun") == target and ctx.upagraha_house("maandi") == target else []
        if ctype == "planet_conjunct_planet":
            a = cond.get("planet") or cond.get("a")
            b = cond.get("with") or cond.get("b")
            return success() if a in ctx.planets and b in ctx.planets and ctx.house_of(a) == ctx.house_of(b) else []
        if ctype == "lord_in_house":
            lord = ctx.lord_of_house(cond.get("lord_of") or cond.get("house") or cond.get("lord_house"))
            target = cond.get("in_house") or cond.get("target_house")
            return success() if lord and ctx.house_of(lord) == target else []
        if ctype == "house_lord_in_kendra":
            lord = ctx.lord_of_house(cond.get("house"))
            return success() if lord and ctx.is_kendra(ctx.house_of(lord)) else []
        if ctype == "house_lord_in_trine":
            lord = ctx.lord_of_house(cond.get("house"))
            return success() if lord and ctx.is_trikona(ctx.house_of(lord)) else []
        if ctype in ("lagna_hemmed_by_malefics_not_aspected_by_benefics", "lagna_hemmed_by_benefics_not_aspected_by_malefics"):
            group = MALEFICS if "malefics" in ctype else BENEFICS
            blockers = BENEFICS if "malefics" in ctype else MALEFICS
            has_2 = any(ctx.house_of(p) == 2 for p in group if p in ctx.planets)
            has_12 = any(ctx.house_of(p) == 12 for p in group if p in ctx.planets)
            aspected = any(aspects(p, 1) for p in blockers if p in ctx.planets)
            return success() if has_2 and has_12 and not aspected else []
        if ctype == "planets_in_mutual_kendras_or_conjunction":
            ps = planet_list()
            if len(ps) >= 2:
                a, b = ps[0], ps[1]
                ha, hb = ctx.house_of(a), ctx.house_of(b)
                return success() if ha and hb and (ha == hb or ctx.house_offset(ha, hb) in (0, 3, 6, 9)) else []
        if ctype == "lords_in_mutual_conjunction_or_aspect":
            houses = cond.get("lords") or []
            ps = [house_lord(h) for h in houses]
            return success() if len(ps) >= 2 and related(ps[0], ps[1]) else []
        if ctype == "aspected_by_benefics":
            p = cond.get("planet")
            if isinstance(p, str) and p.endswith("_lord"):
                p = house_lord(int(p.split("_")[0])) if p.split("_")[0].isdigit() else None
            return success() if p and any(aspects(b, p) for b in BENEFICS if b in ctx.planets) else []
        if ctype == "aspected_by_malefic":
            p = cond.get("planet")
            if p == "4th_lord":
                p = house_lord(4)
            return success() if p and any(aspects(m, p) for m in MALEFICS if m in ctx.planets) else []
        if ctype == "5th_lord_afflicted_by_saturn_or_rahu":
            p = house_lord(5)
            return success() if p and (related(p, "Saturn") or related(p, "Rahu")) else []
        if ctype == "malefic_in_lagna_or_gulika_in_trine_OR_gulika_with_kendra_trine_lord_OR_l1_with_rahu_sat_ket":
            l1 = house_lord(1)
            gh = ctx.upagraha_house("gulika")
            # PyJHora: condition 3 stands alone; condition 1 requires BOTH malefic in Lagna AND Gulika in trine.
            l1_with_rahu_sat_ket = l1 and any(ctx.house_of(l1) == ctx.house_of(p) for p in ["Rahu", "Saturn", "Ketu"] if p in ctx.planets and p != l1)
            if l1_with_rahu_sat_ket:
                return success()
            if gh is None:
                return []
            malefic_in_lagna = any(ctx.house_of(p) == 1 for p in MALEFICS if p in ctx.planets)
            gulika_in_trine = gh in (1, 5, 9)
            if malefic_in_lagna and gulika_in_trine:
                return success()
            kendra_trine_lords = {house_lord(h) for h in (1, 4, 5, 7, 9, 10)}
            gulika_with_kendra_trine_lord = any(
                lord and lord in ctx.planets and ctx.house_of(lord) == gh for lord in kendra_trine_lords
            )
            return success() if gulika_with_kendra_trine_lord else []
        if ctype == "same_lord_for_1st_and_4th":
            return success() if house_lord(1) == house_lord(4) else []
        if ctype == "1st_and_4th_lords_are_natural_or_temporal_friends":
            # 保守近似：同宫/互相位视作 temporal association。
            l1, l4 = house_lord(1), house_lord(4)
            return success() if l1 and l4 and related(l1, l4) else []
        if ctype == "1st_and_4th_lords_aspected_by_benefics":
            l1, l4 = house_lord(1), house_lord(4)
            ok1 = l1 and any(aspects(b, l1) for b in BENEFICS if b in ctx.planets)
            ok4 = l4 and any(aspects(b, l4) for b in BENEFICS if b in ctx.planets)
            return success() if ok1 and ok4 else []
        if ctype == "4th_lord_is_benefic_aspected_by_benefic":
            l4 = house_lord(4)
            return success() if l4 and is_benefic(l4) and any(aspects(b, l4) for b in BENEFICS if b in ctx.planets and b != l4) else []
        if ctype == "4th_house_or_lord_with_aspect_of_jupiter":
            l4 = house_lord(4)
            return success() if "Jupiter" in ctx.planets and (aspects("Jupiter", 4) or (l4 and related("Jupiter", l4))) else []
        if ctype == "4th_lord_with_benefics":
            l4 = house_lord(4)
            return success() if l4 and any(ctx.house_of(l4) == ctx.house_of(b) for b in BENEFICS if b in ctx.planets and b != l4) else []
        if ctype == "4th_lord_aspected_by_benefics":
            l4 = house_lord(4)
            return success() if l4 and any(aspects(b, l4) for b in BENEFICS if b in ctx.planets and b != l4) else []
        if ctype == "4th_lord_in_kendra_or_trikona":
            l4 = house_lord(4)
            return success() if l4 and (ctx.is_kendra(ctx.house_of(l4)) or ctx.is_trikona(ctx.house_of(l4))) else []
        if ctype == "lagna_lord_in_dry_sign":
            l1 = house_lord(1)
            # PyJHora const.dry_signs = [0,1,2,4,5,8] = Aries,Taurus,Gemini,Leo,Virgo,Sagittarius
            dry_signs = {"Aries", "Taurus", "Gemini", "Leo", "Virgo", "Sagittarius"}
            # PyJHora const.dry_planets = [0,2,6] = Sun,Mars,Saturn
            dry_lords = {"Sun", "Mars", "Saturn"}
            # PyJHora Y112: (ll_house in dry_signs) OR (ll_house_owner in dry_planets)
            # ll_house = sign of lagna lord; ll_house_owner = dynamic lord of that sign
            ll_in_dry = l1 and ctx.sign_of(l1) in dry_signs
            l1_house = ctx.house_of(l1) if l1 else None
            ll_owner_dry = l1_house and ctx.lord_of_house(l1_house) in dry_lords
            return success() if l1 and (ll_in_dry or ll_owner_dry) else []
        if ctype == "navamsa_lagna_in_dry_planet_sign":
            d9_asc = ctx.d9.get("ascendant")
            dry_lords = {"Sun", "Mars", "Saturn"}
            return success() if d9_asc and SIGN_LORDS.get(d9_asc) in dry_lords else []
        if ctype == "lagna_lord_and_navamsa_lord_both_in_watery_signs":
            l1 = house_lord(1)
            navamsa_lord = ctx.navamsa_dispositor(l1) if l1 else None
            watery = {"Cancer", "Scorpio", "Pisces"}
            return success() if l1 and navamsa_lord and ctx.sign_of(l1) in watery and ctx.sign_of(navamsa_lord) in watery else []
        if ctype == "jupiter_in_lagna_or_aspects_lagna_from_watery":
            return success() if "Jupiter" in ctx.planets and (ctx.house_of("Jupiter") == 1 or (ctx.sign_of("Jupiter") in {"Cancer", "Scorpio", "Pisces"} and aspects("Jupiter", 1))) else []
        if ctype == "lagna_watery_with_benefics_or_lagna_lord_watery":
            l1 = house_lord(1)
            asc_watery = ctx.ascendant in {"Cancer", "Scorpio", "Pisces"}
            watery_planets = {"Moon", "Venus"}
            return success() if (asc_watery and any(ctx.house_of(b) == 1 for b in BENEFICS if b in ctx.planets)) or (l1 in watery_planets) else []
        if ctype == "jupiter_in_lagna_mars_in_7th":
            return success() if ctx.house_of("Jupiter") == 1 and ctx.house_of("Mars") == 7 else []
        if ctype == "saturn_in_lagna_mars_in_5_7_9":
            return success() if ctx.house_of("Saturn") == 1 and ctx.house_of("Mars") in (5, 7, 9) else []
        if ctype == "saturn_in_12th_with_waning_moon":
            return success() if ctx.house_of("Saturn") == 12 and ctx.is_waning_moon() else []
        if ctype == "moon_mercury_in_kendra_with_planet":
            return success() if ctx.house_of("Moon") == ctx.house_of("Mercury") and ctx.is_kendra(ctx.house_of("Moon")) and len(ctx.planets_in_house(ctx.house_of("Moon"))) >= 3 else []
        if ctype == "four_planet_chain_all_in_kendra_trine_or_exaltation":
            l1 = house_lord(1)
            if not l1:
                return []
            chain = [l1]
            current = l1
            for _ in range(2):
                sign_current = ctx.sign_of(current)
                current = SIGN_LORDS.get(sign_current) if sign_current else None
                if not current:
                    return []
                chain.append(current)
            d9_disp = ctx.navamsa_dispositor(current)
            if not d9_disp:
                return []
            chain.append(d9_disp)
            ok = all(
                p in ctx.planets and (ctx.is_kendra(ctx.house_of(p)) or ctx.is_trikona(ctx.house_of(p)) or ctx.is_exalted(p))
                for p in chain
            )
            return success() if ok else []
        if ctype == "planets_in_relative_houses":
            base = house(cond.get("from", "lagna")) or 1
            offsets = cond.get("houses") or cond.get("offsets") or []
            ps = planet_list(ALL_PLANETS)
            targets = {rel_house(base, int(o) % 12) for o in offsets}
            return success() if any(ctx.house_of(p) in targets for p in ps) else []
        if ctype == "house_empty":
            h = cond.get("house")
            return success() if h and not ctx.planets_in_house(h) else []
        if ctype == "planet_in_house_with_aspect_or_conjunction":
            """Jupiter in 2nd/5th, conjoined or aspected by Mercury AND Venus (kalaanidhi yoga)"""
            planet = cond.get("planet", "")
            house_offsets = cond.get("house_offsets", [])
            aspecting_or_conjoining = cond.get("aspecting_or_conjoining", [])
            if not planet or planet not in ctx.planets:
                return []
            ph = ctx.house_of(planet)
            if ph is None:
                return []
            # Check planet is in one of the target houses (from lagna)
            target_houses = set()
            for off in house_offsets:
                h = (1 + off) % 12
                if h == 0: h = 12
                target_houses.add(h)
            if ph not in target_houses:
                return []
            # Check ALL specified planets must conjoin or aspect
            for other in aspecting_or_conjoining:
                if other not in ctx.planets:
                    return []
                # Check conjunction (same house)
                if ctx.house_of(other) == ph:
                    continue
                # Check aspect (graha drishti)
                if aspects(other, planet):
                    continue
                # Neither conjoined nor aspecting → fail
                return []
            return success()
        return []

    # ------------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------------
    def _resolve_binding(self, ref, ctx, bindings):
        """解析引用，支持变量绑定替换"""
        if ref is None:
            return []
        if isinstance(ref, str) and ref.startswith("$"):
            # 绑定变量引用，如 "$a"
            val = bindings.get(ref[1:])
            if val is None:
                return []
            return [val] if isinstance(val, str) else (val if isinstance(val, list) else [val])
        return ctx.resolve(ref)

    @staticmethod
    def _offset_name(off: int) -> str:
        names = {0: "同宫", 1: "2宫", 2: "3宫", 3: "4宫(Kendra)", 4: "5宫(Trine)",
                 5: "6宫", 6: "7宫(Kendra)", 7: "8宫", 8: "9宫(Trine)",
                 9: "10宫(Kendra)", 10: "11宫", 11: "12宫"}
        return names.get(off, f"{off+1}宫")


# ============================================================================
# 便捷入口
# ============================================================================
def detect_yogas(planets: Dict[str, Dict], ascendant: str,
                 rules_path: Optional[str] = None,
                 context: Optional[Dict] = None) -> List[Dict]:
    """便捷函数：检测 Yoga"""
    if rules_path is None:
        # 自动查找规则文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        skill_dir = os.path.dirname(script_dir)
        rules_path = os.path.join(skill_dir, "references", "yoga_rules.json")
    engine = YogaEngine(rules_path)
    return engine.detect(planets, ascendant, context=context)


def detect_yogas_from_json(chart_json: Dict, rules_path: Optional[str] = None) -> List[Dict]:
    """从 chart JSON 结构中提取 planets + ascendant 并检测"""
    planets = chart_json.get("planets", {})
    asc = chart_json.get("ascendant", chart_json.get("ascendant_sign", "Aries"))
    return detect_yogas(planets, asc, rules_path, context=chart_json.get("context"))


if __name__ == "__main__":
    # 简单自测
    test_planets = {
        "Sun": {"sign": "Aries", "house": 1, "degree": 10.5},
        "Moon": {"sign": "Cancer", "house": 4, "degree": 15.0},
        "Jupiter": {"sign": "Libra", "house": 7, "degree": 20.0},
    }
    print("YogaEngine loaded. Run with a rules file to test.")
