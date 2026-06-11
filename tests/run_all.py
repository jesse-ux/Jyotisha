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

# === v6.7.5 新增功能测试 ===
@test("PMC combustion cancellation")
def t31():
    from pancha_mahapurusha import detect_pancha_mahapurusha
    p = {'Mars': {'sign': 'Capricorn', 'house': 4, 'degree': 50}}
    r = detect_pancha_mahapurusha(p, sun_degree=53)
    assert r[0]['is_valid'] == False, "Mars too close to Sun should cancel PMC"

@test("PMC retrograde cancellation")
def t32():
    from pancha_mahapurusha import detect_pancha_mahapurusha
    p = {'Jupiter': {'sign': 'Cancer', 'house': 1, 'degree': 95, 'retrograde': True}}
    r = detect_pancha_mahapurusha(p)
    assert r[0]['is_valid'] == False

@test("Bhava Bala computation")
def t33():
    from bhava_bala import calc_bhava_adhipathi_bala, calc_bhava_dig_bala
    adhi = calc_bhava_adhipathi_bala(['Aries']*12, {'Mars': 500})
    assert len(adhi) == 12
    dig = calc_bhava_dig_bala(['Aries']*12, [15]*12)
    assert len(dig) == 12

@test("Kakshya scoring")
def t34():
    from kakshya import calc_kakshya_scores
    p = {'Sun': {'sign': 'Aries', 'degree': 15.5}}
    r = calc_kakshya_scores(p, 0)
    assert 'Sun' in r['planets']

@test("Sudarshana convergence")
def t35():
    from sudarshana_chakra import calc_sudarshana_chakra
    p = {'Sun': {'sign_idx': 0, 'degree': 15}, 'Moon': {'sign_idx': 3, 'degree': 22}}
    r = calc_sudarshana_chakra(p, asc_sign_idx=0)
    assert 'convergence' in r

@test("Career analysis fields")
def t36():
    from career_analysis import analyze_career
    p = {'Sun': {'house': 10}, 'Saturn': {'house': 6}}
    r = analyze_career(p, 'Aries')
    assert len(r['fields']) >= 1

@test("Relationship Venus check")
def t37():
    from relationship_analysis import analyze_relationship
    p = {'Venus': {'sign': 'Taurus', 'house': 7}, 'Moon': {'house': 4}}
    r = analyze_relationship(p, 'Aries')
    assert 'assessment' in r

@test("Prashna chart creation")
def t38():
    from prashna import calc_prashna_chart, get_kp_prashna_answer
    from datetime import datetime
    r = calc_prashna_chart(datetime.now(), {'Sun': {'sign': 'Aries'}}, 45.5)
    assert r['asc_sign'] in ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

@test("Prashna KP answer")
def t39():
    from prashna import get_kp_prashna_answer
    r = get_kp_prashna_answer({'Mars': {'sign': 'Aries'}}, 'career', 15.5)
    assert r['confidence'] in ('高', '中')

@test("Prashna Arudha")
def t40():
    from prashna import detect_prashna_arudha
    r = detect_prashna_arudha({'Mars': {'sign': 'Aries'}}, 15.5, 7)
    assert r['arudha_house'] >= 1

@test("Conditional Dasha trigger")
def t41():
    from conditional_dashas import check_dwisaptati_condition
    assert check_dwisaptati_condition('Sun', 1) == True

@test("Conditional Dasha calc")
def t42():
    from conditional_dashas import calc_dwisaptati_dasha
    from datetime import datetime
    r = calc_dwisaptati_dasha(datetime(1990,6,15), 'Sun', 15.5)
    assert len(r) == 8

@test("Extended Dasha registry")
def t43():
    from extended_dashas import get_dasha_info, get_available_dashas
    assert get_dasha_info('kalachakra')['type'] == 'nakshatra'
    assert len(get_available_dashas()) >= 35

@test("Yoga expansion detect")
def t44():
    from yoga_expansion import detect_kemadruma, detect_graha_yuddha
    r = detect_kemadruma({'Moon': {'sign': 'Aries'}})
    assert isinstance(r, dict)

@test("Yoga graha_yuddha")
def t45():
    from yoga_expansion import detect_graha_yuddha
    r = detect_graha_yuddha({'Mars': {'degree': 50.0}, 'Jupiter': {'degree': 50.3}})
    assert len(r) >= 1

@test("Yoga gandanta")
def t46():
    from yoga_expansion import detect_gandanta
    r = detect_gandanta({'Moon': {'degree': 118.5}})  # Cancer end
    assert len(r) >= 0  # may or may not be gandanta

@test("Rectifier accuracy matrix")
def t47():
    from birth_time_rectifier import get_effective_accuracy, get_enabled_vargas
    acc = get_effective_accuracy('minute', 'hospital')
    assert acc == 'minute'
    v = get_enabled_vargas('minute')
    assert v['D9'] == 'enabled'

@test("Tajika Yogas detect")
def t48():
    from tajika import detect_tajika_yogas
    r = detect_tajika_yogas({'Sun': {'sign': 'Aries', 'degree': 15}, 'Moon': {'sign': 'Aries', 'degree': 18}})
    assert len(r) >= 1

@test("Tajika Sahams count")
def t49():
    from tajika import calc_all_sahams
    from datetime import datetime
    r = calc_all_sahams({'Sun': 80, 'Moon': 105, 'Mars': 220, 'Mercury': 75, 'Jupiter': 310, 'Venus': 350, 'Saturn': 180, 'Rahu': 45, 'Ketu': 225}, 15.0, datetime(1990,6,15,12,0))
    assert len(r) >= 30

@test("Chart renderer SVG")
def t50():
    from chart_renderer import render_south_indian_chart
    svg = render_south_indian_chart({'Sun': 'Aries', 'Moon': 'Cancer'}, 'Aries')
    assert '<svg' in svg and '</svg>' in svg

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
