#!/usr/bin/env python3
"""
自动化Yoga误差分析器
对Top FP/FN规则，提取具体星盘例子并比较中间计算结果
"""
import json, sys, os
from collections import defaultdict

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, 'scripts'))
from yoga_engine import YogaEngine, YogaContext

RULES_PATH = os.path.join(SKILL_DIR, 'references', 'yoga_rules.json')
POS_PATH = os.path.join(SKILL_DIR, 'references', 'planet_positions_60.json')
PYJ_PATH = os.path.join(SKILL_DIR, 'references', 'standard_test_charts.json')
REPORT_PATH = os.path.join(SKILL_DIR, 'references', 'validation_logic_report.json')

def main():
    engine = YogaEngine(RULES_PATH)
    
    with open(POS_PATH) as f:
        pos_data = json.load(f)
    with open(PYJ_PATH) as f:
        pyj_data = json.load(f)
    with open(REPORT_PATH) as f:
        report = json.load(f)
    
    pyj_charts = {c['name']: c for c in pyj_data['charts']}
    charts_by_name = {c['name']: c for c in pos_data['charts']}
    
    # 从false_positives和false_negatives列表中按规则分组
    fp_by_rule = defaultdict(list)
    fn_by_rule = defaultdict(list)
    
    for item in report.get('false_positives', []):
        fp_by_rule[item['rule_id']].append(item['chart'])
    
    for item in report.get('false_negatives', []):
        fn_by_rule[item['rule_id']].append(item['chart'])
    
    # 合并errors，按总数量排序
    all_errors = {}
    for rid in set(list(fp_by_rule.keys()) + list(fn_by_rule.keys())):
        all_errors[rid] = {
            'fp': len(fp_by_rule.get(rid, [])),
            'fn': len(fn_by_rule.get(rid, [])),
            'fp_charts': fp_by_rule.get(rid, []),
            'fn_charts': fn_by_rule.get(rid, [])
        }
    
    sorted_errors = sorted(all_errors.items(), key=lambda x: x[1]['fp'] + x[1]['fn'], reverse=True)
    
    print("=" * 80)
    print("Top Yoga Error Analysis")
    print("=" * 80)
    
    for rule_id, err in sorted_errors[:15]:
        total = err['fp'] + err['fn']
        if total == 0:
            continue
        
        rule = next((r for r in engine.rules if r['id'] == rule_id), None)
        if not rule:
            continue
        
        print(f"\n{'='*80}")
        print(f"Rule: {rule_id} ({rule.get('name', '')}) — FP:{err['fp']} FN:{err['fn']} Total:{total}")
        print(f"{'='*80}")
        
        if err['fn_charts']:
            print(f"\n  FN Examples (PyJHora=True, Skill=False):")
            for chart_name in err['fn_charts'][:3]:
                analyze_example(engine, charts_by_name, pyj_charts, chart_name, rule_id, 'FN')
        
        if err['fp_charts']:
            print(f"\n  FP Examples (PyJHora=False, Skill=True):")
            for chart_name in err['fp_charts'][:3]:
                analyze_example(engine, charts_by_name, pyj_charts, chart_name, rule_id, 'FP')

def analyze_example(engine, charts_by_name, pyj_charts, chart_name, rule_id, error_type):
    chart = charts_by_name.get(chart_name)
    if not chart:
        return
    
    planets = chart['planets']
    ascendant = chart['ascendant']
    pyj_chart = pyj_charts.get(chart_name)
    pyj_yogas = pyj_chart.get('expected_yogas', []) if pyj_chart else []
    
    ctx = YogaContext(planets, ascendant)
    
    print(f"\n    [{error_type}] {chart_name} — Asc: {ascendant}")
    
    # 根据规则id输出相关中间计算
    if rule_id in ['kahala_yoga', 'bvr_kaahala_yoga']:
        l1 = ctx.lord_of_house(1)
        l4 = ctx.lord_of_house(4)
        l9 = ctx.lord_of_house(9)
        print(f"      L1={l1} in H{ctx.house_of(l1)} (strong: {ctx.house_of(l1) in [1,4,5,7,9,10] if l1 else 'N/A'})")
        print(f"      L4={l4} in H{ctx.house_of(l4)}")
        print(f"      L9={l9} in H{ctx.house_of(l9)}")
        if l4 and l9:
            off = (ctx.house_of(l9) - ctx.house_of(l4)) % 12
            print(f"      offset(L4,L9)={off} (kendra: {off in [0,3,6,9]})")
    
    elif rule_id == 'sankha_yoga':
        l1 = ctx.lord_of_house(1)
        l5 = ctx.lord_of_house(5)
        l6 = ctx.lord_of_house(6)
        l9 = ctx.lord_of_house(9)
        l10 = ctx.lord_of_house(10)
        print(f"      L1={l1} in H{ctx.house_of(l1)} (strong: {ctx.house_of(l1) in [1,4,5,7,9,10] if l1 else 'N/A'})")
        print(f"      L5={l5} in H{ctx.house_of(l5)}")
        print(f"      L6={l6} in H{ctx.house_of(l6)}")
        print(f"      L9={l9} in H{ctx.house_of(l9)} (strong: {ctx.house_of(l9) in [1,4,5,7,9,10] if l9 else 'N/A'})")
        print(f"      L10={l10} in H{ctx.house_of(l10)}")
        if l5 and l6:
            off1 = (ctx.house_of(l6) - ctx.house_of(l5)) % 12
            print(f"      offset(L5,L6)={off1} (kendra: {off1 in [0,3,6,9]})")
        if l1 and l10:
            print(f"      L1==L10 house: {ctx.house_of(l1) == ctx.house_of(l10)}")
            print(f"      L1 sign: {ctx.sign_of(l1)} (movable: {ctx.sign_of(l1) in ['Aries','Cancer','Libra','Capricorn'] if l1 else 'N/A'})")
    
    elif rule_id == 'bvr_dharidhra_11_precise':
        l1 = ctx.lord_of_house(1)
        l2 = ctx.lord_of_house(2)
        l11 = ctx.lord_of_house(11)
        print(f"      L2={l2} in H{ctx.house_of(l2)}")
        print(f"      L11={l11} in H{ctx.house_of(l11)}")
        print(f"      method1 (L2/L11 in 6/8/12): {ctx.house_of(l2) in [6,8,12] if l2 else False} / {ctx.house_of(l11) in [6,8,12] if l11 else False}")
    
    elif rule_id == 'bvr_annadana_yoga':
        l2 = ctx.lord_of_house(2)
        l11 = ctx.lord_of_house(11)
        print(f"      L2={l2} in H{ctx.house_of(l2)}")
        print(f"      L11={l11} in H{ctx.house_of(l11)}")
    
    elif rule_id == 'bvr_kapata_yoga':
        l4 = ctx.lord_of_house(4)
        print(f"      L4={l4} in H{ctx.house_of(l4)}")
    
    elif rule_id == 'bvr_nishkapata_precise':
        l4 = ctx.lord_of_house(4)
        print(f"      L4={l4} in H{ctx.house_of(l4)}")
    
    elif rule_id == 'bvr_thrikaala_gnana_yoga':
        jup = ctx.house_of('Jupiter') if 'Jupiter' in planets else None
        mer = ctx.house_of('Mercury') if 'Mercury' in planets else None
        print(f"      Jupiter in H{jup}")
        print(f"      Mercury in H{mer}")
    
    else:
        for h in range(1, 13):
            p = ctx.lord_of_house(h)
            if p:
                print(f"      L{h}={p} in H{ctx.house_of(p)}")
    
    # 列出PyJHora期望的yoga（包含当前规则的变体）
    matched = [y for y in pyj_yogas if rule_id.replace('bvr_', '') in y or rule_id in y]
    print(f"      PyJHora matched: {matched}")

if __name__ == '__main__':
    main()
