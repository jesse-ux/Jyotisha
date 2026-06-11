#!/usr/bin/env python3
"""
Chara Dasha KN Rao Benchmark v1.1
比较 v6.1.11 yinduzhanxing Chara Dasha 与 PyJHora KN Rao method。

策略：用 PyJHora 计算行星位置作为共享输入，两个实现基于相同数据运行。
这样隔离算法差异，消除天文计算差异。

依赖: pip install jhora numpy
"""
import sys, json, os

# 添加scripts路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))
from jaimini import SIGNS, _chara_dasha_duration_knrao, _chara_progression_knrao, _EVEN_FOOTED_SIGNS

# PyJHora
from jhora.horoscope.dhasa.raasi import chara as pj_chara
from jhora.horoscope.chart import charts
from jhora.panchanga import drik
from jhora import const, utils

# ─────────────────────────────────────────────
# 10个测试案例（与Round 7相同）
# ─────────────────────────────────────────────
TEST_CASES = [
    {"id": "smoke_beijing_1990_noon",     "year":1990, "month":6, "day":15, "hour":12, "minute":0, "lat":39.9,  "lon":116.4, "tz":8},
    {"id": "smoke_newyork_1985_morning",  "year":1985, "month":3, "day":22, "hour":9,  "minute":30, "lat":40.7,  "lon":-74.0, "tz":-5},
    {"id": "smoke_london_1970_evening",   "year":1970, "month":9, "day":12, "hour":19, "minute":0,  "lat":51.5,  "lon":-0.1,  "tz":0},
    {"id": "smoke_delhi_2000_midnight",   "year":2000, "month":1, "day":1,  "hour":0,  "minute":0,  "lat":28.6,  "lon":77.2,  "tz":5.5},
    {"id": "smoke_sydney_1999_afternoon", "year":1999, "month":8, "day":7,  "hour":15, "minute":45, "lat":-33.9, "lon":151.2, "tz":10},
    {"id": "smoke_tokyo_1964_noon",       "year":1964, "month":10, "day":10,"hour":12, "minute":0,  "lat":35.7,  "lon":139.7, "tz":9},
    {"id": "smoke_cairo_1952_dawn",       "year":1952, "month":7, "day":23, "hour":6,  "minute":0,  "lat":30.0,  "lon":31.2,  "tz":2},
    {"id": "smoke_paris_1989_noon",       "year":1989, "month":11,"day":9,  "hour":12, "minute":30, "lat":48.9,  "lon":2.3,   "tz":1},
    {"id": "smoke_losangeles_1995_night", "year":1995, "month":2, "day":14, "hour":22, "minute":15, "lat":34.1,  "lon":-118.2,"tz":-8},
    {"id": "smoke_sao_paulo_2004_morning","year":2004, "month":12,"day":25, "hour":7,  "minute":0,  "lat":-23.5, "lon":-46.6, "tz":-3},
]

# 行星名称到PyJHora ID
PLANET_NAMES = {
    const.SUN_ID: "Sun", const.MOON_ID: "Moon", const.MARS_ID: "Mars",
    const.MERCURY_ID: "Mercury", const.JUPITER_ID: "Jupiter", const.VENUS_ID: "Venus",
    const.SATURN_ID: "Saturn", const.RAHU_ID: "Rahu", const.KETU_ID: "Ketu",
}


def run_benchmark():
    total_sign = 0; sign_match = 0
    total_dur = 0; dur_match = 0
    detail_lines = []
    sample_details = []

    for case in TEST_CASES:
        # 1. 用 PyJHora 获取行星位置
        dob = drik.Date(case["year"], case["month"], case["day"])
        tob = (case["hour"], case["minute"], 0)
        place = drik.Place(f'test_{case["id"]}', case["lat"], case["lon"], case["tz"])
        jd = utils.julian_day_number(dob, tob)
        pp = charts.divisional_chart(jd, place, divisional_chart_factor=1)[:const._pp_count_upto_ketu]

        asc_house = pp[0][1][0]  # 0-indexed ascendant sign (pp[0] = Lagna)
        
        # 2. 构建共享的行星经度字典（供我们的代码使用）
        # 注意: pp[0]=Lagna, pp[1]=Sun, pp[2]=Moon, ... 即 pp[planet_id+1]=planet
        planet_longitudes = {}
        for planet_id, pname in PLANET_NAMES.items():
            sign = pp[planet_id + 1][1][0]
            deg = pp[planet_id + 1][1][1]
            planet_longitudes[pname] = sign * 30 + deg

        # 3. 我们的 KN Rao 实现
        our_progression = _chara_progression_knrao(asc_house, planet_longitudes)
        our_durations = [_chara_dasha_duration_knrao(planet_longitudes, s) for s in our_progression]

        # 4. PyJHora KN Rao 实现（oracle）
        pj_progression = pj_chara._dhasa_progression_knrao_method(pp)
        pj_durations = [pj_chara._dhasa_duration_knrao_method(pp, s) for s in pj_progression]

        # 5. 比较
        case_sign_match = 0; case_dur_match = 0
        mismatches = []
        for i in range(12):
            our_s = our_progression[i]
            pj_s = pj_progression[i]
            our_d = our_durations[i]
            pj_d = pj_durations[i]

            if our_s == pj_s:
                case_sign_match += 1
            else:
                mismatches.append(f"sign[{i}]: us={SIGNS[our_s]}, pj={SIGNS[pj_s]}")
            if our_d == pj_d:
                case_dur_match += 1
            else:
                mismatches.append(f"dur[{i}]: us={our_d}, pj={pj_d}")

        total_sign += 12; sign_match += case_sign_match
        total_dur += 12; dur_match += case_dur_match

        our_first3 = ",".join(SIGNS[s] for s in our_progression[:3])
        pj_first3 = ",".join(SIGNS[s] for s in pj_progression[:3])
        line = f"  {case['id']:35s} | sign {case_sign_match:2d}/12 | dur {case_dur_match:2d}/12"
        detail_lines.append(line)
        
        sample_details.append({
            "case": case['id'],
            "asc": SIGNS[asc_house],
            "our_first_3": our_first3,
            "pj_first_3": pj_first3,
            "sign_match": f"{case_sign_match}/12",
            "dur_match": f"{case_dur_match}/12",
            "mismatches": mismatches[:5]  # 最多5个不匹配项
        })

    # ── 输出 ──
    print("=" * 80)
    print("Chara Dasha KN Rao Benchmark v1.1")
    print(f"Skill: v6.1.11 (共享PyJHora行星位置)")
    print("=" * 80)
    
    print(f"\n{'Case':40s} | Sign Match | Dur Match | Us first3 vs PJ first3")
    print("-" * 80)
    for i, s in enumerate(sample_details):
        line = f"  {s['case']:35s} | {s['sign_match']:>10s} | {s['dur_match']:>9s} | {s['our_first_3']} | {s['pj_first_3']}"
        print(line)
    print("-" * 80)

    total_all = total_sign + total_dur
    match_all = sign_match + dur_match
    print(f"\nSign  Sequence Match: {sign_match}/{total_sign} = {sign_match/total_sign*100:.2f}%")
    print(f"Duration Match:       {dur_match}/{total_dur} = {dur_match/total_dur*100:.2f}%")
    print(f"Overall Match:        {match_all}/{total_all} = {match_all/total_all*100:.2f}%")

    if match_all / total_all >= 0.95:
        status = "✅ PASS ✓"
    elif match_all / total_all >= 0.85:
        status = "⚠️ BORDERLINE"
    else:
        status = "❌ FAIL"
    print(f"\nBenchmark Result: {status}")

    # 放生不匹配
    if status != "✅ PASS ✓":
        print("\n--- 不匹配详情 ---")
        for s in sample_details:
            if s["mismatches"]:
                print(f"\n{s['case']}:")
                for m in s["mismatches"]:
                    print(f"  {m}")

    # 保存 JSON
    out = os.path.join(os.path.dirname(__file__), "..", "outputs", "chara_dasha_knrao_benchmark.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    result = {
        "version": "v6.1.11",
        "benchmark": "chara_dasha_kn_rao",
        "total_sign_match": sign_match,
        "total_dur_match": dur_match,
        "total_sign": total_sign,
        "total_dur": total_dur,
        "sign_match_rate": round(sign_match/total_sign, 4) if total_sign else 0,
        "dur_match_rate": round(dur_match/total_dur, 4) if total_dur else 0,
        "status": status,
        "samples": sample_details,
    }
    with open(out, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    run_benchmark()
