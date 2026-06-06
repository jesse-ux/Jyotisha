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
# pushkala_yoga (BVR-26): L1 with Moon; Moon's dispositor in kendra/Adhimitra + rasi-aspects Lagna
# -------------------------------------------------------
print('\n--- pushkala_yoga ---')
# Leo asc, Sun(L1) in 5th/Gemini with Moon, dispositor=Mercury in 10th/Capricorn(kendra, rasi-aspects Leo)
results.append(check('True-l1-with-moon-disp-kendra', 'pushkala_yoga', {
    'Sun':{'house':5,'sign':'Gemini','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':10,'sign':'Capricorn','degree':10},
    'Jupiter':{'house':11,'sign':'Sagittarius','degree':5},'Venus':{'house':2,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', True))

results.append(check('False-l1-not-with-moon', 'pushkala_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':1,'sign':'Sagittarius','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', False))

results.append(check('False-disp-not-kendra', 'pushkala_yoga', {
    'Sun':{'house':5,'sign':'Gemini','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':4,'sign':'Scorpio','degree':10},'Mercury':{'house':12,'sign':'Pisces','degree':10},
    'Jupiter':{'house':1,'sign':'Sagittarius','degree':5},'Venus':{'house':2,'sign':'Virgo','degree':10},
    'Saturn':{'house':6,'sign':'Capricorn','degree':10},'Rahu':{'house':3,'sign':'Libra','degree':10},
    'Ketu':{'house':9,'sign':'Aries','degree':10},
}, 'Leo', False))

# -------------------------------------------------------
# koorma_yoga (BVR-54 Method 1): 5/6/7 all strong benefics OR 1/3/11 all strong benefics
# -------------------------------------------------------
print('\n--- koorma_yoga ---')
# 1/3/11 all occupied by strong benefics: Jupiter(1/Leo), Venus(3/Libra), Moon(11/Gemini)
results.append(check('True-benefics-in-1-3-11', 'koorma_yoga', {
    'Sun':{'house':12,'sign':'Taurus','degree':10},'Moon':{'house':11,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':1,'sign':'Leo','degree':5},'Venus':{'house':3,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', True))

results.append(check('False-malefic-in-target-houses', 'koorma_yoga', {
    'Sun':{'house':1,'sign':'Leo','degree':10},'Moon':{'house':5,'sign':'Sagittarius','degree':15},
    'Mars':{'house':10,'sign':'Taurus','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':9,'sign':'Aries','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':4,'sign':'Scorpio','degree':10},
    'Ketu':{'house':10,'sign':'Taurus','degree':10},
}, 'Leo', False))

results.append(check('False-empty-target-house', 'koorma_yoga', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':12,'sign':'Sagittarius','degree':5},'Venus':{'house':3,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', False))

results.append(check('False-weak-benefic-in-house', 'koorma_yoga', {
    'Sun':{'house':12,'sign':'Taurus','degree':10},'Moon':{'house':11,'sign':'Gemini','degree':15},
    'Mars':{'house':8,'sign':'Pisces','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':1,'sign':'Capricorn','degree':5},'Venus':{'house':3,'sign':'Libra','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':6,'sign':'Capricorn','degree':10},
    'Ketu':{'house':12,'sign':'Cancer','degree':10},
}, 'Leo', False))

# -------------------------------------------------------
# bvr_dharidhra_11_precise
# -------------------------------------------------------
print('\n--- bvr_dharidhra_11_precise ---')
# True: L2 (Mercury) or L11 in dusthana
results.append(check('True-l2-l11-in-dusthana', 'bvr_dharidhra_11_precise', {
    'Sun':{'house':9,'sign':'Aries','degree':10},'Moon':{'house':5,'sign':'Gemini','degree':15},
    'Mars':{'house':4,'sign':'Scorpio','degree':10},'Mercury':{'house':8,'sign':'Pisces','degree':10},
    'Jupiter':{'house':1,'sign':'Leo','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':2,'sign':'Virgo','degree':10},
    'Ketu':{'house':8,'sign':'Pisces','degree':10},
}, 'Leo', True))

# True-v149: L2/L11 not in dusthana, but v149 triggers: L1 (Sun) associated with trik lord
# (L6 Saturn aspects Sun from 7th) and malefic Mars aspects L1 from 10th
results.append(check('True-v149-assoc-malefic', 'bvr_dharidhra_11_precise', {
    'Sun':{'house':1,'sign':'Leo','degree':10},'Moon':{'house':5,'sign':'Sagittarius','degree':15},
    'Mars':{'house':10,'sign':'Taurus','degree':10},'Mercury':{'house':2,'sign':'Virgo','degree':10},
    'Jupiter':{'house':9,'sign':'Aries','degree':5},'Venus':{'house':11,'sign':'Gemini','degree':10},
    'Saturn':{'house':7,'sign':'Aquarius','degree':10},'Rahu':{'house':3,'sign':'Libra','degree':10},
    'Ketu':{'house':9,'sign':'Aries','degree':10},
}, 'Leo', True))

# False: Cancer asc - no variants trigger. L2(Sun)/L11(Venus) not dusthana,
# L1(Moon) not with trik lords, no malefic aspect on Moon
results.append(check('False-no-variant-triggers', 'bvr_dharidhra_11_precise', {
    'Sun':{'house':9,'sign':'Pisces','degree':10},'Moon':{'house':4,'sign':'Libra','degree':15},
    'Mars':{'house':5,'sign':'Scorpio','degree':10},'Mercury':{'house':8,'sign':'Aquarius','degree':10},
    'Jupiter':{'house':3,'sign':'Virgo','degree':5},'Venus':{'house':10,'sign':'Aries','degree':10},
    'Saturn':{'house':11,'sign':'Taurus','degree':10},'Rahu':{'house':8,'sign':'Aquarius','degree':10},
    'Ketu':{'house':5,'sign':'Scorpio','degree':10},
}, 'Cancer', False))

# Summary
ok = sum(1 for r in results if r)
total = len(results)
print(f'\nResults: {ok}/{total} passed ({total-ok} failed)')
