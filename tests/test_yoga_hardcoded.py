"""
PyJHora 风格硬编码 Yoga True/False 测试
"""
import sys, os
SKILL_DIR = '/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology'
sys.path.insert(0, os.path.join(SKILL_DIR, 'scripts'))
RULES_PATH = os.path.join(SKILL_DIR, 'references', 'yoga_rules.json')
from yoga_engine import YogaEngine
engine = YogaEngine(RULES_PATH)

def detect(rule_id, planets, ascendant, context=None):
    results = engine.detect(planets, ascendant, context=context)
    return any(r.get('rule_id') == rule_id for r in results)

def check(name, rule_id, planets, asc, expected):
    result = detect(rule_id, planets, asc)
    ok = result == expected
    tag = 'PASS' if ok else 'FAIL'
    print(f'  [{tag}] {name}: expect={expected} got={result}')
    return ok

results = []

print('=' * 55)
print('Hardcoded Yoga Tests (PyJHora style)')
print('=' * 55)

# -------------------------------------------------------
# pushkala_yoga: asc_lord exalted/own + Moon not deb + benefic in 1st
# -------------------------------------------------------
print('\n--- pushkala_yoga ---')
results.append(check('True-lion-asc-exalted-sun', 'pushkala_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':1,'sign':'Sagittarius','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', True))

results.append(check('False-gemini-asc-neutral', 'pushkala_yoga', {
    'Sun':{'house':12,'sign':'Taurus','degree':10},'Moon':{'house':6,'sign':'Libra','degree':15},
    'Mars':{'house':3,'sign':'Virgo','degree':10},'Mercury':{'house':11,'sign':'Pisces','degree':10},
    'Jupiter':{'house':7,'sign':'Pisces','degree':5},'Venus':{'house':5,'sign':'Sagittarius','degree':10},
    'Saturn':{'house':8,'sign':'Capricorn','degree':10},'Rahu':{'house':4,'sign':'Scorpio','degree':10},
    'Ketu':{'house':10,'sign':'Taurus','degree':10},
}, 'Gemini', False))

results.append(check('False-moon-debilitated', 'pushkala_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':12,'sign':'Scorpio','degree':15},
    'Mars':{'house':4,'sign':'Scorpio','degree':10},'Mercury':{'house':8,'sign':'Pisces','degree':10},
    'Jupiter':{'house':1,'sign':'Sagittarius','degree':5},'Venus':{'house':2,'sign':'Virgo','degree':10},
    'Saturn':{'house':6,'sign':'Capricorn','degree':10},'Rahu':{'house':3,'sign':'Libra','degree':10},
    'Ketu':{'house':9,'sign':'Aries','degree':10},
}, 'Leo', False))

# -------------------------------------------------------
# koorma_yoga: benefic in 1st AND (5th or 9th lord in 1st)
# -------------------------------------------------------
print('\n--- koorma_yoga ---')
results.append(check('True-5th-lord-in-1st', 'koorma_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':1,'sign':'Sagittarius','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', True))

results.append(check('True-9th-lord-in-1st', 'koorma_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':1,'sign':'Aries','degree':5},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':11,'sign':'Sagittarius','degree':5},'Venus':{'house':1,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', True))

results.append(check('False-ben-in-1st-no-lord', 'koorma_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':1,'sign':'Virgo','degree':10},
    'Jupiter':{'house':11,'sign':'Sagittarius','degree':5},'Venus':{'house':2,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', False))

results.append(check('False-lord-in-1st-no-ben', 'koorma_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':1,'sign':'Aries','degree':5},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':11,'sign':'Sagittarius','degree':5},'Venus':{'house':2,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', False))

# -------------------------------------------------------
# bvr_dharidhra_11_precise: method1
# -------------------------------------------------------
print('\n--- bvr_dharidhra_11_precise ---')
results.append(check('True-l2-l11-in-dusthana', 'bvr_dharidhra_11_precise', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':4,'sign':'Scorpio','degree':10},'Mercury':{'house':8,'sign':'Pisces','degree':10},
    'Jupiter':{'house':1,'sign':'Leo','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':2,'sign':'Virgo','degree':10},
    'Ketu':{'house':8,'sign':'Pisces','degree':10},
}, 'Leo', True))

results.append(check('False-l2-l11-not-dusthana', 'bvr_dharidhra_11_precise', {
    'Sun':{'house':1,'sign':'Leo','degree':10},'Moon':{'house':5,'sign':'Sagittarius','degree':15},
    'Mars':{'house':10,'sign':'Taurus','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':9,'sign':'Aries','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':3,'sign':'Libra','degree':10},
    'Ketu':{'house':9,'sign':'Aries','degree':10},
}, 'Leo', False))

# Summary
ok = sum(1 for r in results if r)
total = len(results)
print(f'\nResults: {ok}/{total} passed ({total-ok} failed)')
