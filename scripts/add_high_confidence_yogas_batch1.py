#!/usr/bin/env python3
"""
高置信缺失 Yoga 第一批补齐。
原则：
- 只添加 PyJHora/B.V. Raman 中定义清晰、能用当前引擎稳定表达的 Yoga。
- 避免依赖未实现技法、模糊前提或过度推断。
- 对 Aakriti/Nabhasa 类使用可解释的 all_in_houses / occupied_houses_exact 等结构化条件。
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "references" / "yoga_rules.json"


def rule(rid, name, name_cn, category, logic, effects, strength="中", bvr_id=None, dedup_key=None):
    item = {
        "id": rid,
        "name": name,
        "name_cn": name_cn,
        "source": "B.V. Raman / PyJHora",
        "bvr_id": bvr_id,
        "category": category,
        "logic": logic,
        "effects": effects,
        "strength": strength,
        "enabled": True,
        "accuracy_note": "高置信：定义来自 PyJHora/B.V. Raman，且可由当前 Yoga 引擎结构化条件表达。",
    }
    if dedup_key:
        item["dedup_key"] = dedup_key
    return item

VISIBLE = "visible"

BATCH = [
    # ── Sun/Moon classic BVR yogas: 修正/补齐精确定义 ──
    rule(
        "bvr_016_vesi_precise", "Vesi Yoga", "日后行星 Yoga（精确）", "surya",
        {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 2,
         "combo_template": "太阳的第2宫有除月亮外行星：{planets}"},
        ["太阳后方有行星支持", "表达力与行动力增强", "自我驱动力较强"], "中", "BVR-16", "vesi_precise"
    ),
    rule(
        "bvr_017_vosi_precise", "Vosi Yoga", "日前行星 Yoga（精确）", "surya",
        {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 12,
         "combo_template": "太阳的第12宫有除月亮外行星：{planets}"},
        ["太阳前方有行星铺垫", "内在准备力强", "重视计划与隐性资源"], "中", "BVR-17", "vosi_precise"
    ),
    rule(
        "bvr_018_ubhayachara_precise", "Ubhayachara Yoga", "太阳双伴 Yoga（精确）", "surya",
        {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 2},
            {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 12},
        ]},
        ["太阳前后均有行星支撑", "自我表达较完整", "行动前后资源较足"], "强", "BVR-18", "ubhayachara_precise"
    ),
    rule(
        "bvr_002_sunapha_precise", "Sunaphaa Yoga", "月后行星 Yoga（精确）", "chandra",
        {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 2,
         "combo_template": "月亮的第2宫有除太阳外行星：{planets}"},
        ["自力更生", "资源积累能力", "心智有后续支撑"], "中", "BVR-2", "sunapha_precise"
    ),
    rule(
        "bvr_003_anapha_precise", "Anaphaa Yoga", "月前行星 Yoga（精确）", "chandra",
        {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 12,
         "combo_template": "月亮的第12宫有除太阳外行星：{planets}"},
        ["心智有背景支持", "贵人或隐性资源", "独处中成长"], "中", "BVR-3", "anapha_precise"
    ),
    rule(
        "bvr_004_duradhara_precise", "Duradhara Yoga", "月亮双伴 Yoga（精确）", "chandra",
        {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 2},
            {"type": "has_planet_in_house", "planets": {"role": "set", "planets": ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}, "house": 12},
        ]},
        ["月亮前后均有支撑", "心智稳定性增强", "资源与适应力较强"], "强", "BVR-4", "duradhara_precise"
    ),

    # ── Dala Yogas ──
    rule(
        "bvr_101_maalaa", "Maalaa Yoga", "花环 Yoga", "nabhasa",
        {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": "benefics", "house": 1},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 4},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 7},
        ]},
        ["吉星占据三个角宫", "名誉与舒适度提高", "人缘与社会支持强"], "强", "BVR-101", "maalaa"
    ),
    rule(
        "bvr_101_srik", "Srik Yoga", "吉祥花环 Yoga", "nabhasa",
        {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": "benefics", "house": 1},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 4},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 7},
        ]},
        ["同 Maalaa Yoga：吉星角宫支撑", "生活质量与声誉提升"], "强", "BVR-101", "maalaa"
    ),
    rule(
        "bvr_102_sarpa", "Sarpa Yoga", "蛇 Yoga", "nabhasa",
        {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": "malefics", "house": 1},
            {"type": "has_planet_in_house", "planets": "malefics", "house": 4},
            {"type": "has_planet_in_house", "planets": "malefics", "house": 7},
        ]},
        ["凶星占据三个角宫", "压力与竞争显著", "人生推进常伴随阻力"], "弱", "BVR-102", "sarpa_dala"
    ),

    # ── Aakriti/Nabhasa：所有可见行星占据特定宫位集合 ──
    rule("bvr_081_gadaa", "Gadaa Yoga", "锤杵 Yoga", "nabhasa",
         {"type": "occupied_houses_exact_sets", "planets": VISIBLE, "house_sets": [[1, 4], [4, 7], [7, 10], [1, 10]],
          "combo_template": "七曜只占据相邻角宫组合：{houses}"},
         ["行星集中于两个相邻角宫", "人生方向集中", "行动与稳定主题强"], "中", "BVR-81"),
    rule("bvr_082_sakata_aakriti", "Sakata Yoga", "车轮 Yoga（形态）", "nabhasa",
         {"type": "occupied_houses_exact", "planets": VISIBLE, "houses": [1, 7], "combo_template": "七曜只占据1/7宫轴线"},
         ["行星集中在1/7轴线", "自我与关系主题强烈", "人生起伏感较明显"], "中", "BVR-82", "sakata_aakriti"),
    rule("bvr_083_vihanga", "Vihanga Yoga", "飞鸟 Yoga（形态）", "nabhasa",
         {"type": "occupied_houses_exact", "planets": VISIBLE, "houses": [4, 10], "combo_template": "七曜只占据4/10宫轴线"},
         ["家庭与事业轴线突出", "迁移/职业方向强", "生活重心两极化"], "中", "BVR-83", "vihanga"),
    rule("bvr_084_vajra", "Vajra Yoga", "金刚 Yoga（精确）", "nabhasa",
         {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": "benefics", "house": 1},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 7},
            {"type": "has_planet_in_house", "planets": "malefics", "house": 4},
            {"type": "has_planet_in_house", "planets": "malefics", "house": 10},
         ]},
         ["1/7有吉星、4/10有凶星", "外在人际较顺、内外责任压力强", "刚柔并存"], "中", "BVR-84", "vajra_precise"),
    rule("bvr_085_yava", "Yava Yoga", "大麦 Yoga（精确）", "nabhasa",
         {"type": "and", "conditions": [
            {"type": "has_planet_in_house", "planets": "malefics", "house": 1},
            {"type": "has_planet_in_house", "planets": "malefics", "house": 7},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 4},
            {"type": "has_planet_in_house", "planets": "benefics", "house": 10},
         ]},
         ["1/7有凶星、4/10有吉星", "竞争中获得支撑", "内在资源与事业支持较好"], "中", "BVR-85", "yava_precise"),
    rule("bvr_086_sringaataka", "Sringaataka Yoga", "三角峰 Yoga", "nabhasa",
         {"type": "occupied_houses_exact", "planets": VISIBLE, "houses": [1, 5, 9], "combo_template": "七曜只占据1/5/9三方宫"},
         ["行星集中三方宫", "才华、信念与命运主题强", "创造力与精神性较强"], "强", "BVR-86"),
    rule("bvr_087_hala", "Hala Yoga", "犁 Yoga", "nabhasa",
         {"type": "occupied_houses_exact_sets", "planets": VISIBLE, "house_sets": [[2, 6, 10], [3, 7, 11], [4, 8, 12]],
          "combo_template": "七曜只占据互为三方但非1/5/9的组合：{houses}"},
         ["行星集中于互为三方的实务轴", "劳动、组织与现实推进主题强"], "中", "BVR-87"),
    rule("bvr_088_kamala", "Kamala Yoga", "莲花 Yoga", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [1, 4, 7, 10], "combo_template": "七曜全部落入角宫"},
         ["七曜均在角宫", "人生显化力强", "外在事件密集且影响明显"], "强", "BVR-88"),
    rule("bvr_089_vaapi", "Vaapi Yoga", "水池 Yoga", "nabhasa",
         {"type": "all_in_house_sets", "planets": VISIBLE, "house_sets": [[2, 5, 8, 11], [3, 6, 9, 12]],
          "combo_template": "七曜全部落入Panapara或Apoklima宫：{houses}"},
         ["行星集中于续宫或果宫", "资源积累/适应环境主题强", "人生节奏较非线性"], "中", "BVR-89"),

    # ── Sankhya / sequence groups ──
    rule("bvr_071_yoopa_precise", "Yoopa Yoga", "祭柱 Yoga（精确）", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [1, 2, 3, 4], "combo_template": "七曜全部落入1-4宫"},
         ["行星集中于生命早期与基础宫位", "重视家庭、学习与根基"], "中", "BVR-71", "yoopa_precise"),
    rule("bvr_072_sara", "Sara Yoga", "箭 Yoga", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [4, 5, 6, 7], "combo_template": "七曜全部落入4-7宫"},
         ["家庭、创造、工作与关系轴线突出", "人生重心偏向互动与服务"], "中", "BVR-72"),
    rule("bvr_072_ishu", "Ishu Yoga", "箭矢 Yoga", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [4, 5, 6, 7], "combo_template": "七曜全部落入4-7宫"},
         ["同 Sara Yoga：行动目标集中", "关系和现实事务牵引强"], "中", "BVR-72", "sara_ishu"),
    rule("bvr_073_sakti", "Sakti Yoga", "力量 Yoga", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [7, 8, 9, 10], "combo_template": "七曜全部落入7-10宫"},
         ["关系、转化、信念与事业宫位集中", "社会行动力强"], "中", "BVR-73"),
    rule("bvr_074_danda", "Danda Yoga", "杖 Yoga", "nabhasa",
         {"type": "all_in_houses", "planets": VISIBLE, "houses": [10, 11, 12, 1], "combo_template": "七曜全部落入10-12与1宫"},
         ["事业、社群、隐性消耗与自我主题集中", "责任感与压力并存"], "中", "BVR-74"),
    rule("bvr_075_naukaa_precise", "Naukaa Yoga", "船 Yoga（精确）", "nabhasa",
         {"type": "custom", "expr": "all(house_of(p) in [1,2,3,4,5,6,7] for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) and all(len([p for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'] if house_of(p)==h])>0 for h in [1,2,3,4,5,6,7])",
          "combo_template": "七曜分别占据从命宫起连续七宫"},
         ["七曜覆盖命宫起连续七宫", "人生像船行水面：移动、适应、串联能力强"], "中", "BVR-75", "naukaa_precise"),
    rule("bvr_076_koota_precise", "Koota Yoga", "堡垒 Yoga（精确）", "nabhasa",
         {"type": "custom", "expr": "all(house_of(p) in [4,5,6,7,8,9,10] for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) and all(len([p for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'] if house_of(p)==h])>0 for h in [4,5,6,7,8,9,10])",
          "combo_template": "七曜分别占据从4宫起连续七宫"},
         ["七曜覆盖4宫起连续七宫", "防御、结构、家族与社会位置主题强"], "中", "BVR-76", "koota_precise"),
    rule("bvr_077_chatra_precise", "Chatra Yoga", "伞盖 Yoga（精确）", "nabhasa",
         {"type": "custom", "expr": "all(house_of(p) in [7,8,9,10,11,12,1] for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) and all(len([p for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'] if house_of(p)==h])>0 for h in [7,8,9,10,11,12,1])",
          "combo_template": "七曜分别占据从7宫起连续七宫"},
         ["七曜覆盖7宫起连续七宫", "关系、公众、远方与事业主题强"], "中", "BVR-77", "chatra_precise"),
    rule("bvr_078_chaapa_precise", "Chaapa Yoga", "弓 Yoga（精确）", "nabhasa",
         {"type": "custom", "expr": "all(house_of(p) in [10,11,12,1,2,3,4] for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn']) and all(len([p for p in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'] if house_of(p)==h])>0 for h in [10,11,12,1,2,3,4])",
          "combo_template": "七曜分别占据从10宫起连续七宫"},
         ["七曜覆盖10宫起连续七宫", "事业拉弓、目标推进与公众行动力强"], "中", "BVR-78", "chaapa_precise"),

    # ── Dhana / Malika 类：宫主/宫位链条定义明确 ──
    rule("bvr_bhagya_malika", "Bhagya Malika Yoga", "幸运花环 Yoga", "dhana",
         {"type": "custom", "expr": "all(house_of(lord(h)) in [9,10,11] for h in [9,10,11] if lord(h) in planets_list())",
          "combo_template": "9/10/11宫主形成幸运与事业收益链"},
         ["幸运、事业与收益宫主形成连续支撑", "贵人、事业与收入联动"], "强", None),
    rule("bvr_dhana_malika", "Dhana Malika Yoga", "财富花环 Yoga", "dhana",
         {"type": "custom", "expr": "all(house_of(lord(h)) in [2,5,9,11] for h in [2,5,9,11] if lord(h) in planets_list())",
          "combo_template": "2/5/9/11宫主形成财富链"},
         ["财富宫、才华宫、幸运宫、收益宫主互相支撑", "财富积累力增强"], "强", None),
    rule("bvr_lagna_malika", "Lagna Malika Yoga", "命宫花环 Yoga", "raja",
         {"type": "custom", "expr": "all(house_of(lord(h)) in [1,2,3,4] for h in [1,2,3,4] if lord(h) in planets_list())",
          "combo_template": "1-4宫主形成命宫基础链"},
         ["自我、财富、努力、根基彼此支撑", "基础发展稳定"], "中", None),
    rule("bvr_karma_malika_precise", "Karma Malika Yoga", "事业花环 Yoga（精确）", "raja",
         {"type": "custom", "expr": "all(house_of(lord(h)) in [10,11,12,1] for h in [10,11,12,1] if lord(h) in planets_list())",
          "combo_template": "10/11/12/1宫主形成事业闭环"},
         ["事业、收益、远方/隐性成本与自我形成闭环", "职业使命感强"], "中", None, "karma_malika_precise"),
]


def main():
    data = json.loads(RULES.read_text(encoding="utf-8"))
    existing = {r["id"] for r in data["rules"]}
    existing_names = {(r.get("name"), r.get("dedup_key")) for r in data["rules"]}
    added = []
    skipped = []
    for item in BATCH:
        if item["id"] in existing:
            skipped.append(item["id"])
            continue
        data["rules"].append(item)
        existing.add(item["id"])
        added.append(item["id"])

    data["total_rules"] = len(data["rules"])
    RULES.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"added={len(added)} skipped={len(skipped)} total={len(data['rules'])}")
    print("added ids:")
    for rid in added:
        print("  ", rid)
    cats = Counter(r["category"] for r in data["rules"])
    print("categories top:")
    for k, v in cats.most_common(8):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
