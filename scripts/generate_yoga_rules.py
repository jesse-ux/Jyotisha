#!/usr/bin/env python3
"""
生成 yoga_rules.json 的辅助脚本。
将现有 cmd_yoga() 中的 ~76 条规则转换为数据驱动 JSON。
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(SKILL_DIR, "references", "yoga_rules.json")

rules = []

def add_rule(id_, name, name_cn, source, category, logic, effects, strength="中", bvr_id=None, dedup_key=None, enabled=True):
    r = {
        "id": id_,
        "name": name,
        "name_cn": name_cn,
        "source": source,
        "bvr_id": bvr_id,
        "category": category,
        "logic": logic,
        "effects": effects,
        "strength": strength,
        "enabled": enabled,
    }
    if dedup_key:
        r["dedup_key"] = dedup_key
    rules.append(r)


# ============================================================================
# 1. Raja Yoga 系列
# ============================================================================

# Raja Yoga: 角宫主 + 三方宫主 同宫
add_rule(
    "raja_yoga", "Raja Yoga", "王者格局", "BPHS", "raja",
    {
        "type": "any_pair",
        "from": {"role": "kendra_lords"},
        "to": {"role": "trikona_lords"},
        "exclude_self": True,
        "condition": {
            "type": "same_house",
            "a": "$a", "b": "$b",
            "combo_template": "{a}与{b}同在第{h}宫"
        }
    },
    ["权力地位", "事业成功", "社会影响力"], "中"
)

# Dharma Karmadhipati Yoga: 9宫主与10宫主同宫
add_rule(
    "dharma_karmadhipati", "Dharma Karmadhipati Yoga", "法业主同宫格局", "BPHS", "raja",
    {
        "type": "same_house",
        "a": {"role": "lord", "house": 9},
        "b": {"role": "lord", "house": 10},
        "combo_template": "9宫主{a}与10宫主{b}同在第{h}宫"
    },
    ["事业与命运结合", "社会地位高", "精神事业"], "强"
)

# Dharma Karmadhipati (Parivartana): 9宫主与10宫主互换
add_rule(
    "dharma_karmadhipati_parivartana", "Dharma Karmadhipati Yoga (Parivartana)", "法业主互换格局", "BPHS", "raja",
    {
        "type": "parivartana",
        "lord_a": {"role": "lord", "house": 9},
        "lord_b": {"role": "lord", "house": 10},
        "combo_template": "9宫主{la}与10宫主{lb}互换星座"
    },
    ["事业与命运互换提升", "社会地位高", "贵人运强"], "强"
)

# Raja Yoga (Parivartana): 任意角宫主与三方宫主互换
add_rule(
    "raja_yoga_parivartana", "Raja Yoga (Parivartana)", "王者互换格局", "BPHS", "raja",
    {
        "type": "any_pair",
        "from": {"role": "kendra_lords"},
        "to": {"role": "trikona_lords"},
        "exclude_self": True,
        "condition": {
            "type": "parivartana",
            "lord_a": "$a",
            "lord_b": "$b",
            "combo_template": "{la}与{lb}互换星座"
        }
    },
    ["权力与财富互换提升", "社会地位显著", "事业成功"], "极强"
)

# ============================================================================
# 2. Pancha Mahapurusha Yoga (5大伟人)
# ============================================================================

for planet, yoga_name, cn_name in [
    ("Mars", "Ruchaka Yoga", "鲁查卡格局"),
    ("Mercury", "Bhadra Yoga", "巴德拉格局"),
    ("Jupiter", "Hamsa Yoga", "汉萨格局"),
    ("Venus", "Malavya Yoga", "马拉维亚格局"),
    ("Saturn", "Sasa Yoga", "萨萨格局"),
]:
    add_rule(
        f"mahapurusha_{planet.lower()}", yoga_name, f"{cn_name}", "BPHS", "mahapurusha",
        {
            "type": "and",
            "conditions": [
                {"type": "in_houses", "planet": planet, "houses": [1, 4, 7, 10]},
                {"type": "dignity", "planet": planet, "dignity": "exalted",
                 "combo_template": f"{planet}入旺在{{sign}}"}
            ]
        },
        ["卓越才能", "领域领军", "人格魅力"], "极强", bvr_id=None
    )
    # 入庙版本
    add_rule(
        f"mahapurusha_{planet.lower()}_own", yoga_name, f"{cn_name}(入庙)", "BPHS", "mahapurusha",
        {
            "type": "and",
            "conditions": [
                {"type": "in_houses", "planet": planet, "houses": [1, 4, 7, 10]},
                {"type": "dignity", "planet": planet, "dignity": "own",
                 "combo_template": f"{planet}入庙在{{sign}}"}
            ]
        },
        ["卓越才能", "领域领军", "人格魅力"], "强", dedup_key=yoga_name
    )

# Hamsa Yoga (Trikona) - 木星在三方宫入旺/入庙
add_rule(
    "hamsa_trikona", "Hamsa Yoga (Trikona)", "汉萨三方宫格局", "BPHS", "mahapurusha",
    {
        "type": "and",
        "conditions": [
            {"type": "in_houses", "planet": "Jupiter", "houses": [1, 5, 9]},
            {"type": "dignity", "planet": "Jupiter", "dignity": "strong",
             "combo_template": "木星有力在{sign}"}
        ]
    },
    ["智慧卓越", "精神导师", "品德高尚"], "强", dedup_key="Hamsa Yoga"
)

# Moolatrikona 版本
for planet, yoga_name, cn_name in [
    ("Mars", "Ruchaka (Moola) Yoga", "鲁查卡本宫格局"),
    ("Mercury", "Bhadra (Moola) Yoga", "巴德拉本宫格局"),
    ("Jupiter", "Hamsa (Moola) Yoga", "汉萨本宫格局"),
    ("Venus", "Malavya (Moola) Yoga", "马拉维亚本宫格局"),
    ("Saturn", "Sasa (Moola) Yoga", "萨萨本宫格局"),
]:
    add_rule(
        f"moolatrikona_{planet.lower()}", yoga_name, cn_name, "BPHS", "mahapurusha",
        {
            "type": "and",
            "conditions": [
                {"type": "in_houses", "planet": planet, "houses": [1, 4, 7, 10]},
                {"type": "dignity", "planet": planet, "dignity": "moolatrikona",
                 "combo_template": f"{planet}在本宫{{sign}}"}
            ]
        },
        ["卓越才能", "领域领军", "人格魅力"], "强"
    )

# ============================================================================
# 3. Gajakesari Yoga
# ============================================================================

add_rule(
    "gajakesari", "Gajakesari Yoga", "象狮格局", "BPHS", "chandra",
    {
        "type": "and",
        "conditions": [
            {"type": "in_houses", "planet": "Jupiter", "houses": [1, 4, 7, 10]},
            {"type": "in_houses", "planet": "Moon", "houses": [1, 4, 7, 10]}
        ]
    },
    ["智慧学识", "财富名声", "道德品质"], "中", bvr_id="BVR-1"
)

# Gajakesari from Moon
add_rule(
    "gajakesari_from_moon", "Gajakesari Yoga (from Moon)", "象狮格局（从月亮）", "BPHS", "chandra",
    {
        "type": "in_houses_from",
        "planet": "Jupiter",
        "from": "Moon",
        "relations": ["kendra"],
        "combo_template": "木星在第{h}宫（从月亮的Kendra）"
    },
    ["智慧学识", "财富名声", "道德品质"], "强", dedup_key="Gajakesari Yoga"
)

# ============================================================================
# 4. Neechabhanga Raja Yoga
# ============================================================================

add_rule(
    "neechabhanga_basic", "Neechabhanga Raja Yoga", "落陷取消格局", "BPHS", "raja",
    {
        "type": "custom",
        "expr": """
matched = []
for p, info in ctx.planets.items():
    if DEBILITATION.get(p) == info.get("sign"):
        dl = SIGN_LORDS.get(info.get("sign"))
        if dl and dl in ctx.planets and kendra(house_of(dl)):
            matched.append((p, dl))
matched
""",
        "combo_template": "落陷取消格局",
        "strength": "中强"
    },
    ["克服困难", "逆境崛起", "转化能力"], "中强"
)

# Neechabhanga (Kendra) - 落陷行星自身在角宫
add_rule(
    "neechabhanga_kendra", "Neechabhanga Raja Yoga (Kendra)", "落陷取消格局（角宫版）", "BPHS", "raja",
    {
        "type": "custom",
        "expr": """
matched = []
for p, info in ctx.planets.items():
    if DEBILITATION.get(p) == info.get("sign") and kendra(info.get("house")):
        matched.append(p)
matched
""",
        "combo_template": "落陷行星在角宫",
        "strength": "中强"
    },
    ["逆境中崛起", "转化困境为机遇"], "中强", dedup_key="Neechabhanga Raja Yoga"
)

# ============================================================================
# 5. Dhana Yoga 系列
# ============================================================================

add_rule(
    "dhana_yoga", "Dhana Yoga", "财富格局", "BPHS", "dhana",
    {
        "type": "custom",
        "expr": """
import math
ai = ctx.asc_idx
wl = set()
wh = [2, 5, 9, 11]
for h in wh:
    sign = SIGNS[(ai + h - 1) % 12]
    wl.add(SIGN_LORDS[sign])
wc = sum(1 for w in wl if w in ctx.planets and house_of(w) in wh)
wc >= 2
""",
        "combo_template": "财富宫主星落入财富宫",
        "strength": "中"
    },
    ["财富积累", "物质成功", "投资收益"], "中"
)

add_rule(
    "grahi_dhana", "Grahi Dhana Yoga", "星聚财富格局", "Phaladeepika", "dhana",
    {
        "type": "custom",
        "expr": """
ai = ctx.asc_idx
lords = {
    1: SIGN_LORDS[SIGNS[ai % 12]],
    2: SIGN_LORDS[SIGNS[(ai + 1) % 12]],
    11: SIGN_LORDS[SIGNS[(ai + 10) % 12]]
}
ok = False
for wh in [2, 11]:
    cnt = sum(1 for h, lp in lords.items() if lp in ctx.planets and house_of(lp) == wh)
    if cnt >= 2:
        ok = True
        break
ok
""",
        "combo_template": "财富宫主星聚宫",
        "strength": "强"
    },
    ["财运亨通", "投资有利", "收入丰厚"], "强"
)

add_rule(
    "lakshmi_yoga", "Lakshmi Yoga", "拉克什米格局", "BPHS", "dhana",
    {
        "type": "and",
        "conditions": [
            {"type": "in_houses", "planet": {"role": "lord", "house": 9}, "houses": [1]},
            {"type": "dignity", "planet": {"role": "lord", "house": 9}, "dignity": "strong",
             "combo_template": "9宫主入旺/入庙在1宫"}
        ]
    },
    ["财富充裕", "生活幸福", "品德高尚"], "强"
)

add_rule(
    "vasumati_yoga", "Vasumati Yoga", "大地格局", "BPHS", "dhana",
    {
        "type": "custom",
        "expr": """
upachaya_benefics = [p for p in BENEFICS if p in ctx.planets and upachaya(house_of(p))]
len(upachaya_benefics) >= 3
""",
        "combo_template": "吉星在成长宫",
        "strength": "中"
    },
    ["财富丰厚", "生活富足", "物质成功"], "中"
)

# ============================================================================
# 6. Solar Yogas (Veshi/Voshi/Ubhayachari)
# ============================================================================

add_rule(
    "voshi_yoga", "Voshi Yoga", "太阳前瑜伽", "BPHS", "surya",
    {
        "type": "custom",
        "expr": """
if 'Sun' not in ctx.planets:
    False
else:
    sun_h = house_of('Sun')
    h12 = ((sun_h - 1 + 11) % 12) + 1
    planets_in_h12 = [p for p, info in ctx.planets.items() if info.get('house') == h12]
    h2 = ((sun_h - 1 + 1) % 12) + 1
    planets_in_h2 = [p for p, info in ctx.planets.items() if info.get('house') == h2]
    planets_in_h12 and not planets_in_h2
""",
        "combo_template": "行星在太阳第12宫"
    },
    ["口才出众", "善于表达", "受人尊敬"], "中", bvr_id="BVR-16"
)

add_rule(
    "veshi_yoga", "Veshi Yoga", "太阳后瑜伽", "BPHS", "surya",
    {
        "type": "custom",
        "expr": """
if 'Sun' not in ctx.planets:
    False
else:
    sun_h = house_of('Sun')
    h12 = ((sun_h - 1 + 11) % 12) + 1
    planets_in_h12 = [p for p, info in ctx.planets.items() if info.get('house') == h12]
    h2 = ((sun_h - 1 + 1) % 12) + 1
    planets_in_h2 = [p for p, info in ctx.planets.items() if info.get('house') == h2]
    planets_in_h2 and not planets_in_h12
""",
        "combo_template": "行星在太阳第2宫"
    },
    ["财富充裕", "生活舒适", "性情愉快"], "中", bvr_id="BVR-17"
)

add_rule(
    "ubhayachari_yoga", "Ubhayachari Yoga", "太阳双夹瑜伽", "BPHS", "surya",
    {
        "type": "custom",
        "expr": """
if 'Sun' not in ctx.planets:
    False
else:
    sun_h = house_of('Sun')
    h12 = ((sun_h - 1 + 11) % 12) + 1
    planets_in_h12 = [p for p, info in ctx.planets.items() if info.get('house') == h12]
    h2 = ((sun_h - 1 + 1) % 12) + 1
    planets_in_h2 = [p for p, info in ctx.planets.items() if info.get('house') == h2]
    bool(planets_in_h2 and planets_in_h12)
""",
        "combo_template": "太阳两侧均有行星"
    },
    ["性格坚毅", "口才与财富兼备", "受人爱戴"], "强", bvr_id="BVR-18"
)

# ============================================================================
# 7. Lunar Yogas
# ============================================================================

add_rule(
    "anapha_yoga", "Anapha Yoga", "月后瑜伽", "BPHS", "chandra",
    {
        "type": "custom",
        "expr": """
if 'Moon' not in ctx.planets:
    False
else:
    moon_h = house_of('Moon')
    h12 = ((moon_h - 1 + 11) % 12) + 1
    p_in_h12 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h12]
    h2 = ((moon_h - 1 + 1) % 12) + 1
    p_in_h2 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h2]
    p_in_h12 and not p_in_h2
""",
        "combo_template": "行星在月亮第12宫"
    },
    ["体格健壮", "名声良好", "品德高尚"], "中", bvr_id="BVR-3"
)

add_rule(
    "sunapha_yoga", "Sunapha Yoga", "月前瑜伽", "BPHS", "chandra",
    {
        "type": "custom",
        "expr": """
if 'Moon' not in ctx.planets:
    False
else:
    moon_h = house_of('Moon')
    h12 = ((moon_h - 1 + 11) % 12) + 1
    p_in_h12 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h12]
    h2 = ((moon_h - 1 + 1) % 12) + 1
    p_in_h2 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h2]
    p_in_h2 and not p_in_h12
""",
        "combo_template": "行星在月亮第2宫"
    },
    ["自力更生", "财富充裕", "受人尊敬"], "中", bvr_id="BVR-2"
)

add_rule(
    "durudhura_yoga", "Durudhura Yoga", "月双夹瑜伽", "BPHS", "chandra",
    {
        "type": "custom",
        "expr": """
if 'Moon' not in ctx.planets:
    False
else:
    moon_h = house_of('Moon')
    h12 = ((moon_h - 1 + 11) % 12) + 1
    p_in_h12 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h12]
    h2 = ((moon_h - 1 + 1) % 12) + 1
    p_in_h2 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h2]
    bool(p_in_h2 and p_in_h12)
""",
        "combo_template": "月亮两侧均有行星"
    },
    ["享受丰富", "善于辞令", "性格坚定"], "强", bvr_id="BVR-4"
)

add_rule(
    "kemadruma_yoga", "Kemadruma Yoga", "空劫瑜伽", "BPHS", "chandra",
    {
        "type": "custom",
        "expr": """
if 'Moon' not in ctx.planets:
    False
else:
    moon_h = house_of('Moon')
    h12 = ((moon_h - 1 + 11) % 12) + 1
    p_in_h12 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h12]
    h2 = ((moon_h - 1 + 1) % 12) + 1
    p_in_h2 = [p for p, info in ctx.planets.items() if p != 'Moon' and info.get('house') == h2]
    not p_in_h2 and not p_in_h12
""",
        "combo_template": "月亮两侧均无行星"
    },
    ["人生艰辛", "需自力更生", "精神挑战"], "凶", bvr_id="BVR-5"
)

add_rule(
    "chandra_mangala_same", "Chandra-Mangala Yoga", "月火同宫格局", "BPHS", "chandra",
    {
        "type": "same_house",
        "a": "Mars", "b": "Moon",
        "combo_template": "火星与月亮同在第{h}宫"
    },
    ["财富积累", "行动力强", "情绪驱动成功"], "中", bvr_id="BVR-6"
)

add_rule(
    "chandra_mangala_212", "Chandra-Mangala Yoga", "月火2/12格局", "BPHS", "chandra",
    {
        "type": "in_houses_from",
        "planet": "Mars",
        "from": "Moon",
        "relations": ["2nd_12th"],
        "combo_template": "火星在第{h}宫（从月亮的2/12宫）"
    },
    ["财运亨通", "精力充沛", "商业头脑"], "中", dedup_key="Chandra-Mangala Yoga"
)

# ============================================================================
# 8. Vipreet Raja Yoga
# ============================================================================

for dh_h, sub_name, cn_sub in [(6, "Harsha", "喜悦逆行"), (8, "Sarala", "锐利逆行"), (12, "Vimala", "纯净逆行")]:
    add_rule(
        f"vipreet_{dh_h}", f"{sub_name} Vipreet Raja Yoga", f"{cn_sub}格局", "Phaladeepika", "raja",
        {
            "type": "custom",
            "expr": f"""
lord_dh = lord({dh_h})
if lord_dh in ctx.planets:
    lh = house_of(lord_dh)
    lh in [6, 8, 12] and lh != {dh_h}
else:
    False
""",
            "combo_template": f"第{dh_h}宫主星落入凶宫"
        },
        ["因祸得福", "逆境崛起", "困境中成长"], "中强"
    )

# Vipreet dusthana pairs
add_rule(
    "vipreet_pairs", "Vipreet Raja Yoga", "逆行王者格局", "BPHS", "raja",
    {
        "type": "custom",
        "expr": """
pairs = [(6,8), (6,12), (8,12)]
matched = []
for h1, h2 in pairs:
    l1 = lord(h1)
    l2 = lord(h2)
    if l1 in ctx.planets and l2 in ctx.planets:
        if house_of(l1) == h2 and house_of(l2) == h1:
            matched.append((h1, h2, l1, l2))
matched
""",
        "combo_template": "凶宫主星互落"
    },
    ["因祸得福", "逆境崛起"], "中强", dedup_key="Vipreet Raja Yoga"
)

# ============================================================================
# 9. 其他主要 Yoga
# ============================================================================

add_rule(
    "amala_yoga", "Amala Yoga", "无瑕格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
benefics_10_11 = [p for p in BENEFICS if p in ctx.planets and house_of(p) in [10, 11] and not debil(p)]
bool(benefics_10_11)
""",
        "combo_template": "吉星在10/11宫"
    },
    ["名声清白", "受人敬仰", "事业有成"], "中强", bvr_id="BVR-13"
)

add_rule(
    "parvata_yoga", "Parvata Yoga", "山岳格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
kl = list(dict.fromkeys([lord(h) for h in [1,4,7,10]]))
kt = [h for h in [1,5,9]]
kendra_lords_strong = sum(1 for k in kl if k in ctx.planets and (kendra(house_of(k)) or trikona(house_of(k))))
if kendra_lords_strong < 2:
    False
else:
    lord_6 = lord(6)
    lord_8 = lord(8)
    lord_6_ok = lord_6 in ctx.planets and house_of(lord_6) != 1
    lord_8_ok = lord_8 in ctx.planets and house_of(lord_8) != 1
    lord_6_ok or lord_8_ok
""",
        "combo_template": "角宫主星有力+凶宫主星不落入1宫"
    },
    ["智慧卓越", "富有口才", "品格高尚"], "中", bvr_id="BVR-14"
)

add_rule(
    "kahala_yoga", "Kahala Yoga", "勇气格局", "BPHS", "auspicious",
    {
        "type": "same_house",
        "a": {"role": "lord", "house": 3},
        "b": {"role": "lord", "house": 10},
        "combo_template": "3宫主{a}与10宫主{b}同在第{h}宫"
    },
    ["意志坚定", "领导才能", "充满活力"], "中", bvr_id="BVR-15"
)

add_rule(
    "sankha_yoga", "Sankha Yoga", "海螺格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
lord_5 = lord(5)
lord_6 = lord(6)
if lord_5 in ctx.planets and lord_6 in ctx.planets:
    l5h = house_of(lord_5)
    l6h = house_of(lord_6)
    (kendra(l5h) or trikona(l5h)) and (kendra(l6h) or trikona(l6h))
else:
    False
""",
        "combo_template": "5宫主与6宫主均在有力宫位"
    },
    ["学识渊博", "品德高尚", "物质充裕"], "中强", bvr_id="BVR-12"
)

add_rule(
    "bheri_yoga", "Bheri Yoga", "旗帜格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
lord_9 = lord(9)
if lord_9 not in ctx.planets or house_of(lord_9) != 2:
    False
else:
    jv_in_kendra = [p for p in ['Jupiter', 'Venus'] if p in ctx.planets and kendra(house_of(p))]
    bool(jv_in_kendra)
""",
        "combo_template": "9宫主在2宫+木星/金星在角宫"
    },
    ["品德高尚", "长寿幸福", "受人敬仰"], "中"
)

add_rule(
    "mridanga_yoga", "Mridanga Yoga", "鼓格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
if asc_lord not in ctx.planets:
    False
else:
    asc_strong = exalted(asc_lord) or own(asc_lord)
    other_strong = [p for p in ctx.planets if p != asc_lord and p not in ['Rahu', 'Ketu'] and (exalted(p) or own(p))]
    asc_strong and bool(other_strong)
""",
        "combo_template": "上升主星有力+其他行星有力"
    },
    ["权力权威", "个人魅力", "领导气质"], "强"
)

add_rule(
    "sreenatha_yoga", "Sreenatha Yoga", "幸运之主格局", "BPHS", "auspicious",
    {
        "type": "and",
        "conditions": [
            {"type": "in_houses", "planet": {"role": "lord", "house": 7}, "houses": [10]},
            {"type": "in_houses", "planet": {"role": "lord", "house": 10}, "houses": [1]}
        ]
    },
    ["事业辉煌", "婚姻美满", "贵人相助"], "强"
)

add_rule(
    "matsya_yoga", "Matsya Yoga", "鱼格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
ben_in_trikona = [p for p in BENEFICS if p in ctx.planets and house_of(p) in [5, 9]]
mal_in_dusthana = [p for p in MALEFICS if p in ctx.planets and house_of(p) in [6, 8]]
bool(ben_in_trikona and mal_in_dusthana)
""",
        "combo_template": "吉星在三方宫+凶星在凶宫"
    },
    ["聪慧过人", "直觉敏锐", "灵性成长"], "中"
)

add_rule(
    "koorma_yoga", "Koorma Yoga", "龟格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
ben_in_1 = [p for p in BENEFICS if p in ctx.planets and house_of(p) == 1]
lord_5 = lord(5)
lord_9 = lord(9)
lord_5_or_9_in_1 = False
for lp in [lord_5, lord_9]:
    if lp in ctx.planets and house_of(lp) == 1:
        lord_5_or_9_in_1 = True
bool(ben_in_1 and lord_5_or_9_in_1)
""",
        "combo_template": "吉星在1宫+5/9宫主在1宫"
    },
    ["智慧深厚", "耐心坚韧", "精神修养"], "中"
)

add_rule(
    "khadga_yoga", "Khadga Yoga", "剑格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
lord_2 = lord(2)
if lord_2 not in ctx.planets or house_of(lord_2) != 2:
    False
else:
    mal_in_2 = [p for p in MALEFICS if p in ctx.planets and house_of(p) == 2]
    not mal_in_2
""",
        "combo_template": "2宫主在2宫且无凶星"
    },
    ["财富充裕", "口才出众", "品格坚定"], "中"
)

add_rule(
    "kusuma_yoga", "Kusuma Yoga", "花格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
checks = [
    'Jupiter' in ctx.planets and house_of('Jupiter') == 10,
    'Moon' in ctx.planets and house_of('Moon') == 1,
    'Sun' in ctx.planets and house_of('Sun') == 2,
    'Venus' in ctx.planets and house_of('Venus') == 9,
]
sum(checks) >= 3
""",
        "combo_template": "木星10/月亮1/太阳2/金星9 中满足3+"
    },
    ["才貌双全", "受人爱戴", "幸福美满"], "中强"
)

# ============================================================================
# 10. Conjunction Yogas
# ============================================================================

add_rule(
    "guru_mangala_same", "Guru-Mangala Yoga", "木火同宫格局", "BPHS", "conjunction",
    {
        "type": "same_house",
        "a": "Jupiter", "b": "Mars",
        "combo_template": "木星与火星同在第{h}宫"
    },
    ["智慧与行动力兼备", "正义感强", "领导能力"], "中强"
)

add_rule(
    "guru_mangala_parivartana", "Guru-Mangala Yoga", "木火互容格局", "BPHS", "conjunction",
    {
        "type": "parivartana",
        "lord_a": "Jupiter",
        "lord_b": "Mars",
        "combo_template": "木星与火星互换星座"
    },
    ["智慧与行动力兼备", "正义感强", "领导能力"], "强", dedup_key="Guru-Mangala Yoga"
)

add_rule(
    "budhaditya_yoga", "Budhaditya Yoga", "水日同宫格局", "BPHS", "conjunction",
    {
        "type": "same_house",
        "a": "Mercury", "b": "Sun",
        "combo_template": "水星与太阳同在第{h}宫"
    },
    ["智力超群", "口才出众", "学识渊博"], "中强", bvr_id="BVR-26"
)

add_rule(
    "budha_shukra_yoga", "Budha-Shukra Yoga", "水金合相格局", "经典", "conjunction",
    {
        "type": "same_house",
        "a": "Mercury", "b": "Venus",
        "combo_template": "水星与金星同在第{h}宫"
    },
    ["艺术才华", "商业头脑", "审美卓越"], "强"
)

add_rule(
    "surya_chandra_yoga", "Surya-Chandra Yoga", "日月合相格局", "经典", "conjunction",
    {
        "type": "same_house",
        "a": "Sun", "b": "Moon",
        "combo_template": "太阳与月亮同在第{h}宫"
    },
    ["精神力量", "领导气质", "意志坚定"], "强"
)

add_rule(
    "guru_shukra_yoga", "Guru-Shukra Yoga", "木金合相格局", "BPHS", "conjunction",
    {
        "type": "same_house",
        "a": "Jupiter", "b": "Venus",
        "combo_template": "木星与金星同在第{h}宫"
    },
    ["智慧与爱心兼备", "精神富足", "艺术造诣"], "强"
)

add_rule(
    "shani_rahu_yoga", "Shani-Rahu Yoga", "土罗合相格局", "经典", "conjunction",
    {
        "type": "same_house",
        "a": "Saturn", "b": "Rahu",
        "combo_template": "土星与罗睺同在第{h}宫"
    },
    ["纪律与变革", "突破传统", "但也可能带来阻碍"], "中"
)

add_rule(
    "angaraka_yoga", "Angaraka Yoga", "火土合相格局", "BPHS", "conjunction",
    {
        "type": "same_house",
        "a": "Mars", "b": "Saturn",
        "combo_template": "火星与土星同在第{h}宫"
    },
    ["行动力与纪律", "也可能产生冲突", "需平衡"], "中"
)

add_rule(
    "surya_budha_yoga", "Surya-Budha Yoga", "日水紧密合相格局", "经典", "conjunction",
    {
        "type": "same_house",
        "a": "Sun", "b": "Mercury",
        "combo_template": "太阳与水星同在第{h}宫"
    },
    ["智力超群", "沟通能力强", "学习能力佳"], "强"
)

# ============================================================================
# 11. Kartari / 夹击 Yoga
# ============================================================================

add_rule(
    "papakartari_yoga", "Papakartari Yoga", "凶星夹击格局", "Brihat Jataka", "durbhaga",
    {
        "type": "custom",
        "expr": """
targets = [1, 4, 7, 10, 5, 9]
matched = False
for th in targets:
    prev_h = ((th - 2) % 12) + 1
    next_h = (th % 12) + 1
    mal_before = [p for p in MALEFICS if p in ctx.planets and house_of(p) == prev_h]
    mal_after = [p for p in MALEFICS if p in ctx.planets and house_of(p) == next_h]
    if mal_before and mal_after:
        matched = True
        break
matched
""",
        "combo_template": "某宫被凶星前后夹击"
    },
    ["领域受限", "需要额外努力", "阻碍与挑战"], "凶"
)

add_rule(
    "subhakartari_yoga", "Subhakartari Yoga", "吉星护宫格局", "Brihat Jataka", "auspicious",
    {
        "type": "custom",
        "expr": """
targets = [1, 4, 7, 10, 5, 9]
matched = False
for th in targets:
    prev_h = ((th - 2) % 12) + 1
    next_h = (th % 12) + 1
    ben_before = [p for p in BENEFICS if p in ctx.planets and house_of(p) == prev_h]
    ben_after = [p for p in BENEFICS if p in ctx.planets and house_of(p) == next_h]
    if ben_before and ben_after:
        matched = True
        break
matched
""",
        "combo_template": "某宫被吉星前后守护"
    },
    ["领域受保护", "顺利发展", "贵人助力"], "吉"
)

# ============================================================================
# 12. Saraswati / 辩才天女
# ============================================================================

add_rule(
    "saraswati_yoga", "Saraswati Yoga", "辩才天女格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
saraswati_houses = [2, 4, 7, 9, 10]
saraswati_planets = [p for p in ['Jupiter', 'Venus', 'Mercury'] if p in ctx.planets and house_of(p) in saraswati_houses]
if len(saraswati_planets) >= 3 or (len(saraswati_planets) >= 2 and 'Jupiter' in saraswati_planets):
    jup_dig = dignity('Jupiter') if 'Jupiter' in ctx.planets else ''
    jup_dig in ['EXALTED', 'OWN_SIGN', 'MOOLATRIKONA', 'FRIEND']
else:
    False
""",
        "combo_template": "木星/金星/水星在吉宫"
    },
    ["学问渊博", "艺术才华", "表达卓越"], "强"
)

# ============================================================================
# 13. Chamara / Akhanda / Gurumauli
# ============================================================================

add_rule(
    "chamara_yoga", "Chamara Yoga", "拂尘格局", "BPHS", "auspicious",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
if asc_lord not in ctx.planets:
    False
else:
    asc_strong = exalted(asc_lord) or own(asc_lord)
    ben_kt = [p for p in BENEFICS if p in ctx.planets and (kendra(house_of(p)) or trikona(house_of(p)))]
    asc_strong and len(ben_kt) >= 2
""",
        "combo_template": "上升主有力+吉星在角宫/三方宫"
    },
    ["长寿健康", "受人尊敬", "智慧通达"], "强"
)

add_rule(
    "akhanda_samrajya", "Akhanda Samrajya Yoga", "永恒帝王格局", "BPHS", "raja",
    {
        "type": "custom",
        "expr": """
if 'Jupiter' not in ctx.planets:
    False
else:
    jh = house_of('Jupiter')
    if jh not in [2, 5, 9, 11]:
        False
    else:
        lord_11 = lord(11)
        if lord_11 not in ctx.planets:
            False
        else:
            l11h = house_of(lord_11)
            l11h == 11 or kendra(l11h)
""",
        "combo_template": "木星在2/5/9/11宫+11宫主有力"
    },
    ["权力持久", "事业辉煌", "影响力广泛"], "强"
)

add_rule(
    "gurumauli_9", "Gurumauli Yoga", "至上师格局", "经典", "auspicious",
    {
        "type": "in_houses",
        "planet": "Jupiter",
        "houses": [9],
        "combo_template": "木星在9宫"
    },
    ["命运眷顾", "精神导师指引", "福德深厚"], "强"
)

add_rule(
    "gurumauli_with_lord9", "Gurumauli Yoga", "至上师关联格局", "经典", "auspicious",
    {
        "type": "same_house",
        "a": "Jupiter",
        "b": {"role": "lord", "house": 9},
        "combo_template": "木星与9宫主同在第{h}宫"
    },
    ["命运眷顾", "贵人运强", "智慧通达"], "中强", dedup_key="Gurumauli Yoga"
)

# ============================================================================
# 14. 凶 Yoga
# ============================================================================

add_rule(
    "shakata_yoga", "Shakata Yoga", "车格局", "BPHS", "durbhaga",
    {
        "type": "in_houses",
        "planet": "Jupiter",
        "houses": [6, 8, 12],
        "combo_template": "木星在{h}宫"
    },
    ["财富不稳", "健康需注意", "精神起伏"], "凶"
)

add_rule(
    "daridra_11", "Daridra Yoga", "贫困格局", "BPHS", "durbhaga",
    {
        "type": "custom",
        "expr": """
lord_11 = lord(11)
lord_11 in ctx.planets and house_of(lord_11) in [6, 8, 12]
""",
        "combo_template": "11宫主落入凶宫"
    },
    ["财务困难", "需努力积累", "谨慎理财"], "凶"
)

add_rule(
    "daridra_2", "Daridra Yoga (variant)", "贫困格局变体", "BPHS", "durbhaga",
    {
        "type": "custom",
        "expr": """
lord_2 = lord(2)
lord_2 in ctx.planets and debil(lord_2) and dusthana(house_of(lord_2))
""",
        "combo_template": "2宫主落陷在凶宫"
    },
    ["财务压力", "家庭纠纷", "需节俭持家"], "凶", dedup_key="Daridra Yoga"
)

# ============================================================================
# 15. Nabhasa Yogas (分布模式)
# ============================================================================

add_rule(
    "gola_yoga", "Gola Yoga", "球格局", "BPHS", "nabhasa",
    {
        "type": "houses_occupied",
        "planets": "all",
        "count": 1,
        "combo_template": "所有行星在同一宫"
    },
    ["专注集中", "也可能过于极端"], "中"
)

add_rule(
    "yuga_yoga", "Yuga Yoga", "双格局", "BPHS", "nabhasa",
    {
        "type": "houses_occupied",
        "planets": "all",
        "count": 2,
        "combo_template": "所有行星在两宫"
    },
    ["双重性格", "生活两极化"], "中"
)

add_rule(
    "sula_yoga", "Sula Yoga", "三叉格局", "BPHS", "nabhasa",
    {
        "type": "houses_occupied",
        "planets": "all",
        "count": 3,
        "combo_template": "所有行星在三宫"
    },
    ["行动力", "但也可能有冲突"], "中"
)

add_rule(
    "kedara_yoga", "Kedara Yoga", "四重格局", "BPHS", "nabhasa",
    {
        "type": "houses_occupied",
        "planets": "all",
        "count": 4,
        "combo_template": "所有行星在四宫"
    },
    ["稳定", "农业/地产运"], "中"
)

add_rule(
    "veena_yoga", "Veena Yoga", "琴格局", "BPHS", "nabhasa",
    {
        "type": "houses_occupied",
        "planets": "all",
        "count": 7,
        "combo_template": "行星分布在七宫"
    },
    ["艺术才华", "生活丰富", "多才多艺"], "强", bvr_id="BVR-91"
)

add_rule(
    "asraya_yoga", "Asraya Yoga", "依托格局", "BPHS", "nabhasa",
    {
        "type": "all_planets",
        "planets": "all",
        "condition": {
            "type": "custom",
            "expr": "kendra(house_of(bindings.get('planet', ''))) or trikona(house_of(bindings.get('planet', '')))"
        }
    },
    ["生活稳定", "有依靠", "根基深厚"], "中强"
)

add_rule(
    "dala_yoga", "Dala Yoga", "分叶格局", "BPHS", "nabhasa",
    {
        "type": "custom",
        "expr": """
dala_count = sum(1 for dh in [6, 8, 12] if lord(dh) in ctx.planets and kendra(house_of(lord(dh))))
dala_count >= 2
""",
        "combo_template": "凶宫主在角宫"
    },
    ["逆境中崛起", "转化能力"], "中强"
)

add_rule(
    "maala_yoga", "Maala Yoga", "串珠格局", "BPHS", "nabhasa",
    {
        "type": "custom",
        "expr": """
ben_in_kendra = sorted(set(house_of(p) for p in BENEFICS if p in ctx.planets and kendra(house_of(p))))
matched = False
if len(ben_in_kendra) >= 3:
    for i in range(len(ben_in_kendra) - 2):
        if ben_in_kendra[i+1] - ben_in_kendra[i] == 1 and ben_in_kendra[i+2] - ben_in_kendra[i+1] == 1:
            matched = True
            break
matched
""",
        "combo_template": "吉星在连续角宫"
    },
    ["幸运连绵", "福气不断"], "强"
)

# ============================================================================
# 16. 特殊条件 Yoga
# ============================================================================

add_rule(
    "mahabhagya_yoga", "Mahabhagya Yoga", "大运格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
odd_signs = ['Aries', 'Gemini', 'Leo', 'Libra', 'Sagittarius', 'Aquarius']
asc_odd = ctx.ascendant in odd_signs
sun_odd = 'Sun' in ctx.planets and sign_of('Sun') in odd_signs
moon_odd = 'Moon' in ctx.planets and sign_of('Moon') in odd_signs
asc_odd and sun_odd and moon_odd
""",
        "combo_template": "上升/太阳/月亮均在奇数星座"
    },
    ["命运眷顾", "人生顺遂", "贵人运强"], "强"
)

add_rule(
    "pushkala_yoga", "Pushkala Yoga", "丰盈格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
if asc_lord not in ctx.planets:
    False
else:
    asc_strong = exalted(asc_lord) or own(asc_lord)
    moon_ok = 'Moon' in ctx.planets and sign_of('Moon') != DEBILITATION.get('Moon')
    ben_in_asc = [p for p in BENEFICS if p in ctx.planets and house_of(p) == 1]
    asc_strong and moon_ok and bool(ben_in_asc)
""",
        "combo_template": "上升主有力+月亮良好+吉星在1宫"
    },
    ["生活富足", "社会地位高", "受人尊敬"], "强"
)

add_rule(
    "adhi_yoga", "Adhi Yoga", "上方格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
adhi = {6: 12, 8: 2, 12: 11}
matched = False
for dh, uh in adhi.items():
    ben_above = [p for p in BENEFICS if p in ctx.planets and house_of(p) == uh]
    if ben_above:
        matched = True
        break
matched
""",
        "combo_template": "吉星在凶宫上方"
    },
    ["权威地位", "领导能力", "受人尊敬"], "中强", bvr_id="BVR-7"
)

add_rule(
    "chatussagara_yoga", "Chatussagara Yoga", "四角充盈格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
all(len(planets_in(h)) > 0 for h in [1, 4, 7, 10])
""",
        "combo_template": "1/4/7/10宫均有行星"
    },
    ["生活圆满", "各方面均衡发展", "命运眷顾"], "强"
)

add_rule(
    "virinchi_yoga", "Virinchi Yoga", "创造格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
if asc_lord not in ctx.planets:
    False
else:
    asc_ok = kendra(house_of(asc_lord)) or trikona(house_of(asc_lord))
    lord_5 = lord(5)
    lord5_ok = lord_5 in ctx.planets and kendra(house_of(lord_5))
    jup_ok = 'Jupiter' in ctx.planets and (exalted('Jupiter') or own('Jupiter') or house_of('Jupiter') in [1,5,9])
    asc_ok and lord5_ok and jup_ok
""",
        "combo_template": "上升主有力+5宫主在角宫+木星有力"
    },
    ["创造力强", "智慧卓越", "精神修养"], "强"
)

add_rule(
    "veena_artistic", "Veenaa Yoga (Artistic)", "艺术琴格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
ben_in_259 = [p for p in BENEFICS if p in ctx.planets and house_of(p) in [2, 5, 9]]
asc_strong = asc_lord in ctx.planets and (exalted(asc_lord) or own(asc_lord))
len(ben_in_259) >= 2 and asc_strong
""",
        "combo_template": "吉星在2/5/9宫+上升主有力"
    },
    ["艺术才华", "音乐天赋", "审美卓越"], "强"
)

add_rule(
    "kalanidhi_yoga", "Kalanidhi Yoga", "艺藏格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
if 'Jupiter' not in ctx.planets or house_of('Jupiter') not in [2, 5]:
    False
else:
    jh = house_of('Jupiter')
    assoc = [p for p in ['Venus', 'Mercury'] if p in ctx.planets and (house_of(p) == jh or abs(house_of(p) - jh) in [3, 6, 9])]
    bool(assoc)
""",
        "combo_template": "木星在2/5宫+被金星/水星关联"
    },
    ["艺术才华", "学识渊博", "受人尊敬"], "强"
)

add_rule(
    "saubhagya_yoga", "Saubhagya Yoga", "幸运格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
asc_lord = SIGN_LORDS.get(ctx.ascendant)
asc_strong = asc_lord in ctx.planets and kendra(house_of(asc_lord)) and (exalted(asc_lord) or own(asc_lord))
moon_ok = 'Moon' in ctx.planets and house_of('Moon') in [1, 5, 9, 10, 11]
asc_strong and moon_ok
""",
        "combo_template": "上升主有力在角宫+月亮在吉宫"
    },
    ["幸运眷顾", "生活幸福", "婚姻美满"], "强"
)

add_rule(
    "shubha_yoga", "Shubha Yoga", "全吉星格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
benefics_present = [p for p in BENEFICS if p in ctx.planets]
all_benefics_kt = all(kendra(house_of(p)) or trikona(house_of(p)) for p in benefics_present)
all_benefics_kt and len(benefics_present) >= 3
""",
        "combo_template": "所有吉星在角宫或三方宫"
    },
    ["生活顺遂", "福气满满", "受人爱戴"], "强"
)

add_rule(
    "graha_yuddha", "Graha Yuddha", "行星战争", "经典", "special",
    {
        "type": "degree_gap",
        "a": "all",
        "b": "all",
        "max_gap": 1.0,
        "combo_template": "行星在同一星座内相距<1°"
    },
    ["行星力量竞争", "相关领域有张力"], "中"
)

add_rule(
    "pushya_yoga", "Pushya Yoga", "成长格局", "BPHS", "special",
    {
        "type": "custom",
        "expr": """
ben_in_8912 = [p for p in BENEFICS if p in ctx.planets and house_of(p) in [8, 9, 12]]
len(ben_in_8912) >= 2
""",
        "combo_template": "吉星在8/9/12宫"
    },
    ["精神成长", "灵性提升", "命运眷顾"], "中强"
)


# ============================================================================
# 输出 JSON
# ============================================================================
if __name__ == "__main__":
    data = {
        "schema_version": "1.0",
        "description": "Yoga 规则库 - 数据驱动架构 v1.0",
        "total_rules": len(rules),
        "rules": rules
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(rules)} rules -> {OUTPUT_PATH}")
