# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""Rahu/Ketu node-mode arbitration benchmark.

Compares local Jyotish skill canonical output against Swiss Ephemeris Mean/True Node
and PyJHora's default rasi_chart node mode. Samples are fictional/public smoke cases.
"""
import csv
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
CANON = OUT / 'canonical'
REPORT = OUT / 'jyotish_benchmark_round4_node_mode_compare.md'
MATRIX = OUT / 'node_mode_comparison_matrix.csv'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))
PYJHORA_COMPAT = ROOT / 'scripts/pyjhora_compat'

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
NAKSHATRAS = [
    'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
    'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
]
PYJHORA_PLANET_ID = {7: 'Rahu', 8: 'Ketu'}


def norm(deg):
    return deg % 360.0


def sign_of(lon):
    return SIGNS[int(norm(lon) // 30)]


def degree_in_sign(lon):
    return norm(lon) % 30.0


def nakshatra_of(lon):
    unit = 360.0 / 27.0
    idx = int(math.floor(norm(lon) / unit))
    pada = int(math.floor((norm(lon) % unit) / (unit / 4.0))) + 1
    return NAKSHATRAS[idx], min(pada, 4)


def julian_day_utc(birth):
    tz = float(birth['tz'])
    local = datetime(int(birth['year']), int(birth['month']), int(birth['day']), int(birth['hour']), int(birth['minute']))
    utc_dt = local - timedelta(hours=tz)
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def point_from_lon(lon):
    nak, pada = nakshatra_of(lon)
    return {
        'longitude': round(norm(lon), 6),
        'sign': sign_of(lon),
        'degree_in_sign': round(degree_in_sign(lon), 6),
        'nakshatra': nak,
        'nakshatra_pada': pada,
    }


def swiss_nodes(sample, node_pid):
    jd = julian_day_utc(sample['birth'])
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    res, _ = swe.calc_ut(jd, node_pid, flags)
    rahu = point_from_lon(res[0])
    ketu = point_from_lon(res[0] + 180.0)
    return {'Rahu': rahu, 'Ketu': ketu}


def patch_swisseph_for_pyjhora():
    for name in ['SIDM_KRISHNAMURTI_VP291', 'SIDM_TRUE_MULA', 'SIDM_TRUE_CITRA', 'SIDM_TRUE_REVATI']:
        if not hasattr(swe, name):
            setattr(swe, name, getattr(swe, 'SIDM_KRISHNAMURTI', 1))
    orig_calc_ut = swe.calc_ut
    def calc_ut(jd, body, flags=0, *args, **kwargs):
        if 'flags' in kwargs:
            flags = kwargs.pop('flags')
        return orig_calc_ut(jd, body, flags)
    swe.calc_ut = calc_ut
    orig_houses_ex = swe.houses_ex
    def houses_ex(tjdut, lat, lon, hsys=b'P', flags=0, *args, **kwargs):
        if 'flags' in kwargs:
            flags = kwargs.pop('flags')
        if 'hsys' in kwargs:
            hsys = kwargs.pop('hsys')
        return orig_houses_ex(tjdut, lat, lon, hsys, flags)
    swe.houses_ex = houses_ex
    return swe


def pyjhora_default_nodes(sample):
    # PyJHora is used only as an external benchmark. Do not vendor/copy its code into the skill.
    if str(PYJHORA_COMPAT) not in sys.path:
        sys.path.insert(0, str(PYJHORA_COMPAT))
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora import utils, const
    from jhora.panchanga import drik
    from jhora.horoscope.chart import charts
    const._DEFAULT_AYANAMSA_MODE = 'LAHIRI'
    drik.set_ayanamsa_mode('LAHIRI')
    # Note: charts.rasi_chart -> drik.dhasavarga() defaults to set_rahu_ketu_as_true_nodes=True.
    b = sample['birth']
    jd = utils.julian_day_number((b['year'], b['month'], b['day']), (b['hour'], b['minute'], 0))
    place = drik.Place(sample['label'], b['lat'], b['lon'], b['tz'])
    nodes = {}
    for key, value in charts.rasi_chart(jd, place):
        body = PYJHORA_PLANET_ID.get(key)
        if not body:
            continue
        sign_idx, deg = value
        abs_lon = int(sign_idx) * 30.0 + float(deg)
        nodes[body] = point_from_lon(abs_lon)
    return nodes


def local_nodes(sample_id):
    local = json.loads((CANON / f'{sample_id}.canonical.json').read_text())
    out = {}
    for body in ['Rahu', 'Ketu']:
        p = local['planets'][body]
        lon = SIGNS.index(p['sign']) * 30.0 + float(p['degree_in_sign'])
        out[body] = {
            'longitude': round(lon, 6),
            'sign': p['sign'],
            'degree_in_sign': round(float(p['degree_in_sign']), 6),
            'nakshatra': p['nakshatra'],
            'nakshatra_pada': p['nakshatra_pada'],
        }
    return out


def compare_point(rows, sample_id, body, field, local_value, target_name, target_value, tolerance=None):
    status = 'match'
    delta = ''
    if tolerance is not None:
        delta_val = abs(float(local_value) - float(target_value))
        delta = round(delta_val, 6)
        status = 'match' if delta_val <= tolerance else 'mismatch'
    else:
        status = 'match' if local_value == target_value else 'mismatch'
    rows.append({
        'sample_id': sample_id,
        'body': body,
        'field': field,
        'target': target_name,
        'local_skill': local_value,
        'target_value': target_value,
        'delta': delta,
        'status': status,
    })


def summarize(rows, target):
    subset = [r for r in rows if r['target'] == target]
    total = len(subset)
    match = sum(1 for r in subset if r['status'] == 'match')
    return {'target': target, 'total': total, 'match': match, 'mismatch': total - match, 'rate': match / total if total else 0.0}


def write_report(rows):
    targets = ['swiss_mean_node', 'swiss_true_node', 'pyjhora_default_rasi']
    lines = []
    lines.append('# Jyotish benchmark 第四轮：Rahu/Ketu 节点口径仲裁')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 本轮目的')
    lines.append('')
    lines.append('- 解释第三轮 PyJHora 对比中 Rahu/Ketu 大量差异的根因。')
    lines.append('- 对比当前 skill canonical baseline 与 Swiss Ephemeris Mean Node、Swiss Ephemeris True Node、PyJHora rasi_chart 默认输出。')
    lines.append('- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append('| Target | Total | Match | Mismatch | Match rate |')
    lines.append('|---|---:|---:|---:|---:|')
    summaries = [summarize(rows, t) for t in targets]
    for s in summaries:
        lines.append(f"| {s['target']} | {s['total']} | {s['match']} | {s['mismatch']} | {s['rate']:.2%} |")
    lines.append('')
    lines.append('## 3. 分字段统计')
    lines.append('')
    lines.append('| Target | Field | Total | Match | Mismatch |')
    lines.append('|---|---|---:|---:|---:|')
    for target in targets:
        for field in ['sign', 'degree_in_sign', 'nakshatra', 'nakshatra_pada']:
            subset = [r for r in rows if r['target'] == target and r['field'] == field]
            match = sum(1 for r in subset if r['status'] == 'match')
            lines.append(f'| {target} | {field} | {len(subset)} | {match} | {len(subset)-match} |')
    lines.append('')
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    lines.append('## 4. 关键不匹配样例')
    lines.append('')
    lines.append('| Sample | Target | Body | Field | Local skill | Target value | Delta |')
    lines.append('|---|---|---|---|---|---|---:|')
    for r in mismatches[:120]:
        lines.append(f"| {r['sample_id']} | {r['target']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['target_value']} | {r['delta']} |")
    lines.append('')
    lines.append('## 5. 仲裁结论')
    lines.append('')
    lines.append('- 当前 skill 的 Rahu/Ketu 与 Swiss Ephemeris **Mean Node** 口径完全一致；这解释了第一轮 Swiss direct 450/450 匹配。')
    lines.append('- PyJHora 4.8.6 的 `rasi_chart()` 默认走 `drik.dhasavarga(... set_rahu_ketu_as_true_nodes=True)`，即默认使用 **True Node**。')
    lines.append('- 因此第三轮 PyJHora 中 Rahu/Ketu 的 degree/nakshatra/D9/D10 差异，主要不是当前 skill 的计算 bug，而是 **Mean Node vs True Node 口径差异**。')
    lines.append('- 工程建议：当前 skill 应显式声明默认 `node_mode=mean`，后续可新增 `--node-mode mean|true` 参数；benchmark 报告中也应把节点口径列为冻结参数。')
    return '\n'.join(lines)


def main():
    samples = json.loads(DATA.read_text())
    rows = []
    for sample in samples:
        sample_id = sample['id']
        local = local_nodes(sample_id)
        targets = {
            'swiss_mean_node': swiss_nodes(sample, swe.MEAN_NODE),
            'swiss_true_node': swiss_nodes(sample, swe.TRUE_NODE),
            'pyjhora_default_rasi': pyjhora_default_nodes(sample),
        }
        for target_name, target_nodes in targets.items():
            for body in ['Rahu', 'Ketu']:
                for field in ['sign', 'nakshatra', 'nakshatra_pada']:
                    compare_point(rows, sample_id, body, field, local[body][field], target_name, target_nodes[body][field])
                compare_point(rows, sample_id, body, 'degree_in_sign', local[body]['degree_in_sign'], target_name, target_nodes[body]['degree_in_sign'], tolerance=0.1)
    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'body', 'field', 'target', 'local_skill', 'target_value', 'delta', 'status'])
        writer.writeheader()
        writer.writerows(rows)
    REPORT.write_text(write_report(rows))
    print(json.dumps({'report': str(REPORT), 'matrix': str(MATRIX), 'samples': len(samples), 'fields': len(rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
