"""
自动化 Yoga 测试运行器 — 从 yoga_test_suite.json 加载用例并批量验证
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
RULES_PATH = ROOT / 'references' / 'yoga_rules.json'
from yoga_engine import YogaEngine
engine = YogaEngine(str(RULES_PATH))

def detect(rule_id, planets, asc, ctx=None):
    return any(r.get('rule_id') == rule_id for r in engine.detect(planets, asc, context=ctx))

suite_path = ROOT / 'tests' / 'yoga_test_suite.json'
with suite_path.open() as f:
    suite = json.load(f)

passed = 0
failed = 0
failures = []

print(f'Yoga Test Suite: {len(suite)} rules')
print('=' * 60)

for entry in suite:
    rid = entry['rule_id']
    rid_short = rid[-30:] if len(rid) > 30 else rid
    
    for mode in ['true', 'false']:
        if mode not in entry: continue
        d = entry[mode]
        expected = (mode == 'true')
        result = detect(rid, d['planets'], d['asc'], d.get('context'))
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            chart = d.get('chart', '?')
            failures.append(f'  FAIL: {rid_short:30s} {mode:5s} chart={chart} expect={expected} got={result}')

for f in failures:
    print(f)
print(f'\nResults: {passed} passed, {failed} failed ({passed+failed} total)')
