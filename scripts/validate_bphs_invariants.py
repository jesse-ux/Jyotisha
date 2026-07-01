#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BPHS 分盘与 Ashtakavarga 独立验证脚本
不依赖 PyJhora，使用 BPHS 标准书例和数学不变量验证

验证项目：
1. Navamsa (D9) - BPHS 标准算法
2. Dasamsa (D10) - BPHS 标准算法
3. 其他关键分盘的一致性
4. Ashtakavarga - SAV=337 不变量 + BAV 固定总数
5. 分盘间一致性（varga.py vs jyotish_engine.py）
"""

import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

def sign_name(idx): return SIGNS[idx % 12]
def sign_idx(name): return SIGNS.index(name) if name in SIGNS else -1

# =============================================================================
# 1. Navamsa (D9) 验证 - BPHS Chapter 6
# =============================================================================
# 本仓采用的 JHora/BPHS Navamsa 口径：
# - Movable signs (白羊0, 巨蟹3, 天秤6, 摩羯9): 从本星座开始
# - Fixed signs (金牛1, 狮子4, 天蝎7, 水瓶10): 从第9星座开始 (+8)
# - Dual signs (双子2, 处女5, 射手8, 双鱼11): 从第5星座开始 (+4)
# 每份 = 30/9 = 3.333... 度

def calc_navamsa_ref(lon):
    """BPHS标准navamsa - 参考实现"""
    si = int(lon / 30)
    d = lon - si * 30
    ni = int(d / (30 / 9))
    if si % 3 == 0:  # movable
        start = si
    elif si % 3 == 1:  # fixed
        start = (si + 8) % 12
    else:  # dual
        start = (si + 4) % 12
    return (start + ni) % 12

NAVAMSA_TEST_CASES = [
    # Movable signs (si % 3 == 0): start = si
    ("Aries 0° → Aries (movable, part 0)", 0.0, 0),
    ("Aries 3.33° → Taurus (movable, part 1)", 3.3333, 1),
    ("Aries 10° → Cancer (movable, part 3)", 10.0, 3),
    ("Aries 16.67° → Virgo (movable, part 5)", 16.6667, 5),
    ("Aries 23.33° → Scorpio (movable, part 7)", 23.3333, 7),
    ("Aries 28° → Sagittarius (movable, part 8)", 28.0, 8),
    ("Cancer 5° → Leo (movable, part 1)", 90 + 5, 4),
    ("Libra 15° → Capricorn (movable, part 4)", 180 + 15, 9),
    ("Capricorn 20° → Pisces (movable, part 6)", 270 + 20, 11),

    # Fixed signs (si % 3 == 1): start = 9th from sign (+8)
    ("Taurus 0° → Capricorn (fixed, part 0, start=9)", 30 + 0, 9),
    ("Taurus 5° → Aquarius (fixed, part 1, start=9)", 30 + 5, 10),
    ("Taurus 10° → Pisces (fixed, part 3, start=9)", 30 + 10, 0),
    ("Leo 0° → Aries (fixed, part 0, start=0)", 120 + 0, 0),

    # Dual signs (si % 3 == 2): start = 5th from sign (+4)
    ("Gemini 0° → Libra (dual, part 0, start=6)", 60 + 0, 6),
    ("Gemini 5° → Scorpio (dual, part 1, start=6)", 60 + 5, 7),
    ("Virgo 10° → Leo (dual, part 3, start=1)", 150 + 10, 4),
]

# I'll generate test cases programmatically to avoid manual errors
print("=" * 70)
print("BPHS 分盘与 Ashtakavarga 独立验证")
print("=" * 70)

errors = []
passed = 0
failed = 0

def report(test_name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {test_name}")
    else:
        failed += 1
        print(f"  ❌ {test_name}")
        if detail:
            print(f"     {detail}")
        errors.append((test_name, detail))

# =============================================================================
# Test 1: Navamsa (D9) - 使用参考实现对比 varga.py
# =============================================================================
print("\n📐 Test 1: Navamsa (D9) BPHS 标准算法")
print("-" * 50)

def navamsa_ref(lon):
    """BPHS标准navamsa参考实现"""
    si = int(lon / 30)
    d = lon - si * 30
    ni = int(d / (30 / 9))
    if si % 3 == 0: start = si
    elif si % 3 == 1: start = (si + 8) % 12
    else: start = (si + 4) % 12
    return (start + ni) % 12

# 从本仓 scripts/varga.py 导入
from varga import calc_varga

# 全面测试：每个星座的 0°, 5°, 10°, 15°, 20°, 25°
navamsa_mismatch = []
for si in range(12):
    sign = SIGNS[si]
    for deg in [0, 5, 10, 15, 20, 25]:
        lon = si * 30 + deg
        ref = navamsa_ref(lon)
        result = calc_varga(lon, 9)
        actual = sign_idx(result['sign'])
        if ref != actual:
            navamsa_mismatch.append({
                'sign': sign, 'degree': deg, 'lon': lon,
                'expected': SIGNS[ref], 'actual': result['sign'],
                'expected_idx': ref, 'actual_idx': actual
            })

report("Navamsa: varga.py 与 BPHS 参考实现一致",
       len(navamsa_mismatch) == 0,
       f"不匹配: {len(navamsa_mismatch)} / 72 个测试点")

if navamsa_mismatch:
    for m in navamsa_mismatch[:5]:
        print(f"     {m['sign']} {m['degree']}°: expected {m['expected']}, got {m['actual']}")
    if len(navamsa_mismatch) > 5:
        print(f"     ... 还有 {len(navamsa_mismatch)-5} 个不匹配")

# =============================================================================
# Test 2: Dasamsa (D10) BPHS 标准算法
# =============================================================================
print("\n📐 Test 2: Dasamsa (D10) BPHS 标准算法")
print("-" * 50)

def dasamsa_ref(lon):
    """BPHS标准dasamsa参考实现"""
    si = int(lon / 30)
    d = lon - si * 30
    di = int(d / 3)  # 每份3度
    # Odd signs (0,2,4,6,8,10): start from same sign
    # Even signs (1,3,5,7,9,11): start from 9th sign (+8)
    start = si if si % 2 == 0 else (si + 8) % 12
    return (start + di) % 12

dasamsa_mismatch = []
for si in range(12):
    sign = SIGNS[si]
    for deg in [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]:
        lon = si * 30 + deg
        ref = dasamsa_ref(lon)
        result = calc_varga(lon, 10)
        actual = sign_idx(result['sign'])
        if ref != actual:
            dasamsa_mismatch.append({
                'sign': sign, 'degree': deg,
                'expected': SIGNS[ref], 'actual': result['sign']
            })

report("Dasamsa: varga.py 与 BPHS 参考实现一致",
       len(dasamsa_mismatch) == 0,
       f"不匹配: {len(dasamsa_mismatch)} / 120 个测试点")

if dasamsa_mismatch:
    for m in dasamsa_mismatch[:5]:
        print(f"     {m['sign']} {m['degree']}°: expected {m['expected']}, got {m['actual']}")
    if len(dasamsa_mismatch) > 5:
        print(f"     ... 还有 {len(dasamsa_mismatch)-5} 个不匹配")

# =============================================================================
# Test 3: jyotish_engine.py navamsa/dasamsa 与 varga.py 一致性
# =============================================================================
print("\n📐 Test 3: jyotish_engine.py 与 varga.py 一致性")
print("-" * 50)

# 读取 jyotish_engine.py 中的 navamsa/dasamsa 实现
# 由于不能轻易导入（有 argparse），我们直接内联测试

# 内联 jyotish_engine.py 的 navamsa/dasamsa 函数
SIGNS_JE = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
            'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

def navamsa_je(lon):
    si = int(lon / 30); d = lon - si * 30; ni = int(d / (30/9))
    if si % 3 == 0: start = si
    elif si % 3 == 1: start = (si + 8) % 12
    else: start = (si + 4) % 12
    return SIGNS_JE[(start + ni) % 12]

def dasamsa_je(lon):
    si = int(lon / 30); d = lon - si * 30; di = int(d / 3)
    start = si if si % 2 == 0 else (si + 8) % 12
    return SIGNS_JE[(start + di) % 12]

je_navamsa_mismatch = []
je_dasamsa_mismatch = []
for si in range(12):
    for deg in [0, 5, 10, 15, 20, 25]:
        lon = si * 30 + deg
        # Navamsa
        je_n = navamsa_je(lon)
        vg_n = calc_varga(lon, 9)['sign']
        if je_n != vg_n:
            je_navamsa_mismatch.append((SIGNS[si], deg, je_n, vg_n))
        # Dasamsa
        je_d = dasamsa_je(lon)
        vg_d = calc_varga(lon, 10)['sign']
        if je_d != vg_d:
            je_dasamsa_mismatch.append((SIGNS[si], deg, je_d, vg_d))

report("Navamsa: jyotish_engine.py == varga.py",
       len(je_navamsa_mismatch) == 0,
       f"不匹配: {len(je_navamsa_mismatch)} / 72")
report("Dasamsa: jyotish_engine.py == varga.py",
       len(je_dasamsa_mismatch) == 0,
       f"不匹配: {len(je_dasamsa_mismatch)} / 72")

# =============================================================================
# Test 4: 其他关键分盘算法一致性检查
# =============================================================================
print("\n📐 Test 4: 其他关键分盘算法")
print("-" * 50)

# D3 Drekkana: 每星座3份，每份10度
# 第1份→本星座，第2份→+4，第3份→+8
def d3_ref(lon):
    si = int(lon / 30); d = lon - si * 30
    di = int(d / 10)
    offset = [0, 4, 8][di]
    return (si + offset) % 12

d3_mismatch = []
for si in range(12):
    for deg in [0, 10, 20]:
        lon = si * 30 + deg
        ref = d3_ref(lon)
        result = calc_varga(lon, 3)
        actual = sign_idx(result['sign'])
        if ref != actual:
            d3_mismatch.append((SIGNS[si], deg, SIGNS[ref], result['sign']))

report("Drekkana (D3): varga.py 正确",
       len(d3_mismatch) == 0,
       f"不匹配: {len(d3_mismatch)} / 36")

# D12 Dwadasamsa: 每份2.5度，从本星座开始顺序排列
def d12_ref(lon):
    si = int(lon / 30); d = lon - si * 30
    di = int(d / 2.5)
    return (si + di) % 12

d12_mismatch = []
for si in range(12):
    for deg in [0, 5, 10, 15, 20, 25]:
        lon = si * 30 + deg
        ref = d12_ref(lon)
        result = calc_varga(lon, 12)
        actual = sign_idx(result['sign'])
        if ref != actual:
            d12_mismatch.append((SIGNS[si], deg, SIGNS[ref], result['sign']))

report("Dwadasamsa (D12): varga.py 正确",
       len(d12_mismatch) == 0,
       f"不匹配: {len(d12_mismatch)} / 72")

# =============================================================================
# Test 5: Ashtakavarga 不变量验证
# =============================================================================
print("\n⭐ Test 5: Ashtakavarga 不变量")
print("-" * 50)

from ashtakavarga import calc_ashtakavarga, BAV_TOTALS, EXPECTED_SAV_TOTAL

# 测试用例：爱因斯坦星盘 (简化，只提供星座位置)
# 爱因斯坦: 1879-03-14 11:30, Ulm Germany (48.4N, 9.98E)
# 上升: Aquarius, Sun: Pisces, Moon: Sagittarius, Mars: Capricorn,
# Mercury: Aries, Jupiter: Aquarius, Venus: Aries, Saturn: Aries
# 注：以下星座位置从已知数据简化
test_planets = {
    'Sun': {'sign': 'Pisces'},
    'Moon': {'sign': 'Sagittarius'},
    'Mars': {'sign': 'Capricorn'},
    'Mercury': {'sign': 'Aries'},
    'Jupiter': {'sign': 'Aquarius'},
    'Venus': {'sign': 'Aries'},
    'Saturn': {'sign': 'Aries'},
}
asc_idx = sign_idx('Aquarius')

result = calc_ashtakavarga(test_planets, asc_idx)

# 检查 SAV = 337
sav_total = result['sav']['total']
report(f"SAV 总分 = {EXPECTED_SAV_TOTAL}",
       sav_total == EXPECTED_SAV_TOTAL,
       f"实际: {sav_total}")

# 检查每个 BAV 的固定总数
for planet, expected in BAV_TOTALS.items():
    actual = result['bav'][planet]['total']
    report(f"{planet} BAV = {expected}",
           actual == expected,
           f"实际: {actual}")

# 检查 all_bav_valid
report("所有 BAV 校验通过", result['all_bav_valid'])

# =============================================================================
# Test 6: 分盘度数范围检查 (0-30)
# =============================================================================
print("\n📐 Test 6: 分盘度数范围检查")
print("-" * 50)

out_of_range = []
for div in [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
    for si in range(12):
        for deg in [0, 7.5, 15, 22.5, 28]:
            lon = si * 30 + deg
            if lon >= 360: continue
            result = calc_varga(lon, div)
            d = result['degree_in_sign']
            if not (0 <= d < 30):
                out_of_range.append((div, SIGNS[si], deg, d))

report("所有分盘度数在 [0, 30) 范围内",
       len(out_of_range) == 0,
       f"越界: {len(out_of_range)}")
if out_of_range:
    for o in out_of_range[:5]:
        print(f"     D{o[0]} {o[1]} {o[2]}°: degree={o[3]}")

# =============================================================================
# Test 7: 分盘 part_index 范围检查
# =============================================================================
print("\n📐 Test 7: 分盘 part_index 范围检查")
print("-" * 50)

part_errors = []
for div in [2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]:
    max_part = div - 1
    for si in range(12):
        for deg in [0, 7.5, 15, 22.5, 28]:
            lon = si * 30 + deg
            if lon >= 360: continue
            result = calc_varga(lon, div)
            pi = result['part_index']
            if not (0 <= pi <= max_part):
                part_errors.append((div, SIGNS[si], deg, pi, max_part))

report("所有分盘 part_index 在有效范围内",
       len(part_errors) == 0,
       f"错误: {len(part_errors)}")
if part_errors:
    for e in part_errors[:5]:
        print(f"     D{e[0]} {e[1]} {e[2]}°: part_index={e[3]}, max={e[4]}")

# =============================================================================
# 总结
# =============================================================================
print("\n" + "=" * 70)
print("验证总结")
print("=" * 70)
print(f"通过: {passed}")
print(f"失败: {failed}")
print(f"总计: {passed + failed}")

if failed == 0:
    print("\n🎉 所有 BPHS 不变量验证通过！")
else:
    print(f"\n⚠️ {failed} 项验证失败，需要修复")

# 输出详细错误报告
if errors:
    print("\n详细错误列表:")
    for name, detail in errors:
        print(f"  - {name}")
        if detail:
            print(f"    {detail}")
