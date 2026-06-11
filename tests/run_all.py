#!/usr/bin/env python3
"""印度占星Skill自动化测试运行器 v1.0"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))

TESTS = []

def test(name):
    def decorator(fn): TESTS.append((name, fn)); return fn
    return decorator

# === 模块导入测试 ===
@test("ashtakavarga import")
def t1(): from ashtakavarga import calc_ashtakavarga, calc_prastara_av, calc_sodhita_av

@test("shadbala import")
def t2(): from shadbala import calc_shadbala

@test("jaimini import")
def t3(): from jaimini import _chara_dasha_duration_knrao, _resolve_chara_dasha_lord

@test("bhava_bala import")
def t4(): from bhava_bala import calc_bhava_bala

@test("kakshya import")
def t5(): from kakshya import calc_kakshya_scores, get_kakshya_lord

@test("kp_system import") 
def t6(): from kp_system import get_kp_lords, calc_kp_analysis

@test("synastry import")
def t7(): from synastry import calc_ashtakoot

@test("prashna import")
def t8(): from prashna import calc_prashna_chart, get_kp_prashna_answer

@test("remedies import")
def t9(): from remedies import recommend_remedies, quick_remedy

@test("pancha_mahapurusha import")
def t10(): from pancha_mahapurusha import detect_pancha_mahapurusha

@test("sade_sati import") 
def t11(): from sade_sati import calc_sade_sati_complete

@test("sudarshana_chakra import")
def t12(): from sudarshana_chakra import calc_sudarshana_chakra

@test("career_analysis import")
def t13(): from career_analysis import analyze_career

@test("relationship_analysis import")
def t14(): from relationship_analysis import analyze_relationship

@test("muhurtha_election import")
def t15(): from muhurtha_election import evaluate_muhurtha

@test("yoga_expansion import")
def t16(): from yoga_expansion import detect_all_yogas

@test("birth_time_rectifier import")
def t17(): from birth_time_rectifier import check_lagna_boundary, get_effective_accuracy

@test("conditional_dashas import")
def t18(): from conditional_dashas import calc_dwisaptati_dasha, check_dwisaptati_condition

@test("extended_dashas import")
def t19(): from extended_dashas import get_available_dashas, DASHA_REGISTRY

@test("chart_renderer import")
def t20(): from chart_renderer import render_south_indian_chart, render_html_report

# === 功能测试 ===
@test("PAV validation")
def t21():
    from ashtakavarga import calc_prastara_av, SEVEN_PLANETS
    planets = {p: {'sign': 'Aries', 'degree': i*40} for i,p in enumerate(SEVEN_PLANETS)}
    pav = calc_prastara_av(planets, 0)
    assert pav['all_valid'], "PAV validation failed"

@test("Shadbala invariant")
def t22():
    from shadbala import calc_shadbala
    p = {pn: {'sign': 'Aries', 'degree': i*40, 'house': i+1} for i,pn in enumerate(['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'])}
    result = calc_shadbala(p, 'Aries', 12, 15, 45, 0)
    assert len(result['planets']) == 7

@test("KP sublord")
def t23():
    from kp_system import get_kp_lords
    r = get_kp_lords(15.5)
    assert r['sub_lord'] and r['sub_sub_lord']

@test("Synastry score range")
def t24():
    from synastry import calc_ashtakoot
    r = calc_ashtakoot(15.5, 120)
    assert 0 <= r['total_score'] <= 36

@test("Sade Sati detection")
def t25():
    from sade_sati import calc_sade_sati
    r = calc_sade_sati('Aries', 'Aries')
    assert r['active'] and r['phase'] == 'peak'

@test("Remedies generation")
def t26():
    from remedies import recommend_remedies
    sb = {'Sun': {'total_rupas': 0.4}, 'Saturn': {'total_rupas': 0.3}}
    r = recommend_remedies(sb, doshas=['Mangal Dosha'])
    assert len(r['recommendations']['gems']) >= 1

@test("Muhurtha evaluation")
def t27():
    from muhurtha_election import evaluate_muhurtha
    r = evaluate_muhurtha('marriage', 3, 'Rohini', 4, 'Monday', 'Taurus')
    assert r['verdict'] in ('大吉', '尚可', '中性', '不吉')

@test("Dasha count")
def t28():
    from extended_dashas import get_available_dashas
    assert len(get_available_dashas()) >= 30, "Dasha count should be >= 30"

@test("Rectifier boundary check")
def t29():
    from birth_time_rectifier import check_lagna_boundary
    is_b, _ = check_lagna_boundary(1.5)
    assert is_b

@test("PMC detection")
def t30():
    from pancha_mahapurusha import detect_pancha_mahapurusha
    p = {'Mars': {'sign': 'Capricorn', 'house': 4, 'degree': 280}}
    r = detect_pancha_mahapurusha(p)
    assert len(r) >= 1

# === 运行 ===
if __name__ == '__main__':
    passed = 0; failed = 0; start = time.time()
    print(f"\n{'='*50}")
    print(f"🔮 Jyotish Skill Test Suite v1.0 — {len(TESTS)} tests")
    print(f"{'='*50}")
    for name, fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  ✅ {name}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {name}: {str(e)[:60]}")
    t = time.time() - start
    print(f"\n{'='*50}")
    print(f"  Passed: {passed}/{len(TESTS)} ({passed/len(TESTS)*100:.0f}%)")
    print(f"  Failed: {failed}")
    print(f"  Time: {t:.1f}s")
    sys.exit(0 if failed == 0 else 1)
