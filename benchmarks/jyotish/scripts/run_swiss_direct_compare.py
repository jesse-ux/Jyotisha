# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import csv
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
SWISS_OUT = OUT / 'swiss_direct'
CANON = OUT / 'canonical'

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN,
    'Rahu': swe.MEAN_NODE,
}
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
NAKSHATRAS = [
    'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
    'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
]


def normalize(deg):
    return deg % 360.0


def sign_of(lon):
    idx = int(normalize(lon) // 30)
    return SIGNS[idx]


def degree_in_sign(lon):
    return normalize(lon) % 30


def nakshatra_of(lon):
    unit = 360.0 / 27.0
    pos = normalize(lon) / unit
    idx = int(math.floor(pos))
    pada = int(math.floor((pos - idx) * 4)) + 1
    if pada > 4:
        pada = 4
    return NAKSHATRAS[idx], pada


def julian_day_utc(birth):
    tz = float(birth['tz'])
    local = datetime(int(birth['year']), int(birth['month']), int(birth['day']), int(birth['hour']), int(birth['minute']))
    utc_dt = local - timedelta(hours=tz)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def calc_swiss(sample):
    birth = sample['birth']
    jd = julian_day_utc(birth)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planets = {}
    for name, pid in PLANETS.items():
        res, ret = swe.calc_ut(jd, pid, flags)
        lon = normalize(res[0])
        nak, pada = nakshatra_of(lon)
        planets[name] = {
            'longitude': round(lon, 6),
            'sign': sign_of(lon),
            'degree_in_sign': round(degree_in_sign(lon), 6),
            'nakshatra': nak,
            'nakshatra_pada': pada,
            'retrograde': bool(res[3] < 0),
        }
    rahu_lon = planets['Rahu']['longitude']
    ketu_lon = normalize(rahu_lon + 180)
    nak, pada = nakshatra_of(ketu_lon)
    planets['Ketu'] = {
        'longitude': round(ketu_lon, 6),
        'sign': sign_of(ketu_lon),
        'degree_in_sign': round(degree_in_sign(ketu_lon), 6),
        'nakshatra': nak,
        'nakshatra_pada': pada,
        'retrograde': planets['Rahu']['retrograde'],
    }
    return {
        'sample_id': sample['id'],
        'engine': 'swiss_direct_lahiri_mean_node',
        'julian_day_ut': jd,
        'parameters': {'ayanamsa': 'Lahiri', 'node': 'Mean Node', 'flags': int(flags)},
        'planets': planets,
    }


def compare_sample(sample_id, swiss):
    local_path = CANON / f'{sample_id}.canonical.json'
    local = json.loads(local_path.read_text())
    rows = []
    for pname in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
        s = swiss['planets'][pname]
        l = local['planets'][pname]
        for field in ['sign','degree_in_sign','nakshatra','nakshatra_pada','retrograde']:
            sv = s.get(field)
            lv = l.get(field)
            status = 'match'
            delta = ''
            if field == 'degree_in_sign':
                try:
                    delta_val = abs(float(sv) - float(lv))
                    delta = round(delta_val, 6)
                    status = 'match' if delta_val <= 0.1 else 'mismatch'
                except Exception:
                    status = 'not_comparable'
            else:
                status = 'match' if sv == lv else 'mismatch'
            rows.append({
                'sample_id': sample_id,
                'body': pname,
                'field': field,
                'local_skill': lv,
                'swiss_direct': sv,
                'delta': delta,
                'status': status,
            })
    return rows


def write_report(rows):
    total = len(rows)
    matches = sum(1 for r in rows if r['status'] == 'match')
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    by_field = {}
    for r in rows:
        by_field.setdefault(r['field'], {'total':0, 'match':0, 'mismatch':0})
        by_field[r['field']]['total'] += 1
        by_field[r['field']][r['status']] = by_field[r['field']].get(r['status'], 0) + 1
    lines = []
    lines.append('# Jyotish benchmark 第一轮 Swiss direct 对比报告')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 范围')
    lines.append('')
    lines.append('- 对比对象：当前 skill canonical baseline vs 直接调用 Swiss Ephemeris。')
    lines.append('- 配置：Sidereal Lahiri，Mean Node，行星黄经与 Nakshatra 字段。')
    lines.append('- 本轮不比较上升、宫位、D9/D10、大运；这些留给下一轮多引擎/参数冻结测试。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append(f'- 字段总数：{total}')
    lines.append(f'- 匹配：{matches}')
    lines.append(f'- 不匹配：{len(mismatches)}')
    lines.append(f'- 匹配率：{matches / total:.2%}' if total else '- 匹配率：N/A')
    lines.append('')
    lines.append('## 3. 分字段结果')
    lines.append('')
    lines.append('| Field | Total | Match | Mismatch |')
    lines.append('|---|---:|---:|---:|')
    for field, stat in sorted(by_field.items()):
        lines.append(f"| {field} | {stat['total']} | {stat.get('match',0)} | {stat.get('mismatch',0)} |")
    lines.append('')
    if mismatches:
        lines.append('## 4. 不匹配样例')
        lines.append('')
        lines.append('| Sample | Body | Field | Local skill | Swiss direct | Delta |')
        lines.append('|---|---|---|---|---|---:|')
        for r in mismatches[:80]:
            lines.append(f"| {r['sample_id']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['swiss_direct']} | {r['delta']} |")
        lines.append('')
    lines.append('## 5. 解释')
    lines.append('')
    lines.append('- 若 sign/nakshatra 大量一致，说明当前 skill 的核心 Lahiri 行星计算大方向可信。')
    lines.append('- 若 degree_in_sign 出现系统性差异，优先检查 ayanamsa、True/Mean Node、UTC换算、Swiss flags。')
    lines.append('- 本轮发现的问题只约束计算层，不直接评价解释和预测能力。')
    report = OUT / 'jyotish_benchmark_round1_swiss_direct_compare.md'
    report.write_text('\n'.join(lines))
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SWISS_OUT.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    all_rows = []
    for sample in samples:
        swiss = calc_swiss(sample)
        (SWISS_OUT / f"{sample['id']}.swiss_direct.json").write_text(json.dumps(swiss, ensure_ascii=False, indent=2))
        all_rows.extend(compare_sample(sample['id'], swiss))
    csv_path = OUT / 'swiss_direct_comparison_matrix.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id','body','field','local_skill','swiss_direct','delta','status'])
        writer.writeheader()
        writer.writerows(all_rows)
    report = write_report(all_rows)
    print(json.dumps({'matrix': str(csv_path), 'report': str(report), 'rows': len(all_rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
