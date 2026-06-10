"""
JHora 基准校准测试套件 v1.0
对比当前引擎的 Shadbala 输出与 JHora/PyJHora 的已知参考值

测试数据集来源：
- BV Raman (作者本人) — PyJHora 标准测试用例
- PVR Rao — PyJHora PVR 教材测试用例
"""

import json
import sys
import os

# 确保可以导入 scripts 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from shadbala import calc_shadbala

# ============================================================================
# 标准测试数据集
# ============================================================================
# 来源：PyJHora test suite + PVR 教材
TEST_CASES = [
    {
        "name": "BV Raman (作者本人)",
        "data": {
            "year": 1918, "month": 10, "day": 16,
            "hour": 14, "minute": 22, "second": 16,
            "lat": 12.97, "lon": 77.58,  # 班加罗尔
            "tz": 5.5,
        },
        # 预期值来源：PyJHora Drik Bala for BV Raman (Raman Ayanamsa)
        "expected": {
            "drik_bala_sunny": 15.86,  # 示例值，需从 JHora 确认
        }
    },
    {
        "name": "PVR Rao (教材示例)",
        "data": {
            "year": 1981, "month": 9, "day": 13,
            "hour": 1, "minute": 30, "second": 0,
            "lat": 28.65, "lon": 77.22,  # 德里
            "tz": 5.5,
        },
        "expected": {}
    },
    {
        "name": "一楠 (本地测试)",
        "data": {
            "year": REDACTED_YEAR, "month": 4, "day": 17,
            "hour": 14, "minute": 45, "second": 20,
            "lat": 36.42, "lon": 114.2,  # 河北REDACTED_PLACE
            "tz": 8.0,
        },
        "expected": {}
    },
]

# ============================================================================
# 参考值：BPHS Shadbala 最低要求（Rupas）
# ============================================================================
BPHS_MIN_REQUIRED = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0,
    "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0
}

# PyJHora 使用的 Naisargika Bala（Shashtiamshas）
NAISARGIKA_REF = {
    "Sun": 60.0, "Moon": 51.43, "Venus": 42.86,
    "Jupiter": 34.29, "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57
}

# ============================================================================
# 内部一致性测试：检查 Shadbala 子项和是否等于总分
# ============================================================================
def test_internal_consistency(result):
    """检查每个行星的6个子项之和是否等于 total_virupas"""
    errors = []
    for pname, pd in result.get("planets", {}).items():
        sthana_total = pd.get("sthana_bala", {}).get("total", 0)
        dig = pd.get("dig_bala", 0)
        kala_total = pd.get("kala_bala", {}).get("total", 0)
        chesta = pd.get("chesta_bala", 0)
        naisargika = pd.get("naisargika_bala", 0)
        drik = pd.get("drik_bala", 0)
        total = pd.get("total_virupas", 0)
        
        computed = sthana_total + dig + kala_total + chesta + naisargika + drik
        diff = abs(computed - total)
        if diff > 0.1:
            errors.append(f"{pname}: 子项和={computed:.2f} ≠ total_virupas={total:.2f} (差{diff:.2f})")
    return errors


# ============================================================================
# 外部一致性测试：检查是否满足 BPHS 最低要求
# ============================================================================
def test_min_required(result):
    """检查每个行星是否满足 BPHS 最低 Shadbala Rupas 要求"""
    errors = []
    for pname, pd in result.get("planets", {}).items():
        total_rupas = pd.get("total_rupas", 0)
        min_req = BPHS_MIN_REQUIRED.get(pname, 5.0)
        if total_rupas < min_req:
            errors.append(f"{pname}: {total_rupas:.2f} Rupas < 最低要求 {min_req:.2f}")
    return errors


# ============================================================================
# Naisargika Bala 对比
# ============================================================================
def test_naisargika(result):
    """检查 Naisargika Bala 是否匹配参考值"""
    errors = []
    for pname, pd in result.get("planets", {}).items():
        actual = pd.get("naisargika_bala", 0)
        expected = NAISARGIKA_REF.get(pname, 0)
        if abs(actual - expected) > 0.1:
            errors.append(f"{pname}: Naisargika={actual:.2f} ≠ 参考值{expected:.2f}")
    return errors


# ============================================================================
# 排序合理性测试
# ============================================================================
def test_ranking_sanity(result):
    """检查排名是否合理（擢升行星应比落陷行星强）"""
    planets = result.get("planets", {})
    ranking = result.get("ranking", [])
    errors = []
    
    # 如果有擢升行星，应排在非擢升行星之前
    if len(ranking) >= 2:
        pass  # 无法自动判断合理排序，只做记录
    
    return errors


# ============================================================================
# 运行全部测试
# ============================================================================
def run_all_tests():
    results_summary = []
    total_tests = 0
    total_errors = 0
    
    for tc in TEST_CASES:
        d = tc["data"]
        print(f"\n{'='*60}")
        print(f"测试: {tc['name']}")
        print(f"     出生: {d['year']}-{d['month']:02d}-{d['day']:02d} {d['hour']:02d}:{d['minute']:02d}")
        print(f"     地点: {d['lat']}°, {d['lon']}°, tz={d['tz']}")
        print(f"{'='*60}")
        
        # 简化：不实际调用占星引擎（引擎需要完整行星数据）
        # 实际运行需要先计算 chart 获取完整行星数据
        # 这里先占位，后续接入 jyotish_engine.py 的 calculate_full_chart
        
        case_result = {
            "name": tc["name"],
            "tests": {},
        }
        
        # 测试1: 内部一致性
        # TODO: 接入完整计算链后启用
        # errors = test_internal_consistency(result)
        
        # 测试2: Naisargika Bala 对比
        # TODO: 接入
        
        results_summary.append(case_result)
    
    return results_summary


# ============================================================================
# 手动单用例测试函数（用于快速验证特定命盘）
# ============================================================================
def verify_shadbala_for_chart(planets, asc_sign, birth_hour, sun_lon, moon_lon,
                               birth_minute=0, chart_name="测试盘"):
    """对给定命盘运行完整的 Shadbala 验证"""
    result = calc_shadbala(planets, asc_sign, birth_hour, sun_lon, moon_lon,
                           birth_minute)
    
    print(f"\n{'='*60}")
    print(f"Shadbala 验证: {chart_name}")
    print(f"{'='*60}")
    print(f"方法: {result['method']}")
    print(f"排名: {' > '.join(result['ranking'])}")
    print(f"最强: {result['strongest']}, 最弱: {result['weakest']}")
    print(f"\n{'行星':>8} | {'Rupas':>6} | {'最低要求':>8} | {'达标?':>5} | {'Chesta':>6} | {'Ishta':>6} | {'Kashta':>6}")
    print("-" * 65)
    
    errors = []
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        pd = result.get("planets", {}).get(pname, {})
        rupas = pd.get("total_rupas", 0)
        min_req = BPHS_MIN_REQUIRED.get(pname, 5.0)
        passed = "✅" if rupas >= min_req else "❌"
        chesta = pd.get("chesta_bala", 0)
        ishta = pd.get("ishta_phala", 0)
        kashta = pd.get("kashta_phala", 0)
        print(f"{pname:>8} | {rupas:>6.2f} | {min_req:>8.2f} | {passed:>5} | {chesta:>6.1f} | {ishta:>6.1f} | {kashta:>6.1f}")
        if rupas < min_req:
            errors.append(f"{pname}: {rupas:.2f} < {min_req:.2f}")
    
    # 内部一致性测试
    consistency = test_internal_consistency(result)
    for e in consistency:
        errors.append(e)
    
    # Naisargika 测试
    naisargika = test_naisargika(result)
    for e in naisargika:
        errors.append(e)
    
    print("-" * 65)
    if errors:
        print(f"\n⚠️  发现 {len(errors)} 个问题:")
        for e in errors:
            print(f"  • {e}")
    else:
        print(f"\n✅ 全部检查通过")
    
    return result, errors


if __name__ == "__main__":
    # 使用一楠的出生数据运行验证
    planets = {
        'Sun': {'sign': 'Aries', 'degree': 27.5, 'house': 9, 'retrograde': False, 'speed': 0.98},
        'Moon': {'sign': 'Aquarius', 'degree': 10.0, 'house': 7, 'retrograde': False, 'speed': 13.5},
        'Mars': {'sign': 'Cancer', 'degree': 5.0, 'house': 12, 'retrograde': False, 'speed': 0.65},
        'Mercury': {'sign': 'Pisces', 'degree': 22.0, 'house': 8, 'retrograde': False, 'speed': 1.2},
        'Jupiter': {'sign': 'Virgo', 'degree': 15.0, 'house': 2, 'retrograde': True, 'speed': -0.08},
        'Venus': {'sign': 'Pisces', 'degree': 5.0, 'house': 8, 'retrograde': False, 'speed': 1.1},
        'Saturn': {'sign': 'Aquarius', 'degree': 28.0, 'house': 7, 'retrograde': False, 'speed': 0.05},
    }
    
    verify_shadbala_for_chart(
        planets, 'Leo', 14.75, 27.5, 310.0,
        birth_minute=45,
        chart_name="一楠 (REDACTED_DATE 14:45 河北REDACTED_PLACE)"
    )
