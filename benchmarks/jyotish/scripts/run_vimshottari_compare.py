#!/usr/bin/env python3
"""
Vimshottari Dasha Benchmark v1.1
比较 v6.1.13 yinduzhanxing Vimshottari Dasha 与 PyJHora 实现。

算法来源：基于jyotishganit (MIT License) 核心算法。
使用恒星年 = 365.25636天。

对比字段：
- MD主星（前3个）、MD起始/结束日期
- AD主星（第1个MD的前3个AD）、AD起始日期

依赖: pip install jhora numpy
"""
import sys, json, os
from datetime import datetime, timedelta

# 添加scripts路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))
from dasha_calculator_enhanced import (
    calculate_dasha_dates, calculate_dasha_start_date,
    DASHA_ORDER, VIMSHOTTARI_PERIODS, HUMAN_LIFE_SPAN_VIMSHOTTARI,
    YEAR_DURATION_DAYS
)

# PyJHora
from jhora.horoscope.dhasa.graha import vimsottari as pj_vimshottari
from jhora.panchanga import drik
from jhora import utils, const
from jhora.horoscope.chart import charts

# ─────────────────────────────────────────────
# 10个测试案例
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

# PyJHora行星ID -> 名称
PLANET_ID_TO_NAME = {0: 'Ketu', 1: 'Venus', 2: 'Sun', 3: 'Moon',
                     4: 'Mars', 5: 'Rahu', 6: 'Jupiter', 7: 'Saturn', 8: 'Mercury'}


def jd_to_datetime(jd):
    """Julian day -> datetime"""
    unix_epoch_jd = 2440587.5
    seconds_since_epoch = (jd - unix_epoch_jd) * 86400
    return datetime(1970, 1, 1) + timedelta(seconds=seconds_since_epoch)


def run_benchmark():
    total_fields = 0
    match_fields = 0
    detail_lines = []
    sample_details = []

    for case in TEST_CASES:
        # 1. 准备PyJHora数据
        dob = drik.Date(case["year"], case["month"], case["day"])
        tob = (case["hour"], case["minute"], 0)
        place = drik.Place(f'test_{case["id"]}', case["lat"], case["lon"], case["tz"])
        jd = utils.julian_day_number(dob, tob)

        birth_date = datetime(case["year"], case["month"], case["day"],
                             case["hour"], case["minute"])

        # 2. 获取Moon经度（来自PyJHora）
        pp = charts.divisional_chart(jd, place, divisional_chart_factor=1)[:const._pp_count_upto_ketu]
        moon_sign = pp[const.MOON_ID + 1][1][0]
        moon_deg = pp[const.MOON_ID + 1][1][1]
        moon_degree = moon_sign * 30 + moon_deg

        # 3. 我们的Vimshottari计算
        our_md_list = calculate_dasha_dates(birth_date, moon_degree)

        # 4. PyJHora Vimshottari MD
        pj_md_dict = pj_vimshottari.vimsottari_mahadasa(jd, place, divisional_chart_factor=1)
        pj_md_ordered = list(pj_md_dict.items())[:3]

        case_match = 0
        case_total = 0
        mismatches = []

        # 比较MD（前3个）- lord + start date
        for i in range(min(3, len(our_md_list), len(pj_md_ordered))):
            our_md = our_md_list[i]
            pj_lord_id, pj_start_jd = pj_md_ordered[i]

            # MD lord
            case_total += 1
            our_lord = our_md['lord']
            pj_lord = PLANET_ID_TO_NAME.get(pj_lord_id, str(pj_lord_id))
            if our_lord == pj_lord:
                case_match += 1
            else:
                mismatches.append(f"MD[{i}] lord: us={our_lord}, pj={pj_lord}")

            # MD start date（比较MD起始时间）
            case_total += 1
            our_start = our_md['start_date']
            pj_start = jd_to_datetime(pj_start_jd)
            diff_days = abs((our_start - pj_start).days)
            if diff_days <= 90:  # 3个月容差（由于恒星年 vs 回归年等差异）
                case_match += 1
            else:
                mismatches.append(f"MD[{i}] start: us={our_start.strftime('%Y-%m-%d')}, pj={pj_start.strftime('%Y-%m-%d')} (diff={diff_days}d)")

        # 比较AD（第1个MD的前3个AD）
        if len(our_md_list) > 0 and len(pj_md_ordered) > 0:
            our_first_md = our_md_list[0]
            our_md_total_days = our_first_md['years'] * YEAR_DURATION_DAYS

            pj_first_lord_id, pj_first_start_jd = pj_md_ordered[0]
            pj_ad_dict = pj_vimshottari._vimsottari_bhukti(pj_first_lord_id, pj_first_start_jd)
            pj_ad_ordered = list(pj_ad_dict.items())[:3]

            for j in range(min(3, len(pj_ad_ordered))):
                pj_ad_lord_id, pj_ad_start_jd = pj_ad_ordered[j]

                # AD lord
                case_total += 1
                pj_ad_lord = PLANET_ID_TO_NAME.get(pj_ad_lord_id, str(pj_ad_lord_id))

                # 我们的AD lord按Vimshottari顺序
                our_first_lord = our_first_md['lord']
                first_idx = DASHA_ORDER.index(our_first_lord)
                ad_idx = (first_idx + j) % 9
                our_ad_lord = DASHA_ORDER[ad_idx]

                if our_ad_lord == pj_ad_lord:
                    case_match += 1
                else:
                    mismatches.append(f"AD[0,{j}] lord: us={our_ad_lord}, pj={pj_ad_lord}")

                # AD start date
                case_total += 1
                pj_ad_start = jd_to_datetime(pj_ad_start_jd)

                # 我们的AD start - 基于比例公式
                our_ad_start = our_first_md['start_date']
                for k in range(j):
                    ad_lord_dur = VIMSHOTTARI_PERIODS[DASHA_ORDER[(first_idx + k) % 9]]
                    ad_days = our_md_total_days * (ad_lord_dur / HUMAN_LIFE_SPAN_VIMSHOTTARI)
                    our_ad_start += timedelta(days=ad_days)

                diff_days = abs((our_ad_start - pj_ad_start).days)
                if diff_days <= 90:
                    case_match += 1
                else:
                    mismatches.append(f"AD[0,{j}] start: us={our_ad_start.strftime('%Y-%m-%d')}, pj={pj_ad_start.strftime('%Y-%m-%d')} (diff={diff_days}d)")

        total_fields += case_total
        match_fields += case_match

        sample_details.append({
            'case': case['id'],
            'match': f"{case_match}/{case_total}",
            'mismatches': mismatches[:5],
        })

    # ── 输出 ──
    print("=" * 80)
    print("Vimshottari Dasha Benchmark v1.1")
    print(f"Skill: v6.1.13 (基于jyotishganit MIT算法 + 恒星年={YEAR_DURATION_DAYS:.5f})")
    print("=" * 80)

    print(f"\n{'Case':40s} | Match")
    print("-" * 80)
    for d in sample_details:
        print(f"  {d['case']:35s} | {d['match']:>10s}")
    print("-" * 80)

    rate = match_fields / total_fields * 100 if total_fields else 0
    print(f"\nTotal Match: {match_fields}/{total_fields} = {rate:.2f}%")

    if rate >= 95:
        status = "✅ PASS ✓"
    elif rate >= 85:
        status = "⚠️ BORDERLINE"
    else:
        status = "❌ FAIL"
    print(f"\nBenchmark Result: {status}")

    if status != "✅ PASS ✓":
        print("\n--- 不匹配详情 ---")
        for d in sample_details:
            if d["mismatches"]:
                print(f"\n{d['case']}:")
                for m in d["mismatches"][:3]:
                    print(f"  {m}")

    # 保存 JSON
    out = os.path.join(os.path.dirname(__file__), "..", "outputs", "vimshottari_benchmark.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    result = {
        "version": "v6.1.13",
        "benchmark": "vimshottari_dasha",
        "total_match": match_fields,
        "total_fields": total_fields,
        "match_rate": round(rate / 100, 4) if total_fields else 0,
        "status": status,
        "samples": sample_details,
    }
    with open(out, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    run_benchmark()
