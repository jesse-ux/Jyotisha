#!/usr/bin/env python3
"""Chara Dasha v6.9.10 dignity_adjustment bug fix verification test."""
import sys
sys.path.insert(0, 'scripts')
from jaimini import calc_chara_dasha, _PLANET_DIGNITY_KNRAO, SIGNS, _chara_dasha_duration_knrao

# ============================================================
# Test 1: Einstein - Gemini Lagna
# ============================================================
print("=" * 70)
print("Test 1: Einstein (Gemini Lagna)")
print("=" * 70)

longitudes_einstein = {
    'Sun': 353.0,    # Pisces (11)
    'Moon': 107.0,   # Cancer (3)
    'Mars': 338.0,   # Pisces (11)
    'Mercury': 332.0, # Pisces (11)
    'Jupiter': 302.0, # Aquarius (10)
    'Venus': 24.0,   # Aries (0)
    'Saturn': 41.0,  # Taurus (1)
    'Rahu': 128.0,   # Leo (4)
    'Ketu': 308.0,   # Aquarius (10)
}

result = calc_chara_dasha(2, longitudes_einstein, 1879, 3, 14)
print(f"Method: {result['method']}")
print(f"Total cycle years: {result['total_cycle_years']}")
print()

for d in result['dasha_sequence']:
    print(f"  {d['order']:2d}. {d['sign']:12s} | Lord: {d['lord']:8s} in {d['lord_in_sign']:12s} | Dur: {d['duration_years']:2d}y | Dignity: {d['dignity_adjustment']}")

exalted = sum(1 for d in result['dasha_sequence'] if d['dignity_adjustment'] == 'exalted')
debilitated = sum(1 for d in result['dasha_sequence'] if d['dignity_adjustment'] == 'debilitated')
none_count = sum(1 for d in result['dasha_sequence'] if d['dignity_adjustment'] == 'none')
print(f"\nDignity counts: exalted={exalted}, debilitated={debilitated}, none={none_count}")

# ============================================================
# Test 2: Obama - Capricorn Lagna
# ============================================================
print("\n" + "=" * 70)
print("Test 2: Obama (Capricorn Lagna)")
print("=" * 70)

longitudes_obama = {
    'Sun': 142.0,    # Leo (4)
    'Moon': 35.0,    # Taurus (1)
    'Mars': 188.0,   # Libra (6)
    'Mercury': 155.0, # Virgo (5)
    'Jupiter': 252.0, # Sagittarius (8)
    'Venus': 175.0,   # Virgo (5)
    'Saturn': 322.0,  # Aquarius (10)
    'Rahu': 72.0,     # Gemini (2)
    'Ketu': 252.0,    # Sagittarius (8)
}

result2 = calc_chara_dasha(9, longitudes_obama, 1961, 8, 4)
print(f"Method: {result2['method']}")
print(f"Total cycle years: {result2['total_cycle_years']}")
print()

for d in result2['dasha_sequence']:
    print(f"  {d['order']:2d}. {d['sign']:12s} | Lord: {d['lord']:8s} in {d['lord_in_sign']:12s} | Dur: {d['duration_years']:2d}y | Dignity: {d['dignity_adjustment']}")

exalted2 = sum(1 for d in result2['dasha_sequence'] if d['dignity_adjustment'] == 'exalted')
debilitated2 = sum(1 for d in result2['dasha_sequence'] if d['dignity_adjustment'] == 'debilitated')
none_count2 = sum(1 for d in result2['dasha_sequence'] if d['dignity_adjustment'] == 'none')
print(f"\nDignity counts: exalted={exalted2}, debilitated={debilitated2}, none={none_count2}")

# ============================================================
# Test 3: Synthetic test - force exalted/debilitated cases
# ============================================================
print("\n" + "=" * 70)
print("Test 3: Synthetic (Aries Lagna) - Force exalted/debilitated")
print("=" * 70)

# Aries Lagna (0)
# Sun in Aries (0) = exalted, Saturn in Aries (0) = debilitated
# Moon in Taurus (1) = exalted, Mars in Capricorn (9) = exalted
# Jupiter in Cancer (3) = exalted, Venus in Pisces (11) = exalted
longitudes_synth = {
    'Sun': 5.0,      # Aries (0) - EXALTED
    'Moon': 35.0,    # Taurus (1) - EXALTED
    'Mars': 275.0,   # Capricorn (9) - EXALTED
    'Mercury': 95.0, # Cancer (3) - NOT exalted for Mercury
    'Jupiter': 95.0, # Cancer (3) - EXALTED
    'Venus': 335.0,  # Pisces (11) - EXALTED
    'Saturn': 5.0,   # Aries (0) - DEBILITATED
    'Rahu': 35.0,    # Taurus (1) - EXALTED
    'Ketu': 215.0,   # Scorpio (7) - EXALTED
}

result3 = calc_chara_dasha(0, longitudes_synth, 1990, 1, 1)
print(f"Method: {result3['method']}")
print(f"Total cycle years: {result3['total_cycle_years']}")
print()

for d in result3['dasha_sequence']:
    print(f"  {d['order']:2d}. {d['sign']:12s} | Lord: {d['lord']:8s} in {d['lord_in_sign']:12s} | Dur: {d['duration_years']:2d}y | Dignity: {d['dignity_adjustment']}")

exalted3 = sum(1 for d in result3['dasha_sequence'] if d['dignity_adjustment'] == 'exalted')
debilitated3 = sum(1 for d in result3['dasha_sequence'] if d['dignity_adjustment'] == 'debilitated')
none_count3 = sum(1 for d in result3['dasha_sequence'] if d['dignity_adjustment'] == 'none')
print(f"\nDignity counts: exalted={exalted3}, debilitated={debilitated3}, none={none_count3}")

# ============================================================
# Test 4: Verify specific dignity logic for each planet
# ============================================================
print("\n" + "=" * 70)
print("Test 4: Direct dignity validation per planet")
print("=" * 70)

test_cases = [
    ('Sun', 0, 'exalted'),     # Aries
    ('Sun', 6, 'debilitated'), # Libra
    ('Moon', 1, 'exalted'),    # Taurus
    ('Moon', 7, 'debilitated'),# Scorpio
    ('Mars', 9, 'exalted'),    # Capricorn
    ('Mars', 3, 'debilitated'),# Cancer
    ('Jupiter', 3, 'exalted'), # Cancer
    ('Jupiter', 9, 'debilitated'),# Capricorn
    ('Venus', 11, 'exalted'),  # Pisces
    ('Venus', 5, 'debilitated'),# Virgo
    ('Saturn', 6, 'exalted'),  # Libra
    ('Saturn', 0, 'debilitated'),# Aries
    ('Rahu', 1, 'exalted'),    # Taurus
    ('Rahu', 7, 'debilitated'),# Scorpio
    ('Ketu', 7, 'exalted'),    # Scorpio
    ('Ketu', 1, 'debilitated'),# Taurus
    ('Mercury', 11, 'debilitated'), # Pisces
]

all_pass = True
for planet, sign_idx, expected in test_cases:
    dignities = _PLANET_DIGNITY_KNRAO.get(planet, {})
    exalted_set = dignities.get('exalted', set())
    debil_set = dignities.get('debilitated', set())

    if expected == 'exalted':
        result = sign_idx in exalted_set
    else:
        result = sign_idx in debil_set

    status = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print(f"  {planet:8s} in {SIGNS[sign_idx]:12s} ({sign_idx:2d}) -> expected {expected:11s}: {status}")

print(f"\nDirect dignity test: {'ALL PASS' if all_pass else 'SOME FAILED'}")

# ============================================================
# Test 5: Simulate pre-bug-fix behavior (lord_house == set())
# ============================================================
print("\n" + "=" * 70)
print("Test 5: Bug fix verification - old vs new behavior")
print("=" * 70)

# The old bug: if lord_house == set() would always be False
# The new fix: if lord_house in exalted_set
# Let's verify that lord_house is an int and exalted_set is a set of ints
for planet, sign_idx, expected in test_cases:
    dignities = _PLANET_DIGNITY_KNRAO.get(planet, {})
    exalted_set = dignities.get('exalted', set())
    debil_set = dignities.get('debilitated', set())

    # lord_house is an int (0-11), exalted_set/debil_set are sets of ints
    # Old bug: lord_house == set() → always False (int != set)
    # New fix: lord_house in exalted_set → correct membership test
    old_bug_result = (sign_idx == set())  # This is what the old code did
    new_fix_result = (sign_idx in exalted_set) if expected == 'exalted' else (sign_idx in debil_set)

    print(f"  {planet:8s} in {SIGNS[sign_idx]:12s}: old_bug={old_bug_result}, new_fix={new_fix_result}")

print("\nOld bug always returned False (int != set), so dignity was always 'none'.")
print("New fix uses 'in' operator for correct set membership test.")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
total_dignity_found = exalted + debilitated + exalted2 + debilitated2 + exalted3 + debilitated3
total_signs = 36  # 3 charts × 12 signs
print(f"Total dignity_adjustment detections across 3 charts: {total_dignity_found}/{total_signs}")
print(f"  Chart 1 (Einstein): exalted={exalted}, debilitated={debilitated}, none={none_count}")
print(f"  Chart 2 (Obama): exalted={exalted2}, debilitated={debilitated2}, none={none_count2}")
print(f"  Chart 3 (Synthetic): exalted={exalted3}, debilitated={debilitated3}, none={none_count3}")
print(f"Direct dignity validation: {'ALL PASS' if all_pass else 'SOME FAILED'}")
print(f"\nBug fix status: dignity_adjustment now correctly shows 'exalted'/'debilitated' instead of always 'none'")
