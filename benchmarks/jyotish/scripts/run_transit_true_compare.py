# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'jyotish_engine.py'
PYTHON = Path(sys.executable)
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
RAW = OUT / 'raw'
TRANSIT_OUT = OUT / 'transit_true'

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


def normalize(deg):
    return deg % 360.0


def sign_of(lon):
    return SIGNS[int(normalize(lon) // 30)]


def degree_in_sign(lon):
    return normalize(lon) % 30


def julian_day_for_transit(date_str, tz):
    y, m, d = map(int, date_str.split('-'))
    local = datetime(y, m, d, 12, 0)
    utc_dt = local - timedelta(hours=float(tz))
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def calc_swiss_transit(date_str, tz):
    jd = julian_day_for_transit(date_str, tz)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planets = {}
    for name, pid in PLANETS.items():
        res, ret = swe.calc_ut(jd, pid, flags)
        lon = normalize(res[0])
        planets[name] = {
            'longitude': round(lon, 6),
            'sign': sign_of(lon),
            'degree_in_sign': round(degree_in_sign(lon), 6),
            'retrograde': bool(res[3] < 0),
        }
    rahu_lon = planets['Rahu']['longitude']
    ketu_lon = normalize(rahu_lon + 180)
    planets['Ketu'] = {
        'longitude': round(ketu_lon, 6),
        'sign': sign_of(ketu_lon),
        'degree_in_sign': round(degree_in_sign(ketu_lon), 6),
        'retrograde': planets['Rahu']['retrograde'],
    }
    return {'julian_day_ut': jd, 'planets': planets, 'parameters': {'ayanamsa': 'Lahiri', 'node': 'Mean Node'}}


def run_full_reading(sample):
    birth = sample['birth']
    transit_date = sample.get('today', '2026-06-03')
    cmd = [
        str(PYTHON), str(SKILL_SCRIPT), 'full-reading',
        '--year', str(birth['year']),
        '--month', str(birth['month']),
        '--day', str(birth['day']),
        '--hour', str(birth['hour']),
        '--minute', str(birth['minute']),
        '--lat', str(birth['lat']),
        '--lon', str(birth['lon']),
        '--tz', str(birth['tz']),
        '--today', transit_date,
        '--transit-date', transit_date,
        '--node-mode', 'mean',
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    raw_path = RAW / f"{sample['id']}.transit_full_reading.json"
    if proc.returncode != 0:
        raw_path.write_text(json.dumps({'cmd': cmd, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}, ensure_ascii=False, indent=2))
        raise RuntimeError(proc.stderr[:500])
    data = json.loads(proc.stdout)
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def compare_sample(sample):
    transit_date = sample.get('today', '2026-06-03')
    data = run_full_reading(sample)
    modules = data.get('modules', {})
    local_transit = modules.get('transit_positions', {})
    local_multi = modules.get('transit_multi_reference', {})
    swiss = calc_swiss_transit(transit_date, sample['birth']['tz'])
    (TRANSIT_OUT / f"{sample['id']}.swiss_transit.json").write_text(json.dumps(swiss, ensure_ascii=False, indent=2))

    rows = []
    rows.append({
        'sample_id': sample['id'],
        'body': 'module',
        'field': 'transit_positions.data_layer',
        'local_skill': local_transit.get('data_layer'),
        'swiss_direct': 'true_transit_positions',
        'delta': '',
        'status': 'match' if local_transit.get('data_layer') == 'true_transit_positions' else 'mismatch',
    })
    rows.append({
        'sample_id': sample['id'],
        'body': 'module',
        'field': 'transit_multi_reference.data_layer',
        'local_skill': local_multi.get('data_layer'),
        'swiss_direct': 'true_transit_positions',
        'delta': '',
        'status': 'match' if local_multi.get('data_layer') == 'true_transit_positions' else 'mismatch',
    })
    rows.append({
        'sample_id': sample['id'],
        'body': 'module',
        'field': 'transit_multi_reference.target_date',
        'local_skill': local_multi.get('target_date'),
        'swiss_direct': transit_date,
        'delta': '',
        'status': 'match' if local_multi.get('target_date') == transit_date else 'mismatch',
    })

    local_planets = local_transit.get('planets', {})
    multi_analysis = local_multi.get('transit_analysis', {})
    for pname in ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
        s = swiss['planets'][pname]
        l = local_planets.get(pname, {})
        for field in ['sign','degree_in_sign','retrograde']:
            sv = s.get(field)
            lv = l.get(field)
            delta = ''
            if field == 'degree_in_sign':
                try:
                    delta_val = abs(float(sv) - float(lv))
                    delta = round(delta_val, 6)
                    status = 'match' if delta_val <= 0.01 else 'mismatch'
                except Exception:
                    status = 'not_comparable'
            else:
                status = 'match' if sv == lv else 'mismatch'
            rows.append({
                'sample_id': sample['id'],
                'body': pname,
                'field': f'transit_positions.{field}',
                'local_skill': lv,
                'swiss_direct': sv,
                'delta': delta,
                'status': status,
            })
        if pname in ['Jupiter','Saturn','Rahu','Ketu']:
            mv = (multi_analysis.get(pname) or {}).get('sign')
            rows.append({
                'sample_id': sample['id'],
                'body': pname,
                'field': 'transit_multi_reference.sign',
                'local_skill': mv,
                'swiss_direct': s.get('sign'),
                'delta': '',
                'status': 'match' if mv == s.get('sign') else 'mismatch',
            })
    return rows


def write_report(rows):
    total = len(rows)
    matches = sum(1 for r in rows if r['status'] == 'match')
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    by_field = {}
    for r in rows:
        by_field.setdefault(r['field'], {'total': 0, 'match': 0, 'mismatch': 0, 'not_comparable': 0})
        by_field[r['field']]['total'] += 1
        by_field[r['field']][r['status']] = by_field[r['field']].get(r['status'], 0) + 1

    lines = []
    lines.append('# Jyotish benchmark 第八轮 Transit 真实过境对比报告')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 范围')
    lines.append('')
    lines.append('- 对比对象：full-reading.modules.transit_positions / transit_multi_reference vs 直接调用 Swiss Ephemeris。')
    lines.append('- 样本：10个公开/虚构 smoke case，不包含真实用户个人资料。')
    lines.append('- 配置：Sidereal Lahiri，Mean Node，transit date 使用样本 today 字段。')
    lines.append('- 重点：确认 full-reading 的多参考点 Transit 不再使用 natal positions fallback，而是使用真实过境行星位置。')
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
        lines.append(f"| {field} | {stat['total']} | {stat.get('match', 0)} | {stat.get('mismatch', 0)} |")
    lines.append('')
    if mismatches:
        lines.append('## 4. 不匹配样例')
        lines.append('')
        lines.append('| Sample | Body | Field | Local skill | Swiss direct | Delta |')
        lines.append('|---|---|---|---|---|---:|')
        for r in mismatches[:80]:
            lines.append(f"| {r['sample_id']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['swiss_direct']} | {r['delta']} |")
        lines.append('')
    lines.append('## 5. 结论')
    lines.append('')
    if mismatches:
        lines.append('- Transit 真实过境链路仍存在不匹配，需继续检查 UTC换算、node mode 或输出路径。')
    else:
        lines.append('- full-reading 的 Transit 输出已明确使用 true_transit_positions。')
        lines.append('- transit_positions 与 Swiss direct 完全对齐；transit_multi_reference 的 Jupiter/Saturn/Rahu/Ketu 星座也与真实过境一致。')
    report = OUT / 'jyotish_benchmark_round8_transit_true_compare.md'
    report.write_text('\n'.join(lines))
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    TRANSIT_OUT.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    all_rows = []
    for sample in samples:
        all_rows.extend(compare_sample(sample))
    csv_path = OUT / 'transit_true_comparison_matrix.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id','body','field','local_skill','swiss_direct','delta','status'])
        writer.writeheader()
        writer.writerows(all_rows)
    report = write_report(all_rows)
    print(json.dumps({
        'rows': len(all_rows),
        'matches': sum(1 for r in all_rows if r['status'] == 'match'),
        'mismatches': sum(1 for r in all_rows if r['status'] == 'mismatch'),
        'csv': str(csv_path),
        'report': str(report),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
