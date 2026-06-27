#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yoga 准确率验证框架 v1.0

功能：
1. 用同一组出生数据，分别调用 PyJhora 和 skill 的 Yoga 检测
2. 对比结果，生成准确率报告
3. 支持批量测试用例（JSON 文件）

用法：
  python3 validate_yoga_accuracy.py --benchmark
  python3 validate_yoga_accuracy.py --test-cases test_cases.json
  python3 validate_yoga_accuracy.py --interactive
"""

import json
import re
import sys
import glob
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from ayanamsa_utils import sidereal_flags

# ============================================================
# 路径设置
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent

# 确保 skill 脚本在 sys.path 中
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ============================================================
# 常量（自包含，与 yoga_engine.py 一致）
# ============================================================
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

# ============================================================
# Skill 功能性 Yoga Category（PyJhora 中无对应规则，属于 skill 特色）
# ============================================================
FUNCTIONAL_CATEGORIES = {
    'dhana', 'kalatra', 'putra', 'ayur', 'vidya', 'shakti',
    'karma', 'asha', 'moksha', 'aryama', 'guru', 'ari', 'varga',
    # raja 虽然是经典概念，但 PyJhora 没有单独函数，skill 按功能性实现
    'raja',
}

# 加载 skill 的 yoga_rules.json，建立 name -> category 映射
def _load_skill_rule_categories() -> Dict[str, str]:
    """读取 yoga_rules.json，返回 {归一化名称: category}"""
    rules_path = SKILL_ROOT / "references" / "yoga_rules.json"
    if not rules_path.exists():
        return {}
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        mapping = {}
        for r in data.get('rules', []):
            if not r.get('enabled', True):
                continue
            key = normalize_name(r.get('name', ''))
            if key:
                mapping[key] = r.get('category', 'unknown')
        return mapping
    except Exception:
        return {}

# 延迟加载，避免在模块导入时读取文件
_SKILL_RULE_CATEGORIES: Optional[Dict[str, str]] = None

def get_skill_rule_categories() -> Dict[str, str]:
    global _SKILL_RULE_CATEGORIES
    if _SKILL_RULE_CATEGORIES is None:
        _SKILL_RULE_CATEGORIES = _load_skill_rule_categories()
    return _SKILL_RULE_CATEGORIES


# ============================================================
# Swiss Ephemeris 星盘计算（独立实现，不依赖 jyotish_engine）
# ============================================================
def skill_compute_chart(year, month, day, hour, minute, lat, lon, tz,
                          node_mode='mean'):
    """
    用 Swiss Ephemeris 计算星盘。
    返回：(planets_dict, asc_idx, jd, ayanamsa)
    """
    import swisseph as swe

    # Julian Day（本地时间 → UTC）
    hour_decimal = hour + minute / 60.0 - tz
    jd = swe.julday(year, month, day, hour_decimal)

    # Ayanamsa
    flags = sidereal_flags(swe, 'lahiri')
    ayanamsa = swe.get_ayanamsa_ut(jd)

    # Ascendant
    asc_info = swe.houses(jd, lat, lon, b'A')  # 'A' = equal houses (Vedic)
    asc_long = asc_info[0][0]
    asc_deg = (asc_long - ayanamsa) % 360
    asc_sign = int(asc_deg / 30)
    asc_idx = asc_sign + 1  # 1-based

    # 行星
    planets = {}
    planet_map = [
        ('Sun', swe.SUN), ('Moon', swe.MOON), ('Mars', swe.MARS),
        ('Mercury', swe.MERCURY), ('Jupiter', swe.JUPITER),
        ('Venus', swe.VENUS), ('Saturn', swe.SATURN),
    ]

    for pname, pid in planet_map:
        res = swe.calc_ut(jd, pid, flags)
        long = res[0][0] % 360
        sign = int(long / 30)
        deg = long % 30.0
        speed = res[0][3]
        is_retro = speed < 0
        house = ((sign - asc_sign) % 12) + 1
        planets[pname] = {
            'longitude': long, 'sign': SIGNS[sign],
            'degree': deg, 'house': house,
            'is_retro': is_retro, 'is_combust': False,
        }

    # Rahu / Ketu
    if node_mode == 'true':
        rahu_res = swe.calc_ut(jd, swe.TRUE_NODE, flags)
    else:
        rahu_res = swe.calc_ut(jd, swe.MEAN_NODE, flags)
    rahu_long = rahu_res[0][0] % 360
    ketu_long = (rahu_long + 180.0) % 360

    for name, long in [('Rahu', rahu_long), ('Ketu', ketu_long)]:
        sign = int(long / 30)
        deg = long % 30.0
        house = ((sign - asc_sign) % 12) + 1
        planets[name] = {
            'longitude': long, 'sign': SIGNS[sign],
            'degree': deg, 'house': house,
            'is_retro': False, 'is_combust': False,
        }

    # 燃烧判断（简化）
    sun_long = planets['Sun']['longitude']
    combust_limits = {
        'Moon': 12.0, 'Mars': 17.0, 'Mercury': 14.0,
        'Jupiter': 11.0, 'Venus': 10.0, 'Saturn': 15.0,
    }
    for pname, limit in combust_limits.items():
        p_long = planets[pname]['longitude']
        diff = abs((p_long - sun_long + 180) % 360 - 180)
        planets[pname]['is_combust'] = diff < limit

    return planets, asc_idx, jd, ayanamsa


def skill_detect_yogas(planets, asc):
    """调用 skill 的 Yoga 引擎检测 Yoga"""
    from yoga_engine import detect_yogas
    return detect_yogas(planets, asc)


# ============================================================
# PyJhora 接口封装
# ============================================================
def init_external_benchmark():
    """初始化 PyJhora，返回是否成功"""
    try:
        import jhora.horoscope.chart.yoga as py_yoga
        import jhora.panchanga.drik as drik
        import jhora.horoscope.chart.charts as charts
        import jhora.const as const
        return True
    except ImportError as e:
        print(f"⚠️ PyJhora 导入失败: {e}")
        return False


def external_benchmark_jd(year, month, day, hour_frac):
    """计算 Julian Day（与 PyJhora 一致）"""
    import swisseph as swe
    return swe.julday(year, month, day, hour_frac)


def external_benchmark_get_yogas(jd, lat, lon, tz, divisional_chart_factor=1):
    """
    调用 PyJhora 获取 D1 宫盘的 Yoga 检测结果。
    返回：{yoga_function_name: {"name": ..., "desc": ..., "benefits": ...}}
    """
    import jhora.horoscope.chart.yoga as py_yoga
    import jhora.panchanga.drik as drik

    place = drik.Place("TestPlace", lat, lon, tz)
    yoga_results, _, _ = py_yoga.get_yoga_details(
        jd, place, divisional_chart_factor=divisional_chart_factor, language='en'
    )
    # yoga_results: {yoga_function_name: [chart_id, yoga_name, yoga_description, yoga_benefits]}
    result = {}
    for fname, details in yoga_results.items():
        result[fname] = {
            "name": details[1] if len(details) > 1 else fname,
            "desc": details[2] if len(details) > 2 else "",
            "benefits": details[3] if len(details) > 3 else "",
            "chart_id": details[0] if len(details) > 0 else "",
        }
    return result


# ============================================================
# 名称归一化（用于对比）
# ============================================================
def normalize_name(name: str) -> str:
    """归一化 Yoga 名称（与 benchmark_yoga_coverage.py 一致）"""
    s = name.lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    for suffix in ("_yoga", "_graha", "_classic", "_calculation", "_calc"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    s = re.sub(r"_\d+$", "", s)
    return s


# 单向名称映射：PyJhora 归一化名称 -> skill 标准归一化名称
# 键是 PyJhora 的归一化名称，值是 skill 的标准归一化名称
# 两边都会通过 _canonical_name() 映射到统一的标准名称空间
CROSS_NAME_MAP = {
    # --- 经典 Yoga 别名（PyJhora -> skill） ---
    "nipuna": "budhaditya",
    "gaja_kesari": "gajakesari",
    "maalavya": "malavya",
    "shasha": "sasa",
    "murdha": "moordha",
    "kedara": "kedaara",
    "kaahala": "kahala",
    "daama": "dama",
    "veenaa": "veena",
    "paasa": "pasa",
    "mridang": "mridanga",
    "sankh": "sankha",
    "chatusagar": "chatussagara",
    "rajalakshan": "rajalakshana",
    "bhaarathi": "bharati",
    "saraswathi": "saraswati",
    "kalpadrum": "kalpadruma",
    "trikala_gnana": "thrikaala_gnana",
    "yukti_samanwithavagmi": "yukthi_samanwithavagmi",
    "mathibhraman": "mathibhramana",
    "swaviryaddhana": "swaveeryaddhana",
    "antya_vayasi_dhana": "anthya_vayasi_dhana",
    "madhya_vayasi_dhana": "madhya_vayasi_dhana",
    "matrumuladdhana": "matrumooladdhana",
    "kalanirdesat_puthranaasa": "kaalanirdesat_puthranaasa",
    "dvadasa_sahodara": "dwadasa_sahodara",
    "vahan": "vahana",
    "parakram": "parakrama",
    "yuddha_pravin": "yuddha_praveena",
    "sumukh": "sumukha",
    "durmukh": "durmukha",
    "kapat": "kapata",
    "nishkapat": "nishkapata",
    "asatyavad": "asatyavadi",
    "bhratruvriddh": "bhratruvriddhi",
    "bandhubhisthyakt": "bandhubhisthyaktha",
    "bandhu_pujy": "bandhu_pujya",
    "matrunas": "matrunasa",
    "matru_sneh": "matru_sneha",
    "bahu_puthr": "bahu_puthra",
    "bahu_stri": "bahu_sthree",
    "eka_puthr": "eka_puthra",
    "satkalatr": "satkalatra",
    "sareera_soukh": "sareera_soukhya",
    "rogagrasth": "rogagrastha",
    "dehasthoul": "dehasthoulya",
    "dehapusht": "dehapushti",
    "krisang": "krisanga",
    "sada_sanchar": "sada_sanchara",
    "annadan": "annadana",
    "amal": "amala",
    "asubh": "asubha",
    "guhyarog": "guhyaroga",
    "dharidhr": "dharidhra",
    "vanchana_chora_bheeth": "vanchana_chora_bheethi",
    "rajabhrasht": "rajabhrashta",
    "vran": "vrana",
    "buddhimatur": "buddhimaturya",
    "ayatna_griha_prapt": "ayatna_griha_prapta",
}


def get_skill_yoga_keys(yoga_list: List[Dict]) -> Set[str]:
    """从 skill 检测结果中提取归一化名称集合"""
    keys = set()
    for y in yoga_list:
        for field in ['name', 'name_cn']:
            val = y.get(field, "")
            if not val or not isinstance(val, str):
                continue
            # 排除纯数字、空字符串、太短的名字
            stripped = val.strip()
            if not stripped or stripped.replace('_', '').replace('-', '').isdigit():
                continue
            if len(stripped) <= 2:
                continue
            key = normalize_name(val)
            if not key or key.replace('_', '').isdigit():
                continue
            key = _canonical_name(key)
            keys.add(key)
    return keys


def _canonical_name(key: str) -> str:
    """通过 CROSS_NAME_MAP 将别名映射到统一的标准名称"""
    return CROSS_NAME_MAP.get(key, key)


def get_external_benchmark_yoga_keys(external_benchmark_results: Dict[str, dict]) -> Set[str]:
    """从 PyJhora 检测结果中提取归一化名称集合"""
    keys = set()
    for fname in external_benchmark_results.keys():
        # 去掉 _from_jd_place 等后缀
        base = re.sub(r"_(from_jd_place|from_planet_positions|calculation|calc)$",
                      "", fname)
        base = base.replace("_yoga", "")
        key = normalize_name(base)
        # 映射到标准名称
        key = _canonical_name(key)
        keys.add(key)
    return keys


# ============================================================
# 核心验证逻辑
# ============================================================
def validate_one_case(case: dict, run_external_benchmark: bool = True) -> dict:
    """
    验证单个测试用例。

    case = {
        "name": "Einstein",
        "year": 1879, "month": 3, "day": 14,
        "hour": 10, "minute": 30,
        "lat": 48.0, "lon": 11.0, "tz": 1.0
    }
    """
    result = {
        "case_name": case.get("name", "unknown"),
        "birth": f"{case['year']}-{case['month']:02d}-{case['day']:02d} "
                f"{case.get('hour', 12):02d}:{case.get('minute', 0):02d}",
        "skill_yogas": [],
        "external_benchmark_yogas": [],
        "matched": [],
        "skill_only": [],   # false positive
        "external_benchmark_only": [], # false negative
        "error": None,
    }

    year = case['year']
    month = case['month']
    day = case['day']
    hour = case.get('hour', 12)
    minute = case.get('minute', 0)
    lat = case['lat']
    lon = case['lon']
    tz = case.get('tz', 0)

    # --- Skill 检测 ---
    try:
        planets, asc, jd, ayanamsa = skill_compute_chart(
            year, month, day, hour, minute, lat, lon, tz
        )
        skill_yogas = skill_detect_yogas(planets, asc)
        result['skill_yogas'] = [y.get('name', y.get('id', '?')) for y in skill_yogas]
        result['skill_count'] = len(skill_yogas)
        result['skill_details'] = []
        for y in skill_yogas:
            result['skill_details'].append({
                'name': y.get('name', ''),
                'id': y.get('id', ''),
                'strength': y.get('strength', ''),
            })
    except Exception as e:
        result['error'] = f"Skill error: {e}\n{traceback.format_exc()}"
        return result

    # --- PyJhora 检测 ---
    if run_external_benchmark:
        try:
            jd_py = external_benchmark_jd(year, month, day, hour + minute / 60.0)
            external_benchmark_results = external_benchmark_get_yogas(jd_py, lat, lon, tz,
                                                 divisional_chart_factor=1)
            result['external_benchmark_yogas'] = list(external_benchmark_results.keys())
            result['external_benchmark_count'] = len(external_benchmark_results)
            result['external_benchmark_details'] = []
            for fname, details in external_benchmark_results.items():
                result['external_benchmark_details'].append({
                    'function': fname,
                    'name': details.get('name', ''),
                    'desc': details.get('desc', ''),
                })
        except Exception as e:
            result['error'] = f"PyJhora error: {e}\n{traceback.format_exc()}"
            return result

        # --- 对比 ---
        skill_keys = get_skill_yoga_keys(skill_yogas)
        external_benchmark_keys = get_external_benchmark_yoga_keys(external_benchmark_results)

        result['matched'] = sorted(skill_keys & external_benchmark_keys)
        result['skill_only'] = sorted(skill_keys - external_benchmark_keys)
        result['external_benchmark_only'] = sorted(external_benchmark_keys - skill_keys)

        # --- 分类：功能性 Yoga vs 经典 Yoga ---
        cat_map = get_skill_rule_categories()
        result['skill_only_functional'] = []
        result['skill_only_classic'] = []
        for key in result['skill_only']:
            cat = cat_map.get(key, 'unknown')
            if cat in FUNCTIONAL_CATEGORIES:
                result['skill_only_functional'].append(key)
            else:
                result['skill_only_classic'].append(key)

    return result


def run_validation(cases: List[dict], run_external_benchmark: bool = True) -> dict:
    """运行批量验证"""
    report = {
        "total_cases": len(cases),
        "cases": [],
        "summary": {
            "total_skill_yogas": 0,
            "total_external_benchmark_yogas": 0,
            "total_matched": 0,
            "total_skill_only": 0,
            "total_external_benchmark_only": 0,
            "total_skill_only_functional": 0,
            "total_skill_only_classic": 0,
        }
    }

    for case in cases:
        name = case.get('name', 'unknown')
        print(f"🔍 验证: {name} ({case['year']}-{case['month']:02d}-{case['day']:02d})")
        r = validate_one_case(case, run_external_benchmark=run_external_benchmark)
        report['cases'].append(r)

        if r['error']:
            print(f"   ❌ 错误: {r['error'][:300]}")
            continue

        sc = r.get('skill_count', 0)
        pc = r.get('external_benchmark_count', '?')
        func_n = len(r.get('skill_only_functional', []))
        classic_n = len(r.get('skill_only_classic', []))
        print(f"   Skill: {sc} | PyJhora: {pc}")
        print(f"   匹配: {len(r['matched'])} | "
              f"Skill独有: {len(r['skill_only'])} (功能性{func_n}, 经典{classic_n}) | "
              f"PyJhora独有: {len(r['external_benchmark_only'])}")

        report['summary']['total_skill_yogas'] += sc
        if isinstance(pc, int):
            report['summary']['total_external_benchmark_yogas'] += pc
        report['summary']['total_matched'] += len(r['matched'])
        report['summary']['total_skill_only'] += len(r['skill_only'])
        if isinstance(pc, int):
            report['summary']['total_external_benchmark_only'] += len(r['external_benchmark_only'])
        report['summary']['total_skill_only_functional'] += func_n
        report['summary']['total_skill_only_classic'] += classic_n

    return report


# ============================================================
# 测试用例
# ============================================================
BENCHMARK_CASES = [
    {
        "name": "Einstein",
        "year": 1879, "month": 3, "day": 14,
        "hour": 10, "minute": 30,
        "lat": 48.0, "lon": 11.0, "tz": 1.0,
    },
    {
        "name": "Steve Jobs",
        "year": 1955, "month": 2, "day": 24,
        "hour": 19, "minute": 30,
        "lat": 37.0, "lon": -122.0, "tz": -8.0,
    },
    {
        "name": "NM Gandhi",
        "year": 1869, "month": 10, "day": 2,
        "hour": 8, "minute": 52,
        "lat": 21.0, "lon": 73.0, "tz": 5.5,
    },
    {
        "name": "APJ Abdul Kalam",
        "year": 1931, "month": 10, "day": 15,
        "hour": 6, "minute": 0,
        "lat": 8.0, "lon": 78.0, "tz": 5.5,
    },
    {
        "name": "Queen Elizabeth II",
        "year": 1926, "month": 4, "day": 21,
        "hour": 2, "minute": 40,
        "lat": 51.0, "lon": 0.0, "tz": 0.0,
    },
]


# ============================================================
# 报告输出
# ============================================================
def print_report(report: dict):
    """打印验证报告"""
    print("\n" + "=" * 70)
    print("🧘 Yoga 准确率验证报告")
    print("=" * 70)

    summary = report['summary']
    total_skill = summary['total_skill_yogas']
    total_external_benchmark = summary['total_external_benchmark_yogas']
    matched = summary['total_matched']
    skill_only = summary['total_skill_only']
    external_benchmark_only = summary['total_external_benchmark_only']
    func_only = summary.get('total_skill_only_functional', 0)
    classic_only = summary.get('total_skill_only_classic', 0)

    print(f"\n📊 汇总:")
    print(f"  测试用例数: {report['total_cases']}")
    print(f"  Skill 检测总数: {total_skill}")
    print(f"  PyJhora 检测总数: {total_external_benchmark}")
    print(f"  匹配总数: {matched}")
    print(f"  Skill 独有: {skill_only} (功能性{func_only}, 经典{classic_only})")
    print(f"  PyJhora 独有 (skill 缺失): {external_benchmark_only}")

    if total_skill > 0:
        precision = matched / total_skill * 100
        print(f"\n  总体精确率 (Precision): {precision:.1f}%")

    if total_external_benchmark > 0:
        recall = matched / total_external_benchmark * 100
        print(f"  总体召回率 (Recall): {recall:.1f}%")

    # --- 核心经典 Yoga 准确率（排除 skill 特色功能性 Yoga）---
    classic_skill_total = total_skill - func_only
    if classic_skill_total > 0:
        classic_precision = matched / classic_skill_total * 100
        print(f"\n  🎯 核心经典 Yoga 精确率: {classic_precision:.1f}%")
        print(f"     (排除 {func_only} 条功能性 Yoga 后: {matched}/{classic_skill_total})")
    if total_external_benchmark > 0:
        classic_recall = matched / total_external_benchmark * 100
        print(f"  🎯 核心经典 Yoga 召回率: {classic_recall:.1f}%")

    # --- 全局不匹配统计 ---
    print(f"\n🔍 全局不匹配分析:")
    all_skill_classic = set()
    all_skill_func = set()
    all_external_benchmark_missing = set()
    for r in report['cases']:
        if r.get('error'):
            continue
        all_skill_classic.update(r.get('skill_only_classic', []))
        all_skill_func.update(r.get('skill_only_functional', []))
        all_external_benchmark_missing.update(r.get('external_benchmark_only', []))

    print(f"  Skill 经典 Yoga 不匹配（可能误判）: {len(all_skill_classic)} 种")
    if all_skill_classic:
        print(f"     {sorted(all_skill_classic)[:15]}")
    print(f"  Skill 功能性 Yoga（PyJhora 无对应，属 skill 特色）: {len(all_skill_func)} 种")
    if all_skill_func:
        print(f"     {sorted(all_skill_func)[:15]}")
    print(f"  PyJhora 有但 Skill 缺失的 Yoga: {len(all_external_benchmark_missing)} 种")
    if all_external_benchmark_missing:
        print(f"     {sorted(all_external_benchmark_missing)[:15]}")

    # --- 改进建议 ---
    print(f"\n💡 改进建议:")
    print(f"  1. 【规则校准】以下 {len(all_skill_classic)} 种经典 Yoga 两边实现不一致，")
    print(f"     建议逐条核对 BPHS 原文，修正 skill 规则条件:")
    for name in sorted(all_skill_classic)[:10]:
        print(f"     - {name}")
    if len(all_skill_classic) > 10:
        print(f"     ... 等共 {len(all_skill_classic)} 种")

    missing_top = sorted(all_external_benchmark_missing)[:20]
    print(f"\n  2. 【规则补齐】以下 {len(all_external_benchmark_missing)} 种 Yoga PyJhora 已实现但 skill 缺失，")
    print(f"     建议按优先级补充（推荐先补充高频出现的）:")
    for name in missing_top[:15]:
        print(f"     - {name}")
    if len(all_external_benchmark_missing) > 15:
        print(f"     ... 等共 {len(all_external_benchmark_missing)} 种")

    print(f"\n  3. 【名称映射】当前 CROSS_NAME_MAP 已覆盖常见别名，")
    print(f"     如仍有新别名发现，请添加到映射表中。")

    print(f"\n📋 逐案例详情:")
    for r in report['cases']:
        print(f"\n  【{r['case_name']}】 {r['birth']}")
        if r.get('error'):
            print(f"    ❌ {r['error'][:300]}")
            continue
        sc = r.get('skill_count', 0)
        pc = r.get('external_benchmark_count', '?')
        print(f"    Skill ({sc}): {r['skill_yogas'][:5]}{'...' if len(r['skill_yogas']) > 5 else ''}")
        if 'external_benchmark_yogas' in r:
            print(f"    PyJhora ({pc}): {r['external_benchmark_yogas'][:5]}{'...' if len(r['external_benchmark_yogas']) > 5 else ''}")
        func_n = len(r.get('skill_only_functional', []))
        cls_n = len(r.get('skill_only_classic', []))
        print(f"    匹配: {len(r['matched'])} | Skill独有: {len(r['skill_only'])}(功能{func_n},经典{cls_n}) | PyJhora独有: {len(r['external_benchmark_only'])}")

        if r.get('skill_only_classic'):
            print(f"    Skill 经典不匹配: {r['skill_only_classic'][:10]}")
        if r.get('skill_only_functional'):
            print(f"    Skill 功能性: {r['skill_only_functional'][:10]}")
        if r.get('external_benchmark_only'):
            print(f"    PyJhora 独有: {r['external_benchmark_only'][:10]}")


def save_report(report: dict, output_file: str):
    """保存报告为 JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 报告已保存: {output_file}")


# ============================================================
# 主程序
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Yoga 准确率验证框架")
    parser.add_argument('--test-cases', help='测试用例 JSON 文件路径')
    parser.add_argument('--interactive', action='store_true', help='手动输入出生数据')
    parser.add_argument('--benchmark', action='store_true', help='运行内置基准测试')
    parser.add_argument('--output', '-o', default='validation_report.json', help='输出报告文件')
    parser.add_argument('--skip-pyjhora', action='store_true', help='跳过 PyJhora（只测试 skill）')
    args = parser.parse_args()

    # 检查 PyJhora
    if not args.skip_external_benchmark:
        if not init_external_benchmark():
            print("❌ PyJhora 不可用，请先安装: pip install pyjhora swisseph")
            print("   提示：也可用 --skip-pyjhora 只测试 skill 侧")
            return 1

    # 加载测试用例
    if args.test_cases:
        with open(args.test_cases, 'r', encoding='utf-8') as f:
            cases = json.load(f)
    elif args.benchmark:
        cases = BENCHMARK_CASES
    elif args.interactive:
        cases = [interactive_input()]
    else:
        print("使用 --benchmark 运行内置测试，或 --test-cases 指定测试用例文件")
        return 1

    # 运行验证
    report = run_validation(cases, run_external_benchmark=not args.skip_external_benchmark)

    # 输出报告
    print_report(report)
    save_report(report, args.output)

    return 0


def interactive_input() -> dict:
    """手动输入出生数据"""
    print("\n请输入出生数据:")
    name = input("  姓名 (可选): ").strip() or "Test"
    year = int(input("  年: "))
    month = int(input("  月: "))
    day = int(input("  日: "))
    hour = int(input("  时 (24小时制): "))
    minute = int(input("  分: "))
    lat = float(input("  纬度 (度, 北正南负): "))
    lon = float(input("  经度 (度, 东正西负): "))
    tz = float(input("  时区 (小时, 东正西负): "))

    return {
        "name": name, "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lon": lon, "tz": tz,
    }


if __name__ == '__main__':
    sys.exit(main())
