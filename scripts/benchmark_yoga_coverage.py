#!/usr/bin/env python3
"""
Yoga 覆盖率 benchmark：对比当前 skill JSON 规则库与 PyJHora yoga.py。

目标：
1. 统计当前 references/yoga_rules.json 规则数量和分类分布
2. 若本机存在 PyJHora 安装，提取 jhora.horoscope.chart.yoga.py 中的唯一 Yoga 名称
3. 用名称归一化 + alias 表做近似覆盖匹配
4. 输出覆盖率、疑似缺失项和疑似重复项，作为后续补规则依据

说明：
- 这是覆盖 benchmark，不判断每条规则的数学条件是否与 PyJHora 完全等价。
- PyJHora 大量函数是同一 Yoga 的编号变体；本脚本会把函数名归一为唯一 Yoga 名称。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

SKILL_ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = SKILL_ROOT / "references" / "yoga_rules.json"

# 常见拼写/转写差异。左侧为 PyJHora normalized key，右侧为 skill 中的可能 normalized key。
ALIASES = {
    "sasa": {"shasha", "sasha"},
    "maalavya": {"malavya"},
    "maalaa": {"mala"},
    "maala": {"mala"},
    "gadaa": {"gada"},
    "kedaara": {"kedara"},
    "naukaa": {"nauka"},
    "chaapa": {"chapa"},
    "kaahala": {"kahala"},
    "kalaanidhi": {"kalanidhi"},
    "sreenaatha": {"sreenatha", "srinatha"},
    "vasumathi": {"vasumati"},
    "subha": {"shubha"},
    "dharidhra": {"daridra"},
    "budha_aditya": {"budhaditya", "nipuna"},
    "chandra_mangala": {"chandra_mangal"},
    "gaja_kesari": {"gajakesari"},
    "harihara_brahma": {"harihara_brahma", "hari_hara_brahma"},
    "siva": {"shiva"},
    "vesi": {"vesi"},
    "vosi": {"vosi"},
    "sunaphaa": {"sunapha"},
    "anaphaa": {"anapha"},
    "ubhayachara": {"ubhayachari"},
    "duradhara": {"duradhara"},
}

SKIP_FUNCTIONS = {
    "get_yoga_resources",
    "get_yoga_details",
    "get_yoga_details_for_all_charts",
    "grihanasa_yoga_planet_positions",
    "are_lords_exchanged",
}


def normalize_name(name: str) -> str:
    """Normalize Yoga names for approximate matching."""
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


def extract_skill_names(rules: list[dict]) -> tuple[set[str], dict[str, list[str]]]:
    keys: set[str] = set()
    reverse: dict[str, list[str]] = defaultdict(list)
    for rule in rules:
        raw_names = [rule.get("name", ""), rule.get("name_cn", ""), rule.get("id", "")]
        for raw in raw_names:
            key = normalize_name(raw)
            if not key:
                continue
            keys.add(key)
            reverse[key].append(rule.get("id", "?"))
        # 对英文名进一步拆出核心 token 组合，处理 “Gaja Kesari Yoga (Classic)” 这类名称
        en = rule.get("name", "")
        key = normalize_name(en)
        if key:
            parts = [p for p in key.split("_") if p not in {"yoga", "classic", "from", "lord", "lords", "combination"}]
            if parts:
                compact = "_".join(parts[:3])
                keys.add(compact)
                reverse[compact].append(rule.get("id", "?"))
    return keys, reverse


def extract_pyjhora_names(pyjhora_yoga_file: Path) -> set[str]:
    content = pyjhora_yoga_file.read_text(encoding="utf-8", errors="ignore")
    funcs = re.findall(r"^def ([a-zA-Z_][a-zA-Z0-9_]*)\(", content, re.MULTILINE)
    names: set[str] = set()
    for fn in funcs:
        if fn in SKIP_FUNCTIONS:
            continue
        if fn.startswith("_"):
            # PyJHora 的内部 calculation 函数大多也是 Yoga；保留 *_yoga*_calculation
            if "yoga" not in fn:
                continue
        if "_from_" in fn or "_get_" in fn or "_is_" in fn:
            continue
        base = fn
        base = re.sub(r"^_+", "", base)
        base = base.replace("_calculation", "").replace("_calc", "")
        base = re.sub(r"_\d+$", "", base)
        if base.endswith("_yoga"):
            base = base[:-5]
        key = normalize_name(base)
        if key and key not in SKIP_FUNCTIONS:
            names.add(key)
    return names


def find_pyjhora_yoga_file(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() else None

    candidates: list[Path] = []
    for root in sys.path:
        if not root:
            continue
        p = Path(root) / "jhora" / "horoscope" / "chart" / "yoga.py"
        if p.exists():
            candidates.append(p)

    # 常见 WorkBuddy isolated venv 位置
    home = Path.home()
    candidates.extend(home.glob(".workbuddy/binaries/python/envs/*/lib/python*/site-packages/jhora/horoscope/chart/yoga.py"))

    return candidates[0] if candidates else None


def covered(py_key: str, skill_keys: set[str]) -> bool:
    if py_key in skill_keys:
        return True
    compact_py = py_key.replace("_", "")
    compact_skill = {k.replace("_", "") for k in skill_keys}
    if compact_py in compact_skill:
        return True
    for alias in ALIASES.get(py_key, set()):
        if alias in skill_keys or alias.replace("_", "") in compact_skill:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Yoga coverage against PyJHora yoga.py")
    parser.add_argument("--pyjhora-yoga-file", help="Path to PyJHora jhora/horoscope/chart/yoga.py")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--show-missing", type=int, default=60, help="How many missing items to display")
    args = parser.parse_args()

    data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    all_rules = data.get("rules", [])
    rules = [r for r in all_rules if r.get("enabled", True)]
    ids = [r.get("id") for r in all_rules]
    dup_ids = sorted([i for i, c in Counter(ids).items() if c > 1])
    categories = Counter(r.get("category", "unknown") for r in rules)
    strength_values = Counter(r.get("strength", "?") for r in rules)

    skill_keys, skill_reverse = extract_skill_names(rules)

    pyjhora_file = find_pyjhora_yoga_file(args.pyjhora_yoga_file)
    py_names: set[str] = set()
    missing: list[str] = []
    coverage_pct = None
    if pyjhora_file:
        py_names = extract_pyjhora_names(pyjhora_file)
        missing = sorted([name for name in py_names if not covered(name, skill_keys)])
        coverage_pct = round((len(py_names) - len(missing)) / len(py_names) * 100, 2) if py_names else None

    result = {
        "rules_file": str(RULES_FILE),
        "total_rules": len(all_rules),
        "enabled_rules": len(rules),
        "disabled_rules": len(all_rules) - len(rules),
        "declared_total_rules": data.get("total_rules"),
        "declared_total_enabled_rules": data.get("total_enabled_rules"),
        "schema_version": data.get("schema_version"),
        "duplicate_ids": dup_ids,
        "categories": dict(categories.most_common()),
        "strength_values": dict(strength_values),
        "skill_normalized_name_keys": len(skill_keys),
        "pyjhora_yoga_file": str(pyjhora_file) if pyjhora_file else None,
        "pyjhora_unique_yoga_names": len(py_names) if pyjhora_file else None,
        "matched_unique_yoga_names": (len(py_names) - len(missing)) if pyjhora_file else None,
        "coverage_pct": coverage_pct,
        "missing_count": len(missing) if pyjhora_file else None,
        "missing": missing,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("🧘 Yoga Coverage Benchmark")
    print("=" * 60)
    print(f"规则文件: {RULES_FILE}")
    print(f"Schema: {data.get('schema_version')}")
    print(f"规则总数: {len(all_rules)} (enabled={len(rules)}, disabled={len(all_rules) - len(rules)}, declared={data.get('total_rules')})")
    print(f"重复 ID: {len(dup_ids)}" + (f" → {dup_ids}" if dup_ids else " ✅"))
    print(f"Strength 值: {dict(strength_values)}")
    print("\n分类统计:")
    for cat, count in categories.most_common():
        print(f"  {cat:16s} {count:3d}")

    print("\nPyJHora 对比:")
    if not pyjhora_file:
        print("  未找到 PyJHora yoga.py；仅完成本地 JSON 统计。")
        print("  可用 --pyjhora-yoga-file 指定路径。")
    else:
        print(f"  yoga.py: {pyjhora_file}")
        print(f"  PyJHora 唯一 Yoga 名称: {len(py_names)}")
        print(f"  已匹配: {len(py_names) - len(missing)}")
        print(f"  疑似缺失: {len(missing)}")
        print(f"  名称覆盖率: {coverage_pct}%")
        if missing:
            print(f"\n疑似缺失 Top {min(args.show_missing, len(missing))}:")
            for i, name in enumerate(missing[: args.show_missing], 1):
                print(f"  {i:3d}. {name}")
            if len(missing) > args.show_missing:
                print(f"  ... 还有 {len(missing) - args.show_missing} 条")

    print("\n说明: 此 benchmark 为名称覆盖率，不等同于逐条数学逻辑等价验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
