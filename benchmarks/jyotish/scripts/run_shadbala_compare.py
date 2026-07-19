#!/usr/bin/env python3
"""
Shadbala Benchmark v1.0
比较 v6.1.13 yinduzhanxing Shadbala 与 PyJHora 实现。

依赖: pip install jhora numpy
"""
import sys, json, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))
from shadbala import calc_shadbala, NAISARGIKA_BALA

# PyJHora
from jhora import const, utils
from jhora.panchanga import drik
from jhora.horoscope.chart import charts
from jhora.horoscope.chart import strength as pj_strength

TEST_CASES = [
    {"id": "beijing_1990_noon",     "year":1990, "month":6, "day":15, "hour":12, "minute":0, "lat":39.9,  "lon":116.4, "tz":8},
    {"id": "newyork_1985_morning",  "year":1985, "month":3, "day":22, "hour":9,  "minute":30, "lat":40.7,  "lon":-74.0, "tz":-5},
    {"id": "london_1970_evening",   "year":1970, "month":9, "day":12, "hour":19, "minute":0,  "lat":51.5,  "lon":-0.1,  "tz":0},
    {"id": "delhi_2000_midnight",   "year":2000, "month":1, "day":1,  "hour":0,  "minute":0,  "lat":28.6,  "lon":77.2,  "tz":5.5},
    {"id": "sydney_1999_afternoon", "year":1999, "month":8, "day":7,  "hour":15, "minute":45, "lat":-33.9, "lon":151.2, "tz":10},
]

PLANET_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']


def run_benchmark():
    total_planets = 0
    within_10pct = 0
    within_20pct = 0
    details = []

    for case in TEST_CASES:
        dob = drik.Date(case["year"], case["month"], case["day"])
        tob = (case["hour"], case["minute"], 0)
        place = drik.Place(f'test_{case["id"]}', case["lat"], case["lon"], case["tz"])
        jd = utils.julian_day_number(dob, tob)
        pp = charts.divisional_chart(jd, place, divisional_chart_factor=1)[:const._pp_count_upto_ketu]

        # 提取行星位置
        asc_sign_idx = pp[0][1][0]
        sun_sign = pp[const.SUN_ID + 1][1][0]
        moon_sign = pp[const.MOON_ID + 1][1][1]
        sun_lon = sun_sign * 30 + pp[const.SUN_ID + 1][1][1]
        moon_lon = moon_sign

        planets = {}
        for pid, pname in {const.SUN_ID: 'Sun', const.MOON_ID: 'Moon',
                           const.MARS_ID: 'Mars', const.MERCURY_ID: 'Mercury',
                           const.JUPITER_ID: 'Jupiter', const.VENUS_ID: 'Venus',
                           const.SATURN_ID: 'Saturn'}.items():
            sign = pp[pid + 1][1][0]
            deg = pp[pid + 1][1][1]
            house = (sign - asc_sign_idx) % 12 + 1
            retro = pp[pid + 1][4] if len(pp[pid + 1]) > 4 else False
            speed = pp[pid + 1][3] if len(pp[pid + 1]) > 3 else 1.0
            planets[pname] = {
                'sign': SIGNS[sign],
                'degree': sign * 30 + deg,
                'house': house,
                'retrograde': retro,
                'speed': speed,
            }

        # 我们的Shadbala
        our = calc_shadbala(planets, SIGNS[asc_sign_idx],
                           case["hour"] + case["minute"] / 60,
                           sun_lon, moon_lon, case["minute"])

        # PyJHora Shadbala
        try:
            pj_total_rupas = pj_strength.shad_bala(jd, place)[7]
        except:
            print(f"  PyJHora shadbala failed for {case['id']}")
            continue

        case_match = 0
        case_total = 0
        case_details = []

        for pname in PLANET_NAMES:
            if pname not in planets or pname not in our['planets']:
                continue

            our_rupas = our['planets'][pname]['total_rupas']
            pj_rupas = pj_total_rupas[PLANET_NAMES.index(pname)]

            total_planets += 1
            if pj_rupas > 0:
                diff_pct = abs(our_rupas - pj_rupas) / pj_rupas * 100
                if diff_pct <= 10:
                    within_10pct += 1
                if diff_pct <= 20:
                    within_20pct += 1
                case_details.append(f"{pname}: us={our_rupas:.2f}, pj={pj_rupas:.2f} ({diff_pct:.1f}%)")

        details.append({
            'case': case['id'],
            'planets': case_details,
        })

    print("=" * 80)
    print("Shadbala Benchmark v1.0")
    print(f"Total planets: {total_planets}")
    print("=" * 80)
    print(f"Within 10% of PyJHora: {within_10pct}/{total_planets} = {within_10pct/total_planets*100:.1f}%" if total_planets else "N/A")
    print(f"Within 20% of PyJHora: {within_20pct}/{total_planets} = {within_20pct/total_planets*100:.1f}%" if total_planets else "N/A")

    for d in details:
        print(f"\n{d['case']}:")
        for pd in d['planets']:
            print(f"  {pd}")

    if within_20pct / total_planets >= 0.8 if total_planets else False:
        print("\n✅ PASS (≥80% within 20%)")
    else:
        print("\n⚠️ NEEDS IMPROVEMENT")

if __name__ == "__main__":
    run_benchmark()
